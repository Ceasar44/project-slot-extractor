"""Compare API formats without modifying production data or checkpoints."""

import argparse
import json
import os
import time
import uuid
from pathlib import Path

import httpx
import yaml

from slot_extractor.data.generator import (
    GenerationRequest,
    build_generation_messages,
    parse_raw_json,
)
from slot_extractor.data.raw_schema import raw_response_schema
from slot_extractor.inference.openai_responses import _response_text
from slot_extractor.registry import load_registry

QUALITY_INSTRUCTION = (
    "user_input 必须是完整自然的用户搜索需求，至少4个有意义的文字字符，"
    "不是单字符、占位符或句子的首字。Gold 中每个分类取值必须在原话中显式出现"
    "其 Registry 名称或别名，数值使用阿拉伯数字；不要仅凭场景或参考例句填写 Gold。\n"
)
MODES = ("chat_plain", "chat_schema", "responses_schema")


def probe_messages(registry, index):
    # Reproduce the earlier minLength=1 prompt, before the quality guard was added.
    messages = build_generation_messages(GenerationRequest("single_filter", index), registry)
    system = messages[0]["content"].replace(QUALITY_INSTRUCTION, "")
    system = system.split("Raw JSON Schema：", 1)[0]
    schema = raw_response_schema(registry)
    messages[0]["content"] = system + "Raw JSON Schema：" + json.dumps(schema, ensure_ascii=False)
    return messages, schema


def request_body(mode, model, messages, schema, provider=None):
    body = {"model": model}
    if provider:
        body["provider"] = {"only": [provider], "allow_fallbacks": False}
    if mode == "responses_schema":
        body.update({
            "input": messages,
            "max_output_tokens": 4096,
            "text": {"format": {
                "type": "json_schema", "name": "baking_search_raw",
                "strict": True, "schema": schema,
            }},
        })
        return "/responses", body
    body.update({"messages": messages, "max_tokens": 4096})
    if mode == "chat_schema":
        body["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "baking_search_raw", "strict": True, "schema": schema,
        }}
    return "/chat/completions", body


def summarize(mode, payload):
    if payload.get("error"):
        return {"error": payload["error"]}
    try:
        if mode == "responses_schema":
            text = _response_text(payload)
            finish = payload.get("status")
        else:
            choice = payload["choices"][0]
            text = choice["message"].get("content")
            finish = choice.get("finish_reason")
        record = parse_raw_json(text)
        user_input = record["input"]["user_input"]
        if not isinstance(user_input, str):
            raise ValueError("user_input is not a string")
        return {
            "user_input": user_input, "characters": len(user_input),
            "meaningful_characters": sum(c.isalnum() for c in user_input),
            "finish": finish,
        }
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        return {"parse_error": str(exc)}


def run(args):
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    base_url = config.get("base_url") or os.environ[config["base_url_env"]]
    key = config.get("api_key") or os.environ[config["api_key_env"]]
    model = args.model or config["model"]
    registry = load_registry("configs/catalog/registry.yaml")
    if args.repeats < 1:
        raise ValueError("--repeats must be positive")
    messages, schema = probe_messages(registry, args.index)
    # Every run gets a fresh folder; no production data is read or written.
    root = Path(args.output_root) / f"probe-{uuid.uuid4().hex[:12]}"
    root.mkdir(parents=True, exist_ok=False)
    results = []
    total = len(MODES) * args.repeats
    print(f"Model={model}; provider={args.provider or 'automatic routing'}; requests={total}")
    print(f"Artifacts: {root}", flush=True)

    def save(path, content):
        serialized = json.dumps(content, ensure_ascii=False, indent=2)
        if key:
            serialized = serialized.replace(key, "<redacted>")
        path.write_text(serialized + "\n", encoding="utf-8")

    for repeat in range(1, args.repeats + 1):
        for mode in MODES:
            endpoint, body = request_body(mode, model, messages, schema, args.provider)
            name = f"{repeat:02d}-{mode}"
            save(root / f"{name}.request.json", body)
            print(f"[{len(results) + 1}/{total}] {mode}: requesting...", flush=True)
            result = {"mode": mode, "repeat": repeat}
            started = time.monotonic()
            try:
                response = httpx.post(
                    base_url.rstrip("/") + endpoint,
                    headers={"Authorization": f"Bearer {key}"},
                    json=body, timeout=args.timeout,
                )
                raw = response.text.replace(key, "<redacted>") if key else response.text
                (root / f"{name}.response.txt").write_text(raw, encoding="utf-8")
                result["http_status"] = response.status_code
                try:
                    payload = response.json()
                except ValueError:
                    result["error"] = "Non-JSON response; see saved response.txt"
                else:
                    result.update(summarize(mode, payload))
                    result["provider"] = payload.get("provider")
                    result["response_id"] = payload.get("id")
                    result["usage"] = payload.get("usage")
            except httpx.TransportError as exc:
                result["error"] = str(exc)
            result["seconds"] = round(time.monotonic() - started, 2)
            results.append(result)
            save(root / "summary.json", results)
            display = json.dumps(result, ensure_ascii=False)
            print(display.replace(key, "<redacted>") if key else display, flush=True)
    print(f"Finished. Summary: {root / 'summary.json'}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/inference/openai_responses_gpt_5.6_sol.yaml")
    parser.add_argument("--model")
    parser.add_argument("--provider", help="Exact OpenRouter provider slug; disables fallback")
    parser.add_argument(
        "--index", type=int, default=3, help="Single-filter field index; 3 is flavor"
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output-root", default=".tmp/openrouter-probes")
    args = parser.parse_args()
    try:
        return run(args)
    except (ValueError, KeyError, OSError) as exc:
        print(f"Probe setup failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
