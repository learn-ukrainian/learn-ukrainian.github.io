"""Loopback observer heartbeat helper (#7075)."""

from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from scripts.orchestration.observer_heartbeat import (
    HeartbeatError,
    main,
    post_observer_presence,
    presence_url,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_presence_url_rejects_non_loopback() -> None:
    with pytest.raises(HeartbeatError):
        presence_url("http://example.com:8765")
    with pytest.raises(HeartbeatError):
        presence_url("http://[::1]:8765")
    with pytest.raises(HeartbeatError):
        presence_url("http://127.0.0.1:atlas-runner")
    with pytest.raises(HeartbeatError):
        presence_url("http://[::1")


def test_post_observer_presence_posts_cursor_payload() -> None:
    captured: dict[str, object] = {}

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        captured["url"] = getattr(request, "full_url", None)
        captured["body"] = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        return _FakeResponse(
            {
                "agent": "cursor",
                "task_id": "7075",
                "status": "working",
                "host_id": "cloud-observer",
            }
        )

    row = post_observer_presence(
        agent="cursor",
        task_id="7075",
        epic="7073",
        summary="cursor driver occupancy heartbeat",
        opener=opener,
    )
    assert captured["url"] == "http://127.0.0.1:8765/api/observer/presence"
    assert captured["body"] == {
        "agent": "cursor",
        "kind": "observer",
        "task_id": "7075",
        "status": "working",
        "epic": "7073",
        "summary": "cursor driver occupancy heartbeat",
    }
    assert row["agent"] == "cursor"
    assert row["host_id"] == "cloud-observer"


def test_post_observer_presence_does_not_echo_response_text() -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        return _FakeResponse({"agent": "atlas-runner", "task_id": "see unexpected-data", "status": "working"})

    row = post_observer_presence(agent="cursor", task_id="7075", opener=opener)
    assert row == {"agent": "cursor", "task_id": "7075", "status": "working", "host_id": None}


def test_main_prints_opaque_ack_only(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        return _FakeResponse({"agent": "cursor", "task_id": "7075", "status": "working"})

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert main(["--agent", "cursor", "--task-id", "7075", "--status", "working"]) == 0
    out = capsys.readouterr().out
    assert "agent=cursor" in out
    assert "127.0.0.1" not in out
    assert "atlas-runner" not in out


def test_main_fail_open_message_on_unreachable(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        raise URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert main(["--agent", "cursor", "--task-id", "7075"]) == 1
    err = capsys.readouterr().err
    assert "monitor unreachable" in err
    assert "127.0.0.1" not in err


def test_main_malformed_port_does_not_print_alias(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "http://127.0.0.1:atlas-runner")
    assert main(["--agent", "cursor", "--task-id", "7075"]) == 2
    err = capsys.readouterr().err
    assert "monitor URL must be http loopback" in err
    assert "atlas-runner" not in err
    assert "Traceback" not in err


def test_main_timeout_is_unreachable(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        raise TimeoutError("stalled")

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert main(["--agent", "cursor", "--task-id", "7075"]) == 1
    err = capsys.readouterr().err
    assert "monitor unreachable" in err
    assert "Traceback" not in err
    assert "stalled" not in err


def test_post_observer_presence_posts_codex_payload() -> None:
    captured: dict[str, object] = {}

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        captured["url"] = getattr(request, "full_url", None)
        captured["body"] = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        return _FakeResponse(
            {
                "agent": "codex",
                "task_id": "7104",
                "status": "idle",
                "host_id": "cloud-observer",
            }
        )

    row = post_observer_presence(
        agent="codex",
        task_id="7104",
        status="idle",
        epic="7073",
        summary="codex ui mac observer heartbeat",
        opener=opener,
    )
    assert captured["url"] == "http://127.0.0.1:8765/api/observer/presence"
    assert captured["body"] == {
        "agent": "codex",
        "kind": "observer",
        "task_id": "7104",
        "status": "idle",
        "epic": "7073",
        "summary": "codex ui mac observer heartbeat",
    }
    assert row["agent"] == "codex"
    assert row["task_id"] == "7104"
    assert row["status"] == "idle"
    assert row["host_id"] == "cloud-observer"


def test_post_observer_presence_rejects_unknown_agent_fail_closed() -> None:
    for unknown in ("claude", "gemini", "atlas-runner", "hramatka", "custom"):
        with pytest.raises(HeartbeatError, match="unknown observer agent"):
            post_observer_presence(agent=unknown, task_id="7104")


def test_post_observer_presence_rejects_invalid_status() -> None:
    for invalid in ("running", "done", "active", "offline", "unknown"):
        with pytest.raises(HeartbeatError, match="invalid status"):
            post_observer_presence(agent="cursor", task_id="7104", status=invalid)


def test_main_rejects_unknown_agent_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--agent", "claude", "--task-id", "7104"]) == 2
    err = capsys.readouterr().err
    assert "unknown observer agent" in err


def test_main_missing_required_args_fail_closed(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "--agent and --task-id are required" in err


def test_detect_mac_gui_session_cursor_and_codex() -> None:
    from scripts.orchestration.observer_heartbeat import (
        detect_live_gui_agents,
        detect_mac_gui_session,
        is_gui_process_for_agent,
    )

    cursor_processes = [
        "/Applications/Cursor.app/Contents/MacOS/Cursor",
        "/Applications/Cursor.app/Contents/Frameworks/Cursor Helper (Renderer).app/Contents/MacOS/Cursor Helper (Renderer)",
        "/usr/bin/bash",
    ]
    codex_processes = [
        "/Applications/Codex.app/Contents/MacOS/Codex",
        "/Applications/Codex.app/Contents/Frameworks/Codex Helper.app/Contents/MacOS/Codex Helper",
        "/usr/bin/python",
    ]
    both_processes = cursor_processes + codex_processes
    neither_processes = ["/usr/bin/bash", "/usr/bin/python", "/usr/bin/git", "node"]

    assert detect_mac_gui_session("cursor", process_lines=cursor_processes) is True
    assert detect_mac_gui_session("codex", process_lines=cursor_processes) is False

    assert detect_mac_gui_session("codex", process_lines=codex_processes) is True
    assert detect_mac_gui_session("cursor", process_lines=codex_processes) is False

    assert detect_live_gui_agents(process_lines=both_processes) == ["cursor", "codex"]
    assert detect_live_gui_agents(process_lines=neither_processes) == []

    # Direct process pattern unit checks
    assert is_gui_process_for_agent("cursor", "/Applications/Cursor.app/Contents/MacOS/Cursor") is True
    assert is_gui_process_for_agent("cursor", "Cursor") is True
    assert is_gui_process_for_agent("cursor", "Cursor Helper") is True
    assert is_gui_process_for_agent("cursor", "python scripts/orchestration/observer_heartbeat.py") is False

    assert is_gui_process_for_agent("codex", "/Applications/Codex.app/Contents/MacOS/Codex") is True
    assert is_gui_process_for_agent("codex", "Codex") is True
    assert is_gui_process_for_agent("codex", "codex-ui") is True
    assert is_gui_process_for_agent("codex", "codex exec") is False


def test_detect_mac_gui_session_rejects_unknown_agent() -> None:
    from scripts.orchestration.observer_heartbeat import detect_mac_gui_session

    with pytest.raises(HeartbeatError, match="unknown observer agent"):
        detect_mac_gui_session("claude", process_lines=[])


def test_sweep_mac_gui_presence() -> None:
    from scripts.orchestration.observer_heartbeat import sweep_mac_gui_presence

    posted_bodies: list[dict[str, object]] = []

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        body = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        posted_bodies.append(body)
        return _FakeResponse(
            {
                "agent": body["agent"],
                "task_id": body["task_id"],
                "status": body["status"],
                "host_id": "cloud-observer",
            }
        )

    # When both Cursor and Codex are running
    lines = [
        "/Applications/Cursor.app/Contents/MacOS/Cursor",
        "/Applications/Codex.app/Contents/MacOS/Codex",
    ]
    results = sweep_mac_gui_presence(
        opener=opener,
        process_lines=lines,
        cursor_task_id="cursor-gui",
        codex_task_id="codex-gui",
        status="idle",
    )
    assert len(results) == 2
    assert {r["agent"] for r in results} == {"cursor", "codex"}
    assert {b["agent"] for b in posted_bodies} == {"cursor", "codex"}
    for b in posted_bodies:
        assert b["status"] == "idle"

    # When neither is running -> omits heartbeats
    posted_bodies.clear()
    results_empty = sweep_mac_gui_presence(
        opener=opener,
        process_lines=["/usr/bin/bash"],
    )
    assert results_empty == []
    assert posted_bodies == []


def test_main_mac_gui_mode_posts_idle_for_running_gui(capsys: pytest.CaptureFixture[str]) -> None:
    posted: list[dict[str, object]] = []

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        body = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        posted.append(body)
        return _FakeResponse(
            {
                "agent": body["agent"],
                "task_id": body["task_id"],
                "status": body["status"],
                "host_id": "cloud-observer",
            }
        )

    lines = ["/Applications/Cursor.app/Contents/MacOS/Cursor"]
    rc = main(["--mac-gui"], opener=opener, process_lines=lines)
    assert rc == 0
    assert len(posted) == 1
    assert posted[0]["agent"] == "cursor"
    assert posted[0]["task_id"] == "cursor-gui"
    assert posted[0]["status"] == "idle"
    out = capsys.readouterr().out
    assert "agent=cursor task_id=cursor-gui status=idle" in out


def test_main_mac_gui_mode_noop_when_not_running(capsys: pytest.CaptureFixture[str]) -> None:
    posted: list[dict[str, object]] = []

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        posted.append({})
        return _FakeResponse({})

    rc = main(["--mac-gui"], opener=opener, process_lines=["/usr/bin/bash"])
    assert rc == 0
    assert posted == []
    out = capsys.readouterr().out
    assert "no live mac gui sessions detected" in out
