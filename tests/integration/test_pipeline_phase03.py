"""Offline SearchPatch raw-to-SFT CLI smoke with an independent frozen eval fixture."""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from slot_extractor.schemas.search_patch import HardFilter, SearchPatch
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl


def test_search_raw_to_sft_cli(tmp_path):
    records = [
        {
            "id": f"train-{i:06d}",
            "scenario": "single_filter",
            "tags": ["single_turn", "flavor"],
            "input": {"current_search_state": None, "user_input": f"开心果味的，需求{i}"},
            "expected": SearchPatch(
                hard_filters=(HardFilter("flavor", "in", values=("pistachio",)),)
            ).to_dict(),
            "assertions": [{"type": "field_exact", "field": "flavor"}],
        }
        for i in range(1, 11)
    ]
    evaluation = json.loads(json.dumps(records[0]))
    evaluation["id"] = "eval-000001"
    evaluation["input"]["user_input"] = "只要 pistachio 风味"
    write_jsonl(tmp_path / "raw.jsonl", records)
    write_jsonl(tmp_path / "eval.jsonl", [evaluation])
    config = {
        "version": "baking-v1.0",
        "registry_path": "configs/catalog/registry.yaml",
        "seed": 42,
        "eval_path": str(tmp_path / "eval.jsonl"),
        "output_root": str(tmp_path / "out"),
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(config))
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path.cwd() / "src"), str(Path.cwd()), env.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.data.build_dataset",
            "--config",
            str(tmp_path / "config.yaml"),
            "--raw-input",
            str(tmp_path / "raw.jsonl"),
        ],
        text=True,
        capture_output=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert "raw=10, sft_train=9, sft_val=1" in completed.stdout
    rows = list(read_jsonl(tmp_path / "out/processed/sft/baking-v1.0/train.jsonl"))
    assert all(set(r) == {"system", "conversations"} for r in rows)
    assert not (tmp_path / "out/processed/dpo").exists()
