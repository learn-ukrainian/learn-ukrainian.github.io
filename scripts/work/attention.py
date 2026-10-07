"""Deterministic health, attention rank, and safe-next-action derivation.

Activity volume, comment counts, story points, and model opinion are never
health evidence (frozen brief semantics). Merge advice is a read of the latest
persisted lifecycle receipt plus Work's own same-head observation. It never
calls the live closeout observer, a GitHub runner, the local-git observer,
``reconcile``, or ``write_lifecycle``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from scripts.github_check_rollup import collapse_status_rollup

HEALTH_RANK = {
    "OFF_TRACK": 0,
    "AT_RISK": 1,
    "UNKNOWN": 2,
    "ON_TRACK": 3,
}

# Actionable-view deny list (#6850): rows whose only next step is browsing
# GitHub, inspecting an unknown, or nothing are not pick-list work. The server
# stamps ``flags.attention`` from ``is_actionable``; the dashboard reads that
# flag and does not keep a copy of this set.
NON_ACTIONABLE_ACTION_CODES = frozenset({"INSPECT_UNKNOWN", "OPEN_GITHUB", "NONE"})

# Receipt ``observed_at`` older than this cannot support merge advice (#9741 A1).
LEDGER_RECEIPT_FRESHNESS_S = 900
# Age below this is a future receipt, not freshness. The value is a small
# negative clock-skew allowance (#9741). A timestamp further ahead stays
# unknown so it cannot remain fresh for the skew plus the 900s window.
LEDGER_RECEIPT_FUTURE_TOLERANCE_S = -30

_FAILING_CHECK_TOKENS = frozenset({"FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"})
_PENDING_CHECK_TOKENS = frozenset({"PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED"})
_PASSING_CHECK_TOKENS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
_TERMINAL_CHECK_STATES = _FAILING_CHECK_TOKENS | _PASSING_CHECK_TOKENS

# Unsuccessful terminals stay visible. ``done`` is termination, not delivery.
_OFF_TRACK_TERMINALS = frozenset({"failed", "timeout", "no_deliverable"})
_VISIBLE_TERMINALS = frozenset(
    {
        "failed",
        "timeout",
        "no_deliverable",
        "cancelled",
        "crashed",
        "rate_limited",
        "dry_run",
        "blocked",
    }
)
_ACTIVE_EXECUTION = frozenset({"running", "spawning"})


def is_actionable(item: dict[str, Any] | None) -> bool:
    """True when a projection row is real pick-list work (#6850 semantics).

    OFF_TRACK / AT_RISK always demand attention; otherwise the safe next
    action must be a doing verb outside the deny list.
    """
    if not item:
        return False
    if item.get("health") in {"OFF_TRACK", "AT_RISK"}:
        return True
    code = str(((item.get("safe_next_action") or {}).get("code")) or "")
    return bool(code) and code not in NON_ACTIONABLE_ACTION_CODES


def _action(code: str, reasons: list[str], state: str) -> dict[str, Any]:
    """One safe-next-action object. ``state`` qualifies the action, not admission."""
    return {"code": code, "reason_codes": reasons, "state": state}


def _rollup_token(entry: dict[str, Any]) -> str:
    """Check token from ``state`` or ``status``, then ``conclusion``.

    Check runs in production carry ``status`` (REST and ``gh``). Commit
    statuses carry ``state``. A status other than ``COMPLETED`` is pending,
    including an in-progress run with no conclusion. A completed run is its
    conclusion. A terminal state that disagrees with the conclusion is unknown.
    """
    state = str(entry.get("state") or "").strip().upper()
    status = str(entry.get("status") or "").strip().upper()
    conclusion = str(entry.get("conclusion") or "").strip().upper()
    if status and status != "COMPLETED":
        return "PENDING"
    if state in _TERMINAL_CHECK_STATES and conclusion and state != conclusion:
        return "UNKNOWN"
    if state == "COMPLETED" or status == "COMPLETED":
        return conclusion or "UNKNOWN"
    return state or status or conclusion


def _pr_check_state(pr: dict[str, Any] | None) -> str:
    """Return failing | pending | passing | unknown from GH list rollup only."""
    if not pr:
        return "unknown"
    rollup = pr.get("statusCheckRollup")
    if rollup is None:
        return "unknown"
    states: list[str] = []
    if isinstance(rollup, list):
        for entry in collapse_status_rollup(rollup):
            if isinstance(entry, dict):
                states.append(_rollup_token(entry))
            else:
                states.append(str(entry).upper())
    elif isinstance(rollup, dict):
        states.append(_rollup_token(rollup))
    else:
        states.append(str(rollup).upper())
    if not states:
        return "unknown"
    if any(token in _FAILING_CHECK_TOKENS for token in states):
        return "failing"
    if any(token in _PENDING_CHECK_TOKENS for token in states):
        return "pending"
    if all(token in _PASSING_CHECK_TOKENS for token in states):
        return "passing"
    return "unknown"


def _task_alive(item: dict[str, Any]) -> bool | None:
    """Liveness of a task row. Missing evidence is unknown, not alive."""
    dispatch = (item.get("projections") or {}).get("dispatch") or {}
    alive = dispatch.get("alive")
    if isinstance(alive, list):
        if not alive:
            return None
        flag = alive[0]
    else:
        flag = alive
    if flag is True:
        return True
    if flag is False:
        return False
    return None


def _execution_liveness_reason(dispatch: dict[str, Any]) -> str | None:
    """A running or spawning task with dead or unknown liveness is not healthy execution."""
    statuses = dispatch.get("statuses") or []
    alive = dispatch.get("alive") or []
    if not isinstance(statuses, list):
        return None
    for index, status in enumerate(statuses):
        if status not in _ACTIVE_EXECUTION:
            continue
        flag = alive[index] if isinstance(alive, list) and index < len(alive) else None
        if flag is True:
            continue
        if flag is False:
            return "task_liveness_dead"
        return "task_liveness_unknown"
    return None


def _linked_terminal(dispatch: dict[str, Any]) -> str | None:
    statuses = dispatch.get("statuses") or []
    if not isinstance(statuses, list):
        return None
    for status in statuses:
        if status in _VISIBLE_TERMINALS or status == "needs_finalize":
            return str(status)
    return None


def derive_health(item: dict[str, Any], *, source_ok: bool) -> str:
    """Rule-derived health. Never infers from activity metrics."""
    if not source_ok:
        return "UNKNOWN"

    flags = item.get("flags") or {}
    if flags.get("dependency_cycle"):
        return "OFF_TRACK"
    if flags.get("dependency_violated"):
        return "OFF_TRACK"

    kind = item.get("resource_kind")
    projections = item.get("projections") or {}
    stream = projections.get("stream") or {}
    review = projections.get("review") or {}
    verification = projections.get("verification") or {}
    dispatch = projections.get("dispatch") or {}

    if kind == "pr":
        check = verification.get("ci_state") or "unknown"
        if check == "failing":
            return "OFF_TRACK"
        if item.get("lifecycle") == "draft":
            return "AT_RISK"
        if check == "pending":
            return "AT_RISK"
        decision = str(review.get("review_decision") or "").upper()
        if decision in {"CHANGES_REQUESTED"}:
            return "OFF_TRACK"
        if decision in {"", "REVIEW_REQUIRED", "NONE"} and check == "passing":
            return "AT_RISK"
        if decision == "APPROVED" and check == "passing":
            evidence = verification.get("merge_evidence") or {}
            if evidence.get("state") == "ready":
                return "ON_TRACK"
            return "UNKNOWN"
        if check == "unknown":
            return "UNKNOWN"
        return "AT_RISK"

    if kind == "issue":
        status = stream.get("status") or "unknown"
        # Current membership unknown is never green, including a stale orphan
        # or multi-home classification kept only as history.
        if status == "unknown":
            return "UNKNOWN"
        if flags.get("has_blocker"):
            return "AT_RISK"
        if status == "multi_homed":
            return "OFF_TRACK"
        if status == "orphan":
            return "AT_RISK"
        if status == "pending_native":
            return "AT_RISK"
        if _execution_liveness_reason(dispatch) or _linked_terminal(dispatch):
            return "AT_RISK"
        if status in {"homed", "epic"}:
            return "ON_TRACK"
        return "UNKNOWN"

    if kind == "task":
        status = str(item.get("lifecycle") or "")
        if status in _OFF_TRACK_TERMINALS:
            return "OFF_TRACK"
        if status in _VISIBLE_TERMINALS or status == "needs_finalize":
            return "AT_RISK"
        if status in _ACTIVE_EXECUTION:
            # Dead or unknown liveness is attention, not healthy execution.
            return "AT_RISK"
        # ``done`` proves the dispatch ended. It does not prove delivery.
        return "UNKNOWN"

    if kind == "review":
        # formal_review_jobs is the retired sealed-CF era dataset (operator
        # 2026-08-07); the current direct ask-<lane> CF flow writes nothing
        # there. Only rows still in flight can be attention-driving — every
        # terminal state (failed/rejected/error/complete/completed/published),
        # sealed or not, is historical and must read neutral, never OFF_TRACK
        # (issue #6862).
        state = str(item.get("lifecycle") or "")
        if state in {"running", "queued", "pending"}:
            return "AT_RISK"
        return "UNKNOWN"

    return "UNKNOWN"


def _issue_unknown_reasons(item: dict[str, Any], stream: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    flags = item.get("flags") or {}
    if flags.get("source_ok") is False:
        reasons.append("source_unavailable")
    membership_reason = stream.get("membership_reason")
    if isinstance(membership_reason, str) and membership_reason:
        reasons.append(membership_reason)
    if not reasons:
        reasons.append("authority_unknown")
    return reasons


def derive_safe_next_action(item: dict[str, Any]) -> dict[str, Any]:
    kind = item.get("resource_kind")
    flags = item.get("flags") or {}
    projections = item.get("projections") or {}
    stream = projections.get("stream") or {}
    review = projections.get("review") or {}
    verification = projections.get("verification") or {}
    dispatch = projections.get("dispatch") or {}

    # Missing qualification fails closed. Unit callers that omit the flag keep
    # the previous rule path; a projection row always sets the flag.
    if flags.get("source_ok") is False:
        return _action("INSPECT_UNKNOWN", ["source_unavailable"], "unknown")
    if flags.get("dependency_cycle"):
        return _action("RESOLVE_BLOCKER", ["dependency_cycle"], "ready")
    if flags.get("has_blocker"):
        return _action("RESOLVE_BLOCKER", ["blocked_by"], "waiting")

    if kind == "issue":
        status = stream.get("status")
        if status == "orphan":
            return _action("TRIAGE_ORPHAN", ["stream_orphan"], "ready")
        if status == "multi_homed":
            return _action("RESOLVE_MULTI_HOME", ["stream_multi_homed"], "ready")
        if status == "pending_native":
            return _action("LINK_PENDING_NATIVE", ["pending_native_link"], "ready")
        liveness = _execution_liveness_reason(dispatch)
        if liveness:
            return _action("INSPECT_UNKNOWN", [liveness], "unknown")
        terminal = _linked_terminal(dispatch)
        if terminal:
            return _action("INSPECT_UNKNOWN", [f"task_{terminal}"], "unknown")
        if status == "unknown" or item.get("health") == "UNKNOWN":
            return _action("INSPECT_UNKNOWN", _issue_unknown_reasons(item, stream), "unknown")
        return _action("OPEN_GITHUB", ["public_issue"], "none")

    if kind == "pr":
        ci = verification.get("ci_state") or "unknown"
        decision = str(review.get("review_decision") or "").upper()
        if ci == "failing":
            return _action("FIX_CI", ["ci_failing"], "ready")
        if ci == "pending":
            return _action("WAIT_CI", ["ci_pending"], "waiting")
        if decision == "CHANGES_REQUESTED":
            return _action("ADDRESS_REVIEW", ["changes_requested"], "ready")
        if decision in {"", "NONE", "REVIEW_REQUIRED"} and ci == "passing":
            return _action("REQUEST_CF_REVIEW", ["review_required"], "ready")
        if decision == "APPROVED" and ci == "passing":
            evidence = verification.get("merge_evidence") or {}
            if evidence.get("state") == "ready":
                return _action("MERGE_WHEN_READY", ["ci_passed_current_head"], "ready")
            reason = str(evidence.get("reason") or "merge_evidence_unknown")
            return _action("INSPECT_UNKNOWN", [reason], "unknown")
        if decision == "APPROVED":
            # Unknown CI must name the same reason as merge evidence. Waiting
            # on review would hide that the head is already approved.
            evidence = verification.get("merge_evidence") or {}
            reason = str(evidence.get("reason") or "ci_unknown")
            return _action("INSPECT_UNKNOWN", [reason], "unknown")
        if item.get("lifecycle") == "draft":
            return _action("OPEN_GITHUB", ["draft_pr"], "none")
        return _action("WAIT_REVIEW", ["pr_open"], "waiting")

    if kind == "task":
        status = str(item.get("lifecycle") or "")
        if status in _ACTIVE_EXECUTION:
            alive = _task_alive(item)
            if alive is True:
                return _action("CONTINUE_DISPATCH", [f"task_{status}"], "ready")
            reason = "task_liveness_dead" if alive is False else "task_liveness_unknown"
            return _action("INSPECT_UNKNOWN", [reason], "unknown")
        if status == "needs_finalize":
            return _action("INSPECT_UNKNOWN", ["task_needs_finalize"], "unknown")
        if status in _VISIBLE_TERMINALS:
            return _action("INSPECT_UNKNOWN", [f"task_{status}"], "unknown")
        if status == "done":
            return _action("NONE", ["task_done_not_delivered"], "none")
        return _action("INSPECT_UNKNOWN", ["task_terminal"], "unknown")

    if kind == "review":
        if item.get("lifecycle") in {"running", "queued", "pending"}:
            return _action("WAIT_REVIEW", ["formal_review_pending"], "waiting")
        if review.get("sealed_verdict_available"):
            return _action("NONE", ["sealed_verdict_available"], "none")
        # Retired sealed-CF era rows (terminal or unresolved "open" jobs the
        # dead pipeline never sealed) never ask for a CF review themselves —
        # that ask belongs to the PR row under the current direct ask-<lane>
        # flow (issue #6862).
        return _action("NONE", ["formal_review_terminal_historical"], "none")

    if item.get("health") == "UNKNOWN":
        return _action("INSPECT_UNKNOWN", ["unknown_health"], "unknown")
    return _action("NONE", ["no_action"], "none")


def _parse_observed_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _unknown(reason: str) -> dict[str, str]:
    return {"state": "unknown", "reason": reason}


def qualify_merge_advice(
    item: dict[str, Any],
    ledger: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> dict[str, str]:
    """Public-safe merge qualification for one PR row.

    Positive advice requires ``evaluate`` on the latest persisted receipt to
    return ``CI_PASSED`` with no hard blockers, the receipt to match this
    repository, PR, and head within ``LEDGER_RECEIPT_FRESHNESS_S`` and not
    further ahead than ``LEDGER_RECEIPT_FUTURE_TOLERANCE_S``, and Work's own
    same-head observation to show a non-draft PR whose merge state is
    neither ``DIRTY`` nor ``UNKNOWN``, with no requested changes and CI neither
    failing nor pending. Anything else suppresses merge advice.
    """
    if not isinstance(ledger, dict):
        return _unknown("no_ledger")
    receipts = ledger.get("observation_receipts")
    if not isinstance(receipts, list) or not receipts or not isinstance(receipts[-1], dict):
        return _unknown("no_ledger")
    receipt = receipts[-1]
    observation = receipt.get("observation")
    if not isinstance(observation, dict):
        return _unknown("no_ledger")

    github = observation.get("github") if isinstance(observation.get("github"), dict) else {}
    pr = github.get("pr") if isinstance(github.get("pr"), dict) else {}
    repository = str(item.get("repository_id") or "")
    if str(github.get("repository") or "") != repository:
        return _unknown("receipt_repository_mismatch")
    try:
        pr_number = int(item.get("remote_id"))
    except (TypeError, ValueError):
        return _unknown("receipt_pr_mismatch")
    if pr.get("number") != pr_number:
        return _unknown("receipt_pr_mismatch")
    verification = (item.get("projections") or {}).get("verification") or {}
    head = verification.get("head_sha")
    if not isinstance(head, str) or not head or pr.get("head_sha") != head:
        return _unknown("receipt_head_mismatch")

    observed = _parse_observed_at(receipt.get("observed_at"))
    if observed is None:
        return _unknown("receipt_observed_at_missing")
    moment = now if now is not None else datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    age_s = (moment.astimezone(UTC) - observed).total_seconds()
    if age_s < LEDGER_RECEIPT_FUTURE_TOLERANCE_S:
        return _unknown("receipt_observed_at_future")
    if age_s > LEDGER_RECEIPT_FRESHNESS_S:
        return _unknown("receipt_stale")

    try:
        from scripts.orchestration.task_lifecycle import LifecycleError, evaluate

        result = evaluate(ledger, observation)
    except LifecycleError:
        return _unknown("lifecycle_error")
    except Exception:
        return _unknown("evaluation_exception")
    if not isinstance(result, dict):
        return _unknown("evaluation_exception")
    hard = result.get("hard_blockers") or []
    if hard:
        return _unknown("hard_blockers")
    if result.get("last_success_state") != "CI_PASSED":
        return _unknown("ci_not_passed")

    if item.get("lifecycle") == "draft":
        return _unknown("draft")
    merge_state = str(verification.get("merge_state_status") or "").upper()
    if not merge_state or merge_state == "UNKNOWN":
        return _unknown("merge_state_unknown")
    if merge_state == "DIRTY":
        return _unknown("merge_state_dirty")
    decision = str((((item.get("projections") or {}).get("review") or {}).get("review_decision")) or "").upper()
    if decision == "CHANGES_REQUESTED":
        return _unknown("changes_requested")
    ci_state = verification.get("ci_state") or "unknown"
    if ci_state == "failing":
        return _unknown("ci_failing")
    if ci_state == "pending":
        return _unknown("ci_pending")
    if ci_state != "passing":
        return _unknown("ci_unknown")
    return {"state": "ready", "reason": "ci_passed_current_head"}


def index_ledgers_by_pr(ledgers: list[dict[str, Any]] | None) -> dict[tuple[str, int], list[dict[str, Any]]]:
    """Group persisted ledgers by ``(repository, pr number)``. Ambiguous groups stay lists."""
    found: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for ledger in ledgers or []:
        if not isinstance(ledger, dict):
            continue
        identity = ledger.get("identity") if isinstance(ledger.get("identity"), dict) else {}
        pr = ledger.get("pr") if isinstance(ledger.get("pr"), dict) else {}
        repository = identity.get("repository")
        number = pr.get("number")
        if isinstance(repository, str) and isinstance(number, int) and not isinstance(number, bool):
            found.setdefault((repository, number), []).append(ledger)
    return found


def attach_merge_evidence(
    items: list[dict[str, Any]],
    ledgers: list[dict[str, Any]] | None,
    *,
    now: datetime | None = None,
) -> None:
    """Stamp each PR row with a public-safe merge qualification. Ledger bodies stay out."""
    index = index_ledgers_by_pr(ledgers)
    for item in items:
        if item.get("resource_kind") != "pr":
            continue
        projections = item.setdefault("projections", {})
        verification = projections.setdefault("verification", {})
        repository = str(item.get("repository_id") or "")
        try:
            number = int(item.get("remote_id"))
        except (TypeError, ValueError):
            verification["merge_evidence"] = _unknown("no_ledger")
            continue
        group = index.get((repository, number), [])
        if len(group) > 1:
            verification["merge_evidence"] = _unknown("ledger_ambiguous")
            continue
        verification["merge_evidence"] = qualify_merge_advice(
            item,
            group[0] if group else None,
            now=now,
        )


def attention_rank_key(item: dict[str, Any]) -> tuple:
    """Lower tuple sorts first (higher attention). Deterministic tie-break on work_id."""
    health = item.get("health") or "UNKNOWN"
    flags = item.get("flags") or {}
    kind = item.get("resource_kind") or ""
    stream_status = ((item.get("projections") or {}).get("stream") or {}).get("status") or ""
    return (
        HEALTH_RANK.get(health, 9),
        0 if flags.get("dependency_cycle") else 1,
        0 if stream_status == "multi_homed" else 1,
        0 if stream_status == "orphan" else 1,
        0 if kind == "pr" and health != "ON_TRACK" else 1,
        0 if kind == "task" and item.get("lifecycle") in {"running", "failed"} else 1,
        str(item.get("work_id") or ""),
    )


def assign_attention(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(items, key=attention_rank_key)
    attention: list[dict[str, Any]] = []
    for rank, item in enumerate(ordered):
        item["attention_rank"] = rank
        attention.append(
            {
                "work_id": item["work_id"],
                "attention_rank": rank,
                "health": item["health"],
                "safe_next_action": item["safe_next_action"],
                "title": item.get("title") or "",
                "resource_kind": item.get("resource_kind"),
                "repository_id": item.get("repository_id"),
                "remote_id": item.get("remote_id"),
            }
        )
    return attention


def apply_health_and_actions(
    items: list[dict[str, Any]],
    *,
    source_ok: bool,
) -> list[dict[str, Any]]:
    for item in items:
        flags = item.get("flags")
        row_ok = bool(flags["source_ok"]) if isinstance(flags, dict) and "source_ok" in flags else source_ok
        item["health"] = derive_health(item, source_ok=row_ok)
        item["safe_next_action"] = derive_safe_next_action(item)
        if not isinstance(item.get("flags"), dict):
            item["flags"] = {}
        item["flags"]["attention"] = is_actionable(item)
    return assign_attention(items)
