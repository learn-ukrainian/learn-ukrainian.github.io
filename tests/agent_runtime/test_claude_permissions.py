"""Command and deployed-hook coverage for headless Claude workers."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import REVIEWER_PERMISSION_PROFILE, ClaudeAdapter
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
    assert (str(tracked_hooks / "guard-reviewer-publish.py") in commands) is (mode == "read-only")

    if mode == "read-only":
        assert plan.env_overrides["LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK"] == "1"
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
        assert set(REVIEWER_PERMISSION_PROFILE["allow"]) <= set(
            plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        )
        assert set(REVIEWER_PERMISSION_PROFILE["deny"]) == set(
            plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
        )
    else:
        assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
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
    assert plan.env_overrides["LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK"] == "1"


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


def test_tracked_hooks_work_in_fresh_clone_without_deployed_claude(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters import claude

    root = Path(__file__).resolve().parents[2]
    clone = tmp_path / "fresh"
    subprocess.run(["git", "clone", "--shared", "--no-checkout", str(root), str(clone)], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "-C", str(clone), "sparse-checkout", "set", "agents_extensions", "scripts"], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "-C", str(clone), "checkout", "HEAD"], check=True, capture_output=True, timeout=30)
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
        task_id=None, session_id=None, tool_config=None,
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


@pytest.mark.parametrize("allowed_tools", ["mcp__sources__*", "Read,Bash(git push *)", ""])
@pytest.mark.parametrize("strict_mcp_config", [False, True])
def test_explicit_allowed_tools_are_not_widened_or_narrowed(
    tmp_path: Path, allowed_tools: str, strict_mcp_config: bool,
) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
        task_id=None, session_id=None,
        tool_config={
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
        tool_config={"reviewer_profile": False},
    )
    assert "--allowedTools" not in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--disallowedTools" not in plan.cmd
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
