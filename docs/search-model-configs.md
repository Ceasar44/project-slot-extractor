# 烘焙搜索模型配置

Task 11 为 Qwen3 0.6B 和 1.7B 接通搜索 SFT、推理、评估与量化配置。数据采用 Task 07 的 baking-v1.0，Prompt 和指标复用 Task 04/08。配置可离线加载；正式训练、量化与模型验收需要先提供审核后的数据和运行环境。

## 配置与标识

| 用途 | 路径或标识 |
| --- | --- |
| SFT overrides | configs/training/llamafactory/sft/baking-qwen3-0.6b.yaml、baking-qwen3-1.7b.yaml |
| Renderer run ID | baking-qwen3-0.6b、baking-qwen3-1.7b |
| SFT 数据注册 | baking_v1_0_train、baking_v1_0_val |
| dataset_dir | data/processed/baking-v1.0 |
| adapter 目录 | models/adapters/baking-search-qwen3-{0.6,1.7}b-sft-v1 |
| 推理配置 | configs/inference/baking-qwen3-0.6b.yaml、baking-qwen3-1.7b.yaml |
| 评估配置 | configs/evaluation/baking_search_v1.yaml |
| 量化 Registry | configs/quantization/baking_search_v1.yaml |
| Q4 模型 ID | baking-search-qwen3-{0.6,1.7}b-sft-v1-q4-k-m |
| F16 模型 ID | baking-search-qwen3-{0.6,1.7}b-sft-v1-f16 |

从仓库根目录执行下面命令。SFT override 经已有 Renderer 与 _base_sft.yaml 合并后才能交给 LLaMA-Factory；不要直接训练 override 文件。新配置明确覆盖旧 dataset、eval_dataset、dataset_dir 和 output_dir，不训练旧预约数据。SFT 验证集是 train/val 切分结果，Frozen Eval 不用于选训练 checkpoint。

```powershell
python -m scripts.train.render_config --run-id baking-qwen3-0.6b
python -m scripts.train.render_config --run-id baking-qwen3-1.7b
```

Renderer 的历史 `--all` 与 run_matrix.sh 仍针对旧实验矩阵；搜索训练显式选择以上 run ID。新版本 CLI 别名为 search-build-dataset 和 search-eval，原 slot-* 别名兼容保留。没有注册搜索 DPO 数据集或 DPO 模型。

## Token 预检与训练

继承 LoRA rank=16、learning_rate=1e-4、3 epochs、Qwen3 template 和 enable_thinking=false。每设备 batch=1、梯度累积=16，cutoff_len=8192、packing=false。推理 max_tokens=2048，单槽 llama-server context=12288。长度是初始配置，训练前必须用实际 tokenizer 检查全部 train/val；它们不是已证明足够的最大输入上限。

LLaMA-Factory 的 cutoff_len 会截断超长输入，因此新增 check_search_data 检查完整 system/user/gold 序列、推理输入加输出预算和 Gold 输出长度，模板差异预留 32 tokens。超限直接失败，不修改或截断样本。检查使用本地缓存 tokenizer，不联网下载，可用 --tokenizer 指定本地目录。

```powershell
python -m scripts.train.check_search_data --run-id baking-qwen3-0.6b
python -m scripts.train.check_search_data --run-id baking-qwen3-1.7b
llamafactory-cli train configs/training/llamafactory/_rendered/baking-qwen3-0.6b.yaml
llamafactory-cli train configs/training/llamafactory/_rendered/baking-qwen3-1.7b.yaml
```

先冻结独立 data/eval/baking-v1.0/test.jsonl，再生成、审核 Raw 并通过 Task 07 构建 train/val。预检依赖训练环境的 Transformers 与实际 tokenizer。cutoff_len 或 max_tokens 调整后必须同步检查量化 Registry 的 server_args/context_size；8K 序列的显存需求需在目标训练设备上验证。

## 量化与本地推理

新 ModelRegistry 使用 baking_search profile，包含两个 Q4_K_M 目标及两个匹配 SFT F16 anchor。显式 adapter_path 与训练输出一致，模型产物和 Manifest 使用新的搜索名称。推理后端沿用 llama_server，请求关闭 thinking。

实际构建入口 build_phase05_real 已支持 --config，使用配置的 adapter_path、校准数据、工具路径、线程数和 imatrix context。转换器使用当前 Python；匹配 anchor 按 base_model 和 adapter_run_id 查找。其默认配置仍保留历史行为。

