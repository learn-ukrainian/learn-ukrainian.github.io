"""Prompt preflight — split feasibility + coherence checks before content generation.

**Feasibility** (Gemini Flash, writer self-check): Can the writer execute these
instructions without hitting contradictions or impossible targets?

**Coherence** (Claude Sonnet, reviewer check): Does the rendered prompt actually
implement the plan YAML? Are all plan sections, objectives, and vocabulary
represented?

Both checks run in parallel. Results merge into CombinedPreflightResult with the
same .high_issues / .status / .issues interface as the old PreflightResult.

Auto-fix applies ONLY to feasibility issues. Coherence HIGH issues cause an
immediate pipeline failure (human must fix the template or plan).
"""

from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pipeline.core import log

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class PreflightIssue:
    """A single issue found during prompt preflight."""
    issue_type: str  # CONTRADICTION | MISSING_INSTRUCTION | IMPOSSIBLE_TARGET | UNCLEAR
    location: str  # where in the prompt
    problem: str  # what's wrong
    suggested_fix: str  # how to fix it
    severity: str  # HIGH | MEDIUM | LOW
    source: str = "unknown"  # "feasibility" | "coherence"


@dataclass
class PreflightResult:
    """Result of a single preflight check (feasibility OR coherence)."""
    status: str  # PASS | ISSUES_FOUND | DISPATCH_ERROR | PARSE_ERROR
    issues: list[PreflightIssue] = field(default_factory=list)
    raw_output: str = ""

    @property
    def high_issues(self) -> list[PreflightIssue]:
        return [i for i in self.issues if i.severity == "HIGH"]


@dataclass
class CombinedPreflightResult:
    """Merged result from feasibility + coherence checks.

    Provides the same interface as PreflightResult for backward compatibility.
    """
    feasibility: PreflightResult
    coherence: PreflightResult | None  # None when plan unavailable (skipped)

    @property
    def status(self) -> str:
        statuses = [self.feasibility.status]
        if self.coherence is not None:
            statuses.append(self.coherence.status)
        if any(s == "ISSUES_FOUND" for s in statuses):
            return "ISSUES_FOUND"
        if all(s == "PASS" for s in statuses):
            return "PASS"
        # Propagate the worst non-PASS status (errors > issues > pass)
        _ERROR_STATUSES = {"DISPATCH_ERROR", "PARSE_ERROR"}
        for s in statuses:
            if s in _ERROR_STATUSES:
                return s
        return statuses[0]

    @property
    def issues(self) -> list[PreflightIssue]:
        result = list(self.feasibility.issues)
        if self.coherence is not None:
            result.extend(self.coherence.issues)
        return result

    @property
    def high_issues(self) -> list[PreflightIssue]:
        return [i for i in self.issues if i.severity == "HIGH"]

    @property
    def feasibility_high_issues(self) -> list[PreflightIssue]:
        return [i for i in self.feasibility.issues if i.severity == "HIGH"]

    @property
    def coherence_high_issues(self) -> list[PreflightIssue]:
        if self.coherence is None:
            return []
        return [i for i in self.coherence.issues if i.severity == "HIGH"]

    @property
    def raw_output(self) -> str:
        parts = [self.feasibility.raw_output]
        if self.coherence is not None:
            parts.append(self.coherence.raw_output)
        return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Audit context builder
# ---------------------------------------------------------------------------


