"""Behavior tests for the local merge queue keeper."""

from __future__ import annotations

import fcntl
import itertools
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from scripts.opsec import prepublish as gate
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.orchestration.integration_sweep import RECEIPT_FIELD, Verdict, build_receipt, parse_marker
from scripts.publish import github as publisher
from scripts.publish import recovery
from scripts.review.record_cf_verdict import build_comment
from tests.opsec_fixtures import CATALOG, TOKEN

HEAD_A = "a" * 40
HEAD_B = "b" * 40


def pr(**changes: Any) -> dict[str, Any]:
    row = {
        "id": "PR_node_42",
        "number": 42,
        "title": "A change",
        "isDraft": False,
        "headRefOid": HEAD_A,
        "baseRefName": "main",
        "isInMergeQueue": False,
        "mergeStateStatus": "CLEAN",
        "autoMergeRequest": None,
        "labels": {"totalCount": 0, "pageInfo": {"hasNextPage": False}, "nodes": []},
    }
    row.update(changes)
    return row


def checks(head: str = HEAD_A, conclusion: str = "success", status: str = "completed") -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "head_sha": head,
            "status": status,
            "conclusion": conclusion,
            "started_at": "2026-09-23T00:00:00Z",
        }
        for name in ("CI Gate", "Analyze (python)")
    ]


@pytest.fixture(autouse=True)
def recovery_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    common = tmp_path / ".git"
    common.mkdir()
    monkeypatch.setattr(recovery, "ledger_path", lambda cwd: common / "ci-recovery.sqlite3")


