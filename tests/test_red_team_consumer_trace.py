"""#10437: fixed consumer handling, with a census and behavior probes."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from lu_machinery.api.fleet_board import prs
from lu_machinery.fleet_comms import review_publication, review_publisher
from lu_machinery.fleet_comms.review_publication import DEFAULT_GATE_KIND
from lu_machinery.orchestration import integration_sweep as sweep
from lu_machinery.orchestration import merge_queue_keeper as keeper
from lu_machinery.review.record_cf_verdict import build_comment
from lu_machinery.review.record_cf_verdict import build_comment as _recovery_build_comment

# Product fixtures retained from the machinery test consumers (C-5048).

_keeper_HEAD_A = "a" * 40


def _keeper_checks(
    head: str = _keeper_HEAD_A, conclusion: str = "success", status: str = "completed"
) -> list[dict[str, Any]]:
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


def _keeper_pr(**changes: Any) -> dict[str, Any]:
    row = {
        "id": "PR_node_42",
        "number": 42,
        "title": "A change",
        "isDraft": False,
        "headRefOid": _keeper_HEAD_A,
        "baseRefName": "main",
        "isInMergeQueue": False,
        "mergeStateStatus": "CLEAN",
        "autoMergeRequest": None,
        "labels": {"totalCount": 0, "pageInfo": {"hasNextPage": False}, "nodes": []},
    }
    row.update(changes)
    return row


def _keeper_recorded(
    verdict: str, started: str, head: str = _keeper_HEAD_A, *, review_mode: str = "cross_family"
) -> dict[str, Any]:
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


def _keeper_recovery_comment(head: str = _keeper_HEAD_A) -> dict[str, Any]:
    data = {
        "pr": 42,
        "head": head,
        "run_id": 123,
        "job_ids": [456],
        "tested_sha": "c" * 40,
        "queue_group_diff": {
            "base_sha": "d" * 40,
            "head_sha": "c" * 40,
            "paths": ["lu_machinery/earlier-pr.py", "lu_machinery/this-pr.py"],
        },
        "failure_evidence": "Runner outage in linked job log",
        "unrelated_to_diff": "Runner failed before checkout",
    }
    return {
        "id": 789,
        "body": "<!-- ci-recovery-evidence " + json.dumps(data) + " -->",
        "user": {"login": "driver"},
        "author_association": "MEMBER",
    }


class _keeper_FakeGitHub:
    root = Path.cwd()
    repository = "github.com/unit/public"

    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or _keeper_pr()
        self.fresh = dict(self.row)
        self.fresh["state"] = "OPEN"
        self.fresh["labels"] = []
        self.check_rows = _keeper_checks(self.row["headRefOid"])
        self.queue_enabled = True
        self.remaining = 3000
        self.membership_result = True
        self.comments_rows: list[dict[str, Any]] = [
            _keeper_recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", self.row["headRefOid"]),
            _keeper_recovery_comment(self.row["headRefOid"]),
        ]
        self.actions: list[tuple[str, Any]] = []
        self.fail_removal = False
        self.removal_read_failure = False
        self.events: list[dict[str, Any]] = []
        self.run_rows: list[dict[str, Any]] = []
        self.job_rows: list[dict[str, Any]] = []
        self.issue_rows: list[dict[str, Any]] = []
        self.squash: bool | None = False
        self.files = ["lu_machinery/example.py"]

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

    def pr_file_rows(self, number: int) -> list[dict[str, Any]]:
        return [{"filename": path, "status": "modified"} for path in self.files]

    def pr_files(self, number: int) -> list[str]:
        return keeper.pr_file_paths(self.pr_file_rows(number))

    def checks(self, head: str) -> list[dict[str, Any]]:
        return self.check_rows

    def current(self, number: int) -> dict[str, Any]:
        return self.fresh

    def enqueue(self, number: int, head: str) -> None:
        if self.row.get("isInMergeQueue") is True:
            self.actions.append(("cleanup", (number, head)))
            return
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

    def issue_comment(self, number: int, body: str) -> None:
        self.actions.append(("issue-comment", (number, body)))

    def create_issue(self, title: str, body: str) -> int:
        self.actions.append(("issue", title))
        number = 1000 + len(self.issue_rows)
        self.issue_rows.append({"title": title, "body": body, "number": number})
        return number


def _keeper_mutations(fake: _keeper_FakeGitHub) -> list[str]:
    return [kind for kind, _ in fake.actions if kind not in {"squash-read", "cleanup"}]


def _board_mq(**kwargs: object) -> prs.MqSnapshot:
    return prs.MqSnapshot(
        usable=kwargs.pop("usable", True),
        keeper=kwargs.pop("keeper", {"queued": {}, "drops": {}}),
        since=kwargs.pop("since", {}),
    )


_board_SHA = "a" * 40


def _board_pull(
    number: int = 42,
    sha: str = _board_SHA,
    *,
    title: str = "Add a lesson",
    draft: bool = False,
    head_ref: str = "feature",
    base_ref: str = "main",
    labels: tuple[dict[str, str], ...] = (),
    body: str = "",
    merge_state: str | None = "CLEAN",
    epics: tuple[str, ...] = (),
    commit_at: str | None = None,
) -> prs.Pull:
    return prs.Pull(
        number=number,
        title=title,
        draft=draft,
        head_sha=sha,
        head_ref=head_ref,
        base_ref=base_ref,
        labels=labels,
        body=body,
        merge_state=merge_state,
        epics=epics,
        commit_at=commit_at,
    )


_board_LOGIN = "fleet"

_board_REPO = "example/repo"


def _board_check(
    name: str, sha: str = _board_SHA, *, status: str = "completed", conclusion: str = "success"
) -> dict[str, str]:
    return {
        "name": name,
        "head_sha": sha,
        "status": status,
        "conclusion": conclusion,
        "started_at": "2026-10-09T00:00:00Z",
    }


def _board_green(sha: str = _board_SHA) -> tuple[dict[str, str], ...]:
    return (_board_check("CI Gate", sha),)


def _board_comment(sha: str, *, verdict: str = "APPROVED") -> dict[str, str | dict[str, str]]:
    started = "2026-10-09T08:00:00.000001+00:00"
    marker = f"<!-- cf-verdict v1 sha={sha} task=review-one started={started} verdict={verdict} model=gpt-6.1-sol family=openai -->"
    body = f"### Cross-family review\nhead: {sha}\nReviewer family: openai\nVERDICT: {verdict}\nReviewer model: gpt-6.1-sol\nTask id: review-one\n\n<details><summary>Reviewer's reply</summary>\n\nnoted\n\n</details>\n\n{marker}"
    return {
        "id": f"review-{sha[:8]}",
        "body": body,
        "user": {"login": _board_LOGIN},
        "author_association": "OWNER",
        "created_at": "2026-10-09T08:00:00Z",
        "updated_at": "2026-10-09T08:00:00Z",
    }


def _board_view(
    *pulls: prs.Pull, queued: dict[int, bool] | None = None, login: str | None = _board_LOGIN, **kwargs: object
) -> prs.GithubView:
    comments = kwargs.pop("comments", None)
    if comments is None:
        comments = {pull.number: (_board_comment(pull.head_sha),) for pull in pulls}
    checks = kwargs.pop("checks", None)
    if checks is None:
        checks = {pull.head_sha: _board_green(pull.head_sha) for pull in pulls}
    return prs.GithubView(
        repo=_board_REPO,
        login=login,
        default_branch=kwargs.pop("default_branch", "main"),
        pulls=pulls,
        comments=comments,
        checks=checks,
        queued={pull.number: False for pull in pulls} if queued is None else queued,
        **kwargs,
    )


def _publication_approved_evidence() -> dict[str, object]:
    return {
        "schema_version": "code-review-findings.v1",
        "overall": {
            "correctness": "correct",
            "explanation": "The review found no defects that block approval.",
            "confidence": 0.95,
        },
        "findings": [],
    }


_publication_SHA_A = "a" * 40


def _publication_sealed(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "review_id": "review_deadbeef",
        "repository": "learn-ukrainian/learn-ukrainian.github.io",
        "pr_number": 5512,
        "head_sha": _publication_SHA_A,
        "gate_kind": DEFAULT_GATE_KIND,
        "verdict": "APPROVED",
        "model": "claude-opus-5",
        "family": "anthropic",
        "harness": "claude",
    }
    base.update(overrides)
    return base


_recovery_HEAD = "a" * 40

_recovery_TESTED = "c" * 40


def _recovery_evidence(head=_recovery_HEAD):
    return {
        "pr": 42,
        "head": head,
        "run_id": 123,
        "job_ids": [456],
        "tested_sha": _recovery_TESTED,
        "queue_group_diff": {
            "base_sha": "d" * 40,
            "head_sha": _recovery_TESTED,
            "paths": ["lu_machinery/earlier-pr.py", "lu_machinery/this-pr.py"],
        },
        "failure_evidence": "Job log confirms runner checkout failure",
        "unrelated_to_diff": "Failure precedes execution of changed code",
    }


_recovery_NEW_HEAD = "b" * 40


class _recovery_Transport:
    def __init__(self):
        self.head = _recovery_HEAD
        self.proof = _recovery_evidence()
        self.approved = True
        self.attempt = 1
        self.status = "completed"
        self.conclusion = "failure"
        self.event = "merge_group"
        self.failed_ids = [456]
        self.removed = True
        self.future_commit = False
        self.removal_head = _recovery_HEAD
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
        self.queued = False
        self.files = [[{"filename": "lu_machinery/example.py"}]]
        self.compare_rows = {
            "base_commit": {"sha": "d" * 40},
            "merge_base_commit": {"sha": "d" * 40},
            "status": "ahead",
            "files": [{"filename": "lu_machinery/earlier-pr.py"}, {"filename": "lu_machinery/this-pr.py"}],
        }
        self.candidate_record = {
            "base_sha": "d" * 40,
            "head_sha": _recovery_TESTED,
            "head_ref": "refs/heads/gh-readonly-queue/main/pr-42-" + "e" * 40,
            "run_id": 123,
            "run_attempt": 1,
        }

    def __call__(self, argv, **kwargs):
        if argv[1:3] == ["pr", "view"]:
            assert "isInMergeQueue" not in argv[argv.index("--json") + 1].split(",")
            data = {
                "number": 42,
                "isDraft": False,
                "mergeStateStatus": "CLEAN",
                "headRefOid": self.head,
                "headRefName": "codex/fixture",
                "state": "OPEN",
                "isCrossRepository": False,
                "baseRefName": "main",
            }
        elif argv[1:3] == ["pr", "checks"]:
            data = []
        elif argv[1:5] == ["api", "--method", "POST", "graphql"]:
            payload = json.loads(Path(argv[6]).read_text())
            query = payload["query"]
            if query.startswith("mutation"):
                assert "enqueuePullRequest" in query
                self.writes.append(argv)
                if self.failure:
                    raise subprocess.TimeoutExpired(argv, 60)
                self.queued = True
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"enqueuePullRequest": {"mergeQueueEntry": {"position": 1}}}}), ""
                )
            if "mergeQueueEntry" in query:
                data = {
                    "number": 42,
                    "state": "OPEN",
                    "headRefOid": self.head,
                    "headRefName": "codex/fixture",
                    "isInMergeQueue": self.queued,
                    "mergeQueueEntry": {"headCommit": {"oid": _recovery_TESTED}},
                }
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"repository": {"pullRequest": data}}}), ""
                )
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
                        "pageInfo": {"hasNextPage": end < len(events), "endCursor": str(end) if nodes else None},
                    }
                else:
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
                            "id": "PR_fixture_42",
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
                    "body": _recovery_build_comment(
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
            elif endpoint.endswith("/files"):
                data = self.files
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
                    "head_sha": _recovery_TESTED,
                    "event": self.event,
                    "head_branch": "gh-readonly-queue/main/pr-42-" + "e" * 40,
                    "run_attempt": self.attempt,
                    "pull_requests": self.associations
                    if self.associations is not None
                    else []
                    if self.event == "merge_group"
                    else [{"number": 42, "head": {"sha": self.head}}],
                }
            elif endpoint.endswith("/actions/runs/123/artifacts"):
                data = {
                    "total_count": 1,
                    "artifacts": [{"name": "ci-queue-candidate", "id": 77, "expired": False, "size_in_bytes": 1024}],
                }
            elif endpoint.endswith("/actions/artifacts/77/zip"):
                with io.BytesIO() as buffer:
                    with zipfile.ZipFile(buffer, "w") as archive:
                        archive.writestr("queue-candidate.json", json.dumps(self.candidate_record))
                    kwargs["stdout"].write(buffer.getvalue())
                return subprocess.CompletedProcess(argv, 0, "", "")
            elif "/compare/" in endpoint:
                data = self.compare_rows
            elif endpoint.endswith("/pulls/42"):
                self.pull_reads += 1
                data = {
                    "state": "open",
                    "head": {"sha": _recovery_NEW_HEAD if self.moved and self.pull_reads > 1 else self.head},
                }
            elif endpoint == "user":
                data = {"login": "driver"}
            else:
                pytest.fail(f"unexpected read {endpoint}")
        else:
            self.writes.append(argv)
            if self.failure:
                raise subprocess.TimeoutExpired(argv, 60)
            if argv[1:3] == ["pr", "merge"]:
                self.queued = True
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")


# Publication and telemetry readers are included so a new reference cannot
# silently enter the approval path. These are handling labels, not endorsements.

HANDLING = {
    "lu_machinery/orchestration/merge_queue_keeper.py": "accept-as-approval",
    "lu_machinery/orchestration/integration_sweep.py": "accept-as-approval",
    "lu_machinery/orchestration/stalled_work.py": "ignore",
    "lu_machinery/publish/github.py": "accept-as-approval",
    "lu_machinery/fleet_comms/review_publisher.py": "accept-as-approval",
    "lu_machinery/api/fleet_board/prs.py": "display-label",
    "lu_machinery/fleet_comms/review_publication.py": "ignore",
    "scripts/lexicon/published_record_dispositions.py": "refuse",
    "lu_machinery/orchestration/integration_sweep.py#CI-blocker-exclusion": "ignore",
    "lu_machinery/review/record_cf_verdict.py": "accept-as-approval",
    # The lineage rule reads A's APPROVE as each seat's current verdict before an extension or carry-over.
    "lu_machinery/review/review_lineage.py": "accept-as-approval",
    "lu_machinery/fleet_comms/cli.py": "ignore",
    "lu_machinery/fleet_comms/efficiency_metrics.py": "ignore",
}


def _mentions_review_contract(tree: ast.AST) -> bool:
    names = {"DEFAULT_STATUS_CONTEXT", "lookup_verdict", "parse_marker", "MARKER_PREFIX"}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and ("cf-verdict" in node.value or "fleet/cross-family-review" in node.value)
        ):
            return True
        if (
            isinstance(node, (ast.Name, ast.Attribute))
            and (node.id if isinstance(node, ast.Name) else node.attr) in names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and any(alias.name in names for alias in node.names):
            return True
    return False


@pytest.mark.repo_wide
def test_every_marker_or_status_consumer_has_a_fixed_handling_row():
    root = Path(__file__).resolve().parents[1]
    installed = files("lu_machinery")
    ownership = json.loads(installed.joinpath("lint/rename-map.json").read_text())
    product = (
        path for path in (root / "scripts").rglob("*.py")
        if ownership.get(path.relative_to(root).as_posix()) != "machinery"
    )
    consumers = {
        "lu_machinery/" + path.relative_to(installed).as_posix()
        for path in installed.rglob("*.py")
        if _mentions_review_contract(ast.parse(path.read_text(encoding="utf-8")))
    } | {
        path.relative_to(root).as_posix() for path in product
        if _mentions_review_contract(ast.parse(path.read_text(encoding="utf-8")))
    }
    assert consumers == {path.split("#", 1)[0] for path in HANDLING}
    assert set(HANDLING.values()) == {"accept-as-approval", "display-label", "refuse", "ignore"}


def _comment(mode="red_team", *, login="fleet"):
    from tests.orchestration.test_integration_sweep import comment

    return comment(review_mode=mode, login=login)


def test_keeper_and_sweep_accept_red_team_approval(tmp_path):
    from tests.orchestration.test_integration_sweep import SHA, pr
    FakeGitHub = _keeper_FakeGitHub
    mutations = _keeper_mutations
    recorded = _keeper_recorded

    fake = FakeGitHub()
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", review_mode="red_team")]
    lines, failed = keeper.run(fake, tmp_path / "keeper.json", apply=True)
    assert failed is False and mutations(fake) == ["enqueue"]
    assert "reason=ready" in lines[0]
    verdict = sweep.lookup_verdict([_comment()], SHA, "fleet")
    assert sweep.classify_pr(pr(), verdict, queued=False, observed_at="2026-10-11T00:00:00Z").state == "ready"
    assert keeper._recorded_approval_for_head([_comment()], SHA, "fleet") is True
    assert HANDLING["lu_machinery/orchestration/merge_queue_keeper.py"] == "accept-as-approval"
    assert HANDLING["lu_machinery/orchestration/integration_sweep.py"] == "accept-as-approval"


def test_fleet_board_counts_red_team_as_ready():
    """#10452 AC-02: display the mode, and do not present it as an ordinary approval."""
    from lu_machinery.api.fleet_board import prs
    _mq = _board_mq
    _pull = _board_pull
    _view = _board_view
    from tests.orchestration.test_integration_sweep import SHA

    pull = _pull(sha=SHA)
    comment = _comment(login="fleet")
    view = _view(pull, login="fleet", comments={pull.number: (comment,)})
    cf = prs._cf(pull, view)
    ordinary = prs._cf(
        pull,
        _view(pull, login="fleet", comments={pull.number: (_comment("cross_family"),)}),
    )
    assert cf == {"verdict": "APPROVED", "at_head": True, "review_mode": "red_team"}
    assert ordinary == {"verdict": "APPROVED", "at_head": True}
    assert cf.keys() - ordinary.keys() == {"review_mode"}
    assert prs._verdict_at((comment,), "fleet") is not None
    _, ready, minutes = prs._ready_minutes(
        pull,
        ci="green",
        cf=cf,
        mq_status="not_queued",
        hold=False,
        mq=_mq(since={f"{pull.number}:{SHA}": "2026-10-11T00:00:00Z"}),
        now=datetime(2026, 10, 11, 1, tzinfo=UTC),
        threshold=30,
    )
    assert ready is True and minutes == 60
    assert HANDLING["lu_machinery/api/fleet_board/prs.py"] == "display-label"


