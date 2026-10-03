from __future__ import annotations

import argparse
import sys
from pathlib import Path

from slot_extractor.schemas.dataset_contract import (
    DatasetContractError,
    load_dataset_contract,
    validate_dataset_against_contract,
)
from slot_extractor.schemas.sample import load_samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate baking search cases against Registry.")
    parser.add_argument("--cases", default="data/eval/baking-v1.0/test.jsonl")
    parser.add_argument("--contract", default="configs/catalog/registry.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        contract = load_dataset_contract(Path(args.contract))
        samples = load_samples(Path(args.cases), contract)
        if not samples:
            raise DatasetContractError("search dataset must be nonempty")
        validate_dataset_against_contract(samples, contract)
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Validated {len(samples)} search cases against Registry {contract.registry_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
