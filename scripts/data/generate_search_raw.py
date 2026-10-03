"""Generate baking search raw gold; no training or paid calls during validation."""

import argparse
import sys
from pathlib import Path

import yaml

from slot_extractor.data.search_generation import generate_raw_dataset, generation_requests
from slot_extractor.inference.factory import build_backend_from_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate baking search raw gold")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict-audit", action="store_true")
    args = parser.parse_args()
    try:
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("generation config must be an object")
        if args.dry_run:
            print(
                f"dataset={config['dataset_id']} samples={len(generation_requests(config))} "
                f"scenarios={len(config['counts'])}"
            )
            return 0
        backend = build_backend_from_config(config["generate_inference_config"])
        output = generate_raw_dataset(
            config, backend, args.output_dir or config["output_dir"], strict_audit=args.strict_audit
        )
        print(output)
        return 0
    except Exception as exc:
        print(f"search raw generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
