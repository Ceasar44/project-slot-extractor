from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from slot_extractor.inference.base import GenerationParams
from slot_extractor.schemas.results import GenerationResult


class EmptyResponseError(ValueError):
    """A response has no usable assistant text and may be retried."""


@dataclass(frozen=True)
class OpenAIResponsesConfig:
    model: str
    base_url: str
    api_key: str
    timeout_s: float = 180.0
    temperature: float | None = None
    max_tokens: int = 512


def _responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "assistant" and isinstance(message.get("tool_calls"), list):
            if isinstance(content, str) and content:
                items.append({"role": "assistant", "content": content})
            for tool_call in message["tool_calls"]:
                function = tool_call.get("function", {})
                items.append(
                    {
                        "type": "function_call",
                        "call_id": tool_call.get("id"),
                        "name": function.get("name"),
                        "arguments": function.get("arguments", "{}"),
                    }
                )
            continue
        if role == "tool":
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": message.get("tool_call_id"),
                    "output": content,
                }
            )
            continue
        if role in {"system", "user", "assistant"} and isinstance(content, str):
            items.append({"role": role, "content": content})
    return items


def _response_text(payload: dict[str, Any]) -> str:
    if payload.get("status") == "failed" or payload.get("error"):
        error = json.dumps(payload.get("error"), ensure_ascii=False)
        raise ValueError(
            f"Responses API failed: status={payload.get('status')}, "
            f"id={payload.get('id')}, error={error[:4000]}"
        )
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    texts: list[str] = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise ValueError("Responses API returned a refusal")
            text = content.get("text")
            if content.get("type") == "output_text" and isinstance(text, str) and text.strip():
                texts.append(text)
    if not texts:
        raise EmptyResponseError(
            "Responses API payload contains no output text: "
            f"status={payload.get('status')}, "
            f"incomplete_details={payload.get('incomplete_details')}, "
            f"output_types={[item.get('type') for item in payload.get('output', [])]}, "
            f"usage={payload.get('usage')}"
        )
    return "".join(texts)


class OpenAIResponsesBackend:
    def __init__(self, config: OpenAIResponsesConfig) -> None:
        self.model = config.model
        self._base_url = config.base_url.rstrip("/")
        self._api_key = config.api_key
        self._timeout_s = config.timeout_s
        self._temperature = config.temperature
        self._default_params = GenerationParams(max_tokens=config.max_tokens)

    def generate(
        self, messages: list[dict[str, Any]], params: GenerationParams | None = None
    ) -> GenerationResult:
        generation_params = params or self._default_params
        request_payload: dict[str, Any] = {
            "model": self.model,
            "input": _responses_input(messages),
            "max_output_tokens": generation_params.max_tokens,
        }
        if self._temperature is not None:
            request_payload["temperature"] = self._temperature
        if generation_params.response_schema is not None:
            request_payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": generation_params.response_schema_name,
                    "strict": True,
                    "schema": generation_params.response_schema,
                }
            }

        started = time.perf_counter()
        response: httpx.Response | None = None
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{self._base_url}/responses",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=request_payload,
                    timeout=self._timeout_s,
                )
            except httpx.TransportError:
                if attempt == 2:
                    raise
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = response.text
                if self._api_key:
                    detail = detail.replace(self._api_key, "<redacted>")
                raise httpx.HTTPStatusError(
                    f"{exc}\nServer response: {detail[:4000]}",
                    request=exc.request,
                    response=exc.response,
                ) from exc
            payload = response.json()
            try:
                response_text = _response_text(payload)
            except EmptyResponseError:
                if attempt == 2 or payload.get("status") not in {"completed", "incomplete"}:
                    raise
                continue
            except ValueError as exc:
                detail = str(exc)
                if self._api_key:
                    detail = detail.replace(self._api_key, "<redacted>")
                raise ValueError(detail) from exc
            break
        if response is None:  # pragma: no cover - loop either returns or raises
            raise RuntimeError("Responses API request produced no response")
        total_ms = (time.perf_counter() - started) * 1000
        usage = payload.get("usage", {})
        output_tokens = usage.get("output_tokens")
        tokens_per_s = output_tokens * 1000 / total_ms if output_tokens else None
        return GenerationResult(
            text=response_text,
            model=self.model,
            prefill_ms=None,
            first_token_ms=None,
            total_ms=total_ms,
            output_tokens=output_tokens,
            tokens_per_s=tokens_per_s,
            raw=payload,
        )
