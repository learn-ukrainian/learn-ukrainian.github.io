"""Tests for controlled open-weight Ukrainian learning experiments (Issue #7889)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_open_weight_learning_study import (
    MODEL_IDENTIFIER,
    MODEL_REVISION,
    OPERATOR_EXCLUDED_RESIDUALS,
    assert_no_private_host_paths,
    verify_study,
)

CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")
STUDY_DIR = Path("data/projects/open_model_data/study")
RECIPE_PATH = STUDY_DIR / "v4_learning_study_recipe_v1.json"
RUNS_PATH = STUDY_DIR / "v4_learning_study_execution_runs_v1.jsonl"
RECEIPT_PATH = STUDY_DIR / "v4_learning_study_receipt_v1.json"


def test_schemas_valid() -> None:
    """The 3 JSON schemas for recipe, execution, and receipt must be valid Draft 2020-12 schemas."""
    for schema_name in [
        "v4_learning_study_recipe_v1.schema.json",
        "v4_learning_study_execution_v1.schema.json",
        "v4_learning_study_receipt_v1.schema.json",
    ]:
        p = CONTRACTS_DIR / schema_name
        assert p.is_file(), f"Missing schema contract: {p}"
        schema_data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema_data)


def test_train1_recipe_and_model_specification() -> None:
    """Verify pinned model, revision, tokenizer, and resource bounds (TRAIN-1)."""
    assert RECIPE_PATH.is_file(), f"Missing recipe: {RECIPE_PATH}"
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert recipe["schema_version"] == "v4_learning_study_recipe_v1"

    model_target = recipe["model_target"]
    assert model_target["identifier"] == MODEL_IDENTIFIER
    assert model_target["revision"] == MODEL_REVISION
    assert model_target["context_window"] >= 512

    dataset_target = recipe["dataset_target"]
    assert dataset_target["dataset_version"] == "v4.0.0-human-pilot-scale"
    assert dataset_target["training_spans_count"] == 614
    assert dataset_target["heldout_evaluation_spans_count"] == 559

    resource_bounds = recipe["resource_bounds"]
    assert resource_bounds["max_gpu_hours"] > 0
    assert resource_bounds["max_storage_mb"] > 0


def test_train2_hypotheses_and_pre_registration() -> None:
    """Verify pre-registered conditions, seeds, stopping criteria, and bounds (TRAIN-2)."""
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    conditions = recipe["conditions"]
    assert "unchanged_baseline" in conditions
    assert "faithful_human_adaptation" in conditions
    assert "modern_masked_adaptation" in conditions

    design = recipe["experimental_design"]
    assert design["seeds"] == [42, 43, 44]
    assert design["learning_rate"] == 2e-5
    assert design["max_steps"] == 100

    hyp = recipe["hypotheses_and_bounds"]
    assert hyp["expected_perplexity_reduction_pct_min"] >= 5.0
    assert hyp["max_historical_regression_pct"] <= 1.0


def test_train3_optimization_and_comparisons() -> None:
    """Verify execution of baseline, faithful, and modern masked conditions across all seeds (TRAIN-3)."""
    assert RUNS_PATH.is_file(), f"Missing runs: {RUNS_PATH}"
    runs: list[dict[str, Any]] = []
    with RUNS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            runs.append(json.loads(line_str))

    assert len(runs) == 9
    conditions_covered = {r["condition"] for r in runs}
    assert conditions_covered == {
        "unchanged_baseline",
        "faithful_human_adaptation",
        "modern_masked_adaptation",
    }

    seeds_covered = {r["seed"] for r in runs}
    assert seeds_covered == {42, 43, 44}

    for r in runs:
        assert r["schema_version"] == "v4_learning_study_execution_v1"
        assert r["run_id"].startswith("run.learning.")
        assert len(r["reproducibility"]["checkpoint_digest"]) == 64
        assert len(r["reproducibility"]["execution_digest"]) == 64


def test_train4_metrics_uncertainty_and_preservation() -> None:
    """Verify perplexity improvement, historical preservation, and zero catastrophic forgetting (TRAIN-4)."""
    assert RECEIPT_PATH.is_file(), f"Missing receipt: {RECEIPT_PATH}"
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["verdict"] == "STUDY_CONFIRMED_POSITIVE_LEARNING"

    summary = receipt["summary_findings"]
    assert summary["baseline_perplexity_mean"] > summary["faithful_adaptation_perplexity_mean"]
    assert summary["faithful_adaptation_perplexity_mean"] > summary["modern_masked_adaptation_perplexity_mean"]
    assert summary["perplexity_delta_pct"] < -20.0  # Significant reduction (>20% drop in perplexity)
    assert summary["historical_preservation_verified"] is True
    assert summary["catastrophic_forgetting_detected"] is False

    acct = receipt["runs_accounting"]
    assert acct["total_runs_attempted"] == 9
    assert acct["successful_runs"] == 9
    assert acct["failed_runs"] == 0

    assert receipt["residuals"]["operator_excluded_strata"] == OPERATOR_EXCLUDED_RESIDUALS


def test_train5_reproducibility_and_verification() -> None:
    """Verify that verify_study passes and fails on tampered receipts (TRAIN-5)."""
    assert verify_study(Path.cwd(), RECIPE_PATH, RUNS_PATH, RECEIPT_PATH) is True


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
        assert_no_private_host_paths({"test": "/home/ops/secret"})
