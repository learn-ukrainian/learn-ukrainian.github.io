"""
Admin & Maintenance API router.

Mounted at /api/admin/ in main.py.

Endpoints:
  GET  /api/admin/health                  Unified health check
  GET  /api/admin/disk-usage              Disk usage breakdown
  POST /api/admin/maintenance/vacuum-broker   VACUUM the message broker SQLite DB
  POST /api/admin/maintenance/clean-logs      Delete logs older than N days
  GET  /api/admin/maintenance/embedding-cache-stats  Embedding cache info
  GET  /api/admin/maintenance/annotation-stats       Image annotation quality stats
"""

import asyncio
import contextlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from .config import (
    BATCH_STATE_DIR,
    LOGS_DIR,
    MESSAGE_DB,
    PROJECT_ROOT,
    SOURCES_DB,
    VESUM_DB,
)
from .config import (
    TEXTBOOK_IMAGES_DIR as IMAGE_DIR,
)
from .resilience import connect_sqlite

router = APIRouter(tags=["admin"])

# ── Config ────────────────────────────────────────────────────────

ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}

# Restore for test compatibility
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
DATA_DIR = PROJECT_ROOT / "data"
MCP_DIR = PROJECT_ROOT / ".mcp"


# ── Helpers ───────────────────────────────────────────────────────


def _dir_size(path: Path) -> int:
    """Total size in bytes of all files under path (recursive)."""
    if not path.exists():
        return 0
    total = 0
    if path.is_file():
        return path.stat().st_size
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


def _broker_health() -> dict:
    """Read broker DB health synchronously."""
    result = {"status": "missing", "size_bytes": 0, "queue_depth": 0}
    if not MESSAGE_DB.exists():
        return result
    result["status"] = "healthy"
    result["size_bytes"] = MESSAGE_DB.stat().st_size
    try:
        conn = connect_sqlite(f"file:{MESSAGE_DB}?mode=ro", uri=True)
        result["queue_depth"] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE acknowledged = 0"
        ).fetchone()[0]
        conn.close()
    except Exception:
        result["status"] = "error"
    return result


# ── Health ────────────────────────────────────────────────────────


@router.get("/health")
async def unified_health():
    """Unified health check: databases, broker, disk, uptime."""
    from .main import _SERVER_START

    now = datetime.now(UTC)
    uptime = now - _SERVER_START

    # Run independent checks in parallel
    broker = await asyncio.to_thread(_broker_health)

    # Database statuses
    sources_ok = SOURCES_DB.exists()
    vesum_ok = VESUM_DB.exists()

    # Disk usage (quick summary) — run in thread to not block event loop
    data_size = await asyncio.to_thread(_dir_size, DATA_DIR)

    return {
        "status": "ok" if sources_ok and vesum_ok and broker["status"] == "healthy" else "degraded",
        "checked_at": now.isoformat(),
        "uptime_seconds": int(uptime.total_seconds()),
        "databases": {
            "sources_db": "ok" if sources_ok else "missing",
            "vesum_db": "ok" if vesum_ok else "missing",
        },
        "broker": {
            **broker,
            "size_human": _format_bytes(broker["size_bytes"]),
        },
        "disk": {
            "data_dir_bytes": data_size,
            "data_dir_human": _format_bytes(data_size),
        },
    }


@router.get("/disk-usage")
async def disk_usage():
    """Detailed disk usage breakdown for data directories."""
    dirs = {
        "sources_db": SOURCES_DB,
        "vesum_db": VESUM_DB,
        "textbook_images": IMAGE_DIR,
        "textbooks": DATA_DIR / "textbooks",
        "literary_texts": DATA_DIR / "literary_texts",
        "batch_state": BATCH_STATE_DIR,
        "logs": LOGS_DIR,
    }

    # Run all dir_size calls in parallel
    async def _measure(label: str, path: Path) -> tuple[str, dict]:
        size = await asyncio.to_thread(_dir_size, path)
        return label, {
            "path": str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path),
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
async def vacuum_broker():
    """VACUUM the SQLite message broker database to reclaim space."""
    if not MESSAGE_DB.exists():
        return JSONResponse(status_code=404, content={"error": "Broker DB not found"})

    size_before = MESSAGE_DB.stat().st_size
    try:
        conn = connect_sqlite(str(MESSAGE_DB))
        conn.execute("VACUUM")
        conn.close()
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "VACUUM failed"},
        )
    size_after = MESSAGE_DB.stat().st_size

    return {
        "status": "ok",
        "size_before": _format_bytes(size_before),
        "size_after": _format_bytes(size_after),
        "freed_bytes": size_before - size_after,
        "freed_human": _format_bytes(max(0, size_before - size_after)),
    }


@router.post("/maintenance/clean-logs")
async def clean_logs(max_age_days: int = Query(30, ge=1, le=365)):
    """Delete log files older than max_age_days."""
    cutoff = time.time() - (max_age_days * 86400)
    deleted = []

    scan_dirs = [LOGS_DIR]
    mcp_servers = MCP_DIR / "servers"
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
                    deleted.append({"path": str(f.relative_to(PROJECT_ROOT)), "size": st.st_size})
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
async def embedding_cache_stats():
    """Show embedding cache status from data/literary_texts/.embed_cache/."""
    cache_dir = DATA_DIR / "literary_texts" / ".embed_cache"
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

    lit_dir = DATA_DIR / "literary_texts"
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
async def annotation_stats():
    """Image annotation quality stats: teaching_value distribution, empty/garbled counts."""
    if not IMAGE_DIR.exists():
        return {"error": "textbook_images directory not found"}

    total_images = 0
    annotated = 0
    teaching_values = {"high": 0, "medium": 0, "low": 0, "none": 0, "unknown": 0}
    empty_descriptions = 0
    garbled_count = 0

    for grade_dir in sorted(IMAGE_DIR.iterdir()):
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


# ── Stubs for backward compatibility (used by older tests) ──────

@router.get("/collections")
async def collection_details():
    return {"collections": [], "count": 0, "status": "deprecated"}

@router.post("/collections/verify")
async def verify_collections():
    return {"results": [], "source_counts": {}, "status": "deprecated"}

@router.post("/backup/qdrant")
async def create_qdrant_backup():
    return {"status": "error", "message": "Qdrant is deprecated"}

@router.get("/backup/list")
async def list_backups():
    return {"backups": [], "count": 0, "total_size_bytes": 0, "status": "deprecated"}

@router.delete("/backup/{filename}")
async def delete_backup(filename: str):
    return {"deleted": filename, "freed_bytes": 0, "status": "deprecated"}

# Private stubs for unittests that patch internal helpers
async def _qdrant_get(path: str): return None
async def _qdrant_post(path: str): return None
async def _qdrant_collection_details(names: list[str]): return {}
async def _docker_status(container: str): return "deprecated"
