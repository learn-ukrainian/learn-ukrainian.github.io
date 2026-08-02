"""Deterministic, side-effect-free balancing for eligible formal reviewers.

Hard policy remains in :mod:`reviewer_resolver`.  This module intentionally
does not query Fleet Comms, CodexBar, or process state: callers pass a bounded
routing-budget snapshot and this code makes one reproducible choice from it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class RoutingMetrics:
    """The route-local signals used only after hard eligibility succeeds."""

    completed_input_bytes: int | None = None
    active_reserved_input_bytes: int | None = None
    quota_remaining_pct: float | None = None
    quota_fresh: bool = True
    inflight: int = 0
    failures: int = 0
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


def _integer(value: object) -> int:
    number = _number(value)
    return int(number) if number is not None else 0


def _route_record(candidate: Any, snapshot: Mapping[str, object] | None) -> Mapping[str, object]:
    if not isinstance(snapshot, Mapping):
        return {}
    agents = snapshot.get("agents")
    if not isinstance(agents, Mapping):
        return {}
    keys = (candidate.name, candidate.route, candidate.concrete_model, *sorted(candidate.health_keys))
    for key in keys:
        record = agents.get(key)
        if isinstance(record, Mapping):
            return record
    return {}


def metrics_for(candidate: Any, snapshot: Mapping[str, object] | None) -> RoutingMetrics:
    """Extract tolerant route-local scheduler metrics from one API snapshot."""
    record = _route_record(candidate, snapshot)
    diagnostics = snapshot.get("diagnostics") if isinstance(snapshot, Mapping) else None
    runtime = record.get("runtime") if isinstance(record.get("runtime"), Mapping) else {}
    scheduler = record.get("scheduler") if isinstance(record.get("scheduler"), Mapping) else {}
    in_flight = snapshot.get("in_flight") if isinstance(snapshot, Mapping) else {}
    inflight_value = in_flight.get(candidate.route) if isinstance(in_flight, Mapping) else None

    completed = scheduler.get("completed_input_bytes", record.get("completed_input_bytes"))
    reserved = scheduler.get("active_reserved_input_bytes", record.get("active_reserved_input_bytes"))
    remaining = scheduler.get("quota_remaining_pct", record.get("remaining_pct"))
    stale = scheduler.get("quota_stale")
    if stale is None and isinstance(diagnostics, Mapping):
        stale = diagnostics.get("stale")
    circuit_open = bool(
        scheduler.get("circuit_open", record.get("circuit_open", runtime.get("circuit_open", False)))
    )
    return RoutingMetrics(
        completed_input_bytes=(int(_number(completed)) if _number(completed) is not None else None),
        active_reserved_input_bytes=(int(_number(reserved)) if _number(reserved) is not None else None),
        quota_remaining_pct=_number(remaining),
        quota_fresh=not bool(stale),
        inflight=_integer(scheduler.get("inflight", inflight_value)),
        failures=_integer(scheduler.get("failures", runtime.get("error", record.get("failures", 0)))),
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


def selection_key(candidate: Any, *, snapshot: Mapping[str, object] | None, exact_head: str | None, policy_version: str) -> tuple[object, ...]:
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
    headroom_unknown = metrics.quota_remaining_pct is None
    capacity_evidence_rank = 2 if headroom_unknown else (0 if metrics.quota_fresh else 1)
    headroom = -(metrics.quota_remaining_pct or 0.0)
    return (
        capacity_evidence_rank,
        load_unknown,
        normalized_load,
        headroom,
        metrics.inflight,
        metrics.failures,
        stable_tie_break(exact_head=exact_head, policy_version=policy_version, candidate_name=candidate.name),
    )
