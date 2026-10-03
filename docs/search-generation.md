# 烘焙搜索 Raw Gold 生成

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

```powershell
python -m scripts.data.generate_search_raw --config configs/data/baking_search_v1.yaml --strict-audit
```

生成器发送 Registry 摘要、Raw Schema、抽取规则和场景约束，要求全局 minimal_patch 断言。校验失败时向后端反馈错误并重试，最多三次。ID 由程序按请求顺序分配为 train/val/eval 六位编号；生成模型提供的 ID 和标签不作为权威值。标签从通过合同校验的 Gold 推导，最多 16 项；复杂样本优先保留能力标签，完整字段统计由 coverage 报告提供。

生成流水线支持并发，结果按请求顺序持久化。每条完成样本写入原子 checkpoint；再次执行相同命令只生成未完成请求。恢复会重校验已有样本、ID、场景、标签、断言、多轮形态、重复输入和评估隔离，并核对配置、Registry、评估集、后端模型、Schema、规则、场景和生成实现的签名。任何身份变化都拒绝混用 checkpoint。外部请求错误直接失败，已有 checkpoint 保留。

同一用户原话的空白归一化指纹用于保守去重及评估隔离，即使状态不同也拒绝复用该话术；近义改写仍需要人工复核。已经存在的 `samples.jsonl` 不覆盖，修订数据必须使用新版本目录。一个输出目录同时只运行一个生成进程。

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
