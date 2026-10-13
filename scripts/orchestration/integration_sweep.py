#!/usr/bin/env python3
"""Read-only, exact-head PR landing report. The local keeper owns mutations (#8564).

Approval needs a published marker *and* the recorder's receipt in the review
task record (#10501). The receipt is same-user traceability evidence: it stops
accidental and supported-path bypasses, not a same-user writer who edits task
records or code. Isolated, unmintable review authority is separate later work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.ci.advisory_checks import is_advisory, load_advisory_checks
from scripts.common.github_client import GitHubRateLimited, timer
from scripts.github_check_rollup import group_collapsed_by_name
from scripts.opsec.prepublish import normalize_repository
from scripts.orchestration.task_record_store import locate_task_record
from scripts.publish.github import Request, request_run
from scripts.review.language_lane import is_ukrainian_review

Runner = Callable[[list[str]], str]
SHA = re.compile(r"[0-9a-f]{40}\Z")
MARKER = re.compile(
    r"<!-- cf-verdict v1 sha=(?P<sha>[0-9a-f]{40}) task=(?P<task>[^\s]+) "
    r"started=(?P<started>[^\s]+) verdict=(?P<verdict>APPROVED|APPROVE|CHANGES_REQUESTED|BLOCKED) "
    r"model=(?P<model>[^\s]+) family=(?P<family>[^\s]+)(?: review_mode=(?P<review_mode>red_team))?"
    r"(?: unknown_history=(?P<unknown_history>[0-9a-f]{40}(?:,[0-9a-f]{40})*))?"
    r"(?: review_profile=(?P<review_profile>ukrainian))?(?: sources_calls=(?P<sources_calls>[0-9]+))? -->\Z"
)
MARKER_PREFIX = "<!-- cf-verdict"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
REJECTED = frozenset({"CHANGES_REQUESTED", "BLOCKED"})
# The recorder normalizes APPROVE to APPROVED, but older trailers carry the reviewer's raw token (#10119).
VERDICT_ALIASES = {"APPROVE": "APPROVED"}
SUCCESSFUL = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
REQUIRED_CHECKS = ("CI Gate",)
DEFAULT_GH_TIMEOUT_SECONDS = 60.0
# The recorder's publication receipt inside the review task record (#10501).
RECEIPT_FIELD = "cf_recording"
RECEIPT_SCHEMA = "cf-recording.v1"
ACTIVE_TASK_STATUSES = frozenset({"spawning", "running", "queued"})
# Approval states that block admission without revoking a queued head.
UNRECEIPTED = "CF-unreceipted"
IN_FLIGHT = "CF-in-flight"


class SweepError(RuntimeError):
    """An authoritative lookup failed; no landing decision can follow."""


def comment_digest(body: str) -> str:
    """SHA-256 of a published comment body, the receipt's content binding."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def build_receipt(
    *,
    repository: str,
    pr: int,
    head_sha: str,
    task_id: str,
    run_nonce: str,
    model: str,
    family: str,
    verdict: str,
    review_mode: str,
    comment_id: int,
    body: str,
) -> dict[str, Any]:
    """The ``cf_recording`` value the recorder stores after a verified comment readback."""
    return {
        "schema": RECEIPT_SCHEMA,
        "repository": normalize_repository(repository),
        "pr": pr,
        "head_sha": head_sha,
        "task_id": task_id,
        "run_nonce": run_nonce,
        "model": model,
        "family": family,
        "verdict": verdict,
        "review_mode": review_mode,
        "comment_id": comment_id,
        "comment_sha256": comment_digest(body),
    }


def default_tasks_dir(repo_root: Path) -> Path:
    """The primary checkout's task ledger, also when run from a linked worktree."""
    try:
        common = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise SweepError("task ledger location unknown") from exc
    return Path(common).parent / "batch_state" / "tasks"


REVIEW_HEAD_FIELDS = ("pinned_head", "worktree_base_sha", "review_head", "review_head_sha", "pr_head_sha", "head_sha")


