"""Strict raw validation, including deterministic gold consistency checks."""

from slot_extractor.registry import Registry
from slot_extractor.schemas.dataset_contract import validate_sample_against_contract
from slot_extractor.schemas.sample import Sample


class RawValidationError(ValueError):
    pass


def validate_raw_sample(sample: Sample, registry: Registry) -> None:
    errors = validate_sample_against_contract(sample, registry)
    if errors:
        raise RawValidationError("\n".join(errors))
