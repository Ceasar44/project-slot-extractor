import json
from dataclasses import dataclass

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.generator import (
    GenerationError,
    GenerationRequest,
    RawGenerator,
    build_generation_messages,
    generation_sample_id,
    parse_raw_json,
)
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference, SortSpec


@dataclass
class Result:
    text: str


class SequenceBackend:
    model = "stub"

    def __init__(self, records):
        self.records = iter(records)
        self.calls = []

    def generate(self, messages, params=None):
        self.calls.append((messages, params))
        value = next(self.records)
        if isinstance(value, Exception):
            raise value
        return Result(value if isinstance(value, str) else json.dumps(value))


def scenario_record(scenario):
    item = multi_record() if SCENARIOS[scenario].multi_turn else record()
    item["scenario"] = scenario
    patches = {
        "single_filter": SearchPatch(
            hard_filters=(HardFilter("flavor", "in", values=("pistachio",)),)
        ),
        "multi_filter": SearchPatch(
            hard_filters=(
                HardFilter("flavor", "in", values=("pistachio",)),
                HardFilter("price", "lte", value=20),
            )
        ),
        "negation": SearchPatch(hard_filters=(HardFilter("flavor", "not_in", values=("peanut",)),)),
        "allergy_vs_flavor": SearchPatch(
            hard_filters=(HardFilter("allergen", "not_in", values=("peanut",)),)
        ),
        "clear": SearchPatch(clear_fields=("flavor",)),
        "numeric_price": SearchPatch(hard_filters=(HardFilter("price", "lte", value=20),)),
        "numeric_size": SearchPatch(hard_filters=(HardFilter("size", "eq", value=8, unit="oz"),)),
        "relative_numeric": SearchPatch(
            soft_preferences=(SoftPreference("sweetness_level", "lower"),)
        ),
        "sort": SearchPatch(sort=SortSpec("price", "asc")),
        "query_text": SearchPatch(query_text="Dubai Chocolate"),
        "unmapped": SearchPatch(unmapped_terms=("高级一点",)),
        "reset": SearchPatch(
            reset=True, hard_filters=(HardFilter("flavor", "in", values=("strawberry",)),)
        ),
    }
    if scenario in patches:
        item["expected"] = patches[scenario].to_dict()
    if scenario == "unmapped":
        item["input"]["user_input"] += "，高级一点"
    item["assertions"] = [{"type": "minimal_patch", "field": None}]
    return item


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_all_scenarios_generate_contract_valid_gold(scenario):
    backend = SequenceBackend([scenario_record(scenario)])
    index = 3 if scenario == "single_filter" else 19
    sample = RawGenerator(backend, registry()).generate_one(GenerationRequest(scenario, index))
    assert sample.id == f"train-{index:06d}"
    assert sample.scenario == scenario
    assert scenario in sample.tags
    params = backend.calls[0][1]
    assert params.response_schema_name == "baking_search_raw"
    assert params.response_schema["additionalProperties"] is False


def test_retry_feedback_and_program_owned_metadata():
    bad = record()
    bad["expected"]["hard_filters"][0]["field"] = "invented"
    good = record()
    good["id"], good["tags"] = "model-made-id", ["invented"]
    backend = SequenceBackend([bad, good])
    sample = RawGenerator(backend, registry()).generate_one(GenerationRequest("hard_soft_mix", 1))
    assert sample.id == "train-000001"
    assert "invented" not in sample.tags
    assert "unknown" in backend.calls[1][0][-1]["content"]
    assert len(backend.calls) == 2


@pytest.mark.parametrize("mutation", ["scenario", "assertions", "turn", "extra"])
def test_generation_rejects_invalid_gold(mutation):
    item = record()
    if mutation == "scenario":
        item["scenario"] = "numeric_price"
    elif mutation == "assertions":
        item["assertions"] = []
    elif mutation == "turn":
        item = multi_record()
        item["scenario"] = "hard_soft_mix"
    else:
        item["extra"] = True
    with pytest.raises(GenerationError):
        RawGenerator(SequenceBackend([item]), registry(), max_attempts=1).generate_one(
            GenerationRequest("hard_soft_mix", 1)
        )


@pytest.mark.parametrize("text", ["```json\n{}\n```", '{"x":1,"x":2}', '{"x":NaN}', "[]"])
def test_strict_json_boundary(text):
    with pytest.raises(GenerationError):
        parse_raw_json(text)


@pytest.mark.parametrize(
    "generation_request",
    [
        GenerationRequest("bad", 1),
        GenerationRequest("sort", True),
        GenerationRequest("sort", 0),
        GenerationRequest("sort", 1000000),
        GenerationRequest("sort", 1, split="bad"),
    ],
)
def test_invalid_request_rejected_before_backend(generation_request):
    with pytest.raises(GenerationError):
        generation_sample_id(generation_request)


def test_duplicate_requests_fail_before_generation():
    backend = SequenceBackend([])
    request = GenerationRequest("sort", 1)
    with pytest.raises(GenerationError, match="duplicate"):
        RawGenerator(backend, registry()).generate_many([request, request])
    assert not backend.calls


def test_prompt_uses_registry_and_search_contract():
    messages = build_generation_messages(GenerationRequest("numeric_size", 1), registry())
    text = str(messages)
    for expected in ("current_search_state", "SearchPatch", "assertions", "pistachio", "原单位"):
        assert expected in text
    assert "find_technicians" not in text


@pytest.mark.parametrize("index,name", enumerate(registry().model_extractable_fields(), 1))
def test_single_filter_quota_covers_every_registry_field(index, name):
    spec = registry().field(name)
    if spec.values:
        condition = HardFilter(name, "in", values=(spec.values[0].code,))
    elif spec.type == "boolean":
        condition = HardFilter(name, "eq", value=True)
    else:
        condition = HardFilter(name, "eq", value=2, unit="g" if spec.units else None)
    item = scenario_record("single_filter")
    item["expected"] = SearchPatch(hard_filters=(condition,)).to_dict()
    sample = RawGenerator(SequenceBackend([item]), registry()).generate_one(
        GenerationRequest("single_filter", index)
    )
    assert sample.expected["hard_filters"][0]["field"] == name


def test_allergy_scenario_alternates_safety_and_flavor_exclusion():
    item = scenario_record("allergy_vs_flavor")
    item["expected"] = SearchPatch(
        hard_filters=(HardFilter("flavor", "not_in", values=("peanut",)),)
    ).to_dict()
    sample = RawGenerator(SequenceBackend([item]), registry()).generate_one(
        GenerationRequest("allergy_vs_flavor", 2)
    )
    assert "allergen" not in sample.tags
    with pytest.raises(GenerationError, match="exclude only allergen"):
        RawGenerator(SequenceBackend([item]), registry(), max_attempts=1).generate_one(
            GenerationRequest("allergy_vs_flavor", 1)
        )
