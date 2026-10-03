from copy import deepcopy
from dataclasses import replace

import pytest
from search_dataset_helpers import REGISTRY_PATH, multi_record, record, registry

from slot_extractor.registry import ValueSpec
from slot_extractor.schemas.dataset_contract import (
    ASSERTION_TYPES,
    SCENARIO_CODES,
    DatasetContractError,
    load_dataset_contract,
    validate_dataset_against_contract,
    validate_record_against_contract,
    validate_sample_against_contract,
)
from slot_extractor.schemas.sample import sample_from_record
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SortSpec


@pytest.mark.parametrize("factory", [record, multi_record])
def test_valid_gold(factory):
    sample = sample_from_record(factory(), registry())
    assert validate_sample_against_contract(sample, registry()) == []


@pytest.mark.parametrize(
    "area, field",
    [
        ("sample", "scenario"),
        ("sample", "tags"),
        ("sample", "assertions"),
        ("input", "user_input"),
        ("input", "current_search_state"),
        ("expected", "reset"),
        ("expected", "unmapped_terms"),
    ],
)
def test_required_keys(area, field):
    item = record()
    del (item if area == "sample" else item[area])[field]
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize(
    "area, key",
    [
        ("sample", "output_kind"),
        ("sample", "dpo_targets"),
        ("input", "history"),
        ("input", "current_time"),
        ("input", "current_state"),
        ("expected", "reply"),
        ("expected", "action"),
    ],
)
def test_legacy_and_extra_keys_rejected(area, key):
    item = record()
    (item if area == "sample" else item[area])[key] = None
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize(
    "key, value",
    [
        ("id", " "),
        ("id", None),
        ("scenario", []),
        ("scenario", "ask"),
        ("tags", []),
        ("tags", ["x"] * 2),
        ("tags", [str(i) for i in range(17)]),
        ("tags", [None]),
        ("tags", [" "]),
        ("assertions", "field_exact"),
        ("input", []),
        ("expected", None),
    ],
)
def test_malformed_metadata(key, value):
    item = record()
    item[key] = value
    with pytest.raises(DatasetContractError):
        sample_from_record(item, registry())


@pytest.mark.parametrize("value", [None, [], "json", 12])
def test_nonobject_record(value):
    assert validate_record_against_contract(value, registry())


@pytest.mark.parametrize("value", ["", " ", "x" * 513, None, 1])
def test_bad_user_input(value):
    item = record()
    item["input"]["user_input"] = value
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize(
    "assertion",
    [
        {},
        {"type": "field_exact", "field": None},
        {"type": "field_exact", "field": "technician_name"},
        {"type": "operator_correct", "field": "sort"},
        {"type": "value_normalized", "field": "query_text"},
        {"type": [], "field": None},
        {"type": "minimal_patch", "field": []},
        {"type": "unknown", "field": None},
        {"type": "sort_correct", "field": None, "extra": True},
    ],
)
def test_bad_assertion(assertion):
    item = record()
    item["assertions"] = [assertion]
    assert validate_record_against_contract(item, registry())


def test_duplicate_assertions():
    item = record()
    item["assertions"] *= 2
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize("kind", sorted(ASSERTION_TYPES))
def test_all_assertion_types_supported(kind):
    item = multi_record()
    field = {
        "field_replaced": "flavor",
        "field_preserved": "application",
        "field_exact": "allergen",
        "operator_correct": "price",
        "value_normalized": "flavor",
    }.get(kind)
    if kind == "field_cleared":
        item["expected"]["clear_fields"] = ["application"]
        field = "application"
    item["assertions"] = [{"type": kind, "field": field}]
    assert validate_record_against_contract(item, registry()) == []


@pytest.mark.parametrize(
    "kind, field",
    [
        ("field_replaced", "allergen"),
        ("field_preserved", "flavor"),
        ("field_cleared", "price"),
        ("field_exact", "application"),
    ],
)
def test_assertion_must_be_supported_by_gold(kind, field):
    item = multi_record()
    item["assertions"] = [{"type": kind, "field": field}]
    assert validate_record_against_contract(item, registry())


def test_duplicate_ids_aggregate_errors():
    sample = sample_from_record(record(), registry())
    broken = replace(sample, id="bad", scenario="ask")
    with pytest.raises(DatasetContractError) as exc:
        validate_dataset_against_contract([sample, sample, broken], registry())
    assert "duplicate sample id" in str(exc.value)
    assert "bad: scenario" in str(exc.value)


def test_load_contract_is_registry():
    assert load_dataset_contract(REGISTRY_PATH) == registry()
    with pytest.raises(DatasetContractError):
        load_dataset_contract("missing.yaml")


