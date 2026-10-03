# 烘焙搜索双模型对比

Task 10 新增 search_compare 应用，以 Task 11 的烘焙模型 Registry 为默认入口。两侧各执行一次模型推理，依次展示原始输出、Parsed SearchPatch、Validator 结果、合并状态与字段 diff、编译后的查询及延迟/token 指标。应用不请求 Typesense 或商品数据，不执行技师工具，不生成自然语言回复。

## 启动

从仓库根目录、已安装项目依赖的 Python 环境运行：

```powershell
python -m uvicorn slot_extractor.search_compare.app:create_app --factory --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000。选择左右模型并分别加载，模型就绪后输入搜索需求。默认选 0.6B 和 1.7B 的 Q4_K_M，F16 anchor 也可手动选择。没有正式 GGUF 或可信 Manifest 时模型仍显示，但不能选择和加载；这不影响用注入后端执行离线测试。

配置默认读取 configs/catalog/registry.yaml 和 configs/quantization/baking_search_v1.yaml。价格编译使用 USD，可通过 create_app 的 currency 参数指定索引币种；不同显式币种会编译失败，不自动换汇。独立的左右 llama-server 端口为 18090/18091，避免连接到历史预约或 Task 11 的评估服务器。推理沿用 SearchPatch Prompt、关闭 thinking，输出预算 2048 tokens，超时 180 秒。

模型驻留在各自槽位，同一侧重复加载同一模型直接复用；切换、卸载或应用正常退出时结束旧服务器。启动失败会停止已启动的子进程。Manifest 验证须匹配所选 model ID、artifact kind 和实际 GGUF，且 hash 正确。可用性缓存按 Manifest 与 GGUF 的时间/大小签名刷新，支持打开页面后模型产物才完成的情况。

## 多轮状态

浏览器每侧独立保存当前 SearchState，下一轮只发送该状态和本轮原话。完整历史和前几轮模型回复不会再次进入 Prompt。服务端无会话存储，刷新页面会清空当前状态；导出 JSON 保存所有本次页面内的请求和事件。

只有 Patch 校验、状态合并和查询编译全部成功，浏览器才采用返回的 next_state。JSON/Schema/冲突错误不会合并状态；编译错误可显示候选 merged_state 和 diff，但 next_state 仍是旧状态。两侧独立处理，一侧失败不会阻止另一侧完成。PASS 代表协议与条件校验通过，不代表自然语言语义已正确提取；模型质量仍应以审核后的 Frozen Eval 为依据。

展开“当前搜索状态”可编辑完整状态 JSON。清空两侧状态使下一轮从 null 开始；“右侧使用左侧状态”可恢复一致的输入条件。切换所选模型会清空该侧状态，避免把旧模型的上下文隐式沿用。清空状态不删除已经记录的导出历史，也不卸载驻留模型。

顺序模式依次执行左右模型，推理耗时仅计 backend.generate 调用，不包含加载、Prompt 构建、校验和编译。并行模式使用两个工作线程实际并发，所有事件标记 comparable=false；CPU 等资源竞争使其时延不适合直接比较。不同 compare 请求及加载/卸载操作通过统一锁串行，防止请求进行中切换同一模型槽位。数据是本次实验观测，不代替正式性能基准。

## API

| 路由 | 用途 |
| --- | --- |
| GET /api/models | 列出模型及可用性、不可用原因 |
| GET /api/registry | 搜索字段合同、版本、索引币种和后端模式 |
| POST /api/model-slots/{left,right}/load | 加载 {model_id} |
| POST /api/model-slots/{left,right}/unload | 卸载该侧服务器 |
| POST /api/compare | NDJSON 搜索比较流 |
| POST /api/client-logs | 本地客户端错误诊断 |

CompareRequest 示例：

```json
{
  "left_model_id": "baking-search-qwen3-0.6b-sft-v1-q4-k-m",
  "right_model_id": "baking-search-qwen3-1.7b-sft-v1-q4-k-m",
  "mode": "sequential",
  "user_input": "做可颂夹心，最好开心果味，不要太甜，20美元以内",
  "current_search_state": null
}
```

需要独立状态时传 left_current_search_state/right_current_search_state；未提供的一侧继承 current_search_state，显式 null 表示该侧从空状态开始。用户原话不能为空白且最长 512 字符，状态必须通过 Registry-aware 校验。请求拒绝未知属性，因此旧 left_history/right_history 不会被误当作搜索上下文。

输入错误在推理前返回 422，未知模型/槽位返回 404，缺失产物返回 409，显式加载失败返回 503。已经开始的比较使用流内错误表示某侧失败，HTTP 200 本身不表示两侧成功。

每行事件含 request_id、side、seq、type、payload、comparable。事件类型依次为 side_status、search_patch_generated、search_patch_parsed、search_patch_validated、search_state_merged、search_query_compiled、search_metrics；错误处出现 search_error。每侧最终返回 side_result，含状态、错误阶段和完整 ModelSideResult。不可解析输出仍保留原始文本，界面以 textContent 呈现，不执行模型返回的 HTML。NDJSON 非有限指标写为 null。

JSON 导出含各轮原始请求、当时的左右状态及完整事件；NDJSON 导出所有带 request_id 的事件。导出和前端交互在一轮运行期间锁定，避免记录未完成的结果。页面仅展示当前一轮 trace，多轮记录保留在导出中。

## 诊断与历史兼容

默认 JSONL 日志位于 reports/generated/search-compare/app.jsonl，左右服务器日志在同目录。复用原有 DiagnosticLog 的线程安全和轮转能力，事件改为 search_patch_generated/validated、search_state_merged、search_query_compiled 等，包含 request ID 和侧别。日志包含本地实验输入和输出。

旧 tool_loop、find_technicians、Fixture 和 Phase 05/06 比较入口保留为显式历史接口，历史脚本与测试继续使用；新 search_compare 主路径不导入预约 Prompt、技师 Fixture 或工具执行器。README 的默认比较命令已切换到新应用。全面归档与旧测试 marker 整理仍属于 Task 12。

## 验证

```powershell
python -m pytest tests/unit/test_search_compare_orchestrator.py tests/integration/test_search_compare_app.py
python -m pytest
```

测试覆盖完整搜索 trace、多轮继承/清除/重置、单位保留与编译换算、非法 JSON/枚举与币种错误、左右状态隔离、同模型复用、模型可用性刷新、实际并行与跨请求串行、加载失败、诊断日志及 NDJSON。浏览器验证使用明确标记的离线注入后端，检查页面渲染、替换与失败回滚、JSON 导出、重置、卸载和移动端横向溢出。未运行真实烘焙模型；正式 GGUF 尚待训练和量化。

2026-10-03 验证：Python 3.11 全量回归 1,027 项通过，1 项 local_backend 按默认配置排除；Task 10 新增 28 项测试。相关 Python 文件 Ruff 与 Git 空白检查通过，前端 JavaScript 语法检查通过。使用独立临时 Chromium 配置完成上述浏览器交互检查，并检查 1440px 桌面及 390px 移动端截图。测试复用本机既有依赖；尚未在真实 baking GGUF 或完整训练环境下验证。
