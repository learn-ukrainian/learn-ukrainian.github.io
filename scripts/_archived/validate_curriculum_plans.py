#!/usr/bin/env python3
"""
Comprehensive curriculum-plan alignment validation.

Checks:
1. All curriculum.yaml modules have corresponding plan files
2. No orphan plan files exist
3. Word targets are appropriate for level

Usage:
    .venv/bin/python scripts/validate_curriculum_plans.py [level]
"""

import sys
from pathlib import Path
import yaml
import re

# Expected word targets by level (min, max)
WORD_TARGET_RANGES = {
    'a1': (500, 1600),
    'a2': (600, 1800),
    'b1': (1000, 3500),
    'b2': (1500, 4000),
    'b2-hist': (3000, 6500),
    'c1': (2000, 5000),
    'c1-bio': (3000, 6000),
    'c1-hist': (3000, 6000),
    'c2': (2500, 6000),
    'lit': (3000, 7000),
}


def load_curriculum():
    """Load curriculum.yaml and return level->modules mapping."""
    curriculum_path = Path('curriculum/l2-uk-en/curriculum.yaml')
    with open(curriculum_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    result = {}
    for level_key, level_data in data.get('levels', {}).items():
        modules = level_data.get('modules', [])
        result[level_key] = modules
    return result


def extract_slug(filename: str) -> str:
    """Extract slug from filename, handling numeric prefixes."""
    stem = Path(filename).stem
    # Match patterns like "01-slug", "123-slug"
    match = re.match(r'^\d+-(.+)$', stem)
    if match:
        return match.group(1)
    return stem


def validate_level(level: str, expected_modules: list) -> dict:
    """Validate a single level's plans against curriculum."""
    plans_dir = Path(f'curriculum/l2-uk-en/plans/{level}')

    issues = {
        'missing_plans': [],
        'orphan_plans': [],
        'word_target_issues': [],
        'schema_issues': [],
    }

    if not plans_dir.exists():
        issues['missing_plans'] = [f"[{i}] {m}" for i, m in enumerate(expected_modules, 1)]
        return issues

    # Build mapping: slug -> (path, index)
    # For plan files
    plan_files = list(plans_dir.glob('*.yaml'))
    plan_slug_to_path = {}
    for p in plan_files:
        slug = extract_slug(p.name)
        plan_slug_to_path[slug] = p
        # Also keep the full stem for matching prefixed entries
        plan_slug_to_path[p.stem] = p

    # For expected modules - extract their slugs too
    expected_slugs = []
    for module in expected_modules:
        slug = extract_slug(module)
        expected_slugs.append(slug)

    expected_slug_set = set(expected_slugs)
    matched_plan_files = set()

    # Check for missing plans
    for i, module in enumerate(expected_modules, 1):
        slug = extract_slug(module)
        # Try to find by slug or by full module name
        if slug in plan_slug_to_path:
            matched_plan_files.add(plan_slug_to_path[slug])
        elif module in plan_slug_to_path:
            matched_plan_files.add(plan_slug_to_path[module])
        else:
            issues['missing_plans'].append(f"[{i}] {module}")

    # Check for orphan plans
    for p in plan_files:
        if p not in matched_plan_files:
            issues['orphan_plans'].append(p.stem)

    # Load and check each matched plan
    for p in matched_plan_files:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                plan = yaml.safe_load(f)
        except yaml.YAMLError:
            issues['schema_issues'].append(f"{p.stem}: YAML parse error")
            continue

        if not plan:
            issues['schema_issues'].append(f"{p.stem}: Empty plan")
            continue

        # Check word target
        word_target = plan.get('word_target', 0)
        if level in WORD_TARGET_RANGES and word_target:
            min_words, max_words = WORD_TARGET_RANGES[level]
            if word_target < min_words or word_target > max_words:
                issues['word_target_issues'].append(
                    f"{p.stem}: {word_target} words (expected {min_words}-{max_words})"
                )

    return issues


def main():
    curriculum = load_curriculum()

    # Determine which levels to check
    if len(sys.argv) > 1:
        levels = [sys.argv[1]]
    else:
        levels = list(curriculum.keys())

    print("=" * 70)
    print("CURRICULUM-PLAN ALIGNMENT VALIDATION")
    print("=" * 70)

    total_issues = 0

    for level in sorted(levels):
        if level not in curriculum:
            print(f"\n[!] Level {level} not in curriculum.yaml")
            continue

        expected = curriculum[level]
        print(f"\n--- {level.upper()} ({len(expected)} modules expected) ---")

        issues = validate_level(level, expected)
        level_issues = len(issues['missing_plans']) + len(issues['orphan_plans'])

        if issues['missing_plans']:
            print(f"\n  MISSING PLANS ({len(issues['missing_plans'])}):")
            for m in issues['missing_plans'][:10]:
                print(f"    - {m}")
            if len(issues['missing_plans']) > 10:
                print(f"    ... and {len(issues['missing_plans']) - 10} more")

        if issues['orphan_plans']:
            print(f"\n  ORPHAN PLANS ({len(issues['orphan_plans'])}):")
            for m in issues['orphan_plans'][:10]:
                print(f"    - {m}")
            if len(issues['orphan_plans']) > 10:
                print(f"    ... and {len(issues['orphan_plans']) - 10} more")

        if issues['word_target_issues']:
            print(f"\n  WORD TARGET OUT OF RANGE ({len(issues['word_target_issues'])}):")
            for e in issues['word_target_issues'][:5]:
                print(f"    - {e}")
            if len(issues['word_target_issues']) > 5:
                print(f"    ... and {len(issues['word_target_issues']) - 5} more")

        if level_issues == 0 and not issues['word_target_issues']:
            print(f"  All OK")
        elif level_issues == 0:
            print(f"  Plans aligned (word targets may need adjustment)")

        total_issues += level_issues

    print("\n" + "=" * 70)
    if total_issues > 0:
        print(f"[!] {total_issues} missing/orphan issues. Fix before proceeding.")
        sys.exit(1)
    else:
        print("[OK] All curriculum-plan alignments valid.")
        sys.exit(0)


if __name__ == '__main__':
    main()
