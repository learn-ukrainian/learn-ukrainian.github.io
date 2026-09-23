"""Branch-pinned verdict recorder failure and serialization tests (#8509)."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.review import record_cf_verdict as recorder

SHA = "a" * 40
OTHER = "b" * 40
BRANCH = "codex/42"
REPOSITORY = "owner/repo"


def task(**updates):
    data = {
        "repository": REPOSITORY,
        "worktree_branch": BRANCH,
        "worktree_base_sha": SHA,
        "model": "gpt-6-sol",
        "agent": "codex",
        "started_at": "2026-09-23T12:00:00.000001+00:00",
        "status": "done",
    }
    data.update(updates)
    return data


def write_task(root: Path, *, task_id="review-one", reply="VERDICT: APPROVE", **updates):
    root.mkdir(parents=True, exist_ok=True)
    (root / task_id).parent.mkdir(parents=True, exist_ok=True)
    (root / f"{task_id}.json").write_text(json.dumps(task(**updates)))
    (root / f"{task_id}.result").write_text(reply)


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("VERDICT: APPROVE", "APPROVED"),
        ("VERDICT: APPROVED", "APPROVED"),
        ("VERDICT: REQUEST_CHANGES", "CHANGES_REQUESTED"),
        ("VERDICT: CHANGES_REQUESTED", "CHANGES_REQUESTED"),
        ("VERDICT: BLOCKED", "BLOCKED"),
    ],
)
def test_token_normalization(reply, expected):
    assert recorder.normalize_verdict(reply) == expected


def test_full_nested_task_id_is_safe_and_loadable(tmp_path):
    write_task(tmp_path, task_id="codex/review-one")
    loaded, reply = recorder._task("codex/review-one", tmp_path)
    assert loaded["status"] == "done"
    assert reply == "VERDICT: APPROVE"
    with pytest.raises(recorder.RecordError, match="invalid task id"):
        recorder._task("codex/../review-one", tmp_path)


def test_repo_root_timeout_fails_closed(monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(recorder.subprocess, "run", timeout)
    with pytest.raises(recorder.RecordError, match="Git repository lookup timed out after 30 seconds"):
        recorder._repo_root()


@pytest.mark.parametrize("reply", ["No verdict", "VERDICT: APPROVE\nVERDICT: BLOCKED"])
def test_missing_or_ambiguous_verdict_refused(reply):
    with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
        recorder.normalize_verdict(reply)


@pytest.mark.parametrize(
    "updates,reply,reason",
    [
        ({"status": "running"}, "VERDICT: APPROVE", "not done"),
        ({"worktree_branch": None}, "VERDICT: APPROVE", "--branch"),
        ({"worktree_base_sha": None}, "VERDICT: APPROVE", "reviewed SHA"),
        (
            {"agent": "cursor", "resolved_model_known": False, "resolved_model": "unknown"},
            "VERDICT: APPROVE",
            "Cursor reviewer model unknown",
        ),
        ({}, "VERDICT: APPROVE\nVERDICT: BLOCKED", "ambiguous"),
        ({}, "No verdict", "missing"),
    ],
)
def test_task_refusals_before_network(tmp_path, updates, reply, reason):
    tasks = tmp_path / "tasks"
    write_task(tasks, reply=reply, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


def setup_record(monkeypatch, tmp_path, *, head=SHA, branch=BRANCH, families=None, status_error=False):
    tasks = tmp_path / "tasks"
    write_task(tasks)
    comments = []
    calls = {"posts": 0, "statuses": 0}

    def fake_json(args, *, input_text=None):
        if args[:3] == ["gh", "pr", "view"]:
            return {"number": 42, "headRefOid": head, "headRefName": branch, "state": "OPEN"}
        if args[:3] == ["gh", "pr", "list"]:
            return [{"number": 42, "headRefOid": head, "headRefName": branch}]
        if args[:4] == ["gh", "api", "-X", "POST"]:
            calls["posts"] += 1
            item = {
                "id": calls["posts"],
                "body": json.loads(input_text)["body"],
                "user": {"login": "fleet"},
                "author_association": "MEMBER",
                "created_at": "2026-09-23T13:00:00Z",
                "updated_at": "2026-09-23T13:00:00Z",
            }
            comments.append(item)
            return item
        if args[:2] == ["gh", "api"] and "issues/comments/" in args[2]:
            return comments[-1]
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_json", fake_json)
    monkeypatch.setattr(
        recorder,
        "author_families",
        lambda repository, number, task_root: families if families is not None else {"google"},
    )
    monkeypatch.setattr(recorder.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(recorder.GitHubAdapter, "comments", lambda self, repository, number: list(comments))

    def fake_status(**kwargs):
        calls["statuses"] += 1
        if status_error:
            raise RuntimeError("status write failed")

    monkeypatch.setattr(recorder, "post_commit_status", fake_status)
    return tasks, comments, calls


def test_head_and_branch_mismatch_refused(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path, head=OTHER)
    with pytest.raises(recorder.RecordError, match="head moved"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    tasks, _, _ = setup_record(monkeypatch, tmp_path, branch="other/branch")
    with pytest.raises(recorder.RecordError, match="branch does not match"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def test_same_family_refused(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path, families={"google", "openai"})
    with pytest.raises(recorder.RecordError, match="equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def test_rerun_same_task_reconciles_status_without_new_comment(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    first = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    second = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert first["comment"] == "posted"
    assert second["comment"] == "existing"
    assert calls == {"posts": 1, "statuses": 2}
    assert len(comments) == 1
    assert comments[0]["body"].splitlines()[-1].startswith("<!-- cf-verdict v1 sha=")


def test_status_failure_keeps_comment_and_reports_partial(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, status_error=True)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert result["status"].startswith("failed:")
    assert len(comments) == 1


def test_concurrent_recorders_for_same_sha_serialize(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(recorder.record, "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
            for _ in range(2)
        ]
        results = [future.result() for future in futures]
    assert {result["comment"] for result in results} == {"posted", "existing"}
    assert calls["posts"] == 1
    assert len(comments) == 1


def test_two_tasks_on_one_sha_each_get_a_comment(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(
        tasks, task_id="review-two", reply="VERDICT: CHANGES_REQUESTED", started_at="2026-09-23T12:00:01.000001+00:00"
    )
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    recorder.record("review-two", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert len(comments) == 2
    assert calls["posts"] == 2


def test_mixed_or_unknown_author_family_refused(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    def commit(trailer):
        return {"commit": {"message": f"work\n\nX-Agent: {trailer}"}}

    monkeypatch.setattr(
        recorder, "_pages", lambda args: [commit("codex/gpt-6-sol"), commit("agy/gemini-3.8-flash-high")]
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai", "google"}
    monkeypatch.setattr(recorder, "_pages", lambda args: [commit("cursor/task-without-record")])
    with pytest.raises(recorder.RecordError, match="provenance unavailable"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize(
    "trailer,expected",
    [
        ("kimi/k2", {"moonshot"}),
        ("codex/gpt-6-luna", {"openai"}),
        ("cursor/grok-4.7", {"xai"}),
    ],
)
def test_author_family_resolves_model_with_harness_fallback(monkeypatch, tmp_path, trailer, expected):
    def commit(value):
        return {"commit": {"message": f"work\n\nX-Agent: {value}"}}

    monkeypatch.setattr(recorder, "_pages", lambda args: [commit(trailer)])
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == expected


def test_unknown_harness_model_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "work\n\nX-Agent: unknownharness/x"}}],
    )
    with pytest.raises(recorder.RecordError):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_cursor_auto_union_family_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "work\n\nX-Agent: cursor/auto"}}],
    )
    with pytest.raises(recorder.RecordError, match="mixed or unknown"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_mixed_xai_and_moonshot_author_families_are_returned(monkeypatch, tmp_path):
    def commit(trailer):
        return {"commit": {"message": f"work\n\nX-Agent: {trailer}"}}

    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [commit("grok/grok-4.7"), commit("kimi/k2")],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"xai", "moonshot"}


def test_author_task_record_resolves_task_id_trailer(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, task_id="author-task", model="gemini-3.8-flash-high", agent="agy")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: agy/author-task"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"google"}


def test_comment_truncation_retains_marker():
    body = recorder.build_comment(
        sha=SHA,
        task_id="review-one",
        started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED",
        model="gpt-6-sol",
        family="openai",
        reply="x" * 70_000,
    )
    assert len(body.encode()) <= recorder.MAX_COMMENT_BYTES
    assert "[Review reply truncated" in body
    assert recorder.parse_marker(body)["task"] == "review-one"
