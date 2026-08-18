"""Work control-plane public API — read-only foundation.

Mounted at ``/api/work`` with versioned routes under ``/v1/*``.
Never proxies private adapters or mutates GitHub / dispatch state.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from scripts.api.state_helpers import cache_get, cache_get_with_age, cache_invalidate, cache_set
from scripts.orchestration.fleet_taxonomy import FleetTaxonomyError, resolve_area
from scripts.orchestration.issue_stream_audit import load_registry
from scripts.work.attention import is_actionable
from scripts.work.normalize import build_public_projection
from scripts.work.schema import (
    SchemaValidationError,
    admit_projection_filters,
    parse_saved_view_params,
    schema_digest_sha256,
    validate_projection,
)
from scripts.work.sources_public import private_capability_seam, public_repository_id

log = logging.getLogger(__name__)

router = APIRouter(tags=["work"])

CACHE_KEY = "work:v1:projection"
CACHE_TTL_S = 30.0
WARM_TARGET_S = 2.0
TIMEOUT_S = 5.0

NEXT_DEFAULT_LIMIT = 7
NEXT_MAX_LIMIT = 25
NEXT_RETRY_AFTER_S = 3.0
NEXT_TOP_BLOCKERS = 3
# Bound stale-serve for /next: expired cache may be returned while a
# single-flight refresh runs, but never past this age (residual #3 / #6890).
NEXT_MAX_STALE_S = 300.0
# Bound one background build (#6984): the single-flight slot must always free
# again even when a section collector hangs, or every later /next caller sees
# 503 stale forever. Well above the per-section timeouts in sources_public.
NEXT_BUILD_TIMEOUT_S = 20.0
STREAM_REGISTRY_CACHE_KEY = "work:v1:stream-registry"
STREAM_REGISTRY_TTL_S = 60.0


def _next_error(
    status_code: int,
    body: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Return a /next error body without FastAPI ``{"detail": ...}`` wrapping.

    Machine consumers parse the documented inner object on the wire (#6890 #6).
    """
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _filters_from_request(request: Request) -> dict[str, Any]:
    raw: dict[str, list[str] | str | None] = {}
    for key in ("health", "kind", "lifecycle", "orphan", "repository_id", "source_id"):
        values = request.query_params.getlist(key)
        if not values:
            continue
        raw[key] = values if len(values) > 1 else values[0]
    # Reject known-private / free-text keys early with a clear 400.
    forbidden = {
        k
        for k in request.query_params
        if k
        not in {
            "health",
            "kind",
            "lifecycle",
            "orphan",
            "repository_id",
            "source_id",
            "fresh",
        }
    }
    if forbidden:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_saved_view",
                "message": f"unsupported filter keys: {sorted(forbidden)}",
            },
        )
    try:
        return parse_saved_view_params(raw)
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_saved_view", "message": str(exc)},
        ) from exc


def projection_cache_key(filters: dict[str, Any]) -> str:
    """Permanent warm-cache key for a validated, canonical filter dict.

    Self-validates via the shared projection filter admission gate so direct
    callers cannot mint keys for unknown filters or foreign ``repository_id``
    values. Reordered/duplicate multivalues within the finite raw bound collapse
    to one permanent key. The key string is built once from the canonical dict
    (no double-encoding).
    """
    canonical = admit_projection_filters(filters or {})
    return f"{CACHE_KEY}:{sorted(canonical.items())!r}"


def _build_sync(filters: dict[str, Any], *, cache_age_s: float = 0.0) -> dict[str, Any]:
    payload = build_public_projection(filters=filters or None, cache_age_s=cache_age_s)
    return validate_projection(payload)


_IN_FLIGHT_BUILDS: dict[str, asyncio.Task[dict[str, Any]]] = {}


