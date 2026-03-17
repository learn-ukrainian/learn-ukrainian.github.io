"""Tests for semantic false friends detection in content.

Issue: #912
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.checks.russicism_detection import check_semantic_false_friends


class TestSemanticFalseFriends:
    """check_semantic_false_friends catches Ukrainian words with Russian meanings."""

    def _check(self, content: str, file_path: str = "") -> list[dict]:
        return check_semantic_false_friends(content, file_path)

    def test_detects_лук_as_onion_bold(self):
        content = "The word **лук** (onion) is commonly used."
        result = self._check(content)
        assert len(result) == 1
        assert result[0]["type"] == "SEMANTIC_FALSE_FRIEND"
        assert "лук" in result[0]["issue"]
        assert "onion" in result[0]["issue"]

    def test_detects_лук_as_onion_dash(self):
        content = "лук — onion"
        result = self._check(content)
        assert len(result) == 1

    def test_detects_неділя_as_week(self):
        content = "**неділя** (week) is the first word."
        result = self._check(content)
        assert len(result) == 1
        assert "неділя" in result[0]["issue"]
        assert "week" in result[0]["issue"]

    def test_detects_город_as_city_in_table(self):
        content = "| город | city |"
        result = self._check(content)
        assert len(result) == 1
        assert "город" in result[0]["issue"]

    def test_correct_usage_not_flagged(self):
        """лук (bow) is the correct Ukrainian meaning — should not flag."""
        content = "The word **лук** (bow) refers to a weapon."
        result = self._check(content)
        assert len(result) == 0

    def test_correct_неділя_not_flagged(self):
        """неділя (Sunday) is correct — should not flag."""
        content = "**неділя** (Sunday) is the last day."
        result = self._check(content)
        assert len(result) == 0

    def test_цибуля_not_flagged(self):
        """цибуля (onion) is the correct Ukrainian word — no false friend."""
        content = "**цибуля** (onion) is a vegetable."
        result = self._check(content)
        assert len(result) == 0

    def test_exempt_tracks_skipped(self):
        """OES and RUTH tracks may contain legitimate Russian context."""
        content = "**лук** (onion) in historical text."
        assert self._check(content, "/curriculum/l2-uk-en/oes/test.md") == []
        assert self._check(content, "/curriculum/l2-uk-en/ruth/test.md") == []

    def test_quote_context_skipped(self):
        """Matches inside guillemets should be skipped."""
        content = "Порівняйте: «лук (onion)» — русизм."
        result = self._check(content)
        assert len(result) == 0

    def test_case_insensitive(self):
        content = "**Лук** (Onion) appears here."
        result = self._check(content)
        assert len(result) == 1

    def test_multiple_false_friends(self):
        content = "**лук** (onion) and **неділя** (week) and **город** (city)"
        result = self._check(content)
        assert len(result) == 1  # returns one aggregated violation
        assert "3 semantic false friend" in result[0]["issue"]

    def test_new_entries_річ(self):
        content = "**річ** (speech) is important."
        result = self._check(content)
        assert len(result) == 1
        assert "річ" in result[0]["issue"]

    def test_new_entries_шар(self):
        content = "шар — ball"
        result = self._check(content)
        assert len(result) == 1

    def test_new_entries_мешкати(self):
        content = "**мешкати** (to delay)"
        result = self._check(content)
        assert len(result) == 1

    def test_severity_is_critical(self):
        content = "**лук** (onion)"
        result = self._check(content)
        assert result[0]["severity"] == "critical"

    def test_no_substring_match(self):
        """'ball' should not match 'balloon'."""
        content = "**шар** (balloon)"
        result = self._check(content)
        assert len(result) == 0

    def test_with_article(self):
        """Should catch 'an onion' not just 'onion'."""
        content = "**лук** (an onion)"
        result = self._check(content)
        assert len(result) == 1

    def test_blockquote_skipped(self):
        content = "> **лук** (onion) in a quote."
        result = self._check(content)
        assert len(result) == 0

    def test_colon_separator(self):
        content = "лук: onion"
        result = self._check(content)
        assert len(result) == 1

    def test_reversed_table(self):
        content = "| onion | лук |"
        result = self._check(content)
        assert len(result) == 1

    def test_removed_entries_no_false_positive(self):
        """рушник (towel) and дурний (stupid) should NOT be flagged — they're correct Ukrainian."""
        content = "**рушник** (towel) and **дурний** (stupid)"
        result = self._check(content)
        assert len(result) == 0

    def test_гадати_not_flagged(self):
        """гадати (to guess) is valid Ukrainian — removed from dictionary."""
        content = "**гадати** (to guess)"
        result = self._check(content)
        assert len(result) == 0

    def test_narrative_zones_only(self):
        """Should not match inside code blocks or YAML frontmatter."""
        content = "---\ntitle: лук (onion)\n---\n\nNormal text here."
        result = self._check(content)
        assert len(result) == 0


