#!/usr/bin/env python3
"""Pipeline v5 — Clean pipeline implementation (no v2/v3 legacy code).

Phase implementations + state management + all phase-specific helpers.
Imported by build_module_v5.py.

Pipeline: research → discover → content → activities → validate → [review] → mdx

State file: state.json (plain phase keys, mode: "v5").
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Imports from pipeline_lib (shared utilities — never duplicated)
# ---------------------------------------------------------------------------
import contextlib

import pipeline_lib
from batch_gemini_config import (
    CLAUDE_MODEL_CORE_ACTIVITIES,
    CLAUDE_MODEL_CORE_RESEARCH,
    CLAUDE_MODEL_FINAL_REVIEW,
    PHASES_DIR,
    PRO_MODEL,
    PRO_TRACKS,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
)
from pipeline_lib import (
    FileLock,
    ModuleContext,
    _dispatch_prompt,
    _gemini_output_path,
    _get_activities_template,
    # Tier-based prompt dispatch
    _get_prompt_tier,
    _get_scoring_output_table,
    # Scoring helpers (for Gemini review)
    _get_scoring_section,
    _now_iso,
    _run_with_heartbeat,
    # Thread-safe locks
    _state_lock,
    # Validation
    _validate_activities_yaml,
    # Bilingual section titles
    bilingualify_section_titles,
    # Dispatch + logging
    dispatch_gemini,
    # Fix-prompt helpers moved to pipeline_v5.py (section 2b)
    fill_template,
    log,
    # Phase B content (archive check + fallback to phase_2_content)
    phase_B_content,
    # Phase helpers
    run_verify,
    save_gemini_session,
    # Preflight + completion
    write_review_with_hash,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_AUDIT_FIX_ITERS_CORE = 6
MAX_AUDIT_FIX_ITERS_SEMINAR = 8
MAX_REVIEW_FIX_ITERS = 2

# Dispatch timeouts (seconds)
TIMEOUT_CONTENT = 600
TIMEOUT_CONTENT_SELFAUDIT = 1200  # 20 min: generate + audit + fix in one session
TIMEOUT_ACTIVITIES = 600
TIMEOUT_FIX = 600
TIMEOUT_REVIEW = 900

# Claude model defaults — sourced from batch_gemini_config (single source of truth)
CLAUDE_MODEL_ACTIVITIES = CLAUDE_MODEL_CORE_ACTIVITIES
CLAUDE_MODEL_RESEARCH = CLAUDE_MODEL_CORE_RESEARCH
CLAUDE_MODEL_REVIEW = CLAUDE_MODEL_FINAL_REVIEW

ESCALATION_MODEL_CLAUDE = CLAUDE_MODEL_FINAL_REVIEW
ESCALATION_MODEL_GEMINI = PRO_MODEL

# Track-aware timeouts
TIMEOUT_REVIEW_CORE = 600
TIMEOUT_REVIEW_SEMINAR = 750
TIMEOUT_FIX_CORE = 600
TIMEOUT_FIX_SEMINAR = 600
TIMEOUT_FIX_AUDIT_ONLY = 600

# Seminar tracks that get longer timeouts
_SEMINAR_TIMEOUT_TRACKS = {"hist", "istorio", "bio", "lit", "oes", "ruth"}

# Audit failure codes that indicate diffuse issues (not FIND/REPLACE fixable)
_DIFFUSE_FAILURE_CODES = {
    "ROBOTIC_STRUCTURE",
    "STRUCTURAL_MONOTONY",
    "CONTENT_REDUNDANCY",
    "EXCESSIVE_METAPHOR",
    "THEORY_FRONTLOADING",
    "LOW_IMMERSION",
}

# Phase sequence
PHASES = ["research", "discover", "sandbox", "content", "activities", "validate", "review", "mdx"]

PHASE_LABELS: dict[str, str] = {
    "research":   "Research + Meta",
    "discover":   "Discover (video + blog search)",
    "sandbox":    "Lexical Sandbox (VESUM-validated word bank)",
    "content":    "Content (prose)",
    "activities": "Activities + Vocab",
    "validate":   "Validate (audit + screen + Gemini fix)",
    "review":     "Review (Gemini/Claude, optional)",
    "mdx":        "MDX Generation",
}

# Non-blocking phases (failures don't stop the pipeline)
NON_BLOCKING = {"validate", "review", "discover", "sandbox"}

# Research constants
_RESEARCH_EXISTS_MIN_WORDS = 500
_META_SECTION_MAX_PCT = 0.25

# Calibration directory
_CALIBRATION_DIR = Path(__file__).resolve().parent.parent / "claude_extensions" / "phases" / "calibration"


# ============================================================================
# 1. State Management (~100 lines)
# ============================================================================

def _state_file(ctx: ModuleContext) -> Path:
    return ctx.orch_dir / "state.json"


def load_state(ctx: ModuleContext) -> dict:
    """Load v5 state with fallback: state.json → state-v5.json (migrate) → state-v4.json (migrate) → fresh.

    v3/v2 states are ignored — those modules start fresh in v5.
    """
    # 1. state.json — authoritative
    sf = _state_file(ctx)
    if sf.exists():
        try:
            data = json.loads(sf.read_text("utf-8"))
            # Only accept v5 state files (mode == "v5"), skip legacy state.json
            if data.get("mode") == "v5":
                return data
            # Legacy state.json — back up and remove so we don't re-parse every run
            legacy_backup = sf.with_suffix(".legacy.json")
            sf.rename(legacy_backup)
            logger.debug("state.json mode=%s (not v5) — moved to %s",
                         data.get("mode"), legacy_backup.name)
        except Exception as e:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = sf.with_suffix(f".corrupted.{ts}.json")
            sf.rename(backup)
            logger.warning(
                "state.json corrupted for %s/%s — backed up to %s, resetting. Error: %s",
                ctx.track, ctx.slug, backup.name, e,
            )

    # 2. state-v5.json — migrate (rename to state.json)
    sf_v5_legacy = ctx.orch_dir / "state-v5.json"
    if sf_v5_legacy.exists():
        try:
            data = json.loads(sf_v5_legacy.read_text("utf-8"))
            sf_v5_legacy.unlink()
            log("  State migration: state-v5.json → state.json (old file removed)")
            return data
        except Exception as e:
            logger.warning("state-v5.json unreadable for %s/%s: %s — trying v4",
                           ctx.track, ctx.slug, e)

    # 3. state-v4.json — migrate (strip "v4-" prefixes from phase keys)
    sf_v4 = ctx.orch_dir / "state-v4.json"
    if sf_v4.exists():
        try:
            v4_data = json.loads(sf_v4.read_text("utf-8"))
            return _migrate_v4_to_v5(v4_data, ctx)
        except Exception as e:
            logger.warning("state-v4.json unreadable for %s/%s: %s — starting fresh",
                           ctx.track, ctx.slug, e)

    # 4. Anything else — fresh state
    return _fresh_state(ctx)


def _fresh_state(ctx: ModuleContext) -> dict:
    return {"track": ctx.track, "slug": ctx.slug, "mode": "v5", "phases": {}}


def _migrate_v4_to_v5(v4_data: dict, ctx: ModuleContext) -> dict:
    """Strip 'v4-' prefixes from phase keys to produce v5 state."""
    v5_state = {
        "track": v4_data.get("track", ctx.track),
        "slug": v4_data.get("slug", ctx.slug),
        "mode": "v5",
        "phases": {},
    }
    v4_phases = v4_data.get("phases", {})
    for key, value in v4_phases.items():
        # Strip "v4-" prefix if present
        clean_key = key[3:] if key.startswith("v4-") else key
        v5_state["phases"][clean_key] = value

    n_migrated = len(v5_state["phases"])
    if n_migrated > 0:
        log(f"  State migration: v4→v5 — migrated {n_migrated} phase(s)")
    return v5_state


def save_state(ctx: ModuleContext, state: dict) -> None:
    """Atomically write state.json."""
    sf = _state_file(ctx)
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


def is_complete(state: dict, phase_id: str) -> bool:
    """Check if a phase is marked complete in v5 state."""
    info = state.get("phases", {}).get(phase_id, {})
    return info.get("status") == "complete"


def _mark_phase(state: dict, phase_id: str, ctx: ModuleContext, status: str, **extra: Any) -> None:
    """Mark a phase status in v5 state (thread-safe via file lock)."""
    lock = _state_lock or FileLock(str(_state_file(ctx)) + ".lock")
    with lock:
        phases = state.setdefault("phases", {})
        phases[phase_id] = {"status": status, "ts": _now_iso(), **extra}
        save_state(ctx, state)


def mark_complete(state: dict, phase_id: str, ctx: ModuleContext, **extra: Any) -> None:
    """Mark a phase as complete in v5 state."""
    _mark_phase(state, phase_id, ctx, "complete", **extra)


def mark_failed(state: dict, phase_id: str, ctx: ModuleContext, **extra: Any) -> None:
    """Mark a phase as failed in v5 state."""
    _mark_phase(state, phase_id, ctx, "failed", **extra)


# ============================================================================
# 2. Shared helpers
# ============================================================================

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DScreenResult:
    """Result of deterministic screen — collects all pre-LLM findings."""
    metrics: dict[str, str]
    deterministic_issues: list[dict] = field(default_factory=list)
    audit_passed: bool = False
    audit_output: str = ""
    h2_sections: str = ""
    vesum_stats: dict = field(default_factory=dict)
    vesum_not_found: list[dict] = field(default_factory=list)


@dataclass
class D1Result:
    """Parsed result of D.1 Markdown review."""
    ok: bool
    issues: list[dict] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    verdict: str = ""
    raw_review: str = ""


# ---------------------------------------------------------------------------
# LLM filler scanner
# ---------------------------------------------------------------------------

_LLM_FILLER_DEFS: list[tuple[str, bool]] = [
    (r"\bIt'?s worth noting that\b", False),
    (r"\bThis is particularly important because\b", False),
    (r"\binterestingly\b", False),
    (r"\bOne of the key aspects\b", False),
    (r"\bLet'?s explore\b", False),
    (r"\bLet'?s dive in\b", False),
    (r"\bLet'?s take a closer look\b", False),
    (r"\bIn this lesson,? we will\b", True),
    (r"\bIn this module,? we will\b", True),
    (r"\bIn this (?:lesson|module|section),? we (?:will|are going to) (?:explore|learn|discover)\b", True),
    (r"\bIt is important to note\b", False),
    (r"\bNumbers are everywhere\b", False),
    (r"\bLanguage is not just about\b", False),
    (r"\bAs we'?ve seen\b", False),
    (r"\bAs you can see\b", False),
    (r"\bIn conclusion\b", False),
    (r"\bTo summarize\b", False),
    (r"\bThis brings us to\b", False),
    (r"\bце не просто\b.*?\bа й\b", False),
    (r"\bдавайте розглянемо\b", False),
    (r"\bдавайте дізнаємося\b", False),
    (r"\bцікаво,?\s+що\b", False),
    (r"\bварто зазначити,?\s+що\b", False),
    (r"\bдзеркало\s+культури\b", False),
    (r"\bархітектура\s+мови\b", False),
    (r"\bдвигун\s+прогресу\b", False),
]
_LLM_FILLER_COMPILED: list[tuple[re.Pattern, bool]] = [
    (re.compile(p, re.IGNORECASE), always) for p, always in _LLM_FILLER_DEFS
]


def _scan_llm_filler(content: str) -> list[dict]:
    """Scan content for LLM filler PATTERNS — repetition is the signal."""
    issues: list[dict] = []

    lines = content.split("\n")
    narrative_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(">") or stripped.startswith("```") or stripped.startswith("---"):
            continue
        narrative_lines.append((i + 1, line))

    narrative_text = "\n".join(line for _, line in narrative_lines)

    for pattern, always in _LLM_FILLER_COMPILED:
        matches = list(pattern.finditer(narrative_text))
        if len(matches) < 2 and not always:
            continue
        for m in matches:
            char_pos = m.start()
            narrative_idx = narrative_text[:char_pos].count("\n")
            if narrative_idx < len(narrative_lines):
                line_num = narrative_lines[narrative_idx][0]
            else:
                line_num = narrative_lines[-1][0] if narrative_lines else 1
            count_note = f" ({len(matches)}x)" if len(matches) >= 2 else ""
            issues.append({
                "type": "LLM_FILLER",
                "severity": "MEDIUM",
                "location": f"~line {line_num}",
                "text": m.group()[:80] + count_note,
                "fix": "Rephrase — this phrase appears repeatedly (LLM pattern)" if len(matches) >= 2
                       else "Rephrase — formulaic opener",
            })

    return issues


# ---------------------------------------------------------------------------
# Deterministic screen + fixes
# ---------------------------------------------------------------------------

_deterministic_fix_mtimes: dict[str, float] = {}


def _run_deterministic_fixes(ctx: ModuleContext) -> int:
    """Run all zero-cost deterministic fixes on a module's files."""
    total = 0
    content_path = ctx.paths.get("md")

    target_files = [
        content_path,
        ctx.paths.get("vocabulary"),
        ctx.paths.get("activities"),
    ]
    current_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    last_mtime = _deterministic_fix_mtimes.get(ctx.slug, 0.0)
    if current_max_mtime > 0 and current_max_mtime <= last_mtime:
        return 0

    # 1. Content text transforms — read once, apply all, write once
    if content_path and content_path.exists():
        try:
            text = content_path.read_text("utf-8")
            dirty = False

            # 1a. Euphony auto-fix
            try:
                from audit.checks.euphony import auto_fix_euphony
                text, n = auto_fix_euphony(text, str(content_path))
                if n > 0:
                    dirty = True
                    total += n
                    log(f"    Auto-fix: {n} euphony violation(s)")
            except Exception as e:
                logger.warning("Auto-fix: euphony failed: %s", e)

            # 1b. Demote extra H1 headings to H2
            # Exception: Summary/Підсумок MUST stay H1 (audit spec requires it)
            _H1_ALLOWED = {'summary', 'підсумок'}
            try:
                lines = text.split('\n')
                h1_count = 0
                changed = False
                in_code_block = False
                for i, line in enumerate(lines):
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        continue
                    if line.startswith('# ') and not line.startswith('## '):
                        h1_count += 1
                        if h1_count > 1:
                            # Don't demote sections that spec requires as H1
                            heading_text = line.lstrip('# ').strip().lower()
                            if heading_text not in _H1_ALLOWED:
                                lines[i] = '#' + line
                                changed = True
                if changed:
                    text = '\n'.join(lines)
                    dirty = True
                    total += 1
                    log("    Auto-fix: demoted extra H1 heading(s) to H2 (preserved Summary/Підсумок)")
            except Exception as e:
                logger.warning("Auto-fix: H1 demotion failed: %s", e)

            # 1c. Auto-correct H2 section titles to match content_outline
            try:
                if ctx.content_outline:
                    expected_titles = {
                        (s.get("section") or s.get("title", "")).strip(): (s.get("section") or s.get("title", "")).strip()
                        for s in ctx.content_outline if s.get("section") or s.get("title")
                    }
                    if expected_titles:
                        from difflib import SequenceMatcher

                        from audit.checks.outline_compliance import normalize_section_name
                        new_lines = text.split('\n')
                        in_cb = False
                        for i, ln in enumerate(new_lines):
                            if ln.strip().startswith('```'):
                                in_cb = not in_cb
                                continue
                            if in_cb:
                                continue
                            if ln.startswith('## ') and not ln.startswith('### '):
                                md_title = ln[3:].strip()
                                md_norm = normalize_section_name(md_title)
                                # Check if this title already matches an expected title
                                exact_match = any(
                                    normalize_section_name(et) == md_norm for et in expected_titles
                                )
                                if not exact_match:
                                    # Try fuzzy match
                                    best_score = 0.0
                                    best_expected = ""
                                    for et in expected_titles:
                                        score = SequenceMatcher(
                                            None, md_norm, normalize_section_name(et)
                                        ).ratio()
                                        if score > best_score:
                                            best_score = score
                                            best_expected = et
                                    if best_score >= 0.6 and best_expected:
                                        new_lines[i] = f"## {best_expected}"
                                        changed = True
                                        log(f"    Auto-fix: H2 title '{md_title}' → '{best_expected}' (similarity {best_score:.0%})")
                        if changed:
                            text = '\n'.join(new_lines)
                            dirty = True
                            total += 1
            except Exception as e:
                logger.warning("Auto-fix: H2 title correction failed: %s", e)

            # 1d. Strip IPA / phonetic brackets
            try:
                cleaned = re.sub(r' \[[^\]\n]{2,40}\] \(', ' (', text)
                if cleaned != text:
                    n_ipa = text.count('[') - cleaned.count('[')
                    text = cleaned
                    dirty = True
                    total += n_ipa
                    log(f"    Auto-fix: stripped {n_ipa} IPA/phonetic bracket(s)")
            except Exception as e:
                logger.warning("Auto-fix: IPA strip failed: %s", e)

            if dirty:
                content_path.write_text(text, "utf-8")
        except Exception as e:
            logger.warning("Auto-fix: content read failed: %s", e)

    # 2. YAML schema fixes (activities)
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

    # 3. YAML text-level fixes (vocab)
    vocab_path = ctx.paths.get("vocabulary")
    if vocab_path and vocab_path.exists():
        try:
            from audit.checks.yaml_schema_validation import fix_raw_yaml_text
            raw = vocab_path.read_text("utf-8")
            fixed, fix_msgs = fix_raw_yaml_text(raw)
            if fix_msgs:
                vocab_path.write_text(fixed, "utf-8")
                total += len(fix_msgs)
                log(f"    Auto-fix: {len(fix_msgs)} vocab YAML text fix(es) in {vocab_path.name}")
                for msg in fix_msgs[:3]:
                    log(f"      {msg[:120]}")
        except Exception as e:
            logger.warning("Auto-fix: vocab YAML fix failed", exc_info=True)
            log(f"    Auto-fix: vocab YAML fix failed: {e}")

    # 4. Forbidden activity removal
    if act_path and act_path.exists():
        try:
            from audit.checks.yaml_schema_validation import remove_forbidden_activities
            from audit.core import detect_focus, detect_level, load_yaml_meta
            meta_data = load_yaml_meta(str(content_path)) if content_path else {}
            if content_path and content_path.exists():
                content_path.read_text("utf-8")
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

    new_max_mtime = max(
        (p.stat().st_mtime for p in target_files if p and p.exists()),
        default=0.0,
    )
    _deterministic_fix_mtimes[ctx.slug] = new_max_mtime

    return total


