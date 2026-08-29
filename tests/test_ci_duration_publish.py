"""Lock merge_group duration publishing (#7141 next throughput slice).

Green merge_group runs through 2026-08-29 skipped ``Publish pytest durations``
because the job ``if`` was push-to-main only. That hid the MQ shard-test
totals that decide queue wall-clock. This slice runs the publisher on
successful merge_group python matrices, writes the step summary + artifact,
and keeps cache *save* on push-to-main (queue-branch caches are not
readable from later groups or from main).

CI Gate still does not require the job on merge_group: a publisher flake
must not dequeue a green pytest spine. Push still requires it so a missing
validating-run artifact fails the visible main check.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ci.gate_required_results import FULL_REQUIRED, PUSH_REQUIRED, required_jobs

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    data = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _steps(job_id: str) -> list[dict]:
    job = _load_ci()["jobs"][job_id]
    assert isinstance(job, dict)
    steps = job["steps"]
    assert isinstance(steps, list)
    return steps


def _named(job_id: str, name: str) -> dict:
    for step in _steps(job_id):
        if step.get("name") == name:
            return step
    raise AssertionError(f"{job_id} is missing step {name!r}")


def test_duration_publish_runs_on_merge_group_and_main_push() -> None:
    publish = _load_ci()["jobs"]["pytest-duration-publish"]
    condition = publish["if"]
    assert "github.event_name == 'merge_group'" in condition
    assert "github.event_name == 'push'" in condition
    assert "github.ref == 'refs/heads/main'" in condition
    assert "needs.python.result == 'success'" in condition
    assert "needs.landing-class.outputs.class != 'docs_skills'" in condition
    assert "pull_request" not in condition


def test_duration_publish_cache_save_stays_main_push_only() -> None:
    save = _named("pytest-duration-publish", "Save successful-main duration dataset")
    assert save["if"] == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert save["with"]["path"] == "ci-artifacts/pytest-durations.json"
    assert save["with"]["key"] == "pytest-shard-durations-v1-main-${{ github.sha }}"


def test_duration_publish_uploads_dataset_artifact() -> None:
    upload = _named("pytest-duration-publish", "Upload published duration dataset")
    assert upload["with"]["name"] == "pytest-durations"
    assert upload["with"]["path"] == "ci-artifacts/pytest-durations.json"
    assert upload["with"]["if-no-files-found"] == "error"


def test_duration_publish_labels_summary_with_event() -> None:
    step = _named("pytest-duration-publish", "Publish successful landing-tier durations and p95 summary")
    assert "--event \"${{ github.event_name }}\"" in step["run"]
    assert "publish-durations" in step["run"]


def test_merge_group_gate_does_not_require_duration_publish() -> None:
    assert "pytest-duration-publish" not in FULL_REQUIRED
    assert required_jobs("merge_group") == FULL_REQUIRED
    assert "pytest-duration-publish" in PUSH_REQUIRED
    assert required_jobs("push") == PUSH_REQUIRED


def test_duration_publish_still_downloads_from_validating_run_or_self() -> None:
    download = _named("pytest-duration-publish", "Download pytest shard results")
    assert download["with"]["run-id"] == (
        "${{ needs.landing-class.outputs.validating_run_id || github.run_id }}"
    )
    assert download["with"]["pattern"] == "pytest-shard-*"
