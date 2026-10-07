"""Versioned raw generation with atomic checkpoints and contract-aware resume."""

import hashlib
import json
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict
from pathlib import Path

from slot_extractor.data.coverage_audit import audit_semantic_coverage
from slot_extractor.data.diversity_audit import audit_diversity, audit_plans
from slot_extractor.data.generation_plan import build_generation_plan, interleave_requests
from slot_extractor.data.generation_quality import (
    generation_response_schema,
    validate_generation_quality,
)
from slot_extractor.data.generator import (
    GenerationError,
    GenerationRequest,
    RawGenerator,
    generation_sample_id,
)
from slot_extractor.data.isolation import IsolationError, assert_no_eval_overlap, input_fingerprint
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.tag_audit import audit_tags
from slot_extractor.prompts.rules import SYSTEM_RULES
from slot_extractor.registry import load_registry
from slot_extractor.utils.jsonl import read_jsonl, replace_with_retry, write_jsonl


class DuplicateInputError(ValueError):
    """A generated utterance duplicates an already accepted sample."""


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
    replace_with_retry(temporary, path)


def prepare_generation_plan(config, registry=None):
    options = config.get("planning", {})
    if not isinstance(options, dict) or type(options.get("enabled", False)) is not bool:
        raise ValueError("planning.enabled must be boolean")
    if not options.get("enabled", False):
        return None, None
    if config.get("version") == "baking-v1.0":
        raise ValueError("planned generation requires a new training version, not baking-v1.0")
    registry = registry or load_registry(config["registry_path"])
    plans = build_generation_plan(config, registry)
    report = audit_plans(plans, registry, config.get("diversity"))
    if not report["ok"]:
        raise ValueError(f"infeasible diversity plan: {report['deficits']}")
    return plans, report


