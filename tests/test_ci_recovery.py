"""Behavioral proof for the shared rerun/re-enqueue allowance (#10304)."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from scripts.opsec import prepublish as gate
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.publish import github as pub
from scripts.review.record_cf_verdict import build_comment
from tests.opsec_fixtures import CATALOG

HEAD = "a" * 40
NEW_HEAD = "b" * 40
TESTED = "c" * 40


def evidence(head=HEAD):
    return {
        "pr": 42,
        "head": head,
        "run_id": 123,
        "job_ids": [456],
        "tested_sha": TESTED,
        "failure_evidence": "Job log confirms runner checkout failure",
        "unrelated_to_diff": "Failure precedes execution of changed code",
    }


class Transport:
    def __init__(self):
        self.head = HEAD
        self.proof = evidence()
        self.approved = True
        self.attempt = 1
        self.event = "merge_group"
        self.failed_ids = [456]
        self.removed = True
        self.future_commit = False
        self.failure = False
        self.moved = False
        self.pull_reads = 0
        self.writes = []

    def __call__(self, argv, **kwargs):
        if argv[1:3] == ["pr", "view"]:
            data = {"number": 42, "isDraft": False, "headRefOid": self.head}
        elif argv[1:3] == ["pr", "checks"]:
            data = []
        elif argv[1:5] == ["api", "--method", "POST", "graphql"]:
            data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "headRefOid": self.head,
                            "isMergeQueueEnabled": True,
                            "viewerMergeHeadlineText": "change (#42)",
                            "viewerMergeBodyText": "change",
                        }
                    }
                }
            }
        elif argv[1] == "api":
            endpoint = next(arg for arg in argv if arg.startswith("repos/") or arg.split("?", 1)[0] == "user").split("?", 1)[0]
            if endpoint.endswith("/comments"):
                approval = {
                    "body": build_comment(
                        sha=self.head,
                        task_id="review",
                        started="2026-10-09T10:00:00.000001+00:00",
                        verdict="APPROVED" if self.approved else "CHANGES_REQUESTED",
                        model="claude-opus-5-5",
                        family="anthropic",
                        reply="VERDICT: APPROVE",
                    ),
                    "user": {"login": "driver"},
                    "author_association": "MEMBER",
                    "created_at": "2026-10-09T10:00:01Z",
                    "updated_at": "2026-10-09T10:00:01Z",
                }
                comments = [approval]
                if self.proof is not None:
                    comments.append({"id": 789, "body": "<!-- ci-recovery-evidence " + json.dumps(self.proof) + " -->"})
                data = [comments]
            elif endpoint.endswith("/timeline"):
                data = (
                    [[{"event": "removed_from_merge_queue", "created_at": "2026-10-09T11:00:00Z"}]]
                    if self.removed
                    else [[]]
                )
                if self.future_commit:
                    data[0].append({"event": "committed", "sha": self.head,
                                    "committer": {"date": "2099-01-01T00:00:00Z"}})
            elif endpoint.endswith("/jobs"):
                data = [{"jobs": [{"id": job, "conclusion": "failure"} for job in self.failed_ids]}]
            elif endpoint.endswith("/runs/123"):
                data = {
                    "id": 123,
                    "status": "completed",
                    "conclusion": "failure",
                    "head_sha": TESTED,
                    "event": self.event,
                    "head_branch": "gh-readonly-queue/main/pr-42-abcdef",
                    "run_attempt": self.attempt,
                    "pull_requests": []
                    if self.event == "merge_group"
                    else [{"number": 42, "head": {"sha": self.head}}],
                }
            elif endpoint.endswith("/pulls/42"):
                self.pull_reads += 1
                data = {"state": "open", "head": {"sha": NEW_HEAD if self.moved and self.pull_reads > 1 else self.head}}
            elif endpoint == "user":
                data = {"login": "driver"}
            else:
                pytest.fail(f"unexpected read {endpoint}")
        else:
            self.writes.append(argv)
            if self.failure:
                raise subprocess.TimeoutExpired(argv, 60)
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")


@pytest.fixture
def setup(tmp_path, monkeypatch, synthetic_opsec):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    common = tmp_path / ".git"
    common.mkdir()
    # On origin/main the behavioral regressions exercise the old publisher.
    if hasattr(pub, "recovery"):
        monkeypatch.setattr(pub.recovery, "ledger_path", lambda cwd: common / "ci-recovery.sqlite3")
    return tmp_path, Transport()


def recover(setup, action):
    root, transport = setup
    if action == "run-rerun":
        return pub.publish(action, number=123, repo="unit/public", cwd=root, env={}, runner=transport)
    if action == "keeper":
        client = keeper.GitHub(root, "unit/public")
        # Use the real keeper adapter and real publisher, with only the transport replaced.
        with pytest.MonkeyPatch.context() as patches:
            patches.setattr(
                keeper,
                "request_run",
                lambda request, **kwargs: pub.request_run(request, runner=transport, env={}, **kwargs),
            )
            return client.enqueue(42, transport.head, **({"recovery_attempt": True} if hasattr(pub, "recovery") else {}))
    return pub.publish("pr-merge", number=42, repo="unit/public", cwd=root, env={}, runner=transport)


@pytest.mark.parametrize("first", ["run-rerun", "keeper", "direct"])
@pytest.mark.parametrize("second", ["run-rerun", "keeper", "direct"])
def test_paths_share_allowance_and_preserve_old_head(setup, first, second):
    _, transport = setup
    recover(setup, first)
    assert len(transport.writes) == 1
    error = keeper.KeeperError if second == "keeper" else gate.PublishBlocked
    with pytest.raises(
        error, match="RECOVERY_ALLOWANCE_SPENT: first=" + ("run-rerun" if first == "run-rerun" else "re-enqueue")
    ):
        recover(setup, second)
    assert len(transport.writes) == 1
    transport.head = NEW_HEAD
    transport.proof = evidence(NEW_HEAD)
    recover(setup, second)
    assert len(transport.writes) == 2
    transport.head = HEAD
    transport.proof = evidence()
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, second)
    assert len(transport.writes) == 2


@pytest.mark.parametrize("action", ["run-rerun", "direct"])
def test_missing_evidence_refuses_without_consuming(setup, action):
    _, transport = setup
    transport.proof = None
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, action)
    assert transport.writes == []
    transport.proof = evidence()
    recover(setup, action)
    assert len(transport.writes) == 1


@pytest.mark.parametrize("field", ["run_id", "job_ids", "tested_sha", "failure_evidence", "unrelated_to_diff", "head"])
def test_partial_evidence_refuses(setup, field):
    _, transport = setup
    del transport.proof[field]
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, "run-rerun")
    assert transport.writes == []


@pytest.mark.parametrize("action", ["run-rerun", "direct"])
@pytest.mark.parametrize("cause", ["unapproved", "jobs", "tested", "moved"])
def test_invalid_live_evidence_refuses(setup, action, cause):
    _, transport = setup
    if cause == "unapproved":
        transport.approved = False
    elif cause == "jobs":
        transport.failed_ids.append(999)
    elif cause == "tested":
        transport.proof["tested_sha"] = HEAD
    else:
        transport.moved = True
        if action == "direct":
            transport.pull_reads = 1
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_"):
        recover(setup, action)
    assert transport.writes == []


def test_failed_transport_does_not_refund(setup):
    _, transport = setup
    transport.failure = True
    with pytest.raises(subprocess.TimeoutExpired):
        recover(setup, "run-rerun")
    transport.failure = False
    with pytest.raises(gate.PublishBlocked, match=r"RECOVERY_ALLOWANCE_SPENT.*run-rerun"):
        recover(setup, "direct")
    assert len(transport.writes) == 1


def test_concurrent_consumption_serializes(setup):
    root, _ = setup
    module = pub.recovery
    path = module.ledger_path(root)
    barrier = Barrier(2)

    def attempt(action):
        barrier.wait(timeout=10)
        try:
            module.consume(path, "github.com/unit/public", 42, HEAD, action, evidence())
            return "allowed"
        except gate.PublishBlocked as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, ["run-rerun", "re-enqueue"]))
    assert results.count("allowed") == 1
    assert sum(value.startswith("RECOVERY_ALLOWANCE_SPENT:") for value in results) == 1
    assert module.first_attempt(path, "github.com/unit/public", 42, HEAD)["action"] in {"run-rerun", "re-enqueue"}


def test_legacy_spending_survives_migration(setup):
    root, transport = setup
    (root / "batch_state").mkdir()
    (root / "batch_state/merge_queue_keeper.json").write_text(json.dumps({"requeued": {f"42:{HEAD}": "previous"}}))
    with pytest.raises(gate.PublishBlocked, match=r"RECOVERY_ALLOWANCE_SPENT.*legacy"):
        recover(setup, "run-rerun")
    assert transport.writes == []


def test_first_enqueue_does_not_spend_recovery(setup):
    root, transport = setup
    transport.removed = False
    transport.proof = None
    recover(setup, "direct")
    assert len(transport.writes) == 1
    assert not pub.recovery.ledger_path(root).exists()


@pytest.mark.parametrize("action", ["run-rerun", "direct"])
def test_prior_workflow_attempt_without_record_refuses(setup, action):
    _, transport = setup
    transport.attempt = 2
    with pytest.raises(gate.PublishBlocked, match=r"RECOVERY_ALLOWANCE_SPENT.*prior workflow"):
        recover(setup, action)
    assert transport.writes == []


def test_ledger_path_shared_across_linked_worktrees(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "fixture",
        ],
        check=True,
        timeout=30,
    )
    linked = tmp_path / "linked"
    subprocess.run(
        ["git", "-C", str(root), "worktree", "add", "--detach", str(linked)], check=True, capture_output=True, timeout=30
    )
    assert pub.recovery.ledger_path(root) == pub.recovery.ledger_path(linked)


def test_ledger_unavailable_refuses(tmp_path):
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_RECORD_UNAVAILABLE"):
        pub.recovery.ledger_path(tmp_path)
    corrupt = tmp_path / "ci-recovery.sqlite3"
    corrupt.write_text("corrupt")
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_RECORD_UNAVAILABLE"):
        pub.recovery.first_attempt(corrupt, "unit/public", 42, HEAD)
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_RECORD_UNAVAILABLE"):
        pub.recovery.consume(corrupt, "unit/public", 42, HEAD, "run-rerun", evidence())


def test_cli_uses_the_same_allowance(setup):
    _, transport = setup
    assert pub.main(["run-rerun", "--repo", "unit/public", "--number", "123"], runner=transport) == 0
    assert pub.main(["run-rerun", "--repo", "unit/public", "--number", "123"], runner=transport) == 2
    assert len(transport.writes) == 1


def test_pull_request_run_uses_pr_head_not_tested_merge_sha(setup):
    _, transport = setup
    transport.event = "pull_request"
    recover(setup, "run-rerun")
    assert len(transport.writes) == 1


def test_malformed_posted_evidence_refuses(setup):
    module = pub.recovery
    comments = [{"id": 1, "body": "<!-- ci-recovery-evidence {bad json} -->"},
                {"id": 2, "body": "<!-- ci-recovery-evidence {\"job_ids\":[]} -->"}]
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        module.evidence_from_comments(comments, 42, HEAD)


def test_legacy_state_corruption_fails_closed(setup):
    root, transport = setup
    (root / "batch_state").mkdir()
    (root / "batch_state/merge_queue_keeper.json").write_text("corrupt")
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_RECORD_UNAVAILABLE"):
        recover(setup, "run-rerun")
    assert transport.writes == []


def test_future_commit_date_cannot_refund_same_head(setup):
    _, transport = setup
    recover(setup, "run-rerun")
    transport.future_commit = True
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, "direct")
    assert len(transport.writes) == 1
