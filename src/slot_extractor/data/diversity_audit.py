"""Distribution audits supplement, rather than replace, natural-language Gold review."""

from collections import Counter, defaultdict
from itertools import combinations

from slot_extractor.data.generation_plan import encoded, semantic_signature


def audit_diversity(records, registry, targets=None):
    targets = targets or {}
    groups = defaultdict(list)
    for item in records:
        row = item.to_dict() if hasattr(item, "to_dict") else item
        groups[row["scenario"]].append(row)
    scenarios = {}
    deficits = []
    minimum_combinations = targets.get("min_field_combinations", 10)
    minimum_unique = targets.get("min_semantic_unique_ratio", 0.8)
    slack = targets.get("value_share_slack", 0.1)
    if type(minimum_combinations) is not int or minimum_combinations < 1:
        raise ValueError("min_field_combinations must be a positive integer")
    if not 0 < minimum_unique <= 1 or not 0 <= slack <= 1:
        raise ValueError("invalid diversity ratio")
    for scenario, rows in groups.items():
        signatures, patches, field_sets, pairs = Counter(), Counter(), Counter(), Counter()
        fields, operators, units, numbers, values, languages, styles = (Counter() for _ in range(7))
        ids = defaultdict(list)
        anchors = Counter()
        for row in rows:
            patch = row["expected"]
            state = row["input"]["current_search_state"]
            sig = semantic_signature(scenario, patch, state)
            signatures[sig] += 1
            patches[encoded(patch)] += 1
            ids[sig].append(row["id"])
            conditions = patch["hard_filters"] + patch["soft_preferences"]
            names = sorted({c["field"] for c in conditions})
            field_sets["+".join(names)] += 1
            pairs.update("+".join(pair) for pair in combinations(names, 2))
            fields.update(names)
            for kind, key in (("hard_filters", "op"), ("soft_preferences", "preference")):
                for condition in patch[kind]:
                    name = condition["field"]
                    operators[f"{kind}:{name}:{condition[key]}"] += 1
                    if condition["unit"]:
                        units[f"{name}:{condition['unit']}"] += 1
                    for code in condition["values"]:
                        values[f"{name}:{code}"] += 1
                    for scalar in ("value", "min_value", "max_value"):
                        if condition[scalar] is not None:
                            numbers[f"{name}:{scalar}:{condition[scalar]}"] += 1
            languages[row.get("language", "not_recorded")] += 1
            styles[row.get("style", "not_recorded")] += 1
            croissant = any("croissant_pastry" in c["values"] for c in conditions)
            pistachio = any(
                c["field"] == "flavor" and "pistachio" in c["values"] for c in conditions
            )
            price20 = any(
                c["field"] == "price"
                and any(c[key] == 20 for key in ("value", "min_value", "max_value"))
                for c in conditions
            )
            anchors.update(
                {
                    "croissant": int(croissant),
                    "pistachio": int(pistachio),
                    "price_20": int(price20),
                    "all_three": int(croissant and pistachio and price20),
                }
            )
        total = len(rows)
        ratio = len(signatures) / total
        if scenario in {"multi_filter", "hard_soft_mix"}:
            if len(field_sets) < minimum_combinations:
                deficits.append(
                    f"{scenario}: field combinations {len(field_sets)} < {minimum_combinations}"
                )
            if ratio < minimum_unique:
                deficits.append(f"{scenario}: semantic unique ratio {ratio:.3f} < {minimum_unique}")
            for name in fields:
                legal = registry.allowed_values(name)
                relevant = {key: n for key, n in values.items() if key.startswith(f"{name}:")}
                n = sum(relevant.values())
                if legal and n >= len(legal):
                    cap = ((n + len(legal) - 1) // len(legal)) / n + slack
                    if max(relevant.values(), default=0) / n > cap:
                        deficits.append(
                            f"{scenario}:{name}: categorical value concentration exceeds {cap:.3f}"
                        )
        scenarios[scenario] = {
            "count": total,
            "semantic_unique_ratio": ratio,
            "patch_unique_ratio": len(patches) / total,
            "field_combinations": dict(field_sets),
            "field_pairs": dict(pairs),
            "fields": dict(fields),
            "values": dict(values),
            "operators": dict(operators),
            "numbers": dict(numbers),
            "units": dict(units),
            "language_assignments": dict(languages),
            "style_assignments": dict(styles),
            "example_anchors": dict(anchors),
            "top_semantics": [
                {"signature": sig, "count": count, "ids": ids[sig]}
                for sig, count in signatures.most_common(10)
            ],
        }
    return {"ok": not deficits, "deficits": deficits, "scenarios": scenarios}


def audit_plans(plans, registry, targets=None):
    report = audit_diversity([plan.to_dict() for plan in plans], registry, targets)
    report["sample_count"] = len(plans)
    report["plan_sha256"] = semantic_signature("generation_plan", [p.to_dict() for p in plans])
    return report
