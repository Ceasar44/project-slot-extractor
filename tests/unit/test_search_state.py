import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from slot_extractor.registry import load_registry
from slot_extractor.schemas.output import OutputValidationError
from slot_extractor.schemas.search_patch import SearchPatch
from slot_extractor.schemas.search_state import (
    STATE_FIELDS,
    SearchState,
    empty_search_state,
    validate_search_state,
)


@pytest.fixture
def registry():
    return load_registry(Path(__file__).resolve().parents[2] / "configs/catalog/registry.yaml")


def state():
    return empty_search_state().to_dict()


def test_empty_state_and_roundtrip(registry):
    empty = empty_search_state()
    assert empty == SearchState()
    assert set(empty.to_dict()) == STATE_FIELDS
    assert SearchState.from_dict(json.loads(json.dumps(empty.to_dict())), registry) == empty
    with pytest.raises(FrozenInstanceError):
        empty.query_text = "changed"


@pytest.mark.parametrize("key", ["reset", "clear_fields", "unmapped_terms", "schema_version"])
def test_patch_only_fields_never_persist(registry, key):
    with pytest.raises(OutputValidationError, match="schema fields"):
        validate_search_state({**state(), key: SearchPatch().to_dict()[key]}, registry)


@pytest.mark.parametrize("key", sorted(STATE_FIELDS))
def test_missing_state_fields(registry, key):
    data = state()
    del data[key]
    with pytest.raises(OutputValidationError):
        validate_search_state(data, registry)


@pytest.mark.parametrize("data", [None, [], "{}", 1])
def test_invalid_state_type(registry, data):
    with pytest.raises(OutputValidationError):
        validate_search_state(data, registry)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("query_text", ""),
        ("query_text", "x" * 129),
        ("hard_filters", None),
        ("hard_filters", [{}]),
        ("soft_preferences", {}),
        ("soft_preferences", [None]),
        ("sort", {"field": "newest", "order": "asc"}),
    ],
)
def test_state_reuses_strict_validators(registry, key, value):
    with pytest.raises(OutputValidationError):
        validate_search_state({**state(), key: value}, registry)


def test_populated_state_roundtrip_and_detachment(registry):
    data = state()
    data["query_text"] = "Dubai Chocolate"
    data["hard_filters"] = [
        {
            "field": "flavor",
            "op": "in",
            "value": None,
            "values": ["pistachio"],
            "min_value": None,
            "max_value": None,
            "unit": None,
        }
    ]
    data["soft_preferences"] = [
        {
            "field": "size",
            "preference": "around",
            "value": 8,
            "values": [],
            "min_value": None,
            "max_value": None,
            "unit": "oz",
        }
    ]
    data["sort"] = {"field": "rating", "order": "desc"}
    parsed = validate_search_state(data, registry)
    assert parsed.to_dict() == data
    data["hard_filters"][0]["values"].clear()
    parsed.to_dict()["hard_filters"].clear()
    assert parsed.hard_filters[0].values == ("pistachio",)
    assert parsed.soft_preferences[0].unit == "oz"
    assert state() == empty_search_state().to_dict()
