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
        ("agent", "10.0.0.1"),
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
        "host_id": "host-job",
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
