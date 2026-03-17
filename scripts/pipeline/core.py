#!/usr/bin/env python3
"""Pipeline core — ModuleContext, logging, preflight, content generation, and shared utilities.

Moved from pipeline_lib.py. A backward-compat stub at scripts/pipeline_lib.py
re-exports everything for existing callers.

Key design decisions:
  - Config tables: delegated to pipeline.config_tables
  - Dispatch: delegated to pipeline.dispatch (Gemini + Claude)
  - log: thread-safe by default (no string hacks)
  - No monkey-patching anywhere
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
# .parent.parent because this file is at scripts/pipeline/core.py
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    PHASES_DIR,
    PRO_MODEL,
    PRO_TRACKS,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
    VENV_PYTHON,
    get_module_paths,
    get_track_config,
    slug_for_num,
)

# ============================================================================
# 3. ModuleContext Dataclass
# ============================================================================

@dataclass
class ModuleContext:
    """All paths, config, state for a module build."""
    track: str
    module_num: int
    slug: str
    mode: str  # "v5" (current) | DEPRECATED: "full", "content-only", "enrich", "e2e", "v3"

    # Paths (populated by preflight)
    paths: dict[str, Path] = field(default_factory=dict)
    orch_dir: Path = field(default=Path("."))

    # Plan data
    plan: dict = field(default_factory=dict)
    word_target: int = 0
    topic_title: str = ""
    content_outline: list[dict] = field(default_factory=list)

    # Config from tables
    skill_name: str = ""
    skill_identity: str = ""
    persona_flavor: str = ""
    immersion_rule: str = ""
    level_constraints: str = ""
    activity_config: dict[str, str] = field(default_factory=dict)
    model: str = PRO_MODEL

    # Track config from batch_gemini_config
    track_config: dict = field(default_factory=dict)

    # State tracking
    state: dict = field(default_factory=dict)
    state_path: Path = field(default=Path("."))

    # Built placeholders (in-memory, no YAML round-trip)
    placeholders: dict[str, str] = field(default_factory=dict)

    # CLI flags
    dry_run: bool = False
    force_phase: str | None = None
    rebuild: bool = False
    claude_review: bool = False


# ============================================================================
# 4. State Helpers (delegated to pipeline.state)
# ============================================================================

from pipeline.state import (
    _now_iso,
    load_state,
)

# ============================================================================
# 5. Logging (thread-safe, no string hacks)
# ============================================================================

_log_lock = threading.Lock()
_log_fh = None


def _init_log(slug: str) -> None:
    """Open a log file in logs/ for this build run."""
    global _log_fh
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"build-{slug}-{ts}.log"
    _log_fh = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — module-level log fd, closed at exit
    _log_fh.write(f"=== pipeline — {slug} — {ts} ===\n")
    print(f"Log: {log_path}", flush=True)


def log(msg: str) -> None:
    """Print to stdout and append to log file (thread-safe)."""
    with _log_lock:
        print(msg, flush=True)
        if _log_fh:
            _log_fh.write(msg + "\n")
            _log_fh.flush()


def mark_phase(ctx: ModuleContext, phase: str, status: str, **extra: Any) -> None:
    """Legacy no-op. v5 uses pipeline.state.mark_complete/mark_failed."""
    return


# ============================================================================
# 1-2. Config Tables & Resolver Functions (delegated to pipeline.config_tables)
# ============================================================================

from pipeline.config_tables import (  # noqa: F401
    ACTIVITY_CONFIGS,
    IMMERSION_RULES,
    LEVEL_CONSTRAINTS,
    TRACK_SKILLS,
    _build_exact_section_titles,
    _get_checkpoint_guidance,
    _get_checkpoint_review_guidance,
    _get_writing_style,
    _get_writing_tone,
    _is_checkpoint_module,
    bilingualify_section_titles,
    get_activity_config,
    get_expansion_method,
    get_h3_word_range,
    get_immersion_rule,
    get_item_minimums_table,
    get_level_constraints,
    get_level_label,
    get_pedagogical_constraints,
    get_structural_rules,
    get_track_skill,
    track_to_level_focus,
)

# ============================================================================
# 6. Dispatch Helpers (delegated to pipeline.dispatch)
# ============================================================================

TMP_DIR = Path(tempfile.gettempdir())
MAX_FIX_ITERATIONS = 3


def run_script(args: list[str], capture: bool = False, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a script via .venv/bin/python with cwd=PROJECT_ROOT."""
    cmd = [VENV_PYTHON, *args]
    return subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=capture,
        text=True, timeout=timeout,
    )


# Backward-compat re-exports from pipeline.dispatch
from pipeline.dispatch import (  # noqa: F401
    dispatch_gemini,
    dispatch_gemini_raw,
    save_gemini_session,
)

# ---------------------------------------------------------------------------
# Pre-dispatch prompt health check
# ---------------------------------------------------------------------------


def check_prompt_health(
    ctx: ModuleContext, prompt_text: str, phase_name: str
) -> list[str]:
    """Validate a filled prompt before dispatching to an LLM.

    Returns a list of issues found. Empty list = healthy prompt.
    Each issue is a string like "WARNING: ..." or "ERROR: ...".
    ERROR items should block dispatch; WARNING items are informational.
    """
    issues: list[str] = []
    track_base = ctx.track.split("-")[0] if ctx.track else ""
    is_core = track_base.lower() in {"a1", "a2", "b1", "b2", "c1", "c2"}

    # 1. Content-phase checks
    if phase_name == "content":
        if "{IMMERSION_RULE}" in prompt_text:
            issues.append("ERROR: IMMERSION_RULE placeholder was not filled")
        elif is_core:
            imm_rule = getattr(ctx, "immersion_rule", "")
            if not imm_rule or len(imm_rule.strip()) < 20:
                issues.append("WARNING: IMMERSION_RULE is empty/trivial — immersion targets will be missed")

        if "{SECTION_BUDGET_TABLE}" in prompt_text:
            issues.append("ERROR: SECTION_BUDGET_TABLE placeholder unfilled — word targets won't be communicated")

        if "{WORD_TARGET}" in prompt_text:
            issues.append("ERROR: WORD_TARGET placeholder unfilled")

    # 3. Activities-phase checks
    if phase_name == "activities" and "{REQUIRED_TYPES}" in prompt_text:
        issues.append("ERROR: REQUIRED_TYPES placeholder unfilled — activity diversity will be random")

    # 4. Universal: detect unfilled placeholders (any {UPPERCASE_THING} remaining)
    unfilled = set(re.findall(r"\{([A-Z][A-Z_]{3,})\}", prompt_text))
    # Filter out known false positives (markdown/code patterns)
    _false_positives = {"JSON", "YAML", "HTML", "UTF8", "VESUM", "PASS", "FAIL",
                        "TRUE", "FALSE", "NULL", "NONE", "TODO", "NOTE", "IMPORTANT"}
    unfilled -= _false_positives
    if unfilled:
        issues.append(
            f"WARNING: {len(unfilled)} unfilled placeholder(s) in {phase_name} prompt: "
            f"{', '.join(sorted(unfilled)[:5])}"
        )

    return issues


def log_prompt_health(issues: list[str], phase_name: str) -> bool:
    """Log prompt health issues. Returns False if any ERROR-level issue found."""
    if not issues:
        return True

    has_error = False
    for issue in issues:
        log(f"  {phase_name}: HEALTH-CHECK {issue}")
        if issue.startswith("ERROR:"):
            has_error = True

    if has_error:
        log(f"  {phase_name}: BLOCKED by prompt health check — fix template/placeholders before dispatch")

    return not has_error


# ============================================================================
# 10. Template & Extraction Helpers
# ============================================================================

def fill_template(
    template: Path, placeholders: dict[str, str], output: Path,
    overrides: dict[str, str] | None = None, strict: bool = False,
) -> bool:
    """Fill a template with placeholders dict (in-memory). Returns True on success."""
    from generate_mdx.fill_template import fill_template as _fill
    from generate_mdx.fill_template import find_unresolved

    if not template.exists():
        log(f"  fill_template FAILED: template not found: {template}")
        return False

    template_text = template.read_text(encoding="utf-8")
    merged = dict(placeholders)
    if overrides:
        merged.update(overrides)

    filled = _fill(template_text, merged)
    unresolved = find_unresolved(filled)
    if unresolved:
        msg = f"Unresolved placeholders ({len(unresolved)}): {', '.join(unresolved)}"
        if strict:
            log(f"  fill_template FAILED: {msg}")
            return False
        else:
            logger.debug("fill_template: %s", msg)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(filled, encoding="utf-8")
    return True


def _gemini_output_path(slug: str, phase: str) -> Path:
    return TMP_DIR / f"gemini-output-{slug}-phase-{phase}.txt"


def _dispatch_prompt(ctx: ModuleContext, prompt_file: Path) -> str:
    """Build the standard dispatch prompt string."""
    content = prompt_file.read_text("utf-8")
    return f"Activate skill {ctx.skill_name}.\n\n{content}"



