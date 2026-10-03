from dataclasses import asdict

import pytest

from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference
from slot_extractor.search import SearchValidationError, collect_validation_errors, validate_patch


def test_collects_multiple_errors_with_paths_and_codes(registry):
    data = SearchPatch().to_dict()
    data["reset"] = "false"
    data["schema_version"] = "2.0"
    data["hard_filters"] = [
        HardFilter("unknown", "eq", value=1).to_dict(),
        HardFilter("flavor", "in", values=("开心果",)).to_dict(),
    ]
    errors = collect_validation_errors(data, registry)
    assert {(e.path, e.code) for e in errors} == {
        ("reset", "invalid_type"),
        ("schema_version", "invalid_version"),
        ("hard_filters[0]", "unknown_field"),
        ("hard_filters[1]", "unknown_value"),
    }
    assert all(asdict(e)["message"] for e in errors)
    assert errors == collect_validation_errors(data, registry)
    with pytest.raises(SearchValidationError) as exc:
        validate_patch(data, registry)
    assert exc.value.errors == errors


@pytest.mark.parametrize("data", [None, [], {}, {"extra": True}])
def test_root_errors_are_structured(registry, data):
    errors = collect_validation_errors(data, registry)
    assert len(errors) == 1
    assert errors[0].path == "$"


@pytest.mark.parametrize(
    ("item", "code"),
    [
        (HardFilter("flavor", "eq", value="pistachio"), "invalid_operator"),
        (HardFilter("price", "lte", value=20, unit="usd"), "invalid_unit"),
        (HardFilter("sweetness_level", "lte", value=6), "invalid_range"),
    ],
)
def test_specific_condition_errors(registry, item, code):
    assert collect_validation_errors(SearchPatch(hard_filters=(item,)), registry)[0].code == code


@pytest.mark.parametrize(
    "conditions",
    [
        (HardFilter("price", "gte", value=30), HardFilter("price", "lte", value=20)),
        (
            HardFilter("price", "eq", value=25),
            HardFilter("price", "between", min_value=1, max_value=20),
        ),
        (HardFilter("bake_stable", "eq", value=True), HardFilter("bake_stable", "eq", value=False)),
        (
            HardFilter("flavor", "in", values=("matcha",)),
            HardFilter("flavor", "not_in", values=("matcha",)),
        ),
        (
            HardFilter("allergen", "in", values=("pistachio",)),
            HardFilter("allergen", "not_in", values=("tree_nut",)),
        ),
        (
            HardFilter("size", "gte", value=1, unit="kg"),
            HardFilter("size", "lte", value=500, unit="g"),
        ),
    ],
)
def test_unsatisfiable_hard_conditions(registry, conditions):
    errors = collect_validation_errors(SearchPatch(hard_filters=conditions), registry)
    assert errors[0].code == "conflicting_filters"


def test_mixed_currencies_cannot_be_compared(registry):
    patch = SearchPatch(
        hard_filters=(HardFilter("price", "gte", value=10, unit="USD"),),
        soft_preferences=(SoftPreference("price", "around", value=20, unit="CNY"),),
    )
    assert collect_validation_errors(patch, registry)[0].code == "mixed_currency"


@pytest.mark.parametrize(
    "preferences",
    [
        (
            SoftPreference("flavor", "prefer", values=("matcha",)),
            SoftPreference("flavor", "avoid", values=("matcha",)),
        ),
        (SoftPreference("price", "lower"), SoftPreference("price", "higher")),
    ],
)
def test_opposing_preferences(registry, preferences):
    assert (
        collect_validation_errors(SearchPatch(soft_preferences=preferences), registry)[0].code
        == "conflicting_preferences"
    )


def test_multivalued_facets_are_not_treated_as_scalar(registry):
    conditions = (
        HardFilter("flavor", "in", values=("matcha",)),
        HardFilter("flavor", "in", values=("white_chocolate",)),
    )
    assert validate_patch(SearchPatch(hard_filters=conditions), registry).hard_filters == conditions


def test_or_clause_can_retain_a_nonexcluded_value(registry):
    patch = SearchPatch(
        hard_filters=(
            HardFilter("flavor", "in", values=("matcha", "pistachio")),
            HardFilter("flavor", "not_in", values=("pistachio",)),
        )
    )
    assert collect_validation_errors(patch, registry) == ()


def test_flavor_does_not_imply_allergen(registry):
    patch = SearchPatch(
        hard_filters=(
            HardFilter("flavor", "in", values=("pistachio",)),
            HardFilter("allergen", "not_in", values=("tree_nut",)),
        )
    )
    assert validate_patch(patch, registry) == patch


def test_touching_numeric_bounds_and_equivalent_units(registry):
    patch = SearchPatch(
        hard_filters=(
            HardFilter("size", "gte", value=1, unit="kg"),
            HardFilter("size", "lte", value=1000, unit="g"),
        )
    )
    assert collect_validation_errors(patch, registry) == ()


@pytest.mark.parametrize("soft", [False, True])
def test_conversion_overflow_is_structured(registry, soft):
    if soft:
        patch = SearchPatch(
            soft_preferences=(SoftPreference("size", "around", value=1e308, unit="kg"),)
        )
    else:
        patch = SearchPatch(hard_filters=(HardFilter("size", "eq", value=1e308, unit="kg"),))
    assert collect_validation_errors(patch, registry)[0].code == "invalid_unit"


def test_direct_typed_construction_cannot_bypass_validation(registry):
    with pytest.raises(SearchValidationError):
        validate_patch(SearchPatch(reset=1), registry)