def build_audit_context(track: str, module_num: int) -> str:
    """Build a summary of audit gates and thresholds for this level.

    Reads directly from audit/config.py — single source of truth.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from audit.config import GRAMMAR_CONSTRAINTS, LEVEL_CONFIG
    except ImportError:
        return "(audit config not available)"

    base = track.split("-")[0].upper()
    cfg = LEVEL_CONFIG.get(base, {})
    grammar = GRAMMAR_CONSTRAINTS.get(base, {})

    lines = [
        "## Audit Gates (your content will be checked against these)",
        "",
        f"Level: {base}",
        f"Word target: {cfg.get('target_words', '?')}",
        f"Word ceiling: ~{int(cfg.get('target_words', 0) * 1.5)} (exceeding = FAIL)",
        f"Min activities: {cfg.get('min_activities', '?')}",
        f"Min engagement boxes: {cfg.get('min_engagement', '?')}",
        f"Min activity types: {cfg.get('min_types_unique', '?')}",
        "",
        "### Immersion",
        "Target range: defined in the prompt's Immersion Target section (varies by module).",
        "Tables count ZERO for immersion — only blockquotes, bulleted lists, and pattern boxes count.",
        "",
        "### Grammar constraints",
        f"Max words per Ukrainian sentence: {grammar.get('max_words_per_sentence', '?')}",
        f"Participles allowed: {grammar.get('participles', '?')}",
        f"Max clauses: {grammar.get('max_clauses', '?')}",
        "",
        "### Structure",
        "MUST have a Summary/Підсумок section (structure gate FAILS without it).",
        "",
        "### Pedagogy",
        "Sentences exceeding word limit = COMPLEXITY violation.",
        "Participles before B1 = GRAMMAR violation.",
        "Euphony (у/в alternation) errors are flagged.",
    ]
    return "\n".join(lines)


def build_dimension_context(track: str, module_num: int) -> str:
    """Build a summary of scoring dimensions for this tier."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from pipeline.core import _get_prompt_tier
    except ImportError:
        return "(tier config not available)"

    tier = _get_prompt_tier(track, module_num)

    if tier == "beginner":
        return """## Scoring Dimensions (7 — Beginner Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — no Russianisms, correct Ukrainian, natural phrasing
2. Engagement — would the learner continue reading? Hook in first 50 words
3. Writing Quality — clarity, pacing, no word salad, logical flow
4. Immersion — % Ukrainian must hit target range (tables = ZERO)
5. Structure — lesson arc: WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE
6. Emotional Safety — ≥15 direct address, encouragement, quick wins
7. Lesson Quality — does it feel like a patient, encouraging tutor?"""

    if tier == "core":
        return """## Scoring Dimensions (7 — Core Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — native-level Ukrainian, register appropriate
2. Teaching Quality — did the learner actually learn something?
3. Writing Quality — depth, insights, "why" layer
4. Immersion — 85-100% Ukrainian
5. Structure — arc: HOOK → DISCOVER → EXPLAIN → PRACTICE → APPLY → SUMMARIZE
6. Engagement — real-world application, challenge, anticipation of confusion
7. Teaching Quality Score — effective instruction"""

    if tier == "seminar":
        return """## Scoring Dimensions (12 — Seminar Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Decolonization — Ukrainian-centric perspective, not Russian imperial
2. Language Quality — zero tolerance for Russianisms
3. Engagement — would you stay reading to the end?
4. Writing Quality — prose craft, narrative flow
5. Immersion — 98-100% Ukrainian
6. Research & Primary Sources — 3+ cited sources, 5+ dated events, 2+ primary quotes
7. Patriotic Content — Ukrainian pride, resistance framing
8. Pacing — max 200 words continuous exposition before break
9. Narrative Arc — HOOK → TENSION → JOURNEY → CLIMAX → RESOLUTION → CALL TO ACTION
10. Emotional Journey — curiosity, surprise, pride, empowerment
11. Weak Moment Detection — dead intros, walls of facts, energy drops
12. Lecture Quality — memorable, transformative, quotable"""

    # advanced
    return """## Scoring Dimensions (7 — Advanced Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — native sophistication, register awareness
2. Learning Quality — did this stretch the learner intellectually?
3. Sophistication — nuance, subtlety, exceptions
4. Immersion — 100% Ukrainian, no English scaffolding
5. Structure — arc: PROVOCATION → EXPLORATION → NUANCE → MASTERY → APPLICATION
6. Intellectual Engagement — challenges, nuance acknowledgments, production tasks
7. Learning Quality Score — treats learner as near-native"""


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

