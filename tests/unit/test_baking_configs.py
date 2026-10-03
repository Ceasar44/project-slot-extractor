import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from search_dataset_helpers import record, registry

from scripts.eval.run_eval import main as eval_main
from scripts.quantize import build_phase05_real as gguf
from scripts.train.check_search_data import check_rows
from scripts.train.render_config import load_yaml, render_run
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.sft_render import render_sft
from slot_extractor.evaluation.config import check_thresholds, load_evaluation_config
from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.inference import llama_server_manager as server_module
from slot_extractor.inference.factory import build_backend_from_config
from slot_extractor.inference.llama_server_manager import LlamaServerManager
from slot_extractor.quantization.registry import ModelRegistry
from slot_extractor.schemas.results import GenerationResult

QUANTIZATION = Path("configs/quantization/baking_search_v1.yaml")
EVALUATION = Path("configs/evaluation/baking_search_v1.yaml")


@pytest.mark.parametrize("size", ["0.6", "1.7"])
def test_training_inference_quantization_identity_and_paths(size, tmp_path):
    run_id = f"baking-qwen3-{size}b"
    config = load_yaml(render_run(run_id, output_root=tmp_path))
    assert config["dataset"] == "baking_v1_0_train"
    assert config["eval_dataset"] == "baking_v1_0_val"
    assert config["dataset_dir"] == "data/processed/baking-v1.0"
    assert config["enable_thinking"] is False and config["cutoff_len"] == 8192
    backend = build_backend_from_config(f"configs/inference/{run_id}.yaml")
    models = ModelRegistry.from_config(QUANTIZATION)
    model = models.get(backend.model)
    assert model.adapter_path == Path(config["output_dir"])
    assert model.adapter_run_id == run_id
    assert model.base_model == config["model_name_or_path"]
    assert model.server_args[-2:] == ("--alias", backend.model)
    assert config["cutoff_len"] + backend._default_params.max_tokens <= int(model.server_args[1])
    anchors = [a for a in models.anchors() if a.adapter_run_id == run_id]
    assert len(anchors) == 1 and anchors[0].adapter_path == model.adapter_path
    assert "phase04" not in str(model.artifact_path)


def test_search_matrix_and_frozen_eval_are_independent_of_appointment():
    models = ModelRegistry.from_config(QUANTIZATION)
    assert len(models.quantization_targets()) == 2 and len(models.anchors()) == 2
    evaluation = load_evaluation_config(EVALUATION)
    assert evaluation["cases"] == "data/eval/baking-v1.0/test.jsonl"
    assert len(evaluation["backends"]) == 2
    assert evaluation["thresholds"]["allergen_semantics"] == 1


@pytest.mark.parametrize(
    "metric,value",
    [("schema_valid", float("nan")), ("schema_valid", True), ("schema_valid", 1.1), ("typo", 0.9)],
)
def test_invalid_acceptance_configuration_fails(metric, value, tmp_path):
    config = load_evaluation_config(EVALUATION)
    config["thresholds"] = {metric: value}
    path = tmp_path / "eval.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="threshold"):
        load_evaluation_config(path)


class Backend:
    model = "test-search"

    def __init__(self, output):
        self.output = output

    def generate(self, messages, params=None):
        return GenerationResult(json.dumps(self.output), self.model, 1, 1, 1)


def test_unknown_gates_do_not_depend_on_gold_assertions():
    item = record()
    item["assertions"] = []
    sample = raw_sample_from_record(item, registry())
    output = deepcopy(item["expected"])
    output["soft_preferences"][0]["values"] = ["invented_flavor"]
    card = run_evaluation([sample], Backend(output), registry())
    result = check_thresholds(card, [sample], registry(), {"no_unknown_value": 1})
    assert not result["passed"] and result["checks"]["no_unknown_value"]["score"] == 0


def test_inapplicable_safety_gate_cannot_pass():
    item = record()
    sample = raw_sample_from_record(item, registry())
    card = run_evaluation([sample], Backend(item["expected"]), registry())
    # A gate on negation requires a dataset with applicable negation cases.
    result = check_thresholds(card, [sample], registry(), {"negation": 1})
    assert not result["passed"] and result["checks"]["negation"]["applicable"] == 0