```powershell
python -m scripts.quantize.build_search --dry-run
python -m scripts.quantize.build_search
```

dry-run 仅显示目标及路径可用性，不意味着依赖齐全。正式构建需训练 adapter、本地完整 Qwen 权重、Transformers/PEFT/Torch 和 llama.cpp 转换/量化工具。校准文件 data/calibration/baking-search-v1.txt 应从审核后的 SFT train 的真实 Prompt 与 Gold 序列制备，不能用 val 或 Frozen Eval。当前尚未制备该文件；正式命令缺少输入时会失败。

实际 Manifest 记录校准与 adapter 文件 SHA256、模型来源及 GGUF SHA256。搜索版本拒绝复用已有 merged、imatrix、GGUF 和 Manifest，以免旧缓存被标记为新输入产物；中途失败需检查并显式处理未完成产物，或使用新的模型版本。GGUF 的 hash 验证不代表模型质量验收，仍要启动服务器并运行 Frozen Eval。

旧 run_phase05 是抽象流水线入口，其 stage 命令协议并非直接调用原生 llama.cpp 参数；本业务真实构建使用上面的 build_phase05_real，不改写历史流水线。

两个模型分别运行以下命令（各占一个终端），随后执行评估。server_args 配置 API alias，管理器同时验证 API 返回的模型身份。

```powershell
python -m slot_extractor.inference.llama_server_manager --config configs/quantization/baking_search_v1.yaml --server deployment/llama_cpp/bin/llama-server.exe --model-id baking-search-qwen3-0.6b-sft-v1-q4-k-m --port 8080
python -m slot_extractor.inference.llama_server_manager --config configs/quantization/baking_search_v1.yaml --server deployment/llama_cpp/bin/llama-server.exe --model-id baking-search-qwen3-1.7b-sft-v1-q4-k-m --port 8081
```

## 评估与验收

```powershell
python -m scripts.eval.run_eval --config configs/evaluation/baking_search_v1.yaml --model baking-qwen3-0.6b
python -m scripts.eval.run_eval --config configs/evaluation/baking_search_v1.yaml --model baking-qwen3-1.7b
```

两模型共享一个 Frozen Eval 与 Registry，默认使用 schema/assertions/patch 评分器。配置模式禁止覆盖 backend/cases/registry，报告目录可用 --report-dir 指向独立实验目录。旧 --backend-config/--cases 调用仍可用，但不自动执行配置验收门槛。

验收门槛为 Schema Valid=100%、Allergen Semantics=100%、no_unknown_field=100%、no_unknown_value=100%。未知字段/值检查覆盖全部响应，不依赖 Gold 是否写了相应断言。任何门槛没有适用样本时都不通过，避免把 n/a 当作满分。其余提取、硬软、状态、幻觉和最小 Patch 指标继续报告，具体上线目标需根据 Frozen Eval 和基线另行确定。

报告包含评估数据/Registry/config/backend hash、各门槛分数和适用数量。退出码 0 表示本次门槛通过，2 表示已完成评估但门槛不通过，1 表示配置、数据或推理执行失败。相同模型写同一目录会覆盖报告，应为不同实验指定不同目录。配置名称不构成冻结证明，冻结时仍须更新 dataset-registry 的状态和 hash。

## 验证边界

本任务验证配置衔接、真实 CLI 的离线 mock 路径、验收门槛、token 超限拒绝、量化参数及来源 hash、API alias 身份。测试不调用付费模型，不生成正式语料，不进行 GPU 训练或原生 GGUF 构建。

2026-10-03 验证结果：Python 3.11 全量回归 999 项通过，1 项 local_backend 按默认配置排除；Task 11 的 19 项测试在 Python 3.13 下通过。相关文件 Ruff 与 Git diff 空白检查通过，两套 SFT 配置渲染、数据构建 dry-run 和量化 dry-run 通过。量化 dry-run 明确显示正式校准文件及 llama.cpp 工具尚不存在；未验证实际 tokenizer 的全数据长度或训练依赖完整安装。Python 3.13 复用现有纯 Python 测试依赖，并在测试进程内适配 Windows sandbox 的临时目录权限，生产代码未加入该适配。

参考：[LLaMA-Factory 参数说明](https://llamafactory.readthedocs.io/en/latest/advanced/arguments.html)、[llama.cpp server 参数](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)。
