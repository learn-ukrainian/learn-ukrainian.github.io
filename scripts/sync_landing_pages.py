#!/usr/bin/env python3
"""
sync_landing_pages.py - Sync website landing pages with curriculum state.

Updates:
- docusaurus/docs/intro.mdx (main curriculum overview)
- docusaurus/docs/{level}/index.mdx (level landing pages)

Data sources:
- Configuration: docs/l2-uk-en/level-status.yaml (planned counts, status overrides)
- Ready modules: docusaurus/docs/{level}/module-*.mdx files

Usage:
    python scripts/sync_landing_pages.py           # Apply changes
    python scripts/sync_landing_pages.py --dry-run # Preview only
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# Project root
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / 'docs' / 'l2-uk-en' / 'level-status.yaml'


def load_config() -> dict:
    """Load level configuration from YAML file."""
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found: {CONFIG_PATH}")
        print("Create docs/l2-uk-en/level-status.yaml with level configurations.")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    # Validate and normalize
    levels = {}
    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        if level not in config:
            print(f"Warning: Level {level} not found in config, using defaults")
            levels[level] = {'planned': 0, 'status': 'auto', 'description': f'{level.upper()} Level'}
        else:
            levels[level] = {
                'planned': config[level].get('planned', 0),
                'status': config[level].get('status', 'auto'),
                'description': config[level].get('description', f'{level.upper()} Level'),
            }

    return levels


# Load configuration
LEVELS = load_config()


def count_ready_modules(level: str) -> int:
    """Count MDX files for a level."""
    mdx_dir = ROOT / 'docusaurus' / 'docs' / level
    if not mdx_dir.exists():
        return 0
    return len(list(mdx_dir.glob('module-*.mdx')))


def get_status(level: str, ready: int, planned: int) -> tuple[str, str]:
    """
    Determine status based on completion percentage.

    Returns: (emoji_status, status_text)
    """
    # Check for manual override from config
    level_config = LEVELS.get(level, {})
    if level_config.get('status') == 'complete':
        return '✅', 'Complete'

    if planned == 0:
        return '📋', 'Planned'

    pct = ready / planned

    if pct >= 1.0:
        return '🔍', 'In QA'  # 100% but not manually verified
    elif pct >= 0.10:
        return '🚧', 'In Progress'  # 10-99%
    else:
        return '📋', 'Planned'  # <10%


def collect_stats() -> dict:
    """Collect statistics for all levels."""
    stats = {}
    for level, config in LEVELS.items():
        ready = count_ready_modules(level)
        planned = config['planned']
        emoji, status_text = get_status(level, ready, planned)

        stats[level] = {
            'ready': ready,
            'planned': planned,
            'emoji': emoji,
            'status': status_text,
            'description': config['description'],
            'pct': round(100 * ready / planned) if planned > 0 else 0,
        }
    return stats


def update_intro_mdx(stats: dict, dry_run: bool) -> bool:
    """Update the main intro.mdx curriculum table."""
    intro_path = ROOT / 'docusaurus' / 'docs' / 'intro.mdx'
    if not intro_path.exists():
        print(f"  ! {intro_path} not found")
        return False

    content = intro_path.read_text()
    original = content

    # Build new curriculum table
    table_lines = [
        "| Level | Description | Lessons | Status |",
        "|-------|-------------|---------|--------|",
    ]

    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        s = stats[level]
        status_str = f"{s['emoji']} {s['status']}"
        table_lines.append(
            f"| **{level.upper()}** | {s['description']} | {s['planned']} | {status_str} |"
        )

    new_table = '\n'.join(table_lines)

    # Replace the curriculum table (header + separator + 6 data rows)
    pattern = (
        r'\| Level \| Description \| Lessons \| Status \|\n'
        r'\|[-]+\|[-]+\|[-]+\|[-]+\|\n'
        r'(?:\|[^\n]+\|\n)+'
    )
    content = re.sub(pattern, new_table + '\n', content)

    # Update total count
    total_planned = sum(stats[l]['planned'] for l in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2'])
    total_pattern = r'\*\*Total:\*\* \d+\+? lessons'
    content = re.sub(total_pattern, f'**Total:** {total_planned} lessons', content)

    if content != original:
        if dry_run:
            print(f"  ~ Would update {intro_path.relative_to(ROOT)}")
        else:
            intro_path.write_text(content)
            print(f"  ✓ Updated {intro_path.relative_to(ROOT)}")
        return True
    else:
        print(f"  - {intro_path.relative_to(ROOT)} (no changes)")
        return False


def update_level_index(level: str, stats: dict, dry_run: bool) -> bool:
    """Update a level's index.mdx with current stats."""
    index_path = ROOT / 'docusaurus' / 'docs' / level / 'index.mdx'
    if not index_path.exists():
        print(f"  - {level}/index.mdx not found")
        return False

    content = index_path.read_text()
    original = content
    s = stats[level]

    # Update header line patterns (various formats used)
    # Pattern 1: "**В розробці — 145 модулів**"
    # Pattern 2: "**🚧 В розробці — 86/86 модулів**"

    if s['status'] == 'Complete':
        new_header = f"**{s['emoji']} Завершено — {s['ready']} модулів**"
    elif s['status'] == 'In QA':
        new_header = f"**{s['emoji']} На перевірці — {s['ready']}/{s['planned']} модулів**"
    elif s['status'] == 'In Progress':
        new_header = f"**{s['emoji']} В розробці — {s['ready']}/{s['planned']} модулів**"
    else:  # Planned
        new_header = f"**{s['emoji']} Заплановано — 0/{s['planned']} модулів**"

    # Replace header line (first bold line with модулів)
    header_pattern = r'\*\*(?:✅|🔍|🚧|📋|В розробці)?[^*]*?(?:модулі?в?|modules?)\*\*'
    if re.search(header_pattern, content):
        content = re.sub(header_pattern, new_header, content, count=1)

    if content != original:
        if dry_run:
            print(f"  ~ Would update {index_path.relative_to(ROOT)}")
        else:
            index_path.write_text(content)
            print(f"  ✓ Updated {index_path.relative_to(ROOT)}")
        return True
    else:
        print(f"  - {level}/index.mdx (no changes)")
        return False


def print_summary(stats: dict):
    """Print a summary table."""
    print("\n📊 Landing Page Sync\n")
    print("Level  Planned  Ready  Status")
    print("─────  ───────  ─────  ──────")

    total_planned = 0
    total_ready = 0

    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        s = stats[level]
        total_planned += s['planned']
        total_ready += s['ready']

        pct_str = f"({s['pct']}%)" if s['status'] == 'In Progress' else ''
        print(f"{level.upper():5}  {s['planned']:7}  {s['ready']:5}  {s['emoji']} {s['status']} {pct_str}")

    print(f"\nTotal: {total_planned} modules ({total_ready} ready)")


def main():
    parser = argparse.ArgumentParser(description='Sync landing pages with curriculum state')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    stats = collect_stats()
    print_summary(stats)

    print("\nUpdating files:" if not args.dry_run else "\nDry run - would update:")

    updated = []

    # Update main intro.mdx
    if update_intro_mdx(stats, args.dry_run):
        updated.append('intro.mdx')

    # Update level index pages
    for level in LEVELS:
        if update_level_index(level, stats, args.dry_run):
            updated.append(f'{level}/index.mdx')

    if updated:
        print(f"\n{'Would update' if args.dry_run else 'Updated'}: {len(updated)} file(s)")
    else:
        print("\nNo changes needed.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
