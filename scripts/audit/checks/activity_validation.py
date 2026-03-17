"""Activity validation check for audit system."""

import json
import re


def _has_unjumble_content(item) -> bool:
    """Check if an unjumble/anagram item has content in any valid field."""
    if hasattr(item, 'words'):
        return bool(item.words)
    if hasattr(item, 'scrambled'):
        return bool(item.scrambled)
    # Legacy dictionary
    if isinstance(item, dict):
        return any(item.get(f) for f in ('words', 'jumbled', 'prompt', 'scrambled'))
    return False


def check_unjumble_empty_jumbled(yaml_activities: list) -> list:
    """Check for unjumble activities with empty jumbled fields (Issue #362)."""
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type not in ('unjumble', 'anagram'):
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for item_idx, item in enumerate(items, 1):
            if not _has_unjumble_content(item):
                violations.append({
                    'type': 'EMPTY_UNJUMBLE_CONTENT',
                    'severity': 'critical',
                    'activity': title,
                    'message': f'Item {item_idx}: Missing words/jumbled/prompt/scrambled field - will generate empty jumbled field in MDX',
                    'suggestion': 'Add words: [array], jumbled: "string", prompt: "string", or scrambled: "string" to item'
                })

    return violations


def check_mdx_unjumble_rendering(mdx_content: str) -> list:
    """Check MDX for empty jumbled fields in Unjumble components (Issue #362)."""
    violations = []

    # Find all Unjumble components
    unjumble_pattern = r'<Unjumble[^>]*title="([^"]*)"[^>]*items=\{JSON\.parse\(`([^`]+)`\)\}'

    for match in re.finditer(unjumble_pattern, mdx_content):
        title = match.group(1)
        json_str = match.group(2)

        try:
            items = json.loads(json_str)
            empty_count = sum(1 for item in items if not item.get('jumbled', ''))

            if empty_count > 0:
                violations.append({
                    'type': 'EMPTY_JUMBLED_MDX',
                    'severity': 'critical',
                    'activity': title,
                    'message': f'{empty_count} items have empty jumbled fields - activity will not render',
                    'suggestion': 'Regenerate MDX with fixed generate_mdx.py (see Issue #362)'
                })
        except json.JSONDecodeError:
            # Skip malformed JSON - other checks will catch it
            pass

    return violations


def _get_mark_text_and_answers(activity) -> tuple[str, list, str]:
    """Get text, answers, and title from a mark-the-words activity."""
    title = _get_activity_attr(activity, 'title', 'Untitled')
    text = _get_activity_attr(activity, 'text', '') or _get_activity_attr(activity, 'passage', '')
    answers = _get_activity_attr(activity, 'answers', [])
    if not answers:
        answers = _get_activity_attr(activity, 'correct_words', [])
    return text, answers or [], title


_MORPHEME_PATTERN = re.compile(r'([а-яіїєґА-ЯІЇЄҐ]*)\*([а-яіїєґА-ЯІЇЄҐ]+)\*([а-яіїєґА-ЯІЇЄҐ]*)')


def _validate_morpheme_match(match, text: str, title: str) -> list:
    """Validate a single morpheme pattern match."""
    violations = []
    prefix, morpheme, suffix = match.group(1), match.group(2), match.group(3)
    full_word = prefix + morpheme + suffix

    if not full_word or full_word == morpheme:
        return violations

    plain_text = re.sub(
        r'[а-яіїєґА-ЯІЇЄҐ]*\*([а-яіїєґА-ЯІЇЄҐ]+)\*[а-яіїєґА-ЯІЇЄҐ]*',
        lambda m: m.group(0).replace('*', ''), text)

    if full_word.lower() not in plain_text.lower():
        violations.append({
            'type': 'INVALID_MORPHEME_WORD',
            'severity': 'error',
            'activity': title,
            'message': f'Morpheme pattern "{prefix}*{morpheme}*{suffix}" constructs word "{full_word}" which is not found in the text',
            'suggestion': f'Verify morpheme pattern is correct or word "{full_word}" exists in text'
        })

    if morpheme.lower() not in full_word.lower():
        violations.append({
            'type': 'INVALID_MORPHEME_POSITION',
            'severity': 'error',
            'activity': title,
            'message': f'Morpheme "{morpheme}" not found in word "{full_word}"',
            'suggestion': 'Morpheme should be part of the word, e.g., "*при*йшов" or "Чит*ач*"'
        })

    return violations


