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
_NOT_FOUND_MARKER = "Could not resolve to a PullRequest"


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise MalformedPayload(reason)


def _is_int(value: Any, minimum: int) -> bool:
    """An exact int (never a bool, float or string) that is at least ``minimum``."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _optional(value: Any, check: Any) -> bool:
    """``null`` (or an absent key) is allowed; anything else must pass ``check``."""
    return value is None or bool(check(value))


def _object(value: Any, reason: str) -> dict[str, Any]:
    _require(isinstance(value, dict), reason)
    return value


def _validate_check_suites(commit: Any) -> None:
    """``headCommit`` is null or an object whose ``checkSuites.nodes`` is a list of suite objects."""
    if commit is None:
        return
    suites = _object(commit, "headCommit")
    check_suites = suites.get("checkSuites")
    if check_suites is None:
        return
    nodes = _object(check_suites, "checkSuites").get("nodes")
    _require(nodes is None or isinstance(nodes, list), "checkSuites.nodes")
    for node in nodes or []:
        suite = _object(node, "checkSuites.nodes[]")
        _require(_optional(suite.get("status"), _is_text), "checkSuite.status")
        _require(_optional(suite.get("conclusion"), _is_text), "checkSuite.conclusion")
        _require(_optional(suite.get("createdAt"), _is_text), "checkSuite.createdAt")
        run = suite.get("workflowRun")
        if run is None:
            continue
        run = _object(run, "workflowRun")
        _require(_is_text(run.get("url")), "workflowRun.url")
        _require(_optional(run.get("event"), _is_text), "workflowRun.event")
        _require(_optional(run.get("createdAt"), _is_text), "workflowRun.createdAt")
        _require(_optional(run.get("id"), lambda v: _is_int(v, 0)), "workflowRun.id")
        workflow = run.get("workflow")
        _require(workflow is None or isinstance(workflow, dict), "workflowRun.workflow")
        _require(_optional((workflow or {}).get("name"), _is_text), "workflow.name")


def _validate_entry_fields(entry: dict[str, Any], reason: str) -> None:
    """The queue-position fields shared by a pull request's own entry and a queue node."""
    _require(_optional(entry.get("position"), lambda v: _is_int(v, 1)), f"{reason}.position")
    _require(_optional(entry.get("state"), _is_text), f"{reason}.state")
    _require(_optional(entry.get("enqueuedAt"), _is_text), f"{reason}.enqueuedAt")
    _require(_optional(entry.get("estimatedTimeToMerge"), lambda v: _is_int(v, 0)), f"{reason}.estimatedTimeToMerge")


def _validate_pull_request(pull: dict[str, Any], pr_number: int) -> None:
    number = pull.get("number")
    _require(_is_int(number, 1) and number == pr_number, "pullRequest.number")
    state = pull.get("state")
    _require(isinstance(state, str) and state in _PR_STATES, "pullRequest.state")
    merged, in_queue = pull.get("merged"), pull.get("isInMergeQueue")
    _require(isinstance(merged, bool), "pullRequest.merged")
    _require(isinstance(in_queue, bool), "pullRequest.isInMergeQueue")
    _require(merged == (state == "MERGED"), "pullRequest.merged/state")
    _require(_optional(pull.get("mergeStateStatus"), _is_text), "pullRequest.mergeStateStatus")
    entry = pull.get("mergeQueueEntry")
    if entry is not None:
        entry = _object(entry, "mergeQueueEntry")
        _require(in_queue, "mergeQueueEntry/isInMergeQueue")
        _validate_entry_fields(entry, "mergeQueueEntry")
        _validate_check_suites(entry.get("headCommit"))


def _validate_merge_queue(queue: Any) -> None:
    if queue is None:
        return
    queue = _object(queue, "mergeQueue")
    _require(_optional(queue.get("url"), _is_text), "mergeQueue.url")
    _require(
        _optional(queue.get("nextEntryEstimatedTimeToMerge"), lambda v: _is_int(v, 0)),
        "mergeQueue.nextEntryEstimatedTimeToMerge",
    )
    entries = queue.get("entries")
    if entries is None:
        return
    nodes = _object(entries, "mergeQueue.entries").get("nodes")
    _require(nodes is None or isinstance(nodes, list), "mergeQueue.entries.nodes")
    for node in nodes or []:
        node = _object(node, "mergeQueue.entries.nodes[]")
        _validate_entry_fields(node, "mergeQueue.entries.nodes[]")
        pull = _object(node.get("pullRequest"), "mergeQueue.entries.nodes[].pullRequest")
        _require(_is_int(pull.get("number"), 1), "mergeQueue.entries.nodes[].pullRequest.number")


@dataclass(frozen=True)
class QueueDocument:
    """A GraphQL ``queue-status`` document that passed :func:`parse_queue_status`."""

    pull_request: dict[str, Any]
    merge_queue: dict[str, Any]


