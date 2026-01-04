#!/usr/bin/env python3
"""
Convert dialogue-reorder activities to cloze format using line-by-line processing.

This preserves file structure, comments, and formatting while converting activities.

Usage:
    python scripts/convert_dialogue_to_cloze.py [file1.yaml file2.yaml ...]

If no files specified, processes all YAML files containing dialogue-reorder activities.
"""

import re
import sys
import random
from pathlib import Path
from typing import List, Tuple


def convert_dialogue_to_cloze_simple(content: str) -> Tuple[str, int]:
    """
    Convert dialogue-reorder activities to cloze format using simple line processing.

    Args:
        content: File content

    Returns:
        Tuple of (modified content, count of conversions)
    """
    lines = content.split('\n')
    output = []
    conversions = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is the start of a dialogue-reorder activity
        if re.match(r'^-\s*type:\s+dialogue-reorder\s*$', line):
            # Found a dialogue-reorder activity - collect all lines until next activity
            activity_lines = [line]
            i += 1

            # Collect metadata (id, title, etc.) until we hit 'lines:'
            while i < len(lines) and not re.match(r'^\s+lines:\s*$', lines[i]):
                activity_lines.append(lines[i])
                i += 1

            if i < len(lines):
                activity_lines.append(lines[i])  # Add 'lines:' line
                i += 1

            # Collect all dialogue lines
            dialogue_texts = []
            while i < len(lines):
                current = lines[i]

                # Check if we've hit the next activity or comment
                if re.match(r'^-\s*type:', current) or re.match(r'^#', current):
                    break

                # Check for start of a dialogue line item (either order or text first)
                if re.match(r'^\s+-\s+(order|text):', current):
                    # Start of a dialogue line - collect order and text
                    text = None
                    order = None

                    # Process this line and next few to collect both order and text
                    temp_i = i
                    while temp_i < len(lines) and re.match(r'^\s+(order|text|speaker):', lines[temp_i]):
                        line_content = lines[temp_i]

                        order_match = re.match(r'^\s+order:\s+\d+\s*$', line_content)
                        text_match = re.match(r'^\s+text:\s+(.+)$', line_content)

                        if order_match:
                            order = True  # We have an order
                        elif text_match:
                            text = text_match.group(1).strip()

                        temp_i += 1

                    if text:
                        dialogue_texts.append(text)

                    i = temp_i
                else:
                    i += 1

            # Extract title from activity_lines
            title = "Dialogue"
            for act_line in activity_lines:
                title_match = re.match(r'^\s+title:\s+(.+)$', act_line)
                if title_match:
                    title = title_match.group(1).strip()
                    break

            # Generate cloze activity
            if dialogue_texts:
                cloze_lines = generate_cloze_activity(title, dialogue_texts)
                output.extend(cloze_lines)
                conversions += 1
            else:
                # No dialogue texts found, keep original
                output.extend(activity_lines)

        else:
            output.append(line)
            i += 1

    return '\n'.join(output), conversions


def generate_cloze_activity(title: str, dialogue_texts: List[str]) -> List[str]:
    """
    Generate cloze activity lines from dialogue texts.

    Args:
        title: Activity title
        dialogue_texts: List of dialogue text strings

    Returns:
        List of lines for the cloze activity
    """
    # Build cloze passage with all texts as blanks
    passage_lines = []

    for text in dialogue_texts:
        # Generate distractors - pick 2 random other lines
        distractors = [t for t in dialogue_texts if t != text]
        random.shuffle(distractors)
        selected_distractors = distractors[:min(2, len(distractors))]

        # Build options: correct answer first, then distractors
        options = [text] + selected_distractors

        # Escape pipes
        options_escaped = [opt.replace('|', '\\|') for opt in options]

        # Create cloze line
        options_str = '|'.join(options_escaped)
        passage_lines.append(f"    — {{{options_str}}}")

    # Build activity
    activity = [
        '- type: cloze',
        f'  title: {title}',
        '  passage: |'
    ]
    activity.extend(passage_lines)

    return activity


def process_file(filepath: Path, dry_run: bool = False) -> Tuple[int, bool]:
    """
    Process a single YAML file to convert dialogue-reorder activities.

    Args:
        filepath: Path to YAML file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (conversion_count, success)
    """
    try:
        # Read file content
        content = filepath.read_text(encoding='utf-8')

        # Check if file contains dialogue-reorder
        if 'type: dialogue-reorder' not in content:
            return (0, True)

        # Convert dialogue activities
        modified, count = convert_dialogue_to_cloze_simple(content)

        if count == 0:
            print(f"  {filepath.name}: No dialogue-reorder activities found")
            return (0, True)

        # Try to get relative path for display
        try:
            display_path = filepath.relative_to(Path.cwd())
        except ValueError:
            display_path = filepath

        print(f"{'[DRY RUN] ' if dry_run else ''}✓ {display_path}: {count} dialogue-reorder → cloze")

        if not dry_run:
            filepath.write_text(modified, encoding='utf-8')

        return (count, True)

    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return (0, False)


def find_files_with_dialogue_reorder() -> List[Path]:
    """Find all YAML files containing dialogue-reorder activities."""
    curriculum_dir = Path("curriculum/l2-uk-en")

    if not curriculum_dir.exists():
        print(f"Error: {curriculum_dir} not found")
        return []

    files_with_dialogue = []

    for yaml_file in curriculum_dir.rglob("*.yaml"):
        try:
            content = yaml_file.read_text(encoding='utf-8')
            if 'type: dialogue-reorder' in content:
                files_with_dialogue.append(yaml_file)
        except Exception as e:
            print(f"Warning: Could not read {yaml_file}: {e}")

    return files_with_dialogue


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert dialogue-reorder activities to cloze format"
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='YAML files to process (if none specified, auto-detects files with dialogue-reorder)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--sample',
        type=int,
        metavar='N',
        help='Process only first N files (for testing)'
    )

    args = parser.parse_args()

    if args.files:
        files = [Path(f).resolve() for f in args.files]
    else:
        print("Searching for files with dialogue-reorder activities...")
        files = find_files_with_dialogue_reorder()

        if not files:
            print("No files with dialogue-reorder activities found.")
            return 0

        print(f"\nFound {len(files)} file(s) with dialogue-reorder activities\n")

    # Limit to sample size if requested
    if args.sample:
        files = files[:args.sample]
        print(f"Processing first {len(files)} file(s) (sample mode)\n")

    total_converted = 0
    files_modified = 0

    for filepath in files:
        count, success = process_file(filepath, dry_run=args.dry_run)
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
