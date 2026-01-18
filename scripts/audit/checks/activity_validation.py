"""Activity validation check for audit system."""

import re
import json
from pathlib import Path
from typing import Dict, List


def check_unjumble_empty_jumbled(yaml_activities: list) -> list:
    """Check for unjumble activities with empty jumbled fields (Issue #362)."""
    violations = []

    for activity in yaml_activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type not in ['unjumble', 'anagram']:
            continue

        title = activity.title if hasattr(activity, 'title') else activity.get('title', 'Untitled')
        items = activity.items if hasattr(activity, 'items') else activity.get('items', [])

        for item_idx, item in enumerate(items, 1):
            # Check if item has none of the valid field formats
            # Handle both dataclass object and dictionary
            if hasattr(item, 'words'):
                has_words = bool(item.words)
                has_jumbled = False
                has_prompt = False
                has_scrambled = False
            elif hasattr(item, 'scrambled'):
                has_words = False
                has_jumbled = False
                has_prompt = False
                has_scrambled = bool(item.scrambled)
            else:
                # Legacy dictionary
                has_words = 'words' in item and item['words']
                has_jumbled = 'jumbled' in item and item['jumbled']
                has_prompt = 'prompt' in item and item['prompt']
                has_scrambled = 'scrambled' in item and item['scrambled']

            if not (has_words or has_jumbled or has_prompt or has_scrambled):
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


def check_morpheme_patterns(yaml_activities: list) -> list:
    """Check for valid morpheme patterns in mark-the-words activities (Issue #363)."""
    violations = []

    for activity in yaml_activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'mark-the-words':
            continue

        text = getattr(activity, 'text', '') or getattr(activity, 'passage', '')
        if not text and isinstance(activity, dict):
            text = activity.get('text', '') or activity.get('passage', '')
            
        answers = getattr(activity, 'answers', [])
        if not answers and isinstance(activity, dict):
            answers = activity.get('answers', []) or activity.get('correct_words', [])
            
        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')

        if answers and '*' not in text:
            # If using answers array and no asterisks, it's not a morpheme activity
            continue

        # Pattern: (prefix)*morpheme*(suffix)
        morpheme_pattern = r'([а-яіїєґА-ЯІЇЄҐ]*)\*([а-яіїєґА-ЯІЇЄҐ]+)\*([а-яіїєґА-ЯІЇЄҐ]*)'
        matches = list(re.finditer(morpheme_pattern, text))

        if not matches:
            continue

        for match in matches:
            prefix = match.group(1)
            morpheme = match.group(2)
            suffix = match.group(3)
            full_word = prefix + morpheme + suffix

            if not full_word or full_word == morpheme:
                continue

            plain_text = re.sub(r'[а-яіїєґА-ЯІЇЄҐ]*\*([а-яіїєґА-ЯІЇЄҐ]+)\*[а-яіїєґА-ЯІЇЄҐ]*',
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
                    'suggestion': f'Morpheme should be part of the word, e.g., "*при*йшов" or "Чит*ач*"'
                })

    return violations


def check_mark_the_words_format(activities: list) -> list:
    """Check mark-the-words activities have consistent format (brackets or asterisks, not both)."""
    violations = []

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'mark-the-words':
            continue

        text = getattr(activity, 'text', '') or getattr(activity, 'passage', '')
        if not text and isinstance(activity, dict):
            text = activity.get('text', '') or activity.get('passage', '')
            
        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')

        # Check for old bracket format: [word](category)
        has_brackets = bool(re.search(r'\[([^\]]+)\]\([^)]+\)', text))

        # Check for new morpheme format: *morpheme*word
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


