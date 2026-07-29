"""Contracts for the Codex-specific lifecycle-hook manifest and entry point."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import tomllib
from pathlib import Path

from scripts.agent_runtime import codex_hook_policy
from scripts.agent_runtime.codex_hook_policy import (
    ENFORCE_VENV_TIMEOUT,
    LOCAL_BASH_GUARDS,
    MERGE_GUARDS,
    PRIMARY_WRITE_GUARD,
    _result_code,
    _run_enforce_venv,
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
PROJECT_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "config.toml"
ENTRY = REPO_ROOT / "scripts" / "agent_runtime" / "codex_hook_entry.sh"
VENV_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "enforce-venv.sh"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-gemini-inbox.sh"
SESSION_SETUP_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "session-setup.sh"
POST_COMPACT_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "post-compact.sh"


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


def test_codex_project_config_leaves_root_model_user_selectable() -> None:
    config = tomllib.loads(PROJECT_CONFIG.read_text(encoding="utf-8"))

    assert "model" not in config
    assert "model_reasoning_effort" not in config
    assert config["features"] == {
        "multi_agent": True,
        "remote_compaction_v2": True,
        "memories": False,
        "multi_agent_v2": {
            "enabled": True,
            "hide_spawn_agent_metadata": False,
            "tool_namespace": "agents",
        },
    }
    assert config["agents"] == {
        "enabled": True,
        "max_concurrent_threads_per_session": 3,
        "default_subagent_model": "gpt-5.6-terra",
        "default_subagent_reasoning_effort": "medium",
        "interrupt_message": True,
    }


def test_codex_compaction_has_one_bounded_hydration_path() -> None:
    hooks = _manifest()["hooks"]
    session_group = hooks["SessionStart"][0]
    compact_group = hooks["PostCompact"][0]

    assert session_group["matcher"] == "startup|resume|clear"
    assert session_group["hooks"][0]["additionalContextLimit"] == 1200
    assert compact_group["matcher"] == "manual|auto"
    assert compact_group["hooks"][0]["additionalContextLimit"] == 800


def test_ordinary_codex_start_is_concise_and_postcompact_is_silent(
    tmp_path: Path,
) -> None:
    deployed_hooks = tmp_path / ".codex" / "hooks"
    deployed_hooks.mkdir(parents=True)
    session_hook = deployed_hooks / "session-setup.sh"
    compact_hook = deployed_hooks / "post-compact.sh"
    shutil.copy2(SESSION_SETUP_HOOK, session_hook)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)

    environment = os.environ.copy()
    for key in tuple(environment):
        if (
            key.startswith("LEARN_UKRAINIAN_")
            or key.startswith("CODEX_")
            or key.startswith("SESSION_")
            or key == "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS"
        ):
            environment.pop(key, None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(PRIMARY_ROOT),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(PRIMARY_ROOT),
            "HOME": os.fspath(tmp_path / "home"),
        }
    )
    started = subprocess.run(
        ["bash", os.fspath(session_hook)],
        input=json.dumps({"source": "startup", "model": "gpt-5.6-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=30,
    )

    assert started.returncode == 0, started.stderr
    context = json.loads(started.stdout)["hookSpecificOutput"]["additionalContext"]
    assert len(context.encode()) < 500
    assert "profile=native_codex" in context
    assert "Native compaction is runtime-owned" in context
    assert "NO EPIC ASSIGNED" not in context
    assert "THREAD ROLLOVER" not in context
    assert "MEMORY.md" not in context

    compacted = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )
    assert compacted.returncode == 0, compacted.stderr
    assert compacted.stdout == ""


def test_bound_codex_driver_hydrates_exact_stream_and_points_to_shadow_diary(
    tmp_path: Path,
) -> None:
    deployed_hooks = tmp_path / ".codex" / "hooks"
    deployed_hooks.mkdir(parents=True)
    compact_hook = deployed_hooks / "post-compact.sh"
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)
    diary = tmp_path / ".claude" / "devops-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    diary.parent.mkdir(parents=True)
    diary.write_text("# durable driver state\n", encoding="utf-8")
    bounded_runner = tmp_path / "bounded_command.py"
    bounded_runner.write_text("# fixture\n", encoding="utf-8")
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/bin/bash\n"
        "printf '%s\\n' "
        "'{\"schema_name\":\"HydrationCapsuleV1\","
        "\"execution_allowed\":true,"
        "\"next_drive_boundary\":{\"status\":\"ok\",\"value\":\"issue:1\"}}'\n"
        "printf '%s\\n' 'ACTION: hydration ready — continue the current driver.'\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(tmp_path),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(tmp_path),
            "SESSION_HANDOFF_AGENT": "codex-devops",
            "SESSION_EPIC": "devops",
            "THREAD_ROLLOVER_PYTHON": os.fspath(fake_python),
            "SESSION_BOUNDED_RUNNER": os.fspath(bounded_runner),
        }
    )

    compacted = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )

    assert compacted.returncode == 0, compacted.stderr
    context = json.loads(compacted.stdout)["additionalContext"]
    assert "CODEX FLEET-DRIVER HYDRATION" in context
    assert '"schema_name":"HydrationCapsuleV1"' in context
    assert ".claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md" in context
    assert "continue only from the capsule's next_drive_boundary" in context


def test_codex_tool_events_have_one_deterministic_command_hook() -> None:
    hooks = _manifest()["hooks"]

    pre_groups = hooks["PreToolUse"]
    assert len(pre_groups) == 1
    assert pre_groups[0]["matcher"] == "^(Bash|Write|Edit|MultiEdit|apply_patch)$"
    assert len(pre_groups[0]["hooks"]) == 1
    pre_hook = pre_groups[0]["hooks"][0]
    assert 'codex_hook_entry.sh" pre-tool-use' in pre_hook["command"]
    assert pre_hook["timeout"] == 45

    post_groups = hooks["PostToolUse"]
    assert len(post_groups) == 1
    assert len(post_groups[0]["hooks"]) == 1
    assert 'codex_hook_entry.sh" post-tool-use' in post_groups[0]["hooks"][0]["command"]


def test_codex_policy_preserves_tool_scopes_and_per_guard_deadlines() -> None:
    assert ENFORCE_VENV_TIMEOUT == 3
    assert LOCAL_BASH_GUARDS == (
        ("heal-core-bare.py", 3),
        ("guard-branch-switch-in-main.py", 3),
        ("guard-secret-print.py", 5),
    )
    assert PRIMARY_WRITE_GUARD == ("guard-primary-checkout-write.py", 5)
    assert MERGE_GUARDS == (
        ("guard-admin-merge.py", 20),
        ("guard-pr-merge.py", 20),
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


def test_non_rewrite_guard_stdout_fails_closed(
    tmp_path: Path,
    capsys,
) -> None:
    guard = tmp_path / "noisy_guard.py"
    guard.write_text("print('not-json')\n", encoding="utf-8")
    result = run_guard(
        PRIMARY_ROOT / ".venv" / "bin" / "python",
        guard,
        "{}",
        timeout_seconds=1,
    )

    assert _result_code([result]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unexpected stdout" in captured.err
    assert "not-json" in captured.err


def test_codex_policy_venv_rewrite_timeout_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    guard = tmp_path / "enforce-venv.sh"
    guard.write_text("#!/bin/bash\nsleep 5\n", encoding="utf-8")
    monkeypatch.setattr(codex_hook_policy, "ENFORCE_VENV_TIMEOUT", 0.01)

    result = _run_enforce_venv(tmp_path, tmp_path, "{}")

    assert result.returncode == 2
    assert result.timed_out is True
    assert "enforce-venv.sh exceeded 0.01s" in result.stderr
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
