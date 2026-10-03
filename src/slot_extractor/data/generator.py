"""Registry-aware baking raw gold generation with validation feedback."""

import json
from dataclasses import dataclass

from slot_extractor.data.raw_sample import RAW_FIELDS, RawSample, raw_sample_from_record
from slot_extractor.data.raw_schema import raw_response_schema
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.inference.base import Backend, GenerationParams
from slot_extractor.prompts.rules import SYSTEM_RULES, render_registry_summary
from slot_extractor.registry import Registry
from slot_extractor.schemas.output import parse_model_json


class GenerationError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationRequest:
    scenario: str
    index: int
    split: str = "train"
    seed: int = 42


def generation_sample_id(request: GenerationRequest) -> str:
    if request.scenario not in SCENARIOS:
        raise GenerationError(f"unknown scenario: {request.scenario}")
    if type(request.index) is not int or not 1 <= request.index <= 999999:
        raise GenerationError("index must be an integer between 1 and 999999")
    if request.split not in {"train", "val", "eval"} or type(request.seed) is not int:
        raise GenerationError("invalid split or seed")
    return f"{request.split}-{request.index:06d}"


def build_generation_messages(request: GenerationRequest, registry: Registry) -> list[dict]:
    sample_id = generation_sample_id(request)
    spec = SCENARIOS[request.scenario]
    system = (
        "你是烘焙风味酱搜索意图 Raw Gold 数据生成器。只输出单个原始 JSON，不要解释或代码围栏。\n"
        "严格包含 id/scenario/tags/input/expected/assertions 六个顶层字段。"
        "input 仅含 current_search_state 和 user_input；expected 是本轮最小 SearchPatch。\n"
        "assertions 使用 {type,field} 对象，覆盖本题重要评分点，包含全局 minimal_patch。"
        "不要生成自然语言回复、工具调用或完整历史。使用自然多样的中英文表达，不照抄例句。\n"
        'id 由程序分配，tags 由程序推导；暂填 tags=["pending"]。\n'
        f"提取规则：{SYSTEM_RULES}\nRegistry：{render_registry_summary(registry)}\n"
        f"Raw JSON Schema：{json.dumps(raw_response_schema(registry), ensure_ascii=False)}"
    )
    user = (
        f"Sample ID: {sample_id}\nscenario: {request.scenario}\n"
        f"多样性种子：{request.seed}，序号：{request.index}\n"
        f"场景硬约束：{spec.instruction}\n参考表达：{spec.example}\n"
        + (
            "必须提供非空的 current_search_state。"
            if spec.multi_turn
            else "本场景生成单轮样本，current_search_state=null。"
        )
    )
    if request.scenario == "single_filter":
        fields = registry.model_extractable_fields()
        user += f"\n本题目标字段：{fields[(request.index - 1) % len(fields)]}。"
    elif request.scenario == "allergy_vs_flavor":
        target = "allergen" if request.index % 2 else "flavor"
        user += f"\n本题排除语义目标：{target}，不得附加另一字段的排除。"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_raw_json(text: str) -> dict:
    try:
        return parse_model_json(text)
    except ValueError as exc:
        raise GenerationError(str(exc)) from exc


class RawGenerator:
    def __init__(self, backend: Backend, registry: Registry, max_attempts: int = 3):
        if type(max_attempts) is not int or max_attempts < 1:
            raise GenerationError("max_attempts must be a positive integer")
        self.backend, self.registry, self.max_attempts = backend, registry, max_attempts

    def generate_one(self, request: GenerationRequest) -> RawSample:
        sample_id = generation_sample_id(request)
        messages = build_generation_messages(request, self.registry)
        params = GenerationParams(
            temperature=0.7,
            max_tokens=4096,
            response_schema=raw_response_schema(self.registry),
            response_schema_name="baking_search_raw",
        )
        last_error = None
        for _ in range(self.max_attempts):
            result = self.backend.generate(messages, params)
            try:
                record = parse_raw_json(result.text)
                if set(record) != RAW_FIELDS:
                    raise GenerationError("raw output must contain exactly the six fixed fields")
                if record.get("scenario") != request.scenario:
                    raise GenerationError("scenario differs from requested scenario")
                record["id"] = sample_id
                record["tags"] = ["pending"]
                sample = raw_sample_from_record(record, self.registry)
                if {"type": "minimal_patch", "field": None} not in sample.assertions:
                    raise GenerationError("assertions must include global minimal_patch")
                multi = sample.input["current_search_state"] is not None
                if multi != SCENARIOS[request.scenario].multi_turn:
                    raise GenerationError("current_search_state differs from requested turn type")
                conditions = sample.expected["hard_filters"] + sample.expected["soft_preferences"]
                if request.scenario == "single_filter":
                    fields = self.registry.model_extractable_fields()
                    target = fields[(request.index - 1) % len(fields)]
                    if conditions[0]["field"] != target:
                        raise GenerationError(f"single_filter must cover requested field: {target}")
                if request.scenario == "allergy_vs_flavor":
                    target = "allergen" if request.index % 2 else "flavor"
                    excluded = {
                        c["field"]
                        for c in conditions
                        if c.get("op") == "not_in" or c.get("preference") == "avoid"
                    }
                    if target not in excluded or ({"allergen", "flavor"} - {target}) & excluded:
                        raise GenerationError(f"allergy_vs_flavor must exclude only {target}")
                record["tags"] = derive_tags(sample.to_dict(), self.registry)
                return raw_sample_from_record(record, self.registry)
            except ValueError as exc:
                last_error = exc
                messages = [
                    *messages,
                    {"role": "assistant", "content": result.text},
                    {"role": "user", "content": f"校验失败：{exc}。修正并输出完整原始 JSON。"},
                ]
        raise GenerationError(
            f"{sample_id} failed after {self.max_attempts} attempts: {last_error}"
        ) from last_error

    def generate_many(self, requests: list[GenerationRequest]) -> list[RawSample]:
        ids = [generation_sample_id(request) for request in requests]
        if len(ids) != len(set(ids)):
            raise GenerationError("duplicate generation request id")
        return [self.generate_one(request) for request in requests]
