"""Opt-in baking smoke against a running Qwen3 llama-server."""
import pytest

from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.inference.factory import build_backend_from_config
from slot_extractor.registry import load_registry
from slot_extractor.schemas.sample import load_samples


@pytest.mark.local_backend
def test_pipeline_llama_server_end_to_end() -> None:
    registry = load_registry("configs/catalog/registry.yaml")
    samples = load_samples("tests/fixtures/baking_search_smoke.jsonl", registry)
    backend = build_backend_from_config("configs/inference/baking-qwen3-0.6b.yaml")

    scorecard = run_evaluation(samples, backend, registry)

    assert scorecard.n == len(samples)
    assert scorecard.dimensions["schema_valid"].score == 1.0
    assert scorecard.dimensions["allergen_semantics"].score == 1.0
    # 速度改为原始时延统计，随分数卡产出（不再是 0/1 打分维度）。
    assert scorecard.timing is not None
    assert scorecard.timing.total_ms_mean is not None
