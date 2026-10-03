> Historical appointment project instructions, archived during Task 12.
> Use the repository root README for the baking search workflow.

# Slot-Extractor Fine-tuning

Fine-tuning and evaluation project for baking sauce search parameter extraction.
The default data/evaluation pipeline uses SearchPatch; historical appointment experiments are retained.

## Baking search comparison

```powershell
python -m uvicorn slot_extractor.search_compare.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Each side shows raw output, SearchPatch validation, merged state,
state changes, compiled search parameters and timing. Models require the baking GGUF artifacts
and verified manifests; unavailable models remain visible. See [comparison workflow](docs/search-compare.md)
and [training/inference/quantization configuration](docs/search-model-configs.md).

## Historical appointment comparison

Phase 05 includes a registry-driven quantization/evaluation pipeline and a local two-model
tool-loop comparison app. See `docs/project-structure.md` for repository ownership.

Start the comparison UI after provisioning the registered GGUF artifacts and llama.cpp binaries:

```powershell
uv run python -m uvicorn slot_extractor.tool_loop.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The app reads models from
`configs/quantization/phase05.yaml` and technicians from the versioned fixture; unavailable models
remain visible but cannot be selected.

## Reproducing Phase 05 models

The repository includes the six final LoRA adapters used by the Phase 05 experiment matrix under
`models/adapters/`. Each directory contains only `adapter_config.json` and
`adapter_model.safetensors`; training checkpoints and duplicated tokenizers are intentionally
excluded. The adapter configuration identifies its matching upstream Qwen base model.

Merged models and GGUF files are generated artifacts and are not committed. Rebuild them with the
registry and quantization pipeline:

```powershell
uv run python -m scripts.quantize.run_phase05 --config configs/quantization/phase05.yaml
```

The committed training and inference configurations, adapters, evaluation dataset, fixture, and
pipeline code are the reproducibility boundary. Base model downloads remain subject to their
upstream license and availability.

## AutoDL / 国内远端训练的 Hugging Face 配置

训练配置使用 `Qwen/Qwen3-*` 仓库名。即使模型权重已经缓存在本机，Transformers 和
Hugging Face Hub 在启动时仍可能访问远端，解析 `main` revision、检查元数据和确认缺失
文件。国内实例直连 `huggingface.co` 可能长时间停在 `loading configuration file`。

AutoDL 实例启动或重启后设置：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/huggingface
```

`HF_ENDPOINT` 决定元数据查询和缺失文件下载地址；`HF_HOME` 指向持久盘中的模型缓存。
这不会强制重新下载已有模型。若确认缓存完整，也可以额外启用完全离线模式：

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

环境变量只在当前 shell 中有效；需要长期保留时可写入 `~/.bashrc`。各阶段的远端训练包
也会设置适合 AutoDL 的默认值，但允许调用方通过已有环境变量覆盖。