def check_morpheme_patterns(yaml_activities: list) -> list:
    """Check for valid morpheme patterns in mark-the-words activities (Issue #363)."""
    violations = []

    for activity in yaml_activities:
        if _get_activity_attr(activity, 'type', '') != 'mark-the-words':
            continue

        text, answers, title = _get_mark_text_and_answers(activity)

        if answers and '*' not in text:
            continue

        for match in _MORPHEME_PATTERN.finditer(text):
            violations.extend(_validate_morpheme_match(match, text, title))

    return violations


def check_mark_the_words_format(activities: list) -> list:
    """Check mark-the-words activities have consistent format (brackets or asterisks, not both)."""
    violations = []

    for activity in activities:
        if _get_activity_attr(activity, 'type', '') != 'mark-the-words':
            continue

        text = _get_activity_attr(activity, 'text', '') or _get_activity_attr(activity, 'passage', '')
        title = _get_activity_attr(activity, 'title', 'Untitled')

        has_brackets = bool(re.search(r'\[([^\]]+)\]\([^)]+\)', text))
        has_morphemes = bool(re.search(r'\*[а-яіїєґА-ЯІЇЄҐ]+\*', text))

        if has_brackets and has_morphemes:
            violations.append({
                'type': 'MIXED_MARK_FORMAT',
                'severity': 'warning',
                'activity': title,
                'message': 'Activity uses both bracket [word](cat) and morpheme *mor*pheme formats',
                'suggestion': 'Use one format consistently: brackets for full words, asterisks for morphemes'
            })

    return violations


_VAGUE_MORPHEME_PATTERNS = [
    re.compile(r'prefix,?\s+suffix,?\s+(or|and)\s+root', re.IGNORECASE),
    re.compile(r'root,?\s+prefix,?\s+(or|and)\s+suffix', re.IGNORECASE),
    re.compile(r'suffix,?\s+prefix,?\s+(or|and)\s+root', re.IGNORECASE),
    re.compile(r'click\s+on\s+(any|all)\s+(word\s+parts?|morphemes?)', re.IGNORECASE),
    re.compile(r'find\s+(any|all)\s+(word\s+parts?|morphemes?)', re.IGNORECASE),
]


def _check_vague_instruction(text: str, title: str) -> list:
    """Check if the instruction text is too vague for morpheme identification."""
    instruction = text.split('\n\n')[0] if '\n\n' in text else text.split('\n')[0]
    for pattern in _VAGUE_MORPHEME_PATTERNS:
        if pattern.search(instruction):
            return [{
                'type': 'VAGUE_MORPHEME_INSTRUCTION',
                'severity': 'critical',
                'activity': title,
                'message': f'Vague instruction detected: "{instruction[:100]}"',
                'suggestion': 'Use specific instruction like "Click on all prefixes" or "Click on roots showing place names"',
                'pedagogical_issue': 'Students cannot determine what specific pattern to identify'
            }]
    return []


def _check_morpheme_consistency(text: str, title: str, morpheme_count: int) -> list:
    """Check if morpheme marking is consistent (all full words or all fragments)."""
    marked_items = re.findall(r'\*([а-яіїєґА-ЯІЇЄҐ]+)\*([а-яіїєґА-ЯІЇЄҐ]*)', text)
    has_full_words = False
    has_fragments = False

    for morpheme, rest in marked_items:
        if rest:
            has_fragments = True
        else:
            if re.search(rf'\*{re.escape(morpheme)}\*[\s\.,!?\u2014;:]', text):
                has_full_words = True

    if has_full_words and has_fragments and morpheme_count >= 3:
        return [{
            'type': 'INCONSISTENT_MORPHEME_TYPES',
            'severity': 'warning',
            'activity': title,
            'message': 'Activity mixes full words and morpheme fragments',
            'suggestion': 'Use consistent marking: either all full words (*читач*) or all fragments (*при*йшов)',
            'pedagogical_issue': 'Inconsistent marking confuses the pattern students should learn'
        }]
    return []


