"""Registry-aware baking raw gold generation with validation feedback."""

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from slot_extractor.data.generation_plan import IntentPlan
from slot_extractor.data.generation_quality import (
    generation_response_schema,
    validate_generation_quality,
)
from slot_extractor.data.raw_sample import RAW_FIELDS, RawSample, raw_sample_from_record
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.inference.base import Backend, GenerationParams
from slot_extractor.prompts.rules import SYSTEM_RULES, render_registry_summary
from slot_extractor.registry import Registry
from slot_extractor.schemas.output import parse_model_json
from slot_extractor.utils.jsonl import write_jsonl


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
        "user_input 必须是完整自然的用户搜索需求，至少4个有意义的文字字符，"
        "不是单字符、占位符或句子的首字。Gold 中每个分类取值必须在原话中显式出现"
        "其 Registry 名称或别名，数值使用阿拉伯数字；不要仅凭场景或参考例句填写 Gold。\n"
        'id 由程序分配，tags 由程序推导；暂填 tags=["pending"]。\n'
        f"提取规则：{SYSTEM_RULES}\nRegistry：{render_registry_summary(registry)}\n"
        f"Raw JSON Schema：{json.dumps(generation_response_schema(registry), ensure_ascii=False)}"
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


def build_planned_messages(plan: IntentPlan, registry: Registry) -> list[dict]:
    system = (
        "你是烘焙搜索训练样本的自然语言创作者。只输出六字段 Raw JSON，不输出解释或代码围栏。"
        "程序已分配合法意图，必须保持提供的 id/scenario/current_search_state/expected/assertions，"
        "只创作 input.user_input，tags 暂填 pending。不要推断或增加计划外条件。"
        "原话需要完整、自然，至少4个有意义字符。计划里每个条件都要有原话依据；"
        "分类值使用 Registry 名称或别名，数值和单位显式保留，省略币种时不能补币种。"
        "硬要求、软偏好、否定、清除和重置的强度必须忠实表达，当前状态不是本轮新需求。"
        "query_text/unmapped_terms 需要包含指定原文。不同场景不要套用同一用途/风味/预算例句。\n"
        f"抽取规则：{SYSTEM_RULES}\nRegistry：{render_registry_summary(registry)}\n"
        f"Raw JSON Schema：{json.dumps(generation_response_schema(registry), ensure_ascii=False)}"
    )
    user = (
        f"场景要求：{SCENARIOS[plan.scenario].instruction}\n"
        f"语言={plan.language}；风格={plan.style}；条件表达顺序={plan.order}。"
        "语言风格不能改变条件语义；代号表示 zh中文、en英文、mixed中英混合。\n"
        f"表达依据：{json.dumps(plan.expressions, ensure_ascii=False)}\n"
        "下面六字段中，user_input 的空字符串只是待填写位置，必须生成完整原话；"
        "其余计划不得改动：\n" + json.dumps(plan.record(""), ensure_ascii=False)
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_raw_json(text: str) -> dict:
    try:
        return parse_model_json(text)
    except ValueError as exc:
        raise GenerationError(str(exc)) from exc


class RawGenerator:
    def __init__(
        self,
        backend: Backend,
        registry: Registry,
        max_attempts: int = 3,
        diagnostics_dir: Path | None = None,
    ):
        if type(max_attempts) is not int or max_attempts < 1:
            raise GenerationError("max_attempts must be a positive integer")
        self.backend, self.registry, self.max_attempts = backend, registry, max_attempts
        self.diagnostics_dir = diagnostics_dir

    def generate_one(
        self,
        request: GenerationRequest,
        *,
        rejected_sample: RawSample | None = None,
        plan: IntentPlan | None = None,
    ) -> RawSample:
        sample_id = generation_sample_id(request)
        if plan is not None and (plan.id != sample_id or plan.scenario != request.scenario):
            raise GenerationError("request differs from assigned IntentPlan")
        messages = (
            build_planned_messages(plan, self.registry)
            if plan is not None
            else build_generation_messages(request, self.registry)
        )
        if rejected_sample is not None:
            messages.extend(
                [
                    {
                        "role": "assistant",
                        "content": json.dumps(rejected_sample.to_dict(), ensure_ascii=False),
                    },
                    {
                        "role": "user",
                        "content": (
                            "上一个样本的 user_input 与已有训练数据或独立评估数据重复，不能入库。"
                            "保持本题 ID、场景、目标字段及单/多轮要求，重新创作明显不同的用户原话，"
                            "不要只修改空白、ID 或 current_search_state。"
                            "同步修改 expected 和 assertions，使 Gold 忠实对应新的用户原话。"
                            "输出完整的六字段 Raw JSON。"
                        ),
                    },
                ]
            )
        params = GenerationParams(
            temperature=0.7,
            max_tokens=4096,
            response_schema=generation_response_schema(self.registry),
            response_schema_name="baking_search_raw",
        )
        last_error = None
        for attempt in range(self.max_attempts):
            result = self.backend.generate(messages, params)
            try:
                record = parse_raw_json(result.text)
                if set(record) != RAW_FIELDS:
                    raise GenerationError("raw output must contain exactly the six fixed fields")
                if record.get("scenario") != request.scenario:
                    raise GenerationError("scenario differs from requested scenario")
                record["id"] = sample_id
                record["tags"] = ["pending"]
                if plan is not None:
                    plan.assert_matches(record)
                sample = raw_sample_from_record(record, self.registry)
                if {"type": "minimal_patch", "field": None} not in sample.assertions:
                    raise GenerationError("assertions must include global minimal_patch")
                multi = sample.input["current_search_state"] is not None
                if multi != SCENARIOS[request.scenario].multi_turn:
                    raise GenerationError("current_search_state differs from requested turn type")
                conditions = sample.expected["hard_filters"] + sample.expected["soft_preferences"]
                if request.scenario == "single_filter" and plan is None:
                    fields = self.registry.model_extractable_fields()
                    target = fields[(request.index - 1) % len(fields)]
                    if conditions[0]["field"] != target:
                        raise GenerationError(f"single_filter must cover requested field: {target}")
                if request.scenario == "allergy_vs_flavor" and plan is None:
                    target = "allergen" if request.index % 2 else "flavor"
                    excluded = {
                        c["field"]
                        for c in conditions
                        if c.get("op") == "not_in" or c.get("preference") == "avoid"
                    }
                    if target not in excluded or ({"allergen", "flavor"} - {target}) & excluded:
                        raise GenerationError(f"allergy_vs_flavor must exclude only {target}")
                record["tags"] = derive_tags(sample.to_dict(), self.registry)
                sample = raw_sample_from_record(record, self.registry)
                validate_generation_quality(sample, self.registry, plan=plan)
                return sample
            except ValueError as exc:
                last_error = exc
                if self.diagnostics_dir is not None:
                    # Unique file per attempt: duplicate rewrites do not overwrite earlier evidence.
                    write_jsonl(
                        self.diagnostics_dir / f"{sample_id}-{uuid.uuid4().hex}.jsonl",
                        [
                            {
                                "id": sample_id,
                                "attempt": attempt + 1,
                                "error": str(exc),
                                "output_text": result.text,
                                "response_id": getattr(result, "raw", {}).get("id"),
                                "plan": plan.to_dict() if plan else None,
                            }
                        ],
                    )
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
