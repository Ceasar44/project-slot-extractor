# 烘焙搜索 Raw Gold 生成

新一轮训练生成请使用 `configs/data/baking_search_v1_1.yaml`。v1.1 从 Registry 派生并冻结全部 1,820 条意图计划，程序决定当前状态、Gold 和断言，模型只创作对应原话。计划中的字段、分类值、操作符、数值范围、单位、排序与清除目标均先通过现有合同校验；不再向模型提供固定场景例句。表达风格、语言及条件顺序按配额分配，生成按场景交错排程。

先运行离线计划检查（不会访问模型，也不会修改 checkpoint）：

```powershell
$env:PYTHONPATH = "$PWD/src;$PWD"
.\.venv\Scripts\python.exe -m scripts.data.generate_search_raw --config configs/data/baking_search_v1_1.yaml --dry-run
```

独立试跑配置 `configs/data/baking_search_v1_1_pilot.yaml` 包含 42 条：14 条单条件覆盖全部字段，其余 14 类场景各 2 条。输出在 `.tmp/baking-v1.1-pilot/`，与正式计划分开。试跑只检查小规模场景可用性，字段组合门槛为 1；正式配置的门槛仍为 10，不使用试跑产物替代正式数据。以下命令会调用已配置的生成模型：

```powershell
.\.venv\Scripts\python.exe -m scripts.data.generate_search_raw --config configs/data/baking_search_v1_1_pilot.yaml --strict-audit
```

审核试跑原话与 Gold 后，再正式生成和构建：

```powershell
.\.venv\Scripts\python.exe -m scripts.data.generate_search_raw --config configs/data/baking_search_v1_1.yaml --strict-audit
.\.venv\Scripts\python.exe -m scripts.data.build_dataset --config configs/data/baking_search_v1_1.yaml --raw-input data/raw/baking-v1.1/samples.jsonl --strict-audit
```

计划模式新增 `generation_plan.jsonl`、`plan_audit.json`、最终 `diversity.json` 和 `diagnostics/`。报告统计条件组合、分类值、数值、单位、原始固定例句的联合条件频率；语言/风格统计标记为 assignments，表示程序分配，并非已确认模型实际遵守。多条件与硬软混合场景要求至少 10 种字段组合、语义唯一比例至少 80%，并按合法候选数量检查分类值集中度；排序等有限候选场景允许同 Gold 多表达。

模型改写 Gold、状态或断言时会拒绝并按同一计划重试。检查还会拦截明显缺失分类/数值/单位依据、错误否定、未表达的软偏好、遗漏清除/重置等情况；规则检查不能完整证明自然语言语义正确，manifest 始终标记需要独立复核。自由文本候选是 AI 起草，待人工审核，不是新的 Registry 枚举。

断点签名包含计划、Registry、评估集、规划器及审计实现、后端协议、推理配置和输出预算参数，不保存 Key。恢复会核对计划文件、全部已存样本及原话隔离；计划改变时拒绝混用。v1.0 的旧候选保留为诊断资料，不能通过改签名混入 v1.1。SFT 构建也会再次验证完整计划配额、计划一致性和多样性，防止通过外部 Raw 输入绕过生成验收。

Task 06 已将默认 ScenarioSpec、RawGenerator、标签审计和语义覆盖审计切换到搜索业务。新生成入口只产出 Raw Gold，不构建 SFT/DPO。Task 07 已接入 SFT Renderer、Dataset Build 和默认 build_dataset CLI，详见 search-dataset-build.md。

## 场景和配额

`configs/data/baking_search_v1.yaml` 使用迁移计划的 15 类场景，共 1,820 条。Task 05 按 Raw 规范建立的 14 类合同在本任务补入 `relative_numeric`；JSON Schema 从同一代码集合派生。该场景必须含 lower/higher/around 软偏好，不允许用硬数值代替模糊表达。

单字段场景按 Registry 顺序轮换目标字段，避免训练数据只覆盖常见风味。过敏原边界场景按请求序号交替生成 allergen 安全排除和 flavor 风味排除，并校验没有同时误加另一字段的排除。多轮场景必须提供状态；其他场景为单轮。Field/value/operator/unit 合法性仍只从 Registry 读取。

## 生成与恢复

从仓库根目录运行配额检查，不会访问模型：

```powershell
python -m scripts.data.generate_search_raw --config configs/data/baking_search_v1.yaml --dry-run
```

正式生成前，先建立并冻结 `data/eval/baking-v1.0/test.jsonl`，按新 Raw 合同保存非空评估集。不要使用旧预约评估集。配置中的推理文件指定生成后端；鉴权沿用该后端的环境配置。

当前生成配置使用 `backend: openai_chat`，调用 `/chat/completions`，不发送 `response_format` 或服务端强制 JSON Schema。提示词仍提供 Raw Schema，字符串 `minLength` 为 1；返回结果在本地执行严格 JSON、合同、文本质量及去重检查，失败时按既有上限重试。生成质量检查仍要求完整原话（至少 4 个文字/数字字符），并检查分类别名和显式数值依据；Schema 的最低长度不等于生成质量要求。该检查只拦截明显错误，不替代 Gold 语义审核。历史配置文件名 `openai_responses_gpt_5.6_sol.yaml` 保留以兼容数据配置引用，以文件内的 `backend` 和 `model` 为准。

