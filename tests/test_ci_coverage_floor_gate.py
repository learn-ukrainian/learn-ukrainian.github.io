"""Hermetic lock: coverage-floor stays on the gate path without XML/HTML render."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"


def _load_ci() -> dict:
    data = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _coverage_floor(jobs: dict) -> dict:
    job = jobs["coverage-floor"]
    assert isinstance(job, dict)
    return job


def _named_step(job: dict, name: str) -> dict:
    for step in job["steps"]:
        if step.get("name") == name:
            return step
    raise AssertionError(f"coverage-floor is missing step {name!r}")


def test_coverage_floor_stays_on_full_tier_gate_path() -> None:
    jobs = _load_ci()["jobs"]
    assert "coverage-floor" in jobs["ci-gate"]["needs"]
    job = _coverage_floor(jobs)
    assert job["if"] == "github.event_name != 'pull_request'"
    assert job["needs"] == ["python", "landing-class"]


def test_combine_and_enforce_keeps_floor_and_drops_render() -> None:
    step = _named_step(_coverage_floor(_load_ci()["jobs"]), "Combine and enforce")
    run = step["run"]
    assert "coverage combine" in run
    assert "coverage report --fail-under=35" in run
    assert "refusing to pass vacuously" in run
    assert "coverage xml" not in run
    assert "coverage html" not in run
    assert "coverage-html" not in run


def test_upload_ships_text_report_and_combined_data_only() -> None:
    job = _coverage_floor(_load_ci()["jobs"])
    uploads = [
        step
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    ]
    assert len(uploads) == 1
    step = uploads[0]
    with_block = step["with"]
    path = with_block["path"]
    assert "coverage-report.txt" in path
    assert ".coverage" in path
    assert with_block["include-hidden-files"] is True
    assert "coverage.xml" not in path
    assert "coverage-html/" not in path
    assert "coverage.xml" not in str(step)
    assert "coverage-html/" not in str(step)
