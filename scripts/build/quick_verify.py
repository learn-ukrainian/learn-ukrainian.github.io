"""V6 Step 6b: Quick Verify — fast structural check after WRITE.

Runs cheap, deterministic checks on generated content BEFORE exercises
are filled. Catches major failures early so we can retry without wasting
time on exercise generation and stress annotation.

Checks:
1. Structural integrity — all H2 headers from plan present
2. Word count bounds — within ±15% of target
3. Toxic token scan — severe Russianisms, Latin chars in Cyrillic
4. Vocabulary inclusion — core required vocab items appear in prose
5. Exercise items — placeholders/filled exercises match plan activity_hints count

Returns a list of QuickVerifyError. Empty list = PASS.

Issue: #1006
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class QuickVerifyError:
    """A single verification failure."""
    check: str        # e.g. "STRUCTURE", "WORD_COUNT", "TOXIC", "VOCABULARY"
    severity: str     # "ERROR" or "WARNING"
    message: str

    def __str__(self) -> str:
        icon = "❌" if self.severity == "ERROR" else "⚠️"
        return f"  {icon} [{self.check}] {self.message}"


# --- Toxic tokens ---

# Russian-only characters that should NEVER appear in Ukrainian text
RUSSIAN_CHARS = re.compile(r"[ыэёъЫЭЁЪ]")

# Severe Russianisms that indicate wholesale Russian text
SEVERE_RUSSIANISMS = [
    "пожалуйста", "спасибо", "хорошо", "конечно", "потому що",
    "ничего", "сейчас", "тоже", "здесь",
]

# Russian/archaic words that need word-boundary matching (too short for substring)
# Format: (russian_form, correct_ukrainian, description)
WORD_BOUNDARY_RUSSIANISMS = [
    ("кон", "кін", "Russian кон — Ukrainian кін (stage/round)"),
    ("кот", "кіт", "Russian кот — Ukrainian кіт (cat)"),
]

# Latin characters that shouldn't appear in Ukrainian prose
# (but might appear in URLs, code blocks, or English translations)
LATIN_IN_CYRILLIC = re.compile(
    r"(?<=[А-ЯІЇЄҐа-яіїєґ])[A-Za-z]|[A-Za-z](?=[А-ЯІЇЄҐа-яіїєґ])"
)


def _check_structure(content: str, plan: dict) -> list[QuickVerifyError]:
    """Check that all H2 headers from the plan are present in content."""
    errors = []
    sections = plan.get("content_outline", [])

    for section in sections:
        title = section.get("section", "")
        if not title:
            continue

        # Extract the Ukrainian part (before parenthetical English)
        uk_title = re.split(r"\s*\(", title)[0].strip()

        # Check if this heading exists in content (fuzzy — allow minor variations)
        # Look for ## followed by something containing the Ukrainian title
        pattern = re.compile(
            r"^##\s+.*" + re.escape(uk_title[:15]),
            re.MULTILINE | re.IGNORECASE,
        )
        if not pattern.search(content):
            errors.append(QuickVerifyError(
                check="STRUCTURE",
                severity="ERROR",
                message=f"Missing section heading: '{title}'",
            ))

    return errors


def _check_word_count(content: str, plan: dict) -> list[QuickVerifyError]:
    """Check word count is within ±15% of target."""
    errors = []
    target = plan.get("word_target", 1200)

    # Count words (exclude markdown syntax, exercise blocks, meta-notes)
    # Strip ALL fenced blocks (:::anything ... :::) — exercise placeholders AND filled DSL
    text = re.sub(
        r"^:::.*?^:::",
        "",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    # Strip "Content notes" / meta-notes section at end (LLM self-audit artifact)
    # The --- separator before content notes must NOT eat the whole file.
    # Only strip --- followed by "Content notes" or similar meta-sections.
    text = re.sub(r"\*\*Content notes:\*\*.*$", "", text, flags=re.DOTALL)
    text = re.sub(r"\n---\s*\n\*\*(?:Content|Note|Meta).*$", "", text, flags=re.DOTALL)
    # Strip markdown headings, links, images, tables
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)  # table rows
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    words = len(text.split())
    lower = int(target * 0.85)

    if words < lower:
        errors.append(QuickVerifyError(
            check="WORD_COUNT",
            severity="ERROR",
            message=f"Too short: {words} words (target: {target}, minimum: {lower})",
        ))
    # No upper ceiling — word targets are MINIMUMS. More content is always acceptable.

    return errors


def _check_toxic_tokens(content: str) -> list[QuickVerifyError]:
    """Scan for Russian characters, severe Russianisms, Latin-Cyrillic mixing."""
    errors = []

    # Russian characters
    russian_matches = RUSSIAN_CHARS.findall(content)
    if russian_matches:
        chars = ", ".join(set(russian_matches))
        errors.append(QuickVerifyError(
            check="TOXIC",
            severity="ERROR",
            message=f"Russian characters found: {chars}",
        ))

    # Severe Russianisms (case-insensitive)
    content_lower = content.lower()
    found_russianisms = [w for w in SEVERE_RUSSIANISMS if w in content_lower]
    if found_russianisms:
        errors.append(QuickVerifyError(
            check="TOXIC",
            severity="ERROR",
            message=f"Severe Russianisms: {', '.join(found_russianisms)}",
        ))

    # Word-boundary Russianisms (short words that need exact matching)
    found_wb = []
    for russian, ukrainian, _desc in WORD_BOUNDARY_RUSSIANISMS:
        pattern = re.compile(rf"\b{re.escape(russian)}\b", re.IGNORECASE)
        if pattern.search(content):
            found_wb.append(f"{russian}→{ukrainian}")
    if found_wb:
        errors.append(QuickVerifyError(
            check="TOXIC",
            severity="ERROR",
            message=f"Russian/archaic words: {', '.join(found_wb)}",
        ))

    # Latin chars mixed into Cyrillic words (not in code blocks or URLs)
    # Strip code blocks and URLs first
    clean = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    clean = re.sub(r"`[^`]+`", "", clean)
    clean = re.sub(r"https?://\S+", "", clean)
    clean = re.sub(r"\([^)]*https?[^)]*\)", "", clean)

    latin_mixed = LATIN_IN_CYRILLIC.findall(clean)
    if latin_mixed:
        examples = ", ".join(set(latin_mixed[:5]))
        errors.append(QuickVerifyError(
            check="TOXIC",
            severity="WARNING",
            message=f"Latin characters mixed with Cyrillic: {examples}",
        ))

    return errors


def _check_vocabulary(content: str, plan: dict) -> list[QuickVerifyError]:
    """Check that required vocabulary items appear in the prose."""
    errors = []
    vocab = plan.get("vocabulary_hints", {})
    required = vocab.get("required", [])

    if not required:
        return errors

    content_lower = content.lower()
    missing = []

    for item in required:
        if not isinstance(item, str):
            continue
        # Skip descriptive/meta entries (checkpoint modules, etc.)
        # These describe the vocab policy, not actual words to check
        item_lower = str(item).lower()
        if any(skip in item_lower for skip in (
            "recycled", "no new", "all vocabulary from", "revision",
            "checkpoint", "no required", "see m0",
        )):
            continue
        # Extract the Ukrainian word (before parenthetical translation)
        # e.g., "стіл (table, m)" → "стіл"
        word = re.split(r"\s*\(", str(item))[0].strip().lower()
        # For multi-word items like "він, вона, воно", check each
        parts = [p.strip() for p in word.split(",")]
        found = any(p in content_lower for p in parts if len(p) > 1)
        if not found and len(word) > 1:
            missing.append(item)

    if missing:
        # Only ERROR if >30% missing; WARNING otherwise
        ratio = len(missing) / len(required)
        severity = "ERROR" if ratio > 0.3 else "WARNING"
        errors.append(QuickVerifyError(
            check="VOCABULARY",
            severity=severity,
            message=f"Missing {len(missing)}/{len(required)} required vocab: "
                    f"{', '.join(str(m) for m in missing[:5])}",
        ))

    return errors


def _check_exercise_items(content: str, plan: dict) -> list[QuickVerifyError]:
    """Check that exercise placeholders have enough items matching plan activity_hints."""
    errors = []
    activity_hints = plan.get("activity_hints", [])

    if not activity_hints:
        return errors

    # Count INJECT_ACTIVITY markers (current pipeline) + legacy DSL blocks
    activity_markers = re.findall(
        r"<!--\s*INJECT_ACTIVITY:\s*[a-z0-9][a-z0-9-]*\s*-->",
        content,
    )

    # Also check for already-injected JSX activity components
    jsx_activities = re.findall(
        r"^<(Quiz|FillIn|MatchUp|GroupSort|TrueFalse|OddOneOut|DivideWords|CountSyllables|PickSyllables)\b",
        content, re.MULTILINE,
    )

    # Legacy: exercise placeholders and DSL blocks (kept for backward compat)
    placeholders = re.findall(
        r":::exercise-placeholder\s*\n(.*?):::",
        content, re.DOTALL,
    )
    filled_exercises = re.findall(
        r"^:::(quiz|fill-in|match-up|group-sort|true-false)\b",
        content, re.MULTILINE,
    )

    total_exercises = len(activity_markers) + len(jsx_activities) + len(placeholders) + len(filled_exercises)
    expected = len(activity_hints)

    if total_exercises == 0 and activity_hints:
        errors.append(QuickVerifyError(
            check="EXERCISES",
            severity="WARNING",
            message=f"Plan expects {expected} exercise(s) but content has 0 placeholders",
        ))
        return errors

    if total_exercises < expected:
        errors.append(QuickVerifyError(
            check="EXERCISES",
            severity="WARNING",
            message=f"Plan expects {expected} exercise(s) but content has {total_exercises}",
        ))

    return errors


def _check_activity_sequencing(content: str, plan: dict) -> list[QuickVerifyError]:
    """Check that inline activity markers appear AFTER all concepts they test.

    gf-013: An activity that tests multiple concepts (e.g., soft sign AND
    apostrophe) must be placed after ALL those concepts are taught. This is
    critical for Ukrainian where apostrophe rules appear constantly.

    Strategy: parse H2 section positions, parse INJECT_ACTIVITY positions,
    then cross-reference activity hint focus text against section titles.
    """
    errors = []
    activity_hints = plan.get("activity_hints", [])
    if not activity_hints:
        return errors

    # Build a map: activity hint focus → keywords for matching
    # e.g., "Does this word have a soft sign, apostrophe, or neither?" → ["soft sign", "apostrophe"]
    _CONCEPT_KEYWORDS = {
        "apostrophe": ["апостроф", "apostrophe", "апо́стро́ф"],
        "soft sign": ["м'який знак", "soft sign", "м'яки́й знак", "missing ь", "missing Ь"],
        "voiced": ["дзвінкі", "voiced", "voiceless", "глухі"],
        "г vs ґ": ["вимова", "pronounc", "г vs ґ", "ґ"],
    }

    # Find H2 section positions (line numbers)
    lines = content.split("\n")
    section_positions: dict[str, int] = {}  # concept_key → first line where taught
    for i, line in enumerate(lines):
        if line.startswith("## "):
            title_lower = line.lower()
            for concept, keywords in _CONCEPT_KEYWORDS.items():
                if any(kw.lower() in title_lower for kw in keywords) and concept not in section_positions:
                    section_positions[concept] = i

    # Find ALL INJECT_ACTIVITY marker positions (including duplicates)
    marker_occurrences: list[tuple[str, int]] = []  # (marker_id, line_number)
    for i, line in enumerate(lines):
        m = re.match(r"<!--\s*INJECT_ACTIVITY:\s*([a-z0-9][a-z0-9-]*)\s*-->", line)
        if m:
            marker_occurrences.append((m.group(1), i))

    # Cross-reference: for each activity hint, check if its marker appears
    # after all concepts mentioned in the hint's focus text
    for hint in activity_hints:
        focus = (hint.get("focus", "") or "").lower()
        if not focus:
            continue

        # Find which concepts this activity tests
        tested_concepts = []
        for concept, keywords in _CONCEPT_KEYWORDS.items():
            if any(kw.lower() in focus for kw in keywords):
                tested_concepts.append(concept)

        if len(tested_concepts) < 2:
            # Single-concept activities can't have sequencing issues
            continue

        # Find markers for this hint (match by type in marker id)
        hint_type = hint.get("type", "")
        matching_markers = [
            (mid, pos) for mid, pos in marker_occurrences
            if hint_type in mid
        ]

        for marker_id, marker_line in matching_markers:
            # Check that ALL tested concepts have a section BEFORE this marker
            for concept in tested_concepts:
                section_line = section_positions.get(concept)
                if section_line is not None and marker_line < section_line:
                    errors.append(QuickVerifyError(
                        check="ACTIVITY_SEQUENCE",
                        severity="ERROR",
                        message=(
                            f"Activity marker '<!-- INJECT_ACTIVITY: {marker_id} -->' "
                            f"(line {marker_line + 1}) tests '{concept}' but appears "
                            f"BEFORE the section that teaches it (line {section_line + 1}). "
                            f"Move the marker after all tested concepts are taught."
                        ),
                    ))

    return errors


def quick_verify(content: str, plan: dict) -> list[QuickVerifyError]:
    """Run all quick verification checks.

    Args:
        content: Generated markdown content.
        plan: Parsed plan YAML dict.

    Returns:
        List of QuickVerifyError. Empty = PASS.
    """
    errors = []
    errors.extend(_check_structure(content, plan))
    errors.extend(_check_word_count(content, plan))
    errors.extend(_check_toxic_tokens(content))
    errors.extend(_check_vocabulary(content, plan))
    errors.extend(_check_exercise_items(content, plan))
    errors.extend(_check_activity_sequencing(content, plan))
    return errors


def has_errors(results: list[QuickVerifyError]) -> bool:
    """Check if any results are ERROR severity (not just warnings)."""
    return any(r.severity == "ERROR" for r in results)


def format_results(results: list[QuickVerifyError]) -> str:
    """Format results for logging."""
    if not results:
        return "  ✅ Quick verify PASSED — all structural checks clean"

    lines = []
    error_count = sum(1 for r in results if r.severity == "ERROR")
    warn_count = sum(1 for r in results if r.severity == "WARNING")

    if error_count:
        lines.append(f"  ❌ Quick verify FAILED — {error_count} error(s), {warn_count} warning(s)")
    else:
        lines.append(f"  ⚠️ Quick verify PASSED with {warn_count} warning(s)")

    for r in results:
        lines.append(str(r))

    return "\n".join(lines)


def build_correction_directive(results: list[QuickVerifyError]) -> str:
    """Build a correction directive for retry prompt from verify errors.

    Returns a <correction_directive> block that goes at the TOP of the
    retry prompt. Does NOT include failed output (prevents anchoring).
    """
    if not results:
        return ""

    lines = ["<correction_directive>",
             "CRITICAL: Your previous attempt failed the following checks. "
             "Write the module FROM SCRATCH. All original constraints still apply.\n"]

    for r in results:
        if r.severity == "ERROR":
            lines.append(f"- FIX: {r.message}")

    for r in results:
        if r.severity == "WARNING":
            lines.append(f"- NOTE: {r.message}")

    lines.append("</correction_directive>")
    return "\n".join(lines)


# CLI for testing
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Quick verify V6 content")
    parser.add_argument("content", type=Path, help="Path to generated content .md")
    parser.add_argument("plan", type=Path, help="Path to plan .yaml")
    args = parser.parse_args()

    content_text = args.content.read_text("utf-8")
    plan_data = yaml.safe_load(args.plan.read_text("utf-8"))

    results = quick_verify(content_text, plan_data)
    print(format_results(results))

    if has_errors(results):
        print("\n" + build_correction_directive(results))
        sys.exit(1)
