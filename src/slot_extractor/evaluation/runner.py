"""Run a validated search dataset through a backend and gold-aware scorers."""

from copy import deepcopy
from dataclasses import asdict

from slot_extractor.evaluation.assertions import evaluate_in_context, prepare_evaluation
from slot_extractor.evaluation.scenarios import aggregate_scenario_slices
from slot_extractor.evaluation.scorecard import aggregate_scorecard
from slot_extractor.evaluation.scorer import Scorer
from slot_extractor.evaluation.scorers.search_patch import (
    AssertionScorer,
    PatchScorer,
    SchemaScorer,
    field_counts,
)
from slot_extractor.inference.base import Backend
from slot_extractor.prompts.template import PromptBuilder
from slot_extractor.registry import Registry
from slot_extractor.schemas.dataset_contract import validate_dataset_against_contract
from slot_extractor.schemas.results import CaseResult
from slot_extractor.schemas.sample import Sample


def default_scorers() -> list[Scorer]:
    return [SchemaScorer(), AssertionScorer(), PatchScorer()]


def run_evaluation(
    samples: list[Sample], backend: Backend, registry: Registry, scorers: list[Scorer] | None = None
):
    if not samples:
        raise ValueError("search evaluation dataset must be nonempty")
    validate_dataset_against_contract(samples, registry)
    builder = PromptBuilder(registry)
    active = default_scorers() if scorers is None else scorers
    cases = []
    for sample in samples:
        generation = backend.generate(builder.build_messages(sample))
        ctx = prepare_evaluation(sample, generation.text, registry)
        ctx.assertions = [evaluate_in_context(a, ctx) for a in sample.assertions]
        dimensions = {}
        for scorer in active:
            values = scorer.score(ctx)
            if dimensions.keys() & values.keys():
                raise ValueError("scorers returned duplicate metric names")
            dimensions.update(values)
        cases.append(
            CaseResult(
                sample.id,
                generation.text,
                dimensions,
                ctx.output,
                sample.scenario,
                generation.total_ms,
                generation.first_token_ms,
                generation.tokens_per_s,
                list(sample.tags),
                [asdict(a) for a in ctx.assertions],
                ctx.errors,
                field_counts(ctx),
                deepcopy(ctx.expected),
                ctx.actual_state,
                ctx.gold_state,
            )
        )
    return aggregate_scorecard(
        backend.model, cases, scenario_slices=aggregate_scenario_slices(samples, cases)
    )