class TestSemanticFalseFriendsPlanScanner:
    """Existing plan scanner still works with expanded dictionary."""

    def test_scan_plan_finds_лук(self, tmp_path):
        from pipeline.semantic_russianisms import scan_plan_for_russianisms
        plan_file = tmp_path / "test-plan.yaml"
        plan_file.write_text(
            "vocabulary_hints:\n"
            "  required:\n"
            "    - 'лук (onion)'\n"
        )
        findings = scan_plan_for_russianisms(plan_file)
        assert len(findings) == 1
        assert findings[0]["word"] == "лук"

    def test_scan_plan_no_false_positive(self, tmp_path):
        from pipeline.semantic_russianisms import scan_plan_for_russianisms
        plan_file = tmp_path / "test-plan.yaml"
        plan_file.write_text(
            "vocabulary_hints:\n"
            "  required:\n"
            "    - 'цибуля (onion)'\n"
            "    - 'неділя (Sunday)'\n"
        )
        findings = scan_plan_for_russianisms(plan_file)
        assert len(findings) == 0

    def test_scan_plan_content_outline(self, tmp_path):
        """Scanner should also check content_outline points."""
        from pipeline.semantic_russianisms import scan_plan_for_russianisms
        plan_file = tmp_path / "test-plan.yaml"
        plan_file.write_text(
            "content_outline:\n"
            "- section: Test\n"
            "  points:\n"
            "    - 'лук (hard Л — onion) vs люк'\n"
        )
        findings = scan_plan_for_russianisms(plan_file)
        assert len(findings) == 1
        assert findings[0]["word"] == "лук"
        assert "content_outline" in findings[0]["category"]

    def test_scan_plan_content_outline_no_false_positive(self, tmp_path):
        from pipeline.semantic_russianisms import scan_plan_for_russianisms
        plan_file = tmp_path / "test-plan.yaml"
        plan_file.write_text(
            "content_outline:\n"
            "- section: Test\n"
            "  points:\n"
            "    - 'лук (bow) vs люк (hatch)'\n"
        )
        findings = scan_plan_for_russianisms(plan_file)
        assert len(findings) == 0

    def test_scan_research(self, tmp_path):
        from pipeline.semantic_russianisms import scan_research_for_russianisms
        research_file = tmp_path / "research.md"
        research_file.write_text(
            "## Vocabulary\n"
            "- город (city) is a common word\n"
        )
        findings = scan_research_for_russianisms(research_file)
        assert len(findings) == 1
        assert findings[0]["word"] == "город"

    def test_scan_research_no_false_positive(self, tmp_path):
        from pipeline.semantic_russianisms import scan_research_for_russianisms
        research_file = tmp_path / "research.md"
        research_file.write_text(
            "## Vocabulary\n"
            "- місто (city) is a common word\n"
        )
        findings = scan_research_for_russianisms(research_file)
        assert len(findings) == 0