def check_morpheme_pedagogy(activities: list) -> list:
    """Check for pedagogically weak morpheme activities."""
    violations = []

    for activity in activities:
        if _get_activity_attr(activity, 'type', '') != 'mark-the-words':
            continue

        text = _get_activity_attr(activity, 'text', '') or _get_activity_attr(activity, 'passage', '')
        title = _get_activity_attr(activity, 'title', 'Untitled')

        violations.extend(_check_vague_instruction(text, title))

        morpheme_count = len(re.findall(r'\*[а-яіїєґА-ЯІЇЄҐ]+\*', text))
        if morpheme_count > 10:
            violations.append({
                'type': 'TOO_MANY_MORPHEMES',
                'severity': 'warning',
                'activity': title,
                'message': f'Activity has {morpheme_count} marked morphemes (recommended max: 10)',
                'suggestion': 'Reduce to 6-10 clear examples with focused pattern',
                'pedagogical_issue': 'Too many examples can overwhelm students and dilute learning objective'
            })

        violations.extend(_check_morpheme_consistency(text, title, morpheme_count))

    return violations


_ENGLISH_HINT_PATTERN = re.compile(r'\([a-z][a-z\s/]+\)')
_GRAMMAR_ANNOTATION_PATTERN = re.compile(r'\([a-z]{2,4}\.\)')

# Allowed hints for gender agreement testing (possessives)
_GENDER_AGREEMENT_HINTS = {
    '(my)', '(your)', '(his)', '(her)', '(its)', '(our)', '(their)',
    '(your informal)', '(your formal)', '(your formal/plural)',
    '(my book)', '(his car)', '(her house)',
}

_A1_A2_SCAFFOLDING_HINTS = {
    '(example)', '(hint)', '(listen)', '(repeat)', '(choose)',
    '(say)', '(read)', '(write)', '(match)', '(correct)',
    '(true)', '(false)', '(yes)', '(no)', '(answer)',
    '(singular)', '(plural)', '(masculine)', '(feminine)', '(neuter)',
}


def _collect_activity_text(activity, act_type: str) -> str:
    """Collect checkable text from an activity based on its type."""
    if act_type == 'cloze':
        return _get_activity_attr(activity, 'passage', '') or ''
    if act_type in ('fill-in', 'error-correction'):
        items = _get_activity_attr(activity, 'items', [])
        parts = []
        for item in items:
            sentence = item.get('sentence', '') if isinstance(item, dict) else getattr(item, 'sentence', '')
            parts.append(sentence)
        return '\n'.join(parts)
    return ''


def _filter_real_hints(hints: list[str], allowed_scaffolding: set) -> list[str]:
    """Filter out grammar annotations and allowed hints from a list of hint matches."""
    real = []
    for hint in hints:
        hint_lower = hint.lower()
        if _GRAMMAR_ANNOTATION_PATTERN.match(hint):
            continue
        if hint_lower in _GENDER_AGREEMENT_HINTS:
            continue
        if hint_lower in allowed_scaffolding:
            continue
        real.append(hint)
    return real


