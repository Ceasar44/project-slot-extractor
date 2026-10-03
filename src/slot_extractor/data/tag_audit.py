"""Derive bounded tags from validated gold, never generated free-form labels."""

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from slot_extractor.registry import Registry
from slot_extractor.schemas.sample import Sample
from slot_extractor.search import merge_search_state


def derive_tags(record: dict, registry: Registry) -> list[str]:
    patch = record["expected"]
    current = record["input"]["current_search_state"]
    after = merge_search_state(current, patch, registry).to_dict()
    hard, soft = patch["hard_filters"], patch["soft_preferences"]
    tags = ["multi_turn" if current is not None else "single_turn", record["scenario"]]
    if hard:
        tags.append("hard")
    if soft:
        tags.append("soft")
    if hard and soft:
        tags.append("hard_soft")
    if any(f["op"] == "not_in" for f in hard) or any(f["preference"] == "avoid" for f in soft):
        tags.append("negation")
    if any(f["preference"] in {"lower", "higher", "around"} for f in soft):
        tags.append("relative_numeric")
    if patch["clear_fields"]:
        tags.append("clear")
    if patch["reset"]:
        tags.append("reset")
    if patch["query_text"] is not None:
        tags.append("query_text")
    if patch["sort"] is not None:
        tags.append("sort")
    if patch["unmapped_terms"]:
        tags.append("unmapped")
    touched = {f["field"] for f in hard + soft} | set(patch["clear_fields"])
    if patch["query_text"] is not None:
        touched.add("query_text")
    if patch["sort"] is not None:
        touched.add("sort")
    if current is not None and not patch["reset"]:
        old_fields = {f["field"] for f in current["hard_filters"] + current["soft_preferences"]}

        def conditions_for(state, field):
            return sorted(
                json.dumps(c, sort_keys=True)
                for key in ("hard_filters", "soft_preferences")
                for c in state[key]
                if c["field"] == field
            )

        if any(
            conditions_for(current, f) != conditions_for(after, f)
            for f in old_fields & {c["field"] for c in hard + soft}
        ):
            tags.append("replace")
        if old_fields - touched:
            tags.append("preserve_state")
        if any(
            current[f] is not None and current[f] == after[f] and f not in touched
            for f in ("query_text", "sort")
        ):
            tags.append("preserve_state")
    tags.extend(sorted({f["field"] for f in hard + soft} | set(patch["clear_fields"])))
    # Capability tags take precedence when many fields would exceed the raw limit.
    return list(dict.fromkeys(tags))[:16]


@dataclass(frozen=True)
class TagAuditReport:
    counts: dict[str, int]
    mismatched_ids: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.mismatched_ids


def audit_tags(samples: Iterable[Sample], registry: Registry) -> TagAuditReport:
    counts: Counter[str] = Counter()
    mismatches = []
    for sample in samples:
        tags = derive_tags(sample.to_dict(), registry)
        counts.update(tags)
        if sample.tags != tags:
            mismatches.append(sample.id)
    return TagAuditReport(dict(sorted(counts.items())), tuple(mismatches))
