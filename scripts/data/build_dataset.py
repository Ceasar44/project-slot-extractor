"""Build baking search SFT from raw input or the Task 06 generation pipeline."""

import argparse
import sys
from pathlib import Path

import yaml

from slot_extractor.data.dataset_build import _split, build_dataset, validate_build_target
from slot_extractor.data.diversity_audit import audit_diversity
from slot_extractor.data.generation_quality import validate_generation_quality
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.search_generation import (
    generate_raw_dataset,
    generation_requests,
    prepare_generation_plan,
)
from slot_extractor.inference.factory import build_backend_from_config
from slot_extractor.registry import load_registry
from slot_extractor.utils.jsonl import read_jsonl


def _parser():
    parser = argparse.ArgumentParser(description="Build baking search SFT datasets")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root")
    parser.add_argument("--dry-run", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--raw-input")
    mode.add_argument("--generate", action="store_true")
    mode.add_argument("--mock", action="store_true")
    parser.add_argument("--strict-audit", action="store_true")
    return parser


def _load_config(path):
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("search build config must be an object")
    if value.get("enable_dpo", False) is not False or value.get("dpo_target_counts"):
        raise ValueError("search DPO must be disabled until Task 09")
    if value.get("split", "train") != "train":
        raise ValueError("SFT builder requires training raw data, not evaluation generation")
    return value


def _generation_requests(config):
    return generation_requests(config)


def run(args):
    config = _load_config(args.config)
    registry = load_registry(config["registry_path"])
    root = Path(args.output_root or config["output_root"])
    version = config["version"]
    validate_build_target(root, version)
    _split([], config["seed"], config.get("val_fraction", 0.1))
    expected_id = f"baking-raw-{version.removeprefix('baking-')}"
    if config.get("dataset_id", expected_id) != expected_id:
        raise ValueError("raw dataset_id differs from search build version")
    if args.dry_run:
        prepare_generation_plan(config, registry)
        requests = _generation_requests(config)
        print(f"search_sft version={version} samples={len(requests)} enable_dpo=false")
        return 0
    if args.raw_input:
        source = Path(args.raw_input)
    elif args.generate or args.mock:
        key = "mock_inference_config" if args.mock else "generate_inference_config"
        if key not in config:
            raise ValueError(f"search config must define {key}")
        source = generate_raw_dataset(
            config,
            build_backend_from_config(config[key]),
            root / "raw" / version,
            strict_audit=args.strict_audit,
        )
    else:
        raise ValueError("choose --raw-input, --generate or --mock explicitly")
    samples = [raw_sample_from_record(r, registry) for r in read_jsonl(source)]
    plans, _ = prepare_generation_plan(config, registry)
    if plans:
        plan_by_id = {plan.id: plan for plan in plans}
        if len(samples) != len(plans) or {sample.id for sample in samples} != set(plan_by_id):
            raise ValueError("raw samples do not fulfill the complete planned quota")
        audit_rows = []
        for sample in samples:
            plan = plan_by_id[sample.id]
            validate_generation_quality(sample, registry, plan=plan)
            audit_rows.append(dict(sample.to_dict(), language=plan.language, style=plan.style))
        diversity = audit_diversity(audit_rows, registry, config.get("diversity"))
        if not diversity["ok"]:
            raise ValueError(f"raw diversity deficits: {diversity['deficits']}")
    evaluation = list(read_jsonl(config["eval_path"]))
    result = build_dataset(
        samples,
        evaluation,
        root,
        version,
        config["seed"],
        registry=registry,
        registry_path=config["registry_path"],
        enable_dpo=config.get("enable_dpo", False),
        val_fraction=config.get("val_fraction", 0.1),
        strict_audit=args.strict_audit,
        coverage_minimums=config.get("coverage_minimums"),
        source_raw_path=source,
        eval_path=config["eval_path"],
    )
    print(f"raw={result.raw_count}, sft_train={result.train_count}, sft_val={result.val_count}")
    print("enable_dpo=false eval_overlap=0")
    for path in (result.sft_train, result.sft_val, result.dataset_info, result.manifest):
        print(path)
    return 0


def main():
    try:
        return run(_parser().parse_args())
    except Exception as exc:
        print(f"search build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
