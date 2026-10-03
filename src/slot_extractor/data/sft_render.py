"""Render validated search gold as system + human + gpt, without tool metadata."""

import json

from slot_extractor.data.raw_sample import RawSample
from slot_extractor.data.raw_validator import validate_raw_sample
from slot_extractor.prompts.template import PromptBuilder
from slot_extractor.registry import Registry


class ShareGPTFormatError(ValueError):
    pass


def compact_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def messages_to_sharegpt(messages: list[dict]) -> list[dict[str, str]]:
    result = []
    for index, message in enumerate(messages):
        if set(message) != {"role", "content"} or not isinstance(message["content"], str):
            raise ShareGPTFormatError("messages require only role and text content")
        expected = "user" if index % 2 == 0 else "assistant"
        if message["role"] != expected:
            raise ShareGPTFormatError("search conversations must alternate user/assistant")
        result.append(
            {"from": "human" if expected == "user" else "gpt", "value": message["content"]}
        )
    return result


def render_sft(raw: RawSample, registry: Registry) -> dict:
    validate_raw_sample(raw, registry)
    system, user = PromptBuilder(registry).build_messages(raw)
    conversations = messages_to_sharegpt(
        [
            user,
            {"role": "assistant", "content": compact_json(raw.expected)},
        ]
    )
    return {"system": system["content"], "conversations": conversations}
