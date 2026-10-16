#!/usr/bin/env python3
"""Query and report GitHub Merge Queue status, position, ETA, and CI run for a pull request.

Answers #7814 item 13:
After `gh pr merge` enqueues into the merge queue, this helper prints queue
membership, queue position, ETA (or 'in queue, position unknown'), and the latest
`merge_group` workflow run URL so drivers do not stall on OPEN + CLEAN with only
the '! The merge strategy...' hint.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for standalone script invocation
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ci.ci_timings import (
    _gh_env,
    extract_pr_number,
    resolve_repository,
)
from scripts.common import github_client
from scripts.common import github_payload as gp
from scripts.publish.github import read


def parse_pr_identifier(value: str | int) -> int:
    """Extract integer PR number from a number, '#123', URL, or branch name."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("Empty pull request identifier provided.")
    # Match URL like https://github.com/.../pull/1234
    url_m = re.search(r"/pull/(\d+)", text)
    if url_m:
        return int(url_m.group(1))
    # Match queue branch or feature branch with PR number
    pr_num = extract_pr_number(text)
    if pr_num is not None:
        return pr_num
    # Match branch or text with prefix '#123' or 'pr123'
    m = re.search(r"(?:^|[#/_-]|pr)(\d+)(?:[#/_.-]|$)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Fallback to pure digits if present
    digits = re.findall(r"\d+", text)
    if digits:
        return int(digits[0])
    raise ValueError(f"Could not parse pull request number from: {value!r}")


def format_eta_human(seconds: int | None) -> str | None:
    """Format seconds into a concise human-readable ETA (~X min, ~Xh Ym, <1 min)."""
    if seconds is None:
        return None
    if seconds < 60:
        return "<1 min"
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"~{minutes} min"
    hours = minutes // 60
    rem_min = minutes % 60
    if rem_min == 0:
        return f"~{hours}h"
    return f"~{hours}h {rem_min}m"


def build_summary_line(
    pr_number: int,
    queued: bool,
    position: int | None,
    state: str | None,
    eta_human: str | None,
    run_url: str | None,
    pr_state: str,
    pr_merged: bool,
    merge_state_status: str | None,
) -> str:
    """Build a single deterministic human-readable status line."""
    run_part = f"run={run_url}" if run_url else "run=none"
    if queued:
        if position is not None:
            pos_part = f"position={position}"
            details: list[str] = []
            if state:
                details.append(state)
            if eta_human:
                details.append(f"{eta_human} ETA")
            detail_str = f" ({', '.join(details)})" if details else ""
            return f"PR #{pr_number}: queued=yes, {pos_part}{detail_str}, {run_part}"
        else:
            return f"PR #{pr_number}: queued=yes, position=unknown (in queue, position unknown), {run_part}"
    else:
        if pr_merged:
            return f"PR #{pr_number}: queued=no (merged=yes, state=MERGED), {run_part}"
        elif pr_state == "CLOSED":
            return f"PR #{pr_number}: queued=no (state=CLOSED), {run_part}"
        else:
            status_desc = f"state={pr_state}"
            if merge_state_status:
                status_desc += f", mergeStateStatus={merge_state_status}"
            return f"PR #{pr_number}: queued=no ({status_desc}), {run_part}"


def find_latest_merge_group_run(
    runs: list[dict[str, Any]],
    target_pr: int,
) -> dict[str, Any] | None:
    """Find the most recent merge_group workflow run for target_pr, preferring CI."""
    matching: list[dict[str, Any]] = []
    for r in runs:
        if not isinstance(r, dict):
            continue
        event = r.get("event")
        if event is not None and event != "merge_group":
            continue
        branch = r.get("head_branch") or r.get("headBranch") or ""
        if event is None and not branch.startswith("gh-readonly-queue/"):
            continue
        if extract_pr_number(branch) == target_pr:
            matching.append(r)
    if not matching:
        return None

    def _sort_key(run: dict[str, Any]) -> tuple[str, int]:
        ts = str(run.get("created_at") or run.get("createdAt") or run.get("updated_at") or run.get("updatedAt") or "")
        run_id = run.get("id") or run.get("databaseId") or 0
        try:
            numeric_id = int(run_id)
        except (ValueError, TypeError):
            numeric_id = 0
        return (ts, numeric_id)

    matching.sort(key=_sort_key, reverse=True)
    newest_created = str(matching[0].get("created_at") or matching[0].get("createdAt") or "")
    if newest_created:
        same_batch = [r for r in matching if str(r.get("created_at") or r.get("createdAt") or "") == newest_created]
    else:
        same_batch = matching
    ci_run = next((r for r in same_batch if str(r.get("name") or "").upper() == "CI"), None)
    return ci_run or matching[0]


@dataclass(frozen=True)
class MergeQueueStatus:
    pr_number: int
    queued: bool
    position: int | None
    state: str | None
    enqueued_at: str | None
    estimated_time_to_merge_seconds: int | None
    estimated_time_to_merge_human: str | None
    latest_merge_group_run_url: str | None
    latest_merge_group_run_status: str | None
    latest_merge_group_run_conclusion: str | None
    pr_state: str
    pr_merged: bool
    pr_merge_state_status: str | None
    queue_url: str | None
    summary_line: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "enqueued_at": self.enqueued_at,
            "estimated_time_to_merge_human": self.estimated_time_to_merge_human,
            "estimated_time_to_merge_seconds": self.estimated_time_to_merge_seconds,
            "latest_merge_group_run_conclusion": self.latest_merge_group_run_conclusion,
            "latest_merge_group_run_status": self.latest_merge_group_run_status,
            "latest_merge_group_run_url": self.latest_merge_group_run_url,
            "position": self.position,
            "pr_merge_state_status": self.pr_merge_state_status,
            "pr_merged": self.pr_merged,
            "pr_number": self.pr_number,
            "pr_state": self.pr_state,
            "queue_url": self.queue_url,
            "queued": self.queued,
            "state": self.state,
            "summary_line": self.summary_line,
        }