def check_morpheme_pedagogy(activities: list) -> list:
    """Check for pedagogically weak morpheme activities."""
    violations = []

    for activity in activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type')
        if act_type != 'mark-the-words':
            continue

        text = getattr(activity, 'text', '') or getattr(activity, 'passage', '')
        if not text and isinstance(activity, dict):
            text = activity.get('text', '') or activity.get('passage', '')
            
        title = getattr(activity, 'title', 'Untitled')
        if not title and isinstance(activity, dict):
            title = activity.get('title', 'Untitled')

        # Check for vague instructions (case-insensitive)
        vague_patterns = [
            r'prefix,?\s+suffix,?\s+(or|and)\s+root',
            r'root,?\s+prefix,?\s+(or|and)\s+suffix',
            r'suffix,?\s+prefix,?\s+(or|and)\s+root',
            r'click\s+on\s+(any|all)\s+(word\s+parts?|morphemes?)',
            r'find\s+(any|all)\s+(word\s+parts?|morphemes?)',
        ]

        instruction_text = text.split('\n\n')[0] if '\n\n' in text else text.split('\n')[0]

        for pattern in vague_patterns:
            if re.search(pattern, instruction_text, re.IGNORECASE):
                violations.append({
                    'type': 'VAGUE_MORPHEME_INSTRUCTION',
                    'severity': 'critical',
                    'activity': title,
                    'message': f'Vague instruction detected: "{instruction_text[:100]}"',
                    'suggestion': 'Use specific instruction like "Click on all prefixes" or "Click on roots showing place names"',
                    'pedagogical_issue': 'Students cannot determine what specific pattern to identify'
                })
                break

        # Count marked morphemes (asterisk patterns)
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

        # Analyze morpheme consistency (check if mixing full words vs fragments)
        marked_items = re.findall(r'\*([а-яіїєґА-ЯІЇЄҐ]+)\*([а-яіїєґА-ЯІЇЄҐ]*)', text)

        has_full_words = False  # *word* with no continuation
        has_fragments = False   # *prefix*rest or *root*suffix

        for morpheme, rest in marked_items:
            if rest:  # *morpheme*rest - fragment
                has_fragments = True
            else:  # *word* - full word
                # Check if this is truly a standalone word (followed by space or punctuation)
                pattern = rf'\*{re.escape(morpheme)}\*[\s\.,!?—;:]'
                if re.search(pattern, text):
                    has_full_words = True

        if has_full_words and has_fragments and morpheme_count >= 3:
            violations.append({
                'type': 'INCONSISTENT_MORPHEME_TYPES',
                'severity': 'warning',
                'activity': title,
                'message': 'Activity mixes full words and morpheme fragments',
                'suggestion': 'Use consistent marking: either all full words (*читач*) or all fragments (*при*йшов)',
                'pedagogical_issue': 'Inconsistent marking confuses the pattern students should learn'
            })

    return violations


def check_english_hints_in_activities(yaml_activities: list, level: str, module_num: int) -> list:
    """Check for inappropriate English hints in activities."""
    violations = []

    # Pattern for English hint: (lowercase word or phrase)
    # Excludes grammar annotations: (nom.), (acc.), (pl.), etc.
    english_hint_pattern = r'\([a-z][a-z\s/]+\)'  # (word) or (multiple words)
    grammar_annotation_pattern = r'\([a-z]{2,4}\.\)'  # (nom.), (acc.), etc.

    # Allowed hints for gender agreement testing (possessives)
    # These are needed to indicate WHICH possessive, when testing gender form
    gender_agreement_hints = {
        '(my)', '(your)', '(his)', '(her)', '(its)', '(our)', '(their)',
        '(your informal)', '(your formal)', '(your formal/plural)',
        '(my book)', '(his car)', '(her house)',  # Common examples
    }

    for activity in yaml_activities:
        act_type = activity.type if hasattr(activity, 'type') else activity.get('type', '')
        title = activity.title if hasattr(activity, 'title') else activity.get('title', 'Untitled')

        # Check different activity structures
        text_to_check = ''

        if act_type == 'cloze':
            text_to_check = getattr(activity, 'passage', '')
            if not text_to_check and hasattr(activity, 'get'):
                text_to_check = activity.get('passage', '')
        elif act_type in ('fill-in', 'error-correction'):
            # Check all items
            items = getattr(activity, 'items', [])
            if not items and hasattr(activity, 'get'):
                items = activity.get('items', [])
            
            for item in items:
                if isinstance(item, dict):
                    sentence = item.get('sentence', '')
                else:
                    sentence = getattr(item, 'sentence', '')
                
                text_to_check += sentence + '\n'

        if not text_to_check:
            continue

        # Find all potential English hints
        hints = re.findall(english_hint_pattern, text_to_check)

        # Filter out grammar annotations and allowed gender agreement hints
        real_hints = []
        for hint in hints:
            hint_lower = hint.lower()
            if re.match(grammar_annotation_pattern, hint):
                continue  # Grammar annotation - OK
            if hint_lower in gender_agreement_hints:
                continue  # Gender agreement hint - allowed
            real_hints.append(hint)

        if real_hints:
            severity = 'critical' if len(real_hints) > 5 else 'warning'
            violations.append({
                'type': 'ENGLISH_HINTS_IN_ACTIVITY',
                'severity': severity,
                'activity': title,
                'activity_type': act_type,
                'message': f'Found {len(real_hints)} English hints: {", ".join(real_hints[:5])}{"..." if len(real_hints) > 5 else ""}',
                'suggestion': 'Remove English hints - students should understand from context. For word formation activities, add Ukrainian context instead.',
                'pedagogical_issue': f'English hints make it too easy and defeat the learning objective. Students match English→Ukrainian instead of understanding patterns.',
                'examples': real_hints[:10]
            })

    return violations


