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


def safe_load_with_duplicate_check(content: str) -> Tuple[Any, List[str]]:
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
# ERROR MESSAGE ENHANCEMENT
# =============================================================================

def generate_actionable_error(
    activity: Dict,
    error: 'jsonschema.ValidationError',
    type_schema: Dict,
    activity_index: Optional[int] = None
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
    activity_id = f"Activity"
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
        parts.append(f"  💡 Remove unexpected properties or check for typos in field names")
    elif "is not of type" in error_message:
        # Wrong type
        parts.append(f"  💡 Check the data type - expected {error.schema.get('type', 'unknown')}")

    # Add example fix for common errors
    example = _generate_example_fix(activity_type, error, type_schema)
    if example:
        parts.append(f"\n  Example fix:")
        for line in example.split('\n'):
            parts.append(f"  {line}")

    # Add documentation link
    doc_anchor = activity_type.lower()
    parts.append(f"\n  📖 See: docs/ACTIVITY-YAML-REFERENCE.md#{doc_anchor}")

    return '\n'.join(parts)


def _generate_example_fix(activity_type: str, error: 'jsonschema.ValidationError', type_schema: Dict) -> Optional[str]:
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

def validate_activity(activity: Dict, base_schema: Dict, activity_index: Optional[int] = None) -> List[str]:
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
            errors.append(f"cloze: passage contains blank lines (\\n\\n) which break MDX rendering. Use single newlines only.")

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
    # Includes track levels: lit, b2-hist, c1-bio, b2-pro, c1-pro
    level_match = None
    for parent in yaml_path.parents:
        if parent.name in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit', 'b2-hist', 'c1-bio', 'c1-hist', 'oes', 'ruth', 'b2-pro', 'c1-pro']:
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
            with open(schema_path, 'r', encoding='utf-8') as f:
                level_schema = json.load(f)

    # Load base schema for individual activity validation
    try:
        base_schema = load_base_schema()
    except FileNotFoundError as e:
        return False, [str(e)]

    # Load activities from YAML with duplicate key detection
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        data, duplicate_errors = safe_load_with_duplicate_check(content)

        # Report duplicate keys as errors (these are serious issues)
        if duplicate_errors:
            errors.extend(duplicate_errors)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    if not data:
        return len(errors) == 0, errors

    # Handle both formats: list of activities or dict with 'activities' key
    if isinstance(data, dict) and 'activities' in data:
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

    # Fix 1b: Remove 'question' property if not allowed at activity level
    # (Some B2 modules have 'question' at top level instead of 'title')
    if 'question' in activity and 'question' not in allowed_properties:
        # Keep the value if it's the only description
        if 'title' not in activity:
            activity['title'] = activity['question']
            fixes.append(f"Renamed 'question' to 'title' in {activity_type}")
        del activity['question']
        fixes.append(f"Removed invalid 'question' property from {activity_type}")
        modified = True

    # Fix 1c: Remove 'text' property if not allowed at activity level
    if 'text' in activity and 'text' not in allowed_properties:
        del activity['text']
        fixes.append(f"Removed invalid 'text' property from {activity_type}")
        modified = True

    # Fix 2: mark-the-words - extract answers from text if marked with *asterisks*
    if activity_type == 'mark-the-words':
        if 'text' in activity and 'answers' not in activity:
            text = activity['text']
            # Extract words marked with *asterisks* (if any)
            import re
            marked_words = re.findall(r'\*([^\*]+)\*', text)
            if marked_words:
                activity['answers'] = marked_words
                # Remove asterisks from text
                activity['text'] = re.sub(r'\*([^\*]+)\*', r'\1', text)
                fixes.append(f"Extracted answers from text ({len(marked_words)} words)")
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

    # Fix 4: translate - ensure source property exists and restructure if needed
    if activity_type == 'translate' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                # Rename question → source (or delete question if source already exists)
                if 'question' in item:
                    if 'source' not in item:
                        item['source'] = item['question']
                        fixes.append(f"Renamed 'question' to 'source' in translate item {i+1}")
                    del item['question']
                    fixes.append(f"Removed invalid 'question' from translate item {i+1}")
                    modified = True
                # Convert answer → options array (single correct option)
                if 'answer' in item and 'options' not in item:
                    item['options'] = [{'text': str(item['answer']), 'correct': True}]
                    del item['answer']
                    fixes.append(f"Converted 'answer' to 'options' array in translate item {i+1}")
                    modified = True
                # Ensure options items have string text (not numbers)
                if 'options' in item:
                    for opt in item['options']:
                        if isinstance(opt, dict) and 'text' in opt and not isinstance(opt['text'], str):
                            opt['text'] = str(opt['text'])
                            fixes.append(f"Converted option text to string in translate item {i+1}")
                            modified = True

    # Fix 5: quiz/select - ensure question property exists and type coercion
    if activity_type in ['quiz', 'select'] and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                if 'question' not in item:
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
                # Type coercion for options
                if 'options' in item:
                    for opt in item['options']:
                        if isinstance(opt, dict) and 'text' in opt and not isinstance(opt['text'], str):
                            opt['text'] = str(opt['text'])
                            fixes.append(f"Converted option text to string in {activity_type} item {i+1}")
                            modified = True

    # Fix 5b: quiz/select - add missing correct:false to options
    if activity_type in ['quiz', 'select'] and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict) and 'options' in item:
                options_fixed = 0
                for opt in item['options']:
                    if isinstance(opt, dict) and 'correct' not in opt:
                        opt['correct'] = False
                        options_fixed += 1
                if options_fixed > 0:
                    fixes.append(f"Added 'correct: false' to {options_fixed} options in {activity_type} item {i+1}")
                    modified = True

    # Fix 5c: match-up - type coercion for pairs
    if activity_type == 'match-up' and 'pairs' in activity:
        for i, pair in enumerate(activity['pairs']):
            if isinstance(pair, dict):
                if 'left' in pair and not isinstance(pair['left'], str):
                    pair['left'] = str(pair['left'])
                    fixes.append(f"Converted pair left to string in match-up pair {i+1}")
                    modified = True
                if 'right' in pair and not isinstance(pair['right'], str):
                    pair['right'] = str(pair['right'])
                    fixes.append(f"Converted pair right to string in match-up pair {i+1}")
                    modified = True

    # Fix 6: true-false - rename text→statement, answer→correct
    if activity_type == 'true-false' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                if 'text' in item and 'statement' not in item:
                    item['statement'] = item['text']
                    del item['text']
                    fixes.append(f"Renamed 'text' to 'statement' in true-false item {i+1}")
                    modified = True
                if 'answer' in item and 'correct' not in item:
                    item['correct'] = item['answer']
                    del item['answer']
                    fixes.append(f"Renamed 'answer' to 'correct' in true-false item {i+1}")
                    modified = True

    # Fix 7: fill-in - rename text→sentence
    if activity_type == 'fill-in' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                if 'text' in item and 'sentence' not in item:
                    item['sentence'] = item['text']
                    del item['text']
                    fixes.append(f"Renamed 'text' to 'sentence' in fill-in item {i+1}")
                    modified = True

    # Fix 8: error-correction - ensure sentence property exists and type coercion
    if activity_type == 'error-correction' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                if 'text' in item and 'sentence' not in item:
                    item['sentence'] = item['text']
                    del item['text']
                    fixes.append(f"Renamed 'text' to 'sentence' in error-correction item {i+1}")
                    modified = True
                # If 'error' is used as the full sentence (schema requires both 'sentence' AND 'error')
                elif 'error' in item and 'sentence' not in item:
                    # Copy error to sentence (both are required, error should stay as error word)
                    item['sentence'] = item['error']
                    fixes.append(f"Copied 'error' to 'sentence' in error-correction item {i+1}")
                    modified = True
                # Type coercion for answer
                if 'answer' in item and not isinstance(item['answer'], str):
                    item['answer'] = str(item['answer'])
                    fixes.append(f"Converted answer to string in error-correction item {i+1}")
                    modified = True

    # Fix 9: group-sort - rename title→name in groups
    if activity_type == 'group-sort' and 'groups' in activity:
        for group in activity['groups']:
            if isinstance(group, dict):
                if 'title' in group and 'name' not in group:
                    group['name'] = group['title']
                    del group['title']
                    fixes.append(f"Renamed 'title' to 'name' in group-sort group")
                    modified = True

    # Fix 10: select - try property renames only (structural fixes need manual review)
    # Note: flat format (items with question+correct bool) vs proper format (items with question+options array)
    # are semantically different. Flat format needs manual regeneration, not auto-fix.
    if activity_type == 'select' and 'items' in activity:
        for i, item in enumerate(activity['items']):
            if isinstance(item, dict):
                # Only try simple property renames if 'options' exists
                if 'options' not in item:
                    if 'answers' in item:
                        item['options'] = item['answers']
                        del item['answers']
                        fixes.append(f"Renamed 'answers' to 'options' in select item {i+1}")
                        modified = True
                    elif 'choices' in item:
                        item['options'] = item['choices']
                        del item['choices']
                        fixes.append(f"Renamed 'choices' to 'options' in select item {i+1}")
                        modified = True

    # Fix 11: Add missing instruction field with default text
    # Default instructions by activity type (in Ukrainian for B1+ immersion)
    DEFAULT_INSTRUCTIONS = {
        'quiz': 'Оберіть правильну відповідь.',
        'match-up': "З'єднайте відповідні елементи.",
        'fill-in': 'Оберіть правильне слово для заповнення пропуску.',
        'true-false': 'Визначте, чи твердження правильне.',
        'group-sort': 'Розподіліть елементи за групами.',
        'unjumble': 'Розташуйте слова у правильному порядку.',
        'cloze': 'Заповніть пропуски, обравши правильні слова.',
        'error-correction': 'Знайдіть і виправте помилку в реченні.',
        'mark-the-words': 'Клацніть на слова, що відповідають критерію.',
        'select': 'Оберіть усі правильні відповіді.',
        'translate': 'Оберіть правильний переклад.',
        'anagram': 'Розташуйте літери у правильному порядку.',
    }

    if 'instruction' not in activity and activity_type in DEFAULT_INSTRUCTIONS:
        activity['instruction'] = DEFAULT_INSTRUCTIONS[activity_type]
        fixes.append(f"Added default instruction for {activity_type}")
        modified = True

    # Fix 12: Remove blank lines from cloze passages (causes MDX rendering issues)
    if activity_type == 'cloze' and 'passage' in activity:
        passage = activity['passage']
        if '\n\n' in passage:
            # Replace all double newlines with single newlines
            fixed_passage = passage.replace('\n\n', '\n')
            # Clean up any triple+ newlines that might exist
            while '\n\n' in fixed_passage:
                fixed_passage = fixed_passage.replace('\n\n', '\n')
            activity['passage'] = fixed_passage
            fixes.append(f"Removed blank lines from cloze passage (fixes MDX rendering)")
            modified = True

    return modified, fixes


