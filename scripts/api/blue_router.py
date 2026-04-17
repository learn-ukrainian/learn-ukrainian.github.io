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

from fastapi import APIRouter, HTTPException, Response

from .config import BATCH_STATE_DIR, CURRICULUM_ROOT, LEVELS, PROJECT_ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.status_cache import get_source_paths, read_status
from slug_utils import to_bare_slug

router = APIRouter(tags=["blue"])


@router.get("/health")
async def health():
    """Health check — Blue dashboard uses this to detect API availability."""
    return {
        "status": "ok",
        "batch_state_dir_exists": BATCH_STATE_DIR.exists(),
    }


@router.get("/live-status", deprecated=True)
async def live_status(response: Response):
    """Ground truth: scan filesystem for actual module files per track.

    DEPRECATED (GH #1309): use ``/api/state/build-status`` (all tracks)
    or ``/api/state/build-status/{track}`` (single track) instead.
    The state endpoints have a stricter contract, are covered by
    tests, and carry per-section freshness metadata. This handler
    remains for backwards compatibility but will be removed.

    Responses carry ``X-Deprecated: true`` and ``X-Deprecated-Use``
    so clients can log a warning without parsing the JSON body.

    Uses #561 status cache (read_status + get_source_paths) for staleness detection.
    This is the real picture — checks what files exist on disk.
    """
    response.headers["X-Deprecated"] = "true"
    response.headers["X-Deprecated-Use"] = "/api/state/build-status"
    response.headers["Warning"] = (
        '299 - "This endpoint is deprecated; migrate to /api/state/build-status (#1309)"'
    )

    results = {}
    for level_cfg in LEVELS:
        track = level_cfg["id"]
        level_dir = CURRICULUM_ROOT / level_cfg["path"]
        if not level_dir.exists():
            continue

        meta_dir = level_dir / "meta"
        status_dir = level_dir / "status"
        modules = []

        if meta_dir.exists():
            for meta_file in sorted(meta_dir.glob("*.yaml")):
                slug = meta_file.stem
                sp = get_source_paths(level_dir, slug)
                has_meta = sp["meta"].exists() if sp["meta"] else False
                has_lesson = sp["md"].exists() if sp["md"] else False
                has_activities = sp["activities"].exists() if sp["activities"] else False
                has_vocab = sp["vocabulary"].exists() if sp["vocabulary"] else False

                status_file = status_dir / f"{slug}.json"
                result = read_status(status_file, source_paths=sp)

                file_count = sum([has_meta, has_lesson, has_activities, has_vocab])
                if result and result.is_fresh and result.status == "pass":
                    state = "pass"
                elif result and not result.is_fresh and result.status == "pass":
                    state = "stale-pass"
                elif file_count == 4:
                    state = "built"
                elif file_count > 1:
                    state = "partial"
                else:
                    state = "skeleton"

                mod_info = {
                    "slug": slug,
                    "state": state,
                    "files": {
                        "meta": has_meta, "lesson": has_lesson,
                        "activities": has_activities, "vocabulary": has_vocab,
                    },
                }
                if result:
                    mod_info["audit_status"] = result.status
                    mod_info["is_fresh"] = result.is_fresh
                modules.append(mod_info)

        results[track] = {
            "module_count": len(modules),
            "states": {
                "pass": sum(1 for m in modules if m["state"] == "pass"),
                "stale_pass": sum(1 for m in modules if m["state"] == "stale-pass"),
                "built": sum(1 for m in modules if m["state"] == "built"),
                "partial": sum(1 for m in modules if m["state"] == "partial"),
                "skeleton": sum(1 for m in modules if m["state"] == "skeleton"),
            },
            "modules": modules,
        }
    return results


