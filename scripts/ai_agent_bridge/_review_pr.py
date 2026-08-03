"""Canonical thin ``review-pr`` entrypoint (Sol fleet-comms Phase 0–3).

Pointer-only: no embedded diffs or inventory YAML. Prefer sealed Codex
``--review --pr`` isolation (#5285). Claude-dark local default for
opencode-family reviewers is GLM-5.2 (LOCAL-ONLY — never CI).

Formal CF model + effort pins (operator 2026-07-21): practical seats @ high
— Terra / Sonnet 5 / GLM, with pinned AGY as a quota substitution — not Sol/Fable on routine PRs. Authority seats
remain on the critical review ladder only (see model_catalog.yaml).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from ._review_safety import (
    MAX_REVIEW_REQUEST_BYTES,
    ReviewSafetyError,
    assert_content_size,
    prepend_read_only_contract,
)

_PR_REF_RE = re.compile(r"^(?:#|pr-)?(?P<num>\d+)$", re.IGNORECASE)

# Reviewer request ids (not harness marketing names).
REVIEWER_CODEX = "codex"
REVIEWER_GLM = "glm"
REVIEWER_CLAUDE = "claude"
REVIEWER_AGY = "agy"
REVIEWER_GROK = "grok"
REVIEWER_KIMI = "kimi"
REVIEWER_AUTO = "auto"

EXPLICIT_REVIEWER_CANDIDATE: dict[str, str] = {
    REVIEWER_CODEX: "gpt-5.6-terra",
    REVIEWER_CLAUDE: "claude-sonnet-5",
    REVIEWER_AGY: "gemini-3.6-flash",
    REVIEWER_GLM: "glm-5.2",
    REVIEWER_GROK: "grok-4.5",
    REVIEWER_KIMI: "kimi-k3",
    "kimicc": "kimi-k3",
}

# Practical formal CF pins — keep in sync with model_catalog formal_cf_defaults.
FORMAL_CF_MODEL: dict[str, str] = {
    REVIEWER_CODEX: "gpt-5.6-terra",
    REVIEWER_CLAUDE: "claude-sonnet-5",
    REVIEWER_AGY: "gemini-3.6-flash-high",
    REVIEWER_GLM: "glm-5.2",
    REVIEWER_GROK: "grok-4.5",
    REVIEWER_KIMI: "kimi-code/k3",
    "kimicc": "kimi-code/k3",
}
FORMAL_CF_EFFORT: dict[str, str] = {
    REVIEWER_CODEX: "high",
    REVIEWER_CLAUDE: "high",
    REVIEWER_AGY: "high",
    REVIEWER_GLM: "high",
    REVIEWER_GROK: "high",
    REVIEWER_KIMI: "high",
    "kimicc": "high",
}


def _formal_review_authority_key(
    repository: str,
    pr_number: int,
    head_sha: str,
    patch_sha256: str,
) -> str:
    """Return a bounded opaque key for one exact-head sealed review."""
    identity = json.dumps(
        {
            "repository": repository,
            "pr_number": pr_number,
            "head_sha": head_sha,
            "patch_sha256": patch_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "formal-review:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _canonical_review_response_text(response: str) -> str:
    """Extract one JSON object from the two bounded ACP wrapper shapes."""
    stripped = response.strip()
    match = re.fullmatch(r"```json\r?\n(?P<body>.+)\r?\n```", stripped, re.DOTALL)
    if match is not None and "```" not in match.group("body"):
        return match.group("body").strip()
    wrapped_match = re.fullmatch(
        r"(?P<prefix>.{1,500}?)\r?\n```json\r?\n(?P<body>.+)\r?\n```",
        stripped,
        re.DOTALL,
    )
    if wrapped_match is not None:
        prefix = wrapped_match.group("prefix")
        # Admit the common provider wrapper only when it is bounded prose,
        # followed by exactly one terminal JSON fence. Schema validation still
        # owns the verdict; this merely normalizes transport decoration.
        body = wrapped_match.group("body")
        if (
            "{" not in prefix
            and "}" not in prefix
            and "```" not in prefix
            and "```" not in body
        ):
            return body.strip()
    object_start = stripped.find("{")
    if object_start > 0 and "}" not in stripped[:object_start]:
        try:
            _value, object_end = json.JSONDecoder().raw_decode(stripped, object_start)
        except json.JSONDecodeError:
            return stripped
        if not stripped[object_end:].strip():
            return stripped[object_start:object_end]
    return stripped


def _finish_authority_job_once(
    authority: Any,
    job_id: str,
    *,
    worker_id: str,
    fence_token: int,
    state: str,
    result: bytes,
) -> bool:
    """Terminalize only while this worker still owns the fenced authority lease."""
    from scripts.fleet_comms.authority import AuthorityStaleLeaseError

    try:
        authority.finish_job(
            job_id,
            worker_id=worker_id,
            fence_token=fence_token,
            state=state,
            result=result,
        )
    except AuthorityStaleLeaseError:
        return False
    return True


def _settle_routing_reservation_once(
    routing_ledger: Any,
    reservation_id: str,
    **settlement: Any,
) -> bool:
    """Settle a durable reservation without leaking cleanup races as tracebacks."""
    from scripts.fleet_comms.routing_reservations import RoutingReservationError

    try:
        routing_ledger.settle(reservation_id, **settlement)
    except RoutingReservationError as exc:
        if str(exc) not in {"reservation_not_found", "terminal_settlement_conflict"}:
            raise
        return False
    return True


def _compute_review_routing_budget() -> dict[str, Any]:
    """Take a bounded fresh capacity snapshot for this standalone process."""
    from scripts.api.codexbar_usage import refresh_provider_usage_data
    from scripts.api.state_router import SUBSCRIPTION_LANES, compute_routing_budget

    # CodexBar's last-known-good cache is process-local. A new review-pr
    # process therefore cannot use cache-only mode without falsely marking
    # every subscription lane unavailable and draining the API-backed lanes.
    budget = compute_routing_budget(fresh_codexbar=True)
    agents = budget.get("agents") if isinstance(budget, dict) else None
    unavailable = tuple(
        lane
        for lane in SUBSCRIPTION_LANES
        if isinstance(agents, dict)
        and isinstance(agents.get(lane), dict)
        and agents[lane].get("status") in {"unknown", "unavailable"}
    )
    if unavailable:
        # CodexBar provider probes can serialize internally. Retry missing
        # lanes one at a time so they do not time out behind one another.
        for lane in unavailable:
            refresh_provider_usage_data((lane,), timeout_s=5.0)
        # The retry populated this process's last-known-good cache; do not
        # launch a second all-provider refresh while projecting it.
        budget = compute_routing_budget(fresh_codexbar=False)
    return budget


class _ReviewPrLifecycle:
    """Attach formal-run terminal evidence to its bridge ask without changing asks."""

    def __init__(self, *, background: bool):
        self.background = background
        self.message_id: int | None = None
        self._terminal: Any = None

    def message_created(self, message_id: int) -> None:
        """Write launch evidence before the adapter enters its run/spawn path."""
        from ._ask_lifecycle import _AskTerminalRecorder, _write_ask_launch_record

        self.message_id = message_id
        _write_ask_launch_record(message_id, pid=os.getpid(), target="review-pr")
        self._terminal = _AskTerminalRecorder(message_id)

    def record_terminal(self) -> None:
        """Write the synchronous formal review's terminal state from its ask status."""
        if self.background or self.message_id is None or self._terminal is None:
            return
        from ._ask_lifecycle import _ask_status

        status = _ask_status(self.message_id)
        if status and status.startswith("replied:"):
            self._terminal.write(0, "success")
        elif status and (status.startswith("timed-out:") or "timeout" in status.lower()):
            self._terminal.write(1, "timeout", cause=status)
        else:
            self._terminal.write(1, "failed", cause=status or "review-pr ended without a reply")

    def record_spawn_failure(self, exc: BaseException) -> None:
        """Leave the dispatch failure reason durable after an ask id exists."""
        if self.message_id is None or self._terminal is None:
            return
        from ._ask_lifecycle import record_ask_failure

        cause = f"{type(exc).__name__}: {exc}"
        record_ask_failure(self.message_id, cause)
        self._terminal.write(1, "spawn-failure" if self.background else "exception", cause=cause)

