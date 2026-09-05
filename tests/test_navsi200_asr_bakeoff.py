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
    DEFAULT_SAMPLE_AUDIO_PATH,
    ENGINE_METADATA,
    compute_cer,
    compute_token_overlap,
    compute_wer,
    detect_russisms,
    load_audio,
    normalize_text,
    transcribe_faster_whisper,
)
from navsi200_catalog import load_catalog


class TestScoringAndCompareHelpers:
    """Verification of ASR scoring, distance, overlap, and linguistic sanitization."""

    def test_normalize_text_casing_and_apostrophes(self) -> None:
        raw = "М'яч, пʼять, з’їзд та КИЇВ!.."
        expected = "м'яч п'ять з'їзд та київ"
        assert normalize_text(raw) == expected

    def test_normalize_text_empty(self) -> None:
        assert normalize_text("") == ""
        assert normalize_text("   \n\t  ") == ""

    def test_compute_wer_exact_match(self) -> None:
        ref = "це тестове речення для перевірки"
        hyp = "Це тестове речення для перевірки!"
        assert compute_wer(ref, hyp) == 0.0

    def test_compute_wer_empty_cases(self) -> None:
        assert compute_wer("", "") == 0.0
        assert compute_wer("слово", "") == 1.0
        assert compute_wer("", "слово") == 1.0

    def test_compute_wer_operations(self) -> None:
        ref = "один два три чотири"
        # 1 substitution ("два" -> "дванадцять")
        assert compute_wer(ref, "один дванадцять три чотири") == 0.25
        # 1 deletion ("чотири" missing)
        assert compute_wer(ref, "один два три") == 0.25
        # 1 insertion ("нуль")
        assert compute_wer(ref, "нуль один два три чотири") == 0.25
        # 2 errors in 4 words = 0.50
        assert compute_wer(ref, "один сто три п'ять") == 0.50

    def test_compute_cer_exact_and_distance(self) -> None:
        assert compute_cer("або", "або") == 0.0
        assert compute_cer("", "") == 0.0
        assert compute_cer("або", "") == 1.0
        # 1 substitution in 3 chars = 1/3
        assert pytest.approx(compute_cer("або", "аби"), 0.01) == 0.3333

    def test_compute_token_overlap(self) -> None:
        ref = "сонце світить яскраво"
        hyp = "сонце світить тепло"
        overlap = compute_token_overlap(ref, hyp)

        # Intersection: {"сонце", "світить"} (2)
        # Union: {"сонце", "світить", "яскраво", "тепло"} (4)
        assert overlap["jaccard"] == 0.5
        assert pytest.approx(overlap["precision"], 0.01) == 0.6667
        assert pytest.approx(overlap["recall"], 0.01) == 0.6667
        assert pytest.approx(overlap["f1"], 0.01) == 0.6667

    def test_compute_token_overlap_empty(self) -> None:
        assert compute_token_overlap("", "")["jaccard"] == 1.0
        assert compute_token_overlap("слово", "")["jaccard"] == 0.0


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

    def test_engine_metadata_documented(self) -> None:
        required_engines = {"yt-auto-captions", "faster-whisper", "wav2vec2-uk"}
        assert required_engines.issubset(set(ENGINE_METADATA.keys()))

        for name, meta in ENGINE_METADATA.items():
            assert "engine" in meta, f"Missing engine in {name}"
            assert "provider" in meta, f"Missing provider in {name}"
            assert "license" in meta, f"Missing license in {name}"
            assert "language_pinning" in meta, f"Missing language_pinning in {name}"

    def test_whisper_strictly_requires_uk_pinning(self) -> None:
        with pytest.raises(ValueError, match="strictly pinned to 'uk'"):
            transcribe_faster_whisper(b"", language="ru")

        with pytest.raises(ValueError, match="strictly pinned to 'uk'"):
            transcribe_faster_whisper(b"", language="auto")  # type: ignore[arg-type]


class TestAudioLoading:
    """Verification of robust audio file loading."""

    def test_load_audio_fixture(self) -> None:
        assert DEFAULT_SAMPLE_AUDIO_PATH.exists()
        audio_data, sr = load_audio(DEFAULT_SAMPLE_AUDIO_PATH, target_sr=16000)
        assert sr == 16000
        assert len(audio_data) > 0
        assert audio_data.dtype.kind == "f"
        assert -1.05 <= float(audio_data.min()) <= 1.05
        assert -1.05 <= float(audio_data.max()) <= 1.05


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

    def test_privacy_no_teacher_names_in_ledger(self) -> None:
        raw = DEFAULT_BAKEOFF_LEDGER_PATH.read_text(encoding="utf-8").lower()
        forbidden = ["огойко", "охойко", "ohoiko", "анни огойко", "анна огойко"]
        for name in forbidden:
            assert name not in raw, f"Privacy violation: found '{name}' in committed bake-off ledger"

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

    def test_calibration_benchmark_metrics_present(self, ledger_data: dict) -> None:
        bench = ledger_data.get("calibration_benchmark")
        assert bench is not None, "Calibration benchmark must be recorded in ledger"
        assert "engines" in bench
        engines = bench["engines"]

        # Faster-whisper
        assert "faster-whisper" in engines
        w_eng = engines["faster-whisper"]
        assert w_eng["status"] == "success"
        assert w_eng["language_pinned"] == "uk"
        assert isinstance(w_eng["wer"], (int, float))
        assert isinstance(w_eng["cer"], (int, float))
        assert "jaccard" in w_eng["overlap"]

        # Wav2Vec2
        assert "wav2vec2-uk" in engines
        v_eng = engines["wav2vec2-uk"]
        assert v_eng["status"] == "success"
        assert isinstance(v_eng["wer"], (int, float))
        assert isinstance(v_eng["cer"], (int, float))
        assert "jaccard" in v_eng["overlap"]
