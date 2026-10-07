import pytest
from search_dataset_helpers import record, registry
from test_generator import SequenceBackend, scenario_record

from slot_extractor.data.generation_quality import (
    generation_response_schema,
    validate_generation_quality,
)
from slot_extractor.data.generator import GenerationError, GenerationRequest, RawGenerator
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.raw_schema import raw_response_schema


@pytest.mark.parametrize("text", ["想", "更", "y", "要", "<", "我", "能", "！!！!", "y   "])
def test_degenerate_inputs_are_rejected_and_rewritten(text):
    bad = scenario_record("single_filter")
    bad["input"]["user_input"] = text
    backend = SequenceBackend([bad, scenario_record("single_filter")])
    result = RawGenerator(backend, registry()).generate_one(GenerationRequest("single_filter", 3))
    assert result.input["user_input"] == "这次只要开心果味的。"
    assert "generation quality" in backend.calls[1][0][-1]["content"]


def test_long_unrelated_input_does_not_pass_length_check_alone():
    bad = scenario_record("single_filter")
    bad["input"]["user_input"] = "我今天想买点东西。"
    with pytest.raises(GenerationError, match="flavor=pistachio has no explicit"):
        RawGenerator(SequenceBackend([bad]), registry(), max_attempts=1).generate_one(
            GenerationRequest("single_filter", 3)
        )


def test_numeric_threshold_requires_evidence_in_request():
    bad = record()
    bad["input"]["user_input"] = "价格便宜一点，最好开心果，不要太甜"
    with pytest.raises(ValueError, match="price.value=20"):
        validate_generation_quality(raw_sample_from_record(bad, registry()), registry())


@pytest.mark.parametrize(
    "text,value",
    [
        ("I need flavor intensity of at least 3.", 3),
        ("I need flavor intensity of at least 3!", 3),
        ("Budget must be at most 12.5.", 12.5),
        ("Budget must be at most 0.", 0),
    ],
)
def test_numeric_evidence_allows_sentence_punctuation(text, value):
    from slot_extractor.schemas.search_patch import HardFilter, SearchPatch

    item = record()
    item["scenario"] = "single_filter"
    item["input"]["user_input"] = text
    field = "flavor_intensity" if "intensity" in text else "price"
    item["expected"] = SearchPatch(hard_filters=(HardFilter(field, "gte", value=value),)).to_dict()
    item["assertions"] = [{"type": "minimal_patch", "field": None}]
    validate_generation_quality(raw_sample_from_record(item, registry()), registry())


def test_decimal_does_not_provide_evidence_for_its_integer_prefix():
    item = record()
    item["input"]["user_input"] = "20.5美元以内，最好开心果，不要太甜"
    with pytest.raises(ValueError, match="price.value=20"):
        validate_generation_quality(raw_sample_from_record(item, registry()), registry())


def test_english_aliases_are_case_insensitive_and_word_bounded():
    item = scenario_record("single_filter")
    item["input"]["user_input"] = "I want PISTACHIO flavor."
    validate_generation_quality(raw_sample_from_record(item, registry()), registry())
    item["input"]["user_input"] = "I want antipistachio flavor."
    with pytest.raises(ValueError, match="no explicit"):
        validate_generation_quality(raw_sample_from_record(item, registry()), registry())


def test_english_negation_cues_are_words_and_support_typographic_apostrophes():
    from slot_extractor.data.generation_quality import _has_cue

    assert not _has_cue("piano options", ("no ",))
    assert _has_cue("don't choose those", ("don't",))
    assert _has_cue("don’t choose those", ("don't",))
    assert _has_cue("my preference is for those", ("prefer",))
    assert _has_cue("preferably avoiding those", ("prefer", "avoid"))
    assert not _has_cue("unpreferred options", ("prefer",))


def test_generation_schema_does_not_change_frozen_eval_contract():
    schema = generation_response_schema(registry())
    assert schema["$defs"]["input"]["properties"]["user_input"]["minLength"] == 1
    public = raw_response_schema(registry())
    assert public["$defs"]["input"]["properties"]["user_input"]["minLength"] == 1


def test_missing_texture_evidence_feedback_lists_accepted_aliases_and_original_input():
    item = scenario_record("single_filter")
    item["input"]["user_input"] = "找一种适合装饰的酱。"
    item["expected"]["hard_filters"][0].update(field="texture", values=["pipeable"])
    with pytest.raises(ValueError) as caught:
        validate_generation_quality(raw_sample_from_record(item, registry()), registry())
    detail = str(caught.value)
    assert "找一种适合装饰的酱。" in detail
    assert "可裱挤" in detail
    assert "可挤注" in detail
