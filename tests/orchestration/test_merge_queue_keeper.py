"""Behavior tests for the local merge queue keeper."""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.opsec import prepublish as gate
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.orchestration.integration_sweep import Verdict
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


class FakeGitHub:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or pr()
        self.fresh = dict(self.row)
        self.fresh["state"] = "OPEN"
        self.fresh["labels"] = []
        self.check_rows = checks(self.row["headRefOid"])
        self.queue_enabled = True
        self.remaining = 3000
        self.membership_result = True
        self.comments_rows: list[dict[str, Any]] = []
        self.actions: list[tuple[str, Any]] = []
        self.fail_removal = False
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

    def enqueue(self, number: int, head: str) -> None:
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

    def runs(self, since: str) -> list[dict[str, Any]]:
        return self.run_rows

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        return self.job_rows

    def issues(self, title: str) -> list[dict[str, Any]]:
        return self.issue_rows

    def create_issue(self, title: str, body: str) -> None:
        self.actions.append(("issue", title))
        self.issue_rows.append({"title": title})


def run(
    fake: FakeGitHub, path: Path, monkeypatch: pytest.MonkeyPatch, verdict: str = "APPROVED", *, apply: bool = True
) -> tuple[list[str], bool]:
    monkeypatch.setattr(keeper, "lookup_verdict", lambda comments, head, login: Verdict(verdict))
    monkeypatch.setattr(keeper, "_ever_approved", lambda comments, login: verdict == "APPROVED")
    return keeper.run(fake, path, apply=apply)


def mutations(fake: FakeGitHub) -> list[str]:
    return [kind for kind, _ in fake.actions if kind != "squash-read"]


def recorded(verdict: str, started: str, head: str = HEAD_A, *, review_mode: str = "cross_family") -> dict[str, Any]:
    return {
        "body": build_comment(
            sha=head,
            task_id="review",
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
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert "disarm" not in mutations(fake)
    assert "dequeue" not in mutations(fake)
    assert any(line == "#42 held: needs-CF" for line in lines)


@pytest.mark.parametrize("permission", [None, "absent", "deny", "grant"])
def test_approval_after_needs_cf_removal_obeys_requeue_permission(tmp_path: Path, permission: str | None) -> None:
    path = tmp_path / "state.json"
    queued = FakeGitHub(pr(isInMergeQueue=True))
    lines, failed = keeper.run(queued, path, apply=True)
    assert not failed and "#42 revoked: needs-CF" in lines
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1

    approved = FakeGitHub()
    approved.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00")]
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


def test_needs_cf_comment_is_retried_after_the_pull_request_leaves_the_queue(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    queued = FakeGitHub(pr(isInMergeQueue=True))

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
        keeper, "lookup_verdict", lambda *args: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
    )
    lines, failed = keeper.run(fake, tmp_path / "state.json", apply=True)
    assert not failed
    assert mutations(fake) == []
    assert "reason=CF-unknown" in lines[0]


def test_queued_red_ci_revokes_even_when_verdict_lookup_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.check_rows = checks(conclusion="failure")
    monkeypatch.setattr(
        keeper, "lookup_verdict", lambda *args: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
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
    fake.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
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
    fake.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    fake.run_rows = [
        {
            "id": 123,
            "event": "merge_group",
            "conclusion": "failure",
            "created_at": "2026-09-23T00:00:02Z",
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
    monkeypatch.setattr(keeper, "lookup_verdict", lambda comments, head, login: Verdict("APPROVED"))
    monkeypatch.setattr(keeper, "_ever_approved", lambda comments, login: True)
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
    assert "reason=requeue-spent" in lines[0]


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
    assert not failed and "reason=requeue-spent" in lines[0]
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