_FEASIBILITY_PROMPT = """You are about to build a module using the prompt below. This prompt has been carefully engineered to produce content that passes all audit gates. Your job is to confirm you can execute it AND that no semantic Russianisms are present.

**Default answer: PASS.** This prompt is designed to work. Only report issues if something will genuinely prevent you from building content that passes all audit gates, OR if vocabulary contains a semantic false friend.

## The Prompt

<prompt>
{RENDERED_PROMPT}
</prompt>

## Audit Gates (what your content will be checked against)

{AUDIT_CONTEXT}

{DIMENSION_CONTEXT}

## Check 1: Prompt Feasibility

Read the prompt carefully. Only report an issue if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (not "could be clearer" — literally missing)

Do NOT report: style preferences, wording suggestions, minor ambiguities, things that "could be improved."

**Gate names** (only these matter): Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Check 2: Semantic False Friends (Russianisms)

These Ukrainian words exist in BOTH Ukrainian and Russian but have DIFFERENT meanings. Check the prompt's vocabulary lists, example words, and content outline for misuse.

{FALSE_FRIENDS_TABLE}

**Only flag a word if the prompt USES or DEFINES it with the Russian meaning.** Do NOT flag:
- Warnings about the false friend (e.g., "неділя ≠ week" or "лук means bow, not onion")
- Discussions explaining the difference between Ukrainian and Russian meanings
- Correct Ukrainian usage of the word

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # or MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, UNCLEAR, RUSSICISM
      location: "vocabulary_hints, required list"
      problem: "город paired with 'city' — this is the Russian meaning. Ukrainian город = garden/vegetable patch"
      suggested_fix: "Replace город (city) with місто (city), or change meaning to 'garden'"
      severity: HIGH  # or MEDIUM, LOW
```

If there are no issues, return:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```

Be SPECIFIC. Cite exact text from the prompt. Focus on issues that will cause audit FAILURES or introduce Russianisms."""


_COHERENCE_PROMPT = """You are a curriculum reviewer checking whether a content generation prompt correctly implements its plan.

## The Plan

<plan>
{PLAN_YAML}
</plan>

## The Rendered Prompt

<prompt>
{RENDERED_PROMPT}
</prompt>

## Audit Gates

{AUDIT_CONTEXT}

## Instructions

You MUST complete ALL checks below before producing your verdict. Work through them one by one.

### Step 1: Section coverage checklist
For EACH section in the plan's `content_outline`, find the matching section header or word budget in the prompt. List every plan section and whether it has a match:

Plan section → Prompt match (YES/NO + where)

### Step 2: Word target check
Compare the plan's `word_target` with the prompt's word budget. Do they match?

### Step 3: Vocabulary check
Scan the plan's `vocabulary_hints.required` list. Are all items present or referenced in the prompt?

### Step 4: Objective check
For each plan `objective`, confirm the prompt contains instructions that would achieve it.

## Verdict Rules

After completing the checklist, report issues ONLY for:
- A plan section **completely missing** from the prompt (not just reworded)
- The prompt **contradicts** a plan objective or constraint
- The word target in the prompt **differs** from the plan
- Required vocabulary items **absent** from the prompt

Do NOT flag: minor wording differences, section reordering, extra scaffolding the prompt adds beyond the plan.

## Output Format

First output your checklist (Steps 1-4), then the YAML verdict:

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: MISSING_PLAN_SECTION  # or PLAN_CONTRADICTION, WORD_TARGET_MISMATCH, MISSING_VOCABULARY
      location: "content_outline section 3: Verb Conjugation Patterns"
      problem: "Plan section 'Verb Conjugation Patterns' has no corresponding section in the prompt"
      suggested_fix: "Add a section header and word budget for verb conjugation patterns"
      severity: HIGH  # or MEDIUM, LOW
```

If all checks pass:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```"""


def _build_false_friends_table() -> str:
    """Build a markdown reference table of semantic false friends for the feasibility check."""
    try:
        from pipeline.semantic_russianisms import SEMANTIC_FALSE_FRIENDS
    except ImportError:
        return "(false friends reference not available)"

    lines = []
    for ff in SEMANTIC_FALSE_FRIENDS:
        russian = ", ".join(ff["russian_meanings"][:3])
        lines.append(
            f"- **{ff['word']}**: Russian meaning = {russian}; "
            f"Ukrainian meaning = {ff['ukrainian_meaning']}. "
            f"Correct word for '{russian}' → **{ff['replacement']}**"
        )
    return "\n".join(lines)


