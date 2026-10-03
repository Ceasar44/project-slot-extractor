from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference
from slot_extractor.schemas.search_state import SearchState

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "configs/catalog/registry.yaml"


def registry():
    return load_registry(REGISTRY_PATH)


def record():
    return {
        "id": "train-000001",
        "scenario": "hard_soft_mix",
        "tags": ["single_turn", "flavor", "price"],
        "input": {"current_search_state": None, "user_input": "20美元以内，最好开心果，不要太甜"},
        "expected": SearchPatch(
            hard_filters=(HardFilter("price", "lte", value=20, unit="USD"),),
            soft_preferences=(
                SoftPreference("flavor", "prefer", values=("pistachio",)),
                SoftPreference("sweetness_level", "lower"),
            ),
        ).to_dict(),
        "assertions": [
            {"type": "hard_soft_correct", "field": None},
            {"type": "minimal_patch", "field": None},
        ],
    }


def multi_record():
    item = record()
    item["scenario"] = "replace"
    item["tags"] = ["multi_turn", "flavor", "price", "allergen"]
    item["input"] = {
        "current_search_state": SearchState(
            hard_filters=(
                HardFilter("application", "in", values=("croissant_pastry",)),
                HardFilter("price", "lte", value=25, unit="USD"),
            ),
            soft_preferences=(SoftPreference("flavor", "prefer", values=("pistachio",)),),
        ).to_dict(),
        "user_input": "口味改成抹茶优先，预算提高到30美元，但不能含花生",
    }
    item["expected"] = SearchPatch(
        hard_filters=(
            HardFilter("price", "lte", value=30, unit="USD"),
            HardFilter("allergen", "not_in", values=("peanut",)),
        ),
        soft_preferences=(SoftPreference("flavor", "prefer", values=("matcha",)),),
    ).to_dict()
    item["assertions"] = [
        {"type": "field_replaced", "field": "flavor"},
        {"type": "field_replaced", "field": "price"},
        {"type": "field_preserved", "field": "application"},
        {"type": "field_exact", "field": "allergen"},
        {"type": "minimal_patch", "field": None},
    ]
    return item
