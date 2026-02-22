#!/usr/bin/env python3
"""Deterministic E2E Module Builder v3 — Optimised 4-Call Pipeline.

v3 collapses multiple v2 phases into optimised calls, reducing round-trips
from 8-9 calls to 4 baseline (worst case 8 with fix iterations).

Cross-agent pipeline: Gemini builds (A/B/C), Claude reviews (D).
This prevents self-review gaming detected by anti-gaming audit checks.

Pipeline:
    Phase A:  Research + Meta         (1 Gemini call) ← v2 phases 0, 0.5, 1
    Phase B:  Content                 (1 Gemini call) ← v2 phase 2 + track context
    Phase C:  Activities + Vocab      (1 Gemini call) ← v2 phases 4a+4b + track context
    Audit:    Prose+Enrichment audit  (0-3 Gemini fix calls)
    Phase D:  Review + Fix            (1-2 Claude calls) ← cross-agent review
    Phase F:  Final Review            (opt., agent-selectable) ← v2 phase 9
    Phase E:  MDX                     (0 LLM calls) ← ALWAYS LAST

Baseline: 3 Gemini + 1 Claude. Worst case: 3G + 3G audit + 2C Phase D = 8.
Typical: 4-6 calls. v2: 8-9+.

Usage:
    .venv/bin/python scripts/build_module_v3.py a1 12
    .venv/bin/python scripts/build_module_v3.py b2-hist 5
    .venv/bin/python scripts/build_module_v3.py a1 --all
    .venv/bin/python scripts/build_module_v3.py a1 --range 1-20
    .venv/bin/python scripts/build_module_v3.py b2-hist --all --research-only
    .venv/bin/python scripts/build_module_v3.py a1 12 --rebuild
    .venv/bin/python scripts/build_module_v3.py a1 12 --dry-run
    .venv/bin/python scripts/build_module_v3.py a1 12 --verify
    .venv/bin/python scripts/build_module_v3.py a1 12 --no-track-context
    .venv/bin/python scripts/build_module_v3.py a1 12 --force-phase B
    .venv/bin/python scripts/build_module_v3.py a1 12 --force-phase D
    .venv/bin/python scripts/build_module_v3.py a1 12 --final-review
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import textwrap
import time
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Import from v2 — v3 reuses v2's helpers and monkey-patches
# ---------------------------------------------------------------------------
import build_module_v2 as v2
from build_module_v2 import (
    # Monkey-patched dispatch + log (already wired up at v2 import time)
    dispatch_gemini, log,
    # Phase helpers
    run_verify_prose_only, run_verify,
    _build_fix_prompt, _apply_section_fixes, _identify_affected_sections,
    fill_template, _dispatch_prompt, _gemini_output_path,
    mark_phase_locked,
    # Phase E + F (MDX + Claude final review) — reuse directly
    phase_8_mdx as phase_E_v3_delegate,
    phase_9_final_review as phase_F_v3_delegate,
    # Preflight + completion
    preflight_v2, write_completion_report_v2,
)
import build_module as v1
from build_module import (
    is_phase_complete, load_state, save_state, _now_iso,
    extract_phase_output, write_placeholders,
    write_review_with_hash,
    ModuleContext,
)
from batch_gemini_config import (
    CURRICULUM_DIR, PHASES_DIR, PRO_MODEL, PROJECT_ROOT,
    SEMINAR_TRACKS, PRO_TRACKS, get_module_index, get_module_paths,
    slug_for_num,
    CLAUDE_MODEL_CORE_RESEARCH, CLAUDE_MODEL_CORE_ACTIVITIES,
    CLAUDE_MODEL_SEMINAR_RESEARCH, CLAUDE_MODEL_SEMINAR_ACTIVITIES,
    CLAUDE_MODEL_FINAL_REVIEW,
)

# ---------------------------------------------------------------------------
# V3-specific constants
# ---------------------------------------------------------------------------
PHASE_SEQUENCE_V3 = ["A", "B", "C", "audit", "D"]

# Phase IDs mapped to their state.json keys
_V3_PHASE_STATE_IDS: dict[str, list[str]] = {
    "A":     ["v3-A"],
    "B":     ["v3-B"],
    "C":     ["v3-C"],
    "audit": ["v3-audit"],
    "D":     ["v3-D"],
    "E":     ["8"],          # MDX reuses v2's phase 8 state
    "F":     ["9-final-review"],
}

PHASE_LABELS_V3: dict[str, str] = {
    "A":     "Research + Meta",
    "B":     "Content (with track context)",
    "C":     "Activities + Vocab (with track context)",
    "audit": "Prose + Enrichment Audit+Fix Loop",
    "D":     "Cross-Agent Review + Fix (Claude)",
    "E":     "MDX Generation (deterministic)",
    "F":     "Final Review (agent-selectable)",
}

MAX_AUDIT_FIX_ITERS_CORE = 3
MAX_AUDIT_FIX_ITERS_SEMINAR = 5
MAX_D_ITERS = 3


def _max_audit_iters(track: str) -> int:
    """Seminar tracks get more fix attempts due to higher word counts and complexity (#607)."""
    if track in SEMINAR_TRACKS or track in PRO_TRACKS:
        return MAX_AUDIT_FIX_ITERS_SEMINAR
    return MAX_AUDIT_FIX_ITERS_CORE
ESCALATION_MODEL_CLAUDE = "claude-opus-4-6"       # Escalation: Claude fixes what Gemini can't
ESCALATION_MODEL_GEMINI = PRO_MODEL                # Escalation: Gemini fixes what Claude can't

# Dispatch timeouts (seconds) — fail fast instead of hanging
TIMEOUT_CONTENT = 600       # Phase A/B: research + content generation (10 min)
TIMEOUT_ACTIVITIES = 600    # Phase C: activities + vocab (10 min)
TIMEOUT_FIX = 600           # Audit/D/F fix dispatches (10 min — was 300, too tight)
TIMEOUT_REVIEW = 600        # Phase D review+fix (10 min)

# Cap for track context injection
TRACK_CONTEXT_MAX_MODULES_CORE = 5      # Core tracks: last 5 modules for consistency
TRACK_CONTEXT_MAX_MODULES_SEMINAR = 0   # Seminar tracks: independent topics, skip entirely
TRACK_CONTEXT_MAX_CHARS = 150_000       # Hard char cap (~50K tokens)


# ---------------------------------------------------------------------------
# State file — v3 uses a separate file so v2 and v3 don't collide
# ---------------------------------------------------------------------------

def _state_file_v3(ctx: ModuleContext) -> Path:
    return ctx.orch_dir / "state-v3.json"


def _load_state_v3(ctx: ModuleContext) -> dict:
    import json
    sf = _state_file_v3(ctx)
    if sf.exists():
        try:
            return json.loads(sf.read_text("utf-8"))
        except Exception as e:
            # Back up corrupted file before resetting (#601)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = sf.with_suffix(f".corrupted.{ts}.json")
            sf.rename(backup)
            logger.warning(
                "state-v3.json corrupted for %s/%s — backed up to %s, resetting state. Error: %s",
                ctx.track, ctx.slug, backup.name, e,
            )
    return {"track": ctx.track, "slug": ctx.slug, "mode": "v3", "phases": {}}


def _save_state_v3(ctx: ModuleContext, state: dict) -> None:
    import json, tempfile
    sf = _state_file_v3(ctx)
    sf.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: write to temp file then rename to avoid partial writes (#601)
    content = json.dumps(state, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=sf.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(sf)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _is_phase_v3_complete(ctx: ModuleContext, phase_id: str, state: dict) -> bool:
    """Check if a v3 phase is marked complete in state-v3.json."""
    for sid in _V3_PHASE_STATE_IDS.get(phase_id, [phase_id]):
        info = state.get("phases", {}).get(sid, {})
        if info.get("status") == "complete":
            return True
    return False


def _mark_phase_v3(ctx: ModuleContext, state: dict, phase_id: str, status: str, **extra: Any) -> None:
    """Mark a v3 phase in state-v3.json (thread-safe via v2's file lock)."""
    from build_module_v2 import _state_lock, FileLock
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state-v3.json.lock"))
    with lock:
        phases = state.setdefault("phases", {})
        for sid in _V3_PHASE_STATE_IDS.get(phase_id, [phase_id]):
            phases[sid] = {"status": status, "ts": _now_iso(), **extra}
        _save_state_v3(ctx, state)


# ---------------------------------------------------------------------------
# Layer 3: v2 → v3 state migration (one-time, non-destructive)
# ---------------------------------------------------------------------------

# Mapping from v2 phase groups to v3 phase IDs.
# ALL v2 phases in "required" must be complete for the migration to fire.
# "optional" phases don't block migration but are checked for completeness.
_V2_TO_V3_MIGRATION_MAP: list[dict[str, Any]] = [
    {
        "v3_phase": "A",
        "required_v2": ["0", "1"],
        "optional_v2": ["0.5"],
        "artifact_check": "meta",  # Meta must exist — v2 phase 1 should have created it
    },
    {
        "v3_phase": "B",
        "required_v2": ["2"],
        "optional_v2": [],
        "artifact_check": "md",  # Content .md must exist
    },
    {
        "v3_phase": "C",
        "required_v2": ["3a", "3b"],
        "optional_v2": [],
        "artifact_check": "activities",  # Activities file must exist
    },
    {
        "v3_phase": "audit",
        "required_v2": ["3", "5-enrich"],
        "optional_v2": [],
        "artifact_check": None,
    },
    {
        "v3_phase": "D",
        "required_v2": ["6", "7-final"],
        "optional_v2": ["6b"],
        "artifact_check": None,
    },
]


def _migrate_v2_state_to_v3(ctx: ModuleContext, state: dict) -> bool:
    """One-time migration of v2 state.json phases into v3 state-v3.json.

    Only runs if v3 state has NO phases yet (fresh state). Reads the v2
    state.json and maps completed v2 phase groups to v3 phase IDs.

    Returns True if any phases were migrated (for logging).
    """
    # Guard: only migrate if v3 state is empty (one-time)
    if state.get("phases"):
        return False

    # Read v2 state
    v2_state = ctx.state  # v2 state is loaded by preflight_v2 into ctx.state
    v2_phases = v2_state.get("phases", {})
    if not v2_phases:
        return False

    migrated = []
    for mapping in _V2_TO_V3_MIGRATION_MAP:
        v3_phase = mapping["v3_phase"]
        required = mapping["required_v2"]
        artifact_key = mapping["artifact_check"]

        # All required v2 phases must be complete
        all_required = all(
            v2_phases.get(p, {}).get("status") == "complete"
            for p in required
        )
        if not all_required:
            continue

        # Artifact check: the output file must exist
        if artifact_key:
            artifact_path = ctx.paths.get(artifact_key)
            if not artifact_path or not artifact_path.exists():
                continue
            # For content .md, also verify it's non-trivial
            if artifact_key == "md":
                try:
                    wc = len(artifact_path.read_text("utf-8").split())
                    if wc < 100:  # Trivially small = not real content
                        continue
                except Exception:
                    continue

        _mark_phase_v3(ctx, state, v3_phase, "complete",
                       note="migrated-from-v2")
        migrated.append(v3_phase)

    # Also check Phase F (9-final-review) — maps directly
    if v2_phases.get("9-final-review", {}).get("status") == "complete":
        _mark_phase_v3(ctx, state, "F", "complete",
                       note="migrated-from-v2",
                       verdict=v2_phases["9-final-review"].get("verdict", ""))
        migrated.append("F")

    if migrated:
        log(f"  State migration: v2→v3 — migrated phases: {', '.join(migrated)}")
        # Note: audit+D revalidation against current rules is handled by
        # _validate_audit_state() in run_pipeline_v3 (runs after migration).
        return True
    return False


def _validate_audit_state(ctx: ModuleContext, state: dict) -> None:
    """Ensure v3 audit+D completion is consistent with current audit rules.

    Handles two cases:
    1. Migrated states where post-migration gate didn't exist yet (stale files)
    2. Non-migrated states that passed under old rules but fail under new ones

    If audit and D are both marked complete but full audit fails, clears them
    so the fix loops run. Skipped when audit is already failed (let it re-run)
    or when force flags are set.
    """
    if ctx.force_phase or getattr(ctx, "refresh", False):
        return

    phases = state.get("phases", {})
    audit_phase = phases.get("v3-audit", {})
    audit_status = audit_phase.get("status")

    # Handle failed modules with exhausted state — reset for fresh tries under new rules
    if audit_status == "failed":
        content_path = ctx.paths.get("md")
        if content_path and content_path.exists():
            passed, _ = run_verify(content_path, content_only=True)
            if passed:
                # Now passes! Mark complete.
                _mark_phase_v3(ctx, state, "audit", "complete",
                               attempts=audit_phase.get("attempts", 0),
                               note="revalidation-pass")
                log(f"  Audit revalidation: previously FAILED but now PASSES — marking complete")
                return
            # Still fails — but clear exhaustion state so it gets fresh Gemini tries
            cleared = []
            for phase_key in ("audit", "D"):
                for sid in _V3_PHASE_STATE_IDS.get(phase_key, []):
                    if phases.pop(sid, None):
                        cleared.append(sid)
            if cleared:
                _save_state_v3(ctx, state)
                log(f"  Audit revalidation: clearing stale FAILED state — fresh fix loop")
        return

    # Only validate if audit is marked complete
    if audit_status != "complete":
        return

    content_path = ctx.paths.get("md")
    if not content_path or not content_path.exists():
        return

    passed, _ = run_verify(content_path, content_only=False)
    if passed:
        return

    # Full audit fails under current rules — clear audit (and D if present) for fix loops
    cleared = []
    for phase_key in ("audit", "D"):
        for sid in _V3_PHASE_STATE_IDS.get(phase_key, []):
            if phases.pop(sid, None):
                cleared.append(sid)
    if cleared:
        _save_state_v3(ctx, state)
        log(f"  Audit revalidation: FAIL under current rules — cleared {', '.join(cleared)} for fix loops")


# ---------------------------------------------------------------------------
# Claude headless dispatch (Phase A and C via Claude CLI)
# ---------------------------------------------------------------------------

CLAUDE_MODEL_ACTIVITIES = "claude-sonnet-4-6"   # Phase C default
CLAUDE_MODEL_RESEARCH   = "claude-sonnet-4-6"   # Phase A default
CLAUDE_MODEL_REVIEW     = "claude-opus-4-6"     # Phase D default (cross-agent review needs best model)


def _dispatch_claude_phase(
    prompt_file: Path,
    phase_label: str,
    model: str = CLAUDE_MODEL_ACTIVITIES,
    timeout: int = 600,
    allow_tools: list[str] | None = None,
) -> tuple[bool, str]:
    """Call Claude CLI headlessly for a phase prompt file.

    Reads prompt_file, substitutes 'You are Gemini' → 'You are Claude',
    calls `claude --model {model} -p <prompt>`, returns (ok, output).
    """
    import shutil
    claude_bin = shutil.which("claude") or "claude"
    env = __import__("os").environ.copy()
    env.pop("CLAUDECODE", None)  # Prevent nested-session error

    prompt = prompt_file.read_text("utf-8")
    # Adapt persona — templates say "You are Gemini"
    prompt = prompt.replace("You are Gemini", "You are Claude")

    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]
    if allow_tools:
        cmd.extend(["--allowedTools", ",".join(allow_tools)])
    # Reinforce output format — Claude sometimes ignores delimiters in long prompts
    cmd.extend(["--append-system-prompt",
                 "CRITICAL: Your output MUST contain ===REVIEW_START=== and ===REVIEW_END=== "
                 "delimiters wrapping the full structured review. Output without these delimiters "
                 "is automatically discarded. Do NOT summarize — produce the FULL review with "
                 "all 13 dimensions scored, all required H2 sections, and all citations."])

    try:
        from build_module import _run_with_heartbeat
        result = _run_with_heartbeat(
            cmd,
            label=f"Claude {phase_label}",
            timeout=timeout,
            capture_output=True, text=True,
            input=prompt,
            cwd=str(PROJECT_ROOT), env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  Claude CLI error (rc={result.returncode}): {err[:300]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  Claude CLI not found — ensure 'claude' is on PATH")
        return False, ""
    except subprocess.TimeoutExpired:
        log(f"  Claude CLI TIMEOUT ({timeout}s)")
        return False, ""
    except Exception as e:
        log(f"  Claude CLI exception: {e}")
        return False, ""


# ---------------------------------------------------------------------------
# Track context injection
# ---------------------------------------------------------------------------

def _write_track_context(ctx: ModuleContext) -> Path:
    """Track context is not needed — plans, research, and enriched meta outlines
    already give Gemini everything required for consistent, non-repetitive content.
    Returns an empty file (kept for interface compatibility with Phase B/C).
    """
    context_path = ctx.orch_dir / "track-context.md"
    context_path.write_text("", "utf-8")
    return context_path


# ---------------------------------------------------------------------------
# Helper: extract delimiter content
# ---------------------------------------------------------------------------

def _extract_delimiter(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between ===TAG_START=== and ===TAG_END=== delimiters."""
    if start_tag not in text or end_tag not in text:
        return None
    s = text.index(start_tag) + len(start_tag)
    e = text.index(end_tag)
    return text[s:e].strip()


def _count_diff_lines(before: str, after: str) -> int:
    """Count the number of changed lines between two texts.

    Uses difflib for accurate line-level diff — counts additions, deletions,
    and modifications. Unlike set-based diff, this correctly handles duplicate
    lines and doesn't miss bulk insertions (#623).
    """
    import difflib
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = list(difflib.unified_diff(before_lines, after_lines, n=0))
    # Count lines starting with + or - (excluding the +++ and --- headers)
    return sum(1 for line in diff if line.startswith(('+', '-'))
               and not line.startswith(('+++', '---')))


# ---------------------------------------------------------------------------
# Phase D helpers: pre-compute audit metrics + extract H2 sections
# ---------------------------------------------------------------------------

def _compute_audit_metrics(ctx: ModuleContext) -> dict[str, str]:
    """Pre-compute audit metrics by running the audit programmatically.

    Returns a dict of string values ready for template injection. This replaces
    the old {AUDIT_WORD_COUNT} etc. placeholders that were never substituted.
    """
    import yaml
    from audit.cleaners import clean_for_stats, clean_for_immersion, extract_core_content, calculate_immersion

    metrics: dict[str, str] = {}
    content_path = ctx.paths.get("md")

    # Word count
    if content_path and content_path.exists():
        content = content_path.read_text("utf-8")
        # Strip frontmatter
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]

        core = extract_core_content(body)
        core_lines = [ln for ln in core.split("\n") if not ln.strip().startswith("|")]
        core_cleaned = clean_for_stats("\n".join(core_lines))
        word_count = len(core_cleaned.split())
    else:
        word_count = 0
        body = ""
        content = ""

    word_target = ctx.word_target or 0
    word_pct = (word_count / word_target * 100) if word_target else 0
    metrics["COMPUTED_WORD_COUNT"] = str(word_count)
    metrics["COMPUTED_WORD_TARGET"] = str(word_target)
    metrics["COMPUTED_WORD_PERCENT"] = f"{word_pct:.1f}"

    # Activity count (from YAML sidecar)
    act_path = ctx.paths.get("activities")
    act_count = 0
    if act_path and act_path.exists():
        try:
            act_data = yaml.safe_load(act_path.read_text("utf-8"))
            if isinstance(act_data, list):
                act_count = len(act_data)
        except Exception:
            pass
    metrics["COMPUTED_ACTIVITY_COUNT"] = str(act_count)

    # Vocabulary count (from YAML sidecar — key may be "vocab" or "vocabulary")
    vocab_path = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
    vocab_count = 0
    if vocab_path and vocab_path.exists():
        try:
            vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
            if isinstance(vocab_data, list):
                vocab_count = len(vocab_data)
            elif isinstance(vocab_data, dict):
                # Some vocab files have a 'vocabulary' key
                vlist = vocab_data.get("vocabulary", vocab_data.get("items", []))
                if isinstance(vlist, list):
                    vocab_count = len(vlist)
        except Exception:
            pass
    metrics["COMPUTED_VOCAB_COUNT"] = str(vocab_count)

    # Engagement box count
    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭📜⚔️🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮🎓🔍])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography)\])'
    )
    engagement_count = len(engagement_pattern.findall(content))
    metrics["COMPUTED_ENGAGEMENT_COUNT"] = str(engagement_count)

    # Immersion percentage (calculate_immersion already returns 0-100)
    if body:
        imm_text = clean_for_immersion(body)
        immersion_pct = calculate_immersion(imm_text)
    else:
        immersion_pct = 0.0
    metrics["COMPUTED_IMMERSION_PERCENT"] = f"{immersion_pct:.1f}"

    # Immersion target (level-dependent)
    from audit.config import get_a1_immersion_range, get_a2_immersion_range, get_b1_immersion_range
    level = ctx.track.split("-")[0].upper() if "-" not in ctx.track else ctx.track.upper()
    # Normalize: a1 -> A1, b2-hist -> B2-HIST
    level_code = level[:2] if len(level) >= 2 else level
    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    try:
        if level_code == "A1":
            min_imm, max_imm = get_a1_immersion_range(module_num)
        elif level_code == "A2":
            min_imm, max_imm = get_a2_immersion_range(module_num)
        elif level_code == "B1":
            min_imm, max_imm = get_b1_immersion_range(module_num)
        else:
            min_imm, max_imm = 85, 95  # B2+ default
    except Exception:
        min_imm, max_imm = 80, 95
    metrics["COMPUTED_IMMERSION_TARGET"] = f"{min_imm}-{max_imm}%"

    # Audit status (quick run)
    if content_path and content_path.exists():
        passed, _ = run_verify(content_path, content_only=False)
        metrics["COMPUTED_AUDIT_STATUS"] = "PASS" if passed else "FAIL"
    else:
        metrics["COMPUTED_AUDIT_STATUS"] = "NO_CONTENT"

    return metrics


def _extract_h2_sections(content_path: Path) -> str:
    """Extract all H2 headers from a content .md file as a numbered list."""
    if not content_path.exists():
        return "(content file not found)"
    text = content_path.read_text("utf-8")
    h2s = re.findall(r"^## (.+)$", text, re.MULTILINE)
    if not h2s:
        return "(no H2 sections found)"
    return "\n".join(f"{i}. {h}" for i, h in enumerate(h2s, 1))


def _inject_metrics_into_prompt(prompt_text: str, metrics: dict[str, str]) -> str:
    """Replace {COMPUTED_*} placeholders in a prompt with computed values."""
    for key, val in metrics.items():
        prompt_text = prompt_text.replace("{" + key + "}", val)
    return prompt_text


def _extract_audit_failures(audit_output: str) -> str:
    """Extract the actionable failure lines from audit output for the repair prompt."""
    lines = audit_output.strip().split("\n")
    # Keep FAIL lines, error lines, and gate descriptions
    failure_lines = []
    for line in lines:
        stripped = line.strip()
        if any(kw in stripped.upper() for kw in ["FAIL", "ERROR", "VIOLATION", "MISSING", "GATE"]):
            failure_lines.append(stripped)
        elif stripped.startswith("❌") or stripped.startswith("🔴"):
            failure_lines.append(stripped)
    if not failure_lines:
        # Fallback: return last 40 lines
        return "\n".join(lines[-40:])
    return "\n".join(failure_lines)


# Audit failure codes that indicate diffuse issues (not FIND/REPLACE fixable).
# These require structural rewrite, not targeted repair.
_DIFFUSE_FAILURE_CODES = {
    "ROBOTIC_STRUCTURE",        # Sentence pattern repetition throughout
    "CONTENT_REDUNDANCY",       # Duplicate sentences across sections
    "EXCESSIVE_METAPHOR",       # Too many metaphors (prose style issue)
    "THEORY_FRONTLOADING",      # Structure issue: too much theory before practice
    "LOW_IMMERSION",            # Fundamental language balance problem
}

# Review keywords that indicate diffuse issues (from D.1 review text).
# These are specific phrases unlikely to appear in unrelated contexts.
_DIFFUSE_REVIEW_KEYWORDS = [
    "structural rewrite needed",
    "needs rebuild",
    "fundamental restructuring",
    "wholesale rewrite",
]


def _run_deterministic_fixes(ctx: ModuleContext) -> int:
    """Run all zero-cost deterministic fixes on a module's files.

    Consolidates: euphony, IPA normalization, YAML schema fixes, forbidden
    activity removal. Returns total number of fixes applied.

    Called before the diffuse-vs-targeted triage so that cascading failures
    from a single YAML error don't trick the triage into marking the module
    as needing a full rebuild (#623).
    """
    total = 0
    content_path = ctx.paths.get("md")

    # 1. Euphony auto-fix (content .md)
    if content_path and content_path.exists():
        from audit.checks.euphony import auto_fix_euphony
        text = content_path.read_text("utf-8")
        fixed_text, n = auto_fix_euphony(text, str(content_path))
        if n > 0:
            content_path.write_text(fixed_text, "utf-8")
            total += n
            log(f"    Auto-fix: {n} euphony violation(s)")

    # 2. IPA normalization (content, vocab, activities)
    from lint_ipa import apply_fixes as ipa_apply_fixes
    vocab_path = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
    for target in [content_path, vocab_path, ctx.paths.get("activities")]:
        if target and target.exists():
            t = target.read_text("utf-8")
            fixed_t, n = ipa_apply_fixes(t)
            if n > 0:
                target.write_text(fixed_t, "utf-8")
                total += n
                log(f"    Auto-fix: {n} IPA issue(s) in {target.name}")

    # 3. YAML schema fixes (activities file)
    act_path = ctx.paths.get("activities")
    if act_path and act_path.exists():
        try:
            from audit.checks.yaml_schema_validation import fix_yaml_file
            n, msgs = fix_yaml_file(act_path, dry_run=False)
            if n > 0:
                total += n
                log(f"    Auto-fix: {n} YAML schema fix(es) in {act_path.name}")
                for msg in msgs[:3]:
                    log(f"      {msg[:120]}")
        except Exception as e:
            log(f"    Auto-fix: YAML fix failed: {e}")

    # 4. Forbidden activity removal (level/focus-dependent)
    if act_path and act_path.exists():
        try:
            from audit.checks.yaml_schema_validation import remove_forbidden_activities
            from audit.core import detect_level, detect_focus, load_yaml_meta
            meta_data = load_yaml_meta(str(content_path)) if content_path else {}
            if content_path and content_path.exists():
                content = content_path.read_text("utf-8")
                import yaml as yaml_lib
                fm_str = yaml_lib.dump(meta_data, sort_keys=False, allow_unicode=True) if meta_data else ""
                level_code, module_num, _ = detect_level(str(content_path), fm_str)
                module_focus = detect_focus(fm_str, level_code, module_num,
                                            meta_data.get("title", "") if meta_data else "", str(content_path))
                n_removed, _ = remove_forbidden_activities(act_path, level_code, module_focus, dry_run=False)
                if n_removed > 0:
                    total += n_removed
                    log(f"    Auto-fix: removed {n_removed} forbidden activity(ies)")
        except Exception as e:
            log(f"    Auto-fix: forbidden activity check failed: {e}")

    return total


def _all_issues_diffuse(audit_output: str, review_text: str) -> bool:
    """Determine if ALL issues are diffuse (not fixable by FIND/REPLACE).

    Returns True only if there are failure signals AND every one is diffuse.
    If there are ANY targeted failures (grammar, missing content, wrong facts),
    returns False so D.2 can attempt a repair.

    Classification is deterministic — based on audit failure codes and
    review keywords, not LLM judgment (#623).
    """
    import re as _re

    # Extract failing codes: look for lines containing ❌ or FAIL followed by [CODE]
    # Uses a reliable regex that checks the full line context, not fragile split logic.
    failing_codes: set[str] = set()
    for line in audit_output.split("\n"):
        if "❌" in line or "FAIL" in line.upper():
            codes_in_line = _re.findall(r'\[([A-Z_]{3,})\]', line)
            failing_codes.update(codes_in_line)

    if not failing_codes and not review_text:
        return False  # No signal at all — don't skip D.2

    # Check if ALL failing codes are diffuse
    has_targeted = bool(failing_codes - _DIFFUSE_FAILURE_CODES)
    if has_targeted:
        return False  # At least one targeted issue exists

    # Also check review text for diffuse keywords (exact phrase match)
    review_lower = review_text.lower() if review_text else ""
    has_diffuse_review = any(kw in review_lower for kw in _DIFFUSE_REVIEW_KEYWORDS)

    # Only return True if we found diffuse signals and NO targeted signals
    has_diffuse_audit = bool(failing_codes & _DIFFUSE_FAILURE_CODES)
    return has_diffuse_audit or has_diffuse_review


# ---------------------------------------------------------------------------
# Phase A: Research + Meta (combined)
# ---------------------------------------------------------------------------

_RESEARCH_EXISTS_MIN_WORDS = 500  # Min word count for an existing research file to be considered usable
_META_SECTION_MAX_PCT = 0.25      # A single section must not exceed 25% of word_target


def _meta_has_oversized_sections(ctx: ModuleContext) -> bool:
    """Return True if any meta section consumes >25% of word_target.

    Used as a health check inside phase_A_v3: if Phase A is marked complete but
    the meta still has oversized sections (written by old prompts), re-run Phase A
    automatically to produce a properly split outline.
    """
    import yaml
    meta_path = ctx.paths.get("meta")
    if not meta_path or not meta_path.exists():
        return False
    try:
        data = yaml.safe_load(meta_path.read_text("utf-8")) or {}
        wt = data.get("word_target", 0)
        if not wt:
            return False
        threshold = wt * _META_SECTION_MAX_PCT
        outline = data.get("content_outline", [])
        return any(
            isinstance(s, dict) and s.get("words", 0) > threshold
            for s in outline
        )
    except Exception:
        return False


def _research_file_is_usable(ctx: ModuleContext) -> bool:
    """Return True if an existing research file has enough content to skip re-research."""
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        return False
    try:
        text = research_path.read_text("utf-8")
        word_count = len(text.split())
        return word_count >= _RESEARCH_EXISTS_MIN_WORDS
    except Exception:
        return False


def phase_A_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase A: Research + Meta outline.

    For seminar tracks:
      - If research file exists and is substantial (>= 500 words):
          dispatch phase-A-meta-only.md (meta rebuild from existing research, 1 call saved)
      - Otherwise:
          dispatch phase-A-seminar.md (full research + meta, standard path)

    For core tracks: uses phase-A-core.md (lightweight research + meta).

    Extracts RESEARCH_START/END → saves to research path (full path only).
    Extracts META_OUTLINE_START/END → updates meta file (both paths).
    """
    phase = "A"

    # Layer 2A: Artifact guard — don't rewrite the blueprint of a house that's already built.
    # If content .md exists and meets word target, meta is "locked" regardless of health checks.
    force_research = getattr(ctx, "force_research", False)
    if not force_research and _is_phase_v3_complete(ctx, phase, state):
        content_path = ctx.paths.get("md")
        content_exists = content_path and content_path.exists()
        content_sufficient = False
        if content_exists:
            try:
                wc = len(content_path.read_text("utf-8").split())
                content_sufficient = wc >= ctx.word_target * 0.8
            except Exception:
                pass

        if content_sufficient:
            # Content was built against this meta — lock it, skip health checks entirely
            log(f"  Phase A: SKIP (meta locked — content exists at {wc}w, target {ctx.word_target}w)")
            return True
        elif _meta_has_oversized_sections(ctx):
            # No content yet, meta is bad — re-run
            log("  Phase A: Meta health check FAILED — oversized section detected, re-running")
            _mark_phase_v3(ctx, state, phase, "pending", note="health-check-reset")
        else:
            # Sanity: meta file must actually exist before skipping
            meta_path = ctx.paths.get("meta")
            if meta_path and not meta_path.exists():
                log("  Phase A: State says complete but meta missing — re-running")
                _mark_phase_v3(ctx, state, phase, "pending", note="missing-meta-reset")
            else:
                log("  Phase A: SKIP (already complete)")
                return True
    elif not force_research and not getattr(ctx, "refresh", False) and not _is_phase_v3_complete(ctx, phase, state):
        # Phase A not yet complete in v3 state — but check if content already exists
        # (v2-built module where migration didn't fire, or partial migration)
        # Skipped on --rebuild (refresh=True) so Phase A can regenerate meta
        content_path = ctx.paths.get("md")
        meta_path = ctx.paths.get("meta")
        if content_path and content_path.exists() and meta_path and meta_path.exists():
            try:
                import yaml as _yaml
                wc = len(content_path.read_text("utf-8").split())
                meta_data = _yaml.safe_load(meta_path.read_text("utf-8")) or {}
                has_outline = (isinstance(meta_data.get("content_outline"), list)
                               and len(meta_data.get("content_outline", [])) >= 2)
                has_target = bool(meta_data.get("word_target"))
                if wc >= ctx.word_target * 0.8 and has_outline and has_target:
                    log(f"  Phase A: ADOPT — existing content ({wc}w) + valid meta → locking")
                    _mark_phase_v3(ctx, state, phase, "complete", note="adopted-existing-meta")
                    return True
            except Exception:
                pass

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    is_pro = ctx.track in PRO_TRACKS

    # Optimisation: if research already exists (pre-seeded), skip re-research
    research_exists = (is_seminar or is_pro) and _research_file_is_usable(ctx)
    if is_seminar or is_pro:
        if research_exists:
            research_path = ctx.paths.get("research")
            word_count = len(research_path.read_text("utf-8").split()) if research_path else 0
            log(f"  Phase A: Research file found ({word_count:,}w) — skipping research, meta-only")
            template_name = "phase-A-meta-only.md"
        elif is_pro:
            template_name = "phase-A-pro.md"
        else:
            template_name = "phase-A-seminar.md"
    else:
        template_name = "phase-A-core.md"

    template = PHASES_DIR / template_name

    if not template.exists():
        log(f"  Phase A: ERROR — template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "phase-A-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log(f"  Phase A: DRY-RUN — would dispatch {template_name}")
        return True

    use_claude = "A" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_A", CLAUDE_MODEL_RESEARCH)
        log(f"  Phase A: Dispatching {template_name} via Claude ({claude_model})...")
        ok, raw_output = _dispatch_claude_phase(
            prompt_file, "Phase A", model=claude_model,
            timeout=600,
            allow_tools=["WebSearch", "WebFetch", "Read"],
        )
    else:
        log(f"  Phase A: Dispatching {template_name}...")
        output_file = _gemini_output_path(ctx.slug, "pA")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v3-{ctx.slug}-pA",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_CONTENT,
        )
        # Save raw output to orchestration dir for debugging
        if raw_output:
            (ctx.orch_dir / "phase-A-output.md").write_text(raw_output, "utf-8")
    if not ok:
        log(f"  Phase A: FAILED — {'Claude' if use_claude else 'Gemini'} dispatch error")
        _mark_phase_v3(ctx, state, phase, "failed")
        return False

    # Extract and save research (only in full research path — meta-only doesn't produce this)
    if not research_exists:
        research_text = _extract_delimiter(raw_output, "===RESEARCH_START===", "===RESEARCH_END===")
        if research_text:
            research_path = ctx.paths.get("research")
            if research_path:
                research_path.parent.mkdir(parents=True, exist_ok=True)
                research_path.write_text(research_text, "utf-8")
                log(f"  Phase A: Research saved → {research_path.name}")
            else:
                (ctx.orch_dir / "phase-A-research.md").write_text(research_text, "utf-8")
                log("  Phase A: Research saved → phase-A-research.md (no research path in ctx)")
        else:
            if is_seminar or is_pro:
                log("  Phase A: WARNING — no RESEARCH delimiters in output (seminar/pro track)")
            else:
                log("  Phase A: NOTE — no research delimiters (expected for some core tracks)")

    # Extract and apply meta outline
    meta_text = _extract_delimiter(raw_output, "===META_OUTLINE_START===", "===META_OUTLINE_END===")
    if meta_text:
        import yaml
        try:
            outline_data = yaml.safe_load(meta_text)
        except yaml.YAMLError as e:
            log(f"  Phase A: WARNING — meta outline YAML parse error: {e}")
            outline_data = None

        if outline_data and isinstance(outline_data, dict) and "content_outline" in outline_data:
            meta_path = ctx.paths.get("meta")
            if meta_path and meta_path.exists():
                try:
                    existing_meta = yaml.safe_load(meta_path.read_text("utf-8")) or {}
                    existing_meta["content_outline"] = outline_data["content_outline"]
                    meta_path.write_text(
                        yaml.dump(existing_meta, allow_unicode=True,
                                  default_flow_style=False, sort_keys=False),
                        "utf-8",
                    )
                    # Update ctx's content_outline so Phase B can see it
                    ctx.content_outline = outline_data["content_outline"]  # type: ignore[attr-defined]
                    mode = "meta-only" if research_exists else "full"
                    log(f"  Phase A: Meta outline updated [{mode}] → {meta_path.name} "
                        f"({len(outline_data['content_outline'])} sections)")
                except Exception as e:
                    log(f"  Phase A: WARNING — could not update meta: {e}")
            else:
                (ctx.orch_dir / "phase-A-meta-outline.yaml").write_text(meta_text, "utf-8")
                log("  Phase A: Meta outline saved → phase-A-meta-outline.yaml (no meta path)")
        else:
            log("  Phase A: WARNING — no content_outline in META_OUTLINE block")
            (ctx.orch_dir / "phase-A-meta-outline-raw.md").write_text(meta_text or "", "utf-8")
    else:
        log("  Phase A: FAILED — no META_OUTLINE delimiters in output")
        _mark_phase_v3(ctx, state, phase, "failed")
        return False

    _mark_phase_v3(ctx, state, phase, "complete",
                   task_id=f"v3-{ctx.slug}-pA",
                   mode="meta-only" if research_exists else "full")
    return True


# ---------------------------------------------------------------------------
# Phase B: Content (delegates to v2's phase_2_v2 + track context)
# ---------------------------------------------------------------------------

def phase_B_v3(ctx: ModuleContext, state: dict, use_track_context: bool = True) -> bool:
    """Phase B: Write prose. Delegates to v2's phase_2_content with track context override.

    Track context is injected by writing track-context.md and setting
    TRACK_CONTEXT_PATH placeholder override before dispatching.
    """
    phase = "B"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  Phase B: SKIP (already complete)")
        return True

    # Layer 2B: Artifact guard — if content .md already exists and is substantial,
    # adopt it rather than regenerating. This prevents v2-built content from being
    # overwritten when v3 runs on a track with existing v2 modules.
    if not getattr(ctx, "refresh", False):
        content_path = ctx.paths.get("md")
        if content_path and content_path.exists():
            try:
                wc = len(content_path.read_text("utf-8").split())
                if wc >= ctx.word_target * 0.8:
                    log(f"  Phase B: ADOPT — existing content ({wc}w, target {ctx.word_target}w)")
                    _mark_phase_v3(ctx, state, phase, "complete", note="adopted-existing-content",
                                   words=wc)
                    # Also mark v2 phase 2 so v2 doesn't try to regenerate
                    mark_phase_locked(ctx, "2", "complete", note="v3-phase-B-adopt", words=wc)
                    return True
            except Exception:
                pass

    if ctx.dry_run:
        log("  Phase B: DRY-RUN — would dispatch content (phase-2-content.md)")
        return True

    # Inject track context path into placeholders if requested
    if use_track_context:
        log("  Phase B: Building track context...")
        track_ctx_path = _write_track_context(ctx)
        # Inject TRACK_CONTEXT_PATH override so fill_template uses it
        # We monkey-patch the placeholder file temporarily via overrides in fill_template
        # (The template references {TRACK_CONTEXT_PATH} optionally — no-strict mode ignores unknowns)
        ctx._track_context_path = str(track_ctx_path)  # type: ignore[attr-defined]
        log(f"  Phase B: Track context → {track_ctx_path.name} "
            f"({track_ctx_path.stat().st_size:,} bytes)")

    # Use v2's phase_2_content — it handles archive detection, adoption, etc.
    # Temporarily inject TRACK_CONTEXT_PATH as a fill_template override by wrapping dispatch
    if use_track_context and hasattr(ctx, "_track_context_path"):
        _inject_track_context_placeholder(ctx, "TRACK_CONTEXT_PATH")

    ok = v2.phase_2_v2(ctx)

    if not ok:
        _mark_phase_v3(ctx, state, phase, "failed")
        return False

    # Post-B gates (#623): fail fast on structurally doomed content.
    content_path = ctx.paths.get("md")
    if content_path and content_path.exists():
        from audit.cleaners import clean_for_stats
        raw = content_path.read_text("utf-8")

        # Gate 1: Word count — content must be ≥80% of target
        if ctx.word_target:
            wc = len(clean_for_stats(raw).split())
            threshold = ctx.word_target * 0.8
            if wc < threshold:
                log(f"  Phase B: FAILED — word count {wc} < 80% target ({int(threshold)}w)")
                _mark_phase_v3(ctx, state, phase, "failed",
                               note=f"word-count-{wc}-below-80pct-{ctx.word_target}")
                return False

        # Gate 2: Content purity pre-screen — catch worst AI artifacts
        # (robotic starters, duplicate sentences) before they reach Phase D.
        from audit.checks.content_purity import check_content_purity
        purity_violations = check_content_purity(raw)
        critical = [v for v in purity_violations if v.get("severity") == "error"]
        if critical:
            log(f"  Phase B: WARNING — {len(critical)} content purity issue(s) detected")
            for v in critical[:3]:
                log(f"    {v['type']}: {v['issue'][:100]}")

    _mark_phase_v3(ctx, state, phase, "complete")
    # Invalidate downstream artifacts — status cache and review files are now stale
    _invalidate_stale_artifacts(ctx)
    return True


def _invalidate_stale_artifacts(ctx: ModuleContext) -> None:
    """Delete stale audit cache and review files after content rebuild.

    When Phase B writes new content, any previous audit results and review
    files are from the OLD content and must not be served by the API.
    """
    slug = ctx.slug
    track_dir = ctx.paths.get("md", Path()).parent

    # 1. Delete status cache
    status_file = track_dir / "status" / f"{slug}.json"
    if status_file.exists():
        status_file.unlink()
        log(f"  Phase B: Invalidated stale status cache: {status_file.name}")

    # 2. Delete old review files (Phase D will regenerate them)
    review_dir = track_dir / "review"
    for review_name in [f"{slug}-review.md", f"{slug}-final-review.md"]:
        review_file = review_dir / review_name
        if review_file.exists():
            review_file.unlink()
            log(f"  Phase B: Invalidated stale review: {review_name}")

    # 3. Delete old audit log
    audit_file = track_dir / "audit" / f"{slug}-audit.md"
    if audit_file.exists():
        audit_file.unlink()
        log(f"  Phase B: Invalidated stale audit: {audit_file.name}")


def _inject_track_context_placeholder(ctx: ModuleContext, key: str) -> None:
    """Append TRACK_CONTEXT_PATH to placeholders.yaml so phase-2-content.md can use it.

    Uses --no-strict so if the template doesn't reference it, it's silently ignored.
    """
    import yaml
    placeholder_path = ctx.orch_dir / "placeholders.yaml"
    if not placeholder_path.exists():
        return
    try:
        data = yaml.safe_load(placeholder_path.read_text("utf-8")) or {}
        data[key] = getattr(ctx, "_track_context_path", "")
        placeholder_path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False),
            "utf-8",
        )
    except Exception as e:
        log(f"  Phase B: WARNING — could not inject {key}: {e}")


# ---------------------------------------------------------------------------
# Phase C: Activities + Vocabulary (single combined call)
# ---------------------------------------------------------------------------

def phase_C_v3(ctx: ModuleContext, state: dict, use_track_context: bool = True) -> bool:
    """Phase C: Generate activities + vocabulary in a single Gemini call.

    Uses existing phase-3-activities.md template (outputs both ACTIVITIES + VOCABULARY).
    Injects track context if available.
    """
    phase = "C"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  Phase C: SKIP (already complete)")
        return True

    # Check if both files already exist and are valid
    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")
    if (act_path and act_path.exists() and voc_path and voc_path.exists()):
        from build_module_v2 import _validate_activities_yaml
        if _validate_activities_yaml(act_path):
            log("  Phase C: ADOPT — existing activities/vocab found and valid")
            _mark_phase_v3(ctx, state, phase, "complete", note="adopted-existing")
            return True
        else:
            log("  Phase C: Existing activities invalid — deleting and regenerating")
            act_path.unlink(missing_ok=True)

    # Inject track context
    if use_track_context:
        if not hasattr(ctx, "_track_context_path"):
            track_ctx_path = _write_track_context(ctx)
            ctx._track_context_path = str(track_ctx_path)  # type: ignore[attr-defined]
            log(f"  Phase C: Track context → {Path(ctx._track_context_path).name}")
        _inject_track_context_placeholder(ctx, "TRACK_CONTEXT_PATH")

    template = PHASES_DIR / "phase-3-activities.md"
    if not template.exists():
        log(f"  Phase C: ERROR — template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "phase-C-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log("  Phase C: DRY-RUN — would dispatch phase-3-activities.md")
        return True

    use_claude = "C" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_C", CLAUDE_MODEL_ACTIVITIES)
        log(f"  Phase C: Dispatching activities + vocab via Claude ({claude_model})...")
        ok, raw_output = _dispatch_claude_phase(
            prompt_file, "Phase C", model=claude_model, timeout=600,
        )
    else:
        log("  Phase C: Dispatching activities + vocab...")
        output_file = _gemini_output_path(ctx.slug, "pC")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v3-{ctx.slug}-pC",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_ACTIVITIES,
        )
    if not ok:
        log(f"  Phase C: FAILED — {'Claude' if use_claude else 'Gemini'} dispatch error")
        _mark_phase_v3(ctx, state, phase, "failed")
        return False

    # Phase C uses stdout_only=True. Gemini outputs ACTIVITIES + VOCABULARY
    # delimiters to stdout. Extract from raw_output and write to target files.
    wrote_activities = act_path and act_path.exists() and act_path.stat().st_size > 10
    wrote_vocab = voc_path and voc_path.exists() and voc_path.stat().st_size > 10

    if not wrote_activities:
        activities_text = _extract_delimiter(raw_output, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
        if activities_text and act_path:
            act_path.parent.mkdir(parents=True, exist_ok=True)
            act_path.write_text(activities_text, "utf-8")
            wrote_activities = True
            log(f"  Phase C: Activities extracted → {act_path.name}")

    if not wrote_vocab:
        vocab_text = _extract_delimiter(raw_output, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            wrote_vocab = True
            log(f"  Phase C: Vocabulary extracted → {voc_path.name}")

    if not wrote_activities or not wrote_vocab:
        log(f"  Phase C: FAILED — missing files: activities={wrote_activities}, vocab={wrote_vocab}")
        _mark_phase_v3(ctx, state, phase, "failed",
                       note=f"missing-files-act={wrote_activities}-voc={wrote_vocab}")
        return False

    # Post-C schema validation gate (#623): verify generated YAML is valid
    # before marking complete — prevents 15-20 modules from wasting audit+D cycles
    from build_module_v2 import _validate_activities_yaml
    if act_path and act_path.exists() and not _validate_activities_yaml(act_path):
        log(f"  Phase C: FAILED — activities YAML failed schema validation")
        _mark_phase_v3(ctx, state, phase, "failed", note="activities-schema-invalid")
        return False

    # Also mark v1 state IDs so downstream phases don't regenerate
    mark_phase_locked(ctx, "3a", "complete", note="v3-phase-C")
    mark_phase_locked(ctx, "3b", "complete", note="v3-phase-C")

    _mark_phase_v3(ctx, state, phase, "complete", task_id=f"v3-{ctx.slug}-pC")
    return True


# ---------------------------------------------------------------------------
# Agent escalation: hand fix to the other agent when primary exhausts
# ---------------------------------------------------------------------------

def _escalate_fix(ctx: ModuleContext, audit_output: str, phase_label: str,
                  content_only: bool = True, primary_agent: str = "gemini") -> bool:
    """Escalate a failed fix to the opposite agent when primary exhausts.

    When primary_agent is 'gemini' (audit fix loops), escalates to Claude Opus.
    When primary_agent is 'claude' (Phase D), escalates to Gemini.
    Builds a targeted fix prompt, dispatches, applies section fixes, re-audits.
    Returns True if audit passes after fix.
    """
    # Pre-flight: retry audit once — borderline cases can flip between runs.
    # Avoids wasting an Opus call on a non-deterministic flake.
    passed_retry, _ = run_verify(ctx.paths["md"], content_only=content_only)
    if passed_retry:
        log(f"  {phase_label}: Pre-escalation retry PASS — no escalation needed")
        return True

    import textwrap

    # Build a targeted escalation prompt — always use section-level format
    # since Claude CLI outputs to stdout (can't edit files directly)
    lines = audit_output.strip().split("\n")
    error_excerpt = "\n".join(lines[-60:])

    content_path = ctx.paths["md"]
    affected = _identify_affected_sections(audit_output, content_path)

    # Read the affected sections so Claude has context
    section_content = ""
    if affected and content_path.exists():
        full_text = content_path.read_text("utf-8")
        for section_name in affected:
            # Extract the section text
            import re
            pattern = rf"(^## {re.escape(section_name)}.*?)(?=^## |\Z)"
            match = re.search(pattern, full_text, re.MULTILINE | re.DOTALL)
            if match:
                section_content += f"\n---\n{match.group(1).strip()}\n"

    if not affected:
        # Fallback: read last 200 lines of the file for context
        if content_path.exists():
            all_lines = content_path.read_text("utf-8").split("\n")
            section_content = "\n".join(all_lines[-200:])

    prompt_text = textwrap.dedent(f"""\
        # Escalation Fix — {phase_label}

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        {error_excerpt}
        ```

        ## Current Content of Affected Section(s)

        {section_content}

        ## File Path

        `{content_path}`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {{section title}}
        {{fixed section content}}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.
    """)

    fix_file = ctx.orch_dir / f"{phase_label}-escalation-prompt.md"
    fix_file.write_text(prompt_text, "utf-8")

    if primary_agent == "claude":
        # Primary was Claude → escalate to Gemini
        log(f"  {phase_label}: Escalating to Gemini (primary was Claude)...")
        output_file = _gemini_output_path(ctx.slug, f"{phase_label}-escalation")
        ok, output = dispatch_gemini(
            _dispatch_prompt(ctx, fix_file),
            task_id=f"v3-{ctx.slug}-escalation",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_FIX,
        )
    else:
        # Primary was Gemini → escalate to Claude Opus
        log(f"  {phase_label}: Escalating to Claude Opus...")
        ok, output = _dispatch_claude_phase(
            fix_file,
            phase_label=f"{phase_label}-escalation",
            model=ESCALATION_MODEL_CLAUDE,
            timeout=900,  # 15 min — Opus needs more time for large audit+content
        )
    if not ok:
        log(f"  {phase_label}: Escalation dispatch failed")
        return False

    # Apply section fixes from Claude's output
    if output and "===SECTION_FIX_START===" in output:
        _apply_section_fixes(ctx.paths["md"], output)
        escalation_agent = "Gemini" if primary_agent == "claude" else "Claude"
        log(f"  {phase_label}: {escalation_agent} escalation fixes applied")
    elif output:
        log(f"  {phase_label}: Escalation output missing SECTION_FIX delimiters — cannot apply")
        # Save raw output for debugging
        (ctx.orch_dir / f"{phase_label}-escalation-raw.md").write_text(output, "utf-8")

    # Re-audit
    passed, _ = run_verify(ctx.paths["md"], content_only=content_only)
    if passed:
        escalation_agent = "Gemini" if primary_agent == "claude" else "Claude Opus"
        log(f"  {phase_label}: Escalation PASS — {escalation_agent} fixed the issues")
    else:
        log(f"  {phase_label}: Escalation FAIL — both agents exhausted")
    return passed


# ---------------------------------------------------------------------------
# Audit loop (combined prose + enrichment)
# ---------------------------------------------------------------------------

def phase_audit_v3(ctx: ModuleContext, state: dict) -> bool:
    """Audit loop: runs prose/enrichment audit (content_only), dispatches fixes.

    Combines v2's Phase 3 (prose) and Phase 5 (enrichment) into one loop.
    Max iterations are track-aware (#607). Uses run_verify (content_only=True) —
    skips activity + review gates since this loop focuses on prose fixes.
    Activity validation runs in the pre-D gate via --skip-review (#606).
    """
    phase = "audit"
    max_iters = getattr(ctx, "max_fix", None) or _max_audit_iters(ctx.track)

    if _is_phase_v3_complete(ctx, phase, state):
        log("  Audit: SKIP (already complete)")
        return True

    # Handle previously exhausted audit — skip Gemini, try escalation directly
    audit_state = state.get("phases", {}).get("v3-audit", {})
    if audit_state.get("status") == "failed" and not ctx.force_phase:
        prev_attempts = audit_state.get("attempts", 0)
        was_escalated = "escalation" in audit_state.get("note", "")
        if prev_attempts >= max_iters:
            if was_escalated:
                log(f"  Audit: SKIP — both agents exhausted. Use --force-phase audit to retry.")
                return False
            if ctx.dry_run:
                log(f"  Audit: DRY-RUN — Gemini previously exhausted, would escalate to Claude")
                return True
            # Gemini exhausted but escalation not tried — go straight to Claude
            log(f"  Audit: Gemini previously exhausted — trying direct escalation")
            passed, output = run_verify(ctx.paths["md"], content_only=True)
            if passed:
                log(f"  Audit: PASS (issues resolved since last run)")
                _mark_phase_v3(ctx, state, phase, "complete", attempts=prev_attempts)
                mark_phase_locked(ctx, "3", "complete", note="v3-audit")
                mark_phase_locked(ctx, "5-enrich", "complete", note="v3-audit")
                return True
            if _escalate_fix(ctx, output, "Audit", content_only=True):
                _mark_phase_v3(ctx, state, phase, "complete",
                               attempts=prev_attempts, note="escalation-claude")
                mark_phase_locked(ctx, "3", "complete", note="v3-audit-escalation")
                mark_phase_locked(ctx, "5-enrich", "complete", note="v3-audit-escalation")
                return True
            _mark_phase_v3(ctx, state, phase, "failed",
                           attempts=prev_attempts, note="escalation-failed")
            return False

    if ctx.dry_run:
        log("  Audit: DRY-RUN — would run audit loop")
        return True

    # Auto-fix pass: apply deterministic fixes (euphony, IPA, formatting) before
    # calling any LLM. Zero API cost, instant.
    content_path = ctx.paths["md"]
    auto_fix_total = 0
    if content_path.exists():
        from audit.checks.euphony import auto_fix_euphony
        text = content_path.read_text("utf-8")
        fixed_text, num_fixes = auto_fix_euphony(text, str(content_path))
        if num_fixes > 0:
            content_path.write_text(fixed_text, "utf-8")
            auto_fix_total += num_fixes
            log(f"  Audit: Auto-fixed {num_fixes} euphony violation(s)")

        # IPA normalization (w→ʋ, v→ʋ, affricate tie-bars)
        from lint_ipa import apply_fixes as ipa_apply_fixes
        vocab_path = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
        for target in [content_path, vocab_path, ctx.paths.get("activities")]:
            if target and target.exists():
                t = target.read_text("utf-8")
                fixed_t, n = ipa_apply_fixes(t)
                if n > 0:
                    target.write_text(fixed_t, "utf-8")
                    auto_fix_total += n
                    log(f"  Audit: Auto-fixed {n} IPA issue(s) in {target.name}")

        if auto_fix_total > 0:
            # Re-audit after auto-fix — may already pass
            passed, output = run_verify(content_path, content_only=True)
            if passed:
                log("  Audit: PASS (auto-fix only — zero LLM calls)")
                _mark_phase_v3(ctx, state, phase, "complete", attempts=0, note="auto-fix")
                mark_phase_locked(ctx, "3", "complete", note="v3-audit-autofix")
                mark_phase_locked(ctx, "5-enrich", "complete", note="v3-audit-autofix")
                return True
            log("  Audit: Auto-fix applied but other issues remain — entering LLM fix loop")

    for attempt in range(1, max_iters + 1):
        if attempt == 1:
            log("  Audit: Initial full audit...")
        else:
            log(f"  Audit: Audit after fix {attempt - 1}/{max_iters - 1}...")

        passed, output = run_verify(ctx.paths["md"], content_only=True)

        log_file = ctx.orch_dir / f"pAudit-attempt-{attempt}.log"
        log_file.write_text(output, "utf-8")

        if passed:
            fixes = attempt - 1
            log(f"  Audit: PASS{f' (after {fixes} fix(es))' if fixes else ''}")
            _mark_phase_v3(ctx, state, phase, "complete", attempts=attempt)
            # Also mark v2 prose/enrichment phases so v2 doesn't re-run them
            mark_phase_locked(ctx, "3", "complete", note="v3-audit")
            mark_phase_locked(ctx, "5-enrich", "complete", note="v3-audit")
            return True

        if attempt == 1:
            log("  Audit: FAIL — needs fixes")
        else:
            log(f"  Audit: FAIL (fix {attempt - 1} insufficient)")

        if attempt >= max_iters:
            log(f"  Audit: EXHAUSTED — {max_iters - 1} Gemini fix attempts")
            # Escalate to Claude Opus before giving up
            if _escalate_fix(ctx, output, "Audit", content_only=True):
                _mark_phase_v3(ctx, state, phase, "complete",
                               attempts=attempt, note="escalation-claude")
                mark_phase_locked(ctx, "3", "complete", note="v3-audit-escalation")
                mark_phase_locked(ctx, "5-enrich", "complete", note="v3-audit-escalation")
                return True
            _mark_phase_v3(ctx, state, phase, "failed",
                           attempts=attempt, note="escalation-failed")
            return False

        # Dispatch fix
        fix_num = attempt
        fix_prompt = _build_fix_prompt(ctx, output, content_only=True)
        fix_prompt_file = ctx.orch_dir / f"pAudit-fix{fix_num}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, "utf-8")

        log(f"  Audit: Dispatching fix {fix_num}/{max_iters - 1}...")
        fix_output = _gemini_output_path(ctx.slug, f"pAudit-fix{fix_num}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"v3-{ctx.slug}-pAudit-fix{fix_num}",
            model=ctx.model, allow_write=True, output_file=fix_output,
            timeout=TIMEOUT_FIX,
        )
        if not ok:
            log(f"  Audit: Fix dispatch {fix_num} failed")
            continue

        if fix_output.exists():
            fix_text = fix_output.read_text("utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)

    return False


# ---------------------------------------------------------------------------
# Phase D helpers
# ---------------------------------------------------------------------------

def _quick_review_quality_gate(review_text: str, content_path: Path) -> tuple[bool, str]:
    """Fast pre-save check: reject obviously shallow/fake reviews.

    Catches reviews that have proper delimiters but are trivially thin
    (e.g. from a reformat retry that wrapped a 3-line summary in delimiters).

    Returns (ok, reason).  ok=True means the review is plausibly real.
    """
    from audit.checks.review_validation import _extract_ukrainian_citations
    from audit.checks.review_gaming import _extract_h2_headers

    # --- Citation density ---
    citations = _extract_ukrainian_citations(review_text)
    content_text = content_path.read_text("utf-8") if content_path.exists() else ""
    word_count = len(content_text.split())

    # For content > 1000 words, expect at least 4 citations.
    # For shorter content, scale down (min 2).
    min_citations = max(2, word_count // 600) if word_count > 500 else 2
    if len(citations) < min_citations:
        return False, (
            f"Shallow review: {len(citations)} citation(s), need ≥{min_citations} "
            f"for {word_count}-word content"
        )

    # --- Section coverage ---
    if content_text:
        h2s = _extract_h2_headers(content_text)
        # Filter standard non-content headers
        skip = {'словник', 'vocabulary', 'лексика', 'бібліографія', 'джерела',
                'література', 'використані джерела', 'самооцінювання',
                'self-assessment', 'самоперевірка'}
        h2s = [h for h in h2s if h.strip().lower() not in skip]

        if len(h2s) >= 3:
            review_lower = review_text.lower()
            mentioned = sum(
                1 for h in h2s
                if h.strip().lower() in review_lower
                or (len(h.split(':')[0].strip()) > 3
                    and h.split(':')[0].strip().lower() in review_lower)
            )
            coverage = mentioned / len(h2s)
            if coverage < 0.15:  # Nearly zero coverage = clearly fake
                return False, (
                    f"Shallow review: covers {mentioned}/{len(h2s)} "
                    f"({coverage:.0%}) content sections"
                )

    # --- Minimum length ---
    if len(review_text.split()) < 150:
        return False, f"Shallow review: only {len(review_text.split())} words"

    return True, "OK"


# ---------------------------------------------------------------------------
# Phase D: Cross-Agent Review + Fix (Claude reviews Gemini's work)
# Two-step: D.1 Evidence+Review → D.2 Targeted Repair (if needed)
# ---------------------------------------------------------------------------

def phase_D_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase D: Two-step cross-agent adversarial review via Claude.

    Step 1 (D.1): Evidence collection + review — Claude reads files with tool
        access, produces a structured review with verified citations.
    Step 2 (D.2): Targeted repair — only if Step 1's review + re-audit show
        failures. Claude gets the review + specific audit failures, produces
        FIND/REPLACE fix pairs.

    No blind retry loop — Step 2 gets targeted feedback from Step 1 + audit.
    """
    phase = "D"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  Phase D: SKIP (already complete)")
        return True

    # Pre-D activity validation gate (#606)
    # Activities must exist AND pass audit before Phase D can proceed.
    # Uses --skip-review since the review file doesn't exist yet.
    act_path = ctx.paths.get("activities")
    vocab_path = ctx.paths.get("vocabulary")
    missing = []
    if act_path and not act_path.exists():
        missing.append(f"activities: {act_path.name}")
    if vocab_path and not vocab_path.exists():
        missing.append(f"vocabulary: {vocab_path.name}")
    if missing:
        log(f"  Phase D: BLOCKED — missing sidecar files: {', '.join(missing)}")
        log(f"  Phase D: Run Phase C first or create missing files")
        return False

    if not ctx.dry_run:
        # Auto-fix euphony before pre-D validation — deterministic, zero API cost
        from audit.checks.euphony import auto_fix_euphony
        text = ctx.paths["md"].read_text("utf-8")
        fixed_text, n_euphony = auto_fix_euphony(text, str(ctx.paths["md"]))
        if n_euphony > 0:
            ctx.paths["md"].write_text(fixed_text, "utf-8")
            log(f"  Phase D: Auto-fixed {n_euphony} euphony violation(s) (pre-validation)")

        log("  Phase D: Pre-D activity validation (--skip-review)...")
        pre_d_passed, pre_d_output = run_verify(ctx.paths["md"], skip_review=True)
        if not pre_d_passed:
            pre_d_log = ctx.orch_dir / "pD-pre-validation.log"
            pre_d_log.write_text(pre_d_output, "utf-8")
            log("  Phase D: BLOCKED — activity/vocab audit failed (see pD-pre-validation.log)")
            for line in pre_d_output.strip().split("\n")[-5:]:
                log(f"    {line}")
            return False
        log("  Phase D: Pre-D validation PASS")

    d1_template = PHASES_DIR / "phase-D1-evidence-review.md"
    d2_template = PHASES_DIR / "phase-D2-repair.md"
    if not d1_template.exists():
        log(f"  Phase D: ERROR — D1 template not found: {d1_template}")
        return False
    if not d2_template.exists():
        log(f"  Phase D: ERROR — D2 template not found: {d2_template}")
        return False

    if ctx.dry_run:
        log("  Phase D: DRY-RUN — would dispatch D1 (evidence+review) + D2 (repair)")
        return True

    claude_model_D = getattr(ctx, "claude_model_D", CLAUDE_MODEL_REVIEW)

    # -----------------------------------------------------------------------
    # Step 1: Evidence Collection + Review
    # -----------------------------------------------------------------------
    log(f"  Phase D.1: Computing audit metrics...")
    metrics = _compute_audit_metrics(ctx)
    sections = _extract_h2_sections(ctx.paths["md"])

    prompt_file = ctx.orch_dir / "phase-D-prompt-1.md"
    if not fill_template(d1_template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    # Inject computed metrics and H2 sections into the prompt
    prompt_text = prompt_file.read_text("utf-8")
    prompt_text = _inject_metrics_into_prompt(prompt_text, metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", sections)
    prompt_file.write_text(prompt_text, "utf-8")

    log(f"  Phase D.1: Dispatching evidence+review via Claude ({claude_model_D})...")
    log(f"    Metrics: {metrics.get('COMPUTED_WORD_COUNT', '?')}w / "
        f"{metrics.get('COMPUTED_WORD_TARGET', '?')}w, "
        f"{metrics.get('COMPUTED_ACTIVITY_COUNT', '?')} activities, "
        f"immersion {metrics.get('COMPUTED_IMMERSION_PERCENT', '?')}%")

    ok, raw_output = _dispatch_claude_phase(
        prompt_file, "Phase D.1",
        model=claude_model_D, timeout=TIMEOUT_REVIEW,
        allow_tools=["Read", "Grep", "Glob"],
    )
    if not ok:
        log("  Phase D.1: Dispatch FAILED")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-dispatch-failed")
        return False

    # Extract review
    review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if not review_text:
        log("  Phase D.1: WARNING — no REVIEW delimiters in output (retrying full D.1)")
        # Save raw output for debugging
        (ctx.orch_dir / "phase-D1-raw-output.md").write_text(raw_output, "utf-8")

        # Retry once: re-run the full D.1 prompt (not just reformat)
        ok2, raw2 = _dispatch_claude_phase(
            prompt_file, "Phase D.1 (retry)",
            model=claude_model_D, timeout=TIMEOUT_REVIEW,
            allow_tools=["Read", "Grep", "Glob"],
        )
        if ok2:
            review_text = _extract_delimiter(raw2, "===REVIEW_START===", "===REVIEW_END===")

        if not review_text:
            log("  Phase D.1: Full retry also failed — no delimiters")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-no-review")
            return False

        log("  Phase D.1: Full retry succeeded — delimiters found")

    # Pre-save quality gate: reject obviously shallow/fake reviews
    qg_ok, qg_reason = _quick_review_quality_gate(review_text, ctx.paths["md"])
    if not qg_ok:
        log(f"  Phase D.1: REJECTED — {qg_reason}")
        (ctx.orch_dir / "phase-D1-rejected-review.md").write_text(review_text, "utf-8")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1,
                       note=f"d1-shallow-review")
        return False

    # Inject Reviewed-By metadata if Claude forgot it
    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** {claude_model_D}\n\n{review_text}"

    # Save review with content hash for staleness detection (#618)
    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "phase-D-review-1.md").write_text(review_text, "utf-8")
    log(f"  Phase D.1: Review saved → {ctx.paths['review'].name}")

    # Auto-fix euphony before auditing — deterministic, zero API cost
    from audit.checks.euphony import auto_fix_euphony
    text = ctx.paths["md"].read_text("utf-8")
    fixed_text, n_euphony = auto_fix_euphony(text, str(ctx.paths["md"]))
    if n_euphony > 0:
        ctx.paths["md"].write_text(fixed_text, "utf-8")
        log(f"  Phase D.1: Auto-fixed {n_euphony} euphony violation(s)")

    # Run full audit to check review quality + content
    log("  Phase D.1: Running audit after review...")
    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
    audit_log = ctx.orch_dir / "pD-audit-1.log"
    audit_log.write_text(audit_out, "utf-8")

    # Check review verdict: even if audit passes, the review may flag issues
    # that require D.2 repair (calques, LLM fingerprints, activity errors, etc.)
    review_says_fail = False
    if review_text:
        import re as _re
        _status_m = _re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
        _score_m = _re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
        if _status_m and _status_m.group(1) == "FAIL":
            review_says_fail = True
            log(f"  Phase D.1: Review verdict: FAIL")
        elif _score_m and float(_score_m.group(1)) < 9.0:
            review_says_fail = True
            log(f"  Phase D.1: Review score {_score_m.group(1)}/10 < 9.0 — needs repair")

    if passed and not review_says_fail:
        log("  Phase D: PASS (D.1 review sufficient — no repair needed)")
        _mark_phase_v3(ctx, state, phase, "complete", attempts=1, note="d1-only")
        mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
        return True

    if passed and review_says_fail:
        log("  Phase D.1: Audit PASSED but review flags issues — proceeding to D.2 for repair")

    # Citation failure detection (#615): if the review itself is bad (fabricated
    # citations), don't proceed to D.2 content repair — that can't fix a bad review.
    # Instead, delete the review and mark as failed for retry.
    # Only match CRITICAL violations (❌ prefix) — warning-severity cases are inconclusive.
    _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
    if any(f"\u274c [{tag}]" in audit_out for tag in _CITATION_FAILURES):
        log("  Phase D.1: REVIEW QUALITY FAILURE — fabricated/unverified citations detected")
        log("  Phase D.1: Deleting bad review (D.2 cannot fix a bad review)")
        if ctx.paths["review"].exists():
            ctx.paths["review"].unlink()
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1,
                       note="d1-citation-failure")
        return False

    # -----------------------------------------------------------------------
    # Pre-D.2 deterministic fix pass (#623): try all zero-cost auto-fixes
    # before deciding whether to send to LLM or rebuild. A single YAML error
    # can cascade into 5-10 audit failures that look "diffuse" but are
    # actually one deterministic fix away from passing.
    # -----------------------------------------------------------------------
    auto_fix_count = _run_deterministic_fixes(ctx)
    if auto_fix_count > 0:
        log(f"  Phase D.2: Pre-triage auto-fix applied {auto_fix_count} fix(es) — re-auditing...")
        passed_after_autofix, audit_out_after = run_verify(ctx.paths["md"], content_only=False)
        if passed_after_autofix and not review_says_fail:
            log("  Phase D: PASS (deterministic fixes resolved all issues — zero LLM cost)")
            _mark_phase_v3(ctx, state, phase, "complete", attempts=1, note="d1-plus-autofix")
            mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
            return True
        # Use the fresh audit output for triage decisions
        audit_out = audit_out_after

    # Pre-D.2 triage: skip D.2 if all REMAINING issues are diffuse (not fixable
    # by FIND/REPLACE). Only runs AFTER deterministic fixes have been tried.
    if _all_issues_diffuse(audit_out, review_text):
        log("  Phase D.2: SKIPPED — all remaining issues are diffuse (needs rebuild, not repair)")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1,
                       note="needs-rebuild-diffuse-issues")
        return False

    # -----------------------------------------------------------------------
    # Step 2: Targeted Repair (only if Step 1 didn't pass audit)
    # -----------------------------------------------------------------------
    log("  Phase D.2: Audit failed after review — dispatching targeted repair...")

    # Extract specific audit failures for the repair prompt
    failures = _extract_audit_failures(audit_out)

    prompt_file2 = ctx.orch_dir / "phase-D-prompt-2.md"
    if not fill_template(d2_template, ctx.orch_dir / "placeholders.yaml", prompt_file2):
        return False

    # Inject review text and audit failures into D2 prompt
    prompt2_text = prompt_file2.read_text("utf-8")
    prompt2_text = prompt2_text.replace("{INJECTED_REVIEW_TEXT}", review_text)
    prompt2_text = prompt2_text.replace("{INJECTED_AUDIT_FAILURES}", failures)
    prompt_file2.write_text(prompt2_text, "utf-8")

    ok2, raw_output2 = _dispatch_claude_phase(
        prompt_file2, "Phase D.2",
        model=claude_model_D, timeout=TIMEOUT_FIX,
        allow_tools=["Read", "Grep", "Glob"],
    )
    if not ok2:
        log("  Phase D.2: Dispatch FAILED")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=2, note="d2-dispatch-failed")
        return False

    # Apply fixes if present, with diff-size blocker (#623)
    if "===SECTION_FIX_START===" in raw_output2:
        # Snapshot content before fixes for diff-size check
        content_before = ctx.paths["md"].read_text("utf-8")
        act_before: str | None = None
        if ctx.paths.get("activities") and ctx.paths["activities"].exists():
            act_before = ctx.paths["activities"].read_text("utf-8")

        _apply_section_fixes(ctx.paths["md"], raw_output2)
        if ctx.paths.get("activities"):
            _apply_section_fixes(ctx.paths["activities"], raw_output2)

        # Diff-size blocker: count FIND/REPLACE pairs vs actual changed lines.
        # If changes exceed 2× the fix pair count, the repair went beyond scope.
        fix_pair_count = raw_output2.count("FIND:") if "FIND:" in raw_output2 else 1
        content_after = ctx.paths["md"].read_text("utf-8")
        act_after: str | None = None
        if ctx.paths.get("activities") and ctx.paths["activities"].exists():
            act_after = ctx.paths["activities"].read_text("utf-8")

        changed_lines = _count_diff_lines(content_before, content_after)
        if act_before is not None and act_after is not None:
            changed_lines += _count_diff_lines(act_before, act_after)
        # Each FIND/REPLACE pair can legitimately change a multi-line paragraph.
        # Allow ~15 lines per pair (6-line find + 6-line replace + context).
        max_allowed = max(fix_pair_count * 15, 30)  # At least 30 lines always OK

        if changed_lines > max_allowed:
            log(f"  Phase D.2: REJECTED — repair changed {changed_lines} lines "
                f"(max {max_allowed} for {fix_pair_count} fix pairs)")
            log(f"  Phase D.2: Reverting content to pre-fix state")
            ctx.paths["md"].write_text(content_before, "utf-8")
            if act_before is not None and ctx.paths.get("activities"):
                ctx.paths["activities"].write_text(act_before, "utf-8")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=2,
                           note="d2-diff-too-large")
            return False

        log(f"  Phase D.2: Section fixes applied ({changed_lines} lines changed, "
            f"{fix_pair_count} fix pairs)")
    else:
        log("  Phase D.2: WARNING — no SECTION_FIX delimiters in output")
        (ctx.orch_dir / "phase-D2-raw-output.md").write_text(raw_output2, "utf-8")

    # Auto-fix euphony before final audit
    text2 = ctx.paths["md"].read_text("utf-8")
    fixed_text2, n_euphony2 = auto_fix_euphony(text2, str(ctx.paths["md"]))
    if n_euphony2 > 0:
        ctx.paths["md"].write_text(fixed_text2, "utf-8")
        log(f"  Phase D.2: Auto-fixed {n_euphony2} euphony violation(s)")

    # Final re-audit
    log("  Phase D.2: Running final audit...")
    passed, audit_out2 = run_verify(ctx.paths["md"], content_only=False)
    audit_log2 = ctx.orch_dir / "pD-audit-2.log"
    audit_log2.write_text(audit_out2, "utf-8")

    if passed:
        log("  Phase D: PASS (after D.1 review + D.2 repair)")
        _mark_phase_v3(ctx, state, phase, "complete", attempts=2)
        mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
        return True

    log("  Phase D: EXHAUSTED — D.1 review + D.2 repair both insufficient")
    log("  Phase D: Module marked as NEEDS-REBUILD (use --rebuild to regenerate)")
    _mark_phase_v3(ctx, state, phase, "failed", attempts=2, note="needs-rebuild")
    return False


# ---------------------------------------------------------------------------
# Phase E: MDX (always last — delegates to v2)
# ---------------------------------------------------------------------------

def phase_E_v3(ctx: ModuleContext) -> bool:
    """Phase E: MDX generation + lint. Delegates to v2's phase_8_mdx."""
    return phase_E_v3_delegate(ctx)


# ---------------------------------------------------------------------------
# Phase F: Final Review (optional, agent-selectable)
# ---------------------------------------------------------------------------

def phase_F_v3(ctx: ModuleContext) -> bool:
    """Phase F: Final QA gate. Agent-selectable via --final-review-agent.

    Default: Claude (delegates to v2 phase_9_final_review).
    With --final-review-agent gemini: dispatches same prompt via Gemini.
    """
    agent = getattr(ctx, "final_review_agent", "claude")
    if agent == "gemini":
        return _phase_F_gemini(ctx)
    return phase_F_v3_delegate(ctx)


def _phase_F_gemini(ctx: ModuleContext) -> bool:
    """Phase F via Gemini: build the final QA prompt and dispatch to Gemini.

    Uses the same Phase D review-fix template but in read-only review mode.
    This enables true cross-agent Phase F: if Phase D is Claude, Phase F can be Gemini.
    """
    if not getattr(ctx, "final_review", False):
        return True

    phase = "9-final-review"
    if is_phase_complete(ctx, phase):
        log("  Phase F (Gemini): SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Phase F: DRY-RUN — would call Gemini for final review")
        return True

    # Use the Phase D review template (same review format)
    template = PHASES_DIR / "phase-D-review-fix.md"
    if not template.exists():
        log(f"  Phase F (Gemini): ERROR — template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "phase-F-gemini-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    log(f"  Phase F (Gemini): Dispatching final review via Gemini...")
    output_file = _gemini_output_path(ctx.slug, "pF")
    ok, raw_output = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"v3-{ctx.slug}-pF",
        model=ctx.model, stdout_only=True, output_file=output_file,
        timeout=TIMEOUT_REVIEW,
    )
    if not ok:
        log("  Phase F (Gemini): Dispatch failed")
        return False

    # Extract and save review with content hash (#618)
    review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if review_text:
        final_review_path = ctx.paths["review"].parent / f"{ctx.slug}-final-review.md"
        write_review_with_hash(final_review_path, review_text, ctx.paths["md"])
        (ctx.orch_dir / "phase-9-final-review.md").write_text(review_text, "utf-8")
        log(f"  Phase F (Gemini): Review saved → {final_review_path.name}")

    # Apply fixes if present
    if "===SECTION_FIX_START===" in raw_output:
        _apply_section_fixes(ctx.paths["md"], raw_output)
        if ctx.paths.get("activities"):
            _apply_section_fixes(ctx.paths["activities"], raw_output)
        log("  Phase F (Gemini): Section fixes applied")

    # Extract verdict — Phase D template uses **PASS**/**FAIL** under "## Verdict"
    verdict = "NEEDS_WORK"
    if re.search(r"\*\*PASS\*\*", raw_output):
        verdict = "APPROVE"
    elif re.search(r"\*\*FAIL\*\*", raw_output):
        verdict = "REJECT"
    log(f"  Phase F (Gemini): Verdict → {verdict}")

    if verdict == "REJECT":
        mark_phase_locked(ctx, phase, "failed", verdict=verdict)
        return False

    mark_phase_locked(ctx, phase, "complete", verdict=verdict)
    return True


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

PHASE_FUNCTIONS_V3: dict[str, Any] = {
    "A":     phase_A_v3,        # takes (ctx, state)
    "B":     phase_B_v3,        # takes (ctx, state, use_track_context)
    "C":     phase_C_v3,        # takes (ctx, state, use_track_context)
    "audit": phase_audit_v3,    # takes (ctx, state)
    "D":     phase_D_v3,        # takes (ctx, state)
    "E":     phase_E_v3,        # takes (ctx) — delegates to v2
    "F":     phase_F_v3,        # takes (ctx) — delegates to v2
}


def run_pipeline_v3(ctx: ModuleContext, research_only: bool = False,
                    no_track_context: bool = False) -> bool:
    """Execute the v3 optimised pipeline."""
    state = _load_state_v3(ctx)
    use_tc = not no_track_context

    # Layer 3: One-time v2→v3 state migration (skipped on --force-phase and --rebuild)
    if not ctx.force_phase and not getattr(ctx, "refresh", False):
        _migrate_v2_state_to_v3(ctx, state)

    # Revalidate audit+D against current rules (catches stale state from old runs)
    _validate_audit_state(ctx, state)

    log(f"\nPipeline v3: 4-call optimised — {len(PHASE_SEQUENCE_V3)} phases")
    if ctx.dry_run:
        log("  (DRY-RUN — no Gemini dispatches)")
    if no_track_context:
        log("  (--no-track-context — skipping track context injection)")
    log("")

    # Print phase plan
    for phase_id in PHASE_SEQUENCE_V3:
        label = PHASE_LABELS_V3.get(phase_id, phase_id)
        skip_note = " [DONE]" if _is_phase_v3_complete(ctx, phase_id, state) else ""
        log(f"  Phase {phase_id}: {label}{skip_note}")
    if ctx.final_review:
        phase_f_note = " [DONE]" if _is_phase_v3_complete(ctx, "F", state) else ""
        log(f"  Phase F: {PHASE_LABELS_V3['F']}{phase_f_note}")
    log(f"  Phase E: {PHASE_LABELS_V3['E']} (always last)")
    log("")

    # --force-phase: single phase only
    force_phase = ctx.force_phase
    if force_phase:
        # Case-insensitive lookup: "audit" stays "audit", "A"/"a" → "A"
        _phase_key_map = {k.upper(): k for k in PHASE_FUNCTIONS_V3}
        force_key = _phase_key_map.get(str(force_phase).upper())
        if force_key is None:
            log(f"  ERROR: Unknown v3 phase '{force_phase}'. Valid: {', '.join(PHASE_SEQUENCE_V3 + ['E', 'F'])}")
            return False
        log(f"  --force-phase {force_key}: running only this phase")
        # For state-aware phases, clear the v3 state first
        if force_key in _V3_PHASE_STATE_IDS:
            phases = state.setdefault("phases", {})
            for sid in _V3_PHASE_STATE_IDS[force_key]:
                phases.pop(sid, None)
            _save_state_v3(ctx, state)
        func = PHASE_FUNCTIONS_V3[force_key]
        return _call_phase_func(func, force_key, ctx, state, use_tc)

    # --restart-from
    restart_from = getattr(ctx, "restart_from", None)
    if restart_from:
        restart_upper = str(restart_from).upper()
        if restart_upper not in PHASE_SEQUENCE_V3:
            log(f"  ERROR: Unknown v3 phase '{restart_upper}'. Valid: {', '.join(PHASE_SEQUENCE_V3)}")
            return False
        idx = PHASE_SEQUENCE_V3.index(restart_upper)
        remaining = PHASE_SEQUENCE_V3[idx:]
        # Clear state for restarted phases
        phases = state.setdefault("phases", {})
        for pid in remaining:
            for sid in _V3_PHASE_STATE_IDS.get(pid, []):
                phases.pop(sid, None)
        _save_state_v3(ctx, state)
        log(f"  --restart-from {restart_upper}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            if not _call_phase_func(PHASE_FUNCTIONS_V3[phase_id], phase_id, ctx, state, use_tc):
                log(f"\n  PIPELINE STOPPED at phase {phase_id}")
                return False
        # Don't fall through to MDX here — handled below
        return _run_final_phases(ctx, state)

    # Full pipeline
    # MDX (Phase E) is always deferred to after all other phases including F
    for phase_id in PHASE_SEQUENCE_V3:
        func = PHASE_FUNCTIONS_V3[phase_id]
        if not _call_phase_func(func, phase_id, ctx, state, use_tc):
            log(f"\n  PIPELINE STOPPED at phase {phase_id}")
            return False

        # --research-only: stop after Phase A
        if research_only and phase_id == "A":
            log("\n  --research-only: Phase A complete, stopping")
            return True

    return _run_final_phases(ctx, state)


def _run_final_phases(ctx: ModuleContext, state: dict) -> bool:
    """Run Phase F (optional) then Phase E (always). Returns overall success."""
    # Phase F: Final Review (optional, agent-selectable)
    if getattr(ctx, "final_review", False):
        # Check if Phase F already completed (skip → no post-F repair needed)
        phase_f_already_done = _is_phase_v3_complete(ctx, "F", state) or is_phase_complete(ctx, "9-final-review")

        log(f"\n  Phase F: {PHASE_LABELS_V3['F']}")
        if not phase_F_v3(ctx):
            log("\n  PIPELINE STOPPED at phase F (REJECT verdict)")
            return False

        # Post-F audit fix loop: Only needed when Phase F actually RAN and may
        # have applied fixes that break compliance. Skip if F was already done.
        if phase_f_already_done:
            log("  Phase F: Skipped post-fix audit (Phase F was already complete)")
        else:
            # Auto-fix euphony before checking — Phase F review may have introduced violations
            from audit.checks.euphony import auto_fix_euphony
            text = ctx.paths["md"].read_text("utf-8")
            fixed_text, n_auto = auto_fix_euphony(text, str(ctx.paths["md"]))
            if n_auto > 0:
                ctx.paths["md"].write_text(fixed_text, "utf-8")
                log(f"  Phase F: Auto-fixed {n_auto} euphony violation(s)")

            passed, output = run_verify(ctx.paths["md"], content_only=False)
            if not passed:
                log("  Phase F: Post-fix audit FAIL — running repair loop (max 2 iters)")
                for fix_iter in range(1, 3):
                    fix_prompt = _build_fix_prompt(ctx, output, content_only=False)
                    fix_file = ctx.orch_dir / f"phase-F-repair{fix_iter}-prompt.md"
                    fix_file.write_text(fix_prompt, "utf-8")
                    log(f"  Phase F: Dispatching repair fix {fix_iter}/2...")
                    fix_output = _gemini_output_path(ctx.slug, f"phase-F-repair{fix_iter}")
                    ok, _ = dispatch_gemini(
                        _dispatch_prompt(ctx, fix_file),
                        task_id=f"v3-{ctx.slug}-F-repair{fix_iter}",
                        model=ctx.model, allow_write=True, output_file=fix_output,
                        timeout=TIMEOUT_FIX,
                    )
                    if not ok:
                        log(f"  Phase F: Repair {fix_iter} dispatch failed")
                        break
                    passed, output = run_verify(ctx.paths["md"], content_only=False)
                    if passed:
                        log(f"  Phase F: Repair PASS (after {fix_iter} fix(es))")
                        break
                    log(f"  Phase F: Repair {fix_iter} insufficient")
                if not passed:
                    # Escalate to Claude Opus (Gemini repair exhausted)
                    if _escalate_fix(ctx, output, "Phase F repair", content_only=False):
                        passed = True
                    else:
                        log("  Phase F: Repair loop EXHAUSTED — proceeding to MDX anyway")

    # Phase E: MDX — always last, always regenerates
    log(f"\n  Phase E: {PHASE_LABELS_V3['E']} (post-review)")
    # Reset v2 MDX state so it regenerates even when already complete
    ctx.state.get("phases", {}).pop("8", None)
    v1.save_state(ctx)
    return phase_E_v3(ctx)


def _call_phase_func(func: Any, phase_id: str, ctx: ModuleContext,
                     state: dict, use_tc: bool) -> bool:
    """Call a v3 phase function with the right signature."""
    if phase_id in ("B", "C"):
        return func(ctx, state, use_tc)
    elif phase_id in ("E", "F"):
        return func(ctx)
    else:
        return func(ctx, state)


# ---------------------------------------------------------------------------
# Preflight v3 — wraps v2's preflight + patches state file + adds v3 attrs
# ---------------------------------------------------------------------------

def preflight_v3(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, set v3-specific attributes."""
    ctx = preflight_v2(args)

    # Override mode
    ctx.mode = "v3"  # type: ignore[attr-defined]
    ctx.state["mode"] = "v3"

    # v3-specific flags
    ctx.no_track_context = getattr(args, "no_track_context", False)  # type: ignore[attr-defined]
    ctx.research_only = getattr(args, "research_only", False)  # type: ignore[attr-defined]

    # --use-claude: set of phase IDs to dispatch via Claude CLI instead of Gemini
    use_claude_str = getattr(args, "use_claude", "") or ""
    ctx.use_claude = set(use_claude_str.replace(",", " ").upper().split()) if use_claude_str else set()  # type: ignore[attr-defined]

    # Per-phase Claude model — seminar + pro tracks default to Opus, core to Sonnet
    _is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track in PRO_TRACKS
    _default_gen_model = "claude-opus-4-6" if _is_seminar else CLAUDE_MODEL_ACTIVITIES
    ctx.claude_model_A = getattr(args, "claude_model_A", None) or _default_gen_model   # type: ignore[attr-defined]
    ctx.claude_model_C = getattr(args, "claude_model_C", None) or _default_gen_model   # type: ignore[attr-defined]
    ctx.claude_model_D = getattr(args, "claude_model_D", None) or CLAUDE_MODEL_REVIEW  # type: ignore[attr-defined]
    ctx.claude_model_F = getattr(args, "claude_model_F", None) or "claude-opus-4-6"    # type: ignore[attr-defined]
    ctx.final_review_agent = getattr(args, "final_review_agent", "claude")             # type: ignore[attr-defined]

    # --gemini-model: override Gemini model for all phases
    gemini_model_override = getattr(args, "gemini_model", None)
    if gemini_model_override:
        ctx.model = gemini_model_override  # type: ignore[attr-defined]

    # --rebuild forces Phase B to regenerate even if content file exists
    if getattr(args, "rebuild", False):
        ctx.refresh = True  # type: ignore[attr-defined]

    # Copy restart_from if not already set by v2 preflight
    if not hasattr(ctx, "restart_from"):
        ctx.restart_from = getattr(args, "restart_from", None)  # type: ignore[attr-defined]

    # --max-fix N: override audit fix iterations
    ctx.max_fix = getattr(args, "max_fix", None)  # type: ignore[attr-defined]

    return ctx


# ---------------------------------------------------------------------------
# Layer 1: Batch skip helpers
# ---------------------------------------------------------------------------

def _is_final_review_done(paths: dict[str, Path]) -> bool:
    """Check if final review (Phase F / v2 phase 9) is done in either state file."""
    import json
    orch_dir = paths.get("orchestration")
    if not orch_dir:
        # Derive from md path: .../b1/slug.md → .../b1/orchestration/slug/
        md = paths.get("md")
        if md:
            orch_dir = md.parent / "orchestration" / md.stem
    if not orch_dir or not Path(orch_dir).is_dir():
        return False

    orch = Path(orch_dir)

    # Check v3 state
    v3_state = orch / "state-v3.json"
    if v3_state.exists():
        try:
            data = json.loads(v3_state.read_text("utf-8"))
            info = data.get("phases", {}).get("9-final-review", {})
            if info.get("status") == "complete":
                return True
        except Exception:
            pass

    # Check v2 state
    v2_state = orch / "state.json"
    if v2_state.exists():
        try:
            data = json.loads(v2_state.read_text("utf-8"))
            info = data.get("phases", {}).get("9-final-review", {})
            if info.get("status") == "complete":
                return True
        except Exception:
            pass

    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="E2E Module Builder v3 — 4-call optimised pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s a1 12                           # Full E2E (4 calls)
              %(prog)s b2-hist 5                       # Seminar track
              %(prog)s a1 --all                        # Build entire track
              %(prog)s a1 --range 1-20                 # Build range
              %(prog)s b2-hist --all --research-only   # Pre-seed all research
              %(prog)s a1 12 --rebuild                 # Nuke v3 state, restart
              %(prog)s a1 12 --dry-run                 # Show plan, no dispatches
              %(prog)s a1 12 --verify                  # Just audit
              %(prog)s a1 12 --no-track-context        # Skip track context injection
              %(prog)s a1 12 --force-phase B           # Re-run Phase B only
              %(prog)s a1 12 --force-phase D           # Re-run review+fix only
              %(prog)s a1 12 --max-fix 7                # Override audit fix iterations
              %(prog)s a1 12 --final-review            # + Claude QA gate (Phase F)
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., c1-bio, b2-hist, ...)")
    parser.add_argument("num", type=int, nargs="?", default=None,
                        help="1-indexed module number (optional with --all or --range)")

    parser.add_argument("--all", action="store_true", dest="build_all",
                        help="Build all modules in the track sequentially")
    parser.add_argument("--range", type=str, default=None, dest="build_range",
                        help="Build a range of modules (e.g. 1-20)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke v3 state and rebuild from Phase A")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a single v3 phase (A/B/C/audit/D/E/F)")
    parser.add_argument("--restart-from", type=str, default=None,
                        help="Restart from a v3 phase (A/B/C/audit/D)")
    parser.add_argument("--force-research", action="store_true",
                        help="Force fresh Phase A research even if research file exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching to Gemini")
    parser.add_argument("--refresh", action="store_true",
                        help="Regenerate prose from updated research")
    parser.add_argument("--verify", action="store_true",
                        help="Just run audit, print PASS/FAIL, exit")
    parser.add_argument("--no-track-context", action="store_true", dest="no_track_context",
                        help="Skip track context injection in Phases B and C")
    parser.add_argument("--research-only", action="store_true", dest="research_only",
                        help="Run Phase A only (pre-seed research for all modules)")
    parser.add_argument("--final-review", action="store_true", dest="final_review",
                        help="Run Phase F: final QA gate after Phase D (optional)")
    parser.add_argument("--final-review-agent", type=str, default="claude",
                        choices=["claude", "gemini"], dest="final_review_agent",
                        help="Agent for Phase F final review (default: claude)")
    parser.add_argument("--use-claude", type=str, default="", dest="use_claude",
                        help="Phases to run via Claude instead of Gemini (e.g. 'A', 'C', 'A C'). "
                             "A=research, C=activities. Phase D always uses Claude (cross-agent).")
    parser.add_argument("--gemini-model", type=str, default=None, dest="gemini_model",
                        help="Override Gemini model for all phases (default: from batch_gemini_config)")
    parser.add_argument("--claude-model-A", type=str, default=None, dest="claude_model_A",
                        help=f"Claude model for Phase A/research (default: sonnet for core, opus for seminar)")
    parser.add_argument("--claude-model-C", type=str, default=None, dest="claude_model_C",
                        help=f"Claude model for Phase C/activities (default: sonnet for core, opus for seminar)")
    parser.add_argument("--claude-model-D", type=str, default=None, dest="claude_model_D",
                        help="Claude model for Phase D/review (default: claude-opus-4-6)")
    parser.add_argument("--claude-model-F", type=str, default=None, dest="claude_model_F",
                        help="Claude model for Phase F/final-review (default: claude-opus-4-6)")
    parser.add_argument("--max-fix", type=int, default=None, dest="max_fix",
                        help="Override max audit fix iterations (default: 3 core, 5 seminar)")

    args = parser.parse_args()

    # Validate: need num, --all, or --range
    if args.num is None and not args.build_all and not args.build_range:
        parser.error("Either provide a module number, --all, or --range")

    # --all / --range: batch mode
    if args.build_all or args.build_range:
        idx = get_module_index(args.track)
        total = idx["total"]

        if args.build_all:
            nums = list(range(1, total + 1))
            print(f"Building ALL {total} modules in {args.track} (v3)", flush=True)
        else:
            m = re.match(r"^(\d+)-(\d+)$", args.build_range)
            if not m:
                parser.error(f"Invalid range: {args.build_range!r} (expected N-M)")
            start, end = int(m.group(1)), int(m.group(2))
            if start < 1 or end > total or start > end:
                parser.error(f"Range {start}-{end} out of bounds (track has {total} modules)")
            nums = list(range(start, end + 1))
            print(f"Building {args.track} modules {start}-{end} ({len(nums)} modules, v3)", flush=True)

        passed_list, failed_list, skipped_list = [], [], []
        t0_batch = time.time()

        for i, n in enumerate(nums, 1):
            slug = slug_for_num(args.track, n)
            print(f"\n{'='*70}", flush=True)
            print(f"[{i}/{len(nums)}] {args.track} #{n} — {slug}", flush=True)
            print(f"{'='*70}", flush=True)

            # Layer 1: Tiered batch skip — avoid running full audit on v2-built modules
            # that already pass. Even if they fall through, Layer 2 guards prevent
            # Phase A/B/C from overwriting existing artifacts.
            if not args.rebuild and not args.force_phase:
                try:
                    paths = get_module_paths(args.track, slug)
                    if paths["md"].exists():
                        # Tier 1: Full audit pass — cheapest check
                        full_passed, _ = run_verify(paths["md"], content_only=False)
                        if full_passed:
                            want_final_review = getattr(args, "final_review", False)
                            if not want_final_review:
                                # No --final-review → skip entirely
                                print(f"  SKIP: already passing full audit", flush=True)
                                skipped_list.append((n, slug))
                                continue
                            elif _is_final_review_done(paths):
                                # --final-review requested but already done → skip
                                print(f"  SKIP: passing audit + final review done", flush=True)
                                skipped_list.append((n, slug))
                                continue
                            else:
                                # --final-review requested, not done yet → fall through
                                # Layer 2 guards protect A/B/C; pipeline runs only F+E
                                print(f"  PARTIAL: audit passes, needs final review", flush=True)
                        else:
                            # Full audit fails — check content+activities (skip review)
                            sr_passed, _ = run_verify(paths["md"], skip_review=True)
                            if sr_passed:
                                # Content+activities OK, needs review only
                                # Fall through — Layer 2 guards protect A/B/C
                                print(f"  PARTIAL: content+activities pass, needs review", flush=True)
                            else:
                                co_passed, _ = run_verify(paths["md"], content_only=True)
                                if co_passed:
                                    # Content OK, but activities/review gates fail
                                    # Fall through — Layer 2 guards protect A/B/C
                                    print(f"  PARTIAL: content passes, needs activities/review", flush=True)
                                # else: all fail → full pipeline (no print, just fall through)
                except Exception:
                    pass

            single_args = argparse.Namespace(
                track=args.track, num=n,
                build_all=False, build_range=None,
                rebuild=args.rebuild, force_phase=args.force_phase,
                restart_from=getattr(args, "restart_from", None),
                force_research=getattr(args, "force_research", False),
                dry_run=args.dry_run,
                refresh=getattr(args, "refresh", False), verify=False,
                no_track_context=args.no_track_context,
                research_only=args.research_only,
                final_review=getattr(args, "final_review", False),
                final_review_agent=getattr(args, "final_review_agent", "claude"),
                use_claude=getattr(args, "use_claude", ""),
                claude_model_A=getattr(args, "claude_model_A", None),
                claude_model_C=getattr(args, "claude_model_C", None),
                claude_model_D=getattr(args, "claude_model_D", None),
                claude_model_F=getattr(args, "claude_model_F", None),
                max_fix=getattr(args, "max_fix", None),
            )
            rc = _run_single_module(single_args)
            if rc == 0:
                passed_list.append((n, slug))
            else:
                failed_list.append((n, slug))
                print("  FAILED — continuing to next module", flush=True)

        elapsed = time.time() - t0_batch
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        print(f"\n{'='*70}", flush=True)
        print(f"BATCH COMPLETE — {args.track} v3 [{elapsed_str}]", flush=True)
        print(f"  Passed:  {len(passed_list)}", flush=True)
        print(f"  Failed:  {len(failed_list)}", flush=True)
        print(f"  Skipped: {len(skipped_list)} (already passing)", flush=True)
        if failed_list:
            print("  Failed modules:", flush=True)
            for n, slug in failed_list:
                print(f"    #{n} {slug}", flush=True)
        print(f"{'='*70}", flush=True)
        return 1 if failed_list else 0

    # --verify mode
    if args.verify:
        try:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            content_path = paths["md"]
            if not content_path.exists():
                print(f"FAIL: Content file not found: {content_path}", flush=True)
                return 1
            passed, output = run_verify(content_path, content_only=False)
            if passed:
                print(f"PASS: {slug} (fully complete)", flush=True)
                return 0
            else:
                # Check intermediate levels: content+activities or content-only
                passed_sr, _ = run_verify(content_path, skip_review=True)
                if passed_sr:
                    print(f"CONTENT+ACTIVITIES: {slug} (needs review)", flush=True)
                    return 0
                passed_co, _ = run_verify(content_path, content_only=True)
                if passed_co:
                    print(f"CONTENT-ONLY: {slug} (activities not validated)", flush=True)
                    return 0
                print(f"FAIL: {slug}", flush=True)
                for line in output.strip().split("\n")[-20:]:
                    print(f"  {line}", flush=True)
                return 1
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            return 1

    return _run_single_module(args)


def _run_single_module(args: argparse.Namespace) -> int:
    """Run the v3 pipeline for a single module. Returns 0 on success, 1 on failure."""
    from build_module import _init_log
    try:
        # --rebuild: nuke v3 state
        if args.rebuild:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            orch_dir = (paths.get("orchestration")
                        or CURRICULUM_DIR / "l2-uk-en" / args.track / "orchestration" / slug)
            state_v3 = orch_dir / "state-v3.json"
            if state_v3.exists():
                state_v3.unlink()
                print("  --rebuild: cleared state-v3.json", flush=True)

        ctx = preflight_v3(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        t0 = time.time()
        ok = run_pipeline_v3(
            ctx,
            research_only=getattr(ctx, "research_only", False),
            no_track_context=getattr(ctx, "no_track_context", False),
        )
        elapsed = time.time() - t0
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        write_completion_report_v2(ctx, ok)

        if ok:
            if ctx.dry_run:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in v3 mode [{elapsed_str}]")
            elif ctx.force_phase:
                log(f"\nVERDICT: PASS — phase {ctx.force_phase} complete [{elapsed_str}]")
            elif getattr(ctx, "research_only", False):
                log(f"\nVERDICT: PASS — research complete (v3) [{elapsed_str}]")
            else:
                passed, output = run_verify(ctx.paths["md"], content_only=False)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} fully complete (v3) [{elapsed_str}]")
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
