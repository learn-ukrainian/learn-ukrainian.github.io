"""
Tests for YAML schema validation audit checks.

Tests the live audit check functions from yaml_schema_validation.py
which validate plan, meta, and vocabulary YAML against project schemas.

Issue: #534, #520
"""

# Add scripts to path
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.yaml_schema_validation import (
    check_meta_yaml_schema,
    check_plan_yaml_schema,
    check_vocabulary_yaml_schema,
)

# =============================================================================
# FIXTURES
# =============================================================================


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

    @pytest.mark.repo_wide
    def test_a2_plans_match_module_schema(self):
        plans_dir = (
            Path(__file__).parent.parent
            / "curriculum"
            / "l2-uk-en"
            / "plans"
            / "a2"
        )
        failures = {}

        for plan_path in sorted(plans_dir.glob("*.yaml")):
            violations = check_plan_yaml_schema(str(plan_path), "a2", 0)
            errors = [
                violation["message"]
                for violation in violations
                if violation["severity"] == "error"
            ]
            if errors:
                failures[plan_path.name] = errors

        assert failures == {}


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


# =============================================================================
# VOCABULARY YAML SCHEMA AUDIT CHECK TESTS
# =============================================================================


class TestVocabularyYamlSchemaCheck:

    def test_valid_vocab_no_errors(self, valid_vocab_data, tmp_path):
        path = _write_yaml(tmp_path, "vocabulary", "test.yaml", valid_vocab_data)
        violations = check_vocabulary_yaml_schema(str(path), "b1", 1)
        assert all(v["severity"] != "error" for v in violations)
