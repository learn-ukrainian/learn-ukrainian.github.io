"""Tests for navsi200 ASR bake-off runner, scoring helpers, and honest ledger (#4705)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from navsi200_asr_bakeoff import (
    DEFAULT_BAKEOFF_LEDGER_PATH,
    detect_russisms,
    normalize_text,
    transcribe_faster_whisper,
)
from navsi200_catalog import load_catalog

# The bake-off ledger is an untracked artifact (#8809 P1); these tests validate the real produced file.
BAKEOFF_LEDGER = pytest.mark.needs_artifact("corpus_audit_snapshots", "corpus_audit/navsi200-asr-bakeoff-ledger.json")


class TestScoringAndCompareHelpers:
    """Verification of ASR scoring, distance, overlap, and linguistic sanitization."""

    def test_normalize_text_casing_and_apostrophes(self) -> None:
        raw = "М'яч, пʼять, з’їзд та КИЇВ!.."
        expected = "м'яч п'ять з'їзд та київ"
        assert normalize_text(raw) == expected


class TestLinguisticAndRussismDetection:
    """Verification of orthographic and lexical Russism / calque checks."""

    def test_detect_russisms_clean_ukrainian(self) -> None:
        clean = "Сьогодні чудовий день для вивчення української мови та орфографії."
        result = detect_russisms(clean, custom_patterns=["дозволяє", "даний"])
        assert result["letter_count"] == 0
        assert result["letters_found"] == []
        assert result["calque_count"] == 0
        assert result["total_russisms"] == 0

    def test_detect_russisms_russian_specific_letters(self) -> None:
        bad_text = "Это быстрый тест с буквами ы, э, ъ, ё."
        result = detect_russisms(bad_text)
        assert result["letter_count"] >= 4
        assert "ы" in result["letters_found"]
        assert "э" in result["letters_found"]
        assert "ъ" in result["letters_found"]
        assert "ё" in result["letters_found"]
        assert result["total_russisms"] >= 4

    def test_detect_russisms_calques_from_gec(self) -> None:
        text = "Цей підхід дозволяє вирішити даний випадок."
        result = detect_russisms(text, custom_patterns=["дозволяє", "даний"])
        assert result["calque_count"] == 2
        assert "дозволяє" in result["calques_found"]
        assert "даний" in result["calques_found"]


class TestEngineSpecificationAndPinning:
    """Verification of engine configuration, licensing, and language pinning."""

    def test_whisper_strictly_requires_uk_pinning(self) -> None:
        with pytest.raises(ValueError, match="strictly pinned to 'uk'"):
            transcribe_faster_whisper(b"", language="ru")

        with pytest.raises(ValueError, match="strictly pinned to 'uk'"):
            transcribe_faster_whisper(b"", language="auto")  # type: ignore[arg-type]


class TestAsrBakeoffLedgerAndPrivacy:
    """Verification of honest ledger accounting and OPSEC privacy gates."""

    @pytest.fixture(scope="class")
    def ledger_data(self) -> dict:
        import json

        assert DEFAULT_BAKEOFF_LEDGER_PATH.exists(), f"Ledger not found at {DEFAULT_BAKEOFF_LEDGER_PATH}"
        with DEFAULT_BAKEOFF_LEDGER_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def catalog_data(self) -> dict:
        return load_catalog()

    @BAKEOFF_LEDGER
    def test_privacy_no_teacher_names_in_ledger(self) -> None:
        raw = DEFAULT_BAKEOFF_LEDGER_PATH.read_text(encoding="utf-8").lower()
        forbidden = ["огойко", "охойко", "ohoiko", "анни огойко", "анна огойко"]
        for name in forbidden:
            assert name not in raw, f"Privacy violation: found '{name}' in committed bake-off ledger"

    @BAKEOFF_LEDGER
    def test_privacy_no_verbatim_transcripts_in_ledger(self, ledger_data: dict) -> None:
        for entry in ledger_data["lessons"]:
            assert "transcript" not in entry
            assert "subtitles" not in entry
            assert "text" not in entry
            assert "raw_captions" not in entry
            assert "hypothesis" not in entry

    def test_raw_dumps_directory_is_gitignored(self) -> None:
        res = subprocess.run(
            ["git", "check-ignore", "data/native-reviewer-lessons/navsi200-asr-dumps/test.txt"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert res.returncode == 0, "Raw ASR dumps directory must be ignored by git"

    def test_cli_help_has_no_home_paths(self) -> None:
        res = subprocess.run(
            [sys.executable, "scripts/navsi200_asr_bakeoff.py", "--help"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        assert "--whisper-model" in res.stdout
        assert "--wav2vec2-model" in res.stdout
        assert "/home/" not in res.stdout + res.stderr

    @BAKEOFF_LEDGER
    def test_honest_accounting_in_ledger(self, ledger_data: dict, catalog_data: dict) -> None:
        summary = ledger_data["summary"]
        lessons = ledger_data["lessons"]

        assert summary["total_catalog_lessons"] == 158
        assert len(lessons) == 158
        assert len(catalog_data["lessons"]) == 158

        # Honest counts: 157 captions bot-blocked, 1 available
        assert summary["captions_available"] == 1
        assert summary["captions_bot_blocked"] == 157
        # Audio is not claimed for unauthenticated cloud runner
        assert summary["audio_bot_blocked"] == 158
        assert summary["audio_available"] == 0

        # Verify all catalog video IDs are accounted for
        catalog_ids = {l["video_id"] for l in catalog_data["lessons"]}
        ledger_ids = {l["video_id"] for l in lessons}
        assert catalog_ids == ledger_ids