def active_review_heads(tasks_dir: Path, repository: str) -> tuple[frozenset[str], frozenset[str]]:
    """Heads targeted by active non-red-team reviews, and (casefolded) by any dispatch preparing them.

    Reads the hot ledger only: an archived record is terminal. An unreadable
    directory or record raises ``OSError``/``ValueError``/``TypeError`` so
    every caller fails closed.
    """
    reviewed: set[str] = set()
    prepared: set[str] = set()
    wanted = normalize_repository(repository)
    # The shared iterator suppresses enumeration errors. Read locally so both
    # an unreadable directory and a failed glob refuse this guard.
    list(tasks_dir.iterdir())
    for path in sorted(path for path in tasks_dir.glob("*.json") if path.is_file()):
        task = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(task, dict):
            raise ValueError("task record is not an object")
        if task.get("status") not in ACTIVE_TASK_STATUSES or task.get("review_mode", "cross_family") == "red_team":
            continue
        owner = task.get("repository")
        same_repository = isinstance(owner, str) and normalize_repository(owner) == wanted
        prep = task.get("worktree_prep")
        prep_sha = prep.get("base_sha") if isinstance(prep, dict) else None
        # Prep rows lack review typing and repository metadata. Fail closed:
        # even non-review dispatches preparing this head briefly block.
        if isinstance(prep_sha, str) and SHA.fullmatch(prep_sha.casefold()) and (same_repository or owner is None):
            prepared.add(prep_sha.casefold())
        review = (
            task.get("review")
            or task.get("pr") is not None
            or task.get("review_attempt")
            or task.get("require_review_verdict")
            or task.get("review_profile")
            or task.get("review_author_model")
            or task.get("review_risk")
            or task.get("type") == "review"
        )
        if review and same_repository:
            heads = [task.get(name) for name in REVIEW_HEAD_FIELDS]
            if any(value is not None and not isinstance(value, str) for value in heads):
                raise TypeError("active review head field is malformed")
            reviewed.update(value for value in heads if value is not None)
    return frozenset(reviewed), frozenset(prepared)


def outside_review_in_flight(tasks_dir: Path, repository: str, sha: str) -> bool:
    """Whether an active non-red-team review (or a dispatch preparing ``sha``) targets this head."""
    reviewed, prepared = active_review_heads(tasks_dir, repository)
    return sha in reviewed or sha.casefold() in prepared


class EvidenceUnavailable(SweepError):
    """The local review ledger could not be read; the head stays unknown."""


@dataclass
class ReviewLedger:
    """One snapshot of the local review ledger for a repository (#10501).

    The active-review scan runs at most once per object; build a new one for a
    fresh read. Task records are read fresh on every lookup, hot then archive.
    Same-user traceability only, never isolated authority.
    """

    tasks_dir: Path
    repository: str
    _active: tuple[frozenset[str], frozenset[str]] | None = field(default=None, repr=False)

    def in_flight(self, sha: str) -> bool:
        if self._active is None:
            try:
                self._active = active_review_heads(self.tasks_dir, self.repository)
            except (OSError, ValueError, TypeError) as exc:
                raise EvidenceUnavailable("review ledger unreadable") from exc
        reviewed, prepared = self._active
        return sha in reviewed or sha.casefold() in prepared

    def task(self, task_id: str) -> dict[str, Any] | None:
        """The hot or archived review task record, ``None`` when absent."""
        try:
            path = locate_task_record(self.tasks_dir, task_id)
            if path is None:
                return None
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise EvidenceUnavailable("review task record unreadable") from exc
        if not isinstance(record, dict):
            raise EvidenceUnavailable("review task record malformed")
        return record

    def evidence(self, number: int, *, historical: bool = False) -> RecordedEvidence:
        return RecordedEvidence(self, number, historical)