def build_feasibility_prompt(rendered_prompt: str, track: str, module_num: int) -> str:
    """Build the feasibility check prompt (writer self-check + Russicism detection)."""
    if len(rendered_prompt) > 40000:
        rendered_prompt = rendered_prompt[:40000] + "\n\n... (prompt truncated for review) ..."

    audit_ctx = build_audit_context(track, module_num)
    dim_ctx = build_dimension_context(track, module_num)
    ff_table = _build_false_friends_table()

    return _FEASIBILITY_PROMPT.format(
        RENDERED_PROMPT=rendered_prompt,
        AUDIT_CONTEXT=audit_ctx,
        DIMENSION_CONTEXT=dim_ctx,
        FALSE_FRIENDS_TABLE=ff_table,
    )


def build_coherence_prompt(
    rendered_prompt: str, plan_yaml: str, track: str, module_num: int,
) -> str:
    """Build the coherence check prompt (reviewer plan-prompt alignment)."""
    if len(rendered_prompt) > 40000:
        rendered_prompt = rendered_prompt[:40000] + "\n\n... (prompt truncated for review) ..."
    if len(plan_yaml) > 10000:
        plan_yaml = plan_yaml[:10000] + "\n\n... (plan truncated) ..."

    audit_ctx = build_audit_context(track, module_num)

    return _COHERENCE_PROMPT.format(
        RENDERED_PROMPT=rendered_prompt,
        PLAN_YAML=plan_yaml,
        AUDIT_CONTEXT=audit_ctx,
    )


# Keep backward compat alias
def build_preflight_prompt(rendered_prompt: str, track: str, module_num: int) -> str:
    """Build the full preflight check prompt (backward compat — uses feasibility prompt)."""
    return build_feasibility_prompt(rendered_prompt, track, module_num)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_preflight_response(text: str, source: str = "unknown") -> PreflightResult:
    """Parse a preflight review response into structured result.

    Args:
        text: Raw LLM output (YAML with optional markdown fences).
        source: Label for issue provenance ("feasibility" or "coherence").
    """
    if not text or not text.strip():
        return PreflightResult(status="PASS", raw_output="(empty response)")

    # Clean markdown code fences
    cleaned = text.strip()
    cleaned = re.sub(r"```ya?ml\s*\n?", "", cleaned)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)

    # Try to extract YAML block
    yaml_match = re.search(r"prompt_preflight:\s*\n([\s\S]+?)(?:\n\S|\Z)", cleaned)
    yaml_text = ("prompt_preflight:\n" + yaml_match.group(1)) if yaml_match else cleaned

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        # Try the whole text
        try:
            data = yaml.safe_load(cleaned)
        except yaml.YAMLError:
            return PreflightResult(status="PARSE_ERROR", raw_output=text)

    if not isinstance(data, dict):
        return PreflightResult(status="PARSE_ERROR", raw_output=text)

    pf = data.get("prompt_preflight", data)
    status = pf.get("status", "PASS")
    raw_issues = pf.get("issues", [])

    issues = []
    if isinstance(raw_issues, list):
        for item in raw_issues:
            if not isinstance(item, dict):
                continue
            issues.append(PreflightIssue(
                issue_type=str(item.get("type", "UNCLEAR")),
                location=str(item.get("location", "")),
                problem=str(item.get("problem", "")),
                suggested_fix=str(item.get("suggested_fix", "")),
                severity=str(item.get("severity", "MEDIUM")).upper(),
                source=source,
            ))

    if issues and status == "PASS":
        status = "ISSUES_FOUND"

    return PreflightResult(status=status, issues=issues, raw_output=text)


# ---------------------------------------------------------------------------
# Auto-fix (feasibility issues only)
# ---------------------------------------------------------------------------


