"""Guard and replenish GitHub merge queues from exact-head review and CI evidence."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import heapq
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.github_client import GitHubRateLimited
from scripts.gh_merge_queue_status import extract_pr_number
from scripts.github_check_rollup import bind_workflow_runs, group_collapsed_by_name, project_check_runs
from scripts.opsec.prepublish import (
    PublishBlocked,
    check_texts,
    normalize_repository,
    publication_boundary,
    publication_cli,
)
from scripts.orchestration.integration_sweep import (
    COMMENTS_UNAVAILABLE,
    Verdict,
    classify_pr,
    lookup_verdict,
    parse_marker,
    verdict_detail,
)
from scripts.publish.github import Request, request_run

FLOOR = 500
MARKER = "<!-- mq-keeper head={head} reason={reason} -->"
HOLD_TITLE = re.compile(r"\[(?:needs operator go|hold)\]", re.I)
HOLD_LABELS = {"needs-operator-go", "hold", "do-not-merge", "blocked"}
# No recorded approval for the head that would merge. All three surface as needs-CF.
MISSING_CF_STATES = frozenset({"needs-CF", "CF-stale", "CF-unrecorded"})
SHA = re.compile(r"[0-9a-f]{40}\Z")
# Dependency-update PRs get no per-language ``Analyze (…)`` CodeQL runs, only
# the top-level CodeQL check from GitHub code scanning (#8587, #9921). That
# check stands in for Analyze only when every changed file is an npm or pip/uv
# lockfile or package.json, whoever authored the PR: anyone with write access
# can push code to a dependabot branch, and github-actions bumps edit workflows.
CODEQL_CHECK = "CodeQL"
# GitHub's code-scanning app; both its id and its reserved slug must match.
CODEQL_APP_ID = 57789
CODEQL_APP = "github-advanced-security"
CODEQL_PASSING = frozenset({"success", "neutral"})
DEPENDENCY_FILES = frozenset({"package-lock.json", "package.json", "uv.lock"})
REQUIREMENTS_FILE = re.compile(r"requirements[\w.-]*\.txt\Z")
# GitHub's PR-files endpoint stops at this many files without saying so.
PR_FILES_LIMIT = 3000
# Slow mode: ``--apply`` skips a run that starts within this many seconds of
# the last recorded run, so a frequent timer can be throttled without a unit edit.
MIN_INTERVAL_ENV = "MQ_KEEPER_MIN_INTERVAL_SECONDS"
SLOW_FLAG_ENV = "MQ_KEEPER_SLOW_FLAG"
SLOW_INTERVAL_SECONDS = 300
# Timer jitter allowance so a throttled minute timer still runs on the fifth minute.
INTERVAL_SLACK_SECONDS = 15
AGGREGATE_JOBS = frozenset({"CI Gate"})
# Job and check names and failed-test identifiers come from workflow files and CI
# logs, so any PR author controls them; gate reasons embed check names, and
# GitHub error text is unvetted. They reach public issue titles, issue bodies and
# PR comments only through ``display_text`` / ``code_span``, bounded here, and the
# HTML comment marker only through ``marker_value``. Decisions and local log
# lines keep the raw text.
DISPLAY_JOB_LIMIT = 100  # characters of a job name shown, before the id suffix
DISPLAY_TEST_LIMIT = 200  # characters of a failed-test identifier shown
DISPLAY_REASON_LIMIT = 200  # characters of a gate reason or GitHub error shown
DISPLAY_ID_LENGTH = 8  # hex digits of the raw-text digest appended to altered text
MARKER_ID_LENGTH = 16  # hex digits of the raw-text digest that replaces a disallowed marker value


# (pattern, replacement) pairs applied in order by ``display_text``.
_NEUTRALISERS = tuple(
    (re.compile(pattern), replacement)
    for pattern, replacement in (
        (r"@", "(at)"),  # user and team mentions, and bare addresses
        (r"#(?=\d)", "(#)"),  # issue and PR references
        (r"(?i)\bGH-(?=\d)", "GH(-)"),
        (r"\[", "("),  # inline links, images and references
        (r"\]", ")"),
        (r"<", "\u2039"),  # HTML and autolinks
        (r">", "\u203a"),
        (r"`", "'"),  # code spans and fences
        (r"~", "-"),  # tilde fences and strike-through
        (r"&(?=#?\w+;)", "(&)"),  # character references
        (r"://", ":(//)"),  # bare URLs
        (r"(?i)\bwww\.", "www(.)"),
    )
)
_DROPPED_CATEGORIES = frozenset({"Cf", "Cs", "Co", "Cn"})  # format, surrogate, private, unassigned
_SPACED_CATEGORIES = frozenset({"Cc", "Zl", "Zp"})  # control and line or paragraph separators
# Short ASCII without ``<``, ``>``, ``!``, ``@``, brackets, backticks or line breaks:
# such a value can neither end the HTML comment nor mention, link or format anything.
_MARKER_VALUE = re.compile(r"[A-Za-z0-9 _.,;:=+/()-]{1,200}\Z")


def display_text(raw: str, limit: int = DISPLAY_JOB_LIMIT) -> str:
    """Plain text safe for an issue title or Markdown body, deterministic in ``raw``.

    Neutralises mentions (including look-alike ``@`` signs and ``@org/team``),
    Markdown links and images, HTML, backticks and tildes, issue and PR
    auto-references, newlines and control or format characters, then bounds the
    length. Text that had to change gets a short digest of the raw text, so two
    different hostile names never collapse into one title. Benign names pass
    through unchanged, which keeps titles of already filed issues matching.
    """
    text = unicodedata.normalize("NFKC", raw)  # folds full-width and small ``@``, ``#``, backtick, ``<``
    categories = [(char, unicodedata.category(char)) for char in text]
    text = "".join(" " if cat in _SPACED_CATEGORIES else char for char, cat in categories if cat not in _DROPPED_CATEGORIES)
    text = " ".join(text.split())
    for pattern, replacement in _NEUTRALISERS:
        text = pattern.sub(replacement, text)
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"
    text = text or "(unnamed)"
    if text != raw:
        text += f" (id:{hashlib.sha256(raw.encode('utf-8', 'surrogatepass')).hexdigest()[:DISPLAY_ID_LENGTH]})"
    return text


def code_span(raw: str, limit: int = DISPLAY_JOB_LIMIT) -> str:
    """``display_text`` inside an inline code span: inert Markdown even if a pattern slips through."""
    return f"`{display_text(raw, limit)}`"


def marker_value(raw: str) -> str:
    """``raw`` for an HTML comment marker when it is allowlisted, else a digest of it.

    Fixed reasons, head SHAs and plain check names keep the markers of comments
    already posted, so de-duplication still finds them. Any other text becomes
    ``sha256-<hex>``: deterministic in ``raw`` and unable to break out of the marker.
    """
    if _MARKER_VALUE.fullmatch(raw):
        return raw
    return f"sha256-{hashlib.sha256(raw.encode('utf-8', 'surrogatepass')).hexdigest()[:MARKER_ID_LENGTH]}"


class KeeperError(RuntimeError):
    """A GitHub response or mutation was incomplete or failed."""


def _auto_merge_armed(row: Mapping[str, Any]) -> bool:
    request = row.get("autoMergeRequest")
    return isinstance(request, Mapping) and bool(request.get("enabledAt"))


class GitHub:
    def __init__(self, root: Path, repository: str) -> None:
        self.root, self.repository = root, repository

    @publication_boundary(KeeperError)
    def call(self, *args: str) -> str:
        try:
            result = request_run(
                args[0] if len(args) == 1 and isinstance(args[0], Request) else ["gh", *args],
                cwd=self.root,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise KeeperError("GitHub request timed out") from exc
        observation = getattr(result, "github_result", None)
        if observation is not None and (observation.stale or observation.error == "github_rate_limited"):
            raise GitHubRateLimited(observation.reset_at)
        if result.returncode:
            raise KeeperError((result.stderr or result.stdout or "GitHub request failed").strip()[:500])
        return result.stdout

    def json(self, *args: str) -> Any:
        try:
            return json.loads(self.call(*args))
        except ValueError as exc:
            raise KeeperError("invalid GitHub JSON") from exc

    def paged(self, request: Request) -> list[dict[str, Any]]:
        request.fields.update(paginate=True, slurp=True)
        pages = self.json(request)
        if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
            raise KeeperError(f"partial pagination: {request.verb}")
        rows = [row for page in pages for row in page]
        if not all(isinstance(row, dict) for row in rows):
            raise KeeperError(f"malformed pagination: {request.verb}")
        return rows

    def identity(self) -> str:
        value = self.json(Request("read-identity")).get("login", "").strip()
        if not value:
            raise KeeperError("authenticated identity unknown")
        return value

    def branch_names(self) -> set[str]:
        rows = self.json(
            "pr", "list", "-R", self.repository, "--state", "open", "--limit", "1000", "--json", "baseRefName"
        )
        if (
            not isinstance(rows, list)
            or len(rows) >= 1000
            or not all(isinstance(row, dict) and isinstance(row.get("baseRefName"), str) for row in rows)
        ):
            raise KeeperError("open PR branch list incomplete")
        return {row["baseRefName"] for row in rows}

    def snapshot(self, branches: set[str]) -> dict[str, Any]:
        data = self.json(Request("read-queue-snapshot", repo=self.repository, branches=branches))
        if not isinstance(data, dict) or data.get("errors"):
            raise KeeperError("partial GraphQL snapshot")
        payload = data.get("data")
        repo = payload.get("repository") if isinstance(payload, dict) else None
        rate = payload.get("rateLimit") if isinstance(payload, dict) else None
        prs = repo.get("pullRequests") if isinstance(repo, dict) else None
        if (
            not isinstance(rate, dict)
            or not isinstance(rate.get("remaining"), int)
            or not isinstance(rate.get("cost"), int)
            or not isinstance(prs, dict)
            or not isinstance(prs.get("nodes"), list)
        ):
            raise KeeperError("incomplete GraphQL snapshot")
        if prs.get("pageInfo", {}).get("hasNextPage") or prs.get("totalCount") != len(prs["nodes"]):
            raise KeeperError("partial open PR page")
        queues = {branch: repo.get(f"q{i}") is not None for i, branch in enumerate(sorted(branches))}
        if any(f"q{i}" not in repo for i in range(len(branches))):
            raise KeeperError("queue configuration unknown")
        return {
            "prs": prs["nodes"],
            "queues": queues,
            "remaining": rate["remaining"],
            "cost": rate["cost"],
            "reset_at": rate.get("resetAt"),
        }

    def comments(self, number: int) -> list[dict[str, Any]]:
        return self.paged(Request("read-comments", repo=self.repository, number=number))

    def checks(self, head: str) -> list[dict[str, Any]]:
        data = self.json(Request("read-checks", repo=self.repository, sha=head))
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("total_count"), int)
            or not isinstance(data.get("check_runs"), list)
            or data["total_count"] != len(data["check_runs"])
        ):
            raise KeeperError("check-runs page incomplete")
        repo = self.repository.removeprefix("github.com/")
        rows = bind_workflow_runs(
            data["check_runs"], head, repo,
            lambda number: self.json(Request("read-run", repo=self.repository, number=number)),
        )
        if rows is None:
            raise KeeperError("check workflow provenance unknown")
        return rows

    def files(self, number: int) -> list[dict[str, Any]]:
        """Every changed file of a PR; raises when the list may be truncated or incomplete."""
        pull = self.json(Request("read-pull", repo=self.repository, number=number))
        changed = pull.get("changed_files") if isinstance(pull, dict) else None
        if type(changed) is not int:
            raise KeeperError("PR changed-file count unknown")
        if changed >= PR_FILES_LIMIT:
            raise KeeperError("PR file list truncated")
        rows = self.paged(Request("read-pr-files", repo=self.repository, number=number))
        if len(rows) >= PR_FILES_LIMIT or len(rows) != changed:
            raise KeeperError("PR file list incomplete")
        return rows

    def current(self, number: int) -> dict[str, Any]:
        row = self.json(
            "pr",
            "view",
            str(number),
            "-R",
            self.repository,
            "--json",
            "number,title,isDraft,headRefOid,baseRefName,autoMergeRequest,mergeStateStatus,state",
        )
        if not isinstance(row, dict):
            raise KeeperError("current PR lookup incomplete")
        row["labels"] = self.paged(Request("read-labels", repo=self.repository, number=number))
        return row

    def membership(self, number: int) -> bool:
        data = self.json(Request("read-membership", repo=self.repository, number=number))
        if not isinstance(data, dict) or data.get("errors"):
            raise KeeperError("queue membership lookup failed")
        node = ((data.get("data") or {}).get("repository") or {}).get("pullRequest")
        if not isinstance(node, dict) or not isinstance(node.get("isInMergeQueue"), bool):
            raise KeeperError("queue membership unknown")
        return node["isInMergeQueue"]

    def squash_blocked(self, number: int, head: str) -> bool | None:
        """Whether the squash text a queued PR will publish has a blocking finding; None when unverified.

        The enqueue mutation takes no commit text: GitHub composes the queued
        squash from the PR's current title and body. pr-merge scanned that text
        at enqueue, and every agent title or body edit is scanned by the
        publisher; this re-reads the current default text, and the message of
        the queue entry's head commit once GitHub reports one, so an edit made
        any other way after enqueue is caught at the next run.
        """
        try:
            data = self.json(Request("read-squash-text", repo=self.repository, number=number))
            pull = data["data"]["repository"]["pullRequest"]
            texts = [pull["viewerMergeHeadlineText"], pull["viewerMergeBodyText"]]
            names = ["default_subject", "default_body"]
            commit = (pull.get("mergeQueueEntry") or {}).get("headCommit")
            if commit is not None:
                texts.append(commit["message"])
                names.append("queue_entry_commit.message")
            if data.get("errors") or pull["headRefOid"] != head or not all(isinstance(text, str) for text in texts):
                return None
        except (KeeperError, KeyError, TypeError, AttributeError):
            return None
        try:
            check_texts(normalize_repository(self.repository), texts, environment={}, field_names=names)
        except PublishBlocked as error:
            return True if error.indices else None
        except Exception:
            return None
        return False

    def enqueue(self, number: int, head: str) -> None:
        self.call(Request("pr-merge", repo=self.repository, number=number, match_head=head))

    def dequeue(self, node_id: str) -> None:
        data = self.json(Request("pr-dequeue", repo=self.repository, node_id=node_id))
        if not isinstance(data, dict) or data.get("errors") or not (data.get("data") or {}).get("dequeuePullRequest"):
            raise KeeperError("dequeue failed")

    def disarm(self, number: int) -> None:
        self.call(Request("pr-disarm", repo=self.repository, number=number))

    def comment(self, number: int, body: str) -> None:
        self.call(Request("pr-comment", repo=self.repository, number=number, body=body))

    def timeline(self, number: int) -> list[dict[str, Any]]:
        return self.paged(Request("read-timeline", repo=self.repository, number=number))

    def created_at(self, number: int) -> str:
        """PR creation is a complete lower bound when its queue-entry event is absent."""
        pull = self.json(Request("read-pull", repo=self.repository, number=number))
        stamp = pull.get("created_at") if isinstance(pull, dict) else None
        if not isinstance(stamp, str):
            raise KeeperError("PR creation time unknown")
        try:
            datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise KeeperError("PR creation time invalid") from exc
        return stamp

    def runs(self, since: str) -> list[dict[str, Any]]:
        end = datetime.now(UTC).replace(microsecond=0)
        try:
            start = datetime.fromisoformat(since.replace("Z", "+00:00")).astimezone(UTC).replace(microsecond=0)
        except ValueError:
            start = end - timedelta(days=1)
        return self._runs_window(start, end)

    def _runs_window(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        if start > end:
            return []
        pages = self.json(
            Request(
                "read-runs",
                repo=self.repository,
                start=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                paginate=True,
                slurp=True,
            )
        )
        if not isinstance(pages, list) or not all(
            isinstance(page, dict) and isinstance(page.get("workflow_runs"), list) for page in pages
        ):
            raise KeeperError("merge_group run pagination incomplete")
        runs = [item for page in pages for item in page["workflow_runs"]]
        total = pages[0].get("total_count") if pages else None
        if type(total) is int and total > 1000:
            if start == end:
                raise KeeperError("merge_group run cap exceeded within one second")
            middle = start + timedelta(seconds=int((end - start).total_seconds()) // 2)
            return self._runs_window(start, middle) + self._runs_window(middle + timedelta(seconds=1), end)
        if not all(isinstance(item, dict) for item in runs) or not pages or pages[0].get("total_count") != len(runs):
            raise KeeperError("merge_group run page incomplete")
        return runs

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        data = self.json(Request("read-jobs", repo=self.repository, number=run_id))
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list) or data.get("total_count", 0) > 100:
            raise KeeperError("merge_group job page incomplete")
        return data["jobs"]

    def failed_tests(self, job_id: int) -> list[str]:
        """Extract only a test's relative source identifier, never log values."""
        log = self.call("run", "view", "-R", self.repository, "--job", str(job_id), "--log")
        tests: list[str] = []
        for match in re.finditer(r"\bFAILED\s+(tests/[^\r\n]+?)(?:\s+-\s|\r?$)", log, re.M):
            # Pytest parameter IDs can contain arbitrary private runtime data.
            # Project only the source path and Python identifiers; decline any
            # unrecognized text instead of forwarding it into a public comment.
            identifier = match[1].partition("[")[0]
            if re.fullmatch(
                r"tests/(?:[A-Za-z_][A-Za-z0-9_]*/)*[A-Za-z_][A-Za-z0-9_]*\.py"
                r"(?:::[A-Za-z_][A-Za-z0-9_]*)+",
                identifier,
            ) and identifier not in tests:
                tests.append(identifier)
        return tests

    def issue_comment(self, number: int, body: str) -> None:
        self.call(Request("issue-comment", repo=self.repository, number=number, body=body))

    def issues(self, title: str) -> list[dict[str, Any]]:
        return self.paged(Request("read-issues", repo=self.repository))

    def create_issue(self, title: str, body: str) -> int:
        raise KeeperError("automatic flaky-test issue creation is disabled; report finding to CTO")


