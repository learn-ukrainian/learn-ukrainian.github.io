#!/usr/bin/env python3
"""
Unified Curriculum Schema Validator

Validates all curriculum YAML file types (activity, plan, meta, vocabulary)
against their respective JSON schemas.

Usage:
    .venv/bin/python scripts/validate_schemas.py {path_or_level}

Examples:
    .venv/bin/python scripts/validate_schemas.py curriculum/l2-uk-en/a1/activities/01-the-cyrillic-code-i.yaml
    .venv/bin/python scripts/validate_schemas.py curriculum/l2-uk-en/plans/b1/
    .venv/bin/python scripts/validate_schemas.py a1
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import yaml
try:
    import jsonschema
    from jsonschema import Draft7Validator, validators
except ImportError:
    print("Error: jsonschema library not installed. Run: pip install jsonschema")
    sys.exit(1)

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Add project root to path for shared module imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.validation import get_schema_path, load_schema, validate_yaml_content, detect_meta_type, LineLoader

# =============================================================================
# YAML LOADING
# =============================================================================

def load_yaml(path: Path) -> Tuple[Optional[Any], List[str]]:
    """Load YAML with error handling and line numbers."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.load(content, Loader=LineLoader)
            return data, []
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]
    except Exception as e:
        return None, [f"Error reading file: {e}"]

# =============================================================================
# VALIDATION ENGINE
# =============================================================================

class SchemaValidator:
    def __init__(self):
        self.cache = {}

    def get_cached_schema(self, schema_path: Path) -> Optional[Dict]:
        if schema_path in self.cache:
            return self.cache[schema_path]

        schema = load_schema(schema_path)
        if schema:
            self.cache[schema_path] = schema
        return schema

    def validate(self, data: Any, schema: Dict) -> List[str]:
        return validate_yaml_content(data, schema)

# =============================================================================
# FILE TYPE DETECTION
# =============================================================================

def detect_file_type(path: Path, data: Any) -> Optional[str]:
    """Detect the type of curriculum file based on path and content."""
    path_str = str(path).lower()

    if "/activities/" in path_str or path_str.endswith(".activities.yaml"):
        return "activity"

    if "/plans/" in path_str:
        return "plan"

    if "/meta/" in path_str:
        return "meta"

    if "/vocabulary/" in path_str:
        return "vocabulary"

    # Content-based detection fallback
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict) and "type" in data[0]:
            return "activity"

    if isinstance(data, dict):
        if "content_outline" in data and "word_target" in data:
            return "plan"
        if "focus" in data and "activity_hints" in data:
            return "meta"
        if "items" in data and ("lemma" in data["items"][0] if data["items"] else True):
            return "vocabulary"

    return None

# =============================================================================
# TYPE-SPECIFIC VALIDATORS
# =============================================================================

def validate_activity(path: Path, data: Any, validator: SchemaValidator) -> List[str]:
    if not isinstance(data, list):
        return ["Activity file must be a list of activities at root."]

    # Detect level from path
    level = "b1"  # Default
    for part in path.parts:
        if part.lower() in ["a1", "a2", "b1", "b2", "c1", "c2", "lit", "b2-hist", "c1-bio", "c1-hist", "oes", "ruth"]:
            level = part.lower()
            break

    schema_path = get_schema_path("activity", level)
    schema = validator.get_cached_schema(schema_path)
    if not schema:
        return [f"Schema not found for level {level}"]

    return validator.validate(data, schema)

def validate_plan(path: Path, data: Any, validator: SchemaValidator) -> List[str]:
    schema_path = get_schema_path("plan")
    schema = validator.get_cached_schema(schema_path)
    if not schema:
        return ["Plan schema not found"]
    return validator.validate(data, schema)

def validate_meta(path: Path, data: Any, validator: SchemaValidator) -> List[str]:
    meta_type = detect_meta_type(data)
    schema_path = get_schema_path(meta_type)

    schema = validator.get_cached_schema(schema_path)
    if not schema:
        return ["Meta schema not found"]
    return validator.validate(data, schema)

def validate_vocabulary(path: Path, data: Any, validator: SchemaValidator) -> List[str]:
    schema_path = get_schema_path("vocabulary")
    schema = validator.get_cached_schema(schema_path)
    if not schema:
        return ["Vocabulary schema not found"]
    return validator.validate(data, schema)

# =============================================================================
# MAIN RUNNER
# =============================================================================

def validate_file(path: Path, validator: SchemaValidator) -> Tuple[bool, List[str], Optional[str]]:
    data, errors = load_yaml(path)
    if errors:
        return False, errors, None

    file_type = detect_file_type(path, data)
    if not file_type:
        return False, ["Could not determine curriculum file type."], None

    if file_type == "activity":
        errors = validate_activity(path, data, validator)
    elif file_type == "plan":
        errors = validate_plan(path, data, validator)
    elif file_type == "meta":
        errors = validate_meta(path, data, validator)
    elif file_type == "vocabulary":
        errors = validate_vocabulary(path, data, validator)

    return len(errors) == 0, errors, file_type

def main():
    parser = argparse.ArgumentParser(description="Validate curriculum YAML files against schemas")
    parser.add_argument("path", help="Path to file, directory, or level name (e.g., a1)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Search directories recursively")
    args = parser.parse_args()

    target_path = Path(args.path)

    # Handle level name (e.g., "a1")
    if not target_path.exists():
        curriculum_base = Path("curriculum/l2-uk-en")
        if (curriculum_base / args.path).exists():
            target_path = curriculum_base / args.path
        else:
            print(f"{Colors.RED}Error: Path or level '{args.path}' not found.{Colors.RESET}")
            sys.exit(1)

    files_to_validate = []
    if target_path.is_file():
        files_to_validate.append(target_path)
    else:
        pattern = "**/*.yaml" if args.recursive else "*.yaml"
        # Search in specific subdirectories if it's a level directory
        if (target_path / "activities").exists() or (target_path / "meta").exists() or (target_path / "vocabulary").exists():
             for sub in ["activities", "meta", "vocabulary"]:
                 files_to_validate.extend((target_path / sub).glob("**/*.yaml"))
             # Also check plans
             plans_base = Path("curriculum/l2-uk-en/plans") / target_path.name
             if plans_base.exists():
                 files_to_validate.extend(plans_base.glob("*.yaml"))
        else:
            files_to_validate.extend(target_path.glob(pattern))

    if not files_to_validate:
        print(f"{Colors.YELLOW}No YAML files found to validate in {target_path}.{Colors.RESET}")
        return

    validator = SchemaValidator()
    total_files = 0
    passed_files = 0

    print(f"{Colors.BOLD}Validating {len(files_to_validate)} files...{Colors.RESET}\n")

    for path in sorted(files_to_validate):
        total_files += 1
        is_valid, errors, file_type = validate_file(path, validator)

        rel_path = path
        try:
            rel_path = path.relative_to(Path.cwd())
        except ValueError:
            pass

        type_str = f"[{file_type.upper()}]" if file_type else ""

        if is_valid:
            print(f"{Colors.GREEN}✓ {rel_path} {type_str}{Colors.RESET}")
            passed_files += 1
        else:
            print(f"{Colors.RED}✗ {rel_path} {type_str}{Colors.RESET}")
            for err in errors:
                print(f"  {Colors.RED}↳ {err}{Colors.RESET}")
            print()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"Summary: {passed_files}/{total_files} files passed.")
    print(f"{'='*60}")

    if passed_files < total_files:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
