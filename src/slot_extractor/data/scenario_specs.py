"""Search generation instructions sharing the raw contract vocabulary."""

from dataclasses import dataclass

from slot_extractor.schemas.dataset_contract import SCENARIO_CODES


@dataclass(frozen=True)
class ScenarioSpec:
    instruction: str
    example: str
    multi_turn: bool = False


SCENARIOS = {
    "single_filter": ScenarioSpec(
        "单轮仅提取一个条件，覆盖不同字段及中英文别名，不附加常识条件。", "想要开心果味的"
    ),
    "multi_filter": ScenarioSpec(
        "单轮至少两个硬条件，区分制作对象、使用方式与商品形态。", "可颂夹心用，20美元以内"
    ),
    "hard_soft_mix": ScenarioSpec(
        "同时包含硬条件与软偏好，强度忠实原话；模糊甜度不硬量化。",
        "做可颂夹馅，20美元以内，最好开心果，不要太甜",
    ),
    "negation": ScenarioSpec(
        "覆盖硬排除 not_in 与软回避 avoid，不将普通口味排除猜成过敏。", "不要花生味"
    ),
    "allergy_vs_flavor": ScenarioSpec(
        "交替生成过敏安全限制与普通风味排除；allergen 只用硬条件。"
        "不要花生味只排除 flavor；花生过敏只排除 allergen，不展开父子关系。",
        "花生过敏，但想要巧克力味",
    ),
    "replace": ScenarioSpec(
        "提供有旧条件的状态，新意图整体替换同字段旧 hard/soft；只写修改字段。",
        "口味改成抹茶优先，预算提高到30美元",
        True,
    ),
    "clear": ScenarioSpec(
        "提供有旧条件的状态；明确取消限制使用 clear_fields，不把换口味当清除。",
        "价格不限了，排序也不用了",
        True,
    ),
    "preserve_state": ScenarioSpec(
        "提供至少两个已有字段，仅修改其中一项；未修改字段只存在于状态，不重复进 Patch。",
        "其他不变，口味换成抹茶",
        True,
    ),
    "numeric_price": ScenarioSpec(
        "覆盖 eq/gte/lte/between、零价格、显式币种及省略币种；不猜币种，不换汇。",
        "预算在15到25美元之间",
    ),
    "numeric_size": ScenarioSpec("覆盖 g/kg/oz 及比较符；保留原单位，不换算成克。", "至少1公斤装"),
    "relative_numeric": ScenarioSpec(
        "覆盖 lower/higher/around 软偏好；不要太甜不猜阈值，价格低一点不猜预算。",
        "风味浓一点，不要太甜，8oz左右",
    ),
    "sort": ScenarioSpec(
        "只提取明确排序，字段和方向从 Registry 选择；高端一点不能猜成价格降序。",
        "按价格从低到高排列",
    ),
    "query_text": ScenarioSpec(
        "保留不能结构化但适合商品全文检索的词；结构化词不重复进 query_text。",
        "找 Dubai Chocolate 风格的",
    ),
    "unmapped": ScenarioSpec(
        "无法安全映射的需求原文进入 unmapped_terms；不猜字段、取值、过滤或排序。",
        "开心果味的，整体高级一点",
    ),
    "reset": ScenarioSpec(
        "提供已有状态，用户明确从头搜索；reset=true，丢弃旧状态后只提取新需求。",
        "前面的都不要了，重新找草莓味的",
        True,
    ),
}

if set(SCENARIOS) != set(SCENARIO_CODES):
    raise RuntimeError("generation scenarios differ from the raw contract")
