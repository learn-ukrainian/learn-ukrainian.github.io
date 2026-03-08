"""
Tests for YAML schema validation audit checks.

Tests the live audit check functions from yaml_schema_validation.py
which validate plan, meta, and vocabulary YAML against project schemas.

Issue: #534, #520
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.yaml_schema_validation import (
    check_plan_yaml_schema,
    check_meta_yaml_schema,
    check_vocabulary_yaml_schema,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def valid_plan_data():
    return {
        "module": "01-test-module",
        "level": "b1",
        "sequence": 1,
        "version": "2.0",
        "title": "Test Module",
        "focus": "grammar",
        "pedagogy": "TTT",
        "objectives": ["Learn something"],
        "content_outline": [
            {"section": "Introduction", "words": 500}
        ],
        "word_target": 3000,
    }


@pytest.fixture
def valid_meta_data():
    return {
        "id": "b1-01",
        "title": "Test Module",
        "slug": "test-module",
        "version": "2.0",
        "phase": "B1.1",
        "focus": "grammar",
        "word_target": 3000,
        "sources": [
            {"name": "Test", "url": "https://example.com", "type": "reference"}
        ],
        "content_outline": [
            {"section": "Intro", "words": 500, "points": ["Point 1"]}
        ],
        "vocabulary_hints": {"required": ["слово"]},
        "activity_hints": [
            {"type": "quiz", "focus": "test"}
        ],
    }


@pytest.fixture
def valid_vocab_data():
    return {
        "module": "01-test-module",
        "level": "B1",
        "version": "2.0",
        "items": [
            {
                "lemma": "привіт",
                "translation": "hello",
                "pos": "noun",
                "gender": "m",
            }
        ],
    }


# =============================================================================
# HELPERS
# =============================================================================


def _write_yaml(tmp_dir: Path, subdir: str, filename: str, data) -> Path:
    """Write YAML data to a temp file within the expected directory structure."""
    target_dir = tmp_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    return path


# =============================================================================
# PLAN YAML SCHEMA AUDIT CHECK TESTS
# =============================================================================


class TestPlanYamlSchemaCheck:

    def test_valid_plan_no_errors(self, valid_plan_data, tmp_path):
        plan_dir = tmp_path / "plans" / "b1"
        plan_dir.mkdir(parents=True)
        plan_path = plan_dir / "test-module.yaml"
        with open(plan_path, "w") as f:
            yaml.dump(valid_plan_data, f, allow_unicode=True)
        violations = check_plan_yaml_schema(str(plan_path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)

    def test_missing_word_target(self, valid_plan_data, tmp_path):
        del valid_plan_data["word_target"]
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        violations = check_plan_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert len(error_violations) > 0

    def test_missing_objectives(self, valid_plan_data, tmp_path):
        del valid_plan_data["objectives"]
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        violations = check_plan_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert len(error_violations) > 0


# =============================================================================
# META YAML SCHEMA AUDIT CHECK TESTS
# =============================================================================


class TestMetaYamlSchemaCheck:

    def test_valid_meta_no_errors(self, valid_meta_data, tmp_path):
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        meta_path = meta_dir / "test.yaml"
        with open(meta_path, "w") as f:
            yaml.dump(valid_meta_data, f, allow_unicode=True)
        violations = check_meta_yaml_schema(str(meta_path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)

    def test_missing_required_fields(self, valid_meta_data, tmp_path):
        del valid_meta_data["id"]
        del valid_meta_data["title"]
        path = _write_yaml(tmp_path, "meta", "test.yaml", valid_meta_data)
        violations = check_meta_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert len(error_violations) > 0


# =============================================================================
# VOCABULARY YAML SCHEMA AUDIT CHECK TESTS
# =============================================================================


class TestVocabularyYamlSchemaCheck:

    def test_valid_vocab_no_errors(self, valid_vocab_data, tmp_path):
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)

    def test_missing_lemma_fails(self, valid_vocab_data, tmp_path):
        del valid_vocab_data["items"][0]["lemma"]
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert len(error_violations) > 0

    def test_missing_translation_fails(self, valid_vocab_data, tmp_path):
        del valid_vocab_data["items"][0]["translation"]
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert len(error_violations) > 0

    def test_empty_items_fails(self, valid_vocab_data, tmp_path):
        valid_vocab_data["items"] = []
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        assert len(violations) > 0

    def test_minimal_vocab_item(self, tmp_path):
        """Vocab item with only required fields (no ipa, no gender)."""
        data = {
            "items": [
                {"lemma": "говорити", "translation": "to speak", "pos": "verb"}
            ]
        }
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        error_violations = [v for v in violations if v["severity"] == "error"]
        assert error_violations == []
