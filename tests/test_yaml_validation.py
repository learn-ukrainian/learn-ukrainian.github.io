"""
Tests for YAML schema validation logic.
"""

import pytest
from pathlib import Path
import yaml
import tempfile
import os

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from audit.checks.yaml_schema_validation import (
    validate_activity,
    validate_activity_yaml_file,
    load_base_schema
)

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def base_schema():
    return load_base_schema()

@pytest.fixture
def valid_quiz_data():
    return {
        "type": "quiz",
        "title": "Valid Quiz",
        "items": [
            {
                "question": "Question?",
                "options": [
                    {"text": "Correct", "correct": True},
                    {"text": "Wrong 1", "correct": False},
                    {"text": "Wrong 2", "correct": False},
                    {"text": "Wrong 3", "correct": False}
                ]
            }
        ]
    }

@pytest.fixture
def invalid_quiz_data():
    return {
        "type": "quiz",
        "title": "Invalid Quiz",
        "items": [
            {
                "question": "Missing options"
                # options field missing
            }
        ]
    }

# =============================================================================
# TESTS
# =============================================================================

class TestActivityValidation:
    """Test individual activity validation."""

    def test_validate_valid_quiz(self, valid_quiz_data, base_schema):
        errors = validate_activity(valid_quiz_data, base_schema)
        assert len(errors) == 0

    def test_validate_invalid_quiz(self, invalid_quiz_data, base_schema):
        errors = validate_activity(invalid_quiz_data, base_schema)
        assert len(errors) > 0
        assert "options" in errors[0]

    def test_validate_unknown_type(self, base_schema):
        bad_data = {"type": "nonexistent-type", "title": "Bad"}
        errors = validate_activity(bad_data, base_schema)
        assert len(errors) == 1
        assert "Unknown activity type" in errors[0]

    def test_validate_missing_type(self, base_schema):
        bad_data = {"title": "No Type"}
        errors = validate_activity(bad_data, base_schema)
        assert len(errors) == 1
        assert "missing 'type'" in errors[0]

class TestFileValidation:
    """Test full YAML file validation."""

    def test_validate_valid_file(self, valid_quiz_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump([valid_quiz_data], f)
            temp_path = Path(f.name)
        
        try:
            is_valid, errors = validate_activity_yaml_file(temp_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            if temp_path.exists():
                os.remove(temp_path)

    def test_validate_invalid_file(self, invalid_quiz_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump([invalid_quiz_data], f)
            temp_path = Path(f.name)
        
        try:
            is_valid, errors = validate_activity_yaml_file(temp_path)
            assert not is_valid
            assert len(errors) > 0
        finally:
            if temp_path.exists():
                os.remove(temp_path)

    def test_validate_malformed_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(" - this is : invalid : yaml : structure")
            temp_path = Path(f.name)
        
        try:
            is_valid, errors = validate_activity_yaml_file(temp_path)
            assert not is_valid
            assert any("YAML parse error" in e or "Invalid YAML structure" in e for e in errors)
        finally:
            if temp_path.exists():
                os.remove(temp_path)

    def test_validate_nonexistent_file(self):
        is_valid, errors = validate_activity_yaml_file(Path("nonexistent.yaml"))
        assert is_valid  # Function returns True if file doesn't exist (legacy behavior)
        assert len(errors) == 0
