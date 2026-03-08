"""
State API router — v3/v4/v5 pipeline state, research/review coverage, weak points, issues.

Mounted at /api/state/ in main.py.

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module v3/v4/v5 phase state for one track
  GET /api/state/ready-to-build       Phase A done, Phase B not started
  GET /api/state/weak-points          Modules with quality issues
  GET /api/state/build-status/{track}  Compact live build progress (one call)
  GET /api/state/build-status          All-tracks build progress summary
  GET /api/state/module/{track}/{num}  Single module deep-dive with comms
  GET /api/state/final-reviews/{track} Phase F results aggregated per track
  GET /api/state/failing              Modules with audit/phase failures
  GET /api/state/research-coverage    Per-track research completeness
  GET /api/state/research/{track}    Per-module research quality + dimensions + upgrade queue
  GET /api/state/review-coverage      Per-track review completeness + quality
  GET /api/state/issues               Aggregated outstanding issues

Performance notes:
  - Heavy endpoints (summary, research-coverage, review-coverage, pipeline/{track})
    run their sync I/O in asyncio.to_thread() to avoid blocking the event loop.
  - Results are cached in-memory with a TTL (60s for summary/pipeline, 300s for coverage).
"""

import asyncio
import json
import re
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS, MESSAGE_DB

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import contextlib

from research_quality import assess_research_compat, find_research_path

from .review_parsing import count_review_issues, extract_plan_verdict, extract_review_score, extract_review_verdict

router = APIRouter(tags=["state"])


def _extract_content_hash(review_path: Path) -> str | None:
    """Extract content hash from review file header (#618).

    Reviews written by write_review_with_hash() start with:
        <!-- content-hash: abc123def456 -->
    Returns the hash string, or None if not found.
    """
    try:
        with open(review_path, encoding="utf-8") as f:
            first_line = f.readline()
        m = re.match(r"<!-- content-hash: ([a-f0-9]+) -->", first_line)
        return m.group(1) if m else None
    except Exception:
        return None


def _is_review_stale(review_path: Path, content_path: Path | None) -> bool:
    """Check if a review file is stale relative to its content (#618).

    Uses content hash if available (robust, mtime-independent).
    Falls back to mtime comparison with <= for older reviews without hash.
    """
    if not content_path or not content_path.exists():
        return False

    import hashlib
    review_hash = _extract_content_hash(review_path)
    if review_hash:
        current_hash = hashlib.md5(content_path.read_bytes(), usedforsecurity=False).hexdigest()[:12]
        return review_hash != current_hash

    # Fallback: mtime comparison — stale only if review is strictly older.
    # Equal mtimes (git checkout resets both to same time) = fresh.
    content_mtime = content_path.stat().st_mtime
    return content_mtime > 0 and review_path.stat().st_mtime < content_mtime


# ==================== CONSTANTS ====================

CURRICULUM_YAML = CURRICULUM_ROOT / "curriculum.yaml"
PLANS_ROOT = CURRICULUM_ROOT / "plans"

PROFILE_MAP = {
    "a1": "core", "a2": "core", "b1": "core", "b2": "core",
    "b2-pro": "pro", "c1-pro": "pro",
    "c1": "core", "c2": "core",
    "hist": "seminar", "istorio": "seminar", "bio": "seminar",
    "lit": "seminar", "lit-essay": "seminar", "lit-hist-fic": "seminar",
    "lit-fantastika": "seminar", "lit-war": "seminar",
    "lit-humor": "seminar", "lit-youth": "seminar",
    "lit-doc": "seminar", "lit-drama": "seminar",
    "lit-crimea": "seminar",
    "oes": "seminar", "ruth": "seminar",
}

# ==================== TTL CACHE ====================

_ttl_cache: dict[str, tuple[float, object]] = {}


def _cache_get(key: str, ttl: float) -> object | None:
    """Return cached value if still within TTL, else None."""
    entry = _ttl_cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def _cache_set(key: str, value: object) -> None:
    _ttl_cache[key] = (time.time(), value)


# ==================== PRIVATE HELPERS ====================

_curriculum_cache: dict | None = None


def _load_curriculum() -> dict:
    """Load curriculum.yaml once and cache."""
    global _curriculum_cache
    if _curriculum_cache is None:
        _curriculum_cache = yaml.safe_load(CURRICULUM_YAML.read_text()) or {} if CURRICULUM_YAML.exists() else {}
    return _curriculum_cache


def _to_bare_slug(entry: str) -> str:
    """Strip numeric prefix if present (e.g. '01-the-cyrillic-code-i' → 'the-cyrillic-code-i')."""
    if not entry:
        return entry
    entry = entry.split("#")[0].strip()
    match = re.match(r"^\d+-(.+)$", entry)
    return match.group(1) if match else entry


def _get_plan_slugs(track_id: str) -> list[tuple[int, str]]:
    """Return [(num, slug)] for a track, sorted by position.

    Primary: curriculum.yaml ordering.
    Fallback: scan PLANS_ROOT / track_id / *.yaml, sorted alphabetically.
    Tracks not in curriculum.yaml and with no plans/ dir return [].
    """
    data = _load_curriculum()
    modules = data.get("levels", {}).get(track_id, {}).get("modules", [])
    if modules:
        result = []
        for i, entry in enumerate(modules):
            slug = _to_bare_slug(str(entry))
            if slug:
                result.append((i + 1, slug))
        return result

    # Fallback: individual plan YAML files (seminar tracks during early dev)
    plan_dir = PLANS_ROOT / track_id
    if plan_dir.is_dir():
        plan_files = sorted(plan_dir.glob("*.yaml"))
        return [(i + 1, f.stem) for i, f in enumerate(plan_files)]

    return []


def _read_v4_state(orch_dir: Path) -> dict:
    """Read state-v4.json, return {} if missing or invalid."""
    state_file = orch_dir / "state-v4.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


def _read_v3_state(orch_dir: Path) -> dict:
    """Read state-v3.json, return {} if missing or invalid."""
    state_file = orch_dir / "state-v3.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


def _read_v2_state(orch_dir: Path) -> dict:
    """Read state.json (v2 pipeline), return {} if missing or invalid."""
    state_file = orch_dir / "state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text()) or {}
    except Exception:
        return {}


V4_PHASE_ORDER = ["research", "discover", "content", "activities", "validate", "review", "mdx"]
V5_PHASE_ORDER = ["research", "discover", "sandbox", "content", "activities", "validate", "review", "mdx"]


