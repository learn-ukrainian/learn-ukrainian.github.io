#!/usr/bin/env python3
"""E2E Module Builder — Pipeline v4 (named phases) + v3 (legacy).

Pipeline v4 (default):
    research → discover → content → activities → validate → [review] → mdx

    Named phases replace v3's letter-coded A/B/C/D/E/F:
    - validate: merges v3 audit + D.0 + D.0.5 (all deterministic checks + Gemini fix)
    - review: merges v3 D.1 + D.2 + F (Claude review + up to 2 fix attempts)
    - mdx: always runs, even on validate/review failure (for preview)

    Two modes:
    - RC (default): research → content → activities → validate → mdx (status: draft)
    - Full (--review): adds Claude review phase (status: reviewed)

Pipeline v3 (--v3 flag):
    Phase A → B → C → audit → D → [F] → E (legacy, preserved for compatibility)

Cross-agent pipeline: Gemini builds, Claude reviews (prevents self-review gaming).

Usage:
    .venv/bin/python scripts/build_module.py a1 12                    # RC mode (v4)
    .venv/bin/python scripts/build_module.py a1 12 --review           # Full mode (v4)
    .venv/bin/python scripts/build_module.py hist 5 --review          # Seminar + review
    .venv/bin/python scripts/build_module.py a1 --all                 # Build all (RC)
    .venv/bin/python scripts/build_module.py a1 12 --restart-from review  # Review → mdx
    .venv/bin/python scripts/build_module.py a1 12 --force-phase validate # Re-validate
    .venv/bin/python scripts/build_module.py a1 12 --v3               # Legacy v3 pipeline
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import textwrap
import time
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Import from pipeline_lib — consolidated shared utilities (no monkey-patching)
# ---------------------------------------------------------------------------
import pipeline_lib
from pipeline_lib import (
    # Dispatch + logging
    dispatch_gemini, log,
    # Phase helpers
    run_verify,
    _build_fix_prompt, _apply_section_fixes, _identify_affected_sections,
    fill_template, _dispatch_prompt, _gemini_output_path,
    mark_phase_locked, _run_with_heartbeat, _init_log,
    # Phase E + F (MDX + Claude final review) — reuse directly
    phase_8_mdx as phase_E_v3_delegate,
    phase_9_final_review as phase_F_v3_delegate,
    # Phase B content (archive check + fallback to phase_2_content)
    phase_B_content,
    # Preflight + completion
    preflight_v2, write_completion_report_v2,
    # State helpers
    is_phase_complete, load_state, save_state, _now_iso,
    write_placeholders,
    write_review_with_hash,
    ModuleContext,
    # Thread-safe locks
    _state_lock, FileLock,
    # Validation
    _validate_activities_yaml,
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

MAX_AUDIT_FIX_ITERS_CORE = 6
MAX_AUDIT_FIX_ITERS_SEMINAR = 8
MAX_D_ITERS = 4


def _max_audit_iters(track: str) -> int:
    """Seminar tracks get more fix attempts due to higher word counts and complexity (#607)."""
    if track in SEMINAR_TRACKS or track in PRO_TRACKS:
        return MAX_AUDIT_FIX_ITERS_SEMINAR
    return MAX_AUDIT_FIX_ITERS_CORE
ESCALATION_MODEL_CLAUDE = "claude-opus-4-6"       # Escalation: Claude fixes what Gemini can't
ESCALATION_MODEL_GEMINI = PRO_MODEL                # Escalation: Gemini fixes what Claude can't

# ---------------------------------------------------------------------------
# V4 pipeline constants — named phases, simplified architecture
# ---------------------------------------------------------------------------
PHASE_SEQUENCE_V4 = ["research", "discover", "content", "activities", "validate", "review", "mdx"]

_V4_PHASE_STATE_IDS: dict[str, list[str]] = {
    "research":   ["v4-research"],
    "discover":   ["v4-discover"],
    "content":    ["v4-content"],
    "activities": ["v4-activities"],
    "validate":   ["v4-validate"],
    "review":     ["v4-review"],
    "mdx":        ["v4-mdx"],
}

PHASE_LABELS_V4: dict[str, str] = {
    "research":   "Research + Meta",
    "discover":   "Discover (video + blog search)",
    "content":    "Content (prose)",
    "activities": "Activities + Vocab",
    "validate":   "Validate (audit + screen + Gemini fix)",
    "review":     "Review (Claude, optional)",
    "mdx":        "MDX Generation",
}

MAX_REVIEW_FIX_ITERS = 2  # Review phase: max fix attempts after Claude review

# Dispatch timeouts (seconds) — fail fast instead of hanging
TIMEOUT_CONTENT = 600       # Phase A/B: research + content generation (10 min)
TIMEOUT_ACTIVITIES = 600    # Phase C: activities + vocab (10 min)
TIMEOUT_FIX = 600           # Audit/D/F fix dispatches (10 min — was 300, too tight)
TIMEOUT_PRE_D_FIX = 120     # D.0 pre-validation fixes (2 min — simple targeted replacements)
TIMEOUT_REVIEW = 900        # Phase D review (15 min — D.1 uses tool access, needs more time)

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
    """Mark a v3 phase in state-v3.json (thread-safe via file lock)."""
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state-v3.json.lock"))
    with lock:
        phases = state.setdefault("phases", {})
        for sid in _V3_PHASE_STATE_IDS.get(phase_id, [phase_id]):
            phases[sid] = {"status": status, "ts": _now_iso(), **extra}
        _save_state_v3(ctx, state)


# ---------------------------------------------------------------------------
# V4 state helpers
# ---------------------------------------------------------------------------

def _state_file_v4(ctx: ModuleContext) -> Path:
    return ctx.orch_dir / "state-v4.json"


def _load_state_v4(ctx: ModuleContext) -> dict:
    import json
    sf = _state_file_v4(ctx)
    if sf.exists():
        try:
            return json.loads(sf.read_text("utf-8"))
        except Exception as e:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = sf.with_suffix(f".corrupted.{ts}.json")
            sf.rename(backup)
            logger.warning(
                "state-v4.json corrupted for %s/%s — backed up to %s, resetting state. Error: %s",
                ctx.track, ctx.slug, backup.name, e,
            )
    return {"track": ctx.track, "slug": ctx.slug, "mode": "v4", "phases": {}}


def _save_state_v4(ctx: ModuleContext, state: dict) -> None:
    import json, tempfile
    sf = _state_file_v4(ctx)
    sf.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(state, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=sf.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(sf)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _is_phase_v4_complete(ctx: ModuleContext, phase_id: str, state: dict) -> bool:
    """Check if a v4 phase is marked complete in state-v4.json."""
    for sid in _V4_PHASE_STATE_IDS.get(phase_id, [phase_id]):
        info = state.get("phases", {}).get(sid, {})
        if info.get("status") == "complete":
            return True
    return False


def _mark_phase_v4(ctx: ModuleContext, state: dict, phase_id: str, status: str, **extra: Any) -> None:
    """Mark a v4 phase in state-v4.json (thread-safe via file lock)."""
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state-v4.json.lock"))
    with lock:
        phases = state.setdefault("phases", {})
        for sid in _V4_PHASE_STATE_IDS.get(phase_id, [phase_id]):
            phases[sid] = {"status": status, "ts": _now_iso(), **extra}
        _save_state_v4(ctx, state)


# ---------------------------------------------------------------------------
# V4 screen result serialization (cache between validate → review)
# ---------------------------------------------------------------------------

def _compute_content_hash(ctx: ModuleContext) -> str:
    """Hash md + activities + vocab files for cache invalidation."""
    import hashlib
    h = hashlib.md5()
    for key in ("md", "activities", "vocabulary", "vocab"):
        p = ctx.paths.get(key)
        if p and p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _save_screen_result(ctx: ModuleContext, screen: DScreenResult) -> None:
    """Save DScreenResult + content hash for review phase reuse."""
    import json, dataclasses
    data = dataclasses.asdict(screen)
    data["content_hash"] = _compute_content_hash(ctx)
    (ctx.orch_dir / "screen-result.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def _load_screen_result(ctx: ModuleContext) -> DScreenResult | None:
    """Load cached screen result, return None if stale or missing."""
    import json
    f = ctx.orch_dir / "screen-result.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text("utf-8"))
    except Exception:
        return None
    current_hash = _compute_content_hash(ctx)
    if data.get("content_hash") != current_hash:
        log("  Review: Cached screen stale — re-screening")
        return None
    # Reconstruct DScreenResult (drop content_hash key)
    data.pop("content_hash", None)
    try:
        return DScreenResult(**data)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# V4 status propagation (draft / reviewed)
# ---------------------------------------------------------------------------

def _update_pipeline_status(ctx: ModuleContext, pipeline_status: str) -> None:
    """Write pipeline_status into status/{slug}.json."""
    import json
    status_path = ctx.paths.get("status")
    if not status_path:
        return
    status_path.parent.mkdir(parents=True, exist_ok=True)
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text("utf-8"))
        except Exception:
            data = {}
    else:
        data = {}
    data["pipeline_status"] = pipeline_status
    data["pipeline_status_ts"] = _now_iso()
    status_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    log(f"  Status: {pipeline_status} → {status_path.name}")


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
        # Guard against infinite re-exhaustion: if note says "needs-rebuild" or
        # "escalation-failed", the module is structurally broken — don't waste API calls.
        audit_note = audit_phase.get("note", "")
        if audit_note in ("needs-rebuild", "escalation-failed"):
            log(f"  Audit revalidation: skipping — module marked '{audit_note}'")
            return

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
            # Still fails — only clear if this is the first revalidation attempt
            # (prevents infinite clear→exhaust→clear loop in batch mode)
            prev_attempts = audit_phase.get("attempts", 0)
            if prev_attempts <= 1:
                cleared = []
                for phase_key in ("audit", "D"):
                    for sid in _V3_PHASE_STATE_IDS.get(phase_key, []):
                        if phases.pop(sid, None):
                            cleared.append(sid)
                if cleared:
                    _save_state_v3(ctx, state)
                    log(f"  Audit revalidation: clearing stale FAILED state — fresh fix loop")
            else:
                log(f"  Audit revalidation: still failing after {prev_attempts} attempts — not clearing (use --rebuild to reset)")
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
CLAUDE_MODEL_REVIEW     = "claude-opus-4-6"     # Phase D.1/D.2 default (deep analysis + repair needs best model)
CLAUDE_MODEL_REREVIEW   = "claude-opus-4-6"     # Phase D.3 default — same model as D.1 to prevent calibration drift (#633)


def _apply_find_replace_fixes(file_path: Path, raw_output: str) -> int:
    """Apply FIND/REPLACE fix pairs from D.2 output to a file.

    Parses the FIND:/REPLACE: pairs within ===SECTION_FIX_START=== blocks,
    applies exact string replacements, and returns the count of successful
    replacements. Falls back to normalized whitespace matching if exact match
    fails.

    This replaces _apply_section_fixes for Phase D.2, which uses FIND/REPLACE
    pairs rather than whole-section replacement.
    """
    if not file_path.exists():
        return 0

    # Extract the fix block
    fix_match = re.search(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        raw_output, re.DOTALL,
    )
    if not fix_match:
        return 0

    fix_block = fix_match.group(1)

    # Only process lines targeting this file.
    # Default to active — if Claude omits FILE: headers (single-file fix),
    # we still apply the FIND/REPLACE pairs instead of silently dropping them.
    current_file_active = True
    file_name = file_path.name
    pairs: list[tuple[str, str]] = []
    current_find: list[str] | None = None
    current_replace: list[str] | None = None
    mode = None  # "find" or "replace"

    for line in fix_block.split("\n"):
        stripped = line.strip()

        # FILE: header — check if this section targets our file
        if stripped.startswith("FILE:"):
            file_ref = stripped[5:].strip()
            current_file_active = (
                file_name in file_ref
                or str(file_path) in file_ref
                or file_path.name == Path(file_ref).name
            )
            mode = None
            current_find = None
            current_replace = None
            continue

        if not current_file_active:
            continue

        # Separator between pairs
        if stripped == "---":
            # Save the completed pair
            if current_find is not None and current_replace is not None:
                pairs.append(("\n".join(current_find), "\n".join(current_replace)))
            current_find = None
            current_replace = None
            mode = None
            continue

        if stripped == "FIND:":
            current_find = []
            mode = "find"
            continue
        if stripped == "REPLACE:":
            current_replace = []
            mode = "replace"
            continue

        # Accumulate content lines
        if mode == "find" and current_find is not None:
            current_find.append(line)
        elif mode == "replace" and current_replace is not None:
            current_replace.append(line)

    # Don't forget the last pair (may not have trailing ---)
    if current_find is not None and current_replace is not None:
        pairs.append(("\n".join(current_find), "\n".join(current_replace)))

    if not pairs:
        return 0

    content = file_path.read_text("utf-8")
    applied = 0

    for find_text, replace_text in pairs:
        find_text = find_text.strip()
        replace_text = replace_text.strip()
        if not find_text or find_text == replace_text:
            continue

        # Strip «» quotes if present (some models wrap in guillemets)
        if find_text.startswith("«") and find_text.endswith("»"):
            find_text = find_text[1:-1]
        if replace_text.startswith("«") and replace_text.endswith("»"):
            replace_text = replace_text[1:-1]

        # Try exact match first
        if find_text in content:
            content = content.replace(find_text, replace_text, 1)
            applied += 1
            continue

        # Fallback: normalize whitespace and try again
        normalized_find = re.sub(r'\s+', ' ', find_text).strip()
        # Search for the normalized version in normalized content
        normalized_content = re.sub(r'\s+', ' ', content)
        if normalized_find in normalized_content:
            # Find the position in normalized content, then map back
            idx = normalized_content.index(normalized_find)
            # Rebuild: find the corresponding range in original content
            # by counting non-whitespace characters up to idx
            char_count = 0
            orig_start = 0
            for i, ch in enumerate(content):
                if char_count >= idx:
                    orig_start = i
                    break
                if ch in (' ', '\t', '\n', '\r'):
                    if i == 0 or content[i-1] not in (' ', '\t', '\n', '\r'):
                        char_count += 1
                else:
                    char_count += 1
            # Find the end by matching the normalized find length
            end_count = 0
            orig_end = orig_start
            target_len = len(normalized_find)
            for i in range(orig_start, len(content)):
                ch = content[i]
                if ch in (' ', '\t', '\n', '\r'):
                    if i == orig_start or content[i-1] not in (' ', '\t', '\n', '\r'):
                        end_count += 1
                else:
                    end_count += 1
                if end_count >= target_len:
                    orig_end = i + 1
                    break

            content = content[:orig_start] + replace_text + content[orig_end:]
            applied += 1
            log(f"    Fix applied (fuzzy match): {find_text[:60]}...")
        else:
            log(f"    Fix SKIPPED (no match): {find_text[:80]}...")

    if applied > 0:
        file_path.write_text(content, "utf-8")

    return applied


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
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Prevent nested-session error

    prompt = prompt_file.read_text("utf-8")
    # Adapt persona — templates say "You are Gemini"
    prompt = prompt.replace("You are Gemini", "You are Claude")

    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]
    if allow_tools:
        cmd.extend(["--allowedTools", ",".join(allow_tools)])
    
    # Reinforce output format — Claude sometimes ignores delimiters in long prompts
    _PHASE_DELIMITERS: dict[str, tuple[str, str]] = {
        "D.1":     ("===REVIEW_START===", "===REVIEW_END==="),
        "D.2":     ("===SECTION_FIX_START===", "===SECTION_FIX_END==="),
        "C vocab": ("===VOCABULARY_START===", "===VOCABULARY_END==="),
        "C":       ("===ACTIVITIES_START===", "===ACTIVITIES_END==="),
        "A":       ("===META_OUTLINE_START===", "===META_OUTLINE_END==="),
    }
    # Match the most specific phase label substring (order matters — longest first)
    expected_start, expected_end = "===REVIEW_START===", "===REVIEW_END==="
    for key in ("D.2", "D.1", "C vocab", "C", "A"):
        if key in phase_label:
            expected_start, expected_end = _PHASE_DELIMITERS[key]
            break

    cmd.extend(["--append-system-prompt",
                 f"CRITICAL: Your output MUST contain {expected_start} and {expected_end} "
                 "delimiters wrapping the full structured output. Output without these delimiters "
                 "is automatically discarded. Do NOT summarize — produce the FULL output requested."])

    try:
        from pipeline_lib import _run_with_heartbeat
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
# Helper: extract delimiter content
# ---------------------------------------------------------------------------

def _extract_delimiter(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiters. Anchors on LAST start tag (Gemini echoes templates).

    If real content is truncated (no end tag after last start), returns None so
    _extract_delimiter_tolerant() can recover partial content.

    Why not rfind(end_tag)? If Gemini echoes format (with both START+END) then
    truncates real content before its END tag, rfind(end_tag) finds the echo's
    END tag — silently returns the short echo. Anchoring on last START avoids this.
    """
    s = text.rfind(start_tag)
    if s == -1:
        return None
    s += len(start_tag)
    e = text.find(end_tag, s)
    if e == -1:
        return None  # Truncation — let tolerant fallback handle it
    return text[s:e].strip()


def _extract_delimiter_tolerant(
    text: str, start_tag: str, end_tag: str, *, content_type: str = "yaml"
) -> str | None:
    """Extract delimited content, tolerating missing end tag.

    First tries exact extraction. If the end tag is missing but the start tag
    exists (Gemini truncation or missing closing delimiter), extracts from start
    tag to the last valid line (strips bridge status footer lines).

    Args:
        content_type: ``"yaml"`` (default) validates with yaml.safe_load and
            checks for ``items`` key — designed for vocab/activity YAML.
            ``"markdown"`` skips YAML validation and returns cleaned content
            if non-empty — used for D.1 Markdown reviews.
    """
    # Try exact match first
    exact = _extract_delimiter(text, start_tag, end_tag)
    if exact:
        return exact

    # Tolerant: start tag present, end tag missing — use rfind so we
    # recover truncated REAL block, not the echoed format example
    s = text.rfind(start_tag)
    if s == -1:
        return None

    s += len(start_tag)
    raw = text[s:]

    # Strip footer lines from the end (bridge footer, status messages)
    lines = raw.split("\n")
    clean_lines = []
    for line in lines:
        # Stop at bridge status markers or separator lines
        stripped = line.strip()
        if stripped.startswith("─") or stripped.startswith("✅") or stripped.startswith("✓"):
            break
        if stripped.startswith("===") and stripped.endswith("==="):
            break
        clean_lines.append(line)

    # Trim trailing blank lines
    while clean_lines and not clean_lines[-1].strip():
        clean_lines.pop()

    candidate = "\n".join(clean_lines).strip()
    if not candidate:
        return None

    # --- Markdown mode: accept any non-empty content ---
    if content_type == "markdown":
        log(f"    Tolerant extraction (markdown): recovered {len(candidate)} chars (missing {end_tag})")
        return candidate

    # --- YAML mode: validate structure before accepting ---
    import yaml
    try:
        parsed = yaml.safe_load(candidate)
        if parsed and isinstance(parsed, dict) and "items" in parsed:
            log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (missing {end_tag})")
            return candidate
    except yaml.YAMLError:
        # Try truncating to last complete entry (last line ending with a complete value)
        # Find the last complete `- lemma:` block
        last_good = -1
        for i, line in enumerate(clean_lines):
            if line.strip().startswith("- lemma:"):
                last_good = i
        if last_good > 0 and last_good > 1:
            # Find next `- lemma:` or end, take up to before it
            for j in range(last_good, len(clean_lines)):
                ln = clean_lines[j].strip()
                if j > last_good and ln.startswith("- lemma:"):
                    break
            # Keep lines up to (but not including) the incomplete last entry
            trimmed = "\n".join(clean_lines[:last_good]).strip()
            try:
                parsed = yaml.safe_load(trimmed)
                if parsed and isinstance(parsed, dict) and "items" in parsed:
                    log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (trimmed incomplete entry)")
                    return trimmed
            except yaml.YAMLError:
                pass

    return None


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

def _compute_metrics_direct(ctx: ModuleContext) -> dict[str, str]:
    """Compute audit metrics WITHOUT running the audit subprocess.

    Returns a dict of string values ready for template injection. Pure computation
    only — no run_verify() call. Used by _deterministic_screen() (D.0) to avoid
    redundant audit invocations.

    Metrics computed: word count, immersion%, richness, engagement, activity count,
    vocab count. Does NOT set COMPUTED_AUDIT_STATUS (caller handles that).
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

    word_target = getattr(ctx, "word_target", 0) or 0
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
    # Normalize: a1 -> A1, hist -> HIST
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

    # Richness breakdown (so Phase D knows what to fix)
    if content_path and content_path.exists():
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from calculate_richness import calculate_richness_score
            act_types = []
            if act_path and act_path.exists():
                try:
                    act_data_rich = yaml.safe_load(act_path.read_text("utf-8"))
                    if isinstance(act_data_rich, list):
                        act_types = [a.get("type", "") for a in act_data_rich if isinstance(a, dict)]
                except Exception:
                    pass
            level_code_rich = ctx.track.split("-")[0].lower() if "-" not in ctx.track else ctx.track.lower()
            richness = calculate_richness_score(content, level_code_rich, str(content_path), act_types)
            metrics["COMPUTED_RICHNESS_SCORE"] = str(richness.get("score", 0))
            metrics["COMPUTED_RICHNESS_THRESHOLD"] = str(richness.get("threshold", 95))
            # Build actionable breakdown of below-target dimensions
            raw = richness.get("raw", {})
            targets = richness.get("targets", {})
            gaps = []
            for dim, target in targets.items():
                actual = raw.get(dim, 0)
                if actual < target:
                    gaps.append(f"{dim}: {actual}/{target}")
            metrics["COMPUTED_RICHNESS_GAPS"] = ", ".join(gaps) if gaps else "none"
        except Exception:
            metrics["COMPUTED_RICHNESS_SCORE"] = "?"
            metrics["COMPUTED_RICHNESS_THRESHOLD"] = "?"
            metrics["COMPUTED_RICHNESS_GAPS"] = "?"

    return metrics


def _compute_audit_metrics(ctx: ModuleContext) -> dict[str, str]:
    """Pre-compute audit metrics including a full audit run.

    Backward-compatible wrapper around _compute_metrics_direct() — adds
    COMPUTED_AUDIT_STATUS by running run_verify(). Used by Phase F and
    any caller that needs the audit status alongside metrics.
    """
    metrics = _compute_metrics_direct(ctx)
    content_path = ctx.paths.get("md")
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


def _build_d3_context(d1_review: str, repair_cycle: int) -> str:
    """Build D.3 context injection with D.1 findings and D.2 repair info (#633).

    Gives D.3 focus (knows what to verify) without blinding it (still does
    full review and can find regressions from D.2 rewrites).
    """
    # Extract the key parts of the D.1 review for context
    # Truncate to avoid bloating the prompt — keep issues + verdict
    review_lines = d1_review.strip().split('\n')
    # Keep first 80 lines max (scores + issues + verdict — skip lengthy evidence)
    truncated = '\n'.join(review_lines[:80])
    if len(review_lines) > 80:
        truncated += f"\n\n... ({len(review_lines) - 80} more lines truncated)"

    return f"""## D.3 Re-Review Context (Repair Cycle {repair_cycle})

> **You are re-reviewing content that was already reviewed and repaired.**
> A previous D.1 review found issues. D.2 applied targeted FIND/REPLACE fixes.
> Your job: **verify the fixes landed correctly AND check for regressions** introduced by the repair.

### What D.1 Found (previous review summary)

<details>
<summary>D.1 Review (click to expand)</summary>

{truncated}

</details>

### Your D.3 Re-Review Focus

1. **Verify each D.1 issue was fixed** — check that the specific problems from D.1 no longer exist in the current content
2. **Check for D.2 regressions** — D.2 rewrites may have introduced new errors (broken sentences, orphaned references, formatting damage)
3. **Score the current state** — your scores reflect the content AS IT IS NOW, not the D.1 review's scores
4. **Do NOT auto-pass** — if D.2 fixes created new problems, flag them even though the originals are fixed

---"""


def _extract_audit_failures(audit_output: str) -> str:
    """Extract actionable failure lines from audit output for the D.2 repair prompt.

    Captures: gate failures, pedagogical violations (including ROBOTIC_STRUCTURE,
    STRUCTURAL_MONOTONY), immersion hints, and severity indicators. This ensures
    D.2 can fix both review issues AND audit gate failures in one pass (#633).
    """
    lines = audit_output.strip().split("\n")
    failure_lines = []
    # Track whether we're inside a pedagogical violations section
    in_ped_section = False

    for line in lines:
        stripped = line.strip()

        # Gate failures and error keywords
        if any(kw in stripped.upper() for kw in [
            "FAIL", "ERROR", "VIOLATION", "MISSING", "GATE",
            "ROBOTIC", "MONOTONY", "IMMERSION TOO", "SEVERITY",
        ]):
            failure_lines.append(stripped)
            continue

        # Emoji-prefixed status lines
        if stripped.startswith("❌") or stripped.startswith("🔴") or stripped.startswith("⚠️"):
            failure_lines.append(stripped)
            continue

        # Pedagogical violation details (type-tagged lines)
        if stripped.startswith("- **[") or stripped.startswith("- ["):
            failure_lines.append(stripped)
            continue

        # Immersion fix hints
        if "IMMERSION" in stripped.upper() and ("LOW" in stripped.upper() or "HIGH" in stripped.upper()):
            failure_lines.append(stripped)
            continue

        # Section headers for context
        if stripped.startswith("## PEDAGOGICAL") or stripped.startswith("## Low Density"):
            in_ped_section = True
            failure_lines.append(stripped)
            continue

        # Lines inside pedagogical violation section (don't break on blank lines —
        # pedagogical sections may have blank lines between bullet points #633)
        if in_ped_section:
            if stripped.startswith("## "):
                in_ped_section = False
            elif stripped:
                failure_lines.append(stripped)
                continue

    if not failure_lines:
        # Fallback: return last 40 lines
        return "\n".join(lines[-40:])
    return "\n".join(failure_lines)


# Audit failure codes that indicate diffuse issues (not FIND/REPLACE fixable).
# These require structural rewrite, not targeted repair.
_DIFFUSE_FAILURE_CODES = {
    "ROBOTIC_STRUCTURE",        # Sentence pattern repetition throughout
    "STRUCTURAL_MONOTONY",      # Section openers share >70% lexical overlap (#633)
    "CONTENT_REDUNDANCY",       # Duplicate sentences across sections
    "EXCESSIVE_METAPHOR",       # Too many metaphors (prose style issue)
    "THEORY_FRONTLOADING",      # Structure issue: too much theory before practice
    "LOW_IMMERSION",            # Fundamental language balance problem
}

_deterministic_fix_mtimes: dict[str, float] = {}  # slug → max mtime of last fix pass


def _run_deterministic_fixes(ctx: ModuleContext) -> int:
    """Run all zero-cost deterministic fixes on a module's files.

    Consolidates: euphony, YAML schema fixes, forbidden
    activity removal. Returns total number of fixes applied.

    Uses mtime tracking to skip redundant runs when files haven't changed
    since the last pass (#625).

    Called before the diffuse-vs-targeted triage so that cascading failures
    from a single YAML error don't trick the triage into marking the module
    as needing a full rebuild (#623).
    """
    total = 0
    content_path = ctx.paths.get("md")

    # Dirty-flag: skip if no files changed since last fix pass
    target_files = [
        content_path,
        ctx.paths.get("vocab") or ctx.paths.get("vocabulary"),
        ctx.paths.get("activities"),
    ]
    current_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    last_mtime = _deterministic_fix_mtimes.get(ctx.slug, 0.0)
    if current_max_mtime > 0 and current_max_mtime <= last_mtime:
        return 0  # Files unchanged since last pass

    # 1. Euphony auto-fix (content .md)
    if content_path and content_path.exists():
        try:
            from audit.checks.euphony import auto_fix_euphony
            text = content_path.read_text("utf-8")
            fixed_text, n = auto_fix_euphony(text, str(content_path))
            if n > 0:
                content_path.write_text(fixed_text, "utf-8")
                total += n
                log(f"    Auto-fix: {n} euphony violation(s)")
        except Exception as e:
            logger.warning("Auto-fix: euphony failed", exc_info=True)
            log(f"    Auto-fix: euphony failed: {e}")

    # 2. YAML schema fixes (activities file)
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
            logger.warning("Auto-fix: YAML fix failed", exc_info=True)
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
            logger.warning("Auto-fix: forbidden activity check failed", exc_info=True)
            log(f"    Auto-fix: forbidden activity check failed: {e}")

    # Update mtime tracker so subsequent calls within the same pipeline skip
    # unless files are modified again (e.g. by an LLM fix dispatch).
    new_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    _deterministic_fix_mtimes[ctx.slug] = new_max_mtime

    return total


def _all_issues_diffuse(audit_output: str) -> bool:
    """Determine if ALL audit issues are diffuse (not fixable by FIND/REPLACE).

    Returns True only if audit has failing codes AND every one is diffuse.
    If audit passed (no failing codes), returns False — review issues are
    always targeted (specific lines/fixes) and should go to D.2.

    Classification is deterministic — based on audit failure codes only.
    Review text is NOT used for classification because review issues are
    always targeted (specific lines, specific fixes) by definition (#623).
    """
    import re as _re

    # Extract failing codes: look for lines containing ❌ or FAIL followed by [CODE]
    # Uses a reliable regex that checks the full line context, not fragile split logic.
    failing_codes: set[str] = set()
    for line in audit_output.split("\n"):
        if "❌" in line or "FAIL" in line.upper():
            codes_in_line = _re.findall(r'\[([A-Z_]{3,})\]', line)
            failing_codes.update(codes_in_line)

    # If audit passed (no failing codes), ALL issues come from the review.
    # Review issues are targeted by definition — the reviewer identifies specific
    # lines, calques, grammar errors, activity mismatches. Never skip D.2 here.
    if not failing_codes:
        return False

    # Check if ALL failing audit codes are diffuse (not fixable by FIND/REPLACE)
    has_targeted = bool(failing_codes - _DIFFUSE_FAILURE_CODES)
    if has_targeted:
        return False  # At least one targeted audit issue exists

    # All audit failures are diffuse — D.2 FIND/REPLACE won't help
    return True


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
            log(f"  research: SKIP (meta locked — content exists at {wc}w, target {ctx.word_target}w)")
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
                log("  research: SKIP (already complete)")
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
        # Strip markdown code fences that LLMs sometimes wrap around YAML
        meta_text_clean = re.sub(r'^```(?:ya?ml)?\s*\n', '', meta_text.strip())
        meta_text_clean = re.sub(r'\n```\s*$', '', meta_text_clean)
        try:
            outline_data = yaml.safe_load(meta_text_clean)
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

def phase_B_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase B: Write prose. Delegates to v2's phase_2_content."""
    phase = "B"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  content: SKIP (already complete)")
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

    ok = phase_B_content(ctx)

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


# ---------------------------------------------------------------------------
# Phase C: Activities + Vocabulary (single combined call)
# ---------------------------------------------------------------------------

def _build_vocab_only_prompt(ctx: ModuleContext) -> str | None:
    """Build a lightweight prompt for vocabulary-only generation.

    Used as fallback when Phase C output is truncated (activities extracted
    but vocabulary cut off by output token limit).
    """
    content_path = ctx.paths.get("md")
    plan_path = ctx.paths.get("plan")
    meta_path = ctx.paths.get("meta")

    if not content_path or not content_path.exists():
        return None

    plan_ref = f"\n\n**Plan file** (vocabulary_hints — follow this list):\n```\n{plan_path}\n```" if plan_path and plan_path.exists() else ""
    meta_ref = f"\n\n**Meta file** (vocab count target):\n```\n{meta_path}\n```" if meta_path and meta_path.exists() else ""

    return f"""You are a TEXT GENERATOR. Generate ONLY vocabulary YAML for a Ukrainian language module.

Read the lesson content:
```
{content_path}
```
{plan_ref}{meta_ref}

## Task

Generate vocabulary YAML for the key terms taught in this lesson. Follow vocabulary_hints from the plan file if available.

## Format

Each entry uses: `lemma` (Ukrainian), `translation` (English), `pos` (part of speech).
Optional: `gender` (m/f/n for nouns), `aspect` (perfective/imperfective for verbs), `notes`, `usage`, `example`.

Do NOT include `ipa` fields.

## Output

You MUST output BOTH the opening AND closing delimiters. The closing delimiter is MANDATORY.

===VOCABULARY_START===

items:
  - lemma: "слово"
    translation: "word"
    pos: "noun"
    gender: "n"

===VOCABULARY_END===

CRITICAL: You MUST end your output with the line ===VOCABULARY_END=== — the pipeline CANNOT extract your work without it.
Output NOTHING else. No commentary, no explanation. Just the delimited vocabulary YAML.
"""


def phase_C_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase C: Generate activities + vocabulary in a single Gemini call."""
    phase = "C"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  activities: SKIP (already complete)")
        return True

    # Check if both files already exist and are valid
    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")
    if (act_path and act_path.exists() and voc_path and voc_path.exists()):
        if _validate_activities_yaml(act_path):
            # Staleness check: if plan or content is newer than activities,
            # the activities are stale (built from an old plan/content).
            # --rebuild sets ctx.refresh=True which forces regeneration.
            stale = False
            if getattr(ctx, "refresh", False):
                stale = True
                log("  Phase C: --rebuild flag set — regenerating activities/vocab")
            else:
                act_mtime = act_path.stat().st_mtime
                plan_path = ctx.paths.get("plan")
                content_path = ctx.paths.get("md")
                for ref_path, ref_label in [
                    (plan_path, "plan"),
                    (content_path, "content"),
                ]:
                    if ref_path and ref_path.exists() and ref_path.stat().st_mtime > act_mtime:
                        stale = True
                        log(f"  Phase C: Activities predate {ref_label} — regenerating")
                        break

            if stale:
                act_path.unlink(missing_ok=True)
                if voc_path and voc_path.exists():
                    voc_path.unlink(missing_ok=True)
                log("  Phase C: Deleted stale activities/vocab for regeneration")
            else:
                log("  Phase C: ADOPT — existing activities/vocab found and valid")
                _mark_phase_v3(ctx, state, phase, "complete", note="adopted-existing")
                return True
        else:
            log("  Phase C: Existing activities invalid — deleting and regenerating")
            act_path.unlink(missing_ok=True)
            # Also delete stale vocabulary — it was paired with the invalid activities
            if voc_path and voc_path.exists():
                voc_path.unlink(missing_ok=True)
                log("  Phase C: Also deleted stale vocabulary (paired with invalid activities)")

    # Fast path: if activities exist and valid but vocabulary is missing (truncation
    # recovery), skip the full dispatch and go straight to vocabulary-only.
    if (act_path and act_path.exists() and act_path.stat().st_size > 10
            and (not voc_path or not voc_path.exists())):
        if _validate_activities_yaml(act_path):
            log("  Phase C: Activities exist and valid, vocabulary missing — vocab-only dispatch")
            use_claude = "C" in getattr(ctx, "use_claude", set())
            vocab_prompt = _build_vocab_only_prompt(ctx)
            if vocab_prompt:
                vocab_prompt_file = ctx.orch_dir / "phase-C-vocab-fallback.md"
                vocab_prompt_file.write_text(vocab_prompt, "utf-8")
                if use_claude:
                    claude_model = getattr(ctx, "claude_model_C", CLAUDE_MODEL_ACTIVITIES)
                    vok, vraw = _dispatch_claude_phase(
                        vocab_prompt_file, "Phase C vocab", model=claude_model, timeout=300,
                    )
                else:
                    vok, vraw = dispatch_gemini(
                        _dispatch_prompt(ctx, vocab_prompt_file),
                        task_id=f"v3-{ctx.slug}-pC-vocab",
                        model=ctx.model, stdout_only=True,
                        output_file=_gemini_output_path(ctx.slug, "pC-vocab"),
                        timeout=300,
                    )
                if vok:
                    vocab_text = _extract_delimiter_tolerant(vraw, "===VOCABULARY_START===", "===VOCABULARY_END===")
                    if vocab_text and voc_path:
                        voc_path.parent.mkdir(parents=True, exist_ok=True)
                        voc_path.write_text(vocab_text, "utf-8")
                        log(f"  Phase C: Vocabulary generated via fast-path → {voc_path.name}")
                        # Validate activities schema before marking complete
                        if not _validate_activities_yaml(act_path):
                            log("  Phase C: FAILED — activities YAML failed schema validation")
                            _mark_phase_v3(ctx, state, phase, "failed", note="activities-schema-invalid")
                            return False
                        mark_phase_locked(ctx, "3a", "complete", note="v3-phase-C")
                        mark_phase_locked(ctx, "3b", "complete", note="v3-phase-C")
                        _mark_phase_v3(ctx, state, phase, "complete", task_id=f"v3-{ctx.slug}-pC-vocab")
                        return True
            log("  Phase C: Vocab fast-path failed — falling through to full dispatch")

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
        vocab_text = _extract_delimiter_tolerant(raw_output, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            wrote_vocab = True
            log(f"  Phase C: Vocabulary extracted → {voc_path.name}")

    # Extract and log friction
    friction = _extract_delimiter(raw_output, "===FRICTION_START===", "===FRICTION_END===")
    if friction:
        friction_file = ctx.orch_dir / "phase-C-friction.md"
        friction_file.write_text(friction, encoding="utf-8")
        log(f"  Phase C: Friction report saved → {friction_file.name}")
        # Detect real truncation — ignore echoed template placeholders
        is_real_truncation = (
            "TOKEN_LIMIT_TRUNCATION" in friction
            and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
        )
        if is_real_truncation:
            log(f"  Phase C: ⚠ Gemini reported token limit truncation")

    # Vocabulary fallback: if activities extracted but vocabulary truncated (Gemini
    # hit output token limit), dispatch a lightweight vocabulary-only call.
    # Affects ~10% of Phase C runs — truncation always cuts vocabulary since it
    # comes after activities in the output.
    if wrote_activities and not wrote_vocab and "===VOCABULARY_START===" in raw_output:
        log("  Phase C: Vocabulary truncated (VOCABULARY_START without END) — dispatching vocab-only fallback")
        vocab_prompt = _build_vocab_only_prompt(ctx)
        if vocab_prompt:
            vocab_prompt_file = ctx.orch_dir / "phase-C-vocab-fallback.md"
            vocab_prompt_file.write_text(vocab_prompt, "utf-8")

            if use_claude:
                claude_model = getattr(ctx, "claude_model_C", CLAUDE_MODEL_ACTIVITIES)
                vok, vraw = _dispatch_claude_phase(
                    vocab_prompt_file, "Phase C vocab", model=claude_model, timeout=300,
                )
            else:
                vok, vraw = dispatch_gemini(
                    _dispatch_prompt(ctx, vocab_prompt_file),
                    task_id=f"v3-{ctx.slug}-pC-vocab",
                    model=ctx.model, stdout_only=True,
                    output_file=_gemini_output_path(ctx.slug, "pC-vocab"),
                    timeout=300,
                )
            if vok:
                vocab_text = _extract_delimiter_tolerant(vraw, "===VOCABULARY_START===", "===VOCABULARY_END===")
                if vocab_text and voc_path:
                    voc_path.parent.mkdir(parents=True, exist_ok=True)
                    voc_path.write_text(vocab_text, "utf-8")
                    wrote_vocab = True
                    log(f"  Phase C: Vocabulary extracted from fallback → {voc_path.name}")
                else:
                    log("  Phase C: Vocab fallback returned no valid delimited content")
            else:
                log("  Phase C: Vocab fallback dispatch failed")

    if not wrote_activities or not wrote_vocab:
        log(f"  Phase C: FAILED — missing files: activities={wrote_activities}, vocab={wrote_vocab}")
        _mark_phase_v3(ctx, state, phase, "failed",
                       note=f"missing-files-act={wrote_activities}-voc={wrote_vocab}")
        return False

    # Post-C schema validation gate (#623): verify generated YAML is valid
    # before marking complete — prevents 15-20 modules from wasting audit+D cycles
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
        # Also apply to activities/vocab if not content_only
        if not content_only:
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                _apply_section_fixes(ctx.paths["activities"], output)
            _vp = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
            if _vp and _vp.exists():
                _apply_section_fixes(_vp, output)
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

    content_path = ctx.paths["md"]

    # Auto-fix pass: apply deterministic fixes (euphony, YAML, forbidden
    # activities) before calling any LLM. Zero API cost, instant.
    auto_fix_total = _run_deterministic_fixes(ctx)
    if auto_fix_total > 0:
        log(f"  Audit: {auto_fix_total} deterministic fix(es) applied")

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
# Phase D dataclasses + helpers (D.0 screen, D.1 parser, LLM filler scanner)
# ---------------------------------------------------------------------------

@dataclass
class DScreenResult:
    """Result of D.0 deterministic screen — collects all pre-LLM findings."""
    metrics: dict[str, str]                   # COMPUTED_* placeholders (no audit status)
    deterministic_issues: list[dict] = field(default_factory=list)  # From regex checks
    audit_passed: bool = False
    audit_output: str = ""
    h2_sections: str = ""
    rag_verify_stats: dict = field(default_factory=dict)            # RAG word verification stats
    rag_verify_not_found: list[dict] = field(default_factory=list)  # Words not in VESUM/RAG


@dataclass
class D1Result:
    """Parsed result of D.1 Markdown review."""
    ok: bool
    issues: list[dict] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    verdict: str = ""   # "PASS" or "FAIL"
    raw_review: str = ""


# LLM filler phrases — absorbed from proofread.py's telltale list.
# Case-insensitive regex patterns for common AI-generated padding.
_LLM_FILLER_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bIt'?s worth noting that\b",
        r"\bThis is particularly important because\b",
        r"\binterestingly\b",
        r"\bOne of the key aspects\b",
        r"\bLet'?s explore\b",
        r"\bLet'?s dive in\b",
        r"\bLet'?s take a closer look\b",
        r"\bIn this lesson,? we will\b",
        r"\bIt is important to note\b",
        r"\bNumbers are everywhere\b",
        r"\bLanguage is not just about\b",
        r"\bAs we'?ve seen\b",
        r"\bAs you can see\b",
        r"\bIn conclusion\b",
        r"\bTo summarize\b",
        r"\bThis brings us to\b",
    ]
]

# Additional Ukrainian filler patterns (LLM-typical in Ukrainian content)
_LLM_FILLER_PATTERNS_UK: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bце не просто\b.*\bа й\b",                # "це не просто X, а й Y"
        r"\bдавайте розглянемо\b",                     # "let's consider"
        r"\bдавайте дізнаємося\b",                     # "let's find out"
        r"\bцікаво,?\s+що\b",                          # "interestingly, that"
        r"\bварто зазначити,?\s+що\b",                 # "it's worth noting that"
        r"\bдзеркало\s+культури\b",                    # LLM-typical metaphor
        r"\bархітектура\s+мови\b",                     # LLM-typical metaphor
        r"\bдвигун\s+прогресу\b",                      # LLM-typical metaphor
    ]
]


def _scan_llm_filler(content: str) -> list[dict]:
    """Scan content for LLM filler phrases.

    Returns a list of issue dicts compatible with DScreenResult.deterministic_issues.
    Only flags phrases found outside of blockquotes and callout boxes.
    """
    issues: list[dict] = []

    # Split into lines for context, skip blockquotes and callout lines
    lines = content.split("\n")
    narrative_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip blockquotes, callouts, code blocks, frontmatter
        if stripped.startswith(">") or stripped.startswith("```") or stripped.startswith("---"):
            continue
        narrative_lines.append((i + 1, line))

    narrative_text = "\n".join(line for _, line in narrative_lines)

    for pattern in _LLM_FILLER_PATTERNS + _LLM_FILLER_PATTERNS_UK:
        for m in pattern.finditer(narrative_text):
            # Find approximate line number
            char_pos = m.start()
            line_num = narrative_text[:char_pos].count("\n") + 1
            issues.append({
                "type": "LLM_FILLER",
                "severity": "MEDIUM",
                "location": f"~line {line_num}",
                "text": m.group()[:80],
                "fix": "Rewrite into concrete, specific teaching content",
            })

    return issues


def _parse_d1_review(raw_output: str) -> D1Result:
    """Parse D.1 Markdown review from ===REVIEW_START=== / ===REVIEW_END=== delimiters.

    The D.1 template produces structured Markdown (not YAML). This function
    extracts the overall score, per-dimension scores from the ``## Scores``
    table, critical issues, and verdict.

    Returns a D1Result with parsed fields.
    """
    review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if not review_text:
        # Try tolerant extraction (missing end tag) — markdown mode skips YAML validation
        review_text = _extract_delimiter_tolerant(
            raw_output, "===REVIEW_START===", "===REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    # --- Extract verdict ---
    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    # --- Extract overall score ---
    score = 0.0
    score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        score = float(score_m.group(1))

    # --- Extract per-dimension scores from ## Scores table ---
    scores: dict[str, float] = {}
    if score > 0:
        scores["overall"] = score

    scores_section = re.search(
        r'## Scores\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if scores_section:
        # Match table rows: | N | Dimension Name | X/10 | or | N | Dimension Name | X.X/10 |
        dim_rows = re.findall(
            r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*([\d.]+)/10\s*\|',
            scores_section.group(1),
        )
        for dim_name, dim_score in dim_rows:
            # Normalize dimension name: "Language Quality" → "language_quality"
            key = dim_name.strip().lower().replace(" ", "_")
            try:
                scores[key] = float(dim_score)
            except ValueError:
                pass

        # Also check for "Weighted Overall:" line in the scores section
        weighted_m = re.search(
            r'\*\*Weighted Overall:\*\*.*?=\s*\*\*([\d.]+)/10\*\*',
            scores_section.group(1),
        )
        if weighted_m:
            try:
                scores["weighted_overall"] = float(weighted_m.group(1))
            except ValueError:
                pass

    # Determine verdict from score if not explicit
    if not verdict and score > 0:
        verdict = "PASS" if score >= 9.0 else "FAIL"

    # --- Extract issues from "Critical Issues Found" section ---
    issues: list[dict] = []
    issues_section = re.search(
        r'## Critical Issues Found\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if issues_section:
        issue_blocks = re.findall(
            r'### Issue \d+:\s*(.+?)(?=### Issue|\Z)',
            issues_section.group(1),
            re.DOTALL,
        )
        for block in issue_blocks:
            issue: dict[str, str] = {"type": "REVIEW_ISSUE", "severity": "HIGH"}
            loc_m = re.search(r'\*\*Location\*\*:\s*(.+)', block)
            if loc_m:
                issue["location"] = loc_m.group(1).strip()
            prob_m = re.search(r'\*\*Problem\*\*:\s*(.+)', block)
            if prob_m:
                issue["text"] = prob_m.group(1).strip()
            fix_m = re.search(r'\*\*Fix\*\*:\s*(.+)', block)
            if fix_m:
                issue["fix"] = fix_m.group(1).strip()
            issues.append(issue)

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


# Keep old name as alias for backward compatibility with any external callers
_parse_d1_yaml = _parse_d1_review


def _extract_fix_plan(review_text: str) -> str:
    """Extract only actionable sections from a D.1 review for the D.2 fix prompt.

    Pulls: Critical Issues Found, Ukrainian Language Issues, Fix Plan to Reach *.
    Falls back to full review text if no sections are found.
    """
    sections: list[str] = []
    # Try multiple header variants for each section
    _PATTERNS = [
        r'(## Critical Issues Found\s*\n.*?)(?=\n## |\Z)',
        r'(## Ukrainian Language Issues\s*\n.*?)(?=\n## |\Z)',
        r'(## Fix Plan to Reach [^\n]+\n.*?)(?=\n## |\Z)',
    ]
    for pattern in _PATTERNS:
        m = re.search(pattern, review_text, re.DOTALL)
        if m:
            sections.append(m.group(1).strip())

    if not sections:
        return review_text  # fallback: inject full review
    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Track calibration system — per-level calibration injected into D.1 prompt
# ---------------------------------------------------------------------------

_CALIBRATION_DIR = Path(__file__).resolve().parent.parent / "claude_extensions" / "phases" / "calibration"


def _get_track_calibration(level: str, module_num: int) -> str:
    """Read the appropriate calibration file for a track/level + module number.

    Handles the B1 bridge vs immersed split (modules 1-5 use b1-bridge.md,
    modules 6+ use b1-immersed.md). Falls back to empty string if no
    calibration file exists for the track.
    """
    # Determine calibration file name
    level_lower = level.lower()

    if level_lower == "b1" and module_num <= 5:
        cal_name = "b1-bridge.md"
    elif level_lower == "b1":
        cal_name = "b1-immersed.md"
    elif level_lower.startswith("lit"):
        cal_name = "lit.md"
    else:
        cal_name = f"{level_lower}.md"

    cal_path = _CALIBRATION_DIR / cal_name
    if cal_path.exists():
        return cal_path.read_text("utf-8")

    # Fallback: try base level (e.g., b2 for b2-pro)
    base = level_lower.split("-")[0]
    fallback = _CALIBRATION_DIR / f"{base}.md"
    if fallback.exists():
        return fallback.read_text("utf-8")

    return ""


def _get_russicism_table(level: str) -> str:
    """Extract the Russicism Lookup section from a calibration file.

    Used to seed D.0's regex scanner with track-specific Russicism patterns
    and to inject the lookup table into the D.1 prompt.
    """
    cal_text = _get_track_calibration(level, 1)  # module_num=1 for table extraction
    if not cal_text:
        return ""

    # Extract section between ## Russicism Lookup and the next ## heading
    m = re.search(
        r'## Russicism Lookup.*?\n(.*?)(?=\n## |\Z)',
        cal_text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# Seminar tracks that get longer timeouts and mandatory Phase F after D.2
_SEMINAR_TIMEOUT_TRACKS = {"hist", "istorio", "bio", "lit", "oes", "ruth"}

# ---------------------------------------------------------------------------
# RAG: Pre-fetch literary primary source matches for D.1 quote verification
# ---------------------------------------------------------------------------

def _extract_quotes_from_content(content_path: Path) -> list[str]:
    """Extract quoted passages from module content for RAG verification.

    Looks for:
    - Text in «» (Ukrainian guillemets)
    - Blockquote lines starting with >
    """
    if not content_path.exists():
        return []

    text = content_path.read_text("utf-8")
    quotes = []

    # Ukrainian guillemets «...»
    for match in re.finditer(r"«([^»]{10,200})»", text):
        quotes.append(match.group(1).strip())

    # Blockquote lines (> text) — skip metadata/callout markers
    for match in re.finditer(r"^>\s+(.{10,200})", text, re.MULTILINE):
        line = match.group(1).strip()
        # Skip callout markers like [!did-you-know], [!culture-note], etc.
        if line.startswith("[!") or line.startswith("**"):
            continue
        quotes.append(line)

    return quotes


def _prefetch_rag_context(ctx: ModuleContext) -> str:
    """Pre-fetch RAG results for quotes found in module content.

    Returns formatted string for injection into D.1 prompt as {RAG_PRIMARY_SOURCES}.
    Only runs for seminar tracks with literary primary sources.
    """
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    if track_key not in SEMINAR_TRACKS:
        return "(Not a seminar track — no RAG verification needed)"

    content_path = ctx.paths.get("md")
    if not content_path or not content_path.exists():
        return "(Content file not found — cannot extract quotes)"

    quotes = _extract_quotes_from_content(content_path)
    if not quotes:
        return "(No quoted passages found in module content)"

    # Try to import RAG query module — gracefully degrade if Qdrant is down
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from rag.query import search_literary
    except ImportError:
        return "(RAG module not available — install qdrant-client and rag dependencies)"

    results = []
    for quote in quotes[:10]:  # Cap at 10 quotes to avoid prompt bloat
        try:
            hits = search_literary(quote, limit=2)
        except Exception as e:
            results.append(f"### Quote: «{quote[:80]}...»\n- RAG error: {e}\n")
            continue

        if not hits:
            results.append(f"### Quote: «{quote[:80]}...»\n- **No match found** in primary sources\n")
        else:
            lines = [f"### Quote: «{quote[:80]}...»"]
            for hit in hits:
                lines.append(
                    f"- **Match** (score {hit['score']:.3f}): "
                    f"{hit['work']} ({hit['year']}) — "
                    f"`{hit['text'][:150]}...`"
                )
            results.append("\n".join(lines) + "\n")

    return "\n".join(results) if results else "(No quotes extracted for verification)"


# Track-aware timeouts
TIMEOUT_REVIEW_CORE = 600       # A1-B2 core tracks (10 min)
TIMEOUT_REVIEW_SEMINAR = 750    # Seminar tracks (12.5 min)

# D.2 fix timeouts — shorter than D.1 (mechanical task, Read tool only)
TIMEOUT_FIX_CORE = 300          # A1-B2 fix (5 min max, typically ~1-2 min)
TIMEOUT_FIX_SEMINAR = 420       # Seminar fix (7 min max, typically ~2-4 min)
TIMEOUT_FIX_AUDIT_ONLY = 180    # Audit-only fix (3 min max, typically <1 min)


def _get_review_timeout(track: str) -> int:
    """Return the appropriate D.1 review timeout for a track."""
    key = "lit" if track.startswith("lit-") else track
    if key in _SEMINAR_TIMEOUT_TRACKS or key in SEMINAR_TRACKS:
        return TIMEOUT_REVIEW_SEMINAR
    return TIMEOUT_REVIEW_CORE


def _get_fix_timeout(track: str, audit_only: bool = False) -> int:
    """Return the appropriate D.2 fix timeout for a track."""
    if audit_only:
        return TIMEOUT_FIX_AUDIT_ONLY
    key = "lit" if track.startswith("lit-") else track
    if key in _SEMINAR_TIMEOUT_TRACKS or key in SEMINAR_TRACKS:
        return TIMEOUT_FIX_SEMINAR
    return TIMEOUT_FIX_CORE


# ---------------------------------------------------------------------------
# D.0: Deterministic Screen
# ---------------------------------------------------------------------------

def _deterministic_screen(ctx: ModuleContext, skip_review: bool = False) -> DScreenResult:
    """D.0: Run all deterministic checks before LLM review.

    Orchestrates:
    1. _run_deterministic_fixes(ctx) — euphony, YAML schema
    2. _compute_metrics_direct(ctx) — word count, immersion, richness (no audit subprocess)
    3. Single run_verify() — THE one audit call for D.0
    4. Russicism regex scan — from russicism_detection.py
    5. LLM filler regex scan — absorbed from proofread.py patterns
    6. RAG word verification — VESUM + Qdrant (graceful degradation)

    Args:
        skip_review: If True, pass --skip-review to audit (used when review
            phase runs later and MISSING_REVIEW is expected).

    Returns DScreenResult with all findings for D.1 injection.
    """
    result = DScreenResult(metrics={})

    # 1. Deterministic fixes (zero-cost)
    n_fixes = _run_deterministic_fixes(ctx)
    if n_fixes > 0:
        log(f"  D.0: {n_fixes} deterministic fix(es) applied")

    # 2. Compute metrics (no audit subprocess)
    result.metrics = _compute_metrics_direct(ctx)

    # 3. H2 sections
    content_path = ctx.paths.get("md")
    if content_path and content_path.exists():
        result.h2_sections = _extract_h2_sections(content_path)
    else:
        result.h2_sections = "(content file not found)"

    # 4. Single audit run
    if content_path and content_path.exists():
        result.audit_passed, result.audit_output = run_verify(
            content_path, content_only=False, skip_review=skip_review)
        result.metrics["COMPUTED_AUDIT_STATUS"] = "PASS" if result.audit_passed else "FAIL"
    else:
        result.audit_passed = False
        result.audit_output = "NO_CONTENT"
        result.metrics["COMPUTED_AUDIT_STATUS"] = "NO_CONTENT"

    # 5. Russicism regex scan
    if content_path and content_path.exists():
        try:
            from audit.checks.russicism_detection import check_russicisms
            content_text = content_path.read_text("utf-8")
            russicism_issues = check_russicisms(content_text, str(content_path))
            for r in russicism_issues:
                result.deterministic_issues.append({
                    "type": "RUSSIANISM",
                    "severity": r.get("severity", "HIGH").upper(),
                    "text": r.get("issue", ""),
                    "fix": r.get("fix", ""),
                })
        except Exception as e:
            logger.warning("D.0: Russicism scan failed: %s", e)

    # 6. LLM filler scan
    if content_path and content_path.exists():
        try:
            content_text = content_path.read_text("utf-8")
            filler_issues = _scan_llm_filler(content_text)
            result.deterministic_issues.extend(filler_issues)
        except Exception as e:
            logger.warning("D.0: LLM filler scan failed: %s", e)

    # 7. Word verification (VESUM only — RAG/Qdrant adds latency for marginal value)
    if content_path and content_path.exists():
        try:
            from rag_batch_verify import verify_module as rag_verify_module
            rag_results, rag_stats = rag_verify_module(
                content_path, use_rag=False, skip_activities=False,
            )
            result.rag_verify_stats = rag_stats
            result.rag_verify_not_found = [
                r for r in rag_results if r["status"] in ("❌", "⚠️")
            ]
            n_not_found = rag_stats.get("not_found", 0)
            n_partial = rag_stats.get("rag_hits", 0)
            if n_not_found > 0 or n_partial > 0:
                log(f"  D.0: RAG verify: {rag_stats['total']} words, "
                    f"{rag_stats['vesum_hits']} VESUM ✓, "
                    f"{n_partial} RAG-only ⚠️, {n_not_found} not found ❌")
            else:
                log(f"  D.0: RAG verify: {rag_stats['total']} words, "
                    f"100% VESUM coverage ✅")
        except Exception as e:
            logger.warning("D.0: RAG word verification failed: %s", e)

    det_count = len(result.deterministic_issues)
    if det_count > 0:
        log(f"  D.0: {det_count} deterministic issue(s) found "
            f"({sum(1 for i in result.deterministic_issues if i['type'] == 'RUSSIANISM')} Russianisms, "
            f"{sum(1 for i in result.deterministic_issues if i['type'] == 'LLM_FILLER')} filler)")

    return result


# ---------------------------------------------------------------------------
# Phase D: Cross-Agent Review + Fix (Claude reviews Gemini's work)
# D.0 (deterministic screen) → D.1 (structured review) → D.2 (repair if needed)
# ---------------------------------------------------------------------------

def _format_deterministic_issues(issues: list[dict]) -> str:
    """Format D.0 deterministic issues as text for prompt injection."""
    if not issues:
        return "(No deterministic issues found — D.0 pre-screen clean)"
    lines = []
    for i, iss in enumerate(issues, 1):
        lines.append(f"{i}. **[{iss.get('type', 'UNKNOWN')}]** (severity: {iss.get('severity', '?')})")
        if iss.get("location"):
            lines.append(f"   Location: {iss['location']}")
        if iss.get("text"):
            lines.append(f"   Text: {iss['text'][:120]}")
        if iss.get("fix"):
            lines.append(f"   Fix: {iss['fix'][:120]}")
    return "\n".join(lines)


def _format_filler_phrases(issues: list[dict]) -> str:
    """Format LLM filler findings for prompt injection."""
    filler = [i for i in issues if i.get("type") == "LLM_FILLER"]
    if not filler:
        return "(No LLM filler phrases detected by D.0 scanner)"
    lines = ["D.0 found these filler phrases — verify each one:"]
    for f in filler[:10]:
        lines.append(f"- \"{f.get('text', '')}\" at {f.get('location', '?')}")
    return "\n".join(lines)


def _format_rag_verification(stats: dict, not_found: list[dict]) -> str:
    """Format RAG word verification results for D.1 prompt injection."""
    if not stats:
        return "(RAG word verification did not run — VESUM DB may be missing)"

    total = stats.get("total", 0)
    vesum = stats.get("vesum_hits", 0)
    coverage = (vesum / total * 100) if total else 0

    lines = [
        f"**Words checked:** {total} | **VESUM coverage:** {vesum}/{total} ({coverage:.1f}%)",
    ]

    if not not_found:
        lines.append("All words verified ✅ — no morphological issues detected.")
        return "\n".join(lines)

    not_found_words = [r for r in not_found if r["status"] == "❌"]
    partial_words = [r for r in not_found if r["status"] == "⚠️"]

    if not_found_words:
        lines.append("")
        lines.append(f"**❌ Not found in VESUM or textbooks ({len(not_found_words)}):**")
        for r in not_found_words[:15]:  # Cap at 15 to avoid prompt bloat
            lines.append(f"- `{r['original']}` (source: {r['source']})")
        if len(not_found_words) > 15:
            lines.append(f"- ... and {len(not_found_words) - 15} more")
        lines.append("")
        lines.append("**Action:** Check if these are valid Ukrainian word forms. "
                      "Proper nouns and vocative forms may be legitimate. "
                      "Hallucinated forms or Russianisms must be flagged.")

    if partial_words:
        lines.append("")
        lines.append(f"**⚠️ Found in textbooks only, not VESUM ({len(partial_words)}):**")
        for r in partial_words[:10]:
            lines.append(f"- `{r['original']}` (source: {r['source']})")

    return "\n".join(lines)


def phase_D_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase D: Cross-agent adversarial review via Claude (refactored).

    D.0: Deterministic screen — regex scans, metrics, single audit
    D.1: Structured review — Claude with track calibration, pre-screen results
    D.2: Targeted repair — only if D.1 FAIL, max 2 iterations, NO re-review

    Eliminates D.3 (re-review) — the biggest time saving. D.2 modules get a
    single post-repair audit. Seminar D.2 modules get mandatory Phase F.
    """
    phase = "D"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  validate: SKIP (already complete)")
        return True

    # Pre-D activity validation gate (#606)
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

    # -----------------------------------------------------------------------
    # D.0: Deterministic Screen
    # -----------------------------------------------------------------------
    if not ctx.dry_run:
        log("  D.0: Running deterministic screen...")
        screen = _deterministic_screen(ctx)

        # D.0 fix loop removed — D.0.5 proofread handles all fixes (#660)
        # D.0 only screens; D.0.5 dispatches Gemini proofread+fix for everything.

        log(f"  D.0: Screen complete — audit {'PASS' if screen.audit_passed else 'FAIL'}, "
            f"{len(screen.deterministic_issues)} deterministic issue(s)")

        # -------------------------------------------------------------------
        # D.0.5: Gemini Proofread + Fix (editorial polish before Claude review)
        # Uses proofread.py --fix --no-mdx (Gemini Pro, tested best per #640)
        # Only runs when D.0 found issues — clean modules skip straight to D.1
        # -------------------------------------------------------------------
        if screen.deterministic_issues or not screen.audit_passed:
            module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
            log(f"  D.0.5: Dispatching Gemini proofread+fix on {ctx.slug}...")
            proofread_cmd = [
                sys.executable, str(SCRIPTS_DIR / "proofread.py"),
                ctx.track, str(module_num), "--fix", "--no-mdx",
            ]
            try:
                proofread_result = subprocess.run(
                    proofread_cmd, capture_output=True, text=True, timeout=300,
                )
                # Extract summary from proofread output
                pf_lines = (proofread_result.stdout or "").strip().split("\n")
                pf_found = [l for l in pf_lines if "FOUND:" in l or "CLEAN:" in l or "Applied" in l]
                for line in pf_found[-3:]:
                    log(f"    {line.strip()}")
                if proofread_result.returncode != 0 and not pf_found:
                    log(f"  D.0.5: proofread.py exited with code {proofread_result.returncode}")
                    # Non-fatal — continue to D.1 even if proofread had issues
            except subprocess.TimeoutExpired:
                log("  D.0.5: proofread.py timed out (300s) — continuing without proofread fixes")
            except Exception as e:
                log(f"  D.0.5: proofread.py error: {e} — continuing without proofread fixes")

            # Re-run D.0 screen after proofread fixes to update metrics
            log("  D.0.5: Re-screening after proofread fixes...")
            screen = _deterministic_screen(ctx)
            log(f"  D.0.5: Post-proofread — audit {'PASS' if screen.audit_passed else 'FAIL'}, "
                f"{len(screen.deterministic_issues)} deterministic issue(s)")
        else:
            log("  D.0.5: Skipped — D.0 found no issues, proceeding to D.1")

    else:
        screen = None  # type: ignore[assignment]

    # Template selection — use structured review template
    d1_template = PHASES_DIR / "phase-D1-structured-review.md"
    if not d1_template.exists():
        # Fallback to original template
        d1_template = PHASES_DIR / "phase-D1-evidence-review.md"
    d2_template = PHASES_DIR / "phase-D2-repair.md"
    if not d1_template.exists():
        log(f"  Phase D: ERROR — D1 template not found: {d1_template}")
        return False
    if not d2_template.exists():
        log(f"  Phase D: ERROR — D2 template not found: {d2_template}")
        return False

    if ctx.dry_run:
        log("  Phase D: DRY-RUN — would dispatch D.0 (screen) + D.1 (review) + D.2 (repair)")
        return True

    claude_model_D = getattr(ctx, "claude_model_D", CLAUDE_MODEL_REVIEW)
    review_timeout = _get_review_timeout(ctx.track)

    # -----------------------------------------------------------------------
    # D.1: Structured Review (with track calibration + pre-screen results)
    # -----------------------------------------------------------------------
    log(f"  D.1: Preparing structured review prompt...")

    # Get track calibration
    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    track_calibration = _get_track_calibration(ctx.track, module_num)
    russicism_table = _get_russicism_table(ctx.track)

    prompt_file = ctx.orch_dir / "phase-D-prompt-1.md"
    if not fill_template(d1_template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    # Inject all placeholders into prompt
    prompt_text = prompt_file.read_text("utf-8")
    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", screen.h2_sections)
    prompt_text = prompt_text.replace("{TRACK_CALIBRATION}", track_calibration or "(No track calibration available)")
    prompt_text = prompt_text.replace("{DETERMINISTIC_ISSUES}", _format_deterministic_issues(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{RUSSIANISM_TABLE}", russicism_table or "(No track-specific Russianism table available — use general checklist)")
    prompt_text = prompt_text.replace("{FILLER_PHRASES}", _format_filler_phrases(screen.deterministic_issues))

    # RAG primary source verification (seminar tracks only)
    rag_context = _prefetch_rag_context(ctx)
    prompt_text = prompt_text.replace("{RAG_PRIMARY_SOURCES}", rag_context)

    # RAG word verification (all tracks)
    rag_word_context = _format_rag_verification(
        screen.rag_verify_stats, screen.rag_verify_not_found,
    )
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", rag_word_context)

    prompt_file.write_text(prompt_text, "utf-8")

    log(f"  D.1: Dispatching evidence+review via Claude ({claude_model_D}, {review_timeout}s)...")
    log(f"    Metrics: {screen.metrics.get('COMPUTED_WORD_COUNT', '?')}w / "
        f"{screen.metrics.get('COMPUTED_WORD_TARGET', '?')}w, "
        f"{screen.metrics.get('COMPUTED_ACTIVITY_COUNT', '?')} activities, "
        f"immersion {screen.metrics.get('COMPUTED_IMMERSION_PERCENT', '?')}%")
    if track_calibration:
        log(f"    Track calibration: injected ({len(track_calibration)} chars)")
    if "(Not a seminar" not in rag_context and "(No quoted" not in rag_context:
        n_quotes = rag_context.count("### Quote:")
        log(f"    RAG verification: {n_quotes} quote(s) checked against primary sources")

    ok, raw_output = _dispatch_claude_phase(
        prompt_file, "Phase D.1",
        model=claude_model_D, timeout=review_timeout,
        allow_tools=["Read", "Grep", "Glob"],
    )
    if not ok:
        log("  D.1: Dispatch FAILED")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-dispatch-failed")
        return False

    # Parse Markdown review
    d1 = _parse_d1_review(raw_output)

    if not d1.ok or not d1.raw_review:
        log("  D.1: WARNING — no REVIEW delimiters in output (retrying full D.1)")
        (ctx.orch_dir / "phase-D1-raw-output.md").write_text(raw_output, "utf-8")

        # Retry once
        ok2, raw2 = _dispatch_claude_phase(
            prompt_file, "Phase D.1 (retry)",
            model=claude_model_D, timeout=review_timeout,
            allow_tools=["Read", "Grep", "Glob"],
        )
        if ok2:
            d1 = _parse_d1_review(raw2)

        if not d1.ok or not d1.raw_review:
            log("  D.1: Full retry also failed — no delimiters")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-no-review")
            return False

        log("  D.1: Full retry succeeded — delimiters found")

    review_text = d1.raw_review

    # Pre-save quality gate
    qg_ok, qg_reason = _quick_review_quality_gate(review_text, ctx.paths["md"])
    if not qg_ok:
        log(f"  D.1: REJECTED — {qg_reason}")
        (ctx.orch_dir / "phase-D1-rejected-review.md").write_text(review_text, "utf-8")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-shallow-review")
        return False

    # Inject Reviewed-By metadata if Claude forgot it
    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** {claude_model_D}\n\n{review_text}"

    # Save review with content hash for staleness detection (#618)
    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "phase-D-review-1.md").write_text(review_text, "utf-8")
    log(f"  D.1: Review saved → {ctx.paths['review'].name}")

    # Deterministic fixes after review save — zero API cost
    n_postD1 = _run_deterministic_fixes(ctx)
    if n_postD1 > 0:
        log(f"  D.1: {n_postD1} deterministic fix(es) applied")

    # Post-D.1 audit (single run_verify)
    log("  D.1: Running audit after review...")
    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
    audit_log = ctx.orch_dir / "pD-audit-1.log"
    audit_log.write_text(audit_out, "utf-8")

    # Check review verdict from parsed D1Result
    review_says_fail = d1.verdict == "FAIL"
    if not review_says_fail and d1.scores.get("overall", 10) < 9.0:
        review_says_fail = True
    # Fallback: check prose markers if D1Result didn't parse verdict
    if not d1.verdict:
        _status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
        _score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
        if _status_m and _status_m.group(1) == "FAIL":
            review_says_fail = True
        elif _score_m and float(_score_m.group(1)) < 9.0:
            review_says_fail = True

    if review_says_fail:
        log(f"  D.1: Review verdict: FAIL")
    else:
        log(f"  D.1: Review verdict: PASS")

    # Fast path: D.1 PASS + audit PASS → done
    if passed and not review_says_fail:
        log("  Phase D: PASS (D.1 review sufficient — no repair needed)")
        _mark_phase_v3(ctx, state, phase, "complete", attempts=1, note="d1-only")
        mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
        mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
        return True

    # Audit fails but review passes — let D.2 try to fix audit issues.
    # Review PASS means the content is structurally sound (sections present, activities work,
    # vocab adequate). Audit failures at this point are fixable: pedagogy violations, word count
    # shortfalls, transliteration, engagement counts, etc.
    _audit_only_d2 = False  # When True, D.2 fixes audit failures only (review said PASS)
    if not passed and not review_says_fail:
        # Log what's failing for diagnostics
        fail_lines = [l.strip() for l in audit_out.split("\n")
                      if "❌" in l and "AUDIT FAILED" not in l][:5]
        log(f"  D.1: Audit FAIL but review PASS — proceeding to D.2 for audit-only fixes")
        for line in fail_lines:
            log(f"    {line}")
        review_says_fail = True  # Force D.2 entry
        _audit_only_d2 = True  # Flag: D.2 should fix audit failures only, not review issues

    if passed and review_says_fail:
        log("  D.1: Audit PASSED but review flags issues — proceeding to D.2 for repair")

    # Citation failure detection (#615)
    _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
    if any(f"\u274c [{tag}]" in audit_out for tag in _CITATION_FAILURES):
        log("  D.1: REVIEW QUALITY FAILURE — fabricated/unverified citations detected")
        log("  D.1: Deleting bad review (D.2 cannot fix a bad review)")
        if ctx.paths["review"].exists():
            ctx.paths["review"].unlink()
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="d1-citation-failure")
        return False

    # Pre-D.2 deterministic fix pass (#623)
    auto_fix_count = _run_deterministic_fixes(ctx)
    if auto_fix_count > 0:
        log(f"  D.2: Pre-triage auto-fix applied {auto_fix_count} fix(es) — re-auditing...")
        passed_after_autofix, audit_out_after = run_verify(ctx.paths["md"], content_only=False)
        if passed_after_autofix and not review_says_fail:
            log("  Phase D: PASS (deterministic fixes resolved all issues — zero LLM cost)")
            _mark_phase_v3(ctx, state, phase, "complete", attempts=1, note="d1-plus-autofix")
            mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
            return True
        audit_out = audit_out_after

    # Pre-D.2 triage: skip if all issues are diffuse
    if _all_issues_diffuse(audit_out):
        log("  D.2: SKIPPED — all remaining issues are diffuse (needs rebuild, not repair)")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="needs-rebuild-diffuse-issues")
        return False

    # Merge deterministic issues + review issues for D.2
    all_issues = screen.deterministic_issues + d1.issues
    targeted = [i for i in all_issues if i.get("type", "") not in _DIFFUSE_FAILURE_CODES]
    if not targeted and not review_says_fail:
        log("  D.2: No targeted issues found — marking needs-rebuild")
        _mark_phase_v3(ctx, state, phase, "failed", attempts=1, note="needs-rebuild-diffuse")
        return False

    # -----------------------------------------------------------------------
    # D.2: Targeted Repair (max 2 iterations, NO D.3 re-review)
    # -----------------------------------------------------------------------
    MAX_D2_ITERS = 2

    v3_fix_timeout = _get_fix_timeout(ctx.track, audit_only=_audit_only_d2)

    # Build fix plan once (constant across iterations — review_text doesn't change)
    if _audit_only_d2:
        fix_plan = (
            "**IMPORTANT: The D.1 review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions — they are informational only.**\n\n"
            "(Review omitted — verdict was PASS)\n"
        )
    else:
        fix_plan = _extract_fix_plan(review_text)

    for d2_iter in range(MAX_D2_ITERS):
        iter_suffix = "" if d2_iter == 0 else f" (iter {d2_iter + 1})"
        total_attempts = 2 + d2_iter

        log(f"  D.2{iter_suffix}: Dispatching targeted repair...")
        failures = _extract_audit_failures(audit_out) or "None (audit passed). Focus exclusively on the Fix Plan."

        prompt_file2 = ctx.orch_dir / f"phase-D-prompt-{2 + d2_iter}.md"
        if not fill_template(d2_template, ctx.orch_dir / "placeholders.yaml", prompt_file2):
            return False

        prompt2_text = prompt_file2.read_text("utf-8")
        prompt2_text = prompt2_text.replace("{EXTRACTED_FIX_PLAN}", fix_plan)
        prompt2_text = prompt2_text.replace("{INJECTED_AUDIT_FAILURES}", failures)
        prompt_file2.write_text(prompt2_text, "utf-8")

        ok2, raw_output2 = _dispatch_claude_phase(
            prompt_file2, f"Phase D.2{iter_suffix}",
            model=claude_model_D, timeout=v3_fix_timeout,
            allow_tools=["Read"],
        )
        if not ok2:
            log(f"  D.2{iter_suffix}: Dispatch FAILED")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=total_attempts,
                           note="d2-dispatch-failed")
            return False

        # Apply fixes with diff-size blocker (#623)
        if "===SECTION_FIX_START===" in raw_output2:
            content_before = ctx.paths["md"].read_text("utf-8")
            act_before: str | None = None
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                act_before = ctx.paths["activities"].read_text("utf-8")
            vp = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
            vocab_before: str | None = None
            if vp and vp.exists():
                vocab_before = vp.read_text("utf-8")

            n_md = _apply_find_replace_fixes(ctx.paths["md"], raw_output2)
            n_act = 0
            if ctx.paths.get("activities"):
                n_act = _apply_find_replace_fixes(ctx.paths["activities"], raw_output2)
            n_vocab = 0
            if vp and vp.exists():
                n_vocab = _apply_find_replace_fixes(vp, raw_output2)
            log(f"  D.2{iter_suffix}: Applied {n_md} content, {n_act} activity, {n_vocab} vocab fix(es)")

            fix_pair_count = raw_output2.count("FIND:") if "FIND:" in raw_output2 else 1
            content_after = ctx.paths["md"].read_text("utf-8")
            act_after: str | None = None
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                act_after = ctx.paths["activities"].read_text("utf-8")
            vocab_after: str | None = None
            if vp and vp.exists():
                vocab_after = vp.read_text("utf-8")

            changed_lines = _count_diff_lines(content_before, content_after)
            if act_before is not None and act_after is not None:
                changed_lines += _count_diff_lines(act_before, act_after)
            if vocab_before is not None and vocab_after is not None:
                changed_lines += _count_diff_lines(vocab_before, vocab_after)
            max_allowed = max(fix_pair_count * 25, 50)

            if changed_lines > max_allowed:
                log(f"  D.2{iter_suffix}: REJECTED — {changed_lines} lines changed "
                    f"(max {max_allowed} for {fix_pair_count} fix pairs)")
                ctx.paths["md"].write_text(content_before, "utf-8")
                if act_before is not None and ctx.paths.get("activities"):
                    ctx.paths["activities"].write_text(act_before, "utf-8")
                if vocab_before is not None and vp:
                    vp.write_text(vocab_before, "utf-8")
                _mark_phase_v3(ctx, state, phase, "failed", attempts=total_attempts,
                               note="d2-diff-too-large")
                return False

            log(f"  D.2{iter_suffix}: Fixes applied ({changed_lines} lines, {fix_pair_count} pairs)")
        else:
            log(f"  D.2{iter_suffix}: WARNING — no SECTION_FIX delimiters")
            (ctx.orch_dir / f"phase-D2-iter{d2_iter + 1}-raw.md").write_text(raw_output2, "utf-8")

        # Post-D.2 deterministic fixes + single audit (NO D.3 re-review)
        _run_deterministic_fixes(ctx)
        passed, loop_audit_out = run_verify(ctx.paths["md"], content_only=False)
        audit_log = ctx.orch_dir / f"pD-audit-{2 + d2_iter}.log"
        audit_log.write_text(loop_audit_out, "utf-8")

        if passed:
            note = f"d2-iter{d2_iter + 1}"
            # Tag D.2 modules for Phase F tracking
            is_seminar = ctx.track in _SEMINAR_TIMEOUT_TRACKS or ctx.track in SEMINAR_TRACKS
            if is_seminar:
                note += "-seminar-needs-phaseF"
            log(f"  Phase D: PASS (after D.1 + D.2 iter {d2_iter + 1})")
            _mark_phase_v3(ctx, state, phase, "complete", attempts=total_attempts, note=note)
            mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
            return True

        audit_out = loop_audit_out
        if d2_iter < MAX_D2_ITERS - 1:
            log(f"  D.2{iter_suffix}: Still FAIL — running another D.2 iteration...")

    log("  Phase D: EXHAUSTED — D.1 + D.2 repair iterations all insufficient")
    log("  Phase D: Module marked as NEEDS-REBUILD (use --rebuild to regenerate)")
    _mark_phase_v3(ctx, state, phase, "failed",
                   attempts=1 + MAX_D2_ITERS, note="needs-rebuild")
    return False


def phase_D_rescreen(ctx: ModuleContext, state: dict) -> bool:
    """Rescreen mode: D.0 screen → proofread.py --fix (Gemini Pro) → re-audit.

    For modules that already passed Phase D but need fixes for newly-added
    deterministic checks (e.g., new Russicism patterns, LLM filler detection).
    Uses Gemini Pro for repairs (tested best for proofreading, see #640).
    """
    log(f"  RESCREEN: Running D.0 deterministic screen on {ctx.slug}...")

    screen = _deterministic_screen(ctx)

    if screen.audit_passed and not screen.deterministic_issues:
        log("  RESCREEN: CLEAN — no issues found, audit passes")
        return True

    if not screen.deterministic_issues:
        if not screen.audit_passed:
            log("  RESCREEN: No deterministic issues but audit FAIL — needs full Phase D")
            return False
        log("  RESCREEN: CLEAN — no deterministic issues")
        return True

    # Report findings
    issue_summary: dict[str, int] = {}
    for iss in screen.deterministic_issues:
        t = iss.get("type", "UNKNOWN")
        issue_summary[t] = issue_summary.get(t, 0) + 1
    summary_str = ", ".join(f"{k}:{v}" for k, v in issue_summary.items())
    log(f"  RESCREEN: Found {len(screen.deterministic_issues)} issue(s): {summary_str}")

    if ctx.dry_run:
        log("  RESCREEN: DRY-RUN — would dispatch proofread.py --fix (Gemini Pro)")
        for iss in screen.deterministic_issues[:10]:
            log(f"    - [{iss.get('type')}] {iss.get('text', '')[:60]}")
        return True

    # Dispatch proofread.py --fix (Gemini Pro) for the actual repair
    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    log(f"  RESCREEN: Dispatching proofread.py --fix on {ctx.track} {module_num}...")

    proofread_cmd = [
        sys.executable, str(SCRIPTS_DIR / "proofread.py"),
        ctx.track, str(module_num), "--fix", "--no-mdx",
    ]
    try:
        result = subprocess.run(
            proofread_cmd, capture_output=True, text=True, timeout=300,
        )
        log(f"  RESCREEN: proofread.py exited with code {result.returncode}")
        if result.stdout:
            for line in result.stdout.strip().split("\n")[-10:]:
                log(f"    {line}")
    except subprocess.TimeoutExpired:
        log("  RESCREEN: proofread.py timed out (300s)")
        return False
    except Exception as e:
        log(f"  RESCREEN: proofread.py error: {e}")
        return False

    # Post-fix: run deterministic fixes + full audit
    _run_deterministic_fixes(ctx)
    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
    audit_log = ctx.orch_dir / "rescreen-audit.log"
    audit_log.write_text(audit_out, "utf-8")

    if passed:
        log("  RESCREEN: PASS (after proofread fix + audit)")
        return True

    log("  RESCREEN: FAIL — proofread fixes applied but audit still fails")
    log("  RESCREEN: Module may need full --force-phase D")
    for line in audit_out.strip().split("\n")[-5:]:
        log(f"    {line}")
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
        log("  review: SKIP (already complete)")
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

    # Inject computed metrics (richness, immersion, etc.) into placeholders
    metrics_f = _compute_audit_metrics(ctx)
    pf_text = prompt_file.read_text("utf-8")
    pf_text = _inject_metrics_into_prompt(pf_text, metrics_f)
    prompt_file.write_text(pf_text, "utf-8")

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
# V4 Phase Functions
# ---------------------------------------------------------------------------

_V4_TO_V3_PHASE_MAP: dict[str, list[str]] = {
    "research":   ["A", "2"],
    "content":    ["B", "3"],
    "activities": ["C", "5-enrich"],
}


# Empty v3 state — passed to v3 functions when called from v4 so they
# never see themselves as "complete" (v4 state is authoritative).
_V3_EMPTY_STATE: dict = {"phases": {}}


def _v3_state_for_delegation(ctx: ModuleContext) -> dict:
    """Load v3 state for delegating to v3 phase functions.

    Only used by run_pipeline_v3 (--v3 flag). v4 passes _V3_EMPTY_STATE instead.
    """
    return _load_state_v3(ctx)


def _clear_v3_phases_for_v4(ctx: ModuleContext, v4_phase_ids: list[str]) -> None:
    """Clear v3 state entries for phases being re-run via v4 --force-phase/--restart-from.

    When v4 forces a delegated phase (research/content/activities), the v3 state
    must also be cleared or phase_A/B/C_v3 will see it as complete and skip.
    """
    v3_ids_to_clear: list[str] = []
    for pid in v4_phase_ids:
        v3_ids_to_clear.extend(_V4_TO_V3_PHASE_MAP.get(pid, []))
    if not v3_ids_to_clear:
        return
    v3_state = _load_state_v3(ctx)
    phases = v3_state.get("phases", {})
    changed = False
    for v3id in v3_ids_to_clear:
        if v3id in phases:
            phases.pop(v3id)
            changed = True
    if changed:
        _save_state_v3(ctx, v3_state)


def phase_research_v4(ctx: ModuleContext, state: dict) -> bool:
    """v4 research = v3 Phase A (skip v3 state check — v4 state is authoritative)."""
    if _is_phase_v4_complete(ctx, "research", state):
        log("  research: SKIP (already complete)")
        return True
    result = phase_A_v3(ctx, _V3_EMPTY_STATE)
    if result:
        _mark_phase_v4(ctx, state, "research", "complete")
    return result


def phase_discover_v4(ctx: ModuleContext, state: dict) -> bool:
    """v4 discover — video/blog search. Always returns True (non-blocking)."""
    if _is_phase_v4_complete(ctx, "discover", state):
        log("  discover: SKIP (already complete)")
        return True
    if getattr(ctx, "skip_discover", False):
        log("  discover: SKIP (--skip-discover)")
        _mark_phase_v4(ctx, state, "discover", "complete", skipped=True)
        return True
    if ctx.dry_run:
        log("  discover: SKIP (dry-run)")
        return True

    from video_discovery import (
        run_discovery,
        write_discovery_yaml,
        format_discovery_for_template,
    )

    # Extract keywords from topic + vocabulary hints
    keywords = [ctx.topic_title]
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    if isinstance(vocab_hints, dict):
        keywords.extend(vocab_hints.get("required", [])[:5])
    elif isinstance(vocab_hints, list):
        keywords.extend(vocab_hints[:5])

    log(f"  discover: searching for videos (keywords: {keywords[:3]}...)")
    result = run_discovery(
        topic=ctx.topic_title,
        keywords=keywords,
        outline=ctx.content_outline,
        vocab=keywords[1:],  # skip topic title
        dispatch_fn=pipeline_lib.dispatch_gemini_raw,
        track=ctx.track,
    )

    discovery_path = ctx.orch_dir / "discovery.yaml"
    write_discovery_yaml(result, discovery_path)

    if result.error:
        log(f"  discover: completed with error: {result.error}")
    elif result.warning:
        log(f"  discover: {result.warning}")
    else:
        relevant = [v for v in result.videos if v.relevance_score >= 0.5]
        log(f"  discover: found {len(result.videos)} videos, {len(relevant)} relevant")

    # Append video refs to research file
    _append_discovery_to_research(ctx, result)

    _mark_phase_v4(ctx, state, "discover", "complete")
    return True  # always non-blocking


def _append_discovery_to_research(ctx: ModuleContext, result) -> None:
    """Append a ## Video Discovery section to the research file."""
    from video_discovery import DiscoveryResult
    if not isinstance(result, DiscoveryResult):
        return
    relevant = [v for v in result.videos if v.relevance_score >= 0.5]
    if not relevant:
        return
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        return
    lines = ["\n\n## Video Discovery\n"]
    for v in relevant:
        lines.append(f"- [{v.title}]({v.url}) ({v.channel}) — {v.relevance_note}")
    try:
        with open(research_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        log(f"  discover: failed to append to research: {e}")


def phase_content_v4(ctx: ModuleContext, state: dict) -> bool:
    """v4 content = v3 Phase B (skip v3 state check — v4 state is authoritative)."""
    if _is_phase_v4_complete(ctx, "content", state):
        log("  content: SKIP (already complete)")
        return True
    result = phase_B_v3(ctx, _V3_EMPTY_STATE)
    if result:
        _mark_phase_v4(ctx, state, "content", "complete")
    return result


def phase_activities_v4(ctx: ModuleContext, state: dict) -> bool:
    """v4 activities = v3 Phase C (skip v3 state check — v4 state is authoritative)."""
    if _is_phase_v4_complete(ctx, "activities", state):
        log("  activities: SKIP (already complete)")
        return True
    result = phase_C_v3(ctx, _V3_EMPTY_STATE)
    if result:
        _mark_phase_v4(ctx, state, "activities", "complete")
    return result


def phase_validate_v4(ctx: ModuleContext, state: dict) -> bool:
    """Validate: full deterministic checks + Gemini fix loop.

    Merges v3 audit + screen + D.0 + D.0.5 into one phase.
    Runs content_only=False (full audit including activities).
    """
    phase = "validate"
    # When review phase follows, skip the review gate in audit
    # (MISSING_REVIEW is expected — review phase creates the review file)
    _skip_review = getattr(ctx, "review", False) or getattr(ctx, "final_review", False)
    if _is_phase_v4_complete(ctx, phase, state):
        log("  validate: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  validate: DRY-RUN — would run full audit + screen + fix loop")
        return True

    # Check sidecar files exist (moved from phase_D_v3)
    act_path = ctx.paths.get("activities")
    vocab_path = ctx.paths.get("vocabulary")
    missing = []
    if act_path and not act_path.exists():
        missing.append(f"activities: {act_path.name}")
    if vocab_path and not vocab_path.exists():
        missing.append(f"vocabulary: {vocab_path.name}")
    if missing:
        log(f"  validate: BLOCKED — missing sidecar files: {', '.join(missing)}")
        return False

    # Auto-fix pass: apply deterministic fixes before any LLM call
    auto_fix_total = _run_deterministic_fixes(ctx)
    if auto_fix_total > 0:
        log(f"  validate: {auto_fix_total} deterministic fix(es) applied")

    def _log_screen(label: str, scr: DScreenResult) -> None:
        dc = len(scr.deterministic_issues)
        if scr.audit_passed and dc == 0:
            log(f"  validate: {label} — PASS")
        elif scr.audit_passed:
            log(f"  validate: {label} — audit PASS, {dc} deterministic issue(s)")
        elif dc > 0:
            log(f"  validate: {label} — audit FAIL, {dc} deterministic issue(s)")
        else:
            log(f"  validate: {label} — audit FAIL (gate violations, no deterministic issues)")

    # Initial screen (content_only=False — full audit including activities)
    screen = _deterministic_screen(ctx, skip_review=_skip_review)
    _log_screen("Initial", screen)

    if screen.audit_passed and not screen.deterministic_issues:
        _save_screen_result(ctx, screen)
        _mark_phase_v4(ctx, state, phase, "complete", attempts=0)
        _update_pipeline_status(ctx, "draft")
        return True

    # Gemini proofread (D.0.5 logic) — only when prose-related issues exist.
    # Skip proofread if only activity/schema/vocab issues (wasteful otherwise).
    _PROSE_ISSUE_TYPES = {"RUSSIANISM", "LLM_FILLER"}
    _PROSE_AUDIT_KEYWORDS = {"naturalness", "word_count", "immersion", "engagement", "euphony"}
    _has_prose_issues = any(
        i["type"] in _PROSE_ISSUE_TYPES for i in screen.deterministic_issues
    )
    if not _has_prose_issues and not screen.audit_passed:
        # Check audit output for prose-related gate failures
        _audit_lower = screen.audit_output.lower()
        _has_prose_issues = any(kw in _audit_lower for kw in _PROSE_AUDIT_KEYWORDS)
    if _has_prose_issues:
        module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
        log(f"  validate: Dispatching Gemini proofread+fix on {ctx.slug}...")
        proofread_cmd = [
            sys.executable, str(SCRIPTS_DIR / "proofread.py"),
            ctx.track, str(module_num), "--fix", "--no-mdx",
        ]
        try:
            proofread_result = subprocess.run(
                proofread_cmd, capture_output=True, text=True, timeout=300,
            )
            pf_lines = (proofread_result.stdout or "").strip().split("\n")
            pf_found = [l for l in pf_lines if "FOUND:" in l or "CLEAN:" in l or "Applied" in l]
            for line in pf_found[-3:]:
                log(f"    {line.strip()}")
        except subprocess.TimeoutExpired:
            log("  validate: proofread.py timed out (300s) — continuing")
        except Exception as e:
            log(f"  validate: proofread.py error: {e} — continuing")

        # Re-screen after proofread
        screen = _deterministic_screen(ctx, skip_review=_skip_review)
        _log_screen("Post-proofread", screen)

        if screen.audit_passed and not screen.deterministic_issues:
            _save_screen_result(ctx, screen)
            _mark_phase_v4(ctx, state, phase, "complete", attempts=0, note="proofread-fix")
            _update_pipeline_status(ctx, "draft")
            return True

    # Gemini fix loop (audit fix loop logic from phase_audit_v3)
    max_iters = getattr(ctx, "max_fix", None) or _max_audit_iters(ctx.track)
    content_path = ctx.paths["md"]

    for attempt in range(1, max_iters + 1):
        log(f"  validate: Fix attempt {attempt}/{max_iters}...")

        # Build fix prompt
        fix_prompt = _build_fix_prompt(ctx, screen.audit_output, content_only=False)
        fix_prompt_file = ctx.orch_dir / f"validate-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, "utf-8")

        # Dispatch Gemini fix
        fix_output = _gemini_output_path(ctx.slug, f"validate-fix{attempt}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"v4-{ctx.slug}-validate-fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
            timeout=TIMEOUT_FIX,
        )
        if not ok:
            log(f"  validate: Fix dispatch {attempt} failed")
            continue

        if fix_output.exists():
            fix_text = fix_output.read_text("utf-8")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)
                # Apply fixes to activities/vocab too (content_only=False)
                if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                    _apply_section_fixes(ctx.paths["activities"], fix_text)
                _vp = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
                if _vp and _vp.exists():
                    _apply_section_fixes(_vp, fix_text)

        # Deterministic fixes after LLM fix
        _run_deterministic_fixes(ctx)

        # Re-screen
        screen = _deterministic_screen(ctx, skip_review=_skip_review)

        if screen.audit_passed and not screen.deterministic_issues:
            _save_screen_result(ctx, screen)
            _mark_phase_v4(ctx, state, phase, "complete", attempts=attempt)
            _update_pipeline_status(ctx, "draft")
            return True

        if attempt >= max_iters:
            log(f"  validate: EXHAUSTED — {max_iters} fix attempts")
            # Try escalation to Claude
            if _escalate_fix(ctx, screen.audit_output, "validate", content_only=False):
                screen = _deterministic_screen(ctx, skip_review=_skip_review)
                _save_screen_result(ctx, screen)
                _mark_phase_v4(ctx, state, phase, "complete",
                               attempts=attempt, note="escalation-claude")
                _update_pipeline_status(ctx, "draft")
                return True
            _save_screen_result(ctx, screen)
            _mark_phase_v4(ctx, state, phase, "failed",
                           attempts=attempt, note="exhausted")
            _update_pipeline_status(ctx, "needs-manual-review")
            return False

    # Should not reach here, but save results for safety
    _save_screen_result(ctx, screen)
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


def phase_review_v4(ctx: ModuleContext, state: dict) -> bool:
    """Review: Claude structured review + up to 2 fix attempts.

    Loads cached screen results from validate phase.
    Claude reviews holistically (pedagogy, naturalness, accuracy).
    If FAIL: up to 2 Claude fix attempts, then re-validate.
    """
    phase = "review"
    if _is_phase_v4_complete(ctx, phase, state):
        log("  review: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  review: DRY-RUN — would dispatch Claude structured review")
        return True

    # Load cached screen results (with stale hash check)
    screen = _load_screen_result(ctx)
    if screen is None:
        log("  review: No cached screen — running fresh screen")
        screen = _deterministic_screen(ctx)

    # Template selection
    d1_template = PHASES_DIR / "phase-D1-structured-review.md"
    if not d1_template.exists():
        d1_template = PHASES_DIR / "phase-D1-evidence-review.md"
    d2_template = PHASES_DIR / "phase-D2-repair.md"
    if not d1_template.exists():
        log(f"  review: ERROR — D1 template not found: {d1_template}")
        return False
    if not d2_template.exists():
        log(f"  review: ERROR — D2 template not found: {d2_template}")
        return False

    claude_model = getattr(ctx, "claude_model_D", CLAUDE_MODEL_REVIEW)
    review_timeout = _get_review_timeout(ctx.track)

    # -----------------------------------------------------------------------
    # Claude structured review (D.1 logic)
    # -----------------------------------------------------------------------
    log(f"  review: Preparing structured review prompt...")

    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    track_calibration = _get_track_calibration(ctx.track, module_num)
    russicism_table = _get_russicism_table(ctx.track)

    prompt_file = ctx.orch_dir / "review-prompt.md"
    if not fill_template(d1_template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    # Inject all placeholders into prompt
    prompt_text = prompt_file.read_text("utf-8")
    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", screen.h2_sections)
    prompt_text = prompt_text.replace("{TRACK_CALIBRATION}", track_calibration or "(No track calibration available)")
    prompt_text = prompt_text.replace("{DETERMINISTIC_ISSUES}", _format_deterministic_issues(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{RUSSIANISM_TABLE}", russicism_table or "(No track-specific Russianism table available — use general checklist)")
    prompt_text = prompt_text.replace("{FILLER_PHRASES}", _format_filler_phrases(screen.deterministic_issues))

    # RAG primary source verification
    rag_context = _prefetch_rag_context(ctx)
    prompt_text = prompt_text.replace("{RAG_PRIMARY_SOURCES}", rag_context)

    # RAG word verification
    rag_word_context = _format_rag_verification(
        screen.rag_verify_stats, screen.rag_verify_not_found,
    )
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", rag_word_context)

    prompt_file.write_text(prompt_text, "utf-8")

    log(f"  review: Dispatching Claude review ({claude_model}, {review_timeout}s)...")
    log(f"    Metrics: {screen.metrics.get('COMPUTED_WORD_COUNT', '?')}w / "
        f"{screen.metrics.get('COMPUTED_WORD_TARGET', '?')}w, "
        f"{screen.metrics.get('COMPUTED_ACTIVITY_COUNT', '?')} activities, "
        f"immersion {screen.metrics.get('COMPUTED_IMMERSION_PERCENT', '?')}%")

    ok, raw_output = _dispatch_claude_phase(
        prompt_file, "Phase D.1",
        model=claude_model, timeout=review_timeout,
        allow_tools=["Read", "Grep", "Glob"],
    )
    if not ok:
        log("  review: Dispatch FAILED")
        _mark_phase_v4(ctx, state, phase, "failed", attempts=1, note="dispatch-failed")
        return False

    # Parse review
    d1 = _parse_d1_review(raw_output)

    if not d1.ok or not d1.raw_review:
        log("  review: WARNING — no REVIEW delimiters in output (retrying)")
        (ctx.orch_dir / "review-raw-output.md").write_text(raw_output, "utf-8")

        ok2, raw2 = _dispatch_claude_phase(
            prompt_file, "Phase D.1 (retry)",
            model=claude_model, timeout=review_timeout,
            allow_tools=["Read", "Grep", "Glob"],
        )
        if ok2:
            d1 = _parse_d1_review(raw2)

        if not d1.ok or not d1.raw_review:
            log("  review: Retry also failed — no delimiters")
            _mark_phase_v4(ctx, state, phase, "failed", attempts=1, note="no-review")
            return False

    review_text = d1.raw_review

    # Pre-save quality gate
    qg_ok, qg_reason = _quick_review_quality_gate(review_text, ctx.paths["md"])
    if not qg_ok:
        log(f"  review: REJECTED — {qg_reason}")
        (ctx.orch_dir / "review-rejected.md").write_text(review_text, "utf-8")
        _mark_phase_v4(ctx, state, phase, "failed", attempts=1, note="shallow-review")
        return False

    # Inject Reviewed-By metadata
    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** {claude_model}\n\n{review_text}"

    # Save review
    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
    log(f"  review: Review saved → {ctx.paths['review'].name}")

    # Deterministic fixes after review
    _run_deterministic_fixes(ctx)

    # Post-review audit
    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

    # Check review verdict
    review_says_fail = d1.verdict == "FAIL"
    if not review_says_fail and d1.scores.get("overall", 10) < 9.0:
        review_says_fail = True
    if not d1.verdict:
        _status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
        _score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
        if _status_m and _status_m.group(1) == "FAIL":
            review_says_fail = True
        elif _score_m and float(_score_m.group(1)) < 9.0:
            review_says_fail = True

    # Fast path: review PASS + audit PASS → done
    if passed and not review_says_fail:
        log("  review: PASS (no repair needed)")
        _mark_phase_v4(ctx, state, phase, "complete", attempts=1, note="review-only")
        _update_pipeline_status(ctx, "reviewed")
        mark_phase_locked(ctx, "6", "complete", note="v4-review")
        mark_phase_locked(ctx, "7-final", "complete", note="v4-review")
        return True

    # Citation failure detection
    _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
    if any(f"\u274c [{tag}]" in audit_out for tag in _CITATION_FAILURES):
        log("  review: REVIEW QUALITY FAILURE — fabricated/unverified citations")
        if ctx.paths["review"].exists():
            ctx.paths["review"].unlink()
        _mark_phase_v4(ctx, state, phase, "failed", attempts=1, note="citation-failure")
        return False

    # Pre-fix deterministic pass
    auto_fix_count = _run_deterministic_fixes(ctx)
    if auto_fix_count > 0:
        passed_after_autofix, audit_out = run_verify(ctx.paths["md"], content_only=False)
        if passed_after_autofix and not review_says_fail:
            _mark_phase_v4(ctx, state, phase, "complete", attempts=1, note="autofix")
            _update_pipeline_status(ctx, "reviewed")
            mark_phase_locked(ctx, "6", "complete", note="v4-review")
            mark_phase_locked(ctx, "7-final", "complete", note="v4-review")
            return True

    # Pre-fix triage: skip if all issues are diffuse
    if _all_issues_diffuse(audit_out):
        log("  review: SKIPPED fix — all issues are diffuse (needs manual review)")
        _mark_phase_v4(ctx, state, phase, "failed", attempts=1, note="needs-manual-review")
        _update_pipeline_status(ctx, "needs-manual-review")
        return False

    # Determine if D.2 should fix audit failures only (review said PASS)
    _audit_only_fix = not review_says_fail and not passed

    # -----------------------------------------------------------------------
    # Fix attempts (up to MAX_REVIEW_FIX_ITERS)
    # -----------------------------------------------------------------------
    fix_timeout = _get_fix_timeout(ctx.track, audit_only=_audit_only_fix)

    # Build fix plan once (constant across iterations — review_text doesn't change)
    if _audit_only_fix:
        fix_plan = (
            "**IMPORTANT: The review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions — they are informational only.**\n\n"
            "(Review omitted — verdict was PASS)\n"
        )
    else:
        fix_plan = _extract_fix_plan(review_text)

    for fix_iter in range(MAX_REVIEW_FIX_ITERS):
        iter_suffix = "" if fix_iter == 0 else f" (iter {fix_iter + 1})"
        total_attempts = 2 + fix_iter

        log(f"  review: Fix attempt {fix_iter + 1}/{MAX_REVIEW_FIX_ITERS}{iter_suffix}...")
        failures = _extract_audit_failures(audit_out) or "None (audit passed). Focus exclusively on the Fix Plan."

        prompt_file2 = ctx.orch_dir / f"review-fix-{fix_iter + 1}-prompt.md"
        if not fill_template(d2_template, ctx.orch_dir / "placeholders.yaml", prompt_file2):
            return False

        prompt2_text = prompt_file2.read_text("utf-8")
        prompt2_text = prompt2_text.replace("{EXTRACTED_FIX_PLAN}", fix_plan)
        prompt2_text = prompt2_text.replace("{INJECTED_AUDIT_FAILURES}", failures)
        prompt_file2.write_text(prompt2_text, "utf-8")

        ok2, raw_output2 = _dispatch_claude_phase(
            prompt_file2, f"Phase D.2{iter_suffix}",
            model=claude_model, timeout=fix_timeout,
            allow_tools=["Read"],
        )
        if not ok2:
            log(f"  review: Fix dispatch failed{iter_suffix}")
            _mark_phase_v4(ctx, state, phase, "failed",
                           attempts=total_attempts, note="fix-dispatch-failed")
            return False

        # Apply FIND/REPLACE fixes with diff-size blocker
        if "===SECTION_FIX_START===" in raw_output2:
            content_before = ctx.paths["md"].read_text("utf-8")
            act_before: str | None = None
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                act_before = ctx.paths["activities"].read_text("utf-8")
            vp = ctx.paths.get("vocab") or ctx.paths.get("vocabulary")
            vocab_before: str | None = None
            if vp and vp.exists():
                vocab_before = vp.read_text("utf-8")

            n_md = _apply_find_replace_fixes(ctx.paths["md"], raw_output2)
            n_act = 0
            if ctx.paths.get("activities"):
                n_act = _apply_find_replace_fixes(ctx.paths["activities"], raw_output2)
            n_vocab = 0
            if vp and vp.exists():
                n_vocab = _apply_find_replace_fixes(vp, raw_output2)
            log(f"  review: Applied {n_md} content, {n_act} activity, {n_vocab} vocab fix(es)")

            fix_pair_count = raw_output2.count("FIND:") if "FIND:" in raw_output2 else 1
            content_after = ctx.paths["md"].read_text("utf-8")
            act_after: str | None = None
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                act_after = ctx.paths["activities"].read_text("utf-8")
            vocab_after: str | None = None
            if vp and vp.exists():
                vocab_after = vp.read_text("utf-8")

            changed_lines = _count_diff_lines(content_before, content_after)
            if act_before is not None and act_after is not None:
                changed_lines += _count_diff_lines(act_before, act_after)
            if vocab_before is not None and vocab_after is not None:
                changed_lines += _count_diff_lines(vocab_before, vocab_after)
            max_allowed = max(fix_pair_count * 25, 50)

            if changed_lines > max_allowed:
                log(f"  review: REJECTED — {changed_lines} lines changed "
                    f"(max {max_allowed} for {fix_pair_count} fix pairs)")
                ctx.paths["md"].write_text(content_before, "utf-8")
                if act_before is not None and ctx.paths.get("activities"):
                    ctx.paths["activities"].write_text(act_before, "utf-8")
                if vocab_before is not None and vp:
                    vp.write_text(vocab_before, "utf-8")
                _mark_phase_v4(ctx, state, phase, "failed",
                               attempts=total_attempts, note="diff-too-large")
                _update_pipeline_status(ctx, "needs-manual-review")
                return False
        else:
            log(f"  review: WARNING — no SECTION_FIX delimiters{iter_suffix}")
            (ctx.orch_dir / f"review-fix-{fix_iter + 1}-raw.md").write_text(raw_output2, "utf-8")

        # Post-fix deterministic fixes + audit
        _run_deterministic_fixes(ctx)
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

        if passed:
            log(f"  review: PASS (after fix {fix_iter + 1})")
            _mark_phase_v4(ctx, state, phase, "complete",
                           attempts=total_attempts, note=f"fix-iter{fix_iter + 1}")
            _update_pipeline_status(ctx, "reviewed")
            mark_phase_locked(ctx, "6", "complete", note="v4-review")
            mark_phase_locked(ctx, "7-final", "complete", note="v4-review")
            return True

        if fix_iter < MAX_REVIEW_FIX_ITERS - 1:
            log(f"  review: Fix {fix_iter + 1} insufficient — trying again...")

    log("  review: EXHAUSTED — review + fix attempts all insufficient")
    _mark_phase_v4(ctx, state, phase, "failed",
                   attempts=2 + MAX_REVIEW_FIX_ITERS, note="needs-manual-review")
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


def phase_mdx_v4(ctx: ModuleContext) -> bool:
    """v4 mdx = v3 Phase E (MDX generation + lint)."""
    # Reset v2 MDX state so it regenerates
    ctx.state.get("phases", {}).pop("8", None)
    save_state(ctx)
    return phase_E_v3(ctx)


# ---------------------------------------------------------------------------
# V4 Pipeline Runner
# ---------------------------------------------------------------------------

PHASE_FUNCTIONS_V4: dict[str, Any] = {
    "research":   phase_research_v4,
    "discover":   phase_discover_v4,
    "content":    phase_content_v4,
    "activities": phase_activities_v4,
    "validate":   phase_validate_v4,
    "review":     phase_review_v4,
    "mdx":        phase_mdx_v4,
}


def run_pipeline_v4(ctx: ModuleContext, research_only: bool = False) -> bool:
    """Execute the v4 named-phase pipeline."""
    state = _load_state_v4(ctx)

    log(f"\nPipeline v4: named phases — {len(PHASE_SEQUENCE_V4)} phases")
    if ctx.dry_run:
        log("  (DRY-RUN — no dispatches)")
    log("")

    # Determine sequence
    has_review = getattr(ctx, "review", False)
    if research_only:
        sequence = ["research"]
    elif has_review:
        sequence = list(PHASE_SEQUENCE_V4)  # all phases including review
    else:
        sequence = [p for p in PHASE_SEQUENCE_V4 if p != "review"]  # RC mode

    # Print phase plan
    for phase_id in sequence:
        label = PHASE_LABELS_V4.get(phase_id, phase_id)
        skip_note = " [DONE]" if _is_phase_v4_complete(ctx, phase_id, state) else ""
        log(f"  {phase_id}: {label}{skip_note}")
    log("")

    # --force-phase: single phase only
    force_phase = ctx.force_phase
    if force_phase:
        force_key = force_phase.lower()
        if force_key not in PHASE_FUNCTIONS_V4:
            log(f"  ERROR: Unknown v4 phase '{force_phase}'. Valid: {', '.join(PHASE_SEQUENCE_V4)}")
            return False
        log(f"  --force-phase {force_key}: running only this phase")
        # Clear the v4 state for this phase
        phases = state.setdefault("phases", {})
        for sid in _V4_PHASE_STATE_IDS.get(force_key, []):
            phases.pop(sid, None)
        _save_state_v4(ctx, state)
        # Also clear v3 state for delegated phases (research/content/activities)
        _clear_v3_phases_for_v4(ctx, [force_key])
        func = PHASE_FUNCTIONS_V4[force_key]
        return _call_phase_v4(func, force_key, ctx, state)

    # --restart-from: clear from this phase onward and run
    restart_from = getattr(ctx, "restart_from", None)
    if restart_from:
        restart_key = restart_from.lower()
        if restart_key not in PHASE_FUNCTIONS_V4:
            log(f"  ERROR: Unknown v4 phase '{restart_from}'. Valid: {', '.join(PHASE_SEQUENCE_V4)}")
            return False
        idx = PHASE_SEQUENCE_V4.index(restart_key)
        remaining = PHASE_SEQUENCE_V4[idx:]
        # Filter out review if not requested
        if not has_review:
            remaining = [p for p in remaining if p != "review"]
        # Clear state for restarted phases (v4 + v3 delegation)
        _clear_v3_phases_for_v4(ctx, remaining)
        phases = state.setdefault("phases", {})
        for pid in remaining:
            for sid in _V4_PHASE_STATE_IDS.get(pid, []):
                phases.pop(sid, None)
        _save_state_v4(ctx, state)
        log(f"  --restart-from {restart_key}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            if not _call_phase_v4(PHASE_FUNCTIONS_V4[phase_id], phase_id, ctx, state):
                if phase_id in ("validate", "review", "discover"):
                    log(f"  {phase_id}: FAIL — continuing")
                    continue
                log(f"\n  PIPELINE STOPPED at {phase_id}")
                return False
        return True

    # --stop-before
    stop_before = getattr(ctx, "stop_before_v4", None)

    # Full pipeline
    for phase_id in sequence:
        if stop_before and phase_id == stop_before:
            log(f"\n  Stopping before {phase_id}")
            return True

        func = PHASE_FUNCTIONS_V4[phase_id]
        if not _call_phase_v4(func, phase_id, ctx, state):
            if phase_id in ("validate", "review", "discover"):
                log(f"  {phase_id}: FAIL — continuing")
                continue
            log(f"\n  PIPELINE STOPPED at {phase_id}")
            return False

        if research_only and phase_id == "research":
            log("\n  --research-only: research complete, stopping")
            return True

    return True


def _call_phase_v4(func: Any, phase_id: str, ctx: ModuleContext,
                   state: dict) -> bool:
    """Call a v4 phase function."""
    if phase_id == "mdx":
        return func(ctx)
    else:
        return func(ctx, state)


# ---------------------------------------------------------------------------
# V3 Pipeline Runner (legacy)
# ---------------------------------------------------------------------------

PHASE_FUNCTIONS_V3: dict[str, Any] = {
    "A":     phase_A_v3,        # (ctx, state)
    "B":     phase_B_v3,        # (ctx, state)
    "C":     phase_C_v3,        # (ctx, state)
    "audit": phase_audit_v3,    # (ctx, state)
    "D":     phase_D_v3,        # (ctx, state)
    "E":     phase_E_v3,        # (ctx) — delegates to v2
    "F":     phase_F_v3,        # (ctx) — delegates to v2
}


def run_pipeline_v3(ctx: ModuleContext, research_only: bool = False) -> bool:
    """Execute the v3 optimised pipeline."""
    state = _load_state_v3(ctx)

    # Layer 3: One-time v2→v3 state migration (skipped on --force-phase and --rebuild)
    if not ctx.force_phase and not getattr(ctx, "refresh", False):
        _migrate_v2_state_to_v3(ctx, state)

    # Revalidate audit+D against current rules (catches stale state from old runs)
    _validate_audit_state(ctx, state)

    log(f"\nPipeline v3: 4-call optimised — {len(PHASE_SEQUENCE_V3)} phases")
    if ctx.dry_run:
        log("  (DRY-RUN — no Gemini dispatches)")
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
        return _call_phase_func(func, force_key, ctx, state)

    # --restart-from
    restart_from = getattr(ctx, "restart_from", None)
    if restart_from:
        # Case-insensitive lookup: "audit" stays "audit", "A"/"a" → "A"
        _restart_key_map = {k.upper(): k for k in PHASE_SEQUENCE_V3}
        restart_key = _restart_key_map.get(str(restart_from).upper())
        if restart_key is None:
            log(f"  ERROR: Unknown v3 phase '{restart_from}'. Valid: {', '.join(PHASE_SEQUENCE_V3)}")
            return False
        idx = PHASE_SEQUENCE_V3.index(restart_key)
        remaining = PHASE_SEQUENCE_V3[idx:]
        # Clear state for restarted phases
        phases = state.setdefault("phases", {})
        for pid in remaining:
            for sid in _V3_PHASE_STATE_IDS.get(pid, []):
                phases.pop(sid, None)
        _save_state_v3(ctx, state)
        log(f"  --restart-from {restart_key}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            if not _call_phase_func(PHASE_FUNCTIONS_V3[phase_id], phase_id, ctx, state):
                log(f"\n  PIPELINE STOPPED at phase {phase_id}")
                return False
        # Don't fall through to MDX here — handled below
        return _run_final_phases(ctx, state)

    # Full pipeline
    # MDX (Phase E) is always deferred to after all other phases including F
    stop_after = getattr(ctx, "stop_after", None)
    stopped = False  # tracks whether we've passed the stop-after phase

    phases_run = []
    for phase_id in PHASE_SEQUENCE_V3:
        # --stop-before / --stop-after: don't start phases past the cutoff
        if stopped:
            log(f"\n  Stopping: skipping phase {phase_id} ({PHASE_LABELS_V3.get(phase_id, phase_id)})")
            break

        func = PHASE_FUNCTIONS_V3[phase_id]
        if not _call_phase_func(func, phase_id, ctx, state):
            log(f"\n  PIPELINE STOPPED at phase {phase_id}")
            return False
        phases_run.append(phase_id)

        # --research-only: stop after Phase A
        if research_only and phase_id == "A":
            log("\n  --research-only: Phase A complete, stopping")
            return True

        if stop_after and phase_id == stop_after:
            stopped = True

    if stopped:
        log(f"\n  Pipeline stopped: completed phases {' → '.join(phases_run)}")
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
            # Deterministic fixes before checking — Phase F may have introduced violations
            n_postF = _run_deterministic_fixes(ctx)
            if n_postF > 0:
                log(f"  Phase F: {n_postF} deterministic fix(es) applied")

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
    save_state(ctx)
    return phase_E_v3(ctx)


def _call_phase_func(func: Any, phase_id: str, ctx: ModuleContext,
                     state: dict) -> bool:
    """Call a v3 phase function with the right signature."""
    if phase_id in ("E", "F"):
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
    ctx.research_only = getattr(args, "research_only", False)  # type: ignore[attr-defined]
    # --stop-before D  → internally means "stop after audit" (the phase before D)
    # --stop-after C   → deprecated alias, means "stop after C" (audit is skipped)
    _sb = (getattr(args, "stop_before", None) or "").upper() or None
    _sa = (getattr(args, "stop_after", None) or "").upper() or None
    _is_v4 = not getattr(args, "use_v3", False)
    if _sb and _sa:
        log("  ERROR: --stop-before and --stop-after are mutually exclusive")
        raise SystemExit(1)
    if _sb and not _is_v4:
        # v3 mode: Convert --stop-before X → stop after the phase preceding X
        # Case-insensitive lookup matching PHASE_SEQUENCE_V3 keys
        _all_phases = PHASE_SEQUENCE_V3 + ["E", "F"]
        _sb_key_map = {k.upper(): k for k in _all_phases}
        _sb = _sb_key_map.get(_sb.upper(), _sb)
        _all_upper = [p.upper() for p in _all_phases]
        if _sb.upper() not in _all_upper:
            log(f"  ERROR: Unknown phase '{_sb}'. Valid phases: {', '.join(_all_phases)}")
            raise SystemExit(1)
        idx = _all_upper.index(_sb.upper())
        if idx == 0:
            log(f"  ERROR: --stop-before {_sb} would skip all phases")
            raise SystemExit(1)
        _sa = _all_phases[idx - 1]  # phase before the specified one
    elif _sa:
        if _sa == "AUDIT":
            _sa = "audit"
    ctx.stop_after = _sa  # type: ignore[attr-defined]

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


def preflight_v4(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan/meta, set v4-specific attributes."""
    # Reuse v3 preflight for common setup (paths, plan, meta, models)
    ctx = preflight_v3(args)

    # Override mode
    ctx.mode = "v4"  # type: ignore[attr-defined]
    ctx.state["mode"] = "v4"

    # v4-specific flags
    ctx.review = getattr(args, "review", False)  # type: ignore[attr-defined]
    ctx.skip_discover = getattr(args, "skip_discover", False)  # type: ignore[attr-defined]

    # --stop-before for v4 (named phases)
    sb = getattr(args, "stop_before", None)
    if sb:
        sb_lower = sb.lower()
        if sb_lower not in PHASE_FUNCTIONS_V4:
            log(f"  ERROR: Unknown v4 phase '{sb}'. Valid: {', '.join(PHASE_SEQUENCE_V4)}")
            raise SystemExit(1)
        ctx.stop_before_v4 = sb_lower  # type: ignore[attr-defined]
    else:
        ctx.stop_before_v4 = None  # type: ignore[attr-defined]

    # --restart-from for v4
    rf = getattr(args, "restart_from", None)
    if rf:
        ctx.restart_from = rf.lower()  # type: ignore[attr-defined]

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
        description="E2E Module Builder v4 — named-phase pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Pipeline v4 phases: research → content → activities → validate → [review] → mdx

            Examples:
              %(prog)s a1 12                            # RC mode (no Claude review)
              %(prog)s a1 12 --review                   # Full mode (with Claude review)
              %(prog)s hist 5 --review                  # Seminar + review
              %(prog)s a1 --all                         # Build entire track (RC)
              %(prog)s a1 --range 1-20                  # Build range
              %(prog)s hist --all --research-only       # Pre-seed all research
              %(prog)s a1 12 --rebuild                  # Nuke state, restart
              %(prog)s a1 12 --dry-run                  # Show plan, no dispatches
              %(prog)s a1 12 --verify                   # Just audit
              %(prog)s a1 12 --force-phase validate     # Re-run validate only
              %(prog)s a1 12 --force-phase review       # Re-run review only
              %(prog)s a1 12 --restart-from review      # Run: review → mdx
              %(prog)s a1 12 --stop-before review       # Run: research→content→activities→validate→mdx
              %(prog)s a1 12 --max-fix 7                # Override fix iterations
              %(prog)s a1 12 --v3                       # Use legacy v3 pipeline
        """),
    )
    parser.add_argument("track", help="Track identifier (a1, a2, b1, ..., bio, hist, ...)")
    parser.add_argument("num", type=int, nargs="?", default=None,
                        help="1-indexed module number (optional with --all or --range)")

    parser.add_argument("--all", action="store_true", dest="build_all",
                        help="Build all modules in the track sequentially")
    parser.add_argument("--range", type=str, default=None, dest="build_range",
                        help="Build a range of modules (e.g. 1-20)")
    parser.add_argument("--rebuild", action="store_true",
                        help="Nuke state and rebuild from research")
    parser.add_argument("--force-phase", type=str, default=None,
                        help="Re-run a single phase (research/content/activities/validate/review/mdx)")
    parser.add_argument("--restart-from", type=str, default=None,
                        help="Restart from a phase (e.g. --restart-from review)")
    parser.add_argument("--force-research", action="store_true",
                        help="Force fresh research even if research file exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show plan without dispatching")
    parser.add_argument("--refresh", action="store_true",
                        help="Regenerate prose from updated research")
    parser.add_argument("--verify", action="store_true",
                        help="Just run audit, print PASS/FAIL, exit")
    parser.add_argument("--research-only", action="store_true", dest="research_only",
                        help="Run research phase only")
    parser.add_argument("--skip-discover", action="store_true", dest="skip_discover",
                        help="Skip video/blog discovery phase")
    parser.add_argument("--review", action="store_true",
                        help="Include Claude review phase (default: RC mode without review)")
    parser.add_argument("--stop-before", type=str, default=None, dest="stop_before",
                        help="Stop before this phase (e.g. --stop-before validate)")
    parser.add_argument("--stop-after", type=str, default=None, dest="stop_after",
                        help="(v3 compat) Stop after this phase")
    parser.add_argument("--final-review", action="store_true", dest="final_review",
                        help="(v3 compat) Alias for --review")
    parser.add_argument("--final-review-agent", type=str, default="claude",
                        choices=["claude", "gemini"], dest="final_review_agent",
                        help="(v3 compat) Agent for final review")
    parser.add_argument("--use-claude", type=str, default="", dest="use_claude",
                        help="Phases to run via Claude instead of Gemini (e.g. 'A', 'C', 'A C')")
    parser.add_argument("--gemini-model", type=str, default=None, dest="gemini_model",
                        help="Override Gemini model for all phases")
    parser.add_argument("--claude-model-A", type=str, default=None, dest="claude_model_A",
                        help="Claude model for research")
    parser.add_argument("--claude-model-C", type=str, default=None, dest="claude_model_C",
                        help="Claude model for activities")
    parser.add_argument("--claude-model-D", type=str, default=None, dest="claude_model_D",
                        help="Claude model for review (default: claude-opus-4-6)")
    parser.add_argument("--claude-model-F", type=str, default=None, dest="claude_model_F",
                        help="(v3 compat) Claude model for final review")
    parser.add_argument("--max-fix", type=int, default=None, dest="max_fix",
                        help="Override max fix iterations (default: 6 core, 8 seminar)")
    parser.add_argument("--rescreen", action="store_true",
                        help="(v3 compat) Run deterministic screen + fix only")
    parser.add_argument("--v3", action="store_true", dest="use_v3",
                        help="Use legacy v3 pipeline instead of v4")

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
            _ver = "v3" if args.use_v3 else "v4"
            print(f"Building ALL {total} modules in {args.track} ({_ver})", flush=True)
        else:
            m = re.match(r"^(\d+)-(\d+)$", args.build_range)
            if not m:
                parser.error(f"Invalid range: {args.build_range!r} (expected N-M)")
            start, end = int(m.group(1)), int(m.group(2))
            if start < 1 or end > total or start > end:
                parser.error(f"Range {start}-{end} out of bounds (track has {total} modules)")
            nums = list(range(start, end + 1))
            print(f"Building {args.track} modules {start}-{end} ({len(nums)} modules, {_ver})", flush=True)

        passed_list, failed_list, skipped_list = [], [], []
        t0_batch = time.time()

        for i, n in enumerate(nums, 1):
            slug = slug_for_num(args.track, n)
            print(f"\n{'='*70}", flush=True)
            print(f"[{i}/{len(nums)}] {args.track} #{n} — {slug}", flush=True)
            print(f"{'='*70}", flush=True)

            # --rescreen batch: skip modules that don't have content yet
            if getattr(args, "rescreen", False):
                try:
                    paths = get_module_paths(args.track, slug)
                    if not paths["md"].exists():
                        print(f"  SKIP: no content file", flush=True)
                        skipped_list.append((n, slug))
                        continue
                except Exception:
                    print(f"  SKIP: could not resolve paths", flush=True)
                    skipped_list.append((n, slug))
                    continue

            # Layer 1: Tiered batch skip — avoid running full audit on v2-built modules
            # that already pass. Even if they fall through, Layer 2 guards prevent
            # Phase A/B/C from overwriting existing artifacts.
            if not args.rebuild and not args.force_phase and not getattr(args, "rescreen", False):
                try:
                    paths = get_module_paths(args.track, slug)
                    if paths["md"].exists():
                        # Tier 1: Full audit pass — cheapest check
                        full_passed, _ = run_verify(paths["md"], content_only=False)
                        if full_passed:
                            # Guard: don't skip if v3 Phase D is incomplete.
                            # A module can pass audit but have a failed/pending D
                            # (e.g. review saved from a prior failed attempt).
                            _v3d_incomplete = False
                            _orch_dir = paths["md"].parent / "orchestration" / slug
                            _state_file = _orch_dir / "state-v3.json"
                            if _state_file.exists():
                                import json as _json_check
                                _st = _json_check.loads(_state_file.read_text("utf-8"))
                                _d_info = _st.get("phases", {}).get("v3-D", {})
                                _d_status = _d_info.get("status")
                                if _d_status and _d_status != "complete":
                                    _v3d_incomplete = True
                                    print(f"  PARTIAL: audit passes but v3-D is '{_d_status}' — needs pipeline", flush=True)

                            if not _v3d_incomplete:
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
                research_only=args.research_only,
                review=getattr(args, "review", False) or getattr(args, "final_review", False),
                final_review=getattr(args, "final_review", False),
                final_review_agent=getattr(args, "final_review_agent", "claude"),
                use_claude=getattr(args, "use_claude", ""),
                claude_model_A=getattr(args, "claude_model_A", None),
                claude_model_C=getattr(args, "claude_model_C", None),
                claude_model_D=getattr(args, "claude_model_D", None),
                claude_model_F=getattr(args, "claude_model_F", None),
                max_fix=getattr(args, "max_fix", None),
                stop_before=getattr(args, "stop_before", None),
                stop_after=getattr(args, "stop_after", None),
                rescreen=getattr(args, "rescreen", False),
                use_v3=getattr(args, "use_v3", False),
                gemini_model=getattr(args, "gemini_model", None),
                skip_discover=getattr(args, "skip_discover", False),
            )
            rc = _run_single_module(single_args)
            if rc == 0:
                passed_list.append((n, slug))
            else:
                # Auto-rebuild: if review/D exhausted, attempt one rebuild.
                _rebuilt_ok = False
                if not args.rebuild:
                    try:
                        _rb_paths = get_module_paths(args.track, slug)
                        _rb_orch = _rb_paths["md"].parent / "orchestration" / slug
                        _needs_rebuild = False
                        # Check v4 state first
                        _rb_v4 = _rb_orch / "state-v4.json"
                        if _rb_v4.exists():
                            import json as _jrb
                            _rb_st = _jrb.loads(_rb_v4.read_text("utf-8"))
                            for phase_key in ("v4-review", "v4-validate"):
                                _ph = _rb_st.get("phases", {}).get(phase_key, {})
                                if _ph.get("note", "").startswith("needs-"):
                                    _needs_rebuild = True
                                    break
                        # Fallback: check v3 state
                        if not _needs_rebuild:
                            _rb_v3 = _rb_orch / "state-v3.json"
                            if _rb_v3.exists():
                                import json as _jrb
                                _rb_st = _jrb.loads(_rb_v3.read_text("utf-8"))
                                _rb_d = _rb_st.get("phases", {}).get("v3-D", {})
                                if _rb_d.get("note", "").startswith("needs-rebuild"):
                                    _needs_rebuild = True
                        if _needs_rebuild:
                            print(f"  AUTO-REBUILD: review exhausted — attempting rebuild...", flush=True)
                            rebuild_args = argparse.Namespace(**vars(single_args))
                            rebuild_args.rebuild = True
                            if _run_single_module(rebuild_args) == 0:
                                passed_list.append((n, slug))
                                print(f"  AUTO-REBUILD: SUCCESS", flush=True)
                                _rebuilt_ok = True
                            else:
                                print(f"  AUTO-REBUILD: FAILED — module needs manual attention", flush=True)
                    except Exception as _rbe:
                        print(f"  AUTO-REBUILD: error checking state — {_rbe}", flush=True)
                if not _rebuilt_ok:
                    failed_list.append((n, slug))
                    print("  FAILED — continuing to next module", flush=True)

        elapsed = time.time() - t0_batch
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        print(f"\n{'='*70}", flush=True)
        print(f"BATCH COMPLETE — {args.track} {_ver} [{elapsed_str}]", flush=True)
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
    """Run the pipeline for a single module. Returns 0 on success, 1 on failure.

    Uses v4 pipeline by default, v3 with --v3 flag.
    """
    use_v3 = getattr(args, "use_v3", False)

    # Compat: --final-review implies --review in v4
    if not use_v3 and getattr(args, "final_review", False):
        args.review = True

    try:
        # --rebuild: nuke state files
        if args.rebuild:
            slug = slug_for_num(args.track, args.num)
            paths = get_module_paths(args.track, slug)
            orch_dir = (paths.get("orchestration")
                        or CURRICULUM_DIR / "l2-uk-en" / args.track / "orchestration" / slug)
            for state_name in ("state-v4.json", "state-v3.json"):
                sf = orch_dir / state_name
                if sf.exists():
                    sf.unlink()
                    print(f"  --rebuild: cleared {state_name}", flush=True)

        if use_v3:
            ctx = preflight_v3(args)
        else:
            ctx = preflight_v4(args)
        _init_log(ctx.slug)
        write_placeholders(ctx)

        # --rescreen: v3 compat — D.0 screen + D.2 repair only
        if getattr(args, "rescreen", False):
            t0 = time.time()
            if use_v3:
                state = _load_state_v3(ctx)
                ok = phase_D_rescreen(ctx, state)
            else:
                # v4: --rescreen → --force-phase validate
                state = _load_state_v4(ctx)
                phases = state.setdefault("phases", {})
                for sid in _V4_PHASE_STATE_IDS.get("validate", []):
                    phases.pop(sid, None)
                _save_state_v4(ctx, state)
                ok = phase_validate_v4(ctx, state)
            elapsed = time.time() - t0
            elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
            if ok:
                log(f"\nRESCREEN: PASS — {ctx.slug} [{elapsed_str}]")
            else:
                log(f"\nRESCREEN: FAIL — {ctx.slug} [{elapsed_str}]")
            return 0 if ok else 1

        t0 = time.time()
        if use_v3:
            ok = run_pipeline_v3(
                ctx,
                research_only=getattr(ctx, "research_only", False),
            )
        else:
            ok = run_pipeline_v4(
                ctx,
                research_only=getattr(ctx, "research_only", False),
            )
        elapsed = time.time() - t0
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        write_completion_report_v2(ctx, ok)

        _ver = "v3" if use_v3 else "v4"
        if ok:
            if ctx.dry_run:
                log(f"\nDRY-RUN COMPLETE — would build {ctx.slug} in {_ver} mode [{elapsed_str}]")
            elif ctx.force_phase:
                log(f"\nVERDICT: PASS — phase {ctx.force_phase} complete [{elapsed_str}]")
            elif getattr(ctx, "research_only", False):
                log(f"\nVERDICT: PASS — research complete ({_ver}) [{elapsed_str}]")
            elif getattr(ctx, "stop_before_v4", None) or getattr(ctx, "stop_after", None):
                log(f"\nVERDICT: PARTIAL — stopped early ({_ver}) [{elapsed_str}]")
            else:
                passed, output = run_verify(ctx.paths["md"], content_only=False)
                if passed:
                    log(f"\nVERDICT: PASS — {ctx.slug} fully complete ({_ver}) [{elapsed_str}]")
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
