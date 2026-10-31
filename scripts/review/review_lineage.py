"""A PR's review lineage: every review run on record and every verdict published for it.

Rule (designated approval: CTO proposal, Sol 6.1 APPROVE, advisory task
cto-7eba-adv-carryover2, condition 4): every review task of the PR is terminal,
every review verdict is published and matches its run, and the approved head's
APPROVE is the latest verdict of every reviewer seat. Unknown, unpublished or
in-flight evidence refuses. A finished run whose verdict was never published
stops refusing only when its seat recorded a later verdict at another head
(:func:`superseded_runs`; designated approval: CTO proposal, Sol 6.1 APPROVE
WITH CHANGES, advisory task cto-e08a-advlineage-sol). A finished run whose
only outcome is a published capability failure
(``scripts/review/capability_failure.py``) has no verdict and fills no seat.
The approval carry-over and the repair-verification round
(``scripts/review/repair_round.py``) both apply it before anything else. Ported from the carry-over's reviewed reader (#11907) so the two
share one implementation.

Cooperative threat model, as in ``scripts/agent_runtime/bounded_advisory.py``:
a process that can rewrite task records or edit comments as the recorder's
login is outside it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.dispatcher.admission import review_typed
from scripts.guardrails.delegate_ownership import TERMINAL_TASK_STATUSES
from scripts.opsec.prepublish import normalize_repository
from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX,
    REJECTED,
    SHA,
    TRUSTED_ASSOCIATIONS,
    lookup_verdict,
    parse_marker,
)
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME, read_task_record
from scripts.review import capability_failure
from scripts.review import record_cf_verdict as recorder
from scripts.review.capability_failure import run_started as _started
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.reviewer_resolver import resolve_family
from scripts.review.ukrainian_seats import (
    UKRAINIAN_SEAT_FAMILIES,
    attested_author_families,
    required_ukrainian_seats,
)
from scripts.review.verdict_parser import recognized_verdicts

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


def review_records(task_root: Path, *, repository: str) -> list[tuple[Path, dict[str, Any]]]:
    """Every hot and archived review task record of this repository, with its path."""
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise LineageRefused(f"task ledger unavailable: {exc}") from None
    records = []
    for path in paths:
        try:
            record = read_task_record(path)
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
        records.append((path, record))
    return records


def lineage_runs(
    task_root: Path,
    *,
    repository: str,
    number: int | None,
    branch: str | None,
    records: Sequence[tuple[Path, Mapping[str, Any]]] | None = None,
) -> list[ReviewRun]:
    """Every hot and archived review run of this PR; an archived run is kept beside a hot one.

    A run belongs to the PR by its recorded ``pr`` or its review branch; a caller that knows
    only one of them passes None for the other. ``records`` is the caller's own
    :func:`review_records` read, when it has one.
    """
    if records is None:
        records = review_records(task_root, repository=repository)
    return [
        _read_run(path, record)
        for path, record in records
        if (number is not None and record.get("pr") == number) or branch in _review_branches(record)
    ]


def _trusted_markers(
    comments: Sequence[Mapping[str, Any]], login: str, *, strict: bool = True
) -> list[tuple[tuple[str, str], dict[str, Any]]]:
    """The intact, attested verdict markers ``login`` posted; a damaged one refuses, or is skipped unless ``strict``."""
    markers = []
    for index, comment in enumerate(comments):
        body = comment.get("body") if isinstance(comment, Mapping) else None
        if not isinstance(body, str):
            if strict:
                raise LineageRefused(f"PR comment {index} malformed")
            continue
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
            problem = f"unreadable verdict marker in comment {ref}"
        elif comment.get("created_at") != comment.get("updated_at"):
            problem = f"verdict marker in comment {ref} was edited"
        elif marker["family"] in UNATTESTED_FAMILIES or resolve_family(marker["model"]) != marker["family"]:
            problem = f"verdict marker in comment {ref} has no attested reviewer family"
        else:
            markers.append(((marker["started"], str(comment.get("created_at"))), marker))
            continue
        if strict:
            raise LineageRefused(problem)
    return markers


def _profile(item: Mapping[str, Any]) -> str:
    """The normalized review profile of a run record or a verdict marker."""
    return "ukrainian" if is_ukrainian_review(item) else "code"


def _finished_verdict(run: ReviewRun) -> tuple[str, str, int | str, str, str, str] | None:
    """Head, verdict, finding count, reviewer model and family, and start of a finished run whose evidence holds.

    The head obeys the recorder's own rules: a full SHA, and the pinned head when one is recorded.
    """
    started = _started(run.record)
    sha = run.record.get("worktree_base_sha")
    if (
        run.record.get("status") != "done"
        or run.reply is None
        or started is None
        or not isinstance(sha, str)
        or not SHA.fullmatch(sha)
        or run.record.get("pinned_head") not in (None, sha)
    ):
        return None
    try:
        verdict, findings = recorder._review_verdict_and_count(run.reply)
        model, family = recorder.reviewer_identity(run.record)
    except recorder.RecordError:
        return None
    return sha, verdict, findings, model, family, started


def _supersede(
    runs: Sequence[ReviewRun], markers: Sequence[Mapping[str, Any]], events: set[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Each finished, unpublished, unclassified run that a later verdict of its own seat supersedes."""
    witnesses = []
    orphans = []
    for run in runs:
        evidence = _finished_verdict(run)
        if evidence is None:
            continue
        sha, verdict, findings, model, family, started = evidence
        profile = _profile(run.record)
        published = [m for m in markers if m["task"] == run.task_id and m["started"] == started]
        if published:
            # A witness's published verdict is exactly what its own record re-derives.
            if all(
                (m["sha"], m["verdict"], m["model"], m["family"], _profile(m)) == (sha, verdict, model, family, profile)
                for m in published
            ):
                witnesses.append(
                    {
                        "task": run.task_id,
                        "started": started,
                        "head": sha,
                        "verdict": verdict,
                        "model": model,
                        "family": family,
                        "profile": profile,
                    }
                )
        elif (run.task_id, started) not in events:
            orphans.append(
                {
                    "task": run.task_id,
                    "started": started,
                    "head": sha,
                    "verdict": verdict,
                    "findings": findings,
                    "model": model,
                    "family": family,
                    "profile": profile,
                }
            )
    superseded = []
    for orphan in sorted(orphans, key=lambda item: item["started"]):
        later = [
            witness
            for witness in witnesses
            if (witness["family"], witness["profile"]) == (orphan["family"], orphan["profile"])
            and witness["head"] != orphan["head"]
            and witness["started"] > orphan["started"]
        ]
        if later:
            # The seat's latest recorded verdict is the one that counts.
            witness = max(later, key=lambda item: item["started"])
            superseded.append(
                {
                    **orphan,
                    "superseded_by": {key: witness[key] for key in ("task", "started", "head", "verdict", "model")},
                }
            )
    return superseded


