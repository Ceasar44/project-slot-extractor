"""Generate baking search raw gold; no training or paid calls during validation."""

import argparse
import sys
from pathlib import Path

import yaml

from slot_extractor.data.search_generation import (
    generate_raw_dataset,
    generation_requests,
    prepare_generation_plan,
)
from slot_extractor.inference.factory import build_backend_from_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate baking search raw gold")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict-audit", action="store_true")
    parser.add_argument(
        "--resume-backend-from-identity",
        help="Verified previous identity JSON for an explicit backend change",
    )
    parser.add_argument(
        "--validate-resume",
        action="store_true",
        help="Validate and save resume metadata without calling the model",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first exhausted sample validation retry",
    )
    args = parser.parse_args()
    try:
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("generation config must be an object")
        if args.dry_run:
            _, audit = prepare_generation_plan(config)
            print(
                f"dataset={config['dataset_id']} samples={len(generation_requests(config))} "
                f"scenarios={len(config['counts'])}"
            )
            if audit:
                import json

                print(
                    json.dumps(
                        {
                            "plan_sha256": audit["plan_sha256"],
                            "diversity_ok": audit["ok"],
                            "scenarios": {
                                name: {
                                    "count": item["count"],
                                    "field_combinations": len(item["field_combinations"]),
                                    "semantic_unique_ratio": item["semantic_unique_ratio"],
                                    "example_anchors": item["example_anchors"],
                                }
                                for name, item in audit["scenarios"].items()
                            },
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            return 0
        backend = build_backend_from_config(config["generate_inference_config"])
        previous_identity = None
        if args.resume_backend_from_identity:
            import json

            previous_identity = json.loads(
                Path(args.resume_backend_from_identity).read_text(encoding="utf-8")
            )
        output = generate_raw_dataset(
            config,
            backend,
            args.output_dir or config["output_dir"],
            strict_audit=args.strict_audit,
            fail_fast=args.fail_fast,
            resume_backend_identity=previous_identity,
            validate_resume=args.validate_resume,
        )
        print(output)
        return 0 if args.validate_resume or output.name == "samples.jsonl" else 2
    except Exception as exc:
        print(f"search raw generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
