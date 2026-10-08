import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from search_dataset_helpers import registry
from test_generator import Result, SequenceBackend

from slot_extractor.data.diversity_audit import audit_diversity, audit_plans
from slot_extractor.data.generation_plan import (
    build_generation_plan,
    encoded,
    interleave_requests,
    semantic_signature,
)
from slot_extractor.data.generation_quality import validate_generation_quality
from slot_extractor.data.generator import GenerationRequest, RawGenerator, build_planned_messages
from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.search_generation import (
    generate_raw_dataset,
    generation_requests,
    prepare_generation_plan,
)
from slot_extractor.data.tag_audit import derive_tags
from slot_extractor.registry import ValueSpec
from slot_extractor.utils.jsonl import read_jsonl, write_jsonl

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs/data/baking_search_v1_1.yaml"


def config():
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def render(plan):
    """Explicit mock language, not an LLM-derived claim of naturalness."""
    record = plan.record("")
    patch = record["expected"]
    phrases = ["本次搜索的要求如下"]
    for kind, op in (("hard_filters", "op"), ("soft_preferences", "preference")):
        for condition in patch[kind]:
            prefix = "最好" if kind == "soft_preferences" else "必须"
            if condition[op] in {"not_in", "avoid"}:
                prefix += "不要"
            values = "和".join(condition["values"])
            scalar = " ".join(
                str(condition[k])
                for k in ("value", "min_value", "max_value")
                if condition[k] is not None
            )
            phrases.append(
                f"{prefix}{condition['field']} {values} {scalar} {condition['unit'] or ''}"
            )
    if patch["reset"]:
        phrases.append("重新开始搜索")
    if patch["clear_fields"]:
        phrases.append("取消已有条件" + "+".join(patch["clear_fields"]))
    if patch["sort"]:
        phrases.append(f"按 {patch['sort']['field']} {patch['sort']['order']} 排序")
    if patch["query_text"]:
        phrases.append(patch["query_text"])
    phrases.extend(patch["unmapped_terms"])
    record["input"]["user_input"] = "；".join(phrases)
    return record


@pytest.fixture(scope="module")
def full_plans():
    return build_generation_plan(config(), registry())


def test_all_1820_plans_are_registry_and_scenario_legal(full_plans):
    reg = registry()
    assert len(full_plans) == 1820
    assert {plan.scenario for plan in full_plans} == set(SCENARIOS)
    for plan in full_plans:
        item = render(plan)
        item["tags"] = derive_tags(item, reg)
        sample = raw_sample_from_record(item, reg)
        validate_generation_quality(sample, reg, plan=plan)
        assert len(item["assertions"]) >= 4
    audit = audit_plans(full_plans, reg, config()["diversity"])
    assert audit["ok"], audit["deficits"]
    for name in ("multi_filter", "hard_soft_mix"):
        report = audit["scenarios"][name]
        assert len(report["field_combinations"]) >= 10
        assert report["semantic_unique_ratio"] >= 0.8
        assert report["example_anchors"]["all_three"] == 0


def test_plan_is_deterministic_and_ids_survive_interleaving(full_plans):
    assert [p.to_dict() for p in full_plans] == [
        p.to_dict() for p in build_generation_plan(config(), registry())
    ]
    requests = generation_requests(config())
    scheduled = interleave_requests(requests)
    assert [r.scenario for r in scheduled[:15]] == list(SCENARIOS)
    assert {r.index for r in scheduled} == {r.index for r in requests}


@pytest.mark.parametrize(
    "field,pool",
    [
        ("price", [-1, 5]),
        ("size", [0, 1]),
        ("sweetness_level", [1, 6]),
        ("flavor_intensity", [True, 2]),
        ("imaginary", [1, 2]),
    ],
)
def test_invalid_numeric_pools_fail_before_model_call(field, pool):
    cfg = config()
    cfg["planning"]["numeric_pools"][field] = pool
    with pytest.raises(ValueError):
        build_generation_plan(cfg, registry())