@pytest.fixture(autouse=True)
def _fresh_generation_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forget the store generations this process read: test ledgers are short-lived directories."""
    from scripts.orchestration import task_record_store

    monkeypatch.setattr(task_record_store, "_GENERATION_FLOOR", {})


def recovery_comment(head: str = HEAD_A) -> dict[str, Any]:
    data = {
        "pr": 42,
        "head": head,
        "run_id": 123,
        "job_ids": [456],
        "tested_sha": "c" * 40,
        "failure_evidence": "Runner outage in linked job log",
        "unrelated_to_diff": "Runner failed before checkout",
    }
    return {
        "id": 789,
        "body": "<!-- ci-recovery-evidence " + json.dumps(data) + " -->",
        "user": {"login": "driver"},
        "author_association": "MEMBER",
    }


def write_receipts(tasks_dir: Path, rows: list[dict[str, Any]], *, repository: str, number: int) -> None:
    """Bind each genuinely recorded approval the way the recorder does (#10501)."""
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        # The recorder never binds a marker that does not parse.
        if not row.get("_receipt") or (marker := parse_marker(row["body"])) is None:
            continue
        task = marker["task"]
        record = {"task_id": task, "run_nonce": f"nonce-{task}", "status": "done"}
        record[RECEIPT_FIELD] = build_receipt(
            repository=repository,
            pr=number,
            head_sha=marker["sha"],
            task_id=task,
            run_nonce=record["run_nonce"],
            model=marker["model"],
            family=marker["family"],
            verdict=marker["verdict"],
            review_mode=marker.get("review_mode", "cross_family"),
            comment_id=row["id"],
            body=row["body"],
        )
        (tasks_dir / f"{task}.json").write_text(json.dumps(record))


class FakeGitHub:
    root = Path.cwd()
    repository = "github.com/unit/public"

    @property
    def tasks_dir(self) -> Path:
        """The review ledger, holding a receipt for every genuinely recorded approval row."""
        path = Path(self._ledger.name)
        write_receipts(path, self.comments_rows, repository=self.repository, number=self.row["number"])
        return path

    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self._ledger = tempfile.TemporaryDirectory(prefix="keeper-ledger-")
        self.row = row or pr()
        self.fresh = dict(self.row)
        self.fresh["state"] = "OPEN"
        self.fresh["labels"] = []
        self.check_rows = checks(self.row["headRefOid"])
        self.queue_enabled = True
        self.remaining = 3000
        self.membership_result = True
        self.comments_rows: list[dict[str, Any]] = [
            recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", self.row["headRefOid"]),
            recovery_comment(self.row["headRefOid"]),
        ]
        self.actions: list[tuple[str, Any]] = []
        self.fail_removal = False
        self.removal_read_failure = False
        self.events: list[dict[str, Any]] = []
        self.run_rows: list[dict[str, Any]] = []
        self.job_rows: list[dict[str, Any]] = []
        self.issue_rows: list[dict[str, Any]] = []
        self.squash: bool | None = False
        self.file_rows: list[dict[str, Any]] = [{"filename": "scripts/example.py"}]
        self.lookups: list[str] = []

    def squash_blocked(self, number: int, head: str) -> bool | None:
        self.actions.append(("squash-read", (number, head)))
        return self.squash

    def branch_names(self) -> set[str]:
        return {self.row["baseRefName"]}

    def snapshot(self, branches: set[str]) -> dict[str, Any]:
        return {
            "prs": [self.row],
            "queues": {self.row["baseRefName"]: self.queue_enabled},
            "remaining": self.remaining,
            "cost": 10,
        }

    def identity(self) -> str:
        return "driver"

    def comments(self, number: int) -> list[dict[str, Any]]:
        return list(self.comments_rows)

    def checks(self, head: str) -> list[dict[str, Any]]:
        return self.check_rows

    def current(self, number: int) -> dict[str, Any]:
        return self.fresh

    def files(self, number: int) -> list[dict[str, Any]]:
        self.lookups.append("files")
        return self.file_rows

    def enqueue(self, number: int, head: str, *, recovery_attempt: bool = False) -> None:
        # Every enqueue traverses the real publisher removal check, even when
        # the keeper has never observed a drop or set recovery_attempt.
        from tests.test_ci_recovery import Transport

        transport = Transport()
        transport.head = head
        transport.removed = bool(self.events)
        transport.removal_failure = self.removal_read_failure
        if self.events:
            transport.removal_history = [
                {
                    "beforeCommit": event.get("beforeCommit", {"oid": HEAD_A}),
                    "createdAt": event["created_at"],
                    "reason": event.get("reason"),
                }
                for event in sorted(self.events, key=lambda event: event["created_at"])
            ]

        def sender(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
            if any("/comments?" in arg for arg in argv):
                return subprocess.CompletedProcess(argv, 0, json.dumps([self.comments_rows]), "")
            return transport(argv, **kwargs)

        try:
            reservation = publisher._prepare_recovery(
                "pr-merge",
                {"number": number, "match_head": head, "recovery": recovery_attempt},
                self.repository,
                self.root,
                {},
                sender,
                queue=True,
            )
            if reservation:
                path, pr_number, sha, action, evidence = reservation
                recovery.consume(path, self.repository, pr_number, sha, action, evidence)
        except gate.PublishBlocked as exc:
            raise keeper.KeeperError(str(exc)) from exc
        self.actions.append(("enqueue", (number, head)))

    def membership(self, number: int) -> bool:
        return self.membership_result

    def dequeue(self, node_id: str) -> None:
        self.actions.append(("dequeue", node_id))
        if self.fail_removal:
            raise keeper.KeeperError("remove failed")

    def disarm(self, number: int) -> None:
        self.actions.append(("disarm", number))

    def comment(self, number: int, body: str) -> None:
        self.actions.append(("comment", body))
        self.comments_rows.append({"body": body, "user": {"login": "driver"}})

    def timeline(self, number: int) -> list[dict[str, Any]]:
        return self.events

    def created_at(self, number: int) -> str:
        return "2026-09-01T00:00:00Z"

    def runs(self, since: str) -> list[dict[str, Any]]:
        return self.run_rows

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        return self.job_rows

    def issues(self, title: str) -> list[dict[str, Any]]:
        return self.issue_rows

    def create_issue(self, title: str, body: str) -> None:
        self.actions.append(("issue", title))
        self.issue_rows.append({"title": title})


_REAL_LOOKUP_VERDICT = keeper.lookup_verdict
_REAL_EVER_APPROVED = keeper._ever_approved


def run(
    fake: FakeGitHub, path: Path, monkeypatch: pytest.MonkeyPatch, verdict: str = "APPROVED", *, apply: bool = True
) -> tuple[list[str], bool]:
    """Run the keeper; an APPROVED run resolves the fake's receipted approval through the real resolver.

    Other verdicts are stubbed: they exercise CI, hold and queue handling, not review evidence.
    """
    if verdict == "APPROVED":
        monkeypatch.setattr(keeper, "lookup_verdict", _REAL_LOOKUP_VERDICT)
        monkeypatch.setattr(keeper, "_ever_approved", _REAL_EVER_APPROVED)
    else:
        monkeypatch.setattr(keeper, "lookup_verdict", lambda comments, head, login, **_kwargs: Verdict(verdict))
        monkeypatch.setattr(keeper, "_ever_approved", lambda comments, login, evidence=None: False)
    return keeper.run(fake, path, apply=apply)


def mutations(fake: FakeGitHub) -> list[str]:
    return [kind for kind, _ in fake.actions if kind != "squash-read"]


_COMMENT_IDS = itertools.count(5000)


def recorded(
    verdict: str,
    started: str,
    head: str = HEAD_A,
    *,
    review_mode: str = "cross_family",
    task: str = "review",
    receipt: bool = True,
) -> dict[str, Any]:
    """A recorder-published marker; ``receipt`` binds an approval in the fake ledger."""
    return {
        "id": next(_COMMENT_IDS),
        "body": build_comment(
            sha=head,
            task_id=task,
            started=started,
            verdict=verdict,
            model="gpt-6.1-sol",
            family="openai",
            reply="VERDICT: " + verdict,
            review_mode=review_mode,
        ),
        "user": {"login": "driver"},
        "author_association": "MEMBER",
        "created_at": "2026-09-23T13:00:00Z",
        "updated_at": "2026-09-23T13:00:00Z",
        "_receipt": receipt and verdict in {"APPROVED", "APPROVE"},
    }


def test_prompt_bound_red_team_marker_is_accepted_by_keeper(tmp_path: Path) -> None:
    fake = FakeGitHub()
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", review_mode="red_team")]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == ["enqueue"]
    assert "reason=ready" in lines[0]


def test_red_team_marker_without_mode_is_not_accepted_by_keeper(tmp_path: Path) -> None:
    fake = FakeGitHub()
    item = recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", review_mode="red_team")
    item["body"] = item["body"].replace(" review_mode=red_team", "")
    fake.comments_rows = [item]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-unknown" in lines[0]


def _keeper_comment(fake: FakeGitHub) -> str:
    bodies = [body for kind, body in fake.actions if kind == "comment"]
    assert len(bodies) == 1
    return bodies[0]


def test_queued_with_cf_at_head_is_kept(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert mutations(fake) == []
    assert "reason=ready" in lines[0]
    assert not any("revoked" in line for line in lines)
    assert json.loads(path.read_text())["queued"]["42"] == HEAD_A


def test_queued_without_cf_at_head_is_revoked(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = []
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert mutations(fake) == ["dequeue", "comment"]
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: needs-CF" in lines
    assert "reason=needs-CF" in lines[0]
    body = _keeper_comment(fake)
    assert body == (
        "Merge queue keeper: #42 was not queued because needs-CF.\n\n"
        f"<!-- mq-keeper head={HEAD_A} reason=needs-CF -->"
    )
    state = json.loads(path.read_text())
    assert "42" not in state["queued"]
    assert state["drops"][f"42:{HEAD_A}"] == 1
    assert f"42:{HEAD_A}" not in state.get("pending_comments", {})
    assert f"42:{HEAD_A}" not in state.get("squash_revoked", {})


def test_queued_cf_only_at_old_head_is_revoked(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True, headRefOid=HEAD_B))
    fake.fresh["headRefOid"] = HEAD_B
    fake.check_rows = checks(HEAD_B)
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", head=HEAD_A)]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == ["dequeue", "comment"]
    assert "#42 revoked: needs-CF" in lines
    assert "reason=needs-CF" in lines[0]
    body = _keeper_comment(fake)
    assert f"head={HEAD_B} reason=needs-CF" in body
    assert "was not queued because needs-CF." in body


def test_armed_without_cf_stays_held(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(autoMergeRequest={"enabledAt": "2026-09-23T13:00:00Z"}))
    fake.comments_rows = []
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "disarm" not in mutations(fake)
    assert "dequeue" not in mutations(fake)
    assert any(line == "#42 held: needs-CF" for line in lines)


@pytest.mark.parametrize("permission", [None, "absent", "deny", "grant"])
def test_approval_after_needs_cf_removal_obeys_requeue_permission(tmp_path: Path, permission: str | None) -> None:
    path = tmp_path / "state.json"
    queued = FakeGitHub(pr(isInMergeQueue=True))
    queued.comments_rows = []
    lines, failed = keeper.run(queued, path, apply=True)
    assert not failed and "#42 revoked: needs-CF" in lines
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1

    approved = FakeGitHub()
    approved.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00"), recovery_comment()]
    gate = None
    if permission == "absent":
        gate = _gate(tmp_path, {})
    elif permission in {"deny", "grant"}:
        gate = _gate(tmp_path, {f"42:{HEAD_A}": {"decision": permission}})
    lines, failed = keeper.run(approved, path, apply=True, requeue_gate=gate)
    assert not failed
    if permission == "grant":
        assert ("enqueue", (42, HEAD_A)) in approved.actions
        assert f"42:{HEAD_A}" in json.loads(path.read_text())["requeued"]
        return
    assert "enqueue" not in mutations(approved)
    expected = "requeue-denied" if permission == "deny" else "requeue-pending"
    assert f"reason={expected}" in lines[0]


def test_red_ci_with_missing_cf_still_records_the_removal(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    queued = FakeGitHub(pr(isInMergeQueue=True))
    queued.comments_rows = []
    queued.check_rows = checks(conclusion="failure")
    lines, failed = keeper.run(queued, path, apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in queued.actions
    assert "#42 revoked: CI-red-CI Gate" in lines
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1

    approved = FakeGitHub()
    approved.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    lines, failed = keeper.run(approved, path, apply=True)
    assert not failed
    assert "enqueue" not in mutations(approved)
    assert "reason=requeue-pending" in lines[0]


def test_needs_cf_comment_is_retried_after_the_pull_request_leaves_the_queue(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    queued = FakeGitHub(pr(isInMergeQueue=True))
    queued.comments_rows = []

    def fail_comment(number: int, body: str) -> None:
        raise keeper.KeeperError("comment failed")

    queued.comment = fail_comment  # type: ignore[method-assign]
    lines, failed = keeper.run(queued, path, apply=True)
    assert failed and any("FAILED" in line for line in lines)
    assert ("dequeue", "PR_node_42") in queued.actions
    state = json.loads(path.read_text())
    assert state["pending_comments"][f"42:{HEAD_A}"] == "needs-CF"
    assert state["drops"][f"42:{HEAD_A}"] == 1
    assert "42" not in state["queued"]

    again = FakeGitHub()
    again.comments_rows = []
    lines, failed = keeper.run(again, path, apply=True)
    assert not failed
    assert "enqueue" not in mutations(again)
    body = _keeper_comment(again)
    assert body == (
        "Merge queue keeper: #42 was not queued because needs-CF.\n\n"
        f"<!-- mq-keeper head={HEAD_A} reason=needs-CF -->"
    )
    saved = json.loads(path.read_text())
    assert f"42:{HEAD_A}" not in saved.get("pending_comments", {})
    assert saved["drops"][f"42:{HEAD_A}"] == 1


def test_queued_missing_cf_dry_run_reports_only(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = []
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=False)
    assert not failed
    assert mutations(fake) == []
    assert not path.exists()
    assert len(lines) == 1
    assert "reason=needs-CF" in lines[0]
    assert "queued=True" in lines[0]
    assert "revoked" not in lines[0]


def test_queued_legacy_approval_is_revoked(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [{"body": "VERDICT: APPROVE", "user": {"login": "driver"}}]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: needs-CF" in lines
    assert "reason=needs-CF" in lines[0]


def test_queued_recorded_rejection_revokes(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [
        recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00"),
        recorded("CHANGES_REQUESTED", "2026-09-23T12:00:01.000001+00:00"),
    ]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "CF-changes_requested" in lines[0]


def test_queued_recorded_approval_then_hold_revokes(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    fake.fresh["labels"] = [{"name": "hold"}]
    keeper.run(fake, tmp_path / "state.json", apply=True)
    assert ("dequeue", "PR_node_42") in fake.actions


@pytest.mark.parametrize("label", ["do-not-merge", "blocked"])
def test_approved_green_hold_label_is_not_enqueued(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str) -> None:
    labels = [{"name": label.upper()}]
    fake = FakeGitHub(pr(labels={"totalCount": 1, "pageInfo": {"hasNextPage": False}, "nodes": labels}))
    fake.fresh["labels"] = labels
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=hold" in lines[0]


@pytest.mark.parametrize("label", ["do-not-merge", "blocked"])
def test_queued_hold_label_is_revoked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.fresh["labels"] = [{"name": label.upper()}]
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: hold" in lines


def test_queued_legacy_red_ci_revokes(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [{"body": "VERDICT: APPROVE", "user": {"login": "driver"}}]
    fake.check_rows = checks(conclusion="failure")
    keeper.run(fake, tmp_path / "state.json", apply=True)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_queued_verdict_lookup_error_reports_without_revocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    monkeypatch.setattr(
        keeper, "lookup_verdict", lambda *args, **_kw: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
    )
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == []
    assert "reason=CF-unknown" in lines[0]


def test_queued_red_ci_revokes_even_when_verdict_lookup_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.check_rows = checks(conclusion="failure")
    monkeypatch.setattr(
        keeper, "lookup_verdict", lambda *args, **_kw: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
    )
    keeper.run(fake, tmp_path / "state.json", apply=True)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_queued_red_ci_wins_over_other_pending_check(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.check_rows = checks(conclusion="pending", status="in_progress")
    fake.check_rows[1].update(status="completed", conclusion="failure")
    keeper.run(fake, tmp_path / "state.json", apply=True)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_queued_approval_then_unknown_marker_revokes(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    path = tmp_path / "state.json"
    keeper.run(fake, path, apply=True)
    assert mutations(fake) == []
    fake.comments_rows[0]["updated_at"] = "2026-09-23T13:00:01Z"
    keeper.run(fake, path, apply=True)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_queued_stale_recorded_approval_is_revoked(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True, headRefOid=HEAD_B))
    fake.check_rows = checks(HEAD_B)
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: needs-CF" in lines
    assert "reason=needs-CF" in lines[0]


def test_enqueue_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert mutations(fake) == ["enqueue"]
    assert fake.actions[0][1] == (42, HEAD_A)
    assert "#42 enqueued" in lines


@pytest.mark.parametrize(
    "change,verdict",
    [
        ({"isDraft": True}, "APPROVED"),
        ({}, "CHANGES_REQUESTED"),
        ({}, "unknown"),
    ],
)
def test_non_ready_never_enqueued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: dict[str, Any], verdict: str
) -> None:
    fake = FakeGitHub(pr(**change))
    run(fake, tmp_path / "state.json", monkeypatch, verdict)
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize("outcome", ["failure", "pending"])
def test_ci_blockers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str) -> None:
    fake = FakeGitHub()
    fake.check_rows = checks(conclusion=outcome, status="in_progress" if outcome == "pending" else "completed")
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)


def test_base_without_queue_is_report_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.queue_enabled = False
    lines, _ = run(fake, tmp_path / "state.json", monkeypatch)
    assert mutations(fake) == []
    assert "reason=no-merge-queue" in lines[0]


def test_new_head_resets_drop_count(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(headRefOid=HEAD_B))
    fake.check_rows = checks(HEAD_B)
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {}, "drops": {f"42:{HEAD_A}": 3}}))
    run(fake, path, monkeypatch)
    assert mutations(fake) == ["enqueue"]


def test_moved_head_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.fresh["headRefOid"] = HEAD_B
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize(
    "field,value",
    [
        ("labels", [{"name": "HoLd"}]),
        ("title", "Change [NeEdS OpErAtOr Go]"),
    ],
)
def test_hold_revokes_queued(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: Any) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.fresh[field] = value
    run(fake, tmp_path / "state.json", monkeypatch)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_red_ci_revokes_queued(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.check_rows = checks(conclusion="failure")
    run(fake, tmp_path / "state.json", monkeypatch)
    assert ("dequeue", "PR_node_42") in fake.actions


def test_removal_failure_is_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.check_rows = checks(conclusion="failure")
    fake.fail_removal = True
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert failed and any("FAILED" in line for line in lines)


def test_zero_exit_without_membership_is_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.membership_result = False
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert failed and any("without queue membership" in line for line in lines)


def test_enqueue_without_membership_but_armed_auto_merge_reports_armed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeGitHub()
    fake.membership_result = False
    fake.fresh["autoMergeRequest"] = {"enabledAt": "2026-09-23T13:00:00Z"}
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert any(line == "#42 armed" for line in lines)
    assert not any("FAILED" in line for line in lines)


def test_help_epilog_documents_hold_mechanisms() -> None:
    epilog = keeper.build_parser().epilog or ""
    assert "labels" in epilog
    assert "[hold]" in epilog


def test_third_drop_stops_and_comments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {}, "drops": {f"42:{HEAD_A}": 3}}))
    run(fake, path, monkeypatch)
    assert mutations(fake) == ["comment"]
    assert "reason=third-drop" in fake.actions[0][1]


def test_comment_once_per_reason(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.check_rows = checks(conclusion="failure")
    path = tmp_path / "state.json"
    run(fake, path, monkeypatch)
    run(fake, path, monkeypatch)
    assert mutations(fake).count("comment") == 1
    fake.fresh["title"] = "Change [hold]"
    run(fake, path, monkeypatch)
    assert mutations(fake).count("comment") == 2


@pytest.mark.parametrize(
    "draft,verdict,ci",
    [
        (True, "needs-CF", "success"),
        (False, "needs-CF", "pending"),
    ],
)
def test_never_approved_no_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, draft: bool, verdict: str, ci: str
) -> None:
    fake = FakeGitHub(pr(isDraft=draft))
    fake.check_rows = checks(conclusion=ci, status="in_progress" if ci == "pending" else "completed")
    run(fake, tmp_path / "state.json", monkeypatch, verdict)
    assert "comment" not in mutations(fake)


def test_partial_graphql_row_and_budget_no_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(labels={"totalCount": 2, "pageInfo": {"hasNextPage": True}, "nodes": []}))
    fake.fresh["labels"] = None
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)
    fake = FakeGitHub()
    fake.remaining = 490
    lines, _ = run(fake, tmp_path / "low.json", monkeypatch)
    assert mutations(fake) == []
    assert any("budget stop" in line for line in lines)


def test_armed_revocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(autoMergeRequest={"enabledAt": "now"}))
    fake.check_rows = checks(conclusion="failure")
    run(fake, tmp_path / "state.json", monkeypatch)
    assert ("disarm", 42) in fake.actions