def test_ci_blocker_exclusion_ignores_review_status():
    from tests.orchestration.test_integration_sweep import pr

    pull = pr()
    pull["statusCheckRollup"].append({"context": "fleet/cross-family-review", "state": "FAILURE"})
    assert sweep._check_blockers(pull) == []
    assert HANDLING["lu_machinery/orchestration/integration_sweep.py#CI-blocker-exclusion"] == "ignore"


def test_publication_ignores_marker_and_publisher_accepts_sealed_approval(monkeypatch):
    _approved_evidence = _publication_approved_evidence
    _sealed = _publication_sealed

    sealed = review_publication.parse_sealed_verdict_payload(
        _sealed(
            review_evidence=_approved_evidence(),
            review_mode="red_team",
            marker="invalid marker",
        )
    )
    plan = review_publication.plan_publication(sealed, current_head_sha=sealed.head_sha, mutate=True)
    assert plan.status_state == "success"
    assert "review_mode=red_team" not in plan.comment_body
    assert review_publication.DEFAULT_STATUS_CONTEXT == "fleet/cross-family-review"
    statuses = []
    monkeypatch.setattr(review_publisher, "post_pr_comment", lambda **_kwargs: "https://example.com/comment")
    monkeypatch.setattr(review_publisher, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    assert review_publisher.execute_publication(plan).status_posted is True
    assert statuses[0]["context"] == "fleet/cross-family-review"
    assert statuses[0]["state"] == "success"
    assert "review_mode" not in statuses[0]["description"]
    assert HANDLING["lu_machinery/fleet_comms/review_publication.py"] == "ignore"
    assert HANDLING["lu_machinery/fleet_comms/review_publisher.py"] == "accept-as-approval"


def test_lexicon_dispositions_refuse_red_team(tmp_path):
    from scripts.lexicon import published_record_dispositions as dispositions
    from tests.test_published_record_dispositions import native_receipt

    row, hold_digest = {"row_id": "release-fixture"}, "b" * 64
    digest = dispositions.canonical_sha256(row)
    receipt = json.dumps(native_receipt())
    for mode in ("cross_family", "red_team"):
        body = build_comment(
            sha="a" * 40,
            task_id="review-fixture",
            started="2026-10-11T00:00:00.000001+00:00",
            verdict="APPROVED",
            model="claude-opus-5-5",
            family="anthropic",
            review_mode=mode,
            reply=f"release-row-sha256: {digest}\nsuperseded-hold-row-sha256: {hold_digest}",
        )
        bindings = [
            {
                "row_sha256": digest,
                "superseded_row_sha256": hold_digest,
                "receipt_json": receipt,
                "receipt_sha256": hashlib.sha256(receipt.encode()).hexdigest(),
                "verdict_body": body,
                "verdict_sha256": hashlib.sha256(body.encode()).hexdigest(),
            }
        ]
        if mode == "red_team":
            with pytest.raises(ValueError, match="cross-family APPROVED verdict"):
                dispositions._validate_release_review(tmp_path, row, hold_digest, bindings)
        else:
            dispositions._validate_release_review(tmp_path, row, hold_digest, bindings)
    assert HANDLING["scripts/lexicon/published_record_dispositions.py"] == "refuse"


def test_recovery_accepts_red_team_approval(tmp_path, monkeypatch):
    from lu_machinery.publish import github
    Transport = _recovery_Transport

    monkeypatch.setattr(github.recovery, "ledger_path", lambda _cwd: tmp_path / "recovery.sqlite3")
    monkeypatch.setattr(
        __import__(__name__, fromlist=["_recovery_build_comment"]), "_recovery_build_comment", lambda **kwargs: build_comment(**kwargs, review_mode="red_team")
    )
    transport = Transport()
    # Exercise recovery admission only, through an entirely local transport.
    record = github._prepare_recovery(
        "run-rerun",
        {"number": 123},
        "unit/public",
        tmp_path,
        {},
        transport,
    )
    assert record[2] == transport.head
    assert transport.writes == []
    assert HANDLING["lu_machinery/publish/github.py"] == "accept-as-approval"
