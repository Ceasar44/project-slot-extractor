"""Author the fixed, synthetic baking-v1.0 evaluation artifact, never training data.

The curated cases below are the source, not an LLM generation recipe. Refuse to
overwrite published artifacts. Gold replay checks the harness, not model quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

from slot_extractor.data.coverage_audit import audit_semantic_coverage
from slot_extractor.data.tag_audit import audit_tags, derive_tags
from slot_extractor.evaluation.assertions import evaluate_in_context, prepare_evaluation
from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.inference.mock import MockBackend, MockResponse
from slot_extractor.registry import load_registry
from slot_extractor.schemas.dataset_contract import validate_dataset_against_contract
from slot_extractor.schemas.sample import sample_from_record
from slot_extractor.search import merge_search_state

QUOTAS = dict(
    zip(
        (
            "single_filter",
            "multi_filter",
            "hard_soft_mix",
            "negation",
            "allergy_vs_flavor",
            "replace",
            "clear",
            "preserve_state",
            "numeric_price",
            "numeric_size",
            "relative_numeric",
            "sort",
            "query_text",
            "unmapped",
            "reset",
        ),
        (20, 15, 20, 10, 25, 15, 10, 15, 15, 10, 10, 5, 5, 10, 15),
        strict=True,
    )
)
DATE = "2026-10-06"
DATASET = Path("data/eval/baking-v1.0")
DOCS = Path("docs/baking-frozen-eval-v1")


def condition(
    field, operator, value=None, *, values=None, low=None, high=None, unit=None, soft=False
):
    return {
        "field": field,
        "preference" if soft else "op": operator,
        "value": value,
        "values": values or [],
        "min_value": low,
        "max_value": high,
        "unit": unit,
    }


def cat(field, *values, op="in"):
    return condition(field, op, values=list(values))


def pref(field, *values, op="prefer"):
    return condition(field, op, values=list(values), soft=True)


def num(field, op, value=None, **kwargs):
    return condition(field, op, value, **kwargs)


def patch(hard=(), soft=(), clear=(), query=None, sort=None, reset=False, unmapped=()):
    return {
        "schema_version": "1.0",
        "reset": reset,
        "hard_filters": list(hard),
        "soft_preferences": list(soft),
        "clear_fields": list(clear),
        "query_text": query,
        "sort": sort,
        "unmapped_terms": list(unmapped),
    }


def state(hard=(), soft=(), query=None, sort=None):
    return {
        "hard_filters": list(hard),
        "soft_preferences": list(soft),
        "query_text": query,
        "sort": sort,
    }


def curated_cases():
    rows = []

    def add(scenario, text, gold, reason, current=None, checks=()):
        assertions = [
            ("no_unknown_field", None),
            ("no_unknown_value", None),
            ("no_hallucinated_filter", None),
            ("minimal_patch", None),
        ]
        touched = sorted({c["field"] for c in gold["hard_filters"] + gold["soft_preferences"]})
        assertions.extend(("field_exact", field) for field in touched)
        assertions.extend(("operator_correct", field) for field in touched)
        if gold["soft_preferences"]:
            assertions.append(("hard_soft_correct", None))
        if any(c["op"] == "not_in" for c in gold["hard_filters"]) or any(
            c["preference"] == "avoid" for c in gold["soft_preferences"]
        ):
            assertions.append(("negation_correct", None))
        if scenario == "allergy_vs_flavor" or "allergen" in touched:
            assertions.append(("allergen_semantics_correct", None))
        assertions.extend(("field_cleared", field) for field in gold["clear_fields"])
        for field, kind in (("query_text", "query_text_correct"), ("sort", "sort_correct")):
            if gold[field] is not None:
                assertions.append((kind, None))
        if gold["unmapped_terms"]:
            assertions.append(("unmapped_correct", None))
        assertions.extend(checks)
        assertions = list(dict.fromkeys(assertions))
        rows.append(
            {
                "record": {
                    "id": f"eval-{len(rows) + 1:06d}",
                    "scenario": scenario,
                    "tags": [scenario],
                    "input": {"current_search_state": deepcopy(current), "user_input": text},
                    "expected": deepcopy(gold),
                    "assertions": [{"type": t, "field": f} for t, f in assertions],
                },
                "rationale": reason,
            }
        )

    # Single conditions cover all fourteen fields without inferred attributes.
    singles = [
        (
            "只找涂抹酱这一种产品形态。",
            cat("product_type", "cream_spread"),
            "产品形态明确；不推断用途。",
        ),
        (
            "我要水果风味这一大类，具体水果不限。",
            cat("flavor_family", "fruit"),
            "只给大类，不猜具体风味。",
        ),
        ("这次只选开心果味。", cat("flavor", "pistachio"), "具体风味不重复输出父级。"),
        (
            "要用在泡芙上，其他条件没要求。",
            cat("application", "choux_puff"),
            "制作对象不推断夹馅或质构。",
        ),
        ("使用方式必须是淋面。", cat("use_mode", "drizzle"), "使用方式与产品形态独立。"),
        ("我需要有颗粒感的质构。", cat("texture", "chunky"), "物理质构明示。"),
        ("只看标注纯素的商品。", cat("dietary_claim", "vegan"), "饮食声明不扩展过敏原排除。"),
        (
            "必须排除含芝麻过敏原的商品。",
            cat("allergen", "sesame", op="not_in"),
            "安全排除为硬条件。",
        ),
        ("未开封必须可以常温保存。", cat("storage", "shelf_stable"), "未开封储存要求。"),
        ("必须经过验证能耐烤。", num("bake_stable", "eq", True), "耐烤明确为布尔真。"),
        ("甜度等级就选3级。", num("sweetness_level", "eq", 3), "明确等级，不是相对偏好。"),
        ("风味强度至少4级。", num("flavor_intensity", "gte", 4), "明确数值下界。"),
        ("每件标价必须是18美元。", num("price", "eq", 18, unit="USD"), "精确价格及显式币种。"),
        ("净含量恰好250克装。", num("size", "eq", 250, unit="g"), "规格精确值。"),
        (
            "产品形态只接受水果制品或果酱。",
            cat("product_type", "fruit_preparation"),
            "产品形态不猜水果口味。",
        ),
        ("风味指定为black sesame。", cat("flavor", "black_sesame"), "英文别名映射，不输出未知值。"),
        ("拿来做macaron，其他随意。", cat("application", "macaron"), "英文制作对象。"),
        ("需要标明无麸质的。", cat("dietary_claim", "gluten_free"), "声明不自行增加wheat排除。"),
        ("只接受未开封冷冻储存的。", cat("storage", "frozen"), "储存枚举映射。"),
        (
            "商品必须明确标注不耐烤。",
            num("bake_stable", "eq", False),
            "明确假值；未知属性不等于假。",
        ),
    ]
    for text, c, reason in singles:
        add("single_filter", text, patch([c]), reason)

    multis = [
        (
            "做可颂夹馅用，两个条件都必须满足。",
            [cat("application", "croissant_pastry"), cat("use_mode", "fill")],
        ),
        (
            "要抹茶味，并且未开封常温保存。",
            [cat("flavor", "matcha"), cat("storage", "shelf_stable")],
        ),
        (
            "选淋酱这种形态，质构必须流动型。",
            [cat("product_type", "sauce_topping"), cat("texture", "pourable")],
        ),
        (
            "必须是纯素商品，而且排除含花生过敏原的。",
            [cat("dietary_claim", "vegan"), cat("allergen", "peanut", op="not_in")],
        ),
        (
            "只要黑巧克力味，甜度最多2级。",
            [cat("flavor", "dark_chocolate"), num("sweetness_level", "lte", 2)],
        ),
        (
            "必须用于蛋糕，且要可裱挤的质构。",
            [cat("application", "cake_cupcake"), cat("texture", "pipeable")],
        ),
        (
            "单件不超过22美元，至少500克装。",
            [num("price", "lte", 22, unit="USD"), num("size", "gte", 500, unit="g")],
        ),
        (
            "只能选水果大类，而且要无乳制品声明。",
            [cat("flavor_family", "fruit"), cat("dietary_claim", "dairy_free")],
        ),
        (
            "草莓或蓝莓都行，但必须是果酱形态。",
            [cat("flavor", "strawberry", "blueberry"), cat("product_type", "fruit_preparation")],
        ),
        (
            "用于曲奇一起烘烤，商品必须验证耐烤。",
            [
                cat("application", "cookie_biscuit"),
                cat("use_mode", "bake_in"),
                num("bake_stable", "eq", True),
            ],
        ),
        (
            "要可挤压质构，并且未开封冷藏。",
            [cat("texture", "squeezable"), cat("storage", "refrigerated")],
        ),
        ("找咖啡味的，使用方式必须是拌入。", [cat("flavor", "coffee"), cat("use_mode", "swirl")]),
        (
            "需要无蛋声明，风味强度限定2到4级。",
            [cat("dietary_claim", "egg_free"), num("flavor_intensity", "between", low=2, high=4)],
        ),
        (
            "用于面包涂抹，不接受有颗粒的质构。",
            [
                cat("application", "bread_toast"),
                cat("use_mode", "spread"),
                cat("texture", "chunky", op="not_in"),
            ],
        ),
        (
            "选夹馅酱形态、香草味和1公斤装，都是硬要求。",
            [
                cat("product_type", "filling_paste"),
                cat("flavor", "vanilla"),
                num("size", "eq", 1, unit="kg"),
            ],
        ),
    ]
    for text, cs in multis:
        add("multi_filter", text, patch(cs), "只提取明示的多个硬条件；并列用途不推导额外属性。")

    mixes = [
        (
            "必须用于可颂夹心，口味最好是开心果。",
            [cat("application", "croissant_pastry"), cat("use_mode", "fill")],
            [pref("flavor", "pistachio")],
        ),
        (
            "预算上限20美元，甜度希望低一点。",
            [num("price", "lte", 20, unit="USD")],
            [num("sweetness_level", "lower", soft=True)],
        ),
        (
            "必须是淋酱，最好是流动型质构。",
            [cat("product_type", "sauce_topping")],
            [pref("texture", "pourable")],
        ),
        (
            "标明纯素是必须的，风味优先抹茶。",
            [cat("dietary_claim", "vegan")],
            [pref("flavor", "matcha")],
        ),
        (
            "必须排除牛奶过敏原，最好常温保存。",
            [cat("allergen", "milk", op="not_in")],
            [pref("storage", "shelf_stable")],
        ),
        (
            "规格至少500克，价格希望低一些。",
            [num("size", "gte", 500, unit="g")],
            [num("price", "lower", soft=True)],
        ),
        (
            "商品必须耐烤，风味强度希望高一点。",
            [num("bake_stable", "eq", True)],
            [num("flavor_intensity", "higher", soft=True)],
        ),
        (
            "必须用于蛋糕，尽量避开咖啡味。",
            [cat("application", "cake_cupcake")],
            [pref("flavor", "coffee", op="avoid")],
        ),
        (
            "甜度必须1到3级，最好带水果风味。",
            [num("sweetness_level", "between", low=1, high=3)],
            [pref("flavor_family", "fruit")],
        ),
        (
            "必须有无麸质声明，使用方式最好是涂抹。",
            [cat("dietary_claim", "gluten_free")],
            [pref("use_mode", "spread")],
        ),
        (
            "选草莓味是硬要求，净含量最好约8盎司。",
            [cat("flavor", "strawberry")],
            [num("size", "around", 8, unit="oz", soft=True)],
        ),
        (
            "只能选未开封冷藏的，产品形态最好是涂抹酱。",
            [cat("storage", "refrigerated")],
            [pref("product_type", "cream_spread")],
        ),
        (
            "必须用于泡芙，最好有无蛋声明。",
            [cat("application", "choux_puff")],
            [pref("dietary_claim", "egg_free")],
        ),
        (
            "必须有颗粒，价格最好在12到18美元之间。",
            [cat("texture", "chunky")],
            [num("price", "between", low=12, high=18, unit="USD", soft=True)],
        ),
        (
            "风味必须是焙茶，甜度最好在2到3级之间。",
            [cat("flavor", "hojicha")],
            [num("sweetness_level", "between", low=2, high=3, soft=True)],
        ),
        (
            "必须是500克装，最好不要冷冻储存。",
            [num("size", "eq", 500, unit="g")],
            [pref("storage", "frozen", op="avoid")],
        ),
        (
            "必须用于冰淇淋，风味强度最好约3级。",
            [cat("application", "ice_cream_frozen")],
            [num("flavor_intensity", "around", 3, soft=True)],
        ),
        (
            "必须是奶油酱形态，尽量不选勺取型质构。",
            [cat("product_type", "cream_spread")],
            [pref("texture", "spoonable", op="avoid")],
        ),
        (
            "预算不得超过16美元，最好用于塔派。",
            [num("price", "lte", 16, unit="USD")],
            [pref("application", "tart_pie")],
        ),
        (
            "必须排除鸡蛋过敏原，风味优先香草或卡仕达。",
            [cat("allergen", "egg", op="not_in")],
            [pref("flavor", "vanilla", "custard")],
        ),
    ]
    for text, hard, soft in mixes:
        add(
            "hard_soft_mix",
            text,
            patch(hard, soft),
            "必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。",
        )

    negatives = [
        ("不要焦糖味，其他风味没限制。", patch([cat("flavor", "caramel", op="not_in")])),
        ("尽量避开榛子味，但不是硬性要求。", patch(soft=[pref("flavor", "hazelnut", op="avoid")])),
        ("排除冷冻储存的商品。", patch([cat("storage", "frozen", op="not_in")])),
        ("最好别选淋酱这种形态。", patch(soft=[pref("product_type", "sauce_topping", op="avoid")])),
        ("不要颗粒质构。", patch([cat("texture", "chunky", op="not_in")])),
        ("尽量不用涂抹这种使用方式。", patch(soft=[pref("use_mode", "spread", op="avoid")])),
        (
            "不要茶与咖啡这一整个风味大类。",
            patch([cat("flavor_family", "tea_coffee", op="not_in")]),
        ),
        ("最好不要用于咖啡饮品。", patch(soft=[pref("application", "coffee_drink", op="avoid")])),
        ("不看带纯素声明的商品。", patch([cat("dietary_claim", "vegan", op="not_in")])),
        (
            "不要红豆味，也不要紫薯味。",
            patch([cat("flavor", "red_bean", "purple_sweet_potato", op="not_in")]),
        ),
    ]
    for text, gold in negatives:
        add("negation", text, gold, "否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。")

    safety = [
        ("我对花生过敏，必须排除含花生过敏原的产品。", "allergen", ["peanut"]),
        ("只是不要花生味，没有提出过敏要求。", "flavor", ["peanut"]),
        ("我对开心果过敏，必须排除开心果过敏原。", "allergen", ["pistachio"]),
        ("开心果味不喜欢，请排除这种口味。", "flavor", ["pistachio"]),
        ("榛子过敏，请过滤含榛子过敏原的。", "allergen", ["hazelnut"]),
        ("不要榛子风味，仅仅是口味选择。", "flavor", ["hazelnut"]),
        ("对杏仁过敏，含杏仁过敏原的不能要。", "allergen", ["almond"]),
        ("杏仁味排除掉，不要追加其他限制。", "flavor", ["almond"]),
        ("必须排除树坚果过敏原。", "allergen", ["tree_nut"]),
        ("牛奶过敏，请排除牛奶过敏原。", "allergen", ["milk"]),
        ("对鸡蛋过敏，排除鸡蛋过敏原。", "allergen", ["egg"]),
        ("小麦过敏，含小麦过敏原的不能买。", "allergen", ["wheat"]),
        ("对大豆过敏，必须排除大豆过敏原。", "allergen", ["soy"]),
        ("芝麻过敏，筛掉含芝麻过敏原的。", "allergen", ["sesame"]),
        ("不要黑芝麻味的，我只是在选口味。", "flavor", ["black_sesame"]),
        ("腰果过敏，排除腰果过敏原，不扩大范围。", "allergen", ["cashew"]),
        ("核桃过敏，必须排除核桃过敏原。", "allergen", ["walnut"]),
        ("我对花生和鸡蛋过敏，二者都必须排除。", "allergen", ["peanut", "egg"]),
        ("牛奶及大豆过敏原都不接受。", "allergen", ["milk", "soy"]),
        ("排除花生味和榛子味，别把口味偏好当过敏。", "flavor", ["peanut", "hazelnut"]),
    ]
    for text, field, values in safety:
        add(
            "allergy_vs_flavor",
            text,
            patch([cat(field, *values, op="not_in")]),
            "过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。",
        )
    add(
        "allergy_vs_flavor",
        "花生过敏必须排除花生过敏原，同时口味必须是黑巧克力。",
        patch([cat("allergen", "peanut", op="not_in"), cat("flavor", "dark_chocolate")]),
        "安全条件与风味条件分别提取，不能互相替代。",
    )
    add(
        "allergy_vs_flavor",
        "必须排除牛奶过敏原，另外不要牛奶巧克力味。",
        patch([cat("allergen", "milk", op="not_in"), cat("flavor", "milk_chocolate", op="not_in")]),
        "分别明示两个排除意图，两个字段都保留。",
    )
    add(
        "allergy_vs_flavor",
        "尽量避开花生味，其他没有限制。",
        patch(soft=[pref("flavor", "peanut", op="avoid")]),
        "普通风味软回避，不添加allergen。",
    )
    add(
        "allergy_vs_flavor",
        "开心果味是必须的，但必须排除花生过敏原。",
        patch([cat("flavor", "pistachio"), cat("allergen", "peanut", op="not_in")]),
        "花生安全限制不扩大为所有树坚果。",
    )
    add(
        "allergy_vs_flavor",
        "花生过敏必须排除花生过敏原，最好选草莓味。",
        patch([cat("allergen", "peanut", op="not_in")], [pref("flavor", "strawberry")]),
        "安全限制是硬条件，最好口味是软偏好。",
    )

    replacements = [
        (
            "口味改成必须抹茶，原来的口味条件取消。",
            state([cat("flavor", "pistachio")]),
            patch([cat("flavor", "matcha")]),
            "flavor",
        ),
        (
            "原来的口味硬要求改为最好草莓。",
            state([cat("flavor", "pistachio")]),
            patch(soft=[pref("flavor", "strawberry")]),
            "flavor",
        ),
        (
            "口味现在必须是黑巧，原先软偏好不保留。",
            state(soft=[pref("flavor", "matcha")]),
            patch([cat("flavor", "dark_chocolate")]),
            "flavor",
        ),
        (
            "预算上限改为30美元。",
            state([num("price", "lte", 20, unit="USD")]),
            patch([num("price", "lte", 30, unit="USD")]),
            "price",
        ),
        (
            "包装改成恰好1公斤装。",
            state([num("size", "eq", 500, unit="g")]),
            patch([num("size", "eq", 1, unit="kg")]),
            "size",
        ),
        (
            "储存要求换成必须冷藏。",
            state([cat("storage", "shelf_stable")]),
            patch([cat("storage", "refrigerated")]),
            "storage",
        ),
        (
            "质构改成必须有颗粒。",
            state([cat("texture", "pourable")]),
            patch([cat("texture", "chunky")]),
            "texture",
        ),
        (
            "产品形态换成淋酱，作为硬要求。",
            state([cat("product_type", "cream_spread")]),
            patch([cat("product_type", "sauce_topping")]),
            "product_type",
        ),
        (
            "用途改成必须用于马卡龙。",
            state([cat("application", "cake_cupcake")]),
            patch([cat("application", "macaron")]),
            "application",
        ),
        (
            "使用方式换成必须淋面。",
            state([cat("use_mode", "fill")]),
            patch([cat("use_mode", "drizzle")]),
            "use_mode",
        ),
        (
            "甜度改成最多2级，不保留原来甜度条件。",
            state([num("sweetness_level", "eq", 4)]),
            patch([num("sweetness_level", "lte", 2)]),
            "sweetness_level",
        ),
        (
            "风味强度不设具体等级了，改为浓一点优先。",
            state([num("flavor_intensity", "eq", 2)]),
            patch(soft=[num("flavor_intensity", "higher", soft=True)]),
            "flavor_intensity",
        ),
        (
            "排序换成价格从高到低。",
            state(sort={"field": "price", "order": "asc"}),
            patch(sort={"field": "price", "order": "desc"}),
            "sort",
        ),
        (
            "全文搜索词改为Dubai Chocolate，原词不要了。",
            state(query="Paris Style"),
            patch(query="Dubai Chocolate"),
            "query_text",
        ),
        (
            "风味大类改成必须茶与咖啡，原来的水果类不要了。",
            state([cat("flavor_family", "fruit")]),
            patch([cat("flavor_family", "tea_coffee")]),
            "flavor_family",
        ),
    ]
    for text, current, gold, field in replacements:
        add(
            "replace",
            text,
            gold,
            "同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。",
            current,
            [("field_replaced", field)],
        )

    clears = [
        ("价格不限了，取消预算条件。", state([num("price", "lte", 20, unit="USD")]), ["price"]),
        ("不用限制包装规格了。", state([num("size", "gte", 500, unit="g")]), ["size"]),
        ("口味不挑了，取消口味要求。", state([cat("flavor", "pistachio")]), ["flavor"]),
        (
            "常温偏好撤销，储存条件不限。",
            state(soft=[pref("storage", "shelf_stable")]),
            ["storage"],
        ),
        ("质构限制取消。", state([cat("texture", "chunky")]), ["texture"]),
        ("排序取消，恢复默认排序。", state(sort={"field": "rating", "order": "desc"}), ["sort"]),
        ("把全文搜索词清掉。", state(query="Dubai Chocolate"), ["query_text"]),
        (
            "价格和规格这两个条件都取消。",
            state([num("price", "lte", 25, unit="USD"), num("size", "eq", 1, unit="kg")]),
            ["price", "size"],
        ),
        (
            "取消甜度条件，硬限制和偏好都不保留。",
            state(
                [num("sweetness_level", "lte", 3)], [num("sweetness_level", "around", 2, soft=True)]
            ),
            ["sweetness_level"],
        ),
        ("耐烤不再作为筛选条件。", state([num("bake_stable", "eq", True)]), ["bake_stable"]),
    ]
    for text, current, fields in clears:
        add(
            "clear",
            text,
            patch(clear=fields),
            "明确取消已有条件，仅写clear_fields；不伪造null条件。",
            current,
        )

    keeps = [
        (
            "口味换成必须抹茶，20美元预算不变。",
            state([cat("flavor", "pistachio"), num("price", "lte", 20, unit="USD")]),
            patch([cat("flavor", "matcha")]),
            "flavor",
            "price",
        ),
        (
            "预算提高到30美元以内，草莓味不变。",
            state([cat("flavor", "strawberry"), num("price", "lte", 15, unit="USD")]),
            patch([num("price", "lte", 30, unit="USD")]),
            "price",
            "flavor",
        ),
        (
            "规格改成1公斤装，冷藏要求保持。",
            state([num("size", "eq", 250, unit="g"), cat("storage", "refrigerated")]),
            patch([num("size", "eq", 1, unit="kg")]),
            "size",
            "storage",
        ),
        (
            "用途改成马卡龙，夹馅方式照旧。",
            state([cat("application", "choux_puff"), cat("use_mode", "fill")]),
            patch([cat("application", "macaron")]),
            "application",
            "use_mode",
        ),
        (
            "改为淋面使用，奶油酱形态不变。",
            state([cat("use_mode", "spread"), cat("product_type", "cream_spread")]),
            patch([cat("use_mode", "drizzle")]),
            "use_mode",
            "product_type",
        ),
        (
            "质构换成有颗粒，纯素声明要求不变。",
            state([cat("texture", "spoonable"), cat("dietary_claim", "vegan")]),
            patch([cat("texture", "chunky")]),
            "texture",
            "dietary_claim",
        ),
        (
            "口味改成必须香草，花生过敏原排除照旧。",
            state([cat("flavor", "coffee"), cat("allergen", "peanut", op="not_in")]),
            patch([cat("flavor", "vanilla")]),
            "flavor",
            "allergen",
        ),
        (
            "甜度换成最多2级，耐烤要求不动。",
            state([num("sweetness_level", "eq", 4), num("bake_stable", "eq", True)]),
            patch([num("sweetness_level", "lte", 2)]),
            "sweetness_level",
            "bake_stable",
        ),
        (
            "风味强度改为浓一点优先，抹茶口味不变。",
            state([num("flavor_intensity", "eq", 2), cat("flavor", "matcha")]),
            patch(soft=[num("flavor_intensity", "higher", soft=True)]),
            "flavor_intensity",
            "flavor",
        ),
        (
            "储存改成必须常温，价格排序保持。",
            state([cat("storage", "frozen")], sort={"field": "price", "order": "asc"}),
            patch([cat("storage", "shelf_stable")]),
            "storage",
            "sort",
        ),
        (
            "排序改为评分从高到低，全文词保持。",
            state(
                [cat("flavor", "dark_chocolate")],
                query="Dubai Chocolate",
                sort={"field": "price", "order": "asc"},
            ),
            patch(sort={"field": "rating", "order": "desc"}),
            "sort",
            "query_text",
        ),
        (
            "口味硬条件改成最好开心果，原预算不变。",
            state([cat("flavor", "hazelnut"), num("price", "lte", 24, unit="USD")]),
            patch(soft=[pref("flavor", "pistachio")]),
            "flavor",
            "price",
        ),
        (
            "只增加必须无蛋的声明要求，原来的草莓味和常温条件都保留。",
            state([cat("flavor", "strawberry"), cat("storage", "shelf_stable")]),
            patch([cat("dietary_claim", "egg_free")]),
            None,
            "flavor",
        ),
        (
            "预算改成最多28美元，原来最好纯素的偏好不变。",
            state([num("price", "lte", 18, unit="USD")], [pref("dietary_claim", "vegan")]),
            patch([num("price", "lte", 28, unit="USD")]),
            "price",
            "dietary_claim",
        ),
        (
            "口味换成必须柠檬，原有规格和排序都不动。",
            state(
                [cat("flavor", "mango"), num("size", "eq", 500, unit="g")],
                sort={"field": "newest", "order": "desc"},
            ),
            patch([cat("flavor", "lemon")]),
            "flavor",
            "size",
        ),
    ]
    for text, current, gold, changed, kept in keeps:
        checks = [("field_preserved", kept)]
        if changed:
            checks.append(("field_replaced", changed))
        add(
            "preserve_state",
            text,
            gold,
            "只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。",
            current,
            checks,
        )

    prices = [
        ("价格必须恰好9美元。", "eq", 9, None, None, "USD"),
        ("价格上限是19美元，含19。", "lte", 19, None, None, "USD"),
        ("只看至少10美元的，含10美元。", "gte", 10, None, None, "USD"),
        ("价格必须在12到26美元之间，包含两端。", "between", None, 12, 26, "USD"),
        ("只看价格为0美元的。", "eq", 0, None, None, "USD"),
        ("标价最多0美元。", "lte", 0, None, None, "USD"),
        ("单件价格必须是12.5美元。", "eq", 12.5, None, None, "USD"),
        ("最多19.99美元一件。", "lte", 19.99, None, None, "USD"),
        ("单价最低0.5美元。", "gte", 0.5, None, None, "USD"),
        ("价格限定8.5至13.5美元，含两端。", "between", None, 8.5, 13.5, "USD"),
        ("价格最多20，币种暂不指定。", "lte", 20, None, None, None),
        ("单价必须15，先不指定货币。", "eq", 15, None, None, None),
        ("单价至少6，币种没有要求。", "gte", 6, None, None, None),
        ("价格限定11到17，货币不指定。", "between", None, 11, 17, None),
        ("价格只能是7到7美元，两个边界相同。", "between", None, 7, 7, "USD"),
    ]
    for text, op, value, low, high, unit in prices:
        add(
            "numeric_price",
            text,
            patch([num("price", op, value, low=low, high=high, unit=unit)]),
            "数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。",
        )

    sizes = [
        ("包装净含量必须是300克。", "eq", 300, None, None, "g"),
        ("只看至少750克装。", "gte", 750, None, None, "g"),
        ("最多400克一包。", "lte", 400, None, None, "g"),
        ("净含量限定200到600克，含边界。", "between", None, 200, 600, "g"),
        ("必须是2公斤装。", "eq", 2, None, None, "kg"),
        ("净含量至少0.5公斤。", "gte", 0.5, None, None, "kg"),
        ("每包不超过1.5公斤。", "lte", 1.5, None, None, "kg"),
        ("规格必须在0.25到1公斤之间。", "between", None, 0.25, 1, "kg"),
        ("要恰好8oz的包装。", "eq", 8, None, None, "oz"),
        ("包装至少12盎司。", "gte", 12, None, None, "oz"),
    ]
    for text, op, value, low, high, unit in sizes:
        add(
            "numeric_size",
            text,
            patch([num("size", op, value, low=low, high=high, unit=unit)]),
            "提取包装净含量；保留g/kg/oz，不在Gold中换算为克。",
            checks=[("value_normalized", "size")],
        )

    relatives = [
        ("甜度希望低一些，不要设等级上限。", num("sweetness_level", "lower", soft=True)),
        ("甜度希望高一点，具体等级不限。", num("sweetness_level", "higher", soft=True)),
        ("甜度最好在3级左右。", num("sweetness_level", "around", 3, soft=True)),
        ("风味希望淡一点，不要猜等级。", num("flavor_intensity", "lower", soft=True)),
        ("风味浓一些优先，没指定强度等级。", num("flavor_intensity", "higher", soft=True)),
        ("风味强度最好在4级附近。", num("flavor_intensity", "around", 4, soft=True)),
        ("价格便宜一些就好，不设预算。", num("price", "lower", soft=True)),
        ("价格最好在15美元左右。", num("price", "around", 15, unit="USD", soft=True)),
        ("包装希望小一点，没要求具体规格。", num("size", "lower", soft=True)),
        ("净含量最好在1公斤左右。", num("size", "around", 1, unit="kg", soft=True)),
    ]
    for text, c in relatives:
        add(
            "relative_numeric",
            text,
            patch(soft=[c]),
            "相对表达为lower/higher/around软偏好；无锚点不猜数值。",
        )

    for text, field, order in [
        ("请按价格从低到高排列。", "price", "asc"),
        ("按价格由高到低显示。", "price", "desc"),
        ("先显示最新发布的。", "newest", "desc"),
        ("按热度从高到低排。", "popularity", "desc"),
        ("评分最高的排前面。", "rating", "desc"),
    ]:
        add(
            "sort",
            text,
            patch(sort={"field": field, "order": order}),
            "只输出明示排序；不虚构过滤条件。",
        )

    for text, query in [
        ("全文搜索关键词用Dubai Chocolate。", "Dubai Chocolate"),
        ("请用Paris Style作为全文检索词。", "Paris Style"),
        ("在商品全文中搜索限定词Christmas Edition。", "Christmas Edition"),
        ("全文检索关键词设为Sakura Collection。", "Sakura Collection"),
        ("商品全文关键词只用Summer Special。", "Summer Special"),
    ]:
        add("query_text", text, patch(query=query), "用户明示商品全文词；不创造Registry枚举。")

    unknowns = [
        ("必须是开心果味，另外整体高级一点。", [cat("flavor", "pistachio")], "整体高级一点"),
        ("必须用于蛋糕，还要有仪式感。", [cat("application", "cake_cupcake")], "有仪式感"),
        ("必须是草莓味，另外颜值高一点。", [cat("flavor", "strawberry")], "颜值高一点"),
        ("必须常温保存，还要包装有故事感。", [cat("storage", "shelf_stable")], "包装有故事感"),
        ("必须有纯素声明，还要小众一点。", [cat("dietary_claim", "vegan")], "小众一点"),
        (
            "必须是淋酱形态，还要有高级餐厅氛围。",
            [cat("product_type", "sauce_topping")],
            "有高级餐厅氛围",
        ),
        ("净含量必须500克，还要品牌有情怀。", [num("size", "eq", 500, unit="g")], "品牌有情怀"),
        (
            "价格最多21美元，还要适合拍照出片。",
            [num("price", "lte", 21, unit="USD")],
            "适合拍照出片",
        ),
        (
            "必须黑巧克力味，还要名字听起来高级。",
            [cat("flavor", "dark_chocolate")],
            "名字听起来高级",
        ),
        ("必须冷藏保存，还要整体很有格调。", [cat("storage", "refrigerated")], "整体很有格调"),
    ]
    for text, hard, fragment in unknowns:
        add(
            "unmapped",
            text,
            patch(hard, unmapped=[fragment]),
            "抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。",
        )

    old = state(
        [cat("flavor", "pistachio"), num("price", "lte", 20, unit="USD")],
        [pref("storage", "shelf_stable")],
        query="Old Collection",
        sort={"field": "price", "order": "asc"},
    )
    resets = [
        ("前面的全不要了，重新找必须草莓味的。", patch([cat("flavor", "strawberry")], reset=True)),
        ("从头搜索，只要求抹茶味。", patch([cat("flavor", "matcha")], reset=True)),
        (
            "清空所有旧条件，新的预算是最多35美元。",
            patch([num("price", "lte", 35, unit="USD")], reset=True),
        ),
        ("重新开始，只要500克装。", patch([num("size", "eq", 500, unit="g")], reset=True)),
        (
            "之前的条件都取消，现在必须用于泡芙。",
            patch([cat("application", "choux_puff")], reset=True),
        ),
        ("重置搜索，只选淋面使用方式。", patch([cat("use_mode", "drizzle")], reset=True)),
        ("全部重新来，质构必须可挤压。", patch([cat("texture", "squeezable")], reset=True)),
        ("旧条件全部撤销，只筛未开封冷藏。", patch([cat("storage", "refrigerated")], reset=True)),
        ("清空之前的搜索，只要求商品耐烤。", patch([num("bake_stable", "eq", True)], reset=True)),
        ("从头找，只要求有无大豆声明。", patch([cat("dietary_claim", "soy_free")], reset=True)),
        (
            "全部重置，现在只排除芝麻过敏原。",
            patch([cat("allergen", "sesame", op="not_in")], reset=True),
        ),
        ("重开一次搜索，只要水果风味大类。", patch([cat("flavor_family", "fruit")], reset=True)),
        (
            "旧搜索不要了，新的只希望甜度低一些。",
            patch(soft=[num("sweetness_level", "lower", soft=True)], reset=True),
        ),
        (
            "所有旧条件清空，新搜索只按最新发布排序。",
            patch(sort={"field": "newest", "order": "desc"}, reset=True),
        ),
        ("把前面的条件全部清空，暂时不添加新条件。", patch(reset=True)),
    ]
    for text, gold in resets:
        add("reset", text, gold, "reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。", old)
    return rows


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def normalized(text):
    return re.sub(r"\s+", " ", text.strip())


def audit_existing(records):
    inputs = {normalized(r["input"]["user_input"]): r["id"] for r in records}
    overlaps, scanned, count = [], [], 0
    for root in (Path("data/raw"), Path("data/processed")):
        for path in sorted(root.rglob("*.jsonl")):
            blob = path.read_bytes()
            scanned.append({"path": path.as_posix(), "sha256": sha(blob)})
            for line in blob.decode("utf-8-sig").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                count += 1
                text = row.get("input", {}).get("user_input")
                if text is None:
                    text = next(
                        (
                            m.get("value")
                            for m in row.get("conversations", [])
                            if m.get("from") == "human"
                        ),
                        None,
                    )
                if isinstance(text, str) and normalized(text) in inputs:
                    overlaps.append({"eval_id": inputs[normalized(text)], "file": path.as_posix()})
    return {
        "scanned_files": scanned,
        "scanned_rows": count,
        "exact_user_input_overlaps": overlaps,
        "scope": "Existing data/raw and data/processed JSONL; whitespace-normalized user text.",
        "limitations": "No paraphrase equivalence proof; no future baking train/val exists yet.",
    }


def check_negative_controls(samples, registry):
    """Confirm common erroneous answers fail; all outputs are scripted, not model calls."""
    controls = []

    def check(sample, wrong, label, assertion_type):
        ctx = prepare_evaluation(sample, json.dumps(wrong, ensure_ascii=False), registry)
        results = [evaluate_in_context(a, ctx) for a in sample.assertions]
        detected = any(not r.passed and r.expression["type"] == assertion_type for r in results)
        if not detected:
            raise ValueError(f"negative control undetected: {label}")
        controls.append(
            {
                "sample_id": sample.id,
                "error": label,
                "expected_failed_assertion": assertion_type,
                "detected": True,
                "wrong_output": wrong,
            }
        )

    sample = next(s for s in samples if s.scenario == "allergy_vs_flavor")
    wrong = deepcopy(sample.expected)
    wrong["hard_filters"][0]["field"] = "flavor"
    check(sample, wrong, "过敏原排除误写为风味排除", "allergen_semantics_correct")
    sample = next(s for s in samples if s.scenario == "hard_soft_mix")
    wrong = deepcopy(sample.expected)
    c = wrong["soft_preferences"].pop()
    c["op"] = "in"
    del c["preference"]
    wrong["hard_filters"].append(c)
    check(sample, wrong, "最好风味误写为硬过滤", "hard_soft_correct")
    sample = next(s for s in samples if s.scenario == "relative_numeric")
    wrong = deepcopy(sample.expected)
    wrong["soft_preferences"] = []
    wrong["hard_filters"] = [num("sweetness_level", "lte", 2)]
    check(sample, wrong, "相对甜度擅自硬量化", "hard_soft_correct")
    sample = next(s for s in samples if s.scenario == "preserve_state")
    wrong = deepcopy(sample.expected)
    wrong["reset"] = True
    check(sample, wrong, "修改口味时误重置并丢失预算", "field_preserved")
    sample = next(
        s
        for s in samples
        if s.scenario == "numeric_size" and s.expected["hard_filters"][0]["unit"] == "kg"
    )
    wrong = deepcopy(sample.expected)
    wrong["hard_filters"][0]["value"] *= 1000
    wrong["hard_filters"][0]["unit"] = "g"
    check(sample, wrong, "模型提前换算kg为g", "field_exact")
    sample = next(s for s in samples if s.scenario == "reset")
    wrong = deepcopy(sample.expected)
    wrong["reset"] = False
    check(sample, wrong, "重开搜索漏写reset", "minimal_patch")
    sample = samples[0]
    wrong = deepcopy(sample.expected)
    wrong["hard_filters"][0]["field"] = "invented_field"
    check(sample, wrong, "未知字段", "no_unknown_field")
    wrong = deepcopy(sample.expected)
    wrong["hard_filters"][0]["values"] = ["invented_value"]
    check(sample, wrong, "未知枚举", "no_unknown_value")
    return controls


def make_artifacts():
    registry_path = Path("configs/catalog/registry.yaml")
    registry = load_registry(registry_path)
    rows = curated_cases()
    for row in rows:
        row["record"]["tags"] = derive_tags(row["record"], registry)
    records = [row["record"] for row in rows]
    # Strict parser, dataset validator, coverage and tag audit are production code.
    samples = [sample_from_record(r, registry) for r in records]
    validate_dataset_against_contract(samples, registry)
    counts = Counter(r["scenario"] for r in records)
    if dict(counts) != QUOTAS or len(records) != 200:
        raise ValueError(f"scenario quota mismatch: {counts}")
    fingerprints = [normalized(r["input"]["user_input"]) for r in records]
    if len(set(fingerprints)) != len(records):
        raise ValueError("duplicate normalized user input")
    coverage = audit_semantic_coverage(samples, registry)
    tags = audit_tags(samples, registry)
    if not coverage.ok or not tags.ok:
        raise ValueError("coverage/tag audit failed")
    isolation = audit_existing(records)
    if isolation["exact_user_input_overlaps"]:
        raise ValueError("existing training input overlap")
    backend = MockBackend(
        "gold-replay-only-not-model-baseline",
        {
            r["input"]["user_input"]: MockResponse(
                json.dumps(r["expected"], ensure_ascii=False), 0, 0, 1, 1
            )
            for r in records
        },
    )
    replay = run_evaluation(samples, backend, registry)
    failures = [
        c.sample_id
        for c in replay.cases
        if c.validation_errors
        or any(a["passed"] is not True for a in c.assertions)
        or any(d.score is not None and d.score != 1 for d in c.dimensions.values())
    ]
    if failures:
        raise ValueError(f"Gold self-consistency replay failed: {failures}")
    data = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records)
    digest = sha(data.encode("utf-8"))
    similar = []
    for i, left in enumerate(records):
        for right in records[i + 1 :]:
            ratio = SequenceMatcher(
                None, left["input"]["user_input"], right["input"]["user_input"]
            ).ratio()
            if ratio >= 0.8:
                similar.append(
                    {
                        "left": left["id"],
                        "right": right["id"],
                        "ratio": round(ratio, 4),
                        "disposition": (
                            "Intentional controlled contrast; not independent observations."
                        ),
                    }
                )
    checks = {
        "dataset_id": "baking-eval-v1.0",
        "sample_count": 200,
        "scenario_counts": dict(counts),
        "contract_valid": True,
        "unique_ids": len({r["id"] for r in records}) == 200,
        "unique_normalized_user_inputs": True,
        "coverage": asdict(coverage),
        "tag_audit": asdict(tags),
        "isolation": isolation,
        "near_duplicate_pairs_threshold_0_8": similar,
        "gold_replay": {
            "purpose": "Harness/assertion self-consistency, NOT inference or baseline",
            "cases": 200,
            "assertions": sum(len(r["assertions"]) for r in records),
            "failed_ids": failures,
            "model_calls": 0,
        },
        "negative_controls": check_negative_controls(samples, registry),
    }
    reviews = []
    for row in rows:
        record = row["record"]
        reviews.append(
            {
                "id": record["id"],
                "reviewer": "Codex (AI author and reviewer)",
                "review_date": DATE,
                "source": "Synthetic curated input; no customer logs",
                "semantic_rationale": row["rationale"],
                "gold_merged_state": merge_search_state(
                    record["input"]["current_search_state"], record["expected"], registry
                ).to_dict(),
                "contract_and_assertions": "passed",
                "human_review_status": "pending",
                "independent_review": False,
            }
        )
    manifest = {
        "dataset_id": "baking-eval-v1.0",
        "version": "baking-v1.0",
        "role": "evaluation",
        "status": "frozen",
        "frozen_date": DATE,
        "sample_count": 200,
        "cases_path": (DATASET / "test.jsonl").as_posix(),
        "cases_sha256": digest,
        "registry_path": registry_path.as_posix(),
        "registry_version": registry.registry_version,
        "registry_sha256": sha(registry_path.read_bytes()),
        "scenario_counts": dict(counts),
        "source": "Explicit synthetic cases authored by Codex; no external generator calls",
        "source_path": "scripts/data/create_baking_frozen_eval_v1.py",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "review_status": "ai_reviewed_pending_independent_human_review",
        "baseline_status": "not_run_per_user_request",
        "model_calls": 0,
        "training_parent": None,
        "do_not_train_on": True,
        "limitations": [
            "Synthetic, Chinese-dominant, capability-balanced, not production frequency weighted",
            "AI author/reviewer; not independently human approved",
            "Controlled contrast samples are correlated; no confidence interval claims",
            "Not a blind holdout after use for iterative error correction",
            "Extraction benchmark; does not measure live product retrieval "
            "or food safety certification",
        ],
    }
    files = {
        DATASET / "test.jsonl": data,
        DATASET / "test.sha256": digest + "\n",
        DATASET / "coverage.json": dump(asdict(coverage)),
        DATASET / "validation-report.json": dump(checks),
        DATASET / "review-records.jsonl": "".join(
            json.dumps(r, ensure_ascii=False) + "\n" for r in reviews
        ),
    }
    files.update(make_docs(rows, reviews, checks, manifest))
    manifest["artifact_sha256"] = {p.as_posix(): sha(s.encode("utf-8")) for p, s in files.items()}
    files[DATASET / "manifest.json"] = dump(manifest)
    return files, manifest


def make_docs(rows, reviews, checks, manifest):
    heading = f"冻结评估集 baking-v1.0｜制作日期 {DATE}｜200条合成样本"
    scope = (
        "AI起草并复核；未经过独立人工审核。冻结表示本版本内容固定，不等于业务验收或食品安全认证。"
    )
    files = {}

    def doc(number, title, body):
        files[DOCS / f"{number:02d}-{title}.md"] = (
            f"# 第{number}步：{title}\n\n{heading}\n\n{body}\n"
        )

    doc(
        1,
        "评估目标与合同",
        """评估一次SearchPatch抽取：当前SearchState + 用户本轮原话 → 最小SearchPatch。

