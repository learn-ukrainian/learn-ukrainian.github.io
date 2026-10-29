"""A PR's review lineage: every review run on record and every verdict published for it.

Rule (designated approval: CTO proposal, Sol 6.1 APPROVE, advisory task
cto-7eba-adv-carryover2, condition 4): every review task of the PR is terminal,
every review verdict is published and matches its run, and the approved head's
APPROVE is the latest verdict of every reviewer seat. Unknown, unpublished or
in-flight evidence refuses. The approval carry-over and the repair-verification
round (``scripts/review/repair_round.py``) both apply it before
anything else. Ported from the carry-over's reviewed reader (#11907) so the two
share one implementation.

Cooperative threat model, as in ``scripts/agent_runtime/bounded_advisory.py``:
a process that can rewrite task records or edit comments as the recorder's
login is outside it.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.dispatcher.admission import review_typed
from scripts.guardrails.delegate_ownership import TERMINAL_TASK_STATUSES
from scripts.opsec.prepublish import normalize_repository
from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX,
    REJECTED,
    TRUSTED_ASSOCIATIONS,
    lookup_verdict,
    parse_marker,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.review import record_cf_verdict as recorder
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.reviewer_resolver import resolve_family
from scripts.review.verdict_parser import recognized_verdicts

# A learner-facing Ukrainian change seats two reviewers from two families
# (review-loop references/ukrainian.md § Seats); every other profile seats one.
UKRAINIAN_SEATS = 2
UNATTESTED_FAMILIES = frozenset({"unknown", "unattested", "ambiguous", "conflicting"})


class LineageRefused(recorder.RecordError):
    """The review lineage does not prove the approved head's APPROVE is current."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"LINEAGE_REFUSED: {detail}")
        self.detail = detail


def _is_review_task(task: Mapping[str, Any]) -> bool:
    """Whatever dispatch types as a review (``admission.review_typed``), plus legacy review markers.

    An advisory decision (``advisory_role``) is not a review; its consumer checks it.
    """
    if task.get("advisory_role") is not None:
        return False
    return review_typed(dict(task)) or bool(task.get("review_mode") or task.get("type") == "review")


def _review_branches(task: Mapping[str, Any]) -> set[Any]:
    """The branch identities the recorder reads for this run (``record_cf_verdict._review_branch``)."""
    fields = ("review_branch",) if task.get("schema_version") == 2 else ("review_branch", "worktree_branch")
    return {task.get(field) for field in fields if task.get(field) is not None}


@dataclass(frozen=True)
class ReviewRun:
    """One dispatch run of a review task: its record and its reply, read together."""

    task_id: str
    record: Mapping[str, Any]
    reply: str | None


def _read_run(path: Path, record: Mapping[str, Any]) -> ReviewRun:
    """Read one run's reply, refusing a reply its record's digest disowns.

    The run is named by its recorded task id, which its published verdict
    names; an archived record's file name carries an archive stamp. Its reply
    is always the ``<stem>.result`` beside it (``stale_task_records._sidecar_names``),
    never another run's reply under the bare task id.
    """
    recorded = record.get("task_id")
    task_id = recorded if isinstance(recorded, str) and recorded else path.stem
    result = path.with_suffix(".result")
    try:
        raw = result.read_bytes() if result.exists() else None
    except OSError as exc:
        raise LineageRefused(f"review task {task_id} reply unreadable: {exc}") from None
    expected = record.get("result_sha256")
    if raw is not None and expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise LineageRefused(f"review task {task_id} reply does not match its recorded digest")
    try:
        reply = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n") if raw is not None else None
    except UnicodeDecodeError:
        raise LineageRefused(f"review task {task_id} reply is not UTF-8") from None
    return ReviewRun(task_id, record, reply)


def lineage_runs(task_root: Path, *, repository: str, number: int, branch: str) -> list[ReviewRun]:
    """Every hot and archived review run of this PR; an archived run is kept beside a hot one."""
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise LineageRefused(f"task ledger unavailable: {exc}") from None
    runs = []
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LineageRefused(f"task record {path.name} unreadable: {exc}") from None
        if (
            not isinstance(record, dict)
            or record.get("status") in {"dry_run", "dry-run"}
            or not _is_review_task(record)
        ):
            continue
        if not isinstance(record.get("repository"), str) or normalize_repository(
            record["repository"]
        ) != normalize_repository(repository):
            continue
        if record.get("pr") == number or branch in _review_branches(record):
            runs.append(_read_run(path, record))
    return runs


