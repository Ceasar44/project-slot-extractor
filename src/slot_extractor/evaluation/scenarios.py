"""Search scenario and tag slices with explicit applicable denominators."""

from collections import defaultdict

from slot_extractor.schemas.results import CaseResult
from slot_extractor.schemas.sample import Sample


def scenario_labels(sample: Sample) -> set[str]:
    turn = "multi_turn" if sample.input["current_search_state"] is not None else "single_turn"
    return {f"scenario:{sample.scenario}", f"tag:{turn}", *(f"tag:{tag}" for tag in sample.tags)}


def aggregate_scenario_slices(samples: list[Sample], cases: list[CaseResult]) -> dict:
    by_id = {c.sample_id: c for c in cases}
    grouped = defaultdict(list)
    for sample in samples:
        if sample.id not in by_id:
            continue
        for label in scenario_labels(sample):
            grouped[label].append(by_id[sample.id])
    result = {}
    for label, rows in sorted(grouped.items()):
        metrics = {}
        for name in sorted({name for row in rows for name in row.dimensions}):
            values = [
                row.dimensions[name].score
                for row in rows
                if name in row.dimensions and row.dimensions[name].score is not None
            ]
            metrics[name] = {
                "score": sum(values) / len(values) if values else None,
                "applicable_count": len(values),
            }
        result[label] = {"count": len(rows), "metrics": metrics}
    return result