def _detect_pipeline_version(orch_dir: Path) -> str:
    """Detect pipeline version for a module.

    Priority: state.json mode=v5 > state-v4.json > state-v3.json > state.json["mode"] > "unbuilt".
    """
    # v5 uses state.json with mode: "v5"
    v2 = _read_v2_state(orch_dir)
    if v2.get("mode") == "v5":
        return "v5"
    if (orch_dir / "state-v4.json").exists():
        return "v4"
    if (orch_dir / "state-v3.json").exists():
        return "v3"
    if v2.get("mode") == "v4":
        return "v4"
    if v2:
        return "v3"
    return "unbuilt"


def _parse_v4_phase_status(v4_state: dict, phase_name: str) -> dict:
    """Extract status info for a v4 phase (e.g. 'research', 'content')."""
    phase = v4_state.get("phases", {}).get(f"v4-{phase_name}", {})
    if not phase:
        return {"status": "pending"}
    return {
        "status": phase.get("status", "pending"),
        "ts": phase.get("ts"),
    }


def _parse_v5_phase_status(v5_state: dict, phase_name: str) -> dict:
    """Extract status info for a v5 phase. V5 uses plain keys (no prefix)."""
    phase = v5_state.get("phases", {}).get(phase_name, {})
    if not phase:
        return {"status": "pending"}
    return {
        "status": phase.get("status", "pending"),
        "ts": phase.get("ts"),
    }


def _has_research_file(track_dir: Path, slug: str) -> bool:
    """Return True if a research file exists for this module."""
    return (track_dir / "research" / f"{slug}-research.md").exists()


def _is_research_done(v3: dict, v2: dict, track_dir: Path | None = None, slug: str | None = None, v4: dict | None = None, v5: dict | None = None) -> bool:
    """Research done if v5/v4 research complete, v3 Phase A complete, v2 phase '1' complete, or research file exists."""
    if v5 and v5.get("phases", {}).get("research", {}).get("status") == "complete":
        return True
    if v4 and v4.get("phases", {}).get("v4-research", {}).get("status") == "complete":
        return True
    if v3.get("phases", {}).get("v3-A", {}).get("status") == "complete":
        return True
    if v2.get("phases", {}).get("1", {}).get("status") == "complete":
        return True
    return bool(track_dir is not None and slug is not None and _has_research_file(track_dir, slug))


def _is_content_done(v3: dict, v2: dict, v4: dict | None = None, v5: dict | None = None) -> bool:
    """Content done if v5/v4 content complete, v3 Phase B complete, OR v2 phase '2' complete."""
    if v5 and v5.get("phases", {}).get("content", {}).get("status") == "complete":
        return True
    if v4 and v4.get("phases", {}).get("v4-content", {}).get("status") == "complete":
        return True
    if v3.get("phases", {}).get("v3-B", {}).get("status") == "complete":
        return True
    return v2.get("phases", {}).get("2", {}).get("status") == "complete"


