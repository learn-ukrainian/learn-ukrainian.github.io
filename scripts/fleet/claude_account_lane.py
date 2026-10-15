"""The ``claude`` lane as the account a claude dispatch runs as (#10619).

The routing-budget ``claude`` lane row is the Monitor host's default account
(``a``). A claude dispatch that runs as another account is judged on that
account's ``claude_accounts`` row instead, by every decision that reads the
claude lane: the dispatch budget guard, reviewer selection, and the
plan-headroom stop (``scripts.agent_runtime.model_pause``).

The account view keeps the lane row's route facts, which no account owns
(``SHARED_ROUTE_FACT_KEYS``): spawn-phase lane health (one streak over every
account's claude tasks, so start-up, sandbox and CLI faults), route
eligibility, the route circuit, the review scheduler's concurrency state, and
the runtime outcome counts. It drops everything that is one account's meter:
the default account's usage windows, pace, credit, login and probe state, the
scheduler's quota reading (``SCHEDULER_QUOTA_FIELDS``), and the runtime
rate-limit evidence (``ACCOUNT_RATE_LIMIT_FIELDS``). A Claude rate limit is one
account's quota event, but runtime usage records carry no account label, so a
rate-limit cluster cannot be attributed to an account; it is reported as
unattributed evidence and never becomes another account's capacity verdict.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

SHARED_ROUTE_FACT_KEYS = ("health", "runtime", "scheduler", "circuit_open", "eligible")
ACCOUNT_RATE_LIMIT_FIELDS = frozenset(
    {"rate_limited", "last_rate_limited_at", "models_rate_limited", "headroom_blocked", "headroom_reason"}
)
SCHEDULER_QUOTA_FIELDS = frozenset({"quota_remaining_pct", "quota_stale"})
# The normalizer's error-shape keys, which the producer leaves out of a lane's ``codexbar``.
_NATIVE_ERROR_SHAPE_KEYS = frozenset({"lane", "status", "auth_error", "error_kind", "error_code"})


def account_left_pct(window: Any) -> float | None:
    """A ``claude_accounts`` window's ``left_pct`` when it is a real percentage, else None."""
    value = window.get("left_pct") if isinstance(window, Mapping) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value) if 0 <= value <= 100 else None


def _without(record: Any, keys: frozenset[str]) -> Any:
    return {key: value for key, value in record.items() if key not in keys} if isinstance(record, Mapping) else record


def route_facts(lane_row: Any) -> dict[str, Any]:
    """The lane row's route facts with every account meter field removed."""
    lane = lane_row if isinstance(lane_row, Mapping) else {}
    route = {key: lane[key] for key in SHARED_ROUTE_FACT_KEYS if key in lane}
    if "runtime" in route:
        route["runtime"] = _without(route["runtime"], ACCOUNT_RATE_LIMIT_FIELDS)
    if "scheduler" in route:
        route["scheduler"] = _without(route["scheduler"], SCHEDULER_QUOTA_FIELDS)
    return route


