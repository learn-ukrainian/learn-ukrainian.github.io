"""Sealed review-budget grants for one PR and its existing review lineage.

New CTO rulings have exactly REQUEST_FIELDS; existing elevated grants retain
their original fields and digests. The non-author designated advisor
seals every field plus decision and request_sha256 under review_budget_elevation.
Elevated blocker classes admit at most five rounds while the latest rejection
keeps the named P0/P1 open. A withheld-capability ruling instead seals blocked
run bindings and complete verification-only finding excerpts, plus a bound retry
probe demonstrating capability. It admits min(5, 3 + distinct qualifying heads).
A p2-fix-verification ruling seals the rejected and candidate heads, the delta
digest and the P2 finding ids; it admits round 4 only, once per work lineage,
consumed at dispatch (issue #12548; CTO proposal, Sol 6.1 APPROVE in task
cto-f932-rule-p2round2-sol). An owner-request ruling seals the tracker item recording
the project owner's request and the round count it records; it admits the PR's own
tier budget plus exactly that count, past five when the tier is already five, while
the latest recorded rejection lists the cited finding (issue #12551, tracker C-4100).
No path resets spent rounds or changes existing verdicts.

The designated advisor judges the semantics of the complete bound evidence;
this module verifies provenance, publication, current eligibility and allowance.
The cooperative threat model excludes a process rewriting task records or
publishing under another identity, as in bounded_advisory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.bounded_advisory import (
    ADVISORY_AGENTS,
    AdvisoryRefused,
    canonical_sha256,
    fenced_object,
    load_sealed_result,
)
from scripts.opsec.prepublish import normalize_repository
from scripts.orchestration.integration_sweep import REJECTED, REPLY_CLOSER, REPLY_OPENER, lookup_verdict
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME, read_task_record
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import REVIEW_BUDGET_ELEVATION_ROLE, advisory_role_policy, canonical_model_id
from scripts.review.reviewer_resolver import UNRESOLVED_AUTHOR_FAMILIES, resolve_family
from scripts.review.verdict_parser import (
    REVIEW_CAPABILITIES,
    checked_findings_payload,
    finding_entries,
    recognized_verdicts,
    structured_finding_entries,
)

# The CTO seat's stable Fleet Comms identity; session-specific slots are not issuers.
ISSUERS = frozenset({"claude-cto"})
# The change classes review-loop references/policy.md § Budget elevates.
WITHHELD_CAPABILITY = "withheld-capability"
P2_FIX = "p2-fix-verification"
P2_FIELD = "p2_fix_verification"
P2_FIELDS = frozenset({"rejected_head", "candidate_head", "delta_sha256", "finding_ids"})
# The project owner's request for more rounds on one PR (review-loop policy § Budget, `budget_tier: elevated`).
OWNER_REQUEST = "owner-request"
OWNER_FIELD = "owner_request"
OWNER_FIELDS = frozenset({"tracker_item", "rounds"})
TRACKER_ITEM = re.compile(r"C-[1-9][0-9]{0,5}")
LEGACY_CLASSES = frozenset({"security", "permissions", "authentication", "data-loss", "state-concurrency"})
BLOCKER_CLASSES = LEGACY_CLASSES | {WITHHELD_CAPABILITY, P2_FIX, OWNER_REQUEST}
# The single fix-verification round is round 4: the default budget plus one.
P2_ROUND_ALLOWANCE = recorder.DEFAULT_REVIEW_ROUNDS + 1
P2_RECEIPT_DIR = "review-p2-fix-rounds"
P2_RECEIPT_SCHEMA = "review-p2-fix-round.v1"
REQUEST_FIELDS = frozenset(
    {
        "repository",
        "pr",
        "lineage_id",
        "scope_paths",
        "finding_id",
        "blocker_class",
        "issuer",
        "issuer_model",
        "issued_at",
        "withheld_capability",
        P2_FIELD,
        OWNER_FIELD,
    }
)
FINDING_ID = re.compile(r"F[1-9][0-9]{0,3}")
BLOCKING_SEVERITIES = ("P0", "P1")

# Typed refusal reasons.
REQUEST = "request"
ISSUER = "issuer"
APPROVAL = "approval"
BINDING = "binding"
SCOPE = "scope"
BLOCKER = "blocker"
EVIDENCE = "evidence"
CAPABILITY = "capability"
SPENT = "spent"
VERIFICATION = "verification"
RUN_FIELDS = frozenset({"task_id", "run_nonce", "reviewed_sha", "reply_sha256"})
DIGEST = re.compile(r"[0-9a-f]{64}")
EXCLUSION_ATTESTATION = {
    "complete_reply_execution_obstruction_only": True,
    "no_substantive_defect": True,
    "no_security_fail": True,
}


class GrantRefused(recorder.RecordError):
    """An elevated-tier grant condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"BUDGET_GRANT_REFUSED[{reason}]: {detail}")
        self.reason = reason
        self.detail = detail


