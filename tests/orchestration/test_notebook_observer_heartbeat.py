"""Notebook heartbeat marker, resolver, and GUI honesty fixtures."""

from __future__ import annotations

import json

from scripts.api.telemetry.transcript_tokens import TranscriptTelemetry
from scripts.orchestration import observer_heartbeat
from scripts.orchestration.session_markers import write_session_marker


class _Response:
    def __init__(self, body: dict[str, object]) -> None:
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_marker_sweep_posts_working_telemetry_without_local_details(monkeypatch, tmp_path) -> None:
    session_id = "123e4567-e89b-12d3-a456-426614174000"
    write_session_marker(
        agent="claude",
        harness="claude-code",
        instance_id=session_id,
        epic="7177",
        task_id="7189",
        pid=1234,
        root=tmp_path,
    )
    monkeypatch.setattr(
        observer_heartbeat,
        "session_context_telemetry",
        lambda *args, **kwargs: TranscriptTelemetry(12345, 12000, 3, tmp_path / "private.jsonl"),
    )
    monkeypatch.setattr(
        observer_heartbeat,
        "read_session_record",
        lambda *args, **kwargs: {"actual_context_window_tokens": 272000},
    )
    posted: list[dict[str, object]] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        body = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        posted.append(body)
        return _Response({"host_id": "mac-operator"})

    rows = observer_heartbeat.sweep_session_markers(
        repo_root=tmp_path,
        marker_root=tmp_path,
        host_id="mac-operator",
        pid_alive=lambda pid: pid == 1234,
        opener=opener,
    )
    assert len(rows) == 1
    assert posted == [
        {
            "agent": "claude",
            "kind": "observer",
            "task_id": "7189",
            "status": "working",
            "epic": "7177",
            "summary": "Notebook session",
            "host_id": "mac-operator",
            "instance_id": session_id,
            "ctx_tokens": 12345,
            "window_tokens": 272000,
        }
    ]
    wire = json.dumps(posted)
    assert "private.jsonl" not in wire
    assert "pid" not in wire
    assert "mac-operator" in wire


def test_gui_process_is_idle_and_uses_gui_instance(monkeypatch) -> None:
    posted: list[dict[str, object]] = []

    def opener(request: object, timeout: int = 0) -> _Response:
        del timeout
        body = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        posted.append(body)
        return _Response({"host_id": "mac-operator"})

    observer_heartbeat.sweep_mac_gui_presence(
        process_lines=["/Applications/Cursor.app/Contents/MacOS/Cursor"],
        host_id="mac-operator",
        status="working",
        opener=opener,
    )
    assert posted == [
        {
            "agent": "cursor",
            "kind": "observer",
            "task_id": "cursor-gui",
            "status": "idle",
            "summary": "GUI session",
            "host_id": "mac-operator",
            "instance_id": "gui",
        }
    ]