def check_english_hints_in_activities(yaml_activities: list, level: str, module_num: int) -> list:
    """Check for inappropriate English hints in activities."""
    violations = []

    base_level = level.split('-')[0].upper() if level else ''
    is_beginner = base_level in ('A1', 'A2')
    critical_threshold = 15 if is_beginner else 5
    severity_floor = 'info' if is_beginner else 'warning'
    scaffolding = _A1_A2_SCAFFOLDING_HINTS if is_beginner else set()

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        title = _get_activity_attr(activity, 'title', 'Untitled')

        text_to_check = _collect_activity_text(activity, act_type)
        if not text_to_check:
            continue

        hints = _ENGLISH_HINT_PATTERN.findall(text_to_check)
        real_hints = _filter_real_hints(hints, scaffolding)

        if real_hints:
            severity = 'critical' if len(real_hints) > critical_threshold else severity_floor
            violations.append({
                'type': 'ENGLISH_HINTS_IN_ACTIVITY',
                'severity': severity,
                'activity': title,
                'activity_type': act_type,
                'message': f'Found {len(real_hints)} English hints: {", ".join(real_hints[:5])}{"..." if len(real_hints) > 5 else ""}',
                'suggestion': 'Remove English hints - students should understand from context. For word formation activities, add Ukrainian context instead.',
                'pedagogical_issue': 'English hints make it too easy and defeat the learning objective. Students match English\u2192Ukrainian instead of understanding patterns.',
                'examples': real_hints[:10]
            })

    return violations


def _get_activity_attr(activity, attr: str, default=None):
    """Helper to get attribute from activity object or dictionary.

    Checks isinstance(dict) FIRST to avoid dict built-in methods (like
    dict.items, dict.keys) shadowing actual dict keys of the same name.
    """
    if isinstance(activity, dict):
        return activity.get(attr, default)
    if hasattr(activity, attr):
        return getattr(activity, attr, default)
    return default


_SEMINAR_TRACKS = {'lit', 'hist', 'istorio', 'bio', 'bio-seminar'}
_ANALYTICAL_TYPES = {'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'}


def _collect_reading_ids(yaml_activities: list) -> tuple[set, list]:
    """Collect reading IDs and titles of readings missing IDs."""
    reading_ids = set()
    missing_id_titles = []
    for idx, activity in enumerate(yaml_activities):
        if _get_activity_attr(activity, 'type', '') == 'reading':
            act_id = _get_activity_attr(activity, 'id')
            if act_id:
                reading_ids.add(act_id)
            else:
                missing_id_titles.append(
                    _get_activity_attr(activity, 'title', f'Activity {idx+1}'))
    return reading_ids, missing_id_titles


def _check_analytical_sources(yaml_activities: list, reading_ids: set) -> tuple[set, list]:
    """Check analytical activities for valid source_reading references."""
    referenced = set()
    violations = []
    for idx, activity in enumerate(yaml_activities):
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type not in _ANALYTICAL_TYPES:
            continue
        title = _get_activity_attr(activity, 'title', f'Activity {idx+1}')
        source_reading = _get_activity_attr(activity, 'source_reading')

        if source_reading:
            referenced.add(source_reading)
            if source_reading not in reading_ids:
                violations.append({
                    'type': 'INVALID_SOURCE_READING', 'severity': 'critical',
                    'activity': title,
                    'message': f'source_reading "{source_reading}" not found in module readings',
                    'suggestion': f'Valid reading IDs: {", ".join(sorted(reading_ids)) if reading_ids else "(none defined)"}'
                })
        else:
            violations.append({
                'type': 'MISSING_SOURCE_READING', 'severity': 'critical',
                'activity': title, 'activity_type': act_type,
                'message': f'{act_type} activity lacks source_reading link',
                'suggestion': 'Add source_reading: "reading-XX" to link this analysis to its source text'
            })
    return referenced, violations