def _find_content_file(track_dir: Path, slug: str) -> Path | None:
    """Find the module content .md file."""
    for pattern in [f"{slug}.md", f"*-{slug}.md"]:
        matches = list(track_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def _get_audit_status(track_dir: Path, slug: str) -> dict:
    """Read status/{slug}.json. Returns {status, word_count, word_target, blocking_issues}.

    Staleness guard: if the content file is newer than the status cache,
    the audit result is stale — return 'stale' instead of the cached pass/fail.
    """
    status_file = track_dir / "status" / f"{slug}.json"
    if not status_file.exists():
        return {"status": "not_run", "word_count": 0, "word_target": 0, "blocking_issues": []}
    try:
        # Staleness check: content rebuilt after last audit?
        content_file = _find_content_file(track_dir, slug)
        if content_file and content_file.exists():
            content_mtime = content_file.stat().st_mtime
            status_mtime = status_file.stat().st_mtime
            if content_mtime > status_mtime:
                # Content is newer than audit cache — result is stale
                # Still read word count from content for display purposes
                word_count = len(content_file.read_text().split())
                return {
                    "status": "stale",
                    "word_count": word_count,
                    "word_target": 0,
                    "blocking_issues": [],
                    "stale_reason": "content rebuilt after last audit",
                }

        data = json.loads(status_file.read_text())
        overall_status = data.get("overall", {}).get("status", "unknown")

        # Extract word count from lesson gate message
        word_count = 0
        word_target = 0
        lesson_msg = data.get("gates", {}).get("lesson", {}).get("message", "")
        if "/" in str(lesson_msg):
            parts = str(lesson_msg).split("/")
            try:
                word_count = int(parts[0].strip().split()[-1])
            except (ValueError, IndexError):
                # Fallback: count words from the .md file directly
                for md_candidate in track_dir.glob(f"*{slug}*.md"):
                    if md_candidate.is_file():
                        word_count = len(md_candidate.read_text().split())
                        break
            with contextlib.suppress(ValueError, IndexError):
                word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0

        # Collect blocking issues (failed gates)
        blocking_issues = []
        for gate_name, gate_info in data.get("gates", {}).items():
            if isinstance(gate_info, dict) and gate_info.get("status") == "fail":
                blocking_issues.append({
                    "gate": gate_name,
                    "message": gate_info.get("message", ""),
                })
        return {
            "status": overall_status,
            "word_count": word_count,
            "word_target": word_target,
            "blocking_issues": blocking_issues,
        }
    except Exception:
        return {"status": "error", "word_count": 0, "word_target": 0, "blocking_issues": []}


def _get_research_score(track_dir: Path, slug: str, track_id: str) -> int | None:
    """Get research quality score for a module (0-10 or None)."""
    rp = find_research_path(track_dir, slug)
    if not rp:
        return None
    result = assess_research_compat(rp, track_id, None)
    if result and result.get("score") is not None:
        return result["score"]
    return None


def _parse_phase_status(v3_state: dict, phase_key: str) -> dict:
    """Extract status info for a v3 phase key (e.g. 'v3-A')."""
    phase = v3_state.get("phases", {}).get(phase_key, {})
    if not phase:
        return {"status": "pending"}
    return {
        "status": phase.get("status", "pending"),
        "mode": phase.get("mode"),
        "ts": phase.get("ts"),
        "attempts": phase.get("attempts"),
    }


def _get_word_target_from_plan(track_id: str, slug: str) -> int:
    """Try to read word_target from the individual plan YAML file."""
    plan_file = PLANS_ROOT / track_id / f"{slug}.yaml"
    if not plan_file.exists():
        return 0
    try:
        data = yaml.safe_load(plan_file.read_text()) or {}
        return data.get("word_target", 0)
    except Exception:
        return 0


# ==================== SYNC COMPUTE FUNCTIONS (run in thread) ====================

def _compute_summary() -> dict:
    """Synchronous summary computation — safe to run in asyncio.to_thread()."""
    generated_at = datetime.now(UTC).isoformat()
    tracks_out = {}
    totals = {
        "total": 0, "research_done": 0, "content_done": 0,
        "audit_passing": 0, "reviewed": 0, "final_review_done": 0,
        "prompt_reviewed": 0, "content_reviewed": 0,
    }

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = _get_plan_slugs(track_id)
        if not plan_slugs:
            continue

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        profile = PROFILE_MAP.get(track_id, "core")

        research_done = 0
        content_done = 0
        audit_passing = 0
        reviewed = 0
        final_review_done = 0
        prompt_reviewed = 0
        content_reviewed = 0

        audit_dir = track_dir / "audit"
        for _num, slug in plan_slugs:
            orch_dir = track_dir / "orchestration" / slug
            v2 = _read_v2_state(orch_dir)
            v5 = v2 if v2.get("mode") == "v5" else None
            v4 = _read_v4_state(orch_dir) if not v5 else {}
            v3 = _read_v3_state(orch_dir) if not v5 else {}

            if _is_research_done(v3, v2, track_dir, slug, v4=v4, v5=v5):
                research_done += 1
            if _is_content_done(v3, v2, v4=v4, v5=v5):
                content_done += 1

            audit = _get_audit_status(track_dir, slug)
            if audit["status"] == "pass":
                audit_passing += 1

            review_file = track_dir / "review" / f"{slug}-review.md"
            if review_file.exists():
                reviewed += 1
            final_review = track_dir / "review" / f"{slug}-final-review.md"
            if final_review.exists():
                final_review_done += 1
            if (audit_dir / f"{slug}-prompt-review.md").exists():
                prompt_reviewed += 1
            if (audit_dir / f"{slug}-content-review.md").exists():
                content_reviewed += 1

        total = len(plan_slugs)
        tracks_out[track_id] = {
            "total": total,
            "profile": profile,
            "research_done": research_done,
            "content_done": content_done,
            "audit_passing": audit_passing,
            "reviewed": reviewed,
            "final_review_done": final_review_done,
            "prompt_reviewed": prompt_reviewed,
            "content_reviewed": content_reviewed,
        }

        totals["total"] += total
        totals["research_done"] += research_done
        totals["content_done"] += content_done
        totals["audit_passing"] += audit_passing
        totals["reviewed"] += reviewed
        totals["final_review_done"] += final_review_done
        totals["prompt_reviewed"] += prompt_reviewed
        totals["content_reviewed"] += content_reviewed

    return {"generated_at": generated_at, "tracks": tracks_out, "totals": totals}


def _compute_pipeline_track(track_id: str, level_cfg: dict) -> dict:
    """Sync computation for pipeline/{track}."""
    plan_slugs = _get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    modules = []

    for num, slug in plan_slugs:
        orch_dir = track_dir / "orchestration" / slug
        version = _detect_pipeline_version(orch_dir)

        audit = _get_audit_status(track_dir, slug)
        research_score = _get_research_score(track_dir, slug, track_id)

        word_count = audit.get("word_count", 0)
        word_target = audit.get("word_target", 0)
        if word_target == 0:
            word_target = _get_word_target_from_plan(track_id, slug)

        if version == "v5":
            v5 = _read_v2_state(orch_dir)  # v5 uses state.json
            phases = {
                name: _parse_v5_phase_status(v5, name)
                for name in V5_PHASE_ORDER
            }
            modules.append({
                "num": num,
                "slug": slug,
                "pipeline_version": "v5",
                "needs_rebuild": False,
                "phases": phases,
                "audit": audit["status"],
                "words": word_count,
                "word_target": word_target,
                "research_score": research_score,
                "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
                "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
            })
        elif version == "v4":
            v4 = _read_v4_state(orch_dir)
            phases = {
                name: _parse_v4_phase_status(v4, name)
                for name in V4_PHASE_ORDER
            }
            modules.append({
                "num": num,
                "slug": slug,
                "pipeline_version": "v4",
                "needs_rebuild": False,
                "phases": phases,
                "audit": audit["status"],
                "words": word_count,
                "word_target": word_target,
                "research_score": research_score,
                "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
                "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
            })
        else:
            v3 = _read_v3_state(orch_dir)
            v2 = _read_v2_state(orch_dir)

            # For phase chip display: if v3-A is empty but v2 phase 1 is complete,
            # synthesise a v3-A entry so the chip shows correctly.
            if not v3.get("phases", {}).get("v3-A") and v2.get("phases", {}).get("1", {}).get("status") == "complete":
                v3.setdefault("phases", {})["v3-A"] = {
                    "status": "complete",
                    "mode": "v2-adopted",
                    "ts": v2["phases"]["1"].get("timestamp"),
                }
            if not v3.get("phases", {}).get("v3-B") and v2.get("phases", {}).get("2", {}).get("status") == "complete":
                v3.setdefault("phases", {})["v3-B"] = {
                    "status": "complete",
                    "mode": "v2-adopted",
                    "ts": v2["phases"]["2"].get("timestamp"),
                }

            modules.append({
                "num": num,
                "slug": slug,
                "pipeline_version": "v3" if version == "v3" else "unbuilt",
                "needs_rebuild": True,
                "phases": {
                    "A": _parse_phase_status(v3, "v3-A"),
                    "B": _parse_phase_status(v3, "v3-B"),
                    "C": _parse_phase_status(v3, "v3-C"),
                    "audit": _parse_phase_status(v3, "v3-audit"),
                    "D": _parse_phase_status(v3, "v3-D"),
                },
                "audit": audit["status"],
                "words": word_count,
                "word_target": word_target,
                "research_score": research_score,
                "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
                "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
            })

    return {"track": track_id, "total": len(modules), "modules": modules}


def _compute_research_coverage() -> dict:
    """Sync research coverage computation."""
    tracks_out = {}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = _get_plan_slugs(track_id)
        if not plan_slugs:
            continue

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        total = len(plan_slugs)
        has_research = 0
        quality_counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0}
        scores = []
        needs_upgrade = 0

        for _num, slug in plan_slugs:
            rp = find_research_path(track_dir, slug)
            if not rp:
                continue
            result = assess_research_compat(rp, track_id, None)
            if not result or not result.get("exists"):
                continue
            has_research += 1
            quality = result.get("quality")
            if quality in quality_counts:
                quality_counts[quality] += 1
            score = result.get("score")
            if score is not None:
                scores.append(score)
            if score is not None and score < 7:
                needs_upgrade += 1

        pct_coverage = round(has_research / total * 100) if total > 0 else 0
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        tracks_out[track_id] = {
            "total_modules": total,
            "has_research": has_research,
            "pct_coverage": pct_coverage,
            "quality": quality_counts,
            "avg_score": avg_score,
            "needs_upgrade": needs_upgrade,
        }

    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks_out}