@dataclass(frozen=True)
class RecordedEvidence:
    """The ledger evidence one PR's verdict lookup consults.

    ``historical`` lookups ask what was recorded, so an active review does not
    hide an earlier receipted approval; admission lookups never set it.
    """

    ledger: ReviewLedger
    number: int
    historical: bool = False

    def in_flight(self, sha: str) -> bool:
        return not self.historical and self.ledger.in_flight(sha)

    def receipted(self, marker: Mapping[str, Any], comment: Mapping[str, Any]) -> bool:
        """Whether this exact comment is the recorder's verified publication for ``marker``.

        A missing record or receipt is ``False``; an unreadable record or a
        non-object receipt raises :class:`EvidenceUnavailable`.
        """
        record = self.ledger.task(marker["task"])
        if record is None or record.get(RECEIPT_FIELD) is None:
            return False
        receipt = record[RECEIPT_FIELD]
        if not isinstance(receipt, dict):
            raise EvidenceUnavailable("recorder receipt malformed")
        body, comment_id = comment.get("body"), comment.get("id")
        repository = normalize_repository(self.ledger.repository)
        run_nonce = record.get("run_nonce")
        return (
            repository != "unknown"
            and isinstance(body, str)
            and type(comment_id) is int
            and isinstance(run_nonce, str)
            and bool(run_nonce)
            and record.get("task_id") == marker["task"]
            and receipt
            == build_receipt(
                repository=repository,
                pr=self.number,
                head_sha=marker["sha"],
                task_id=marker["task"],
                run_nonce=run_nonce,
                model=marker["model"],
                family=marker["family"],
                verdict=marker["verdict"],
                review_mode=marker.get("review_mode", "cross_family"),
                comment_id=comment_id,
                body=body,
            )
        )


@dataclass(frozen=True)
class Verdict:
    state: str
    task: str | None = None
    model: str | None = None
    family: str | None = None
    started: datetime | None = None
    untrusted_markers: tuple[str, ...] = ()
    review_mode: str = "cross_family"
    unknown_history: tuple[str, ...] = ()


@dataclass(frozen=True)
class PRReport:
    number: int
    head: str
    observed_at: str
    state: str
    blockers: tuple[str, ...]
    untrusted_markers: tuple[str, ...] = ()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else None


def _field(comment: Mapping[str, Any], *keys: str) -> Any:
    return next((comment[key] for key in keys if key in comment), None)


def _author_login(comment: Mapping[str, Any]) -> str | None:
    author = _field(comment, "user", "author")
    if isinstance(author, Mapping):
        login = author.get("login")
        return login if isinstance(login, str) else None
    return None


def _terminal_marker(body: str) -> re.Match[str] | None:
    """Return the well-formed trailer when it is the body's only marker and its last line."""
    if body.count(MARKER_PREFIX) != 1:
        return None
    return MARKER.fullmatch(body.rstrip("\n").split("\n")[-1])


def _edited(comment: Mapping[str, Any]) -> bool:
    created = _timestamp(_field(comment, "created_at", "createdAt"))
    updated = _timestamp(_field(comment, "updated_at", "updatedAt"))
    return created is None or updated is None or created != updated


