from copy import deepcopy
from dataclasses import replace

import pytest
from jsonschema import Draft202012Validator, ValidationError
from search_dataset_helpers import record, registry

from slot_extractor.data.raw_sample import RAW_FIELDS
from slot_extractor.data.raw_schema import raw_response_schema, search_patch_schema
from slot_extractor.registry import ValueSpec
from slot_extractor.schemas.dataset_contract import validate_record_against_contract
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference


def test_closed_schema_and_standard_validation():
    schema = raw_response_schema(registry())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(record())
    assert set(schema["required"]) == RAW_FIELDS

    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            if "enum" in value or "const" in value:
                assert "type" in value
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)


@pytest.mark.parametrize(
    "condition",
    [
        HardFilter("flavor", "in", values=("pistachio", "matcha")),
        HardFilter("allergen", "not_in", values=("tree_nut",)),
        HardFilter("bake_stable", "eq", value=False),
        HardFilter("sweetness_level", "lte", value=2),
        HardFilter("price", "gte", value=0, unit=None),
        HardFilter("price", "between", min_value=10, max_value=20, unit="USD"),
        HardFilter("size", "eq", value=1, unit="kg"),
        SoftPreference("size", "around", value=8, unit="oz"),
        SoftPreference("size", "lower"),
        SoftPreference("sweetness_level", "between", min_value=1, max_value=2),
        SoftPreference("flavor", "avoid", values=("peanut",)),
    ],
)
def test_payload_shapes_match_runtime(condition):
    patch = SearchPatch(
        hard_filters=(condition,) if isinstance(condition, HardFilter) else (),
        soft_preferences=(condition,) if isinstance(condition, SoftPreference) else (),
    ).to_dict()
    Draft202012Validator(search_patch_schema(registry())).validate(patch)
    item = record()
    item["scenario"] = "single_filter"
    item["expected"] = patch
    item["assertions"] = []
    assert validate_record_against_contract(item, registry()) == []


@pytest.mark.parametrize(
    "condition",
    [
        HardFilter("flavor", "in", values=()),
        HardFilter("flavor", "in", values=("pistachio", "pistachio")),
        HardFilter("flavor", "in", values=("unknown",)),
        HardFilter("flavor", "eq", value="pistachio"),
        HardFilter("bake_stable", "eq", value=None),
        HardFilter("bake_stable", "eq", value=1),
        HardFilter("price", "lte", value=True),
        HardFilter("price", "lte", value=-1),
        HardFilter("price", "lte", value=20, unit="xUSDx"),
        HardFilter("price", "lte", value=20, unit="usd"),
        HardFilter("price", "lte", value=20, min_value=1),
        HardFilter("size", "eq", value=0, unit="g"),
        HardFilter("size", "eq", value=8),
        HardFilter("size", "eq", value=8, unit="lb"),
        HardFilter("sweetness_level", "lte", value=6),
        HardFilter("sweetness_level", "lte", value=2.5),
        SoftPreference("allergen", "avoid", values=("peanut",)),
        SoftPreference("sweetness_level", "lower", value=2),
    ],
)
def test_bad_payloads_rejected_by_both_layers(condition):
    patch = SearchPatch(
        hard_filters=(condition,) if isinstance(condition, HardFilter) else (),
        soft_preferences=(condition,) if isinstance(condition, SoftPreference) else (),
    ).to_dict()
    with pytest.raises(ValidationError):
        Draft202012Validator(search_patch_schema(registry())).validate(patch)
    item = record()
    item["expected"] = patch
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize(
    "path, value",
    [
        (("id",), " "),
        (("scenario",), "ask"),
        (("tags",), []),
        (("tags",), ["x", "x"]),
        (("input", "user_input"), "x" * 513),
        (("expected", "query_text"), "x" * 129),
        (("expected", "clear_fields"), ["technician_name"]),
        (("expected", "unmapped_terms"), [str(i) for i in range(6)]),
        (("expected", "unmapped_terms"), ["x" * 65]),
        (("expected", "sort"), {"field": "price", "order": "wrong"}),
        (("assertions",), [{"type": "field_exact", "field": None}]),
        (("assertions",), [{"type": "unknown", "field": None}]),
    ],
)
def test_metadata_and_limits_match_python_contract(path, value):
    item = record()
    target = item
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert not Draft202012Validator(raw_response_schema(registry())).is_valid(item)
    assert validate_record_against_contract(item, registry())


def test_registry_drift_updates_values_clear_fields_and_sort():
    base = registry()
    changed = replace(
        base,
        fields=tuple(
            replace(spec, values=(*spec.values, ValueSpec("new_flavor", "New", ())))
            if spec.name == "flavor"
            else replace(spec, clearable=False)
            if spec.name == "price"
            else spec
            for spec in base.fields
        ),
        search=replace(
            base.search,
            sort_fields=tuple(
                replace(spec, orders=("desc",)) if spec.field == "price" else spec
                for spec in base.search.sort_fields
            ),
        ),
    )
    item = record()
    item["expected"]["soft_preferences"][0]["values"] = ["new_flavor"]
    assert not Draft202012Validator(raw_response_schema(base)).is_valid(item)
    validator = Draft202012Validator(raw_response_schema(changed))
    validator.validate(item)
    item["expected"]["clear_fields"] = ["price"]
    assert not validator.is_valid(item)
    item["expected"]["clear_fields"] = []
    item["expected"]["sort"] = {"field": "price", "order": "asc"}
    assert not validator.is_valid(item)


def test_schema_calls_return_independent_objects():
    first = raw_response_schema(registry())
    original = deepcopy(first)
    first["$defs"]["expected"]["properties"]["clear_fields"]["items"]["enum"].clear()
    assert raw_response_schema(registry()) == original


def test_cross_field_constraints_need_python_validation():
    item = record()
    item["expected"]["hard_filters"] = [
        HardFilter("price", "between", min_value=30, max_value=20).to_dict()
    ]
    # Standard JSON Schema cannot compare two numeric properties.
    Draft202012Validator(raw_response_schema(registry())).validate(item)
    assert validate_record_against_contract(item, registry())
