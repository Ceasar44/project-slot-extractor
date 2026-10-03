from copy import deepcopy

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.evaluation.assertions import CHECKERS, evaluate_assertion
from slot_extractor.schemas.dataset_contract import ASSERTION_TYPES
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SortSpec


def assertion_case(kind):
    item = record()
    field = None
    if kind in {
        "field_replaced",
        "field_preserved",
        "field_cleared",
        "allergen_semantics_correct",
        "minimal_patch",
    }:
        item = multi_record()
    if kind == "field_replaced":
        field = "flavor"
    elif kind == "field_preserved":
        field = "application"
    elif kind == "field_cleared":
        field = "flavor"
        item["scenario"] = "clear"
        item["expected"] = SearchPatch(clear_fields=("flavor",)).to_dict()
    elif kind in {"field_exact", "operator_correct"}:
        field = "price"
    elif kind == "value_normalized":
        field = "flavor"
    elif kind == "negation_correct":
        field = "flavor"
        item["scenario"] = "negation"
        item["expected"] = SearchPatch(
            hard_filters=(HardFilter("flavor", "not_in", values=("peanut",)),)
        ).to_dict()
    elif kind == "query_text_correct":
        item["scenario"] = "query_text"
        item["expected"] = SearchPatch(query_text="Dubai Chocolate").to_dict()
    elif kind == "sort_correct":
        item["scenario"] = "sort"
        item["expected"] = SearchPatch(sort=SortSpec("price", "asc")).to_dict()
    elif kind == "unmapped_correct":
        item["scenario"] = "unmapped"
        item["input"]["user_input"] += "，高级一点"
        item["expected"] = SearchPatch(unmapped_terms=("高级一点",)).to_dict()
    assertion = {"type": kind, "field": field}
    item["assertions"] = [assertion]
    sample = raw_sample_from_record(item, registry())
    bad = deepcopy(sample.expected)
    if kind == "field_exact":
        bad["hard_filters"][0]["value"] = 19
    elif kind == "field_replaced":
        bad["soft_preferences"][0]["values"] = ["pistachio"]
    elif kind == "field_preserved":
        bad["clear_fields"] = ["application"]
    elif kind == "field_cleared":
        bad["clear_fields"] = []
    elif kind == "operator_correct":
        bad["hard_filters"][0]["op"] = "gte"
    elif kind == "value_normalized":
        bad["soft_preferences"][0]["values"] = ["hazelnut"]
    elif kind == "hard_soft_correct":
        c = bad["soft_preferences"].pop(0)
        c.pop("preference")
        c["op"] = "in"
        bad["hard_filters"].append(c)
    elif kind == "negation_correct":
        bad["hard_filters"][0]["op"] = "in"
    elif kind == "allergen_semantics_correct":
        bad["hard_filters"][1]["field"] = "flavor"
    elif kind == "query_text_correct":
        bad["query_text"] = None
    elif kind == "sort_correct":
        bad["sort"]["order"] = "desc"
    elif kind == "no_unknown_field":
        bad["hard_filters"][0]["field"] = "premium"
    elif kind == "no_unknown_value":
        bad["soft_preferences"][0]["values"] = ["invented"]
    elif kind == "no_hallucinated_filter":
        bad["hard_filters"].append(HardFilter("texture", "in", values=("pipeable",)).to_dict())
    elif kind == "unmapped_correct":
        bad["unmapped_terms"] = []
    elif kind == "minimal_patch":
        bad["hard_filters"].append(
            deepcopy(sample.input["current_search_state"]["hard_filters"][0])
        )
    return sample, assertion, bad


@pytest.mark.parametrize("kind", sorted(ASSERTION_TYPES))
def test_every_assertion_has_positive_and_negative_gold_comparison(kind):
    sample, assertion, bad = assertion_case(kind)
    assert evaluate_assertion(assertion, sample.expected, sample, registry()).passed
    result = evaluate_assertion(assertion, bad, sample, registry())
    assert not result.passed
    assert result.dimension in {"schema", "field", "intent", "state", "safety", "search"}


def test_assertion_registry_covers_contract_exactly():
    assert set(CHECKERS) == ASSERTION_TYPES


@pytest.mark.parametrize("name", ["query_text", "sort"])
def test_special_fields_can_be_cleared_and_preserved(name):
    item = multi_record()
    item["scenario"] = "clear"
    item["input"]["current_search_state"][name] = (
        "Dubai" if name == "query_text" else {"field": "price", "order": "asc"}
    )
    item["expected"] = SearchPatch(clear_fields=(name,)).to_dict()
    item["assertions"] = [{"type": "field_cleared", "field": name}]
    sample = raw_sample_from_record(item, registry())
    assert evaluate_assertion(sample.assertions[0], sample.expected, sample, registry()).passed
    bad = deepcopy(sample.expected)
    bad["reset"] = True
    bad["clear_fields"] = []
    assert not evaluate_assertion(sample.assertions[0], bad, sample, registry()).passed


def test_state_preservation_does_not_hide_wrong_reset():
    sample, assertion, _ = assertion_case("field_preserved")
    bad = deepcopy(sample.expected)
    bad["reset"] = True
    assert not evaluate_assertion(assertion, bad, sample, registry()).passed


@pytest.mark.parametrize(
    "data", ["```json\n{}\n```", '{"reset":true,"reset":false}', "[]", "NaN", {}]
)
def test_invalid_json_and_shapes_fail_semantic_assertions(data):
    sample, assertion, _ = assertion_case("hard_soft_correct")
    assert not evaluate_assertion(assertion, data, sample, registry()).passed


@pytest.mark.parametrize("mutation", ["field", "values", "clear"])
def test_unknown_checks_handle_unhashable_payloads(mutation):
    sample, _, _ = assertion_case("no_unknown_field")
    bad = deepcopy(sample.expected)
    if mutation == "field":
        bad["hard_filters"][0]["field"] = []
    elif mutation == "values":
        bad["soft_preferences"][0]["values"] = [{}]
    else:
        bad["clear_fields"] = [[]]
    for kind in ("no_unknown_field", "no_unknown_value"):
        result = evaluate_assertion({"type": kind, "field": None}, bad, sample, registry())
        assert isinstance(result.passed, bool)


@pytest.mark.parametrize(
    "assertion",
    [
        "price == 20",
        {"type": "bad", "field": None},
        {"type": "field_exact", "field": None},
        {"type": "minimal_patch", "field": "invented"},
    ],
)
def test_bad_assertion_configuration_is_not_silently_scored(assertion):
    sample = raw_sample_from_record(record(), registry())
    with pytest.raises(ValueError):
        evaluate_assertion(assertion, sample.expected, sample, registry())