def parse_marker(body: str) -> dict[str, Any] | None:
    """Accept an intact terminal marker; Ukrainian reviews need positive Sources calls."""
    match = _terminal_marker(body)
    if match is None:
        return None
    item: dict[str, Any] = match.groupdict()
    sources = item["sources_calls"]
    try:
        item["sources_calls"] = int(sources) if sources is not None else None
    except ValueError:
        return None
    profile = item.pop("review_profile")
    if profile is not None:
        item["review_profile"] = profile
    prefix = body.split("<details>", 1)[0]
    ukrainian = is_ukrainian_review(item) or "Review profile: ukrainian\n" in prefix
    if ukrainian and (item["sources_calls"] is None or item["sources_calls"] <= 0):
        return None
    if profile is not None and f"Review profile: {profile}\n" not in prefix:
        return None
    if sources is not None and f"Sources MCP calls: {item['sources_calls']}\n" not in prefix:
        return None
    mode = item.pop("review_mode")
    history = item.pop("unknown_history")
    if history is not None:
        shas = history.split(",")
        if (
            mode != "red_team"
            or shas != sorted(set(shas))
            or f"Unknown history: {history}\n" not in prefix
            or "Historical authorship: unknown_historical\n" not in prefix
            or "No author model assumed.\n" not in prefix
        ):
            return None
        item["unknown_history"] = shas
    elif "Unknown history:" in prefix or "Historical authorship:" in prefix:
        return None
    if mode is not None:
        item["review_mode"] = mode
        if not body.startswith("### Adversarial red-team review\nReview mode: red_team\n"):
            return None
    elif not body.startswith("### Cross-family review\n") or "Review mode:" in body.split("<details>", 1)[0]:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}(?:Z|\+00:00)", item["started"]):
        return None
    if _timestamp(item["started"]) is None:
        return None
    if (
        f"head: {item['sha']}" not in body
        or f"Reviewer family: {item['family']}" not in body
        or f"VERDICT: {item['verdict']}" not in body
        or f"Reviewer model: {item['model']}" not in body
        or f"Task id: {item['task']}" not in body
    ):
        return None
    item["verdict"] = VERDICT_ALIASES.get(item["verdict"], item["verdict"])
    return item


def _effective_start(marker: Mapping[str, Any], comment: Mapping[str, Any]) -> datetime | None:
    """The marker's declared start, clamped to when GitHub created its comment (#10501)."""
    started = _timestamp(marker["started"])
    created = _timestamp(_field(comment, "created_at", "createdAt"))
    if started is None or created is None:
        return None
    return min(started, created)


def _verdict(state: str, item: tuple[datetime, int, dict[str, Any]], untrusted: list[str]) -> Verdict:
    start, _index, marker = item
    return Verdict(
        state,
        marker["task"],
        marker["model"],
        marker["family"],
        start,
        tuple(untrusted),
        marker.get("review_mode", "cross_family"),
        tuple(marker.get("unknown_history", ())),
    )


def lookup_verdict(
    comments: Sequence[Mapping[str, Any]] | None,
    sha: str,
    authenticated_login: str | None,
    *,
    complete: bool = True,
    evidence: RecordedEvidence | None = None,
) -> Verdict:
    """Resolve one SHA's recorded review state; the one resolver every landing decision uses.

    Precedence, independent of comment order and declared timestamps: any
    trusted same-head rejection; then malformed or edited evidence
    (``unknown``); then, with ``evidence``, an active outside review
    (``CF-in-flight``); then an approval whose recorder receipt matches
    (``APPROVED``) or none does (``CF-unreceipted``). A marker's start is
    clamped to its comment's creation time.

    ``evidence=None`` is the comment-only view for displays and secondary
    gates; queue decisions always pass :class:`RecordedEvidence`.
    """
    if not complete or not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        return Verdict("unknown")
    if not SHA.fullmatch(sha) or not authenticated_login:
        return Verdict("unknown")
    approvals: list[tuple[datetime, int, dict[str, Any]]] = []
    rejections: list[tuple[datetime, int, dict[str, Any]]] = []
    receipted: list[tuple[datetime, int, dict[str, Any]]] = []
    untrusted: list[str] = []
    legacy = False
    other_head = False
    poisoned = False
    for index, comment in enumerate(comments):
        if not isinstance(comment, Mapping):
            poisoned = True
            continue
        body = comment.get("body")
        if not isinstance(body, str):
            poisoned = True
            continue
        if MARKER_PREFIX not in body:
            if re.search(r"(?im)^\s*VERDICT:", body):
                legacy = True
            continue
        marker = parse_marker(body)
        login = _author_login(comment)
        association = _field(comment, "author_association", "authorAssociation")
        if login != authenticated_login or association not in TRUSTED_ASSOCIATIONS:
            untrusted.append(str(_field(comment, "id", "databaseId") or index))
            continue
        if marker is None:
            trailer = _terminal_marker(body)
            if (
                trailer is None
                or trailer["verdict"] != "APPROVE"
                or is_ukrainian_review(trailer.groupdict())
                or "Review profile: ukrainian\n" in body.split("<details>", 1)[0]
            ):
                poisoned = True
                continue
            # An approval trailer outside the keeper format cannot hide a rejection, so it neither
            # poisons the head nor counts as approval; an edited one still poisons it (#10119).
            if trailer["sha"] == sha and _edited(comment):
                poisoned = True
                continue
            if re.search(r"(?im)^\s*VERDICT:", body):
                legacy = True
            continue
        if marker["sha"] != sha:
            other_head = True
            continue
        start = _effective_start(marker, comment)
        if marker["family"] in {"unknown", "unattested", "ambiguous", "conflicting"} or _edited(comment):
            poisoned = True
            continue
        if start is None:
            poisoned = True
            continue
        item = (start, index, marker)
        (rejections if marker["verdict"] in REJECTED else approvals).append(item)
    if rejections:
        # Every applicable same-head rejection blocks; report the latest one.
        winner = max(rejections, key=lambda item: item[0])
        return _verdict(winner[2]["verdict"], winner, untrusted)
    if poisoned:
        return Verdict("unknown", untrusted_markers=tuple(untrusted))
    if not approvals:
        state = "CF-unrecorded" if legacy else "CF-stale" if other_head else "needs-CF"
        return Verdict(state, untrusted_markers=tuple(untrusted))
    if evidence is None:
        receipted = approvals
    else:
        try:
            if evidence.in_flight(sha):
                return Verdict(IN_FLIGHT, untrusted_markers=tuple(untrusted))
            receipted = [item for item in approvals if evidence.receipted(item[2], comments[item[1]])]
        except EvidenceUnavailable:
            return Verdict("unknown", untrusted_markers=tuple(untrusted))
    if not receipted:
        return Verdict(UNRECEIPTED, untrusted_markers=tuple(untrusted))
    return _verdict("APPROVED", max(receipted, key=lambda item: item[0]), untrusted)


