import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from slot_extractor.quantization.lineage import Lineage
from slot_extractor.quantization.manifest import (
    ArtifactHash,
    StageManifest,
    sha256_file,
    write_manifest_atomic,
)
from slot_extractor.quantization.registry import ModelRegistry
from slot_extractor.schemas.results import GenerationResult
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference
from slot_extractor.schemas.search_state import SearchState
from slot_extractor.search_compare import app as app_module
from slot_extractor.search_compare.app import create_app

CONFIG = Path("configs/quantization/baking_search_v1.yaml")
MODELS = ModelRegistry.from_config(CONFIG)
LEFT, RIGHT = [s.model_id for s in MODELS.quantization_targets()]
PATCH = SearchPatch(
    hard_filters=(HardFilter("price", "lte", value=20, unit="USD"),),
    soft_preferences=(SoftPreference("flavor", "prefer", values=("pistachio",)),),
).to_dict()


class Backend:
    def __init__(self, model, output=None):
        self.model, self.output, self.calls = model, output or PATCH, []

    def generate(self, messages, params=None):
        self.calls.append(messages)
        if messages[-1]["content"] == "价格不限了":
            output = SearchPatch(clear_fields=("price",)).to_dict()
        else:
            output = self.output
        return GenerationResult(
            output if isinstance(output, str) else json.dumps(output),
            self.model,
            1,
            2,
            3,
            output_tokens=30,
            input_tokens=100,
            tokens_per_s=10,
        )


def body(**changes):
    return {
        "left_model_id": LEFT,
        "right_model_id": RIGHT,
        "user_input": "20美元以内，最好开心果",
        **changes,
    }


def results(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in response.text.splitlines()]
    return {e["side"]: e["payload"] for e in events if e["type"] == "side_result"}, events


def test_search_ui_and_full_pipeline_with_independent_multiturn_states(tmp_path):
    backends = {}

    def factory(spec):
        backends[spec.model_id] = Backend(spec.model_id)
        return backends[spec.model_id]

    with TestClient(create_app(backend_factory=factory, log_path=tmp_path / "log.jsonl")) as api:
        assert api.get("/").status_code == 200
        assert api.get("/api/technicians").status_code == 404
        assert len(api.get("/api/registry").json()["registry"]["fields"]) == 14
        first, events = results(api.post("/api/compare", json=body()))
        assert all(r["status"] == "complete" for r in first.values())
        assert len({e["request_id"] for e in events}) == 1
        assert all(e["comparable"] for e in events)
        assert first["left"]["compiled_query"]["parameters"]["filter_by"] == "price:<=20"
        next_body = body(
            user_input="价格不限了",
            left_current_search_state=first["left"]["next_state"],
            right_current_search_state=first["right"]["next_state"],
        )
        second, _ = results(api.post("/api/compare", json=next_body))
        assert all(r["next_state"]["hard_filters"] == [] for r in second.values())
        assert all(
            r["next_state"]["soft_preferences"][0]["values"] == ["pistachio"]
            for r in second.values()
        )
        assert len(backends) == 2 and all(len(b.calls) == 2 for b in backends.values())
        assert api.post("/api/model-slots/left/unload").status_code == 200
        assert (
            api.post("/api/client-logs", json={"level": "error", "message": "UI error"}).status_code
            == 204
        )
    names = [
        json.loads(line)["event"]
        for line in (tmp_path / "log.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert "search_patch_generated" in names and "search_query_compiled" in names
    assert "model_unloaded" in names and "app_stopped" in names


def test_one_failed_side_preserves_state_and_other_side_completes(tmp_path):
    current = SearchState(
        hard_filters=(HardFilter("application", "in", values=("croissant_pastry",)),)
    ).to_dict()
    with TestClient(
        create_app(
            backend_factory=lambda s: Backend(
                s.model_id, "invalid" if s.model_id == LEFT else PATCH
            ),
            log_path=tmp_path / "log",
        )
    ) as api:
        result, _ = results(api.post("/api/compare", json=body(current_search_state=current)))
    assert result["left"]["status"] == "error"
    assert result["left"]["error"]["stage"] == "parse"
    assert result["left"]["next_state"] == current
    assert result["right"]["status"] == "complete"
    assert result["right"]["next_state"]["hard_filters"][0]["field"] == "application"


def test_explicit_null_side_state_overrides_shared_state(tmp_path):
    current = SearchState(
        hard_filters=(HardFilter("application", "in", values=("croissant_pastry",)),)
    ).to_dict()
    with TestClient(
        create_app(backend_factory=lambda s: Backend(s.model_id), log_path=tmp_path / "log")
    ) as api:
        result, _ = results(
            api.post(
                "/api/compare",
                json=body(current_search_state=current, left_current_search_state=None),
            )
        )
    assert result["left"]["current_state"] is None
    assert result["right"]["current_state"] == current


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"left_current_search_state": {"flavor": "pistachio"}}, 422),
        ({"user_input": "   "}, 422),
        ({"user_input": "x" * 513}, 422),
        ({"left_history": []}, 422),
        ({"mode": "anything"}, 422),
        ({"left_model_id": "missing"}, 404),
    ],
)
def test_invalid_requests_fail_before_loading_or_inference(tmp_path, changes, code):
    creations = []
    with TestClient(
        create_app(
            backend_factory=lambda s: creations.append(s.model_id) or Backend(s.model_id),
            log_path=tmp_path / "log",
        )
    ) as api:
        assert api.post("/api/compare", json=body(**changes)).status_code == code
    assert creations == []