def _deterministic_screen(ctx: ModuleContext, skip_review: bool = False) -> DScreenResult:
    """Run all deterministic checks before LLM review."""
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

    # Read content text once for steps 5, 6, 7.5
    content_text: str | None = None
    if content_path and content_path.exists():
        try:
            content_text = content_path.read_text("utf-8")
        except Exception as e:
            logger.warning("D.0: Failed to read content file: %s", e)

    # 5. Russicism regex scan
    if content_text is not None:
        try:
            from audit.checks.russicism_detection import check_russicisms
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
    if content_text is not None:
        try:
            filler_issues = _scan_llm_filler(content_text)
            result.deterministic_issues.extend(filler_issues)
        except Exception as e:
            logger.warning("D.0: LLM filler scan failed: %s", e)

    # 7. IPA / phonetic bracket scan
    if content_text is not None:
        _IPA_PATTERNS = [
            (re.compile(r'\[([a-z]+-)+[a-z]+\]'), "syllable breakdown"),
            (re.compile(r'\[[ɑɛɪɔʊəʃʒθðŋɾˈˌː\w\s]+\]'), "IPA transcription"),
        ]
        _IPA_WHITELIST = {"[Ø]"}
        for pattern, desc in _IPA_PATTERNS:
            matches = [m for m in pattern.finditer(content_text)
                       if m.group() not in _IPA_WHITELIST]
            if matches:
                for m in matches[:5]:
                    line_num = content_text[:m.start()].count('\n') + 1
                    result.deterministic_issues.append({
                        "type": "IPA_BANNED",
                        "severity": "HIGH",
                        "location": f"~line {line_num}",
                        "text": f"Banned {desc}: {m.group()[:60]}",
                        "fix": "Remove phonetic brackets. Use only stress marks (´) for pronunciation.",
                    })

    # 8. Word verification (VESUM only)
    if content_path and content_path.exists():
        try:
            from rag_batch_verify import verify_module as vesum_verify_module
            vesum_results, vesum_stats = vesum_verify_module(
                content_path, use_rag=False, skip_activities=False,
            )
            result.vesum_stats = vesum_stats
            result.vesum_not_found = [
                r for r in vesum_results if r["status"] in ("❌", "⚠️")
            ]
            n_not_found = vesum_stats.get("not_found", 0)
            n_partial = vesum_stats.get("rag_hits", 0)
            total_words = vesum_stats.get("total", 0)
            vesum_hits = vesum_stats.get("vesum_hits", 0)
            if n_not_found > 0 or n_partial > 0:
                log(f"  D.0: VESUM verify: {total_words} words, "
                    f"{vesum_hits} VESUM ✓, "
                    f"{n_partial} RAG-only ⚠️, {n_not_found} not found ❌")
            else:
                log(f"  D.0: VESUM verify: {total_words} words, "
                    f"100% VESUM coverage ✅")
            pct = (vesum_hits / total_words * 100) if total_words else 100
            result.audit_output += (
                f"\nVESUM: {vesum_hits}/{total_words} ({pct:.0f}%) verified"
            )
            if n_not_found > 0:
                not_found_words = [r["original"] for r in result.vesum_not_found
                                   if r["status"] == "❌"][:10]
                result.audit_output += (
                    f"\n⚠️ VESUM not found ({n_not_found}): "
                    + ", ".join(not_found_words)
                )
        except Exception as e:
            logger.warning("D.0: VESUM word verification failed: %s", e)

    # 7.5 Rule engine
    if content_text is not None:
        try:
            from audit.checks.rule_engine import run_rule_engine
            level_code = ctx.track.split("-")[0].upper()
            rule_issues = run_rule_engine(content_text, level_code, ctx.module_num, ctx.track)
            result.deterministic_issues.extend(rule_issues)
            if rule_issues:
                log(f"  D.0: Rule engine: {len(rule_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Rule engine failed: %s", e)

    # 7.6 VESUM morphological validator (tag-based grammar constraints)
    if content_text is not None:
        try:
            from audit.checks.morphological_validator import validate_morphology
            level_code = ctx.track.split("-")[0].upper() if "-" in ctx.track else ctx.track.upper()
            morph_issues = validate_morphology(
                content_text, level_code, ctx.module_num, ctx.track)
            result.deterministic_issues.extend(morph_issues)
            if morph_issues:
                log(f"  D.0: Morphological validator: {len(morph_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Morphological validator failed: %s", e)

    # 9. Content quality pipeline checks
    if content_text is not None:
        try:
            from audit.checks.content_quality_pipeline import run_content_quality_checks
            level_code = ctx.track.split("-")[0].upper() if "-" in ctx.track else ctx.track.upper()
            cq_issues = run_content_quality_checks(
                content=content_text,
                level_code=level_code,
                module_num=ctx.module_num,
                plan=getattr(ctx, "plan", None),
                activities_path=ctx.paths.get("activities"),
                vesum_not_found=result.vesum_not_found,
            )
            result.deterministic_issues.extend(cq_issues)
            if cq_issues:
                log(f"  D.0: Content quality: {len(cq_issues)} issue(s)")
        except Exception as e:
            logger.warning("D.0: Content quality checks failed: %s", e)

    det_count = len(result.deterministic_issues)
    if det_count > 0:
        n_rules = sum(1 for i in result.deterministic_issues if i["type"] in ("PEDAGOGICAL", "DECODABILITY"))
        n_cq = sum(1 for i in result.deterministic_issues if i["type"] in (
            "UNTRANSLATED_NON_DECODABLE", "WALL_OF_TEXT", "LOW_ENGAGEMENT",
            "REPETITIVE_TRANSITIONS", "PLAN_SECTION_MISSING", "ACTIVITY_VESUM_FAIL"))
        log(f"  D.0: {det_count} deterministic issue(s) found "
            f"({sum(1 for i in result.deterministic_issues if i['type'] == 'RUSSIANISM')} Russianisms, "
            f"{sum(1 for i in result.deterministic_issues if i['type'] == 'LLM_FILLER')} filler, "
            f"{n_rules} rule-engine, {n_cq} content-quality)")

    return result


# ---------------------------------------------------------------------------
# Screen result caching
# ---------------------------------------------------------------------------

def _compute_content_hash(ctx: ModuleContext) -> str:
    """Hash md + activities + vocab files for cache invalidation."""
    import hashlib
    h = hashlib.md5(usedforsecurity=False)
    for key in ("md", "activities", "vocabulary"):
        p = ctx.paths.get(key)
        if p and p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _save_screen_result(ctx: ModuleContext, screen: DScreenResult) -> None:
    """Save DScreenResult + content hash for review phase reuse."""
    import dataclasses
    data = dataclasses.asdict(screen)
    data["content_hash"] = _compute_content_hash(ctx)
    (ctx.orch_dir / "screen-result.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def _load_screen_result(ctx: ModuleContext) -> DScreenResult | None:
    """Load cached screen result, return None if stale or missing."""
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
    data.pop("content_hash", None)
    try:
        return DScreenResult(**data)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pipeline status propagation
# ---------------------------------------------------------------------------

def _update_pipeline_status(ctx: ModuleContext, pipeline_status: str) -> None:
    """Write pipeline_status into status/{slug}.json."""
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
# Module file helpers (snapshot, diff, apply fixes)
# ---------------------------------------------------------------------------

def _module_file_paths(ctx: ModuleContext) -> list[tuple[str, Path | None]]:
    """Return [(label, path)] for the three module files."""
    return [
        ("md", ctx.paths.get("md")),
        ("activities", ctx.paths.get("activities")),
        ("vocabulary", ctx.paths.get("vocabulary")),
    ]


def _snapshot_module_files(ctx: ModuleContext) -> dict[str, str]:
    """Snapshot content/activities/vocab before an edit pass."""
    snapshots = {}
    for label, p in _module_file_paths(ctx):
        if p and p.exists():
            snapshots[label] = p.read_text("utf-8")
    return snapshots


def _count_diff_lines(before: str, after: str) -> int:
    """Count the number of changed lines between two texts."""
    import difflib
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = list(difflib.unified_diff(before_lines, after_lines, n=0))
    return sum(1 for line in diff if line.startswith(('+', '-'))
               and not line.startswith(('+++', '---')))


def _log_d1_edits(ctx: ModuleContext, pre_snapshots: dict[str, str]) -> None:
    """Log what D.1 changed via Edit tool by diffing pre/post snapshots."""
    import difflib

    any_changes = False
    diff_lines: list[str] = []

    for label, p in _module_file_paths(ctx):
        old = pre_snapshots.get(label, "")
        if not p or not p.exists():
            continue
        new = p.read_text("utf-8")
        if old == new:
            continue

        any_changes = True
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{label} (before D.1)",
            tofile=f"{label} (after D.1)",
            n=1,
        ))
        n_changed = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        log(f"  D.1 edit: {label} — {n_changed} line(s) changed")
        diff_lines.extend(diff)

    if any_changes:
        diff_path = ctx.orch_dir / "d1-edits.diff"
        diff_path.write_text("".join(diff_lines), "utf-8")
        log(f"  D.1 edit: Full diff saved → {diff_path.name}")
    else:
        log("  D.1 edit: No file changes detected (Edit tool not used or all edits reverted)")


def _apply_module_fixes(ctx: ModuleContext, raw_output: str) -> int:
    """Apply FIND/REPLACE fix pairs from LLM output to all module files."""
    if "===SECTION_FIX_START===" not in raw_output:
        return 0
    total = 0
    for _label, p in _module_file_paths(ctx):
        if p and p.exists():
            total += _apply_find_replace_fixes(p, raw_output)
    return total


def _apply_fixes_with_rollback(
    ctx: ModuleContext, raw_output: str, log_prefix: str,
) -> tuple[bool, int]:
    """Apply FIND/REPLACE fixes with diff-size guard and rollback."""
    if "===SECTION_FIX_START===" not in raw_output:
        return True, 0

    before = _snapshot_module_files(ctx)
    n_fixes = _apply_module_fixes(ctx, raw_output)

    fix_pair_count = raw_output.count("FIND:") if "FIND:" in raw_output else 1
    after = _snapshot_module_files(ctx)

    changed_lines = 0
    for label in before:
        if label in after:
            changed_lines += _count_diff_lines(before[label], after[label])

    max_allowed = max(fix_pair_count * 25, 50)

    if changed_lines > max_allowed:
        log(f"  {log_prefix}: REJECTED — {changed_lines} lines changed "
            f"(max {max_allowed} for {fix_pair_count} fix pairs)")
        for label, p in _module_file_paths(ctx):
            if label in before and p:
                p.write_text(before[label], "utf-8")
        return False, n_fixes

    log(f"  {log_prefix}: Fixes applied ({changed_lines} lines, {fix_pair_count} pairs)")
    return True, n_fixes


# ---------------------------------------------------------------------------
# Clean fix text + FIND/REPLACE parser
# ---------------------------------------------------------------------------

def _clean_fix_text(text: str) -> str:
    """Strip LLM formatting artifacts from FIND/REPLACE text."""
    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        s = line.strip()
        if re.match(r'^Section:\s*["\u201c\u00ab]', s, re.IGNORECASE):
            continue
        if s.startswith("```"):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    if result.startswith("«") and result.endswith("»"):
        result = result[1:-1]
    if result.startswith("\u201e") and result.endswith("\u201c"):
        result = result[1:-1]
    return result


def _apply_find_replace_fixes(file_path: Path, raw_output: str) -> int:
    """Apply FIND/REPLACE fix pairs from D.2 output to a file."""
    if not file_path.exists():
        return 0

    fix_matches = re.findall(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        raw_output, re.DOTALL,
    )
    if not fix_matches:
        return 0

    fix_block = fix_matches[-1]

    current_file_active = True
    file_name = file_path.name
    pairs: list[tuple[str, str]] = []
    current_find: list[str] | None = None
    current_replace: list[str] | None = None
    mode = None

    for line in fix_block.split("\n"):
        stripped = line.strip()

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

        if stripped == "---":
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

        if mode == "find" and current_find is not None:
            current_find.append(line)
        elif mode == "replace" and current_replace is not None:
            current_replace.append(line)

    if current_find is not None and current_replace is not None:
        pairs.append(("\n".join(current_find), "\n".join(current_replace)))

    if not pairs:
        return 0

    content = file_path.read_text("utf-8")
    applied = 0
    skipped = []

    for i, (find_text, replace_text) in enumerate(pairs, 1):
        find_text = _clean_fix_text(find_text)
        replace_text = _clean_fix_text(replace_text)
        if not find_text or find_text == replace_text:
            skipped.append((i, "empty/identical", find_text[:60].replace('\n', ' ') if find_text else ""))
            continue

        if find_text in content:
            content = content.replace(find_text, replace_text, 1)
            applied += 1
            continue

        normalized_find = re.sub(r'\s+', ' ', find_text).strip()
        normalized_content = re.sub(r'\s+', ' ', content)
        if normalized_find in normalized_content:
            idx = normalized_content.index(normalized_find)
            char_count = 0
            orig_start = 0
            for i_ch, ch in enumerate(content):
                if char_count >= idx:
                    orig_start = i_ch
                    break
                if ch in (' ', '\t', '\n', '\r'):
                    if i_ch == 0 or content[i_ch-1] not in (' ', '\t', '\n', '\r'):
                        char_count += 1
                else:
                    char_count += 1
            end_count = 0
            orig_end = orig_start
            target_len = len(normalized_find)
            for i_ch in range(orig_start, len(content)):
                ch = content[i_ch]
                if ch in (' ', '\t', '\n', '\r'):
                    if i_ch == orig_start or content[i_ch-1] not in (' ', '\t', '\n', '\r'):
                        end_count += 1
                else:
                    end_count += 1
                if end_count >= target_len:
                    orig_end = i_ch + 1
                    break

            content = content[:orig_start] + replace_text + content[orig_end:]
            applied += 1
        else:
            find_preview = find_text[:60].replace('\n', ' ')
            skipped.append((i, "no match", find_preview))

    total_pairs = len(pairs)
    parts = [f"{applied}/{total_pairs} applied"]
    if skipped:
        parts.append(f"{len(skipped)} skipped")
    log(f"    FIND/REPLACE {file_path.name}: {', '.join(parts)}")
    for idx_s, reason, preview in skipped:
        log(f"      ⚠ #{idx_s} {reason}: {preview}...")
    if applied > 0:
        file_path.write_text(content, "utf-8")

    return applied


# ---------------------------------------------------------------------------
# Claude headless dispatch
# ---------------------------------------------------------------------------

def _dispatch_claude_phase(
    prompt_file: Path,
    phase_label: str,
    model: str = CLAUDE_MODEL_ACTIVITIES,
    timeout: int = 600,
    allow_tools: list[str] | None = None,
) -> tuple[bool, str]:
    """Call Claude CLI headlessly for a phase prompt file."""
    import shutil
    claude_bin = shutil.which("claude") or "claude"
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    prompt = prompt_file.read_text("utf-8")
    prompt = prompt.replace("You are Gemini", "You are Claude")

    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]
    if allow_tools:
        cmd.extend(["--allowedTools", ",".join(allow_tools)])

    _PHASE_DELIMITERS: dict[str, tuple[str, str]] = {
        "D.1":     ("===REVIEW_START===", "===REVIEW_END==="),
        "D.2":     ("===SECTION_FIX_START===", "===SECTION_FIX_END==="),
        "C vocab": ("===VOCABULARY_START===", "===VOCABULARY_END==="),
        "C":       ("===ACTIVITIES_START===", "===ACTIVITIES_END==="),
        "A":       ("===META_OUTLINE_START===", "===META_OUTLINE_END==="),
    }
    expected_start, expected_end = "===REVIEW_START===", "===REVIEW_END==="
    for key in ("D.2", "D.1", "C vocab", "C", "A"):
        if key in phase_label:
            expected_start, expected_end = _PHASE_DELIMITERS[key]
            break

    if "D.1" in phase_label:
        cmd.extend(["--append-system-prompt",
                     f"CRITICAL: Your output MUST contain {expected_start} and {expected_end} "
                     "delimiters wrapping the review, AND ===SECTION_FIX_START=== / ===SECTION_FIX_END=== "
                     "delimiters wrapping FIND/REPLACE fix pairs for every issue found. "
                     "Both blocks are required. Output without these delimiters is automatically discarded. "
                     "FIND/REPLACE FORMAT: The FIND text must be RAW file content copy-pasted from Read output. "
                     "Do NOT add Section/Line metadata headers, do NOT wrap in triple backticks, "
                     "do NOT add any framing text. Just the raw text that exists in the file."])
    elif "D.2" in phase_label and allow_tools:
        cmd.extend(["--append-system-prompt",
                     "You have Edit and Grep tools. Fix each issue by editing files directly. "
                     "Use Grep to verify text exists before editing. "
                     "Do NOT output FIND/REPLACE blocks — use the Edit tool instead. "
                     "After all fixes, output a ===FRICTION_START=== / ===FRICTION_END=== block "
                     "documenting any issues encountered."])
    else:
        cmd.extend(["--append-system-prompt",
                     f"CRITICAL: Your output MUST contain {expected_start} and {expected_end} "
                     "delimiters wrapping the full structured output. Output without these delimiters "
                     "is automatically discarded. Do NOT summarize — produce the FULL output requested."])

    try:
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
# Delimiter extraction
# ---------------------------------------------------------------------------