def _check_row_kind(row: Mapping[str, Any]) -> str:
    """Return ``red``, ``pending``, ``unknown``, or ``green`` for one surviving row."""
    status = str(row.get("status") or row.get("state") or "").upper()
    outcome = str(row.get("conclusion") or row.get("state") or "").upper()
    if not status and not outcome:
        return "unknown"
    if status not in {"COMPLETED", "SUCCESS", "FAILURE", "ERROR"}:
        return "pending"
    if outcome not in SUCCESSFUL:
        return "red" if outcome else "pending"
    return "green"


def _check_blockers(pr: Mapping[str, Any], required: Sequence[str] = REQUIRED_CHECKS) -> list[str]:
    """Block when any non-advisory row surviving the shared collapse is red or pending.

    A missing rollup or a non-check value is still ``CI unknown``. Timestamp
    ties and same-named jobs from different workflows are not collapsed to one
    winner: one red or pending survivor fails that name.
    """
    checks = pr.get("statusCheckRollup")
    if not isinstance(checks, list):
        return ["CI unknown"]
    if any(not isinstance(check, Mapping) for check in checks):
        return ["CI unknown"]
    named, _other = group_collapsed_by_name(list(checks))
    policy = load_advisory_checks()
    grouped = {
        name: blocking_rows
        for name, rows in named.items()
        if name != "fleet/cross-family-review"
        if (
            blocking_rows := [
                row
                for row in rows
                if not is_advisory(name, workflow=row.get("workflowName") or row.get("workflow"), policy=policy)
            ]
        )
    }
    blockers = []
    for name in set(required) | set(grouped):
        versions = grouped.get(name, [])
        if not versions:
            blockers.append(f"CI pending {name}")
            continue
        kinds = {_check_row_kind(row) for row in versions}
        if "red" in kinds:
            blockers.append(f"CI red {name}")
        elif "pending" in kinds:
            blockers.append(f"CI pending {name}")
        elif "unknown" in kinds:
            blockers.append(f"CI unknown {name}")
    return sorted(blockers)