def fix_raw_yaml_text(content: str) -> Tuple[str, List[str]]:
    """
    Fix YAML issues at the raw text level (before parsing).

    This handles issues that prevent YAML from parsing at all,
    like double-quoted strings with asterisks being interpreted as aliases.

    Returns (fixed_content, list_of_fixes).
    """
    fixes = []
    import re

    # Fix: Convert double-quoted text with asterisks to single quotes
    # YAML interprets *word as an alias reference, causing parse errors
    # when asterisks are followed by Cyrillic characters

    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Match: text: "..." (double-quoted text field containing asterisks)
        match = re.match(r'^(\s*text:\s*)"(.+)"(\s*)$', line)
        if match and '*' in match.group(2):
            prefix = match.group(1)
            text_content = match.group(2)
            suffix = match.group(3)

            # Handle escaped quotes and inner quotes
            # Remove escape backslashes before quotes
            text_content = text_content.replace('\\"', '"')

            # Convert ASCII double quotes to Ukrainian guillemets (alternating « »)
            # This handles cases like: "text with "*marked*" words"
            result = []
            quote_open = False
            for char in text_content:
                if char == '"':
                    if quote_open:
                        result.append('»')
                        quote_open = False
                    else:
                        result.append('«')
                        quote_open = True
                else:
                    result.append(char)
            text_content = ''.join(result)

            # Escape single quotes if present (YAML single-quoted strings)
            text_content = text_content.replace("'", "''")

            fixes.append("Converted double-quoted text with asterisks to single quotes")
            fixed_lines.append(f"{prefix}'{text_content}'{suffix}")
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines), fixes


