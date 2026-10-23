"""Tests for controlled open-weight Ukrainian learning experiments (Issue #7889)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data.v4_open_weight_learning_study import (
    assert_no_private_host_paths,
)
from tests._host_path_guard import FIXTURE_HOME

STUDY_DIR = Path("data/projects/open_model_data/study")
RECIPE_PATH = Path("registry/projects/open_model_data/study/v4_learning_study_recipe_v1.json")
RUNS_PATH = STUDY_DIR / "v4_learning_study_execution_runs_v1.jsonl"
RECEIPT_PATH = STUDY_DIR / "v4_learning_study_receipt_v1.json"


@pytest.mark.needs_artifact(
    "open_model_study_outputs",
    "projects/open_model_data/study/v4_learning_study_receipt_v1.json",
)
def test_privacy_host_paths_clean() -> None:
    """Verify zero private host paths exist in any study artifact."""
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(recipe)

    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(receipt)

    with RUNS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                assert_no_private_host_paths(json.loads(line))

    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_no_private_host_paths({"test": f"{FIXTURE_HOME}/secret"})
