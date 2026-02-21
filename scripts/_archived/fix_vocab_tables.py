#!/usr/bin/env python3
"""
Transform vocabulary tables from 3-4 column format to 6-column format.

Current A2 formats:
- | Ukrainian | IPA | English | Category |
- | Ukrainian | IPA | English | Aspect |
- | Ukrainian | IPA | English |

Target format:
- | Word | IPA | English | POS | Gender | Note |

Usage:
    python3 scripts/fix_vocab_tables.py curriculum/l2-uk-en/a2/*.md
"""

import re
import sys
import os
from pathlib import Path

# POS inference from Category/Aspect field
POS_MAP = {
    # Direct mappings
    'verb': 'verb',
    'noun': 'noun',
    'adj': 'adj',
    'adv': 'adv',
    'prep': 'prep',
    'preposition': 'prep',
    'conj': 'conj',
    'conjunction': 'conj',
    'pron': 'pron',
    'pronoun': 'pron',
    'phrase': 'phrase',
    'interj': 'interj',
    'interjection': 'interj',
    'particle': 'part',
    'numeral': 'num',

    # Category-based inference
    'transport': 'noun',
    'grammar': 'noun',
    'service': 'noun',
    'question': 'pron',
    'linking verb': 'verb',
    'dative pronoun': 'pron',
    'irregular': 'adj',

    # Aspect markers -> verb
    'impf': 'verb',
    'pf': 'verb',
    'impf fut': 'verb',
    'pf fut': 'verb',
    'pf past': 'verb',
    'impf past': 'verb',
}

# Gender inference patterns for Ukrainian nouns
def infer_gender(word):
    """Infer gender from Ukrainian word ending."""
    word = word.strip().lower()

    # Remove any slashes for gender variants like "радий/рада"
    if '/' in word:
        word = word.split('/')[0]

    # Common patterns
    if word.endswith(('ість', 'ость', 'ня', 'ка', 'ва', 'да', 'ба', 'ція', 'сія', 'га', 'ха', 'за', 'ча', 'ша', 'ща', 'жа')):
        return 'f'
    if word.endswith(('а', 'я')) and not word.endswith(('ття', 'ння', 'лля')):
        return 'f'
    if word.endswith(('о', 'е', 'я', 'ття', 'ння', 'лля')):
        return 'n'
    if word.endswith(('ий', 'ій', 'ок', 'ик', 'ак', 'ар', 'ень', 'ач', 'ець', 'ник')):
        return 'm'

    # Default to masculine for consonant endings
    if word and word[-1] not in 'аеиіоуяєї':
        return 'm'

    return '-'

def infer_pos_from_word(word):
    """Infer POS from word patterns."""
    word = word.strip().lower()

    # Handle slashes (gender variants like "радий/рада")
    if '/' in word:
        word = word.split('/')[0]

    # Verb patterns (infinitives)
    if word.endswith(('ти', 'тись', 'ться')):
        return 'verb'

    # Adjective patterns
    if word.endswith(('ий', 'ій', 'иї', 'ої')):
        return 'adj'

    # Feminine adjective
    if word.endswith(('ша', 'ше', 'ші')) and len(word) > 4:
        return 'adj'

    # Comparative/superlative adjectives
    if word.startswith('най') and len(word) > 5:
        return 'adj'

    # Adverb patterns (predicative)
    adverb_markers = ('потрібно', 'необхідно', 'цікаво', 'добре', 'погано', 'гарно',
                      'приємно', 'легко', 'важко', 'швидко', 'повільно', 'далеко',
                      'близько', 'тут', 'там', 'вчора', 'сьогодні', 'завтра',
                      'спочатку', 'потім', 'тепер', 'раніше', 'пізніше')
    if word in adverb_markers:
        return 'adv'

    # Conjunction patterns
    conjunctions = ('і', 'й', 'та', 'або', 'чи', 'що', 'щоб', 'бо', 'тому', 'якщо',
                    'якби', 'коли', 'поки', 'хоча', 'як', 'ніж')
    if word in conjunctions or word.startswith('тому що'):
        return 'conj'

    # Preposition patterns
    prepositions = ('в', 'у', 'на', 'з', 'із', 'зі', 'до', 'від', 'без', 'для',
                    'про', 'через', 'над', 'під', 'між', 'за', 'перед', 'біля')
    if word in prepositions:
        return 'prep'

    # Pronoun patterns
    pronouns = ('я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони',
                'мене', 'тебе', 'його', 'її', 'нас', 'вас', 'їх',
                'мені', 'тобі', 'йому', 'їй', 'нам', 'вам', 'їм',
                'мною', 'тобою', 'ним', 'нею', 'нами', 'вами', 'ними',
                'який', 'яка', 'яке', 'які', 'чий', 'чия', 'чиє', 'чиї',
                'цей', 'ця', 'це', 'ці', 'той', 'та', 'те', 'ті',
                'хто', 'що', 'себе', 'собі', 'собою')
    if word in pronouns:
        return 'pron'

    # Noun patterns - be generous since most words are nouns
    # Feminine noun endings
    if word.endswith(('ість', 'ость', 'ція', 'сія', 'ка', 'ня', 'ва', 'да', 'ба', 'ла', 'ма', 'на', 'па', 'ра', 'са', 'та', 'ша', 'ча', 'ща', 'жа', 'за', 'ха', 'га', 'фа')):
        return 'noun'
    if word.endswith(('а', 'я')) and len(word) > 2:
        # Most -а/-я endings are feminine nouns
        return 'noun'

    # Neuter noun endings
    if word.endswith(('о', 'е', 'ття', 'ння', 'лля', 'ення', 'ання')):
        return 'noun'

    # Masculine noun endings (consonant final)
    if len(word) > 2 and word[-1] not in 'аеиіоуяєїь':
        return 'noun'

    # Soft masculine nouns
    if word.endswith('ь') and len(word) > 2:
        return 'noun'

    return 'noun'  # Default to noun