def _extract_delimited_content(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiter tags, handling code block wrapping.

    Uses the LONGEST match when multiple delimiter pairs exist.
    """
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL,
    )
    matches = pattern.findall(cleaned)
    if not matches:
        return None
    best = max(matches, key=len)
    return best.strip()


# ============================================================================
# 11. Verify Helpers
# ============================================================================

def run_verify(content_path: Path, *,
               skip_review: bool = False) -> tuple[bool, str]:
    """Run verification gate via audit_module.sh. Returns (passed, output)."""
    audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
    cmd = [audit_script]
    if skip_review:
        cmd.append("--skip-review")
    cmd.append(str(content_path))
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output


def write_review_with_hash(review_path: Path, review_text: str,
                           content_path: Path) -> None:
    """Write review file with embedded content hash for staleness detection."""
    content_hash = hashlib.md5(content_path.read_bytes(), usedforsecurity=False).hexdigest()[:12]
    header = f"<!-- content-hash: {content_hash} -->\n"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(header + review_text, "utf-8")


# Prose-only verification (from v2) — ignores review + activity gates
_NON_PROSE_GATES = {"review", "activities", "density", "unique_types", "priority",
                    "engagement", "activity_quality"}
_ACTIVITY_PEDAGOGY_CODES = {
    "MISSING_ADVANCED_ACTIVITY",
    "MISSING_REQUIRED_ACTIVITY",
    "ACTIVITY_TYPE_MISMATCH",
}


def run_verify_prose_only(content_path: Path) -> tuple[bool, str]:
    """Run audit_module.sh --skip-activities and check only prose-relevant gates."""
    audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
    result = subprocess.run(
        [audit_script, "--skip-activities", str(content_path)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")

    track_dir = content_path.parent
    slug = content_path.stem
    bare_slug = slug.split("-", 1)[1] if slug[0].isdigit() and "-" in slug else slug
    status_file = track_dir / "status" / f"{bare_slug}.json"

    if not status_file.exists():
        return False, output + "\nNo status JSON produced by audit"

    status = json.loads(status_file.read_text(encoding="utf-8"))
    gates = status.get("gates", {})

    activity_ped_count = 0
    for code in _ACTIVITY_PEDAGOGY_CODES:
        activity_ped_count += output.count(f"[{code}]")

    failing = []
    for gate_name, gate_data in gates.items():
        if gate_name in _NON_PROSE_GATES:
            continue
        if gate_data.get("status") == "fail":
            msg = gate_data.get("message", "")
            if gate_name == "lesson" and "pedagogy" in msg:
                ped_match = re.search(r"pedagogy:\s*(\d+)\s*violation", msg)
                if ped_match:
                    total_ped = int(ped_match.group(1))
                    if activity_ped_count >= total_ped:
                        continue
                    real_ped = total_ped - activity_ped_count
                    msg = re.sub(r"pedagogy:\s*\d+\s*violations?",
                                 f"pedagogy: {real_ped} violations", msg)
            failing.append(f"{gate_name}: {msg}")

    if failing:
        return False, output + "\nProse-relevant failures:\n" + "\n".join(f"  {f}" for f in failing)
    return True, output


# ============================================================================
# 12. Fix Prompt Helpers
# ============================================================================

def _parse_section(section: Any) -> tuple[str, int]:
    """Parse a content_outline section entry. Returns (title, words)."""
    if isinstance(section, dict):
        title = section.get("section", section.get("title", "Untitled"))
        words = section.get("words", 0)
        return str(title), int(words)
    return str(section), 0



# Fix-prompt helpers moved to pipeline_v5.py — the only consumer.


# ============================================================================
# 14. Review Tier Helpers
# ============================================================================

REVIEW_TIERS_DIR = PROJECT_ROOT / "claude_extensions" / "skills" / "plan-review" / "review-tiers"

TIER_MAP: dict[str, str] = {
    "a1": "tier-1-beginner.md",
    "a2": "tier-1-beginner.md",
    "b1": "tier-2-core.md",
    "b2": "tier-2-core.md",
    "b2-pro": "tier-2-core.md",
    "hist": "tier-3-seminar.md",
    "bio": "tier-3-seminar.md",
    "istorio": "tier-3-seminar.md",
    "lit": "tier-3-seminar.md",
    "c1": "tier-4-advanced.md",
    "c1-pro": "tier-4-advanced.md",
    "c2": "tier-4-advanced.md",
}


def get_tier_guidance(track: str) -> str:
    """Read the appropriate review-tier guidance file for a track."""
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    path = REVIEW_TIERS_DIR / tier_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Tier guidance file not found: {tier_file})"


def _is_tier1(track: str) -> bool:
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    return tier_file == "tier-1-beginner.md"


def _get_scoring_section(track: str) -> str:
    """Return the STEP 4 scoring block with tier-appropriate dimensions."""
    if _is_tier1(track):
        return """### STEP 4: Score 7 Dimensions

| # | Dimension | Weight | Auto-fail |
|---|-----------|--------|-----------|
| 1 | Experience Quality | 1.5 | <7 |
| 2 | Language | 1.1 | <8 |
| 3 | Pedagogy | 1.2 | <7 |
| 4 | Activities | 1.3 | <7 |
| 5 | Beginner Safety | 1.3 | <7 |
| 6 | LLM Fingerprint | 1.0 | <7 |
| 7 | Linguistic Accuracy | 1.5 | <9 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Language x 1.1 + Pedagogy x 1.2 +
          Activities x 1.3 + Beginner_Safety x 1.3 + LLM x 1.0 +
          Linguistic_Accuracy x 1.5) / 8.9
```

**Why 7 dimensions?** A1/A2 modules are short and topic-constrained, so Coherence, Relevance, Educational, Immersion, Richness, and Factual Accuracy are noise at this level — they auto-pass trivially and waste reviewer attention. Focus scoring on what actually differentiates good beginner modules."""
    else:
        return """### STEP 4: Score 13 Dimensions

| # | Dimension | Auto-fail |
|---|-----------|-----------|
| 1 | Experience Quality | <7 |
| 2 | Coherence | <7 |
| 3 | Relevance | <7 |
| 4 | Educational | <7 |
| 5 | Language | <8 |
| 6 | Pedagogy | <7 |
| 7 | Immersion | <6 |
| 8 | Activities | <7 |
| 9 | Richness | <6 |
| 10 | Beginner Safety | <7 |
| 11 | LLM Fingerprint | <7 |
| 12 | Linguistic Accuracy | <9 |
| 13 | Factual Accuracy | <8 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Coherence x 1.0 + Relevance x 1.0 + Educational x 1.2 +
          Language x 1.1 + Pedagogy x 1.2 + Immersion x 1.0 + Activities x 1.3 +
          Richness x 0.9 + Beginner_Safety x 1.3 + LLM x 1.0 + Linguistic_Accuracy x 1.5 +
          Factual_Accuracy x 1.5) / 15.5
```

**Factual Accuracy note:** ALL tracks — verify callout boxes (`[!did-you-know]`, `[!myth-buster]`, `[!culture-note]`, `[!fun-fact]`) for fabricated claims. Seminar tracks — additionally verify against research notes/Key Facts Ledger. Do NOT auto-score 9 for any track."""


def _get_scoring_output_table(track: str) -> str:
    if _is_tier1(track):
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Language | X/10 | <8 | [specific finding] |
| 3 | Pedagogy | X/10 | <7 | [specific finding] |
| 4 | Activities | X/10 | <7 | [specific finding] |
| 5 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 6 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 7 | Linguistic Accuracy | X/10 | <9 | [specific finding] |"""
    else:
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Coherence | X/10 | <7 | [specific finding] |
| 3 | Relevance | X/10 | <7 | [specific finding] |
| 4 | Educational | X/10 | <7 | [specific finding] |
| 5 | Language | X/10 | <8 | [specific finding] |
| 6 | Pedagogy | X/10 | <7 | [specific finding] |
| 7 | Immersion | X/10 | <6 | [actual % vs target] |
| 8 | Activities | X/10 | <7 | [specific finding] |
| 9 | Richness | X/10 | <6 | [specific finding] |
| 10 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 11 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 12 | Linguistic Accuracy | X/10 | <9 | [specific finding] |
| 13 | Factual Accuracy | X/10 | <8 | [specific finding or "N/A — core track"] |"""


def _get_prompt_tier(track: str, module_num: int) -> str:
    """Determine prompt tier based on track and module number.

    Returns: 'beginner', 'core', or 'seminar'.
    """
    track_lower = track.lower()
    # Use canonical SEMINAR_TRACKS/PRO_TRACKS sets from batch_gemini_config
    if track_lower in SEMINAR_TRACKS or track_lower.split("-")[0] in SEMINAR_TRACKS:
        return "seminar"
    if track_lower in PRO_TRACKS:
        return "core"
    base = track.split("-")[0].upper()
    if base == "A1":
        return "beginner"
    if base == "A2" and module_num <= 20:
        return "beginner"
    return "core"


def _get_content_template(track: str, module_num: int,
                          full_build: bool = False, rag: bool = False,
                          slug: str = "") -> str:
    """Return the content prompt filename for the given tier."""
    tier = _get_prompt_tier(track, module_num)
    # Checkpoint modules get dedicated templates
    if slug and _is_checkpoint_module(slug):
        if tier == "beginner":
            return "beginner-checkpoint.md"
        return "core-checkpoint.md"
    if tier == "beginner":
        # Always use RAG template — RAG server is always available.
        # Full-build extracts activities from the output; non-full-build ignores them.
        return "beginner-full-rag.md"
    if tier == "seminar":
        return "content.md"
    return "core-content.md"



def _get_activities_template(track: str, module_num: int,
                             slug: str = "") -> str:
    """Return the activities prompt filename for the given tier."""
    tier = _get_prompt_tier(track, module_num)
    # Checkpoint modules get dedicated activity templates
    if slug and _is_checkpoint_module(slug):
        if tier == "beginner":
            return "beginner-checkpoint-activities.md"
        return "core-checkpoint-activities.md"
    if tier == "beginner":
        return "beginner-activities.md"
    if tier == "seminar":
        return "activities.md"
    return "core-activities.md"


def _read_phase_file(filename: str) -> str:
    path = PHASES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Phase file not found: {filename})"


def _get_ukrainian_topic(ctx: ModuleContext) -> str:
    """Get Ukrainian topic keywords for RAG search. English kills semantic matching."""
    # Use grammar field if available — it's already in Ukrainian
    grammar = ctx.plan.get("grammar", [])
    if grammar:
        return " ".join(grammar[:2])
    # Fall back to title but warn — English titles won't match Ukrainian textbooks well
    return ctx.plan.get("title", ctx.slug).replace("-", " ")


def _get_summary_heading(ctx: ModuleContext) -> str:
    """Get the summary heading from the plan's content_outline, falling back to defaults."""
    outline = ctx.plan.get("content_outline", [])
    for section in outline:
        if isinstance(section, dict):
            name = section.get("section", "")
            if "підсумок" in name.lower() or "summary" in name.lower():
                return name
    # Fallback
    if ctx.track.startswith("a1") and ctx.module_num <= 14:
        return "Підсумок — Summary"
    return "Підсумок"


