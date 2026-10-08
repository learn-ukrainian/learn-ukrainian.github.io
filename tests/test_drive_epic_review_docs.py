"""Offline walkthrough for detached formal review (#9663).

Actual dispatch stdout and task-record producer evidence is covered by
tests/test_delegate.py::test_dispatch_generates_and_persists_run_nonce.
"""

from __future__ import annotations

import io
import json
import re
import shlex
from pathlib import Path

import pytest

from scripts import delegate
from scripts.ai_agent_bridge import _cli
from scripts.review import record_cf_verdict as recorder

REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "agents_extensions/shared/skills/drive-epic/references/review-merge-cleanup.md"
)
HEAD = "a" * 40
NONCE = "run-nonce-fixture"


def _canonical_review_asks():
    """Extract executable ask recipes across the original shared instruction scope."""
    shared = REFERENCE.parents[3]
    recipes = []
    for root in (shared / "skills", shared / "rules"):
        for path in sorted(root.rglob("*.md")):
            body = path.read_text(encoding="utf-8")
            for block in re.findall(r"^```[^\n]*\n(.*?)^```", body, re.M | re.S):
                for line in block.replace("\\\n", " ").splitlines():
                    if "scripts/ai_agent_bridge/__main__.py ask-" not in line:
                        continue
                    command = line.split("scripts/ai_agent_bridge/__main__.py ", 1)[1]
                    argv = shlex.split(command.replace("ask-<lane>", "ask-claude"))
                    if "--review" in argv or ("--type" in argv and argv[argv.index("--type") + 1] == "review"):
                        recipes.append(pytest.param(argv, id=str(path.relative_to(shared))))
    assert recipes, "canonical formal-review launch inventory must not be empty"
    return recipes


@pytest.mark.parametrize("argv", _canonical_review_asks())
def test_canonical_review_ask_recipes_forward_pushed_branch_target(argv, monkeypatch):
    """Run the documented argv through the real parser and handler, without inference."""
    args = _cli._build_parser().parse_args(argv)
    assert args.branch, "pre-PR formal review must target the pushed author branch"
    assert args.pr is None
    monkeypatch.setattr(_cli, "require_core_or_exit", lambda _name: None)
    monkeypatch.setattr(_cli.sys, "stdin", io.StringIO("Review the pushed branch."))
    dispatched = []
    monkeypatch.setattr(_cli, "_dispatch_headless_review", lambda *a, **kw: dispatched.append(kw))
    _cli._handle_acp_compat(args, "claude")
    assert len(dispatched) == 1
    assert dispatched[0]["branch"] == args.branch
    assert dispatched[0]["pr_number"] is None


