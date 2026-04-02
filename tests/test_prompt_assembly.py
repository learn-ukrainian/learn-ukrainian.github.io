"""
Tests for prompt template assembly (fill_template.py).

Covers:
- fill_template() — placeholder substitution
- find_unresolved() — unresolved placeholder detection
- main() CLI — end-to-end with YAML files, --set overrides, strict mode

Issue: #520
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fill_template import PLACEHOLDER_RE, fill_template, find_unresolved, main

# =============================================================================
# fill_template() UNIT TESTS
# =============================================================================

class TestFillTemplate:

    def test_single_placeholder(self):
        result = fill_template("Hello {NAME}!", {"NAME": "World"})
        assert result == "Hello World!"

    def test_multiple_placeholders(self):
        template = "Track: {TRACK}, Level: {LEVEL}, Target: {WORD_TARGET} words"
        placeholders = {"TRACK": "hist", "LEVEL": "B2", "WORD_TARGET": "3500"}
        result = fill_template(template, placeholders)
        assert result == "Track: hist, Level: B2, Target: 3500 words"

    def test_repeated_placeholder(self):
        """Same placeholder used twice in template."""
        template = "{SLUG} content for {SLUG}"
        result = fill_template(template, {"SLUG": "my-family"})
        assert result == "my-family content for my-family"

    def test_no_placeholders_returns_unchanged(self):
        template = "No placeholders here."
        result = fill_template(template, {"UNUSED": "value"})
        assert result == "No placeholders here."

    def test_empty_placeholders_dict(self):
        template = "Template with {PLACEHOLDER}"
        result = fill_template(template, {})
        assert result == "Template with {PLACEHOLDER}"

    def test_numeric_value_converted_to_string(self):
        result = fill_template("Target: {WORD_TARGET}", {"WORD_TARGET": 3000})
        assert result == "Target: 3000"

    def test_multiline_template(self):
        template = "# {TOPIC_TITLE}\n\nLevel: {LEVEL}\n\n## Content\n{CONTENT}"
        placeholders = {
            "TOPIC_TITLE": "Моя родина",
            "LEVEL": "A1",
            "CONTENT": "Це контент модуля.",
        }
        result = fill_template(template, placeholders)
        assert "# Моя родина" in result
        assert "Level: A1" in result
        assert "Це контент модуля." in result

    def test_unicode_content_preserved(self):
        """Ukrainian text with apostrophes and special chars survives substitution."""
        template = "Словник: {VOCAB}"
        result = fill_template(template, {"VOCAB": "м'яч, пів'яблуко, з'їсти"})
        assert "м'яч" in result
        assert "з'їсти" in result

    def test_path_as_value(self):
        """Absolute paths are valid placeholder values."""
        template = "Read: {PLAN_PATH}"
        result = fill_template(template, {
            "PLAN_PATH": "/curriculum/l2-uk-en/b1/plans/my-module.yaml"
        })
        assert "/curriculum/l2-uk-en/b1/plans/my-module.yaml" in result

    def test_empty_string_value(self):
        """Empty string replaces placeholder (doesn't skip it)."""
        result = fill_template("Before {GAP} after", {"GAP": ""})
        assert result == "Before  after"


# =============================================================================
# find_unresolved() UNIT TESTS
# =============================================================================

class TestFindUnresolved:

    def test_no_unresolved(self):
        text = "All filled, no placeholders."
        assert find_unresolved(text) == []

    def test_single_unresolved(self):
        text = "Missing {WORD_TARGET} here."
        assert find_unresolved(text) == ["{WORD_TARGET}"]

    def test_multiple_unresolved(self):
        text = "Track: {TRACK}, Level: {LEVEL}"
        result = find_unresolved(text)
        assert "{LEVEL}" in result
        assert "{TRACK}" in result
        assert len(result) == 2

    def test_deduplicated(self):
        """Same placeholder appearing twice counts once."""
        text = "{SLUG} and {SLUG} again"
        assert find_unresolved(text) == ["{SLUG}"]

    def test_lowercase_not_matched(self):
        """Lowercase {placeholders} are NOT detected as unresolved."""
        text = "This {lowercase} is fine."
        assert find_unresolved(text) == []

    def test_single_char_not_matched(self):
        """Single char like {A} doesn't match (requires 2+ chars)."""
        text = "Value {A} here"
        assert find_unresolved(text) == []

    def test_mixed_case_not_matched(self):
        """Mixed case like {Word} doesn't match (must be all uppercase start)."""
        text = "The {Word} value"
        assert find_unresolved(text) == []

    def test_real_template_placeholders(self):
        """Typical placeholders from the build pipeline."""
        text = """
        Track: {TRACK}
        Word target: {WORD_TARGET}
        Computed: {COMPUTED_WORD_COUNT}
        Persona: {PERSONA_VOICE}
        """
        result = find_unresolved(text)
        assert len(result) == 4
        assert "{COMPUTED_WORD_COUNT}" in result
        assert "{PERSONA_VOICE}" in result


# =============================================================================
# PLACEHOLDER_RE REGEX TESTS
# =============================================================================

class TestPlaceholderRegex:

    @pytest.mark.parametrize("token", [
        "{TRACK}", "{WORD_TARGET}", "{COMPUTED_WORD_COUNT}",
        "{AB}", "{A1}", "{LEVEL_CONSTRAINTS}",
    ])
    def test_valid_placeholders_match(self, token):
        assert PLACEHOLDER_RE.match(token)

    @pytest.mark.parametrize("token", [
        "{a}", "{lowercase}", "{A}", "{1NVALID}", "TRACK",
        "{}", "{a_b}", "{{DOUBLE}}",
    ])
    def test_invalid_patterns_dont_match(self, token):
        assert not PLACEHOLDER_RE.match(token)


# =============================================================================
# main() CLI INTEGRATION TESTS
# =============================================================================

class TestMainCLI:

    def test_basic_fill_and_write(self, tmp_path, monkeypatch):
        """Template + YAML → filled output file."""
        template = tmp_path / "template.md"
        template.write_text("# {TOPIC_TITLE}\n\nWords: {WORD_TARGET}")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({
            "TOPIC_TITLE": "Моя родина",
            "WORD_TARGET": "3000",
        }))

        output = tmp_path / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
        ])
        result = main()
        assert result == 0
        assert output.exists()
        content = output.read_text()
        assert "# Моя родина" in content
        assert "Words: 3000" in content

    def test_strict_mode_fails_on_unresolved(self, tmp_path, monkeypatch):
        """Strict mode returns 1 when placeholders remain."""
        template = tmp_path / "template.md"
        template.write_text("{RESOLVED} and {MISSING}")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"RESOLVED": "ok"}))

        output = tmp_path / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
            "--strict",
        ])
        result = main()
        assert result == 1

    def test_no_strict_mode_warns_but_succeeds(self, tmp_path, monkeypatch):
        """Non-strict mode returns 0 even with unresolved placeholders."""
        template = tmp_path / "template.md"
        template.write_text("{RESOLVED} and {MISSING}")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"RESOLVED": "ok"}))

        output = tmp_path / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
            "--no-strict",
        ])
        result = main()
        assert result == 0
        assert "{MISSING}" in output.read_text()

    def test_set_override(self, tmp_path, monkeypatch):
        """--set overrides YAML values."""
        template = tmp_path / "template.md"
        template.write_text("{WORD_TARGET} words")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"WORD_TARGET": "2000"}))

        output = tmp_path / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
            "--set", "WORD_TARGET=5000",
        ])
        result = main()
        assert result == 0
        assert "5000 words" in output.read_text()

    def test_missing_template_returns_1(self, tmp_path, monkeypatch):
        """Missing template file → exit code 1."""
        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"X": "Y"}))

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(tmp_path / "nonexistent.md"),
            "--placeholders", str(placeholders),
            "--output", str(tmp_path / "out.md"),
        ])
        result = main()
        assert result == 1

    def test_missing_placeholders_file_returns_1(self, tmp_path, monkeypatch):
        """Missing placeholders YAML → exit code 1."""
        template = tmp_path / "template.md"
        template.write_text("content")

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(tmp_path / "nonexistent.yaml"),
            "--output", str(tmp_path / "out.md"),
        ])
        result = main()
        assert result == 1

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        """Output file's parent dirs are created automatically."""
        template = tmp_path / "template.md"
        template.write_text("content")

        placeholders = tmp_path / "placeholders.yaml"
        placeholders.write_text(yaml.dump({"X": "Y"}))

        output = tmp_path / "deep" / "nested" / "output.md"

        monkeypatch.setattr("sys.argv", [
            "fill_template.py",
            "--template", str(template),
            "--placeholders", str(placeholders),
            "--output", str(output),
        ])
        result = main()
        assert result == 0
        assert output.exists()