# Known fix patterns: maps issue keywords to prompt sections to remove/replace.
# Each entry: (trigger_keywords, section_header_pattern, action)
_FIX_PATTERNS: list[tuple[list[str], str, str]] = [
    # Contradiction: immersion target mismatch
    (
        ["45-65%", "45–65%", "immersion target"],
        r"(?i)this high volume is REQUIRED to hit the \d+-\d+% immersion target",
        "this high volume is REQUIRED to hit the immersion target specified above",
    ),
    # Contradiction: verb ban vs verb warning
    (
        ["verb", "imperative", "banned", "Irregular Forms"],
        r"### Irregular Forms Warning.*?(?=\n###|\n---|\Z)",
        "",  # remove entire section
    ),
]


def apply_preflight_fixes(
    prompt_path: Path,
    high_issues: list[PreflightIssue],
    orch_dir: Path,
) -> Path | None:
    """Apply suggested fixes from preflight HIGH issues to the rendered prompt.

    Only applies fixes from feasibility issues. Coherence issues require human
    intervention (template/plan rework).

    Saves the fixed prompt to orch_dir/content-prompt-fixed.md.
    Returns the path to the fixed prompt, or None if no fixes could be applied.
    """
    # Filter to feasibility issues only — coherence issues can't be auto-fixed
    fixable_issues = [i for i in high_issues if i.source != "coherence"]
    if not fixable_issues:
        return None

    prompt_text = prompt_path.read_text("utf-8")
    original = prompt_text
    fixes_applied = 0

    for issue in fixable_issues:
        combined = f"{issue.problem} {issue.suggested_fix}".lower()

        # Try pattern-based fixes first
        for trigger_words, pattern, replacement in _FIX_PATTERNS:
            if any(w.lower() in combined for w in trigger_words):
                new_text = re.sub(pattern, replacement, prompt_text, flags=re.DOTALL)
                if new_text != prompt_text:
                    prompt_text = new_text
                    fixes_applied += 1
                    log(f"  preflight: Applied pattern fix for [{issue.issue_type}] {issue.location}")
                    break

        # If no pattern matched but the fix suggests removing a section,
        # try to find and remove the section by header
        if "remove" in issue.suggested_fix.lower() and fixes_applied == 0:
            # Extract section name from the location field
            section_match = re.search(r"###?\s+(.+?)(?:\s+vs|\s+section|\Z)", issue.location)
            if section_match:
                section_name = section_match.group(1).strip()
                # Remove the section (header + content until next section)
                section_pattern = rf"###\s+{re.escape(section_name)}.*?(?=\n###|\n---|\n##[^#]|\Z)"
                new_text = re.sub(section_pattern, "", prompt_text, flags=re.DOTALL)
                if new_text != prompt_text:
                    prompt_text = new_text
                    fixes_applied += 1
                    log(f"  preflight: Removed section '{section_name}' per suggested fix")

    if fixes_applied == 0:
        return None

    # Clean up multiple blank lines left by removals
    prompt_text = re.sub(r"\n{4,}", "\n\n\n", prompt_text)

    # Save the fixed prompt
    fixed_path = orch_dir / "content-prompt-fixed.md"
    fixed_path.write_text(prompt_text, "utf-8")

    # Also save a diff for verification
    import difflib
    orig_lines = original.splitlines()
    fixed_lines = prompt_text.splitlines()
    diff = difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile="original-prompt.md",
        tofile="content-prompt-fixed.md",
        n=2,
    )
    diff_text = "\n".join(diff)
    if diff_text:
        diff_path = orch_dir / "preflight-fix-diff.md"
        diff_path.write_text(diff_text, "utf-8")
        log(f"  preflight: Diff saved → {diff_path.name} ({fixes_applied} fix(es))")

    return fixed_path


# ---------------------------------------------------------------------------
# Individual check runners
# ---------------------------------------------------------------------------


