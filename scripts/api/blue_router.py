"""
Blue Team API router — endpoints for the Blue (Claude) batch monitor dashboard.

Mounted at /api/blue/ in main.py. Gold team cannot conflict with these endpoints.
"""

import json
import subprocess

# Import #561 status cache layer
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)

from .monitor_context import MonitorContext, get_ctx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.checks.activity_validation import (
    check_fill_in_answer_in_options,
    check_mark_the_words_answers_in_text,
    check_quiz_single_correct,
    check_select_min_correct,
    check_translate_single_correct,
    check_unjumble_out_of_scope_dative,
    check_unjumble_runon_answer,
)
from slug_utils import to_bare_slug
from yaml_activities import ActivityParser

AUDIT_MODULE_TIMEOUT_SECONDS: float = 60.0

router = APIRouter(tags=["blue"])


@router.get("/health")
async def health(ctx: MonitorContext = Depends(get_ctx)):
    """Health check — Blue dashboard uses this to detect API availability."""
    return {
        "status": "ok",
        "batch_state_dir_exists": ctx.roots.batch_state_dir.exists(),
    }


@router.get("/freshness")
async def data_freshness(ctx: MonitorContext = Depends(get_ctx)):
    """Return data source ages so dashboard can show staleness warnings."""
    sources = {}
    batch_state_dir = ctx.roots.batch_state_dir
    for cp_file in batch_state_dir.glob("checkpoint_*.json"):
        track = cp_file.stem.replace("checkpoint_", "")
        try:
            mtime = cp_file.stat().st_mtime
            sources[f"checkpoint_{track}"] = {
                "age_seconds": int(datetime.now().timestamp() - mtime),
            }
        except Exception:
            pass

    ds_file = batch_state_dir / "dispatcher_state.json"
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


