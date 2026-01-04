"""Activity validation check for audit system."""

import re
import json
from pathlib import Path
from typing import Dict, List


def check_unjumble_empty_jumbled(yaml_activities: list) -> list:
    """Check for unjumble activities with empty jumbled fields (Issue #362)."""
    violations = []

    for activity in yaml_activities:
        if activity.get('type') not in ['unjumble', 'anagram']:
            continue

        items = activity.get('items', [])
        title = activity.get('title', 'Untitled')

        for item_idx, item in enumerate(items, 1):
            # Check if item has none of the valid field formats
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
    """Check for valid morpheme patterns in mark-the-words activities (Issue #363).

    Supports three pattern types:
    - *prefix*rest (e.g., *при*йшов)
    - rest*suffix* (e.g., Чит*ач*)
    - *wholeWord* (e.g., *Читач*)
    """
    violations = []

    for activity in yaml_activities:
        if activity.get('type') != 'mark-the-words':
            continue

        text = activity.get('text', '')
        title = activity.get('title', 'Untitled')

        # Pattern: (prefix)*morpheme*(suffix)
        # Group 1: optional text before * (prefix of word)
        # Group 2: morpheme inside * * (the part to highlight)
        # Group 3: optional text after * (suffix of word)
        morpheme_pattern = r'([а-яіїєґА-ЯІЇЄҐ]*)\*([а-яіїєґА-ЯІЇЄҐ]+)\*([а-яіїєґА-ЯІЇЄҐ]*)'
        matches = list(re.finditer(morpheme_pattern, text))

        if not matches:
            # No morpheme patterns found - this is fine, could be full word matching
            continue

        # Validate each morpheme pattern
        for match in matches:
            prefix = match.group(1)      # Text before morpheme
            morpheme = match.group(2)    # The morpheme to highlight
            suffix = match.group(3)      # Text after morpheme
            full_word = prefix + morpheme + suffix

            # Skip if no word context (isolated *morpheme* without prefix or suffix)
            if not full_word or full_word == morpheme:
                # This is a standalone morpheme like *при* - allowed
                continue

            # Remove asterisks to get the actual text
            plain_text = re.sub(r'[а-яіїєґА-ЯІЇЄҐ]*\*([а-яіїєґА-ЯІЇЄҐ]+)\*[а-яіїєґА-ЯІЇЄҐ]*',
                               lambda m: m.group(0).replace('*', ''), text)

            # Verify the full word exists in the plain text
            if full_word.lower() not in plain_text.lower():
                violations.append({
                    'type': 'INVALID_MORPHEME_WORD',
                    'severity': 'error',
                    'activity': title,
                    'message': f'Morpheme pattern "{prefix}*{morpheme}*{suffix}" constructs word "{full_word}" which is not found in the text',
                    'suggestion': f'Verify morpheme pattern is correct or word "{full_word}" exists in text'
                })

            # Verify morpheme is actually part of the full word
            if morpheme.lower() not in full_word.lower():
                violations.append({
                    'type': 'INVALID_MORPHEME_POSITION',
                    'severity': 'error',
                    'activity': title,
                    'message': f'Morpheme "{morpheme}" not found in word "{full_word}"',
                    'suggestion': f'Morpheme should be part of the word, e.g., "*при*йшов" or "Чит*ач*"'
                })

    return violations


def check_mark_the_words_format(yaml_activities: list) -> list:
    """Check mark-the-words activities have consistent format (brackets or asterisks, not both)."""
    violations = []

    for activity in yaml_activities:
        if activity.get('type') != 'mark-the-words':
            continue

        text = activity.get('text', '')
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


def check_morpheme_pedagogy(yaml_activities: list) -> list:
    """
    Check for pedagogically weak morpheme activities.

    Detects:
    1. Vague instructions ("prefix, suffix, or root" - unclear what to click)
    2. Too many possible answers (>10 marked morphemes)
    3. Inconsistent morpheme types (mixing prefixes, roots, whole words)

    These activities are pedagogically weak because:
    - Students don't know what specific pattern to look for
    - Multiple valid interpretations exist
    - No clear learning objective
    """
    violations = []

    for activity in yaml_activities:
        if activity.get('type') != 'mark-the-words':
            continue

        text = activity.get('text', '')
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
    """
    Check for inappropriate English hints in activities.

    English hints like "(arrived)", "(reader)", "(entrance)" make activities too easy
    and defeat the learning objective. Students should understand meaning from context,
    not match English translations.

    Grammar annotations like "(nom.)", "(acc.)", "(adj)", "(imp)" are OK - those are
    linguistic metadata, not translation hints.
    """
    violations = []

    # Pattern for English hint: (lowercase word or phrase)
    # Excludes grammar annotations: (nom.), (acc.), (pl.), etc.
    english_hint_pattern = r'\([a-z][a-z\s]+\)'  # (word) or (multiple words)
    grammar_annotation_pattern = r'\([a-z]{2,4}\.\)'  # (nom.), (acc.), etc.

    for activity in yaml_activities:
        act_type = activity.get('type', '')
        title = activity.get('title', 'Untitled')

        # Check different activity structures
        text_to_check = ''

        if act_type == 'cloze':
            text_to_check = activity.get('passage', '')
        elif act_type == 'fill-in':
            # Check all items
            items = activity.get('items', [])
            for item in items:
                sentence = item.get('sentence', '')
                text_to_check += sentence + '\n'
        elif act_type == 'error-correction':
            # Check all items
            items = activity.get('items', [])
            for item in items:
                sentence = item.get('sentence', '')
                text_to_check += sentence + '\n'

        if not text_to_check:
            continue

        # Find all potential English hints
        hints = re.findall(english_hint_pattern, text_to_check)

        # Filter out grammar annotations
        real_hints = []
        for hint in hints:
            if not re.match(grammar_annotation_pattern, hint):
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


__all__ = [
    'check_unjumble_empty_jumbled',
    'check_mdx_unjumble_rendering',
    'check_morpheme_patterns',
    'check_mark_the_words_format',
    'check_morpheme_pedagogy',
    'check_english_hints_in_activities',
]
