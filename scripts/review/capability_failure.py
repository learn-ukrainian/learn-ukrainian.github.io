"""A review run that failed only for lack of a capability: a typed outcome, never a verdict.

Approved design: CTO proposal, Sol 6.1 APPROVE WITH CHANGES (coordinator stream,
epic #10453). A finished review run whose verdict was never published refuses
every later round of its lineage (``review_lineage.check_lineage``). When the
reviewer stopped only because a capability it needed was missing, the
recording authority may publish this classification for the run instead.

1. Eligible (:func:`classify`, the one shared rule). The run finished
   (``done``) with a recorded reply digest; its reply's verdict is ``BLOCKED``
   with a known finding count of zero, which only a structured
   ``code-review-findings.v1`` reply proves (a prose reply's count is unknown;
   "no in-scope blocker" is not zero findings); and the missing capability is
   evidenced: ``sources-mcp`` by the run's own runtime count of zero Sources MCP
   calls on the Ukrainian profile, which requires them, and every other
   capability by the structured reply's ``missing_capabilities`` list.
2. Published (:func:`build_comment`). A PR comment whose last line is one
   ``review-capability-failure`` marker binding the task and run (start and
   run nonce), the reviewed SHA, the reply digest, the missing capability, the
   reviewer and the recording authority. The run's reply is not copied or
   changed.
3. Applied. The lineage accepts such a run only when its event re-derives
   exactly from the record and reply, and refuses a missing event, an event
   with no run, several events for one run, or an event beside a published
   verdict. The verdict recorder refuses to publish a verdict for a classified
   run. Round counting and the merge-queue keeper read only verdict markers, so
   a capability failure opens no round, approves nothing, rejects nothing and
   fills no reviewer seat: every required review still has to happen.

Cooperative threat model, as in ``scripts/agent_runtime/bounded_advisory.py``:
the authority is recorded, not authenticated, so a process that rewrites task
records or posts comments as the recorder's login is outside it. An event can
classify only a run that qualifies on its own record and reply.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.opsec.prepublish import check_texts, normalize_repository, publication_boundary, publication_cli
from scripts.review import record_cf_verdict as recorder
from scripts.review.budget_grant import ISSUERS
from scripts.review.language_lane import is_ukrainian_review

EVENT_PREFIX = "<!-- review-capability-failure"
SOURCES_MCP = "sources-mcp"
# The capabilities a reviewer can lack; ``sources-mcp`` alone has runtime evidence in the task record.
CAPABILITIES = frozenset({SOURCES_MCP, "test-execution", "shell", "browser", "checkout-data"})
# The structured reply's own declaration of what it lacked, beside the canonical findings fields.
DECLARATION_FIELD = "missing_capabilities"
# Only the CTO seat records a classification.
AUTHORITIES = ISSUERS
_EVENT = re.compile(
    r"<!-- review-capability-failure v1 sha=(?P<sha>[0-9a-f]{40}) task=(?P<task>\S+) "
    r"started=(?P<started>\S+) run=(?P<run>[0-9A-Za-z._-]+) result_sha256=(?P<result_sha256>[0-9a-f]{64}) "
    r"capability=(?P<capability>[a-z-]+) model=(?P<model>\S+) family=(?P<family>\S+) "
    r"authority=(?P<authority>\S+) -->"
)
_DIGEST = re.compile(r"[0-9a-f]{64}")

# Typed refusal reasons.
RUN = "run"
VERDICT = "verdict"
FINDINGS = "findings"
CAPABILITY = "capability"
AUTHORITY = "authority"
PUBLICATION = "publication"


class CapabilityFailureRefused(recorder.RecordError):
    """A capability-failure condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"CAPABILITY_FAILURE_REFUSED[{reason}]: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class CapabilityFailure:
    """One run's classification, exactly as its event publishes it."""

    task: str
    started: str
    run: str
    sha: str
    result_sha256: str
    capability: str
    model: str
    family: str
    authority: str

    def marker(self) -> str:
        return (
            f"{EVENT_PREFIX} v1 sha={self.sha} task={self.task} started={self.started} run={self.run} "
            f"result_sha256={self.result_sha256} capability={self.capability} model={self.model} "
            f"family={self.family} authority={self.authority} -->"
        )


