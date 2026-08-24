"""Fixture coverage for notebook session marker lifecycle and ghost cleanup."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from scripts.orchestration.session_markers import (
    MARKER_SCHEMA,
    iter_session_markers,
    remove_session_marker,
    write_session_marker,
)


def _stamp(delta: timedelta = timedelta()) -> str:
    return (datetime.now(UTC) + delta).isoformat().replace("+00:00", "Z")


def test_marker_write_read_and_pid_fenced_remove(tmp_path) -> None:
    path = write_session_marker(
        agent="claude",
        harness="claude-code",
        instance_id="session-7189",
        epic="7177",
        task_id="7189",
        pid=1234,
        started_at=_stamp(),
        root=tmp_path,
    )
    assert path == tmp_path / "session-7189.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {
        "schema": MARKER_SCHEMA,
        "agent": "claude",
        "harness": "claude-code",
        "instance_id": "session-7189",
        "epic": "7177",
        "task_id": "7189",
        "pid": 1234,
        "started_at": payload["started_at"],
    }
    assert all("path" not in key.lower() for key in payload)
    assert [marker.instance_id for marker in iter_session_markers(root=tmp_path, pid_alive=lambda pid: pid == 1234)] == [
        "session-7189"
    ]
    assert remove_session_marker("session-7189", root=tmp_path, expected_pid=9999) is False
    assert path.exists()
    assert remove_session_marker("session-7189", root=tmp_path, expected_pid=1234) is True
    assert not path.exists()


def test_dead_and_expired_markers_are_deleted(tmp_path) -> None:
    write_session_marker(
        agent="codex",
        harness="codex",
        instance_id="old-session",
        pid=1111,
        started_at=_stamp(timedelta(hours=-25)),
        root=tmp_path,
    )
    write_session_marker(
        agent="cursor",
        harness="cursor",
        instance_id="dead-session",
        pid=2222,
        started_at=_stamp(),
        root=tmp_path,
    )
    assert list(iter_session_markers(root=tmp_path, pid_alive=lambda pid: pid == 1111)) == []
    assert list(tmp_path.glob("*.json")) == []


def test_marker_rejects_path_like_identity(tmp_path) -> None:
    assert (
        write_session_marker(
            agent="claude",
            harness="claude-code",
            instance_id="../outside",
            pid=1234,
            root=tmp_path,
        )
        is None
    )
    assert list(tmp_path.iterdir()) == []
