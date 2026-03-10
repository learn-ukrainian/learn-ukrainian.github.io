"""Module scanning and track aggregation helpers for the dashboard API router.

Contains functions for scanning tracks, building module info, computing
track stats, finding active builds, and classifying pipeline queues.
"""

import contextlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml
from .config import CURRICULUM_ROOT, LEVELS, SEMINAR_TRACK_IDS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.status_cache import get_source_paths, read_status
from research_quality import assess_research_compat, find_research_path, get_rubric

from .review_parsing import extract_plan_verdict, extract_review_score, extract_review_verdict
from .state_helpers import detect_pipeline_version, parse_v4_phase_status, read_v2_state, read_v4_state, V4_PHASE_ORDER

# Simple TTL cache for scan_track results
_track_cache: dict[str, tuple[float, dict]] = {}
_TRACK_CACHE_TTL = 30.0  # seconds


def scan_track_cached(track_id: str, track_path: str, manifest_modules: list) -> dict:
    """Cached wrapper around scan_track."""
    entry = _track_cache.get(track_id)
    if entry and (time.time() - entry[0]) < _TRACK_CACHE_TTL:
        return entry[1]
    result = scan_track(track_id, track_path, manifest_modules)
    _track_cache[track_id] = (time.time(), result)
    return result


def load_manifest() -> dict:
    """Load the curriculum manifest YAML file."""
    manifest_path = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest_path.exists():
        return {}
    with open(manifest_path) as f:
        return yaml.safe_load(f) or {}


def parse_slug(entry) -> str:
    """Extract slug from a manifest entry, stripping comments."""
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def read_yaml_file(path: Path) -> dict | None:
    """Safely read and parse a YAML file, returning None on any error."""
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def default_research_info(track_id: str) -> dict:
    """Return a default (empty) research info dict for a track."""
    return {
        "exists": False, "words": 0, "quality": None,
        "score": None, "markers": None,
        "profile": get_rubric(track_id),
        "dimensions": None, "gaps": None,
    }


def extract_word_count_from_status(result) -> tuple[int, int, int, str | None]:
    """Parse word count, target, deferred count, and last audit from status data."""
    if not result or not result.data:
        return 0, 0, 0, None

    overall = result.data.get("overall", {})
    gates = result.data.get("gates", {})
    deferred_count = overall.get("deferred_count", 0)
    last_audit = result.data.get("timestamp")

    word_count = 0
    word_target = 0
    lesson_msg = gates.get("lesson", {}).get("message", "")
    if "/" in str(lesson_msg):
        parts = str(lesson_msg).split("/")
        with contextlib.suppress(ValueError, IndexError):
            word_count = int(parts[0].strip().split()[-1]) if parts[0].strip() else 0
        with contextlib.suppress(ValueError, IndexError):
            word_target = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0

    return word_count, word_target, deferred_count, last_audit


def extract_review_info(track_dir: Path, slug: str) -> dict:
    """Extract review score, verdict, and plan review info for a module."""
    info: dict = {
        "has_review": False, "has_final_review": False,
        "review_score": None, "review_verdict": None,
        "has_plan_review": False, "plan_review_verdict": None,
    }

    review_file = track_dir / "review" / f"{slug}-review.md"
    info["has_review"] = review_file.exists()
    info["has_final_review"] = (track_dir / "review" / f"{slug}-final-review.md").exists()

    if info["has_review"]:
        try:
            text = review_file.read_text(errors="replace")
            info["review_score"] = extract_review_score(text)
            info["review_verdict"] = extract_review_verdict(text)
        except Exception:
            pass

    plan_review_file = track_dir / "audit" / f"{slug}-plan-review.md"
    info["has_plan_review"] = plan_review_file.exists()
    if info["has_plan_review"]:
        try:
            text = plan_review_file.read_text(errors="replace")
            info["plan_review_verdict"] = extract_plan_verdict(text)
        except Exception:
            pass

    return info


