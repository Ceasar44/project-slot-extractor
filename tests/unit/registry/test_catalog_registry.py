"""Catalog contract, rejection cases and single-source derivation tests."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from slot_extractor.registry import Registry, RegistryError, load_registry
from slot_extractor.registry.derived import (
    derive_facet_map,
    derive_index_map,
    derive_model_registry,
    derive_operator_map,
    derive_value_enums,
)

CATALOG = Path(__file__).resolve().parents[3] / "configs/catalog/registry.yaml"


@pytest.fixture
def payload():
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


@pytest.fixture
def registry():
    return load_registry(CATALOG)


def field(payload, name):
    return next(item for item in payload["fields"] if item["name"] == name)


def test_catalog_matches_spec(registry):
    assert registry.registry_version == "1.0"
    assert len(registry.fields) == 14
    assert len(registry.allowed_values("flavor")) == 27
    assert len(registry.allowed_values("application")) == 10
    assert registry.field("size").index_field == "size_g"
    assert registry.field("size").exclusive_minimum
    assert registry.field("price").minimum == 0
    assert registry.field("price").unit_pattern == "^[A-Z]{3}$"
    for name in ("sweetness_level", "flavor_intensity"):
        spec = registry.field(name)
        assert (spec.type, spec.minimum, spec.maximum) == ("integer", 1, 5)
    assert registry.soft_operators("allergen") == ()
    assert registry.soft_operators("bake_stable") == ()
    assert registry.hard_operators("bake_stable") == ("eq",)
    assert registry.allowed_values("price") == frozenset()
    assert {s.field for s in registry.search.sort_fields} == {
        "price",
        "newest",
        "popularity",
        "rating",
    }


def test_units_and_relationships(registry):
    assert {u.code: u.factor for u in registry.field("size").units} == {
        "g": 1,
        "kg": 1000,
        "oz": 28.349523125,
    }
    flavor = registry.field("flavor")
    assert flavor.parent_field == "flavor_family"
    assert next(v.parent for v in flavor.values if v.code == "matcha") == "tea_coffee"
    allergens = {v.code: v.parent for v in registry.field("allergen").values}
    assert allergens["pistachio"] == "tree_nut"
    assert allergens["peanut"] is None


@pytest.mark.parametrize("text", ["开心果", "开心果味", " PISTACHIO "])
def test_alias_resolution_is_exact_and_normalized(registry, text):
    assert registry.resolve_alias("flavor", text) == "pistachio"
    assert registry.resolve_alias("flavor", "想要开心果") is None


def test_aliases_are_scoped_to_field(registry):
    assert registry.resolve_alias("flavor", "花生") == "peanut"
    assert registry.resolve_alias("allergen", "花生") == "peanut"
    assert registry.resolve_alias("application", "coffee") == "coffee_drink"
    assert registry.resolve_alias("flavor", "coffee") == "coffee"


@pytest.mark.parametrize("method", ["field", "allowed_values", "hard_operators", "soft_operators"])
def test_unknown_fields_raise(registry, method):
    with pytest.raises(RegistryError, match="unknown field"):
        getattr(registry, method)("unknown")
    with pytest.raises(RegistryError):
        registry.resolve_alias("unknown", "开心果")


def test_immutable_and_detached_from_input(payload):
    registry = Registry.from_dict(payload)
    field(payload, "flavor")["values"][0]["aliases"].append("changed")
    assert registry.resolve_alias("flavor", "changed") is None
    with pytest.raises(FrozenInstanceError):
        registry.registry_version = "2.0"
    with pytest.raises(FrozenInstanceError):
        registry.field("flavor").values[0].code = "changed"
    with pytest.raises(FrozenInstanceError):
        registry.search.sort_fields[0].orders = ()


def test_derivations_follow_configuration(payload):
    extra = {"code": "test_flavor", "label": "测试风味", "aliases": ["测试"], "parent": "fruit"}
    field(payload, "flavor")["values"].append(extra)
    field(payload, "texture")["clearable"] = False
    field(payload, "texture")["model_extractable"] = False
    field(payload, "texture")["facet"] = False
    registry = Registry.from_dict(payload)
    summary = derive_model_registry(registry)
    assert "test_flavor" in registry.allowed_values("flavor")
    assert "test_flavor" in derive_value_enums(registry)["flavor"]
    assert extra["code"] in {v["code"] for v in summary["fields"]["flavor"]["values"]}
    assert registry.resolve_alias("flavor", "测试") == "test_flavor"
    assert "texture" not in registry.clearable_fields()
    assert "texture" not in registry.model_extractable_fields()
    assert "texture" not in summary["fields"]
    assert "texture" not in derive_facet_map(registry)
    assert {"query_text", "sort"} <= registry.clearable_fields()
    assert set(summary["clear_fields"]) == registry.clearable_fields()
    assert derive_index_map(registry)["size"] == "size_g"
    assert derive_operator_map(registry)["flavor"]["hard"] == ["in", "not_in"]
    assert summary["fields"]["size"]["units"] == [u.code for u in registry.field("size").units]
    assert summary["sort_fields"] == {s.field: list(s.orders) for s in registry.search.sort_fields}
    assert "index_field" not in json.dumps(summary)
    assert "factor" not in json.dumps(summary)
    summary["fields"]["flavor"]["values"].clear()
    assert derive_model_registry(registry)["fields"]["flavor"]["values"]


@pytest.mark.parametrize("value", [None, [], {}, {"registry_version": "1.0"}])
def test_invalid_root(value):
    with pytest.raises(RegistryError):
        Registry.from_dict(value)


@pytest.mark.parametrize("version", [1.0, True, "2.0", None])
def test_invalid_versions(payload, version):
    payload["registry_version"] = version
    with pytest.raises(RegistryError, match="registry_version"):
        Registry.from_dict(payload)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("unknown", True),
        ("fields", []),
        ("fields", {}),
        ("search", None),
    ],
)
def test_invalid_top_level(payload, key, value):
    payload[key] = value
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("type", "string"),
        ("hard_operators", ["eq"]),
        ("soft_operators", ["lower"]),
        ("hard_operators", []),
        ("hard_operators", ["in", "in"]),
        ("values", []),
        ("values", {}),
        ("clearable", "true"),
        ("facet", 1),
        ("model_extractable", None),
        ("index_field", ""),
        ("name", "query_text"),
        ("name", "sort"),
        ("name", "bad-name"),
        ("description", ""),
        ("unknown", True),
        ("parent_field", "missing"),
        ("parent_field", "price"),
        ("minimum", 0),
        ("unit_kind", "mass"),
    ],
)
def test_invalid_field_configs(payload, key, value):
    field(payload, "flavor")[key] = value
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize("key", ["type", "values", "clearable", "index_field", "hard_operators"])
def test_missing_required_field_keys(payload, key):
    del field(payload, "flavor")[key]
    with pytest.raises(RegistryError, match="missing keys"):
        Registry.from_dict(payload)


def test_duplicate_fields_and_indices(payload):
    payload["fields"].append(deepcopy(payload["fields"][0]))
    with pytest.raises(RegistryError, match="duplicate field"):
        Registry.from_dict(payload)
    payload["fields"].pop()
    field(payload, "flavor")["index_field"] = "application"
    with pytest.raises(RegistryError, match="duplicate index"):
        Registry.from_dict(payload)


def test_duplicate_codes(payload):
    values = field(payload, "flavor")["values"]
    values.append(deepcopy(values[0]))
    with pytest.raises(RegistryError, match="duplicate canonical code"):
        Registry.from_dict(payload)


@pytest.mark.parametrize("alias", ["开心果", " PISTACHIO ", "MATCHA", "新别名"])
def test_alias_collisions(payload, alias):
    values = field(payload, "flavor")["values"]
    if alias == "新别名":
        values[1]["aliases"].extend([alias, alias.lower()])
    elif alias.startswith(" "):
        values[1]["aliases"].append(alias.strip())
    else:
        values[1]["aliases"].append(alias)
    with pytest.raises(RegistryError, match="duplicate"):
        Registry.from_dict(payload)


@pytest.mark.parametrize("mode", ["unknown", "missing", "self", "cycle", "cross_cycle"])
def test_invalid_hierarchies(payload, mode):
    values = field(payload, "allergen")["values"]
    if mode == "unknown":
        values[4]["parent"] = "missing"
    elif mode == "missing":
        del field(payload, "flavor")["values"][0]["parent"]
    elif mode == "self":
        values[4]["parent"] = values[4]["code"]
    elif mode == "cycle":
        values[3]["parent"] = values[4]["code"]
    else:
        family = field(payload, "flavor_family")
        family["parent_field"] = "flavor"
        for value in family["values"]:
            value["parent"] = "pistachio"
    with pytest.raises(RegistryError, match="parent"):
        Registry.from_dict(payload)


@pytest.mark.parametrize(
    ("name", "key", "value"),
    [
        ("price", "minimum", True),
        ("price", "minimum", float("nan")),
        ("price", "maximum", -1),
        ("sweetness_level", "minimum", 1.5),
        ("size", "maximum", 0),
        ("size", "exclusive_minimum", "true"),
        ("price", "unit_pattern", "["),
        ("price", "unit_kind", "unknown"),
        ("size", "base_unit", "lb"),
        ("size", "unit_pattern", "g"),
        ("bake_stable", "values", [{"code": "yes", "label": "yes", "aliases": []}]),
    ],
)
def test_invalid_numeric_and_unit_configs(payload, name, key, value):
    field(payload, name)[key] = value
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize("factor", [0, -1, True, float("inf"), "1000"])
def test_invalid_unit_factors(payload, factor):
    field(payload, "size")["units"][0]["factor"] = factor
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize("mutation", ["duplicate", "base_factor", "orphan", "no_minimum"])
def test_invalid_unit_dependencies(payload, mutation):
    size = field(payload, "size")
    if mutation == "duplicate":
        size["units"].append(deepcopy(size["units"][0]))
    elif mutation == "base_factor":
        size["units"][0]["factor"] = 2
    elif mutation == "orphan":
        del size["unit_kind"]
    else:
        del size["minimum"]
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize("value", [[], {}, None, True])
@pytest.mark.parametrize("key", ["base_unit", "unit_kind"])
def test_unit_metadata_types(payload, key, value):
    field(payload, "size")[key] = value
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("orders", ["up"]),
        ("orders", []),
        ("index_field", "other_price"),
        ("field", "flavor"),
        ("extra", True),
    ],
)
def test_invalid_sort(payload, key, value):
    payload["search"]["sort_fields"][0][key] = value
    with pytest.raises(RegistryError):
        Registry.from_dict(payload)


def test_invalid_search(payload):
    payload["search"]["sort_fields"].append(deepcopy(payload["search"]["sort_fields"][0]))
    with pytest.raises(RegistryError, match="sort"):
        Registry.from_dict(payload)
    payload["search"]["sort_fields"].pop()
    payload["search"]["query_fields"] = []
    with pytest.raises(RegistryError, match="query_fields"):
        Registry.from_dict(payload)


@pytest.mark.parametrize(
    "content",
    [
        "registry_version: '1.0'\nregistry_version: '2.0'\n",
        "fields: [",
        "!!python/object:foo {}",
        "42",
        "",
        "null",
        "? [bad, key]\n: value\n",
    ],
)
def test_yaml_errors_are_registry_errors(tmp_path, content):
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(RegistryError, match="invalid registry"):
        load_registry(path)


def test_missing_file(tmp_path):
    with pytest.raises(RegistryError, match="invalid registry"):
        load_registry(tmp_path / "missing.yaml")
