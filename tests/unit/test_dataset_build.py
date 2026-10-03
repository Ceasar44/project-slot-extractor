import json
from copy import deepcopy
from dataclasses import replace

import pytest
from search_dataset_helpers import REGISTRY_PATH, record, registry
from test_generator import scenario_record

from slot_extractor.data.dataset_build import _split, build_dataset
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def samples(count=20, scenario="hard_soft_mix", start=0):
    result = []
    catalog = registry()
    for index in range(start, start + count):
        item = scenario_record(scenario)
        item["id"] = f"train-{index + 1:06d}"
        item["input"]["user_input"] += f"；需求编号{index}"
        item["tags"] = derive_tags(item, catalog)
        result.append(raw_sample_from_record(item, catalog))
    return result


def evaluation():
    item = record()
    item["id"] = "eval-000001"
    item["input"]["user_input"] = "评估专用，20美元以内，开心果优先"
    return [item]


def build(tmp_path, rows=None, **kwargs):
    return build_dataset(
        samples() if rows is None else rows,
        evaluation(),
        tmp_path,
        "baking-v1.0",
        42,
        registry=registry(),
        registry_path=REGISTRY_PATH,
        **kwargs,
    )


def test_build_writes_only_sft_and_records_lineage(tmp_path):
    result = build(tmp_path)
    assert (result.raw_count, result.train_count, result.val_count) == (20, 18, 2)
    assert not (tmp_path / "processed/dpo").exists()
    assert not hasattr(result, "dpo_train")
    info = json.loads(result.dataset_info.read_text(encoding="utf-8"))
    assert set(info) == {"baking_v1_0_train", "baking_v1_0_val"}
    for entry in info.values():
        assert "tools" not in entry["columns"] and "function_tag" not in entry["tags"]
        assert (result.dataset_info.parent / entry["file_name"]).is_file()
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "baking-sft-v1.0"
    assert len(manifest["registry_sha256"]) == len(manifest["eval_sha256"]) == 64
    assert not set(manifest["train"]["ids"]) & set(manifest["val"]["ids"])
    assert manifest["enable_dpo"] is False
    assert len(list(read_jsonl(result.sft_train))) == 18


def test_split_is_reproducible_and_preserves_all_non_singleton_strata():
    rows = samples(20) + samples(10, "numeric_size", 20) + samples(1, "unmapped", 30)
    train, val = _split(rows, 42)
    train2, val2 = _split(list(reversed(rows)), 42)
    assert [s.id for s in train] == [s.id for s in train2]
    assert [s.id for s in val] == [s.id for s in val2]
    assert len(train) == 28 and len(val) == 3
    assert {s.scenario for s in val} == {"hard_soft_mix", "numeric_size"}
    assert "unmapped" in {s.scenario for s in train}


def test_small_strata_never_lose_their_only_training_example():
    rows = samples(2) + samples(1, "sort", 2)
    train, val = _split(rows, 42, 0.9)
    assert len(train) == 2 and len(val) == 1
    assert {s.scenario for s in train} == {"hard_soft_mix", "sort"}


@pytest.mark.parametrize("enable_dpo", [True, 1, None])
def test_dpo_cannot_silently_use_appointment_perturbations(tmp_path, enable_dpo):
    with pytest.raises(ValueError, match="Task 09"):
        build(tmp_path, enable_dpo=enable_dpo)
    assert not list(tmp_path.iterdir())


def test_input_and_eval_isolation_fail_before_writing(tmp_path):
    rows = samples(2)
    duplicate = replace(rows[1], input=deepcopy(rows[0].input))
    with pytest.raises(ValueError, match="duplicate raw input"):
        build(tmp_path, [rows[0], duplicate])
    eval_input = deepcopy(evaluation()[0]["input"])
    with pytest.raises(ValueError, match="overlaps eval"):
        build(tmp_path, [replace(rows[0], input=eval_input)])
    assert not list(tmp_path.iterdir())


def test_duplicate_ids_and_invalid_raw_rejected(tmp_path):
    rows = samples(2)
    with pytest.raises(ValueError, match="duplicate"):
        build(tmp_path, [rows[0], replace(rows[1], id=rows[0].id)])
    with pytest.raises(ValueError):
        build(tmp_path, [replace(rows[0], expected={})])
    assert not list(tmp_path.iterdir())


def test_existing_version_is_preserved(tmp_path):
    result = build(tmp_path)
    original = result.sft_train.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        build(tmp_path)
    assert result.sft_train.read_bytes() == original


def test_authoritative_raw_can_be_reused_but_not_overwritten(tmp_path):
    rows = samples(2)
    raw = tmp_path / "raw/baking-v1.0/samples.jsonl"
    write_jsonl(raw, [s.to_dict() for s in rows])
    before = raw.read_bytes()
    build(tmp_path, rows, source_raw_path=raw)
    assert raw.read_bytes() == before


def test_mismatched_existing_raw_and_registry_are_rejected(tmp_path):
    write_jsonl(tmp_path / "raw/baking-v1.0/samples.jsonl", [])
    with pytest.raises(ValueError, match="authoritative raw"):
        build(tmp_path)
    other = replace(registry(), registry_version="different")
    with pytest.raises(ValueError, match="registry object"):
        build_dataset(
            samples(),
            evaluation(),
            tmp_path,
            "baking-v1.0",
            42,
            registry=other,
            registry_path=REGISTRY_PATH,
        )


def test_strict_audit_and_empty_eval_do_not_publish(tmp_path):
    with pytest.raises(ValueError, match="search audit"):
        build(tmp_path, strict_audit=True)
    with pytest.raises(ValueError, match="nonempty"):
        build_dataset(
            samples(),
            [],
            tmp_path,
            "baking-v1.0",
            42,
            registry=registry(),
            registry_path=REGISTRY_PATH,
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("version", ["v0.1", "../baking-v1.0", "baking-v1.0/other", ""])
def test_version_names_cannot_reuse_legacy_or_escape_root(tmp_path, version):
    with pytest.raises(ValueError, match="search version"):
        build_dataset(
            samples(),
            evaluation(),
            tmp_path,
            version,
            42,
            registry=registry(),
            registry_path=REGISTRY_PATH,
        )


@pytest.mark.parametrize("ratio", [0, 1, -1, float("nan"), True])
def test_invalid_validation_fraction(ratio):
    with pytest.raises(ValueError, match="fraction"):
        _split([], 42, ratio)


def test_split_separates_turn_strata_and_preserves_exact_global_target():
    rows = samples(100)
    # Raw sort samples may legitimately use either null or an existing search state.
    sorts = samples(1, "sort", 100) + samples(2, "sort", 101)
    state = {"query_text": "existing", "hard_filters": [], "soft_preferences": [], "sort": None}
    sorts[1:] = [replace(s, input={**s.input, "current_search_state": state}) for s in sorts[1:]]
    train, val = _split(rows + sorts, 42)
    assert len(val) == 10
    assert sorts[0].id in {s.id for s in train}
    assert any(s.scenario == "sort" and s.input["current_search_state"] is not None for s in val)


def test_same_eval_id_with_different_input_is_rejected(tmp_path):
    rows = samples(1)
    with pytest.raises(ValueError, match="IDs overlap"):
        build(tmp_path, [replace(rows[0], id="eval-000001")])


def test_build_does_not_mutate_authoritative_gold(tmp_path):
    rows = samples(2)
    before = [s.to_dict() for s in rows]
    build(tmp_path, rows)
    assert [s.to_dict() for s in rows] == before
