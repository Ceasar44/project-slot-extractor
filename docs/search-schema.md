# SearchPatch 和 SearchState v1.0

Task 02 建立搜索协议的数据结构和校验边界。业务字段、取值、合法操作符、排序及可清除字段均读取 Task 01 的 Registry，不维护第二套业务枚举。

```python
import json
from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.schemas.output import parse_model_json, validate_search_patch_output
from slot_extractor.schemas.search_patch import SearchPatch
from slot_extractor.schemas.search_state import empty_search_state, validate_search_state

registry = load_registry(Path("configs/catalog/registry.yaml"))
model_text = json.dumps(SearchPatch().to_dict())
patch = validate_search_patch_output(parse_model_json(model_text), registry)
state = validate_search_state(empty_search_state().to_dict(), registry)
```

校验入口接收解码后的 JSON 对象，返回不可变的类型对象；`from_dict(data, registry)` 使用相同校验。`to_dict()` 返回完整固定字段形状及 JSON 数组，每次调用都新建容器。直接调用数据类构造器用于内部代码，外部输入必须经过校验入口。所有协议错误统一为 `SearchPatchValidationError`，`OutputValidationError` 是该异常的别名。

SearchPatch 必须包含版本、reset、query_text、hard_filters、soft_preferences、sort、clear_fields 和 unmapped_terms 八个字段。SearchState 只包含 query_text、hard_filters、soft_preferences 和 sort，拒绝 Patch 命令及版本字段。单轮输入中的 `current_search_state=null` 由后续 Sample 合同处理，`validate_search_state()` 本身要求完整状态对象。

硬条件使用 `op`，软偏好使用 `preference`；其余固定子字段均为 field、value、values、min_value、max_value、unit。分类操作要求非空且去重的 canonical values；单值操作只使用 value；between 只使用上下界且下界不大于上界；lower/higher 保持空数值载荷，不为“低一点”猜测阈值。整数必须使用 JSON 整数，布尔值不得替代数值。数值必须有限并满足 Registry 范围。

有数值或范围的重量条件必须提供 Registry 中定义的单位，相对 lower/higher 可省略单位。货币可为 null，显式币种按 Registry 的格式校验；本任务不填默认币种、不换算重量、不展开过敏原层级。query_text 限制为非空文本或 null，最长 128 字符；unmapped_terms 最多 5 项，每项 1–64 字符且去重。clear_fields 必须来自 Registry 并且去重。

该层校验结构及字段合同，不执行状态合并或判断用户语义。同字段多条条件、同字段硬软条件及 clear 后重新设置的处理，由后续 Search Runtime 负责。JSON 解析拒绝 Markdown 围栏、额外文本、非对象根、重复键和非有限数值，不使用别名自动修复模型输出。

`CaseResult` 保存原始 model_output 和类型化的 output（SearchPatch）；无有效结果时 output 为 None，并可携带 scenario。新结果对象不含 final/tool_call 或对话类型字段。

迁移兼容：旧预约校验移入 `schemas/legacy_output.py`，旧报告对象改名为 `LegacyCaseResult`。尚未迁移的数据、评估和工具流程显式使用兼容接口；新 `schemas/output.py` 不导出旧字段常量及旧校验函数。兼容接口会随后续任务替换，保留独立旧合同测试以验证现有流程。

验证：`python -m pytest tests/unit/test_output_schema.py tests/unit/test_search_state.py`。
