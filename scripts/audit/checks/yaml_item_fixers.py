"""
Per-activity-type YAML item fix functions.

Each function fixes common schema violations for a specific activity type
(e.g., renaming fields, coercing types, extracting answers from text).
"""

import re


def fix_invalid_top_level_properties(activity: dict, activity_type: str, allowed_properties) -> list[str]:
    """Fix 1: Remove invalid top-level properties not in schema."""
    fixes = []
    if 'id' in activity and 'id' not in allowed_properties:
        del activity['id']
        fixes.append(f"Removed invalid 'id' property from {activity_type}")
    if 'question' in activity and 'question' not in allowed_properties:
        if 'title' not in activity:
            activity['title'] = activity['question']
            fixes.append(f"Renamed 'question' to 'title' in {activity_type}")
        del activity['question']
        fixes.append(f"Removed invalid 'question' property from {activity_type}")
    if 'text' in activity and 'text' not in allowed_properties:
        del activity['text']
        fixes.append(f"Removed invalid 'text' property from {activity_type}")
    return fixes


def fix_mark_the_words(activity: dict) -> list[str]:
    """Fix 2: Extract answers from mark-the-words text marked with *asterisks*."""
    fixes = []
    if 'text' not in activity or 'answers' in activity:
        return fixes
    text = activity['text']
    marked_words = re.findall(r'\*([^\*]+)\*', text)
    if marked_words:
        activity['answers'] = marked_words
        activity['text'] = re.sub(r'\*([^\*]+)\*', r'\1', text)
        fixes.append(f"Extracted answers from text ({len(marked_words)} words)")
    return fixes


def fix_unjumble_items(activity: dict) -> list[str]:
    """Fix 3: Convert scrambled to words array in unjumble items."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if not isinstance(item, dict):
            continue
        if 'scrambled' in item and 'words' in item:
            del item['scrambled']
            fixes.append(f"Removed duplicate 'scrambled' property from unjumble item {i+1}")
        elif 'scrambled' in item and 'words' not in item:
            scrambled = item['scrambled']
            words = [w.strip() for w in scrambled.split(' / ')] if ' / ' in scrambled else scrambled.split()
            item['words'] = words
            del item['scrambled']
            fixes.append(f"Converted 'scrambled' to 'words' array in unjumble item {i+1}")
    return fixes


def _fix_translate_item(item: dict, idx: int) -> list[str]:
    """Fix a single translate item: rename question->source, answer->options, coerce types."""
    fixes = []
    if 'question' in item:
        if 'source' not in item:
            item['source'] = item['question']
            fixes.append(f"Renamed 'question' to 'source' in translate item {idx}")
        del item['question']
        fixes.append(f"Removed invalid 'question' from translate item {idx}")
    if 'answer' in item and 'options' not in item:
        item['options'] = [{'text': str(item['answer']), 'correct': True}]
        del item['answer']
        fixes.append(f"Converted 'answer' to 'options' array in translate item {idx}")
    if 'options' in item:
        for opt in item['options']:
            if isinstance(opt, dict) and 'text' in opt and not isinstance(opt['text'], str):
                opt['text'] = str(opt['text'])
                fixes.append(f"Converted option text to string in translate item {idx}")
    return fixes


def fix_translate_items(activity: dict) -> list[str]:
    """Fix 4: Ensure source property exists and restructure translate items."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if isinstance(item, dict):
            fixes.extend(_fix_translate_item(item, i + 1))
    return fixes


def _fix_question_field(item: dict, activity_type: str, idx: int) -> list[str]:
    """Fix missing 'question' field by renaming 'prompt' or 'text'."""
    fixes = []
    if 'question' not in item:
        if 'prompt' in item:
            item['question'] = item['prompt']
            del item['prompt']
            fixes.append(f"Renamed 'prompt' to 'question' in {activity_type} item {idx}")
        elif 'text' in item:
            item['question'] = item['text']
            del item['text']
            fixes.append(f"Renamed 'text' to 'question' in {activity_type} item {idx}")
    return fixes


