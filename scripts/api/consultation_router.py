"""
Consultation monitoring API router.

Mounted at /api/consultation/ in main.py.

Endpoints:
  GET  /api/consultation/queue                 List pending proposals
  GET  /api/consultation/queue/{filename}      Full proposal detail
  POST /api/consultation/queue/{filename}/approve  Apply changes, move to applied/
  POST /api/consultation/queue/{filename}/reject   Move to rejected/
  GET  /api/consultation/history               All consultations across modules
  GET  /api/consultation/history/{track}/{slug} Timeline for one module
  GET  /api/consultation/metrics               Aggregate stats
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT
from .state_helpers import cache_get, cache_set, read_v2_state

# Import TemplateChange and apply_template_patch at module level.
# state_helpers already inserts scripts/ into sys.path, so this import works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.consultation import TemplateChange, apply_template_patch

router = APIRouter(tags=["consultation"])

# Queue directory — same constant as pipeline.consultation
QUEUE_DIR = PROJECT_ROOT / "claude_extensions" / "consultation-queue"
APPLIED_DIR = QUEUE_DIR / "applied"
REJECTED_DIR = QUEUE_DIR / "rejected"

# Template base directory
TEMPLATE_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"

# Track IDs for iteration
_TRACK_IDS = [level["id"] for level in LEVELS]


# ==================== HELPERS ====================


def _parse_queue_file(path: Path) -> dict | None:
    """Parse a queue YAML file, return dict or None on error."""
    try:
        return yaml.safe_load(path.read_text("utf-8"))
    except Exception:
        return None


def _list_queue_files() -> list[Path]:
    """List pending .yaml files in queue dir (not README, not subdirs)."""
    if not QUEUE_DIR.exists():
        return []
    return sorted(
        f for f in QUEUE_DIR.iterdir()
        if f.is_file() and f.suffix == ".yaml"
    )


def _queue_summary(path: Path, data: dict) -> dict:
    """Build a summary dict for a queue entry (for list endpoint)."""
    source = data.get("source_module", "")
    parts = source.split("/", 1)
    track = parts[0] if len(parts) == 2 else ""
    slug = parts[1] if len(parts) == 2 else source

    changes = data.get("proposed_changes", [])
    target_files = list({c.get("file", "") for c in changes if c.get("file")})

    return {
        "filename": path.name,
        "source_module": source,
        "track": track,
        "slug": slug,
        "consultation_num": data.get("consultation_num"),
        "confidence": data.get("confidence", "unknown"),
        "root_cause_summary": (data.get("root_cause", "") or "")[:200],
        "change_count": len(changes),
        "queued_at": data.get("queued_at", ""),
        "target_files": target_files,
    }


def _list_queue_with_summaries() -> dict:
    """List pending proposals with summaries (runs in thread)."""
    files = _list_queue_files()
    items = []
    for f in files:
        data = _parse_queue_file(f)
        if data:
            items.append(_queue_summary(f, data))
    return {"pending": items, "count": len(items)}


def _get_queue_detail(filename: str) -> tuple[int, dict]:
    """Get detail for a queue file. Returns (status_code, response_dict)."""
    for subdir, status in [(QUEUE_DIR, "pending"), (APPLIED_DIR, "applied"), (REJECTED_DIR, "rejected")]:
        path = subdir / filename
        if path.exists() and path.is_file():
            data = _parse_queue_file(path)
            if data:
                return 200, {"status": status, "filename": filename, **data}
    return 404, {"error": f"Proposal not found: {filename}"}


def _collect_all_consultations(
    track_filter: str | None = None,
    outcome_filter: str | None = None,
) -> list[dict]:
    """Scan all state.json files and collect consultation entries."""
    cache_key = "consultation_history_all"
    cached = cache_get(cache_key, ttl=30)
    if cached is not None:
        results = cached
    else:
        results = []
        for track_id in _TRACK_IDS:
            track_dir = CURRICULUM_ROOT / track_id
            orch_dir = track_dir / "orchestration"
            if not orch_dir.is_dir():
                continue
            for slug_dir in orch_dir.iterdir():
                if not slug_dir.is_dir():
                    continue
                state = read_v2_state(slug_dir)
                for entry in state.get("consultations", []):
                    results.append({
                        "track": track_id,
                        "slug": slug_dir.name,
                        **entry,
                    })
        results.sort(key=lambda x: x.get("ts", ""), reverse=True)
        cache_set(cache_key, results)

    # Apply filters
    if track_filter:
        results = [r for r in results if r["track"] == track_filter]
    if outcome_filter:
        results = [r for r in results if r.get("outcome") == outcome_filter]

    return results


def _resolve_template_path(file_field: str) -> Path | None:
    """Resolve a change's file field to a safe template path.

    Validates the resolved path is strictly within TEMPLATE_DIR.
    Returns None if the file doesn't exist or escapes the template dir.
    """
    if not file_field:
        return None
    # Try as relative path within TEMPLATE_DIR first, fall back to basename
    candidate = TEMPLATE_DIR / Path(file_field).name
    try:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(TEMPLATE_DIR.resolve()):
            return None
    except (ValueError, OSError):
        return None
    return candidate if candidate.exists() else None


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace to single spaces for fuzzy matching."""
    import re
    return re.sub(r"\s+", " ", text).strip()


