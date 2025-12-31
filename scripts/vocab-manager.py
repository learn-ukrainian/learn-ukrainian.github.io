#!/usr/bin/env python3
"""
Vocabulary Manager for Learn Ukrainian

Manages the master vocabulary database with proper lemma tracking.
Ensures each lemma is introduced once and tracks module ownership.

Usage:
    python scripts/vocab-manager.py build [curriculum]     # Build vocab.csv from modules
    python scripts/vocab-manager.py stats [curriculum]     # Show statistics
    python scripts/vocab-manager.py check [curriculum]     # Validate modules against vocab
    python scripts/vocab-manager.py duplicates [curriculum] # Find duplicate lemmas

Examples:
    python scripts/vocab-manager.py build l2-uk-en
    python scripts/vocab-manager.py stats l2-uk-en
"""

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def get_level_from_module(module_num: int) -> str:
    """Determine CEFR level from module number."""
    if module_num <= 30:
        return 'A1'
    elif module_num <= 65:
        return 'A2'
    elif module_num <= 100:
        return 'B1'
    elif module_num <= 135:
        return 'B2'
    elif module_num <= 170:
        return 'C1'
    else:
        return 'C2'


def extract_vocabulary_from_module(filepath: str) -> list[dict]:
    """Extract vocabulary entries from a module file."""
    words = []

    match = re.search(r'module-(\d+)\.md$', filepath)
    if not match:
        return words
    module_num = int(match.group(1))
    level = get_level_from_module(module_num)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find vocabulary section with table
    vocab_match = re.search(
        r'# Vocabulary\n\n\|[^\n]+\|\n\|[-\|\s]+\|\n(.*?)(?=\n---|\n#|\Z)',
        content,
        re.DOTALL
    )

    if not vocab_match:
        return words

    vocab_section = vocab_match.group(1)
    for line in vocab_section.strip().split('\n'):
        if line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            # Expected: | word | ipa | english | pos | gender | note |
            if len(parts) >= 5:
                word = parts[1]
                ipa = parts[2] if len(parts) > 2 else ''
                english = parts[3] if len(parts) > 3 else ''
                pos = parts[4] if len(parts) > 4 else ''
                gender = parts[5] if len(parts) > 5 else ''
                note = parts[6] if len(parts) > 6 else ''

                # Skip header rows or empty
                if word and re.search(r'[А-ЯІЇЄҐа-яіїєґ]', word):
                    words.append({
                        'lemma': word,
                        'ipa': ipa,
                        'english': english,
                        'pos': pos,
                        'gender': gender,
                        'note': note,
                        'module': module_num,
                        'level': level,
                    })

    return words


def build_vocabulary(curriculum_path: str) -> list[dict]:
    """Build vocabulary list from all modules, keeping first occurrence."""
    modules_path = Path(curriculum_path) / 'modules'

    if not modules_path.exists():
        print(f"Error: Modules path not found: {modules_path}")
        sys.exit(1)

    # Track lemmas: keep first occurrence only
    lemma_registry = {}  # lemma -> full entry
    duplicates = defaultdict(list)  # lemma -> list of modules

    module_files = sorted(modules_path.glob('module-*.md'))

    for filepath in module_files:
        words = extract_vocabulary_from_module(str(filepath))
        for entry in words:
            lemma = entry['lemma']
            module = entry['module']

            if lemma in lemma_registry:
                # Duplicate - record it
                duplicates[lemma].append(module)
            else:
                # First occurrence - register it
                lemma_registry[lemma] = entry
                duplicates[lemma].append(module)

    return list(lemma_registry.values()), duplicates


def save_vocabulary_csv(vocab: list[dict], output_path: str):
    """Save vocabulary to CSV file."""
    fieldnames = ['lemma', 'ipa', 'english', 'pos', 'gender', 'module', 'level', 'note']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in sorted(vocab, key=lambda x: (x['level'], x['module'], x['lemma'])):
            writer.writerow(entry)

    print(f"Saved {len(vocab)} lemmas to {output_path}")


