import json
import threading
from concurrent.futures import ThreadPoolExecutor

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
        generate_raw_dataset(
            cfg, SequenceBackend([record() for _ in range(5)]),
            tmp_path / "duplicates", fail_fast=True,
        )
    write_jsonl(cfg["eval_path"], [record()])
    with pytest.raises(ValueError, match="overlaps eval"):
        generate_raw_dataset(
            cfg, SequenceBackend([record() for _ in range(4)]),
            tmp_path / "overlap", fail_fast=True,
        )


@pytest.mark.parametrize("overlap_eval", [False, True])
def test_duplicate_rewrite_succeeds_with_feedback_and_preserves_ids(tmp_path, overlap_eval):
    cfg = config(tmp_path, count=1 if overlap_eval else 2)
    if overlap_eval:
        write_jsonl(cfg["eval_path"], [record()])
        responses = [record(), different_record()]
    else:
        responses = [record(), record(), different_record()]
    backend = SequenceBackend(responses)
    output = generate_raw_dataset(cfg, backend, tmp_path / "raw")
    rows = list(read_jsonl(output))
    assert len(rows) == cfg["counts"]["hard_soft_mix"]
    assert [row["id"] for row in rows] == [f"train-{i:06d}" for i in range(1, len(rows) + 1)]
    feedback = backend.calls[-1][0]
    assert "不要只修改空白" in feedback[-1]["content"]
    assert json.loads(feedback[-2]["content"])["input"]["user_input"] == record()["input"]["user_input"]
    assert list(read_jsonl(output.parent / ".generation_checkpoint.jsonl")) == rows


def test_retry_exhaustion_keeps_checkpoint_and_resumes_only_missing_sample(tmp_path):
    cfg = config(tmp_path)
    cfg["max_duplicate_retries"] = 1
    root = tmp_path / "raw"
    backend = SequenceBackend([record(), record(), record()])
    with pytest.raises(ValueError, match="exhausted 1 duplicate retries"):
        generate_raw_dataset(cfg, backend, root, fail_fast=True)
    assert len(backend.calls) == 3
    assert len(list(read_jsonl(root / ".generation_checkpoint.jsonl"))) == 1
    assert not (root / "samples.jsonl").exists()
    resumed = SequenceBackend([different_record()])
    output = generate_raw_dataset(cfg, resumed, root)
    assert len(resumed.calls) == 1
    assert len(list(read_jsonl(output))) == 2


def test_concurrent_duplicate_results_are_rewritten_before_commit(tmp_path):
    cfg = config(tmp_path)
    cfg["generation_concurrency"] = 2
    barrier = threading.Barrier(2)
    lock = threading.Lock()

    class CollisionBackend:
        model = "stub"
        calls = 0

        def generate(self, messages, params=None):
            from test_generator import Result

            with lock:
                self.calls += 1
                first = self.calls <= 2
            if first:
                barrier.wait(timeout=5)
            return Result(json.dumps(record() if first else different_record()))

    backend = CollisionBackend()
    output = generate_raw_dataset(cfg, backend, tmp_path / "raw")
    rows = list(read_jsonl(output))
    assert backend.calls == 3
    assert len({r["input"]["user_input"] for r in rows}) == 2


def test_duplicate_checkpoint_is_rejected_without_regeneration(tmp_path):
    cfg = config(tmp_path)
    root = tmp_path / "raw"
    with pytest.raises(RuntimeError):
        generate_raw_dataset(cfg, SequenceBackend([record(), RuntimeError("offline")]), root)
    rows = list(read_jsonl(root / ".generation_checkpoint.jsonl"))
    duplicate = dict(rows[0], id="train-000002")
    write_jsonl(root / ".generation_checkpoint.jsonl", [rows[0], duplicate])
    backend = SequenceBackend([])
    with pytest.raises(ValueError, match="duplicate generated input"):
        generate_raw_dataset(cfg, backend, root)
    assert not backend.calls


@pytest.mark.parametrize("limit", [-1, True, "3"])
def test_invalid_duplicate_retry_limit_is_rejected(tmp_path, limit):
    cfg = config(tmp_path)
    cfg["max_duplicate_retries"] = limit
    with pytest.raises(ValueError, match="max_duplicate_retries"):
        generate_raw_dataset(cfg, SequenceBackend([]), tmp_path / "raw")


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


def test_failure_cancels_queue_and_reports_reason_before_waiting(tmp_path, monkeypatch, capsys):
    import slot_extractor.data.search_generation as pipeline

    stopping = threading.Event()

    class ObservedExecutor(ThreadPoolExecutor):
        def shutdown(self, wait=True, *, cancel_futures=False):
            if cancel_futures:
                assert "forbidden" in capsys.readouterr().err
                # Cancel queued work before releasing the one remaining in-flight request.
                super().shutdown(wait=False, cancel_futures=True)
                stopping.set()
            return super().shutdown(wait=wait, cancel_futures=cancel_futures)

    class FailingBackend:
        model = "test"
        calls = 0

        def generate(self, messages, params=None):
            self.calls += 1
            if self.calls > 1:
                assert stopping.wait(5)
            raise RuntimeError("forbidden")

    monkeypatch.setattr(pipeline, "ThreadPoolExecutor", ObservedExecutor)
    backend = FailingBackend()
    with pytest.raises(RuntimeError, match="forbidden"):
        generate_raw_dataset(config(tmp_path, count=100), backend, tmp_path / "raw")
    assert backend.calls <= 2
    assert not (tmp_path / "raw" / "samples.jsonl").exists()