def check_seminar_reading_pairing(yaml_activities: list, level: str) -> list:
    """Check that seminar track activities have proper reading-analysis pairing."""
    level_lower = level.lower() if level else ''
    if level_lower not in _SEMINAR_TRACKS:
        return []

    violations = []
    reading_ids, missing_id_titles = _collect_reading_ids(yaml_activities)

    for title in missing_id_titles:
        violations.append({
            'type': 'READING_MISSING_ID', 'severity': 'critical',
            'activity': title,
            'message': 'Reading activity missing required "id" field',
            'suggestion': 'Add id: "reading-01" (or similar) to link with analytical activities'
        })

    referenced, analytical_violations = _check_analytical_sources(yaml_activities, reading_ids)
    violations.extend(analytical_violations)

    for reading_id in reading_ids - referenced:
        reading_title = reading_id
        for activity in yaml_activities:
            if _get_activity_attr(activity, 'id') == reading_id:
                reading_title = _get_activity_attr(activity, 'title', reading_id)
                break
        violations.append({
            'type': 'ORPHAN_READING', 'severity': 'warning',
            'activity': reading_title,
            'message': f'Reading "{reading_id}" is not referenced by any analytical activity',
            'suggestion': f'Add source_reading: "{reading_id}" to an essay-response, critical-analysis, or comparative-study'
        })

    return violations


def _get_item_options(item) -> list:
    """Get options list from an activity item (object or dict)."""
    if hasattr(item, 'options'):
        return item.options or []
    if isinstance(item, dict):
        return item.get('options', [])
    return []


def _count_correct_options(options: list) -> int:
    """Count how many options are marked correct: true."""
    count = 0
    for opt in options:
        if hasattr(opt, 'correct'):
            if opt.correct:
                count += 1
        elif isinstance(opt, dict) and opt.get('correct', False):
            count += 1
    return count


def check_select_min_correct(yaml_activities: list) -> list:
    """
    Check that select activities have min_correct matching the actual number of
    correct: true options in each question.

    Bug pattern: min_correct: 2 but 3 options are marked correct: true.
    This makes the activity unsolvable (student must pick exactly min_correct
    but more are actually correct).
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type != 'select':
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            options = _get_item_options(item)
            min_correct = _get_activity_attr(item, 'min_correct', None)
            if min_correct is None:
                continue

            actual_correct = _count_correct_options(options)
            if actual_correct != min_correct:
                violations.append({
                    'type': 'SELECT_MIN_CORRECT_MISMATCH',
                    'severity': 'critical',
                    'activity': title,
                    'message': (
                        f'Question {idx}: min_correct={min_correct} but '
                        f'{actual_correct} options are marked correct: true. '
                        f'These must match exactly.'
                    ),
                    'suggestion': (
                        f'Set min_correct: {actual_correct} OR mark exactly '
                        f'{min_correct} options as correct: true.'
                    ),
                })

    return violations


def check_quiz_single_correct(yaml_activities: list) -> list:
    """
    Check that each quiz item has exactly one correct: true option.

    Bug pattern: 0 or 2+ options marked correct in a single quiz question.
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type != 'quiz':
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            options = _get_item_options(item)
            if not options:
                continue

            correct_count = _count_correct_options(options)
            if correct_count != 1:
                violations.append({
                    'type': 'QUIZ_CORRECT_COUNT',
                    'severity': 'critical',
                    'activity': title,
                    'message': (
                        f'Question {idx} has {correct_count} correct options '
                        f'(must be exactly 1).'
                    ),
                    'suggestion': 'Mark exactly one option as correct: true per question.',
                })

    return violations


def check_fill_in_answer_in_options(yaml_activities: list) -> list:
    """
    Check that fill-in items have their answer present in the options list.

    Bug pattern: answer: "слово" but options: ["інше", "щось"] — the correct
    answer is not selectable.
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type != 'fill-in':
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            answer = _get_activity_attr(item, 'answer', '')
            options = _get_item_options(item)

            if not answer or not options:
                continue

            if answer not in options:
                violations.append({
                    'type': 'FILL_IN_ANSWER_NOT_IN_OPTIONS',
                    'severity': 'critical',
                    'activity': title,
                    'message': (
                        f'Item {idx}: answer "{answer}" not found in options '
                        f'{options}. Student cannot select the correct answer.'
                    ),
                    'suggestion': f'Add "{answer}" to the options list.',
                })

    return violations


def check_translate_single_correct(yaml_activities: list) -> list:
    """
    Check that each translate item has exactly one correct: true option.
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type != 'translate':
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            options = _get_item_options(item)
            if not options:
                continue

            correct_count = _count_correct_options(options)
            if correct_count != 1:
                violations.append({
                    'type': 'TRANSLATE_CORRECT_COUNT',
                    'severity': 'critical',
                    'activity': title,
                    'message': (
                        f'Item {idx} has {correct_count} correct options '
                        f'(must be exactly 1).'
                    ),
                    'suggestion': 'Mark exactly one translation option as correct: true.',
                })

    return violations


