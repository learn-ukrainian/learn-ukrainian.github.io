"""
Activity-related validation checks.

Validates activity complexity, level restrictions, and re-exports
from submodules for backward compatibility.
"""

import re
import sys
from pathlib import Path

from ..config import (
    ACTIVITY_COMPLEXITY,
    ACTIVITY_RESTRICTIONS,
)

# Re-export from activity_counting for backward compatibility
from .activity_counting import (
    check_activity_ukrainian_content,
    check_anagram_min_letters,
    check_resources_placement,
    check_resources_required,
    check_unjumble_word_match,
    count_items,
)

# Re-export from activity_format_checks for backward compatibility
from .activity_format_checks import (
    check_activity_header_format,
    check_cloze_syntax_errors,
    check_error_correction_format,
    check_error_correction_hints,
    check_forbidden_activity_types,
    check_hints_in_activities,
    check_malformed_cloze_activities,
    check_mark_the_words_format,
    check_yaml_activity_types,
)

# Re-export from activity_pedagogy_checks for backward compatibility
from .activity_pedagogy_checks import (
    check_activity_focus_alignment,
    check_activity_sequencing,
    check_activity_variety,
    check_advanced_activities_presence,
    check_answer_position_bias,
    check_matchup_misuse,
)

# Add parent dir to path for imports
SCRIPT_DIR = Path(__file__).parent.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
from yaml_activities import Activity


def _apply_a1_early_relaxations(rules: dict, act_type: str) -> None:
    """Apply relaxed complexity rules for A1 M01-M05 (alphabet phase)."""
    relaxations = {
        'quiz': {'min_len': 1},  # Single-word prompts valid for phonetics/syllable quizzes
        'match-up': {'pairs_max': 15},
        'group-sort': {'items_min': 6, 'items_max': 30, 'groups_min': 2},
        'fill-in': {'min_items': 6},
    }
    if act_type in relaxations:
        rules.update(relaxations[act_type])


def _apply_b1_bridge_relaxations(rules: dict, act_type: str) -> None:
    """Apply relaxed complexity rules for B1 M01-M05 (bridge modules)."""
    relaxations = {
        'quiz': {'min_len': 5, 'max_len': 20},
        'unjumble': {'words_min': 6, 'words_max': 16},
        'match-up': {'pairs_min': 12, 'pairs_max': 18},
        'fill-in': {'sent_min': 6, 'sent_max': 14},
        'true-false': {'min_len': 6, 'max_len': 18},
        'group-sort': {'groups_min': 2, 'groups_max': 5, 'items_min': 12},
        'error-correction': {'errors': 1, 'min_len': 6, 'max_len': 10},
        'cloze': {'sentences': [3, 4, 5], 'blanks': [3, 4]},
        'mark-the-words': {'min_len': 8, 'max_len': 12, 'marks': [2, 3, 4]},
        'select': {'min_len': 6, 'max_len': 10, 'options': [4, 5], 'correct': [2, 3]},
        'translate': {'min_len': 4, 'max_len': 8},
    }
    if act_type in relaxations:
        rules.update(relaxations[act_type])


def _check_structural_requirements(act_type: str, title: str, body: str, act_obj) -> list[dict]:
    """Check structural requirements (model-answer, rubric) for advanced activity types."""
    violations = []
    if act_type == 'essay-response' and not act_obj:
        if '> [!model-answer]' not in body:
            violations.append({
                'type': 'STRUCTURE_MISSING',
                'issue': f"essay-response '{title}' missing mandatory > [!model-answer]",
                'fix': "All essay responses must include a model answer."
            })
        if '> [!rubric]' not in body:
            violations.append({
                'type': 'STRUCTURE_MISSING',
                'issue': f"essay-response '{title}' missing mandatory > [!rubric]",
                'fix': "All essay responses must include a rubric."
            })
    if act_type in ('critical-analysis', 'comparative-study', 'authorial-intent') and not act_obj and '> [!model-answer]' not in body:
        violations.append({
            'type': 'STRUCTURE_MISSING',
            'issue': f"{act_type} '{title}' missing mandatory > [!model-answer]",
            'fix': f"All {act_type} activities must include a model answer."
        })
    return violations


