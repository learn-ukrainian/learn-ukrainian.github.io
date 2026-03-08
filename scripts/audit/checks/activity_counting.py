"""
Activity item counting and content language checks.

Handles counting items in activities (both YAML and legacy markdown)
and checking Ukrainian content ratios.
"""

import re
import sys
from pathlib import Path

from ..config import VALID_ACTIVITY_TYPES

SCRIPT_DIR = Path(__file__).parent.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
from yaml_activities import Activity


def _count_yaml_items(activity: Activity) -> int:
    """Count items in a YAML Activity object by type."""
    from yaml_activities import (
        AnagramActivity,
        AuthorialIntentActivity,
        ClassifyActivity,
        ClozeActivity,
        ComparativeStudyActivity,
        CriticalAnalysisActivity,
        ErrorCorrectionActivity,
        EssayResponseActivity,
        EtymologyTraceActivity,
        FillInActivity,
        GrammarIdentifyActivity,
        GroupSortActivity,
        ImageToLetterActivity,
        MarkTheWordsActivity,
        MatchUpActivity,
        QuizActivity,
        ReadingActivity,
        SelectActivity,
        TranslateActivity,
        TrueFalseActivity,
        UnjumbleActivity,
        WatchAndRepeatActivity,
    )

    if isinstance(activity, (QuizActivity, FillInActivity, UnjumbleActivity,
                             ErrorCorrectionActivity, TranslateActivity, AnagramActivity,
                             SelectActivity, TrueFalseActivity,
                             EtymologyTraceActivity, GrammarIdentifyActivity,
                             ImageToLetterActivity, WatchAndRepeatActivity)):
        return len(activity.items)
    elif isinstance(activity, MatchUpActivity):
        return len(activity.pairs)
    elif isinstance(activity, GroupSortActivity):
        return sum(len(group.items) for group in activity.groups)
    elif isinstance(activity, ClassifyActivity):
        return sum(len(cat.items) for cat in activity.categories)
    elif isinstance(activity, ClozeActivity):
        if activity.blanks:
            return len(activity.blanks)
        return len(re.findall(r'\{[^}|]+\|[^}]+\}', activity.passage))
    elif isinstance(activity, MarkTheWordsActivity):
        if activity.answers:
            return len(activity.answers)
        return len(re.findall(r'\*([^\*]+)\*', activity.text))
    elif isinstance(activity, ReadingActivity):
        count = 0
        if activity.text:
            count = 1
        if activity.tasks:
            count = max(count, len(activity.tasks))
        return count
    elif isinstance(activity, (EssayResponseActivity, CriticalAnalysisActivity,
                               ComparativeStudyActivity, AuthorialIntentActivity)):
        return 1

    # Handle single-exercise types
    act_type = getattr(activity, 'type', '')
    if act_type in ('transcription', 'phonology-lab', 'parallel-text',
                    'paleography-analysis', 'historical-writing', 'register-identify',
                    'loanword-trace', 'comparative-style'):
        return 1
    return 0


def _count_markdown_items(text: str) -> int:
    """Count items in a markdown activity section."""
    numbered = len(re.findall(r'^\s*\d+\.', text, re.MULTILINE))

    table_lines = [
        line for line in text.split('\n')
        if line.strip().startswith('|') and '---' not in line
    ]
    table_count = max(0, len(table_lines) - 1) if table_lines else 0

    checkboxes = len(re.findall(r'^\s*-\s*\[[ xX]?\]', text, re.MULTILINE))
    bullets = len(re.findall(r'^\s*-\s+[^\s]', text, re.MULTILINE))

    cloze_numbered = len(re.findall(r'\{\d+(?::[^}]+)?\}', text))
    cloze_inline = len(re.findall(r'\{[^}|]+\|[^}]+\}', text))
    cloze_placeholders = cloze_numbered + cloze_inline

    mark_words_brackets = len([
        m for m in re.findall(r'\[([^\]]+)\]', text)
        if not m.startswith('!') and not re.match(r'[^\s]+\]\(', m)
    ])
    mark_words_asterisks = len(re.findall(r'\*[^\*]+\*', text))
    mark_words = mark_words_brackets + mark_words_asterisks

    if numbered > 0:
        return numbered
    elif table_count > 0:
        return table_count
    elif cloze_placeholders > 0:
        return cloze_placeholders
    elif mark_words > 0:
        return mark_words
    elif checkboxes > 0:
        return checkboxes
    else:
        return bullets


