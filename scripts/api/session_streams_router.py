"""Sol PR-K: read-only Monitor surfaces for session streams + dual-write drift.

Exposes stream digest/status, dual-write inventory, and projection drift without
any cutover mutation. Operator cutovers remain explicit CLI/events.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from agents_extensions.shared.session_streams.dual_write import list_handoff_candidates
from agents_extensions.shared.session_streams.handoff import diagnose_handoff
from agents_extensions.shared.session_streams.model import entry_as_dict
from agents_extensions.shared.session_streams.projection import (
    detect_projection_drift,
    list_projection_receipts,
)
from agents_extensions.shared.session_streams.store import NotFoundError

from .monitor_context import MonitorContext, get_ctx
from .repository_authority import build_repository_identity

router = APIRouter(tags=["session-streams"])


def _store_health(ctx: MonitorContext) -> dict[str, Any]:
    """Return store reachability and migration versions without its path."""
    connection = None
    try:
        if ctx.stores.session_streams_database is None:
            return {"reachable": False, "schema_versions": []}
        connection = ctx.stores.session_streams_database.connect(read_only=True)
        versions = [
            int(row[0])
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        ]
        return {"reachable": True, "schema_versions": versions}
    except Exception:
        return {"reachable": False, "schema_versions": []}
    finally:
        if connection is not None:
            connection.close()


@router.get("/v1/health")
def session_streams_health(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    """Liveness for the session-streams monitor surface (no cutover)."""
    root = ctx.roots.live_repo_root
    return {
        "ok": True,
        "repo": build_repository_identity(root),
        "store": _store_health(ctx),
        "cutover": "operator-gated",
    }


@router.get("/v1/status/{stream_id:path}")
def session_stream_status(
    stream_id: str,
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
    """Handoff/lease diagnosis for one stream (read-only; no claim)."""
    if not stream_id.startswith("epic:"):
        raise HTTPException(status_code=400, detail="stream_id must look like epic:N")
    store = ctx.stores.session_streams_store
    if store is None:
        raise HTTPException(status_code=404, detail="session-stream database is unavailable")
    try:
        status = diagnose_handoff(store, stream_id)
    except (NotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail="status_failed") from exc
    return status.as_dict()


@router.get("/v1/digest/{stream_id:path}")
def session_stream_digest(
    stream_id: str,
    limit: int = Query(default=20, ge=0, le=500),
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
    """Pinned entries plus last N non-pinned entries (bounded)."""
    if not stream_id.startswith("epic:"):
        raise HTTPException(status_code=400, detail="stream_id must look like epic:N")
    store = ctx.stores.session_streams_store
    if store is None:
        raise HTTPException(status_code=404, detail="session-stream database is unavailable")
    try:
        digest = store.load_digest(stream_id, limit=limit)
    except (NotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="digest_failed") from exc
    return {
        "stream_id": stream_id,
        "limit": limit,
        "pinned": [entry_as_dict(e) for e in digest.pinned],
        "recent": [entry_as_dict(e) for e in digest.recent],
        "pinned_count": len(digest.pinned),
        "recent_count": len(digest.recent),
    }


@router.get("/v1/dual-write-status")
def dual_write_status(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    """Inventory-derived handoff dual-write paths and file existence (no cutover)."""
    root = ctx.roots.live_repo_root
    candidates = list_handoff_candidates(root)
    rows = [
        {
            "stream_id": c.stream_id,
            "stream_name": c.stream_name,
            "title": c.title,
            "exists": c.exists,
        }
        for c in candidates
    ]
    missing = sum(1 for r in rows if not r["exists"])
    return {
        "repo": build_repository_identity(root),
        "store": _store_health(ctx),
        "total": len(rows),
        "missing_files": missing,
        "candidates": rows,
        "cutover": "operator-gated",
    }


@router.get("/v1/drift")
def projection_drift(
    stream_id: str | None = Query(default=None, description="Optional epic:N filter"),
    dry_run: bool = Query(
        default=True,
        description="When true, classify only without writing new receipts when possible",
    ),
    ctx: MonitorContext = Depends(get_ctx),
) -> dict[str, Any]:
    """Projection drift surface for dual-write (PR-K).

    Default dry_run=true returns the latest receipt snapshot + dual-write
    missing-file count without forcing a full project rewrite. Set dry_run=false
    to run detect_projection_drift (records receipts; still no stream cutover).
    """
    root = ctx.roots.live_repo_root
    store = ctx.stores.session_streams_store
    if store is None:
        raise HTTPException(status_code=500, detail="session_streams_store unavailable")
    if dry_run:
        receipts = list_projection_receipts(store, stream_id=stream_id)
        dual = dual_write_status(ctx=ctx)
        return {
            "mode": "receipts_snapshot",
            "stream_id": stream_id,
            "receipt_count": len(receipts),
            "receipts": receipts[-50:],  # bounded
            "dual_write_missing_files": dual["missing_files"],
            "cutover": "operator-gated",
        }

    stream_ids = (stream_id,) if stream_id else None
    try:
        batch = detect_projection_drift(store, root, stream_ids=stream_ids)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="drift_failed") from exc
    # ProjectionBatchResult may be a dataclass — best-effort serialization
    if hasattr(batch, "as_dict"):
        payload = batch.as_dict()
    elif hasattr(batch, "__dict__"):
        payload = dict(batch.__dict__)
    else:
        payload = {"result": str(batch)}
    return {
        "mode": "detect_projection_drift",
        "stream_id": stream_id,
        "batch": payload,
        "cutover": "operator-gated",
    }


@router.get("/v1/plane-continuity")
def plane_continuity_bundle(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    """One-shot continuity board: health + dual-write + optional plane-status pointer.

    Does not mutate streams or flip message-plane defaults.
    """
    health = session_streams_health(ctx=ctx)
    dual = dual_write_status(ctx=ctx)
    return {
        "session_streams": health,
        "dual_write": {
            "total": dual["total"],
            "missing_files": dual["missing_files"],
        },
        "message_plane": {
            "status_path": "/api/comms/v1/plane-status",
            "default_cutover": "off — operator-gated",
        },
        "cutover": "operator-gated",
    }