def _fix_option_types(item: dict, activity_type: str, idx: int) -> list[str]:
    """Coerce option text to string, convert string options to dicts, and add missing correct:false."""
    fixes = []
    if 'options' not in item or not isinstance(item['options'], list):
        return fixes

    for i, opt in enumerate(item['options']):
        if isinstance(opt, str):
            item['options'][i] = {'text': opt, 'correct': False}
            fixes.append(f"Converted string option to dict in {activity_type} item {idx}")
        elif isinstance(opt, dict) and 'text' in opt and not isinstance(opt['text'], str):
            opt['text'] = str(opt['text'])
            fixes.append(f"Converted option text to string in {activity_type} item {idx}")

    options_fixed = sum(1 for opt in item['options']
                        if isinstance(opt, dict) and 'correct' not in opt)
    for opt in item['options']:
        if isinstance(opt, dict) and 'correct' not in opt:
            opt['correct'] = False
    if options_fixed > 0:
        fixes.append(f"Added 'correct: false' to {options_fixed} options in {activity_type} item {idx}")
    return fixes


def fix_quiz_select_items(activity: dict, activity_type: str) -> list[str]:
    """Fix 5/5b: Ensure question property, type coercion, missing correct:false, pad/truncate options."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if not isinstance(item, dict):
            continue
        fixes.extend(_fix_question_field(item, activity_type, i + 1))
        fixes.extend(_fix_option_types(item, activity_type, i + 1))

        # Pad or truncate quiz options to exactly 4
        if activity_type == 'quiz' and 'options' in item and isinstance(item['options'], list):
            while len(item['options']) < 4:
                item['options'].append({'text': 'None of the above', 'correct': False})
                fixes.append(f"Padded quiz item {i + 1} to 4 options")
            if len(item['options']) > 4:
                # Ensure the correct option is kept when truncating
                correct_opts = [o for o in item['options'] if o.get('correct')]
                incorrect_opts = [o for o in item['options'] if not o.get('correct')]
                item['options'] = (correct_opts + incorrect_opts)[:4]
                fixes.append(f"Truncated quiz item {i + 1} to exactly 4 options")

    return fixes


def fix_quiz_answer_field(activity: dict) -> list[str]:
    """Fix: remove standalone 'answer' field from quiz items, mark matching option correct."""
    fixes = []
    if activity.get('type') not in ('quiz', 'select'):
        return fixes
    for i, item in enumerate(activity.get('items', [])):
        if not isinstance(item, dict) or 'answer' not in item:
            continue

        answer_text = str(item['answer']).strip()
        answer_text_lower = answer_text.lower()
        matched = False

        # Mark the matching option as correct
        for opt in item.get('options', []):
            if isinstance(opt, dict) and str(opt.get('text', '')).strip().lower() == answer_text_lower:
                opt['correct'] = True
                matched = True
                fixes.append(f"Marked correct option from 'answer' field in quiz item {i+1}")
                break

        # If no option matched the answer text, inject it so the quiz is solvable
        if not matched and isinstance(item.get('options'), list):
            # Prefer to replace a generic/padding option if one exists, or append if we have room
            if len(item['options']) < 4:
                item['options'].append({'text': answer_text, 'correct': True})
            else:
                # Overwrite the last incorrect option with the correct answer
                for opt in reversed(item['options']):
                    if not opt.get('correct'):
                        opt['text'] = answer_text
                        opt['correct'] = True
                        break
            fixes.append(f"Injected missing 'answer' field text into options for quiz item {i+1}")

        del item['answer']
        fixes.append(f"Removed standalone 'answer' field from quiz item {i+1}")

        # Ensure that at least one option is marked correct in a quiz!
        if activity.get('type') == 'quiz' and isinstance(item.get('options'), list):
            has_correct = any(opt.get('correct') for opt in item['options'] if isinstance(opt, dict))
            if not has_correct and len(item['options']) > 0:
                item['options'][0]['correct'] = True
                fixes.append(f"Fallback: Marked first option correct in quiz item {i+1} as no correct option was found")

    return fixes


def fix_match_up_pairs(activity: dict) -> list[str]:
    """Fix 5c: Type coercion for match-up pairs."""
    fixes = []
    if 'pairs' not in activity:
        return fixes
    for i, pair in enumerate(activity['pairs']):
        if not isinstance(pair, dict):
            continue
        if 'left' in pair and not isinstance(pair['left'], str):
            pair['left'] = str(pair['left'])
            fixes.append(f"Converted pair left to string in match-up pair {i+1}")
        if 'right' in pair and not isinstance(pair['right'], str):
            pair['right'] = str(pair['right'])
            fixes.append(f"Converted pair right to string in match-up pair {i+1}")
    return fixes


def fix_true_false_items(activity: dict) -> list[str]:
    """Fix 6: Rename text->statement, answer->correct in true-false items."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if not isinstance(item, dict):
            continue
        if 'text' in item and 'statement' not in item:
            item['statement'] = item['text']
            del item['text']
            fixes.append(f"Renamed 'text' to 'statement' in true-false item {i+1}")
        if 'answer' in item and 'correct' not in item:
            item['correct'] = item['answer']
            del item['answer']
            fixes.append(f"Renamed 'answer' to 'correct' in true-false item {i+1}")
        if 'is_true' in item and 'correct' not in item:
            item['correct'] = item['is_true']
            del item['is_true']
            fixes.append(f"Renamed 'is_true' to 'correct' in true-false item {i+1}")
    return fixes


