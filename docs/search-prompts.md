# SearchPatch Prompt

Task 04 将新的 Prompt 入口改为烘焙风味酱搜索意图抽取。输入只包含当前搜索状态及本轮用户话术，输出目标为本轮最小 SearchPatch。

```python
from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.prompts.template import PromptBuilder

registry = load_registry(Path("configs/catalog/registry.yaml"))
builder = PromptBuilder(registry)
messages = builder.build_messages({
    "current_search_state": None,
    "user_input": "做可颂夹心，最好开心果味，不要太甜，20美元以内",
})
```

`PromptBuilder(registry)` 必须显式传入 Registry。`build_messages()` 支持直接传入搜索 input 字典、含 input 的 Raw 记录，或具有 input 属性的样本对象，供后续 Sample 改造接入。必须同时提供 current_search_state 和 user_input；单轮状态为 null，多轮状态可传 SearchState 或完整状态字典。输入话术保持原文，非空且最多 512 字符；状态使用 Task 02 Schema 校验。

消息固定为 system 和 user 两条，各自只包含 role、content。system 包含搜索规则、Schema 派生的空 Patch 形状、精简 Registry 和当前状态；user 只包含本轮原话。id、scenario、tags、assertions、expected 及旧 history、current_time、available_tools、current_state 均不复制进消息。模型无需读取完整对话历史；上游负责维护合并后的状态。

`render_registry_summary()` 从 Task 01 的模型合同派生：保留字段描述、类型、操作符、范围、单位、取值和别名，将取值压缩成 code 到显示名称及别名数组的映射，并去除冗余别名。排序和可清除字段同样来自 Registry；不包含索引映射、转换系数或父子展开细节。Builder 缓存固定 system 前缀，Registry 更新后须创建新 Builder。

规则明确最小 Patch、硬软强度、同字段替换、reset/clear、操作符载荷、单位保留、风味与过敏原区分、用途字段边界、全文词及 unmapped 的使用。单位归一化、状态合并和过敏原展开由 Task 03 的运行时完成。Prompt 不执行抽取或语义评分；本任务测试验证输入构建及合同一致性，模型行为需后续数据和评估任务验证。

迁移兼容：旧预约规则保存在 legacy_rules.py，旧构建器为 legacy_template.LegacyPromptBuilder。历史 SFT Renderer、预约评估和工具流程显式使用兼容接口；默认 SFT 和评估已在 Task 07、Task 08 迁移到搜索构建器，新规则和构建器不自动回退到旧业务。

验证：`python -m pytest tests/unit/test_prompt_builder.py`，并执行全量回归测试。
