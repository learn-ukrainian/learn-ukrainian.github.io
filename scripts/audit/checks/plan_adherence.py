"""
Plan Adherence Checker — Deterministic checks comparing built content vs plan YAML.

Catches issues that Gemini's generation misses:
1. Vocabulary coverage (stress-normalized)
2. Structural elements (plan says "chart/table" → must have markdown table)
3. Activity count compliance (activity_hints item counts are hard constraints)
4. Activity focus compliance (match activity focus descriptions vs built activity)

All checks are deterministic — no LLM needed.

Issue: #849
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PlanAdherenceIssue:
    """A single plan adherence violation."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    check_type: str  # VOCAB_NOT_IN_CONTENT, MISSING_STRUCTURAL_ELEMENT, etc.
    section: str  # Which section or activity is affected
    expected: str  # What the plan says
    actual: str  # What the content has
    fix_hint: str  # Actionable description of how to fix


@dataclass
class PlanAdherenceResult:
    """Complete plan adherence check result."""
    issues: list[PlanAdherenceIssue] = field(default_factory=list)
    checks_run: int = 0
    checks_passed: int = 0

    @property
    def passed(self) -> bool:
        return not any(i.severity in ("CRITICAL", "HIGH") for i in self.issues)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _strip_stress(text: str) -> str:
    """Remove combining acute accents (stress marks) from text."""
    return unicodedata.normalize("NFD", text).replace("\u0301", "")


