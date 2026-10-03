# src/slot_extractor/schemas/results.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .search_patch import SearchPatch


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    prefill_ms: float | None
    first_token_ms: float | None
    total_ms: float
    output_tokens: int | None = None
    tokens_per_s: float | None = None
    input_tokens: int | None = None
    decode_ms: float | None = None
    prefill_tokens_per_s: float | None = None
    decode_tokens_per_s: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DimensionScore:
    dimension: str
    score: float | None
    passed: bool | None
    detail: str


@dataclass(frozen=True)
class CaseResult:
    sample_id: str
    model_output: str
    dimensions: dict[str, DimensionScore]
    output: SearchPatch | None = None
    scenario: str | None = None
    total_ms: float | None = None
    first_token_ms: float | None = None
    tokens_per_s: float | None = None
    tags: list[str] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    field_counts: dict[str, int] = field(default_factory=dict)
    expected: dict[str, Any] | None = None
    merged_state: dict[str, Any] | None = None
    expected_state: dict[str, Any] | None = None


@dataclass(frozen=True)
class LegacyCaseResult:
    """Explicit report shape for historical appointment evaluation."""

    sample_id: str
    output_kind: str
    conversation_kind: str
    model_output: str
    dimensions: dict[str, DimensionScore]
    total_ms: float | None = None
    first_token_ms: float | None = None
    tokens_per_s: float | None = None


@dataclass(frozen=True)
class TimingSummary:
    """全样本原始时延统计（不卡阈值，供后续分析）。单位：毫秒 / tokens/s。"""

    count: int
    total_ms_mean: float | None
    total_ms_p50: float | None
    total_ms_p95: float | None
    total_ms_max: float | None
    total_ms_min: float | None
    first_token_ms_mean: float | None
    tokens_per_s_mean: float | None


@dataclass(frozen=True)
class Scorecard:
    model: str
    n: int
    dimensions: dict[str, DimensionScore]
    cases: list[CaseResult] | list[LegacyCaseResult]
    timing: TimingSummary | None = None


@dataclass(frozen=True)
class SearchScorecard(Scorecard):
    scenario_slices: dict[str, Any] = field(default_factory=dict)
    assertion_stats: dict[str, Any] = field(default_factory=dict)
    field_metrics: dict[str, Any] = field(default_factory=dict)
