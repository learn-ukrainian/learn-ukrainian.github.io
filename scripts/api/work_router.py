"""Work control-plane public API — read-only foundation.

Mounted at ``/api/work`` with versioned routes under ``/v1/*``.
Never proxies private adapters or mutates GitHub / dispatch state.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from scripts.api.state_helpers import cache_get_with_age, cache_invalidate, cache_set
from scripts.work.normalize import build_public_projection
from scripts.work.schema import (
    SchemaValidationError,
    parse_saved_view_params,
    schema_digest_sha256,
    validate_projection,
)
from scripts.work.sources_public import private_capability_seam, public_repository_id

router = APIRouter(tags=["work"])

CACHE_KEY = "work:v1:projection"
CACHE_TTL_S = 30.0
WARM_TARGET_S = 2.0
TIMEOUT_S = 5.0


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
    """Permanent warm-cache key for a canonical filter dict.

    Callers must pass already-canonicalized multivalue filters (see
    ``parse_saved_view_params``) so equivalent query forms collide.
    """
    return f"{CACHE_KEY}:{sorted(filters.items())!r}"


def _build_sync(filters: dict[str, Any], *, cache_age_s: float = 0.0) -> dict[str, Any]:
    payload = build_public_projection(filters=filters or None, cache_age_s=cache_age_s)
    return validate_projection(payload)


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

    started = time.monotonic()
    try:
        payload = await asyncio.wait_for(
            asyncio.to_thread(_build_sync, filters, cache_age_s=0.0),
            timeout=TIMEOUT_S,
        )
    except TimeoutError as exc:
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

    _ = time.monotonic() - started  # elapsed retained for future metrics only
    payload["cache_age_s"] = 0.0
    cache_set(key, payload)
    return payload


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
        "saved_view_keys": sorted(
            {"health", "kind", "lifecycle", "orphan", "repository_id", "source_id"}
        ),
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
