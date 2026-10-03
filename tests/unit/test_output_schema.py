import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path

import pytest
import yaml

from slot_extractor.registry import Registry, load_registry
from slot_extractor.schemas.output import (
    OutputValidationError,
    parse_model_json,
    validate_search_patch_output,
)
from slot_extractor.schemas.results import CaseResult
from slot_extractor.schemas.search_patch import (
    PATCH_FIELDS,
    HardFilter,
    SearchPatch,
    SoftPreference,
    SortSpec,
    validate_clear_fields,
    validate_hard_filter,
    validate_search_patch,
    validate_soft_preference,
    validate_sort,
)

CATALOG = Path(__file__).resolve().parents[2] / "configs/catalog/registry.yaml"


@pytest.fixture
def registry():
    return load_registry(CATALOG)


def condition(name="flavor", op="in", *, soft=False, **updates):
    return {
        "field": name,
        "preference" if soft else "op": op,
        "value": None,
        "values": [],
        "min_value": None,
        "max_value": None,
        "unit": None,
        **updates,
    }


def patch(**updates):
    return {**SearchPatch().to_dict(), **updates}


def test_empty_patch_exact_shape_and_roundtrip(registry):
    data = patch()
    assert set(data) == PATCH_FIELDS
    result = validate_search_patch_output(parse_model_json(json.dumps(data)), registry)
    assert result == SearchPatch()
    assert result.to_dict() == data
    assert SearchPatch.from_dict(data, registry) == result


def test_complete_patch_preserves_units_and_minimal_contents(registry):
    data = patch(
        reset=True,
        query_text="Dubai Chocolate",
        hard_filters=[
            condition("price", "lte", value=30, unit="USD"),
            condition("allergen", "not_in", values=["tree_nut"]),
        ],
        soft_preferences=[
            condition("size", "around", soft=True, value=8, unit="oz"),
            condition("sweetness_level", "lower", soft=True),
        ],
        sort={"field": "price", "order": "asc"},
        clear_fields=["flavor", "query_text", "sort"],
        unmapped_terms=["高级一点"],
    )
    parsed = validate_search_patch(data, registry)
    assert parsed.to_dict() == data
    assert parsed.soft_preferences[0].value == 8
    assert parsed.soft_preferences[0].unit == "oz"
    assert parsed.hard_filters[1].values == ("tree_nut",)
    assert isinstance(parsed.hard_filters[0], HardFilter)
    assert isinstance(parsed.soft_preferences[0], SoftPreference)
    assert parsed.sort == SortSpec("price", "asc")
    data["hard_filters"][1]["values"].append("peanut")
    parsed.to_dict()["soft_preferences"].clear()
    assert parsed.hard_filters[1].values == ("tree_nut",)
    assert len(parsed.soft_preferences) == 2
    with pytest.raises(FrozenInstanceError):
        parsed.reset = False


def test_every_registry_operator_accepts_its_payload(registry):
    for spec in registry.fields:
        for soft, ops in ((False, spec.hard_operators), (True, spec.soft_operators)):
            for op in ops:
                item = condition(spec.name, op, soft=soft)
                if spec.unit_kind == "mass":
                    item["unit"] = spec.base_unit
                if op in ("in", "not_in", "prefer", "avoid"):
                    item["values"] = [spec.values[0].code]
                elif op == "between":
                    item["min_value"], item["max_value"] = 1, 2
                elif op not in ("lower", "higher"):
                    item["value"] = True if spec.type == "boolean" else 1
                validate = validate_soft_preference if soft else validate_hard_filter
                assert validate(item, registry).to_dict() == item


@pytest.mark.parametrize("key", sorted(PATCH_FIELDS))
def test_missing_patch_fields(registry, key):
    data = patch()
    del data[key]
    with pytest.raises(OutputValidationError, match="schema fields"):
        validate_search_patch_output(data, registry)