def _build_learner_state(ctx: ModuleContext) -> str:
    """Build the learner state manifest for this module."""
    try:
        from pipeline.learner_state import build_learner_state, format_learner_state
        state = build_learner_state(ctx.track, ctx.module_num)
        return format_learner_state(state)
    except Exception as e:
        log(f"  learner-state: Skipped — {e}")
        return "(Learner state not available)"


# ============================================================================
# 15. Write Placeholders
# ============================================================================

def build_placeholders(ctx: ModuleContext) -> None:
    """Build placeholders dict and store on ctx (in-memory, no disk YAML)."""
    if ctx.placeholders and not ctx.rebuild and not getattr(ctx, "force_phase", False):
        log("Placeholders: Using existing (in-memory)")
        return

    level_label = get_level_label(ctx.track)
    quick_ref_path = ctx.track_config.get("quick_ref", "")
    placeholders = {
        "TRACK": ctx.track,
        "LEVEL": level_label,
        "SLUG": ctx.slug,
        "TOPIC_TITLE": ctx.topic_title,
        "MODULE_NUM": str(ctx.module_num),
        "PLAN_PATH": str(ctx.paths["plan"]),
        "PLAN_CONTENT": ctx.paths["plan"].read_text(encoding="utf-8") if ctx.paths["plan"].exists() else "",
        "CONTENT_PATH": str(ctx.paths["md"]),
        "ACTIVITIES_PATH": str(ctx.paths["activities"]),
        "VOCAB_PATH": str(ctx.paths["vocabulary"]),
        "RESEARCH_PATH": str(ctx.paths["research"]),
        "REVIEW_PATH": str(ctx.paths["review"]),
        "QUICK_REF_PATH": str(quick_ref_path) if quick_ref_path else "",
        "QUICK_REF_CONTENT": quick_ref_path.read_text(encoding="utf-8") if quick_ref_path and quick_ref_path.exists() else "",
        "SCHEMA_PATH": f"schemas/activities-{ctx.track}.schema.json",
        "WORD_TARGET": str(ctx.word_target),
        "WORD_CEILING": str(int(ctx.word_target * 1.5)),
        "SKILL_IDENTITY": ctx.skill_identity,
        "PERSONA_FLAVOR": ctx.persona_flavor,
        "PERSONA_VOICE": ctx.plan.get("persona", {}).get("voice", ""),
        "PERSONA_ROLE": ctx.plan.get("persona", {}).get("role", ""),
        "IMMERSION_RULE": ctx.immersion_rule,
        "LEVEL_CONSTRAINTS": ctx.level_constraints,
        "PEDAGOGICAL_CONSTRAINTS": get_pedagogical_constraints(ctx.track, ctx.module_num, ctx.plan),
        "DECODABLE_VOCABULARY": "",  # Decodable system removed (#841) — plan vocabulary_hints is source of truth
        "LEARNER_STATE": _build_learner_state(ctx),
        "STRUCTURAL_RULES": get_structural_rules(ctx.track, ctx.module_num),
        "H3_WORD_RANGE": get_h3_word_range(ctx.track, ctx.module_num),
        "EXPANSION_METHOD": get_expansion_method(ctx.track, ctx.module_num),
        "WRITING_TONE_INSTRUCTION": _get_writing_tone(ctx.track, ctx.module_num),
        "WRITING_STYLE": _get_writing_style(ctx),
        "TEXTBOOK_EXAMPLES": _prefetch_textbook_examples(ctx),
        "TEXTBOOK_ACTIVITY_EXAMPLES": _prefetch_textbook_activity_examples(ctx),
        "TEXTBOOK_GRADE": _get_textbook_grade(ctx),
        "TOPIC_KEYWORDS": " ".join(ctx.plan.get("keywords", [])[:3]) or _get_ukrainian_topic(ctx),
        "CHECKPOINT_GUIDANCE": _get_checkpoint_guidance(ctx),
        "CHECKPOINT_REVIEW_GUIDANCE": _get_checkpoint_review_guidance(ctx),
        "EXACT_SECTION_TITLES": _build_exact_section_titles(ctx),
        "INTRO_HOOK": (
            "Why does this matter?" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Чому це важливо? — Why does this matter?" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Чому це важливо?"
        ),
        "SUMMARY_HEADING": _get_summary_heading(ctx),
        "SELF_CHECK_HEADING": (
            "Check yourself:" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Перевірте себе — Check yourself:" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Перевірте себе:"
        ),
        "TIER_EXEMPLAR": "",  # Removed — structural rules work better than exemplars
        "TIER_GUIDANCE": get_tier_guidance(ctx.track),
        "D1_OUTPUT_FORMAT": _read_phase_file("review-output-format.md"),
        "SCORING_SECTION": _get_scoring_section(ctx.track),
        "SCORING_OUTPUT_TABLE": _get_scoring_output_table(ctx.track),
    }

    # Vocabulary hints from plan — injected inline so Gemini sees the actual
    # required/recommended items without needing to read the plan file from disk.
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    if vocab_hints:
        # Normalize: some plans use a bare list instead of {required: [], recommended: []}
        if isinstance(vocab_hints, list):
            vocab_hints = {"required": vocab_hints, "recommended": []}
        vh_lines = ["### Vocabulary from Plan (MANDATORY — include ALL required items)\n"]
        required = vocab_hints.get("required", [])
        recommended = vocab_hints.get("recommended", [])
        if required:
            vh_lines.append("**Required** (MUST appear in vocabulary YAML):")
            for item in required:
                vh_lines.append(f"- {item}")
            vh_lines.append("")
        if recommended:
            vh_lines.append("**Recommended** (use in your content to reach the vocabulary target):")
            for item in recommended:
                vh_lines.append(f"- {item}")
            vh_lines.append("")
        vh_lines.append("These are your TARGET words — teach them all and use them heavily. "
                        "For the rest of the text, use natural, level-appropriate Ukrainian.")
        vh_lines.append("")
        vh_lines.append("**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints "
                        "MUST appear at least once in the module content. Orphaned vocabulary "
                        "(listed but never used in content) is a validation failure.")
        placeholders["VOCAB_HINTS"] = "\n".join(vh_lines)
        placeholders["VOCABULARY_HINTS"] = placeholders["VOCAB_HINTS"]
    else:
        placeholders["VOCAB_HINTS"] = ""
        placeholders["VOCABULARY_HINTS"] = ""

    # Video discovery placeholder
    discovery_path = ctx.orch_dir / "discovery.yaml"
    if discovery_path.exists():
        try:
            from video_discovery import format_discovery_for_template, read_discovery_yaml
            result = read_discovery_yaml(discovery_path)
            placeholders["VIDEO_DISCOVERY"] = format_discovery_for_template(result)
        except Exception:
            placeholders["VIDEO_DISCOVERY"] = ""
    else:
        placeholders["VIDEO_DISCOVERY"] = ""

    # Supplement with YouTube links from research (research may find per-letter
    # videos that channel-based discovery missed)
    research_path = ctx.paths.get("research")
    if research_path and research_path.exists():
        try:
            import re as _re
            research_text = research_path.read_text("utf-8")
            yt_links = _re.findall(
                r'-\s*(.+?)\s*[-—]\s*(https://www\.youtube\.com/watch\?v=[^\s]+)',
                research_text,
            )
            if yt_links:
                lines = ["\n### Research Videos"]
                lines.append("*These videos were found during the research phase. "
                             "Embed each one next to its corresponding letter/topic section "
                             "using a markdown link.*\n")
                for desc, url in yt_links:
                    lines.append(f"- {desc.strip()} — {url}")
                placeholders["VIDEO_DISCOVERY"] += "\n".join(lines)
        except Exception:
            pass

    # Pronunciation videos from plan (alphabet modules)
    pv = ctx.plan.get("pronunciation_videos")
    if pv and isinstance(pv, dict):
        credit = pv.get('credit', 'Anna Ohoiko — Ukrainian Lessons')
        letters = pv.get("letters", {})
        overview = pv.get("overview")
        playlist = pv.get("playlist")

        pv_lines = ["### Pronunciation Videos (from plan — MANDATORY embeds)"]
        pv_lines.append(f"*Credit: {credit}*\n")
        if overview:
            pv_lines.append(f"- **Overview**: [{credit} — Overview]({overview})")
        if playlist:
            pv_lines.append(f"- **Full Playlist**: [{credit} — Playlist]({playlist})")
        if letters:
            pv_lines.append("")
            pv_lines.append("**Each letter below MUST get its video embedded "
                            "in the corresponding H3 section:**\n")
            for letter, url in letters.items():
                pv_lines.append(f"- **Літера {letter}**: [{credit} — {letter}]({url})")
        elif overview:
            pv_lines.append("")
            pv_lines.append("**Embed the overview video in the introduction section "
                            "and reference the playlist for students who want per-letter videos.**")
        placeholders["PRONUNCIATION_VIDEOS"] = "\n".join(pv_lines)
    else:
        placeholders["PRONUNCIATION_VIDEOS"] = ""

    # Tier detection
    tier = _get_prompt_tier(ctx.track, ctx.module_num)

    # Quality dimensions — tier-aware (#844): beginner/core get base dimensions,
    # seminar gets extended dimensions (decolonization, primary sources).
    _qd_file = "_shared-quality-dimensions-seminar.md" if tier == "seminar" else "_shared-quality-dimensions.md"
    placeholders["QUALITY_DIMENSIONS"] = _read_phase_file(_qd_file)

    # Pre-flight instructions (#844) — injected into content prompts.
    # Skipped when --skip-preflight is set on the context.
    if getattr(ctx, "skip_preflight", False):
        placeholders["PREFLIGHT_INSTRUCTIONS"] = ""
    else:
        _preflight_raw = _read_phase_file("_shared-preflight.md")
        placeholders["PREFLIGHT_INSTRUCTIONS"] = _preflight_raw

    # Legacy shared rules — kept as empty string for backward compatibility with
    # templates that still reference {SHARED_CONTENT_RULES} / {SELF_AUDIT_SNIPPET}.
    # New templates (#844) use {QUALITY_DIMENSIONS} + {PREFLIGHT_INSTRUCTIONS} instead.
    rules_tier = "beginner" if tier == "beginner" else "core"
    _shared_rules_file = f"_shared-content-rules-{rules_tier}.md"
    placeholders["SHARED_CONTENT_RULES"] = _read_phase_file(_shared_rules_file)
    placeholders["SHARED_ACTIVITY_RULES"] = _read_phase_file("_shared-activity-rules.md")
    if tier == "beginner":
        placeholders["SELF_AUDIT_SNIPPET"] = ""
    else:
        _self_audit_raw = _read_phase_file("_shared-self-audit.md")
        placeholders["SELF_AUDIT_SNIPPET"] = _self_audit_raw.replace(
            "{CONTENT_PATH}", placeholders.get("CONTENT_PATH", "")
        )

    # Lexical Sandbox removed in #820 — VESUM post-validation replaces it.
    # Placeholder kept as empty string so existing templates don't break.
    placeholders["LEXICAL_SANDBOX"] = ""

    # Folk Micro-Genres (загадки, скоромовки, прислів'я etc.)
    try:
        from folk_injector import build_folk_material
        folk_text = build_folk_material(track=ctx.track, slug=ctx.slug)
        placeholders["FOLK_MATERIAL"] = folk_text
        ctx._folk_material = folk_text
        if folk_text:
            log(f"  folk: Injected folk material ({len(folk_text)} chars)")
    except Exception as e:
        logger.debug("folk_injector not available: %s", e)
        placeholders["FOLK_MATERIAL"] = ""
        ctx._folk_material = ""

    placeholders.update(ctx.activity_config)

    # Populate REQUIRED_TYPES if empty — from plan activity_hints or PRIORITY_TYPES
    if not placeholders.get("REQUIRED_TYPES"):
        plan_hints = ctx.plan.get("activity_hints", [])
        if plan_hints and isinstance(plan_hints, list):
            # Hints can be strings ("quiz") or dicts ({"type": "quiz", "focus": "..."})
            hint_types = []
            for h in plan_hints[:5]:
                if isinstance(h, dict):
                    hint_types.append(h.get("type", str(h)))
                else:
                    hint_types.append(str(h))
            placeholders["REQUIRED_TYPES"] = ", ".join(hint_types)
        elif placeholders.get("PRIORITY_TYPES"):
            # Use first 3 priority types as required minimum variety
            priorities = [t.strip() for t in placeholders["PRIORITY_TYPES"].split(",")]
            placeholders["REQUIRED_TYPES"] = ", ".join(priorities[:3])

    # REQUIRED_TYPES comes from plan activity_hints (source of truth).
    # No hardcoded overrides — if a plan needs bukvar types, they're in activity_hints.

    placeholders["ITEM_MINIMUMS_TABLE"] = get_item_minimums_table(ctx.track, ctx.module_num)
    ctx.placeholders = placeholders
    log(f"Placeholders: Built ({len(placeholders)} keys)")


