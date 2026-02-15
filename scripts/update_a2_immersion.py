#!/usr/bin/env python3
"""
Update A2 plan files with graduated immersion bands.

Reads curriculum.yaml for A2 module order, maps position to immersion band:
  - Positions  0-19 (M01-20, Core grammar)    → 50-60% Ukrainian
  - Positions 20-49 (M21-50, Applied grammar)  → 60-75% Ukrainian
  - Positions 50-69 (M51-70, Consolidation)    → 75-90% Ukrainian

Optional: --include-b1-bridge updates B1 M01-05 to 70-85% Ukrainian.

Usage:
  .venv/bin/python scripts/update_a2_immersion.py --dry-run
  .venv/bin/python scripts/update_a2_immersion.py --fix
  .venv/bin/python scripts/update_a2_immersion.py --fix --include-b1-bridge
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
PLANS_A2 = ROOT / "curriculum" / "l2-uk-en" / "plans" / "a2"
PLANS_B1 = ROOT / "curriculum" / "l2-uk-en" / "plans" / "b1"

# Band definitions: (start_pos, end_pos, immersion_value)
A2_BANDS = [
    (0, 19, "50-60% Ukrainian"),
    (20, 49, "60-75% Ukrainian"),
    (50, 69, "75-90% Ukrainian"),
]

B1_BRIDGE_IMMERSION = "70-85% Ukrainian"
B1_BRIDGE_COUNT = 5  # M01-05


def get_immersion_band(position: int) -> str:
    """Map a 0-indexed position to its immersion band value."""
    for start, end, value in A2_BANDS:
        if start <= position <= end:
            return value
    raise ValueError(f"Position {position} out of range for A2 bands")


def load_curriculum_modules(level: str) -> list[str]:
    """Load ordered module slugs from curriculum.yaml."""
    with open(CURRICULUM) as f:
        data = yaml.safe_load(f)
    return data["levels"][level]["modules"]


def update_plan_immersion(plan_path: Path, new_immersion: str, dry_run: bool) -> tuple[str, str]:
    """Update the immersion field in a plan file. Returns (old_value, new_value)."""
    text = plan_path.read_text()

    # Find existing immersion line
    match = re.search(r"^immersion:\s*(.+)$", text, re.MULTILINE)
    if match:
        old_value = match.group(1).strip()
        if old_value == new_immersion:
            return old_value, new_immersion  # No change needed

        if not dry_run:
            new_text = text[: match.start()] + f"immersion: {new_immersion}" + text[match.end() :]
            plan_path.write_text(new_text)
        return old_value, new_immersion
    else:
        # No immersion field — append before phase: line or at end
        phase_match = re.search(r"^phase:", text, re.MULTILINE)
        if phase_match:
            insert_pos = phase_match.start()
            new_line = f"immersion: {new_immersion}\n"
        else:
            insert_pos = len(text)
            new_line = f"\nimmersion: {new_immersion}\n"

        if not dry_run:
            new_text = text[:insert_pos] + new_line + text[insert_pos:]
            plan_path.write_text(new_text)
        return "(missing)", new_immersion


def main():
    parser = argparse.ArgumentParser(description="Update A2 immersion bands in plan files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    group.add_argument("--fix", action="store_true", help="Apply changes to plan files")
    parser.add_argument(
        "--include-b1-bridge",
        action="store_true",
        help="Also update B1 M01-05 bridge modules to 70-85%%",
    )
    args = parser.parse_args()

    dry_run = args.dry_run
    mode = "DRY RUN" if dry_run else "APPLYING"
    print(f"=== A2 Graduated Immersion Update ({mode}) ===\n")

    # --- A2 modules ---
    a2_modules = load_curriculum_modules("a2")
    print(f"A2 modules in curriculum.yaml: {len(a2_modules)}")

    band_counts = {band[2]: 0 for band in A2_BANDS}
    changes = 0
    missing_plans = 0

    for pos, slug in enumerate(a2_modules):
        plan_path = PLANS_A2 / f"{slug}.yaml"
        if not plan_path.exists():
            print(f"  MISSING: {plan_path.name}")
            missing_plans += 1
            continue

        new_immersion = get_immersion_band(pos)
        old_val, new_val = update_plan_immersion(plan_path, new_immersion, dry_run)
        band_counts[new_immersion] = band_counts.get(new_immersion, 0) + 1

        if old_val != new_val:
            changes += 1
            print(f"  M{pos+1:02d} {slug}: {old_val} → {new_val}")
        elif old_val == "(missing)":
            changes += 1
            print(f"  M{pos+1:02d} {slug}: (added) {new_val}")

    print(f"\nA2 Summary:")
    print(f"  Total modules: {len(a2_modules)}")
    print(f"  Missing plans: {missing_plans}")
    print(f"  Changes: {changes}")
    print(f"  Band distribution:")
    for band_label, count in band_counts.items():
        print(f"    {band_label}: {count}")

    # --- B1 bridge modules ---
    if args.include_b1_bridge:
        print(f"\n=== B1 Bridge Modules (M01-05) ({mode}) ===\n")
        b1_modules = load_curriculum_modules("b1")
        b1_changes = 0

        for pos in range(min(B1_BRIDGE_COUNT, len(b1_modules))):
            slug = b1_modules[pos]
            plan_path = PLANS_B1 / f"{slug}.yaml"
            if not plan_path.exists():
                print(f"  MISSING: {plan_path.name}")
                continue

            old_val, new_val = update_plan_immersion(plan_path, B1_BRIDGE_IMMERSION, dry_run)
            if old_val != new_val:
                b1_changes += 1
                print(f"  B1-M{pos+1:02d} {slug}: {old_val} → {new_val}")

        print(f"\nB1 Bridge Summary: {b1_changes} changes")

    # --- Final ---
    if dry_run:
        print(f"\n{'='*50}")
        print("DRY RUN complete. Run with --fix to apply changes.")
    else:
        print(f"\n{'='*50}")
        print("Changes applied successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
