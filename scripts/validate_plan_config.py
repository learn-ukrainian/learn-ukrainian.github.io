#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from audit.config import get_word_target

WORD_TARGET_TOLERANCE = 0.05

def get_config_target(level: str, sequence: int = 1, focus: str = None) -> int:
    level_map = {
        'a1': 'A1', 'a2': 'A2', 'b1': 'B1', 'b2': 'B2',
        'c1': 'C1', 'c2': 'C2',
        'b2-hist': 'B2-history', 'c1-hist': 'C1-history',
        'c1-bio': 'C1-biography', 'lit': 'LIT',
    }
    level_code = level_map.get(level.lower(), level.upper())
    from audit.config import LEVEL_CONFIG
    if level_code in LEVEL_CONFIG:
        return LEVEL_CONFIG[level_code].get('target_words', 2000)
    return get_word_target(level_code, sequence, focus)

def validate_plan(plan_path: Path, level: str) -> list:
    errors = []
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = yaml.safe_load(f)
    except Exception as e: return [f"Failed to parse YAML: {e}"]
    if not plan: return ["Empty plan file"]

    plan_target = plan.get('word_target', 0)
    sequence = plan.get('sequence', 1)
    focus = plan.get('focus')
    config_target = get_config_target(level, sequence, focus)

    if plan_target == 0:
        errors.append(f"Missing word_target (config expects {config_target})")
    elif plan_target < config_target * (1 - WORD_TARGET_TOLERANCE):
        errors.append(f"word_target under config: plan={plan_target}, config={config_target}")

    outline = plan.get('content_outline', [])
    if not outline:
        errors.append("Missing content_outline")
    else:
        outline_sum = sum(s.get('words', 0) for s in outline)
        if outline_sum == 0 and level.lower() not in ['oes', 'ruth']:
            errors.append("content_outline has no word budgets")
        elif abs(outline_sum - plan_target) > plan_target * WORD_TARGET_TOLERANCE and level.lower() not in ['oes', 'ruth']:
            errors.append(f"content_outline sum ({outline_sum}) doesn't match word_target ({plan_target})")

    required_fields = ['module', 'level', 'title', 'objectives']
    aliases = {'module': ['module_number'], 'title': ['title_uk']}
    for field in required_fields:
        value = plan.get(field)
        if not value:
            for alias in aliases.get(field, []):
                value = plan.get(alias);
                if value: break
        if not value and level.lower() not in ['oes', 'ruth']:
            errors.append(f"Missing required field: {field}")
    return errors

def validate_level(level: str) -> dict:
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')
    if not plans_dir.exists(): return {'level': level, 'error': 'Not found', 'plans': []}
    results = []
    for plan_path in sorted(plans_dir.glob('*.yaml')):
        errors = validate_plan(plan_path, level)
        results.append({'path': plan_path, 'slug': plan_path.stem, 'errors': errors, 'valid': len(errors) == 0})
    return {'level': level, 'total': len(results), 'valid': sum(1 for r in results if r['valid']), 'invalid': sum(1 for r in results if not r['valid']), 'plans': results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', nargs='?')
    args = parser.parse_args()
    if args.target: levels = [args.target]
    else:
        plans_base = Path('curriculum/l2-uk-en/plans')
        levels = [d.name for d in sorted(plans_base.iterdir()) if d.is_dir() and not d.name.startswith('.')]

    total_invalid = 0
    for level in levels:
        result = validate_level(level)
        if result.get('error'): continue
        if result['invalid'] > 0:
            print(f"❌ {level.upper()}: {result['invalid']} errors")
            for p in result['plans']:
                if p['errors']: print(f"  {p['slug']}: {p['errors']}")
            total_invalid += result['invalid']
        else: print(f"✅ {level.upper()}: valid")
    sys.exit(1 if total_invalid > 0 else 0)

if __name__ == '__main__': main()
