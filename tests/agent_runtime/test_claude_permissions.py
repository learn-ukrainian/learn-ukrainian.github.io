"""Command and deployed-hook coverage for headless Claude workers."""

import asyncio
import importlib.util
import io
import json
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import (
    REVIEWER_PERMISSION_PROFILE,
    SOURCES_PERSISTING_TOOLS,
    SOURCES_READ_ONLY_TOOLS,
    ClaudeAdapter,
)
from scripts.agent_runtime.env_sanitize import build_agent_env
from scripts.common.repo_root import project_interpreter


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_claude_worker_modes_install_guards(mode: str, tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--bare" not in plan.cmd
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    hooks = settings["hooks"]["PreToolUse"]
    assert {"Bash", "Write|Edit|MultiEdit"} <= {group["matcher"] for group in hooks}
    commands = [hook["command"] for group in hooks for hook in group["hooks"]]
    root = Path(__file__).resolve().parents[2]
    tracked_hooks = root / "agents_extensions/shared/hooks"
    interpreter = str(project_interpreter(root))
    for name in (
        "guard-primary-checkout-write.py",
        "guard-secret-print.py",
        "guard-pr-merge.py",
        "guard-branch-switch-in-main.py",
        "guard-admin-merge.py",
        "enforce-venv.sh",
        "heal-core-bare.py",
    ):
        tracked = str(tracked_hooks / name)
        expected = shlex.join([interpreter, tracked]) if name in _PINNED_GUARDS else shlex.quote(tracked)
        assert expected in commands
    assert all(Path(arg).is_file() for command in commands for arg in shlex.split(command))
    assert shlex.quote(str(tracked_hooks / "guard-reviewer-publish.py")) not in commands
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
    assert "--disallowedTools" not in plan.cmd
    if mode == "workspace-write":
        # Headless print mode denies approval-requiring tools. dontAsk plus the
        # worker allow list is the documented non-interactive mode. Danger keeps
        # its own flag and must not grow a --permission-mode.
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
        granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        assert granted == [
            "Bash",
            "Read",
            "Edit",
            "Write",
            "Grep",
            "Glob",
            "LS",
            "WebFetch",
            "WebSearch",
        ]
        assert "NotebookEdit" not in granted
        assert not any(name.startswith("mcp__") for name in granted)
        assert plan.cmd.count("--allowedTools") == 1
        assert "--dangerously-skip-permissions" not in plan.cmd
    else:
        assert "--permission-mode" not in plan.cmd
        assert "--allowedTools" not in plan.cmd
        assert ("--dangerously-skip-permissions" in plan.cmd) is (mode == "danger")


def test_workspace_write_keeps_explicit_allowed_tools(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"allowed_tools": "mcp__sources__*"},
    )
    assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
    assert plan.cmd.count("--allowedTools") == 1
    assert plan.cmd[plan.cmd.index("--allowedTools") + 1] == "mcp__sources__*"
    assert "Bash" not in plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "--disallowedTools" not in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd


def test_workspace_write_names_mcp_servers_from_config(tmp_path: Path) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(
        json.dumps({"mcpServers": {"sources": {}, "other_tool": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(config)},
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__sources__*" in granted
    assert "mcp__other_tool__*" in granted
    assert "mcp__sources" not in granted
    assert "NotebookEdit" not in granted


def test_workspace_write_mcp_config_comes_from_worker_cwd(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"worker_only": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__worker_only__*" in granted
    assert "mcp__sources__*" not in granted


def test_explicit_mcp_config_path_wins_over_worker_cwd(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"from_cwd": {}}}),
        encoding="utf-8",
    )
    explicit = tmp_path / "explicit.json"
    explicit.write_text(
        json.dumps({"mcpServers": {"from_explicit": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(explicit)},
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_explicit__*" in granted
    assert "mcp__from_cwd__*" not in granted

    missing = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(tmp_path / "absent.json")},
    )
    missing_granted = missing.cmd[missing.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_cwd__*" not in missing_granted
    assert not any(name.startswith("mcp__") for name in missing_granted)


def test_workspace_write_rejects_invalid_mcp_config(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    shaped = tmp_path / "shaped"
    shaped.mkdir()
    (shaped / ".mcp.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="mcpServers"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=shaped,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )


def test_workspace_write_rejects_unreadable_mcp_config(tmp_path: Path) -> None:
    config = tmp_path / ".mcp.json"
    config.write_text('{"mcpServers": {}}\n', encoding="utf-8")
    config.chmod(0)
    try:
        with pytest.raises(ValueError, match="unreadable"):
            ClaudeAdapter().build_invocation(
                prompt="inspect",
                mode="workspace-write",
                cwd=tmp_path,
                model=None,
                task_id=None,
                session_id=None,
                tool_config=None,
            )
    finally:
        config.chmod(0o644)


def test_workspace_write_rejects_inexpressible_mcp_server_name(tmp_path: Path) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(
        json.dumps({"mcpServers": {"ok": {}, "bad,name": {}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cannot be expressed"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"mcp_config_path": str(config)},
        )


def test_reviewer_tools_opt_in_installs_profile(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
    sources_read = {f"mcp__sources__{name}" for name in SOURCES_READ_ONLY_TOOLS}
    sources_persisting = {f"mcp__sources__{name}" for name in SOURCES_PERSISTING_TOOLS}
    assert set(REVIEWER_PERMISSION_PROFILE["allow"]) | sources_read == set(
        plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    )
    assert set(REVIEWER_PERMISSION_PROFILE["deny"]) | sources_persisting == set(
        plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
    )
    assert plan.env_overrides["LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK"] == "1"
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)


def test_discussion_readonly_keeps_separate_permissions(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"discussion_readonly": True},
    )
    assert "--settings" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == "Read,Grep,Glob,LS"
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides


def test_review_isolation_keeps_separate_permissions(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters import claude
    from scripts.review import isolation

    mcp = tmp_path / "empty.json"
    mcp.write_text('{"mcpServers":{}}\n', encoding="utf-8")
    monkeypatch.setattr(isolation, "validated_review_write_root", lambda _: tmp_path)
    monkeypatch.setattr(claude, "_isolated_review_response_schema", lambda _: "{}")
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "review_isolation": True,
            "review_engine_binary": "/bin/true",
            "strict_mcp_config": True,
            "mcp_config_path": str(mcp),
            "setting_sources": "",
            "allowed_tools": "",
        },
    )
    assert "--settings" in plan.cmd
    assert "--safe-mode" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == ""


@pytest.mark.repo_wide
@pytest.mark.parametrize("has_interpreter", [True, False], ids=["with-interpreter", "missing-interpreter"])
def test_tracked_hooks_work_in_fresh_clone_without_deployed_claude(
    tmp_path: Path, monkeypatch, has_interpreter: bool
) -> None:
    from scripts.agent_runtime.adapters import claude

    # Fixture clone of the tracked hook tree. Cloning this repository
    # (`git clone --shared`) exceeds the 30s bound when the host is busy (#8947).
    root = Path(__file__).resolve().parents[2]
    seed = tmp_path / "fixture"
    clone = tmp_path / "fresh"
    seed.mkdir()
    tracked_claude = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "--name-only", "HEAD", ".claude"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert tracked_claude.stdout == ""
    archived = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "archive",
            "--format=tar",
            "HEAD",
            "agents_extensions/shared/settings.json",
            "agents_extensions/shared/hooks",
            "scripts/agent_runtime/adapters/claude.py",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    with tarfile.open(fileobj=io.BytesIO(archived.stdout), mode="r|") as bundle:
        bundle.extractall(seed, filter="data")
    for args in (
        ["init"],
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.invalid"],
        ["add", "agents_extensions", "scripts"],
        ["commit", "-m", "fixture"],
    ):
        subprocess.run(["git", "-C", str(seed), *args], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "clone", str(seed), str(clone)], check=True, capture_output=True, timeout=30)
    assert not (clone / ".claude").exists()
    monkeypatch.setattr(claude, "__file__", str(clone / "scripts/agent_runtime/adapters/claude.py"))
    interpreter = clone / ".venv/bin/python"
    if not has_interpreter:
        assert not interpreter.exists()
        # Hosted CI's unowned interpreter is a valid fallback. Pin a foreign
        # checkout's interpreter so this case exercises refusal on every runner.
        foreign = tmp_path / "other/.venv/bin/python"
        foreign.parent.mkdir(parents=True)
        foreign.symlink_to(sys.executable)
        monkeypatch.setattr(sys, "executable", str(foreign))
        with pytest.raises(FileNotFoundError, match="project interpreter not found"):
            claude._worker_guard_settings(publish_guard=True)
        return

    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(sys.executable)
    settings = json.loads(claude._worker_guard_settings(publish_guard=True))
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    tracked_hooks = clone / "agents_extensions/shared/hooks"
    assert shlex.quote(str(tracked_hooks / "guard-reviewer-publish.py")) in commands
    assert all(Path(arg).is_file() for command in commands for arg in shlex.split(command))
    for name in _PINNED_GUARDS:
        expected = shlex.join([str(interpreter), str(tracked_hooks / name)])
        assert expected in commands
        result = subprocess.run(
            shlex.split(expected),
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}),
            cwd=clone,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    assert not (clone / ".claude").exists()


_ROOT = Path(__file__).resolve().parents[2]
_WRAPPER = 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh"'
_PINNED_GUARDS = ("guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py")


def _guard_source_tree(root: Path, commands: list[str], *, interpreter: bool = True) -> Path:
    """A checkout-shaped tree whose settings name ``commands`` as Bash PreToolUse hooks."""
    hooks = root / "agents_extensions/shared/hooks"
    hooks.mkdir(parents=True)
    for name in ("enforce-venv.sh", "guard-secret-print.py", *_PINNED_GUARDS):
        (hooks / name).write_text("#!/bin/sh\n", encoding="utf-8")
    groups = [{"matcher": "Bash", "hooks": [{"type": "command", "command": c, "timeout": 7} for c in commands]}]
    (root / "agents_extensions/shared/settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": groups}}), encoding="utf-8"
    )
    if interpreter:
        python = root / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")
    return hooks


def _settings_from(root: Path, monkeypatch) -> list[dict]:
    from scripts.agent_runtime.adapters import claude

    monkeypatch.setattr(claude, "__file__", str(root / "scripts/agent_runtime/adapters/claude.py"))
    settings = json.loads(claude._worker_guard_settings())
    return [hook for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]


def test_worker_guards_run_parser_guards_under_the_project_interpreter(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters.claude import PROJECT_PYTHON_GUARDS

    assert set(_PINNED_GUARDS) == PROJECT_PYTHON_GUARDS
    hooks_dir = _guard_source_tree(
        tmp_path,
        [
            "$CLAUDE_PROJECT_DIR/.claude/hooks/enforce-venv.sh",
            *(f"{_WRAPPER} {name}" for name in _PINNED_GUARDS),
            "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-secret-print.py",
            "sh -c 'entire hooks claude-code pre-task || true'",
        ],
    )
    hooks = _settings_from(tmp_path, monkeypatch)
    python = str(tmp_path / ".venv/bin/python")
    assert [hook["command"] for hook in hooks] == [
        str(hooks_dir / "enforce-venv.sh"),
        *(shlex.join([python, str(hooks_dir / name)]) for name in _PINNED_GUARDS),
        str(hooks_dir / "guard-secret-print.py"),
    ]
    assert all(hook["timeout"] == 7 and hook["type"] == "command" for hook in hooks)


_SPLIT_WRAPPER = 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-"hook.sh'
_ESCAPED_WRAPPER = r"bash $CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python\-hook.sh"


@pytest.mark.parametrize(
    "command",
    [
        f"{_SPLIT_WRAPPER} guard-pr-merge.py",
        f"{_WRAPPER} 'guard-pr-'merge.py",
        f"{_ESCAPED_WRAPPER} guard\\-pr-merge.py",
        f'{_WRAPPER} "guard-pr-merge.py"',
    ],
)
def test_worker_guards_classify_the_wrapper_after_tokenization(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    [hook] = _settings_from(tmp_path, monkeypatch)
    assert hook["command"] == shlex.join([str(tmp_path / ".venv/bin/python"), str(hooks_dir / "guard-pr-merge.py")])


@pytest.mark.parametrize(
    "command",
    [
        '"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-secret-"print.py',
        r"$CLAUDE_PROJECT_DIR/.claude/hooks/guard\-secret-print.py",
    ],
)
def test_worker_guards_classify_the_plain_path_after_tokenization(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    [hook] = _settings_from(tmp_path, monkeypatch)
    assert hook["command"] == str(hooks_dir / "guard-secret-print.py")


@pytest.mark.parametrize(
    "command",
    [
        "sh -c 'entire hooks claude-code pre-task || true'",
        "echo hello",
        "",
    ],
)
def test_worker_guards_leave_unrelated_hooks_untouched(tmp_path: Path, command: str) -> None:
    from scripts.agent_runtime.adapters.claude import _worker_guard_invocation

    assert _worker_guard_invocation(command, tmp_path) is None


@pytest.mark.parametrize(
    "command",
    [
        # Unknown guard, extra or missing arguments in the canonical spelling.
        f"{_WRAPPER} guard-secret-print.py",
        f"{_WRAPPER} guard-pr-merge.py --extra",
        f"{_WRAPPER} ../hooks/guard-pr-merge.py",
        f"{_WRAPPER}",
        # The same defects behind split quoting and backslash spellings.
        f"{_SPLIT_WRAPPER} guard-pr-merge.py --extra",
        f"{_SPLIT_WRAPPER}",
        f"{_SPLIT_WRAPPER} guard-secret-print.py",
        f"{_ESCAPED_WRAPPER} guard-pr-merge.py extra",
        f"{_ESCAPED_WRAPPER}",
        f"{_WRAPPER} 'guard-pr-'merge.py --extra",
        # Another launcher, wrapper path or nesting.
        'sh "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh" guard-pr-merge.py',
        '"$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh" guard-pr-merge.py',
        'bash "/elsewhere/run-project-python-hook.sh" guard-pr-merge.py',
        "sh -c 'bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh\" guard-pr-merge.py'",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh",
        # A parser guard or the hooks directory outside both supported forms.
        "/usr/bin/python3 'guard-pr-'merge.py",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-pr-merge.py --extra",
        "bash $CLAUDE_PROJECT_DIR/.claude/hooks/enforce-venv.sh",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/../hooks/guard-pr-merge.py",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/",
    ],
)
def test_worker_guards_refuse_other_fleet_guard_forms(tmp_path: Path, monkeypatch, command: str) -> None:
    _guard_source_tree(tmp_path, [command])
    with pytest.raises(RuntimeError, match="Claude worker guard has an unsupported form"):
        _settings_from(tmp_path, monkeypatch)


@pytest.mark.parametrize(
    "command",
    [f"{_WRAPPER} 'guard-pr-merge.py", "sh -c 'entire hooks claude-code pre-task"],
)
def test_worker_guards_refuse_an_unreadable_hook_command(tmp_path: Path, monkeypatch, command: str) -> None:
    _guard_source_tree(tmp_path, [command])
    with pytest.raises(RuntimeError, match="unreadable"):
        _settings_from(tmp_path, monkeypatch)


def test_grok_agent_definition_keeps_a_split_quoted_parser_guard(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters.grok_build import _guard_agent_definition

    hooks_dir = _guard_source_tree(tmp_path, [f"{_SPLIT_WRAPPER} guard-pr-merge.py"])
    _settings_from(tmp_path, monkeypatch)  # points the adapter at the fixture tree
    definition = _guard_agent_definition(
        name="probe", description="probe", body="probe", publish_guard=False, native_aliases=False
    )
    pinned = shlex.join([str(tmp_path / ".venv/bin/python"), str(hooks_dir / "guard-pr-merge.py")])
    bridge = shlex.quote(str(_ROOT / "scripts/agent_runtime/grok_hook_bridge.py"))
    assert json.dumps(f"{bridge} {shlex.quote(pinned)}") in definition


@pytest.mark.parametrize(
    "command",
    [f"{_WRAPPER} guard-pr-merge.py", "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-pr-merge.py"],
)
def test_worker_guards_refuse_a_missing_guard_file(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    (hooks_dir / "guard-pr-merge.py").unlink()
    with pytest.raises(RuntimeError, match="Claude worker guard unavailable"):
        _settings_from(tmp_path, monkeypatch)


def test_worker_guards_fail_closed_without_a_project_interpreter(tmp_path: Path, monkeypatch) -> None:
    # No .venv in the tree, and the running interpreter belongs to another checkout.
    root = tmp_path / "checkout"
    _guard_source_tree(root, [f"{_WRAPPER} guard-pr-merge.py"], interpreter=False)
    foreign = tmp_path / "other/.venv/bin/python"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(foreign))
    with pytest.raises(FileNotFoundError, match="project interpreter not found"):
        _settings_from(root, monkeypatch)


def test_readonly_transport_rejects_every_push_wrapper(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True, timeout=30)
    (work / "sample.txt").write_text("sample\n", encoding="utf-8")
    for args in (
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.invalid"],
        ["add", "sample.txt"],
        ["commit", "-m", "fixture"],
        ["remote", "add", "origin", str(remote)],
        ["config", "remote.origin.push", "HEAD:refs/heads/probe"],
    ):
        subprocess.run(["git", "-C", str(work), *args], check=True, capture_output=True, timeout=30)

    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=work,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    assert (
        subprocess.run(
            ["git", "-C", str(work), "status", "--porcelain"], env=env, capture_output=True, timeout=30
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "-C", str(work), "ls-remote", "origin"], env=env, capture_output=True, timeout=30
        ).returncode
        == 0
    )
    for command, cwd in (
        (["git", "push"], work),
        (["git", "-C", str(work), "push"], tmp_path),
        (["bash", "-c", "git push"], work),
        (
            [sys.executable, "-c", "import subprocess; raise SystemExit(subprocess.run(['git','push']).returncode)"],
            work,
        ),
    ):
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode != 0, (command, result.stdout, result.stderr)
        refs = subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname)"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        assert refs.stdout == ""


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("git push", True),
        ("git -C /tmp/example push --dry-run", True),
        ("git -c core.quotePath=false push", True),
        ("env X=1 git push", True),
        ("bash -c 'git push'", True),
        ("sh -c 'gh api -f body=probe repos/o/r/issues/1/comments'", True),
        ("eval 'gh pr merge 1'", True),
        ("gh issue reopen 1", True),
        ("gh pr create --help", True),
        ("gh api --method PATCH repos/o/r", True),
        ("gh api -X POST repos/o/r", True),
        ("gh api --raw-field body=x repos/o/r", True),
        ("gh release create v1", True),
        ("gh workflow run ci.yml", True),
        ("gh pr view 1 --json number", False),
        ("gh api -X GET repos/o/r", False),
        ("git status --short", False),
    ],
)
def test_reviewer_publish_hook(command: str, blocked: bool) -> None:
    hook = Path(__file__).resolve().parents[2] / "agents_extensions/shared/hooks/guard-reviewer-publish.py"
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run([sys.executable, str(hook)], input=payload, capture_output=True, text=True, timeout=30)
    assert (result.returncode == 2) is blocked, (command, result.stderr)


SOURCES_RULES = [f"mcp__sources__{name}" for name in SOURCES_READ_ONLY_TOOLS]
PERSISTING_RULES = [f"mcp__sources__{name}" for name in SOURCES_PERSISTING_TOOLS]
SOURCES_SERVER_PATH = Path(__file__).resolve().parents[2] / ".mcp/servers/sources/server.py"


def _reviewer_plan(cwd: Path, **extra) -> list[str]:
    return (
        ClaudeAdapter()
        .build_invocation(
            prompt="inspect",
            mode="read-only",
            cwd=cwd,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"reviewer_tools": True, **extra},
        )
        .cmd
    )


