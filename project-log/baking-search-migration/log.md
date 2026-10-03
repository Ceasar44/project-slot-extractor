# 烘焙搜索迁移日志

## 2026-10-03 / Task 12

完成搜索主线代码审查、默认数据校验与服务器 smoke 迁移、历史测试 legacy 隔离、共用诊断日志解耦、搜索量化入口和 README / 目录文档重写。
修复量化 base revision 缓存失败后选用其他快照的问题，保留历史脚本、技师 fixture、模型和报告的路径。

验证：搜索主线 780 passed / 1 local_backend deselected；历史预约 256 passed；Task 12 与隔离测试 Python 3.13 下 11 passed。Ruff、空白与文档链接检查通过，搜索和历史数据校验、构建 dry-run 通过。

范围：代码与文档收尾完成；baking Raw / SFT / Eval 注册仍为 planned，真实模型质量验收尚未进行，Task 09 Search DPO 暂缓。
后续先设计审核并冻结 baking Eval，再生成审核 Raw、构建 SFT、训练量化两模型，执行同一 Frozen Eval 的多维验收。

完整审查发现、修复、历史归档清单与验收状态见 [迁移记录](../../docs/search-migration-notes.md)。
