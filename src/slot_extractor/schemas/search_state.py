"""Persistent search conditions; patch commands never become stored state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from slot_extractor.registry import Registry

from .search_patch import (
    HardFilter,
    SoftPreference,
    SortSpec,
    ensure_exact_fields,
    ensure_list,
    validate_hard_filter,
    validate_soft_preference,
    validate_sort,
    validate_text,
)

STATE_FIELDS = frozenset({"query_text", "hard_filters", "soft_preferences", "sort"})


@dataclass(frozen=True)
class SearchState:
    query_text: str | None = None
    hard_filters: tuple[HardFilter, ...] = ()
    soft_preferences: tuple[SoftPreference, ...] = ()
    sort: SortSpec | None = None

    @classmethod
    def from_dict(cls, data: Any, registry: Registry) -> SearchState:
        return validate_search_state(data, registry)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_text": self.query_text,
            "hard_filters": [f.to_dict() for f in self.hard_filters],
            "soft_preferences": [f.to_dict() for f in self.soft_preferences],
            "sort": self.sort.to_dict() if self.sort else None,
        }


def empty_search_state() -> SearchState:
    return SearchState()


def validate_search_state(data: Any, registry: Registry) -> SearchState:
    item = ensure_exact_fields(data, STATE_FIELDS, "SearchState")
    validate_text(item["query_text"], "query_text", 128, nullable=True)
    return SearchState(
        query_text=item["query_text"],
        hard_filters=tuple(
            validate_hard_filter(f, registry)
            for f in ensure_list(item["hard_filters"], "hard_filters")
        ),
        soft_preferences=tuple(
            validate_soft_preference(f, registry)
            for f in ensure_list(item["soft_preferences"], "soft_preferences")
        ),
        sort=validate_sort(item["sort"], registry),
    )