def build_module_info(track_dir, plans_dir, track_id, slug, idx) -> dict:
    """Build the info dict for a single module in a track scan."""
    num = idx + 1

    sp = get_source_paths(track_dir, slug) if track_dir.exists() else {}
    has_md = sp.get("md") and sp["md"].exists() if sp else False
    has_meta = sp.get("meta") and sp["meta"].exists() if sp else False
    has_activities = sp.get("activities") and sp["activities"].exists() if sp else False
    has_vocab = sp.get("vocabulary") and sp["vocabulary"].exists() if sp else False
    plan_file = plans_dir / f"{slug}.yaml"
    has_plan = plan_file.exists()

    content_path = sp.get("md") if sp else None
    rp = find_research_path(track_dir, slug)
    research_info = assess_research_compat(rp, track_id, content_path) if rp else None
    if research_info is None:
        research_info = default_research_info(track_id)

    status_file = track_dir / "status" / f"{slug}.json"
    result = read_status(status_file, source_paths=sp) if status_file.exists() else None

    overall_status = "missing"
    gates = {}
    word_count, word_target, deferred_count, last_audit = extract_word_count_from_status(result)

    if result and result.data:
        overall_status = result.data.get("overall", {}).get("status", "fail")
        gates = result.data.get("gates", {})
    elif has_md:
        overall_status = "unaudited"
        md_content = sp["md"].read_text() if sp.get("md") else ""
        word_count = len(md_content.split())

    if word_target == 0 and has_plan:
        plan_data = read_yaml_file(plan_file)
        word_target = plan_data.get("word_target", 0) if plan_data else 0

    orch_dir = track_dir / "orchestration" / slug
    orch_exists = orch_dir.exists()
    pipeline_version = detect_pipeline_version(orch_dir) if orch_exists else "unbuilt"
    review_info = extract_review_info(track_dir, slug)
    friction_count = sum(1 for _ in orch_dir.glob("*friction*")) if orch_exists else 0

    return {
        "slug": slug, "num": num, "pipeline_version": pipeline_version,
        "needs_rebuild": pipeline_version != "v4",
        "status": overall_status, "word_count": word_count, "word_target": word_target,
        "deferred_count": deferred_count, "gates": gates,
        "files": {
            "plan": has_plan, "meta": has_meta, "lesson": has_md,
            "activities": has_activities, "vocabulary": has_vocab,
            "review": review_info["has_review"], "final_review": review_info["has_final_review"],
            "plan_review": review_info["has_plan_review"],
        },
        "has_review": review_info["has_review"],
        "has_final_review": review_info["has_final_review"],
        "review_score": review_info["review_score"],
        "review_verdict": review_info["review_verdict"],
        "has_plan_review": review_info["has_plan_review"],
        "plan_review_verdict": review_info["plan_review_verdict"],
        "friction_count": friction_count, "last_audit": last_audit,
        "is_fresh": result.is_fresh if result else False,
        "research": research_info,
    }


def compute_track_stats(modules: list, track_id: str) -> dict:
    """Aggregate per-module data into track-level stats."""
    stats = {
        "pass": sum(1 for m in modules if m["status"] == "pass"),
        "content_complete": sum(1 for m in modules if m["status"] == "content-complete"),
        "fail": sum(1 for m in modules if m["status"] == "fail"),
        "unaudited": sum(1 for m in modules if m["status"] == "unaudited"),
        "missing": sum(1 for m in modules if m["status"] == "missing"),
        "reviewed": sum(1 for m in modules if m.get("has_review")),
        "final_review": sum(1 for m in modules if m.get("has_final_review")),
        "plan_reviewed": sum(1 for m in modules if m.get("has_plan_review")),
        "plan_pass": sum(1 for m in modules if m.get("plan_review_verdict") == "PASS"),
        "plan_needs_fixes": sum(1 for m in modules if m.get("plan_review_verdict") == "NEEDS FIXES"),
        "plan_fail": sum(1 for m in modules if m.get("plan_review_verdict") == "FAIL"),
    }

    rubric_name = get_rubric(track_id)
    research_total = sum(1 for m in modules if m.get("research", {}).get("exists"))
    research_stats: dict = {"total": research_total, "profile": rubric_name}
    if rubric_name:
        for label in ["exemplary", "solid", "adequate", "thin", "stub"]:
            research_stats[label] = sum(
                1 for m in modules if m.get("research", {}).get("quality") == label
            )
    stats["research"] = research_stats
    return stats


