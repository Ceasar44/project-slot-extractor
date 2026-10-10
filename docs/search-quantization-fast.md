# 搜索模型快速量化与阶段复用

从项目根目录、已安装 Torch / Transformers / PEFT 的 Python 环境执行。下面是 Linux
命令；Windows PowerShell 使用 `$env:PYTHONPATH = "$PWD/src;$PWD"`。

## 构建模式

`configs/quantization/baking_search_v1.yaml` 注册两种大小的完整校准、快速校准、无校准 Q4
以及对应 F16。原来的完整模式保持 8192 上下文、batch 128、不限 chunks；未指定
`--model-id` 时只构建原来的两个完整模式，不自动运行实验模式。

| ID 后缀 | 行为 | 校准输入 |
| --- | --- | --- |
| `q4-k-m` | 完整校准 | `baking-search-v1.txt` |
| `q4-k-m-fast` | 2048 上下文、最多 50 chunks、关闭 PPL | 分层抽样文本及其来源 Manifest |
| `q4-k-m-no-imatrix` | 直接 Q4_K_M 量化 | 无需校准文件及 imatrix 工具 |

实验模式的输出和 Manifest 路径彼此独立。它们共享同一训练 adapter 和 F16 anchor，
但不能在质量未评估时视为与完整模式等价。

## Linux 与本地基座

Linux 将 `toolchain` 路径配置为本机编译出的无 `.exe` 后缀程序。例如源码压缩包目录：

```yaml
toolchain:
  resolve: huggingface-cli
  merge: llamafactory-cli
  convert_f16: deployment/llama_cpp/source/llama.cpp-master/convert_hf_to_gguf.py
  imatrix: deployment/llama_cpp/source/llama.cpp-master/build/bin/llama-imatrix
  quantize: deployment/llama_cpp/source/llama.cpp-master/build/bin/llama-quantize
  server: deployment/llama_cpp/source/llama.cpp-master/build/bin/llama-server
base_model_paths:
  Qwen/Qwen3-0.6B: models/base/Qwen3-0.6B
```

`base_model_paths` 只指定本地加载路径，不改变模型 Registry 的基座标识。必须使用训练时的
完整基座；构建记录实际权重及 tokenizer 的 hash。没有配置本地路径时，仍读取 HF 本地缓存。

源码压缩包没有 `.git` 时，构建记录 builder 源码 hash；也可显式设置
`project_revision: <真实项目版本>`。不再要求为运行构建而初始化 Git。

## 制备代表性校准集

```bash
export PYTHONPATH="$PWD/src:$PWD"
python -m scripts.quantize.prepare_search_calibration \
  --dataset-version baking-v1.1 --max-samples 150 --seed 42 \
  --tokenizer models/adapters/baking-search-qwen3-0.6b-sft-v1 \
  --output data/calibration/baking-search-v1-fast.txt
```

脚本核验 SFT Manifest 中 Raw / train / val / Registry / Frozen Eval 的 hash，按 train ID
将 Raw 场景与 SFT 行一一核对，并检查 train 与 val / Frozen Eval 的输入重叠。每个场景
至少抽一条，按场景轮转、固定随机种子选择，保留完整 system / user / Gold 和 Qwen3
非思考模板。`max-samples` 小于训练场景数时拒绝执行。

输出旁的 `.manifest.json` 记录样本 ID、场景数量、token 数、tokenizer 指纹、来源 hash
和 Gold 审核状态。抽样不会将待审核数据自动标记为已审核。已有校准文本拒绝覆盖，改参数
时使用新的输出路径，并更新对应 `model_options.<model-id>.calibration_data`。

1.7B 请使用它自己的 tokenizer，并输出 `data/calibration/baking-search-v1-fast-1.7b.txt`。

## 构建和检查

```bash
python -m scripts.quantize.build_search \
  --model-id baking-search-qwen3-0.6b-sft-v1-q4-k-m-fast --dry-run
python -m scripts.quantize.build_search \
  --model-id baking-search-qwen3-0.6b-sft-v1-q4-k-m-fast
```

跳过校准：

```bash
python -m scripts.quantize.build_search \
  --model-id baking-search-qwen3-0.6b-sft-v1-q4-k-m-no-imatrix
```

`dry-run` 会列出各目标实际使用的校准路径和参数，不导入训练依赖，也不证明完整运行条件
齐全。参数可由顶层 `imatrix` 或 `model_options.<model-id>.imatrix` 覆盖。`threads` 是
实际可用 CPU 线程数；校准上下文与模型服务的 12288 上下文相互独立。

## 可靠复用与中断恢复

合并结果放入 `work_root/sources/<输入指纹>/merged`，矩阵放入
`work_root/matrices/<输入及参数指纹>.gguf`。每阶段保存完成状态、输入、参数和输出 hash。
同样命令再次执行会核验并输出 `reuse:`；修改校准参数只重做矩阵和 Q4，不重新合并和转换。
修改基座、adapter 或合并依赖版本会使上游复用失效。

阶段写入独立临时目录，只有命令成功并校验非空输出后才提升为正式产物并写完成记录。
imatrix 周期性保存的中间结果不被视为完成，失败重跑重新计算该阶段，不从 checkpoint
自动续算。失败临时目录保留供诊断；不会自动删除已有用户产物。

F16 转换成功后立即写其 Manifest，即使后续校准失败，也可加载 F16。最终 Manifest 记录
校准参数、实际基座内容、adapter、F16、矩阵及工具 hash，并兼容原来的加载校验。

同阶段的并发构建由 `.lock` 文件阻止；异常杀进程后，先确认没有构建进程再处理残留锁。

**旧流程产物没有新阶段完成记录时，拒绝自动复用。** 不会只凭文件存在、大小非零就把旧
F16 或矩阵认定为完成。迁移时先保留旧产物，用一份配置副本指定新的 F16 artifact /
manifest 路径和 `work_root`；不要直接删除或覆盖正在运行的旧构建输出。旧流程若已生成
完整 GGUF 和 Manifest，仍可用原来的服务入口加载。

## 评估与双模型对比

对比应用会自动显示新增 Registry 条目，无需手动增加前端选项。构建成功后可选择 F16、
完整 Q4、fast 或 no-imatrix；缺少产物的模型继续显示不可用。

先用服务管理器启动所选实验 model ID 到 8080，再评估：

```bash
python -m scripts.eval.run_eval \
  --config configs/evaluation/baking_search_v1.yaml \
  --model baking-qwen3-0.6b-fast \
  --report-dir reports/generated/baking-search-v1/fast-first
```

无校准版使用 `--model baking-qwen3-0.6b-no-imatrix`。各实验共享相同 Frozen Eval 和验收
门槛；报告目录分开保存。CPU 时间取决于实例资源，新的参数需重新测量，不能保证固定速度。
