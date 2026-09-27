"""Opt-in Grok reviewer shell and hook boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.agent_runtime.env_sanitize import build_agent_env

ROOT = Path(__file__).resolve().parents[2]


def _plan(tmp_path: Path, config: dict | None):
    with patch("scripts.agent_runtime.adapters.grok_build.shutil.which", return_value="/usr/bin/grok"):
        return GrokBuildAdapter().build_invocation(
            prompt="inspect", mode="read-only", cwd=tmp_path, model=None,
            task_id=None, session_id=None, tool_config=config, effort="low",
        )


def test_reviewer_opt_in_adds_bash_and_all_tracked_guards(tmp_path: Path) -> None:
    adapter = GrokBuildAdapter()
    baseline = _plan(tmp_path, None)
    reviewer = _plan(tmp_path, {"reviewer_tools": True})
    try:
        agent_path = Path(reviewer.cmd[reviewer.cmd.index("--agent") + 1])
        definition = agent_path.read_text(encoding="utf-8")
        assert definition.count("type: command") == 9
        for name in (
            "enforce-venv.sh", "heal-core-bare.py", "guard-branch-switch-in-main.py",
            "guard-admin-merge.py", "guard-pr-merge.py", "guard-secret-print.py",
            "guard-primary-checkout-write.py", "guard-reviewer-publish.py",
        ):
            assert str(ROOT / "agents_extensions/shared/hooks" / name) in definition
        assert str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py") in definition
        # The only argv changes are the per-invocation agent and Bash deny removal.
        normalized = reviewer.cmd[3:]
        baseline_without_bash = baseline.cmd.copy()
        bash_index = baseline_without_bash.index("Bash")
        del baseline_without_bash[bash_index - 1 : bash_index + 1]
        assert normalized == baseline_without_bash[1:]
        assert reviewer.env_overrides == {"LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK": "1"}
        env = build_agent_env(provider="grok", overrides=reviewer.env_overrides)
        assert any(value == "url.file:///dev/null/claude-read-only/.pushInsteadOf" for key, value in env.items() if key.startswith("GIT_CONFIG_KEY_"))
    finally:
        adapter.cleanup_invocation(reviewer)
    assert not agent_path.exists()


@pytest.mark.parametrize(
    "config",
    [
        {"reviewer_tools": True, "allowed_tools": "Read"},
        {"reviewer_tools": True, "strict_mcp_config": True},
        {"reviewer_tools": True, "mcp_server_names": ["sources"]},
        {"reviewer_tools": False},
    ],
)
def test_nonordinary_callers_keep_baseline_argv(tmp_path: Path, config: dict) -> None:
    baseline_config = {key: value for key, value in config.items() if key != "reviewer_tools"}
    assert _plan(tmp_path, config).cmd == _plan(tmp_path, baseline_config).cmd


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("gh pr view 8912 --json number", False),
        ("git push --dry-run", True),
        ("gh pr comment 8912 --body test", True),
    ],
)
def test_grok_hook_bridge_runs_publish_guard(command: str, blocked: bool) -> None:
    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": command},
        "cwd": str(ROOT),
    }
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
         str(ROOT / "agents_extensions/shared/hooks/guard-reviewer-publish.py")],
        input=json.dumps(event), capture_output=True, text=True, timeout=30,
    )
    assert (result.returncode == 2) is blocked, (command, result.stderr)


def test_grok_hook_bridge_denies_unreadable_event() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
         str(ROOT / "agents_extensions/shared/hooks/guard-reviewer-publish.py")],
        input="{}", capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2


def test_grok_hook_bridge_runs_fleet_venv_guard() -> None:
    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": "python3 --version"},
        "cwd": str(ROOT),
    }
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
         str(ROOT / "agents_extensions/shared/hooks/enforce-venv.sh")],
        input=json.dumps(event), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert "Unqualified interpreter blocked" in result.stderr
