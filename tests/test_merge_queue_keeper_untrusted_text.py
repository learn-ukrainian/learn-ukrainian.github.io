"""Untrusted CI text never escapes into public merge-queue keeper comments, markers or issues (#10600).

Workflow job and check names, failed-test identifiers and GitHub error text are
controlled by whoever can push a workflow. These tests drive the real
``keeper.run`` through the real ``GitHub.comment`` / ``GitHub.create_issue``
methods and the typed publisher; only read observations and the final ``gh``
transport are injected, and assertions inspect the exact bytes that would be
published.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import merge_queue_keeper as keeper
from scripts.publish import github as publisher
from scripts.publish import recovery
from scripts.review.record_cf_verdict import build_comment

HEAD = "a" * 40
RUN_URL = "https://github.com/unit/public/actions/runs/321"
REPRODUCER = "Analyze (@review-probe/maintainers [click](https://example.invalid/probe))"
# Everything a marker value may contain; ``<``, ``>``, ``@``, ``!`` and newlines never qualify.
MARKER_LINE = re.compile(r"<!-- mq-keeper head=[0-9a-f]{40} reason=[A-Za-z0-9 _.,;:=+/()-]{1,200} -->\Z")
CODE_SPAN = re.compile(r"`[^`\n]*`")
LOOKALIKE_AT = ("@", "＠", "﹫")


class Transport:
    """Final ``gh`` runner: records published text, answers log reads, refuses anything else."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.log = ""

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        verb = argv[1:3]
        if verb in (["pr", "comment"], ["issue", "create"]):
            body = Path(argv[argv.index("--body-file") + 1]).read_text(encoding="utf-8")
            title = next((arg.partition("=")[2] for arg in argv if arg.startswith("--title=")), "")
            self.sent.append((" ".join(verb), title, body))
            return subprocess.CompletedProcess(argv, 0, "https://github.com/unit/public/issues/1\n", "")
        if verb == ["run", "view"]:
            return subprocess.CompletedProcess(argv, 0, self.log, "")
        raise AssertionError(f"unexpected gh operation: {verb}")

    def comments(self) -> list[str]:
        return [body for verb, _, body in self.sent if verb == "pr comment"]

    def issues(self) -> list[tuple[str, str]]:
        return [(title, body) for verb, title, body in self.sent if verb == "issue create"]


def approval() -> dict[str, Any]:
    return {
        "body": build_comment(
            sha=HEAD,
            task_id="review",
            started="2026-09-23T12:00:00.000001+00:00",
            verdict="APPROVED",
            model="gpt-6.1-sol",
            family="openai",
            reply="VERDICT: APPROVED",
        ),
        "user": {"login": "driver"},
        "author_association": "MEMBER",
        "created_at": "2026-09-23T13:00:00Z",
        "updated_at": "2026-09-23T13:00:00Z",
    }


def check(name: str, status: str = "completed", conclusion: str | None = "success") -> dict[str, Any]:
    return {
        "name": name,
        "head_sha": HEAD,
        "status": status,
        "conclusion": conclusion,
        "started_at": "2026-09-23T00:00:00Z",
    }


