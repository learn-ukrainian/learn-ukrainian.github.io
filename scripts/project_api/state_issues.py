"""Issue collection and review analysis for state API endpoints.

Handles final review aggregation and issue pattern counting.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from lu_machinery.api import config
from lu_machinery.path_safety import safe_join

from .curriculum_state import V6_PHASE_ORDER as V6_PHASES
from .curriculum_state import (
    detect_pipeline_version,
    get_final_review_info,
    get_plan_slugs,
    read_v2_state,
    read_v3_state,
)

ISSUE_PATTERN_KEYWORDS = [
    "FACTUAL",
    "PLAN COMPLIANCE",
    "ACTIVITY",
    "ANTI-SURZHYK",
    "PRONUNCIATION",
    "MISLEADING",
    "COLONIAL",
    "WORD COUNT",
    "MISSING",
    "RUSSICISM",
]


def _is_ready_for_final_review(orch_dir, version: str) -> bool:
    """Return True when pipeline state indicates final review can run."""
    if version == "v6":
        phases = read_v2_state(orch_dir).get("phases", {})
        terminal_phase = V6_PHASES[-1] if V6_PHASES else "audit"
        return cast("bool", phases.get(terminal_phase, {}).get("status") == "complete")
    if version == "v5":
        phases = read_v2_state(orch_dir).get("phases", {})
        return cast("bool", phases.get("validate", {}).get("status") == "complete")
    if version == "v3":
        phases = read_v3_state(orch_dir).get("phases", {})
        return cast("bool", phases.get("v3-audit", {}).get("status") == "complete")
    return False


def compute_final_reviews(
    track_id: str,
    level_cfg: dict,
    *,
    curriculum_root: Path | None = None,
    plans_root: Path | None = None,
) -> dict:
    """Compute final review aggregation for a track."""
    if curriculum_root is None:
        curriculum_root = config.CURRICULUM_ROOT
    plan_slugs = get_plan_slugs(track_id, curriculum_root=curriculum_root, plans_root=plans_root)
    track_dir = curriculum_root / level_cfg["path"]

    approved = []
    rejected = []
    pending = []
    all_issues = []

    for num, slug in plan_slugs:
        info = get_final_review_info(track_dir, slug, curriculum_root=curriculum_root)
        if info is None:
            orch_dir = safe_join(track_dir / "orchestration", slug)
            version = detect_pipeline_version(orch_dir)
            if _is_ready_for_final_review(orch_dir, version):
                pending.append({"num": num, "slug": slug})
            continue

        entry = {"num": num, "slug": slug, **info}
        if info["verdict"] == "APPROVE":
            approved.append(entry)
        else:
            rejected.append(entry)
            for issue in info.get("issues", []):
                all_issues.append({"module": slug, "num": num, **issue})

    pattern_counts = count_issue_patterns(all_issues)
    total_reviewed = len(approved) + len(rejected)

    return {
        "track": track_id,
        "total_reviewed": total_reviewed,
        "approved": len(approved),
        "rejected": len(rejected),
        "pending_review": len(pending),
        "approval_rate": (f"{round(len(approved) / total_reviewed * 100)}%" if total_reviewed > 0 else "N/A"),
        "issue_patterns": pattern_counts,
        "rejected_modules": rejected,
        "pending_modules": pending[:10],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def count_issue_patterns(all_issues: list) -> dict:
    """Count keyword patterns across issue summaries."""
    pattern_counts: dict[str, int] = {}
    for issue in all_issues:
        summary = issue["summary"].upper()
        for keyword in ISSUE_PATTERN_KEYWORDS:
            if keyword in summary:
                pattern_counts[keyword] = pattern_counts.get(keyword, 0) + 1
    return pattern_counts