@pytest.mark.parametrize("data", [None, [], "{}", 1, {1: "value"}])
def test_invalid_root_types(registry, data):
    with pytest.raises(OutputValidationError):
        validate_search_patch_output(data, registry)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", 1.0),
        ("schema_version", "2.0"),
        ("schema_version", None),
        ("reset", 1),
        ("reset", "false"),
        ("reset", None),
        ("query_text", ""),
        ("query_text", "  "),
        ("query_text", 1),
        ("query_text", "x" * 129),
        ("hard_filters", None),
        ("hard_filters", {}),
        ("hard_filters", [None]),
        ("soft_preferences", ()),
        ("soft_preferences", [{}]),
        ("action", "final"),
        ("unmapped_terms", None),
        ("unmapped_terms", [""]),
        ("unmapped_terms", [1]),
        ("unmapped_terms", ["a", "a"]),
        ("unmapped_terms", ["x" * 65]),
        ("unmapped_terms", [str(i) for i in range(6)]),
    ],
)
def test_invalid_patch_properties(registry, key, value):
    with pytest.raises(OutputValidationError):
        validate_search_patch_output(patch(**{key: value}), registry)


@pytest.mark.parametrize(
    ("name", "op", "updates"),
    [
        ("unknown", "in", {"values": ["pistachio"]}),
        ("flavor", "eq", {"value": "pistachio"}),
        ("flavor", "in", {"values": ["开心果"]}),
        ("flavor", "in", {"values": ["PISTACHIO"]}),
        ("flavor", "in", {"values": ["pistachio", "pistachio"]}),
        ("flavor", "in", {"values": [True]}),
        ("flavor", "in", {"values": [{}]}),
        ("flavor", "in", {"values": "pistachio"}),
        ("flavor", "in", {}),
        ("flavor", "not_in", {"values": ["peanut"], "value": "peanut"}),
        ("flavor", "in", {"values": ["pistachio"], "min_value": 1}),
        ("flavor", "in", {"values": ["pistachio"], "unit": "g"}),
        ("price", "lte", {"value": True}),
        ("price", "lte", {"value": "20"}),
        ("price", "gte", {"value": -1}),
        ("price", "eq", {"value": float("nan")}),
        ("price", "eq", {"value": float("inf")}),
        ("price", "lte", {"value": 20, "unit": "usd"}),
        ("price", "lte", {"value": 20, "unit": "g"}),
        ("price", "lte", {"value": 20, "unit": []}),
        ("price", "eq", {"value": 1, "values": [1]}),
        ("price", "eq", {"value": 1, "max_value": 1}),
        ("price", "between", {"min_value": 30, "max_value": 20}),
        ("price", "between", {"min_value": 1}),
        ("price", "between", {"min_value": 1, "max_value": 2, "value": 1}),
        ("price", "between", {"min_value": True, "max_value": 2}),
        ("sweetness_level", "eq", {"value": 2.0}),
        ("sweetness_level", "gte", {"value": 0}),
        ("flavor_intensity", "lte", {"value": 6}),
        ("size", "eq", {"value": 0, "unit": "g"}),
        ("size", "eq", {"value": 8}),
        ("size", "eq", {"value": 8, "unit": "lb"}),
        ("bake_stable", "eq", {"value": 1}),
        ("bake_stable", "eq", {"value": None}),
        ("bake_stable", "gte", {"value": True}),
    ],
)
def test_invalid_hard_conditions(registry, name, op, updates):
    with pytest.raises(OutputValidationError):
        validate_hard_filter(condition(name, op, **updates), registry)


@pytest.mark.parametrize(
    "key", ["field", "op", "value", "values", "min_value", "max_value", "unit"]
)
def test_condition_shape_is_fixed(registry, key):
    item = condition(values=["pistachio"])
    del item[key]
    with pytest.raises(OutputValidationError, match="schema fields"):
        validate_hard_filter(item, registry)


@pytest.mark.parametrize("updates", [{"extra": 1}, {"field": []}, {"op": []}])
def test_malformed_condition_members(registry, updates):
    with pytest.raises(OutputValidationError):
        validate_hard_filter(condition(values=["pistachio"], **updates), registry)


