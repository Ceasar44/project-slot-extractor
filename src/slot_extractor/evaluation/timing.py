"""Descriptive backend timing shared by search reports."""

import math

from slot_extractor.schemas.results import TimingSummary


def summarize_timing(cases):
    def values(attribute):
        return sorted(
            v
            for c in cases
            if type(v := getattr(c, attribute)) in {int, float} and math.isfinite(v) and v >= 0
        )

    def mean(items):
        return sum(items) / len(items) if items else None

    def percentile(items, fraction):
        if not items:
            return None
        rank = fraction * (len(items) - 1)
        low = int(rank)
        return items[low] + (items[min(low + 1, len(items) - 1)] - items[low]) * (rank - low)

    totals = values("total_ms")
    return TimingSummary(
        len(totals),
        mean(totals),
        percentile(totals, 0.5),
        percentile(totals, 0.95),
        max(totals) if totals else None,
        min(totals) if totals else None,
        mean(values("first_token_ms")),
        mean(values("tokens_per_s")),
    )