def test_currency_pattern_and_infeasible_targets_fail_offline():
    cfg = config()
    cfg["planning"]["currencies"] = ["invalid_currency"]
    with pytest.raises(ValueError, match="unit_pattern"):
        prepare_generation_plan(cfg)
    cfg = config()
    cfg["diversity"]["min_field_combinations"] = 10000
    with pytest.raises(ValueError, match="infeasible"):
        prepare_generation_plan(cfg)


def test_candidates_follow_changed_registry_not_copied_enums():
    reg = registry()
    reg = replace(
        reg,
        fields=tuple(
            replace(f, values=(ValueSpec("custom_flavor", "定制风味", ("定制风味",)),))
            if f.name == "flavor"
            else f
            for f in reg.fields
        ),
    )
    cfg = config()
    cfg["counts"] = {"single_filter": 28}
    for plan in build_generation_plan(cfg, reg):
        for condition in (
            json.loads(plan.patch_json)["hard_filters"]
            + json.loads(plan.patch_json)["soft_preferences"]
        ):
            if condition["field"] == "flavor":
                assert condition["values"] == ["custom_flavor"]


def test_fixed_example_is_absent_and_gold_change_is_retried(full_plans, tmp_path):
    plan = next(p for p in full_plans if p.scenario == "hard_soft_mix")
    messages = build_planned_messages(plan, registry())
    assert "参考表达" not in str(messages)
    good = render(plan)
    bad = deepcopy(good)
    bad["expected"]["hard_filters"] = []
    backend = SequenceBackend([bad, good])
    generated = RawGenerator(backend, registry(), diagnostics_dir=tmp_path).generate_one(
        GenerationRequest(plan.scenario, int(plan.id.split("-")[-1])),
        plan=plan,
    )
    plan.assert_matches(generated.to_dict())
    assert "Gold differs from IntentPlan" in backend.calls[1][0][-1]["content"]
    diagnostic = list(tmp_path.glob("*.jsonl"))
    assert len(diagnostic) == 1
    assert list(read_jsonl(diagnostic[0]))[0]["output_text"] == json.dumps(bad)


def test_plan_match_ignores_condition_and_assertion_array_order(full_plans):
    plan = next(p for p in full_plans if len(json.loads(p.patch_json)["hard_filters"]) >= 2)
    item = render(plan)
    item["expected"]["hard_filters"].reverse()
    item["assertions"].reverse()
    plan.assert_matches(item)


def test_planned_text_rejects_wrong_negation_and_unit_conversion(full_plans):
    reg = registry()
    negative = next(p for p in full_plans if p.scenario == "negation")
    row = render(negative)
    row["input"]["user_input"] = row["input"]["user_input"].replace("不要", "想要")
    with pytest.raises(ValueError, match="negation"):
        validate_generation_quality(raw_sample_from_record(row, reg), reg, plan=negative)
    size = next(
        p
        for p in full_plans
        if p.scenario == "numeric_size"
        and json.loads(p.patch_json)["hard_filters"][0]["unit"] == "g"
    )
    row = render(size)
    row["input"]["user_input"] = row["input"]["user_input"].replace(" g", " kg")
    with pytest.raises(ValueError, match="original unit g"):
        validate_generation_quality(raw_sample_from_record(row, reg), reg, plan=size)
    hard = next(
        p
        for p in full_plans
        if p.scenario == "single_filter"
        and json.loads(p.patch_json)["hard_filters"]
        and reg.field(json.loads(p.patch_json)["hard_filters"][0]["field"]).values
        and json.loads(p.patch_json)["hard_filters"][0]["field"] != "allergen"
    )
    row = render(hard)
    row["input"]["user_input"] = row["input"]["user_input"].replace("必须", "最好")
    with pytest.raises(ValueError, match="hard requirement softened"):
        validate_generation_quality(raw_sample_from_record(row, reg), reg, plan=hard)


