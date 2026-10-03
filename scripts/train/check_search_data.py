"""Offline token budget preflight for baking SFT; never truncate gold silently."""

import argparse
import json
import sys
from pathlib import Path

from scripts.train.render_config import CONFIG_ROOT, deep_merge, find_override, load_yaml
from slot_extractor.quantization.registry import ModelRegistry
from slot_extractor.registry import load_registry
from slot_extractor.schemas.output import parse_model_json, validate_search_patch_output


def check_rows(path, tokenizer, registry, cutoff_len, max_tokens=2048, context_size=12288):
    count, longest, longest_prompt, longest_gold = 0, 0, 0, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        turns = row.get("conversations", [])
        if set(row) != {"system", "conversations"} or (
            len(turns) != 2 or [t.get("from") for t in turns] != ["human", "gpt"]
        ):
            raise ValueError(f"{path}: row {count + 1} is not search SFT")
        validate_search_patch_output(parse_model_json(turns[1]["value"]), registry)
        messages = [
            {"role": "system", "content": row["system"]},
            {"role": "user", "content": turns[0]["value"]},
        ]
        prompt = len(
            tokenizer.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True, enable_thinking=False
            )
        )
        full = len(
            tokenizer.apply_chat_template(
                [*messages, {"role": "assistant", "content": turns[1]["value"]}],
                tokenize=True,
                add_generation_prompt=False,
                enable_thinking=False,
            )
        )
        gold = len(tokenizer.encode(turns[1]["value"], add_special_tokens=False))
        # Reserve template differences between Transformers and LLaMA-Factory.
        if full + 32 > cutoff_len or prompt + max_tokens > context_size or gold + 32 > max_tokens:
            raise ValueError(
                f"{path}: row {count + 1} exceeds token budget "
                f"(full={full}, prompt={prompt}, gold={gold}); increase matching configs"
            )
        count += 1
        longest, longest_prompt, longest_gold = (
            max(longest, full),
            max(longest_prompt, prompt),
            max(longest_gold, gold),
        )
    if not count:
        raise ValueError(f"empty search SFT: {path}")
    return {
        "rows": count,
        "max_full_tokens": longest,
        "max_prompt_tokens": longest_prompt,
        "max_gold_tokens": longest_gold,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--tokenizer", help="Local tokenizer directory; default is cached Qwen base"
    )
    args = parser.parse_args(argv)
    try:
        override = load_yaml(find_override(args.run_id))
        if not args.run_id.startswith("baking-"):
            raise ValueError("search preflight requires a baking run ID")
        config = deep_merge(load_yaml(CONFIG_ROOT / "_base_sft.yaml"), override)
        root = Path(config["dataset_dir"])
        info = json.loads((root / "dataset_info.json").read_text(encoding="utf-8"))
        paths = [root / info[config[key]]["file_name"] for key in ("dataset", "eval_dataset")]
        if any(not p.is_file() for p in paths):
            raise ValueError("build reviewed baking train/val data before token preflight")
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            args.tokenizer or config["model_name_or_path"], local_files_only=True
        )
        registry = load_registry(Path("configs/catalog/registry.yaml"))
        inference = load_yaml(Path("configs/inference") / f"{args.run_id}.yaml")
        models = ModelRegistry.from_config(Path("configs/quantization/baking_search_v1.yaml"))
        model = models.get(inference["model"])
        context_size = int(model.server_args[model.server_args.index("--ctx-size") + 1])
        result = {
            str(path): check_rows(
                path,
                tokenizer,
                registry,
                config["cutoff_len"],
                inference["max_tokens"],
                context_size,
            )
            for path in paths
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(f"search token preflight failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