def _find_matches(find_text: str, content: str) -> bool:
    """Check if FIND text exists in content (exact or whitespace-normalized)."""
    if find_text in content:
        return True
    return _normalize_ws(find_text) in _normalize_ws(content)


def _validate_find_strings(proposal: dict) -> list[dict]:
    """Check that each FIND string exists in its target template.

    Uses exact match first, then whitespace-normalized fallback (same as
    apply_template_patch). Returns a list of mismatches.
    """
    mismatches = []
    for i, change in enumerate(proposal.get("proposed_changes", [])):
        file_field = change.get("file", "")
        find_text = change.get("find", "")
        if not file_field or not find_text:
            continue
        template_path = _resolve_template_path(file_field)
        if not template_path:
            mismatches.append({
                "change_index": i,
                "file": file_field,
                "error": f"template not found or outside template dir: {Path(file_field).name}",
                "find_preview": find_text[:80],
            })
            continue
        content = template_path.read_text("utf-8")
        if not _find_matches(find_text, content):
            mismatches.append({
                "change_index": i,
                "file": file_field,
                "error": "FIND string not found in template",
                "find_preview": find_text[:80],
            })
    return mismatches


def _apply_proposal(proposal: dict) -> tuple[bool, int, list[str]]:
    """Apply all changes in a proposal to their templates.

    Returns (success, num_applied, errors).
    """
    changes = [
        TemplateChange(
            find=c.get("find", ""),
            replace=c.get("replace", ""),
            file=c.get("file", ""),
            rationale=c.get("rationale", ""),
        )
        for c in proposal.get("proposed_changes", [])
    ]

    # Group changes by target template
    templates: dict[str, list[TemplateChange]] = {}
    for change in changes:
        name = Path(change.file).name if change.file else ""
        if name:
            templates.setdefault(name, []).append(change)

    total_applied = 0
    errors = []
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    for template_name, tpl_changes in templates.items():
        template_path = _resolve_template_path(template_name)
        if not template_path:
            errors.append(f"template not found: {template_name}")
            continue
        # Write patched version alongside original
        output_path = TEMPLATE_DIR / f"consultation-patched-{now}-{template_name}"
        ok, applied = apply_template_patch(template_path, tpl_changes, output_path)
        if not ok:
            errors.append(f"patch failed for {template_name}")
        else:
            total_applied += applied
            if applied > 0:
                # Replace original with patched version
                shutil.copy2(output_path, template_path)
                output_path.unlink()

    return len(errors) == 0, total_applied, errors


def _do_approve(filename: str) -> tuple[int, dict]:
    """Execute approval: validate, patch, move. Returns (status_code, response)."""
    path = QUEUE_DIR / filename

    # Idempotent: already applied
    if (APPLIED_DIR / filename).exists():
        return 200, {"status": "already_applied", "filename": filename, "message": "No-op: already approved"}

    if not path.exists() or not path.is_file():
        return 404, {"error": f"Proposal not found: {filename}"}

    data = _parse_queue_file(path)
    if not data:
        return 400, {"error": "Malformed queue file"}

    # Validate FIND strings exist before applying
    mismatches = _validate_find_strings(data)
    if mismatches:
        return 409, {"error": "FIND string mismatch — cannot apply", "mismatches": mismatches}

    # Apply patches
    _ok, applied, errors = _apply_proposal(data)

    # Move to applied/ regardless (the proposal was approved even if 0 changes matched)
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), APPLIED_DIR / filename)

    return 200, {
        "status": "approved",
        "filename": filename,
        "changes_applied": applied,
        "errors": errors if errors else None,
    }


