"""Shell guards must receive Claude Monitor commands as well as Bash (#10339).

Local Claude tool-use records provide the Monitor input shapes below: command,
description, timeout_ms, and the older timeout/persistent string fields. Commands
are synthetic; no session text or command is copied into these fixtures.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

import pytest

from tests.test_guard_primary_checkout_write import _run as run_primary
from tests.test_guard_primary_checkout_write import repo as repo
from tests.test_guard_primary_checkout_write import repo_template as repo_template

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "agents_extensions/shared/settings.json"
HOOKS = SETTINGS.parent / "hooks"
SHELL_GUARDS = {
    "enforce-venv.sh",
    "heal-core-bare.py",
    "guard-branch-switch-in-main.py",
    "guard-admin-merge.py",
    "guard-pr-merge.py",
    "guard-secret-print.py",
    "guard-primary-checkout-write.py",
    "guard-public-github-text.py",
}


def matched_hooks(tool: str) -> list[dict]:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return [
        hook
        for entry in settings["hooks"]["PreToolUse"]
        if re.fullmatch(entry.get("matcher", ".*"), tool)
        for hook in entry["hooks"]
    ]


def assert_registered(guard: str) -> None:
    assert any(hook["command"].endswith("/" + guard) for hook in matched_hooks("Monitor"))


def load_guard(name: str):
    spec = importlib.util.spec_from_file_location("monitor_" + name.replace("-", "_"), HOOKS / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def monitor_payload(command: str, cwd: Path, legacy: bool = False) -> dict:
    tool_input = {"command": command, "description": "Synthetic shell guard probe"}
    if legacy:
        tool_input.update(timeout="10m", persistent="false")
    else:
        tool_input["timeout_ms"] = 600_000
    return {"hook_event_name": "PreToolUse", "tool_name": "Monitor", "cwd": str(cwd), "tool_input": tool_input}


def test_monitor_runs_exactly_the_bash_hook_chain():
    bash = matched_hooks("Bash")
    assert {Path(hook["command"]).name for hook in bash} == SHELL_GUARDS
    assert matched_hooks("Monitor") == bash
    # Keep the complete existing matcher denominator explicit.
    assert {Path(h["command"]).name for h in matched_hooks("Write")} == {"guard-primary-checkout-write.py"}
    for tool in ("Edit", "MultiEdit"):
        assert matched_hooks(tool) == matched_hooks("Write")
    assert len(matched_hooks("Task")) == 1
    assert "pre-task" in matched_hooks("Task")[0]["command"]


@pytest.mark.parametrize("legacy", [False, True], ids=["timeout_ms", "legacy-timeout"])
@pytest.mark.parametrize("target", ["primary", "dispatch", "read"], ids=["blocked-write", "allowed-write", "allowed-read"])
def test_monitor_primary_checkout_guard(repo: Path, legacy: bool, target: str):
    dispatch = repo / ".worktrees/dispatch/claude/task-1"
    command = {
        "primary": f"printf changed > {repo}/curriculum/tracked.md",
        "dispatch": f"printf changed > {dispatch}/curriculum/tracked.md",
        "read": "git status --short",
    }[target]
    result = run_primary(dispatch, monitor_payload(command, dispatch, legacy))
    assert result.returncode == (2 if target == "primary" else 0), result.stderr
    assert_registered("guard-primary-checkout-write.py")


@pytest.mark.parametrize("legacy", [False, True], ids=["timeout_ms", "legacy-timeout"])
@pytest.mark.parametrize("failing", [True, False], ids=["blocked-checks", "allowed-green"])
def test_monitor_admin_merge_guard(monkeypatch, legacy: bool, failing: bool):
    guard = load_guard("guard-admin-merge.py")
    seen = []
    monkeypatch.setattr(guard, "_failing_blocking_checks", lambda pr: seen.append(pr) or (["CI Gate"] if failing else []))
    payload = monitor_payload("gh pr merge 42 --admin", ROOT, legacy)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == (2 if failing else 0)
    assert seen == ["42"]
    assert_registered("guard-admin-merge.py")


@pytest.mark.parametrize("command", ["gh issue list", "git status --short"], ids=["shim-installed", "read-unchanged"])
def test_monitor_public_github_guard_preserves_input(monkeypatch, capsys, command: str):
    from scripts.opsec import prepublish

    guard = load_guard("guard-public-github-text.py")
    monkeypatch.setenv("PATH", os.defpath)
    monkeypatch.setattr(prepublish, "real_gh", lambda env: "gh")
    payload = monitor_payload(command, ROOT)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 0
    output = capsys.readouterr().out
    if command.startswith("gh "):
        updated = json.loads(output)["hookSpecificOutput"]["updatedInput"]
        assert updated["command"].startswith("export PATH=")
        assert updated["command"].endswith(command)
        assert {k: v for k, v in updated.items() if k != "command"} == {
            k: v for k, v in payload["tool_input"].items() if k != "command"
        }
    else:
        assert output == ""
    assert_registered("guard-public-github-text.py")


def test_monitor_websocket_input_does_not_become_a_shell_command(repo: Path, monkeypatch, capsys):
    payload = monitor_payload("unused", repo)
    del payload["tool_input"]["command"]
    payload["tool_input"]["ws"] = {"url": "wss://example.invalid/events"}
    assert run_primary(repo, payload).returncode == 0
    for name in ("guard-admin-merge.py", "guard-public-github-text.py"):
        guard = load_guard(name)
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        assert guard.main() == 0
        assert_registered(name)
    assert capsys.readouterr().out == ""
