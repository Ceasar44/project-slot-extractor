import json

import pytest
import yaml

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference, SortSpec
from slot_extractor.schemas.search_state import SearchState
from slot_extractor.search import (
    QueryCompileError,
    SearchValidationError,
    build_soft_ranking,
    compile_hard_filter,
    compile_typesense_query,
    merge_search_state,
)


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (HardFilter("flavor", "in", values=("matcha", "pistachio")), "flavor:=[pistachio,matcha]"),
        (HardFilter("flavor", "not_in", values=("peanut",)), "flavor:!=[peanut]"),
        (HardFilter("bake_stable", "eq", value=True), "bake_stable:=true"),
        (HardFilter("bake_stable", "eq", value=False), "bake_stable:=false"),
        (HardFilter("price", "eq", value=0), "price:=0"),
        (HardFilter("price", "gte", value=10), "price:>=10"),
        (HardFilter("price", "lte", value=20), "price:<=20"),
        (HardFilter("price", "between", min_value=10, max_value=20), "price:[10..20]"),
        (HardFilter("size", "eq", value=8, unit="oz"), "size_g:=226.796185"),
        (HardFilter("size", "gte", value=1, unit="kg"), "size_g:>=1000.0"),
    ],
)
def test_filter_syntax_and_normalization(registry, item, expected):
    assert compile_hard_filter(item, registry, currency="USD") == expected
    assert compile_hard_filter(item.to_dict(), registry, currency="USD") == expected


def test_empty_query(registry):
    result = compile_typesense_query(SearchState(), registry)
    assert result.parameters == {"q": "*", "query_by": ",".join(registry.search.query_fields)}
    assert result.ranking_hints == ()
    json.dumps(result.to_dict())


def test_full_pipeline_from_patch_to_query(registry):
    patch = SearchPatch(
        hard_filters=(
            HardFilter("application", "in", values=("croissant_pastry",)),
            HardFilter("price", "lte", value=20),
        ),
        soft_preferences=(
            SoftPreference("flavor", "prefer", values=("pistachio",)),
            SoftPreference("sweetness_level", "lower"),
        ),
    )
    state = merge_search_state(None, patch.to_dict(), registry)
    query = compile_typesense_query(state.to_dict(), registry, currency="USD")
    assert query.parameters["filter_by"] == "application:=[croissant_pastry] && price:<=20"
    assert "sort_by" not in query.parameters
    assert query.ranking_hints[0]["index_field"] == "flavor"
    assert query.ranking_hints[1]["preference"] == "lower"
    assert state.hard_filters[1].unit is None


def test_soft_preferences_never_become_hard_filters_or_implicit_sort(registry):
    state = SearchState(
        soft_preferences=(
            SoftPreference("size", "around", value=8, unit="oz"),
            SoftPreference("price", "lower"),
        )
    )
    result = compile_typesense_query(state, registry, currency="USD")
    assert "filter_by" not in result.parameters
    assert "sort_by" not in result.parameters
    assert result.ranking_hints[0]["value"] == pytest.approx(226.796185)
    assert result.ranking_hints[0]["unit"] == "g"
    assert result.ranking_hints[1]["unit"] == "USD"
    assert (
        build_soft_ranking(state.soft_preferences, registry, currency="USD") == result.ranking_hints
    )


def test_query_text_is_only_sent_as_q(registry):
    text = "Dubai Chocolate && price:<1"
    result = compile_typesense_query(SearchState(query_text=text), registry)
    assert result.parameters["q"] == text
    assert "filter_by" not in result.parameters


def test_all_configured_sort_mappings(registry):
    for spec in registry.search.sort_fields:
        for order in spec.orders:
            result = compile_typesense_query(
                SearchState(sort=SortSpec(spec.field, order)), registry
            )
            assert result.parameters["sort_by"] == f"{spec.index_field}:{order}"


def test_tree_nut_expansion_and_peanut_independence(registry):
    expression = compile_hard_filter(
        HardFilter("allergen", "not_in", values=("tree_nut",)), registry
    )
    assert expression == "allergen:!=[tree_nut,pistachio,hazelnut,almond,cashew,walnut]"
    assert "peanut" not in expression
    assert (
        compile_hard_filter(HardFilter("allergen", "not_in", values=("pistachio",)), registry)
        == "allergen:!=[pistachio]"
    )
    assert (
        compile_hard_filter(HardFilter("flavor", "in", values=("pistachio",)), registry)
        == "flavor:=[pistachio]"
    )


def test_registry_changes_drive_index_and_descendant_expansion(registry):
    # Build from the sole YAML source, including a new grandchild in the hierarchy.
    from pathlib import Path

    data = yaml.safe_load(
        (Path(__file__).resolve().parents[3] / "configs/catalog/registry.yaml").read_text(
            encoding="utf-8"
        )
    )
    allergen = next(f for f in data["fields"] if f["name"] == "allergen")
    allergen["index_field"] = "verified_allergens"
    allergen["values"].append(
        {"code": "test_child", "label": "测试", "aliases": [], "parent": "pistachio"}
    )
    modified = Registry.from_dict(data)
    expression = compile_hard_filter(
        HardFilter("allergen", "not_in", values=("tree_nut", "pistachio")), modified
    )
    assert expression.startswith("verified_allergens:!=[")
    assert expression.count("pistachio") == 1
    assert "test_child" in expression


@pytest.mark.parametrize("unit", [None, "USD"])
def test_price_requires_index_currency_context(registry, unit):
    with pytest.raises(QueryCompileError, match="index currency"):
        compile_typesense_query(
            SearchState(hard_filters=(HardFilter("price", "eq", value=10, unit=unit),)), registry
        )


def test_explicit_currency_must_match_index(registry):
    with pytest.raises(QueryCompileError, match="differs"):
        compile_typesense_query(
            SearchState(hard_filters=(HardFilter("price", "eq", value=10, unit="CNY"),)),
            registry,
            currency="USD",
        )


def test_invalid_state_cannot_be_compiled(registry):
    with pytest.raises(SearchValidationError):
        compile_typesense_query(
            SearchState(hard_filters=(HardFilter("flavor", "in", values=("x] || price:<1",)),)),
            registry,
        )


def test_compiled_serialization_does_not_share_nested_values(registry):
    query = compile_typesense_query(
        SearchState(soft_preferences=(SoftPreference("flavor", "prefer", values=("matcha",)),)),
        registry,
    )
    data = query.to_dict()
    data["ranking_hints"][0]["values"].clear()
    data["parameters"]["q"] = "changed"
    assert query.parameters["q"] == "*"
    assert query.ranking_hints[0]["values"] == ["matcha"]
