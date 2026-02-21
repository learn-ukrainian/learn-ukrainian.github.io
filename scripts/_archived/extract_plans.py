#!/usr/bin/env python3
"""
Extract module plans from meta files to create standalone plan files.

This script extracts plan-relevant data from existing meta files and creates
minimal plan YAML files in the plans/{level}/ directory structure.

Usage:
    python scripts/extract_plans.py b1              # Extract all B1 plans
    python scripts/extract_plans.py b1 5            # Extract single module
    python scripts/extract_plans.py b1 1-10         # Extract range
    python scripts/extract_plans.py all             # Extract all levels
    python scripts/extract_plans.py --validate b1   # Validate existing plans

The extraction preserves:
- module, level, sequence, version, title, subtitle
- focus, pedagogy, objectives
- content_outline, word_target, word_tolerance
- vocabulary (required, recommended, forbidden)
- activities spec (types_required, min_items_per_type, etc.)
- connects_to, constraints, sources
"""

import sys
import re
import yaml
from pathlib import Path
from datetime import datetime
import json
import jsonschema

# Project root
ROOT = Path(__file__).parent.parent

# Levels that have meta files to extract from
CORE_LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
TRACK_LEVELS = ['b2-hist', 'c1-bio', 'c1-hist', 'lit']
ALL_LEVELS = CORE_LEVELS + TRACK_LEVELS

# Plan schema for validation
PLAN_SCHEMA_PATH = ROOT / "schemas" / "module-plan.schema.json"

# Fields to extract for plans (in order)
PLAN_FIELDS = [
    'module', 'level', 'sequence', 'version', 'title', 'subtitle',
    'focus', 'pedagogy', 'objectives', 'sources', 'content_outline',
    'word_target', 'word_tolerance', 'vocabulary', 'activities',
    'connects_to', 'constraints', 'changelog'
]


def parse_module_filter(filter_str: str) -> set[int]:
    """Parse module filter string into set of module numbers."""
    result = set()
    parts = filter_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(part))
    return result


def load_curriculum_yaml():
    """Load curriculum.yaml to get module order."""
    curriculum_path = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    with open(curriculum_path) as f:
        return yaml.safe_load(f)


def load_schema():
    """Load the module plan schema for validation."""
    if PLAN_SCHEMA_PATH.exists():
        with open(PLAN_SCHEMA_PATH) as f:
            return json.load(f)
    return None


def extract_sequence_from_slug(slug: str) -> int | None:
    """Extract sequence number from slug like '01-how-to-talk'."""
    match = re.match(r'^(\d+)-', slug)
    if match:
        return int(match.group(1))
    return None


def find_meta_file(level: str, slug: str) -> Path | None:
    """Find meta file for given level and slug."""
    meta_dir = ROOT / "curriculum" / "l2-uk-en" / level / "meta"

    # Try exact slug match
    exact = meta_dir / f"{slug}.yaml"
    if exact.exists():
        return exact

    # Try numbered pattern
    numbered = list(meta_dir.glob(f"*-{slug}.yaml"))
    if numbered:
        return numbered[0]

    # Try partial match
    matches = list(meta_dir.glob(f"*{slug}*.yaml"))
    if matches:
        return matches[0]

    return None


def normalize_vocabulary(meta: dict) -> dict | None:
    """Normalize vocabulary from meta format to plan format."""
    # Check vocabulary_hints first (B1 format)
    vocab_hints = meta.get('vocabulary_hints', {})
    if vocab_hints:
        return {
            'required': vocab_hints.get('required', []),
            'recommended': vocab_hints.get('recommended', []),
            'forbidden': vocab_hints.get('forbidden', [])
        }

    # Check vocabulary field
    vocab = meta.get('vocabulary', {})
    if isinstance(vocab, dict):
        return {
            'required': vocab.get('required', []),
            'recommended': vocab.get('recommended', []),
            'forbidden': vocab.get('forbidden', [])
        }

    return None