模型输入只含Registry规则、当前状态和原话；ID、场景、tags、Gold及assertions不进入Prompt。
Gold固定8字段；样本固定id/scenario/tags/input/expected/assertions六字段。
SearchState只含hard_filters/soft_preferences/query_text/sort，不存reset或clear_fields。

业务事实源为configs/catalog/registry.yaml（版本1.0）。覆盖14个可抽取字段：product_type、flavor_family、flavor、application、use_mode、texture、dietary_claim、allergen、storage、bake_stable、sweetness_level、flavor_intensity、price、size。

评估能力：字段和值、硬软强度、否定与过敏原、数值原单位、替换/清除/保持/重置、全文词、未知需求和最小Patch。
合并与单位换算由确定性代码执行；此集合不评估商品召回、Typesense在线结果或自然语言回复。

Schema Valid、Allergen Semantics、no_unknown_field、no_unknown_value验收门槛均100%；
无适用样本不算通过。
自然语言正确性依赖Gold；合同校验和Gold回放不能证明业务代表性。""",
    )
    quota_table = "| 场景 | 计划 | 实际 |\n|---|---:|---:|\n" + "".join(
        f"| {name} | {number} | {checks['scenario_counts'][name]} |\n"
        for name, number in QUOTAS.items()
    )
    field_table = "| 字段 | Gold涉及样本数（含清除） |\n|---|---:|\n" + "".join(
        f"| {name} | {number} |\n" for name, number in checks["coverage"]["fields"].items()
    )
    doc(
        2,
        "覆盖矩阵与配额",
        f"{quota_table}\n合计200条；每条一个主场景，能力与字段用派生tags交叉统计。\n\n{field_table}\n"
        "配额由业务风险人工设计，不复制训练配额，也不模拟生产频率。价格均USD或未指定币种；规格覆盖g/kg/oz。\n"
        "排序覆盖price双向及newest/popularity/rating降序。所有过敏原枚举有正向的排除测试。\n"
        "能力覆盖默认门槛为15场景、14字段和hard/soft/negation/allergen/replace/clear/preserve_state至少一次。\n"
        "覆盖通过不等于全部枚举、操作符及组合穷尽；详细算子/单位统计见coverage.json。",
    )
    input_blocks = []
    gold_blocks = []
    assertion_blocks = []
    review_table = "| ID | 场景 | 语义依据 | 合同/断言 | 独立人工审核 |\n|---|---|---|---|---|\n"
    for row, review in zip(rows, reviews, strict=True):
        r = row["record"]
        input_blocks.append(
            f"## {r['id']} · {r['scenario']}\n\n考察：{row['rationale']}\n\n"
            f"```json\n{dump(r['input'])}```\n"
        )
        gold_blocks.append(
            f"## {r['id']}\n\n原话：{r['input']['user_input']}\n\n依据：{row['rationale']}\n\n"
            f"本轮Gold：\n\n```json\n{dump(r['expected'])}```\n\n"
            f"Gold合并状态：\n\n```json\n{dump(review['gold_merged_state'])}```\n"
        )
        assertion_blocks.append(f"## {r['id']}\n\n```json\n{dump(r['assertions'])}```\n")
        review_table += f"| {r['id']} | {r['scenario']} | {row['rationale']} | 通过 | 待审核 |\n"
    doc(
        3,
        "输入样本设计",
        "来源：本次直接编写的合成输入，不是客户日志，也未使用生成API。\n"
        "总计200条。多轮用给定前态测试一次转移，不向模型传完整对话；同一前态可作为对照控制。\n"
        "用户原话均不重复。审核关注用途/形态、硬软、口味/过敏、数值/相对偏好的边界。\n\n"
        + "\n".join(input_blocks),
    )
    doc(
        4,
        "Gold标注与状态转换",
        "以下为所有样本的Gold及确定性合并结果。Gold只提取明示意图：不由用途猜形态/质构；"
        "不展开层级；不猜相对数值；不推断币种；保留kg/oz原单位。\n"
        "未修改字段只保留在合并状态中，reset丢弃旧状态。unmapped_terms为原话的连续片段。\n\n"
        + "\n".join(gold_blocks),
    )
    doc(
        5,
        "断言设计",
        "所有样本检查未知字段/值、幻觉条件和最小Patch。条件字段检查field_exact及operator_correct；"
        "按内容追加hard_soft/negation/allergen、替换/保持/清除、全文/排序/未映射断言。\n"
        "tags由derive_tags生成，不由模型或手工标签决定。所有断言参数及Gold支持性通过现有合同校验。\n\n"
        + "\n".join(assertion_blocks),
    )
    doc(
        6,
        "语义复核与审核记录",
        f"{scope}\n\n审核主体：Codex；同一AI负责作者与复核，不能称为独立人工双人审核。\n"
        "逐条检查明示字段、硬软强度、过敏原/风味、数值单位、旧态泄漏、最小Patch及不可映射片段。\n"
        "机器审核：合同、Gold支持性、确定性合并和Gold断言回放；结果可定位到每个ID。\n"
        "下面的依据是AI语义复核记录，不是外部专家签字。正式验收前建议逐条独立审核。\n"
        "若审核改变样本内容，发布新版本；不要直接改冻结的test.jsonl。\n\n" + review_table,
    )
    doc(
        7,
        "程序校验覆盖与隔离",
        "校验使用项目现有严格Sample解析、合同、audit_semantic_coverage、audit_tags及评分器。\n"
        f"结果：200条合法，15场景配额匹配，14字段覆盖，ID/归一化原话唯一；{checks['gold_replay']['assertions']}条断言Gold回放通过。\n"
        "Gold回放直接返回已知Gold，不调用模型，不记录虚构性能数字，不是基线或模型准确率。\n"
        "另用8个脚本错误输出验证评分器能检出：过敏/风味混淆、硬软误判、相对数值硬量化、"
        "丢失旧状态、单位提前换算、漏reset、未知字段及未知值。全部正确拒绝，不调用模型。\n"
        f"隔离：扫描data/raw与data/processed下{len(checks['isolation']['scanned_files'])}个JSONL，"
        f"共{checks['isolation']['scanned_rows']}行，未发现归一化原话完全相同的训练输入。\n"
        f"内部SequenceMatcher相似度≥0.8共有{len(checks['near_duplicate_pairs_threshold_0_8'])}对；详见validation-report.json。\n"
        "对照样本允许相关表达；不要把它们视作独立随机抽样或据此宣称统计置信度。\n"
        "没有未来烘焙训练集，因此当前隔离只针对已存在文件；后续生成/构建仍必须检查训练隔离。"
        "字符串检查不能证明近义改写隔离。\n\n"
        "```powershell\nuv run python -m scripts.eval.validate_dataset\n"
        "uv run python -m scripts.data.generate_search_raw "
        "--config configs/data/baking_search_v1.yaml --dry-run\n```\n"
        "完整机器结果在data/eval/baking-v1.0/validation-report.json。",
    )
    doc(
        8,
        "冻结版本与来源",
        f"冻结版本：baking-v1.0；日期：{DATE}；样本200条。\n\n"
        f"test.jsonl SHA256：`{manifest['cases_sha256']}`\n\n"
        f"Registry SHA256：`{manifest['registry_sha256']}`\n\n"
        "产物：test.jsonl、test.sha256、DATASET_CARD.md、coverage.json、validation-report.json、review-records.jsonl和manifest.json。\n"
        "manifest记录样本、Registry、制备脚本及文档hash；dataset-registry记录frozen状态与AI审核边界。\n"
        f"{scope}\n\n"
        "禁止训练使用本集或近义改写；改变Gold、原话或合同应建立新版本并同步配置。\n"
        "制备脚本默认dry-run，只有--publish写入；已有正式产物时拒绝覆盖。\n\n"
        "```powershell\nGet-FileHash data/eval/baking-v1.0/test.jsonl -Algorithm SHA256\n```\n"
        "完整来源和产物核验：`uv run python -m scripts.eval.verify_frozen_search_eval`。\n"
        "纳入Git的提交由用户决定；本次没有执行提交或推送。",
    )
    doc(
        9,
        "基线暂缓与后续使用",
        "按用户要求，本次不运行未微调基线，也不训练、不量化、不启动模型服务器。\n"
        "基线状态：not_run_per_user_request。已有Gold回放只验证数据与评分器自洽。\n"
        "后续先为未微调模型另配推理配置，再使用同一冻结文件；当前baking默认配置是SFT模型。\n"
        "正式训练Raw生成可读取此冻结文件进行输入隔离；先审Gold再训练。\n"
        "对评估错误定向修复后，此集合不是独立盲测；最终泛化验收应另留未曝光holdout。\n"
        "当前不调用外部API，不下载权重，不生成训练数据。",
    )
    files[DOCS / "README.md"] = (
        "# 烘焙冻结评估集制作记录\n\n"
        + heading
        + "\n\n"
        + scope
        + "\n\n"
        + "\n".join(f"- [{p.stem}]({p.name})" for p in files if p.parent == DOCS)
        + "\n\n"
    )
    files[DATASET / "DATASET_CARD.md"] = f"""# Baking Frozen Eval v1.0

