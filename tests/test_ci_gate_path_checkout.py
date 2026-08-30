"""Lock the #7141 Gate-path checkout slim (next Wave B item 4 slice).

Green merge_group 33282368887 (2026-08-30) still serialized:

- landing-class checkout 33s (fetch-depth 0) before shards can start
- coverage-floor checkout 19s after the last shard
- CI Gate checkout 20s + setup-python 11s for a 1s stdlib verify

This slice shallows/sparses those three jobs only. CI Gate stays the sole
required check; merge_group cancel-in-progress stays false; live
failure/skipped/missing still fail-closed; no class-keyed merge_group skips.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ci.gate_required_results import FULL_REQUIRED, GATE_NEEDS_JOBS

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
_SETUP_PYTHON = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"


def _load_ci() -> dict:
    data = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _job(job_id: str) -> dict:
    job = _load_ci()["jobs"][job_id]
    assert isinstance(job, dict)
    return job


def _steps(job_id: str) -> list[dict]:
    steps = _job(job_id)["steps"]
    assert isinstance(steps, list)
    return steps


def _named(job_id: str, name: str) -> dict:
    for step in _steps(job_id):
        if step.get("name") == name:
            return step
    raise AssertionError(f"{job_id} is missing step {name!r}")


def _checkout(job_id: str) -> dict:
    for step in _steps(job_id):
        if str(step.get("uses", "")).startswith(_CHECKOUT):
            return step
    raise AssertionError(f"{job_id} is missing actions/checkout")


def test_landing_class_uses_shallow_clone_and_fetches_missing_base() -> None:
    checkout = _checkout("landing-class")
    assert checkout["with"]["fetch-depth"] == 2
    assert checkout["with"]["persist-credentials"] is False

    fetch = _named("landing-class", "Fetch landing-class range endpoints")
    assert fetch["env"]["BASE_SHA"] == (
        "${{ github.event.merge_group.base_sha || github.event.before }}"
    )
    run = fetch["run"]
    assert "git fetch --no-tags --depth=1 origin" in run
    assert "fail-closes to full" in run
    assert "${{" not in run


def test_landing_class_freezes_snapshot_with_system_python3() -> None:
    freeze = _named("landing-class", "Freeze immutable pytest duration snapshot")
    assert "python3 scripts/ci/pytest_shards.py snapshot" in freeze["run"]
    names = [step.get("name") for step in _steps("landing-class")]
    uses = [str(step.get("uses", "")) for step in _steps("landing-class")]
    assert not any(item.startswith(_SETUP_PYTHON) for item in uses)
    assert "Classify landing class" in names


def test_coverage_floor_sparse_checkouts_scripts_and_coverage_pins() -> None:
    checkout = _checkout("coverage-floor")
    sparse = checkout["with"]["sparse-checkout"]
    assert "scripts" in sparse
    assert "pyproject.toml" in sparse
    assert "requirements-lock.txt" in sparse
    assert checkout["with"]["sparse-checkout-cone-mode"] is False
    combine = _named("coverage-floor", "Combine and enforce")
    assert "coverage report --fail-under=35" in combine["run"]
    assert "coverage xml" not in combine["run"]


def test_ci_gate_sparse_checkouts_scripts_ci_and_skips_setup_python() -> None:
    checkout = _checkout("ci-gate")
    assert "scripts/ci" in checkout["with"]["sparse-checkout"]
    assert checkout["with"]["sparse-checkout-cone-mode"] is True
    uses = [str(step.get("uses", "")) for step in _steps("ci-gate")]
    assert not any(item.startswith(_SETUP_PYTHON) for item in uses)

    verify = _named("ci-gate", "Verify pytest shard completeness")
    assert "python3 scripts/ci/pytest_shards.py verify-artifacts" in verify["run"]
    evaluate = _named("ci-gate", "Fail unless every event-required job succeeded")
    assert "python3 scripts/ci/gate_required_results.py" in evaluate["run"]


def test_gate_and_merge_group_invariants_hold_after_checkout_slim() -> None:
    workflow = _load_ci()
    concurrency = workflow["concurrency"]
    assert concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"
    gate = workflow["jobs"]["ci-gate"]
    assert gate["if"] == "always() && !cancelled()"
    assert set(gate["needs"]) == set(GATE_NEEDS_JOBS)
    assert "pytest-fastlane" in FULL_REQUIRED
    assert "python" in FULL_REQUIRED
    assert "coverage-floor" in FULL_REQUIRED
    assert "frontend" in FULL_REQUIRED
    python = workflow["jobs"]["python"]
    assert python["needs"] == ["landing-class"]
    assert python["strategy"]["fail-fast"] is False
