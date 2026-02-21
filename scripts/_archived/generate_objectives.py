#!/usr/bin/env python3
"""
Generate objectives for plan files that are missing them.

Objectives are generated based on:
- Module title
- Focus (grammar, vocab, cultural, history, biography)
- Content outline sections
- Level

Usage:
    .venv/bin/python scripts/generate_objectives.py --check          # Report only
    .venv/bin/python scripts/generate_objectives.py --fix            # Fix all
    .venv/bin/python scripts/generate_objectives.py --fix b2         # Fix specific level
"""

import argparse
import sys
from pathlib import Path

import yaml


# Bloom's taxonomy verbs by focus type
OBJECTIVE_VERBS = {
    'grammar': [
        'Identify and correctly use',
        'Form and apply',
        'Distinguish between',
        'Master the usage of',
        'Apply in context',
    ],
    'vocab': [
        'Expand vocabulary related to',
        'Use appropriately',
        'Distinguish nuances of',
        'Apply in various contexts',
        'Master key terminology for',
    ],
    'cultural': [
        'Understand and appreciate',
        'Analyze the significance of',
        'Compare and contrast',
        'Discuss key aspects of',
        'Explore the role of',
    ],
    'history': [
        'Analyze the causes and consequences of',
        'Evaluate the historical significance of',
        'Trace the development of',
        'Examine primary sources related to',
        'Compare historical perspectives on',
    ],
    'biography': [
        'Analyze the life and legacy of',
        'Evaluate the contributions of',
        'Trace the career and influence of',
        'Examine the historical context of',
        'Assess the impact of',
    ],
    'literature': [
        'Analyze literary techniques in',
        'Interpret themes and motifs of',
        'Evaluate the cultural significance of',
        'Compare stylistic elements across',
        'Examine the historical context of',
    ],
    'default': [
        'Understand and apply',
        'Analyze and evaluate',
        'Identify key concepts of',
        'Demonstrate proficiency in',
        'Master essential skills for',
    ],
}


def get_focus_from_level(level: str) -> str:
    """Determine focus type from level name."""
    level_lower = level.lower()
    if 'hist' in level_lower:
        return 'history'
    if 'bio' in level_lower:
        return 'biography'
    if 'lit' in level_lower:
        return 'literature'
    return 'default'


def extract_topic_from_title(title: str) -> str:
    """Extract the main topic from a module title."""
    # Remove common prefixes
    prefixes = ['Checkpoint:', 'Review:', 'Practice:', 'Synthesis:']
    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
    return title


def generate_objectives(plan: dict, level: str) -> list:
    """Generate 2-3 objectives based on plan content."""
    title = plan.get('title', '')
    focus = plan.get('focus', get_focus_from_level(level))
    outline = plan.get('content_outline', [])

    # Get appropriate verbs for this focus
    verbs = OBJECTIVE_VERBS.get(focus, OBJECTIVE_VERBS['default'])

    # Extract topic from title
    topic = extract_topic_from_title(title)

    objectives = []

    # First objective: based on title
    if topic:
        objectives.append(f"{verbs[0]} {topic.lower()}")

    # Second objective: based on first content section
    if outline and len(outline) > 0:
        first_section = outline[0].get('section', '')
        if first_section:
            # Clean up section name
            section_topic = first_section.split('—')[-1].strip() if '—' in first_section else first_section
            section_topic = section_topic.split(':')[-1].strip() if ':' in section_topic else section_topic
            objectives.append(f"{verbs[1]} {section_topic.lower()}")

    # Third objective: based on overall focus or last section
    if len(outline) > 2:
        last_section = outline[-1].get('section', '')
        if last_section and 'підсумок' not in last_section.lower() and 'висновок' not in last_section.lower():
            section_topic = last_section.split('—')[-1].strip() if '—' in last_section else last_section
            objectives.append(f"{verbs[2]} {section_topic.lower()}")
    elif len(objectives) < 2:
        # Fallback objective
        objectives.append(f"{verbs[2]} key concepts in this module")

    # Ensure we have at least 2 objectives
    if len(objectives) < 2:
        objectives.append(f"Apply knowledge of {topic.lower()} in practical contexts")

    # Capitalize first letter of each objective
    objectives = [obj[0].upper() + obj[1:] if obj else obj for obj in objectives]

    # Limit to 3 objectives
    return objectives[:3]


def load_plan(plan_path: Path) -> dict:
    """Load a plan YAML file."""
    with open(plan_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_plan(plan_path: Path, plan: dict) -> None:
    """Save a plan YAML file."""
    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def check_plan(plan_path: Path, level: str) -> dict:
    """Check if a plan is missing objectives."""
    plan = load_plan(plan_path)

    if not plan:
        return {'status': 'empty', 'path': plan_path}

    objectives = plan.get('objectives', [])
    missing = not objectives or len(objectives) == 0

    return {
        'path': plan_path,
        'slug': plan.get('module', plan_path.stem),
        'title': plan.get('title', ''),
        'missing': missing,
        'current_objectives': objectives,
    }


def fix_plan(plan_path: Path, level: str, dry_run: bool = False) -> dict:
    """Add objectives to a plan that's missing them."""
    result = check_plan(plan_path, level)

    if not result.get('missing'):
        result['action'] = 'no_change'
        return result

    plan = load_plan(plan_path)
    new_objectives = generate_objectives(plan, level)

    # Insert objectives after title or at appropriate position
    plan['objectives'] = new_objectives

    if not dry_run:
        save_plan(plan_path, plan)
        result['action'] = 'fixed'
    else:
        result['action'] = 'would_fix'

    result['new_objectives'] = new_objectives
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
        'missing': sum(1 for r in results if r.get('missing')),
        'results': results,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Generate objectives for plans missing them',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--check', action='store_true', help='Check for missing objectives')
    parser.add_argument('--fix', action='store_true', help='Generate and add objectives')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed')
    parser.add_argument('level', nargs='?', help='Specific level to process')

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
    total_missing = 0
    total_fixed = 0

    for level in levels:
        result = process_level(level, fix=args.fix, dry_run=args.dry_run)

        if 'error' in result:
            print(f"\n{level.upper()}: {result['error']}")
            continue

        missing = result['missing']
        total_missing += missing

        if missing == 0:
            print(f"\n{level.upper()}: ✅ All {result['total']} plans have objectives")
            continue

        print(f"\n{level.upper()}: ❌ {missing}/{result['total']} plans missing objectives")

        # Show details (limit output)
        shown = 0
        for r in result['results']:
            if not r.get('missing'):
                continue

            if args.fix:
                if r.get('action') == 'fixed':
                    total_fixed += 1
                    if shown < 3:  # Show first 3 examples
                        print(f"  ✅ {r['slug']}: {r.get('new_objectives', [])[:2]}")
                        shown += 1
                elif r.get('action') == 'would_fix':
                    total_fixed += 1
                    if shown < 3:
                        print(f"  🔧 {r['slug']}: {r.get('new_objectives', [])[:2]} [dry-run]")
                        shown += 1
            else:
                if shown < 5:
                    print(f"  • {r['slug']}: {r['title'][:50]}")
                    shown += 1

        if shown < missing:
            print(f"  ... and {missing - shown} more")

    # Summary
    print(f"\n{'='*50}")
    if args.check:
        print(f"Total plans missing objectives: {total_missing}")
        if total_missing > 0:
            print("Run with --fix to generate objectives")
    elif args.fix:
        if args.dry_run:
            print(f"Would fix: {total_fixed} plans")
            print("Run without --dry-run to apply changes")
        else:
            print(f"Fixed: {total_fixed} plans")


if __name__ == '__main__':
    main()