@pytest.mark.parametrize("invalid,exit_code", [(False, 0), (True, 2)])
def test_evaluation_config_cli_writes_gates_and_exit_status(tmp_path, invalid, exit_code):
    item = record()
    item["id"] = "eval-000001"
    cases = tmp_path / "cases.jsonl"
    cases.write_text(json.dumps(item) + "\n", encoding="utf-8")
    backend = tmp_path / "mock.yaml"
    backend.write_text(
        yaml.safe_dump(
            {
                "backend": "mock",
                "model": "baking-test",
                "responses": {
                    item["input"]["user_input"]: {
                        "text": "invalid" if invalid else json.dumps(item["expected"]),
                        "prefill_ms": 1,
                        "first_token_ms": 1,
                        "total_ms": 2,
                        "output_tokens": 10,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    config = load_evaluation_config(EVALUATION)
    config.update(
        cases=str(cases), backends={"test": str(backend)}, report_dir=str(tmp_path / "reports")
    )
    path = tmp_path / "eval.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    assert eval_main(["--config", str(path), "--model", "test"]) == exit_code
    report = json.loads((tmp_path / "reports/scorecard-baking-test.json").read_text())
    assert report["acceptance"]["passed"] == (not invalid)
    assert report["evaluation_config"]["backend_sha256"]
    assert eval_main(["--config", str(path), "--model", "test", "--cases", str(cases)]) == 1


class Tokenizer:
    def __init__(self, full=100, prompt=70, gold=30):
        self.full, self.prompt, self.gold = full, prompt, gold

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs["enable_thinking"] is False
        return [0] * (self.full if len(messages) == 3 else self.prompt)

    def encode(self, text, **kwargs):
        return [0] * self.gold


@pytest.mark.parametrize("full,prompt,gold", [(101, 70, 30), (100, 111, 30), (100, 70, 70)])
def test_token_preflight_rejects_truncation_and_generation_overflow(tmp_path, full, prompt, gold):
    path = tmp_path / "train.jsonl"
    path.write_text(
        json.dumps(render_sft(raw_sample_from_record(record(), registry()), registry())),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exceeds token budget"):
        check_rows(path, Tokenizer(full, prompt, gold), registry(), 132, 100, 210)


def test_token_preflight_accepts_boundary_and_counts_all_rows(tmp_path):
    path = tmp_path / "train.jsonl"
    row = render_sft(raw_sample_from_record(record(), registry()), registry())
    path.write_text((json.dumps(row) + "\n") * 2, encoding="utf-8")
    assert check_rows(path, Tokenizer(), registry(), 132, 100, 210)["rows"] == 2


def test_real_quantization_dry_run_does_not_import_training_stack(capsys):
    assert gguf.main(["--config", str(QUANTIZATION), "--dry-run"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert Path(result["calibration"]) == Path("data/calibration/baking-search-v1.txt")
    assert all("baking-search" in path for path in result["adapters"])


def test_real_quantization_commands_use_selected_calibration_and_context(tmp_path, monkeypatch):
    commands = []
    monkeypatch.setattr(gguf, "run", lambda command, log: commands.append(command))
    tools = gguf.Tools(Path("convert.py"), Path("imatrix.exe"), Path("quantize.exe"))
    gguf.build_imatrix(
        Path("model.gguf"),
        tmp_path / "imatrix.dat",
        tools,
        tmp_path / "log",
        Path("baking-calibration.txt"),
        4,
        8192,
    )
    assert commands[0][commands[0].index("-f") + 1] == "baking-calibration.txt"
    assert commands[0][commands[0].index("-c") + 1] == "8192"
    gguf.quantize(
        Path("model.gguf"), Path("imatrix.dat"), tmp_path / "out.gguf", tools, tmp_path / "log", 4
    )
    assert commands[1][-2:] == ["Q4_K_M", "4"]


def test_search_server_alias_is_checked_during_readiness(tmp_path, monkeypatch):
    models = ModelRegistry.from_config(QUANTIZATION)
    spec = models.quantization_targets()[0]
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(
        server_module, "read_and_verify_manifest", lambda p: Mock(status="complete")
    )
    monkeypatch.setattr(server_module.subprocess, "Popen", lambda *a, **kw: process)
    response = Mock()
    response.status = 200
    response.read.return_value = json.dumps({"data": [{"id": spec.model_id}]}).encode()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=None)
    monkeypatch.setattr(server_module, "urlopen", lambda *a, **kw: response)
    manager = LlamaServerManager(models, Path("server.exe"))
    manager.start(spec.model_id, tmp_path / "server.log")
    manager.wait_ready(process, 0)
    manager.stop(process)


def test_real_search_build_routes_adapter_and_writes_source_hashes(tmp_path, monkeypatch):
    payload = load_yaml(QUANTIZATION)
    original = ModelRegistry.from_config(QUANTIZATION)
    target, anchor = original.quantization_targets()[0], original.anchors()[0]
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    for name in ("adapter_config.json", "adapter_model.safetensors"):
        (adapter / name).write_text("test", encoding="utf-8")
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
    models = ModelRegistry((target, anchor), "baking_search")
    monkeypatch.setattr(gguf.ModelRegistry, "from_config", lambda p: models)
    calibration = tmp_path / "calibration.txt"
    calibration.write_text("training only", encoding="utf-8")
    payload["calibration_data"], payload["work_root"] = str(calibration), str(tmp_path / "work")
    for key in ("convert_f16", "imatrix", "quantize"):
        tool = tmp_path / key
        tool.write_text("tool", encoding="utf-8")
        payload["toolchain"][key] = str(tool)
    config = tmp_path / "quantization.yaml"
    config.write_text(yaml.safe_dump(payload), encoding="utf-8")
    monkeypatch.setattr(gguf, "cached_base", lambda s: tmp_path / "base")
    seen = {}
    monkeypatch.setattr(
        gguf, "merge_adapter", lambda s, b, d: seen.update(adapter=s.adapter_path) or b
    )
    monkeypatch.setattr(gguf, "convert", lambda s, o, t, log: o.write_bytes(b"f16"))
    monkeypatch.setattr(
        gguf,
        "build_imatrix",
        lambda f, o, t, log, c, th, ctx: seen.update(calibration=c, context=ctx),
    )
    monkeypatch.setattr(gguf, "quantize", lambda f, i, o, t, log, th: o.write_bytes(b"q4"))
    monkeypatch.setattr(gguf.subprocess, "check_output", lambda *a, **kw: "revision")
    assert gguf.main(["--config", str(config)]) == 0
    assert seen == {"adapter": adapter, "calibration": calibration, "context": 8192}
    manifest = json.loads(target.manifest_path.read_text(encoding="utf-8"))
    assert dict(manifest["lineage"]["source_sha256"]).keys() == {
        "calibration",
        "adapter_config.json",
        "adapter_model.safetensors",
    }
    assert anchor.manifest_path.exists()
    with pytest.raises(FileExistsError, match="outputs already exist"):
        gguf.main(["--config", str(config)])
