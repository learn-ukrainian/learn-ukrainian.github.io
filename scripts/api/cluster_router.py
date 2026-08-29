"""Cluster readiness check router (Phase 0 — sqlite authority, no multi-host HA).

Clients use this endpoint to decide if this host can serve cluster-authoritative
reads. Reports storage-seam authority and whether the process can open authority
stores without claiming multi-host HA.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends

from scripts.control_plane import storage
from scripts.control_plane.storage import StoreId

from .monitor_context import MonitorContext, get_ctx, production_context

router = APIRouter(tags=["cluster"])


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def check_cluster_readiness(ctx: MonitorContext | None = None) -> dict[str, Any]:
    """Evaluate cluster readiness against authority stores."""
    resolved_ctx = _resolve_context(ctx)
    now = datetime.now(UTC)
    repo_root = resolved_ctx.roots.project_root if resolved_ctx.roots else None

    stores_status: dict[str, dict[str, Any]] = {}
    can_serve_cluster_reads = True

    # Active authority stores in Phase 0
    active_stores = [
        StoreId.FLEET_COMMS,
        StoreId.SESSION_STREAMS,
        StoreId.WRITE_OWNERSHIP,
    ]

    for store_id in active_stores:
        authority = storage.resolve_authority(store_id)
        accessible = False
        reason: str | None = None

        if authority is storage.Authority.PG:
            dsn = storage._pg_dsn()
            if not dsn:
                accessible = False
                reason = "pg authority configured but LEARN_UKRAINIAN_CP_PG_DSN is missing"
                can_serve_cluster_reads = False
            else:
                # In Phase 0, postgres is configured via DSN
                accessible = True
        elif authority in (storage.Authority.SQLITE, storage.Authority.SHADOW):
            try:
                db_path = storage.sqlite_path(store_id, repo_root=repo_root)
                if db_path.is_file():
                    # Test connecting through the control plane storage seam
                    conn = storage.connect(store_id, read_only=True, repo_root=repo_root)
                    conn.execute("SELECT 1")
                    conn.close()
                    accessible = True
                else:
                    # Database file doesn't exist yet, verify parent directory is writable
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    if os.access(db_path.parent, os.W_OK):
                        accessible = True
                    else:
                        accessible = False
                        reason = f"directory {db_path.parent} is not writable"
                        can_serve_cluster_reads = False
            except Exception as exc:
                accessible = False
                reason = str(exc)
                can_serve_cluster_reads = False

        status_entry: dict[str, Any] = {
            "authority": authority.value,
            "accessible": accessible,
        }
        if reason:
            status_entry["reason"] = reason
        stores_status[store_id.value] = status_entry

    # Task index has no sqlite backing in Phase 0
    task_authority = storage.resolve_authority(StoreId.TASK_INDEX)
    stores_status[StoreId.TASK_INDEX.value] = {
        "authority": task_authority.value,
        "accessible": False,
        "reason": "no sqlite backing in Phase 0",
    }

    return {
        "status": "ready" if can_serve_cluster_reads else "unready",
        "ready": can_serve_cluster_reads,
        "can_serve_cluster_reads": can_serve_cluster_reads,
        "ha_claimed": False,
        "storage_seam": stores_status,
        "checked_at": now.isoformat().replace("+00:00", "Z"),
    }


@router.get("/readiness")
async def cluster_readiness(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    """Cluster readiness endpoint for cluster-authoritative read decisions."""
    return check_cluster_readiness(ctx)
