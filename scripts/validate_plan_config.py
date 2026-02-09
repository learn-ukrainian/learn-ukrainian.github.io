#!/usr/bin/env python3
"""
Validate plan files against config.py before content generation.
"""

import argparse
import sys
from pathlib import Path
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
try:
    from audit.config import get_word_target, LEVEL_CONFIG
except ImportError:
    # Fallback for environments where audit is not in path
    LEVEL_CONFIG = {}
    def get_word_target(level, sequence, focus): return 2000

# Tolerance for word_target mismatch
WORD_TARGET_TOLERANCE = 0.20 # Relaxed to 20%

def get_config_target(level: str, sequence: int = 1, focus: str = None) -> int:
    """Get the authoritative word target from config.py."""
    level_map = {
        'a1': 'A1', 'a2': 'A2', 'b1': 'B1', 'b2': 'B2',
        'c1': 'C1', 'c2': 'C2',
        'b2-hist': 'B2-history', 'c1-hist': 'C1-history',
        'c1-bio': 'C1-biography', 'lit': 'LIT',
        'oes': 'OES', 'ruth': 'RUTH'
    }
    level_code = level_map.get(level.lower(), level.upper())

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

    if not plan: return ["Empty plan file"]

    # Experimental tracks (OES, RUTH) have relaxed validation for draft data
    is_experimental = level.lower() in ('oes', 'ruth') or 'oes' in str(plan_path).lower() or 'ruth' in str(plan_path).lower()

    plan_target = plan.get('word_target', plan.get('word_budget', 0))
    sequence = plan.get('sequence', plan.get('module_number', 1))
    focus = plan.get('focus')
    config_target = get_config_target(level, sequence, focus)

    # Word target validation
    if not is_experimental:
        if plan_target == 0:
            errors.append(f"Missing word_target (config expects {config_target})")
        elif plan_target < config_target * (1 - WORD_TARGET_TOLERANCE):
            errors.append(f"word_target too low: plan={plan_target}, config={config_target}")

    # Outline validation
    outline = plan.get('content_outline', [])
    if not outline and not is_experimental:
        errors.append("Missing content_outline")
    elif outline:
        outline_sum = sum(s.get('words', 0) for s in outline)
        if outline_sum == 0 and not is_experimental:
            errors.append("content_outline has no word budgets")
        elif plan_target > 0 and abs(outline_sum - plan_target) > plan_target * WORD_TARGET_TOLERANCE:
            if not is_experimental:
                errors.append(f"Outline sum ({outline_sum}) deviates from target ({plan_target})")

    # Field validation
    required = [
        ('module', ['module_number', 'module']),
        ('title', ['title_uk', 'title_en', 'title']),
    ]
    if not is_experimental:
        required.extend([
            ('level', []),
            ('objectives', ['learning_outcomes', 'objectives'])
        ])

    for field, aliases in required:
        val = plan.get(field)
        if not val:
            for alias in aliases:
                val = plan.get(alias)
                if val: break
        if not val:
            errors.append(f"Missing required field: {field}")

    return errors

def validate_level(level: str) -> dict:
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')
    if not plans_dir.exists():
        return {'level': level, 'error': f'Not found: {plans_dir}', 'plans': []}

    results = []
    for plan_path in sorted(plans_dir.glob('*.yaml')):
        errors = validate_plan(plan_path, level)
        results.append({
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
    parser = argparse.ArgumentParser()
    parser.add_argument('target', nargs='?')
    args = parser.parse_args()

    if args.target:
        levels = [args.target]
    else:
        plans_base = Path('curriculum/l2-uk-en/plans')
        levels = [d.name for d in sorted(plans_base.iterdir()) if d.is_dir() and not d.name.startswith('.')]

    total_invalid = 0
    total_plans = 0

    for level in levels:
        result = validate_level(level)
        if 'error' in result: continue

        total_plans += result['total']
        total_invalid += result['invalid']

        if result['invalid'] > 0:
            print(f"❌ {level.upper()}: {result['invalid']}/{result['total']} plans have errors")
            for plan in result['plans']:
                if plan['errors']:
                    print(f"   • {plan['slug']}: {', '.join(plan['errors'])}")
        else:
            print(f"✅ {level.upper()}: {result['total']} plans valid")

    if total_invalid == 0:
        print(f"\n✅ All {total_plans} plans valid")
        sys.exit(0)
    else:
        print(f"\n❌ {total_invalid} plans have errors")
        sys.exit(1)

if __name__ == '__main__':
    main()
