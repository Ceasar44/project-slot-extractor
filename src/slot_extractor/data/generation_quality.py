"""Conservative generation-only checks, distinct from the public Raw/Eval contract."""

import json
import re
from decimal import Decimal

from slot_extractor.data.raw_sample import RawSample
from slot_extractor.data.raw_schema import raw_response_schema
from slot_extractor.registry import Registry

MIN_INPUT_CHARACTERS = 4


def generation_response_schema(registry: Registry) -> dict:
    schema = raw_response_schema(registry)
    text = schema["$defs"]["input"]["properties"]["user_input"]
    text["minLength"] = 1
    text["description"] = "完整自然的用户搜索需求，明确表达 Gold 条件，不能只输出首字符或占位符。"
    return schema


def _mentions(text: str, alias: str) -> bool:
    alias = alias.strip().casefold()
    if not alias:
        return False
    if alias.isascii():
        # English multiword labels allow ordinary whitespace or hyphen typography.
        # Registry codes containing underscores still require the exact code spelling.
        pattern = r"[\s\-\u2010-\u2015]+".join(re.escape(word) for word in alias.split())
        return (
            re.search(r"(?<![a-z0-9_])" + pattern + r"(?![a-z0-9_])", text, flags=re.IGNORECASE)
            is not None
        )
    return alias in text


def _has_cue(text, cues):
    # Match English words, not substrings such as "no" at the end of "piano".
    normalized = text.replace("’", "'").replace("‘", "'")
    forms = {
        "prefer": (
            "prefer",
            "prefers",
            "preferred",
            "preferring",
            "preference",
            "preferences",
            "preferably",
        ),
        "avoid": ("avoid", "avoids", "avoided", "avoiding", "avoidance"),
        "exclude": ("exclude", "excludes", "excluded", "excluding"),
    }
    return any(_mentions(normalized, form) for cue in cues for form in forms.get(cue, (cue,)))


def _mentions_unit(text, alias):
    if alias == "元":
        return re.search(r"\d\s*元", text) is not None
    if alias == "克":
        return re.search(r"(?<!千)克", text) is not None
    if alias.isascii():
        return (
            re.search(r"(?<![a-z])" + re.escape(alias.casefold()) + r"(?![a-z])", text) is not None
        )
    return alias in text


def validate_generation_quality(sample: RawSample, registry: Registry, *, plan=None) -> None:
    """Reject obvious ungrounded Gold; this does not certify full semantic correctness."""
    text = sample.input["user_input"].strip().casefold()
    if plan is not None:
        plan.assert_matches(sample.to_dict())
    if sum(c.isalnum() for c in text) < MIN_INPUT_CHARACTERS:
        raise ValueError(
            "generation quality: user_input must express a complete search request with at least "
            f"{MIN_INPUT_CHARACTERS} letters/digits/Chinese characters; "
            f"got {sample.input['user_input']!r}. "
            "Rewrite the entire user_input, not just its first character or punctuation."
        )
    # A period followed by a digit belongs to a decimal; a sentence-ending period does not.
    numbers = {Decimal(m) for m in re.findall(r"(?<![\d.])-?\d+(?:\.\d+)?(?!\d|\.\d)", text)}
    for condition in sample.expected["hard_filters"] + sample.expected["soft_preferences"]:
        spec = registry.field(condition["field"])
        for code in condition["values"]:
            value = next(v for v in spec.values if v.code == code)
            aliases = (value.code, value.label, *value.aliases)
            if not any(_mentions(text, alias) for alias in aliases):
                raise ValueError(
                    f"generation quality: {spec.name}={code} "
                    "has no explicit value/alias in user_input. "
                    f"user_input={sample.input['user_input']!r}. "
                    "Recognized expressions for this value: "
                    f"{json.dumps(list(dict.fromkeys(aliases)), ensure_ascii=False)}. "
                    "Use one of those expressions explicitly in the rewritten user_input. "
                    "Rewrite the request to explicitly mention the intended value, or remove "
                    "the unsupported condition; "
                    "do not invent a condition from an unrelated sentence."
                )
        if spec.type in {"number", "integer"}:
            for key in ("value", "min_value", "max_value"):
                value = condition[key]
                if value is not None and Decimal(str(value)) not in numbers:
                    raise ValueError(
                        f"generation quality: {spec.name}.{key}={value} is absent from user_input. "
                        "For generated samples, explicitly write numeric values "
                        "using Arabic digits; "
                        "do not infer thresholds from vague language."
                    )
    if plan is not None:
        _validate_planned_text(sample, registry)


