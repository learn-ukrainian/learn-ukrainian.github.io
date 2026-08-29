"""
Admin & Maintenance API router.

Mounted at /api/admin/ in main.py.

Endpoints:
  GET  /api/admin/backup/list             List existing backups
  DELETE /api/admin/backup/{filename}     Delete a backup file
  GET  /api/admin/health                  Unified health check
  GET  /api/admin/disk-usage              Disk usage breakdown
  POST /api/admin/maintenance/vacuum-broker   VACUUM the message broker SQLite DB
  POST /api/admin/maintenance/clean-logs      Delete logs older than N days
  GET  /api/admin/maintenance/embedding-cache-stats  Embedding cache info
  GET  /api/admin/maintenance/annotation-stats       Image annotation quality stats
"""

import asyncio
import contextlib
import inspect
import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from .monitor_context import MonitorContext, get_ctx, production_context

router = APIRouter(tags=["admin"])
START_TIME = time.time()

# Roots and store handles come from MonitorContext via Depends(get_ctx)
# (#7269 step 8): this module keeps no module-global Path seams.

ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    """Fall back to the live production context for plain-Python callers."""
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


def _data_dir(ctx: MonitorContext) -> Path:
    return ctx.roots.project_root / "data"


def _image_dir(ctx: MonitorContext) -> Path:
    return ctx.roots.images_dir or (_data_dir(ctx) / "textbook_images")


def _mcp_dir(ctx: MonitorContext) -> Path:
    return ctx.roots.project_root / ".mcp"


# ── Helpers ───────────────────────────────────────────────────────


def _dir_size(path: Path) -> int:
    """Total size in bytes of all files under path (recursive)."""
    if not path.exists():
        return 0
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for name in filenames:
            with contextlib.suppress(OSError):
                total += os.path.getsize(os.path.join(dirpath, name))
    return total


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _broker_health(ctx: MonitorContext | None = None) -> dict:
    """Read broker DB health synchronously."""
    resolved = _resolve_context(ctx)
    message_db = resolved.roots.message_db_path
    result = {"status": "missing", "size_bytes": 0, "queue_depth": 0}
    if message_db is None or not message_db.exists():
        return result
    result["status"] = "healthy"
    result["size_bytes"] = message_db.stat().st_size
    try:
        handle = resolved.stores.message_db
        if handle is None:
            result["status"] = "error"
            return result
        conn = handle.connect(read_only=True)
        result["queue_depth"] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE acknowledged = 0"
        ).fetchone()[0]
        conn.close()
    except Exception:
        result["status"] = "error"
    return result


# ── Backup ────────────────────────────────────────────────────────


@router.get("/backup/list")
async def list_backups(ctx: MonitorContext = Depends(get_ctx)):
    """List existing backup files with timestamps and sizes."""
    backup_dir = ctx.roots.backup_dir
    if not backup_dir.exists():
        return {"backups": [], "total_size_bytes": 0, "backup_dir": str(backup_dir)}

    # Collect stats in one pass to avoid double stat() per file
    entries = []
    for f in backup_dir.iterdir():
        if not f.is_file():
            continue
        try:
            st = f.stat()
            entries.append((f.name, st.st_size, st.st_mtime))
        except OSError:
            continue

    entries.sort(key=lambda e: e[2], reverse=True)

    total = 0
    backups = []
    for name, size, mtime in entries:
        total += size
        backups.append({
            "filename": name,
            "size_bytes": size,
            "size_human": _format_bytes(size),
            "created_at": datetime.fromtimestamp(mtime, tz=UTC).isoformat(),
        })

    return {
        "backups": backups,
        "count": len(backups),
        "total_size_bytes": total,
        "total_size_human": _format_bytes(total),
        "backup_dir": str(backup_dir),
    }


@router.delete("/backup/{filename}")
async def delete_backup(filename: str, ctx: MonitorContext = Depends(get_ctx)):
    """Delete a backup file."""
    try:
        path = safe_join(ctx.roots.backup_dir, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename") from None

    try:
        size = path.stat().st_size
        path.unlink()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Backup not found") from e

    return {"deleted": filename, "freed_bytes": size, "freed_human": _format_bytes(size)}


# ── Health ────────────────────────────────────────────────────────
@router.get("/health")
async def unified_health(ctx: MonitorContext = Depends(get_ctx)):
    """Unified health check: broker, disk, and API uptime."""
    broker = _broker_health(ctx)
    if inspect.isawaitable(broker):
        broker = await broker
    disk = shutil.disk_usage(ctx.roots.project_root)
    disk_pct = round(disk.used / disk.total * 100, 1)

    broker_payload = dict(broker)
    if "size_bytes" in broker_payload:
        broker_payload["size_human"] = _format_bytes(broker_payload["size_bytes"])

    return {
        "status": "ok" if broker["status"] == "healthy" else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "broker": broker_payload,
        "disk": {
            "used_pct": disk_pct,
            "free": _format_bytes(disk.free),
            "total": _format_bytes(disk.total),
        },
    }


@router.get("/disk-usage")
async def disk_usage(ctx: MonitorContext = Depends(get_ctx)):
    """Detailed disk usage breakdown for data directories."""
    data_dir = _data_dir(ctx)
    dirs = {
        "textbook_images": data_dir / "textbook_images",
        "textbooks": data_dir / "textbooks",
        "literary_texts": data_dir / "literary_texts",
        "textbook_chunks": data_dir / "textbook_chunks",
        "backups": ctx.roots.backup_dir,
        "logs": ctx.roots.logs_dir,
        "vesum_db": data_dir / "vesum.db",
    }

    # Run all dir_size calls in parallel
    async def _measure(label: str, path: Path) -> tuple[str, dict]:
        if path.is_file():
            size = path.stat().st_size if path.exists() else 0
        else:
            size = await asyncio.to_thread(_dir_size, path)
        # OPSEC (#7081): never expose absolute/host paths to the observer UI.
        return label, {
            "exists": path.exists(),
            "size_bytes": size,
            "size_human": _format_bytes(size),
        }

    results = await asyncio.gather(*[_measure(k, v) for k, v in dirs.items()])
    breakdown = dict(results)
    total = sum(v["size_bytes"] for v in breakdown.values())

    return {
        "breakdown": breakdown,
        "total_bytes": total,
        "total_human": _format_bytes(total),
    }


# ── Maintenance ───────────────────────────────────────────────────


@router.post("/maintenance/vacuum-broker")
async def vacuum_broker(ctx: MonitorContext = Depends(get_ctx)):
    """VACUUM the SQLite message broker database to reclaim space."""
    message_db = ctx.roots.message_db_path
    handle = ctx.stores.message_db
    if message_db is None or not message_db.exists() or handle is None:
        return JSONResponse(status_code=404, content={"error": "Broker DB not found"})

    size_before = message_db.stat().st_size
    try:
        conn = handle.connect()
        conn.execute("VACUUM")
        conn.close()
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "VACUUM failed"},
        )
    size_after = message_db.stat().st_size

    return {
        "status": "ok",
        "size_before": _format_bytes(size_before),
        "size_after": _format_bytes(size_after),
        "freed_bytes": size_before - size_after,
        "freed_human": _format_bytes(max(0, size_before - size_after)),
    }


