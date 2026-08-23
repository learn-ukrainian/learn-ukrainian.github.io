"""Acceptance tests for push-to-main merge-queue deduplication (#7173)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.ci import landing_class
from scripts.ci.gate_required_results import (
    FULL_REQUIRED,
    FULL_TIER_EVENTS,
    PUSH_REQUIRED,
    evaluate_gate,
    required_jobs,
)

REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
BEFORE_SHA = "before-sha"
HEAD_SHA = "head-sha"
PRODUCT_PATHS = ["scripts/app.py"]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _valid_run(*, run_id: int = 7173, base_sha: str = BEFORE_SHA) -> dict[str, Any]:
    return {
        "id": run_id,
        "event": "merge_group",
        "head_sha": HEAD_SHA,
        "path": ".github/workflows/ci.yml",
        "base_sha": base_sha,
        "status": "in_progress",
    }


def _valid_jobs() -> list[dict[str, Any]]:
    return [
        {"id": "ci-gate", "name": "CI Gate", "conclusion": "success"},
        *[
            {"id": f"python-{shard}", "name": f"Python (pytest) [{shard}/4]", "conclusion": "success"}
            for shard in range(1, 5)
        ],
    ]


def _valid_artifacts() -> list[dict[str, Any]]:
    return [{"name": f"pytest-shard-{shard}", "expired": False} for shard in range(1, 5)]


def _api(
    *,
    runs: list[dict[str, Any]] | None = None,
    jobs: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
    error: BaseException | None = None,
) -> tuple[Any, list[str]]:
    calls: list[str] = []

    def get(path: str) -> Any:
        calls.append(path)
        if error is not None:
            raise error
        if "/actions/workflows/ci.yml/runs?" in path:
            return {"workflow_runs": [_valid_run()] if runs is None else runs}
        if path.endswith("/jobs?per_page=100"):
            return {"jobs": _valid_jobs() if jobs is None else jobs}
        if path.endswith("/artifacts?per_page=100"):
            return {"artifacts": _valid_artifacts() if artifacts is None else artifacts}
        if "/commits/" in path:
            return {"parents": [{"sha": BEFORE_SHA}]}
        raise AssertionError(f"unexpected injected API path: {path}")

    return get, calls


def _classify(
    monkeypatch: pytest.MonkeyPatch,
    *,
    paths: list[str] | None = None,
    rederived_paths: list[str] | None = None,
    api: Any | None = None,
    event_name: str = "push",
    ref: str = "refs/heads/main",
    forced: str = "false",
    kill_switch: str = "on",
    before_sha: str = BEFORE_SHA,
) -> tuple[str, str | None]:
    monkeypatch.setattr(
        landing_class,
        "changed_files",
        lambda _git_range, *, cwd=None: list(PRODUCT_PATHS if rederived_paths is None else rederived_paths),
    )
    if api is None:
        api, _calls = _api()
    return landing_class.classify_push_to_main(
        PRODUCT_PATHS if paths is None else paths,
        before_sha=before_sha,
        head_sha=HEAD_SHA,
        event_name=event_name,
        ref=ref,
        forced=forced,
        kill_switch=kill_switch,
        repository=REPOSITORY,
        api_get=api,
    )


@pytest.mark.parametrize(
    "case",
    [
        "no run",
        "two ci.yml runs",
        "only a hygiene.yml run",
        "Gate failed",
        "one Python job failed",
        "shard artifacts missing",
        "docs_skills re-derivation",
        "API error",
        "API timeout",
        "forced push",
        "workflow_dispatch",
        "schedule",
        "self-reference file in diff",
        "kill switch unset",
        "kill switch off",
        "kill switch garbage",
        "before differs from base_sha",
    ],
    ids=lambda case: case.replace(" ", "-").replace("/", "-") if isinstance(case, str) else case,
)
def test_each_unproven_condition_fails_closed_to_full(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    """Each locked proof bullet is independently mutation-sensitive."""
    run = _valid_run()
    jobs = _valid_jobs()
    artifacts = _valid_artifacts()
    rederived_paths = PRODUCT_PATHS
    event_name = "push"
    forced = "false"
    kill_switch = "on"
    before_sha = BEFORE_SHA

    if case == "no run":
        runs: list[dict[str, Any]] = []
    elif case == "two ci.yml runs":
        runs = [_valid_run(run_id=1), _valid_run(run_id=2)]
    elif case == "only a hygiene.yml run":
        hygiene_run = _valid_run()
        hygiene_run["path"] = ".github/workflows/hygiene.yml"
        runs = [hygiene_run]
    else:
        runs = [run]
    if case == "Gate failed":
        jobs[0]["conclusion"] = "failure"
    if case == "one Python job failed":
        jobs[2]["conclusion"] = "failure"
    if case == "shard artifacts missing":
        artifacts.pop()
    if case == "docs_skills re-derivation":
        rederived_paths = ["docs/only.md"]
    if case in {"API error", "API timeout"}:
        error: BaseException = RuntimeError("API error") if case == "API error" else TimeoutError("API timeout")
        api, _calls = _api(error=error)
    else:
        api, _calls = _api(runs=runs, jobs=jobs, artifacts=artifacts)
    if case == "forced push":
        forced = "true"
    if case == "workflow_dispatch":
        event_name = "workflow_dispatch"
    if case == "schedule":
        event_name = "schedule"
    paths = ["scripts/ci/landing_class.py"] if case == "self-reference file in diff" else None
    if case == "kill switch unset":
        kill_switch = ""
    if case == "kill switch off":
        kill_switch = "off"
    if case == "kill switch garbage":
        kill_switch = "garbage"
    if case == "before differs from base_sha":
        before_sha = "different-before"

    result, run_id = _classify(
        monkeypatch,
        paths=paths,
        rederived_paths=rederived_paths,
        api=api,
        event_name=event_name,
        forced=forced,
        kill_switch=kill_switch,
        before_sha=before_sha,
    )
    assert result == landing_class.CLASS_FULL, case
    assert run_id is None, case


def test_all_locked_proof_bullets_emit_mq_validated_and_run_id(monkeypatch: pytest.MonkeyPatch) -> None:
    api, calls = _api()
    result, run_id = _classify(monkeypatch, api=api)

    assert result == landing_class.CLASS_MQ_VALIDATED
    assert run_id == "7173"
    assert any("event=merge_group" in path and "head_sha=head-sha" in path for path in calls)
    assert any(path.endswith("/jobs?per_page=100") for path in calls)
    assert any(path.endswith("/artifacts?per_page=100") for path in calls)


def test_merge_group_base_falls_back_to_first_commit_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    run = _valid_run()
    del run["base_sha"]
    api, calls = _api(runs=[run])
    result, run_id = _classify(monkeypatch, api=api)

    assert (result, run_id) == (landing_class.CLASS_MQ_VALIDATED, "7173")
    assert any("/commits/head-sha" in path for path in calls)


def test_rederived_range_is_exact_push_before_to_head(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []
    api, _calls = _api()

    monkeypatch.setattr(
        landing_class,
        "changed_files",
        lambda git_range, *, cwd=None: seen.append(git_range) or list(PRODUCT_PATHS),
    )
    result, _run_id = landing_class.classify_push_to_main(
        PRODUCT_PATHS,
        before_sha=BEFORE_SHA,
        head_sha=HEAD_SHA,
        event_name="push",
        ref="refs/heads/main",
        forced="false",
        kill_switch="on",
        repository=REPOSITORY,
        api_get=api,
    )

    assert result == landing_class.CLASS_MQ_VALIDATED
    assert seen == [f"{BEFORE_SHA}..{HEAD_SHA}"]


def test_main_always_exits_zero_and_writes_full_on_api_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(landing_class, "changed_files", lambda _git_range, *, cwd=None: list(PRODUCT_PATHS))
    monkeypatch.setattr(landing_class, "github_api_get", lambda _path, **_kwargs: (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_EVENT_FORCED", "false")
    monkeypatch.setenv("CI_PUSH_DEDUP", "on")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPOSITORY)
    output = tmp_path / "github-output"
    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    exit_code = landing_class.main(
        [
            "--base",
            BEFORE_SHA,
            "--before",
            BEFORE_SHA,
            "--head",
            HEAD_SHA,
            "--event",
            "push",
            "--repository",
            REPOSITORY,
            "--json",
            "--github-output",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["class"] == landing_class.CLASS_FULL
    assert output.read_text(encoding="utf-8") == "class=full\n"


def test_mq_output_contains_validating_run_id(tmp_path: Path) -> None:
    output = tmp_path / "github-output"
    landing_class.write_github_output(
        landing_class.CLASS_MQ_VALIDATED,
        output,
        validating_run_id="7173",
    )

    assert output.read_text(encoding="utf-8") == "class=mq_validated\nvalidating_run_id=7173\n"


def _success_results(required: tuple[str, ...] = PUSH_REQUIRED) -> dict[str, str]:
    return {job: "success" for job in required}


def test_gate_rejects_full_class_python_noop() -> None:
    failures = evaluate_gate(
        "push",
        _success_results(),
        landing_class="full",
        python_noop=True,
    )

    assert failures == ["class=full: python no-op is not allowed"]


def test_gate_rejects_mq_class_without_validating_run_proof() -> None:
    failures = evaluate_gate(
        "push",
        _success_results(),
        landing_class="mq_validated",
        python_noop=True,
        validating_run_id="",
    )

    assert failures == ["class=mq_validated: validating run proof is missing"]


def test_gate_accepts_mq_class_with_noop_and_validating_run() -> None:
    assert (
        evaluate_gate(
            "push",
            _success_results(),
            landing_class="mq_validated",
            python_noop=True,
            validating_run_id="7173",
        )
        == []
    )


def _steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for step in job.get("steps", []) if isinstance(step, dict)]


def _step(job: dict[str, Any], name: str) -> dict[str, Any]:
    return next(step for step in _steps(job) if step.get("name") == name)


def test_ci_workflow_wires_push_dedup_and_scheduled_coverage() -> None:
    workflow_text = _WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    jobs = workflow["jobs"]
    triggers = workflow.get("on", workflow.get(True))

    assert "schedule" in triggers
    assert "github.event_name == 'schedule'" in workflow_text
    assert "github.event_name == 'schedule' }}" in workflow_text
    assert jobs["landing-class"]["permissions"]["actions"] == "read"
    assert "validating_run_id" in jobs["landing-class"]["outputs"]
    for job_name in ("pytest-plan", "python", "coverage-floor", "ci-gate"):
        job_text = str(jobs[job_name])
        assert "mq_validated" in job_text
        assert "github.event_name == 'push'" in job_text
    for step_name in ("Download shard coverage data", "Combine and enforce", "Upload coverage report and combined data"):
        assert "github.event_name == 'schedule'" in _step(jobs["coverage-floor"], step_name)["if"]

    python_env = _step(jobs["python"], "Run planned pytest shard")["env"]
    assert "github.event_name == 'schedule'" in python_env["COLLECT_COVERAGE"]

    for job_name in ("pytest-plan", "python", "coverage-floor", "ci-gate"):
        for step in _steps(jobs[job_name]):
            condition = str(step.get("if", ""))
            if "mq_validated" in condition:
                assert (
                    "github.event_name == 'push'" in condition
                    or "github.event_name != 'push'" in condition
                )

    publish = jobs["pytest-duration-publish"]
    assert set(publish["needs"]) == {"python", "landing-class"}
    assert publish["permissions"]["actions"] == "read"
    download = _step(publish, "Download pytest shard results")
    assert download["with"]["run-id"] == "${{ needs.landing-class.outputs.validating_run_id || github.run_id }}"
    assert download["with"]["github-token"] == "${{ github.token }}"
    assert "for shard in 1 2 3 4" in _step(publish, "Require four shard logs for duration publication")["run"]
    assert "pytest-duration-publish" in jobs["ci-gate"]["needs"]
    gate_run = _step(jobs["ci-gate"], "Fail unless every event-required job succeeded")["run"]
    assert "--class" in gate_run
    assert "--python-noop" in gate_run
    assert "--validating-run-id" in gate_run
    assert "pytest-duration-publish" in str(_step(jobs["ci-gate"], "Fail unless every event-required job succeeded"))

    shard_upload = _step(jobs["python"], "Upload pytest shard plan and results")
    assert shard_upload["with"]["retention-days"] == 3
    assert "mq_validated" not in str(jobs["frontend"])
    assert "mq_validated" not in str(jobs["frontend-e2e"])


def test_publish_missing_artifacts_fails_visibly_on_push_gate() -> None:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    guard = _step(jobs["pytest-duration-publish"], "Require four shard logs for duration publication")["run"]

    assert "::error::pytest shard artifact/log missing" in guard
    assert "exit 1" in guard
    assert "pytest-duration-publish" in jobs["ci-gate"]["needs"]


def test_full_tier_events_include_daily_schedule() -> None:
    assert "schedule" in FULL_TIER_EVENTS
    assert required_jobs("schedule") == FULL_REQUIRED
