"""Keep frozen appointment regressions separate from baking search tests."""

import pytest

LEGACY_PREFIXES = (
    "test_legacy_",
    "test_phase04_",
    "test_phase05_",
    "test_phase06_",
    "test_run_phase",
    "test_import_phase06_",
    "test_select_phase04",
    "test_scorer_reply_",
    "test_scorer_task_correctness",
)
LEGACY_FILES = {
    "test_dpo_perturb.py",
    "test_eval_dataset.py",
    "test_package_cloud_artifacts.py",
    "test_pipeline_mock.py",
    "test_pipeline_phase02.py",
    "test_scorer_preferences.py",
}
DEFAULT_SELECTION = "not local_backend and not legacy"


def is_legacy(path):
    return path.name.startswith(LEGACY_PREFIXES) or path.name in LEGACY_FILES


def pytest_ignore_collect(collection_path, config):
    # Avoid importing historical dependencies when running the default search suite.
    if config.getoption("markexpr") == DEFAULT_SELECTION and is_legacy(collection_path):
        return True
    return None


def pytest_collection_modifyitems(items):
    for item in items:
        if is_legacy(item.path):
            item.add_marker(pytest.mark.legacy)
