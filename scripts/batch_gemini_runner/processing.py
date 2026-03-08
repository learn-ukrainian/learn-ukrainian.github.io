"""Module processing logic for the batch Gemini runner.

Handles build-mode processing (process_module), fix-mode processing
(process_module_fix), diagnosis, and fix state management.
"""

import json
import re
from datetime import datetime

from audit.status_cache import read_status
from batch_gemini_config import get_module_paths
from batch_utils import atomic_write_json
from slug_utils import review_path as _review_path

from .constants import FAILURES_DIR, MAX_FIX_ITERATIONS, log
from .execution import delete_review_files, run_audit, run_phase
from .prompt import _read_file_safe


def process_module(runner, slug):
    """Run all phases for a single module (build mode).

    Args:
        runner: BatchRunner instance.
        slug: Module slug.

    Returns:
        True if all phases succeeded, False otherwise.
    """
    paths = get_module_paths(runner.track, slug)
    orch_dir = paths["orchestration"]
    orch_dir.mkdir(parents=True, exist_ok=True)

    # In build mode, delete existing review upfront so audit doesn't fail
    # on a stale/fake review during content/activity phases.
    if 5 in runner.config["phases"] and delete_review_files(paths, slug):
        log.info("  Removing existing review (will be regenerated in phase 5)")

    for phase in runner.config["phases"]:
        log.info(f"  Phase {phase}...")
        runner.state["modules"][slug]["phase"] = phase
        runner._save_state()

        success = run_phase(runner, phase, slug, paths)
        if not success:
            return False
    return True