def classify_pr(pr: Mapping[str, Any], verdict: Verdict, *, queued: bool | None, observed_at: str) -> PRReport:
    """Expose a deterministic, importable state classifier for the queue keeper."""
    number = pr.get("number")
    head = pr.get("headRefOid")
    if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
        return PRReport(int(number or 0), str(head or "")[:12], observed_at, "unknown", ("invalid PR identity",))
    blockers: list[str] = []
    if pr.get("isDraft") is True:
        blockers.append("draft")
    if verdict.state != "APPROVED":
        blockers.append(verdict.state)
    blockers.extend(_check_blockers(pr))
    mergeable = str(pr.get("mergeable") or "").upper()
    if mergeable in {"CONFLICTING", "DIRTY"}:
        blockers.append("merge conflict")
    if queued is None:
        blockers.append("queue lookup unknown")
    if pr.get("isDraft") is True:
        state = "blocked draft"
    elif queued is True:
        state = "queued"
    elif pr.get("autoMergeRequest"):
        state = "armed"
    elif verdict.state == "unknown" or queued is None or "CI unknown" in " ".join(blockers):
        state = "CF-unknown" if verdict.state == "unknown" else "unknown"
    elif verdict.state in {"needs-CF", "CF-unrecorded", "CF-stale"}:
        state = verdict.state
    elif verdict.state in REJECTED:
        state = "CF-rejected"
    elif verdict.state != "APPROVED":
        state = verdict.state
    elif any(item.startswith("CI red") for item in blockers):
        state = "CI-red " + ", ".join(item.removeprefix("CI red ") for item in blockers if item.startswith("CI red"))
    elif any(item.startswith("CI pending") for item in blockers):
        state = "CI-pending"
    elif "merge conflict" in blockers:
        state = "blocked merge conflict"
    else:
        state = "ready"
    return PRReport(number, head[:12], observed_at, state, tuple(blockers), verdict.untrusted_markers)


class GitHubAdapter:
    """Read-only GitHub CLI boundary. Paged lookups use --slurp and reject malformed pages."""

    def __init__(self, repo_root: Path, *, runner: Runner | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._runner = runner or self._default_runner

    def _default_runner(self, args: list[str]) -> str:
        try:
            result = request_run(
                args,
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                timeout=DEFAULT_GH_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SweepError(
                f"{args.verb if isinstance(args, Request) else ' '.join(args[:4])} timed out after {DEFAULT_GH_TIMEOUT_SECONDS}s"
            ) from exc
        observation = getattr(result, "github_result", None)
        if observation is not None and (observation.stale or observation.error == "github_rate_limited"):
            raise GitHubRateLimited(observation.reset_at)
        if result.returncode:
            raise SweepError((result.stderr or result.stdout or "GitHub lookup failed")[:1000])
        return result.stdout

    def _json(self, args: list[str]) -> Any:
        try:
            return json.loads(self._runner(args))
        except (ValueError, TypeError) as exc:
            raise SweepError("GitHub returned invalid JSON") from exc

    def identity(self) -> str:
        login = self._json(Request("read-identity")).get("login", "").strip()
        if not login:
            raise SweepError("authenticated gh identity unavailable")
        return login

    def list_open_prs(self, repository: str) -> list[dict[str, Any]]:
        payload = self._json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,isDraft,headRefOid,headRefName,baseRefName,autoMergeRequest,statusCheckRollup,mergeable",
            ]
        )
        if not isinstance(payload, list) or len(payload) >= 1000 or not all(isinstance(item, dict) for item in payload):
            raise SweepError("open PR list partial or malformed")
        return payload

    def comments(self, repository: str, number: int) -> list[dict[str, Any]]:
        pages = self._json(Request("read-comments", repo=repository, number=number, paginate=True, slurp=True))
        if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
            raise SweepError("PR comments pagination incomplete")
        comments = [item for page in pages for item in page]
        if not all(isinstance(item, dict) for item in comments):
            raise SweepError("PR comments malformed")
        return comments

    def queue_membership(self, repository: str, pr: Mapping[str, Any]) -> bool:
        data = self._json(
            Request(
                "read-membership-head", repo=repository, number=pr["number"], branch=pr.get("baseRefName") or "main"
            )
        )
        if not isinstance(data, dict) or data.get("errors"):
            raise SweepError("merge queue GraphQL lookup incomplete")
        repo = (data.get("data") or {}).get("repository")
        node = repo.get("pullRequest") if isinstance(repo, dict) else None
        if (
            not isinstance(node, dict)
            or node.get("headRefOid") != pr.get("headRefOid")
            or not isinstance(node.get("isInMergeQueue"), bool)
        ):
            raise SweepError("merge queue head moved or membership unavailable")
        return node["isInMergeQueue"]


