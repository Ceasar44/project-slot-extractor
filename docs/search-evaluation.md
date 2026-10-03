# SearchPatch 评估（Task 08）

默认评估入口已迁移到烘焙酱搜索合同。输入为 Task 05 的六字段 Raw 样本，Gold、断言配置及重复 ID 在推理前校验；模型只收到 Task 04 构造的 system/user 消息，不收到 ID、标签、场景、Gold 或断言。默认执行 Schema、参数化断言和 Patch 指标评分，不依赖旧预约回复评分器。

## 运行

在仓库根目录运行：

```powershell
python -m scripts.eval.run_eval --backend-config <推理配置.yaml> --cases data/eval/baking-v1.0/test.jsonl --registry configs/catalog/registry.yaml --report-dir reports/generated/search
```

安装后的 `slot-eval` 和 `search-eval` 使用相同参数。采样和 token 限制沿用后端配置。Task 11 已提供两模型配置和 `--config/--model` 验收入口，见 [搜索模型配置](search-model-configs.md)。空评估集、不合法 Gold 或后端请求异常使命令失败；收到响应但 JSON/Schema 不合法作为失败样本进入分数卡。

离线 MockBackend 可用完整 user 消息内容作为 responses 的键，因此评估不需要向模型消息添加 Sample ID。历史 mock 的 Sample ID 机制仍保留；Task 06 的生成 mock 使用 ID。测试覆盖真实 CLI 与 mock 链路，不调用付费模型。

## 断言与指标

`evaluation/assertions.py` 保留 AssertionResult，接收 `{type, field}` 对象。16 类断言与 Raw 合同一致，归入 schema、field、intent、state、safety、search 六维。字段替换、保留、清空同时使用原状态、Gold 合并状态和模型合并状态，不把 reset 当作显式字段操作。query_text 和 sort 也支持字段断言。

| 分数卡指标 | 比较及分母 |
| --- | --- |
| Schema Valid | 严格 JSON 与 Registry/Patch 校验，全体样本 |
| Exact Match | 完整 Patch 规范化相等；忽略集合及条件顺序，保留单位、值、重复项和 reset 语义 |
| Field Extraction | Gold 与模型触及字段并集上的字段完整正确率，包含 clear 意图 |
| Hard/Soft | 字段、值和硬软归属一致，操作符由独立断言检查 |
| Negation | 否定条件及硬软归属一致；双方都无否定时不适用 |
| State Preserve | Gold 未触及的原有字段保持一致；Gold reset 或无应保留字段时不适用 |
| Allergen Semantics | allergen Patch 及合并状态与 Gold 一致；原状态/Gold 涉及过敏原、Gold 涉及风味或模型添加过敏原时适用 |
| Hallucination Free | 模型条件、clear、query_text、sort 是 Gold 允许的子集；遗漏由提取/精确指标检出 |
| Minimal Patch | reset 意图正确、无额外条件，且每个提交字段实际改变旧状态；clear 只能清除已有字段 |
| Assertions | 样本内断言通过率；无断言时不适用 |

食品安全、硬软强度、幻觉和全文词评分以审核后的 Gold 为依据，不用关键词猜测用户语义。因此合法结构或评分实现本身不能证明 Gold 正确。单位保持原样，1 kg 与 1000 g 不在 Patch 精确评分中视为相等；运行时归一化另行负责。

无效输出使适用的语义指标失败，但 unknown-field/value 断言仍可独立说明出错来源。无效输出不计入可信模型字段集合，Gold 触及字段计为漏提取。字段 micro precision/recall/F1 另行聚合：整个字段正确计 TP，错误字段同时计 FP 和 FN，额外字段计 FP，遗漏字段计 FN；reset 本身由 Patch 指标检查。无任何字段时 micro 指标为 n/a。

总分及 scenario/tag 切片只在适用样本上平均，同时报告适用数量；不适用不充当满分。切片名称使用 scenario:、tag: 前缀，并提供单轮/多轮标签。原始时延是描述性统计，无延迟通过门槛；非有限及负值不参加时延汇总。

## 报告和兼容

JSON 报告包含原始模型输出、合法 Patch 或校验错误、Gold、双方合并状态、逐条断言、字段计数、场景/标签切片及断言类型/维度统计。CLI 追加评估文件 SHA256、Registry 版本和 SHA256。非法数值不会产生 NaN/Infinity JSON；模型名会清理后用于报告文件名。相同模型再次写入同目录会替换报告，应使用不同目录保留实验历史。

旧预约 runner、断言、场景切片、分数卡、reply_semantics 和 scorers 已移入显式 legacy 模块。历史脚本和测试调用这些兼容接口。旧 CLI 为 `python -m scripts.eval.run_legacy_eval`；新 CLI 不自动识别或回退旧数据。

Task 08 完成评估实现及离线验证，没有生成或冻结正式 baking Frozen Eval，没有执行真实模型基线，也没有宣称模型已通过食品安全验收。正式基线需要审核并冻结评估集后运行上述命令；dataset-registry 中的 planned 状态保持原意。

2026-10-03 验证：全量回归 980 项通过，1 项需要本地 llama-server 的测试按默认配置排除；新增搜索评估 48 项在 Python 3.13 下通过。相关源码、脚本和测试 Ruff 检查通过，git diff --check 通过。Python 3.13 验证复用了本机 Python 3.11 的纯 Python 测试依赖，尚未验证完整训练依赖安装。
