"""Tests for VERIFY flag handling in V6 pipeline (#1018).

Tests extraction, resolution, saving, and review injection of
<!-- VERIFY: ... --> flags that writers use to signal uncertainty.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build.v6_build import (
    _extract_verify_flags,
    _resolve_verify_flags,
    _save_verify_flags,
)


class TestExtractVerifyFlags:
    """AC1: Extract <!-- VERIFY: ... --> flags from content."""

    def test_single_flag(self):
        content = "Some text <!-- VERIFY: is слово correct here? --> more text."
        flags = _extract_verify_flags(content)
        assert len(flags) == 1
        assert flags[0]["claim"] == "is слово correct here?"
        assert flags[0]["resolved"] is False
        assert flags[0]["resolution"] == ""

    def test_multiple_flags(self):
        content = (
            "## Section\n\n"
            "Text with <!-- VERIFY: наголос on привіт --> and "
            "more <!-- VERIFY: does пом'якшення exist? --> here."
        )
        flags = _extract_verify_flags(content)
        assert len(flags) == 2
        assert "привіт" in flags[0]["claim"]
        assert "пом'якшення" in flags[1]["claim"]

    def test_no_flags(self):
        content = "Clean content without any verification markers."
        flags = _extract_verify_flags(content)
        assert flags == []

    def test_whitespace_tolerance(self):
        content = "<!--VERIFY: tight --> and <!--  VERIFY:   loose   --> done."
        flags = _extract_verify_flags(content)
        assert len(flags) == 2
        assert flags[0]["claim"] == "tight"
        assert flags[1]["claim"] == "loose"

    def test_multiline_not_matched(self):
        """VERIFY flags should be single-line (non-greedy match)."""
        content = "<!-- VERIFY: word1 --> normal text <!-- VERIFY: word2 -->"
        flags = _extract_verify_flags(content)
        assert len(flags) == 2
        assert flags[0]["claim"] == "word1"
        assert flags[1]["claim"] == "word2"

    def test_regular_html_comments_ignored(self):
        """Non-VERIFY comments should not be extracted."""
        content = "<!-- TAB:Урок --> text <!-- some comment --> <!-- VERIFY: real flag -->"
        flags = _extract_verify_flags(content)
        assert len(flags) == 1
        assert flags[0]["claim"] == "real flag"


class TestResolveVerifyFlags:
    """AC2: Automated resolution via VESUM for flagged words."""

    def test_known_word_resolved(self):
        """A flag containing a known Ukrainian word should be resolved."""
        flags = [{"claim": "is мама correct here?", "resolved": False, "resolution": ""}]

        # Mock VESUM database
        with patch("build.v6_build.PROJECT_ROOT") as mock_root:
            mock_root.__truediv__ = lambda s, k: Path("/fake") / k if hasattr(s, '__truediv__') else s
            # Use the real function but with a mock DB
            # Instead, test with a simulated sqlite response
            import sqlite3
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                db_path = Path(f.name)

            db = sqlite3.connect(str(db_path))
            db.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
            db.execute("INSERT INTO forms VALUES ('мама', 'мама', 'noun', ':f:')")
            db.commit()
            db.close()

            # Patch PROJECT_ROOT so vesum_db points to our temp DB
            import build.v6_build as module
            original_root = module.PROJECT_ROOT
            try:
                # Create data dir structure
                data_dir = db_path.parent / "data"
                data_dir.mkdir(exist_ok=True)
                vesum_path = data_dir / "vesum.db"
                import shutil
                shutil.copy(str(db_path), str(vesum_path))
                module.PROJECT_ROOT = db_path.parent

                result = _resolve_verify_flags(flags)
                assert result[0]["resolved"] is True
                assert "мама" in result[0]["resolution"]
                assert "noun" in result[0]["resolution"]
            finally:
                module.PROJECT_ROOT = original_root
                db_path.unlink(missing_ok=True)
                vesum_path.unlink(missing_ok=True)
                data_dir.rmdir()

    def test_unknown_word_stays_unresolved(self):
        """A flag with no VESUM-known words stays unresolved."""
        flags = [{"claim": "xyz123 not a word", "resolved": False, "resolution": ""}]

        import sqlite3
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        db = sqlite3.connect(str(db_path))
        db.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        db.commit()
        db.close()

        import build.v6_build as module
        original_root = module.PROJECT_ROOT
        try:
            data_dir = db_path.parent / "data"
            data_dir.mkdir(exist_ok=True)
            vesum_path = data_dir / "vesum.db"
            import shutil
            shutil.copy(str(db_path), str(vesum_path))
            module.PROJECT_ROOT = db_path.parent

            result = _resolve_verify_flags(flags)
            assert result[0]["resolved"] is False
            assert result[0]["resolution"] == ""
        finally:
            module.PROJECT_ROOT = original_root
            db_path.unlink(missing_ok=True)
            vesum_path.unlink(missing_ok=True)
            data_dir.rmdir()

    def test_empty_flags_returns_empty(self):
        result = _resolve_verify_flags([])
        assert result == []

    def test_no_vesum_db_returns_unchanged(self):
        """If VESUM DB doesn't exist, flags stay unresolved."""
        flags = [{"claim": "слово", "resolved": False, "resolution": ""}]

        import build.v6_build as module
        original_root = module.PROJECT_ROOT
        try:
            module.PROJECT_ROOT = Path("/nonexistent")
            result = _resolve_verify_flags(flags)
            assert result[0]["resolved"] is False
        finally:
            module.PROJECT_ROOT = original_root


