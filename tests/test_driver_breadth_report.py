"""Tests for scripts.fleet.driver_breadth_report."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.fleet.driver_breadth_report import _tier_for, build_report, load_tasks, main


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
    started = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    payload = {
        "task_id": task_id,
        "agent": agent,
        "model": model,
        "initiator": initiator,
        "status": status,
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_s": 10,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_tier_for_gemini_flash_high_is_practical() -> None:
    """CF F1: bare 'flash' must not map gemini-3.6-flash-high to heap."""
    assert _tier_for("agy", "gemini-3.6-flash-high") == "practical"
    assert _tier_for("gemini", "gemini-3.6-flash-high") == "practical"
    # Bare flash / mini tokens still heap when not -high.
    assert _tier_for("agy", "gemini-2.0-flash") == "heap"
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
    tasks = load_tasks(tasks_dir, initiator_prefix="grok", since=datetime.now(timezone.utc) - timedelta(hours=24))
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
    tasks = load_tasks(tasks_dir, initiator_prefix="grok", since=datetime.now(timezone.utc) - timedelta(hours=24))
    report = build_report(tasks)
    assert report["distinct_agents"] >= 2
    assert report["tiers"].get("heap", 0) >= 1  # luna
    assert report["breadth_floor_ok"] is True


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
    code = main(
        [
            "--tasks-dir",
            str(tasks_dir),
            "--initiator",
            "grok",
            "--enforce",
            "--note-file",
            str(note),
            "--json",
        ]
    )
    assert code == 0
