import httpx
import pytest

from slot_extractor.inference.openai_responses import (
    EmptyResponseError,
    OpenAIResponsesBackend,
    OpenAIResponsesConfig,
    _response_text,
)


def test_http_error_includes_server_reason_without_api_key(monkeypatch):
    key = "private-test-key"
    response = httpx.Response(
        403,
        request=httpx.Request("POST", "https://example.test/responses"),
        json={"error": {"message": f"Model access denied for {key}"}},
    )
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)
    backend = OpenAIResponsesBackend(OpenAIResponsesConfig("test", "https://example.test", key))
    with pytest.raises(httpx.HTTPStatusError) as caught:
        backend.generate([{"role": "user", "content": "test"}])
    assert "Model access denied" in str(caught.value)
    assert key not in str(caught.value)
    assert caught.value.response.status_code == 403


def test_empty_completed_response_retries_then_uses_message_text(monkeypatch):
    payloads = iter([
        {"status": "completed", "output": [{"type": "reasoning"}]},
        {"status": "completed", "output_text": "", "output": [{
            "type": "message", "content": [{"type": "output_text", "text": "{}"}],
        }]},
    ])
    calls = []

    def post(*args, **kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(
            200, request=httpx.Request("POST", args[0]), json=next(payloads),
        )

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIResponsesBackend(OpenAIResponsesConfig("test", "https://example.test", "key"))
    assert backend.generate([{"role": "user", "content": "test"}]).text == "{}"
    assert len(calls) == 2
    assert calls[0] == calls[1]


def test_persistent_empty_response_has_bounded_retries_and_diagnostics(monkeypatch):
    calls = []

    def post(*args, **kwargs):
        calls.append(1)
        return httpx.Response(200, request=httpx.Request("POST", args[0]), json={
            "status": "completed", "output": [{"type": "reasoning"}],
            "usage": {"output_tokens": 4096},
        })

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIResponsesBackend(OpenAIResponsesConfig("test", "https://example.test", "key"))
    with pytest.raises(EmptyResponseError, match="output_types=.*reasoning.*4096"):
        backend.generate([{"role": "user", "content": "test"}])
    assert len(calls) == 3


def test_refusal_is_not_treated_as_retryable_empty_output():
    with pytest.raises(ValueError, match="refusal") as caught:
        _response_text({"output": [{"type": "message", "content": [{"type": "refusal"}]}]})
    assert not isinstance(caught.value, EmptyResponseError)


def test_failed_response_reports_provider_error_without_retry_or_key(monkeypatch):
    calls = []

    def post(*args, **kwargs):
        calls.append(1)
        return httpx.Response(200, request=httpx.Request("POST", args[0]), json={
            "id": "resp-test", "status": "failed", "output": [],
            "error": {"code": "provider_error", "message": "Access denied for private-test-key"},
        })

    monkeypatch.setattr(httpx, "post", post)
    backend = OpenAIResponsesBackend(
        OpenAIResponsesConfig("test", "https://example.test", "private-test-key")
    )
    with pytest.raises(ValueError) as caught:
        backend.generate([{"role": "user", "content": "test"}])
    detail = str(caught.value)
    assert "provider_error" in detail
    assert "Access denied" in detail
    assert "resp-test" in detail
    assert "private-test-key" not in detail
    assert len(calls) == 1
