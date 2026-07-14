"""Tests for hardcoded ab dispatch wrapper commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _dispatch_wrappers as wrappers


def _option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def _patch_state_dir(monkeypatch, tmp_path: Path) -> Path:
    state_dir = tmp_path / "states"
    state_dir.mkdir()

    def state_path(task_id: str) -> Path:
        return state_dir / f"{task_id}.json"

    monkeypatch.setattr(wrappers, "_task_state_path", state_path)
    return state_dir


def test_dispatch_fix_with_explicit_brief_file_appends_checklist_and_dispatches(monkeypatch, tmp_path):
    brief = tmp_path / "brief.md"
    brief.write_text("# Fix this\n\nExisting acceptance criteria.\n", encoding="utf-8")
    calls = []
    captured_prompt: dict[str, str | Path] = {}

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        prompt_path = Path(_option(command, "--prompt-file"))
        captured_prompt["path"] = prompt_path
        captured_prompt["text"] = prompt_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)

    rc = wrappers.handle_dispatch_fix(
        argparse.Namespace(task_id="1741", brief_file=str(brief), dry_run=False)
    )

    assert rc == 0
    command = calls[0][0]
    assert command[:3] == [".venv/bin/python", "scripts/delegate.py", "dispatch"]
    assert _option(command, "--agent") == "codex"
    assert _option(command, "--mode") == "danger"
    assert "--worktree" in command
    assert _option(command, "--base") == "origin/main"
    assert _option(command, "--task-id") == "1741"
    assert _option(command, "--effort") == "high"
    assert "Existing acceptance criteria." in str(captured_prompt["text"])
    assert wrappers.MANDATORY_COMMIT_PUSH_PR_CHECKLIST in str(captured_prompt["text"])
    assert not Path(captured_prompt["path"]).exists()


def test_dispatch_fix_with_auto_brief_uses_issue_body_and_dry_run_state(monkeypatch, tmp_path):
    state_dir = _patch_state_dir(monkeypatch, tmp_path)
    lease_root = tmp_path / "learn-ukrainian" / "task-1701"
    lease_root.mkdir(parents=True)
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(lease_root))

    def fake_run(command, **kwargs):
        assert command == ["gh", "issue", "view", "1701", "--json", "title,body"]
        payload = {"title": "Security issue", "body": "Acceptance criteria from issue."}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload))

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)

    rc = wrappers.handle_dispatch_fix(
        argparse.Namespace(task_id="1701", brief_file=None, dry_run=True)
    )

    assert rc == 0
    state = json.loads((state_dir / "1701.json").read_text(encoding="utf-8"))
    command = state["command"]
    assert state["status"] == "dry-run"
    assert state["agent"] == "codex"
    assert state["mode"] == "danger"
    assert state["model"] is None
    assert state["effort"] == "high"
    assert _option(command, "--task-id") == "1701"
    prompt_path = Path(state["prompt_file"])
    assert prompt_path.parent == lease_root
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "Security issue" in prompt
    assert "Acceptance criteria from issue." in prompt
    assert wrappers.MANDATORY_COMMIT_PUSH_PR_CHECKLIST in prompt


def test_review_deep_for_pr_target_generates_prompt_and_dry_run_state(monkeypatch, tmp_path):
    state_dir = _patch_state_dir(monkeypatch, tmp_path)
    lease_root = tmp_path / "learn-ukrainian" / "task-review"
    lease_root.mkdir(parents=True)
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(lease_root))

    def fake_run(command, **kwargs):
        if command == ["gh", "pr", "view", "1740", "--json", "title,body,files"]:
            payload = {
                "title": "Wrapper PR",
                "body": "Review this behavior.",
                "files": [{"path": "scripts/ai_agent_bridge/_cli.py", "additions": 10, "deletions": 2}],
            }
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload))
        if command == ["gh", "pr", "diff", "1740"]:
            return subprocess.CompletedProcess(command, 0, stdout="diff --git a/file b/file\n+change\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)

    rc = wrappers.handle_review_deep(
        argparse.Namespace(target="1740", effort="xhigh", dry_run=True)
    )

    assert rc == 0
    state_path = next(state_dir.glob("review-1740-*.json"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    command = state["command"]
    assert state["agent"] == "claude"
    assert state["mode"] == "read-only"
    assert state["model"] == "claude-opus-4-8"
    assert state["effort"] == "xhigh"
    assert _option(command, "--agent") == "claude"
    assert _option(command, "--model") == "claude-opus-4-8"
    assert _option(command, "--effort") == "xhigh"
    assert _option(command, "--task-id").startswith("review-1740-")
    prompt_path = Path(state["prompt_file"])
    assert prompt_path.parent == lease_root
    prompt = prompt_path.read_text(encoding="utf-8")
    assert wrappers.REVIEW_DEEP_INSTRUCTIONS in prompt
    assert "Review this behavior." in prompt
    assert "diff --git" in prompt


def test_review_deep_for_path_target_generates_prompt_and_dispatches(monkeypatch, tmp_path):
    target = tmp_path / "target.py"
    target.write_text("def broken():\n    return missing_name\n", encoding="utf-8")
    calls = []
    captured_prompt: dict[str, str | Path] = {}

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        prompt_path = Path(_option(command, "--prompt-file"))
        captured_prompt["path"] = prompt_path
        captured_prompt["text"] = prompt_path.read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)

    rc = wrappers.handle_review_deep(
        argparse.Namespace(target=str(target), effort="high", dry_run=False)
    )

    assert rc == 0
    command = calls[0][0]
    assert _option(command, "--agent") == "claude"
    assert _option(command, "--mode") == "read-only"
    assert _option(command, "--model") == "claude-opus-4-8"
    assert _option(command, "--effort") == "high"
    assert _option(command, "--task-id").startswith("review-")
    assert wrappers.REVIEW_DEEP_INSTRUCTIONS in str(captured_prompt["text"])
    assert "def broken()" in str(captured_prompt["text"])
    assert not Path(captured_prompt["path"]).exists()
