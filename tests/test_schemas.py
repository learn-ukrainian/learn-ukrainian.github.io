import pytest
from pathlib import Path
import yaml
from scripts.audit.checks.yaml_schema_validation import (
    validate_activity,
    load_base_schema,
    safe_load_with_duplicate_check,
    fix_activity_violations,
    validate_activity_yaml_file
)

@pytest.fixture
def base_schema():
    return load_base_schema()

def test_validate_valid_quiz(base_schema):
    activity = {
        "type": "quiz",
        "title": "Valid Quiz",
        "instruction": "Test",
        "items": [
            {
                "question": "Q1",
                "options": [
                    {"text": "A1", "correct": True},
                    {"text": "A2", "correct": False},
                    {"text": "A3", "correct": False},
                    {"text": "A4", "correct": False}
                ]
            }
        ]
    }
    errors = validate_activity(activity, base_schema)
    assert len(errors) == 0

def test_validate_invalid_quiz(base_schema):
    activity = {
        "type": "quiz",
        "title": "Invalid Quiz",
        # missing items
    }
    errors = validate_activity(activity, base_schema)
    assert len(errors) > 0

def test_duplicate_key_detection():
    yaml_content = """
key1: value1
key1: value2
"""
    data, errors = safe_load_with_duplicate_check(yaml_content)
    assert len(errors) > 0
    assert "Duplicate key 'key1'" in errors[0]

def test_fix_activity_violations(base_schema):
    activity = {
        "type": "quiz",
        "question": "This should be title",
        "items": [
            {
                "question": "Q1",
                "options": [
                    {"text": "A1"} # missing correct: false
                ]
            }
        ]
    }
    modified, fixes = fix_activity_violations(activity, base_schema)
    assert modified
    assert "title" in activity
    assert activity["title"] == "This should be title"
    assert activity["items"][0]["options"][0]["correct"] is False

def test_validate_activity_yaml_file(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    # Create a valid bare list
    content = [
        {
            "type": "quiz",
            "title": "T1",
            "instruction": "I1",
            "items": [{
                "question": "Q1",
                "options": [
                    {"text": "O1", "correct": True},
                    {"text": "O2", "correct": False},
                    {"text": "O3", "correct": False},
                    {"text": "O4", "correct": False}
                ]
            }]
        }
    ]
    with open(yaml_file, "w") as f:
        yaml.dump(content, f)

    # Path needs to be such that level detection works if we want level-specific checks
    # But for a simple check, it should pass
    is_valid, errors = validate_activity_yaml_file(yaml_file)
    assert is_valid
    assert len(errors) == 0

def test_validate_activity_yaml_file_wrapped(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    # Invalid: wrapped in 'activities' key
    content = {
        "activities": [
            {"type": "quiz", "title": "T1", "items": []}
        ]
    }
    with open(yaml_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_activity_yaml_file(yaml_file)
    assert not is_valid
    assert any("dictionary wrapper" in err for err in errors)
