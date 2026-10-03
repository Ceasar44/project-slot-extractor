"""Deterministic unit conversion using the catalog's conversion factors."""

import math
import re
from dataclasses import replace
from decimal import Decimal

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import HardFilter, SoftPreference


class UnitNormalizationError(ValueError):
    """A unit cannot be normalized without guessing or currency conversion."""


def normalize_mass(
    value: int | float, unit: str, registry: Registry, *, field: str = "size"
) -> float:
    spec = registry.field(field)
    if spec.unit_kind != "mass" or not isinstance(unit, str):
        raise UnitNormalizationError(f"{field}: expected a mass unit")
    factor = next((u.factor for u in spec.units if u.code == unit), None)
    if factor is None:
        raise UnitNormalizationError(f"{field}: unsupported unit {unit!r}")
    if type(value) not in (int, float):
        raise UnitNormalizationError("mass must be numeric, excluding boolean")
    try:
        result = float(Decimal(str(value)) * Decimal(str(factor)))
    except (ValueError, OverflowError) as exc:
        raise UnitNormalizationError("mass is not finite") from exc
    if not math.isfinite(result) or result <= 0:
        raise UnitNormalizationError("mass must be positive and finite")
    return result


def normalize_currency_unit(
    unit: str | None,
    registry: Registry,
    *,
    default_currency: str | None = None,
    field: str = "price",
) -> str | None:
    spec = registry.field(field)
    if spec.unit_kind != "currency" or spec.unit_pattern is None:
        raise UnitNormalizationError(f"{field}: not a currency field")
    for code in (unit, default_currency):
        if code is not None and (
            not isinstance(code, str) or not re.fullmatch(spec.unit_pattern, code)
        ):
            raise UnitNormalizationError(f"{field}: invalid currency code {code!r}")
    if unit is not None and default_currency is not None and unit != default_currency:
        raise UnitNormalizationError(
            f"{field}: currency {unit} differs from index currency {default_currency}"
        )
    return unit if unit is not None else default_currency


def normalize_condition(
    item: HardFilter | SoftPreference,
    registry: Registry,
    *,
    default_currency: str | None = None,
) -> HardFilter | SoftPreference:
    """Return a new condition; never alter persisted user units."""
    spec = registry.field(item.field)
    if spec.unit_kind == "currency":
        return replace(
            item,
            unit=normalize_currency_unit(
                item.unit,
                registry,
                default_currency=default_currency,
                field=item.field,
            ),
        )
    if spec.unit_kind != "mass":
        return item
    updates = {}
    for key in ("value", "min_value", "max_value"):
        if (value := getattr(item, key)) is not None:
            updates[key] = normalize_mass(value, item.unit, registry, field=item.field)
    return replace(item, unit=spec.base_unit if updates else item.unit, **updates)
