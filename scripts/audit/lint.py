"""
Lint checks for module markdown content.

Checks activity structure, line patterns, AI contamination,
and typography in markdown files.
"""

import re

from .config import AI_CONTAMINATION_PATTERNS, VALID_ACTIVITY_TYPES


def check_typography(content: str) -> list[str]:
    """
    Check for incorrect typography usage (ASCII quotes).

    NOTE: This check is disabled because angular quotes are not compatible
    with YAML files. Since all modern modules use Clean MD architecture with
    activities in YAML sidecars, we don't enforce angular quotes in markdown
    to avoid compatibility issues when content is copied to YAML.
    """
    errors = []
    return errors


def _lint_activity_structure(lines_raw: list[str]) -> list[str]:
    """Check activity section structure: type tracking, fill-in answers, anagram format, hints."""
    lint_errors = []
    in_activities = False
    current_activity_type = None
    fill_in_needs_answer = False

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        if re.match(r'^#{1,2}\s+(Activities|Вправи)', stripped, re.IGNORECASE):
            in_activities = True

        if in_activities and stripped.startswith('## '):
            if fill_in_needs_answer:
                lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                fill_in_needs_answer = False

            parts = stripped.split(':')
            if len(parts) > 1:
                header_type = parts[0].replace('##', '').strip().lower()
                current_activity_type = header_type
            else:
                current_activity_type = None

        if current_activity_type == 'anagram' and re.search(r'\w\s+/\s+\w\s+/', stripped):
            lint_errors.append(f"Line {line_num}: Invalid Anagram format. Use spaces (a b c), not slashes.")

        if in_activities and (stripped.startswith('type: ') or stripped.startswith('items:')):
            lint_errors.append(f"Line {line_num}: YAML detected in Activities. Use markdown.")

        if current_activity_type and current_activity_type not in VALID_ACTIVITY_TYPES:
            lint_errors.append(f"Line {line_num}: Invalid Activity Type '{current_activity_type}'. Supported: {', '.join(VALID_ACTIVITY_TYPES)}.")

        if current_activity_type == 'fill-in':
            if re.match(r'^\d+\.', stripped):
                if fill_in_needs_answer:
                    lint_errors.append(f"Line {line_num}: Previous Fill-in item missing '> [!answer]'.")
                fill_in_needs_answer = True
                if '___' not in stripped:
                    lint_errors.append(f"Line {line_num}: Fill-in item missing '___' placeholder.")

            if '> [!answer]' in stripped:
                fill_in_needs_answer = False

        if current_activity_type == 'true-false' and '> [!explanation]' in stripped:
            lint_errors.append(f"Line {line_num}: T/F Activity contains '[!explanation]'. Remove all hints/solutions.")

        if in_activities and (re.search(r'\[Hint:.*?\]', stripped, re.IGNORECASE) or re.search(r'\(Hint:.*?\)', stripped, re.IGNORECASE) or re.search(r'\bHint:', stripped, re.IGNORECASE)):
                lint_errors.append(f"Line {line_num}: Activity Hint detected. Policy: Remove all hints (e.g. [Hint: ...]) from activities.")

    return lint_errors


def _lint_line_patterns(lines_raw: list[str], module_num: int) -> list[str]:
    """Check per-line format patterns: callouts, checkboxes, audio, headers, transliteration."""
    lint_errors = []

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        if "**Answer:**" in stripped or "**Option:**" in stripped:
            lint_errors.append(f"Line {line_num}: Old format detected. Use '> [!answer]'.")

        if '> [!explanation]' in stripped and '[!answer]' in stripped:
            lint_errors.append(f"Line {line_num}: Malformed Explanation. Contains '[!answer]' inside explanation block.")

        if (stripped.startswith('- [')
                and not re.match(r'- \[[ xX]\]', stripped)
                and '](http' not in stripped  # exclude markdown links (even with nested brackets)
                and not re.match(r'- \[[^\]]+\]\(', stripped)):  # exclude simple markdown links
            lint_errors.append(f"Line {line_num}: Invalid Checkbox format. Use '- [ ]' or '- [x]'.")

        is_vocab_row = (stripped.startswith('|') and stripped.count('|') >= 3)
        if 'audio_' in stripped and not is_vocab_row:
            lint_errors.append(f"Line {line_num}: 'audio_' link detected outside Vocabulary Table. User Rule: Audio links only in Vocab.")

        if re.match(r'^#+\s*$', stripped):
            lint_errors.append(f"Line {line_num}: Empty Header detected (Lonely '#'). Remove or add title.")

        if module_num >= 21 and '|' in stripped:
                lower_stripped = stripped.lower()
                if '| translit' in lower_stripped:
                    lint_errors.append(f"Line {line_num}: Transliteration Column detected in M{module_num} (Policy M21+: None). Remove column.")

    return lint_errors


def _lint_ai_contamination(content: str) -> list[str]:
    """Check for AI contamination patterns (thinking/self-correction artifacts)."""
    lint_errors = []
    lines_raw = content.split('\n')

    for i, line in enumerate(lines_raw):
        line_num = i + 1
        stripped = line.strip()

        for pat in AI_CONTAMINATION_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                if "Wait" in pat and "**" in stripped:
                    continue
                if "Sorry" in pat and "**" in stripped:
                    continue
                if "error-correction" in stripped.lower():
                    continue
                lint_errors.append(f"Line {line_num}: AI Contamination detected ('{pat}'). Remove thinking/self-correction artifacts.")

    return lint_errors


def run_lint_checks(content: str, section_map: dict, module_num: int) -> list[str]:
    """Run markdown lint checks (orchestrator)."""
    lint_errors = []
    lines_raw = content.split('\n')

    lint_errors.extend(check_typography(content))
    lint_errors.extend(_lint_activity_structure(lines_raw))
    lint_errors.extend(_lint_line_patterns(lines_raw, module_num))
    lint_errors.extend(_lint_ai_contamination(content))

    return lint_errors
