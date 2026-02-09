import pytest
import os
import yaml
import json
from pathlib import Path
from scripts.validate_schemas import validate_yaml, SCHEMA_MAP

@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "curriculum"
    d.mkdir()
    (d / "activities").mkdir()
    (d / "meta").mkdir()
    (d / "vocabulary").mkdir()
    (d / "plans").mkdir()
    (d / "plans" / "b2-hist").mkdir()
    return d

def test_validate_activity_valid(temp_dir):
    activity_file = temp_dir / "activities" / "test.yaml"
    content = [
        {
            "type": "quiz",
            "title": "Test Quiz",
            "instruction": "Test instruction",
            "items": [
                {
                    "question": "Q1",
                    "options": [
                        {"text": "O1", "correct": True},
                        {"text": "O2", "correct": False},
                        {"text": "O3", "correct": False},
                        {"text": "O4", "correct": False}
                    ]
                }
            ]
        }
    ]
    with open(activity_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(activity_file)
    assert is_valid, f"Expected valid activity, got errors: {errors}"

def test_validate_activity_invalid(temp_dir):
    activity_file = temp_dir / "activities" / "test.yaml"
    content = [
        {
            "type": "quiz",
            "title": "", # Too short
            "items": [] # Too short
        }
    ]
    with open(activity_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(activity_file)
    assert not is_valid
    assert any("title" in e for e in errors) or any("items" in e for e in errors)

def test_validate_meta_valid(temp_dir):
    meta_file = temp_dir / "meta" / "test.yaml"
    content = {
        "module": "test-module",
        "level": "B2",
        "slug": "test",
        "version": "2.0",
        "pedagogy": "CBI",
        "grammar": ["Grammar 1"]
    }
    with open(meta_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(meta_file)
    assert is_valid, f"Expected valid meta, got errors: {errors}"

def test_validate_meta_invalid_missing_required(temp_dir):
    meta_file = temp_dir / "meta" / "test.yaml"
    content = {
        "module": "test-module",
        "level": "B2"
        # Missing slug, version, pedagogy, grammar
    }
    with open(meta_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(meta_file)
    assert not is_valid
    assert any("pedagogy" in e.lower() for e in errors)
    assert any("grammar" in e.lower() for e in errors)

def test_validate_vocabulary_valid(temp_dir):
    vocab_file = temp_dir / "vocabulary" / "test.yaml"
    content = {
        "items": [
            {
                "lemma": "слово",
                "ipa": "slovo",
                "pos": "noun",
                "translation": "word"
            }
        ]
    }
    with open(vocab_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(vocab_file)
    assert is_valid, f"Expected valid vocabulary, got errors: {errors}"

def test_validate_vocabulary_invalid_missing_ipa(temp_dir):
    vocab_file = temp_dir / "vocabulary" / "test.yaml"
    content = {
        "items": [
            {
                "lemma": "слово",
                "pos": "noun",
                "translation": "word"
            }
        ]
    }
    with open(vocab_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(vocab_file)
    assert not is_valid
    assert any("ipa" in e.lower() for e in errors)

def test_validate_plan_valid(temp_dir):
    plan_file = temp_dir / "plans" / "b2-hist" / "test.yaml"
    content = {
        "module": "test",
        "level": "b2-hist",
        "sequence": 1,
        "version": "2.0",
        "title": "Title",
        "focus": "history",
        "pedagogy": "seminar",
        "objectives": ["Obj 1"],
        "content_outline": [{"section": "Sec 1", "words": 500}],
        "word_target": 500
    }
    with open(plan_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(plan_file)
    assert is_valid, f"Expected valid plan, got errors: {errors}"

def test_validate_plan_invalid_word_target(temp_dir):
    plan_file = temp_dir / "plans" / "b2-hist" / "test.yaml"
    content = {
        "module": "test",
        "level": "b2-hist",
        "sequence": 1,
        "version": "2.0",
        "title": "Title",
        "focus": "history",
        "pedagogy": "seminar",
        "objectives": ["Obj 1"],
        "content_outline": [{"section": "Sec 1", "words": 100}],
        "word_target": 100 # Too low (min 500 in schema)
    }
    with open(plan_file, "w") as f:
        yaml.dump(content, f)

    is_valid, errors = validate_yaml(plan_file)
    assert not is_valid
    assert any("word_target" in e.lower() for e in errors)