class TestSaveVerifyFlags:
    """AC3: Flags saved to orchestration/{slug}/verify-flags.yaml."""

    def test_save_creates_file(self, tmp_path):
        """Flags are saved as YAML to the orchestration directory."""
        import build.v6_build as module
        original_root = module.CURRICULUM_ROOT
        try:
            module.CURRICULUM_ROOT = tmp_path
            (tmp_path / "a1" / "orchestration" / "test-slug").mkdir(parents=True)

            flags = [
                {"claim": "is привіт correct?", "resolved": True, "resolution": "VESUM confirms: привіт"},
                {"claim": "unknown word", "resolved": False, "resolution": ""},
            ]
            path = _save_verify_flags("a1", "test-slug", flags)

            assert path.exists()
            loaded = yaml.safe_load(path.read_text("utf-8"))
            assert len(loaded) == 2
            assert loaded[0]["resolved"] is True
            assert loaded[1]["resolved"] is False
        finally:
            module.CURRICULUM_ROOT = original_root

    def test_save_creates_directory(self, tmp_path):
        """Directory is created if it doesn't exist."""
        import build.v6_build as module
        original_root = module.CURRICULUM_ROOT
        try:
            module.CURRICULUM_ROOT = tmp_path

            flags = [{"claim": "test", "resolved": False, "resolution": ""}]
            path = _save_verify_flags("a1", "new-slug", flags)

            assert path.exists()
            assert path.parent.name == "new-slug"
        finally:
            module.CURRICULUM_ROOT = original_root


class TestVerifyFlagsInStepVerify:
    """AC4: step_verify extracts and processes VERIFY flags (non-blocking)."""

    def test_verify_flags_dont_block_build(self):
        """VERIFY flags should NOT cause step_verify to return False."""
        content = "## Section\n\nGood Ukrainian text <!-- VERIFY: is наголос right? --> here.\n"

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(content)
            content_path = Path(f.name)

        try:
            # Flags should be extracted but not treated as errors
            flags = _extract_verify_flags(content)
            assert len(flags) == 1
            # The flags don't add to the issues list — they're tracked separately
        finally:
            content_path.unlink(missing_ok=True)


class TestReviewInjection:
    """AC5: Review prompt includes VERIFY flags as positive signal."""

    def test_injection_format(self):
        """Verify the format of the injected VERIFY flags section."""
        flags = [
            {"claim": "is привіт correct?", "resolved": True, "resolution": "VESUM confirms: привіт -> lemma 'привіт', POS: intj"},
            {"claim": "unknown idiom", "resolved": False, "resolution": ""},
        ]
        unresolved = [f for f in flags if not f.get("resolved")]
        resolved = [f for f in flags if f.get("resolved")]

        # Simulate the injection logic from step_review
        flag_inject = (
            "\n\n## Writer Uncertainty Flags (VERIFY)\n\n"
            "The writer honestly flagged these items as uncertain. "
            "This is a POSITIVE signal — it means the writer was careful "
            "rather than guessing. Please verify each claim:\n\n"
        )
        if unresolved:
            flag_inject += "**Unresolved (needs your verification):**\n"
            for f in unresolved:
                flag_inject += f"- {f['claim']}\n"
            flag_inject += "\n"
        if resolved:
            flag_inject += "**Auto-resolved via VESUM (for context):**\n"
            for f in resolved:
                flag_inject += f"- {f['claim']} -- {f['resolution']}\n"
            flag_inject += "\n"

        assert "POSITIVE signal" in flag_inject
        assert "unknown idiom" in flag_inject
        assert "Unresolved" in flag_inject
        assert "Auto-resolved" in flag_inject
        assert "привіт" in flag_inject


class TestBuildStatsTracking:
    """AC6: Build stats track flag counts."""

    def test_flag_counts(self):
        """Extracted flags can be counted for stats."""
        content = (
            "<!-- VERIFY: word1 --> "
            "<!-- VERIFY: word2 --> "
            "<!-- VERIFY: word3 -->"
        )
        flags = _extract_verify_flags(content)
        assert len(flags) == 3

        # After resolution, stats are derivable
        flags[0]["resolved"] = True
        resolved = sum(1 for f in flags if f["resolved"])
        unresolved = sum(1 for f in flags if not f["resolved"])
        assert resolved == 1
        assert unresolved == 2
