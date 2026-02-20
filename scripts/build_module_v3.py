#!/usr/bin/env python3
"""Deterministic E2E Module Builder v3 — Optimised 4-Call Pipeline.

v3 collapses multiple v2 phases into single Gemini calls, reducing round-trips
from 8-9 calls to 4 baseline (worst case 9 with fix iterations).

Pipeline:
    Phase A:  Research + Meta         (1 call) ← v2 phases 0, 0.5, 1
    Phase B:  Content                 (1 call) ← v2 phase 2 + track context
    Phase C:  Activities + Vocab      (1 call) ← v2 phases 4a+4b + track context
    Audit:    Prose+Enrichment audit  (0-3 fix calls)
    Phase D:  Review + Fix            (1-2 calls) ← v2 phases 6, 6b, 7
    Phase F:  Claude Final Review     (opt.) ← v2 phase 9
    Phase E:  MDX                     (0 LLM calls) ← ALWAYS LAST

Baseline: 4 Gemini calls. Worst case: 4 + 3 audit fixes + 2 Phase D retries = 9.
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
import re
import textwrap
import time
import sys
from pathlib import Path
from typing import Any

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
    _build_fix_prompt, _apply_section_fixes,
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
    "D":     "Adversarial Review + Fix",
    "E":     "MDX Generation (deterministic)",
    "F":     "Claude Final Review (QA Gate)",
}

MAX_AUDIT_FIX_ITERS = 3
MAX_D_ITERS = 2

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
        except Exception:
            pass
    return {"track": ctx.track, "slug": ctx.slug, "mode": "v3", "phases": {}}


def _save_state_v3(ctx: ModuleContext, state: dict) -> None:
    import json
    sf = _state_file_v3(ctx)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2, ensure_ascii=False), "utf-8")


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
# Claude headless dispatch (Phase A and C via Claude CLI)
# ---------------------------------------------------------------------------

CLAUDE_MODEL_ACTIVITIES = "claude-sonnet-4-6"   # Phase C default
CLAUDE_MODEL_RESEARCH   = "claude-sonnet-4-6"   # Phase A default


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
    import subprocess
    claude_bin = shutil.which("claude") or "claude"
    env = __import__("os").environ.copy()
    env.pop("CLAUDECODE", None)  # Prevent nested-session error

    prompt = prompt_file.read_text("utf-8")
    # Adapt persona — templates say "You are Gemini"
    prompt = prompt.replace("You are Gemini", "You are Claude")

    cmd = [claude_bin, "--model", model, "-p", prompt, "--output-format", "text"]
    if allow_tools:
        cmd.extend(["--allowedTools", ",".join(allow_tools)])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
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
    if _is_phase_v3_complete(ctx, phase, state):
        # Health-check the existing meta — if sections are oversized, silently re-run
        if _meta_has_oversized_sections(ctx):
            log("  Phase A: Meta health check FAILED — oversized section detected, re-running")
            _mark_phase_v3(ctx, state, phase, "pending", note="health-check-reset")
        else:
            log("  Phase A: SKIP (already complete)")
            return True

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

    if ok:
        _mark_phase_v3(ctx, state, phase, "complete")
    else:
        _mark_phase_v3(ctx, state, phase, "failed")
    return ok


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
        log(f"  Phase C: WARNING — activities={wrote_activities}, vocab={wrote_vocab}")

    # Also mark v1 state IDs so downstream phases don't regenerate
    mark_phase_locked(ctx, "3a", "complete", note="v3-phase-C")
    mark_phase_locked(ctx, "3b", "complete", note="v3-phase-C")

    _mark_phase_v3(ctx, state, phase, "complete", task_id=f"v3-{ctx.slug}-pC")
    return True


# ---------------------------------------------------------------------------
# Audit loop (combined prose + enrichment)
# ---------------------------------------------------------------------------

def phase_audit_v3(ctx: ModuleContext, state: dict) -> bool:
    """Audit loop: runs prose/enrichment audit (content_only), dispatches fixes.

    Combines v2's Phase 3 (prose) and Phase 5 (enrichment) into one loop.
    Max 3 iterations. Uses run_verify (content_only=True) — skips review gate
    since the review file doesn't exist yet (Phase D creates it).
    """
    phase = "audit"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  Audit: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  Audit: DRY-RUN — would run audit loop")
        return True

    for attempt in range(1, MAX_AUDIT_FIX_ITERS + 1):
        if attempt == 1:
            log("  Audit: Initial full audit...")
        else:
            log(f"  Audit: Audit after fix {attempt - 1}/{MAX_AUDIT_FIX_ITERS - 1}...")

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

        if attempt >= MAX_AUDIT_FIX_ITERS:
            log(f"  Audit: EXHAUSTED — {MAX_AUDIT_FIX_ITERS - 1} fix attempts")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=attempt)
            return False

        # Dispatch fix
        fix_num = attempt
        fix_prompt = _build_fix_prompt(ctx, output, content_only=True)
        fix_prompt_file = ctx.orch_dir / f"pAudit-fix{fix_num}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, "utf-8")

        log(f"  Audit: Dispatching fix {fix_num}/{MAX_AUDIT_FIX_ITERS - 1}...")
        fix_output = _gemini_output_path(ctx.slug, f"pAudit-fix{fix_num}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"v3-{ctx.slug}-pAudit-fix{fix_num}",
            model=ctx.model, allow_write=True, output_file=fix_output,
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
# Phase D: Adversarial Review + Fix (combined)
# ---------------------------------------------------------------------------

def phase_D_v3(ctx: ModuleContext, state: dict) -> bool:
    """Phase D: Adversarial review + inline fixes in one call, then re-audit.

    Max 2 iterations. Each iteration:
    1. Dispatch phase-D-review-fix.md
    2. Extract REVIEW → save to review file
    3. Apply SECTION_FIX if present
    4. Re-audit
    5. If passed → done; else retry (max 2 total)
    """
    phase = "D"
    if _is_phase_v3_complete(ctx, phase, state):
        log("  Phase D: SKIP (already complete)")
        return True

    template = PHASES_DIR / "phase-D-review-fix.md"
    if not template.exists():
        log(f"  Phase D: ERROR — template not found: {template}")
        return False

    if ctx.dry_run:
        log("  Phase D: DRY-RUN — would dispatch phase-D-review-fix.md")
        return True

    for attempt in range(1, MAX_D_ITERS + 1):
        log(f"  Phase D: Dispatching review+fix (attempt {attempt}/{MAX_D_ITERS})...")

        prompt_file = ctx.orch_dir / f"phase-D-prompt-{attempt}.md"
        if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
            return False

        output_file = _gemini_output_path(ctx.slug, f"pD-{attempt}")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v3-{ctx.slug}-pD-{attempt}",
            model=ctx.model, stdout_only=True, output_file=output_file,
        )
        if not ok:
            log(f"  Phase D: Dispatch failed (attempt {attempt})")
            if attempt == MAX_D_ITERS:
                _mark_phase_v3(ctx, state, phase, "failed", attempts=attempt)
                return False
            continue

        # Extract review → save
        review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
        if review_text:
            ctx.paths["review"].parent.mkdir(parents=True, exist_ok=True)
            ctx.paths["review"].write_text(review_text, "utf-8")
            (ctx.orch_dir / f"phase-D-review-{attempt}.md").write_text(review_text, "utf-8")
            log(f"  Phase D: Review saved → {ctx.paths['review'].name}")
        else:
            log(f"  Phase D: WARNING — no REVIEW delimiters (attempt {attempt})")

        # Apply fixes if present
        if "===SECTION_FIX_START===" in raw_output:
            _apply_section_fixes(ctx.paths["md"], raw_output)
            # Also apply to activities file (phase-D-review-fix.md can fix both)
            if ctx.paths.get("activities"):
                _apply_section_fixes(ctx.paths["activities"], raw_output)
            log(f"  Phase D: Section fixes applied")

        # Re-audit
        log(f"  Phase D: Re-auditing after attempt {attempt}...")
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
        audit_log = ctx.orch_dir / f"pD-audit-{attempt}.log"
        audit_log.write_text(audit_out, "utf-8")

        if passed:
            log(f"  Phase D: PASS (attempt {attempt})")
            _mark_phase_v3(ctx, state, phase, "complete", attempts=attempt)
            # Mark v2 review + final audit phases as done too
            mark_phase_locked(ctx, "6", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "6b", "complete", note="v3-phase-D")
            mark_phase_locked(ctx, "7-final", "complete", note="v3-phase-D")
            return True

        if attempt == MAX_D_ITERS:
            log(f"  Phase D: EXHAUSTED — {MAX_D_ITERS} attempts, audit still failing")
            _mark_phase_v3(ctx, state, phase, "failed", attempts=attempt)
            return False

        log(f"  Phase D: Audit failed after attempt {attempt} — retrying review+fix")

    return False


# ---------------------------------------------------------------------------
# Phase E: MDX (always last — delegates to v2)
# ---------------------------------------------------------------------------

def phase_E_v3(ctx: ModuleContext) -> bool:
    """Phase E: MDX generation + lint. Delegates to v2's phase_8_mdx."""
    return phase_E_v3_delegate(ctx)


