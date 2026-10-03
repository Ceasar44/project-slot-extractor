import json

import pytest
from search_dataset_helpers import REGISTRY_PATH, record, registry
from test_generator import SequenceBackend

from slot_extractor.data.generator import GenerationRequest, RawGenerator
from slot_extractor.data.search_generation import generate_raw_dataset, generation_requests
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def config(tmp_path, count=2):
    evaluation = record()
    evaluation["id"] = "eval-000001"
    evaluation["input"]["user_input"] = "评估专用需求"
    eval_path = tmp_path / "eval.jsonl"
    write_jsonl(eval_path, [evaluation])
    return {
        "dataset_id": "baking-raw-test",
        "registry_path": str(REGISTRY_PATH),
        "eval_path": str(eval_path),
        "counts": {"hard_soft_mix": count},
        "generation_concurrency": 1,
        "seed": 42,
        "coverage_minimums": {},
    }


def different_record():
    item = record()
    item["input"]["user_input"] += "，做吐司用"
    return item


def test_raw_pipeline_records_lineage_and_prevents_overwrite(tmp_path):
    cfg = config(tmp_path)
    backend = SequenceBackend([record(), different_record()])
    output = generate_raw_dataset(cfg, backend, tmp_path / "raw", strict_audit=True)
    rows = list(read_jsonl(output))
    assert [r["id"] for r in rows] == ["train-000001", "train-000002"]
    manifest = json.loads((output.parent / "manifest.json").read_text())
    assert len(manifest["registry_sha256"]) == len(manifest["eval_sha256"]) == 64
    assert manifest["gold_review_required"] is True
    with pytest.raises(ValueError, match="already exists"):
        generate_raw_dataset(cfg, backend, output.parent)


def test_resume_does_not_regenerate_completed_samples(tmp_path):
    cfg = config(tmp_path)
    root = tmp_path / "raw"
    with pytest.raises(RuntimeError, match="offline"):
        generate_raw_dataset(cfg, SequenceBackend([record(), RuntimeError("offline")]), root)
    assert len(list(read_jsonl(root / ".generation_checkpoint.jsonl"))) == 1
    backend = SequenceBackend([different_record()])
    output = generate_raw_dataset(cfg, backend, root)
    assert len(backend.calls) == 1
    assert len(list(read_jsonl(output))) == 2


def test_resume_refuses_changed_contract(tmp_path):
    cfg = config(tmp_path)
    root = tmp_path / "raw"
    with pytest.raises(RuntimeError):
        generate_raw_dataset(cfg, SequenceBackend([record(), RuntimeError()]), root)
    cfg["seed"] = 9
    with pytest.raises(ValueError, match="contract changed"):
        generate_raw_dataset(cfg, SequenceBackend([]), root)


def test_eval_overlap_and_duplicate_input_are_rejected(tmp_path):
    cfg = config(tmp_path)
    with pytest.raises(ValueError, match="duplicate generated input"):
        generate_raw_dataset(cfg, SequenceBackend([record(), record()]), tmp_path / "duplicates")
    write_jsonl(cfg["eval_path"], [record()])
    with pytest.raises(ValueError, match="overlaps eval"):
        generate_raw_dataset(cfg, SequenceBackend([record()]), tmp_path / "overlap")


def test_strict_coverage_failure_keeps_checkpoint_without_publishing(tmp_path):
    cfg = config(tmp_path, 1)
    cfg["coverage_minimums"] = {"fields": {"allergen": 1}}
    root = tmp_path / "raw"
    with pytest.raises(ValueError, match="coverage deficits"):
        generate_raw_dataset(cfg, SequenceBackend([record()]), root, strict_audit=True)
    assert not (root / "samples.jsonl").exists()
    assert (root / ".generation_checkpoint.jsonl").exists()


def test_checkpoint_gold_is_revalidated(tmp_path):
    cfg = config(tmp_path)
    root = tmp_path / "raw"
    with pytest.raises(RuntimeError):
        generate_raw_dataset(cfg, SequenceBackend([record(), RuntimeError()]), root)
    sample = (
        RawGenerator(SequenceBackend([record()]), registry())
        .generate_one(GenerationRequest("hard_soft_mix", 1))
        .to_dict()
    )
    sample["expected"]["hard_filters"][0]["field"] = "unknown"
    write_jsonl(root / ".generation_checkpoint.jsonl", [sample])
    with pytest.raises(ValueError, match="unknown"):
        generate_raw_dataset(cfg, SequenceBackend([]), root)


@pytest.mark.parametrize("counts", [{}, {"bad": 1}, {"sort": -1}, {"sort": True}, {"sort": 0}])
def test_invalid_quotas(counts):
    with pytest.raises(ValueError):
        generation_requests({"counts": counts})