class MalformedPayload(RuntimeError):
    """A GitHub payload that is not exactly the whitelisted shape this tool consumes.

    It is an *unavailable* outcome: never a clean status, never "pull request absent", never an
    empty run list. ``reason`` is a fixed, controlled string naming the failed field.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"unavailable: malformed payload ({reason})")
        self.reason = reason


_PR_STATES = frozenset({"OPEN", "CLOSED", "MERGED"})
RUNS_PAGE_SIZE = 30  # ``per_page=30`` in the REST runs request and ``-L 30`` in the fallback
QUEUE_ENTRIES_PAGE_SIZE = 50  # ``entries(first: 50)`` in the ``queue-status`` query


def _opt_text(obj: dict[str, Any], key: str, what: str) -> str | None:
    return gp.optional(obj, key, gp.require_str, what)


def _opt_int(obj: dict[str, Any], key: str, what: str, minimum: int) -> int | None:
    return gp.optional(obj, key, gp.require_int, what, minimum=minimum)


def _run_id(value: Any, what: str) -> str | int:
    """A GraphQL run ``id`` is an opaque ID string; a REST or recorded run id is an int64."""
    if isinstance(value, str):
        return gp.require_str(value, what)
    return gp.require_int(value, what, minimum=0, maximum=gp.INT64_MAX)


@dataclass(frozen=True)
class QueueEntry:
    position: int | None
    state: str | None
    enqueued_at: str | None
    eta_seconds: int | None


def _entry(obj: dict[str, Any], what: str) -> QueueEntry:
    """The queue-position fields shared by a pull request's own entry and a queue node."""
    return QueueEntry(
        position=_opt_int(obj, "position", f"{what}.position", 1),
        state=_opt_text(obj, "state", f"{what}.state"),
        enqueued_at=_opt_text(obj, "enqueuedAt", f"{what}.enqueuedAt"),
        eta_seconds=_opt_int(obj, "estimatedTimeToMerge", f"{what}.estimatedTimeToMerge", 0),
    )