冻结日期：{DATE}；200条合成评估样本；15类场景；14个可抽取字段。
用途：烘焙搜索SearchPatch抽取及一次状态转换的能力评估，禁止训练使用。

来源：Codex逐项编写固定样本和Gold，无生成API调用，无真实客户日志。
审核：AI作者/复核，自洽校验通过；独立人工审核待完成。frozen仅表示内容版本固定。
基线：按用户要求暂不运行；没有真实模型效果或性能结论。

样本固定六字段；当前状态+本轮原话为输入；expected为最小Patch；单轮为null状态。
场景与派生tags、断言适用性均符合当前Registry及严格数据合同。

{quota_table}

校验：合同/ID/归一化原话、场景配额、语义覆盖、标签及Gold断言回放全部通过。
Gold回放并非模型评估；独立语义审核仍需人工确认。
已扫描历史Raw/SFT JSONL，未发现相同归一化输入；近义改写和未来训练集仍须复核。

局限：中文为主，人工配额分布不代表真实流量；全文词为明示检索指令，未穷尽自然表达；
未穷尽枚举/操作符/组合、歧义及矛盾输入、非USD币种、极长表达；
相近对照样本有关联，不能宣称独立随机样本置信区间；不评估真实检索或食品安全认证。
多轮采用给定前态逐轮测试，不覆盖端到端连续对话的误差累积。

