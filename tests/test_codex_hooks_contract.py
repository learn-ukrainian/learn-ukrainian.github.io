"""Contracts for the Codex-specific lifecycle-hook manifest and entry point."""

from __future__ import annotations

import gc
import json
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
import weakref
from pathlib import Path

import pytest

from scripts.agent_runtime import codex_hook_policy
from scripts.agent_runtime.adapters.codex import CodexAdapter, _portable_hook_command
from scripts.agent_runtime.codex_hook_policy import (
    ENFORCE_VENV_TIMEOUT,
    LOCAL_BASH_GUARDS,
    MERGE_GUARDS,
    PRIMARY_WRITE_GUARD,
    REWRITE_BASH_GUARDS,
    _result_code,
    _run_enforce_venv,
    run_guard,
)
from tests.helpers.python import project_python

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
        timeout=30,
    ).strip()
).parent
HOOKS_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "hooks.json"
PROJECT_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "config.toml"
ENTRY = REPO_ROOT / "scripts" / "agent_runtime" / "codex_hook_entry.sh"
VENV_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "enforce-venv.sh"
INBOX_HOOK = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "check-agent-inbox.sh"
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


def _make_exact_python_checkout(root: Path, *, delegate: Path | None = None) -> None:
    python = root / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    script = "#!/bin/bash\nprintf 'Python 3.12.14\\n'\n"
    if delegate is not None:
        script = (
            "#!/bin/bash\n"
            'if [ "${1:-}" = "--version" ]; then\n'
            "  printf 'Python 3.12.14\\n'\n"
            "  exit 0\n"
            "fi\n"
            f'exec {shlex.quote(os.fspath(delegate))} "$@"\n'
        )
    python.write_text(script, encoding="utf-8")
    python.chmod(0o755)
    (root / ".python-version").write_text("3.12.14\n", encoding="utf-8")


def _make_linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    primary = tmp_path / "primary"
    worktree = tmp_path / "linked"
    primary.mkdir()
    _run(["git", "init", "-b", "main"], cwd=primary)
    _run(["git", "config", "user.email", "hooks@example.invalid"], cwd=primary)
    _run(["git", "config", "user.name", "Hook Tests"], cwd=primary)
    (primary / "README.md").write_text("hook test\n", encoding="utf-8")
    _make_exact_python_checkout(
        primary,
        delegate=Path(project_python()),
    )
    _run(["git", "add", "README.md"], cwd=primary)
    _run(["git", "commit", "-m", "test fixture"], cwd=primary)
    _run(["git", "worktree", "add", "-b", "codex/hooks-test", str(worktree)], cwd=primary)
    return primary, worktree


def _manifest() -> dict:
    return json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))


def test_grok_post_compact_reminder_uses_sol_worker_default(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(POST_COMPACT_HOOK)],
        cwd=tmp_path,
        env={**os.environ, "GROK_AGENT": "grok", "SESSION_EPIC": "", "CODEX_COMPACT_SESSION_START": ""},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["additionalContext"]
    assert "default eligible code worker = Sol high" in context
    assert "explicit Luna/Flash bounded routes require a Sol advisory envelope" in context
    assert "default bounded work = Sol advisory envelope" not in context


