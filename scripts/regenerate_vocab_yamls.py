#!/usr/bin/env python3
"""
Regenerate vocabulary YAML files from vocabulary.db for all A1-B2 modules.

Usage:
    .venv/bin/python scripts/regenerate_vocab_yamls.py [--levels a1,a2,b1,b2] [--dry-run]

Examples:
    .venv/bin/python scripts/regenerate_vocab_yamls.py --dry-run
    .venv/bin/python scripts/regenerate_vocab_yamls.py --levels a1,a2
"""

import argparse
import sqlite3
import yaml
from pathlib import Path
from typing import List, Dict

# Configuration
CURRICULUM_DIR = Path("curriculum/l2-uk-en")
DB_PATH = CURRICULUM_DIR / "vocabulary.db"

# Module ranges by level (sequential numbering across all levels)
# Each level has internal numbering 1-N, mapped to sequential numbering:
LEVEL_RANGES = {
    'A1': (1, 44),       # A1 M1-44 → Sequential 1-44 (44 modules)
    'A2': (45, 114),     # A2 M1-70 → Sequential 45-114 (70 modules)
    'B1': (115, 206),    # B1 M1-92 → Sequential 115-206 (92 modules)
    'B2': (207, 300),    # B2 M1-94 → Sequential 207-300 (94 modules)
}

def get_db_connection():
    """Get database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_module_slug(level: str, module_in_level: int) -> str:
    """
    Get module slug by finding the corresponding .md file.

    Args:
        level: Level code (a1, a2, b1, b2)
        module_in_level: Module number within the level (1-based)

    Returns:
        Slug extracted from filename (e.g., "the-cyrillic-code-i")
    """
    level_dir = CURRICULUM_DIR / level.lower()

    # Look for module file with this number
    pattern = f"{module_in_level:02d}-*.md"
    matches = list(level_dir.glob(pattern))

    if not matches:
        raise ValueError(f"Module file not found: {level}/{pattern}")

    if len(matches) > 1:
        raise ValueError(f"Multiple module files found: {level}/{pattern}")

    # Extract slug from filename (e.g., "01-the-cyrillic-code-i.md" -> "the-cyrillic-code-i")
    filename = matches[0].stem  # Remove .md extension
    slug = filename.split('-', 1)[1]  # Remove number prefix

    return slug

def get_module_vocabulary(module_num: int, level: str) -> Dict:
    """
    Get all vocabulary for a module from the database.

    Args:
        module_num: Sequential module number (1-300)
        level: Level code (A1, A2, B1, B2)

    Returns:
        Dictionary with 'lemmas' and 'expressions' lists
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine if we should include review words
    # A1: only new words (is_new=1)
    # A2+: all words (new + review)
    include_review = (level != 'A1')

    # Build WHERE clause
    if include_review:
        where_clause = "mv.module_num = ?"
        params = (module_num,)
    else:
        where_clause = "mv.module_num = ? AND mv.is_new = 1"
        params = (module_num,)

    # Get lemmas
    cursor.execute(f"""
        SELECT l.uk, l.ipa, l.en, l.pos, l.gender, l.notes
        FROM module_vocabulary mv
        JOIN lemmas l ON mv.entry_id = l.id
        WHERE {where_clause} AND mv.entry_type = 'lemma'
        ORDER BY l.uk
    """, params)

    lemmas = []
    for row in cursor.fetchall():
        item = {
            'lemma': row['uk'],
            'ipa': row['ipa'] or '',
            'translation': row['en'] or '',
            'pos': row['pos'] or 'noun',
        }

        # Add optional fields only if present
        if row['gender']:
            item['gender'] = row['gender']
        if row['notes']:
            item['notes'] = row['notes']

        lemmas.append(item)

    # Get expressions
    cursor.execute(f"""
        SELECT e.uk, e.ipa, e.en, e.type, e.notes
        FROM module_vocabulary mv
        JOIN expressions e ON mv.entry_id = e.id
        WHERE {where_clause} AND mv.entry_type = 'expression'
        ORDER BY e.uk
    """, params)

    expressions = []
    for row in cursor.fetchall():
        item = {
            'lemma': row['uk'],
            'ipa': row['ipa'] or '',
            'translation': row['en'] or '',
            'pos': row['type'] or 'phrase',
        }

        if row['notes']:
            item['notes'] = row['notes']

        expressions.append(item)

    conn.close()

    # Combine lemmas and expressions
    all_items = lemmas + expressions

    return {
        'items': all_items,
        'count': len(all_items)
    }

