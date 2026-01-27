#!/usr/bin/env python3
"""
Sync content_outline in plan files from actual markdown section structure.

Reads the markdown file, extracts H2 sections and their word counts,
and updates the plan file's content_outline to match reality.

Usage:
    .venv/bin/python scripts/sync_outline_from_markdown.py b1 72-80
    .venv/bin/python scripts/sync_outline_from_markdown.py b1 72
    .venv/bin/python scripts/sync_outline_from_markdown.py --dry-run b1 72-80
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audit.checks.outline_compliance import extract_markdown_sections


def find_markdown_file(level: str, module_num: int) -> Path | None:
    """Find markdown file for a module number."""
    base_dir = Path(__file__).parent.parent / "curriculum" / "l2-uk-en" / level

    # Look for files matching pattern {num}-*.md
    pattern = f"{module_num:02d}-*.md"
    matches = list(base_dir.glob(pattern))

    if not matches:
        # Try single digit
        pattern = f"{module_num}-*.md"
        matches = list(base_dir.glob(pattern))

    return matches[0] if matches else None


def find_plan_file(level: str, slug: str) -> Path | None:
    """Find plan file for a module slug."""
    plan_dir = Path(__file__).parent.parent / "curriculum" / "l2-uk-en" / "plans" / level

    # Remove leading number from slug
    import re
    clean_slug = re.sub(r"^\d+-", "", slug)

    plan_path = plan_dir / f"{clean_slug}.yaml"
    if plan_path.exists():
        return plan_path

    # Try with number prefix
    plan_path = plan_dir / f"{slug}.yaml"
    return plan_path if plan_path.exists() else None


def sync_outline(md_path: Path, plan_path: Path, dry_run: bool = False) -> dict:
    """
    Sync content_outline from markdown to plan file.

    Returns dict with:
        - success: bool
        - message: str
        - old_outline: list | None
        - new_outline: list
    """
    # Extract sections from markdown
    sections = extract_markdown_sections(md_path)

    if not sections:
        return {
            "success": False,
            "message": "No sections found in markdown",
            "old_outline": None,
            "new_outline": [],
        }

    # Build new content_outline
    new_outline = []
    total_words = 0

    for section_name, section_data in sections.items():
        words = section_data["words"]
        new_outline.append({
            "section": section_name,
            "words": words,
        })
        total_words += words

    # Load existing plan
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = yaml.safe_load(f)

    old_outline = plan_data.get("content_outline")
    old_target = plan_data.get("word_target")

    # Update plan
    plan_data["content_outline"] = new_outline
    plan_data["word_target"] = total_words

    if not dry_run:
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(plan_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {
        "success": True,
        "message": f"Updated outline: {len(new_outline)} sections, {total_words} words (was {old_target})",
        "old_outline": old_outline,
        "new_outline": new_outline,
        "word_target": total_words,
    }


def main():
    parser = argparse.ArgumentParser(description="Sync content_outline from markdown to plan files")
    parser.add_argument("level", help="Level (e.g., b1, b2-hist)")
    parser.add_argument("modules", help="Module number(s) (e.g., 72, 72-80)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")

    args = parser.parse_args()

    # Parse module range
    if "-" in args.modules:
        start, end = map(int, args.modules.split("-"))
        module_nums = range(start, end + 1)
    else:
        module_nums = [int(args.modules)]

    print(f"\n{'DRY RUN - ' if args.dry_run else ''}Syncing outlines for {args.level} modules {args.modules}\n")

    success_count = 0
    error_count = 0

    for num in module_nums:
        # Find markdown file
        md_path = find_markdown_file(args.level, num)
        if not md_path:
            print(f"  ❌ M{num}: No markdown file found")
            error_count += 1
            continue

        slug = md_path.stem

        # Find plan file
        plan_path = find_plan_file(args.level, slug)
        if not plan_path:
            print(f"  ❌ M{num} ({slug}): No plan file found")
            error_count += 1
            continue

        # Sync outline
        result = sync_outline(md_path, plan_path, dry_run=args.dry_run)

        if result["success"]:
            print(f"  ✅ M{num} ({slug}): {result['message']}")
            success_count += 1
        else:
            print(f"  ❌ M{num} ({slug}): {result['message']}")
            error_count += 1

    print(f"\n{'DRY RUN - ' if args.dry_run else ''}Done: {success_count} synced, {error_count} errors\n")


if __name__ == "__main__":
    main()
