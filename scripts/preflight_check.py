#!/usr/bin/env python3
"""
Pre-flight check for module building.

Validates alignment between plan, meta, and stub files BEFORE content generation.
Catches issues early to prevent wasted work.

Usage:
    .venv/bin/python scripts/preflight_check.py curriculum/l2-uk-en/b2-hist/krym-1954.md
    .venv/bin/python scripts/preflight_check.py b2-hist 112
"""

import sys
import yaml
from pathlib import Path
from typing import Optional


def load_yaml(path: Path) -> Optional[dict]:
    """Load YAML file, return None if missing."""
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def check_module(md_path: Path) -> tuple[bool, list[str]]:
    """
    Run pre-flight checks on a module.

    Returns (passed, issues) tuple.
    """
    issues = []

    # Derive paths
    level_dir = md_path.parent
    level = level_dir.name
    slug = md_path.stem
    # Handle numbered prefix (e.g., 112-krym-1954.md -> krym-1954)
    if '-' in slug and slug.split('-')[0].isdigit():
        slug = '-'.join(slug.split('-')[1:])

    base = level_dir.parent  # curriculum/l2-uk-en

    plan_path = base / "plans" / level / f"{slug}.yaml"
    meta_path = level_dir / "meta" / f"{slug}.yaml"
    activities_path = level_dir / "activities" / f"{slug}.yaml"
    vocab_path = level_dir / "vocabulary" / f"{slug}.yaml"

    # 1. Check plan exists
    plan = load_yaml(plan_path)
    if plan is None:
        issues.append(f"❌ MISSING: Plan file not found: {plan_path}")
        return False, issues

    # 2. Check meta exists
    meta = load_yaml(meta_path)
    if meta is None:
        issues.append(f"❌ MISSING: Meta file not found: {meta_path}")
        return False, issues

    # 3. Check plan has required fields
    required_plan_fields = ['module_number', 'title', 'objectives', 'vocabulary_hints']
    for field in required_plan_fields:
        if field not in plan:
            issues.append(f"⚠️ PLAN: Missing required field '{field}'")

    # 4. Check meta has required fields
    required_meta_fields = ['module', 'pedagogy']
    for field in required_meta_fields:
        if field not in meta:
            issues.append(f"⚠️ META: Missing required field '{field}'")

    # 5. Check module numbers match
    plan_num = plan.get('module_number')
    meta_num = meta.get('module')
    if plan_num and meta_num and plan_num != meta_num:
        issues.append(f"❌ MISMATCH: Plan module_number ({plan_num}) != meta module ({meta_num})")

    # 6. Check word_target exists
    word_target = plan.get('word_target') or meta.get('word_target')
    if not word_target:
        issues.append("⚠️ TARGET: No word_target in plan or meta")

    # 7. Check content_outline exists (for guidance)
    if 'content_outline' not in plan:
        issues.append("ℹ️ PLAN: No content_outline (section guidance unavailable)")

    # 8. Check vocabulary_hints exist
    vocab_hints = plan.get('vocabulary_hints', [])
    if not vocab_hints:
        issues.append("⚠️ PLAN: No vocabulary_hints")
    elif len(vocab_hints) < 10:
        issues.append(f"ℹ️ PLAN: Only {len(vocab_hints)} vocabulary hints (consider more)")

    # 9. Check activity_hints exist
    activity_hints = plan.get('activity_hints', [])
    if not activity_hints:
        issues.append("ℹ️ PLAN: No activity_hints (will need to determine activity types)")

    # 10. Check for existing artifacts (info only)
    if activities_path.exists():
        activities = load_yaml(activities_path)
        if activities:
            issues.append(f"ℹ️ EXISTS: Activities file exists with {len(activities)} activities")

    if vocab_path.exists():
        vocab = load_yaml(vocab_path)
        if vocab and 'items' in vocab:
            issues.append(f"ℹ️ EXISTS: Vocabulary file exists with {len(vocab['items'])} items")

    # 11. Check .md stub exists and has frontmatter
    if md_path.exists():
        content = md_path.read_text()
        if content.startswith('---'):
            # Has frontmatter
            try:
                _, fm, _ = content.split('---', 2)
                frontmatter = yaml.safe_load(fm)
                if frontmatter:
                    issues.append("ℹ️ EXISTS: MD file has frontmatter")
            except:
                issues.append("⚠️ MD: Frontmatter parsing error")
        else:
            issues.append("⚠️ MD: No frontmatter in stub")
    else:
        issues.append("ℹ️ MD: Content file doesn't exist yet (will be created)")

    # Determine pass/fail
    has_blockers = any(issue.startswith("❌") for issue in issues)

    return not has_blockers, issues


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/preflight_check.py <md_path>")
        print("       .venv/bin/python scripts/preflight_check.py <level> <module_num>")
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) == 3:
        # level + module_num format
        level = sys.argv[1]
        module_num = sys.argv[2]
        # Find the module
        level_dir = Path(f"curriculum/l2-uk-en/{level}")
        if not level_dir.exists():
            print(f"❌ Level directory not found: {level_dir}")
            sys.exit(1)

        # Find MD file with this module number
        candidates = list(level_dir.glob(f"{module_num}-*.md")) + list(level_dir.glob(f"*-{module_num}.md"))
        if not candidates:
            # Try without prefix
            candidates = list(level_dir.glob("*.md"))
            candidates = [c for c in candidates if module_num in c.stem]

        if not candidates:
            print(f"❌ No module found for {level} #{module_num}")
            sys.exit(1)

        md_path = candidates[0]
    else:
        md_path = Path(sys.argv[1])

    if not md_path.suffix == '.md':
        print(f"❌ Expected .md file, got: {md_path}")
        sys.exit(1)

    print(f"🔍 Pre-flight check: {md_path.name}")
    print("=" * 50)

    passed, issues = check_module(md_path)

    for issue in issues:
        print(issue)

    print("=" * 50)
    if passed:
        print("✅ PRE-FLIGHT PASSED - Ready to build")
        sys.exit(0)
    else:
        print("❌ PRE-FLIGHT FAILED - Fix blockers first")
        sys.exit(1)


if __name__ == "__main__":
    main()
