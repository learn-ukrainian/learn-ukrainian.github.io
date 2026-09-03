"""Unit tests for the single-tuple CI Gate aggregation (2026-09-03 simple-CI cutover)."""

from __future__ import annotations

import pytest

from scripts.ci.gate_required_results import (
    GATE_NEEDS_JOBS,
    REQUIRED_JOBS,
    evaluate_gate,
    main,
    parse_results,
)


def _all_success() -> dict[str, str]:
    return {job: "success" for job in REQUIRED_JOBS}


def test_required_jobs_is_one_tuple_for_every_event() -> None:
    for event in ("pull_request", "merge_group", "push", "schedule", "workflow_dispatch", "unknown-event"):
        assert evaluate_gate(event, _all_success()) == []


def test_gate_needs_jobs_matches_required_jobs() -> None:
    assert frozenset(REQUIRED_JOBS) == GATE_NEEDS_JOBS


def test_cf_attest_is_retired() -> None:
    assert "cf-attest" not in REQUIRED_JOBS


def test_retired_jobs_are_not_required() -> None:
    for retired in ("landing-class", "pytest-plan", "python", "coverage-floor", "pytest-duration-publish", "frontend-e2e"):
        assert retired not in REQUIRED_JOBS


@pytest.mark.parametrize("required_job", REQUIRED_JOBS)
@pytest.mark.parametrize("bad", ["failure", "cancelled", "skipped"])
def test_rejects_bad_dep(bad: str, required_job: str) -> None:
    results = _all_success()
    results[required_job] = bad
    failures = evaluate_gate("merge_group", results)
    assert any(f"{required_job}: {bad}" in item for item in failures)


def test_rejects_missing_dep() -> None:
    results = _all_success()
    del results["contracts"]
    failures = evaluate_gate("pull_request", results)
    assert any("contracts: missing" in item for item in failures)


def test_parse_results_round_trip() -> None:
    assert parse_results("ruff=success,contracts=failure") == {
        "ruff": "success",
        "contracts": "failure",
    }


def test_main_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    full = ",".join(f"{job}=success" for job in REQUIRED_JOBS)
    assert main(["--event", "merge_group", "--results", full]) == 0
    bad = full.replace("pytest=success", "pytest=skipped")
    assert main(["--event", "merge_group", "--results", bad]) == 1
    err = capsys.readouterr().err
    assert "pytest: skipped" in err


def test_main_malformed_results() -> None:
    assert main(["--event", "pull_request", "--results", "not-a-pair"]) == 2
