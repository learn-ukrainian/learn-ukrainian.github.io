"""Process-wide TTL cache and single-flight helpers shared by Monitor routers.

Keys are strings chosen by each caller and scoped per app context with
:func:`ctx_cache_scope`. The curriculum readers that used to live here are
product code in ``scripts.project_api.curriculum_state`` (Monitor split,
C-4687).
"""

from __future__ import annotations

# ==================== TTL CACHE ====================
#
# In-process cache shared across routers. Keys are strings chosen by
# each caller (conventionally prefixed with the router/feature name,
# e.g. "orient_git", "summary"). Values are whatever the caller wants
# to cache. TTL is measured in seconds.
#
# Timestamps use ``time.monotonic()`` so TTL is resilient to wall-clock
# jumps (NTP sync, DST, manual clock edits) — see GH #1309 reviewer
# BLOCKER. Monotonic values are only valid within this process; the
# dict is in-memory anyway, so restart clears it naturally.
#
# The clock is a module-level seam so tests can advance cache time
# explicitly and wait on completion signals instead of asserting
# wall-clock staleness budgets on loaded CI runners (#8583).
import asyncio
import concurrent.futures
import logging
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .monitor_context import MonitorContext

_ttl_cache: dict[str, tuple[float, object]] = {}
_ttl_cache_lock = threading.Lock()
# prefix -> the only key still allowed to publish under that prefix.
_retained: dict[str, str] = {}
_inflight_futures: dict[str, concurrent.futures.Future] = {}
_inflight_lock = threading.Lock()
_ttl_clock: Callable[[], float] = time.monotonic

T = TypeVar("T")


def ctx_cache_scope(ctx: MonitorContext | None) -> str:
    """Cache-key / single-slot scope for one app context (#7494).

    Two app instances with different roots must never share TTL entries or
    thrash each other's last-good slots. Empty string when ``ctx`` is absent
    (plain-Python callers that have not resolved a context yet).
    """
    if ctx is None:
        return ""
    return f"@{ctx.roots.project_root}"


def ctx_scoped_ttl_key(ctx: MonitorContext, *parts: object) -> str:
    """Canonical ctx-scoped TTL-cache key: ``<resolved project root>:<parts...>`` (#7494).

    Single source of truth for the key format so a writer in one router
    (e.g. the state router's summary endpoint) and a reader in another
    (e.g. the dashboard overview) always address the same entry within one
    app context, while two app instances with different roots stay isolated.
    """
    root = str(ctx.roots.project_root.resolve())
    return ":".join((root, *(str(p) for p in parts)))


def cache_get(key: str, ttl: float) -> object | None:
    """Return cached value if still within TTL, else None."""
    now = _ttl_clock()
    with _ttl_cache_lock:
        entry = _ttl_cache.get(key)
    if entry and (now - entry[0]) < ttl:
        return entry[1]
    return None


def cache_get_with_age(key: str, ttl: float) -> tuple[object, float] | None:
    """Return cached value and age if still within TTL, else None."""
    now = _ttl_clock()
    with _ttl_cache_lock:
        entry = _ttl_cache.get(key)
    if entry is None:
        return None
    age = now - entry[0]
    if age < ttl:
        return entry[1], age
    return None


def _generation_superseded(key: str) -> bool:
    """True when a newer generation has replaced this key under its prefix."""
    return any(key.startswith(prefix) and key != current for prefix, current in _retained.items())


def cache_set(key: str, value: object) -> None:
    """Store a value in the TTL cache.

    A generation that ``cache_retain`` already replaced does not publish again.
    """
    now = _ttl_clock()
    with _ttl_cache_lock:
        if _generation_superseded(key):
            return
        _ttl_cache[key] = (now, value)


def cache_get_or_compute(  # noqa: UP047 — ruff pyflakes lacks PEP 695 type-param support here
    key: str,
    ttl: float,
    compute: Callable[[], T],
    *,
    force: bool = False,
) -> T:
    """Return a TTL-cached value, coalescing concurrent misses into one compute.

    Used for expensive curriculum walks (``weak-points``, ``pipeline-versions``)
    so a stampede of cold GETs cannot multiply a ~2k-module scan (#7973).
    ``force=True`` bypasses a warm entry (``?fresh=true``) but still coalesces
    concurrent forced recomputes onto a single flight for the same key.
    """
    if not force:
        cached = cache_get(key, ttl)
        if cached is not None:
            return cached  # type: ignore[return-value]

    fut, leader, cached = _claim_flight(key, ttl, force=force)
    if cached is not None:
        return cached  # type: ignore[return-value]
    assert fut is not None
    if not leader:
        return fut.result(timeout=180)
    return _finish_flight(key, fut, compute)


def cache_get_stored(key: str) -> tuple[object, float] | None:
    """Return a stored value and how long it has been stored, ignoring TTL."""
    now = _ttl_clock()
    with _ttl_cache_lock:
        entry = _ttl_cache.get(key)
    if entry is None:
        return None
    return entry[1], now - entry[0]