def test_detached_exact_head_review_launch_settle_and_publication_guards(monkeypatch, tmp_path, capsys):
    """Retired ask background fails; native dispatch settles by nonce and rejects bad evidence."""
    # Reproduce the formerly documented command through the real ask parser and
    # handler. Refusal occurs before any provider, task, or GitHub boundary.
    ask = _cli._build_parser().parse_args(
        ["ask-codex", "-", "--task-id", "review-fixture", "--background"]
    )
    monkeypatch.setattr(_cli, "require_core_or_exit", lambda _name: None)
    with pytest.raises(SystemExit, match="legacy ask --background is retired"):
        _cli._handle_acp_compat(ask, "codex")
    branch_ask = _cli._build_parser().parse_args(
        [
            "ask-codex",
            "Review the pushed author branch at its resolved remote head.",
            "--task-id", "review-fixture",
            "--review",
            "--branch", "codex/author",
        ]
    )
    assert branch_ask.branch == "codex/author"
    assert branch_ask.review

    reference = REFERENCE.read_text(encoding="utf-8")
    assert "`--background` flag is rejected" in reference
    assert "scripts/delegate.py dispatch" in reference
    assert "--pinned-head \"$HEAD_SHA\"" in reference
    assert "--run-nonce \"$REVIEW_NONCE\"" in reference
    assert "scripts/review/record_cf_verdict.py" in reference
    assert "requires_silence_timeout" in reference
    assert "Only terminal task-record" in reference
    shared_rules = REFERENCE.parents[3] / "rules"
    fleet_rules = (shared_rules / "fleet-comms-coordination.md").read_text(encoding="utf-8")
    model_rules = (shared_rules / "model-assignment.md").read_text(encoding="utf-8")
    workflow_rules = (shared_rules / "workflow.md").read_text(encoding="utf-8")
    for rules in (fleet_rules, model_rules):
        assert "--review --branch <branch>" in rules
        assert "record_cf_verdict.py" in rules
        assert "ask --pinned-head" not in rules
    assert "compare the actual reviewed SHA" in workflow_rules

    # Parse the documented producer with delegate's real CLI. Its public
    # contract is detached dispatch; this fixture replaces only the worker
    # launch/provider boundary and returns its task ID plus nonce immediately.
    launch = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent", "claude",
            "--model", "claude-opus-5-5",
            "--effort", "high",
            "--mode", "read-only",
            "--worktree",
            "--task-id", "review-fixture",
            "--prompt-file", str(tmp_path / "review.md"),
            "--branch", "codex/author",
            "--pinned-head", HEAD,
            "--require-review-verdict",
            "--review-profile", "code",
            "--review-author-model", "gpt-6.1-sol",
            "--review-risk", "medium",
        ]
    )
    assert launch.func is delegate.cmd_dispatch
    assert launch.agent == "claude"
    assert launch.mode == "read-only"
    assert launch.worktree == "auto"
    assert launch.branch == "codex/author"
    assert launch.pinned_head == HEAD
    assert launch.require_review_verdict
    assert launch.review_profile == "code"
    assert launch.review_author_model == "gpt-6.1-sol"
    assert launch.review_risk == "medium"

    task_root = tmp_path / "tasks"
    task_root.mkdir()
    task_path = task_root / "review-fixture.json"
    task = {
        "task_id": "review-fixture",
        "run_nonce": NONCE,
        "status": "running",
        "agent": "claude",
        "model": "claude-opus-5-5",
        "worktree_branch": "codex/author",
        "worktree_base_sha": HEAD,
        "repository": "owner/repo",
        "started_at": "2026-10-08T00:00:00+00:00",
    }
    task_path.write_text(json.dumps(task), encoding="utf-8")
    (task_root / "review-fixture.result").write_text("VERDICT: APPROVE\n", encoding="utf-8")
    # The existing producer regression runs cmd_dispatch --dry-run and checks
    # its actual two-line task-id/run-nonce stdout against the persisted record.
    review_task, review_nonce = "review-fixture", NONCE
    assert json.loads(task_path.read_text(encoding="utf-8"))["status"] == "running"

    # A client wait deadline can expire while task state remains running. Its
    # 124 result is not settlement; re-arm the same parsed wait/nonce.
    wait = delegate.build_parser().parse_args(
        ["wait", review_task, "--run-nonce", review_nonce, "--timeout", "1"]
    )
    assert wait.run_nonce == NONCE
    assert wait.func is delegate.cmd_wait

    def read_task(_task_id):
        return task_path, json.loads(task_path.read_text(encoding="utf-8"))

    clock = [0.0]
    monkeypatch.setattr(delegate.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(delegate, "_read_state_or_archived", read_task)
    monkeypatch.setattr(delegate, "_heal_dead_task", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: clock.__setitem__(0, 2.0))
    assert delegate.cmd_wait(wait) == 124
    expired = json.loads(capsys.readouterr().err)
    assert expired["last_known_status"] == "running"
    assert json.loads(task_path.read_text(encoding="utf-8"))["run_nonce"] == review_nonce

    # Re-arm the same task/run nonce; the worker fixture now reaches terminal
    # done, after which the task record and actual reply can be checked.
    wait.timeout = 10
    clock[0] = 0.0

    def settle(_seconds):
        current = json.loads(task_path.read_text(encoding="utf-8"))
        current["status"] = "done"
        current["result_file"] = str(task_root / "review-fixture.result")
        current["resolved_model"] = "claude-opus-5-5"
        task_path.write_text(json.dumps(current), encoding="utf-8")

    monkeypatch.setattr(delegate.time, "sleep", settle)
    assert delegate.cmd_wait(wait) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "done"

    completed, reply = recorder._task(review_task, task_root)
    assert completed["run_nonce"] == review_nonce
    assert completed["resolved_model"] == "claude-opus-5-5"
    assert recorder.normalize_verdict(reply) == "APPROVED"

    # Publication is permitted only after the PR still names the reviewed
    # branch and SHA. Stub the GitHub lookup at that boundary and prove a moved
    # head prevents the publisher from running.
    monkeypatch.setattr(
        recorder,
        "_pr",
        lambda *_args, **_kwargs: {
            "number": 7,
            "headRefName": "codex/author",
            "headRefOid": "b" * 40,
            "state": "OPEN",
        },
    )
    monkeypatch.setattr(
        recorder,
        "post_commit_status",
        lambda *_args, **_kwargs: pytest.fail("moved head must not publish"),
    )
    with pytest.raises(recorder.RecordError, match="PR head moved since review"):
        recorder.record(
            review_task,
            pr_number=7,
            task_root=task_root,
            lock_root=tmp_path / "locks",
        )

    # A completed record without its reply is not publishable evidence.
    reply_path = task_path.with_suffix(".result")
    missing_reply = task_root / "missing.reply"
    reply_path.rename(missing_reply)
    with pytest.raises(recorder.RecordError, match="record or reply unavailable"):
        recorder._task(review_task, task_root)
    missing_reply.rename(reply_path)

    # Terminal failure wins over approval-looking reply text.
    failed = dict(completed, status="failed")
    task_path.write_text(json.dumps(failed), encoding="utf-8")
    with pytest.raises(recorder.RecordError, match="review task is not done"):
        recorder._task(review_task, task_root)