def _suite_runs(commit: dict[str, Any] | None, pr_number: int) -> tuple[dict[str, Any], ...]:
    """Candidate merge_group runs from ``headCommit.checkSuites.nodes``; every node is validated."""
    if commit is None:
        return ()
    check_suites = gp.optional(commit, "checkSuites", gp.require_object, "checkSuites")
    if check_suites is None:
        return ()
    runs: list[dict[str, Any]] = []
    for node in gp.optional(check_suites, "nodes", gp.require_list, "checkSuites.nodes") or []:
        suite = gp.require_object(node, "checkSuites.nodes[]")
        status = _opt_text(suite, "status", "checkSuite.status")
        conclusion = _opt_text(suite, "conclusion", "checkSuite.conclusion")
        suite_created = _opt_text(suite, "createdAt", "checkSuite.createdAt")
        run = gp.optional(suite, "workflowRun", gp.require_object, "workflowRun")
        if run is None:
            continue
        url = gp.require_str(gp.field(run, "url", "workflowRun.url"), "workflowRun.url")
        event = _opt_text(run, "event", "workflowRun.event")
        created = _opt_text(run, "createdAt", "workflowRun.createdAt")
        run_id = gp.optional(run, "id", _run_id, "workflowRun.id")
        workflow = gp.optional(run, "workflow", gp.require_object, "workflowRun.workflow")
        name = _opt_text(workflow, "name", "workflow.name") if workflow is not None else None
        # Filter out non-merge_group runs (e.g. stale pull_request run)
        if event and event != "merge_group":
            continue
        runs.append(
            {
                "id": run_id or 0,
                "url": url,
                "html_url": url,
                "name": name or "",
                "status": status,
                "conclusion": conclusion,
                "event": event or "merge_group",
                "head_branch": f"gh-readonly-queue/main/pr-{pr_number}-suite",
                "created_at": created or suite_created or "",
            }
        )
    return tuple(runs)


@dataclass(frozen=True)
class QueueDocument:
    """The typed fields of a GraphQL ``queue-status`` document that passed :func:`parse_queue_status`."""

    state: str
    merged: bool
    merge_state_status: str | None
    in_queue: bool
    entry: QueueEntry | None
    suite_runs: tuple[dict[str, Any], ...]
    queue_url: str | None
    next_eta_seconds: int | None
    queue_nodes: tuple[tuple[int, QueueEntry], ...]


def _queue_nodes(entries: dict[str, Any], *, consumed: bool) -> tuple[tuple[int, QueueEntry], ...]:
    """Every queue node is validated; when the tool reads them they must be the complete first page."""
    nodes = gp.optional(entries, "nodes", gp.require_list, "mergeQueue.entries.nodes")
    total = _opt_int(entries, "totalCount", "mergeQueue.entries.totalCount", 0)
    parsed = []
    for node in nodes or []:
        node = gp.require_object(node, "mergeQueue.entries.nodes[]")
        pull = gp.require_object(gp.field(node, "pullRequest", "nodes[].pullRequest"), "nodes[].pullRequest")
        number = gp.require_int(
            gp.field(pull, "number", "nodes[].pullRequest.number"), "nodes[].pullRequest.number", minimum=1
        )
        parsed.append((number, _entry(node, "mergeQueue.entries.nodes[]")))
    if consumed:
        if nodes is None or total is None:
            raise gp.UnavailablePayload("mergeQueue.entries")
        gp.require_complete_page(nodes, total, "mergeQueue.entries", page_size=QUEUE_ENTRIES_PAGE_SIZE)
    return tuple(parsed)


def _not_found_error(error: Any, pr_number: int) -> bool:
    """GitHub's own error for an unresolvable pull request, naming exactly the requested number."""
    return (
        isinstance(error, dict)
        and error.get("message") == f"Could not resolve to a PullRequest with the number of {pr_number}."
        and error.get("type", "NOT_FOUND") == "NOT_FOUND"
        and error.get("path", ["repository", "pullRequest"]) == ["repository", "pullRequest"]
    )


