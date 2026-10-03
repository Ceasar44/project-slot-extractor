"""Evaluate search gold with an explicit Registry, preserving legacy CLI separately."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from slot_extractor.evaluation.config import SCORERS, check_thresholds, load_evaluation_config
from slot_extractor.evaluation.runner import run_evaluation
from slot_extractor.evaluation.scorecard import render_scorecard, write_scorecard_json
from slot_extractor.inference.factory import build_backend_from_config
from slot_extractor.registry import load_registry
from slot_extractor.schemas.sample import load_samples


def build_parser():
    parser = argparse.ArgumentParser(description="Run SearchPatch evaluation")
    parser.add_argument("--config", help="Search evaluation YAML (paths relative to repo root)")
    parser.add_argument("--model", help="Model key in evaluation config backends")
    parser.add_argument("--backend-config")
    parser.add_argument("--cases")
    parser.add_argument("--registry")
    parser.add_argument("--report-dir")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        config = load_evaluation_config(args.config) if args.config else None
        if args.model and not config:
            raise ValueError("--model requires --config")
        if config:
            if args.model not in config["backends"]:
                raise ValueError("--model must select a key from evaluation backends")
            if args.backend_config or args.cases or args.registry:
                raise ValueError("--config owns backend/cases/registry; do not override them")
        backend_path = config["backends"][args.model] if config else args.backend_config
        cases = config["cases"] if config else args.cases
        if not backend_path or not cases:
            raise ValueError("provide --config/--model or --backend-config/--cases")
        registry_path = Path(
            config["registry"] if config else (args.registry or "configs/catalog/registry.yaml")
        )
        cases_path = Path(cases)
        report_dir = args.report_dir or (
            config["report_dir"] if config else "reports/generated/search"
        )
        registry = load_registry(registry_path)
        samples = load_samples(cases_path, registry)
        backend = build_backend_from_config(backend_path)
        scorers = [SCORERS[name]() for name in config["scorers"]] if config else None
        card = run_evaluation(samples, backend, registry, scorers)
        print(render_scorecard(card))
        report = write_scorecard_json(card, report_dir)
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["dataset"] = {
            "cases_path": str(cases_path),
            "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
            "registry_version": registry.registry_version,
            "registry_sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        }
        acceptance = None
        if config:
            acceptance = check_thresholds(card, samples, registry, config["thresholds"])
            payload["acceptance"] = acceptance
            payload["evaluation_config"] = {
                "path": args.config,
                "sha256": hashlib.sha256(Path(args.config).read_bytes()).hexdigest(),
                "model_key": args.model,
                "backend_path": backend_path,
                "backend_sha256": hashlib.sha256(Path(backend_path).read_bytes()).hexdigest(),
            }
        temporary = report.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(report)
        print(f"Report JSON: {report}")
        if acceptance is not None:
            print(f"Acceptance: {'PASS' if acceptance['passed'] else 'FAIL'}")
            if not acceptance["passed"]:
                return 2
        return 0
    except Exception as exc:
        print(f"search evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
