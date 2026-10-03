"""Strict model JSON boundary for SearchPatch output."""

from __future__ import annotations

import json
import math
from typing import Any

from slot_extractor.registry import Registry

from .search_patch import SearchPatch, SearchPatchValidationError, validate_search_patch

OutputValidationError = SearchPatchValidationError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OutputValidationError(f"model output contains duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise OutputValidationError(f"model output contains nonfinite JSON number: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise OutputValidationError(f"model output contains nonfinite JSON number: {value}")
    return number


def parse_model_json(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise OutputValidationError("model output must be JSON text")
    stripped = text.strip()
    if stripped.startswith("```") or stripped.endswith("```"):
        raise OutputValidationError("model output must be raw JSON, not Markdown fenced JSON")
    try:
        value = json.loads(
            stripped,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except json.JSONDecodeError as exc:
        raise OutputValidationError(f"model output is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise OutputValidationError("model output must be a JSON object")
    return value


def validate_search_patch_output(data: Any, registry: Registry) -> SearchPatch:
    """Validate decoded JSON, returning a detached immutable SearchPatch."""
    return validate_search_patch(data, registry)
