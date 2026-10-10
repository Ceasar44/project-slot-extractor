"""Search builds with verified stage reuse and atomic output promotion."""

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from slot_extractor.quantization.manifest import sha256_file, write_manifest_atomic


@dataclass(frozen=True)
class ImatrixOptions:
    enabled: bool = True
    context_size: int = 8192
    batch_size: int = 128
    max_chunks: int | None = None
    no_ppl: bool = False

    @classmethod
    def from_payload(cls, payload):
        values = dict(payload.get("imatrix", {}))
        values.setdefault("context_size", payload.get("context_size", 512))
        options = cls(**values)
        for key in ("enabled", "no_ppl"):
            if not isinstance(getattr(options, key), bool):
                raise ValueError(f"imatrix.{key} must be boolean")
        for key in ("context_size", "batch_size", "max_chunks"):
            value = getattr(options, key)
            if value is None and key == "max_chunks":
                continue
            if type(value) is not int or value < 1:
                raise ValueError(f"imatrix.{key} must be a positive integer")
        return options


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def hashes(path):
    if path.is_file():
        return {path.name: sha256_file(path)}
    files = sorted(p for p in path.rglob("*") if p.is_file())
    if not files:
        raise FileNotFoundError(f"empty stage input/output: {path}")
    return {p.relative_to(path).as_posix(): sha256_file(p) for p in files}


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8") as output:
        json.dump(payload, output, ensure_ascii=False, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def stage(name, output, record, inputs, parameters, action, *, directory=False):
    record.parent.mkdir(parents=True, exist_ok=True)
    lock = record.with_suffix(record.suffix + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(
            f"stage locked: {lock}; check the owning process before removing it"
        ) from error
    try:
        with os.fdopen(descriptor, "w") as owner:
            owner.write(str(os.getpid()))
        return _stage(name, output, record, inputs, parameters, action, directory=directory)
    finally:
        lock.unlink(missing_ok=True)


def _stage(name, output, record, inputs, parameters, action, *, directory=False):
    """Only an intact completion record allows reuse; checkpoints never do."""
    key = digest({"inputs": inputs, "parameters": parameters})
    previous = None
    if record.is_file():
        previous = json.loads(record.read_text(encoding="utf-8"))
    if output.exists():
        if previous is None or previous.get("status") != "complete":
            raise FileExistsError(
                f"unverified existing {name}: {output}; use a new artifact path/version"
            )
        actual = hashes(output)
        if actual != previous["outputs"]:
            raise ValueError(f"{name} output hash mismatch: {output}")
        if previous["key"] == key:
            print(f"reuse: {name}: {output}", flush=True)
            return
        if directory:
            raise ValueError("directory stage inputs changed; use a new source cache key")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Unique temporary outputs avoid accidentally reusing periodic imatrix saves.
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=output.parent))
    temporary = temporary_root / ("model" if directory else output.name)
    pending = record.with_suffix(record.suffix + ".running")
    atomic_json(pending, {"status": "running", "key": key, "temporary": str(temporary)})
    print(f"build: {name}: {output}", flush=True)
    try:
        action(temporary)
        if not directory and (not temporary.is_file() or temporary.stat().st_size == 0):
            raise RuntimeError(f"{name} produced no output")
        output_hashes = hashes(temporary)
        temporary.replace(output)
        atomic_json(
            record,
            {
                "status": "complete",
                "key": key,
                "inputs": inputs,
                "parameters": parameters,
                "outputs": output_hashes,
            },
        )
        pending.unlink(missing_ok=True)
        temporary_root.rmdir()
    except Exception as error:
        atomic_json(pending, {"status": "failed", "key": key, "error": str(error)})
        raise


def project_revision(payload):
    if payload.get("project_revision"):
        return str(payload["project_revision"])
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        # Source archives have no Git metadata. Identify the builder, never invent a commit.
        return "source-sha256:" + digest(
            {
                name: sha256_file(Path(__file__).with_name(name))
                for name in ("search_build.py", "build_phase05_real.py")
            }
        )