async def _run_build_job(key: str, filters: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = await asyncio.wait_for(
            asyncio.to_thread(_build_sync, filters, cache_age_s=0.0),
            timeout=NEXT_BUILD_TIMEOUT_S,
        )
        payload["cache_age_s"] = 0.0
        cache_set(key, payload)
        return payload
    finally:
        _IN_FLIGHT_BUILDS.pop(key, None)


def _consume_build_failure(task: asyncio.Task[dict[str, Any]]) -> None:
    """Log (and thereby retrieve) fire-and-forget build failures.

    Without this, a refresh kicked by /next that raises is dropped silently
    and the cache just keeps aging toward the 503 stale cliff (#6984).
    """
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        log.warning("work projection background build failed: %s: %s", type(exc).__name__, exc)


def _get_or_create_build_task(key: str, filters: dict[str, Any]) -> asyncio.Task[dict[str, Any]]:
    task = _IN_FLIGHT_BUILDS.get(key)
    if task is None or task.done():
        task = asyncio.create_task(_run_build_job(key, filters))
        task.add_done_callback(_consume_build_failure)
        _IN_FLIGHT_BUILDS[key] = task
    return task


def warm_projection_cache(
    filters: dict[str, Any] | None = None,
) -> asyncio.Task[dict[str, Any]] | None:
    """Schedule asynchronous background warm-up of the public projection cache."""
    canonical = admit_projection_filters(filters or {})
    key = projection_cache_key(canonical)
    cached = cache_get_with_age(key, CACHE_TTL_S)
    if cached is not None:
        return None
    try:
        _ = asyncio.get_running_loop()
    except RuntimeError:
        return None
    return _get_or_create_build_task(key, canonical)


@router.get("/v1/projection")
async def work_projection(
    request: Request,
    fresh: bool = Query(False, description="Bypass warm projection cache."),
) -> dict[str, Any]:
    """Normalized public attention list with source envelopes and degradation."""
    filters = _filters_from_request(request)
    key = projection_cache_key(filters)

    if not fresh:
        cached = cache_get_with_age(key, CACHE_TTL_S)
        if cached is not None:
            payload, age = cached
            if isinstance(payload, dict):
                # Return a shallow copy with updated cache_age_s.
                out = dict(payload)
                out["cache_age_s"] = float(age)
                return out

    if fresh:
        cache_invalidate(CACHE_KEY)

    task = _get_or_create_build_task(key, filters)
    try:
        payload = await asyncio.wait_for(asyncio.shield(task), timeout=TIMEOUT_S)
    except TimeoutError as exc:
        stale = cache_get_with_age(key, float("inf"))
        if stale is not None and isinstance(stale[0], dict):
            out = dict(stale[0])
            out["cache_age_s"] = float(stale[1])
            return out
        # Typed degradation envelope — never a bare 500 hide of healthy sources.
        raise HTTPException(
            status_code=504,
            detail={
                "error": "work_projection_timeout",
                "message": f"projection exceeded {TIMEOUT_S}s budget",
                "budget": {"warm_target_s": WARM_TARGET_S, "timeout_s": TIMEOUT_S},
                "capabilities": {
                    "mutation": False,
                    "private_source": private_capability_seam(),
                },
                "foundation_status": "FOUNDATION_COMPLETE",
            },
        ) from exc
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "work_projection_invalid", "message": str(exc)},
        ) from exc

    out = dict(payload)
    return out


def _known_streams() -> list[str] | None:
    """Registry stream keys with a small TTL cache; None when unreadable (fail closed)."""
    cached = cache_get(STREAM_REGISTRY_CACHE_KEY, STREAM_REGISTRY_TTL_S)
    if isinstance(cached, list):
        return cached
    try:
        names = sorted(load_registry().keys())
    except Exception:
        return None
    cache_set(STREAM_REGISTRY_CACHE_KEY, names)
    return names


def _item_streams(item: dict[str, Any]) -> list[str]:
    streams = ((item.get("projections") or {}).get("stream") or {}).get("streams")
    if not isinstance(streams, list):
        return []
    return [s for s in streams if isinstance(s, str) and s]


def _resolve_stream_alias(stream: str, known: list[str]) -> str | None:
    """Resolve an area/alias name (e.g. SESSION_EPIC ``infra``) to one stream.

    Uses the fleet taxonomy (scripts/config/fleet_taxonomy.yaml), the same
    resolver the session hooks use. Only an unambiguous mapping — exactly one
    known stream among the area's id + aliases — aliases; anything else
    returns None so the caller fails closed with 400 unknown_stream (#6984).
    """
    try:
        area = resolve_area(stream)
    except FleetTaxonomyError:
        return None
    candidates = [name for name in (area.id, *area.aliases) if name in known]
    return candidates[0] if len(candidates) == 1 else None


