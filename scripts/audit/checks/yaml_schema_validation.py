"""
YAML Activity Schema Validation

Validates activity YAML files against the JSON schemas defined in schemas/activities-*.schema.json.
Catches non-conforming activity formats during the audit workflow.

Issue: #397
"""

import json
import re
from pathlib import Path
from typing import Any

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

import yaml

# =============================================================================
# DUPLICATE KEY DETECTION
# =============================================================================

class DuplicateKeyError(Exception):
    """Raised when duplicate keys are found in YAML."""
    pass


class DuplicateKeyLoader(yaml.SafeLoader):
    """Custom YAML loader that detects duplicate keys."""
    pass


def _construct_mapping_with_duplicate_check(loader, node):
    """Construct a mapping while checking for duplicate keys."""
    loader.flatten_mapping(node)
    pairs = []
    seen_keys = {}
    duplicates = []

    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)

        if key in seen_keys:
            # Record the duplicate with line numbers
            original_line = seen_keys[key]
            duplicate_line = key_node.start_mark.line + 1  # 1-indexed
            duplicates.append((key, original_line, duplicate_line))
        else:
            seen_keys[key] = key_node.start_mark.line + 1  # 1-indexed

        value = loader.construct_object(value_node, deep=False)
        pairs.append((key, value))

    if duplicates:
        # Store duplicates for later reporting (attach to loader)
        if not hasattr(loader, '_duplicates'):
            loader._duplicates = []
        loader._duplicates.extend(duplicates)

    return dict(pairs)


# Register the custom constructor
DuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_with_duplicate_check
)


def safe_load_with_duplicate_check(content: str) -> tuple[Any, list[str]]:
    """
    Load YAML content and check for duplicate keys.

    Returns:
        Tuple of (parsed_data, list_of_duplicate_key_errors)
    """
    errors = []
    loader = DuplicateKeyLoader(content)
    try:
        data = loader.get_single_data()

        # Collect any duplicates found
        if hasattr(loader, '_duplicates'):
            for key, line1, line2 in loader._duplicates:
                errors.append(
                    f"Duplicate key '{key}' at line {line2} (first defined at line {line1})"
                )
    finally:
        loader.dispose()

    return data, errors


# =============================================================================
# SCHEMA LOADING
# =============================================================================

def get_schemas_dir() -> Path:
    """Get the schemas directory path."""
    return Path(__file__).parent.parent.parent.parent / "schemas"


def load_base_schema() -> dict:
    """Load the base activities schema with all activity type definitions.

    Tries V2 schema first (activity-v2.schema.json), falls back to V1
    (activities-base.schema.json) for backward compatibility.
    """
    v2_path = get_schemas_dir() / "activity-v2.schema.json"
    v1_path = get_schemas_dir() / "activities-base.schema.json"

    schema_path = v2_path if v2_path.exists() else v1_path
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {v1_path}")

    with open(schema_path, encoding='utf-8') as f:
        return json.load(f)


def get_activity_schema(activity_type: str, base_schema: dict) -> dict | None:
    """Get the schema definition for a specific activity type.

    Checks for track-specific definitions first (e.g., reading-istorio),
    then falls back to the base type name (e.g., reading).
    """
    definitions = base_schema.get('$defs', base_schema.get('definitions', {}))
    # Track-specific schemas name definitions as "type-track" (e.g., "reading-istorio")
    # Try all keys that start with the activity type and pick the first match
    for key in definitions:
        if key.startswith(f"{activity_type}-"):
            return definitions[key]
    return definitions.get(activity_type)


# =============================================================================
# ERROR MESSAGE ENHANCEMENT
# =============================================================================

