"""Issue collection and review analysis for state API endpoints.

Handles final review aggregation, outstanding issue collection from
review files and audit failures, and issue pattern counting.
"""

import re
from datetime import UTC, datetime

from .config import CURRICULUM_ROOT, LEVELS
from .state_helpers import (
    PLANS_ROOT,
    detect_pipeline_version,
    find_content_file,
    get_audit_status,
    get_final_review_info,
    get_plan_slugs,
    is_review_stale,
    read_v2_state,
    read_v3_state,
)


CRITICAL_KEYWORDS = frozenset({
    "factual error", "factual mistake", "incorrect", "wrong",
    "grammar error", "grammatical error", "activity error",
    "missing section", "critical",
})

ISSUE_PATTERN_KEYWORDS = [
    "FACTUAL", "PLAN COMPLIANCE", "ACTIVITY", "ANTI-SURZHYK",
    "PRONUNCIATION", "MISLEADING", "COLONIAL", "WORD COUNT",
    "MISSING", "RUSSICISM",
]


def compute_final_reviews(track_id: str, level_cfg: dict) -> dict:
    """Compute final review aggregation for a track."""
    plan_slugs = get_plan_slugs(track_id)
    track_dir = CURRICULUM_ROOT / level_cfg["path"]

    approved = []
    rejected = []
    pending = []
    all_issues = []

    for num, slug in plan_slugs:
        info = get_final_review_info(track_dir, slug)
        if info is None:
            orch_dir = track_dir / "orchestration" / slug
            version = detect_pipeline_version(orch_dir)
            if version == "v5":
                phases = read_v2_state(orch_dir).get("phases", {})
                audit_status = phases.get("validate", {}).get("status")
            else:
                phases = read_v3_state(orch_dir).get("phases", {})
                audit_status = phases.get("v3-audit", {}).get("status")
            if audit_status == "complete":
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
        "approval_rate": (
            f"{round(len(approved) / total_reviewed * 100)}%"
            if total_reviewed > 0 else "N/A"
        ),
        "issue_patterns": pattern_counts,
        "rejected_modules": rejected,
        "pending_modules": pending[:10],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def count_issue_patterns(all_issues: list) -> dict:
    """Count keyword patterns across issue summaries."""
    pattern_counts = {}
    for issue in all_issues:
        summary = issue["summary"].upper()
        for keyword in ISSUE_PATTERN_KEYWORDS:
            if keyword in summary:
                pattern_counts[keyword] = pattern_counts.get(keyword, 0) + 1
    return pattern_counts


def compute_issues(track: str | None, severity: str | None) -> dict:
    """Compute aggregated outstanding issues."""
    issues = []
    level_cfgs = [l for l in LEVELS if l["id"] == track] if track else LEVELS

    for level_cfg in level_cfgs:
        track_id = level_cfg["id"]
        plan_slugs = get_plan_slugs(track_id)
        track_dir = CURRICULUM_ROOT / level_cfg["path"]
        review_dir = track_dir / "review"

        for num, slug in plan_slugs:
            collect_review_issues(
                track_dir, review_dir, track_id, slug, num, issues,
            )
            collect_audit_issues(track_dir, track_id, slug, num, issues)

    if severity:
        issues = [i for i in issues if i["severity"] == severity]

    by_severity: dict[str, int] = {}
    for issue in issues:
        s = issue["severity"]
        by_severity[s] = by_severity.get(s, 0) + 1

    return {"total": len(issues), "by_severity": by_severity, "issues": issues}


def collect_review_issues(track_dir, review_dir, track_id, slug, num, issues):
    """Collect issues from review files for a single module."""
    content_file = find_content_file(track_dir, slug)

    for review_filename in [f"{slug}-review.md", f"{slug}-final-review.md"]:
        review_file = review_dir / review_filename
        if not review_file.exists():
            continue

        if is_review_stale(review_file, content_file):
            continue

        text = review_file.read_text()
        parse_review_blocks(text, review_filename, track_id, slug, num, issues)


def parse_review_blocks(text, review_filename, track_id, slug, num, issues):
    """Parse issue blocks from a review file's text."""
    issue_blocks = re.split(
        r"(?=^#{1,4}\s+Issue\s*#?\s*\d+)",
        text, flags=re.MULTILINE | re.IGNORECASE,
    )
    for block in issue_blocks:
        if not re.match(r"^#{1,4}\s+Issue\s*#?\s*\d+", block, re.IGNORECASE):
            continue

        issue = _parse_single_issue_block(block, review_filename, track_id, slug, num)
        issues.append(issue)


def _parse_single_issue_block(block, review_filename, track_id, slug, num):
    """Parse a single issue block into a structured dict."""
    title_match = re.match(
        r"^#{1,4}\s+Issue\s*#?\s*\d+[:\s\u2014\u2013-]*(.+?)$",
        block, re.MULTILINE | re.IGNORECASE,
    )
    title = title_match.group(1).strip() if title_match else "Issue"

    loc_match = re.search(
        r"(?:\*\*|__)Location(?:\*\*|__)[:\s]+(.+?)(?:\n|$)",
        block, re.IGNORECASE,
    )
    location = loc_match.group(1).strip() if loc_match else ""

    fix_match = re.search(
        r"(?:\*\*|__)Fix(?:\*\*|__)[:\s]+(.+?)(?:\n\n|\Z)",
        block, re.IGNORECASE | re.DOTALL,
    )
    fix = fix_match.group(1).strip()[:200] if fix_match else ""

    combined = (title + " " + block[:300]).lower()
    issue_severity = "warning"
    for kw in CRITICAL_KEYWORDS:
        if kw in combined:
            issue_severity = "critical"
            break

    source_type = "final-review" if "final-review" in review_filename else "review"
    return {
        "track": track_id, "slug": slug, "num": num,
        "source": source_type, "severity": issue_severity,
        "title": title[:80], "location": location[:120], "fix": fix,
    }


def collect_audit_issues(track_dir, track_id, slug, num, issues):
    """Collect audit failure issues for a single module."""
    audit = get_audit_status(track_dir, slug)
    if audit["status"] == "fail":
        for blocking in audit.get("blocking_issues", []):
            issues.append({
                "track": track_id, "slug": slug, "num": num,
                "source": "audit", "severity": "critical",
                "title": f"Audit gate failed: {blocking.get('gate', 'unknown')}",
                "location": blocking.get("gate", ""),
                "fix": blocking.get("message", "")[:200],
            })
