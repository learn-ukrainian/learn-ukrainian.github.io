"""The Claude account is part of the route key (#10619, #10630).

A claude seat runs as one Claude account, so every decision about a claude
route is a decision about that account: the dispatch budget guard, reviewer
selection (dispatch admission and ``closeout_cli resolve-reviewer``) and the
plan-headroom stop (``scripts.agent_runtime.model_pause``). This module owns
that key and the only reads of the routing snapshot's claude meter:

- :class:`ClaudeAccount` is the account part of a route key. It is built only
  here: :func:`resolve_route_account` resolves and binds a dispatch's account
  before admission, :func:`account_from_record` reads a task record's, and
  :func:`no_claude_account` is the account of a route that reaches no claude seat.
- :func:`select_account`, :func:`account_agents`, :func:`lane_record`,
  :func:`account_weekly_used_pct` and :func:`capacity_verdict` read the
  snapshot for a named account; none has a default, and a call without a
  ``ClaudeAccount`` raises ``TypeError``. :func:`other_lane_record` reads a
  lane no account owns and refuses the claude lane.

The routing-budget ``claude`` lane row is the Monitor host's default account
(``a``). Another account is read from its ``claude_accounts`` row instead. The
account view keeps the lane row's route facts, which no account owns
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
An unresolved account's meter reads as unknown, and no claude seat is
selected on it.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

SHARED_ROUTE_FACT_KEYS = ("health", "runtime", "scheduler", "circuit_open", "eligible")
ACCOUNT_RATE_LIMIT_FIELDS = frozenset(
    {"rate_limited", "last_rate_limited_at", "models_rate_limited", "headroom_blocked", "headroom_reason"}
)
SCHEDULER_QUOTA_FIELDS = frozenset({"quota_remaining_pct", "quota_stale"})
# The normalizer's error-shape keys, which the producer leaves out of a lane's ``codexbar``.
_NATIVE_ERROR_SHAPE_KEYS = frozenset({"lane", "status", "auth_error", "error_kind", "error_code"})
# The source of an account that could not be resolved or bound.
UNRESOLVED_SOURCE = "unresolved"
# The capacity verdict on one account's claude seat (:func:`capacity_verdict`).
HOT, HEALTHY, UNKNOWN = "hot", "healthy", "unknown"


@dataclass(frozen=True)
class ClaudeAccount:
    """The account a claude route runs as: the account part of its route key (#10630).

    A resolved account has a ``label`` and the ``source`` it came from. An
    unresolved one has no label, source ``unresolved`` and the
    ``ClaudeAccountRefused`` code in ``refusal``: its meter reads as unknown
    and no claude seat is selected on it. Built only by this module.
    """

    label: str | None
    source: str
    refusal: str | None = None

    def __post_init__(self) -> None:
        from scripts.agent_runtime.attempt_boundary import (
            CLAUDE_ACCOUNT_LABELS,
            CLAUDE_ACCOUNT_REFUSAL_CODES,
            CLAUDE_ACCOUNT_SOURCES,
        )

        if self.label is None:
            valid = self.source == UNRESOLVED_SOURCE and self.refusal in CLAUDE_ACCOUNT_REFUSAL_CODES
        else:
            valid = self.label in CLAUDE_ACCOUNT_LABELS and self.source in CLAUDE_ACCOUNT_SOURCES
            valid = valid and self.refusal is None
        if not valid:
            raise ValueError("invalid Claude account route key")

    @property
    def resolved(self) -> bool:
        return self.label is not None


def require_account(account: object) -> ClaudeAccount:
    """``account`` when it is a :class:`ClaudeAccount`; anything else (a bare label, None) raises ``TypeError``."""
    if not isinstance(account, ClaudeAccount):
        raise TypeError(f"the claude lane is read for a named ClaudeAccount (#10630), not {type(account).__name__}")
    return account


def resolve_route_account(
    explicit: object = None,
    *,
    strict: bool,
    recorded: Callable[[], str | None] | None = None,
    environ: Mapping[str, str] | None = None,
) -> ClaudeAccount:
    """The account a request's claude routes run as, resolved and bound before admission (#10619, #10733).

    The label is, in order: ``recorded()`` (a ``--force-new`` re-run's earlier
    record; a different ``explicit`` label is refused), ``explicit``, the
    default-account file, then the built-in default. A non-default label then
    has its binding and credential sources verified (``verify_claude_account``),
    so no claude seat is admitted on an account that was not bound. ``strict``
    (a claude request) raises ``ClaudeAccountRefused``; otherwise a refusal
    returns the unresolved account with its code.
    """
    from scripts.agent_runtime.attempt_boundary import (
        ClaudeAccountRefused,
        resolve_claude_account_label,
        resolve_dispatch_claude_account,
        verify_claude_account,
    )

    try:
        previous = recorded() if recorded is not None else None
        if previous is None:
            label, source = resolve_dispatch_claude_account(explicit, environ=environ)
        elif explicit is None:
            label, source = previous, "record"
        elif resolve_claude_account_label(explicit) == previous:
            label, source = previous, "explicit"
        else:
            raise ClaudeAccountRefused("claude_account_record_conflict")
        verify_claude_account(label, environ=environ)
    except ClaudeAccountRefused as exc:
        if strict:
            raise
        return ClaudeAccount(None, UNRESOLVED_SOURCE, exc.code)
    return ClaudeAccount(label, source)


def no_claude_account() -> ClaudeAccount:
    """The account of a route that reaches no claude seat: unresolved, so nothing claude is judged or admitted on it."""
    return ClaudeAccount(None, UNRESOLVED_SOURCE, "claude_account_seat_unsupported")


def account_from_record(record: Mapping[str, Any], *, agent: str) -> ClaudeAccount:
    """The account a task record's seat runs as (#10619).

    A claude record names its label, bound at dispatch and verified again
    where the worker authenticates; a claude record without one predates
    labels and ran as the default account. Another seat's record names no
    Claude account, so the result is unresolved and no claude reading is
    judged on it.
    """
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_ACCOUNT_KEY,
        ClaudeAccountRefused,
        resolve_claude_account_label,
    )

    if agent != "claude":
        return no_claude_account()
    try:
        label = resolve_claude_account_label(record.get(CLAUDE_ACCOUNT_KEY))
    except ClaudeAccountRefused as exc:
        return ClaudeAccount(None, UNRESOLVED_SOURCE, exc.code)
    return ClaudeAccount(label, "record")


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
    meter: Mapping[str, Any] = row if isinstance(row, Mapping) else {}
    # A non-string status (a list or mapping) is unhashable and never healthy.
    state = meter.get("status") if isinstance(meter.get("status"), str) else None
    session, weekly = meter.get("session5h"), meter.get("weekly")
    session_left, weekly_left = account_left_pct(session), account_left_pct(weekly)
    if (
        state not in {"ok", "stale"}
        or session_left is None
        or weekly_left is None
        or not isinstance(session, Mapping)
        or not isinstance(weekly, Mapping)
    ):
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


def select_account(payload: Mapping[str, Any], *, account: ClaudeAccount) -> tuple[Mapping[str, Any], dict[str, Any]]:
    """``payload`` with its ``claude`` lane read as ``account``, and the account evidence.

    The default account keeps the lane row (``meter`` ``agents.claude``).
    Another resolved account gets a copy whose ``agents.claude`` is
    :func:`lane_view` of its ``claude_accounts`` row; the evidence names that
    ``meter``, its ``state`` (``ok``, ``stale`` or ``unknown``), the ``reason``
    it is unknown, and the lane row's ``unattributed_rate_limits`` when they
    blocked it. An unresolved account reads the lane's route facts with an
    unknown meter, state ``unresolved`` and its refusal code as the reason. A
    payload without lane records (no or an empty ``agents`` map) is returned
    as is, with ``meter`` None.
    """
    from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT

    account = require_account(account)
    if account.label == DEFAULT_CLAUDE_ACCOUNT:
        return payload, {"label": account.label, "meter": "agents.claude"}
    unresolved = {} if account.resolved else {"state": "unresolved", "reason": account.refusal}
    agents = payload.get("agents") if isinstance(payload, Mapping) else None
    if not isinstance(agents, Mapping) or not agents:
        return payload, {"label": account.label, "meter": None, **unresolved}
    lane_row = agents.get("claude")
    if account.label is None:
        view: dict[str, Any] = {"status": "unknown", "freshness": "unavailable", **route_facts(lane_row)}
        evidence: dict[str, Any] = {"label": None, "meter": None, **unresolved}
    else:
        row_key = f"claude:{account.label}"
        rows = payload.get("claude_accounts")
        view, unknown = lane_view(rows.get(row_key) if isinstance(rows, Mapping) else None, lane_row)
        evidence = {
            "label": account.label,
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


def account_agents(payload: Mapping[str, Any] | None, *, account: ClaudeAccount) -> Mapping[str, Any]:
    """The snapshot's lane records with the claude lane read as ``account`` (empty when it has none)."""
    view, _ = select_account(payload or {}, account=account)
    agents = view.get("agents")
    return agents if isinstance(agents, Mapping) else {}


def lane_record(payload: Mapping[str, Any] | None, lane: str, *, account: ClaudeAccount) -> Mapping[str, Any]:
    """One lane's record from the snapshot, the claude lane read as ``account`` (empty when absent)."""
    record = account_agents(payload, account=account).get(lane)
    return record if isinstance(record, Mapping) else {}


def other_lane_record(payload: Any, lane: str) -> Mapping[str, Any]:
    """A lane no Claude account owns, read without one; the claude lane raises ``ValueError``."""
    if lane.strip().casefold() == "claude":
        raise ValueError("the claude lane is read for a named account: use lane_record (#10630)")
    agents = payload.get("agents") if isinstance(payload, Mapping) else None
    record = agents.get(lane) if isinstance(agents, Mapping) else None
    return record if isinstance(record, Mapping) else {}


def account_weekly_used_pct(payload: Any, *, account: ClaudeAccount) -> float | None:
    """``account``'s weekly used-% from a routing-budget payload, or None.

    Only a fresh reading may block: the default account's lane row when its
    probe is fresh and not withdrawn (status ``unknown``), another account's
    ``ok`` row (measured within the cache TTL, no failure since) with a known
    weekly ``left_pct``. A stale, unknown or missing reading, and an
    unresolved account, give None.
    """
    from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT

    account = require_account(account)
    if not isinstance(payload, Mapping) or account.label is None:
        return None
    if account.label == DEFAULT_CLAUDE_ACCOUNT:
        agents = payload.get("agents")
        info = agents.get("claude") if isinstance(agents, Mapping) else None
        if not isinstance(info, Mapping) or info.get("status") == "unknown":
            return None  # missing, or withdrawn as stale by Monitor
        codexbar = info.get("codexbar")
        if not isinstance(codexbar, Mapping):
            return None
        if codexbar.get("stale") is not False or codexbar.get("freshness") != "fresh":
            return None  # only a fresh probe reading may block a dispatch
        value = codexbar.get("weekly_used_pct")
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return None
    rows = payload.get("claude_accounts")
    row = rows.get(f"claude:{account.label}") if isinstance(rows, Mapping) else None
    if not isinstance(row, Mapping) or row.get("status") != "ok" or row.get("stale") is not False:
        return None
    left = account_left_pct(row.get("weekly"))
    return None if left is None else 100.0 - left


def capacity_verdict(payload: Mapping[str, Any] | None, *, account: ClaudeAccount) -> str:
    """The capacity verdict on ``account``'s claude seat: :data:`HOT`, :data:`HEALTHY` or :data:`UNKNOWN`.

    The capacity owner's class (:func:`credit_lane.routing_facts`) of the
    claude lane record read as ``account``: ``avoid`` is hot, ``verified`` is
    healthy, and any unknown or stale reading is unknown. An unresolved
    account is unknown whatever the lane row says. Every decision consumer
    reaches the same verdict.
    """
    from scripts.fleet import credit_lane

    if not require_account(account).resolved:
        return UNKNOWN
    diagnostics = payload.get("diagnostics") if isinstance(payload, Mapping) else None
    facts = credit_lane.routing_facts(
        "claude",
        lane_record(payload, "claude", account=account),
        model=None,
        snapshot_metadata=diagnostics if isinstance(diagnostics, Mapping) else None,
    )
    return {credit_lane.CAPACITY_AVOID: HOT, credit_lane.CAPACITY_VERIFIED: HEALTHY}.get(facts.capacity, UNKNOWN)
