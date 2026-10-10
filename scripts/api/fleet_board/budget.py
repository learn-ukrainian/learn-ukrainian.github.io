"""Per-subscription budget projection over the existing routing-budget compute.

The fleet route does not change ``/api/state/routing-budget``. It calls the
same compute function, keeps the result for a short time, and stops waiting
after ``BUDGET_DEADLINE_S``. A slow refresh serves the previous result with
source status ``stale`` and its age. Missing percentages stay null.
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .. import state_router
from ..monitor_context import MonitorContext
from ..subscription_usage import _parse_resets_at_any, compute_usage_pace
from .envelope import utc_timestamp
from .sources import SourceReport, report

SOURCE_NAME = "routing_budget"
BUDGET_TTL_S = 15.0
BUDGET_DEADLINE_S = 2.0


@dataclass(frozen=True)
class _Entry:
    stored_at: float
    payload: dict[str, Any]


_lock = threading.Lock()
_entries: dict[str, _Entry] = {}
_flights: dict[str, Future[dict[str, Any]]] = {}
_generation = 0
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="fleet-board-budget")


def _now() -> datetime:
    return datetime.now(UTC)


def _cache_key(ctx: MonitorContext) -> str:
    return str(ctx.roots.project_root.resolve())


def clear_cache() -> None:
    """Drop cached budgets and ignore refreshes already in flight."""
    global _generation
    with _lock:
        _generation += 1
        _entries.clear()
        _flights.clear()


def prime(ctx: MonitorContext, payload: dict[str, Any], *, age_s: float) -> None:
    """Store a budget as if it had been computed ``age_s`` seconds ago."""
    with _lock:
        _entries[_cache_key(ctx)] = _Entry(time.monotonic() - age_s, payload)


def _number(raw: Any) -> float | None:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if not math.isfinite(value):
        return None
    return value


def _timestamp(raw: Any) -> str | None:
    """Normalize a supported reset instant to whole-second UTC."""
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
        return None
    parsed = _parse_resets_at_any(raw)
    if parsed is None:
        return None
    return utc_timestamp(parsed)


def unknown_budget() -> dict[str, Any]:
    return {
        "subscriptions": [
            {
                "subscription": lane,
                "used_pct": None,
                "elapsed_pct": None,
                "pace": None,
                "reset_at": None,
                "recommendation": None,
            }
            for lane in state_router.SUBSCRIPTION_LANES
        ]
    }


def _pace_reading(used: float | None, reset_at: str | None, now: datetime) -> dict[str, Any] | None:
    if reset_at is None:
        return None
    sample = 0.0 if used is None else used
    try:
        reading = compute_usage_pace(sample, reset_at, now=now)
    except Exception:
        return None
    if not isinstance(reading, dict):
        return None
    return reading


def _subscription(lane: str, info: Mapping[str, Any], *, now: datetime) -> dict[str, Any]:
    codexbar = info.get("codexbar")
    if not isinstance(codexbar, Mapping):
        codexbar = {}
    used = _number(codexbar.get("weekly_used_pct"))
    if used is None:
        used = _number(info.get("burn_pct_7d"))
    reset_at = _timestamp(codexbar.get("weekly_resets_at")) or _timestamp(info.get("resets_at"))
    reading = _pace_reading(used, reset_at, now)
    elapsed = _number(reading.get("expected_pct")) if reading is not None else None
    if elapsed is None:
        elapsed = _number(codexbar.get("weekly_expected_pct"))
    pace: str | None = None
    if used is not None and reading is not None:
        stage = reading.get("stage")
        if isinstance(stage, str) and stage.strip():
            pace = stage
    status = info.get("status")
    recommendation = status.strip() if isinstance(status, str) and status.strip() else None
    return {
        "subscription": lane,
        "used_pct": used,
        "elapsed_pct": elapsed,
        "pace": pace,
        "reset_at": reset_at,
        "recommendation": recommendation,
    }


def project_budget(raw: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """One row per subscription lane. Unknown measurements are null."""
    moment = now or _now()
    agents = raw.get("agents")
    if not isinstance(agents, Mapping):
        agents = {}
    rows: list[dict[str, Any]] = []
    for lane in state_router.SUBSCRIPTION_LANES:
        info = agents.get(lane)
        rows.append(_subscription(lane, info if isinstance(info, Mapping) else {}, now=moment))
    return {"subscriptions": rows}


def _invoke(ctx: MonitorContext) -> dict[str, Any]:
    roots = ctx.roots
    payload = state_router.compute_routing_budget(
        transport="dispatch",
        fresh_codexbar=False,
        refresh_requested=False,
        budget_config_path=roots.project_root / "scripts" / "config" / "agent_budgets.yaml",
        tasks_dir=roots.batch_state_dir / "tasks",
        project_root=roots.project_root,
        curriculum_root=roots.curriculum_root,
        batch_state_dir=roots.batch_state_dir,
    )
    if not isinstance(payload, dict):
        raise TypeError
    return payload


def _fresh(key: str, moment: float) -> tuple[_Entry, float] | None:
    entry = _entries.get(key)
    if entry is None:
        return None
    age = moment - entry.stored_at
    if age < BUDGET_TTL_S:
        return entry, max(0.0, age)
    return None


def _expired(key: str) -> tuple[dict[str, Any], float] | None:
    with _lock:
        entry = _entries.get(key)
    if entry is None:
        return None
    return entry.payload, max(0.0, time.monotonic() - entry.stored_at)


def _remember_result(key: str, flight: Future[dict[str, Any]], generation: int) -> None:
    """Store a finished refresh unless a newer cache generation has taken over."""
    try:
        payload = flight.result(timeout=0)
    except Exception:
        payload = None
    with _lock:
        if _generation != generation:
            return
        if isinstance(payload, dict):
            _entries[key] = _Entry(time.monotonic(), payload)
        if _flights.get(key) is flight:
            _flights.pop(key, None)


def _stale_payload(key: str) -> tuple[dict[str, Any] | None, str, float | None]:
    expired = _expired(key)
    if expired is None:
        return None, "unavailable", None
    cached, age = expired
    return cached, "stale", age


def _read_cached_or_compute(
    key: str,
    compute: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any] | None, str, float | None]:
    started = time.monotonic()
    with _lock:
        generation = _generation
        fresh = _fresh(key, started)
        if fresh is not None:
            entry, age = fresh
            return entry.payload, "ok", age
        flight = _flights.get(key)
        if flight is None:
            flight = _executor.submit(compute)
            _flights[key] = flight
            attached = False
        else:
            attached = True
    if not attached:
        flight.add_done_callback(lambda done, key=key, generation=generation: _remember_result(key, done, generation))
    remaining = max(0.0, BUDGET_DEADLINE_S - (time.monotonic() - started))
    try:
        payload = flight.result(timeout=remaining)
    except TimeoutError:
        return _stale_payload(key)
    except Exception:
        return _stale_payload(key)
    if not isinstance(payload, dict):
        return _stale_payload(key)
    with _lock:
        if _generation == generation:
            _entries[key] = _Entry(time.monotonic(), payload)
    return payload, "ok", 0.0


def _source_status(payload: Mapping[str, Any], cache_status: str, cache_age: float | None) -> tuple[str, float | None]:
    if cache_status == "stale":
        return "stale", 0.0 if cache_age is None else cache_age
    diagnostics = payload.get("diagnostics")
    if isinstance(diagnostics, Mapping) and diagnostics.get("stale") is True:
        age = _number(diagnostics.get("data_age_s"))
        if age is None or age < 0:
            age = 0.0 if cache_age is None else cache_age
        return "stale", age
    return "ok", 0.0 if cache_age is None else cache_age


def load_budget(ctx: MonitorContext, *, now: datetime | None = None) -> tuple[dict[str, Any], SourceReport]:
    """Return the projected budget and its source row. Never raises."""
    moment = now or _now()
    try:
        payload, cache_status, cache_age = _read_cached_or_compute(_cache_key(ctx), lambda: _invoke(ctx))
    except Exception:
        payload, cache_status, cache_age = None, "unavailable", None
    if payload is None:
        return unknown_budget(), report(SOURCE_NAME, "unavailable")
    try:
        data = project_budget(payload, now=moment)
    except Exception:
        return unknown_budget(), report(SOURCE_NAME, "unavailable")
    status, age = _source_status(payload, cache_status, cache_age)
    return data, report(SOURCE_NAME, status, age_s=age)