def _compute_review_coverage() -> dict:
    """Sync review coverage computation."""
    tracks_out = {}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = _get_plan_slugs(track_id)
        if not plan_slugs:
            continue

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        review_dir = track_dir / "review"

        total_built = 0
        has_review = 0
        has_final_review = 0
        scores = []
        pass_count = 0
        total_issues = 0

        # Plan review counters
        audit_dir = track_dir / "audit"
        plan_reviewed = 0
        plan_pass = 0
        plan_needs_fixes = 0
        plan_fail = 0

        for num, slug in plan_slugs:
            md_exists = any([
                (track_dir / f"{slug}.md").exists(),
                (track_dir / f"{num:02d}-{slug}.md").exists(),
                (track_dir / f"{num}-{slug}.md").exists(),
            ])
            if md_exists:
                total_built += 1

            review_file = review_dir / f"{slug}-review.md"
            final_review_file = review_dir / f"{slug}-final-review.md"

            if review_file.exists():
                has_review += 1
                text = review_file.read_text()
                score = extract_review_score(text)
                verdict = extract_review_verdict(text)

                if score is not None:
                    scores.append(score)
                if verdict == "PASS":
                    pass_count += 1
                total_issues += count_review_issues(text)

            if final_review_file.exists():
                has_final_review += 1

            # Plan review
            plan_review_file = audit_dir / f"{slug}-plan-review.md"
            if plan_review_file.exists():
                plan_reviewed += 1
                try:
                    pr_text = plan_review_file.read_text(errors="replace")
                    v = extract_plan_verdict(pr_text)
                    if v == "PASS":
                        plan_pass += 1
                    elif v == "NEEDS FIXES":
                        plan_needs_fixes += 1
                    elif v == "FAIL":
                        plan_fail += 1
                except Exception:
                    pass

        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        pass_rate = round(pass_count / has_review, 2) if has_review > 0 else None

        tracks_out[track_id] = {
            "total_built": total_built,
            "has_review": has_review,
            "has_final_review": has_final_review,
            "avg_score": avg_score,
            "pass_rate": pass_rate,
            "total_issues_found": total_issues,
            "plan_reviewed": plan_reviewed,
            "plan_pass": plan_pass,
            "plan_needs_fixes": plan_needs_fixes,
            "plan_fail": plan_fail,
        }

    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks_out}


# ==================== ENDPOINTS ====================


@router.get("/summary")
async def state_summary():
    """Full project snapshot. One call replaces 5 bash scripts at session start."""
    cached = _cache_get("summary", ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_summary)
    _cache_set("summary", result)
    return result


@router.get("/pipeline/{track_id}")
async def pipeline_track(track_id: str):
    """Per-module v3 phase state for one track."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"pipeline_{track_id}"
    cached = _cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_pipeline_track, track_id, level_cfg)
    _cache_set(cache_key, result)
    return result


@router.get("/pipeline-versions")
async def pipeline_versions(track: str | None = Query(None)):
    """All modules grouped by pipeline version."""
    def _compute():
        counts = {"v5": 0, "v4": 0, "v3": 0, "unbuilt": 0}
        by_version: dict[str, list] = {"v5": [], "v4": [], "v3": [], "unbuilt": []}
        per_track: dict[str, dict] = {}

        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            if not plan_slugs:
                continue

            track_dir = CURRICULUM_ROOT / level_cfg["path"]
            track_counts = {"v5": 0, "v4": 0, "v3": 0, "unbuilt": 0}

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                version = _detect_pipeline_version(orch_dir)
                counts[version] += 1
                track_counts[version] += 1
                by_version[version].append({
                    "track": track_id, "num": num, "slug": slug,
                })

            per_track[track_id] = track_counts

        total = sum(counts.values())
        built = counts["v5"] + counts["v4"]
        return {
            "total": total,
            "counts": counts,
            "pct_v5": round(counts["v5"] / total * 100) if total else 0,
            "pct_built": round(built / total * 100) if total else 0,
            "needs_rebuild": counts["v3"] + counts["unbuilt"],
            "per_track": per_track,
            "v5_modules": by_version["v5"],
            "v4_modules": by_version["v4"],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    cache_key = f"pipeline_versions_{track or 'all'}"
    cached = _cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set(cache_key, result)
    return result


@router.get("/ready-to-build")
async def ready_to_build(track: str | None = Query(None)):
    """Modules where Phase A is complete but Phase B hasn't started. The build queue."""
    def _compute():
        ready = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                v4 = _read_v4_state(orch_dir)
                v3 = _read_v3_state(orch_dir)
                v2 = _read_v2_state(orch_dir)

                if _is_research_done(v3, v2, track_dir, slug, v4=v4) and not _is_content_done(v3, v2, v4=v4):
                    version = _detect_pipeline_version(orch_dir)
                    if version == "v4":
                        research_phase = v4.get("phases", {}).get("v4-research", {})
                        ready.append({
                            "track": track_id,
                            "num": num,
                            "slug": slug,
                            "pipeline_version": "v4",
                            "phase_a_ts": research_phase.get("ts"),
                            "phase_a_mode": None,
                        })
                    else:
                        phase_a = v3.get("phases", {}).get("v3-A") or v2.get("phases", {}).get("1") or {}
                        ready.append({
                            "track": track_id,
                            "num": num,
                            "slug": slug,
                            "pipeline_version": version,
                            "phase_a_ts": phase_a.get("ts") or phase_a.get("timestamp"),
                            "phase_a_mode": phase_a.get("mode"),
                        })
        return {"count": len(ready), "modules": ready}

    return await asyncio.to_thread(_compute)


@router.get("/weak-points")
async def weak_points(
    track: str | None = Query(None),
    min_score: int = Query(7, ge=0, le=10),
    limit: int = Query(20, ge=1, le=500),
):
    """Modules with quality issues: failing audit, thin research, or low word count."""
    def _compute():
        weak = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                issues = []
                audit = _get_audit_status(track_dir, slug)

                if audit["status"] == "fail":
                    issues.append("audit_fail")

                # Only score research when a track filter is active — too expensive for 1500+ modules
                research_score = _get_research_score(track_dir, slug, track_id) if track else None
                if research_score is not None and research_score < min_score:
                    issues.append(f"research_score_{research_score}")

                word_count = audit.get("word_count", 0)
                word_target = audit.get("word_target", 0)
                if word_target == 0:
                    word_target = _get_word_target_from_plan(track_id, slug)
                if word_target > 0 and word_count > 0 and word_count < word_target * 0.8:
                    issues.append(f"low_words_{word_count}/{word_target}")

                if issues:
                    orch_dir = track_dir / "orchestration" / slug
                    version = _detect_pipeline_version(orch_dir)
                    weak.append({
                        "track": track_id,
                        "num": num,
                        "slug": slug,
                        "audit_status": audit["status"],
                        "word_count": word_count,
                        "word_target": word_target,
                        "research_score": research_score,
                        "pipeline_version": version,
                        "issues": issues,
                    })

        def severity_key(m):
            score = 0
            for issue in m["issues"]:
                if "audit_fail" in issue:
                    score += 100
                elif "research_score" in issue:
                    score += 50
                elif "low_words" in issue:
                    score += 10
            return -score

        weak.sort(key=severity_key)
        return {"count": len(weak), "modules": weak[:limit]}

    return await asyncio.to_thread(_compute)


