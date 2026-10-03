# 项目结构

主流程是 Registry → SearchPatch → SearchState → Typesense 参数；训练流程是独立 Frozen Eval → Raw 审核 → SFT train/val → 两模型训练 → GGUF → 同一 Eval 验收。

```text
configs/
  catalog/registry.yaml                 烘焙字段、值、单位、层级和索引映射
  data/baking_search_v1.yaml             场景配额与搜索数据构建
  evaluation/baking_search_v1.yaml       两模型共享 Eval 与硬门槛
  inference/baking-qwen3-*.yaml          本地搜索推理
  training/llamafactory/sft/baking-*.yaml 搜索 SFT overrides
  quantization/baking_search_v1.yaml     搜索 Q4/F16 模型注册
src/slot_extractor/
  registry/                             业务 Registry 加载、校验和派生视图
  schemas/search_patch.py                固定 Patch 协议
  schemas/search_state.py                持久化搜索状态
  schemas/{sample,dataset_contract}.py   搜索 Raw/Eval 合同
  prompts/{rules,template}.py            搜索模型输入
  search/                               校验、合并、单位归一化、查询编译
  data/                                 Raw 生成、覆盖审计、隔离与 SFT 构建
  evaluation/                           搜索断言、评分、切片与报告
  inference/                            共用模型后端和 llama-server 管理
  quantization/                         共用模型来源、hash 与产物校验
  search_compare/                        搜索比较 API 和静态界面
  utils/                                共用 JSONL 与诊断日志
scripts/
  data/generate_search_raw.py            搜索 Raw 生成入口
  data/build_dataset.py                  搜索 SFT 构建入口
  eval/validate_dataset.py               搜索数据校验入口
  eval/run_eval.py                       搜索评估入口
  train/render_config.py                 共用训练配置合并
  train/check_search_data.py             搜索 token 预算预检
  quantize/build_search.py               搜索量化入口
data/
  dataset-registry.yaml                  历史与搜索数据来源注册
  eval/baking-v1.0/                      正式评估预留路径
  raw/baking-v1.0/                       正式 Raw 预留路径
  processed/sft/baking-v1.0/              正式 SFT 预留路径
tests/
  fixtures/baking_search_smoke.jsonl      开发 smoke，不是 Frozen Eval
  conftest.py                           搜索默认收集与 legacy 标记
  unit/search/                          确定性搜索运行时测试
  integration/test_search_compare_app.py 搜索 API 测试
  integration/test_pipeline_phase03.py   搜索 Raw → SFT CLI
  integration/test_pipeline_llama_server.py 可选真实搜索服务器 smoke
docs/                                   主线协议、流程与迁移说明
docs/archive/                           历史 README 复现说明
```

预留路径不表示文件已存在。当前正式 baking 数据的状态仍为 `planned`；模型配置也不表示模型已训练。
模型业务映射由 Catalog Registry 管理；量化 ModelRegistry 管理模型 artifact 和 lineage，两者职责不同。
`configs/quantization/phase05.yaml` 仅为历史预约矩阵，搜索矩阵使用 `baking_search_v1.yaml`。

## 历史边界

`legacy_*` 模块、`tool_loop/`、Phase 04–06 专项脚本、旧模型、旧 Raw/Eval/SFT/DPO 和技师 fixture 原地保留。
它们用于复现既有报告，不作为搜索默认路径，不继续添加搜索业务条件。
默认测试跳过历史文件收集；显式 `-m "legacy and not local_backend"` 运行历史测试。
包名与共用基础设施保持兼容，归档清单及验收状态见 [迁移记录](search-migration-notes.md)。
