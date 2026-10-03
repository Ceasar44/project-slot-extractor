from copy import deepcopy

import pytest
from search_dataset_helpers import record

from slot_extractor.data.isolation import IsolationError, assert_no_eval_overlap, input_fingerprint


def test_fingerprint_ignores_json_key_order_and_whitespace() -> None:
    original = record()
    original["input"]["user_input"] = "明天"
    reordered = deepcopy(original)
    reordered["input"] = dict(reversed(list(reordered["input"].items())))
    reordered["input"]["user_input"] = "  明天   "
    assert input_fingerprint(original) == input_fingerprint(reordered)


def test_overlap_is_rejected() -> None:
    train = record()
    evaluation = {"id": "eval-1", "input": deepcopy(train["input"])}
    with pytest.raises(IsolationError, match="eval-1"):
        assert_no_eval_overlap([train], [evaluation])
