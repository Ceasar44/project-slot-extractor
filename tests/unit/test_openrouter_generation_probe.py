import json
from types import SimpleNamespace

import httpx
from search_dataset_helpers import registry

from scripts.data.probe_openrouter_generation import MODES, probe_messages, request_body, run


def test_three_modes_use_same_original_prompt_and_schema():
    messages, schema = probe_messages(registry(), 3)
    assert "至少4个" not in messages[0]["content"]
    assert schema["$defs"]["input"]["properties"]["user_input"]["minLength"] == 1
    bodies = {mode: request_body(mode, "test", messages, schema, "provider-test") for mode in MODES}
    assert bodies["chat_plain"][0] == "/chat/completions"
    assert "response_format" not in bodies["chat_plain"][1]
    assert bodies["responses_schema"][0] == "/responses"
    assert bodies["responses_schema"][1]["input"] == bodies["chat_plain"][1]["messages"]
    assert bodies["chat_schema"][1]["response_format"]["json_schema"]["schema"] == schema
    for _, body in bodies.values():
        assert body["provider"] == {"only": ["provider-test"], "allow_fallbacks": False}


def test_probe_saves_raw_responses_and_handles_api_failure_without_stopping(tmp_path, monkeypatch):
    cfg = tmp_path / "backend.yaml"
    cfg.write_text("model: test\nbase_url: https://example.test/v1\napi_key: private-key\n")
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        if len(calls) == 3:
            payload = {"status": "failed", "error": {"message": "denied private-key"}}
        else:
            text = "想要开心果味" if len(calls) == 1 else "想"
            payload = {"choices": [{"message": {"content": json.dumps({
                "input": {"user_input": text},
            })}, "finish_reason": "stop"}]}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", post)
    args = SimpleNamespace(config=str(cfg), model=None, provider=None, repeats=1, index=3,
                           output_root=str(tmp_path / "probes"), timeout=30)
    assert run(args) == 0
    assert len(calls) == 3
    summary_path = next((tmp_path / "probes").glob("*/summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert [row.get("characters") for row in summary] == [6, 1, None]
    assert "denied" in summary[2]["error"]["message"]
    assert "private-key" not in summary_path.read_text(encoding="utf-8")
    assert len(list(summary_path.parent.glob("*.response.txt"))) == 3