def test_flaky_issue_requires_two_distinct_prs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    path = tmp_path / "state.json"
    timestamp = keeper.datetime.now(keeper.UTC).isoformat()
    path.write_text(json.dumps({"queued": {}, "drops": {}, "failures": [{"job": "pytest", "pr": 42, "at": timestamp}]}))
    run(fake, path, monkeypatch)
    assert "issue" not in mutations(fake)
    state = json.loads(path.read_text())
    state["failures"].append({"job": "pytest", "pr": 43, "at": timestamp})
    path.write_text(json.dumps(state))
    run(fake, path, monkeypatch)
    assert mutations(fake).count("issue") == 1


def test_report_does_not_write_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    path = tmp_path / "state.json"
    run(fake, path, monkeypatch, apply=False)
    assert not path.exists()
    assert mutations(fake) == []


def test_lock_overlap_exits_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock_path = tmp_path / "batch_state/locks/merge_queue_keeper.lock"
    lock_path.parent.mkdir(parents=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        monkeypatch.setattr(keeper, "GitHub", lambda *args: pytest.fail("network used under lock overlap"))
        assert keeper.main(["--apply", "--repo-root", str(tmp_path)]) == 0


def test_missing_membership_field_never_enqueues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    row = pr()
    del row["isInMergeQueue"]
    fake = FakeGitHub(row)
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)


def test_unknown_fresh_read_leaves_queued_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.current = lambda number: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert mutations(fake) == []
    assert any("fresh-read-unknown" in line for line in lines)


def test_drop_at_old_head_does_not_block_new_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(headRefOid=HEAD_B))
    fake.check_rows = checks(HEAD_B)
    fake.events = [{"id": 987, "event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    path = tmp_path / "state.json"
    path.write_text(
        json.dumps({"queued": {"42": HEAD_A}, "drops": {f"42:{HEAD_A}": 2}, "observed": "2026-09-23T00:00:00Z"})
    )
    run(fake, path, monkeypatch)
    assert mutations(fake) == ["enqueue"]
    state = json.loads(path.read_text())
    assert state["drops"][f"42:{HEAD_A}"] == 3
    assert f"42:{HEAD_B}" not in state["drops"]


def test_recent_rejection_overrides_approval_in_keeper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.review.record_cf_verdict import build_comment

    fake = FakeGitHub()

    def comment(verdict: str, started: str) -> dict[str, Any]:
        return {
            "body": build_comment(
                sha=HEAD_A,
                task_id="review",
                started=started,
                verdict=verdict,
                model="gpt-6.1-sol",
                family="openai",
                reply="VERDICT: " + verdict,
            ),
            "user": {"login": "driver"},
            "author_association": "MEMBER",
            "created_at": "2026-09-23T13:00:00Z",
            "updated_at": "2026-09-23T13:00:00Z",
        }

    fake.comments_rows = [
        comment("APPROVED", "2026-09-23T12:00:00.000001+00:00"),
        comment("CHANGES_REQUESTED", "2026-09-23T12:00:01.000001+00:00"),
    ]
    lines, _ = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert "enqueue" not in mutations(fake)
    assert "CF-changes_requested" in lines[0]


@pytest.mark.parametrize("granted", [False, True])
def test_red_merge_group_drop_with_green_branch_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, granted: bool
) -> None:
    fake = FakeGitHub()
    fake.events = [{"id": 987, "event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    fake.run_rows = [
        {
            "id": 123,
            "event": "merge_group",
            "conclusion": "failure",
            "created_at": "2026-09-22T23:00:02Z",
            "updated_at": "2026-09-23T00:00:02Z",
            "head_branch": "gh-readonly-queue/main/pr-42-deadbeef",
            "html_url": "https://github.com/example/runs/123",
        }
    ]
    fake.job_rows = [{"name": "pytest", "conclusion": "failure"}, {"name": "ruff", "conclusion": "success"}]
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": "2026-09-23T00:00:00Z"}))
    if granted:
        lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}}))
    else:
        lines, failed = run(fake, path, monkeypatch)
    assert not failed
    comments = [body for action, body in fake.actions if action == "comment"]
    state = json.loads(path.read_text())
    assert state["drops"][f"42:{HEAD_A}"] == 1
    assert "drop_events" not in state
    assert state["failures"][0]["job"] == "pytest"
    if granted:
        assert mutations(fake) == ["enqueue"]
        assert comments == []
        assert f"42:{HEAD_A}" in state["requeued"]
    else:
        assert mutations(fake) == ["comment"]
        assert "reason=requeue-pending" in lines[0]
        assert "https://github.com/example/runs/123" in comments[0]
        assert "failing jobs: pytest" in comments[0]
        # The persisted drop still holds after the observation cycle ends.
        again = FakeGitHub()
        lines, failed = run(again, path, monkeypatch)
        assert not failed and "reason=requeue-pending" in lines[0]
        assert mutations(again) == []


def test_runs_preserves_timestamp_and_paginates_at_filtered_url(tmp_path, monkeypatch) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")
    urls = []

    def transport(argv, **kwargs):
        urls.append(argv)
        pages = [{"total_count": 2, "workflow_runs": [{"id": n}]} for n in (1, 2)]
        return subprocess.CompletedProcess(argv, 0, json.dumps(pages), "")

    monkeypatch.setattr(
        keeper, "request_run", lambda request, **kwargs: publisher.request_run(request, runner=transport, **kwargs)
    )
    assert client.runs("2026-10-10T08:12:34Z") == [{"id": 1}, {"id": 2}]
    assert "event=merge_group&created=2026-10-10T08:12:34Z.." in urls[0][4]
    assert "--paginate" in urls[0] and "--slurp" in urls[0]


def test_runs_splits_capped_window_without_losing_boundary_runs(tmp_path, monkeypatch) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")
    windows = []

    def read(request):
        window = request.fields["start"], request.fields["end"]
        windows.append(window)
        return [{"total_count": 1001 if len(windows) == 1 else 1,
                 "workflow_runs": [] if len(windows) == 1 else [{"id": len(windows)}]}]

    monkeypatch.setattr(client, "json", read)
    rows = client._runs_window(datetime(2026, 10, 10, tzinfo=UTC), datetime(2026, 10, 10, 0, 0, 3, tzinfo=UTC))
    assert [row["id"] for row in rows] == [2, 3]
    assert windows[1:] == [
        ("2026-10-10T00:00:00Z", "2026-10-10T00:00:01Z"),
        ("2026-10-10T00:00:02Z", "2026-10-10T00:00:03Z"),
    ]


@pytest.mark.parametrize("total", [2, 1001])
def test_runs_incomplete_or_unsplittable_response_is_error(tmp_path, monkeypatch, total) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")
    monkeypatch.setattr(client, "json", lambda request: [{"total_count": total, "workflow_runs": []}])
    stamp = datetime(2026, 10, 10, tzinfo=UTC)
    with pytest.raises(keeper.KeeperError, match=r"incomplete|cap exceeded"):
        client._runs_window(stamp, stamp)


def test_drop_lookup_error_is_not_reported_as_unknown(tmp_path, monkeypatch) -> None:
    fake = FakeGitHub()
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": "2026-09-23T00:00:00Z"}))

    def unavailable(since):
        raise keeper.KeeperError("merge_group run page incomplete")

    monkeypatch.setattr(fake, "runs", unavailable)
    run(fake, path, monkeypatch)
    comments = [body for action, body in fake.actions if action == "comment"]
    assert "diagnosis lookup failed: merge_group run page incomplete" in comments[0]
    assert "diagnosis unknown" not in comments[0]
    assert f"42:{HEAD_A}" in json.loads(path.read_text())["undiagnosed"]


def test_drop_without_matching_run_is_unknown() -> None:
    fake = FakeGitHub()
    fake.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    detail, jobs = keeper._drop_detail(fake, 42, HEAD_A, "2026-09-23T00:00:00Z")
    assert "failing merge_group run unknown" in detail and jobs == []


@pytest.mark.parametrize("entry_available", [False, True])
def test_drop_finds_run_created_before_last_queue_observation(monkeypatch, entry_available) -> None:
    fake = FakeGitHub()
    observed = "2026-10-10T08:00:00Z"
    entered = "2026-10-08T07:00:00Z"
    if entry_available:
        fake.events = [{"event": "added_to_merge_queue", "created_at": entered}]
    fake.events.append({"event": "removed_from_merge_queue", "created_at": "2026-10-10T08:01:00Z"})
    failed_run = {
        "id": 123, "event": "merge_group", "conclusion": "failure",
        "created_at": "2026-10-08T07:01:00Z",
        "updated_at": "2026-10-10T07:59:00Z" if entry_available else "2026-10-10T08:00:30Z",
        "head_branch": "gh-readonly-queue/main/pr-42-deadbeef",
    }
    # A run from an earlier queue cycle must not supply the diagnosis, nor
    # may a current failure associated with a different PR.
    stale = {**failed_run, "id": 124, "created_at": "2026-10-07T07:00:00Z",
             "updated_at": "2026-10-07T07:30:00Z"}
    unrelated = {**failed_run, "id": 125, "head_branch": "gh-readonly-queue/main/pr-43-deadbeef"}
    windows = []

    def runs(start):
        windows.append(start)
        return [row for row in (failed_run, stale, unrelated) if row["created_at"] >= start]

    monkeypatch.setattr(fake, "runs", runs)
    fake.job_rows = [{"name": "pytest", "conclusion": "failure"}]
    detail, jobs = keeper._drop_detail(fake, 42, HEAD_A, observed)
    assert windows == [entered if entry_available else fake.created_at(42)]
    assert "Failing merge_group: 123; failing jobs: pytest" in detail
    assert jobs == ["pytest"]


@pytest.mark.parametrize("payload,valid", [
    ({"created_at": "2026-10-01T00:00:00Z"}, True),
    ({}, False), ({"created_at": "invalid"}, False), ([], False),
])
def test_pr_creation_lower_bound_is_validated(tmp_path, monkeypatch, payload, valid) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")

    def read(request):
        assert request.verb == "read-pull" and request.fields["number"] == 42
        return payload

    monkeypatch.setattr(client, "json", read)
    if valid:
        assert client.created_at(42) == payload["created_at"]
    else:
        with pytest.raises(keeper.KeeperError, match="PR creation time"):
            client.created_at(42)


@pytest.mark.parametrize("node,expected", [
    ("tests/test_unit.py::test_case", "tests/test_unit.py::test_case"),
    ("tests/sub/test_unit.py::TestGroup::test_case[private-runtime-value]",
     "tests/sub/test_unit.py::TestGroup::test_case"),
    ("tests/test_unit.py::test_case[private runtime value - more detail]",
     "tests/test_unit.py::test_case"),
    ("tests/../private.py::test_case", ""),
    ("tests/test_unit.py::test_case private-runtime-value", ""),
    ("tests/test_unit.py::test_case\x1b[31m", ""),
])
def test_failed_test_log_projects_only_source_identifier(tmp_path, monkeypatch, node, expected) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")
    monkeypatch.setattr(client, "call", lambda *args: f"FAILED {node} - AssertionError: private-error-value\n")
    assert client.first_failed_test(456) == expected


