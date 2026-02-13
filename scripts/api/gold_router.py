"""
Gold Team API router — endpoints for the Gold (Gemini) batch monitor dashboard.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException
import yaml

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, PROJECT_ROOT

# Ensure scripts/ is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.status_cache import read_status

router = APIRouter(tags=["gold"])

@router.get("/health")
async def health():
    return {"status": "ok", "team": "gold"}

@router.get("/ground-truth")
async def ground_truth():
    """Scan the entire project for the latest status of every module."""
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    result = {}
    # 1. Map all modules from manifest
    for level_id, level_data in manifest.get("levels", {}).items():
        for m_entry in level_data.get("modules", []):
            slug = m_entry.split("#")[0].strip() if isinstance(m_entry, str) else str(m_entry)
            result[slug] = {"status": "pending", "level": level_id}

    # 2. Hunt for status files in canonical folders
    for status_file in CURRICULUM_ROOT.rglob("status/*.json"):
        if "_archive" in str(status_file): continue
        slug = status_file.stem
        if slug in result:
            try:
                with open(status_file) as f:
                    data = json.load(f)
                result[slug]["status"] = data.get("overall", {}).get("status", "pending")
                result[slug]["source"] = "canonical"
            except Exception: pass

    # 3. Hunt for 'in-flight' status files in orchestration folders
    # These often look like {slug}.json or contain audit data
    for orch_file in CURRICULUM_ROOT.rglob("orchestration/**/*.json"):
        slug = orch_file.stem
        if slug in result and result[slug]["status"] == "pending":
            try:
                with open(orch_file) as f:
                    data = json.load(f)
                # If it has the audit schema, use it
                if "overall" in data and "status" in data["overall"]:
                    result[slug]["status"] = data["overall"]["status"]
                    result[slug]["source"] = "orchestration"
            except Exception: pass

    return {
        "modules": result,
        "last_scan": datetime.now(timezone.utc).isoformat()
    }


@router.get("/union-stats")
async def union_stats():
    """State of the Union: Reconcile Manifest vs Plans vs Build vs Status."""
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    stats = {
        "total_manifest": 0,
        "total_planned": 0,
        "total_built": 0,
        "total_passed": 0,
        "word_count_estimate": 0,
        "tracks": {}
    }

    # Plans directory
    plans_root = CURRICULUM_ROOT / "plans"

    for track_id, track_data in manifest.get("levels", {}).items():
        track_modules = track_data.get("modules", [])
        track_stats = {
            "manifest_count": len(track_modules),
            "planned_count": 0,
            "built_count": 0,
            "passed_count": 0,
            "gaps": []
        }
        
        track_dir = CURRICULUM_ROOT / track_id
        plans_dir = plans_root / track_id
        
        for m_entry in track_modules:
            slug = m_entry.split("#")[0].strip() if isinstance(m_entry, str) else str(m_entry)
            stats["total_manifest"] += 1
            
            # 1. Check Plan
            # Try both {slug}.yaml and bare-slug.yaml
            plan_file = plans_dir / f"{slug}.yaml"
            has_plan = plan_file.exists()
            if has_plan:
                track_stats["planned_count"] += 1
                stats["total_planned"] += 1
            
            # 2. Check Build (MD file)
            md_file = track_dir / f"{slug}.md"
            has_build = md_file.exists()
            if has_build:
                track_stats["built_count"] += 1
                stats["total_built"] += 1
                
            # 3. Check Status
            status_file = track_dir / "status" / f"{slug}.json"
            has_status = status_file.exists()
            if has_status:
                try:
                    with open(status_file) as f:
                        status_data = json.load(f)
                    if status_data.get("overall", {}).get("status") == "pass":
                        track_stats["passed_count"] += 1
                        stats["total_passed"] += 1
                        # Estimate word count from status
                        msg = status_data.get("gates", {}).get("lesson", {}).get("message", "0/0")
                        stats["word_count_estimate"] += int(msg.split("/")[0])
                except: pass
            
            # Identify Gaps
            if not has_plan: track_stats["gaps"].append({"slug": slug, "type": "MISSING_PLAN"})
            elif not has_build: track_stats["gaps"].append({"slug": slug, "type": "MISSING_BUILD"})

        stats["tracks"][track_id] = track_stats

    return stats


@router.get("/plan-details/{track_id}")
async def plan_details(track_id: str):
    """Return detailed blueprint info for every module in a track's plan."""
    plans_dir = CURRICULUM_ROOT / "plans" / track_id
    if not plans_dir.exists():
        return {"error": f"Plans directory not found for {track_id}"}

    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)
    
    track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])
    
    details = []
    for m_entry in track_modules:
        slug = m_entry.split("#")[0].strip() if isinstance(m_entry, str) else str(m_entry)
        plan_file = plans_dir / f"{slug}.yaml"
        
        module_plan = {"slug": slug, "status": "unplanned"}
        if plan_file.exists():
            try:
                with open(plan_file) as f:
                    data = yaml.safe_load(f)
                module_plan = {
                    "slug": slug,
                    "status": "planned",
                    "title": data.get("title", slug),
                    "focus": data.get("focus", "N/A"),
                    "word_target": data.get("word_target", 0),
                    "grammar": data.get("grammar", []),
                    "objectives": data.get("objectives", []),
                    "pedagogy": data.get("pedagogy", "N/A")
                }
            except: pass
        details.append(module_plan)
        
    return details


