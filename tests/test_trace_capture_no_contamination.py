from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter


def test_gemini_session_does_not_leak_across_invocations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "learn-ukrainian"
    chats = home / ".gemini" / "tmp" / cwd.name / "chats"
    chats.mkdir(parents=True)
    cwd.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("GEMINI_AUTH_MODE", "subscription")

    previous = chats / "session-previous.json"
    previous.write_text(
        json.dumps({
            "messages": [
                {"type": "user", "content": [{"text": "PREVIOUS PLAN"}]},
                {
                    "type": "tool_call",
                    "name": "mcp__sources__stale",
                    "arguments": {"query": "old"},
                },
                {"type": "gemini", "content": "Previous answer."},
            ],
        }),
        encoding="utf-8",
    )

    prompt = "CURRENT PLAN: write this module."
    adapter = GeminiAdapter()
    plan = adapter.build_invocation(
        prompt=prompt,
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    current = chats / "session-current.json"
    current.write_text(
        json.dumps({
            "messages": [
                {"type": "user", "content": [{"text": prompt}]},
                {
                    "type": "tool_call",
                    "name": "mcp__sources__current",
                    "arguments": {"query": "new"},
                },
                {"type": "gemini", "content": "Current answer."},
            ],
        }),
        encoding="utf-8",
    )
    newer_mtime = time.time() + 10
    os.utime(previous, (newer_mtime, newer_mtime))

    trace = adapter._read_latest_session_trace(plan)

    assert "mcp__sources__current" in trace
    assert "mcp__sources__stale" not in trace


def test_codex_prompt_echo_does_not_appear_in_tool_calls(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")
    stderr = "\n".join([
        "User prompt:",
        '{"type":"tool_call","name":"mcp__sources__prompt_echo",'
        '"arguments":{"query":"example from instructions"}}',
    ])

    result = CodexAdapter().parse_response(
        stdout="",
        stderr=stderr,
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert result.tool_calls == []


def test_claude_text_output_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="output_format='stream-json'"):
        ClaudeAdapter().build_invocation(
            prompt="hello",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"cmd_prefix": ["true"], "output_format": "text"},
        )


def test_codex_rollout_trace_still_records_real_tool_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    today = datetime.now(UTC)
    rollout_dir = (
        home
        / ".codex"
        / "sessions"
        / f"{today.year:04d}"
        / f"{today.month:02d}"
        / f"{today.day:02d}"
    )
    rollout_dir.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home)

    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")
    prompt = "Write the module."
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt=prompt,
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )

    (rollout_dir / "rollout-current.jsonl").write_text(
        "\n".join([
            json.dumps({
                "type": "event_msg",
                "payload": {"type": "user_message", "message": prompt},
            }),
            json.dumps({
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "mcp__sources__verify_words",
                    "arguments": {"words": ["день"]},
                    "call_id": "call-1",
                },
            }),
        ]),
        encoding="utf-8",
    )

    result = adapter.parse_response(
        stdout="",
        stderr='{"type":"tool_call","name":"mcp__sources__prompt_echo"}',
        returncode=0,
        output_file=output_file,
        plan=plan,
    )

    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__verify_words"
    ]
