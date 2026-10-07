# src/slot_extractor/utils/jsonl.py
from __future__ import annotations

import json
import time
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

_RAW_ORDER = ("id", "scenario", "tags", "input", "expected", "assertions")
_INPUT_ORDER = ("current_search_state", "user_input")
_PATCH_ORDER = (
    "schema_version",
    "reset",
    "hard_filters",
    "soft_preferences",
    "clear_fields",
    "query_text",
    "sort",
    "unmapped_terms",
)
_STATE_ORDER = ("query_text", "hard_filters", "soft_preferences", "sort")
_PAYLOAD_ORDER = ("value", "values", "min_value", "max_value", "unit")


def order_search_raw_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Return a detached ordered Raw record; leave unrelated JSONL formats untouched."""
    if not set(_RAW_ORDER).issubset(record):
        return record

    def ordered(value, order=()):
        if isinstance(value, list):
            return [ordered(item) for item in value]
        if not isinstance(value, dict):
            return value
        if not order:
            if set(_INPUT_ORDER) == set(value):
                order = _INPUT_ORDER
            elif set(_PATCH_ORDER) == set(value):
                order = _PATCH_ORDER
            elif set(_STATE_ORDER) == set(value):
                order = _STATE_ORDER
            elif {"field", "op", *_PAYLOAD_ORDER} == set(value):
                order = ("field", "op", *_PAYLOAD_ORDER)
            elif {"field", "preference", *_PAYLOAD_ORDER} == set(value):
                order = ("field", "preference", *_PAYLOAD_ORDER)
            elif set(value) == {"type", "field"}:
                order = ("type", "field")
            elif set(value) == {"field", "order"}:
                order = ("field", "order")
        keys = [key for key in order if key in value]
        keys.extend(key for key in value if key not in keys)
        return {key: ordered(value[key]) for key in keys}

    return ordered(record, _RAW_ORDER)


def replace_with_retry(source: Path, target: Path, attempts: int = 10) -> None:
    """Keep the old checkpoint intact while retrying transient Windows file locks."""
    for attempt in range(attempts):
        try:
            source.replace(target)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(min(0.1 * 2**attempt, 1.0))


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    jsonl_path = Path(path)
    with jsonl_path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{jsonl_path}:{line_no} is not valid JSON: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{jsonl_path}:{line_no} must contain a JSON object")
            yield value


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(
                json.dumps(
                    order_search_raw_fields(record), ensure_ascii=False, separators=(",", ":")
                )
                + "\n"
            )
    replace_with_retry(temporary, target)
