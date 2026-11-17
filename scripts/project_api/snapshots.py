"""Stale-while-revalidate snapshots for the product routes whose scans take seconds.

A curriculum walk, a wiki registry scan or a git history search can take longer
than a request may wait. Such a route serves the stored result at once with its
true age (``X-Snapshot-Age-S``, measured from when the scan started reading) and
lets one background flight replace it once it is older than the route's TTL.
The flights are the machinery single-flight cache
(``lu_machinery.api.state_helpers``), so concurrent readers and the startup
warmup share one scan per key.

A request waits for a scan only when nothing usable is stored: a cold key, a
forced ``?fresh=true`` read, or a key whose last scan failed (a failing refresh
never hides behind old data: the next reader gets the error). That wait is bounded by
``COLD_WAIT_S``; past it the route answers a typed 503 with ``Retry-After``
while the scan keeps running and stores its result. A scan that raises reaches
the route unchanged, so each route keeps its own error mapping.

Example:
  .venv/bin/python -c "from scripts.project_api import snapshots; print(snapshots.COLD_WAIT_S)"
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import HTTPException, Response
from lu_machinery.api.monitor_context import MonitorContext
from lu_machinery.api.state_helpers import (
    cache_get_or_compute,
    cache_get_or_compute_async,
    cache_get_stored,
    ctx_scoped_ttl_key,
    schedule_cache_refresh,
)

# Below the Monitor's 10-second request timeout, so a cold read answers a typed
# 503 instead of being cut off with a 504.
COLD_WAIT_S = 5.0
AGE_HEADER = "X-Snapshot-Age-S"
RETRY_AFTER_S = 5

CacheState = Literal["hit", "stale", "miss"]

_log = logging.getLogger("project_api.snapshots")
# Monotonic clock for snapshot ages; a module seam so tests can set the time.
_clock: Callable[[], float] = time.monotonic
# Keys whose most recent scan raised. Their stored value is not served again
# until a scan succeeds.
_failed_keys: set[str] = set()
_failed_lock = threading.Lock()


@dataclass(frozen=True)
class Snapshot:
    """One stored scan result and the moment the scan started reading its sources."""

    value: Any
    started: float
    generated_at: str

    @property
    def age_s(self) -> float:
        return max(0.0, _clock() - self.started)


def _stamped(key: str, compute: Callable[[], Any]) -> Callable[[], Snapshot]:
    def run() -> Snapshot:
        started = _clock()
        generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        try:
            value = compute()
        except BaseException:
            with _failed_lock:
                _failed_keys.add(key)
            raise
        with _failed_lock:
            _failed_keys.discard(key)
        return Snapshot(value, started, generated_at)

    return run


def _last_scan_failed(key: str) -> bool:
    with _failed_lock:
        return key in _failed_keys


def snapshot_key(ctx: MonitorContext, name: str, *params: object) -> str:
    """The cache key of one route snapshot, scoped to the app context."""
    return ctx_scoped_ttl_key(ctx, "snapshot", name, *params)


async def read_snapshot(
    ctx: MonitorContext,
    name: str,
    params: tuple[object, ...],
    ttl: float,
    compute: Callable[[], Any],
    *,
    force: bool = False,
) -> tuple[Snapshot, CacheState]:
    """Return the snapshot for ``name``/``params`` and whether it was a hit, stale or new.

    A value older than ``ttl`` is still served (with its age) while one
    background scan replaces it, unless the last scan failed. Never blocks the event loop: a stored value is
    returned directly, and a scan runs on a worker thread.
    """
    key = snapshot_key(ctx, name, *params)
    stamped = _stamped(key, compute)
    stored = None if force else cache_get_stored(key)
    if stored is not None:
        held, stored_age = stored
        if not isinstance(held, Snapshot):
            raise TypeError(f"snapshot key {name!r} holds a {type(held).__name__}")
        if not _last_scan_failed(key):
            if stored_age < ttl:
                return held, "hit"
            schedule_cache_refresh(key, ttl, stamped)
            return held, "stale"
        force = True
    try:
        snapshot: Snapshot = await asyncio.wait_for(
            cache_get_or_compute_async(key, ttl, stamped, force=force), timeout=COLD_WAIT_S
        )
    except TimeoutError:
        raise HTTPException(
            status_code=503,
            detail={"code": "SNAPSHOT_WARMING", "snapshot": name, "retry_after_s": RETRY_AFTER_S},
            headers={"Retry-After": str(RETRY_AFTER_S), "Cache-Control": "no-store"},
        ) from None
    return snapshot, "miss"


def prime_snapshot(
    ctx: MonitorContext, name: str, params: tuple[object, ...], ttl: float, compute: Callable[[], Any]
) -> None:
    """Fill one snapshot from the startup warmup thread; a failure is logged, not raised.

    The warmup runs every hook in order on one thread, so one failing scan must
    not leave the later snapshots cold.
    """
    key = snapshot_key(ctx, name, *params)
    try:
        cache_get_or_compute(key, ttl, _stamped(key, compute))
    except Exception as exc:
        _log.warning("Snapshot warmup failed for %s: %s", name, exc)


def stamp_age(response: Response, snapshot: Snapshot) -> None:
    """Expose the snapshot's true age on the response."""
    response.headers[AGE_HEADER] = f"{snapshot.age_s:.3f}"
