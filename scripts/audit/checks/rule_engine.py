"""Declarative validation rule engine for pedagogical and decodability checks.

Adding a new check = adding a dict entry to RULES. Rules declare their
applicability (levels, module ranges). Evaluator returns issues compatible
with DScreenResult.deterministic_issues format → feeds into Gemini fix loop.

When to use this vs standalone checks: see plan docs. TL;DR: if you can
express it as "find pattern X in modules Y-Z of level L" → rule engine.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

# Type alias for custom check functions
CustomCheckFn = Callable[["ValidationRule", str, str, int], list[dict]]


@dataclass
class ValidationRule:
    """A single declarative validation rule."""

    name: str  # e.g. "NO_IMPERATIVES_EARLY_A1"
    category: str  # "PEDAGOGICAL" | "DECODABILITY" — maps to issue type
    severity: str  # "HIGH" | "MEDIUM"
    description: str  # Human-readable for fix prompts
    fix: str  # Suggested fix for Gemini

    # Applicability (all must match; None = all)
    levels: list[str] | None = None
    module_range: tuple[int, int] | None = None  # inclusive

    # Check mechanism (exactly one set)
    patterns: list[str] | None = None  # Regex (any match = violation)
    charset_check: dict | None = None  # {"allowed": "АаМм...", "section_markers": [...]}
    custom_check: str | None = None  # Function name in _CUSTOM_CHECKS

    case_sensitive: bool = True
    max_hits: int = 5  # Cap findings per rule
    deprecated: bool = False  # Replaced by VESUM morphological validator (#753)


# ---------------------------------------------------------------------------
# Decodability data table — generates rules 3-5
# ---------------------------------------------------------------------------

_BASE_SECTION_MARKERS = [
    "Перші склади", "First Syllables", "First Words",
    "Reading Practice", "Self-Check", "Практика читання",
    "Перевір себе",
]

_DECODABILITY_SPECS: list[tuple[int, str, str, list[str]]] = [
    # (module_num, allowed_chars, description_suffix, extra_markers)
    (1, "АаОоУуМмЛлНнСс",
     "АОУМЛНС (7 letters). Students cannot decode other Cyrillic letters yet.",
     []),
    (2, "АаОоУуМмЛлНнСсКкИиІіРрВвТтЕе",
     "the 14 letters learned so far.",
     ["Reading Drill", "Нові склади"]),
    (3, "АаОоУуМмЛлНнСсКкИиІіРрВвТтЕеБбДдПпЗзГгХхЖжШшЧч",
     "the 23 letters learned so far.",
     ["Reading Drill", "Нові склади"]),
]


def _make_decodability_rules() -> list[ValidationRule]:
    """Generate decodability rules from the specs table."""
    rules = []
    for mod_num, allowed, desc_suffix, extra_markers in _DECODABILITY_SPECS:
        # Build human-readable letter list for fix text
        upper_letters = [c for c in allowed if c.isupper()]
        letter_list = ", ".join(upper_letters)
        rules.append(ValidationRule(
            name=f"DECODABILITY_M{mod_num}",
            category="DECODABILITY",
            severity="HIGH",
            description=f"M{mod_num} reading-drill sections must only use letters "
            f"{desc_suffix}",
            fix=f"Replace words containing unknown letters with words using only "
            f"{letter_list}. Or move the content to a later module.",
            levels=["A1"],
            module_range=(mod_num, mod_num),
            charset_check={
                "allowed": allowed,
                "section_markers": _BASE_SECTION_MARKERS + extra_markers,
            },
        ))
    return rules


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

RULES: list[ValidationRule] = [
    # 1. No imperatives in early A1 (M1-46) — DEPRECATED: replaced by VESUM morphological validator (#753)
    ValidationRule(
        name="NO_IMPERATIVES_EARLY_A1",
        category="PEDAGOGICAL",
        severity="HIGH",
        description="Imperative verb forms should not appear in early A1 modules (M1-46). "
        "Students haven't learned verb conjugation yet.",
        fix="Replace imperative verbs with English instructions or simple noun phrases. "
        "E.g. 'Слухайте уважно!' → 'Listen carefully!' or 'Listening practice:'",
        levels=["A1"],
        module_range=(1, 46),
        patterns=[
            r"\b(?:Слухайте|Читайте|Повторюйте|Пишіть|Дивіться|Спробуйте)\b",
            r"\b(?:Почитаймо|Послухаймо|Подивімось|Попрацюймо)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:йте|іть)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:аймо|яймо|імо)\b",
        ],
        deprecated=True,
    ),
    # 2. No verb conjugation before M15 — DEPRECATED: replaced by VESUM morphological validator (#753)
    ValidationRule(
        name="NO_VERB_CONJUGATION_PRE_M15",
        category="PEDAGOGICAL",
        severity="HIGH",
        description="Conjugated Ukrainian verb forms should not appear before M15. "
        "Students are still learning the alphabet and basic words.",
        fix="Replace conjugated verbs with English equivalents or noun phrases. "
        "E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'",
        levels=["A1"],
        module_range=(1, 14),
        patterns=[
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:ємо|імо)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:иш|їш|єш|аш)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:ите|їте|єте|ате)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:ують|юють|ають|яють|ять)\b",
            r"\b[А-ЯҐЄІЇа-яґєії]+(?:ає|іє|ить)\b",
            r"\b(?:вивчаємо|читаємо|пишемо|говоримо|знаємо|бачимо|робиш|робите|робить|маєш|маєте|має)\b",
        ],
        deprecated=True,
    ),
    # 2b. No non-nominative case forms before M25 — DEPRECATED: replaced by VESUM morphological validator (#753)
    ValidationRule(
        name="NO_OBLIQUE_CASES_PRE_M25",
        category="PEDAGOGICAL",
        severity="HIGH",
        description="Non-nominative case forms should not appear in M5-14 content. "
        "Only nominative case is available at this stage. Exception: memorized "
        "chunks in vocabulary tables or callout boxes.",
        fix="Replace oblique case forms with nominative equivalents or use English. "
        "E.g. 'на роботі' (locative) → 'робота' (nominative) or 'at work' (English). "
        "Exception: memorized phrases in vocabulary tables are OK.",
        levels=["A1"],
        module_range=(5, 14),
        custom_check="check_oblique_cases",
        deprecated=True,
    ),
    # 3-5. Decodability rules (generated from data table)
    *_make_decodability_rules(),
    # 6. Self-check questions in early A1 must contain English
    ValidationRule(
        name="SELF_CHECK_NEEDS_ENGLISH",
        category="PEDAGOGICAL",
        severity="MEDIUM",
        description="Self-check questions in M1-14 must contain English (Latin characters) "
        "so pre-literate students can understand them.",
        fix="Add English translations to self-check questions. "
        "E.g. 'Яка це літера?' → 'What letter is this? / Яка це літера?'",
        levels=["A1"],
        module_range=(1, 14),
        custom_check="check_self_check_english",
    ),
]


# ---------------------------------------------------------------------------
# Applicability filter
# ---------------------------------------------------------------------------

def _rule_applies(rule: ValidationRule, level_code: str, module_num: int,
                  track_code: str) -> bool:
    """Check if a rule applies to this module."""
    if rule.levels is not None and level_code.upper() not in [lv.upper() for lv in rule.levels]:
        return False
    if rule.module_range is not None:
        lo, hi = rule.module_range
        if not (lo <= module_num <= hi):
            return False
    return True


# ---------------------------------------------------------------------------
# Check mechanisms
# ---------------------------------------------------------------------------

# Words that match verb conjugation patterns but are actually nouns/adjectives
_VERB_FALSE_POSITIVES = {
    "університе", "університеті", "алфавіте",
    "інтернеті", "комп'ютері", "документі",
    "має",  # allow as memorized chunk "як справи? — має" in greetings
}


def _check_patterns(rule: ValidationRule, content: str) -> list[dict]:
    """Run regex patterns against content. Any match = violation."""
    issues: list[dict] = []
    flags = 0 if rule.case_sensitive else re.IGNORECASE
    for pattern in (rule.patterns or []):
        for m in re.finditer(pattern, content, flags):
            if len(issues) >= rule.max_hits:
                return issues
            matched = m.group()
            # Skip known false positives for verb rules
            if rule.name.startswith("NO_VERB") and matched.lower() in _VERB_FALSE_POSITIVES:
                continue
            # Find approximate line number
            line_num = content[:m.start()].count("\n") + 1
            issues.append({
                "type": rule.category,
                "severity": rule.severity,
                "text": f"[{rule.name}] '{matched}' — {rule.description}",
                "fix": rule.fix,
                "location": f"~line {line_num}",
            })
    return issues[:rule.max_hits]


def _is_drill_line(line: str) -> bool:
    """Return True if a line is likely a reading-drill line (not metalanguage).

    Drill lines are word lists, syllable grids, or short phrases the student
    reads aloud. We skip:
    - English-majority prose (instructional scaffolding)
    - Markdown headings (section names use metalanguage)
    - Callout labels (> [!tip], > [!culture], etc.)
    - Lines with IPA transcriptions (letter-teaching examples, not drills)
    - Bold metalanguage terms (**Літера**, **Відкриті склади**)
    """
    stripped = line.strip()
    if not stripped:
        return False
    # Skip headings
    if stripped.startswith("#"):
        return False
    # Skip callout type labels (> [!tip] Title)
    if re.match(r">\s*\[!", stripped):
        return False
    # Skip lines with IPA transcriptions — these are letter-teaching examples
    if "[" in stripped and "]" in stripped and any(
        c in stripped for c in "ɐɪɔɛʲˈ"
    ):
        return False
    # Count Cyrillic vs ASCII alphabetic characters
    cyrillic = sum(1 for c in stripped if "\u0400" <= c <= "\u04ff")
    ascii_alpha = sum(1 for c in stripped if c.isascii() and c.isalpha())
    # If line is mostly English, it's instructional prose
    if ascii_alpha > cyrillic and ascii_alpha > 10:
        return False
    # Must have at least some Cyrillic to be a drill line
    return cyrillic > 0


def _check_charset(rule: ValidationRule, content: str) -> list[dict]:
    """Check that reading-drill sections only use allowed characters."""
    cfg = rule.charset_check
    if not cfg:
        return []
    allowed = set(cfg["allowed"])
    markers = cfg.get("section_markers", [])

    # Find reading-drill sections by markers
    sections = _extract_marked_sections(content, markers)
    if not sections:
        return []

    issues: list[dict] = []
    for section_name, section_text, section_start_line in sections:
        for line_offset, line in enumerate(section_text.split("\n")):
            if not _is_drill_line(line):
                continue
            # Extract Ukrainian words (Cyrillic sequences)
            for m in re.finditer(r"[А-ЯҐЄІЇа-яґєії'ʼ]+", line):
                word = m.group().replace("'", "").replace("ʼ", "")
                bad_chars = set(word) - allowed
                if bad_chars:
                    line_num = section_start_line + line_offset
                    issues.append({
                        "type": rule.category,
                        "severity": rule.severity,
                        "text": (
                            f"[{rule.name}] '{m.group()}' in '{section_name}' "
                            f"contains unknown letter(s): {', '.join(sorted(bad_chars))}"
                        ),
                        "fix": rule.fix,
                        "location": f"~line {line_num}",
                    })
                    if len(issues) >= rule.max_hits:
                        return issues
    return issues


def _extract_marked_sections(content: str, markers: list[str]) -> list[tuple[str, str, int]]:
    """Extract text sections that follow marker headings.

    Returns list of (marker_name, section_text, start_line_number).
    A section extends from the marker line to the next heading of equal or
    higher level, or end of file.
    """
    lines = content.split("\n")
    results: list[tuple[str, str, int]] = []

    for i, line in enumerate(lines):
        # Only match markers in actual headings (not prose text)
        if _heading_level(line) == 0:
            continue
        stripped = line.strip().lstrip("#").strip()
        for marker in markers:
            if marker.lower() in stripped.lower():
                # Determine heading level of this marker
                marker_level = _heading_level(line)
                # Collect lines until next heading of equal/higher level
                section_lines: list[str] = []
                for j in range(i + 1, len(lines)):
                    hl = _heading_level(lines[j])
                    if hl > 0 and hl <= marker_level:
                        break
                    section_lines.append(lines[j])
                results.append((marker, "\n".join(section_lines), i + 1))
                break  # Don't match multiple markers on same line
    return results


def _heading_level(line: str) -> int:
    """Return markdown heading level (1-6) or 0 if not a heading."""
    stripped = line.lstrip()
    if stripped.startswith("#"):
        hashes = len(stripped) - len(stripped.lstrip("#"))
        if hashes <= 6 and (len(stripped) == hashes or stripped[hashes] == " "):
            return hashes
    return 0


# ---------------------------------------------------------------------------
# Custom checks
# ---------------------------------------------------------------------------

def _check_self_check_english(rule: ValidationRule, content: str,
                              level_code: str, module_num: int) -> list[dict]:
    """Self-check questions in early A1 must contain Latin characters."""
    issues: list[dict] = []
    sections = _extract_marked_sections(
        content,
        ["Self-Check", "Перевір себе", "Самоперевірка"],
    )
    if not sections:
        return []

    latin_re = re.compile(r"[A-Za-z]")
    for _section_name, section_text, start_line in sections:
        lines = section_text.split("\n")
        for j, line in enumerate(lines):
            stripped = line.strip()
            # Look for question-like lines (numbered, bulleted, or ending with ?)
            if not stripped:
                continue
            is_question = (
                stripped.endswith("?")
                or re.match(r"^\d+[\.\)]\s", stripped)
                or re.match(r"^[-*]\s", stripped)
            )
            if not is_question:
                continue
            # Check if it contains any Latin characters
            if not latin_re.search(stripped):
                line_num = start_line + j
                issues.append({
                    "type": "PEDAGOGICAL",
                    "severity": "MEDIUM",
                    "text": (
                        f"[SELF_CHECK_NEEDS_ENGLISH] Question has no English: "
                        f"'{stripped[:60]}'"
                    ),
                    "fix": "Add English translation so pre-literate students can "
                    "understand the question.",
                    "location": f"~line {line_num}",
                })
                if len(issues) >= rule.max_hits:
                    return issues
    return issues


def _check_oblique_cases(
    rule: ValidationRule, content: str, level_code: str, module_num: int,
) -> list[dict]:
    """Detect non-nominative case usage in M5-14 prose.

    Looks for common preposition+noun patterns that require oblique cases:
    - Locative: на/у/в + locative (на роботі, у місті, в школі)
    - Instrumental: з/із + instrumental (з другом, із сестрою)
    - Genitive: від/до/без + genitive (від мами, до школи)
    - Dative: specific verb patterns

    Skips table rows, vocabulary sections, callout boxes, and memorized phrases.
    """
    issues: list[dict] = []

    # Memorized phrases that use oblique cases but are taught as fixed chunks
    _ALLOWED_CHUNKS = {
        "до побачення", "до зустрічі", "на жаль", "на здоров'я",
        "будь ласка", "з днем", "на добраніч", "до речі",
        "на щастя", "без сумніву", "з повагою",
    }

    # Preposition patterns that force oblique cases
    oblique_patterns = [
        # Locative: на/у/в + noun ending in -і/-ї/-у/-ю (locative endings)
        (r"(?:на|у|в)\s+[а-яґєії]+(?:і|ї|у|ю)\b", "locative"),
        # Instrumental: з/із/зі + noun ending in -ом/-ем/-ою/-ею/-ям/-ями
        (r"(?:зі?|із)\s+[а-яґєії]+(?:ом|ем|ою|ею|ям|ями)\b", "instrumental"),
        # Genitive prepositions: від/до/без/для/біля
        (r"(?:від|до|без|для|біля)\s+[а-яґєії]+(?:и|і|а|я|у|ю)\b", "genitive"),
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip tables, callout boxes, code blocks, vocabulary sections
        if (stripped.startswith("|") or stripped.startswith(">") or
                stripped.startswith("```") or stripped.startswith("---")):
            continue
        # Skip lines that are clearly English-dominant (translation context)
        latin_chars = sum(1 for c in stripped if c.isascii() and c.isalpha())
        cyrillic_chars = sum(1 for c in stripped if '\u0400' <= c <= '\u04ff')
        if latin_chars > cyrillic_chars * 2:
            continue

        for pattern, case_name in oblique_patterns:
            matches = re.findall(pattern, stripped, re.IGNORECASE)
            for match in matches:
                # Skip memorized phrases
                if match.lower() in _ALLOWED_CHUNKS:
                    continue
                if any(match.lower().startswith(chunk) or chunk.startswith(match.lower())
                       for chunk in _ALLOWED_CHUNKS):
                    continue
                issues.append({
                    "type": "PEDAGOGICAL",
                    "severity": rule.severity,
                    "text": (
                        f"[NO_OBLIQUE_CASES_PRE_M25] {case_name} case usage: "
                        f"'{match}' — only nominative allowed in M5-14"
                    ),
                    "fix": rule.fix,
                    "location": f"~line {i}",
                })
                if len(issues) >= rule.max_hits:
                    return issues

    return issues


_CUSTOM_CHECKS: dict[str, CustomCheckFn] = {
    "check_self_check_english": _check_self_check_english,
    "check_oblique_cases": _check_oblique_cases,
}

# Validate all custom_check references at import time
for _rule in RULES:
    if _rule.custom_check and _rule.custom_check not in _CUSTOM_CHECKS:
        raise ValueError(
            f"Rule {_rule.name} references unknown custom check: {_rule.custom_check}"
        )


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _deduplicate(issues: list[dict]) -> list[dict]:
    """Deduplicate by (rule_name extracted from text, match_text first 40 chars)."""
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []
    for issue in issues:
        text = issue.get("text", "")
        # Extract rule name from "[RULE_NAME] ..."
        rule_name = ""
        if text.startswith("["):
            end = text.find("]")
            if end > 0:
                rule_name = text[1:end]
        # Extract matched content (after the rule name)
        match_text = text[text.find("'"):text.find("'", text.find("'") + 1) + 1] if "'" in text else text
        key = (rule_name, match_text[:40])
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_rule_engine(content: str, level_code: str, module_num: int,
                    track_code: str) -> list[dict]:
    """Run all applicable rules against content.

    Args:
        content: Module markdown content.
        level_code: Level code (e.g. "A1", "B2").
        module_num: Module sequence number.
        track_code: Track code (e.g. "a1", "b2-grammar").

    Returns:
        List of issue dicts compatible with DScreenResult.deterministic_issues.
    """
    issues: list[dict] = []
    for rule in RULES:
        if rule.deprecated:
            continue
        if not _rule_applies(rule, level_code, module_num, track_code):
            continue
        if rule.patterns:
            issues.extend(_check_patterns(rule, content))
        elif rule.charset_check:
            issues.extend(_check_charset(rule, content))
        elif rule.custom_check:
            check_fn = _CUSTOM_CHECKS.get(rule.custom_check)
            if check_fn:
                issues.extend(check_fn(rule, content, level_code, module_num))
    return _deduplicate(issues)
