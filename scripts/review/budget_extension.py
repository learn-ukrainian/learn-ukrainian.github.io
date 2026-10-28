"""A recordable, single-use review budget extension: one round past a PR's budget.

A PR approved at head A in its last budgeted round can meet a base-branch change
that conflicts with it. The fix is a new head N, and the verdict recorder
refuses round ``budget + 1``. This is the recordable outcome of the CTO-and-
advisor escalation for that case (review-loop ``references/policy.md`` § Budget).
Approved design: CTO proposal, Sol 6.1 APPROVE (advisory task
cto-7eba-adv-extension2), answering the refusal in cto-7eba-adv-extension.

1. Request. A JSON object committed on the default branch under
   ``batch_state/review-budget-extensions/`` with exactly the fields ``pr``,
   ``lineage_id`` (the issue or branch lineage the budget follows),
   ``approved_head`` (A), ``reason_class`` (``post-approval-base-conflict``),
   ``grant`` (1) and ``requested_at`` (ISO-8601 with a timezone). Its digest is
   its canonical SHA-256 (``bounded_advisory.canonical_sha256``); print it with
   ``record_cf_verdict.py budget-extension digest <file>``. One commit adds it
   and none changes it; that commit's ``X-Agent`` trailer names its author.
2. Approval. A read-only dispatch on the designated advisor outside the request
   author's family (operator-expectations item 12: an Anthropic author needs Sol,
   an OpenAI author Opus) with ``--advisory-role review_budget_extension
   --advisory-binding <digest>``. Its result holds exactly one fenced
   ``budget-extension`` JSON object: ``{decision, pr, lineage_id,
   approved_head, reason_class, grant, request_sha256}``, sealed at finish like
   a bounded advisory envelope (``bounded_advisory.load_sealed_result``).
3. Admission. The recorder admits round ``budget + 1`` at N only when the
   review lineage before N passes (``review_lineage``: every run terminal and
   published, A's APPROVE each seat's latest verdict), the PR has exactly one
   request and its lineage has no other, the one finished approval task bound
   to the request's digest passes every check above with ``decision`` APPROVE
   and every other field equal to the request, and N descends from A only
   through merges of the base branch (each commit from N back to A on the
   first-parent chain is a two-parent merge whose second parent is on the base
   branch). Everything else refuses.

Limits. One extension per lineage, ever: the request names its PR, a lineage
has one request, and the round must be exactly ``budget + 1``, so a verdict at
any later head refuses whatever the extension round decided. Both Ukrainian
seats at N are that one round. Cooperative threat model, as in
``bounded_advisory``: a process that can rewrite task records, results or the
default branch is outside it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent_runtime.bounded_advisory import (
    AdvisoryRefused,
    canonical_sha256,
    fenced_object,
    load_sealed_result,
)
from scripts.guardrails.delegate_ownership import TERMINAL_TASK_STATUSES
from scripts.orchestration.integration_sweep import SHA
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import REVIEW_BUDGET_EXTENSION_ROLE, advisory_role_policy
from scripts.review.review_lineage import LineageRefused, check_lineage, lineage_runs
from scripts.review.reviewer_resolver import UNRESOLVED_AUTHOR_FAMILIES

REQUEST_DIR = "batch_state/review-budget-extensions"
REASON_CLASS = "post-approval-base-conflict"
GRANT = 1
REQUEST_FIELDS = frozenset({"pr", "lineage_id", "approved_head", "reason_class", "grant", "requested_at"})
LINEAGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/#-]{0,199}")
GIT_TIMEOUT_S = 60.0
# A base-conflict fix is one merge, or a few; a longer first-parent walk is not one.
MAX_BASE_MERGES = 10

# Typed refusal reasons.
REQUEST = "request"
LINEAGE = "lineage"
AUTHOR = "author"
APPROVAL = "approval"
DESCENT = "descent"


class ExtensionRefused(recorder.RecordError):
    """A budget extension condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"BUDGET_EXTENSION_REFUSED[{reason}]: {detail}")
        self.reason = reason