def _load_plan(plan_path: Path) -> dict | None:
    """Load plan YAML, return None if missing or invalid."""
    if not plan_path.exists():
        return None
    try:
        with open(plan_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _read_content(md_path: Path) -> str:
    """Read markdown content file."""
    if not md_path.exists():
        return ""
    return md_path.read_text(encoding="utf-8")


def _load_activities(activities_path: Path) -> list[dict]:
    """Load activities YAML (bare list at root)."""
    if not activities_path.exists():
        return []
    try:
        with open(activities_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Check 1: Vocabulary coverage (stress-normalized)
# ---------------------------------------------------------------------------

_VOCAB_HINT_WORD_RE = re.compile(r"^(\S+)")


def _extract_word_from_hint(hint: str) -> str:
    """Extract the first word from a vocabulary hint string like 'мама (mom) — ...'."""
    m = _VOCAB_HINT_WORD_RE.match(hint.strip())
    return m.group(1) if m else ""


def check_vocab_coverage(
    plan: dict, content_text: str, activities_text: str,
) -> list[PlanAdherenceIssue]:
    """Check that all required vocabulary_hints words appear in content."""
    issues = []
    hints = plan.get("vocabulary_hints", {})
    if not hints:
        return issues

    required = hints.get("required", [])
    content_lower = _strip_stress(content_text.lower())
    activities_lower = _strip_stress(activities_text.lower())
    combined = content_lower + " " + activities_lower

    for hint in required:
        word = _extract_word_from_hint(hint)
        if not word:
            continue
        word_normalized = _strip_stress(word.lower())
        # Use word boundary to avoid matching inside longer words (e.g., кіт ≠ кімната)
        pattern = re.compile(r"(?<!\w)" + re.escape(word_normalized) + r"(?!\w)")
        if not pattern.search(combined):
            issues.append(PlanAdherenceIssue(
                severity="HIGH",
                check_type="VOCAB_NOT_IN_CONTENT",
                section="vocabulary",
                expected=f"Required word '{word}' must appear in content",
                actual="Word not found (after stress-mark normalization)",
                fix_hint=f"Add '{word}' to an appropriate section in the content",
            ))

    return issues


# ---------------------------------------------------------------------------
# Check 2: Structural elements (chart/table/list detection)
# ---------------------------------------------------------------------------

_VISUAL_KEYWORDS = re.compile(
    r"\b(chart|table|list\s+(?:all|of\s+all)|map|display|show)\b",
    re.IGNORECASE,
)

_MARKDOWN_TABLE_RE = re.compile(r"^\|.+\|", re.MULTILINE)
_MARKDOWN_BULLET_RE = re.compile(r"^[-*]\s+\S", re.MULTILINE)
_MARKDOWN_NUMBERED_RE = re.compile(r"^\d+\.\s+\S", re.MULTILINE)


def _section_has_structural_element(section_text: str) -> bool:
    """Check if a section contains a markdown table, bulleted list, or numbered list."""
    return bool(
        _MARKDOWN_TABLE_RE.search(section_text)
        or _MARKDOWN_BULLET_RE.search(section_text)
        or _MARKDOWN_NUMBERED_RE.search(section_text)
    )


def _extract_sections(content: str) -> dict[str, str]:
    """Extract H2 sections from markdown content as name→text."""
    sections: dict[str, str] = {}
    current_name = ""
    current_lines: list[str] = []

    for line in content.split("\n"):
        h2_match = re.match(r"^##\s+(.+)$", line)
        if h2_match:
            if current_name:
                sections[current_name] = "\n".join(current_lines)
            current_name = h2_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_name:
        sections[current_name] = "\n".join(current_lines)

    return sections


def check_structural_elements(
    plan: dict, content_text: str,
) -> list[PlanAdherenceIssue]:
    """Check that plan points with visual keywords produce structural elements."""
    issues = []
    outline = plan.get("content_outline", [])
    if not outline:
        return issues

    sections = _extract_sections(content_text)

    for section_def in outline:
        section_name = section_def.get("section", "")
        points = section_def.get("points", [])

        # Check if any plan point contains visual keywords
        visual_points = []
        for point in points:
            if _VISUAL_KEYWORDS.search(str(point)):
                visual_points.append(str(point))

        if not visual_points:
            continue

        # Find the matching content section
        matched_section_text = None
        section_name_lower = section_name.lower()
        for sec_name, sec_text in sections.items():
            if section_name_lower in sec_name.lower() or sec_name.lower() in section_name_lower:
                matched_section_text = sec_text
                break

        if matched_section_text is None:
            # Section missing entirely — outline_compliance.py handles this
            continue

        if not _section_has_structural_element(matched_section_text):
            issues.append(PlanAdherenceIssue(
                severity="HIGH",
                check_type="MISSING_STRUCTURAL_ELEMENT",
                section=section_name,
                expected=f"Plan point requires visual element: {visual_points[0][:100]}",
                actual="Section contains only prose — no table or bulleted list found",
                fix_hint=f"Add a markdown table or bulleted list to section '{section_name}'",
            ))

    return issues


# ---------------------------------------------------------------------------
# Check 3: Activity count compliance
# ---------------------------------------------------------------------------

def check_activity_counts(
    plan: dict, activities: list[dict],
) -> list[PlanAdherenceIssue]:
    """Check that built activities meet activity_hints item counts."""
    issues = []
    hints = plan.get("activity_hints", [])
    if not hints:
        return issues

    # Build lookup: type → list of built activities of that type
    built: dict[str, list[dict]] = {}
    for act in activities:
        atype = act.get("type", "")
        built.setdefault(atype, []).append(act)

    for hint in hints:
        hint_type = hint.get("type", "")
        raw_items = hint.get("items", 0)
        # Plan YAML may use "12+" or "8+" — extract the integer
        try:
            expected_items = int(str(raw_items).rstrip("+").strip())
        except (ValueError, TypeError):
            expected_items = 0

        if not hint_type or expected_items <= 0:
            continue

        matching = built.get(hint_type, [])
        if not matching:
            issues.append(PlanAdherenceIssue(
                severity="HIGH",
                check_type="ACTIVITY_TYPE_MISSING",
                section=f"activity:{hint_type}",
                expected=f"Plan requires activity type '{hint_type}' with {expected_items} items",
                actual="Activity type not found in built activities",
                fix_hint=f"Add a '{hint_type}' activity with ≥{expected_items} items",
            ))
            continue

        # Count items across all activities of this type
        for act in matching:
            actual_count = _count_activity_items(act)
            if actual_count < expected_items:
                issues.append(PlanAdherenceIssue(
                    severity="HIGH",
                    check_type="ACTIVITY_UNDERCOUNT",
                    section=f"activity:{hint_type}",
                    expected=f"Plan requires ≥{expected_items} items",
                    actual=f"Activity has {actual_count} items",
                    fix_hint=f"Add {expected_items - actual_count} more items to '{hint_type}' activity",
                ))

    return issues


def _count_activity_items(activity: dict) -> int:
    """Count items in an activity regardless of type."""
    # Different activity types use different keys
    if "items" in activity:
        return len(activity["items"])
    if "pairs" in activity:
        return len(activity["pairs"])
    if "groups" in activity:
        return sum(len(g.get("items", [])) for g in activity["groups"])
    if "categories" in activity:
        return sum(len(c.get("items", [])) for c in activity["categories"])
    return 0


# ---------------------------------------------------------------------------
# Check 4: Activity focus compliance
# ---------------------------------------------------------------------------

_FOCUS_KEYWORDS = {
    "false friend": ["false friend", "looks like", "letter.*sound", "≠"],
    "letter_sound": ["letter.*sound", "sound.*letter", "pronunciation"],
    "vocab_translation": ["word.*translation", "meaning", "definition"],
}


def check_activity_focus(
    plan: dict, activities: list[dict],
) -> list[PlanAdherenceIssue]:
    """Check that activity focus descriptions match built activity content."""
    issues = []
    hints = plan.get("activity_hints", [])
    if not hints:
        return issues

    # Build lookup
    built: dict[str, list[dict]] = {}
    for act in activities:
        built.setdefault(act.get("type", ""), []).append(act)

    for hint in hints:
        hint_type = hint.get("type", "")
        focus = hint.get("focus", "")
        if not focus or not hint_type:
            continue

        matching = built.get(hint_type, [])
        if not matching:
            continue  # Missing type handled by check_activity_counts

        # Detect if focus describes a non-standard pattern
        focus_lower = focus.lower()
        is_false_friend = any(
            re.search(pat, focus_lower)
            for pat in _FOCUS_KEYWORDS["false friend"]
        )

        if is_false_friend:
            # Check if the built activity actually tests false friends
            for act in matching:
                act_text = yaml.dump(act, allow_unicode=True).lower()
                has_false_friend_content = any(
                    marker in act_text
                    for marker in ["sound", "/n/", "/s/", "≠", "looks like"]
                )
                if not has_false_friend_content:
                    issues.append(PlanAdherenceIssue(
                        severity="MEDIUM",
                        check_type="ACTIVITY_FOCUS_MISMATCH",
                        section=f"activity:{hint_type}",
                        expected=f"Plan focus: '{focus}'",
                        actual="Built activity appears to use default pattern (e.g., word→translation) instead",
                        fix_hint=f"Rewrite '{hint_type}' activity to match focus: {focus}",
                    ))

    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_plan_adherence(
    md_path: Path,
    plan_path: Path,
    activities_path: Path,
) -> PlanAdherenceResult:
    """Run all plan adherence checks.

    Args:
        md_path: Path to the built .md content file.
        plan_path: Path to the plan YAML file.
        activities_path: Path to the built activities YAML file.

    Returns:
        PlanAdherenceResult with issues and summary.
    """
    result = PlanAdherenceResult()

    plan = _load_plan(plan_path)
    if plan is None:
        return result

    content_text = _read_content(md_path)
    if not content_text:
        return result

    activities = _load_activities(activities_path)
    activities_text = yaml.dump(activities, allow_unicode=True) if activities else ""

    # Run all checks
    checks = [
        ("vocab_coverage", check_vocab_coverage(plan, content_text, activities_text)),
        ("structural_elements", check_structural_elements(plan, content_text)),
        ("activity_counts", check_activity_counts(plan, activities)),
        ("activity_focus", check_activity_focus(plan, activities)),
    ]

    for _name, check_issues in checks:
        result.checks_run += 1
        if not check_issues:
            result.checks_passed += 1
        result.issues.extend(check_issues)

    return result
