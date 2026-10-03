import json
from copy import deepcopy

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.schemas.results import GenerationResult
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch
from slot_extractor.schemas.search_state import SearchState
from slot_extractor.search_compare.ndjson import encode_event
from slot_extractor.search_compare.orchestrator import SearchComparisonOrchestrator, state_diff


class Backend:
    model = "search-test"

    def __init__(self, output):
        self.output, self.messages, self.calls = output, None, 0

    def generate(self, messages, params=None):
        self.messages = messages
        self.calls += 1
        return GenerationResult(
            self.output if isinstance(self.output, str) else json.dumps(self.output),
            self.model,
            1,
            2,
            10,
            output_tokens=100,
            input_tokens=200,
            tokens_per_s=10,
        )


def test_complete_search_trace_and_single_inference():
    item = multi_record()
    before = deepcopy(item["input"]["current_search_state"])
    backend = Backend(item["expected"])
    trace = SearchComparisonOrchestrator(backend, registry()).run(
        item["input"]["user_input"], before
    )
    assert trace.result.status == "complete" and backend.calls == 1
    assert trace.result.validation["valid"]
    assert trace.result.next_state == trace.result.merged_state
    assert "allergen:!=[peanut]" in trace.result.compiled_query["parameters"]["filter_by"]
    assert {row["field"] for row in trace.result.state_diff} == {"price", "allergen", "flavor"}
    assert item["input"]["current_search_state"] == before
    assert [m["role"] for m in backend.messages] == ["system", "user"]
    assert backend.messages[1]["content"] == item["input"]["user_input"]
    assert "train-000001" not in str(backend.messages)
    assert [e.kind for e in trace.events] == [
        "search_patch_generated",
        "search_patch_parsed",
        "search_patch_validated",
        "search_state_merged",
        "search_query_compiled",
        "search_metrics",
    ]


@pytest.mark.parametrize(
    "output,stage",
    [
        ("```json\n{}\n```", "parse"),
        ({"action": "tool_call", "tool_name": "find_technicians"}, "validation"),
    ],
)
def test_invalid_output_never_merges_or_advances_state(output, stage):
    current = multi_record()["input"]["current_search_state"]
    trace = SearchComparisonOrchestrator(Backend(output), registry()).run("换成抹茶", current)
    assert trace.result.error["stage"] == stage
    assert trace.result.validation["valid"] is False
    assert trace.result.next_state == current
    assert trace.result.merged_state is None and trace.result.compiled_query is None
    assert trace.result.raw_output


def test_invalid_enum_returns_readable_validation_error():
    output = record()["expected"]
    output["soft_preferences"][0]["values"] = ["invented"]
    result = SearchComparisonOrchestrator(Backend(output), registry()).run("开心果").result
    assert result.error["stage"] == "validation"
    assert result.validation["errors"][0]["path"] == "soft_preferences[0]"
    assert result.next_state is None


def test_compile_failure_keeps_candidate_state_but_does_not_commit():
    patch = SearchPatch(hard_filters=(HardFilter("price", "lte", value=20, unit="CNY"),))
    result = (
        SearchComparisonOrchestrator(Backend(patch.to_dict()), registry()).run("20元以内").result
    )
    assert result.validation["valid"] and result.merged_state
    assert result.error["stage"] == "compile" and result.next_state is None
    assert result.compiled_query is None


def test_state_merge_conflict_is_isolated_from_valid_patch():
    current = SearchState(
        hard_filters=(HardFilter("price", "lte", value=20, unit="CNY"),)
    ).to_dict()
    patch = SearchPatch(hard_filters=(HardFilter("size", "eq", value=1, unit="kg"),))
    result = (
        SearchComparisonOrchestrator(Backend(patch.to_dict()), registry())
        .run("1公斤", current)
        .result
    )
    assert result.next_state == current and result.error["stage"] == "compile"


@pytest.mark.parametrize("patch", [SearchPatch(clear_fields=("price",)), SearchPatch(reset=True)])
def test_clear_and_reset_are_applied_before_compile(patch):
    current = SearchState(
        hard_filters=(HardFilter("price", "lte", value=20, unit="USD"),)
    ).to_dict()
    result = (
        SearchComparisonOrchestrator(Backend(patch.to_dict()), registry())
        .run("价格不限", current)
        .result
    )
    assert result.status == "complete" and result.next_state["hard_filters"] == []
    assert "filter_by" not in result.compiled_query["parameters"]


def test_mass_normalized_in_query_while_state_keeps_user_units():
    patch = SearchPatch(hard_filters=(HardFilter("size", "eq", value=1, unit="kg"),))
    result = SearchComparisonOrchestrator(Backend(patch.to_dict()), registry()).run("1公斤").result
    assert result.next_state["hard_filters"][0]["unit"] == "kg"
    assert result.compiled_query["parameters"]["filter_by"] == "size_g:=1000.0"


def test_invalid_start_state_is_rejected_before_inference():
    backend = Backend(SearchPatch().to_dict())
    with pytest.raises(ValueError):
        SearchComparisonOrchestrator(backend, registry()).run("开心果", {"flavor": "pistachio"})
    assert backend.calls == 0


def test_diff_ignores_condition_and_value_array_order():
    before = SearchState(
        hard_filters=(
            HardFilter("flavor", "in", values=("pistachio", "matcha")),
            HardFilter("price", "lte", value=20),
        )
    ).to_dict()
    after = deepcopy(before)
    after["hard_filters"].reverse()
    after["hard_filters"][1]["values"].reverse()
    assert state_diff(before, after, registry()) == []


def test_ndjson_never_emits_nonfinite_numbers_or_literal_newlines():
    text = encode_event(
        "request", "left", 1, "metrics", {"bad": float("nan"), "text": "a\nb"}, True
    )
    assert len(text.splitlines()) == 1
    assert json.loads(text)["payload"] == {"bad": None, "text": "a\nb"}