@dataclass(frozen=True)
class ExtensionRequest:
    path: str
    request: dict[str, Any]

    @property
    def sha256(self) -> str:
        return canonical_sha256(self.request)


def parse_request(raw: bytes, label: str) -> dict[str, Any]:
    """The typed request in ``raw``, or a refusal naming ``label``."""
    try:
        request = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ExtensionRefused(REQUEST, f"{label} is not UTF-8 JSON: {exc}") from None
    if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
        found = sorted(request) if isinstance(request, dict) else type(request).__name__
        raise ExtensionRefused(REQUEST, f"{label} must hold exactly {sorted(REQUEST_FIELDS)}, found {found}")
    pr, grant = request["pr"], request["grant"]
    if isinstance(pr, bool) or not isinstance(pr, int) or pr < 1:
        raise ExtensionRefused(REQUEST, f"{label} pr must be a positive integer")
    if not isinstance(request["lineage_id"], str) or not LINEAGE_ID.fullmatch(request["lineage_id"]):
        raise ExtensionRefused(REQUEST, f"{label} lineage_id must match {LINEAGE_ID.pattern}")
    head = request["approved_head"]
    if not isinstance(head, str) or not SHA.fullmatch(head) or head != head.lower():
        raise ExtensionRefused(REQUEST, f"{label} approved_head must be a full lowercase commit SHA")
    if request["reason_class"] != REASON_CLASS:
        raise ExtensionRefused(REQUEST, f"{label} reason_class must be {REASON_CLASS!r}")
    if isinstance(grant, bool) or grant != GRANT:
        raise ExtensionRefused(REQUEST, f"{label} grant must be {GRANT}")
    try:
        stamp = datetime.fromisoformat(str(request["requested_at"]).replace("Z", "+00:00"))
    except ValueError:
        stamp = None
    if not isinstance(request["requested_at"], str) or stamp is None or stamp.tzinfo is None:
        raise ExtensionRefused(REQUEST, f"{label} requested_at must be an ISO-8601 time with a timezone")
    return request


def _git(repo_root: Path, *args: str, reason: str) -> bytes:
    try:
        return recorder._facts_git(
            repo_root, list(args), deadline=time.monotonic() + GIT_TIMEOUT_S, code=recorder.FACTS_TARGET_UNKNOWN
        )
    except recorder.BranchFactsError as exc:
        raise ExtensionRefused(reason, str(exc)) from None


def load_requests(repo_root: Path, tip: str) -> list[ExtensionRequest]:
    """Every request committed under ``REQUEST_DIR`` at the default-branch tip."""
    listing = _git(repo_root, "ls-tree", "-z", tip, "--", f"{REQUEST_DIR}/", reason=REQUEST)
    requests = []
    for entry in (item for item in listing.split(b"\0") if item):
        meta, _, raw_path = entry.partition(b"\t")
        path = raw_path.decode("utf-8", "replace")
        if not path.endswith(".json"):
            continue
        if meta.split()[:2] != [b"100644", b"blob"]:
            raise ExtensionRefused(REQUEST, f"{path} is not a regular file")
        blob = _git(repo_root, "cat-file", "blob", f"{tip}:{path}", reason=REQUEST)
        requests.append(ExtensionRequest(path, parse_request(blob, path)))
    return requests


def request_for(requests: Sequence[ExtensionRequest], pr: int) -> ExtensionRequest | None:
    """This PR's one request, refusing a second one for the PR or for its lineage."""
    mine = [item for item in requests if item.request["pr"] == pr]
    if not mine:
        return None
    if len(mine) > 1:
        raise ExtensionRefused(REQUEST, f"PR #{pr} has {len(mine)} requests: {sorted(item.path for item in mine)}")
    lineage = mine[0].request["lineage_id"]
    others = sorted(item.path for item in requests if item is not mine[0] and item.request["lineage_id"] == lineage)
    if others:
        raise ExtensionRefused(REQUEST, f"lineage {lineage!r} already has an extension request: {others}")
    return mine[0]


