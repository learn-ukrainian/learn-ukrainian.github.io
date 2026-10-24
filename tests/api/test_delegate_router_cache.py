"""Regressions for task-summary freshness and SQLite cache isolation."""

from __future__ import annotations

import json
import os

from scripts.api import delegate_router, state_router


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