@pytest.mark.parametrize(
    "text",
    [
        "I'd prefer to steer clear of dairy-free options—do you have anything else?",
        "I'd rather stay away from DAIRY‐FREE options if possible.",
        "I would prefer not to choose dairy free options.",
        "我不太想要 dairy free 的那种，能避开就优先避开。",
    ],
)
def test_dairy_free_soft_avoid_accepts_hyphenation_and_avoidance_phrases(full_plans, text):
    plan = next(p for p in full_plans if p.id == "train-000008")
    sample = raw_sample_from_record(plan.record(text), registry())
    validate_generation_quality(sample, registry(), plan=plan)


@pytest.mark.parametrize(
    "text",
    [
        "Which ones are dairy free? I'd rather avoid those with dairy.",
        "I prefer dairy-free options.",
        "I'd prefer to steer clear of undairy-free options.",
    ],
)
def test_dairy_free_avoid_rejects_reversed_intent_and_substring_matches(full_plans, text):
    plan = next(p for p in full_plans if p.id == "train-000008")
    with pytest.raises(ValueError):
        validate_generation_quality(
            raw_sample_from_record(plan.record(text), registry()), registry(), plan=plan
        )


def test_semantic_audit_rejects_example_paraphrases_but_allows_sort_repetitions(full_plans):
    plan = next(p for p in full_plans if p.scenario == "hard_soft_mix")
    rows = [plan.record(f"这是不同句式的请求{i}") for i in range(100)]
    report = audit_diversity(rows, registry(), config()["diversity"])
    assert not report["ok"]
    assert any("semantic unique ratio" in error for error in report["deficits"])
    sorts = [p.to_dict() for p in full_plans if p.scenario == "sort"]
    assert audit_diversity(sorts, registry())["ok"]


def test_planned_pipeline_persists_plan_and_refuses_resume_contract_changes(tmp_path):
    cfg = config()
    cfg["counts"] = {"single_filter": 2, "sort": 2}
    cfg["generation_concurrency"] = 1
    evaluation = render(build_generation_plan(cfg, registry())[0])
    evaluation["id"] = "eval-000001"
    evaluation["input"]["user_input"] = "独立评估专用原话"
    cfg["eval_path"] = str(tmp_path / "eval.jsonl")
    write_jsonl(cfg["eval_path"], [evaluation])
    cfg["registry_path"] = str(CONFIG_PATH.parents[1] / "catalog/registry.yaml")
    plans = build_generation_plan(cfg, registry())
    by_id = {plan.id: plan for plan in plans}

    class PlannedBackend:
        model = "stub"
        calls = []
        fail = True

        def generate(self, messages, params=None):
            item = json.loads(messages[1]["content"].split("\n")[-1])
            self.calls.append(item["id"])
            if len(self.calls) == 2 and self.fail:
                raise RuntimeError("offline")
            row = render(by_id[item["id"]])
            return Result(json.dumps(row))

    backend = PlannedBackend()
    root = tmp_path / "raw"
    with pytest.raises(RuntimeError, match="offline"):
        generate_raw_dataset(cfg, backend, root)
    assert len(list(read_jsonl(root / ".generation_checkpoint.jsonl"))) == 1
    assert len(list(read_jsonl(root / "generation_plan.jsonl"))) == 4
    changed = deepcopy(cfg)
    changed["planning"]["styles"] = ["question"]
    with pytest.raises(ValueError, match="contract changed"):
        generate_raw_dataset(changed, backend, root)
    backend._reasoning = {"enabled": False}
    with pytest.raises(ValueError, match="contract changed"):
        generate_raw_dataset(cfg, backend, root)
    backend._reasoning = None
    ledger = root / "generation_plan.jsonl"
    original = ledger.read_bytes()
    ledger_rows = list(read_jsonl(ledger))
    ledger_rows[0]["style"] = "tampered"
    write_jsonl(ledger, ledger_rows)
    with pytest.raises(ValueError, match="persisted generation plan"):
        generate_raw_dataset(cfg, backend, root)
    ledger.write_bytes(original)
    backend.fail = False
    output = generate_raw_dataset(cfg, backend, root)
    assert len(list(read_jsonl(output))) == 4
    assert (root / "diversity.json").exists()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["diversity_ok"]
    assert manifest["gold_review_required"]
    assert "train-000001" not in backend.calls[2:]