@pytest.mark.parametrize("session_id", [None, "worker-thread"])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_worker_binds_tracked_guards_without_deployed_config(tmp_path, session_id, mode):
    primary, worktree = _make_linked_worktree(tmp_path)
    assert not (worktree / ".codex").exists()
    plan = CodexAdapter().build_invocation(
        prompt="test",
        mode=mode,
        cwd=worktree,
        model=None,
        task_id=None,
        session_id=session_id,
        tool_config={"codex_home_override": str(tmp_path / "private-home"), "disable_features": ["hooks"]},
    )
    try:
        overrides = [plan.cmd[index + 1] for index, arg in enumerate(plan.cmd) if arg == "-c"]
        config = tomllib.loads(next(value for value in overrides if value.startswith("hooks.PreToolUse=")))
        groups = config["hooks"]["PreToolUse"]
        toggles = [
            arg
            for index, arg in enumerate(plan.cmd[:-1])
            if arg in {"--enable", "--disable"} and plan.cmd[index + 1] == "hooks"
        ]
        assert toggles == ["--enable"]
        assert "--dangerously-bypass-hook-trust" in plan.cmd
        # The TOML overlay must never embed this checkout's absolute paths.
        override = next(value for value in overrides if value.startswith("hooks.PreToolUse="))
        assert str(REPO_ROOT) not in override
        assert str(PRIMARY_ROOT) not in override
        runner = groups[0]["hooks"][0]
        assert "git -C" in runner["command"]
        assert "LU_CODEX_HOOK_SOURCE" in runner["command"]
        assert "scripts/agent_runtime/codex_hook_entry.sh" in runner["command"]
        assert groups[0]["matcher"] == _manifest()["hooks"]["PreToolUse"][0]["matcher"]
        assert runner["timeout"] == 45
        # Freeze the independent shared-settings denominator, including the
        # shared guard absent from the original Codex runner.
        shared = json.loads((REPO_ROOT / "agents_extensions/shared/settings.json").read_text())
        expected = {
            Path(shlex.split(hook["command"])[-1]).name
            for group in shared["hooks"]["PreToolUse"]
            for hook in group["hooks"]
            if ".claude/hooks/" in hook["command"]
        }
        actual = {name for name, _ in (*LOCAL_BASH_GUARDS, *REWRITE_BASH_GUARDS, PRIMARY_WRITE_GUARD, *MERGE_GUARDS)}
        actual.add("enforce-venv.sh")
        actual.update(
            name for name in expected for group in groups[1:] for hook in group["hooks"] if name in hook["command"]
        )
        assert actual == expected
        for tool in ("Write", "apply_patch", "Bash"):
            payload = {
                "hook_event_name": "PreToolUse",
                "cwd": str(worktree),
                "tool_name": tool,
                "tool_input": {
                    "file_path": str(primary / "README.md"),
                    "command": f"echo forbidden > {shlex.quote(str(primary / 'README.md'))}",
                    "patch": f"*** Begin Patch\n*** Update File: {primary / 'README.md'}\n@@\n-hook test\n+forbidden\n*** End Patch",
                },
            }
            # Use the actual session cwd and launch environment. Forcing the
            # source cwd would hide session-checkout substitution (#10305).
            completed = subprocess.run(
                ["bash", "-c", runner["command"]],
                cwd=worktree,
                env={**os.environ, **plan.env_overrides},
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            assert completed.returncode == 2, completed.stderr
            assert "guard-primary-checkout-write" in completed.stderr
        assert (primary / "README.md").read_text() == "hook test\n"
    finally:
        plan.output_file.unlink()


def test_worker_appended_shared_guards_execute_through_shell(tmp_path):
    """Appended shared guards must resolve and run under Codex's shell, not exit 127."""
    _, worktree = _make_linked_worktree(tmp_path)
    plan = CodexAdapter().build_invocation(
        prompt="test",
        mode="workspace-write",
        cwd=worktree,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"codex_home_override": str(tmp_path / "private-home"), "disable_features": ["hooks"]},
    )
    try:
        override = next(
            plan.cmd[index + 1]
            for index, arg in enumerate(plan.cmd[:-1])
            if arg == "-c" and plan.cmd[index + 1].startswith("hooks.PreToolUse=")
        )
        groups = tomllib.loads(override)["hooks"]["PreToolUse"]
        appended = [hook for group in groups[1:] for hook in group["hooks"]]
        assert not any("guard-public-github-text.py" in hook["command"] for hook in appended)
        assert ("guard-public-github-text.py", 5) in REWRITE_BASH_GUARDS
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(worktree),
            "tool_name": "Bash",
            "tool_input": {"command": "echo hello"},
        }
        for hook in appended:
            completed = subprocess.run(
                ["bash", "-c", hook["command"]],
                cwd=worktree,
                env={**os.environ, **plan.env_overrides},
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            assert completed.returncode == 0, (hook["command"], completed.stderr)
            assert "No such file" not in completed.stderr
    finally:
        plan.output_file.unlink(missing_ok=True)


@pytest.mark.parametrize("session_id", [None, "worker-thread"])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
@pytest.mark.parametrize("disable_features", [["hooks"], ("hooks", "apps", "hooks", "shell_tool")])
def test_worker_hooks_stay_enabled_in_cli_feature_state(tmp_path, session_id, mode, disable_features):
    """Inspect the CLI's effective features without starting a provider turn."""
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("Codex CLI unavailable for local feature-state inspection")
    home = tmp_path / "private-home"
    home.mkdir()
    (home / "config.toml").write_text(
        '[features]\nhooks = false\n[mcp_servers.sources]\ncommand = "true"\n',
        encoding="utf-8",
    )
    plan = CodexAdapter().build_invocation(
        prompt="test",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session_id,
        tool_config={
            "codex_home_override": str(home),
            "disable_features": disable_features,
            # These generic caller keys are unsupported and must stay local.
            "enable_features": ["hooks", "apps"],
            "config_overrides": {"features.hooks": False},
            "features": {"hooks": False},
            "config": ["features.hooks=false"],
        },
    )
    try:
        # Preserve every feature toggle and config override in adapter order;
        # the CLI, rather than an order assertion, decides the effective state.
        flags = [
            token
            for index, arg in enumerate(plan.cmd[:-1])
            if arg in {"-c", "--enable", "--disable"}
            for token in (arg, plan.cmd[index + 1])
        ]
        result = subprocess.run(
            [binary, "features", "list", *flags],
            cwd=plan.cwd,
            env={**os.environ, **plan.env_overrides},
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        features = {fields[0]: fields[-1] for line in result.stdout.splitlines() if (fields := line.split())}
        hooks_state = next((line for line in result.stdout.splitlines() if line.split()[0] == "hooks"), "hooks missing")
        assert features.get("hooks") == "true", hooks_state
        assert features.get("apps") == "false", result.stdout
        if "shell_tool" in disable_features:
            assert features.get("shell_tool") == "false", result.stdout
    finally:
        plan.output_file.unlink(missing_ok=True)


def test_codex_config_encoder_round_trips_nested_hook_tables():
    value = {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": 'echo "quoted"', "timeout": 45, "async": False}],
            }
        ]
    }
    assert tomllib.loads("hooks=" + CodexAdapter._encode_config_value(value))["hooks"] == value


@pytest.mark.parametrize("defect", ["missing-runner", "empty-groups", "foreign-command"])
def test_worker_hook_binding_fails_closed_on_unavailable_or_changed_runner(monkeypatch, defect):
    from scripts.agent_runtime.adapters import codex

    manifest = _manifest()
    if defect == "empty-groups":
        manifest["hooks"]["PreToolUse"] = []
    elif defect == "foreign-command":
        manifest["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = "true"
    read_text = Path.read_text
    is_file = Path.is_file
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: json.dumps(manifest) if path == HOOKS_CONFIG else read_text(path, *a, **kw),
    )
    monkeypatch.setattr(
        Path, "is_file", lambda path: False if defect == "missing-runner" and path == ENTRY else is_file(path)
    )
    with pytest.raises(RuntimeError, match="Codex worker PreToolUse"):
        codex._worker_hook_flags()


def test_codex_manifest_uses_only_supported_result_event() -> None:
    hooks = _manifest()["hooks"]

    assert "PostToolUse" in hooks
    assert "PostToolUseFailure" not in hooks


def test_codex_project_config_leaves_root_model_user_selectable() -> None:
    config = tomllib.loads(PROJECT_CONFIG.read_text(encoding="utf-8"))

    assert "model" not in config
    assert "model_reasoning_effort" not in config
    assert config["features"] == {
        "hooks": True,
        "multi_agent": True,
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
        "default_subagent_model": "gpt-6.1-sol",
        "default_subagent_reasoning_effort": "high",
        "interrupt_message": True,
    }


def test_codex_compaction_has_one_bounded_hydration_path() -> None:
    hooks = _manifest()["hooks"]
    session_groups = hooks["SessionStart"]
    session_group, compact_group = session_groups

    assert session_group["matcher"] == "startup|resume|clear"
    assert session_group["hooks"][0]["additionalContextLimit"] == 1200
    assert compact_group["matcher"] == "compact"
    assert "CODEX_COMPACT_SESSION_START=1" in compact_group["hooks"][0]["command"]
    assert 'post-compact.sh"' in compact_group["hooks"][0]["command"]
    assert compact_group["hooks"][0]["timeout"] == 15
    assert compact_group["hooks"][0]["additionalContextLimit"] == 800
    assert "PostCompact" not in hooks


def test_ordinary_codex_start_is_concise_and_compact_session_start_is_silent(
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
            "CLAUDE_PROFILE_RESOLVER_SH": os.fspath(REPO_ROOT / "scripts/lib/profile_resolver.sh"),
            "CLAUDE_PROFILE_RESOLVER_PY": os.fspath(REPO_ROOT / "scripts/lib/context_profiles.py"),
            "HOME": os.fspath(tmp_path / "home"),
        }
    )
    started = subprocess.run(
        ["bash", os.fspath(session_hook)],
        input=json.dumps({"source": "startup", "model": "gpt-6.1-sol"}),
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
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment | {"CODEX_COMPACT_SESSION_START": "1"},
        timeout=10,
    )
    assert compacted.returncode == 0, compacted.stderr
    assert compacted.stdout == ""


