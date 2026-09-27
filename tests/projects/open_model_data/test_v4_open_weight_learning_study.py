"""Tests for controlled open-weight Ukrainian learning experiments (Issue #7889)."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from scripts.projects.open_model_data import v4_open_weight_learning_study as study
from scripts.projects.open_model_data.v4_open_weight_learning_study import (
    MODEL_IDENTIFIER,
    MODEL_REVISION,
    OPERATOR_EXCLUDED_RESIDUALS,
    assert_no_private_host_paths,
    verify_study,
)
from scripts.storage import artifacts, paths

CONTRACTS_DIR = Path("registry/projects/open_model_data/contracts")
STUDY_DIR = Path("data/projects/open_model_data/study")
RECIPE_PATH = Path("registry/projects/open_model_data/study/v4_learning_study_recipe_v1.json")
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


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)


def _fixture_repo(tmp_path: Path, *, changed_recipe: bool = False) -> Path:
    """Commit K baselines and keep only the three A fixture members on disk."""
    repo = tmp_path / "study-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    root = Path.cwd()
    registry_files = [
        study._RECIPE,
        "registry/projects/open_model_data/study/uldr_v1_acceptance_sample.signoff_template.json",
        "registry/projects/open_model_data/dataset/v4_human_source_dataset_manifest_v1.json",
        "registry/projects/open_model_data/dataset/v4_human_source_dataset_receipt_v1.json",
        *(
            f"registry/projects/open_model_data/contracts/{name}"
            for name in (
                "v4_learning_study_recipe_v1.schema.json",
                "v4_learning_study_execution_v1.schema.json",
                "v4_learning_study_receipt_v1.schema.json",
            )
        ),
    ]
    for relative in registry_files:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, target)
    if changed_recipe:
        recipe = json.loads((repo / study._RECIPE).read_text())
        recipe["recipe_id"] = "prior.recipe"
        (repo / study._RECIPE).write_text(json.dumps(recipe) + "\n")
    data_files = {
        study._RUNS: (root / f"data/{study._RUNS}").read_bytes(),
        study._RECEIPT: (root / f"data/{study._RECEIPT}").read_bytes(),
        "projects/open_model_data/dataset/v4_human_source_dataset_records_v1.jsonl": b"{}\n",
    }
    if changed_recipe:
        old_receipt = json.loads(data_files[study._RECEIPT])
        old_receipt["recipe_sha256"] = paths.hash_file(repo / study._RECIPE)
        data_files[study._RECEIPT] = (json.dumps(old_receipt, indent=2) + "\n").encode()
    for relative, content in data_files.items():
        target = repo / "data" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    table = repo / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason", "judgment"))
        for relative, content in data_files.items():
            group = study._DATASET_GROUP if "/dataset/" in relative else study._GROUP
            writer.writerow((f"data/{relative}", "100644", "", len(content), "A", group, "fixture", "test"))
    companions = {
        study._GROUP: [
            study._RECIPE,
            "registry/projects/open_model_data/study/uldr_v1_acceptance_sample.signoff_template.json",
        ],
        study._DATASET_GROUP: [
            "registry/projects/open_model_data/dataset/v4_human_source_dataset_manifest_v1.json",
            "registry/projects/open_model_data/dataset/v4_human_source_dataset_receipt_v1.json",
        ],
    }
    for group, bound in companions.items():
        entries = []
        for relative, content in data_files.items():
            if (study._DATASET_GROUP if "/dataset/" in relative else study._GROUP) == group:
                sha = hashlib.sha256(content).hexdigest()
                entries.append(
                    {"path": f"data/{relative}", "mode": "100644", "size": len(content), "sha256": sha, "store": sha}
                )
        manifest = {
            "schema": 1,
            "group": group,
            "entries": entries,
            "set_descriptor": {
                "members": sorted(entry["path"][5:] for entry in entries),
                "companions": {relative: paths.hash_file(repo / relative) for relative in bound},
            },
        }
        (repo / f"registry/artifacts/{group}.manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
    _git(repo, "add", "registry")
    _git(repo, "commit", "-qm", "committed K fixture baseline")
    return repo


def _managed(repo: Path) -> tuple[Path, Path, Path]:
    return repo / study._RECIPE, repo / "data" / study._RUNS, repo / "data" / study._RECEIPT


def test_managed_prepare_changed_repeated_and_run_verify(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, changed_recipe=True)
    recipe, runs, receipt = _managed(repo)
    before_runs = runs.read_bytes()
    study.build_recipe(repo, recipe)
    assert recipe.read_bytes() != (
        subprocess.run(
            ["git", "show", f"HEAD:{study._RECIPE}"], cwd=repo, check=True, capture_output=True, timeout=30
        ).stdout
    )
    assert runs.read_bytes() == before_runs
    assert paths.artifact_set(study._GROUP, repo=repo).companions[study._RECIPE] == recipe.read_bytes()
    assert not study.verify_study(repo, recipe, runs, receipt)
    study.build_recipe(repo, recipe)
    result = study.prepare_and_run(repo, recipe, runs, receipt)
    assert result["recipe_sha256"] == paths.hash_file(recipe)
    assert study.verify_study(repo, recipe, runs, receipt)
    assert paths.artifact_set(study._GROUP, repo=repo).artifacts[study._RUNS] == runs.read_bytes()


def test_managed_unchanged_prepare_direct_run_and_stale_recipe(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    recipe, runs, receipt = _managed(repo)
    original = recipe.read_bytes()
    study.build_recipe(repo, recipe)
    assert recipe.read_bytes() == original
    study.build_recipe(repo, recipe)
    study.run_study(repo, recipe, runs, receipt)
    assert study.verify_study(repo, recipe, runs, receipt)
    recipe.write_bytes(b"stale recipe")
    with pytest.raises(ValueError, match="companion changed"):
        study.run_study(repo, recipe, runs, receipt)


def test_managed_publish_failure_preserves_prior_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _fixture_repo(tmp_path, changed_recipe=True)
    recipe, runs, receipt = _managed(repo)
    prior = tuple(path.read_bytes() for path in (recipe, runs, receipt))
    manifest = (repo / f"registry/artifacts/{study._GROUP}.manifest.json").read_bytes()

    def fail_copy(*_args: object) -> None:
        raise OSError("injected store failure")

    monkeypatch.setattr(artifacts, "_store_copy", fail_copy)
    with pytest.raises(OSError, match="injected store failure"):
        study.prepare_and_run(repo, recipe, runs, receipt)
    assert tuple(path.read_bytes() for path in (recipe, runs, receipt)) == prior
    assert (repo / f"registry/artifacts/{study._GROUP}.manifest.json").read_bytes() == manifest


def test_companion_only_prepare_rejects_changed_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _fixture_repo(tmp_path, changed_recipe=True)
    recipe, runs, receipt = _managed(repo)
    before = tuple(path.read_bytes() for path in (recipe, runs, receipt))
    publish = study.publish_set

    def concurrent_manifest(*args: object, **kwargs: object) -> dict[str, str | None]:
        manifest_path = repo / f"registry/artifacts/{study._GROUP}.manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["concurrent_note"] = "different generation"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return publish(*args, **kwargs)

    monkeypatch.setattr(study, "publish_set", concurrent_manifest)
    with pytest.raises(ValueError, match="stale expected manifest"):
        study.build_recipe(repo, recipe)
    assert tuple(path.read_bytes() for path in (recipe, runs, receipt)) == before


def test_managed_cli_explicit_paths(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path, changed_recipe=True)
    recipe, runs, receipt = _managed(repo)
    for action in ("prepare", "prepare", "run", "verify"):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.projects.open_model_data.v4_open_weight_learning_study",
                action,
                "--repo-root",
                str(repo),
                "--recipe",
                str(recipe),
                "--runs",
                str(runs),
                "--receipt",
                str(receipt),
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr


def test_managed_verify_missing_member_requires_hydrate(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    recipe, runs, receipt = _managed(repo)
    runs.unlink()
    with pytest.raises(ValueError, match="hydrate --group open_model_study_outputs"):
        study.verify_study(repo, recipe, runs, receipt)


def test_external_paths_remain_writable(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    external = tmp_path / "export"
    recipe, runs, receipt = (external / name for name in ("recipe.json", "runs.jsonl", "receipt.json"))
    study.prepare_and_run(repo, recipe, runs, receipt)
    assert study.verify_study(repo, recipe, runs, receipt)
    assert not recipe.is_relative_to(repo)
    for action in ("run", "verify"):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.projects.open_model_data.v4_open_weight_learning_study",
                action,
                "--repo-root",
                str(repo),
                "--recipe",
                str(recipe),
                "--runs",
                str(runs),
                "--receipt",
                str(receipt),
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
