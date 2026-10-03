# 烘焙搜索 SFT 数据构建

Task 07 接通 Raw Gold → SFT → 版本化产物。默认 Renderer、Dataset Builder 和 `slot-build-dataset` CLI 均使用搜索合同；旧预约构建器移至显式 legacy 入口，历史数据保持原样。

## 构建入口

先检查配置，不调用模型或生成文件：

```powershell
python -m scripts.data.build_dataset --config configs/data/baking_search_v1.yaml --dry-run
```

使用已经生成并审核的 Raw Gold 构建：

```powershell
python -m scripts.data.build_dataset --config configs/data/baking_search_v1.yaml --raw-input data/raw/baking-v1.0/samples.jsonl --strict-audit
```

需要生成时，CLI 接入 Task 06 的并发/重试/checkpoint 流程，再执行相同构建：

```powershell
python -m scripts.data.build_dataset --config configs/data/baking_search_v1.yaml --generate --strict-audit
```

正式生成前必须提供独立、非空且符合搜索 Raw 合同的 `data/eval/baking-v1.0/test.jsonl`。不能使用旧预约评估集。若生成已完成而构建未完成，使用 `--raw-input` 接续构建；生成入口不会覆盖已发布 Raw。`--mock` 使用配置中显式指定的 mock_inference_config，必须按 Sample ID 提供搜索 Raw 响应；默认正式配置没有内置 mock 语料，测试使用 stub/mock 后端离线验证。

新 CLI 必须明确选择 raw-input/generate/mock，避免默认触发生成。已有预约配置用以下兼容入口：

```powershell
python -m scripts.data.build_legacy_dataset --config configs/data/phase03.yaml --mock --output-root .tmp/legacy-smoke
```

## SFT 合同

每条 ShareGPT 行只有 system 和 conversations；conversations 固定为 human 本轮原话与 gpt 标准 SearchPatch。System 使用 Task 04 PromptBuilder，含精简 Registry、提取规则及 current_search_state。scenario/tags/assertions/id 不进入模型消息；tools/function_call/observation 均不生成。

Assistant 保存本轮最小 Patch，未修改字段只出现在当前状态中。用户原单位与币种保留，不在 Renderer 中换算。Gold JSON 使用紧凑、键排序的确定性序列化；这不改变原始样本。所有外部样本先通过 Task 05 合同校验。

## 分层与隔离

切分按 scenario 和从输入推导的单/多轮类型分层，默认验证比例 10%。每个至少两条样本的层保留至少一条训练样本及一条验证样本；单样本层全部留在训练集。比例与层覆盖不能同时满足时优先保持层覆盖，Manifest 记录实际数量。固定 seed，先按 ID 排序再分层洗牌，因此不受输入遍历顺序影响。Manifest 分别记录训练/验证的 ID、场景和标签分布，用于检查字段与能力覆盖。

构建拒绝重复 ID、重复原话指纹、训练与评估的 ID/输入交集，验证集也执行输入隔离。指纹继承 Task 06 的保守规则：搜索样本即使状态不同，同一归一化用户话术也不能跨集合或重复入库；近义改写需要审核。冻结评估不参与切分、训练或 SFT 导出。

`--strict-audit` 同时检查 Gold 派生标签与 Task 06 语义覆盖。结构检查、隔离或审计失败不会发布构建产物。手工审核的 Raw 未采用规范标签时可先检查 coverage 报告并修订，再严格构建。

## 产物与版本

| 产物 | 路径 |
|---|---|
| 权威 Raw 快照 | data/raw/baking-v1.0/samples.jsonl |
| SFT train/val | data/processed/sft/baking-v1.0/train.jsonl 和 val.jsonl |
| LLaMA-Factory 注册 | data/processed/baking-v1.0/dataset_info.json |
| 构建 Manifest | data/processed/baking-v1.0/manifest.json |
| 覆盖与说明 | 同目录 coverage.json 和 DATASET_CARD.md |

dataset_info 注册 baking_v1_0_train 和 baking_v1_0_val，采用 ShareGPT，只映射 messages/system 与 human/gpt 标签，引用文件相对 dataset_info 目录定位。没有 tools 列或 DPO 注册项。

Manifest 记录 Registry 版本和原始 YAML SHA256、评估 hash、Raw/train/val 文件 hash、seed、实际切分、Renderer/Prompt 来源 hash，以及原 Raw Manifest。Registry、原始文件、样本数、dataset_id 或评估 hash 与 Raw 来源不符时拒绝构建。已有权威 Raw 仅核对，不重写其文件和 Manifest；从外部输入构建时保存同内容的快照。

搜索版本必须使用 baking-vX.Y 或 baking-vX.Y.Z，避免复用旧预约 v0.x 路径。已存在 processed 元数据、SFT 或 DPO 同版本目录时拒绝覆盖；文件写入使用临时文件替换，Manifest 最后写入表示构建完成。文件系统写入失败若留下部分输出，应检查后使用新版本目录重建；不自动删除已有数据。一个版本目录同时只运行一个构建进程。

配置 enable_dpo 默认 false。当前 true、非布尔值或非空 dpo_target_counts 会失败，搜索 DPO 留给 Task 09，不调用旧预约扰动。data/dataset-registry.yaml 已追加 baking raw/sft/eval v1.0 的 planned 条目；它们不表示正式语料已生成或评估已冻结。

旧 SFT/Builder/工具 Schema 分别在 legacy_sft_render、legacy_dataset_build、legacy_tool_schema。历史 Phase 06 和旧 DPO 显式导入这些模块，默认搜索入口不做自动业务回退。

## 验证

测试覆盖单/多轮 SFT、最小 Patch、工具角色拒绝、确定性分层、单样本层、Gold 不变、来源漂移、DPO 禁用、版本保护、评估隔离，以及 raw-input 和 generate/mock → build 的完整链路。集成测试离线调用真实 CLI，历史预约测试保留为 test_legacy_*。

```powershell
python -m pytest tests/unit/test_sft_render.py tests/unit/test_dataset_build.py tests/unit/test_build_dataset_cli.py tests/integration/test_pipeline_phase03.py
python -m pytest
```

2026-10-03 验证结果：Python 3.11 全量 932 项通过，1 项 local_backend 按项目配置排除；Python 3.13 下 Task 07 新增 40 项测试通过，包含真实 CLI 子进程集成测试。Task 07 涉及文件的 Ruff 和 Git diff 空白检查通过；正式配置 dry-run 输出 1,820 条、enable_dpo=false。验证使用离线后端，未调用付费模型或生成正式训练语料。

本机 Python 3.11 复用 `.tmp/task06-deps` 中的项目测试依赖；Python 3.13 复用现有纯 Python 测试依赖，并在测试进程内适配 Windows sandbox 临时目录权限。上述环境适配不进入生产代码。
