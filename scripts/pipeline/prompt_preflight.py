"""Prompt preflight — single writer call checks feasibility, Russianisms, and plan coherence.

One LLM call to the writer agent before content generation. Checks:
1. Prompt feasibility (contradictions, impossible targets, missing instructions)
2. Semantic false friends (Russianisms in vocabulary/content)
3. Plan-prompt coherence (section coverage, word target, vocabulary — when plan available)

Returns structured PreflightResult with auto-fixable issues.
"""

from __future__ import annotations

import re
import sys
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
    issue_type: str  # CONTRADICTION | MISSING_INSTRUCTION | IMPOSSIBLE_TARGET | UNCLEAR | RUSSICISM | MISSING_PLAN_SECTION | ...
    location: str  # where in the prompt
    problem: str  # what's wrong
    suggested_fix: str  # how to fix it
    severity: str  # HIGH | MEDIUM | LOW
    source: str = "preflight"


@dataclass
class PreflightResult:
    """Result of the preflight check."""
    status: str  # PASS | ISSUES_FOUND | DISPATCH_ERROR | PARSE_ERROR
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
        f"Word target (MINIMUM): {cfg.get('target_words', '?')}",
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
# Prompt builder (single unified prompt)
# ---------------------------------------------------------------------------

_PREFLIGHT_PROMPT = """You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
{RENDERED_PROMPT}
</prompt>

{PLAN_SECTION}

## Audit Gates

{AUDIT_CONTEXT}

{DIMENSION_CONTEXT}

## Check 1: Prompt Feasibility

Only report if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (literally missing, not "could be clearer")

**Gate names**: Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Check 2: Semantic False Friends (Russianisms)

These Ukrainian words exist in BOTH Ukrainian and Russian but have DIFFERENT meanings:

{FALSE_FRIENDS_TABLE}

**Only flag if the prompt USES or DEFINES a word with the Russian meaning.** Do NOT flag:
- Warnings about the false friend (e.g., "неділя ≠ week")
- Discussions explaining the difference
- Correct Ukrainian usage

{COHERENCE_SECTION}

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, RUSSICISM, MISSING_PLAN_SECTION, PLAN_CONTRADICTION, WORD_TARGET_MISMATCH
      location: "where in the prompt"
      problem: "what's wrong"
      suggested_fix: "how to fix it"
      severity: HIGH  # or MEDIUM, LOW
```

If no issues: `prompt_preflight: {{status: PASS, issues: []}}`

Be SPECIFIC. Cite exact text."""


_COHERENCE_SECTION = """## Check 3: Plan-Prompt Coherence

Compare the plan (above) to the rendered prompt. Check:
1. **Section coverage**: Every plan `content_outline` section has a matching section in the prompt
2. **Word target**: Plan's `word_target` matches the prompt's word budget
3. **Vocabulary**: All `vocabulary_hints.required` items appear in the prompt
4. **Objectives**: The prompt's instructions would achieve all plan `objectives`

Only flag if a plan section is **completely missing**, the word target **differs**, or required vocabulary is **absent**. Do NOT flag rewordings or extra scaffolding."""


def _build_false_friends_table() -> str:
    """Build a markdown reference table of semantic false friends."""
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


def build_preflight_prompt(
    rendered_prompt: str,
    track: str,
    module_num: int,
    plan_yaml: str | None = None,
) -> str:
    """Build the unified preflight prompt (feasibility + Russianisms + coherence).

    When plan_yaml is provided, includes the plan and coherence check.
    """
    if len(rendered_prompt) > 40000:
        rendered_prompt = rendered_prompt[:40000] + "\n\n... (prompt truncated for review) ..."

    audit_ctx = build_audit_context(track, module_num)
    dim_ctx = build_dimension_context(track, module_num)
    ff_table = _build_false_friends_table()

    if plan_yaml:
        if len(plan_yaml) > 10000:
            plan_yaml = plan_yaml[:10000] + "\n\n... (plan truncated) ..."
        plan_section = f"## The Plan\n\n<plan>\n{plan_yaml}\n</plan>"
        coherence_section = _COHERENCE_SECTION
    else:
        plan_section = ""
        coherence_section = ""

    return _PREFLIGHT_PROMPT.format(
        RENDERED_PROMPT=rendered_prompt,
        PLAN_SECTION=plan_section,
        AUDIT_CONTEXT=audit_ctx,
        DIMENSION_CONTEXT=dim_ctx,
        FALSE_FRIENDS_TABLE=ff_table,
        COHERENCE_SECTION=coherence_section,
    )


# Backward compat aliases
build_feasibility_prompt = build_preflight_prompt
build_coherence_prompt = None  # removed — use build_preflight_prompt with plan_yaml


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_preflight_response(text: str, source: str = "preflight") -> PreflightResult:
    """Parse preflight review response into structured result."""
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
# Auto-fix (prompt pattern fixes)
# ---------------------------------------------------------------------------

