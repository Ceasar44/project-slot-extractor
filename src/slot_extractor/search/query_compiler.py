"""Compile hard conditions to Typesense parameters, soft ones to ranking hints."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import (
    HardFilter,
    SoftPreference,
    validate_hard_filter,
    validate_soft_preference,
)

from .unit_normalizer import UnitNormalizationError, normalize_condition
from .validator import expand_hierarchy, validate_state


class QueryCompileError(ValueError):
    """Search cannot be compiled without a valid runtime/index contract."""


@dataclass(frozen=True)
class CompiledQuery:
    parameters: dict[str, str]
    ranking_hints: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameters": dict(self.parameters),
            "ranking_hints": [
                dict(hint, values=list(hint["values"])) for hint in self.ranking_hints
            ],
        }


def _normalize(
    item: HardFilter | SoftPreference, registry: Registry, currency: str | None
) -> HardFilter | SoftPreference:
    spec = registry.field(item.field)
    if spec.unit_kind == "currency" and currency is None:
        raise QueryCompileError(f"{item.field}: index currency is required")
    try:
        return normalize_condition(item, registry, default_currency=currency)
    except UnitNormalizationError as exc:
        raise QueryCompileError(str(exc)) from exc


def _numeric(value: int | float | bool) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    return format(Decimal(str(value)), "f")


def compile_hard_filter(data: Any, registry: Registry, *, currency: str | None = None) -> str:
    item = validate_hard_filter(data.to_dict() if isinstance(data, HardFilter) else data, registry)
    item = _normalize(item, registry, currency)
    index = registry.field(item.field).index_field
    if item.op in ("in", "not_in"):
        # Registry canonical codes allow only [a-z][a-z0-9_]*; no raw user text enters filters.
        values = expand_hierarchy(item.field, item.values, registry)
        operator = ":=" if item.op == "in" else ":!="
        return f"{index}{operator}[{','.join(values)}]"
    if item.op == "between":
        return f"{index}:[{_numeric(item.min_value)}..{_numeric(item.max_value)}]"
    operator = {"eq": "=", "gte": ">=", "lte": "<="}[item.op]
    return f"{index}:{operator}{_numeric(item.value)}"


def build_soft_ranking(
    preferences: tuple[SoftPreference, ...] | list[dict[str, Any]],
    registry: Registry,
    *,
    currency: str | None = None,
) -> tuple[dict[str, Any], ...]:
    hints = []
    for data in preferences:
        item = validate_soft_preference(
            data.to_dict() if isinstance(data, SoftPreference) else data,
            registry,
        )
        item = _normalize(item, registry, currency)
        hint = item.to_dict()
        hint["index_field"] = registry.field(item.field).index_field
        hints.append(hint)
    return tuple(hints)


def compile_typesense_query(
    data: Any,
    registry: Registry,
    *,
    currency: str | None = None,
) -> CompiledQuery:
    state = validate_state(data, registry)
    parameters = {
        "q": state.query_text if state.query_text is not None else "*",
        "query_by": ",".join(registry.search.query_fields),
    }
    if state.hard_filters:
        parameters["filter_by"] = " && ".join(
            compile_hard_filter(item, registry, currency=currency) for item in state.hard_filters
        )
    if state.sort is not None:
        sort = next(s for s in registry.search.sort_fields if s.field == state.sort.field)
        parameters["sort_by"] = f"{sort.index_field}:{state.sort.order}"
    return CompiledQuery(
        parameters,
        build_soft_ranking(
            state.soft_preferences,
            registry,
            currency=currency,
        ),
    )
