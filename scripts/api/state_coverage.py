"""Coverage and summary computations for the state API.

These functions compute summary, pipeline track, research coverage,
and review coverage data. All are sync functions designed for asyncio.to_thread().
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

try:
    from path_safety import safe_join, trusted_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join, trusted_join  # scripts.api package import (production)

from .config import CURRICULUM_ROOT, LEVELS, PROJECT_ROOT, SEMINAR_TRACK_IDS
from .state_helpers import (
    PROFILE_MAP,
    detect_pipeline_version,
    find_content_file,
    get_audit_status,
    get_plan_slugs,
    get_research_score,
    get_word_target_from_plan,
    is_content_done,
    load_module_state,
    parse_phase_status_from_state,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research_quality import assess_research_compat, find_research_path

from .review_parsing import count_review_issues, extract_plan_verdict, extract_review_score, extract_review_verdict

# Import canonical phase list from pipeline
try:
    from scripts.build.phase_constants import PHASE_LABELS as V6_PHASE_LABELS
    from scripts.build.phase_constants import PHASES as V6_PHASES
except ImportError:
    V6_PHASES = [
        "check", "research", "skeleton", "pre-verify", "write",
        "exercises", "activities", "repair", "verify-exercises",
        "annotate", "vocab", "enrich", "verify", "review", "stress",
        "publish", "audit",
    ]
    V6_PHASE_LABELS = {}


def compute_summary() -> dict:
    """Synchronous summary computation -- safe to run in asyncio.to_thread()."""
    generated_at = datetime.now(UTC).isoformat()
    module_sources = _module_sources_by_track()
    tracks_out = {}
    totals = {
        "total": 0, "research_done": 0, "content_done": 0,
        "audit_passing": 0, "reviewed": 0, "final_review_done": 0,
        "prompt_reviewed": 0, "content_reviewed": 0,
        "generated_md": 0, "published_mdx": 0, "dossier_done": 0,
        "dossier_docs": 0, "dossier_curriculum": 0, "audit_stale": 0,
    }

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
        if not plan_slugs:
            continue

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        profile = PROFILE_MAP.get(track_id, "core")
        counts = _count_summary_for_track(track_dir, track_id, plan_slugs)

        tracks_out[track_id] = {
            "total": len(plan_slugs),
            "profile": profile,
            "is_seminar": track_id in SEMINAR_TRACK_IDS,
            "module_source": module_sources.get(track_id, "plans-fallback"),
            **counts,
        }

        for key in totals:
            if key == "total":
                totals["total"] += len(plan_slugs)
            elif key in counts:
                totals[key] += counts[key]

    return {
        "generated_at": generated_at,
        "tracks": tracks_out,
        "totals": totals,
        "sources": {
            "module_catalog": "curriculum.yaml with plans/{track}/*.yaml fallback",
            "build_state": "curriculum/l2-uk-en/{track}/orchestration/{slug}/state.json",
            "generated_md": "curriculum/l2-uk-en/{track}/{slug}.md",
            "published_mdx": "site/src/content/docs/{track}/{slug}.mdx",
            "audit": "curriculum/l2-uk-en/{track}/status/{slug}.json",
            "review": "curriculum/l2-uk-en/{track}/review/{slug}-review.md",
            "dossier": [
                "curriculum/l2-uk-en/{track}/research/{slug}-research.md",
                "curriculum/l2-uk-en/{track}/research/{slug}-knowledge-packet.md",
                "docs/research/{track}/{slug}.md",
            ],
        },
    }


def _module_sources_by_track() -> dict[str, str]:
    """Describe which catalog source get_plan_slugs will use per track."""
    data_path = CURRICULUM_ROOT / "curriculum.yaml"
    try:
        data = yaml.safe_load(data_path.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    levels = data.get("levels", {})
    return {
        level_cfg["id"]: (
            "curriculum.yaml"
            if levels.get(level_cfg["id"], {}).get("modules", [])
            else "plans-fallback"
        )
        for level_cfg in LEVELS
    }


def _count_summary_for_track(track_dir, track_id, plan_slugs):
    """Count research/content/audit/review stats for a single track."""
    research_done = content_done = audit_passing = 0
    reviewed = final_review_done = prompt_reviewed = content_reviewed = 0
    generated_md = published_mdx = dossier_done = 0
    dossier_docs = dossier_curriculum = audit_stale = 0

    audit_dir = track_dir / "audit"
    for _num, slug in plan_slugs:
        # trusted_join: slug from repo plan config, per-module scan hot loop (#4931 perf).
        orch_dir = trusted_join(track_dir / "orchestration", slug)
        state = load_module_state(track_id, slug, orch_dir)

        research_path = find_research_path(track_dir, slug)
        if research_path:
            dossier_done += 1
            research_parts = research_path.parts
            if "docs" in research_parts and "research" in research_parts:
                dossier_docs += 1
            else:
                dossier_curriculum += 1

        research_phase = parse_phase_status_from_state(state, "research")
        if research_phase.get("status") == "complete" or research_path:
            research_done += 1
        if is_content_done(state):
            content_done += 1
        if find_content_file(track_dir, slug):
            generated_md += 1
        if _published_mdx_path(track_id, slug).exists():
            published_mdx += 1

        audit = get_audit_status(track_dir, slug)
        if audit["status"] == "pass":
            audit_passing += 1
        if audit["status"] == "stale":
            audit_stale += 1

        if (track_dir / "review" / f"{slug}-review.md").exists():
            reviewed += 1
        if (track_dir / "review" / f"{slug}-final-review.md").exists():
            final_review_done += 1
        if (audit_dir / f"{slug}-prompt-review.md").exists():
            prompt_reviewed += 1
        if (audit_dir / f"{slug}-content-review.md").exists():
            content_reviewed += 1

    return {
        "research_done": research_done, "content_done": content_done,
        "audit_passing": audit_passing, "reviewed": reviewed,
        "final_review_done": final_review_done,
        "prompt_reviewed": prompt_reviewed, "content_reviewed": content_reviewed,
        "generated_md": generated_md, "published_mdx": published_mdx,
        "dossier_done": dossier_done, "dossier_docs": dossier_docs,
        "dossier_curriculum": dossier_curriculum, "audit_stale": audit_stale,
    }


def _published_mdx_path(track_id: str, slug: str) -> Path:
    return PROJECT_ROOT / "site" / "src" / "content" / "docs" / track_id / f"{slug}.mdx"


def compute_pipeline_track(track_id: str, level_cfg: dict) -> dict:
    """Sync computation for pipeline/{track}."""
    plan_slugs = get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]
    modules = []

    for num, slug in plan_slugs:
        # trusted_join: slug from repo plan config, per-module scan hot loop (#4931 perf).
        orch_dir = trusted_join(track_dir / "orchestration", slug)
        version = detect_pipeline_version(orch_dir)
        state = load_module_state(track_id, slug, orch_dir)

        audit = get_audit_status(track_dir, slug)
        research_score = get_research_score(track_dir, slug, track_id)
        research_path = find_research_path(track_dir, slug)
        content_path = find_content_file(track_dir, slug)

        word_count = audit.get("word_count", 0)
        word_target = audit.get("word_target", 0)
        if word_target == 0:
            word_target = get_word_target_from_plan(track_id, slug)

        phases = {
            name: parse_phase_status_from_state(state, name)
            for name in V6_PHASES
        }

        modules.append({
            "num": num, "slug": slug,
            "pipeline_version": version,
            "needs_rebuild": version != "v6",
            "phases": phases,
            "audit": audit["status"],
            "word_count": word_count,
            "words": word_count, "word_target": word_target,
            "research_score": research_score,
            "generated_md": bool(content_path),
            "published_mdx": _published_mdx_path(track_id, slug).exists(),
            "dossier": {
                "exists": research_path is not None,
                "source": _research_source(research_path),
            },
            "prompt_review": (track_dir / "audit" / f"{slug}-prompt-review.md").exists(),
            "content_review": (track_dir / "audit" / f"{slug}-content-review.md").exists(),
        })

    return {
        "track": track_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(modules),
        "profile": PROFILE_MAP.get(track_id, "core"),
        "is_seminar": track_id in SEMINAR_TRACK_IDS,
        "phase_order": V6_PHASES,
        "phase_labels": {name: V6_PHASE_LABELS.get(name, name) for name in V6_PHASES},
        "modules": modules,
    }


def _research_source(research_path: Path | None) -> str | None:
    if research_path is None:
        return None
    parts = research_path.parts
    if "docs" in parts and "research" in parts:
        return "docs/research"
    return "curriculum/research"


def compute_research_coverage() -> dict:
    """Sync research coverage computation."""
    tracks_out = {}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
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
            "total_modules": total, "has_research": has_research,
            "pct_coverage": pct_coverage, "quality": quality_counts,
            "avg_score": avg_score, "needs_upgrade": needs_upgrade,
        }

    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks_out}


def compute_review_coverage() -> dict:
    """Sync review coverage computation."""
    tracks_out = {}

    for level_cfg in LEVELS:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
        if not plan_slugs:
            continue

        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        stats = _compute_review_stats_for_track(track_dir, plan_slugs)
        tracks_out[track_id] = stats

    return {"generated_at": datetime.now(UTC).isoformat(), "tracks": tracks_out}


def _compute_review_stats_for_track(track_dir, plan_slugs):
    """Compute review statistics for a single track."""
    review_dir = track_dir / "review"
    audit_dir = track_dir / "audit"

    total_built = has_review = has_final_review = pass_count = total_issues = 0
    scores = []
    plan_reviewed = plan_pass = plan_needs_fixes = plan_fail = 0

    for num, slug in plan_slugs:
        md_exists = any([
            (track_dir / f"{slug}.md").exists(),
            (track_dir / f"{num:02d}-{slug}.md").exists(),
            (track_dir / f"{num}-{slug}.md").exists(),
        ])
        if md_exists:
            total_built += 1

        review_file = review_dir / f"{slug}-review.md"
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

        if (review_dir / f"{slug}-final-review.md").exists():
            has_final_review += 1

        plan_review_file = audit_dir / f"{slug}-plan-review.md"
        if plan_review_file.exists():
            plan_reviewed += 1
            try:
                v = extract_plan_verdict(plan_review_file.read_text(errors="replace"))
                if v == "PASS":
                    plan_pass += 1
                elif v == "NEEDS FIXES":
                    plan_needs_fixes += 1
                elif v == "FAIL":
                    plan_fail += 1
            except Exception:
                pass

    return {
        "total_built": total_built, "has_review": has_review,
        "has_final_review": has_final_review,
        "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
        "pass_rate": round(pass_count / has_review, 2) if has_review > 0 else None,
        "total_issues_found": total_issues,
        "plan_reviewed": plan_reviewed, "plan_pass": plan_pass,
        "plan_needs_fixes": plan_needs_fixes, "plan_fail": plan_fail,
    }