def get_orchestration_info(orch_dir: Path) -> dict:
    """Collect orchestration phase listing, friction count, and pipeline version."""
    if not orch_dir.exists():
        return {"orchestration": [], "friction_count": 0, "pipeline_version": "unbuilt", "needs_rebuild": True}

    phases = []
    for f in sorted(orch_dir.iterdir(), key=lambda x: x.stat().st_mtime):
        if f.is_file():
            st = f.stat()
            phases.append({
                "file": f.name, "size": st.st_size,
                "timestamp": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
            })

    version = detect_pipeline_version(orch_dir)
    info: dict = {
        "orchestration": phases,
        "friction_count": sum(1 for _ in orch_dir.glob("*friction*")),
        "pipeline_version": version, "needs_rebuild": version != "v5",
    }
    if version == "v5":
        v5 = read_v2_state(orch_dir)
        info["v5_phases"] = v5.get("phases", {})
    elif version == "v4":
        v4 = read_v4_state(orch_dir)
        info["v4_phases"] = {name: parse_v4_phase_status(v4, name) for name in V4_PHASE_ORDER}
    return info


def scan_track(track_id: str, track_path: str, manifest_modules: list) -> dict:
    """Scan a single track and return module-level detail."""
    track_dir = CURRICULUM_ROOT / track_path
    plans_dir = CURRICULUM_ROOT / "plans" / track_id

    modules = [
        build_module_info(track_dir, plans_dir, track_id, parse_slug(m_entry), idx)
        for idx, m_entry in enumerate(manifest_modules)
    ]

    return {
        "track_id": track_id, "track_path": track_path,
        "module_count": len(modules),
        "is_seminar": track_id in SEMINAR_TRACK_IDS,
        "stats": compute_track_stats(modules, track_id),
        "modules": modules,
    }


def find_active_builds() -> list[dict]:
    """Find orchestration dirs modified in last 15 minutes."""
    active_builds = []
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
            latest_file = ""
            for f in module_dir.iterdir():
                if f.is_file() and f.stat().st_mtime > latest_mtime:
                    latest_mtime = f.stat().st_mtime
                    latest_file = f.name
            age = datetime.now().timestamp() - latest_mtime
            if age < 900:
                files = [f.name for f in module_dir.iterdir() if f.is_file()]
                has_phase3 = any("phase-3" in fn for fn in files)
                has_phase7 = any("phase-7" in fn or "final-review" in fn for fn in files)
                stage = "hetman" if has_phase3 or has_phase7 else "otaman"
                active_builds.append({
                    "slug": module_dir.name, "track": track_dir.name,
                    "stage": stage, "latest_file": latest_file, "seconds_ago": int(age),
                })
    return active_builds


def classify_module_queue(track_id, track_dir, slug, idx, status_file) -> str | None:
    """Classify a module into a queue: 'otaman', 'hetman', 'final_review', or None."""
    if not status_file.exists():
        md_exists = any(
            (track_dir / f).exists()
            for f in [f"{slug}.md", f"{idx + 1:02d}-{slug}.md", f"{idx + 1}-{slug}.md"]
        )
        return None if md_exists else "otaman"

    try:
        with open(status_file) as f:
            data = json.load(f)
        overall = data.get("overall", {}).get("status", "")
        deferred = data.get("overall", {}).get("deferred_count", 0)

        if overall == "content-complete" or deferred > 0:
            return "hetman"
        if overall == "fail":
            lesson_status = data.get("gates", {}).get("lesson", {}).get("status", "")
            return "otaman" if lesson_status == "fail" else None
        if overall == "pass":
            review_file = track_dir / "review" / f"{slug}-final-review.md"
            return "final_review" if not review_file.exists() else None
    except Exception:
        pass
    return None


def scan_pipeline_queues() -> tuple[list, list, list]:
    """Scan all tracks to build otaman, hetman, and final_review queues."""
    manifest = load_manifest()
    otaman_queue: list[dict] = []
    hetman_queue: list[dict] = []
    final_review_queue: list[dict] = []

    queue_map = {"otaman": otaman_queue, "hetman": hetman_queue, "final_review": final_review_queue}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        status_dir = track_dir / "status"
        track_modules = manifest.get("levels", {}).get(track_id, {}).get("modules", [])

        for idx, m_entry in enumerate(track_modules):
            slug = parse_slug(m_entry)
            classification = classify_module_queue(
                track_id, track_dir, slug, idx, status_dir / f"{slug}.json",
            )
            if classification:
                queue_map[classification].append({"track": track_id, "slug": slug, "num": idx + 1})

    return otaman_queue, hetman_queue, final_review_queue
