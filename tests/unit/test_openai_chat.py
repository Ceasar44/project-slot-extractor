import json

import httpx
import pytest
from search_dataset_helpers import registry
from test_generator import scenario_record

from slot_extractor.data.generator import GenerationRequest, RawGenerator
from slot_extractor.inference.base import GenerationParams
from slot_extractor.inference.factory import build_backend_from_config
from slot_extractor.inference.openai_chat import OpenAIChatBackend, OpenAIChatConfig


def test_factory_builds_chat_backend_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_CHAT_URL", "https://example.test/v1")
    monkeypatch.setenv("TEST_CHAT_KEY", "key")
    path = tmp_path / "chat.yaml"
    path.write_text(
        "backend: openai_chat\nmodel: test\n"
        "base_url_env: TEST_CHAT_URL\napi_key_env: TEST_CHAT_KEY\n"
    )
    assert isinstance(build_backend_from_config(path), OpenAIChatBackend)


def test_generation_uses_chat_without_response_format_and_retries_bad_json(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        content = (
            "invalid JSON" if len(calls) == 1 else json.dumps(scenario_record("single_filter"))
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 30},
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIChatBackend(OpenAIChatConfig("test", "https://example.test/v1/", "key"))
    sample = RawGenerator(backend, registry()).generate_one(GenerationRequest("single_filter", 3))
    assert sample.input["user_input"] == "这次只要开心果味的。"
    assert len(calls) == 2
    for url, kwargs in calls:
        assert url == "https://example.test/v1/chat/completions"
        assert "response_format" not in kwargs["json"]
        assert "text" not in kwargs["json"]
        assert "input" not in kwargs["json"]
        assert kwargs["json"]["max_tokens"] == 4096
    assert "校验失败" in calls[1][1]["json"]["messages"][-1]["content"]


@pytest.mark.parametrize("status", [200, 403])
def test_api_errors_include_reason_and_do_not_retry_or_expose_key(monkeypatch, status):
    calls = []

    def post(url, **kwargs):
        calls.append(1)
        return httpx.Response(
            status,
            request=httpx.Request("POST", url),
            json={
                "error": {"message": "provider denied secret-key"},
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIChatBackend(OpenAIChatConfig("test", "https://example.test", "secret-key"))
    with pytest.raises((ValueError, httpx.HTTPStatusError)) as caught:
        backend.generate([{"role": "user", "content": "test"}])
    assert "provider denied" in str(caught.value)
    assert "secret-key" not in str(caught.value)
    assert len(calls) == 1


def test_empty_content_retries_and_records_token_usage(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs["json"])
        text = "" if len(calls) == 1 else "{}"
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [{"message": {"content": text}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 30},
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIChatBackend(OpenAIChatConfig("test", "https://example.test", "key"))
    result = backend.generate(
        [], GenerationParams(max_tokens=999, response_schema={"type": "object"})
    )
    assert result.text == "{}"
    assert result.input_tokens == 100
    assert result.output_tokens == 30
    assert calls[0]["max_tokens"] == 999
    assert "response_format" not in calls[0]


def test_length_exhaustion_increases_budget_and_disables_reasoning(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs["json"])
        truncated = len(calls) < 3
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [
                    {
                        "message": {"content": "" if truncated else "{}"},
                        "finish_reason": "length" if truncated else "stop",
                    }
                ],
                "usage": {"completion_tokens": kwargs["json"]["max_tokens"]},
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIChatBackend(
        OpenAIChatConfig(
            "test",
            "https://example.test",
            "key",
            reasoning={"enabled": False},
        )
    )
    assert backend.generate([]).text == "{}"
    assert [call["max_tokens"] for call in calls] == [4096, 8192, 16384]
    assert all(call["reasoning"] == {"enabled": False} for call in calls)


def test_length_retry_cap_rejects_partial_output(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs["json"]["max_tokens"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [{"message": {"content": '{"unfinished":'}, "finish_reason": "length"}],
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIChatBackend(
        OpenAIChatConfig(
            "test",
            "https://example.test",
            "key",
            max_retry_tokens=8192,
        )
    )
    with pytest.raises(ValueError, match="output truncated.*max_tokens=8192"):
        backend.generate([])
    assert calls == [4096, 8192]


def test_factory_passes_reasoning_settings(tmp_path):
    path = tmp_path / "chat.yaml"
    path.write_text(
        "backend: openai_chat\nmodel: test\nbase_url: https://example.test\napi_key: key\n"
        "reasoning:\n  enabled: false\nmax_retry_tokens: 8192\n"
    )
    backend = build_backend_from_config(path)
    assert backend._reasoning == {"enabled": False}
    assert backend._max_retry_tokens == 8192


def test_deepseek_thinking_disabled_is_sent_on_each_retry(tmp_path, monkeypatch):
    path = tmp_path / "deepseek.yaml"
    path.write_text(
        "backend: openai_chat\nmodel: deepseek-v4-flash\n"
        "base_url: https://example.test/v1\napi_key: key\n"
        "thinking:\n  type: disabled\n",
        encoding="utf-8",
    )
    backend = build_backend_from_config(path)
    calls = []

    def post(url, **kwargs):
        calls.append(kwargs["json"])
        truncated = len(calls) == 1
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [
                    {
                        "message": {"content": "" if truncated else "{}"},
                        "finish_reason": "length" if truncated else "stop",
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", post)
    assert backend.generate([]).text == "{}"
    assert len(calls) == 2
    assert all(call["thinking"] == {"type": "disabled"} for call in calls)
    assert all("reasoning" not in call for call in calls)


@pytest.mark.parametrize("thinking", [{"enabled": False}, {"type": "invalid"}, False])
def test_invalid_thinking_settings_are_rejected(thinking):
    with pytest.raises(ValueError, match="thinking must contain"):
        OpenAIChatBackend(
            OpenAIChatConfig("test", "https://example.test", "key", thinking=thinking)
        )


def test_conflicting_reasoning_and_thinking_settings_are_rejected():
    with pytest.raises(ValueError, match="either thinking or reasoning"):
        OpenAIChatBackend(
            OpenAIChatConfig(
                "test",
                "https://example.test",
                "key",
                reasoning={"enabled": False},
                thinking={"type": "disabled"},
            )
        )


@pytest.mark.parametrize("status", [502, 503, 504])
def test_transient_gateway_errors_retry_without_changing_request(monkeypatch, status):
    calls = []
    delays = []

    def post(url, **kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(
            status if len(calls) < 3 else 200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]},
        )

    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr("slot_extractor.inference.openai_chat.time.sleep", delays.append)
    backend = OpenAIChatBackend(
        OpenAIChatConfig(
            "test",
            "https://example.test",
            "key",
            thinking={"type": "disabled"},
        )
    )
    assert backend.generate([]).text == "{}"
    assert len(calls) == 3
    assert delays == [1, 2]
    assert calls[0] == calls[1] == calls[2]
    assert calls[-1]["thinking"] == {"type": "disabled"}


def test_gateway_retry_exhaustion_preserves_error_and_redacts_key(monkeypatch):
    calls = []
    delays = []

    def post(url, **kwargs):
        calls.append(1)
        return httpx.Response(
            502,
            request=httpx.Request("POST", url),
            json={"error": {"message": "upstream failure secret-key"}},
        )

    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr("slot_extractor.inference.openai_chat.time.sleep", delays.append)
    backend = OpenAIChatBackend(OpenAIChatConfig("test", "https://example.test", "secret-key"))
    with pytest.raises(httpx.HTTPStatusError) as caught:
        backend.generate([])
    assert caught.value.response.status_code == 502
    assert "upstream failure" in str(caught.value)
    assert "secret-key" not in str(caught.value)
    assert len(calls) == 3
    assert delays == [1, 2]
