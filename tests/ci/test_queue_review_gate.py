"""Coverage for scripts/ci/queue_review_gate.py, the merge-queue review requirement.

Every case builds a real temporary repository shaped like a GitHub merge-queue candidate:
two PR heads branched from the branch tip, and a squash commit per PR stacked on the one
before, with the event's ``base_sha`` naming the earlier entry's candidate (as run
42975253378 did). Only GitHub's GraphQL API is replaced, by a function returning payloads
shaped like the live ``mergeQueue`` and ``object(oid:)`` reads.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.ci import queue_review_gate as gate

_GIT_BIN = os.environ.get("AGENT_REAL_GIT", "git")  # the agent shim refuses some plumbing
REPOSITORY = "owner/repo"
ENQUEUED_AT = "2026-11-11T10:00:00Z"


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        [_GIT_BIN, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={**os.environ, **(env or {})},
    )
    assert result.returncode == 0, f"git {' '.join(args)}: {result.stderr}"
    return result.stdout.strip()


class Candidate:
    """Branch tip ``tip``; PR 1 and PR 2 heads; squashes ``s1`` (on tip) and ``s2`` (on s1)."""

    def __init__(self, root: Path) -> None:
        self.repo = root / "work"
        self.repo.mkdir()
        _git(self.repo, "init", "-q", "-b", "main")
        for key, value in (("user.name", "LU Unattributed"), ("user.email", "unattributed@local.invalid")):
            _git(self.repo, "config", key, value)
        self._index = root / "index"
        self.tip = self.commit(None, {"README.md": "base\n"}, "Initial commit")
        self.heads = {
            1: self.commit(self.tip, {"one.txt": "1\n"}, "one"),
            2: self.commit(self.tip, {"two.txt": "2\n"}, "two"),
        }
        self.s1 = self.squash(self.tip, self.heads[1], 1)
        self.s2 = self.squash(self.s1, self.heads[2], 2)

    def commit(self, parent: str | None, files: dict[str, str], message: str) -> str:
        env = {"GIT_INDEX_FILE": str(self._index)}
        if parent is None:
            _git(self.repo, "read-tree", "--empty", env=env)
        else:
            _git(self.repo, "read-tree", parent, env=env)
        for name, text in files.items():
            (self.repo / name).write_text(text, encoding="utf-8")
            blob = _git(self.repo, "hash-object", "-w", name)
            _git(self.repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{name}", env=env)
        tree = _git(self.repo, "write-tree", env=env)
        return _git(self.repo, "commit-tree", tree, *(["-p", parent] if parent else []), "-m", message)

    def squash(self, parent: str, head: str, number: int) -> str:
        tree = _git(self.repo, "merge-tree", "--write-tree", parent, head).split("\n", 1)[0]
        return _git(self.repo, "commit-tree", tree, "-p", parent, "-m", f"change {number} (#{number})")

    def event(self) -> gate.Event:
        return gate.Event(REPOSITORY, "main", self.s1, self.s2, 2)

    def entry(self, number: int, *, commit: str | None = None, head: str | None = None, position: int = 0) -> dict:
        return {
            "position": position or number,
            "enqueuedAt": ENQUEUED_AT,
            "headCommit": {"oid": commit or {1: self.s1, 2: self.s2}[number]},
            "pullRequest": {
                "number": number,
                "state": "OPEN",
                "baseRefName": "main",
                "headRefOid": head or self.heads[number],
            },
        }


class FakeGitHub:
    """Serves queue pages and current review states; records every call."""

    def __init__(self, tip: str, pages: list[list[dict]], states: dict[str, str | None], total: int | None = None):
        self.tip, self.pages, self.states = tip, pages, states
        self.total = sum(len(page) for page in pages) if total is None else total
        self.calls: list[str] = []
        self.failures = 0
        self.pushed_after_enqueue: set[str] = set()

    def __call__(self, query: str, variables: dict) -> dict:
        if self.failures:
            self.failures -= 1
            self.calls.append("error")
            return {"errors": [{"message": "Something went wrong"}]}
        if query == gate.QUEUE_QUERY:
            index = int(variables["after"] or 0)
            self.calls.append(f"page{index}")
            more = index + 1 < len(self.pages)
            return {
                "data": {
                    "repository": {
                        "ref": {"target": {"oid": self.tip}},
                        "mergeQueue": {
                            "entries": {
                                "totalCount": self.total,
                                "pageInfo": {"hasNextPage": more, "endCursor": str(index + 1) if more else None},
                                "nodes": self.pages[index],
                            }
                        },
                    }
                }
            }
        self.calls.append("status")
        repository = {}
        for key, head in variables.items():
            if key.startswith("h"):
                state = self.states.get(head)
                created = "2026-11-11T10:05:00Z" if head in self.pushed_after_enqueue else "2026-11-11T09:55:00Z"
                repository[key] = {
                    "oid": head,
                    "checkSuites": {"totalCount": 1, "nodes": [{"createdAt": created}]},
                    "status": None
                    if state is None
                    else {"context": None if state == "NO_CONTEXT" else {"state": state}},
                }
        return {"data": {"repository": repository}}


@pytest.fixture
def candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Candidate:
    built = Candidate(tmp_path)
    monkeypatch.chdir(built.repo)
    return built


def _run(candidate: Candidate, github: FakeGitHub, attempts: int = 2) -> int:
    return gate.run(candidate.event(), github, attempts=attempts, delay=0, sleep=lambda _seconds: None)


def test_approved_earlier_and_last_members_pass(candidate: Candidate, capsys: pytest.CaptureFixture[str]) -> None:
    """Positive control for the stacked shape: a gate that maps members wrongly blocks every landing."""
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"},
    )
    assert _run(candidate, github) == 0
    out = capsys.readouterr().out
    assert "#1 (queue position 1" in out and "#2 (queue position 2" in out


def test_earlier_member_without_review_fails_the_candidate(
    candidate: Candidate, capsys: pytest.CaptureFixture[str]
) -> None:
    """Defect: checking only the ref's PR (event base..head) lets an unreviewed earlier entry land."""
    github = FakeGitHub(candidate.tip, [[candidate.entry(1), candidate.entry(2)]], {candidate.heads[2]: "SUCCESS"})
    assert _run(candidate, github) == 1
    out = capsys.readouterr().out
    assert "::error::queue review gate: #1 " in out and "no fleet/cross-family-review status" in out
    assert "#2 (queue position 2" in out and "success" in out


