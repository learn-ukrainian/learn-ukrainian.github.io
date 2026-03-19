#!/usr/bin/env python3
"""Pipeline v5 — Clean pipeline implementation (no v2/v3 legacy code).

Phase implementations + state management + all phase-specific helpers.
Imported by build_module_v5.py.

Pipeline: research (+ discover) → content → validate → activities → review → mdx
(Sandbox phase removed in #820 — VESUM post-validation replaces it.)
(Discover merged into research — phase_discover() is a passthrough.)

State file: state.json (plain phase keys, mode: "v5").
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Imports from pipeline_lib (shared utilities — never duplicated)
# ---------------------------------------------------------------------------

import pipeline_lib
from batch_gemini_config import (
    CLAUDE_MODEL_CORE_ACTIVITIES,
    CLAUDE_MODEL_CORE_CONTENT,
    CLAUDE_MODEL_CORE_RESEARCH,
    CLAUDE_MODEL_FINAL_REVIEW,
    PHASES_DIR,
    PRO_MODEL,
    PRO_TRACKS,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
)
from pipeline_lib import (
    ModuleContext,
    _dispatch_prompt,
    _gemini_output_path,
    _get_activities_template,
    _get_content_template,
    # Tier-based prompt dispatch
    _get_prompt_tier,
    _get_scoring_output_table,
    # Scoring helpers (for Gemini review)
    _get_scoring_section,
    _now_iso,
    _validate_activities_yaml,
    # Bilingual section titles
    bilingualify_section_titles,
    # Dispatch + logging
    dispatch_gemini,
    # Fix-prompt helpers moved to pipeline_v5.py (section 2b)
    fill_template,
    log,
    # Phase helpers
    run_verify,
    run_verify_prose_only,
    save_gemini_session,
    # Preflight + completion
    write_review_with_hash,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_AUDIT_FIX_ITERS_CORE = 3    # Mar 2026: raised from 2 — modules often need 3 passes
MAX_AUDIT_FIX_ITERS_SEMINAR = 4  # Mar 2026: raised from 3
MAX_REVIEW_FIX_ITERS = 3        # Mar 2026: raised from 2 — M05 needed 14+2 fixes in 2 iters, still had unresolved

# Dispatch timeouts (seconds)
TIMEOUT_CONTENT = 600
TIMEOUT_CONTENT_SELFAUDIT = 1200  # 20 min: generate + audit + fix in one session
TIMEOUT_RESEARCH = 900  # 15 min: research involves many RAG tool calls
TIMEOUT_ACTIVITIES = 600
TIMEOUT_FIX = 600
TIMEOUT_REVIEW = 900

# Claude model defaults — sourced from batch_gemini_config (single source of truth)
CLAUDE_MODEL_ACTIVITIES = CLAUDE_MODEL_CORE_ACTIVITIES
CLAUDE_MODEL_CONTENT = CLAUDE_MODEL_CORE_CONTENT
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

# RAG tools available during review phases (VESUM verification + textbook search)
_RAG_REVIEW_TOOLS = [
    "mcp__rag__verify_word",
    "mcp__rag__verify_lemma",
    "mcp__rag__search_text",
    "mcp__rag__search_images",
    "mcp__rag__search_literary",
]

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
    "INFO",              # Non-blocking informational (#980)
    "HEADING_LEVEL",     # Non-blocking structural preference (#980)
    "COMPLEXITY_WORD_COUNT",  # Quiz question length — not a content issue
    "LLM_PERSONA_LEAK",  # Minor style issue
    "INLINE_ENGLISH_IN_PROSE",  # Immersion style, not error
}

# Phase sequence — activities run AFTER review so prose is human-approved first
PHASES = ["research", "discover", "content", "validate", "activities", "review", "mdx"]

PHASE_LABELS: dict[str, str] = {
    "research":   "Research + Discover",
    "discover":   "Discover (merged into research)",
    "content":    "Content (prose + activity plans)",
    "validate":   "Validate (prose-only audit + screen + Gemini fix)",
    "review":     "Review (Gemini/Claude, optional)",
    "activities": "Activities + Vocab (from plans + RAG)",
    "mdx":        "MDX Generation",
}

# Non-blocking phases (failures don't stop the pipeline)
NON_BLOCKING = {"validate", "review", "discover"}

# Research constants
_RESEARCH_EXISTS_MIN_WORDS = 500
_META_SECTION_MAX_PCT = 0.25

# ============================================================================
# 1. State Management — delegated to pipeline.state
# ============================================================================

# ============================================================================
# 2. Shared helpers — parsing, extraction, formatting delegated to pipeline.parsing
# ============================================================================
from pipeline.parsing import (
    D1Result,
    DScreenResult,
    _extract_audit_failures,
    _extract_delimiter,
    _extract_delimiter_tolerant,
    _extract_fix_plan,
    _extract_gate_blockers,
    _extract_vesum_failures,
    _format_deterministic_issues,
    _format_filler_phrases,
    _format_vesum_verification,
    _get_russicism_table,
    _get_track_calibration,
    _inject_file_contents,
    _inject_metrics_into_prompt,
    _parse_d1_review,
    _parse_factual_review,
    _quick_review_quality_gate,
)

# ---------------------------------------------------------------------------
# Deterministic screen + fixes — delegated to pipeline.screen
# ---------------------------------------------------------------------------
from pipeline.screen import (
    _deterministic_screen,
    _run_deterministic_fixes,
)
from pipeline.state import (
    executor_deterministic,
    executor_llm,
    executor_script,
    is_complete,
    load_state,  # noqa: F401 — re-exported for build_module_v5
    mark_complete,
    mark_failed,
    save_state,
)

# ---------------------------------------------------------------------------
# Executor helper — avoids repeating use_claude + model resolution everywhere
# ---------------------------------------------------------------------------

_PHASE_CLAUDE_LETTER = {"research": "A", "content": "B", "activities": "C", "review": "D"}
_PHASE_CLAUDE_MODEL_ATTR = {
    "A": ("claude_model_A", CLAUDE_MODEL_RESEARCH),
    "B": ("claude_model_B", CLAUDE_MODEL_CONTENT),
    "C": ("claude_model_C", CLAUDE_MODEL_ACTIVITIES),
    "D": ("claude_model_D", CLAUDE_MODEL_REVIEW),
}


def _phase_executor(ctx: ModuleContext, phase_name: str) -> dict:
    """Build executor dict for an LLM phase, respecting --use-claude flags."""
    letter = _PHASE_CLAUDE_LETTER.get(phase_name, "")
    use_claude = letter and letter in getattr(ctx, "use_claude", set())
    if use_claude:
        attr, default = _PHASE_CLAUDE_MODEL_ATTR[letter]
        return executor_llm("claude", getattr(ctx, attr, default))
    return executor_llm("gemini", ctx.model)


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
# Module file helpers — delegated to pipeline.fixes
# ---------------------------------------------------------------------------

from pipeline.fixes import (
    _apply_fixes_with_rollback,
    _apply_module_fixes,
    _count_diff_lines,
    _log_d1_edits,
    _module_file_paths,
    _snapshot_module_files,
)

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
    """Call Claude CLI headlessly for a phase prompt file.

    Delegates to pipeline.dispatch.dispatch_claude_phase.
    """
    from pipeline.dispatch import dispatch_claude_phase
    return dispatch_claude_phase(
        prompt_file, phase_label,
        model=model, timeout=timeout, allow_tools=allow_tools,
    )




# ---------------------------------------------------------------------------
# Agent escalation
# ---------------------------------------------------------------------------

def _escalate_fix(ctx: ModuleContext, audit_output: str, phase_label: str,
                  content_only: bool = True, primary_agent: str = "gemini",
                  skip_review: bool = False) -> bool:
    """Escalate a failed fix to the opposite agent."""
    passed_retry, _ = run_verify(ctx.paths["md"], skip_review=skip_review)
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

    if content_only:
        passed, _ = run_verify_prose_only(ctx.paths["md"])
    else:
        passed, _ = run_verify(ctx.paths["md"], skip_review=skip_review)
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


def _has_oversized_sections(ctx: ModuleContext) -> bool:
    """Return True if any plan section consumes >25% of word_target."""
    wt = ctx.word_target
    if not wt:
        return False
    threshold = wt * _META_SECTION_MAX_PCT
    outline = ctx.content_outline
    return any(
        isinstance(s, dict) and s.get("words", 0) > threshold
        for s in outline
    )


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

    if not content_path or not content_path.exists():
        return None

    plan_ref = f"\n\n**Plan file** (vocabulary_hints — follow this list):\n```\n{plan_path}\n```" if plan_path and plan_path.exists() else ""

    return f"""You are a TEXT GENERATOR. Generate ONLY vocabulary YAML for a Ukrainian language module.

Read the lesson content:
```
{content_path}
```
{plan_ref}

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

    # Inject friction constraints (#970)
    from pipeline.core import _load_friction_constraints
    prompt_text = prompt_text.replace("{FRICTION_CONSTRAINTS}",
                                      _load_friction_constraints(ctx))

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

    # Inject friction constraints (#970)
    from pipeline.core import _load_friction_constraints
    prompt_text = prompt_text.replace("{FRICTION_CONSTRAINTS}",
                                      _load_friction_constraints(ctx))

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
    # Re-score the fixed content with a lightweight LLM call (#975)
    pass  # _rescore_post_fix disabled #980
    mark_complete(state, phase, ctx, attempts=attempts,
                  note=note, review_grounding=grounding,
                  executor=executor_llm("gemini", ctx.model))
    _update_pipeline_status(ctx, "reviewed")
    return True


def _rescore_post_fix(ctx: ModuleContext) -> None:
    """Re-score the module after fixes using a lightweight LLM call.

    Reads the fixed content + activities, asks for a quick 7-dimension
    score, and appends it to the review file. Uses Claude Sonnet for
    speed (not a full review — just scoring).
    """
    review_path = ctx.paths.get("review")
    content_path = ctx.paths.get("md")
    if not review_path or not review_path.exists():
        return
    if not content_path or not content_path.exists():
        return

    try:
        content = content_path.read_text("utf-8")
        act_path = ctx.paths.get("activities")
        act_text = act_path.read_text("utf-8") if act_path and act_path.exists() else ""

        prompt = (
            "You are scoring a Ukrainian language module (A1 beginner). "
            "Score these 7 dimensions from 1-10 based on the content below. "
            "Be honest — no inflation. Output ONLY a JSON object:\n"
            '{"experience": N, "language": N, "pedagogy": N, "activities": N, '
            '"beginner_safety": N, "llm_fingerprint": N, "linguistic_accuracy": N, '
            '"overall": N.N, "verdict": "PASS or FAIL"}\n\n'
            f"Content ({len(content.split())} words):\n{content[:8000]}\n\n"
            f"Activities:\n{act_text[:3000]}\n"
        )

        import tempfile

        from pipeline.dispatch import dispatch_claude_phase
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(prompt)
            prompt_path = Path(f.name)

        ok, raw = dispatch_claude_phase(
            prompt_path, "Post-fix scoring",
            model="claude-opus-4-6", timeout=300,
        )
        prompt_path.unlink(missing_ok=True)

        if not ok or not raw:
            log("  review: Post-fix re-scoring failed (no response)")
            return

        # Parse JSON from response
        import json as _json

        # Find JSON in response
        import re as _re
        json_match = _re.search(r'\{[^}]+\}', raw)
        if not json_match:
            log("  review: Post-fix re-scoring — no JSON in response")
            return

        scores = _json.loads(json_match.group())
        overall = scores.get("overall", 0)
        verdict = scores.get("verdict", "?")

        # Append to review file
        review_text = review_path.read_text("utf-8")
        post_fix_section = (
            f"\n\n---\n\n## Post-Fix Re-Score (automated)\n\n"
            f"**Scored by:** claude-opus-4-6 (on fixed content)\n"
            f"**Overall Score:** {overall}/10\n"
            f"**Verdict:** {verdict}\n\n"
            f"| Dimension | Score |\n|-----------|-------|\n"
        )
        for dim in ("experience", "language", "pedagogy", "activities",
                     "beginner_safety", "llm_fingerprint", "linguistic_accuracy"):
            post_fix_section += f"| {dim} | {scores.get(dim, '?')}/10 |\n"

        review_path.write_text(review_text + post_fix_section, "utf-8")
        log(f"  review: Post-fix re-score: {overall}/10 ({verdict})")

    except Exception as e:
        log(f"  review: Post-fix re-scoring failed: {e}")






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
    # Replace existing Resource Discovery section if present
    existing = research_path.read_text(encoding="utf-8")
    if "## Resource Discovery" in existing:
        # Strip old section (everything from ## Resource Discovery to EOF or next ## heading)
        import re
        existing = re.sub(
            r"\n*## Resource Discovery\n.*",
            "", existing, flags=re.DOTALL,
        ).rstrip()
        research_path.write_text(existing + "\n", encoding="utf-8")
        log("  discover: Replaced old Resource Discovery section")
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


def _run_discovery_within_research(ctx: ModuleContext, state: dict) -> None:
    """Run discovery search within the research phase (non-blocking).

    Extracts the core logic from phase_discover() so that discovery runs
    as part of research instead of a separate phase.
    """
    if getattr(ctx, "skip_discover", False):
        log("  research/discover: SKIP (--skip-discover)")
        mark_complete(state, "discover", ctx, skipped=True,
                      note="merged-into-research",
                      executor=executor_script("discover_passthrough"))
        return
    if ctx.dry_run:
        log("  research/discover: SKIP (dry-run)")
        return

    try:
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

        log(f"  research/discover: searching (keywords: {keywords[:4]}...)")

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

        _update_external_resources(ctx, result)

        relevant = [v for v in result.videos if v.relevance_score >= 0.5]
        n_rag = len(result.rag_chunks) + len(result.rag_images) + len(result.rag_literary)
        log(f"  research/discover: {len(result.videos)} videos ({len(relevant)} relevant), "
            f"{len(result.blogs)} blogs, {n_rag} RAG items")
        if result.error:
            log(f"  research/discover: WARNING: {result.error}")
        elif result.warning:
            log(f"  research/discover: WARNING: {result.warning}")

        _append_discovery_to_research(ctx, result)

        mark_complete(state, "discover", ctx, note="merged-into-research",
                      executor=executor_script("discovery_search"))

    except Exception as e:
        log(f"  research/discover: WARNING — discovery failed (non-blocking): {e}")
        mark_complete(state, "discover", ctx, note="merged-into-research-failed",
                      error=str(e),
                      executor=executor_script("discovery_search"))


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
    schemas_dir = Path(__file__).parent.parent.parent / "schemas"
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


def _format_deterministic_issue(index: int, iss: dict,
                                content_lines: list[str]) -> str:
    """Format a single deterministic issue into fix instructions."""
    issue_type = iss.get("type", "UNKNOWN")
    lines_block: list[str] = [f"### Fix {index}: {issue_type}"]

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

    return "\n".join(lines_block)