def fix_fill_in_items(activity: dict) -> list[str]:
    """Fix 7: Rename text->sentence in fill-in items."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if isinstance(item, dict) and 'text' in item and 'sentence' not in item:
            item['sentence'] = item['text']
            del item['text']
            fixes.append(f"Renamed 'text' to 'sentence' in fill-in item {i+1}")
    return fixes


def fix_error_correction_items(activity: dict) -> list[str]:
    """Fix 8: Ensure sentence property exists and type coercion."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if not isinstance(item, dict):
            continue
        if 'text' in item and 'sentence' not in item:
            item['sentence'] = item['text']
            del item['text']
            fixes.append(f"Renamed 'text' to 'sentence' in error-correction item {i+1}")
        elif 'error' in item and 'sentence' not in item:
            item['sentence'] = item['error']
            fixes.append(f"Copied 'error' to 'sentence' in error-correction item {i+1}")
        if 'answer' in item and not isinstance(item['answer'], str):
            item['answer'] = str(item['answer'])
            fixes.append(f"Converted answer to string in error-correction item {i+1}")
    return fixes


def fix_group_sort_groups(activity: dict) -> list[str]:
    """Fix 9: Rename title->name in group-sort groups."""
    fixes = []
    if 'groups' not in activity:
        return fixes
    for group in activity['groups']:
        if isinstance(group, dict) and 'title' in group and 'name' not in group:
            group['name'] = group['title']
            del group['title']
            fixes.append("Renamed 'title' to 'name' in group-sort group")
    return fixes


def fix_classify_groups_to_categories(activity: dict) -> list[str]:
    """Fix: classify using groups/name instead of categories/label."""
    fixes = []
    if activity.get('type') != 'classify':
        return fixes
    # Convert groups → categories
    if 'groups' in activity and 'categories' not in activity:
        activity['categories'] = activity.pop('groups')
        fixes.append("Renamed 'groups' to 'categories' in classify activity")
    # Convert name → label in each category
    for cat in activity.get('categories', []):
        if isinstance(cat, dict) and 'name' in cat and 'label' not in cat:
            cat['label'] = cat.pop('name')
            fixes.append("Renamed 'name' to 'label' in classify category")
    return fixes


def fix_select_property_renames(activity: dict) -> list[str]:
    """Fix 10: Rename answers/choices to options in select items."""
    fixes = []
    if 'items' not in activity:
        return fixes
    for i, item in enumerate(activity['items']):
        if isinstance(item, dict) and 'options' not in item:
            if 'answers' in item:
                item['options'] = item['answers']
                del item['answers']
                fixes.append(f"Renamed 'answers' to 'options' in select item {i+1}")
            elif 'choices' in item:
                item['options'] = item['choices']
                del item['choices']
                fixes.append(f"Renamed 'choices' to 'options' in select item {i+1}")
    return fixes