# ============================================================================
# 16. Archive Helpers (from v2)
# ============================================================================

ARCHIVE_DIR = PROJECT_ROOT / "_archive"
ARCHIVE_WORD_THRESHOLD = 2000
ARCHIVE_GIT_REF = os.environ.get("ARCHIVE_GIT_REF", "944f3524a^")
ARCHIVE_SKIP_TRACKS: set[str] = {"bio", "istorio", "lit"}


def detect_archived_prose(track: str, slug: str) -> tuple[bool, str, Path | None]:
    """Check for restorable archived prose."""
    if track in ARCHIVE_SKIP_TRACKS:
        return False, "", None
    track_archive = ARCHIVE_DIR / track
    if track_archive.is_dir():
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


def restore_from_archive(ctx: ModuleContext, archive_dir: Path | None) -> bool:
    """Restore archived prose (and optionally activities/vocab) to live paths."""
    slug = ctx.slug
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
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
    if not content_path.exists():
        return False
    word_count = len(content_path.read_text(encoding="utf-8").split())
    if word_count < ARCHIVE_WORD_THRESHOLD:
        log(f"  Restore: REJECTED — only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
        content_path.unlink()
        return False
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


def _check_archive_fits_outline(ctx: ModuleContext) -> tuple[bool, list[str], list[str]]:
    """Check if archived prose covers the sections from the current content_outline."""
    archive_dir = getattr(ctx, "archive_dir", None)
    slug = ctx.slug
    if archive_dir is not None:
        src = archive_dir / f"{slug}.md"
        if not src.exists():
            return False, [], []
        content = src.read_text(encoding="utf-8")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return False, [], []
        content = result.stdout
    archive_h2s = {h.strip().lower() for h in re.findall(r"^## (.+)$", content, re.MULTILINE)}
    outline = ctx.content_outline
    if not outline:
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
    return coverage >= 0.7, matched, missing


# ============================================================================
# 17. Phase 2 Content Generation (from v1, used as fallback by Phase B)
# ============================================================================

def _build_section_budget_table(sections: list, word_target: int) -> str:
    """Build a markdown table of section word budgets."""
    rows = ["| Section | Minimum |", "|---------|---------|"]
    for section in sections:
        title, words = _parse_section(section)
        if words <= 0:
            words = word_target // max(len(sections), 1)
        rows.append(f"| {title} | {words}+ |")
    rows.append(f"| **Total** | **{word_target}+ (aim for ~{int(word_target * 1.2)})** |")
    return "\n".join(rows)


def _build_phase2_expansion_prompt(
    ctx: ModuleContext, current_text: str, current_words: int,
    deficit: int, had_truncation: bool = False,
) -> str:
    """Build a prompt telling Gemini to expand thin content to meet word target."""
    sections: list[tuple[str, int]] = []
    current_section = ""
    section_text: list[str] = []
    for line in current_text.split("\n"):
        h2_match = re.match(r'^##\s+(.+)', line)
        if h2_match:
            if current_section and section_text:
                wc = len(" ".join(section_text).split())
                sections.append((current_section, wc))
            current_section = h2_match.group(1)
            section_text = []
        else:
            section_text.append(line)
    if current_section and section_text:
        wc = len(" ".join(section_text).split())
        sections.append((current_section, wc))
    section_report = "\n".join(f"- **{name}**: {wc} words" for name, wc in sections)
    research_path = ctx.paths.get("research", "")
    base_level = ctx.track.split('-')[0].upper() if ctx.track else ''
    # A1/A2: 1.2x overshoot to safely clear minimum. B1+: 1.5x.
    overshoot = int(ctx.word_target * 1.2) if base_level in ('A1', 'A2') or had_truncation else int(ctx.word_target * 1.5)
    return f"""# content: EXPAND — Content is {current_words} words, need {ctx.word_target}+

> **Persona reminder:** You are {ctx.skill_identity}. Write in the voice of {ctx.persona_flavor}. Maintain your voice throughout.

## Problem

Your previous output was **{current_words} words** — below the **{ctx.word_target} word minimum**.
You need to add approximately **{deficit} more words** of substantive content.

### Current section word counts:
{section_report}

## Your Task

Read the current content file at `{ctx.paths["md"]}` and the original prompt at `{ctx.orch_dir / "content-prompt.md"}`.

**Rewrite the ENTIRE module** with expanded content. Every H3 subsection needs:
- Substantive explanatory prose (not just headings and bullet points)
- Example sentences in context
- Callout boxes where appropriate

**DO NOT add filler or padding.** Expand with real pedagogical content only.

## Critical Rules
- Write at least **{overshoot} words**
- Use research file: `{research_path}`
- Immersion: {ctx.immersion_rule}
- Output between `===CONTENT_START===` and `===CONTENT_END===` delimiters

## Output Format

===CONTENT_START===
{{entire rewritten module with dramatically expanded content}}
===CONTENT_END===

===WORD_COUNTS_START===
Section "{{name}}": {{count}} words
...
Total: {{total}} words
===WORD_COUNTS_END===
"""


def _prefetch_sources_for_phase_B(ctx: ModuleContext) -> str:
    """Pre-fetch primary source excerpts from RAG for Phase B content generation.

    For seminar tracks: extracts section names + key terms from plan/meta,
    searches literary RAG, returns formatted excerpts Gemini can cite.
    """
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    if track_key not in SEMINAR_TRACKS:
        return ""

    # Extract search terms from content_outline section names + topic title
    search_terms = []
    topic = ctx.topic_title or ctx.slug.replace("-", " ")
    search_terms.append(topic)
    for section in ctx.content_outline:
        section_name = section.get("section") or section.get("title", "")
        if section_name:
            search_terms.append(section_name)
    # Add vocabulary hints as search terms
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    for term in vocab_hints.get("required", [])[:3]:
        search_terms.append(term)
    # Cap at 5 searches
    search_terms = [t for t in search_terms if t.strip()][:5]
    if not search_terms:
        return ""

    try:
        from rag.query import search_literary
    except ImportError:
        return ""

    results = []
    seen_chunks = set()
    for term in search_terms:
        try:
            hits = search_literary(term, limit=2)
        except Exception:
            continue
        for hit in hits:
            cid = hit.get("chunk_id", "")
            if cid in seen_chunks:
                continue
            seen_chunks.add(cid)
            work = hit.get("work", "unknown")
            year = hit.get("year", "?")
            genre = hit.get("genre", "")
            text = hit.get("text", "")[:300]
            results.append(
                f"**{work}** ({year}, {genre}):\n> {text}"
            )

    if not results:
        return ""

    return "\n\n".join(results[:8])  # Cap at 8 excerpts


def _clean_textbook_text(text: str) -> str:
    """Strip OCR artifacts from textbook text without destroying numbered lists.

    Removes: stray brackets [], excessive blank lines, stray pipe characters.
    Preserves: numbered lists (1. Foo), lettered sub-tasks (А. Б. В.).
    """
    # Remove stray brackets — preserve markdown links [text](url) and images ![alt](url)
    text = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'MDLINK\1MDURL\2MDEND', text)  # protect links
    text = re.sub(r'[\[\]]', '', text)  # strip stray brackets
    text = re.sub(r'MDLINK(.*?)MDURL(.*?)MDEND', r'[\1](\2)', text)  # restore links
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove stray pipe chars at start/end of lines (OCR table artifacts)
    text = re.sub(r'^\|?\s*\|\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def _prefetch_textbook_examples(ctx: ModuleContext) -> str:
    """Pre-fetch textbook/encyclopedia examples from RAG for content generation.

    - A1/A2: searches bukvar (grade 1-2) for letter/syllable exercises
    - B1+ core: searches ukrainska-mova for grammar explanations
    - Seminar (HIST/BIO/ISTORIO/LIT/OES/RUTH): searches textbooks for factual grounding
    Returns formatted examples Gemini can use as reference material.
    """
    base = ctx.track.split("-")[0]
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    is_seminar = track_key in SEMINAR_TRACKS

    # Build search terms from plan keywords and section titles
    search_terms = []
    plan_keywords = ctx.plan.get("keywords", [])
    if plan_keywords:
        search_terms.extend(plan_keywords[:3])
    for section in ctx.content_outline[:3]:
        section_name = section.get("section") or section.get("title", "")
        if section_name:
            # Strip English translations in parentheses or after em-dash
            uk_part = section_name.split("(")[0].strip() if "(" in section_name else section_name
            if "—" in uk_part:
                parts = uk_part.split("—", 1)
                # Pick whichever side has Cyrillic (handles English-first titles)
                def has_cyr(s: str) -> bool:
                    return any("\u0400" <= c <= "\u04ff" for c in s)
                uk_part = parts[0].strip() if has_cyr(parts[0]) else parts[1].strip()
            search_terms.append(uk_part)
    if not search_terms:
        topic = ctx.topic_title or ctx.slug.replace("-", " ")
        search_terms.append(topic)

    search_terms = [t for t in search_terms if t.strip()][:4]
    if not search_terms:
        return ""

    results = []
    seen_chunks = set()

    # --- Seminar tracks: search textbooks (history, literature) ---
    if is_seminar:
        try:
            from rag.query import search_text as _st
        except ImportError:
            _st = None

        # Search textbooks without subject filter — plan keywords naturally match
        # history textbooks for HIST/ISTORIO, literature for LIT/OES/RUTH
        if _st:
            for term in search_terms:
                try:
                    hits = _st(term, limit=3)
                except Exception:
                    continue
                for hit in hits:
                    cid = hit.get("chunk_id", "")
                    if cid in seen_chunks:
                        continue
                    seen_chunks.add(cid)
                    source = hit.get("source", "")
                    section = hit.get("section", "")
                    text = _clean_textbook_text(hit.get("text", "")[:500])
                    results.append(
                        f"**{source}** — {section}:\n```\n{text}\n```"
                    )


        if results:
            header = (
                "## Textbook & Encyclopedia Reference\n\n"
                "These are excerpts from real Ukrainian school textbooks and encyclopedias. "
                "Use them for **factual grounding** — verify dates, names, events, and literary analysis "
                "against these authoritative sources. Do NOT invent historical details or attribute "
                "incorrect quotes to authors.\n\n"
            )
            return header + "\n\n".join(results[:8])
        return ""  # Literary sources still handled by _prefetch_sources_for_phase_B

    # --- A1/A2: bukvar ---
    try:
        from rag.query import search_text
    except ImportError:
        return ""

    if base in ("a1", "a2") and (base != "a1" or ctx.module_num <= 14):
        # M1-M14 (script & first contact): bukvar syllable/letter exercises
        # A2: grade 2 bukvar
        subject = "bukvar"
        grade = 1 if base == "a1" else 2
        header = (
            "## Textbook Reference Examples (from real Ukrainian буквар)\n\n"
            "These are real exercises from Ukrainian 1st-grade primers. "
            "Use them as **inspiration for style and difficulty level** — "
            "notice how they use simple syllable combinations, short words, "
            "and build progressively. Do NOT copy them verbatim, but match their "
            "pedagogical approach and simplicity.\n\n"
        )
    elif base == "a1" and ctx.module_num >= 15:
        # M15+: grammar textbooks (verbs, cases, tenses) — bukvar is irrelevant
        # Higher grades first: imperative mood = Grade 7, not Grade 3
        # No subject filter — some Grade 4 books lack subject metadata
        subject = None
        grade = [7, 6, 5, 4, 3]  # Higher grades first for grammar topics
        header = (
            "## Textbook Reference (from Ukrainian grammar textbooks)\n\n"
            "These are explanations from Ukrainian school grammar textbooks. "
            "Use them as **reference** for grammar rules and examples. "
            "Adapt for adult A1 learners — keep explanations simple "
            "but maintain grammatical accuracy.\n\n"
        )
    else:
        # --- B1+ core tracks: ukrainska-mova grammar ---
        subject = "ukrainska-mova"
        grade = None  # Search all grades — grammar concepts span multiple years
        header = (
            "## Textbook Reference (from real Ukrainian grammar textbooks)\n\n"
            "These are explanations from Ukrainian school grammar textbooks. "
            "Use them as **authoritative reference** for grammar rules, terminology, "
            "and examples. Cross-check your explanations against these. "
            "Adapt for adult learners but keep the grammatical accuracy.\n\n"
        )

    # Normalize grade to a list for iteration
    grade_list = grade if isinstance(grade, list) else ([grade] if grade is not None else [None])

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
                author = hit.get("author", "")
                hit_grade = hit.get("grade", "")
                section = hit.get("section_title", hit.get("section", ""))
                text = _clean_textbook_text(hit.get("text", "")[:500])
                label = f"Grade {hit_grade}, {author}" if author else f"Grade {hit_grade}"
                results.append(
                    f"**{label}** — {section}:\n```\n{text}\n```"
                )

    if not results:
        return ""

    note = (
        "\n\nNOTE: The textbook examples above are provided as INSPIRATION "
        "for the pedagogical approach, NOT as content to copy. For modules M15+, "
        "focus on the communicative patterns, not the letter/syllable exercises.\n"
    )
    return header + "\n\n".join(results[:6]) + note


def _get_textbook_grade(ctx: ModuleContext) -> str:
    """Return the recommended textbook grade range for RAG searches.

    Mapping rationale (CEFR → Ukrainian school grades):
      A1 M1-14 (phonology)    → Grades 1-2 (Большакова, Вашуленко — bukvar)
      A1 M15+  (early grammar) → Grades 3-5 (basic cases, tenses, gender)
      A2                       → Grades 3-5 (elementary grammar, simple texts)
      B1                       → Grades 5-7 (Заболотний, Авраменко — morphology)
      B2                       → Grades 8-9 (register, error correction, complex syntax)
      C1                       → Grades 9-10 (stylistics, complex structures)
      C2                       → Grades 10-11 (mastery, rare forms)
      Seminars (HIST, BIO...) → Grades 9-11 (full advanced range)

    Grade is a HARD FILTER in Qdrant — only chunks tagged with matching
    grade(s) are returned.  Overly wide ranges pull in too-complex material.
    """
    base = ctx.track.split("-")[0]
    if base == "a1" and ctx.module_num <= 14:
        return "1-2"
    elif base == "a1":
        return "3-5"  # was 3-7; grades 6-7 contain morphology beyond A1
    elif base == "a2":
        return "3-5"  # was 3-4; grade 5 adds transitive verbs, cases
    elif base == "b1":
        return "5-7"
    elif base == "b2":
        return "8-9"  # was 7-8; grade 7 overlaps B1
    elif base == "c1":
        return "9-10"
    elif base == "c2":
        return "10-11"
    # Seminars (hist, bio, lit, istorio, oes, ruth) — full advanced range
    return "9-11"


# Imperative verbs that signal exercise blocks (task instructions) in textbooks.
# Grade 1-2 use bare imperatives; grade 3+ use formal/plural imperatives.
_EXERCISE_MARKERS = (
    # Singular (grade 1-4)
    "знайди", "спиши", "визнач", "прочитай", "утвори", "добери",
    "запиши", "виправ", "випиши", "підкресли", "розгадай", "склади",
    "збери", "розглянь", "назви", "відшукай", "поміркуй", "пригадай",
    # Plural formal (grade 5-11)
    "спишіть", "визначте", "утворіть", "доберіть", "запишіть",
    "виправте", "випишіть", "підкресліть", "перепишіть", "розберіть",
    "відредагуйте", "скоригуйте", "установіть", "згрупуйте",
    # Exercise markers
    "вправа", "крок 1",
)

_EXERCISE_MARKER_RE = re.compile(
    r'\b(' + '|'.join(re.escape(m) for m in _EXERCISE_MARKERS) + r')',
    re.IGNORECASE,
)


def _prefetch_textbook_activity_examples(ctx: ModuleContext) -> str:
    """Pre-fetch real textbook exercises (вправи) from RAG as activity inspiration.

    Grade mapping (validated against textbook content analysis):
    - A1 M1-M14 → grade 1-2 bukvar (letters, syllables, basic words)
    - A1 M15+   → grade 2-3 (gender, number, basic parts of speech)
    - A2        → grade 3-4 (cases, verb tenses, adj-noun agreement)
    - B1        → grade 5-7 (morphology, word building, style)
    - B2        → grade 7-8 (syntax, error correction, register)
    - C1+       → grade 9-11 (complex syntax, stylistics)

    Exercise labeling varies by grade:
    - Grade 1: bare imperatives (Знайди, Збери, Утвори) — no "Вправа"
    - Grade 2-4: sequential numbers (70., 195., 430.)
    - Grade 5-7: "Вправа NNN" (Litvinova) or plain numbers (others)
    - Grade 8-11: plain numbers + І./ІІ. sub-levels, А./Б./В. sub-tasks
    """
    try:
        from rag.query import search_text
    except ImportError:
        return ""

    base = ctx.track.split("-")[0]

    # Grade mapping + subject + search focus per level
    # Each entry: (grades, subject, focus_queries)
    if base == "a1" and ctx.module_num <= 14:
        grades = [1, 2]
        subject = "bukvar"
        # Grade 1-2 bukvar: bare imperative tasks, no "Вправа" numbering
        focus_queries = [
            "знайди слово букву склад",
            "збери утвори визнач назви",
        ]
    elif base == "a1" and ctx.module_num >= 15:
        grades = [3, 5, 6, 7]  # Grammar topics taught across grades 3-7
        subject = "ukrainska-mova"
        # Use plan section titles as search terms (topic-specific)
        focus_queries = []
        for section in ctx.content_outline[:3]:
            section_name = section.get("section") or section.get("title", "")
            if section_name:
                uk_part = section_name.split("(")[0].strip()
                focus_queries.append(uk_part)
        if not focus_queries:
            focus_queries = [
                "визнач рід іменників число",
                "добери прикметник спиши",
            ]
    elif base == "a2":
        grades = [3, 4]
        subject = "ukrainska-mova"
        # Grade 3-4: case declension, verb conjugation, agreement
        focus_queries = [
            "відмінок іменника називний родовий",
            "дієслово час особа спиши",
        ]
    elif base == "b1":
        grades = [5, 6, 7]
        subject = "ukrainska-mova"
        focus_queries = [
            "спишіть визначте утворіть слова",
            "суфікс префікс будова слова",
        ]
    elif base == "b2":
        grades = [7, 8]
        subject = "ukrainska-mova"
        focus_queries = [
            "спишіть речення підкресліть граматичні основи",
            "відредагуйте речення виправте помилки",
        ]
    else:  # C1, C2
        grades = [9, 10, 11]
        subject = "ukrainska-mova"
        focus_queries = [
            "складнопідрядне речення підрядне",
            "стилістичні засоби установіть відповідність",
        ]

    # Add topic-specific terms from plan keywords
    search_terms = list(focus_queries)
    plan_keywords = ctx.plan.get("keywords", [])
    # Grade 1-2: no "вправа" prefix; grade 3+: add it for better relevance
    prefix = "" if base == "a1" and ctx.module_num <= 14 else "вправа "
    for kw in plan_keywords[:2]:
        search_terms.append(f"{prefix}{kw}")

    results: list[str] = []
    seen_chunks: set[str] = set()

    grade_list = grades if grades is not None else [None]
    for term in search_terms:
        if len(results) >= 5:
            break
        for grade in grade_list:
            if len(results) >= 5:
                break
            try:
                hits = search_text(term, grade=grade, subject=subject, limit=2)
            except Exception:
                continue
            for hit in hits:
                cid = hit.get("chunk_id", "")
                if cid in seen_chunks:
                    continue
                seen_chunks.add(cid)
                text = hit.get("text", "")[:600]
                # Filter: must contain exercise instruction verbs (word boundary)
                if not _EXERCISE_MARKER_RE.search(text):
                    continue
                author = hit.get("author", "")
                hit_grade = hit.get("grade", "")
                section = hit.get("section_title", hit.get("section", ""))
                label = f"Grade {hit_grade}, {author}" if author else f"Grade {hit_grade}"
                results.append(
                    f"**{label}** — {section}:\n```\n{text}\n```"
                )

    if not results:
        return ""

    translate_note = (
        " Since your students are English-speaking adults, **translate exercise instructions "
        "to English** while keeping Ukrainian content words. Adapt the pedagogical approach "
        "(progressive difficulty, real-world context) but not the language of instruction."
        if base in ("a1", "a2") else ""
    )

    return (
        f"### Real Textbook Exercises (вправи) — Pedagogical Inspiration\n\n"
        f"These are real exercises from Ukrainian school textbooks{' (grade ' + '/'.join(str(g) for g in grades) + ')' if grades else ''}. "
        f"Study their **pedagogical patterns** — how they build progressively, "
        f"use familiar vocabulary, and test specific skills.{translate_note}\n\n"
        + "\n\n".join(results[:5])
    )


def phase_2_content(ctx: ModuleContext) -> bool:
    """content: Content (whole-module, single Gemini call)."""
    sections = ctx.content_outline
    if not sections:
        log("  content: FAILED — no content_outline in plan")
        return False
    # Ensure bilingual section titles for early A1 (idempotent)
    sections = bilingualify_section_titles(sections, ctx.track, ctx.module_num)

    num_sections = len(sections)
    # Read engagement minimum from audit config (source of truth)
    try:
        from audit.config import LEVEL_CONFIG
        _base = ctx.track.split('-')[0].upper() if ctx.track else 'A1'
        _cfg_engagement = LEVEL_CONFIG.get(_base, {}).get('min_engagement', 3)
    except Exception:
        _cfg_engagement = 3
    engagement_min = _cfg_engagement
    example_min = 8
    base_level = ctx.track.split('-')[0].upper() if ctx.track else ''
    overshoot = int(ctx.word_target * 1.2) if base_level in ('A1', 'A2') else int(ctx.word_target * 1.5)

    log(f"  content: Whole-module generation ({num_sections} sections, target: {ctx.word_target}w, overshoot: {overshoot}w)")

    # Tier-based content prompt dispatch
    content_template_name = _get_content_template(
        ctx.track, ctx.module_num,
        full_build=getattr(ctx, "full_build", False),
        rag=getattr(ctx, "rag", False),
        slug=ctx.slug,
    )
    template = PHASES_DIR / content_template_name
    # Check for consultation-patched template (from --consult)
    patched = ctx.orch_dir / f"consultation-patched-{content_template_name}"
    if patched.exists():
        template = patched
        log(f"  content: Using consultation-patched template: {patched.name}")
    elif not template.exists():
        # Fallback to monolithic prompt
        template = PHASES_DIR / "content.md"
        log(f"  content: Tier template {content_template_name} not found, falling back to content.md")
    else:
        log(f"  content: Using tier template: {content_template_name}")
    prompt_file = ctx.orch_dir / "content-prompt.md"

    word_target_tokens = ctx.word_target * 2 // 1000
    primary_sources = _prefetch_sources_for_phase_B(ctx)

    # Fix 12: Extract research-identified errors and surface them to content prompt
    research_errors = ""
    _research_path = ctx.paths.get("research")
    if _research_path and _research_path.exists():
        try:
            _research_text = _research_path.read_text("utf-8")
            _error_lines: list[str] = []
            _in_error_section = False
            for _rline in _research_text.split("\n"):
                _lower = _rline.lower()
                if any(kw in _lower for kw in ["common errors:", "помилки", "common mistakes:",
                                                 "типові помилки", "frequent errors"]):
                    _in_error_section = True
                    _error_lines.append(_rline)
                elif _in_error_section:
                    if _rline.startswith("#"):
                        # Next heading — stop collecting
                        break  # New heading ends the section
                    else:
                        _error_lines.append(_rline)
            if len(_error_lines) > 1:
                research_errors = "\n".join(_error_lines).strip()
                log(f"  content: Extracted {len(_error_lines)-1} research error line(s) for content prompt")
        except Exception:
            pass

    overrides = {
        "OVERSHOOT_TARGET": str(overshoot),
        "ENGAGEMENT_MIN": str(engagement_min),
        "EXAMPLE_MIN": str(example_min),
        "SECTION_BUDGET_TABLE": _build_section_budget_table(sections, ctx.word_target),
        "WORD_TARGET_TOKENS": str(word_target_tokens),
        "PRIMARY_SOURCE_EXCERPTS": primary_sources or "(No primary source excerpts available from RAG)",
        "RESEARCH_ERRORS": (
            f"RESEARCH-IDENTIFIED ERRORS (avoid these in content):\n{research_errors}"
            if research_errors else ""
        ),
        "FOLK_MATERIAL": getattr(ctx, "_folk_material", ""),
    }
    if not fill_template(template, ctx.placeholders, prompt_file, overrides=overrides):
        return False

    # Pre-dispatch health check: catch template/placeholder bugs before wasting a Gemini call
    prompt_text = prompt_file.read_text("utf-8")
    health_issues = check_prompt_health(ctx, prompt_text, "content")
    if not log_prompt_health(health_issues, "Phase 2"):
        return False

    # Pre-content gate: Deterministic Russicism scan on plan vocabulary
    # (LLM-based contextual Russicism detection is now in the feasibility preflight check)
    try:
        from pipeline.semantic_russianisms import scan_plan_for_russianisms
        plan_path = ctx.paths.get("plan")
        if plan_path and plan_path.exists():
            vocab_findings = scan_plan_for_russianisms(plan_path)
            if vocab_findings:
                log(f"  pre-content: SEMANTIC RUSSICISM — {len(vocab_findings)} false friend(s) in vocabulary_hints")
                for f in vocab_findings:
                    log(f"    ❌ '{f['word']}' used as '{f['meaning_found']}' "
                        f"(Ukrainian meaning: {f['ukrainian_meaning']})")
                log("  pre-content: Fix plan vocabulary_hints manually, then re-run")
                return False
    except Exception as e:
        log(f"  pre-content: Russicism scan skipped — {e}")

    # Pre-content gate: Research quality assessment (informational)
    try:
        rp = ctx.paths.get("research")
        if rp and rp.exists():
            from research_quality import assess_research_compat
            rq = assess_research_compat(rp, ctx.track, ctx.paths.get("md"))
            if rq:
                score = rq.get("score")
                quality = rq.get("quality", "unknown")
                log(f"  pre-content: Research quality: {quality} ({score}/10)" if score else
                    f"  pre-content: Research quality: {quality}")
    except Exception as e:
        log(f"  pre-content: Research quality check skipped — {e}")

    # Prompt preflight: feasibility (writer self-check) + coherence (reviewer) in parallel
    if not getattr(ctx, "skip_prompt_preflight", False):
        try:
            from pipeline.prompt_preflight import apply_preflight_fixes, run_prompt_preflight

            # Feasibility = writer's self-check (same agent that builds content)
            # Coherence = reviewer (opposite of writer)
            # Both use simple signature: (prompt_text: str) -> tuple[bool, str]
            writer = getattr(ctx, "writer", "gemini")
            coherence_model = getattr(ctx, "coherence_model", None)

            if writer == "claude":
                from pipeline.prompt_preflight import _dispatch_claude_simple, _dispatch_gemini_simple
                _feasibility_dispatch = _dispatch_claude_simple
                # Reviewer = Gemini
                _coherence_dispatch = _dispatch_gemini_simple
            else:
                from pipeline.prompt_preflight import _dispatch_gemini_simple
                # Writer = Gemini (default)
                _feasibility_dispatch = _dispatch_gemini_simple
                # Reviewer = Claude (default)
                _coherence_dispatch = None  # uses _dispatch_claude_simple in run_prompt_preflight

            preflight = run_prompt_preflight(
                prompt_file, ctx.track, ctx.module_num, ctx.orch_dir,
                dispatch_fn=_feasibility_dispatch,
                coherence_dispatch_fn=_coherence_dispatch,
                plan_path=ctx.paths.get("plan"),
                coherence_model=coherence_model,
            )

            # Helper to persist preflight state before any early return
            def _save_preflight_state(auto_fixed: bool = False) -> None:
                feas_status = preflight.feasibility.status
                coh_status = preflight.coherence.status if preflight.coherence else "SKIPPED"
                ctx.state.setdefault("phases", {}).setdefault("content", {})["prompt_preflight"] = {
                    "status": preflight.status,
                    "feasibility_status": feas_status,
                    "coherence_status": coh_status,
                    "issues": len(preflight.issues),
                    "high": len(preflight.high_issues),
                    "auto_fixed": auto_fixed,
                }

            # Coherence HIGH issues → immediate failure (human must fix)
            if preflight.coherence_high_issues:
                log(f"  preflight: BLOCKED — {len(preflight.coherence_high_issues)} "
                    "coherence HIGH issue(s) (plan-prompt misalignment)")
                for ci in preflight.coherence_high_issues:
                    log(f"    → {ci.problem[:150]}")
                log("  preflight: Fix the template or plan, then re-run")
                _save_preflight_state()
                return False

            # Feasibility HIGH issues → try auto-fix
            if preflight.feasibility_high_issues:
                log(f"  preflight: WARNING — {len(preflight.feasibility_high_issues)} "
                    "feasibility HIGH issue(s)")
                for hi in preflight.feasibility_high_issues:
                    log(f"    → {hi.problem[:150]}")
                    if hi.suggested_fix:
                        log(f"      FIX: {hi.suggested_fix[:150]}")

                # Split issues by type
                russicism_issues = [i for i in preflight.feasibility_high_issues
                                    if i.issue_type == "RUSSICISM"]
                prompt_issues = [i for i in preflight.feasibility_high_issues
                                 if i.issue_type != "RUSSICISM"]

                auto_fixed = False

                # Fix Russianisms in the plan (not the prompt)
                if russicism_issues:
                    plan_path = ctx.paths.get("plan")
                    if plan_path and plan_path.exists():
                        try:
                            from plan_autofix import fix_russianisms_in_plan
                            issue_dicts = [{"issue_type": i.issue_type, "problem": i.problem,
                                            "suggested_fix": i.suggested_fix} for i in russicism_issues]
                            n_fixes, changes = fix_russianisms_in_plan(plan_path, issue_dicts)
                            if n_fixes > 0:
                                log(f"  preflight: Fixed {n_fixes} Russicism(s) in plan")
                                for c in changes:
                                    log(f"    ✅ {c}")
                                auto_fixed = True
                            else:
                                log("  preflight: BLOCKED — Russicism(s) found but auto-fix could not resolve them")
                                log("  preflight: Fix plan vocabulary_hints manually, then re-run")
                                _save_preflight_state()
                                return False
                        except Exception as e:
                            log(f"  preflight: Russicism auto-fix failed — {e}")
                            _save_preflight_state()
                            return False

                # Fix prompt contradictions (existing pattern-based fix)
                if prompt_issues:
                    fixed_prompt_path = apply_preflight_fixes(
                        prompt_file, prompt_issues, ctx.orch_dir,
                    )
                    if fixed_prompt_path:
                        log(f"  preflight: Auto-fixed prompt saved → {fixed_prompt_path.name}")
                        prompt_file = fixed_prompt_path
                        auto_fixed = True
                    else:
                        log("  preflight: BLOCKED — prompt issues but auto-fix failed")
                        log("  preflight: Fix the template or pipeline code, then re-run")
                        _save_preflight_state()
                        return False

            _save_preflight_state(auto_fixed=auto_fixed if preflight.feasibility_high_issues else False)
        except Exception as e:
            log(f"  preflight: Skipped — {e}")

    if getattr(ctx, "preflight_only", False):
        log("  content: PREFLIGHT-ONLY — stopping before content dispatch")
        log(f"  content: Prompt ready at {prompt_file}")
        return True

    if ctx.dry_run:
        log("  content: DRY-RUN — would dispatch whole-module content generation")
        return True

    MAX_P2_ATTEMPTS = 3
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    last_friction = None
    _dispatch_fn = getattr(ctx, "content_dispatch_fn", None) or dispatch_gemini

    for attempt in range(1, MAX_P2_ATTEMPTS + 1):
        attempt_suffix = "" if attempt == 1 else f"-r{attempt}"
        task_suffix = "" if attempt == 1 else f"-r{attempt}"

        if attempt > 1 and content_path.exists():
            current_text = content_path.read_text(encoding="utf-8")
            current_words = len(current_text.split())
            # Skip expand if content already meets or exceeds word target
            if current_words >= ctx.word_target:
                log(f"  content: word count {current_words} >= target {ctx.word_target}, skipping expand")
                return True
            deficit = ctx.word_target - current_words
            had_truncation = last_friction and "TOKEN_LIMIT_TRUNCATION" in last_friction
            if had_truncation:
                log(f"  content: Adjusting expansion target to {ctx.word_target}w (1.0x) due to previous truncation")
            expand_prompt = _build_phase2_expansion_prompt(
                ctx, current_text, current_words, deficit, had_truncation
            )
            expand_prompt_file = ctx.orch_dir / f"content-expand-{attempt}.md"
            expand_prompt_file.write_text(expand_prompt, encoding="utf-8")
            dispatch_file = expand_prompt_file
            log(f"  content: Retry {attempt}/{MAX_P2_ATTEMPTS} — expanding {current_words}w → {ctx.word_target}w target")
        else:
            dispatch_file = prompt_file

        # Safety check: save the final prompt Gemini will see
        final_prompt_path = ctx.orch_dir / "content-prompt-final.md"
        final_prompt_path.write_text(dispatch_file.read_text("utf-8"), "utf-8")
        log(f"  content: Final prompt saved → {final_prompt_path.name} (inspect before/during build)")

        output_file = _gemini_output_path(ctx.slug, f"2{attempt_suffix}")
        ok, _ = _dispatch_fn(
            _dispatch_prompt(ctx, dispatch_file),
            task_id=f"yw-{ctx.slug}-p2{task_suffix}",
            model=ctx.model, stdout_only=True, output_file=output_file,
            allow_write=True, timeout=1200,
        )
        if not ok:
            log(f"  content: Dispatch failed (attempt {attempt})")
            continue

        content_text = None
        if output_file.exists():
            raw = output_file.read_text(encoding="utf-8")

            # Pre-flight check (#844): if agent output contains a FAIL preflight,
            # save the report and halt — do not extract content.
            preflight_text = _extract_delimited_content(raw, "===PREFLIGHT_START===", "===PREFLIGHT_END===")
            if preflight_text:
                preflight_file = ctx.orch_dir / "preflight-report.md"
                preflight_file.write_text(preflight_text, encoding="utf-8")
                preflight_lower = preflight_text.lower()
                preflight_failed = "status: fail" in preflight_lower or "status:fail" in preflight_lower
                if preflight_failed:
                    log("  content: PRE-FLIGHT FAILED — agent halted before generating content")
                    log(f"  content: Report saved → {preflight_file.name}")
                    return False
                else:
                    log("  content: Pre-flight PASSED → proceeding with content extraction")

            content_text = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")
            friction = _extract_delimited_content(raw, "===FRICTION_START===", "===FRICTION_END===")
            if friction:
                friction_file = ctx.orch_dir / f"content-friction-{attempt}.md"
                friction_file.write_text(friction, encoding="utf-8")
                log(f"  content: Friction report saved → {friction_file.name}")
                is_real_truncation = (
                    "TOKEN_LIMIT_TRUNCATION" in friction
                    and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
                )
                if is_real_truncation:
                    log("  content: ⚠ Gemini reported token limit truncation")
                last_friction = friction if is_real_truncation else last_friction

            # Extract builder notes
            builder_notes = _extract_delimited_content(raw, "===BUILDER_NOTES_START===", "===BUILDER_NOTES_END===")
            if builder_notes:
                notes_file = ctx.orch_dir / "builder-notes.yaml"
                notes_file.write_text(builder_notes, encoding="utf-8")
                log(f"  content: Builder notes saved → {notes_file.name}")

            # Extract activity plans (generated alongside content for Phase 2→activities handoff)
            activity_plans = _extract_delimited_content(raw, "===ACTIVITY_PLANS_START===", "===ACTIVITY_PLANS_END===")
            if activity_plans:
                plans_path = ctx.paths.get("activities")
                if plans_path:
                    plans_file = plans_path.parent / f"{ctx.slug}-plans.yaml"
                    plans_file.parent.mkdir(parents=True, exist_ok=True)
                    plans_file.write_text(activity_plans, encoding="utf-8")
                    (ctx.orch_dir / "activity-plans.yaml").write_text(activity_plans, "utf-8")
                    log(f"  content: Activity plans extracted → {plans_file.name}")

            # Extract self-audit result if Gemini ran audit in-session
            self_audit = _extract_delimited_content(raw, "===SELF_AUDIT_START===", "===SELF_AUDIT_END===")
            if self_audit:
                sa_file = ctx.orch_dir / f"self-audit-output-{attempt}.md"
                sa_file.write_text(self_audit, encoding="utf-8")
                sa_passed = "status: PASS" in self_audit or "status:PASS" in self_audit
                log(f"  content: Self-audit {'PASSED' if sa_passed else 'FAILED'} → {sa_file.name}")
                if sa_passed:
                    ctx._self_audited = True  # type: ignore[attr-defined]

        if not content_text:
            # Fallback: Gemini may have written directly to CONTENT_PATH via allow_write
            if content_path.exists() and content_path.stat().st_size > 100:
                content_text = content_path.read_text(encoding="utf-8")
                log(f"  content: No delimiters, but Gemini wrote {content_path.name} directly ({len(content_text.split())}w)")
            else:
                log(f"  content: No delimited content extracted (attempt {attempt})")
                continue

        content_path.write_text(content_text, encoding="utf-8")
        # Save extracted content + session to orchestration dir for traceability
        (ctx.orch_dir / f"content-output-{attempt}.md").write_text(content_text, encoding="utf-8")
        save_gemini_session(ctx.orch_dir, label=f"content-attempt-{attempt}")
        total_words = len(content_text.split())
        pct = total_words * 100 // max(ctx.word_target, 1)
        log(f"  content: {total_words} words written ({pct}% of {ctx.word_target} target)")

        # Full-build mode: extract activities + vocabulary from same response
        if getattr(ctx, "full_build", False) and raw:
            for path_key, start, end, orch_name, label in (
                ("activities", "===ACTIVITIES_START===", "===ACTIVITIES_END===",
                 "activities-output.yaml", "Activities"),
                ("vocabulary", "===VOCABULARY_START===", "===VOCABULARY_END===",
                 "activities-output-vocabulary.yaml", "Vocabulary"),
            ):
                text = _extract_delimited_content(raw, start, end)
                target = ctx.paths.get(path_key) if text else None
                if target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8")
                    (ctx.orch_dir / orch_name).write_text(text, "utf-8")
                    log(f"  content: {label} extracted from full-build → {target.name}")

        if total_words >= ctx.word_target * 0.75:
            return True
        log(f"  content: Too thin — {total_words}w vs {ctx.word_target}w target (attempt {attempt})")

    log(f"  content: FAIL — exhausted {MAX_P2_ATTEMPTS} attempts, content still under 50% of target")
    return False


# phase_B_content removed — logic inlined into pipeline_v5.phase_content


# ============================================================================
# 19. Preflight
# ============================================================================

def preflight_v2(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan, detect archive. Returns ModuleContext."""
    track, num = args.track, args.num
    slug = slug_for_num(track, num)
    log(f"Module: {track} #{num} → {slug}")

    paths = get_module_paths(track, slug)
    orch_dir = paths["orchestration"]
    for d in [orch_dir, paths["md"].parent,
              paths["activities"].parent, paths["vocabulary"].parent,
              paths["review"].parent, paths["research"].parent,
              paths["status"].parent]:
        d.mkdir(parents=True, exist_ok=True)

    plan_path = paths["plan"]
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found: {plan_path}")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    skill_name, skill_identity, persona_flavor = get_track_skill(track, num)
    immersion_rule = get_immersion_rule(track, num)
    level_constraints = get_level_constraints(track, plan)
    activity_config = get_activity_config(track, num)
    track_config = get_track_config(track)

    # config.py is the source of truth for word targets
    try:
        from audit.config import get_word_target as _get_wt
        level_code, module_focus = track_to_level_focus(track)
        word_target = _get_wt(level_code, num, module_focus)
    except Exception:
        word_target = plan.get("word_target", 0)
    topic_title = plan.get("title", slug.replace("-", " ").title())
    content_outline = plan.get("content_outline", [])

    ctx = ModuleContext(
        track=track, module_num=num, slug=slug, mode="e2e",
        paths=paths, orch_dir=orch_dir,
        plan=plan,
        word_target=word_target, topic_title=topic_title,
        content_outline=content_outline,
        skill_name=skill_name, skill_identity=skill_identity,
        persona_flavor=persona_flavor,
        immersion_rule=immersion_rule, level_constraints=level_constraints,
        activity_config=activity_config,
        model=track_config.get("model", PRO_MODEL),
        track_config=track_config,
        dry_run=getattr(args, "dry_run", False),
        force_phase=getattr(args, "force_phase", None),
        rebuild=getattr(args, "rebuild", False),
    )

    ctx.state = load_state(ctx)
    ctx.state["mode"] = "e2e"

    from pipeline.state import init_state_lock
    init_state_lock(ctx)

    # v5 handles --rebuild artifact cleanup in build_module_v5.py;
    # log state status for observability
    is_dry = getattr(args, "dry_run", False)
    if getattr(args, "rebuild", False):
        if is_dry:
            log("State: RESET (--rebuild) — DRY-RUN, no artifacts deleted")
        else:
            log("State: RESET (--rebuild)")
    else:
        restart_from = getattr(args, "restart_from", None)
        if restart_from:
            log(f"State: Restarting from {restart_from}")
        elif ctx.state.get("phases"):
            completed = [p for p, v in ctx.state["phases"].items() if v.get("status") == "complete"]
            log(f"State: Loaded — phases complete: {', '.join(completed) or 'none'}")
        else:
            log("State: Fresh")

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    if is_seminar:
        is_archived, archive_source, archive_dir = detect_archived_prose(ctx.track, ctx.slug)
    else:
        is_archived, archive_source, archive_dir = False, "", None

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


# ============================================================================
# 21. Completion Reports
# ============================================================================

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
    # Check for plan auto-fix changelog
    plan_fix_lines = ""
    plan_path = ctx.paths.get("plan")
    if plan_path and plan_path.exists():
        try:
            plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
            if isinstance(plan_data, dict) and plan_data.get("plan_fixes"):
                fixes = plan_data["plan_fixes"]
                if isinstance(fixes, list) and fixes:
                    latest = fixes[-1]
                    changes = latest.get("changes", [])
                    plan_fix_lines = f"\n          Plan fixes: v{latest.get('version', '?')} — {len(changes)} change(s)"
        except Exception:
            pass

    report = textwrap.dedent(f"""\
        {verdict}: pipeline {ctx.track} {ctx.module_num}

          Module:   {ctx.slug}
          Track:    {ctx.track}
          Mode:     {ctx.mode}
          Words:    {word_count} (target: {ctx.word_target})
          Sections: {sections_done}/{sections_total}
          Archive:  {'yes — ' + getattr(ctx, 'archive_source', '') if is_archived else 'no'}
          Verdict:  {verdict}
          Date:     {_now_iso()}{plan_fix_lines}
    """)
    completion_file = ctx.orch_dir / "completion.md"
    completion_file.write_text(report, encoding="utf-8")
    log(f"\nCompletion report → {completion_file}")


# ============================================================================
# 22. Validation Helpers
# ============================================================================

def _validate_activities_yaml(path: Path) -> bool:
    """Check if an activities YAML file passes schema validation."""
    try:
        from audit.checks.yaml_schema_validation import validate_activity_yaml_file
        valid, errors = validate_activity_yaml_file(path)
        if not valid:
            for e in errors[:3]:
                err_str = e.replace('\n', ' ')
                if len(err_str) > 200:
                    err_str = err_str[:197] + "..."
                log(f"    Schema error: {err_str}")
        return valid
    except Exception as e:
        log(f"    Schema validation error: {e}")
        return False
