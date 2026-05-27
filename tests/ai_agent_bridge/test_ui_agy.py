from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.ai_agent_bridge import _ui_agy as ui_agy

THREAD_ID = "48fd721e-a259-438c-9eb9-53b0fd271c11"


def _patch_agy_roots(monkeypatch, tmp_path: Path) -> Path:
    app_data = tmp_path / "antigravity-cli"
    monkeypatch.setattr(ui_agy, "AGY_APP_DATA_ROOT", app_data)
    monkeypatch.setattr(ui_agy, "AGY_CONVERSATIONS_ROOT", app_data / "conversations")
    return app_data


def _write_transcript_events(app_data: Path, events: list[dict]) -> Path:
    transcript = (
        app_data
        / "brain"
        / THREAD_ID
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )
    return transcript


def test_find_session_file_happy_path_and_missing(tmp_path: Path, monkeypatch) -> None:
    app_data = _patch_agy_roots(monkeypatch, tmp_path)
    conversations = app_data / "conversations"
    conversations.mkdir(parents=True)
    session = conversations / f"{THREAD_ID}.pb"
    session.write_bytes(b"probe")

    assert ui_agy.find_session_file(THREAD_ID) == session
    assert ui_agy.find_session_file("00000000-0000-0000-0000-000000000000") is None


def test_extract_final_message_from_synthetic_agy_event_stream() -> None:
    events = [
        {"type": "USER_INPUT", "content": "question"},
        {"type": "PLANNER_RESPONSE", "content": "first answer"},
        {"type": "MODEL_RESPONSE", "content": "final answer"},
    ]

    assert ui_agy._extract_final_message(events) == "final answer"


def test_send_with_mocked_subprocess_parses_stdout_event_stream(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app_data = _patch_agy_roots(monkeypatch, tmp_path)
    monkeypatch.setattr(ui_agy.tempfile, "gettempdir", lambda: "/tmp")
    conversations = app_data / "conversations"
    conversations.mkdir(parents=True)
    session = conversations / f"{THREAD_ID}.pb"
    session.write_bytes(b"probe")

    stdout = "\n".join(
        [
            json.dumps({"type": "USER_INPUT", "content": "Bridge prompt"}),
            json.dumps({"type": "PLANNER_RESPONSE", "content": "known final"}),
        ]
    )

    def fake_run(cmd, **kwargs):
        assert cmd[:6] == [
            "agy",
            "--print-timeout",
            "12s",
            "--dangerously-skip-permissions",
            "--log-file",
            str(Path("/tmp") / "agy-ui-bridge-bridge-test.log"),
        ]
        assert cmd[6:8] == ["--conversation", THREAD_ID]
        assert cmd[8] == "--print"
        assert cmd[9].startswith("Bridge-ID: bridge-test\n\n")
        assert kwargs["cwd"] == str(tmp_path)
        assert kwargs["timeout"] == 12
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(ui_agy.subprocess, "run", fake_run)

    result = ui_agy.send(
        thread_id=THREAD_ID,
        message="hello",
        bridge_id="bridge-test",
        cwd=tmp_path,
        timeout_s=12,
    )

    assert result["bridge_id"] == "bridge-test"
    assert result["thread_id"] == THREAD_ID
    assert result["exit_code"] == 0
    assert result["final_message"] == "known final"
    assert result["session_file"] == str(session)
    assert len(result["events"]) == 2


def test_send_uses_only_current_transcript_events(tmp_path: Path, monkeypatch) -> None:
    app_data = _patch_agy_roots(monkeypatch, tmp_path)
    monkeypatch.setattr(ui_agy.tempfile, "gettempdir", lambda: str(tmp_path))
    _write_transcript_events(
        app_data,
        [{"type": "PLANNER_RESPONSE", "content": "stale previous answer"}],
    )

    def fake_run(cmd, **kwargs):
        log_path = Path(cmd[5])
        log_path.write_text(
            f"Print mode: conversation={THREAD_ID}, sending message\n",
            encoding="utf-8",
        )
        _write_transcript_events(
            app_data,
            [
                {"type": "PLANNER_RESPONSE", "content": "stale previous answer"},
                {"type": "PLANNER_RESPONSE", "content": "current answer"},
            ],
        )
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="stale previous answer\ncurrent answer\n",
            stderr="",
        )

    monkeypatch.setattr(ui_agy.subprocess, "run", fake_run)

    result = ui_agy.send(
        thread_id=THREAD_ID,
        message="hello",
        bridge_id="bridge-current",
        cwd=tmp_path,
        timeout_s=12,
    )

    assert result["final_message"] == "current answer"
    assert result["events"] == [{"type": "PLANNER_RESPONSE", "content": "current answer"}]
    assert not (tmp_path / "agy-ui-bridge-bridge-current.log").exists()


def test_send_timeout_returns_negative_exit_code(tmp_path: Path, monkeypatch) -> None:
    app_data = _patch_agy_roots(monkeypatch, tmp_path)
    _write_transcript_events(
        app_data,
        [{"type": "PLANNER_RESPONSE", "content": "stale previous answer"}],
    )

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=cmd,
            timeout=3,
            output="partial stdout",
            stderr=b"partial stderr",
        )

    monkeypatch.setattr(ui_agy.subprocess, "run", fake_run)

    result = ui_agy.send(
        thread_id=THREAD_ID,
        message="hello",
        bridge_id="bridge-timeout",
        cwd=tmp_path,
        timeout_s=3,
    )

    assert result["exit_code"] == -1
    assert result["final_message"] == "partial stdout"
    assert result["events"] == [{"type": "stdout_text", "content": "partial stdout"}]
    assert result["stderr"].startswith("[timeout after 3s]")
    assert "partial stderr" in result["stderr"]


def test_cli_main_reads_message_from_file(tmp_path: Path, monkeypatch, capsys) -> None:
    message_file = tmp_path / "relay.md"
    message_file.write_text("from file", encoding="utf-8")
    captured: dict = {}

    def fake_send(**kwargs):
        captured.update(kwargs)
        return {
            "bridge_id": "bridge-file",
            "thread_id": THREAD_ID,
            "exit_code": 0,
            "events": [{"type": "PLANNER_RESPONSE", "content": "ok"}],
            "final_message": "ok",
            "duration_s": 0.1,
            "session_file": "/tmp/session.pb",
            "stderr": "",
        }

    monkeypatch.setattr(ui_agy, "send", fake_send)

    rc = ui_agy.cli_main(
        ["--thread", THREAD_ID, "--from-file", str(message_file), "--json"]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert captured["thread_id"] == THREAD_ID
    assert captured["message"] == "from file"
    assert out["event_count"] == 1
