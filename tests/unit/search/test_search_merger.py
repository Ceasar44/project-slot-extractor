from copy import deepcopy

import pytest

from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference, SortSpec
from slot_extractor.schemas.search_state import SearchState
from slot_extractor.search import SearchValidationError, fields_touched_by_patch, merge_search_state


def current():
    return SearchState(
        query_text="Dubai Chocolate",
        hard_filters=(
            HardFilter("application", "in", values=("croissant_pastry",)),
            HardFilter("price", "lte", value=20, unit="USD"),
        ),
        soft_preferences=(SoftPreference("flavor", "prefer", values=("pistachio",)),),
        sort=SortSpec("price", "asc"),
    )


def test_plan_example_preserves_untouched_fields(registry):
    before = current()
    patch = SearchPatch(hard_filters=(HardFilter("flavor", "in", values=("matcha",)),))
    result = merge_search_state(before, patch, registry)
    assert result.hard_filters == before.hard_filters + patch.hard_filters
    assert not result.soft_preferences
    assert result.sort == before.sort
    assert result.query_text == before.query_text
    assert fields_touched_by_patch(patch, registry) == {"flavor"}


def test_soft_replaces_all_old_hard_and_soft_for_field(registry):
    old = SearchState(
        hard_filters=(HardFilter("price", "gte", value=10), HardFilter("price", "lte", value=30))
    )
    patch = SearchPatch(soft_preferences=(SoftPreference("price", "lower"),))
    result = merge_search_state(old, patch, registry)
    assert result.hard_filters == ()
    assert result.soft_preferences == patch.soft_preferences


def test_multiple_new_conditions_and_hard_soft_can_coexist(registry):
    patch = SearchPatch(
        hard_filters=(HardFilter("price", "gte", value=10), HardFilter("price", "lte", value=30)),
        soft_preferences=(SoftPreference("price", "lower"),),
    )
    result = merge_search_state(current(), patch, registry)
    assert [f for f in result.hard_filters if f.field == "price"] == list(patch.hard_filters)
    assert result.soft_preferences[-1] == patch.soft_preferences[0]


def test_clear_removes_conditions_and_special_fields(registry):
    result = merge_search_state(
        current(), SearchPatch(clear_fields=("flavor", "price", "query_text", "sort")), registry
    )
    assert result == SearchState(hard_filters=(current().hard_filters[0],))


def test_clear_then_set_applies_new_values(registry):
    patch = SearchPatch(
        clear_fields=("flavor", "query_text", "sort"),
        query_text="new query",
        soft_preferences=(SoftPreference("flavor", "prefer", values=("matcha",)),),
        sort=SortSpec("newest", "desc"),
    )
    result = merge_search_state(current(), patch, registry)
    assert result.query_text == "new query"
    assert result.sort == patch.sort
    assert result.soft_preferences == patch.soft_preferences


def test_reset_discards_everything_before_applying_patch(registry):
    patch = SearchPatch(reset=True, hard_filters=(HardFilter("size", "eq", value=8, unit="oz"),))
    result = merge_search_state(current(), patch, registry)
    assert result == SearchState(hard_filters=patch.hard_filters)
    assert result.hard_filters[0].unit == "oz"
    assert fields_touched_by_patch(patch, registry) == {f.name for f in registry.fields} | {
        "query_text",
        "sort",
    }
    assert merge_search_state(current(), SearchPatch(reset=True), registry) == SearchState()


def test_null_query_and_sort_mean_preserve_and_empty_patch_is_noop(registry):
    assert merge_search_state(current(), SearchPatch(), registry) == current()
    assert fields_touched_by_patch(SearchPatch(), registry) == frozenset()
    assert merge_search_state(None, SearchPatch(), registry) == SearchState()


def test_json_inputs_and_outputs_are_detached(registry):
    old = current().to_dict()
    patch = SearchPatch(clear_fields=("flavor",)).to_dict()
    snapshot = deepcopy((old, patch))
    result = merge_search_state(old, patch, registry)
    assert (old, patch) == snapshot
    old["hard_filters"].clear()
    assert len(result.hard_filters) == 2
    assert set(result.to_dict()) == {"query_text", "hard_filters", "soft_preferences", "sort"}


@pytest.mark.parametrize(
    "patch",
    [
        SearchPatch(clear_fields=("unknown",)),
        SearchPatch(
            hard_filters=(
                HardFilter("price", "gte", value=30),
                HardFilter("price", "lte", value=20),
            )
        ),
    ],
)
def test_merger_rejects_invalid_patch_without_mutation(registry, patch):
    old = current()
    with pytest.raises(SearchValidationError):
        merge_search_state(old, patch, registry)
    assert old == current()


def test_merger_validates_persistent_state(registry):
    with pytest.raises(SearchValidationError):
        merge_search_state({}, SearchPatch(), registry)


def test_reset_does_not_read_discarded_state(registry):
    assert merge_search_state({}, SearchPatch(reset=True), registry) == SearchState()