def _hold(row: Mapping[str, Any]) -> bool | None:
    title = row.get("title")
    labels = row.get("labels")
    if not isinstance(title, str) or not isinstance(labels, (list, dict)):
        return None
    if isinstance(labels, dict):
        if labels.get("pageInfo", {}).get("hasNextPage") or labels.get("totalCount", 0) > len(labels.get("nodes", [])):
            return None
        labels = labels.get("nodes")
    if not isinstance(labels, list) or not all(
        isinstance(item, dict) and isinstance(item.get("name"), str) for item in labels
    ):
        return None
    return bool(HOLD_TITLE.search(title) or any(item["name"].casefold() in HOLD_LABELS for item in labels))


def _latest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(rows, key=lambda item: item.get("started_at") or item.get("created_at") or "")


def _codeql_rows(checks: list[dict[str, Any]], head: str) -> list[dict[str, Any]]:
    """Top-level CodeQL check runs at ``head`` from GitHub code scanning (not a same-named workflow job)."""
    return [
        row
        for row in checks
        if isinstance(row, dict)
        and row.get("head_sha") == head
        and row.get("name") == CODEQL_CHECK
        and isinstance(row.get("app"), dict)
        and row["app"].get("id") == CODEQL_APP_ID
        and row["app"].get("slug") == CODEQL_APP
    ]


