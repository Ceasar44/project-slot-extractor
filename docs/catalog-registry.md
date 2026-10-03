# 烘焙风味酱 Registry

Task 01 新增独立的搜索域定义，不改变现有预约训练和推理流程。业务字段和取值的唯一来源是 `configs/catalog/registry.yaml`，依据迁移计划及 Raw Dataset Spec v1.0 第 5 节建立。

```python
from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.registry.derived import derive_model_registry, derive_value_enums

registry = load_registry(Path("configs/catalog/registry.yaml"))
prompt_contract = derive_model_registry(registry)
value_enums = derive_value_enums(registry)
```

`Registry` 及其嵌套对象不可变。`field()`、`allowed_values()`、`hard_operators()`、`soft_operators()` 对未知字段抛出 `RegistryError`。`model_extractable_fields()` 返回可抽取字段名；`clearable_fields()` 从配置派生并加入协议字段 `query_text` 和 `sort`。派生结果是新建的 JSON 可序列化对象，修改结果不会污染 Registry。

分类取值必须有 `code`、`label`、`aliases`。规范代码自动参与精确别名解析；别名去除首尾空白并忽略大小写，冲突仅在同一字段内检查。`resolve_alias()` 只用于数据生成、工具和测试，不应用来猜测或修复模型输出。

`parent_field` 指定跨字段父级，未指定时取值的 `parent` 指向同字段取值。加载时拒绝不存在的父级及循环关系；过敏原展开在后续 QueryCompiler 中实现。单位转换系数保留在 Registry，Prompt 派生结果仅包含单位名称，不包含系数和索引元数据。

货币采用三位大写代码格式，不维护币种白名单，不在本任务进行汇率换算。除规范明确指定的净含量索引外，字段同名索引和 `newest → published_at` 是初始搜索集成约定；接入实际商品索引时在 YAML 中统一调整。

新增取值只需更新 YAML，值枚举、别名解析和 Prompt 摘要会自动更新。新增业务字段须提供完整配置；加载器不写死字段数量，以支持后续扩展。协议支持的类型和操作符语法在加载器中检查。

验证：`python -m pytest tests/unit/registry`（使用项目环境或设置 `PYTHONPATH=src`）。
