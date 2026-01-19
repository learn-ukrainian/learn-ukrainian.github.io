"""
Meta YAML validation checks.
Enforces strict metadata requirements for Seminar-style modules.
"""

import json
import os
from pathlib import Path
import jsonschema

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
