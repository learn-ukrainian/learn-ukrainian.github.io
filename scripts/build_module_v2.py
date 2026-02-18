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
    .venv/bin/python scripts/build_module_v2.py {track} --all               # Build entire track
    .venv/bin/python scripts/build_module_v2.py {track} --range 4-44        # Build range
    .venv/bin/python scripts/build_module_v2.py {track} {num} --rebuild     # Nuke state, restart
    .venv/bin/python scripts/build_module_v2.py {track} {num} --force-phase 3  # Re-run phase
    .venv/bin/python scripts/build_module_v2.py {track} {num} --dry-run     # Show plan
    .venv/bin/python scripts/build_module_v2.py {track} {num} --verify      # Just audit
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time

import yaml
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
    CURRICULUM_DIR, FLASH_MODEL, PHASES_DIR, PRO_MODEL, PROJECT_ROOT,
    SEMINAR_TRACKS, get_module_index, get_module_paths, get_track_config,
    slug_for_num,
)

# ---------------------------------------------------------------------------
# Thread-safe state via filelock
# ---------------------------------------------------------------------------
_HAS_FILELOCK = False
try:
    from filelock import FileLock
    _HAS_FILELOCK = True
except ImportError:
    import warnings
    warnings.warn(
        "filelock not installed — parallel 4a+4b will run sequentially. "
        "Install with: pip install filelock",
        stacklevel=1,
    )
    class FileLock:  # type: ignore[no-redef]
        def __init__(self, path: str | Path):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a: Any):
            pass

_state_lock: FileLock | None = None
_log_lock = threading.Lock()


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


# Monkey-patch v1's mark_phase so all delegated phase functions use locking.
# Guard: only patch if not already wrapped (prevents double-patch if this module
# is loaded twice — once as __main__ and once via deferred import).
_original_mark_phase = v1.mark_phase
if not getattr(v1.mark_phase, "_is_locked_wrapper", False):
    mark_phase_locked._is_locked_wrapper = True  # type: ignore[attr-defined]
    v1.mark_phase = mark_phase_locked  # type: ignore[assignment]

# Monkey-patch v1's log for thread-safe output during parallel 4a+4b
_original_log = v1.log


def _log_threadsafe(msg: str) -> None:
    # Remap v1 phase names to v2 display names
    msg = msg.replace("Phase 3a:", "Phase 4a:").replace("Phase 3b:", "Phase 4b:")
    with _log_lock:
        _original_log(msg)


v1.log = _log_threadsafe  # type: ignore[assignment]
log = _log_threadsafe  # Override our own import too


# Monkey-patch dispatch_gemini to always use stdout_only=True in v2 pipeline,
# with automatic flash→pro fallback when flash is rate-limited.
_original_dispatch_gemini = v1.dispatch_gemini

# Rate limit / auth failure signatures in Gemini CLI output
_RATE_LIMIT_PATTERNS = [
    "Error authenticating",
    "FatalAuthenti",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "quota exceeded",
    "429",
]


def _is_rate_limited(output: str) -> bool:
    """Check if dispatch failed due to rate limiting or auth exhaustion."""
    lower = output.lower()
    return any(p.lower() in lower for p in _RATE_LIMIT_PATTERNS)