def parse_request(request: Any, label: str) -> dict[str, Any]:
    """The typed ruling in ``request``, or a refusal naming ``label``."""
    # Rulings sealed before a field existed keep their shape; a p2 or owner-request ruling always carries its own.
    blocker = request.get("blocker_class") if isinstance(request, dict) else None
    shapes = [REQUEST_FIELDS]
    if blocker != OWNER_REQUEST:
        shapes.append(REQUEST_FIELDS - {OWNER_FIELD})
        if blocker != P2_FIX:
            shapes.append(REQUEST_FIELDS - {OWNER_FIELD, P2_FIELD})
        if isinstance(blocker, str) and blocker in LEGACY_CLASSES:
            shapes.append(REQUEST_FIELDS - {OWNER_FIELD, P2_FIELD, "withheld_capability"})
    if not isinstance(request, dict) or set(request) not in shapes:
        found = sorted(request) if isinstance(request, dict) else type(request).__name__
        raise GrantRefused(REQUEST, f"{label} must hold exactly {sorted(REQUEST_FIELDS)}, found {found}")
    pr = request["pr"]
    if isinstance(pr, bool) or not isinstance(pr, int) or pr < 1:
        raise GrantRefused(REQUEST, f"{label} pr must be a positive integer")
    for field in ("repository", "lineage_id", "issuer", "issuer_model"):
        if not isinstance(request[field], str) or not request[field].strip():
            raise GrantRefused(REQUEST, f"{label} {field} must be a non-empty string")
    paths = request["scope_paths"]
    if (
        not isinstance(paths, list)
        or not paths
        or not all(isinstance(path, str) and path and not path.startswith("/") for path in paths)
        or paths != sorted(set(paths))
    ):
        raise GrantRefused(REQUEST, f"{label} scope_paths must be a sorted list of distinct repository paths")
    if not isinstance(request["finding_id"], str) or not FINDING_ID.fullmatch(request["finding_id"]):
        raise GrantRefused(REQUEST, f"{label} finding_id must match {FINDING_ID.pattern}")
    if not isinstance(request["blocker_class"], str) or request["blocker_class"] not in BLOCKER_CLASSES:
        raise GrantRefused(REQUEST, f"{label} blocker_class must be one of {sorted(BLOCKER_CLASSES)}")
    try:
        stamp = datetime.fromisoformat(str(request["issued_at"]).replace("Z", "+00:00"))
    except ValueError:
        stamp = None
    if not isinstance(request["issued_at"], str) or stamp is None or stamp.tzinfo is None:
        raise GrantRefused(REQUEST, f"{label} issued_at must be an ISO-8601 time with a timezone")
    withheld = request.get("withheld_capability")
    if request["blocker_class"] != WITHHELD_CAPABILITY:
        if withheld is not None:
            raise GrantRefused(REQUEST, f"{label} withheld_capability must be null for other classes")
    else:
        required = {"capability", "runs", "retry_probe"}
        if not isinstance(withheld, dict) or set(withheld) not in (required, required | {"admission_exclusion"}):
            raise GrantRefused(REQUEST, f"{label} withheld_capability needs capability, runs and retry_probe")
        if not isinstance(withheld["capability"], str) or withheld["capability"] not in REVIEW_CAPABILITIES:
            raise GrantRefused(REQUEST, f"{label} has an unknown capability")
        if not isinstance(withheld["runs"], list) or not withheld["runs"]:
            raise GrantRefused(REQUEST, f"{label} needs cited blocked runs")
        for run in withheld["runs"]:
            _parse_run(run, {"verification_only_evidence"}, label)
        _parse_run(withheld["retry_probe"], {"capability_evidence"}, label)
        if withheld.get("admission_exclusion") is not None:
            _parse_run(withheld["admission_exclusion"], set(), label)
    p2 = request.get(P2_FIELD)
    if request["blocker_class"] != P2_FIX:
        if p2 is not None:
            raise GrantRefused(REQUEST, f"{label} {P2_FIELD} must be null for other classes")
    elif (not isinstance(p2, dict) or set(p2) != P2_FIELDS
          or not all(isinstance(p2[key], str) and recorder.SHA.fullmatch(p2[key])
                     for key in ("rejected_head", "candidate_head"))
          or p2["rejected_head"] == p2["candidate_head"]
          or not isinstance(p2["delta_sha256"], str) or not DIGEST.fullmatch(p2["delta_sha256"])
          or not isinstance(p2["finding_ids"], list) or not p2["finding_ids"]
          or not all(isinstance(item, str) and FINDING_ID.fullmatch(item) for item in p2["finding_ids"])
          or p2["finding_ids"] != sorted(set(p2["finding_ids"]))
          or request["finding_id"] not in p2["finding_ids"]):
        raise GrantRefused(REQUEST, f"{label} {P2_FIELD} needs two distinct full heads, a delta digest and the "
                                    "sorted distinct finding ids, finding_id among them")
    owner = request.get(OWNER_FIELD)
    if request["blocker_class"] != OWNER_REQUEST:
        if owner is not None:
            raise GrantRefused(REQUEST, f"{label} {OWNER_FIELD} must be null for other classes")
    elif (not isinstance(owner, dict) or set(owner) != OWNER_FIELDS
          or not isinstance(owner["tracker_item"], str) or not TRACKER_ITEM.fullmatch(owner["tracker_item"])
          or isinstance(owner["rounds"], bool) or not isinstance(owner["rounds"], int) or owner["rounds"] < 1):
        raise GrantRefused(REQUEST, f"{label} {OWNER_FIELD} needs the tracker_item recording the owner's request "
                                    f"({TRACKER_ITEM.pattern}) and the positive count of rounds it records")
    return request


def _parse_run(run: Any, extra: set[str], label: str) -> None:
    if not isinstance(run, dict) or set(run) != RUN_FIELDS | extra:
        raise GrantRefused(REQUEST, f"{label} run must hold exactly {sorted(RUN_FIELDS | extra)}")
    if any(not isinstance(run[key], str) or not run[key].strip() for key in run):
        raise GrantRefused(REQUEST, f"{label} run fields must be non-empty strings")
    if not recorder.TASK_ID.fullmatch(run["task_id"]) or not re.fullmatch(r"[0-9A-Za-z._-]+", run["run_nonce"]):
        raise GrantRefused(REQUEST, f"{label} invalid task id or run nonce")
    if not recorder.SHA.fullmatch(run["reviewed_sha"]) or not DIGEST.fullmatch(run["reply_sha256"]):
        raise GrantRefused(REQUEST, f"{label} run needs a full reviewed SHA and reply digest")


@dataclass(frozen=True)
class Grant:
    task_id: str
    request: dict[str, Any]
    request_sha256: str
    advisor_model: str
    result_sha256: str
    admission_exclusion_attestation: dict[str, bool] | None = None


