#!/usr/bin/env python3
"""
Check if any planned "Core Vocabulary" words were completely forgotten
across all A1-B2 modules.

Not checking per-module accuracy, just:
- Is word X in ANY A1-B2 vocabulary YAML?
"""

import re
import yaml
from pathlib import Path
from collections import defaultdict

LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2']


def parse_plan_vocabulary(plan_path: Path) -> set:
    """Extract all vocabulary from a curriculum plan (all modules)."""
    content = plan_path.read_text(encoding='utf-8')

    vocab_pattern = re.compile(r'\*\*Vocabulary\s+\(\d+\s+words?\):\*\*\s*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)

    all_words = set()

    for vocab_match in vocab_pattern.finditer(content):
        raw_vocab = vocab_match.group(1).strip()
        # Clean up
        clean_vocab = re.sub(r'\([^)]*\)', '', raw_vocab)
        clean_vocab = clean_vocab.replace('...', '')

        words = [w.strip().lower() for w in clean_vocab.split(',')
                if w.strip() and not w.strip().startswith('[')
                and 'review' not in w.lower()]

        all_words.update(words)

    return all_words


def get_all_implemented_vocabulary(level: str) -> set:
    """Get all vocabulary from all YAML files in a level."""
    project_root = Path(__file__).parent.parent
    vocab_dir = project_root / 'curriculum' / 'l2-uk-en' / level.lower() / 'vocabulary'

    all_words = set()

    for vocab_file in vocab_dir.glob('*.yaml'):
        try:
            with open(vocab_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'items' not in data:
                continue

            for item in data['items']:
                if 'lemma' in item:
                    all_words.add(item['lemma'].lower())

        except Exception as e:
            print(f"⚠️  Error reading {vocab_file.name}: {e}")

    return all_words


def main():
    print("=" * 80)
    print("MISSING CORE WORDS CHECK")
    print("Are any planned words completely absent from A1-B2 implementation?")
    print("=" * 80)
    print()

    project_root = Path(__file__).parent.parent
    plan_dir = project_root / 'docs' / 'l2-uk-en'

    # Get all planned vocabulary across A1-B2
    all_planned = set()
    planned_by_level = {}

    print("📖 Reading curriculum plans...")
    for level in LEVEL_ORDER:
        plan_file = plan_dir / f'{level}-CURRICULUM-PLAN.md'
        if not plan_file.exists():
            continue

        level_planned = parse_plan_vocabulary(plan_file)
        planned_by_level[level] = level_planned
        all_planned.update(level_planned)
        print(f"   {level}: {len(level_planned)} words in plan")

    print(f"\n📚 Total unique words across A1-B2 plans: {len(all_planned)}")
    print()

    # Get all implemented vocabulary across A1-B2
    all_implemented = set()
    implemented_by_level = {}

    print("📂 Reading vocabulary YAML files...")
    for level in LEVEL_ORDER:
        level_vocab = get_all_implemented_vocabulary(level)
        implemented_by_level[level] = level_vocab
        all_implemented.update(level_vocab)
        print(f"   {level}: {len(level_vocab)} words in YAML files")

    print(f"\n✅ Total unique words across A1-B2 YAMLs: {len(all_implemented)}")
    print()

    # Find completely missing words
    completely_missing = all_planned - all_implemented

    # Also check if any planned word appears in a LATER level
    missing_by_level = {}
    for level in LEVEL_ORDER:
        level_planned = planned_by_level[level]
        level_implemented = implemented_by_level[level]

        # Words planned for this level but missing from this level
        level_missing = level_planned - level_implemented

        # But might be in later levels (teaching order changed)
        level_missing_but_taught_later = set()
        for word in level_missing:
            for later_level in LEVEL_ORDER[LEVEL_ORDER.index(level)+1:]:
                if word in implemented_by_level[later_level]:
                    level_missing_but_taught_later.add(word)
                    break

        # Words planned for this level, missing from this level, and never taught later
        truly_missing_from_level = level_missing - level_missing_but_taught_later

        missing_by_level[level] = {
            'taught_later': level_missing_but_taught_later,
            'never_taught': truly_missing_from_level & completely_missing
        }

    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    if not completely_missing:
        print("✅ SUCCESS: ALL planned vocabulary was taught somewhere in A1-B2!")
        print()
        print("Some words may have moved to different modules/levels,")
        print("but every planned word appears in at least one YAML file.")
        print()
        return 0

    # Show completely missing words
    print(f"❌ Found {len(completely_missing)} words planned but NEVER taught in A1-B2:")
    print()

    # Group by which level planned them
    missing_by_origin = defaultdict(list)
    for level in LEVEL_ORDER:
        for word in planned_by_level[level]:
            if word in completely_missing:
                missing_by_origin[level].append(word)

    for level in LEVEL_ORDER:
        if missing_by_origin[level]:
            print(f"{level} planned ({len(missing_by_origin[level])} missing):")
            for word in sorted(missing_by_origin[level])[:20]:
                print(f"   - {word}")
            if len(missing_by_origin[level]) > 20:
                print(f"   ... and {len(missing_by_origin[level]) - 20} more")
            print()

    # Also show summary of teaching order changes
    print("=" * 80)
    print("TEACHING ORDER CHANGES (words taught, but in different level)")
    print("=" * 80)
    print()

    for level in LEVEL_ORDER:
        taught_later = missing_by_level[level]['taught_later']
        if taught_later:
            print(f"{level} → moved to later levels: {len(taught_later)} words")
            for word in sorted(taught_later)[:10]:
                # Find where it was actually taught
                for later_level in LEVEL_ORDER[LEVEL_ORDER.index(level)+1:]:
                    if word in implemented_by_level[later_level]:
                        print(f"   - {word} (taught in {later_level})")
                        break
            if len(taught_later) > 10:
                print(f"   ... and {len(taught_later) - 10} more")
            print()

    return 1 if completely_missing else 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
