"""Regression checks for reviewed migration entry points and model provenance."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from search_dataset_helpers import record

from scripts.eval.validate_dataset import build_parser, main
from scripts.quantize import build_phase05_real, build_search
from slot_extractor.quantization.registry import ModelRegistry
from slot_extractor.utils.jsonl import write_jsonl


def test_default_validator_uses_search_contract():
    args = build_parser().parse_args([])
    assert args.cases == "data/eval/baking-v1.0/test.jsonl"
    assert args.contract == "configs/catalog/registry.yaml"


def test_search_validator_accepts_reviewable_records(tmp_path, capsys):
    path = tmp_path / "cases.jsonl"
    write_jsonl(path, [record()])
    assert main(["--cases", str(path)]) == 0
    assert "1 search cases" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["empty", "invalid", "missing", "appointment"])
def test_validator_returns_failure_for_unusable_datasets(tmp_path, kind, capsys):
    path = tmp_path / "cases.jsonl"
    if kind == "empty":
        path.write_text("", encoding="utf-8")
    elif kind == "invalid":
        path.write_text("{broken", encoding="utf-8")
    elif kind == "appointment":
        path = Path("tests/fixtures/phase01_eval.jsonl")
    assert main(["--cases", str(path)]) == 1
    assert capsys.readouterr().err


def test_cached_base_preserves_requested_revision_and_never_falls_back(monkeypatch):
    spec = ModelRegistry.from_config(Path("configs/quantization/baking_search_v1.yaml")).models[0]
    download = Mock(return_value="exact-snapshot")
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(snapshot_download=download))
    assert build_phase05_real.cached_base(spec) == Path("exact-snapshot")
    download.assert_called_once_with(
        spec.base_model, revision=spec.base_revision, local_files_only=True
    )
    download.side_effect = OSError("requested revision not cached")
    with pytest.raises(RuntimeError, match="cannot resolve cached base"):
        build_phase05_real.cached_base(spec)


def test_search_quantization_entry_defaults_to_baking_and_allows_explicit_config(monkeypatch):
    builder = Mock(return_value=0)
    monkeypatch.setattr(build_search, "build_real", builder)
    assert build_search.main(["--dry-run"]) == 0
    builder.assert_called_with(
        ["--config", "configs/quantization/baking_search_v1.yaml", "--dry-run"]
    )
    build_search.main(["--config=custom.yaml", "--dry-run"])
    builder.assert_called_with(["--config=custom.yaml", "--dry-run"])
