"""
Activity pedagogy and alignment checks.

Validates match-up misuse, focus alignment (grammar vs vocab),
answer position bias, activity variety, sequencing, and advanced type presence.
"""

import re
from collections import Counter

from ..config import (
    REQUIRED_ADVANCED_TYPES,
    STAGE_ORDER,
)


_SORTING_PROMPTS = [
    re.compile(r'which\s+(word|one|item)s?\s+(needs?|has|have|is|are|contains?)', re.IGNORECASE),
    re.compile(r'sort\s+(by|into|the)', re.IGNORECASE),
    re.compile(r'categoriz|classif|group\s+(the|these)', re.IGNORECASE),
    re.compile(r'(with|without)\s+(soft sign|\u044c|apostrophe)', re.IGNORECASE),
    re.compile(r'які\s+(слова|з них)', re.IGNORECASE),
    re.compile(r'розсортуй|класифікуй|розділ', re.IGNORECASE),
]


def _is_sorting_prompt(text: str) -> bool:
    """Check if text contains patterns suggesting a sorting task."""
    return any(p.search(text) for p in _SORTING_PROMPTS)


def _has_symmetric_pairs(body: str) -> bool:
    """Check if match-up body has symmetric pairs (X vs variant-of-X)."""
    rows = re.findall(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', body)
    if len(rows) < 4:
        return False
    cyrillic_only = re.compile(r'[^а-яіїєґА-ЯІЇЄҐ]')
    symmetric = 0
    for left, right in rows:
        lc = cyrillic_only.sub('', left)
        rc = cyrillic_only.sub('', right)
        if len(lc) >= 3 and len(rc) >= 3 and lc[:3].lower() == rc[:3].lower():
            symmetric += 1
    return symmetric >= len(rows) * 0.5


def check_matchup_misuse(content: str) -> list[dict]:
    """Detect match-up activities that should be group-sort."""
    violations = []
    matchups = re.findall(
        r'##\s*match-up:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)',
        content, re.DOTALL | re.IGNORECASE)

    for title, body in matchups:
        title_stripped = title.strip()

        if _is_sorting_prompt(title + ' ' + body[:200]):
            violations.append({
                'type': 'ACTIVITY_MISUSE',
                'issue': f"match-up '{title_stripped}' appears to be a sorting task",
                'fix': "Use group-sort instead. Match-up requires semantic pairs (Ukrainian\u2194English, Synonym\u2194Antonym). Sorting by category should be group-sort."
            })
        elif _has_symmetric_pairs(body):
            violations.append({
                'type': 'ACTIVITY_MISUSE',
                'issue': f"match-up '{title_stripped}' has symmetric pairs (X vs variant-of-X)",
                'fix': "This pattern (same word with/without feature) should be group-sort. Match-up expects different concepts that pair logically."
            })

    return violations


def _determine_focus(level_code: str, module_num: int, frontmatter_str: str) -> tuple[bool, bool]:
    """Determine if a B1/B2 module is grammar-focused or vocab-focused."""
    is_grammar = False
    is_vocab = False

    if level_code == 'B1':
        is_grammar = module_num <= 45
        is_vocab = module_num > 45
    elif level_code == 'B2':
        is_grammar = module_num <= 40
        is_vocab = module_num > 40

    fm_lower = frontmatter_str.lower()
    if 'grammar' in fm_lower:
        is_grammar, is_vocab = True, False
    elif 'vocab' in fm_lower or 'vocabulary' in fm_lower:
        is_grammar, is_vocab = False, True

    return is_grammar, is_vocab


def check_activity_focus_alignment(content: str, level_code: str, module_num: int, frontmatter_str: str) -> list[dict]:
    """Check if activities align with grammar vs vocabulary focus (B1/B2).

    Checkpoints are exempt - they use quiz-heavy activity mix for comprehensive testing.
    """
    if level_code not in ['B1', 'B2']:
        return []

    fm_lower = frontmatter_str.lower()
    if 'checkpoint' in fm_lower or 'контрольна точка' in fm_lower:
        return []

    is_grammar, is_vocab = _determine_focus(level_code, module_num, frontmatter_str)

    activity_types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )
    activity_types = [t.lower() for t in activity_types]
    if not activity_types:
        return []

    violations = []
    type_counts = Counter(activity_types)
    grammar_priority = ['error-correction', 'fill-in', 'unjumble', 'cloze']

    if is_grammar:
        priority_count = sum(type_counts.get(t, 0) for t in grammar_priority)
        total = len(activity_types)
        if priority_count < total * 0.3:
            violations.append({
                'type': 'FOCUS_MISMATCH',
                'issue': f"{level_code} M{module_num:02d} is grammar-focused but lacks grammar-priority activities",
                'fix': f"Grammar modules should emphasize: {', '.join(grammar_priority)}. Currently only {priority_count}/{total} activities are grammar-focused."
            })
    elif is_vocab:
        avoid_count = type_counts.get('group-sort', 0)
        if avoid_count >= 2:
            violations.append({
                'type': 'FOCUS_MISMATCH',
                'issue': f"{level_code} M{module_num:02d} is vocab-focused but uses group-sort ({avoid_count}x)",
                'fix': "Vocabulary modules should avoid group-sort (cognitive overload when learning new words). Use match-up, mark-the-words, or translate instead."
            })

    return violations


