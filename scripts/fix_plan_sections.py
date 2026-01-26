#!/usr/bin/env python3
"""
Fix plan content_outline sections to match actual markdown H2 headers.

This is a more aggressive fix that updates plans to match whatever structure
the markdown actually has, regardless of PPP/checkpoint/other format.
"""

import re
import subprocess
import sys
from pathlib import Path
import yaml


# Sections to exclude (boilerplate)
EXCLUDED_SECTIONS = {
    'need more practice?',
    'підсумок',
}


def get_sections_from_markdown(md_path: Path) -> list[tuple[str, int]]:
    """Extract H2 sections and approximate word counts."""
    content = md_path.read_text(encoding='utf-8')

    sections = []
    h2_pattern = r'^## (.+)$'

    lines = content.split('\n')
    current_section = None
    current_lines = []

    for line in lines:
        match = re.match(h2_pattern, line)
        if match:
            if current_section and current_section.lower() not in EXCLUDED_SECTIONS:
                word_count = len(' '.join(current_lines).split())
                sections.append((current_section, word_count))
            current_section = match.group(1).strip()
            current_lines = []
        elif current_section:
            current_lines.append(line)

    if current_section and current_section.lower() not in EXCLUDED_SECTIONS:
        word_count = len(' '.join(current_lines).split())
        sections.append((current_section, word_count))

    return sections


def get_audit_counts(md_path: Path) -> dict[str, int]:
    """Get accurate word counts from audit."""
    result = subprocess.run(
        ['.venv/bin/python', 'scripts/audit_module.py', str(md_path)],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr
    counts = {}

    # Parse: "     Section Name           123 /  456  ✅"
    pattern = r'^\s+(\S.*?)\s+(\d+)\s+/\s+\d+\s+[✅❌⚠️]'
    for line in output.split('\n'):
        match = re.match(pattern, line)
        if match:
            counts[match.group(1).strip()] = int(match.group(2))

    return counts


def update_plan(plan_path: Path, md_path: Path, dry_run: bool = False) -> bool:
    """Update plan content_outline to match markdown sections."""
    content = plan_path.read_text(encoding='utf-8')
    plan = yaml.safe_load(content)

    if not plan:
        return False

    # Get sections from markdown
    md_sections = get_sections_from_markdown(md_path)

    if not md_sections:
        print("  No sections found in markdown")
        return False

    # Build new content_outline
    new_outline = []
    for section_name, approx_words in md_sections:
        new_outline.append({
            'section': section_name,
            'words': approx_words,
            'points': [f'Content for {section_name}']
        })

    # Check if change needed
    old_sections = [s.get('section', '') for s in plan.get('content_outline', [])]
    new_sections = [s['section'] for s in new_outline]

    if old_sections == new_sections:
        return False

    plan['content_outline'] = new_outline
    plan['word_target'] = sum(s['words'] for s in new_outline)

    if dry_run:
        print(f"  Would update: {len(old_sections)} -> {len(new_sections)} sections")
        return True

    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    print(f"  Updated: {len(old_sections)} -> {len(new_sections)} sections")
    return True


def main():
    dry_run = '--dry-run' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('-')]

    if not args:
        print("Usage: fix_plan_sections.py <level> [module_num]")
        sys.exit(1)

    level = args[0]
    module_filter = args[1] if len(args) > 1 else None

    base_path = Path('curriculum/l2-uk-en')
    md_path = base_path / level
    plans_path = base_path / 'plans' / level

    md_files = sorted(md_path.glob('*.md'))

    if module_filter:
        md_files = [f for f in md_files if f.stem.startswith(f"{module_filter.zfill(2)}-")]

    updated = 0
    for md_file in md_files:
        slug = md_file.stem
        plan_file = plans_path / f"{slug}.yaml"

        if not plan_file.exists():
            continue

        print(f"Processing {slug}...")

        if update_plan(plan_file, md_file, dry_run):
            updated += 1

    print(f"\nUpdated: {updated}")


if __name__ == '__main__':
    main()