def superseded_runs(
    *, runs: Sequence[ReviewRun], comments: Sequence[Mapping[str, Any]], login: str, exclude_head: str | None = None
) -> list[dict[str, Any]]:
    """Finished runs whose verdict was never published and that a later verdict of their seat supersedes.

    A seat is a reviewer family with a normalized review profile, and its
    latest recorded verdict is the one that counts (review-loop policy). The
    witness is a finished run whose intact published verdict matches its own
    record, from the same seat, at a different head, started strictly later.
    A run with a capability-failure event, a run whose reply, verdict or
    reviewer identity does not hold, and everything at ``exclude_head`` (the
    round being recorded) neither is superseded nor supersedes. Each entry
    names the run, its pinned head, its unpublished verdict and finding count,
    and the witness. The superseded run's head stays a reviewed head, and its
    findings stay in the ledger: supersession resolves none of them.
    """
    markers = [m for _, m in _trusted_markers(comments, login, strict=False) if m["sha"] != exclude_head]
    try:
        events = {(e.task, e.started) for e in capability_failure.events(comments, login) if e.sha != exclude_head}
    except recorder.RecordError:
        # Unreadable events classify no run here, so more heads count; check_lineage refuses them.
        events = set()
    runs = [run for run in runs if exclude_head is None or run.record.get("worktree_base_sha") != exclude_head]
    return _supersede(runs, markers, events)


