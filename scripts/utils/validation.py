"""
Shared validation utilities for curriculum YAML files.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"

def get_schema_path(file_type: str, level: Optional[str] = None) -> Optional[Path]:
    """Get the path to the appropriate schema file."""
    if file_type == "activity":
        if level:
            path = SCHEMAS_DIR / f"activities-{level.lower()}.schema.json"
            if path.exists():
                return path
        return SCHEMAS_DIR / "activities-base.schema.json"

    if file_type == "plan":
        return SCHEMAS_DIR / "module-plan.schema.json"

    if file_type == "meta":
        return SCHEMAS_DIR / "meta-module.schema.json"

    if file_type == "meta-minimal":
        return SCHEMAS_DIR / "meta-module-minimal.schema.json"

    if file_type == "vocabulary":
        return SCHEMAS_DIR / "vocabulary.schema.json"

    return None

def load_schema(schema_path: Path) -> Optional[Dict]:
    """Load a JSON schema from a file."""
    if not schema_path.exists():
        return None
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class LineLoader(yaml.SafeLoader):
    """Custom YAML loader that attaches line numbers to dicts."""
    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        # Store line number in a way that doesn't interfere with validation
        # We'll use a separate attribute if possible, or just accept we need to clean it
        mapping['__line__'] = node.start_mark.line + 1
        return mapping

def validate_yaml_content(data: Any, schema: Dict) -> List[str]:
    """Validate data against a schema and return list of error messages."""
    if not HAS_JSONSCHEMA:
        return ["jsonschema library not installed"]

    if data is None:
        return ["YAML file is empty"]

    errors = []

    # Create a deep copy without __line__ keys for validation
    def clean_data(obj):
        if isinstance(obj, dict):
            return {k: clean_data(v) for k, v in obj.items() if k != '__line__'}
        if isinstance(obj, list):
            return [clean_data(i) for i in obj]
        return obj

    cleaned_data = clean_data(data)

    validator = Draft7Validator(schema)
    for error in validator.iter_errors(cleaned_data):
        # Try to find line number from original data
        line_num = None
        curr = data
        for part in error.path:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            elif isinstance(curr, list) and isinstance(part, int) and part < len(curr):
                curr = curr[part]
            else:
                break

        if isinstance(curr, dict) and '__line__' in curr:
            line_num = curr['__line__']

        path = " -> ".join(str(p) for p in error.path) if error.path else "root"
        line_info = f" (line {line_num})" if line_num else ""
        errors.append(f"Field '{path}'{line_info}: {error.message}")

    return errors

def detect_meta_type(data: Any) -> str:
    """Detect if a meta file is full or minimal."""
    if data is None:
        return "meta-minimal"
    is_full = any(field in data for field in ["content_outline", "vocabulary_hints", "activity_hints", "sources"])
    return "meta" if is_full else "meta-minimal"