def test_registry_drift_changes_validation_without_duplicate_enums():
    base = registry()
    added = ValueSpec("test_flavor", "测试", ())
    changed = replace(
        base,
        fields=tuple(
            replace(spec, values=(*spec.values, added)) if spec.name == "flavor" else spec
            for spec in base.fields
        ),
    )
    item = record()
    item["expected"]["soft_preferences"][0]["values"] = ["test_flavor"]
    assert validate_record_against_contract(item, base)
    assert validate_record_against_contract(item, changed) == []


def test_nonextractable_field_rejected_in_gold():
    base = registry()
    changed = replace(
        base,
        fields=tuple(
            replace(spec, model_extractable=False) if spec.name == "flavor" else spec
            for spec in base.fields
        ),
    )
    assert validate_record_against_contract(record(), changed)


@pytest.mark.parametrize("scenario", SCENARIO_CODES)
def test_each_scenario_requires_appropriate_patch(scenario):
    item = record()
    item["scenario"] = scenario
    item["expected"] = SearchPatch().to_dict()
    assert validate_record_against_contract(item, registry())


def test_minimal_patch_detects_repeated_old_field():
    item = multi_record()
    item["expected"]["hard_filters"].append(
        deepcopy(item["input"]["current_search_state"]["hard_filters"][0])
    )
    assert any("minimal_patch" in e for e in validate_record_against_contract(item, registry()))
    item["assertions"] = []
    assert validate_record_against_contract(item, registry()) == []


def test_clear_and_set_conflict():
    item = multi_record()
    item["expected"]["clear_fields"] = ["flavor"]
    assert any("clear and set" in e for e in validate_record_against_contract(item, registry()))


def test_reset_with_clear_is_redundant():
    item = record()
    item["scenario"] = "reset"
    item["expected"]["reset"] = True
    item["expected"]["clear_fields"] = ["price"]
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize("field", ["query_text", "sort"])
def test_special_fields_can_be_cleared_and_asserted(field):
    item = multi_record()
    item["scenario"] = "clear"
    item["input"]["current_search_state"][field] = (
        "Dubai Chocolate" if field == "query_text" else {"field": "price", "order": "asc"}
    )
    item["expected"] = SearchPatch(clear_fields=(field,)).to_dict()
    item["assertions"] = [{"type": "field_cleared", "field": field}]
    assert validate_record_against_contract(item, registry()) == []


def test_condition_order_does_not_fake_replacement():
    item = multi_record()
    before = HardFilter("flavor", "in", values=("pistachio", "matcha")).to_dict()
    item["input"]["current_search_state"]["hard_filters"] = [before]
    item["input"]["current_search_state"]["soft_preferences"] = []
    after = deepcopy(before)
    after["values"].reverse()
    item["expected"] = SearchPatch().to_dict()
    item["expected"]["hard_filters"] = [after]
    item["assertions"] = []
    assert validate_record_against_contract(item, registry())


@pytest.mark.parametrize("scenario", SCENARIO_CODES)
def test_valid_example_for_every_scenario(scenario):
    item = multi_record() if scenario in {"replace", "clear", "preserve_state"} else record()
    item["scenario"] = scenario
    item["assertions"] = []
    patches = {
        "single_filter": SearchPatch(hard_filters=(HardFilter("price", "lte", value=20),)),
        "multi_filter": SearchPatch(
            hard_filters=(
                HardFilter("price", "lte", value=20),
                HardFilter("flavor", "in", values=("pistachio",)),
            )
        ),
        "negation": SearchPatch(hard_filters=(HardFilter("flavor", "not_in", values=("peanut",)),)),
        "allergy_vs_flavor": SearchPatch(
            hard_filters=(HardFilter("allergen", "not_in", values=("peanut",)),)
        ),
        "clear": SearchPatch(clear_fields=("flavor",)),
        "numeric_price": SearchPatch(hard_filters=(HardFilter("price", "lte", value=20),)),
        "numeric_size": SearchPatch(hard_filters=(HardFilter("size", "eq", value=8, unit="oz"),)),
        "sort": SearchPatch(sort=SortSpec("price", "asc")),
        "query_text": SearchPatch(query_text="Dubai Chocolate"),
        "unmapped": SearchPatch(unmapped_terms=("高级一点",)),
        "reset": SearchPatch(reset=True),
    }
    if scenario in patches:
        item["expected"] = patches[scenario].to_dict()
    if scenario == "unmapped":
        item["input"]["user_input"] += "，高级一点"
    assert validate_record_against_contract(item, registry()) == []


def test_dataset_invalid_unhashable_id_is_diagnostic():
    sample = sample_from_record(record(), registry())
    with pytest.raises(DatasetContractError, match="id: must be nonempty text"):
        validate_dataset_against_contract([replace(sample, id=[])], registry())


@pytest.mark.parametrize("extra", ["schema_version", "reset", "unmapped_terms", "clear_fields"])
def test_patch_commands_never_persist_in_state(extra):
    item = multi_record()
    item["input"]["current_search_state"][extra] = None
    assert validate_record_against_contract(item, registry())
