#!/usr/bin/env python3
"""
Fix plan word_target mismatches against config.py.

This script:
1. Reads the authoritative target_words from config.py
2. Compares against each plan's word_target
3. Recalculates section budgets proportionally to match config
4. Updates both word_target and content_outline section words

Usage:
    .venv/bin/python scripts/fix_plan_word_targets.py --check          # Report mismatches only
    .venv/bin/python scripts/fix_plan_word_targets.py --fix            # Fix all mismatches
    .venv/bin/python scripts/fix_plan_word_targets.py --fix c1-hist    # Fix specific level
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from audit.config import get_word_target


def get_config_target(level: str, module_num: int = 1, focus: str = None) -> int:
    """Get the authoritative word target from config.py."""
    # Map plan level names to LEVEL_CONFIG keys
    # Note: LEVEL_CONFIG uses 'C1-history' not 'C1-HIST'
    level_map = {
        'a1': 'A1',
        'a2': 'A2',
        'b1': 'B1',
        'b2': 'B2',
        'c1': 'C1',
        'c2': 'C2',
        'b2-hist': 'B2-history',
        'c1-hist': 'C1-history',
        'c1-bio': 'C1-biography',
        'lit': 'LIT',
    }

    level_code = level_map.get(level.lower(), level.upper())

    # For seminar tracks with specific config keys, get directly from LEVEL_CONFIG
    # instead of going through get_word_target which has different logic
    from audit.config import LEVEL_CONFIG
    if level_code in LEVEL_CONFIG:
        return LEVEL_CONFIG[level_code].get('target_words', 2000)

    return get_word_target(level_code, module_num, focus)


def load_plan(plan_path: Path) -> dict:
    """Load a plan YAML file."""
    with open(plan_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_plan(plan_path: Path, plan: dict) -> None:
    """Save a plan YAML file."""
    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def recalculate_sections(content_outline: list, current_total: int, new_total: int) -> list:
    """Recalculate section word budgets proportionally."""
    if current_total == 0:
        return content_outline

    ratio = new_total / current_total
    new_outline = []
    running_total = 0

    for i, section in enumerate(content_outline):
        new_section = dict(section)
        old_words = section.get('words', 0)

        if i == len(content_outline) - 1:
            # Last section gets remainder to ensure exact total
            new_words = new_total - running_total
        else:
            # Round to nearest integer, but ensure minimum of 100 words
            new_words = max(100, round(old_words * ratio))

        new_section['words'] = new_words
        running_total += new_words
        new_outline.append(new_section)

    return new_outline


def check_plan(plan_path: Path, level: str) -> dict:
    """Check a single plan for word_target mismatch or outline sum mismatch."""
    plan = load_plan(plan_path)

    if not plan:
        return {'status': 'empty', 'path': plan_path}

    plan_target = plan.get('word_target', 0)
    sequence = plan.get('sequence', 1)
    focus = plan.get('focus')

    config_target = get_config_target(level, sequence, focus)

    # Calculate current outline total
    outline = plan.get('content_outline', [])
    outline_total = sum(s.get('words', 0) for s in outline)

    # Flag as mismatch if:
    # 1. plan_target < config_target (needs more words)
    # 2. outline_sum != plan_target (sections don't match word_target)
    is_under = plan_target < config_target
    outline_mismatch = outline_total > 0 and abs(outline_total - plan_target) > plan_target * 0.05

    return {
        'path': plan_path,
        'slug': plan.get('module', plan_path.stem),
        'plan_target': plan_target,
        'config_target': config_target,
        'outline_total': outline_total,
        'mismatch': is_under,  # word_target under config
        'outline_mismatch': outline_mismatch,  # outline sum != word_target
        'delta': config_target - plan_target,
    }


def fix_plan(plan_path: Path, level: str, dry_run: bool = False) -> dict:
    """Fix a single plan's word_target and section budgets."""
    result = check_plan(plan_path, level)

    needs_fix = result.get('mismatch') or result.get('outline_mismatch')
    if not needs_fix:
        result['action'] = 'no_change'
        return result

    plan = load_plan(plan_path)
    old_target = result['plan_target']
    config_target = result['config_target']

    # Determine new target: use config if under, otherwise keep plan target
    if result.get('mismatch'):
        new_target = config_target
        plan['word_target'] = new_target
    else:
        new_target = old_target  # Keep existing word_target, just fix outline

    # Recalculate sections to match new_target
    old_outline = plan.get('content_outline', [])
    old_total = sum(s.get('words', 0) for s in old_outline)

    if old_total > 0:
        new_outline = recalculate_sections(old_outline, old_total, new_target)
        plan['content_outline'] = new_outline

    if not dry_run:
        save_plan(plan_path, plan)
        result['action'] = 'fixed'
    else:
        result['action'] = 'would_fix'

    result['new_outline_total'] = sum(s.get('words', 0) for s in plan.get('content_outline', []))

    return result


