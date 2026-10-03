"""Search evaluation configuration and explicit acceptance gates."""

import math
from pathlib import Path

import yaml

from slot_extractor.evaluation.assertions import evaluate_in_context, prepare_evaluation
from slot_extractor.evaluation.scorecard import DIMENSION_ORDER
from slot_extractor.evaluation.scorers.search_patch import (
    AssertionScorer,
    PatchScorer,
    SchemaScorer,
)

SCORERS = {"schema": SchemaScorer, "assertions": AssertionScorer, "patch": PatchScorer}
DIAGNOSTICS = {"no_unknown_field", "no_unknown_value"}


def load_evaluation_config(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    keys = {"registry", "cases", "report_dir", "backends", "scorers", "thresholds"}
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError(
            "evaluation config requires registry/cases/report_dir/backends/scorers/thresholds"
        )
    for key in ("registry", "cases", "report_dir"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(f"evaluation {key} must be a nonempty path")
    backends = data["backends"]
    if (
        not isinstance(backends, dict)
        or not backends
        or any(
            not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
            for k, v in backends.items()
        )
    ):
        raise ValueError("evaluation backends must map model keys to configuration paths")
    if data["scorers"] != list(SCORERS):
        raise ValueError("search scorers must be [schema, assertions, patch]")
    thresholds = data["thresholds"]
    if not isinstance(thresholds, dict) or not thresholds:
        raise ValueError("thresholds must be a nonempty mapping")
    for name, value in thresholds.items():
        if name not in set(DIMENSION_ORDER) | DIAGNOSTICS:
            raise ValueError(f"unknown threshold metric: {name}")
        if type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"invalid threshold: {name}")
    return data


def check_thresholds(card, samples, registry, thresholds: dict) -> dict:
    """Unknown diagnostics cover every case even when gold omitted those assertions."""
    contexts = None
    checks = {}
    for name, minimum in thresholds.items():
        if name in DIAGNOSTICS:
            if contexts is None:
                contexts = [
                    prepare_evaluation(sample, case.model_output, registry)
                    for sample, case in zip(samples, card.cases, strict=True)
                ]
            count = len(contexts)
            score = (
                sum(
                    evaluate_in_context({"type": name, "field": None}, ctx).passed
                    for ctx in contexts
                )
                / count
                if count
                else None
            )
        else:
            values = [
                case.dimensions[name].score
                for case in card.cases
                if name in case.dimensions and case.dimensions[name].score is not None
            ]
            count = len(values)
            score = card.dimensions[name].score
        checks[name] = {
            "score": score,
            "minimum": minimum,
            "applicable": count,
            "passed": score is not None and count > 0 and score >= minimum,
        }
    return {"passed": all(c["passed"] for c in checks.values()), "checks": checks}
