"""Apply only this turn's changes to immutable persistent search state."""

from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_state import SearchState, empty_search_state

from .validator import validate_patch, validate_state


def fields_touched_by_patch(data: Any, registry: Registry) -> frozenset[str]:
    patch = validate_patch(data, registry)
    if patch.reset:
        return frozenset(f.name for f in registry.fields) | {"query_text", "sort"}
    touched = set(patch.clear_fields) | {
        f.field for f in (*patch.hard_filters, *patch.soft_preferences)
    }
    if patch.query_text is not None:
        touched.add("query_text")
    if patch.sort is not None:
        touched.add("sort")
    return frozenset(touched)


def merge_search_state(current: Any, patch: Any, registry: Registry) -> SearchState:
    patch = validate_patch(patch, registry)
    previous = (
        empty_search_state()
        if patch.reset or current is None
        else validate_state(current, registry)
    )
    replaced = set(patch.clear_fields) | {
        f.field for f in (*patch.hard_filters, *patch.soft_preferences)
    }
    query = None if "query_text" in patch.clear_fields else previous.query_text
    sort = None if "sort" in patch.clear_fields else previous.sort
    result = SearchState(
        query_text=patch.query_text if patch.query_text is not None else query,
        hard_filters=tuple(f for f in previous.hard_filters if f.field not in replaced)
        + patch.hard_filters,
        soft_preferences=tuple(f for f in previous.soft_preferences if f.field not in replaced)
        + patch.soft_preferences,
        sort=patch.sort if patch.sort is not None else sort,
    )
    return validate_state(result, registry)