@router.post("/maintenance/clean-logs")
async def clean_logs(
    max_age_days: int = Query(30, ge=1, le=365),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Delete log files older than max_age_days."""
    cutoff = time.time() - (max_age_days * 86400)
    deleted = []

    scan_dirs = [ctx.roots.logs_dir]
    mcp_servers = _mcp_dir(ctx) / "servers"
    if mcp_servers.exists():
        for server_dir in mcp_servers.iterdir():
            log_sub = server_dir / "logs"
            if log_sub.exists():
                scan_dirs.append(log_sub)

    total_freed = 0
    for log_dir in scan_dirs:
        if not log_dir.exists():
            continue
        for f in log_dir.rglob("*.log"):
            if not f.is_file():
                continue
            try:
                st = f.stat()
                if st.st_mtime < cutoff:
                    f.unlink()
                    total_freed += st.st_size
                    deleted.append({"path": str(f.relative_to(ctx.roots.project_root)), "size": st.st_size})
            except OSError:
                pass

    return {
        "status": "ok",
        "max_age_days": max_age_days,
        "deleted_count": len(deleted),
        "freed_bytes": total_freed,
        "freed_human": _format_bytes(total_freed),
        "deleted": deleted,
    }


@router.get("/maintenance/embedding-cache-stats")
async def embedding_cache_stats(ctx: MonitorContext = Depends(get_ctx)):
    """Show embedding cache status from data/literary_texts/.embed_cache/."""
    data_dir = _data_dir(ctx)
    cache_dir = data_dir / "literary_texts" / ".embed_cache"
    if not cache_dir.exists():
        return {"exists": False, "cached_files": 0, "total_size_bytes": 0}

    by_ext = {}
    file_count = 0
    total_size = 0
    for f in cache_dir.iterdir():
        if not f.is_file():
            continue
        st = f.stat()
        file_count += 1
        total_size += st.st_size
        ext = f.suffix or "(none)"
        bucket = by_ext.setdefault(ext, {"count": 0, "size": 0})
        bucket["count"] += 1
        bucket["size"] += st.st_size

    lit_dir = data_dir / "literary_texts"
    source_files = sum(1 for f in lit_dir.iterdir() if f.is_file() and f.suffix in (".txt", ".md"))

    return {
        "exists": True,
        "cached_files": file_count,
        "total_size_bytes": total_size,
        "total_size_human": _format_bytes(total_size),
        "by_extension": by_ext,
        "source_files": source_files,
    }


@router.get("/maintenance/annotation-stats")
async def annotation_stats(ctx: MonitorContext = Depends(get_ctx)):
    """Image annotation quality stats: teaching_value distribution, empty/garbled counts."""
    image_dir = _image_dir(ctx)
    if not image_dir.exists():
        return {"error": "textbook_images directory not found"}

    total_images = 0
    annotated = 0
    teaching_values = {"high": 0, "medium": 0, "low": 0, "none": 0, "unknown": 0}
    empty_descriptions = 0
    garbled_count = 0

    for grade_dir in sorted(image_dir.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue

        ann_file = grade_dir / "annotations.json"
        if not ann_file.exists():
            for f in grade_dir.iterdir():
                if f.is_file() and f.suffix.lower() in ALLOWED_IMG_EXT:
                    total_images += 1
            continue

        try:
            data = json.loads(ann_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        for entry in (data if isinstance(data, list) else data.values()):
            if not isinstance(entry, dict):
                continue
            total_images += 1
            desc = entry.get("description_uk", "")
            tv = entry.get("teaching_value", "unknown")

            if desc:
                annotated += 1
                if any(c in desc for c in ("\x00", "\ufffd", "\u0410", "\u0411")):
                    garbled_count += 1
            else:
                empty_descriptions += 1

            if tv in teaching_values:
                teaching_values[tv] += 1
            else:
                teaching_values["unknown"] += 1

    return {
        "total_images": total_images,
        "annotated": annotated,
        "empty_descriptions": empty_descriptions,
        "garbled_encoding": garbled_count,
        "teaching_value_distribution": teaching_values,
        "annotation_rate": round(annotated / total_images * 100, 1) if total_images > 0 else 0,
    }


# ── Collection Management ────────────────────────────────────────
