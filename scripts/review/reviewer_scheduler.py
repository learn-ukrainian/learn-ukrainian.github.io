"""Deterministic, side-effect-free balancing for eligible formal reviewers.

Hard policy remains in :mod:`reviewer_resolver`.  This module intentionally
does not query Fleet Comms, CodexBar, or process state: callers pass a bounded
routing-budget snapshot and this code makes one reproducible choice from it.
Remaining allowance and observation freshness are the shared owner's pure
readings (:mod:`scripts.fleet.credit_lane`, #9740); nothing here re-derives them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from scripts.fleet import credit_lane
from scripts.review.capacity import review_capacity


@dataclass(frozen=True)
class RoutingMetrics:
    """The route-local signals used only after hard eligibility succeeds.

    ``quota_fresh``, ``inflight`` and ``failures`` are None when the snapshot
    does not observe them: unknown, never stored as fresh or zero (#9740 F5).
    """

    completed_input_bytes: int | None = None
    active_reserved_input_bytes: int | None = None
    quota_remaining_pct: float | None = None
    quota_fresh: bool | None = None
    inflight: int | None = None
    failures: int | None = None
    circuit_open: bool = False
    capacity_exhausted: bool = False

    @property
    def load_bytes(self) -> int | None:
        if self.completed_input_bytes is None and self.active_reserved_input_bytes is None:
            return None
        return (self.completed_input_bytes or 0) + (self.active_reserved_input_bytes or 0)


def _number(value: object, *, minimum: float = 0) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        return None
    return float(value)


def _optional_integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _route_record(
    candidate: Any, snapshot: Mapping[str, object] | None, *, prefer_route: bool = False
) -> Mapping[str, object]:
    if not isinstance(snapshot, Mapping):
        return {}
    keys = (
        candidate.name, candidate.route, candidate.concrete_model, getattr(candidate, "family", ""),
        *sorted(candidate.health_keys),
    )
    if prefer_route:
        # Allowance belongs to the canonical seat; model health aliases must
        # not hide an exhausted shared window. Aliases remain a fallback.
        keys = (candidate.route, *keys)
    agents = snapshot.get("agents")
    if not isinstance(agents, Mapping):
        # Legacy injected health maps carry no quota, but hot still orders
        # otherwise equal review fits without becoming an exclusion.
        for key in keys:
            status = snapshot.get(key)
            if isinstance(status, str):
                return {"status": status.strip().lower()}
        return {}
    for key in keys:
        record = agents.get(key)
        if isinstance(record, Mapping):
            return record
    return {}


def _quota_remaining(record: Mapping[str, object], scheduler: Mapping[str, object]) -> float | None:
    """The owner's tightest plan window; a scheduling-only observation can only tighten it."""
    plan = credit_lane.plan_remaining_pct(record)
    scheduling = _number(scheduler.get("quota_remaining_pct"))
    known = [value for value in (plan, scheduling) if value is not None]
    return min(known) if known else None


def _quota_fresh(record: Mapping[str, object], scheduler: Mapping[str, object], diagnostics: object) -> bool | None:
    """Scheduler-provided ``quota_stale`` first, else the owner's observation freshness; unknown is None."""
    stale = scheduler.get("quota_stale")
    if isinstance(stale, bool):
        return not stale
    freshness, _ = credit_lane.observation_freshness(
        record,
        diagnostics if isinstance(diagnostics, Mapping) else None,
        credit_lane.probe_max_age_s(),
    )
    return {credit_lane.FRESH: True, credit_lane.STALE: False}.get(freshness)


def metrics_for(candidate: Any, snapshot: Mapping[str, object] | None) -> RoutingMetrics:
    """Extract route-local scheduler metrics from one API snapshot; unobserved values stay None."""
    record = _route_record(candidate, snapshot)
    diagnostics = snapshot.get("diagnostics") if isinstance(snapshot, Mapping) else None
    runtime = record.get("runtime") if isinstance(record.get("runtime"), Mapping) else {}
    scheduler = record.get("scheduler") if isinstance(record.get("scheduler"), Mapping) else {}
    in_flight = snapshot.get("in_flight") if isinstance(snapshot, Mapping) else None
    # A snapshot ``in_flight`` map is an observation: an absent route there ran nothing.
    inflight_value = in_flight.get(candidate.route, 0) if isinstance(in_flight, Mapping) else None

    completed = scheduler.get("completed_input_bytes", record.get("completed_input_bytes"))
    reserved = scheduler.get("active_reserved_input_bytes", record.get("active_reserved_input_bytes"))
    failures = scheduler.get("failures", runtime.get("error", record.get("failures")))
    circuit_open = bool(scheduler.get("circuit_open", record.get("circuit_open", runtime.get("circuit_open", False))))
    return RoutingMetrics(
        completed_input_bytes=(int(_number(completed)) if _number(completed) is not None else None),
        active_reserved_input_bytes=(int(_number(reserved)) if _number(reserved) is not None else None),
        quota_remaining_pct=_quota_remaining(record, scheduler),
        quota_fresh=_quota_fresh(record, scheduler, diagnostics),
        inflight=_optional_integer(scheduler.get("inflight", inflight_value)),
        failures=_optional_integer(failures),
        circuit_open=circuit_open,
        capacity_exhausted=bool(scheduler.get("capacity_exhausted", False)),
    )


def circuit_exclusion_reason(candidate: Any, snapshot: Mapping[str, object] | None) -> str | None:
    """Return a hard operational exclusion without balancing candidates."""
    metrics = metrics_for(candidate, snapshot)
    if metrics.circuit_open:
        return "route circuit is open — transport is operationally unavailable"
    if metrics.capacity_exhausted:
        return "credential bucket has no unreserved concurrency slot"
    return None


def stable_tie_break(*, exact_head: str | None, policy_version: str, candidate_name: str) -> str:
    """Stable final tie-break; never derive traffic from YAML insertion order."""
    material = "\0".join((exact_head or "no-exact-head", policy_version, candidate_name))
    return sha256(material.encode("utf-8")).hexdigest()


def selection_key(
    candidate: Any, *, snapshot: Mapping[str, object] | None, exact_head: str | None, policy_version: str
) -> tuple[object, ...]:
    """Return a total order for candidates that already passed every hard gate."""
    metrics = metrics_for(candidate, snapshot)
    weight = float(candidate.capacity_weight)
    load = metrics.load_bytes
    # Fresh capacity evidence outranks stale last-known-good evidence, and both
    # outrank a route with no usable headroom signal. This keeps an unknown
    # account from looking infinitely available merely because it has no
    # recorded work. Fairness then compares normalized work only within the
    # same conservative evidence class.
    load_unknown = load is None
    normalized_load = (load / weight) if load is not None else 0.0
    # Unknown freshness ranks after known-stale evidence; unknown in-flight and
    # failure counts rank after any observed count, never as zero.
    headroom_unknown = metrics.quota_remaining_pct is None
    freshness_rank = {True: 0, False: 1, None: 2}[metrics.quota_fresh]
    capacity_evidence_rank = 3 if headroom_unknown else freshness_rank
    headroom = -(metrics.quota_remaining_pct or 0.0)
    capacity = review_capacity(_route_record(candidate, snapshot, prefer_route=True), (snapshot or {}).get("diagnostics"))
    return (
        capacity.pressure,
        capacity_evidence_rank,
        load_unknown,
        normalized_load,
        headroom,
        (metrics.inflight is None, metrics.inflight or 0),
        (metrics.failures is None, metrics.failures or 0),
        stable_tie_break(exact_head=exact_head, policy_version=policy_version, candidate_name=candidate.name),
    )
