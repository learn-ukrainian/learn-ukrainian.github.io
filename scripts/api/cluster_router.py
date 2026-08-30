"""Cluster readiness check router (#7493 — probe injected stores, bounded, no side effects).

Clients use this endpoint to decide if this host can serve cluster-authoritative
reads. Contract (private HA plan v3.1 + 2026-08-30 review):

- Postgres authority pings via the storage seam with BOTH a connect timeout and
  a statement timeout; a configured DSN alone is never "ready".
- A GET must not mutate the filesystem (no directory creation) and an absent
  sqlite database is NOT accessible — "could be created later" is not "can
  serve authoritative reads now".
- Probes run off the event loop, concurrently, under one total deadline.
- Reasons are fixed, OPSEC-safe codes — never exception text or paths.
- ``task_index`` is reported as optional (no backing in Phase 0) and never
  affects readiness; liveness stays on ``/api/health``, readiness here.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from scripts.control_plane import storage
from scripts.control_plane.storage import StoreId

from .monitor_context import MonitorContext, get_ctx, production_context

router = APIRouter(tags=["cluster"])

# Bounded probe budget: pg connect_timeout (3s, storage seam) + statement
# timeout must fit inside the per-probe deadline; the endpoint answers within
# the total deadline even when every store hangs.
_STATEMENT_TIMEOUT_MS = 2000
_PROBE_DEADLINE_S = 6.0
_TOTAL_DEADLINE_S = 8.0

# Fixed reason codes (OPSEC: no exception text, paths, DSNs, or hostnames).
_REASON_DSN_MISSING = "pg_dsn_missing"
_REASON_PG_PROBE_FAILED = "pg_probe_failed"
_REASON_DB_MISSING = "sqlite_database_missing"
_REASON_SQLITE_PROBE_FAILED = "sqlite_probe_failed"
_REASON_PROBE_TIMEOUT = "probe_timeout"
_REASON_NO_BACKING = "no_sqlite_backing_in_phase_0"

_ACTIVE_STORES = (
    StoreId.FLEET_COMMS,
    StoreId.SESSION_STREAMS,
    StoreId.WRITE_OWNERSHIP,
)


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def _sqlite_path_for(
    store_id: StoreId, ctx: MonitorContext, repo_root: Path | None
) -> Path:
    """Prefer the context's injected store handle over re-derived paths (#7493)."""
    if store_id is StoreId.SESSION_STREAMS:
        database = ctx.stores.session_streams_database
        if database is not None and getattr(database, "path", None) is not None:
            return Path(database.path)
        return Path(ctx.roots.session_streams_db_path)
    return storage.sqlite_path(store_id, repo_root=repo_root)


def _probe_sqlite(store_id: StoreId, db_path: Path) -> tuple[bool, str | None]:
    if not db_path.is_file():
        # Readiness never creates directories or files: an absent database
        # cannot serve authoritative reads, whatever the parent permissions.
        return False, _REASON_DB_MISSING
    try:
        # Through the storage seam (read-only URI open) — the router itself
        # never calls sqlite3.connect (app-factory step-two allowlist).
        conn = storage.connect(store_id, path=db_path, read_only=True)
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception:
        # OPSEC: fixed code only — no str(exc), which can carry paths.
        return False, _REASON_SQLITE_PROBE_FAILED
    return True, None


def _probe_pg(store_id: StoreId, repo_root: Path | None) -> tuple[bool, str | None]:
    if not storage._pg_dsn():
        return False, _REASON_DSN_MISSING
    try:
        conn = storage.connect(store_id, read_only=True, repo_root=repo_root)
        try:
            # Plan contract: SELECT 1 *with a timeout* — connect_timeout covers
            # the handshake only; a hung server post-connect must not hold the
            # probe. SET is allowed inside a read-only session.
            conn.execute(f"SET statement_timeout = {_STATEMENT_TIMEOUT_MS}")
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception:
        return False, _REASON_PG_PROBE_FAILED
    return True, None


def _probe_store(
    store_id: StoreId, ctx: MonitorContext, repo_root: Path | None
) -> dict[str, Any]:
    authority = storage.resolve_authority(store_id)
    if authority is storage.Authority.PG:
        accessible, reason = _probe_pg(store_id, repo_root)
    elif authority in (storage.Authority.SQLITE, storage.Authority.SHADOW):
        try:
            db_path = _sqlite_path_for(store_id, ctx, repo_root)
        except Exception:
            db_path = None
        if db_path is None:
            accessible, reason = False, _REASON_SQLITE_PROBE_FAILED
        else:
            accessible, reason = _probe_sqlite(store_id, db_path)
    else:
        accessible, reason = False, _REASON_SQLITE_PROBE_FAILED
    entry: dict[str, Any] = {"authority": authority.value, "accessible": accessible}
    if reason:
        entry["reason"] = reason
    return entry


def check_cluster_readiness(ctx: MonitorContext | None = None) -> dict[str, Any]:
    """Evaluate cluster readiness against the app's authority stores.

    Blocking by design — callers on an event loop go through the sync route
    handler (FastAPI threadpool) or their own executor.
    """
    resolved_ctx = _resolve_context(ctx)
    now = datetime.now(UTC)
    repo_root = resolved_ctx.roots.project_root if resolved_ctx.roots else None

    stores_status: dict[str, dict[str, Any]] = {}
    # NOT a ``with`` block: ThreadPoolExecutor.__exit__ JOINS workers, so one
    # hung probe (e.g. a wedged sqlite open) would hold the response past
    # every advertised deadline (CF r1 finding, PR #7499). Shut down without
    # waiting; a stuck worker thread is bounded by the pg connect/statement
    # timeouts and cannot block the answer.
    pool = ThreadPoolExecutor(max_workers=len(_ACTIVE_STORES))
    try:
        futures = {
            store_id: pool.submit(_probe_store, store_id, resolved_ctx, repo_root)
            for store_id in _ACTIVE_STORES
        }
        deadline = time.monotonic() + _TOTAL_DEADLINE_S
        for store_id, future in futures.items():
            per_probe = min(_PROBE_DEADLINE_S, max(0.0, deadline - time.monotonic()))
            try:
                entry = future.result(timeout=per_probe)
            except TimeoutError:
                entry = {
                    "authority": storage.resolve_authority(store_id).value,
                    "accessible": False,
                    "reason": _REASON_PROBE_TIMEOUT,
                }
            except Exception:
                entry = {
                    "authority": "unknown",
                    "accessible": False,
                    "reason": _REASON_SQLITE_PROBE_FAILED,
                }
            stores_status[store_id.value] = entry
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    can_serve_cluster_reads = all(
        entry["accessible"] for entry in stores_status.values()
    )

    # task_index is explicitly optional in Phase 0: reported for visibility,
    # labeled, and never part of the readiness decision.
    stores_status[StoreId.TASK_INDEX.value] = {
        "authority": storage.resolve_authority(StoreId.TASK_INDEX).value,
        "accessible": False,
        "optional": True,
        "reason": _REASON_NO_BACKING,
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
def cluster_readiness(ctx: MonitorContext = Depends(get_ctx)) -> dict[str, Any]:
    """Cluster readiness for cluster-authoritative read decisions.

    Sync handler on purpose: FastAPI runs it in the threadpool, keeping the
    blocking store probes off the event loop (#7493).
    """
    return check_cluster_readiness(ctx)