def _format_gate_failure(gf: dict) -> str:
    """Format a single gate failure into fix instructions."""
    gate = gf["gate"]
    detail = gf["detail"]
    lines_block = [f"### Fix: Gate `{gate}` FAIL — {detail}"]

    if gate.lower() in ("words", "word_count"):
        lines_block.append("**Action:** Expand content in the shortest sections. "
                         "Add examples, explanations, or practice scenarios.")
    elif gate.lower() == "immersion":
        lines_block.append(_format_immersion_gate_action(detail))
    elif gate.lower() in ("activities", "unique_types"):
        lines_block.append("**Action:** Add more activities or diversify activity types "
                         "in the activities YAML file.")
    elif gate.lower() == "engagement":
        lines_block.append("**Action:** Add engagement boxes: `[!tip]`, `[!note]`, "
                         "`[!cultural]`, `[!myth-buster]`.")
    elif gate == "YAML_SCHEMA":
        lines_block.append(f"**Action:** Fix the YAML schema violation: {detail}")

    return "\n".join(lines_block)


def _format_immersion_gate_action(detail: str) -> str:
    """Build action text for an immersion gate failure."""
    imm_match = re.search(r"([\d.]+)%\s+LOW\s+\(target\s+(\d+)-(\d+)%", detail)
    if imm_match:
        current_imm = float(imm_match.group(1))
        target_min = int(imm_match.group(2))
        gap = target_min - current_imm
        if gap > 15:
            return (
                f"**\u26a0 SCOPE WARNING:** Immersion gap is {gap:.0f}% ({current_imm:.1f}% \u2192 {target_min}% min). "
                "This is too large for a fix pass. Focus on the EASIEST wins:\n"
                "1. Add Ukrainian section headers with English in parentheses\n"
                "2. Add '\u041d\u0430\u043f\u0440\u0438\u043a\u043b\u0430\u0434:' / '\u041f\u043e\u0440\u0456\u0432\u043d\u044f\u0439\u0442\u0435:' before example blocks\n"
                "3. Add short Ukrainian phrases with (translations) in existing paragraphs\n"
                "Do NOT rewrite entire sections. Target +5-8% improvement max.")
    return ("**Action:** Add more Ukrainian-language content blocks. "
            "Convert some English explanations to Ukrainian with English glosses.")


def _collect_unparsed_failures(audit_output: str, parsed_gates: set[str]) -> list[str]:
    """Collect audit failures not already covered by parsed gate_failures."""
    audit_lines = audit_output.strip().split("\n")
    return [
        ln.strip() for ln in audit_lines
        if ("\u274c" in ln or "VIOLATION" in ln) and not any(g in ln for g in parsed_gates)
    ]


def _build_fallback_instructions(audit_output: str) -> str:
    """Build fallback fix instructions when no specific issues were extracted."""
    audit_lines = audit_output.strip().split("\n")
    fail_lines = [ln for ln in audit_lines if "\u274c" in ln or "FAIL" in ln or "VIOLATION" in ln]
    if fail_lines:
        return "### Audit Failures\n\n```\n" + "\n".join(fail_lines[-20:]) + "\n```"
    # Ultra-fallback: include the full audit tail so the fix prompt is never empty
    tail = "\n".join(audit_lines[-30:])
    return (
        "### Audit Output (no specific failures extracted \u2014 review raw output)\n\n"
        f"```\n{tail}\n```"
    )


