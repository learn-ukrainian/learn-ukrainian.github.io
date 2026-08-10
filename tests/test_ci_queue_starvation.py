"""Hermetic coverage for #4811 runner-queue starvation mitigations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from scripts.ci.queue_starvation_recovery import (
    TAIL_JOB_NAMES,
    decide_queue_starvation_rerun,
    scan_and_recover,
    select_candidate_runs,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_HYGIENE = _REPO_ROOT / ".github/workflows/hygiene.yml"
_RECOVERY = _REPO_ROOT / ".github/workflows/ci-gate-queue-recovery.yml"

# Always-on jobs that start together on every CI event (matrix shards count).
_MAX_ALWAYS_ON_PARALLEL_SLOTS = 6


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _triggers(workflow: dict) -> dict:
    raw = workflow.get("on", workflow.get(True))
    assert raw is not None
    return raw


def test_ci_folds_secret_scan_and_pr_body_into_contracts() -> None:
    jobs = _load(_CI)["jobs"]
    assert "security" not in jobs
    assert "pr-body-references" not in jobs
    contracts_steps = "\n".join(
        step.get("name", "") + "\n" + str(step.get("uses", "")) + "\n" + str(step.get("run", ""))
        for step in jobs["contracts"]["steps"]
    )
    assert "trufflesecurity/trufflehog@" in contracts_steps
    assert "lint_pr_closing_references.py" in contracts_steps
    assert set(jobs["ci-gate"]["needs"]) == {
        "python",
        "contracts",
        "frontend",
        "coverage-floor",
    }


def test_frontend_e2e_waits_for_ci_gate_success() -> None:
    e2e = _load(_CI)["jobs"]["frontend-e2e"]
    assert e2e["needs"] == ["ci-gate"]
    assert "needs.ci-gate.result == 'success'" in str(e2e["if"])


def test_always_on_parallel_runner_slots_stay_within_budget() -> None:
    jobs = _load(_CI)["jobs"]
    parallel = 0
    for name, job in jobs.items():
        if name in {"ci-gate", "coverage-floor", "frontend-e2e"}:
            continue
        if "needs" in job:
            continue
        matrix = job.get("strategy", {}).get("matrix", {})
        shards = matrix.get("shard")
        if isinstance(shards, list):
            parallel += len(shards)
        else:
            parallel += 1
    assert parallel <= _MAX_ALWAYS_ON_PARALLEL_SLOTS, (
        f"always-on parallel slots={parallel} exceed budget {_MAX_ALWAYS_ON_PARALLEL_SLOTS} (#4811)"
    )


def test_hygiene_uses_one_composite_checks_job() -> None:
    jobs = _load(_HYGIENE)["jobs"]
    assert "hygiene-checks" in jobs
    for retired in (
        "quality-gates",
        "lint-prompts",
        "postmortem-hygiene",
        "agent-config",
        "scripts-root-guard",
    ):
        assert retired not in jobs, f"{retired} must stay folded into hygiene-checks (#4811)"


def test_recovery_workflow_is_schedule_dispatch_default_branch_and_write_scoped() -> None:
    workflow = _load(_RECOVERY)
    triggers = _triggers(workflow)
    text = _RECOVERY.read_text(encoding="utf-8")
    assert "workflow_run" not in triggers
    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert triggers["schedule"]
    assert "cron" in triggers["schedule"][0]
    recover = workflow["jobs"]["recover"]
    assert recover["permissions"] == {"contents": "read", "actions": "write"}
    checkout = next(
        step for step in recover["steps"] if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    assert "ref" not in checkout.get("with", {}), (
        "recovery must not checkout a subject run's head SHA while holding actions:write"
    )
    assert "--scan" in text
    assert "queue_starvation_recovery.py" in text
    # Documented Option A: no privileged reaction to untrusted workflow completions.
    assert "Do NOT use workflow_run" in text or "do not use workflow_run" in text.lower()


def _jobs(*rows: tuple[str, str, int]) -> list[dict]:
    return [{"name": name, "conclusion": conclusion, "id": job_id} for name, conclusion, job_id in rows]


@pytest.mark.parametrize(
    ("jobs", "run_attempt", "expect_rerun", "reason_substr"),
    [
        (
            _jobs(
                ("Python (pytest) [1/4]", "success", 1),
                ("Contracts (schema, MDX, atlas, BIO)", "success", 2),
                ("Frontend (build + vitest)", "success", 3),
                ("Coverage floor", "success", 4),
                ("CI Gate", "cancelled", 5),
            ),
            1,
            True,
            "queue-starvation",
        ),
        (
            _jobs(
                ("Python (pytest) [1/4]", "success", 1),
                ("Coverage floor", "cancelled", 4),
                ("CI Gate", "cancelled", 5),
            ),
            1,
            True,
            "queue-starvation",
        ),
        (
            _jobs(
                ("Python (pytest) [1/4]", "failure", 1),
                ("CI Gate", "cancelled", 5),
            ),
            1,
            False,
            "failed job",
        ),
        (
            _jobs(
                ("Python (pytest) [1/4]", "cancelled", 1),
                ("CI Gate", "cancelled", 5),
            ),
            1,
            False,
            "non-tail",
        ),
        (
            _jobs(
                ("Python (pytest) [1/4]", "success", 1),
                ("CI Gate", "cancelled", 5),
            ),
            2,
            False,
            "max_attempts",
        ),
        (
            _jobs(
                ("Python (pytest) [1/4]", "success", 1),
                ("CI Gate", "failure", 5),
            ),
            1,
            False,
            "failed job",
        ),
    ],
)
def test_queue_starvation_decision_matrix(
    jobs: list[dict],
    run_attempt: int,
    expect_rerun: bool,
    reason_substr: str,
) -> None:
    decision = decide_queue_starvation_rerun(jobs, run_attempt=run_attempt)
    assert decision.should_rerun is expect_rerun
    assert reason_substr in decision.reason
    if expect_rerun:
        assert decision.job_ids
        assert set(decision.job_ids) <= {job["id"] for job in jobs if job["name"] in TAIL_JOB_NAMES}
        # Coverage floor before CI Gate when both were cancelled.
        names_by_id = {job["id"]: job["name"] for job in jobs}
        ordered_names = [names_by_id[job_id] for job_id in decision.job_ids]
        if "Coverage floor" in ordered_names and "CI Gate" in ordered_names:
            assert ordered_names.index("Coverage floor") < ordered_names.index("CI Gate")


def test_cli_emits_github_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ci import queue_starvation_recovery as mod

    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        '[{"name":"Python (pytest) [1/4]","conclusion":"success","id":11},'
        '{"name":"CI Gate","conclusion":"cancelled","id":99}]',
        encoding="utf-8",
    )
    out = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert (
        mod.main(
            [
                "--jobs-json",
                str(jobs_path),
                "--run-attempt",
                "1",
                "--github-output",
            ]
        )
        == 0
    )
    text = out.read_text(encoding="utf-8")
    assert "should_rerun=true" in text
    assert "job_ids=99" in text


def test_select_candidate_runs_filters_by_conclusion_and_lookback() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    runs = [
        {
            "id": 1,
            "name": "CI",
            "status": "completed",
            "conclusion": "cancelled",
            "run_attempt": 1,
            "updated_at": "2026-08-10T11:50:00Z",
        },
        {
            "id": 2,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "run_attempt": 1,
            "updated_at": "2026-08-10T11:55:00Z",
        },
        {
            "id": 3,
            "name": "Hygiene",
            "status": "completed",
            "conclusion": "failure",
            "run_attempt": 1,
            "updated_at": "2026-08-10T11:55:00Z",
        },
        {
            "id": 4,
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "run_attempt": 1,
            "updated_at": "2026-08-10T09:00:00Z",
        },
    ]
    selected = select_candidate_runs(runs, now=now, lookback_minutes=90)
    assert [run["id"] for run in selected] == [1]


def test_scan_and_recover_applies_only_matching_cancelled_tails() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    runs = [
        {
            "id": 101,
            "name": "CI",
            "status": "completed",
            "conclusion": "cancelled",
            "run_attempt": 1,
            "updated_at": (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        {
            "id": 102,
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "run_attempt": 1,
            "updated_at": (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    ]
    jobs_by_run = {
        101: _jobs(
            ("Python (pytest) [1/4]", "success", 11),
            ("CI Gate", "cancelled", 99),
        ),
        102: _jobs(
            ("Python (pytest) [1/4]", "failure", 21),
            ("CI Gate", "cancelled", 29),
        ),
    }
    reran: list[int] = []

    actions = scan_and_recover(
        runs,
        fetch_jobs=lambda run_id: jobs_by_run[run_id],
        rerun_job=reran.append,
        apply=True,
        now=now,
        lookback_minutes=90,
    )
    assert [action.run_id for action in actions] == [101, 102]
    assert actions[0].decision.should_rerun is True
    assert actions[0].applied is True
    assert actions[1].decision.should_rerun is False
    assert actions[1].applied is False
    assert reran == [99]
