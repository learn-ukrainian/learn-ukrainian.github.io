#!/usr/bin/env python3
"""
Batch Vocabulary Enrichment Pipeline.

Enriches ALL vocabulary YAML files across all levels using pymorphy3.
Then rebuilds the vocabulary.db from the enriched files.

Usage:
    .venv/bin/python scripts/batch_vocab_rebuild.py
    .venv/bin/python scripts/batch_vocab_rebuild.py --level b2-hist  # Single level
    .venv/bin/python scripts/batch_vocab_rebuild.py --dry-run       # Preview only
"""

import argparse
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

CURRICULUM_DIR = Path("curriculum/l2-uk-en")

# All vocabulary directories in order
LEVELS = [
    'a1', 'a2', 'b1', 'b2',       # Core levels
    'b2-hist', 'b2-pro',          # B2 tracks
    'c1', 'c1-bio', 'c1-pro',     # C1 tracks
    'lit'                          # LIT track
]


def get_vocab_files(level: str) -> list[Path]:
    """Get all vocabulary YAML files for a level."""
    vocab_dir = CURRICULUM_DIR / level / 'vocabulary'
    if not vocab_dir.exists():
        return []
    return sorted(vocab_dir.glob('*.yaml'))


def enrich_single_file(yaml_path: Path, dry_run: bool = False) -> dict:
    """
    Run vocab_enrich_nlp.py on a single file.
    
    Returns dict with 'path', 'success', 'original', 'final', 'error'
    """
    cmd = [
        sys.executable,
        'scripts/vocab_enrich_nlp.py',
        str(yaml_path)
    ]
    if dry_run:
        cmd.append('--dry-run')
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Parse output for stats
        output = result.stdout + result.stderr
        original = 0
        final = 0
        
        for line in output.split('\n'):
            if 'Original entries:' in line:
                original = int(line.split(':')[1].strip())
            elif 'After deduplication:' in line:
                final = int(line.split(':')[1].strip())
        
        return {
            'path': str(yaml_path),
            'success': result.returncode == 0,
            'original': original,
            'final': final,
            'error': result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {
            'path': str(yaml_path),
            'success': False,
            'original': 0,
            'final': 0,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Batch vocabulary enrichment')
    parser.add_argument('--level', type=str, help='Process single level only')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--skip-rebuild', action='store_true', 
                        help='Skip database rebuild after enrichment')
    args = parser.parse_args()
    
    levels_to_process = [args.level] if args.level else LEVELS
    
    print("=" * 70)
    print("🔧 BATCH VOCABULARY ENRICHMENT PIPELINE")
    print("=" * 70)
    
    total_files = 0
    total_original = 0
    total_final = 0
    errors = []
    
    for level in levels_to_process:
        files = get_vocab_files(level)
        if not files:
            print(f"\n⚠️  Level '{level}': No vocabulary files found")
            continue
        
        print(f"\n📂 Processing {level.upper()} ({len(files)} files)...")
        
        for yaml_path in files:
            result = enrich_single_file(yaml_path, args.dry_run)
            total_files += 1
            total_original += result['original']
            total_final += result['final']
            
            if result['success']:
                reduction = result['original'] - result['final']
                if reduction > 0:
                    print(f"  ✓ {yaml_path.name}: {result['original']} → {result['final']} (-{reduction})")
                else:
                    print(f"  ✓ {yaml_path.name}: {result['final']} entries")
            else:
                print(f"  ✗ {yaml_path.name}: ERROR")
                errors.append((yaml_path.name, result['error']))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"  Files processed:    {total_files}")
    print(f"  Original entries:   {total_original:,}")
    print(f"  After dedup:        {total_final:,}")
    
    if total_original > 0:
        reduction = total_original - total_final
        pct = (reduction / total_original) * 100
        print(f"  Reduction:          {reduction:,} ({pct:.1f}%)")
    
    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        for name, err in errors[:5]:
            print(f"    - {name}: {err[:100]}")
    
    # Rebuild database
    if not args.dry_run and not args.skip_rebuild:
        print("\n" + "=" * 70)
        print("🗄️  REBUILDING VOCABULARY DATABASE")
        print("=" * 70)
        
        result = subprocess.run(
            [sys.executable, 'scripts/rebuild_vocab_from_yaml.py', '--force'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Database rebuilt successfully!")
            print(result.stdout)
        else:
            print("  ❌ Database rebuild failed!")
            print(result.stderr)
    
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
