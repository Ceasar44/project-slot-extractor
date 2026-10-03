"""Explicit validator for historical appointment evaluation datasets."""

import argparse
import sys

from slot_extractor.schemas.legacy_dataset_contract import (
    load_dataset_contract,
    validate_dataset_against_contract,
)
from slot_extractor.schemas.legacy_sample import load_samples


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="data/eval/test.jsonl")
    parser.add_argument("--contract", default="data/eval/dataset_contract.json")
    args = parser.parse_args(argv)
    try:
        samples = load_samples(args.cases)
        contract = load_dataset_contract(args.contract)
        validate_dataset_against_contract(samples, contract)
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Validated {len(samples)} historical appointment cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