def run(
    adapter: GitHubAdapter, repository: str, *, tasks_dir: Path, now: datetime | None = None
) -> list[PRReport]:
    """Classify every open PR; approval needs the recorder receipt in ``tasks_dir``."""
    observed = (now or datetime.now(UTC)).isoformat(timespec="microseconds")
    prs = adapter.list_open_prs(repository)
    ledger = ReviewLedger(tasks_dir, repository)
    try:
        login = adapter.identity()
    except SweepError:
        login = None
    rows = []
    for pr in prs:
        number, head = pr.get("number"), pr.get("headRefOid")
        if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
            rows.append(classify_pr(pr, Verdict("unknown"), queued=None, observed_at=observed))
            continue
        try:
            verdict = lookup_verdict(
                adapter.comments(repository, number), head, login, evidence=ledger.evidence(number)
            )
        except SweepError:
            verdict = Verdict("unknown")
        try:
            queued = adapter.queue_membership(repository, pr)
        except (SweepError, ValueError, KeyError):
            queued = None
        rows.append(classify_pr(pr, verdict, queued=queued, observed_at=observed))
    return rows


@timer
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report exact-head PR review, CI and queue state without mutations.\n"
        "Use for landing evidence; the local keeper owns queue changes.\n"
        "Approval needs the recorder receipt in the review task record: same-user\n"
        "traceability against accidental bypass, not isolated review authority (#10501).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.integration_sweep --repo owner/repo --report\n"
        "  .venv/bin/python -m scripts.orchestration.integration_sweep --repo owner/repo --json\n"
        "Outputs: Read-only GitHub PR state report on stdout; no writes.\n"
        "Exit codes: 0: report complete; 1: lookup failed; 2: retired --apply refused.\n"
        "Related: scripts/review/record_cf_verdict.py, scripts/orchestration/merge_queue_keeper.py; #9951, #10501",
    )
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--report", action="store_true", help="Print the read-only PR state report (default behavior)")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text (default: text)")
    parser.add_argument("--apply", action="store_true", help="Retired and refused; landing is keeper-owned (default: false)")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(),
                        help="Checkout used for GitHub commands, e.g. . (default: current working directory)")
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        help="Review task ledger holding recorder receipts (default: the primary checkout's batch_state/tasks)",
    )
    args = parser.parse_args(argv)
    if args.apply:
        print("integration sweep refused: --apply is retired; this sweep is report-only")
        return 2
    try:
        tasks_dir = args.tasks_dir or default_tasks_dir(args.repo_root)
        rows = run(GitHubAdapter(args.repo_root), args.repo, tasks_dir=tasks_dir)
    except SweepError as exc:
        print(f"integration sweep refused: {exc}")
        return 1
    if args.json:
        print(json.dumps([asdict(row) for row in rows], sort_keys=True))
    else:
        for row in rows:
            blockers = ", ".join(row.blockers) or "none"
            untrusted = f" untrusted-marker={','.join(row.untrusted_markers)}" if row.untrusted_markers else ""
            print(
                f"#{row.number} head={row.head} observed_at={row.observed_at} state={row.state} blockers={blockers}{untrusted}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
