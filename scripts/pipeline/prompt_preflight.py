"""Prompt preflight check — Gemini validates its own instructions before content generation.

Sends the rendered prompt to Gemini along with audit gate thresholds and scoring
dimensions. Gemini identifies contradictions, impossible targets, and missing
instructions that would cause audit failures.

Returns structured feedback that the pipeline can auto-apply or log.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pipeline_lib import log

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


@dataclass
class PreflightResult:
    """Result of a prompt preflight check."""
    status: str  # PASS | ISSUES_FOUND
    issues: list[PreflightIssue] = field(default_factory=list)
    raw_output: str = ""

    @property
    def high_issues(self) -> list[PreflightIssue]:
        return [i for i in self.issues if i.severity == "HIGH"]


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
        from pipeline_lib import _get_prompt_tier
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
# Preflight prompt builder
# ---------------------------------------------------------------------------

_PREFLIGHT_PROMPT = """You are reviewing a content generation prompt BEFORE it is used to build a module. Your job is to find problems that will cause the generated content to FAIL the audit.

## The Prompt to Review

<prompt>
{RENDERED_PROMPT}
</prompt>

## What the Audit Will Check

{AUDIT_CONTEXT}

{DIMENSION_CONTEXT}

## Your Task

Analyze the prompt above and identify:
1. **CONTRADICTIONS** — instructions that conflict with each other or with the audit gates
2. **IMPOSSIBLE TARGETS** — the instructions make it mathematically impossible to hit a gate
3. **MISSING INSTRUCTIONS** — something the audit requires but the prompt doesn't mention
4. **UNCLEAR** — ambiguous instructions that could be interpreted wrong

For each issue, provide a specific fix.

**Severity guidelines — be VERY strict about HIGH:**
- **HIGH**: Will cause the generated content to FAIL one of these specific automated audit gates: Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion, Review. You MUST name which gate will fail. If you cannot name a gate → it's not HIGH.
- **MEDIUM**: Could cause a lower review score but won't fail any gate.
- **LOW**: Style preference, minor ambiguity, or cosmetic issue.

Examples of NOT HIGH: heading format preferences, RAG query language, video embed syntax, vocabulary wording, image-to-letter using emojis (not URLs). These don't fail gates.
Examples of HIGH: word target impossible to reach (Words gate), missing H2 section (Structure gate), banned grammar used (Pedagogy gate).

**Do NOT flag**: image-to-letter activities use emoji characters (👩, 🐈), not image URLs. This is by design.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # or MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, UNCLEAR
      location: "Section 4, line about tables"
      problem: "Template says tables have highest density but audit strips tables from immersion"
      suggested_fix: "Remove 'highest density' claim, add warning that tables = zero immersion"
      severity: HIGH  # or MEDIUM, LOW
```

If there are no issues, return:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```

Be SPECIFIC. Cite exact text from the prompt. Focus on issues that will cause audit FAILURES, not style preferences."""


def build_preflight_prompt(rendered_prompt: str, track: str, module_num: int) -> str:
    """Build the full preflight check prompt."""
    # Truncate very long prompts to avoid token limits
    if len(rendered_prompt) > 40000:
        rendered_prompt = rendered_prompt[:40000] + "\n\n... (prompt truncated for review) ..."

    audit_ctx = build_audit_context(track, module_num)
    dim_ctx = build_dimension_context(track, module_num)

    return _PREFLIGHT_PROMPT.format(
        RENDERED_PROMPT=rendered_prompt,
        AUDIT_CONTEXT=audit_ctx,
        DIMENSION_CONTEXT=dim_ctx,
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_preflight_response(text: str) -> PreflightResult:
    """Parse Gemini's preflight review response into structured result."""
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
            ))

    if issues and status == "PASS":
        status = "ISSUES_FOUND"

    return PreflightResult(status=status, issues=issues, raw_output=text)


# ---------------------------------------------------------------------------
# Auto-fix
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

    Saves the fixed prompt to orch_dir/content-prompt-fixed.md.
    Returns the path to the fixed prompt, or None if no fixes could be applied.
    """
    prompt_text = prompt_path.read_text("utf-8")
    original = prompt_text
    fixes_applied = 0

    for issue in high_issues:
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
    orig_lines = original.splitlines()
    fixed_lines = prompt_text.splitlines()
    import difflib
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
# Runner
# ---------------------------------------------------------------------------


def run_prompt_preflight(
    rendered_prompt_path: Path,
    track: str,
    module_num: int,
    orch_dir: Path,
    dispatch_fn=None,
) -> PreflightResult:
    """Run the prompt preflight check.

    Args:
        rendered_prompt_path: Path to the rendered content prompt
        track: Track identifier
        module_num: Module number
        orch_dir: Orchestration directory for saving artifacts
        dispatch_fn: Gemini dispatch function (default: dispatch_gemini)

    Returns:
        PreflightResult with status and issues
    """
    if dispatch_fn is None:
        from pipeline_lib import dispatch_gemini
        dispatch_fn = dispatch_gemini

    rendered_prompt = rendered_prompt_path.read_text("utf-8")
    preflight_prompt_text = build_preflight_prompt(rendered_prompt, track, module_num)

    # Save the preflight prompt for debugging
    preflight_prompt_path = orch_dir / "preflight-prompt.md"
    preflight_prompt_path.write_text(preflight_prompt_text, "utf-8")

    log("  preflight: Dispatching prompt review to Gemini...")

    # Dispatch to Gemini
    output_path = orch_dir / "preflight-output.md"
    task_id = f"preflight-{track}-{module_num}"

    ok, raw = dispatch_fn(
        str(preflight_prompt_path),
        task_id,
        output_file=output_path,
    )

    if not ok:
        log("  preflight: Gemini dispatch failed")
        return PreflightResult(status="DISPATCH_ERROR", raw_output=raw or "")

    raw_output = output_path.read_text("utf-8") if output_path.exists() else (raw or "")
    result = parse_preflight_response(raw_output)

    # Log results
    if result.status == "PASS":
        log("  preflight: PASS — no issues found")
    elif result.status == "ISSUES_FOUND":
        high = len(result.high_issues)
        total = len(result.issues)
        log(f"  preflight: {total} issue(s) found ({high} HIGH)")
        for issue in result.issues:
            severity_marker = "!!" if issue.severity == "HIGH" else "?"
            log(f"    {severity_marker} [{issue.issue_type}] {issue.problem[:120]}")
    else:
        log(f"  preflight: {result.status} — could not parse response")

    # Save structured result
    result_path = orch_dir / "preflight-result.yaml"
    result_data = {
        "status": result.status,
        "issue_count": len(result.issues),
        "high_count": len(result.high_issues),
        "issues": [
            {
                "type": i.issue_type,
                "location": i.location,
                "problem": i.problem,
                "suggested_fix": i.suggested_fix,
                "severity": i.severity,
            }
            for i in result.issues
        ],
    }
    result_path.write_text(
        yaml.dump(result_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )

    return result