def process_module_fix(runner, slug):
    """Audit-driven fix loop for an existing module.

    1. Check required files exist
    2. Loop: audit -> diagnose -> act (fix_content / fix_activities / apply_fixes)
    3. Stall detection: if same gates fail for 3 consecutive iterations -> break early
    4. Return True when all gates pass, False if exhausted

    Args:
        runner: BatchRunner instance.
        slug: Module slug.

    Returns:
        True if module passes all gates, False if exhausted.
    """
    paths = get_module_paths(runner.track, slug)
    orch_dir = paths["orchestration"]
    orch_dir.mkdir(parents=True, exist_ok=True)

    # Precondition checks
    if not paths["md"].exists():
        log.error(f"  Fix mode requires existing content. Missing: {paths['md']}")
        return False

    content = _read_file_safe(paths["md"])
    word_count = len(content.split())
    if word_count < 200:
        log.error(f"  Content too thin for fix mode ({word_count} words). Use build mode.")
        return False

    if not paths["meta"].exists():
        log.error(f"  Fix mode requires meta file. Missing: {paths['meta']}")
        return False

    if not paths["plan"].exists():
        log.error(f"  Fix mode requires plan file. Missing: {paths['plan']}")
        return False

    fix_state = {
        "slug": slug,
        "iterations": [],
        "started": datetime.now().isoformat() + "Z",
    }
    review_regen_count = 0
    max_review_regens = 2
    # Stall detection: track failing gates across iterations
    previous_failing_gates = []
    stall_count = 0
    max_stall = 3

    for iteration in range(1, MAX_FIX_ITERATIONS + 1):
        log.info(f"  Fix iteration {iteration}/{MAX_FIX_ITERATIONS}")
        iter_state = {
            "iteration": iteration,
            "started": datetime.now().isoformat() + "Z",
        }

        # Step 1: Run audit
        audit_result = run_audit(paths["md"])
        iter_state["audit_passed"] = audit_result["passed"]

        # Step 2: Read status JSON for diagnosis
        status_data = _read_status_json(paths, slug)
        if not status_data:
            log.warning("  Could not read status JSON after audit. Retrying audit...")
            continue

        # Step 3: Diagnose
        action = _diagnose_module(status_data, paths, slug)
        iter_state["action"] = action
        log.info(f"  Diagnosis: {action}")

        # Stall detection: check if same gates keep failing
        current_failing = sorted([
            g for g in ("meta", "lesson", "activities", "vocabulary", "naturalness")
            if status_data.get("gates", {}).get(g, {}).get("status") == "fail"
        ])
        if current_failing == previous_failing_gates and current_failing:
            stall_count += 1
            if stall_count >= max_stall:
                log.error(f"  STALL: Same gates {current_failing} failing for {stall_count} iterations. Breaking early.")
                iter_state["result"] = "stall_detected"
                fix_state["iterations"].append(iter_state)
                break
        else:
            stall_count = 0
        previous_failing_gates = current_failing

        if action == "done":
            iter_state["result"] = "success"
            fix_state["iterations"].append(iter_state)
            fix_state["result"] = "success"
            _save_fix_state(orch_dir, fix_state)
            log.info(f"  Module {slug} passes all gates.")
            return True

        elif action == "generate_fix_plan":
            # Generate review ONLY for its Fix Plan -- review scores are ignored.
            review_regen_count += 1
            if review_regen_count > max_review_regens:
                log.warning(f"  Fix plan generation exhausted ({review_regen_count}/{max_review_regens}).")
                iter_state["result"] = "fix_plan_gen_exhausted"
                fix_state["iterations"].append(iter_state)
                _save_fix_state(orch_dir, fix_state)
                continue

            # Delete old review if present
            if delete_review_files(paths, slug):
                log.info("  Deleting old review...")

            log.info(f"  Running phase 5 for Fix Plan only (attempt {review_regen_count}/{max_review_regens})...")
            success = run_phase(runner, 5, slug, paths)
            if not success:
                iter_state["result"] = "phase5_failed"
                fix_state["iterations"].append(iter_state)
                _save_fix_state(orch_dir, fix_state)
                log.error("  Phase 5 (fix plan generation) failed.")
                return False

            iter_state["result"] = "fix_plan_generated"
            log.info("  Fix Plan generated. Next iteration will apply fixes...")

        elif action == "fix_content":
            log.info("  Running content-only fix phase...")
            success = run_phase(runner, "fix-content", slug, paths)
            if not success:
                iter_state["result"] = "fix_content_failed"
                fix_state["iterations"].append(iter_state)
                _save_fix_state(orch_dir, fix_state)
                log.error("  Content fix phase failed.")
                # Don't return False -- try again next iteration
                continue

            iter_state["result"] = "content_fixed"
            if _check_content_gates_pass(paths, slug):
                iter_state["result"] = "success_after_content_fix"
                fix_state["iterations"].append(iter_state)
                fix_state["result"] = "success"
                _save_fix_state(orch_dir, fix_state)
                log.info(f"  Module {slug} passes all content gates after content fix.")
                return True

        elif action == "fix_activities":
            log.info("  Running activities-only fix phase...")
            # Pass audit errors so the template knows what to fix
            audit_errors = audit_result.get("errors", "")
            success = run_phase(runner, "fix-activities", slug, paths, error_msg=audit_errors)
            if not success:
                iter_state["result"] = "fix_activities_failed"
                fix_state["iterations"].append(iter_state)
                _save_fix_state(orch_dir, fix_state)
                log.error("  Activities fix phase failed.")
                continue

            iter_state["result"] = "activities_fixed"
            if _check_content_gates_pass(paths, slug):
                iter_state["result"] = "success_after_activities_fix"
                fix_state["iterations"].append(iter_state)
                fix_state["result"] = "success"
                _save_fix_state(orch_dir, fix_state)
                log.info(f"  Module {slug} passes all content gates after activities fix.")
                return True

        elif action == "apply_fixes":
            log.info("  Running combined fix phase (applying review Fix Plan)...")
            success = run_phase(runner, "fix", slug, paths)
            if not success:
                iter_state["result"] = "fix_phase_failed"
                fix_state["iterations"].append(iter_state)
                _save_fix_state(orch_dir, fix_state)
                log.error("  Fix phase failed.")
                return False

            iter_state["result"] = "fixes_applied"
            if _check_content_gates_pass(paths, slug):
                iter_state["result"] = "success_after_fix"
                fix_state["iterations"].append(iter_state)
                fix_state["result"] = "success"
                _save_fix_state(orch_dir, fix_state)
                log.info(f"  Module {slug} passes all content gates after fix (review skipped -- anti-gaming).")
                return True

        fix_state["iterations"].append(iter_state)
        _save_fix_state(orch_dir, fix_state)

    # Exhausted all iterations -- save to failure queue for Claude review
    fix_state["result"] = "exhausted"
    _save_fix_state(orch_dir, fix_state)
    _save_failure(runner, slug, fix_state, status_data)
    log.error(f"  Fix mode exhausted {MAX_FIX_ITERATIONS} iterations for {slug}.")
    return False