def generate_yaml_file(level: str, module_in_level: int, sequential_num: int, dry_run: bool = False):
    """
    Generate vocabulary YAML file for a module.

    Args:
        level: Level code (A1, A2, B1, B2)
        module_in_level: Module number within the level (1-based)
        sequential_num: Sequential module number (1-300)
        dry_run: If True, only print what would be done without writing files
    """
    # Get module slug
    try:
        slug = get_module_slug(level, module_in_level)
    except ValueError as e:
        print(f"  ⚠️  {e}")
        return False

    # Get vocabulary from database
    vocab_data = get_module_vocabulary(sequential_num, level)

    if vocab_data['count'] == 0:
        print(f"  ⚠️  No vocabulary found for {level}/M{module_in_level:02d}")
        return False

    # Prepare YAML data
    yaml_data = {
        'module': f"{module_in_level:02d}-{slug}",
        'level': level,
        'version': '2.0',
        'items': vocab_data['items']
    }

    # Output path
    output_path = CURRICULUM_DIR / level.lower() / 'vocabulary' / f"{module_in_level:02d}-{slug}.yaml"

    if dry_run:
        print(f"  📄 Would generate: {output_path.relative_to(CURRICULUM_DIR)} ({vocab_data['count']} items)")
        return True

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write YAML file
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"  ✅ Generated: {output_path.relative_to(CURRICULUM_DIR)} ({vocab_data['count']} items)")
    return True

def regenerate_vocabs(levels: List[str], dry_run: bool = False):
    """Regenerate vocabulary YAML files for specified levels."""

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        print("Run: .venv/bin/python scripts/rebuild_vocab_from_yaml.py --force")
        return

    # Statistics
    stats = {
        'total_modules': 0,
        'generated': 0,
        'skipped': 0
    }

    for level in levels:
        level_upper = level.upper()

        if level_upper not in LEVEL_RANGES:
            print(f"⚠️  Unknown level: {level}")
            continue

        start_seq, end_seq = LEVEL_RANGES[level_upper]
        module_count = end_seq - start_seq + 1

        print(f"\n📚 {level_upper}: Processing {module_count} modules (sequential #{start_seq}-{end_seq})")

        for i, sequential_num in enumerate(range(start_seq, end_seq + 1), 1):
            module_in_level = i
            success = generate_yaml_file(level_upper, module_in_level, sequential_num, dry_run)

            stats['total_modules'] += 1
            if success:
                stats['generated'] += 1
            else:
                stats['skipped'] += 1

    # Final statistics
    print(f"\n{'='*60}")
    if dry_run:
        print(f"🔍 DRY RUN COMPLETE")
    else:
        print(f"✅ VOCABULARY YAMLS REGENERATED")
    print(f"{'='*60}")
    print(f"  📂 Total modules: {stats['total_modules']}")
    print(f"  ✅ Generated: {stats['generated']}")
    print(f"  ⚠️  Skipped: {stats['skipped']}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Regenerate vocabulary YAML files from vocabulary.db'
    )
    parser.add_argument(
        '--levels',
        type=str,
        default='a1,a2,b1,b2',
        help='Comma-separated list of levels to process (default: a1,a2,b1,b2)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually writing files'
    )

    args = parser.parse_args()

    levels = [l.strip().upper() for l in args.levels.split(',')]

    print("="*60)
    print("  Vocabulary YAML Regeneration")
    print("="*60)
    print(f"  Levels: {', '.join(levels)}")
    print(f"  Dry run: {args.dry_run}")
    print("="*60)

    regenerate_vocabs(levels, args.dry_run)

if __name__ == '__main__':
    main()
