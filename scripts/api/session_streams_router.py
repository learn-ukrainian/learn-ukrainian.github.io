"""Sol PR-K: read-only Monitor surfaces for session streams + dual-write drift.

Exposes stream digest/status, dual-write inventory, and projection drift without
any cutover mutation. Operator cutovers remain explicit CLI/events.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.dual_write import list_handoff_candidates
from agents_extensions.shared.session_streams.handoff import diagnose_handoff
from agents_extensions.shared.session_streams.model import entry_as_dict
from agents_extensions.shared.session_streams.projection import (
    detect_projection_drift,
    list_projection_receipts,
)
from agents_extensions.shared.session_streams.store import NotFoundError, SessionStreamStore

from .config import LIVE_REPO_ROOT, PROJECT_ROOT
from .repository_authority import preparation_data_root

router = APIRouter(tags=["session-streams"])


def _repo_root() -> Path:
    """Live-data checkout that owns shared .agent/ + dual-write handoffs.

    Release-mode API code roots under ``.runtime/api/releases/<sha>`` have no
    ``.git`` and do not symlink ``.agent`` / ``.claude`` (see LIVE_DATA_PATHS).
    ``primary_checkout_root(PROJECT_ROOT)`` therefore returns the release path
    and PR-K surfaces 404 for a DB that only exists on the live primary.
    Use the same authority helper as state_router: when PROJECT_ROOT is a
    release snapshot, read mutable continuity state from LIVE_REPO_ROOT.
    """
    return preparation_data_root(
        project_root=Path(PROJECT_ROOT),
        live_repo_root=Path(LIVE_REPO_ROOT),
    )


def _db_path() -> Path:
    return _repo_root() / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3"


def _store() -> SessionStreamStore:
    db_path = _db_path()
    if not db_path.is_file():
        raise FileNotFoundError(f"session-stream database does not exist: {db_path}")
    return SessionStreamStore(SessionStreamDatabase(db_path))


@router.get("/v1/health")
def session_streams_health() -> dict[str, Any]:
    """Liveness for the session-streams monitor surface (no cutover)."""
    root = _repo_root()
    db_path = _db_path()
    return {
        "ok": True,
        "repo_root": str(root),
        "db_exists": db_path.is_file(),
        "db_path": str(db_path),
        "cutover": "operator-gated",
    }


@router.get("/v1/status/{stream_id:path}")
def session_stream_status(stream_id: str) -> dict[str, Any]:
    """Handoff/lease diagnosis for one stream (read-only; no claim)."""
    if not stream_id.startswith("epic:"):
        raise HTTPException(status_code=400, detail="stream_id must look like epic:N")
    try:
        status = diagnose_handoff(_store(), stream_id)
    except (NotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise HTTPException(status_code=500, detail=f"status_failed:{exc}") from exc
    return status.as_dict()


@router.get("/v1/digest/{stream_id:path}")
def session_stream_digest(
    stream_id: str,
    limit: int = Query(default=20, ge=0, le=500),
) -> dict[str, Any]:
    """Pinned entries plus last N non-pinned entries (bounded)."""
    if not stream_id.startswith("epic:"):
        raise HTTPException(status_code=400, detail="stream_id must look like epic:N")
    try:
        digest = _store().load_digest(stream_id, limit=limit)
    except (NotFoundError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"digest_failed:{exc}") from exc
    return {
        "stream_id": stream_id,
        "limit": limit,
        "pinned": [entry_as_dict(e) for e in digest.pinned],
        "recent": [entry_as_dict(e) for e in digest.recent],
        "pinned_count": len(digest.pinned),
        "recent_count": len(digest.recent),
    }


@router.get("/v1/dual-write-status")
def dual_write_status() -> dict[str, Any]:
    """Inventory-derived handoff dual-write paths and file existence (no cutover)."""
    root = _repo_root()
    candidates = list_handoff_candidates(root)
    rows = [
        {
            "stream_id": c.stream_id,
            "stream_name": c.stream_name,
            "title": c.title,
            "path": str(c.path.relative_to(root)) if c.path.is_relative_to(root) else str(c.path),
            "exists": c.exists,
        }
        for c in candidates
    ]
    missing = sum(1 for r in rows if not r["exists"])
    return {
        "repo_root": str(root),
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
) -> dict[str, Any]:
    """Projection drift surface for dual-write (PR-K).

    Default dry_run=true returns the latest receipt snapshot + dual-write
    missing-file count without forcing a full project rewrite. Set dry_run=false
    to run detect_projection_drift (records receipts; still no stream cutover).
    """
    root = _repo_root()
    store = _store()
    if dry_run:
        receipts = list_projection_receipts(store, stream_id=stream_id)
        dual = dual_write_status()
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
        raise HTTPException(status_code=500, detail=f"drift_failed:{exc}") from exc
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
def plane_continuity_bundle() -> dict[str, Any]:
    """One-shot continuity board: health + dual-write + optional plane-status pointer.

    Does not mutate streams or flip message-plane defaults.
    """
    health = session_streams_health()
    dual = dual_write_status()
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
