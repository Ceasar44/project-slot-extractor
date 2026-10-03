"""Schema validation with API-friendly paths, codes and deterministic conflicts."""

from dataclasses import dataclass
from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import (
    PATCH_FIELDS,
    HardFilter,
    SearchPatch,
    SearchPatchValidationError,
    SoftPreference,
    ensure_exact_fields,
    validate_hard_filter,
    validate_search_patch,
    validate_soft_preference,
)
from slot_extractor.schemas.search_state import SearchState, validate_search_state

from .unit_normalizer import UnitNormalizationError, normalize_condition


@dataclass(frozen=True)
class ValidationError:
    code: str
    path: str
    message: str


class SearchValidationError(SearchPatchValidationError):
    def __init__(self, errors: tuple[ValidationError, ...]):
        self.errors = errors
        super().__init__("; ".join(f"{e.path}: {e.message}" for e in errors))


def expand_hierarchy(field: str, values: tuple[str, ...], registry: Registry) -> tuple[str, ...]:
    """Expand same-field descendants only; never infer allergen from flavor."""
    spec = registry.field(field)
    selected = set(values)
    if spec.parent_field is None:
        while True:
            added = {v.code for v in spec.values if v.parent in selected} - selected
            if not added:
                break
            selected.update(added)
    return tuple(v.code for v in spec.values if v.code in selected)


def _schema_error(exc: Exception, path: str) -> ValidationError:
    message = str(exc)
    code = "invalid_shape"
    for fragment, candidate in (
        ("unknown field", "unknown_field"),
        ("unsupported operator", "invalid_operator"),
        ("canonical value", "unknown_value"),
        ("unit", "invalid_unit"),
        ("currency", "invalid_unit"),
        ("minimum", "invalid_range"),
        ("maximum", "invalid_range"),
        ("min_value must", "invalid_range"),
        ("schema_version", "invalid_version"),
        ("must be", "invalid_type"),
        ("duplicate", "duplicate_value"),
    ):
        if fragment in message:
            code = candidate
            break
    return ValidationError(code, path, message)


def condition_conflicts(
    hard: tuple[HardFilter, ...],
    soft: tuple[SoftPreference, ...],
    registry: Registry,
) -> tuple[ValidationError, ...]:
    errors = []
    for spec in registry.fields:
        conditions = [f for f in hard if f.field == spec.name]
        preferences = [f for f in soft if f.field == spec.name]
        path = f"hard_filters.{spec.name}"
        conflict = False
        if spec.type == "categorical":
            excluded = set().union(
                *(
                    set(expand_hierarchy(spec.name, f.values, registry))
                    for f in conditions
                    if f.op == "not_in"
                )
            )
            conflict = any(
                set(expand_hierarchy(spec.name, f.values, registry)) <= excluded
                for f in conditions
                if f.op == "in"
            )
        elif spec.type == "boolean":
            conflict = len({f.value for f in conditions}) > 1
        else:
            currencies = {f.unit for f in (*conditions, *preferences) if f.unit is not None}
            if spec.unit_kind == "currency" and len(currencies) > 1:
                errors.append(
                    ValidationError("mixed_currency", path, "cannot compare different currencies")
                )
                continue
            try:
                conditions = [normalize_condition(f, registry) for f in conditions]
            except UnitNormalizationError as exc:
                errors.append(ValidationError("invalid_unit", path, str(exc)))
                continue
            try:
                for preference in preferences:
                    normalize_condition(preference, registry)
            except UnitNormalizationError as exc:
                errors.append(
                    ValidationError(
                        "invalid_unit",
                        f"soft_preferences.{spec.name}",
                        str(exc),
                    )
                )
                continue
            low, high = float("-inf"), float("inf")
            for item in conditions:
                if item.op in ("eq", "gte"):
                    low = max(low, item.value)
                if item.op in ("eq", "lte"):
                    high = min(high, item.value)
                if item.op == "between":
                    low, high = max(low, item.min_value), min(high, item.max_value)
            conflict = low > high
        if conflict:
            errors.append(
                ValidationError(
                    "conflicting_filters", path, "hard conditions cannot all be satisfied"
                )
            )
        prefer = {v for f in preferences if f.preference == "prefer" for v in f.values}
        avoid = {v for f in preferences if f.preference == "avoid" for v in f.values}
        directions = {f.preference for f in preferences}
        if prefer & avoid or {"lower", "higher"} <= directions:
            errors.append(
                ValidationError(
                    "conflicting_preferences",
                    f"soft_preferences.{spec.name}",
                    "opposing soft preferences",
                )
            )
    return tuple(errors)


def collect_validation_errors(data: Any, registry: Registry) -> tuple[ValidationError, ...]:
    if isinstance(data, SearchPatch):
        data = data.to_dict()
    try:
        ensure_exact_fields(data, PATCH_FIELDS, "SearchPatch")
    except SearchPatchValidationError as exc:
        return (_schema_error(exc, "$"),)
    errors = []
    for key in sorted(PATCH_FIELDS - {"hard_filters", "soft_preferences"}):
        candidate = SearchPatch().to_dict()
        candidate[key] = data[key]
        try:
            validate_search_patch(candidate, registry)
        except SearchPatchValidationError as exc:
            errors.append(_schema_error(exc, key))
    for key, validator in (
        ("hard_filters", validate_hard_filter),
        ("soft_preferences", validate_soft_preference),
    ):
        if not isinstance(data[key], list):
            errors.append(ValidationError("invalid_type", key, "must be an array"))
            continue
        for index, item in enumerate(data[key]):
            try:
                validator(item, registry)
            except SearchPatchValidationError as exc:
                errors.append(_schema_error(exc, f"{key}[{index}]"))
    if errors:
        return tuple(errors)
    parsed = validate_search_patch(data, registry)
    return condition_conflicts(parsed.hard_filters, parsed.soft_preferences, registry)


def validate_patch(data: Any, registry: Registry) -> SearchPatch:
    errors = collect_validation_errors(data, registry)
    if errors:
        raise SearchValidationError(errors)
    return validate_search_patch(
        data.to_dict() if isinstance(data, SearchPatch) else data, registry
    )


def validate_state(data: Any, registry: Registry) -> SearchState:
    try:
        state = validate_search_state(
            data.to_dict() if isinstance(data, SearchState) else data, registry
        )
    except SearchPatchValidationError as exc:
        raise SearchValidationError((_schema_error(exc, "state"),)) from exc
    errors = condition_conflicts(state.hard_filters, state.soft_preferences, registry)
    if errors:
        raise SearchValidationError(errors)
    return state
