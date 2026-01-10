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

    # Custom validation for cloze activities
    if activity_type == 'cloze':
        passage = activity.get('passage', '')
        has_blanks_array = 'blanks' in activity
        has_curly_braces = '{' in passage
        has_pipe_format = '|' in passage

        if has_curly_braces and not has_blanks_array and not has_pipe_format:
            # Passage has {word} markers but no way to present options
            errors.append(f"cloze: passage has {{word}} markers but no 'blanks' array or '|' options format")
        elif has_curly_braces and not has_pipe_format and has_blanks_array:
            # Has blanks array - markers should be {1}, {2}, etc.
            markers = re.findall(r'\{([^}]+)\}', passage)
            non_numeric = [m for m in markers if not m.isdigit()]
            if non_numeric:
                errors.append(f"cloze: when using 'blanks' array, passage markers must be {{1}}, {{2}}, etc. (not words)")

    return errors


def validate_activity_yaml_file(yaml_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate all activities in a YAML file against the schema.

    Returns (is_valid, list_of_errors).
    """
    errors = []

    if not yaml_path.exists():
        return True, []  # No YAML file is OK (module might use embedded activities)

    # Detect level from path to load correct schema
    level_match = None
    for parent in yaml_path.parents:
        if parent.name in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
            level_match = parent.name
            break

    # Load level-specific schema (has minItems constraint)
    level_schema = None
    if level_match:
        if level_match in ['a1', 'a2']:
            schema_path = get_schemas_dir() / f"activities-{level_match}.schema.json"
        else:
            # B1, B2, C1, C2 all use activities-b1.schema.json
            schema_path = get_schemas_dir() / "activities-b1.schema.json"

        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                level_schema = json.load(f)

    # Load base schema for individual activity validation
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

    # FIRST: Validate entire array against level schema (checks minItems, etc.)
    if level_schema:
        try:
            jsonschema.validate(instance=activities, schema=level_schema)
        except jsonschema.ValidationError as e:
            # Array-level validation error (e.g., too few items)
            # Format concise error messages
            if "too short" in e.message.lower():
                min_items = level_schema.get('minItems', 'N/A')
                errors.append(f"Insufficient activities: {len(activities)} found, minimum {min_items} required for {level_match.upper()}")
            else:
                errors.append(f"Array validation: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")

    # SECOND: Validate each activity individually
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


# =============================================================================
# AUTO-FIX FUNCTIONS
# =============================================================================

def fix_activity_violations(activity: Dict, base_schema: Dict) -> Tuple[bool, List[str]]:
    """
    Automatically fix common YAML schema violations in an activity.

    Returns (was_modified, list_of_fixes_applied).
    """
    fixes = []
    modified = False
    activity_type = activity.get('type', 'unknown')

    # Get schema for this activity type
    type_schema = get_activity_schema(activity_type, base_schema)
    if not type_schema:
        return False, []

    # Fix 1: Remove 'id' property if not allowed in schema
    allowed_properties = type_schema.get('properties', {}).keys()
    if 'id' in activity and 'id' not in allowed_properties:
        del activity['id']
        fixes.append(f"Removed invalid 'id' property from {activity_type}")
        modified = True

    # Fix 2: mark-the-words - extract correct_words from passage
    if activity_type == 'mark-the-words':
        if 'passage' in activity and 'correct_words' not in activity:
            passage = activity['passage']
            # Extract words marked with *asterisks*
            import re
            marked_words = re.findall(r'\*([^\*]+)\*', passage)
            if marked_words:
                activity['correct_words'] = marked_words
                fixes.append(f"Added correct_words extracted from passage ({len(marked_words)} words)")
                modified = True

    # Fix 3: unjumble - convert scrambled to words array
    if activity_type == 'unjumble' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                # Remove scrambled property if exists alongside words
                if 'scrambled' in item and 'words' in item:
                    del item['scrambled']
                    fixes.append(f"Removed duplicate 'scrambled' property from unjumble item {i+1}")
                    modified = True
                # Convert scrambled to words if words missing
                elif 'scrambled' in item and 'words' not in item:
                    scrambled = item['scrambled']
                    # Split by ' / ' or whitespace
                    if ' / ' in scrambled:
                        words = [w.strip() for w in scrambled.split(' / ')]
                    else:
                        words = scrambled.split()
                    item['words'] = words
                    del item['scrambled']
                    fixes.append(f"Converted 'scrambled' to 'words' array in unjumble item {i+1}")
                    modified = True

    # Fix 4: translate - ensure source property exists
    if activity_type == 'translate' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict) and 'source' not in item:
                # Try to extract source from context or first option
                if 'options' in item and item['options']:
                    # Use question field if it exists
                    if 'question' in item:
                        item['source'] = item['question']
                        fixes.append(f"Added 'source' from 'question' in translate item {i+1}")
                        modified = True

    # Fix 5: quiz/select - ensure question property exists
    if activity_type in ['quiz', 'select'] and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict) and 'question' not in item:
                # Try to use prompt or text field
                if 'prompt' in item:
                    item['question'] = item['prompt']
                    del item['prompt']
                    fixes.append(f"Renamed 'prompt' to 'question' in {activity_type} item {i+1}")
                    modified = True
                elif 'text' in item:
                    item['question'] = item['text']
                    del item['text']
                    fixes.append(f"Renamed 'text' to 'question' in {activity_type} item {i+1}")
                    modified = True

    # Fix 6: Remove 'instruction' if it's not in the schema properties
    # (Some old YAMLs have this, but it's now part of the schema)
    # Actually, instruction IS valid now, so skip this fix

    return modified, fixes


def fix_yaml_file(yaml_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Auto-fix schema violations in a YAML activity file.

    Args:
        yaml_path: Path to the YAML file
        dry_run: If True, only report fixes without saving

    Returns (num_fixes_applied, list_of_fix_messages).
    """
    all_fixes = []
    total_fixes = 0

    if not yaml_path.exists():
        return 0, []

    # Load base schema
    try:
        base_schema = load_base_schema()
    except FileNotFoundError as e:
        return 0, [f"Schema not found: {e}"]

    # Load activities from YAML
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return 0, [f"YAML parse error (cannot auto-fix): {e}"]

    if not data:
        return 0, []

    # Handle both formats
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
        root_is_dict = True
    elif isinstance(data, list):
        activities = data
        root_is_dict = False
    else:
        return 0, ["Invalid YAML structure"]

    # Fix each activity
    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            continue

        modified, fixes = fix_activity_violations(activity, base_schema)
        if modified:
            total_fixes += len(fixes)
            activity_title = activity.get('title', f'Activity {i+1}')[:40]
            all_fixes.append(f"[{i+1}] {activity_title}:")
            for fix in fixes:
                all_fixes.append(f"    ✓ {fix}")

    # Save if modifications were made and not dry run
    if total_fixes > 0 and not dry_run:
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                if root_is_dict:
                    yaml.dump({'activities': activities}, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)
                else:
                    yaml.dump(activities, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)
            all_fixes.insert(0, f"✅ Saved {total_fixes} fixes to {yaml_path.name}")
        except Exception as e:
            all_fixes.insert(0, f"❌ Error saving fixes: {e}")
            return 0, all_fixes
    elif total_fixes > 0 and dry_run:
        all_fixes.insert(0, f"🔍 DRY RUN: Would apply {total_fixes} fixes to {yaml_path.name}")

    return total_fixes, all_fixes


__all__ = [
    'check_activity_yaml_schema',
    'validate_activity_yaml_file',
    'validate_activity',
    'fix_activity_violations',
    'fix_yaml_file',
]
