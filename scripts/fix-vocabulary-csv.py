#!/usr/bin/env python3
"""
Fix vocabulary.csv data quality issues for B1 entries.
Issues addressed:
1. Normalize aspect pairs (impf/pf in pos → verb with aspect in note)
2. Normalize motion types (uni/multi in pos → verb with motion type in note)
3. Fix column shifts from CSV parsing issues
4. Standardize non-standard POS values
5. Ensure proper gender values
"""

import csv
import sys
from pathlib import Path

# Valid POS values
VALID_POS = {'noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'pron', 'num', 'phrase', 'fixed expr', 'particle', 'interjection'}

# Valid gender values
VALID_GENDER = {'m', 'f', 'n', 'pl', '-', ''}

def fix_entry(row):
    """Fix a single vocabulary entry and return the corrected row."""
    if len(row) < 7:
        return row, []

    lemma, ipa, english, pos, gender, module, level = row[:7]
    note = row[7] if len(row) > 7 else ''
    issues = []

    # Trim whitespace
    pos = pos.strip()
    gender = gender.strip()
    note = note.strip()

    # Fix 1: Aspect pairs - impf/pf in pos field with paired verb in gender
    if pos in ('impf', 'pf', 'imperfective', 'perfective'):
        aspect_note = 'impf' if pos in ('impf', 'imperfective') else 'pf'
        paired_verb = gender if gender and not gender in VALID_GENDER else ''

        # Add aspect to note
        if note:
            note = f"{aspect_note}; paired: {paired_verb}; {note}" if paired_verb else f"{aspect_note}; {note}"
        else:
            note = f"{aspect_note}; paired: {paired_verb}" if paired_verb else aspect_note

        pos = 'verb'
        gender = '-'
        issues.append(f"Fixed aspect pair format: {lemma}")

    # Fix 2: Motion type in pos field
    elif pos in ('uni', 'multi'):
        motion_note = 'unidirectional' if pos == 'uni' else 'multidirectional'
        if note:
            note = f"{motion_note}; {note}"
        else:
            note = motion_note
        pos = 'verb'
        gender = '-'
        issues.append(f"Fixed motion type format: {lemma}")

    # Fix 3: Gender value in pos field (column shift)
    elif pos in ('m', 'f', 'n', 'pl') and gender == '':
        # This is a shifted entry - pos contains gender, need to determine real POS
        # Most of these are nouns
        gender = pos
        pos = 'noun'
        issues.append(f"Fixed shifted columns (gender→pos): {lemma}")

    # Fix 4: Semantic labels as POS
    elif pos in ('figurative', 'idiom'):
        if note:
            note = f"{pos}; {note}"
        else:
            note = pos
        pos = 'phrase'
        gender = '-'
        issues.append(f"Fixed semantic label as POS: {lemma}")

    elif pos in ('urgency', 'encouragement', 'deadline', 'genitive', 'signals imperfective', 'often with perfective'):
        if note:
            note = f"{pos}; {note}"
        else:
            note = pos
        # Determine likely POS from context
        pos = 'adv'  # Most of these are adverbial expressions
        gender = '-'
        issues.append(f"Fixed semantic label as POS: {lemma}")

    elif pos in ('+ infinitive', '+ imperfective'):
        if note:
            note = f"usage: {pos}; {note}"
        else:
            note = f"usage: {pos}"
        pos = 'verb'
        gender = '-'
        issues.append(f"Fixed usage pattern as POS: {lemma}")

    elif pos == 'grammar term':
        pos = 'noun'
        gender = '-'
        if note:
            note = f"grammar term; {note}"
        else:
            note = 'grammar term'
        issues.append(f"Fixed grammar term: {lemma}")

    # Fix 5: Missing POS (dash)
    elif pos == '-':
        # Try to infer from lemma or context
        if 'ся' in lemma or 'ти' in lemma[-2:]:
            pos = 'verb'
        elif lemma in ('сюди', 'туди', 'звідси', 'більше не', 'ні... ні', 'весь час', 'за годину'):
            pos = 'adv'
        else:
            pos = 'phrase'  # Default for unclear cases
        issues.append(f"Inferred POS for: {lemma}")

    # Fix 6: Check for CSV parsing issues (pos contains partial English)
    elif pos.startswith(' ') or '"' in pos:
        # This is a parsing issue - try to extract the real pos from the mess
        issues.append(f"CSV parsing issue detected: {lemma} (manual review needed)")
        # Keep as-is for manual review, but flag it

    # Ensure gender is valid
    if gender not in VALID_GENDER and pos in ('noun',):
        if gender in ('m', 'f', 'n', 'pl'):
            pass  # Already valid
        elif gender.startswith(('а', 'о', 'у', 'е', 'и', 'і', 'я', 'є', 'ї', 'ю')):
            # Likely a Ukrainian word (paired verb) - for verbs, gender should be -
            gender = '-'
        else:
            gender = '-'
            issues.append(f"Reset invalid gender for: {lemma}")

    return [lemma, ipa, english, pos, gender, module, level, note], issues

def process_csv(input_path, output_path):
    """Process the entire CSV file and fix issues."""
    all_issues = []
    fixed_rows = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        fixed_rows.append(header)

        for row in reader:
            if len(row) < 7:
                fixed_rows.append(row)
                continue

            # Only process B1 entries for now
            if row[6] == 'B1':
                fixed_row, issues = fix_entry(row)
                fixed_rows.append(fixed_row)
                all_issues.extend(issues)
            else:
                fixed_rows.append(row)

    # Write fixed CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(fixed_rows)

    return all_issues

def main():
    vocab_path = Path('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/vocabulary.csv')
    output_path = vocab_path  # Overwrite in place

    print("Fixing vocabulary.csv B1 entries...")
    issues = process_csv(vocab_path, output_path)

    print(f"\nFixed {len(issues)} issues:")
    for issue in issues[:50]:
        print(f"  - {issue}")

    if len(issues) > 50:
        print(f"  ... and {len(issues) - 50} more")

    print(f"\nDone! Updated {vocab_path}")

if __name__ == '__main__':
    main()