# ---------------------------------------------------------------------------
# Phase F: Claude Final Review (optional — delegates to v2)
# ---------------------------------------------------------------------------

def phase_F_v3(ctx: ModuleContext) -> bool:
    """Phase F: Claude final QA gate. Delegates to v2's phase_9_final_review."""
    return phase_F_v3_delegate(ctx)


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
    # Phase F: Claude Final Review (optional)
    if getattr(ctx, "final_review", False):
        log(f"\n  Phase F: {PHASE_LABELS_V3['F']}")
        if not phase_F_v3(ctx):
            log("\n  PIPELINE STOPPED at phase F (REJECT verdict)")
            return False

        # Post-F audit fix loop: Phase F may apply fixes that break compliance.
        # Run up to 2 additional Gemini fix iterations to repair any regressions.
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
    ctx.claude_model_F = getattr(args, "claude_model_F", None) or "claude-opus-4-6"    # type: ignore[attr-defined]

    # --rebuild forces Phase B to regenerate even if content file exists
    if getattr(args, "rebuild", False):
        ctx.refresh = True  # type: ignore[attr-defined]

    # Copy restart_from if not already set by v2 preflight
    if not hasattr(ctx, "restart_from"):
        ctx.restart_from = getattr(args, "restart_from", None)  # type: ignore[attr-defined]

    return ctx


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
    parser.add_argument("--claude-review", action="store_true", dest="claude_review",
                        help="Use Claude API for Phase D review instead of Gemini")
    parser.add_argument("--final-review", action="store_true", dest="final_review",
                        help="Run Phase F: Claude final QA gate after Phase D")
    parser.add_argument("--use-claude", type=str, default="", dest="use_claude",
                        help="Phases to run via Claude instead of Gemini (e.g. 'A', 'C', 'A C'). "
                             "A=research, C=activities. --final-review (Phase F) always uses Claude.")
    parser.add_argument("--claude-model-A", type=str, default=None, dest="claude_model_A",
                        help=f"Claude model for Phase A/research (default: sonnet for core, opus for seminar)")
    parser.add_argument("--claude-model-C", type=str, default=None, dest="claude_model_C",
                        help=f"Claude model for Phase C/activities (default: sonnet for core, opus for seminar)")
    parser.add_argument("--claude-model-F", type=str, default=None, dest="claude_model_F",
                        help="Claude model for Phase F/final-review (default: claude-opus-4-6)")

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

            # Skip already-complete unless --rebuild
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
                    pass

            single_args = argparse.Namespace(
                track=args.track, num=n,
                build_all=False, build_range=None,
                rebuild=args.rebuild, force_phase=args.force_phase,
                restart_from=getattr(args, "restart_from", None),
                force_research=args.force_research, dry_run=args.dry_run,
                refresh=args.refresh, verify=False,
                no_track_context=args.no_track_context,
                research_only=args.research_only,
                claude_review=getattr(args, "claude_review", False),
                final_review=getattr(args, "final_review", False),
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
                passed_co, _ = run_verify(content_path, content_only=True)
                if passed_co:
                    print(f"CONTENT-COMPLETE: {slug} (activities still needed)", flush=True)
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