def test_invalid_sample_is_skipped_and_missing_id_is_retried_on_resume(tmp_path, capsys):
    cfg = config(tmp_path, count=3)
    root = tmp_path / "raw"
    invalid = dict(record(), scenario="sort")
    backend = SequenceBackend([invalid] * 3 + [record(), different_record()])
    checkpoint = generate_raw_dataset(cfg, backend, root, strict_audit=True)
    assert checkpoint.name == ".generation_checkpoint.jsonl"
    assert [row["id"] for row in read_jsonl(checkpoint)] == ["train-000002", "train-000003"]
    assert len(backend.calls) == 5
    assert not (root / "samples.jsonl").exists()
    failures = json.loads((root / "generation_failures.json").read_text())["failures"]
    assert failures[0]["id"] == "train-000001"
    assert "failed after 3 attempts" in failures[0]["error"]
    assert "continuing" in capsys.readouterr().err
    replacement = record()
    replacement["input"]["user_input"] += " please"
    resumed = SequenceBackend([replacement])
    output = generate_raw_dataset(cfg, resumed, root, strict_audit=True)
    assert len(resumed.calls) == 1
    assert [row["id"] for row in read_jsonl(output)] == [
        "train-000001", "train-000002", "train-000003"
    ]
    assert json.loads((root / "generation_failures.json").read_text()) == {"failures": []}


def test_all_invalid_samples_leave_empty_resumable_checkpoint(tmp_path):
    invalid = dict(record(), scenario="sort")
    root = tmp_path / "raw"
    output = generate_raw_dataset(config(tmp_path), SequenceBackend([invalid] * 6), root)
    assert list(read_jsonl(output)) == []
    assert len(json.loads((root / "generation_failures.json").read_text())["failures"]) == 2
    assert not (root / "samples.jsonl").exists()


def test_validation_failure_can_still_stop_immediately(tmp_path):
    invalid = dict(record(), scenario="sort")
    backend = SequenceBackend([invalid] * 3 + [record()])
    with pytest.raises(ValueError, match="failed after 3 attempts"):
        generate_raw_dataset(config(tmp_path), backend, tmp_path / "raw", fail_fast=True)
    assert len(backend.calls) == 3


def test_duplicate_exhaustion_skips_sample_and_continues(tmp_path):
    cfg = config(tmp_path, count=3)
    cfg["max_duplicate_retries"] = 0
    checkpoint = generate_raw_dataset(
        cfg, SequenceBackend([record(), record(), different_record()]), tmp_path / "raw"
    )
    assert [row["id"] for row in read_jsonl(checkpoint)] == ["train-000001", "train-000003"]


def test_concurrent_validation_failure_does_not_cancel_other_samples(tmp_path, monkeypatch):
    from slot_extractor.data.generator import GenerationError

    cfg = config(tmp_path, count=3)
    cfg["generation_concurrency"] = 2
    barrier = threading.Barrier(2)
    original = RawGenerator.generate_one

    def generate(self, request, **kwargs):
        if request.index <= 2:
            barrier.wait(timeout=5)
        if request.index == 1:
            raise GenerationError("validation exhausted")
        item = record() if request.index == 2 else different_record()
        return original(RawGenerator(SequenceBackend([item]), registry()), request, **kwargs)

    monkeypatch.setattr(RawGenerator, "generate_one", generate)
    output = generate_raw_dataset(cfg, SequenceBackend([]), tmp_path / "raw")
    assert [row["id"] for row in read_jsonl(output)] == ["train-000002", "train-000003"]


def test_previous_scheduler_checkpoint_can_resume_but_other_changes_are_rejected(
    tmp_path, monkeypatch
):
    import slot_extractor.data.search_generation as pipeline

    cfg = config(tmp_path)
    root = tmp_path / "raw"
    identities = []
    original_hash = pipeline._hash

    def capture(value):
        if isinstance(value, dict) and "implementation_sha256" in value:
            identities.append(value)
        return original_hash(value)

    monkeypatch.setattr(pipeline, "_hash", capture)
    with pytest.raises(RuntimeError, match="offline"):
        generate_raw_dataset(cfg, SequenceBackend([record(), RuntimeError("offline")]), root)
    previous = identities[0]
    previous["implementation_sha256"]["search_generation.py"] = (
        "84e91e1ec47ed6338ef4f09d172d7a27d469622d91d82526e2f5ce18f59f7468"
    )
    meta = root / ".generation_checkpoint.meta.json"
    meta.write_text(json.dumps({"signature": original_hash(previous)}), encoding="utf-8")
    changed = dict(cfg, seed=9)
    with pytest.raises(ValueError, match="contract changed"):
        generate_raw_dataset(changed, SequenceBackend([]), root)
    output = generate_raw_dataset(cfg, SequenceBackend([different_record()]), root)
    assert len(list(read_jsonl(output))) == 2
