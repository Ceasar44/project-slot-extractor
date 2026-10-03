"""Closed JSON Schema derived from Registry and the SearchPatch payload grammar."""

from __future__ import annotations

from typing import Any

from slot_extractor.registry import FieldSpec, Registry
from slot_extractor.schemas.dataset_contract import (
    ASSERTION_TYPES,
    SCENARIO_CODES,
    assertion_fields,
)


def _closed(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _text(limit: int | None = None) -> dict[str, Any]:
    result = {"type": "string", "minLength": 1, "pattern": r"\S"}
    if limit is not None:
        result["maxLength"] = limit
    return result


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def _number(spec: FieldSpec) -> dict:
    schema = {"type": spec.type}
    if spec.minimum is not None:
        schema["exclusiveMinimum" if spec.exclusive_minimum else "minimum"] = spec.minimum
    if spec.maximum is not None:
        schema["maximum"] = spec.maximum
    return schema


def _unit(spec: FieldSpec, operator: str) -> dict:
    if spec.unit_kind == "mass":
        schema = {"type": "string", "enum": [u.code for u in spec.units]}
        return _nullable(schema) if operator in {"lower", "higher"} else schema
    if spec.unit_kind == "currency":
        # Runtime uses fullmatch; JSON Schema patterns otherwise match substrings.
        return _nullable({"type": "string", "pattern": f"^(?:{spec.unit_pattern})$"})
    return {"type": "null"}


def _condition(spec: FieldSpec, operator: str, *, soft: bool) -> dict:
    null = {"type": "null"}
    properties = {
        "field": {"type": "string", "const": spec.name},
        "preference" if soft else "op": {"type": "string", "const": operator},
        "value": null,
        "values": {"type": "array", "maxItems": 0},
        "min_value": null,
        "max_value": null,
        "unit": _unit(spec, operator),
    }
    if operator in {"in", "not_in", "prefer", "avoid"}:
        properties["values"] = {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "enum": [v.code for v in spec.values]},
        }
    elif operator == "between":
        properties["min_value"] = _number(spec)
        properties["max_value"] = _number(spec)
    elif operator not in {"lower", "higher"}:
        properties["value"] = {"type": "boolean"} if spec.type == "boolean" else _number(spec)
    return _closed(properties)


def _conditions(registry: Registry, *, soft: bool, model_only: bool) -> dict:
    variants = [
        _condition(spec, op, soft=soft)
        for spec in registry.fields
        if not model_only or spec.model_extractable
        for op in (spec.soft_operators if soft else spec.hard_operators)
    ]
    return {"type": "array", "items": {"anyOf": variants} if variants else False}


def _sort(registry: Registry) -> dict:
    variants = [
        _closed(
            {
                "field": {"type": "string", "const": spec.field},
                "order": {"type": "string", "enum": list(spec.orders)},
            }
        )
        for spec in registry.search.sort_fields
    ]
    return {"anyOf": [{"type": "null"}, *variants]}


def search_state_schema(registry: Registry) -> dict[str, Any]:
    return _closed(
        {
            "query_text": _nullable(_text(128)),
            "hard_filters": _conditions(registry, soft=False, model_only=False),
            "soft_preferences": _conditions(registry, soft=True, model_only=False),
            "sort": _sort(registry),
        }
    )


def search_patch_schema(registry: Registry) -> dict[str, Any]:
    return _closed(
        {
            "schema_version": {"type": "string", "const": "1.0"},
            "reset": {"type": "boolean"},
            "query_text": _nullable(_text(128)),
            "hard_filters": _conditions(registry, soft=False, model_only=True),
            "soft_preferences": _conditions(registry, soft=True, model_only=True),
            "sort": _sort(registry),
            "clear_fields": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "enum": sorted(registry.clearable_fields())},
            },
            "unmapped_terms": {
                "type": "array",
                "maxItems": 5,
                "uniqueItems": True,
                "items": _text(64),
            },
        }
    )


def raw_response_schema(registry: Registry) -> dict[str, Any]:
    schema = _closed(
        {
            "id": _text(),
            "scenario": {"type": "string", "enum": list(SCENARIO_CODES)},
            "tags": {
                "type": "array",
                "minItems": 1,
                "maxItems": 16,
                "uniqueItems": True,
                "items": _text(),
            },
            "input": {"$ref": "#/$defs/input"},
            "expected": {"$ref": "#/$defs/expected"},
            "assertions": {
                "type": "array",
                "uniqueItems": True,
                "items": {"$ref": "#/$defs/assertion"},
            },
        }
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$defs"] = {
        "input": _closed(
            {"current_search_state": _nullable({"$ref": "#/$defs/state"}), "user_input": _text(512)}
        ),
        "expected": search_patch_schema(registry),
        "state": search_state_schema(registry),
        "assertion": {
            "anyOf": [
                _closed(
                    {
                        "type": {"type": "string", "const": kind},
                        "field": {
                            "type": ["string", "null"],
                            "enum": assertion_fields(kind, registry),
                        },
                    }
                )
                for kind in sorted(ASSERTION_TYPES)
            ]
        },
    }
    return schema