_DEFAULT_CHECKLIST = """\
## Formal cross-family PR review (pointer-only)

**PR:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/{pr}
**Reviewer seat:** {reviewer_model} @ effort={reviewer_effort} (transport={reviewer})
**Expected:** pull the PR evidence yourself (sealed snapshot / gh). Do not request
the operator to paste the diff.

### Required output
Emit exactly one canonical `code-review-findings.v1` JSON object — no markdown
or trailing `VERDICT:` line. It must contain `overall`
(`correctness`, `explanation`, `confidence`) and every finding with its
canonical location and evidence fields. Publication derives the GitHub gate
verdict from this evidence and preserves the review body in the PR comment.
Use `"correct"`, `"incorrect"`, or `"uncertain"` for `overall.correctness`.
Every `confidence` value MUST be a JSON number from 0.0 through 1.0 (for
example, `0.95`), never a string such as `"high"`. A clean review therefore
has exactly this shape (replace the explanation, not the field types):
`{{"schema_version":"code-review-findings.v1","overall":{{"correctness":"correct","explanation":"No actionable findings.","confidence":0.95}},"findings":[]}}`
Each finding object has exactly these fields: `id`, `title`, `body`, `priority`,
`confidence`, `category`, `location`, `verbatim`, `why_wrong`, `smallest_fix`,
and `sources`. Put claim type `"present"` or `"missing"` only inside the
`location` object alongside `path`, `start_line`, and `end_line`; never add
`claim_type` at the finding root. Do not invent enum aliases such as `"pass"`.
"""


def parse_pr_number(raw: str) -> int:
    text = raw.strip()
    match = _PR_REF_RE.match(text)
    if not match:
        raise ReviewSafetyError(f"invalid_pr_ref: {raw!r} (expected digits or #N)")
    return int(match.group("num"))


def build_review_pr_prompt(
    pr: int,
    *,
    reviewer: str,
    model: str,
    effort: str,
    extra: str | None = None,
) -> str:
    body = _DEFAULT_CHECKLIST.format(
        pr=pr,
        reviewer=reviewer,
        reviewer_model=model,
        reviewer_effort=effort,
    )
    if extra and extra.strip():
        body = f"{body}\n\n## Additional scope\n{extra.strip()}\n"
    body = prepend_read_only_contract(body)
    assert_content_size(body, limit=MAX_REVIEW_REQUEST_BYTES, label="review_pr_prompt")
    return body


