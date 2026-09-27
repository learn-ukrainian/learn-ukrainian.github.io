"""Command and deployed-hook coverage for headless Claude workers."""

import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import REVIEWER_PERMISSION_PROFILE, ClaudeAdapter
from scripts.guardrails.worktree_containment import resolve_main_root


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
    primary_hooks = resolve_main_root(Path(__file__)) / ".claude/hooks"
    for name in (
        "guard-primary-checkout-write.py", "guard-secret-print.py",
        "guard-pr-merge.py", "guard-branch-switch-in-main.py",
        "guard-admin-merge.py", "enforce-venv.sh", "heal-core-bare.py",
    ):
        assert str(primary_hooks / name) in commands
    assert all(Path(command).is_file() for command in commands)

    if mode == "read-only":
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
        assert set(REVIEWER_PERMISSION_PROFILE["allow"]) <= set(
            plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        )
        assert set(REVIEWER_PERMISSION_PROFILE["deny"]) == set(
            plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
        )
    else:
        assert "--permission-mode" not in plan.cmd
        assert "--disallowedTools" not in plan.cmd
    assert ("--dangerously-skip-permissions" in plan.cmd) is (mode == "danger")


def test_discussion_readonly_keeps_separate_permissions(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None, tool_config={"discussion_readonly": True},
    )
    assert "--settings" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == "Read,Grep,Glob,LS"


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
    assert "--settings" not in plan.cmd
    assert "--safe-mode" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert plan.cmd[plan.cmd.index("--tools") + 1] == ""


def test_sources_allowance_only_when_mcp_config_is_passed(tmp_path: Path) -> None:
    def plan(config: dict) -> list[str]:
        return ClaudeAdapter().build_invocation(
            prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
            task_id=None, session_id=None, tool_config=config,
        ).cmd

    ordinary = plan({})
    with_mcp = plan({"mcp_config_path": "/tmp/sources.json"})
    assert "mcp__sources__*" not in ordinary[ordinary.index("--allowedTools") + 1]
    assert "mcp__sources__*" in with_mcp[with_mcp.index("--allowedTools") + 1]
    assert with_mcp.count("--allowedTools") == 1
