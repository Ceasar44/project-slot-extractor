# Task 12：代码审查与迁移收尾

2026-10-03 完成搜索主线入口、历史测试隔离、文档与归档整理。审查依据迁移计划与当前实现；文档中的任务定义作为项目需求参考，不自动执行其提交、发布或外部操作。

## 审查范围与修复

检查 Registry / SearchPatch 合同、状态合并与编译、Raw/SFT 隔离、评分硬门槛、比较 API 状态提交及模型量化来源。
现有测试覆盖单位、层级、冲突、未知字段值、过敏与风味区分、失败状态回滚、双侧失败隔离、数据版本和来源 hash。

| 问题 | 影响 | 修复与验证 |
| --- | --- | --- |
| 通用 validate_dataset 仍导入预约合同 | 默认命令无法校验搜索数据，可能校验错业务 | 默认改为 baking Eval + Registry；新增显式 validate_legacy_dataset；测试搜索接受、预约/空/缺失/非法文件拒绝 |
| llama-server smoke 仍使用预约数据与评分 | 真实服务器集成检查未验证搜索链路 | 改用 baking smoke fixture、搜索 runner 和 baking 推理配置；同一 fixture 的 mock 集成验证 schema / allergen / exact-match |
| 指定 base revision 缓存失败后任取本地快照 | 真实模型来源可能与 Manifest revision 不一致 | 删除模糊 fallback；保持请求 revision 和 local-only；回归测试验证缓存失败直接报错 |
| 预约测试与主线混合 | 历史业务与依赖继续阻塞搜索默认回归 | 添加 legacy marker 与默认收集隔离，历史显式 opt-in |
| 搜索诊断模块从 tool_loop 导入 | 搜索运行路径仍耦合预约 app 目录 | 诊断实现移至 utils；tool_loop 保留兼容导入，API 回归覆盖共用日志 |
| README 和项目结构主要描述预约 | 默认操作指南指向旧模型与数据 | 重写主线 README / 结构，增加默认 baking 量化入口，保存历史 README |

搜索比较界面的正常路径是一轮推理后校验、合并、编译，全部成功才提交 next_state。
软偏好仅作为 ranking hints，不混入硬 filter；当前没有连接真实商品索引验证召回效果。
JSON / schema / runtime 测试不能证明自然语言 Gold 或真实模型的提取质量。

## 历史归档策略

采用原地归档，保留文件路径与既有报告引用；不删除旧模型、数据、技师 fixture 或专项脚本。
历史文件冻结为预约复现用途，搜索功能在 Registry / search / search_compare 和 baking 配置中维护。

| 历史范围 | 保留目的 | 搜索替代入口 |
| --- | --- | --- |
| schemas/prompts/data/evaluation 下 legacy_* | 预约协议、生成和评分复现 | 同目录不带 legacy 的搜索模块 |
| src/slot_extractor/tool_loop/ | 技师工具循环与旧比较界面 | search_compare/ |
| data/fixtures/technicians/ | 已用于历史报告的技师 fixture | Catalog Registry；不生成虚构技师替代数据 |
| data/eval/test.jsonl 与旧 processed/raw/DPO | 历史数据版本来源 | baking-v1.0 独立数据版本 |
| configs/quantization/phase05.yaml、旧 training/inference | 预约模型矩阵 | baking 配置 |
| scripts/data/phase06_round*.py 与 src/slot_extractor/data/phase06_*.py | 预约定向训练数据迭代 | generate_search_raw / build_dataset |
| scripts/eval/run_phase06_round*.py、Phase 04–06 评估/报告 | 预约专项迭代复现 | run_eval --config baking_search_v1.yaml |
| experiments/phase06、project-log/phase*、reports 既有产物 | 既有实验结论追溯 | 新报告独立 reports/generated/baking-search-v1 |
| docs/archive/appointment-readme.md | 旧使用说明快照 | 根 README |

共用 inference / quantization / JSONL / diagnostics 保持共享，不因历史调用方存在而归为预约专属。
真实 GGUF 构建实现仍位于 build_phase05_real，共用构建逻辑；搜索命令为 build_search，默认 baking 配置。
`slot_extractor` 包名与旧 slot-* 兼容命令保留；默认业务已切换搜索。

## 测试分类

默认 `python -m pytest` 运行新业务和共用基础设施；历史测试通过文件名显式归类，不按字符串中是否出现 technician 判断，以保留拒绝旧协议等搜索负例测试。
`test_legacy_*`、预约 Phase 04–06、回复评分与明确旧数据测试标为 legacy。
默认收集先跳过这些文件，减少历史依赖对主线的影响。
历史和全量运行分别使用以下命令：

```powershell
python -m pytest -m "legacy and not local_backend"
python -m pytest -m "not local_backend"
python -m pytest tests/integration/test_pipeline_llama_server.py -m local_backend
```

最后一条需本地烘焙服务器；该 smoke 只有开发用例，不是正式质量验收。
新增历史测试应沿用 legacy/phase 文件名规则；共享基础设施测试放在中性命名文件。

## 最终验收状态

| 门槛 | 当前状态 | 完成所需证据 |
| --- | --- | --- |
| 搜索主线 pytest | 本次运行结果见下方 | 离线主线通过 |
| 历史预约可追溯 | 原文件与历史报告保留，独立测试 | legacy 回归 |
| Frozen Eval 与 SFT 无重叠 | 构建代码和负例测试具备；正式数据待生成 | 审核后的数据、isolation 结果、实际 artifact hash |
| dataset-registry sha256 / parent | baking parent 已登记，状态 planned | 冻结后登记真实 SHA256、版本与 parent，不能虚构 |
| 未知字段/值各 0%、Allergen 100% | 硬门槛配置与拒绝测试具备；正式模型未验收 | 两模型真实 Frozen Eval 报告 |
| 两模型相同 Frozen Eval | 配置指向同一文件 | 两报告 dataset hash 相同，查看多维分数及失败样本 |
| 真实训练、量化与商品查询 | 待执行 | tokenizer 预算、训练产物、GGUF、服务器与索引联调 |
| Task 09 Search DPO | 暂缓 | SFT 基线稳定后独立立项 |

Task 12 的代码与文档收尾完成不代表上述正式数据和模型验收已通过。
下一步先审核并冻结独立 baking Eval，再生成/审核 Raw、构建 SFT、训练和量化两模型，最后执行共享 Eval 硬门槛。

## 本次验证

本次离线回归在现有 Python 3.11 环境运行：搜索主线 780 项通过，1 项 local_backend 排除；显式 legacy 回归 256 项通过。两次运行合计覆盖 1,036 项离线测试。
Task 12 新增测试与搜索数据隔离测试在 Python 3.13 下另行通过 11 项；复用现有纯 Python 测试依赖，并在测试进程内适配 Windows sandbox 临时目录权限，没有改变生产代码。
相关搜索主线与新增文件的 Ruff 检查、改动空白检查、文档相对链接检查通过。
搜索 smoke 数据校验通过（2 条），显式历史数据校验通过（51 条）；搜索 SFT 与量化 dry-run 通过。
量化 dry-run 明确显示正式校准文件与 llama.cpp 工具缺失。未执行真实 local_backend smoke、付费生成、GPU 训练或实际 GGUF 构建。