def resolve_reviewer(selection: str, *, claude_available: bool | None = None) -> str:
    """Validate a semantic reviewer request; auto remains unresolved here."""
    choice = (selection or REVIEWER_AUTO).strip().lower()
    if choice == REVIEWER_AUTO:
        _ = claude_available  # compatibility-only hint; never routing authority
        return REVIEWER_AUTO
    if choice in EXPLICIT_REVIEWER_CANDIDATE:
        return choice
    raise ReviewSafetyError(
        f"unsupported_reviewer: {selection!r} "
        f"(choose auto|codex|glm|claude|agy|grok|kimi)"
    )


def formal_cf_pin(reviewer: str) -> tuple[str, str]:
    """Return (model_id, effort) for a formal CF transport."""
    model = FORMAL_CF_MODEL[reviewer]
    effort = FORMAL_CF_EFFORT[reviewer]
    return model, effort


def _headroom_band(record: dict[str, Any]) -> str:
    status = str(record.get("status") or "unknown")
    remaining = record.get("remaining_pct")
    if status in {"hot", "near_cap", "unavailable", "unhealthy"}:
        return "near_cap" if status in {"hot", "near_cap"} else "unavailable"
    if isinstance(remaining, (int, float)) and not isinstance(remaining, bool):
        if remaining <= 10:
            return "near_cap"
        if remaining <= 25:
            return "constrained"
        return "healthy"
    return "unknown"


def _routing_trace(resolution: Any) -> dict[str, Any]:
    return {
        "decision_order": [
            "hard_eligibility",
            "task_fit_suitability",
            "quality_tier",
            "quota_cost_capacity_failure_pressure",
            "stable_exact_tie_break",
        ],
        "policy_version": resolution.policy_version,
        "substitution_note": resolution.substitution_note,
        "candidates": [
            {
                "name": item.name,
                "model": item.concrete_model,
                "family": item.family,
                "route": item.route,
                "status": item.status,
                "reason": item.reason,
                "suitability_rank": item.suitability_rank,
                "quality_tier": item.quality_tier,
                "health": item.health,
                "selection_score": list(item.selection_score) if item.selection_score is not None else None,
            }
            for item in resolution.trace
        ],
    }


def _semantic_request_matches(reservation: Any, request: Any) -> bool:
    return all(
        (
            reservation.author_model == request.author_model,
            reservation.author_family == request.author_family,
            reservation.requested_role == request.requested_role,
            reservation.requested_profile == request.requested_profile,
            reservation.requested_risk == request.requested_risk,
            reservation.route_mode == request.route_mode,
            reservation.requested_reviewer == request.requested_reviewer,
            reservation.estimated_input_bytes == request.estimated_input_bytes,
        )
    )


def _usage_int(result: Any, *keys: str) -> int | None:
    record = getattr(result, "usage_record", None)
    if not isinstance(record, dict):
        return None
    for key in keys:
        value = record.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None


def _failure_classification(result: Any | None, exc: BaseException | None = None) -> str:
    if result is not None:
        if bool(getattr(result, "rate_limited", False)):
            return "rate_limited"
        record = getattr(result, "usage_record", None)
        if isinstance(record, dict) and record.get("failure_code") in {
            "provider_unavailable",
            "rate_limited",
            "timeout",
            "transport_error",
            "acp_adapter_incompatible",
            "acp_adapter_missing",
            "acp_agent_disconnected",
            "acp_agent_startup",
            "acp_auth_required",
            "acp_permission_denied",
            "acp_permission_unavailable",
            "acp_review_evidence_invalid",
            "acp_review_evidence_too_large",
            "acp_session_create_timeout",
            "acp_turn_limit",
        }:
            return str(record["failure_code"])
        if bool(getattr(result, "stalled", False)):
            return "timeout"
    if exc is not None and "timeout" in type(exc).__name__.lower():
        return "timeout"
    return "transport_error"


def _evidence_metrics(evidence: str) -> dict[str, int]:
    """Extract the parent-computed, non-secret evidence byte receipt."""
    marker = "AUTHORITATIVE SEALED REVIEW EVIDENCE\n"
    end_marker = "\nEND AUTHORITATIVE SEALED REVIEW EVIDENCE"
    try:
        payload = evidence.split(marker, 1)[1].split(end_marker, 1)[0]
        dossier = json.loads(payload.rsplit("\n", 1)[-1])
        metrics = dossier.get("evidence_metrics", {})
    except (IndexError, json.JSONDecodeError, AttributeError):
        return {}
    if not isinstance(metrics, dict):
        return {}
    return {
        key: value
        for key, value in metrics.items()
        if isinstance(key, str)
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    }


def _transport_failure_receipt(
    *,
    classification: str,
    result: Any | None,
    exc: BaseException | None,
) -> dict[str, Any]:
    """Return bounded diagnostics without persisting provider response bodies."""
    usage = getattr(result, "usage_record", None)
    failure_code = usage.get("failure_code") if isinstance(usage, dict) else None
    diagnostic = getattr(result, "stderr_excerpt", None)
    if not diagnostic and exc is not None:
        diagnostic = f"{type(exc).__name__}: {exc}"
    return {
        "failure_classification": classification,
        "provider_failure_code": failure_code if isinstance(failure_code, str) else None,
        "diagnostic": str(diagnostic)[:500] if diagnostic else None,
        "transport": "acp",
    }


