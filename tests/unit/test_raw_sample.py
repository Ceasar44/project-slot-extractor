import json

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import RAW_FIELDS, RawSample, raw_sample_from_record
from slot_extractor.prompts.template import PromptBuilder
from slot_extractor.schemas.sample import load_samples, sample_from_record


@pytest.mark.parametrize("factory", [record, multi_record])
def test_roundtrip_and_ownership(factory):
    original = factory()
    sample = raw_sample_from_record(original, registry())
    assert isinstance(sample, RawSample)
    assert sample.to_dict() == original
    assert set(sample.to_dict()) == RAW_FIELDS
    original["expected"]["hard_filters"].clear()
    exported = sample.to_dict()
    exported["tags"].clear()
    assert sample.expected["hard_filters"]
    assert sample.tags


def test_raw_and_eval_share_contract():
    item = record()
    assert (
        raw_sample_from_record(item, registry()).to_dict()
        == sample_from_record(item, registry()).to_dict()
    )


def test_model_sees_only_input():
    sample = raw_sample_from_record(multi_record(), registry())
    messages = PromptBuilder(registry()).build_messages(sample)
    assert messages[1]["content"] == sample.input["user_input"]
    assert sample.id not in messages[0]["content"]
    assert "field_replaced" not in messages[0]["content"]


def test_load_jsonl_and_duplicate_ids(tmp_path):
    path = tmp_path / "search.jsonl"
    line = json.dumps(record(), ensure_ascii=False)
    path.write_text(line + "\n", encoding="utf-8")
    assert load_samples(path, registry())[0].to_dict() == record()
    path.write_text(line + "\n" + line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate sample id"):
        load_samples(path, registry())
