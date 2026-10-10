import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from search_dataset_helpers import multi_record, record, registry

from scripts.quantize import build_phase05_real as real
from scripts.quantize.prepare_search_calibration import prepare, select_samples
from scripts.quantize.search_build import ImatrixOptions, stage
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.sft_render import render_sft
from slot_extractor.quantization.manifest import read_and_verify_manifest, sha256_file
from slot_extractor.quantization.registry import ModelRegistry
from slot_extractor.search_compare.app import create_app


def test_stage_reuses_verified_outputs_and_rebuilds_changed_inputs(tmp_path):
    output, record = tmp_path / "matrix.gguf", tmp_path / "stage.json"
    calls = []

    def action(path):
        calls.append(path)
        path.write_bytes(b"complete")

    stage("imatrix", output, record, {"input": "one"}, {}, action)
    stage("imatrix", output, record, {"input": "one"}, {}, action)
    assert len(calls) == 1
    stage("imatrix", output, record, {"input": "two"}, {}, action)
    assert len(calls) == 2
    output.write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="hash mismatch"):
        stage("imatrix", output, record, {"input": "two"}, {}, action)


def test_interrupted_imatrix_never_becomes_completed_output(tmp_path):
    output, record = tmp_path / "matrix.gguf", tmp_path / "stage.json"

    def interrupted(path):
        path.write_bytes(b"periodic checkpoint")
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError):
        stage("imatrix", output, record, {}, {}, interrupted)
    assert not output.exists() and not record.exists()
    stage("imatrix", output, record, {}, {}, lambda p: p.write_bytes(b"final"))
    assert output.read_bytes() == b"final"


def test_untracked_legacy_f16_is_not_automatically_trusted(tmp_path):
    output = tmp_path / "f16.gguf"
    output.write_bytes(b"legacy")
    with pytest.raises(FileExistsError, match="unverified"):
        stage("f16", output, tmp_path / "record.json", {}, {}, lambda p: None)


@pytest.mark.parametrize(
    "values",
    [
        {"max_chunks": 0},
        {"batch_size": True},
        {"enabled": "false"},
        {"no_ppl": 1},
    ],
)
def test_invalid_imatrix_options(values):
    with pytest.raises(ValueError):
        ImatrixOptions.from_payload({"imatrix": values})


def test_options_and_optional_matrix_commands(tmp_path, monkeypatch):
    commands = []
    monkeypatch.setattr(real, "run", lambda command, log: commands.append(command))
    tools = real.Tools(Path("convert.py"), Path("imatrix"), Path("quantize"))
    real.build_imatrix(
        Path("f16"),
        tmp_path / "matrix",
        tools,
        tmp_path / "log",
        max_chunks=50,
        no_ppl=True,
        batch_size=256,
    )
    assert commands[0][-3:] == ["--chunks", "50", "--no-ppl"]
    assert commands[0][commands[0].index("-b") + 1] == "256"
    assert "--parse-special" in commands[0]
    real.quantize(Path("f16"), None, tmp_path / "q4", tools, tmp_path / "log")
    assert "--imatrix" not in commands[1]


def test_stratified_selection_is_reproducible_and_covers_scenarios():
    records = [{"id": str(i), "scenario": str(i % 4)} for i in range(40)]
    selected = select_samples(records, 12, 42)
    assert selected == select_samples(list(reversed(records)), 12, 42)
    assert len({r["id"] for r in selected}) == 12
    assert {r["scenario"] for r in selected} == {"0", "1", "2", "3"}
    with pytest.raises(ValueError, match="every training scenario"):
        select_samples(records, 3, 42)


class FakeTokenizer:
    chat_template = "test"

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs["enable_thinking"] is False
        assert [m["role"] for m in messages] == ["system", "user", "assistant"]
        return json.dumps(messages, ensure_ascii=False)

    def encode(self, text, **kwargs):
        return list(range(len(text)))

    def get_vocab(self):
        return {"test": 0}


