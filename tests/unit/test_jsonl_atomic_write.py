from copy import deepcopy
from pathlib import Path

import pytest

from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def test_raw_writer_orders_all_nested_objects_without_changing_content(tmp_path):
    from search_dataset_helpers import multi_record

    def reverse_keys(value):
        if isinstance(value, dict):
            return {key: reverse_keys(item) for key, item in reversed(list(value.items()))}
        if isinstance(value, list):
            return [reverse_keys(item) for item in value]
        return value

    row = reverse_keys(multi_record())
    before = deepcopy(row)
    target = tmp_path / "raw.jsonl"
    write_jsonl(target, [row])
    saved = next(read_jsonl(target))
    assert saved == before
    assert row == before
    assert list(saved) == ["id", "scenario", "tags", "input", "expected", "assertions"]
    assert list(saved["input"]) == ["current_search_state", "user_input"]
    assert list(saved["input"]["current_search_state"]) == [
        "query_text",
        "hard_filters",
        "soft_preferences",
        "sort",
    ]
    assert list(saved["expected"]) == [
        "schema_version",
        "reset",
        "hard_filters",
        "soft_preferences",
        "clear_fields",
        "query_text",
        "sort",
        "unmapped_terms",
    ]
    for container in (saved["expected"], saved["input"]["current_search_state"]):
        for kind, op in (("hard_filters", "op"), ("soft_preferences", "preference")):
            for condition in container[kind]:
                assert list(condition) == [
                    "field",
                    op,
                    "value",
                    "values",
                    "min_value",
                    "max_value",
                    "unit",
                ]
    assert all(list(assertion) == ["type", "field"] for assertion in saved["assertions"])


def test_writer_keeps_unrelated_sft_layout_and_array_order(tmp_path):
    row = {"conversations": [{"value": "hello", "from": "human"}], "system": "rules"}
    target = tmp_path / "sft.jsonl"
    write_jsonl(target, [row])
    saved = next(read_jsonl(target))
    assert list(saved) == ["conversations", "system"]
    assert list(saved["conversations"][0]) == ["value", "from"]


def test_checkpoint_replace_retries_transient_file_lock(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint.jsonl"
    write_jsonl(target, [{"id": "old"}])
    original = Path.replace
    calls = []
    sleeps = []

    def replace(source, destination):
        calls.append(1)
        if len(calls) <= 2:
            assert list(read_jsonl(target)) == [{"id": "old"}]
            raise PermissionError("temporarily locked")
        return original(source, destination)

    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr("slot_extractor.utils.jsonl.time.sleep", sleeps.append)
    write_jsonl(target, [{"id": "new"}])
    assert len(calls) == 3
    assert sleeps == [0.1, 0.2]
    assert list(read_jsonl(target)) == [{"id": "new"}]


def test_persistent_lock_keeps_old_checkpoint_and_complete_temp_file(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint.jsonl"
    write_jsonl(target, [{"id": "old"}])
    calls = []

    def locked(*args):
        calls.append(1)
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr("slot_extractor.utils.jsonl.time.sleep", lambda delay: None)
    with pytest.raises(PermissionError):
        write_jsonl(target, [{"id": "new"}])
    assert len(calls) == 10
    assert list(read_jsonl(target)) == [{"id": "old"}]
    assert list(read_jsonl(target.with_suffix(".jsonl.tmp"))) == [{"id": "new"}]
