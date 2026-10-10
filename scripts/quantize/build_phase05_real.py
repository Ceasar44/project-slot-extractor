"""Build the real Phase 05 GGUF matrix from cached Qwen bases and Phase 04 adapters."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from slot_extractor.quantization.lineage import Lineage, cache_key
from slot_extractor.quantization.manifest import (
    ArtifactHash,
    StageManifest,
    sha256_file,
    write_manifest_atomic,
)
from slot_extractor.quantization.registry import ModelRegistry, ModelSpec


@dataclass(frozen=True)
class Tools:
    converter: Path
    imatrix: Path
    quantize: Path


def run(command: list[str], log: Path) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as output:
        output.write(f"$ {' '.join(command)}\n")
        output.flush()
        completed = subprocess.run(
            command, stdout=output, stderr=subprocess.STDOUT, text=True, check=False
        )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")


def cached_base(spec: ModelSpec) -> Path:
    local = Path(spec.base_model)
    if local.is_dir():
        if not local.joinpath("config.json").is_file() or not list(local.glob("*.safetensors")):
            raise FileNotFoundError(f"incomplete local base: {local}")
        return local
    from huggingface_hub import snapshot_download

    try:
        return Path(
            snapshot_download(spec.base_model, revision=spec.base_revision, local_files_only=True)
        )
    except Exception as error:
        # A different cached revision must not be labelled as the requested base.
        raise RuntimeError(
            f"cannot resolve cached base {spec.base_model}@{spec.base_revision}"
        ) from error


def merge_adapter(spec: ModelSpec, base: Path, destination: Path) -> Path:
    if destination.joinpath("config.json").is_file():
        return destination
    adapter = spec.adapter_path or (
        Path("experiments/runs") / f"phase04-{spec.adapter_run_id}" / "adapter"
    )
    if not adapter.joinpath("adapter_model.safetensors").is_file():
        raise FileNotFoundError(f"adapter missing: {adapter}")
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model = AutoModelForCausalLM.from_pretrained(
        base, torch_dtype=torch.float16, low_cpu_mem_usage=True, local_files_only=True
    )
    merged = PeftModel.from_pretrained(model, adapter, local_files_only=True).merge_and_unload()
    destination.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(destination, safe_serialization=True, max_shard_size="4GB")
    AutoTokenizer.from_pretrained(base, local_files_only=True).save_pretrained(destination)
    del merged, model
    return destination


def convert(source: Path, output: Path, tools: Tools, log: Path) -> None:
    if output.is_file() and output.stat().st_size:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    run(
        [
            sys.executable,
            str(tools.converter),
            str(source),
            "--outfile",
            str(temporary),
            "--outtype",
            "f16",
        ],
        log,
    )
    if not temporary.is_file() or temporary.stat().st_size == 0:
        raise RuntimeError("converter did not produce a non-empty GGUF")
    temporary.replace(output)


def build_imatrix(
    f16: Path,
    output: Path,
    tools: Tools,
    log: Path,
    calibration: Path = Path("data/calibration/phase05-v1.txt"),
    threads: int = 8,
    context_size: int = 512,
    *,
    batch_size: int = 128,
    max_chunks: int | None = None,
    no_ppl: bool = False,
) -> None:
    if output.is_file() and output.stat().st_size:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(tools.imatrix),
        "-m",
        str(f16),
        "-f",
        str(calibration),
        "-o",
        str(output),
        "-t",
        str(threads),
        "-c",
        str(context_size),
        "-b",
        str(batch_size),
        "--parse-special",
    ]
    if max_chunks is not None:
        command.extend(["--chunks", str(max_chunks)])
    if no_ppl:
        command.append("--no-ppl")
    run(command, log)


def quantize(
    f16: Path, imatrix: Path | None, output: Path, tools: Tools, log: Path, threads: int = 8
) -> None:
    if output.is_file() and output.stat().st_size:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [str(tools.quantize)]
    if imatrix is not None:
        command.extend(["--imatrix", str(imatrix)])
    command.extend(
        [
            str(f16),
            str(output),
            "Q4_K_M",
            str(threads),
        ]
    )
    run(command, log)


def manifest_for(
    spec: ModelSpec,
    output: Path,
    command: tuple[str, ...],
    calibration: Path | None = None,
    *,
    project_revision: str | None = None,
    tool_versions=None,
    extra_sources=(),
    parameters=None,
) -> StageManifest:
    sources = list(extra_sources)
    if calibration is not None:
        sources.append(("calibration", sha256_file(calibration)))
    if spec.adapter_path is not None:
        sources.extend(
            (name, sha256_file(spec.adapter_path / name))
            for name in ("adapter_config.json", "adapter_model.safetensors")
        )
    lineage = Lineage(
        spec.model_id,
        spec.base_model,
        spec.base_revision,
        spec.parent_model_id,
        spec.adapter_run_id,
        tuple(sources),
        project_revision
        or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        tool_versions or (("llama.cpp", "local-release"),),
    )
    return StageManifest(
        spec.model_id,
        "verify",
        "complete",
        spec.artifact_kind,
        spec.is_anchor,
        cache_key(lineage, "real-build", parameters or {"type": spec.artifact_kind}),
        lineage,
        (),
        (ArtifactHash(str(output), sha256_file(output)),),
        command,
        None,
        parameters or {},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/quantization/phase05.yaml"))
    parser.add_argument("--model-id", action="append")
    parser.add_argument(
        "--dry-run", action="store_true", help="Inspect paths without heavy imports or commands"
    )
    args = parser.parse_args(argv)
    registry = ModelRegistry.from_config(args.config)
    payload = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if registry.profile == "baking_search" and payload.get("stage_reuse", True):
        from scripts.quantize.search_build import build_search

        return build_search(args, registry, payload)
    calibration = Path(payload["calibration_data"])
    work_root = Path(payload["work_root"])
    threads = int(payload.get("threads", 8))
    context_size = int(payload.get("context_size", 512))
    if threads < 1 or context_size < 1:
        raise ValueError("threads and context_size must be positive")
    if "data/eval/" in f"/{calibration.as_posix().lower()}":
        raise ValueError("calibration cannot use Frozen Eval")
    toolchain = payload["toolchain"]
    tools = Tools(
        Path(toolchain["convert_f16"]),
        Path(toolchain["imatrix"]),
        Path(toolchain["quantize"]),
    )
    targets = registry.quantization_targets()
    if args.model_id:
        targets = tuple(registry.get(model_id) for model_id in args.model_id)
    if any(s.artifact_kind != "q4_k_m" or s.is_anchor for s in targets):
        raise ValueError("select Q4_K_M targets; matching F16 anchors are built automatically")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "models": [s.model_id for s in targets],
                    "adapters": [str(s.adapter_path) for s in targets],
                    "calibration": str(calibration),
                    "calibration_exists": calibration.is_file(),
                    "tools": {
                        k: {"path": str(v), "exists": v.is_file()} for k, v in vars(tools).items()
                    },
                },
                indent=2,
            )
        )
        return 0
    if not calibration.is_file() or not calibration.stat().st_size:
        raise FileNotFoundError(f"prepare nonempty training-only calibration first: {calibration}")
    for tool in vars(tools).values():
        if not tool.is_file():
            raise FileNotFoundError(f"quantization tool missing: {tool}")
    for spec in targets:
        if spec.adapter_path is not None and any(
            not (spec.adapter_path / name).is_file()
            for name in ("adapter_config.json", "adapter_model.safetensors")
        ):
            raise FileNotFoundError(f"trained adapter missing: {spec.adapter_path}")
        if spec.adapter_path is not None:
            existing = [
                spec.artifact_path,
                spec.manifest_path,
                Path("models/merged") / f"hf-{spec.model_id}",
                Path("models/imatrix") / f"{spec.model_id}.dat",
                *[
                    a.artifact_path
                    for a in registry.anchors()
                    if a.adapter_run_id == spec.adapter_run_id
                ],
            ]
            if any(path.exists() for path in existing):
                raise FileExistsError(
                    f"search outputs already exist: {spec.model_id}; use a new version "
                    "or inspect and explicitly remove incomplete outputs before rebuilding"
                )
    f16_by_source: dict[tuple[str, str | None], Path] = {}
    for spec in targets:
        work = work_root / spec.model_id
        log = work / "real-build.log"
        base = cached_base(spec)
        source = (
            base
            if spec.stage == "base"
            else merge_adapter(spec, base, Path("models/merged") / f"hf-{spec.model_id}")
        )
        key = (spec.base_model, spec.adapter_run_id)
        anchors = [
            a
            for a in registry.anchors()
            if (a.base_model == spec.base_model and a.adapter_run_id == spec.adapter_run_id)
        ]
        anchor = anchors[0] if len(anchors) == 1 else None
        if spec.stage == "sft":
            if anchor is None:
                raise ValueError(f"expected one matching F16 anchor: {spec.model_id}")
            f16 = anchor.artifact_path
        else:
            f16 = work / "model-f16.gguf"
        convert(source, f16, tools, log)
        f16_by_source[key] = f16
        imatrix = Path("models/imatrix") / f"{spec.model_id}.dat"
        build_imatrix(f16, imatrix, tools, log, calibration, threads, context_size)
        quantize(f16, imatrix, spec.artifact_path, tools, log, threads)
        write_manifest_atomic(
            spec.manifest_path, manifest_for(spec, spec.artifact_path, ("Q4_K_M",), calibration)
        )
        if spec.stage == "sft":
            write_manifest_atomic(
                anchor.manifest_path, manifest_for(anchor, f16, ("convert-f16",), calibration)
            )
        print(f"complete: {spec.model_id}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