def test_explicit_non_driver_codex_compact_session_start_is_silent(tmp_path: Path) -> None:
    compact_hook = tmp_path / ".codex" / "hooks" / "post-compact.sh"
    compact_hook.parent.mkdir(parents=True)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)
    environment = os.environ.copy()
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": os.fspath(tmp_path),
            "CODEX_CANONICAL_REPO_ROOT": os.fspath(tmp_path),
            "SESSION_HANDOFF_AGENT": "codex",
        }
    )
    environment.pop("SESSION_EPIC", None)

    completed = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        env=environment | {"CODEX_COMPACT_SESSION_START": "1"},
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""


def _run_bound_codex_compact(tmp_path: Path, *, block_hydration_import: bool = False) -> str:
    """Exercise the real bounded runner and canary handoff resolver."""
    (tmp_path / "scripts").symlink_to(REPO_ROOT / "scripts", target_is_directory=True)
    compact_hook = tmp_path / ".codex" / "hooks" / "post-compact.sh"
    compact_hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(POST_COMPACT_HOOK, compact_hook)
    fake_python = tmp_path / "fake-python"
    selection_guard = ""
    if block_hydration_import:
        # Selection must not pay the unrelated hydration runtime's import cost.
        guarded_selection = (
            "import sys; sys.modules['scripts.session_canary.shared_hydration'] = None; exec(sys.argv.pop(1))"
        )
        selection_guard = (
            "if [ \"${1:-}\" = '-c' ]; then\n"
            "  shift\n"
            f'  exec {shlex.quote(sys.executable)} -c {shlex.quote(guarded_selection)} "$@"\n'
            "fi\n"
        )
    fake_python.write_text(
        "#!/bin/bash\n"
        "if [ \"${1:-}\" = '-m' ]; then\n"
        '  printf \'%s\\n\' \'{"schema_name":"HydrationCapsuleV1","execution_allowed":true}\'\n'
        "  exit 0\n"
        "fi\n" + selection_guard + f'exec {shlex.quote(sys.executable)} "$@"\n',
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
            "SESSION_BOUNDED_RUNNER": os.fspath(REPO_ROOT / "scripts/agent_runtime/bounded_command.py"),
            "CODEX_COMPACT_SESSION_START": "1",
        }
    )
    completed = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"source": "compact", "model": "gpt-6.1-sol"}),
        text=True,
        capture_output=True,
        check=False,
        cwd=tmp_path.parent,
        env=environment,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "SessionStart"
    legacy = subprocess.run(
        ["bash", os.fspath(compact_hook)],
        input=json.dumps({"hook_event_name": "PostCompact", "model": "claude-sonnet-5"}),
        text=True,
        capture_output=True,
        check=False,
        cwd=tmp_path.parent,
        env={key: value for key, value in environment.items() if key != "CODEX_COMPACT_SESSION_START"},
        timeout=10,
    )
    assert legacy.returncode == 0, legacy.stderr
    legacy_output = json.loads(legacy.stdout)
    assert "hookSpecificOutput" not in legacy_output
    assert legacy_output["additionalContext"] == output["additionalContext"]
    return output["additionalContext"]