@router.get("/freshness")
async def data_freshness():
    """Return data source ages so dashboard can show staleness warnings."""
    sources = {}
    for cp_file in BATCH_STATE_DIR.glob("checkpoint_*.json"):
        track = cp_file.stem.replace("checkpoint_", "")
        try:
            mtime = cp_file.stat().st_mtime
            sources[f"checkpoint_{track}"] = {
                "age_seconds": int(datetime.now().timestamp() - mtime),
            }
        except Exception:
            pass

    ds_file = BATCH_STATE_DIR / "dispatcher_state.json"
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
async def get_audit_status(track_id: str, slug: str, fresh: bool = False):
    """Return audit status for a module.

    Default: reads cached status/{slug}.json (instant).
    ?fresh=true: runs audit_module.sh first, then returns result (10-30s).

    Returns structured JSON — no need to parse terminal output.
    """
    bare = to_bare_slug(slug)
    track_dir = CURRICULUM_ROOT / track_id
    md_candidates = list(track_dir.glob(f"*{bare}.md")) + list(track_dir.glob(f"{slug}.md"))
    md_path = md_candidates[0] if md_candidates else track_dir / f"{slug}.md"
    status_file = track_dir / "status" / f"{bare}.json"

    if fresh:
        if not md_path.exists():
            raise HTTPException(status_code=404, detail=f"Module file not found: {md_path}")
        audit_script = PROJECT_ROOT / "scripts" / "audit_module.sh"
        subprocess.run(
            [str(audit_script), str(md_path)],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read status: {e}") from e

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
async def get_activity_errors(track_id: str, slug: str):
    """Run all 7 structural activity checks and return violations as JSON.

    Runs in-process (no subprocess) — fast. Checks:
      SELECT_MIN_CORRECT_MISMATCH, QUIZ_CORRECT_COUNT,
      FILL_IN_ANSWER_NOT_IN_OPTIONS, TRANSLATE_CORRECT_COUNT,
      MARK_THE_WORDS_ANSWER_NOT_IN_TEXT, UNJUMBLE_RUNON_SENTENCE,
      UNJUMBLE_POSSIBLE_OUT_OF_SCOPE_DATIVE
    """
    bare = to_bare_slug(slug)
    activities_path = CURRICULUM_ROOT / track_id / "activities" / f"{bare}.yaml"

    if not activities_path.exists():
        return {"track": track_id, "slug": slug, "error": "No activities file found", "violations": []}

    try:
        from audit.checks.activity_validation import (
            check_fill_in_answer_in_options,
            check_mark_the_words_answers_in_text,
            check_quiz_single_correct,
            check_select_min_correct,
            check_translate_single_correct,
            check_unjumble_out_of_scope_dative,
            check_unjumble_runon_answer,
        )
        from yaml_activities import ActivityParser
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
    except Exception as e:
        return {"track": track_id, "slug": slug, "error": str(e), "violations": []}

    critical = [v for v in violations if v.get("severity") == "critical"]
    warnings = [v for v in violations if v.get("severity") == "warning"]

    return {
        "track": track_id,
        "slug": slug,
        "activities_file": str(activities_path.relative_to(PROJECT_ROOT)),
        "activity_count": len(activities),
        "total_violations": len(violations),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "violations": violations,
    }


@router.get("/final-review-summary/{track_id}/{slug}")
async def get_final_review_summary(track_id: str, slug: str):
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
    track_dir = CURRICULUM_ROOT / track_id

    # --- 1. Audit status ---
    status_file = track_dir / "status" / f"{bare}.json"
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
                    from datetime import datetime
                    last = datetime.fromisoformat(data["last_audit"].replace("Z", "+00:00"))
                    audit_age_seconds = max(0, int((datetime.now(UTC) - last).total_seconds()))
                except Exception:
                    pass
        except Exception as e:
            audit_summary["error"] = str(e)

    # --- 2. File completeness ---
    md_candidates = list(track_dir.glob(f"*{bare}.md")) + list(track_dir.glob(f"{slug}.md"))
    md_path = md_candidates[0] if md_candidates else None
    files = {
        "lesson": md_path.exists() if md_path else False,
        "activities": (track_dir / "activities" / f"{bare}.yaml").exists(),
        "vocabulary": (track_dir / "vocabulary" / f"{bare}.yaml").exists(),
        "meta": (track_dir / "meta" / f"{bare}.yaml").exists(),
        "review": (track_dir / "review" / f"{bare}-review.md").exists(),
        "audit_log": (track_dir / "audit" / f"{bare}-audit.log").exists(),
    }

    # --- 3. Activity structural errors ---
    activity_errors = {"total_violations": 0, "critical_count": 0, "warning_count": 0, "violations": []}
    activities_path = track_dir / "activities" / f"{bare}.yaml"
    if activities_path.exists():
        try:
            from audit.checks.activity_validation import (
                check_fill_in_answer_in_options,
                check_mark_the_words_answers_in_text,
                check_quiz_single_correct,
                check_select_min_correct,
                check_translate_single_correct,
                check_unjumble_out_of_scope_dative,
                check_unjumble_runon_answer,
            )
            from yaml_activities import ActivityParser
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
        except Exception as e:
            activity_errors["error"] = str(e)

    # --- 4. Review file validation status ---
    review_status = {"exists": files["review"], "warnings": []}
    audit_log = track_dir / "audit" / f"{bare}-audit.log"
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

    verdict = "READY_TO_APPROVE" if (audit_ok and activities_ok and review_ok and not stale) \
        else "NEEDS_REVIEW"

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
