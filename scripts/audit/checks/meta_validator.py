"""
Meta YAML validation checks.
Enforces strict metadata requirements for Seminar-style modules.
Also validates activity_hints types against VALID_ACTIVITY_TYPES for all modules.
"""

import json
import os
import sys
from pathlib import Path
import jsonschema

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from slug_utils import to_bare_slug

from ..config import VALID_ACTIVITY_TYPES


def check_activity_hints_valid(meta_data: dict | None) -> list[dict]:
    """
    Validate that activity_hints types are valid activity types.

    This runs for ALL modules with meta.yaml, not just seminar modules.

    Args:
        meta_data: The loaded Meta YAML dict (or None).

    Returns:
        List of violation dictionaries.
    """
    violations = []

    if not meta_data:
        return violations

    activity_hints = meta_data.get('activity_hints', [])
    if not activity_hints:
        return violations

    invalid_types = []
    for hint in activity_hints:
        if isinstance(hint, dict):
            activity_type = hint.get('type')
            if activity_type and activity_type not in VALID_ACTIVITY_TYPES:
                invalid_types.append(activity_type)

    if invalid_types:
        violations.append({
            'type': 'INVALID_ACTIVITY_TYPE',
            'severity': 'critical',
            'message': f"Invalid activity types in activity_hints: {invalid_types}. Valid types: {VALID_ACTIVITY_TYPES}",
            'fix': f"Replace invalid types with valid ones from: {', '.join(VALID_ACTIVITY_TYPES)}"
        })

    return violations


def check_research_file(file_path: str) -> list[dict]:
    """
    Check that seminar track modules have a research file.

    Research files are expected at:
        curriculum/l2-uk-en/{track}/research/{slug}-research.md

    Determines track from the file path directory (e.g., c1-bio from .../c1-bio/slug.md).

    Args:
        file_path: Path to the module .md file.

    Returns:
        List of violation dictionaries (warning level).
    """
    seminar_tracks = {'b2-hist', 'c1-hist', 'c1-bio', 'lit', 'oes', 'ruth'}

    md_path = Path(file_path)
    # Track is the parent directory name (e.g., c1-bio, b2-hist)
    track = md_path.parent.name
    if track.lower() not in seminar_tracks:
        return []

    stem = md_path.stem  # e.g., "04-radyanska-istoriohrafiia" or "radyanska-istoriohrafiia"
    research_dir = md_path.parent / "research"

    # Try exact stem match first (e.g., research/04-slug-research.md)
    research_file = research_dir / f"{stem}-research.md"
    if research_file.exists():
        return []

    # Fallback: strip number prefix (e.g., "04-slug" → "slug") and try again
    base_slug = to_bare_slug(stem)
    if base_slug != stem:
        fallback_file = research_dir / f"{base_slug}-research.md"
        if fallback_file.exists():
            return []

    return [{
        'type': 'MISSING_RESEARCH',
        'severity': 'warning',
        'message': f'No research file found for seminar module. Expected: research/{stem}-research.md',
        'fix': f'Run /full-rebuild {track} or /research to create research notes before content generation.'
    }]


def check_seminar_meta_requirements(meta_data: dict | None, level_code: str, pedagogy: str) -> list[dict]:
    """
    Validate that seminar-style modules (B2-HIST, C1, LIT) have proper Meta YAML
    and adhere to the strict schema.

    Args:
        meta_data: The loaded Meta YAML dict (or None).
        level_code: The level code (e.g., 'B2', 'C1', 'LIT').
        pedagogy: The pedagogy string (e.g., 'seminar').

    Returns:
        List of violation dictionaries.
    """
    violations = []

    # Determine if this is a seminar module
    is_seminar = pedagogy and pedagogy.lower() == 'seminar'
    is_seminar_track = level_code.lower() in ['b2-hist', 'c1-hist', 'c1-bio', 'lit']

    # If not a seminar module, we skip strict validation
    if not (is_seminar or is_seminar_track):
        return violations

    # 1. Check for Meta YAML existence
    if not meta_data:
        return [{
            'type': 'MISSING_META_YAML',
            'severity': 'critical',
            'message': 'Seminar modules REQUIRE a Meta YAML sidecar.',
            'fix': 'Create curriculum/l2-uk-en/{level}/meta/{slug}.yaml using the Seminar format.'
        }]

    # 2. Schema Validation
    schema_path = Path('schemas/meta-module.schema.json')
    if not schema_path.exists():
        return [{
            'type': 'MISSING_SCHEMA',
            'severity': 'warning',
            'message': 'Meta schema definition not found.',
            'fix': 'Ensure schemas/meta-module.schema.json exists.'
        }]

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        jsonschema.validate(instance=meta_data, schema=schema)
        
    except jsonschema.ValidationError as e:
        # Format the validation error for readability
        path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        return [{
            'type': 'INVALID_META_YAML',
            'severity': 'critical',
            'message': f"Meta YAML Schema Violation at '{path}': {e.message}",
            'fix': 'Correct the YAML structure to match schemas/meta-module.schema.json'
        }]
    except Exception as e:
        return [{
            'type': 'SCHEMA_ERROR',
            'severity': 'critical',
            'message': f"Schema validation error: {str(e)}",
            'fix': 'Check schema JSON validity.'
        }]

    # 3. Content Outline Check (Double Check)
    # The schema checks structure, but let's ensure we have valid content
    if 'content_outline' not in meta_data or not meta_data['content_outline']:
         return [{
            'type': 'EMPTY_OUTLINE',
            'severity': 'critical',
            'message': 'Seminar modules must have a defined content_outline.',
            'fix': 'Add sections to content_outline in YAML.'
        }]

    return violations