def get_plan_levels() -> list:
    """Get all levels that have plan directories."""
    plans_dir = Path('curriculum/l2-uk-en/plans')
    levels = []

    for subdir in sorted(plans_dir.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith('.'):
            levels.append(subdir.name)

    return levels


def process_level(level: str, fix: bool = False, dry_run: bool = False) -> dict:
    """Process all plans for a level."""
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')

    if not plans_dir.exists():
        return {'level': level, 'error': 'Directory not found', 'results': []}

    results = []
    for plan_path in sorted(plans_dir.glob('*.yaml')):
        if fix:
            result = fix_plan(plan_path, level, dry_run)
        else:
            result = check_plan(plan_path, level)
        results.append(result)

    return {
        'level': level,
        'total': len(results),
        'mismatches': sum(1 for r in results if r.get('mismatch')),
        'outline_mismatches': sum(1 for r in results if r.get('outline_mismatch')),
        'needs_fix': sum(1 for r in results if r.get('mismatch') or r.get('outline_mismatch')),
        'results': results,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Fix plan word_target mismatches against config.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check all levels for mismatches
    .venv/bin/python scripts/fix_plan_word_targets.py --check

    # Check specific level
    .venv/bin/python scripts/fix_plan_word_targets.py --check c1-hist

    # Fix all mismatches (dry run)
    .venv/bin/python scripts/fix_plan_word_targets.py --fix --dry-run

    # Fix specific level
    .venv/bin/python scripts/fix_plan_word_targets.py --fix c1-hist
        """
    )

    parser.add_argument('--check', action='store_true', help='Check for mismatches (report only)')
    parser.add_argument('--fix', action='store_true', help='Fix mismatches')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('level', nargs='?', help='Specific level to process (e.g., c1-hist)')

    args = parser.parse_args()

    if not args.check and not args.fix:
        parser.print_help()
        sys.exit(1)

    # Get levels to process
    if args.level:
        levels = [args.level]
    else:
        levels = get_plan_levels()

    # Process each level
    total_issues = 0
    total_fixed = 0

    for level in levels:
        result = process_level(level, fix=args.fix, dry_run=args.dry_run)

        if 'error' in result:
            print(f"\n{level.upper()}: {result['error']}")
            continue

        needs_fix = result['needs_fix']
        total_issues += needs_fix

        if needs_fix == 0:
            print(f"\n{level.upper()}: ✅ All {result['total']} plans OK")
            continue

        print(f"\n{level.upper()}: ❌ {needs_fix}/{result['total']} plans need fixing")

        # Show details
        for r in result['results']:
            has_issue = r.get('mismatch') or r.get('outline_mismatch')
            if not has_issue:
                continue

            action = r.get('action', 'check')
            issue_type = []
            if r.get('mismatch'):
                issue_type.append(f"target: {r['plan_target']}→{r['config_target']}")
            if r.get('outline_mismatch'):
                issue_type.append(f"outline: {r['outline_total']}→{r['plan_target']}")
            issue_str = ', '.join(issue_type)

            if args.fix:
                if action == 'fixed':
                    total_fixed += 1
                    print(f"  ✅ {r['slug']}: {issue_str}")
                elif action == 'would_fix':
                    total_fixed += 1
                    print(f"  🔧 {r['slug']}: {issue_str} [dry-run]")
            else:
                print(f"  • {r['slug']}: {issue_str}")

    # Summary
    print(f"\n{'='*50}")
    if args.check:
        print(f"Total plans needing fix: {total_issues}")
        if total_issues > 0:
            print(f"Run with --fix to correct them")
    elif args.fix:
        if args.dry_run:
            print(f"Would fix: {total_fixed} plans")
            print("Run without --dry-run to apply changes")
        else:
            print(f"Fixed: {total_fixed} plans")


if __name__ == '__main__':
    main()