def _started(record: Mapping[str, Any]) -> str | None:
    """The run's start as the recorder writes it into a marker."""
    try:
        started = datetime.fromisoformat(str(record.get("started_at") or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if started.tzinfo is None:
        return None
    return started.astimezone(UTC).isoformat(timespec="microseconds")


def _trusted_markers(comments: Sequence[Mapping[str, Any]], login: str) -> list[tuple[tuple[str, str], dict[str, Any]]]:
    markers = []
    for index, comment in enumerate(comments):
        body = comment.get("body") if isinstance(comment, Mapping) else None
        if not isinstance(body, str):
            raise LineageRefused(f"PR comment {index} malformed")
        if MARKER_PREFIX not in body:
            continue
        if (
            comment.get("user", {}).get("login") != login
            or comment.get("author_association") not in TRUSTED_ASSOCIATIONS
        ):
            continue
        marker = parse_marker(body)
        ref = comment.get("id", index)
        if marker is None:
            raise LineageRefused(f"unreadable verdict marker in comment {ref}")
        if comment.get("created_at") != comment.get("updated_at"):
            raise LineageRefused(f"verdict marker in comment {ref} was edited")
        if marker["family"] in UNATTESTED_FAMILIES or resolve_family(marker["model"]) != marker["family"]:
            raise LineageRefused(f"verdict marker in comment {ref} has no attested reviewer family")
        markers.append(((marker["started"], str(comment.get("created_at"))), marker))
    return markers


def check_lineage(
    *,
    runs: Sequence[ReviewRun],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    approved: str,
    exclude_head: str | None = None,
) -> list[str]:
    """Return the seats (reviewer families) whose latest verdict is the approved head's APPROVE.

    Every published verdict must belong to a run on record, and every run must
    be terminal with a reply: a finished run's verdict, model, family and start
    must match its published marker, and any other run's reply must carry no
    verdict at all. ``exclude_head`` drops the runs and verdicts of one later
    head, the round being recorded, which is not part of the lineage before it.
    """
    markers = [item for item in _trusted_markers(comments, login) if item[1]["sha"] != exclude_head]
    runs = [run for run in runs if exclude_head is None or run.record.get("worktree_base_sha") != exclude_head]
    claimed: set[tuple[str, str]] = set()
    for run in runs:
        status = run.record.get("status")
        if status not in TERMINAL_TASK_STATUSES:
            raise LineageRefused(f"review task {run.task_id} is not terminal (status {status!r})")
        if run.reply is None:
            raise LineageRefused(f"review task {run.task_id} ({status}) has no reply on record")
        if status != "done":
            if recognized_verdicts(run.reply):
                raise LineageRefused(f"review task {run.task_id} ({status}) carries an unpublished verdict")
            continue
        try:
            verdict = recorder._review_verdict_and_count(run.reply)[0]
            # The recorder's own attestation and formal-reviewer rules decide who reviewed.
            model, family = recorder.reviewer_identity(run.record)
        except recorder.RecordError as exc:
            raise LineageRefused(f"review task {run.task_id} evidence refused: {exc}") from None
        started = _started(run.record)
        published = [m for _, m in markers if m["task"] == run.task_id and m["started"] == started]
        if not published:
            raise LineageRefused(f"review task {run.task_id} finished but its verdict is unpublished")
        for marker in published:
            if (
                marker["sha"] != run.record.get("worktree_base_sha")
                or marker["verdict"] != verdict
                or marker["model"] != model
                or marker["family"] != family
            ):
                raise LineageRefused(f"published verdict of {run.task_id} conflicts with its task record")
        claimed.add((run.task_id, started))
    for _, marker in markers:
        if (marker["task"], marker["started"]) not in claimed:
            raise LineageRefused(f"published verdict of task {marker['task']} has no review run on record")
    current = lookup_verdict(list(comments), approved, login)
    if current.state != "APPROVED":
        raise LineageRefused(f"approved head {approved} reads as {current.state}, not APPROVED")
    latest: dict[str, dict[str, Any]] = {}
    for _, marker in sorted(markers, key=lambda item: item[0]):
        latest[marker["family"]] = marker
    for family, marker in sorted(latest.items()):
        if marker["sha"] != approved or marker["verdict"] in REJECTED:
            raise LineageRefused(
                f"seat {family}'s latest verdict is {marker['verdict']} at {marker['sha']}, not A's APPROVE"
            )
    seats = sorted(latest)
    ukrainian = any(marker["sha"] == approved and is_ukrainian_review(marker) for _, marker in markers) or any(
        run.record.get("worktree_base_sha") == approved and is_ukrainian_review(run.record) for run in runs
    )
    required = UKRAINIAN_SEATS if ukrainian else 1
    if len(seats) < required:
        raise LineageRefused(f"{len(seats)} seat(s) approved {approved}; this profile requires {required}")
    return seats
