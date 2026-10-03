import json
from copy import deepcopy

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.sft_render import ShareGPTFormatError, messages_to_sharegpt, render_sft


@pytest.mark.parametrize("factory", [record, multi_record])
def test_render_uses_two_roles_and_exact_patch(factory):
    item = factory()
    original = deepcopy(item)
    row = render_sft(raw_sample_from_record(item, registry()), registry())
    assert set(row) == {"system", "conversations"}
    assert [m["from"] for m in row["conversations"]] == ["human", "gpt"]
    assert row["conversations"][0]["value"] == item["input"]["user_input"]
    assert json.loads(row["conversations"][1]["value"]) == item["expected"]
    assert "当前搜索状态：" in row["system"]
    assert item == original
    for metadata in (item["id"], '"scenario":', '"tags":', '"assertions":'):
        assert metadata not in str(row)
    assert "find_technicians" not in str(row)


def test_renderer_does_not_replace_patch_with_merged_state():
    item = multi_record()
    row = render_sft(raw_sample_from_record(item, registry()), registry())
    target = json.loads(row["conversations"][1]["value"])
    assert all(c["field"] != "application" for c in target["hard_filters"])
    assert "croissant_pastry" in row["system"]


@pytest.mark.parametrize(
    "messages",
    [
        [{"role": "tool", "content": "result"}],
        [{"role": "assistant", "content": "reply"}],
        [{"role": "user", "content": "hi", "tool_calls": []}],
        [{"role": "user", "content": None}],
    ],
)
def test_tool_roles_extra_keys_and_invalid_content_are_rejected(messages):
    with pytest.raises(ShareGPTFormatError):
        messages_to_sharegpt(messages)
