"""Tests for pipeline consultation parser, template patcher, and queue."""

import sys
import textwrap
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.consultation import (
    ConsultationResult,
    TemplateChange,
    apply_template_patch,
    parse_consultation,
    queue_for_approval,
    record_consultation,
)

# ── parse_consultation ─────────────────────────────────────────────────


class TestParseConsultation:
    """Tests for YAML consultation result parsing."""

    VALID_YAML = textwrap.dedent("""\
        root_cause: |
          The template instructs Gemini to write tables but doesn't specify Ukrainian-only content.
        proposed_changes:
          - find: |
              Write a comparison table
            replace: |
              Write a comparison table using ONLY Ukrainian words in the table cells
            file: "content.md"
            rationale: "Prevents English leaking into tables"
        scope: this_module
        action: rebuild
        confidence: high
        additional_notes: |
          The template is otherwise well-structured.
    """)

    def test_valid_yaml_parses(self):
        result = parse_consultation(self.VALID_YAML)
        assert result is not None
        assert isinstance(result, ConsultationResult)
        assert "doesn't specify" in result.root_cause
        assert len(result.proposed_changes) == 1
        assert result.proposed_changes[0].file == "content.md"
        assert result.scope == "this_module"
        assert result.action == "rebuild"
        assert result.confidence == "high"

    def test_valid_yaml_change_fields(self):
        result = parse_consultation(self.VALID_YAML)
        assert result is not None
        change = result.proposed_changes[0]
        assert "comparison table" in change.find
        assert "ONLY Ukrainian" in change.replace
        assert change.rationale == "Prevents English leaking into tables"

    def test_multiple_changes(self):
        text = textwrap.dedent("""\
            root_cause: Multiple issues
            proposed_changes:
              - find: "old text 1"
                replace: "new text 1"
                file: "a.md"
              - find: "old text 2"
                replace: "new text 2"
                file: "b.md"
            scope: all_modules
            action: rebuild
            confidence: medium
        """)
        result = parse_consultation(text)
        assert result is not None
        assert len(result.proposed_changes) == 2
        assert result.proposed_changes[0].file == "a.md"
        assert result.proposed_changes[1].file == "b.md"

    def test_empty_text_returns_none(self):
        assert parse_consultation("") is None
        assert parse_consultation("   ") is None

    def test_non_yaml_returns_none(self):
        assert parse_consultation("This is just plain text, not YAML") is None

    def test_missing_root_cause_returns_none(self):
        text = textwrap.dedent("""\
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: this_module
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_missing_scope_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_invalid_scope_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: everywhere
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_invalid_action_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: this_module
            action: delete
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_invalid_confidence_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: this_module
            action: rebuild
            confidence: maybe
        """)
        assert parse_consultation(text) is None

    def test_proposed_changes_not_list_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes: "just a string"
            scope: this_module
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_change_missing_find_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - replace: "y"
                file: "z.md"
            scope: this_module
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_change_not_dict_returns_none(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - "just a string"
            scope: this_module
            action: rebuild
            confidence: high
        """)
        assert parse_consultation(text) is None

    def test_optional_additional_notes(self):
        text = textwrap.dedent("""\
            root_cause: Something
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: this_module
            action: fix
            confidence: low
        """)
        result = parse_consultation(text)
        assert result is not None
        assert result.additional_notes == ""

    def test_markdown_fences_stripped(self):
        """Gemini often wraps YAML in ```yaml ... ``` fences."""
        text = textwrap.dedent("""\
            ```yaml
            root_cause: Template issue
            proposed_changes:
              - find: "old"
                replace: "new"
                file: "content.md"
            scope: this_module
            action: rebuild
            confidence: high
            ```
        """)
        result = parse_consultation(text)
        assert result is not None
        assert result.root_cause == "Template issue"

    def test_triple_backtick_inside_content_stripped(self):
        """Even mid-content backtick lines should be removed."""
        text = textwrap.dedent("""\
            ```
            root_cause: Has backticks
            proposed_changes:
              - find: "x"
                replace: "y"
                file: "z.md"
            scope: all_modules
            action: fix
            confidence: low
            ```
        """)
        result = parse_consultation(text)
        assert result is not None

    def test_empty_replace_is_allowed(self):
        """A change can replace text with nothing (deletion)."""
        text = textwrap.dedent("""\
            root_cause: Remove bad instruction
            proposed_changes:
              - find: "Delete this line"
                replace: ""
                file: "content.md"
            scope: this_module
            action: rebuild
            confidence: high
        """)
        result = parse_consultation(text)
        assert result is not None
        assert result.proposed_changes[0].replace == ""


# ── apply_template_patch ───────────────────────────────────────────────


class TestApplyTemplatePatch:
    """Tests for FIND/REPLACE template patching."""

    def test_exact_match_applies(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Write a table\nwith examples\n")
        output = tmp_path / "patched-content.md"

        changes = [TemplateChange(
            find="Write a table",
            replace="Write a Ukrainian-only table",
            file="content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 1
        assert "Ukrainian-only table" in output.read_text()
        # Original unchanged
        assert "Write a table" in template.read_text()
        assert "Ukrainian-only" not in template.read_text()

    def test_no_match_returns_zero(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Some template content\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="This text does not exist in the template",
            replace="Replacement",
            file="content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 0
        # Output file should NOT be written with 0 changes (avoids false
        # positive on the consultation-patched-* detection in rebuild)
        assert not output.exists()

    def test_wrong_file_skipped(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Write a table\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="Write a table",
            replace="REPLACED",
            file="activities.md",  # Different file
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 0
        assert not output.exists()

    def test_empty_file_field_matches_all(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Write a table\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="Write a table",
            replace="REPLACED",
            file="",  # Empty = matches all
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 1

    def test_whitespace_normalized_fallback(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Write   a\n  table\n  with examples\n")
        output = tmp_path / "patched.md"

        # Gemini often normalizes whitespace in its find text
        changes = [TemplateChange(
            find="Write a table with examples",  # Normalized
            replace="REPLACED",
            file="content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 1
        result = output.read_text()
        assert "REPLACED" in result

    def test_only_first_occurrence_replaced(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("Write a table\nMore text\nWrite a table\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="Write a table",
            replace="REPLACED",
            file="content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 1
        result = output.read_text()
        assert result.count("REPLACED") == 1
        assert result.count("Write a table") == 1  # Second occurrence preserved

    def test_missing_template_returns_false(self, tmp_path):
        output = tmp_path / "patched.md"
        changes = [TemplateChange(find="x", replace="y", file="content.md")]

        ok, applied = apply_template_patch(tmp_path / "nonexistent.md", changes, output)
        assert ok is False
        assert applied == 0

    def test_multiple_changes_applied_sequentially(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("First instruction\nSecond instruction\n")
        output = tmp_path / "patched.md"

        changes = [
            TemplateChange(find="First instruction", replace="Changed first", file="content.md"),
            TemplateChange(find="Second instruction", replace="Changed second", file="content.md"),
        ]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 2
        result = output.read_text()
        assert "Changed first" in result
        assert "Changed second" in result

    def test_identical_find_replace_skipped(self, tmp_path):
        template = tmp_path / "content.md"
        template.write_text("No change needed\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="No change needed",
            replace="No change needed",
            file="content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 0
        assert not output.exists()

    def test_path_in_file_field_matches(self, tmp_path):
        """File field with path like 'phases/gemini/content.md' should match 'content.md'."""
        template = tmp_path / "content.md"
        template.write_text("Old text\n")
        output = tmp_path / "patched.md"

        changes = [TemplateChange(
            find="Old text",
            replace="New text",
            file="phases/gemini/content.md",
        )]

        ok, applied = apply_template_patch(template, changes, output)
        assert ok is True
        assert applied == 1


# ── queue_for_approval ─────────────────────────────────────────────────


class TestQueueForApproval:
    """Tests for the human approval queue."""

    def _make_result(self):
        return ConsultationResult(
            root_cause="Template missing Ukrainian constraint",
            proposed_changes=[
                TemplateChange(
                    find="Write a table",
                    replace="Write a Ukrainian table",
                    file="content.md",
                    rationale="Prevent English",
                ),
            ],
            scope="all_modules",
            action="rebuild",
            confidence="high",
            additional_notes="Affects all levels",
        )

    def test_writes_yaml_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline.consultation.QUEUE_DIR", tmp_path)
        result = self._make_result()

        path = queue_for_approval(result, "test-slug", "a1", 1)
        assert path.exists()
        assert path.suffix == ".yaml"
        assert "test-slug" in path.name

        data = yaml.safe_load(path.read_text())
        assert data["source_module"] == "a1/test-slug"
        assert data["consultation_num"] == 1
        assert data["confidence"] == "high"
        assert len(data["proposed_changes"]) == 1
        assert data["proposed_changes"][0]["find"] == "Write a table"

    def test_includes_source_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pipeline.consultation.QUEUE_DIR", tmp_path)
        result = self._make_result()

        path = queue_for_approval(
            result, "slug", "a1", 2,
            consultation_file=Path("/some/orch/consultation-2.md"),
        )
        data = yaml.safe_load(path.read_text())
        assert data["source_file"] == "/some/orch/consultation-2.md"

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        queue_dir = tmp_path / "new-queue"
        monkeypatch.setattr("pipeline.consultation.QUEUE_DIR", queue_dir)
        result = self._make_result()

        path = queue_for_approval(result, "slug", "a1", 1)
        assert queue_dir.is_dir()
        assert path.exists()


# ── record_consultation ────────────────────────────────────────────────


class TestRecordConsultation:
    """Tests for state tracking."""

    def test_records_applied_consultation(self):
        state = {"track": "a1", "slug": "test", "mode": "v5", "phases": {}}
        result = ConsultationResult(
            root_cause="x",
            proposed_changes=[TemplateChange(find="a", replace="b", file="c.md")],
            scope="this_module", action="rebuild", confidence="high",
        )

        record_consultation(state, 1, result, "applied")

        assert "consultations" in state
        assert len(state["consultations"]) == 1
        entry = state["consultations"][0]
        assert entry["num"] == 1
        assert entry["outcome"] == "applied"
        assert entry["scope"] == "this_module"
        assert entry["action"] == "rebuild"
        assert entry["confidence"] == "high"
        assert entry["changes_count"] == 1
        assert "ts" in entry

    def test_records_parse_failure(self):
        state = {"phases": {}}
        record_consultation(state, 1, None, "parse_failed")

        assert len(state["consultations"]) == 1
        entry = state["consultations"][0]
        assert entry["outcome"] == "parse_failed"
        assert "scope" not in entry  # No result to extract from

    def test_appends_multiple_consultations(self):
        state = {"phases": {}}
        result = ConsultationResult(
            root_cause="x",
            proposed_changes=[],
            scope="this_module", action="fix", confidence="low",
        )

        record_consultation(state, 1, result, "no_action")
        record_consultation(state, 2, result, "applied")

        assert len(state["consultations"]) == 2
        assert state["consultations"][0]["num"] == 1
        assert state["consultations"][1]["num"] == 2

    def test_records_queued_consultation(self):
        state = {"phases": {}}
        result = ConsultationResult(
            root_cause="x",
            proposed_changes=[
                TemplateChange(find="a", replace="b", file="c.md"),
                TemplateChange(find="c", replace="d", file="e.md"),
            ],
            scope="all_modules", action="rebuild", confidence="medium",
        )

        record_consultation(state, 3, result, "queued")

        entry = state["consultations"][0]
        assert entry["outcome"] == "queued"
        assert entry["changes_count"] == 2
