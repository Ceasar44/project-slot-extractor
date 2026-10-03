from search_dataset_helpers import multi_record, record, registry

from slot_extractor.data.raw_sample import raw_sample_from_record
from slot_extractor.data.tag_audit import audit_tags, derive_tags
from slot_extractor.schemas.search_patch import SearchPatch


def test_tags_follow_gold_and_ignore_model_tags():
    item = record()
    tags = derive_tags(item, registry())
    assert {
        "single_turn",
        "hard_soft",
        "relative_numeric",
        "price",
        "flavor",
        "sweetness_level",
    } <= set(tags)
    item["tags"] = ["made_up"]
    assert derive_tags(item, registry()) == tags
    assert len(tags) <= 16 and len(tags) == len(set(tags))
    assert not audit_tags([raw_sample_from_record(item, registry())], registry()).ok
    item["tags"] = tags
    assert audit_tags([raw_sample_from_record(item, registry())], registry()).ok


def test_replace_preservation_clear_reset_are_distinct():
    item = multi_record()
    assert {"replace", "preserve_state", "allergen", "negation"} <= set(
        derive_tags(item, registry())
    )
    item["expected"] = SearchPatch(clear_fields=("flavor",)).to_dict()
    item["scenario"] = "clear"
    assert "clear" in derive_tags(item, registry())
    assert "replace" not in derive_tags(item, registry())
    item["expected"] = SearchPatch(reset=True).to_dict()
    item["scenario"] = "reset"
    assert "preserve_state" not in derive_tags(item, registry())
