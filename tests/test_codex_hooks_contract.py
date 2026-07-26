"""Contracts for the Codex-specific lifecycle-hook manifest and entry point."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

from scripts.agent_runtime.codex_hook_policy import (
    LOCAL_BASH_GUARDS,
    MERGE_GUARDS,
    PRIMARY_WRITE_GUARD,
    run_guard,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
    ).strip()
).parent
HOOKS_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "hooks.json"
ENTRY = REPO_ROOT / "scripts" / "agent_runtime" / "codex_hook_entry.sh"
VENV_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "enforce-venv.sh"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-gemini-inbox.sh"


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )


def _make_linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    primary = tmp_path / "primary"
    worktree = tmp_path / "linked"
    primary.mkdir()
    _run(["git", "init", "-b", "main"], cwd=primary)
    _run(["git", "config", "user.email", "hooks@example.invalid"], cwd=primary)
    _run(["git", "config", "user.name", "Hook Tests"], cwd=primary)
    (primary / "README.md").write_text("hook test\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=primary)
    _run(["git", "commit", "-m", "test fixture"], cwd=primary)
    (primary / ".venv").symlink_to(PRIMARY_ROOT / ".venv", target_is_directory=True)
    _run(["git", "worktree", "add", "-b", "codex/hooks-test", str(worktree)], cwd=primary)
    return primary, worktree


def _manifest() -> dict:
    return json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))


def test_codex_manifest_uses_only_supported_result_event() -> None:
    hooks = _manifest()["hooks"]

    assert "PostToolUse" in hooks
    assert "PostToolUseFailure" not in hooks


def test_codex_tool_events_have_one_deterministic_command_hook() -> None:
    hooks = _manifest()["hooks"]

    pre_groups = hooks["PreToolUse"]
    assert len(pre_groups) == 1
    assert pre_groups[0]["matcher"] == "^(Bash|Write|Edit|MultiEdit|apply_patch)$"
    assert len(pre_groups[0]["hooks"]) == 1
    pre_hook = pre_groups[0]["hooks"][0]
    assert 'codex_hook_entry.sh" pre-tool-use' in pre_hook["command"]
    assert pre_hook["timeout"] == 55

    post_groups = hooks["PostToolUse"]
    assert len(post_groups) == 1
    assert len(post_groups[0]["hooks"]) == 1
    assert 'codex_hook_entry.sh" post-tool-use' in post_groups[0]["hooks"][0]["command"]


def test_codex_policy_preserves_tool_scopes_and_per_guard_deadlines() -> None:
    assert LOCAL_BASH_GUARDS == (
        ("heal-core-bare.py", 3),
        ("guard-branch-switch-in-main.py", 3),
        ("guard-secret-print.py", 5),
    )
    assert PRIMARY_WRITE_GUARD == ("guard-primary-checkout-write.py", 5)
    assert MERGE_GUARDS == (
        ("guard-admin-merge.py", 30),
        ("guard-pr-merge.py", 30),
    )


def test_codex_policy_guard_timeout_fails_closed(tmp_path: Path) -> None:
    guard = tmp_path / "slow_guard.py"
    guard.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    result = run_guard(
        PRIMARY_ROOT / ".venv" / "bin" / "python",
        guard,
        "{}",
        timeout_seconds=0.01,
    )

    assert result.returncode == 2
    assert result.timed_out is True
    assert "blocking the tool call fail-closed" in result.stderr


def test_codex_entry_rewrites_bare_python_from_worktree_without_local_venv(
    tmp_path: Path,
) -> None:
    primary, worktree = _make_linked_worktree(tmp_path)
    assert not (worktree / ".venv").exists()

    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(primary),
        "tool_name": "Bash",
        "tool_input": {
            "command": 'python3 -c "print(1)"',
            "workdir": str(worktree),
        },
    }
    completed = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=worktree,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)
    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "allow"
    assert specific["updatedInput"]["command"] == (f'{primary}/.venv/bin/python -c "print(1)"')


def test_claude_python_rewrite_shape_remains_compatible() -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(PRIMARY_ROOT),
        "tool_name": "Bash",
        "tool_input": {"command": "python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(PRIMARY_ROOT)
    environment.pop("LEARN_UK_HOOK_PROVIDER", None)

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=REPO_ROOT,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "modifiedInput": {
            "command": f"{PRIMARY_ROOT}/.venv/bin/python --version",
        }
    }


def test_python_rewrite_preserves_checkout_path_metacharacters(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout&pipe|root"
    canonical.mkdir()
    (canonical / ".venv").symlink_to(
        PRIMARY_ROOT / ".venv",
        target_is_directory=True,
    )
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": 'python3 -c "print(1)"'},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)
    environment["LEARN_UK_HOOK_PROVIDER"] = "codex"

    completed = subprocess.run(
        ["bash", str(VENV_HOOK)],
        cwd=canonical,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    updated = json.loads(completed.stdout)["hookSpecificOutput"]["updatedInput"]
    assert updated["command"] == (f'{canonical}/.venv/bin/python -c "print(1)"')


def _make_inbox_db(project: Path) -> None:
    db = project / ".mcp" / "servers" / "message-broker" / "messages.db"
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as connection:
        connection.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
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
        connection.executemany(
            """
            INSERT INTO messages
                (from_llm, to_llm, message_type, task_id, content, timestamp,
                 acknowledged, claimed_by)
            VALUES (?, ?, 'status', 'hooks', ?, '2026-07-26T00:00:00Z', 0, NULL)
            """,
            [
                ("claude", "codex", "codex-only message"),
                ("codex", "claude", "claude-only message"),
            ],
        )


def test_inbox_hook_targets_requested_provider(tmp_path: Path) -> None:
    _make_inbox_db(tmp_path)
    environment = os.environ.copy()
    environment["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    environment["LEARN_UK_HOOK_RECIPIENT"] = "codex"

    completed = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 1 unread message" in context
    assert "codex-only message" in context
    assert "claude-only message" not in context
