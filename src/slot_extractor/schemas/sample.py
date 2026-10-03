"""Search dataset samples; metadata never enters the model input."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.utils.jsonl import read_jsonl

SAMPLE_FIELDS = frozenset({"id", "scenario", "tags", "input", "expected", "assertions"})


@dataclass(frozen=True)
class Sample:
    id: str
    scenario: str
    tags: list[str]
    input: dict[str, Any]
    expected: dict[str, Any]
    assertions: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return deepcopy({name: getattr(self, name) for name in SAMPLE_FIELDS})


def sample_from_record(record: Any, registry: Registry) -> Sample:
    from .dataset_contract import DatasetContractError, validate_record_against_contract

    errors = validate_record_against_contract(record, registry)
    if errors:
        raise DatasetContractError("\n".join(errors))
    return Sample(**deepcopy(record))


def load_samples(path: str | Path, registry: Registry) -> list[Sample]:
    from .dataset_contract import validate_dataset_against_contract

    samples = [sample_from_record(record, registry) for record in read_jsonl(path)]
    validate_dataset_against_contract(samples, registry)
    return samples