def _granted(cmd: list[str]) -> list[str]:
    assert cmd.count("--allowedTools") == 1
    return cmd[cmd.index("--allowedTools") + 1].split(",")


def _denied(cmd: list[str]) -> list[str]:
    assert cmd.count("--disallowedTools") == 1
    return cmd[cmd.index("--disallowedTools") + 1].split(",")


def _mcp_config(cmd: list[str]) -> dict:
    """The one MCP config the argv loads; it must be strict so nothing else is merged in."""
    assert cmd.count("--mcp-config") == 1
    assert cmd.count("--strict-mcp-config") == 1
    index = cmd.index("--mcp-config")
    assert cmd[index - 1] == "--strict-mcp-config"
    return json.loads(cmd[index + 1])


def test_sources_tool_split_matches_server_annotations() -> None:
    """Granted tools are exactly the read-only ones; persisting ones are exactly the rest (#9551).

    tests/mcp/test_sources_tool_side_effects.py ties the annotations to the writes each tool attempts.
    """
    spec = importlib.util.spec_from_file_location("sources_server_contract", SOURCES_SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    tools = asyncio.run(server.list_tools())
    assert sorted(tool.name for tool in tools if tool.annotations.read_only_hint is True) == list(
        SOURCES_READ_ONLY_TOOLS
    )
    assert sorted(tool.name for tool in tools if tool.annotations.read_only_hint is False) == list(
        SOURCES_PERSISTING_TOOLS
    )
    assert "query_wikipedia" in SOURCES_PERSISTING_TOOLS
    assert all(tool.annotations.destructive_hint is False for tool in tools)


def test_reviewer_loads_only_the_trusted_sources_server(tmp_path: Path) -> None:
    from scripts.agent_runtime.review_mcp import (
        isolated_sources_mcp_config,
        review_server_checkout,
        sources_server_launch,
    )
    from scripts.common.repo_root import project_interpreter

    cmd = _reviewer_plan(tmp_path)
    config = _mcp_config(cmd)
    assert config == isolated_sources_mcp_config(*sources_server_launch())
    server = config["mcpServers"]["sources"]
    assert list(config["mcpServers"]) == ["sources"]
    # tests/agent_runtime/test_review_mcp.py launches this under a hostile session environment.
    assert server == {
        "command": "/usr/bin/env",
        "args": [
            "-i",
            "PATH=/usr/bin:/bin",
            "LC_ALL=C.UTF-8",
            str(project_interpreter()),
            "-I",
            str(review_server_checkout() / ".mcp" / "servers" / "sources" / "server.py"),
        ],
    }
    granted = _granted(cmd)
    assert granted == [*REVIEWER_PERMISSION_PROFILE["allow"], *SOURCES_RULES]
    assert "mcp__sources__*" not in granted
    assert not set(PERSISTING_RULES) & set(granted)
    # Deny outranks any allow rule a reviewed checkout's settings file could add.
    assert _denied(cmd) == [*REVIEWER_PERMISSION_PROFILE["deny"], *PERSISTING_RULES]
    assert "mcp__sources__query_wikipedia" in _denied(cmd)
    assert not {"Edit", "Write", "NotebookEdit", "MultiEdit"} & set(granted)
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    settings = json.loads(cmd[cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)
    assert any(command.endswith("guard-primary-checkout-write.py") for command in commands)


@pytest.mark.parametrize(
    "worktree_config",
    [
        {"mcpServers": {"sources": {"type": "streamable-http", "url": "http://127.0.0.1:9/mcp"}}},
        {"mcpServers": {"sources": {"command": "/bin/sh", "args": ["-c", "write-anything"]}}},
        {"mcpServers": {"sources": {"command": "python", "args": ["evil_server.py"]}, "other_tool": {}}},
        {"mcpServers": {"other_tool": {"command": "python", "args": ["other.py"]}}},
        "{not json",
    ],
    ids=["sources-url", "sources-command", "sources-plus-other", "other-only", "invalid"],
)
def test_worktree_mcp_json_gains_the_reviewer_nothing(tmp_path: Path, worktree_config) -> None:
    """A reviewed branch's .mcp.json never reaches the reviewer argv, whatever it names `sources` (#9551)."""
    clean = tmp_path / "clean"
    clean.mkdir()
    reviewed = tmp_path / "reviewed"
    reviewed.mkdir()
    text = worktree_config if isinstance(worktree_config, str) else json.dumps(worktree_config)
    (reviewed / ".mcp.json").write_text(text, encoding="utf-8")
    cmd = _reviewer_plan(reviewed)
    assert cmd == _reviewer_plan(clean)
    joined = "\n".join(cmd)
    for planted in ("127.0.0.1:9", "/bin/sh", "evil_server.py", "other_tool", "other.py"):
        assert planted not in joined
    assert not any(name.startswith("mcp__other_tool") for name in _granted(cmd))


def test_reviewer_refuses_a_caller_mcp_config_outside_formal_full_access(tmp_path: Path) -> None:
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"mcpServers": {"sources": {"command": "/bin/sh"}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="formal full-access"):
        _reviewer_plan(tmp_path, mcp_config_path=str(config))
    with pytest.raises(ValueError, match="formal full-access"):
        _reviewer_plan(tmp_path, mcp_config_path=str(config), review_access="isolated")


def test_full_review_access_keeps_review_tool_set(tmp_path: Path) -> None:
    from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")  # never read for formal attempts
    attempt = tmp_path / "attempt.json"
    cmd = _reviewer_plan(tmp_path, mcp_config_path=str(attempt), strict_mcp_config=True, review_access="full")
    assert _granted(cmd) == [
        *REVIEWER_PERMISSION_PROFILE["allow"],
        *review_tools_allowed_csv("claude", "full").split(","),
    ]
    assert _denied(cmd) == list(REVIEWER_PERMISSION_PROFILE["deny"])
    # The formal attempt's own harness-written config is the only one loaded.
    assert cmd.count("--mcp-config") == 1
    assert cmd[cmd.index("--mcp-config") + 1] == str(attempt)
    assert cmd[cmd.index("--mcp-config") - 1] == "--strict-mcp-config"


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_sources_config_leaves_write_and_danger_argv_unchanged(tmp_path: Path, mode: str) -> None:
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"sources": {}}}), encoding="utf-8")
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    assert "--disallowedTools" not in plan.cmd
    assert not any(rule in plan.cmd for rule in SOURCES_RULES)
    if mode == "workspace-write":
        assert _granted(plan.cmd) == [
            "Bash",
            "Read",
            "Edit",
            "Write",
            "Grep",
            "Glob",
            "LS",
            "WebFetch",
            "WebSearch",
            "mcp__sources__*",
        ]
    else:
        assert "--allowedTools" not in plan.cmd
        assert "--dangerously-skip-permissions" in plan.cmd


@pytest.mark.parametrize("allowed_tools", ["mcp__sources__*", "Read,Bash(git push *)", ""])
@pytest.mark.parametrize("strict_mcp_config", [False, True])
def test_explicit_allowed_tools_are_not_widened_or_narrowed(
    tmp_path: Path,
    allowed_tools: str,
    strict_mcp_config: bool,
) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "reviewer_tools": True,
            "allowed_tools": allowed_tools,
            "mcp_config_path": str(tmp_path / "sources.json"),
            "strict_mcp_config": strict_mcp_config,
        },
    )
    assert plan.cmd.count("--allowedTools") == 1
    assert plan.cmd[plan.cmd.index("--allowedTools") + 1] == allowed_tools
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert not any(command.endswith("guard-reviewer-publish.py") for command in commands)


def test_readonly_content_writer_keeps_legacy_cli_permissions(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="write content",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={},
    )
    assert "--allowedTools" not in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
