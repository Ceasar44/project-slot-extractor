"""Immutable catalog definitions shared by search, prompts and datasets."""

from dataclasses import dataclass
from typing import Any


class RegistryError(ValueError):
    """The catalog registry is invalid or a requested field is unknown."""


def normalize_alias(text: str) -> str:
    """Normalize exact aliases without fuzzy matching or intent inference."""
    return text.strip().casefold()


@dataclass(frozen=True)
class ValueSpec:
    code: str
    label: str
    aliases: tuple[str, ...]
    parent: str | None = None


@dataclass(frozen=True)
class UnitSpec:
    code: str
    factor: float


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    description: str
    hard_operators: tuple[str, ...]
    soft_operators: tuple[str, ...]
    values: tuple[ValueSpec, ...]
    model_extractable: bool
    clearable: bool
    facet: bool
    index_field: str
    parent_field: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    exclusive_minimum: bool = False
    unit_kind: str | None = None
    units: tuple[UnitSpec, ...] = ()
    unit_pattern: str | None = None
    base_unit: str | None = None


@dataclass(frozen=True)
class SortSpec:
    field: str
    index_field: str
    orders: tuple[str, ...]


@dataclass(frozen=True)
class SearchSpec:
    query_fields: tuple[str, ...]
    sort_fields: tuple[SortSpec, ...]


@dataclass(frozen=True)
class Registry:
    registry_version: str
    fields: tuple[FieldSpec, ...]
    search: SearchSpec

    @classmethod
    def from_dict(cls, data: Any) -> "Registry":
        from .loader import parse_registry

        return parse_registry(data)

    def field(self, name: str) -> FieldSpec:
        for field in self.fields:
            if field.name == name:
                return field
        raise RegistryError(f"unknown field: {name}")

    def model_extractable_fields(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.model_extractable)

    def clearable_fields(self) -> frozenset[str]:
        return frozenset(field.name for field in self.fields if field.clearable) | {
            "query_text",
            "sort",
        }

    def allowed_values(self, field: str) -> frozenset[str]:
        return frozenset(value.code for value in self.field(field).values)

    def hard_operators(self, field: str) -> tuple[str, ...]:
        return self.field(field).hard_operators

    def soft_operators(self, field: str) -> tuple[str, ...]:
        return self.field(field).soft_operators

    def resolve_alias(self, field: str, text: str) -> str | None:
        """For generation/tools only; never repair model predictions implicitly."""
        key = normalize_alias(text)
        for value in self.field(field).values:
            if key in {normalize_alias(item) for item in (value.code, *value.aliases)}:
                return value.code
        return None
