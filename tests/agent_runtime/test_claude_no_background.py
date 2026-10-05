"""Headless Claude workers cannot end a run with background work pending (#9690).

A print-mode run exits when its final turn ends, so background work it started
is killed or never reported. The adapter disables background execution with
``CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`` and a settings deny for the tools
that variable leaves available. These tests launch a fake ``claude`` through
the real runner, so the switch must survive ``env_sanitize.build_agent_env``.
The fake reproduces the gating observed live in Claude Code 2.1.289: with the
variable, Bash refuses ``run_in_background`` and a background subagent runs in
the foreground; Monitor, ScheduleWakeup, CronCreate and Workflow are refused
only when denied.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime import runner
from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.adapters.claude import (
    HEADLESS_BACKGROUND_ENV,
    HEADLESS_BACKGROUND_TOOL_DENIES,
    ClaudeAdapter,
)
from scripts.agent_runtime.env_sanitize import build_agent_env

SWITCH = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
REPO_ROOT = Path(__file__).resolve().parents[2]

_FAKE_CLAUDE = textwrap.dedent(
    """
    import json, os, sys

    argv = sys.argv[1:]
    if "--version" in argv:
        print("2.1.289 (Claude Code)")
        sys.exit(0)
    settings = json.loads(argv[argv.index("--settings") + 1]) if "--settings" in argv else {}
    denied = set(settings.get("permissions", {}).get("deny", []))
    with open(os.environ["LU_FAKE_CLAUDE_DUMP"], "w", encoding="utf-8") as handle:
        json.dump({"argv": argv, "env": dict(os.environ)}, handle)

    # The scripted worker tries every background path, as review-9484-c did.
    switch = os.environ.get("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS") == "1"
    pending = []
    if not switch:
        pending += ["Bash run_in_background", "Agent run_in_background"]
    pending += [tool for tool in ("Monitor", "ScheduleWakeup", "CronCreate", "Workflow") if tool not in denied]
    if pending:
        text = "Started in the background: " + ", ".join(pending) + ". The final report will follow when it completes."
    else:
        text = "FINAL REPORT: every command ran in the foreground. VERDICT: APPROVE"
    session = "00000000-0000-4000-8000-000000009690"
    print(json.dumps({"type": "system", "subtype": "init", "session_id": session}))
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": text, "session_id": session}))
    """
)


@pytest.fixture
def fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    script = tmp_path / "fake_claude.py"
    script.write_text(_FAKE_CLAUDE, encoding="utf-8")
    binary = tmp_path / "claude"
    binary.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    binary.chmod(0o755)
    dump = tmp_path / "dump.json"
    monkeypatch.setenv("LU_FAKE_CLAUDE_DUMP", str(dump))
    # An ambient value must not be what makes the test pass.
    monkeypatch.delenv(SWITCH, raising=False)
    return binary, dump


def _invoke(binary: Path, cwd: Path, mode: str) -> runner.Result:
    with (
        patch.object(runner, "has_headroom", return_value=(True, "")),
        patch.object(runner, "write_record"),
    ):
        return runner.invoke(
            "claude",
            "review the branch",
            mode=mode,
            cwd=cwd,
            tool_config={"cmd_prefix": [str(binary)]},
            hard_timeout=60,
        )


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_runner_launch_carries_switch_and_worker_reports_in_full(fake_claude, tmp_path: Path, mode: str) -> None:
    """AC-01: through the real runner and sanitizer, background work is refused."""
    binary, dump = fake_claude
    workdir = tmp_path / "work"
    workdir.mkdir()

    result = _invoke(binary, workdir, mode)

    seen = json.loads(dump.read_text(encoding="utf-8"))
    assert seen["env"][SWITCH] == "1"
    argv = seen["argv"]
    assert argv[0] == "-p"
    deny = json.loads(argv[argv.index("--settings") + 1])["permissions"]["deny"]
    assert set(HEADLESS_BACKGROUND_TOOL_DENIES) <= set(deny)
    assert result.ok is True
    assert result.response == "FINAL REPORT: every command ran in the foreground. VERDICT: APPROVE"
    assert SWITCH not in os.environ


def test_fake_cli_reproduces_the_lost_report_without_the_switch(
    fake_claude, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control: without the adapter's switch the worker ends with work pending."""
    binary, dump = fake_claude
    monkeypatch.setattr(claude, "HEADLESS_BACKGROUND_ENV", {})
    monkeypatch.setattr(claude, "HEADLESS_BACKGROUND_TOOL_DENIES", ())

    result = _invoke(binary, tmp_path, "workspace-write")

    assert SWITCH not in json.loads(dump.read_text(encoding="utf-8"))["env"]
    assert result.response.startswith("Started in the background: Bash run_in_background")
    assert "final report will follow" in result.response


def test_sanitizer_keeps_switch_for_claude_only() -> None:
    """The allowlist entry is scoped to the Claude provider."""
    assert build_agent_env(provider="claude", overrides=HEADLESS_BACKGROUND_ENV)[SWITCH] == "1"
    assert build_agent_env(provider="claude-tools", overrides=HEADLESS_BACKGROUND_ENV)[SWITCH] == "1"
    assert SWITCH not in build_agent_env(provider="codex", overrides=HEADLESS_BACKGROUND_ENV)


@pytest.mark.parametrize(
    "tool_config",
    [
        None,
        {"reviewer_tools": True},
        {"allowed_tools": "Bash,Monitor"},
        {"agent": "reviewer"},
        {"max_budget_usd": 1},
    ],
    ids=["plain", "reviewer", "explicit-allow", "agent", "budget"],
)
@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_every_headless_plan_disables_background(tmp_path: Path, mode: str, tool_config) -> None:
    """Every adapter plan is headless (-p) and carries both halves of the switch."""
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={**(tool_config or {}), "cmd_prefix": ["claude"]},
    )
    assert plan.cmd[1] == "-p"
    assert plan.env_overrides[SWITCH] == "1"
    assert plan.cmd.count("--settings") == 1
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    assert settings["permissions"]["deny"] == ["Monitor", "ScheduleWakeup", "CronCreate", "Workflow"]
    # The guard hooks are unchanged by the added deny.
    publish_guard = mode == "read-only" and tool_config == {"reviewer_tools": True}
    assert settings["hooks"] == json.loads(claude._worker_guard_settings(publish_guard=publish_guard))["hooks"]


@pytest.mark.parametrize("launcher", ["start-claude.sh", "start-claude-driver.sh", "scripts/launchers/claude.sh"])
def test_interactive_launchers_do_not_disable_background(launcher: str) -> None:
    """Interactive sessions are outside the adapter and keep background tasks."""
    text = (REPO_ROOT / launcher).read_text(encoding="utf-8")
    assert SWITCH not in text
    assert not any(tool in text for tool in ("permissions.deny", "--disallowedTools Monitor"))
    assert "agent_runtime" not in text
