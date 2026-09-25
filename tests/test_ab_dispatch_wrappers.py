"""Tests for hardcoded ab dispatch wrapper commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers


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
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
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
    assert "--force-new" in command
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
    assert "--force-new" in command
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
        if command == ["gh", "pr", "view", "1740", "--json", "title,files,url,headRefOid"]:
            payload = {
                "title": "Wrapper PR",
                "url": "https://example.com/pull/1740",
                "headRefOid": "deadbeef",
                "files": [{"path": "scripts/ai_agent_bridge/_cli.py", "additions": 10, "deletions": 2}],
            }
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload))
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
    assert "READ-ONLY REVIEW CONTRACT" in prompt
    assert "deadbeef" in prompt
    assert "scripts/ai_agent_bridge/_cli.py" in prompt
    # Pointer-only: no embedded PR body or unified diff
    assert "Review this behavior." not in prompt
    assert "diff --git" not in prompt


def test_review_deep_for_path_target_generates_prompt_and_dispatches(monkeypatch, tmp_path):
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
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
    text = str(captured_prompt["text"])
    assert wrappers.REVIEW_DEEP_INSTRUCTIONS in text
    assert "READ-ONLY REVIEW CONTRACT" in text
    assert "target.py" in text
    # Pointer-only: file *names*, not full source paste
    assert "def broken()" not in text
    assert "missing_name" not in text
    assert not Path(captured_prompt["path"]).exists()


def test_run_json_command_passes_default_timeout(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout='{"ok": true}')

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    res = wrappers._run_json_command(["echo", "hi"])
    assert res == {"ok": True}
    assert calls[0][1].get("timeout") == wrappers.DEFAULT_JSON_COMMAND_TIMEOUT_SECONDS


def test_run_json_command_timeout_raises_timeout_expired(monkeypatch):
    def timeout_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, wrappers.DEFAULT_JSON_COMMAND_TIMEOUT_SECONDS)

    monkeypatch.setattr(wrappers.subprocess, "run", timeout_run)
    import pytest

    with pytest.raises(subprocess.TimeoutExpired):
        wrappers._run_json_command(["echo", "hi"])


def test_run_text_command_passes_default_timeout(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="hello\n")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    res = wrappers._run_text_command(["echo", "hello"])
    assert res == "hello\n"
    assert calls[0][1].get("timeout") == wrappers.DEFAULT_TEXT_COMMAND_TIMEOUT_SECONDS


def test_run_text_command_timeout_raises_timeout_expired(monkeypatch):
    def timeout_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, wrappers.DEFAULT_TEXT_COMMAND_TIMEOUT_SECONDS)

    monkeypatch.setattr(wrappers.subprocess, "run", timeout_run)
    import pytest

    with pytest.raises(subprocess.TimeoutExpired):
        wrappers._run_text_command(["echo", "hi"])


def test_run_dispatch_passes_timeout(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("test", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    rc = wrappers._run_dispatch(["python", "--task-id", "123"], False, prompt_file)
    assert rc == 0
    assert calls[0][1].get("timeout") == wrappers.DISPATCH_COMMAND_TIMEOUT_SECONDS


def test_run_dispatch_timeout_returns_1(monkeypatch, tmp_path, capsys):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("test", encoding="utf-8")

    def timeout_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, wrappers.DISPATCH_COMMAND_TIMEOUT_SECONDS)

    monkeypatch.setattr(wrappers.subprocess, "run", timeout_run)
    rc = wrappers._run_dispatch(["python", "--task-id", "123"], False, prompt_file)
    assert rc == 1
    err = capsys.readouterr().err
    assert f"dispatch command timed out after {wrappers.DISPATCH_COMMAND_TIMEOUT_SECONDS}s" in err


def test_ask_kimi_review_argv_selects_kimicc_harness():
    command = wrappers.build_ask_review_dispatch_command(
        "kimi",
        "review-8703",
        Path("prompt.md"),
        model=None,
        effort=None,
    )
    assert command[command.index("--agent") + 1] == "kimi"
    assert command[command.index("--harness") + 1] == "kimicc"
    assert "--mode" in command and command[command.index("--mode") + 1] == "read-only"


def test_ask_non_kimi_review_argv_omits_kimicc_harness():
    command = wrappers.build_ask_review_dispatch_command(
        "claude",
        "review-1",
        Path("prompt.md"),
        model=None,
        effort=None,
    )
    assert "--harness" not in command
    assert command[command.index("--agent") + 1] == "claude"
    assert command[command.index("--mode") + 1] == "read-only"


def test_run_ask_review_dispatch_dispatch_timeout_raises_runtime_error(monkeypatch):
    import pytest

    def timeout_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, wrappers.DISPATCH_COMMAND_TIMEOUT_SECONDS)

    monkeypatch.setattr(wrappers.subprocess, "run", timeout_run)
    with pytest.raises(RuntimeError, match=r"delegate\.py dispatch timed out"):
        wrappers.run_ask_review_dispatch("claude", "review this", task_id="task-123")


def test_run_ask_review_dispatch_wait_timeout_raises_runtime_error(monkeypatch):
    import pytest

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            raise subprocess.TimeoutExpired(cmd, 1860)
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=r"delegate\.py wait timed out at process level"):
        wrappers.run_ask_review_dispatch("claude", "review this", task_id="task-123")


def test_run_ask_review_dispatch_passes_expected_timeouts(monkeypatch, tmp_path):
    result_file = tmp_path / "result.md"
    result_file.write_text("Reviewed the diff.\nVERDICT: APPROVED\n", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"status": "done", "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    state = wrappers.run_ask_review_dispatch(
        "claude", "review this", task_id="task-123", hard_timeout=600
    )
    assert state["ok"] is True
    assert state["status"] == "done"
    assert state["response"] == "Reviewed the diff.\nVERDICT: APPROVED\n"
    assert "--require-review-verdict" in calls[0][0]
    assert calls[0][1].get("timeout") == wrappers.DISPATCH_COMMAND_TIMEOUT_SECONDS
    assert calls[1][1].get("timeout") == 600 + wrappers.ASK_REVIEW_WAIT_GRACE_SECONDS
    assert "--branch" not in calls[0][0]


def test_run_ask_review_dispatch_attaches_author_branch(monkeypatch, tmp_path):
    result_file = tmp_path / "result.md"
    result_file.write_text("VERDICT: APPROVE\n", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"status": "done", "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    wrappers.run_ask_review_dispatch(
        "claude",
        "review this",
        task_id="review-1",
        branch="agy/impl-8419-stall-clock",
    )
    dispatch = calls[0]
    assert dispatch[dispatch.index("--branch") + 1] == "agy/impl-8419-stall-clock"


def test_run_ask_review_dispatch_without_verdict_is_no_deliverable(monkeypatch, tmp_path):
    """A verdict-less review reply must not report ok even when wait exits 0 (#8421)."""
    result_file = tmp_path / "result.md"
    result_file.write_text("I will wait for the background command to finish.\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"status": "done", "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    state = wrappers.run_ask_review_dispatch("claude", "review this", task_id="task-123")
    assert state["ok"] is False
    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "review_missing_verdict_line"


def test_run_ask_review_dispatch_with_approve_verdict_stays_done(monkeypatch, tmp_path):
    """VERDICT: APPROVE (no D) is accepted by the live review parsers (#8421)."""
    result_file = tmp_path / "result.md"
    result_file.write_text("Findings: none.\nVERDICT: APPROVE\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"status": "done", "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    state = wrappers.run_ask_review_dispatch("claude", "review this", task_id="task-123")
    assert state["ok"] is True
    assert state["status"] == "done"
    assert state.get("no_deliverable_reason") is None


def test_run_ask_review_dispatch_judges_by_verdict_not_dispatch_exit(monkeypatch, tmp_path):
    """#8786: a read-only review has no push; its verdict line is the deliverable.

    The live failure had the worker print a complete verdict and then exit
    non-zero as ``no_deliverable``. The wrapper must judge a review by the
    parsed verdict, not by the dispatch process exit code, and a reply with no
    verdict must still fail loudly (covered by the sibling test above).
    """
    result_file = tmp_path / "result.md"
    result_file.write_text(
        "Adversarial review complete.\n\n**Verdict**: **APPROVE**\n", encoding="utf-8"
    )

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                1,
                stdout=json.dumps({"status": "no_deliverable", "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    state = wrappers.run_ask_review_dispatch("deepseek", "review this", task_id="review-8786")
    assert state["ok"] is True
    assert state["status"] == "done"
    assert state.get("no_deliverable_reason") is None


def _run_review_with_wait_state(monkeypatch, tmp_path, *, status, wait_rc, response):
    result_file = tmp_path / "result.md"
    result_file.write_text(response, encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            return subprocess.CompletedProcess(cmd, 0)
        if "wait" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                wait_rc,
                stdout=json.dumps({"status": status, "result_file": str(result_file)}),
            )
        raise AssertionError(f"unexpected cmd: {cmd}")

    monkeypatch.setattr(wrappers.subprocess, "run", fake_run)
    return wrappers.run_ask_review_dispatch("deepseek", "review this", task_id="review-8786")


@pytest.mark.parametrize(
    "status", ["timeout", "failed", "crashed", "rate_limited", "cancelled"]
)
def test_run_ask_review_dispatch_never_promotes_failed_terminal_status(
    monkeypatch, tmp_path, status
):
    """#8786 review: a verdict beside a non-completed run is not a success.

    ``delegate wait`` reported ``timeout`` (or another terminal failure) while
    the partial result file already carried ``VERDICT: APPROVE``; the wrapper
    used to rewrite that to ``done`` / ``ok: true`` / exit 0.
    """
    state = _run_review_with_wait_state(
        monkeypatch,
        tmp_path,
        status=status,
        wait_rc=1,
        response="Partial review.\nVERDICT: APPROVE\n",
    )
    assert state["ok"] is False
    assert state["status"] == status
    assert state["stderr_excerpt"]


def test_run_ask_review_dispatch_ignores_quoted_verdict_example(monkeypatch, tmp_path):
    """#8786 review: a quoted example of the format is not a verdict."""
    state = _run_review_with_wait_state(
        monkeypatch,
        tmp_path,
        status="done",
        wait_rc=0,
        response="I will report `VERDICT: APPROVE` later.\n```\nVERDICT: APPROVE\n```\n",
    )
    assert state["ok"] is False
    assert state["status"] == "no_deliverable"
    assert state["no_deliverable_reason"] == "review_missing_verdict_line"


def test_run_ask_review_dispatch_last_verdict_line_wins(monkeypatch, tmp_path):
    state = _run_review_with_wait_state(
        monkeypatch,
        tmp_path,
        status="no_deliverable",
        wait_rc=1,
        response="VERDICT: APPROVE\n\n**VERDICT: REQUEST_CHANGES**\n",
    )
    assert state["ok"] is True
    assert state["status"] == "done"
