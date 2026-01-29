#!/usr/bin/env python3
"""
Batch schema validation for activity YAML files.

Validates activity files against the JSON schema BEFORE running full audit.
This provides faster, more specific feedback on schema issues.

Usage:
    .venv/bin/python scripts/validate_activities_schema.py curriculum/l2-uk-en/b2-hist/activities/krym-1954.yaml
    .venv/bin/python scripts/validate_activities_schema.py --level b2-hist
    .venv/bin/python scripts/validate_activities_schema.py --all
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft7Validator, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def load_schema() -> dict:
    """Load the activity base schema."""
    schema_path = Path("schemas/activities-base.schema.json")
    if not schema_path.exists():
        print(f"❌ Schema not found: {schema_path}")
        sys.exit(1)
    with open(schema_path) as f:
        return json.load(f)


def validate_activity(activity: dict, schema: dict, activity_num: int) -> list[str]:
    """Validate a single activity against its type schema."""
    errors = []

    activity_type = activity.get('type')
    if not activity_type:
        errors.append(f"Activity #{activity_num}: Missing 'type' field")
        return errors

    # Get type-specific definition
    type_def = schema.get('definitions', {}).get(activity_type)
    if not type_def:
        errors.append(f"Activity #{activity_num}: Unknown type '{activity_type}'")
        return errors

    if not HAS_JSONSCHEMA:
        # Basic validation without jsonschema
        return validate_activity_basic(activity, type_def, activity_num)

    # Full JSON Schema validation
    validator = Draft7Validator(type_def)
    for error in validator.iter_errors(activity):
        path = '.'.join(str(p) for p in error.path) or '(root)'
        errors.append(f"Activity #{activity_num} ({activity_type}): {path} - {error.message}")

    return errors


def validate_activity_basic(activity: dict, type_def: dict, activity_num: int) -> list[str]:
    """Basic validation without jsonschema library."""
    errors = []
    activity_type = activity.get('type')

    # Check required fields
    required = type_def.get('required', [])
    for field in required:
        if field not in activity:
            errors.append(f"Activity #{activity_num} ({activity_type}): Missing required field '{field}'")

    # Check for extra fields (additionalProperties: false)
    if type_def.get('additionalProperties') is False:
        allowed = set(type_def.get('properties', {}).keys())
        # Handle oneOf schemas (like reading)
        if 'oneOf' in type_def:
            for variant in type_def['oneOf']:
                allowed.update(variant.get('properties', {}).keys())

        actual = set(activity.keys())
        extra = actual - allowed
        if extra:
            errors.append(f"Activity #{activity_num} ({activity_type}): Extra fields not allowed: {extra}")

    return errors


def validate_file(yaml_path: Path, schema: dict) -> tuple[bool, list[str]]:
    """Validate an activity YAML file."""
    errors = []

    if not yaml_path.exists():
        return False, [f"File not found: {yaml_path}"]

    try:
        with open(yaml_path) as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    if content is None:
        return False, ["Empty file"]

    # Check root structure - must be a list
    if isinstance(content, dict):
        if 'activities' in content:
            errors.append("Root should be a bare list, not wrapped in 'activities:'")
            content = content['activities']
        else:
            errors.append("Root should be a list of activities, got dict")
            return False, errors

    if not isinstance(content, list):
        errors.append(f"Root should be a list, got {type(content).__name__}")
        return False, errors

    # Validate each activity
    for i, activity in enumerate(content, 1):
        if not isinstance(activity, dict):
            errors.append(f"Activity #{i}: Should be a dict, got {type(activity).__name__}")
            continue
        activity_errors = validate_activity(activity, schema, i)
        errors.extend(activity_errors)

    return len(errors) == 0, errors


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: .venv/bin/python scripts/validate_activities_schema.py <file.yaml>")
        print("       .venv/bin/python scripts/validate_activities_schema.py --level b2-hist")
        print("       .venv/bin/python scripts/validate_activities_schema.py --all")
        sys.exit(1)

    schema = load_schema()

    if not HAS_JSONSCHEMA:
        print("⚠️ jsonschema not installed - using basic validation")
        print("   Install with: pip install jsonschema")
        print()

    files_to_check = []

    if args[0] == '--all':
        files_to_check = list(Path("curriculum/l2-uk-en").glob("*/activities/*.yaml"))
    elif args[0] == '--level':
        if len(args) < 2:
            print("❌ --level requires a level name")
            sys.exit(1)
        level = args[1]
        level_dir = Path(f"curriculum/l2-uk-en/{level}/activities")
        if not level_dir.exists():
            print(f"❌ Directory not found: {level_dir}")
            sys.exit(1)
        files_to_check = list(level_dir.glob("*.yaml"))
    else:
        files_to_check = [Path(args[0])]

    total_errors = 0
    files_with_errors = 0

    for yaml_path in sorted(files_to_check):
        passed, errors = validate_file(yaml_path, schema)

        if not passed:
            files_with_errors += 1
            total_errors += len(errors)
            print(f"\n❌ {yaml_path.name}")
            for error in errors:
                print(f"   {error}")
        else:
            print(f"✅ {yaml_path.name}")

    print()
    print("=" * 50)
    if total_errors == 0:
        print(f"✅ All {len(files_to_check)} files passed schema validation")
        sys.exit(0)
    else:
        print(f"❌ {files_with_errors}/{len(files_to_check)} files have errors ({total_errors} total)")
        sys.exit(1)


if __name__ == "__main__":
    main()
