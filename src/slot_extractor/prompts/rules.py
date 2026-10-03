"""Search intent extraction rules and a compact Registry-derived contract."""

import json

from slot_extractor.registry import Registry
from slot_extractor.registry.derived import derive_model_registry
from slot_extractor.schemas.search_patch import SearchPatch

SYSTEM_RULES = (
    "你是烘焙风味酱商品搜索参数抽取器。只输出一个 JSON 对象，不解释、不使用 Markdown。\n"
    "输出 SearchPatch v1.0，所有固定字段都必须存在，不增加字段，不省略 null 或空数组。\n"
    "根据当前搜索状态和本轮用户话术，提取本轮最小变更；不要输出合并后的完整状态。"
    "只写用户本轮明确修改的字段，未修改条件由程序继承，不重复写入 Patch。"
    "本轮出现某字段时，该字段旧硬条件和旧软偏好都会被替换；同字段的新条件要一并写全。\n"
    "只有明确重新开始搜索时 reset=true，否则为 false。明确取消条件写 clear_fields，"
    "不要用空 values、value=null 或复写旧状态代替清除。"
    "取消全文词或排序分别清除 query_text 或 sort。"
    "query_text=null 和 sort=null 表示本轮未修改，不代表清除。\n"
    "硬软强度：必须、只要、不能、预算上限等明确门槛写 hard_filters；"
    "最好、优先、尽量等偏好写 soft_preferences。合法字段、canonical code 和操作符仅来自 Registry。"
    "不要把软偏好升级为硬门槛，也不要把明确限制软化。\n"
    "每个硬条件固定包含 field、op、value、values、min_value、max_value、unit；"
    "每个软偏好固定包含 field、preference、value、values、min_value、max_value、unit。"
    "in/not_in/prefer/avoid 只填非空 values，其余数值载荷为 null；"
    "eq/gte/lte/around 只填 value，values=[]，上下界为 null；"
    "between 只填 min_value/max_value 且下界不大于上界，value=null、values=[]；"
    "lower/higher 不猜阈值，value/min_value/max_value=null、values=[]。\n"
    "不要太甜只表达 sweetness_level 的 lower 偏好，不擅自量化为等级；"
    "风味浓一点只表达 flavor_intensity 的 higher 偏好。保留重量原单位，不换算；"
    "明确说出货币才填 unit，否则为 null；无单位的分类、布尔和等级字段 unit=null。"
    "整数等级不得输出小数，布尔值使用 true/false。\n"
    "flavor 表示风味，allergen 表示明确的过敏原包含或排除要求；"
    "不要花生味排除 flavor，花生过敏或不能含花生排除 allergen。"
    "过敏原安全限制只用硬条件，不用软偏好，不由风味猜过敏原；父子展开交给程序。\n"
    "application 表示做什么产品，use_mode 表示怎么用；用途不反推 product_type 或 texture。"
    "具体 flavor 不重复输出 flavor_family。饮食声明只提取明确需求，不推断商品属性。\n"
    "query_text 只保留适合商品全文检索且无法结构化的词，已结构化词不重复放入。"
    "无法安全映射的需求片段写 unmapped_terms，不猜价格、评分或商品属性。"
    "sort 只在明确要求排序时填写 field/order，来自 Registry；不要由高端或好一点猜排序。\n"
    "query_text 非空时最多128字符；unmapped_terms 最多5项，每项1到64字符；"
    "values、clear_fields、unmapped_terms 去重。只提取用户表达，不添加常识条件。"
)


def render_search_patch_shape() -> str:
    return json.dumps(SearchPatch().to_dict(), ensure_ascii=False, separators=(",", ":"))


def render_registry_summary(registry: Registry) -> str:
    """Compact prompt view: business values are never copied into Python constants."""
    summary = derive_model_registry(registry)
    for spec in summary["fields"].values():
        if "values" in spec:
            spec["values"] = {
                value["code"]: list(
                    dict.fromkeys(
                        [
                            value["label"],
                            *(
                                alias
                                for alias in value["aliases"]
                                if alias != value["code"] and alias != value["label"]
                            ),
                        ]
                    )
                )
                for value in spec["values"]
            }
    return json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