def _build_section_fix_format(audit_output: str, ctx: ModuleContext,
                               content_text: str, word_count: int) -> str:
    """Build section-level fix output format instructions."""
    if not content_text:
        return ""
    affected_sections = _identify_affected_sections(audit_output, ctx.paths["md"], content=content_text)
    if not affected_sections:
        return ""
    section_list = ", ".join(f'"{s}"' for s in affected_sections)
    if word_count >= 3000:
        scope_note = f"This module is {word_count} words. Fix ONLY sections: {section_list}"
    else:
        scope_note = f"Fix the affected sections: {section_list}"
    return textwrap.dedent(f"""\

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


def _build_file_list(ctx: ModuleContext, content_only: bool) -> str:
    """Build the file list section for the fix prompt."""
    file_list = f"- Content: `{ctx.paths['md']}`"
    if not content_only:
        if ctx.paths.get("activities"):
            file_list += f"\n- Activities: `{ctx.paths['activities']}`"
        if ctx.paths.get("vocabulary"):
            file_list += f"\n- Vocabulary: `{ctx.paths['vocabulary']}`"
    return file_list


def _build_fix_prompt(ctx: ModuleContext, audit_output: str, content_only: bool,
                      deterministic_issues: list[dict] | None = None) -> str:
    """Build a surgical fix prompt with per-issue instructions.

    Instead of dumping 60 lines of audit output, this extracts specific
    failures and produces exact instructions Gemini can act on.
    """
    from pipeline_lib import get_pedagogical_constraints

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

    # 1. Deterministic issues
    for i, iss in enumerate(det_issues, 1):
        fix_instructions.append(_format_deterministic_issue(i, iss, content_lines))

    # 2. Gate failures
    for gf in gate_failures:
        fix_instructions.append(_format_gate_failure(gf))

    # 3. Pedagogical violations
    for i, pv in enumerate(ped_violations, len(det_issues) + len(gate_failures) + 1):
        lines_block = [f"### Fix {i}: PEDAGOGICAL_VIOLATION"]
        lines_block.append(f"**What:** [{pv['type']}] {pv['issue']}")
        if pv.get("fix"):
            lines_block.append(f"**How to fix:** {pv['fix']}")
        fix_instructions.append("\n".join(lines_block))

    # 4. Unparsed failures
    parsed_gates = {gf["gate"] for gf in gate_failures}
    unparsed_fails = _collect_unparsed_failures(audit_output, parsed_gates)
    if unparsed_fails:
        fix_instructions.append("### Other Audit Failures\n\n```\n" + "\n".join(unparsed_fails[-20:]) + "\n```")

    # 5. Fallback if nothing extracted
    if not fix_instructions:
        fix_instructions.append(_build_fallback_instructions(audit_output))

    # Pedagogical constraints (compact)
    ped_constraints = get_pedagogical_constraints(ctx.track, ctx.module_num, ctx.plan)
    ped_section = ""
    if ped_constraints:
        ped_section = f"\n## Constraints (do NOT violate while fixing)\n\n{ped_constraints}\n"

    # Decodable vocabulary removed (#841) — plan vocabulary_hints is source of truth
    decodable_section = ""

    # Lexical sandbox — compact lemma list so fix agent stays on-vocabulary
    sandbox_section = ""
    sandbox_text = getattr(ctx, "_lexical_sandbox", "")
    if sandbox_text and len(sandbox_text.strip()) > 50:
        # Extract just the lemma list from the full sandbox markdown
        lemmas: list[str] = []
        for line in sandbox_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("| ") and not stripped.startswith("|---") and not stripped.startswith("| Lemma"):
                parts = stripped.split("|")
                if len(parts) >= 2:
                    lemma = parts[1].strip()
                    if lemma:
                        lemmas.append(lemma)
            elif stripped.startswith("- **"):
                word = stripped.split("**")[1] if "**" in stripped else ""
                if word:
                    lemmas.append(word)
        if lemmas:
            sandbox_section = (
                "\n## Lexical Sandbox (allowed Ukrainian vocabulary)\n\n"
                f"This module's verified vocabulary: **{', '.join(lemmas)}**\n\n"
                "**CRITICAL**: When adding or modifying Ukrainian text, use ONLY words from this list "
                "plus basic function words (pronouns, prepositions, conjunctions, numbers). "
                "Do NOT introduce new content words not in this sandbox.\n"
            )

    # Immersion rule — structural containment guidance for fix agent
    immersion_section = ""
    imm_rule = getattr(ctx, "immersion_rule", "")
    if imm_rule and len(imm_rule.strip()) > 20:
        # Extract just the target line and key structural rules
        target_line = imm_rule.split("\n")[0] if "\n" in imm_rule else imm_rule
        immersion_section = (
            f"\n## Immersion Rules\n\n{target_line}\n\n"
            "**Structural containment**: English prose in paragraphs. "
            "Ukrainian in CONTAINERS ONLY (tables, blockquotes, numbered lists, dialogues). "
            "Do NOT mix Ukrainian words into English sentences.\n"
        )

    # Level constraints (grammar restrictions)
    level_constraints = getattr(ctx, "level_constraints", "")
    level_section = ""
    if level_constraints and len(level_constraints.strip()) > 10:
        level_section = f"\n## Level Constraints\n\n{level_constraints}\n"

    section_fix = _build_section_fix_format(audit_output, ctx, content_text, word_count)
    file_list = _build_file_list(ctx, content_only)

    fixes_text = "\n\n".join(fix_instructions)
    total_fixes = len(det_issues) + len(gate_failures) + len(ped_violations)
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

    # Friction constraints (#970)
    from pipeline.core import _load_friction_constraints
    friction_text = _load_friction_constraints(ctx)
    friction_section = f"\n## Friction Constraints (DO NOT reintroduce)\n\n{friction_text}\n" if friction_text else ""

    return textwrap.dedent(f"""\
        # Fix ALL {total_fixes} issue(s) in `{ctx.slug}`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are {total_fixes} issues. You must produce fixes for all {total_fixes}.**
        **After you finish, count your fixes. If the count is less than {total_fixes}, go back and fix the ones you missed.**

        {fixes_text}
        {schema_hint}
        {ped_section}
        {decodable_section}
        {sandbox_section}
        {immersion_section}
        {level_section}
        {friction_section}
        {vesum_section}

        ## Files

        {file_list}

        ## Rules

        1. Fix ALL {total_fixes} issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.
        {section_fix}
    """)


# ============================================================================
# 3. Phase implementations
# ============================================================================

# ---------------------------------------------------------------------------
# Phase: research
# ---------------------------------------------------------------------------

def _check_research_skip(ctx: ModuleContext, state: dict) -> bool | None:
    """Check whether research phase should be skipped.

    Returns True if skip, False if state was cleared for re-run, None to continue.
    """
    force_research = getattr(ctx, "force_research", False)
    if force_research:
        state.get("phases", {}).pop("research", None)
        save_state(ctx, state)
        return None  # re-run

    content_path = ctx.paths.get("md")
    content_exists = content_path and content_path.exists()
    content_sufficient = False
    if content_exists:
        try:
            wc = len(content_path.read_text("utf-8").split())
            content_sufficient = wc >= ctx.word_target * 0.8
        except Exception:
            pass

    # Even if content is sufficient, if research file was deleted, re-run
    research_path = ctx.paths.get("research")
    research_file_exists = research_path and research_path.exists()

    if content_sufficient and research_file_exists:
        log(f"  research: SKIP (meta locked — content exists at {wc}w, target {ctx.word_target}w)")
        return True
    elif content_sufficient and not research_file_exists:
        log("  research: Research file deleted — re-running despite existing content")
        state.get("phases", {}).pop("research", None)
        save_state(ctx, state)
        return None  # re-run

    if _has_oversized_sections(ctx) and not _research_file_is_usable(ctx):
        log("  research: Oversized section detected + no usable research, re-running")
        state.get("phases", {}).pop("research", None)
        save_state(ctx, state)
        return None  # re-run

    log("  research: SKIP (already complete)")
    return True


def _prefetch_textbook_for_research(ctx: ModuleContext) -> str:
    """Pre-fetch textbook excerpts for research phase (beginner modules).

    Searches RAG for textbook content related to the module topic so the
    research prompt has real pedagogical material to reference.

    Search strategy:
    - Ukrainian-only search terms (English topic titles kill semantic matching)
    - Higher grades first for grammar modules (M15+: imperatives = Grade 7, not 3)
    - Plan section titles are the best source of Ukrainian search terms
    - Vocabulary hints provide additional coverage
    """
    try:
        from rag.query import search_text
    except ImportError:
        return ""

    def has_cyrillic(s: str) -> bool:
        return any("\u0400" <= c <= "\u04ff" for c in s)

    # Build search terms — Ukrainian only, section titles first (most specific)
    search_terms: list[str] = []

    # 1. Section titles from content outline (guaranteed bilingual for beginner)
    for section in (ctx.content_outline or [])[:4]:
        title = section.get("section") or section.get("title", "")
        if title:
            uk_part = title.split("(")[0].strip()
            if uk_part and has_cyrillic(uk_part):
                search_terms.append(uk_part)

    # 2. Plan keywords (if present)
    plan_keywords = ctx.plan.get("keywords", [])
    for kw in plan_keywords[:3]:
        if has_cyrillic(str(kw)):
            search_terms.append(str(kw))

    # 3. Topic title — only if it has Cyrillic (skip English-only titles)
    topic = ctx.topic_title or ctx.slug.replace("-", " ")
    if topic and has_cyrillic(topic):
        uk_topic = topic.split("(")[0].strip()
        if uk_topic:
            search_terms.append(uk_topic)

    # 4. Ukrainian words from plan vocabulary_hints
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    hint_items: list = []
    if isinstance(vocab_hints, dict):
        for v in vocab_hints.values():
            if isinstance(v, list):
                hint_items.extend(v[:3])
    elif isinstance(vocab_hints, list):
        hint_items = vocab_hints[:5]
    for vh in hint_items[:5]:
        word = vh.get("word", "") if isinstance(vh, dict) else str(vh)
        first_word = word.split("/")[0].split("(")[0].split(" ")[0].strip()
        if first_word and has_cyrillic(first_word):
            search_terms.append(first_word)

    search_terms = list(dict.fromkeys(t.strip() for t in search_terms if t.strip()))[:6]
    if not search_terms:
        return ""

    base = ctx.track.split("-")[0]
    # No subject filter — some Grade 4 books lack subject metadata
    subject = None

    # Grade priority: grammar modules (M15+) search higher grades first
    # because grammar topics like imperative mood are taught in Grade 7,
    # while Grade 3 only has generic verb introduction (noise).
    if base in ("a1", "a2") and ctx.module_num >= 15:
        grade_list = [7, 6, 5, 4, 3]  # Higher grades first for grammar
    elif base in ("a1", "a2"):
        grade_list = [3, 4, 5, 6, 7]  # Lower grades for early modules
    else:
        grade_list = [None]  # B1+: search all grades

    results = []
    seen_chunks: set[str] = set()
    for term in search_terms:
        for g in grade_list:
            try:
                hits = search_text(term, grade=g, subject=subject, limit=2)
            except Exception:
                continue
            for hit in hits:
                cid = hit.get("chunk_id", "")
                if cid in seen_chunks:
                    continue
                seen_chunks.add(cid)
                # Build source label from available metadata
                author = hit.get("author", "")
                hit_grade = hit.get("grade", "")
                section = hit.get("section_title", hit.get("section", ""))
                label_parts = []
                if hit_grade:
                    label_parts.append(f"Grade {hit_grade}")
                if author:
                    label_parts.append(author)
                source_label = ", ".join(label_parts) if label_parts else hit.get("source", "Unknown")
                if section:
                    source_label += f" — {section}"
                text = hit.get("text", "")[:500]
                results.append(f"**{source_label}**:\n```\n{text}\n```")
        if len(results) >= 6:
            break

    if not results:
        return ""

    header = (
        "## Textbook Excerpts (from real Ukrainian school textbooks)\n\n"
        "Use these as authoritative reference for your research. Note how textbooks "
        "teach this topic: what exercises they use, what cultural examples they include, "
        "what common errors they address.\n\n"
    )
    return header + "\n\n".join(results[:6])


def _select_research_template(ctx: ModuleContext, is_seminar: bool, is_pro: bool,
                               research_exists: bool) -> str:
    """Select the appropriate research prompt template name."""
    if is_seminar or is_pro:
        if research_exists:
            research_path = ctx.paths.get("research")
            word_count = len(research_path.read_text("utf-8").split()) if research_path else 0
            log(f"  research: Research file found ({word_count:,}w) — skipping research, meta-only")
            return "research-meta-only.md"
        elif is_pro:
            return "research-pro.md"
        else:
            return "research-seminar.md"

    tier = _get_prompt_tier(ctx.track, ctx.module_num)
    if tier == "beginner":
        template_name = "beginner-research.md"
        if not (PHASES_DIR / template_name).exists():
            log("  research: beginner-research.md not found, falling back to research-core.md")
            return "research-core.md"
        log("  research: Using beginner tier research prompt")
        return template_name

    return "research-core.md"


def _dispatch_research(ctx: ModuleContext, prompt_file: Path,
                        template_name: str) -> tuple[bool, str]:
    """Dispatch research to Claude or Gemini. Returns (ok, raw_output)."""
    use_claude = "A" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_A", CLAUDE_MODEL_RESEARCH)
        log(f"  research: Dispatching {template_name} via Claude ({claude_model})...")
        return _dispatch_claude_phase(
            prompt_file, "Phase A", model=claude_model,
            timeout=600,
            allow_tools=[
                "WebSearch", "WebFetch", "Read",
                "mcp__rag__search_text", "mcp__rag__verify_word",
                "mcp__rag__verify_lemma", "mcp__rag__search_images",
                "mcp__rag__search_literary", "mcp__rag__query_wikipedia",
            ],
        )

    log(f"  research: Dispatching {template_name}...")
    output_file = _gemini_output_path(ctx.slug, "pA")
    ok, raw_output = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"v5-{ctx.slug}-pA",
        model=ctx.model, stdout_only=True, output_file=output_file,
        timeout=TIMEOUT_RESEARCH,
    )
    if raw_output:
        (ctx.orch_dir / "research-output.md").write_text(raw_output, "utf-8")
    save_gemini_session(ctx.orch_dir, label="research")
    return ok, raw_output


def _save_research_output(ctx: ModuleContext, raw_output: str,
                           research_exists: bool, is_seminar: bool,
                           is_pro: bool) -> None:
    """Extract and save research text from LLM output."""
    if research_exists:
        return
    research_text = _extract_delimiter(raw_output, "===RESEARCH_START===", "===RESEARCH_END===")
    if research_text:
        research_path = ctx.paths.get("research")
        if research_path:
            research_path.parent.mkdir(parents=True, exist_ok=True)
            research_path.write_text(research_text, "utf-8")
            log(f"  research: Research saved \u2192 {research_path.name}")
        else:
            (ctx.orch_dir / "research-fallback.md").write_text(research_text, "utf-8")
            log("  research: Research saved \u2192 research-fallback.md (no research path in ctx)")
    else:
        if is_seminar or is_pro:
            log("  research: WARNING \u2014 no RESEARCH delimiters in output (seminar/pro track)")
        else:
            log("  research: NOTE \u2014 no research delimiters (expected for some core tracks)")


def _apply_meta_outline(ctx: ModuleContext, raw_output: str,
                         research_exists: bool) -> bool:
    """Extract and apply meta outline from LLM output. Returns True on success."""
    import yaml

    meta_text = _extract_delimiter(raw_output, "===META_OUTLINE_START===", "===META_OUTLINE_END===")
    if not meta_text:
        log("  research: No META_OUTLINE \u2014 plan content_outline is source of truth")
        return True

    meta_text_clean = re.sub(r'^```(?:ya?ml)?\s*\n', '', meta_text.strip())
    meta_text_clean = re.sub(r'\n```\s*$', '', meta_text_clean)
    try:
        outline_data = yaml.safe_load(meta_text_clean)
    except yaml.YAMLError as e:
        log(f"  research: WARNING \u2014 meta outline YAML parse error: {e}")
        outline_data = None

    if not (outline_data and isinstance(outline_data, dict) and "content_outline" in outline_data):
        log("  research: WARNING \u2014 no content_outline in META_OUTLINE block")
        return True  # non-fatal

    outline_data["content_outline"] = bilingualify_section_titles(
        outline_data["content_outline"], ctx.track, ctx.module_num,
    )
    ctx.content_outline = outline_data["content_outline"]  # type: ignore[attr-defined]
    log(f"  research: Outline from LLM applied ({len(outline_data['content_outline'])} sections)")
    return True


def phase_research(ctx: ModuleContext, state: dict) -> bool:
    """Research + Meta outline generation."""
    if is_complete(state, "research"):
        skip = _check_research_skip(ctx, state)
        if skip is True:
            return True
        # skip is None means state was cleared, fall through to re-run
    else:
        # Research not marked complete in state, but file may already exist
        # (e.g. batch ran research+discover with --stop-before content).
        # Don't redo expensive research if the file is usable.
        force_research = getattr(ctx, "force_research", False)
        if not force_research and _research_file_is_usable(ctx):
            log("  research: SKIP (research file exists and is usable)")
            mark_complete(state, "research", ctx, note="file-exists",
                          executor=executor_script("file_exists_skip"))
            return True

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    is_pro = ctx.track in PRO_TRACKS

    # --rebuild: normally delete old research file so it gets regenerated fresh
    # (research files live outside orch dir and survive orch cleanup)
    # BUT: if the research file is already usable, keep it — research is the
    # most expensive phase and batch runs should not redo completed work.
    force_research = getattr(ctx, "force_research", False)
    if ctx.rebuild and not force_research:
        research_path = ctx.paths.get("research")
        if research_path and research_path.exists():
            if _research_file_is_usable(ctx):
                log("  research: --rebuild — keeping existing research (usable)")
                mark_complete(state, "research", ctx, note="rebuild-kept",
                              executor=executor_script("rebuild_kept_skip"))
                # Still run discovery merge if needed
                _run_discovery_within_research(ctx, state)
                return True
            else:
                research_path.unlink()
                log("  research: --rebuild — deleted old research file (unusable)")
    elif ctx.rebuild and force_research:
        research_path = ctx.paths.get("research")
        if research_path and research_path.exists():
            research_path.unlink()
            log("  research: --rebuild + --force-phase — deleted research file")
    research_exists = (is_seminar or is_pro) and _research_file_is_usable(ctx)

    template_name = _select_research_template(ctx, is_seminar, is_pro, research_exists)
    template = PHASES_DIR / template_name

    if not template.exists():
        log(f"  research: ERROR \u2014 template not found: {template}")
        return False

    prompt_file = ctx.orch_dir / "research-prompt.md"
    overrides = {}
    if template_name == "beginner-research.md":
        textbook_ctx = _prefetch_textbook_for_research(ctx)
        if textbook_ctx:
            overrides["TEXTBOOK_CONTEXT"] = textbook_ctx
            log(f"  research: Injected {len(textbook_ctx):,} chars of textbook context")
        else:
            overrides["TEXTBOOK_CONTEXT"] = "(No textbook excerpts found for this topic)"
    if not fill_template(template, ctx.placeholders, prompt_file,
                         overrides=overrides):
        return False

    if ctx.dry_run:
        log(f"  research: DRY-RUN \u2014 would dispatch {template_name}")
        return True

    _res_exec = _phase_executor(ctx, "research")

    ok, raw_output = _dispatch_research(ctx, prompt_file, template_name)
    if not ok:
        use_claude = "A" in getattr(ctx, "use_claude", set())
        log(f"  research: FAILED \u2014 {'Claude' if use_claude else 'Gemini'} dispatch error")
        mark_failed(state, "research", ctx, executor=_res_exec)
        return False

    _save_research_output(ctx, raw_output, research_exists, is_seminar, is_pro)

    if not _apply_meta_outline(ctx, raw_output, research_exists):
        mark_failed(state, "research", ctx, executor=_res_exec)
        return False

    # Run discovery within research (merged — non-blocking)
    _run_discovery_within_research(ctx, state)

    mark_complete(state, "research", ctx,
                  task_id=f"v5-{ctx.slug}-pA",
                  mode="meta-only" if research_exists else "full",
                  executor=_res_exec)
    return True


# ---------------------------------------------------------------------------
# Phase: discover (passthrough — merged into research)
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
    """Discover: passthrough (merged into research phase).

    Discovery now runs at the end of phase_research(). This function exists
    only for backwards compatibility with --restart-from discover.
    """
    if is_complete(state, "discover"):
        log("  discover: SKIP (already complete)")
        return True
    log("  discover: SKIP (merged into research phase)")
    mark_complete(state, "discover", ctx, note="merged-into-research",
                  executor=executor_script("discover_passthrough"))
    return True



def _make_content_dispatch_fn(
    ctx: ModuleContext,
) -> Callable[..., tuple[bool, str]]:
    """Create a Claude content dispatch function bound to *ctx*.

    Returns a callable with the same signature as ``dispatch_gemini()``
    so it can be used as a drop-in replacement via ``ctx.content_dispatch_fn``.
    """
    claude_model = getattr(ctx, "claude_model_B", CLAUDE_MODEL_CONTENT)

    def _dispatch(
        prompt: str, task_id: str, model: str = "",
        stdout_only: bool = True, allow_write: bool = False,
        output_file: Path | None = None, timeout: int = 1200,
    ) -> tuple[bool, str]:
        # Ignore Gemini model names passed by phase_2_content (ctx.model is Gemini)
        effective_model = (model if model and "claude" in model else "") or claude_model
        log(f"  content: Dispatching via Claude ({effective_model})...")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8",
        ) as f:
            f.write(prompt)
            prompt_path = Path(f.name)

        try:
            ok, raw_output = _dispatch_claude_phase(
                prompt_path, "Phase B",
                model=effective_model,
                timeout=timeout,
                allow_tools=[
                    "mcp__rag__verify_word", "mcp__rag__verify_words",
                    "mcp__rag__verify_lemma", "mcp__rag__search_text",
                    "mcp__rag__query_pravopys",
                    "WebFetch", "Bash", "Read", "Grep",
                ],
            )
        finally:
            prompt_path.unlink(missing_ok=True)

        if ok and output_file and raw_output:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(raw_output, encoding="utf-8")

        return ok, raw_output

    return _dispatch


def _try_adopt_or_generate_content(ctx: ModuleContext) -> bool:
    """Check for adoptable existing content or archive, else generate fresh.

    Inlined from the old phase_B_content → phase_2_content chain.
    """
    content_path = ctx.paths["md"]

    # Skip adoption when --force-phase content is set — always regenerate
    force_regen = (getattr(ctx, "force_phase", None) or "").lower() == "content"

    # 1. Adopt existing content if it meets word target
    if not force_regen and content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
        if word_count >= ctx.word_target * 0.8:
            refresh_needed = False
            research_path = ctx.paths.get("research")
            if research_path and research_path.exists():
                try:
                    from research_quality import assess_research_compat
                    info = assess_research_compat(research_path, ctx.track, content_path)
                    if info and info.get("content_alignment", {}).get("refresh_recommended"):
                        refresh_needed = True
                        reasons = info["content_alignment"].get("reasons", [])
                        log("  content: Research-content misalignment detected")
                        for r in reasons:
                            log(f"    - {r}")
                except ImportError:
                    pass
            if refresh_needed and getattr(ctx, "refresh", False):
                log("  content: --refresh flag set — regenerating prose from research")
            elif refresh_needed:
                log("  content: ADOPT (use --refresh to regenerate from updated research)")
                return True
            else:
                log(f"  content: ADOPT — existing prose found ({word_count}w, target {ctx.word_target}w)")
                return True

    # 2. Try archive restoration for seminar tracks
    if not force_regen and getattr(ctx, "is_archived", False):
        from pipeline_lib import _check_archive_fits_outline, restore_from_archive
        fits, matched, missing = _check_archive_fits_outline(ctx)
        archive_source = getattr(ctx, "archive_source", "unknown")
        if fits:
            log(f"  content: Archive fits outline — {len(matched)}/{len(matched)+len(missing)} sections match")
            if missing:
                log(f"  content: Missing sections (will be caught in activities): {', '.join(missing)}")
            if ctx.dry_run:
                log(f"  content: DRY-RUN — would restore from archive ({archive_source})")
                return True
            archive_dir = getattr(ctx, "archive_dir", None)
            if restore_from_archive(ctx, archive_dir):
                return True
            else:
                log("  content: Archive restore FAILED — falling back to generation")
        else:
            log(f"  content: Archive does NOT fit outline — only {len(matched)}/{len(matched)+len(missing)} sections match")
            log("  content: Generating fresh prose instead")

    # 3. Generate fresh content
    from pipeline_lib import phase_2_content
    return phase_2_content(ctx)


def phase_content(ctx: ModuleContext, state: dict) -> bool:
    """Content: write prose. Adopt existing, restore archive, or generate fresh."""
    if is_complete(state, "content"):
        log("  content: SKIP (already complete)")
        return True

    _cnt_exec = _phase_executor(ctx, "content")

    if ctx.dry_run:
        log("  content: DRY-RUN — would dispatch content (content.md)")
        return True

    # Wire Claude dispatch if --use-claude B
    if "B" in getattr(ctx, "use_claude", set()):
        model = getattr(ctx, "claude_model_B", CLAUDE_MODEL_CONTENT)
        log(f"  content: Using Claude for content generation (model: {model})")
        ctx.content_dispatch_fn = _make_content_dispatch_fn(ctx)  # type: ignore[attr-defined]

    # --- Adopt existing content if it meets word target ---
    ok = _try_adopt_or_generate_content(ctx)

    if not ok:
        mark_failed(state, "content", ctx, executor=_cnt_exec)
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

        # Deterministic stress mark annotation
        try:
            from pipeline.stress_annotator import annotate_file
            n_stressed = annotate_file(content_path)
            if n_stressed > 0:
                log(f"  content: Added stress marks to {n_stressed} Ukrainian words")
                raw = content_path.read_text("utf-8")  # re-read after annotation
        except ImportError:
            log("  content: WARNING — stress annotator not available (pip install ukrainian-word-stress)")
        except Exception as e:
            log(f"  content: WARNING — stress annotation failed: {e}")

        # Gate 1: Word count
        if ctx.word_target:
            wc = len(clean_for_stats(raw).split())
            threshold = ctx.word_target * 0.8
            if wc < threshold:
                log(f"  content: FAILED — word count {wc} < 80% target ({int(threshold)}w)")
                mark_failed(state, "content", ctx,
                            note=f"word-count-{wc}-below-80pct-{ctx.word_target}",
                            executor=_cnt_exec)
                return False

        # Gate 2: Content purity pre-screen
        from audit.checks.content_purity import check_content_purity
        purity_violations = check_content_purity(raw)
        critical = [v for v in purity_violations if v.get("severity") == "error"]
        if critical:
            log(f"  content: WARNING — {len(critical)} content purity issue(s) detected")
            for v in critical[:3]:
                log(f"    {v['type']}: {v['issue'][:100]}")

        # Info: Textbook citation density (non-blocking)
        citations = re.findall(r'<!--\s*adapted from:', raw)
        originals = re.findall(r'<!--\s*original:', raw)
        citation_count = len(citations)
        if citation_count > 0:
            log(f"  content: INFO — {citation_count} textbook adaptation(s) cited, {len(originals)} original(s)")
        elif ctx.track.split("-")[0] in ("a1", "a2"):
            log("  content: INFO — no textbook citations found (<!-- adapted from: --> comments)")

    # mark_complete replaces the entire phase dict, so self_audited must go in as **extra
    _content_extra: dict = {}
    if self_audited:
        _content_extra["self_audited"] = True
    _content_extra["executor"] = _cnt_exec
    mark_complete(state, "content", ctx, **_content_extra)
    _invalidate_stale_artifacts(ctx)

    # Full-build: if activities+vocab were extracted during content, mark activities done
    if getattr(ctx, "full_build", False):
        act_path = ctx.paths.get("activities")
        voc_path = ctx.paths.get("vocabulary")
        if (act_path and act_path.exists() and act_path.stat().st_size > 10
                and voc_path and voc_path.exists() and voc_path.stat().st_size > 10):
            mark_complete(state, "activities", ctx, note="extracted-from-full-build",
                          executor=_cnt_exec)
            log("  content: Full-build activities+vocab adopted — skipping separate activities phase")

    return True


# ---------------------------------------------------------------------------
# Phase: activities — helpers
# ---------------------------------------------------------------------------


def _check_existing_activities(ctx: ModuleContext, state: dict) -> str | None:
    """Check existing activities/vocab files for staleness or adoption.

    Returns:
        "adopt" — existing files are valid and fresh, caller should return True
        "regenerate" — stale/invalid files deleted, caller should continue
        None — no existing files, caller should continue
    """
    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")
    if not (act_path and act_path.exists() and voc_path and voc_path.exists()):
        return None

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
            return "regenerate"
        else:
            log("  activities: ADOPT — existing activities/vocab found and valid")
            mark_complete(state, "activities", ctx, note="adopted-existing",
                          executor=executor_script("adopted_existing"))
            return "adopt"
    else:
        log("  activities: Existing activities invalid — deleting and regenerating")
        act_path.unlink(missing_ok=True)
        if voc_path and voc_path.exists():
            voc_path.unlink(missing_ok=True)
            log("  activities: Also deleted stale vocabulary (paired with invalid activities)")
        return "regenerate"


def _dispatch_vocab_only(ctx: ModuleContext, prompt_label: str) -> tuple[bool, str]:
    """Dispatch a vocab-only prompt to Claude or Gemini.

    Returns (ok, raw_output).
    """
    vocab_prompt = _build_vocab_only_prompt(ctx)
    if not vocab_prompt:
        return False, ""
    vocab_prompt_file = ctx.orch_dir / "activities-vocab-fallback.md"
    vocab_prompt_file.write_text(vocab_prompt, "utf-8")
    use_claude = "C" in getattr(ctx, "use_claude", set())
    if use_claude:
        claude_model = getattr(ctx, "claude_model_C", CLAUDE_MODEL_ACTIVITIES)
        return _dispatch_claude_phase(
            vocab_prompt_file, prompt_label, model=claude_model, timeout=300,
        )
    else:
        return dispatch_gemini(
            _dispatch_prompt(ctx, vocab_prompt_file),
            task_id=f"v5-{ctx.slug}-pC-vocab",
            model=ctx.model, stdout_only=True,
            output_file=_gemini_output_path(ctx.slug, "pC-vocab"),
            timeout=300,
        )


def _try_vocab_fast_path(ctx: ModuleContext, state: dict) -> bool | None:
    """Try vocab-only generation when activities exist but vocab is missing.

    Returns True/False for definitive results, None to fall through.
    """
    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")
    if not (act_path and act_path.exists() and act_path.stat().st_size > 10
            and (not voc_path or not voc_path.exists())
            and _validate_activities_yaml(act_path)):
        return None

    log("  activities: Activities exist and valid, vocabulary missing — vocab-only dispatch")
    vok, vraw = _dispatch_vocab_only(ctx, "Phase C vocab")
    if vok:
        vocab_text = _extract_delimiter_tolerant(vraw, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            log(f"  activities: Vocabulary generated via fast-path → {voc_path.name}")
            if not _validate_activities_yaml(act_path):
                log("  activities: FAILED — activities YAML failed schema validation")
                mark_failed(state, "activities", ctx, note="activities-schema-invalid",
                            executor=_phase_executor(ctx, "activities"))
                return False
            mark_complete(state, "activities", ctx, task_id=f"v5-{ctx.slug}-pC-vocab",
                          executor=_phase_executor(ctx, "activities"))
            return True
    log("  activities: Vocab fast-path failed — falling through to full dispatch")
    return None


def _resolve_activities_template(ctx: ModuleContext) -> Path | None:
    """Resolve the activities prompt template, returning None on error."""
    activities_template_name = _get_activities_template(ctx.track, ctx.module_num, slug=ctx.slug)
    template = PHASES_DIR / activities_template_name
    if not template.exists():
        template = PHASES_DIR / "activities.md"
        log(f"  activities: Tier template {activities_template_name} not found, falling back to activities.md")
    else:
        log(f"  activities: Using tier template: {activities_template_name}")
    if not template.exists():
        log(f"  activities: ERROR — template not found: {template}")
        return None
    return template


def _dispatch_activities(ctx: ModuleContext, prompt_file: Path) -> tuple[bool, str]:
    """Dispatch activities+vocab generation to Claude or Gemini.

    Returns (ok, raw_output).
    """
    # Always use Claude Sonnet for activities — structured YAML output is
    # Claude's strength. Gemini keeps inventing wrong field names. (#977)
    claude_model = getattr(ctx, "claude_model_C", "claude-sonnet-4-6")
    log(f"  activities: Dispatching activities + vocab via Claude ({claude_model})...")
    return _dispatch_claude_phase(
        prompt_file, "Phase C", model=claude_model, timeout=600,
        allow_tools=[
            "mcp__rag__verify_word", "mcp__rag__verify_words",
            "mcp__rag__verify_lemma", "mcp__rag__search_text",
        ],
    )
    # Gemini dispatch kept as dead code for reference
    if False:
        log("  activities: Dispatching activities + vocab...")
        output_file = _gemini_output_path(ctx.slug, "pC")
        return dispatch_gemini(
            _dispatch_prompt(ctx, prompt_file),
            task_id=f"v5-{ctx.slug}-pC",
            model=ctx.model, stdout_only=True, output_file=output_file,
            timeout=TIMEOUT_ACTIVITIES,
        )


def _extract_activities_output(ctx: ModuleContext, raw_output: str) -> tuple[bool, bool]:
    """Extract activities and vocabulary from LLM output, write to disk.

    Returns (wrote_activities, wrote_vocab).
    """
    act_path = ctx.paths.get("activities")
    voc_path = ctx.paths.get("vocabulary")

    wrote_activities = act_path and act_path.exists() and act_path.stat().st_size > 10
    wrote_vocab = voc_path and voc_path.exists() and voc_path.stat().st_size > 10

    if not wrote_activities:
        activities_text = _extract_delimiter(raw_output, "===ACTIVITIES_START===", "===ACTIVITIES_END===")
        if activities_text and act_path:
            act_path.parent.mkdir(parents=True, exist_ok=True)
            act_path.write_text(activities_text, "utf-8")
            wrote_activities = True
            log(f"  activities: Activities extracted → {act_path.name}")
            (ctx.orch_dir / "activities-output.yaml").write_text(activities_text, "utf-8")
            save_gemini_session(ctx.orch_dir, label="activities")

    if not wrote_vocab:
        vocab_text = _extract_delimiter_tolerant(raw_output, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            wrote_vocab = True
            log(f"  activities: Vocabulary extracted → {voc_path.name}")
            (ctx.orch_dir / "activities-output-vocabulary.yaml").write_text(vocab_text, "utf-8")

    # Post-extraction VESUM check on activity distractors (#975 AC2)
    if wrote_activities and act_path and act_path.exists():
        try:
            _verify_activity_distractors(act_path, ctx.module_num)
        except Exception as e:
            log(f"  activities: Distractor verification failed: {e}")

    return wrote_activities, wrote_vocab


def _verify_activity_distractors(act_path: Path, module_num: int = 0) -> None:
    """Post-extraction VESUM check on all activity text fields.

    Extracts all Ukrainian words from options/distractors/answers,
    verifies against VESUM, and logs failures.

    A1.1 phonetics modules (M01-M06): skip words ≤ 3 chars — these are
    syllable fragments (МА, КІ, МО) used in blending exercises, not
    standalone words. VESUM correctly reports them as not-found.

    Issue: #975 AC2
    """
    from rag_batch_verify import extract_words_from_yaml, vesum_batch_lookup

    words = extract_words_from_yaml(act_path, is_vocab=False)
    if not words:
        return

    # A1.1 (M01-M06): skip syllable fragments (≤ 3 chars)
    # Other modules: skip single letters only (≤ 1 char)
    min_len = 4 if module_num <= 6 else 2
    check_words = [clean for clean in words if len(clean) >= min_len]
    if not check_words:
        return

    results = vesum_batch_lookup(check_words)
    failed = [words[w] for w in check_words if not results.get(w)]

    if failed:
        log(f"  activities: VESUM distractor check: {len(failed)} NOT FOUND: {', '.join(failed[:10])}")
    else:
        log(f"  activities: VESUM distractor check: {len(check_words)} words OK ✅")


def _extract_build_diagnostics(ctx: ModuleContext, raw_output: str) -> None:
    """Extract builder notes and friction report from LLM output."""
    # Builder notes
    builder_notes = _extract_delimiter(raw_output, "===BUILDER_NOTES_START===", "===BUILDER_NOTES_END===")
    if builder_notes:
        notes_file = ctx.orch_dir / "activities-builder-notes.yaml"
        notes_file.write_text(builder_notes, encoding="utf-8")
        log(f"  activities: Builder notes saved → {notes_file.name}")

    # Friction report
    friction = _extract_delimiter(raw_output, "===FRICTION_START===", "===FRICTION_END===")
    if friction:
        friction_file = ctx.orch_dir / "activities-friction.md"
        friction_file.write_text(friction, encoding="utf-8")
        log(f"  activities: Friction report saved → {friction_file.name}")
        is_real_truncation = (
            "TOKEN_LIMIT_TRUNCATION" in friction
            and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
        )
        if is_real_truncation:
            log("  activities: Gemini reported token limit truncation")


def _vocab_fallback(ctx: ModuleContext, raw_output: str) -> bool:
    """Attempt vocab-only fallback when vocab was truncated.

    Returns True if vocab was successfully generated.
    """
    voc_path = ctx.paths.get("vocabulary")
    if "===VOCABULARY_START===" not in raw_output:
        return False

    log("  activities: Vocabulary truncated — dispatching vocab-only fallback")
    vok, vraw = _dispatch_vocab_only(ctx, "Phase C vocab")
    if vok:
        vocab_text = _extract_delimiter_tolerant(vraw, "===VOCABULARY_START===", "===VOCABULARY_END===")
        if vocab_text and voc_path:
            voc_path.parent.mkdir(parents=True, exist_ok=True)
            voc_path.write_text(vocab_text, "utf-8")
            log(f"  activities: Vocabulary extracted from fallback → {voc_path.name}")
            return True
        else:
            log("  activities: Vocab fallback returned no valid delimited content")
    else:
        log("  activities: Vocab fallback dispatch failed")
    return False


# ---------------------------------------------------------------------------
# Phase: activities
# ---------------------------------------------------------------------------

def _load_activity_plans(ctx: ModuleContext) -> str:
    """Load activity plans YAML if it exists. Returns plans text or empty string."""
    act_path = ctx.paths.get("activities")
    if not act_path:
        return ""
    plans_file = act_path.parent / f"{ctx.slug}-plans.yaml"
    if not plans_file.exists():
        # Also check orchestration dir
        orch_plans = ctx.orch_dir / "activity-plans.yaml"
        if orch_plans.exists():
            plans_file = orch_plans
        else:
            return ""
    try:
        return plans_file.read_text("utf-8")
    except Exception:
        return ""


def _search_textbook_exercises(ctx: ModuleContext, plans_text: str) -> str:
    """Search RAG for textbook exercises matching the activity plans.

    Returns formatted textbook exercise context or empty string.
    This is a best-effort search — failure is non-blocking.
    """
    if not plans_text:
        return "(No activity plans available for textbook search)"

    # Extract focus keywords from plans
    import yaml as _yaml
    try:
        plans = _yaml.safe_load(plans_text)
        if not isinstance(plans, list):
            return "(Could not parse activity plans)"
    except Exception:
        return "(Could not parse activity plans)"

    search_terms = []
    for plan in plans[:6]:  # Limit to 6 searches
        focus = plan.get("focus", "")
        if focus:
            # Build Ukrainian search term
            term = f"вправа {focus}"
            search_terms.append(term)

    if not search_terms:
        return "(No search terms extracted from plans)"

    # Try direct RAG search import
    results_parts = []
    try:
        from rag.query import search_text
        for term in search_terms[:4]:  # Max 4 RAG searches
            hits = search_text(term, limit=2)
            if hits:
                formatted = "\n---\n".join(h.get("text", "")[:300] for h in hits)
                results_parts.append(f"### Search: {term}\n\n{formatted}")
    except ImportError:
        log("  activities: RAG module not available (non-blocking)")
    except Exception as e:
        log(f"  activities: RAG textbook search failed (non-blocking): {e}")

    if results_parts:
        return "\n\n".join(results_parts)
    return "(No textbook exercises found via RAG — generate original activities from plans)"


def phase_activities(ctx: ModuleContext, state: dict) -> bool:
    """Activities + Vocabulary generation (from plans + RAG when available)."""
    if is_complete(state, "activities"):
        log("  activities: SKIP (already complete)")
        return True

    # Check/adopt existing activities
    existing = _check_existing_activities(ctx, state)
    if existing == "adopt":
        return True

    # Fast path: vocab-only recovery
    fast = _try_vocab_fast_path(ctx, state)
    if fast is not None:
        return fast

    # Check for activity plans (generated during content phase)
    plans_text = _load_activity_plans(ctx)
    has_plans = bool(plans_text.strip())

    # Choose template: plan-based (activity-build.md) or traditional
    if has_plans:
        template = PHASES_DIR / "activity-build.md"
        if template.exists():
            log("  activities: Using plan-based template (activity-build.md)")
        else:
            log("  activities: activity-build.md not found, falling back to standard template")
            template = None
    else:
        template = None

    if template is None:
        template = _resolve_activities_template(ctx)
        if template is None:
            return False

    # Check for consultation-patched template (from --consult)
    patched = ctx.orch_dir / f"consultation-patched-{template.name}"
    if patched.exists():
        template = patched
        log(f"  activities: Using consultation-patched template: {patched.name}")

    # Build prompt with plan + RAG overrides
    prompt_file = ctx.orch_dir / "activities-prompt.md"
    overrides = {}
    if has_plans:
        overrides["ACTIVITY_PLANS"] = plans_text
        textbook_exercises = _search_textbook_exercises(ctx, plans_text)
        overrides["TEXTBOOK_EXERCISES"] = textbook_exercises
        log(f"  activities: Loaded {len(plans_text.splitlines())} plan lines, "
            f"{'found' if 'Search:' in textbook_exercises else 'no'} textbook exercises")

    if not fill_template(template, ctx.placeholders, prompt_file, overrides=overrides):
        return False

    # Pre-dispatch health check
    prompt_text = prompt_file.read_text("utf-8")
    health_issues = pipeline_lib.check_prompt_health(ctx, prompt_text, "activities")
    if not pipeline_lib.log_prompt_health(health_issues, "activities"):
        return False

    if ctx.dry_run:
        log("  activities: DRY-RUN — would dispatch activities.md")
        return True

    _act_exec = _phase_executor(ctx, "activities")

    # Dispatch LLM
    ok, raw_output = _dispatch_activities(ctx, prompt_file)
    if not ok:
        use_claude = "C" in getattr(ctx, "use_claude", set())
        log(f"  activities: FAILED — {'Claude' if use_claude else 'Gemini'} dispatch error")
        mark_failed(state, "activities", ctx, executor=_act_exec)
        return False

    # Extract outputs
    wrote_activities, wrote_vocab = _extract_activities_output(ctx, raw_output)

    # Friction report
    _extract_build_diagnostics(ctx, raw_output)

    # Vocabulary fallback if needed
    if wrote_activities and not wrote_vocab and _vocab_fallback(ctx, raw_output):
        wrote_vocab = True

    if not wrote_activities or not wrote_vocab:
        log(f"  activities: FAILED — missing files: activities={wrote_activities}, vocab={wrote_vocab}")
        mark_failed(state, "activities", ctx,
                    note=f"missing-files-act={wrote_activities}-voc={wrote_vocab}",
                    executor=_act_exec)
        return False

    # Post-C: auto-fix YAML before schema validation (#977)
    act_path = ctx.paths.get("activities")
    if act_path and act_path.exists():
        try:
            from pipeline.screen import _fix_yaml_activities
            n_yaml_fixes = _fix_yaml_activities(act_path)
            if n_yaml_fixes > 0:
                log(f"  activities: Auto-fixed {n_yaml_fixes} YAML schema issue(s) before validation")
        except Exception as e:
            log(f"  activities: YAML auto-fix failed: {e}")

    # Post-C schema validation gate
    if act_path and act_path.exists() and not _validate_activities_yaml(act_path):
        log("  activities: FAILED — activities YAML failed schema validation")
        mark_failed(state, "activities", ctx, note="activities-schema-invalid",
                    executor=_act_exec)
        return False

    mark_complete(state, "activities", ctx, task_id=f"v5-{ctx.slug}-pC",
                  executor=_act_exec)
    return True


# ---------------------------------------------------------------------------
# Phase: validate — helpers
# ---------------------------------------------------------------------------

_VALIDATE_NON_BLOCKING_ISSUE_TYPES = {"LLM_FILLER"}


def _validate_log_screen(label: str, scr: DScreenResult) -> None:
    """Log a validate screen result."""
    dc = len(scr.deterministic_issues)
    if scr.audit_passed and dc == 0:
        log(f"  validate: {label} — PASS")
    elif scr.audit_passed:
        log(f"  validate: {label} — audit PASS, {dc} deterministic issue(s)")
    elif dc > 0:
        log(f"  validate: {label} — audit FAIL, {dc} deterministic issue(s)")
    else:
        log(f"  validate: {label} — audit FAIL (gate violations, no deterministic issues)")


def _validate_only_non_blocking(scr: DScreenResult) -> bool:
    """Check if all deterministic issues are non-blocking."""
    return all(
        i["type"] in _VALIDATE_NON_BLOCKING_ISSUE_TYPES
        for i in scr.deterministic_issues
    )


def _validate_check_sidecars(ctx: ModuleContext) -> bool:
    """Check that required sidecar files exist. Returns False if blocked.

    Since activities now run AFTER review, validate only checks for content.
    Activities/vocab are optional at this stage — they'll be built later.
    """
    content_path = ctx.paths.get("md")
    if content_path and not content_path.exists():
        log(f"  validate: BLOCKED — content file missing: {content_path.name}")
        return False
    return True


def _validate_plan_autofix(ctx: ModuleContext, screen: DScreenResult) -> None:
    """Run plan auto-fix if VESUM not-found words exist."""
    if not screen.vesum_not_found:
        return
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


def _validate_run_proofread(ctx: ModuleContext, screen: DScreenResult) -> DScreenResult | None:
    """Run Gemini proofread if prose issues detected.

    Returns updated screen if proofread ran, None otherwise.
    """
    _PROSE_ISSUE_TYPES = {"RUSSIANISM", "LLM_FILLER", "PEDAGOGICAL", "DECODABILITY"}
    _PROSE_AUDIT_KEYWORDS = {"naturalness", "word_count", "immersion", "engagement", "euphony"}
    has_prose_issues = any(
        i["type"] in _PROSE_ISSUE_TYPES for i in screen.deterministic_issues
    )
    if not has_prose_issues and not screen.audit_passed:
        audit_lower = screen.audit_output.lower()
        has_prose_issues = any(kw in audit_lower for kw in _PROSE_AUDIT_KEYWORDS)
    if not has_prose_issues:
        return None

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

    new_screen = _deterministic_screen(ctx, skip_review=True, skip_activities=True)
    _validate_log_screen("Post-proofread", new_screen)
    return new_screen


def _validate_try_escalate(ctx: ModuleContext, screen: DScreenResult,
                           state: dict, phase: str, attempt: int,
                           note_success: str, note_fail: str) -> bool | None:
    """Try escalation fix, return True/False or None if not attempted."""
    if _escalate_fix(ctx, screen.audit_output, "validate", content_only=True, skip_review=True):
        new_screen = _deterministic_screen(ctx, skip_review=True, skip_activities=True)
        _save_screen_result(ctx, new_screen)
        mark_complete(state, phase, ctx, attempts=attempt, note=note_success,
                      executor=executor_llm("claude", ESCALATION_MODEL_CLAUDE))
        _update_pipeline_status(ctx, "draft")
        return True
    _save_screen_result(ctx, screen)
    mark_failed(state, phase, ctx, attempts=attempt, note=note_fail,
                executor=executor_llm("claude", ESCALATION_MODEL_CLAUDE))
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


def _validate_apply_fix_output(ctx: ModuleContext, fix_output: Path, attempt: int) -> None:
    """Apply section fixes from Gemini fix output."""
    if not fix_output.exists():
        return
    fix_text = fix_output.read_text("utf-8")
    (ctx.orch_dir / f"validate-fix{attempt}-raw.md").write_text(fix_text, "utf-8")
    save_gemini_session(ctx.orch_dir, label=f"validate-fix{attempt}")
    if "===SECTION_FIX_START===" in fix_text:
        _apply_section_fixes(ctx.paths["md"], fix_text)
        if ctx.paths.get("activities") and ctx.paths["activities"].exists():
            _apply_section_fixes(ctx.paths["activities"], fix_text)
        _vp = ctx.paths.get("vocabulary")
        if _vp and _vp.exists():
            _apply_section_fixes(_vp, fix_text)


def _validate_fix_loop(ctx: ModuleContext, state: dict, phase: str,
                       screen: DScreenResult, max_iters: int) -> bool:
    """Run the Gemini fix loop for validation. Returns True on pass."""
    prev_audit_output = screen.audit_output
    consecutive_failures = 0
    seen_fix_hashes: set[str] = set()

    for attempt in range(1, max_iters + 1):
        log(f"  validate: Fix attempt {attempt}/{max_iters}...")

        fix_prompt = _build_fix_prompt(ctx, screen.audit_output, content_only=True,
                                       deterministic_issues=screen.deterministic_issues)

        # Guard: skip if fix prompt has no specific violations
        fix_count = fix_prompt.count("### Fix")
        other_failures = "### Other Audit Failures" in fix_prompt
        if fix_count == 0 and not other_failures:
            log("  validate: EMPTY fix prompt (no violations extracted), escalating directly")
            result = _validate_try_escalate(
                ctx, screen, state, phase, attempt,
                "escalation-empty-fix", "empty-fix-exhausted")
            return result if result is not None else False

        # Dedup: skip if identical fix prompt
        fix_hash = hashlib.sha256(fix_prompt.encode()).hexdigest()[:16]
        if fix_hash in seen_fix_hashes:
            # Diagnose: is this a prompt engineering bug or a genuine content issue?
            diagnosis = _diagnose_dedup_cause(fix_prompt, screen)
            if diagnosis:
                # Known prompt/context problem — escalation won't help
                log(f"  validate: DEDUP — prompt engineering issue detected: {diagnosis}")
                _save_friction_report(ctx, attempt, fix_prompt, diagnosis)
                _save_screen_result(ctx, screen)
                mark_failed(state, phase, ctx, attempts=attempt,
                            note=f"dedup-prompt-bug:{diagnosis}",
                            executor=executor_llm("gemini", ctx.model))
                _update_pipeline_status(ctx, "needs-template-fix")
                return False
            # Unknown cause — escalate to Opus as last resort
            log("  validate: DEDUP — no known prompt issue, escalating to Claude")
            result = _validate_try_escalate(
                ctx, screen, state, phase, attempt,
                "escalation-claude-dedup", "dedup-exhausted")
            return result if result is not None else False
        seen_fix_hashes.add(fix_hash)

        fix_prompt_file = ctx.orch_dir / f"validate-fix{attempt}-prompt.md"
        fix_prompt_file.write_text(fix_prompt, "utf-8")

        fix_output = _gemini_output_path(ctx.slug, f"validate-fix{attempt}")
        # Use Pro for fixes — better quality = fewer iterations needed.
        # Flash was exhausted during overnight builds (#972). Fallback handles rate limits.
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

        _validate_apply_fix_output(ctx, fix_output, attempt)
        _run_deterministic_fixes(ctx)
        screen = _deterministic_screen(ctx, skip_review=True, skip_activities=True)

        if attempt > 0 and screen.audit_output == prev_audit_output:
            log(f"  validate: WARNING — fix {attempt} made no progress")
            if screen.audit_passed:
                log("  validate: Audit PASSES — exiting fix loop")
                _save_screen_result(ctx, screen)
                mark_complete(state, phase, ctx, attempts=attempt,
                              note=f"pass-with-{len(screen.deterministic_issues)}-info-issues",
                              executor=executor_llm("gemini", ctx.model))
                _update_pipeline_status(ctx, "draft")
                return True
        prev_audit_output = screen.audit_output

        if screen.audit_passed and (not screen.deterministic_issues or _validate_only_non_blocking(screen)):
            _save_screen_result(ctx, screen)
            mark_complete(state, phase, ctx, attempts=attempt,
                          executor=executor_llm("gemini", ctx.model))
            _update_pipeline_status(ctx, "draft")
            return True

        if attempt >= max_iters:
            log(f"  validate: EXHAUSTED — {max_iters} fix attempts")
            result = _validate_try_escalate(
                ctx, screen, state, phase, attempt,
                "escalation-claude", "exhausted")
            return result if result is not None else False

    _save_screen_result(ctx, screen)
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


# ---------------------------------------------------------------------------
# Phase: validate
# ---------------------------------------------------------------------------

def _diagnose_dedup_cause(fix_prompt: str, screen: DScreenResult) -> str | None:
    """Diagnose why a fix prompt is identical to a previous attempt.

    Returns a short diagnostic string if a known prompt engineering issue
    is detected, or None if the cause is unknown (legitimate escalation).
    """
    # 1. Immersion gap too large for fix pass
    imm_match = re.search(r"Gate `Immersion` FAIL.*?([\d.]+)%\s+LOW\s+\(target\s+(\d+)", fix_prompt)
    if imm_match:
        current = float(imm_match.group(1))
        target = int(imm_match.group(2))
        if target - current > 10:
            return f"immersion-gap-{target - current:.0f}pp"

    # 2. Activity count too low with no required types guidance
    if "Gate `Activities` FAIL" in fix_prompt and ("Required types:" not in fix_prompt or "Required types: \n" in fix_prompt):
            return "activities-no-required-types"

    # 3. Constraint conflict: fix says remove dative but sandbox lists dative forms
    if "Dative case used at A1" in fix_prompt and "мені" not in fix_prompt.split("FORBIDDEN")[0] if "FORBIDDEN" in fix_prompt else True:
        # Check if the fix prompt's constraints section doesn't mention dative ban
        constraints_section = fix_prompt.split("## Constraints")[1] if "## Constraints" in fix_prompt else ""
        if "dative" not in constraints_section.lower():
            return "constraint-conflict-dative"

    # 4. Multiple gate failures (5+) — likely systemic template issue
    # Exclude diffuse codes (ROBOTIC_STRUCTURE, etc.) since those are expected
    # to fail and don't indicate a template bug
    gate_fail_count = fix_prompt.count("Gate `")
    ped_codes = re.findall(r'\[([A-Z_]{3,})\]', fix_prompt)
    targeted_ped_count = sum(1 for c in ped_codes if c not in _DIFFUSE_FAILURE_CODES)
    total_targeted = gate_fail_count + targeted_ped_count
    # Mar 2026: raised from 5 to 15. Many "failures" are now non-blocking
    # (INFO, HEADING_LEVEL removed from blocking). The precheck was killing
    # 25/66 modules without even trying to fix them. (#980)
    if total_targeted >= 15:
        return f"systemic-{total_targeted}-failures"

    return None


def _save_friction_report(ctx: ModuleContext, attempt: int,
                          fix_prompt: str, diagnosis: str) -> None:
    """Save a friction report when dedup detects a prompt engineering issue."""
    report_path = ctx.orch_dir / "content-friction-dedup.md"
    gate_failures = re.findall(r"Gate `(\w+)` FAIL", fix_prompt)
    ped_violations = re.findall(r"\[([A-Z_]+)\]", fix_prompt)

    report = (
        f"**Phase**: Validate (fix loop)\n"
        f"**Step**: Dedup at attempt {attempt}\n"
        f"**Friction Type**: PROMPT_ENGINEERING_BUG\n"
        f"**Diagnosis**: {diagnosis}\n"
        f"**Gate Failures**: {', '.join(gate_failures) or 'none'}\n"
        f"**Violations**: {', '.join(set(ped_violations)) or 'none'}\n"
        f"**Raw Error**: Fix prompt was identical to previous attempt — "
        f"Gemini cannot fix these issues with the current template/context.\n"
        f"**Action Required**: Review and fix the prompt template or sandbox "
        f"configuration before rebuilding.\n"
    )
    report_path.write_text(report, "utf-8")
    log(f"  validate: Friction report saved to {report_path.name}")


def _immersion_needs_regeneration(screen: DScreenResult) -> bool:
    """Check if immersion failure is too large to fix — needs content regeneration.

    Returns True when immersion is >10pp below the target floor, meaning
    the content structure is fundamentally English-heavy and can't be patched
    by adding a few Ukrainian headers/phrases.
    """
    for line in screen.audit_output.split("\n"):
        m = re.match(r"\s*Immersion\s+❌\s+([\d.]+)%\s+LOW\s+\(target\s+(\d+)-(\d+)%", line)
        if m:
            current = float(m.group(1))
            target_min = int(m.group(2))
            gap = target_min - current
            if gap > 10:
                log(f"  validate: Immersion {current:.1f}% vs {target_min}% floor — gap {gap:.0f}pp (>10pp threshold)")
                return True
    return False


def phase_validate(ctx: ModuleContext, state: dict) -> bool:
    """Validate: full deterministic checks + Gemini fix loop."""
    phase = "validate"
    if is_complete(state, phase):
        log("  validate: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  validate: DRY-RUN — would run full audit + screen + fix loop")
        return True

    if not _validate_check_sidecars(ctx):
        return False

    # Auto-fix pass
    auto_fix_total = _run_deterministic_fixes(ctx)
    if auto_fix_total > 0:
        log(f"  validate: {auto_fix_total} deterministic fix(es) applied")

    # Initial screen (prose-only — activities not built yet)
    screen = _deterministic_screen(ctx, skip_review=True, skip_activities=True)
    _validate_log_screen("Initial", screen)

    # Plan auto-fix
    _validate_plan_autofix(ctx, screen)

    _val_exec = executor_deterministic("morphological_validator")

    # Early pass: no issues
    if screen.audit_passed and not screen.deterministic_issues:
        _save_screen_result(ctx, screen)
        mark_complete(state, phase, ctx, attempts=0, executor=_val_exec)
        _update_pipeline_status(ctx, "draft")
        return True

    # Early pass: only non-blocking issues
    if screen.audit_passed and _validate_only_non_blocking(screen):
        n = len(screen.deterministic_issues)
        log(f"  validate: PASS — audit gates pass, {n} non-blocking issue(s) (filler)")
        _save_screen_result(ctx, screen)
        mark_complete(state, phase, ctx, attempts=0,
                      note=f"pass-with-{n}-filler-issues", executor=_val_exec)
        _update_pipeline_status(ctx, "draft")
        return True

    # Gemini proofread
    proofread_screen = _validate_run_proofread(ctx, screen)
    if proofread_screen is not None:
        screen = proofread_screen
        if screen.audit_passed and (not screen.deterministic_issues or _validate_only_non_blocking(screen)):
            n = len(screen.deterministic_issues)
            note = "proofread-fix" if n == 0 else f"proofread-fix-with-{n}-filler"
            _save_screen_result(ctx, screen)
            mark_complete(state, phase, ctx, attempts=0, note=note,
                          executor=executor_llm("gemini", ctx.model))
            _update_pipeline_status(ctx, "draft")
            return True

    # Pre-check: detect prompt engineering bugs BEFORE wasting a fix cycle
    # Build the fix prompt that WOULD be sent and diagnose it proactively
    pre_fix_prompt = _build_fix_prompt(ctx, screen.audit_output, content_only=True,
                                       deterministic_issues=screen.deterministic_issues)
    pre_diagnosis = _diagnose_dedup_cause(pre_fix_prompt, screen)
    if pre_diagnosis and pre_diagnosis.startswith("systemic"):
        # Systemic failures (5+ gates) — template is fundamentally broken, don't even try
        log(f"  validate: PRE-CHECK — prompt engineering issue: {pre_diagnosis}")
        _save_friction_report(ctx, 0, pre_fix_prompt, pre_diagnosis)
        _save_screen_result(ctx, screen)
        mark_failed(state, phase, ctx, attempts=0, note=f"precheck-prompt-bug:{pre_diagnosis}",
                    executor=_val_exec)
        _update_pipeline_status(ctx, "needs-template-fix")
        return False

    # Check if immersion is the primary blocker with a large gap — regenerate instead of fix
    regen_key = "_immersion_regenerated"
    if _immersion_needs_regeneration(screen) and not state.get(regen_key):
        log("  validate: Immersion gap too large for fix loop — regenerating content")
        state[regen_key] = True  # Prevent infinite regeneration loop
        # Clear content completion so it re-runs (activities run later, after review)
        if "content" in state.get("phases", {}):
            del state["phases"]["content"]
        # Re-run content phase inline
        if not phase_content(ctx, state):
            log("  validate: Content regeneration FAILED")
            mark_failed(state, phase, ctx, note="immersion-regen-content-fail",
                        executor=_val_exec)
            return False
        # Re-screen with regenerated content (prose-only)
        _run_deterministic_fixes(ctx)
        screen = _deterministic_screen(ctx, skip_review=True, skip_activities=True)
        _validate_log_screen("Post-regeneration", screen)
        if screen.audit_passed and (not screen.deterministic_issues or _validate_only_non_blocking(screen)):
            _save_screen_result(ctx, screen)
            mark_complete(state, phase, ctx, attempts=0, note="immersion-regenerated",
                          executor=_val_exec)
            _update_pipeline_status(ctx, "draft")
            return True
        # Fall through to fix loop with regenerated content

    # Gemini fix loop
    max_iters = getattr(ctx, "max_fix", None) or _max_audit_iters(ctx.track)
    content_self_audited = state.get("phases", {}).get("content", {}).get("self_audited", False)
    if content_self_audited and max_iters > 2:
        log(f"  validate: Content was self-audited — reducing max fix iterations from {max_iters} to 2")
        max_iters = 2
    ctx.paths["md"]  # ensure md path exists

    return _validate_fix_loop(ctx, state, phase, screen, max_iters)


# ---------------------------------------------------------------------------
# Phase: review (Claude) — helpers
# ---------------------------------------------------------------------------


def _review_resolve_templates() -> tuple[Path | None, Path | None]:
    """Resolve D1 and D2 review templates. Returns (d1_template, d2_template)."""
    d1_template = PHASES_DIR / "review-structured.md"
    if not d1_template.exists():
        d1_template = PHASES_DIR / "review-evidence.md"
    d2_template = PHASES_DIR / "review-repair.md"
    if not d1_template.exists():
        log(f"  review: ERROR — D1 template not found: {d1_template}")
        return None, None
    if not d2_template.exists():
        log(f"  review: ERROR — D2 template not found: {d2_template}")
        return None, None
    return d1_template, d2_template


def _review_build_d1_prompt(ctx: ModuleContext, screen: DScreenResult,
                            d1_template: Path) -> Path | None:
    """Build the D1 review prompt with all injected context. Returns prompt path or None."""
    module_num = ctx.module_num if hasattr(ctx, "module_num") else 1
    track_calibration = _get_track_calibration(ctx.track, module_num)
    russicism_table = _get_russicism_table(ctx.track)

    prompt_file = ctx.orch_dir / "review-prompt.md"
    if not fill_template(d1_template, ctx.placeholders, prompt_file):
        return None

    prompt_text = prompt_file.read_text("utf-8")
    prompt_text = _inject_metrics_into_prompt(prompt_text, screen.metrics)
    prompt_text = prompt_text.replace("{COMPUTED_H2_SECTIONS}", screen.h2_sections)
    prompt_text = prompt_text.replace("{TRACK_CALIBRATION}", track_calibration or "(No track calibration available)")
    prompt_text = prompt_text.replace("{DETERMINISTIC_ISSUES}", _format_deterministic_issues(screen.deterministic_issues))
    prompt_text = prompt_text.replace("{RUSSIANISM_TABLE}", russicism_table or "(No track-specific Russianism table available — use general checklist)")
    prompt_text = prompt_text.replace("{FILLER_PHRASES}", _format_filler_phrases(screen.deterministic_issues))

    # Inject builder notes if available
    builder_notes_path = ctx.orch_dir / "builder-notes.yaml"
    if builder_notes_path.exists():
        builder_notes = builder_notes_path.read_text("utf-8")
        notes_block = f"```yaml\n{builder_notes}\n```\nFocus your review on the `review_focus` items above."
    else:
        notes_block = "(No builder notes from content phase)"
    prompt_text = prompt_text.replace("{BUILDER_NOTES_BLOCK}", notes_block)

    rag_context = _prefetch_rag_context(ctx)
    prompt_text = prompt_text.replace("{RAG_PRIMARY_SOURCES}", rag_context)

    vesum_word_context = _format_vesum_verification(screen.vesum_stats, screen.vesum_not_found)
    prompt_text = prompt_text.replace("{RAG_WORD_VERIFICATION}", vesum_word_context)

    prompt_file.write_text(prompt_text, "utf-8")

    log(f"    Metrics: {screen.metrics.get('COMPUTED_WORD_COUNT', '?')}w / "
        f"{screen.metrics.get('COMPUTED_WORD_TARGET', '?')}w, "
        f"{screen.metrics.get('COMPUTED_ACTIVITY_COUNT', '?')} activities, "
        f"immersion {screen.metrics.get('COMPUTED_IMMERSION_PERCENT', '?')}%")
    return prompt_file


def _review_dispatch_d1(ctx: ModuleContext, prompt_file: Path,
                        claude_model: str, review_timeout: int,
                        state: dict, phase: str) -> tuple[Any, str, str] | None:
    """Dispatch D1 review with retry. Returns (d1_result, review_text, raw_output) or None."""
    _pre_d1_snapshots = _snapshot_module_files(ctx)

    d1_tools = ["Read", "Grep", "Glob", "Edit", *_RAG_REVIEW_TOOLS]

    ok, raw_output = _dispatch_claude_phase(
        prompt_file, "Phase D.1",
        model=claude_model, timeout=review_timeout,
        allow_tools=d1_tools,
    )
    if not ok:
        log("  review: Dispatch FAILED")
        _claude_exec = executor_llm("claude", claude_model)
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed",
                    executor=_claude_exec)
        return None

    _log_d1_edits(ctx, _pre_d1_snapshots)
    d1 = _parse_d1_review(raw_output)

    _claude_exec = executor_llm("claude", claude_model)

    if not d1.ok or not d1.raw_review:
        log("  review: WARNING — no REVIEW delimiters in output (retrying)")
        (ctx.orch_dir / "review-raw-output.md").write_text(raw_output, "utf-8")

        ok2, raw2 = _dispatch_claude_phase(
            prompt_file, "Phase D.1 (retry)",
            model=claude_model, timeout=review_timeout,
            allow_tools=d1_tools,
        )
        if ok2:
            d1 = _parse_d1_review(raw2)

        if not d1.ok or not d1.raw_review:
            log("  review: Retry also failed — no delimiters")
            mark_failed(state, phase, ctx, attempts=1, note="no-review",
                        executor=_claude_exec)
            return None

    review_text = d1.raw_review

    qg_ok, qg_reason = _quick_review_quality_gate(review_text, ctx.paths["md"])
    if not qg_ok:
        log(f"  review: REJECTED — {qg_reason}")
        (ctx.orch_dir / "review-rejected.md").write_text(review_text, "utf-8")
        mark_failed(state, phase, ctx, attempts=1, note="shallow-review",
                    executor=_claude_exec)
        return None

    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** {claude_model}\n\n{review_text}"

    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
    (ctx.orch_dir / "review-raw-output.md").write_text(raw_output, "utf-8")
    log(f"  review: Review saved → {ctx.paths['review'].name}")

    return d1, review_text, raw_output


def _review_determine_verdict(d1: Any, review_text: str) -> bool:
    """Determine if the review says FAIL. Returns True if review says fail."""
    review_says_fail = d1.verdict == "FAIL"
    if not review_says_fail and d1.scores.get("overall", 10) < 9.0:
        review_says_fail = True
    if not d1.verdict:
        status_m = re.search(r'\*\*Status:\*\*\s*(FAIL|PASS)', review_text)
        score_m = re.search(r'\*\*Overall Score:\*\*\s*([\d.]+)/10', review_text)
        if (status_m and status_m.group(1) == "FAIL") or (score_m and float(score_m.group(1)) < 9.0):
            review_says_fail = True
    return review_says_fail


def _review_d2_fix_iteration(ctx: ModuleContext, d2_template: Path,
                             claude_model: str, fix_timeout: int,
                             fix_plan: str, audit_out: str,
                             fix_iter: int) -> tuple[bool | None, str]:
    """Run a single D2 fix iteration.

    Returns (result, updated_audit_out) where result is True (pass),
    False (hard fail), or None (continue to next iteration).
    """
    iter_suffix = "" if fix_iter == 0 else f" (iter {fix_iter + 1})"

    log(f"  review: Fix attempt {fix_iter + 1}/{MAX_REVIEW_FIX_ITERS}{iter_suffix}...")
    failures = _extract_audit_failures(audit_out) or "None (audit passed). Focus exclusively on the Fix Plan."
    failures += _extract_gate_blockers(ctx)
    failures += _extract_vesum_failures(ctx)

    prompt_file2 = ctx.orch_dir / f"review-fix-{fix_iter + 1}-prompt.md"
    if not fill_template(d2_template, ctx.placeholders, prompt_file2):
        return False, audit_out

    prompt2_text = prompt_file2.read_text("utf-8")
    prompt2_text = prompt2_text.replace("{EXTRACTED_FIX_PLAN}", fix_plan)
    prompt2_text = prompt2_text.replace("{INJECTED_AUDIT_FAILURES}", failures)
    prompt2_text = _inject_file_contents(prompt2_text, ctx)
    prompt_file2.write_text(prompt2_text, "utf-8")

    before_d2 = _snapshot_module_files(ctx)

    d2_tools = ["Edit", "Grep", *_RAG_REVIEW_TOOLS]

    ok2, raw_output2 = _dispatch_claude_phase(
        prompt_file2, f"Phase D.2{iter_suffix}",
        model=claude_model, timeout=fix_timeout,
        allow_tools=d2_tools,
    )
    if not ok2:
        log(f"  review: Fix dispatch failed{iter_suffix}")
        return False, audit_out

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
        return False, audit_out
    if changed_lines == 0:
        log(f"  review: WARNING — D.2 made no file changes{iter_suffix}")
        (ctx.orch_dir / f"review-fix-{fix_iter + 1}-raw.md").write_text(raw_output2, "utf-8")
    else:
        log(f"  review: D.2 applied fixes ({changed_lines} lines changed){iter_suffix}")

    _run_deterministic_fixes(ctx)
    passed, new_audit_out = run_verify(ctx.paths["md"])

    if passed:
        pass  # _rescore_post_fix disabled #980
        log(f"  review: PASS (after fix {fix_iter + 1})")
        return True, new_audit_out

    if fix_iter < MAX_REVIEW_FIX_ITERS - 1:
        log(f"  review: Fix {fix_iter + 1} insufficient — trying again...")

    return None, new_audit_out


def _review_d2_loop(ctx: ModuleContext, state: dict, phase: str,
                    d2_template: Path, claude_model: str,
                    review_text: str, review_says_fail: bool,
                    passed: bool, audit_out: str,
                    plan_adherence_text: str = "",
                    d1_fix_note: str = "") -> bool:
    """Run the D2 repair loop after D1 review. Returns True on pass."""
    # Check for citation failures
    _CITATION_FAILURES = ("FABRICATED_CITATIONS", "UNVERIFIED_CITATIONS")
    if any(f"\u274c [{tag}]" in audit_out for tag in _CITATION_FAILURES):
        log("  review: REVIEW QUALITY FAILURE — fabricated/unverified citations")
        if ctx.paths["review"].exists():
            ctx.paths["review"].unlink()
        _rev_exec = executor_llm("claude", claude_model)
        mark_failed(state, phase, ctx, attempts=1, note="citation-failure",
                    executor=_rev_exec)
        return False

    _rev_exec = executor_llm("claude", claude_model)

    # Try deterministic auto-fix
    auto_fix_count = _run_deterministic_fixes(ctx)
    if auto_fix_count > 0:
        passed_after_autofix, audit_out = run_verify(ctx.paths["md"])
        if passed_after_autofix and not review_says_fail:
            pass  # _rescore_post_fix disabled #980
            mark_complete(state, phase, ctx, attempts=1, note="autofix",
                          executor=_rev_exec)
            _update_pipeline_status(ctx, "reviewed")
            return True

    if _all_issues_diffuse(audit_out) and not plan_adherence_text:
        log("  review: SKIPPED fix — all issues are diffuse (needs manual review)")
        mark_failed(state, phase, ctx, attempts=1, note="needs-manual-review",
                    executor=_rev_exec)
        _update_pipeline_status(ctx, "needs-manual-review")
        return False
    elif _all_issues_diffuse(audit_out) and plan_adherence_text:
        log("  review: audit issues are diffuse but plan adherence has HIGH issues — proceeding with fix")

    audit_only_fix = not review_says_fail and not passed
    fix_timeout = _get_fix_timeout(ctx.track, audit_only=audit_only_fix)

    if audit_only_fix:
        fix_plan = (
            "**IMPORTANT: The review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions — they are informational only.**\n\n"
            "(Review omitted — verdict was PASS)\n"
        )
    else:
        fix_plan = _extract_fix_plan(review_text)

    # Inject structured review findings for targeted fixes (#937)
    if not audit_only_fix:
        from pipeline.review_findings import inject_findings_into_fix_plan
        fix_plan = inject_findings_into_fix_plan(ctx.orch_dir, fix_plan, "review")

    # Inject plan adherence issues (deterministic, HIGH severity)
    if plan_adherence_text:
        fix_plan = plan_adherence_text + "\n\n---\n\n" + fix_plan

    # Tell D2 about already-applied D1 fixes to prevent reversion
    if d1_fix_note:
        fix_plan = d1_fix_note + "\n" + fix_plan

    for fix_iter in range(MAX_REVIEW_FIX_ITERS):
        total_attempts = 2 + fix_iter
        result, audit_out = _review_d2_fix_iteration(
            ctx, d2_template, claude_model, fix_timeout,
            fix_plan, audit_out, fix_iter,
        )
        if result is True:
            mark_complete(state, phase, ctx,
                          attempts=total_attempts, note=f"fix-iter{fix_iter + 1}",
                          executor=_rev_exec)
            _update_pipeline_status(ctx, "reviewed")
            return True
        if result is False:
            mark_failed(state, phase, ctx,
                        attempts=total_attempts,
                        note="fix-dispatch-failed" if fix_iter == 0 else "diff-too-large",
                        executor=_rev_exec)
            _update_pipeline_status(ctx, "needs-manual-review")
            return False

    # Re-score on exhaustion (#975)
    pass  # _rescore_post_fix disabled #980

    # Check content gates only (skip review verdict — it's stale during fix loop)
    final_passed, _ = run_verify(ctx.paths["md"], skip_review=True)
    if final_passed:
        log("  review: Fix loop exhausted but content gates PASS — accepting with post-fix score")
        mark_complete(state, phase, ctx, attempts=2 + MAX_REVIEW_FIX_ITERS,
                      note="exhausted-content-passes", executor=_rev_exec)
        _update_pipeline_status(ctx, "reviewed")
        return True

    log("  review: EXHAUSTED — content gates still failing")
    mark_failed(state, phase, ctx,
                attempts=2 + MAX_REVIEW_FIX_ITERS, note="needs-manual-review",
                executor=_rev_exec)
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


# ---------------------------------------------------------------------------
# Plan adherence (deterministic, injected into review)
# ---------------------------------------------------------------------------

def _run_plan_adherence_check(ctx: ModuleContext) -> str:
    """Run plan adherence checks, return formatted fix text (empty if no issues)."""
    try:
        from audit.checks.plan_adherence import check_plan_adherence
    except ImportError:
        logger.warning("plan_adherence module not available — skipping")
        return ""

    plan_path = ctx.paths.get("plan")
    md_path = ctx.paths.get("md")
    activities_path = ctx.paths.get("activities")

    if not plan_path or not md_path:
        return ""

    result = check_plan_adherence(md_path, plan_path, activities_path or Path("/dev/null"))

    if not result.issues:
        log(f"  plan-adherence: {result.checks_run} checks, all passed")
        return ""

    high_issues = [i for i in result.issues if i.severity in ("CRITICAL", "HIGH")]
    medium_issues = [i for i in result.issues if i.severity == "MEDIUM"]

    log(f"  plan-adherence: {len(high_issues)} HIGH, {len(medium_issues)} MEDIUM issue(s)")

    if not high_issues and not medium_issues:
        # Only LOW — log but don't inject into fix plan
        return ""

    lines = ["## Plan Adherence Issues (Deterministic — MUST FIX)\n"]
    for issue in [*high_issues, *medium_issues]:
        lines.append(f"- **[{issue.severity}] {issue.check_type}** in `{issue.section}`")
        lines.append(f"  - Expected: {issue.expected}")
        lines.append(f"  - Actual: {issue.actual}")
        lines.append(f"  - Fix: {issue.fix_hint}")
        lines.append("")

    return "\n".join(lines)


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

    # Resolve templates
    d1_template, d2_template = _review_resolve_templates()
    if d1_template is None:
        return False

    claude_model = getattr(ctx, "claude_model_D", CLAUDE_MODEL_REVIEW)
    review_timeout = _get_review_timeout(ctx.track)

    log("  review: Preparing structured review prompt...")

    # Build and dispatch D1
    prompt_file = _review_build_d1_prompt(ctx, screen, d1_template)
    if prompt_file is None:
        return False

    log(f"  review: Dispatching Claude review ({claude_model}, {review_timeout}s)...")

    d1_result = _review_dispatch_d1(ctx, prompt_file, claude_model, review_timeout, state, phase)
    if d1_result is None:
        return False

    d1, review_text, raw_output = d1_result

    # Apply D1 inline fixes
    n_d1_fixes = _apply_module_fixes(ctx, raw_output)
    if n_d1_fixes > 0:
        log(f"  review: Applied {n_d1_fixes} inline fix(es) from review")
    elif "===SECTION_FIX_START===" in raw_output:
        log("  review: Fix block found but 0 fixes matched — check review-raw-output.md")

    _run_deterministic_fixes(ctx)
    plan_adherence_text = _run_plan_adherence_check(ctx)
    passed, audit_out = run_verify(ctx.paths["md"])

    # Determine verdict
    review_says_fail = _review_determine_verdict(d1, review_text)

    # Plan adherence HIGH issues force a fix round
    has_plan_issues = bool(plan_adherence_text)
    if has_plan_issues:
        review_says_fail = True

    # Early pass: no repair needed
    if passed and not review_says_fail:
        log("  review: PASS (no repair needed)")
        mark_complete(state, phase, ctx, attempts=1, note="review-only",
                      executor=executor_llm("claude", claude_model))
        _update_pipeline_status(ctx, "reviewed")
        return True

    # Early pass: D1 inline fixes resolved issues
    if passed and review_says_fail and n_d1_fixes > 0 and not has_plan_issues:
        log(f"  review: PASS (D.1 inline fixes resolved review issues — {n_d1_fixes} fix(es))")
        mark_complete(state, phase, ctx, attempts=1, note="d1-inline-fixes",
                      executor=executor_llm("claude", claude_model))
        _update_pipeline_status(ctx, "reviewed")
        return True

    # D2 repair loop
    # If D1 already applied inline fixes, tell D2 to skip those
    d1_fix_note = ""
    if n_d1_fixes > 0:
        d1_fix_note = (
            f"\n\n**NOTE: {n_d1_fixes} inline fix(es) from the review "
            "have ALREADY been applied to the files. Do NOT re-apply "
            "those fixes. Read the CURRENT file contents carefully — "
            "they reflect the post-fix state. Only fix issues that "
            "are still present in the current files.**\n"
        )

    return _review_d2_loop(
        ctx, state, phase, d2_template, claude_model,
        review_text, review_says_fail, passed, audit_out,
        plan_adherence_text=plan_adherence_text,
        d1_fix_note=d1_fix_note,
    )


# ---------------------------------------------------------------------------
# Phase: review (Gemini RAG-grounded)
# ---------------------------------------------------------------------------

def _dispatch_review_passes(ctx: ModuleContext, screen, rag_data: dict,
                             total_rag: int) -> tuple[D1Result | None, D1Result | None, str, str]:
    """Dispatch Pass 1 (factual) then Pass 2 (linguistic) sequentially.

    Returns (pass1_result, pass2_result, raw1, raw2).
    """
    raw1 = ""
    raw2 = ""
    pass1_result: D1Result | None = None

    # Pass 1: Factual check (RAG-grounded)
    if total_rag > 0:
        pass1_prompt = _build_pass1_prompt(ctx, screen, rag_data)
        (ctx.orch_dir / "review-pass1-prompt.md").write_text(pass1_prompt, "utf-8")

        log("  review-gemini: Dispatching Pass 1 (factual check)...")
        ok1, raw1 = pipeline_lib.dispatch_gemini_raw(
            pass1_prompt, task_id=f"{ctx.slug}-review-pass1", timeout=600)

        if ok1:
            (ctx.orch_dir / "review-pass1-raw.md").write_text(raw1, "utf-8")
            pass1_result = _parse_factual_review(raw1)
            if pass1_result.ok:
                disc_count = len([i for i in pass1_result.issues if i.get("type") == "FACTUAL_DISCREPANCY"])
                log(f"  review-gemini: Pass 1 \u2014 {pass1_result.verdict} "
                    f"({disc_count} discrepancies, score {pass1_result.scores.get('factual_accuracy', '?')})")
            else:
                log("  review-gemini: Pass 1 \u2014 failed to parse output")
        else:
            log("  review-gemini: Pass 1 \u2014 dispatch failed")
    else:
        log("  review-gemini: Pass 1 SKIPPED (no RAG sources)")
        pass1_result = D1Result(ok=True, verdict="PASS", raw_review="(No RAG sources available \u2014 factual check skipped)")

    # Pass 2: Linguistic review
    pass2_prompt = _build_pass2_prompt(ctx, screen)
    (ctx.orch_dir / "review-pass2-prompt.md").write_text(pass2_prompt, "utf-8")

    log("  review-gemini: Dispatching Pass 2 (linguistic review)...")
    ok2, raw2 = pipeline_lib.dispatch_gemini_raw(
        pass2_prompt, task_id=f"{ctx.slug}-review-pass2", timeout=600)

    pass2_result: D1Result | None = None
    if ok2:
        (ctx.orch_dir / "review-pass2-raw.md").write_text(raw2, "utf-8")
        pass2_result = _parse_d1_review(raw2)
        if pass2_result.ok:
            log(f"  review-gemini: Pass 2 \u2014 {pass2_result.verdict} "
                f"(overall {pass2_result.scores.get('overall', '?')}/10)")
        else:
            log("  review-gemini: Pass 2 \u2014 failed to parse output")
    else:
        log("  review-gemini: Pass 2 \u2014 dispatch failed")

    return pass1_result, pass2_result, raw1, raw2


def _apply_review_fixes_and_plan_autofix(ctx: ModuleContext, screen,
                                          raw1: str, raw2: str) -> int:
    """Apply inline fixes from review passes, run deterministic fixes, and plan auto-fix.

    Returns the number of inline fixes applied.
    """
    n_fixes = 0
    if raw1 and "===SECTION_FIX_START===" in raw1:
        n_fixes += _apply_module_fixes(ctx, raw1)
    if raw2 and "===SECTION_FIX_START===" in raw2:
        n_fixes += _apply_module_fixes(ctx, raw2)
    if n_fixes > 0:
        log(f"  review-gemini: Applied {n_fixes} inline fix(es) from review passes")

    _run_deterministic_fixes(ctx)

    # Plan auto-fix
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

    return n_fixes


def _run_review_fix_loop(ctx: ModuleContext, state: dict, phase: str,
                          fix_plan: str, audit_out: str,
                          review_grounding: str) -> bool:
    """Run the review fix loop. Returns True if audit passes after a fix iteration."""
    for fix_iter in range(MAX_REVIEW_FIX_ITERS):
        total_attempts = 2 + fix_iter
        log(f"  review-gemini: Fix attempt {fix_iter + 1}/{MAX_REVIEW_FIX_ITERS}...")

        applied = _gemini_fix_iteration(ctx, fix_plan, audit_out, fix_iter)
        if not applied and fix_iter == 0:
            log("  review-gemini: No fixes applied \u2014 trying once more")

        _run_deterministic_fixes(ctx)
        passed, audit_out = run_verify(ctx.paths["md"], skip_review=True)

        if passed:
            log(f"  review-gemini: PASS (after fix {fix_iter + 1})")
            return _complete_gemini_review(ctx, state, phase, total_attempts,
                                           f"gemini-fix-iter{fix_iter + 1}",
                                           grounding=review_grounding)

        if fix_iter < MAX_REVIEW_FIX_ITERS - 1:
            log(f"  review-gemini: Fix {fix_iter + 1} insufficient \u2014 trying again...")

    # Re-score on exhaustion — fixes may have improved quality (#975)
    pass  # _rescore_post_fix disabled #980

    # Check content gates only (skip review verdict — it's stale)
    final_passed, _ = run_verify(ctx.paths["md"], skip_review=True)
    if final_passed:
        log("  review-gemini: Fix loop exhausted but content gates PASS — accepting with post-fix score")
        return _complete_gemini_review(ctx, state, phase,
                                       2 + MAX_REVIEW_FIX_ITERS,
                                       "exhausted-content-passes",
                                       grounding=review_grounding)

    log("  review-gemini: EXHAUSTED — content gates still failing")
    mark_failed(state, phase, ctx,
                attempts=2 + MAX_REVIEW_FIX_ITERS, note="needs-manual-review",
                executor=executor_llm("gemini", ctx.model))
    _update_pipeline_status(ctx, "needs-manual-review")
    return False


def phase_review_gemini(ctx: ModuleContext, state: dict) -> bool:
    """Gemini RAG-grounded review: sharded Fact Checker + Language Pedant."""
    phase = "review"
    if is_complete(state, phase):
        log("  review-gemini: SKIP (already complete)")
        return True

    if ctx.dry_run:
        log("  review-gemini: DRY-RUN \u2014 would dispatch Gemini sharded review")
        return True

    # 1. Load cached screen from validate phase
    screen = _load_screen_result(ctx)
    if screen is None:
        log("  review-gemini: No cached screen \u2014 running fresh screen")
        screen = _deterministic_screen(ctx)

    # 2. Load RAG discovery data
    rag_data = _load_rag_for_review(ctx)
    total_rag = len(rag_data["text_chunks"]) + len(rag_data["images"]) + len(rag_data["literary"])
    log(f"  review-gemini: RAG data loaded \u2014 {total_rag} items "
        f"(text: {len(rag_data['text_chunks'])}, images: {len(rag_data['images'])}, "
        f"literary: {len(rag_data['literary'])})")

    # 3-4. Dispatch review passes
    pass1_result, pass2_result, raw1, raw2 = _dispatch_review_passes(ctx, screen, rag_data, total_rag)

    # 5. Merge results
    merged = _merge_gemini_review_passes(pass1_result, pass2_result)
    if not merged.ok:
        log("  review-gemini: Merge FAILED \u2014 both passes unusable")
        mark_failed(state, phase, ctx, attempts=1, note="dispatch-failed",
                    executor=executor_llm("gemini", ctx.model))
        return False

    pass1_contributed = (pass1_result is not None and pass1_result.ok
                         and "factual_accuracy" in pass1_result.scores)
    review_grounding = "rag-textbook" if pass1_contributed else "linguistic-only"
    if not pass1_contributed and total_rag > 0:
        log("  review-gemini: WARNING \u2014 Pass 1 (factual check) failed, "
            "review grounding downgraded to linguistic-only")

    review_text = merged.raw_review

    # 6. Quality gate check
    if len(review_text.split()) < 100:
        log(f"  review-gemini: REJECTED \u2014 review too short ({len(review_text.split())} words)")
        mark_failed(state, phase, ctx, attempts=1, note="shallow-review",
                    executor=executor_llm("gemini", ctx.model))
        return False

    # 7. Inject Reviewed-By metadata
    if "Reviewed-By:" not in review_text:
        review_text = f"**Reviewed-By:** gemini-2.5-pro (RAG-grounded)\n\n{review_text}"

    # 8. Save review
    write_review_with_hash(ctx.paths["review"], review_text, ctx.paths["md"])
    (ctx.orch_dir / "review-result.md").write_text(review_text, "utf-8")
    log(f"  review-gemini: Review saved \u2192 {ctx.paths['review'].name}")

    # 9-10. Apply fixes
    n_fixes = _apply_review_fixes_and_plan_autofix(ctx, screen, raw1, raw2)

    # 10.5. Plan adherence check (deterministic — runs in both Claude and Gemini paths)
    plan_adherence_text = _run_plan_adherence_check(ctx)
    if plan_adherence_text:
        log("  review-gemini: Plan adherence issues found — will inject into fix plan")

    # 11. Post-review audit
    passed, audit_out = run_verify(ctx.paths["md"])

    review_says_fail = merged.verdict == "FAIL"
    if not review_says_fail and merged.scores.get("overall", 10) < 9.0:
        review_says_fail = True
    # Plan adherence failures also trigger fix loop
    if plan_adherence_text:
        review_says_fail = True

    if passed and not review_says_fail:
        log("  review-gemini: PASS (no repair needed)")
        return _complete_gemini_review(ctx, state, phase, 1, "gemini-review-only", grounding=review_grounding)

    if passed and review_says_fail and n_fixes > 0:
        # Check if all review issues were resolved by inline fixes (#975)
        _review_score = merged.scores.get("overall", 10)
        _n_issues = len(merged.issues or [])
        if n_fixes >= _n_issues or _review_score >= 9.0:
            # All issues fixed or score high enough — done
            _post_fix_passed, _post_fix_output = run_verify(ctx.paths["md"])
            log(f"  review-gemini: PASS (inline fixes resolved review issues — {n_fixes} fix(es), post-fix audit: {'PASS' if _post_fix_passed else 'FAIL'})")
            return _complete_gemini_review(ctx, state, phase, 1, "gemini-inline-fixes", grounding=review_grounding)
        else:
            # Partial fix — unresolved issues remain, enter fix loop
            log(f"  review-gemini: {n_fixes}/{_n_issues} issues fixed inline (score {_review_score}/10) — entering fix loop for remaining")

    if _all_issues_diffuse(audit_out):
        log("  review-gemini: SKIPPED fix \u2014 all issues diffuse (needs manual review)")
        mark_failed(state, phase, ctx, attempts=1, note="needs-manual-review",
                    executor=executor_llm("gemini", ctx.model))
        _update_pipeline_status(ctx, "needs-manual-review")
        return False

    # 12. Build fix plan and run fix loop
    _audit_only_fix = not review_says_fail and not passed
    if _audit_only_fix:
        fix_plan = (
            "**IMPORTANT: The review verdict was PASS. "
            "Fix ONLY the audit failures listed below. "
            "Do NOT fix review suggestions \u2014 they are informational only.**\n\n"
            "(Review omitted \u2014 verdict was PASS)\n"
        )
    else:
        fix_plan = _extract_fix_plan(review_text)

    # Inject plan adherence issues into fix plan
    if plan_adherence_text:
        fix_plan = plan_adherence_text + "\n\n---\n\n" + fix_plan

    # Inject structured review findings for targeted fixes (#937)
    if not _audit_only_fix:
        from pipeline.review_findings import inject_findings_into_fix_plan
        fix_plan = inject_findings_into_fix_plan(ctx.orch_dir, fix_plan, "review-gemini")

    return _run_review_fix_loop(ctx, state, phase, fix_plan, audit_out, review_grounding)


# ---------------------------------------------------------------------------
# Phase: review (dispatch)
# ---------------------------------------------------------------------------

def phase_review(ctx: ModuleContext, state: dict) -> bool:
    """Route review to Gemini (default) or Claude based on ctx.review_agent."""
    review_agent = getattr(ctx, "review_agent", "claude")
    if review_agent == "claude":
        log("  review: Using Claude reviewer")
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

_RESOURCES_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "resources" / "external_resources.yaml"


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
# 3b. Consultation — self-improving prompt loop
# ============================================================================

def run_consultation(ctx: ModuleContext, state: dict) -> bool:
    """Run prompt consultation on the latest failure.

    Instead of fixing content, this diagnoses template issues and proposes
    template edits. Gemini reads files directly via paths. Results are parsed
    and either applied (this_module) or queued (all_modules).
    """
    from pipeline.consultation import (
        apply_template_patch,
        parse_consultation,
        queue_for_approval,
        record_consultation,
    )

    log(f"\n  Consultation mode for {ctx.slug}")

    # ── 1. Find failure data ──────────────────────────────────────────
    review_failures = ""
    for fname in ("review-result.md", "review-raw-output.md"):
        f = ctx.orch_dir / fname
        if f.exists():
            review_failures = f.read_text("utf-8")[:4000]
            log(f"  consultation: Using failure data from {fname}")
            break

    if not review_failures:
        friction_files = sorted(ctx.orch_dir.glob("validate-fix*-raw.md"), reverse=True)
        if friction_files:
            review_failures = friction_files[0].read_text("utf-8")[:4000]
            log(f"  consultation: Using failure data from {friction_files[0].name}")

    # Fallback: audit report (when validate/review artifacts were cleaned)
    if not review_failures:
        audit_log = ctx.paths["md"].parent / "audit" / f"{ctx.slug}-audit.md"
        if audit_log.exists():
            review_failures = audit_log.read_text("utf-8")[:4000]
            log("  consultation: Using failure data from audit report")

    if not review_failures:
        log("  consultation: No failure data found — nothing to consult on")
        return False

    # ── 2. Identify base template + rendered prompt + output ──────────
    # Base template: the source file in PHASES_DIR (what we want to fix)
    content_template_name = _get_content_template(
        ctx.track, ctx.module_num,
        full_build=getattr(ctx, "full_build", False),
        rag=getattr(ctx, "rag", False),
        slug=ctx.slug,
    )
    base_template_path = PHASES_DIR / content_template_name

    # Also check activities template
    if not base_template_path.exists():
        activities_template_name = _get_activities_template(ctx.track, ctx.module_num, slug=ctx.slug)
        base_template_path = PHASES_DIR / activities_template_name

    if not base_template_path.exists():
        log(f"  consultation: Base template not found: {base_template_path}")
        return False
    log(f"  consultation: Base template → {base_template_path}")

    # Rendered prompt (what was sent to LLM)
    rendered_prompt_path = ""
    for prompt_name in ("content-prompt.md", "activities-prompt.md"):
        p = ctx.orch_dir / prompt_name
        if p.exists():
            rendered_prompt_path = str(p)
            break

    # Module output
    module_output_path = ""
    content_path = ctx.paths.get("md")
    if content_path and content_path.exists():
        module_output_path = str(content_path)

    # ── 3. Build consultation prompt (paths, not excerpts) ────────────
    consultation_template = PHASES_DIR / "consultation.md"
    if not consultation_template.exists():
        log(f"  consultation: Template not found: {consultation_template}")
        return False

    prompt_text = consultation_template.read_text("utf-8")
    prompt_text = prompt_text.replace("{REVIEW_FAILURES}", review_failures)
    prompt_text = prompt_text.replace("{BASE_TEMPLATE_PATH}", str(base_template_path))
    prompt_text = prompt_text.replace("{RENDERED_PROMPT_PATH}", rendered_prompt_path)
    prompt_text = prompt_text.replace("{MODULE_OUTPUT_PATH}", module_output_path)

    # Count existing consultations (exclude prompt files from count)
    existing = [f for f in ctx.orch_dir.glob("consultation-*.md")
                if "-prompt" not in f.name and "-raw" not in f.name]
    n = len(existing) + 1

    prompt_file = ctx.orch_dir / f"consultation-{n}-prompt.md"
    prompt_file.write_text(prompt_text, "utf-8")

    if ctx.dry_run:
        log(f"  consultation: DRY-RUN — would dispatch consultation #{n}")
        return True

    # ── 4. Dispatch to Gemini ─────────────────────────────────────────
    output_file = _gemini_output_path(ctx.slug, f"consultation-{n}")
    ok, raw = dispatch_gemini(
        _dispatch_prompt(ctx, prompt_file),
        task_id=f"v5-{ctx.slug}-consult-{n}",
        model=ctx.model, stdout_only=True, output_file=output_file,
        timeout=600,
    )

    if not ok:
        log("  consultation: Gemini dispatch FAILED")
        return False

    # ── 5. Extract and parse result ───────────────────────────────────
    from pipeline.parsing import _extract_delimiter
    result_text = _extract_delimiter(raw, "===CONSULTATION_START===", "===CONSULTATION_END===")

    if not result_text:
        raw_file = ctx.orch_dir / f"consultation-{n}-raw.md"
        raw_file.write_text(raw, "utf-8")
        log(f"  consultation: No delimiters found — raw saved to {raw_file.name}")
        record_consultation(state, n, None, "parse_failed")
        save_state(ctx, state)
        return False

    result_file = ctx.orch_dir / f"consultation-{n}.md"
    result_file.write_text(result_text, "utf-8")
    log(f"  consultation: Result saved → {result_file.name}")

    parsed = parse_consultation(result_text)
    if not parsed:
        log("  consultation: YAML parse failed — see raw result")
        record_consultation(state, n, None, "parse_failed")
        save_state(ctx, state)
        return True  # Not a dispatch failure, just bad YAML

    # Log key findings
    log(f"    scope: {parsed.scope}")
    log(f"    action: {parsed.action}")
    log(f"    confidence: {parsed.confidence}")
    log(f"    changes: {len(parsed.proposed_changes)}")

    # ── 6. Act on result ──────────────────────────────────────────────
    if parsed.scope == "all_modules":
        queue_path = queue_for_approval(
            parsed, ctx.slug, ctx.track, n,
            consultation_file=result_file,
        )
        record_consultation(state, n, parsed, "queued")
        log(f"  consultation: Queued for human approval → {queue_path.name}")

    elif parsed.action == "rebuild":
        # Patch a copy of the base template for rebuild
        patched_path = ctx.orch_dir / f"consultation-patched-{base_template_path.name}"
        success, applied = apply_template_patch(
            base_template_path, parsed.proposed_changes, patched_path,
        )
        if success and applied > 0:
            record_consultation(state, n, parsed, "applied")
            log(f"  consultation: Patched template ({applied} changes) → {patched_path.name}")
            log("  consultation: Rebuild with:")
            log(f"    .venv/bin/python scripts/build_module_v5.py {ctx.track} {ctx.module_num} --restart-from content")
        else:
            record_consultation(state, n, parsed, "no_match")
            log("  consultation: Patch produced 0 matches — template may have changed")
            log(f"  consultation: Review consultation-{n}.md manually")

    else:
        # action == "fix" — one-off LLM fluke, template is fine
        record_consultation(state, n, parsed, "no_action")
        log("  consultation: One-off LLM issue — no template change needed")

    save_state(ctx, state)
    return True


# ============================================================================
# 4. Pipeline runner
# ============================================================================

PHASE_FUNCTIONS: dict[str, Any] = {
    "research":   phase_research,
    "discover":   phase_discover,
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
    # Log agent configuration
    writer = getattr(ctx, "writer", "gemini")
    review_agent = getattr(ctx, "review_agent", "claude")
    content_model = getattr(ctx, "claude_model_B", CLAUDE_MODEL_CONTENT) if writer == "claude" else ctx.model
    log(f"\nPipeline v5: named phases — {len(PHASES)} phases")
    log(f"  Agents: content={writer} ({content_model}), activities=claude (claude-sonnet-4-6), review={review_agent}")
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

    # --stop-before (used by --preflight-only and others)
    stop_before = getattr(ctx, "stop_before_phase", None)

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
        # Clean stale orchestration artifacts for restarted phases (#969 AC7)
        # Keeps: friction.yaml, state.json, research/discovery files
        _RESTART_KEEP = {"friction.yaml", "state.json", "completion.md",
                         "builder-notes.yaml", "discovery.yaml"}
        _RESTART_KEEP_PREFIXES = ("research-", "discover-")
        if ctx.orch_dir.is_dir():
            removed_orch = 0
            for f in ctx.orch_dir.iterdir():
                if not f.is_file():
                    continue
                if f.name in _RESTART_KEEP:
                    continue
                if f.name.startswith(_RESTART_KEEP_PREFIXES):
                    continue
                if f.name.endswith("-gemini-session.json"):
                    continue
                # Only clean artifacts from restarted phases
                is_content_artifact = any(f.name.startswith(p) for p in
                    ("content-", "validate-", "activities-", "review-", "screen-",
                     "preflight-output", "preflight-prompt"))
                if "content" in remaining and is_content_artifact:
                    f.unlink()
                    removed_orch += 1
            if removed_orch:
                log(f"  --restart-from: cleaned {removed_orch} stale orchestration artifact(s)")
        save_state(ctx, state)
        if "research" in remaining:
            ctx.force_research = True  # type: ignore[attr-defined]
        log(f"  --restart-from {restart_key}: running phases {', '.join(remaining)}")
        for phase_id in remaining:
            if stop_before and phase_id == stop_before:
                log(f"\n  Stopping before {phase_id}")
                return True
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