test.jsonl SHA256：`{manifest["cases_sha256"]}`
Registry版本：{manifest["registry_version"]}；SHA256：`{manifest["registry_sha256"]}`。
manifest.json记录来源与辅助产物hash；修改冻结内容必须发布新版本。

完整九步记录：[制作文档](../../../docs/baking-frozen-eval-v1/README.md)。
"""
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish", action="store_true", help="Publish only if all outputs are absent"
    )
    args = parser.parse_args()
    files, manifest = make_artifacts()
    if not args.publish:
        print(
            dump(
                {
                    "mode": "dry-run",
                    "sample_count": 200,
                    "cases_sha256": manifest["cases_sha256"],
                    "outputs": [str(p) for p in files],
                }
            )
        )
        return
    existing = [str(p) for p in files if p.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite frozen artifacts: {existing}")
    registry_path = Path("data/dataset-registry.yaml")
    original = registry_path.read_text(encoding="utf-8")
    registry = yaml.safe_load(original)
    entry = next(e for e in registry["datasets"] if e["dataset_id"] == "baking-eval-v1.0")
    if entry["status"] != "planned":
        raise ValueError("evaluation registry entry must be planned before publication")
    start = original.index("  - dataset_id: baking-eval-v1.0")
    next_entry = original.find("\n  - dataset_id:", start + 1)
    end = next_entry if next_entry >= 0 else original.find("\n#", start)
    if end < 0:
        end = len(original)
    updated = original[start:end].replace("status: planned", "status: frozen", 1)
    updated = updated.replace(
        "    first_used_in: null",
        "    first_used_in: null\n"
        f"    frozen_date: '{DATE}'\n    sha256: {manifest['cases_sha256']}\n"
        "    sha256_file: data/eval/baking-v1.0/test.sha256\n"
        "    manifest: data/eval/baking-v1.0/manifest.json\n"
        "    review_status: ai_reviewed_pending_independent_human_review\n"
        "    baseline_status: not_run_per_user_request",
    )
    updated = updated.replace(
        "独立烘焙评估集预留；必须在正式训练语料生成前设计、审核并冻结。",
        "200条独立合成烘焙评估样本；版本已冻结，AI复核通过，独立人工审核待完成；未运行基线，禁止训练使用。",
    )
    updated_registry = original[:start] + updated + original[end:]
    # Validate the updated document before publishing any artifact.
    yaml.safe_load(updated_registry)
    for path, content in files.items():
        write(path, content)
    write(registry_path, updated_registry)
    print(f"Published {len(files)} artifacts; 200 cases; sha256={manifest['cases_sha256']}")


if __name__ == "__main__":
    main()
