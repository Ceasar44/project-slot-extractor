# Baking Frozen Eval v1.0

冻结日期：2026-10-06；200条合成评估样本；15类场景；14个可抽取字段。
用途：烘焙搜索SearchPatch抽取及一次状态转换的能力评估，禁止训练使用。

来源：Codex逐项编写固定样本和Gold，无生成API调用，无真实客户日志。
审核：AI作者/复核，自洽校验通过；独立人工审核待完成。frozen仅表示内容版本固定。
基线：按用户要求暂不运行；没有真实模型效果或性能结论。

样本固定六字段；当前状态+本轮原话为输入；expected为最小Patch；单轮为null状态。
场景与派生tags、断言适用性均符合当前Registry及严格数据合同。

| 场景 | 计划 | 实际 |
|---|---:|---:|
| single_filter | 20 | 20 |
| multi_filter | 15 | 15 |
| hard_soft_mix | 20 | 20 |
| negation | 10 | 10 |
| allergy_vs_flavor | 25 | 25 |
| replace | 15 | 15 |
| clear | 10 | 10 |
| preserve_state | 15 | 15 |
| numeric_price | 15 | 15 |
| numeric_size | 10 | 10 |
| relative_numeric | 10 | 10 |
| sort | 5 | 5 |
| query_text | 5 | 5 |
| unmapped | 10 | 10 |
| reset | 15 | 15 |


校验：合同/ID/归一化原话、场景配额、语义覆盖、标签及Gold断言回放全部通过。
Gold回放并非模型评估；独立语义审核仍需人工确认。
已扫描历史Raw/SFT JSONL，未发现相同归一化输入；近义改写和未来训练集仍须复核。

局限：中文为主，人工配额分布不代表真实流量；全文词为明示检索指令，未穷尽自然表达；
未穷尽枚举/操作符/组合、歧义及矛盾输入、非USD币种、极长表达；
相近对照样本有关联，不能宣称独立随机样本置信区间；不评估真实检索或食品安全认证。
多轮采用给定前态逐轮测试，不覆盖端到端连续对话的误差累积。

test.jsonl SHA256：`60ccf3ef02909f435d82c6a9c49b8079665abe5d0b8810e4dac2dd5eef72d0db`
Registry版本：1.0；SHA256：`8aae1bd74a811697eef13344af36545959bc0d18149bbc549519e7532c178304`。
manifest.json记录来源与辅助产物hash；修改冻结内容必须发布新版本。

完整九步记录：[制作文档](../../../docs/baking-frozen-eval-v1/README.md)。
