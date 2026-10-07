"""Registry-driven dataset validation and deterministic gold consistency.

Natural-language correctness requires gold review and Task 08 scorers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from slot_extractor.registry import Registry, RegistryError, load_registry
from slot_extractor.schemas.sample import SAMPLE_FIELDS, Sample
from slot_extractor.schemas.search_patch import ensure_exact_fields, validate_text
from slot_extractor.schemas.search_state import empty_search_state
from slot_extractor.search.state_merger import merge_search_state
from slot_extractor.search.validator import validate_patch, validate_state

# Metadata vocabulary, separate from catalog enums and Task 06 scenario specs.
SCENARIO_CODES = (
    "single_filter",
    "multi_filter",
    "hard_soft_mix",
    "negation",
    "allergy_vs_flavor",
    "replace",
    "clear",
    "preserve_state",
    "numeric_price",
    "numeric_size",
    "relative_numeric",
    "sort",
    "query_text",
    "unmapped",
    "reset",
)
FIELD_ASSERTIONS = frozenset(
    {
        "field_exact",
        "field_replaced",
        "field_preserved",
        "field_cleared",
        "operator_correct",
        "value_normalized",
    }
)
GLOBAL_ASSERTIONS = frozenset(
    {
        "hard_soft_correct",
        "negation_correct",
        "allergen_semantics_correct",
        "query_text_correct",
        "sort_correct",
        "no_unknown_field",
        "no_unknown_value",
        "no_hallucinated_filter",
        "unmapped_correct",
        "minimal_patch",
    }
)
ASSERTION_TYPES = FIELD_ASSERTIONS | GLOBAL_ASSERTIONS


class DatasetContractError(ValueError):
    pass


def load_dataset_contract(path: str | Path) -> Registry:
    """Catalog YAML replaces the duplicated business contract JSON."""
    try:
        return load_registry(Path(path))
    except (RegistryError, OSError) as exc:
        raise DatasetContractError(str(exc)) from exc


def _strings(value: Any, context: str, *, minimum: int, maximum: int) -> None:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{context}: requires {minimum} to {maximum} strings")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}: entries must be nonempty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{context}: duplicate entries")


def assertion_fields(kind: str, registry: Registry) -> list[str | None]:
    fields = list(registry.model_extractable_fields())
    if kind not in {"operator_correct", "value_normalized"}:
        fields += ["query_text", "sort"]
    return fields if kind in FIELD_ASSERTIONS else [None, *fields]


def _validate_assertions(value: Any, registry: Registry) -> None:
    if not isinstance(value, list):
        raise ValueError("assertions: must be an array")
    seen = set()
    for index, item in enumerate(value):
        ensure_exact_fields(item, {"type", "field"}, f"assertions[{index}]")
        kind, field = item["type"], item["field"]
        if not isinstance(kind, str) or kind not in ASSERTION_TYPES:
            raise ValueError(f"assertions[{index}]: unsupported assertion type")
        if field is not None and not isinstance(field, str):
            raise ValueError(f"assertions[{index}]: unsupported assertion field")
        if field not in assertion_fields(kind, registry):
            raise ValueError(f"assertions[{index}]: {kind} requires a supported field")
        if (kind, field) in seen:
            raise ValueError(f"assertions[{index}]: duplicate assertion")
        seen.add((kind, field))


def _field_value(state: dict, field: str) -> Any:
    if field in {"query_text", "sort"}:
        return state[field]

    # Compare conditions independently of array ordering, including value arrays.
    def key(item: dict) -> str:
        return repr({**item, "values": sorted(item["values"])})

    return {
        name: sorted(key(item) for item in state[name] if item["field"] == field)
        for name in ("hard_filters", "soft_preferences")
    }


def _present(state: dict, field: str) -> bool:
    value = _field_value(state, field)
    return value is not None if field in {"query_text", "sort"} else any(value.values())


def _validate_semantics(record: dict, registry: Registry) -> list[str]:
    patch = validate_patch(record["expected"], registry)
    current = record["input"]["current_search_state"]
    before = validate_state(current, registry) if current is not None else empty_search_state()
    after = merge_search_state(before, patch, registry)
    previous, merged = before.to_dict(), after.to_dict()
    new = {f.field for f in (*patch.hard_filters, *patch.soft_preferences)}
    if patch.query_text is not None:
        new.add("query_text")
    if patch.sort is not None:
        new.add("sort")
    errors = []
    if new & set(patch.clear_fields):
        errors.append("clear_fields: cannot clear and set the same field")
    if patch.reset and patch.clear_fields:
        errors.append("clear_fields: redundant when reset=true")
    for term in patch.unmapped_terms:
        if term not in record["input"]["user_input"]:
            errors.append(f"unmapped_terms: {term!r} is absent from user_input")
    scenario = record["scenario"]
    conditions = (*patch.hard_filters, *patch.soft_preferences)
    requirements = {
        "single_filter": len(conditions) == 1,
        "multi_filter": len(patch.hard_filters) >= 2,
        "hard_soft_mix": bool(patch.hard_filters and patch.soft_preferences),
        "negation": any(f.op == "not_in" for f in patch.hard_filters)
        or any(f.preference == "avoid" for f in patch.soft_preferences),
        "allergy_vs_flavor": any(f.field in {"allergen", "flavor"} for f in conditions),
        "replace": current is not None
        and any(
            _present(previous, f) and _field_value(previous, f) != _field_value(merged, f)
            for f in new
        )
        and not patch.reset,
        "clear": bool(patch.clear_fields) and not patch.reset,
        "preserve_state": current is not None
        and not patch.reset
        and bool(new)
        and any(
            _present(previous, f) and f not in new | set(patch.clear_fields)
            for f in (*registry.model_extractable_fields(), "query_text", "sort")
        ),
        "numeric_price": any(f.field == "price" for f in conditions),
        "numeric_size": any(f.field == "size" for f in conditions),
        "relative_numeric": any(
            f.preference in {"lower", "higher", "around"} for f in patch.soft_preferences
        ),
        "sort": patch.sort is not None,
        "query_text": patch.query_text is not None,
        "unmapped": bool(patch.unmapped_terms),
        "reset": patch.reset,
    }
    if not requirements[scenario]:
        if scenario == "single_filter":
            errors.append(
                "scenario 'single_filter': requires exactly one condition in "
                "hard_filters + soft_preferences combined; "
                f"got {len(patch.hard_filters)} hard and {len(patch.soft_preferences)} soft; "
                f"fields={[c.field for c in conditions]}. "
                "Use only the requested target field and do not duplicate it as hard and soft."
            )
        else:
            errors.append(f"scenario {scenario!r}: inconsistent with state/patch")
    for assertion in record["assertions"]:
        kind, field = assertion["type"], assertion["field"]
        supported = True
        if kind == "field_preserved":
            supported = (
                _present(previous, field)
                and not patch.reset
                and field not in new | set(patch.clear_fields)
                and _field_value(previous, field) == _field_value(merged, field)
            )
        elif kind == "field_replaced":
            supported = (
                _present(previous, field)
                and field in new
                and not patch.reset
                and _field_value(previous, field) != _field_value(merged, field)
            )
        elif kind == "field_cleared":
            supported = (
                _present(previous, field)
                and field in patch.clear_fields
                and not _present(merged, field)
            )
        elif kind in {"field_exact", "operator_correct", "value_normalized"}:
            supported = field in new
        elif kind == "minimal_patch" and not patch.reset:
            # Check only when requested: users can explicitly reaffirm a condition.
            candidates = new if field is None else new & {field}
            supported = all(
                _field_value(previous, f) != _field_value(merged, f) for f in candidates
            )
        if not supported:
            errors.append(f"assertions: {kind}({field}) is unsupported by gold state/patch")
    return errors


def validate_record_against_contract(record: Any, registry: Registry) -> list[str]:
    """Return diagnostics without leaking TypeError on malformed JSON shapes."""
    sample_id = record.get("id", "<unknown>") if isinstance(record, dict) else "<unknown>"
    try:
        ensure_exact_fields(record, SAMPLE_FIELDS, "sample")
        if not isinstance(record["id"], str) or not record["id"].strip():
            raise ValueError("id: must be nonempty text")
        if not isinstance(record["scenario"], str) or record["scenario"] not in SCENARIO_CODES:
            raise ValueError("scenario: unsupported search scenario")
        _strings(record["tags"], "tags", minimum=1, maximum=16)
        input_obj = ensure_exact_fields(
            record["input"],
            {"current_search_state", "user_input"},
            "input",
        )
        validate_text(input_obj["user_input"], "input.user_input", 512)
        if input_obj["current_search_state"] is not None:
            validate_state(input_obj["current_search_state"], registry)
        patch = validate_patch(record["expected"], registry)
        for item in (*patch.hard_filters, *patch.soft_preferences):
            if item.field not in registry.model_extractable_fields():
                raise ValueError(f"{item.field}: field is not model extractable")
        _validate_assertions(record["assertions"], registry)
        errors = _validate_semantics(record, registry)
    except ValueError as exc:
        errors = [str(exc)]
    return [f"{sample_id}: {error}" for error in errors]


def validate_sample_against_contract(sample: Sample, contract: Registry) -> list[str]:
    return validate_record_against_contract(sample.to_dict(), contract)


def validate_dataset_against_contract(samples: list[Sample], contract: Registry) -> None:
    errors = []
    ids = set()
    for sample in samples:
        errors.extend(validate_sample_against_contract(sample, contract))
        if not isinstance(sample.id, str):
            continue
        if sample.id in ids:
            errors.append(f"duplicate sample id: {sample.id}")
        ids.add(sample.id)
    if errors:
        raise DatasetContractError("\n".join(errors))