def count_items(text: str, activity: Activity | None = None) -> int:
    """Count items in an activity section (Markdown or YAML Activity object)."""
    if activity:
        return _count_yaml_items(activity)
    return _count_markdown_items(text)


def check_activity_ukrainian_content(content: str, level_code: str = 'A1', module_num: int = 1) -> list[dict]:
    """Check if activities contain Ukrainian content (not just English)."""
    violations = []

    if level_code == 'A1' and module_num <= 2:
        return violations

    activity_pattern = r'##\s*([a-z-]+):\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    activities = re.findall(activity_pattern, content, re.DOTALL | re.IGNORECASE)

    min_cyrillic_ratio = 0.10
    if level_code in ['B1', 'B2', 'C1', 'C2']:
        min_cyrillic_ratio = 0.20

    for act_type, title, body in activities:
        act_type_lower = act_type.lower()

        if act_type_lower not in VALID_ACTIVITY_TYPES:
            continue
        if act_type_lower == 'anagram':
            continue

        text = title + ' ' + body

        clean_text = re.sub(r'\[[ xX]?\]', '', text)
        clean_text = re.sub(r'\|', '', clean_text)
        clean_text = re.sub(r'[#*_>`~\-]', '', clean_text)
        clean_text = re.sub(r'\{[^}]+\}', '', clean_text)

        cyrillic_chars = len(re.findall(r'[\u0430-\u044f\u0456\u0457\u0454\u0491\u0410-\u042f\u0406\u0407\u0404\u0490]', clean_text))
        latin_chars = len(re.findall(r'[a-zA-Z]', clean_text))
        total_text_chars = cyrillic_chars + latin_chars

        if total_text_chars < 20:
            continue

        cyrillic_ratio = cyrillic_chars / total_text_chars if total_text_chars > 0 else 0

        if cyrillic_ratio < min_cyrillic_ratio:
            violations.append({
                'type': 'NO_UKRAINIAN_CONTENT',
                'issue': f"Activity '{act_type}: {title.strip()}' has only {cyrillic_ratio:.0%} Ukrainian content ({cyrillic_chars}/{total_text_chars} chars)",
                'fix': "Activities must contain Ukrainian examples/sentences/words. Rewrite with Ukrainian content."
            })

    return violations


def check_anagram_min_letters(content: str, yaml_activities=None) -> list[dict]:
    """Check anagram items: space-separated format, letter count matches answer, min 3 letters."""
    violations = []

    if yaml_activities:
        for activity in yaml_activities:
            if not hasattr(activity, 'type') or activity.type != 'anagram':
                continue
            title = getattr(activity, 'title', 'Untitled')
            for i, item in enumerate(getattr(activity, 'items', []), 1):
                violations.extend(_check_anagram_item(title, i, item))
    else:
        anagram_pattern = r'##\s*anagram:\s*([^\n]+)\n(.*?)(?=\n##|\n#\s|\Z)'
        anagrams = re.findall(anagram_pattern, content, re.DOTALL | re.IGNORECASE)
        for title, body in anagrams:
            items = re.findall(r'\d+\.\s*([^\n]+)', body)
            for i, item in enumerate(items, 1):
                letters = re.split(r'[\s/]+', item.strip())
                letters = [l.strip() for l in letters if l.strip() and not l.startswith('>')]
                if len(letters) <= 2:
                    violations.append({
                        'type': 'ANAGRAM_TOO_SHORT',
                        'issue': f"Anagram '{title.strip()}' item {i} has only {len(letters)} letter(s): '{item.strip()}'",
                        'fix': "Anagram items must have at least 3 letters."
                    })

    return violations


