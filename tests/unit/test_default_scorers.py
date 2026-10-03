from slot_extractor.evaluation.runner import default_scorers


def test_default_scorers_are_search_only():
    assert [type(s).__name__ for s in default_scorers()] == [
        "SchemaScorer",
        "AssertionScorer",
        "PatchScorer",
    ]
