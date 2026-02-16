#!/usr/bin/env python3
"""Deterministic E2E Module Builder v2 — Single Pipeline.

Replaces v1's split content-only / enrich / full modes with a unified pipeline.
Supports archive restoration for 1.4M words of research-based prose.

Pipeline:
    Phase 0:  Research              [SKIP if archived prose > 2000w]
    Phase 1:  Meta/Outline          [always]
    Phase 2:  Write Prose           [SKIP if archived prose — restore from archive]
    Phase 3:  Prose Audit+Fix Loop  [max 3 iters, Legacy Cleanse for archived]
    Phase 4a: Activities Gen        [parallel with 4b]
    Phase 4b: Vocabulary Gen        [parallel with 4a]
    Phase 5:  Enrichment Audit+Fix  [max 3 iters, activities+vocab focus]
    Phase 6:  Adversarial Review    [fresh Gemini session]
    Phase 6b: Apply Review Fixes    [verification pass]
    Phase 7:  Final Audit+Fix       [max 2 iters, comprehensive]
    Phase 8:  MDX Generation+Lint   [deterministic, no LLM]

Usage:
    .venv/bin/python scripts/build_module_v2.py {track} {num}               # Full E2E
    .venv/bin/python scripts/build_module_v2.py {track} {num} --rebuild     # Nuke state, restart
    .venv/bin/python scripts/build_module_v2.py {track} {num} --force-phase 3  # Re-run phase
    .venv/bin/python scripts/build_module_v2.py {track} {num} --dry-run     # Show plan
    .venv/bin/python scripts/build_module_v2.py {track} {num} --verify      # Just audit
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Imports from v1 — build_module.py is the utility library
# ---------------------------------------------------------------------------
import build_module as v1
from build_module import (
    # Config tables (re-exported for batch dispatchers that may import from v2)
    TRACK_SKILLS, IMMERSION_RULES, LEVEL_CONSTRAINTS, ACTIVITY_CONFIGS,
    # Resolvers
    get_track_skill, get_immersion_rule, get_level_constraints,
    get_activity_config, get_level_label,
    # State machine
    load_state, save_state, is_phase_complete, _now_iso,
    # Dispatch helpers
    run_script, fill_template, dispatch_gemini,
    extract_phase_output, run_verify, VENV_PYTHON,
    # Phase helpers
    _build_seam_context, _parse_section, _apply_section_fixes,
    _identify_affected_sections, _build_fix_prompt,
    _is_rubber_stamp, _compute_audit_metrics,
    _gemini_output_path, _dispatch_prompt,
    # Phase functions (reused via delegation)
    phase_0_research, phase_1_meta, phase_2_content,
    phase_3a_activities, phase_3b_vocabulary,
    phase_6_review, phase_6b_apply_fixes, phase_5_mdx,
    # Preflight helpers
    write_placeholders, get_tier_guidance, TIER_MAP,
    # Logging
    _init_log, log,
    # Constants
    ModuleContext,
)
from batch_gemini_config import (
    CURRICULUM_DIR, PHASES_DIR, PRO_MODEL, PROJECT_ROOT, SEMINAR_TRACKS,
    get_module_paths, get_track_config, slug_for_num,
)

# ---------------------------------------------------------------------------
# Thread-safe state via filelock
# ---------------------------------------------------------------------------
try:
    from filelock import FileLock
except ImportError:
    # Fallback: no-op lock (single-threaded is fine for most runs)
    class FileLock:  # type: ignore[no-redef]
        def __init__(self, path: str | Path):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a: Any):
            pass

_state_lock: FileLock | None = None


def _init_state_lock(ctx: ModuleContext) -> None:
    """Create a file-based lock for thread-safe state writes."""
    global _state_lock
    lock_path = ctx.orch_dir / "state.json.lock"
    _state_lock = FileLock(str(lock_path))


def mark_phase_locked(ctx: ModuleContext, phase: str, status: str, **extra: Any) -> None:
    """Thread-safe wrapper around v1's mark_phase."""
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state.json.lock"))
    with lock:
        _original_mark_phase(ctx, phase, status, **extra)