def _check_anagram_item(title: str, i: int, item) -> list[dict]:
    """Validate a single anagram item from YAML."""
    violations = []
    scrambled = getattr(item, 'scrambled', '')
    answer = getattr(item, 'answer', '')

    scrambled_letters = scrambled.split(' ')
    if len(scrambled_letters) == 1 and len(scrambled) > 1:
        violations.append({
            'type': 'ANAGRAM_FORMAT',
            'issue': f"Anagram '{title}' item {i}: scrambled '{scrambled}' is not space-separated. React component needs '\u0430 \u0439 \u0447' not '\u0430\u0439\u0447'.",
            'fix': "Add spaces between letters: '\u0430 \u0439 \u0447' instead of '\u0430\u0439\u0447'."
        })
        scrambled_letters = list(scrambled)

    scrambled_sorted = sorted(l.upper() for l in scrambled_letters if l.strip())
    answer_sorted = sorted(answer.upper())
    if scrambled_sorted != answer_sorted:
        violations.append({
            'type': 'ANAGRAM_LETTER_MISMATCH',
            'issue': f"Anagram '{title}' item {i}: scrambled letters {scrambled_sorted} don't match answer '{answer}' letters {answer_sorted}.",
            'fix': "Scrambled letters must be exactly the same letters as the answer, just reordered."
        })

    if len(scrambled_letters) < 3:
        violations.append({
            'type': 'ANAGRAM_TOO_SHORT',
            'issue': f"Anagram '{title}' item {i} has only {len(scrambled_letters)} letter(s): '{scrambled}'",
            'fix': "Anagram items must have at least 3 letters."
        })

    return violations


def check_unjumble_word_match(content: str) -> list[dict]:
    """Check if unjumble jumbled words match answer words exactly."""
    violations = []
    from collections import Counter

    unjumble_pattern = r'##\s*unjumble:\s*([^\n]+)\n(.*?)(?=\n##\s|\n#\s|\Z)'
    unjumbles = re.findall(unjumble_pattern, content, re.DOTALL | re.IGNORECASE)

    for title, body in unjumbles:
        item_pattern = r'(\d+)\.\s*([^\n>]+)\n\s*>\s*\[!answer\]\s*([^\n]+)'
        items = re.findall(item_pattern, body)

        for item_num, jumbled_text, answer_text in items:
            jumbled_words = [w.strip().lower() for w in jumbled_text.split('/') if w.strip()]

            answer_clean = re.sub(r'[\u2014\-,.:;!?()\u00ab\u00bb"]', ' ', answer_text)
            answer_words = [w.strip().lower() for w in answer_clean.split() if w.strip()]

            jumbled_words = [re.sub(r'[\u2014\-,.:;!?()\u00ab\u00bb"]', '', w) for w in jumbled_words]
            jumbled_words = [w for w in jumbled_words if w]

            jumbled_counter = Counter(jumbled_words)
            answer_counter = Counter(answer_words)

            missing_from_jumbled = answer_counter - jumbled_counter
            extra_in_jumbled = jumbled_counter - answer_counter

            if missing_from_jumbled:
                missing_list = [f"{word}(\u00d7{count})" if count > 1 else word
                               for word, count in missing_from_jumbled.items()]
                violations.append({
                    'type': 'UNJUMBLE_WORD_MISMATCH',
                    'issue': f"Unjumble '{title.strip()}' item {item_num}: answer has words not in jumbled set: {', '.join(missing_list)}",
                    'fix': "Add missing words to the jumbled set, or fix the answer."
                })

            if extra_in_jumbled:
                extra_list = [f"{word}(\u00d7{count})" if count > 1 else word
                             for word, count in extra_in_jumbled.items()]
                violations.append({
                    'type': 'UNJUMBLE_WORD_MISMATCH',
                    'issue': f"Unjumble '{title.strip()}' item {item_num}: jumbled set has extra words not in answer: {', '.join(extra_list)}",
                    'fix': "Remove extra words from jumbled set, or fix the answer."
                })

    return violations


def check_resources_placement(content: str) -> list[dict]:
    """DEPRECATED - Resources are now managed in YAML."""
    return []


def check_resources_required(content: str) -> list[dict]:
    """DEPRECATED - Resources are now managed in YAML."""
    return []