def test_drop_comment_does_not_publish_failed_test_parameters(tmp_path, monkeypatch) -> None:
    fake = FakeGitHub()
    fake.run_rows = [{
        "id": 123, "event": "merge_group", "conclusion": "failure",
        "created_at": "2026-10-09T07:00:00Z", "updated_at": "2026-10-10T08:01:00Z",
        "head_branch": "gh-readonly-queue/main/pr-42-deadbeef",
    }]
    fake.job_rows = [{"id": 456, "name": "pytest", "conclusion": "failure"}]
    client = keeper.GitHub(tmp_path, "unit/public")
    private_value = "private-runtime-value"
    monkeypatch.setattr(client, "call", lambda *args:
                        f"FAILED tests/test_unit.py::test_case[{private_value}] - private-error-value\n")
    monkeypatch.setattr(fake, "first_failed_test", client.first_failed_test, raising=False)
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": "2026-10-10T08:00:00Z"}))
    lines, failed = run(fake, path, monkeypatch)
    assert not failed
    comments = [body for action, body in fake.actions if action == "comment"]
    assert len(comments) == 1
    assert "First FAILED test: tests/test_unit.py::test_case." in comments[0]
    assert "Failing merge_group: 123; failing jobs: pytest" in comments[0]
    public_and_state = "\n".join([*lines, *comments, path.read_text()])
    assert private_value not in public_and_state
    assert "private-error-value" not in public_and_state


@pytest.mark.parametrize("log_error", [False, True])
def test_drop_detail_keeps_run_and_jobs_with_optional_first_failed_test(tmp_path, monkeypatch, log_error) -> None:
    client = keeper.GitHub(tmp_path, "unit/public")
    monkeypatch.setattr(client, "timeline", lambda number: [])
    monkeypatch.setattr(client, "created_at", lambda number: "2026-10-01T00:00:00Z")
    monkeypatch.setattr(client, "runs", lambda since: [{
        "id": 123, "event": "merge_group", "conclusion": "failure",
        "head_branch": "gh-readonly-queue/main/pr-10256-deadbeef",
        "created_at": "2026-10-10T01:00:00Z", "html_url": "https://github.com/example/runs/123",
    }])
    monkeypatch.setattr(client, "jobs", lambda run: [
        {"id": 456, "name": "pytest (N)", "conclusion": "failure"},
        {"name": "CI Gate", "conclusion": "failure"},
    ])

    def call(*args):
        assert args[-3:] == ("--job", "456", "--log")
        if log_error:
            raise keeper.KeeperError("log expired")
        return "2026-10-10T01:00:00Z FAILED tests/test_lint_tmp_paths.py::test_paths - AssertionError\nFAILED tests/other.py::test_other - error"

    monkeypatch.setattr(client, "call", call)
    detail, jobs = keeper._drop_detail(client, 10256, HEAD_A, "2026-10-10T00:00:00Z")
    assert "https://github.com/example/runs/123" in detail and "pytest (N)" in detail
    assert jobs == ["CI Gate", "pytest (N)"]
    assert ("First FAILED test: tests/test_lint_tmp_paths.py::test_paths" in detail) is not log_error
    assert "other.py" not in detail and "unknown" not in detail


def test_base_changed_before_mutation_cannot_merge_directly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.fresh["baseRefName"] = "release-without-queue"
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")


# --- Queued squash text is re-read and scanned each run (#9339) ---


@pytest.mark.parametrize(
    "squash,dequeued,line",
    [(True, True, "revoked: squash-text-blocked"), (None, False, "squash text unverified"), (False, False, None)],
)
def test_queued_squash_text_is_rescanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, squash, dequeued, line
) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.squash = squash
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert ("squash-read", (42, HEAD_A)) in fake.actions and not failed
    assert (("dequeue", "PR_node_42") in fake.actions) is dequeued
    assert line is None or any(line in item for item in lines), lines


def test_squash_text_is_not_read_for_unqueued_or_stale_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.fresh["headRefOid"] = HEAD_B
    run(fake, tmp_path / "state.json", monkeypatch)
    ready = FakeGitHub()
    run(ready, tmp_path / "ready.json", monkeypatch)
    assert not any(kind == "squash-read" for kind, _ in fake.actions + ready.actions)


def _squash_reply(subject="clean (#42)", body="* clean", entry=None, head=HEAD_A):
    pull = {
        "headRefOid": head,
        "viewerMergeHeadlineText": subject,
        "viewerMergeBodyText": body,
        "mergeQueueEntry": entry,
    }
    return {"data": {"repository": {"pullRequest": pull}}}


@pytest.mark.parametrize(
    "reply,expected",
    [
        (_squash_reply(), False),
        (_squash_reply(entry={"headCommit": None}), False),
        (_squash_reply(subject="edited " + TOKEN), True),
        (_squash_reply(body="* " + TOKEN), True),
        (_squash_reply(entry={"headCommit": {"oid": HEAD_B, "message": "queued " + TOKEN}}), True),
        (_squash_reply(subject=TOKEN, head=HEAD_B), None),
        ({"errors": [{"message": "x"}], **_squash_reply(subject=TOKEN)}, None),
        ({"data": {"repository": {"pullRequest": None}}}, None),
        ([], None),
        (_squash_reply(body=None), None),
    ],
)
def test_github_squash_blocked(reply, expected, monkeypatch: pytest.MonkeyPatch) -> None:
    gh = keeper.GitHub(Path("."), "unit/public")
    requests = []
    monkeypatch.setattr(gh, "json", lambda request: requests.append(request) or reply)
    assert gh.squash_blocked(42, HEAD_A) is expected
    assert requests[0].verb == "read-squash-text" and requests[0].fields == {"repo": "unit/public", "number": 42}


def test_github_squash_blocked_is_unverified_without_a_matcher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "private_tooling", lambda: tmp_path / "absent")
    gh = keeper.GitHub(Path("."), "unit/public")
    monkeypatch.setattr(gh, "json", lambda request: _squash_reply())
    assert gh.squash_blocked(42, HEAD_A) is None


# --- Dependency-update PRs without Analyze runs (#8587, #9921) -----------------------------


def codeql_only(head: str = HEAD_A, conclusion: str = "neutral", status: str = "completed") -> list[dict[str, Any]]:
    """Check runs as GitHub reports them for a dependabot lockfile PR: CI Gate plus top-level CodeQL, no Analyze."""
    return [
        {
            "name": "CI Gate",
            "head_sha": head,
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-09-23T00:00:00Z",
            "app": {"id": 15368, "slug": "github-actions"},
        },
        {
            "name": "CodeQL",
            "head_sha": head,
            "status": status,
            "conclusion": conclusion if status == "completed" else None,
            "started_at": "2026-09-23T00:00:00Z",
            "app": {"id": keeper.CODEQL_APP_ID, "slug": "github-advanced-security"},
        },
    ]


def test_dependabot_lockfile_pr_with_neutral_codeql_and_no_analyze_is_queueable(tmp_path: Path, monkeypatch) -> None:
    """#9921: a dependabot npm bump changing only package-lock.json, CodeQL neutral, no Analyze run."""
    fake = FakeGitHub(pr(title="build(deps-dev): Bump a package"))
    fake.check_rows = codeql_only()
    fake.file_rows = [{"filename": "package-lock.json"}]

    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert not failed
    assert "reason=ready" in lines[0]
    assert mutations(fake) == ["enqueue"]


@pytest.mark.parametrize(
    "files",
    [
        [{"filename": "package-lock.json"}],
        [{"filename": "site/package.json"}, {"filename": "site/package-lock.json"}],
        [{"filename": "requirements-dev.txt"}, {"filename": ".dagger/uv.lock"}],
    ],
)
def test_lockfile_only_pr_with_passing_codeql_is_queueable(tmp_path: Path, monkeypatch, files) -> None:
    fake = FakeGitHub()
    fake.check_rows = codeql_only(conclusion="success")
    fake.file_rows = files

    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert not failed
    assert "reason=ready" in lines[0]
    assert mutations(fake) == ["enqueue"]


@pytest.mark.parametrize(
    "files",
    [
        [{"filename": ".github/workflows/ci.yml"}],  # a dependabot github-actions bump
        [{"filename": "package-lock.json"}, {"filename": "scripts/example.py"}],  # code pushed onto a bot branch
        [{"filename": "scripts/example.py"}],
        [{"filename": "package-lock.json"}, {"filename": "src/app.ts"}],
        [{"filename": "package.json", "previous_filename": "scripts/build.js"}],
        [{"filename": "pyproject.toml"}],  # not on the lockfile list
        [{"filename": "requirements.in"}],
        [],
    ],
)
def test_pr_without_analyze_and_non_lockfile_changes_still_waits(tmp_path: Path, monkeypatch, files) -> None:
    """Authorship never matters: only the changed files decide, so a dependabot title or author is no shortcut."""
    fake = FakeGitHub(pr(title="build(deps): Bump something"))
    fake.check_rows = codeql_only()
    fake.file_rows = files

    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert not failed
    assert "reason=CodeQL-pending" in lines[0]
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize("conclusion", ["failure", "action_required", "cancelled", "timed_out"])
def test_failing_codeql_blocks_a_lockfile_pr(tmp_path: Path, monkeypatch, conclusion) -> None:
    fake = FakeGitHub()
    fake.check_rows = codeql_only(conclusion=conclusion)
    fake.file_rows = [{"filename": "package-lock.json"}]

    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert not failed
    assert "reason=CI-red-CodeQL" in lines[0]
    assert "enqueue" not in mutations(fake)


def test_running_codeql_keeps_a_lockfile_pr_pending(tmp_path: Path, monkeypatch) -> None:
    fake = FakeGitHub()
    fake.check_rows = codeql_only(status="in_progress")
    fake.file_rows = [{"filename": "package-lock.json"}]

    lines, _failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert "reason=CodeQL-pending" in lines[0]
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize(
    "app",
    [
        {"id": 15368, "slug": "github-actions"},
        {"id": 1, "slug": "github-advanced-security"},
        {"slug": "github-advanced-security"},
        None,
    ],
)
def test_codeql_check_from_any_other_app_is_not_evidence(tmp_path: Path, monkeypatch, app) -> None:
    fake = FakeGitHub()
    fake.check_rows = codeql_only()
    fake.check_rows[1]["app"] = app
    fake.file_rows = [{"filename": "package-lock.json"}]

    lines, _failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert "reason=CodeQL-pending" in lines[0]
    assert fake.lookups == []
    assert "enqueue" not in mutations(fake)


def test_pr_with_analyze_runs_never_reads_files(tmp_path: Path, monkeypatch) -> None:
    fake = FakeGitHub()

    lines, _failed = run(fake, tmp_path / "state.json", monkeypatch)

    assert "reason=ready" in lines[0]
    assert fake.lookups == []


def test_file_lookup_failure_never_enqueues(tmp_path: Path, monkeypatch) -> None:
    fake = FakeGitHub()
    fake.check_rows = codeql_only()

    def broken(_number: int) -> list[dict[str, Any]]:
        raise keeper.KeeperError("PR file list incomplete")

    fake.files = broken  # type: ignore[method-assign]

    lines, _failed = run(fake, tmp_path / "state.json", monkeypatch)

    # A failed evidence read is handled like a failed check read: nothing is ready.
    assert "reason=ready" not in lines[0]
    assert "enqueue" not in mutations(fake)


def _github_files(monkeypatch, *, changed: Any, rows: list[dict[str, Any]]) -> keeper.GitHub:
    client = keeper.GitHub(Path("."), "o/r")
    reads: list[str] = []

    def fake_json(request: Any) -> Any:
        reads.append(request.verb)
        assert request.verb == "read-pull"
        return {"number": 7, "changed_files": changed}

    def fake_paged(request: Any) -> list[dict[str, Any]]:
        reads.append(request.verb)
        assert request.verb == "read-pr-files"
        return rows

    monkeypatch.setattr(client, "json", fake_json)
    monkeypatch.setattr(client, "paged", fake_paged)
    client.reads = reads  # type: ignore[attr-defined]
    return client


