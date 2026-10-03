"""Search quality scorecards; latency remains descriptive, without thresholds."""

import json
import math
import re
from dataclasses import asdict
from pathlib import Path

from slot_extractor.evaluation.timing import summarize_timing
from slot_extractor.schemas.results import CaseResult, DimensionScore, SearchScorecard

DIMENSION_ORDER = [
    "schema_valid",
    "exact_match",
    "field_extraction",
    "hard_soft",
    "negation",
    "state_preserve",
    "allergen_semantics",
    "hallucination_free",
    "minimal_patch",
    "assertions",
]


def aggregate_scorecard(model: str, cases: list[CaseResult], *, scenario_slices=None):
    aggregated = {}
    for name in DIMENSION_ORDER:
        values = [
            c.dimensions[name].score
            for c in cases
            if name in c.dimensions and c.dimensions[name].score is not None
        ]
        mean = sum(values) / len(values) if values else None
        aggregated[name] = DimensionScore(
            name,
            mean,
            None if mean is None else mean == 1,
            f"{len(values)} applicable / {len(cases)} cases",
        )
    stats = {}
    for case in cases:
        for assertion in case.assertions:
            for label in (
                f"type:{assertion['expression']['type']}",
                f"dimension:{assertion['dimension']}",
            ):
                row = stats.setdefault(label, {"count": 0, "passed": 0})
                row["count"] += 1
                row["passed"] += assertion["passed"]
    for row in stats.values():
        row["score"] = row["passed"] / row["count"]
    counts = {k: sum(c.field_counts.get(k, 0) for c in cases) for k in ("tp", "fp", "fn")}
    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
    metrics = {
        **counts,
        "precision": tp / (tp + fp) if tp + fp else (0 if fn else None),
        "recall": tp / (tp + fn) if tp + fn else (0 if fp else None),
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }
    return SearchScorecard(
        model,
        len(cases),
        aggregated,
        cases,
        summarize_timing(cases),
        scenario_slices or {},
        stats,
        metrics,
    )


def render_scorecard(card: SearchScorecard) -> str:
    labels = {
        "schema_valid": "Schema Valid",
        "exact_match": "Exact Match",
        "field_extraction": "Field Extraction",
        "hard_soft": "Hard/Soft",
        "negation": "Negation",
        "state_preserve": "State Preserve",
        "allergen_semantics": "Allergen Semantics",
        "hallucination_free": "Hallucination Free",
        "minimal_patch": "Minimal Patch",
        "assertions": "Assertions",
    }
    lines = [f"SearchPatch 评估分数卡 (model={card.model} / n={card.n})"]
    for name in DIMENSION_ORDER:
        metric = card.dimensions[name]
        value = "n/a" if metric.score is None else f"{metric.score:.1%}"
        lines.append(f"{labels[name]}: {value} ({metric.detail})")
    f1 = card.field_metrics.get("f1")
    lines.append(f"Field micro F1: {'n/a' if f1 is None else f'{f1:.1%}'}")
    if card.timing and card.timing.count:
        lines.append(
            f"原始时延: mean={card.timing.total_ms_mean:.1f}ms, "
            f"p95={card.timing.total_ms_p95:.1f}ms; count={card.timing.count}"
        )
    else:
        lines.append("原始时延: n/a")
    return "\n".join(lines)


def write_scorecard_json(card: SearchScorecard, report_dir: str | Path) -> Path:
    directory = Path(report_dir)
    directory.mkdir(parents=True, exist_ok=True)
    model = re.sub(r"[^A-Za-z0-9._-]+", "_", card.model).strip("._") or "model"
    target = directory / f"scorecard-{model}.json"
    payload = asdict(card)

    # Invalid backend timing values must not create nonstandard NaN/Infinity JSON reports.
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {k: finite(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [finite(v) for v in value]
        return value

    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(finite(payload), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(target)
    return target