@router.get("/audit/{track_id}/{slug}")
async def get_audit_status(
    track_id: str, slug: str, fresh: bool = False, ctx: MonitorContext = Depends(get_ctx)
):
    """Return audit status for a module.

    Default: reads cached status/{slug}.json (instant).
    ?fresh=true: runs audit_module.sh first, then returns result (10-30s).

    Returns structured JSON — no need to parse terminal output.
    """
    bare = to_bare_slug(slug)
    project_root = ctx.roots.project_root
    try:
        track_dir = safe_join(ctx.roots.curriculum_root, track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track/slug") from None
    md_candidates = list(track_dir.glob(f"*{bare}.md"))
    md_path = md_candidates[0] if md_candidates else safe_join(track_dir, f"{slug}.md")
    status_file = safe_join(track_dir, "status", f"{bare}.json")

    if fresh:
        if not md_path.exists():
            raise HTTPException(status_code=404, detail=f"Module file not found: {md_path}")
        audit_script = project_root / "scripts" / "audit_module.sh"
        try:
            subprocess.run(
                [str(audit_script), str(md_path)],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=AUDIT_MODULE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail=f"Audit execution timed out after {AUDIT_MODULE_TIMEOUT_SECONDS}s",
            ) from None
        # Script writes status JSON as a side effect — re-read below

    if not status_file.exists():
        return {
            "track": track_id,
            "slug": slug,
            "status": "not_audited",
            "message": "No status file found. Run with ?fresh=true to audit.",
        }

    try:
        with open(status_file) as f:
            data = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read status") from None

    # Surface the most important info at the top level
    overall = data.get("overall", {})
    gates = data.get("gates", {})
    return {
        "track": track_id,
        "slug": slug,
        "overall_status": overall.get("status", "unknown"),
        "pass_count": overall.get("pass_count", 0),
        "fail_count": overall.get("fail_count", 0),
        "blocking_issues": overall.get("blocking_issues", []),
        "last_audit": data.get("last_audit"),
        "gates": {
            name: {
                "status": g.get("status"),
                "message": g.get("message", ""),
                "violations": g.get("violations", 0),
            }
            for name, g in gates.items()
        },
        "fresh": fresh,
    }


@router.get("/activity-errors/{track_id}/{slug}")
async def get_activity_errors(track_id: str, slug: str, ctx: MonitorContext = Depends(get_ctx)):
    """Run all 7 structural activity checks and return violations as JSON.

    Runs in-process (no subprocess) — fast. Checks:
      SELECT_MIN_CORRECT_MISMATCH, QUIZ_CORRECT_COUNT,
      FILL_IN_ANSWER_NOT_IN_OPTIONS, TRANSLATE_CORRECT_COUNT,
      MARK_THE_WORDS_ANSWER_NOT_IN_TEXT, UNJUMBLE_RUNON_SENTENCE,
      UNJUMBLE_POSSIBLE_OUT_OF_SCOPE_DATIVE
    """
    bare = to_bare_slug(slug)
    activities_path = safe_join(ctx.roots.curriculum_root, track_id, "activities", f"{bare}.yaml")

    if not activities_path.exists():
        return {"track": track_id, "slug": slug, "error": "No activities file found", "violations": []}

    try:
        parser = ActivityParser()
        activities = parser.parse(activities_path)

        violations = (
            check_select_min_correct(activities)
            + check_quiz_single_correct(activities)
            + check_fill_in_answer_in_options(activities)
            + check_translate_single_correct(activities)
            + check_mark_the_words_answers_in_text(activities)
            + check_unjumble_runon_answer(activities)
            + check_unjumble_out_of_scope_dative(activities)
        )
    except Exception:
        return {"track": track_id, "slug": slug, "error": "Validation failed", "violations": []}

    critical = [v for v in violations if v.get("severity") == "critical"]
    warnings = [v for v in violations if v.get("severity") == "warning"]

    return {
        "track": track_id,
        "slug": slug,
        "activities_file": str(activities_path.relative_to(ctx.roots.project_root)),
        "activity_count": len(activities),
        "total_violations": len(violations),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "violations": violations,
    }


@router.get("/final-review-summary/{track_id}/{slug}")
async def get_final_review_summary(track_id: str, slug: str, ctx: MonitorContext = Depends(get_ctx)):
    """Aggregate endpoint for Claude's /final-review workflow.

    One call returns everything needed to start a final review:
      - Audit gate summary (pass/fail per gate)
      - Activity structural errors (all 7 checks)
      - Review file status (exists? citation warnings?)
      - Build completeness (all 4 files present?)
      - Staleness (seconds since last audit)

    Replaces: reading status JSON + running scan_activity_errors +
              checking review file + checking audit log separately.
    """
    bare = to_bare_slug(slug)
    try:
        track_dir = safe_join(ctx.roots.curriculum_root, track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track/slug") from None

    # --- 1. Audit status ---
    status_file = safe_join(track_dir, "status", f"{bare}.json")
    audit_summary = {"status": "not_audited", "gates": {}, "blocking_issues": []}
    audit_age_seconds = None

    if status_file.exists():
        try:
            with open(status_file) as f:
                data = json.load(f)
            overall = data.get("overall", {})
            audit_summary = {
                "status": overall.get("status", "unknown"),
                "pass_count": overall.get("pass_count", 0),
                "fail_count": overall.get("fail_count", 0),
                "blocking_issues": overall.get("blocking_issues", []),
                "gates": {
                    name: {"status": g.get("status"), "message": g.get("message", "")}
                    for name, g in data.get("gates", {}).items()
                },
            }
            if data.get("last_audit"):
                try:
                    last = datetime.fromisoformat(data["last_audit"].replace("Z", "+00:00"))
                    audit_age_seconds = max(0, int((datetime.now(UTC) - last).total_seconds()))
                except Exception:
                    pass
        except Exception:
            audit_summary["error"] = "Failed to load audit status"

    # --- 2. File completeness ---
    md_path = safe_join(track_dir, f"{slug}.md")
    files = {
        "lesson": md_path.exists() if md_path else False,
        "activities": safe_join(track_dir, "activities", f"{bare}.yaml").exists(),
        "vocabulary": safe_join(track_dir, "vocabulary", f"{bare}.yaml").exists(),
        "meta": safe_join(track_dir, "meta", f"{bare}.yaml").exists(),
        "review": safe_join(track_dir, "review", f"{bare}-review.md").exists(),
        "audit_log": safe_join(track_dir, "audit", f"{bare}-audit.log").exists(),
    }

    # --- 3. Activity structural errors ---
    activity_errors = {"total_violations": 0, "critical_count": 0, "warning_count": 0, "violations": []}
    activities_path = safe_join(track_dir, "activities", f"{bare}.yaml")
    if activities_path.exists():
        try:
            activities = ActivityParser().parse(activities_path)
            violations = (
                check_select_min_correct(activities)
                + check_quiz_single_correct(activities)
                + check_fill_in_answer_in_options(activities)
                + check_translate_single_correct(activities)
                + check_mark_the_words_answers_in_text(activities)
                + check_unjumble_runon_answer(activities)
                + check_unjumble_out_of_scope_dative(activities)
            )
            activity_errors = {
                "total_violations": len(violations),
                "critical_count": sum(1 for v in violations if v.get("severity") == "critical"),
                "warning_count": sum(1 for v in violations if v.get("severity") == "warning"),
                "violations": violations,
            }
        except Exception:
            activity_errors["error"] = "Failed to parse activities"

    # --- 4. Review file validation status ---
    review_status = {"exists": files["review"], "warnings": []}
    audit_log = safe_join(track_dir, "audit", f"{bare}-audit.log")
    if audit_log.exists():
        log_text = audit_log.read_text()
        if "UNVERIFIED_CITATIONS" in log_text:
            review_status["warnings"].append("UNVERIFIED_CITATIONS: review cites text not found in module")
        if "RUBBER_STAMP" in log_text or "GAMING_LANGUAGE" in log_text:
            review_status["warnings"].append("Review integrity check failed — possible self-grading")

    # --- 5. Quick verdict ---
    audit_ok = audit_summary.get("status") == "pass"
    activities_ok = activity_errors["critical_count"] == 0
    review_ok = review_status["exists"] and not review_status["warnings"]
    stale = audit_age_seconds is not None and audit_age_seconds > 3600

    verdict = "READY_TO_APPROVE" if (audit_ok and activities_ok and review_ok and not stale) else "NEEDS_REVIEW"

    return {
        "track": track_id,
        "slug": slug,
        "verdict": verdict,
        "audit_age_seconds": audit_age_seconds,
        "audit_stale": stale,
        "audit": audit_summary,
        "files": files,
        "activity_errors": activity_errors,
        "review": review_status,
    }
