#!/usr/bin/env python3
"""
Convert dialogue-reorder activities to cloze format.

Usage:
    python scripts/convert_dialogue_to_cloze.py [file1.yaml file2.yaml ...]
"""

import re
import sys
import random
from pathlib import Path
from typing import List, Tuple
import yaml


def extract_dialogue_texts(yaml_block: str) -> List[str]:
    """
    Extract dialogue text lines from a dialogue-reorder YAML block.

    Args:
        yaml_block: String containing the dialogue-reorder activity

    Returns:
        List of dialogue text strings in order
    """
    # Parse the entire block as YAML to get structured data
    try:
        # Parse the whole activity block
        parsed = yaml.safe_load(yaml_block)

        # Handle case where block is parsed as a list (starts with -)
        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0]

        if not parsed or not isinstance(parsed, dict) or 'lines' not in parsed:
            return []

        lines = parsed['lines']

        if not isinstance(lines, list):
            return []

        # Sort by order and extract text
        sorted_lines = sorted(lines, key=lambda x: x.get('order', 999))
        texts = [line.get('text', '').strip() for line in sorted_lines if line.get('text')]

        return texts
    except Exception as e:
        print(f"  Warning: Could not parse dialogue lines: {e}")
        return []


def generate_cloze_block(title: str, texts: List[str], has_id: bool = False, activity_id: str = "") -> str:
    """
    Generate a cloze activity block from dialogue texts.

    Args:
        title: Activity title
        texts: List of dialogue text strings
        has_id: Whether original had an id field
        activity_id: The id value if present

    Returns:
        Formatted cloze activity block
    """
    if not texts:
        return ""

    # Generate cloze lines
    cloze_lines = []
    for text in texts:
        # Get distractors
        distractors = [t for t in texts if t != text]
        random.shuffle(distractors)
        selected = distractors[:min(2, len(distractors))]

        # Build options
        options = [text] + selected
        options_str = '|'.join(opt.replace('|', '\\|') for opt in options)

        cloze_lines.append(f"    — {{{options_str}}}")

    # Build activity
    lines = ['- type: cloze']
    if has_id:
        lines.append(f'  id: {activity_id}')
    lines.append(f'  title: {title}')
    lines.append('  passage: |')
    lines.extend(cloze_lines)

    return '\n'.join(lines)


def convert_file(filepath: Path, dry_run: bool = False) -> Tuple[int, bool]:
    """
    Convert all dialogue-reorder activities in a file to cloze.

    Args:
        filepath: Path to YAML file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (conversion_count, success)
    """
    try:
        content = filepath.read_text(encoding='utf-8')

        if 'type: dialogue-reorder' not in content:
            return (0, True)

        conversions = 0
        modified = content

        # Find all dialogue-reorder blocks
        # Pattern: from "- type: dialogue-reorder" to next "- type:" or "# " comment
        pattern = r'(-\s*type:\s*dialogue-reorder\s*\n(?:.*\n)*?(?=^-\s*type:|^#\s|^$|\Z))'

        matches = list(re.finditer(pattern, content, re.MULTILINE))

        # Process in reverse to avoid offset issues
        for match in reversed(matches):
            block = match.group(1)

            # Extract title
            title_match = re.search(r'title:\s*(.+)', block)
            title = title_match.group(1).strip() if title_match else "Dialogue"

            # Extract id if present
            id_match = re.search(r'id:\s*(.+)', block)
            has_id = bool(id_match)
            activity_id = id_match.group(1).strip() if id_match else ""

            # Extract dialogue texts
            texts = extract_dialogue_texts(block)

            if not texts:
                print(f"  Warning: No dialogue texts found in '{title}'")
                continue

            # Generate cloze block
            cloze_block = generate_cloze_block(title, texts, has_id, activity_id)

            if cloze_block:
                # Replace the block
                modified = modified[:match.start()] + cloze_block + '\n' + modified[match.end():]
                conversions += 1

        if conversions == 0:
            return (0, True)

        # Display path
        try:
            display_path = filepath.relative_to(Path.cwd())
        except ValueError:
            display_path = filepath

        print(f"{'[DRY RUN] ' if dry_run else ''}✓ {display_path}: {conversions} dialogue-reorder → cloze")

        if not dry_run:
            filepath.write_text(modified, encoding='utf-8')

        return (conversions, True)

    except Exception as e:
        print(f"✗ Error processing {filepath.name}: {e}")
        import traceback
        traceback.print_exc()
        return (0, False)


def find_files() -> List[Path]:
    """Find all YAML files with dialogue-reorder activities."""
    curriculum_dir = Path("curriculum/l2-uk-en")

    if not curriculum_dir.exists():
        print(f"Error: {curriculum_dir} not found")
        return []

    files = []
    for yaml_file in curriculum_dir.rglob("*.yaml"):
        try:
            content = yaml_file.read_text(encoding='utf-8')
            if 'type: dialogue-reorder' in content:
                files.append(yaml_file)
        except Exception:
            pass

    return files


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert dialogue-reorder to cloze")
    parser.add_argument('files', nargs='*', help='Files to process')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--sample', type=int, help='Process only first N files')

    args = parser.parse_args()

    if args.files:
        files = [Path(f).resolve() for f in args.files]
    else:
        print("Searching for files with dialogue-reorder activities...")
        files = find_files()

        if not files:
            print("No files found.")
            return 0

        print(f"\nFound {len(files)} file(s)\n")

    if args.sample:
        files = files[:args.sample]
        print(f"Processing first {len(files)} file(s) (sample mode)\n")

    total_converted = 0
    files_modified = 0

    for filepath in files:
        count, success = convert_file(filepath, dry_run=args.dry_run)
        if count > 0:
            files_modified += 1
            total_converted += count

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Files processed: {len(files)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Activities converted: {total_converted}")

    if args.dry_run and files_modified > 0:
        print("\nRun without --dry-run to apply changes.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
