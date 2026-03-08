"""
Admin & Maintenance API router.

Mounted at /api/admin/ in main.py.

Endpoints:
  POST /api/admin/backup/qdrant           Create Qdrant snapshot + copy to backup dir
  GET  /api/admin/backup/list             List existing backups
  DELETE /api/admin/backup/{filename}     Delete a backup file
  GET  /api/admin/health                  Unified health check
  GET  /api/admin/disk-usage              Disk usage breakdown
  POST /api/admin/maintenance/vacuum-broker   VACUUM the message broker SQLite DB
  POST /api/admin/maintenance/clean-logs      Delete logs older than N days
  GET  /api/admin/maintenance/embedding-cache-stats  Embedding cache info
  GET  /api/admin/maintenance/annotation-stats       Image annotation quality stats
  GET  /api/admin/collections             Extended collection stats
  POST /api/admin/collections/verify      Verify Qdrant vs JSONL counts
"""

import asyncio
import contextlib
import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import MESSAGE_DB, PROJECT_ROOT

router = APIRouter(tags=["admin"])

# ── Config ────────────────────────────────────────────────────────

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
BACKUP_DIR = Path(
    os.environ.get(
        "BACKUP_DIR",
        str(PROJECT_ROOT / "data" / "backups"),
    )
)
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "textbook_images"
LOGS_DIR = PROJECT_ROOT / "logs"
MCP_DIR = PROJECT_ROOT / ".mcp"
ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


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


def _safe_within(path: Path, root: Path) -> bool:
    """Check that resolved path is under root (prevents traversal)."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


_qdrant_client = httpx.AsyncClient(base_url=QDRANT_URL, timeout=10)


async def _qdrant_get(path: str) -> dict | None:
    """GET request to Qdrant REST API. Returns None on failure."""
    try:
        r = await _qdrant_client.get(path)
        r.raise_for_status()
        return r.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None


async def _qdrant_post(path: str, timeout: float = 120) -> dict | None:
    """POST request to Qdrant REST API. Returns None on failure."""
    try:
        r = await _qdrant_client.post(path, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None


async def _qdrant_collection_details(names: list[str]) -> dict[str, dict | None]:
    """Fetch details for multiple collections in parallel."""
    results = await asyncio.gather(
        *[_qdrant_get(f"/collections/{name}") for name in names]
    )
    return dict(zip(names, results, strict=False))


async def _docker_status(container: str) -> str:
    """Check Docker container status without blocking the event loop."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "inspect", "--format", "{{.State.Status}}", container,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        return stdout.decode().strip() if proc.returncode == 0 else "not found"
    except Exception:
        return "docker unavailable"


def _broker_health() -> dict:
    """Read broker DB health synchronously."""
    result = {"status": "missing", "size_bytes": 0, "queue_depth": 0}
    if not MESSAGE_DB.exists():
        return result
    result["status"] = "healthy"
    result["size_bytes"] = MESSAGE_DB.stat().st_size
    try:
        conn = sqlite3.connect(f"file:{MESSAGE_DB}?mode=ro", uri=True)
        result["queue_depth"] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE acknowledged = 0"
        ).fetchone()[0]
        conn.close()
    except Exception:
        result["status"] = "error"
    return result


# ── Backup ────────────────────────────────────────────────────────


@router.post("/backup/qdrant")
async def create_qdrant_backup():
    """Create a full Qdrant snapshot and stream it to the backup directory."""
    result = await _qdrant_post("/snapshots")
    if result is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Qdrant unreachable. Is Docker running?"},
        )

    snapshot_name = result.get("result", {}).get("name")
    if not snapshot_name:
        return JSONResponse(
            status_code=500,
            content={"error": "Snapshot creation failed", "detail": result},
        )

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / snapshot_name

    # Stream download to avoid buffering entire snapshot in memory
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client, client.stream(
            "GET",
            f"{QDRANT_URL}/snapshots/{snapshot_name}",
            follow_redirects=True,
        ) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in r.aiter_bytes(chunk_size=65536):
                    f.write(chunk)
    except Exception as e:
        dest.unlink(missing_ok=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to download snapshot: {e}"},
        )

    size = dest.stat().st_size
    return {
        "status": "ok",
        "snapshot": snapshot_name,
        "path": str(dest),
        "size_bytes": size,
        "size_human": _format_bytes(size),
        "created_at": datetime.now(UTC).isoformat(),
    }


@router.get("/backup/list")
async def list_backups():
    """List existing backup files with timestamps and sizes."""
    if not BACKUP_DIR.exists():
        return {"backups": [], "total_size_bytes": 0, "backup_dir": str(BACKUP_DIR)}

    # Collect stats in one pass to avoid double stat() per file
    entries = []
    for f in BACKUP_DIR.iterdir():
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
        "backup_dir": str(BACKUP_DIR),
    }


@router.delete("/backup/{filename}")
async def delete_backup(filename: str):
    """Delete a backup file."""
    path = BACKUP_DIR / filename
    if not _safe_within(path, BACKUP_DIR):
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        size = path.stat().st_size
        path.unlink()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Backup not found") from e

    return {"deleted": filename, "freed_bytes": size, "freed_human": _format_bytes(size)}


# ── Health ────────────────────────────────────────────────────────