def test_github_files_returns_a_complete_list(monkeypatch) -> None:
    rows = [{"filename": "package-lock.json"}, {"filename": "package.json"}]
    client = _github_files(monkeypatch, changed=2, rows=rows)

    assert client.files(7) == rows
    assert client.reads == ["read-pull", "read-pr-files"]  # type: ignore[attr-defined]


@pytest.mark.parametrize("changed", [3000, 3001, 10000])
def test_github_files_fails_closed_at_the_files_api_cap(monkeypatch, changed) -> None:
    rows = [{"filename": f"lock{i}/package-lock.json"} for i in range(3000)]
    client = _github_files(monkeypatch, changed=changed, rows=rows)

    with pytest.raises(keeper.KeeperError, match="truncated"):
        client.files(7)
    assert client.reads == ["read-pull"]  # type: ignore[attr-defined]


def test_github_files_fails_closed_when_the_listing_reaches_the_cap(monkeypatch) -> None:
    rows = [{"filename": f"lock{i}/package-lock.json"} for i in range(3000)]
    client = _github_files(monkeypatch, changed=2999, rows=rows)

    with pytest.raises(keeper.KeeperError, match="incomplete"):
        client.files(7)


@pytest.mark.parametrize(("changed", "listed"), [(3, 2), (1, 2), (5, 0)])
def test_github_files_fails_closed_on_a_changed_files_mismatch(monkeypatch, changed, listed) -> None:
    rows = [{"filename": "package-lock.json"}] * listed
    client = _github_files(monkeypatch, changed=changed, rows=rows)

    with pytest.raises(keeper.KeeperError, match="incomplete"):
        client.files(7)


@pytest.mark.parametrize("changed", [None, "2", 2.0, True])
def test_github_files_fails_closed_without_a_changed_files_count(monkeypatch, changed) -> None:
    client = _github_files(monkeypatch, changed=changed, rows=[{"filename": "package-lock.json"}] * 2)

    with pytest.raises(keeper.KeeperError, match="count unknown"):
        client.files(7)


# --- Requeue gate and slow mode ---


def _gate(tmp_path: Path, decisions: dict[str, Any] | None = None, *, raw: str | None = None) -> Path:
    path = tmp_path / "requeue.json"
    if raw is not None:
        path.write_text(raw)
    elif decisions is not None:
        path.write_text(json.dumps({"version": 1, "requeue": decisions}))
    return path


def gated(
    fake: FakeGitHub, path: Path, monkeypatch: pytest.MonkeyPatch, gate: Path, *, apply: bool = True
) -> tuple[list[str], bool]:
    monkeypatch.setattr(keeper, "lookup_verdict", lambda comments, head, login, **_kw: Verdict("APPROVED"))
    monkeypatch.setattr(keeper, "_ever_approved", lambda comments, login, evidence=None: True)
    return keeper.run(fake, path, apply=apply, requeue_gate=gate)


def _dropped_state(path: Path, **extra: Any) -> None:
    path.write_text(json.dumps({"queued": {}, "drops": {f"42:{HEAD_A}": 1}, **extra}))


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("drops", [1, 2])
def test_without_gate_a_dropped_head_is_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, apply: bool, drops: int
) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path, drops={f"42:{HEAD_A}": drops})
    fake = FakeGitHub()
    lines, failed = run(fake, path, monkeypatch, apply=apply)
    assert not failed and "reason=requeue-pending" in lines[0]
    assert mutations(fake) == []


@pytest.mark.parametrize(
    "decisions,raw",
    [({}, None), (None, None), (None, "{not json"), (None, json.dumps({"version": 2, "requeue": {}}))],
)
def test_gate_holds_a_dropped_head_without_a_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, decisions: dict[str, Any] | None, raw: str | None
) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path)
    fake = FakeGitHub()
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, decisions, raw=raw))
    assert "enqueue" not in mutations(fake)
    assert "comment" not in mutations(fake)
    assert "reason=requeue-pending" in lines[0] and not failed


def test_gate_requeues_a_granted_head_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path)
    gate = _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}})
    fake = FakeGitHub()
    fake.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    gated(fake, path, monkeypatch, gate)
    assert ("enqueue", (42, HEAD_A)) in fake.actions
    state = json.loads(path.read_text())
    assert f"42:{HEAD_A}" in state["requeued"]
    # A second ejection of the same head stays out even though the grant is still on file.
    state["queued"] = {}
    state["drops"][f"42:{HEAD_A}"] = 2
    path.write_text(json.dumps(state))
    again = FakeGitHub()
    lines, _ = gated(again, path, monkeypatch, gate)
    assert "enqueue" not in mutations(again)
    assert "reason=RECOVERY_ALLOWANCE_SPENT" in lines[0]


@pytest.mark.parametrize("drops", [0, 1, 2])
@pytest.mark.parametrize("configured", [False, True])
def test_used_grant_holds_even_without_another_recorded_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drops: int, configured: bool
) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path, drops={f"42:{HEAD_A}": drops}, requeued={f"42:{HEAD_A}": "used"})
    fake = FakeGitHub()
    if configured:
        lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}}))
    else:
        lines, failed = run(fake, path, monkeypatch)
    assert not failed and "reason=RECOVERY_ALLOWANCE_SPENT" in lines[0]
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize("diagnosis", ["KeeperError", "empty-timeline"])
@pytest.mark.parametrize("granted", [False, True])
@pytest.mark.parametrize("apply", [False, True])
def test_undiagnosed_removal_holds_unchanged_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, diagnosis: str, granted: bool, apply: bool
) -> None:
    path = tmp_path / "state.json"
    since = "2026-09-23T00:00:00Z"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": since}))
    fake = FakeGitHub()
    if diagnosis == "KeeperError":

        def unavailable(number: int) -> list[dict[str, Any]]:
            raise keeper.KeeperError("timeline unavailable")

        monkeypatch.setattr(fake, "timeline", unavailable)
    gate = _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}} if granted else {})
    lines, failed = gated(fake, path, monkeypatch, gate, apply=apply)
    assert not failed and "reason=requeue-unknown" in lines[0]
    assert "enqueue" not in mutations(fake)
    if not apply:
        assert mutations(fake) == []
        assert json.loads(path.read_text())["queued"] == {"42": HEAD_A}
        return

    assert json.loads(path.read_text())["undiagnosed"][f"42:{HEAD_A}"] == since
    again = FakeGitHub()
    lines, failed = gated(again, path, monkeypatch, gate)
    assert not failed and "reason=requeue-unknown" in lines[0]
    assert "enqueue" not in mutations(again)

    # A later diagnosis uses the original observation window and restores the normal grant gate.
    diagnosed = FakeGitHub()
    diagnosed.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    lines, failed = gated(diagnosed, path, monkeypatch, gate)
    assert not failed
    assert ("enqueue" in mutations(diagnosed)) is granted
    if granted:
        assert mutations(diagnosed) == ["enqueue"]
    assert f"42:{HEAD_A}" not in json.loads(path.read_text())["undiagnosed"]


def test_undiagnosed_old_head_does_not_hold_new_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": "2026-09-23T00:00:00Z"}))
    fake = FakeGitHub(pr(headRefOid=HEAD_B))
    lines, failed = run(fake, path, monkeypatch)
    assert not failed and "reason=ready" in lines[0]
    assert mutations(fake) == ["enqueue"]


def test_gate_denial_holds_and_comments_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path)
    fake = FakeGitHub()
    lines, _ = gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "deny"}}))
    assert "enqueue" not in mutations(fake)
    assert "reason=requeue-denied" in lines[0]
    assert [kind for kind in mutations(fake)] == ["comment"]


def test_gate_grant_for_another_head_does_not_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    _dropped_state(path)
    fake = FakeGitHub()
    gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_B}": {"decision": "grant"}}))
    assert "enqueue" not in mutations(fake)


def test_gate_leaves_a_never_dropped_head_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    gated(fake, tmp_path / "state.json", monkeypatch, _gate(tmp_path, {}))
    assert ("enqueue", (42, HEAD_A)) in fake.actions


def test_gate_never_requeues_a_squash_text_revoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    gate = _gate(tmp_path, {})
    queued = FakeGitHub(pr(isInMergeQueue=True))
    queued.squash = True
    gated(queued, path, monkeypatch, gate)
    assert ("dequeue", "PR_node_42") in queued.actions
    assert f"42:{HEAD_A}" in json.loads(path.read_text())["squash_revoked"]
    for squash, enqueued in ((True, False), (None, False), (False, True)):
        fake = FakeGitHub()
        fake.squash = squash
        lines, _ = gated(fake, path, monkeypatch, gate, apply=False)
        assert ("squash-read", (42, HEAD_A)) in fake.actions
        assert ("reason=ready" in lines[0]) is enqueued, (squash, lines)


@pytest.mark.parametrize("blocker", ["hold", "squash-text-blocked"])
def test_keeper_manual_dequeue_then_fix_reenqueues_without_ci_failure_proof(tmp_path, monkeypatch, blocker):
    path = tmp_path / "state.json"
    gate_path = _gate(tmp_path, {})
    queued = FakeGitHub(pr(isInMergeQueue=True))
    if blocker == "hold":
        queued.fresh["labels"] = [{"name": "hold"}]
    else:
        queued.squash = True
    lines, failed = gated(queued, path, monkeypatch, gate_path)
    assert not failed and f"#42 revoked: {blocker}" in lines
    assert ("dequeue", "PR_node_42") in queued.actions

    fixed = FakeGitHub()
    fixed.comments_rows = [fixed.comments_rows[0]]  # Approval, no CI recovery evidence.
    fixed.events = [
        {
            "event": "removed_from_merge_queue",
            "created_at": "2026-10-09T11:00:00Z",
            "beforeCommit": None,
            "reason": "manual",
        }
    ]
    lines, failed = gated(fixed, path, monkeypatch, gate_path)
    assert not failed and "#42 enqueued" in lines
    assert ("enqueue", (42, HEAD_A)) in fixed.actions
    assert not recovery.ledger_path(fixed.root).exists()
    assert not json.loads(path.read_text()).get("requeued")


def test_gate_state_is_pruned_to_open_prs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {}, "drops": {}, "requeued": {f"7:{HEAD_A}": "x", f"42:{HEAD_A}": "y"}}))
    gated(FakeGitHub(), path, monkeypatch, _gate(tmp_path, {}))
    assert json.loads(path.read_text())["requeued"] == {f"42:{HEAD_A}": "y"}


@pytest.mark.parametrize(
    "environ,flag,expected",
    [
        ({}, False, 0),
        ({"MQ_KEEPER_MIN_INTERVAL_SECONDS": "120"}, False, 120),
        ({"MQ_KEEPER_MIN_INTERVAL_SECONDS": "soon"}, False, 300),
        ({}, True, 300),
        ({"MQ_KEEPER_MIN_INTERVAL_SECONDS": "600"}, True, 600),
    ],
)
def test_min_interval(tmp_path: Path, environ: dict[str, str], flag: bool, expected: int) -> None:
    marker = tmp_path / "slow"
    if flag:
        marker.write_text("")
    env = {**environ, "MQ_KEEPER_SLOW_FLAG": str(marker)}
    assert keeper._min_interval(env) == expected


