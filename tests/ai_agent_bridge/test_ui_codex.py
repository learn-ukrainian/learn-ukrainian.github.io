from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.ai_agent_bridge import _ui_codex as ui_codex

THREAD_ID = "019e6063-c3da-78d1-acaa-4cd684a08786"


def _patch_codex_sessions_root(monkeypatch, tmp_path: Path) -> Path:
    sessions_root = tmp_path / ".codex" / "sessions"
    monkeypatch.setattr(ui_codex, "CODEX_SESSIONS_ROOT", sessions_root)
    return sessions_root


def test_find_session_file_happy_path_and_missing(tmp_path: Path, monkeypatch) -> None:
    sessions_root = _patch_codex_sessions_root(monkeypatch, tmp_path)
    day_dir = sessions_root / "2026" / "05" / "26"
    day_dir.mkdir(parents=True)
    older_session = day_dir / f"rollout-2026-05-26T10-00-00-{THREAD_ID}.jsonl"
    older_session.write_text("older\n", encoding="utf-8")
    newer_session = day_dir / f"rollout-2026-05-26T12-00-00-{THREAD_ID}.jsonl"
    newer_session.write_text("newer\n", encoding="utf-8")

    assert ui_codex.find_session_file(THREAD_ID) == newer_session
    assert ui_codex.find_session_file("00000000-0000-0000-0000-000000000000") is None


def test_extract_final_message_from_synthetic_codex_event_stream() -> None:
    events = [
        {
            "type": "item.completed",
            "item": {"type": "command_execution", "aggregated_output": "echo intermediate"},
        },
        {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": "final answer text"},
        },
    ]
    assert ui_codex._extract_final_message(events) == "final answer text"


def test_extract_final_message_fallback_to_command_output() -> None:
    events = [
        {
            "type": "item.completed",
            "item": {"type": "command_execution", "aggregated_output": "PONG 123"},
        },
    ]
    assert ui_codex._extract_final_message(events) == "PONG 123"


def test_send_disables_apps_connector_in_final_argv(tmp_path: Path, monkeypatch) -> None:
    """Dispatched UI resume spawn must unconditionally include --disable apps (#7202, #7181)."""
    captured_cmds: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(ui_codex.subprocess, "run", fake_run)

    result = ui_codex.send(
        thread_id=THREAD_ID,
        message="ping",
        bridge_id="bridge-test-7202",
        cwd=tmp_path,
        timeout_s=30,
    )

    assert result["exit_code"] == 0
    assert len(captured_cmds) == 1
    final_argv = captured_cmds[0]
    assert final_argv == ["codex", "exec", "resume", "--json", "--disable", "apps", THREAD_ID, "-"]
    disable_indices = [i for i, token in enumerate(final_argv[:-1]) if token == "--disable"]
    assert len(disable_indices) == 1
    assert final_argv[disable_indices[0] + 1] == "apps"


def test_send_with_mocked_subprocess_parses_stdout_event_stream(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sessions_root = _patch_codex_sessions_root(monkeypatch, tmp_path)
    day_dir = sessions_root / "2026" / "05" / "26"
    day_dir.mkdir(parents=True)
    session = day_dir / f"rollout-2026-05-26T12-00-00-{THREAD_ID}.jsonl"
    session.write_text("session data\n", encoding="utf-8")

    stdout = "\n".join(
        [
            json.dumps({"type": "turn.started"}),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "Known reply"},
                }
            ),
        ]
    )

    def fake_run(cmd, **kwargs):
        assert cmd == ["codex", "exec", "resume", "--json", "--disable", "apps", THREAD_ID, "-"]
        assert kwargs["input"].startswith("Bridge-ID: bridge-parse-test\n\nhello from bridge")
        assert kwargs["cwd"] == str(tmp_path)
        assert kwargs["timeout"] == 60
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(ui_codex.subprocess, "run", fake_run)

    result = ui_codex.send(
        thread_id=THREAD_ID,
        message="hello from bridge",
        bridge_id="bridge-parse-test",
        cwd=tmp_path,
        timeout_s=60,
    )

    assert result["bridge_id"] == "bridge-parse-test"
    assert result["thread_id"] == THREAD_ID
    assert result["exit_code"] == 0
    assert result["final_message"] == "Known reply"
    assert len(result["events"]) == 2
    assert result["session_file"] == str(session)


def test_send_handles_timeout_expired(tmp_path: Path, monkeypatch) -> None:
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=5, output=b"", stderr=b"hung")

    monkeypatch.setattr(ui_codex.subprocess, "run", fake_run)

    result = ui_codex.send(
        thread_id=THREAD_ID,
        message="timed out task",
        timeout_s=5,
    )

    assert result["exit_code"] == -1
    assert "[timeout after 5s]" in result["stderr"]
    assert "hung" in result["stderr"]
