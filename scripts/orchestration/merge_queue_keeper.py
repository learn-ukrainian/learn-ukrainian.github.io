"""Guard and replenish GitHub merge queues from exact-head review and CI evidence."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.github_client import GitHubRateLimited
from scripts.gh_merge_queue_status import extract_pr_number
from scripts.opsec.prepublish import (
    PublishBlocked,
    check_texts,
    normalize_repository,
    publication_boundary,
    publication_cli,
)
from scripts.orchestration.integration_sweep import Verdict, classify_pr, lookup_verdict, parse_marker
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
# A head the merge queue ejected is re-enqueued at most once, and only with
# a ``grant`` decision for ``"<pr>:<head>"`` in this JSON file (written by
# the operator's flake prover). Without a configured file, no grant exists.
REQUEUE_GATE_ENV = "MQ_KEEPER_REQUEUE_GATE"
# Slow mode: ``--apply`` skips a run that starts within this many seconds of
# the last recorded run, so a frequent timer can be throttled without a unit edit.
MIN_INTERVAL_ENV = "MQ_KEEPER_MIN_INTERVAL_SECONDS"
SLOW_FLAG_ENV = "MQ_KEEPER_SLOW_FLAG"
SLOW_INTERVAL_SECONDS = 300
# Timer jitter allowance so a throttled minute timer still runs on the fifth minute.
INTERVAL_SLACK_SECONDS = 15
# Gate holds the keeper reports without a PR comment: the drop comment already says why.
QUIET_GATE_REASONS = frozenset({"requeue-pending"})


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
            or data["total_count"] > len(data["check_runs"])
        ):
            raise KeeperError("check-runs page incomplete")
        return data["check_runs"]

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

    def runs(self, since: str) -> list[dict[str, Any]]:
        start = (
            since[:10]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", since[:10])
            else (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
        )
        end = datetime.now(UTC).date().isoformat()
        pages = self.json(Request("read-runs", repo=self.repository, start=start, end=end, paginate=True, slurp=True))
        if not isinstance(pages, list) or not all(
            isinstance(page, dict) and isinstance(page.get("workflow_runs"), list) for page in pages
        ):
            raise KeeperError("merge_group run pagination incomplete")
        runs = [item for page in pages for item in page["workflow_runs"]]
        if not all(isinstance(item, dict) for item in runs) or not pages or pages[0].get("total_count") != len(runs):
            raise KeeperError("merge_group run page incomplete")
        return runs

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        data = self.json(Request("read-jobs", repo=self.repository, number=run_id))
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list) or data.get("total_count", 0) > 100:
            raise KeeperError("merge_group job page incomplete")
        return data["jobs"]

    def issues(self, title: str) -> list[dict[str, Any]]:
        return self.paged(Request("read-issues", repo=self.repository))

    def create_issue(self, title: str, body: str) -> None:
        self.call(Request("issue-create", repo=self.repository, title=title, body=body, labels=["infra"]))


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
    names: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in checks:
        if not isinstance(row, dict) or row.get("head_sha") != head or not isinstance(row.get("name"), str):
            return "CI-unknown"
        names[row["name"]].append(row)
    required = ["CI Gate", *(name for name in names if name.startswith("Analyze ("))]
    pending: str | None = "CodeQL-pending" if len(required) == 1 else None
    if pending and dependency_update:
        codeql = _codeql_rows(checks, head)
        latest = _latest(codeql) if codeql else None
        if latest is not None and latest.get("status") == "completed":
            if latest.get("conclusion") not in CODEQL_PASSING:
                return f"CI-red-{CODEQL_CHECK}"
            pending = None
    for name in required:
        rows = names.get(name, [])
        if not rows:
            pending = pending or f"CI-pending-{name}"
            continue
        row = _latest(rows)
        if row.get("status") != "completed":
            pending = pending or f"CI-pending-{name}"
            continue
        if row.get("conclusion") != "success":
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


def _requeue_grants(path: Path | None) -> dict[str, dict[str, Any]] | None:
    """Requeue decisions keyed ``"<pr>:<head>"``, or None when no file is configured.

    A missing, unreadable or malformed decision file grants nothing, so a
    keeper holds every ejected head instead of guessing.
    """
    if path is None:
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("requeue"), dict):
        return {}
    return {key: value for key, value in data["requeue"].items() if isinstance(key, str) and isinstance(value, dict)}


def _requeue_hold(
    drop_key: str, drops: int, grants: dict[str, dict[str, Any]] | None, previous: Mapping[str, Any]
) -> str | None:
    """Why the gate keeps an ejected head out of the queue, or None to let it through."""
    if drop_key in previous.get("requeued", {}):
        return "requeue-spent"
    if drop_key in previous.get("undiagnosed", {}):
        return "requeue-unknown"
    if drops < 1:
        return None
    if grants is None:
        return "requeue-pending"
    decision = grants.get(drop_key, {}).get("decision")
    if decision == "grant":
        return None
    return "requeue-denied" if decision == "deny" else "requeue-pending"


def _gate_hold(
    gh: GitHub,
    number: int,
    head: str,
    drops: int,
    grants: dict[str, dict[str, Any]] | None,
    previous: Mapping[str, Any],
) -> str | None:
    """Gate reason for a not-queued head that is otherwise ready; None when it may be enqueued."""
    drop_key = f"{number}:{head}"
    if (
        grants is not None
        and drop_key in previous.get("squash_revoked", {})
        and gh.squash_blocked(number, head) is not False
    ):
        return "squash-text-blocked"
    return _requeue_hold(drop_key, drops, grants, previous)


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
        or not isinstance(data.get("requeued", {}), dict)
        or not isinstance(data.get("undiagnosed", {}), dict)
        or not isinstance(data.get("squash_revoked", {}), dict)
    ):
        raise KeeperError("keeper state malformed")
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


def _comment_once(
    gh: GitHub, number: int, head: str, reason: str, comments: list[dict[str, Any]], login: str, detail: str = ""
) -> None:
    marker = MARKER.format(head=head, reason=reason)
    if any(marker in str(row.get("body", "")) and (row.get("user") or {}).get("login") == login for row in comments):
        return
    gh.comment(number, f"Merge queue keeper: #{number} was not queued because {reason}.{detail}\n\n{marker}")
    comments.append({"body": marker, "user": {"login": login}})


def _drop_detail(gh: GitHub, number: int, head: str, since: str) -> tuple[str, list[str]]:
    events = [
        item
        for item in gh.timeline(number)
        if item.get("event") == "removed_from_merge_queue" and item.get("created_at", "") >= since
    ]
    if not events:
        return "", []
    runs = [
        item
        for item in gh.runs(since)
        if item.get("event") == "merge_group"
        and item.get("conclusion") == "failure"
        and item.get("created_at", "") >= since
        and extract_pr_number(str(item.get("head_branch", ""))) == number
    ]
    if not runs:
        return " Queue removal confirmed; failing merge_group run unknown.", []
    run = max(runs, key=lambda item: item.get("created_at", ""))
    if not isinstance(run.get("id"), int):
        return " Queue removal confirmed; failing merge_group run id unknown.", []
    jobs = gh.jobs(run["id"])
    failed = sorted(
        {str(job["name"]) for job in jobs if job.get("conclusion") == "failure" and isinstance(job.get("name"), str)}
    )
    return (
        f" Failing merge_group: {run.get('html_url', 'unknown')}; failing jobs: {', '.join(failed) or 'unknown'}.",
        failed,
    )


def run(
    gh: GitHub, state_path: Path, *, apply: bool = False, requeue_gate: Path | None = None
) -> tuple[list[str], bool]:
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
    grants = _requeue_grants(requeue_gate)
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
            comments, verdict, checks, check_rows = [], Verdict("unknown"), "CI-unknown", []
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
        if dropped:
            dropped_head = previous["queued"][key]
            previous.setdefault("undiagnosed", {}).setdefault(f"{number}:{dropped_head}", previous.get("observed", ""))
        else:
            dropped_head = head
        prior_drop_key = f"{number}:{dropped_head}"
        if queued is False and prior_drop_key in previous.get("undiagnosed", {}):
            try:
                detail, failed_jobs = _drop_detail(gh, number, head, previous["undiagnosed"][prior_drop_key])
                if detail:
                    previous["undiagnosed"].pop(prior_drop_key)
                    previous["drops"][prior_drop_key] = int(previous["drops"].get(prior_drop_key, 0)) + 1
                    if dropped_head == head:
                        drops = previous["drops"][drop_key]
                else:
                    detail = " Queue removal diagnosis unknown."
            except KeeperError:
                detail = " Queue removal diagnosis unknown."
        reason = _reason(pr, verdict, checks, drops, queue_enabled)
        if reason == "ready" and queued is not True and not armed:
            try:
                reason = _gate_hold(gh, number, head, drops, grants, previous) or reason
            except KeeperError:
                reason = "requeue-unknown"
        rollup = [
            {
                "name": item.get("name"),
                "status": str(item.get("status", "")).upper(),
                "conclusion": str(item.get("conclusion", "")).upper(),
                "startedAt": item.get("started_at") or item.get("created_at"),
            }
            for item in check_rows
            if isinstance(item, dict)
        ]
        report = classify_pr(
            {**pr, "statusCheckRollup": rollup},
            verdict,
            queued=queued if isinstance(queued, bool) else None,
            observed_at=observed,
        )
        state = "ready" if reason == "ready" and not queued and not armed else report.state
        lines.append(f"#{number} head={head[:12]} state={state} reason={reason} queued={queued} armed={armed}")
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
        try:
            current_verdict = Verdict("unknown")
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
                    current_comments, current_verdict = [], Verdict("unknown")
                    comment_safe = False
                    verdict_lookup_ok = False
                else:
                    verdict_lookup_ok = True
                    comments = current_comments
                    comment_safe = True
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
                    reason = _gate_hold(gh, number, head, drops, grants, previous) or reason
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
                    lines.append(f"#{number} revoked: {revoke}")
                    if queued is True:
                        queued_now.pop(key, None)
                    if revoke == "squash-text-blocked":
                        previous.setdefault("squash_revoked", {})[drop_key] = observed
                    if revoke == "needs-CF" and comment_safe:
                        _comment_once(gh, number, head, revoke, comments, login, detail)
                    estimated_remaining -= 30
                elif reason != "ready":
                    lines.append(f"#{number} held: {reason}")
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
                if grants is not None and drops >= 1:
                    previous.setdefault("requeued", {})[drop_key] = observed
                estimated_remaining -= 30
            if (
                reason not in {"ready", "needs-CF", "CF-unknown", "fresh-evidence-unknown", "fresh-read-unknown"}
                and reason not in QUIET_GATE_REASONS
                and comment_safe
                and (_ever_approved(comments, login) or dropped)
            ):
                _comment_once(gh, number, head, reason, comments, login, detail)
            elif reason != "ready" and dropped and detail and comment_safe:
                _comment_once(gh, number, head, "queue-drop", comments, login, detail)
            for job in failed_jobs:
                previous.setdefault("failures", []).append({"job": job, "pr": number, "at": observed})
        except KeeperError as exc:
            failed = True
            lines.append(f"#{number} FAILED: {exc}")
        budget = estimated_remaining - 30 >= FLOOR
    if apply:
        previous["queued"] = queued_now
        previous["approved"] = approved_now
        previous["observed"] = observed
        for name in ("requeued", "squash_revoked", "undiagnosed"):
            if name in previous:
                previous[name] = {
                    item: value for item, value in previous[name].items() if item.split(":", 1)[0] in open_numbers
                }
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        failures = [
            item
            for item in previous.get("failures", [])
            if isinstance(item, dict) and isinstance(item.get("at"), str) and item["at"] >= cutoff.isoformat()
        ]
        previous["failures"] = failures
        by_job: dict[str, set[int]] = defaultdict(set)
        for item in failures:
            by_job[str(item["job"])].add(int(item["pr"]))
        for job, numbers in by_job.items():
            if len(numbers) < 2 or not budget:
                continue
            title = f"Merge queue flaky test: {job}"
            try:
                issues = gh.issues(title)
                if not any(item.get("title") == title for item in issues):
                    gh.create_issue(
                        title,
                        f"{job} failed merge_group runs on distinct PRs {', '.join(f'#{n}' for n in sorted(numbers))} within 24 hours.",
                    )
            except KeeperError as exc:
                failed = True
                lines.append(f"flaky-test issue FAILED: {exc}")
        _save(state_path, previous)
    return lines, failed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guard and replenish approved, green pull requests in configured merge queues.\nUse --report to inspect and --apply only for authorized local scheduling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.merge_queue_keeper --report\n  .venv/bin/python -m scripts.orchestration.merge_queue_keeper --apply\nHold mechanisms: labels (needs-operator-go, hold, do-not-merge, blocked) and the [hold] or [needs operator go] title marker.\nOutputs: PR states; --apply also mutates queue/comments and local batch_state.\nEnvironment: MQ_KEEPER_REQUEUE_GATE=<decision file> re-enqueues an ejected head once, only with a grant; MQ_KEEPER_MIN_INTERVAL_SECONDS or an existing MQ_KEEPER_SLOW_FLAG file (300 s) throttles --apply.\nExit codes: 0 success/lock overlap/slow-mode skip; 1 lookup or mutation failure.\nRelated: #8564, integration_sweep.py, record_cf_verdict.py.",
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
    gate_value = os.environ.get(REQUEUE_GATE_ENV, "").strip()
    requeue_gate = Path(gate_value) if gate_value else None
    if not args.apply:
        try:
            lines, failed = run(
                GitHub(root, args.repo),
                root / "batch_state/merge_queue_keeper.json",
                apply=False,
                requeue_gate=requeue_gate,
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
            lines, failed = run(GitHub(root, args.repo), state_path, apply=args.apply, requeue_gate=requeue_gate)
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
