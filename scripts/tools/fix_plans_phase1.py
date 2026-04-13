#!/usr/bin/env python3
"""Phase 1: Deterministic plan fixes — add missing Summary sections.

Adds a 'Підсумок — Summary' section to content_outline for plans that lack it.
Bumps plan version (patch increment). Does NOT generate content — just the slot.

Word_target fixes: NOT NEEDED. The validator was wrong — checkpoint/practice/review
plans correctly use subtype targets (A1-checkpoint=1000, A2-checkpoint=1500, etc.).
The real fix is in the validator, not the plans.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def _bump_version(version: str) -> str:
    """Bump patch version: '3.0' → '3.0.1', '3.0.1' → '3.0.2'."""
    parts = str(version).split(".")
    if len(parts) <= 2:
        return f"{version}.1"
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def _has_summary(outline: list[dict]) -> bool:
    """Check if content_outline has a Summary/Підсумок section."""
    for section in outline:
        if not isinstance(section, dict):
            continue
        name = section.get("section", "")
        if "Summary" in name or "Підсумок" in name or "підсумок" in name:
            return True
    return False


def _get_summary_budget(level: str) -> int:
    """Word budget for Summary section by level."""
    budgets = {"a1": 150, "a2": 200, "b1": 300, "b2": 300, "c1": 300, "c2": 300}
    return budgets.get(level.lower(), 200)


def fix_plan(plan_path: Path, level: str, dry_run: bool = False) -> str | None:
    """Add Summary section to a plan if missing. Returns change description or None."""
    text = plan_path.read_text("utf-8")
    plan = yaml.safe_load(text)
    if not plan:
        return None

    outline = plan.get("content_outline", [])
    if not outline or _has_summary(outline):
        return None

    # Add Summary section at the end of content_outline
    budget = _get_summary_budget(level)
    summary_section = {
        "section": "Підсумок — Summary",
        "words": budget,
        "points": [
            "Review key concepts from this module",
            "Self-check questions for the learner",
        ],
    }
    outline.append(summary_section)

    # Bump version
    old_version = str(plan.get("version", "3.0"))
    new_version = _bump_version(old_version)
    plan["version"] = new_version

    if dry_run:
        return f"Would add Summary ({budget}w), version {old_version} → {new_version}"

    # Write back preserving structure
    plan_path.write_text(
        yaml.dump(plan, allow_unicode=True, sort_keys=False, width=120),
        "utf-8",
    )
    return f"Added Summary ({budget}w), version {old_version} → {new_version}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    levels = args if args else ["a1", "a2", "b1", "b2", "c1", "c2"]

    total_fixed = 0
    for level in levels:
        plans_dir = Path(f"curriculum/l2-uk-en/plans/{level}")
        if not plans_dir.exists():
            continue
        fixed = 0
        for plan_path in sorted(plans_dir.glob("*.yaml")):
            result = fix_plan(plan_path, level, dry_run=dry_run)
            if result:
                print(f"  {level}/{plan_path.stem}: {result}")
                fixed += 1
        print(f"{level.upper()}: {fixed} plans {'would be ' if dry_run else ''}fixed")
        total_fixed += fixed

    print(f"\nTotal: {total_fixed} plans {'would be ' if dry_run else ''}fixed")
    mode = "DRY RUN" if dry_run else "APPLIED"
    print(f"Mode: {mode}")


if __name__ == "__main__":
    main()
