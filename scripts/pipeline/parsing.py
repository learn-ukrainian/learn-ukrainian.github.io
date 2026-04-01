"""Pipeline v5 parsing, extraction, and formatting utilities.

Extracted from pipeline_v5.py -- delimiter extraction, audit parsing,
metrics computation, prompt injection, D1 review parsing, LLM filler
scanning, calibration, and quality gate helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.core import ModuleContext, log

# Import helpers -- all heavy logic lives in parsing_helpers.py

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DScreenResult:
    """Result of deterministic screen -- collects all pre-LLM findings."""
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
        if stripped.startswith("\u2500") or stripped.startswith("\u2705") or stripped.startswith("\u2713"):
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

    # Inject friction constraints if placeholder exists (#970 AC4)
    if "{FRICTION_CONSTRAINTS}" in prompt_text:
        from pipeline.core import _load_friction_constraints
        friction = _load_friction_constraints(ctx)
        prompt_text = prompt_text.replace("{FRICTION_CONSTRAINTS}", friction)

    return prompt_text


# ---------------------------------------------------------------------------
# D.1 review parsing (wrappers that pass delimiter functions)
# ---------------------------------------------------------------------------

def _parse_d1_review(raw_output: str) -> D1Result:
    """Parse D.1 Markdown review from delimiters."""
    from pipeline.parsing_helpers import _parse_d1_review as _impl
    return _impl(raw_output, _extract_delimiter, _extract_delimiter_tolerant)


def _parse_factual_review(raw_output: str) -> D1Result:
    """Parse Gemini Fact Checker output."""
    from pipeline.parsing_helpers import _parse_factual_review as _impl
    return _impl(raw_output, _extract_delimiter, _extract_delimiter_tolerant)


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
# Re-exports from sibling modules (parsing_helpers, parsing_review)
# pipeline_v5.py imports everything from pipeline.parsing as the public API
# ---------------------------------------------------------------------------
from pipeline.parsing_helpers import (
    _compute_metrics_direct,
    _extract_audit_failures,
    _extract_gate_blockers,
    _extract_vesum_failures,
    _format_deterministic_issues,
    _format_filler_phrases,
    _format_vesum_verification,
    _get_russicism_table,
    _scan_llm_filler,
)
from pipeline.parsing_review import (
    _build_d3_context,
    _get_track_calibration,
    _quick_review_quality_gate,
)
