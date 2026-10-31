#!/usr/bin/env python3
"""
Validate plan structure before content generation.

Sizing metadata (word targets, section word budgets, budget sums, and
size-policy overrides) is ignored. Objective and content-outline structure
still fails the plan when it is missing.

Usage:
    .venv/bin/python scripts/validate_plan_config.py                    # Validate all
    .venv/bin/python scripts/validate_plan_config.py istorio           # Validate level
    .venv/bin/python scripts/validate_plan_config.py istorio/shcho-*   # Validate specific plan

Exit codes:
    0 = All plans valid
    1 = Validation errors found
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from audit.config import get_word_target


def get_config_target(level: str, sequence: int = 1, focus: str | None = None,
                      slug: str = "") -> int:
    """Get the authoritative word target from config.py.

    Checks subtype-specific keys first (e.g., A2-checkpoint=1500),
    then falls back to the base level key (e.g., A2=2000).
    """
    from audit.config import LEVEL_CONFIG

    # Map plan level names to LEVEL_CONFIG keys
    level_map = {
        'a1': 'A1', 'a2': 'A2', 'b1': 'B1', 'b2': 'B2',
        'c1': 'C1', 'c2': 'C2',
        'hist': 'history', 'istorio': 'istorio',
        'bio': 'biography', 'lit': 'LIT',
    }
    level_code = level_map.get(level.lower(), level.upper())

    # Detect subtype from slug name
    # Priority: most specific match first
    subtype_patterns = [
        ('checkpoint', 'checkpoint'),
        ('capstone', 'capstone'),
        ('bridge', 'capstone'),
        ('finale', 'checkpoint'),
        ('practice-exam', 'checkpoint'),
        ('comprehensive-review', 'checkpoint'),
        ('practice', 'checkpoint'),
        ('review', 'checkpoint'),
    ]
    for pattern, subtype in subtype_patterns:
        if pattern in slug:
            subtype_key = f"{level_code}-{subtype}"
            if subtype_key in LEVEL_CONFIG:
                return LEVEL_CONFIG[subtype_key].get('target_words', 2000)
            break

    # Fall back to base level or focus-specific key
    if level_code in LEVEL_CONFIG:
        return LEVEL_CONFIG[level_code].get('target_words', 2000)

    return get_word_target(level_code, sequence, focus)


def validate_plan(plan_path: Path, level: str) -> list:
    """Validate a single plan file. Returns list of errors.

    ``level`` stays in the signature for existing callers. Acceptance does not
    use it, and it does not apply a word-count target.
    """
    errors = []

    try:
        with open(plan_path, encoding='utf-8') as f:
            plan = yaml.safe_load(f)
    except Exception as e:
        return [f"Failed to parse YAML: {e}"]

    if not plan:
        return ["Empty plan file"]

    outline = plan.get('content_outline', [])
    if not outline:
        errors.append("Missing content_outline")

    # Check required fields
    required_fields = ['module', 'level', 'title', 'objectives']
    for field in required_fields:
        if not plan.get(field):
            errors.append(f"Missing required field: {field}")

    return errors


def validate_level(level: str, plan_pattern: str | None = None) -> dict:
    """Validate all plans for a level."""
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')

    if not plans_dir.exists():
        return {'level': level, 'error': f'Directory not found: {plans_dir}', 'plans': []}

    plan_paths = sorted(plans_dir.glob('*.yaml'))
    if plan_pattern:
        import fnmatch

        plan_paths = [
            plan_path
            for plan_path in plan_paths
            if fnmatch.fnmatch(plan_path.stem, plan_pattern)
        ]

    results = []
    for plan_path in plan_paths:
        errors = validate_plan(plan_path, level)
        results.append({
            'path': plan_path,
            'slug': plan_path.stem,
            'errors': errors,
            'valid': len(errors) == 0,
        })

    return {
        'level': level,
        'total': len(results),
        'valid': sum(1 for r in results if r['valid']),
        'invalid': sum(1 for r in results if not r['valid']),
        'plans': results,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Validate plan files against config.py',
        epilog='Exit code 0 = valid, 1 = errors found'
    )
    parser.add_argument('target', nargs='?',
                        help='Level (e.g., istorio) or plan path pattern (e.g., istorio/shcho-*)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only show errors, not successes')

    args = parser.parse_args()

    # Determine what to validate
    if args.target:
        if '/' in args.target:
            # Specific plan pattern
            level, pattern = args.target.split('/', 1)
            levels = [level]
            plan_pattern = pattern
        else:
            levels = [args.target]
            plan_pattern = None
    else:
        # All levels
        plans_base = Path('curriculum/l2-uk-en/plans')
        levels = [d.name for d in sorted(plans_base.iterdir())
                  if d.is_dir() and not d.name.startswith('.')]
        plan_pattern = None

    # Validate
    total_invalid = 0
    total_plans = 0

    for level in levels:
        result = validate_level(level, plan_pattern=plan_pattern)

        if 'error' in result:
            print(f"❌ {level.upper()}: {result['error']}")
            total_invalid += 1
            continue

        plans = result['plans']

        valid_count = sum(1 for p in plans if p['valid'])
        invalid_count = len(plans) - valid_count
        total_plans += len(plans)
        total_invalid += invalid_count

        if invalid_count == 0:
            if not args.quiet:
                print(f"✅ {level.upper()}: {valid_count} plans valid")
        else:
            print(f"❌ {level.upper()}: {invalid_count}/{len(plans)} plans have errors")
            for plan in plans:
                if plan['errors']:
                    print(f"   • {plan['slug']}:")
                    for err in plan['errors']:
                        print(f"      - {err}")

    # Summary
    print(f"\n{'='*50}")
    if total_invalid == 0:
        print(f"✅ All {total_plans} plans valid")
        sys.exit(0)
    else:
        print(f"❌ {total_invalid} plans have errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