def _fallback_permitted(*, route_mode: str, allow_explicit_fallback: bool) -> bool:
    """Automatic retries may change bucket; explicit pins require opt-in."""
    return route_mode == "auto" or (route_mode == "explicit" and allow_explicit_fallback)


def _routing_attempt_seed(authority_job: Any) -> int:
    """Derive a monotonic retry namespace from durable authority attempts."""
    value = getattr(authority_job, "attempt_count", 0)
    return max(0, value) if isinstance(value, int) and not isinstance(value, bool) else 0


def handle_review_pr(args: argparse.Namespace) -> int:
    """CLI handler for ``review-pr``."""
    try:
        pr = parse_pr_number(str(args.pr))
        reviewer_request = resolve_reviewer(args.reviewer, claude_available=args.claude_available)
        initiator = str(
            getattr(args, "initiator", None)
            or getattr(args, "from_llm", None)
            or os.environ.get("SESSION_HANDOFF_AGENT")
            or ""
        ).strip()
        author_model = str(getattr(args, "author_model", None) or "").strip()
        author_family = str(getattr(args, "author_family", None) or "").strip()
        if not initiator:
            raise ReviewSafetyError("initiator_required: pass --initiator")
        if not author_model or not author_family:
            raise ReviewSafetyError("concrete_author_identity_required: pass --author-model and --author-family")
    except ReviewSafetyError as exc:
        print(f"review-pr: {exc}", file=sys.stderr)
        return 2

    task_id = args.task_id or f"review-pr-{pr}"
    if args.dry_run:
        dry_model = getattr(args, "model", None) or (
            "deterministic-scheduler" if reviewer_request == REVIEWER_AUTO else FORMAL_CF_MODEL[reviewer_request]
        )
        print(
            f"review-pr dry-run pr={pr} reviewer_request={reviewer_request} "
            f"model={dry_model} task_id={task_id} initiator={initiator} "
            f"author={author_model}/{author_family}"
        )
        return 0
    if args.background:
        print(
            "review-pr: background bridge workers are retired; enqueue the formal job "
            "through fleet-comms or run this sealed ACP review synchronously",
            file=sys.stderr,
        )
        return 2

    from agent_runtime.runner import invoke_inter_agent

    from scripts.agent_runtime.adapters.acpx import ACPX_PARTICIPANT_EFFORTS
    from scripts.fleet_comms.authority import AuthorityService, AuthorityStaleLeaseError
    from scripts.fleet_comms.review_publication import (
        SealedVerdict,
        parse_review_evidence,
        verdict_from_review_evidence,
    )
    from scripts.fleet_comms.routing_reservations import (
        RoutingReservationLedger,
        RoutingReservationRequest,
        RoutingReservationUnavailable,
        RoutingSelection,
    )
    from scripts.orchestration.task_identity import DEFAULT_REPOSITORY
    from scripts.review.reviewer_resolver import (
        REVIEW_CANDIDATES,
        ResolverInputs,
        resolve_author_family,
    )
    from scripts.review.reviewer_resolver import resolve_reviewer as resolve_canonical_reviewer

    from ._config import REPO_ROOT
    from ._review_worktree import (
        ReviewTarget,
        ReviewWorktreeError,
        provision_review_worktree,
        validate_code_review_response,
        verify_clean_review_evidence_reads,
    )

    resolved_author_family = resolve_author_family(author_model, author_family)
    if resolved_author_family != author_family:
        print(
            "review-pr: author model/family are unknown, ambiguous, or conflicting; refusing formal review",
            file=sys.stderr,
        )
        return 2
    requested_candidate = None
    if reviewer_request != REVIEWER_AUTO:
        requested_candidate = EXPLICIT_REVIEWER_CANDIDATE[reviewer_request]
    explicit_model = str(getattr(args, "model", None) or "").strip() or None
    if explicit_model:
        matches = [candidate.name for candidate in REVIEW_CANDIDATES.values() if candidate.concrete_model == explicit_model]
        if requested_candidate is not None:
            valid_model_pin = REVIEW_CANDIDATES[requested_candidate].concrete_model == explicit_model
        else:
            valid_model_pin = len(matches) == 1
            if valid_model_pin:
                requested_candidate = matches[0]
        if not valid_model_pin:
            print("review-pr: --model must identify exactly the explicitly requested canonical candidate", file=sys.stderr)
            return 2
    route_mode = "explicit" if requested_candidate is not None else "auto"
    override_reason = str(getattr(args, "override_reason", None) or "").strip() or None
    if requested_candidate is not None and override_reason is None:
        print("review-pr: explicit reviewer/model pin requires --override-reason", file=sys.stderr)
        return 2
    profile = str(getattr(args, "review_profile", None) or "code").strip().lower()
    risk = str(getattr(args, "risk", None) or "medium").strip().lower()
    requested_role = str(getattr(args, "role", None) or "").strip() or None
    ledger_role = requested_role or f"{profile}:{risk}"
    required_capabilities = frozenset(
        getattr(args, "required_capability", None) or ("code_review", "sealed_evidence")
    )
    allow_explicit_fallback = bool(getattr(args, "allow_explicit_fallback", False))
    target = ReviewTarget(pr_number=pr)
    with provision_review_worktree(
        target,
        repo_root=REPO_ROOT,
        acceptance_mode="acp-inline",
    ) as checkout:
        if checkout is None:  # pragma: no cover - target above is mandatory
            raise RuntimeError("sealed review snapshot was not provisioned")
        evidence = checkout.review_prompt_evidence("acp")
        evidence_metrics = _evidence_metrics(evidence)
        sealed_mcp_config = checkout.sealed_acp_tool_config()
        estimated_input_bytes = checkout.sealed_evidence_input_bytes()
        timeout = 86400 if args.no_timeout else 1800
        worker_id = f"review-pr-acp:{os.getpid()}"
        authority_key = _formal_review_authority_key(
            DEFAULT_REPOSITORY,
            pr,
            checkout.sha,
            checkout.patch_digest,
        )
        routing_request = RoutingReservationRequest(
            authority_key=authority_key,
            idempotency_key=f"{authority_key}:routing:0",
            initiator=initiator,
            author_model=author_model,
            author_family=author_family,
            requested_role=ledger_role,
            requested_profile=profile,
            requested_risk=risk,
            route_mode=route_mode,
            estimated_input_bytes=estimated_input_bytes,
            requested_reviewer=requested_candidate,
        )
        with RoutingReservationLedger() as routing_ledger, AuthorityService() as authority:
            authority_job = authority.enqueue_formal_review(
                repository=DEFAULT_REPOSITORY,
                pr_number=pr,
                head_sha=checkout.sha,
                gate_kind="cross-family-review",
                snapshot=evidence.encode("utf-8"),
                idempotency_key=authority_key,
            )
            formal_job = authority.require_publishable_formal_review(
                authority_job.subject_id,
                current_head_sha=checkout.sha,
            )
            routing_reservation = None
            result = None
            coverage_receipt = None
            replayed = authority_job.state == "complete"
            if authority_job.state == "complete":
                routing_reservation = routing_ledger.completed_replay(authority_key)
                if routing_reservation is None or not _semantic_request_matches(routing_reservation, routing_request):
                    print("review-pr: completed exact-head result lacks a matching routing authority receipt", file=sys.stderr)
                    return 1
                replay = authority.read_job_result(authority_job.job_id)
                if replay is None:
                    print("review-pr: completed ACP attempt has no durable result", file=sys.stderr)
                    return 1
                raw_response = replay.decode("utf-8")
            else:
                try:
                    routing_budget = _compute_review_routing_budget()
                except Exception as exc:
                    routing_budget = {
                        "agents": {},
                        "in_flight": {},
                        "diagnostics": {"stale": True, "routing_budget_error": type(exc).__name__},
                    }
                if authority_job.state in {"failed", "expired"}:
                    authority_job = authority.retry_job(authority_job.job_id)
                elif authority_job.state == "dead_lettered":
                    authority_job = authority.redrive_job(authority_job.job_id)
                failed_quota_buckets: set[str] = set()
                fallback_from: str | None = None
                # A later CLI invocation must not reuse a terminal routing
                # idempotency key from an earlier authority attempt. The
                # authority attempt counter is durable and monotonic; gaps are
                # harmless, while reuse could launch work without a fresh
                # reservation after a repaired transport is retried.
                reservation_attempt = _routing_attempt_seed(authority_job)
                fallback_attempt = 0
                while True:
                    selection_diagnostic: dict[str, Any] = {}

                    def select_inside_authority(
                        context: Any,
                        *,
                        attempt_index: int = reservation_attempt,
                        fallback_index: int = fallback_attempt,
                        prior_candidate: str | None = fallback_from,
                        diagnostic: dict[str, Any] = selection_diagnostic,
                    ) -> RoutingSelection | None:
                        snapshot = json.loads(json.dumps(routing_budget))
                        agents = snapshot.setdefault("agents", {})
                        for candidate in REVIEW_CANDIDATES.values():
                            record = agents.setdefault(candidate.route, {})
                            if not isinstance(record, dict):
                                record = {}
                                agents[candidate.route] = record
                            usage = context.bucket_usage(candidate.quota_bucket, rolling_window_seconds=7 * 24 * 3600)
                            circuit = context.bucket_circuit_state(candidate.quota_bucket, candidate.credential_bucket)
                            codexbar = record.get("codexbar") if isinstance(record.get("codexbar"), dict) else {}
                            scheduler = record.setdefault("scheduler", {})
                            scheduler.update(
                                {
                                    "completed_input_bytes": usage.completed_window_bytes,
                                    "active_reserved_input_bytes": usage.reserved_input_bytes,
                                    "inflight": context.active_reservations(candidate.credential_bucket),
                                    "failures": usage.recent_failures,
                                    "circuit_open": bool(circuit and circuit.open_until and circuit.open_until > context.now),
                                    "capacity_exhausted": (
                                        context.available_slots(
                                            candidate.credential_bucket,
                                            candidate.credential_limit,
                                        ) == 0
                                        or context.quota_available_slots(
                                            candidate.quota_bucket,
                                            candidate.quota_limit,
                                        ) == 0
                                    ),
                                    "quota_remaining_pct": record.get("remaining_pct"),
                                    "quota_stale": codexbar.get("freshness") != "fresh",
                                }
                            )
                        pin = requested_candidate if fallback_index == 0 else None
                        resolution = resolve_canonical_reviewer(
                            ResolverInputs(
                                author_model=author_model,
                                author_family=author_family,
                                review_profile=profile,
                                risk=risk,
                                domain=profile,
                                requested_role=requested_role,
                                required_capabilities=required_capabilities,
                                data_egress_policy=getattr(args, "data_egress_policy", None),
                                isolation_required=bool(getattr(args, "isolation_required", True)),
                                exact_head=authority_key,
                                pinned_candidate=pin,
                                pressure_override_reason=override_reason if pin else None,
                            ),
                            runtime_state=snapshot,
                            excluded_quota_buckets=frozenset(failed_quota_buckets),
                        )
                        diagnostic.update(
                            {
                                "fail_closed_reason": resolution.fail_closed_reason,
                                "trace": _routing_trace(resolution),
                            }
                        )
                        selected = resolution.selected
                        if selected is None:
                            return None
                        record = agents.get(selected.route, {})
                        codexbar = record.get("codexbar") if isinstance(record, dict) and isinstance(record.get("codexbar"), dict) else {}
                        fresh_at = codexbar.get("fetched_at") if isinstance(codexbar.get("fetched_at"), str) else None
                        source = "codexbar_fresh" if codexbar.get("freshness") == "fresh" else (
                            "codexbar_last_known_good" if codexbar.get("freshness") == "stale_last_good" else "unavailable"
                        )
                        return RoutingSelection(
                            candidate=selected.name,
                            route=selected.route,
                            model=selected.concrete_model,
                            family=selected.family,
                            quota_bucket=selected.quota_bucket,
                            credential_bucket=selected.credential_bucket,
                            quota_limit=selected.quota_limit,
                            credential_limit=selected.credential_limit,
                            policy_version=resolution.policy_version,
                            quota_snapshot=record if isinstance(record, dict) else {},
                            quota_fresh_at=fresh_at,
                            trace=_routing_trace(resolution),
                            fallback_from=prior_candidate,
                            retry_attempt=attempt_index,
                            quota_source=source,
                            quota_headroom_band=_headroom_band(record if isinstance(record, dict) else {}),
                        )

                    attempt_request = replace(
                        routing_request,
                        idempotency_key=f"{authority_key}:routing:{reservation_attempt}",
                    )
                    try:
                        lease = authority.claim_job(
                            authority_job.job_id,
                            worker_id,
                            lease_seconds=timeout + 30,
                        )
                    except AuthorityStaleLeaseError as exc:
                        if str(exc) != "job_already_claimed":
                            raise
                        print(
                            "review-pr: exact-head formal job is already active; "
                            "no provider call or routing reservation was created",
                            file=sys.stderr,
                        )
                        return 1
                    try:
                        routing_reservation = routing_ledger.reserve_selection(
                            attempt_request,
                            select_inside_authority,
                            ttl_seconds=timeout + 30,
                        )
                    except RoutingReservationUnavailable as exc:
                        _finish_authority_job_once(
                            authority,
                            authority_job.job_id,
                            worker_id=worker_id,
                            fence_token=lease.fence_token,
                            state="failed",
                            result=json.dumps(
                                {
                                    "failure_classification": "no_admissible_route",
                                    "detail": str(exc),
                                    "selection": selection_diagnostic,
                                },
                                sort_keys=True,
                            ).encode("utf-8"),
                        )
                        reason = selection_diagnostic.get("fail_closed_reason") or str(exc)
                        print(f"review-pr: no admissible formal reviewer: {reason}", file=sys.stderr)
                        return 1
                    participant = REVIEW_CANDIDATES[routing_reservation.resolved_candidate].participant
                    model = routing_reservation.resolved_model
                    effort = ACPX_PARTICIPANT_EFFORTS.get(participant)
                    requested_effort = str(getattr(args, "effort", None) or "").strip() or None
                    if requested_effort is not None and requested_effort != effort:
                        _settle_routing_reservation_once(
                            routing_ledger,
                            routing_reservation.reservation_id,
                            status="cancelled",
                            terminal_evidence={"reason": "invalid_effort_pin"},
                        )
                        _finish_authority_job_once(
                            authority,
                            authority_job.job_id,
                            worker_id=worker_id,
                            fence_token=lease.fence_token,
                            state="failed",
                            result=b'{"failure_classification":"invalid_effort_pin"}',
                        )
                        print(
                            f"review-pr: participant {participant} supports effort pin {effort!r}, "
                            f"not {requested_effort!r}",
                            file=sys.stderr,
                        )
                        return 2
                    prompt = build_review_pr_prompt(
                        pr,
                        reviewer=routing_reservation.resolved_route,
                        model=model,
                        effort=effort or "provider_default",
                        extra=args.extra,
                    )
                    sealed_prompt = prompt + evidence
                    routing_ledger.mark_started(routing_reservation.reservation_id)
                    previous_transport = os.environ.get("LU_ACPX_TRANSPORT")
                    os.environ["LU_ACPX_TRANSPORT"] = "active"
                    invocation_error: BaseException | None = None
                    try:
                        result = invoke_inter_agent(
                            participant,
                            sealed_prompt,
                            cwd=checkout.path,
                            task_id=task_id,
                            correlation_id=formal_job.review_id,
                            idempotency_key=authority_key,
                            source=initiator,
                            model=model,
                            effort=effort,
                            sealed_review_mcp_config=sealed_mcp_config,
                            hard_timeout=timeout,
                        )
                    except BaseException as exc:
                        invocation_error = exc
                    finally:
                        if previous_transport is None:
                            os.environ.pop("LU_ACPX_TRANSPORT", None)
                        else:
                            os.environ["LU_ACPX_TRANSPORT"] = previous_transport
                    raw_response = str(getattr(result, "response", "")) if result is not None else ""
                    if invocation_error is None and result is not None and getattr(result, "ok", False):
                        break
                    classification = _failure_classification(result, invocation_error)
                    failure_receipt = _transport_failure_receipt(
                        classification=classification,
                        result=result,
                        exc=invocation_error,
                    )
                    routing_settled = _settle_routing_reservation_once(
                        routing_ledger,
                        routing_reservation.reservation_id,
                        status="failed",
                        actual_input_bytes=estimated_input_bytes,
                        actual_output_bytes=len(raw_response.encode("utf-8")),
                        actual_input_tokens=_usage_int(result, "input_tokens") if result is not None else None,
                        actual_output_tokens=_usage_int(result, "output_tokens", "tokens") if result is not None else None,
                        failure_classification=classification,
                        circuit_open_seconds=300,
                    )
                    authority_finished = _finish_authority_job_once(
                        authority,
                        authority_job.job_id,
                        worker_id=worker_id,
                        fence_token=lease.fence_token,
                        state="failed",
                        result=json.dumps(failure_receipt, sort_keys=True).encode("utf-8"),
                    )
                    if not routing_settled or not authority_finished:
                        print(
                            "review-pr: durable routing or authority state changed while the reviewer was running; "
                            "the provider result was not accepted",
                            file=sys.stderr,
                        )
                        return 1
                    can_fallback = _fallback_permitted(
                        route_mode=route_mode,
                        allow_explicit_fallback=allow_explicit_fallback,
                    )
                    if not can_fallback or fallback_attempt >= len(REVIEW_CANDIDATES) - 1:
                        if invocation_error is not None:
                            print(f"review-pr: ACP reviewer failed: {type(invocation_error).__name__}", file=sys.stderr)
                        else:
                            print("review-pr: ACP reviewer failed", file=sys.stderr)
                        return 1
                    failed_quota_buckets.add(routing_reservation.quota_bucket)
                    fallback_from = routing_reservation.resolved_candidate
                    reservation_attempt += 1
                    fallback_attempt += 1
                    authority_job = authority.retry_job(authority_job.job_id)

            if not raw_response:
                if not replayed:
                    if routing_reservation is not None:
                        _settle_routing_reservation_once(
                            routing_ledger,
                            routing_reservation.reservation_id,
                            status="failed",
                            actual_input_bytes=estimated_input_bytes,
                            actual_output_bytes=0,
                            failure_classification="result_invalid",
                        )
                    _finish_authority_job_once(
                        authority,
                        authority_job.job_id,
                        worker_id=worker_id,
                        fence_token=lease.fence_token,
                        state="failed",
                        result=b"",
                    )
                print("review-pr: ACP reviewer failed without bridge retry", file=sys.stderr)
                return 1
            canonical_response = _canonical_review_response_text(raw_response)
            try:
                validate_code_review_response(
                    canonical_response,
                    base_sha=checkout.base_sha,
                    head_sha=checkout.sha,
                    patch_sha256=checkout.patch_digest,
                    changed_paths=checkout.changed_paths,
                    evidence_root=checkout.path,
                    changed_lines=checkout.changed_line_numbers,
                )
                if not replayed:
                    coverage_receipt = verify_clean_review_evidence_reads(
                        result,
                        engine="acp",
                        evidence_root=checkout.path,
                        changed_paths=checkout.changed_paths,
                    )
            except ReviewWorktreeError as exc:
                if not replayed:
                    if routing_reservation is not None:
                        _settle_routing_reservation_once(
                            routing_ledger,
                            routing_reservation.reservation_id,
                            status="failed",
                            actual_input_bytes=estimated_input_bytes,
                            actual_output_bytes=len(raw_response.encode("utf-8")),
                            actual_input_tokens=_usage_int(result, "input_tokens") if result is not None else None,
                            actual_output_tokens=_usage_int(result, "output_tokens", "tokens") if result is not None else None,
                            failure_classification="result_invalid",
                        )
                    authority_finished = _finish_authority_job_once(
                        authority,
                        authority_job.job_id,
                        worker_id=worker_id,
                        fence_token=lease.fence_token,
                        state="failed",
                        result=raw_response.encode("utf-8"),
                    )
                    if not authority_finished:
                        print(
                            "review-pr: authority lease was lost while validating the reviewer result; "
                            "the routing reservation was released",
                            file=sys.stderr,
                        )
                print(f"review-pr: reviewer result invalid: {exc}", file=sys.stderr)
                return 1
            if not replayed:
                routing_settled = _settle_routing_reservation_once(
                    routing_ledger,
                    routing_reservation.reservation_id,
                    status="complete",
                    actual_input_bytes=(
                        coverage_receipt.get("total_delivered_bytes", estimated_input_bytes)
                        if isinstance(coverage_receipt, dict)
                        else estimated_input_bytes
                    ),
                    actual_output_bytes=len(canonical_response.encode("utf-8")),
                    actual_input_tokens=_usage_int(result, "input_tokens"),
                    actual_output_tokens=_usage_int(result, "output_tokens", "tokens"),
                    terminal_evidence={
                        "coverage_receipt": coverage_receipt or {},
                        "unique_evidence_bytes": estimated_input_bytes,
                        "serialized_prompt_bytes": len(evidence.encode("utf-8")),
                        "evidence_metrics": evidence_metrics,
                    },
                )
                if not routing_settled:
                    print(
                        "review-pr: routing reservation disappeared before verdict acceptance; "
                        "the provider result was not published",
                        file=sys.stderr,
                    )
                    return 1
                authority_finished = _finish_authority_job_once(
                    authority,
                    authority_job.job_id,
                    worker_id=worker_id,
                    fence_token=lease.fence_token,
                    state="complete",
                    result=canonical_response.encode("utf-8"),
                )
                if not authority_finished:
                    print(
                        "review-pr: authority lease was lost before verdict acceptance; "
                        "the completed routing usage receipt was retained but the verdict was not published",
                        file=sys.stderr,
                    )
                    return 1
            canonical = json.loads(canonical_response)
            review_evidence = parse_review_evidence(canonical)
            verdict = (
                "BLOCKED"
                if review_evidence is None
                else verdict_from_review_evidence(review_evidence)
            )
            sealed = SealedVerdict(
                review_id=formal_job.review_id,
                repository=DEFAULT_REPOSITORY,
                pr_number=pr,
                head_sha=checkout.sha,
                gate_kind="cross-family-review",
                verdict=verdict,
                model=routing_reservation.resolved_model,
                family=routing_reservation.resolved_family,
                harness="acp",
                review_evidence=review_evidence,
            )
            authority.accept_formal_review_verdict(formal_job.review_id, sealed)
            print(
                json.dumps(
                    {
                        "review_id": formal_job.review_id,
                        "pr": pr,
                        "head_sha": checkout.sha,
                        "snapshot_artifact_id": formal_job.snapshot_artifact_id,
                        "authority_job_id": authority_job.job_id,
                        "verdict": verdict,
                        "reviewer_request": reviewer_request,
                        "resolved_candidate": routing_reservation.resolved_candidate,
                        "model": routing_reservation.resolved_model,
                        "family": routing_reservation.resolved_family,
                        "quota_bucket": routing_reservation.quota_bucket,
                        "credential_bucket": routing_reservation.credential_bucket,
                        "routing_reservation_id": routing_reservation.reservation_id,
                        "exact_head_replay": replayed,
                        "coverage_receipt": coverage_receipt,
                        "evidence_metrics": evidence_metrics,
                        "reported_input_tokens": _usage_int(result, "input_tokens"),
                        "reported_output_tokens": _usage_int(result, "output_tokens", "tokens"),
                        "serialized_prompt_bytes": len(evidence.encode("utf-8")),
                        "transport": "acp",
                    },
                    sort_keys=True,
                )
            )
            return 0 if verdict == "APPROVED" else 1