def _check_content_gates_pass(paths, slug):
    """Check if all content gates pass (anti-gaming: ignore review gate)."""
    post_fix_status = _read_status_json(paths, slug)
    if not post_fix_status:
        return False
    post_fix_gates = post_fix_status.get("gates", {})
    gates_ok = all(
        post_fix_gates.get(g, {}).get("status") != "fail"
        for g in ("meta", "lesson", "activities", "vocabulary", "naturalness")
    )
    post_blocking = post_fix_status.get("overall", {}).get("blocking_issues", [])
    post_content_blocking = [
        i for i in post_blocking
        if not any(kw in i.lower() for kw in ("review", "review validation"))
    ]
    return gates_ok and not post_content_blocking


def _diagnose_module(status_data, paths, slug):
    """Analyze status JSON and decide what action to take.

    Returns one of: "done", "fix_content", "fix_activities", "apply_fixes",
                     "generate_fix_plan"

    ARCHITECTURAL RULE: Gemini NEVER reviews its own batch work.
    Self-review is inherently biased (self-grading produces inflated scores).
    The automated audit gates (meta, lesson, activities, vocabulary, naturalness)
    are the quality check in fix mode. When all content gates pass, the module
    is done -- no LLM review needed. Reviews are only meaningful when done by
    a DIFFERENT agent (e.g., Claude reviewing Gemini's work via /review-content).
    """
    overall = status_data.get("overall", {})
    gates = status_data.get("gates", {})

    # Check if everything passes (including review if it exists)
    if overall.get("status") == "pass":
        return "done"

    # Check content gates only -- review gate is IGNORED in fix mode
    failing_gates = []
    for gate_name in ("meta", "lesson", "activities", "vocabulary", "naturalness"):
        gate = gates.get(gate_name, {})
        if gate.get("status") == "fail":
            failing_gates.append(gate_name)

    # Also check blocking_issues (e.g., outline compliance errors)
    # These set has_critical_failure in audit but aren't captured in gates
    blocking_issues = overall.get("blocking_issues", [])
    # Filter out review-related blocking issues (anti-gaming)
    content_blocking = [
        issue for issue in blocking_issues
        if not any(kw in issue.lower() for kw in ("review", "review validation"))
    ]

    # All content gates pass AND no content blocking issues -> done
    if not failing_gates and not content_blocking:
        log.info("  All content gates pass. Skipping self-review (anti-gaming).")
        return "done"

    if content_blocking:
        failing_gates.extend([f"blocking:{issue}" for issue in content_blocking])

    # Categorize failures for targeted fix routing
    content_failed = (
        "lesson" in failing_gates or
        "naturalness" in failing_gates or
        any(g.startswith("blocking:") for g in failing_gates)
    )
    activities_failed = "activities" in failing_gates or "vocabulary" in failing_gates

    # Route to targeted fix (split phases to avoid truncation)
    if content_failed:
        # Content issues -- check if review has a Fix Plan for content
        rev_path = _review_path(paths["md"].parent, slug)
        review_exists = rev_path.exists()
        has_fix_plan = False
        if review_exists:
            review_content = _read_file_safe(rev_path)
            has_fix_plan = "Fix Plan" in review_content or "fix plan" in review_content.lower()

        if review_exists and has_fix_plan:
            return "fix_content"

        # No Fix Plan -- generate review to get one
        log.info(f"  Content gates failing: {failing_gates}. Generating review for Fix Plan...")
        return "generate_fix_plan"

    elif activities_failed:
        # Only activities/vocabulary failed -- use targeted fix
        log.info(f"  Activity gates failing: {failing_gates}. Running targeted activity fix...")
        return "fix_activities"

    # Fallback: if only meta fails, try the combined fix
    if _review_path(paths["md"].parent, slug).exists():
        return "apply_fixes"

    log.info(f"  Gates failing: {failing_gates}. Generating review for Fix Plan...")
    return "generate_fix_plan"