@router.get("/health")
async def unified_health():
    """Unified health check: Qdrant, broker, disk, uptime."""
    from .main import _SERVER_START

    now = datetime.now(UTC)
    uptime = now - _SERVER_START

    # Run independent checks in parallel
    qdrant_future = _qdrant_get("/collections")
    docker_future = _docker_status("qdrant")
    broker = await asyncio.to_thread(_broker_health)
    qdrant_info, docker_stat = await asyncio.gather(qdrant_future, docker_future)

    # Qdrant details — fetch all collections in parallel
    qdrant_ok = qdrant_info is not None
    qdrant_collections = []
    total_points = 0
    if qdrant_ok:
        names = [c.get("name", "") for c in qdrant_info.get("result", {}).get("collections", [])]
        details = await _qdrant_collection_details(names)
        for name in names:
            detail = details.get(name)
            points = detail.get("result", {}).get("points_count", 0) if detail else 0
            total_points += points
            qdrant_collections.append({"name": name, "points": points})

    # Disk usage (quick summary) — run in thread to not block event loop
    data_size = await asyncio.to_thread(_dir_size, DATA_DIR)

    return {
        "status": "ok" if qdrant_ok and broker["status"] == "healthy" else "degraded",
        "checked_at": now.isoformat(),
        "uptime_seconds": int(uptime.total_seconds()),
        "qdrant": {
            "status": "healthy" if qdrant_ok else "unreachable",
            "docker": docker_stat,
            "collections": qdrant_collections,
            "total_points": total_points,
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
        "qdrant_storage": DATA_DIR / "qdrant" / "storage",
        "textbook_images": DATA_DIR / "textbook_images",
        "textbooks": DATA_DIR / "textbooks",
        "literary_texts": DATA_DIR / "literary_texts",
        "textbook_chunks": DATA_DIR / "textbook_chunks",
        "backups": BACKUP_DIR,
        "logs": LOGS_DIR,
        "vesum_db": DATA_DIR / "vesum.db",
    }

    # Run all dir_size calls in parallel
    async def _measure(label: str, path: Path) -> tuple[str, dict]:
        if path.is_file():
            size = path.stat().st_size if path.exists() else 0
        else:
            size = await asyncio.to_thread(_dir_size, path)
        return label, {
            "path": str(path),
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
        conn = sqlite3.connect(str(MESSAGE_DB))
        conn.execute("VACUUM")
        conn.close()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"VACUUM failed: {e}"},
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


# ── Collection Management ────────────────────────────────────────


@router.get("/collections")
async def collection_details():
    """Extended collection stats with coverage info."""
    qdrant_info = await _qdrant_get("/collections")
    if qdrant_info is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Qdrant unreachable. Start with: docker start qdrant"},
        )

    names = [c.get("name", "") for c in qdrant_info.get("result", {}).get("collections", [])]
    details = await _qdrant_collection_details(names)

    collections = []
    for name in names:
        detail = details.get(name)
        if not detail:
            collections.append({"name": name, "error": "could not fetch details"})
            continue

        info = detail.get("result", {})
        collections.append({
            "name": name,
            "points_count": info.get("points_count", 0),
            "vectors_count": info.get("vectors_count", 0),
            "indexed_vectors_count": info.get("indexed_vectors_count", 0),
            "status": info.get("status", "unknown"),
            "config": {
                "vector_size": info.get("config", {}).get("params", {}).get("vectors", {}),
            },
        })

    return {"collections": collections, "count": len(collections)}


@router.post("/collections/verify")
async def verify_collections():
    """Compare Qdrant point counts vs on-disk JSONL chunk counts."""
    qdrant_info = await _qdrant_get("/collections")
    if qdrant_info is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Qdrant unreachable"},
        )

    # Count on-disk sources
    source_counts = {}

    chunks_dir = DATA_DIR / "textbook_chunks"
    if chunks_dir.exists():
        chunk_count = 0
        for f in chunks_dir.rglob("*.jsonl"):
            with contextlib.suppress(OSError):
                chunk_count += sum(1 for line in f.open() if line.strip())
        source_counts["textbook_chunks"] = chunk_count

    if IMAGE_DIR.exists():
        img_count = 0
        for grade_dir in IMAGE_DIR.iterdir():
            if grade_dir.is_dir() and grade_dir.name.startswith("grade-"):
                img_count += sum(
                    1 for f in grade_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in ALLOWED_IMG_EXT
                )
        source_counts["textbook_images"] = img_count

    lit_dir = DATA_DIR / "literary_texts"
    if lit_dir.exists():
        lit_count = 0
        for f in lit_dir.rglob("*.jsonl"):
            with contextlib.suppress(OSError):
                lit_count += sum(1 for line in f.open() if line.strip())
        source_counts["literary_texts"] = lit_count

    # Fetch all collection details in parallel
    names = [c.get("name", "") for c in qdrant_info.get("result", {}).get("collections", [])]
    details = await _qdrant_collection_details(names)

    results = []
    for name in names:
        detail = details.get(name)
        qdrant_points = detail.get("result", {}).get("points_count", 0) if detail else 0
        disk_count = source_counts.get(name)
        gap = (qdrant_points - disk_count) if disk_count is not None else None

        results.append({
            "collection": name,
            "qdrant_points": qdrant_points,
            "disk_chunks": disk_count,
            "gap": gap,
            "status": "ok" if gap == 0 else ("surplus" if gap and gap > 0 else "deficit") if gap is not None else "no_source_mapping",
        })

    return {
        "results": results,
        "source_counts": source_counts,
        "verified_at": datetime.now(UTC).isoformat(),
    }
