# Search Runtime

Task 03 将 SearchPatch 校验、状态合并、单位归一化和 Typesense 查询编译接成确定性流程，不依赖模型做业务推理，也不发送网络请求。

```python
from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.schemas.search_patch import HardFilter, SearchPatch, SoftPreference
from slot_extractor.search import merge_search_state, compile_typesense_query

registry = load_registry(Path("configs/catalog/registry.yaml"))
patch = SearchPatch(
    hard_filters=(HardFilter("price", "lte", value=20),),
    soft_preferences=(SoftPreference("size", "around", value=8, unit="oz"),),
)
state = merge_search_state(None, patch, registry)
compiled = compile_typesense_query(state, registry, currency="USD")
print(compiled.to_dict())
# parameters: q="*", query_by=Registry全文字段, filter_by="price:<=20"
# ranking_hints: size around 226.796185, unit=g, index_field=size_g
```

`validate_patch()` 接收字典或类型对象，返回经过 Schema 和冲突校验的 SearchPatch。`collect_validation_errors()` 返回带 code、path、message 的错误元组，可用 `dataclasses.asdict()` 转成 API 响应。校验会收集不同顶层属性及不同条件中的错误；单条条件报告其首个错误。`SearchValidationError.errors` 保存相同的错误结果。Schema 不合法时先报告结构错误，不继续解释非法条件。

冲突检查包括数值区间交集为空、布尔条件矛盾、分类 OR 条件的全部候选被排除、不同显式币种，以及互相反向的软偏好。比较重量条件前使用 Registry 单位系数换算。同字段的多条分类 in 条件可以由多值商品同时满足，不把它们误判为单值枚举冲突。风味不推断过敏原，硬预算也可以同时保留低价软偏好。

`merge_search_state(current, patch, registry)` 的顺序是：reset 时抛弃旧状态；删除 clear_fields 指定的条件；删除本轮触及字段的旧硬条件和旧软偏好；写入本轮全部新条件。未修改字段继承。query_text/sort 为 null 表示本轮未修改，显式清除使用 clear_fields；清除后同轮重新设置时，新值生效。reset 不读取已丢弃的旧状态。`fields_touched_by_patch()` 返回受影响字段；reset 时包括 Registry 全部字段及 query_text/sort。

状态始终保存用户的原始单位。`normalize_mass()` 使用 Registry 系数，返回基础单位数值，不做任意小数位舍入。`normalize_currency_unit()` 在无上下文时保留 null，有上下文时填充索引币种；不自动改大小写、不换汇。`compile_typesense_query(..., currency=...)` 遇到任何价格条件或偏好时要求索引币种，并拒绝与之不匹配的显式币种。

`CompiledQuery.parameters` 只包含可以传给 Typesense Search API 的参数。全文词进入 q，缺省使用 `*`；query_by 从 Registry 派生。硬条件组合为 filter_by；显式排序从 Registry 映射为 sort_by。软偏好转成独立的 `ranking_hints`，保留原操作及归一化载荷，由后续搜索/重排层消费；它们不会自动变成硬筛选或覆盖用户排序。发送搜索请求时仅使用 parameters，不能把整个 to_dict() 结果当作 Typesense 参数。

同字段父子层级在编译时展开并去重，使用 Registry 顺序保持输出稳定；跨字段关系不会被猜成新的条件。树坚果包含配置中所有子孙过敏原，花生独立。编译器不因“开心果味”添加开心果过敏原条件。canonical code 和索引字段在 Registry 中限制为安全标识符，用户原文不进入 filter_by。

过滤操作符、OR 数组、AND 组合及排序参数依据 [Typesense 30.0 Search API](https://typesense.org/docs/30.0/api/search.html#filter-parameters)。尚未对接实际商品集合；索引字段、可排序字段和商品属性应与 Registry 约定一致，过敏原过滤依赖商品端已经核实的数据。

验证：`python -m pytest tests/unit/search`；另执行全量测试检查已有流程回归。