# Monkey-patch v1's mark_phase so all delegated phase functions use locking
_original_mark_phase = v1.mark_phase
v1.mark_phase = mark_phase_locked  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Archive Detection + Restoration
# ---------------------------------------------------------------------------
ARCHIVE_DIR = PROJECT_ROOT / "_archive"
ARCHIVE_WORD_THRESHOLD = 2000
# Git commit before clean-slate rebuild (prose lives in parent)
ARCHIVE_GIT_REF = "944f3524a^"


def detect_archived_prose(track: str, slug: str) -> tuple[bool, str, Path | None]:
    """Check for restorable archived prose.

    Search order:
      1. _archive/{track}/{latest_timestamp}/{slug}.md  (filesystem)
      2. git show 944f3524a^:curriculum/l2-uk-en/{track}/{slug}.md  (git history)

    Returns (is_archived, source_description, archive_dir_or_None).
    For git-based archives, archive_dir is None (content extracted on demand).
    """
    # --- Filesystem archive ---
    track_archive = ARCHIVE_DIR / track
    if track_archive.is_dir():
        # Find latest timestamp dir (sorted lexicographically = chronologically)
        ts_dirs = sorted(
            [d for d in track_archive.iterdir() if d.is_dir() and not d.name.startswith("_")],
            reverse=True,
        )
        for ts_dir in ts_dirs:
            md_path = ts_dir / f"{slug}.md"
            if md_path.exists():
                word_count = len(md_path.read_text(encoding="utf-8").split())
                if word_count >= ARCHIVE_WORD_THRESHOLD:
                    return True, f"filesystem: {ts_dir.name} ({word_count}w)", ts_dir
                log(f"  Archive: found {md_path.name} but only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")

    # --- Git history archive ---
    try:
        git_path = f"curriculum/l2-uk-en/{track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0 and result.stdout:
            word_count = len(result.stdout.split())
            if word_count >= ARCHIVE_WORD_THRESHOLD:
                return True, f"git:{ARCHIVE_GIT_REF} ({word_count}w)", None
    except (subprocess.TimeoutExpired, OSError):
        pass

    return False, "", None