def _next_rank_key(item: dict[str, Any]) -> tuple[int, str]:
    return (int(item.get("attention_rank") or 0), str(item.get("work_id") or ""))


@router.get("/v1/next", response_model=None)
async def work_next(
    stream: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="Stream key from scripts/config/issue_streams.yaml (the caller's lane epic).",
    ),
    limit: int = Query(NEXT_DEFAULT_LIMIT, ge=1, le=NEXT_MAX_LIMIT),
) -> dict[str, Any] | JSONResponse:
    """Stream-scoped actionable pick list served strictly from the warm cache (#6880).

    Never builds a cold projection: absent cache → 503 ``building`` with
    ``retry_after_s``. A present-but-expired cache is served as-is (honest
    ``cache_age_s``) while the shared single-flight refresh runs in the
    background so /next-only pollers converge without ever blocking — until
    age exceeds ``NEXT_MAX_STALE_S``, which fails closed with 503 ``stale``.
    The background build itself is bounded by ``NEXT_BUILD_TIMEOUT_S`` so a
    hung collector frees the single-flight slot instead of wedging every
    later caller at 503 stale (#6984). ``stream`` also accepts unambiguous
    fleet-taxonomy area aliases (``infra`` → ``infra-harness``); an
    unreadable stream registry fails closed with 503 ``registry_unavailable``
    rather than treating typos as an empty queue (#6890).
    """
    known = _known_streams()
    if known is None:
        return _next_error(
            503,
            {
                "error": "registry_unavailable",
                "message": "issue stream registry is unreadable; refusing to serve /next",
                "retry_after_s": NEXT_RETRY_AFTER_S,
            },
            headers={"Retry-After": str(int(NEXT_RETRY_AFTER_S))},
        )
    requested_stream = stream
    if stream not in known:
        aliased = _resolve_stream_alias(stream, known)
        if aliased is not None:
            stream = aliased
    if stream not in known:
        return _next_error(
            400,
            {
                "error": "unknown_stream",
                "message": f"unknown stream {requested_stream!r}",
                "valid_streams": known,
            },
        )

    key = projection_cache_key({})
    cached = cache_get_with_age(key, float("inf"))
    if cached is None or not isinstance(cached[0], dict):
        return _next_error(
            503,
            {
                "error": "building",
                "message": "work projection cache is cold; retry shortly",
                "retry_after_s": NEXT_RETRY_AFTER_S,
            },
            headers={"Retry-After": str(int(NEXT_RETRY_AFTER_S))},
        )
    payload, age = cached
    if age >= NEXT_MAX_STALE_S:
        _get_or_create_build_task(key, {})
        return _next_error(
            503,
            {
                "error": "stale",
                "message": (f"work projection cache age {age:.0f}s exceeds max stale {NEXT_MAX_STALE_S:.0f}s"),
                "cache_age_s": float(age),
                "max_stale_s": NEXT_MAX_STALE_S,
                "retry_after_s": NEXT_RETRY_AFTER_S,
            },
            headers={"Retry-After": str(int(NEXT_RETRY_AFTER_S))},
        )
    if age >= CACHE_TTL_S:
        _get_or_create_build_task(key, {})

    items = [i for i in payload.get("items") or [] if isinstance(i, dict)]
    actionable = [i for i in items if is_actionable(i)]

    scoped = sorted((i for i in actionable if stream in _item_streams(i)), key=_next_rank_key)
    queue = [
        {
            "work_id": i.get("work_id"),
            "resource_kind": i.get("resource_kind"),
            "remote_id": i.get("remote_id"),
            "title": i.get("title") or "",
            "health": i.get("health"),
            "safe_next_action": i.get("safe_next_action") or {},
            "attention_rank": i.get("attention_rank"),
            "url": (i.get("urls") or {}).get("html"),
        }
        for i in scoped[:limit]
    ]

    counts: dict[str, int] = {name: 0 for name in known if name != stream}
    unscoped = 0
    for i in actionable:
        streams_of = _item_streams(i)
        if not streams_of:
            unscoped += 1
            continue
        for name in streams_of:
            if name != stream:
                counts[name] = counts.get(name, 0) + 1

    top_blockers = [
        {
            "work_id": i.get("work_id"),
            "resource_kind": i.get("resource_kind"),
            "title": i.get("title") or "",
            "health": i.get("health"),
            "action_code": str(((i.get("safe_next_action") or {}).get("code")) or ""),
            "streams": _item_streams(i),
        }
        for i in sorted(
            (i for i in actionable if i.get("health") == "OFF_TRACK"),
            key=_next_rank_key,
        )[:NEXT_TOP_BLOCKERS]
    ]

    # Honesty for the migration-pending lane (#6984): body-homed tickets whose
    # native sub-issue link is still pending are AT_RISK work the caller must
    # see either in the queue (when their body-derived membership includes
    # this stream) or named here with a reason — never only a silent bump of
    # unscoped_actionable_count.
    excluded_pending = [
        {
            "work_id": i.get("work_id"),
            "remote_id": i.get("remote_id"),
            "title": i.get("title") or "",
            "streams": _item_streams(i),
            "reason": ("no_stream_membership" if not _item_streams(i) else "scoped_to_other_stream"),
        }
        for i in sorted(
            (
                i
                for i in actionable
                if ((i.get("projections") or {}).get("stream") or {}).get("status") == "pending_native"
                and stream not in _item_streams(i)
            ),
            key=_next_rank_key,
        )
    ]

    body: dict[str, Any] = {
        "schema_version": "work-next.v1",
        "stream": stream,
        "generated_at": payload.get("generated_at"),
        "cache_age_s": float(age),
        "limit": limit,
        "queue": queue,
        "digest": {
            "other_streams": {
                "actionable_counts_by_stream": {k: counts[k] for k in sorted(counts)},
                "top_blockers": top_blockers,
            },
            "unscoped_actionable_count": unscoped,
            "excluded_pending_native": {
                "count": len(excluded_pending),
                "items": excluded_pending[:NEXT_MAX_LIMIT],
            },
        },
        "capabilities": {"mutation": False},
    }
    if requested_stream != stream:
        body["requested_stream"] = requested_stream
    return body