def test_missing_artifacts_are_visible_but_cannot_load(tmp_path):
    with TestClient(create_app(log_path=tmp_path / "log")) as api:
        listed = api.get("/api/models").json()
        assert len(listed) == 4 and all(not m["available"] for m in listed)
        assert all(m["unavailable_reason"] for m in listed)
        assert api.post("/api/model-slots/left/load", json={"model_id": LEFT}).status_code == 409
        assert (
            api.post("/api/model-slots/left/load", json={"model_id": "missing"}).status_code == 404
        )
        assert api.post("/api/model-slots/third/unload").status_code == 404


def test_availability_refreshes_after_build_and_detects_changed_artifact(tmp_path):
    spec = replace(
        MODELS.get(LEFT),
        artifact_path=tmp_path / "model.gguf",
        manifest_path=tmp_path / "manifest.json",
    )
    local_models = ModelRegistry((spec,), "baking_search")
    with TestClient(create_app(registry=local_models, log_path=tmp_path / "log")) as api:
        assert not api.get("/api/models").json()[0]["available"]
        spec.artifact_path.write_bytes(b"gguf")
        manifest = StageManifest(
            spec.model_id,
            "verify",
            "complete",
            spec.artifact_kind,
            False,
            "cache",
            Lineage(spec.model_id, spec.base_model, "main", None, None, (), "revision", ()),
            (),
            (ArtifactHash(str(spec.artifact_path), sha256_file(spec.artifact_path)),),
            (),
            None,
        )
        write_manifest_atomic(spec.manifest_path, manifest)
        assert api.get("/api/models").json()[0]["available"]
        spec.artifact_path.write_bytes(b"tampered-gguf")
        assert not api.get("/api/models").json()[0]["available"]


@pytest.mark.parametrize("mode,maximum", [("sequential", 1), ("parallel", 2)])
def test_parallel_is_actual_concurrency_and_performance_is_labelled(tmp_path, mode, maximum):
    active = 0
    seen_maximum = 0
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    class SlowBackend(Backend):
        def generate(self, messages, params=None):
            nonlocal active, seen_maximum
            with lock:
                active += 1
                seen_maximum = max(seen_maximum, active)
            try:
                if mode == "parallel":
                    barrier.wait(timeout=5)
                time.sleep(0.01)
                return super().generate(messages, params)
            finally:
                with lock:
                    active -= 1

    with TestClient(
        create_app(backend_factory=lambda s: SlowBackend(s.model_id), log_path=tmp_path / "log")
    ) as api:
        result, events = results(api.post("/api/compare", json=body(mode=mode)))
    assert all(r["status"] == "complete" for r in result.values())
    assert seen_maximum == maximum
    assert all(e["comparable"] == (mode == "sequential") for e in events)


def test_comparisons_and_slot_mutations_are_serialized(tmp_path):
    active, maximum = 0, 0
    lock = threading.Lock()

    class SlowBackend(Backend):
        def generate(self, messages, params=None):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            try:
                time.sleep(0.015)
                return super().generate(messages, params)
            finally:
                with lock:
                    active -= 1

    app = create_app(backend_factory=lambda s: SlowBackend(s.model_id), log_path=tmp_path / "log")
    with TestClient(app) as api, ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(lambda _: api.post("/api/compare", json=body()).status_code, range(2))
        )
    assert responses == [200, 200] and maximum == 1


def test_loading_failure_is_isolated_and_logged(tmp_path):
    def factory(spec):
        if spec.model_id == LEFT:
            raise RuntimeError("load failed")
        return Backend(spec.model_id)

    with TestClient(create_app(backend_factory=factory, log_path=tmp_path / "log")) as api:
        assert api.post("/api/model-slots/left/load", json={"model_id": LEFT}).status_code == 503
        result, _ = results(api.post("/api/compare", json=body()))
    assert result["left"]["status"] == "error" and result["right"]["status"] == "complete"


def test_real_server_slots_reuse_and_cleanup_after_readiness_failure(tmp_path, monkeypatch):
    managers = []

    class Manager:
        def __init__(self, registry, server, port, threads):
            self.port, self.stops, self.starts = port, [], []
            self.base_url = f"http://127.0.0.1:{port}/v1"
            managers.append(self)

        def start(self, model_id, log):
            self.starts.append(model_id)
            return object()

        def wait_ready(self, process, timeout):
            if self.port == 18091:
                raise RuntimeError("not ready")

        def stop(self, process):
            self.stops.append(process)

    monkeypatch.setattr(app_module, "LlamaServerManager", Manager)
    diagnostics = app_module.DiagnosticLog(tmp_path / "log")
    slots = app_module.ResidentModelSlots(
        MODELS, diagnostics, {"toolchain": {"server": "server.exe"}}
    )
    first = slots.load("left", LEFT)
    assert slots.load("left", LEFT) is first and len(managers) == 1
    assert first._default_params.max_tokens == 2048
    with pytest.raises(RuntimeError, match="not ready"):
        slots.load("right", RIGHT)
    assert len(managers[1].stops) == 1
    slots.close()
    assert len(managers[0].stops) == 1
    diagnostics.close()
