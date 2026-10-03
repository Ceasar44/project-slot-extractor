"""Deterministic SearchPatch runtime; does not perform network requests."""

from .query_compiler import (
    CompiledQuery,
    QueryCompileError,
    build_soft_ranking,
    compile_hard_filter,
    compile_typesense_query,
)
from .state_merger import fields_touched_by_patch, merge_search_state
from .unit_normalizer import UnitNormalizationError, normalize_currency_unit, normalize_mass
from .validator import (
    SearchValidationError,
    ValidationError,
    collect_validation_errors,
    validate_patch,
    validate_state,
)

__all__ = [
    "CompiledQuery",
    "QueryCompileError",
    "SearchValidationError",
    "UnitNormalizationError",
    "ValidationError",
    "build_soft_ranking",
    "collect_validation_errors",
    "compile_hard_filter",
    "compile_typesense_query",
    "fields_touched_by_patch",
    "merge_search_state",
    "normalize_currency_unit",
    "normalize_mass",
    "validate_patch",
    "validate_state",
]