def _log_and_save_result(
    result: PreflightResult,
    label: str,
    result_path: Path,
) -> None:
    """Log and save a single preflight check result."""
    if result.status == "PASS":
        log(f"  preflight-{label}: PASS — no issues found")
    elif result.status == "ISSUES_FOUND":
        high = len(result.high_issues)
        total = len(result.issues)
        log(f"  preflight-{label}: {total} issue(s) found ({high} HIGH)")
        for issue in result.issues:
            severity_marker = "!!" if issue.severity == "HIGH" else "?"
            log(f"    {severity_marker} [{issue.issue_type}] {issue.problem[:120]}")
    else:
        log(f"  preflight-{label}: {result.status} — could not parse response")

    result_data = {
        "status": result.status,
        "source": label,
        "issue_count": len(result.issues),
        "high_count": len(result.high_issues),
        "issues": [
            {
                "type": i.issue_type,
                "location": i.location,
                "problem": i.problem,
                "suggested_fix": i.suggested_fix,
                "severity": i.severity,
                "source": i.source,
            }
            for i in result.issues
        ],
    }
    result_path.write_text(
        yaml.dump(result_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )


def _dispatch_gemini_simple(
    prompt: str, model: str | None = None, timeout: int = 300,
) -> tuple[bool, str]:
    """Call Gemini via the standard dispatch — simple (prompt_text) → (ok, output) interface."""
    from batch_gemini_config import FLASH_MODEL
    from pipeline.core import dispatch_gemini
    return dispatch_gemini(
        prompt, task_id="preflight-feasibility",
        model=model or FLASH_MODEL, stdout_only=True, timeout=timeout,
    )


def run_feasibility_check(
    rendered_prompt_path: Path,
    track: str,
    module_num: int,
    orch_dir: Path,
    dispatch_fn=None,
) -> PreflightResult:
    """Run the feasibility check (writer self-check + Russicism detection).

    dispatch_fn signature: (prompt_text: str) -> tuple[bool, str]
    """
    if dispatch_fn is None:
        dispatch_fn = _dispatch_gemini_simple

    rendered_prompt = rendered_prompt_path.read_text("utf-8")
    prompt_text = build_feasibility_prompt(rendered_prompt, track, module_num)

    prompt_path = orch_dir / "preflight-feasibility-prompt.md"
    prompt_path.write_text(prompt_text, "utf-8")

    log("  preflight-feasibility: Dispatching to writer agent...")

    ok, raw = dispatch_fn(prompt_text)

    if not ok:
        log("  preflight-feasibility: Dispatch failed")
        return PreflightResult(status="DISPATCH_ERROR", raw_output=raw or "")

    raw_output = raw or ""
    # Save output for debugging
    output_path = orch_dir / "preflight-feasibility-output.md"
    output_path.write_text(raw_output, "utf-8")
    result = parse_preflight_response(raw_output, source="feasibility")

    result_path = orch_dir / "preflight-feasibility-result.yaml"
    _log_and_save_result(result, "feasibility", result_path)

    return result


def _dispatch_claude_simple(
    prompt: str, model: str = "claude-sonnet-4-6", timeout: int = 300,
) -> tuple[bool, str]:
    """Call Claude CLI with a plain prompt — no delimiters, no review-phase baggage.

    Unlike dispatch_claude_phase (which injects ===REVIEW_START=== delimiters and
    review-specific system prompts), this sends the prompt as-is and returns the
    full response text.
    """
    import shutil
    import subprocess as _sp

    claude_bin = shutil.which("claude") or "claude"
    cmd = [claude_bin, "--model", model, "-p", "--output-format", "text"]

    try:
        result = _sp.run(
            cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  preflight-coherence: Claude CLI error (rc={result.returncode}): {err[:200]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  preflight-coherence: Claude CLI not found")
        return False, ""
    except _sp.TimeoutExpired:
        log(f"  preflight-coherence: Claude CLI timeout ({timeout}s)")
        return False, ""


def run_coherence_check(
    rendered_prompt_path: Path,
    plan_path: Path,
    track: str,
    module_num: int,
    orch_dir: Path,
    dispatch_fn=None,
) -> PreflightResult:
    """Run the coherence check (reviewer plan-prompt alignment via Claude Sonnet)."""
    if dispatch_fn is None:
        dispatch_fn = _dispatch_claude_simple

    rendered_prompt = rendered_prompt_path.read_text("utf-8")
    plan_yaml = plan_path.read_text("utf-8")
    prompt_text = build_coherence_prompt(rendered_prompt, plan_yaml, track, module_num)

    prompt_path = orch_dir / "preflight-coherence-prompt.md"
    prompt_path.write_text(prompt_text, "utf-8")

    log("  preflight-coherence: Dispatching to reviewer agent (Claude Sonnet)...")

    ok, raw = dispatch_fn(prompt_text)

    if not ok:
        log("  preflight-coherence: Dispatch failed")
        return PreflightResult(status="DISPATCH_ERROR", raw_output=raw or "")

    raw_output = raw or ""
    # Save output for debugging
    output_path = orch_dir / "preflight-coherence-output.md"
    output_path.write_text(raw_output, "utf-8")

    result = parse_preflight_response(raw_output, source="coherence")

    result_path = orch_dir / "preflight-coherence-result.yaml"
    _log_and_save_result(result, "coherence", result_path)

    return result


# ---------------------------------------------------------------------------
# Combined runner (main entry point)
# ---------------------------------------------------------------------------


def run_prompt_preflight(
    rendered_prompt_path: Path,
    track: str,
    module_num: int,
    orch_dir: Path,
    dispatch_fn=None,
    coherence_dispatch_fn=None,
    plan_path: Path | None = None,
    coherence_model: str | None = None,
) -> CombinedPreflightResult:
    """Run both preflight checks in parallel and return combined result.

    Args:
        rendered_prompt_path: Path to the rendered content prompt.
        track: Track identifier (e.g. "a1").
        module_num: Module sequence number.
        orch_dir: Orchestration directory for saving artifacts.
        dispatch_fn: Gemini dispatch function for feasibility (default: dispatch_gemini with Flash).
        coherence_dispatch_fn: Claude dispatch function for coherence.
            Signature: (prompt_text: str) -> tuple[bool, str].
            Default: _dispatch_claude_simple with coherence_model.
        plan_path: Path to plan YAML. If None, coherence check is skipped.
        coherence_model: Override model for coherence check (default: claude-sonnet-4-6).

    Returns:
        CombinedPreflightResult with merged issues from both checks.
    """
    # Build coherence dispatch with model override
    if coherence_dispatch_fn is None and plan_path is not None:
        model = coherence_model or "claude-sonnet-4-6"

        def coherence_dispatch_fn(prompt_text: str) -> tuple[bool, str]:
            return _dispatch_claude_simple(prompt_text, model=model)

    # Run checks in parallel if coherence is available
    if plan_path is not None and plan_path.exists():
        log("  preflight: Running feasibility + coherence checks in parallel...")

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            feas_future = executor.submit(
                run_feasibility_check,
                rendered_prompt_path, track, module_num, orch_dir, dispatch_fn,
            )
            coh_future = executor.submit(
                run_coherence_check,
                rendered_prompt_path, plan_path, track, module_num, orch_dir,
                coherence_dispatch_fn,
            )
            feasibility = feas_future.result()
            coherence = coh_future.result()
        except KeyboardInterrupt:
            log("  preflight: Interrupted — cancelling checks...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        finally:
            executor.shutdown(wait=False)
    else:
        if plan_path is None:
            log("  preflight: No plan path — skipping coherence check")
        elif not plan_path.exists():
            log(f"  preflight: Plan not found at {plan_path} — skipping coherence check")
        feasibility = run_feasibility_check(
            rendered_prompt_path, track, module_num, orch_dir, dispatch_fn,
        )
        coherence = None

    combined = CombinedPreflightResult(feasibility=feasibility, coherence=coherence)

    # Save combined result (backward compat)
    combined_data = {
        "status": combined.status,
        "feasibility_status": feasibility.status,
        "coherence_status": coherence.status if coherence else "SKIPPED",
        "issue_count": len(combined.issues),
        "high_count": len(combined.high_issues),
        "issues": [
            {
                "type": i.issue_type,
                "location": i.location,
                "problem": i.problem,
                "suggested_fix": i.suggested_fix,
                "severity": i.severity,
                "source": i.source,
            }
            for i in combined.issues
        ],
    }
    combined_path = orch_dir / "preflight-result.yaml"
    combined_path.write_text(
        yaml.dump(combined_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )

    return combined