def restore_from_archive(
    ctx: ModuleContext, archive_dir: Path | None,
) -> bool:
    """Restore archived prose (and optionally meta/activities/vocab) to live paths.

    If archive_dir is None, restores from git history.
    Returns True if content was successfully restored.
    """
    slug = ctx.slug
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Restore prose only (NOT meta — Phase 1 already generated fresh meta)
    if archive_dir is not None:
        src_md = archive_dir / f"{slug}.md"
        if not src_md.exists():
            log(f"  Restore: {src_md} not found")
            return False
        shutil.copy2(src_md, content_path)
        log(f"  Restore: prose {src_md.name} → {content_path.name}")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0 or not result.stdout:
            log("  Restore: git extraction failed")
            return False
        content_path.write_text(result.stdout, encoding="utf-8")
        log(f"  Restore: git:{ARCHIVE_GIT_REF}:{git_path} → {content_path.name}")

    # Step 2: Verify word count BEFORE restoring supplementary files
    if not content_path.exists():
        return False
    word_count = len(content_path.read_text(encoding="utf-8").split())
    if word_count < ARCHIVE_WORD_THRESHOLD:
        log(f"  Restore: REJECTED — only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
        content_path.unlink()  # Clean up — don't leave debris
        return False

    # Step 3: Restore activities + vocabulary (NOT meta — fresh from Phase 1)
    for sub, dest_key in [("activities", "activities"), ("vocabulary", "vocabulary")]:
        if archive_dir is not None:
            src = archive_dir / sub / f"{slug}.yaml"
            if src.exists():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, ctx.paths[dest_key])
                log(f"  Restore: {sub}/{slug}.yaml")
        else:
            git_sub = f"curriculum/l2-uk-en/{ctx.track}/{sub}/{slug}.yaml"
            r = subprocess.run(
                ["git", "show", f"{ARCHIVE_GIT_REF}:{git_sub}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            if r.returncode == 0 and r.stdout.strip():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                ctx.paths[dest_key].write_text(r.stdout, encoding="utf-8")
                log(f"  Restore: git {sub}/{slug}.yaml")

    pct = word_count * 100 // max(ctx.word_target, 1)
    log(f"  Restore: {word_count} words ({pct}% of {ctx.word_target} target)")
    return True


# ---------------------------------------------------------------------------
# V2 Phase Functions
# ---------------------------------------------------------------------------
MAX_PROSE_FIX_ITERS = 3
MAX_ENRICHMENT_FIX_ITERS = 3
MAX_FINAL_FIX_ITERS = 2


def phase_0_v2(ctx: ModuleContext) -> bool:
    """Phase 0: Research. Always runs — plan + research = source of truth."""
    return phase_0_research(ctx)


def phase_1_v2(ctx: ModuleContext) -> bool:
    """Phase 1: Meta/Outline. Always runs."""
    return phase_1_meta(ctx)


def _check_archive_fits_outline(ctx: ModuleContext) -> tuple[bool, list[str], list[str]]:
    """Check if archived prose covers the sections from the current content_outline.

    Returns (fits, matched_sections, missing_sections).
    A module "fits" if at least 70% of outline sections have matching H2s in archive.
    """
    archive_dir = getattr(ctx, "archive_dir", None)
    slug = ctx.slug

    # Read archived prose
    if archive_dir is not None:
        src = archive_dir / f"{slug}.md"
        if not src.exists():
            return False, [], []
        content = src.read_text(encoding="utf-8")
    else:
        # Git archive — read content
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return False, [], []
        content = result.stdout

    # Extract H2 headers from archived prose
    archive_h2s = {h.strip().lower() for h in re.findall(r"^## (.+)$", content, re.MULTILINE)}

    # Compare against outline
    outline = ctx.content_outline
    if not outline:
        # No outline yet — can't compare, assume it fits if word count is good
        word_count = len(content.split())
        return word_count >= ARCHIVE_WORD_THRESHOLD, [], []

    matched = []
    missing = []
    for section in outline:
        title, _ = _parse_section(section)
        if title.strip().lower() in archive_h2s:
            matched.append(title)
        else:
            missing.append(title)

    total = len(outline)
    coverage = len(matched) / total if total > 0 else 0
    fits = coverage >= 0.7  # 70% section coverage threshold

    return fits, matched, missing


def phase_2_v2(ctx: ModuleContext) -> bool:
    """Phase 2: Write Prose. Checks archived prose against plan+research outline.

    Archive is used only if it covers >=70% of the content_outline sections.
    Plan + research remain the source of truth.
    """
    phase = "2"
    if is_phase_complete(ctx, phase):
        log("  Phase 2: SKIP (already complete)")
        return True

    if getattr(ctx, "is_archived", False):
        fits, matched, missing = _check_archive_fits_outline(ctx)
        archive_source = getattr(ctx, "archive_source", "unknown")

        if fits:
            log(f"  Phase 2: Archive fits outline — {len(matched)}/{len(matched)+len(missing)} sections match")
            if missing:
                log(f"  Phase 2: Missing sections (will be caught in Phase 3): {', '.join(missing)}")

            if ctx.dry_run:
                log(f"  Phase 2: DRY-RUN — would restore from archive ({archive_source})")
                return True

            archive_dir = getattr(ctx, "archive_dir", None)
            if restore_from_archive(ctx, archive_dir):
                mark_phase_locked(ctx, phase, "complete", note="restored-from-archive",
                                  source=archive_source,
                                  sections_matched=len(matched),
                                  sections_missing=len(missing))
                return True
            else:
                log("  Phase 2: Archive restore FAILED — falling back to generation")
        else:
            log(f"  Phase 2: Archive does NOT fit outline — only {len(matched)}/{len(matched)+len(missing)} sections match")
            log(f"  Phase 2: Generating fresh prose instead")
            # Fall through to v1 content generation

    return phase_2_content(ctx)


def phase_3_prose_audit_fix(ctx: ModuleContext) -> bool:
    """Phase 3: Prose-only audit+fix loop (max 3 iterations).

    For archived content, also runs Legacy Cleanse (IPA lint, outline compliance).
    """
    phase = "3"
    if is_phase_complete(ctx, phase):
        log("  Phase 3: SKIP (already complete)")
        return True

    if ctx.dry_run:
        extra = " + Legacy Cleanse" if getattr(ctx, "is_archived", False) else ""
        log(f"  Phase 3: DRY-RUN — would run prose audit{extra}")
        return True

    # Legacy Cleanse for archived content
    if getattr(ctx, "is_archived", False):
        _run_legacy_cleanse(ctx)

    for attempt in range(1, MAX_PROSE_FIX_ITERS + 1):
        log(f"  Phase 3: Prose audit attempt {attempt}/{MAX_PROSE_FIX_ITERS}...")
        passed, output = run_verify(ctx.paths["md"], content_only=True)

        log_file = ctx.orch_dir / f"phase3-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            log(f"  Phase 3: PASS (attempt {attempt})")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        log(f"  Phase 3: FAIL (attempt {attempt})")
        if attempt >= MAX_PROSE_FIX_ITERS:
            log(f"  Phase 3: EXHAUSTED — {MAX_PROSE_FIX_ITERS} attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch fix to Gemini
        fix_prompt = _build_fix_prompt(ctx, output, content_only=True)
        fix_prompt_file = ctx.orch_dir / f"phase3-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 3: Dispatching prose fix {attempt}...")
        fix_output = _gemini_output_path(ctx.slug, f"p3-fix{attempt}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p3fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 3: Fix dispatch {attempt} failed")
            continue

        # Apply section-level fixes
        if fix_output.exists():
            fix_text = fix_output.read_text(encoding="utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


def _run_legacy_cleanse(ctx: ModuleContext) -> None:
    """Modernize archived content: IPA lint, outline compliance check."""
    content_path = ctx.paths["md"]
    if not content_path.exists():
        return

    log("  Legacy Cleanse: running IPA lint...")
    run_script(
        [str(SCRIPTS_DIR / "lint_ipa.py"), str(content_path), "--fix"],
        capture=True,
    )

    # Check outline compliance: verify all H2 sections from plan exist
    outline = ctx.content_outline
    if not outline:
        return

    content = content_path.read_text(encoding="utf-8")
    existing_h2s = {h.strip().lower() for h in re.findall(r"^## (.+)$", content, re.MULTILINE)}
    missing = []
    for section in outline:
        title, _ = _parse_section(section)
        if title.strip().lower() not in existing_h2s:
            missing.append(title)

    if missing:
        log(f"  Legacy Cleanse: {len(missing)} outline sections missing from archived content:")
        for m in missing:
            log(f"    - {m}")
        # These will be caught by the audit loop in Phase 3


# Phase 4a/4b use v1 functions directly. The phase IDs in state.json use
# v1's "3a"/"3b" names for backward compatibility with existing state files.

def phase_4a_activities(ctx: ModuleContext) -> bool:
    """Phase 4a: Activities generation. Delegates to v1's phase_3a (state ID: '3a')."""
    return phase_3a_activities(ctx)


def phase_4b_vocabulary(ctx: ModuleContext) -> bool:
    """Phase 4b: Vocabulary generation. Delegates to v1's phase_3b (state ID: '3b')."""
    return phase_3b_vocabulary(ctx)


def _run_parallel_4ab(ctx: ModuleContext) -> bool:
    """Run activities + vocabulary generation in parallel via ThreadPoolExecutor.

    Falls back to sequential in dry-run mode.
    """
    if ctx.dry_run:
        if not phase_4a_activities(ctx):
            return False
        return phase_4b_vocabulary(ctx)

    # Check if both already complete
    if is_phase_complete(ctx, "3a") and is_phase_complete(ctx, "3b"):
        log("  Phase 4a+4b: SKIP (both already complete)")
        return True

    results: dict[str, bool] = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        if not is_phase_complete(ctx, "3a"):
            futures[executor.submit(phase_4a_activities, ctx)] = "4a"
        else:
            results["4a"] = True
            log("  Phase 4a: SKIP (already complete)")

        if not is_phase_complete(ctx, "3b"):
            futures[executor.submit(phase_4b_vocabulary, ctx)] = "4b"
        else:
            results["4b"] = True
            log("  Phase 4b: SKIP (already complete)")

        for future in as_completed(futures):
            phase_name = futures[future]
            try:
                results[phase_name] = future.result()
            except Exception as e:
                log(f"  Phase {phase_name}: EXCEPTION — {e}")
                results[phase_name] = False

    if not results.get("4a", False):
        log("  Phase 4a: FAILED")
        return False
    if not results.get("4b", False):
        log("  Phase 4b: FAILED")
        return False

    return True


def phase_5_enrichment_audit_fix(ctx: ModuleContext) -> bool:
    """Phase 5: Enrichment audit+fix loop (activities + vocab focus, max 3 iters)."""
    phase = "5-enrich"
    if is_phase_complete(ctx, phase):
        log("  Phase 5: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 5: DRY-RUN — would run enrichment audit")
        return True

    for attempt in range(1, MAX_ENRICHMENT_FIX_ITERS + 1):
        log(f"  Phase 5: Enrichment audit attempt {attempt}/{MAX_ENRICHMENT_FIX_ITERS}...")
        passed, output = run_verify(ctx.paths["md"], content_only=False)

        log_file = ctx.orch_dir / f"phase5-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            log(f"  Phase 5: PASS (attempt {attempt})")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        log(f"  Phase 5: FAIL (attempt {attempt})")
        if attempt >= MAX_ENRICHMENT_FIX_ITERS:
            log(f"  Phase 5: EXHAUSTED — {MAX_ENRICHMENT_FIX_ITERS} attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch enrichment fix
        fix_prompt = _build_fix_prompt(ctx, output, content_only=False)
        fix_prompt_file = ctx.orch_dir / f"phase5-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 5: Dispatching enrichment fix {attempt}...")
        fix_output = _gemini_output_path(ctx.slug, f"p5-fix{attempt}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p5fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 5: Fix dispatch {attempt} failed")
            continue

        if fix_output.exists():
            fix_text = fix_output.read_text(encoding="utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


def phase_6_v2(ctx: ModuleContext) -> bool:
    """Phase 6: Adversarial review. Delegates to v1."""
    return phase_6_review(ctx)


def phase_6b_v2(ctx: ModuleContext) -> bool:
    """Phase 6b: Apply review fixes. Delegates to v1."""
    return phase_6b_apply_fixes(ctx)


def phase_7_final_audit_fix(ctx: ModuleContext) -> bool:
    """Phase 7: Final comprehensive audit+fix loop (max 2 iters)."""
    phase = "7-final"
    if is_phase_complete(ctx, phase):
        log("  Phase 7: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 7: DRY-RUN — would run final audit")
        return True

    for attempt in range(1, MAX_FINAL_FIX_ITERS + 1):
        log(f"  Phase 7: Final audit attempt {attempt}/{MAX_FINAL_FIX_ITERS}...")
        passed, output = run_verify(ctx.paths["md"], content_only=False)

        log_file = ctx.orch_dir / f"phase7-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            log(f"  Phase 7: PASS (attempt {attempt})")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        log(f"  Phase 7: FAIL (attempt {attempt})")
        if attempt >= MAX_FINAL_FIX_ITERS:
            log(f"  Phase 7: EXHAUSTED — {MAX_FINAL_FIX_ITERS} attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch comprehensive fix
        fix_prompt = _build_fix_prompt(ctx, output, content_only=False)
        fix_prompt_file = ctx.orch_dir / f"phase7-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 7: Dispatching final fix {attempt}...")
        fix_output = _gemini_output_path(ctx.slug, f"p7-fix{attempt}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p7fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 7: Fix dispatch {attempt} failed")
            continue

        if fix_output.exists():
            fix_text = fix_output.read_text(encoding="utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


def phase_8_mdx(ctx: ModuleContext) -> bool:
    """Phase 8: MDX generation + lint. Deterministic, no LLM."""
    phase = "8"
    if is_phase_complete(ctx, phase):
        log("  Phase 8: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 8: DRY-RUN — would generate MDX")
        return True

    log("  Phase 8: Generating MDX...")
    result = run_script([
        str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", ctx.track, str(ctx.module_num),
    ], capture=True)

    if result.returncode != 0:
        log(f"  Phase 8: WARNING — MDX generation returned {result.returncode}")

    mark_phase_locked(ctx, phase, "complete")
    return True


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

# Unified phase sequence — no mode branching
PHASE_SEQUENCE = [
    "0",    # Research
    "1",    # Meta/Outline
    "2",    # Write Prose
    "3",    # Prose Audit+Fix
    "4ab",  # Activities + Vocabulary (parallel)
    "5",    # Enrichment Audit+Fix
    "6",    # Adversarial Review
    "6b",   # Apply Review Fixes
    "7",    # Final Audit+Fix
    "8",    # MDX Generation
]

PHASE_FUNCTIONS_V2: dict[str, Any] = {
    "0":    phase_0_v2,
    "1":    phase_1_v2,
    "2":    phase_2_v2,
    "3":    phase_3_prose_audit_fix,
    "4ab":  _run_parallel_4ab,
    "5":    phase_5_enrichment_audit_fix,
    "6":    phase_6_v2,
    "6b":   phase_6b_v2,
    "7":    phase_7_final_audit_fix,
    "8":    phase_8_mdx,
}

PHASE_LABELS: dict[str, str] = {
    "0":    "Research",
    "1":    "Meta/Outline",
    "2":    "Write Prose",
    "3":    "Prose Audit+Fix",
    "4ab":  "Activities + Vocabulary (parallel)",
    "5":    "Enrichment Audit+Fix",
    "6":    "Adversarial Review",
    "6b":   "Apply Review Fixes",
    "7":    "Final Audit+Fix",
    "8":    "MDX Generation",
}


def run_pipeline_v2(ctx: ModuleContext) -> bool:
    """Execute the unified E2E pipeline."""
    is_archived = getattr(ctx, "is_archived", False)

    log(f"\nPipeline v2: E2E mode — {len(PHASE_SEQUENCE)} phases")
    if is_archived:
        log(f"  Archive: {getattr(ctx, 'archive_source', 'unknown')}")
    if ctx.dry_run:
        log("  (DRY-RUN — no Gemini dispatches)")
    log("")

    # Print phase plan
    for phase_id in PHASE_SEQUENCE:
        label = PHASE_LABELS.get(phase_id, phase_id)
        skip_note = ""

        # Show skip status for archived phases
        # Phase 0 always runs (plan+research = source of truth)
        if phase_id == "2" and is_archived:
            skip_note = " [CHECK: archive vs outline]"

        # Check existing state for done phases
        state_ids = _phase_state_ids(phase_id)
        if all(is_phase_complete(ctx, sid) for sid in state_ids):
            skip_note = " [DONE]"

        log(f"  Phase {phase_id}: {label}{skip_note}")

    log("")

    # Handle --force-phase
    force_phase = ctx.force_phase
    if force_phase:
        if force_phase not in PHASE_FUNCTIONS_V2:
            log(f"  ERROR: Unknown phase '{force_phase}'. Valid: {', '.join(PHASE_SEQUENCE)}")
            return False
        log(f"  --force-phase {force_phase}: running only this phase")
        func = PHASE_FUNCTIONS_V2[force_phase]
        return func(ctx)

    # Execute phases sequentially
    for phase_id in PHASE_SEQUENCE:
        func = PHASE_FUNCTIONS_V2.get(phase_id)
        if not func:
            log(f"  Unknown phase: {phase_id}")
            continue

        if not func(ctx):
            log(f"\n  PIPELINE STOPPED at phase {phase_id}")
            return False

    return True


def _phase_state_ids(phase_id: str) -> list[str]:
    """Map v2 phase IDs to state.json phase IDs (returns list for uniformity).

    v2 phase "4ab" maps to v1's "3a" + "3b" for backward compat.
    v2 phase "5" uses "5-enrich", "7" uses "7-final", "8" uses "8".
    All others match their v2 IDs.
    """
    if phase_id == "4ab":
        return ["3a", "3b"]
    if phase_id == "5":
        return ["5-enrich"]
    if phase_id == "7":
        return ["7-final"]
    return [phase_id]


# ---------------------------------------------------------------------------
# Preflight + Completion
# ---------------------------------------------------------------------------

def preflight_v2(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, detect archive. Returns ModuleContext."""
    # Use v1's preflight for base setup (it handles all path/config resolution)
    # Set mode flags so v1 gives us mode="full" as the base
    args.content_only = False
    args.enrich = False
    ctx = v1.preflight(args)

    # Override mode to "e2e"
    ctx.mode = "e2e"
    ctx.state["mode"] = "e2e"

    # Initialize thread-safe state lock
    _init_state_lock(ctx)

    # Archive detection — seminar tracks only (core tracks regenerate fresh)
    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    if is_seminar:
        is_archived, archive_source, archive_dir = detect_archived_prose(ctx.track, ctx.slug)
    else:
        is_archived, archive_source, archive_dir = False, "", None

    # Attach as extra attributes (ModuleContext is a dataclass, allows dynamic attrs)
    ctx.is_archived = is_archived  # type: ignore[attr-defined]
    ctx.archive_source = archive_source  # type: ignore[attr-defined]
    ctx.archive_dir = archive_dir  # type: ignore[attr-defined]

    if is_archived:
        log(f"Archive: DETECTED — {archive_source}")
    else:
        log("Archive: none found")

    return ctx


def write_completion_report_v2(ctx: ModuleContext, passed: bool) -> None:
    """Write completion report to orchestration dir."""
    content_path = ctx.paths["md"]
    word_count = 0
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())

    verdict = "PASS" if passed else "FAIL"
    is_archived = getattr(ctx, "is_archived", False)

    sections_info = ctx.state.get("phases", {}).get("2", {})
    sections_done = sections_info.get("sections_done", "?")
    sections_total = sections_info.get("sections_total", "?")

    report = textwrap.dedent(f"""\
        {verdict}: build_module_v2.py {ctx.track} {ctx.module_num} — E2E

          Module:   {ctx.slug}
          Track:    {ctx.track}
          Mode:     e2e
          Words:    {word_count} (target: {ctx.word_target})
          Sections: {sections_done}/{sections_total}
          Archive:  {'yes — ' + getattr(ctx, 'archive_source', '') if is_archived else 'no'}
          Verdict:  {verdict}
          Date:     {_now_iso()}
    """)

    completion_file = ctx.orch_dir / "completion.md"
    completion_file.write_text(report, encoding="utf-8")
    log(f"\nCompletion report → {completion_file}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="E2E Module Builder v2 — single unified pipeline with archive support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s a1 12                    # Full E2E pipeline (resume-aware)
              %(prog)s b2-hist 1                # E2E with archive restore
              %(prog)s a1 12 --rebuild          # Nuke state, rebuild from Phase 0
              %(prog)s a1 12 --force-phase 3    # Re-run specific phase only
              %(prog)s a1 12 --dry-run          # Show plan without dispatching
              %(prog)s a1 12 --verify           # Just run audit, print PASS/FAIL
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., c1-bio, b2-hist, lit, ...)")
    parser.add_argument("num", type=int, help="1-indexed module number within the track")

    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke state and rebuild from Phase 0")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a specific phase even if state says complete")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching to Gemini")
    parser.add_argument("--verify", action="store_true",
                        help="Just run audit, print PASS/FAIL, exit")

    args = parser.parse_args()

    # --verify mode: just run audit and exit
    if args.verify:
        try:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            content_path = paths["md"]

            if not content_path.exists():
                print(f"FAIL: Content file not found: {content_path}", flush=True)
                return 1

            passed, output = run_verify(content_path, content_only=False)
            if not passed:
                passed_co, output_co = run_verify(content_path, content_only=True)
                if passed_co:
                    print(f"CONTENT-COMPLETE: {slug} (activities still needed)", flush=True)
                    return 0
                else:
                    print(f"FAIL: {slug}", flush=True)
                    for line in output_co.strip().split("\n")[-20:]:
                        print(f"  {line}", flush=True)
                    return 1
            else:
                print(f"PASS: {slug} (fully complete)", flush=True)
                return 0
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            return 1

    # Main pipeline
    try:
        ctx = preflight_v2(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        ok = run_pipeline_v2(ctx)
        write_completion_report_v2(ctx, ok)

        if ok:
            if not ctx.dry_run:
                passed, output = run_verify(ctx.paths["md"], content_only=False)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} fully complete (e2e)")
                else:
                    log(f"\nVERDICT: FAIL — final verification failed")
                    for line in output.strip().split("\n")[-15:]:
                        log(f"  {line}")
                    return 1
            else:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in e2e mode")
            return 0
        else:
            log(f"\nPIPELINE FAILED — check logs in {ctx.orch_dir}")
            return 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", flush=True)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", flush=True)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", flush=True)
        return 130


if __name__ == "__main__":
    sys.exit(main())