def lane_view(row: Any, lane_row: Any) -> tuple[dict[str, Any], str | None]:
    """The ``claude`` lane record for one ``claude_accounts`` row, and why its meter is unknown.

    An ``ok`` or ``stale`` row with known weekly and session ``left_pct`` takes the
    producer's path for the default account: the windows ``_probe_claude_native``
    builds, ``_normalize_provider_data`` and ``_status_from_weekly_used`` on the
    weekly used-%, so near cap, warm and pace deficit use the default lane's
    thresholds. A stale row reads ``stale_last_good`` like a stale default
    probe. Any other row reads status ``unknown`` with the probe
    ``unavailable`` and no pace, and the reason is returned (otherwise None).
    Both carry :func:`route_facts` of the lane row and nothing of the default
    account's own meter, credit or login state.
    """
    from scripts.api.state_router import _status_from_weekly_used
    from scripts.api.subscription_usage import _normalize_provider_data, _window_from_used_pct

    route = route_facts(lane_row)
    meter = row if isinstance(row, Mapping) else {}
    # A non-string status (a list or mapping) is unhashable and never healthy.
    state = meter.get("status") if isinstance(meter.get("status"), str) else None
    session, weekly = meter.get("session5h"), meter.get("weekly")
    session_left, weekly_left = account_left_pct(session), account_left_pct(weekly)
    if state not in {"ok", "stale"} or session_left is None or weekly_left is None:
        if not meter:
            reason = "no account row"
        elif state not in {"ok", "stale"}:
            reason = str(meter.get("reason") or f"status {state or 'missing'}")
        else:
            reason = "weekly or session left_pct unknown"
        return {"status": "unknown", "freshness": "unavailable", **route}, reason
    stale = state == "stale"
    usage = {
        "primary": _window_from_used_pct(100.0 - session_left, window_minutes=300, resets_at=session.get("resets_at")),
        "secondary": _window_from_used_pct(
            100.0 - weekly_left, window_minutes=10080, resets_at=weekly.get("resets_at")
        ),
    }
    native = _normalize_provider_data("claude", {"provider": "claude", "source": "claude_account", "usage": usage})
    native.update({"freshness": "stale_last_good" if stale else "fresh", "stale": stale, "age_s": meter.get("age_s")})
    used = 100.0 - weekly_left  # the producer's capacity used-%: the weekly window's
    status = _status_from_weekly_used(
        used, native, lane="claude", info={**native, "codexbar": native}, snapshot_stale=stale
    )
    return {
        "status": status,
        "status_source": "weekly_pace",
        "interactive": {"status": status, "burn_pct_7d": used},
        "burn_pct_7d": used,
        "remaining_pct": 100.0 - used,
        "resets_at": native.get("weekly_resets_at"),
        "freshness": native["freshness"],
        "age_s": native["age_s"],
        "codexbar": {key: value for key, value in native.items() if key not in _NATIVE_ERROR_SHAPE_KEYS},
        **route,
    }, None


def select_account(payload: Mapping[str, Any], label: str | None) -> tuple[Mapping[str, Any], dict[str, Any] | None]:
    """``payload`` with its ``claude`` lane read as account ``label``, and the account evidence.

    ``label`` None (not a claude dispatch) returns the payload and no evidence.
    The default label keeps the lane row (``meter`` ``agents.claude``). Another
    label gets a copy whose ``agents.claude`` is :func:`lane_view` of its
    ``claude_accounts`` row; the evidence names that ``meter``, its ``state``
    (``ok``, ``stale`` or ``unknown``), the ``reason`` it is unknown, and the
    lane row's ``unattributed_rate_limits`` when they blocked it. A payload
    without an ``agents`` map is returned as is, with ``meter`` None.
    """
    from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT

    if label is None:
        return payload, None
    if label == DEFAULT_CLAUDE_ACCOUNT:
        return payload, {"label": label, "meter": "agents.claude"}
    agents = payload.get("agents")
    if not isinstance(agents, Mapping):
        return payload, {"label": label, "meter": None}
    row_key = f"claude:{label}"
    rows = payload.get("claude_accounts")
    lane_row = agents.get("claude")
    view, unknown = lane_view(rows.get(row_key) if isinstance(rows, Mapping) else None, lane_row)
    evidence: dict[str, Any] = {
        "label": label,
        "meter": f"claude_accounts.{row_key}",
        "state": "unknown" if unknown is not None else "stale" if view["freshness"] != "fresh" else "ok",
        "reason": unknown,
    }
    runtime = lane_row.get("runtime") if isinstance(lane_row, Mapping) else None
    if isinstance(runtime, Mapping) and runtime.get("headroom_blocked"):
        evidence["unattributed_rate_limits"] = {
            key: runtime[key] for key in sorted(ACCOUNT_RATE_LIMIT_FIELDS) if key in runtime
        }
    return {**payload, "agents": {**agents, "claude": view}}, evidence


def account_weekly_used_pct(payload: Any, label: str) -> float | None:
    """Account ``label``'s weekly used-% from a routing-budget payload, or None.

    Only an ``ok`` row (measured within the cache TTL, no failure since) with a
    known weekly ``left_pct`` gives a reading: like the lane row's fresh-probe
    rule, a stale, unknown or missing row never blocks.
    """
    rows = payload.get("claude_accounts") if isinstance(payload, Mapping) else None
    row = rows.get(f"claude:{label}") if isinstance(rows, Mapping) else None
    if not isinstance(row, Mapping) or row.get("status") != "ok" or row.get("stale") is not False:
        return None
    left = account_left_pct(row.get("weekly"))
    return None if left is None else 100.0 - left