def _check_state(checks: list[dict[str, Any]], head: str, *, dependency_update: bool = False) -> str:
    """``ok``, a pending reason or ``CI-red-<check>`` for ``CI Gate`` plus CodeQL at ``head``.

    CodeQL evidence is the ``Analyze (…)`` runs. A PR with none of them waits
    (``CodeQL-pending``) unless ``dependency_update`` is set, in which case the
    completed top-level CodeQL check must be success or neutral (#9921).
    """
    for row in checks:
        if not isinstance(row, dict) or row.get("head_sha") != head or not isinstance(row.get("name"), str):
            return "CI-unknown"
    names, _ = group_collapsed_by_name(project_check_runs(checks))
    required = ["CI Gate", *(name for name in names if name.startswith("Analyze ("))]
    pending: str | None = "CodeQL-pending" if len(required) == 1 else None
    if pending and dependency_update:
        codeql = _codeql_rows(checks, head)
        latest, _ = group_collapsed_by_name(project_check_runs(codeql))
        survivors = latest.get(CODEQL_CHECK, [])
        if survivors and all(row.get("status") == "COMPLETED" for row in survivors):
            if any(row.get("conclusion", "").lower() not in CODEQL_PASSING for row in survivors):
                return f"CI-red-{CODEQL_CHECK}"
            pending = None
    for name in required:
        rows = names.get(name, [])
        if not rows:
            pending = pending or f"CI-pending-{name}"
            continue
        for row in rows:
            if row.get("status") != "COMPLETED":
                pending = pending or f"CI-pending-{name}"
                continue
            if row.get("conclusion") != "SUCCESS":
                return f"CI-red-{name}"
    return pending or "ok"


def _dependency_file(path: Any) -> bool:
    if not isinstance(path, str) or not path:
        return False
    name = path.rsplit("/", 1)[-1]
    return name in DEPENDENCY_FILES or bool(REQUIREMENTS_FILE.fullmatch(name))


