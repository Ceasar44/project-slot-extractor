from dataclasses import replace

import pytest
from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.raw_validator import RawValidationError, validate_raw_sample
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference


@pytest.mark.parametrize("factory", [record, multi_record])
def test_valid_raw(factory):
    validate_raw_sample(raw_sample_from_record(factory(), registry()), registry())


@pytest.mark.parametrize(
    "condition",
    [
        HardFilter("price", "lte", value=True),
        HardFilter("price", "lte", value=-1),
        HardFilter("price", "lte", value=float("nan")),
        HardFilter("size", "eq", value=0, unit="g"),
        HardFilter("size", "eq", value=8),
        HardFilter("size", "eq", value=8, unit="lb"),
        HardFilter("sweetness_level", "lte", value=2.5),
        HardFilter("sweetness_level", "lte", value=6),
        HardFilter("flavor", "in", values=("开心果",)),
        HardFilter("unknown", "in", values=("pistachio",)),
        HardFilter("price", "between", min_value=30, max_value=20),
    ],
)
def test_invalid_gold_conditions(condition):
    sample = raw_sample_from_record(record(), registry())
    patch = SearchPatch(hard_filters=(condition,)).to_dict()
    with pytest.raises(RawValidationError):
        validate_raw_sample(replace(sample, expected=patch), registry())


def test_conflicting_gold_filters_and_state():
    item = record()
    item["expected"]["hard_filters"].append(
        HardFilter("price", "gte", value=30, unit="USD").to_dict()
    )
    with pytest.raises(ValueError, match="cannot all be satisfied"):
        raw_sample_from_record(item, registry())
    item = multi_record()
    item["input"]["current_search_state"]["hard_filters"].append(
        HardFilter("price", "gte", value=30, unit="USD").to_dict()
    )
    with pytest.raises(ValueError, match="cannot all be satisfied"):
        raw_sample_from_record(item, registry())


def test_allergen_soft_preference_rejected():
    item = record()
    item["expected"]["soft_preferences"] = [
        SoftPreference("allergen", "avoid", values=("peanut",)).to_dict()
    ]
    with pytest.raises(ValueError):
        raw_sample_from_record(item, registry())


def test_unmapped_terms_must_quote_user_input():
    item = record()
    item["scenario"] = "unmapped"
    item["expected"]["unmapped_terms"] = ["高级一点"]
    with pytest.raises(ValueError, match="absent from user_input"):
        raw_sample_from_record(item, registry())
    item["input"]["user_input"] += "，高级一点"
    validate_raw_sample(raw_sample_from_record(item, registry()), registry())


def test_units_preserved_without_conversion():
    item = record()
    item["scenario"] = "numeric_size"
    item["expected"] = SearchPatch(
        soft_preferences=(SoftPreference("size", "around", value=8, unit="oz"),)
    ).to_dict()
    item["assertions"] = []
    sample = raw_sample_from_record(item, registry())
    validate_raw_sample(sample, registry())
    assert sample.expected["soft_preferences"][0]["value"] == 8
    assert sample.expected["soft_preferences"][0]["unit"] == "oz"