def test_throttled_uses_the_last_observed_run(tmp_path: Path) -> None:
    from datetime import UTC, datetime, timedelta

    now = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
    path = tmp_path / "state.json"
    assert keeper._throttled(path, 300, now) is False
    for age, expected in ((60, True), (290, False), (400, False)):
        path.write_text(json.dumps({"observed": (now - timedelta(seconds=age)).isoformat()}))
        assert keeper._throttled(path, 300, now) is expected
        assert keeper._throttled(path, 0, now) is False


def test_slow_mode_skips_apply_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import UTC, datetime

    state = tmp_path / "batch_state/merge_queue_keeper.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"queued": {}, "drops": {}, "observed": datetime.now(UTC).isoformat()}))
    flag = tmp_path / "slow"
    flag.write_text("")
    monkeypatch.setenv("MQ_KEEPER_SLOW_FLAG", str(flag))
    monkeypatch.setattr(keeper, "GitHub", lambda *args: pytest.fail("network used in slow mode"))
    assert keeper.main(["--apply", "--repo-root", str(tmp_path)]) == 0


def test_keeper_timer_runs_every_minute() -> None:
    timer = Path(__file__).resolve().parents[2] / "packaging/systemd/learn-ukrainian-merge-queue-keeper.timer"
    text = timer.read_text()
    assert "OnCalendar=*:*:00" in text
    assert "AccuracySec=5s" in text


def _ejected(fake: FakeGitHub, path: Path, jobs: list[str], **state: Any) -> None:
    since = "2026-09-23T00:00:00Z"
    fake.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    fake.run_rows = [
        {
            "id": 321,
            "event": "merge_group",
            "conclusion": "failure",
            "created_at": "2026-09-23T00:00:02Z",
            "head_branch": "gh-readonly-queue/main/pr-42-deadbeef",
            "html_url": "https://github.com/example/runs/321",
        }
    ]
    fake.job_rows = [{"name": job, "conclusion": "failure"} for job in jobs]
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": since, **state}))


def _recent(job: str, pr_number: int) -> dict[str, Any]:
    return {"job": job, "pr": pr_number, "at": "2999-01-01T00:00:00+00:00"}


def test_queue_wide_failure_requeues_once_and_spends_shared_allowance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    _ejected(fake, path, ["pytest (9)", "CI Gate"], failures=[_recent("pytest (9)", 7)])
    gate_path = _gate(tmp_path, {})
    lines, failed = gated(fake, path, monkeypatch, gate_path)
    assert not failed
    assert ("enqueue", (42, HEAD_A)) in fake.actions
    assert any("requeued after a queue-wide failure" in line for line in lines)
    state = json.loads(path.read_text())
    assert state["drops"][f"42:{HEAD_A}"] == 1
    assert state["shared_requeues"][f"42:{HEAD_A}"] == 1
    assert f"42:{HEAD_A}" not in state.get("shared_pass", {})
    attempt = recovery.first_attempt(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A)
    assert attempt["action"] == "re-enqueue"
    assert attempt["comment_id"] == 789

    # A later genuine ejection cannot get a second recovery, even with a grant.
    again = FakeGitHub()
    again.events = fake.events
    again.run_rows = fake.run_rows
    again.job_rows = fake.job_rows
    gate_path = _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}})
    lines, failed = gated(again, path, monkeypatch, gate_path)
    assert not failed and "reason=RECOVERY_ALLOWANCE_SPENT" in lines[0]
    assert "enqueue" not in mutations(again)
    assert recovery.first_attempt(recovery.ledger_path(again.root), again.repository, 42, HEAD_A) == attempt


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("spent", ["run-rerun", "re-enqueue", "legacy"])
def test_queue_wide_failure_holds_a_spent_allowance(tmp_path, monkeypatch, apply, spent):
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    extra = {"requeued": {f"42:{HEAD_A}": "earlier"}} if spent == "legacy" else {}
    if spent != "legacy":
        evidence = recovery.evidence_from_comments(fake.comments_rows, 42, HEAD_A, authenticated_login="driver")
        recovery.consume(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A, spent, evidence)
    prior = recovery.first_attempt(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A)
    _ejected(fake, path, ["pytest (9)", "CI Gate"], failures=[_recent("pytest (9)", 7)], **extra)
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {}), apply=apply)
    assert not failed and "reason=RECOVERY_ALLOWANCE_SPENT" in lines[0]
    assert "enqueue" not in mutations(fake)
    assert recovery.first_attempt(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A) == prior
    if apply:
        comment = next(body for action, body in fake.actions if action == "comment")
        assert "any re-enqueue uses this head's shared recovery allowance" in comment
        assert "not counted against this head" not in comment


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("saved_pass", [False, True])
def test_queue_wide_failure_holds_without_posted_recovery_evidence(tmp_path, monkeypatch, apply, saved_pass):
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    fake.comments_rows = [fake.comments_rows[0]]
    _ejected(fake, path, ["pytest (9)", "CI Gate"], failures=[_recent("pytest (9)", 7)])
    if saved_pass:
        path.write_text(json.dumps({"queued": {}, "drops": {}, "shared_pass": {f"42:{HEAD_A}": "earlier"}}))
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {}), apply=apply)
    assert not failed and "reason=RECOVERY_EVIDENCE_MISSING" in lines[0]
    assert "enqueue" not in mutations(fake)
    assert recovery.first_attempt(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A) is None
    if apply and not saved_pass:
        assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1


def test_failure_new_to_the_window_still_counts_against_the_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    _ejected(fake, path, ["pytest (9)", "CI Gate"], failures=[_recent("pytest (3)", 7), _recent("pytest (9)", 42)])
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {}))
    assert not failed and "enqueue" not in mutations(fake)
    assert "reason=requeue-pending" in lines[0]
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1


def test_aggregate_job_alone_never_attributes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    _ejected(fake, path, ["CI Gate"], failures=[_recent("CI Gate", 7)])
    lines, _ = gated(fake, path, monkeypatch, _gate(tmp_path, {}))
    assert "enqueue" not in mutations(fake) and "reason=requeue-pending" in lines[0]


def test_every_failing_job_must_be_shared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    _ejected(fake, path, ["pytest (9)", "pytest (2)", "CI Gate"], failures=[_recent("pytest (9)", 7)])
    lines, _ = gated(fake, path, monkeypatch, _gate(tmp_path, {}))
    assert "enqueue" not in mutations(fake) and "reason=requeue-pending" in lines[0]


def test_shared_failure_requeues_are_capped_per_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    cap = keeper.SHARED_FAILURE_REQUEUE_LIMIT
    _ejected(
        fake,
        path,
        ["pytest (9)", "CI Gate"],
        failures=[_recent("pytest (9)", 7)],
        shared_requeues={f"42:{HEAD_A}": cap},
    )
    lines, _ = gated(fake, path, monkeypatch, _gate(tmp_path, {}))
    assert "enqueue" not in mutations(fake) and "reason=requeue-pending" in lines[0]
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1


def test_shared_failure_still_requires_green_head_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "state.json"
    fake = FakeGitHub()
    fake.check_rows = checks(HEAD_A, conclusion="failure")
    _ejected(fake, path, ["pytest (9)", "CI Gate"], failures=[_recent("pytest (9)", 7)])
    gated(fake, path, monkeypatch, _gate(tmp_path, {}))
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize(
    "name", ["requeued", "squash_revoked", "undiagnosed", "pending_comments", "shared_pass", "shared_requeues"]
)
def test_per_head_state_cleanup_preserves_only_open_prs(tmp_path: Path, name: str) -> None:
    fake = FakeGitHub()
    fake.queue_enabled = False
    path = tmp_path / "state.json"
    open_key, closed_key = f"42:{HEAD_A}", f"7:{HEAD_B}"
    value = 1 if name == "shared_requeues" else "needs-CF" if name == "pending_comments" else "earlier"
    path.write_text(json.dumps({"queued": {}, "drops": {}, name: {open_key: value, closed_key: value}}))

    _, failed = keeper.run(fake, path, apply=True)

    assert not failed
    assert json.loads(path.read_text())[name] == {open_key: value}


def test_shared_rerun_record_holds_keeper_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    evidence = recovery.evidence_from_comments(fake.comments_rows, 42, HEAD_A, authenticated_login="driver")
    recovery.consume(recovery.ledger_path(fake.root), fake.repository, 42, HEAD_A, "run-rerun", evidence)
    path = tmp_path / "state.json"
    _dropped_state(path)
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}}))
    assert not failed
    assert "RECOVERY_ALLOWANCE_SPENT: first=run-rerun" in lines[0]
    assert "enqueue" not in mutations(fake)


def test_shared_record_unknown_holds_keeper_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: Any) -> None:
        raise gate.PublishBlocked("RECOVERY_RECORD_UNAVAILABLE")

    monkeypatch.setattr(recovery, "first_attempt", unavailable)
    path = tmp_path / "state.json"
    _dropped_state(path)
    fake = FakeGitHub()
    lines, failed = gated(fake, path, monkeypatch, _gate(tmp_path, {f"42:{HEAD_A}": {"decision": "grant"}}))
    assert failed and "reason=requeue-unknown" in lines[0]
    assert any("FAILED: RECOVERY_RECORD_UNAVAILABLE" in line for line in lines)
    assert "enqueue" not in mutations(fake)


def test_multiple_removals_do_not_persist_obsolete_bindings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(headRefOid=HEAD_B))
    fake.events = [
        {"id": event_id, "event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}
        for event_id in (987, 988)
    ]
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "observed": "2026-09-23T00:00:00Z"}))
    run(fake, path, monkeypatch)
    state = json.loads(path.read_text())
    assert "drop_events" not in state
    assert state["drops"][f"42:{HEAD_A}"] == 1


@pytest.mark.parametrize(
    "cause",
    ["unbound", "manual-dequeue", "red-checks", "changed-verdict", "hold-label", "blocked-squash", "predates-deploy"],
)
def test_publisher_allows_new_head_after_unbound_or_revoked_removal(tmp_path, monkeypatch, cause):
    path = tmp_path / "state.json"
    old = FakeGitHub(pr(isInMergeQueue=True))
    if cause in {"red-checks", "changed-verdict", "hold-label", "blocked-squash"}:
        verdict = "APPROVED"
        if cause == "red-checks":
            old.check_rows = checks(conclusion="failure")
        elif cause == "changed-verdict":
            verdict = "CHANGES_REQUESTED"
        elif cause == "hold-label":
            old.fresh["labels"] = [{"name": "hold"}]
        else:
            old.squash = True
        run(old, path, monkeypatch, verdict=verdict)
        assert "dequeue" in mutations(old)
    elif cause == "manual-dequeue":
        old.dequeue("PR_node_42")
        assert "dequeue" in mutations(old)
    fresh = FakeGitHub(pr(headRefOid=HEAD_B))
    fresh.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", HEAD_B)]
    fresh.events = [
        {
            "event": "removed_from_merge_queue",
            "beforeCommit": {"oid": HEAD_A},
            "created_at": "2020-01-01T00:00:00Z" if cause == "predates-deploy" else "2026-09-23T00:00:01Z",
        }
    ]
    _, failed = run(fresh, path, monkeypatch)
    assert not failed
    assert "enqueue" in mutations(fresh)
    assert recovery.first_attempt(recovery.ledger_path(fresh.root), fresh.repository, 42, HEAD_B) is None


def test_publisher_requires_recovery_for_unobserved_current_head_removal(tmp_path, monkeypatch):
    fake = FakeGitHub()
    fake.events = [
        {"event": "removed_from_merge_queue", "beforeCommit": {"oid": HEAD_A}, "created_at": "2026-09-23T00:00:01Z"}
    ]
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert failed
    assert "enqueue" not in mutations(fake)
    assert any("RECOVERY_EVIDENCE_MISSING" in line for line in lines)


