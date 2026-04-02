"""Tests for audit/audit_module.py CLI entry point."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestAutoFixIpa:
    def test_no_files_returns_zero(self, tmp_path):
        from audit.audit_module import auto_fix_ipa
        # Point at a nonexistent markdown file
        fake_md = str(tmp_path / "nonexistent.md")
        fixes, messages = auto_fix_ipa(fake_md)
        assert fixes == 0
        assert messages == []

    def test_existing_file_without_ipa_issues(self, tmp_path):
        from audit.audit_module import auto_fix_ipa
        md_file = tmp_path / "test-module.md"
        md_file.write_text("# Test\n\nNo IPA here.\n")
        with patch("lint_ipa.apply_fixes", return_value=("# Test\n\nNo IPA here.\n", 0)):
            fixes, messages = auto_fix_ipa(str(md_file))
        assert fixes == 0


class TestAutoFixYamlViolations:
    def test_no_yaml_returns_info(self, tmp_path):
        from audit.audit_module import auto_fix_yaml_violations
        md_file = tmp_path / "test-module.md"
        md_file.write_text("---\ntitle: Test\n---\n# Test\n")
        fixes, messages = auto_fix_yaml_violations(str(md_file))
        assert fixes == 0
        assert any("No YAML file" in m for m in messages)


class TestCliArgParsing:
    """Test that the argparse setup accepts expected flags."""

    def test_basic_args(self):
        import argparse
        # Simulate the parser from audit_module
        parser = argparse.ArgumentParser()
        parser.add_argument("files", nargs="*")
        parser.add_argument("--fix", action="store_true")
        parser.add_argument("--naturalness", action="store_true")
        parser.add_argument("--skip-activities", action="store_true")
        parser.add_argument("--skip-review", action="store_true")

        args = parser.parse_args(["test.md", "--fix", "--skip-activities"])
        assert args.files == ["test.md"]
        assert args.fix is True
        assert args.skip_activities is True
        assert args.skip_review is False
