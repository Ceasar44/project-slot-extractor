"""API and trace contracts for independent search comparison lanes."""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    left_model_id: str = Field(min_length=1)
    right_model_id: str = Field(min_length=1)
    user_input: str = Field(min_length=1, max_length=512)
    mode: Literal["sequential", "parallel"] = "sequential"
    current_search_state: dict[str, Any] | None = None
    left_current_search_state: dict[str, Any] | None = None
    right_current_search_state: dict[str, Any] | None = None

    def state_for(self, side: str):
        key = f"{side}_current_search_state"
        return getattr(self, key) if key in self.model_fields_set else self.current_search_state


class LoadModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    model_id: str = Field(min_length=1)


class ClientLogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    level: Literal["info", "error"]
    message: str = Field(min_length=1, max_length=2048)
    context: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class SearchEvent:
    kind: str
    payload: dict[str, Any]


@dataclass
class ModelSideResult:
    model_id: str
    status: str = "error"
    raw_output: str | None = None
    parsed_patch: dict | None = None
    validation: dict = field(default_factory=lambda: {"valid": None, "errors": []})
    current_state: dict | None = None
    merged_state: dict | None = None
    next_state: dict | None = None
    state_diff: list[dict] = field(default_factory=list)
    compiled_query: dict | None = None
    metrics: dict = field(default_factory=dict)
    error: dict | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SearchTrace:
    result: ModelSideResult
    events: tuple[SearchEvent, ...]
