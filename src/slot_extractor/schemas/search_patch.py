"""SearchPatch v1.0 structures and Registry-driven validation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from slot_extractor.registry import FieldSpec, Registry, RegistryError

Scalar = str | int | float | bool | None
PATCH_FIELDS = frozenset(
    {
        "schema_version",
        "reset",
        "query_text",
        "hard_filters",
        "soft_preferences",
        "sort",
        "clear_fields",
        "unmapped_terms",
    }
)
_PAYLOAD_FIELDS = {"field", "value", "values", "min_value", "max_value", "unit"}


class SearchPatchValidationError(ValueError):
    """A search patch or state violates the protocol or catalog contract."""


@dataclass(frozen=True)
class HardFilter:
    field: str
    op: str
    value: Scalar = None
    values: tuple[str, ...] = ()
    min_value: int | float | None = None
    max_value: int | float | None = None
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "op": self.op, **_payload_dict(self)}


@dataclass(frozen=True)
class SoftPreference:
    field: str
    preference: str
    value: Scalar = None
    values: tuple[str, ...] = ()
    min_value: int | float | None = None
    max_value: int | float | None = None
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "preference": self.preference, **_payload_dict(self)}


def _payload_dict(item: HardFilter | SoftPreference) -> dict[str, Any]:
    return {
        "value": item.value,
        "values": list(item.values),
        "min_value": item.min_value,
        "max_value": item.max_value,
        "unit": item.unit,
    }


@dataclass(frozen=True)
class SortSpec:
    field: str
    order: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "order": self.order}


@dataclass(frozen=True)
class SearchPatch:
    schema_version: str = "1.0"
    reset: bool = False
    query_text: str | None = None
    hard_filters: tuple[HardFilter, ...] = ()
    soft_preferences: tuple[SoftPreference, ...] = ()
    sort: SortSpec | None = None
    clear_fields: tuple[str, ...] = ()
    unmapped_terms: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Any, registry: Registry) -> SearchPatch:
        return validate_search_patch(data, registry)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "reset": self.reset,
            "query_text": self.query_text,
            "hard_filters": [f.to_dict() for f in self.hard_filters],
            "soft_preferences": [f.to_dict() for f in self.soft_preferences],
            "sort": self.sort.to_dict() if self.sort else None,
            "clear_fields": list(self.clear_fields),
            "unmapped_terms": list(self.unmapped_terms),
        }


def ensure_exact_fields(data: Any, expected: set[str] | frozenset[str], context: str) -> dict:
    if not isinstance(data, dict) or any(not isinstance(k, str) for k in data):
        raise SearchPatchValidationError(f"{context}: must be an object with string keys")
    if set(data) != expected:
        raise SearchPatchValidationError(
            f"{context}: schema fields mismatch: missing={sorted(expected - data.keys())}, "
            f"extra={sorted(data.keys() - expected)}"
        )
    return data


def ensure_list(data: Any, context: str) -> list:
    if not isinstance(data, list):
        raise SearchPatchValidationError(f"{context}: must be an array")
    return data


def validate_text(value: Any, context: str, limit: int, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SearchPatchValidationError(
            f"{context}: must be a nonempty string of 1–{limit} characters"
        )


def _strings(data: Any, context: str, limit: int) -> tuple[str, ...]:
    items = ensure_list(data, context)
    for item in items:
        validate_text(item, context, limit)
    if len(set(items)) != len(items):
        raise SearchPatchValidationError(f"{context}: duplicate values")
    return tuple(items)


def _number(value: Any, spec: FieldSpec, context: str) -> None:
    if type(value) not in (int, float) or (spec.type == "integer" and type(value) is not int):
        raise SearchPatchValidationError(f"{context}: must be {spec.type}, excluding boolean")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise SearchPatchValidationError(f"{context}: must be finite")
    if spec.minimum is not None and (
        value < spec.minimum or (spec.exclusive_minimum and value == spec.minimum)
    ):
        raise SearchPatchValidationError(f"{context}: below minimum {spec.minimum}")
    if spec.maximum is not None and value > spec.maximum:
        raise SearchPatchValidationError(f"{context}: above maximum {spec.maximum}")


def _unit(unit: Any, spec: FieldSpec, op: str) -> None:
    if unit is None:
        if spec.unit_kind == "mass" and op not in ("lower", "higher"):
            raise SearchPatchValidationError(f"{spec.name}.unit: mass value requires a unit")
        return
    if not isinstance(unit, str) or spec.unit_kind is None:
        raise SearchPatchValidationError(f"{spec.name}.unit: unit not allowed")
    if spec.unit_kind == "mass" and unit not in {u.code for u in spec.units}:
        raise SearchPatchValidationError(f"{spec.name}.unit: unsupported mass unit")
    if spec.unit_kind == "currency" and (
        spec.unit_pattern is None or not re.fullmatch(spec.unit_pattern, unit)
    ):
        raise SearchPatchValidationError(f"{spec.name}.unit: invalid currency code")


def _validate_condition(data: Any, registry: Registry, *, soft: bool) -> dict:
    key = "preference" if soft else "op"
    item = ensure_exact_fields(
        data, _PAYLOAD_FIELDS | {key}, "soft preference" if soft else "hard filter"
    )
    name = item["field"]
    if not isinstance(name, str):
        raise SearchPatchValidationError("field: must be a Registry field code")
    try:
        spec = registry.field(name)
    except RegistryError as exc:
        raise SearchPatchValidationError(str(exc)) from exc
    op = item[key]
    allowed = spec.soft_operators if soft else spec.hard_operators
    if not isinstance(op, str) or op not in allowed:
        raise SearchPatchValidationError(f"{name}.{key}: unsupported operator {op!r}")
    values = ensure_list(item["values"], f"{name}.values")
    _unit(item["unit"], spec, op)
    if op in ("in", "not_in", "prefer", "avoid"):
        if not values or any(item[k] is not None for k in ("value", "min_value", "max_value")):
            raise SearchPatchValidationError(f"{name}: {op} requires only nonempty values")
        if any(not isinstance(v, str) or v not in registry.allowed_values(name) for v in values):
            raise SearchPatchValidationError(f"{name}.values: unknown canonical value")
        if len(set(values)) != len(values):
            raise SearchPatchValidationError(f"{name}.values: duplicate values")
    elif op == "between":
        if values or item["value"] is not None:
            raise SearchPatchValidationError(f"{name}: between requires only min_value/max_value")
        _number(item["min_value"], spec, f"{name}.min_value")
        _number(item["max_value"], spec, f"{name}.max_value")
        if item["min_value"] > item["max_value"]:
            raise SearchPatchValidationError(f"{name}: min_value must be <= max_value")
    elif op in ("lower", "higher"):
        if values or any(item[k] is not None for k in ("value", "min_value", "max_value")):
            raise SearchPatchValidationError(f"{name}: {op} requires empty payload")
    else:
        if values or item["min_value"] is not None or item["max_value"] is not None:
            raise SearchPatchValidationError(f"{name}: {op} requires only value")
        if spec.type == "boolean":
            if type(item["value"]) is not bool:
                raise SearchPatchValidationError(f"{name}.value: must be boolean")
        else:
            _number(item["value"], spec, f"{name}.value")
    return {**item, "values": tuple(values)}


def validate_hard_filter(data: Any, registry: Registry) -> HardFilter:
    return HardFilter(**_validate_condition(data, registry, soft=False))


def validate_soft_preference(data: Any, registry: Registry) -> SoftPreference:
    return SoftPreference(**_validate_condition(data, registry, soft=True))


def validate_sort(data: Any, registry: Registry) -> SortSpec | None:
    if data is None:
        return None
    item = ensure_exact_fields(data, {"field", "order"}, "sort")
    spec = next((s for s in registry.search.sort_fields if s.field == item["field"]), None)
    if spec is None or not isinstance(item["order"], str) or item["order"] not in spec.orders:
        raise SearchPatchValidationError("sort: unsupported field/order")
    return SortSpec(**item)


def validate_clear_fields(data: Any, registry: Registry) -> tuple[str, ...]:
    names = _strings(data, "clear_fields", 128)
    if set(names) - registry.clearable_fields():
        raise SearchPatchValidationError("clear_fields: unsupported field")
    return names


def validate_search_patch(data: Any, registry: Registry) -> SearchPatch:
    item = ensure_exact_fields(data, PATCH_FIELDS, "SearchPatch")
    if item["schema_version"] != "1.0":
        raise SearchPatchValidationError("schema_version: must be string '1.0'")
    if type(item["reset"]) is not bool:
        raise SearchPatchValidationError("reset: must be boolean")
    validate_text(item["query_text"], "query_text", 128, nullable=True)
    hard = tuple(
        validate_hard_filter(f, registry) for f in ensure_list(item["hard_filters"], "hard_filters")
    )
    soft = tuple(
        validate_soft_preference(f, registry)
        for f in ensure_list(item["soft_preferences"], "soft_preferences")
    )
    unmapped = _strings(item["unmapped_terms"], "unmapped_terms", 64)
    if len(unmapped) > 5:
        raise SearchPatchValidationError("unmapped_terms: at most 5 terms")
    return SearchPatch(
        reset=item["reset"],
        query_text=item["query_text"],
        hard_filters=hard,
        soft_preferences=soft,
        sort=validate_sort(item["sort"], registry),
        clear_fields=validate_clear_fields(item["clear_fields"], registry),
        unmapped_terms=unmapped,
    )
