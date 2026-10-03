"""Fresh JSON-compatible projections; business enums live only in the YAML."""

from typing import Any

from .models import Registry


def derive_operator_map(registry: Registry) -> dict[str, dict[str, list[str]]]:
    return {
        f.name: {"hard": list(f.hard_operators), "soft": list(f.soft_operators)}
        for f in registry.fields
    }


def derive_value_enums(registry: Registry) -> dict[str, list[str]]:
    return {f.name: [v.code for v in f.values] for f in registry.fields if f.values}


def derive_index_map(registry: Registry) -> dict[str, str]:
    return {f.name: f.index_field for f in registry.fields}


def derive_facet_map(registry: Registry) -> dict[str, str]:
    return {f.name: f.index_field for f in registry.fields if f.facet}


def derive_model_registry(registry: Registry) -> dict[str, Any]:
    """Prompt contract omits index metadata and deterministic conversion factors."""
    fields: dict[str, Any] = {}
    for f in registry.fields:
        if not f.model_extractable:
            continue
        item: dict[str, Any] = {
            "type": f.type,
            "description": f.description,
            "hard_operators": list(f.hard_operators),
            "soft_operators": list(f.soft_operators),
        }
        if f.values:
            item["values"] = [
                {"code": v.code, "label": v.label, "aliases": list(v.aliases)} for v in f.values
            ]
        for bound in ("minimum", "maximum"):
            if (value := getattr(f, bound)) is not None:
                item[bound] = value
        if f.exclusive_minimum:
            item["exclusive_minimum"] = True
        if f.unit_kind:
            item["unit_kind"] = f.unit_kind
            if f.units:
                item["units"] = [u.code for u in f.units]
            if f.unit_pattern:
                item["unit_pattern"] = f.unit_pattern
        fields[f.name] = item
    return {
        "registry_version": registry.registry_version,
        "fields": fields,
        "clear_fields": sorted(registry.clearable_fields()),
        "sort_fields": {s.field: list(s.orders) for s in registry.search.sort_fields},
    }
