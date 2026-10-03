"""Command and deployed-hook coverage for headless Claude workers."""

import asyncio
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import (
    REVIEWER_PERMISSION_PROFILE,
    SOURCES_READ_ONLY_TOOLS,
    ClaudeAdapter,
)
from scripts.agent_runtime.env_sanitize import build_agent_env


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_claude_worker_modes_install_guards(mode: str, tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode=mode, cwd=tmp_path, model=None,
        task_id=None, session_id=None, tool_config=None,
    )
    assert "--bare" not in plan.cmd
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    hooks = settings["hooks"]["PreToolUse"]
    assert {"Bash", "Write|Edit|MultiEdit"} <= {group["matcher"] for group in hooks}
    commands = [hook["command"] for group in hooks for hook in group["hooks"]]
    tracked_hooks = Path(__file__).resolve().parents[2] / "agents_extensions/shared/hooks"
    for name in (
        "guard-primary-checkout-write.py", "guard-secret-print.py",
        "guard-pr-merge.py", "guard-branch-switch-in-main.py",
        "guard-admin-merge.py", "enforce-venv.sh", "heal-core-bare.py",
    ):
        assert str(tracked_hooks / name) in commands
    assert all(Path(command).is_file() for command in commands)
    assert str(tracked_hooks / "guard-reviewer-publish.py") not in commands
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
    assert "--disallowedTools" not in plan.cmd
    if mode == "workspace-write":
        # Headless print mode denies approval-requiring tools. dontAsk plus the
        # worker allow list is the documented non-interactive mode. Danger keeps
        # its own flag and must not grow a --permission-mode.
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
        granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        assert granted == [
            "Bash", "Read", "Edit", "Write",
            "Grep", "Glob", "LS", "WebFetch", "WebSearch",
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
        prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
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
        prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
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
        prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=None, tool_config=None,
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
        prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
        tool_config={"mcp_config_path": str(explicit)},
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_explicit__*" in granted
    assert "mcp__from_cwd__*" not in granted

    missing = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
        tool_config={"mcp_config_path": str(tmp_path / "absent.json")},
    )
    missing_granted = missing.cmd[missing.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_cwd__*" not in missing_granted
    assert not any(name.startswith("mcp__") for name in missing_granted)


def test_workspace_write_rejects_invalid_mcp_config(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        ClaudeAdapter().build_invocation(
            prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
            task_id=None, session_id=None, tool_config=None,
        )

    shaped = tmp_path / "shaped"
    shaped.mkdir()
    (shaped / ".mcp.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="mcpServers"):
        ClaudeAdapter().build_invocation(
            prompt="inspect", mode="workspace-write", cwd=shaped, model=None,
            task_id=None, session_id=None, tool_config=None,
        )


def test_workspace_write_rejects_unreadable_mcp_config(tmp_path: Path) -> None:
    config = tmp_path / ".mcp.json"
    config.write_text('{"mcpServers": {}}\n', encoding="utf-8")
    config.chmod(0)
    try:
        with pytest.raises(ValueError, match="unreadable"):
            ClaudeAdapter().build_invocation(
                prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
                task_id=None, session_id=None, tool_config=None,
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
            prompt="inspect", mode="workspace-write", cwd=tmp_path, model=None,
            task_id=None, session_id=None,
            tool_config={"mcp_config_path": str(config)},
        )


def test_reviewer_tools_opt_in_installs_profile(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None, tool_config={"reviewer_tools": True},
    )
    assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
    assert set(REVIEWER_PERMISSION_PROFILE["allow"]) == set(
        plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    )
    assert set(REVIEWER_PERMISSION_PROFILE["deny"]) == set(
        plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
    )
    assert plan.env_overrides["LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK"] == "1"
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)


def test_discussion_readonly_keeps_separate_permissions(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None, tool_config={"discussion_readonly": True},
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
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
        tool_config={
            "review_isolation": True, "review_engine_binary": "/bin/true",
            "strict_mcp_config": True, "mcp_config_path": str(mcp),
            "setting_sources": "", "allowed_tools": "",
        },
    )
    assert "--settings" in plan.cmd
    assert "--safe-mode" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == ""


@pytest.mark.repo_wide
def test_tracked_hooks_work_in_fresh_clone_without_deployed_claude(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters import claude

    # Fixture clone of the tracked hook tree. Cloning this repository
    # (`git clone --shared`) exceeds the 30s bound when the host is busy (#8947).
    root = Path(__file__).resolve().parents[2]
    seed = tmp_path / "fixture"
    clone = tmp_path / "fresh"
    seed.mkdir()
    tracked_claude = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "--name-only", "HEAD", ".claude"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert tracked_claude.stdout == ""
    archived = subprocess.run(
        [
            "git", "-C", str(root), "archive", "--format=tar", "HEAD",
            "agents_extensions/shared/settings.json",
            "agents_extensions/shared/hooks",
            "scripts/agent_runtime/adapters/claude.py",
        ],
        check=True, capture_output=True, timeout=30,
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
    settings = json.loads(claude._worker_guard_settings(publish_guard=True))
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert str(clone / "agents_extensions/shared/hooks/guard-reviewer-publish.py") in commands
    assert all(Path(command).is_file() for command in commands)


def test_readonly_transport_rejects_every_push_wrapper(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True, timeout=30)
    (work / "sample.txt").write_text("sample\n", encoding="utf-8")
    for args in (["config", "user.name", "Test"], ["config", "user.email", "test@example.invalid"],
                 ["add", "sample.txt"], ["commit", "-m", "fixture"],
                 ["remote", "add", "origin", str(remote)],
                 ["config", "remote.origin.push", "HEAD:refs/heads/probe"]):
        subprocess.run(["git", "-C", str(work), *args], check=True, capture_output=True, timeout=30)

    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=work, model=None,
        task_id=None, session_id=None, tool_config={"reviewer_tools": True},
    )
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    assert subprocess.run(["git", "-C", str(work), "status", "--porcelain"], env=env, capture_output=True, timeout=30).returncode == 0
    assert subprocess.run(["git", "-C", str(work), "ls-remote", "origin"], env=env, capture_output=True, timeout=30).returncode == 0
    for command, cwd in (
        (["git", "push"], work),
        (["git", "-C", str(work), "push"], tmp_path),
        (["bash", "-c", "git push"], work),
        ([sys.executable, "-c", "import subprocess; raise SystemExit(subprocess.run(['git','push']).returncode)"], work),
    ):
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode != 0, (command, result.stdout, result.stderr)
        refs = subprocess.run(["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname)"], capture_output=True, text=True, check=True, timeout=30)
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


def test_sources_read_only_tools_match_server_contract() -> None:
    """The granted names are exactly the server's tools, each read-only and non-destructive (#9551)."""
    spec = importlib.util.spec_from_file_location("sources_server_contract", SOURCES_SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    tools = asyncio.run(server.list_tools())
    assert sorted(tool.name for tool in tools) == list(SOURCES_READ_ONLY_TOOLS)
    for tool in tools:
        assert tool.annotations.read_only_hint is True, tool.name
        assert tool.annotations.destructive_hint is False, tool.name


def test_reviewer_grants_every_sources_tool_from_worker_mcp_config(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"sources": {}, "other_tool": {}}}),
        encoding="utf-8",
    )
    cmd = _reviewer_plan(tmp_path)
    granted = _granted(cmd)
    assert granted == [*REVIEWER_PERMISSION_PROFILE["allow"], *SOURCES_RULES]
    # Only the read-only-by-contract server is granted, by exact tool name.
    assert not any(name.startswith("mcp__other_tool") for name in granted)
    assert "mcp__sources__*" not in granted
    # No write-capable tool: the reviewer deny list and guards are unchanged.
    assert not {"Edit", "Write", "NotebookEdit", "MultiEdit"} & set(granted)
    assert set(cmd[cmd.index("--disallowedTools") + 1].split(",")) == set(REVIEWER_PERMISSION_PROFILE["deny"])
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    settings = json.loads(cmd[cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)
    assert any(command.endswith("guard-primary-checkout-write.py") for command in commands)


def test_reviewer_explicit_mcp_config_path_wins_over_worker_cwd(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"sources": {}}}), encoding="utf-8")
    explicit = tmp_path / "explicit.json"
    explicit.write_text(json.dumps({"mcpServers": {"other_tool": {}}}), encoding="utf-8")
    granted = _granted(_reviewer_plan(tmp_path, mcp_config_path=str(explicit)))
    assert not any(name.startswith("mcp__") for name in granted)

    explicit.write_text(json.dumps({"mcpServers": {"sources": {}}}), encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    granted = _granted(_reviewer_plan(empty, mcp_config_path=str(explicit)))
    assert [name for name in granted if name.startswith("mcp__")] == SOURCES_RULES


def test_reviewer_missing_mcp_config_grants_no_mcp_tools(tmp_path: Path) -> None:
    for cmd in (
        _reviewer_plan(tmp_path),
        _reviewer_plan(tmp_path, mcp_config_path=str(tmp_path / "absent.json")),
    ):
        assert _granted(cmd) == list(REVIEWER_PERMISSION_PROFILE["allow"])


@pytest.mark.parametrize(
    ("content", "match"),
    [("{", "invalid JSON"), ("[]", "mcpServers"), ('{"mcpServers": {"bad,name": {}}}', "cannot be expressed")],
)
def test_reviewer_rejects_unusable_mcp_config(tmp_path: Path, content: str, match: str) -> None:
    (tmp_path / ".mcp.json").write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        _reviewer_plan(tmp_path)


def test_reviewer_rejects_unreadable_mcp_config(tmp_path: Path) -> None:
    config = tmp_path / ".mcp.json"
    config.write_text('{"mcpServers": {"sources": {}}}\n', encoding="utf-8")
    config.chmod(0)
    try:
        with pytest.raises(ValueError, match="unreadable"):
            _reviewer_plan(tmp_path)
    finally:
        config.chmod(0o644)


def test_full_review_access_keeps_review_tool_set(tmp_path: Path) -> None:
    from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")  # never read for formal attempts
    granted = _granted(_reviewer_plan(tmp_path, mcp_config_path=str(tmp_path / "attempt.json"), review_access="full"))
    assert granted == [*REVIEWER_PERMISSION_PROFILE["allow"], *review_tools_allowed_csv("claude", "full").split(",")]


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
    tmp_path: Path, allowed_tools: str, strict_mcp_config: bool,
) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
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
        prompt="write content", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
        tool_config={},
    )
    assert "--allowedTools" not in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