def request_author_family(
    repo_root: Path, tip: str, item: ExtensionRequest, *, repository: str, task_root: Path
) -> str:
    """The family of the one commit that added the request, from its ``X-Agent`` trailer."""
    commits = _git(repo_root, "rev-list", tip, "--", item.path, reason=AUTHOR).decode("ascii", "replace").split()
    if len(commits) != 1:
        raise ExtensionRefused(AUTHOR, f"{item.path} must be added by one commit and never changed ({len(commits)})")
    message = _git(repo_root, "log", "-1", "--format=%B", commits[0], reason=AUTHOR).decode("utf-8", "replace")
    # A squash merge repeats one trailer per squashed commit.
    trailers = set(re.findall(r"(?m)^X-Agent:\s*([^\s]+)\s*$", message))
    if len(trailers) != 1:
        raise ExtensionRefused(AUTHOR, f"commit {commits[0]} adding {item.path} has no single X-Agent author")
    try:
        family = recorder._attribute_trailer(
            commits[0], trailers.pop(), repository=repository, task_root=task_root
        ).family
    except recorder.RecordError as exc:
        raise ExtensionRefused(AUTHOR, f"request author unresolved: {exc}") from None
    if family is None or family in UNRESOLVED_AUTHOR_FAMILIES:
        raise ExtensionRefused(AUTHOR, f"request author family of commit {commits[0]} is unresolved")
    return family


def _approval_records(task_root: Path, digest: str) -> list[tuple[str, Path, dict[str, Any]]]:
    """Every hot or archived task record bound to ``digest`` as its advisory binding."""
    found = []
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise ExtensionRefused(APPROVAL, f"task ledger unavailable: {exc}") from None
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
            if digest not in text:
                continue
            record = json.loads(text)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise ExtensionRefused(APPROVAL, f"task record {path.name} unreadable: {exc}") from None
        if isinstance(record, dict) and record.get("advisory_binding_sha256") == digest:
            found.append((path.stem, path, record))
    return found


def check_approval(item: ExtensionRequest, *, task_root: Path, author_family: str) -> dict[str, Any]:
    """The one finished, sealed, typed APPROVE bound to the request, from the non-author advisor."""
    try:
        policy = advisory_role_policy(REVIEW_BUDGET_EXTENSION_ROLE)
    except KeyError:
        raise ExtensionRefused(APPROVAL, f"the model catalog defines no {REVIEW_BUDGET_EXTENSION_ROLE} role") from None
    advisor = policy.advisor_outside(author_family)
    if advisor is None:
        raise ExtensionRefused(
            APPROVAL,
            f"a request authored in family {author_family!r} has no single non-author designated advisor "
            "(operator-expectations item 12 needs both; escalate to the operator)",
        )
    digest = item.sha256
    records = _approval_records(task_root, digest)
    if running := sorted(
        task_id for task_id, _, record in records if record.get("status") not in TERMINAL_TASK_STATUSES
    ):
        raise ExtensionRefused(APPROVAL, f"approval task(s) still in flight for request {digest}: {running}")
    done = [(task_id, path) for task_id, path, record in records if record.get("status") == "done"]
    if len(done) != 1:
        raise ExtensionRefused(
            APPROVAL, f"request {digest} needs exactly one finished approval task, found {len(done)}"
        )
    task_id, path = done[0]
    try:
        sealed = load_sealed_result(
            task_id, state_path=path, role=policy.role, route=policy.route, model_id=advisor, binding_sha256=digest
        )
        decision = fenced_object(sealed.result_text, policy.fence)
        if set(decision) != set(policy.output_fields):
            raise ExtensionRefused(
                APPROVAL,
                f"the {policy.fence} object must hold exactly {list(policy.output_fields)}, found {sorted(decision)}",
            )
        sealed.require_sealed_object(decision, task_id)
    except AdvisoryRefused as exc:
        raise ExtensionRefused(APPROVAL, str(exc)) from None
    expected = {
        "decision": "APPROVE",
        **{field: item.request[field] for field in ("pr", "lineage_id", "approved_head", "reason_class", "grant")},
        "request_sha256": digest,
    }
    for field, value in expected.items():
        # Exact JSON types: true is not 1.
        if type(decision[field]) is not type(value) or decision[field] != value:
            raise ExtensionRefused(
                APPROVAL, f"advisory task {task_id!r} decided {field}={decision[field]!r}, not {value!r}"
            )
    return {"approval_task": task_id, "advisor_model": advisor, "approval_result_sha256": sealed.result_sha256}


