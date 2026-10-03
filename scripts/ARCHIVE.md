# 历史专项脚本边界

预约专属 Phase 04–06 训练、数据迭代、评估和报告脚本原地归档，用于历史复现。
尤其 `data/phase06_round*.py` 与 `eval/run_phase06_round*.py` 冻结为历史用途，不继续堆叠烘焙条件。
不要移动或删除既有路径，历史报告和测试依赖它们。

烘焙主入口：`data/generate_search_raw.py`、`data/build_dataset.py`、`eval/validate_dataset.py`、`eval/run_eval.py`、`train/check_search_data.py`、`quantize/build_search.py`。
`train/render_config.py` 和 `quantize/build_phase05_real.py` 是共用实现，搜索使用显式 baking run/config。
完整归档范围与验收状态见 `docs/search-migration-notes.md`。