def generate_actionable_error(
    activity: dict,
    error: 'jsonschema.ValidationError',
    type_schema: dict,
    activity_index: int | None = None
) -> str:
    """
    Generate an actionable, human-friendly error message from a schema validation error.

    Includes:
    - Activity context (index, type, title)
    - Clear explanation
    - Example fix from schema
    - Documentation link
    """
    activity_type = activity.get('type', 'unknown')
    activity_title = activity.get('title', 'Untitled')

    # Build activity identifier
    activity_id = "Activity"
    if activity_index is not None:
        activity_id = f"Activity #{activity_index + 1}"
    activity_id += f" ({activity_type})"
    if activity_title and activity_title != 'Untitled':
        # Truncate long titles
        display_title = activity_title[:40] + '...' if len(activity_title) > 40 else activity_title
        activity_id += f' "{display_title}"'

    # Extract error details
    error_path = '.'.join(str(p) for p in error.path) if error.path else ''
    error_message = error.message

    # Build the error message parts
    parts = [f"\n{activity_id}:"]
    parts.append(f"  ❌ {error_message}")

    # Add context about what field/path failed
    if error_path:
        parts.append(f"  📍 At: {error_path}")

    # Generate helpful explanation based on error type
    if "'items' is a required property" in error_message or "'pairs' is a required property" in error_message:
        # Missing required field
        required_fields = type_schema.get('required', [])
        parts.append(f"  💡 {activity_type} requires: {', '.join(required_fields)}")
    elif "is a required property" in error_message:
        # Generic required property
        missing_field = error_message.split("'")[1] if "'" in error_message else "field"
        parts.append(f"  💡 Required field '{missing_field}' is missing")
    elif "Additional properties are not allowed" in error_message:
        # Extra field that shouldn't be there
        parts.append("  💡 Remove unexpected properties or check for typos in field names")
    elif "is not of type" in error_message:
        # Wrong type
        parts.append(f"  💡 Check the data type - expected {error.schema.get('type', 'unknown')}")

    # Add example fix for common errors
    example = _generate_example_fix(activity_type, error, type_schema)
    if example:
        parts.append("\n  Example fix:")
        for line in example.split('\n'):
            parts.append(f"  {line}")

    # Add documentation link
    doc_anchor = activity_type.lower()
    parts.append(f"\n  📖 See: docs/ACTIVITY-YAML-REFERENCE.md#{doc_anchor}")

    return '\n'.join(parts)


def _generate_example_fix(activity_type: str, error: 'jsonschema.ValidationError', type_schema: dict) -> str | None:
    """Generate a minimal example fix for common schema errors."""

    # For missing required fields, show minimal valid structure
    if "is a required property" in error.message:
        examples = {
            'quiz': """- type: quiz
  title: "Your quiz title"
  items:
    - question: "Question text?"
      options:
        - text: "Option 1"
          correct: true
        - text: "Option 2"
          correct: false""",

            'match-up': """- type: match-up
  title: "Your match-up title"
  pairs:
    - left: "Item 1"
      right: "Match 1"
    - left: "Item 2"
      right: "Match 2" """,

            'fill-in': """- type: fill-in
  title: "Your fill-in title"
  items:
    - sentence: "Київ — {столиця} України."
      answer: "столиця" """,

            'group-sort': """- type: group-sort
  title: "Your group-sort title"
  groups:
    - name: "Group 1"
      items: ["Item A", "Item B"]
    - name: "Group 2"
      items: ["Item C", "Item D"]""",

            'cloze': """- type: cloze
  title: "Your cloze title"
  passage: "Text with {blank1} and {blank2} to fill."
  blanks:
    - options: ["correct", "wrong1", "wrong2"]
    - options: ["correct", "wrong1", "wrong2"]""",
        }

        return examples.get(activity_type)

    return None


# =============================================================================
# VALIDATION
# =============================================================================

def validate_activity(activity: dict, base_schema: dict, activity_index: int | None = None) -> list[str]:
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
        # Generate actionable, human-friendly error message
        actionable_error = generate_actionable_error(activity, e, type_schema, activity_index)
        errors.append(actionable_error)
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error for {activity_type}: {e.message}")

    # Custom validation for cloze activities
    if activity_type == 'cloze':
        passage = activity.get('passage', '')
        has_blanks_array = 'blanks' in activity
        has_curly_braces = '{' in passage
        has_pipe_format = '|' in passage

        # Check for blank lines in passage (causes MDX/HTML rendering issues)
        if '\n\n' in passage:
            errors.append("cloze: passage contains blank lines (\\n\\n) which break MDX rendering. Use single newlines only.")

        # Check for full-sentence options in cloze blanks (indicates wrong activity type)
        if has_curly_braces and has_pipe_format:
            blanks = re.findall(r'\{([^}]+)\}', passage)
            for blank_idx, blank_content in enumerate(blanks):
                options = [opt.strip() for opt in blank_content.split('|')]
                for option in options:
                    # Skip placeholders
                    if option in ['--', '-', ''] or len(option) < 3:
                        continue
                    # Full sentences with ? or ! are strong signals of misuse
                    if option.rstrip().endswith('?') or option.rstrip().endswith('!'):
                        errors.append(f"cloze: blank #{blank_idx + 1} has sentence options ending in '?' or '!' - this should be a 'select' activity, not cloze")
                        break  # One error per blank is enough
                    # Very long options (>35 chars) likely indicate full sentences
                    if len(option) > 35:
                        errors.append(f"cloze: blank #{blank_idx + 1} has very long options (>35 chars) - consider using 'select' activity instead")
                        break

        if has_curly_braces and not has_blanks_array and not has_pipe_format:
            # Passage has {word} markers but no way to present options
            errors.append("cloze: passage has {word} markers but no 'blanks' array or '|' options format")
        elif has_curly_braces and not has_pipe_format and has_blanks_array:
            # Has blanks array - markers should be {1}, {2}, etc.
            markers = re.findall(r'\{([^}]+)\}', passage)
            non_numeric = [m for m in markers if not m.isdigit()]
            if non_numeric:
                errors.append("cloze: when using 'blanks' array, passage markers must be {1}, {2}, etc. (not words)")

    return errors