def dispatched_rounds(
    *, runs: Sequence[ReviewRun], comments: Sequence[Mapping[str, Any]], login: str, exclude_head: str | None = None
) -> dict[str, list[str]]:
    """Each head a review run on record was dispatched at, with its runs' task ids, recorded or not (#12098).

    A round is one reviewer dispatch at one exact head (review-loop policy), so a run counts from its
    dispatch, whatever its status and whether its verdict was ever published. A writing task is not
    a reviewer dispatch, and a run whose published capability failure classifies it opens no round.
    ``exclude_head`` drops the round being decided.
    """
    try:
        events = {(e.task, e.started) for e in capability_failure.events(comments, login)}
    except recorder.RecordError:
        # Unreadable events classify no run here, so more heads count; check_lineage refuses them.
        events = set()
    rounds: dict[str, list[str]] = {}
    for run in runs:
        head = run.record.get("worktree_base_sha")
        if not isinstance(head, str) or not SHA.fullmatch(head) or head == exclude_head:
            continue
        if run.record.get("mode") == "workspace-write":
            continue
        if (run.task_id, _started(run.record)) not in events:
            rounds.setdefault(head, []).append(run.task_id)
    return rounds


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
    must match its published marker, unless a later verdict of its seat
    supersedes it (:func:`superseded_runs`), and any other run's reply must
    carry no verdict at all. A finished run may instead have exactly one capability-failure
    event that its record and reply re-derive (``capability_failure.require_bound``),
    never beside a published verdict. ``exclude_head`` drops the runs, verdicts
    and events of one later head, the round being recorded, which is not part of
    the lineage before it.
    """
    markers = [item for item in _trusted_markers(comments, login) if item[1]["sha"] != exclude_head]
    try:
        failures = [event for event in capability_failure.events(comments, login) if event.sha != exclude_head]
    except recorder.RecordError as exc:
        raise LineageRefused(str(exc)) from None
    runs = [run for run in runs if exclude_head is None or run.record.get("worktree_base_sha") != exclude_head]
    superseded = {
        (item["task"], item["started"])
        for item in _supersede(runs, [m for _, m in markers], {(e.task, e.started) for e in failures})
    }
    claimed: set[tuple[str, str]] = set()
    classified: set[tuple[str, str]] = set()
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
        started = _started(run.record)
        published = [m for _, m in markers if m["task"] == run.task_id and m["started"] == started]
        try:
            events = capability_failure.run_events(failures, run.task_id, started)
            if events and published:
                raise LineageRefused(f"review task {run.task_id} has both a published verdict and a capability failure")
            if events:
                capability_failure.require_bound(events[0], run.task_id, run.record, run.reply)
                classified.add((run.task_id, events[0].started))
                continue
            verdict = recorder._review_verdict_and_count(run.reply)[0]
            # The recorder's own attestation and formal-reviewer rules decide who reviewed.
            model, family = recorder.reviewer_identity(run.record)
        except LineageRefused:
            raise
        except recorder.RecordError as exc:
            raise LineageRefused(f"review task {run.task_id} evidence refused: {exc}") from None
        if not published:
            if (run.task_id, started) in superseded:
                continue
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
    for event in failures:
        if (event.task, event.started) not in classified:
            raise LineageRefused(f"capability failure of task {event.task} has no finished review run on record")
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
    if ukrainian:
        approving = {
            family
            for family, marker in latest.items()
            if marker["sha"] == approved
            and marker["verdict"] not in REJECTED
            and family in UKRAINIAN_SEAT_FAMILIES
            and is_ukrainian_review(marker)
        }
        head_markers = [
            marker for _, marker in markers if marker["sha"] == approved and is_ukrainian_review(marker)
        ]
        missing = sorted(required_ukrainian_seats(attested_author_families(head_markers)) - approving)
        if missing:
            raise LineageRefused(
                f"{len(approving)} Ukrainian seat(s) approved {approved}; missing {','.join(missing)}"
            )
    elif not seats:
        raise LineageRefused(f"0 seat(s) approved {approved}; this profile requires 1")
    return seats