def test_normalization_and_signatures_include_old_state():
    assert encoded({"values": ["b", "a"]}) == encoded({"values": ["a", "b"]})
    assert semantic_signature("replace", {}, {"value": "old1"}) != semantic_signature(
        "replace", {}, {"value": "old2"}
    )


def test_explicit_backend_migration_revalidates_and_keeps_provenance(tmp_path, monkeypatch):
    import slot_extractor.data.search_generation as pipeline

    cfg = config()
    cfg["counts"] = {"single_filter": 2}
    cfg["generation_concurrency"] = 1
    cfg["registry_path"] = str(CONFIG_PATH.parents[1] / "catalog/registry.yaml")
    plans = build_generation_plan(cfg, registry())
    evaluation = render(plans[0])
    evaluation["id"] = "eval-000001"
    evaluation["input"]["user_input"] = "独立评估专用原话"
    cfg["eval_path"] = str(tmp_path / "eval.jsonl")
    write_jsonl(cfg["eval_path"], [evaluation])
    old_identities = []
    original_hash = pipeline._hash

    def capture(value):
        if isinstance(value, dict) and "implementation_sha256" in value:
            old_identities.append(deepcopy(value))
        return original_hash(value)

    monkeypatch.setattr(pipeline, "_hash", capture)

    class Backend:
        model = "old-model"
        _base_url = "https://old.example/v1"

        def __init__(self):
            self.calls = []

        def generate(self, messages, params=None):
            sample_id = json.loads(messages[1]["content"].split("\n")[-1])["id"]
            self.calls.append(sample_id)
            if self.model == "old-model" and len(self.calls) == 2:
                raise RuntimeError("offline")
            plan = next(p for p in plans if p.id == sample_id)
            return Result(json.dumps(render(plan)))

    root = tmp_path / "raw"
    with pytest.raises(RuntimeError, match="offline"):
        generate_raw_dataset(cfg, Backend(), root)
    old_identity = old_identities[0]
    backend = Backend()
    backend.model = "new-model"
    backend._base_url = "https://new.example/v1"
    backend._thinking = {"type": "disabled"}
    meta = root / ".generation_checkpoint.meta.json"
    previous_meta = meta.read_bytes()
    with pytest.raises(ValueError, match="contract changed"):
        generate_raw_dataset(cfg, backend, root)
    forged = deepcopy(old_identity)
    forged["model"] = "forged"
    with pytest.raises(ValueError, match="does not match checkpoint"):
        generate_raw_dataset(cfg, backend, root, resume_backend_identity=forged)
    with pytest.raises(ValueError, match="cannot change the generation contract"):
        generate_raw_dataset(
            dict(cfg, seed=99), backend, root, resume_backend_identity=old_identity
        )
    checkpoint = root / ".generation_checkpoint.jsonl"
    checkpoint_bytes = checkpoint.read_bytes()
    rows = list(read_jsonl(checkpoint))
    rows[0]["expected"]["schema_version"] = "invalid"
    write_jsonl(checkpoint, rows)
    with pytest.raises(ValueError):
        generate_raw_dataset(cfg, backend, root, resume_backend_identity=old_identity)
    assert meta.read_bytes() == previous_meta
    checkpoint.write_bytes(checkpoint_bytes)
    generate_raw_dataset(
        cfg, backend, root, resume_backend_identity=old_identity, validate_resume=True
    )
    assert backend.calls == []
    assert checkpoint.read_bytes() == checkpoint_bytes
    history = json.loads(meta.read_text())["backend_transitions"]
    assert history[0]["previous_backend"]["model"] == "old-model"
    assert history[0]["next_backend"]["model"] == "new-model"
    assert history[0]["next_backend"]["thinking"] == {"type": "disabled"}
    assert history[0]["retained_sample_ids"] == ["train-000001"]
    output = generate_raw_dataset(cfg, backend, root)
    assert backend.calls == ["train-000002"]
    assert json.loads((root / "manifest.json").read_text())["backend_transitions"] == history
    assert len(list(read_jsonl(output))) == 2
