"""Contracts for fail-open behavior of Claude and Cursor Entire hooks, and updated inbox instruction."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from scripts.entire import cursor_native_hook_shim as cursor_shim

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-gemini-inbox.sh"
CURSOR_SHIM_SCRIPT = REPO_ROOT / "scripts" / "entire" / "cursor_native_hook_shim.py"


def _claude_entire_hooks() -> list[dict]:
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    needle = "entire hooks claude-code"
    return [
        hook
        for event in settings["hooks"]
        for entry in settings["hooks"][event]
        for hook in entry.get("hooks", [])
        if needle in hook.get("command", "")
    ]


def _make_fake_entire_cli(directory: Path, *, exit_code: int = 1) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    fake_cli = directory / "entire"
    fake_cli.write_text(
        "#!/bin/sh\n"
        "echo 'failed to parse hook event: empty hook input' >&2\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)
    return fake_cli


def _make_inbox_db(tmp_path: Path) -> Path:
    db_path = tmp_path / ".mcp" / "servers" / "message-broker" / "messages.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_llm TEXT,
                to_llm TEXT,
                message_type TEXT,
                task_id TEXT,
                content TEXT,
                timestamp TEXT,
                acknowledged INTEGER,
                claimed_by TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO messages
                (from_llm, to_llm, message_type, task_id, content, timestamp,
                 acknowledged, claimed_by)
            VALUES (?, ?, 'status', 'hooks', ?, '2026-07-26T00:00:00Z', 0, NULL)
            """,
            [
                ("claude", "codex", "codex-targeted unread payload"),
                ("codex", "claude", "claude-targeted unread payload"),
                ("claude", "gemini", "gemini-targeted unread payload"),
            ],
        )
    return db_path


def test_claude_entire_hooks_manifest_structure() -> None:
    """Claude settings should have 7 composed Entire hooks without exec and ending with || true."""
    hooks = _claude_entire_hooks()
    assert len(hooks) == 7

    verbs = {
        re.search(r"entire hooks claude-code (\S+)", hook["command"]).group(1)
        for hook in hooks
    }
    assert verbs == {
        "session-start",
        "pre-task",
        "post-task",
        "post-todo",
        "user-prompt-submit",
        "stop",
        "session-end",
    }
    assert all(hook["timeout"] == 30 for hook in hooks)
    assert all("if ! command -v entire" in hook["command"] for hook in hooks)
    assert all("exec entire" not in hook["command"] for hook in hooks)
    assert all(hook["command"].endswith("|| true'") for hook in hooks)


def test_claude_entire_hooks_fail_open_when_cli_errors(tmp_path: Path) -> None:
    """Every Claude Entire hook command exits 0 when a fake entire on PATH exits 1."""
    fake_bin = tmp_path / "bin"
    _make_fake_entire_cli(fake_bin, exit_code=1)
    env = {"PATH": f"{fake_bin}:/usr/bin:/bin"}

    hooks = _claude_entire_hooks()
    assert len(hooks) == 7

    for hook in hooks:
        for stdin_data in ("", "{}\n", '{"event":"UserPromptSubmit"}\n'):
            result = subprocess.run(
                ["/bin/sh", "-c", hook["command"]],
                input=stdin_data,
                capture_output=True,
                text=True,
                check=False,
                env=env,
                timeout=5,
            )
            assert result.returncode == 0, (
                f"Hook {hook['command']} exited with {result.returncode} on stdin={stdin_data!r}"
            )


def test_cursor_stock_commands_fail_open_when_cli_errors(tmp_path: Path) -> None:
    """Stock Cursor hook commands must not exec and must exit 0 when entire on PATH exits 1."""
    fake_bin = tmp_path / "bin"
    _make_fake_entire_cli(fake_bin, exit_code=1)
    env = {"PATH": f"{fake_bin}:/usr/bin:/bin"}

    stock_commands = cursor_shim._STOCK_COMMANDS
    assert len(stock_commands) == 7

    for key, command in stock_commands.items():
        assert "exec entire" not in command, f"Stock command {key} still uses exec: {command}"
        assert command.endswith("|| true'"), f"Stock command {key} does not end with || true': {command}"

        for stdin_data in ("", "{}\n", '{"conversation_id":"c123"}\n'):
            result = subprocess.run(
                ["/bin/sh", "-c", command],
                input=stdin_data,
                capture_output=True,
                text=True,
                check=False,
                env=env,
                timeout=5,
            )
            assert result.returncode == 0, (
                f"Cursor stock command {key} exited with {result.returncode} on stdin={stdin_data!r}"
            )