def check_activity_sequencing(content: str, pedagogy: str) -> list[dict]:
    """Check activity sequencing based on PPP or TTT methodology."""
    violations = []

    activity_stages = []
    for match in re.finditer(
        r'##\s+\w+[^:]*:\s*[^\s]*\[stage:\s*([^\s]+)\]',
        content, re.IGNORECASE
    ):
        activity_stages.append(match.group(1).strip().lower())

    if not activity_stages:
        return violations

    method = 'PPP'
    if pedagogy:
        pedagogy_upper = pedagogy.upper()
        if 'TTT' in pedagogy_upper:
            method = 'TTT'
        elif 'CLIL' in pedagogy_upper or 'NARRATIVE' in pedagogy_upper:
            method = 'CLIL'
    expected_order = STAGE_ORDER.get(method, STAGE_ORDER['PPP'])

    last_valid_idx = -1
    for stage in activity_stages:
        if stage in expected_order:
            current_idx = expected_order.index(stage)
            if current_idx < last_valid_idx:
                violations.append({
                    'type': 'SEQUENCING',
                    'issue': f"Activity stage '{stage}' appears after later stage (expected {method} order)",
                    'fix': f"Reorder activities: {' \u2192 '.join(expected_order)}"
                })
                break
            last_valid_idx = current_idx

    if 'free-production' in set(activity_stages) and 'presentation' not in content.lower() and method == 'PPP':
        violations.append({
            'type': 'SEQUENCING',
            'issue': "Free-production activity found but no Presentation section",
            'fix': "Add Presentation section before Practice activities (PPP methodology)"
        })

    return violations


def check_answer_position_bias(content: str) -> list[dict]:
    """Check if correct answers are always in same position (bias)."""
    violations = []

    activities = re.findall(
        r'##\s+(quiz|select|translate)[^#]*?(?=\n##|\n#\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )

    for activity in activities:
        if isinstance(activity, tuple):
            activity = activity[0]

        questions = re.split(r'\n\d+\.', activity)
        positions = []

        for q in questions:
            options = re.findall(r'-\s*\[([ xX])\]', q)
            for i, opt in enumerate(options):
                if opt.lower() == 'x':
                    positions.append(i + 1)
                    break

        if len(positions) >= 4:
            counts = Counter(positions)
            most_common_pos, most_common_count = counts.most_common(1)[0]
            bias_ratio = most_common_count / len(positions)

            if bias_ratio > 0.7:
                violations.append({
                    'type': 'ANSWER_BIAS',
                    'issue': f"Answer position bias detected: {most_common_count}/{len(positions)} ({bias_ratio:.0%}) answers in position {most_common_pos}",
                    'fix': "Randomize correct answer positions to prevent pattern guessing."
                })

    return violations


def check_activity_variety(content: str) -> list[dict]:
    """Check if same activity type is used too many times."""
    violations = []

    activity_types = re.findall(
        r'##\s*(quiz|match-up|fill-in|true-false|group-sort|unjumble|error-correction|anagram|cloze|select|translate|mark-the-words):',
        content, re.IGNORECASE
    )

    if not activity_types:
        return violations

    type_counts = Counter(t.lower() for t in activity_types)
    total = len(activity_types)

    for act_type, count in type_counts.items():
        if count >= 4 and count / total > 0.4:
            violations.append({
                'type': 'VARIETY',
                'issue': f"Activity type '{act_type}' overused: {count}/{total} activities ({count/total:.0%})",
                'fix': "Use more diverse activity types for better engagement."
            })

    return violations


def check_advanced_activities_presence(found_types: list[str], level_code: str, module_focus: str | None = None) -> list[dict]:
    """Check if advanced levels have required advanced activity types."""
    if module_focus == 'checkpoint':
        return []

    violations = []
    if level_code in ('B2', 'C1', 'C2', 'LIT'):
        req_key = module_focus if module_focus in REQUIRED_ADVANCED_TYPES else 'default'
        required_types = REQUIRED_ADVANCED_TYPES.get(req_key, [])

        for req_type in required_types:
            if req_type not in found_types:
                violations.append({
                    'type': 'MISSING_ADVANCED_ACTIVITY',
                    'severity': 'warning',
                    'issue': f"B2+ module (focus: {module_focus}) missing advanced activity type: {req_type}",
                    'fix': f"Add a {req_type} activity to meet advanced richness standards."
                })

    return violations
