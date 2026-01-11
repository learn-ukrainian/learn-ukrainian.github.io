#!/usr/bin/env python3
"""
Detect blank lines in cloze activity passages across all curriculum YAML files.

Blank lines (\n\n) in cloze passages cause MDX/HTML rendering issues.
This script scans all activities/*.yaml files and reports violations.
"""

import yaml
import sys
from pathlib import Path
from typing import List, Tuple

def detect_blank_lines_in_cloze(yaml_path: Path) -> List[Tuple[int, str]]:
    """
    Detect cloze activities with blank lines in their passages.

    Returns: List of (activity_index, title) tuples with violations
    """
    violations = []

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            activities = yaml.safe_load(f)

        if not activities:
            return violations

        for idx, activity in enumerate(activities):
            if not isinstance(activity, dict):
                continue

            if activity.get('type') == 'cloze':
                passage = activity.get('passage', '')
                title = activity.get('title', f'Untitled cloze #{idx+1}')

                # Check for double newlines (blank lines)
                if '\n\n' in passage:
                    violations.append((idx, title))

    except Exception as e:
        print(f"Error processing {yaml_path}: {e}", file=sys.stderr)

    return violations

def scan_curriculum(base_path: Path) -> dict:
    """
    Scan entire curriculum for cloze blank line violations.

    Returns: Dict mapping file paths to violation lists
    """
    results = {}

    # Scan all levels
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']

    for level in levels:
        level_path = base_path / level / 'activities'
        if not level_path.exists():
            continue

        for yaml_file in sorted(level_path.glob('*.yaml')):
            violations = detect_blank_lines_in_cloze(yaml_file)
            if violations:
                results[yaml_file] = violations

    return results

def main():
    # Find curriculum base path
    script_dir = Path(__file__).parent
    curriculum_base = script_dir.parent / 'curriculum' / 'l2-uk-en'

    if not curriculum_base.exists():
        print(f"Curriculum path not found: {curriculum_base}", file=sys.stderr)
        sys.exit(1)

    print("Scanning curriculum for cloze activities with blank lines...\n")

    results = scan_curriculum(curriculum_base)

    if not results:
        print("✅ No violations found - all cloze activities are clean!")
        sys.exit(0)

    # Report violations
    print(f"❌ Found {len(results)} files with violations:\n")

    total_violations = 0
    for yaml_path, violations in sorted(results.items()):
        level = yaml_path.parent.parent.name
        module = yaml_path.stem

        print(f"📁 {level}/{module} ({len(violations)} violations)")
        for idx, title in violations:
            print(f"   - Activity #{idx+1}: {title}")
            total_violations += 1
        print()

    print(f"Total violations: {total_violations} cloze activities across {len(results)} modules")
    sys.exit(1)

if __name__ == '__main__':
    main()
