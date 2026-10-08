"""Chat Completions backend with JSON validated locally, without forced output format."""

import json
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx

from slot_extractor.inference.base import GenerationParams
from slot_extractor.schemas.results import GenerationResult


@dataclass(frozen=True)
class OpenAIChatConfig:
    model: str
    base_url: str
    api_key: str
    timeout_s: float = 180.0
    temperature: float | None = None
    max_tokens: int = 4096
    reasoning: dict[str, Any] | None = None
    max_retry_tokens: int = 16384
    thinking: dict[str, Any] | None = None


class OpenAIChatBackend:
    def __init__(self, config: OpenAIChatConfig) -> None:
        self.model = config.model
        self._base_url = config.base_url.rstrip("/")
        self._api_key = config.api_key
        self._timeout_s = config.timeout_s
        self._temperature = config.temperature
        self._reasoning = config.reasoning
        self._thinking = config.thinking
        if self._thinking is not None:
            if (
                not isinstance(self._thinking, dict)
                or set(self._thinking) != {"type"}
                or self._thinking["type"] not in ("enabled", "disabled")
            ):
                raise ValueError("thinking must contain type: enabled or disabled")
            if self._reasoning is not None:
                raise ValueError("configure either thinking or reasoning, not both")
        self._max_retry_tokens = config.max_retry_tokens
        if type(self._max_retry_tokens) is not int or self._max_retry_tokens < 1:
            raise ValueError("max_retry_tokens must be a positive integer")
        self._default_params = GenerationParams(max_tokens=config.max_tokens)

    def _redact(self, text: str) -> str:
        return text.replace(self._api_key, "<redacted>") if self._api_key else text

    def generate(
        self, messages: list[dict[str, Any]], params: GenerationParams | None = None
    ) -> GenerationResult:
        params = params or self._default_params
        body = {
            "model": self.model,
            "messages": [
                {k: v for k, v in message.items() if not k.startswith("_")} for message in messages
            ],
            "max_tokens": params.max_tokens,
        }
        # response_schema is intentionally not sent: the caller validates JSON locally.
        if self._temperature is not None:
            body["temperature"] = self._temperature
        if self._reasoning is not None:
            body["reasoning"] = dict(self._reasoning)
        if self._thinking is not None:
            body["thinking"] = dict(self._thinking)
        started = time.perf_counter()
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=body,
                    timeout=self._timeout_s,
                )
            except httpx.TransportError:
                if attempt == 2:
                    raise
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if response.status_code in {502, 503, 504} and attempt < 2:
                    delay_s = 2**attempt
                    print(
                        f"Chat API: HTTP {response.status_code}; retrying in {delay_s}s "
                        f"({attempt + 1}/2)",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(delay_s)
                    continue
                raise httpx.HTTPStatusError(
                    f"{exc}\nServer response: {self._redact(response.text)[:4000]}",
                    request=exc.request,
                    response=exc.response,
                ) from exc
            payload = response.json()
            if payload.get("error"):
                raise ValueError(
                    "Chat API failed: "
                    + self._redact(json.dumps(payload["error"], ensure_ascii=False))[:4000]
                )
            choices = payload.get("choices") or []
            choice = choices[0] if choices else {}
            message = choice.get("message") or {}
            if message.get("refusal") or choice.get("finish_reason") == "content_filter":
                raise ValueError("Chat API returned a refusal or content filter")
            text = message.get("content")
            if choice.get("finish_reason") == "length":
                budget = body["max_tokens"]
                if attempt < 2 and budget < self._max_retry_tokens:
                    # Copy rather than mutate the payload already sent on the previous attempt.
                    body = dict(body, max_tokens=min(budget * 2, self._max_retry_tokens))
                    print(
                        f"Chat API: output token limit {budget} exhausted; "
                        f"retrying with max_tokens={body['max_tokens']} "
                        f"({attempt + 1}/2)",
                        file=sys.stderr,
                        flush=True,
                    )
                    continue
                raise ValueError(
                    f"Chat API output truncated: finish_reason=length, "
                    f"max_tokens={budget}, usage={payload.get('usage')}"
                )
            if isinstance(text, str) and text.strip():
                break
            if attempt == 2:
                raise ValueError(
                    f"Chat API contains no output text after 3 attempts: "
                    f"finish_reason={choice.get('finish_reason')}, usage={payload.get('usage')}"
                )
        total_ms = (time.perf_counter() - started) * 1000
        usage = payload.get("usage") or {}
        output_tokens = usage.get("completion_tokens")
        return GenerationResult(
            text=text,
            model=self.model,
            total_ms=total_ms,
            prefill_ms=None,
            first_token_ms=None,
            output_tokens=output_tokens,
            input_tokens=usage.get("prompt_tokens"),
            tokens_per_s=output_tokens * 1000 / total_ms if output_tokens and total_ms else None,
            raw=payload,
        )