def _positively_not_found(document: dict[str, Any], errors: list[dict[str, Any]], pr_number: int) -> bool:
    """Every error is the not-found error for this number, and ``data.repository.pullRequest`` is null."""
    if not all(_not_found_error(error, pr_number) for error in errors):
        return False
    try:
        data = gp.require_object(gp.field(document, "data", "data"), "data")
        repository = gp.require_object(gp.field(data, "repository", "data.repository"), "data.repository")
        return gp.field(repository, "pullRequest", "data.repository.pullRequest") is None
    except gp.UnavailablePayload:
        return False


def parse_queue_status(document: Any, pr_number: int, *, repo: str | None = None) -> QueueDocument:
    """The single choke point for a GraphQL ``queue-status`` document, live or offline.

    Returns the typed fields, or raises before anything is decided:

    * ``ValueError`` - GraphQL positively reports the pull request unresolvable: every error is
      the not-found error for exactly this number and ``data.repository.pullRequest`` is null;
    * ``RuntimeError`` - GraphQL returned any other errors (a partial result is not trusted);
    * :class:`MalformedPayload` (a ``RuntimeError``) - the document is not exactly the whitelisted
      shape, or it carries failure or paging evidence anywhere outside ``errors``
      (:func:`scripts.common.github_payload.reject_failure_evidence`).
    """
    try:
        document = gp.require_object(document, "document")
        errors = gp.graphql_errors(document)
        gp.reject_failure_evidence({key: value for key, value in document.items() if key != "errors"})
        if errors:
            if _positively_not_found(document, errors, pr_number):
                raise ValueError(_not_found_message(pr_number, repo))
            raise RuntimeError(f"GraphQL error: {'; '.join(error['message'] for error in errors)}")
        return _queue_document(document, pr_number)
    except gp.UnavailablePayload as exc:
        raise MalformedPayload(exc.reason) from None


def _queue_document(document: dict[str, Any], pr_number: int) -> QueueDocument:
    data = gp.require_object(gp.field(document, "data", "data"), "data")
    repository = gp.require_object(gp.field(data, "repository", "data.repository"), "data.repository")
    pull = gp.require_object(
        gp.field(repository, "pullRequest", "data.repository.pullRequest"), "data.repository.pullRequest"
    )
    number = gp.require_int(gp.field(pull, "number", "pullRequest.number"), "pullRequest.number", minimum=1)
    if number != pr_number:
        raise gp.UnavailablePayload("pullRequest.number")
    state = gp.require_str(gp.field(pull, "state", "pullRequest.state"), "pullRequest.state")
    if state not in _PR_STATES:
        raise gp.UnavailablePayload("pullRequest.state")
    merged = gp.require_bool(gp.field(pull, "merged", "pullRequest.merged"), "pullRequest.merged")
    in_queue = gp.require_bool(
        gp.field(pull, "isInMergeQueue", "pullRequest.isInMergeQueue"), "pullRequest.isInMergeQueue"
    )
    if merged != (state == "MERGED"):
        raise gp.UnavailablePayload("pullRequest.merged/state")
    merge_state_status = _opt_text(pull, "mergeStateStatus", "pullRequest.mergeStateStatus")

    entry: QueueEntry | None = None
    suite_runs: tuple[dict[str, Any], ...] = ()
    entry_obj = gp.optional(pull, "mergeQueueEntry", gp.require_object, "mergeQueueEntry")
    if entry_obj is not None:
        if not in_queue:
            raise gp.UnavailablePayload("mergeQueueEntry/isInMergeQueue")
        entry = _entry(entry_obj, "mergeQueueEntry")
        suite_runs = _suite_runs(gp.optional(entry_obj, "headCommit", gp.require_object, "headCommit"), pr_number)

    queue_url: str | None = None
    next_eta: int | None = None
    queue_nodes: tuple[tuple[int, QueueEntry], ...] = ()
    # The queue nodes are read only to place a queued pull request that has no entry of its own.
    consumed = in_queue and entry is None
    queue = gp.optional(repository, "mergeQueue", gp.require_object, "mergeQueue")
    if queue is not None:
        queue_url = _opt_text(queue, "url", "mergeQueue.url")
        next_eta = _opt_int(queue, "nextEntryEstimatedTimeToMerge", "mergeQueue.nextEntryEstimatedTimeToMerge", 0)
        entries = gp.optional(queue, "entries", gp.require_object, "mergeQueue.entries")
        if entries is not None:
            queue_nodes = _queue_nodes(entries, consumed=consumed)
        elif consumed:
            raise gp.UnavailablePayload("mergeQueue.entries")
    return QueueDocument(
        state=state,
        merged=merged,
        merge_state_status=merge_state_status,
        in_queue=in_queue,
        entry=entry,
        suite_runs=suite_runs,
        queue_url=queue_url,
        next_eta_seconds=next_eta,
        queue_nodes=queue_nodes,
    )


