"""A portable baking smoke fixture, also used by the optional server smoke."""

import json

from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.inference.mock import MockBackend, MockResponse
from slot_extractor.registry import load_registry
from slot_extractor.schemas.sample import load_samples


def test_baking_smoke_pipeline():
    registry = load_registry("configs/catalog/registry.yaml")
    samples = load_samples("tests/fixtures/baking_search_smoke.jsonl", registry)
    backend = MockBackend(
        model="baking-smoke",
        responses={
            s.input["user_input"]: MockResponse(json.dumps(s.expected), 1, 2, 10, 100)
            for s in samples
        },
    )
    card = run_evaluation(samples, backend, registry)
    assert card.n == 2
    assert card.dimensions["schema_valid"].score == 1.0
    assert card.dimensions["allergen_semantics"].score == 1.0
    assert card.dimensions["exact_match"].score == 1.0