@pytest.mark.parametrize("state", ["FAILURE", "PENDING", "ERROR", "EXPECTED", "NO_CONTEXT"])
def test_current_state_other_than_success_fails(candidate: Candidate, state: str) -> None:
    """Defect: treating any status, or a status without the review context, as an approval.

    GitHub's ``context(name:)`` is the newest state for the context, so a later failure
    after an older success arrives here as FAILURE and must block.
    """
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: state},
    )
    assert _run(candidate, github) == 1


def test_approval_on_a_head_the_candidate_did_not_include_fails(
    candidate: Candidate, capsys: pytest.CaptureFixture[str]
) -> None:
    """Defect: an approved newer head vouching for the older head the candidate was built from."""
    moved = candidate.commit(candidate.heads[1], {"one.txt": "changed\n"}, "one, amended")
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1, head=moved), candidate.entry(2)]],
        {moved: "SUCCESS", candidate.heads[2]: "SUCCESS"},
    )
    assert _run(candidate, github) == 1
    assert "#1 (queue position 1, candidate commit" in (out := capsys.readouterr().out)
    assert "tree mismatch" in out


@pytest.mark.parametrize("change", ["identical-tree", "empty-commit"])
def test_head_pushed_after_the_enqueue_fails_even_with_an_identical_tree(
    candidate: Candidate, capsys: pytest.CaptureFixture[str], change: str
) -> None:
    """Defect: tree equality standing in for head identity, so an approved later head vouches for
    the unapproved head the candidate was built from (review round 1, F1)."""
    if change == "identical-tree":
        moved = candidate.commit(candidate.heads[2], {"one.txt": "1\n"}, "copy the earlier change")
    else:
        moved = candidate.commit(candidate.heads[2], {}, "empty head move")
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2, head=moved)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "FAILURE", moved: "SUCCESS"},
    )
    github.pushed_after_enqueue.add(moved)
    assert _run(candidate, github) == 1
    assert "no pre-enqueue check-suite witness" in capsys.readouterr().out


