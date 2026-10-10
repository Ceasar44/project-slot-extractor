"""Prepare a deterministic, scenario-balanced calibration corpus from SFT train only."""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from scripts.quantize.search_build import atomic_json
from slot_extractor.data.isolation import assert_no_eval_overlap
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.sft_render import render_sft
from slot_extractor.quantization.manifest import sha256_file
from slot_extractor.registry import load_registry


def read_jsonl(path):
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def select_samples(records, maximum, seed):
    groups = defaultdict(list)
    for record in records:
        groups[record["scenario"]].append(record)
    if maximum < len(groups):
        raise ValueError("max-samples must cover every training scenario")
    rng = random.Random(seed)
    for scenario in sorted(groups):
        group = groups[scenario]
        group.sort(key=lambda row: row["id"])
        rng.shuffle(group)
    selected = []
    while len(selected) < min(maximum, len(records)):
        for scenario in sorted(groups):
            if groups[scenario]:
                selected.append(groups[scenario].pop())
                if len(selected) == min(maximum, len(records)):
                    break
    # Avoid putting the same scenario consecutively in the token stream.
    return selected


def prepare(
    manifest_path,
    train_path,
    val_path,
    registry_path,
    tokenizer,
    output,
    maximum=150,
    seed=42,
    tokenizer_source="local",
    evaluation_path=Path("data/eval/baking-v1.0/test.jsonl"),
):
    if maximum < 1:
        raise ValueError("max-samples must be positive")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(evaluation_path) != manifest["eval_sha256"]:
        raise ValueError("Frozen Eval hash differs from SFT manifest")
    registry = load_registry(registry_path)
    if sha256_file(registry_path) != manifest["registry_sha256"]:
        raise ValueError("Registry hash differs from SFT manifest")
    raw_path = Path(manifest["source_raw_path"].replace("\\", "/"))
    for path in (raw_path, train_path, val_path):
        if "data/eval/" in path.resolve().as_posix().lower() + "/":
            raise ValueError("calibration input cannot use Frozen Eval")
    for name, path in (("raw", raw_path), ("train", train_path), ("val", val_path)):
        if sha256_file(path) != manifest["artifacts"][f"{name}_sha256"]:
            raise ValueError(f"{name} hash differs from SFT manifest")
    train_ids, val_ids = manifest["train"]["ids"], manifest["val"]["ids"]
    if len(train_ids) != len(set(train_ids)) or set(train_ids) & set(val_ids):
        raise ValueError("invalid or overlapping train/val IDs")
    rows = read_jsonl(train_path)
    if not rows or len(rows) != len(train_ids):
        raise ValueError("train count differs from manifest")
    raw_rows = read_jsonl(raw_path)
    raw = {row["id"]: row for row in raw_rows}
    if len(raw) != len(raw_rows):
        raise ValueError("duplicate Raw IDs")
    eligible = []
    rendered = {}
    for sample_id, row in zip(train_ids, rows, strict=True):
        record = raw[sample_id]
        if render_sft(raw_sample_from_record(record, registry), registry) != row:
            raise ValueError(f"train/Raw rendering mismatch: {sample_id}")
        rendered[sample_id] = row
        eligible.append(record)
    assert_no_eval_overlap(eligible, [raw[sample_id] for sample_id in val_ids])
    assert_no_eval_overlap(eligible, read_jsonl(evaluation_path))
    selected = select_samples(eligible, maximum, seed)
    if output.exists() or output.with_suffix(".manifest.json").exists():
        raise FileExistsError(f"calibration output exists; choose a new path: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    tokens = 0
    with temporary.open("w", encoding="utf-8", newline="\n") as target:
        for record in selected:
            row = rendered[record["id"]]
            turns = row["conversations"]
            messages = [
                {"role": "system", "content": row["system"]},
                {"role": "user", "content": turns[0]["value"]},
                {"role": "assistant", "content": turns[1]["value"]},
            ]
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False, enable_thinking=False
            )
            tokens += len(tokenizer.encode(text, add_special_tokens=False))
            target.write(text + "\n")
    temporary.replace(output)
    tokenizer_identity = {
        "source": tokenizer_source,
        "chat_template": getattr(tokenizer, "chat_template", None),
        "vocab": tokenizer.get_vocab(),
    }
    from scripts.quantize.search_build import digest

    metadata = {
        "dataset_id": manifest["dataset_id"],
        "split": "train",
        "seed": seed,
        "max_samples": maximum,
        "sample_ids": [r["id"] for r in selected],
        "sample_count": len(selected),
        "scenario_counts": dict(sorted(Counter(r["scenario"] for r in selected).items())),
        "token_count": tokens,
        "tokenizer_sha256": digest(tokenizer_identity),
        "source_manifest_sha256": sha256_file(manifest_path),
        "source_sha256": {
            "raw": sha256_file(raw_path),
            "train": sha256_file(train_path),
            "val": sha256_file(val_path),
            "registry": sha256_file(registry_path),
        },
        "calibration_sha256": sha256_file(output),
        "eval_sha256": sha256_file(evaluation_path),
        "gold_review_required": manifest.get("gold_review_required", True),
    }
    atomic_json(output.with_suffix(".manifest.json"), metadata)
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version", default="baking-v1.1")
    parser.add_argument("--max-samples", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tokenizer", default="models/adapters/baking-search-qwen3-0.6b-sft-v1")
    parser.add_argument("--registry", type=Path, default=Path("configs/catalog/registry.yaml"))
    parser.add_argument("--eval", type=Path, default=Path("data/eval/baking-v1.0/test.jsonl"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/calibration/baking-search-v1-fast.txt")
    )
    args = parser.parse_args(argv)
    if Path(args.dataset_version).name != args.dataset_version or args.dataset_version in {
        ".",
        "..",
    }:
        parser.error("dataset-version must be a directory name")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)
    root = Path("data/processed")
    result = prepare(
        root / args.dataset_version / "manifest.json",
        root / "sft" / args.dataset_version / "train.jsonl",
        root / "sft" / args.dataset_version / "val.jsonl",
        args.registry,
        tokenizer,
        args.output,
        args.max_samples,
        args.seed,
        args.tokenizer,
        args.eval,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