def test_cursor_shim_commands_fail_open_when_cli_errors(tmp_path: Path) -> None:
    """Cursor shim invocation must fail open when entire on PATH exits 1."""
    fake_bin = tmp_path / "bin"
    _make_fake_entire_cli(fake_bin, exit_code=1)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '/usr/bin:/bin')}"

    for verb in ("session-start", "before-submit-prompt", "stop"):
        for stdin_data in ("", "{}\n", '{"conversation_id":"dummy"}\n'):
            result = subprocess.run(
                [sys.executable, str(CURSOR_SHIM_SCRIPT), verb],
                input=stdin_data,
                capture_output=True,
                text=True,
                check=False,
                env=env,
                cwd=str(REPO_ROOT),
                timeout=5,
            )
            assert result.returncode == 0, (
                f"Cursor shim {verb} exited with {result.returncode} on stdin={stdin_data!r}"
            )

    managed_commands = cursor_shim._MANAGED_COMMANDS
    for key, command in managed_commands.items():
        assert command.endswith("; exit 0'")
        for stdin_data in ("", "{}\n"):
            result = subprocess.run(
                ["/bin/sh", "-c", command],
                input=stdin_data,
                capture_output=True,
                text=True,
                check=False,
                env=env,
                cwd=str(REPO_ROOT),
                timeout=5,
            )
            assert result.returncode == 0, (
                f"Managed command {key} exited with {result.returncode} on stdin={stdin_data!r}"
            )


def test_inbox_hook_emits_provider_scoped_previews_and_live_inbox_instruction(tmp_path: Path) -> None:
    """Inbox hook must emit provider previews and live inbox command, never mcp__message-broker."""
    _make_inbox_db(tmp_path)

    test_cases = [
        ("claude", "CLAUDE INBOX: 1 unread message", "claude-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for claude"),
        ("codex", "CODEX INBOX: 1 unread message", "codex-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for codex"),
        ("gemini", "GEMINI INBOX: 1 unread message", "gemini-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for gemini"),
    ]

    for recipient, expected_header, expected_preview, expected_instruction in test_cases:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
        env["LEARN_UK_HOOK_RECIPIENT"] = recipient
        env.pop("LEARN_UK_HOOK_SESSION_ID", None)
        env.pop("LEARN_UKRAINIAN_SESSION_ID", None)
        env.pop("CODEX_THREAD_ID", None)
        env.pop("CODEX_SESSION_ID", None)

        completed = subprocess.run(
            ["bash", str(INBOX_HOOK)],
            input="{}",
            text=True,
            capture_output=True,
            check=False,
            env=env,
            timeout=10,
        )

        assert completed.returncode == 0, completed.stderr
        output = json.loads(completed.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        assert expected_header in context, f"Expected header '{expected_header}' missing in:\n{context}"
        assert expected_preview in context, f"Expected preview '{expected_preview}' missing in:\n{context}"
        assert expected_instruction in context, f"Expected instruction '{expected_instruction}' missing in:\n{context}"
        assert "mcp__message-broker" not in context, f"Retired MCP tool found in:\n{context}"


def test_inbox_hook_defaults_to_claude_recipient(tmp_path: Path) -> None:
    """When LEARN_UK_HOOK_RECIPIENT is unset, inbox hook defaults to claude."""
    _make_inbox_db(tmp_path)

    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    env.pop("LEARN_UK_HOOK_RECIPIENT", None)
    env.pop("LEARN_UK_HOOK_SESSION_ID", None)
    env.pop("LEARN_UKRAINIAN_SESSION_ID", None)
    env.pop("CODEX_THREAD_ID", None)
    env.pop("CODEX_SESSION_ID", None)

    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)
    context = output["hookSpecificOutput"]["additionalContext"]

    assert "CLAUDE INBOX: 1 unread message" in context
    assert ".venv/bin/python -m scripts.ai_agent_bridge inbox --for claude" in context
    assert "mcp__message-broker" not in context
