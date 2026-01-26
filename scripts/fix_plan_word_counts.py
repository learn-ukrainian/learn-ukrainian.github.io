#!/usr/bin/env python3
"""
Fix plan word counts to match actual markdown content (as measured by audit).

This script:
1. Runs the audit to get actual section word counts
2. Updates the plan's content_outline with those counts
"""

import re
import subprocess
import sys
from pathlib import Path
import yaml


def get_audit_section_counts(md_path: Path) -> dict[str, int]:
    """Run audit and extract section word counts."""
    result = subprocess.run(
        ['.venv/bin/python', 'scripts/audit_module.py', str(md_path)],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    # Parse section word analysis
    # Format: "     Warm-up            100 /  100  ✅ "
    section_pattern = r'^\s+(\S.*?)\s+(\d+)\s+/\s+\d+\s+[✅❌⚠️]'

    counts = {}
    for line in output.split('\n'):
        match = re.match(section_pattern, line)
        if match:
            section_name = match.group(1).strip()
            actual_count = int(match.group(2))
            counts[section_name] = actual_count

    return counts


def update_plan_counts(plan_path: Path, counts: dict[str, int], dry_run: bool = False) -> bool:
    """Update plan's content_outline word counts."""
    content = plan_path.read_text(encoding='utf-8')
    plan = yaml.safe_load(content)

    if not plan or 'content_outline' not in plan:
        return False

    changed = False
    for section in plan['content_outline']:
        section_name = section.get('section', '')
        if section_name in counts:
            actual = counts[section_name]
            if section.get('words') != actual:
                section['words'] = actual
                changed = True

    if not changed:
        return False

    # Update word_target
    total = sum(s.get('words', 0) for s in plan['content_outline'])
    plan['word_target'] = total

    if dry_run:
        print(f"  Would update: {plan_path}")
        return True

    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return True


def main():
    dry_run = '--dry-run' in sys.argv
    level = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else 'a1'

    base_path = Path('curriculum/l2-uk-en')
    md_path = base_path / level
    plans_path = base_path / 'plans' / level

    if not md_path.exists() or not plans_path.exists():
        print(f"ERROR: Paths not found for level {level}")
        sys.exit(1)

    md_files = sorted(md_path.glob('*.md'))

    updated = 0
    skipped = 0

    for md_file in md_files:
        slug = md_file.stem
        plan_file = plans_path / f"{slug}.yaml"

        if not plan_file.exists():
            continue

        print(f"Processing {slug}...", end=' ')

        # Get actual counts from audit
        counts = get_audit_section_counts(md_file)

        if not counts:
            print("SKIP (no sections found)")
            skipped += 1
            continue

        if update_plan_counts(plan_file, counts, dry_run):
            print("UPDATED")
            updated += 1
        else:
            print("OK (no change needed)")
            skipped += 1

    print(f"\nSummary: {updated} updated, {skipped} skipped")
    if dry_run:
        print("(DRY RUN)")


if __name__ == '__main__':
    main()
