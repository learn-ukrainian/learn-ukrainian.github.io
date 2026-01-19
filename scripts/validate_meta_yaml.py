#!/usr/bin/env python3
"""
Meta YAML Validation & Migration Script

Validates all meta YAML files against the schema and reports missing fields.
Can also auto-fix common issues.

Usage:
    .venv/bin/python scripts/validate_meta_yaml.py                    # Validate all
    .venv/bin/python scripts/validate_meta_yaml.py --level b2-hist    # Validate specific level
    .venv/bin/python scripts/validate_meta_yaml.py --fix              # Auto-fix issues
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
import jsonschema

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


SCHEMA_PATH = Path("schemas/meta-module.schema.json")
SCHEMA_MINIMAL_PATH = Path("schemas/meta-module-minimal.schema.json")
CURRICULUM_BASE = Path("curriculum/l2-uk-en")

# Levels that use the new meta YAML architecture
META_YAML_LEVELS = [
    "a1", "a2", "b1", "b2", "b2-hist", 
    "c1", "c1-hist", "c1-bio", "c2", "lit"
]

# Default values for missing optional fields
DEFAULT_VALUES = {
    "duration": 120,
    "transliteration": "none",
    "tags": [],
    "objectives": [],
    "grammar": [],
    "pedagogy": "seminar",
    "register": "публіцистичний",
    "vocabulary_count": 25,
    "immersion": "100% Ukrainian",
}

# Fields that indicate a "full agent spec" meta file
AGENT_SPEC_FIELDS = ["content_outline", "vocabulary_hints", "activity_hints", "sources"]


def load_schemas() -> tuple[dict, dict]:
    """Load both the full and minimal meta module JSON schemas."""
    schemas = {}
    
    for name, path in [("full", SCHEMA_PATH), ("minimal", SCHEMA_MINIMAL_PATH)]:
        if not path.exists():
            print(f"{Colors.RED}❌ Schema not found: {path}{Colors.RESET}")
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            schemas[name] = json.load(f)
    
    return schemas["full"], schemas["minimal"]


def is_full_spec(data: dict) -> bool:
    """Determine if a meta file is a full agent spec or a minimal stub."""
    return any(field in data for field in AGENT_SPEC_FIELDS)


def find_meta_files(level: str | None = None) -> list[Path]:
    """Find all meta YAML files, optionally filtered by level."""
    meta_files = []
    
    levels = [level] if level else META_YAML_LEVELS
    
    for lvl in levels:
        meta_dir = CURRICULUM_BASE / lvl / "meta"
        if meta_dir.exists():
            meta_files.extend(meta_dir.glob("*.yaml"))
    
    return sorted(meta_files)


def validate_meta_file(file_path: Path, full_schema: dict, minimal_schema: dict, fix: bool = False) -> dict:
    """
    Validate a single meta YAML file against the appropriate schema.
    
    Auto-detects whether to use full (agent spec) or minimal schema based on content.
    
    Returns a dict with:
        - valid: bool
        - errors: list of error messages
        - warnings: list of warning messages (missing optional fields)
        - fixed: list of fields that were auto-fixed
        - schema_type: 'full' or 'minimal'
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "fixed": [],
        "schema_type": "unknown"
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        result["valid"] = False
        result["errors"].append(f"YAML parse error: {e}")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"File read error: {e}")
        return result
    
    if not data:
        result["valid"] = False
        result["errors"].append("Empty YAML file")
        return result
    
    # Auto-detect schema type
    if is_full_spec(data):
        schema = full_schema
        result["schema_type"] = "full"
    else:
        schema = minimal_schema
        result["schema_type"] = "minimal"
    
    # Check for required fields from schema
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {field}")
    
    # Schema validation
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        result["valid"] = False
        result["errors"].append(f"Schema violation at '{path}': {e.message}")
    
    # Check for recommended optional fields
    optional_fields = ["duration", "transliteration", "tags", "objectives", "grammar", "pedagogy"]
    missing_optional = [f for f in optional_fields if f not in data]
    
    if missing_optional:
        result["warnings"].append(f"Missing optional fields: {', '.join(missing_optional)}")
        
        if fix:
            # Auto-fix by adding default values
            modified = False
            for field in missing_optional:
                if field in DEFAULT_VALUES:
                    data[field] = DEFAULT_VALUES[field]
                    result["fixed"].append(field)
                    modified = True
            
            if modified:
                # Write back with preserved comments if possible
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # Check for 'module' vs 'id' normalization
    if 'module' not in data and 'id' in data:
        result["warnings"].append("Has 'id' but missing 'module' field")
        if fix:
            data['module'] = data['id']
            result["fixed"].append("module (copied from id)")
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # Check content_outline completeness
    if 'content_outline' in data:
        outline = data['content_outline']
        if not outline:
            result["warnings"].append("content_outline is empty")
        else:
            total_words = sum(s.get('words', 0) for s in outline)
            word_target = data.get('word_target', 0)
            if word_target > 0 and total_words < word_target * 0.8:
                result["warnings"].append(
                    f"Outline word sum ({total_words}) < 80% of word_target ({word_target})"
                )
    
    # Check activity_hints completeness
    if 'activity_hints' in data:
        hints = data['activity_hints']
        if not hints:
            result["warnings"].append("activity_hints is empty")
        elif len(hints) < 4:
            result["warnings"].append(f"Only {len(hints)} activity hints (recommend 4+)")
    
    return result


