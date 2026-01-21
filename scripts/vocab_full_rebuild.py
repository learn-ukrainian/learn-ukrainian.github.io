#!/usr/bin/env python3
"""
FULL VOCABULARY REBUILD PIPELINE

This is a DESTRUCTIVE operation that:
1. Deletes ALL existing vocabulary YAML files
2. Deletes the vocabulary.db
3. Re-extracts vocabulary from ALL markdown source files with pymorphy3
4. Rebuilds the vocabulary.db from the fresh YAMLs

Usage:
    .venv/bin/python scripts/vocab_full_rebuild.py --confirm
    .venv/bin/python scripts/vocab_full_rebuild.py --level b2-hist --confirm
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CURRICULUM_DIR = Path("curriculum/l2-uk-en")
DB_PATH = CURRICULUM_DIR / "vocabulary.db"

# All levels with vocabulary
LEVELS = [
    'a1', 'a2', 'b1', 'b2',
    'b2-hist', 'b2-pro',
    'c1', 'c1-bio', 'c1-pro',
    'lit'
]


def delete_vocab_yamls(levels: list[str]) -> int:
    """Delete all vocabulary YAML files for given levels."""
    count = 0
    for level in levels:
        vocab_dir = CURRICULUM_DIR / level / 'vocabulary'
        if vocab_dir.exists():
            for yaml_file in vocab_dir.glob('*.yaml'):
                yaml_file.unlink()
                count += 1
    return count


def delete_database() -> bool:
    """Delete the vocabulary database."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        return True
    return False


def extract_vocabulary_for_level(level: str) -> dict:
    """Run vocab_extract_proper.py for all markdown files in a level."""
    level_dir = CURRICULUM_DIR / level
    md_files = list(level_dir.glob('*.md'))
    
    if not md_files:
        return {'level': level, 'files': 0, 'lemmas': 0, 'success': True}
    
    # Run extraction
    cmd = [sys.executable, 'scripts/vocab_extract_proper.py'] + [str(f) for f in md_files]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    
    # Parse output for stats
    lemmas = 0
    for line in result.stdout.split('\n'):
        if 'Entries created:' in line:
            try:
                lemmas = int(line.split(':')[1].strip().replace(',', ''))
            except:
                pass
    
    return {
        'level': level,
        'files': len(md_files),
        'lemmas': lemmas,
        'success': result.returncode == 0,
        'error': result.stderr if result.returncode != 0 else None
    }


def rebuild_database() -> bool:
    """Rebuild vocabulary.db from YAML files."""
    result = subprocess.run(
        [sys.executable, 'scripts/rebuild_vocab_from_yaml.py', '--force'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Full vocabulary rebuild pipeline')
    parser.add_argument('--level', type=str, help='Rebuild single level only')
    parser.add_argument('--confirm', action='store_true', 
                        help='Confirm destructive operation')
    parser.add_argument('--skip-db-rebuild', action='store_true',
                        help='Skip database rebuild (extraction only)')
    
    args = parser.parse_args()
    
    levels = args.level.split(',') if args.level else LEVELS
    
    if not args.confirm:
        print("⚠️  WARNING: This is a DESTRUCTIVE operation!")
        print("   It will DELETE all vocabulary YAML files and the vocabulary.db")
        print("   and rebuild everything from markdown source files.")
        print()
        print("   Run with --confirm to proceed.")
        print(f"   Affected levels: {', '.join(levels)}")
        return 1
    
    print("=" * 70)
    print("🔄 FULL VOCABULARY REBUILD PIPELINE")
    print("=" * 70)
    
    # Step 1: Delete old YAMLs
    print("\n1️⃣  DELETING OLD VOCABULARY YAMLS...")
    deleted_yamls = delete_vocab_yamls(levels)
    print(f"   Deleted {deleted_yamls} YAML files")
    
    # Step 2: Delete old DB (only if doing full rebuild)
    if not args.level:
        print("\n2️⃣  DELETING VOCABULARY DATABASE...")
        if delete_database():
            print(f"   Deleted {DB_PATH}")
        else:
            print("   Database not found (already deleted)")
    
    # Step 3: Extract fresh vocabulary
    print("\n3️⃣  EXTRACTING FRESH VOCABULARY FROM MARKDOWN...")
    total_files = 0
    total_lemmas = 0
    
    for level in levels:
        print(f"\n   📂 {level.upper()}...")
        stats = extract_vocabulary_for_level(level)
        total_files += stats['files']
        total_lemmas += stats['lemmas']
        
        if stats['success']:
            print(f"      ✓ {stats['files']} files → {stats['lemmas']} lemmas")
        else:
            print(f"      ✗ Error: {stats.get('error', 'Unknown')[:100]}")
    
    # Step 4: Rebuild database
    if not args.skip_db_rebuild and not args.level:
        print("\n4️⃣  REBUILDING VOCABULARY DATABASE...")
        if rebuild_database():
            print("   ✅ Database rebuilt successfully!")
        else:
            print("   ❌ Database rebuild failed!")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 REBUILD COMPLETE")
    print("=" * 70)
    print(f"   Levels processed: {len(levels)}")
    print(f"   Files processed:  {total_files}")
    print(f"   Lemmas extracted: {total_lemmas:,}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
