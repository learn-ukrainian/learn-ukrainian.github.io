#!/usr/bin/env python3
"""
Fix inappropriate English hints in A2+ activities.

Removes hints like (arrived), (entrance), (reader) but preserves grammar annotations like (nom.), (acc.).

Usage:
    python scripts/fix_english_hints.py [--dry-run] [file_or_dir]
"""

import re
import sys
from pathlib import Path
import argparse

def should_remove_hint(hint_text):
    """Check if hint should be removed (True) or kept (False)."""
    # Keep grammar annotations (with or without period):
    # (nom.), (acc.), (gen.), (pl.) - with period
    # (adj), (imp), (perf), (gen) - without period
    # (gen pl), (dat), (voc) - case abbreviations
    grammar_terms = [
        'nom', 'acc', 'gen', 'dat', 'ins', 'loc', 'voc',  # Cases
        'sg', 'pl', 'du',  # Number
        'masc', 'fem', 'neut', 'm', 'f', 'n',  # Gender
        'adj', 'adv', 'noun', 'verb', 'pron',  # Parts of speech
        'imp', 'perf', 'impf',  # Aspect
        'past', 'pres', 'fut',  # Tense
        'gen pl', 'dat pl', 'acc pl', 'ins pl', 'loc pl',  # Plural cases
    ]

    # Strip parentheses for checking
    content = hint_text.strip('()')

    # Keep if it's a known grammar term (with or without period)
    content_clean = content.rstrip('.')
    if content_clean.lower() in grammar_terms:
        return False

    # Keep short abbreviations (likely grammar)
    if len(content_clean) <= 4 and not ' ' in content_clean:
        return False

    # Remove multi-word English phrases
    if ' ' in content and len(content.split()) >= 2:
        return True

    # Remove longer single words (likely English translations)
    if len(content) > 8:
        return True

    return False

def fix_markdown_file(file_path, dry_run=False):
    """Remove English hints from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # Find all hints
    hints_found = re.findall(r'\([a-z][a-z\s]+\)', original)
    hints_to_remove = [h for h in hints_found if should_remove_hint(h)]
    
    if not hints_to_remove:
        return 0
    
    # Remove hints
    cleaned = original
    for hint in set(hints_to_remove):  # Use set to avoid duplicate removals
        # Remove hint and any leading space
        cleaned = re.sub(rf'\s*{re.escape(hint)}', '', cleaned)
    
    if dry_run:
        print(f"[DRY RUN] Would remove {len(hints_to_remove)} hints from {file_path}")
        print(f"  Hints: {', '.join(sorted(set(hints_to_remove)))}")
        return len(hints_to_remove)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    print(f"✓ Removed {len(hints_to_remove)} hints from {file_path}")
    return len(hints_to_remove)

def fix_yaml_file(file_path, dry_run=False):
    """Remove English hints from YAML activity file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    # Find all hints
    hints_found = re.findall(r'\([a-z][a-z\s]+\)', original)
    hints_to_remove = [h for h in hints_found if should_remove_hint(h)]
    
    if not hints_to_remove:
        return 0
    
    # Remove hints
    cleaned = original
    for hint in set(hints_to_remove):
        cleaned = re.sub(rf'\s*{re.escape(hint)}', '', cleaned)
    
    if dry_run:
        print(f"[DRY RUN] Would remove {len(hints_to_remove)} hints from {file_path}")
        print(f"  Hints: {', '.join(sorted(set(hints_to_remove)))}")
        return len(hints_to_remove)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    print(f"✓ Removed {len(hints_to_remove)} hints from {file_path}")
    return len(hints_to_remove)

def main():
    parser = argparse.ArgumentParser(description='Remove English hints from A2+ activities')
    parser.add_argument('path', nargs='?', default='curriculum/l2-uk-en/a2', help='File or directory to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    args = parser.parse_args()
    
    path = Path(args.path)
    total_fixed = 0
    
    if path.is_file():
        if path.suffix == '.md':
            total_fixed = fix_markdown_file(path, args.dry_run)
        elif path.suffix == '.yaml':
            total_fixed = fix_yaml_file(path, args.dry_run)
    elif path.is_dir():
        # Process all markdown and YAML files
        for md_file in sorted(path.glob('**/*.md')):
            total_fixed += fix_markdown_file(md_file, args.dry_run)
        for yaml_file in sorted(path.glob('**/*.yaml')):
            total_fixed += fix_yaml_file(yaml_file, args.dry_run)
    
    print(f"\n{'[DRY RUN] Would remove' if args.dry_run else 'Removed'} {total_fixed} total hints")

if __name__ == '__main__':
    main()
