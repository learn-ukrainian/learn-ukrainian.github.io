"""Contracts for fail-open behavior of Claude and Cursor Entire hooks, and updated inbox instruction."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.entire import cursor_native_hook_shim as cursor_shim
from tests.helpers.agy_inbox_fixtures import BODY_MARKER, add_authority, add_legacy, snapshot

pytest_plugins = ("tests.helpers.agy_inbox_fixtures",)

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SETTINGS = REPO_ROOT / "agents_extensions" / "shared" / "settings.json"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-agent-inbox.sh"
CURSOR_SHIM_SCRIPT = REPO_ROOT / "scripts" / "entire" / "cursor_native_hook_shim.py"


def _hook_env(stores=None) -> dict[str, str]:
    """Isolate hook identity, bypass flags, interpreter and both store pointers."""
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith(("SESSION_", "FLEET_COMMS_", "LEARN_UK_HOOK_")) or key in {
            "AB_DB_PATH", "GEMINI_SESSION", "LEARN_UKRAINIAN_PIPELINE", "LU_DRIVER_STATE_PYTHON",
            "LEARN_UKRAINIAN_SESSION_ID", "CODEX_THREAD_ID", "CODEX_SESSION_ID", "TEST_INBOX_ROSTER",
        }:
            env.pop(key, None)
    if stores is not None:
        env.update({
            "CLAUDE_PROJECT_DIR": str(REPO_ROOT), "AB_DB_PATH": str(stores[0]),
            "FLEET_COMMS_ROOT": str(stores[1].parent), "FLEET_COMMS_ALLOW_LOCAL_SHADOW": "1",
            "LU_DRIVER_STATE_PYTHON": sys.executable,
        })
    return env


def _claude_entire_hooks() -> list[dict]:
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    needle = "hooks claude-code "
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


def test_claude_entire_hooks_manifest_structure() -> None:
    """Claude settings should have 7 composed Entire hooks without exec and ending with || true."""
    hooks = _claude_entire_hooks()
    assert len(hooks) == 7

    verbs = {
        re.search(r"hooks claude-code ([a-z-]+)", hook["command"]).group(1)
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
    # Entire 0.11.5's Claude Code template gives stop and post-task 120s, the rest 30s.
    assert {
        re.search(r"hooks claude-code ([a-z-]+)", hook["command"]).group(1): hook["timeout"]
        for hook in hooks
    } == {
        "session-start": 30,
        "pre-task": 30,
        "post-task": 120,
        "post-todo": 30,
        "user-prompt-submit": 30,
        "stop": 120,
        "session-end": 30,
    }
    assert all("if ! command -v entire" in hook["command"] for hook in hooks)
    assert all("exec entire" not in hook["command"] for hook in hooks)
    # Capture runs only behind the guard (version + private route), which always exits 0.
    assert all("/scripts/entire/capture_guard.sh" in hook["command"] for hook in hooks)
    assert not any("entire hooks claude-code" in hook["command"] for hook in hooks)


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


def test_inbox_hook_emits_provider_scoped_metadata_and_drain_instruction(tmp_path: Path, stores) -> None:
    """The real shell reports scoped metadata without bodies, writes or bridge execution."""
    source = INBOX_HOOK.read_text(encoding="utf-8")
    assert "-m scripts.inbox_pending --native-hook --recipient" in source
    assert "sqlite3" not in source and "scripts.ai_agent_bridge" not in source
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|REPLACE)\b", source)
    for index, recipient in enumerate(("claude", "codex", "gemini")):
        add_authority(stores[1], recipient=recipient, identifier="authority-message_" + str(index) * 32,
                      delivery_id=f"delivery-{index}")
        add_legacy(stores[0], recipient=recipient, identifier=index + 1)
        before = snapshot(stores)
        env = _hook_env(stores) | {"LEARN_UK_HOOK_RECIPIENT": recipient}
        completed = subprocess.run(
            ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
            check=False, env=env, timeout=5,
        )
        assert completed.returncode == 0 and completed.stderr == ""
        output = json.loads(completed.stdout)["hookSpecificOutput"]
        assert output["hookEventName"] == "UserPromptSubmit"
        context = output["additionalContext"]
        assert "AUTHORITY INBOX: 1; oldest " in context and "unknown" not in context
        assert "legacy 1" in context and len(context) <= 500
        assert f"deliveries claim --recipient {recipient} " in context
        assert f"scripts.ai_agent_bridge inbox --for {recipient}" in context
        assert "mcp__message-broker" not in context and BODY_MARKER not in context
        assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()


def test_inbox_hook_defaults_to_claude_recipient(tmp_path: Path, stores) -> None:
    add_authority(stores[1], recipient="claude")
    add_legacy(stores[0], recipient="claude")
    before = snapshot(stores)
    env = _hook_env(stores)
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: 1; oldest " in context
    assert "unknown" not in context and "legacy 1" in context
    assert "deliveries claim --recipient claude " in context
    assert "scripts.ai_agent_bridge inbox --for claude" in context


def test_inbox_hook_reports_unknown_when_project_interpreter_is_missing(tmp_path: Path) -> None:
    env = _hook_env() | {
        "CLAUDE_PROJECT_DIR": str(tmp_path), "LEARN_UK_HOOK_RECIPIENT": "codex",
        "LU_DRIVER_STATE_PYTHON": str(tmp_path / "missing-interpreter"),
    }
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0 and completed.stderr == ""
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert context == "AUTHORITY INBOX: unknown; oldest unknown; .venv/bin/python -m scripts.fleet_comms deliveries --help"
    assert not (tmp_path / ".agent").exists()


def test_inbox_hook_reports_unknown_when_metadata_cli_errors(tmp_path: Path, stores) -> None:
    interpreter = tmp_path / "failing-interpreter"
    interpreter.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    interpreter.chmod(0o700)
    before = snapshot(stores)
    env = _hook_env(stores)
    env.update({"LEARN_UK_HOOK_RECIPIENT": "codex", "LU_DRIVER_STATE_PYTHON": str(interpreter)})
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert context == "AUTHORITY INBOX: unknown; oldest unknown; .venv/bin/python -m scripts.fleet_comms deliveries --help"


def test_inbox_hook_bounds_metadata_without_body_previews(tmp_path: Path, stores) -> None:
    for index in range(6):
        add_authority(stores[1], recipient="codex", identifier="authority-message_" + str(index) * 32,
                      delivery_id=f"delivery-{index}")
    add_legacy(stores[0], recipient="codex", acknowledged=1, identifier=201)
    add_legacy(stores[0], recipient="codex", consumed=1, identifier=202)
    before = snapshot(stores)
    env = _hook_env(stores)
    env["LEARN_UK_HOOK_RECIPIENT"] = "codex"
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: 6; oldest " in context and "legacy 0" in context
    assert "unknown" not in context
    assert "deliveries claim --recipient codex " in context
    assert "inbox --for" not in context
    assert "authority-message_" not in context and "delivery-" not in context
    assert "[unread]" not in context and "preview" not in context


def test_stamp_pytest_hook_scoped_to_bash_matcher() -> None:
    """stamp-pytest only inspects a Bash command; it must not fire for other tools (#8529)."""
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    for event in ("PostToolUse", "PostToolUseFailure"):
        entries = [
            entry
            for entry in settings["hooks"][event]
            if any("stamp-pytest" in hook.get("command", "") for hook in entry.get("hooks", []))
        ]
        assert len(entries) == 1, f"{event}: expected exactly one stamp-pytest entry"
        assert entries[0].get("matcher") == "Bash", f"{event}: stamp-pytest must be Bash-scoped"

    post_unscoped = [
        entry for entry in settings["hooks"]["PostToolUse"] if "matcher" not in entry
    ]
    unscoped_commands = [
        hook["command"] for entry in post_unscoped for hook in entry.get("hooks", [])
    ]
    assert any("tool-timing.sh" in command for command in unscoped_commands)
    assert any("context-monitor.sh" in command for command in unscoped_commands)


def test_inbox_hook_proven_zero_never_starts_bridge(tmp_path: Path, stores) -> None:
    """A valid empty lane stays proven zero without importing bridge execution."""
    add_legacy(stores[0], recipient="lane:infra", acknowledged=1, consumed=1)
    add_legacy(stores[0], recipient="claude", identifier=2)
    before = snapshot(stores)
    env = _hook_env(stores)
    env["LEARN_UK_HOOK_RECIPIENT"] = "lane:infra"
    direct = subprocess.run(
        [sys.executable, "-c",
         "import sys; from scripts.inbox_pending import main; "
         "assert not any('ai_agent_bridge.' + name in module "
         "for module in sys.modules "
         "for name in ('_cli', '_claude', '_codex', '_gemini', '_grok_build', '_model')); "
         "raise SystemExit(main(['--native-hook', '--recipient', 'lane:infra']))"],
        text=True, capture_output=True, check=False, env=env, cwd=REPO_ROOT, timeout=5,
    )
    assert direct.returncode == 0, direct.stderr
    assert direct.stderr == ""
    assert "AUTHORITY INBOX: 0; oldest none; legacy 0;" in json.loads(direct.stdout)[
        "hookSpecificOutput"
    ]["additionalContext"]
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: 0; oldest none; legacy 0;" in context
    assert "unknown" not in context and "inbox --for" not in context
    assert "deliveries claim --recipient lane:infra " in context
    assert "scripts.ai_agent_bridge" not in INBOX_HOOK.read_text()


def test_inbox_hook_keeps_legacy_drain_when_authority_is_unreadable(tmp_path: Path, stores) -> None:
    add_legacy(stores[0], recipient="codex")
    stores[1].write_bytes(b"not a sqlite database")
    before = tuple(path.read_bytes() for path in stores)
    env = _hook_env(stores)
    env["LEARN_UK_HOOK_RECIPIENT"] = "codex"
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert tuple(path.read_bytes() for path in stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: unknown; oldest unknown; legacy 1;" in context
    assert "scripts.ai_agent_bridge inbox --for codex" in context
    assert "deliveries claim --recipient codex " in context


def test_inbox_hook_grok_seat_dual_reads_grok_build_alias(tmp_path: Path, stores) -> None:
    """The canonical alias policy includes grok-build without widening another seat."""
    add_legacy(stores[0], recipient="grok-build")
    add_legacy(stores[0], recipient="codex", identifier=2)
    before = snapshot(stores)
    env = _hook_env(stores)
    env["LEARN_UK_HOOK_RECIPIENT"] = "grok"
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert snapshot(stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: 0; oldest none; legacy 1;" in context
    assert "scripts.ai_agent_bridge inbox --for grok" in context
    assert "unknown" not in context


def test_inbox_hook_reports_each_store_independently_on_legacy_error(tmp_path: Path, stores) -> None:
    add_authority(stores[1], recipient="codex")
    stores[0].write_bytes(b"not a sqlite database")
    before = tuple(path.read_bytes() for path in stores)
    env = _hook_env(stores)
    env["LEARN_UK_HOOK_RECIPIENT"] = "codex"
    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)], input="{}", text=True, capture_output=True,
        check=False, env=env, timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    output = json.loads(completed.stdout)
    assert set(output) == {"hookSpecificOutput"}
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert len(context) <= 500 and context.isascii()
    assert BODY_MARKER not in completed.stdout
    assert tuple(path.read_bytes() for path in stores) == before
    assert not (tmp_path / ".agent" / "runtime").exists()
    assert "AUTHORITY INBOX: 1; oldest " in context and "legacy unknown;" in context
    assert "deliveries claim --recipient codex " in context and "inbox --for" not in context