def check_mark_the_words_answers_in_text(yaml_activities: list) -> list:
    """Check that every answer in mark-the-words activities exists in the text."""
    violations = []

    for activity in yaml_activities:
        if _get_activity_attr(activity, 'type', '') != 'mark-the-words':
            continue

        text, answers, title = _get_mark_text_and_answers(activity)
        if not text or not answers:
            continue

        for ans in answers:
            if ans not in text:
                violations.append({
                    'type': 'MARK_THE_WORDS_ANSWER_NOT_IN_TEXT',
                    'severity': 'critical',
                    'activity': title,
                    'message': f'Answer "{ans}" not found in activity text.',
                    'suggestion': f'Either add "{ans}" to the text or remove it from answers. '
                                  f'Students cannot mark what is not in the text.',
                })

    return violations


# Sentence-ending punctuation that legitimately precedes a capital letter
_SENTENCE_ENDS = set('.!?:—»')

# Ukrainian words that are ALWAYS capitalised regardless of position.
# Я = first-person pronoun, Ви = formal second-person pronoun.
_ALWAYS_CAPITAL = {'Я', 'Ви'}


def check_unjumble_runon_answer(yaml_activities: list) -> list:
    """
    Check unjumble answers for run-on sentences.

    A run-on is detected when a capital-letter token appears mid-answer
    (not at position 0) and the preceding token does not end with
    sentence-closing punctuation (.  !  ?  :  —  »).

    Catches: "Вітаю тебе Це маленький подарунок" where "Це" starts a new
    sentence but there is no full-stop after "тебе".

    Always-capital Ukrainian words (Я) are excluded to avoid false positives.
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type not in ('unjumble', 'anagram'):
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            if hasattr(item, 'answer'):
                answer = item.answer or ''
            elif isinstance(item, dict):
                answer = item.get('answer', '') or ''
            else:
                continue

            if not answer:
                continue

            tokens = answer.split()
            for i, token in enumerate(tokens[1:], 1):  # skip first token
                if not token or not token[0].isupper():
                    continue
                # Strip trailing punctuation before checking always-capital set
                token_bare = token.rstrip('.,!?:;—»')
                if token_bare in _ALWAYS_CAPITAL:
                    continue
                # If token itself ends with sentence punctuation, it closes a
                # sentence (proper noun like "Іван.") — not starting a new one
                if token[-1] in _SENTENCE_ENDS:
                    continue
                prev_token = tokens[i - 1]
                if prev_token and prev_token[-1] in _SENTENCE_ENDS:
                    continue  # capital after sentence-end is fine
                # Capital token mid-answer with no preceding punctuation
                violations.append({
                    'type': 'UNJUMBLE_RUNON_SENTENCE',
                    'severity': 'warning',
                    'activity': title,
                    'message': (
                        f'Item {idx}: capital letter "{token}" appears after '
                        f'"{prev_token}" without sentence-ending punctuation. '
                        f'Possible run-on: two sentences merged into one answer.'
                    ),
                    'suggestion': (
                        'If two sentences are intended, split into two separate '
                        'unjumble items. If it is a proper noun mid-sentence, '
                        'verify it is correct.'
                    ),
                    'answer': answer,
                })
                break  # one violation per item is enough


    return violations


# Possessive adjective dative forms — a clear signal that dative NOUNS
# (not pronouns) are being used. These are distinct from the taught dative
# pronouns (мені, тобі, йому, їй, нам, вам, їм).
_POSSESSIVE_DATIVE_FORMS = {
    'моїй', 'твоїй', 'нашій', 'вашій', 'своїй',      # singular feminine dative
    'моєму', 'твоєму', 'нашому', 'вашому', 'своєму',  # singular masc/neut dative
    'моїм', 'твоїм', 'нашим', 'вашим', 'своїм',       # plural dative
}


def check_unjumble_out_of_scope_dative(yaml_activities: list) -> list:
    """
    Detect unjumble items that use possessive-adjective dative forms
    (моїй сестрі, твоєму другу, etc.), which signal dative NOUN phrases.

    Dative nouns are taught in a separate module from dative pronouns.
    Using them in a pronouns-only module introduces out-of-scope grammar.

    Fires as WARNING — human/Gemini must confirm whether dative nouns
    are actually in scope for this module.
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        if act_type != 'unjumble':
            continue

        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            if hasattr(item, 'words'):
                words = item.words or []
            elif isinstance(item, dict):
                words = item.get('words', []) or []
            else:
                continue

            flagged = [w for w in words if w.lower() in _POSSESSIVE_DATIVE_FORMS]
            if flagged:
                violations.append({
                    'type': 'UNJUMBLE_POSSIBLE_OUT_OF_SCOPE_DATIVE',
                    'severity': 'warning',
                    'activity': title,
                    'message': (
                        f'Item {idx} contains possessive dative form(s) '
                        f'{flagged} — these signal dative NOUN phrases, '
                        f'not dative pronouns. Verify this grammar is in '
                        f'scope for the current module.'
                    ),
                    'suggestion': (
                        'If this module only teaches dative pronouns '
                        '(мені, тобі, йому…), replace with a dative pronoun. '
                        'If dative nouns ARE in scope, this warning can be ignored.'
                    ),
                    'words': words,
                })

    return violations