def _get_activity_attr(activity, attr: str, default=None):
    """Helper to get attribute from activity object or dictionary."""
    if hasattr(activity, attr):
        return getattr(activity, attr, default)
    elif isinstance(activity, dict):
        return activity.get(attr, default)
    return default


def check_seminar_reading_pairing(yaml_activities: list, level: str) -> list:
    """
    Check that seminar track activities have proper reading-analysis pairing.

    Validation rules:
    1. Every reading activity should have an id field
    2. Analytical activities (essay-response, critical-analysis, comparative-study,
       authorial-intent) should have source_reading linking to a reading id
    3. Orphan readings (not referenced by any analysis) trigger WARNING
    4. Orphan analyses (missing or invalid source_reading) trigger ERROR

    Only applies to seminar tracks: LIT, B2-HIST, C1-HIST, C1-BIO
    """
    violations = []

    # Seminar tracks that require reading-analysis pairing
    seminar_tracks = {'lit', 'b2-hist', 'c1-hist', 'c1-bio', 'c1-bio-seminar'}
    level_lower = level.lower() if level else ''

    # Skip if not a seminar track
    if level_lower not in seminar_tracks:
        return violations

    # Collect reading IDs
    reading_ids = set()
    readings_without_id = []

    for idx, activity in enumerate(yaml_activities):
        act_type = _get_activity_attr(activity, 'type', '')
        title = _get_activity_attr(activity, 'title', f'Activity {idx+1}')

        if act_type == 'reading':
            act_id = _get_activity_attr(activity, 'id')
            if act_id:
                reading_ids.add(act_id)
            else:
                readings_without_id.append(title)

    # Check for readings without ID
    for title in readings_without_id:
        violations.append({
            'type': 'READING_MISSING_ID',
            'severity': 'critical',
            'activity': title,
            'message': 'Reading activity missing required "id" field',
            'suggestion': 'Add id: "reading-01" (or similar) to link with analytical activities'
        })

    # Collect referenced readings from analytical activities
    referenced_readings = set()
    analytical_types = {'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent'}

    for idx, activity in enumerate(yaml_activities):
        act_type = _get_activity_attr(activity, 'type', '')
        title = _get_activity_attr(activity, 'title', f'Activity {idx+1}')

        if act_type in analytical_types:
            source_reading = _get_activity_attr(activity, 'source_reading')

            if source_reading:
                referenced_readings.add(source_reading)
                # Check if source_reading points to valid reading
                if source_reading not in reading_ids:
                    violations.append({
                        'type': 'INVALID_SOURCE_READING',
                        'severity': 'critical',
                        'activity': title,
                        'message': f'source_reading "{source_reading}" not found in module readings',
                        'suggestion': f'Valid reading IDs: {", ".join(sorted(reading_ids)) if reading_ids else "(none defined)"}'
                    })
            else:
                # Missing source_reading - this is a warning (recommended but not required)
                violations.append({
                    'type': 'MISSING_SOURCE_READING',
                    'severity': 'warning',
                    'activity': title,
                    'activity_type': act_type,
                    'message': f'{act_type} activity lacks source_reading link',
                    'suggestion': 'Add source_reading: "reading-XX" to link this analysis to its source text'
                })

    # Check for orphan readings (defined but never referenced)
    orphan_readings = reading_ids - referenced_readings
    for reading_id in orphan_readings:
        # Find the reading title
        reading_title = reading_id
        for activity in yaml_activities:
            act_id = _get_activity_attr(activity, 'id')
            if act_id == reading_id:
                reading_title = _get_activity_attr(activity, 'title', reading_id)
                break

        violations.append({
            'type': 'ORPHAN_READING',
            'severity': 'warning',
            'activity': reading_title,
            'message': f'Reading "{reading_id}" is not referenced by any analytical activity',
            'suggestion': 'Add source_reading: "{}" to an essay-response, critical-analysis, or comparative-study'.format(reading_id)
        })

    return violations


__all__ = [
    'check_unjumble_empty_jumbled',
    'check_mdx_unjumble_rendering',
    'check_morpheme_patterns',
    'check_mark_the_words_format',
    'check_morpheme_pedagogy',
    'check_english_hints_in_activities',
    'check_seminar_reading_pairing',
]
