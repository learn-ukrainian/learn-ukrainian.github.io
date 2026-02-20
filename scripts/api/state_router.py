"""
State API router — v3 pipeline state, research/review coverage, weak points, issues.

Mounted at /api/state/ in main.py.

Endpoints:
  GET /api/state/summary              Full project snapshot
  GET /api/state/pipeline/{track}     Per-module v3 phase state for one track
  GET /api/state/ready-to-build       Phase A done, Phase B not started
  GET /api/state/weak-points          Modules with quality issues
  GET /api/state/failing              Modules with audit/phase failures
  GET /api/state/research-coverage    Per-track research completeness
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
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT, SEMINAR_TRACK_IDS

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from research_quality import assess_research_compat, find_research_path

router = APIRouter(tags=["state"])

# ==================== CONSTANTS ====================

CURRICULUM_YAML = CURRICULUM_ROOT / "curriculum.yaml"
PLANS_ROOT = CURRICULUM_ROOT / "plans"

PROFILE_MAP = {
    "a1": "core", "a2": "core", "b1": "core", "b2": "core",
    "b2-pro": "pro", "c1-pro": "pro",
    "c1": "core", "c2": "core",
    "b2-hist": "seminar", "c1-hist": "seminar", "c1-bio": "seminar",
    "lit": "seminar", "lit-essay": "seminar", "lit-hist-fic": "seminar",
    "lit-fantastika": "seminar", "lit-war": "seminar",
    "lit-humor": "seminar", "lit-juvenile": "seminar",
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
        if CURRICULUM_YAML.exists():
            _curriculum_cache = yaml.safe_load(CURRICULUM_YAML.read_text()) or {}
        else:
            _curriculum_cache = {}
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


def _has_research_file(track_dir: Path, slug: str) -> bool:
    """Return True if a research file exists for this module."""
    return (track_dir / "research" / f"{slug}-research.md").exists()


def _is_research_done(v3: dict, v2: dict, track_dir: Path = None, slug: str = None) -> bool:
    """Research done if v3 Phase A complete, v2 phase '1' complete, or research file exists."""
    if v3.get("phases", {}).get("v3-A", {}).get("status") == "complete":
        return True
    if v2.get("phases", {}).get("1", {}).get("status") == "complete":
        return True
    if track_dir is not None and slug is not None and _has_research_file(track_dir, slug):
        return True
    return False


def _is_content_done(v3: dict, v2: dict) -> bool:
    """Content done if v3 Phase B complete OR v2 phase '2' complete."""
    if v3.get("phases", {}).get("v3-B", {}).get("status") == "complete":
        return True
    if v2.get("phases", {}).get("2", {}).get("status") == "complete":
        return True
    return False


def _get_audit_status(track_dir: Path, slug: str) -> dict:
    """Read status/{slug}.json. Returns {status, word_count, word_target, blocking_issues}."""
    status_file = track_dir / "status" / f"{slug}.json"
    if not status_file.exists():
        return {"status": "not_run", "word_count": 0, "word_target": 0, "blocking_issues": []}
    try:
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
            try:
                word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                pass

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
    generated_at = datetime.now(timezone.utc).isoformat()
    tracks_out = {}
    totals = {
        "total": 0, "research_done": 0, "content_done": 0,
        "audit_passing": 0, "final_review_done": 0,
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
        final_review_done = 0

        for num, slug in plan_slugs:
            orch_dir = track_dir / "orchestration" / slug
            v3 = _read_v3_state(orch_dir)
            v2 = _read_v2_state(orch_dir)

            if _is_research_done(v3, v2, track_dir, slug):
                research_done += 1
            if _is_content_done(v3, v2):
                content_done += 1

            audit = _get_audit_status(track_dir, slug)
            if audit["status"] == "pass":
                audit_passing += 1

            final_review = track_dir / "review" / f"{slug}-final-review.md"
            if final_review.exists():
                final_review_done += 1

        total = len(plan_slugs)
        tracks_out[track_id] = {
            "total": total,
            "profile": profile,
            "research_done": research_done,
            "content_done": content_done,
            "audit_passing": audit_passing,
            "final_review_done": final_review_done,
        }

        totals["total"] += total
        totals["research_done"] += research_done
        totals["content_done"] += content_done
        totals["audit_passing"] += audit_passing
        totals["final_review_done"] += final_review_done

    return {"generated_at": generated_at, "tracks": tracks_out, "totals": totals}


def _compute_pipeline_track(track_id: str, level_cfg: dict) -> dict:
    """Sync computation for pipeline/{track}."""
    plan_slugs = _get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    modules = []

    for num, slug in plan_slugs:
        orch_dir = track_dir / "orchestration" / slug
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

        audit = _get_audit_status(track_dir, slug)
        research_score = _get_research_score(track_dir, slug, track_id)

        word_count = audit.get("word_count", 0)
        word_target = audit.get("word_target", 0)
        if word_target == 0:
            word_target = _get_word_target_from_plan(track_id, slug)

        modules.append({
            "num": num,
            "slug": slug,
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

        for num, slug in plan_slugs:
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

    return {"generated_at": datetime.now(timezone.utc).isoformat(), "tracks": tracks_out}


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
                score_match = re.search(r"Overall Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", text, re.IGNORECASE)
                status_match = re.search(r"\bStatus:\s*(PASS|FAIL)\b", text, re.IGNORECASE)
                issue_count = len(re.findall(r"^#{1,4}\s+Issue\s*#?\s*\d+", text, re.MULTILINE | re.IGNORECASE))

                if score_match:
                    scores.append(float(score_match.group(1)))
                if status_match and status_match.group(1).upper() == "PASS":
                    pass_count += 1
                total_issues += issue_count

            if final_review_file.exists():
                has_final_review += 1

        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        pass_rate = round(pass_count / has_review, 2) if has_review > 0 else None

        tracks_out[track_id] = {
            "total_built": total_built,
            "has_review": has_review,
            "has_final_review": has_final_review,
            "avg_score": avg_score,
            "pass_rate": pass_rate,
            "total_issues_found": total_issues,
        }

    return {"generated_at": datetime.now(timezone.utc).isoformat(), "tracks": tracks_out}


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


@router.get("/ready-to-build")
async def ready_to_build(track: Optional[str] = Query(None)):
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
                v3 = _read_v3_state(orch_dir)
                v2 = _read_v2_state(orch_dir)

                if _is_research_done(v3, v2, track_dir, slug) and not _is_content_done(v3, v2):
                    phase_a = v3.get("phases", {}).get("v3-A") or v2.get("phases", {}).get("1") or {}
                    ready.append({
                        "track": track_id,
                        "num": num,
                        "slug": slug,
                        "phase_a_ts": phase_a.get("ts") or phase_a.get("timestamp"),
                        "phase_a_mode": phase_a.get("mode"),
                    })
        return {"count": len(ready), "modules": ready}

    return await asyncio.to_thread(_compute)


@router.get("/weak-points")
async def weak_points(
    track: Optional[str] = Query(None),
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
                    weak.append({
                        "track": track_id,
                        "num": num,
                        "slug": slug,
                        "audit_status": audit["status"],
                        "word_count": word_count,
                        "word_target": word_target,
                        "research_score": research_score,
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
async def failing_modules(track: Optional[str] = Query(None)):
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
                v3 = _read_v3_state(orch_dir)
                phases = v3.get("phases", {})

                audit = _get_audit_status(track_dir, slug)
                failed_phases = [
                    k.replace("v3-", "") for k, v in phases.items()
                    if isinstance(v, dict) and v.get("status") == "failed"
                ]

                if audit["status"] == "fail" or failed_phases:
                    failing.append({
                        "track": track_id,
                        "num": num,
                        "slug": slug,
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


@router.get("/review-coverage")
async def review_coverage():
    """Per-track review and final-review coverage + quality signal."""
    cached = _cache_get("review_coverage", ttl=300.0)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_compute_review_coverage)
    _cache_set("review_coverage", result)
    return result


@router.get("/issues")
async def outstanding_issues(
    track: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
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
                for review_filename in [f"{slug}-review.md", f"{slug}-final-review.md"]:
                    review_file = review_dir / review_filename
                    if not review_file.exists():
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
