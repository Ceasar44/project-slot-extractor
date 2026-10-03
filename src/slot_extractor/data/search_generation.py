"""Versioned raw generation with atomic checkpoints and contract-aware resume."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from slot_extractor.data.coverage_audit import audit_semantic_coverage
from slot_extractor.data.generator import GenerationRequest, RawGenerator, generation_sample_id
from slot_extractor.data.isolation import assert_no_eval_overlap, input_fingerprint
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.raw_schema import raw_response_schema
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.tag_audit import audit_tags
from slot_extractor.prompts.rules import SYSTEM_RULES
from slot_extractor.registry import load_registry
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def generation_requests(config: dict) -> list[GenerationRequest]:
    counts = config.get("counts")
    if not isinstance(counts, dict) or not counts or set(counts) - set(SCENARIOS):
        raise ValueError("counts must map search scenario codes to quotas")
    requests = []
    for scenario, count in counts.items():
        if type(count) is not int or count < 0:
            raise ValueError("scenario quota must be a nonnegative integer")
        for _ in range(count):
            request = GenerationRequest(
                scenario, len(requests) + 1, config.get("split", "train"), config.get("seed", 42)
            )
            generation_sample_id(request)
            requests.append(request)
    if not requests:
        raise ValueError("at least one sample is required")
    return requests


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def generate_raw_dataset(config: dict, backend, output_dir: str | Path, *, strict_audit=False):
    """Generate raw only; SFT rendering belongs to Task 07. Never replace final raw gold."""
    requests = generation_requests(config)
    if not isinstance(config.get("dataset_id"), str) or not config["dataset_id"].strip():
        raise ValueError("dataset_id must be nonempty text")
    registry_path = Path(config["registry_path"])
    registry = load_registry(registry_path)
    concurrency = config.get("generation_concurrency", 1)
    if type(concurrency) is not int or concurrency < 1:
        raise ValueError("generation_concurrency must be a positive integer")
    generator = RawGenerator(backend, registry, config.get("max_attempts", 3))
    # The evaluation set must exist before generating a training corpus.
    eval_records = []
    eval_hash = None
    if config.get("split", "train") != "eval":
        eval_path = Path(config["eval_path"])
        eval_records = list(read_jsonl(eval_path))
        if not eval_records:
            raise ValueError("frozen evaluation dataset must not be empty")
        for record in eval_records:
            raw_sample_from_record(record, registry)
        eval_hash = hashlib.sha256(eval_path.read_bytes()).hexdigest()
    root = Path(output_dir)
    output = root / "samples.jsonl"
    manifest_path = root / "manifest.json"
    if output.exists():
        raise ValueError(f"raw dataset already exists: {output}; use a new version")
    registry_hash = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    identity = {
        "config": config,
        "registry_sha256": registry_hash,
        "eval_sha256": eval_hash,
        "model": backend.model,
        "raw_schema": raw_response_schema(registry),
        "rules": SYSTEM_RULES,
        "scenarios": {k: asdict(v) for k, v in SCENARIOS.items()},
        "implementation_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("generator.py", "tag_audit.py", "search_generation.py")
        },
    }
    signature = _hash(identity)
    checkpoint = root / ".generation_checkpoint.jsonl"
    meta = root / ".generation_checkpoint.meta.json"
    if checkpoint.exists() and not meta.exists():
        raise ValueError("checkpoint has no identity metadata")
    if meta.exists() and json.loads(meta.read_text(encoding="utf-8"))["signature"] != signature:
        raise ValueError("checkpoint config/registry/eval/model contract changed")
    _write_json(meta, {"signature": signature})
    by_id = {generation_sample_id(r): r for r in requests}
    completed = {}
    fingerprints = set()

    def accept(sample):
        request = by_id.get(sample.id)
        if request is None or request.scenario != sample.scenario:
            raise ValueError("checkpoint/generated sample does not match request")
        if sample.id in completed:
            raise ValueError("duplicate checkpoint/generated id")
        if not audit_tags([sample], registry).ok:
            raise ValueError("checkpoint/generated tags differ from gold")
        if {"type": "minimal_patch", "field": None} not in sample.assertions:
            raise ValueError("checkpoint/generated assertions lack minimal_patch")
        if (sample.input["current_search_state"] is not None) != SCENARIOS[
            sample.scenario
        ].multi_turn:
            raise ValueError("checkpoint/generated turn type differs from scenario")
        assert_no_eval_overlap([sample], eval_records)
        fingerprint = input_fingerprint(sample)
        if fingerprint in fingerprints:
            raise ValueError("duplicate generated input; inspect checkpoint and retry")
        fingerprints.add(fingerprint)
        completed[sample.id] = sample

    if checkpoint.exists():
        for record in read_jsonl(checkpoint):
            accept(raw_sample_from_record(record, registry))
    pending = [r for r in requests if generation_sample_id(r) not in completed]
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(generator.generate_one, r) for r in pending]
        for future in as_completed(futures):
            accept(future.result())
            write_jsonl(checkpoint, [completed[i].to_dict() for i in by_id if i in completed])
    samples = [completed[i] for i in by_id]
    coverage = audit_semantic_coverage(samples, registry, config.get("coverage_minimums"))
    _write_json(root / "coverage.json", asdict(coverage))
    if strict_audit and not coverage.ok:
        raise ValueError(f"coverage deficits: {coverage.deficits}")
    write_jsonl(output, [s.to_dict() for s in samples])
    _write_json(
        manifest_path,
        {
            "dataset_id": config["dataset_id"],
            "registry_version": registry.registry_version,
            "registry_sha256": registry_hash,
            "eval_sha256": eval_hash,
            "signature": signature,
            "seed": config.get("seed", 42),
            "model": backend.model,
            "sample_count": len(samples),
            "raw_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "scenario_counts": coverage.scenarios,
            "coverage_ok": coverage.ok,
            "gold_review_required": True,
        },
    )
    return output
