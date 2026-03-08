"""
Activity format and content validation checks.

Validates mark-the-words format, hints, error-correction hints,
cloze syntax, malformed activities, and forbidden activity types.
"""

import re

from ..config import LEVEL_CONFIG, VALID_ACTIVITY_TYPES
from .activity_helpers import (
    count_error_correction_placeholders,
    get_field,
    get_items,
    get_title,
    get_type,
    has_hint,
)

# Backward-compatible aliases (private names used by other modules)
_get_title = get_title
_get_field = get_field
_get_items = get_items
_get_type = get_type
_has_hint = has_hint


def _get_mark_the_words_fields(activity) -> tuple[str, str, list]:
    """Extract passage and correct_words from a mark-the-words activity."""
    title = get_title(activity)
    if isinstance(activity, dict):
        passage = activity.get('passage', '') or activity.get('text', '')
        correct_words = activity.get('correct_words', []) or activity.get('answers', [])
    else:
        passage = getattr(activity, 'text', '') or ''
        correct_words = getattr(activity, 'answers', []) or []
    return title, passage, correct_words


def check_mark_the_words_format(activities: list) -> list[dict]:
    """Check for malformed mark-the-words activities in YAML."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        if get_type(activity) != 'mark-the-words':
            continue

        title, passage, correct_words = _get_mark_the_words_fields(activity)

        if not passage:
            violations.append({
                'type': 'MISSING_FIELD',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' is missing 'passage' field",
                'fix': "Add 'passage' field with the content"
            })

        if not correct_words and '*' not in passage:
            violations.append({
                'type': 'MISSING_FIELD',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' is missing 'correct_words' array",
                'fix': "Add 'correct_words' array with correct words"
            })

        if '(correct)' in passage or '(wrong)' in passage:
            violations.append({
                'type': 'MALFORMED_MARK_THE_WORDS',
                'severity': 'critical',
                'issue': f"mark-the-words '{title}' contains (correct)/(wrong) annotations",
                'fix': "Remove (correct)/(wrong) annotations and use 'correct_words' array"
            })

        for ans in correct_words:
            if ans not in passage:
                violations.append({
                    'type': 'INVALID_ANSWER',
                    'severity': 'critical',
                    'issue': f"mark-the-words '{title}' answer '{ans}' not found in passage",
                    'fix': f"Ensure '{ans}' is exactly present in the passage field"
                })

    return violations


def check_hints_in_activities(activities: list) -> list[dict]:
    """Check for hint fields in activities (all should be removed)."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = get_type(activity) or 'unknown'
        title = get_title(activity)

        if has_hint(activity):
            violations.append({
                'type': 'HINT_IN_ACTIVITY',
                'severity': 'critical',
                'issue': f"{act_type} activity '{title}' has activity-level hint field",
                'fix': "Remove all 'hint' fields from activities (they break activities and provide no real pedagogical value)"
            })
            continue

        for idx, item in enumerate(get_items(activity)):
            if has_hint(item):
                violations.append({
                    'type': 'HINT_IN_ACTIVITY',
                    'severity': 'critical',
                    'issue': f"{act_type} activity '{title}' has item-level hint in item {idx + 1}",
                    'fix': "Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)"
                })
                break

    return violations


def _is_error_highlighted(sentence: str, error: str) -> bool:
    """Check if an error word is highlighted with markdown formatting in the sentence."""
    patterns = [
        rf'\*\*{re.escape(error)}\*\*',
        rf'\*{re.escape(error)}\*',
        rf'__{re.escape(error)}__',
        rf'_{re.escape(error)}_',
    ]
    return any(re.search(p, sentence, re.IGNORECASE) for p in patterns)


def check_error_correction_hints(activities: list) -> list[dict]:
    """Check for error-correction activities where the error word is highlighted."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        if get_type(activity) != 'error-correction':
            continue

        title = get_title(activity)

        for idx, item in enumerate(get_items(activity)):
            sentence = get_field(item, 'sentence')
            error = get_field(item, 'error')

            if not sentence or not error:
                continue

            error_str = str(error).strip()
            if _is_error_highlighted(str(sentence), error_str):
                violations.append({
                    'type': 'ERROR_WORD_HIGHLIGHTED',
                    'severity': 'critical',
                    'issue': f"error-correction activity '{title}' item {idx + 1}: error word '{error_str}' is highlighted in sentence (ruins activity)",
                    'fix': f"Remove formatting from '{error_str}' in sentence. Error-correction activities should NOT highlight the error word - students must find it themselves."
                })

    return violations


def _is_dialogue_blank(blank: str) -> bool:
    """Check if a cloze blank contains a dialogue line instead of a word/phrase."""
    for opt in (o.strip() for o in blank.split('|')):
        word_count = len(opt.split())
        has_dialogue_marker = '\u2014' in opt or '\u00ab' in opt or '\u00bb' in opt
        ends_with_punctuation = opt.endswith(('.', '?', '!'))
        if word_count >= 5 and (has_dialogue_marker or ends_with_punctuation):
            return True
    return False


def check_malformed_cloze_activities(activities: list) -> list[dict]:
    """Check for cloze activities with complete sentences as blanks."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'cloze':
            continue

        title = get_title(activity)
        passage = get_field(activity, 'passage')
        if not passage:
            continue

        blanks = re.findall(r'\{([^}]+)\}', passage)
        if not blanks:
            continue

        dialogue_line_count = sum(1 for b in blanks if _is_dialogue_blank(b))
        total_blanks = len(blanks)
        if dialogue_line_count >= total_blanks * 0.5:
            violations.append({
                'type': 'MALFORMED_CLOZE',
                'severity': 'critical',
                'issue': f"Cloze activity '{title}' has dialogue lines as blanks (should be word/phrase blanks)",
                'fix': f"Convert to proper cloze format with word/phrase blanks, or use a different activity type. Found {dialogue_line_count}/{total_blanks} blanks with complete dialogue lines."
            })

    return violations


