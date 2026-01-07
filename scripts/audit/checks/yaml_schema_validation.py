"""
YAML Activity Schema Validation

Validates activity YAML files against the JSON schemas defined in schemas/activities-*.schema.json.
Catches non-conforming activity formats during the audit workflow.

Issue: #397
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

import yaml


# =============================================================================
# SCHEMA LOADING
# =============================================================================

def get_schemas_dir() -> Path:
    """Get the schemas directory path."""
    return Path(__file__).parent.parent.parent.parent / "schemas"


def load_base_schema() -> Dict:
    """Load the base activities schema with all activity type definitions."""
    schema_path = get_schemas_dir() / "activities-base.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_activity_schema(activity_type: str, base_schema: Dict) -> Optional[Dict]:
    """Get the schema definition for a specific activity type."""
    definitions = base_schema.get('definitions', {})
    return definitions.get(activity_type)


# =============================================================================
# VALIDATION
# =============================================================================

def validate_activity(activity: Dict, base_schema: Dict) -> List[str]:
    """
    Validate a single activity against its schema.
    
    Returns a list of validation error messages (empty if valid).
    """
    errors = []
    
    if not HAS_JSONSCHEMA:
        return ["jsonschema library not installed - cannot validate schemas"]
    
    activity_type = activity.get('type')
    if not activity_type:
        return ["Activity missing 'type' field"]
    
    # Get schema for this activity type
    type_schema = get_activity_schema(activity_type, base_schema)
    if not type_schema:
        # Unknown type - might be valid but not in base schema
        return [f"Unknown activity type: '{activity_type}' (not in schema)"]
    
    # Validate against the schema
    try:
        jsonschema.validate(instance=activity, schema=type_schema)
    except jsonschema.ValidationError as e:
        # Extract the most useful error message
        if e.path:
            path = '.'.join(str(p) for p in e.path)
            errors.append(f"{activity_type}: '{path}' - {e.message}")
        else:
            errors.append(f"{activity_type}: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error for {activity_type}: {e.message}")
    
    return errors


def validate_activity_yaml_file(yaml_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate all activities in a YAML file against the schema.
    
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if not yaml_path.exists():
        return True, []  # No YAML file is OK (module might use embedded activities)
    
    # Load base schema
    try:
        base_schema = load_base_schema()
    except FileNotFoundError as e:
        return False, [str(e)]
    
    # Load activities from YAML
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]
    
    if not data:
        return True, []
    
    # Handle both formats: list of activities or dict with 'activities' key
    activities = data if isinstance(data, list) else data.get('activities', [])
    
    if not isinstance(activities, list):
        return False, ["Invalid YAML structure: expected list of activities"]
    
    # Validate each activity
    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            errors.append(f"Activity {i}: not a dictionary")
            continue
        
        activity_errors = validate_activity(activity, base_schema)
        for err in activity_errors:
            activity_id = activity.get('id', f'index-{i}')
            activity_title = activity.get('title', '')[:30]
            errors.append(f"[{activity_id}] {err}")
    
    return len(errors) == 0, errors


# =============================================================================
# AUDIT CHECK FUNCTION
# =============================================================================

def check_activity_yaml_schema(
    file_path: str,
    level: str,
    module_num: int,
) -> List[Dict]:
    """
    Check that activity YAML files conform to the JSON schema.
    
    This is the main entry point called by the audit system.
    
    Returns list of violation dicts with 'type', 'message', 'severity'.
    """
    violations = []
    
    if not HAS_JSONSCHEMA:
        # Warn but don't fail if jsonschema not installed
        violations.append({
            'type': 'SCHEMA_CHECK_SKIPPED',
            'message': 'jsonschema library not installed. Run: pip install jsonschema',
            'severity': 'warning'
        })
        return violations
    
    # Find the activities YAML file
    md_path = Path(file_path)
    slug = md_path.stem
    activities_dir = md_path.parent / "activities"
    yaml_path = activities_dir / f"{slug}.yaml"
    
    if not yaml_path.exists():
        # No YAML file - that's OK, module might use embedded activities
        return []
    
    # Validate
    is_valid, errors = validate_activity_yaml_file(yaml_path)
    
    for error in errors:
        violations.append({
            'type': 'YAML_SCHEMA_VIOLATION',
            'message': f"Schema error in {yaml_path.name}: {error}",
            'severity': 'error',
        })
    
    return violations


__all__ = [
    'check_activity_yaml_schema',
    'validate_activity_yaml_file',
    'validate_activity',
]
