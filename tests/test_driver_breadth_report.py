"""Tests for scripts.fleet.driver_breadth_report."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.fleet.driver_breadth_report import (
    _parse_ts,
    _tier_for,
    build_report,
    load_tasks,
    main,
)


def _task(
    path: Path,
    *,
    task_id: str,
    agent: str,
    model: str,
    initiator: str,
    status: str = "done",
    hours_ago: float = 1.0,
) -> None:
    started = datetime.now(UTC) - timedelta(hours=hours_ago)
    payload = {
        "task_id": task_id,
        "agent": agent,
        "model": model,
        "initiator": initiator,
        "status": status,
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_s": 10,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_parse_ts_naive_becomes_utc() -> None:
    dt = _parse_ts("2026-08-06T12:00:00")
    assert dt is not None
    assert dt.tzinfo is not None


def test_note_file_requires_fleet_breadth_marker(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for i in range(3):
        _task(
            tasks_dir / f"t{i}.json",
            task_id=f"work-{i}",
            agent="claude",
            model="claude-sonnet-5",
            initiator="grok-night-drive",
        )
    bad = tmp_path / "bad.md"
    bad.write_text("x\n", encoding="utf-8")
    assert (
        main(
            [
                "--tasks-dir",
                str(tasks_dir),
                "--initiator",
                "grok",
                "--enforce",
                "--note-file",
                str(bad),
                "--json",
            ]
        )
        == 2
    )


def test_tier_for_gemini_flash_high_is_practical() -> None:
    """CF F1: bare 'flash' must not map gemini-*-flash-high to heap."""
    assert _tier_for("agy", "gemini-3.7-flash-high") == "practical"
    assert _tier_for("gemini", "gemini-3.7-flash-high") == "practical"
    assert _tier_for("agy", "gemini-3.6-flash-high") == "practical"
    # Bare flash token still heap when not flash-high.
    assert _tier_for("codex", "gpt-5.6-luna") == "heap"
    # 'mini' must not match inside 'gemini'
    assert _tier_for("agy", "gemini-3.1-pro-high") == "practical"


def test_breadth_floor_fails_single_seat(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for i in range(3):
        _task(
            tasks_dir / f"t{i}.json",
            task_id=f"work-{i}",
            agent="claude",
            model="claude-sonnet-5",
            initiator="grok-night-drive",
        )
    tasks = load_tasks(tasks_dir, initiator_prefix="grok", since=datetime.now(UTC) - timedelta(hours=24))
    report = build_report(tasks)
    assert report["implement_dispatch_count"] == 3
    assert report["distinct_agents"] == 1
    assert report["breadth_floor_applies"] is True
    assert report["breadth_floor_ok"] is False


def test_breadth_floor_ok_two_agents_two_tiers(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _task(tasks_dir / "a.json", task_id="a", agent="claude", model="claude-sonnet-5", initiator="grok-x")
    _task(tasks_dir / "b.json", task_id="b", agent="codex", model="gpt-5.6-luna", initiator="grok-x")
    _task(tasks_dir / "c.json", task_id="c", agent="codex", model="gpt-5.6-terra", initiator="grok-x")
    tasks = load_tasks(tasks_dir, initiator_prefix="grok", since=datetime.now(UTC) - timedelta(hours=24))
    report = build_report(tasks)
    assert report["distinct_agents"] >= 2
    assert report["implement_tiers"].get("heap", 0) >= 1  # luna
    assert report["breadth_floor_ok"] is True


def test_breadth_floor_ignores_review_tasks_for_diversity(tmp_path: Path) -> None:
    """CF: review-* must not launder single-seat implement marathons."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for i in range(3):
        _task(
            tasks_dir / f"impl{i}.json",
            task_id=f"impl-{i}",
            agent="claude",
            model="claude-sonnet-5",
            initiator="grok-x",
        )
    _task(
        tasks_dir / "rev.json",
        task_id="review-cf-1",
        agent="codex",
        model="gpt-5.6-terra",
        initiator="grok-x",
    )
    tasks = load_tasks(tasks_dir, initiator_prefix="grok", since=datetime.now(UTC) - timedelta(hours=24))
    report = build_report(tasks)
    assert report["implement_dispatch_count"] == 3
    assert report["breadth_floor_applies"] is True
    assert report["distinct_agents"] == 1
    assert report["breadth_floor_ok"] is False


def test_enforce_exits_two_without_note(tmp_path: Path, monkeypatch) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for i in range(3):
        _task(
            tasks_dir / f"t{i}.json",
            task_id=f"work-{i}",
            agent="claude",
            model="claude-sonnet-5",
            initiator="grok-night-drive",
        )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--since-hours",
            "24",
            "--enforce",
            "--json",
        ]
    )
    assert code == 2


