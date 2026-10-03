import json

import yaml

from scripts.eval.run_eval import main
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch
from slot_extractor.utils.jsonl import write_jsonl


def test_search_cli_uses_mock_by_user_text_without_leaking_sample_ids(tmp_path, capsys):
    patch = SearchPatch(hard_filters=(HardFilter("flavor", "in", values=("pistachio",)),)).to_dict()
    sample = {
        "id": "eval-000001",
        "scenario": "single_filter",
        "tags": ["flavor"],
        "input": {"current_search_state": None, "user_input": "想要开心果味"},
        "expected": patch,
        "assertions": [{"type": "field_exact", "field": "flavor"}],
    }
    cases = tmp_path / "cases.jsonl"
    write_jsonl(cases, [sample])
    config = tmp_path / "backend.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "backend": "mock",
                "model": "search-mock",
                "responses": {
                    sample["input"]["user_input"]: {
                        "text": json.dumps(patch),
                        "prefill_ms": 1,
                        "first_token_ms": 2,
                        "total_ms": 10,
                        "output_tokens": 100,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    assert (
        main(
            [
                "--backend-config",
                str(config),
                "--cases",
                str(cases),
                "--report-dir",
                str(tmp_path / "reports"),
            ]
        )
        == 0
    )
    text = capsys.readouterr().out
    assert "SearchPatch" in text and "Schema Valid: 100.0%" in text
    report = json.loads(
        (tmp_path / "reports/scorecard-search-mock.json").read_text(encoding="utf-8")
    )
    assert report["dataset"]["registry_sha256"]
    assert report["cases"][0]["assertions"][0]["passed"]


def test_appointment_dataset_is_rejected_by_new_cli(tmp_path):
    assert (
        main(
            [
                "--backend-config",
                "configs/inference/mock.yaml",
                "--cases",
                "tests/fixtures/phase01_eval.jsonl",
                "--report-dir",
                str(tmp_path),
            ]
        )
        == 1
    )
    assert not list(tmp_path.iterdir())
