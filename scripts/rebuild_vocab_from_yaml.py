#!/usr/bin/env python3
"""
Rebuild vocabulary.db from YAML vocabulary files.

Scans A1, A2, B1, B2 vocabulary/ directories and populates:
- lemmas (single words)
- expressions (phrases/idioms)
- module_vocabulary (linkage)

Usage:
    .venv/bin/python scripts/rebuild_vocab_from_yaml.py [--levels a1,a2,b1,b2] [--force]

Examples:
    .venv/bin/python scripts/rebuild_vocab_from_yaml.py --force
    .venv/bin/python scripts/rebuild_vocab_from_yaml.py --levels a1,a2,b1,b2
"""

import argparse
import sqlite3
import yaml
import re
from pathlib import Path
from typing import Set, Dict, List

# Configuration
CURRICULUM_DIR = Path("curriculum/l2-uk-en")
DB_PATH = CURRICULUM_DIR / "vocabulary.db"

def get_db_connection():
    """Get database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def extract_module_number(filename: str) -> int:
    """Extract module number from filename like '01-title.yaml' -> 1"""
    match = re.match(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 999  # Fallback for files without numbers

def slugify(text: str) -> str:
    """Create URL-safe slug from Ukrainian text."""
    # Simple transliteration
    translit = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ye', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya', ' ': '-', "'": ''
    }
    result = []
    for char in text.lower():
        result.append(translit.get(char, char))
    slug = ''.join(result)
    # Remove non-alphanumeric except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def determine_entry_type(item: Dict) -> str:
    """Determine if item is a lemma or expression."""
    pos = item.get('pos', '')
    lemma = item.get('lemma', '')

    # Check POS first
    if pos in ['phrase', 'idiom', 'collocation', 'proverb']:
        return 'expression'

    # Check for multi-word
    if ' ' in lemma.strip():
        return 'expression'

    return 'lemma'

def process_yaml_file(yaml_path: Path, level: str, known_words: Set[str]) -> Dict:
    """
    Process a single YAML vocabulary file.

    Returns:
        Dictionary with 'lemmas', 'expressions', and 'module_num'
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'items' not in data:
        return {'lemmas': [], 'expressions': [], 'module_num': 0}

    module_num = extract_module_number(yaml_path.stem)

    lemmas = []
    expressions = []

    for item in data['items']:
        lemma_text = item.get('lemma', '').strip()
        if not lemma_text:
            continue

        entry_type = determine_entry_type(item)
        is_new = lemma_text not in known_words

        # Track as known
        known_words.add(lemma_text)

        entry = {
            'uk': lemma_text,
            'ipa': item.get('ipa', ''),
            'en': item.get('translation', ''),
            'pos': item.get('pos', 'noun'),
            'gender': item.get('gender', ''),
            'notes': item.get('notes', ''),
            'level': level,
            'module_num': module_num,
            'is_new': is_new
        }

        if entry_type == 'lemma':
            lemmas.append(entry)
        else:
            expressions.append(entry)

    return {
        'lemmas': lemmas,
        'expressions': expressions,
        'module_num': module_num
    }