def test_publisher_removal_read_failure_refuses_initial_keeper_enqueue(tmp_path, monkeypatch):
    fake = FakeGitHub()
    fake.removal_read_failure = True
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert failed
    assert "enqueue" not in mutations(fake)
    assert any("RECOVERY_REMOVAL_UNKNOWN" in line for line in lines)


# --- #10501: every keeper positive path requires the recorder receipt ---


def _ledger_record(fake: FakeGitHub, name: str, record: dict[str, Any]) -> None:
    (Path(fake._ledger.name) / f"{name}.json").write_text(json.dumps(record))


def _active_review(fake: FakeGitHub, head: str = HEAD_A) -> None:
    _ledger_record(
        fake,
        "active-review",
        {"task_id": "active-review", "status": "running", "repository": "unit/public", "type": "review",
         "pinned_head": head},
    )


class FreshHook(FakeGitHub):
    """Run ``hook`` once, at the fresh pre-enqueue read."""

    def __init__(self, hook, row: dict[str, Any] | None = None) -> None:
        super().__init__(row)
        self.hook = hook

    def current(self, number: int) -> dict[str, Any]:
        if self.hook is not None:
            hook, self.hook = self.hook, None
            hook(self)
        return super().current(number)


def test_genuine_receipted_approval_and_green_ci_enqueues(tmp_path: Path) -> None:
    fake = FakeGitHub()
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == ["enqueue"]
    assert "reason=ready" in lines[0]
    assert "#42 enqueued" in lines


def test_unreceipted_approval_is_held_and_never_enqueued(tmp_path: Path) -> None:
    fake = FakeGitHub()
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", receipt=False)]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-unreceipted" in lines[0]
    assert "#42 held: CF-unreceipted" not in lines  # Not queued: the hold is the initial reason.


def test_queued_unreceipted_head_is_revoked_like_a_missing_approval(tmp_path: Path) -> None:
    """A known unreceipted approval is no recorded approval: the queued head comes out (#10501).

    This replaces the bfd4f38931 expectation that the head stayed queued and
    uncounted: that asserted the unsafe retention the exact-head review found.
    """
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", receipt=False)]
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "enqueue" not in mutations(fake)
    assert "#42 revoked: CF-unreceipted" in lines
    state = json.loads(path.read_text())
    assert "42" not in state["queued"]
    assert state["drops"][f"42:{HEAD_A}"] == 1
    assert _keeper_comment(fake) == (
        "Merge queue keeper: #42 was not queued because CF-unreceipted.\n\n"
        f"<!-- mq-keeper head={HEAD_A} reason=CF-unreceipted -->"
    )


def test_armed_unreceipted_head_is_disarmed(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(autoMergeRequest={"enabledAt": "2026-09-23T13:00:00Z"}))
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", receipt=False)]
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert ("disarm", 42) in fake.actions
    assert "dequeue" not in mutations(fake) and "enqueue" not in mutations(fake)
    assert "#42 revoked: CF-unreceipted" in lines


class FixedLedger(FakeGitHub):
    """Bind the genuine receipt once, then leave the ledger as the test arranges it."""

    def __init__(self, row: dict[str, Any] | None = None) -> None:
        super().__init__(row)
        self.ledger = FakeGitHub.tasks_dir.fget(self)

    @property
    def tasks_dir(self) -> Path:
        return self.ledger


@pytest.mark.parametrize("failure", ["unreadable", "mid-archive", "parked"])
def test_unreadable_receipt_evidence_never_revokes_a_receipted_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """Evidence the keeper cannot read is unavailable (#10501); it is never a known unreceipted approval."""
    from scripts.orchestration import stale_task_records

    fake = FixedLedger(pr(isInMergeQueue=True))
    record = fake.ledger / "review.json"
    archive = fake.ledger / "archive"
    if failure == "unreadable":
        original = Path.read_text

        def unreadable(self, *args, **kwargs):
            if self == record:
                raise PermissionError("record unreadable")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", unreadable)
    else:
        archive.mkdir()
        staged = stale_task_records._stage(record, archive)
        if failure == "parked":
            record.write_text("{}")  # A writer took the hot name; the receipt-bearing record is parked.
            stale_task_records._unstage(staged, record, archive)
            record.unlink()
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert mutations(fake) == []
    assert "reason=CF-evidence-unavailable" in lines[0]
    assert f"42:{HEAD_A}" not in json.loads(path.read_text())["drops"]


def test_active_outside_review_blocks_the_initial_read(tmp_path: Path) -> None:
    fake = FakeGitHub()
    _active_review(fake)
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-in-flight" in lines[0]


@pytest.mark.parametrize("change", ["review-starts", "receipt-lost", "record-corrupted", "rejection-recorded"])
def test_fresh_pre_enqueue_read_rechecks_the_receipt_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    def hook(fake: FakeGitHub) -> None:
        if change == "review-starts":
            _active_review(fake)
        elif change == "receipt-lost":
            record = json.loads((Path(fake._ledger.name) / "review.json").read_text())
            record.pop(keeper_receipt_field())
            _ledger_record(fake, "review", record)
        elif change == "record-corrupted":
            (Path(fake._ledger.name) / "review.json").write_text("{")
        else:
            fake.comments_rows.append(recorded("BLOCKED", "2026-09-23T11:00:00.000001+00:00", task="reject"))

    admissions: list[str] = []
    resolve = keeper.lookup_verdict

    def spy(comments, head, login, **kwargs):
        verdict = resolve(comments, head, login, **kwargs)
        evidence = kwargs.get("evidence")
        if evidence is not None and not evidence.historical:
            admissions.append(verdict.state)
        return verdict

    monkeypatch.setattr(keeper, "lookup_verdict", spy)
    fake = FreshHook(hook)
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    expected = {
        "review-starts": "CF-in-flight",
        "receipt-lost": "CF-unreceipted",
        "record-corrupted": "CF-evidence-unavailable",
        "rejection-recorded": "BLOCKED",
    }[change]
    # The initial read was clean; the fresh pre-enqueue read saw the change.
    assert admissions == ["APPROVED", expected]
    assert "reason=ready" in lines[0]


def keeper_receipt_field() -> str:
    from scripts.orchestration.integration_sweep import RECEIPT_FIELD as field

    return field


@pytest.mark.parametrize("order", ["approval-first", "rejection-first"])
def test_future_approval_never_overrides_an_earlier_rejection(tmp_path: Path, order: str) -> None:
    approval = recorded("APPROVED", "2030-01-01T00:00:00.000001+00:00", task="approve")
    rejection = recorded("CHANGES_REQUESTED", "2026-09-23T12:00:00.000001+00:00", task="reject")
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.comments_rows = [approval, rejection] if order == "approval-first" else [rejection, approval]
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: CF-changes_requested" in lines


def test_malformed_review_record_is_unknown_and_never_enqueued(tmp_path: Path) -> None:
    original = FakeGitHub.tasks_dir.fget

    class Corrupt(FakeGitHub):
        @property
        def tasks_dir(self) -> Path:
            path = original(self)
            (path / "review.json").write_text("[]")
            return path

    fake = Corrupt()
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-unknown" in lines[0]


def test_historical_helpers_require_receipts_but_ignore_active_reviews() -> None:
    from scripts.orchestration.integration_sweep import ReviewLedger

    fake = FakeGitHub()
    genuine = recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", task="genuine")
    comment_only = recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", HEAD_B, task="comment-only", receipt=False)
    fake.comments_rows = [genuine, comment_only]
    ledger = ReviewLedger(fake.tasks_dir, fake.repository)
    _active_review(fake)
    history = ledger.evidence(42, historical=True)
    assert keeper._recorded_approval_for_head(fake.comments_rows, HEAD_A, "driver", history)
    assert not keeper._recorded_approval_for_head(fake.comments_rows, HEAD_B, "driver", history)
    assert keeper._ever_approved(fake.comments_rows, "driver", history)
    assert not keeper._ever_approved([comment_only], "driver", history)


def test_keeper_ledger_location_failure_fails_the_run(tmp_path: Path) -> None:
    gh = keeper.GitHub(tmp_path / "not-a-checkout", "unit/public")
    with pytest.raises(keeper.KeeperError, match="task ledger location unknown"):
        _ = gh.tasks_dir
    assert keeper.GitHub(tmp_path, "unit/public", tasks_dir=tmp_path / "tasks").tasks_dir == tmp_path / "tasks"


# RE-07: the keeper uses the same completed-task veto as the sweep.
def unpublished_review(fake: FakeGitHub, token: str | None, *, head=HEAD_A, archive=False, **updates) -> None:
    directory = Path(fake._ledger.name) / "archive" if archive else Path(fake._ledger.name)
    directory.mkdir(parents=True, exist_ok=True)
    record = {"task_id": "unpublished", "status": "done", "review": True,
              "repository": fake.repository, "pinned_head": head, **updates}
    (directory / "unpublished.json").write_text(json.dumps(record))
    if token is not None:
        (directory / "unpublished.result").write_text("VERDICT: " + token)


@pytest.mark.parametrize("token,state", [("REQUEST_CHANGES", "CHANGES_REQUESTED"), ("BLOCKED", "BLOCKED")])
@pytest.mark.parametrize("order", ["approval-first", "rejection-first"])
@pytest.mark.parametrize("queued", [False, True])
@pytest.mark.parametrize("archive", [False, True])
def test_keeper_unpublished_rejection_beats_later_recorded_approval(tmp_path, token, state, order, queued, archive):
    fake = FakeGitHub(pr(isInMergeQueue=queued))
    fake.comments_rows = [recorded("APPROVED", "2030-01-01T00:00:00.000001+00:00")]
    if order == "approval-first":
        _ = fake.tasks_dir
    unpublished_review(fake, token, archive=archive)
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-" + state.lower() in lines[0]
    assert ("dequeue" in mutations(fake)) == queued


@pytest.mark.parametrize("token,state", [("REQUEST_CHANGES", "CHANGES_REQUESTED"), ("BLOCKED", "BLOCKED"),
                                        (None, "unknown"), ("APPROVE\nVERDICT: BLOCKED", "unknown")])
def test_fresh_pre_enqueue_read_consults_unpublished_completed_tasks(tmp_path, monkeypatch, token, state):
    fake = FreshHook(lambda current: unpublished_review(current, token))
    admissions = []
    original = keeper.lookup_verdict

    def spy(comments, head, login, **kwargs):
        verdict = original(comments, head, login, **kwargs)
        if kwargs.get("evidence") is not None and not kwargs["evidence"].historical:
            admissions.append(verdict.state)
        return verdict

    monkeypatch.setattr(keeper, "lookup_verdict", spy)
    _, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert admissions == ["APPROVED", state]
    assert "enqueue" not in mutations(fake)


@pytest.mark.parametrize("updates", [{"head": HEAD_B}, {"repository": "unit/other"}])
def test_keeper_other_target_rejection_does_not_block_positive_control(tmp_path, updates):
    fake = FakeGitHub()
    unpublished_review(fake, "REQUEST_CHANGES", **updates)
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == ["enqueue"]
    assert "reason=ready" in lines[0]


def test_keeper_historical_positive_paths_obey_unpublished_rejections():
    from scripts.orchestration.integration_sweep import ReviewLedger

    fake = FakeGitHub()
    history = ReviewLedger(fake.tasks_dir, fake.repository).evidence(42, historical=True)
    unpublished_review(fake, "BLOCKED")
    assert not keeper._recorded_approval_for_head(fake.comments_rows, HEAD_A, "driver", history)
    assert not keeper._ever_approved(fake.comments_rows, "driver", history)


