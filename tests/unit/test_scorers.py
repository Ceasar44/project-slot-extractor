import json
from copy import deepcopy

from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.evaluation.assertions import prepare_evaluation
from slot_extractor.evaluation.scorers.search_patch import PatchScorer, SchemaScorer, field_counts


def context(item=None, actual=None):
    item = item or record()
    sample = raw_sample_from_record(item, registry())
    return prepare_evaluation(sample, json.dumps(actual or sample.expected), registry())


def test_exact_match_ignores_condition_and_set_order():
    item = multi_record()
    actual = deepcopy(item["expected"])
    actual["hard_filters"].reverse()
    metrics = PatchScorer().score(context(item, actual))
    assert metrics["exact_match"].score == 1
    assert metrics["state_preserve"].score == 1


def test_missing_one_field_produces_partial_field_counts_and_no_hallucination():
    item = record()
    actual = deepcopy(item["expected"])
    actual["soft_preferences"].pop()
    ctx = context(item, actual)
    assert field_counts(ctx) == {"tp": 2, "fp": 0, "fn": 1}
    scores = PatchScorer().score(ctx)
    assert scores["exact_match"].score == 0
    assert scores["field_extraction"].score == 2 / 3
    assert scores["hallucination_free"].score == 1


def test_unknown_enum_is_schema_failure_and_not_exact_match():
    item = record()
    actual = deepcopy(item["expected"])
    actual["soft_preferences"][0]["values"] = ["made_up"]
    ctx = context(item, actual)
    assert SchemaScorer().score(ctx)["schema_valid"].score == 0
    assert PatchScorer().score(ctx)["exact_match"].score == 0
    assert ctx.output is None and ctx.errors


def test_duplicate_old_state_fails_minimal_but_can_preserve_state():
    item = multi_record()
    actual = deepcopy(item["expected"])
    actual["hard_filters"].append(
        deepcopy(item["input"]["current_search_state"]["hard_filters"][0])
    )
    scores = PatchScorer().score(context(item, actual))
    assert scores["state_preserve"].score == 1
    assert scores["minimal_patch"].score == 0


def test_numeric_units_are_not_automatically_equated():
    from slot_extractor.schemas.search_patch import HardFilter, SearchPatch

    item = record()
    item["scenario"] = "numeric_size"
    item["expected"] = SearchPatch(
        hard_filters=(HardFilter("size", "eq", value=1, unit="kg"),)
    ).to_dict()
    actual = SearchPatch(hard_filters=(HardFilter("size", "eq", value=1000, unit="g"),)).to_dict()
    assert PatchScorer().score(context(item, actual))["exact_match"].score == 0
