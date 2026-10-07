"""Deterministic search intents drawn exclusively from validated Registry candidates."""

import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.registry import Registry
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference, SortSpec
from slot_extractor.schemas.search_state import SearchState


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        items = [canonical(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return value


def encoded(value):
    return json.dumps(canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_signature(scenario, patch, state=None):
    return hashlib.sha256(
        encoded({"scenario": scenario, "patch": patch, "state": state}).encode()
    ).hexdigest()


@dataclass(frozen=True)
class IntentPlan:
    id: str
    scenario: str
    state_json: str
    patch_json: str
    assertions_json: str
    expressions: tuple[str, ...]
    language: str
    style: str
    order: str

    def record(self, user_input):
        return {
            "id": self.id,
            "scenario": self.scenario,
            "tags": ["pending"],
            "input": {
                "current_search_state": json.loads(self.state_json),
                "user_input": user_input,
            },
            "expected": json.loads(self.patch_json),
            "assertions": json.loads(self.assertions_json),
        }

    def to_dict(self):
        return {
            **self.record(""),
            "expressions": list(self.expressions),
            "language": self.language,
            "style": self.style,
            "order": self.order,
            "semantic_signature": semantic_signature(
                self.scenario, json.loads(self.patch_json), json.loads(self.state_json)
            ),
        }

    def assert_matches(self, record):
        if record["scenario"] != self.scenario:
            raise ValueError("generated scenario differs from IntentPlan")
        if canonical(record["input"]["current_search_state"]) != json.loads(self.state_json):
            raise ValueError("generated current_search_state differs from IntentPlan")
        if canonical(record["expected"]) != json.loads(self.patch_json):
            raise ValueError(
                "generated Gold differs from IntentPlan; preserve every planned condition"
            )
        if encoded(record["assertions"]) != self.assertions_json:
            raise ValueError("generated assertions differ from IntentPlan")


class Planner:
    def __init__(self, registry: Registry, config):
        self.registry = registry
        self.rng = random.Random(config.get("seed", 42))
        self.counts = Counter()
        options = config["planning"]
        self.numeric = options.get("numeric_pools", {})
        self.currencies = options.get("currencies", [None, "USD", "EUR", "CNY"])
        self.query_terms = options.get("query_terms", [])
        self.unmapped_terms = options.get("unmapped_terms", [])
        self.languages = options.get("languages", ["zh", "en", "mixed"])
        self.styles = options.get("styles", ["statement", "question", "colloquial"])
        self.orders = options.get("orders", ["forward", "reverse", "shuffled"])
        for items, allowed, name in (
            (self.languages, {"zh", "en", "mixed"}, "languages"),
            (self.styles, {"statement", "question", "colloquial"}, "styles"),
            (self.orders, {"forward", "reverse", "shuffled"}, "orders"),
        ):
            if not items or len(set(items)) != len(items) or not set(items) <= allowed:
                raise ValueError(f"invalid planning.{name}")
        for name in self.numeric:
            if registry.field(name).type not in {"number", "integer"}:
                raise ValueError(f"numeric pool is not a numeric Registry field: {name}")
        for spec in registry.fields:
            if spec.type in {"number", "integer"} and spec.model_extractable:
                pool = self.numeric.get(spec.name)
                if not isinstance(pool, list) or len(pool) < 2:
                    raise ValueError(
                        f"planning.numeric_pools.{spec.name} needs at least two values"
                    )
                unit = spec.units[0].code if spec.units else None
                operator = next(
                    (op for op in spec.hard_operators if op in {"eq", "gte", "lte", "between"}),
                    None,
                )
                if operator is None:
                    raise ValueError(f"no hard numeric operator for {spec.name}")
                for value in pool:
                    # Registry validator, including numeric types, bounds and operator payloads.
                    SearchPatch.from_dict(
                        SearchPatch(
                            hard_filters=(
                                HardFilter(
                                    spec.name,
                                    operator,
                                    value=value if operator != "between" else None,
                                    min_value=value if operator == "between" else None,
                                    max_value=value if operator == "between" else None,
                                    unit=unit,
                                ),
                            )
                        ).to_dict(),
                        registry,
                    )
                if len(set(pool)) != len(pool):
                    raise ValueError(f"duplicate numeric pool values for {spec.name}")
            if spec.unit_kind == "currency":
                if not self.currencies or any(
                    unit is not None
                    and (not isinstance(unit, str) or re.fullmatch(spec.unit_pattern, unit) is None)
                    for unit in self.currencies
                ):
                    raise ValueError("planning.currencies violates Registry unit_pattern")
        for items, limit, name in (
            (self.query_terms, 128, "query_terms"),
            (self.unmapped_terms, 64, "unmapped_terms"),
        ):
            if (
                not items
                or len(set(items)) != len(items)
                or any(
                    not isinstance(term, str) or not term.strip() or len(term) > limit
                    for term in items
                )
            ):
                raise ValueError(f"invalid planning.{name}; use a reviewed free-text pool")
        self.fields = [registry.field(name) for name in registry.model_extractable_fields()]

    def pick(self, group, candidates, key=lambda item: str(item)):
        candidates = list(candidates)
        if not candidates:
            raise ValueError(f"no Registry-legal candidates for {group}")
        scores = [self.counts[(group, key(item))] for item in candidates]
        minimum = min(scores)
        chosen = self.rng.choice(
            [item for item, score in zip(candidates, scores, strict=True) if score == minimum]
        )
        self.counts[(group, key(chosen))] += 1
        return chosen

    def field(self, scenario, soft=False, exclude=(), predicate=lambda spec: True):
        return self.pick(
            (scenario, "soft" if soft else "hard", "field"),
            [
                spec
                for spec in self.fields
                if spec.name not in exclude
                and predicate(spec)
                and (spec.soft_operators if soft else spec.hard_operators)
            ],
            key=lambda spec: spec.name,
        )

    def condition(self, scenario, spec, soft=False, operator=None):
        ops = spec.soft_operators if soft else spec.hard_operators
        operator = operator or self.pick(
            (scenario, spec.name, "soft" if soft else "hard", "operator"), ops
        )
        if operator not in ops:
            raise ValueError(f"illegal planned operator {spec.name}:{operator}")
        values = ()
        value = low = high = unit = None
        expression = ""
        if spec.values:
            selected = self.pick((scenario, spec.name, "value"), spec.values, key=lambda v: v.code)
            values = (selected.code,)
            alias = self.pick(
                (scenario, spec.name, selected.code, "alias"),
                (selected.label, *selected.aliases, selected.code),
            )
            expression = alias
        elif spec.type == "boolean":
            value = self.pick((scenario, spec.name, "boolean"), [False, True])
            expression = f"{spec.name}={str(value).lower()}（明确说明烘烤稳定性要求）"
        else:
            if spec.units:
                unit = self.pick((scenario, spec.name, "unit"), [u.code for u in spec.units])
            elif spec.unit_kind == "currency":
                unit = self.pick((scenario, spec.name, "unit"), self.currencies)
            if operator == "between":
                low, high = self.pick(
                    (scenario, spec.name, "interval"),
                    combinations(sorted(self.numeric[spec.name]), 2),
                )
                expression = f"{spec.name}: {low}–{high} {unit or '（不指定币种）'}"
            elif operator not in {"lower", "higher"}:
                value = self.pick((scenario, spec.name, "number"), self.numeric[spec.name])
                expression = f"{spec.name}: {value} {unit or ''}"
            else:
                expression = f"{spec.name}: {operator}，不要补数值"
        cls = SoftPreference if soft else HardFilter
        condition = cls(
            spec.name,
            operator,
            value=value,
            values=values,
            min_value=low,
            max_value=high,
            unit=unit,
        )
        return condition, f"{'软偏好' if soft else '硬要求'} {operator}: {expression}"

    def assertions(self, patch, state):
        items = [
            ("minimal_patch", None),
            ("no_unknown_field", None),
            ("no_unknown_value", None),
            ("no_hallucinated_filter", None),
        ]
        touched = {c.field for c in (*patch.hard_filters, *patch.soft_preferences)}
        for name in sorted(touched):
            items.extend([("field_exact", name), ("operator_correct", name)])
        for name in patch.clear_fields:
            items.append(("field_cleared", name))
        if state and not patch.reset:
            old = {c.field for c in (*state.hard_filters, *state.soft_preferences)}
            for name in sorted(old & touched):
                items.append(("field_replaced", name))
            for name in sorted(old - touched - set(patch.clear_fields)):
                items.append(("field_preserved", name))
        if patch.soft_preferences:
            items.append(("hard_soft_correct", None))
        if any(c.op == "not_in" for c in patch.hard_filters) or any(
            c.preference == "avoid" for c in patch.soft_preferences
        ):
            items.append(("negation_correct", None))
        if "allergen" in touched:
            items.append(("allergen_semantics_correct", None))
        if patch.query_text:
            items.append(("query_text_correct", None))
        if patch.sort:
            items.append(("sort_correct", None))
        if patch.unmapped_terms:
            items.append(("unmapped_correct", None))
        # Tags have their own bound; assertions intentionally have no 16-item cap.
        return [{"type": kind, "field": field} for kind, field in dict.fromkeys(items)]

    def plan(self, scenario, index, split):
        hard, soft, expressions = [], [], []
        state = None
        patch_args = {}

        def add(spec, prefer=False, op=None):
            condition, expression = self.condition(scenario, spec, prefer, op)
            (soft if prefer else hard).append(condition)
            expressions.append(expression)
            return condition

        if scenario == "single_filter":
            spec = self.pick((scenario, "field"), self.fields, key=lambda f: f.name)
            prefer = (
                not spec.hard_operators
                or bool(spec.soft_operators)
                and self.pick((scenario, spec.name, "strength"), [False, True])
            )
            add(spec, prefer)
        elif scenario in {"multi_filter", "hard_soft_mix"}:
            count = 2 if scenario == "multi_filter" else 1
            if self.pick((scenario, "extra_condition"), [False, True]):
                count += 1
            for _ in range(count):
                add(self.field(scenario, exclude=[c.field for c in hard]))
            if scenario == "hard_soft_mix":
                add(self.field(scenario, soft=True, exclude=[c.field for c in hard]), True)
        elif scenario == "negation":
            prefer = self.pick((scenario, "strength"), [False, True])
            op = "avoid" if prefer else "not_in"
            add(
                self.field(
                    scenario,
                    soft=prefer,
                    predicate=lambda f: op in (f.soft_operators if prefer else f.hard_operators),
                ),
                prefer,
                op,
            )
        elif scenario == "allergy_vs_flavor":
            name = self.pick((scenario, "boundary"), ["allergen", "flavor"])
            add(self.registry.field(name), op="not_in")
            expressions.append(
                "明确过敏安全排除" if name == "allergen" else "只是排除口味，不是过敏"
            )
        elif scenario in {"numeric_price", "numeric_size"}:
            add(self.registry.field("price" if scenario == "numeric_price" else "size"))
        elif scenario == "relative_numeric":
            spec = self.field(
                scenario,
                soft=True,
                predicate=lambda f: bool(set(f.soft_operators) & {"lower", "higher", "around"}),
            )
            op = self.pick(
                (scenario, spec.name, "relative_op"),
                [op for op in spec.soft_operators if op in {"lower", "higher", "around"}],
            )
            add(spec, True, op)
        elif scenario in {"replace", "preserve_state"}:
            spec = self.field(scenario)
            new = add(spec)
            old, _ = self.condition(scenario, spec)
            for _ in range(100):
                if old != new:
                    break
                old, _ = self.condition(scenario, spec)
            else:
                raise ValueError(f"no distinct replacement for {spec.name}")
            keep_spec = self.field(scenario, exclude=[spec.name])
            keep, _ = self.condition(scenario, keep_spec)
            state = SearchState(hard_filters=(old, keep))
            expressions.append("只修改指定字段，其他条件保持不变")
        elif scenario == "clear":
            name = self.pick((scenario, "clear"), sorted(self.registry.clearable_fields()))
            patch_args["clear_fields"] = (name,)
            if name == "query_text":
                state = SearchState(query_text=self.pick((scenario, "old_query"), self.query_terms))
            elif name == "sort":
                sort = self.pick(
                    (scenario, "old_sort"),
                    [
                        SortSpec(s.field, order)
                        for s in self.registry.search.sort_fields
                        for order in s.orders
                    ],
                )
                state = SearchState(sort=sort)
            else:
                old, _ = self.condition(scenario, self.registry.field(name))
                state = SearchState(hard_filters=(old,))
            expressions.append(f"明确取消 {name} 的已有条件，不添加新条件")
        elif scenario == "reset":
            old, _ = self.condition(scenario, self.field(scenario))
            state = SearchState(hard_filters=(old,))
            patch_args["reset"] = True
            add(self.field(scenario))
            expressions.append("明确重新开始搜索，旧条件全部不要")
        elif scenario == "sort":
            selected = self.pick(
                (scenario, "sort"),
                [
                    SortSpec(s.field, order)
                    for s in self.registry.search.sort_fields
                    for order in s.orders
                ],
            )
            patch_args["sort"] = selected
            expressions.append(f"明确按 {selected.field} {selected.order} 排序")
        elif scenario == "query_text":
            term = self.pick((scenario, "query"), self.query_terms)
            patch_args["query_text"] = term
            expressions.append(f"商品全文搜索关键词：{term}，原文保留")
        elif scenario == "unmapped":
            term = self.pick((scenario, "unmapped"), self.unmapped_terms)
            patch_args["unmapped_terms"] = (term,)
            expressions.append(f"无法安全映射的要求：{term}，原文保留，不能发明过滤字段")
        else:
            raise ValueError(f"unimplemented scenario {scenario}")
        patch = SearchPatch(hard_filters=tuple(hard), soft_preferences=tuple(soft), **patch_args)
        # Never emit a planned record before complete Registry/state/scenario validation.
        SearchPatch.from_dict(patch.to_dict(), self.registry)
        if state:
            SearchState.from_dict(state.to_dict(), self.registry)
        plan = IntentPlan(
            f"{split}-{index:06d}",
            scenario,
            encoded(state.to_dict() if state else None),
            encoded(patch.to_dict()),
            encoded(self.assertions(patch, state)),
            tuple(expressions),
            self.pick((scenario, "language"), self.languages),
            self.pick((scenario, "style"), self.styles),
            self.pick((scenario, "order"), self.orders),
        )
        record = plan.record("需求草稿：" + "；".join(expressions))
        record["tags"] = derive_tags(record, self.registry)
        raw_sample_from_record(record, self.registry)
        return plan


def build_generation_plan(config, registry):
    planner = Planner(registry, config)
    plans = []
    for scenario, count in config["counts"].items():
        if scenario not in SCENARIOS or type(count) is not int or count < 0:
            raise ValueError("invalid scenario quota")
        for _ in range(count):
            plans.append(planner.plan(scenario, len(plans) + 1, config.get("split", "train")))
    if not plans:
        raise ValueError("generation plan must be nonempty")
    return plans


def interleave_requests(requests):
    groups = {}
    for request in requests:
        groups.setdefault(request.scenario, []).append(request)
    return [
        group[index]
        for index in range(max(map(len, groups.values()), default=0))
        for group in groups.values()
        if index < len(group)
    ]