def _read_status_json(paths, slug):
    """Read the status JSON for a module via the shared status cache layer.

    Returns the raw data dict (for backward compatibility with callers
    that access gates directly), or None if not found.
    """
    status_dir = paths["md"].parent / "status"
    status_file = status_dir / f"{paths['md'].stem}.json"
    # No source_paths -> skip freshness check (runner always re-audits anyway)
    result = read_status(status_file)
    return result.data if result else None


def _save_fix_state(orch_dir, fix_state):
    """Save fix tracking state to orchestration dir."""
    fix_state_file = orch_dir / "fix-state.json"
    atomic_write_json(fix_state_file, fix_state)


def _save_failure(runner, slug, fix_state, last_status):
    """Save failure details for Claude review.

    Creates batch_state/failures/{track}/{slug}.json with:
    - Which gates failed and why
    - What actions were tried
    - Last audit status
    - Enough context for Claude to diagnose the root cause
    """
    failures_dir = FAILURES_DIR / runner.track
    failures_dir.mkdir(parents=True, exist_ok=True)

    # Extract failed gates from last status
    gates = last_status.get("gates", {})
    failed_gates = {
        name: info for name, info in gates.items()
        if isinstance(info, dict) and info.get("status") == "fail"
    }

    # Extract dryness flags from last status
    dryness_flags = last_status.get("dryness_flags", [])

    # Summarize iterations
    actions_tried = []
    for it in fix_state.get("iterations", []):
        actions_tried.append({
            "iteration": it.get("iteration"),
            "diagnosis": it.get("action"),
            "result": it.get("result"),
        })

    # Extract word count from lesson gate message (e.g. "4234/4300 (raw: 4337)")
    lesson_msg = gates.get("lesson", {}).get("message", "")
    word_count = {}
    wc_match = re.match(r"(\d+)/(\d+)", lesson_msg)
    if wc_match:
        word_count = {
            "actual": int(wc_match.group(1)),
            "target": int(wc_match.group(2)),
        }

    failure = {
        "track": runner.track,
        "slug": slug,
        "timestamp": datetime.now().isoformat() + "Z",
        "iterations_used": len(fix_state.get("iterations", [])),
        "failed_gates": failed_gates,
        "dryness_flags": dryness_flags,
        "actions_tried": actions_tried,
        "blocking_issues": last_status.get("overall", {}).get("blocking_issues", []),
        "word_count": word_count,
    }

    failure_file = failures_dir / f"{slug}.json"

    # Check if already escalated -- don't spam the broker on re-failures
    if failure_file.exists():
        try:
            prev = json.loads(failure_file.read_text(encoding="utf-8"))
            prev.get("escalated", False)
        except Exception:
            pass

    # Disable automatic escalation -- stay in Gemini fix loop
    failure["escalated"] = False

    # Diagnostic print
    log.error(f"  GIVING UP on {slug} after {failure['iterations_used']} iterations.")
    log.error(f"  Reason: Failed gates: {', '.join(failed_gates.keys())}")
    for g, info in failed_gates.items():
        log.error(f"    - {g}: {info.get('message')}")
    if failure.get("blocking_issues"):
        log.error(f"  Blocking issues: {failure['blocking_issues']}")

    atomic_write_json(failure_file, failure)
    log.info(f"  Failure saved: {failure_file}")

    return  # Stop here -- do not send broker message to Claude