def validate_activity_yaml_file(yaml_path: Path) -> tuple[bool, list[str]]:
    """
    Validate all activities in a YAML file against the schema.

    Returns (is_valid, list_of_errors).
    """
    errors = []

    if not yaml_path.exists():
        return True, []  # No YAML file is OK (module might use embedded activities)

    # Detect level from path to load correct schema
    # Includes track levels: lit, hist, bio, b2-pro, c1-pro
    level_match = None
    for parent in yaml_path.parents:
        if parent.name in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit', 'hist', 'bio', 'istorio', 'oes', 'ruth', 'b2-pro', 'c1-pro']:
            level_match = parent.name
            break

    # Load level-specific schema (has minItems constraint)
    level_schema = None
    if level_match:
        # Check for level-specific schema (e.g., activities-c1.schema.json)
        schema_path = get_schemas_dir() / f"activities-{level_match}.schema.json"

        # Fallback to B1 schema if specific one doesn't exist (B1 is the baseline for B1+)
        if not schema_path.exists():
            schema_path = get_schemas_dir() / "activities-b1.schema.json"

        if schema_path.exists():
            with open(schema_path, encoding='utf-8') as f:
                level_schema = json.load(f)

    # Load base schema for individual activity validation
    try:
        base_schema = load_base_schema()
    except FileNotFoundError as e:
        return False, [str(e)]

    # Load activities from YAML with duplicate key detection
    try:
        with open(yaml_path, encoding='utf-8') as f:
            content = f.read()
        data, duplicate_errors = safe_load_with_duplicate_check(content)

        # Report duplicate keys as errors (these are serious issues)
        if duplicate_errors:
            errors.extend(duplicate_errors)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    if not data:
        return len(errors) == 0, errors

    # Handle multiple formats:
    # V1: bare list of activities at root
    # V1b: dict with 'activities' key wrapping a list
    # V2: dict with 'version', 'module', 'inline', 'workbook' keys (activity-v2.schema.json)
    if isinstance(data, dict) and ('inline' in data or 'workbook' in data):
        # V2 format: merge inline + workbook into single list for validation
        activities = []
        for section in ('inline', 'workbook'):
            section_data = data.get(section, [])
            if isinstance(section_data, list):
                activities.extend(section_data)
    elif isinstance(data, dict) and 'activities' in data:
        activities = data.get('activities', [])
        errors.append(
            "⚠️ YAML uses dictionary wrapper (`activities:` key). "
            "Activities MUST be a bare list at root level. "
            "Run auto-fix: .venv/bin/python scripts/audit_module.py --fix <file.md>"
        )
    elif isinstance(data, list):
        activities = data
    else:
        return False, ["Invalid YAML structure: expected list of activities"]

    # FIRST: Validate entire array against level schema (checks minItems, etc.)
    if level_schema:
        try:
            jsonschema.validate(instance=activities, schema=level_schema)
        except jsonschema.ValidationError as e:
            # Array-level validation error (e.g., too few items)
            # Format concise error messages
            # Array-level validation error (e.g., too few items)
            # Format concise error messages
            if "too short" in e.message.lower() and len(e.path) == 0:
                min_items = level_schema.get('minItems', 'N/A')
                errors.append(f"Insufficient activities: {len(activities)} found, minimum {min_items} required for {level_match.upper()}")
            else:
                path_str = f" at key '{e.path[-1]}'" if e.path else ""
                errors.append(f"Schema validation error{path_str}: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")

    # SECOND: Validate each activity individually ONLY if no level schema
    # If level schema exists and validated, it already covers individual activities
    # with level-specific definitions (e.g., LIT has source_reading, reading without resource)
    if not level_schema:
        for i, activity in enumerate(activities):
            if not isinstance(activity, dict):
                errors.append(f"Activity {i}: not a dictionary")
                continue

            activity_errors = validate_activity(activity, base_schema, activity_index=i)
            for err in activity_errors:
                # Errors are now self-contained with context, don't add prefix
                errors.append(err)

    return len(errors) == 0, errors


# =============================================================================
# AUDIT CHECK FUNCTION
# =============================================================================

def check_activity_yaml_schema(
    file_path: str,
    level: str,
    module_num: int,
) -> list[dict]:
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
    _is_valid, errors = validate_activity_yaml_file(yaml_path)

    for error in errors:
        violations.append({
            'type': 'YAML_SCHEMA_VIOLATION',
            'message': f"Schema error in {yaml_path.name}: {error}",
            'severity': 'error',
        })

    return violations


