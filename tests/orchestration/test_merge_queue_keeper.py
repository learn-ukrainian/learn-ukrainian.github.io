"""Behavior tests for the local merge queue keeper."""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import merge_queue_keeper as keeper
from scripts.orchestration.integration_sweep import Verdict

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
    return [kind for kind, _ in fake.actions]


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


def test_unknown_fresh_read_revokes_queued(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub(pr(isInMergeQueue=True))
    fake.current = lambda number: (_ for _ in ()).throw(keeper.KeeperError("lookup failed"))
    lines, failed = run(fake, tmp_path / "state.json", monkeypatch)
    assert not failed
    assert ("dequeue", "PR_node_42") in fake.actions
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
    assert "enqueue" in mutations(fake)
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
                model="gpt-6-sol",
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


def test_queue_drop_comment_names_failing_run_and_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    run(fake, path, monkeypatch)
    comments = [body for action, body in fake.actions if action == "comment"]
    assert len(comments) == 1
    assert "https://github.com/example/runs/123" in comments[0]
    assert "failing jobs: pytest" in comments[0]
    assert json.loads(path.read_text())["drops"][f"42:{HEAD_A}"] == 1


def test_base_changed_before_mutation_cannot_merge_directly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGitHub()
    fake.fresh["baseRefName"] = "release-without-queue"
    run(fake, tmp_path / "state.json", monkeypatch)
    assert "enqueue" not in mutations(fake)