def transform_vocabulary_table(content):
    """Transform vocabulary table to 6-column format."""
    lines = content.split('\n')
    modified = False
    in_vocab_section = False
    new_lines = []

    for i, line in enumerate(lines):
        # Detect vocabulary section
        if line.strip() == '# Vocabulary':
            in_vocab_section = True
            new_lines.append(line)
            continue

        # End of vocabulary section
        if in_vocab_section and line.startswith('---'):
            in_vocab_section = False
            new_lines.append(line)
            continue

        if not in_vocab_section:
            new_lines.append(line)
            continue

        # Process table lines in vocabulary section
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            # parts[0] is empty (before first |), parts[-1] may be empty (after last |)
            cols = [p for p in parts if p or p == '']

            # Handle header row
            if any(h in line.lower() for h in ['ukrainian', 'word', 'ipa', '---']):
                if '---' in line:
                    # Separator row - make it 6 columns
                    new_lines.append('| --- | --- | --- | --- | --- | --- |')
                    modified = True
                else:
                    # Header row - standardize
                    new_lines.append('| Word | IPA | English | POS | Gender | Note |')
                    modified = True
                continue

            # Skip non-table content
            if len(cols) < 4:  # Need at least | word | ipa | english |
                new_lines.append(line)
                continue

            # Extract existing data
            word = cols[1] if len(cols) > 1 else ''
            ipa = cols[2] if len(cols) > 2 else ''
            english = cols[3] if len(cols) > 3 else ''
            col4 = cols[4] if len(cols) > 4 else ''

            # Skip empty rows
            if not word or word == 'Word':
                new_lines.append(line)
                continue

            # Handle previously transformed 6-column rows
            is_6col = len(cols) >= 7

            # Infer POS
            pos = None
            note = ''
            col5 = cols[5] if len(cols) > 5 else ''
            col6 = cols[6] if len(cols) > 6 else ''

            if is_6col:
                # Already 6-column format - check if POS/Gender need re-inference
                existing_pos = col4
                existing_gender = col5
                existing_note = col6

                if existing_pos and existing_pos != '-':
                    # Keep existing good data
                    pos = existing_pos
                    note = existing_note
                else:
                    # Need to re-infer
                    pos = infer_pos_from_word(word)
                    note = existing_note
            else:
                # Original 3-4 column format - transform
                # Check col4 for POS-like info
                col4_lower = col4.lower() if col4 else ''
                if col4_lower in POS_MAP:
                    pos = POS_MAP[col4_lower]
                    note = ''  # POS info moved to proper column
                elif col4_lower and col4_lower.split()[0] in POS_MAP:
                    pos = POS_MAP[col4_lower.split()[0]]
                    note = col4  # Keep full info as note
                elif col4_lower.startswith(('impf', 'pf')):
                    pos = 'verb'
                    note = col4
                elif col4:
                    # Keep as note if not recognizable
                    note = col4

                # Infer POS from word if not determined
                if not pos:
                    pos = infer_pos_from_word(word)

            # Infer gender for nouns
            gender = '-'
            if pos == 'noun':
                gender = infer_gender(word)
            elif is_6col and col5 and col5 != '-':
                gender = col5  # Keep existing gender

            # Build new row
            new_line = f'| {word} | {ipa} | {english} | {pos} | {gender} | {note} |'
            new_lines.append(new_line)
            modified = True
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), modified

def process_file(filepath):
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for "no vocabulary" type messages
    if 'no new vocabulary' in content.lower() or 'review module' in content.lower():
        return False

    new_content, modified = transform_vocabulary_table(content)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Transformed vocabulary table in {os.path.basename(filepath)}")
        return True

    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_vocab_tables.py <file.md> [file2.md ...]")
        print("       python3 fix_vocab_tables.py curriculum/l2-uk-en/a2/*.md")
        sys.exit(1)

    files = sys.argv[1:]
    total_fixed = 0

    for filepath in files:
        if os.path.isfile(filepath) and filepath.endswith('.md'):
            if process_file(filepath):
                total_fixed += 1

    print(f"\n✅ Transformed vocabulary tables in {total_fixed} files.")

if __name__ == "__main__":
    main()