# Review findings at 2c1d222a (#10501): the run() positive path and unsettled reviews.
def test_run_helper_approval_goes_through_the_receipt_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", receipt=False)]
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-unreceipted" in lines[0]


def _unsettled_review(fake: FakeGitHub, status: str, reply: str | None) -> None:
    ledger = Path(fake._ledger.name)
    _ledger_record(
        fake,
        "unsettled-review",
        {"task_id": "unsettled-review", "status": status, "repository": "unit/public", "type": "review",
         "pinned_head": HEAD_A},
    )
    if reply is not None:
        (ledger / "unsettled-review.result").write_text(reply)


@pytest.mark.parametrize(
    "status,reply,reason",
    [
        ("running", None, "CF-in-flight"),
        ("needs_finalize", "VERDICT: APPROVE", "CF-in-flight"),
        ("needs_finalize", "VERDICT: BLOCKED", "CF-blocked"),
    ],
)
@pytest.mark.parametrize("membership", ["queued", "armed"])
def test_unsettled_outside_review_revokes_an_admitted_head(
    tmp_path: Path, status: str, reply: str | None, reason: str, membership: str
) -> None:
    row = pr(isInMergeQueue=True) if membership == "queued" else pr(autoMergeRequest={"enabledAt": "now"})
    fake = FakeGitHub(row)
    _ = fake.tasks_dir  # Bind the receipt of the earlier approval.
    _unsettled_review(fake, status, reply)
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    removal = ("dequeue", "PR_node_42") if membership == "queued" else ("disarm", 42)
    assert removal in fake.actions
    assert "enqueue" not in mutations(fake)
    assert f"#42 revoked: {reason}" in lines
    # An unsettled review is not a missing approval: the removal is not drop-counted.
    assert f"42:{HEAD_A}" not in json.loads(path.read_text())["drops"]


def test_settled_approval_after_in_flight_removal_requeues(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    _ = fake.tasks_dir
    _unsettled_review(fake, "running", None)
    path = tmp_path / "state.json"
    _lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    (Path(fake._ledger.name) / "unsettled-review.json").unlink()
    again = FakeGitHub(pr())
    again._ledger = fake._ledger
    lines, failed = keeper.run(again, path, apply=True)
    assert not failed
    assert mutations(again) == ["enqueue"]
    assert "reason=ready" in lines[0]


# Exact-head review of bfd4f38931 (#10501): the fresh read is one coherent ledger read and
# an unsettled review whose target cannot be resolved blocks admission.
@pytest.mark.parametrize("token,reason", [("REQUEST_CHANGES", "CF-changes_requested"), ("BLOCKED", "CF-blocked")])
def test_restore_during_the_fresh_read_never_enqueues_a_rejected_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, token: str, reason: str
) -> None:
    """The reviewer's probe: rejection at the first read, then a supported restore splits the fresh read."""
    from scripts.orchestration import stale_task_records

    original = Path.iterdir
    fired: list[dict[str, int]] = []

    def hook(fake: FakeGitHub) -> None:
        ledger = Path(fake._ledger.name)

        def iterdir(self):
            items = list(original(self))
            if not fired and self == ledger:
                fired.append(stale_task_records.restore_archived(ledger, ["unpublished"], apply=True)["actions"])
            return iter(items)

        monkeypatch.setattr(Path, "iterdir", iterdir)

    fake = FreshHook(hook)
    unpublished_review(fake, token, archive=True)
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert f"reason={reason}" in lines[0]
    assert fired == [{"restored": 1}]
    assert "enqueue" not in mutations(fake)
    assert (Path(fake._ledger.name) / "unpublished.json").is_file()


@pytest.mark.parametrize(
    "fields",
    [
        {"pinned_head": ""},
        {"pinned_head": "a" * 12},
        {"pinned_head": "z" * 40},
        {"pinned_head": None},
        {"repository": None},
        {"pr": "42"},
    ],
)
def test_unresolved_active_review_never_enqueues(tmp_path: Path, fields: dict[str, Any]) -> None:
    fake = FakeGitHub()
    record = {"task_id": "active-review", "status": "running", "repository": "unit/public", "type": "review",
              "pinned_head": HEAD_A, **fields}
    _ledger_record(fake, "active-review", {key: value for key, value in record.items() if value is not None})
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "enqueue" not in mutations(fake)
    assert "reason=CF-unknown" in lines[0]


def test_unresolved_active_review_removes_an_approved_queued_head_without_a_drop(tmp_path: Path) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    _ = fake.tasks_dir  # Bind the receipt of the earlier approval.
    _ledger_record(fake, "active-review", {"task_id": "active-review", "status": "running",
                                           "repository": "unit/public", "type": "review", "pinned_head": ""})
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: CF-unknown-after-approval" in lines
    assert f"42:{HEAD_A}" not in json.loads(path.read_text())["drops"]


# Exact-head review of 3972f8be (#10501): a seqlocked ledger read, and ledger evidence the keeper cannot
# read (unavailable) holds a head instead of revoking it; only a readable, stable ledger proves a receipt absent.
UNAVAILABLE = "CF-evidence-unavailable"


class FreshFixedLedger(FixedLedger):
    """A fixed ledger whose ``hook`` runs once, at the fresh pre-enqueue read."""

    hook = None

    def current(self, number: int) -> dict[str, Any]:
        if self.hook is not None:
            hook, self.hook = self.hook, None
            hook(self)
        return super().current(number)


@pytest.fixture
def isolated_locks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import delegate

    monkeypatch.setattr(delegate, "_WORKTREE_LOCK_DIR", tmp_path / "worktree-locks")


@pytest.mark.parametrize("token,reason", [("REQUEST_CHANGES", "CF-changes_requested"), ("BLOCKED", "CF-blocked")])
def test_repeated_archive_restore_during_the_fresh_read_never_enqueues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_locks: None, token: str, reason: str
) -> None:
    """The reviewer's interleaving with the public archive/restore calls: never enqueued."""
    from scripts.orchestration import stale_task_records

    fake = FreshFixedLedger()
    ledger = fake.ledger
    archive = ledger / "archive"
    archive.mkdir()
    (ledger / "review.json").rename(archive / "review.json")  # Only the rejection moves below.
    unpublished_review(fake, token, archive=True)
    original = Path.iterdir
    moves: list[dict[str, int]] = []

    def hook(_fake: FakeGitHub) -> None:
        listings: list[Path] = []
        busy: list[bool] = []

        def iterdir(self):
            if busy or self not in (ledger, archive):
                return original(self)
            busy.append(True)
            try:
                listings.append(self)
                if len(listings) == 3:
                    moves.append(stale_task_records.archive_terminal(ledger, min_age_days=0, apply=True)["actions"])
                items = list(original(self))
                if len(listings) in (1, 3):
                    moves.append(stale_task_records.restore_archived(ledger, ["unpublished"], apply=True)["actions"])
                return iter(items)
            finally:
                busy.pop()

        monkeypatch.setattr(Path, "iterdir", iterdir)

    fake.hook = hook
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert f"reason={reason}" in lines[0]
    assert moves == [{"restored": 1}, {"archived": 1}, {"restored": 1}]
    assert "enqueue" not in mutations(fake)
    assert "#42 enqueued" not in lines


def _make_unavailable(ledger: Path, failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Leave the genuine receipt-bearing record unreadable, truncated, mid-move or parked."""
    from scripts.orchestration import stale_task_records

    record = ledger / "review.json"
    archive = ledger / "archive"
    if failure == "unreadable":
        original = Path.read_text

        def unreadable(self, *args, **kwargs):
            if self == record:
                raise PermissionError("record unreadable")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", unreadable)
    elif failure == "truncated":
        record.write_text(record.read_text()[:40])
    else:
        archive.mkdir(exist_ok=True)
        staged = stale_task_records._stage(record, archive)
        if failure == "parked":
            record.write_text("{}")  # A writer took the hot name; the receipt-bearing record is parked.
            stale_task_records._unstage(staged, record, archive)
            record.unlink()


FAILURES = ["unreadable", "truncated", "staged", "parked"]


@pytest.mark.parametrize("membership", ["queued", "armed"])
@pytest.mark.parametrize("failure", FAILURES)
def test_receipt_unavailable_after_the_initial_read_holds_instead_of_revoking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str, membership: str
) -> None:
    row = pr(isInMergeQueue=True) if membership == "queued" else pr(autoMergeRequest={"enabledAt": "now"})
    fake = FreshFixedLedger(row)
    fake.hook = lambda _fake: _make_unavailable(fake.ledger, failure, monkeypatch)
    path = tmp_path / "state.json"
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert "reason=ready" in lines[0]  # The initial read saw the genuine receipt.
    assert mutations(fake) == []
    assert f"#42 held: {UNAVAILABLE}" in lines
    state = json.loads(path.read_text())
    assert f"42:{HEAD_A}" not in state["drops"]
    assert state["approved"] == {"42": HEAD_A}
    if membership == "queued":
        assert state["queued"] == {"42": HEAD_A}


@pytest.mark.parametrize("failure", FAILURES)
def test_persisted_approval_with_unavailable_evidence_all_run_is_held(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    fake = FixedLedger(pr(isInMergeQueue=True))
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "approved": {"42": HEAD_A}}))
    _make_unavailable(fake.ledger, failure, monkeypatch)
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert f"reason={UNAVAILABLE}" in lines[0]
    assert mutations(fake) == []
    assert f"#42 held: {UNAVAILABLE}" in lines
    state = json.loads(path.read_text())
    assert state["approved"] == {"42": HEAD_A} and state["queued"] == {"42": HEAD_A}
    assert f"42:{HEAD_A}" not in state["drops"]


def test_persisted_approval_whose_readable_ledger_lacks_the_receipt_is_revoked(tmp_path: Path) -> None:
    """Known invalidity still revokes: the record reads cleanly and binds no receipt for the marker."""
    fake = FixedLedger(pr(isInMergeQueue=True))
    record = json.loads((fake.ledger / "review.json").read_text())
    record.pop(RECEIPT_FIELD)
    (fake.ledger / "review.json").write_text(json.dumps(record))
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "approved": {"42": HEAD_A}}))
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: CF-unreceipted" in lines
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1


def test_receipt_lost_after_the_initial_read_is_revoked(tmp_path: Path) -> None:
    def lose(fake: FakeGitHub) -> None:
        record = json.loads((fake.ledger / "review.json").read_text())
        record.pop(RECEIPT_FIELD)
        (fake.ledger / "review.json").write_text(json.dumps(record))

    fake = FreshFixedLedger(pr(isInMergeQueue=True))
    fake.hook = lose
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
    assert "#42 revoked: CF-unreceipted" in lines


def test_unavailable_evidence_after_a_queue_drop_posts_no_pull_request_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A local ledger that cannot be read is the keeper's problem, not the pull request's: no note."""
    fake = FixedLedger(pr(isInMergeQueue=False))
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"queued": {"42": HEAD_A}, "drops": {}, "approved": {"42": HEAD_A}}))
    _make_unavailable(fake.ledger, "truncated", monkeypatch)
    lines, failed = keeper.run(fake, path, apply=True)
    assert not failed
    assert f"reason={UNAVAILABLE}" in lines[0]
    assert "enqueue" not in mutations(fake)
    assert not [body for kind, body in fake.actions if kind == "comment" and UNAVAILABLE in body]
