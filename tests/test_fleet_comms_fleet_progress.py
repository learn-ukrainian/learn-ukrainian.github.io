"""Tests for fleet progress (private #670 AC-PROGRESS)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.fleet_comms.cli import EXIT_OK, fleet_progress_payload, main


def test_fleet_progress_payload_surfaces_idle_and_work_exceptions(tmp_path: Path) -> None:
    store = tmp_path / "idle_settle" / "events.jsonl"
    store.parent.mkdir(parents=True)
    # Minimal event shapes consumed by build_report counters via injected list
    idle_events = [
        {
            "schema": "fleet-idle-settle-event.v1",
            "outcome": "missing_action",
            "eligible": True,
        },
        {
            "schema": "fleet-idle-settle-event.v1",
            "outcome": "disposed",
            "eligible": True,
            "disposition": "no_ready_work",
            "disposition_honest": False,
        },
        {
            "schema": "fleet-idle-settle-event.v1",
            "outcome": "invalid_disposition",
            "eligible": True,
        },
    ]
    work_next = {
        "available": True,
        "payload": {
            "queue": [
                {
                    "remote_id": "7898",
                    "title": "feat(ci): path-selected pytest",
                    "health": "OFF_TRACK",
                    "safe_next_action": {"code": "FIX_CI"},
                }
            ],
            "digest": {
                "other_streams": {
                    "top_blockers": [
                        {
                            "action_code": "FIX_CI",
                            "health": "OFF_TRACK",
                            "title": "feat(ci): path-selected pytest",
                        }
                    ]
                }
            },
        },
    }
    delegate_active = {
        "available": True,
        "payload": {
            "tasks": [
                {"task_id": "review-x", "agent": "agy", "status": "failed"},
                {"task_id": "ok-task", "agent": "codex", "status": "running"},
            ]
        },
    }

    payload = fleet_progress_payload(
        repo_root=tmp_path,
        idle_store=store,
        idle_events=idle_events,
        work_next=work_next,
        delegate_active=delegate_active,
    )

    assert payload["ac"] == "AC-PROGRESS"
    assert payload["idle_settle"]["missing_action"] == 1
    assert payload["idle_settle"]["dishonest"] == 1
    assert payload["idle_settle"]["invalid_disposition"] == 1
    assert payload["work_next"]["available"] is True
    assert payload["work_next"]["queue_len"] == 1
    assert payload["delegate_active"]["failed_or_terminal"] == [
        {"task_id": "review-x", "agent": "agy", "status": "failed"}
    ]
    kinds = {e["kind"] for e in payload["exceptions"]}
    assert "idle_settle_missing_action" in kinds
    assert "idle_settle_dishonest" in kinds
    assert "idle_settle_invalid_disposition" in kinds
    assert "work_queue" in kinds
    assert "delegate_terminal" in kinds
    assert payload["exception_count"] >= 5


def test_fleet_progress_fail_open_when_monitor_down(tmp_path: Path) -> None:
    payload = fleet_progress_payload(
        repo_root=tmp_path,
        idle_store=tmp_path / "missing.jsonl",
        idle_events=[],
        work_next={"available": False, "reason": "URLError"},
        delegate_active={"available": False, "reason": "TimeoutError"},
    )
    assert payload["work_next"]["available"] is False
    assert payload["delegate_active"]["available"] is False
    assert payload["exception_count"] == 0


def test_fleet_progress_cli_emits_json(tmp_path: Path, capsys) -> None:
    store = tmp_path / "events.jsonl"
    store.write_text("", encoding="utf-8")
    code = main(
        [
            "fleet",
            "progress",
            "--repo-root",
            str(tmp_path),
            "--idle-store",
            str(store),
            "--monitor-url",
            "http://127.0.0.1:59999",
        ]
    )
    assert code == EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["ac"] == "AC-PROGRESS"
    assert "exceptions" in out