OpenRouter 生成配置显式发送 `reasoning: {enabled: false}`，请求关闭推理以给 Raw JSON 留出预算。供应商是否执行该设置需看实际 usage。遇到 `finish_reason=length`（包括只有 reasoning 或部分正文）时，不按原预算盲目重试，而是逐步增大总输出预算，默认从 4096 到 8192，再到 `max_retry_tokens: 16384` 上限；仍截断时停止并保留 checkpoint。正常样本不增加预算，HTTP 拒绝和内容拒绝不触发预算升级。

```powershell
python -m scripts.data.generate_search_raw --config configs/data/baking_search_v1.yaml --strict-audit
```

生成器发送 Registry 摘要、Raw Schema、抽取规则和场景约束，要求全局 minimal_patch 断言。校验失败时向后端反馈错误并重试，最多三次。ID 由程序按请求顺序分配为 train/val/eval 六位编号；生成模型提供的 ID 和标签不作为权威值。标签从通过合同校验的 Gold 推导，最多 16 项；复杂样本优先保留能力标签，完整字段统计由 coverage 报告提供。

生成流水线支持并发，结果按请求顺序持久化。每条完成样本写入原子 checkpoint；再次执行相同命令只生成未完成请求。恢复会重校验已有样本、ID、场景、标签、断言、多轮形态、重复输入和评估隔离，并核对配置、Registry、评估集、后端模型、Schema、规则、场景和生成实现的签名。身份变化拒绝混用 checkpoint；本次只调整调度逻辑的更新兼容紧邻上一版实现的签名，其余合同及 hash 必须一致。外部请求错误直接失败，已有 checkpoint 保留。

单条样本校验重试耗尽或重复改写耗尽时，默认记录到 `generation_failures.json`，跳过该 ID 并继续剩余请求。全部请求处理后若仍有失败，只保留 checkpoint，不发布不满足完整配额的 `samples.jsonl`；CLI 返回退出码 2，表示本轮执行完毕但数据尚未齐全。再次执行原命令会重试全部缺失 ID，已成功样本不再调用模型。补齐后继续执行覆盖及多样性审计。`--fail-fast` 可恢复单条失败立即中断的行为；鉴权、网络等后端异常、checkpoint 损坏和文件写入失败仍直接中断。

同一用户原话的空白归一化指纹用于保守去重及评估隔离，即使状态不同也拒绝复用该话术；近义改写仍需要人工复核。新生成样本遇到训练重复或评估重叠时，自动要求模型重写用户原话及对应 Gold，保持样本 ID、场景和目标字段；默认最多重写 3 次，可通过 `max_duplicate_retries` 设置（0 表示禁用）。日志显示重写原因及次数；超限时跳过该条，保留已通过校验的 checkpoint 并继续剩余任务。恢复时发现 checkpoint 本身重复仍直接失败，不自动改写已保存样本。并发任务数量限制在 `generation_concurrency` 内，提交前串行检查去重，避免同时返回的相同输入入库。已经存在的 `samples.jsonl` 不覆盖，修订数据必须使用新版本目录。一个输出目录同时只运行一个生成进程。

产物包括 samples.jsonl、manifest.json、coverage.json 和恢复用 checkpoint。Manifest 记录 Registry 版本/原始文件 hash、评估 hash、种子、生成模型、原始数据 hash、场景数量及审核标记。种子用于固定请求顺序和提示词多样性，不保证外部模型逐字可复现。

覆盖报告统计场景、14 个 Registry 字段、hard/soft 操作符、原始单位、否定、过敏原、替换、清除和状态保持。默认要求所有场景、所有可抽取字段及关键能力至少出现一次；配置可用 coverage_minimums 覆盖门槛。`--strict-audit` 不满足门槛时保留 checkpoint 和报告，不发布最终 Raw 数据。结构合法及覆盖达标不证明自然语言 Gold 正确，正式训练前仍需审核硬软强度、安全语义和未表达条件。

## 旧流程兼容

旧生成、场景、覆盖和标签实现移至 legacy_generator、legacy_scenario_specs、legacy_coverage_audit、legacy_tag_audit。旧 fake_names 改名为 legacy_fake_names，仅旧 DPO 扰动依赖它。旧 Dataset Builder 和 build_legacy_dataset CLI 显式导入 legacy 模块，不自动识别或回退业务。旧测试保存在 test_legacy_*；原始历史数据不改写。

## 验证

新测试覆盖 15 类场景、全部 Registry 字段、过敏/风味交替、无效输出重试、严格 JSON、配额、标签、覆盖门槛、checkpoint 恢复和漂移拒绝、重复输入、评估隔离及最终数据覆盖保护。测试使用本地 stub 后端，不调用付费模型，也不生成生产训练集。

```powershell
python -m pytest tests/unit/test_generator.py tests/unit/test_scenario_specs.py tests/unit/test_tag_audit.py tests/unit/test_coverage_audit.py tests/unit/test_search_generation.py
python -m pytest
```

2026-10-03 验证结果：Python 3.11 全量回归 892 项通过，1 项 local_backend 按项目配置排除；Python 3.13 下 Task 06 新测试 65 项通过；新测试连同 Dataset Contract/Raw Schema 测试 222 项通过。Task 06 涉及文件的 Ruff 和 Git diff 空白检查通过，CLI dry-run 确认 1,820 条、15 类场景。

本机默认 Python 缺少 jsonschema；验证时将项目已声明的依赖安装至被 Git 忽略的 `.tmp/task06-deps` 并加入 PYTHONPATH，没有改变全局 Python 环境。Python 3.13 测试复用现有纯 Python 测试依赖，使用测试进程内的临时目录权限适配绕过 Windows sandbox 对 mode=0700 的限制；生产代码没有该适配。