# Auto-fix functions are in yaml_schema_fixes.py but re-exported here
# for backward compatibility. Import lazily to avoid circular imports.
def fix_raw_yaml_text(content):
    """Re-export from yaml_schema_fixes."""
    from .yaml_schema_fixes import fix_raw_yaml_text as _fn
    return _fn(content)

def fix_yaml_file(yaml_path, dry_run=False):
    """Re-export from yaml_schema_fixes."""
    from .yaml_schema_fixes import fix_yaml_file as _fn
    return _fn(yaml_path, dry_run)

def remove_forbidden_activities(yaml_path, level_code, module_focus=None, dry_run=False):
    """Re-export from yaml_schema_fixes."""
    from .yaml_schema_fixes import remove_forbidden_activities as _fn
    return _fn(yaml_path, level_code, module_focus, dry_run)


# =============================================================================
# PLAN / META / VOCABULARY SCHEMA CHECK FUNCTIONS
# =============================================================================

def _validate_yaml_against_schema(yaml_path: Path, schema_name: str) -> list[str]:
    """
    Generic helper: load a YAML file and validate it against a named JSON schema.

    Returns list of error strings (empty = valid).
    """
    if not HAS_JSONSCHEMA:
        return []

    if not yaml_path.exists():
        return []

    schema_path = get_schemas_dir() / schema_name
    if not schema_path.exists():
        return [f"Schema not found: {schema_path}"]

    with open(schema_path, encoding='utf-8') as f:
        schema = json.load(f)

    try:
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if data is None:
        return [f"File is empty: {yaml_path}"]

    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        field_path = '.'.join(str(p) for p in e.absolute_path) if e.absolute_path else '(root)'
        errors.append(f"{field_path}: {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")

    return errors


def check_plan_yaml_schema(
    file_path: str,
    level: str,
    module_num: int,
) -> list[dict]:
    """
    Check that a plan YAML file conforms to module-plan.schema.json.

    Returns list of violation dicts with 'type', 'message', 'severity'.
    """
    violations = []

    if not HAS_JSONSCHEMA:
        violations.append({
            'type': 'SCHEMA_CHECK_SKIPPED',
            'message': 'jsonschema library not installed. Run: pip install jsonschema',
            'severity': 'warning'
        })
        return violations

    yaml_path = Path(file_path)
    if not yaml_path.exists():
        return []

    errors = _validate_yaml_against_schema(yaml_path, 'module-plan.schema.json')

    for error in errors:
        violations.append({
            'type': 'PLAN_SCHEMA_VIOLATION',
            'message': f"Schema error in {yaml_path.name}: {error}",
            'severity': 'error',
        })

    return violations


def check_meta_yaml_schema(
    file_path: str,
    level: str,
    module_num: int,
) -> list[dict]:
    """
    Check that a meta YAML file conforms to meta-module.schema.json.

    Returns list of violation dicts with 'type', 'message', 'severity'.
    """
    violations = []

    if not HAS_JSONSCHEMA:
        violations.append({
            'type': 'SCHEMA_CHECK_SKIPPED',
            'message': 'jsonschema library not installed. Run: pip install jsonschema',
            'severity': 'warning'
        })
        return violations

    yaml_path = Path(file_path)
    if not yaml_path.exists():
        return []

    errors = _validate_yaml_against_schema(yaml_path, 'meta-module.schema.json')

    for error in errors:
        violations.append({
            'type': 'META_SCHEMA_VIOLATION',
            'message': f"Schema error in {yaml_path.name}: {error}",
            'severity': 'error',
        })

    return violations


def check_vocabulary_yaml_schema(
    file_path: str,
    level: str,
    module_num: int,
) -> list[dict]:
    """
    Check that a vocabulary YAML file conforms to vocabulary.schema.json.

    Returns list of violation dicts with 'type', 'message', 'severity'.
    """
    violations = []

    if not HAS_JSONSCHEMA:
        violations.append({
            'type': 'SCHEMA_CHECK_SKIPPED',
            'message': 'jsonschema library not installed. Run: pip install jsonschema',
            'severity': 'warning'
        })
        return violations

    yaml_path = Path(file_path)
    if not yaml_path.exists():
        return []

    errors = _validate_yaml_against_schema(yaml_path, 'vocabulary.schema.json')

    for error in errors:
        violations.append({
            'type': 'VOCABULARY_SCHEMA_VIOLATION',
            'message': f"Schema error in {yaml_path.name}: {error}",
            'severity': 'error',
        })

    return violations


__all__ = [
    'check_activity_yaml_schema',
    'check_meta_yaml_schema',
    'check_plan_yaml_schema',
    'check_vocabulary_yaml_schema',
    'fix_raw_yaml_text',
    'fix_yaml_file',
    'remove_forbidden_activities',
    'validate_activity',
    'validate_activity_yaml_file',
]
