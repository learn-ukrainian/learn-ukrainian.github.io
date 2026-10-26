"""C2244 changed-behavior tests for false status, attribution and side effects."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts import flow
from scripts.common.github_client import Response
from scripts.orchestration import dead_worker_state
from scripts.review.record_cf_verdict import build_comment

HEAD = "a" * 40
OLD = "b" * 40
NOW = "2026-10-26T12:00:00Z"
NONCE = "29c6cfa493ff44f8b2b6dc563d9f80e4"


@pytest.fixture
def source(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main", str(root)], check=True, capture_output=True, timeout=30)
    (root / "batch_state/tasks/archive").mkdir(parents=True)
    reader = flow.Reader(root)
    calls = []
    issue = {"number": 17, "state": "open", "created_at": NOW, "body": ""}
    pr = {
        "number": 23,
        "state": "open",
        "merged_at": None,
        "head": {"sha": HEAD, "ref": "codex/author", "repo": {"full_name": flow.REPOSITORY}},
        "base": {"ref": "main", "repo": {"full_name": flow.REPOSITORY}},
    }
    replies = {
        "user": {"login": "repository-bot"},
        f"repos/{flow.REPOSITORY}/issues/17": issue,
        f"repos/{flow.REPOSITORY}/issues/17/timeline": [],
        f"repos/{flow.REPOSITORY}/pulls/23": pr,
        f"repos/{flow.REPOSITORY}/pulls/23/reviews": [],
        f"repos/{flow.REPOSITORY}/issues/23/comments": [],
        f"repos/{flow.REPOSITORY}/commits/{HEAD}/check-runs": {"total_count": 0, "check_runs": []},
        "graphql": {"data": {"repository": {"pullRequest": {"headRefOid": HEAD, "isInMergeQueue": False}}}},
    }

    def transport(method, endpoint, headers, body, timeout):
        calls.append((method, endpoint))
        assert endpoint == "user" or endpoint == "graphql" or endpoint.startswith(f"repos/{flow.REPOSITORY}/")
        assert method == "GET" or (method == "POST" and json.loads(body)["query"] == flow.GQL_READS["queue-status"])
        key = endpoint.split("?", 1)[0]
        if key not in replies:
            return Response(404, {}, b"{}")
        return Response(200, {}, json.dumps(replies[key]).encode())

    reader.github.transport = transport
    # Isolate every test from real remote branches, preserving real local Git reads.
    original_git = reader.git

    def git(*args, **kwargs):
        if args[0] == "ls-remote":
            return f"https://github.com/{flow.REPOSITORY}.git\n" if "--get-url" in args else ""
        return original_git(*args, **kwargs)

    reader.git = git
    membership = {
        "repository": flow.REPOSITORY,
        "effective_membership": {"17": {"streams": ["devops"], "epics": [5703], "unique_stream": True}},
    }
    monkeypatch.setattr(flow, "read_membership_index", lambda *a, **kw: membership)
    monkeypatch.setattr(flow, "load_registry", lambda: {"devops": [5703]})

    def local(route):
        if route.startswith("/api/epics/"):
            return {
                "registered": True,
                "stream_name": "devops",
                "lease": {
                    "state": "active",
                    "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                    "holder": {"agent": "codex"},
                },
            }
        assert route == "/api/work/v1/projection?stream=devops"
        return {"orientation_bound": {"complete": False}, "items": []}

    monkeypatch.setattr(flow, "local_read", local)
    return root, reader, replies, issue, pr, calls


def write_task(root, **updates):
    row = {
        "task_id": "owned-author",
        "run_nonce": NONCE,
        "repository": flow.REPOSITORY,
        "status": "done",
        "mode": "danger",
        "started_at": NOW,
        "worktree_path": str(root / ".worktrees/dispatch/codex/author"),
        "worktree_branch": "codex/author",
        "runtime_tmp_root": str(root / "runtime/author"),
        "dor_preflight": {"issues": [17], "dor": "PASS"},
    }
    row.update(updates)
    (root / "batch_state/tasks/owned-author.json").write_text(json.dumps(row))
    return row


def attach_pr(replies):
    replies[f"repos/{flow.REPOSITORY}/issues/17/timeline"] = [
        {
            "event": "cross-referenced",
            "source": {
                "issue": {
                    "number": 23,
                    "pull_request": {},
                    "repository_url": f"https://api.github.com/repos/{flow.REPOSITORY}",
                }
            },
        }
    ]


def comment(sha=HEAD, verdict="APPROVED"):
    text = build_comment(
        sha=sha,
        task_id="independent-review",
        started="2026-10-26T12:00:00.000000Z",
        verdict=verdict,
        model="gemini-3.1-pro-preview",
        family="gemini",
        reply="Reviewed evidence.",
    )
    return {
        "id": 91,
        "body": text,
        "user": {"login": "repository-bot"},
        "author_association": "MEMBER",
        "created_at": "2026-10-26T12:05:00Z",
        "updated_at": "2026-10-26T12:05:00Z",
    }


def test_issue_and_lane_do_not_lose_native_issue_when_dashboard_empty(source):
    _, reader, _, _, _, _ = source
    single = flow.collect(reader, issue=17)
    lane = flow.collect(reader, lane="devops")
    assert single["issues"][0]["issue"] == lane["issues"][0]["issue"] == 17
    assert single["issues"][0]["driver"] == "codex-devops"
    assert "lane_projection_incomplete" in lane["missing_evidence"]


def test_created_does_not_borrow_issue_creation_as_state_age(source):
    _, reader, _, _, _, _ = source
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["state"] == "Created"
    assert row["state_since"] is None and row["age_s"] is None
    assert row["flags"]["overdue"] is None


def test_native_done_without_delivery_never_becomes_cleaned(source):
    root, reader, _, _, _, _ = source
    write_task(root)
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["state"] == "unknown"
    assert "native_done_is_not_delivery" in row["reasons"]
    assert row["resources"]["tasks"][0]["nonce"] == NONCE
    assert set(row["resources"]) == {"tasks", "local_branches", "remote_branches", "worktrees", "temp_dirs", "prs"}


def test_moved_head_invalidates_published_approval(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    replies[f"repos/{flow.REPOSITORY}/issues/23/comments"] = [comment(OLD)]
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["review"]["reviewed_sha"] == OLD
    assert row["review"]["head_sha"] == HEAD
    assert row["review"]["current"] is False
    assert row["state"] != "Testing"
    assert "moved_head_invalidates_review" in row["missing_evidence"]


@pytest.mark.parametrize(
    "status,conclusion,expected", [("completed", "cancelled", "failed"), ("in_progress", None, "pending")]
)
def test_cancelled_ci_is_failure_and_pending_exact_head_is_testing(source, status, conclusion, expected):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    replies[f"repos/{flow.REPOSITORY}/issues/23/comments"] = [comment()]
    replies[f"repos/{flow.REPOSITORY}/commits/{HEAD}/check-runs"] = {
        "total_count": 1,
        "check_runs": [{"name": "CI Gate", "status": status, "conclusion": conclusion, "head_sha": HEAD}],
    }
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["ci"] == expected
    assert row["state"] == ("Testing" if expected == "pending" else "unknown")
    assert row["flags"]["failed"] is (expected == "failed")


def test_absent_ci_is_unknown(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["ci"] == "unknown"
    assert "absent_ci_or_required_check_contract" in row["missing_evidence"]


def test_head_moving_during_observation_invalidates_testing(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    replies[f"repos/{flow.REPOSITORY}/issues/23/comments"] = [comment()]
    replies[f"repos/{flow.REPOSITORY}/commits/{HEAD}/check-runs"] = {
        "total_count": 1,
        "check_runs": [{"name": "CI Gate", "status": "in_progress", "head_sha": HEAD}],
    }
    replies["graphql"]["data"]["repository"]["pullRequest"]["headRefOid"] = OLD
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["state"] != "Testing"
    assert row["review"]["current"] is False and row["ci"] == "unknown"
    assert "head_changed_during_observation" in row["missing_evidence"]


def test_native_approval_does_not_replace_independent_record(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    replies[f"repos/{flow.REPOSITORY}/pulls/23/reviews"] = [
        {"state": "APPROVED", "commit_id": HEAD, "submitted_at": NOW}
    ]
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["review"]["current"] is True
    assert row["review"]["verdict"] == "unknown"


def test_common_reaper_proof_and_full_nonce_required_after_merge(source):
    root, reader, replies, _, pr, _ = source
    attach_pr(replies)
    pr.update(merged_at="2026-10-26T12:10:00Z", state="closed")
    row = write_task(
        root,
        worktree_reap_proof={
            "schema": "merged-reuse-reap.v1",
            "owner": "owned-author",
            "run_nonce": NONCE,
            "pr_number": 23,
            "pr_head_sha": HEAD,
            "pr_state": "MERGED",
            "clean": True,
        },
    )
    folder = root / "batch_state/worktree-reaper"
    folder.mkdir()
    receipt = {
        "schema_version": "worktree-reaper-journal.v1",
        "at": "2026-10-26T12:15:00Z",
        "event": "reap",
        "action": "removed",
        "path": row["worktree_path"],
        "branch": row["worktree_branch"],
        "pr": {"number": 23, "state": "MERGED", "head_sha": HEAD},
    }
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Merged"
    (folder / "journal.jsonl").write_text(json.dumps(receipt) + "\n")
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Cleaned"
    row["worktree_reap_proof"]["run_nonce"] = "another-attempt"
    (root / "batch_state/tasks/owned-author.json").write_text(json.dumps(row))
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Merged"


def test_partial_task_inventory_never_certifies_resource_absence(source):
    root, reader, _, _, _, _ = source
    (root / "batch_state/tasks/broken.json").write_text("{")
    row = flow.collect(reader, issue=17)["issues"][0]
    assert all(value.startswith("incomplete") for value in row["coverage"].values())


def test_missing_task_bindings_never_certify_empty_resource_inventory(source):
    root, reader, _, _, _, _ = source
    write_task(root, worktree_branch=None, worktree_path=None, runtime_tmp_root=None)
    row = flow.collect(reader, issue=17)["issues"][0]
    for kind in ("local_branches", "remote_branches", "worktrees", "temp_dirs"):
        assert row["resources"][kind] == []
        assert row["coverage"][kind].startswith("incomplete")
    assert "owned_resource_coverage_incomplete" in row["missing_evidence"]


def test_missing_review_source_preserves_known_pr_head(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    del replies[f"repos/{flow.REPOSITORY}/pulls/23/reviews"]
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["review"]["head_sha"] == HEAD
    assert row["review"]["verdict"] == "unknown"
    assert "review_source_unknown" in row["missing_evidence"]


def test_unowned_branch_prefix_and_private_bodies_never_escape(source):
    root, reader, _, issue, _, _ = source
    issue["body"] = "private transcript body sk-" + "x" * 36
    secret_path = str(root.parent / "private-fixture/retained")
    write_task(root, runtime_tmp_root=secret_path, prompt_file=secret_path, result=issue["body"])
    unrelated = {
        "task_id": "devops-17-unowned",
        "run_nonce": "foreign-attempt",
        "repository": "private/repository",
        "worktree_branch": "codex/17-unowned",
        "runtime_tmp_root": secret_path,
    }
    (root / "batch_state/tasks/unowned.json").write_text(json.dumps(unrelated))
    row = flow.collect(reader, issue=17)["issues"][0]
    output = json.dumps(row)
    assert secret_path not in output and issue["body"] not in output
    assert "devops-17-unowned" not in output and "private/repository" not in output
    assert row["resources"]["temp_dirs"][0]["path"].startswith("resource-")


def test_ready_requires_dor_and_live_author_requires_process_identity(source):
    root, reader, _, _, _, _ = source
    write_task(root, status="spawning")
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Ready"
    write_task(
        root,
        status="running",
        pid=os.getpid(),
        worker_identity=dead_worker_state.capture_worker_identity(os.getpid(), self_process=True),
    )
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "In progress"
    write_task(root, status="running", pid=os.getpid())
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["state"] != "In progress" and "task_liveness_unknown" in row["reasons"]


def test_fixing_and_queue_use_affirmative_exact_head_evidence(source):
    _, reader, replies, _, _, _ = source
    attach_pr(replies)
    replies[f"repos/{flow.REPOSITORY}/issues/23/comments"] = [comment(verdict="CHANGES_REQUESTED")]
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Fixing"
    replies[f"repos/{flow.REPOSITORY}/issues/23/comments"] = []
    replies["graphql"]["data"]["repository"]["pullRequest"].update(
        isInMergeQueue=True, mergeQueueEntry={"enqueuedAt": NOW}
    )
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "Queued"


def test_in_review_does_not_use_stale_review_head(source):
    root, reader, replies, _, _, _ = source
    attach_pr(replies)
    identity = dead_worker_state.capture_worker_identity(os.getpid(), self_process=True)
    write_task(root, status="running", pid=os.getpid(), worker_identity=identity, mode="read-only", pinned_head=HEAD)
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "In review"
    write_task(root, status="running", pid=os.getpid(), worker_identity=identity, mode="read-only", pinned_head=OLD)
    assert flow.collect(reader, issue=17)["issues"][0]["state"] != "In review"


def test_dirty_retained_worktree_is_reported(source):
    root, reader, _, _, _, _ = source
    row = write_task(root)
    worktree = Path(row["worktree_path"])
    worktree.mkdir(parents=True)
    subprocess.run(["git", "init", "--initial-branch=main", str(worktree)], check=True, capture_output=True, timeout=30)
    (worktree / "retained.txt").write_text("uncommitted work")
    result = flow.collect(reader, issue=17)["issues"][0]
    assert result["resources"]["worktrees"][0]["dirty"] is True
    assert "dirty_retained_worktree" in result["reasons"]
    assert (worktree / "retained.txt").read_text() == "uncommitted work"


def test_dispatcher_v2_process_identity_is_read_without_terminalization(source):
    from scripts.dispatcher.worker import _identity

    root, reader, _, _, _, _ = source
    write_task(root, schema_version=2, status="running", pid=os.getpid(), process_start=_identity(os.getpid()))
    path = root / "batch_state/tasks/owned-author.json"
    before = path.read_bytes()
    assert flow.collect(reader, issue=17)["issues"][0]["state"] == "In progress"
    assert path.read_bytes() == before


def test_local_git_inventory_cannot_execute_repository_fsmonitor(source):
    root, reader, _, _, _, _ = source
    marker = root / "unexpected-side-effect"
    (root / "retained.txt").write_text("uncommitted work")
    subprocess.run(["git", "config", "core.fsmonitor", f"touch {marker}"], cwd=root, check=True, timeout=30)
    assert "retained.txt" in reader.git("status", "--porcelain")
    assert not marker.exists()


def test_owned_local_branch_inventory_excludes_unowned_prefix(source):
    root, reader, _, _, _, _ = source
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "--allow-empty",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    )
    for branch in ("codex/author", "codex/17-unowned"):
        subprocess.run(["git", "branch", branch], cwd=root, check=True, timeout=30)
    write_task(root)
    result = flow.collect(reader, issue=17)["issues"][0]
    assert len(result["resources"]["local_branches"]) == 1
    assert result["resources"]["local_branches"][0]["present"] is True
    assert len(result["resources"]["remote_branches"]) == 1
    assert result["resources"]["remote_branches"][0]["present"] is False


def test_rewritten_remote_never_contacts_a_foreign_repository(source):
    root, reader, _, _, _, _ = source
    write_task(root)
    old_git = reader.git
    contacts = []

    def git(*args, **kwargs):
        if args[0] == "ls-remote":
            if "--get-url" in args:
                return "https://github.com/private/foreign.git"
            contacts.append(args)
        return old_git(*args, **kwargs)

    reader.git = git
    row = flow.collect(reader, issue=17)["issues"][0]
    assert contacts == []
    assert row["coverage"]["remote_branches"].startswith("incomplete")
    assert "private/foreign" not in json.dumps(row)


def test_overdue_uses_existing_owned_acceptance_deadline(source):
    _, reader, _, issue, _, _ = source
    issue["body"] = "- [ ] AC-VERIFY: After merge, review evidence; owner: codex-devops; due: 2020-01-01"
    assert flow.collect(reader, issue=17)["issues"][0]["flags"]["overdue"] is True


def test_cli_rejects_missing_conflicting_and_invalid_selectors():
    for args in (["status"], ["status", "--issue", "0"], ["status", "--issue", "17", "--lane", "devops"]):
        with pytest.raises(SystemExit) as error:
            flow.main(args)
        assert error.value.code == 2


def test_cli_no_write_signalling_provider_or_cross_repository_egress(source, monkeypatch, capsys):
    from scripts.dispatcher.worker import _identity

    root, reader, _, _, _, calls = source
    write_task(root, schema_version=2, status="running", pid=os.getpid(), process_start=_identity(os.getpid()))
    monkeypatch.chdir(root)
    monkeypatch.setattr(flow, "Reader", lambda path: reader)
    monkeypatch.setattr(os, "kill", lambda *a: pytest.fail("status must not signal processes"))
    active = [True]
    forbidden = []

    def audit(event, args):
        if not active[0]:
            return
        if (
            event == "open"
            and len(args) > 2
            and isinstance(args[2], int)
            and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        ):
            forbidden.append("write-open")
        if event in {"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.kill"}:
            forbidden.append(event)
        if event == "sqlite3.connect" and args[0] != ":memory:":
            forbidden.append("persistent-database")
        if event == "subprocess.Popen" and Path(args[0]).name != "git":
            forbidden.append("unexpected-executable")

    sys.addaudithook(audit)
    try:
        assert flow.main(["status", "--issue", "17"]) == 0
    finally:
        active[0] = False
    result = json.loads(capsys.readouterr().out)
    assert result["read_only"] is True and result["issues"][0]["issue"] == 17
    assert forbidden == []
    assert calls and all(
        endpoint == "user" or endpoint.startswith(f"repos/{flow.REPOSITORY}/") for _, endpoint in calls
    )


def test_missing_source_reports_unknown_without_transport_body(source):
    _, reader, replies, _, _, _ = source
    replies.clear()
    row = flow.collect(reader, issue=17)["issues"][0]
    assert row["state"] == "unknown"
    assert "github_issue_unknown" in row["missing_evidence"]


def test_transport_timeout_preserves_partial_report_and_hides_stderr(source):
    _, reader, _, _, _, _ = source

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("gh", 1, stderr="private transcript and host topology")

    reader.github.transport = timeout
    result = flow.collect(reader, lane="devops")
    assert result["issues"][0]["state"] == "unknown"
    assert "github_issue_unknown" in result["issues"][0]["missing_evidence"]
    assert "private transcript" not in json.dumps(result)