def check_descent(repo_root: Path, *, approved: str, head: str, base_tip: str) -> list[str]:
    """The base commits merged on the first-parent path from ``head`` back to ``approved``."""
    merged: list[str] = []
    current = head
    while current != approved:
        if len(merged) >= MAX_BASE_MERGES:
            raise ExtensionRefused(DESCENT, f"{head} is not within {MAX_BASE_MERGES} base merges of {approved}")
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", current, reason=DESCENT).decode().split()
        if len(parents) != 3:
            raise ExtensionRefused(DESCENT, f"commit {current} between {approved} and {head} is not a two-parent merge")
        try:
            recorder._facts_git(
                repo_root,
                ["merge-base", "--is-ancestor", parents[2], base_tip],
                deadline=time.monotonic() + GIT_TIMEOUT_S,
                code=recorder.FACTS_TARGET_UNKNOWN,
            )
        except recorder.BranchFactsError as exc:
            if exc.timed_out:
                raise ExtensionRefused(DESCENT, str(exc)) from None
            raise ExtensionRefused(
                DESCENT, f"merge {current} brings in {parents[2]}, which is not on the base branch"
            ) from None
        merged.append(parents[2])
        current = parents[1]
    if not merged:
        raise ExtensionRefused(DESCENT, f"head {head} is the approved head; no base merge follows it")
    return merged


def admit_extension_round(
    *,
    repository: str,
    number: int,
    branch: str,
    head: str,
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
    repo_root: Path,
) -> dict[str, Any] | None:
    """The extension receipt admitting round ``budget + 1`` at ``head``; None when the PR has no request."""
    base_tip, _ = recorder.default_branch_review_base(repo_root, head)
    item = request_for(load_requests(repo_root, base_tip), number)
    if item is None:
        return None
    approved = item.request["approved_head"]
    try:
        seats = check_lineage(
            runs=lineage_runs(task_root, repository=repository, number=number, branch=branch),
            comments=comments,
            login=login,
            approved=approved,
            exclude_head=head,
        )
    except LineageRefused as exc:
        raise ExtensionRefused(LINEAGE, exc.detail) from None
    author = request_author_family(repo_root, base_tip, item, repository=repository, task_root=task_root)
    approval = check_approval(item, task_root=task_root, author_family=author)
    merged = check_descent(repo_root, approved=approved, head=head, base_tip=base_tip)
    return {
        "request": item.path,
        "request_sha256": item.sha256,
        "lineage_id": item.request["lineage_id"],
        "approved_head": approved,
        "seats": seats,
        "request_author_family": author,
        **approval,
        "base_merges": merged,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py budget-extension",
        description="Inspect a review budget extension request.\n"
        "The recorder admits the extension round itself; this verb only prints the digest to bind.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py budget-extension digest "
        f"{REQUEST_DIR}/pr-42.json\n"
        "Outputs: the request's canonical SHA-256 on stdout, for --advisory-binding.\n"
        "Exit codes: 0: valid request; 1: invalid request.\nRelated: scripts/review/budget_extension.py",
    )
    verbs = parser.add_subparsers(dest="verb", required=True)
    digest = verbs.add_parser("digest", help="Validate a request file and print its canonical SHA-256")
    digest.add_argument("request", type=Path, help=f"Request JSON, e.g. {REQUEST_DIR}/pr-42.json")
    args = parser.parse_args(argv)
    try:
        raw = args.request.read_bytes()
    except OSError as exc:
        print(f"budget extension request unreadable: {exc}")
        return 1
    try:
        request = parse_request(raw, str(args.request))
    except ExtensionRefused as exc:
        print(str(exc))
        return 1
    print(canonical_sha256(request))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