@router.get("/failing")
async def failing_modules(track: str | None = Query(None)):
    """All modules with audit failures or phase failures."""
    def _compute():
        failing = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]

            for num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                version = _detect_pipeline_version(orch_dir)
                audit = _get_audit_status(track_dir, slug)

                if version == "v4":
                    v4 = _read_v4_state(orch_dir)
                    phases = v4.get("phases", {})
                    failed_phases = [
                        k.replace("v4-", "") for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]
                else:
                    v3 = _read_v3_state(orch_dir)
                    phases = v3.get("phases", {})
                    failed_phases = [
                        k.replace("v3-", "") for k, v in phases.items()
                        if isinstance(v, dict) and v.get("status") == "failed"
                    ]

                if audit["status"] == "fail" or failed_phases:
                    failing.append({
                        "track": track_id,
                        "num": num,
                        "slug": slug,
                        "pipeline_version": version,
                        "audit_status": audit["status"],
                        "failed_phases": failed_phases,
                        "blocking_issues": audit.get("blocking_issues", []),
                    })

        return {"count": len(failing), "modules": failing}

    return await asyncio.to_thread(_compute)


@router.get("/research-coverage")
async def research_coverage():
    """Per-track research completeness and quality."""
    cached = _cache_get("research_coverage", ttl=300.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_research_coverage)
    _cache_set("research_coverage", result)
    return result


