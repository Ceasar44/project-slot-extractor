"""Build two-message SearchPatch prompts from explicit search inputs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol

from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import validate_text
from slot_extractor.schemas.search_state import SearchState, validate_search_state

from .rules import SYSTEM_RULES, render_registry_summary, render_search_patch_shape

Message = dict[str, str]


class SearchSample(Protocol):
    input: dict[str, Any]


class PromptBuilder:
    """Only current_search_state and user_input enter the model context."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self._system_prefix = (
            f"{SYSTEM_RULES}\n"
            f"SearchPatch 固定输出形状：{render_search_patch_shape()}\n"
            f"Registry 字段合同：{render_registry_summary(registry)}\n"
        )

    def build_messages(self, sample: Mapping[str, Any] | SearchSample) -> list[Message]:
        if isinstance(sample, Mapping):
            input_obj = sample["input"] if "input" in sample else sample
        else:
            input_obj = getattr(sample, "input", None)
        if not isinstance(input_obj, Mapping):
            raise ValueError("search input must be an object")
        if "current_search_state" not in input_obj or "user_input" not in input_obj:
            raise ValueError("search input requires current_search_state and user_input")
        user_input = input_obj["user_input"]
        validate_text(user_input, "user_input", 512)
        current = input_obj["current_search_state"]
        if current is not None:
            current = validate_search_state(
                current.to_dict() if isinstance(current, SearchState) else current,
                self.registry,
            ).to_dict()
        state_json = json.dumps(current, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return [
            {"role": "system", "content": f"{self._system_prefix}当前搜索状态：{state_json}"},
            {"role": "user", "content": user_input},
        ]


def messages_to_text(messages: list[Message]) -> str:
    """Readable search prompt for local inspection."""
    return "\n".join(f"[{message['role']}] {message['content']}" for message in messages)
