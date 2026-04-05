#!/usr/bin/env python3
"""Update seminar plan activity_hints to use track-specific profiles.

Reads activity profiles from v4-seminar-section-templates.yaml and generates
proper inline + workbook activity_hints for each plan, replacing the generic
quiz/fill-in/essay pattern from the v3→v4 conversion.

Usage:
    # Dry run (show what would change):
    .venv/bin/python scripts/tools/update_plan_activities.py --dry-run

    # Update all seminar plans:
    .venv/bin/python scripts/tools/update_plan_activities.py

    # Update one track:
    .venv/bin/python scripts/tools/update_plan_activities.py --track folk

Issue: #1148
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
TEMPLATES_PATH = PROJECT_ROOT / "docs" / "l2-uk-en" / "v4-seminar-section-templates.yaml"

# Types forbidden in seminar plans
FORBIDDEN_TYPES = {
    "fill-in", "match-up", "cloze", "group-sort",
    "unjumble", "anagram", "mark-the-words", "error-correction",
    "translate", "order",
}

ALL_SEMINAR_TRACKS = [
    "folk", "hist", "bio", "istorio",
    "lit", "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
    "lit-fantastika", "lit-humor", "lit-drama", "lit-doc", "lit-crimea",
    "oes", "ruth",
]


def load_activity_profiles() -> dict:
    """Load track-specific activity profiles from the templates file."""
    with open(TEMPLATES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("activity_profiles", {})


def get_profile(profiles: dict, track: str) -> dict:
    """Get the effective activity profile for a track, handling inheritance."""
    if track in profiles:
        profile = profiles[track]
        if "inherits_activities" in profile:
            base = dict(profiles[profile["inherits_activities"]])
            # Apply workbook overrides: replace the FIRST workbook item with the override
            if "workbook_override" in profile:
                workbook = list(base.get("workbook", []))
                for override in profile["workbook_override"]:
                    # Replace the first workbook item that ISN'T essay-response
                    # (essay-response is always the last item and stays)
                    for i, item in enumerate(workbook):
                        if item["type"] != "essay-response" and item["type"] != override["type"]:
                            workbook[i] = override
                            break
                base["workbook"] = workbook
            return base
        return profile
    # Fallback for lit-* subtracks
    if track.startswith("lit-") and "lit" in profiles:
        return profiles["lit"]
    return profiles.get("folk", {})


def build_activity_hints(profile: dict, plan: dict) -> list[dict]:
    """Generate activity_hints from a track profile + plan content."""
    hints = []

    # Get section names from plan for contextual focus
    sections = plan.get("content_outline", [])
    section_names = [s.get("section", "") for s in sections if isinstance(s, dict)]

    # Inline activities
    for act in profile.get("inline", []):
        hint = {
            "type": act["type"],
            "placement": "inline",
            "after_section": act["after_section"],
            "focus": _contextualize_focus(act["focus"], plan, section_names),
        }
        # Add items count for quiz/true-false
        if act["type"] in ("quiz", "true-false"):
            hint["items"] = 5
        hints.append(hint)

    # Workbook activities
    for act in profile.get("workbook", []):
        hint = {
            "type": act["type"],
            "placement": "workbook",
            "focus": _contextualize_focus(act["focus"], plan, section_names),
        }
        hints.append(hint)

    return hints


def _contextualize_focus(generic_focus: str, plan: dict, section_names: list[str]) -> str:
    """Make a generic focus string more specific using plan content.

    Replaces generic descriptions with plan-specific topics where possible.
    """
    title = plan.get("title", "")

    # For comparative-study, try to pull from global synchronicity in Конфліктна карта
    if "Порівняння" in generic_focus and title:
        return f"{generic_focus} ({title})"

    # For essay, use the plan title
    if "Есе" in generic_focus and title:
        return f"{generic_focus} ({title})"

    return generic_focus


def update_plan(plan_path: Path, profile: dict, *, dry_run: bool = False) -> bool:
    """Update a single plan's activity_hints."""
    with open(plan_path) as f:
        plan = yaml.safe_load(f)

    if not plan or not isinstance(plan, dict):
        return False

    # Generate new hints
    new_hints = build_activity_hints(profile, plan)

    # Check if update is needed
    old_hints = plan.get("activity_hints", [])
    has_forbidden = any(
        isinstance(h, dict) and h.get("type") in FORBIDDEN_TYPES
        for h in old_hints
    )
    is_generic = (
        len(old_hints) <= 4
        and all(isinstance(h, dict) and h.get("type") in ("quiz", "fill-in", "essay-response", "critical-analysis", "note")
                for h in old_hints)
    )

    if not has_forbidden and not is_generic and len(old_hints) >= 5:
        # Plan already has rich, valid hints — skip
        return False

    if dry_run:
        slug = plan_path.stem
        old_types = [h.get("type", "?") for h in old_hints if isinstance(h, dict)]
        new_types = [h["type"] for h in new_hints]
        print(f"  {slug}: {old_types} → {new_types}")
        return True

    plan["activity_hints"] = new_hints

    with open(plan_path, "w") as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, width=120)

    return True


def main():
    parser = argparse.ArgumentParser(description="Update seminar plan activity_hints")
    parser.add_argument("--track", help="Update one track only")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    profiles = load_activity_profiles()
    print(f"📋 Loaded {len(profiles)} activity profiles")

    tracks = [args.track] if args.track else ALL_SEMINAR_TRACKS
    total_updated = 0
    total_skipped = 0

    for track in tracks:
        track_dir = PLANS_ROOT / track
        if not track_dir.is_dir():
            continue

        profile = get_profile(profiles, track)
        if not profile:
            print(f"  ⚠️  No profile for {track}")
            continue

        plans = sorted(
            p for p in track_dir.glob("*.yaml")
            if not p.name.startswith(".") and not p.name.endswith(".bak")
        )

        updated = 0
        for plan_path in plans:
            if update_plan(plan_path, profile, dry_run=args.dry_run):
                updated += 1
            else:
                total_skipped += 1

        if updated:
            print(f"  {track.upper()}: {updated}/{len(plans)} updated")
            total_updated += updated

    print(f"\n{'═' * 40}")
    print(f"  Updated: {total_updated} | Skipped: {total_skipped}")
    if args.dry_run:
        print("  (DRY RUN)")
    print(f"{'═' * 40}")


if __name__ == "__main__":
    main()
