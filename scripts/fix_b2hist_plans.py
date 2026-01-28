#!/usr/bin/env python3
"""Fix B2-HIST plan file issues identified in comprehensive audit."""

import yaml
from pathlib import Path

PLANS_DIR = Path("curriculum/l2-uk-en/plans/b2-hist")
CURRICULUM_FILE = Path("curriculum/l2-uk-en/curriculum.yaml")

# Load curriculum to get correct order
with open(CURRICULUM_FILE) as f:
    curriculum = yaml.safe_load(f)

b2hist_modules = curriculum["levels"]["b2-hist"]["modules"]
slug_to_position = {slug: i + 1 for i, slug in enumerate(b2hist_modules)}

# Files missing pedagogy
MISSING_PEDAGOGY = [
    "afhanistan",
    "chornobyl",
    "mykhailo-chernigivskyi",
    "shistdesiatnyky",
    "syntez-dvokniazivstvo"
]

def fix_plan_file(plan_path: Path):
    """Fix issues in a single plan file."""
    with open(plan_path) as f:
        content = f.read()
        plan = yaml.safe_load(content)

    if not plan:
        print(f"  SKIP: Empty file {plan_path.name}")
        return False

    slug = plan_path.stem
    changes = []

    # 1. Fix module field to use slug format
    if plan.get("module") != slug:
        old_module = plan.get("module", "MISSING")
        plan["module"] = slug
        changes.append(f"module: {old_module} → {slug}")

    # 2. Ensure slug field exists
    if plan.get("slug") != slug:
        plan["slug"] = slug
        changes.append(f"slug: added/fixed → {slug}")

    # 3. Ensure level field
    if plan.get("level") != "B2-HIST":
        plan["level"] = "B2-HIST"
        changes.append("level: → B2-HIST")

    # 4. Ensure version field
    if plan.get("version") != "2.0":
        plan["version"] = "2.0"
        changes.append("version: → 2.0")

    # 5. Add pedagogy if missing
    if slug.replace("-", "") in [p.replace("-", "") for p in MISSING_PEDAGOGY]:
        if "pedagogy" not in plan:
            plan["pedagogy"] = "CBI"
            changes.append("pedagogy: added CBI")

    # 6. Add focus if missing
    if "focus" not in plan:
        plan["focus"] = "history"
        changes.append("focus: added history")

    if changes:
        # Reorder keys for consistency
        ordered = {}
        key_order = ["module", "level", "slug", "version", "title", "subtitle",
                     "content_outline", "word_target", "vocabulary_hints",
                     "activity_hints", "focus", "pedagogy", "prerequisites",
                     "connects_to", "objectives", "grammar", "sources",
                     "register", "phase"]

        for key in key_order:
            if key in plan:
                ordered[key] = plan[key]

        # Add any remaining keys not in order
        for key in plan:
            if key not in ordered:
                ordered[key] = plan[key]

        with open(plan_path, 'w') as f:
            yaml.dump(ordered, f, allow_unicode=True, default_flow_style=False,
                     sort_keys=False, width=1000)

        print(f"  FIXED {plan_path.name}: {', '.join(changes)}")
        return True

    return False

def main():
    print("=" * 60)
    print("B2-HIST Plan File Fixer")
    print("=" * 60)

    plan_files = sorted(PLANS_DIR.glob("*.yaml"))
    print(f"\nFound {len(plan_files)} plan files\n")

    fixed_count = 0
    for plan_path in plan_files:
        if fix_plan_file(plan_path):
            fixed_count += 1

    print(f"\n{'=' * 60}")
    print(f"Fixed {fixed_count} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