def test_bound_codex_driver_hydrates_exact_stream_and_points_to_shadow_diary(
    tmp_path: Path,
) -> None:
    diary = tmp_path / ".claude" / "devops-epic" / "CODEX-DRIVER-HANDOFF.md"
    diary.parent.mkdir(parents=True)
    diary.write_text("# durable driver state\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION" in context
    assert '"schema_name":"HydrationCapsuleV1"' in context
    assert ".claude/devops-epic/CODEX-DRIVER-HANDOFF.md" in context
    assert "continue only from the capsule's next_drive_boundary" in context


def test_lane_goal_file_outranks_capsule_boundary(tmp_path: Path) -> None:
    epic_dir = tmp_path / ".claude" / "devops-epic"
    epic_dir.mkdir(parents=True)
    (epic_dir / "CODEX-DRIVER-HANDOFF.md").write_text("# durable driver state\n", encoding="utf-8")
    (epic_dir / "DRIVER-STATE.md").write_text("# goal\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert "Lane goal file: .claude/devops-epic/DRIVER-STATE.md." in context
    assert "outranks the capsule's next_drive_boundary" in context
    assert "continue only from the capsule's next_drive_boundary" not in context


def test_first_codex_driver_uses_existing_shared_handoff(
    tmp_path: Path,
) -> None:
    fallback = tmp_path / ".claude" / "devops-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("# shared driver state\n", encoding="utf-8")
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION" in context
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert ".claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md" in context


def test_bound_codex_driver_without_any_handoff_blocks(tmp_path: Path) -> None:
    context = _run_bound_codex_compact(tmp_path)
    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" in context
    assert "No Codex/shared driver handoff selected" in context


def test_shared_handoff_selection_does_not_import_hydration_runtime(tmp_path: Path) -> None:
    fallback = tmp_path / ".claude" / "devops-epic" / "CLAUDE-DRIVER-HANDOFF.md"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("# shared driver state\n", encoding="utf-8")

    context = _run_bound_codex_compact(tmp_path, block_hydration_import=True)

    assert "CODEX FLEET-DRIVER HYDRATION BLOCKED" not in context
    assert '"schema_name":"HydrationCapsuleV1"' in context
    assert ".claude/devops-epic/CLAUDE-DRIVER-HANDOFF.md" in context


def test_codex_tool_events_preserve_policy_then_run_optional_entire_hook() -> None:
    hooks = _manifest()["hooks"]

    pre_groups = hooks["PreToolUse"]
    assert len(pre_groups) == 1
    assert pre_groups[0]["matcher"] == "^(Bash|Write|Edit|MultiEdit|apply_patch|write_stdin)$"
    assert len(pre_groups[0]["hooks"]) == 1
    pre_hook = pre_groups[0]["hooks"][0]
    assert 'codex_hook_entry.sh" pre-tool-use' in pre_hook["command"]
    assert pre_hook["timeout"] == 45

    post_groups = hooks["PostToolUse"]
    assert len(post_groups) == 1
    assert len(post_groups[0]["hooks"]) == 2
    assert 'codex_hook_entry.sh" post-tool-use' in post_groups[0]["hooks"][0]["command"]
    assert "entire hooks codex post-tool-use" in post_groups[0]["hooks"][1]["command"]
    assert post_groups[0]["hooks"][1]["timeout"] == 30
    # Optional Entire capture must fail open (exit 0) even when the
    # installed CLI errors, so it can never poison Codex exec.
    assert post_groups[0]["hooks"][1]["command"].endswith("|| true'")


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
        Path(project_python()),
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
        Path(project_python()),
        guard,
        "{}",
        timeout_seconds=1,
    )

    assert _result_code([result]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unexpected stdout" in captured.err
    assert "not-json" in captured.err


def test_codex_policy_venv_guard_timeout_fails_closed(
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


def test_codex_entry_rejects_bare_python_from_worktree_with_copyable_command(
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

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "Unqualified interpreter blocked" in completed.stderr
    assert f'{PRIMARY_ROOT}/.venv/bin/python -c "print(1)"' in completed.stderr


@pytest.mark.parametrize("shim_first", [False, True])
def test_codex_entry_blocks_gh_rewrite_unless_shim_already_first(tmp_path: Path, shim_first: bool) -> None:
    """Codex ignores updatedInput, so a gh command needing the shim must block, not run bare."""
    _, worktree = _make_linked_worktree(tmp_path)
    shim = REPO_ROOT / "scripts" / "agent_runtime" / "shims"
    path = os.environ.get("PATH", "")
    env = {**os.environ, "PATH": f"{shim}{os.pathsep}{path}" if shim_first else path}
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(worktree),
        "tool_name": "Bash",
        "tool_input": {"command": "gh --version", "workdir": str(worktree)},
    }
    completed = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=worktree,
        env=env,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    if shim_first:
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == ""
    else:
        assert completed.returncode == 2
        assert "blocking fail-closed" in completed.stderr


def test_claude_bare_python_is_rejected_without_rewrite_output(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": "python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)
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

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert f"{canonical}/.venv/bin/python --version" in completed.stderr


def test_python_rejection_shell_quotes_checkout_path_metacharacters(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout&pipe|root"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
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

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert r'checkout\&pipe\|root/.venv/bin/python -c "print(1)"' in completed.stderr


def test_qualified_project_python_passes_without_output(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": ".venv/bin/python --version"},
    }
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical)

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

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_bare_python_rejection_blocks_a_canonical_version_mismatch(tmp_path: Path) -> None:
    canonical = tmp_path / "checkout"
    canonical.mkdir()
    _make_exact_python_checkout(canonical)
    (canonical / ".python-version").write_text("3.12.7\n", encoding="utf-8")
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(canonical),
        "tool_name": "Bash",
        "tool_input": {"command": "python --version"},
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

    assert completed.returncode == 2
    assert "expected Python 3.12.7" in completed.stderr


def _make_fake_inbox_python(tmp_path: Path) -> tuple[Path, Path]:
    """Create a project interpreter that exposes only the live inbox CLI shape."""
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True, exist_ok=True)
    fixtures = tmp_path / "inbox-fixtures"
    fixtures.mkdir()
    args_log = tmp_path / "inbox-cli-args.log"
    python.write_text(
        "#!/bin/sh\n"
        'if [ "$#" -ne 5 ] || [ "$1" != "-m" ] || [ "$2" != "scripts.ai_agent_bridge" ] || [ "$3" != "inbox" ] || [ "$4" != "--for" ]; then\n'
        "  exit 64\n"
        "fi\n"
        'printf \'%s\\n\' "$*" >> "$FAKE_INBOX_ARGS"\n'
        'cat "$FAKE_INBOX_FIXTURES/$5.txt"\n',
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


def test_inbox_hook_targets_requested_provider(tmp_path: Path) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "codex", "codex-only message")
    _write_inbox_fixture(fixtures, "claude", "claude-only message")
    environment = os.environ.copy()
    environment.pop("AB_DB_PATH", None)
    environment.update(
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
        env=environment,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 1 unread message" in context
    assert "codex-only message" in context
    assert "claude-only message" not in context
    assert args_log.read_text(encoding="utf-8").strip() == "-m scripts.ai_agent_bridge inbox --for codex"


def test_inbox_dedupes_by_recipient_and_native_session_and_reemits_new_ids(
    tmp_path: Path,
) -> None:
    fixtures, args_log = _make_fake_inbox_python(tmp_path)
    _write_inbox_fixture(fixtures, "codex", "codex-only message")
    _write_inbox_fixture(fixtures, "claude", "claude-only message")
    environment = os.environ.copy()
    environment.pop("AB_DB_PATH", None)
    environment.update(
        {
            "CLAUDE_PROJECT_DIR": str(tmp_path),
            "LEARN_UK_HOOK_RECIPIENT": "codex",
            "CODEX_THREAD_ID": "codex-native-session",
            "FAKE_INBOX_FIXTURES": str(fixtures),
            "FAKE_INBOX_ARGS": str(args_log),
        }
    )

    first = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )
    second = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )
    assert first.returncode == second.returncode == 0
    assert "CODEX INBOX: 1 unread message" in first.stdout
    assert second.stdout == ""

    (fixtures / "codex.txt").write_text(
        "📬 Inbox for codex: 2 unread | 0 read-but-not-live-consumed | 0 live-consumed\n\n"
        "  [101] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      codex-only message\n"
        "  [103] [unread] From: sender | Type: status | 2026-09-02T00:00:00Z\n"
        "      new codex message\n",
        encoding="utf-8",
    )
    third = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=environment,
        timeout=10,
    )
    assert third.returncode == 0
    third_context = json.loads(third.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 2 unread message(s)" in third_context
    assert "new codex message" in third_context

    claude_environment = environment | {"LEARN_UK_HOOK_RECIPIENT": "claude"}
    provider_isolation = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=claude_environment,
        timeout=10,
    )
    assert provider_isolation.returncode == 0
    provider_context = json.loads(provider_isolation.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CLAUDE INBOX: 1 unread message(s)" in provider_context

    new_session_environment = environment | {"CODEX_THREAD_ID": "another-codex-session"}
    session_isolation = subprocess.run(
        ["bash", str(INBOX_HOOK)],
        input="{}",
        text=True,
        capture_output=True,
        check=False,
        env=new_session_environment,
        timeout=10,
    )
    assert session_isolation.returncode == 0
    session_context = json.loads(session_isolation.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "CODEX INBOX: 2 unread message(s)" in session_context
    assert "new codex message" in session_context

    state_files = list((tmp_path / ".agent" / "runtime").glob("inbox-*.ids"))
    assert len(state_files) == 3
    assert all(len(path.stem.removeprefix("inbox-")) == 64 for path in state_files)
    assert all("message" not in path.read_text(encoding="utf-8") for path in state_files)
    assert args_log.read_text(encoding="utf-8").splitlines() == [
        "-m scripts.ai_agent_bridge inbox --for codex",
        "-m scripts.ai_agent_bridge inbox --for codex",
        "-m scripts.ai_agent_bridge inbox --for codex",
        "-m scripts.ai_agent_bridge inbox --for claude",
        "-m scripts.ai_agent_bridge inbox --for codex",
    ]


def _load_pytest_stamp_module():
    """Import the stamp helper by path; it has no package context of its own."""
    import importlib.machinery
    import importlib.util
    import sys

    helper = REPO_ROOT / ".githooks" / "pytest_stamp.py"
    spec = importlib.util.spec_from_loader(
        "pytest_stamp",
        importlib.machinery.SourceFileLoader("pytest_stamp", str(helper)),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _post_tool_use_pytest_payload(worktree: Path, tool_name: str) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "cwd": str(worktree),
        "tool_name": tool_name,
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/test_example.py -q",
            "workdir": str(worktree),
        },
        "duration_ms": 120,
        "tool_response": {"stdout": "1 passed in 0.10s\n"},
    }


def _stamp_environment(stamps: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment["TMPDIR"] = str(stamps)
    return environment


def test_codex_entry_post_tool_use_stamps_bash_pytest_payload(tmp_path: Path) -> None:
    _, worktree = _make_linked_worktree(tmp_path)
    stamps = tmp_path / "stamps"
    stamps.mkdir()
    stamp_module = _load_pytest_stamp_module()
    identity = stamp_module.stamp_identity(worktree)
    assert identity is not None
    marker = stamp_module.marker_path(identity, {"TMPDIR": str(stamps)})

    completed = subprocess.run(
        ["bash", str(ENTRY), "post-tool-use"],
        cwd=worktree,
        input=json.dumps(_post_tool_use_pytest_payload(worktree, "Bash")),
        text=True,
        capture_output=True,
        check=False,
        env=_stamp_environment(stamps),
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert marker.read_text(encoding="utf-8").strip() == identity.key


def test_codex_entry_post_tool_use_skips_stamp_for_non_bash_payload(tmp_path: Path) -> None:
    """pytest_stamp only inspects a Bash command; other tools never invoke it (#8529)."""
    _, worktree = _make_linked_worktree(tmp_path)
    stamps = tmp_path / "stamps"
    stamps.mkdir()
    stamp_module = _load_pytest_stamp_module()
    identity = stamp_module.stamp_identity(worktree)
    assert identity is not None
    marker = stamp_module.marker_path(identity, {"TMPDIR": str(stamps)})

    completed = subprocess.run(
        ["bash", str(ENTRY), "post-tool-use"],
        cwd=worktree,
        input=json.dumps(_post_tool_use_pytest_payload(worktree, "Edit")),
        text=True,
        capture_output=True,
        check=False,
        env=_stamp_environment(stamps),
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert not marker.exists()


def test_compact_hydrate_bound_fits_its_retries() -> None:
    source = (REPO_ROOT / "agents_extensions/shared/hooks/post-compact.sh").read_text(encoding="utf-8")
    assert 'HYDRATION=$(run_bounded 6 "$BOUNDED_PYTHON"' in source
    hooks = json.loads((REPO_ROOT / "agents_extensions/codex/hooks.json").read_text(encoding="utf-8"))
    compact = [
        hook for group in hooks["hooks"]["SessionStart"] if group.get("matcher") == "compact" for hook in group["hooks"]
    ]
    # Selector (2 s) + stream (2 s) + hydrate (6 s) must fit inside the hook timeout.
    assert compact and compact[0]["timeout"] > 2 + 2 + 6


def test_portable_hook_command_rewrites_tracked_words_and_refuses_foreign_paths(tmp_path):
    from scripts.agent_runtime.adapters.codex import _portable_hook_command

    tracked = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "guard-public-github-text.py"
    command = _portable_hook_command(shlex.quote(str(tracked)), REPO_ROOT)
    assert "agents_extensions/shared/hooks/guard-public-github-text.py" in command
    assert "LU_CODEX_HOOK_SOURCE" in command
    assert str(REPO_ROOT) not in command
    with pytest.raises(RuntimeError, match="unportable"):
        _portable_hook_command(shlex.quote(str(tmp_path / "guard.py")), REPO_ROOT)


def test_portable_hook_runs_shared_python_guards():
    from scripts.agent_runtime.adapters.claude import PROJECT_PYTHON_GUARDS, _worker_guard_settings

    settings = json.loads(_worker_guard_settings())
    commands = {
        Path(shlex.split(hook["command"])[-1]).name: hook["command"]
        for group in settings["hooks"]["PreToolUse"]
        for hook in group["hooks"]
        if Path(shlex.split(hook["command"])[-1]).name in PROJECT_PYTHON_GUARDS
    }
    assert commands.keys() == PROJECT_PYTHON_GUARDS
    for name, original in commands.items():
        command = _portable_hook_command(original, REPO_ROOT)
        assert name in command
        assert str(REPO_ROOT) not in command
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=REPO_ROOT,
            env={**os.environ, "LU_CODEX_HOOK_SOURCE": str(REPO_ROOT)},
            input="{}",
            text=True,
            capture_output=True,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("defect", ["untracked", "modified", "option"])
def test_portable_python_hook_rejects_invalid_entry(tmp_path, defect):
    source, _ = _make_linked_worktree(tmp_path)
    entry = source / "entry.py"
    entry.write_text("raise SystemExit(0)\n")
    if defect != "untracked":
        _run(["git", "add", "entry.py"], cwd=source)
        _run(["git", "commit", "-m", "tracked hook"], cwd=source)
    if defect == "modified":
        entry.write_text("raise SystemExit(1)\n")
    argv = [project_python(), str(entry)]
    if defect == "option":
        argv.insert(1, "-c")
    with pytest.raises(RuntimeError, match="unportable"):
        _portable_hook_command(shlex.join(argv), source)


def test_worker_source_handle_hides_location_and_is_released(tmp_path):
    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="test",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    locator = Path(plan.env_overrides["LU_CODEX_HOOK_SOURCE"])
    try:
        assert str(REPO_ROOT) not in json.dumps(plan.env_overrides)
        assert str(PRIMARY_ROOT) not in json.dumps(plan.env_overrides)
        assert locator.resolve(strict=True) == REPO_ROOT
        override = next(value for value in plan.cmd if value.startswith("hooks.PreToolUse="))
        command = tomllib.loads(override)["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        assert str(REPO_ROOT) not in command
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=tmp_path,
            env={**os.environ, **plan.env_overrides},
            input="{}",
            text=True,
            capture_output=True,
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        adapter.cleanup_invocation(plan)
        assert not locator.exists()
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=tmp_path,
            env={**os.environ, **plan.env_overrides},
            input="{}",
            text=True,
            capture_output=True,
            timeout=5,
        )
        assert result.returncode == 2
        adapter.cleanup_invocation(plan)
    finally:
        adapter.cleanup_invocation(plan)
        plan.output_file.unlink(missing_ok=True)


def test_worker_source_handle_unavailable_fails_closed(tmp_path, monkeypatch):
    original = Path.is_dir
    monkeypatch.setattr(Path, "is_dir", lambda path: False if str(path).startswith("/proc/") else original(path))
    with pytest.raises(RuntimeError, match="source handle unavailable"):
        CodexAdapter().build_invocation(
            prompt="test",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )


def test_worker_rejects_substitute_entry_in_session_checkout(tmp_path):
    primary, session = _make_linked_worktree(tmp_path)
    substitute = session / "scripts/agent_runtime/codex_hook_entry.sh"
    substitute.parent.mkdir(parents=True)
    marker = tmp_path / "substitute-ran"
    substitute.write_text(f"printf substitute > {shlex.quote(str(marker))}\nexit 0\n")
    plan = CodexAdapter().build_invocation(
        prompt="test",
        mode="workspace-write",
        cwd=session,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    try:
        override = next(
            plan.cmd[i + 1]
            for i, arg in enumerate(plan.cmd[:-1])
            if arg == "-c" and plan.cmd[i + 1].startswith("hooks.PreToolUse=")
        )
        command = tomllib.loads(override)["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        payload = {"tool_name": "Write", "cwd": str(session), "tool_input": {"file_path": str(primary / "README.md")}}
        completed = subprocess.run(
            ["bash", "-c", command],
            cwd=session,
            env={**os.environ, **plan.env_overrides},
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=2,
        )
        assert completed.returncode == 2, completed.stderr
        assert not marker.exists()
        assert "guard-primary-checkout-write" in completed.stderr
    finally:
        CodexAdapter().cleanup_invocation(plan)
        plan.output_file.unlink(missing_ok=True)


@pytest.mark.parametrize("escape", ["parent-traversal", "symlink"])
def test_portable_hook_rejects_resolved_escape(tmp_path, escape):
    root = tmp_path / "source"
    root.mkdir()
    outside = tmp_path / "outside.sh"
    outside.write_text("exit 0\n")
    if escape == "parent-traversal":
        entry = root / ".." / "outside.sh"
    else:
        entry = root / "entry.sh"
        entry.symlink_to(outside)
    with pytest.raises(RuntimeError, match="unportable"):
        _portable_hook_command(f"bash {shlex.quote(str(entry))}", root)


@pytest.mark.parametrize("defect", ["untracked", "modified"])
def test_portable_hook_rejects_untracked_content(tmp_path, defect):
    source, _ = _make_linked_worktree(tmp_path)
    entry = source / "entry.sh"
    entry.write_text("exit 0\n")
    if defect == "modified":
        _run(["git", "add", "entry.sh"], cwd=source)
        _run(["git", "commit", "-m", "tracked hook"], cwd=source)
        entry.write_text("exit 1\n")
    with pytest.raises(RuntimeError, match="untracked"):
        _portable_hook_command(f"bash {shlex.quote(str(entry))}", source)


@pytest.mark.parametrize("replacement", ["changed-content", "symlink-escape"])
@pytest.mark.parametrize("kind", ["shell", "python"])
def test_portable_hook_rechecks_entry_before_execution(tmp_path, replacement, kind):
    source, session = _make_linked_worktree(tmp_path)
    entry = source / ("entry.py" if kind == "python" else "entry.sh")
    entry.write_text("raise SystemExit(0)\n" if kind == "python" else "exit 0\n")
    _run(["git", "add", entry.name], cwd=source)
    _run(["git", "commit", "-m", "tracked hook"], cwd=source)
    interpreter = str(source / ".venv/bin/python") if kind == "python" else "bash"
    command = _portable_hook_command(shlex.join([interpreter, str(entry)]), source)
    marker = tmp_path / "replacement-ran"
    substitute = (
        f'from pathlib import Path\nPath({str(marker)!r}).write_text("ran")\n'
        if kind == "python"
        else f"printf ran > {shlex.quote(str(marker))}\nexit 0\n"
    )
    if replacement == "changed-content":
        entry.write_text(substitute)
    else:
        outside = tmp_path / entry.name
        outside.write_text(substitute)
        entry.unlink()
        entry.symlink_to(outside)
    # A same-relative-path substitute in the session must never be selected.
    (session / entry.name).write_text(substitute)
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=session,
        env={**os.environ, "LU_CODEX_HOOK_SOURCE": str(source), "GIT_WORK_TREE": str(session)},
        input="{}",
        text=True,
        capture_output=True,
        timeout=2,
    )
    assert result.returncode == 2, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize(
    "shape",
    [
        "gh --version; PATH={stub_dir} gh issue create --body safe",
        "gh --version && PATH={stub_dir} gh issue create --body safe",
        "false || PATH={stub_dir} gh issue create --body safe",
        "gh --version | {stub} issue create --body safe",
        "(PATH={stub_dir} gh issue create --body safe)",
        "echo $({stub} issue create --body safe)",
        'echo "$({stub} issue create --body safe)"',
        "echo `{stub} issue create --body safe`",
        "PATH={stub_dir} gh issue create --body safe",
        "{stub} issue create --body safe",
        "env PATH={stub_dir} gh issue create --body safe",
        "/usr/bin/env PATH={stub_dir} gh issue create --body safe",
        "command {stub} issue create --body safe",
        "exec {stub} issue create --body safe",
        "bash -c 'PATH={stub_dir} gh issue create --body safe'",
        "bash -c 'eval gh issue create --body safe'",
        "bash -c '/usr/bin/env gh issue create --body safe'",
        "bash -c $'gh issue create --body safe'",
        "env -S '{stub} issue create --body safe'",
        "eval 'PATH={stub_dir} gh issue create --body safe'",
        ">/dev/null {stub} issue create --body safe",
        "bash -c '>/dev/null {stub} issue create --body safe'",
        "{{ {stub} issue create --body safe; }}",
        "nice {stub} issue create --body safe",
        "nohup {stub} issue create --body safe",
        "sudo {stub} issue create --body safe",
        "bash -c 'c={stub}; $c issue create --body safe'",
        "printf '%s\\n' '{stub} issue create --body safe' | bash",
        "bash <<< '{stub} issue create --body safe'",
        "busybox sh -c '{stub} issue create --body safe'",
        "{{{stub},issue,create,--body,safe}}",
        "set -- {stub}; $@ issue create --body safe",
        'set -- {stub}; "$@" issue create --body safe',
        "cat <({stub} issue create --body safe)",
        "cat >({stub} issue create --body safe)",
        "find . -exec {stub} issue create --body safe \\;",
        "flock /tmp/lock {stub} issue create --body safe",
        ".venv/bin/python -c \"import os; os.execl('{stub}', 'gh', 'issue', 'create', '--body', 'safe')\"",
        "{stub_dir}/g'h' issue create --body safe",
        "{stub_dir}/g\\h issue create --body safe",
        "flock /tmp/lock {stub_dir}/g'h' issue create --body safe",
        "find . -exec {stub_dir}/g'h' issue create --body safe \\;",
        "cat <(PATH={stub_dir} g'h' issue create --body safe)",
        "{stub_dir}/g{{h..h}} issue create --body safe",
        "PATH={stub_dir} g{{h..h}} issue create --body safe",
        "find . -exec {stub_dir}/g{{h..h}} issue create --body safe \\;",
        "flock /tmp/lock {stub_dir}/g{{h..h}} issue create --body safe",
        "cat <({stub_dir}/g{{h..h}} issue create --body safe)",
        'a={stub_dir}/g; b=h; "$a$b" issue create --body safe',
        'a={stub_dir}/g; b=h; c=issue; d=create; "$a$b" "$c" "$d" --body safe',
        r"PATH={stub_dir} $'g\x68' $'issue' $'create' --body safe",
        "PATH={stub_dir} g{{h..h..1}} issue${{IFS}}create --body safe",
        "PATH={stub_dir} g{{h..h..1}} api repos/o/r/issues -f title=t -f body=b",
        r"PATH={stub_dir} {{g,}}{{,}}{{,}}{{,}}{{,}}{{h,}} $'issue' $'create' --body safe",
        r"flock /tmp/lock PATH={stub_dir} $'g\x68' $'issue' $'create' --body safe",
        r"find . -exec PATH={stub_dir} $'g\x68' $'issue' $'create' --body safe \;",
        r"cat <(PATH={stub_dir} $'g\x68' $'issue' $'create' --body safe)",
        'eval \'a={stub_dir}/g; b=h; c=issue; d=create; "$a$b" "$c" "$d" --body safe\'',
        'bash -c \'a={stub_dir}/g; b=h; c=issue; d=create; "$a$b" "$c" "$d" --body safe\'',
        "a=issue; b=create; {stub_dir}/g? $a $b",
        "a=issue; b=create; {stub_dir}/g* $a $b",
        "a=issue; b=create; {stub_dir}/g[h] $a $b",
        "a=issue; b=create; env {stub_dir}/g? $a $b",
        "a=issue; b=create; command {stub_dir}/g? $a $b",
        "a=issue; b=create; find . -exec {stub_dir}/g? $a $b \\;",
        "bash -c 'a=issue; b=create; {stub_dir}/g? $a $b'",
    ],
)
def test_codex_blocks_publication_bypass_shapes(tmp_path, shape):
    marker = tmp_path / "published"
    stub = tmp_path / "gh"
    stub.write_text(f"#!/bin/bash\nprintf published > {shlex.quote(str(marker))}\n")
    stub.chmod(0o755)
    command = shape.format(stub_dir=shlex.quote(str(tmp_path)), stub=shlex.quote(str(stub)))
    payload = {"tool_name": "Bash", "cwd": str(REPO_ROOT), "tool_input": {"command": command}}
    env = {**os.environ, "PATH": str(REPO_ROOT / "scripts/agent_runtime/shims") + os.pathsep + os.environ["PATH"]}
    result = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=REPO_ROOT,
        env=env,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=2,
    )
    # Offline publication stub: if admission succeeds, prove whether it ran.
    if result.returncode == 0:
        subprocess.run(["bash", "-c", command], env=env, capture_output=True, timeout=10)
    assert result.returncode == 2, result.stderr
    assert not marker.exists()
    assert "not fully shim guarded" in result.stderr


@pytest.mark.parametrize("wrapper", ["", "env ", "/usr/bin/env ", "command ", "command -- ", "exec "])
def test_codex_admits_single_resolved_shim_call(monkeypatch, wrapper):
    shim = REPO_ROOT / "scripts/agent_runtime/shims"
    monkeypatch.setenv("PATH", str(shim) + os.pathsep + os.environ["PATH"])
    assert (
        codex_hook_policy._publication_command_code(
            json.dumps({"tool_input": {"command": wrapper + "gh --version"}}),
            REPO_ROOT / "agents_extensions/shared/hooks",
        )
        == 0
    )


def test_codex_entry_never_uses_session_selected_interpreter(tmp_path):
    source_base = tmp_path / "source-fixture"
    source_base.mkdir()
    source, _ = _make_linked_worktree(source_base)
    entry = source / "scripts/agent_runtime/codex_hook_entry.sh"
    entry.parent.mkdir(parents=True)
    shutil.copyfile(ENTRY, entry)
    source_marker = tmp_path / "source-interpreter-ran"
    # A distinctive result proves this copied entry used the source interpreter.
    (source / ".venv/bin/python").write_text(
        f"#!/bin/bash\nprintf ran > {shlex.quote(str(source_marker))}\nexit 2\n"
    )
    session_base = tmp_path / "session-fixture"
    session_base.mkdir()
    primary, session = _make_linked_worktree(session_base)
    marker = tmp_path / "foreign-interpreter-ran"
    (primary / ".venv/bin/python").write_text(
        f"#!/bin/bash\nprintf ran > {shlex.quote(str(marker))}\nexit 0\n"
    )
    payload = {"tool_name": "Write", "cwd": str(session), "tool_input": {"file_path": str(primary / "README.md")}}
    result = subprocess.run(
        ["bash", str(entry), "pre-tool-use"],
        cwd=session,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=2,
    )
    assert result.returncode == 2, result.stderr
    assert source_marker.read_text() == "ran"
    assert not marker.exists()


@pytest.mark.parametrize(
    "command",
    [
        "echo gh",
        'git commit -m "fix gh routing"',
        "git commit -m 'fix gh $(pwd)'",
        "echo g? '$a'",
        "pytest tests/test_*.py",
    ],
)
def test_codex_publication_data_words_remain_allowed(command):
    assert (
        codex_hook_policy._publication_command_code(
            json.dumps({"tool_input": {"command": command}}),
            REPO_ROOT / "agents_extensions/shared/hooks",
        )
        == 0
    )


@pytest.mark.parametrize("defect", ["missing-source", "unavailable-source", "symlink-loop", "missing-entry"])
def test_hook_resolution_errors_block_with_exit_two(tmp_path, defect):
    source, session = _make_linked_worktree(tmp_path)
    entry = source / "entry.sh"
    entry.write_text("exit 0\n")
    _run(["git", "add", "entry.sh"], cwd=source)
    _run(["git", "commit", "-m", "tracked hook"], cwd=source)
    command = _portable_hook_command(f"bash {shlex.quote(str(entry))}", source)
    (session / "entry.sh").write_text("exit 0\n")
    env = {**os.environ, "LU_CODEX_HOOK_SOURCE": str(source)}
    if defect == "missing-source":
        env.pop("LU_CODEX_HOOK_SOURCE", None)
    elif defect == "unavailable-source":
        env["LU_CODEX_HOOK_SOURCE"] = str(tmp_path / "missing")
    elif defect == "missing-entry":
        entry.unlink()
    else:
        entry.unlink()
        entry.symlink_to(entry.name)
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=session,
        env=env,
        input="{}",
        text=True,
        capture_output=True,
        timeout=2,
    )
    assert result.returncode == 2, result.stderr


@pytest.mark.parametrize("tool", ["write_stdin", "Bash"])
@pytest.mark.parametrize("chars", ["", "echo synthetic\n", "gh issue create --body synthetic\n"])
def test_codex_interactive_input_is_blocked(monkeypatch, tool, chars):
    import io
    import re

    matcher = _manifest()["hooks"]["PreToolUse"][0]["matcher"]
    assert re.fullmatch(matcher, tool)
    monkeypatch.setattr(
        sys,
        "argv",
        ["policy", "--python-bin", "synthetic", "--hooks-dir", "synthetic", "--canonical-root", "synthetic"],
    )
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": tool,
                    "tool_input": {"session_id": 1, "chars": chars},
                }
            )
        ),
    )
    monkeypatch.setattr(codex_hook_policy, "_run_specs", lambda *args: pytest.fail("input admitted"))
    assert codex_hook_policy.main() == 2


