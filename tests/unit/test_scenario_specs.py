from pathlib import Path

import yaml

from slot_extractor.data.scenario_specs import SCENARIOS
from slot_extractor.data.search_generation import generation_requests
from slot_extractor.schemas.dataset_contract import SCENARIO_CODES


def test_scenarios_and_config_match_contract():
    config = yaml.safe_load(Path("configs/data/baking_search_v1.yaml").read_text(encoding="utf-8"))
    assert set(config["counts"]) == set(SCENARIOS) == set(SCENARIO_CODES)
    assert len(SCENARIOS) == 15
    requests = generation_requests(config)
    assert 1500 <= len(requests) <= 3000
    assert len({r.index for r in requests}) == len(requests)
    assert "dpo_target_counts" not in config
    assert all(s.instruction and s.example for s in SCENARIOS.values())