def run_started(record: Mapping[str, Any]) -> str | None:
    """The run's start as the recorder writes it into a verdict marker."""
    try:
        started = datetime.fromisoformat(str(record.get("started_at") or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if started.tzinfo is None:
        return None
    return started.astimezone(UTC).isoformat(timespec="microseconds")


def _declared(reply: str) -> frozenset[str]:
    """The capabilities a structured reply declares missing; a malformed declaration refuses."""
    try:
        payload = json.loads(reply)
    except ValueError:
        return frozenset()
    if not isinstance(payload, dict) or DECLARATION_FIELD not in payload:
        return frozenset()
    declared = payload[DECLARATION_FIELD]
    if (
        not isinstance(declared, list)
        or not declared
        or not all(isinstance(item, str) and item in CAPABILITIES for item in declared)
        or len(set(declared)) != len(declared)
    ):
        raise CapabilityFailureRefused(
            CAPABILITY, f"{DECLARATION_FIELD} must be a non-empty list of distinct names from {sorted(CAPABILITIES)}"
        )
    return frozenset(declared)


def classify(
    task_id: str, record: Mapping[str, Any], reply: str, *, capability: str, authority: str
) -> CapabilityFailure:
    """The run's capability-failure classification, or the refusal naming the unmet condition.

    ``reply`` is the run's reply as its reader returned it: both readers
    (``review_lineage._read_run`` and ``record_cf_verdict._task``) refuse a
    reply that does not match the recorded digest, and this rule requires one.
    """
    if authority not in AUTHORITIES:
        raise CapabilityFailureRefused(AUTHORITY, f"{authority!r} is not a recording authority ({sorted(AUTHORITIES)})")
    if capability not in CAPABILITIES:
        raise CapabilityFailureRefused(CAPABILITY, f"{capability!r} is not one of {sorted(CAPABILITIES)}")
    if record.get("status") != "done":
        raise CapabilityFailureRefused(RUN, f"review task {task_id} did not finish (status {record.get('status')!r})")
    started, run, sha = run_started(record), record.get("run_nonce"), record.get("worktree_base_sha")
    digest = record.get("result_sha256")
    if started is None or not isinstance(run, str) or not re.fullmatch(r"[0-9A-Za-z._-]+", run):
        raise CapabilityFailureRefused(RUN, f"review task {task_id} has no recorded start and run nonce")
    if not isinstance(sha, str) or not recorder.SHA.fullmatch(sha) or record.get("pinned_head") not in (None, sha):
        raise CapabilityFailureRefused(RUN, f"review task {task_id} has no single reviewed SHA")
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise CapabilityFailureRefused(RUN, f"review task {task_id} has no recorded reply digest")
    try:
        verdict, count = recorder._review_verdict_and_count(reply)
        model, family = recorder.reviewer_identity(record)
    except recorder.RecordError as exc:
        raise CapabilityFailureRefused(RUN, f"review task {task_id} evidence refused: {exc}") from None
    if verdict != "BLOCKED":
        raise CapabilityFailureRefused(VERDICT, f"review task {task_id} replied {verdict}, not BLOCKED")
    if count == "unknown":
        raise CapabilityFailureRefused(
            FINDINGS,
            f"review task {task_id} has no known finding count; only a structured code-review-findings.v1 "
            "reply proves zero findings",
        )
    if count:
        raise CapabilityFailureRefused(FINDINGS, f"review task {task_id} carries {count} finding(s)")
    declared = _declared(reply)
    if capability == SOURCES_MCP:
        calls = record.get("sources_mcp_call_count")
        if not is_ukrainian_review(record) or type(calls) is not int or calls != 0:
            raise CapabilityFailureRefused(
                CAPABILITY,
                f"review task {task_id} has no runtime evidence of a missing required Sources MCP: it needs "
                "the Ukrainian profile and a recorded count of zero calls",
            )
    elif capability not in declared:
        raise CapabilityFailureRefused(
            CAPABILITY, f"review task {task_id}'s reply does not declare {capability} in {DECLARATION_FIELD}"
        )
    return CapabilityFailure(task_id, started, run, sha, digest, capability, model, family, authority)


def build_comment(failure: CapabilityFailure) -> str:
    """The event's PR comment: a readable account, then the marker on its last line.

    The v1 text is frozen: a published event must equal it exactly (:func:`_parse`).
    It carries no verdict line, so the merge-queue keeper never reads it as a verdict.
    """
    return (
        "### Review capability failure\n"
        "This review run stopped because a capability it required was missing, and it raised no finding. "
        "It is not a verdict: it approves nothing, rejects nothing, opens no review round and waives no "
        "required review.\n"
        f"head: {failure.sha}\n"
        f"Missing capability: {failure.capability}\n"
        f"Reviewer model: {failure.model}\n"
        f"Reviewer family: {failure.family}\n"
        f"Task id: {failure.task}\n"
        f"Reply digest: {failure.result_sha256}\n"
        f"Recorded by: {failure.authority}\n\n"
        f"{failure.marker()}"
    )


def _parse(body: str) -> CapabilityFailure | None:
    """The event a comment carries on its last line; None when it carries none, a refusal when malformed."""
    last = body.rstrip("\n").split("\n")[-1]
    if not last.startswith(EVENT_PREFIX):
        return None
    match = _EVENT.fullmatch(last)
    if match is None or body.count(EVENT_PREFIX) != 1:
        raise CapabilityFailureRefused(PUBLICATION, "unreadable capability-failure event")
    event = CapabilityFailure(**match.groupdict())
    if body != build_comment(event):
        raise CapabilityFailureRefused(PUBLICATION, f"capability-failure event of task {event.task} was altered")
    return event


def events(comments: Sequence[Mapping[str, Any]], login: str) -> list[CapabilityFailure]:
    """Every capability-failure event ``login`` posted with a trusted association; damaged ones refuse."""
    found = []
    for index, comment in enumerate(comments):
        body = comment.get("body") if isinstance(comment, Mapping) else None
        if not isinstance(body, str):
            raise CapabilityFailureRefused(PUBLICATION, f"PR comment {index} malformed")
        if (
            comment.get("user", {}).get("login") != login
            or comment.get("author_association") not in recorder.TRUSTED_ASSOCIATIONS
        ):
            continue
        event = _parse(body)
        if event is None:
            continue
        if comment.get("created_at") != comment.get("updated_at"):
            raise CapabilityFailureRefused(
                PUBLICATION, f"capability-failure event in comment {comment.get('id', index)} was edited"
            )
        found.append(event)
    return found


def run_events(found: Sequence[CapabilityFailure], task: str, started: str | None) -> list[CapabilityFailure]:
    """The events naming one run; more than one distinct event for it is a conflict."""
    named = [event for event in found if event.task == task and event.started == started]
    if len(set(named)) > 1:
        raise CapabilityFailureRefused(PUBLICATION, f"review task {task} has conflicting capability-failure events")
    return named


def require_bound(event: CapabilityFailure, task_id: str, record: Mapping[str, Any], reply: str) -> None:
    """Refuse an event that the run's record and reply do not re-derive exactly."""
    derived = classify(task_id, record, reply, capability=event.capability, authority=event.authority)
    if derived != event:
        raise CapabilityFailureRefused(
            PUBLICATION, f"capability-failure event of {task_id} conflicts with its task record"
        )


def require_unclassified(comments: Sequence[Mapping[str, Any]], login: str, *, task: str, started: str) -> None:
    """Refuse a verdict for a run already classified as a capability failure: it has no verdict to publish."""
    if run_events(events(comments, login), task, started):
        raise CapabilityFailureRefused(
            PUBLICATION, f"review task {task} is recorded as a capability failure; it has no verdict to publish"
        )


@publication_boundary(recorder.RecordError)
def record_capability_failure(
    task_id: str,
    *,
    pr_number: int,
    capability: str,
    authority: str,
    task_root: Path | None = None,
    lock_root: Path | None = None,
) -> dict[str, Any]:
    """Append the capability-failure event of a finished, unpublished review run to its open PR."""
    root = recorder._repo_root() if task_root is None or lock_root is None else None
    task_root = task_root or root / "batch_state" / "tasks"
    lock_root = lock_root or root / "batch_state" / "locks"
    record, reply = recorder._task(task_id, task_root)
    failure = classify(task_id, record, reply, capability=capability, authority=authority)
    repository, branch = record.get("repository"), recorder._review_branch(record)
    if not isinstance(repository, str) or "/" not in repository:
        raise CapabilityFailureRefused(RUN, "review repository unavailable")
    pr = recorder._pr(repository, branch, pr_number)
    number = pr.get("number")
    if pr.get("headRefName") != branch or not isinstance(number, int):
        raise CapabilityFailureRefused(RUN, f"review task {task_id} did not review PR #{pr_number}'s branch")
    comment = build_comment(failure)
    check_texts(normalize_repository(repository), [comment], environment={})
    adapter = recorder.GitHubAdapter(Path.cwd())
    login = adapter.identity()
    with recorder.sha_lock(repository, failure.sha, lock_root):
        try:
            comments = adapter.comments(repository, number)
        except recorder.SweepError as exc:
            raise recorder.RecordError(f"comment lookup failed: {exc}") from exc
        if any(
            marker["task"] == task_id and marker["started"] == failure.started
            for _, marker in recorder._trusted_markers(comments, login)
        ):
            raise CapabilityFailureRefused(
                PUBLICATION, f"review task {task_id} already has a published verdict; it stays the run's outcome"
            )
        existing = run_events(events(comments, login), task_id, failure.started)
        if existing and existing[0] != failure:
            raise CapabilityFailureRefused(
                PUBLICATION, f"review task {task_id} already has a different capability-failure event"
            )
        if not existing:
            data = recorder._run_json(
                recorder.Request("issue-comment-json", repo=repository, number=number, body=comment)
            )
            comment_id = data.get("id") if isinstance(data, dict) else None
            if not isinstance(comment_id, int):
                raise recorder.RecordError("comment post response lacked id; retry to reconcile")
            readback = recorder._run_json(recorder.Request("read-comment", repo=repository, number=comment_id))
            if (
                not isinstance(readback, dict)
                or readback.get("body") != comment
                or readback.get("user", {}).get("login") != login
                or readback.get("author_association") not in recorder.TRUSTED_ASSOCIATIONS
                or readback.get("created_at") != readback.get("updated_at")
            ):
                raise recorder.RecordError("comment readback mismatch; publication state unknown")
    return {"pr": number, "comment": "existing" if existing else "posted", **asdict(failure)}


@publication_cli(recorder.RecordError)
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py capability-failure",
        description="Record that a finished review run stopped only for a missing capability, with no finding.\n"
        "It publishes a typed event on the run's PR; it is never a verdict or an approval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py capability-failure "
        "--task-id review-unit --pr 42 --capability test-execution --authority claude-cto\n"
        "Outputs: JSON receipt on stdout naming the event's bindings.\n"
        "Exit codes: 0: recorded or already recorded; 1: refused (the reason names the unmet condition).\n"
        "Related: agents_extensions/shared/skills/review-loop/references/policy.md",
    )
    parser.add_argument("--task-id", required=True, help="Finished review task whose verdict was never published")
    parser.add_argument("--pr", type=int, required=True, help="Open PR the run reviewed")
    parser.add_argument("--capability", required=True, choices=sorted(CAPABILITIES), help="The missing capability")
    parser.add_argument("--authority", required=True, help=f"Recording authority, one of {sorted(AUTHORITIES)}")
    args = parser.parse_args(argv)
    try:
        result = record_capability_failure(
            args.task_id, pr_number=args.pr, capability=args.capability, authority=args.authority
        )
    except (recorder.RecordError, recorder.SweepError, ValueError) as exc:
        print(f"capability failure refused: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
