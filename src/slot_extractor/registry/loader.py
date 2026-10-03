"""Strict YAML boundary: reject drift before constructing catalog objects."""

import math
import re
from pathlib import Path
from typing import Any

import yaml

from .models import (
    FieldSpec,
    Registry,
    RegistryError,
    SearchSpec,
    SortSpec,
    UnitSpec,
    ValueSpec,
    normalize_alias,
)

# Protocol grammar, not business field/value enumerations.
_OPS = {
    "categorical": ({"in", "not_in"}, {"prefer", "avoid"}),
    "boolean": ({"eq"}, set()),
    "integer": ({"eq", "gte", "lte", "between"}, {"lower", "higher", "around", "between"}),
    "number": ({"eq", "gte", "lte", "between"}, {"lower", "higher", "around", "between"}),
}


def _object(data: Any, required: set[str], optional: set[str], context: str) -> dict:
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise RegistryError(f"{context}: expected object with string keys")
    if missing := required - data.keys():
        raise RegistryError(f"{context}: missing keys {sorted(missing)}")
    if unknown := data.keys() - required - optional:
        raise RegistryError(f"{context}: unknown keys {sorted(unknown)}")
    return data


def _text(value: Any, context: str, *, code: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RegistryError(f"{context}: expected nonempty trimmed string")
    if code and not re.fullmatch(r"[a-z][a-z0-9_]*", value):
        raise RegistryError(f"{context}: invalid code {value!r}")
    return value


def _list(value: Any, context: str) -> list:
    if not isinstance(value, list):
        raise RegistryError(f"{context}: expected list")
    return value


def _strings(value: Any, context: str) -> tuple[str, ...]:
    result = tuple(_text(item, context) for item in _list(value, context))
    if len(set(result)) != len(result):
        raise RegistryError(f"{context}: duplicate entry")
    return result


def _number(value: Any, context: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise RegistryError(f"{context}: expected finite number")
    return value


def _field(raw: Any) -> FieldSpec:
    required = {
        "name",
        "type",
        "description",
        "hard_operators",
        "soft_operators",
        "values",
        "model_extractable",
        "clearable",
        "facet",
        "index_field",
    }
    optional = {
        "parent_field",
        "minimum",
        "maximum",
        "exclusive_minimum",
        "unit_kind",
        "units",
        "unit_pattern",
        "base_unit",
    }
    raw = _object(raw, required, optional, "field")
    name = _text(raw["name"], "field.name", code=True)
    kind = _text(raw["type"], name)
    if kind not in _OPS:
        raise RegistryError(f"{name}: unsupported type {kind}")
    hard = _strings(raw["hard_operators"], name)
    soft = _strings(raw["soft_operators"], name)
    if not hard or set(hard) - _OPS[kind][0] or set(soft) - _OPS[kind][1]:
        raise RegistryError(f"{name}: illegal operators for {kind}")
    for flag in ("model_extractable", "clearable", "facet", "exclusive_minimum"):
        if flag in raw and type(raw[flag]) is not bool:
            raise RegistryError(f"{name}.{flag}: expected boolean")
    values = []
    aliases: set[str] = set()
    codes: set[str] = set()
    for item in _list(raw["values"], name):
        item = _object(item, {"code", "label", "aliases"}, {"parent"}, name)
        code = _text(item["code"], name, code=True)
        if code in codes:
            raise RegistryError(f"{name}: duplicate canonical code {code}")
        codes.add(code)
        value_aliases = _strings(item["aliases"], name)
        for alias in (code, *value_aliases):
            key = normalize_alias(alias)
            if key in aliases:
                raise RegistryError(f"{name}: duplicate alias {alias!r}")
            aliases.add(key)
        parent = _text(item["parent"], name, code=True) if "parent" in item else None
        values.append(ValueSpec(code, _text(item["label"], name), value_aliases, parent))
    if (kind == "categorical") != bool(values):
        raise RegistryError(f"{name}: only categorical fields require values")
    kwargs = {key: raw[key] for key in optional if key in raw and key != "units"}
    for bound in ("minimum", "maximum"):
        if bound in kwargs:
            _number(kwargs[bound], f"{name}.{bound}")
            if kind not in ("integer", "number"):
                raise RegistryError(f"{name}: bounds require numeric type")
            if kind == "integer" and int(kwargs[bound]) != kwargs[bound]:
                raise RegistryError(f"{name}: integer bounds must be integral")
    if "minimum" in kwargs and "maximum" in kwargs:
        if kwargs["minimum"] > kwargs["maximum"] or (
            kwargs.get("exclusive_minimum", False) and kwargs["minimum"] == kwargs["maximum"]
        ):
            raise RegistryError(f"{name}: invalid bounds")
    if "exclusive_minimum" in kwargs and "minimum" not in kwargs:
        raise RegistryError(f"{name}: exclusive_minimum requires minimum")
    if "parent_field" in kwargs:
        _text(kwargs["parent_field"], name, code=True)
    for key in ("unit_kind", "base_unit"):
        if key in kwargs:
            _text(kwargs[key], f"{name}.{key}")
    unit_kind = kwargs.get("unit_kind")
    units = []
    for item in _list(raw.get("units", []), name):
        item = _object(item, {"code", "factor"}, set(), name)
        unit = _text(item["code"], name)
        factor = _number(item["factor"], name)
        if factor <= 0 or unit in {u.code for u in units}:
            raise RegistryError(f"{name}: invalid or duplicate unit")
        units.append(UnitSpec(unit, factor))
    if unit_kind is not None:
        if kind != "number" or unit_kind not in ("mass", "currency"):
            raise RegistryError(f"{name}: invalid unit_kind")
        if unit_kind == "mass":
            base = kwargs.get("base_unit")
            if not units or base not in {u.code for u in units}:
                raise RegistryError(f"{name}: mass requires units and base_unit")
            if next(u.factor for u in units if u.code == base) != 1:
                raise RegistryError(f"{name}: base unit factor must equal 1")
            if "unit_pattern" in kwargs:
                raise RegistryError(f"{name}: mass cannot use unit_pattern")
        else:
            pattern = _text(kwargs.get("unit_pattern"), name)
            try:
                re.compile(pattern)
            except re.error as exc:
                raise RegistryError(f"{name}: invalid unit_pattern") from exc
            if units or "base_unit" in kwargs:
                raise RegistryError(f"{name}: currency cannot define conversion factors")
    elif units or "unit_pattern" in kwargs or "base_unit" in kwargs:
        raise RegistryError(f"{name}: units require unit_kind")
    return FieldSpec(
        name,
        kind,
        _text(raw["description"], name),
        hard,
        soft,
        tuple(values),
        raw["model_extractable"],
        raw["clearable"],
        raw["facet"],
        _text(raw["index_field"], name, code=True),
        units=tuple(units),
        **kwargs,
    )


def _check_relations(fields: tuple[FieldSpec, ...]) -> None:
    by_name = {field.name: field for field in fields}
    edges: dict[tuple[str, str], tuple[str, str]] = {}
    for field in fields:
        if field.parent_field:
            target = by_name.get(field.parent_field)
            if field.type != "categorical" or target is None or target.type != "categorical":
                raise RegistryError(f"{field.name}: invalid parent_field")
        else:
            target = field
        for value in field.values:
            if value.parent:
                if value.parent not in {v.code for v in target.values}:
                    raise RegistryError(f"{field.name}.{value.code}: invalid parent {value.parent}")
                edges[field.name, value.code] = (target.name, value.parent)
            elif field.parent_field:
                raise RegistryError(f"{field.name}.{value.code}: missing parent")
    for node in edges:
        seen = set()
        current = node
        while current in edges:
            if current in seen:
                raise RegistryError(f"cyclic parent relationship: {node}")
            seen.add(current)
            current = edges[current]


def parse_registry(data: Any) -> Registry:
    data = _object(data, {"registry_version", "fields", "search"}, set(), "registry")
    if data["registry_version"] != "1.0":
        raise RegistryError("registry_version must be string '1.0'")
    fields = tuple(_field(raw) for raw in _list(data["fields"], "fields"))
    if not fields or len({f.name for f in fields}) != len(fields):
        raise RegistryError("empty fields or duplicate field name")
    if any(f.name in {"query_text", "sort"} for f in fields):
        raise RegistryError("query_text and sort are reserved fields")
    if len({f.index_field for f in fields}) != len(fields):
        raise RegistryError("duplicate index_field")
    _check_relations(fields)
    search = _object(data["search"], {"query_fields", "sort_fields"}, set(), "search")
    query = _strings(search["query_fields"], "query_fields")
    if not query:
        raise RegistryError("query_fields cannot be empty")
    for item in query:
        _text(item, "query_fields", code=True)
    sorts = []
    for raw in _list(search["sort_fields"], "sort_fields"):
        raw = _object(raw, {"field", "index_field", "orders"}, set(), "sort")
        field = _text(raw["field"], "sort.field", code=True)
        orders = _strings(raw["orders"], "sort.orders")
        if not orders or set(orders) - {"asc", "desc"} or field in {s.field for s in sorts}:
            raise RegistryError("invalid or duplicate sort")
        index = _text(raw["index_field"], "sort.index_field", code=True)
        existing = next((f for f in fields if f.name == field), None)
        if existing and (
            existing.type not in ("integer", "number") or existing.index_field != index
        ):
            raise RegistryError(f"sort {field}: inconsistent field mapping")
        sorts.append(SortSpec(field, index, orders))
    return Registry(data["registry_version"], fields, SearchSpec(query, tuple(sorts)))


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader normally silently overwrites duplicate mapping keys."""


def _mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise RegistryError(f"invalid or duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node)
    return result


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_registry(path: Path) -> Registry:
    try:
        data = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
        return Registry.from_dict(data)
    except (OSError, UnicodeError, yaml.YAMLError, RegistryError) as exc:
        raise RegistryError(f"invalid registry {path}: {exc}") from exc