def _validate_planned_text(sample, registry):
    """Check explicit evidence; indirect phrasing and full semantics still need review."""
    text = sample.input["user_input"].casefold()
    clauses = re.split(r"[，,；;。.!?！？\n]", text)
    negative = (
        "不要",
        "排除",
        "不含",
        "不能含",
        "不想要",
        "不太想要",
        "不太想选",
        "别用",
        "避免",
        "避开",
        "不选",
        "exclude",
        "avoid",
        "without",
        "no ",
        "not ",
        "don't",
        "do not",
        "steer clear of",
        "stay away from",
        "rather not",
        "not keen on",
        "not a fan of",
    )
    preference = (
        "最好",
        "优先",
        "尽量",
        "偏好",
        "希望",
        "软偏好",
        "prefer",
        "ideally",
        "if possible",
        "would like",
        "rather",
        "不太想要",
        "不太想选",
        "not keen on",
        "not a fan of",
    )
    for kind, operator_key in (("hard_filters", "op"), ("soft_preferences", "preference")):
        for condition in sample.expected[kind]:
            spec = registry.field(condition["field"])
            if spec.values:
                aliases = [
                    alias
                    for value in spec.values
                    if value.code in condition["values"]
                    for alias in (value.code, value.label, *value.aliases)
                ]
                relevant = [
                    clause for clause in clauses if any(_mentions(clause, a) for a in aliases)
                ]
                explicit_field = [clause for clause in relevant if spec.name in clause]
                if explicit_field:
                    relevant = explicit_field
                is_negative = any(_has_cue(clause, negative) for clause in relevant)
                allergy = any("过敏" in clause or "allergic" in clause for clause in relevant)
                is_negative = is_negative or (spec.name == "allergen" and allergy)
                expected_negative = condition[operator_key] in {"not_in", "avoid"}
                if is_negative != expected_negative:
                    raise ValueError(
                        "planned text: negation does not match "
                        f"{spec.name}:{condition[operator_key]}"
                    )
                if spec.name == "flavor" and allergy:
                    raise ValueError(
                        "planned text: allergy cannot be expressed as ordinary flavor exclusion"
                    )
                if kind == "soft_preferences" and not any(
                    _has_cue(clause, preference) for clause in relevant
                ):
                    raise ValueError(
                        f"planned text: explicitly express soft preference for {spec.name}"
                    )
                optional = ("最好", "优先", "尽量", "偏好", "prefer", "ideally", "if possible")
                if (
                    kind == "hard_filters"
                    and spec.name != "allergen"
                    and any(_has_cue(clause, optional) for clause in relevant)
                ):
                    raise ValueError(f"planned text: hard requirement softened for {spec.name}")
            unit = condition["unit"]
            aliases = {
                "g": ("g", "克", "gram", "grams"),
                "kg": ("kg", "公斤", "千克", "kilogram", "kilograms"),
                "oz": ("oz", "盎司", "ounce", "ounces"),
                "USD": ("usd", "美元", "dollar", "dollars", "$"),
                "EUR": ("eur", "欧元", "euro", "euros", "€"),
                "CNY": ("cny", "人民币", "rmb", "元"),
            }
            if unit and not any(
                _mentions_unit(text, alias) for alias in aliases.get(unit, (unit,))
            ):
                raise ValueError(f"planned text: explicitly preserve original unit {unit}")
            if (
                spec.unit_kind == "currency"
                and unit is None
                and any(
                    _mentions_unit(text, alias)
                    for key in ("USD", "EUR", "CNY")
                    for alias in aliases[key]
                )
            ):
                raise ValueError("planned text: planned price has no currency; do not add one")
    query = sample.expected["query_text"]
    if query and query.casefold() not in text:
        raise ValueError("planned text: include the planned query_text verbatim")
    if sample.expected["reset"] and not any(
        cue in text
        for cue in (
            "重新",
            "重来",
            "从头",
            "reset",
            "start over",
            "restart",
            "start again",
        )
    ):
        raise ValueError("planned text: explicitly express reset")
    if sample.expected["clear_fields"] and not any(
        cue in text
        for cue in (
            "取消",
            "清除",
            "不限",
            "不要",
            "去掉",
            "remove",
            "clear",
            "cancel",
            "no limit",
            "drop",
        )
    ):
        raise ValueError("planned text: explicitly express clearing existing conditions")
