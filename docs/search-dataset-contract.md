# SearchPatch 原始样本与数据合同

Task 05 将新业务的 `Sample`、`RawSample` 和 Dataset Contract 改为烘焙风味酱搜索格式。Raw Gold 固定包含 `id`、`scenario`、`tags`、`input`、`expected`、`assertions` 六个字段；输入固定为 `current_search_state` 和 `user_input`。旧预约字段不被新入口接受。

```python
from pathlib import Path

from slot_extractor.registry import load_registry
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.raw_schema import raw_response_schema
from slot_extractor.data.raw_validator import validate_raw_sample
from slot_extractor.prompts.template import PromptBuilder

registry = load_registry(Path("configs/catalog/registry.yaml"))
schema = raw_response_schema(registry)
sample = raw_sample_from_record(record, registry)  # record 为解析后的 Raw JSON
validate_raw_sample(sample, registry)
messages = PromptBuilder(registry).build_messages(sample)
```

所有新入口显式接收 Registry。`load_dataset_contract(path)` 直接加载 catalog YAML，返回 Registry，不再读取复制业务枚举的 dataset contract JSON。字段、取值、操作符、范围、单位、排序和可清除字段均从 Registry 派生。修改 Registry 后重新生成 Schema 即可；Schema 每次调用返回独立对象。

`raw_response_schema(registry)` 返回 Draft 2020-12 JSON Schema，所有对象关闭额外字段并要求固定字段齐全。按字段和操作符生成 condition 分支：集合操作符只使用 `values`，比较操作符只使用 `value`，`between` 使用两个边界，`lower/higher` 使用空载荷。模型保留原始单位，不执行 oz/kg 到 g 的转换。

Python Contract 在结构检查后复用 Task 03 的 patch、state 和合并校验，检查冲突条件、场景与 Gold 的对应关系、clear/set 冲突、reset 后冗余 clear，以及 unmapped 片段是否出现在用户原话中。JSON Schema 无法比较 min/max、检查跨条件冲突或判断状态转换；入库必须同时执行 Python 校验。

`tags` 为 1–16 个非空、去重字符串；`user_input` 为 1–512 字符，保持原话。ID 要求非空；规范中的 `train/val/eval-六位数字` 是推荐命名，暂不作为强制正则。数据集级校验拒绝重复 ID。解析及 `to_dict()` 使用深复制，避免调用方修改原记录或导出结果时污染样本。

Task 05 初始采用 Raw 规范的 14 类场景。Task 06 按迁移计划明确列出的配额表补入 relative_numeric，现为 15 类：single_filter、multi_filter、hard_soft_mix、negation、allergy_vs_flavor、replace、clear、preserve_state、numeric_price、numeric_size、relative_numeric、sort、query_text、unmapped、reset。relative_numeric 必须含 lower/higher/around 软偏好；ScenarioSpec 与 JSON Schema 共用此代码集合。

Assertions 固定为 `{type, field}` 对象，接受规范列出的 16 个类型。`field_exact/replaced/preserved/cleared` 必须提供模型字段或 query_text/sort；`operator_correct/value_normalized` 必须提供模型过滤字段；其余类型支持 null 或合法字段。校验器检查参数合法性、重复 assertion，以及 Gold 是否支持替换、保留、清除和字段提取断言。存在 `minimal_patch` 断言时，也拒绝重复写入未变化的旧字段；没有该断言时允许用户明确重申条件。

本任务只检查可确定验证的 Gold 自洽关系。硬软强度、食品安全语义、是否幻觉过滤及全文词是否适合用户原话，仍需 Gold 审核和 Task 08 的语义评分；合法结构不能证明模型正确理解用户。

旧预约实现保存于 `legacy_sample.py`、`legacy_dataset_contract.py`、`legacy_raw_sample.py`、`legacy_raw_schema.py`、`legacy_raw_validator.py`。旧 DPO 和历史实验显式导入这些模块；新入口不自动回退。Task 06 提供独立搜索 Raw 生成入口；Task 07 已迁移默认 SFT Renderer、Dataset Builder 和 build_dataset CLI；Task 08 已迁移默认评估与参数化断言，详情见 [search-evaluation.md](search-evaluation.md)。旧构建/评估入口为 build_legacy_dataset、run_legacy_eval，兼容测试独立保留。

新增标准 Schema 验证测试依赖 `jsonschema`，位于 dev dependency group。验证命令：

```powershell
uv run --group dev pytest tests/unit/test_dataset_contract.py tests/unit/test_raw_sample.py tests/unit/test_raw_schema.py tests/unit/test_raw_validator.py
uv run --group dev pytest
```

本次验证结果：Task 05 新测试 177 项通过；全量回归在现有 Python 3.11 测试环境中 825 项通过、1 项 local_backend 测试按配置排除；符合项目版本要求的 Python 3.13 环境中，Task 01–05 共 535 项通过。相关改动文件 Ruff 检查、Git diff 空白检查及 `uv lock --check --offline` 通过。全仓 Ruff 仍有原有 `tool_loop/find_technicians.py:55` 的未使用变量告警，该文件未在本任务中修改。
