"""Offline walkthrough for the documented detached formal-review path (#9663)."""

from __future__ import annotations

import json
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

    reference = REFERENCE.read_text(encoding="utf-8")
    assert "`--background` flag is rejected" in reference
    assert "scripts/delegate.py dispatch" in reference
    assert "--pinned-head \"$HEAD_SHA\"" in reference
    assert "--run-nonce \"$REVIEW_NONCE\"" in reference
    assert "scripts/review/record_cf_verdict.py" in reference

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
    # Model the detached producer's two-line stdout receipt. It returns while
    # the worker fixture is still running, leaving the driver free to proceed.
    dispatch_result = "review-fixture\n" + NONCE
    dispatch_lines = dispatch_result.splitlines()
    assert dispatch_lines == ["review-fixture", NONCE]
    review_task, review_nonce = dispatch_lines
    assert json.loads(task_path.read_text(encoding="utf-8"))["status"] == "running"
    independent_work_completed = True
    assert independent_work_completed

    # The armed wait accepts only this run nonce. The first read is still
    # running; the fixture's worker boundary settles it on the next wake.
    wait = delegate.build_parser().parse_args(
        ["wait", review_task, "--run-nonce", review_nonce, "--timeout", "10"]
    )
    assert wait.run_nonce == NONCE
    assert wait.func is delegate.cmd_wait

    def read_task(_task_id):
        return task_path, json.loads(task_path.read_text(encoding="utf-8"))

    def settle(_seconds):
        current = json.loads(task_path.read_text(encoding="utf-8"))
        current["status"] = "done"
        current["result_file"] = str(task_root / "review-fixture.result")
        current["resolved_model"] = "claude-opus-5-5"
        task_path.write_text(json.dumps(current), encoding="utf-8")

    monkeypatch.setattr(delegate, "_read_state_or_archived", read_task)
    monkeypatch.setattr(delegate, "_heal_dead_task", lambda *_args, **_kwargs: None)
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

    # Terminal failure wins over approval-looking reply text.
    failed = dict(completed, status="failed")
    task_path.write_text(json.dumps(failed), encoding="utf-8")
    with pytest.raises(recorder.RecordError, match="review task is not done"):
        recorder._task(review_task, task_root)