def _check_group_sort_counts(title: str, items_count: int, rules: dict, act_obj, body: str) -> list[dict]:
    """Check group-sort group and item counts."""
    violations = []
    if act_obj:
        group_count = len(act_obj.groups)
    else:
        group_headers = re.findall(r'^\s*###\s+([^\n]+)', body, re.MULTILINE)
        group_count = len([h for h in group_headers if not any(
            skip in h.lower() for skip in ['note', 'explanation', 'hint', 'tip']
        )])

    min_g, max_g = rules.get('groups_min', 2), rules.get('groups_max', 4)
    if not (min_g <= group_count <= max_g):
        violations.append({
            'type': 'COMPLEXITY',
            'issue': f"group-sort '{title}' has {group_count} groups (target: {min_g}-{max_g})",
            'fix': f"Adjust number of sorting categories to {min_g}-{max_g}."
        })

    min_i, max_i = rules.get('items_min', 8), rules.get('items_max', 20)
    if not (min_i <= items_count <= max_i):
        violations.append({
            'type': 'COMPLEXITY',
            'issue': f"group-sort '{title}' has {items_count} items (target: {min_i}-{max_i})",
            'fix': f"Adjust number of items to sort to {min_i}-{max_i}."
        })
    return violations


def _check_item_count(act_type: str, title: str, items_count: int, rules: dict,
                      act_obj, body: str, level_code: str) -> list[dict]:
    """Check item/group/pair counts against complexity rules."""
    if act_type == 'group-sort':
        return _check_group_sort_counts(title, items_count, rules, act_obj, body)

    if act_type == 'match-up':
        min_p, max_p = rules.get('pairs_min', 8), rules.get('pairs_max', 18)
        if not (min_p <= items_count <= max_p):
            return [{'type': 'COMPLEXITY',
                     'issue': f"match-up '{title}' has {items_count} pairs (target: {min_p}-{max_p})",
                     'fix': f"Adjust number of pairs to {min_p}-{max_p}."}]
        return []

    min_items = rules.get('min_items', 6)
    if items_count < min_items:
        return [{'type': 'COMPLEXITY',
                 'issue': f"{act_type} '{title}' has {items_count} items (minimum: {min_items})",
                 'fix': f"Add more items. {level_code} {act_type} requires at least {min_items} items."}]
    return []


def _check_unjumble_complexity(title: str, body: str, act_obj, items_count: int,
                                rules: dict, level_code: str) -> list[dict]:
    """Check unjumble format and word count complexity."""
    violations = []

    if not act_obj and len(re.findall(r'/', body)) < items_count:
            violations.append({
                'type': 'FORMAT_ERROR',
                'issue': f"unjumble '{title}' items must use slash '/' separator",
                'fix': "Split words with slashes, e.g. '\u042f / \u043b\u044e\u0431\u043b\u044e / \u043a\u0430\u0432\u0443'."
            })

    items_to_check = []
    if act_obj:
        for item in act_obj.items:
            if hasattr(item, 'words') and isinstance(item.words, list):
                items_to_check.append(' '.join(item.words))
            elif hasattr(item, 'words'):
                items_to_check.append(str(item.words))
    else:
        items_to_check = re.findall(r'\d+\.\s*([^\n>]+)', body)

    min_w, max_w = rules.get('words_min', 4), rules.get('words_max', 20)
    for i, item in enumerate(items_to_check, 1):
        words = len(re.findall(r'[\w\u0400-\u04FF]+', item))
        if words < min_w - 1 or words > max_w + 2:
            violations.append({
                'type': 'COMPLEXITY_WORD_COUNT',
                'issue': f"unjumble '{title}' item {i} has {words} words (target: {min_w}-{max_w})",
                'fix': f"Adjust sentence length to {min_w}-{max_w} words to match {level_code} complexity."
            })
    return violations


def _check_quiz_complexity(title: str, body: str, act_obj, rules: dict,
                           level_code: str) -> list[dict]:
    """Check quiz prompt length and option count complexity."""
    violations = []
    quiz_items = act_obj.items if act_obj else []

    min_len, max_len = rules.get('min_len', 5), rules.get('max_len', 30)

    for i, q in enumerate(quiz_items, 1):
        prompt = getattr(q, 'question', '')
        prompt_words = len(re.findall(r'[\w\u0400-\u04FF]+', prompt))
        if prompt_words < min_len or prompt_words > max_len + 5:
            violations.append({
                'type': 'COMPLEXITY_WORD_COUNT',
                'issue': f"quiz '{title}' Q{i} prompt length {prompt_words} (target: {min_len}-{max_len})",
                'fix': f"Adjust prompt length to {min_len}-{max_len} words."
            })

        options_count = len(q.options)
        target_opts = rules.get('options', [4])
        if isinstance(target_opts, int):
            target_opts = [target_opts]
        if options_count > 0 and options_count not in target_opts and options_count < min(target_opts):
            violations.append({
                'type': 'COMPLEXITY_OPTIONS',
                'issue': f"quiz '{title}' Q{i} has {options_count} options (target: {target_opts})",
                'fix': f"Provide {target_opts} options for {level_code} quizzes."
            })
    return violations


