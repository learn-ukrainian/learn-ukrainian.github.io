"""Regressions for task-summary freshness and SQLite cache isolation."""

from __future__ import annotations

import json
import os
import sqlite3

from scripts.api import delegate_router, state_router
from scripts.api.monitor_context import fixture_context


def test_restored_mtime_does_not_label_stale_in_flight_counts_with_fresh_generation(tmp_path, monkeypatch):
    """A restored mtime must not hide an in-place rewrite from routing's refresh."""
    monkeypatch.setattr(delegate_router, "_TASK_STATE_CACHE", {})
    monkeypatch.setattr(delegate_router, "_LAST_TASKS_DIR_STR", "")
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    task = tasks_dir / "task.json"
    task.write_text(json.dumps({"task_id": "task", "agent": "codex", "status": "spawning"}))
    before = task.stat()

    first_generation = []
    assert state_router._in_flight_by_agent(tasks_dir, task_generation=first_generation)["codex"] == 1
    assert first_generation == [state_router._tasks_content_token(tasks_dir)]

    task.write_text(json.dumps({"task_id": "task", "agent": "codex", "status": "done"}))
    os.utime(task, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert task.stat().st_mtime_ns == before.st_mtime_ns

    refreshed_generation = []
    refreshed = state_router._in_flight_by_agent(tasks_dir, task_generation=refreshed_generation)
    # This is the equality routing uses to accept refreshed counts as fresh.
    assert refreshed_generation == [state_router._tasks_content_token(tasks_dir)]
    assert refreshed_generation != first_generation
    assert refreshed["codex"] == 0


def test_db_skipping_scan_does_not_suppress_persistence_or_vanished_row_deletion(tmp_path, monkeypatch):
    """Directory-only scans must not poison a later scan's SQLite updates."""
    monkeypatch.setattr(delegate_router, "_TASK_STATE_CACHE", {})
    monkeypatch.setattr(delegate_router, "_LAST_TASKS_DIR_STR", "")
    ctx = fixture_context(tmp_path)
    tasks_dir = ctx.roots.batch_state_dir / "tasks"
    tasks_dir.mkdir(parents=True)
    vanished = tasks_dir / "vanished.json"
    vanished.write_text(json.dumps({"task_id": "vanished", "status": "done"}))
    assert delegate_router.list_delegate_tasks(ctx=ctx)["total"] == 1
    db_path = tasks_dir / ".task_cache.sqlite3"
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("SELECT task_id FROM task_cache").fetchall() == [("vanished",)]

    vanished.unlink()
    added = tasks_dir / "added.json"
    added.write_text(json.dumps({"task_id": "added", "status": "done"}))
    assert [row["task_id"] for row in delegate_router._delegate_task_rows(tasks_dir=tasks_dir)] == ["added"]
    # The directory-only scan must leave the persistent index untouched.
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("SELECT task_id FROM task_cache").fetchall() == [("vanished",)]

    assert delegate_router.list_delegate_tasks(ctx=ctx)["tasks"][0]["task_id"] == "added"
    with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("SELECT task_id, status FROM task_cache ORDER BY task_id").fetchall() == [
            ("added", "done"),
        ]
