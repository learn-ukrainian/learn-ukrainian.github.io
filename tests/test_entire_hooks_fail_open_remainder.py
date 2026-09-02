"""Contracts for fail-open behavior of Claude and Cursor Entire hooks, and updated inbox instruction."""

from __future__ import annotations

import json
import os
import re
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


def _make_fake_inbox_python(tmp_path: Path) -> tuple[Path, Path]:
    """Create a project interpreter that exposes only the live inbox CLI shape."""
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    fixtures = tmp_path / "inbox-fixtures"
    fixtures.mkdir()
    args_log = tmp_path / "inbox-cli-args.log"
    python.write_text(
        "#!/bin/sh\n"
        "if [ \"$#\" -ne 5 ] || [ \"$1\" != \"-m\" ] || [ \"$2\" != \"scripts.ai_agent_bridge\" ] || [ \"$3\" != \"inbox\" ] || [ \"$4\" != \"--for\" ]; then\n"
        "  exit 64\n"
        "fi\n"
        "if [ \"${FAKE_INBOX_FAIL:-0}\" = \"1\" ]; then\n"
        "  exit 1\n"
        "fi\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_INBOX_ARGS\"\n"
        "cat \"$FAKE_INBOX_FIXTURES/$5.txt\"\n",
        encoding="utf-8",
    )
    python.chmod(0o755)
    return fixtures, args_log


def _write_inbox_fixture(fixtures: Path, recipient: str, preview: str, *, message_id: int = 101) -> None:
    (fixtures / f"{recipient}.txt").write_text(
        f"📬 Inbox for {recipient}: 1 unread | 0 read-but-not-live-consumed | 0 live-consumed\n\n"
        f"  [{message_id}] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        f"      {preview}\n",
        encoding="utf-8",
    )


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
    source = INBOX_HOOK.read_text(encoding="utf-8")
    assert "sqlite3" not in source.lower()
    assert "messages.db" not in source
    assert ".mcp/servers/message-broker" not in source
    assert '"$PROJECT_DIR/.venv/bin/python" -m scripts.ai_agent_bridge inbox --for "$RECIPIENT"' in source
    fixtures, args_log = _make_fake_inbox_python(tmp_path)

    test_cases = [
        ("claude", "CLAUDE INBOX: 1 unread message", "claude-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for claude"),
        ("codex", "CODEX INBOX: 1 unread message", "codex-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for codex"),
        ("gemini", "GEMINI INBOX: 1 unread message", "gemini-targeted unread payload", ".venv/bin/python -m scripts.ai_agent_bridge inbox --for gemini"),
    ]

    for recipient, expected_header, expected_preview, expected_instruction in test_cases:
        _write_inbox_fixture(fixtures, recipient, expected_preview)
        env = os.environ.copy()
        env.update(
            {
                "CLAUDE_PROJECT_DIR": str(tmp_path),
                "LEARN_UK_HOOK_RECIPIENT": recipient,
                "FAKE_INBOX_FIXTURES": str(fixtures),
                "FAKE_INBOX_ARGS": str(args_log),
            }
        )
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

    assert args_log.read_text(encoding="utf-8").splitlines()[-3:] == [
        "-m scripts.ai_agent_bridge inbox --for claude",
        "-m scripts.ai_agent_bridge inbox --for codex",
        "-m scripts.ai_agent_bridge inbox --for gemini",
    ]


def test_inbox_hook_defaults_to_claude_recipient(tmp_path: Path) -> None:
    """When LEARN_UK_HOOK_RECIPIENT is unset, inbox hook defaults to claude."""
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "claude", "claude-default payload")

    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
        }
    )
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
    assert args_log.read_text(encoding="utf-8").strip() == "-m scripts.ai_agent_bridge inbox --for claude"


def test_inbox_hook_fails_open_when_project_interpreter_is_missing(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update({"CLAUDE_PROJECT_DIR": str(tmp_path), "LEARN_UK_HOOK_RECIPIENT": "codex"})

    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=10,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_inbox_hook_fails_open_when_live_cli_errors(tmp_path: Path) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "codex", "unreachable payload")
    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "LEARN_UK_HOOK_RECIPIENT": "codex",
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
            "FAKE_INBOX_FAIL": "1",
        }
    )

    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=10,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert not args_log.exists()
    assert not (tmp_path / ".agent" / "runtime").exists()


def test_inbox_hook_surfaces_at_most_five_cli_previews(tmp_path: Path) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    rows = "\n".join(
        f"  [{message_id}] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        f"      preview-{message_id}"
        for message_id in range(101, 107)
    )
    (fixtures / "codex.txt").write_text(
        "📬 Inbox for codex: 6 unread | 0 read-but-not-live-consumed | 0 live-consumed\n\n"
        f"{rows}\n"
        "  [201] [read-but-not-live-consumed] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      read-only-body\n"
        "  [202] [live-consumed] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      live-consumed-body\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "LEARN_UK_HOOK_RECIPIENT": "codex",
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
        }
    )

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
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 6 unread message(s) waiting." in context
    assert all(f"preview-{message_id}" in context for message_id in range(101, 106))
    assert "preview-106" not in context
    assert "read-only-body" not in context
    assert "live-consumed-body" not in context
    assert context.count("[unread]") == 5
