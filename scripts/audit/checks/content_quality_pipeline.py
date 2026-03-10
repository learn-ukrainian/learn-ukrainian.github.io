"""Deterministic content quality checks for the build pipeline.

These checks run inside _deterministic_screen() at zero LLM cost.
They catch issues that the manual /content-review skill finds:
untranslated non-decodable phrases, wall-of-text blocks, missing
engagement boxes, repetitive transitions, plan section coverage gaps.

All functions return list[dict] compatible with DScreenResult.deterministic_issues.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Decodable charsets — mirrors pipeline_lib._DECODABLE_CHARSETS but extended
# to cover M1-M6 (the "non-decodable" window where translations are needed).
# ---------------------------------------------------------------------------

_CUMULATIVE_CHARSETS: dict[int, str] = {
    1: "АаОоУуМмЛлНнСс",
    2: "АаОоУуМмЛлНнСсКкИиІіРрВвТтЕе",
    3: "АаОоУуМмЛлНнСсКкИиІіРрВвТтЕеБбДдПпЗзГгХхЖжШшЧч",
    4: "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",  # M4 completes the alphabet
    5: "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",  # full alphabet
    6: "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",  # full alphabet
}

_CYRILLIC_WORD_RE = re.compile(r"[\u0400-\u04ff][\u0400-\u04ff\u0300\u0301\u0027\u2019'-]*", re.UNICODE)

# Zones to skip when scanning for untranslated words
_SKIP_LINE_PATTERNS = [
    re.compile(r"^\s*\|"),           # table rows (vocabulary tables)
    re.compile(r"^\s*>"),            # blockquotes / callouts
    re.compile(r"^#{1,6}\s"),        # headings
    re.compile(r"^\s*```"),          # code fences
    re.compile(r"^\s*---\s*$"),      # horizontal rules / frontmatter
    re.compile(r"^\s*-\s+\*\*"),     # bold list items (vocab lists)
    re.compile(r"^\s*\*\*"),         # lines starting with bold (vocab/example lines)
]

# Callout label words that appear after > [!type] — skip these
_CALLOUT_LABEL_RE = re.compile(
    r">\s*\[![\w-]+\]\s*([\u0400-\u04ff\w]+)"
)

# Pattern for translation in parentheses: (English text)
_TRANSLATION_PARENS_RE = re.compile(
    r"\(([A-Za-z][A-Za-z\s,;:'\-!?.]+)\)"
)


def _get_charset_upper(module_num: int) -> set[str]:
    """Return the set of uppercase Cyrillic letters known at module N."""
    charset_str = _CUMULATIVE_CHARSETS.get(module_num, "")
    if not charset_str:
        return set()
    return {c.upper() for c in charset_str if c.upper() != c.lower()}


def _is_skip_line(line: str) -> bool:
    """Check if a line should be skipped for untranslated-word scanning."""
    return any(pat.search(line) for pat in _SKIP_LINE_PATTERNS)


def _word_has_translation_after(line: str, match_end: int) -> bool:
    """Check if there's an English translation after the word.

    Handles:
    - word (English)
    - word** (English)  — bold words
    - word — English    — dash-separated headings
    """
    rest = line[match_end:match_end + 150]
    # Strip trailing bold/italic markers
    rest = re.sub(r"^[\*_`'ʼ]+", "", rest)
    rest = rest.lstrip()
    # Check parenthesized translation: (English)
    if rest.startswith("("):
        m = _TRANSLATION_PARENS_RE.match(rest)
        if m:
            return True
    # Check dash-separated translation: — English / - English
    dash_m = re.match(r"^[\s]*[—–\-]\s+([A-Za-z])", rest)
    return bool(dash_m)


def _word_is_in_translation_context(line: str, match_start: int) -> bool:
    """Check if the word is inside a translation parenthetical like (Ukrainian — English)."""
    # Find if we're inside parentheses
    depth = 0
    for _i, c in enumerate(line[:match_start]):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
    return depth > 0


def check_untranslated_non_decodable(
    content: str,
    module_num: int,
    level_code: str = "A1",
) -> list[dict]:
    """Flag Ukrainian words with letters outside the current charset that lack translation.

    Scope: A1 M1-M6 only (before full alphabet is learned).
    """
    issues: list[dict] = []
    if level_code.upper() != "A1" or module_num < 1 or module_num > 6:
        return issues

    known_upper = _get_charset_upper(module_num)
    if not known_upper:
        return issues

    lines = content.split("\n")
    in_frontmatter = False
    # Collect callout label words to skip
    callout_labels: set[str] = set()
    for line in lines:
        cm = _CALLOUT_LABEL_RE.search(line)
        if cm:
            callout_labels.add(cm.group(1).lower())

    seen_words: set[str] = set()  # deduplicate same word across lines

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip frontmatter
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        # Skip non-prose lines
        if _is_skip_line(stripped):
            continue

        for m in _CYRILLIC_WORD_RE.finditer(line):
            word = m.group()
            # Strip stress marks for comparison
            clean_word = word.replace("\u0301", "").replace("\u0300", "")

            # Check if any letter is outside the known charset
            word_upper_letters = {c.upper() for c in clean_word if "\u0400" <= c <= "\u04ff"}
            unknown = word_upper_letters - known_upper
            if not unknown:
                continue

            # Skip callout label words
            if clean_word.lower() in callout_labels:
                continue

            # Skip already-reported words (same clean form)
            if clean_word.lower() in seen_words:
                continue

            # Check if translation follows (handles bold markers, dash separators)
            if _word_has_translation_after(line, m.end()):
                seen_words.add(clean_word.lower())
                continue
            # Check if word is inside a translation parenthetical or guillemets
            if _word_is_in_translation_context(line, m.start()):
                continue
            # Skip words inside guillemets «...» (dialogue examples with context)
            before = line[:m.start()]
            if before.count("«") > before.count("»"):
                continue
            # Check if the line itself contains a translation pattern (word — English)
            if re.search(r"[—–\-]\s+[A-Za-z]", line[m.end():m.end() + 50]):
                seen_words.add(clean_word.lower())
                continue

            seen_words.add(clean_word.lower())
            issues.append({
                "type": "UNTRANSLATED_NON_DECODABLE",
                "severity": "MEDIUM",
                "location": f"~line {line_num}",
                "text": f"'{clean_word}' has letters {unknown} not yet learned (M{module_num})",
                "fix": f"Add English translation after the word: {clean_word} (English meaning)",
            })

    # Cap to avoid overwhelming the review prompt
    return issues[:15]


def check_wall_of_text(content: str) -> list[dict]:
    """Flag paragraphs exceeding 300 words without a visual break.

    A visual break is: heading, callout, table, code fence, horizontal rule,
    or empty line followed by a different structural element.
    """
    issues: list[dict] = []
    lines = content.split("\n")

    # Skip frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                start = i + 1
                break

    para_words = 0
    para_start_line = start + 1

    for i in range(start, len(lines)):
        line = lines[i]
        stripped = line.strip()

        is_break = (
            stripped == ""
            or stripped.startswith("#")
            or stripped.startswith(">")
            or stripped.startswith("|")
            or stripped.startswith("```")
            or stripped == "---"
        )

        if is_break:
            if para_words > 300:
                issues.append({
                    "type": "WALL_OF_TEXT",
                    "severity": "MEDIUM",
                    "location": f"~line {para_start_line}",
                    "text": f"Paragraph of {para_words} words without visual break",
                    "fix": "Break into smaller paragraphs, add a callout box, or insert an example.",
                })
            para_words = 0
            para_start_line = i + 2  # next paragraph
        else:
            para_words += len(stripped.split())

    # Check final paragraph
    if para_words > 300:
        issues.append({
            "type": "WALL_OF_TEXT",
            "severity": "MEDIUM",
            "location": f"~line {para_start_line}",
            "text": f"Paragraph of {para_words} words without visual break",
            "fix": "Break into smaller paragraphs, add a callout box, or insert an example.",
        })

    return issues[:5]


def check_engagement_boxes(
    content: str,
    level_code: str,
) -> list[dict]:
    """Check that content has enough engagement elements (callout boxes).

    Thresholds from non-negotiable-rules.md:
    - B2: 6+, C1: 7+
    - A1-A2: 2+, B1: 4+
    """
    issues: list[dict] = []
    level_upper = level_code.upper().split("-")[0]

    # Read from audit config (source of truth)
    try:
        from audit.config import LEVEL_CONFIG
        min_boxes = LEVEL_CONFIG.get(level_upper, {}).get("min_engagement", 3)
    except Exception:
        min_boxes = 3

    # Count callout boxes: > [!type]
    callout_count = len(re.findall(r">\s*\[!", content))

    if callout_count < min_boxes:
        issues.append({
            "type": "LOW_ENGAGEMENT",
            "severity": "MEDIUM",
            "location": "(whole module)",
            "text": f"Only {callout_count} engagement boxes (minimum: {min_boxes} for {level_upper})",
            "fix": f"Add {min_boxes - callout_count} more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)",
        })

    return issues


def check_repetitive_transitions(content: str) -> list[dict]:
    """Flag sections that start with the same transition pattern.

    If 3+ H2 sections start with the same opening phrase pattern,
    it's likely LLM-generated.
    """
    issues: list[dict] = []

    # Extract first sentence after each H2
    h2_openers: list[tuple[int, str]] = []
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("## "):
            # Find first non-empty prose line after heading
            for j in range(i + 1, min(i + 5, len(lines))):
                stripped = lines[j].strip()
                if stripped and not stripped.startswith(("#", ">", "|", "```", "---", "-")):
                    # Extract first ~8 words as the opener
                    words = stripped.split()[:8]
                    opener = " ".join(words).lower()
                    h2_openers.append((i + 1, opener))
                    break

    if len(h2_openers) < 3:
        return issues

    # Check for repeated opening patterns (first 4 words)
    prefix_counts: dict[str, list[int]] = {}
    for line_num, opener in h2_openers:
        prefix = " ".join(opener.split()[:4])
        prefix_counts.setdefault(prefix, []).append(line_num)

    for prefix, line_nums in prefix_counts.items():
        if len(line_nums) >= 3:
            issues.append({
                "type": "REPETITIVE_TRANSITIONS",
                "severity": "LOW",
                "location": f"~lines {', '.join(str(n) for n in line_nums[:5])}",
                "text": f"{len(line_nums)} sections start with '{prefix}...'",
                "fix": "Vary section openings — repetitive transitions are an LLM pattern.",
            })

    return issues[:3]


def check_plan_section_coverage(
    content: str,
    plan: dict | None,
) -> list[dict]:
    """Check that content covers all plan sections.

    Compares H2 headings against plan content_outline sections.
    """
    issues: list[dict] = []
    if not plan:
        return issues

    content_outline = plan.get("content_outline", [])
    if not content_outline:
        return issues

    # Extract planned section titles
    planned_titles: list[str] = []
    for section in content_outline:
        if isinstance(section, dict):
            title = section.get("title", section.get("section", ""))
        elif isinstance(section, str):
            title = section
        else:
            continue
        if title:
            planned_titles.append(title.strip())

    if not planned_titles:
        return issues

    # Extract actual H2 headings
    actual_h2s = [m.group(1).strip() for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)]

    # Normalize for comparison
    def normalize(s: str) -> str:
        return re.sub(r"[^a-zA-Zа-яА-ЯіІїЇєЄґҐ0-9]", "", s.lower())

    actual_normalized = {normalize(h) for h in actual_h2s}

    missing: list[str] = []
    for title in planned_titles:
        if normalize(title) not in actual_normalized:
            # Fuzzy: check if any actual heading contains the plan title words
            title_words = set(normalize(title))
            found = any(
                len(title_words & set(normalize(h))) > len(title_words) * 0.6
                for h in actual_h2s
            )
            if not found:
                missing.append(title)

    if missing:
        issues.append({
            "type": "PLAN_SECTION_MISSING",
            "severity": "HIGH",
            "location": "(plan vs content)",
            "text": f"Missing {len(missing)} plan section(s): {', '.join(missing[:5])}",
            "fix": "Add content for the missing plan sections or update section headings to match plan.",
        })

    return issues


def _collect_failed_words_from_str(val: str, failed_words: set[str]) -> list[str]:
    """Find VESUM-failed Cyrillic words in a string value."""
    flagged = []
    words = _CYRILLIC_WORD_RE.findall(val)
    for w in words:
        if w.lower() in failed_words:
            flagged.append(w)
    return flagged


def _collect_failed_words_from_value(val, failed_words: set[str]) -> list[str]:
    """Find VESUM-failed Cyrillic words in a string or list of strings."""
    flagged = []
    if isinstance(val, str):
        flagged.extend(_collect_failed_words_from_str(val, failed_words))
    elif isinstance(val, list):
        for item in val:
            if isinstance(item, str):
                flagged.extend(_collect_failed_words_from_str(item, failed_words))
    return flagged


def _scan_activity_answers(act: dict, failed_words: set[str]) -> list[str]:
    """Scan a single activity dict for VESUM-failed words in answer/option fields."""
    flagged: list[str] = []

    # Top-level answer fields
    for key in ("answer", "correct", "correct_answer"):
        flagged.extend(_collect_failed_words_from_value(act.get(key, ""), failed_words))

    # Items/options list
    items = act.get("items", act.get("options", []))
    if not isinstance(items, list):
        return flagged

    for item in items:
        if isinstance(item, dict):
            for key in ("answer", "correct", "text", "prompt", "sentence"):
                flagged.extend(_collect_failed_words_from_value(item.get(key, ""), failed_words))
            # Nested options
            sub_options = item.get("options", item.get("words", []))
            if isinstance(sub_options, list):
                for opt in sub_options:
                    if isinstance(opt, str):
                        flagged.extend(_collect_failed_words_from_str(opt, failed_words))
                    elif isinstance(opt, dict):
                        for key in ("text", "answer", "correct"):
                            flagged.extend(_collect_failed_words_from_value(opt.get(key, ""), failed_words))
        elif isinstance(item, str):
            flagged.extend(_collect_failed_words_from_str(item, failed_words))

    return flagged


def check_activity_answers_vesum(
    activities_path: Path | None,
    vesum_not_found: list[dict] | None,
) -> list[dict]:
    """Cross-reference activity answers against VESUM failures.

    If a word in an activity answer was flagged by VESUM as not found,
    that's a HIGH severity issue — students will practice a non-existent word.
    """
    issues: list[dict] = []
    if not activities_path or not activities_path.exists() or not vesum_not_found:
        return issues

    failed_words = {
        entry.get("original", "").strip().lower()
        for entry in vesum_not_found
        if entry.get("original", "").strip()
    }

    if not failed_words:
        return issues

    try:
        import yaml
        raw = activities_path.read_text("utf-8")
        activities = yaml.safe_load(raw)
        if not isinstance(activities, list):
            return issues
    except Exception:
        return issues

    flagged: list[str] = []
    for act in activities:
        if isinstance(act, dict):
            flagged.extend(_scan_activity_answers(act, failed_words))

    if flagged:
        unique = sorted(set(flagged))[:10]
        issues.append({
            "type": "ACTIVITY_VESUM_FAIL",
            "severity": "HIGH",
            "location": f"{activities_path.name}",
            "text": f"Activity answers contain VESUM-failed words: {', '.join(unique)}",
            "fix": "Fix spelling or replace these words — students will practice non-existent forms.",
        })

    return issues



def run_content_quality_checks(
    content: str,
    level_code: str,
    module_num: int,
    plan: dict | None = None,
    activities_path: Path | None = None,
    vesum_not_found: list[dict] | None = None,
) -> list[dict]:
    """Run all content quality pipeline checks. Returns combined issues list."""
    issues: list[dict] = []

    issues.extend(check_untranslated_non_decodable(content, module_num, level_code))
    issues.extend(check_wall_of_text(content))
    issues.extend(check_engagement_boxes(content, level_code))
    issues.extend(check_repetitive_transitions(content))
    issues.extend(check_plan_section_coverage(content, plan))
    issues.extend(check_activity_answers_vesum(activities_path, vesum_not_found))

    return issues