def _dependency_update(gh: GitHub, number: int) -> bool:
    """Whether the PR changes only lockfiles and package.json; the author never matters."""
    files = gh.files(number)
    return bool(files) and all(
        _dependency_file(row.get("filename"))
        and ("previous_filename" not in row or _dependency_file(row.get("previous_filename")))
        for row in files
    )


def _evaluate_checks(gh: GitHub, number: int, head: str, checks: list[dict[str, Any]]) -> str:
    """:func:`_check_state`, reading the file list only when a PR has no ``Analyze`` runs but a CodeQL check."""
    state = _check_state(checks, head)
    if state != "CodeQL-pending" or not _codeql_rows(checks, head):
        return state
    return _check_state(checks, head, dependency_update=_dependency_update(gh, number))


def _reason(row: Mapping[str, Any], verdict: Verdict, check_state: str, drops: int, queue_enabled: bool | None) -> str:
    if queue_enabled is not True:
        return "no-merge-queue" if queue_enabled is False else "queue-unknown"
    if not isinstance(row.get("headRefOid"), str) or not SHA.fullmatch(row["headRefOid"]):
        return "head-unknown"
    if row.get("isDraft") is not False:
        return "draft" if row.get("isDraft") is True else "draft-unknown"
    hold = _hold(row)
    if hold is not False:
        return "hold" if hold else "hold-unknown"
    if verdict.state != "APPROVED":
        return "needs-CF" if verdict.state in MISSING_CF_STATES else f"CF-{verdict.state.lower()}"
    if check_state != "ok":
        return check_state
    if row.get("mergeStateStatus") in {"DIRTY", "UNKNOWN"} or not isinstance(row.get("mergeStateStatus"), str):
        return "merge-state-unknown" if row.get("mergeStateStatus") != "DIRTY" else "merge-conflict"
    if drops >= 3:
        return "third-drop"
    return "ready"


def _gate_hold(gh: GitHub, number: int, head: str, previous: Mapping[str, Any]) -> str | None:
    """Retain the published-text safeguard after a squash-text revocation."""
    if f"{number}:{head}" in previous.get("squash_revoked", {}) and gh.squash_blocked(number, head) is not False:
        return "squash-text-blocked"
    return None


def _min_interval(environ: Mapping[str, str]) -> int:
    """Seconds an ``--apply`` run must wait after the last one (0 = every timer tick)."""
    seconds = 0
    raw = environ.get(MIN_INTERVAL_ENV, "").strip()
    if raw:
        try:
            seconds = max(0, int(raw))
        except ValueError:
            seconds = SLOW_INTERVAL_SECONDS
    flag = environ.get(SLOW_FLAG_ENV, "").strip()
    if flag and Path(flag).exists():
        seconds = max(seconds, SLOW_INTERVAL_SECONDS)
    return seconds


def _throttled(state_path: Path, seconds: int, now: datetime | None = None) -> bool:
    """True when the last recorded run is younger than ``seconds`` (minus timer slack)."""
    if seconds <= 0:
        return False
    try:
        observed = datetime.fromisoformat(json.loads(state_path.read_text())["observed"])
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if observed.tzinfo is None:
        return False
    elapsed = ((now or datetime.now(UTC)) - observed).total_seconds()
    return 0 <= elapsed < seconds - INTERVAL_SLACK_SECONDS


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"queued": {}, "drops": {}}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise KeeperError("keeper state unreadable") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("queued"), dict)
        or not isinstance(data.get("drops"), dict)
        or not isinstance(data.get("approved", {}), dict)
        or not isinstance(data.get("undiagnosed", {}), dict)
        or not isinstance(data.get("squash_revoked", {}), dict)
        or not isinstance(data.get("pending_comments", {}), dict)
        or not isinstance(data.get("flake_issue_updates", {}), dict)
    ):
        raise KeeperError("keeper state malformed")
    for name in ("requeued", "shared_pass", "shared_requeues"):
        data.pop(name, None)
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, sort_keys=True))
    os.replace(temp, path)


def _ever_approved(comments: list[dict[str, Any]], login: str) -> bool:
    heads = set()
    for row in comments:
        body = row.get("body")
        marker = parse_marker(body) if isinstance(body, str) else None
        if marker:
            heads.add(marker["sha"])
    return any(lookup_verdict(comments, head, login).state == "APPROVED" for head in heads)


def _recorded_approval_for_head(comments: list[dict[str, Any]], head: str, login: str) -> bool:
    """Find a recorder-approved head even when a later marker changed the verdict."""
    return any(
        isinstance(row, dict)
        and isinstance(row.get("body"), str)
        and (marker := parse_marker(row["body"])) is not None
        and marker["sha"] == head
        and lookup_verdict([row], head, login).state == "APPROVED"
        for row in comments
    )


def _cf_unknown_detail(cause: str, verdict: Verdict) -> str:
    """Name the typed reason and comment behind a CF-unknown hold or revocation (#11127)."""
    if not cause.startswith("CF-unknown") or verdict.state != "unknown":
        return ""
    return verdict_detail(verdict.reason, verdict.comment_id)


def _revoke_reason(
    row: Mapping[str, Any],
    verdict: Verdict,
    checks: str,
    approved_before: bool,
    verdict_lookup_ok: bool,
    *,
    queued: bool,
) -> str | None:
    """Fresh, positive blockers that may remove a queued or armed PR.

    A queued head with no cross-family approval at that head is removed.
    """
    if row.get("isDraft") is True:
        return "draft"
    if _hold(row) is True:
        return "hold"
    if checks.startswith("CI-red-"):
        return checks
    if verdict.state in {"CHANGES_REQUESTED", "BLOCKED"}:
        return f"CF-{verdict.state.lower()}"
    if verdict_lookup_ok and verdict.state == "unknown" and approved_before:
        return "CF-unknown-after-approval"
    if queued and verdict_lookup_ok and verdict.state in MISSING_CF_STATES:
        return "needs-CF"
    return None


def _flush_pending_comments(
    gh: GitHub,
    number: int,
    comments: list[dict[str, Any]],
    login: str,
    previous: dict[str, Any],
    *,
    comment_safe: bool,
) -> None:
    """Post an owed removal note, including after the pull request has left the queue."""
    pending = previous.get("pending_comments")
    if not isinstance(pending, dict) or not pending or not comment_safe:
        return
    prefix = f"{number}:"
    for key, reason in list(pending.items()):
        if not isinstance(key, str) or not key.startswith(prefix):
            continue
        head = key.split(":", 1)[1]
        if not isinstance(reason, str) or not SHA.fullmatch(head):
            pending.pop(key, None)
            continue
        _comment_once(gh, number, head, reason, comments, login)
        pending.pop(key, None)
    if not pending:
        previous.pop("pending_comments", None)


def _comment_once(
    gh: GitHub, number: int, head: str, reason: str, comments: list[dict[str, Any]], login: str, detail: str = ""
) -> None:
    """Post a hold reason or prior removal diagnosis once; ``detail`` is already display-safe."""
    marker = MARKER.format(head=marker_value(head), reason=marker_value(reason))
    if any(marker in str(row.get("body", "")) and (row.get("user") or {}).get("login") == login for row in comments):
        return
    shown = display_text(reason, DISPLAY_REASON_LIMIT)
    message = "was previously removed from the queue" if reason == "queue-drop" else f"was not queued because {shown}"
    gh.comment(number, f"Merge queue keeper: #{number} {message}.{detail}\n\n{marker}")
    comments.append({"body": marker, "user": {"login": login}})