def populate_database(levels: List[str], force: bool = False):
    """Populate database from YAML files."""

    # Check if database exists
    if DB_PATH.exists() and not force:
        print(f"❌ Database already exists: {DB_PATH}")
        print("Use --force to rebuild from scratch")
        return

    # Remove existing database if force
    if DB_PATH.exists() and force:
        print(f"🗑️  Removing existing database...")
        DB_PATH.unlink()

    # Initialize fresh database
    print(f"🆕 Initializing database: {DB_PATH}")
    import subprocess
    result = subprocess.run([
        '.venv/bin/python', 'scripts/vocab_init.py', 'l2-uk-en', '--force'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to initialize database")
        print(result.stderr)
        return

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Track known words across all levels
    known_words = set()

    # Statistics
    stats = {
        'lemmas_added': 0,
        'expressions_added': 0,
        'modules_processed': 0
    }

    # Sequential module counter across all levels
    # A1: 1-44, A2: 45-115, B1: 116-207, B2: 208-300
    sequential_module_num = 0

    # Process each level in order
    for level in levels:
        level_lower = level.lower()
        vocab_dir = CURRICULUM_DIR / level_lower / 'vocabulary'

        if not vocab_dir.exists():
            print(f"⚠️  Vocabulary directory not found: {vocab_dir}")
            continue

        # Get all YAML files in order
        yaml_files = sorted(list(vocab_dir.glob('*.yaml')))
        yaml_files.sort(key=lambda x: extract_module_number(x.stem))

        print(f"\n📚 Processing {level.upper()}: {len(yaml_files)} modules")

        for yaml_file in yaml_files:
            # Increment sequential module number
            sequential_module_num += 1

            result = process_yaml_file(yaml_file, level.upper(), known_words)

            # Use sequential module number instead of per-level number
            module_num = sequential_module_num
            lemmas = result['lemmas']
            expressions = result['expressions']

            # Insert lemmas
            for lemma in lemmas:
                # Check if already exists (by Ukrainian text)
                cursor.execute("SELECT id, first_module FROM lemmas WHERE uk = ?", (lemma['uk'],))
                existing = cursor.fetchone()

                if not existing:
                    # Create unique ID for new word
                    slug = slugify(lemma['uk'])
                    # Use a counter to ensure uniqueness if needed
                    uid = f"v-{slug}-{lemma['level']}-{module_num}"

                    # Double-check ID doesn't exist (shouldn't happen, but safety)
                    cursor.execute("SELECT id FROM lemmas WHERE id = ?", (uid,))
                    if cursor.fetchone():
                        # Append random suffix if collision
                        import uuid
                        uid = f"v-{slug}-{uuid.uuid4().hex[:8]}"

                    # Insert new lemma
                    cursor.execute("""
                        INSERT INTO lemmas (id, uk, ipa, en, pos, gender, notes, level, first_module)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (uid, lemma['uk'], lemma['ipa'], lemma['en'], lemma['pos'],
                          lemma['gender'], lemma['notes'], lemma['level'], module_num))
                    real_id = uid
                    is_new = 1
                    stats['lemmas_added'] += 1
                else:
                    real_id = existing['id']
                    # Word is new to THIS module if this is not its first appearance
                    is_new = 0

                # Link to module
                cursor.execute("""
                    INSERT OR IGNORE INTO module_vocabulary (module_num, entry_type, entry_id, is_new)
                    VALUES (?, 'lemma', ?, ?)
                """, (module_num, real_id, is_new))

            # Insert expressions
            for expr in expressions:
                # Check if already exists (by Ukrainian text)
                cursor.execute("SELECT id, first_module FROM expressions WHERE uk = ?", (expr['uk'],))
                existing = cursor.fetchone()

                if not existing:
                    # Create unique ID for new expression
                    slug = slugify(expr['uk'])
                    uid = f"e-{slug}-{expr['level']}-{module_num}"

                    # Double-check ID doesn't exist
                    cursor.execute("SELECT id FROM expressions WHERE id = ?", (uid,))
                    if cursor.fetchone():
                        import uuid
                        uid = f"e-{slug}-{uuid.uuid4().hex[:8]}"

                    cursor.execute("""
                        INSERT INTO expressions (id, uk, ipa, en, type, notes, level, first_module)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (uid, expr['uk'], expr['ipa'], expr['en'], expr['pos'],
                          expr['notes'], expr['level'], module_num))
                    real_id = uid
                    is_new = 1
                    stats['expressions_added'] += 1
                else:
                    real_id = existing['id']
                    is_new = 0

                cursor.execute("""
                    INSERT OR IGNORE INTO module_vocabulary (module_num, entry_type, entry_id, is_new)
                    VALUES (?, 'expression', ?, ?)
                """, (module_num, real_id, is_new))

            stats['modules_processed'] += 1

            # Progress indicator
            if stats['modules_processed'] % 10 == 0:
                print(f"  ✓ Processed {stats['modules_processed']} modules...")

    conn.commit()
    conn.close()

    # Final statistics
    print(f"\n{'='*60}")
    print(f"✅ Vocabulary database rebuilt successfully!")
    print(f"{'='*60}")
    print(f"  📝 Lemmas added: {stats['lemmas_added']}")
    print(f"  📚 Expressions added: {stats['expressions_added']}")
    print(f"  📂 Modules processed: {stats['modules_processed']}")
    print(f"  💾 Database: {DB_PATH}")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Rebuild vocabulary.db from YAML vocabulary files'
    )
    parser.add_argument(
        '--levels',
        type=str,
        default='a1,a2,b1,b2',
        help='Comma-separated list of levels to process (default: a1,a2,b1,b2)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild (delete existing database)'
    )

    args = parser.parse_args()

    levels = [l.strip().upper() for l in args.levels.split(',')]

    print("="*60)
    print("  Vocabulary Database Rebuild")
    print("="*60)
    print(f"  Levels: {', '.join(levels)}")
    print(f"  Force: {args.force}")
    print("="*60)

    populate_database(levels, args.force)

if __name__ == '__main__':
    main()
