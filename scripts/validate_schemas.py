#!/usr/bin/env python3
"""
Standalone CLI for validating curriculum YAML files against JSON schemas.

Usage:
    .venv/bin/python scripts/validate_schemas.py <path>
    .venv/bin/python scripts/validate_schemas.py curriculum/l2-uk-en/b1/vocabulary/aspect-complete-system.yaml
    .venv/bin/python scripts/validate_schemas.py curriculum/l2-uk-en/plans/b1/  # validate all YAML in dir

Auto-detects file type from path components:
    activities/  -> activity.schema.json + activities-base.schema.json
    vocabulary/  -> vocabulary.schema.json
    meta/        -> meta-module.schema.json
    plans/       -> module-plan.schema.json

Exit codes:
    0 = all files valid
    1 = validation errors found
    2 = usage error

Issue: #534
"""

import json
import sys
from pathlib import Path

import yaml

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: .venv/bin/pip install jsonschema", file=sys.stderr)
    sys.exit(2)


SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

# Map path components to schema filenames
FILE_TYPE_MAP = {
    "activities": "activity.schema.json",
    "vocabulary": "vocabulary.schema.json",
    "meta": "meta-module.schema.json",
    "plans": "module-plan.schema.json",
}


def detect_file_type(path: Path) -> str | None:
    """Detect curriculum file type from path components."""
    for part in path.parts:
        if part in FILE_TYPE_MAP:
            return part
    return None


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema by filename."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> object:
    """Load a YAML file, returning parsed data."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_file(path: Path) -> list[str]:
    """
    Validate a single YAML file against its schema.

    Returns list of error strings (empty = valid).
    """
    errors = []

    file_type = detect_file_type(path)
    if not file_type:
        return [f"{path}: Cannot detect file type (expected activities/, vocabulary/, meta/, or plans/ in path)"]

    schema_name = FILE_TYPE_MAP[file_type]

    try:
        schema = load_schema(schema_name)
    except FileNotFoundError as e:
        return [f"{path}: {e}"]

    try:
        data = load_yaml(path)
    except yaml.YAMLError as e:
        return [f"{path}: YAML parse error: {e}"]

    if data is None:
        return [f"{path}: File is empty"]

    # Activities: check bare list format
    if file_type == "activities":
        if isinstance(data, dict):
            errors.append(
                f"{path}: Activities must be a bare list at root, not a dictionary. "
                "Remove the 'activities:' wrapper key."
            )
            # Still validate the inner list if possible
            data = data.get("activities", data)
        if not isinstance(data, list):
            return [f"{path}: Expected a list of activities, got {type(data).__name__}"]

    # Validate against schema
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        field_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "(root)"
        errors.append(f"{path}: {field_path}: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"{path}: Schema error: {e.message}")

    # Activities: also validate each item against base schema definitions
    if file_type == "activities" and isinstance(data, list):
        try:
            base_schema = load_schema("activities-base.schema.json")
        except FileNotFoundError:
            pass
        else:
            definitions = base_schema.get("definitions", {})
            for i, activity in enumerate(data):
                if not isinstance(activity, dict):
                    errors.append(f"{path}: [{i}]: Expected dict, got {type(activity).__name__}")
                    continue
                act_type = activity.get("type")
                if not act_type:
                    errors.append(f"{path}: [{i}]: Missing 'type' field")
                    continue
                type_schema = definitions.get(act_type)
                if not type_schema:
                    errors.append(f"{path}: [{i}]: Unknown activity type '{act_type}'")
                    continue
                try:
                    jsonschema.validate(instance=activity, schema=type_schema)
                except jsonschema.ValidationError as e:
                    field = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else act_type
                    errors.append(f"{path}: [{i}] ({act_type}): {field}: {e.message}")

    return errors


def main(args: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 for valid, 1 for errors, 2 for usage error."""
    if args is None:
        args = sys.argv[1:]

    if not args:
        print("Usage: validate_schemas.py <path> [<path> ...]", file=sys.stderr)
        print("  path: YAML file or directory to validate", file=sys.stderr)
        return 2

    all_errors = []

    for arg in args:
        path = Path(arg)

        if not path.exists():
            all_errors.append(f"{path}: File not found")
            continue

        if path.is_dir():
            # Validate all .yaml files in directory
            yaml_files = sorted(path.glob("*.yaml"))
            if not yaml_files:
                print(f"  No .yaml files in {path}")
                continue
            for yaml_file in yaml_files:
                errors = validate_file(yaml_file)
                all_errors.extend(errors)
                if not errors:
                    print(f"  OK  {yaml_file}")
        else:
            if not path.suffix in (".yaml", ".yml"):
                all_errors.append(f"{path}: Not a YAML file")
                continue
            errors = validate_file(path)
            all_errors.extend(errors)
            if not errors:
                print(f"  OK  {path}")

    if all_errors:
        print(f"\n{len(all_errors)} error(s) found:", file=sys.stderr)
        for error in all_errors:
            print(f"  ERROR  {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