def _extract_delimiter(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiters. Anchors on LAST start tag."""
    s = text.rfind(start_tag)
    if s == -1:
        return None
    s += len(start_tag)
    e = text.find(end_tag, s)
    if e == -1:
        return None
    return text[s:e].strip()


def _extract_delimiter_tolerant(
    text: str, start_tag: str, end_tag: str, *, content_type: str = "yaml"
) -> str | None:
    """Extract delimited content, tolerating missing end tag."""
    exact = _extract_delimiter(text, start_tag, end_tag)
    if exact:
        return exact

    s = text.rfind(start_tag)
    if s == -1:
        return None

    s += len(start_tag)
    raw = text[s:]

    lines = raw.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("─") or stripped.startswith("✅") or stripped.startswith("✓"):
            break
        if stripped.startswith("===") and stripped.endswith("==="):
            break
        clean_lines.append(line)

    while clean_lines and not clean_lines[-1].strip():
        clean_lines.pop()

    candidate = "\n".join(clean_lines).strip()
    if not candidate:
        return None

    if content_type == "markdown":
        log(f"    Tolerant extraction (markdown): recovered {len(candidate)} chars (missing {end_tag})")
        return candidate

    import yaml
    try:
        parsed = yaml.safe_load(candidate)
        if parsed and isinstance(parsed, dict) and "items" in parsed:
            log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (missing {end_tag})")
            return candidate
    except yaml.YAMLError:
        last_good = -1
        for i, line in enumerate(clean_lines):
            if line.strip().startswith("- lemma:"):
                last_good = i
        if last_good > 0 and last_good > 1:
            for j in range(last_good, len(clean_lines)):
                ln = clean_lines[j].strip()
                if j > last_good and ln.startswith("- lemma:"):
                    break
            trimmed = "\n".join(clean_lines[:last_good]).strip()
            try:
                parsed = yaml.safe_load(trimmed)
                if parsed and isinstance(parsed, dict) and "items" in parsed:
                    log(f"    Tolerant extraction: recovered {len(parsed['items'])} vocab items (trimmed incomplete entry)")
                    return trimmed
            except yaml.YAMLError:
                pass

    return None


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def _compute_metrics_direct(ctx: ModuleContext) -> dict[str, str]:
    """Compute audit metrics WITHOUT running the audit subprocess."""
    import yaml
    from audit.cleaners import calculate_immersion, clean_for_immersion, clean_for_stats, extract_core_content

    metrics: dict[str, str] = {}
    content_path = ctx.paths.get("md")

    if content_path and content_path.exists():
        content = content_path.read_text("utf-8")
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

    vocab_path = ctx.paths.get("vocabulary")
    vocab_count = 0
    if vocab_path and vocab_path.exists():
        try:
            vocab_data = yaml.safe_load(vocab_path.read_text("utf-8"))
            if isinstance(vocab_data, list):
                vocab_count = len(vocab_data)
            elif isinstance(vocab_data, dict):
                vlist = vocab_data.get("vocabulary", vocab_data.get("items", []))
                if isinstance(vlist, list):
                    vocab_count = len(vlist)
        except Exception:
            pass
    metrics["COMPUTED_VOCAB_COUNT"] = str(vocab_count)

    engagement_pattern = re.compile(
        r'(>\s*[💡⚡🎬🎭📜⚔️🔗🌍🎁🗣️🏠🧭🚌🚇🎟️📱🕵️🌤️🌦️🎱🔮🇺🇦🕰️❓🛠️💂🥪🍺🛍️🏫🏥💊👵🔬🎨🔄📅🍃❄️🚂⏳📚🍲🥣🥗🥙🥚🥛🧩⚠️🛑🎯🎮🎓🔍])|'
        r'(>\s*\[!(note|tip|warning|caution|important|cultural|history-bite|myth-buster|quote|context|analysis|source|legacy|reflection|fact|culture|military|perspective|biography)\])'
    )
    engagement_count = len(engagement_pattern.findall(content))
    metrics["COMPUTED_ENGAGEMENT_COUNT"] = str(engagement_count)

    if body:
        imm_text = clean_for_immersion(body)
        immersion_pct = calculate_immersion(imm_text)
    else:
        immersion_pct = 0.0
    metrics["COMPUTED_IMMERSION_PERCENT"] = f"{immersion_pct:.1f}"

    from audit.config import get_a1_immersion_range, get_a2_immersion_range, get_b1_immersion_range
    level = ctx.track.split("-")[0].upper() if "-" not in ctx.track else ctx.track.upper()
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
            min_imm, max_imm = 85, 95
    except Exception:
        min_imm, max_imm = 80, 95
    metrics["COMPUTED_IMMERSION_TARGET"] = f"{min_imm}-{max_imm}%"

    if content_path and content_path.exists():
        try:
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
            raw_rich = richness.get("raw", {})
            targets = richness.get("targets", {})
            gaps = []
            for dim, target in targets.items():
                actual = raw_rich.get(dim, 0)
                if actual < target:
                    gaps.append(f"{dim}: {actual}/{target}")
            metrics["COMPUTED_RICHNESS_GAPS"] = ", ".join(gaps) if gaps else "none"
        except Exception:
            metrics["COMPUTED_RICHNESS_SCORE"] = "?"
            metrics["COMPUTED_RICHNESS_THRESHOLD"] = "?"
            metrics["COMPUTED_RICHNESS_GAPS"] = "?"

    return metrics



# ---------------------------------------------------------------------------
# H2 section extraction
# ---------------------------------------------------------------------------

def _extract_h2_sections(content_path: Path) -> str:
    """Extract all H2 headers from a content .md file as a numbered list."""
    if not content_path.exists():
        return "(content file not found)"
    text = content_path.read_text("utf-8")
    h2s = re.findall(r"^## (.+)$", text, re.MULTILINE)
    if not h2s:
        return "(no H2 sections found)"
    return "\n".join(f"{i}. {h}" for i, h in enumerate(h2s, 1))


# ---------------------------------------------------------------------------
# Audit failure extraction + formatting helpers
# ---------------------------------------------------------------------------

def _extract_audit_failures(audit_output: str) -> str:
    """Extract actionable failure lines from audit output."""
    lines = audit_output.strip().split("\n")
    failure_lines = []
    in_ped_section = False

    for line in lines:
        stripped = line.strip()

        if any(kw in stripped.upper() for kw in [
            "FAIL", "ERROR", "VIOLATION", "MISSING", "GATE",
            "ROBOTIC", "MONOTONY", "IMMERSION TOO", "SEVERITY",
        ]):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("❌") or stripped.startswith("🔴") or stripped.startswith("⚠️"):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("- **[") or stripped.startswith("- ["):
            failure_lines.append(stripped)
            continue

        if "IMMERSION" in stripped.upper() and ("LOW" in stripped.upper() or "HIGH" in stripped.upper()):
            failure_lines.append(stripped)
            continue

        if stripped.startswith("## PEDAGOGICAL") or stripped.startswith("## Low Density"):
            in_ped_section = True
            failure_lines.append(stripped)
            continue

        if in_ped_section:
            if stripped.startswith("## "):
                in_ped_section = False
            elif stripped:
                failure_lines.append(stripped)
                continue

    if not failure_lines:
        return "\n".join(lines[-40:])
    return "\n".join(failure_lines)


def _extract_gate_blockers(ctx: ModuleContext) -> str:
    """Read status JSON and extract blocking_issues as GATE BLOCKER lines."""
    try:
        status_path = ctx.paths.get("status")
        if not status_path or not status_path.exists():
            return ""
        data = json.loads(status_path.read_text("utf-8"))
        blockers = data.get("overall", {}).get("blocking_issues", [])
        if not blockers:
            return ""
        lines = ["", "--- STATUS JSON GATE BLOCKERS ---"]
        for b in blockers:
            lines.append(f"GATE BLOCKER: {b}")
        return "\n".join(lines)
    except Exception:
        return ""


def _extract_vesum_failures(ctx: ModuleContext) -> str:
    """Read screen-result.json and format VESUM not-found words."""
    try:
        f = ctx.orch_dir / "screen-result.json"
        if not f.exists():
            return ""
        data = json.loads(f.read_text("utf-8"))
        not_found = data.get("vesum_not_found", [])
        if not not_found:
            return ""
        lines = ["", "--- VESUM WORD VERIFICATION FAILURES ---"]
        lines.append("These words were NOT found in the VESUM morphological dictionary.")
        lines.append("Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.")
        for r in not_found[:20]:
            word = r.get("original", r.get("clean", "?"))
            source = r.get("source", "?")
            status = r.get("status", "?")
            lines.append(f"  {status} `{word}` (source: {source})")
        if len(not_found) > 20:
            lines.append(f"  ... and {len(not_found) - 20} more")
        return "\n".join(lines)
    except Exception:
        return ""


def _format_deterministic_issues(issues: list[dict]) -> str:
    """Format deterministic issues as text for prompt injection."""
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


def _format_vesum_verification(stats: dict, not_found: list[dict]) -> str:
    """Format VESUM word verification results for prompt injection."""
    if not stats:
        return "(VESUM word verification did not run — VESUM DB may be missing)"

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
        for r in not_found_words[:15]:
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


# ---------------------------------------------------------------------------
# Prompt injection helpers
# ---------------------------------------------------------------------------

def _inject_metrics_into_prompt(prompt_text: str, metrics: dict[str, str]) -> str:
    """Replace {COMPUTED_*} placeholders in a prompt with computed values."""
    for key, val in metrics.items():
        prompt_text = prompt_text.replace("{" + key + "}", val)
    return prompt_text


def _inject_file_contents(prompt_text: str, ctx: ModuleContext) -> str:
    """Inject module file contents into prompt, replacing placeholders."""
    content_path = ctx.paths.get("md")
    act_path = ctx.paths.get("activities")
    vocab_path = ctx.paths.get("vocabulary")

    content_text = content_path.read_text("utf-8") if content_path and content_path.exists() else "(file not found)"
    act_text = act_path.read_text("utf-8") if act_path and act_path.exists() else "(file not found)"
    vocab_text = vocab_path.read_text("utf-8") if vocab_path and vocab_path.exists() else "(file not found)"

    prompt_text = prompt_text.replace("{CONTENT_FILE_CONTENT}", content_text)
    prompt_text = prompt_text.replace("{ACTIVITIES_FILE_CONTENT}", act_text)
    prompt_text = prompt_text.replace("{VOCAB_FILE_CONTENT}", vocab_text)
    return prompt_text


# ---------------------------------------------------------------------------
# D.1 review parsing
# ---------------------------------------------------------------------------

def _parse_d1_review(raw_output: str) -> D1Result:
    """Parse D.1 Markdown review from delimiters."""
    review_text = _extract_delimiter(raw_output, "===REVIEW_START===", "===REVIEW_END===")
    if not review_text:
        review_text = _extract_delimiter_tolerant(
            raw_output, "===REVIEW_START===", "===REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    score = 0.0
    score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        score = float(score_m.group(1))

    scores: dict[str, float] = {}
    if score > 0:
        scores["overall"] = score

    scores_section = re.search(
        r'## Scores\s*\n(.*?)(?=\n## |\Z)',
        review_text,
        re.DOTALL,
    )
    if scores_section:
        dim_rows = re.findall(
            r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*([\d.]+)/10\s*\|',
            scores_section.group(1),
        )
        for dim_name, dim_score in dim_rows:
            key = dim_name.strip().lower().replace(" ", "_")
            with contextlib.suppress(ValueError):
                scores[key] = float(dim_score)

        weighted_m = re.search(
            r'\*\*Weighted Overall:\*\*.*?=\s*\*\*([\d.]+)/10\*\*',
            scores_section.group(1),
        )
        if weighted_m:
            with contextlib.suppress(ValueError):
                scores["weighted_overall"] = float(weighted_m.group(1))

    if not verdict and score > 0:
        verdict = "PASS" if score >= 9.0 else "FAIL"

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


def _parse_factual_review(raw_output: str) -> D1Result:
    """Parse Gemini Fact Checker output."""
    review_text = _extract_delimiter(raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===")
    if not review_text:
        review_text = _extract_delimiter_tolerant(
            raw_output, "===FACTUAL_REVIEW_START===", "===FACTUAL_REVIEW_END===",
            content_type="markdown",
        )

    if not review_text:
        return D1Result(ok=False, raw_review="", verdict="")

    verdict = ""
    status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
    if status_m:
        verdict = status_m.group(1)

    scores: dict[str, float] = {}
    score_m = re.search(r'\*\*Factual Alignment Score:\*\*\s*([\d.]+)/10', review_text)
    if score_m:
        scores["factual_accuracy"] = float(score_m.group(1))

    plan_m = re.search(r'\*\*Plan Adherence Score:\*\*\s*([\d.]+)/10', review_text)
    if plan_m:
        scores["plan_adherence"] = float(plan_m.group(1))

    plan_missing_m = re.search(r'(\d+)\s+missing', review_text[:500])
    plan_missing_count = int(plan_missing_m.group(1)) if plan_missing_m else 0

    disc_m = re.search(r'\*\*Discrepancies \[Tier 1\]:\*\*\s*(\d+)', review_text)
    discrepancy_count = int(disc_m.group(1)) if disc_m else 0

    re.search(r'\*\*Unverified:\*\*\s*(\d+)', review_text)

    issues: list[dict] = []

    missing_points = re.findall(
        r'- \[ \]\s+(?:Point \d+:\s*)?(.+?)(?:\s*—\s*MISSING)',
        review_text,
    )
    for pt_text in missing_points:
        issues.append({
            "type": "MISSING_PLAN_POINT",
            "severity": "MEDIUM",
            "text": pt_text.strip(),
        })

    disc_blocks = re.findall(
        r'### Discrepancy \d+:\s*(.+?)(?=### Discrepancy|\Z)',
        review_text,
        re.DOTALL,
    )
    for block in disc_blocks:
        issue: dict[str, str] = {"type": "FACTUAL_DISCREPANCY", "severity": "HIGH"}
        mod_m = re.search(r'\*\*Module says:\*\*\s*"(.+?)"', block)
        if mod_m:
            issue["text"] = mod_m.group(1).strip()
        ref_m = re.search(r'\*\*Reference says:\*\*\s*"(.+?)"', block)
        if ref_m:
            issue["reference"] = ref_m.group(1).strip()
        src_m = re.search(r'\*\*Source:\*\*\s*(.+)', block)
        if src_m:
            issue["source"] = src_m.group(1).strip()
        fix_m = re.search(r'\*\*Suggested fix:\*\*\s*(.+)', block)
        if fix_m:
            issue["fix"] = fix_m.group(1).strip()
        issues.append(issue)

    if not verdict:
        verdict = "FAIL" if discrepancy_count > 0 or plan_missing_count >= 3 else "PASS"

    return D1Result(
        ok=True,
        issues=issues,
        scores=scores,
        verdict=verdict,
        raw_review=review_text,
    )


# ---------------------------------------------------------------------------
# D.1 fix plan extraction
# ---------------------------------------------------------------------------

def _extract_fix_plan(review_text: str) -> str:
    """Extract only actionable sections from a review for the fix prompt."""
    sections: list[str] = []
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
        return review_text
    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Track calibration
# ---------------------------------------------------------------------------

def _get_track_calibration(level: str, module_num: int) -> str:
    """Read the appropriate calibration file for a track/level + module number."""
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

    base = level_lower.split("-")[0]
    fallback = _CALIBRATION_DIR / f"{base}.md"
    if fallback.exists():
        return fallback.read_text("utf-8")

    return ""


def _get_russicism_table(level: str) -> str:
    """Extract the Russicism Lookup section from a calibration file."""
    cal_text = _get_track_calibration(level, 1)
    if not cal_text:
        return ""

    m = re.search(
        r'## Russicism Lookup.*?\n(.*?)(?=\n## |\Z)',
        cal_text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# D.3 context builder
# ---------------------------------------------------------------------------

def _build_d3_context(d1_review: str, repair_cycle: int) -> str:
    """Build D.3 context injection with D.1 findings and D.2 repair info."""
    review_lines = d1_review.strip().split('\n')
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


# ---------------------------------------------------------------------------
# Quick review quality gate
# ---------------------------------------------------------------------------

def _quick_review_quality_gate(review_text: str, content_path: Path) -> tuple[bool, str]:
    """Fast pre-save check: reject obviously shallow/fake reviews."""
    from audit.checks.review_gaming import _extract_h2_headers
    from audit.checks.review_validation import _extract_ukrainian_citations

    citations = _extract_ukrainian_citations(review_text)
    content_text = content_path.read_text("utf-8") if content_path.exists() else ""
    word_count = len(content_text.split())

    min_citations = max(2, word_count // 600) if word_count > 500 else 2
    if len(citations) < min_citations:
        return False, (
            f"Shallow review: {len(citations)} citation(s), need ≥{min_citations} "
            f"for {word_count}-word content"
        )

    if content_text:
        h2s = _extract_h2_headers(content_text)
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
            if coverage < 0.15:
                return False, (
                    f"Shallow review: covers {mentioned}/{len(h2s)} "
                    f"({coverage:.0%}) content sections"
                )

    if len(review_text.split()) < 150:
        return False, f"Shallow review: only {len(review_text.split())} words"

    return True, "OK"


# ---------------------------------------------------------------------------
# Agent escalation
# ---------------------------------------------------------------------------

def _escalate_fix(ctx: ModuleContext, audit_output: str, phase_label: str,
                  content_only: bool = True, primary_agent: str = "gemini",
                  skip_review: bool = False) -> bool:
    """Escalate a failed fix to the opposite agent."""
    passed_retry, _ = run_verify(ctx.paths["md"], content_only=content_only,
                                 skip_review=skip_review)
    if passed_retry:
        log(f"  {phase_label}: Pre-escalation retry PASS — no escalation needed")
        return True

    lines = audit_output.strip().split("\n")
    error_excerpt = "\n".join(lines[-60:])

    content_path = ctx.paths["md"]
    affected = _identify_affected_sections(audit_output, content_path)

    section_content = ""
    if affected and content_path.exists():
        full_text = content_path.read_text("utf-8")
        for section_name in affected:
            pattern = rf"(^## {re.escape(section_name)}.*?)(?=^## |\Z)"
            match = re.search(pattern, full_text, re.MULTILINE | re.DOTALL)
            if match:
                section_content += f"\n---\n{match.group(1).strip()}\n"

    if not affected and content_path.exists():
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
        log(f"  {phase_label}: Escalating to Gemini (primary was Claude)...")
        output_file = _gemini_output_path(ctx.slug, f"{phase_label}-escalation")
        ok, output = dispatch_gemini(
            _dispatch_prompt(ctx, fix_file),
            task_id=f"v5-{ctx.slug}-escalation",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_FIX,
        )
    else:
        log(f"  {phase_label}: Escalating to Claude Opus...")
        ok, output = _dispatch_claude_phase(
            fix_file,
            phase_label=f"{phase_label}-escalation",
            model=ESCALATION_MODEL_CLAUDE,
            timeout=900,
        )
    if not ok:
        log(f"  {phase_label}: Escalation dispatch failed")
        return False

    if output and "===SECTION_FIX_START===" in output:
        _apply_section_fixes(ctx.paths["md"], output)
        if not content_only:
            if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                _apply_section_fixes(ctx.paths["activities"], output)
            _vp = ctx.paths.get("vocabulary")
            if _vp and _vp.exists():
                _apply_section_fixes(_vp, output)
        escalation_agent = "Gemini" if primary_agent == "claude" else "Claude"
        log(f"  {phase_label}: {escalation_agent} escalation fixes applied")
    elif output:
        log(f"  {phase_label}: Escalation output missing SECTION_FIX delimiters — cannot apply")
        (ctx.orch_dir / f"{phase_label}-escalation-raw.md").write_text(output, "utf-8")

    passed, _ = run_verify(ctx.paths["md"], content_only=content_only,
                            skip_review=skip_review)
    if passed:
        escalation_agent = "Gemini" if primary_agent == "claude" else "Claude Opus"
        log(f"  {phase_label}: Escalation PASS — {escalation_agent} fixed the issues")
    else:
        log(f"  {phase_label}: Escalation FAIL — both agents exhausted")
    return passed


def _all_issues_diffuse(audit_output: str) -> bool:
    """Determine if ALL audit issues are diffuse (not fixable by FIND/REPLACE)."""
    failing_codes: set[str] = set()
    for line in audit_output.split("\n"):
        if "❌" in line or "FAIL" in line.upper():
            codes_in_line = re.findall(r'\[([A-Z_]{3,})\]', line)
            failing_codes.update(codes_in_line)

    if not failing_codes:
        return False

    has_targeted = bool(failing_codes - _DIFFUSE_FAILURE_CODES)
    return not has_targeted


def _meta_has_oversized_sections(ctx: ModuleContext) -> bool:
    """Return True if any meta section consumes >25% of word_target."""
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
    """Return True if an existing research file has enough content."""
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        return False
    try:
        text = research_path.read_text("utf-8")
        word_count = len(text.split())
        return word_count >= _RESEARCH_EXISTS_MIN_WORDS
    except Exception:
        return False


def _invalidate_stale_artifacts(ctx: ModuleContext) -> None:
    """Delete stale audit cache and review files after content rebuild."""
    slug = ctx.slug
    track_dir = ctx.paths.get("md", Path()).parent

    status_file = track_dir / "status" / f"{slug}.json"
    if status_file.exists():
        status_file.unlink()
        log(f"  Phase B: Invalidated stale status cache: {status_file.name}")

    review_dir = track_dir / "review"
    for review_name in [f"{slug}-review.md", f"{slug}-final-review.md"]:
        review_file = review_dir / review_name
        if review_file.exists():
            review_file.unlink()
            log(f"  Phase B: Invalidated stale review: {review_name}")

    audit_file = track_dir / "audit" / f"{slug}-audit.md"
    if audit_file.exists():
        audit_file.unlink()
        log(f"  Phase B: Invalidated stale audit: {audit_file.name}")


def _build_vocab_only_prompt(ctx: ModuleContext) -> str | None:
    """Build a lightweight prompt for vocabulary-only generation."""
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


def _extract_quotes_from_content(content_path: Path) -> list[str]:
    """Extract quoted passages from module content for RAG verification."""
    if not content_path.exists():
        return []

    text = content_path.read_text("utf-8")
    quotes = []

    for match in re.finditer(r"«([^»]{10,200})»", text):
        quotes.append(match.group(1).strip())

    for match in re.finditer(r"^>\s+(.{10,200})", text, re.MULTILINE):
        line = match.group(1).strip()
        if line.startswith("[!") or line.startswith("**"):
            continue
        quotes.append(line)

    return quotes


def _prefetch_rag_context(ctx: ModuleContext) -> str:
    """Pre-fetch RAG results for quotes found in module content."""
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    if track_key not in SEMINAR_TRACKS:
        return "(Not a seminar track — no RAG verification needed)"

    content_path = ctx.paths.get("md")
    if not content_path or not content_path.exists():
        return "(Content file not found — cannot extract quotes)"

    quotes = _extract_quotes_from_content(content_path)
    if not quotes:
        return "(No quoted passages found in module content)"

    try:
        from rag.query import search_literary
    except ImportError:
        return "(RAG module not available — install qdrant-client and rag dependencies)"

    results = []
    for quote in quotes[:10]:
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


def _get_review_timeout(track: str) -> int:
    """Return the appropriate review timeout for a track."""
    key = "lit" if track.startswith("lit-") else track
    if key in _SEMINAR_TIMEOUT_TRACKS or key in SEMINAR_TRACKS:
        return TIMEOUT_REVIEW_SEMINAR
    return TIMEOUT_REVIEW_CORE


def _get_fix_timeout(track: str, audit_only: bool = False) -> int:
    """Return the appropriate fix timeout for a track."""
    if audit_only:
        return TIMEOUT_FIX_AUDIT_ONLY
    key = "lit" if track.startswith("lit-") else track
    if key in _SEMINAR_TIMEOUT_TRACKS or key in SEMINAR_TRACKS:
        return TIMEOUT_FIX_SEMINAR
    return TIMEOUT_FIX_CORE


def _max_audit_iters(track: str) -> int:
    """Seminar tracks get more fix attempts."""
    if track in SEMINAR_TRACKS or track in PRO_TRACKS:
        return MAX_AUDIT_FIX_ITERS_SEMINAR
    return MAX_AUDIT_FIX_ITERS_CORE


# ---------------------------------------------------------------------------
# RAG loaders for Gemini review
# ---------------------------------------------------------------------------

def _load_rag_for_review(ctx: ModuleContext) -> dict[str, list]:
    """Load RAG data from discovery.yaml."""
    from video_discovery import read_discovery_yaml, search_rag

    discovery_path = ctx.orch_dir / "discovery.yaml"
    rag_data: dict[str, list] = {"text_chunks": [], "images": [], "literary": []}

    if discovery_path.exists():
        try:
            disc = read_discovery_yaml(discovery_path)
            rag_data["text_chunks"] = disc.rag_chunks or []
            rag_data["images"] = disc.rag_images or []
            rag_data["literary"] = disc.rag_literary or []
        except Exception as e:
            log(f"  review-gemini: Failed to parse discovery.yaml: {e}")

    total = len(rag_data["text_chunks"]) + len(rag_data["images"]) + len(rag_data["literary"])
    if total == 0:
        log("  review-gemini: No RAG in discovery.yaml — trying live search")
        try:
            keywords = ctx.plan.get("vocabulary_hints", {}).get("required", [])
            if not keywords:
                keywords = [ctx.slug.replace("-", " ")]
            level = ctx.track.split("-")[0] if "-" in ctx.track else ctx.track
            rag_data = search_rag(keywords, ctx.track, level=level, limit_images=0)
        except Exception as e:
            log(f"  review-gemini: RAG fallback failed: {e}")

    return rag_data


def _build_pass1_prompt(ctx: ModuleContext, screen: DScreenResult, rag_data: dict) -> str:
    """Build Gemini Fact Checker prompt with inline content + RAG references."""
    template_path = PHASES_DIR / "phase-gemini-review-pass1.md"
    prompt_text = template_path.read_text("utf-8")

    content_path = ctx.paths.get("md")
    content_text = content_path.read_text("utf-8") if content_path and content_path.exists() else "(file not found)"
    if len(content_text) > 60_000:
        log(f"  review-gemini: Pass 1 content too large ({len(content_text)} chars) — truncating to 60K")
        content_text = content_text[:60_000] + "\n\n... (content truncated for prompt size) ..."
    prompt_text = prompt_text.replace("{CONTENT_FILE_CONTENT}", content_text)
    prompt_text = prompt_text.replace("{CONTENT_PATH}", str(content_path or ""))

    act_path = ctx.paths.get("activities")
    act_text = act_path.read_text("utf-8") if act_path and act_path.exists() else "(no activities file)"
    prompt_text = prompt_text.replace("{ACTIVITIES_FILE_CONTENT}", act_text)

    plan_path = ctx.paths.get("plan")
    plan_text = plan_path.read_text("utf-8") if plan_path and plan_path.exists() else "(no plan)"
    prompt_text = prompt_text.replace("{PLAN_CONTENT}", plan_text)

    research_path = ctx.paths.get("research")
    research_text = research_path.read_text("utf-8") if research_path and research_path.exists() else "(no research notes)"
    prompt_text = prompt_text.replace("{RESEARCH_CONTENT}", research_text)

    text_chunks = rag_data.get("text_chunks", [])
    images = rag_data.get("images", [])
    literary = rag_data.get("literary", [])

    if text_chunks:
        lines = []
        for i, ch in enumerate(text_chunks):
            chunk_id = ch.get("id", ch.get("chunk_id", f"chunk_{i}"))
            grade = ch.get("grade", 0)
            section = ch.get("section_title", "")
            text = ch.get("text", "")[:300]
            header = f"Textbook, Grade {grade}" if grade else "Textbook"
            if section:
                header += f", {section}"
            lines.append(f"- **[{chunk_id}]** {header}")
            lines.append(f"  {text}")
            lines.append("")
        prompt_text = prompt_text.replace("{RAG_TEXT_CHUNKS}", "\n".join(lines))
    else:
        prompt_text = prompt_text.replace("{RAG_TEXT_CHUNKS}", "(No textbook chunks available)")

    if images:
        lines = []
        for img in images:
            desc = img.get("description_uk", img.get("associated_text_uk", "(no description)"))
            grade = img.get("grade", 0)
            tv = img.get("teaching_value", "")
            lines.append(f"- Grade {grade} [{tv}]: {desc}")
        prompt_text = prompt_text.replace("{RAG_IMAGES}", "\n".join(lines))
    else:
        prompt_text = prompt_text.replace("{RAG_IMAGES}", "(No textbook images available)")

    if literary:
        lines = []
        for lit in literary:
            work = lit.get("work", "")
            year = lit.get("year", "")
            genre = lit.get("genre", "")
            text = lit.get("text", "")[:200]
            lines.append(f"- **{work}** ({year}, {genre})")
            lines.append(f"  {text}")
            lines.append("")
        prompt_text = prompt_text.replace("{RAG_LITERARY}", "\n".join(lines))
    else:
        prompt_text = prompt_text.replace("{RAG_LITERARY}", "(No literary sources available)")

    vesum_context = _format_vesum_verification(screen.vesum_stats, screen.vesum_not_found)
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", vesum_context)

    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)

    return prompt_text


def _build_pass2_prompt(ctx: ModuleContext, screen: DScreenResult) -> str:
    """Build Gemini Language Pedant prompt with inline content + checklists."""
    template_path = PHASES_DIR / "phase-gemini-review-pass2.md"
    prompt_text = template_path.read_text("utf-8")

    content_path = ctx.paths.get("md")
    act_path = ctx.paths.get("activities")
    vocab_path = ctx.paths.get("vocabulary")
    content_text = content_path.read_text("utf-8") if content_path and content_path.exists() else "(file not found)"
    if len(content_text) > 60_000:
        log(f"  review-gemini: Pass 2 content too large ({len(content_text)} chars) — truncating to 60K")
        content_text = content_text[:60_000] + "\n\n... (content truncated for prompt size) ..."
    act_text = act_path.read_text("utf-8") if act_path and act_path.exists() else "(file not found)"
    vocab_text = vocab_path.read_text("utf-8") if vocab_path and vocab_path.exists() else "(file not found)"
    prompt_text = prompt_text.replace("{CONTENT_FILE_CONTENT}", content_text)
    prompt_text = prompt_text.replace("{ACTIVITIES_FILE_CONTENT}", act_text)
    prompt_text = prompt_text.replace("{VOCAB_FILE_CONTENT}", vocab_text)
    prompt_text = prompt_text.replace("{CONTENT_PATH}", str(content_path or ""))
    prompt_text = prompt_text.replace("{ACTIVITIES_PATH}", str(act_path or ""))
    prompt_text = prompt_text.replace("{VOCAB_PATH}", str(vocab_path or ""))

    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", screen.h2_sections)

    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    track_calibration = _get_track_calibration(ctx.track, module_num)
    russicism_table = _get_russicism_table(ctx.track)

    prompt_text = prompt_text.replace("{TRACK_CALIBRATION}", track_calibration or "(No track calibration available)")
    prompt_text = prompt_text.replace("{DETERMINISTIC_ISSUES}", _format_deterministic_issues(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{FILLER_PHRASES}", _format_filler_phrases(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{RUSSIANISM_TABLE}", russicism_table or "(No track-specific Russianism table)")

    vesum_context = _format_vesum_verification(screen.vesum_stats, screen.vesum_not_found)
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", vesum_context)

    prompt_text = prompt_text.replace("{SCORING_SECTION}", _get_scoring_section(ctx.track))
    prompt_text = prompt_text.replace("{SCORING_OUTPUT_TABLE}", _get_scoring_output_table(ctx.track))

    return prompt_text


def _merge_gemini_review_passes(
    pass1: D1Result | None,
    pass2: D1Result | None,
) -> D1Result:
    """Merge results from Fact Checker (pass1) and Language Pedant (pass2)."""
    if pass1 and pass1.ok and pass2 and pass2.ok:
        merged_scores = dict(pass2.scores)
        merged_scores.update(pass1.scores)
        merged_issues = list(pass1.issues) + list(pass2.issues)
        verdict = "FAIL" if (pass1.verdict == "FAIL" or pass2.verdict == "FAIL") else "PASS"
        raw = (
            "# Factual Review (Pass 1)\n\n"
            + pass1.raw_review
            + "\n\n---\n\n# Language Review (Pass 2)\n\n"
            + pass2.raw_review
        )
        return D1Result(
            ok=True,
            issues=merged_issues,
            scores=merged_scores,
            verdict=verdict,
            raw_review=raw,
        )

    if pass2 and pass2.ok:
        log("  review-gemini: Pass 1 dispatch failed — using Pass 2 only")
        return pass2
    if pass1 and pass1.ok:
        log("  review-gemini: Pass 2 dispatch failed — using Pass 1 only")
        return pass1

    log("  review-gemini: Both passes failed")
    return D1Result(ok=False, raw_review="", verdict="")


def _gemini_fix_iteration(
    ctx: ModuleContext, fix_plan: str, audit_out: str, fix_iter: int,
) -> bool:
    """Run one Gemini fix iteration: build prompt -> dispatch -> apply FIND/REPLACE."""
    template_path = PHASES_DIR / "phase-gemini-review-fix.md"
    if not template_path.exists():
        log(f"  review-gemini: Fix template not found: {template_path}")
        return False

    prompt_text = template_path.read_text("utf-8")

    failures = _extract_audit_failures(audit_out) or "None (audit passed). Focus on the Fix Plan."
    failures += _extract_gate_blockers(ctx)
    failures += _extract_vesum_failures(ctx)

    prompt_text = prompt_text.replace("{EXTRACTED_FIX_PLAN}", fix_plan)
    prompt_text = prompt_text.replace("{INJECTED_AUDIT_FAILURES}", failures)

    prompt_text = _inject_file_contents(prompt_text, ctx)
    prompt_text = prompt_text.replace("{CONTENT_PATH}", str(ctx.paths.get("md", "")))
    prompt_text = prompt_text.replace("{ACTIVITIES_PATH}", str(ctx.paths.get("activities", "")))
    prompt_text = prompt_text.replace("{VOCAB_PATH}", str(ctx.paths.get("vocabulary", "")))

    log(f"  review-gemini: Fix {fix_iter + 1} — dispatching to Gemini ({len(prompt_text)} chars)...")

    ok, raw_output = pipeline_lib.dispatch_gemini_raw(
        prompt_text,
        task_id=f"{ctx.slug}-review-fix-{fix_iter + 1}",
        timeout=600,
    )

    if not ok:
        log(f"  review-gemini: Fix dispatch failed (iter {fix_iter + 1})")
        return False

    (ctx.orch_dir / f"review-fix-{fix_iter + 1}-raw.md").write_text(raw_output, "utf-8")

    accepted, n_fixes = _apply_fixes_with_rollback(ctx, raw_output, f"Gemini fix {fix_iter + 1}")
    if not accepted:
        return False

    if n_fixes > 0:
        log(f"  review-gemini: Applied {n_fixes} fix(es) in iteration {fix_iter + 1}")
    else:
        log(f"  review-gemini: No fixes matched in iteration {fix_iter + 1}")

    return n_fixes > 0


def _complete_gemini_review(
    ctx: ModuleContext, state: dict, phase: str, attempts: int, note: str,
    *, grounding: str = "rag-textbook",
) -> bool:
    """Mark Gemini review as complete — shared across all success paths."""
    mark_complete(state, phase, ctx, attempts=attempts,
                  note=note, review_grounding=grounding)
    _update_pipeline_status(ctx, "reviewed")
    return True


# ---------------------------------------------------------------------------
# Discovery helper
# ---------------------------------------------------------------------------

def _append_discovery_to_research(ctx: ModuleContext, result) -> None:
    """Append ## Resource Discovery section to the research file."""
    from video_discovery import DiscoveryResult
    if not isinstance(result, DiscoveryResult):
        return
    relevant_vids = [v for v in result.videos if v.relevance_score >= 0.5]
    has_blogs = bool(result.blogs)
    has_rag = bool(result.rag_chunks or result.rag_images or result.rag_literary)
    if not relevant_vids and not has_blogs and not has_rag:
        return
    research_path = ctx.paths.get("research")
    if not research_path or not research_path.exists():
        return
    lines = ["\n\n## Resource Discovery\n"]
    if relevant_vids:
        lines.append("### Videos")
        for v in relevant_vids:
            lines.append(f"- [{v.title}]({v.url}) ({v.channel}) — {v.relevance_note}")
    if has_blogs:
        lines.append("\n### Blog Articles")
        for b in result.blogs:
            lines.append(f"- [{b['title']}]({b['url']}) ({b.get('source', '')})")
    if result.rag_chunks:
        lines.append("\n### Textbook References (RAG)")
        for ch in result.rag_chunks[:5]:
            section = ch.get("section_title", "")
            grade = ch.get("grade", 0)
            source = ch.get("source", "")
            text_preview = ch.get("text", "")[:500]
            lines.append(f"\n**Grade {grade}, {section}** ({source}):\n{text_preview}\n")
    if result.rag_images:
        lines.append("\n### Textbook Images (RAG)")
        for img in result.rag_images[:3]:
            desc = img.get("description_uk", img.get("associated_text_uk", ""))
            grade = img.get("grade", 0)
            tv = img.get("teaching_value", "")
            lines.append(f"- Grade {grade} [{tv}]: {desc[:80]}")
    if result.rag_literary:
        lines.append("\n### Literary Sources (RAG)")
        for lit in result.rag_literary[:3]:
            work = lit.get("work", "")
            year = lit.get("year", "")
            lines.append(f"- {work} ({year}): {lit.get('text', '')[:80]}...")
    try:
        with open(research_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        log(f"  discover: failed to append to research: {e}")


# ============================================================================
# 2b. Fix-prompt helpers (moved from pipeline_lib.py — only used by v5)
# ============================================================================

def _identify_affected_sections(audit_output: str, content_path: Path, content: str | None = None) -> list[str]:
    """Parse audit output to identify which H2 sections have issues."""
    if content is None:
        if not content_path.exists():
            return []
        content = content_path.read_text(encoding="utf-8")
    h2_headers = re.findall(r"^## (.+)$", content, re.MULTILINE)
    if not h2_headers:
        return []

    affected = set()
    audit_lower = audit_output.lower()
    for header in h2_headers:
        if header.lower() in audit_lower:
            affected.add(header)

    line_refs = re.findall(r"line\s+(\d+)", audit_output, re.IGNORECASE)
    if line_refs:
        lines = content.split("\n")
        current_section = None
        section_ranges: dict[str, tuple[int, int]] = {}
        for i, line in enumerate(lines, 1):
            m = re.match(r"^## (.+)$", line)
            if m:
                if current_section:
                    section_ranges[current_section] = (section_ranges[current_section][0], i - 1)
                current_section = m.group(1)
                section_ranges[current_section] = (i, len(lines))
        if current_section and current_section in section_ranges:
            section_ranges[current_section] = (section_ranges[current_section][0], len(lines))
        for ref in line_refs:
            line_num = int(ref)
            for header, (start, end) in section_ranges.items():
                if start <= line_num <= end:
                    affected.add(header)
                    break

    if 1 <= len(affected) <= 2:
        return sorted(affected)
    return []


def _apply_section_fixes(content_path: Path, fix_output: str) -> None:
    """Apply section-level fixes from delimited Gemini output."""
    fixes = re.findall(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        fix_output, re.DOTALL,
    )
    if not fixes:
        return
    content = content_path.read_text(encoding="utf-8")
    for fix_block in fixes:
        fix_block = fix_block.strip()
        h2_match = re.match(r"^## (.+)$", fix_block, re.MULTILINE)
        if not h2_match:
            continue
        section_title = h2_match.group(1).strip()
        pattern = re.compile(
            rf"(^## {re.escape(section_title)}\s*\n)"
            rf"(.*?)"
            rf"(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(content)
        if match:
            replacement = fix_block + "\n\n"
            content = content[:match.start()] + replacement + content[match.end():]
            log(f"    Applied section fix: {section_title}")
    content_path.write_text(content, encoding="utf-8")


def _build_schema_hint(ctx: ModuleContext, audit_output: str) -> str:
    """If audit output contains YAML_SCHEMA_VIOLATION, extract schema definitions."""
    if "YAML_SCHEMA_VIOLATION" not in audit_output:
        return ""
    failing_types = list(dict.fromkeys(
        m.group(1) for m in re.finditer(r"'type':\s*'([a-z_-]+)'", audit_output)
    ))
    if not failing_types:
        return ""
    track = ctx.track if hasattr(ctx, "track") else ""
    schemas_dir = Path(__file__).parent.parent / "schemas"
    schema_path = schemas_dir / f"activities-{track}.schema.json"
    if not schema_path.exists():
        level_code = track.split("-")[0] if "-" not in track else track
        schema_path = schemas_dir / f"activities-{level_code}.schema.json"
    if not schema_path.exists():
        schema_path = schemas_dir / "activities-base.schema.json"
    if not schema_path.exists():
        return ""
    try:
        schema = json.loads(schema_path.read_text("utf-8"))
        defs = schema.get("definitions", {})
        hints = []
        for failing_type in failing_types:
            type_def = defs.get(f"{failing_type}-{track}") or defs.get(failing_type)
            if not type_def:
                continue
            required = type_def.get("required", [])
            props = list(type_def.get("properties", {}).keys())
            additional = type_def.get("additionalProperties", True)
            no_extra = additional is False
            hints.append(
                f"### `{failing_type}` (from {schema_path.name})\n"
                f"**Required fields:** {', '.join(f'`{r}`' for r in required)}\n"
                f"**Allowed fields:** {', '.join(f'`{p}`' for p in props)}\n"
                f"**additionalProperties:** `{additional}`"
                f"{' — ANY unlisted field = schema violation' if no_extra else ''}\n"
            )
        if not hints:
            return ""
        return "\n\n## Schema Reference (fix activities to match these)\n\n" + "\n".join(hints)
    except Exception:
        return ""


def _extract_gate_failures(audit_output: str) -> list[dict]:
    """Parse audit output to extract specific gate failures with values.

    Returns list of dicts: {gate, status, current, required, detail}
    Also extracts pedagogical violation details from the 📚 section.
    """
    failures = []
    for line in audit_output.split("\n"):
        # Match gate lines like: "Words        ❌ 1200/2000"
        m = re.match(r"\s*([A-Za-z0-9_]+)\s+❌\s+(.*)", line)
        if m:
            gate = m.group(1).strip()
            detail = m.group(2).strip()
            failures.append({"gate": gate, "detail": detail})
            continue
        # Match YAML_SCHEMA_VIOLATION lines
        if "YAML_SCHEMA_VIOLATION" in line:
            failures.append({"gate": "YAML_SCHEMA", "detail": line.strip()})
    return failures


def _extract_pedagogy_violations(audit_output: str) -> list[dict]:
    """Extract detailed pedagogical violations from audit output.

    Parses the 📚 PEDAGOGICAL VIOLATIONS section to get type, issue, and fix.
    These are NOT captured by _extract_gate_failures (which only sees the
    gate summary line 'Pedagogy ❌ 3 violations').
    """
    violations = []
    lines = audit_output.split("\n")
    in_section = False
    for line in lines:
        stripped = line.strip()
        if "📚 PEDAGOGICAL VIOLATIONS FOUND" in stripped:
            in_section = True
            continue
        if in_section:
            # End of section: next header (--- or emoji-prefixed or gate line)
            if stripped.startswith("---") or re.match(r"^[^\[→\s].*[❌✅⚠]", stripped):
                break
            # Violation line: "  [TYPE] description"
            m = re.match(r"\s*\[([^\]]+)\]\s+(.*)", stripped)
            if m:
                vtype = m.group(1)
                # Skip noise from RAG/embedding model loading and progress bars
                if vtype.lower() in ("embed", "info", "warning", "error", "debug"):
                    continue
                if any(noise in stripped for noise in (
                    "Loading BGE", "BGE-M3 loaded", "Fetching", "it/s]",
                    "XLMRoberta", "tokenizer",
                )):
                    continue
                violations.append({
                    "type": vtype,
                    "issue": m.group(2),
                    "fix": "",
                })
                continue
            # Fix line: "     → FIX: description"
            fm = re.match(r"\s*→\s*FIX:\s*(.*)", stripped)
            if fm and violations:
                violations[-1]["fix"] = fm.group(1)
    return violations


def _build_fix_prompt(ctx: ModuleContext, audit_output: str, content_only: bool,
                      deterministic_issues: list[dict] | None = None) -> str:
    """Build a surgical fix prompt with per-issue instructions.

    Instead of dumping 60 lines of audit output, this extracts specific
    failures and produces exact instructions Gemini can act on.
    """
    from pipeline_lib import get_decodable_vocabulary, get_pedagogical_constraints

    det_issues = deterministic_issues or []
    gate_failures = _extract_gate_failures(audit_output)
    ped_violations = _extract_pedagogy_violations(audit_output)
    schema_hint = _build_schema_hint(ctx, audit_output)

    # Read content file once — reuse for line lookups and word count
    content_text = ""
    content_lines: list[str] = []
    word_count = 0
    if ctx.paths["md"].exists():
        content_text = ctx.paths["md"].read_text("utf-8")
        content_lines = content_text.split("\n")
        word_count = len(content_text.split())

    # Build per-issue fix instructions
    fix_instructions: list[str] = []

    # 1. Deterministic issues — inline the actual line content
    for i, iss in enumerate(det_issues, 1):
        issue_type = iss.get("type", "UNKNOWN")
        lines_block: list[str] = [f"### Fix {i}: {issue_type}"]

        # Try to find the actual line in content
        location = iss.get("location", "")
        matched_text = iss.get("text", "")
        line_num = 0
        loc_match = re.search(r"~?line\s*(\d+)", location, re.IGNORECASE)
        if loc_match:
            line_num = int(loc_match.group(1))

        if issue_type == "LLM_FILLER":
            if line_num and line_num <= len(content_lines):
                actual_line = content_lines[line_num - 1].strip()
                lines_block.append(f"**Line {line_num}:** `{actual_line}`")
            elif matched_text:
                lines_block.append(f"**Text:** `{matched_text}`")
            lines_block.append(f"**Action:** Rephrase to remove \"{matched_text}\". "
                             "Start the sentence with a concrete fact instead.")

        elif issue_type == "RUSSIANISM":
            fix_text = iss.get("fix", "")
            lines_block.append(f"**Found:** `{matched_text}`")
            if fix_text:
                lines_block.append(f"**Replace with:** `{fix_text}` (preserve grammatical form)")
            if line_num and line_num <= len(content_lines):
                actual_line = content_lines[line_num - 1].strip()
                lines_block.append(f"**Context (line {line_num}):** `{actual_line}`")

        elif issue_type in ("PEDAGOGICAL", "DECODABILITY"):
            lines_block.append(f"**What:** {matched_text}")
            fix_text = iss.get("fix", "")
            if fix_text:
                lines_block.append(f"**How to fix:** {fix_text}")
            if line_num and line_num <= len(content_lines):
                actual_line = content_lines[line_num - 1].strip()
                lines_block.append(f"**Context (line {line_num}):** `{actual_line}`")

        else:
            if matched_text:
                lines_block.append(f"**What:** {matched_text}")
            fix_text = iss.get("fix", "")
            if fix_text:
                lines_block.append(f"**How to fix:** {fix_text}")
            if location:
                lines_block.append(f"**Where:** {location}")

        fix_instructions.append("\n".join(lines_block))

    # 2. Gate failures — specific action per gate
    for gf in gate_failures:
        gate = gf["gate"]
        detail = gf["detail"]
        lines_block = [f"### Fix: Gate `{gate}` FAIL — {detail}"]

        if gate.lower() in ("words", "word_count"):
            lines_block.append("**Action:** Expand content in the shortest sections. "
                             "Add examples, explanations, or practice scenarios.")
        elif gate.lower() == "immersion":
            # Parse immersion gap to detect unfixable cases
            imm_match = re.search(r"([\d.]+)%\s+LOW\s+\(target\s+(\d+)-(\d+)%", detail)
            if imm_match:
                current_imm = float(imm_match.group(1))
                target_min = int(imm_match.group(2))
                gap = target_min - current_imm
                if gap > 15:
                    lines_block.append(
                        f"**⚠ SCOPE WARNING:** Immersion gap is {gap:.0f}% ({current_imm:.1f}% → {target_min}% min). "
                        "This is too large for a fix pass. Focus on the EASIEST wins:\n"
                        "1. Add Ukrainian section headers with English in parentheses\n"
                        "2. Add 'Наприклад:' / 'Порівняйте:' before example blocks\n"
                        "3. Add short Ukrainian phrases with (translations) in existing paragraphs\n"
                        "Do NOT rewrite entire sections. Target +5-8% improvement max.")
                else:
                    lines_block.append("**Action:** Add more Ukrainian-language content blocks. "
                                     "Convert some English explanations to Ukrainian with English glosses.")
            else:
                lines_block.append("**Action:** Add more Ukrainian-language content blocks. "
                                 "Convert some English explanations to Ukrainian with English glosses.")
        elif gate.lower() in ("activities", "unique_types"):
            lines_block.append("**Action:** Add more activities or diversify activity types "
                             "in the activities YAML file.")
        elif gate.lower() == "engagement":
            lines_block.append("**Action:** Add engagement boxes: `[!tip]`, `[!note]`, "
                             "`[!cultural]`, `[!myth-buster]`.")
        elif gate == "YAML_SCHEMA":
            lines_block.append(f"**Action:** Fix the YAML schema violation: {detail}")

        fix_instructions.append("\n".join(lines_block))

    # 3. Pedagogical violations — extracted from the 📚 section
    # The Pedagogy gate only says "3 violations" — this adds the actual details
    for i, pv in enumerate(ped_violations, len(det_issues) + len(gate_failures) + 1):
        lines_block = [f"### Fix {i}: PEDAGOGICAL_VIOLATION"]
        lines_block.append(f"**What:** [{pv['type']}] {pv['issue']}")
        if pv.get("fix"):
            lines_block.append(f"**How to fix:** {pv['fix']}")
        fix_instructions.append("\n".join(lines_block))

    # Always append any unparsed ❌ failures not already covered by gate_failures
    # This catches LINT errors, TEMPLATE COMPLIANCE, PEDAGOGICAL VIOLATIONS, etc.
    parsed_gates = {gf["gate"] for gf in gate_failures}
    audit_lines = audit_output.strip().split("\n")
    unparsed_fails = [
        ln.strip() for ln in audit_lines
        if ("❌" in ln or "VIOLATION" in ln) and not any(g in ln for g in parsed_gates)
    ]
    if unparsed_fails:
        fix_instructions.append("### Other Audit Failures\n\n```\n" + "\n".join(unparsed_fails[-20:]) + "\n```")

    if not fix_instructions:
        # Last resort: dump condensed fail lines so Gemini always sees WHY audit failed
        fail_lines = [ln for ln in audit_lines if "❌" in ln or "FAIL" in ln or "VIOLATION" in ln]
        if fail_lines:
            fix_instructions.append("### Audit Failures\n\n```\n" + "\n".join(fail_lines[-20:]) + "\n```")
        else:
            # Ultra-fallback: include the full audit tail so the fix prompt is never empty
            tail = "\n".join(audit_lines[-30:])
            fix_instructions.append(
                "### Audit Output (no specific failures extracted — review raw output)\n\n"
                f"```\n{tail}\n```"
            )

    # Pedagogical constraints (compact)
    ped_constraints = get_pedagogical_constraints(ctx.track, ctx.module_num)
    ped_section = ""
    if ped_constraints:
        ped_section = f"\n## Constraints (do NOT violate while fixing)\n\n{ped_constraints}\n"

    # Decodable vocabulary (compact)
    decodable = get_decodable_vocabulary(ctx.track, ctx.module_num, ctx.plan)
    decodable_section = f"\n{decodable}\n" if decodable else ""

    # Section-level fix output format — used for ALL modules
    section_fix = ""
    if content_text:
        affected_sections = _identify_affected_sections(audit_output, ctx.paths["md"], content=content_text)
        if affected_sections:
            section_list = ", ".join(f'"{s}"' for s in affected_sections)
            if word_count >= 3000:
                scope_note = f"This module is {word_count} words. Fix ONLY sections: {section_list}"
            else:
                scope_note = f"Fix the affected sections: {section_list}"
            section_fix = textwrap.dedent(f"""\

                    ## Output Format (MANDATORY)

                    {scope_note}

                    **Wrap EACH fixed section in delimiters:**
                    ```
                    ===SECTION_FIX_START===
                    ## {{section title}}
                    {{fixed section content}}
                    ===SECTION_FIX_END===
                    ```
                """)

    # Build file list
    file_list = f"- Content: `{ctx.paths['md']}`"
    if not content_only:
        if ctx.paths.get("activities"):
            file_list += f"\n- Activities: `{ctx.paths['activities']}`"
        if ctx.paths.get("vocabulary"):
            file_list += f"\n- Vocabulary: `{ctx.paths['vocabulary']}`"

    fixes_text = "\n\n".join(fix_instructions)
    total_fixes = len(det_issues) + len(gate_failures) + len(ped_violations)
    # Never say "Fix 0 issues" — if we got here, something failed
    if total_fixes == 0:
        total_fixes = len(fix_instructions)

    # RAG verification tools — always available via .gemini/settings.json MCP
    vesum_section = textwrap.dedent("""\

        ## Verification Tools (USE THEM)

        You have MCP tools for Ukrainian language verification. **Use them before fixing.**

        - `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
        - `verify_lemma("word")` — get all inflected forms of a word

        **Before replacing any Ukrainian word:**
        1. Call `verify_words` with your replacement to confirm it exists
        2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
        3. Never use a word that returns NOT FOUND — rephrase in English instead
    """)

    return textwrap.dedent(f"""\
        # Fix {total_fixes} issue(s) in `{ctx.slug}`

        {fixes_text}
        {schema_hint}
        {ped_section}
        {decodable_section}
        {vesum_section}

        ## Files

        {file_list}

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.
        {section_fix}
    """)


# ============================================================================
# 3. Phase implementations
# ============================================================================

# ---------------------------------------------------------------------------
# Phase: research
# ---------------------------------------------------------------------------

def phase_research(ctx: ModuleContext, state: dict) -> bool:
    """Research + Meta outline generation."""
    if is_complete(state, "research"):
        # Health check: if content exists and meets target, skip
        force_research = getattr(ctx, "force_research", False)
        if not force_research:
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
                log(f"  research: SKIP (meta locked — content exists at {wc}w, target {ctx.word_target}w)")
                return True
            elif _meta_has_oversized_sections(ctx):
                log("  research: Meta health check FAILED — oversized section detected, re-running")
                state.get("phases", {}).pop("research", None)
                save_state(ctx, state)
            else:
                meta_path = ctx.paths.get("meta")
                if meta_path and not meta_path.exists():
                    log("  research: State says complete but meta missing — re-running")
                    state.get("phases", {}).pop("research", None)
                    save_state(ctx, state)
                else:
                    log("  research: SKIP (already complete)")
                    return True
        else:
            # force_research — clear state and re-run
            state.get("phases", {}).pop("research", None)
            save_state(ctx, state)

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    is_pro = ctx.track in PRO_TRACKS

    research_exists = (is_seminar or is_pro) and _research_file_is_usable(ctx)
    if is_seminar or is_pro:
        if research_exists:
            research_path = ctx.paths.get("research")
            word_count = len(research_path.read_text("utf-8").split()) if research_path else 0
            log(f"  research: Research file found ({word_count:,}w) — skipping research, meta-only")
            template_name = "phase-A-meta-only.md"
        elif is_pro:
            template_name = "phase-A-pro.md"
        else:
            template_name = "phase-A-seminar.md"
    else:
        tier = _get_prompt_tier(ctx.track, ctx.module_num)
        if tier == "beginner":
            template_name = "beginner-research.md"
            if not (PHASES_DIR / template_name).exists():
                template_name = "phase-A-core.md"
                log("  research: beginner-research.md not found, falling back to phase-A-core.md")
            else:
                log("  research: Using beginner tier research prompt")
        else:
            template_name = "phase-A-core.md"

    template = PHASES_DIR / template_name

    if not template.exists():
        log(f"  research: ERROR — template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "phase-A-prompt.md"
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    if ctx.dry_run:
        log(f"  research: DRY-RUN — would dispatch {template_name}")
        return True

    use_claude = "A" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_A", CLAUDE_MODEL_RESEARCH)
        log(f"  research: Dispatching {template_name} via Claude ({claude_model})...")
        ok, raw_output = _dispatch_claude_phase(
            prompt_file, "Phase A", model=claude_model,
            timeout=600,
            allow_tools=["WebSearch", "WebFetch", "Read"],
        )
    else:
        log(f"  research: Dispatching {template_name}...")
        output_file = _gemini_output_path(ctx.slug, "pA")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v5-{ctx.slug}-pA",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_CONTENT,
        )
        if raw_output:
            (ctx.orch_dir / "phase-A-output.md").write_text(raw_output, "utf-8")
    if not ok:
        log(f"  research: FAILED — {'Claude' if use_claude else 'Gemini'} dispatch error")
        mark_failed(state, "research", ctx)
        return False

    # Extract and save research
    if not research_exists:
        research_text = _extract_delimiter(raw_output, "===RESEARCH_START===", "===RESEARCH_END===")
        if research_text:
            research_path = ctx.paths.get("research")
            if research_path:
                research_path.parent.mkdir(parents=True, exist_ok=True)
                research_path.write_text(research_text, "utf-8")
                log(f"  research: Research saved → {research_path.name}")
            else:
                (ctx.orch_dir / "phase-A-research.md").write_text(research_text, "utf-8")
                log("  research: Research saved → phase-A-research.md (no research path in ctx)")
        else:
            if is_seminar or is_pro:
                log("  research: WARNING — no RESEARCH delimiters in output (seminar/pro track)")
            else:
                log("  research: NOTE — no research delimiters (expected for some core tracks)")

    # Extract and apply meta outline
    meta_text = _extract_delimiter(raw_output, "===META_OUTLINE_START===", "===META_OUTLINE_END===")
    if meta_text:
        import yaml
        meta_text_clean = re.sub(r'^```(?:ya?ml)?\s*\n', '', meta_text.strip())
        meta_text_clean = re.sub(r'\n```\s*$', '', meta_text_clean)
        try:
            outline_data = yaml.safe_load(meta_text_clean)
        except yaml.YAMLError as e:
            log(f"  research: WARNING — meta outline YAML parse error: {e}")
            outline_data = None

        if outline_data and isinstance(outline_data, dict) and "content_outline" in outline_data:
            outline_data["content_outline"] = bilingualify_section_titles(
                outline_data["content_outline"], ctx.track, ctx.module_num,
            )
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
                    ctx.content_outline = outline_data["content_outline"]  # type: ignore[attr-defined]
                    mode = "meta-only" if research_exists else "full"
                    log(f"  research: Meta outline updated [{mode}] → {meta_path.name} "
                        f"({len(outline_data['content_outline'])} sections)")
                except Exception as e:
                    log(f"  research: WARNING — could not update meta: {e}")
            else:
                (ctx.orch_dir / "phase-A-meta-outline.yaml").write_text(meta_text, "utf-8")
                log("  research: Meta outline saved → phase-A-meta-outline.yaml (no meta path)")
        else:
            log("  research: WARNING — no content_outline in META_OUTLINE block")
            (ctx.orch_dir / "phase-A-meta-outline-raw.md").write_text(meta_text or "", "utf-8")
    else:
        log("  research: FAILED — no META_OUTLINE delimiters in output")
        mark_failed(state, "research", ctx)
        return False

    mark_complete(state, "research", ctx,
                  task_id=f"v5-{ctx.slug}-pA",
                  mode="meta-only" if research_exists else "full")
    return True


# ---------------------------------------------------------------------------
# Phase: discover
# ---------------------------------------------------------------------------

def _update_external_resources(ctx: ModuleContext, result: Any) -> None:
    """Write discovered blogs/videos to external_resources.yaml."""
    import yaml as _yaml
    ext_path = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
    if not ext_path.exists():
        return

    try:
        data = _yaml.safe_load(ext_path.read_text("utf-8"))
        resources = data.get("resources", {})
    except Exception:
        return

    module_key = f"{ctx.track}-{ctx.slug}"

    # Build new entries from discovery results
    articles: list[dict] = []
    seen_urls: set[str] = set()

    for blog in getattr(result, "blogs", []):
        url = blog.get("url", "")
        if not url or url in seen_urls or blog.get("relevance_score", 0) < 0.5:
            continue
        seen_urls.add(url)
        articles.append({
            "title": blog.get("title", ""),
            "url": url,
            "relevance": "high" if blog.get("relevance_score", 0) >= 0.7 else "medium",
            "source": blog.get("source", ""),
        })

    youtube: list[dict] = []
    for vid in getattr(result, "videos", []):
        url = getattr(vid, "url", "")
        if not url or url in seen_urls or getattr(vid, "relevance_score", 0) < 0.5:
            continue
        seen_urls.add(url)
        youtube.append({
            "title": getattr(vid, "title", ""),
            "url": url,
            "source": getattr(vid, "channel", ""),
        })

    if not articles and not youtube:
        return

    entry = resources.get(module_key, {}) or {}
    if articles:
        entry["articles"] = articles
    if youtube:
        entry["youtube"] = youtube
    resources[module_key] = entry

    try:
        with open(ext_path, "w", encoding="utf-8") as f:
            _yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                       sort_keys=False, width=120)
    except Exception as e:
        log(f"  discover: WARNING — failed to update external_resources.yaml: {e}")

def phase_discover(ctx: ModuleContext, state: dict) -> bool:
    """Discover: video/blog/RAG search. Always returns True (non-blocking).

    Results are written to:
    - discovery/{slug}.yaml (pipeline state, used by review phase for RAG context)
    - external_resources.yaml (single source of truth for MDX rendering)
    """
    if is_complete(state, "discover"):
        log("  discover: SKIP (already complete)")
        return True
    if getattr(ctx, "skip_discover", False):
        log("  discover: SKIP (--skip-discover)")
        mark_complete(state, "discover", ctx, skipped=True)
        return True
    if ctx.dry_run:
        log("  discover: SKIP (dry-run)")
        return True

    from video_discovery import (
        build_discovery_keywords,
        build_search_keywords,
        run_discovery,
        search_blogs,
        search_rag,
        write_discovery_yaml,
    )

    keywords = build_discovery_keywords(ctx.plan)
    if not keywords:
        vocab_hints = ctx.plan.get("vocabulary_hints", {})
        keywords = build_search_keywords(ctx.topic_title, vocab_hints)

    log(f"  discover: searching (keywords: {keywords[:4]}...)")

    result = run_discovery(
        topic=ctx.topic_title,
        keywords=keywords,
        outline=ctx.content_outline,
        vocab=keywords[1:],
        dispatch_fn=pipeline_lib.dispatch_gemini_raw,
        track=ctx.track,
    )

    slug = ctx.slug if hasattr(ctx, "slug") else ""
    level = getattr(ctx, "level", "") or ctx.plan.get("level", "")
    blogs = search_blogs(
        module_slug=slug,
        level=level,
        topic_title=ctx.topic_title,
        keywords=keywords,
    )
    result.blogs = blogs

    rag_results = search_rag(
        keywords=keywords,
        track=ctx.track,
        level=level,
        limit_images=0,
    )
    result.rag_chunks = rag_results.get("text_chunks", [])
    result.rag_images = rag_results.get("images", [])
    result.rag_literary = rag_results.get("literary", [])

    discovery_dir = ctx.paths["md"].parent / "discovery"
    discovery_dir.mkdir(parents=True, exist_ok=True)
    discovery_path = discovery_dir / f"{ctx.slug}.yaml"
    write_discovery_yaml(result, discovery_path)

    orch_discovery = ctx.orch_dir / "discovery.yaml"
    write_discovery_yaml(result, orch_discovery)

    # Write blog/podcast results to external_resources.yaml (single source of truth for MDX)
    _update_external_resources(ctx, result)

    relevant = [v for v in result.videos if v.relevance_score >= 0.5]
    n_rag = len(result.rag_chunks) + len(result.rag_images) + len(result.rag_literary)
    log(f"  discover: {len(result.videos)} videos ({len(relevant)} relevant), "
        f"{len(result.blogs)} blogs, {n_rag} RAG items")
    if result.error:
        log(f"  discover: WARNING: {result.error}")
    elif result.warning:
        log(f"  discover: WARNING: {result.warning}")

    _append_discovery_to_research(ctx, result)

    mark_complete(state, "discover", ctx)
    return True


# ---------------------------------------------------------------------------
# Phase: sandbox + helpers
# ---------------------------------------------------------------------------


def _ensure_sandbox_loaded(ctx: ModuleContext) -> str:
    """Load lexical sandbox into ctx if not already set. Returns the sandbox text."""
    sandbox = getattr(ctx, "_lexical_sandbox", "")
    if sandbox:
        return sandbox
    sandbox_path = ctx.orch_dir / "lexical-sandbox.md"
    if sandbox_path.exists():
        sandbox = sandbox_path.read_text(encoding="utf-8")
        ctx._lexical_sandbox = sandbox
        log(f"  sandbox: Loaded from disk ({len(sandbox)} chars)")
    else:
        ctx._lexical_sandbox = ""
    return ctx._lexical_sandbox


def phase_sandbox(ctx: ModuleContext, state: dict) -> bool:
    """Lexical Sandbox: build VESUM-validated word bank for content generation.

    Two modes:
    - Plan-only (fast): Build sandbox directly from plan vocabulary_hints
    - Pass 1 (full): Dispatch Gemini to request resources, then build sandbox

    The sandbox is saved to orchestration/ and injected into the content prompt
    via the {LEXICAL_SANDBOX} placeholder.
    """
    if is_complete(state, "sandbox"):
        _ensure_sandbox_loaded(ctx)
        log("  sandbox: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  sandbox: DRY-RUN — would build lexical sandbox")
        return True

    try:
        from lexical_sandbox import build_sandbox

        # Build sandbox from plan vocabulary + common words for this level
        sandbox_md = build_sandbox(
            track=ctx.track,
            module_num=ctx.module_num,
            plan=ctx.plan,
            max_examples=6,
        )

        if sandbox_md:
            # Save to orchestration
            sandbox_path = ctx.orch_dir / "lexical-sandbox.md"
            sandbox_path.write_text(sandbox_md, encoding="utf-8")

            # Attach to context for content phase placeholder injection
            ctx._lexical_sandbox = sandbox_md

            word_count = sandbox_md.count("|") // 3  # rough table row count
            log(f"  sandbox: Built lexical sandbox ({len(sandbox_md)} chars, ~{word_count} entries)")
        else:
            log("  sandbox: No vocabulary_hints in plan — skipping sandbox")
            ctx._lexical_sandbox = ""

    except Exception as e:
        logger.warning("sandbox: Failed to build lexical sandbox: %s", e)
        ctx._lexical_sandbox = ""

    mark_complete(state, "sandbox", ctx)
    return True


def phase_content(ctx: ModuleContext, state: dict) -> bool:
    """Content: write prose. Delegates to pipeline_lib.phase_B_content."""
    if is_complete(state, "content"):
        log("  content: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  content: DRY-RUN — would dispatch content (phase-2-content.md)")
        return True

    _ensure_sandbox_loaded(ctx)
    ok = phase_B_content(ctx)

    if not ok:
        mark_failed(state, "content", ctx)
        return False

    # Track self-audit status from content phase
    self_audited = getattr(ctx, "_self_audited", False)
    if self_audited:
        log("  content: Self-audit PASSED in content session — validate will use reduced fix iterations")

    # Post-content gates
    content_path = ctx.paths.get("md")
    if content_path and content_path.exists():
        from audit.cleaners import clean_for_stats
        raw = content_path.read_text("utf-8")

        # Deterministic heading fix: Summary must be H1
        fixed = re.sub(r'^##\s+(Підсумок|Summary)\s*$', r'# \1', raw, flags=re.MULTILINE)
        if fixed != raw:
            content_path.write_text(fixed, "utf-8")
            log("  content: Fixed Summary/Підсумок heading level (## → #)")
            raw = fixed

        # Gate 1: Word count
        if ctx.word_target:
            wc = len(clean_for_stats(raw).split())
            threshold = ctx.word_target * 0.8
            if wc < threshold:
                log(f"  content: FAILED — word count {wc} < 80% target ({int(threshold)}w)")
                mark_failed(state, "content", ctx,
                            note=f"word-count-{wc}-below-80pct-{ctx.word_target}")
                return False

        # Gate 2: Content purity pre-screen
        from audit.checks.content_purity import check_content_purity
        purity_violations = check_content_purity(raw)
        critical = [v for v in purity_violations if v.get("severity") == "error"]
        if critical:
            log(f"  content: WARNING — {len(critical)} content purity issue(s) detected")
            for v in critical[:3]:
                log(f"    {v['type']}: {v['issue'][:100]}")

    # mark_complete replaces the entire phase dict, so self_audited must go in as **extra
    mark_complete(state, "content", ctx, **({"self_audited": True} if self_audited else {}))
    _invalidate_stale_artifacts(ctx)

    # Full-build: if activities+vocab were extracted during content, mark activities done
    if getattr(ctx, "full_build", False):
        act_path = ctx.paths.get("activities")
        voc_path = ctx.paths.get("vocabulary")
        if (act_path and act_path.exists() and act_path.stat().st_size > 10
                and voc_path and voc_path.exists() and voc_path.stat().st_size > 10):
            mark_complete(state, "activities", ctx, note="extracted-from-full-build")
            log("  content: Full-build activities+vocab adopted — skipping separate activities phase")

    return True


# ---------------------------------------------------------------------------
# Phase: activities
# ---------------------------------------------------------------------------

def phase_activities(ctx: ModuleContext, state: dict) -> bool:
    """Activities + Vocabulary generation."""
    if is_complete(state, "activities"):
        log("  activities: SKIP (already complete)")
        return True

    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")
    if (act_path and act_path.exists() and voc_path and voc_path.exists()):
        if _validate_activities_yaml(act_path):
            stale = False
            if getattr(ctx, "refresh", False):
                stale = True
                log("  activities: --rebuild flag set — regenerating activities/vocab")
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
                        log(f"  activities: Activities predate {ref_label} — regenerating")
                        break

            if stale:
                act_path.unlink(missing_ok=True)
                if voc_path and voc_path.exists():
                    voc_path.unlink(missing_ok=True)
                log("  activities: Deleted stale activities/vocab for regeneration")
            else:
                log("  activities: ADOPT — existing activities/vocab found and valid")
                mark_complete(state, "activities", ctx, note="adopted-existing")
                return True
        else:
            log("  activities: Existing activities invalid — deleting and regenerating")
            act_path.unlink(missing_ok=True)
            if voc_path and voc_path.exists():
                voc_path.unlink(missing_ok=True)
                log("  activities: Also deleted stale vocabulary (paired with invalid activities)")

    # Fast path: activities exist but vocabulary missing (truncation recovery)
    if (act_path and act_path.exists() and act_path.stat().st_size > 10
            and (not voc_path or not voc_path.exists())) and _validate_activities_yaml(act_path):
        log("  activities: Activities exist and valid, vocabulary missing — vocab-only dispatch")
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
                    task_id=f"v5-{ctx.slug}-pC-vocab",
                    model=ctx.model, stdout_only=True,
                    output_file=_gemini_output_path(ctx.slug, "pC-vocab"),
                    timeout=300,
                )
            if vok:
                vocab_text = _extract_delimiter_tolerant(vraw, "===VOCABULARY_START===", "===VOCABULARY_END===")
                if vocab_text and voc_path:
                    voc_path.parent.mkdir(parents=True, exist_ok=True)
                    voc_path.write_text(vocab_text, "utf-8")
                    log(f"  activities: Vocabulary generated via fast-path → {voc_path.name}")
                    if not _validate_activities_yaml(act_path):
                        log("  activities: FAILED — activities YAML failed schema validation")
                        mark_failed(state, "activities", ctx, note="activities-schema-invalid")
                        return False
                    mark_complete(state, "activities", ctx, task_id=f"v5-{ctx.slug}-pC-vocab")
                    return True
        log("  activities: Vocab fast-path failed — falling through to full dispatch")

    # Tier-based activities prompt dispatch
    activities_template_name = _get_activities_template(ctx.track, ctx.module_num)
    template = PHASES_DIR / activities_template_name
    if not template.exists():
        template = PHASES_DIR / "phase-3-activities.md"
        log(f"  activities: Tier template {activities_template_name} not found, falling back to phase-3-activities.md")
    else:
        log(f"  activities: Using tier template: {activities_template_name}")
    if not template.exists():
        log(f"  activities: ERROR — template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "phase-C-prompt.md"
    _ensure_sandbox_loaded(ctx)
    overrides = {"LEXICAL_SANDBOX": getattr(ctx, "_lexical_sandbox", "")}
    if not fill_template(template, ctx.orch_dir / "placeholders.yaml", prompt_file, overrides=overrides):
        return False

    if ctx.dry_run:
        log("  activities: DRY-RUN — would dispatch phase-3-activities.md")
        return True

    use_claude = "C" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_C", CLAUDE_MODEL_ACTIVITIES)
        log(f"  activities: Dispatching activities + vocab via Claude ({claude_model})...")
        ok, raw_output = _dispatch_claude_phase(
            prompt_file, "Phase C", model=claude_model, timeout=600,
        )
    else:
        log("  activities: Dispatching activities + vocab...")
        output_file = _gemini_output_path(ctx.slug, "pC")
        ok, raw_output = dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v5-{ctx.slug}-pC",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_ACTIVITIES,
        )
    if not ok:
        log(f"  activities: FAILED — {'Claude' if use_claude else 'Gemini'} dispatch error")
        mark_failed(state, "activities", ctx)
        return False

    wrote_activities = act_path and act_path.exists() and act_path.stat().st_size > 10
    wrote_vocab = voc_path and voc_path.exists() and voc_path.stat().st_size > 10

    if not wrote_activities:
        activities_text = _extract_delimiter(raw_output, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
        if activities_text and act_path:
            act_path.parent.mkdir(parents=True, exist_ok=True)
            act_path.write_text(activities_text, "utf-8")
            wrote_activities = True
            log(f"  activities: Activities extracted → {act_path.name}")
            (ctx.orch_dir / "phase-C-output-activities.yaml").write_text(activities_text, "utf-8")
            save_gemini_session(ctx.orch_dir, label="phase-C")

    if not wrote_vocab:
        vocab_text = _extract_delimiter_tolerant(raw_output, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            wrote_vocab = True
            log(f"  activities: Vocabulary extracted → {voc_path.name}")
            (ctx.orch_dir / "phase-C-output-vocabulary.yaml").write_text(vocab_text, "utf-8")

    # Extract and log friction
    friction = _extract_delimiter(raw_output, "===FRICTION_START===", "===FRICTION_END===")
    if friction:
        friction_file = ctx.orch_dir / "phase-C-friction.md"
        friction_file.write_text(friction, encoding="utf-8")
        log(f"  activities: Friction report saved → {friction_file.name}")
        is_real_truncation = (
            "TOKEN_LIMIT_TRUNCATION" in friction
            and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
        )
        if is_real_truncation:
            log("  activities: Gemini reported token limit truncation")

    # Vocabulary fallback
    if wrote_activities and not wrote_vocab and "===VOCABULARY_START===" in raw_output:
        log("  activities: Vocabulary truncated — dispatching vocab-only fallback")
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
                    task_id=f"v5-{ctx.slug}-pC-vocab",
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
                    log(f"  activities: Vocabulary extracted from fallback → {voc_path.name}")
                else:
                    log("  activities: Vocab fallback returned no valid delimited content")
            else:
                log("  activities: Vocab fallback dispatch failed")

    if not wrote_activities or not wrote_vocab:
        log(f"  activities: FAILED — missing files: activities={wrote_activities}, vocab={wrote_vocab}")
        mark_failed(state, "activities", ctx,
                    note=f"missing-files-act={wrote_activities}-voc={wrote_vocab}")
        return False

    # Post-C schema validation gate
    if act_path and act_path.exists() and not _validate_activities_yaml(act_path):
        log("  activities: FAILED — activities YAML failed schema validation")
        mark_failed(state, "activities", ctx, note="activities-schema-invalid")
        return False

    mark_complete(state, "activities", ctx, task_id=f"v5-{ctx.slug}-pC")
    return True


# ---------------------------------------------------------------------------
# Phase: validate
# ---------------------------------------------------------------------------

def phase_validate(ctx: ModuleContext, state: dict) -> bool:
    """Validate: full deterministic checks + Gemini fix loop."""
    phase = "validate"
    _skip_review = True
    if is_complete(state, phase):
        log("  validate: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  validate: DRY-RUN — would run full audit + screen + fix loop")
        return True

    # Check sidecar files exist
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

    # Auto-fix pass
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

    _NON_BLOCKING_ISSUE_TYPES = {"LLM_FILLER"}

    def _only_non_blocking(scr: DScreenResult) -> bool:
        return all(
            i["type"] in _NON_BLOCKING_ISSUE_TYPES for i in scr.deterministic_issues
        )

    # Initial screen
    screen = _deterministic_screen(ctx, skip_review=_skip_review)
    _log_screen("Initial", screen)

    # Plan auto-fix
    if screen.vesum_not_found:
        try:
            from plan_autofix import auto_fix_plan
            plan_path = ctx.paths.get("plan")
            if plan_path and plan_path.exists():
                n_plan_fixes, plan_changelog = auto_fix_plan(
                    plan_path, screen.deterministic_issues, screen.vesum_not_found)
                if n_plan_fixes:
                    log(f"  validate: Plan auto-fix: {n_plan_fixes} fix(es)")
                    for entry in plan_changelog:
                        log(f"    {entry}")
        except Exception as e:
            logger.warning("validate: Plan auto-fix failed: %s", e)

    if screen.audit_passed and not screen.deterministic_issues:
        _save_screen_result(ctx, screen)
        mark_complete(state, phase, ctx, attempts=0)
        _update_pipeline_status(ctx, "draft")
        return True

    if screen.audit_passed and _only_non_blocking(screen):
        n = len(screen.deterministic_issues)
        log(f"  validate: PASS — audit gates pass, {n} non-blocking issue(s) (filler)")
        _save_screen_result(ctx, screen)
        mark_complete(state, phase, ctx, attempts=0,
                      note=f"pass-with-{n}-filler-issues")
        _update_pipeline_status(ctx, "draft")
        return True

    # Gemini proofread
    _PROSE_ISSUE_TYPES = {"RUSSIANISM", "LLM_FILLER", "PEDAGOGICAL", "DECODABILITY"}
    _PROSE_AUDIT_KEYWORDS = {"naturalness", "word_count", "immersion", "engagement", "euphony"}
    _has_prose_issues = any(
        i["type"] in _PROSE_ISSUE_TYPES for i in screen.deterministic_issues
    )
    if not _has_prose_issues and not screen.audit_passed:
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

        screen = _deterministic_screen(ctx, skip_review=_skip_review)
        _log_screen("Post-proofread", screen)

        if screen.audit_passed and (not screen.deterministic_issues or _only_non_blocking(screen)):
            n = len(screen.deterministic_issues)
            note = "proofread-fix" if n == 0 else f"proofread-fix-with-{n}-filler"
            _save_screen_result(ctx, screen)
            mark_complete(state, phase, ctx, attempts=0, note=note)
            _update_pipeline_status(ctx, "draft")
            return True

    # Gemini fix loop — reduce iterations if content was self-audited
    max_iters = getattr(ctx, "max_fix", None) or _max_audit_iters(ctx.track)
    content_self_audited = state.get("phases", {}).get("content", {}).get("self_audited", False)
    if content_self_audited and max_iters > 2:
        log(f"  validate: Content was self-audited — reducing max fix iterations from {max_iters} to 2")
        max_iters = 2
    ctx.paths["md"]
    prev_audit_output = screen.audit_output

    consecutive_failures = 0
    _seen_fix_hashes: set[str] = set()
    for attempt in range(1, max_iters + 1):
        log(f"  validate: Fix attempt {attempt}/{max_iters}...")

        fix_prompt = _build_fix_prompt(ctx, screen.audit_output, content_only=False,
                                       deterministic_issues=screen.deterministic_issues)

        # Guard: skip if fix prompt has no specific violations (just boilerplate)
        # Count "### Fix" headers — if zero, the prompt is empty/useless
        _fix_count = fix_prompt.count("### Fix")
        _other_failures = "### Other Audit Failures" in fix_prompt
        if _fix_count == 0 and not _other_failures:
            log("  validate: EMPTY fix prompt (no violations extracted), escalating directly")
            if _escalate_fix(ctx, screen.audit_output, "validate", content_only=False, skip_review=True):
                screen = _deterministic_screen(ctx, skip_review=_skip_review)
                _save_screen_result(ctx, screen)
                mark_complete(state, phase, ctx,
                              attempts=attempt, note="escalation-empty-fix")
                _update_pipeline_status(ctx, "draft")
                return True
            _save_screen_result(ctx, screen)
            mark_failed(state, phase, ctx, attempts=attempt, note="empty-fix-exhausted")
            _update_pipeline_status(ctx, "needs-manual-review")
            return False

        # Dedup: skip if we already sent an identical fix prompt
        _fix_hash = hashlib.sha256(fix_prompt.encode()).hexdigest()[:16]
        if _fix_hash in _seen_fix_hashes:
            log("  validate: DEDUP — fix prompt identical to a previous attempt, escalating")
            if _escalate_fix(ctx, screen.audit_output, "validate", content_only=False, skip_review=True):
                screen = _deterministic_screen(ctx, skip_review=_skip_review)
                _save_screen_result(ctx, screen)
                mark_complete(state, phase, ctx,
                              attempts=attempt, note="escalation-claude-dedup")
                _update_pipeline_status(ctx, "draft")
                return True
            _save_screen_result(ctx, screen)
            mark_failed(state, phase, ctx, attempts=attempt, note="dedup-exhausted")
            _update_pipeline_status(ctx, "needs-manual-review")
            return False
        _seen_fix_hashes.add(_fix_hash)

        fix_prompt_file = ctx.orch_dir / f"validate-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, "utf-8")

        fix_output = _gemini_output_path(ctx.slug, f"validate-fix{attempt}")
        ok, _ = dispatch_gemini(
            _dispatch_prompt(ctx, fix_prompt_file),
            task_id=f"v5-{ctx.slug}-validate-fix{attempt}",
            model=ctx.model, allow_write=True, output_file=fix_output,
            timeout=TIMEOUT_FIX,
        )
        if not ok:
            consecutive_failures += 1
            log(f"  validate: Fix dispatch {attempt} failed (consecutive: {consecutive_failures})")
            if consecutive_failures >= 2:
                log("  validate: 2 consecutive dispatch failures — skipping remaining fix attempts")
                break
            continue
        consecutive_failures = 0

        if fix_output.exists():
            fix_text = fix_output.read_text("utf-8")
            # Save raw Gemini output + session to orchestration for debugging fix loops
            (ctx.orch_dir / f"validate-fix{attempt}-raw.md").write_text(fix_text, "utf-8")
            save_gemini_session(ctx.orch_dir, label=f"validate-fix{attempt}")
            if "===SECTION_FIX_START===" in fix_text:
                _apply_section_fixes(ctx.paths["md"], fix_text)
                if ctx.paths.get("activities") and ctx.paths["activities"].exists():
                    _apply_section_fixes(ctx.paths["activities"], fix_text)
                _vp = ctx.paths.get("vocabulary")
                if _vp and _vp.exists():
                    _apply_section_fixes(_vp, fix_text)

        _run_deterministic_fixes(ctx)

        screen = _deterministic_screen(ctx, skip_review=_skip_review)

        if attempt > 0 and screen.audit_output == prev_audit_output:
            log(f"  validate: WARNING — fix {attempt} made no progress")
            if screen.audit_passed:
                log("  validate: Audit PASSES — exiting fix loop")
                _save_screen_result(ctx, screen)
                mark_complete(state, phase, ctx, attempts=attempt,
                              note=f"pass-with-{len(screen.deterministic_issues)}-info-issues")
                _update_pipeline_status(ctx, "draft")
                return True
        prev_audit_output = screen.audit_output

        if screen.audit_passed and (not screen.deterministic_issues or _only_non_blocking(screen)):
            _save_screen_result(ctx, screen)
            mark_complete(state, phase, ctx, attempts=attempt)
            _update_pipeline_status(ctx, "draft")
            return True

        if attempt >= max_iters:
            log(f"  validate: EXHAUSTED — {max_iters} fix attempts")
            if _escalate_fix(ctx, screen.audit_output, "validate", content_only=False, skip_review=True):
                screen = _deterministic_screen(ctx, skip_review=_skip_review)
                _save_screen_result(ctx, screen)
                mark_complete(state, phase, ctx,
                              attempts=attempt, note="escalation-claude")
                _update_pipeline_status(ctx, "draft")
                return True
            _save_screen_result(ctx, screen)
            mark_failed(state, phase, ctx,
                        attempts=attempt, note="exhausted")
            _update_pipeline_status(ctx, "needs-manual-review")
            return False

    _save_screen_result(ctx, screen)
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


# ---------------------------------------------------------------------------
# Phase: review (Claude)
# ---------------------------------------------------------------------------

def phase_review_claude(ctx: ModuleContext, state: dict) -> bool:
    """Review: Claude structured review + up to 2 fix attempts."""
    phase = "review"
    if is_complete(state, phase):
        log("  review: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  review: DRY-RUN — would dispatch Claude structured review")
        return True

    screen = _load_screen_result(ctx)
    if screen is None:
        log("  review: No cached screen — running fresh screen")
        screen = _deterministic_screen(ctx)

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

    log("  review: Preparing structured review prompt...")

    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    track_calibration = _get_track_calibration(ctx.track, module_num)
    russicism_table = _get_russicism_table(ctx.track)

    prompt_file = ctx.orch_dir / "review-prompt.md"
    if not fill_template(d1_template, ctx.orch_dir / "placeholders.yaml", prompt_file):
        return False

    prompt_text = prompt_file.read_text("utf-8")
    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", screen.h2_sections)
    prompt_text = prompt_text.replace("{TRACK_CALIBRATION}", track_calibration or "(No track calibration available)")
    prompt_text = prompt_text.replace("{DETERMINISTIC_ISSUES}", _format_deterministic_issues(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{RUSSIANISM_TABLE}", russicism_table or "(No track-specific Russianism table available — use general checklist)")
    prompt_text = prompt_text.replace("{FILLER_PHRASES}", _format_filler_phrases(screen.deterministic_issues))

    rag_context = _prefetch_rag_context(ctx)
    prompt_text = prompt_text.replace("{RAG_PRIMARY_SOURCES}", rag_context)

    vesum_word_context = _format_vesum_verification(screen.vesum_stats, screen.vesum_not_found)
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", vesum_word_context)

    prompt_file.write_text(prompt_text, "utf-8")

    log(f"  review: Dispatching Claude review ({claude_model}, {review_timeout}s)...")
    log(f"    Metrics: {screen.metrics.get('COMPUTED_WORD_COUNT', '?')}w / "
        f"{screen.metrics.get('COMPUTED_WORD_TARGET', '?')}w, "
        f"{screen.metrics.get('COMPUTED_ACTIVITY_COUNT', '?')} activities, "
        f"immersion {screen.metrics.get('COMPUTED_IMMERSION_PERCENT', '?')}%")

    _pre_d1_snapshots = _snapshot_module_files(ctx)

    ok, raw_output = _dispatch_claude_phase(
        prompt_file, "Phase D.1",
        model=claude_model, timeout=review_timeout,
        allow_tools=["Read", "Grep", "Glob", "Edit"],
    )
    if not ok:
        log("  review: Dispatch FAILED")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed")
        return False

    _log_d1_edits(ctx, _pre_d1_snapshots)

    d1 = _parse_d1_review(raw_output)

    if not d1.ok or not d1.raw_review:
        log("  review: WARNING — no REVIEW delimiters in output (retrying)")
        (ctx.orch_dir / "review-raw-output.md").write_text(raw_output, "utf-8")

        ok2, raw2 = _dispatch_claude_phase(
            prompt_file, "Phase D.1 (retry)",
            model=claude_model, timeout=review_timeout,
            allow_tools=["Read", "Grep", "Glob", "Edit"],
        )
        if ok2:
            d1 = _parse_d1_review(raw2)

        if not d1.ok or not d1.raw_review:
            log("  review: Retry also failed — no delimiters")
            mark_failed(state, phase, ctx, attempts=1, note="no-review")
            return False

    review_text = d1.raw_review

    qg_ok, qg_reason = _quick_review_quality_gate(review_text, ctx.paths["md"])
    if not qg_ok:
        log(f"  review: REJECTED — {qg_reason}")
        (ctx.orch_dir / "review-rejected.md").write_text(review_text, "utf-8")
        mark_failed(state, phase, ctx, attempts=1, note="shallow-review")
        return False

    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** {claude_model}\n\n{review_text}"

    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
    (ctx.orch_dir / "review-raw-output.md").write_text(raw_output, "utf-8")
    log(f"  review: Review saved → {ctx.paths['review'].name}")

    n_d1_fixes = _apply_module_fixes(ctx, raw_output)
    if n_d1_fixes > 0:
        log(f"  review: Applied {n_d1_fixes} inline fix(es) from review")
    elif "===SECTION_FIX_START===" in raw_output:
        log("  review: Fix block found but 0 fixes matched — check review-raw-output.md")

    _run_deterministic_fixes(ctx)

    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

    review_says_fail = d1.verdict == "FAIL"
    if not review_says_fail and d1.scores.get("overall", 10) < 9.0:
        review_says_fail = True
    if not d1.verdict:
        _status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
        _score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
        if (_status_m and _status_m.group(1) == "FAIL") or (_score_m and float(_score_m.group(1)) < 9.0):
            review_says_fail = True

    if passed and not review_says_fail:
        log("  review: PASS (no repair needed)")
        mark_complete(state, phase, ctx, attempts=1, note="review-only")
        _update_pipeline_status(ctx, "reviewed")
        return True

    if passed and review_says_fail and n_d1_fixes > 0:
        log(f"  review: PASS (D.1 inline fixes resolved review issues — {n_d1_fixes} fix(es))")
        mark_complete(state, phase, ctx, attempts=1, note="d1-inline-fixes")
        _update_pipeline_status(ctx, "reviewed")
        return True

    _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
    if any(f"\u274c [{tag}]" in audit_out for tag in _CITATION_FAILURES):
        log("  review: REVIEW QUALITY FAILURE — fabricated/unverified citations")
        if ctx.paths["review"].exists():
            ctx.paths["review"].unlink()
        mark_failed(state, phase, ctx, attempts=1, note="citation-failure")
        return False

    auto_fix_count = _run_deterministic_fixes(ctx)
    if auto_fix_count > 0:
        passed_after_autofix, audit_out = run_verify(ctx.paths["md"], content_only=False)
        if passed_after_autofix and not review_says_fail:
            mark_complete(state, phase, ctx, attempts=1, note="autofix")
            _update_pipeline_status(ctx, "reviewed")
            return True

    if _all_issues_diffuse(audit_out):
        log("  review: SKIPPED fix — all issues are diffuse (needs manual review)")
        mark_failed(state, phase, ctx, attempts=1, note="needs-manual-review")
        _update_pipeline_status(ctx, "needs-manual-review")
        return False

    _audit_only_fix = not review_says_fail and not passed

    fix_timeout = _get_fix_timeout(ctx.track, audit_only=_audit_only_fix)

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
        failures += _extract_gate_blockers(ctx)
        failures += _extract_vesum_failures(ctx)

        prompt_file2 = ctx.orch_dir / f"review-fix-{fix_iter + 1}-prompt.md"
        if not fill_template(d2_template, ctx.orch_dir / "placeholders.yaml", prompt_file2):
            return False

        prompt2_text = prompt_file2.read_text("utf-8")
        prompt2_text = prompt2_text.replace("{EXTRACTED_FIX_PLAN}", fix_plan)
        prompt2_text = prompt2_text.replace("{INJECTED_AUDIT_FAILURES}", failures)
        prompt2_text = _inject_file_contents(prompt2_text, ctx)
        prompt_file2.write_text(prompt2_text, "utf-8")

        before_d2 = _snapshot_module_files(ctx)

        ok2, raw_output2 = _dispatch_claude_phase(
            prompt_file2, f"Phase D.2{iter_suffix}",
            model=claude_model, timeout=fix_timeout,
            allow_tools=["Edit", "Grep"],
        )
        if not ok2:
            log(f"  review: Fix dispatch failed{iter_suffix}")
            mark_failed(state, phase, ctx,
                        attempts=total_attempts, note="fix-dispatch-failed")
            return False

        after_d2 = _snapshot_module_files(ctx)
        changed_lines = 0
        for label in before_d2:
            if label in after_d2:
                changed_lines += _count_diff_lines(before_d2[label], after_d2[label])

        if changed_lines > 200:
            log(f"  review: REJECTED — D.2 changed {changed_lines} lines (max 200){iter_suffix}")
            for label, p in _module_file_paths(ctx):
                if label in before_d2 and p:
                    p.write_text(before_d2[label], "utf-8")
            mark_failed(state, phase, ctx,
                        attempts=total_attempts, note="diff-too-large")
            _update_pipeline_status(ctx, "needs-manual-review")
            return False
        if changed_lines == 0:
            log(f"  review: WARNING — D.2 made no file changes{iter_suffix}")
            (ctx.orch_dir / f"review-fix-{fix_iter + 1}-raw.md").write_text(raw_output2, "utf-8")
        else:
            log(f"  review: D.2 applied fixes ({changed_lines} lines changed){iter_suffix}")

        _run_deterministic_fixes(ctx)
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

        if passed:
            log(f"  review: PASS (after fix {fix_iter + 1})")
            mark_complete(state, phase, ctx,
                          attempts=total_attempts, note=f"fix-iter{fix_iter + 1}")
            _update_pipeline_status(ctx, "reviewed")
            return True

        if fix_iter < MAX_REVIEW_FIX_ITERS - 1:
            log(f"  review: Fix {fix_iter + 1} insufficient — trying again...")

    log("  review: EXHAUSTED — review + fix attempts all insufficient")
    mark_failed(state, phase, ctx,
                attempts=2 + MAX_REVIEW_FIX_ITERS, note="needs-manual-review")
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


# ---------------------------------------------------------------------------
# Phase: review (Gemini RAG-grounded)
# ---------------------------------------------------------------------------

def phase_review_gemini(ctx: ModuleContext, state: dict) -> bool:
    """Gemini RAG-grounded review: sharded Fact Checker + Language Pedant."""
    phase = "review"
    if is_complete(state, phase):
        log("  review-gemini: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  review-gemini: DRY-RUN — would dispatch Gemini sharded review")
        return True

    # 1. Load cached screen from validate phase
    screen = _load_screen_result(ctx)
    if screen is None:
        log("  review-gemini: No cached screen — running fresh screen")
        screen = _deterministic_screen(ctx)

    # 2. Load RAG discovery data
    rag_data = _load_rag_for_review(ctx)
    total_rag = len(rag_data["text_chunks"]) + len(rag_data["images"]) + len(rag_data["literary"])
    log(f"  review-gemini: RAG data loaded — {total_rag} items "
        f"(text: {len(rag_data['text_chunks'])}, images: {len(rag_data['images'])}, "
        f"literary: {len(rag_data['literary'])})")

    # 3-4. Dispatch Pass 1 + Pass 2 in parallel
    from concurrent.futures import ThreadPoolExecutor

    raw1 = ""
    raw2 = ""
    pass1_result: D1Result | None = None
    pass2_result: D1Result | None = None

    pass1_prompt: str | None = None
    if total_rag > 0:
        pass1_prompt = _build_pass1_prompt(ctx, screen, rag_data)
        (ctx.orch_dir / "review-pass1-prompt.md").write_text(pass1_prompt, "utf-8")
    else:
        log("  review-gemini: Pass 1 SKIPPED (no RAG sources)")
        pass1_result = D1Result(ok=True, verdict="PASS", raw_review="(No RAG sources available — factual check skipped)")

    pass2_prompt = _build_pass2_prompt(ctx, screen)
    (ctx.orch_dir / "review-pass2-prompt.md").write_text(pass2_prompt, "utf-8")

    def _dispatch_pass1() -> tuple[bool, str]:
        return pipeline_lib.dispatch_gemini_raw(
            pass1_prompt,
            task_id=f"{ctx.slug}-review-pass1",
            timeout=600,
        )

    def _dispatch_pass2() -> tuple[bool, str]:
        return pipeline_lib.dispatch_gemini_raw(
            pass2_prompt,
            task_id=f"{ctx.slug}-review-pass2",
            timeout=600,
        )

    log("  review-gemini: Dispatching review passes"
        f" {'(Pass 1 + Pass 2 in parallel)' if pass1_prompt else '(Pass 2 only)'}...")

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut1 = pool.submit(_dispatch_pass1) if pass1_prompt else None
        fut2 = pool.submit(_dispatch_pass2)

        if fut1:
            ok1, raw1 = fut1.result()
            if ok1:
                (ctx.orch_dir / "review-pass1-raw.md").write_text(raw1, "utf-8")
                pass1_result = _parse_factual_review(raw1)
                if pass1_result.ok:
                    disc_count = len([i for i in pass1_result.issues if i.get("type") == "FACTUAL_DISCREPANCY"])
                    log(f"  review-gemini: Pass 1 — {pass1_result.verdict} "
                        f"({disc_count} discrepancies, score {pass1_result.scores.get('factual_accuracy', '?')})")
                else:
                    log("  review-gemini: Pass 1 — failed to parse output")
            else:
                log("  review-gemini: Pass 1 — dispatch failed")

        ok2, raw2 = fut2.result()

    if ok2:
        (ctx.orch_dir / "review-pass2-raw.md").write_text(raw2, "utf-8")
        pass2_result = _parse_d1_review(raw2)
        if pass2_result.ok:
            log(f"  review-gemini: Pass 2 — {pass2_result.verdict} "
                f"(overall {pass2_result.scores.get('overall', '?')}/10)")
        else:
            log("  review-gemini: Pass 2 — failed to parse output")
    else:
        log("  review-gemini: Pass 2 — dispatch failed")

    # 5. Merge results
    merged = _merge_gemini_review_passes(pass1_result, pass2_result)
    if not merged.ok:
        log("  review-gemini: Merge FAILED — both passes unusable")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed")
        return False

    pass1_contributed = (pass1_result is not None and pass1_result.ok
                         and "factual_accuracy" in pass1_result.scores)
    review_grounding = "rag-textbook" if pass1_contributed else "linguistic-only"
    if not pass1_contributed and total_rag > 0:
        log("  review-gemini: WARNING — Pass 1 (factual check) failed, "
            "review grounding downgraded to linguistic-only")

    review_text = merged.raw_review

    # 6. Quality gate check
    if len(review_text.split()) < 100:
        log(f"  review-gemini: REJECTED — review too short ({len(review_text.split())} words)")
        mark_failed(state, phase, ctx, attempts=1, note="shallow-review")
        return False

    # 7. Inject Reviewed-By metadata
    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** gemini-2.5-pro (RAG-grounded)\n\n{review_text}"

    # 8. Save review
    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
    log(f"  review-gemini: Review saved → {ctx.paths['review'].name}")

    # 9. Apply inline FIND/REPLACE fixes from both passes
    n_fixes = 0
    if raw1 and "===SECTION_FIX_START===" in raw1:
        n_fixes += _apply_module_fixes(ctx, raw1)
    if raw2 and "===SECTION_FIX_START===" in raw2:
        n_fixes += _apply_module_fixes(ctx, raw2)
    if n_fixes > 0:
        log(f"  review-gemini: Applied {n_fixes} inline fix(es) from review passes")

    # 10. Run deterministic fixes
    _run_deterministic_fixes(ctx)

    # 10.5 Plan auto-fix
    if screen and screen.vesum_not_found:
        try:
            from plan_autofix import auto_fix_plan
            plan_path = ctx.paths.get("plan")
            if plan_path and plan_path.exists():
                n_plan_fixes, plan_changelog = auto_fix_plan(
                    plan_path, screen.deterministic_issues, screen.vesum_not_found)
                if n_plan_fixes:
                    log(f"  review: Plan auto-fix: {n_plan_fixes} fix(es)")
                    for entry in plan_changelog:
                        log(f"    {entry}")
        except Exception as e:
            logger.warning("review: Plan auto-fix failed: %s", e)

    # 11. Post-review audit
    passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

    review_says_fail = merged.verdict == "FAIL"
    if not review_says_fail and merged.scores.get("overall", 10) < 9.0:
        review_says_fail = True

    if passed and not review_says_fail:
        log("  review-gemini: PASS (no repair needed)")
        return _complete_gemini_review(ctx, state, phase, 1, "gemini-review-only", grounding=review_grounding)

    if passed and review_says_fail and n_fixes > 0:
        log(f"  review-gemini: PASS (inline fixes resolved review issues — {n_fixes} fix(es))")
        return _complete_gemini_review(ctx, state, phase, 1, "gemini-inline-fixes", grounding=review_grounding)

    if _all_issues_diffuse(audit_out):
        log("  review-gemini: SKIPPED fix — all issues diffuse (needs manual review)")
        mark_failed(state, phase, ctx, attempts=1, note="needs-manual-review")
        _update_pipeline_status(ctx, "needs-manual-review")
        return False

    _audit_only_fix = not review_says_fail and not passed
    if _audit_only_fix:
        fix_plan = (
            "**IMPORTANT: The review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions — they are informational only.**\n\n"
            "(Review omitted — verdict was PASS)\n"
        )
    else:
        fix_plan = _extract_fix_plan(review_text)

    # 12. Fix loop
    for fix_iter in range(MAX_REVIEW_FIX_ITERS):
        total_attempts = 2 + fix_iter
        log(f"  review-gemini: Fix attempt {fix_iter + 1}/{MAX_REVIEW_FIX_ITERS}...")

        applied = _gemini_fix_iteration(ctx, fix_plan, audit_out, fix_iter)
        if not applied and fix_iter == 0:
            log("  review-gemini: No fixes applied — trying once more")

        _run_deterministic_fixes(ctx)
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)

        if passed:
            log(f"  review-gemini: PASS (after fix {fix_iter + 1})")
            return _complete_gemini_review(ctx, state, phase, total_attempts, f"gemini-fix-iter{fix_iter + 1}", grounding=review_grounding)

        if fix_iter < MAX_REVIEW_FIX_ITERS - 1:
            log(f"  review-gemini: Fix {fix_iter + 1} insufficient — trying again...")

    log("  review-gemini: EXHAUSTED — review + fix attempts all insufficient")
    mark_failed(state, phase, ctx,
                attempts=2 + MAX_REVIEW_FIX_ITERS, note="needs-manual-review")
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


# ---------------------------------------------------------------------------
# Phase: review (dispatch)
# ---------------------------------------------------------------------------

def phase_review(ctx: ModuleContext, state: dict) -> bool:
    """Route review to Gemini (default) or Claude based on ctx.review_agent."""
    review_agent = getattr(ctx, "review_agent", "gemini")
    if review_agent == "claude":
        log("  review: Using Claude reviewer (--review-claude)")
        return phase_review_claude(ctx, state)
    else:
        log("  review: Using Gemini RAG-grounded reviewer (--review)")
        return phase_review_gemini(ctx, state)


# ---------------------------------------------------------------------------
# Phase: mdx
# ---------------------------------------------------------------------------

_GENERIC_URL_PATTERNS = [
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/?$"),
    re.compile(r"^https?://ukrainianlessons\.com/?$"),
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/podcast/?$"),
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/the-podcast/?$"),
    re.compile(r"youtube\.com/watch\?v=example"),
    re.compile(r"^https?://sum\.in\.ua/?$"),
    re.compile(r"^https?://slovnyk\.ua/?$"),
    re.compile(r"^https?://pravopys\.net/?$"),
    re.compile(r"^https?://r2u\.org\.ua/?$"),
    re.compile(r"^https?://(www\.)?youtube\.com/@\w+/?$"),
]

_GENERIC_TITLES = {
    "Ukrainian Lessons Podcast", "Ukrainian Lessons", "Ukrainian Grammar",
    "Speak Ukrainian YouTube", "Colors Guide", "Verb Practice",
}

_RESOURCES_PATH = Path(__file__).resolve().parent.parent / "docs" / "resources" / "external_resources.yaml"


def _is_generic_url(url: str) -> bool:
    return any(p.search(url) for p in _GENERIC_URL_PATTERNS)


def _is_generic_title(title: str) -> bool:
    return title.strip() in _GENERIC_TITLES


def _clean_external_resources(ctx: ModuleContext) -> None:
    """Remove garbage entries from this module's external_resources.yaml slot."""
    if not _RESOURCES_PATH.exists():
        return
    try:
        import yaml
        data = yaml.safe_load(_RESOURCES_PATH.read_text("utf-8"))
        resources = data.get("resources", {})
    except Exception:
        return

    # Find this module's key
    slug = ctx.slug
    matching_keys = [k for k in resources if k == slug or k.endswith(f"-{slug}")]
    if not matching_keys:
        return

    removed = 0
    for key in matching_keys:
        module_data = resources.get(key)
        if not module_data:
            continue
        for cat in ("youtube", "articles", "websites"):
            items = module_data.get(cat, [])
            if not items:
                continue
            clean_items = []
            for item in items:
                url = item.get("url", "")
                title = item.get("title", "")
                if _is_generic_url(url) or _is_generic_title(title) or "example" in url:
                    removed += 1
                else:
                    clean_items.append(item)
            if clean_items:
                module_data[cat] = clean_items
            elif cat in module_data:
                del module_data[cat]

    if removed:
        with open(_RESOURCES_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False, width=120)
        log(f"  mdx: Cleaned {removed} bad external resource entries")


def phase_mdx(ctx: ModuleContext) -> bool:
    """MDX generation + lint. Deterministic, no LLM."""
    if ctx.dry_run:
        log("  mdx: DRY-RUN — would generate MDX")
        return True

    # Clean garbage from external resources before generating MDX
    _clean_external_resources(ctx)

    log("  mdx: Generating MDX...")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "generate_mdx.py"),
         "l2-uk-en", ctx.track, str(ctx.module_num)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        log(f"  mdx: WARNING — MDX generation returned {result.returncode}")
    return True


# ============================================================================
# 4. Pipeline runner
# ============================================================================

PHASE_FUNCTIONS: dict[str, Any] = {
    "research":   phase_research,
    "discover":   phase_discover,
    "sandbox":    phase_sandbox,
    "content":    phase_content,
    "activities": phase_activities,
    "validate":   phase_validate,
    "review":     phase_review,
    "mdx":        phase_mdx,
}


def _call_phase(func: Any, phase_id: str, ctx: ModuleContext,
                state: dict) -> bool:
    """Call a phase function with the appropriate signature."""
    if phase_id == "mdx":
        return func(ctx)
    else:
        return func(ctx, state)


def run_pipeline(ctx: ModuleContext, state: dict, research_only: bool = False) -> bool:
    """Execute the v5 named-phase pipeline."""
    log(f"\nPipeline v5: named phases — {len(PHASES)} phases")
    if ctx.dry_run:
        log("  (DRY-RUN — no dispatches)")
    log("")

    # Determine sequence
    has_review = getattr(ctx, "review", False)
    if research_only:
        sequence = ["research"]
    elif has_review:
        sequence = list(PHASES)
    else:
        sequence = [p for p in PHASES if p != "review"]

    # Print phase plan
    for phase_id in sequence:
        label = PHASE_LABELS.get(phase_id, phase_id)
        skip_note = " [DONE]" if is_complete(state, phase_id) else ""
        log(f"  {phase_id}: {label}{skip_note}")
    log("")

    # --force-phase: single phase only
    force_phase = ctx.force_phase
    if force_phase:
        force_key = force_phase.lower()
        if force_key not in PHASE_FUNCTIONS:
            log(f"  ERROR: Unknown v5 phase '{force_phase}'. Valid: {', '.join(PHASES)}")
            return False
        log(f"  --force-phase {force_key}: running only this phase")
        # Clear state for this phase
        phases = state.setdefault("phases", {})
        phases.pop(force_key, None)
        save_state(ctx, state)
        # Force research re-run if needed
        if force_key == "research":
            ctx.force_research = True  # type: ignore[attr-defined]
        return _call_phase(PHASE_FUNCTIONS[force_key], force_key, ctx, state)

    # --restart-from: clear from this phase onward and run
    restart_from = getattr(ctx, "restart_from", None)
    if restart_from:
        restart_key = restart_from.lower()
        if restart_key not in PHASE_FUNCTIONS:
            log(f"  ERROR: Unknown v5 phase '{restart_from}'. Valid: {', '.join(PHASES)}")
            return False
        idx = PHASES.index(restart_key)
        remaining = PHASES[idx:]
        if not has_review:
            remaining = [p for p in remaining if p != "review"]
        # Clear state AND output files for restarted phases
        phases = state.setdefault("phases", {})
        _phase_outputs = {
            "content": ["md"],
            "activities": ["activities", "vocabulary"],
            "research": ["research"],
        }
        for pid in remaining:
            phases.pop(pid, None)
            for path_key in _phase_outputs.get(pid, []):
                p = ctx.paths.get(path_key)
                if p and p.exists():
                    p.unlink()
                    log(f"  --restart-from: deleted {p.name}")
        save_state(ctx, state)
        if "research" in remaining:
            ctx.force_research = True  # type: ignore[attr-defined]
        log(f"  --restart-from {restart_key}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            if not _call_phase(PHASE_FUNCTIONS[phase_id], phase_id, ctx, state):
                _expected = {
                    "research": ctx.paths.get("research"),
                    "content": ctx.paths.get("md"),
                    "activities": ctx.paths.get("activities"),
                }
                _exp_path = _expected.get(phase_id)
                if _exp_path and not _exp_path.exists():
                    log(f"  {phase_id}: WARNING — no output produced ({_exp_path.name} missing), pipeline may halt")
                if phase_id in NON_BLOCKING:
                    log(f"  {phase_id}: FAIL — continuing")
                    continue
                log(f"\n  PIPELINE STOPPED at {phase_id}")
                return False
        return True

    # --stop-before
    stop_before = getattr(ctx, "stop_before_phase", None)

    # Full pipeline
    for phase_id in sequence:
        if stop_before and phase_id == stop_before:
            log(f"\n  Stopping before {phase_id}")
            return True

        func = PHASE_FUNCTIONS[phase_id]
        ok = _call_phase(func, phase_id, ctx, state)
        if not ok:
            # Check for expected output files to diagnose silent failures
            _expected = {
                "research": ctx.paths.get("research"),
                "content": ctx.paths.get("md"),
                "activities": ctx.paths.get("activities"),
            }
            _exp_path = _expected.get(phase_id)
            if _exp_path and not _exp_path.exists():
                log(f"  {phase_id}: WARNING — no output produced ({_exp_path.name} missing), pipeline may halt")
            if phase_id in NON_BLOCKING:
                log(f"  {phase_id}: FAIL — continuing")
                continue
            log(f"\n  PIPELINE STOPPED at {phase_id}")
            return False

        if research_only and phase_id == "research":
            log("\n  --research-only: research complete, stopping")
            return True

    return True
