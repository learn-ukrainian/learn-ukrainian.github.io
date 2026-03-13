"""Research detail and legacy compatibility functions for state API endpoints.

Contains research detail computation, module detail deep-dive,
pipeline version phase resolution, and legacy research/content checks.
"""

from datetime import UTC, datetime

from .config import CURRICULUM_ROOT
from .state_helpers import (
    PLANS_ROOT,
    V4_PHASE_ORDER,
    V5_PHASE_ORDER,
    detect_pipeline_version,
    find_content_file,
    get_audit_status,
    get_broker_messages_for_slug,
    get_final_review_info,
    get_plan_slugs,
    get_research_score,
    get_word_target_from_plan,
    has_research_file,
    # BACKWARD-COMPAT: v3/v4/v2 parsers needed for ~100+ modules not yet rebuilt on v5
    parse_v3_phase_status,
    parse_v4_phase_status,
    parse_v5_phase_status,
    read_v2_state,
    read_v3_state,
    read_v4_state,
)


def severity_key(m: dict) -> int:
    """Sort key for weak-points severity ranking."""
    score = 0
    for issue in m["issues"]:
        if "audit_fail" in issue:
            score += 100
        elif "research_score" in issue:
            score += 50
        elif "low_words" in issue:
            score += 10
    return -score



def compute_research_detail(track_id: str, level_cfg: dict, min_score: int) -> dict:
    """Compute per-module research quality for a track."""
    from research_quality import (
        DIMENSION_SHORT_LABELS,
        assess_research_compat,
        find_research_path,
        get_dimensions,
        get_rubric,
    )

    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    plan_slugs = get_plan_slugs(track_id)
    rubric_name = get_rubric(track_id)
    dimensions = get_dimensions(rubric_name) if rubric_name else []

    modules = []
    upgrade_queue = []
    quality_counts = {"exemplary": 0, "solid": 0, "adequate": 0, "thin": 0, "stub": 0, "missing": 0}
    scores = []

    for num, slug in plan_slugs:
        mod_entry, quality, score = _assess_module_research(
            track_dir, track_id, num, slug,
            rp_finder=find_research_path, assessor=assess_research_compat,
        )
        modules.append(mod_entry)

        if not mod_entry["exists"]:
            quality_counts["missing"] += 1
            upgrade_queue.append({"num": num, "slug": slug, "score": None, "gaps": ["missing"]})
            continue

        if quality and quality in quality_counts:
            quality_counts[quality] += 1
        if score is not None:
            scores.append(score)
            if score < min_score:
                gaps = mod_entry.get("gaps") or []
                upgrade_queue.append({
                    "num": num, "slug": slug, "score": score,
                    "gaps": [g.split(":")[0] for g in gaps],
                })

    upgrade_queue.sort(key=lambda x: (x["score"] if x["score"] is not None else -1))
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "track": track_id, "rubric": rubric_name,
        "dimensions": dimensions,
        "dimension_labels": {d: DIMENSION_SHORT_LABELS.get(d, d[:3]) for d in dimensions} if dimensions else {},
        "total": len(plan_slugs), "researched": len(scores), "avg_score": avg_score,
        "quality_distribution": quality_counts,
        "upgrade_queue": upgrade_queue, "upgrade_count": len(upgrade_queue),
        "min_score_threshold": min_score, "modules": modules,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _assess_module_research(track_dir, track_id, num, slug, *, rp_finder, assessor):
    """Assess research quality for a single module. Returns (entry, quality, score)."""
    rp = rp_finder(track_dir, slug)
    empty = {
        "num": num, "slug": slug, "exists": False,
        "score": None, "quality": None, "dimensions": None, "gaps": None,
    }
    if not rp:
        return empty, None, None

    content_path = find_content_file(track_dir, slug)
    info = assessor(rp, track_id, content_path)
    if not info or not info.get("exists"):
        return empty, None, None

    dims = info.get("dimensions") or {}
    mod_entry = {
        "num": num, "slug": slug, "exists": True,
        "words": info.get("words", 0),
        "score": info.get("score"), "quality": info.get("quality"),
        "dimensions": {
            k: {"score": v["score"], "max": v["max"], "detail": v["detail"]}
            for k, v in dims.items()
        } if dims else None,
        "gaps": info.get("gaps") or [],
        "content_alignment": info.get("content_alignment"),
    }
    return mod_entry, info.get("quality"), info.get("score")


def compute_module_detail(track_id: str, num: int, level_cfg: dict) -> dict:
    """Compute single module deep-dive data."""
    plan_slugs = get_plan_slugs(track_id)
    match = next(((n, s) for n, s in plan_slugs if n == num), None)
    if not match:
        return {"error": f"Module #{num} not found in track '{track_id}'"}
    _, slug = match
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    orch_dir = track_dir / "orchestration" / slug

    version = detect_pipeline_version(orch_dir)
    # Read state once — reuse for phases + consultations (avoids duplicate I/O)
    state_data = read_v2_state(orch_dir) if version == "v5" else {}
    phases = get_phases_for_version(orch_dir, version, state_data=state_data)

    audit = get_audit_status(track_dir, slug)
    word_target = audit.get("word_target", 0)
    if word_target == 0:
        word_target = get_word_target_from_plan(track_id, slug)

    plan_file = PLANS_ROOT / track_id / f"{slug}.yaml"

    return {
        "track": track_id, "num": num, "slug": slug,
        "pipeline_version": version, "needs_rebuild": version != "v5",
        "phases": phases,
        "audit": {
            "status": audit["status"], "word_count": audit.get("word_count", 0),
            "word_target": word_target, "blocking_issues": audit.get("blocking_issues", []),
        },
        "research": {
            "exists": has_research_file(track_dir, slug),
            "score": get_research_score(track_dir, slug, track_id),
        },
        "review": {"exists": (track_dir / "review" / f"{slug}-review.md").exists()},
        "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
        "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
        "final_review": get_final_review_info(track_dir, slug),
        "enriched": plan_file.with_suffix(".yaml.bak").exists(),
        "consultations": state_data.get("consultations", []),
        "comms": get_broker_messages_for_slug(slug, limit=15),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def get_phases_for_version(orch_dir, version, *, state_data: dict | None = None):
    """Get phase status dict appropriate for the pipeline version."""
    if version == "v5":
        v5 = state_data if state_data is not None else read_v2_state(orch_dir)
        return {name: parse_v5_phase_status(v5, name) for name in V5_PHASE_ORDER}
    elif version == "v4":
        v4 = read_v4_state(orch_dir)
        return {name: parse_v4_phase_status(v4, name) for name in V4_PHASE_ORDER}
    else:
        v3 = read_v3_state(orch_dir)
        return {pid: parse_v3_phase_status(v3, f"v3-{pid}") for pid in ["A", "B", "C", "audit", "D", "E", "F"]}