@router.get("/research/{track_id}")
async def research_detail(track_id: str, min_score: int = 9):
    """Per-module research quality with dimension scores, gaps, and upgrade queue.

    Query params:
      min_score: threshold for upgrade queue (default 9)
    """
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    cache_key = f"research_detail_{track_id}_{min_score}"
    cached = _cache_get(cache_key, ttl=120.0)
    if cached is not None:
        return cached

    def _compute():
        from research_quality import (
            DIMENSION_SHORT_LABELS,
            assess_research_compat,
            find_research_path,
            get_dimensions,
            get_rubric,
        )

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        plan_slugs = _get_plan_slugs(track_id)
        rubric_name = get_rubric(track_id)
        dimensions = get_dimensions(rubric_name) if rubric_name else []

        modules = []
        upgrade_queue = []
        quality_counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0, "missing": 0}
        scores = []

        for num, slug in plan_slugs:
            rp = find_research_path(track_dir, slug)
            if not rp:
                modules.append({
                    "num": num, "slug": slug, "exists": False,
                    "score": None, "quality": None, "dimensions": None, "gaps": None,
                })
                quality_counts["missing"] += 1
                upgrade_queue.append({"num": num, "slug": slug, "score": None, "gaps": ["missing"]})
                continue

            # Assess with content alignment
            content_path = None
            for pattern in [f"{slug}.md", f"*-{slug}.md"]:
                matches = list(track_dir.glob(pattern))
                if matches:
                    content_path = matches[0]
                    break

            info = assess_research_compat(rp, track_id, content_path)
            if not info or not info.get("exists"):
                modules.append({
                    "num": num, "slug": slug, "exists": False,
                    "score": None, "quality": None, "dimensions": None, "gaps": None,
                })
                quality_counts["missing"] += 1
                upgrade_queue.append({"num": num, "slug": slug, "score": None, "gaps": ["missing"]})
                continue

            score = info.get("score")
            quality = info.get("quality")
            dims = info.get("dimensions") or {}
            gaps = info.get("gaps") or []
            alignment = info.get("content_alignment")

            mod_entry = {
                "num": num,
                "slug": slug,
                "exists": True,
                "words": info.get("words", 0),
                "score": score,
                "quality": quality,
                "dimensions": {
                    k: {"score": v["score"], "max": v["max"], "detail": v["detail"]}
                    for k, v in dims.items()
                } if dims else None,
                "gaps": gaps,
                "content_alignment": alignment,
            }
            modules.append(mod_entry)

            if quality and quality in quality_counts:
                quality_counts[quality] += 1
            if score is not None:
                scores.append(score)
                if score < min_score:
                    upgrade_queue.append({
                        "num": num, "slug": slug, "score": score,
                        "gaps": [g.split(":")[0] for g in gaps],
                    })

        # Sort upgrade queue by score ascending (weakest first)
        upgrade_queue.sort(key=lambda x: (x["score"] if x["score"] is not None else -1))

        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        return {
            "track": track_id,
            "rubric": rubric_name,
            "dimensions": dimensions,
            "dimension_labels": {d: DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dimensions} if dimensions else {},
            "total": len(plan_slugs),
            "researched": len(scores),
            "avg_score": avg_score,
            "quality_distribution": quality_counts,
            "upgrade_queue": upgrade_queue,
            "upgrade_count": len(upgrade_queue),
            "min_score_threshold": min_score,
            "modules": modules,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    result = await asyncio.to_thread(_compute)
    _cache_set(cache_key, result)
    return result


@router.get("/review-coverage")
async def review_coverage():
    """Per-track review and final-review coverage + quality signal."""
    cached = _cache_get("review_coverage", ttl=300.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_review_coverage)
    _cache_set("review_coverage", result)
    return result


@router.get("/build-status/{track_id}")
async def build_status(track_id: str):
    """Compact build progress for a track. One call tells you everything.

    Returns: currently building (module + phase), done/total counts,
    last 5 completions with pass/fail, and ETA.
    """
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    def _compute():
        plan_slugs = _get_plan_slugs(track_id)
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        total = len(plan_slugs)

        building_now = []
        done = 0
        queued = 0
        failed = 0
        recent_completions = []

        for num, slug in plan_slugs:
            orch_dir = track_dir / "orchestration" / slug
            version = _detect_pipeline_version(orch_dir)

            # Determine furthest completed phase and any running phase
            furthest = None
            running_phase = None
            latest_ts = None

            if version == "v5":
                v5 = _read_v2_state(orch_dir)
                phases = v5.get("phases", {})
                phase_names = V5_PHASE_ORDER
                for pid in phase_names:
                    p = phases.get(pid, {})
                    status = p.get("status")
                    if status == "complete":
                        furthest = pid
                        ts = p.get("ts")
                        if ts:
                            latest_ts = ts
                    elif status == "running":
                        running_phase = pid
                    elif status == "failed":
                        running_phase = pid + "(FAIL)"
                audit_status = phases.get("validate", {}).get("status")
            else:
                v3 = _read_v3_state(orch_dir)
                phases = v3.get("phases", {})
                for pid in ["v3-A", "v3-B", "v3-C", "v3-audit", "v3-D", "v3-E", "v3-F"]:
                    p = phases.get(pid, {})
                    status = p.get("status")
                    if status == "complete":
                        furthest = pid.replace("v3-", "")
                        ts = p.get("ts")
                        if ts:
                            latest_ts = ts
                    elif status == "running":
                        running_phase = pid.replace("v3-", "")
                    elif status == "failed":
                        running_phase = pid.replace("v3-", "") + "(FAIL)"
                audit_status = phases.get("v3-audit", {}).get("status")

            if audit_status == "complete":
                done += 1
                audit_result = _get_audit_status(track_dir, slug)
                wc = audit_result.get("word_count", 0)
                wt = audit_result.get("word_target", 0)
                recent_completions.append({
                    "num": num,
                    "slug": slug,
                    "phase": furthest or "audit",
                    "audit": audit_result.get("status", "unknown"),
                    "words": f"{wc}/{wt}",
                    "ts": latest_ts,
                })
            elif running_phase:
                building_now.append({
                    "num": num,
                    "slug": slug,
                    "phase": running_phase,
                    "prev": furthest,
                })
            elif audit_status == "failed":
                failed += 1
            elif furthest:
                # Partially done but not running — stalled or queued for next phase
                building_now.append({
                    "num": num,
                    "slug": slug,
                    "phase": f"queued-after-{furthest}",
                    "prev": furthest,
                })
            else:
                queued += 1

        # Sort completions by timestamp, take last 5
        recent_completions.sort(key=lambda x: x.get("ts") or "", reverse=True)
        last_5 = recent_completions[:5]

        return {
            "track": track_id,
            "total": total,
            "done": done,
            "building": len(building_now),
            "queued": queued,
            "failed": failed,
            "progress": f"{done}/{total} ({round(done/total*100) if total else 0}%)",
            "currently_building": building_now[:5],  # Top 5 active
            "recent_completions": last_5,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    cache_key = f"build_status_{track_id}"
    cached = _cache_get(cache_key, ttl=15.0)  # Short TTL — this is for live monitoring
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set(cache_key, result)
    return result


@router.get("/build-status")
async def build_status_all():
    """All-tracks build progress in one call. Shows done/total per active track."""
    def _compute():
        tracks = {}
        for level_cfg in LEVELS:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            if not plan_slugs:
                continue
            track_dir = CURRICULUM_ROOT / level_cfg["path"]
            total = len(plan_slugs)
            done = 0
            building = 0
            failed = 0

            for _num, slug in plan_slugs:
                orch_dir = track_dir / "orchestration" / slug
                v3 = _read_v3_state(orch_dir)
                phases = v3.get("phases", {})
                audit_status = phases.get("v3-audit", {}).get("status")
                if audit_status == "complete":
                    done += 1
                elif audit_status == "failed":
                    failed += 1
                elif any(phases.get(p, {}).get("status") == "running"
                         for p in ["v3-A", "v3-B", "v3-C", "v3-audit", "v3-D", "v3-E", "v3-F"]):
                    building += 1

            tracks[track_id] = {
                "total": total,
                "done": done,
                "building": building,
                "failed": failed,
                "progress": f"{done}/{total} ({round(done/total*100) if total else 0}%)",
            }

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "tracks": tracks,
        }

    cached = _cache_get("build_status_all", ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set("build_status_all", result)
    return result


def _get_broker_messages_for_slug(slug: str, limit: int = 20) -> list[dict]:
    """Query broker DB for messages related to a module slug."""
    if not MESSAGE_DB.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{MESSAGE_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, task_id, from_llm, to_llm, message_type, "
            "substr(content, 1, 200) as preview, timestamp "
            "FROM messages WHERE task_id LIKE ? "
            "ORDER BY id DESC LIMIT ?",
            (f"%{slug}%", limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_final_review_info(track_dir: Path, slug: str) -> dict | None:
    """Parse final review file for verdict and issue count."""
    review_file = track_dir / "review" / f"{slug}-final-review.md"
    if not review_file.exists():
        return None
    try:
        text = review_file.read_text()
        # Extract verdict
        verdict = None
        verdict_match = re.search(r"===VERDICT===\s*(\w+)\s*===END_VERDICT===", text)
        if verdict_match:
            verdict = verdict_match.group(1).strip()

        # Count issues
        issue_count = len(re.findall(
            r"\*\*ISSUE\s+\d+", text, re.IGNORECASE
        ))

        # Extract issue summaries
        issues = []
        for m in re.finditer(
            r"\*\*ISSUE\s+(\d+)\s*[—–-]\s*([^*]+)\*\*",
            text, re.IGNORECASE
        ):
            issues.append({
                "num": int(m.group(1)),
                "summary": m.group(2).strip()[:120],
            })

        return {
            "verdict": verdict,
            "issue_count": issue_count,
            "issues": issues,
            "file": str(review_file.relative_to(CURRICULUM_ROOT)),
        }
    except Exception:
        return None


@router.get("/module/{track_id}/{num}")
async def module_detail(track_id: str, num: int):
    """Single module deep-dive: pipeline state, audit, research, review, comms."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    def _compute():
        plan_slugs = _get_plan_slugs(track_id)
        match = next(((n, s) for n, s in plan_slugs if n == num), None)
        if not match:
            return {"error": f"Module #{num} not found in track '{track_id}'"}
        _, slug = match
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        orch_dir = track_dir / "orchestration" / slug

        version = _detect_pipeline_version(orch_dir)

        # Pipeline phases — v5 uses plain keys, v4 uses v4- prefix, v3 uses letter-coded
        if version == "v5":
            v5 = _read_v2_state(orch_dir)
            phases = {
                name: _parse_v5_phase_status(v5, name)
                for name in V5_PHASE_ORDER
            }
        elif version == "v4":
            v4 = _read_v4_state(orch_dir)
            phases = {
                name: _parse_v4_phase_status(v4, name)
                for name in V4_PHASE_ORDER
            }
        else:
            v3 = _read_v3_state(orch_dir)
            phases = {}
            for pid in ["A", "B", "C", "audit", "D", "E", "F"]:
                phases[pid] = _parse_phase_status(v3, f"v3-{pid}")

        # Audit
        audit = _get_audit_status(track_dir, slug)

        # Research
        research_score = _get_research_score(track_dir, slug, track_id)
        has_research = _has_research_file(track_dir, slug)

        # Review files
        review_file = track_dir / "review" / f"{slug}-review.md"
        has_review = review_file.exists()

        # Claude quality reviews (prompt-review + content-review)
        prompt_review_file = track_dir / "audit" / f"{slug}-prompt-review.md"
        content_review_file = track_dir / "audit" / f"{slug}-content-review.md"
        has_prompt_review = prompt_review_file.exists()
        has_content_review = content_review_file.exists()

        # Final review
        final_review = _get_final_review_info(track_dir, slug)

        # Content file
        word_count = audit.get("word_count", 0)
        word_target = audit.get("word_target", 0)
        if word_target == 0:
            word_target = _get_word_target_from_plan(track_id, slug)

        # Enrichment status (check for .yaml.bak)
        plan_file = PLANS_ROOT / track_id / f"{slug}.yaml"
        enriched = (plan_file.with_suffix(".yaml.bak")).exists()

        # Related broker messages
        comms = _get_broker_messages_for_slug(slug, limit=15)

        return {
            "track": track_id,
            "num": num,
            "slug": slug,
            "pipeline_version": version,
            "needs_rebuild": version != "v4",
            "phases": phases,
            "audit": {
                "status": audit["status"],
                "word_count": word_count,
                "word_target": word_target,
                "blocking_issues": audit.get("blocking_issues", []),
            },
            "research": {
                "exists": has_research,
                "score": research_score,
            },
            "review": {
                "exists": has_review,
            },
            "prompt_review": has_prompt_review,
            "content_review": has_content_review,
            "final_review": final_review,
            "enriched": enriched,
            "comms": comms,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    result = await asyncio.to_thread(_compute)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result


@router.get("/final-reviews/{track_id}")
async def final_reviews_track(track_id: str):
    """Phase F results aggregated per track: verdicts, issue counts, common patterns."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    def _compute():
        plan_slugs = _get_plan_slugs(track_id)
        track_dir = CURRICULUM_ROOT / level_cfg["path"]

        approved = []
        rejected = []
        pending = []
        all_issues = []

        for num, slug in plan_slugs:
            info = _get_final_review_info(track_dir, slug)
            if info is None:
                # Check if module is built but lacks final review
                orch_dir = track_dir / "orchestration" / slug
                v3 = _read_v3_state(orch_dir)
                if v3.get("phases", {}).get("v3-audit", {}).get("status") == "complete":
                    pending.append({"num": num, "slug": slug})
                continue

            entry = {"num": num, "slug": slug, **info}
            if info["verdict"] == "APPROVE":
                approved.append(entry)
            else:
                rejected.append(entry)
                for issue in info.get("issues", []):
                    all_issues.append({
                        "module": slug,
                        "num": num,
                        **issue,
                    })

        # Count issue patterns
        pattern_counts = {}
        for issue in all_issues:
            summary = issue["summary"].upper()
            for keyword in ["FACTUAL", "PLAN COMPLIANCE", "ACTIVITY", "ANTI-SURZHYK",
                           "PRONUNCIATION", "MISLEADING", "COLONIAL", "WORD COUNT",
                           "MISSING", "RUSSICISM"]:
                if keyword in summary:
                    pattern_counts[keyword] = pattern_counts.get(keyword, 0) + 1

        return {
            "track": track_id,
            "total_reviewed": len(approved) + len(rejected),
            "approved": len(approved),
            "rejected": len(rejected),
            "pending_review": len(pending),
            "approval_rate": (
                f"{round(len(approved) / (len(approved) + len(rejected)) * 100)}%"
                if (len(approved) + len(rejected)) > 0 else "N/A"
            ),
            "issue_patterns": pattern_counts,
            "rejected_modules": rejected,
            "pending_modules": pending[:10],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    cache_key = f"final_reviews_{track_id}"
    cached = _cache_get(cache_key, ttl=60.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set(cache_key, result)
    return result


@router.get("/enrichment-status")
async def enrichment_status(track: str | None = Query(None)):
    """Which plans are enriched per track. Checks for .yaml.bak files in plans/."""
    def _compute():
        tracks = {}
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS
        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            if not plan_slugs:
                continue
            plan_dir = PLANS_ROOT / track_id
            enriched = 0
            not_enriched = []
            for _num, slug in plan_slugs:
                bak = plan_dir / f"{slug}.yaml.bak"
                if bak.exists():
                    enriched += 1
                else:
                    not_enriched.append(slug)
            total = len(plan_slugs)
            tracks[track_id] = {
                "total": total,
                "enriched": enriched,
                "pending": total - enriched,
                "pct": round(enriched / total * 100) if total else 0,
                "not_enriched": not_enriched[:10] if len(not_enriched) <= 10 else [*not_enriched[:5], f"...+{len(not_enriched) - 5}"],
            }
        return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks}

    cached = _cache_get("enrichment_status", ttl=120.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set("enrichment_status", result)
    return result


@router.get("/track-health/{track_id}")
async def track_health(track_id: str):
    """Single-call track health: build progress, audit, final review, enrichment, word quality, attention list."""
    level_cfg = next((l for l in LEVELS if l["id"] == track_id), None)
    if not level_cfg:
        return JSONResponse(status_code=404, content={"error": f"Track '{track_id}' not found"})

    def _compute():
        plan_slugs = _get_plan_slugs(track_id)
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        plan_dir = PLANS_ROOT / track_id
        total = len(plan_slugs)

        # Counters
        built = 0
        audit_pass = 0
        audit_fail = 0
        enriched = 0
        final_reviewed = 0
        final_approved = 0
        word_ratios = []
        attention = []
        completion_times = []  # For ETA

        for num, slug in plan_slugs:
            orch_dir = track_dir / "orchestration" / slug
            v3 = _read_v3_state(orch_dir)
            phases = v3.get("phases", {})

            # Built = Phase B complete
            b_phase = phases.get("v3-B", {})
            if b_phase.get("status") == "complete":
                built += 1
                # Record completion timestamp for ETA calc
                ts = b_phase.get("ts")
                if ts:
                    completion_times.append(ts)

            # Audit
            audit = _get_audit_status(track_dir, slug)
            if audit["status"] == "pass":
                audit_pass += 1
            elif audit["status"] == "fail":
                audit_fail += 1
                attention.append({
                    "num": num, "slug": slug,
                    "reason": "audit_fail",
                    "detail": (audit.get("blocking_issues", [{}])[0].get("gate", "")
                              if audit.get("blocking_issues") else ""),
                })

            # Word ratio
            wc = audit.get("word_count", 0)
            wt = audit.get("word_target", 0)
            if wt > 0 and wc > 0:
                word_ratios.append(wc / wt)

            # Enrichment
            if (plan_dir / f"{slug}.yaml.bak").exists():
                enriched += 1

            # Final review
            fr = _get_final_review_info(track_dir, slug)
            if fr:
                final_reviewed += 1
                if fr["verdict"] == "APPROVE":
                    final_approved += 1
                else:
                    attention.append({
                        "num": num, "slug": slug,
                        "reason": f"final_review_{fr['verdict']}",
                        "detail": f"{fr['issue_count']} issues",
                    })

        # ETA calculation
        eta_minutes = None
        remaining = total - built
        if len(completion_times) >= 3:
            # Sort timestamps, compute rate from last 10
            sorted_ts = sorted(completion_times)
            recent = sorted_ts[-min(10, len(sorted_ts)):]
            if len(recent) >= 2:
                try:
                    first = datetime.fromisoformat(recent[0].replace("Z", "+00:00"))
                    last = datetime.fromisoformat(recent[-1].replace("Z", "+00:00"))
                    elapsed = (last - first).total_seconds()
                    if elapsed > 0:
                        rate_per_min = (len(recent) - 1) / (elapsed / 60)
                        if rate_per_min > 0:
                            eta_minutes = round(remaining / rate_per_min)
                except Exception:
                    pass

        avg_word_ratio = round(sum(word_ratios) / len(word_ratios), 2) if word_ratios else None

        # Sort attention by severity
        attention.sort(key=lambda x: 0 if "fail" in x["reason"] else 1)

        return {
            "track": track_id,
            "total": total,
            "build": {"done": built, "pct": round(built / total * 100) if total else 0},
            "audit": {
                "passing": audit_pass,
                "failing": audit_fail,
                "pct": round(audit_pass / total * 100) if total else 0,
            },
            "enrichment": {
                "done": enriched,
                "pct": round(enriched / total * 100) if total else 0,
            },
            "final_review": {
                "reviewed": final_reviewed,
                "approved": final_approved,
                "approval_rate": (
                    f"{round(final_approved / final_reviewed * 100)}%"
                    if final_reviewed else "N/A"
                ),
            },
            "words": {
                "avg_ratio": f"{avg_word_ratio}x" if avg_word_ratio else "N/A",
            },
            "eta": {
                "remaining": remaining,
                "minutes": eta_minutes,
                "display": (
                    f"~{eta_minutes}min ({eta_minutes//60}h{eta_minutes%60:02d}m)"
                    if eta_minutes else "N/A"
                ),
            },
            "attention": attention[:10],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    cache_key = f"track_health_{track_id}"
    cached = _cache_get(cache_key, ttl=30.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute)
    _cache_set(cache_key, result)
    return result


@router.get("/issues")
async def outstanding_issues(
    track: str | None = Query(None),
    severity: str | None = Query(None),
):
    """Aggregated outstanding issues from review files + audit failures."""
    def _compute():
        issues = []
        level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

        CRITICAL_KEYWORDS = {
            "factual error", "factual mistake", "incorrect", "wrong",
            "grammar error", "grammatical error", "activity error",
            "missing section", "critical",
        }

        for level_cfg in level_cfgs:
            track_id = level_cfg["id"]
            plan_slugs = _get_plan_slugs(track_id)
            track_dir = CURRICULUM_ROOT / level_cfg["path"]
            review_dir = track_dir / "review"

            for num, slug in plan_slugs:
                # --- Source 1: Review file issues ---
                # Find content file to check staleness
                content_file = None
                for pattern in [f"{slug}.md", f"*-{slug}.md"]:
                    matches = list(track_dir.glob(pattern))
                    if matches:
                        content_file = matches[0]
                        break
                for review_filename in [f"{slug}-review.md", f"{slug}-final-review.md"]:
                    review_file = review_dir / review_filename
                    if not review_file.exists():
                        continue

                    # Skip stale reviews: content changed since review was written (#618)
                    if _is_review_stale(review_file, content_file):
                        continue

                    text = review_file.read_text()
                    # Permissive split: handles #, ##, ###, ####, "Issue #N", "Issue N"
                    issue_blocks = re.split(
                        r"(?=^#{1,4}\s+Issue\s*#?\s*\d+)",
                        text, flags=re.MULTILINE | re.IGNORECASE
                    )
                    for block in issue_blocks:
                        if not re.match(r"^#{1,4}\s+Issue\s*#?\s*\d+", block, re.IGNORECASE):
                            continue

                        title_match = re.match(
                            r"^#{1,4}\s+Issue\s*#?\s*\d+[:\s—-]*(.+?)$",
                            block, re.MULTILINE | re.IGNORECASE
                        )
                        title = title_match.group(1).strip() if title_match else "Issue"

                        # Support both **bold** and __bold__ for field labels
                        loc_match = re.search(
                            r"(?:\*\*|__)Location(?:\*\*|__)[:\s]+(.+?)(?:\n|$)",
                            block, re.IGNORECASE
                        )
                        location = loc_match.group(1).strip() if loc_match else ""

                        fix_match = re.search(
                            r"(?:\*\*|__)Fix(?:\*\*|__)[:\s]+(.+?)(?:\n\n|\Z)",
                            block, re.IGNORECASE | re.DOTALL
                        )
                        fix = fix_match.group(1).strip()[:200] if fix_match else ""

                        combined = (title + " " + block[:300]).lower()
                        issue_severity = "warning"
                        for kw in CRITICAL_KEYWORDS:
                            if kw in combined:
                                issue_severity = "critical"
                                break

                        source_type = "final-review" if "final-review" in review_filename else "review"
                        issues.append({
                            "track": track_id,
                            "slug": slug,
                            "num": num,
                            "source": source_type,
                            "severity": issue_severity,
                            "title": title[:80],
                            "location": location[:120],
                            "fix": fix,
                        })

                # --- Source 2: Audit failures ---
                audit = _get_audit_status(track_dir, slug)
                if audit["status"] == "fail":
                    for blocking in audit.get("blocking_issues", []):
                        issues.append({
                            "track": track_id,
                            "slug": slug,
                            "num": num,
                            "source": "audit",
                            "severity": "critical",
                            "title": f"Audit gate failed: {blocking.get('gate', 'unknown')}",
                            "location": blocking.get("gate", ""),
                            "fix": blocking.get("message", "")[:200],
                        })

        if severity:
            issues = [i for i in issues if i["severity"] == severity]

        by_severity: dict[str, int] = {}
        for issue in issues:
            s = issue["severity"]
            by_severity[s] = by_severity.get(s, 0) + 1

        return {"total": len(issues), "by_severity": by_severity, "issues": issues}

    return await asyncio.to_thread(_compute)
