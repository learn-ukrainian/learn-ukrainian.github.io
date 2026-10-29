"""A sealed elevated-tier review budget grant: rounds 4 and 5 for one PR's open qualifying blocker.

The review policy (review-loop ``references/policy.md`` § Budget) allows up to
five rounds for a change to security, permissions, authentication, data loss,
or state and concurrency while an evidenced blocker on it stays open. The
recorder raises a PR to five rounds by its changed paths alone
(``record_cf_verdict.review_round_budget``); this module adds the designated
grant for every other change. Approved design: CTO proposal, Sol 6.1 APPROVE
WITH CHANGES (advisory task cto-7923-adv-clog-sol, item 3b).

1. Ruling. The CTO's typed request with exactly the fields ``repository``,
   ``pr``, ``lineage_id`` (the PR's head branch, the lineage its review runs
   follow), ``scope_paths`` (the sorted changed paths the grant covers),
   ``finding_id`` (the open blocker, ``F<n>``), ``blocker_class`` (one of
   ``BLOCKER_CLASSES``), ``issuer`` (the stable CTO identity), ``issuer_model``
   and ``issued_at``. Its digest is its canonical SHA-256
   (``bounded_advisory.canonical_sha256``); print it with
   ``record_cf_verdict.py budget-grant digest <file>``.
2. Approval. A read-only dispatch on the designated advisor outside the issuer
   model's family (operator-expectations item 12) with ``--advisory-role
   review_budget_elevation --advisory-binding <digest> --initiator <issuer>``.
   Its result holds exactly one fenced ``budget-elevation`` JSON object: every
   request field, ``decision`` and ``request_sha256``, sealed at finish
   (``bounded_advisory.load_sealed_result``).
3. Admission. The recorder admits round 4 or 5 of a PR whose changed paths
   give it three only when a finished, sealed APPROVE passes every check
   above, its dispatcher-recorded ``initiator`` is its issuer, it names this
   repository, PR and head branch, its scope covers every changed path, and
   the latest recorded verdict on the PR is a rejection whose reply lists the
   grant's finding at P0 or P1 and not as resolved.

Limits. A grant raises the budget to five rounds in total and never resets the
rounds already counted; a sixth round refuses whatever grants exist. It cannot
move to another repository, PR, branch or wider scope, and each round past the
third needs the cited blocker still open in the verdict before it. Cooperative
threat model, as in ``bounded_advisory``: the initiator and every record are
recorded, not authenticated, so a process that rewrites task records or
dispatches under another identity is outside it.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
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
from scripts.orchestration.integration_sweep import REJECTED
from scripts.orchestration.task_record_store import ARCHIVE_DIR_NAME
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import REVIEW_BUDGET_ELEVATION_ROLE, advisory_role_policy, canonical_model_id
from scripts.review.reviewer_resolver import UNRESOLVED_AUTHOR_FAMILIES, resolve_family

# The CTO seat's stable Fleet Comms identity; session-specific slots are not issuers.
ISSUERS = frozenset({"claude-cto"})
# The change classes review-loop references/policy.md § Budget elevates.
BLOCKER_CLASSES = frozenset({"security", "permissions", "authentication", "data-loss", "state-concurrency"})
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


class GrantRefused(recorder.RecordError):
    """An elevated-tier grant condition failed; ``reason`` names which one."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"BUDGET_GRANT_REFUSED[{reason}]: {detail}")
        self.reason = reason
        self.detail = detail


def parse_request(request: Any, label: str) -> dict[str, Any]:
    """The typed ruling in ``request``, or a refusal naming ``label``."""
    if not isinstance(request, dict) or set(request) != REQUEST_FIELDS:
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
    if request["blocker_class"] not in BLOCKER_CLASSES:
        raise GrantRefused(REQUEST, f"{label} blocker_class must be one of {sorted(BLOCKER_CLASSES)}")
    try:
        stamp = datetime.fromisoformat(str(request["issued_at"]).replace("Z", "+00:00"))
    except ValueError:
        stamp = None
    if not isinstance(request["issued_at"], str) or stamp is None or stamp.tzinfo is None:
        raise GrantRefused(REQUEST, f"{label} issued_at must be an ISO-8601 time with a timezone")
    return request


@dataclass(frozen=True)
class Grant:
    task_id: str
    request: dict[str, Any]
    request_sha256: str
    advisor_model: str
    result_sha256: str


def _grant_records(task_root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Every hot or archived finished task record that ran the elevation role."""
    found = []
    try:
        paths = [*sorted((task_root / ARCHIVE_DIR_NAME).glob("*.json")), *sorted(task_root.glob("*.json"))]
    except OSError as exc:
        raise GrantRefused(APPROVAL, f"task ledger unavailable: {exc}") from None
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
            if REVIEW_BUDGET_ELEVATION_ROLE not in text:
                continue
            record = json.loads(text)
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
        if set(decision) != set(policy.output_fields):
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
    request = parse_request({field: decision[field] for field in REQUEST_FIELDS}, f"advisory task {task_id!r} ruling")
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
    return Grant(task_id, request, digest, advisor, sealed.result_sha256)


def _claimed_pr(path: Path) -> Any:
    """The PR a refused grant's result names, read without any check: it only decides who hears the refusal."""
    try:
        policy = advisory_role_policy(REVIEW_BUDGET_ELEVATION_ROLE)
        return fenced_object(path.with_suffix(".result").read_text(encoding="utf-8"), policy.fence).get("pr")
    except (AdvisoryRefused, KeyError, OSError, UnicodeDecodeError, AttributeError):
        return None


def open_blocker_cited(comments: Sequence[Mapping[str, Any]], login: str, finding_id: str) -> str | None:
    """The head of the latest recorded verdict when it is a rejection listing ``finding_id`` as an open P0/P1."""
    markers = recorder._trusted_markers(comments, login)
    if not markers:
        return None
    index, marker = markers[-1]
    if marker["verdict"] not in REJECTED:
        return None
    body = comments[index].get("body")
    reply = body.partition("<details>")[2] if isinstance(body, str) else ""
    pattern = re.compile(rf"(?m)^\s*{re.escape(finding_id)} \[(P[0-3])\](.*)$")
    for severity, rest in pattern.findall(reply):
        if severity in BLOCKING_SEVERITIES and not re.search(r"\bresolved\b", rest, re.IGNORECASE):
            return marker["sha"]
    return None


def admit_grant_round(
    *,
    repository: str,
    number: int,
    branch: str,
    changed_paths: Sequence[str],
    comments: Sequence[Mapping[str, Any]],
    login: str,
    task_root: Path,
) -> dict[str, Any] | None:
    """The receipt of a grant admitting this round; None when the PR has no grant, or a refusal."""
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
    if not grants:
        if refusals:
            raise GrantRefused(refusals[0].reason, "; ".join(exc.detail for exc in refusals))
        return None
    for grant in grants:
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
    for grant in grants:
        cited = open_blocker_cited(comments, login, grant.request["finding_id"])
        if cited is not None:
            return {
                "grant_task": grant.task_id,
                "request_sha256": grant.request_sha256,
                "advisor_model": grant.advisor_model,
                "approval_result_sha256": grant.result_sha256,
                "finding_id": grant.request["finding_id"],
                "blocker_class": grant.request["blocker_class"],
                "cited_verdict_head": cited,
            }
    findings = sorted({grant.request["finding_id"] for grant in grants})
    raise GrantRefused(
        BLOCKER, f"the latest recorded verdict lists none of the granted findings {findings} as an open P0/P1 blocker"
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