def remove_forbidden_activities(yaml_path: Path, level_code: str, module_focus: str = None, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Remove forbidden activity types from a YAML activity file.

    For seminar tracks (B2-HIST, C1-HIST, C1-BIO, LIT), grammar drill activities
    are forbidden and should be removed.

    Args:
        yaml_path: Path to the YAML file
        level_code: CEFR level (B2, C1, etc.)
        module_focus: Module focus (history, biography, etc.)
        dry_run: If True, only report removals without saving

    Returns (num_removed, list_of_messages).
    """
    from ..config import LEVEL_CONFIG

    all_messages = []
    removed_count = 0

    if not yaml_path.exists():
        return 0, []

    # Get level config
    config_key = f"{level_code}-{module_focus}" if module_focus else level_code
    config = LEVEL_CONFIG.get(config_key, LEVEL_CONFIG.get(level_code, {}))

    # Get forbidden types from config
    forbidden_types = config.get('forbidden_types', set())
    if not forbidden_types:
        return 0, ["No forbidden types defined for this level/track"]

    # Load activities from YAML
    with open(yaml_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    try:
        data, _ = safe_load_with_duplicate_check(raw_content)
    except yaml.YAMLError as e:
        return 0, [f"YAML parse error: {e}"]

    if not data:
        return 0, []

    # Handle both formats — extract activities list
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
    elif isinstance(data, list):
        activities = data
    else:
        return 0, ["Invalid YAML structure"]

    # Find activities to remove
    activities_to_keep = []
    for i, activity in enumerate(activities):
        if not isinstance(activity, dict):
            activities_to_keep.append(activity)
            continue

        act_type = activity.get('type', '').lower()
        title = activity.get('title', f'Activity {i+1}')

        if act_type in forbidden_types:
            removed_count += 1
            all_messages.append(f"  🗑️  Removed [{act_type}] '{title[:40]}...' (forbidden in {config_key})")
        else:
            activities_to_keep.append(activity)

    # Save — ALWAYS as bare list
    if removed_count > 0:
        if not dry_run:
            try:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(activities_to_keep, f, allow_unicode=True,
                             default_flow_style=False, sort_keys=False)
                all_messages.insert(0, f"✅ Removed {removed_count} forbidden activities from {yaml_path.name}")
            except Exception as e:
                all_messages.insert(0, f"❌ Error saving: {e}")
                return 0, all_messages
        else:
            all_messages.insert(0, f"🔍 DRY RUN: Would remove {removed_count} forbidden activities from {yaml_path.name}")

    return removed_count, all_messages


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

    # Pre-fix: Fix raw text issues that prevent YAML parsing
    with open(yaml_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    fixed_content, raw_fixes = fix_raw_yaml_text(raw_content)
    if raw_fixes:
        all_fixes.extend(raw_fixes)
        total_fixes += len(raw_fixes)
        if not dry_run:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
        raw_content = fixed_content

    # Load activities from YAML with duplicate key detection
    try:
        data, duplicate_errors = safe_load_with_duplicate_check(raw_content)
        if duplicate_errors:
            # Duplicates cannot be auto-fixed - report them
            all_fixes.extend([f"⚠️ CANNOT AUTO-FIX: {err}" for err in duplicate_errors])
    except yaml.YAMLError as e:
        return total_fixes, all_fixes + [f"YAML parse error (cannot auto-fix): {e}"]

    if not data:
        return 0, []

    # Handle both formats — auto-unwrap dictionary wrapper to bare list
    if isinstance(data, dict) and 'activities' in data:
        activities = data['activities']
        # Strip metadata keys (module, level, etc.) and unwrap to bare list
        stripped_keys = [k for k in data.keys() if k != 'activities']
        if stripped_keys:
            all_fixes.append(f"✓ Stripped metadata keys from YAML: {', '.join(stripped_keys)}")
        all_fixes.append("✓ Unwrapped `activities:` dictionary to bare list (required format)")
        total_fixes += 1
    elif isinstance(data, list):
        activities = data
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

    # Save — ALWAYS as bare list (never re-wrap in dictionary)
    if total_fixes > 0 and not dry_run:
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(activities, f, allow_unicode=True,
                         default_flow_style=False, sort_keys=False)
            all_fixes.insert(0, f"✅ Saved {total_fixes} fixes to {yaml_path.name}")
        except Exception as e:
            all_fixes.insert(0, f"❌ Error saving fixes: {e}")
            return 0, all_fixes
    elif total_fixes > 0 and dry_run:
        all_fixes.insert(0, f"🔍 DRY RUN: Would apply {total_fixes} fixes to {yaml_path.name}")

    return total_fixes, all_fixes


# =============================================================================
# PLAN / META / VOCABULARY SCHEMA CHECK FUNCTIONS
# =============================================================================

def _validate_yaml_against_schema(yaml_path: Path, schema_name: str) -> List[str]:
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

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
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
) -> List[Dict]:
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
) -> List[Dict]:
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
) -> List[Dict]:
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
    'check_plan_yaml_schema',
    'check_meta_yaml_schema',
    'check_vocabulary_yaml_schema',
    'validate_activity_yaml_file',
    'validate_activity',
    'fix_activity_violations',
    'fix_raw_yaml_text',
    'fix_yaml_file',
    'remove_forbidden_activities',
]
