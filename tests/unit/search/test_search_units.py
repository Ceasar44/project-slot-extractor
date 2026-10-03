from dataclasses import replace

import pytest

from slot_extractor.schemas.search_patch import HardFilter
from slot_extractor.search import UnitNormalizationError, normalize_currency_unit, normalize_mass
from slot_extractor.search.unit_normalizer import normalize_condition


@pytest.mark.parametrize(
    ("value", "unit", "expected"), [(500, "g", 500), (1, "kg", 1000), (8, "oz", 226.796185)]
)
def test_registry_mass_conversion(registry, value, unit, expected):
    assert normalize_mass(value, unit, registry) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "unit"),
    [
        (0, "g"),
        (-1, "kg"),
        (True, "g"),
        ("1", "kg"),
        (1, "lb"),
        (1, None),
        (float("inf"), "g"),
        (float("nan"), "g"),
        (1e308, "kg"),
    ],
)
def test_invalid_mass(registry, value, unit):
    with pytest.raises(UnitNormalizationError):
        normalize_mass(value, unit, registry)


def test_bounds_are_converted_without_mutating_original(registry):
    item = HardFilter("size", "between", min_value=0.5, max_value=1, unit="kg")
    assert normalize_condition(item, registry) == replace(
        item, min_value=500, max_value=1000, unit="g"
    )
    assert item.unit == "kg"


def test_null_currency_preserved_until_runtime_context(registry):
    assert normalize_currency_unit(None, registry) is None
    assert normalize_currency_unit(None, registry, default_currency="USD") == "USD"
    assert normalize_currency_unit("CNY", registry) == "CNY"


@pytest.mark.parametrize(
    ("unit", "default"), [("usd", None), ("$", "USD"), ("EUR", "USD"), (None, "usd"), ([], "USD")]
)
def test_no_currency_guessing_or_exchange(registry, unit, default):
    with pytest.raises(UnitNormalizationError):
        normalize_currency_unit(unit, registry, default_currency=default)


def test_no_currency_value_conversion(registry):
    item = HardFilter("price", "eq", value=20)
    assert normalize_condition(item, registry, default_currency="USD") == replace(item, unit="USD")