def parse_queue_status(
    document: Any, pr_number: int, *, repo: str | None = None, null_data_is_not_found: bool = False
) -> QueueDocument:
    """The single choke point for a GraphQL ``queue-status`` document.

    Returns the validated pull request and merge queue, or raises before anything is decided:

    * ``ValueError`` - GraphQL positively reports the pull request unresolvable (an error naming
      it, and ``pullRequest`` null);
    * ``RuntimeError`` - GraphQL returned errors (a partial result is not trusted);
    * :class:`MalformedPayload` (a ``RuntimeError``) - the document is not exactly the whitelisted
      shape: JSON object, ``data.repository.pullRequest`` an object whose number, state, merged and
      isInMergeQueue are present with the expected types, and every optional field typed.

    ``null_data_is_not_found`` keeps one recorded offline-fixture contract (a bare ``{"data": null}``
    reads as "not found"); the live read never sets it.
    """
    document = _object(document, "document")
    errors = document.get("errors")
    _require(errors is None or isinstance(errors, list), "errors")
    data = document.get("data")
    repository = data.get("repository") if isinstance(data, dict) else None
    pull = repository.get("pullRequest") if isinstance(repository, dict) else None
    if errors:
        messages = [e["message"] for e in errors if isinstance(e, dict) and _is_text(e.get("message"))]
        if pull is None and any(_NOT_FOUND_MARKER in m for m in messages):
            raise ValueError(_not_found_message(pr_number, repo))
        raise RuntimeError(f"GraphQL error: {'; '.join(messages) if messages else 'no error message'}")
    if data is None and null_data_is_not_found and "data" in document:
        raise ValueError(_not_found_message(pr_number, repo))
    _require(isinstance(data, dict), "data")
    _require(isinstance(repository, dict), "data.repository")
    _require(isinstance(pull, dict), "data.repository.pullRequest")
    _validate_pull_request(pull, pr_number)
    _validate_merge_queue(repository.get("mergeQueue"))
    return QueueDocument(pull_request=pull, merge_queue=repository.get("mergeQueue") or {})


def _not_found_message(pr_number: int, repo: str | None) -> str:
    return f"Pull request #{pr_number} not found in repository{f' {repo}' if repo else ''}."


def _valid_run(run: Any) -> bool:
    """A usable Actions run names its page (``html_url`` or ``url``) and its ``status``; every other
    field the tool reads is null/absent or of its expected type."""
    if not isinstance(run, dict) or not _is_text(run.get("html_url") or run.get("url")):
        return False
    if not _is_text(run.get("status")):
        return False
    texts = ("html_url", "url", "conclusion", "event", "name", "head_branch", "headBranch")
    texts += ("created_at", "createdAt", "updated_at", "updatedAt")
    return all(_optional(run.get(k), lambda v: isinstance(v, str)) for k in texts) and all(
        _optional(run.get(k), lambda v: _is_int(v, 0)) for k in ("id", "databaseId")
    )


def parse_actions_runs(data: Any, key: str | None) -> list[dict[str, Any]]:
    """The single choke point for an Actions run list; an unavailable read is never an empty list.

    ``key`` names the list inside a REST object; ``None`` means the payload is itself a list.
    Every element must pass :func:`_valid_run`.
    """
    if key is None:
        runs = data
    else:
        _require(isinstance(data, dict), "runs document")
        runs = data.get(key)
    _require(isinstance(runs, list), "runs list")
    _require(all(_valid_run(r) for r in runs), "run element")
    return runs


def evaluate_status_data(
    graphql_data: dict[str, Any],
    pr_number: int,
    actions_runs: list[dict[str, Any]] | None = None,
) -> MergeQueueStatus:
    """Evaluate a raw GraphQL document and Actions runs into MergeQueueStatus.

    Both inputs are validated by the same choke points as the live read; a malformed document or
    run list raises (:class:`MalformedPayload`) instead of producing a status.
    """
    document = parse_queue_status(graphql_data, pr_number, null_data_is_not_found=True)
    runs = parse_actions_runs(actions_runs, None) if actions_runs is not None else []
    return _evaluate(document, pr_number, runs)