def fix_missing_instruction(activity: dict, activity_type: str) -> list[str]:
    """Fix 11: Add missing instruction field with default text."""
    if 'instruction' not in activity and activity_type in DEFAULT_INSTRUCTIONS:
        activity['instruction'] = DEFAULT_INSTRUCTIONS[activity_type]
        return [f"Added default instruction for {activity_type}"]
    return []


def fix_cloze_blank_lines(activity: dict) -> list[str]:
    """Fix 12: Remove blank lines from cloze passages."""
    if 'passage' not in activity:
        return []
    passage = activity['passage']
    if '\n\n' not in passage:
        return []
    fixed_passage = passage.replace('\n\n', '\n')
    while '\n\n' in fixed_passage:
        fixed_passage = fixed_passage.replace('\n\n', '\n')
    activity['passage'] = fixed_passage
    return ["Removed blank lines from cloze passage (fixes MDX rendering)"]


# Default instructions by activity type (in Ukrainian for B1+ immersion)
DEFAULT_INSTRUCTIONS = {
    'quiz': 'Оберіть правильну відповідь.',
    'match-up': "З'єднайте відповідні елементи.",
    'fill-in': 'Оберіть правильне слово для заповнення пропуску.',
    'true-false': 'Визначте, чи твердження правильне.',
    'group-sort': 'Розподіліть елементи за групами.',
    'unjumble': 'Розташуйте слова у правильному порядку.',
    'cloze': 'Заповніть пропуски, обравши правильні слова.',
    'error-correction': 'Знайдіть і виправте помилку в реченні.',
    'mark-the-words': 'Клацніть на слова, що відповідають критерію.',
    'select': 'Оберіть усі правильні відповіді.',
    'translate': 'Оберіть правильний переклад.',
    'anagram': 'Розташуйте літери у правильному порядку.',
}


def fix_image_to_letter_items(activity: dict) -> list[str]:
    """Fix: image-to-letter items missing emoji/distractors, using wrong field names.

    Common Gemini errors:
    - Uses 'word:' instead of 'emoji:' (or no emoji at all)
    - Missing 'distractors:' array
    - Lowercase answer ('к' instead of 'К')
    """
    fixes = []
    if activity.get('type') != 'image-to-letter':
        return fixes

    # Ukrainian letters for generating distractors
    all_letters = list("АБВГҐДЕЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩ")

    for item in activity.get('items', []):
        if not isinstance(item, dict):
            continue

        # Rename 'word' to 'note' if no emoji — the word is context, not the image
        if 'word' in item and 'emoji' not in item and 'image' not in item:
            item['note'] = item.get('note', '') or item.pop('word')
            if 'word' in item:
                del item['word']
            item['emoji'] = '📝'  # placeholder — better than nothing
            fixes.append("Added placeholder emoji, moved 'word' to 'note'")

        # Uppercase answer
        if 'answer' in item and len(item['answer']) == 1 and item['answer'].islower():
            item['answer'] = item['answer'].upper()
            fixes.append(f"Uppercased answer '{item['answer']}'")

        # Add distractors if missing
        if 'distractors' not in item and 'answer' in item:
            answer = item['answer'].upper()
            distractors = [l for l in all_letters if l != answer][:3]
            item['distractors'] = distractors
            fixes.append(f"Added distractors {distractors} for answer '{answer}'")

    return fixes


# Dispatch table mapping activity type -> fixer function
TYPE_FIXERS = {
    'mark-the-words': fix_mark_the_words,
    'unjumble': fix_unjumble_items,
    'translate': fix_translate_items,
    'match-up': fix_match_up_pairs,
    'true-false': fix_true_false_items,
    'fill-in': fix_fill_in_items,
    'error-correction': fix_error_correction_items,
    'group-sort': fix_group_sort_groups,
    'classify': fix_classify_groups_to_categories,
    'image-to-letter': fix_image_to_letter_items,
    'quiz-answer': fix_quiz_answer_field,
}