def register_review_pr_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "review-pr",
        help="Pointer-only formal PR review (sealed isolation preferred)",
        description=(
            "Canonical formal code-review entrypoint. The orchestrator supplies "
            "semantic requirements; one deterministic suitability-first scheduler "
            "atomically chooses and reserves the sealed ACP route. No LLM performs routing."
        ),
    )
    parser.add_argument("pr", help="PR number (e.g. 5443 or #5443)")
    parser.add_argument(
        "--reviewer",
        default=REVIEWER_AUTO,
        help="auto|codex|glm|claude|agy|grok|kimi (explicit routes are exceptional pins)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Exceptional exact canonical model pin; must agree with --reviewer and "
            "requires --override-reason"
        ),
    )
    parser.add_argument(
        "--effort",
        default=None,
        help=(
            "Override formal CF effort pin (default: high; authority escalate: xhigh)"
        ),
    )
    parser.add_argument("--claude-available", dest="claude_available", action=argparse.BooleanOptionalAction,
                        default=None, help="Deprecated compatibility hint; never routing authority")
    parser.add_argument("--task-id", help="Bridge task id (default: review-pr-<N>)")
    parser.add_argument("--extra", help="Optional extra scope text (kept under size cap)")
    parser.add_argument("--initiator", "--from", dest="initiator", required=True,
                        help="Concrete orchestrator identity persisted in routing authority")
    parser.add_argument("--author-model", required=True, help="Concrete author model/seat identity")
    parser.add_argument("--author-family", required=True, help="Concrete author model family")
    parser.add_argument("--review-profile", choices=("code", "infra"), default="code")
    parser.add_argument("--role", help="Optional exact canonical model role required for this review")
    parser.add_argument("--risk", choices=("critical", "high", "medium", "low"), default="medium")
    parser.add_argument("--required-capability", action="append",
                        help="Repeatable hard capability gate (default: code_review + sealed_evidence)")
    parser.add_argument("--data-egress-policy",
                        help="Explicit data-egress policy token; gated routes fail closed when absent")
    parser.add_argument("--isolation-required", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--override-reason",
                        help="Required evidence for every exceptional explicit reviewer/model pin")
    parser.add_argument("--allow-explicit-fallback", action="store_true",
                        help="Permit an explicit pin to fail over after a retryable transport failure")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--no-timeout", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    # Post-reply finalize is a separate CLI so review-pr stays pointer-only:
    #   .venv/bin/python -m scripts.fleet_comms formal-job accept \
    #       --pr N --verdict APPROVED --model M --family F --harness H [--publish]
