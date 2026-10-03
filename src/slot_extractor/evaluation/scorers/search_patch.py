"""Protocol, parameterized assertions, and gold-aware SearchPatch metrics."""

from slot_extractor.evaluation.assertions import (
    EvaluationContext,
    _projection,
    canonical,
    check_allergen_semantics,
    check_field_exact,
    check_field_preserved,
    check_minimal_patch,
    check_no_hallucinated_filter,
    present,
    touched,
)
from slot_extractor.schemas.results import DimensionScore


def score_value(name, value, detail=""):
    return DimensionScore(
        name,
        value,
        None if value is None else value == 1,
        detail or ("n/a" if value is None else "gold comparison"),
    )


class SchemaScorer:
    def score(self, ctx: EvaluationContext):
        return {
            "schema_valid": score_value(
                "schema_valid",
                float(ctx.output is not None),
                str(ctx.errors) if ctx.errors else "valid SearchPatch",
            )
        }


class AssertionScorer:
    def score(self, ctx: EvaluationContext):
        value = (
            sum(a.passed for a in ctx.assertions) / len(ctx.assertions) if ctx.assertions else None
        )
        return {"assertions": score_value("assertions", value, f"{len(ctx.assertions)} assertions")}


def field_counts(ctx):
    gold = touched(ctx.expected)
    actual = touched(ctx.actual) if ctx.output is not None else set()
    correct = {f for f in gold & actual if check_field_exact(ctx, f)}
    return {"tp": len(correct), "fp": len(actual - correct), "fn": len(gold - correct)}


class PatchScorer:
    def score(self, ctx: EvaluationContext):
        good = ctx.output is not None
        gold = ctx.expected
        actual = ctx.actual
        fields = touched(gold) | (touched(actual) if good else set())
        preserved = [
            f
            for f in (*ctx.registry.model_extractable_fields(), "query_text", "sort")
            if not gold["reset"] and present(ctx.before, f) and f not in touched(gold)
        ]
        negative = bool(_projection(gold, None, "negative")) or (
            good and bool(_projection(actual, None, "negative"))
        )
        allergen = (
            present(ctx.gold_state, "allergen")
            or present(ctx.before, "allergen")
            or any(
                c["field"] in {"flavor", "allergen"}
                for k in ("hard_filters", "soft_preferences")
                for c in gold[k]
            )
            or (
                good
                and any(
                    c["field"] == "allergen"
                    for k in ("hard_filters", "soft_preferences")
                    for c in actual[k]
                )
            )
        )
        values = {
            "exact_match": float(good and canonical(actual) == canonical(gold)),
            "field_extraction": (
                sum(good and check_field_exact(ctx, f) for f in fields) / len(fields)
                if fields
                else (1.0 if good else 0.0)
            ),
            "hard_soft": float(
                good
                and _projection(actual, None, "strength") == _projection(gold, None, "strength")
            ),
            "negation": float(
                good
                and _projection(actual, None, "negative") == _projection(gold, None, "negative")
            )
            if negative
            else None,
            "state_preserve": sum(good and check_field_preserved(ctx, f) for f in preserved)
            / len(preserved)
            if preserved
            else None,
            "allergen_semantics": float(good and check_allergen_semantics(ctx, None))
            if allergen
            else None,
            "hallucination_free": float(good and check_no_hallucinated_filter(ctx, None)),
            "minimal_patch": float(good and check_minimal_patch(ctx, None)),
        }
        return {name: score_value(name, value) for name, value in values.items()}