def _dispatch_gemini_stdout_only(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    ok, output = _original_dispatch_gemini(
        prompt, task_id, model=model,
        stdout_only=True,  # Always stdout-only in v2
        allow_write=allow_write, output_file=output_file, timeout=timeout,
    )
    # Fallback: if flash failed due to rate limit, retry with pro
    if not ok and model == FLASH_MODEL and _is_rate_limited(output):
        log(f"  [fallback] Flash rate-limited, retrying with pro model...")
        ok, output = _original_dispatch_gemini(
            prompt, task_id, model=PRO_MODEL,
            stdout_only=True, allow_write=allow_write,
            output_file=output_file, timeout=timeout,
        )
        if ok:
            log(f"  [fallback] Pro model succeeded")
    return ok, output


v1.dispatch_gemini = _dispatch_gemini_stdout_only  # type: ignore[assignment]
dispatch_gemini = _dispatch_gemini_stdout_only  # Override our own import too


# ---------------------------------------------------------------------------
# Prose-only verification (ignores review + activity gates)
# ---------------------------------------------------------------------------
# Gates that are NOT prose-related — skip in Phase 3 prose audit
_NON_PROSE_GATES = {"review", "activities", "density", "unique_types", "priority",
                    "engagement", "activity_quality"}

# Pedagogy violation codes that are about activities, not prose.
# These leak through --skip-activities into the lesson gate as "pedagogy: N violations".
_ACTIVITY_PEDAGOGY_CODES = {
    "MISSING_ADVANCED_ACTIVITY",
    "MISSING_REQUIRED_ACTIVITY",
    "ACTIVITY_TYPE_MISMATCH",
}


def run_verify_prose_only(content_path: Path) -> tuple[bool, str]:
    """Run audit_module.sh --skip-activities and check only prose-relevant gates.

    Unlike otaman_verify.py which checks review + orchestration artifacts,
    this only looks at gates that Phase 3 can actually fix: words, structure,
    ipa, lint, pedagogy, naturalness, immersion, vocab, persona.

    Activity-related pedagogy violations (MISSING_ADVANCED_ACTIVITY etc.) are
    filtered out because Phase 3 cannot add activities — that's Phase 4's job.
    """
    import json as _json

    audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
    result = subprocess.run(
        [audit_script, "--skip-activities", str(content_path)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")

    # Read the status JSON written by the audit
    track_dir = content_path.parent
    slug = content_path.stem
    bare_slug = slug.split("-", 1)[1] if slug[0].isdigit() and "-" in slug else slug
    status_file = track_dir / "status" / f"{bare_slug}.json"

    if not status_file.exists():
        return False, output + "\nNo status JSON produced by audit"

    status = _json.loads(status_file.read_text(encoding="utf-8"))
    gates = status.get("gates", {})

    # Count how many pedagogy violations are actually about activities (not prose)
    activity_ped_count = 0
    for code in _ACTIVITY_PEDAGOGY_CODES:
        activity_ped_count += output.count(f"[{code}]")

    failing = []
    for gate_name, gate_data in gates.items():
        if gate_name in _NON_PROSE_GATES:
            continue
        if gate_data.get("status") == "fail":
            msg = gate_data.get("message", "")
            # If the lesson gate fails ONLY because of activity-related pedagogy
            # violations, skip it — Phase 3 cannot fix missing activities.
            if gate_name == "lesson" and "pedagogy" in msg:
                # Extract total pedagogy violation count from message
                # Format: "7927/6133 (raw: 8250) | pedagogy: 2 violations"
                ped_match = re.search(r"pedagogy:\s*(\d+)\s*violation", msg)
                if ped_match:
                    total_ped = int(ped_match.group(1))
                    if activity_ped_count >= total_ped:
                        # ALL pedagogy violations are activity-related — skip
                        continue
                    # Some are real prose issues — adjust the message
                    real_ped = total_ped - activity_ped_count
                    msg = re.sub(r"pedagogy:\s*\d+\s*violations?",
                                 f"pedagogy: {real_ped} violations", msg)
            failing.append(f"{gate_name}: {msg}")

    if failing:
        return False, output + "\nProse-relevant failures:\n" + "\n".join(f"  {f}" for f in failing)
    return True, output


# ---------------------------------------------------------------------------
# Archive Detection + Restoration
# ---------------------------------------------------------------------------
ARCHIVE_DIR = PROJECT_ROOT / "_archive"
ARCHIVE_WORD_THRESHOLD = 2000
# Git ref for pre-rebuild content. Points to parent of 944f3524a (the clean-slate
# rebuild commit). This commit is permanent in history — won't be GC'd.
# Override via ARCHIVE_GIT_REF env var if repo history changes.
ARCHIVE_GIT_REF = os.environ.get("ARCHIVE_GIT_REF", "944f3524a^")

# Tracks whose archived content is known to be low-quality and should NOT be
# restored. Research will be regenerated from scratch via Phase 0 instead.
# Add/remove tracks here as quality improves.
ARCHIVE_SKIP_TRACKS: set[str] = {"c1-bio", "c1-hist", "lit"}


def detect_archived_prose(track: str, slug: str) -> tuple[bool, str, Path | None]:
    """Check for restorable archived prose.

    Search order:
      1. _archive/{track}/{latest_timestamp}/{slug}.md  (filesystem)
      2. git show 944f3524a^:curriculum/l2-uk-en/{track}/{slug}.md  (git history)

    Returns (is_archived, source_description, archive_dir_or_None).
    For git-based archives, archive_dir is None (content extracted on demand).
    """
    if track in ARCHIVE_SKIP_TRACKS:
        return False, "", None

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
    # Only use git fallback if no filesystem archive dir exists for this track.
    # If the dir exists but the file is missing, that means it was intentionally
    # deleted (e.g. for redo) — don't resurrect from git.
    if not track_archive.is_dir():
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
MAX_PROSE_FIX_ITERS = 5       # Prose is hardest — more room for convergence
MAX_ENRICHMENT_FIX_ITERS = 3  # Activities/vocab are more mechanical
MAX_FINAL_FIX_ITERS = 3       # Final comprehensive — one extra for edge cases


def _with_flash(ctx: ModuleContext, fn):
    """Run a phase function with flash model, restoring original model after."""
    original = ctx.track_config.get("model", PRO_MODEL)
    ctx.track_config["model"] = FLASH_MODEL
    try:
        return fn(ctx)
    finally:
        ctx.track_config["model"] = original


def phase_0_v2(ctx: ModuleContext) -> bool:
    """Phase 0: Research. Skips if research file already exists, else uses flash."""
    force = getattr(ctx, "force_research", False)
    research_path = ctx.paths.get("research")
    if not force and research_path and research_path.exists() and research_path.stat().st_size > 200:
        if not is_phase_complete(ctx, "0"):
            mark_phase_locked(ctx, "0", "complete", note="adopted-existing-research")
        log(f"  Phase 0: ADOPT — existing research ({research_path.stat().st_size:,} bytes)")
        return True
    if force:
        log("  Phase 0: --force-research — regenerating research")
        # Clear state so v1's phase_0_research doesn't skip
        state = ctx.state.get("phases", {})
        if "0" in state:
            del state["0"]
            save_state(ctx)
    return _with_flash(ctx, phase_0_research)


def phase_1_v2(ctx: ModuleContext) -> bool:
    """Phase 1: Meta/Outline. Uses flash (structured YAML template)."""
    return _with_flash(ctx, phase_1_meta)


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
    # --refresh resets phase 2+ so downstream phases re-run with new prose
    if getattr(ctx, "refresh", False) and is_phase_complete(ctx, phase):
        state_phases = ctx.state.get("phases", {})
        # Clear phase 2 and all downstream phases (3, 4a, 4b, 5, 6, 6b, 7, 8)
        downstream = [k for k in state_phases if k >= "2"]
        for k in downstream:
            del state_phases[k]
        save_state(ctx)
        log(f"  Phase 2: RESET (--refresh flag, cleared {len(downstream)} phases)")
    elif is_phase_complete(ctx, phase):
        log("  Phase 2: SKIP (already complete)")
        return True

    # Adoption check: if file exists and is substantial, skip generation
    content_path = ctx.paths["md"]
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
        if word_count >= ctx.word_target * 0.8:
            # Check research-content alignment (mtime-independent)
            refresh_needed = False
            research_path = ctx.paths.get("research")
            if research_path and research_path.exists():
                try:
                    from research_quality import assess_research_compat
                    info = assess_research_compat(research_path, ctx.track, content_path)
                    if info and info.get("content_alignment", {}).get("refresh_recommended"):
                        refresh_needed = True
                        reasons = info["content_alignment"].get("reasons", [])
                        log(f"  Phase 2: Research-content misalignment detected")
                        for r in reasons:
                            log(f"    - {r}")
                except ImportError:
                    pass

            if refresh_needed and getattr(ctx, "refresh", False):
                log(f"  Phase 2: --refresh flag set — regenerating prose from research")
                # Fall through to generation
            elif refresh_needed:
                log(f"  Phase 2: ADOPT (use --refresh to regenerate from updated research)")
                mark_phase_locked(ctx, phase, "complete", note="adopted-stale-prose", words=word_count)
                return True
            else:
                log(f"  Phase 2: ADOPT — existing prose found ({word_count}w, target {ctx.word_target}w)")
                mark_phase_locked(ctx, phase, "complete", note="adopted-existing-prose", words=word_count)
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

    # In dry-run, content_outline may not exist yet (Phase 1 creates it)
    if ctx.dry_run and not ctx.content_outline:
        log("  Phase 2: DRY-RUN — would generate prose (outline depends on Phase 1)")
        return True

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
        if attempt == 1:
            log("  Phase 3: Initial prose audit...")
        else:
            log(f"  Phase 3: Audit after fix {attempt - 1}/{MAX_PROSE_FIX_ITERS - 1}...")
        passed, output = run_verify_prose_only(ctx.paths["md"])

        log_file = ctx.orch_dir / f"phase3-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            fixes = attempt - 1
            log(f"  Phase 3: PASS{f' (after {fixes} fix(es))' if fixes else ''}")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        if attempt == 1:
            log("  Phase 3: FAIL — needs fixes")
        else:
            log(f"  Phase 3: FAIL (fix {attempt - 1} insufficient)")
        if attempt >= MAX_PROSE_FIX_ITERS:
            log(f"  Phase 3: EXHAUSTED — {MAX_PROSE_FIX_ITERS - 1} fix attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch fix to Gemini
        fix_num = attempt  # fix 1 happens after audit 1 fails
        fix_prompt = _build_fix_prompt(ctx, output, content_only=True)
        fix_prompt_file = ctx.orch_dir / f"phase3-fix{fix_num}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 3: Dispatching prose fix {fix_num}/{MAX_PROSE_FIX_ITERS - 1}...")
        fix_output = _gemini_output_path(ctx.slug, f"p3-fix{fix_num}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p3fix{fix_num}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 3: Fix dispatch {fix_num} failed")
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


def _validate_activities_yaml(path: Path) -> bool:
    """Check if an activities YAML file passes schema validation."""
    try:
        from audit.checks.yaml_schema_validation import validate_activity_yaml_file
        valid, errors = validate_activity_yaml_file(path)
        if not valid:
            for e in errors[:3]:
                log(f"    Schema error: {e[:120]}")
        return valid
    except Exception as e:
        log(f"    Schema validation error: {e}")
        return False  # If we can't validate, don't adopt


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

    Falls back to sequential in dry-run mode or when filelock is missing.
    """
    if ctx.dry_run or not _HAS_FILELOCK:
        if not _HAS_FILELOCK and not ctx.dry_run:
            log("  Phase 4a+4b: Running sequentially (filelock not installed)")
        if not phase_4a_activities(ctx):
            return False
        return phase_4b_vocabulary(ctx)

    # Check if both already complete
    if is_phase_complete(ctx, "3a") and is_phase_complete(ctx, "3b"):
        log("  Phase 4a+4b: SKIP (both already complete)")
        return True

    # Adoption check: if both files exist AND are valid, skip generation
    act_path = ctx.paths["activities"]
    voc_path = ctx.paths["vocabulary"]
    if act_path.exists() and voc_path.exists():
        act_valid = _validate_activities_yaml(act_path)
        if act_valid:
            log("  Phase 4a+4b: ADOPT — existing activities/vocab found and valid")
            mark_phase_locked(ctx, "3a", "complete", note="adopted-existing")
            mark_phase_locked(ctx, "3b", "complete", note="adopted-existing")
            return True
        else:
            log("  Phase 4a+4b: Existing activities invalid — deleting and regenerating")
            act_path.unlink(missing_ok=True)

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
        if attempt == 1:
            log("  Phase 5: Initial enrichment audit...")
        else:
            log(f"  Phase 5: Audit after fix {attempt - 1}/{MAX_ENRICHMENT_FIX_ITERS - 1}...")
        passed, output = run_verify(ctx.paths["md"], content_only=False)

        log_file = ctx.orch_dir / f"phase5-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            fixes = attempt - 1
            log(f"  Phase 5: PASS{f' (after {fixes} fix(es))' if fixes else ''}")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        if attempt == 1:
            log("  Phase 5: FAIL — needs fixes")
        else:
            log(f"  Phase 5: FAIL (fix {attempt - 1} insufficient)")
        if attempt >= MAX_ENRICHMENT_FIX_ITERS:
            log(f"  Phase 5: EXHAUSTED — {MAX_ENRICHMENT_FIX_ITERS - 1} fix attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch enrichment fix
        fix_num = attempt
        fix_prompt = _build_fix_prompt(ctx, output, content_only=False)
        fix_prompt_file = ctx.orch_dir / f"phase5-fix{fix_num}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 5: Dispatching enrichment fix {fix_num}/{MAX_ENRICHMENT_FIX_ITERS - 1}...")
        fix_output = _gemini_output_path(ctx.slug, f"p5-fix{fix_num}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p5fix{fix_num}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 5: Fix dispatch {fix_num} failed")
            continue

        if fix_output.exists():
            fix_text = fix_output.read_text(encoding="utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


def phase_6_claude_review(ctx: ModuleContext) -> bool:
    """Phase 6: Adversarial review via Claude API (cross-agent review)."""
    phase = "6"
    if is_phase_complete(ctx, phase):
        log("  Phase 6 (Claude): SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 6 (Claude): DRY-RUN — would call Claude API for review")
        return True

    ok, review_text = v1.dispatch_claude_review(ctx)
    if not ok or not review_text:
        log("  Phase 6 (Claude): FAILED — falling back to Gemini review")
        return phase_6_review(ctx)

    # Save review to canonical path
    ctx.paths["review"].parent.mkdir(parents=True, exist_ok=True)
    ctx.paths["review"].write_text(review_text, encoding="utf-8")

    # Also save to orchestration dir
    extracted = ctx.orch_dir / "phase-6-review.md"
    extracted.write_text(review_text, encoding="utf-8")

    log(f"  Phase 6 (Claude): Review saved → {ctx.paths['review'].name}")
    mark_phase_locked(ctx, phase, "complete", task_id=f"cr-{ctx.slug}")
    return True


def phase_6_v2(ctx: ModuleContext) -> bool:
    """Phase 6: Adversarial review. Routes to Claude API or Gemini based on flag."""
    if getattr(ctx, "claude_review", False):
        return phase_6_claude_review(ctx)
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
        if attempt == 1:
            log("  Phase 7: Initial final audit...")
        else:
            log(f"  Phase 7: Audit after fix {attempt - 1}/{MAX_FINAL_FIX_ITERS - 1}...")
        passed, output = run_verify(ctx.paths["md"], content_only=False)

        log_file = ctx.orch_dir / f"phase7-audit-attempt-{attempt}.log"
        log_file.write_text(output, encoding="utf-8")

        if passed:
            fixes = attempt - 1
            log(f"  Phase 7: PASS{f' (after {fixes} fix(es))' if fixes else ''}")
            mark_phase_locked(ctx, phase, "complete", attempts=attempt)
            return True

        if attempt == 1:
            log("  Phase 7: FAIL — needs fixes")
        else:
            log(f"  Phase 7: FAIL (fix {attempt - 1} insufficient)")
        if attempt >= MAX_FINAL_FIX_ITERS:
            log(f"  Phase 7: EXHAUSTED — {MAX_FINAL_FIX_ITERS - 1} fix attempts")
            mark_phase_locked(ctx, phase, "failed", attempts=attempt)
            return False

        # Dispatch comprehensive fix
        fix_num = attempt
        fix_prompt = _build_fix_prompt(ctx, output, content_only=False)
        fix_prompt_file = ctx.orch_dir / f"phase7-fix{fix_num}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, encoding="utf-8")

        log(f"  Phase 7: Dispatching final fix {fix_num}/{MAX_FINAL_FIX_ITERS - 1}...")
        fix_output = _gemini_output_path(ctx.slug, f"p7-fix{fix_num}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"yw-{ctx.slug}-p7fix{fix_num}",
            model=ctx.model, allow_write=True, output_file=fix_output,
        )
        if not ok:
            log(f"  Phase 7: Fix dispatch {fix_num} failed")
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
# Phase 9: Claude Final Review (QA gate — runs when --final-review is set)
# ---------------------------------------------------------------------------

def phase_9_final_review(ctx: ModuleContext) -> bool:
    """Phase 9: Final adversarial QA gate via Claude API.

    Only runs when ctx.final_review is True (--final-review flag).
    Reads all module files, calls Claude Opus for semantic review + fixes,
    applies fixes, regenerates MDX, re-audits, saves final review report.
    Returns False only if verdict is REJECT and audit still fails.
    """
    if not getattr(ctx, "final_review", False):
        return True  # Flag not set — silently skip

    phase = "9-final-review"
    if is_phase_complete(ctx, phase):
        log("  Phase 9: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase 9: DRY-RUN — would call Claude API for final review")
        return True

    ok, verdict, report = v1.dispatch_claude_final_review(ctx)
    if not ok:
        log("  Phase 9: FAILED — Claude API unavailable")
        return False  # Hard fail: can't review without Claude

    # Save final review report
    final_review_path = ctx.paths["review"].parent / f"{ctx.slug}-final-review.md"
    final_review_path.parent.mkdir(parents=True, exist_ok=True)
    final_review_path.write_text(report, encoding="utf-8")
    log(f"  Phase 9: Report saved → {final_review_path.name}")

    # Save to orchestration dir too
    orch_report = ctx.orch_dir / "phase-9-final-review.md"
    orch_report.write_text(report, encoding="utf-8")

    # If fixes were applied, regenerate MDX
    if "===FIX_START===" in report:
        log("  Phase 9: Regenerating MDX after fixes...")
        run_script([
            str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", ctx.track, str(ctx.module_num),
        ], capture=True)

        # Re-audit after fixes
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
        audit_log = ctx.orch_dir / "phase9-post-fix-audit.log"
        audit_log.write_text(audit_out, encoding="utf-8")

        if not passed:
            log(f"  Phase 9: Post-fix audit FAILED (verdict: {verdict})")
            if verdict == "REJECT":
                return False
            log("  Phase 9: Audit failed but verdict is not REJECT — marking NEEDS_WORK")
        else:
            log(f"  Phase 9: Post-fix audit PASS")

    if verdict == "REJECT":
        log("  Phase 9: REJECT — module needs rebuild")
        mark_phase_locked(ctx, phase, "failed", verdict=verdict)
        return False

    mark_phase_locked(ctx, phase, "complete", verdict=verdict)
    return True


# ---------------------------------------------------------------------------
# Phase 0.5: Plan Enrichment from Research
# ---------------------------------------------------------------------------

def _merge_enrichment_into_plan(plan: dict, enrichment: dict) -> dict:
    """Deterministic merge: replace section points + extend vocabulary_hints.

    Only touches content_outline.points and vocabulary_hints — all other
    plan fields are preserved untouched.
    """
    # Build lookup: section name -> enriched points
    enriched_sections = {}
    for section in enrichment.get("content_outline", []):
        name = section.get("section", "")
        if name:
            enriched_sections[name] = section.get("points", [])

    # Replace points in matching sections
    for section in plan.get("content_outline", []):
        name = section.get("section", "")
        if name in enriched_sections:
            section["points"] = enriched_sections[name]

    # Merge vocabulary_hints (add collocations, don't remove words)
    enriched_vocab = enrichment.get("vocabulary_hints")
    if enriched_vocab and isinstance(enriched_vocab, dict):
        plan_vocab = plan.setdefault("vocabulary_hints", {})
        for category in ("required", "recommended"):
            if category in enriched_vocab and enriched_vocab[category]:
                plan_vocab[category] = enriched_vocab[category]

    return plan


def phase_0_5_enrich_plan(ctx: ModuleContext) -> bool:
    """Phase 0.5: Enrich plan with research findings.

    Reads research + plan, dispatches to Gemini, merges enriched
    content_outline and vocabulary_hints back into the plan file.
    """
    phase = "0.5"
    if is_phase_complete(ctx, phase):
        log("  Phase 0.5: SKIP (already complete)")
        return True

    # Skip if research doesn't exist (Phase 0 must complete first)
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        log("  Phase 0.5: SKIP — no research file (Phase 0 must run first)")
        return True

    # Quality gate: research must score 9+/10 to avoid enriching from thin research
    MIN_RESEARCH_SCORE = 9
    try:
        from research_quality import assess_research_compat
        info = assess_research_compat(research_path, ctx.track)
        if info and info.get("score") is not None:
            score = info["score"]
            if score < MIN_RESEARCH_SCORE:
                log(f"  Phase 0.5: SKIP — research quality {score}/10 < {MIN_RESEARCH_SCORE} threshold")
                return True
            log(f"  Phase 0.5: Research quality {score}/10 — proceeding")
    except ImportError:
        log("  Phase 0.5: WARNING — research_quality not available, skipping quality gate")

    plan_path = ctx.paths.get("plan")
    if not plan_path or not plan_path.exists():
        log("  Phase 0.5: SKIP — no plan file")
        return True

    # Check if plan already has enrichment markers (idempotency)
    plan_text = plan_path.read_text(encoding="utf-8")
    plan = yaml.safe_load(plan_text) or {}
    has_enrichment = any(
        "—" in str(p) or "learner error:" in str(p) or "cultural hook:" in str(p)
        for section in plan.get("content_outline", [])
        for p in section.get("points", [])
    )
    if has_enrichment and not ctx.force_phase:
        log("  Phase 0.5: SKIP — plan already appears enriched")
        mark_phase_locked(ctx, phase, "complete", note="already-enriched")
        return True

    # Fill template
    template = PHASES_DIR / "phase-0-5-enrich-plan.md"
    if not template.exists():
        log(f"  Phase 0.5: SKIP — template not found: {template}")
        return True

    prompt_file = ctx.orch_dir / "phase-0-5-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log("  Phase 0.5: DRY-RUN — would dispatch plan enrichment")
        return True

    # Dispatch to Gemini
    log("  Phase 0.5: Dispatching plan enrichment...")
    output_file = _gemini_output_path(ctx.slug, "0.5")
    ok, raw_output = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"yw-{ctx.slug}-p0.5",
        model=ctx.model,
        stdout_only=True, output_file=output_file,
    )
    if not ok:
        log("  Phase 0.5: FAILED — Gemini dispatch error")
        return False

    # Extract enrichment from delimiters
    enrichment_text = ""
    if "===ENRICHMENT_START===" in raw_output and "===ENRICHMENT_END===" in raw_output:
        start = raw_output.index("===ENRICHMENT_START===") + len("===ENRICHMENT_START===")
        end = raw_output.index("===ENRICHMENT_END===")
        enrichment_text = raw_output[start:end].strip()
    else:
        log("  Phase 0.5: FAILED — no ENRICHMENT delimiters in output")
        return False

    # Parse enrichment YAML
    try:
        enrichment = yaml.safe_load(enrichment_text) or {}
    except yaml.YAMLError as e:
        log(f"  Phase 0.5: FAILED — YAML parse error: {e}")
        # Save raw output for debugging
        (ctx.orch_dir / "phase-0-5-enrichment-raw.md").write_text(
            enrichment_text, encoding="utf-8"
        )
        return False

    if not enrichment.get("content_outline"):
        log("  Phase 0.5: FAILED — no content_outline in enrichment")
        return False

    # Backup original plan
    backup_path = ctx.orch_dir / "phase-0-5-original-plan.yaml"
    backup_path.write_text(plan_text, encoding="utf-8")

    # Save enrichment artifact
    enrichment_artifact = ctx.orch_dir / "phase-0-5-enrichment.yaml"
    enrichment_artifact.write_text(
        yaml.dump(enrichment, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )

    # Merge enrichment into plan
    enriched_plan = _merge_enrichment_into_plan(plan, enrichment)

    # Validate: no word_target or words fields added
    for forbidden_key in ("words", "word_target", "word_count"):
        enriched_plan.pop(forbidden_key, None)

    # Write enriched plan back
    plan_path.write_text(
        yaml.dump(enriched_plan, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    # Count enriched points
    total_points = sum(
        len(s.get("points", []))
        for s in enriched_plan.get("content_outline", [])
    )
    log(f"  Phase 0.5: Plan enriched ({total_points} points across {len(enriched_plan.get('content_outline', []))} sections)")

    mark_phase_locked(ctx, phase, "complete", task_id=f"yw-{ctx.slug}-p0.5")
    return True


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

# PHASE_SEQUENCE is defined in v1 (build_module.py) to avoid double-import deadlock.
# When build_module_v2.py runs as __main__ and v1's clean_phase_artifacts imports from
# it, Python loads a second module copy that re-executes monkey-patching, creating a
# mark_phase_locked₂ → mark_phase_locked₁ chain = two FileLock objects on the same
# file = flock deadlock on macOS. Keeping the list in v1 eliminates the import.
PHASE_SEQUENCE = v1.PHASE_SEQUENCE

PHASE_FUNCTIONS_V2: dict[str, Any] = {
    "0":    phase_0_v2,
    "0.5":  phase_0_5_enrich_plan,
    "1":    phase_1_v2,
    "2":    phase_2_v2,
    "3":    phase_3_prose_audit_fix,
    "4ab":  _run_parallel_4ab,
    "5":    phase_5_enrichment_audit_fix,
    "6":    phase_6_v2,
    "6b":   phase_6b_v2,
    "7":    phase_7_final_audit_fix,
    "8":    phase_8_mdx,
    "9":    phase_9_final_review,
}

PHASE_LABELS: dict[str, str] = {
    "0":    "Research",
    "0.5":  "Plan Enrichment",
    "1":    "Meta/Outline",
    "2":    "Write Prose",
    "3":    "Prose Audit+Fix",
    "4ab":  "Activities + Vocabulary (parallel)",
    "5":    "Enrichment Audit+Fix",
    "6":    "Adversarial Review",
    "6b":   "Apply Review Fixes",
    "7":    "Final Audit+Fix",
    "8":    "MDX Generation",
    "9":    "Claude Final Review (QA Gate)",
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

    # Handle --force-phase (single phase only)
    force_phase = ctx.force_phase
    if force_phase:
        if force_phase not in PHASE_FUNCTIONS_V2:
            log(f"  ERROR: Unknown phase '{force_phase}'. Valid: {', '.join(PHASE_SEQUENCE)}")
            return False
        log(f"  --force-phase {force_phase}: running only this phase")
        func = PHASE_FUNCTIONS_V2[force_phase]
        return func(ctx)

    # Handle --restart-from (run from that phase through the end)
    restart_from = getattr(ctx, "restart_from", None)
    if restart_from:
        if restart_from not in PHASE_FUNCTIONS_V2:
            log(f"  ERROR: Unknown phase '{restart_from}'. Valid: {', '.join(PHASE_SEQUENCE)}")
            return False
        try:
            start_idx = PHASE_SEQUENCE.index(restart_from)
        except ValueError:
            log(f"  ERROR: Phase '{restart_from}' not in sequence")
            return False
        remaining = PHASE_SEQUENCE[start_idx:]
        log(f"  --restart-from {restart_from}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            func = PHASE_FUNCTIONS_V2.get(phase_id)
            if not func:
                log(f"  Unknown phase: {phase_id}")
                continue
            if not func(ctx):
                log(f"\n  PIPELINE STOPPED at phase {phase_id}")
                return False
        return True

    # Execute phases sequentially (full pipeline)
    for phase_id in PHASE_SEQUENCE:
        func = PHASE_FUNCTIONS_V2.get(phase_id)
        if not func:
            log(f"  Unknown phase: {phase_id}")
            continue

        if not func(ctx):
            log(f"\n  PIPELINE STOPPED at phase {phase_id}")
            return False

    # Phase 9: Claude Final Review (optional — runs when --final-review is set)
    if getattr(ctx, "final_review", False):
        log(f"\n  Phase 9: {PHASE_LABELS['9']}")
        if not phase_9_final_review(ctx):
            log("\n  PIPELINE STOPPED at phase 9 (REJECT verdict)")
            return False

    return True


# _phase_state_ids is defined in v1 (build_module.py) — same double-import reason.
_phase_state_ids = v1._phase_state_ids


# ---------------------------------------------------------------------------
# Preflight + Completion
# ---------------------------------------------------------------------------

def _bootstrap_meta_from_plan(track: str, slug: str) -> None:
    """Create a minimal meta file from plan if meta doesn't exist.

    Phase 1 will regenerate a proper meta later. This just gets us past
    v1's preflight which requires meta to exist.
    """
    paths = get_module_paths(track, slug)
    meta_path = paths["meta"]
    plan_path = paths["plan"]

    if meta_path.exists():
        return
    if not plan_path.exists():
        return  # No plan = nothing to bootstrap from, will fail later

    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    # Word target: plan overrides config, config is fallback
    wt = plan.get("word_target", 0)
    if not wt:
        try:
            from audit.config import get_word_target as _get_wt
            from build_module import track_to_level_focus
            level_code, module_focus = track_to_level_focus(track)
            mod_num = int(slug.split("-")[-1]) if slug[0].isdigit() else 1
            wt = _get_wt(level_code, mod_num, module_focus)
        except Exception:
            wt = 0
    minimal_meta = {
        "slug": slug,
        "title": plan.get("title", slug.replace("-", " ").title()),
        "word_target": wt,
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(yaml.dump(minimal_meta, allow_unicode=True), encoding="utf-8")


def preflight_v2(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, detect archive. Returns ModuleContext."""
    # Bootstrap minimal meta from plan if missing (Phase 1 regenerates it properly)
    track, num = args.track, args.num
    slug = slug_for_num(track, num)
    _bootstrap_meta_from_plan(track, slug)

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
    ctx.force_research = getattr(args, "force_research", False)  # type: ignore[attr-defined]
    ctx.refresh = getattr(args, "refresh", False)  # type: ignore[attr-defined]
    ctx.restart_from = getattr(args, "restart_from", None)  # type: ignore[attr-defined]
    ctx.claude_review = getattr(args, "claude_review", False)  # type: ignore[attr-defined]
    ctx.final_review = getattr(args, "final_review", False)  # type: ignore[attr-defined]

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
              %(prog)s a1 12                         # Full E2E pipeline (resume-aware)
              %(prog)s a1 --all                      # Build entire track sequentially
              %(prog)s a1 --range 4-44               # Build modules 4 through 44
              %(prog)s b2-hist 1                     # E2E with archive restore
              %(prog)s a1 12 --rebuild               # Nuke state, rebuild from Phase 0
              %(prog)s a1 12 --force-phase 3         # Re-run specific phase only
              %(prog)s a1 12 --dry-run               # Show plan without dispatching
              %(prog)s a1 12 --verify                # Just run audit, print PASS/FAIL
              %(prog)s a1 12 --claude-review         # Use Claude API for Phase 6 review
              %(prog)s a1 --all --claude-review      # Build all, Claude reviews each
              %(prog)s a1 12 --final-review          # Full pipeline + Phase 9 Claude QA gate
              %(prog)s a1 12 --claude-review --final-review  # Claude Phase 6 + Phase 9
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., c1-bio, b2-hist, lit, ...)")
    parser.add_argument("num", type=int, nargs="?", default=None,
                        help="1-indexed module number (optional with --all or --range)")

    parser.add_argument("--all", action="store_true", dest="build_all",
                        help="Build all modules in the track sequentially")
    parser.add_argument("--range", type=str, default=None, dest="build_range",
                        help="Build a range of modules (e.g. 4-44, 1-10)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke state and rebuild from Phase 0")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a single phase (cleans that phase's artifacts only)")
    parser.add_argument("--restart-from", type=str, default=None,
                        help="Restart from a phase: cleans that phase + all subsequent, then runs pipeline from there")
    parser.add_argument("--force-research", action="store_true",
                        help="Force fresh Phase 0 research even if research file exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching to Gemini")
    parser.add_argument("--refresh", action="store_true",
                        help="Regenerate prose from updated research (instead of adopting stale content)")
    parser.add_argument("--verify", action="store_true",
                        help="Just run audit, print PASS/FAIL, exit")
    parser.add_argument("--claude-review", action="store_true", dest="claude_review",
                        help="Use Claude API for Phase 6 adversarial review instead of Gemini (cross-agent, no self-review bias)")
    parser.add_argument("--final-review", action="store_true", dest="final_review",
                        help="Run Phase 9: Claude final QA gate after pipeline completes (semantic review + fixes + APPROVE/REJECT verdict)")

    args = parser.parse_args()

    # Validate: need num, --all, or --range
    if args.num is None and not args.build_all and not args.build_range:
        parser.error("Either provide a module number, --all, or --range")

    # --all / --range: resolve module numbers and run sequentially
    if args.build_all or args.build_range:
        idx = get_module_index(args.track)
        total = idx["total"]

        if args.build_all:
            nums = list(range(1, total + 1))
            print(f"Building ALL {total} modules in {args.track}", flush=True)
        else:
            # Parse range like "4-44"
            match = re.match(r"^(\d+)-(\d+)$", args.build_range)
            if not match:
                parser.error(f"Invalid range format: {args.build_range!r} (expected N-M, e.g. 4-44)")
            start, end = int(match.group(1)), int(match.group(2))
            if start < 1 or end > total or start > end:
                parser.error(f"Range {start}-{end} out of bounds (track has {total} modules)")
            nums = list(range(start, end + 1))
            print(f"Building {args.track} modules {start}-{end} ({len(nums)} modules)", flush=True)

        passed_list, failed_list, skipped_list = [], [], []
        t0_batch = time.time()

        for i, n in enumerate(nums, 1):
            slug = slug_for_num(args.track, n)
            print(f"\n{'='*70}", flush=True)
            print(f"[{i}/{len(nums)}] {args.track} #{n} — {slug}", flush=True)
            print(f"{'='*70}", flush=True)

            # Skip already-complete modules (unless --rebuild)
            if not args.rebuild and not args.force_phase:
                try:
                    paths = get_module_paths(args.track, slug)
                    if paths["md"].exists():
                        check_passed, _ = run_verify(paths["md"], content_only=False)
                        if check_passed:
                            print(f"  SKIP: already passing audit", flush=True)
                            skipped_list.append((n, slug))
                            continue
                except Exception:
                    pass  # proceed with build

            # Build single module by re-invoking main logic
            single_args = argparse.Namespace(
                track=args.track, num=n,
                build_all=False, build_range=None,
                rebuild=args.rebuild, force_phase=args.force_phase,
                restart_from=args.restart_from,
                force_research=args.force_research, dry_run=args.dry_run,
                refresh=args.refresh, verify=False,
                claude_review=getattr(args, "claude_review", False),
                final_review=getattr(args, "final_review", False),
            )
            rc = _run_single_module(single_args)
            if rc == 0:
                passed_list.append((n, slug))
            else:
                failed_list.append((n, slug))
                print(f"  FAILED — continuing to next module", flush=True)

        # Summary
        elapsed_batch = time.time() - t0_batch
        elapsed_str = f"{int(elapsed_batch // 60)}m {int(elapsed_batch % 60)}s"
        print(f"\n{'='*70}", flush=True)
        print(f"BATCH COMPLETE — {args.track} [{elapsed_str}]", flush=True)
        print(f"  Passed:  {len(passed_list)}", flush=True)
        print(f"  Failed:  {len(failed_list)}", flush=True)
        print(f"  Skipped: {len(skipped_list)} (already passing)", flush=True)
        if failed_list:
            print(f"  Failed modules:", flush=True)
            for n, slug in failed_list:
                print(f"    #{n} {slug}", flush=True)
        print(f"{'='*70}", flush=True)
        return 1 if failed_list else 0

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

    # Main pipeline (single module)
    return _run_single_module(args)


def _run_single_module(args: argparse.Namespace) -> int:
    """Run the E2E pipeline for a single module. Returns 0 on success, 1 on failure."""
    try:
        ctx = preflight_v2(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        t0 = time.time()
        ok = run_pipeline_v2(ctx)
        elapsed = time.time() - t0
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        write_completion_report_v2(ctx, ok)

        if ok:
            if ctx.dry_run:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in e2e mode [{elapsed_str}]")
            elif ctx.force_phase:
                log(f"\nVERDICT: PASS — phase {ctx.force_phase} complete [{elapsed_str}]")
            else:
                passed, output = run_verify(ctx.paths["md"], content_only=False)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} fully complete (e2e) [{elapsed_str}]")
                else:
                    log(f"\nVERDICT: FAIL — final verification failed [{elapsed_str}]")
                    for line in output.strip().split("\n")[-15:]:
                        log(f"  {line}")
                    return 1
            return 0
        else:
            log(f"\nPIPELINE FAILED — check logs in {ctx.orch_dir} [{elapsed_str}]")
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