def _not_found_message(pr_number: int, repo: str | None) -> str:
    return f"Pull request #{pr_number} not found in repository{f' {repo}' if repo else ''}."


def _offline_fixture_not_found(document: Any, pr_number: int) -> bool:
    """The one recorded offline-fixture contract: ``{"data": null}`` (optionally with only the
    not-found error for this number) reads as "not found". Only :func:`evaluate_status_data` calls
    it; a live read of the same document is unavailable."""
    if not isinstance(document, dict) or "data" not in document or document["data"] is not None:
        return False
    if not document.keys() <= {"data", "errors", "actions_runs"}:
        return False
    try:
        errors = gp.graphql_errors(document)
    except gp.UnavailablePayload:
        return False
    return all(_not_found_error(error, pr_number) for error in errors)


def _valid_run(run: Any, what: str) -> dict[str, Any]:
    """A usable Actions run names its page (``html_url``/``url``), its ``status`` and the head branch
    that matches it to a pull request (``head_branch``/``headBranch``); every other field the tool
    reads is null/absent or of its expected type."""
    run = gp.require_object(run, what)
    for keys in (("html_url", "url"), ("head_branch", "headBranch")):
        present = [gp.optional(run, key, gp.require_str, f"{what}.{key}") for key in keys]
        if not any(present):
            raise gp.UnavailablePayload(f"{what}.{keys[0]}")
    gp.require_str(gp.field(run, "status", f"{what}.status"), f"{what}.status")
    for key in ("conclusion", "event", "name", "created_at", "createdAt", "updated_at", "updatedAt"):
        gp.optional(run, key, gp.require_str, f"{what}.{key}", nonempty=False)
    for key in ("id", "databaseId"):
        gp.optional(run, key, gp.require_int, f"{what}.{key}", minimum=0, maximum=gp.INT64_MAX)
    return run


def parse_actions_runs(data: Any, key: str | None, *, page_size: int | None = None) -> list[dict[str, Any]]:
    """The single choke point for an Actions run list; an unavailable read is never an empty list.

    ``key`` names the list inside a REST object; ``None`` means the payload is itself a list.
    With ``page_size`` the object must declare ``total_count`` and carry the complete first page
    (:func:`scripts.common.github_payload.require_complete_page`). Failure evidence anywhere in
    the payload and any element that fails :func:`_valid_run` refuse the whole read.
    """
    try:
        gp.reject_failure_evidence(data)
        if key is None:
            runs = gp.require_list(data, "runs list")
        else:
            document = gp.require_object(data, "runs document")
            runs = gp.require_list(gp.field(document, key, "runs list"), "runs list")
            if page_size is not None:
                total = gp.require_int(
                    gp.field(document, "total_count", "runs total_count"), "runs total_count", minimum=0
                )
                gp.require_complete_page(runs, total, "runs page", page_size=page_size)
        return [_valid_run(run, "run element") for run in runs]
    except gp.UnavailablePayload as exc:
        raise MalformedPayload(exc.reason) from None