@pytest.mark.parametrize("code", [1, 127, -9])
def test_codex_guard_errors_always_block(code):
    assert _result_code([codex_hook_policy.GuardResult("synthetic", code, "", "")]) == 2


def test_codex_missing_guards_block(tmp_path):
    result = run_guard(Path(sys.executable), tmp_path / "missing.py", "{}", 1)
    assert _result_code([result]) == 2
    result = run_guard(tmp_path / "missing-interpreter", tmp_path / "missing.py", "{}", 1)
    assert _result_code([result]) == 2
    result = _run_enforce_venv(tmp_path, tmp_path, "{}")
    assert result.returncode == 127
    assert _result_code([result]) == 2


def test_codex_public_text_rewrite_without_decision_blocks(capsys):
    result = codex_hook_policy.GuardResult(
        "guard-public-github-text.py",
        0,
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": {"command": "echo synthetic"}}}
        ),
        "",
    )
    assert _result_code([result]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "blocking fail-closed" in captured.err


@pytest.mark.parametrize("payload", ["{", "[]"])
def test_codex_invalid_tool_payload_blocks(tmp_path, payload):
    result = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=tmp_path,
        input=payload,
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 2


@pytest.mark.parametrize("tool", ["write_stdin", "Bash"])
def test_codex_entry_blocks_interactive_input(tmp_path, tool):
    result = subprocess.run(
        ["bash", str(ENTRY), "pre-tool-use"],
        cwd=tmp_path,
        input=json.dumps({"tool_name": tool, "tool_input": {"session_id": 1, "chars": "echo synthetic\n"}}),
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "interactive input" in result.stderr


@pytest.mark.parametrize("explicit_cleanup", [False, True])
def test_worker_source_handle_has_weak_owner(tmp_path, explicit_cleanup):
    from scripts.agent_runtime.adapters.codex import _HOOK_SOURCE_HANDLES

    adapter = CodexAdapter()
    plan = adapter.build_invocation(
        prompt="test", mode="workspace-write", cwd=tmp_path,
        model=None, task_id=None, session_id=None, tool_config=None,
    )
    plan_id = id(plan)
    owner = weakref.ref(plan)
    source_fd = _HOOK_SOURCE_HANDLES[plan_id][1]
    output = plan.output_file
    assert _HOOK_SOURCE_HANDLES[plan_id][0]() is plan
    os.fstat(source_fd)
    if explicit_cleanup:
        adapter.cleanup_invocation(plan)
        adapter.cleanup_invocation(plan)
    del plan
    gc.collect()
    assert owner() is None
    assert plan_id not in _HOOK_SOURCE_HANDLES
    with pytest.raises(OSError):
        os.fstat(source_fd)
    output.unlink(missing_ok=True)


@pytest.mark.parametrize("defect", ["missing-interpreter", "exit-127"])
def test_portable_hook_interpreter_failure_blocks(tmp_path, defect):
    source, session = _make_linked_worktree(tmp_path)
    entry = source / "entry.sh"
    marker = tmp_path / "entry-ran"
    entry.write_text(f"printf ran > {shlex.quote(str(marker))}\n")
    _run(["git", "add", "entry.sh"], cwd=source)
    _run(["git", "commit", "-m", "tracked hook"], cwd=source)
    command = _portable_hook_command(f"bash {shlex.quote(str(entry))}", source)
    interpreter = source / ".venv/bin/python"
    if defect == "missing-interpreter":
        interpreter.unlink()
    else:
        interpreter.write_text("#!/bin/bash\nexit 127\n")
    result = subprocess.run(
        ["bash", "-c", command], cwd=session,
        env={**os.environ, "LU_CODEX_HOOK_SOURCE": str(source)},
        input="{}", text=True, capture_output=True, timeout=2,
    )
    assert result.returncode == 2, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("command", ["synthetic*/echo gh", "synthetic?/git commit -m gh"])
def test_codex_data_mention_requires_literal_executable(command):
    assert codex_hook_policy._publication_command_code(
        json.dumps({"tool_input": {"command": command}}),
        REPO_ROOT / "agents_extensions/shared/hooks",
    ) == 2
