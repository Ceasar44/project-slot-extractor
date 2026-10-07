"""Verify a published search dataset's hashes, Registry, contract and registry entry."""

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from slot_extractor.data.coverage_audit import audit_semantic_coverage
from slot_extractor.data.tag_audit import audit_tags
from slot_extractor.registry import load_registry
from slot_extractor.schemas.dataset_contract import validate_dataset_against_contract
from slot_extractor.schemas.sample import load_samples


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    checks = {
        manifest["cases_path"]: manifest["cases_sha256"],
        manifest["registry_path"]: manifest["registry_sha256"],
        manifest["source_path"]: manifest["source_sha256"],
        **manifest["artifact_sha256"],
    }
    for path, expected in checks.items():
        if digest(path) != expected:
            raise ValueError(f"frozen hash mismatch: {path}")
    cases_path = Path(manifest["cases_path"])
    if (
        cases_path.with_suffix(".sha256").read_text(encoding="ascii").strip()
        != checks[manifest["cases_path"]]
    ):
        raise ValueError("test.sha256 mismatch")
    registry = load_registry(manifest["registry_path"])
    samples = load_samples(cases_path, registry)
    validate_dataset_against_contract(samples, registry)
    if len(samples) != manifest["sample_count"]:
        raise ValueError("sample count mismatch")
    if not audit_tags(samples, registry).ok or not audit_semantic_coverage(samples, registry).ok:
        raise ValueError("tag or coverage audit failed")
    registrations = yaml.safe_load(Path("data/dataset-registry.yaml").read_text(encoding="utf-8"))
    entry = next(e for e in registrations["datasets"] if e["dataset_id"] == manifest["dataset_id"])
    for key, expected in {
        "status": "frozen",
        "path": manifest["cases_path"],
        "sha256": manifest["cases_sha256"],
        "review_status": manifest["review_status"],
        "baseline_status": manifest["baseline_status"],
    }.items():
        if entry.get(key) != expected:
            raise ValueError(f"dataset registration mismatch: {key}")
    return {
        "dataset_id": manifest["dataset_id"],
        "samples": len(samples),
        "hashes_checked": len(checks),
        "review_status": manifest["review_status"],
        "baseline_status": manifest["baseline_status"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/eval/baking-v1.0/manifest.json")
    args = parser.parse_args()
    print(json.dumps(verify(args.manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
