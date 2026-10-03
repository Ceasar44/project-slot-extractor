"""Registry-aware search raw to SFT build; historical appointment builds are explicit."""

import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from slot_extractor.data.coverage_audit import SemanticCoverageReport, audit_semantic_coverage
from slot_extractor.data.isolation import assert_no_eval_overlap, input_fingerprint
from slot_extractor.data.raw_sample import RawSample, raw_sample_from_record
from slot_extractor.data.sft_render import render_sft
from slot_extractor.data.tag_audit import TagAuditReport, audit_tags
from slot_extractor.registry import Registry, load_registry
from slot_extractor.schemas.dataset_contract import validate_dataset_against_contract
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


@dataclass(frozen=True)
class BuildResult:
    raw_samples: Path
    sft_train: Path
    sft_val: Path
    dataset_info: Path
    version_card: Path
    manifest: Path
    raw_count: int
    train_count: int
    val_count: int
    audit: TagAuditReport
    semantic_coverage: SemanticCoverageReport


def _split(samples: list[RawSample], seed: int, val_fraction: float = 0.1):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(val_fraction) not in {int, float} or not 0 < val_fraction < 1:
        raise ValueError("validation fraction must be between zero and one")
    groups = defaultdict(list)
    for sample in samples:
        groups[(sample.scenario, sample.input["current_search_state"] is not None)].append(sample)
    quotas = {
        key: min(len(group) - 1, max(1, int(len(group) * val_fraction))) if len(group) > 1 else 0
        for key, group in groups.items()
    }
    target = min(
        sum(len(g) - 1 for g in groups.values()),
        max(sum(len(g) > 1 for g in groups.values()), round(len(samples) * val_fraction)),
    )
    while sum(quotas.values()) > target:
        candidates = [k for k in groups if quotas[k] > 1]
        key = min(candidates, key=lambda k: (-(quotas[k] - len(groups[k]) * val_fraction), k))
        quotas[key] -= 1
    while sum(quotas.values()) < target:
        candidates = [k for k in groups if quotas[k] < len(groups[k]) - 1]
        key = min(candidates, key=lambda k: (-(len(groups[k]) * val_fraction - quotas[k]), k))
        quotas[key] += 1
    train, validation = [], []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda item: item.id)
        random.Random(f"{seed}:{key}").shuffle(group)
        validation.extend(group[: quotas[key]])
        train.extend(group[quotas[key] :])
    return train, validation


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _slices(samples):
    return {
        "scenarios": dict(sorted(Counter(s.scenario for s in samples).items())),
        "tags": dict(sorted(Counter(t for s in samples for t in s.tags).items())),
        "ids": [s.id for s in samples],
    }


def validate_build_target(output_root: str | Path, version: str) -> None:
    if not isinstance(version, str) or not re.fullmatch(r"baking-v\d+\.\d+(?:\.\d+)?", version):
        raise ValueError("search version must use baking-vX.Y (or baking-vX.Y.Z)")
    root = Path(output_root)
    if (
        any((root / "processed" / suffix / version).exists() for suffix in ("sft", "dpo"))
        or (root / "processed" / version).exists()
    ):
        raise ValueError("processed dataset version already exists; use a new version")


