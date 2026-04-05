"""Tests for step_activities() — Activity V2 pipeline step.

Tests prompt construction, YAML validation, semantic checks,
and retry logic. Does NOT test LLM dispatch (mocked).

Issue: #1042
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.v6_build import (
    _check_activity_semantics,
    step_activities,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "activity-v2.schema.json"
VALID_YAML = textwrap.dedent("""\
    version: "1.0"
    module: things-have-gender
    level: a1

    inline:
      - id: quiz-genders
        type: quiz
        instruction: "Оберіть правильний варіант"
        items:
          - question: "_____ стіл"
            options: ["мій", "моя", "моє"]
            correct: 0

    workbook:
      - id: match-up-genders
        type: match-up
        instruction: "З'єднайте пари"
        pairs:
          - left: "стіл"
            right: "він"
          - left: "книга"
            right: "вона"
          - left: "вікно"
            right: "воно"
""")

VALID_YAML_WITH_FENCE = f"```yaml\n{VALID_YAML}```"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def tmp_module(tmp_path):
    """Create a minimal module environment for step_activities."""
    level = "a1"
    slug = "test-mod"

    # Create directories
    (tmp_path / "curriculum" / "l2-uk-en" / level).mkdir(parents=True)
    (tmp_path / "curriculum" / "l2-uk-en" / "plans" / level).mkdir(parents=True)
    (tmp_path / "curriculum" / "l2-uk-en" / level / "orchestration" / slug).mkdir(parents=True)
    (tmp_path / "schemas").mkdir(parents=True)
    (tmp_path / "scripts" / "build" / "phases").mkdir(parents=True)

    # Write plan
    plan = {
        "title": "Test Module",
        "word_target": 1200,
        "phase": "A1.2",
        "activity_hints": [
            {"type": "quiz", "focus": "Test quiz", "items": 4},
        ],
        "vocabulary_hints": {
            "required": ["стіл", "книга", "вікно"],
        },
    }
    plan_path = tmp_path / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"
    plan_path.write_text(yaml.dump(plan, allow_unicode=True))

    # Write content with injection markers
    content_path = tmp_path / "curriculum" / "l2-uk-en" / level / f"{slug}.md"
    content_path.write_text(
        "## Section One\n\nSome content here.\n\n"
        "<!-- INJECT_ACTIVITY: quiz-genders -->\n\n"
        "## Section Two\n\nMore content.\n"
    )

    # Write prompt template
    template_path = tmp_path / "scripts" / "build" / "phases" / "v6-activities.md"
    template_path.write_text("Prompt: {MODULE_SLUG} {LEVEL} {INJECTION_MARKERS}")

    # Write schema
    import shutil
    shutil.copy(SCHEMA_PATH, tmp_path / "schemas" / "activity-v2.schema.json")

    return {
        "tmp_path": tmp_path,
        "level": level,
        "slug": slug,
        "content_path": content_path,
    }


# ---------------------------------------------------------------------------
# _check_activity_semantics
# ---------------------------------------------------------------------------

class TestCheckActivitySemantics:
    def test_valid_data_no_errors(self):
        data = yaml.safe_load(VALID_YAML)
        assert _check_activity_semantics(data) == []

    def test_missing_id(self):
        data = {
            "inline": [{"type": "quiz", "instruction": "test", "items": []}],
        }
        errors = _check_activity_semantics(data)
        assert len(errors) == 1
        assert "missing required 'id'" in errors[0]

    def test_duplicate_id(self):
        data = {
            "inline": [
                {"id": "quiz-a", "type": "quiz"},
                {"id": "quiz-a", "type": "quiz"},
            ],
        }
        errors = _check_activity_semantics(data)
        assert len(errors) == 1
        assert "duplicate id 'quiz-a'" in errors[0]

    def test_no_inline_no_errors(self):
        data = {"workbook": [{"type": "quiz"}]}
        assert _check_activity_semantics(data) == []

    def test_empty_data(self):
        assert _check_activity_semantics({}) == []


# ---------------------------------------------------------------------------
# Schema validation (the YAML example must validate)
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_example_yaml_validates(self, schema):
        data = yaml.safe_load(VALID_YAML)
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        assert errors == [], f"Schema errors: {[e.message for e in errors]}"

    def test_missing_version_fails(self, schema):
        data = yaml.safe_load(VALID_YAML)
        del data["version"]
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        assert len(errors) > 0

    def test_example_file_validates(self, schema):
        """Validate the shipped example file."""
        example = (
            Path(__file__).resolve().parent.parent
            / "curriculum" / "l2-uk-en" / "a1" / "activities" / "things-have-gender.yaml"
        )
        if not example.exists():
            pytest.skip("Example file not found")
        data = yaml.safe_load(example.read_text())
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        assert errors == [], f"Schema errors: {[e.message for e in errors]}"


# ---------------------------------------------------------------------------
# Prompt construction (unit test: template filling)
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    def test_injection_marker_extraction(self):
        """Verify regex extracts injection markers from prose."""
        import re
        content = (
            "Some text\n"
            "<!-- INJECT_ACTIVITY: quiz-genders -->\n"
            "More text\n"
            "<!-- INJECT_ACTIVITY: fillin-possessives -->\n"
        )
        markers = re.findall(
            r"<!--\s*INJECT_ACTIVITY:\s*([a-z0-9][a-z0-9-]*)\s*-->", content
        )
        assert markers == ["quiz-genders", "fillin-possessives"]

    def test_no_markers_produces_fallback(self):
        import re
        content = "No markers here."
        markers = re.findall(
            r"<!--\s*INJECT_ACTIVITY:\s*([a-z0-9][a-z0-9-]*)\s*-->", content
        )
        assert markers == []


# ---------------------------------------------------------------------------
# YAML fence stripping
# ---------------------------------------------------------------------------

class TestYamlFenceStripping:
    def test_strip_markdown_fence(self):
        """Verify the fence stripping logic matches what step_activities does."""
        raw = VALID_YAML_WITH_FENCE
        clean = raw.strip()
        if clean.startswith("```"):
            first_newline = clean.index("\n")
            clean = clean[first_newline + 1:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        data = yaml.safe_load(clean)
        assert data["version"] == "1.0"
        assert data["module"] == "things-have-gender"

    def test_no_fence_passthrough(self):
        clean = VALID_YAML.strip()
        if clean.startswith("```"):
            first_newline = clean.index("\n")
            clean = clean[first_newline + 1:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        data = yaml.safe_load(clean)
        assert data["version"] == "1.0"


# ---------------------------------------------------------------------------
# step_activities integration (with mocked dispatch)
# ---------------------------------------------------------------------------

class TestStepActivitiesIntegration:
    """Integration tests using mocked dispatch to verify the full step."""

    def test_step_returns_path_on_valid_yaml(self, tmp_module):
        """step_activities returns a path when dispatch returns valid YAML."""
        tp = tmp_module["tmp_path"]

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tp / "curriculum" / "l2-uk-en"),
            patch("build.v6_build.PROJECT_ROOT", tp),
            patch("build.v6_build.PHASES_DIR", tp / "scripts" / "build" / "phases"),
            patch("build.dispatch.dispatch_agent", return_value=(True, VALID_YAML)),
        ):
            result = step_activities(
                tmp_module["content_path"],
                tmp_module["level"],
                8,
                tmp_module["slug"],
                writer="gemini-tools",
            )

        # Should have saved the activities file
        assert result is not None
        assert result.exists()
        data = yaml.safe_load(result.read_text())
        assert data["version"] == "1.0"
        assert len(data.get("inline", [])) == 1
        assert len(data.get("workbook", [])) == 1

    def test_step_retries_on_invalid_yaml(self, tmp_module):
        """step_activities retries when YAML is invalid, then succeeds."""
        tp = tmp_module["tmp_path"]
        bad_yaml = "not: valid: yaml: [[[["

        call_count = 0

        def mock_dispatch(prompt, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True, bad_yaml
            return True, VALID_YAML

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tp / "curriculum" / "l2-uk-en"),
            patch("build.v6_build.PROJECT_ROOT", tp),
            patch("build.v6_build.PHASES_DIR", tp / "scripts" / "build" / "phases"),
            patch("build.dispatch.dispatch_agent", side_effect=mock_dispatch),
        ):
            result = step_activities(
                tmp_module["content_path"],
                tmp_module["level"],
                8,
                tmp_module["slug"],
                writer="gemini-tools",
            )

        assert result is not None
        assert call_count == 2

    def test_step_strips_markdown_fence(self, tmp_module):
        """step_activities strips ```yaml fencing from LLM output."""
        tp = tmp_module["tmp_path"]

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tp / "curriculum" / "l2-uk-en"),
            patch("build.v6_build.PROJECT_ROOT", tp),
            patch("build.v6_build.PHASES_DIR", tp / "scripts" / "build" / "phases"),
            patch("build.dispatch.dispatch_agent", return_value=(True, VALID_YAML_WITH_FENCE)),
        ):
            result = step_activities(
                tmp_module["content_path"],
                tmp_module["level"],
                8,
                tmp_module["slug"],
                writer="gemini-tools",
            )

        assert result is not None
        data = yaml.safe_load(result.read_text())
        assert data["version"] == "1.0"

    def test_step_returns_none_after_max_retries(self, tmp_module):
        """step_activities returns None after exhausting retries."""
        tp = tmp_module["tmp_path"]

        with (
            patch("build.v6_build.CURRICULUM_ROOT", tp / "curriculum" / "l2-uk-en"),
            patch("build.v6_build.PROJECT_ROOT", tp),
            patch("build.v6_build.PHASES_DIR", tp / "scripts" / "build" / "phases"),
            patch("build.dispatch.dispatch_agent", return_value=(True, "not yaml [[[")),
        ):
            result = step_activities(
                tmp_module["content_path"],
                tmp_module["level"],
                8,
                tmp_module["slug"],
                writer="gemini-tools",
                max_retries=1,
            )

        assert result is None
