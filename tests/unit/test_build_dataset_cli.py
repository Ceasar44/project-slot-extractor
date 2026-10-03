import hashlib
import json
from pathlib import Path

import pytest
import yaml
from search_dataset_helpers import REGISTRY_PATH
from test_dataset_build import evaluation, samples
from test_generator import SequenceBackend, scenario_record

from scripts.data import build_dataset as cli
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def setup_config(tmp_path):
    config = {
        "dataset_id": "baking-raw-v1.0",
        "version": "baking-v1.0",
        "output_root": str(tmp_path / "out"),
        "registry_path": str(REGISTRY_PATH),
        "eval_path": str(tmp_path / "eval.jsonl"),
        "counts": {"hard_soft_mix": 2},
        "seed": 42,
        "generation_concurrency": 1,
        "enable_dpo": False,
        "coverage_minimums": {},
        "generate_inference_config": "stub.yaml",
        "mock_inference_config": "stub.yaml",
    }
    write_jsonl(config["eval_path"], evaluation())
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    raw = tmp_path / "input.jsonl"
    write_jsonl(raw, [s.to_dict() for s in samples(2)])
    return path, raw, config


def test_raw_cli_end_to_end_does_not_contact_backend(tmp_path, monkeypatch):
    path, raw, config = setup_config(tmp_path)

    def unexpected_backend(*args):
        raise AssertionError("raw-input build must not load a backend")

    monkeypatch.setattr(cli, "build_backend_from_config", unexpected_backend)
    assert cli.run(cli._parser().parse_args(["--config", str(path), "--raw-input", str(raw)])) == 0
    manifest = json.loads(
        (Path(config["output_root"]) / "processed/baking-v1.0/manifest.json").read_text()
    )
    assert manifest["raw_count"] == 2
    assert (
        len(list(read_jsonl(Path(config["output_root"]) / "processed/sft/baking-v1.0/train.jsonl")))
        == 1
    )


@pytest.mark.parametrize("mode", ["--generate", "--mock"])
def test_generation_then_build_preserves_raw_lineage(tmp_path, monkeypatch, mode):
    path, _, config = setup_config(tmp_path)
    first, second = scenario_record("hard_soft_mix"), scenario_record("hard_soft_mix")
    second["input"]["user_input"] += "，用来做吐司"
    backend = SequenceBackend([first, second])
    monkeypatch.setattr(cli, "build_backend_from_config", lambda _: backend)
    assert cli.run(cli._parser().parse_args(["--config", str(path), mode, "--strict-audit"])) == 0
    root = Path(config["output_root"])
    source = json.loads((root / "raw/baking-v1.0/manifest.json").read_text())
    build = json.loads((root / "processed/baking-v1.0/manifest.json").read_text())
    assert build["source_raw_manifest"] == source
    assert (
        source["raw_sha256"]
        == hashlib.sha256((root / "raw/baking-v1.0/samples.jsonl").read_bytes()).hexdigest()
    )


def test_raw_source_hash_drift_is_rejected(tmp_path):
    path, raw, config = setup_config(tmp_path)
    raw.with_name("manifest.json").write_text(json.dumps({"registry_sha256": "wrong"}))
    with pytest.raises(ValueError, match="source raw manifest"):
        cli.run(cli._parser().parse_args(["--config", str(path), "--raw-input", str(raw)]))
    assert not (Path(config["output_root"]) / "processed").exists()


def test_cli_requires_mode_and_rejects_dpo_configuration(tmp_path):
    path, _, config = setup_config(tmp_path)
    with pytest.raises(ValueError, match="choose"):
        cli.run(cli._parser().parse_args(["--config", str(path)]))
    config["enable_dpo"] = True
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="Task 09"):
        cli._load_config(path)


def test_dry_run_config_uses_search_requests_without_outputs(tmp_path):
    path, _, config = setup_config(tmp_path)
    assert cli.run(cli._parser().parse_args(["--config", str(path), "--dry-run"])) == 0
    assert not Path(config["output_root"]).exists()


def test_invalid_build_target_rejected_before_generation(tmp_path, monkeypatch):
    path, _, config = setup_config(tmp_path)
    config["version"] = "../escape"
    path.write_text(yaml.safe_dump(config))

    def unexpected_backend(*args):
        raise AssertionError("invalid build must not load backend")

    monkeypatch.setattr(cli, "build_backend_from_config", unexpected_backend)
    with pytest.raises(ValueError, match="search version"):
        cli.run(cli._parser().parse_args(["--config", str(path), "--generate"]))


def test_generation_eval_hash_drift_rejected(tmp_path, monkeypatch):
    path, _, config = setup_config(tmp_path)
    first, second = scenario_record("hard_soft_mix"), scenario_record("hard_soft_mix")
    second["input"]["user_input"] += "，用来做吐司"
    from slot_extractor.data.search_generation import generate_raw_dataset

    source = generate_raw_dataset(config, SequenceBackend([first, second]), tmp_path / "generated")
    changed_eval = evaluation()
    changed_eval[0]["input"]["user_input"] += "，新评估版本"
    write_jsonl(config["eval_path"], changed_eval)
    with pytest.raises(ValueError, match="frozen evaluation"):
        cli.run(cli._parser().parse_args(["--config", str(path), "--raw-input", str(source)]))
    assert not (Path(config["output_root"]) / "processed").exists()
