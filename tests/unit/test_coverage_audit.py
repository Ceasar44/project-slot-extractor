import pytest
from search_dataset_helpers import record, registry

from slot_extractor.data.coverage_audit import audit_semantic_coverage
from slot_extractor.data.raw_sample import raw_sample_from_record


def test_coverage_reports_gold_not_freeform_tags():
    item = record()
    item["tags"] = ["allergen", "replace"]
    sample = raw_sample_from_record(item, registry())
    report = audit_semantic_coverage([sample], registry())
    assert report.fields["price"] == 1
    assert report.operators["hard:price:lte"] == 1
    assert report.units["price:USD"] == 1
    assert report.capabilities.get("allergen", 0) == 0
    assert "fields:allergen" in report.deficits
    assert not report.ok


def test_explicit_quotas_have_exact_deficits():
    sample = raw_sample_from_record(record(), registry())
    report = audit_semantic_coverage([sample], registry(), {"scenarios": {"hard_soft_mix": 3}})
    assert report.deficits == {"scenarios:hard_soft_mix": 2}
    assert audit_semantic_coverage([sample], registry(), {}).ok


@pytest.mark.parametrize(
    "minimums", [{"bad": {}}, {"fields": {"price": -1}}, {"fields": {"price": True}}]
)
def test_invalid_audit_configuration(minimums):
    with pytest.raises(ValueError):
        audit_semantic_coverage([], registry(), minimums)
