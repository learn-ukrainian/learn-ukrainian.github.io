"""Unit tests for event-aware CI Gate fail-closed aggregation."""

from __future__ import annotations

import pytest

from scripts.ci.gate_required_results import (
    FULL_REQUIRED,
    LIGHT_REQUIRED,
    PUSH_REQUIRED,
    evaluate_gate,
    main,
    parse_results,
    required_jobs,
)


def _full_success() -> dict[str, str]:
    return {job: "success" for job in FULL_REQUIRED}


def test_required_jobs_pull_request_is_light_tier() -> None:
    assert required_jobs("pull_request") == LIGHT_REQUIRED
    assert "pytest-plan" not in LIGHT_REQUIRED
    assert "python" not in LIGHT_REQUIRED
    assert "coverage-floor" not in LIGHT_REQUIRED


def test_required_jobs_merge_group_is_full_superset() -> None:
    assert required_jobs("merge_group") == FULL_REQUIRED
    assert set(LIGHT_REQUIRED) <= set(FULL_REQUIRED)


def test_required_jobs_push_and_dispatch_are_full() -> None:
    assert required_jobs("push") == PUSH_REQUIRED
    assert set(FULL_REQUIRED) < set(PUSH_REQUIRED)
    assert required_jobs("workflow_dispatch") == FULL_REQUIRED
    assert required_jobs("schedule") == FULL_REQUIRED


def test_unknown_event_fails_closed_as_full_tier() -> None:
    assert required_jobs("unknown-event") == FULL_REQUIRED


def test_merge_group_green_when_all_full_deps_succeed() -> None:
    assert evaluate_gate("merge_group", _full_success()) == []


def test_pull_request_green_when_light_deps_succeed_and_full_skipped() -> None:
    results = {job: "success" for job in LIGHT_REQUIRED}
    results["pytest-plan"] = "skipped"
    results["python"] = "skipped"
    results["coverage-floor"] = "skipped"
    assert evaluate_gate("pull_request", results) == []


def test_merge_group_rejects_skipped_full_tier_dep() -> None:
    results = _full_success()
    results["python"] = "skipped"
    failures = evaluate_gate("merge_group", results)
    assert any("python: skipped" in item for item in failures)


def test_merge_group_rejects_missing_dep() -> None:
    results = _full_success()
    del results["coverage-floor"]
    failures = evaluate_gate("merge_group", results)
    assert any("coverage-floor: missing" in item for item in failures)


@pytest.mark.parametrize("bad", ["failure", "cancelled", "skipped"])
def test_pull_request_rejects_bad_light_dep(bad: str) -> None:
    results = {job: "success" for job in LIGHT_REQUIRED}
    results["contracts"] = bad
    failures = evaluate_gate("pull_request", results)
    assert any(f"contracts: {bad}" in item for item in failures)


def test_parse_results_round_trip() -> None:
    assert parse_results("ruff=success,contracts=failure") == {
        "ruff": "success",
        "contracts": "failure",
    }


def test_main_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    full = ",".join(f"{job}=success" for job in FULL_REQUIRED)
    assert main(["--event", "merge_group", "--results", full]) == 0
    bad = full.replace("python=success", "python=skipped")
    assert main(["--event", "merge_group", "--results", bad]) == 1
    err = capsys.readouterr().err
    assert "python: skipped" in err


def test_main_malformed_results() -> None:
    assert main(["--event", "pull_request", "--results", "not-a-pair"]) == 2
