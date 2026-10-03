"""Authoritative raw gold shares the six-field SearchPatch dataset contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.schemas.sample import SAMPLE_FIELDS, Sample, sample_from_record

RAW_FIELDS = SAMPLE_FIELDS


@dataclass(frozen=True)
class RawSample(Sample):
    """Unrendered question, gold patch and parameterized scoring points."""


def raw_sample_from_record(record: Any, registry: Registry) -> RawSample:
    return RawSample(**sample_from_record(record, registry).to_dict())