def check_duplicate_options(yaml_activities: list) -> list:
    """Detect activities where the same option appears multiple times in an item.

    Bug pattern from M05: options: [о-те-ка, бібліотека, о-те-ка, о-те-ка]
    — three identical distractors due to lazy LLM generation.

    Issue: #969 AC4
    """
    violations = []

    for activity in yaml_activities:
        act_type = _get_activity_attr(activity, 'type', '')
        title = _get_activity_attr(activity, 'title', 'Untitled')
        items = _get_activity_attr(activity, 'items', [])

        for idx, item in enumerate(items, 1):
            options = _get_item_options(item)
            if not options or len(options) < 2:
                continue

            # Normalize options to strings for comparison
            str_options = [str(o).strip().lower() if not isinstance(o, dict)
                          else str(o.get('text', '')).strip().lower()
                          for o in options]

            seen = {}
            duplicates = []
            for opt in str_options:
                if not opt:
                    continue
                if opt in seen:
                    seen[opt] += 1
                    if seen[opt] == 2:  # Report once per duplicate
                        duplicates.append(opt)
                else:
                    seen[opt] = 1

            if duplicates:
                violations.append({
                    'type': 'DUPLICATE_OPTIONS',
                    'severity': 'critical',
                    'activity': title,
                    'message': (
                        f'Item {idx} ({act_type}): duplicate option(s) '
                        f'{duplicates}. LLM copy-pasted the same distractor.'
                    ),
                    'suggestion': 'Replace duplicates with unique, pedagogically sound distractors.',
                })

    return violations


__all__ = [
    'check_duplicate_options',
    'check_english_hints_in_activities',
    'check_fill_in_answer_in_options',
    'check_mark_the_words_answers_in_text',
    'check_mark_the_words_format',
    'check_mdx_unjumble_rendering',
    'check_morpheme_patterns',
    'check_morpheme_pedagogy',
    'check_quiz_single_correct',
    # New semantic correctness checks
    'check_select_min_correct',
    'check_seminar_reading_pairing',
    'check_translate_single_correct',
    'check_unjumble_empty_jumbled',
    'check_unjumble_out_of_scope_dative',
    # Unjumble quality checks
    'check_unjumble_runon_answer',
]