def _do_reject(filename: str, reason: str) -> tuple[int, dict]:
    """Execute rejection: optionally annotate, move. Returns (status_code, response)."""
    path = QUEUE_DIR / filename

    # Idempotent: already rejected
    if (REJECTED_DIR / filename).exists():
        return 200, {"status": "already_rejected", "filename": filename, "message": "No-op: already rejected"}

    if not path.exists() or not path.is_file():
        return 404, {"error": f"Proposal not found: {filename}"}

    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    # Optionally append rejection reason to the file
    if reason:
        data = _parse_queue_file(path)
        if data:
            data["rejected_reason"] = reason
            data["rejected_at"] = datetime.now(UTC).isoformat()
            path.write_text(
                yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
                "utf-8",
            )

    shutil.move(str(path), REJECTED_DIR / filename)
    return 200, {"status": "rejected", "filename": filename, "reason": reason or None}


def _compute_metrics() -> dict:
    """Compute all metrics (runs in thread). Includes keyword extraction."""
    all_entries = _collect_all_consultations()

    by_outcome = Counter(e.get("outcome", "unknown") for e in all_entries)
    by_confidence = Counter(e.get("confidence", "unknown") for e in all_entries)
    by_scope = Counter(e.get("scope", "unknown") for e in all_entries)
    by_track = Counter(e["track"] for e in all_entries)

    # Top root cause keywords from queue files (pending + applied + rejected)
    root_cause_words: Counter[str] = Counter()
    for subdir in [QUEUE_DIR, APPLIED_DIR, REJECTED_DIR]:
        if not subdir.exists():
            continue
        for f in subdir.iterdir():
            if f.suffix != ".yaml":
                continue
            data = _parse_queue_file(f)
            if data and data.get("root_cause"):
                words = data["root_cause"].lower().split()
                for w in words:
                    cleaned = w.strip(".,;:()[]\"'")
                    if len(cleaned) > 4 and cleaned.isalpha():
                        root_cause_words[cleaned] += 1

    pending_count = len(_list_queue_files())

    return {
        "total": len(all_entries),
        "pending_queue": pending_count,
        "by_outcome": dict(by_outcome),
        "by_confidence": dict(by_confidence),
        "by_scope": dict(by_scope),
        "by_track": dict(by_track),
        "top_root_causes": root_cause_words.most_common(15),
    }


# ==================== QUEUE ENDPOINTS ====================


@router.get("/queue")
async def list_queue():
    """List all pending consultation proposals."""
    return await asyncio.to_thread(_list_queue_with_summaries)


@router.get("/queue/{filename}")
async def get_queue_detail(filename: str):
    """Get full detail for a single consultation proposal."""
    code, body = await asyncio.to_thread(_get_queue_detail, filename)
    if code != 200:
        return JSONResponse(status_code=code, content=body)
    return body


@router.post("/queue/{filename}/approve")
async def approve_proposal(
    filename: str,
    confirm: bool = Query(False),
):
    """Approve a consultation proposal — validate and apply template patches."""
    if not confirm:
        return JSONResponse(
            status_code=400,
            content={"error": "Safety guard: pass ?confirm=true to approve"},
        )
    code, body = await asyncio.to_thread(_do_approve, filename)
    if code != 200:
        return JSONResponse(status_code=code, content=body)
    return body


@router.post("/queue/{filename}/reject")
async def reject_proposal(
    filename: str,
    confirm: bool = Query(False),
    reason: str = Query(""),
):
    """Reject a consultation proposal — move to rejected/."""
    if not confirm:
        return JSONResponse(
            status_code=400,
            content={"error": "Safety guard: pass ?confirm=true to reject"},
        )
    code, body = await asyncio.to_thread(_do_reject, filename, reason)
    if code != 200:
        return JSONResponse(status_code=code, content=body)
    return body


# ==================== HISTORY ENDPOINTS ====================


@router.get("/history")
async def get_history(
    track: str | None = Query(None),
    outcome: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """All consultations across all modules, with optional filters."""
    results = await asyncio.to_thread(_collect_all_consultations, track, outcome)
    total = len(results)
    page = results[offset : offset + limit]
    return {"consultations": page, "total": total, "limit": limit, "offset": offset}


@router.get("/history/{track}/{slug}")
async def get_module_history(track: str, slug: str):
    """Consultation timeline for one module."""
    orch_dir = CURRICULUM_ROOT / track / "orchestration" / slug
    if not orch_dir.is_dir():
        return JSONResponse(
            status_code=404,
            content={"error": f"Module not found: {track}/{slug}"},
        )
    state = await asyncio.to_thread(read_v2_state, orch_dir)
    consultations = state.get("consultations", [])
    return {
        "track": track,
        "slug": slug,
        "consultations": consultations,
        "count": len(consultations),
    }


# ==================== METRICS ENDPOINT ====================


@router.get("/metrics")
async def get_metrics():
    """Aggregate consultation stats."""
    cache_key = "consultation_metrics"
    cached = cache_get(cache_key, ttl=30)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_metrics)
    cache_set(cache_key, result)
    return result