def _resolve_complexity_rules(act_type: str, level_code: str, module_focus: str | None) -> dict | None:
    """Resolve complexity rules for an activity type."""
    if act_type not in ACTIVITY_COMPLEXITY:
        return None
    context_key = f"{level_code}-{module_focus}" if module_focus else None
    if context_key and context_key in ACTIVITY_COMPLEXITY[act_type]:
        return ACTIVITY_COMPLEXITY[act_type][context_key].copy()
    if level_code in ACTIVITY_COMPLEXITY[act_type]:
        return ACTIVITY_COMPLEXITY[act_type][level_code].copy()
    return None


def _check_single_activity(act_type: str, title: str, act_obj,
                           rules: dict, level_code: str) -> list[dict]:
    """Run all complexity checks on a single activity."""
    violations = _check_structural_requirements(act_type, title, '', act_obj)
    items_count = count_items('', act_obj)
    violations.extend(_check_item_count(act_type, title, items_count, rules, act_obj, '', level_code))

    if act_type == 'unjumble':
        violations.extend(_check_unjumble_complexity(title, '', act_obj, items_count, rules, level_code))
    elif act_type == 'quiz':
        violations.extend(_check_quiz_complexity(title, '', act_obj, rules, level_code))
    return violations


def check_activity_complexity(content: str, level_code: str, module_num: int = 1,
                              yaml_activities: list[Activity] | None = None,
                              module_focus: str | None = None) -> list[dict]:
    """Check if activities meet complexity requirements for the level."""
    if not yaml_activities:
        return []

    violations = []
    is_a1_early = (level_code == 'A1' and module_num <= 3)  # V2: only M01-M03 are phonetics
    is_b1_bridge = (level_code == 'B1' and module_num <= 5)

    for act in yaml_activities:
        rules = _resolve_complexity_rules(act.type, level_code, module_focus)
        if not rules:
            continue

        if is_a1_early:
            _apply_a1_early_relaxations(rules, act.type)
        if is_b1_bridge:
            _apply_b1_bridge_relaxations(rules, act.type)

        violations.extend(_check_single_activity(
            act.type, getattr(act, 'title', 'Untitled'), act, rules, level_code))

    return violations


def _extract_activity_types(content: str, yaml_activities) -> list[str]:
    """Extract activity types from YAML activities or markdown content."""
    if yaml_activities:
        return [getattr(a, 'type', '').lower() for a in yaml_activities if hasattr(a, 'type')]
    types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )
    return [t.lower() for t in types]


def _check_anagram_restrictions(activity_types: list[str], rules: dict,
                                 level_code: str, module_num: int) -> list[dict]:
    """Check anagram and unjumble level restrictions."""
    violations = []
    if 'anagram' in activity_types:
        if rules.get('anagram_forbidden'):
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity 'anagram' not allowed at {level_code}",
                'fix': "Anagram is only for A1 M01-M10 (Cyrillic scaffolding). Use unjumble instead."
            })
        elif level_code == 'A1' and module_num > rules.get('anagram_limit', 10):
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity 'anagram' should be phased out after A1 M10 (current: M{module_num:02d})",
                'fix': "Anagram is for Cyrillic scaffolding only. Use unjumble for word-ordering practice."
            })

    if 'unjumble' in activity_types:
        anagram_limit = rules.get('anagram_limit', 0)
        if level_code == 'A1' and anagram_limit and module_num <= anagram_limit:
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity 'unjumble' not appropriate for A1 M01-M{anagram_limit:02d} (current: M{module_num:02d})",
                'fix': "A1 M01-M10 students are still learning letters. Use anagram (letter scramble) instead of unjumble (sentence reorder)."
            })
    return violations


def check_activity_level_restrictions(content: str, level_code: str, module_num: int, yaml_activities=None) -> list[dict]:
    """Check if activities are appropriate for the level."""
    activity_types = _extract_activity_types(content, yaml_activities)
    if not activity_types:
        return []

    violations = []
    rules = ACTIVITY_RESTRICTIONS.get(level_code, {})

    # Checkpoint modules (consolidation) get relaxed restrictions —
    # error-correction is valid for testing knowledge the learner already has
    _CHECKPOINT_RELAXED = {'error-correction', 'select', 'translate'}
    is_checkpoint = 'checkpoint' in (content[:500].lower())

    for forbidden in rules.get('forbidden', []):
        if forbidden in activity_types:
            if is_checkpoint and forbidden in _CHECKPOINT_RELAXED:
                continue  # Allow in checkpoints
            violations.append({
                'type': 'LEVEL_RESTRICTION',
                'issue': f"Activity '{forbidden}' not allowed at {level_code}",
                'fix': f"Use level-appropriate activities. '{forbidden}' is introduced at A2+."
            })

    violations.extend(_check_anagram_restrictions(activity_types, rules, level_code, module_num))
    return violations