class Subject(keeper.GitHub):
    """The real client with read observations stubbed; every publication uses the real methods."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "unit/public")
        self.row: dict[str, Any] = {
            "id": "PR_node_42",
            "number": 42,
            "title": "A change",
            "isDraft": False,
            "headRefOid": HEAD,
            "baseRefName": "main",
            "isInMergeQueue": False,
            "mergeStateStatus": "CLEAN",
            "autoMergeRequest": None,
            "labels": {"totalCount": 0, "pageInfo": {"hasNextPage": False}, "nodes": []},
        }
        self.comment_rows: list[dict[str, Any]] = [approval()]
        self.check_rows = [check("CI Gate"), check("Analyze (python)")]
        self.events: list[dict[str, Any]] = []
        self.run_rows: list[dict[str, Any]] = []
        self.job_rows: list[dict[str, Any]] = []
        self.issue_rows: list[dict[str, Any]] = []

    def branch_names(self) -> set[str]:
        return {"main"}

    def snapshot(self, branches: set[str]) -> dict[str, Any]:
        return {"prs": [self.row], "queues": {"main": True}, "remaining": 3000, "cost": 10}

    def identity(self) -> str:
        return "driver"

    def comments(self, number: int) -> list[dict[str, Any]]:
        return list(self.comment_rows)

    def checks(self, head: str) -> list[dict[str, Any]]:
        return self.check_rows

    def current(self, number: int) -> dict[str, Any]:
        return {**self.row, "state": "OPEN", "labels": []}

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

    def comment(self, number: int, body: str) -> None:
        super().comment(number, body)
        self.comment_rows.append({"body": body, "user": {"login": "driver"}})

    def create_issue(self, title: str, body: str) -> None:
        super().create_issue(title, body)
        self.issue_rows.append({"title": title})


@pytest.fixture
def transport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_opsec, publisher_transport) -> Transport:
    monkeypatch.setenv("GH_REPO", "unit/public")
    common = tmp_path / ".git"
    common.mkdir()
    monkeypatch.setattr(recovery, "ledger_path", lambda cwd: common / "ci-recovery.sqlite3")
    sender = Transport()
    monkeypatch.setattr(
        keeper,
        "request_run",
        lambda request, **kwargs: publisher.request_run(request, runner=sender, env={}, **kwargs),
    )
    return sender


def ejected(subject: Subject, path: Path, jobs: list[str], **state: Any) -> None:
    """PR 42 was queued at ``HEAD`` on the last run and has since left the queue after a failed merge_group run."""
    subject.events = [{"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:01Z"}]
    subject.run_rows = [
        {
            "id": 321,
            "event": "merge_group",
            "conclusion": "failure",
            "created_at": "2026-09-23T00:00:02Z",
            "head_branch": "gh-readonly-queue/main/pr-42-deadbeef",
            "html_url": RUN_URL,
        }
    ]
    subject.job_rows = [{"name": job, "conclusion": "failure"} for job in jobs]
    path.write_text(json.dumps({"queued": {"42": HEAD}, "drops": {}, "observed": "2026-09-23T00:00:00Z", **state}))


def drop_with_check(tmp_path: Path, name: str, status: str) -> tuple[Subject, Path]:
    """An ejected PR whose ``name`` check failed (``completed``) or is still running (``in_progress``)."""
    subject = Subject(tmp_path)
    conclusion = "failure" if status == "completed" else None
    subject.check_rows = [check("CI Gate"), check(name, status, conclusion)]
    path = tmp_path / "state.json"
    ejected(subject, path, [name])
    return subject, path


def assert_inert(body: str) -> str:
    """Assert the published body is one plain sentence plus one intact marker; return the sentence."""
    text, separator, marker = body.rpartition("\n\n")
    assert separator, body
    assert MARKER_LINE.fullmatch(marker), marker
    assert not any(token in text for token in ("<!--", "-->", "--!>", "<", ">")), text
    assert not any(char in body for char in LOOKALIKE_AT), body
    outside_spans = CODE_SPAN.sub("", text)
    assert "`" not in outside_spans and "```" not in text, text
    assert "](" not in text and "![" not in text and "[" not in outside_spans, text
    assert "://" not in text.replace(RUN_URL, ""), text
    assert not any(unicodedata.category(char) in {"Cc", "Cf", "Zl", "Zp"} for char in text), ascii(text)
    assert len(body) < 2000
    return text


# --- the reviewer's reproducer: raw names in the CI-red and CI-pending reasons ---


@pytest.mark.parametrize("status,prefix", [("completed", "CI-red-"), ("in_progress", "CI-pending-")])
def test_reviewer_reproducer_publishes_no_mention_or_link_in_reason_or_marker(
    tmp_path: Path, transport: Transport, status: str, prefix: str
) -> None:
    subject, path = drop_with_check(tmp_path, REPRODUCER, status)
    lines, failed = keeper.run(subject, path, apply=True)
    assert not failed, lines
    [body] = transport.comments()
    text = assert_inert(body)
    reason = prefix + REPRODUCER
    assert f"was not queued because {keeper.display_text(reason, keeper.DISPLAY_REASON_LIMIT)}." in text
    assert "review-probe/maintainers" in text  # the job stays identifiable
    assert body.endswith(f"reason={keeper.marker_value(reason)} -->")
    # Decisions and the local log keep the raw name; nothing was enqueued.
    assert f"reason={reason} " in lines[0]
    assert keeper._check_state(subject.check_rows, HEAD) == reason
    assert json.loads(path.read_text())["drops"] == {f"42:{HEAD}": 1}


HOSTILE_NAMES = {
    "marker-terminator": "Analyze (x) --> <!-- x",
    "marker-bang-terminator": "Analyze (x --!> injected)",
    "spoofed-marker": f"Analyze (x)\n\n<!-- mq-keeper head={HEAD} reason=ready -->",
    "newline": "Analyze (python)\n\n# heading\n- [ ] task\r\n@octocat",
    "long": "Analyze (" + "x" * 20000 + "@octocat)",
    "bidi-control": "Analyze (‮evil⁦x⁩​‏\x1b[31m\x00\x85  )",
    "user-mention": "Analyze (@octocat)",
    "team-mention": "Analyze (@org/team-name)",
    "lookalike-at": "Analyze (＠octocat ﹫org/team)",
    "link": "Analyze ([click](https://example.invalid/x))",
    "image": "Analyze (![pixel](https://example.invalid/p.png))",
    "html": "Analyze (<img src=x onerror=alert(1)>)",
    "fence": "Analyze (```sh `x` ~~~)",
    "issue-reference": "Analyze (#123 owner/repo#4 GH-5)",
}


@pytest.mark.parametrize("status", ["completed", "in_progress"])
@pytest.mark.parametrize("label", sorted(HOSTILE_NAMES))
def test_hostile_check_name_cannot_escape_the_comment_or_its_marker(
    tmp_path: Path, transport: Transport, label: str, status: str
) -> None:
    subject, path = drop_with_check(tmp_path, HOSTILE_NAMES[label], status)
    lines, failed = keeper.run(subject, path, apply=True)
    assert not failed, lines
    [body] = transport.comments()
    assert_inert(body)
    assert body.count("\n") == 2


def test_hostile_reason_comment_is_posted_once_across_runs(tmp_path: Path, transport: Transport) -> None:
    subject, path = drop_with_check(tmp_path, REPRODUCER, "in_progress")
    keeper.run(subject, path, apply=True)
    keeper.run(subject, path, apply=True)
    assert len(transport.comments()) == 1


# --- legitimate names and fixed reasons publish exactly what they did before ---


@pytest.mark.parametrize("status,prefix", [("completed", "CI-red-"), ("in_progress", "CI-pending-")])
def test_plain_check_name_publishes_byte_identical_comment_and_marker(
    tmp_path: Path, transport: Transport, status: str, prefix: str
) -> None:
    subject, path = drop_with_check(tmp_path, "Analyze (python)", status)
    keeper.run(subject, path, apply=True)
    reason = f"{prefix}Analyze (python)"
    assert transport.comments() == [
        f"Merge queue keeper: #42 was not queued because {reason}. Failing merge_group: {RUN_URL}; "
        f"failing jobs: `Analyze (python)`.\n\n<!-- mq-keeper head={HEAD} reason={reason} -->"
    ]


def test_comment_posted_before_the_fix_still_deduplicates(tmp_path: Path, transport: Transport) -> None:
    subject, path = drop_with_check(tmp_path, "Analyze (python)", "completed")
    old = f"Merge queue keeper: #42 was not queued because CI-red-Analyze (python).\n\n<!-- mq-keeper head={HEAD} reason=CI-red-Analyze (python) -->"
    subject.comment_rows.append({"body": old, "user": {"login": "driver"}})
    keeper.run(subject, path, apply=True)
    assert transport.comments() == []


@pytest.mark.parametrize(
    "value",
    [
        HEAD,
        "needs-CF",
        "third-drop",
        "queue-drop",
        "CF-changes_requested",
        "CI-red-CI Gate",
        "CI-pending-Analyze (javascript-typescript)",
        "CI-red-CodeQL",
        "requeue-denied",
        "RECOVERY_EVIDENCE_MISSING: run/job IDs, tested SHA, failure evidence and diff diagnosis required on PR",
        recovery.spent_reason({"action": "re-enqueue", "at": "2026-10-15T12:00:00.123456+00:00", "run_id": 7}),
    ],
)
def test_fixed_reasons_and_heads_are_marker_values_unchanged(value: str) -> None:
    assert keeper.marker_value(value) == value
    assert keeper.display_text(value, keeper.DISPLAY_REASON_LIMIT) == value


UNTRUSTED_MARKER_VALUES = {
    **HOSTILE_NAMES,
    "empty": "",
    "over-limit": "x" * 201,
    "non-ascii": "CI-red-Аналіз",
    "lone-gt": "a > b",
}


@pytest.mark.parametrize("label", sorted(UNTRUSTED_MARKER_VALUES))
def test_marker_value_of_untrusted_text_is_a_bounded_digest(label: str) -> None:
    raw = UNTRUSTED_MARKER_VALUES[label]
    value = keeper.marker_value(raw)
    digest = hashlib.sha256(raw.encode("utf-8", "surrogatepass")).hexdigest()
    assert value == f"sha256-{digest[:16]}"
    assert MARKER_LINE.fullmatch(keeper.MARKER.format(head=HEAD, reason=value))
    assert keeper.marker_value(raw + "!") != value


# --- every other untrusted path into a published comment ---


def test_github_error_text_in_failing_job_lookup_is_display_text(tmp_path: Path, transport: Transport) -> None:
    subject, path = drop_with_check(tmp_path, "Analyze (python)", "completed")
    error = "HTTP 502\n\n@octocat [x](https://example.invalid/x) --> <!-- x"

    def jobs(run_id: int) -> list[dict[str, Any]]:
        raise keeper.KeeperError(error)

    subject.jobs = jobs  # type: ignore[method-assign]
    keeper.run(subject, path, apply=True)
    [body] = transport.comments()
    text = assert_inert(body)
    assert f"failing job lookup failed: {keeper.display_text(error, keeper.DISPLAY_REASON_LIMIT)}." in text


def test_github_error_text_in_removal_diagnosis_is_display_text(tmp_path: Path, transport: Transport) -> None:
    subject, path = drop_with_check(tmp_path, "Analyze (python)", "completed")
    error = "timeline unavailable\n@org/team ![p](https://example.invalid/p.png)‮"

    def timeline(number: int) -> list[dict[str, Any]]:
        raise keeper.KeeperError(error)

    subject.timeline = timeline  # type: ignore[method-assign]
    keeper.run(subject, path, apply=True)
    [body] = transport.comments()
    text = assert_inert(body)
    assert f"Queue removal diagnosis lookup failed: {keeper.display_text(error, keeper.DISPLAY_REASON_LIMIT)}." in text


def test_owed_comment_read_back_from_state_is_sanitised(tmp_path: Path, transport: Transport) -> None:
    subject = Subject(tmp_path)
    subject.comment_rows = []  # never approved: only the owed note is published
    path = tmp_path / "state.json"
    owed = "needs-CF --> <!-- x\n@octocat [x](https://example.invalid/x)"
    path.write_text(json.dumps({"queued": {}, "drops": {}, "pending_comments": {f"42:{HEAD}": owed}}))
    lines, failed = keeper.run(subject, path, apply=True)
    assert not failed, lines
    [body] = transport.comments()
    assert_inert(body)
    assert "pending_comments" not in json.loads(path.read_text())


# --- the issue path: title and body of a flaky-test issue ---


@pytest.mark.parametrize("label", sorted(HOSTILE_NAMES))
def test_flaky_issue_title_and_body_stay_inert(tmp_path: Path, transport: Transport, label: str) -> None:
    job = HOSTILE_NAMES[label].replace("Analyze", "pytest", 1)
    test = "tests/a.py::test_x --> <!-- @octocat [l](https://example.invalid/l)\n```"
    subject = Subject(tmp_path)
    path = tmp_path / "state.json"
    ejected(subject, path, [job], failures=[{"job": job, "pr": 7, "at": "2999-01-01T00:00:00+00:00", "test": test}])
    lines, failed = keeper.run(subject, path, apply=True)
    assert not failed, lines
    [(title, body)] = transport.issues()
    for field in (title, body):
        assert not any(token in field for token in ("<", ">", "](", "![", "```", "\n", "\r", *LOOKALIKE_AT)), field
        assert "://" not in field
        assert not any(unicodedata.category(char) in {"Cc", "Cf", "Zl", "Zp"} for char in field)
    assert "`" not in CODE_SPAN.sub("", body)
    assert title == f"Merge queue flaky test: {keeper.display_text(job)}" and len(title) < 256
    assert {item["job"] for item in json.loads(path.read_text())["failures"]} == {job}  # raw name kept
    keeper.run(subject, path, apply=True)
    assert len(transport.issues()) == 1


def test_plain_flaky_issue_is_unchanged(tmp_path: Path, transport: Transport) -> None:
    subject = Subject(tmp_path)
    path = tmp_path / "state.json"
    ejected(subject, path, ["pytest (3)"], failures=[{"job": "pytest (3)", "pr": 7, "at": "2999-01-01T00:00:00+00:00"}])
    keeper.run(subject, path, apply=True)
    assert transport.issues() == [
        (
            "Merge queue flaky test: pytest (3)",
            "`pytest (3)` failed merge_group runs on distinct PRs #7, #42 within 24 hours.",
        )
    ]