@pytest.mark.parametrize(
    ("name", "op", "updates"),
    [
        ("allergen", "avoid", {"values": ["peanut"]}),
        ("bake_stable", "prefer", {"value": True}),
        ("flavor", "lower", {}),
        ("flavor", "prefer", {"values": ["unknown"]}),
        ("flavor", "prefer", {"value": "pistachio"}),
        ("price", "lower", {"value": 20}),
        ("sweetness_level", "higher", {"max_value": 5}),
        ("price", "around", {}),
        ("price", "around", {"value": -1}),
        ("size", "around", {"value": 8}),
        ("size", "between", {"min_value": 8, "max_value": 4, "unit": "oz"}),
    ],
)
def test_invalid_soft_conditions(registry, name, op, updates):
    with pytest.raises(OutputValidationError):
        validate_soft_preference(condition(name, op, soft=True, **updates), registry)


@pytest.mark.parametrize(
    ("name", "value", "unit"),
    [
        ("price", 0, None),
        ("price", 20, "CNY"),
        ("size", 8, "oz"),
        ("size", 1, "kg"),
        ("bake_stable", False, None),
        ("sweetness_level", 1, None),
        ("sweetness_level", 5, None),
    ],
)
def test_valid_boundaries(registry, name, value, unit):
    assert (
        validate_hard_filter(condition(name, "eq", value=value, unit=unit), registry).value == value
    )


@pytest.mark.parametrize(
    "item",
    [
        {},
        [],
        {"field": "unknown", "order": "asc"},
        {"field": "price", "order": "up"},
        {"field": "newest", "order": "asc"},
        {"field": "price", "order": []},
        {"field": "price", "order": "asc", "extra": None},
    ],
)
def test_invalid_sort(registry, item):
    with pytest.raises(OutputValidationError):
        validate_sort(item, registry)


def test_all_configured_sorts(registry):
    assert validate_sort(None, registry) is None
    for spec in registry.search.sort_fields:
        for order in spec.orders:
            assert validate_sort({"field": spec.field, "order": order}, registry) == SortSpec(
                spec.field, order
            )


@pytest.mark.parametrize("names", [None, "price", ["unknown"], ["price", "price"], [1], [[]]])
def test_invalid_clear_fields(registry, names):
    with pytest.raises(OutputValidationError):
        validate_clear_fields(names, registry)


def test_validation_follows_registry_without_alias_repair():
    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    flavor = next(f for f in data["fields"] if f["name"] == "flavor")
    flavor["values"].append(
        {"code": "test_flavor", "label": "测试", "aliases": ["测试"], "parent": "fruit"}
    )
    flavor["clearable"] = False
    flavor["hard_operators"] = ["in"]
    registry = Registry.from_dict(data)
    validate_hard_filter(condition(values=["test_flavor"]), registry)
    with pytest.raises(OutputValidationError):
        validate_hard_filter(condition(values=["测试"]), registry)
    with pytest.raises(OutputValidationError):
        validate_hard_filter(condition(op="not_in", values=["test_flavor"]), registry)
    with pytest.raises(OutputValidationError):
        validate_clear_fields(["flavor"], registry)
    assert (
        set(validate_clear_fields(sorted(registry.clearable_fields()), registry))
        == registry.clearable_fields()
    )


@pytest.mark.parametrize(
    "text",
    [
        "```json\n{}\n```",
        "[]",
        "null",
        "true",
        '"text"',
        "{} extra",
        "{",
        '{"a":1,"a":2}',
        '{"a":{"b":1,"b":2}}',
        '{"a":NaN}',
        '{"a":Infinity}',
        '{"a":1e999}',
        None,
    ],
)
def test_invalid_model_json(text):
    with pytest.raises(OutputValidationError):
        parse_model_json(text)


def test_case_result_uses_search_patch_and_no_kind(registry):
    result = CaseResult("eval-000001", "{}", {}, output=SearchPatch(), scenario="reset")
    record = asdict(result)
    assert "output_kind" not in record
    assert "conversation_kind" not in record
    assert record["output"]["schema_version"] == "1.0"
    invalid = CaseResult("eval-000002", "bad JSON", {})
    assert invalid.output is None


def test_validation_does_not_mutate_input(registry):
    data = patch(hard_filters=[condition(values=["pistachio"])])
    before = deepcopy(data)
    validate_search_patch(data, registry)
    assert data == before