_FIX_PATTERNS: list[tuple[list[str], str, str]] = [
    (
        ["45-65%", "45–65%", "immersion target"],
        r"(?i)this high volume is REQUIRED to hit the \d+-\d+% immersion target",
        "this high volume is REQUIRED to hit the immersion target specified above",
    ),
    (
        ["verb", "imperative", "banned", "Irregular Forms"],
        r"### Irregular Forms Warning.*?(?=\n###|\n---|\Z)",
        "",
    ),
]


def apply_preflight_fixes(
    prompt_path: Path,
    high_issues: list[PreflightIssue],
    orch_dir: Path,
) -> Path | None:
    """Apply pattern-based fixes to the rendered prompt for non-RUSSICISM issues.

    Returns path to fixed prompt, or None if no fixes applied.
    """
    fixable = [i for i in high_issues if i.issue_type != "RUSSICISM"]
    if not fixable:
        return None

    prompt_text = prompt_path.read_text("utf-8")
    original = prompt_text
    fixes_applied = 0

    for issue in fixable:
        combined = f"{issue.problem} {issue.suggested_fix}".lower()
        for trigger_words, pattern, replacement in _FIX_PATTERNS:
            if any(w.lower() in combined for w in trigger_words):
                new_text = re.sub(pattern, replacement, prompt_text, flags=re.DOTALL)
                if new_text != prompt_text:
                    prompt_text = new_text
                    fixes_applied += 1
                    log(f"  preflight: Applied pattern fix for [{issue.issue_type}] {issue.location}")
                    break

        if "remove" in issue.suggested_fix.lower() and fixes_applied == 0:
            section_match = re.search(r"###?\s+(.+?)(?:\s+vs|\s+section|\Z)", issue.location)
            if section_match:
                section_name = section_match.group(1).strip()
                section_pattern = rf"###\s+{re.escape(section_name)}.*?(?=\n###|\n---|\n##[^#]|\Z)"
                new_text = re.sub(section_pattern, "", prompt_text, flags=re.DOTALL)
                if new_text != prompt_text:
                    prompt_text = new_text
                    fixes_applied += 1
                    log(f"  preflight: Removed section '{section_name}' per suggested fix")

    if fixes_applied == 0:
        return None

    prompt_text = re.sub(r"\n{4,}", "\n\n\n", prompt_text)
    fixed_path = orch_dir / "content-prompt-fixed.md"
    fixed_path.write_text(prompt_text, "utf-8")

    import difflib
    diff = difflib.unified_diff(
        original.splitlines(), prompt_text.splitlines(),
        fromfile="original-prompt.md", tofile="content-prompt-fixed.md", n=2,
    )
    diff_text = "\n".join(diff)
    if diff_text:
        diff_path = orch_dir / "preflight-fix-diff.md"
        diff_path.write_text(diff_text, "utf-8")
        log(f"  preflight: Diff saved → {diff_path.name} ({fixes_applied} fix(es))")

    return fixed_path


# ---------------------------------------------------------------------------
# Runner (single call)
# ---------------------------------------------------------------------------


def run_prompt_preflight(
    rendered_prompt_path: Path,
    track: str,
    module_num: int,
    orch_dir: Path,
    dispatch_fn=None,
    plan_path: Path | None = None,
    **_kwargs,
) -> PreflightResult:
    """Run the preflight check — single call to the writer agent.

    Checks feasibility, Russianisms, and plan-prompt coherence (when plan available).

    Args:
        rendered_prompt_path: Path to the rendered content prompt.
        track: Track identifier.
        module_num: Module sequence number.
        orch_dir: Orchestration directory for saving artifacts.
        dispatch_fn: Writer dispatch function. Signature: (prompt_text: str) -> tuple[bool, str].
        plan_path: Path to plan YAML. If provided, coherence check is included.

    Returns:
        PreflightResult with status and issues.
    """
    if dispatch_fn is None:
        from batch_gemini_config import FLASH_MODEL
        from pipeline.core import dispatch_gemini

        def dispatch_fn(prompt_text):
            return dispatch_gemini(
                prompt_text, task_id="preflight",
                model=FLASH_MODEL, stdout_only=True, timeout=300,
            )

    rendered_prompt = rendered_prompt_path.read_text("utf-8")
    plan_yaml = None
    if plan_path and plan_path.exists():
        plan_yaml = plan_path.read_text("utf-8")

    prompt_text = build_preflight_prompt(rendered_prompt, track, module_num, plan_yaml)

    # Save prompt for debugging
    prompt_save_path = orch_dir / "preflight-prompt.md"
    prompt_save_path.write_text(prompt_text, "utf-8")

    log("  preflight: Dispatching to writer agent...")

    ok, raw = dispatch_fn(prompt_text)

    if not ok:
        log("  preflight: Dispatch failed")
        return PreflightResult(status="DISPATCH_ERROR", raw_output=raw or "")

    raw_output = raw or ""
    output_path = orch_dir / "preflight-output.md"
    output_path.write_text(raw_output, "utf-8")

    result = parse_preflight_response(raw_output)

    # Log and save
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
    result_path = orch_dir / "preflight-result.yaml"
    result_path.write_text(
        yaml.dump(result_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        "utf-8",
    )

    return result
