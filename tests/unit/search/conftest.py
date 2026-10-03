from pathlib import Path

import pytest

from slot_extractor.registry import load_registry


@pytest.fixture
def registry():
    return load_registry(Path(__file__).resolve().parents[3] / "configs/catalog/registry.yaml")
