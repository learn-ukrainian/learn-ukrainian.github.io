"""
Blue Team API router — endpoints for the Blue (Claude) batch monitor dashboard.

Mounted at /api/blue/ in main.py. Gold team cannot conflict with these endpoints.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, PROJECT_ROOT

# Import #561 status cache layer
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.status_cache import read_status, get_source_paths

router = APIRouter(tags=["blue"])


@router.get("/health")
async def health():
    """Health check — Blue dashboard uses this to detect API availability."""
    return {
        "status": "ok",
        "batch_state_dir_exists": BATCH_STATE_DIR.exists(),
    }


@router.get("/live-status")
async def live_status():
    """Ground truth: scan filesystem for actual module files per track.

    Uses #561 status cache (read_status + get_source_paths) for staleness detection.
    This is the real picture — checks what files exist on disk.
    """
    results = {}
    for level_cfg in LEVELS:
        track = level_cfg["id"]
        level_dir = CURRICULUM_ROOT / level_cfg["path"]
        if not level_dir.exists():
            continue

        meta_dir = level_dir / "meta"
        status_dir = level_dir / "status"
        modules = []

        if meta_dir.exists():
            for meta_file in sorted(meta_dir.glob("*.yaml")):
                slug = meta_file.stem
                sp = get_source_paths(level_dir, slug)
                has_meta = sp["meta"].exists() if sp["meta"] else False
                has_lesson = sp["md"].exists() if sp["md"] else False
                has_activities = sp["activities"].exists() if sp["activities"] else False
                has_vocab = sp["vocabulary"].exists() if sp["vocabulary"] else False

                status_file = status_dir / f"{slug}.json"
                result = read_status(status_file, source_paths=sp)

                file_count = sum([has_meta, has_lesson, has_activities, has_vocab])
                if result and result.is_fresh and result.status == "pass":
                    state = "pass"
                elif result and not result.is_fresh and result.status == "pass":
                    state = "stale-pass"
                elif file_count == 4:
                    state = "built"
                elif file_count > 1:
                    state = "partial"
                else:
                    state = "skeleton"

                mod_info = {
                    "slug": slug,
                    "state": state,
                    "files": {
                        "meta": has_meta, "lesson": has_lesson,
                        "activities": has_activities, "vocabulary": has_vocab,
                    },
                }
                if result:
                    mod_info["audit_status"] = result.status
                    mod_info["is_fresh"] = result.is_fresh
                modules.append(mod_info)

        results[track] = {
            "module_count": len(modules),
            "states": {
                "pass": sum(1 for m in modules if m["state"] == "pass"),
                "stale_pass": sum(1 for m in modules if m["state"] == "stale-pass"),
                "built": sum(1 for m in modules if m["state"] == "built"),
                "partial": sum(1 for m in modules if m["state"] == "partial"),
                "skeleton": sum(1 for m in modules if m["state"] == "skeleton"),
            },
            "modules": modules,
        }
    return results


@router.get("/freshness")
async def data_freshness():
    """Return data source ages so dashboard can show staleness warnings."""
    sources = {}
    for cp_file in BATCH_STATE_DIR.glob("checkpoint_*.json"):
        track = cp_file.stem.replace("checkpoint_", "")
        try:
            mtime = cp_file.stat().st_mtime
            sources[f"checkpoint_{track}"] = {
                "age_seconds": int(datetime.now().timestamp() - mtime),
            }
        except Exception:
            pass

    ds_file = BATCH_STATE_DIR / "dispatcher_state.json"
    if ds_file.exists():
        try:
            mtime = ds_file.stat().st_mtime
            sources["dispatcher_state"] = {
                "age_seconds": int(datetime.now().timestamp() - mtime),
            }
        except Exception:
            pass
    return sources


@router.get("/metrics")
async def metrics():
    """Metrics — orchestrated mode, no automated velocity."""
    return {
        "avg_velocity": 0,
        "recent_velocity": 0,
        "total_processed": 0,
        "run_count": 0,
    }


@router.get("/history")
async def history():
    """Batch history placeholder."""
    return {"dispatch_history": [], "reports": []}
