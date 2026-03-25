"""
Activity V2 YAML validator.

Validates activity YAML files against the V2 JSON Schema.

Usage:
    .venv/bin/python scripts/validate_activities_v2.py a1 things-have-gender
    .venv/bin/python scripts/validate_activities_v2.py a1 --all
    .venv/bin/python scripts/validate_activities_v2.py c1 b2-review-bridge
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "activity-v2.schema.json"
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def load_schema() -> dict:
    """Load the V2 activity JSON Schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def find_activity_file(level: str, slug: str) -> Path | None:
    """Find the activity YAML file for a given level and slug."""
    path = CURRICULUM_ROOT / level / "activities" / f"{slug}.yaml"
    if path.exists():
        return path
    return None


def find_all_activity_files(level: str) -> list[Path]:
    """Find all activity YAML files for a given level."""
    activities_dir = CURRICULUM_ROOT / level / "activities"
    if not activities_dir.exists():
        return []
    return sorted(activities_dir.glob("*.yaml"))


def validate_file(path: Path, schema: dict) -> list[str]:
    """Validate a single activity YAML file against the V2 schema.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if data is None:
        return ["File is empty"]

    if not isinstance(data, dict):
        return [f"Expected a mapping at root, got {type(data).__name__}"]

    # Validate against schema
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        json_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  [{json_path}] {error.message}")

    # Additional semantic checks beyond JSON Schema
    errors.extend(_check_inline_ids(data))
    errors.extend(_check_duplicate_ids(data))

    return errors


def _check_inline_ids(data: dict) -> list[str]:
    """Verify all inline activities have unique, non-empty ids."""
    errors: list[str] = []
    inline = data.get("inline", [])
    for i, activity in enumerate(inline):
        if not isinstance(activity, dict):
            continue
        aid = activity.get("id")
        if not aid:
            errors.append(f"  inline[{i}]: missing required 'id' field")
    return errors


def _check_duplicate_ids(data: dict) -> list[str]:
    """Check for duplicate ids across inline activities."""
    errors: list[str] = []
    seen: dict[str, int] = {}
    for i, activity in enumerate(data.get("inline", [])):
        if not isinstance(activity, dict):
            continue
        aid = activity.get("id")
        if aid and aid in seen:
            errors.append(
                f"  inline[{i}]: duplicate id '{aid}' "
                f"(first seen at inline[{seen[aid]}])"
            )
        elif aid:
            seen[aid] = i
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate activity V2 YAML files against JSON Schema"
    )
    parser.add_argument("level", help="Level identifier (e.g., a1, c1, hist)")
    parser.add_argument(
        "slug",
        nargs="?",
        default=None,
        help="Module slug (e.g., things-have-gender). Use --all for all modules.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all activity files in the level",
    )
    args = parser.parse_args()

    schema = load_schema()

    if args.all:
        files = find_all_activity_files(args.level)
        if not files:
            print(f"No activity files found in {args.level}/activities/")
            return 1
    elif args.slug:
        path = find_activity_file(args.level, args.slug)
        if path is None:
            print(
                f"Activity file not found: "
                f"{CURRICULUM_ROOT / args.level / 'activities' / (args.slug + '.yaml')}"
            )
            return 1
        files = [path]
    else:
        parser.error("Provide a slug or use --all")
        return 1

    total_errors = 0
    for path in files:
        errors = validate_file(path, schema)
        slug = path.stem
        if errors:
            print(f"FAIL  {args.level}/{slug}")
            for err in errors:
                print(err)
            total_errors += len(errors)
        else:
            print(f"PASS  {args.level}/{slug}")

    print()
    if total_errors:
        print(f"{total_errors} error(s) in {len(files)} file(s)")
        return 1

    print(f"All {len(files)} file(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
