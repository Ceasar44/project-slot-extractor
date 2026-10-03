"""Parameterized search assertions compared with reviewed gold, without NLP inference."""

import json
from dataclasses import dataclass, field
from typing import Any

from slot_extractor.registry import Registry
from slot_extractor.schemas.dataset_contract import ASSERTION_TYPES, assertion_fields
from slot_extractor.schemas.output import parse_model_json
from slot_extractor.schemas.sample import Sample
from slot_extractor.schemas.search_patch import PATCH_FIELDS, SearchPatch
from slot_extractor.schemas.search_state import empty_search_state
from slot_extractor.search import merge_search_state
from slot_extractor.search.validator import collect_validation_errors, validate_patch

DIMENSION_OF = {
    "field_exact": "field",
    "field_replaced": "state",
    "field_preserved": "state",
    "field_cleared": "state",
    "operator_correct": "field",
    "value_normalized": "field",
    "hard_soft_correct": "intent",
    "negation_correct": "intent",
    "allergen_semantics_correct": "safety",
    "query_text_correct": "search",
    "sort_correct": "search",
    "no_unknown_field": "schema",
    "no_unknown_value": "schema",
    "no_hallucinated_filter": "safety",
    "unmapped_correct": "search",
    "minimal_patch": "state",
}


def canonical(value: Any) -> Any:
    """Ignore object/condition/set order, retaining multiplicity and original units."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    return value


def touched(patch: dict) -> set[str]:
    fields = {c["field"] for k in ("hard_filters", "soft_preferences") for c in patch[k]}
    fields.update(patch.get("clear_fields", []))
    return fields | {k for k in ("query_text", "sort") if patch[k] is not None}


def field_value(data: dict, name: str) -> Any:
    if name in {"query_text", "sort"}:
        return canonical(data[name])
    return canonical(
        {
            k: [c for c in data[k] if c["field"] == name]
            for k in ("hard_filters", "soft_preferences")
        }
    )


def present(state: dict, name: str) -> bool:
    value = field_value(state, name)
    return value is not None if name in {"query_text", "sort"} else any(value.values())


@dataclass(frozen=True)
class AssertionResult:
    expression: dict[str, Any]
    passed: bool
    dimension: str
    detail: str


@dataclass
class EvaluationContext:
    sample: Sample
    registry: Registry
    decoded: dict | None
    output: SearchPatch | None
    errors: list[dict]
    expected: dict
    before: dict
    gold_state: dict
    actual_state: dict | None
    assertions: list[AssertionResult] = field(default_factory=list)

    @property
    def actual(self):
        return self.output.to_dict() if self.output is not None else None


def prepare_evaluation(
    sample: Sample, text: str | dict | SearchPatch, registry: Registry
) -> EvaluationContext:
    decoded, output, errors = None, None, []
    try:
        decoded = (
            parse_model_json(text)
            if isinstance(text, str)
            else text.to_dict()
            if isinstance(text, SearchPatch)
            else text
        )
        errors = [vars(e) for e in collect_validation_errors(decoded, registry)]
        if not errors:
            output = validate_patch(decoded, registry)
    except ValueError as exc:
        errors = [{"code": "invalid_json", "path": "$", "message": str(exc)}]
    before = sample.input["current_search_state"] or empty_search_state().to_dict()
    gold = merge_search_state(before, sample.expected, registry).to_dict()
    actual_state = merge_search_state(before, output, registry).to_dict() if output else None
    return EvaluationContext(
        sample, registry, decoded, output, errors, sample.expected, before, gold, actual_state
    )


def _projection(patch, name, mode):
    result = []
    for key, operator in (("hard_filters", "op"), ("soft_preferences", "preference")):
        for c in patch[key]:
            if name is not None and c["field"] != name:
                continue
            if mode == "operator":
                result.append({"kind": key, "field": c["field"], "operator": c[operator]})
            elif mode == "value":
                result.append({k: v for k, v in c.items() if k != operator})
            elif mode == "strength":
                result.append({"kind": key, **{k: v for k, v in c.items() if k != operator}})
            elif mode == "negative" and c[operator] in {"not_in", "avoid"}:
                result.append({"kind": key, **c})
    return canonical(result)


def check_field_exact(ctx, name):
    return field_value(ctx.actual, name) == field_value(ctx.expected, name) and (
        name in ctx.actual["clear_fields"]
    ) == (name in ctx.expected["clear_fields"])


def check_field_replaced(ctx, name):
    return (
        not ctx.actual["reset"]
        and present(ctx.before, name)
        and name in touched(ctx.actual)
        and field_value(ctx.before, name) != field_value(ctx.gold_state, name)
        and field_value(ctx.actual_state, name) == field_value(ctx.gold_state, name)
    )


def check_field_preserved(ctx, name):
    return (
        not ctx.actual["reset"]
        and present(ctx.before, name)
        and field_value(ctx.before, name) == field_value(ctx.gold_state, name)
        and field_value(ctx.actual_state, name) == field_value(ctx.before, name)
    )


def check_field_cleared(ctx, name):
    return (
        not ctx.actual["reset"]
        and name in ctx.expected["clear_fields"]
        and name in ctx.actual["clear_fields"]
        and not present(ctx.actual_state, name)
    )


def check_allergen_semantics(ctx, name):
    return field_value(ctx.actual, "allergen") == field_value(
        ctx.expected, "allergen"
    ) and field_value(ctx.actual_state, "allergen") == field_value(ctx.gold_state, "allergen")


def check_no_hallucinated_filter(ctx, name):
    for key in ("hard_filters", "soft_preferences"):
        gold = canonical([c for c in ctx.expected[key] if name is None or c["field"] == name])
        for c in ctx.actual[key]:
            if (name is None or c["field"] == name) and canonical(c) not in gold:
                return False
    for special in ("query_text", "sort"):
        if name in {None, special} and ctx.actual[special] is not None:
            if canonical(ctx.actual[special]) != canonical(ctx.expected[special]):
                return False
    return all(
        f in ctx.expected["clear_fields"]
        for f in ctx.actual["clear_fields"]
        if name is None or f == name
    )


def check_minimal_patch(ctx, name):
    if ctx.actual["reset"] != ctx.expected["reset"]:
        return False
    if not check_no_hallucinated_filter(ctx, name):
        return False
    if ctx.actual["reset"]:
        return True
    changed = touched(ctx.actual) if name is None else touched(ctx.actual) & {name}
    for f in changed:
        if f in ctx.actual["clear_fields"]:
            if not present(ctx.before, f):
                return False
        elif field_value(ctx.before, f) == field_value(ctx.actual_state, f):
            return False
    return True


def check_no_unknown_field(ctx, name):
    data = ctx.decoded
    if not isinstance(data, dict) or set(data) != PATCH_FIELDS:
        return False
    allowed = set(ctx.registry.model_extractable_fields())
    for key, operator in (("hard_filters", "op"), ("soft_preferences", "preference")):
        if not isinstance(data[key], list):
            return False
        for item in data[key]:
            if (
                not isinstance(item, dict)
                or set(item)
                != {"field", operator, "value", "values", "min_value", "max_value", "unit"}
                or item["field"] not in allowed
            ):
                return False
    if not isinstance(data["clear_fields"], list) or any(
        f not in ctx.registry.clearable_fields() for f in data["clear_fields"]
    ):
        return False
    sort = data["sort"]
    return sort is None or (
        isinstance(sort, dict)
        and set(sort) == {"field", "order"}
        and sort["field"] in {s.field for s in ctx.registry.search.sort_fields}
    )


def check_no_unknown_value(ctx, name):
    if not check_no_unknown_field(ctx, None):
        return False
    for key in ("hard_filters", "soft_preferences"):
        for c in ctx.decoded[key]:
            if name is not None and c["field"] != name:
                continue
            spec = ctx.registry.field(c["field"])
            if spec.type == "categorical":
                if not isinstance(c["values"], list) or any(
                    v not in ctx.registry.allowed_values(c["field"]) for v in c["values"]
                ):
                    return False
    return True


CHECKERS = {
    "field_exact": check_field_exact,
    "field_replaced": check_field_replaced,
    "field_preserved": check_field_preserved,
    "field_cleared": check_field_cleared,
    "operator_correct": lambda c, f: (
        _projection(c.actual, f, "operator") == _projection(c.expected, f, "operator")
    ),
    "value_normalized": lambda c, f: (
        _projection(c.actual, f, "value") == _projection(c.expected, f, "value")
    ),
    "hard_soft_correct": lambda c, f: (
        _projection(c.actual, f, "strength") == _projection(c.expected, f, "strength")
    ),
    "negation_correct": lambda c, f: (
        _projection(c.actual, f, "negative") == _projection(c.expected, f, "negative")
    ),
    "allergen_semantics_correct": check_allergen_semantics,
    "query_text_correct": lambda c, f: c.actual["query_text"] == c.expected["query_text"],
    "sort_correct": lambda c, f: canonical(c.actual["sort"]) == canonical(c.expected["sort"]),
    "no_unknown_field": check_no_unknown_field,
    "no_unknown_value": check_no_unknown_value,
    "no_hallucinated_filter": check_no_hallucinated_filter,
    "unmapped_correct": lambda c, f: (
        canonical(c.actual["unmapped_terms"]) == canonical(c.expected["unmapped_terms"])
    ),
    "minimal_patch": check_minimal_patch,
}

if set(CHECKERS) != ASSERTION_TYPES or set(DIMENSION_OF) != ASSERTION_TYPES:
    raise RuntimeError("assertion registry differs from dataset contract")


def evaluate_in_context(assertion: dict, ctx: EvaluationContext) -> AssertionResult:
    if not isinstance(assertion, dict) or set(assertion) != {"type", "field"}:
        raise ValueError("assertion requires exactly type and field")
    kind, name = assertion["type"], assertion["field"]
    if not isinstance(kind, str) or kind not in CHECKERS:
        raise ValueError("unknown assertion type")
    if name not in assertion_fields(kind, ctx.registry):
        raise ValueError("unsupported assertion field")
    diagnostic = kind in {"no_unknown_field", "no_unknown_value"}
    try:
        ok = bool(CHECKERS[kind](ctx, name)) if ctx.output is not None or diagnostic else False
    except (TypeError, KeyError):
        # Malformed decoded payloads must remain scoreable diagnostics, not crash the run.
        if not diagnostic:
            raise
        ok = False
    detail = (
        "passed"
        if ok
        else (f"validation errors: {ctx.errors}" if ctx.errors else "differs from gold")
    )
    return AssertionResult(dict(assertion), ok, DIMENSION_OF[kind], detail)


def evaluate_assertion(
    assertion: dict, output: dict | SearchPatch | str, sample: Sample, registry: Registry
) -> AssertionResult:
    return evaluate_in_context(assertion, prepare_evaluation(sample, output, registry))