def _drop_detail(gh: GitHub, number: int, head: str, since: str) -> tuple[str, list[str], dict[str, list[str]], int | None]:
    """Return the diagnosis text, the failed job names and all failed tests per job, and run ID."""
    timeline = gh.timeline(number)
    events = [
        item
        for item in timeline
        if item.get("event") == "removed_from_merge_queue" and item.get("created_at", "") >= since
    ]
    entries = [
        item["created_at"]
        for item in timeline
        if item.get("event") == "added_to_merge_queue"
        and isinstance(item.get("created_at"), str)
        and item["created_at"] <= since
    ]
    # A run starts at queue entry, often long before the keeper last saw the
    # PR queued. When the entry is known, it also bounds failures: queue
    # ejection can lag a failure beyond the keeper's last observation.
    start = max(entries) if entries else gh.created_at(number)
    runs = [
        item
        for item in gh.runs(start)
        if item.get("event") == "merge_group"
        and item.get("conclusion") == "failure"
        and (item.get("updated_at") or item.get("created_at", "")) >= (start if entries else since)
        and item.get("created_at", "") >= start
        and extract_pr_number(str(item.get("head_branch", ""))) == number
    ]
    if not runs:
        return (" Queue removal confirmed; failing merge_group run unknown." if events else ""), [], {}, None
    run = max(runs, key=lambda item: item.get("created_at", ""))
    if not isinstance(run.get("id"), int):
        raise KeeperError("matching merge_group run has no valid id")
    run_detail = f" Failing merge_group: {run.get('html_url') or run['id']}"
    try:
        jobs = gh.jobs(run["id"])
    except KeeperError as exc:
        return f"{run_detail}; failing job lookup failed: {display_text(str(exc), DISPLAY_REASON_LIMIT)}.", [], {}, run["id"]
    failed = sorted(
        {str(job["name"]) for job in jobs if job.get("conclusion") == "failure" and isinstance(job.get("name"), str)}
    )
    names = ", ".join(code_span(name) for name in failed) or "none reported"
    detail = f"{run_detail}; failing jobs: {names}."
    tests: dict[str, list[str]] = {}
    for job in jobs:
        if job.get("conclusion") != "failure" or "pytest" not in str(job.get("name", "")) or type(job.get("id")) is not int:
            continue
        try:
            nodes = gh.failed_tests(job["id"])
            if nodes:
                detail += f" First FAILED test: {code_span(nodes[0], DISPLAY_TEST_LIMIT)}."
                tests[str(job["name"])] = nodes
        except KeeperError:
            pass  # Optional log enrichment must not hide the run/job diagnosis.
    return detail, failed, tests, run["id"]


def _flaky_jobs(failures: Any) -> dict[str, tuple[list[int], list[str]]]:
    """Group by failed node ID, falling back to the job only without a node."""
    prs: dict[str, set[int]] = defaultdict(set)
    tests: dict[str, set[str]] = defaultdict(set)
    for item in failures if isinstance(failures, list) else []:
        if not isinstance(item, dict):
            continue
        job, number, test = item.get("job"), item.get("pr"), item.get("test")
        if not isinstance(job, str) or job in AGGREGATE_JOBS or type(number) is not int:
            continue
        key = test if isinstance(test, str) and test else job
        prs[key].add(number)
        if key != job:
            tests[key].add(test)
    return {job: (sorted(numbers), sorted(tests[job])) for job, numbers in prs.items() if len(numbers) >= 2}


def _identity_spellings(key: str) -> frozenset[str]:
    return frozenset({key, display_text(key), display_text(key, DISPLAY_TEST_LIMIT)})


@dataclass(frozen=True)
class _ProseRun:
    text: str
    at_start: bool
    at_end: bool
    emphasis: frozenset[int]


def _markdown_references(source: str) -> tuple[list[_ProseRun], list[str], str | None]:
    """Rebuild prose once, keeping non-prose barriers and real line boundaries.

    Run edges carry source-boundary flags, so a barrier never supplies a line
    ending. Code values remain literal and link labels never become prose.
    """
    try:
        from markdown_it import MarkdownIt

        parser = MarkdownIt("commonmark")
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        tokens = parser.parse(source)
        for scope in [tokens, *(token.children for token in tokens if token.children is not None)]:
            stack = []
            for token in scope:
                if token.type in {"list_item_open", "blockquote_open"} and token.level + 1 >= parser.options["maxNesting"]:
                    raise ValueError("CommonMark nesting limit reached")
                if token.nesting == 1:
                    stack.append((token.tag, token.markup))
                elif token.nesting == -1 and (not stack or stack.pop() != (token.tag, token.markup)):
                    raise ValueError("unbalanced CommonMark tokens")
            if stack:
                raise ValueError("unclosed CommonMark tokens")
        source_lines = source.split("\n")
        references = []
        codes = []
        legacy = None
        for token in tokens:
            if token.type != "inline":
                continue
            if token.children is None or token.map is None:
                raise ValueError("CommonMark inline source unavailable")
            # Block wrappers can strip heading suffixes and indentation. Keep
            # their neighboring source syntax instead of inventing boundaries.
            content_lines = token.content.split("\n")
            raw_lines = source_lines[token.map[0]:token.map[1]]
            cursor = 0
            contexts = []
            for line in content_lines:
                while cursor < len(raw_lines) and line not in raw_lines[cursor]:
                    cursor += 1
                if cursor == len(raw_lines):
                    raise ValueError("CommonMark source boundaries unavailable")
                offset = raw_lines[cursor].index(line)
                contexts.append((raw_lines[cursor][:offset], raw_lines[cursor][offset + len(line):]))
                cursor += 1
            stream = ""
            emphasis: set[int] = set()
            prefix, suffix = contexts[0][0], contexts[-1][1]
            at_start = not prefix or prefix[-1].isspace()
            link_depth = 0
            for child in token.children:
                if child.type == "link_open":
                    link_depth += 1
                elif child.type == "link_close":
                    link_depth -= 1
                elif link_depth:
                    continue
                elif child.type == "text":
                    stream += child.content
                    continue
                elif child.type in {"em_open", "em_close", "strong_open", "strong_close"}:
                    emphasis.update(range(len(stream), len(stream) + len(child.markup)))
                    stream += child.markup
                    continue
                elif child.type in {"softbreak", "hardbreak"}:
                    stream += "\n"
                    continue
                if child.type == "code_inline" and (stream[-1].isspace() if stream else at_start):
                    codes.append(child.content)
                references.append(_ProseRun(stream, at_start, False, frozenset(emphasis)))
                stream, at_start = "", False
                emphasis = set()
            references.append(_ProseRun(stream, at_start, not suffix or suffix.isspace(), frozenset(emphasis)))
            first = token.children[0] if token.children else None
            if token.map[0] == 0 and first is not None and first.type == "code_inline" and source.startswith(first.markup):
                closer = re.search(r"(?<!`)" + re.escape(first.markup) + r"(?!`)", source[len(first.markup):])
                if closer and source[len(first.markup) + closer.end():].startswith(" failed merge_group runs on distinct PRs "):
                    legacy = first.content
        return references, codes, legacy
    except Exception as exc:
        raise KeeperError(f"CommonMark identity parsing failed ({type(exc).__name__})") from exc