def generate_raw_dataset(
    config: dict, backend, output_dir: str | Path, *, strict_audit=False, fail_fast=False
):
    """Generate raw only; SFT rendering belongs to Task 07. Never replace final raw gold."""
    requests = generation_requests(config)
    if not isinstance(config.get("dataset_id"), str) or not config["dataset_id"].strip():
        raise ValueError("dataset_id must be nonempty text")
    registry_path = Path(config["registry_path"])
    registry = load_registry(registry_path)
    plans, plan_audit = prepare_generation_plan(config, registry)
    plan_by_id = {plan.id: plan for plan in plans or []}
    concurrency = config.get("generation_concurrency", 1)
    if type(concurrency) is not int or concurrency < 1:
        raise ValueError("generation_concurrency must be a positive integer")
    duplicate_retries = config.get("max_duplicate_retries", 3)
    if type(duplicate_retries) is not int or duplicate_retries < 0:
        raise ValueError("max_duplicate_retries must be a nonnegative integer")
    generator = RawGenerator(
        backend,
        registry,
        config.get("max_attempts", 3),
        diagnostics_dir=Path(output_dir) / "diagnostics" if plans else None,
    )
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
        "raw_schema": generation_response_schema(registry),
        "rules": SYSTEM_RULES,
        "scenarios": {k: asdict(v) for k, v in SCENARIOS.items()},
        "implementation_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in (
                "generator.py",
                "tag_audit.py",
                "search_generation.py",
                "generation_quality.py",
            )
        },
    }
    if plans:
        identity["plan_sha256"] = plan_audit["plan_sha256"]
        identity["backend"] = {
            "type": type(backend).__name__,
            "model": backend.model,
            "base_url_sha256": _hash(getattr(backend, "_base_url", None)),
            "reasoning": getattr(backend, "_reasoning", None),
            "temperature": getattr(backend, "_temperature", None),
            "max_retry_tokens": getattr(backend, "_max_retry_tokens", None),
            "default_max_tokens": getattr(
                getattr(backend, "_default_params", None), "max_tokens", None
            ),
        }
        backend_source = getattr(sys.modules.get(type(backend).__module__), "__file__", None)
        identity["backend"]["implementation_sha256"] = (
            hashlib.sha256(Path(backend_source).read_bytes()).hexdigest()
            if backend_source and Path(backend_source).is_file()
            else None
        )
        for name in ("generation_plan.py", "diversity_audit.py"):
            identity["implementation_sha256"][name] = hashlib.sha256(
                Path(__file__).with_name(name).read_bytes()
            ).hexdigest()
    signature = _hash(identity)
    checkpoint = root / ".generation_checkpoint.jsonl"
    meta = root / ".generation_checkpoint.meta.json"
    if checkpoint.exists() and not meta.exists():
        raise ValueError("checkpoint has no identity metadata")
    if meta.exists():
        stored_signature = json.loads(meta.read_text(encoding="utf-8"))["signature"]
        # This scheduler-only update preserves the previous validation contract.
        # Accept only the exact preceding implementation with all other hashes unchanged.
        previous_identity = dict(identity)
        previous_identity["implementation_sha256"] = dict(identity["implementation_sha256"])
        previous_identity["implementation_sha256"]["search_generation.py"] = (
            "84e91e1ec47ed6338ef4f09d172d7a27d469622d91d82526e2f5ce18f59f7468"
        )
        if stored_signature not in {signature, _hash(previous_identity)}:
            raise ValueError("checkpoint config/registry/eval/model contract changed")
    if plans:
        plan_path = root / "generation_plan.jsonl"
        rows = [plan.to_dict() for plan in plans]
        if plan_path.exists():
            if list(read_jsonl(plan_path)) != rows:
                raise ValueError("persisted generation plan differs from current contract")
        else:
            if checkpoint.exists():
                raise ValueError("planned checkpoint is missing generation_plan.jsonl")
            write_jsonl(plan_path, rows)
        _write_json(root / "plan_audit.json", plan_audit)
    _write_json(meta, {"signature": signature})
    by_id = {generation_sample_id(r): r for r in requests}
    completed = {}
    failures = {}
    failures_path = root / "generation_failures.json"
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
        validate_generation_quality(sample, registry, plan=plan_by_id.get(sample.id))
        if plans:
            plan_by_id[sample.id].assert_matches(sample.to_dict())
        assert_no_eval_overlap([sample], eval_records)
        fingerprint = input_fingerprint(sample)
        if fingerprint in fingerprints:
            raise DuplicateInputError("duplicate generated input")
        fingerprints.add(fingerprint)
        completed[sample.id] = sample

    if checkpoint.exists():
        for record in read_jsonl(checkpoint):
            accept(raw_sample_from_record(record, registry))
    pending = [r for r in requests if generation_sample_id(r) not in completed]
    if plans:
        pending = interleave_requests(pending)
    print(
        f"Raw generation: {len(completed)}/{len(requests)} completed; "
        f"{len(pending)} pending; concurrency={concurrency}; model={backend.model}",
        file=sys.stderr,
        flush=True,
    )
    executor = ThreadPoolExecutor(max_workers=concurrency)
    try:
        remaining = iter(pending)
        futures = {}

        def submit(request, rejected_sample=None):
            kwargs = {"rejected_sample": rejected_sample} if rejected_sample else {}
            if plans:
                kwargs["plan"] = plan_by_id[generation_sample_id(request)]
            return executor.submit(generator.generate_one, request, **kwargs)

        def submit_next():
            request = next(remaining, None)
            if request is not None:
                futures[submit(request)] = (request, 0)

        def skip(request, exc):
            sample_id = generation_sample_id(request)
            failures[sample_id] = {"id": sample_id, "scenario": request.scenario, "error": str(exc)}
            _write_json(failures_path, {"failures": list(failures.values())})
            print(
                f"Raw generation: {sample_id} skipped: {exc}; "
                f"{len(completed)} completed, {len(failures)} failed; continuing",
                file=sys.stderr,
                flush=True,
            )
            submit_next()

        for _ in range(concurrency):
            submit_next()
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                request, retries = futures.pop(future)
                try:
                    sample = future.result()
                except GenerationError as exc:
                    if fail_fast:
                        raise
                    skip(request, exc)
                    continue
                try:
                    accept(sample)
                except (DuplicateInputError, IsolationError) as exc:
                    if retries >= duplicate_retries:
                        error = ValueError(
                            f"{sample.id}: {exc}; exhausted {duplicate_retries} duplicate retries"
                        )
                        if fail_fast:
                            raise error from exc
                        skip(request, error)
                        continue
                    print(
                        f"Raw generation: {sample.id}: {exc}; "
                        f"rewriting {retries + 1}/{duplicate_retries}",
                        file=sys.stderr,
                        flush=True,
                    )
                    retry = submit(request, rejected_sample=sample)
                    futures[retry] = (request, retries + 1)
                    continue
                write_jsonl(checkpoint, [completed[i].to_dict() for i in by_id if i in completed])
                print(
                    f"Raw generation: {len(completed)}/{len(requests)} checkpoint saved",
                    file=sys.stderr,
                    flush=True,
                )
                submit_next()
    except BaseException as exc:
        print(
            f"Raw generation interrupted: {exc}\n"
            "Cancelling queued requests; waiting for requests already in flight.",
            file=sys.stderr,
            flush=True,
        )
        executor.shutdown(wait=True, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)
    _write_json(failures_path, {"failures": list(failures.values())})
    if failures:
        # Keep the full quota pending; never publish an incomplete training corpus.
        write_jsonl(checkpoint, [completed[i].to_dict() for i in by_id if i in completed])
        print(
            f"Raw generation incomplete: {len(completed)}/{len(requests)} completed; "
            f"{len(failures)} skipped. Saved checkpoint and {failures_path}; "
            "rerun the same command to retry missing samples.",
            file=sys.stderr,
            flush=True,
        )
        return checkpoint
    samples = [completed[i] for i in by_id]
    coverage = audit_semantic_coverage(samples, registry, config.get("coverage_minimums"))
    _write_json(root / "coverage.json", asdict(coverage))
    if strict_audit and not coverage.ok:
        raise ValueError(f"coverage deficits: {coverage.deficits}")
    if plans:
        audit_rows = [
            dict(
                sample.to_dict(),
                language=plan_by_id[sample.id].language,
                style=plan_by_id[sample.id].style,
            )
            for sample in samples
        ]
        diversity = audit_diversity(audit_rows, registry, config.get("diversity"))
        _write_json(root / "diversity.json", diversity)
        if not diversity["ok"]:
            raise ValueError(f"diversity deficits: {diversity['deficits']}")
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
            **(
                {
                    "plan_sha256": plan_audit["plan_sha256"],
                    "diversity_ok": True,
                    "backend": identity["backend"],
                    "gold_review_status": "pending_independent_semantic_review",
                }
                if plans
                else {}
            ),
        },
    )
    return output
