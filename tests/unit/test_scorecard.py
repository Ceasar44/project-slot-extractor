from slot_extractor.evaluation.scorecard import aggregate_scorecard, render_scorecard
from slot_extractor.schemas.results import CaseResult, DimensionScore


def test_scorecard_uses_applicable_denominators_and_micro_field_counts():
    rows = [
        CaseResult(
            "1",
            "",
            {"exact_match": DimensionScore("exact_match", 1.0, True, "ok")},
            field_counts={"tp": 2, "fp": 0, "fn": 0},
        ),
        CaseResult(
            "2",
            "",
            {"exact_match": DimensionScore("exact_match", 0.0, False, "wrong")},
            field_counts={"tp": 0, "fp": 1, "fn": 1},
        ),
    ]
    card = aggregate_scorecard("model", rows)
    assert card.dimensions["exact_match"].score == 0.5
    assert card.dimensions["allergen_semantics"].score is None
    assert card.field_metrics["precision"] == 2 / 3
    assert card.field_metrics["recall"] == 2 / 3
    assert card.field_metrics["f1"] == 2 / 3
    assert "n/a" in render_scorecard(card)
