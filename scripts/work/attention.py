"""Deterministic health, attention rank, and safe-next-action derivation.

Activity volume, comment counts, story points, and model opinion are never
health evidence (frozen brief semantics).
"""

from __future__ import annotations

from typing import Any

HEALTH_RANK = {
    "OFF_TRACK": 0,
    "AT_RISK": 1,
    "UNKNOWN": 2,
    "ON_TRACK": 3,
}

# Actionable-view deny list (#6850): rows whose only next step is browsing
# GitHub, inspecting an unknown, or nothing are not pick-list work. This is
# the SSOT for the server-side predicate; dashboards/work.html mirrors it in
# JS (parity contract test in tests/test_work_dashboard.py).
NON_ACTIONABLE_ACTION_CODES = frozenset({"INSPECT_UNKNOWN", "OPEN_GITHUB", "NONE"})


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


def _pr_check_state(pr: dict[str, Any] | None) -> str:
    """Return failing | pending | passing | unknown from GH list rollup only."""
    if not pr:
        return "unknown"
    rollup = pr.get("statusCheckRollup")
    if rollup is None:
        return "unknown"
    states: list[str] = []
    if isinstance(rollup, list):
        for entry in rollup:
            if isinstance(entry, dict):
                # Cancelled runs can leave an unexpanded matrix parent, not a real check.
                if "${{" in str(entry.get("name") or ""):
                    continue
                states.append(str(entry.get("state") or entry.get("conclusion") or "").upper())
            else:
                states.append(str(entry).upper())
    elif isinstance(rollup, dict):
        states.append(str(rollup.get("state") or "").upper())
    else:
        states.append(str(rollup).upper())
    if not states:
        return "unknown"
    if any(s in {"FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"} for s in states):
        return "failing"
    if any(s in {"PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED"} for s in states):
        return "pending"
    if all(s in {"SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED"} for s in states):
        return "passing"
    return "unknown"


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
            return "ON_TRACK"
        if check == "unknown":
            return "UNKNOWN"
        return "AT_RISK"

    if kind == "issue":
        status = stream.get("status") or "unknown"
        # Streams authority missing/stale for membership → UNKNOWN not green.
        if status == "unknown" and not stream.get("fresh") and stream.get("authority_missing"):
            return "UNKNOWN"
        if flags.get("has_blocker"):
            return "AT_RISK"
        if status == "multi_homed":
            return "OFF_TRACK"
        if status == "orphan":
            return "AT_RISK"
        if status == "pending_native":
            return "AT_RISK"
        if any(s in {"failed", "timeout", "no_deliverable"} for s in (dispatch.get("statuses") or [])):
            return "AT_RISK"
        if status in {"homed", "epic"}:
            return "ON_TRACK"
        return "ON_TRACK"

    if kind == "task":
        status = str(item.get("lifecycle") or "")
        if status in {"failed", "timeout", "no_deliverable"}:
            return "OFF_TRACK"
        if status in {"running", "spawning", "needs_finalize"}:
            return "AT_RISK"
        if status == "done":
            return "ON_TRACK"
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


def derive_safe_next_action(item: dict[str, Any]) -> dict[str, Any]:
    kind = item.get("resource_kind")
    flags = item.get("flags") or {}
    projections = item.get("projections") or {}
    stream = projections.get("stream") or {}
    review = projections.get("review") or {}
    verification = projections.get("verification") or {}
    reasons: list[str] = []

    if flags.get("dependency_cycle"):
        return {"code": "RESOLVE_BLOCKER", "reason_codes": ["dependency_cycle"]}
    if flags.get("has_blocker"):
        return {"code": "RESOLVE_BLOCKER", "reason_codes": ["blocked_by"]}

    if kind == "issue":
        status = stream.get("status")
        if status == "orphan":
            return {"code": "TRIAGE_ORPHAN", "reason_codes": ["stream_orphan"]}
        if status == "multi_homed":
            return {"code": "RESOLVE_MULTI_HOME", "reason_codes": ["stream_multi_homed"]}
        if status == "pending_native":
            return {"code": "LINK_PENDING_NATIVE", "reason_codes": ["pending_native_link"]}
        if item.get("health") == "UNKNOWN":
            return {"code": "INSPECT_UNKNOWN", "reason_codes": ["authority_unknown"]}
        return {"code": "OPEN_GITHUB", "reason_codes": ["public_issue"]}

    if kind == "pr":
        ci = verification.get("ci_state") or "unknown"
        decision = str(review.get("review_decision") or "").upper()
        if ci == "failing":
            return {"code": "FIX_CI", "reason_codes": ["ci_failing"]}
        if ci == "pending":
            return {"code": "WAIT_CI", "reason_codes": ["ci_pending"]}
        if decision == "CHANGES_REQUESTED":
            return {"code": "ADDRESS_REVIEW", "reason_codes": ["changes_requested"]}
        if decision in {"", "NONE", "REVIEW_REQUIRED"} and ci == "passing":
            return {"code": "REQUEST_CF_REVIEW", "reason_codes": ["review_required"]}
        if decision == "APPROVED" and ci == "passing":
            return {"code": "MERGE_WHEN_READY", "reason_codes": ["approved_ci_green"]}
        if item.get("lifecycle") == "draft":
            return {"code": "OPEN_GITHUB", "reason_codes": ["draft_pr"]}
        reasons.append("pr_open")
        return {"code": "WAIT_REVIEW", "reason_codes": reasons or ["review_pending"]}

    if kind == "task":
        status = str(item.get("lifecycle") or "")
        if status in {"running", "spawning", "needs_finalize"}:
            return {"code": "CONTINUE_DISPATCH", "reason_codes": [f"task_{status}"]}
        if status in {"failed", "timeout", "no_deliverable"}:
            return {"code": "INSPECT_UNKNOWN", "reason_codes": [f"task_{status}"]}
        return {"code": "NONE", "reason_codes": ["task_terminal"]}

    if kind == "review":
        if item.get("lifecycle") in {"running", "queued", "pending"}:
            return {"code": "WAIT_REVIEW", "reason_codes": ["formal_review_pending"]}
        if review.get("sealed_verdict_available"):
            return {"code": "NONE", "reason_codes": ["sealed_verdict_available"]}
        # Retired sealed-CF era rows (terminal or unresolved "open" jobs the
        # dead pipeline never sealed) never ask for a CF review themselves —
        # that ask belongs to the PR row under the current direct ask-<lane>
        # flow (issue #6862).
        return {"code": "NONE", "reason_codes": ["formal_review_terminal_historical"]}

    if item.get("health") == "UNKNOWN":
        return {"code": "INSPECT_UNKNOWN", "reason_codes": ["unknown_health"]}
    return {"code": "NONE", "reason_codes": ["no_action"]}


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
        item["health"] = derive_health(item, source_ok=source_ok)
        item["safe_next_action"] = derive_safe_next_action(item)
    return assign_attention(items)
