import json
from copy import deepcopy

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.evaluation.scorecard import render_scorecard, write_scorecard_json
from slot_extractor.schemas.results import GenerationResult


class Backend:
    model = "Qwen/search-model"

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.messages = []

    def generate(self, messages, params=None):
        self.messages.append(messages)
        output = next(self.outputs)
        return GenerationResult(
            output if isinstance(output, str) else json.dumps(output),
            self.model,
            1,
            2,
            10,
            tokens_per_s=20,
        )


def test_runner_keeps_assertion_diagnostics_slices_and_raw_timing(tmp_path):
    first, second = record(), multi_record()
    first["id"], second["id"] = "eval-000001", "eval-000002"
    samples = [raw_sample_from_record(i, registry()) for i in (first, second)]
    backend = Backend([first["expected"], "not JSON"])
    card = run_evaluation(samples, backend, registry())
    assert card.dimensions["schema_valid"].score == 0.5
    assert card.cases[1].output is None and card.cases[1].validation_errors
    assert all(not a["passed"] for a in card.cases[1].assertions)
    assert card.scenario_slices["scenario:replace"]["count"] == 1
    assert card.timing.count == 2
    assert "SearchPatch" in render_scorecard(card)
    assert "resource" not in card.dimensions
    assert "eval-000001" not in str(backend.messages)
    path = write_scorecard_json(card, tmp_path)
    assert path.parent == tmp_path and path.name == "scorecard-Qwen_search-model.json"
    output = json.loads(path.read_text(encoding="utf-8"))
    assert output["cases"][1]["model_output"] == "not JSON"
    assert output["assertion_stats"] and output["field_metrics"]["fn"] > 0
    assert output["cases"][0]["expected"] == first["expected"]
    assert output["cases"][0]["merged_state"] == output["cases"][0]["expected_state"]
    assert output["cases"][1]["merged_state"] is None
    assert output["cases"][1]["expected_state"] is not None


def test_absent_assertions_and_inapplicable_metrics_are_na():
    item = record()
    item["assertions"] = []
    card = run_evaluation(
        [raw_sample_from_record(item, registry())], Backend([item["expected"]]), registry()
    )
    assert card.dimensions["assertions"].score is None
    assert card.dimensions["negation"].score is None
    assert card.dimensions["state_preserve"].score is None
    assert card.field_metrics["f1"] == 1


def test_invalid_gold_and_duplicate_ids_fail_before_backend_call():
    item = record()
    sample = raw_sample_from_record(item, registry())
    backend = Backend([])
    with pytest.raises(ValueError):
        run_evaluation([sample, deepcopy(sample)], backend, registry())
    with pytest.raises(ValueError, match="nonempty"):
        run_evaluation([], backend, registry())
    assert not backend.messages


def test_backend_transport_failure_propagates():
    class FailingBackend(Backend):
        def generate(self, messages, params=None):
            raise ConnectionError("offline")

    sample = raw_sample_from_record(record(), registry())
    with pytest.raises(ConnectionError, match="offline"):
        run_evaluation([sample], FailingBackend([]), registry())


def test_duplicate_scorer_metric_is_rejected():
    from slot_extractor.evaluation.scorers import SchemaScorer

    item = record()
    sample = raw_sample_from_record(item, registry())
    with pytest.raises(ValueError, match="duplicate metric"):
        run_evaluation(
            [sample], Backend([item["expected"]]), registry(), [SchemaScorer(), SchemaScorer()]
        )


def test_nonfinite_backend_timing_does_not_break_json_report(tmp_path):
    class BadTimingBackend(Backend):
        def generate(self, messages, params=None):
            result = super().generate(messages, params)
            return GenerationResult(
                result.text,
                self.model,
                1,
                -1,
                float("nan"),
                tokens_per_s=float("inf"),
            )

    item = record()
    card = run_evaluation(
        [raw_sample_from_record(item, registry())], BadTimingBackend([item["expected"]]), registry()
    )
    assert card.timing.count == 0
    assert card.timing.first_token_ms_mean is None
    assert card.timing.tokens_per_s_mean is None
    report = json.loads(write_scorecard_json(card, tmp_path).read_text(encoding="utf-8"))
    assert report["cases"][0]["total_ms"] is None
    assert report["cases"][0]["tokens_per_s"] is None