@router.get("/inspect/{track_id}/{slug}")
async def inspect_module(track_id: str, slug: str):
    """Deep dive into a specific module's actual file content."""
    md_path = CURRICULUM_ROOT / track_id / f"{slug}.md"
    if not md_path.exists():
        return {"error": "Source file not found"}

    content = md_path.read_text()
    words = len(content.split())
    
    # Simple count of headers and callouts
    h2_count = content.count("\n## ")
    callout_count = content.count("> [!")
    
    return {
        "slug": slug,
        "track": track_id,
        "word_count": words,
        "sections": h2_count,
        "engagement_callouts": callout_count,
        "last_modified": datetime.fromtimestamp(md_path.stat().st_mtime, tz=timezone.utc).isoformat()
    }


@router.get("/orchestration/{track_id}/{slug}")
async def orchestration_history(track_id: str, slug: str):
    """Reconstruct the phase history from the orchestration folder."""
    orch_dir = CURRICULUM_ROOT / track_id / "orchestration" / slug
    if not orch_dir.exists():
        return []

    artifacts = []
    # Sort by mtime to get a chronological timeline
    for f in sorted(orch_dir.iterdir(), key=lambda x: x.stat().st_mtime):
        if f.is_file():
            artifacts.append({
                "file": f.name,
                "type": "audit" if "audit" in f.name else ("prompt" if "prompt" in f.name else "output"),
                "timestamp": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
                "size": f.stat().st_size
            })
    return artifacts


@router.get("/broker-messages")
async def broker_messages():
    """Read the live outbox/inbox for agent communication."""
    outbox = PROJECT_ROOT / ".gemini" / "outbox"
    messages = []
    if outbox.exists():
        for f in sorted(outbox.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(f) as fh:
                    msg = json.load(fh)
                    msg["id"] = f.stem
                    msg["direction"] = "outbound"
                    msg["time"] = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                    messages.append(msg)
            except: pass
    return messages[:50]

@router.get("/active-orchestration")
async def active_orchestration():
    """Scan all orchestration folders for active module builds."""
    active = []
    for track_dir in CURRICULUM_ROOT.iterdir():
        if not track_dir.is_dir():
            continue

        orch_dir = track_dir / "orchestration"
        if not orch_dir.exists():
            continue

        for module_dir in orch_dir.iterdir():
            if not module_dir.is_dir():
                continue

            latest_mtime = 0
            for f in module_dir.iterdir():
                if f.is_file():
                    latest_mtime = max(latest_mtime, f.stat().st_mtime)

            # Active if modified in last 15 mins
            if (datetime.now().timestamp() - latest_mtime) < 900:
                active.append({
                    "slug": module_dir.name,
                    "track": track_dir.name,
                    "seconds_ago": int(datetime.now().timestamp() - latest_mtime)
                })

    return active
