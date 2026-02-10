"""
Tests for JSON Schema validation of curriculum file types:
plan, meta, vocabulary, activity.

Issue: #534
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

# Add scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_schemas import validate_file, main, detect_file_type, load_schema
from audit.checks.yaml_schema_validation import (
    check_plan_yaml_schema,
    check_meta_yaml_schema,
    check_vocabulary_yaml_schema,
)


SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


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
                "ipa": "/prɪʋˈit/",
                "translation": "hello",
                "pos": "noun",
                "gender": "m",
            }
        ],
    }


@pytest.fixture
def valid_activity_data():
    return [
        {
            "type": "quiz",
            "title": "Test Quiz",
            "items": [
                {
                    "question": "What?",
                    "options": [
                        {"text": "A", "correct": True},
                        {"text": "B", "correct": False},
                        {"text": "C", "correct": False},
                        {"text": "D", "correct": False},
                    ],
                }
            ],
        }
    ]


# =============================================================================
# PLAN SCHEMA TESTS
# =============================================================================


class TestPlanSchema:

    def test_valid_plan_passes(self, valid_plan_data, tmp_path):
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert errors == []

    def test_missing_word_target_fails(self, valid_plan_data, tmp_path):
        del valid_plan_data["word_target"]
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert len(errors) > 0
        assert "word_target" in errors[0]

    def test_missing_objectives_fails(self, valid_plan_data, tmp_path):
        del valid_plan_data["objectives"]
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert len(errors) > 0
        assert "objectives" in errors[0]

    def test_invalid_level_fails(self, valid_plan_data, tmp_path):
        valid_plan_data["level"] = "z9"
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert len(errors) > 0

    def test_word_target_below_minimum_fails(self, valid_plan_data, tmp_path):
        valid_plan_data["word_target"] = 10
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert len(errors) > 0

    def test_track_level_b2_hist_passes(self, valid_plan_data, tmp_path):
        """Track levels like B2-HIST should be accepted."""
        valid_plan_data["level"] = "B2-HIST"
        path = _write_yaml(tmp_path, "plans/b2-hist", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        level_errors = [e for e in errors if "level" in e.lower()]
        assert level_errors == []

    def test_track_level_c1_pro_passes(self, valid_plan_data, tmp_path):
        valid_plan_data["level"] = "c1-pro"
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        level_errors = [e for e in errors if "level" in e.lower()]
        assert level_errors == []

    def test_extra_fields_allowed(self, valid_plan_data, tmp_path):
        """Plan schema has additionalProperties:true, so extra fields pass."""
        valid_plan_data["custom_field"] = "should be fine"
        valid_plan_data["grammar"] = ["accusative"]
        path = _write_yaml(tmp_path, "plans/b1", "test.yaml", valid_plan_data)
        errors = validate_file(path)
        assert errors == []


# =============================================================================
# META SCHEMA TESTS
# =============================================================================


class TestMetaSchema:

    def test_valid_meta_passes(self, valid_meta_data, tmp_path):
        path = _write_yaml(tmp_path, "meta", "test.yaml", valid_meta_data)
        errors = validate_file(path)
        assert errors == []

    def test_missing_required_fields_fails(self, valid_meta_data, tmp_path):
        del valid_meta_data["id"]
        del valid_meta_data["title"]
        path = _write_yaml(tmp_path, "meta", "test.yaml", valid_meta_data)
        errors = validate_file(path)
        assert len(errors) > 0

    def test_invalid_focus_fails(self, valid_meta_data, tmp_path):
        valid_meta_data["focus"] = "nonexistent_focus"
        path = _write_yaml(tmp_path, "meta", "test.yaml", valid_meta_data)
        errors = validate_file(path)
        assert len(errors) > 0


# =============================================================================
# VOCABULARY SCHEMA TESTS
# =============================================================================


class TestVocabularySchema:

    def test_valid_vocab_passes(self, valid_vocab_data, tmp_path):
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        errors = validate_file(path)
        assert errors == []

    def test_missing_lemma_fails(self, valid_vocab_data, tmp_path):
        del valid_vocab_data["items"][0]["lemma"]
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        errors = validate_file(path)
        assert len(errors) > 0
        assert "lemma" in errors[0]

    def test_missing_translation_fails(self, valid_vocab_data, tmp_path):
        del valid_vocab_data["items"][0]["translation"]
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        errors = validate_file(path)
        assert len(errors) > 0
        assert "translation" in errors[0]

    def test_invalid_pos_detected(self, valid_vocab_data, tmp_path):
        valid_vocab_data["items"][0]["pos"] = "invalid_pos"
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        errors = validate_file(path)
        assert len(errors) > 0

    def test_empty_items_fails(self, valid_vocab_data, tmp_path):
        valid_vocab_data["items"] = []
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        errors = validate_file(path)
        assert len(errors) > 0

    def test_minimal_vocab_item_passes(self, tmp_path):
        """Vocab item with only required fields (no ipa, no gender)."""
        data = {
            "items": [
                {"lemma": "говорити", "translation": "to speak", "pos": "verb"}
            ]
        }
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", data)
        errors = validate_file(path)
        assert errors == []

    def test_empty_yaml_file(self, tmp_path):
        """Empty YAML file should produce an error, not crash."""
        target_dir = tmp_path / "vocabulary"
        target_dir.mkdir(parents=True)
        path = target_dir / "test.yaml"
        path.write_text("")
        errors = validate_file(path)
        assert len(errors) > 0
        assert "empty" in errors[0].lower()


# =============================================================================
# ACTIVITY SCHEMA TESTS
# =============================================================================


class TestActivitySchema:

    def test_bare_list_passes(self, valid_activity_data, tmp_path):
        path = _write_yaml(tmp_path, "activities", "test.yaml", valid_activity_data)
        errors = validate_file(path)
        assert errors == []

    def test_dict_wrapper_detected(self, valid_activity_data, tmp_path):
        wrapped = {"activities": valid_activity_data}
        path = _write_yaml(tmp_path, "activities", "test.yaml", wrapped)
        errors = validate_file(path)
        assert any("bare list" in e for e in errors)


# =============================================================================
# CLI TESTS
# =============================================================================


class TestCLI:

    def test_main_returns_0_for_valid(self, valid_vocab_data, tmp_path):
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        result = main([str(path)])
        assert result == 0

    def test_main_returns_1_for_invalid(self, tmp_path):
        bad_data = {"items": [{"pos": "noun"}]}  # missing lemma, translation
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", bad_data)
        result = main([str(path)])
        assert result == 1

    def test_main_returns_2_for_no_args(self):
        result = main([])
        assert result == 2


# =============================================================================
# FILE TYPE DETECTION TESTS
# =============================================================================


class TestFileTypeDetection:

    def test_detect_vocabulary(self):
        assert detect_file_type(Path("foo/vocabulary/test.yaml")) == "vocabulary"

    def test_detect_plans(self):
        assert detect_file_type(Path("curriculum/plans/b1/test.yaml")) == "plans"

    def test_detect_meta(self):
        assert detect_file_type(Path("b1/meta/slug.yaml")) == "meta"

    def test_detect_activities(self):
        assert detect_file_type(Path("b1/activities/slug.yaml")) == "activities"

    def test_unknown_path(self):
        assert detect_file_type(Path("random/path/file.yaml")) is None


# =============================================================================
# AUDIT CHECK FUNCTION TESTS
# =============================================================================


class TestAuditCheckFunctions:

    def test_plan_check_valid(self, valid_plan_data, tmp_path):
        # Create a fake module .md file and plan file
        plan_dir = tmp_path / "plans" / "b1"
        plan_dir.mkdir(parents=True)
        plan_path = plan_dir / "test-module.yaml"
        with open(plan_path, "w") as f:
            yaml.dump(valid_plan_data, f, allow_unicode=True)

        violations = check_plan_yaml_schema(str(plan_path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)

    def test_vocab_check_missing_lemma(self, tmp_path):
        vocab_dir = tmp_path / "vocabulary"
        vocab_dir.mkdir()
        vocab_path = vocab_dir / "test.yaml"
        bad_data = {
            "items": [{"translation": "hello", "pos": "noun"}]  # no lemma
        }
        with open(vocab_path, "w") as f:
            yaml.dump(bad_data, f, allow_unicode=True)

        violations = check_vocabulary_yaml_schema(str(vocab_path), "b1", 1)
        assert any(v["severity"] == "error" for v in violations)

    def test_meta_check_valid(self, valid_meta_data, tmp_path):
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        meta_path = meta_dir / "test.yaml"
        with open(meta_path, "w") as f:
            yaml.dump(valid_meta_data, f, allow_unicode=True)

        violations = check_meta_yaml_schema(str(meta_path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)