def _reference_eligible(prose: _ProseRun, start: int, end: int) -> bool:
    """Check literal content, allowing one balanced pair outside its span."""
    text = prose.text
    boundaries = [(start, end)]
    if start and end < len(text) and text[start - 1] == "(" and text[end] == ")":
        boundaries.append((start - 1, end + 1))
    for begin, finish in boundaries:
        if not (text[begin - 1].isspace() if begin else prose.at_start):
            continue
        if finish == len(text):
            if prose.at_end:
                return True
        elif text[finish] == "\n" or (text[finish] in ".,;!?" and (
            text[finish + 1].isspace() if finish + 1 < len(text) else prose.at_end
        )):
            return True
    return False


def _whitespace_view(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Collapse maximal whitespace runs, retaining their complete intervals."""
    chars: list[str] = []
    positions: list[tuple[int, int]] = []
    for index, char in enumerate(text):
        if char.isspace():
            if chars and chars[-1] == " ":
                positions[-1] = (positions[-1][0], index + 1)
                continue
            char = " "
        chars.append(char)
        positions.append((index, index + 1))
    return "".join(chars), positions


def _spelling_occurrences(
    text: str, known: Mapping[str, frozenset[str]], positions: list[tuple[int, int]],
) -> list[tuple[int, int, str]]:
    occurrences = []
    for owner, spellings in known.items():
        for spelling in spellings:
            if not spelling:
                continue
            offset = text.find(spelling)
            while offset != -1:
                occurrences.append((positions[offset][0], positions[offset + len(spelling) - 1][1], owner))
                offset = text.find(spelling, offset + 1)
    return occurrences


def _prose_identities(
    prose: _ProseRun, known: Mapping[str, frozenset[str]],
) -> tuple[set[str], set[str]]:
    """Literal eligibility plus conflict-only W/E interval sweeps.

    Every spelling and overlapping occurrence retains its raw owner. Active
    intervals all intersect the current interval; each pair is visited once.
    """
    literal = _spelling_occurrences(prose.text, known, [(i, i + 1) for i in range(len(prose.text))])
    eligible = {(start, end, owner) for start, end, owner in literal if _reference_eligible(prose, start, end)}
    whitespace, positions = _whitespace_view(prose.text)
    normalized = {owner: frozenset(_whitespace_view(value)[0] for value in values)
                  for owner, values in known.items()}
    without_emphasis = [(char, span) for char, span in zip(whitespace, positions, strict=True)
                        if span[0] not in prose.emphasis]
    # Keep literal candidate spans even when a collapsed whitespace interval
    # covers more source characters than that candidate's own spelling.
    views = [(literal, eligible)]
    for text, spans in ((whitespace, positions),
                        ("".join(char for char, _ in without_emphasis), [span for _, span in without_emphasis])):
        view = _ProseRun(text, prose.at_start, prose.at_end, frozenset())
        occurrences = _spelling_occurrences(text, normalized, [(i, i + 1) for i in range(len(text))])
        mapped = [(spans[start][0], spans[end - 1][1], owner) for start, end, owner in occurrences]
        crossing_eligible = {
            (spans[start][0], spans[end - 1][1], owner) for start, end, owner in occurrences
            if _reference_eligible(view, start, end)
        }
        views.append((literal + mapped, eligible | crossing_eligible))
    contested: set[str] = set()
    for occurrences, crossing_eligible in views:
        active: dict[int, tuple[int, int, str]] = {}
        endings: list[tuple[int, int]] = []
        for index, current in enumerate(sorted(set(occurrences))):
            start, end, owner = current
            while endings and endings[0][0] <= start:
                _, expired = heapq.heappop(endings)
                del active[expired]
            for other in active.values():
                left, right, other_owner = other
                if owner == other_owner:
                    continue
                if left <= start and end <= right and right - left > end - start:
                    if current in eligible:
                        contested.add(owner)
                elif start <= left and right <= end and end - start > right - left:
                    if other in eligible:
                        contested.add(other_owner)
                elif (left < start < right < end or start < left < end < right) and (
                    current in crossing_eligible and other in crossing_eligible
                ):
                    contested.update(item[2] for item in (current, other) if item in eligible)
            active[index] = current
            heapq.heappush(endings, (end, index))
    return {owner for _, _, owner in eligible}, contested


def _canonical_flake_issue(
    key: str, node: bool, issues: list[dict[str, Any]], known: Mapping[str, frozenset[str]]
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve without publication or state writes; ambiguity overrides reuse."""
    identities = known[key]
    display_suffix = rf" \\?\(id:[0-9a-f]{{{DISPLAY_ID_LENGTH}}}\\?\)"
    if re.search(display_suffix + r"\Z", key):
        return None, "digest-shaped raw identity"
    if any(identities & values for other, values in known.items() if other != key):
        return None, "raw/rendered identity collision"
    title_patterns = [re.escape(value) for value in sorted(identities)]
    title_patterns.extend(
        "".join((r"\\?" if char in r"\`*_{}[]()#+.!>~-" else "") + re.escape(char) for char in value)
        for value in sorted(identities - {key})
    )
    title_pattern = "(?:" + "|".join(title_patterns) + ")"
    matches = []
    ambiguous = False
    for item in issues:
        if "pull_request" in item or item.get("state", "open") != "open":
            continue
        title, body = (str(item.get(field) or "") for field in ("title", "body"))
        if title.startswith("Merge queue flaky test: "):
            matched = re.fullmatch("Merge queue flaky test: " + title_pattern, title) is not None
        else:
            body_references, body_codes, legacy = _markdown_references(body)
            if not (node or "<!-- mq-keeper-flake -->" in body or legacy in identities):
                continue
            title_references, title_codes, _ = _markdown_references(title)
            matched = any(code in identities for code in [*title_codes, *body_codes])
            for prose in [*title_references, *body_references]:
                eligible, contested = _prose_identities(prose, known)
                matched |= key in eligible
                ambiguous |= key in contested
        if matched:
            matches.append(item)
    if any(type(item.get("number")) is not int or item["number"] <= 0 for item in matches):
        raise KeeperError("matching flaky-test issue has no valid number")
    if ambiguous:
        return None, "known longer identity in prose"
    return (min(matches, key=lambda item: item["number"]) if matches else None), None


def run(gh: GitHub, state_path: Path, *, apply: bool = False) -> tuple[list[str], bool]:
    branches = gh.branch_names()
    snap = gh.snapshot(branches)
    lines: list[str] = []
    failed = False
    estimated_remaining = snap["remaining"]
    budget = estimated_remaining - 30 >= FLOOR
    if not budget:
        return [
            f"GraphQL budget stop: skipped remaining={snap['remaining']} cost={snap['cost']} floor={FLOOR} reset_at={snap.get('reset_at')}"
        ], False
    previous = _load(state_path)
    queued_now: dict[str, str] = {}
    approved_now: dict[str, str] = {}
    login = gh.identity()
    observed = datetime.now(UTC).isoformat()
    open_numbers = {str(pr.get("number")) for pr in snap["prs"]}
    for pr in snap["prs"]:
        number, head, node_id = pr.get("number"), pr.get("headRefOid"), pr.get("id")
        if not isinstance(number, int) or not isinstance(head, str) or not isinstance(node_id, str):
            lines.append("invalid PR identity: unknown, no mutation")
            continue
        key = str(number)
        approved_before = previous.get("approved", {}).get(key) == head
        queued = pr.get("isInMergeQueue")
        armed = _auto_merge_armed(pr)
        if queued is True:
            queued_now[key] = head
        queue_enabled = snap["queues"].get(pr.get("baseRefName"))
        comment_safe = True
        try:
            comments = gh.comments(number)
            verdict = lookup_verdict(comments, head, login)
            check_rows = gh.checks(head)
            checks = _evaluate_checks(gh, number, head, check_rows)
        except KeeperError:
            comments, checks, check_rows = [], "CI-unknown", []
            verdict = Verdict("unknown", reason=COMMENTS_UNAVAILABLE)
            comment_safe = False
        if comment_safe and _recorded_approval_for_head(comments, head, login):
            approved_before = True
        if approved_before:
            approved_now[key] = head
        drop_key = f"{number}:{head}"
        drops = int(previous["drops"].get(drop_key, 0))
        dropped = key in previous["queued"] and queued is False
        detail = ""
        failed_jobs: list[str] = []
        failed_tests: dict[str, list[str]] = {}
        failed_run: int | None = None
        if dropped:
            dropped_head = previous["queued"][key]
            previous.setdefault("undiagnosed", {}).setdefault(f"{number}:{dropped_head}", previous.get("observed", ""))
        else:
            dropped_head = head
        prior_drop_key = f"{number}:{dropped_head}"
        if queued is False and prior_drop_key in previous.get("undiagnosed", {}):
            try:
                detail, failed_jobs, failed_tests, failed_run = _drop_detail(gh, number, head, previous["undiagnosed"][prior_drop_key])
                if detail:
                    previous["undiagnosed"].pop(prior_drop_key)
                    previous["drops"][prior_drop_key] = int(previous["drops"].get(prior_drop_key, 0)) + 1
                    if dropped_head == head:
                        drops = previous["drops"][drop_key]
                else:
                    detail = " Queue removal diagnosis unknown."
            except KeeperError as exc:
                detail = f" Queue removal diagnosis lookup failed: {display_text(str(exc), DISPLAY_REASON_LIMIT)}."
        reason = _reason(pr, verdict, checks, drops, queue_enabled)
        if reason == "ready" and queued is not True and not armed:
            try:
                reason = _gate_hold(gh, number, head, previous) or reason
            except KeeperError:
                reason = "requeue-unknown"
        rollup = project_check_runs(check_rows)
        report = classify_pr(
            {**pr, "statusCheckRollup": rollup},
            verdict,
            queued=queued if isinstance(queued, bool) else None,
            observed_at=observed,
        )
        state = "ready" if reason == "ready" and not queued and not armed else report.state
        lines.append(
            f"#{number} head={head[:12]} state={state} reason={reason} queued={queued} armed={armed}"
            + verdict_detail(verdict.reason, verdict.comment_id, verdict.superseded_markers)
        )
        if not apply:
            continue
        if not budget:
            continue
        if queue_enabled is False:
            continue
        if not isinstance(queued, bool) and not armed:
            continue
        if "autoMergeRequest" not in pr and not queued:
            continue
        if queued is not True and not armed and queue_enabled is not True:
            continue
        can_comment = comment_safe
        try:
            current_verdict = Verdict("unknown", reason=COMMENTS_UNAVAILABLE)
            current_checks = "CI-unknown"
            verdict_lookup_ok = False
            try:
                current = gh.current(number)
            except KeeperError:
                current = {}
            current_head = current.get("headRefOid")
            if not current:
                reason = "fresh-read-unknown"
            elif (
                current_head != head
                or current.get("state") != "OPEN"
                or current.get("baseRefName") != pr.get("baseRefName")
            ):
                reason = (
                    "head-moved"
                    if current_head != head
                    else "base-changed"
                    if current.get("baseRefName") != pr.get("baseRefName")
                    else "state-changed"
                )
            else:
                try:
                    current_comments = gh.comments(number)
                    current_verdict = lookup_verdict(current_comments, head, login)
                except KeeperError:
                    current_comments, current_verdict = [], Verdict("unknown", reason=COMMENTS_UNAVAILABLE)
                    comment_safe = False
                    verdict_lookup_ok = False
                else:
                    verdict_lookup_ok = True
                    comments = current_comments
                    comment_safe = True
                    can_comment = True
                    verdict = current_verdict
                    if _recorded_approval_for_head(current_comments, head, login):
                        approved_before = True
                        approved_now[key] = head
                try:
                    current_checks = _evaluate_checks(gh, number, head, gh.checks(head))
                except KeeperError:
                    current_checks = "CI-unknown"
                reason = (
                    _reason(current, current_verdict, current_checks, drops, queue_enabled)
                    if verdict_lookup_ok
                    else "fresh-evidence-unknown"
                )
                if reason == "ready" and queued is not True and not armed:
                    reason = _gate_hold(gh, number, head, previous) or reason
            if queued is True or armed:
                fresh = bool(
                    current
                    and current_head == head
                    and current.get("state") == "OPEN"
                    and current.get("baseRefName") == pr.get("baseRefName")
                )
                revoke = (
                    _revoke_reason(
                        current,
                        current_verdict,
                        current_checks,
                        approved_before,
                        verdict_lookup_ok,
                        queued=queued is True,
                    )
                    if fresh
                    else None
                )
                if revoke is None and fresh and queued is True:
                    blocked = gh.squash_blocked(number, head)
                    if blocked:
                        revoke = "squash-text-blocked"
                    elif blocked is None:
                        lines.append(f"#{number} squash text unverified")
                if revoke is not None:
                    if queued is True:
                        gh.dequeue(node_id)
                    else:
                        gh.disarm(number)
                    lines.append(f"#{number} revoked: {revoke}" + _cf_unknown_detail(revoke, current_verdict))
                    if queued is True:
                        queued_now.pop(key, None)
                    if revoke == "squash-text-blocked":
                        previous.setdefault("squash_revoked", {})[drop_key] = observed
                    if queued is True and verdict_lookup_ok and current_verdict.state in MISSING_CF_STATES:
                        # Count the removal even when another blocker is the stated reason.
                        previous["drops"][drop_key] = int(previous["drops"].get(drop_key, 0)) + 1
                        if revoke == "needs-CF":
                            previous.setdefault("pending_comments", {})[drop_key] = revoke
                    estimated_remaining -= 30
                elif reason != "ready":
                    lines.append(f"#{number} held: {reason}" + _cf_unknown_detail(reason, current_verdict))
            elif reason == "ready":
                gh.enqueue(number, head)
                if not gh.membership(number):
                    after_enqueue = gh.current(number)
                    if _auto_merge_armed(after_enqueue):
                        lines.append(f"#{number} armed")
                    else:
                        raise KeeperError("enqueue returned success without queue membership or armed auto-merge")
                else:
                    queued_now[key] = head
                    lines.append(f"#{number} enqueued")
                estimated_remaining -= 30
            _flush_pending_comments(gh, number, comments, login, previous, comment_safe=can_comment)
            if (
                reason not in {"ready", "needs-CF", "CF-unknown", "fresh-evidence-unknown", "fresh-read-unknown"}
                and comment_safe
                and (_ever_approved(comments, login) or dropped)
            ):
                _comment_once(gh, number, head, reason, comments, login, detail)
            elif dropped and dropped_head == head and detail and comment_safe:
                _comment_once(gh, number, head, "queue-drop", comments, login, detail)
            for job in failed_jobs:
                if job in AGGREGATE_JOBS:
                    continue  # The aggregate gate fails whenever any job fails; it is never a flaky test.
                for test in failed_tests.get(job, [""]):
                    record: dict[str, Any] = {"job": job, "pr": number, "at": observed}
                    if failed_run is not None:
                        record["run_id"] = failed_run
                    if test:
                        record["test"] = test
                    previous.setdefault("failures", []).append(record)
        except KeeperError as exc:
            failed = True
            lines.append(f"#{number} FAILED: {exc}")
        budget = estimated_remaining - 30 >= FLOOR
    if apply:
        previous["queued"] = queued_now
        previous["approved"] = approved_now
        previous["observed"] = observed
        for name in ("squash_revoked", "undiagnosed", "pending_comments"):
            if name in previous:
                previous[name] = {
                    item: value for item, value in previous[name].items() if item.split(":", 1)[0] in open_numbers
                }
    # Freeze before pruning, including singleton and old loaded records. Issue
    # update keys and PR/head bookkeeping are never source identities.
    known_keys = set()
    for item in previous.get("failures", []):
        if not isinstance(item, dict):
            continue
        job, test = item.get("job"), item.get("test")
        if isinstance(job, str) and job and job not in AGGREGATE_JOBS:
            known_keys.add(job)
        if isinstance(test, str) and test and test not in AGGREGATE_JOBS:
            known_keys.add(test)
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    failures = [
        item for item in previous.get("failures", [])
        if isinstance(item, dict) and isinstance(item.get("at"), str) and item["at"] >= cutoff.isoformat()
    ]
    previous["failures"] = failures
    issue_updates = previous.setdefault("flake_issue_updates", {})
    flaky = _flaky_jobs(failures)
    known = {key: _identity_spellings(key) for key in frozenset(known_keys | flaky.keys())}
    issues = None
    if flaky and budget:
        try:
            issues = list(gh.issues(""))
        except KeeperError as exc:
            failed = True
            lines.append(f"flaky-test issue listing FAILED: {exc}")
    for key, (numbers, tests) in sorted(flaky.items()):
        if not budget or issues is None:
            continue
        matching = [item for item in failures if (item.get("test") or item.get("job")) == key]
        run_ids = sorted({item["run_id"] for item in matching if type(item.get("run_id")) is int})
        body = (
            f"{code_span(key, DISPLAY_TEST_LIMIT)} failed merge_group runs on distinct PRs "
            f"{', '.join(f'#{n}' for n in numbers)} within 24 hours."
            f" Run IDs: {', '.join(map(str, run_ids)) or 'unknown (legacy record)'}."
        )
        if tests:
            body += f" Failed test: {code_span(tests[0], DISPLAY_TEST_LIMIT)}."
        try:
            marker = "<!-- mq-keeper-flake -->"
            issue, ambiguity = _canonical_flake_issue(key, bool(tests), issues, known)
            lines.append(f"flaky record: {display_text(key, DISPLAY_TEST_LIMIT)}; PRs={','.join(map(str, numbers))}; "
                         f"runs={','.join(map(str, run_ids)) or 'unknown'}; issue={issue.get('number', 'unknown') if issue else 'none'}")
            if ambiguity:
                lines.append(f"CTO finding: ambiguous identity for {display_text(key, DISPLAY_TEST_LIMIT)}; "
                             f"{display_text(ambiguity)}; automatic issue creation disabled")
                continue
            if issue is None:
                lines.append(f"CTO finding: no canonical open issue for {display_text(key, DISPLAY_TEST_LIMIT)}; "
                             "automatic issue creation disabled")
                continue
            if not apply:
                continue
            issue_number = issue.get("number")
            if type(issue_number) is not int:
                raise KeeperError("matching flaky-test issue has no number")
            comments = gh.comments(issue_number)
            recent = any(
                marker in str(comment.get("body", ""))
                and (comment.get("user") or {}).get("login") == login
                and str(comment.get("created_at", "")) >= cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
                for comment in comments
            )
            if not recent and issue_updates.get(str(issue_number), "") < cutoff.isoformat():
                gh.issue_comment(issue_number, body + "\n\n" + marker)
                issue_updates[str(issue_number)] = observed
        except KeeperError as exc:
            failed = True
            lines.append(f"flaky-test issue FAILED: {exc}")
    if apply:
        _save(state_path, previous)
    return lines, failed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guard and replenish approved, green pull requests in configured merge queues.\nUse --report to inspect and --apply only for authorized local scheduling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.merge_queue_keeper --report\n  .venv/bin/python -m scripts.orchestration.merge_queue_keeper --apply\nHold mechanisms: labels (needs-operator-go, hold, do-not-merge, blocked) and the [hold] or [needs operator go] title marker.\nOutputs: PR states; --apply also mutates queue/comments and local batch_state.\nEnvironment: MQ_KEEPER_MIN_INTERVAL_SECONDS or an existing MQ_KEEPER_SLOW_FLAG file (300 s) throttles --apply.\nExit codes: 0 success/lock overlap/slow-mode skip; 1 lookup or mutation failure.\nRelated: #8564, integration_sweep.py, record_cf_verdict.py.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--report", action="store_true", help="Read-only report (default).")
    group.add_argument("--apply", action="store_true", help="Enqueue, revoke, comment, and persist state.")
    parser.add_argument(
        "--repo",
        default="learn-ukrainian/learn-ukrainian.github.io",
        help="GitHub owner/repository (default: project repository).",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="Checkout root (default: current directory)."
    )
    return parser


@publication_cli(KeeperError)
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    lock_path = root / "batch_state/locks/merge_queue_keeper.lock"
    if not args.apply:
        try:
            lines, failed = run(
                GitHub(root, args.repo),
                root / "batch_state/merge_queue_keeper.json",
                apply=False,
            )
        except GitHubRateLimited as exc:
            print(f"merge queue keeper: skipped reset_at={exc.reset_at}")
            return 0
        except KeeperError as exc:
            print(f"merge queue keeper failed: {exc}")
            return 1
        for line in lines:
            print(line)
        return int(failed)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("merge queue keeper: overlap, skipped")
            return 0
        state_path = root / "batch_state/merge_queue_keeper.json"
        interval = _min_interval(os.environ)
        if _throttled(state_path, interval):
            print(f"merge queue keeper: slow mode, skipped interval={interval}s")
            return 0
        try:
            lines, failed = run(GitHub(root, args.repo), state_path, apply=args.apply)
        except GitHubRateLimited as exc:
            print(f"merge queue keeper: skipped reset_at={exc.reset_at}")
            return 0
        except KeeperError as exc:
            print(f"merge queue keeper failed: {exc}")
            return 1
        for line in lines:
            print(line)
        return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