def _evaluate(document: QueueDocument, pr_number: int, actions_runs: list[dict[str, Any]]) -> MergeQueueStatus:
    pr_obj = document.pull_request
    pr_state: str = pr_obj["state"]
    pr_merged: bool = pr_obj["merged"]
    merge_state_status = pr_obj.get("mergeStateStatus")
    is_in_mq: bool = pr_obj["isInMergeQueue"]
    mq_entry = pr_obj.get("mergeQueueEntry")

    mq_obj = document.merge_queue
    queue_url = mq_obj.get("url")
    next_eta = mq_obj.get("nextEntryEstimatedTimeToMerge")

    position: int | None = None
    state: str | None = None
    enqueued_at: str | None = None
    eta_seconds: int | None = None
    head_commit: dict[str, Any] | None = None

    if mq_entry is not None:
        position = mq_entry.get("position")
        state = mq_entry.get("state")
        enqueued_at = mq_entry.get("enqueuedAt")
        eta_seconds = mq_entry.get("estimatedTimeToMerge")
        head_commit = mq_entry.get("headCommit")
    elif is_in_mq:
        # Check entries on mergeQueue object
        for node in (mq_obj.get("entries") or {}).get("nodes") or []:
            if node["pullRequest"]["number"] == pr_number:
                position = node.get("position")
                state = node.get("state")
                enqueued_at = node.get("enqueuedAt")
                eta_seconds = node.get("estimatedTimeToMerge")
                break
        if position is None:
            # isInMergeQueue is true but position could not be resolved from entry
            state = "QUEUED"
            if next_eta is not None:
                eta_seconds = next_eta

    # Collect candidate merge_group workflow runs from checkSuites and actions_runs
    candidate_runs: list[dict[str, Any]] = []

    if head_commit:
        for cs in (head_commit.get("checkSuites") or {}).get("nodes") or []:
            wf_run = cs.get("workflowRun")
            if wf_run is None:
                continue
            wf_url = wf_run["url"]
            wf_event = wf_run.get("event")
            # Filter out non-merge_group runs (e.g. stale pull_request run)
            if wf_event and wf_event != "merge_group":
                continue
            wf_name = (
                (wf_run.get("workflow") or {}).get("name")
                or wf_run.get("name")
                or cs.get("name")
                or ""
            )
            created_at = (
                wf_run.get("createdAt")
                or wf_run.get("created_at")
                or cs.get("createdAt")
                or cs.get("created_at")
                or ""
            )
            run_id = wf_run.get("id") or wf_run.get("databaseId") or cs.get("id") or 0
            candidate_runs.append(
                {
                    "id": run_id,
                    "url": wf_url,
                    "html_url": wf_url,
                    "name": wf_name,
                    "status": cs.get("status") or wf_run.get("status"),
                    "conclusion": cs.get("conclusion") or wf_run.get("conclusion"),
                    "event": wf_event or "merge_group",
                    "head_branch": f"gh-readonly-queue/main/pr-{pr_number}-suite",
                    "created_at": created_at,
                }
            )

    candidate_runs.extend(actions_runs)

    matched_run = find_latest_merge_group_run(candidate_runs, pr_number)
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
        queued=is_in_mq,
        position=position,
        state=state,
        eta_human=eta_human,
        run_url=run_url,
        pr_state=pr_state,
        pr_merged=pr_merged,
        merge_state_status=merge_state_status,
    )

    return MergeQueueStatus(
        pr_number=pr_number,
        queued=is_in_mq,
        position=position,
        state=state,
        enqueued_at=enqueued_at,
        estimated_time_to_merge_seconds=eta_seconds,
        estimated_time_to_merge_human=eta_human,
        latest_merge_group_run_url=run_url,
        latest_merge_group_run_status=run_status,
        latest_merge_group_run_conclusion=run_conclusion,
        pr_state=pr_state,
        pr_merged=pr_merged,
        pr_merge_state_status=merge_state_status,
        queue_url=queue_url,
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

    The return code is checked before the output is parsed. ``key`` names the
    list inside a REST object; ``None`` means the output is itself a list.
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
        data = json.loads(proc.stdout)
    except (TypeError, ValueError):
        raise RuntimeError(_unavailable_message(what, proc)) from None
    try:
        return parse_actions_runs(data, key)
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

    try:
        data = json.loads(proc.stdout)
    except (TypeError, ValueError) as exc:
        err_msg = (proc.stderr or proc.stdout or "").strip() if isinstance(proc.stdout, str) else ""
        raise RuntimeError(f"Failed to parse GraphQL response (exit {proc.returncode}): {err_msg}") from exc

    # The one parse-or-unavailable choke point: a refused read, a failed read, a partial result and
    # every malformed shape end here, before any further request. Only a positively identified
    # missing pull request keeps its own meaning (ValueError).
    try:
        document = parse_queue_status(data, pr_number, repo=repo)
    except MalformedPayload as exc:
        raise RuntimeError(_unavailable_message("GraphQL", proc, data, exc.reason)) from None
    if not _exit_ok(proc):
        raise RuntimeError(_unavailable_message("GraphQL", proc, data))

    # Fetch merge_group workflow runs. An unavailable read raises (no fallback
    # request, never an empty list); only a successful empty list falls back.
    runs_path = f"repos/{owner}/{name}/actions/runs?event=merge_group&per_page=30"
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
            "30",
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
            with open(fixture_file, encoding="utf-8") as f:
                fix_data = json.load(f)
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
                with open(actions_fixture_file, encoding="utf-8") as f:
                    act_data = json.load(f)
                # The same run-list choke point as the live read: a dict names its list by key.
                act_key = None
                if isinstance(act_data, dict):
                    act_key = "workflow_runs" if "workflow_runs" in act_data else "runs"
                actions_runs = parse_actions_runs(act_data, act_key)
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
