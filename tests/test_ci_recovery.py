"""Behavioral proof for the shared rerun/re-enqueue allowance (#10304)."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
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
        self.status = "completed"
        self.conclusion = "failure"
        self.event = "merge_group"
        self.failed_ids = [456]
        self.removed = True
        self.future_commit = False
        self.removal_head = HEAD
        self.removal_date = "2026-10-09T11:00:00Z"
        self.removal_failure = False
        self.removal_history = None
        self.removal_page_size = 100
        self.removal_reason = "removed by actor"
        self.timeline_count = None
        self.removal_reads = []
        self.pushes = []
        self.associations = None
        self.proof_login = "driver"
        self.proof_association = "MEMBER"
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
            payload = json.loads(Path(argv[6]).read_text())
            query = payload["query"]
            if "timelineItems" in query:
                self.removal_reads.append(payload)
                if self.removal_failure:
                    return subprocess.CompletedProcess(argv, 1, "", "lookup failed")
                events = (
                    self.removal_history
                    if self.removal_history is not None
                    else [
                        {
                            "beforeCommit": {
                                "oid": self.removal_head,
                                "committedDate": "2099-01-01T00:00:00Z"
                                if self.future_commit
                                else "2026-10-09T10:00:00Z",
                            }
                            if self.removal_head
                            else None,
                            "createdAt": self.removal_date,
                            "reason": self.removal_reason,
                        }
                    ]
                    if self.removed
                    else []
                )
                if "first:100" in query:
                    start = int(payload["variables"].get("cursor") or 0)
                    nodes = events[start : start + self.removal_page_size]
                    end = start + len(nodes)
                    removals = {
                        "nodes": nodes,
                        "totalCount": self.timeline_count if self.timeline_count is not None else len(events),
                        "pageInfo": {
                            "hasNextPage": end < len(events),
                            "endCursor": str(end) if nodes else None,
                        },
                    }
                else:
                    # Preserve the old API's latest-only response for baseline proof.
                    removals = {"nodes": events[-1:]}
                pull = {"headRefOid": self.head, "pushes": {"nodes": self.pushes}, "removals": removals}
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), ""
                )
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
            endpoint = next(arg for arg in argv if arg.startswith("repos/") or arg.split("?", 1)[0] == "user").split(
                "?", 1
            )[0]
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
                    comments.append(
                        {
                            "id": 789,
                            "body": "<!-- ci-recovery-evidence " + json.dumps(self.proof) + " -->",
                            "user": {"login": self.proof_login},
                            "author_association": self.proof_association,
                        }
                    )
                data = [comments]
            elif endpoint.endswith("/timeline"):
                data = (
                    [[{"id": 987, "event": "removed_from_merge_queue", "created_at": "2026-10-09T11:00:00Z"}]]
                    if self.removed
                    else [[]]
                )
                if self.future_commit:
                    data[0].append(
                        {"event": "committed", "sha": self.head, "committer": {"date": "2099-01-01T00:00:00Z"}}
                    )
            elif endpoint.endswith("/jobs"):
                data = [{"jobs": [{"id": job, "conclusion": "failure"} for job in self.failed_ids]}]
            elif endpoint.endswith("/runs/123"):
                data = {
                    "id": 123,
                    "status": self.status,
                    "conclusion": self.conclusion,
                    "head_sha": TESTED,
                    "event": self.event,
                    "head_branch": "gh-readonly-queue/main/pr-42-abcdef",
                    "run_attempt": self.attempt,
                    "pull_requests": self.associations
                    if self.associations is not None
                    else ([] if self.event == "merge_group" else [{"number": 42, "head": {"sha": self.head}}]),
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


def recover(setup, action, *, recovery=False):
    root, transport = setup
    if action == "run-rerun":
        return pub.publish(action, number=123, repo="unit/public", cwd=root, env={}, runner=transport)
    if action in {"keeper", "keeper-initial"}:
        client = keeper.GitHub(root, "unit/public")
        # Use the real keeper adapter and real publisher, with only the transport replaced.
        with pytest.MonkeyPatch.context() as patches:
            patches.setattr(
                keeper,
                "request_run",
                lambda request, **kwargs: pub.request_run(request, runner=transport, env={}, **kwargs),
            )
            return client.enqueue(42, transport.head, **({"recovery_attempt": True} if action == "keeper" else {}))
    return pub.publish("pr-merge", number=42, repo="unit/public", cwd=root, env={}, runner=transport, recovery=recovery)


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
    transport.removal_head = NEW_HEAD
    transport.removal_history = [
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T11:00:00Z"},
        {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T12:00:00Z"},
    ]
    transport.proof = evidence(NEW_HEAD)
    recover(setup, second)
    assert len(transport.writes) == 2
    transport.head = HEAD
    # GitHub still records the latest removal against the new head.
    transport.proof = evidence()
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, second)
    assert len(transport.writes) == 2


@pytest.mark.parametrize(
    "action,flag", [("direct", False), ("direct", True), ("keeper-initial", False), ("keeper", True)]
)
def test_old_head_after_new_head_dequeue_cannot_refund_reenqueue(setup, action, flag):
    _, transport = setup
    # Initial H1 enqueue, followed by an ejection and its one allowed recovery.
    transport.removed, transport.proof = False, None
    recover(setup, action, recovery=flag)
    assert len(transport.writes) == 1
    transport.removed, transport.proof = True, evidence()
    recover(setup, action, recovery=flag)
    assert len(transport.writes) == 2
    first = {"beforeCommit": {"oid": HEAD}, "createdAt": transport.removal_date}
    transport.head = NEW_HEAD
    transport.proof = None
    recover(setup, action, recovery=flag)
    assert len(transport.writes) == 3
    transport.removal_history = [first, {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T12:00:00Z"}]
    transport.removal_head = NEW_HEAD
    transport.removal_page_size = 1
    transport.head = HEAD
    transport.pushes = [{"afterCommit": {"oid": HEAD}, "createdAt": "2026-10-09T13:00:00Z"}]
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT: first=re-enqueue"):
        recover(setup, action, recovery=flag)
    assert len(transport.writes) == 3
    assert sum(f"--match-head-commit={HEAD}" in write for write in transport.writes) == 2


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
@pytest.mark.parametrize("removed", [False, True])
def test_spent_reenqueue_blocks_normal_enqueue_without_matching_removal(setup, action, removed):
    root, transport = setup
    pub.recovery.consume(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD, "re-enqueue", evidence())
    transport.removed, transport.removal_head, transport.proof = removed, NEW_HEAD, None
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT: first=re-enqueue"):
        recover(setup, action)
    assert transport.writes == []


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
@pytest.mark.parametrize("legacy", [True, False])
def test_normal_enqueue_checks_legacy_or_unreadable_ledger(setup, action, legacy):
    root, transport = setup
    transport.removed, transport.proof = False, None
    if legacy:
        (root / "batch_state").mkdir()
        (root / "batch_state/merge_queue_keeper.json").write_text(json.dumps({"requeued": {f"42:{HEAD}": "previous"}}))
    else:
        pub.recovery.ledger_path(root).write_text("unreadable")
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    reason = "RECOVERY_ALLOWANCE_SPENT.*legacy" if legacy else "RECOVERY_RECORD_UNAVAILABLE"
    with pytest.raises(error, match=reason):
        recover(setup, action)
    assert transport.writes == []


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
def test_earlier_removal_requires_evidence_across_pages(setup, action):
    _, transport = setup
    transport.proof = None
    transport.removal_page_size = 1
    transport.removal_history = [
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T11:00:00Z"},
        {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T12:00:00Z"},
    ]
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, action)
    assert [read["variables"].get("cursor") for read in transport.removal_reads] == [None, "1"]
    assert transport.writes == []


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
        ["git", "-C", str(root), "worktree", "add", "--detach", str(linked)],
        check=True,
        capture_output=True,
        timeout=30,
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
    comments = [
        {"id": 1, "body": "<!-- ci-recovery-evidence {bad json} -->"},
        {"id": 2, "body": '<!-- ci-recovery-evidence {"job_ids":[]} -->'},
    ]
    for comment in comments:
        comment.update(user={"login": "driver"}, author_association="MEMBER")
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        module.evidence_from_comments(comments, 42, HEAD, authenticated_login="driver")


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


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
@pytest.mark.parametrize("history", ["unbound", "keeper-revoked", "manual-dequeue", "multiple", "predates-deploy"])
def test_old_removal_allows_successive_new_heads_without_local_binding(setup, action, history):
    root, transport = setup
    transport.proof = None
    if history == "predates-deploy":
        transport.removal_date = "2020-01-01T00:00:00Z"
    if history == "multiple":
        (root / "batch_state").mkdir()
        (root / "batch_state/merge_queue_keeper.json").write_text(
            json.dumps({"drop_events": {f"42:{HEAD}": [986]}, "requeued": {}})
        )
    for head in (NEW_HEAD, "d" * 40):
        transport.head = head
        recover(setup, action)
        assert pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, head) is None
    assert len(transport.writes) == 2


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
def test_current_head_removal_requires_recovery_even_without_local_binding(setup, action):
    _, transport = setup
    transport.proof = None
    error = keeper.KeeperError if action == "keeper-initial" else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, action)
    assert transport.writes == []


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
def test_removal_read_failure_is_typed_and_never_mutates(setup, action):
    _, transport = setup
    transport.removal_failure = True
    error = keeper.KeeperError if action == "keeper-initial" else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_REMOVAL_UNKNOWN"):
        recover(setup, action)
    assert transport.writes == []


@pytest.mark.parametrize("login,association", [("outsider", "NONE"), ("outsider", "MEMBER"), ("driver", "NONE")])
def test_untrusted_recovery_comment_is_rejected(setup, login, association):
    _, transport = setup
    transport.proof_login, transport.proof_association = login, association
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, "run-rerun")
    assert transport.writes == []


@pytest.mark.parametrize("event", ["push", "schedule"])
@pytest.mark.parametrize(
    "status,conclusion", [("completed", "failure"), ("completed", "success"), ("in_progress", None)]
)
def test_non_pr_failed_runs_keep_rerun_behavior(setup, event, status, conclusion):
    root, transport = setup
    transport.event, transport.associations, transport.proof = event, [], None
    transport.status, transport.conclusion = status, conclusion
    transport.attempt = 3
    recover(setup, "run-rerun")
    assert len(transport.writes) == 1
    assert "--failed" in transport.writes[0]
    assert not pub.recovery.ledger_path(root).exists()


@pytest.mark.parametrize("association", ["OWNER", "MEMBER", "COLLABORATOR"])
def test_trusted_recovery_authors_are_accepted(setup, association):
    _, transport = setup
    transport.proof_association = association
    recover(setup, "run-rerun")
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "event,associations",
    [
        ("pull_request", []),
        ("pull_request_target", []),
        ("merge_group", []),
        ("push", [{"number": 42}, {"number": 43}]),
        ("push", "unknown"),
    ],
)
def test_ambiguous_pr_runs_still_refuse(setup, event, associations):
    _, transport = setup
    transport.event, transport.associations = event, associations
    if event == "merge_group":
        # A merge-group branch must identify its PR even without REST associations.
        original = transport.__call__

        def sender(argv, **kwargs):
            result = original(argv, **kwargs)
            if any("/runs/123?" in arg for arg in argv):
                run = json.loads(result.stdout)
                run["head_branch"] = "unknown"
                result.stdout = json.dumps(run)
            return result

        root, _ = setup
        with pytest.raises(gate.PublishBlocked, match="RECOVERY_PR_UNKNOWN"):
            pub.publish("run-rerun", number=123, repo="unit/public", cwd=root, env={}, runner=sender)
    else:
        with pytest.raises(gate.PublishBlocked, match="RECOVERY_PR_UNKNOWN"):
            recover(setup, "run-rerun")
    assert transport.writes == []


def removal_observation():
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "headRefOid": HEAD,
                    "pushes": {"nodes": []},
                    "removals": {
                        "nodes": [
                            {
                                "beforeCommit": {"oid": HEAD},
                                "createdAt": "2026-10-09T11:00:00Z",
                                "reason": None,
                            }
                        ],
                        "totalCount": 1,
                        "pageInfo": {"hasNextPage": False, "endCursor": "1"},
                    },
                }
            }
        }
    }


@pytest.mark.parametrize(
    "cause",
    [
        "graphql-errors",
        "missing-pull",
        "moved-head",
        "missing-commit",
        "bad-sha",
        "bad-date",
        "naive-date",
        "null-nodes",
        "null-pushes",
        "bad-push-date",
    ],
)
def test_unreadable_removal_data_refuses_with_typed_reason(cause):
    data = removal_observation()
    pull = data["data"]["repository"]["pullRequest"]
    event = pull["removals"]["nodes"][0]
    if cause == "graphql-errors":
        data["errors"] = [{"message": "partial response"}]
    elif cause == "missing-pull":
        data["data"]["repository"]["pullRequest"] = None
    elif cause == "moved-head":
        pull["headRefOid"] = NEW_HEAD
    elif cause == "missing-commit":
        del event["beforeCommit"]
    elif cause == "bad-sha":
        event["beforeCommit"]["oid"] = "unknown"
    elif cause == "bad-date":
        event["createdAt"] = "unknown"
    elif cause == "naive-date":
        event["createdAt"] = "2026-10-09T11:00:00"
    elif cause == "null-nodes":
        pull["removals"]["nodes"] = None
    elif cause == "null-pushes":
        pull["pushes"]["nodes"] = None
    else:
        pull["pushes"]["nodes"] = [{"afterCommit": {"oid": HEAD}, "createdAt": "unknown"}]
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_REMOVAL_UNKNOWN"):
        pub.recovery.queue_removal_at_head(data, HEAD)


@pytest.mark.parametrize(
    "pushed_head,pushed_at,expected",
    [
        (HEAD, "2026-10-09T12:00:00Z", True),
        (HEAD, "2026-10-09T10:00:00Z", True),
        (HEAD, "2026-10-09T11:00:00Z", True),
        (NEW_HEAD, "2026-10-09T12:00:00Z", True),
    ],
)
def test_push_timestamps_do_not_change_known_removal_head(pushed_head, pushed_at, expected):
    data = removal_observation()
    data["data"]["repository"]["pullRequest"]["pushes"]["nodes"] = [
        {"afterCommit": {"oid": pushed_head}, "createdAt": pushed_at},
    ]
    assert pub.recovery.queue_removal_at_head(data, HEAD) is expected


@pytest.mark.parametrize("matching_head", [HEAD, NEW_HEAD])
def test_removal_history_checks_every_event(matching_head):
    data = removal_observation()
    removals = data["data"]["repository"]["pullRequest"]["removals"]
    removals["nodes"].append({"beforeCommit": {"oid": matching_head}, "createdAt": "2026-10-09T12:00:00Z"})
    removals["nodes"][0]["beforeCommit"]["oid"] = NEW_HEAD
    removals["totalCount"] = 2
    assert pub.recovery.queue_removal_at_head(data, HEAD) is (matching_head == HEAD)


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
@pytest.mark.parametrize(
    "cause",
    [
        "missing-page-info",
        "bad-next-page",
        "repeated-cursor",
        "second-page-unreadable",
        "second-page-errors",
        "second-page-head-moved",
        "second-page-missing-commit",
        "page-cap",
    ],
)
def test_incomplete_removal_history_refuses_without_mutation(setup, action, cause):
    root, transport = setup
    transport.head, transport.proof = NEW_HEAD, None
    transport.removal_history = [
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T11:00:00Z"},
        {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T12:00:00Z"},
    ]
    transport.removal_page_size = 1

    def sender(argv, **kwargs):
        result = transport(argv, **kwargs)
        if argv[1:5] != ["api", "--method", "POST", "graphql"]:
            return result
        payload = json.loads(Path(argv[6]).read_text())
        if "timelineItems" not in payload["query"]:
            return result
        second = "cursor" in payload["variables"]
        data = json.loads(result.stdout)
        pull = data["data"]["repository"]["pullRequest"]
        removals = pull["removals"]
        info = removals["pageInfo"]
        if cause == "missing-page-info":
            del removals["pageInfo"]
        elif cause == "bad-next-page":
            info["hasNextPage"] = "false"
        elif cause == "page-cap":
            info.update(hasNextPage=True, endCursor=str(len(transport.removal_reads)))
        elif second:
            if cause == "repeated-cursor":
                info.update(hasNextPage=True, endCursor="1")
            elif cause == "second-page-unreadable":
                return subprocess.CompletedProcess(argv, 1, "", "lookup failed")
            elif cause == "second-page-errors":
                data["errors"] = [{"message": "partial response"}]
            elif cause == "second-page-head-moved":
                pull["headRefOid"] = HEAD
            elif cause == "second-page-missing-commit":
                del removals["nodes"][0]["beforeCommit"]
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")

    with pytest.MonkeyPatch.context() as patches:
        # The shared helper exercises the real publisher through each adapter.
        if action == "direct":

            def invoke():
                return pub.publish("pr-merge", number=42, repo="unit/public", cwd=root, env={}, runner=sender)

            error = gate.PublishBlocked
        else:
            client = keeper.GitHub(root, "unit/public")
            patches.setattr(
                keeper,
                "request_run",
                lambda request, **kwargs: pub.request_run(request, runner=sender, env={}, **kwargs),
            )

            def invoke():
                return client.enqueue(42, NEW_HEAD)

            error = keeper.KeeperError
        with pytest.raises(error, match="RECOVERY_REMOVAL_UNKNOWN"):
            invoke()
    assert transport.writes == []
    assert not pub.recovery.ledger_path(root).exists()
    if cause == "page-cap":
        assert len(transport.removal_reads) == 100


@pytest.mark.parametrize("action", ["direct", "keeper-initial", "keeper"])
@pytest.mark.parametrize("reason", ["failed_checks", "timeout", "FAILED_CHECKS", "TIMEOUT", "unexpected", None])
def test_different_head_push_after_null_ci_removal_requires_and_consumes_recovery(setup, action, reason):
    root, transport = setup
    transport.removal_head, transport.proof = None, None
    transport.removal_reason = reason
    transport.pushes = [{"afterCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T12:00:00Z"}]
    # A force-push to another SHA followed by a fast-forward back to HEAD
    # leaves this latest force-push event pointing at the other SHA.
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, action)
    assert transport.writes == []
    assert not pub.recovery.ledger_path(root).exists()
    transport.proof = evidence()
    recover(setup, action)
    assert len(transport.writes) == 1
    prior = pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD)
    assert prior["action"] == "re-enqueue"
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, action)
    assert len(transport.writes) == 1


@pytest.mark.parametrize(
    "pushed_head,pushed_at",
    [
        (NEW_HEAD, "2026-10-09T10:00:00Z"),
        (NEW_HEAD, "2026-10-09T11:00:00Z"),
        (None, "2026-10-09T12:00:00Z"),
        ("invalid", "2026-10-09T12:00:00Z"),
        (NEW_HEAD, "2026-10-09T12:00:00Z"),
        (HEAD, "2026-10-09T12:00:00Z"),
    ],
)
@pytest.mark.parametrize("reason", ["failed_checks", "timeout", "FAILED_CHECKS", "TIMEOUT", "unexpected", None])
def test_null_ci_removal_is_at_head_regardless_of_push(reason, pushed_head, pushed_at):
    data = removal_observation()
    pull = data["data"]["repository"]["pullRequest"]
    pull["removals"]["nodes"][0].update(beforeCommit=None, reason=reason)
    pull["pushes"]["nodes"] = [{"afterCommit": {"oid": pushed_head}, "createdAt": pushed_at}]
    assert pub.recovery.queue_removal_at_head(data, HEAD) is True


@pytest.mark.parametrize("action", ["direct", "keeper-initial", "keeper"])
@pytest.mark.parametrize("previous_head", [HEAD, NEW_HEAD])
@pytest.mark.parametrize("reason", ["failed_checks", "timeout", "FAILED_CHECKS", "TIMEOUT"])
def test_same_head_push_after_null_ci_removal_requires_and_consumes_recovery(setup, action, previous_head, reason):
    root, transport = setup
    transport.removal_head, transport.removal_reason, transport.proof = None, reason, None
    transport.pushes = [
        {
            "beforeCommit": {"oid": previous_head},
            "afterCommit": {"oid": HEAD},
            "createdAt": "2026-10-09T12:00:00Z",
        }
    ]
    error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
    with pytest.raises(error, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, action)
    assert transport.writes == []
    assert not pub.recovery.ledger_path(root).exists()
    transport.proof = evidence()
    recover(setup, action)
    assert len(transport.writes) == 1
    prior = pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD)
    assert prior["action"] == "re-enqueue"
    with pytest.raises(error, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, action)
    assert len(transport.writes) == 1


@pytest.mark.parametrize("action", ["direct", "keeper-initial", "keeper"])
@pytest.mark.parametrize("removed", [False, True])
def test_timeline_total_includes_unrelated_events(setup, action, removed):
    root, transport = setup
    transport.timeline_count = 7
    transport.removed = removed
    transport.removal_head = NEW_HEAD
    transport.proof = None
    recover(setup, action)
    assert len(transport.writes) == 1
    assert not pub.recovery.ledger_path(root).exists()


def test_timeline_count_can_change_between_complete_pages(setup):
    _, transport = setup
    transport.removal_page_size = 1
    transport.removal_history = [
        {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T11:00:00Z"},
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T12:00:00Z"},
    ]
    base_sender = transport.__call__

    def sender(argv, **kwargs):
        transport.timeline_count = 7 + len(transport.removal_reads)
        return base_sender(argv, **kwargs)

    root, _ = setup
    pub.publish("pr-merge", number=42, repo="unit/public", cwd=root, env={}, runner=sender)
    assert len(transport.removal_reads) == 2
    assert len(transport.writes) == 1


def test_empty_filtered_page_with_continuation_reads_later_removal(setup):
    root, transport = setup
    transport.removal_page_size = 1
    transport.timeline_count = 7
    transport.removal_history = [
        {"beforeCommit": {"oid": NEW_HEAD}, "createdAt": "2026-10-09T11:00:00Z"},
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T12:00:00Z"},
    ]

    def sender(argv, **kwargs):
        result = transport(argv, **kwargs)
        if argv[1:5] == ["api", "--method", "POST", "graphql"]:
            payload = json.loads(Path(argv[6]).read_text())
            if "timelineItems" in payload["query"] and "cursor" not in payload["variables"]:
                data = json.loads(result.stdout)
                data["data"]["repository"]["pullRequest"]["removals"]["nodes"] = []
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
        return result

    pub.publish("pr-merge", number=42, repo="unit/public", cwd=root, env={}, runner=sender)
    assert len(transport.removal_reads) == 2
    assert len(transport.writes) == 1
    assert pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD)


@pytest.mark.parametrize("action", ["direct", "keeper-initial", "keeper"])
@pytest.mark.parametrize("reason", ["manual", "merge_conflict", "behind", "MANUAL", "MERGE_CONFLICT", "BEHIND"])
@pytest.mark.parametrize("removed_head", [None, HEAD, NEW_HEAD])
@pytest.mark.parametrize("current_head", [HEAD, NEW_HEAD])
def test_non_ci_removal_does_not_require_failure_evidence(setup, action, reason, removed_head, current_head):
    root, transport = setup
    transport.removal_reason = reason
    transport.removal_head = removed_head
    transport.timeline_count = 7
    transport.proof = None
    transport.head = current_head
    # No force-push evidence: ordinary pushes after these removals stay usable.
    recover(setup, action)
    assert len(transport.writes) == 1
    assert not pub.recovery.ledger_path(root).exists()


@pytest.mark.parametrize("action", ["direct", "keeper-initial", "keeper"])
@pytest.mark.parametrize("proof", [True, False])
@pytest.mark.parametrize("reason", ["failed_checks", "timeout", "FAILED_CHECKS", "TIMEOUT", "unexpected", None])
def test_null_ci_removal_requires_normal_recovery_evidence(setup, action, proof, reason):
    root, transport = setup
    transport.removal_head = None
    transport.removal_reason = reason
    if proof:
        recover(setup, action)
        assert len(transport.writes) == 1
        assert pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD)
    else:
        transport.proof = None
        error = keeper.KeeperError if action.startswith("keeper") else gate.PublishBlocked
        with pytest.raises(error, match="RECOVERY_EVIDENCE_MISSING"):
            recover(setup, action)
        assert transport.writes == []


def test_manual_removal_cannot_hide_an_earlier_ci_failure(setup):
    _, transport = setup
    transport.removal_page_size = 1
    transport.removal_history = [
        {"beforeCommit": {"oid": HEAD}, "createdAt": "2026-10-09T11:00:00Z", "reason": "failed_checks"},
        {"beforeCommit": None, "createdAt": "2026-10-09T12:00:00Z", "reason": "manual"},
    ]
    transport.proof = None
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_EVIDENCE_MISSING"):
        recover(setup, "direct")
    assert transport.writes == []


def test_manual_removal_does_not_refund_spent_reenqueue(setup):
    _, transport = setup
    recover(setup, "direct")
    transport.removal_head = None
    transport.removal_reason = "manual"
    transport.proof = None
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, "direct")
    assert len(transport.writes) == 1


def test_same_head_push_never_refunds_a_spent_allowance(setup):
    _, transport = setup
    recover(setup, "run-rerun")
    transport.pushes = [{"afterCommit": {"oid": HEAD}, "createdAt": "2026-10-09T12:00:00Z"}]
    with pytest.raises(gate.PublishBlocked, match="RECOVERY_ALLOWANCE_SPENT"):
        recover(setup, "direct")
    assert len(transport.writes) == 1


@pytest.mark.parametrize("action", ["direct", "keeper-initial"])
@pytest.mark.parametrize("removed", [False, True])
def test_branch_rerun_does_not_block_normal_initial_enqueue(setup, action, removed):
    root, transport = setup
    transport.event = "pull_request"
    recover(setup, "run-rerun")
    transport.removed = removed
    transport.removal_head = NEW_HEAD
    transport.proof = None
    recover(setup, action)
    assert len(transport.writes) == 2
    prior = pub.recovery.first_attempt(pub.recovery.ledger_path(root), "github.com/unit/public", 42, HEAD)
    assert prior["action"] == "run-rerun"
