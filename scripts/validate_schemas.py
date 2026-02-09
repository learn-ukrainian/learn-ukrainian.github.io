#!/usr/bin/env python3
"""
YAML Schema Validator for Curriculum Files.

Usage:
    .venv/bin/python scripts/validate_schemas.py <path_to_yaml_or_dir>

Supports:
    - Activities (activities/*.yaml)
    - Meta (meta/*.yaml)
    - Vocabulary (vocabulary/*.yaml)
    - Plans (plans/**/*.yaml)
"""

import sys
import os
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    import jsonschema
    from jsonschema import Draft7Validator, RefResolver
except ImportError:
    print("Error: 'jsonschema' library not found. Install with 'pip install jsonschema'.")
    sys.exit(1)

# Schema mapping based on directory names
SCHEMA_MAP = {
    "activities": "activity.schema.json",
    "meta": "meta.schema.json",
    "vocabulary": "vocabulary.schema.json",
    "plans": "module-plan.schema.json"
}

def get_schema_path(schema_name: str) -> Path:
    """Get the absolute path to a schema file."""
    return Path(__file__).parent.parent / "schemas" / schema_name

def load_json_schema(schema_path: Path) -> Dict:
    """Load a JSON schema from file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def detect_schema_type(file_path: Path) -> Optional[str]:
    """Detect schema type based on file path."""
    parts = file_path.parts
    for folder, schema in SCHEMA_MAP.items():
        if folder in parts:
            return schema

    # Fallback: check filename or content
    if file_path.name.endswith('.yaml'):
        # Could be any, try to guess from parent
        parent_name = file_path.parent.name
        if parent_name in SCHEMA_MAP:
            return SCHEMA_MAP[parent_name]

    return None

def format_error(error: jsonschema.ValidationError, file_path: Path) -> str:
    """Format a jsonschema error into a human-readable message."""
    path = " -> ".join([str(p) for p in error.path])
    if not path:
        path = "root"

    return f"[{file_path}] {path}: {error.message}"

def validate_yaml(file_path: Path, schema_name: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Validate a single YAML file against a schema."""
    if not schema_name:
        schema_name = detect_schema_type(file_path)

    if not schema_name:
        return False, [f"Could not detect schema type for {file_path}"]

    schema_path = get_schema_path(schema_name)
    if not schema_path.exists():
        return False, [f"Schema file not found: {schema_path}"]

    try:
        schema = load_json_schema(schema_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            return True, [] # Empty file is valid (or skip?)

        # Create a resolver to handle relative $refs (e.g., to activities-base.schema.json)
        schema_dir = schema_path.parent.absolute()
        store = {}
        for s_file in schema_dir.glob("*.schema.json"):
            try:
                with open(s_file, 'r', encoding='utf-8') as f:
                    s_data = yaml.safe_load(f)
                    if "$id" in s_data:
                        store[s_data["$id"]] = s_data
                    # Also store by filename to handle simple relative refs
                    store[s_file.name] = s_data
            except Exception:
                continue

        resolver = RefResolver(base_uri=schema_dir.as_uri() + "/", referrer=schema, store=store)

        validator = Draft7Validator(schema, resolver=resolver)
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

        if not errors:
            return True, []

        return False, [format_error(e, file_path) for e in errors]

    except yaml.YAMLError as e:
        return False, [f"[{file_path}] YAML Parse Error: {e}"]
    except Exception as e:
        return False, [f"[{file_path}] Unexpected Error: {e}"]

def main():
    parser = argparse.ArgumentParser(description="Validate curriculum YAML files against JSON schemas.")
    parser.add_argument("path", help="Path to a YAML file or directory containing YAML files.")
    parser.add_argument("--type", choices=SCHEMA_MAP.keys(), help="Explicitly specify schema type.")

    args = parser.parse_args()
    target_path = Path(args.path)

    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist.")
        sys.exit(1)

    files_to_validate = []
    if target_path.is_file():
        files_to_validate.append(target_path)
    else:
        # Recursive search for .yaml files
        for ext in ['*.yaml', '*.yml']:
            files_to_validate.extend(target_path.rglob(ext))

    if not files_to_validate:
        print(f"No YAML files found in {target_path}")
        return

    schema_override = SCHEMA_MAP.get(args.type) if args.type else None

    total_files = 0
    total_errors = 0
    passed_files = 0

    for file_path in files_to_validate:
        # Skip files in hidden directories
        if any(part.startswith('.') for part in file_path.parts):
            continue

        total_files += 1
        is_valid, errors = validate_yaml(file_path, schema_override)

        if is_valid:
            passed_files += 1
        else:
            for err in errors:
                print(err)
            total_errors += len(errors)

    if total_errors > 0:
        print(f"\nValidation failed: {total_errors} errors in {total_files - passed_files} files.")
        sys.exit(1)
    else:
        print(f"\nValidation passed: {passed_files}/{total_files} files are valid.")

if __name__ == "__main__":
    main()