def build_dataset(
    raw_samples: Iterable[RawSample],
    eval_records: Iterable[dict],
    output_root: str | Path,
    version: str,
    seed: int,
    *,
    registry: Registry,
    registry_path: str | Path,
    enable_dpo: bool = False,
    val_fraction: float = 0.1,
    strict_audit: bool = False,
    coverage_minimums: Mapping | None = None,
    source_raw_path: str | Path | None = None,
    eval_path: str | Path | None = None,
) -> BuildResult:
    if type(enable_dpo) is not bool or enable_dpo:
        raise ValueError("search DPO is not implemented; enable_dpo must be false until Task 09")
    validate_build_target(output_root, version)
    registry_path = Path(registry_path)
    if load_registry(registry_path) != registry:
        raise ValueError("registry object differs from registry_path")
    samples, evaluation = list(raw_samples), list(eval_records)
    if not samples or not evaluation:
        raise ValueError("raw samples and frozen search evaluation must be nonempty")
    validate_dataset_against_contract(samples, registry)
    eval_samples = [raw_sample_from_record(r, registry) for r in evaluation]
    validate_dataset_against_contract(eval_samples, registry)
    if {s.id for s in samples} & {s.id for s in eval_samples}:
        raise ValueError("training and evaluation IDs overlap")
    assert_no_eval_overlap(samples, evaluation)
    fingerprints = [input_fingerprint(s) for s in samples]
    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError("duplicate raw input; deduplicate before building")
    audit = audit_tags(samples, registry)
    coverage = audit_semantic_coverage(samples, registry, coverage_minimums)
    if strict_audit and (not audit.ok or not coverage.ok):
        raise ValueError(
            f"search audit failed: tags={audit.mismatched_ids}, coverage={coverage.deficits}"
        )
    train, validation = _split(samples, seed, val_fraction)
    assert_no_eval_overlap(train, validation)
    root = Path(output_root)
    raw_path = root / "raw" / version / "samples.jsonl"
    train_path = root / "processed" / "sft" / version / "train.jsonl"
    val_path = train_path.with_name("val.jsonl")
    meta = root / "processed" / version
    if raw_path.exists():
        if list(read_jsonl(raw_path)) != [s.to_dict() for s in samples]:
            raise ValueError("existing authoritative raw differs from build input")
    source = Path(source_raw_path) if source_raw_path else None
    if source is not None and list(read_jsonl(source)) != [s.to_dict() for s in samples]:
        raise ValueError("source raw file differs from build input")
    if eval_path is not None and list(read_jsonl(eval_path)) != evaluation:
        raise ValueError("evaluation file differs from evaluation records")
    registry_hash = _sha(registry_path)
    eval_hash = (
        _sha(Path(eval_path))
        if eval_path
        else hashlib.sha256(
            json.dumps(evaluation, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    )
    source_manifest = None
    if source is not None and source.with_name("manifest.json").exists():
        source_manifest = json.loads(source.with_name("manifest.json").read_text(encoding="utf-8"))
        if not isinstance(source_manifest, dict):
            raise ValueError("source raw manifest must be an object")
        if (
            source_manifest.get("registry_sha256") != registry_hash
            or source_manifest.get("raw_sha256") != _sha(source)
            or source_manifest.get("sample_count") != len(samples)
            or source_manifest.get("dataset_id") != f"baking-raw-{version.removeprefix('baking-')}"
        ):
            raise ValueError("source raw manifest differs from Registry/raw samples")
        if source_manifest.get("eval_sha256") != eval_hash:
            raise ValueError("source raw manifest differs from frozen evaluation")
    train_rows = [render_sft(s, registry) for s in train]
    val_rows = [render_sft(s, registry) for s in validation]
    token = version.replace("-", "_").replace(".", "_")
    info = {
        f"{token}_{split}": {
            "file_name": f"../sft/{version}/{split}.jsonl",
            "formatting": "sharegpt",
            "columns": {"messages": "conversations", "system": "system"},
            "tags": {
                "role_tag": "from",
                "content_tag": "value",
                "user_tag": "human",
                "assistant_tag": "gpt",
            },
        }
        for split in ("train", "val")
    }
    if not raw_path.exists():
        write_jsonl(raw_path, [dict(sorted(s.to_dict().items())) for s in samples])
    write_jsonl(train_path, train_rows)
    write_jsonl(val_path, val_rows)
    _write_json(meta / "dataset_info.json", info)
    _write_json(meta / "coverage.json", {"tags": asdict(audit), "semantic": asdict(coverage)})
    manifest = {
        "schema_version": 1,
        "dataset_id": f"baking-sft-{version.removeprefix('baking-')}",
        "raw_dataset_id": f"baking-raw-{version.removeprefix('baking-')}",
        "registry_version": registry.registry_version,
        "registry_sha256": registry_hash,
        "eval_sha256": eval_hash,
        "seed": seed,
        "val_fraction": val_fraction,
        "enable_dpo": False,
        "raw_count": len(samples),
        "train_count": len(train),
        "val_count": len(validation),
        "train": _slices(train),
        "val": _slices(validation),
        "source_raw_manifest": source_manifest,
        "source_raw_path": str(source) if source else None,
        "artifacts": {
            "raw_sha256": _sha(raw_path),
            "train_sha256": _sha(train_path),
            "val_sha256": _sha(val_path),
            "dataset_info_sha256": _sha(meta / "dataset_info.json"),
        },
        "renderer_sha256": _sha(Path(__file__).with_name("sft_render.py")),
        "prompt_sha256": _sha(Path(__file__).parents[1] / "prompts" / "rules.py"),
        "prompt_builder_sha256": _sha(Path(__file__).parents[1] / "prompts" / "template.py"),
        "gold_review_required": True,
    }
    card = meta / "DATASET_CARD.md"
    card.write_text(
        f"# Baking search SFT {version}\n\n"
        f"Raw: {len(samples)}; train: {len(train)}; validation: {len(validation)}.\n\n"
        f"Registry: {registry.registry_version}; SHA256: {registry_hash}.\n\n"
        f"Seed: {seed}; scenario and turn strata; validation fraction: {val_fraction}.\n\n"
        "Singleton strata remain in train; other strata retain at least one training sample.\n\n"
        "No tools or DPO. Evaluation overlap: 0. Gold requires semantic review before training.\n",
        encoding="utf-8",
    )
    _write_json(meta / "manifest.json", manifest)
    return BuildResult(
        raw_path,
        train_path,
        val_path,
        meta / "dataset_info.json",
        card,
        meta / "manifest.json",
        len(samples),
        len(train),
        len(validation),
        audit,
        coverage,
    )