def test_entries_on_a_later_page_are_members(candidate: Candidate) -> None:
    """Defect: reading only the first page misses members beyond it."""
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(2)], [candidate.entry(1)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"},
    )
    assert _run(candidate, github) == 0
    assert github.calls == ["page0", "page1", "status"]


def test_short_queue_read_fails_closed(candidate: Candidate) -> None:
    """Defect: trusting a page set that returned fewer entries than the reported total."""
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"},
        total=3,
    )
    assert _run(candidate, github) == 1
    assert "status" not in github.calls


def test_api_errors_fail_closed_after_bounded_retries(candidate: Candidate) -> None:
    """Defect: an API error read as an empty queue or an approval."""
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"},
    )
    github.failures = 5
    assert _run(candidate, github, attempts=3) == 1
    assert github.calls == ["error", "error", "error"]


def test_transient_error_recovers_on_a_fresh_read(candidate: Candidate) -> None:
    """Defect: one transient API error ejecting an approved candidate (no bounded retry)."""
    github = FakeGitHub(
        candidate.tip,
        [[candidate.entry(1), candidate.entry(2)]],
        {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"},
    )
    github.failures = 1
    assert _run(candidate, github) == 0


def test_chain_commit_without_a_queue_entry_fails(candidate: Candidate) -> None:
    """Defect: a candidate commit that no queue entry accounts for is silently skipped."""
    github = FakeGitHub(candidate.tip, [[candidate.entry(2)]], {candidate.heads[2]: "SUCCESS"})
    assert _run(candidate, github) == 1


def test_landed_earlier_member_is_not_required_in_the_queue(candidate: Candidate) -> None:
    """Defect: ejecting a candidate because the entry ahead merged while it was testing."""
    github = FakeGitHub(candidate.s1, [[candidate.entry(2, position=1)]], {candidate.heads[2]: "SUCCESS"})
    assert _run(candidate, github) == 0


@pytest.mark.parametrize("field", ["number", "commit"])
def test_entry_that_disagrees_with_the_chain_fails(candidate: Candidate, field: str) -> None:
    """Defect: binding a review to the wrong PR when the entry and the squash subject disagree."""
    wrong = candidate.entry(1)
    if field == "number":
        wrong["pullRequest"]["number"] = 3
    else:
        wrong["headCommit"]["oid"] = candidate.s2
    github = FakeGitHub(
        candidate.tip, [[wrong, candidate.entry(2)]], {candidate.heads[1]: "SUCCESS", candidate.heads[2]: "SUCCESS"}
    )
    assert _run(candidate, github) == 1


def test_event_whose_ref_disagrees_with_its_base_is_refused() -> None:
    """Defect: trusting a queue ref whose embedded base is not the event's base."""
    payload = {
        "action": "checks_requested",
        "repository": {"full_name": REPOSITORY},
        "merge_group": {
            "base_sha": "a" * 40,
            "head_sha": "b" * 40,
            "base_ref": "refs/heads/main",
            "head_ref": f"refs/heads/gh-readonly-queue/main/pr-7-{'c' * 40}",
        },
    }
    with pytest.raises(gate.GateError):
        gate.parse_event(payload)
    payload["merge_group"]["head_ref"] = f"refs/heads/gh-readonly-queue/main/pr-7-{'a' * 40}"
    assert gate.parse_event(payload) == gate.Event(REPOSITORY, "main", "a" * 40, "b" * 40, 7)
