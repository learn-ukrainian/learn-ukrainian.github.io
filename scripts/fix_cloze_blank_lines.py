#!/usr/bin/env python3
"""
Fix blank lines in cloze activity passages across all curriculum YAML files.

Replaces double newlines (\n\n) with single newlines (\n) in cloze passages
to prevent MDX/HTML rendering issues.
"""

import yaml
import sys
from pathlib import Path
from typing import List, Tuple

def fix_blank_lines_in_cloze(yaml_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Fix cloze activities with blank lines in their passages.

    Returns: (num_fixed, list_of_titles)
    """
    fixed_count = 0
    fixed_titles = []

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            activities = yaml.safe_load(f)

        if not activities:
            return 0, []

        modified = False

        for idx, activity in enumerate(activities):
            if not isinstance(activity, dict):
                continue

            if activity.get('type') == 'cloze':
                passage = activity.get('passage', '')
                title = activity.get('title', f'Untitled cloze #{idx+1}')

                # Check for double newlines (blank lines)
                if '\n\n' in passage:
                    # Replace all occurrences of double newlines with single newline
                    fixed_passage = passage.replace('\n\n', '\n')

                    # Also clean up any triple+ newlines that might exist
                    while '\n\n' in fixed_passage:
                        fixed_passage = fixed_passage.replace('\n\n', '\n')

                    activity['passage'] = fixed_passage
                    fixed_count += 1
                    fixed_titles.append(title)
                    modified = True

        # Write back if modified
        if modified and not dry_run:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(activities, f, allow_unicode=True, sort_keys=False, width=1000)

    except Exception as e:
        print(f"Error processing {yaml_path}: {e}", file=sys.stderr)

    return fixed_count, fixed_titles

def fix_curriculum(base_path: Path, dry_run: bool = False) -> dict:
    """
    Fix entire curriculum for cloze blank line violations.

    Returns: Dict mapping file paths to (count, titles) tuples
    """
    results = {}

    # Scan all levels
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']

    for level in levels:
        level_path = base_path / level / 'activities'
        if not level_path.exists():
            continue

        for yaml_file in sorted(level_path.glob('*.yaml')):
            count, titles = fix_blank_lines_in_cloze(yaml_file, dry_run)
            if count > 0:
                results[yaml_file] = (count, titles)

    return results

def main():
    # Parse args
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # Find curriculum base path
    script_dir = Path(__file__).parent
    curriculum_base = script_dir.parent / 'curriculum' / 'l2-uk-en'

    if not curriculum_base.exists():
        print(f"Curriculum path not found: {curriculum_base}", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    print("Fixing cloze activities with blank lines...\n")

    results = fix_curriculum(curriculum_base, dry_run)

    if not results:
        print("✅ No violations found - all cloze activities are clean!")
        sys.exit(0)

    # Report fixes
    action = "Would fix" if dry_run else "Fixed"
    print(f"✅ {action} {len(results)} files:\n")

    total_fixed = 0
    for yaml_path, (count, titles) in sorted(results.items()):
        level = yaml_path.parent.parent.name
        module = yaml_path.stem

        print(f"📁 {level}/{module} ({count} activities fixed)")
        for title in titles:
            print(f"   - {title}")
            total_fixed += 1
        print()

    print(f"Total: {total_fixed} cloze activities across {len(results)} modules")

    if dry_run:
        print("\nRun without --dry-run to apply fixes")
        sys.exit(0)
    else:
        print("\n✅ All fixes applied successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