@router.get("/v1/capabilities")
async def work_capabilities() -> dict[str, Any]:
    """Public-safe capability + optional private-source seam metadata."""
    return {
        "schema_version": "work-projection.v1",
        "schema_digest_sha256": schema_digest_sha256(),
        "public_repository_id": public_repository_id(),
        "mutation": False,
        "foundation_status": "FOUNDATION_COMPLETE",
        "budget": {"warm_target_s": WARM_TARGET_S, "timeout_s": TIMEOUT_S},
        "class4_endpoints": [
            "GET /api/delegate/active",
            "GET /api/delegate/tasks?status=all&limit<=500",
            "GET /api/fleet/reviews",
        ],
        "github_enumerations_per_refresh": 2,
        "private_source": private_capability_seam(),
        "saved_view_keys": sorted({"health", "kind", "lifecycle", "orphan", "repository_id", "source_id"}),
        "next_queue": {
            "route": "GET /api/work/v1/next",
            "params": {
                "stream": (
                    "required — stream key from scripts/config/issue_streams.yaml; the pick list is scoped to it. "
                    "Unambiguous fleet-taxonomy area aliases (e.g. infra → infra-harness) are accepted (#6984)"
                ),
                "limit": f"optional int, default {NEXT_DEFAULT_LIMIT}, max {NEXT_MAX_LIMIT}",
            },
            "served_from": (
                "warm projection cache only; 503 building + retry_after_s when cold; "
                f"503 stale when cache_age_s ≥ {int(NEXT_MAX_STALE_S)}s; "
                f"background refresh bounded at {int(NEXT_BUILD_TIMEOUT_S)}s so the single-flight slot always frees; "
                "503 registry_unavailable when the stream registry is unreadable"
            ),
        },
    }


@router.get("/v1/health")
async def work_health() -> dict[str, Any]:
    """Cheap liveness for the Work surface itself (not curriculum health)."""
    return {
        "ok": True,
        "surface": "work",
        "schema_version": "work-projection.v1",
        "foundation_status": "FOUNDATION_COMPLETE",
        "mutation": False,
    }
