#!/usr/bin/env python3
"""Generate placeholder MDX stubs for all planned modules without existing MDX files.

Ensures the Starlight sidebar shows all planned modules. Modules with existing
content are untouched. Missing modules get a "coming soon" placeholder.

Usage:
    .venv/bin/python scripts/generate_mdx_stubs.py
    .venv/bin/python scripts/generate_mdx_stubs.py --dry-run
"""

import argparse
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from manifest_utils import load_manifest, CURRICULUM_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARLIGHT_DOCS = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"
PLANS_DIR = CURRICULUM_PATH / "plans"

ALL_LEVELS = [
    "a1", "a2", "b1", "b2", "c1", "c2",
    "hist", "bio", "istorio", "lit", "oes", "ruth",
    "b2-pro", "c1-pro",
]

STUB_TEMPLATE = """\
---
title: "{title}"
description: "{description}"
sidebar:
  order: {order}
  label: "{label}"
---

> 🚧 **Цей модуль ще в розробці.** / **This module is under development.**
"""


def get_plan_title(level: str, slug: str) -> tuple[str, str]:
    """Extract title and subtitle from plan YAML."""
    plan_path = PLANS_DIR / level / f"{slug}.yaml"
    if not plan_path.exists():
        # Fallback: humanize slug
        title = slug.replace("-", " ").title()
        return title, ""

    with open(plan_path) as f:
        plan = yaml.safe_load(f)

    if not plan:
        title = slug.replace("-", " ").title()
        return title, ""

    title = plan.get("title", slug.replace("-", " ").title())
    subtitle = plan.get("subtitle", "")
    return title, subtitle


def get_ordered_slugs(level: str) -> list[str]:
    """Get ordered list of slugs from curriculum.yaml manifest."""
    manifest = load_manifest()
    levels = manifest.get("levels", {})
    level_data = levels.get(level, {})
    modules = level_data.get("modules", [])

    # Strip numeric prefixes (e.g., "01-the-cyrillic-code-i" → "the-cyrillic-code-i")
    slugs = []
    for m in modules:
        if isinstance(m, str):
            # Strip leading NN- prefix
            parts = m.split("-", 1)
            if parts[0].isdigit() and len(parts) > 1:
                slugs.append(parts[1])
            else:
                slugs.append(m)
    return slugs


def generate_stubs(dry_run: bool = False) -> dict[str, int]:
    """Generate MDX stubs for all missing modules. Returns counts per level."""
    counts = {}

    for level in ALL_LEVELS:
        level_dir = STARLIGHT_DOCS / level
        level_dir.mkdir(parents=True, exist_ok=True)

        slugs = get_ordered_slugs(level)
        if not slugs:
            # Fallback: read from plans directory
            plan_dir = PLANS_DIR / level
            if plan_dir.exists():
                slugs = sorted(p.stem for p in plan_dir.glob("*.yaml"))

        created = 0
        for i, slug in enumerate(slugs, 1):
            mdx_path = level_dir / f"{slug}.mdx"
            if mdx_path.exists():
                continue

            title, subtitle = get_plan_title(level, slug)
            # Escape quotes for YAML frontmatter
            safe_title = title.replace('"', '\\"')
            safe_subtitle = subtitle.replace('"', '\\"') if subtitle else ""
            label = f"{i:02d}. {title}"
            safe_label = label.replace('"', '\\"')

            content = STUB_TEMPLATE.format(
                title=safe_title,
                description=safe_subtitle,
                order=i,
                label=safe_label,
            )

            if dry_run:
                print(f"  STUB: {level}/{slug}.mdx ({title})")
            else:
                mdx_path.write_text(content)

            created += 1

        if created > 0:
            counts[level] = created

    return counts


def main():
    parser = argparse.ArgumentParser(description="Generate MDX stubs for missing modules")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    print("Generating MDX stubs for missing modules...")
    if args.dry_run:
        print("(DRY RUN — no files will be created)\n")

    counts = generate_stubs(dry_run=args.dry_run)

    total = sum(counts.values())
    if total == 0:
        print("\nAll modules have MDX files. Nothing to do.")
    else:
        print(f"\n{'Would create' if args.dry_run else 'Created'} {total} stubs:")
        for level, count in sorted(counts.items()):
            print(f"  {level}: {count}")

    print("\nDone!")


if __name__ == "__main__":
    main()