def test_enforce_waived_by_note_file(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for i in range(3):
        _task(
            tasks_dir / f"t{i}.json",
            task_id=f"work-{i}",
            agent="claude",
            model="claude-sonnet-5",
            initiator="grok-night-drive",
        )
    note = tmp_path / "note.md"
    note.write_text("NOTE: fleet_breadth — language-lane only this session\n", encoding="utf-8")
    absent = tmp_path / "no-idle.jsonl"
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--note-file",
            str(note),
            "--idle-store",
            str(absent),
            "--json",
        ]
    )
    assert code == 0


def _diverse_tasks(tasks_dir: Path) -> None:
    _task(tasks_dir / "a.json", task_id="a", agent="claude", model="claude-sonnet-5", initiator="grok-x")
    _task(tasks_dir / "b.json", task_id="b", agent="codex", model="gpt-5.6-luna", initiator="grok-x")
    _task(tasks_dir / "c.json", task_id="c", agent="codex", model="gpt-5.6-terra", initiator="grok-x")


def test_enforce_fails_missing_idle_disposition(tmp_path: Path, capsys) -> None:
    """#6998: --enforce fails MISSING disposition; idle seconds are not a gate."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    store = tmp_path / "idle.jsonl"
    store.write_text(
        json.dumps(
            {
                "schema": "fleet-idle-settle-event.v1",
                "outcome": "missing_action",
                "eligible": True,
                "reminder_fired": True,
                "opportunity_seconds_since_prev": 12.0,
                "disposition_honest": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--json",
            "--idle-store",
            str(store),
        ]
    )
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["breadth_floor_ok"] is True
    assert payload["idle_settle"]["report_only"] is False
    assert payload["idle_settle"]["enforce_fail_codes"] == ["MISSING"]
    assert payload["idle_settle"]["settle_events_missing_action"] == 1
    assert payload["idle_settle"]["eligible_idle_opportunity_seconds"] == 12.0
    assert payload["idle_settle"]["idle_seconds_never_enforce"] is True


def test_enforce_fails_dishonest_idle_disposition(tmp_path: Path, capsys) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    store = tmp_path / "idle.jsonl"
    store.write_text(
        json.dumps(
            {
                "schema": "fleet-idle-settle-event.v1",
                "outcome": "disposed",
                "disposition": "no_ready_work",
                "eligible": True,
                "reminder_fired": False,
                "opportunity_seconds_since_prev": 0.0,
                "disposition_honest": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--json",
            "--idle-store",
            str(store),
        ]
    )
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["idle_settle"]["enforce_fail_codes"] == ["DISHONEST"]
    assert payload["idle_settle"]["settle_events_dishonest"] == 1


def test_enforce_passes_honest_disposition_despite_idle_seconds(tmp_path: Path, capsys) -> None:
    """Authorized idle is not a failure; huge opportunity-seconds must not trip --enforce."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    store = tmp_path / "idle.jsonl"
    store.write_text(
        json.dumps(
            {
                "schema": "fleet-idle-settle-event.v1",
                "outcome": "disposed",
                "disposition": "human_decision",
                "eligible": True,
                "reminder_fired": False,
                "opportunity_seconds_since_prev": 86400.0,
                "disposition_honest": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--json",
            "--idle-store",
            str(store),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["idle_settle"]["enforce_fail_codes"] == []
    assert payload["idle_settle"]["eligible_idle_opportunity_seconds"] == 86400.0
    assert payload["idle_settle"]["idle_seconds_never_enforce"] is True


def test_note_file_does_not_waive_missing_disposition(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    note = tmp_path / "note.md"
    note.write_text("NOTE: fleet_breadth — language-lane only this session\n", encoding="utf-8")
    store = tmp_path / "idle.jsonl"
    store.write_text(
        json.dumps({"schema": "fleet-idle-settle-event.v1", "outcome": "missing_action"}) + "\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--note-file",
            str(note),
            "--idle-store",
            str(store),
            "--json",
        ]
    )
    assert code == 2


def test_enforce_without_idle_store_stays_breadth_only(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    missing = tmp_path / "absent.jsonl"
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--json",
            "--idle-store",
            str(missing),
        ]
    )
    assert code == 0


def test_breadth_report_embeds_admission_wip(tmp_path: Path, capsys) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _diverse_tasks(tasks_dir)
    snap = tmp_path / "snap.json"
    snap.write_text(
        json.dumps(
            {
                "lanes": [{"lane": "cursor", "status": "cool", "in_flight": 0, "will_last": True}],
                "items": [{"item_id": "issue:6998", "ready": True, "valuable": True, "independent": True}],
                "caps": {"authoring_in_flight": 2, "authoring_wip_limit": 2},
            }
        ),
        encoding="utf-8",
    )
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--json",
            "--idle-snapshot-json",
            str(snap),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    admission = payload["admission"]
    assert admission["schema"] == "fleet-admission.v1"
    assert admission["admitted"] is False
    assert admission["queue_ready"] is True
    assert "authoring_wip_cap" in admission["reason_codes"]
    assert admission["wip"]["authoring"]["reason_code"] == "authoring_wip_cap"