def _grant_records(task_root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Every hot or archived finished task record that ran the elevation role."""
    found = []
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise GrantRefused(APPROVAL, f"task ledger unavailable: {exc}") from None
    for path in paths:
        try:
            record = read_task_record(path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise GrantRefused(APPROVAL, f"task record {path.name} unreadable: {exc}") from None
        if isinstance(record, dict) and record.get("advisory_role") == REVIEW_BUDGET_ELEVATION_ROLE:
            task_id = record.get("task_id")
            if record.get("status") == "done":
                found.append((task_id if isinstance(task_id, str) and task_id else path.stem, path, record))
    return found


def _sealed_ruling(task_id: str, path: Path, record: Mapping[str, Any]) -> tuple[dict[str, Any], Any]:
    """The typed object a finished elevation task sealed, read under the model its record names."""
    try:
        policy = advisory_role_policy(REVIEW_BUDGET_ELEVATION_ROLE)
    except KeyError:
        raise GrantRefused(APPROVAL, f"the model catalog defines no {REVIEW_BUDGET_ELEVATION_ROLE} role") from None
    try:
        sealed = load_sealed_result(
            task_id,
            state_path=path,
            role=policy.role,
            route=policy.route,
            model_id=canonical_model_id(record.get("model")),
            binding_sha256=str(record.get("advisory_binding_sha256")),
        )
        decision = fenced_object(sealed.result_text, policy.fence)
        # The shapes sealed before each later field; parse_request decides which class may use which.
        base = set(policy.output_fields) - {P2_FIELD, OWNER_FIELD}
        shapes = [base | {P2_FIELD, OWNER_FIELD}, base | {P2_FIELD}, base, base - {"admission_exclusion_attestation"}]
        if isinstance(decision.get("blocker_class"), str) and decision["blocker_class"] in LEGACY_CLASSES:
            shapes += [shape - {"withheld_capability"} for shape in shapes[2:]]
        if set(decision) not in shapes:
            raise GrantRefused(
                APPROVAL,
                f"the {policy.fence} object must hold exactly {list(policy.output_fields)}, found {sorted(decision)}",
            )
        sealed.require_sealed_object(decision, task_id)
    except AdvisoryRefused as exc:
        raise GrantRefused(APPROVAL, str(exc)) from None
    return decision, sealed


def check_grant(task_id: str, path: Path, record: Mapping[str, Any]) -> Grant:
    """The ruling a finished task sealed, from the non-author advisor, issued by the stable CTO identity."""
    policy = advisory_role_policy(REVIEW_BUDGET_ELEVATION_ROLE)
    if record.get("agent") not in ADVISORY_AGENTS:
        # Only a native harness runs the model it records (dispatcher ``check_advisory_role``).
        raise GrantRefused(
            APPROVAL, f"advisory task {task_id!r} ran on harness {record.get('agent')!r}, not a native one"
        )
    decision, sealed = _sealed_ruling(task_id, path, record)
    request = parse_request({field: decision[field] for field in REQUEST_FIELDS if field in decision},
                            f"advisory task {task_id!r} ruling")
    digest = canonical_sha256(request)
    if decision["request_sha256"] != digest or record.get("advisory_binding_sha256") != digest:
        raise GrantRefused(BINDING, f"advisory task {task_id!r} is not bound to the ruling it carries ({digest})")
    if decision["decision"] != "APPROVE":
        raise GrantRefused(
            APPROVAL, f"advisory task {task_id!r} decided decision={decision['decision']!r}, not 'APPROVE'"
        )
    issuer = request["issuer"]
    if issuer not in ISSUERS:
        raise GrantRefused(ISSUER, f"ruling issuer {issuer!r} is not the stable CTO identity {sorted(ISSUERS)}")
    if record.get("initiator") != issuer:
        raise GrantRefused(
            ISSUER,
            f"advisory task {task_id!r} was dispatched by {record.get('initiator')!r}, not the issuer {issuer!r}",
        )
    family = resolve_family(request["issuer_model"])
    if family in UNRESOLVED_AUTHOR_FAMILIES or family == "unknown":
        raise GrantRefused(ISSUER, f"issuer model {request['issuer_model']!r} has no resolvable family")
    advisor = policy.advisor_outside(family)
    if advisor is None:
        raise GrantRefused(
            APPROVAL,
            f"a ruling issued in family {family!r} has no single non-author designated advisor "
            "(operator-expectations item 12 needs both; escalate to the operator)",
        )
    if canonical_model_id(record.get("model")) != advisor:
        raise GrantRefused(
            APPROVAL, f"advisory task {task_id!r} ran on {record.get('model')!r}, not the advisor {advisor}"
        )
    attestation = decision.get("admission_exclusion_attestation")
    exclusion = (request.get("withheld_capability") or {}).get("admission_exclusion")
    if exclusion is not None:
        if (not isinstance(attestation, dict) or set(attestation) != set(EXCLUSION_ATTESTATION)
                or any(value is not True for value in attestation.values())):
            raise GrantRefused(APPROVAL, "exclusion needs the advisor's sealed complete-reply semantic attestation")
    elif attestation is not None:
        raise GrantRefused(APPROVAL, "exclusion attestation has no bound exclusion")
    return Grant(task_id, request, digest, advisor, sealed.result_sha256, attestation)


def _claimed_pr(path: Path) -> Any:
    """The PR a refused grant's result names, read without any check: it only decides who hears the refusal."""
    try:
        policy = advisory_role_policy(REVIEW_BUDGET_ELEVATION_ROLE)
        return fenced_object(path.with_suffix(".result").read_text(encoding="utf-8"), policy.fence).get("pr")
    except (AdvisoryRefused, KeyError, OSError, UnicodeDecodeError, AttributeError):
        return None


_STILL_OPEN = re.compile(
    r"\bstill open\b|\bremains open\b|\bunresolved\b|\bnot (?:yet )?(?:resolved|fixed|addressed)\b", re.I
)
_CLOSED = re.compile(r"\b(?:resolved|fixed|declined|withdrawn|closed|addressed|superseded)\b", re.I)
_STANDALONE_CLOSED = re.compile(rf"(?<!\w-){_CLOSED.pattern}(?!-\w)", re.I)


def finding_is_open(entry: str) -> bool:
    """Whether an entry is unambiguous evidence that its finding is still open; ambiguity refuses.

    Any standalone closing word (``resolved``, ``fixed``, ``declined`` …)
    anywhere in the entry closes it, whatever it is about, unless the word
    sits inside an open phrase (``not resolved``, ``unresolved`` …).
    With an explicit open phrase, closing words inside hyphenated compounds
    (``fail-closed``, ``closed-form``, ``fixed-width`` …) do not close the entry.
    Without an open phrase, compound closing words still refuse. So a granted round
    needs the reviewer to keep the finding open in plain words, such as
    ``still open: <reason>``, or to raise it new; mixed language never
    admits a round.
    """
    opened = [match.span() for match in _STILL_OPEN.finditer(entry)]
    closing = _STANDALONE_CLOSED if opened else _CLOSED
    return not any(not any(start <= match.start() < end for start, end in opened) for match in closing.finditer(entry))


def _findings_schema_bound(record: Mapping[str, Any]) -> bool | None:
    """Whether a review run was bound to ``code-review-findings.v1``; None when it was bound to anything else."""
    from scripts.review.review_contract import SCHEMA_RELATIVE_PATH, package_repo_root

    path = record.get("output_schema_path")
    if path is None:
        return False
    expected = hashlib.sha256((package_repo_root() / SCHEMA_RELATIVE_PATH).read_bytes()).hexdigest()
    if (not isinstance(path, str) or not Path(path).as_posix().endswith("/" + SCHEMA_RELATIVE_PATH)
            or record.get("output_schema_sha256") != expected):
        return None
    return True


def open_blocker_cited(
    comments: Sequence[Mapping[str, Any]], login: str, finding_id: str, runs: Sequence[Any] | None = None
) -> str | None:
    """The head of the latest recorded verdict when it is a trusted rejection leaving ``finding_id`` an open P0/P1.

    The keeper must read that head as rejected (an edited or unattested
    marker reads as unknown), and the finding's last entry in the reply
    decides its disposition (:func:`finding_is_open`), and its last stated
    severity must be P0 or P1.

    The reply format comes from the recorded run, never from the reply text (#12549). With
    ``runs`` (the PR's review runs), the marker must name exactly one run (task and start). A run
    bound to the ``code-review-findings.v1`` schema is read only from its sealed reply through
    the structured parser, and any failure refuses. A run with no output schema is read as a markdown
    ledger, and a run bound to another schema refuses. Without ``runs``, only the markdown ledger is read.
    Withheld findings are evidence only from a schema-bound run that :func:`_withheld_reply` binds
    to the comment, and only when that sealed reply is not cut (#12592).
    """
    markers = recorder._trusted_markers(comments, login)
    if not markers:
        return None
    index, marker = markers[-1]
    head = marker["sha"]
    if marker["verdict"] not in REJECTED or lookup_verdict(comments, head, login).state not in REJECTED:
        return None
    comment = comments[index]
    if comment.get("created_at") != comment.get("updated_at"):
        return None
    body = comment.get("body")
    published = body.partition("<details>")[2] if isinstance(body, str) else ""
    bound = False
    if runs is not None:
        from scripts.review.capability_failure import run_started

        matches = [run for run in runs if run.task_id == marker["task"] and run_started(run.record) == marker["started"]]
        bound = _findings_schema_bound(matches[0].record) if len(matches) == 1 else None
        if bound is None:
            return None
    if bound:
        # A withheld verdict publishes no reply: only the sealed reply of the one run it records,
        # bound as for the owner-request and p2 grants and not cut, is evidence (#12592).
        reply = matches[0].reply if published else _withheld_reply(body, runs)
        if not published and isinstance(reply, str) and recorder.TRUNCATION_FLAG in reply:
            return None
        entries = structured_finding_entries(reply, finding_id) if isinstance(reply, str) else None
        if entries is None:
            return None
    else:
        entries = finding_entries(published, finding_id)
    severities = [severity for severity, _ in entries if severity]
    if not entries or not severities or severities[-1] not in BLOCKING_SEVERITIES:
        return None
    return head if finding_is_open(entries[-1][1]) else None


def admit_grant_round(
    *,
    repository: str,
    number: int,
    branch: str,
    changed_paths: Sequence[str],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
    head: str,
    recording_run: tuple[str, str] | None = None,
    repo_root: Path | None = None,
    budget: int = recorder.DEFAULT_REVIEW_ROUNDS,
) -> dict[str, Any] | None:
    """The receipt of a grant admitting this round; None when the PR has no grant, or a refusal.

    ``budget`` is the PR's own tier budget, which an owner-request grant extends.
    """
    grants: list[Grant] = []
    refusals: list[GrantRefused] = []
    for task_id, path, record in _grant_records(task_root):
        try:
            grant = check_grant(task_id, path, record)
        except GrantRefused as exc:
            # A refused grant for another PR is not this PR's concern; an unreadable one names no PR.
            if _claimed_pr(path) == number:
                refusals.append(exc)
            continue
        if grant.request["pr"] == number:
            grants.append(grant)
    receipts = []
    exclusions = {
        tuple(sorted(exclusion.items()))
        for grant in grants
        if normalize_repository(grant.request["repository"]) == normalize_repository(repository)
        and (exclusion := (grant.request.get("withheld_capability") or {}).get("admission_exclusion")) is not None
    }
    if len(exclusions) > 1:
        raise GrantRefused(BINDING, "only one excluded run per PR, including across reissued grants")
    for grant in grants:
        try:
            receipts.append(_admit(
                grant, repository=repository, branch=branch, changed_paths=changed_paths, comments=comments, login=login,
                task_root=task_root, head=head, recording_run=recording_run, repo_root=repo_root, budget=budget,
            ))
        except GrantRefused as exc:
            refusals.append(exc)
    if receipts:
        return max(receipts, key=lambda receipt: receipt["round_allowance"])
    if refusals:
        raise GrantRefused(refusals[0].reason, "; ".join(exc.detail for exc in refusals))
    return None


def _admit(
    grant: Grant,
    *,
    repository: str,
    branch: str,
    changed_paths: Sequence[str],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
    head: str,
    recording_run: tuple[str, str] | None,
    repo_root: Path | None = None,
    budget: int = recorder.DEFAULT_REVIEW_ROUNDS,
) -> dict[str, Any]:
    """This one grant's receipt for the round, or why it does not apply."""
    request = grant.request
    if normalize_repository(request["repository"]) != normalize_repository(repository):
        raise GrantRefused(BINDING, f"grant {grant.task_id!r} names repository {request['repository']!r}")
    if request["lineage_id"] != branch:
        raise GrantRefused(
            BINDING, f"grant {grant.task_id!r} follows lineage {request['lineage_id']!r}, not this PR's {branch!r}"
        )
    outside = sorted(set(changed_paths) - set(request["scope_paths"]))
    if outside:
        raise GrantRefused(SCOPE, f"grant {grant.task_id!r} does not cover changed paths {outside}")
    withheld_receipt = {}
    if request["blocker_class"] == WITHHELD_CAPABILITY:
        withheld_receipt = _withheld_round(grant, comments=comments, login=login, task_root=task_root, head=head,
                                          recording_run=recording_run)
        cited = withheld_receipt["cited_verdict_head"]
    elif request["blocker_class"] == P2_FIX:
        withheld_receipt = _p2_fix_round(grant, comments=comments, login=login, task_root=task_root, head=head,
                                         repo_root=repo_root, recording_run=recording_run)
        cited = withheld_receipt["cited_verdict_head"]
    elif request["blocker_class"] == OWNER_REQUEST:
        withheld_receipt = _owner_round(grant, comments=comments, login=login, task_root=task_root, budget=budget)
        cited = withheld_receipt["cited_verdict_head"]
    else:
        from scripts.review import review_lineage as lineage

        try:
            runs = lineage.lineage_runs(task_root, repository=request["repository"], number=request["pr"],
                                        branch=request["lineage_id"])
        except lineage.LineageRefused as exc:
            raise GrantRefused(EVIDENCE, f"grant {grant.task_id!r}: review runs unreadable: {exc}") from None
        cited = open_blocker_cited(comments, login, request["finding_id"], runs)
    if cited is None:
        raise GrantRefused(
            BLOCKER,
            f"grant {grant.task_id!r}: the latest recorded verdict does not leave {request['finding_id']} "
            "an open P0/P1 blocker",
        )
    return {
        "grant_task": grant.task_id,
        "request_sha256": grant.request_sha256,
        "advisor_model": grant.advisor_model,
        "approval_result_sha256": grant.result_sha256,
        "finding_id": request["finding_id"],
        "blocker_class": request["blocker_class"],
        "cited_verdict_head": cited,
        "round_allowance": recorder.ELEVATED_REVIEW_ROUNDS,
        **withheld_receipt,
    }


def _owner_round(
    grant: Grant, *, comments: Sequence[Mapping[str, Any]], login: str, task_root: Path, budget: int
) -> dict[str, Any]:
    """The owner's recorded rounds on top of the PR's tier budget, while its latest rejection lists the finding.

    The designated advisor confirms the sealed count is the one the tracker item records;
    this checks only that the round follows an unedited trusted rejection naming the cited finding.
    """
    request = grant.request
    markers = recorder._trusted_markers(comments, login)
    if not markers:
        raise GrantRefused(BLOCKER, f"grant {grant.task_id!r}: no recorded verdict")
    index, latest = markers[-1]
    comment = comments[index]
    if (latest["verdict"] not in REJECTED or lookup_verdict(comments, latest["sha"], login).state not in REJECTED
            or comment.get("created_at") != comment.get("updated_at")):
        raise GrantRefused(BLOCKER, f"grant {grant.task_id!r}: the latest recorded verdict is not an unedited "
                                    "trusted rejection")
    runs = None
    if REPLY_OPENER not in str(comment.get("body")):
        # Only a withheld verdict needs its run's sealed reply.
        from scripts.review import review_lineage as lineage

        try:
            runs = lineage.lineage_runs(task_root, repository=request["repository"], number=request["pr"],
                                        branch=request["lineage_id"])
        except lineage.LineageRefused as exc:
            raise GrantRefused(EVIDENCE, f"grant {grant.task_id!r}: review runs unreadable: {exc}") from None
    read = _recorded_findings(comment, runs)
    if read is None or request["finding_id"] not in read[1]:
        raise GrantRefused(BLOCKER, f"grant {grant.task_id!r}: the latest recorded rejection does not list "
                                    f"{request['finding_id']}")
    owner = request[OWNER_FIELD]
    return {"cited_verdict_head": latest["sha"], "round_allowance": budget + owner["rounds"], OWNER_FIELD: dict(owner)}


def _admission_exclusion(
    grant: Grant, *, runs: Sequence[Any], markers: Sequence[Any], head: str,
    recording_run: tuple[str, str] | None, comments: Sequence[Mapping[str, Any]], login: str,
) -> dict[str, Any]:
    """Validate one sealed obstruction before dispatch and its exact replacement at recording.

    The advisor judges the complete reply, including defects expressed only in prose.
    Empty findings are only a structural check, never that semantic attestation.
    """
    from scripts.review import review_lineage as lineage

    request = grant.request
    evidence = request["withheld_capability"].get("admission_exclusion")
    if evidence is None:
        return {}
    if grant.admission_exclusion_attestation != EXCLUSION_ATTESTATION:
        raise GrantRefused(APPROVAL, "missing sealed exclusion attestation")
    matches = [run for run in runs if run.task_id == evidence["task_id"]
               and run.record.get("run_nonce") == evidence["run_nonce"]]
    if len(matches) != 1:
        raise GrantRefused(EVIDENCE, "excluded run is missing or ambiguous")
    excluded = matches[0]
    lineage.require_run_binding(evidence, excluded.record, repository=request["repository"],
                                number=request["pr"], branch=request["lineage_id"])
    try:
        payload = json.loads(excluded.reply, object_pairs_hook=recorder._unique_keys,
                             parse_constant=recorder._not_json_constant)
    except (TypeError, ValueError, RecursionError):
        raise GrantRefused(EVIDENCE, "excluded reply must be one structured findings object") from None
    derived = lineage._finished_verdict(excluded)
    if (not isinstance(payload, dict) or payload.get("schema_version") != recorder.REVIEW_SCHEMA_VERSION
            or payload.get("findings") != [] or derived is None or derived[1:3] != ("BLOCKED", 0)
            or evidence["reviewed_sha"] != head
            or any(re.search(r"\bP[0-3]\b", text) or recorder._security_verdict_blocks(text)
                   for text in recorder._strings(payload))
            or any(marker["task"] == excluded.task_id for _, marker in markers)):
        raise GrantRefused(BLOCKER, "excluded run is not an unpublished, empty-findings BLOCKED at the retry head")
    started = lineage._started(excluded.record)
    if lineage.capability_failure.run_events(lineage.capability_failure.events(comments, login), excluded.task_id, started):
        raise GrantRefused(EVIDENCE, "excluded run already has a capability-failure classification")
    if datetime.fromisoformat(started) >= datetime.fromisoformat(request["issued_at"].replace("Z", "+00:00")):
        raise GrantRefused(EVIDENCE, "exclusion must precede its reissued grant")
    replacement = None
    if recording_run is not None:
        matches = [run for run in runs if (run.task_id, run.record.get("run_nonce")) == recording_run]
        if len(matches) != 1:
            raise GrantRefused(EVIDENCE, "replacement run is missing or ambiguous")
        run = matches[0]
        replacement = {"task_id": run.task_id, "run_nonce": run.record.get("run_nonce"),
                       "reviewed_sha": head, "reply_sha256": run.record.get("result_sha256")}
        lineage.require_run_binding(replacement, run.record, repository=request["repository"],
                                    number=request["pr"], branch=request["lineage_id"])
        retry = lineage._finished_verdict(run)
        if (retry is None or retry[4] != derived[4] or lineage._profile(run.record) != lineage._profile(excluded.record)
                or datetime.fromisoformat(retry[5]) <= datetime.fromisoformat(started)):
            raise GrantRefused(BINDING, "replacement must be a later same-seat, same-head review")
    return {"excluded_run": evidence, "replacement_run": replacement,
            "admission_exclusion_attestation": grant.admission_exclusion_attestation}


def _withheld_round(
    grant: Grant, *, comments: Sequence[Mapping[str, Any]], login: str, task_root: Path, head: str,
    recording_run: tuple[str, str] | None,
) -> dict[str, Any]:
    # The sealed advisor attests that each complete finding excerpt describes a corrected
    # defect awaiting verification only, and that the probe excerpt demonstrates capability.
    # These semantic attestations never replace the run and publication checks below.
    from scripts.review import review_lineage as lineage

    request = grant.request
    withheld = request["withheld_capability"]
    try:
        runs = lineage.lineage_runs(task_root, repository=request["repository"], number=request["pr"],
                                    branch=request["lineage_id"])
        markers = lineage._trusted_markers(comments, login)
        exclusion = _admission_exclusion(grant, runs=runs, markers=markers, head=head, recording_run=recording_run,
                                        comments=comments, login=login)
        charged = lineage.dispatched_rounds(runs=runs, comments=comments, login=login, exclude_head=head)
        sources = []
        for evidence in withheld["runs"]:
            run, marker = lineage.bound_published_run(
                evidence, runs=runs, comments=comments, login=login,
                repository=request["repository"], number=request["pr"], branch=request["lineage_id"],
            )
            reply = run.reply
            entries = finding_entries(reply, request["finding_id"])
            excerpt = evidence["verification_only_evidence"]
            ids = set(re.findall(r"\bF[1-9][0-9]{0,3}\b", reply))
            other_entries = [finding_entries(reply, finding) for finding in ids - {request["finding_id"]}]
            missing = re.search(r"^VERDICT:\s*BLOCKED\s*\(missing capability:\s*([^)]+)\)", reply, re.M | re.I)
            capability = withheld["capability"]
            names = [capability, capability.replace("-", " ")]
            if capability in {"shell", "test-execution"}:
                names.append("running code")
            if (marker["verdict"] != "BLOCKED" or recognized_verdicts(reply) != ["BLOCKED"]
                    or missing is None or not any(re.search(r"\b" + re.escape(name) + r"\b", missing[1], re.I)
                                                  for name in names)
                    or any(not found or any(severity != "P3" for severity, _ in found) for found in other_entries)
                    or not entries
                    or excerpt != entries[-1][1]
                    or not re.search(r"\b(?:corrected|resolved|fixed)\b", _STILL_OPEN.sub("", excerpt), re.I)
                    or not re.search(r"\b(?:probe|verif|test|execut)\w*", excerpt, re.I)):
                raise GrantRefused(BLOCKER, f"{run.task_id}: not a capability-only verification rejection")
            critical = [severity for severity, _ in entries if severity in BLOCKING_SEVERITIES]
            prior = [severity for index, old in recorder._trusted_markers(comments, login)
                     if old["started"] < marker["started"]
                     for severity, _ in finding_entries(comments[index]["body"], request["finding_id"])
                     if severity]
            if critical and (not prior or min(critical) < prior[-1]):
                raise GrantRefused(BLOCKER, f"{run.task_id}: a new P0/P1 finding was raised")
            if marker["sha"] not in charged:
                raise GrantRefused(EVIDENCE, f"{run.task_id}: cited head is not an already charged round")
            sources.append((run, marker))
        latest = markers[-1][1] if markers else None
        if latest not in [marker for _, marker in sources]:
            raise GrantRefused(BLOCKER, "latest rejection is not a cited capability-only run")
        first_start = min(marker["started"] for _, marker in sources)
        cited_keys = {(run.task_id, marker["started"]) for run, marker in sources}
        for _, marker in markers:
            if (marker["started"] >= first_start and marker["verdict"] != "APPROVED"
                    and (marker["task"], marker["started"]) not in cited_keys):
                raise GrantRefused(BLOCKER, f"{marker['task']}: a substantive rejection intervened")
        for run in runs:
            started = lineage._started(run.record)
            if exclusion and (run.task_id, run.record.get("run_nonce")) == (
                exclusion["excluded_run"]["task_id"], exclusion["excluded_run"]["run_nonce"]
            ):
                continue
            if recording_run is not None and (run.task_id, run.record.get("run_nonce")) == recording_run:
                continue
            if started is None:
                raise GrantRefused(EVIDENCE, f"{run.task_id}: review start unavailable")
            if started < first_start:
                continue
            # No substantive or unpublished rejection may intervene, even on a different seat.
            evidence = lineage._finished_verdict(run)
            if evidence is None or (evidence[1] != "APPROVED" and (run.task_id, started) not in cited_keys):
                raise GrantRefused(BLOCKER, f"{run.task_id}: a substantive or unknown review intervened")
            lineage.bound_published_run(
                {"task_id": run.task_id, "run_nonce": run.record.get("run_nonce"),
                 "reviewed_sha": run.record.get("worktree_base_sha"), "reply_sha256": run.record.get("result_sha256")},
                runs=runs, comments=comments, login=login, repository=request["repository"],
                number=request["pr"], branch=request["lineage_id"],
            )
        probe_evidence = withheld["retry_probe"]
        probe, reply = recorder._task(probe_evidence["task_id"], task_root)
        lineage.require_run_binding(probe_evidence, probe, repository=request["repository"],
                                    number=None, branch=request["lineage_id"])
        excerpt = probe_evidence["capability_evidence"]
        if (probe_evidence["reviewed_sha"] != head or excerpt not in reply
                or probe.get("mode") != "read-only"
                or re.search(r"missing capability|\b(?:FAIL|BLOCKED)\b", reply, re.I)):
            raise GrantRefused(CAPABILITY, "retry probe does not demonstrate the capability at this head")
        model, _ = recorder.reviewer_identity(probe)
        route = {"agent": probe.get("agent"), "model": model, "mode": probe["mode"]}
        if not isinstance(route["agent"], str) or not route["agent"]:
            raise GrantRefused(CAPABILITY, "retry probe has no recorded harness")
        for run in runs:
            if run.record.get("worktree_base_sha") == head:
                candidate_model, _ = recorder.reviewer_identity(run.record)
                if {"agent": run.record.get("agent"), "model": candidate_model, "mode": run.record.get("mode")} != route:
                    raise GrantRefused(CAPABILITY, f"{run.task_id}: retry route differs from demonstrated route")
    except lineage.LineageRefused as exc:
        raise GrantRefused(EVIDENCE, exc.detail) from None
    except recorder.RecordError as exc:
        if isinstance(exc, GrantRefused):
            raise
        raise GrantRefused(EVIDENCE, str(exc)) from None
    qualifying_heads = sorted({marker["sha"] for _, marker in sources})
    return {
        "cited_verdict_head": latest["sha"],
        "qualifying_heads": qualifying_heads,
        "round_allowance": min(recorder.ELEVATED_REVIEW_ROUNDS, recorder.DEFAULT_REVIEW_ROUNDS + len(qualifying_heads)),
        "retry_route": route,
        "retry_probe": probe_evidence,
        **exclusion,
    }


def _duplicate_key(reply: str) -> bool:
    """Whether a JSON object at any brace of the reply repeats a key, which the canonical parser drops silently.

    Every brace is tried, so no wrapper, line ending or leading whitespace the parser normalizes hides one.
    """
    decoder = json.JSONDecoder(object_pairs_hook=recorder._unique_keys)
    for match in re.finditer(r"\{", reply):
        try:
            decoder.raw_decode(reply, match.start())
        except recorder._DuplicateKey:
            return True
        except (ValueError, RecursionError):
            continue
    return False


def _structured_reply(reply: str) -> tuple[dict[str, Any], tuple[Any, ...]] | None:
    """A structured reply's payload and validated findings (bare, fenced or a VERDICT envelope); None for prose."""
    from scripts.review.review_contract import parse_reviewer_json

    try:
        payload = parse_reviewer_json(reply)
    except recorder.ContractError:
        return None
    if payload.get("schema_version") != recorder.REVIEW_SCHEMA_VERSION:
        return None
    if _duplicate_key(reply):
        raise ValueError("a findings object repeats a key")
    _, evidence = checked_findings_payload(payload)
    return payload, tuple(evidence.findings) if evidence is not None else ()


def _reply_findings(reply: str) -> tuple[bool, dict[str, list[str | None]]] | None:
    """Whether a reply is structured, and the severities of each open finding it names; None when unreadable.

    A structured object lists its open findings. A prose entry always reads as open, since prose cannot
    tell a disposition from a description or an example; an id named outside an entry refuses.
    """
    try:
        structured = _structured_reply(reply)
    except (recorder.ContractError, recorder.ReviewPublicationError, ValueError, RecursionError):
        return None
    if structured is not None:
        found: dict[str, list[str | None]] = {}
        for finding in structured[1]:
            found.setdefault(finding.finding_id, []).append(finding.priority)
        return True, found
    named = {finding: [severity for severity, _ in finding_entries(reply, finding)]
             for finding in set(re.findall(r"\bF[1-9][0-9]{0,3}\b", reply))}
    return None if any(not entries for entries in named.values()) else (False, named)


# The recorder's withheld-findings lines, current and earlier wording (integration_sweep reads both).
_WITHHELD_LINES = (
    "Findings are held privately.",
    "Findings are held privately on the host in CF run output files (`out/<task>.final` and `out/<task>.md`).",
)


def _withheld_reply(body: str, runs: Sequence[Any] | None) -> str | None:
    """The sealed reply of the one run a withheld verdict records; None when no run binds it (#12585).

    The run is the PR's only one with the marker's task and start, its record seals the reply's
    digest (which ``review_lineage`` checks on reading), and its head, verdict, reviewer and finding
    count are exactly what the comment records.
    """
    from scripts.review import review_lineage as lineage

    marker = recorder.parse_marker(body)
    if marker is None or runs is None:
        return None
    matches = [run for run in runs if run.task_id == marker["task"] and lineage._started(run.record) == marker["started"]]
    derived = lineage._finished_verdict(matches[0]) if len(matches) == 1 else None
    if (derived is None or not isinstance(matches[0].record.get("result_sha256"), str)
            or (marker["sha"], marker["verdict"], marker["model"], marker["family"]) != (*derived[:2], *derived[3:5])):
        return None
    record = body.rpartition("<!-- cf-verdict v1 ")[0]
    if not any(record.endswith(f"\nWithheld findings: {derived[2]}\n{line}\n\n") for line in _WITHHELD_LINES):
        return None
    return matches[0].reply


def _recorded_findings(
    comment: Mapping[str, Any], runs: Sequence[Any] | None = None
) -> tuple[bool, dict[str, list[str | None]]] | None:
    """A recorded verdict's findings; None when its reply is cut or unreadable, or withheld and unbound.

    A withheld verdict publishes no reply, so its findings come from the sealed reply of the run it
    records, among ``runs`` (:func:`_withheld_reply`). Only finding ids and severities are returned,
    so no withheld text leaves the check.
    """
    body = comment.get("body")
    if not isinstance(body, str):
        return None
    _, opened, rest = body.partition(REPLY_OPENER)
    if opened:
        reply, closed, _ = rest.rpartition(REPLY_CLOSER)
        if not closed:
            return None
    else:
        reply = _withheld_reply(body, runs) or ""
    # A sealed reply is intact, not necessarily complete: a cut one refuses in either form.
    if not reply.strip() or recorder.TRUNCATION_FLAG in reply:
        return None
    return _reply_findings(reply)


_LINKED_PRS = """query($owner: String!, $name: String!, $pr: Int!) { repository(owner: $owner, name: $name) {
  pullRequest(number: $pr) { closingIssuesReferences(first: 50) { nodes { number
    closedByPullRequestsReferences(first: 50, includeClosedPrs: true) { nodes { number } } } } } } }"""


def _lineage_links(repository: str, number: int) -> tuple[list[int], list[int]]:
    """The issues this PR closes, and every other PR, open or closed, that closes one of them."""
    owner, name = normalize_repository(repository).split("/")[-2:]
    data = recorder._run_json(["gh", "api", "graphql", "-F", f"owner={owner}", "-F", f"name={name}",
                               "-F", f"pr={number}", "-f", f"query={_LINKED_PRS}"])
    try:
        issues = data["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["nodes"]
        return (sorted({issue["number"] for issue in issues}),
                sorted({pr["number"] for issue in issues for pr in issue["closedByPullRequestsReferences"]["nodes"]}
                       - {number}))
    except (KeyError, TypeError) as exc:
        raise GrantRefused(EVIDENCE, f"PR #{number} lineage links unavailable: {exc!r}") from None


def _delta_sha256(repo_root: Path, rejected: str, candidate: str) -> str:
    from scripts.review.repair_round import _diff_sha256

    return _diff_sha256(repo_root, rejected, candidate)


def _p2_receipts(task_root: Path) -> Path:
    """Beside the task ledger, never removed, like the repair rounds' receipts."""
    return task_root.parent / P2_RECEIPT_DIR


def _read_p2_receipt(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise GrantRefused(SPENT, f"p2 round receipt {path.name} unreadable: {exc}") from None
    if not isinstance(data, dict) or data.get("schema") != P2_RECEIPT_SCHEMA:
        raise GrantRefused(SPENT, f"p2 round receipt {path.name} is not a {P2_RECEIPT_SCHEMA} record")
    return data


def _same_p2_round(receipt: Mapping[str, Any], other: Mapping[str, Any]) -> bool:
    return all(receipt.get(key) == other.get(key) for key in ("repository", "pr", "candidate_head"))


def _p2_fix_round(
    grant: Grant, *, comments: Sequence[Mapping[str, Any]], login: str, task_root: Path, head: str,
    repo_root: Path | None, recording_run: tuple[str, str] | None,
) -> dict[str, Any]:
    """Rule 1 against the complete ledger, the sealed binding, and the lineage's single use (#12548)."""
    from scripts.review import review_lineage as lineage
    from scripts.review.repair_round import RepairRefused, _receipt_path, lineage_keys

    request = grant.request
    p2 = request[P2_FIELD]
    if p2["candidate_head"] != head:
        raise GrantRefused(BINDING, f"grant {grant.task_id!r} seals candidate {p2['candidate_head']}, not {head}")
    markers = recorder._trusted_markers(comments, login)
    if not markers:
        raise GrantRefused(BLOCKER, "no recorded verdict")
    latest = markers[-1][1]
    if latest["sha"] != p2["rejected_head"]:
        raise GrantRefused(BINDING, f"the latest recorded verdict is at {latest['sha']}, not the sealed rejected head")
    if (latest["verdict"] != "CHANGES_REQUESTED"
            or lookup_verdict(comments, latest["sha"], login).state != "CHANGES_REQUESTED"):
        raise GrantRefused(BLOCKER, "the latest recorded verdict is not a trusted REJECT")
    try:
        runs, runs_refusal = lineage.lineage_runs(task_root, repository=request["repository"], number=request["pr"],
                                                  branch=request["lineage_id"]), None
    except lineage.LineageRefused as exc:
        runs, runs_refusal = [], exc
    # A finished run whose verdict its seat superseded is no obstruction (rule 5), but supersession resolves
    # no finding: its findings stay open until a recorded structured verdict that started after the run omits
    # them (an earlier-started verdict never saw them), and while open they bind the checks below.
    superseded = lineage.superseded_runs(runs=runs, comments=comments, login=login, exclude_head=head)
    replies = {(run.task_id, lineage._started(run.record)): run.reply for run in runs}
    raised: list[tuple[str, dict[str, list[str | None]]]] = []
    blocking: set[str] = set()
    for entry in superseded:
        text = str(replies[(entry["task"], entry["started"])])
        read = _reply_findings(text)
        if entry["verdict"] == "BLOCKED" or read is None or recorder._security_verdict_blocks(text):
            raise GrantRefused(BLOCKER, f"{entry['task']}: the ledger holds a BLOCKED, a security FAIL, "
                                        "or an edited, withheld or unreadable verdict")
        raised.append((entry["started"], read[1]))
        blocking |= {finding for finding, entries in read[1].items() if set(entries) & set(BLOCKING_SEVERITIES)}
    # After each recorded verdict in order, a structured object lists what stays open, so one it
    # omits is resolved; a prose entry keeps its finding open.
    still_open: set[str] = set()
    found: dict[str, list[str | None]] = {}
    for position, marker in markers:
        comment = comments[position]
        read = _recorded_findings(comment, runs)
        body = str(comment.get("body"))
        # A withheld verdict's security verdict is in its sealed reply.
        sealed = "" if REPLY_OPENER in body else _withheld_reply(body, runs) or ""
        if (marker["verdict"] == "BLOCKED" or read is None
                or comment.get("created_at") != comment.get("updated_at")
                or recorder._security_verdict_blocks(body) or recorder._security_verdict_blocks(sealed)):
            raise GrantRefused(BLOCKER, f"{marker['task']}: the ledger holds a BLOCKED, a security FAIL, "
                                        "or an edited, withheld or unreadable verdict")
        structured, found = read
        if structured:
            raised = [(started, {key: value for key, value in items.items() if started >= marker["started"] or key in found})
                      for started, items in raised]
        still_open = (set() if structured else still_open) | set(found)
        blocking |= {finding for finding, entries in found.items() if set(entries) & set(BLOCKING_SEVERITIES)}
    unresolved: dict[str, list[str | None]] = {}
    for _, items in raised:
        for key, entries in items.items():
            unresolved.setdefault(key, []).extend(entries)
    if blocking & (still_open | set(unresolved)):
        raise GrantRefused(BLOCKER, f"{sorted(blocking & (still_open | set(unresolved)))}: "
                                    "an earlier P0/P1 finding has no recorded resolution")
    # What stays open at the latest rejection: its own findings and every unresolved superseded one.
    open_now = {key: [*found.get(key, []), *unresolved.get(key, [])] for key in (*found, *unresolved)}
    if not found or any(severity != "P2" for entries in open_now.values() for severity in entries):
        raise GrantRefused(BLOCKER, "the latest rejection does not leave a nonempty set of findings, all P2")
    if sorted(open_now) != p2["finding_ids"]:
        raise GrantRefused(BINDING, f"the open findings are {sorted(open_now)}, not the sealed finding ids")
    # Rule 5: every earlier review run is terminal and its verdict published; pushing first earns no credit.
    published = {(marker["task"], marker["started"]) for _, marker in markers}
    if runs_refusal is not None:
        raise GrantRefused(EVIDENCE, runs_refusal.detail)
    forgiven = {(entry["task"], entry["started"]) for entry in superseded}
    for run in runs:
        # Only the run being recorded is exempt; another seat at the candidate head must be published first.
        if (run.task_id, run.record.get("run_nonce")) == recording_run or run.record.get("mode") == "workspace-write":
            continue
        status = run.record.get("status")
        if (status not in lineage.TERMINAL_TASK_STATUSES or run.reply is None
                or (status == "done" and (run.task_id, lineage._started(run.record)) not in published | forgiven)
                or (status != "done" and recognized_verdicts(run.reply))):
            raise GrantRefused(EVIDENCE, f"{run.task_id}: an unknown or unpublished review obstruction")
    if repo_root is None:
        raise GrantRefused(EVIDENCE, "no checkout to compute the fix delta")
    issues, others = _lineage_links(request["repository"], request["pr"])
    if others:
        # Earlier PRs' ledgers are not read here, so a lineage that spans PRs is never admitted.
        raise GrantRefused(EVIDENCE, f"the work lineage spans PRs {others}; escalate to the CTO")
    try:
        delta = _delta_sha256(repo_root, p2["rejected_head"], head)
    except RepairRefused as exc:
        raise GrantRefused(EVIDENCE, exc.detail) from None
    keys = lineage_keys(request["repository"], request["pr"], request["lineage_id"], issues)
    if delta != p2["delta_sha256"]:
        raise GrantRefused(BINDING, f"the delta {p2['rejected_head'][:12]}..{head[:12]} hashes to {delta}")
    round_ = {
        "schema": P2_RECEIPT_SCHEMA, "repository": normalize_repository(request["repository"]), "pr": request["pr"],
        "branch": request["lineage_id"], "lineage_keys": keys, "rejected_head": p2["rejected_head"],
        "candidate_head": head, "delta_sha256": delta, "finding_ids": p2["finding_ids"],
        "grant_task": grant.task_id, "request_sha256": grant.request_sha256,
    }
    for key in keys:
        held = _read_p2_receipt(_receipt_path(_p2_receipts(task_root), key))
        if held is not None and not _same_p2_round(held, round_):
            raise GrantRefused(SPENT, f"lineage {key} used its one p2 fix round at PR #{held.get('pr')} "
                                      f"head {held.get('candidate_head')}; escalate to the CTO")
    return {"cited_verdict_head": latest["sha"], "round_allowance": P2_ROUND_ALLOWANCE, "p2_fix_round": round_}


def record_p2_round(task_root: Path, round_: Mapping[str, Any]) -> None:
    """Spend the lineage's p2 round under every key, at dispatch and again before its verdict is posted."""
    from scripts.review.repair_round import _receipt_path, _write_json

    root = _p2_receipts(task_root)
    root.mkdir(parents=True, exist_ok=True)
    stamped = {**round_, "admitted_at": datetime.now(UTC).isoformat(timespec="seconds")}
    written: list[Path] = []
    for key in round_["lineage_keys"]:
        path = _receipt_path(root, key)
        try:
            _write_json(path, stamped, exclusive=True)
        except FileExistsError:
            held = _read_p2_receipt(path)
            if held is not None and _same_p2_round(held, round_):
                continue
            for done in written:
                done.unlink(missing_ok=True)
            raise GrantRefused(SPENT, f"lineage {key} took its p2 round concurrently; escalate to the CTO") from None
        written.append(path)


def p2_round_at(task_root: Path, *, repository: str, number: int, branch: str, head: str) -> dict[str, Any] | None:
    """This PR's p2 round receipt when ``head`` is its candidate, so every seat at that head must attest."""
    from scripts.review.repair_round import _receipt_path

    repo = repository.casefold()
    for key in (f"pr:{repo}#{number}", f"branch:{repo}:{branch}"):
        held = _read_p2_receipt(_receipt_path(_p2_receipts(task_root), key))
        if held is not None and held.get("pr") == number and held.get("candidate_head") == head:
            return held
    return None


def require_p2_verified(reply: str, round_: Mapping[str, Any]) -> None:
    """An APPROVE in the p2 round carries the reviewer's positive delta attestation, bound to the sealed digest.

    Only a structured reply attests: its ``overall.explanation`` begins with exactly the declaration
    line, the reply mentions ``P2_FIX_DELTA`` nowhere else, and it lists no sealed finding. An
    example, a quotation or a negation is never at that position, and prose cannot attest.
    """
    read = _reply_findings(reply)
    structured = _structured_reply(reply) if read is not None and read[0] else None
    explanation = str(structured[0]["overall"].get("explanation", "")).strip() if structured else ""
    declared = (explanation.splitlines()[:1] == [f"P2_FIX_DELTA: {round_['delta_sha256']} VERIFIED"]
                and sum(text.count("P2_FIX_DELTA") for text in recorder._strings(structured[0])) == 1)
    if not declared or set(round_["finding_ids"]) & set(read[1]):
        raise GrantRefused(
            VERIFICATION,
            "an APPROVE in the p2 fix round is a structured reply whose overall.explanation begins with the line "
            f"`P2_FIX_DELTA: {round_['delta_sha256']} VERIFIED`, mentions P2_FIX_DELTA nowhere else, and lists "
            "none of the sealed findings",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="record_cf_verdict.py budget-grant",
        description="Inspect an elevated-tier review budget grant ruling.\n"
        "The recorder admits the granted rounds itself; this verb only prints the digest to bind.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/review/record_cf_verdict.py budget-grant digest ruling.json\n"
        "Outputs: the ruling's canonical SHA-256 on stdout, for --advisory-binding.\n"
        "Exit codes: 0: valid ruling; 1: invalid ruling.\nRelated: scripts/review/budget_grant.py",
    )
    verbs = parser.add_subparsers(dest="verb", required=True)
    digest = verbs.add_parser("digest", help="Validate a ruling file and print its canonical SHA-256")
    digest.add_argument("ruling", type=Path, help="Ruling JSON with exactly the request fields")
    args = parser.parse_args(argv)
    try:
        request = json.loads(args.ruling.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"budget grant ruling unreadable: {exc}")
        return 1
    try:
        parse_request(request, str(args.ruling))
    except GrantRefused as exc:
        print(str(exc))
        return 1
    print(canonical_sha256(request))
    return 0