def check_cloze_syntax_errors(activities: list) -> list[dict]:
    """Check for cloze activities with invalid syntax in blanks."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        if get_type(activity) != 'cloze':
            continue

        title = get_title(activity)
        passage = get_field(activity, 'passage')
        if not passage:
            continue

        blanks = re.findall(r'\{([^}]+)\}', passage)
        invalid_blanks = [
            (b[:50] + '...' if len(b) > 50 else b)
            for b in blanks if ':' in b
        ]

        if invalid_blanks:
            violations.append({
                'type': 'CLOZE_SYNTAX_ERROR',
                'severity': 'critical',
                'issue': f"Cloze activity '{title}' has invalid syntax with colons inside blanks",
                'fix': f"Remove colons from blanks. Use format {{option1|option2|option3}} not {{option1|word: option2}}. Found {len(invalid_blanks)} invalid blanks."
            })

    return violations


def check_error_correction_format(activities: list) -> list[dict]:
    """Check for malformed error-correction activities."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for activity in activities:
        if get_type(activity) != 'error-correction':
            continue

        title = get_title(activity)
        items = get_items(activity)
        placeholder_count = count_error_correction_placeholders(items)

        if placeholder_count > 0:
            violations.append({
                'type': 'MALFORMED_ERROR_CORRECTION',
                'severity': 'critical',
                'issue': f"Error-correction activity '{title}' uses placeholder syntax instead of real errors",
                'fix': f"Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found {placeholder_count}/{len(items)} items with placeholders/missing errors."
            })

    return violations


def check_forbidden_activity_types(activities: list, level_code: str, module_focus: str | None = None) -> list[dict]:
    """Check if activities contain types forbidden for this level/track."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    config_key = f"{level_code}-{module_focus}" if module_focus else level_code
    config = LEVEL_CONFIG.get(config_key, LEVEL_CONFIG.get(level_code, {}))
    forbidden_types = config.get('forbidden_types', set())
    if not forbidden_types:
        return violations

    for i, activity in enumerate(activities):
        act_type_lower = get_type(activity).lower()
        if not act_type_lower:
            continue

        if act_type_lower in forbidden_types:
            title = get_title(activity)
            violations.append({
                'type': 'FORBIDDEN_ACTIVITY_TYPE',
                'severity': 'critical',
                'issue': f"Activity type '{act_type_lower}' is forbidden in {config_key} track (activity: '{title}')",
                'fix': f"Remove this activity. {config_key} allows only seminar-style activities: reading, essay-response, critical-analysis, comparative-study, authorial-intent, true-false (limited).",
                'auto_fix': 'remove_activity',
                'activity_index': i,
                'activity_type': act_type_lower
            })

    return violations


def check_yaml_activity_types(activities: list) -> list[dict]:
    """Check if all activity types in YAML are valid."""
    violations = []

    if not activities or not isinstance(activities, list):
        return violations

    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue

        act_type = activity.get('type', '').lower()
        if not act_type:
            violations.append({
                'type': 'INVALID_ACTIVITY_TYPE',
                'severity': 'error',
                'issue': f"Activity #{i+1} missing 'type' field",
                'fix': "Add 'type' field to activity"
            })
            continue

        if act_type not in VALID_ACTIVITY_TYPES:
            violations.append({
                'type': 'INVALID_ACTIVITY_TYPE',
                'severity': 'error',
                'issue': f"Invalid activity type '{act_type}' in YAML",
                'fix': f"Use supported type: {', '.join(sorted(VALID_ACTIVITY_TYPES))}"
            })

    return violations


def check_activity_header_format(content: str) -> list[dict]:
    """Check if activity headers use the required format: ## activity-type: Title."""
    violations = []

    activity_types_pattern = '|'.join(VALID_ACTIVITY_TYPES)

    malformed_pattern = rf'^##\s*({activity_types_pattern})\s*$'
    malformed_matches = re.findall(malformed_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in malformed_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}' missing required ': Title' suffix",
            'fix': f"Change to '## {act_type}: Descriptive Title' format. Without the colon and title, the MDX generator will skip this activity entirely."
        })

    empty_title_pattern = rf'^##\s*({activity_types_pattern}):\s*$'
    empty_title_matches = re.findall(empty_title_pattern, content, re.MULTILINE | re.IGNORECASE)

    for act_type in empty_title_matches:
        violations.append({
            'type': 'MALFORMED_ACTIVITY_HEADER',
            'issue': f"Activity header '## {act_type}:' has empty title",
            'fix': f"Add a descriptive Ukrainian title after the colon: '## {act_type}: Назва вправи'"
        })

    return violations
