#!/usr/bin/env python3
"""Add missing 'focus' field to meta files based on curriculum structure."""

import os
import re
import sys
from pathlib import Path

# Define focus values based on level and module number ranges
FOCUS_RULES = {
    'a1': [
        (range(10, 11), 'checkpoint'),
        (range(20, 21), 'checkpoint'),
        (range(34, 35), 'checkpoint'),
        (range(1, 100), 'grammar'),  # Default for A1
    ],
    'a2': [
        # A2 already has all focus fields
    ],
    'b1': [
        # Checkpoints
        (range(15, 16), 'checkpoint'),
        (range(25, 26), 'checkpoint'),
        (range(34, 35), 'checkpoint'),
        (range(41, 42), 'checkpoint'),
        (range(51, 52), 'checkpoint'),
        # Phase-based
        (range(1, 6), 'grammar'),      # M01-05: Metalanguage bridge
        (range(6, 16), 'grammar'),     # M06-15: Aspect mastery
        (range(16, 26), 'grammar'),    # M16-25: Motion verbs
        (range(26, 42), 'grammar'),    # M26-41: Complex sentences
        (range(42, 52), 'grammar'),    # M42-51: Advanced grammar
        (range(52, 72), 'vocabulary'), # M52-71: Vocabulary expansion
        (range(72, 87), 'cultural'),   # M72-86: Contemporary Ukraine
        (range(87, 92), 'skills'),     # M87-91: Skills & Integration
    ],
    'b2': [
        # Checkpoints
        (range(10, 11), 'checkpoint'),
        (range(25, 26), 'checkpoint'),
        (range(40, 41), 'checkpoint'),
        (range(70, 71), 'checkpoint'),
        (range(95, 96), 'checkpoint'),
        (range(110, 111), 'checkpoint'),
        # Phase-based
        (range(1, 11), 'grammar'),       # M01-10: Passive voice
        (range(11, 26), 'grammar'),      # M11-25: Participles
        (range(26, 41), 'grammar'),      # M26-40: Advanced syntax
        (range(41, 71), 'phraseology'),  # M41-70: Phraseology
        (range(71, 132), 'history'),     # M71-131: Ukrainian history
        (range(132, 146), 'skills'),     # M132-145: Skills & Capstone
    ],
    'c1': [
        # C1 is mostly biography-focused, check existing values
        (range(1, 10), 'biography'),
        (range(10, 20), 'biography'),
        (range(20, 30), 'biography'),
        (range(30, 40), 'biography'),
        # Default to biography for C1 if not otherwise specified
        (range(1, 300), 'biography'),
    ],
}


def get_module_number(filename: str) -> int:
    """Extract module number from filename like '01-title.yaml'."""
    match = re.match(r'^(\d+)-', filename)
    if match:
        return int(match.group(1))
    return 0


def get_focus_value(level: str, module_num: int) -> str:
    """Determine the focus value based on level and module number."""
    rules = FOCUS_RULES.get(level, [])
    for num_range, focus in rules:
        if module_num in num_range:
            return focus
    return 'grammar'  # Default fallback


def add_focus_to_file(filepath: Path, focus_value: str, dry_run: bool = False) -> bool:
    """Add focus field to a meta file if missing."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if focus already exists
    if re.search(r'^focus:', content, re.MULTILINE):
        return False

    # Find the right place to insert (after pedagogy field)
    lines = content.split('\n')
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        # Insert after pedagogy line
        if line.startswith('pedagogy:') and not inserted:
            new_lines.append(f'focus: {focus_value}')
            inserted = True

    # If pedagogy not found, insert after phase
    if not inserted:
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.startswith('phase:') and not inserted:
                new_lines.append(f'focus: {focus_value}')
                inserted = True

    if not inserted:
        print(f"  WARNING: Could not find insertion point in {filepath.name}")
        return False

    new_content = '\n'.join(new_lines)

    if dry_run:
        print(f"  Would add 'focus: {focus_value}' to {filepath.name}")
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Added 'focus: {focus_value}' to {filepath.name}")

    return True


def process_level(base_path: Path, level: str, dry_run: bool = False) -> tuple[int, int]:
    """Process all meta files in a level directory."""
    meta_dir = base_path / level / 'meta'
    if not meta_dir.exists():
        print(f"  No meta directory for {level}")
        return 0, 0

    total = 0
    updated = 0

    for filepath in sorted(meta_dir.glob('*.yaml')):
        total += 1
        module_num = get_module_number(filepath.name)
        focus_value = get_focus_value(level, module_num)

        if add_focus_to_file(filepath, focus_value, dry_run):
            updated += 1

    return total, updated


def main():
    dry_run = '--dry-run' in sys.argv
    levels = sys.argv[1:] if len(sys.argv) > 1 else ['a1', 'a2', 'b1', 'b2', 'c1']
    levels = [l for l in levels if l in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']]

    if dry_run:
        print("DRY RUN - no files will be modified\n")
        levels = [l for l in sys.argv[1:] if l in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']]
        if not levels:
            levels = ['a1', 'a2', 'b1', 'b2', 'c1']

    base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'

    total_files = 0
    total_updated = 0

    for level in levels:
        print(f"\n=== Processing {level.upper()} ===")
        files, updated = process_level(base_path, level, dry_run)
        total_files += files
        total_updated += updated
        print(f"  {level}: {updated}/{files} files updated")

    print(f"\n=== Summary ===")
    print(f"Total files processed: {total_files}")
    print(f"Total files updated: {total_updated}")


if __name__ == '__main__':
    main()