def evaluate_status_data(
    graphql_data: dict[str, Any],
    pr_number: int,
    actions_runs: list[dict[str, Any]] | None = None,
) -> MergeQueueStatus:
    """Evaluate a recorded GraphQL document and Actions runs into MergeQueueStatus (offline).

    Both inputs are validated by the same choke points as the live read; a malformed document or
    run list raises (:class:`MalformedPayload`) instead of producing a status.
    """
    if _offline_fixture_not_found(graphql_data, pr_number):
        raise ValueError(_not_found_message(pr_number, None))
    document = parse_queue_status(graphql_data, pr_number)
    runs = parse_actions_runs(actions_runs, None) if actions_runs is not None else []
    return _evaluate(document, pr_number, runs)


def _evaluate(document: QueueDocument, pr_number: int, actions_runs: list[dict[str, Any]]) -> MergeQueueStatus:
    position: int | None = None
    state: str | None = None
    enqueued_at: str | None = None
    eta_seconds: int | None = None

    if document.entry is not None:
        position = document.entry.position
        state = document.entry.state
        enqueued_at = document.entry.enqueued_at
        eta_seconds = document.entry.eta_seconds
    elif document.in_queue:
        # Check entries on mergeQueue object
        for number, node in document.queue_nodes:
            if number == pr_number:
                position = node.position
                state = node.state
                enqueued_at = node.enqueued_at
                eta_seconds = node.eta_seconds
                break
        if position is None:
            # isInMergeQueue is true but position could not be resolved from entry
            state = "QUEUED"
            if document.next_eta_seconds is not None:
                eta_seconds = document.next_eta_seconds

    # Candidate merge_group workflow runs: the check suites first, then the Actions runs
    matched_run = find_latest_merge_group_run([*document.suite_runs, *actions_runs], pr_number)
    run_url: str | None = None
    run_status: str | None = None
    run_conclusion: str | None = None

    if matched_run:
        run_url = matched_run.get("html_url") or matched_run.get("url")
        run_status = matched_run.get("status")
        run_conclusion = matched_run.get("conclusion")

    eta_human = format_eta_human(eta_seconds)
    summary_line = build_summary_line(
        pr_number=pr_number,
        queued=document.in_queue,
        position=position,
        state=state,
        eta_human=eta_human,
        run_url=run_url,
        pr_state=document.state,
        pr_merged=document.merged,
        merge_state_status=document.merge_state_status,
    )

    return MergeQueueStatus(
        pr_number=pr_number,
        queued=document.in_queue,
        position=position,
        state=state,
        enqueued_at=enqueued_at,
        estimated_time_to_merge_seconds=eta_seconds,
        estimated_time_to_merge_human=eta_human,
        latest_merge_group_run_url=run_url,
        latest_merge_group_run_status=run_status,
        latest_merge_group_run_conclusion=run_conclusion,
        pr_state=document.state,
        pr_merged=document.merged,
        pr_merge_state_status=document.merge_state_status,
        queue_url=document.queue_url,
        summary_line=summary_line,
    )


def _unavailable_message(
    what: str, proc: subprocess.CompletedProcess[str], data: Any = None, reason: str | None = None
) -> str:
    """One explicit unavailable diagnostic; only the controlled error code and reason are echoed."""
    code = data.get("error") if isinstance(data, dict) else None
    detail = f": {code}" if isinstance(code, str) and re.fullmatch(r"[a-z_]{1,64}", code) else ""
    why = f" [{reason}]" if reason else ""
    return f"{what} read unavailable (exit {proc.returncode}){detail}{why}."


def _exit_ok(proc: subprocess.CompletedProcess[str]) -> bool:
    """Exactly the int ``0``; a bool, float or string return code is not success."""
    return type(proc.returncode) is int and proc.returncode == 0