def build_search(args, registry, payload):
    from scripts.quantize import build_phase05_real as real

    model_options = payload.get("model_options", {})
    targets = tuple(
        s
        for s in registry.quantization_targets()
        if not model_options.get(s.model_id, {}).get("experimental", False)
    )
    if args.model_id:
        targets = tuple(registry.get(model_id) for model_id in args.model_id)
    if any(s.artifact_kind != "q4_k_m" or s.is_anchor for s in targets):
        raise ValueError("select Q4_K_M targets; matching F16 anchors are built automatically")
    threads = payload.get("threads", 8)
    if type(threads) is not int or threads < 1:
        raise ValueError("threads must be a positive integer")
    options_by_id = {
        s.model_id: ImatrixOptions.from_payload(
            {
                **payload,
                "imatrix": {
                    **payload.get("imatrix", {}),
                    **payload.get("model_options", {}).get(s.model_id, {}).get("imatrix", {}),
                },
            }
        )
        for s in targets
    }
    calibration = Path(payload.get("calibration_data", "data/calibration/baking-search-v1.txt"))
    calibration_by_id = {
        s.model_id: Path(model_options.get(s.model_id, {}).get("calibration_data", calibration))
        for s in targets
    }
    tools = real.Tools(
        *(Path(payload["toolchain"][k]) for k in ("convert_f16", "imatrix", "quantize"))
    )
    if args.dry_run:
        print(
            json.dumps(
                {
                    "models": [s.model_id for s in targets],
                    "adapters": [str(s.adapter_path) for s in targets],
                    "calibration": str(calibration),
                    "calibration_exists": calibration.is_file(),
                    "imatrix": {k: asdict(v) for k, v in options_by_id.items()},
                    "calibrations": {
                        k: {"path": str(v), "exists": v.is_file()}
                        for k, v in calibration_by_id.items()
                    },
                    "tools": {
                        k: {"path": str(v), "exists": v.is_file()} for k, v in vars(tools).items()
                    },
                },
                indent=2,
            )
        )
        return 0
    enabled = any(o.enabled for o in options_by_id.values())
    for model_id, candidate in calibration_by_id.items():
        if not options_by_id[model_id].enabled:
            continue
        if "data/eval/" in candidate.resolve().as_posix().lower() + "/":
            raise ValueError("calibration cannot use Frozen Eval")
        if not candidate.is_file() or not candidate.stat().st_size:
            raise FileNotFoundError(
                f"prepare nonempty training-only calibration first: {candidate}"
            )
        calibration_manifest = candidate.with_suffix(".manifest.json")
        if model_options.get(model_id, {}).get("require_calibration_manifest", False):
            if not calibration_manifest.is_file():
                raise FileNotFoundError(f"prepare calibration provenance: {calibration_manifest}")
        if calibration_manifest.is_file():
            provenance = json.loads(calibration_manifest.read_text(encoding="utf-8"))
            if provenance.get("split") != "train" or provenance.get(
                "calibration_sha256"
            ) != sha256_file(candidate):
                raise ValueError(f"invalid calibration provenance: {calibration_manifest}")
    required = {"converter": tools.converter, "quantize": tools.quantize}
    if enabled:
        required["imatrix"] = tools.imatrix
    for tool in required.values():
        if not tool.is_file():
            raise FileNotFoundError(f"quantization tool missing: {tool}")
    versions = {name: sha256_file(tool) for name, tool in required.items()}
    # Include bundled converter modules, which may change independently of its entry script.
    for folder in ("conversion", "gguf-py"):
        root = tools.converter.parent / folder
        if root.is_dir():
            versions[folder] = digest(
                {p.relative_to(root).as_posix(): sha256_file(p) for p in sorted(root.rglob("*.py"))}
            )
    revision = project_revision(payload)
    work_root = Path(payload["work_root"])
    for spec in targets:
        options = options_by_id[spec.model_id]
        calibration = calibration_by_id[spec.model_id]
        anchors = [
            a
            for a in registry.anchors()
            if (a.base_model, a.adapter_run_id) == (spec.base_model, spec.adapter_run_id)
        ]
        if len(anchors) != 1:
            raise ValueError(f"expected one matching F16 anchor: {spec.model_id}")
        anchor = anchors[0]
        from dataclasses import replace

        local_base = payload.get("base_model_paths", {}).get(spec.base_model)
        base = real.cached_base(replace(spec, base_model=str(local_base)) if local_base else spec)
        # Hash actual weights and tokenizer files; exclude download cache metadata.
        base_suffixes = {".json", ".safetensors", ".bin", ".model", ".txt", ".jinja", ".py"}
        base_hashes = {
            p.name: sha256_file(p)
            for p in sorted(base.iterdir())
            if p.is_file() and p.suffix in base_suffixes
        }
        if not base_hashes:
            raise FileNotFoundError(f"empty base: {base}")
        adapter_hashes = (
            {}
            if spec.adapter_path is None
            else {
                name: sha256_file(spec.adapter_path / name)
                for name in ("adapter_config.json", "adapter_model.safetensors")
            }
        )
        import importlib.metadata

        packages = {
            name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft")
        }
        merge_inputs = {"base": base_hashes, "adapter": adapter_hashes}
        merge_parameters = {
            "dtype": "float16",
            "packages": packages,
            "schema": 1,
            "builder": sha256_file(Path(real.__file__)),
        }
        source_key = digest({"inputs": merge_inputs, "parameters": merge_parameters})
        shared = work_root / "sources" / source_key
        log = work_root / spec.model_id / "real-build.log"
        merged = shared / "merged"
        stage(
            "merge",
            merged,
            shared / "merge.json",
            merge_inputs,
            merge_parameters,
            lambda out, spec=spec, base=base: real.merge_adapter(spec, base, out),
            directory=True,
        )
        f16 = anchor.artifact_path
        f16_record = f16.with_suffix(".stage.json")
        convert_parameters = {
            k: v for k, v in versions.items() if k in {"converter", "conversion", "gguf-py"}
        }
        stage(
            "f16",
            f16,
            f16_record,
            {"merged": hashes(merged)},
            convert_parameters,
            lambda out, merged=merged, log=log: real.convert(merged, out, tools, log),
        )
        f16_hash = sha256_file(f16)
        source_hashes = (("base-content", digest(base_hashes)),)
        write_manifest_atomic(
            anchor.manifest_path,
            real.manifest_for(
                anchor,
                f16,
                ("convert-f16",),
                project_revision=revision,
                tool_versions=tuple(sorted(convert_parameters.items())),
                extra_sources=source_hashes,
                parameters={"conversion": digest(convert_parameters)},
            ),
        )
        matrix = None
        calibration_hash = None
        if options.enabled:
            calibration_hash = sha256_file(calibration)
            matrix_parameters = {
                **asdict(options),
                "threads": threads,
                "tool": versions["imatrix"],
                "parse_special": True,
            }
            matrix_inputs = {"f16": f16_hash, "calibration": calibration_hash}
            provenance_path = calibration.with_suffix(".manifest.json")
            if provenance_path.is_file():
                matrix_inputs["calibration_manifest"] = sha256_file(provenance_path)
            matrix_key = digest({"inputs": matrix_inputs, "parameters": matrix_parameters})
            matrix = work_root / "matrices" / f"{matrix_key}.gguf"
            stage(
                "imatrix",
                matrix,
                matrix.with_suffix(".stage.json"),
                matrix_inputs,
                matrix_parameters,
                lambda out, f16=f16, log=log, calibration=calibration, options=options: (
                    real.build_imatrix(
                        f16,
                        out,
                        tools,
                        log,
                        calibration,
                        threads,
                        options.context_size,
                        batch_size=options.batch_size,
                        max_chunks=options.max_chunks,
                        no_ppl=options.no_ppl,
                    )
                ),
            )
        quant_inputs = {"f16": f16_hash, "imatrix": sha256_file(matrix) if matrix else None}
        parameters = {
            "type": "Q4_K_M",
            "threads": threads,
            "tool": versions["quantize"],
            "imatrix": asdict(options),
            "calibration": calibration_hash,
        }
        stage(
            "q4",
            spec.artifact_path,
            spec.artifact_path.with_suffix(".stage.json"),
            quant_inputs,
            parameters,
            lambda out, f16=f16, matrix=matrix, log=log: real.quantize(
                f16, matrix, out, tools, log, threads
            ),
        )
        command = [str(tools.quantize)]
        if matrix:
            command.extend(["--imatrix", str(matrix)])
        command.extend([str(f16), str(spec.artifact_path), "Q4_K_M", str(threads)])
        write_manifest_atomic(
            spec.manifest_path,
            real.manifest_for(
                spec,
                spec.artifact_path,
                tuple(command),
                calibration if matrix else None,
                project_revision=revision,
                tool_versions=tuple(sorted(versions.items())),
                extra_sources=(
                    *source_hashes,
                    ("f16", f16_hash),
                    *((("imatrix", sha256_file(matrix)),) if matrix else ()),
                    *(
                        (
                            (
                                "calibration_manifest",
                                sha256_file(calibration.with_suffix(".manifest.json")),
                            ),
                        )
                        if matrix and calibration.with_suffix(".manifest.json").is_file()
                        else ()
                    ),
                ),
                parameters=parameters,
            ),
        )
        print(f"complete: {spec.model_id}", flush=True)
    return 0
