"""Tests for adaptive immersion floor based on lexical sandbox size (#773 Fix 3)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import get_a1_immersion_range
from audit.phases_gates import _count_sandbox_lemmas


class TestAdaptiveImmersionRange:
    """Test get_a1_immersion_range with sandbox_lemma_count parameter."""

    def test_no_sandbox_info_unchanged(self):
        """Without sandbox info, ranges are unchanged."""
        assert get_a1_immersion_range(25) == (35, 55)
        assert get_a1_immersion_range(15) == (25, 40)

    def test_none_sandbox_unchanged(self):
        """Explicit None sandbox_lemma_count = no change."""
        assert get_a1_immersion_range(25, None) == (35, 55)
        assert get_a1_immersion_range(15, None) == (25, 40)

    def test_large_sandbox_unchanged(self):
        """Sandbox >= 20 lemmas = no reduction."""
        assert get_a1_immersion_range(25, 20) == (35, 55)
        assert get_a1_immersion_range(25, 50) == (35, 55)
        assert get_a1_immersion_range(15, 30) == (25, 40)

    def test_small_sandbox_m21_plus(self):
        """Sandbox < 20 lemmas reduces floor by 5 for M21+."""
        assert get_a1_immersion_range(25, 15) == (30, 55)
        assert get_a1_immersion_range(25, 19) == (30, 55)

    def test_tiny_sandbox_m21_plus(self):
        """Sandbox < 10 lemmas reduces floor by 10 for M21+."""
        assert get_a1_immersion_range(25, 9) == (25, 55)
        assert get_a1_immersion_range(25, 5) == (25, 55)
        assert get_a1_immersion_range(25, 0) == (25, 55)

    def test_small_sandbox_m11_20(self):
        """Sandbox < 20 lemmas reduces floor by 5 for M11-20."""
        assert get_a1_immersion_range(15, 15) == (20, 40)

    def test_tiny_sandbox_m11_20(self):
        """Sandbox < 10 lemmas reduces floor by 10 for M11-20."""
        assert get_a1_immersion_range(15, 5) == (15, 40)

    def test_floor_never_below_5(self):
        """Floor cannot go below 5 even with tiny sandbox."""
        # M11-20 base is 25, minus 10 = 15, still above 5
        assert get_a1_immersion_range(11, 1)[0] >= 5
        # M21+ base is 35, minus 10 = 25, still above 5
        assert get_a1_immersion_range(25, 1)[0] >= 5

    def test_early_modules_unaffected(self):
        """Modules <= 10 are never affected by sandbox size."""
        assert get_a1_immersion_range(1, 5) == (5, 15)
        assert get_a1_immersion_range(5, 3) == (10, 25)
        assert get_a1_immersion_range(10, 8) == (15, 35)

    def test_max_unchanged(self):
        """Max immersion is never affected by sandbox size."""
        _, max_no_sandbox = get_a1_immersion_range(25)
        _, max_small = get_a1_immersion_range(25, 15)
        _, max_tiny = get_a1_immersion_range(25, 5)
        assert max_no_sandbox == max_small == max_tiny == 55


class TestCountSandboxLemmas:
    """Test _count_sandbox_lemmas helper."""

    def test_missing_sandbox_returns_none(self, tmp_path):
        """No sandbox file = None."""
        md_file = tmp_path / "a1" / "some-module.md"
        md_file.parent.mkdir(parents=True)
        md_file.touch()
        result = _count_sandbox_lemmas(str(md_file))
        assert result is None

    def test_counts_table_rows(self, tmp_path):
        """Counts table data rows correctly."""
        level_dir = tmp_path / "a1"
        orch_dir = level_dir / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        sandbox = orch_dir / "lexical-sandbox.md"
        sandbox.write_text(
            "## Lexical Sandbox\n"
            "### Nouns\n"
            "| Lemma | Gender | Allowed Forms |\n"
            "|-------|--------|---------------|\n"
            "| книга | feminine | книга, книги |\n"
            "| стіл | masculine | стіл, столу |\n"
            "### Other Words\n"
            "- **так** (Adverb)\n"
            "- **ні** (Particle)\n",
            encoding="utf-8",
        )
        md_file = level_dir / "test-module.md"
        md_file.touch()
        result = _count_sandbox_lemmas(str(md_file))
        assert result == 4  # 2 table rows + 2 bullet entries

    def test_ignores_header_and_separator_rows(self, tmp_path):
        """Header and separator rows are not counted."""
        level_dir = tmp_path / "a1"
        orch_dir = level_dir / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        sandbox = orch_dir / "lexical-sandbox.md"
        sandbox.write_text(
            "### Nouns\n"
            "| Lemma | Gender | Allowed Forms |\n"
            "|-------|--------|---------------|\n"
            "| дім | masculine | дім, дому |\n",
            encoding="utf-8",
        )
        md_file = level_dir / "test-module.md"
        md_file.touch()
        result = _count_sandbox_lemmas(str(md_file))
        assert result == 1

    def test_empty_sandbox(self, tmp_path):
        """Empty sandbox file returns 0."""
        level_dir = tmp_path / "a1"
        orch_dir = level_dir / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        sandbox = orch_dir / "lexical-sandbox.md"
        sandbox.write_text("## Lexical Sandbox\n### Usage Rules\n", encoding="utf-8")
        md_file = level_dir / "test-module.md"
        md_file.touch()
        result = _count_sandbox_lemmas(str(md_file))
        assert result == 0
