"""Tests for hardcoded ab dispatch wrapper commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers


def _option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def _capture_native_review(monkeypatch, tmp_path, content, profile, response, *, head=None):
    """Observe the file actually passed to native dispatch; never call a provider."""
    result = tmp_path / "native-result.md"
    result.write_text(response, encoding="utf-8")
    calls = []
    prompts = []

    def native_boundary(command, **kwargs):
        calls.append(command)
        if command[2] == "dispatch":
            prompt = Path(_option(command, "--prompt-file")).read_text(encoding="utf-8")
            prompts.append(prompt)
            assert _option(command, "--mode") == "read-only"
            assert "--require-review-verdict" in command
            assert kwargs["cwd"] == wrappers.REPO_ROOT
            if profile:
                assert _option(command, "--review-profile") == profile
            else:
                assert "--review-profile" not in command
            if head:
                assert _option(command, "--pinned-head") == head
            return subprocess.CompletedProcess(command, 0)
        assert command[2] == "wait"
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({"status": "done", "result_file": str(result)})
        )

    with monkeypatch.context() as patch:
        patch.setenv("LU_RUNTIME_TMP_ROOT", str(tmp_path))
        patch.setattr(wrappers.subprocess, "run", native_boundary)
        state = wrappers.run_ask_review_dispatch(
            "claude", content, task_id="native-contract", review_profile=profile, pinned_head=head
        )
    assert len(calls) == 2  # One dispatch and one wait, no corrective retry.
    assert len(prompts) == 1
    assert state["ok"] is True
    assert state["response"] == response  # No returned JSON/citation rewriting.
    return prompts[0]


@pytest.mark.parametrize(
    ("profile", "review_request", "applicable"),
    [
        ("code", "Review this branch.", True),
        ("infra", "Review this branch.", True),
        (None, "Return code-review-findings.v1 JSON.", True),
        ("code", "Return code-review-findings.v1 JSON.", True),
        ("language", "Return code-review-findings.v1 JSON.", True),
        (None, "Review code; verdict only.", False),
        ("language", "Review this meaning; verdict only.", False),
        ("curriculum", "Review this lesson; verdict only.", False),
        ("heritage", "Review this source; verdict only.", False),
        (None, "Discuss code-review-findings.v10.", False),
    ],
)
def test_native_prompt_delivers_code_contract_only_when_requested(
    monkeypatch, tmp_path, profile, review_request, applicable
):
    content = f"{review_request}\n\nKeep caller whitespace: \t  \n\n"
    prompt = _capture_native_review(monkeypatch, tmp_path, content, profile, "VERDICT: BLOCKED\n")
    if not applicable:
        assert prompt == content
        return
    assert prompt.startswith(content + "\n\n")
    guidance = prompt[len(content) :]
    # Verify instructions at the subprocess boundary rather than a constant's existence.
    assert guidance.count("## Existing code-review output") == 1
    for requirement in (
        "first completed reply",
        "plain, unfenced verdict",
        "one native JSON object",
        "schemas/code-review-findings.v1.schema.json",
        "nonblocking finding",
        "judgment and confidence",
        "repository-relative",
        "all leading",
        "tabs, trailing spaces",
        "intervening blank lines",
        "Only line endings",
        "end_line = start_line + number of quoted source lines - 1",
        'claim_type "present"',
        "actual changed new-side line",
        "body/sources",
        'claim_type "missing"',
        "real contextual",
        "never invent a line",
        "locally reread",
        "pinned head",
        "existing strict verifier",
    ):
        assert requirement in guidance


@pytest.fixture
def native_exact_target(tmp_path):
    """Committed target with whitespace-sensitive changes and an unchanged consumer."""
    from scripts.common.git_context import sanitized_git_env
    from scripts.review.target_resolution import resolve_commit_target

    repo = tmp_path / "target"
    repo.mkdir()

    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            env=sanitized_git_env(),
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "core.hooksPath", "/dev/null")
    source = repo / "service.py"
    source.write_text("def serve():\n    value = 1\n    return value\n", encoding="utf-8")
    (repo / "consumer.py").write_text("from service import serve\n", encoding="utf-8")
    git("add", "service.py", "consumer.py")
    git("commit", "-qm", "base")
    quote = "    value = 2  \n\n\treturn value"
    source.write_text(f"def serve():\n{quote}\n", encoding="utf-8")
    git("add", "service.py")
    git("commit", "-qm", "review target")
    target = resolve_commit_target(repo, "HEAD")
    # The verifier must load frozen Git content, not this subsequent working copy.
    source.write_text("different working copy\n", encoding="utf-8")
    return repo, target, quote


@pytest.mark.parametrize("profile", ["code", "infra", None])
def test_native_first_reply_exact_target_evidence_controls(monkeypatch, tmp_path, native_exact_target, profile):
    from scripts.review.evidence import changed_lines_map, verify_finding_evidence
    from scripts.review.review_contract import validate_reviewer_payload
    from scripts.review.verdict_parser import recognized_verdicts

    repo, target, quote = native_exact_target
    finding = {
        "id": "F1",
        "title": "Nonblocking consumer concern",
        "body": "consumer.py uses serve.",
        "priority": "P3",
        "confidence": 0.65,
        "category": "api",
        "location": {"path": "service.py", "start_line": 2, "end_line": 4, "claim_type": "present"},
        "verbatim": quote,
        "why_wrong": "Changed return may affect the unchanged consumer.",
        "smallest_fix": "Check consumer expectations.",
        "sources": ["consumer.py:1"],
    }
    missing = deepcopy(finding)
    missing.update(id="F2", title="Missing guard", verbatim="def serve():")
    missing["location"].update(start_line=1, end_line=1, claim_type="missing")
    payload = {
        "schema_version": "code-review-findings.v1",
        "overall": {"correctness": "correct", "explanation": "Only nonblocking concerns.", "confidence": 0.9},
        "findings": [finding, missing],
    }
    response = "VERDICT: APPROVE\n" + json.dumps(payload)
    content = "Review the exact target.\n"
    if profile is None:
        content += "Return code-review-findings.v1 JSON.\n"
    prompt = _capture_native_review(monkeypatch, tmp_path, content, profile, response, head=target.head_sha)
    assert "complete literal" in prompt
    assert recognized_verdicts(response) == ["APPROVE"]
    returned = json.loads(response.split("\n", 1)[1])
    validate_reviewer_payload(returned)
    assert returned == payload  # Findings and both confidence levels preserved.
    changed = changed_lines_map(repo, target)
    assert changed == {"service.py": {2, 3, 4}}

    def check(candidate):
        validate_reviewer_payload({**payload, "findings": [candidate]})
        return verify_finding_evidence(candidate, repo_root=repo, target=target, changed_lines=changed)

    assert check(returned["findings"][0]).outcome == "verified"
    assert check(returned["findings"][1]).outcome == "verified"
    stripped = deepcopy(finding)
    stripped["verbatim"] = "\n".join(line.strip() for line in quote.split("\n"))
    assert check(stripped).outcome == "quote_missing"
    inflated = deepcopy(finding)
    inflated["location"]["end_line"] = 5
    assert check(inflated).outcome == "line_mismatch"
    unchanged_line = deepcopy(missing)
    unchanged_line["location"]["claim_type"] = "present"
    assert check(unchanged_line).outcome == "out_of_scope"
    unchanged_consumer = deepcopy(finding)
    unchanged_consumer["location"].update(path="consumer.py", start_line=1, end_line=1)
    unchanged_consumer["verbatim"] = "from service import serve"
    assert check(unchanged_consumer).outcome == "out_of_scope"


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
    assert state["model"] == "claude-opus-5-5"
    assert state["effort"] == "xhigh"
    assert _option(command, "--agent") == "claude"
    assert _option(command, "--model") == "claude-opus-5-5"
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
    assert _option(command, "--model") == "claude-opus-5-5"
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


def _admitted_reviewer(agent: str, model: str | None = None):
    from scripts.agent_runtime.kimi_admission import REVIEW_MODE
    from scripts.agent_runtime.target_admission import resolve_and_admit

    (target,) = resolve_and_admit((agent,), mode=REVIEW_MODE, model=model, review=True)
    return target


def test_ask_kimi_review_is_refused_before_argv_or_prompt(monkeypatch):
    """Formerly ask-kimi --review selected the kimicc harness; Kimi seats now never review."""
    monkeypatch.setattr(wrappers, "_prompt_directory", lambda: pytest.fail("prompt written"))
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        wrappers.run_ask_review_dispatch("kimi", "Review PR #8703.", task_id="review-8703")
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        _admitted_reviewer("kimi")
    # The argv builder takes only an admitted target: a raw seat name never reaches it.
    with pytest.raises(TypeError, match="AdmittedTarget"):
        wrappers.build_ask_review_dispatch_command("kimi", "review-8703", Path("prompt.md"), effort=None)


def test_ask_non_kimi_review_argv_omits_kimicc_harness():
    command = wrappers.build_ask_review_dispatch_command(
        _admitted_reviewer("claude"),
        "review-1",
        Path("prompt.md"),
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


def test_run_ask_review_dispatch_without_verdict_fails_with_reason(monkeypatch, tmp_path):
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
    assert state["status"] == "failed"
    assert state["failure_reason"] == "review_missing_verdict_line"


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
    assert state["status"] == "failed"
    assert state["failure_reason"] == "review_missing_verdict_line"


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
