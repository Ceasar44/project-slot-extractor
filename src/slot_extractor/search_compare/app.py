"""Local SearchPatch comparison API and browser UI."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from copy import deepcopy
from pathlib import Path
from threading import Lock, RLock
from traceback import format_exc
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from slot_extractor.inference.base import Backend
from slot_extractor.inference.llama_server import LlamaServerBackend, LlamaServerConfig
from slot_extractor.inference.llama_server_manager import LlamaServerManager
from slot_extractor.prompts.template import PromptBuilder
from slot_extractor.quantization.manifest import read_and_verify_manifest
from slot_extractor.quantization.registry import ModelRegistry, ModelSpec
from slot_extractor.registry import load_registry
from slot_extractor.registry.derived import derive_model_registry
from slot_extractor.search import normalize_currency_unit, validate_state

from .diagnostics import DiagnosticLog
from .models import ClientLogRequest, CompareRequest, LoadModelRequest, ModelSideResult, SearchTrace
from .ndjson import encode_event, finite_json
from .orchestrator import SearchComparisonOrchestrator

STATIC = Path(__file__).parent / "static"
QUANTIZATION = Path("configs/quantization/baking_search_v1.yaml")


class ResidentModelSlots:
    """Two dedicated server processes, reused until explicitly switched or unloaded."""

    def __init__(self, registry, diagnostics, config, backend_factory=None, slot_ports=None):
        self.registry, self.diagnostics = registry, diagnostics
        self.config, self.backend_factory = config, backend_factory
        self.slot_ports = slot_ports or {"left": 18090, "right": 18091}
        if set(self.slot_ports) != {"left", "right"} or (
            self.slot_ports["left"] == self.slot_ports["right"]
        ):
            raise ValueError("left/right slots require distinct ports")
        self._slots = {}
        self._lock = RLock()

    def load(self, side, model_id):
        if side not in {"left", "right"}:
            raise ValueError("unknown model slot")
        with self._lock:
            current = self._slots.get(side)
            if current and current["model_id"] == model_id:
                self.diagnostics.write("model_reused", side=side, model_id=model_id)
                return current["backend"]
            spec = self.registry.get(model_id)
            self.unload(side)
            manager = process = None
            self.diagnostics.write("model_load_started", side=side, model_id=model_id)
            try:
                if self.backend_factory:
                    backend = self.backend_factory(spec)
                else:
                    manager = LlamaServerManager(
                        self.registry,
                        Path(self.config["toolchain"]["server"]),
                        port=self.slot_ports[side],
                        threads=int(self.config.get("threads", 8)),
                    )
                    process = manager.start(
                        model_id, Path("reports/generated/search-compare") / f"{side}-server.log"
                    )
                    manager.wait_ready(process, 60)
                    backend = LlamaServerBackend(
                        LlamaServerConfig(
                            model=model_id,
                            base_url=manager.base_url,
                            max_tokens=2048,
                            timeout_s=180,
                        )
                    )
            except Exception:
                if manager is not None and process is not None:
                    manager.stop(process)
                self.diagnostics.write(
                    "model_load_failed", side=side, model_id=model_id, traceback=format_exc()
                )
                raise
            self._slots[side] = {
                "model_id": model_id,
                "backend": backend,
                "manager": manager,
                "process": process,
            }
            self.diagnostics.write("model_ready", side=side, model_id=model_id)
            return backend

    def get(self, side, model_id):
        return self.load(side, model_id)

    def unload(self, side):
        with self._lock:
            current = self._slots.pop(side, None)
            if current and current["manager"] is not None:
                current["manager"].stop(current["process"])
            if current:
                self.diagnostics.write("model_unloaded", side=side, model_id=current["model_id"])

    def close(self):
        for side in ("left", "right"):
            self.unload(side)


def create_app(
    registry: ModelRegistry | None = None,
    backend_factory: Callable[[ModelSpec], Backend] | None = None,
    *,
    catalog_path: Path = Path("configs/catalog/registry.yaml"),
    quantization_config: Path = QUANTIZATION,
    log_path: Path = Path("reports/generated/search-compare/app.jsonl"),
    slot_ports: dict[str, int] | None = None,
    currency: str = "USD",
) -> FastAPI:
    catalog = load_registry(catalog_path)
    currency = normalize_currency_unit(currency, catalog)
    config = yaml.safe_load(quantization_config.read_text(encoding="utf-8"))
    registry = registry or ModelRegistry.from_config(quantization_config)
    diagnostics = DiagnosticLog(log_path)
    comparison_lock = Lock()
    slots = ResidentModelSlots(registry, diagnostics, config, backend_factory, slot_ports)
    availability_cache = {}
    availability_lock = Lock()

    @asynccontextmanager
    async def lifespan(_app):
        diagnostics.write(
            "app_started", registry_version=catalog.registry_version, currency=currency
        )
        try:
            yield
        finally:
            with comparison_lock:
                slots.close()
            diagnostics.write("app_stopped")
            diagnostics.close()

    app = FastAPI(title="烘焙搜索双模型对比", lifespan=lifespan)
    app.state.model_slots = slots
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    def model_spec(model_id):
        try:
            return registry.get(model_id)
        except ValueError as exc:
            raise HTTPException(404, "unknown model") from exc

    def availability(spec):
        if backend_factory:
            return True, None
        try:
            # Recheck when a new build appears or the artifact changes, unlike a permanent cache.
            manifest_stat, artifact_stat = spec.manifest_path.stat(), spec.artifact_path.stat()
            signature = (
                manifest_stat.st_mtime_ns,
                manifest_stat.st_size,
                artifact_stat.st_mtime_ns,
                artifact_stat.st_size,
            )
            with availability_lock:
                if availability_cache.get(spec.model_id) == signature:
                    return True, None
                manifest = read_and_verify_manifest(spec.manifest_path)
                if (
                    manifest.status != "complete"
                    or manifest.model_id != spec.model_id
                    or (manifest.artifact_kind != spec.artifact_kind)
                ):
                    raise ValueError("manifest does not describe the completed selected model")
                if not any(
                    Path(a.path).resolve() == spec.artifact_path.resolve() for a in manifest.outputs
                ):
                    raise ValueError("manifest does not include selected artifact")
                availability_cache[spec.model_id] = signature
            return True, None
        except Exception as exc:
            return False, str(exc)

    def require_available(model_id):
        spec = model_spec(model_id)
        ok, reason = availability(spec)
        if not ok:
            raise HTTPException(409, reason or "model unavailable")

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/models")
    def models():
        rows = []
        for spec in registry.models:
            ok, reason = availability(spec)
            rows.append(
                {
                    "model_id": spec.model_id,
                    "stage": spec.stage,
                    "size_b": spec.size_b,
                    "artifact_kind": spec.artifact_kind,
                    "available": ok,
                    "unavailable_reason": reason,
                }
            )
        return rows

    @app.get("/api/registry")
    def registry_summary():
        return {
            "registry": derive_model_registry(catalog), "currency": currency,
            "inference_mode": "injected" if backend_factory else "local",
        }

    @app.post("/api/model-slots/{side}/load")
    def load_model(side: str, request: LoadModelRequest):
        if side not in {"left", "right"}:
            raise HTTPException(404, "unknown model slot")
        require_available(request.model_id)
        try:
            with comparison_lock:
                slots.load(side, request.model_id)
        except Exception as exc:
            raise HTTPException(503, f"model load failed: {exc}") from exc
        return {"side": side, "model_id": request.model_id, "status": "ready"}

    @app.post("/api/model-slots/{side}/unload")
    def unload_model(side: str):
        if side not in {"left", "right"}:
            raise HTTPException(404, "unknown model slot")
        with comparison_lock:
            slots.unload(side)
        return {"side": side, "status": "unloaded"}

    @app.post("/api/client-logs", status_code=204)
    def client_log(request: ClientLogRequest):
        diagnostics.write(
            "client_error" if request.level == "error" else "client_log", **request.model_dump()
        )

    @app.post("/api/compare")
    def compare(request: CompareRequest):
        sides = []
        for side in ("left", "right"):
            state = request.state_for(side)
            try:
                if state is not None:
                    state = validate_state(state, catalog).to_dict()
                PromptBuilder(catalog).build_messages(
                    {
                        "current_search_state": state,
                        "user_input": request.user_input,
                    }
                )
            except ValueError as exc:
                raise HTTPException(422, f"{side} input: {exc}") from exc
            model_id = getattr(request, f"{side}_model_id")
            require_available(model_id)
            sides.append((side, model_id, deepcopy(state)))
        request_id = uuid4().hex
        comparable = request.mode == "sequential"
        diagnostics.write(
            "comparison_started",
            request_id=request_id,
            mode=request.mode,
            user_input=request.user_input,
            sides=sides,
        )

        def run_side(side, model_id, state):
            try:
                backend = slots.get(side, model_id)
                return SearchComparisonOrchestrator(
                    backend, catalog, currency=currency, model_id=model_id
                ).run(request.user_input, state)
            except Exception as exc:
                diagnostics.write(
                    "side_failed", request_id=request_id, side=side, traceback=format_exc()
                )
                return SearchTrace(
                    ModelSideResult(
                        model_id,
                        current_state=state,
                        next_state=state,
                        error={"stage": "load_or_inference", "message": str(exc)},
                    ),
                    (),
                )

        def emit_trace(side, trace):
            for seq, event in enumerate(trace.events, start=1):
                diagnostics.write(
                    event.kind, request_id=request_id, side=side, payload=finite_json(event.payload)
                )
                yield encode_event(request_id, side, seq, event.kind, event.payload, comparable)
            diagnostics.write(
                "side_completed",
                request_id=request_id,
                side=side,
                status=trace.result.status,
                metrics=finite_json(trace.result.metrics),
            )
            yield encode_event(
                request_id,
                side,
                len(trace.events) + 1,
                "side_result",
                trace.result.to_dict(),
                comparable,
            )

        def stream():
            with comparison_lock:
                try:
                    if request.mode == "parallel":
                        for side, _, _ in sides:
                            yield encode_event(
                                request_id,
                                side,
                                0,
                                "side_status",
                                {"status": "inferencing"},
                                comparable,
                            )
                        with ThreadPoolExecutor(max_workers=2) as pool:
                            jobs = {pool.submit(run_side, *item): item[0] for item in sides}
                            for job in as_completed(jobs):
                                yield from emit_trace(jobs[job], job.result())
                    else:
                        for side, model_id, state in sides:
                            yield encode_event(
                                request_id,
                                side,
                                0,
                                "side_status",
                                {"status": "inferencing"},
                                comparable,
                            )
                            yield from emit_trace(side, run_side(side, model_id, state))
                finally:
                    diagnostics.write("comparison_finished", request_id=request_id)

        return StreamingResponse(stream(), media_type="application/x-ndjson")

    return app