def _read_runs(
    command: list[str], env: dict[str, str], timeout: int, what: str, key: str | None
) -> list[dict[str, Any]]:
    """One Actions runs read. Any refusal or failure raises; it is never an empty list.

    The return code is checked before the output is parsed. ``key`` names the list inside a
    REST object, which must carry its complete first page of ``RUNS_PAGE_SIZE``; ``None`` means
    the output is itself a list.
    """
    try:
        proc = github_client.run(command, capture_output=True, text=True, env=env, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("`gh` CLI tool is required but not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{what} read timed out after {timeout}s.") from exc
    except OSError as exc:
        raise RuntimeError(f"{what} read could not start: {type(exc).__name__}.") from exc
    if not _exit_ok(proc):
        raise RuntimeError(_unavailable_message(what, proc))
    try:
        data = gp.decode(proc.stdout)
    except gp.UnavailablePayload as exc:
        raise RuntimeError(_unavailable_message(what, proc, reason=exc.reason)) from None
    try:
        return parse_actions_runs(data, key, page_size=None if key is None else RUNS_PAGE_SIZE)
    except MalformedPayload as exc:
        raise RuntimeError(_unavailable_message(what, proc, data, exc.reason)) from None


def fetch_live_status(
    pr_number: int,
    repo: str,
    branch: str = "main",
    token: str | None = None,
    timeout: int = 30,
) -> MergeQueueStatus:
    """Query GitHub GraphQL and Actions APIs for live merge queue status."""
    if "/" not in repo:
        raise ValueError(f"Invalid repository '{repo}'. Expected 'owner/name'.")
    owner, name = repo.split("/", 1)
    env = _gh_env(token)
    try:
        proc = read(
            "queue-status", repo=repo, number=pr_number, branch=branch,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("`gh` CLI tool is required but not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"GraphQL request timed out after {timeout}s.") from exc
    except OSError as exc:
        raise RuntimeError(f"GraphQL request could not start: {type(exc).__name__}.") from exc

    # The one parse-or-unavailable choke point: a refused read, a failed read, a partial result and
    # every malformed shape (duplicate keys included) end here, before any further request. Only a
    # positively identified missing pull request keeps its own meaning (ValueError).
    try:
        data = gp.decode(proc.stdout)
    except gp.UnavailablePayload as exc:
        raise RuntimeError(_unavailable_message("GraphQL", proc, reason=exc.reason)) from None
    try:
        document = parse_queue_status(data, pr_number, repo=repo)
    except MalformedPayload as exc:
        raise RuntimeError(_unavailable_message("GraphQL", proc, data, exc.reason)) from None
    if not _exit_ok(proc):
        raise RuntimeError(_unavailable_message("GraphQL", proc, data))

    # Fetch merge_group workflow runs. An unavailable or incomplete read raises (no fallback
    # request, never an empty list); only a successful, complete empty page falls back.
    runs_path = f"repos/{owner}/{name}/actions/runs?event=merge_group&per_page={RUNS_PAGE_SIZE}"
    actions_runs = _read_runs(["gh", "api", runs_path], env, timeout, "Actions runs", "workflow_runs")

    if not actions_runs:
        rl_cmd = [
            "gh",
            "run",
            "list",
            "-R",
            f"{owner}/{name}",
            "--event",
            "merge_group",
            "-L",
            str(RUNS_PAGE_SIZE),
            "--json",
            "url,headBranch,status,conclusion,createdAt,name,event",
        ]
        actions_runs = _read_runs(rl_cmd, env, timeout, "Actions run list", None)

    return _evaluate(document, pr_number, actions_runs)


def render_output(
    status: MergeQueueStatus,
    *,
    json_only: bool = False,
    line_only: bool = False,
) -> str:
    """Render output according to format flags."""
    json_str = json.dumps(status.to_dict(), indent=2, sort_keys=True)
    if json_only:
        return json_str
    if line_only:
        return status.summary_line
    # Default: emit JSON followed by the single human summary line
    return f"{json_str}\n{status.summary_line}"


def check_and_report_pr_status(
    pr: str | int,
    repo: str | None = None,
    branch: str = "main",
    json_only: bool = False,
    line_only: bool = False,
    fixture_file: str | Path | None = None,
    actions_fixture_file: str | Path | None = None,
    token: str | None = None,
) -> int:
    """Programmatic entry point for checking and printing PR merge queue status."""
    try:
        pr_number = parse_pr_identifier(pr)
    except ValueError as exc:
        if json_only:
            print(json.dumps({"error": str(exc), "status": "error"}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2

    resolved_repo = resolve_repository(repo)

    if fixture_file:
        try:
            # Recorded fixtures pass the same strict decoder as a live read (duplicate keys refused).
            fix_data = gp.decode(Path(fixture_file).read_text(encoding="utf-8"))
        except Exception as exc:
            if json_only:
                print(
                    json.dumps({"error": f"Error reading fixture {fixture_file}: {exc}", "status": "error"}, indent=2)
                )
            else:
                print(f"Error reading fixture {fixture_file}: {exc}", file=sys.stderr)
            return 1

        actions_runs: list[dict[str, Any]] = []
        if actions_fixture_file:
            try:
                act_data = gp.decode(Path(actions_fixture_file).read_text(encoding="utf-8"))
                # The same run-list choke point as the live read: a dict names its list by key, and a
                # recorded REST page that declares ``total_count`` must carry its complete first page.
                act_key = None
                page_size = None
                if isinstance(act_data, dict):
                    act_key = "workflow_runs" if "workflow_runs" in act_data else "runs"
                    page_size = RUNS_PAGE_SIZE if "total_count" in act_data else None
                actions_runs = parse_actions_runs(act_data, act_key, page_size=page_size)
            except Exception as exc:
                if json_only:
                    print(
                        json.dumps(
                            {
                                "error": f"Error reading actions fixture {actions_fixture_file}: {exc}",
                                "status": "error",
                            },
                            indent=2,
                        )
                    )
                else:
                    print(f"Error reading actions fixture {actions_fixture_file}: {exc}", file=sys.stderr)
                return 1
        embedded_runs = not actions_fixture_file and isinstance(fix_data, dict) and "actions_runs" in fix_data

        try:
            if embedded_runs:
                actions_runs = parse_actions_runs(fix_data["actions_runs"], None)
            status = evaluate_status_data(fix_data, pr_number, actions_runs)
        except (ValueError, RuntimeError) as exc:
            if json_only:
                diag: dict[str, Any] = {
                    "error": str(exc),
                    "pr_number": pr_number,
                    "status": "error",
                }
                if isinstance(fix_data, dict) and fix_data.get("errors"):
                    diag["errors"] = fix_data["errors"]
                print(json.dumps(diag, indent=2))
            else:
                print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        auth_token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        try:
            status = fetch_live_status(
                pr_number=pr_number,
                repo=resolved_repo,
                branch=branch,
                token=auth_token,
            )
        except ValueError as exc:
            if json_only:
                print(json.dumps({"error": str(exc), "pr_number": pr_number, "status": "error"}, indent=2))
            else:
                print(f"Error: {exc}", file=sys.stderr)
            return 1
        except RuntimeError as exc:
            if json_only:
                print(json.dumps({"error": str(exc), "pr_number": pr_number, "status": "error"}, indent=2))
            else:
                print(f"Error querying GitHub: {exc}", file=sys.stderr)
            return 1

    output = render_output(status, json_only=json_only, line_only=line_only)
    print(output)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Check GitHub Merge Queue status, position, ETA, and CI run for a pull request (#7814 item 13).",
    )
    parser.add_argument(
        "pr",
        help="Pull request number, branch, or URL (e.g. 7814, #7814, https://github.com/.../pull/7814).",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub owner/repo (default: detected from git origin or GITHUB_REPOSITORY).",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Target base branch for merge queue (default: %(default)s).",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output structured JSON only.",
    )
    output_group.add_argument(
        "--line",
        "--text",
        action="store_true",
        dest="line_output",
        help="Output single human-readable line only.",
    )
    parser.add_argument(
        "--fixture",
        dest="fixture_file",
        default=None,
        help="Path to recorded JSON fixture for offline evaluation.",
    )
    parser.add_argument(
        "--actions-fixture",
        dest="actions_fixture_file",
        default=None,
        help="Path to recorded GitHub Actions runs fixture file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main function."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    return check_and_report_pr_status(
        pr=args.pr,
        repo=args.repo,
        branch=args.branch,
        json_only=args.json_output,
        line_only=args.line_output,
        fixture_file=args.fixture_file,
        actions_fixture_file=args.actions_fixture_file,
    )


if __name__ == "__main__":
    sys.exit(main())