def test_calibration_train_membership_source_hashes_and_leakage(tmp_path):
    train_records = [record(), multi_record()]
    train_records[1]["id"] = "train-second"
    validation = record()
    validation["id"] = "validation"
    validation["input"]["user_input"] = "独立验证样本"
    evaluation = record()
    evaluation["id"] = "evaluation"
    evaluation["input"]["user_input"] = "独立评估样本"

    def write_rows(path, rows):
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), "utf-8")

    raw_path, train_path = tmp_path / "raw.jsonl", tmp_path / "train.jsonl"
    val_path, eval_path = tmp_path / "val.jsonl", tmp_path / "eval.jsonl"
    write_rows(raw_path, [*train_records, validation])
    write_rows(
        train_path,
        [render_sft(raw_sample_from_record(r, registry()), registry()) for r in train_records],
    )
    write_rows(val_path, [render_sft(raw_sample_from_record(validation, registry()), registry())])
    write_rows(eval_path, [evaluation])
    registry_path = Path("configs/catalog/registry.yaml")
    manifest = {
        "dataset_id": "fixture",
        "registry_sha256": sha256_file(registry_path),
        "eval_sha256": sha256_file(eval_path),
        "source_raw_path": str(raw_path),
        "train": {"ids": [r["id"] for r in train_records]},
        "val": {"ids": [validation["id"]]},
        "gold_review_required": True,
        "artifacts": {
            f"{name}_sha256": sha256_file(path)
            for name, path in (("raw", raw_path), ("train", train_path), ("val", val_path))
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    result = prepare(
        manifest_path,
        train_path,
        val_path,
        registry_path,
        FakeTokenizer(),
        tmp_path / "calibration.txt",
        maximum=2,
        evaluation_path=eval_path,
    )
    assert set(result["sample_ids"]) <= set(manifest["train"]["ids"])
    assert not set(result["sample_ids"]) & set(manifest["val"]["ids"])
    assert len(result["scenario_counts"]) == 2
    assert result["gold_review_required"] is True
    evaluation["input"] = train_records[0]["input"]
    write_rows(eval_path, [evaluation])
    manifest["eval_sha256"] = sha256_file(eval_path)
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(ValueError, match="overlaps eval"):
        prepare(
            manifest_path,
            train_path,
            val_path,
            registry_path,
            FakeTokenizer(),
            tmp_path / "leak.txt",
            maximum=2,
            evaluation_path=eval_path,
        )


def build_fixture(tmp_path, monkeypatch, enabled=True):
    config_path = Path("configs/quantization/baking_search_v1.yaml")
    payload = yaml.safe_load(config_path.read_text("utf-8"))
    registry = ModelRegistry.from_config(config_path)
    target, anchor = registry.quantization_targets()[0], registry.anchors()[0]
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    for name in ("adapter_config.json", "adapter_model.safetensors"):
        (adapter / name).write_bytes(b"adapter")
    base = tmp_path / "base"
    base.mkdir()
    (base / "config.json").write_text("{}")
    (base / "model.safetensors").write_bytes(b"weights")
    target = replace(
        target,
        adapter_path=adapter,
        artifact_path=tmp_path / "q4.gguf",
        manifest_path=tmp_path / "q4.json",
    )
    anchor = replace(
        anchor,
        adapter_path=adapter,
        artifact_path=tmp_path / "f16.gguf",
        manifest_path=tmp_path / "f16.json",
    )
    registry = ModelRegistry((target, anchor), "baking_search")
    monkeypatch.setattr(real.ModelRegistry, "from_config", lambda path: registry)
    monkeypatch.setattr(real, "cached_base", lambda spec: base)
    monkeypatch.setattr("importlib.metadata.version", lambda name: "test-version")
    payload["imatrix"] = {"enabled": enabled, "max_chunks": 50, "no_ppl": True}
    payload["work_root"] = str(tmp_path / "work")
    payload["project_revision"] = "archive-test"
    calibration = tmp_path / "calibration.txt"
    if enabled:
        calibration.write_text("training only")
    payload["calibration_data"] = str(calibration)
    for key in ("convert_f16", "imatrix", "quantize"):
        tool = tmp_path / key
        if enabled or key != "imatrix":
            tool.write_bytes(b"tool")
        payload["toolchain"][key] = str(tool)
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(payload))
    calls = []

    def merge(spec, source, destination):
        calls.append("merge")
        destination.mkdir()
        (destination / "weights").write_bytes(b"merged")
        return destination

    def convert(source, output, tools, log):
        calls.append("f16")
        output.write_bytes(b"f16")

    def imatrix(f16, output, tools, log, calibration, threads, context, **kwargs):
        # F16 can already be loaded in the comparison UI while calibration is running.
        read_and_verify_manifest(anchor.manifest_path)
        calls.append("imatrix")
        output.write_bytes(b"matrix")

    def quantize(f16, matrix, output, tools, log, threads):
        calls.append("q4")
        assert (matrix is not None) == enabled
        output.write_bytes(b"q4")

    monkeypatch.setattr(real, "merge_adapter", merge)
    monkeypatch.setattr(real, "convert", convert)
    monkeypatch.setattr(real, "build_imatrix", imatrix)
    monkeypatch.setattr(real, "quantize", quantize)
    return config, payload, calls, target, anchor


@pytest.mark.parametrize("enabled", [True, False])
def test_build_reuse_parameter_changes_and_ui_manifests(tmp_path, monkeypatch, enabled):
    config, payload, calls, target, anchor = build_fixture(tmp_path, monkeypatch, enabled)
    assert real.main(["--config", str(config)]) == 0
    expected = ["merge", "f16", "imatrix", "q4"] if enabled else ["merge", "f16", "q4"]
    assert calls == expected
    manifest = read_and_verify_manifest(target.manifest_path)
    assert manifest.parameters["imatrix"]["enabled"] is enabled
    assert ("calibration" in dict(manifest.lineage.source_sha256)) == enabled
    assert read_and_verify_manifest(anchor.manifest_path).is_anchor
    real.main(["--config", str(config)])
    assert calls == expected
    if enabled:
        payload["imatrix"]["max_chunks"] = 25
        config.write_text(yaml.safe_dump(payload))
        real.main(["--config", str(config)])
        assert calls == expected + ["imatrix", "q4"]


def test_failed_calibration_keeps_f16_available_and_reuses_upstream(tmp_path, monkeypatch):
    config, payload, calls, target, anchor = build_fixture(tmp_path, monkeypatch)
    successful = real.build_imatrix

    def interrupted(*args, **kwargs):
        args[1].write_bytes(b"checkpoint")
        raise RuntimeError("calibration stopped")

    monkeypatch.setattr(real, "build_imatrix", interrupted)
    with pytest.raises(RuntimeError, match="stopped"):
        real.main(["--config", str(config)])
    assert read_and_verify_manifest(anchor.manifest_path).status == "complete"
    assert not target.artifact_path.exists()
    monkeypatch.setattr(real, "build_imatrix", successful)
    real.main(["--config", str(config)])
    assert calls == ["merge", "f16", "imatrix", "q4"]


def test_two_variants_share_f16_and_are_available_to_compare_api(tmp_path, monkeypatch):
    config, payload, calls, target, anchor = build_fixture(tmp_path, monkeypatch, enabled=False)
    variant = replace(
        target,
        model_id=target.model_id + "-no-imatrix",
        artifact_path=tmp_path / "variant.gguf",
        manifest_path=tmp_path / "variant.json",
    )
    models = ModelRegistry((target, variant, anchor), "baking_search")
    monkeypatch.setattr(real.ModelRegistry, "from_config", lambda path: models)
    real.main(["--config", str(config), "--model-id", target.model_id])
    real.main(["--config", str(config), "--model-id", variant.model_id])
    assert calls == ["merge", "f16", "q4", "q4"]
    with TestClient(
        create_app(registry=models, quantization_config=config, log_path=tmp_path / "app.jsonl")
    ) as client:
        listed = client.get("/api/models").json()
        assert len(listed) == 3 and all(m["available"] for m in listed)


def test_variants_have_distinct_artifacts_and_defaults_exclude_experiments(capsys):
    registry = ModelRegistry.from_config(Path("configs/quantization/baking_search_v1.yaml"))
    assert len({s.artifact_path for s in registry.models}) == len(registry.models)
    real.main(["--config", "configs/quantization/baking_search_v1.yaml", "--dry-run"])
    assert len(json.loads(capsys.readouterr().out)["models"]) == 2