def normalize_activities(meta: dict) -> dict | None:
    """Normalize activities from meta format to plan format."""
    # Check activity_hints first (B1 format)
    hints = meta.get('activity_hints', [])
    if hints:
        # Extract unique types from hints
        types = list(set(h.get('type') for h in hints if h.get('type')))
        return {
            'types_required': types,
            'min_items_per_type': 6,
            'total_min_items': 30,
            'no_mirroring': True
        }

    # Check activities field
    activities = meta.get('activities', {})
    if isinstance(activities, dict) and 'types_required' in activities:
        return activities

    return None


def extract_plan_from_meta(meta: dict, slug: str, level: str) -> dict:
    """Extract plan data from meta file content."""
    plan = {}

    # Module identifier
    plan['module'] = meta.get('slug', slug)
    plan['level'] = level

    # Sequence - extract from slug or id
    seq = extract_sequence_from_slug(slug)
    if seq is None:
        # Try from id field (e.g., "b1-01")
        id_field = meta.get('id', '')
        match = re.search(r'-(\d+)$', id_field)
        if match:
            seq = int(match.group(1))
    plan['sequence'] = seq or 1

    # Version
    plan['version'] = meta.get('version', '1.0')

    # Titles
    plan['title'] = meta.get('title', '')
    if meta.get('subtitle'):
        plan['subtitle'] = meta.get('subtitle')

    # Focus and pedagogy
    plan['focus'] = meta.get('focus', 'grammar')
    plan['pedagogy'] = meta.get('pedagogy', 'TTT')

    # Objectives
    objectives = meta.get('objectives', [])
    plan['objectives'] = objectives if objectives else ['TBD']

    # Sources (if present)
    if meta.get('sources'):
        plan['sources'] = meta.get('sources')

    # Content outline
    content_outline = meta.get('content_outline', [])
    if content_outline:
        plan['content_outline'] = content_outline
    else:
        # Create stub outline
        plan['content_outline'] = [{
            'section': 'Introduction',
            'words': 200,
            'subsections': ['TBD']
        }]

    # Word target
    plan['word_target'] = meta.get('word_target', 1500)
    if meta.get('word_tolerance'):
        plan['word_tolerance'] = meta.get('word_tolerance')

    # Vocabulary
    vocab = normalize_vocabulary(meta)
    if vocab:
        plan['vocabulary'] = vocab

    # Activities
    activities = normalize_activities(meta)
    if activities:
        plan['activities'] = activities

    # Connects to
    if meta.get('connects_to'):
        plan['connects_to'] = meta.get('connects_to')

    # Constraints
    constraints = meta.get('constraints', {})
    if not constraints:
        # Build from individual fields
        constraints = {}
        if meta.get('min_engagement_boxes'):
            constraints['min_engagement_boxes'] = meta.get('min_engagement_boxes')
        if meta.get('min_examples'):
            constraints['min_examples'] = meta.get('min_examples')
        if meta.get('immersion_target'):
            constraints['immersion_target'] = meta.get('immersion_target')
        if meta.get('naturalness_threshold'):
            constraints['naturalness_threshold'] = meta.get('naturalness_threshold')
    if constraints:
        plan['constraints'] = constraints

    return plan