def cache_retain(prefix: str, key: str) -> int:
    """Drop every other entry under ``prefix`` so a new generation replaces the old one.

    Later ``cache_set`` calls for a replaced key are ignored, including a compute
    that was already in flight when the generation changed.
    """
    if not prefix:
        return 0
    with _ttl_cache_lock:
        _retained[prefix] = key
        stale = [item for item in _ttl_cache if item.startswith(prefix) and item != key]
        for item in stale:
            _ttl_cache.pop(item, None)
        return len(stale)


_lead_tasks: set[asyncio.Task] = set()
_refresh_keys: set[str] = set()
_refresh_keys_lock = threading.Lock()
_cache_log = logging.getLogger("state_helpers")


def _claim_flight(key: str, ttl: float, *, force: bool) -> tuple[concurrent.futures.Future | None, bool, object | None]:
    """Claim the single in-flight compute shared by sync and async callers.

    Returns ``(future, is_leader, cached)``. A cached hit has no future.
    A finished flight is not reused, so a later caller can start the next one.
    """
    with _inflight_lock:
        if not force:
            cached = cache_get(key, ttl)
            if cached is not None:
                return None, False, cached
        fut = _inflight_futures.get(key)
        if fut is None or fut.done():
            fut = concurrent.futures.Future()
            _inflight_futures[key] = fut
            return fut, True, None
        return fut, False, None


def _finish_flight(  # noqa: UP047 — ruff pyflakes lacks PEP 695 type-param support here
    key: str,
    fut: concurrent.futures.Future,
    compute: Callable[[], T],
) -> T:
    """Run compute on the caller's thread and publish one result for every waiter."""
    try:
        value = compute()
        cache_set(key, value)
        if not fut.done():
            fut.set_result(value)
        return value
    except BaseException as exc:
        if not fut.done():
            fut.set_exception(exc)
        raise
    finally:
        with _inflight_lock:
            if _inflight_futures.get(key) is fut:
                _inflight_futures.pop(key, None)


async def cache_get_or_compute_async(  # noqa: UP047 — ruff pyflakes lacks PEP 695 type-param support here
    key: str,
    ttl: float,
    compute: Callable[[], T],
    *,
    force: bool = False,
) -> T:
    """TTL read that stays on the event loop when the value is already warm.

    A miss starts one worker thread. Sync warmup and other requests for the
    same key wait on that same flight, so an older compute cannot overwrite a
    newer one. Cancelling one waiter does not cancel the shared result.
    """
    if not force:
        cached = cache_get(key, ttl)
        if cached is not None:
            return cached  # type: ignore[return-value]

    fut, leader, cached = _claim_flight(key, ttl, force=force)
    if cached is not None:
        return cached  # type: ignore[return-value]
    assert fut is not None

    if leader:

        async def _lead() -> None:
            try:
                value = await asyncio.to_thread(compute)
                cache_set(key, value)
                if not fut.done():
                    fut.set_result(value)
            except Exception as exc:
                if not fut.done():
                    fut.set_exception(exc)
            finally:
                with _inflight_lock:
                    if _inflight_futures.get(key) is fut:
                        _inflight_futures.pop(key, None)

        task = asyncio.create_task(_lead())
        _lead_tasks.add(task)
        task.add_done_callback(_lead_tasks.discard)

    # shield: cancelling this waiter must not cancel the shared future.
    return await asyncio.shield(asyncio.wrap_future(fut))


def schedule_cache_refresh(
    key: str, ttl: float, compute: Callable[[], object], *, should_refresh: Callable[[], bool] | None = None,
) -> None:
    """Check and recompute off-loop, sharing one flight without renewing unchanged data."""

    def _run() -> None:
        try:
            if should_refresh is None or should_refresh():
                cache_get_or_compute(key, ttl, compute, force=True)
        except Exception:
            _cache_log.debug("background cache refresh failed", exc_info=True)
        finally:
            with _refresh_keys_lock:
                _refresh_keys.discard(key)

    with _refresh_keys_lock:
        if key in _refresh_keys:
            return
        _refresh_keys.add(key)
    threading.Thread(target=_run, name="status-cache-refresh", daemon=True).start()


def cache_invalidate(prefix: str = "") -> int:
    """Drop every cache entry whose key starts with ``prefix``.

    With ``prefix=""`` (default) the whole cache is cleared. Returns
    the number of entries removed. Useful for ``?fresh=true`` bypass
    paths and for tests that want a clean slate between cases.
    """
    with _ttl_cache_lock:
        keys = [k for k in _ttl_cache if k.startswith(prefix)]
        for key in keys:
            _ttl_cache.pop(key, None)
        if prefix == "":
            _retained.clear()
        else:
            dropped = [
                item
                for item, current in _retained.items()
                if item.startswith(prefix) or current.startswith(prefix)
            ]
            for item in dropped:
                _retained.pop(item, None)
        return len(keys)
