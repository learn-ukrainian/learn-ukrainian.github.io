"""Headless Claude workers cannot end a run with background work pending (#9690).

A print-mode run exits when its final turn ends, so background work it started
is killed or never reported. The adapter disables background execution with
``CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`` and a settings deny for the tools
that variable leaves available. These tests launch a fake ``claude`` through
the real runner, so the switch must survive ``env_sanitize.build_agent_env``.
The KimiCC harness also runs headless Claude Code (through
``kimicc_headless.sh``) and gets both controls; the native Kimi CLI is not
Claude Code and gets neither.
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
from scripts.agent_runtime.adapters import claude, kimi, kimicc
from scripts.agent_runtime.adapters.claude import (
    HEADLESS_BACKGROUND_ENV,
    HEADLESS_BACKGROUND_TOOL_DENIES,
    ClaudeAdapter,
)
from scripts.agent_runtime.adapters.kimi import KimiAdapter
from scripts.agent_runtime.adapters.kimicc import KimiccHarness
from scripts.agent_runtime.env_sanitize import build_agent_env
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config

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
    if "--disallowedTools" in argv:
        denied |= set(argv[argv.index("--disallowedTools") + 1].split(","))
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


_FAKE_KIMI = textwrap.dedent(
    """
    import json, os, sys

    with open(os.environ["LU_FAKE_CLAUDE_DUMP"], "w", encoding="utf-8") as handle:
        json.dump({"argv": sys.argv[1:], "env": dict(os.environ)}, handle)
    print(json.dumps({"role": "assistant", "content": "native kimi done"}))
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


def test_sanitizer_keeps_switch_for_claude_and_adapter_supplied_kimi_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Claude keeps the switch; kimi keeps it only from adapter overrides (the KimiCC plan)."""
    monkeypatch.delenv(SWITCH, raising=False)
    assert build_agent_env(provider="claude", overrides=HEADLESS_BACKGROUND_ENV)[SWITCH] == "1"
    assert build_agent_env(provider="claude-tools", overrides=HEADLESS_BACKGROUND_ENV)[SWITCH] == "1"
    assert build_agent_env(provider="kimi", overrides=HEADLESS_BACKGROUND_ENV)[SWITCH] == "1"
    assert SWITCH not in build_agent_env(provider="codex", overrides=HEADLESS_BACKGROUND_ENV)
    # An ambient export (a dispatch started from a headless Claude worker's
    # shell) never reaches a kimi launch whose plan did not set it.
    monkeypatch.setenv(SWITCH, "1")
    assert SWITCH not in build_agent_env(provider="kimi", overrides={})
    assert SWITCH not in build_agent_env(provider="kimi-tools", overrides={"KIMI_CODE_BIN": "kimi"})


def _admitted_worktree(tmp_path: Path) -> Path:
    worktree = tmp_path / "work"
    worktree.mkdir()
    admitted_tool_config(worktree)
    return worktree


def _invoke_kimi(cwd: Path, tool_config: dict) -> runner.Result:
    with (
        patch.object(runner, "has_headroom", return_value=(True, "")),
        patch.object(runner, "write_record"),
    ):
        return runner.invoke(
            "kimi",
            "add a tooltip to the widget",
            mode="workspace-write",
            cwd=cwd,
            tool_config=admitted_tool_config(cwd, tool_config),
            hard_timeout=60,
        )


def test_kimicc_runner_launch_carries_switch_and_denies(
    fake_claude, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-01 on KimiCC: the real runner, sanitizer and kimicc_headless.sh hand claude -p both controls."""
    binary, dump = fake_claude
    monkeypatch.setattr(kimicc, "_default_claude_bin", lambda: str(binary))
    monkeypatch.setenv("KIMICC_AUTH_TOKEN", "test-route-token")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    worktree = _admitted_worktree(tmp_path)

    result = _invoke_kimi(worktree, {"harness": "kimicc"})

    seen = json.loads(dump.read_text(encoding="utf-8"))
    assert seen["env"][SWITCH] == "1"
    assert seen["env"]["LEARN_UKRAINIAN_TRANSPORT"] == "kimicc"
    argv = seen["argv"]
    assert argv[:2] == ["-p", "--bare"]
    assert argv[argv.index("--disallowedTools") + 1].split(",") == list(HEADLESS_BACKGROUND_TOOL_DENIES)
    assert result.ok is True
    assert result.response == "FINAL REPORT: every command ran in the foreground. VERDICT: APPROVE"
    assert SWITCH not in os.environ