def print_summary(results: dict[Path, dict]) -> None:
    """Print a summary of validation results."""
    total = len(results)
    valid = sum(1 for r in results.values() if r["valid"])
    with_warnings = sum(1 for r in results.values() if r["warnings"])
    fixed = sum(1 for r in results.values() if r["fixed"])
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Total files:     {total}")
    print(f"Valid:           {Colors.GREEN}{valid}{Colors.RESET}")
    print(f"Invalid:         {Colors.RED}{total - valid}{Colors.RESET}")
    print(f"With warnings:   {Colors.YELLOW}{with_warnings}{Colors.RESET}")
    if fixed > 0:
        print(f"Auto-fixed:      {Colors.CYAN}{fixed}{Colors.RESET}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Validate Meta YAML files against schema")
    parser.add_argument("--level", "-l", help="Specific level to validate (e.g., b2-hist)")
    parser.add_argument("--fix", "-f", action="store_true", help="Auto-fix missing optional fields")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all files, not just errors")
    parser.add_argument("--errors-only", "-e", action="store_true", help="Only show errors, hide warnings")
    args = parser.parse_args()
    
    full_schema, minimal_schema = load_schemas()
    meta_files = find_meta_files(args.level)
    
    if not meta_files:
        print(f"{Colors.YELLOW}⚠️ No meta YAML files found{Colors.RESET}")
        if args.level:
            print(f"   Level: {args.level}")
            print(f"   Expected path: {CURRICULUM_BASE / args.level / 'meta'}")
        return
    
    print(f"\n{Colors.BOLD}Validating {len(meta_files)} meta YAML files...{Colors.RESET}\n")
    
    results: dict[Path, dict] = {}
    
    for file_path in meta_files:
        result = validate_meta_file(file_path, full_schema, minimal_schema, fix=args.fix)
        results[file_path] = result
        
        # Determine if we should print this file
        has_issues = not result["valid"] or result["warnings"]
        should_print = args.verbose or has_issues
        
        if should_print:
            # Get relative path for cleaner output
            rel_path = file_path.relative_to(CURRICULUM_BASE)
            
            if result["valid"] and not result["warnings"]:
                if args.verbose:
                    print(f"{Colors.GREEN}✓{Colors.RESET} {rel_path}")
            elif result["valid"]:
                if not args.errors_only:
                    print(f"{Colors.YELLOW}⚠{Colors.RESET} {rel_path}")
                    for warn in result["warnings"]:
                        print(f"   {Colors.YELLOW}↳ {warn}{Colors.RESET}")
            else:
                print(f"{Colors.RED}✗{Colors.RESET} {rel_path}")
                for err in result["errors"]:
                    print(f"   {Colors.RED}↳ {err}{Colors.RESET}")
                if not args.errors_only:
                    for warn in result["warnings"]:
                        print(f"   {Colors.YELLOW}↳ {warn}{Colors.RESET}")
            
            # Show fixed fields
            if result["fixed"]:
                print(f"   {Colors.CYAN}✓ Auto-fixed: {', '.join(result['fixed'])}{Colors.RESET}")
    
    print_summary(results)
    
    # Exit with error code if any files are invalid
    if any(not r["valid"] for r in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
