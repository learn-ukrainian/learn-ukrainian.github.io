"""Sanitizer and schema rejection tests for WorkerRow (#7187)."""

from __future__ import annotations

import pytest

from scripts.api.fleet_workers_models import WorkerRow
from scripts.api.fleet_workers_sanitize import validate_worker_row_dict, validate_workers_list
from scripts.api.project_state_sanitize import ProjectStateValidationError, validate_report_document


def _row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "kind": "delegate",
        "agent": "cursor",
        "harness": None,
        "id": "monitor-7187",
        "run_id": "a1b2c3d4",
        "epic": "epic:7177",
        "state": "live",
        "age_s": 10,
        "seat_model": None,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "/Users/foo/task"),
        ("agent", "203.0.113.7"),
        ("harness", "atlas-runner"),
        ("epic", "branch:main"),
        ("id", "pid:1234"),
        ("id", "run_nonce=abc"),
        ("id", "stderr boom"),
    ],
)
def test_worker_row_rejects_forbidden_string_classes(field: str, value: str) -> None:
    with pytest.raises(ProjectStateValidationError):
        validate_worker_row_dict(_row(**{field: value}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "host.example.org"),
        ("id", "svc:8765"),
        ("id", "198.51.100.4-task"),
        ("id", "vps-task"),
        ("agent", "pid=1234"),
        ("id", "traceback here"),
        ("run_id", "stderr"),
        ("note", "branch-name"),
    ],
)
def test_worker_row_still_rejects_structural_leaks_and_grammar_misses(field: str, value: str) -> None:
    with pytest.raises(ProjectStateValidationError):
        validate_worker_row_dict(_row(**{field: value}))


@pytest.mark.parametrize(
    "task_id",
    [
        "impl-entropy-test-git-stderr",
        "8313-thin-page-report",
        "8672-exporter-memory",
        "fix-8889-branch-r2",
        "triage-exception-budget",
        "port-audit-r1",
    ],
)
def test_worker_row_accepts_task_names_that_contain_hint_words(task_id: str) -> None:
    """#8874: a task named after stderr or a report took down the whole reporter run."""
    assert validate_worker_row_dict(_row(id=task_id)).id == task_id
    assert [row.id for row in validate_workers_list([_row(), _row(id=task_id)])] == ["monitor-7187", task_id]


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "run-nonce-1234abcd1234abcd"),
        ("id", "pid-1234"),
        ("id", "impl-8874-pid-1234"),
        ("id", "fix-8874-run-nonce-1234abcd1234abcd"),
        ("id", "report-run_nonce-deadbeef"),
        ("id", "stderr-pid-42"),
        ("id", "test-kimi-dry-run-nonce"),
        ("id", "review-error-budget-pid-r1"),
        ("id", "report-198.51.100.4"),
        ("agent", "pid-1234"),
        ("harness", "run-nonce-abcd"),
    ],
)
def test_identifier_fields_still_reject_pid_and_nonce_values(field: str, value: str) -> None:
    """#8874 review: the identifier exemption covers keyword hints only, never a PID or nonce."""
    with pytest.raises(ProjectStateValidationError):
        validate_worker_row_dict(_row(**{field: value}))
    with pytest.raises(ProjectStateValidationError):
        validate_workers_list([_row(), _row(**{field: value})])


@pytest.mark.parametrize("task_id", ["run-nonce-1234abcd1234abcd", "pid-1234", "impl-8874-pid-1234"])
def test_report_document_rejects_pid_and_nonce_identifiers(task_id: str) -> None:
    document = _report_document(workers=[_row(), _row(id=task_id)])
    with pytest.raises(ProjectStateValidationError):
        validate_report_document(document)


def test_report_document_keeps_task_name_with_keyword_hint() -> None:
    document = _report_document(workers=[_row(), _row(id="impl-entropy-test-git-stderr")])
    validate_report_document(document)
    assert [row["id"] for row in document["workers"]] == ["monitor-7187", "impl-entropy-test-git-stderr"]


def test_workers_list_cap_rejected() -> None:
    rows = [_row(id=f"t-{index}") for index in range(201)]
    with pytest.raises(ProjectStateValidationError):
        validate_workers_list(rows)


def test_valid_worker_row_round_trip() -> None:
    row = validate_worker_row_dict(_row())
    assert isinstance(row, WorkerRow)
    assert row.run_id == "a1b2c3d4"


def _report_document(*, workers: list[dict[str, object]]) -> dict[str, object]:
    return {
        "host_id": "host-worker",
        "primary": {
            "head_sha": "a" * 40,
            "origin_main_sha": "b" * 40,
            "origin_main_age_s": 1,
            "ahead": 0,
            "behind": 0,
            "dirty_count": 0,
        },
        "worktrees": {"count": 0},
        "services": [
            {
                "name": "api",
                "state": "running",
                "repo": "learn-ukrainian",
                "serving_mode": "release",
                "serving_sha": "b" * 40,
                "checkout_sha": None,
            }
        ],
        "collected_at": "2026-08-24T12:00:00Z",
        "workers": workers,
    }


def test_report_document_accepts_workers_block() -> None:
    validate_report_document(_report_document(workers=[_row()]))
