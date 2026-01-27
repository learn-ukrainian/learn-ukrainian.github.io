#!/usr/bin/env python3
"""
Validate plan files against config.py before content generation.

IMPORTANT: Run this BEFORE generating content or building modules to catch
word_target mismatches early.

This script should be integrated into:
1. Pre-commit hooks
2. CI/CD pipelines
3. Module generation workflows

Usage:
    .venv/bin/python scripts/validate_plan_config.py                    # Validate all
    .venv/bin/python scripts/validate_plan_config.py c1-hist           # Validate level
    .venv/bin/python scripts/validate_plan_config.py c1-hist/shcho-*   # Validate specific plan

Exit codes:
    0 = All plans valid
    1 = Validation errors found
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from audit.config import get_word_target


# Tolerance for word_target mismatch (e.g., 5% variance allowed)
WORD_TARGET_TOLERANCE = 0.05


def get_config_target(level: str, sequence: int = 1, focus: str = None) -> int:
    """Get the authoritative word target from config.py."""
    # Map plan level names to LEVEL_CONFIG keys
    # Note: LEVEL_CONFIG uses 'C1-history' not 'C1-HIST'
    level_map = {
        'a1': 'A1', 'a2': 'A2', 'b1': 'B1', 'b2': 'B2',
        'c1': 'C1', 'c2': 'C2',
        'b2-hist': 'B2-history', 'c1-hist': 'C1-history',
        'c1-bio': 'C1-biography', 'lit': 'LIT',
    }
    level_code = level_map.get(level.lower(), level.upper())

    # For seminar tracks with specific config keys, get directly from LEVEL_CONFIG
    from audit.config import LEVEL_CONFIG
    if level_code in LEVEL_CONFIG:
        return LEVEL_CONFIG[level_code].get('target_words', 2000)

    return get_word_target(level_code, sequence, focus)


def validate_plan(plan_path: Path, level: str) -> list:
    """Validate a single plan file. Returns list of errors."""
    errors = []

    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = yaml.safe_load(f)
    except Exception as e:
        return [f"Failed to parse YAML: {e}"]

    if not plan:
        return ["Empty plan file"]

    # Get targets
    plan_target = plan.get('word_target', 0)
    sequence = plan.get('sequence', 1)
    focus = plan.get('focus')
    config_target = get_config_target(level, sequence, focus)

    # Check word_target matches config
    if plan_target == 0:
        errors.append(f"Missing word_target (config expects {config_target})")
    elif plan_target < config_target * (1 - WORD_TARGET_TOLERANCE):
        # Only flag if plan is UNDER config target (over is allowed - more content is fine)
        errors.append(f"word_target under config: plan={plan_target}, config={config_target}")

    # Check content_outline sums to word_target
    outline = plan.get('content_outline', [])
    if not outline:
        errors.append("Missing content_outline")
    else:
        outline_sum = sum(s.get('words', 0) for s in outline)
        if outline_sum == 0:
            errors.append("content_outline has no word budgets")
        elif abs(outline_sum - plan_target) > plan_target * WORD_TARGET_TOLERANCE:
            errors.append(f"content_outline sum ({outline_sum}) doesn't match word_target ({plan_target})")

    # Check required fields
    required_fields = ['module', 'level', 'title', 'objectives']
    for field in required_fields:
        if not plan.get(field):
            errors.append(f"Missing required field: {field}")

    return errors


def validate_level(level: str) -> dict:
    """Validate all plans for a level."""
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')

    if not plans_dir.exists():
        return {'level': level, 'error': f'Directory not found: {plans_dir}', 'plans': []}

    results = []
    for plan_path in sorted(plans_dir.glob('*.yaml')):
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
                        help='Level (e.g., c1-hist) or plan path pattern (e.g., c1-hist/shcho-*)')
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
        result = validate_level(level)

        if 'error' in result:
            print(f"❌ {level.upper()}: {result['error']}")
            total_invalid += 1
            continue

        # Filter by pattern if specified
        plans = result['plans']
        if plan_pattern:
            import fnmatch
            plans = [p for p in plans if fnmatch.fnmatch(p['slug'], plan_pattern)]

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
        print(f"\nRun: .venv/bin/python scripts/fix_plan_word_targets.py --fix")
        sys.exit(1)


if __name__ == '__main__':
    main()
