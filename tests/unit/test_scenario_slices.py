from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.evaluation.scenarios import aggregate_scenario_slices, scenario_labels
from slot_extractor.schemas.results import CaseResult, DimensionScore


def test_scenario_tags_are_distinct_and_na_is_excluded_from_metric_denominator():
    first, second = record(), multi_record()
    first["id"], second["id"] = "a", "b"
    samples = [raw_sample_from_record(i, registry()) for i in (first, second)]
    assert "scenario:replace" in scenario_labels(samples[1])
    assert "tag:multi_turn" in scenario_labels(samples[1])
    rows = [
        CaseResult("a", "", {"negation": DimensionScore("negation", None, None, "n/a")}),
        CaseResult("b", "", {"negation": DimensionScore("negation", 0.0, False, "wrong")}),
    ]
    slices = aggregate_scenario_slices(samples, rows)
    assert slices["tag:flavor"]["count"] == 2
    assert slices["tag:flavor"]["metrics"]["negation"] == {"score": 0, "applicable_count": 1}
