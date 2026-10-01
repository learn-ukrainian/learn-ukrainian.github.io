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
        "test-kimi-dry-run-nonce",
        "review-error-budget-pid-r1",
    ],
)
def test_worker_row_accepts_task_names_that_contain_hint_words(task_id: str) -> None:
    """#8874: a task named after stderr or a report took down the whole reporter run."""
    assert validate_worker_row_dict(_row(id=task_id)).id == task_id
    assert [row.id for row in validate_workers_list([_row(), _row(id=task_id)])] == ["monitor-7187", task_id]


def test_workers_list_cap_rejected() -> None:
    rows = [_row(id=f"t-{index}") for index in range(201)]
    with pytest.raises(ProjectStateValidationError):
        validate_workers_list(rows)


def test_valid_worker_row_round_trip() -> None:
    row = validate_worker_row_dict(_row())
    assert isinstance(row, WorkerRow)
    assert row.run_id == "a1b2c3d4"


def test_report_document_accepts_workers_block() -> None:
    document = {
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
        "workers": [_row()],
    }
    validate_report_document(document)
