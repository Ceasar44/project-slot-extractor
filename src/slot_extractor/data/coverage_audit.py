"""Coverage counts do not prove natural-language correctness."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.registry import Registry
from slot_extractor.schemas.dataset_contract import SCENARIO_CODES
from slot_extractor.schemas.sample import Sample


@dataclass(frozen=True)
class SemanticCoverageReport:
    sample_count: int
    scenarios: dict[str, int]
    fields: dict[str, int]
    operators: dict[str, int]
    units: dict[str, int]
    capabilities: dict[str, int]
    deficits: dict[str, int]

    @property
    def ok(self) -> bool:
        return not self.deficits


def audit_semantic_coverage(
    samples: Iterable[Sample],
    registry: Registry,
    minimums: Mapping[str, Mapping[str, int]] | None = None,
) -> SemanticCoverageReport:
    counts = {
        key: Counter() for key in ("scenarios", "fields", "operators", "units", "capabilities")
    }
    total = 0
    for sample in samples:
        total += 1
        counts["scenarios"][sample.scenario] += 1
        counts["capabilities"].update(derive_tags(sample.to_dict(), registry))
        patch = sample.expected
        counts["fields"].update(
            {f["field"] for f in patch["hard_filters"] + patch["soft_preferences"]}
            | set(patch["clear_fields"])
        )
        for kind, key in (("hard_filters", "op"), ("soft_preferences", "preference")):
            prefix = "hard" if kind == "hard_filters" else "soft"
            for item in patch[kind]:
                counts["operators"][f"{prefix}:{item['field']}:{item[key]}"] += 1
                if item["unit"] is not None:
                    counts["units"][f"{item['field']}:{item['unit']}"] += 1
    if minimums is None:
        minimums = {
            "scenarios": dict.fromkeys(SCENARIO_CODES, 1),
            "fields": dict.fromkeys(registry.model_extractable_fields(), 1),
            "capabilities": dict.fromkeys(
                ("hard", "soft", "negation", "allergen", "replace", "clear", "preserve_state"), 1
            ),
        }
    deficits = {}
    for group, requirements in minimums.items():
        if group not in counts or not isinstance(requirements, Mapping):
            raise ValueError(f"unknown coverage group: {group}")
        for name, minimum in requirements.items():
            if type(minimum) is not int or minimum < 0:
                raise ValueError("coverage minimum must be a nonnegative integer")
            if (missing := minimum - counts[group][name]) > 0:
                deficits[f"{group}:{name}"] = missing
    return SemanticCoverageReport(
        total, **{k: dict(sorted(v.items())) for k, v in counts.items()}, deficits=deficits
    )