def load_vocabulary_csv(csv_path: str) -> list[dict]:
    """Load vocabulary from CSV file."""
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def print_stats(vocab: list[dict], duplicates: dict):
    """Print vocabulary statistics."""
    # Count by level
    by_level = defaultdict(list)
    for entry in vocab:
        by_level[entry['level']].append(entry)

    # Targets
    targets = {
        'A1': 250,
        'A2': 500,
        'B1': 750,
        'B2': 1000,
        'C1': 1250,
        'C2': 1500,
    }

    print("=" * 70)
    print("VOCABULARY STATISTICS (LEMMA-BASED)")
    print("=" * 70)
    print(f"\nTotal unique lemmas: {len(vocab)}")

    print("\n" + "-" * 70)
    print("BY LEVEL")
    print("-" * 70)

    cumulative = 0
    for level in sorted(by_level.keys()):
        count = len(by_level[level])
        cumulative += count
        target = targets.get(level, 0)
        status = "✓" if cumulative >= target else "✗"
        print(f"  {level}: {count} new lemmas (cumulative: {cumulative}, target: {target}+) {status}")

    print("\n" + "-" * 70)
    print("BY PART OF SPEECH")
    print("-" * 70)

    by_pos = defaultdict(int)
    for entry in vocab:
        pos = entry.get('pos', 'unknown') or 'unknown'
        by_pos[pos] += 1

    for pos, count in sorted(by_pos.items(), key=lambda x: -x[1]):
        print(f"  {pos}: {count}")

    # Duplicates summary
    multi_module = {k: v for k, v in duplicates.items() if len(v) > 1}
    if multi_module:
        print("\n" + "-" * 70)
        print(f"LEMMAS APPEARING IN MULTIPLE MODULES: {len(multi_module)}")
        print("-" * 70)
        print("(First module 'owns' the lemma, others reuse it)")
        for lemma, modules in sorted(multi_module.items(), key=lambda x: x[1][0]):
            owner = modules[0]
            reused = modules[1:]
            print(f"  {lemma}: introduced M{owner:02d}, reused in M{', M'.join(f'{m:02d}' for m in reused)}")


def find_duplicates(curriculum_path: str):
    """Find and report duplicate lemmas across modules."""
    _, duplicates = build_vocabulary(curriculum_path)

    multi_module = {k: v for k, v in duplicates.items() if len(v) > 1}

    print("=" * 70)
    print("DUPLICATE LEMMA ANALYSIS")
    print("=" * 70)
    print(f"\nLemmas appearing in multiple module vocabulary tables: {len(multi_module)}")
    print("\nThese should be reviewed - each lemma should only be in ONE module's vocab table.")
    print("Other modules can USE the word but shouldn't list it as new vocabulary.\n")

    if multi_module:
        print("-" * 70)
        for lemma, modules in sorted(multi_module.items(), key=lambda x: (x[1][0], x[0])):
            level = get_level_from_module(modules[0])
            print(f"  {lemma} ({level}): modules {modules}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    curriculum = sys.argv[2] if len(sys.argv) > 2 else 'l2-uk-en'

    # Build curriculum path
    curriculum_path = Path('curriculum') / curriculum
    if not curriculum_path.exists():
        curriculum_path = Path(curriculum)

    if not curriculum_path.exists():
        print(f"Error: Curriculum not found: {curriculum}")
        sys.exit(1)

    vocab_csv_path = curriculum_path / 'vocabulary.csv'

    if command == 'build':
        vocab, duplicates = build_vocabulary(str(curriculum_path))
        save_vocabulary_csv(vocab, str(vocab_csv_path))
        print_stats(vocab, duplicates)

    elif command == 'stats':
        if vocab_csv_path.exists():
            vocab = load_vocabulary_csv(str(vocab_csv_path))
            # Rebuild duplicates for stats
            _, duplicates = build_vocabulary(str(curriculum_path))
            print_stats(vocab, duplicates)
        else:
            print(f"No vocabulary.csv found. Run 'build' first.")
            vocab, duplicates = build_vocabulary(str(curriculum_path))
            print_stats(vocab, duplicates)

    elif command == 'duplicates':
        find_duplicates(str(curriculum_path))

    elif command == 'check':
        # TODO: Validate modules against vocab.csv
        print("Check command not yet implemented")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