def write_plan_yaml(plan: dict, output_path: Path):
    """Write plan dict to YAML file with nice formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Custom YAML formatting
    class PlanDumper(yaml.SafeDumper):
        pass

    def str_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    PlanDumper.add_representer(str, str_representer)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, Dumper=PlanDumper, allow_unicode=True,
                  default_flow_style=False, sort_keys=False, width=120)


def validate_plan(plan: dict, schema: dict) -> list[str]:
    """Validate plan against schema, return list of errors."""
    errors = []
    try:
        jsonschema.validate(plan, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")
    return errors


def extract_level_plans(level: str, module_filter: set[int] | None = None,
                        validate: bool = False):
    """Extract plans for all modules in a level."""
    filter_desc = f" (modules: {sorted(module_filter)})" if module_filter else ""
    print(f"Extracting plans for {level}{filter_desc}...")

    curriculum = load_curriculum_yaml()
    if level not in curriculum.get('levels', {}):
        print(f"  Level {level} not found in curriculum.yaml")
        return

    level_data = curriculum['levels'][level]
    modules = level_data.get('modules', [])

    if not modules:
        print(f"  No modules found for {level}")
        return

    # Load schema if validating
    schema = load_schema() if validate else None

    plans_dir = ROOT / "curriculum" / "l2-uk-en" / "plans" / level
    plans_dir.mkdir(parents=True, exist_ok=True)

    stats = {'extracted': 0, 'skipped': 0, 'errors': 0, 'validated': 0}

    for i, slug in enumerate(modules, 1):
        if module_filter and i not in module_filter:
            continue

        # Check if plan already exists (for tracks that have plans)
        existing_plan = plans_dir / f"{slug}.yaml"
        if existing_plan.exists():
            if validate and schema:
                with open(existing_plan) as f:
                    plan = yaml.safe_load(f)
                errors = validate_plan(plan, schema)
                if errors:
                    print(f"  {i:03d}. {slug}: INVALID - {errors[0]}")
                    stats['errors'] += 1
                else:
                    stats['validated'] += 1
            else:
                print(f"  {i:03d}. {slug}: skipped (exists)")
                stats['skipped'] += 1
            continue

        # Find meta file
        meta_file = find_meta_file(level, slug)
        if not meta_file:
            print(f"  {i:03d}. {slug}: no meta file")
            stats['errors'] += 1
            continue

        try:
            with open(meta_file) as f:
                meta = yaml.safe_load(f)

            plan = extract_plan_from_meta(meta, slug, level)

            # Validate if requested
            if validate and schema:
                errors = validate_plan(plan, schema)
                if errors:
                    print(f"  {i:03d}. {slug}: INVALID - {errors[0]}")
                    stats['errors'] += 1
                    continue

            # Write plan file
            output_path = plans_dir / f"{slug}.yaml"
            write_plan_yaml(plan, output_path)
            print(f"  {i:03d}. {slug}: extracted")
            stats['extracted'] += 1

        except Exception as e:
            print(f"  {i:03d}. {slug}: ERROR - {e}")
            stats['errors'] += 1

    print(f"\n  Summary: {stats['extracted']} extracted, {stats['skipped']} skipped, "
          f"{stats['errors']} errors")
    if validate:
        print(f"  Validation: {stats['validated']} valid")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_plans.py {level|all} [module_filter]")
        print(f"       python scripts/extract_plans.py --validate {{level|all}}")
        print(f"\nCore levels: {', '.join(CORE_LEVELS)}")
        print(f"Track levels: {', '.join(TRACK_LEVELS)}")
        print("\nModule filter examples:")
        print("  b1 5         # Single module")
        print("  b1 1-10      # Range of modules")
        print("  b1 1-4,6-10  # Multiple ranges")
        sys.exit(1)

    validate = '--validate' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--validate']

    if not args:
        print("Error: no level specified")
        sys.exit(1)

    level_arg = args[0].lower()
    module_filter = None

    # Parse optional module filter
    if len(args) >= 2:
        try:
            module_filter = parse_module_filter(args[1])
        except ValueError:
            print(f"Invalid module filter: {args[1]}")
            sys.exit(1)

    if level_arg == 'all':
        if module_filter:
            print("Module filter not supported with 'all'")
            sys.exit(1)
        for level in ALL_LEVELS:
            extract_level_plans(level, validate=validate)
            print()
    elif level_arg in ALL_LEVELS:
        extract_level_plans(level_arg, module_filter, validate=validate)
    else:
        print(f"Unknown level: {level_arg}")
        print(f"Available: {', '.join(ALL_LEVELS)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