def test_native_kimi_runner_launch_gets_neither_control(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The native Kimi CLI is not Claude Code: no switch (even when exported ambiently) and no denies."""
    script = tmp_path / "fake_kimi.py"
    script.write_text(_FAKE_KIMI, encoding="utf-8")
    binary = tmp_path / "kimi"
    binary.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
    binary.chmod(0o755)
    dump = tmp_path / "dump.json"
    monkeypatch.setenv("LU_FAKE_CLAUDE_DUMP", str(dump))
    monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
    monkeypatch.setenv(SWITCH, "1")
    worktree = _admitted_worktree(tmp_path)

    result = _invoke_kimi(worktree, {"harness": "native"})

    seen = json.loads(dump.read_text(encoding="utf-8"))
    assert seen["argv"][0] == "-p"
    assert SWITCH not in seen["env"]
    assert not {"--disallowedTools", "--settings"} & set(seen["argv"])
    assert not any(tool in arg for arg in seen["argv"] for tool in HEADLESS_BACKGROUND_TOOL_DENIES)
    assert result.ok is True
    assert result.response == "native kimi done"


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


def _claude_plan(tmp_path: Path, mode: str) -> tuple[list[str], dict[str, str]]:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": ["claude"]},
    )
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    return settings["permissions"]["deny"], plan.env_overrides


def _kimicc_plan(tmp_path: Path, mode: str, monkeypatch: pytest.MonkeyPatch) -> tuple[list[str], dict[str, str]]:
    monkeypatch.setattr(kimicc, "_default_claude_bin", lambda: "/usr/bin/claude")
    monkeypatch.setattr(kimicc, "_ensure_supported_claude_cli_version", lambda _: None)
    plan = KimiccHarness().build_invocation(
        prompt="add a tooltip",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=admitted_tool_config(tmp_path, {"harness": "kimicc"}),
    )
    return plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(","), plan.env_overrides


# Every delegate harness that launches Claude Code, with the modes it admits.
# test_claude_code_harness_denominator_is_complete keeps this table honest.
_CLAUDE_CODE_HARNESSES = {
    "adapters/claude.py": (_claude_plan, ("read-only", "workspace-write", "danger")),
    "adapters/kimicc.py": (_kimicc_plan, ("workspace-write",)),
}


@pytest.mark.parametrize(
    ("harness", "mode"),
    [(harness, mode) for harness, (_, modes) in _CLAUDE_CODE_HARNESSES.items() for mode in modes],
)
def test_every_claude_code_harness_plan_disables_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, harness: str, mode: str
) -> None:
    """Each harness that launches Claude Code carries the switch and denies every background tool."""
    build, _ = _CLAUDE_CODE_HARNESSES[harness]
    args = (monkeypatch,) if build is _kimicc_plan else ()
    denied, env_overrides = build(tmp_path, mode, *args)
    assert env_overrides[SWITCH] == "1"
    assert denied == list(HEADLESS_BACKGROUND_TOOL_DENIES)


@pytest.mark.repo_wide
def test_claude_code_harness_denominator_is_complete() -> None:
    """Every runtime adapter that resolves the Claude binary is in the table above."""
    adapters = REPO_ROOT / "scripts" / "agent_runtime" / "adapters"
    launching = {
        f"adapters/{path.name}"
        for path in adapters.glob("*.py")
        if any(marker in path.read_text(encoding="utf-8") for marker in ("_default_claude_bin(", 'which("claude")'))
    }
    assert launching == set(_CLAUDE_CODE_HARNESSES)


def test_native_kimi_plan_has_neither_control(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The native Kimi CLI plan carries no Claude switch and no Claude denies."""
    monkeypatch.setattr(kimi, "_resolve_kimi_binary", lambda: "/usr/bin/kimi")
    for harness in (None, "native"):
        plan = KimiAdapter().build_invocation(
            prompt="add a tooltip",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=admitted_tool_config(tmp_path, {"harness": harness} if harness else None),
        )
        assert SWITCH not in plan.env_overrides
        assert not {"--disallowedTools", "--settings"} & set(plan.cmd)


@pytest.mark.parametrize("launcher", ["start-claude.sh", "start-claude-driver.sh", "scripts/launchers/claude.sh"])
def test_interactive_launchers_do_not_disable_background(launcher: str) -> None:
    """Interactive sessions are outside the adapter and keep background tasks."""
    text = (REPO_ROOT / launcher).read_text(encoding="utf-8")
    assert SWITCH not in text
    assert not any(tool in text for tool in ("permissions.deny", "--disallowedTools Monitor"))
    assert "agent_runtime" not in text
