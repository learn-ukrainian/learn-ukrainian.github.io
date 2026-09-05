"""Tests for navsi200 YouTube captions coverage ledger, fetcher, and privacy gates (#4705)."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts/ is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from navsi200_captions import (
    DEFAULT_LEDGER_PATH,
    clean_vtt_text,
    fetch_single_caption,
    load_caption_ledger,
    order_lessons_by_priority,
    scrub_teacher_names,
)
from navsi200_catalog import load_catalog


class TestNavsi200CaptionsLedger:
    """Verification suite for navsi200-captions-ledger.json and associated utilities."""

    @pytest.fixture(scope="class")
    def ledger(self) -> dict:
        return load_caption_ledger()

    @pytest.fixture(scope="class")
    def catalog(self) -> dict:
        return load_catalog()

    def test_ledger_file_exists(self) -> None:
        assert DEFAULT_LEDGER_PATH.exists(), f"Ledger file not found at {DEFAULT_LEDGER_PATH}"
        assert DEFAULT_LEDGER_PATH.stat().st_size > 1000

    def test_ledger_metadata_shape(self, ledger: dict) -> None:
        assert ledger.get("version") == 1
        assert ledger.get("caption_lang") == "uk"
        assert "generated_at" in ledger
        assert isinstance(ledger.get("summary"), dict)
        assert isinstance(ledger.get("lessons"), list)
        assert isinstance(ledger.get("entries"), list)
        assert len(ledger["lessons"]) == len(ledger["entries"])

    def test_privacy_no_teacher_names_in_ledger(self) -> None:
        raw_text = DEFAULT_LEDGER_PATH.read_text(encoding="utf-8").lower()
        forbidden_names = ["огойко", "охойко", "ohoiko", "анни огойко", "анна огойко"]
        for name in forbidden_names:
            assert name not in raw_text, f"Privacy violation: found teacher name '{name}' in committed ledger"

    def test_privacy_no_verbatim_captions_in_ledger(self, ledger: dict) -> None:
        for entry in ledger["lessons"]:
            assert "transcript" not in entry, "Verbatim transcript key found in ledger entry"
            assert "subtitles" not in entry, "Verbatim subtitles key found in ledger entry"
            assert "text" not in entry, "Verbatim text key found in ledger entry"
            assert "raw_captions" not in entry, "Raw captions key found in ledger entry"

    def test_lessons_shape_and_types(self, ledger: dict) -> None:
        yt_id_pattern = re.compile(r"^[a-zA-Z0-9_\-]{11}$")
        sha256_pattern = re.compile(r"^[a-f0-9]{64}$")
        allowed_statuses = {"available", "bot_blocked", "unavailable", "no_captions", "timeout"}

        lessons = ledger["lessons"]
        assert len(lessons) >= 150

        seen_video_ids = set()
        for entry in lessons:
            vid = entry.get("video_id")
            assert isinstance(vid, str), f"Invalid video_id type: {vid}"
            assert yt_id_pattern.match(vid), f"Invalid video_id format: {vid}"
            assert vid not in seen_video_ids, f"Duplicate video_id: {vid}"
            seen_video_ids.add(vid)

            title = entry.get("title")
            assert isinstance(title, str) and len(title) > 3

            topic = entry.get("topic")
            assert isinstance(topic, str) and len(topic) > 0

            caption_lang = entry.get("caption_lang")
            assert caption_lang == "uk", f"Language must be pinned to 'uk', got {caption_lang}"

            status = entry.get("status")
            assert status in allowed_statuses, f"Unexpected status: {status}"

            char_count = entry.get("char_count")
            assert isinstance(char_count, int) and char_count >= 0

            sha256_hash = entry.get("sha256")
            if status == "available":
                assert isinstance(sha256_hash, str)
                assert sha256_pattern.match(sha256_hash), f"Invalid sha256 format: {sha256_hash}"
                assert char_count > 0, "Available caption must have positive character count"
            else:
                assert sha256_hash is None or sha256_hash == ""
                assert char_count == 0

            assert isinstance(entry.get("is_priority"), bool)

    def test_priority_ordering_in_ledger(self, ledger: dict) -> None:
        lessons = ledger["lessons"]
        priority_indices = [i for i, entry in enumerate(lessons) if entry["is_priority"]]
        non_priority_indices = [i for i, entry in enumerate(lessons) if not entry["is_priority"]]

        assert len(priority_indices) > 0
        assert len(non_priority_indices) > 0
        assert max(priority_indices) < min(non_priority_indices), (
            "Priority lessons must all appear before non-priority lessons in the coverage ledger"
        )

    def test_all_catalog_videos_accounted_for(self, ledger: dict, catalog: dict) -> None:
        catalog_video_ids = {l["video_id"] for l in catalog["lessons"]}
        ledger_video_ids = {l["video_id"] for l in ledger["lessons"]}

        assert catalog_video_ids == ledger_video_ids, (
            f"Mismatch between catalog and ledger video IDs: "
            f"missing={catalog_video_ids - ledger_video_ids}, extra={ledger_video_ids - catalog_video_ids}"
        )

    def test_summary_consistency(self, ledger: dict) -> None:
        summary = ledger["summary"]
        lessons = ledger["lessons"]

        assert summary["total_lessons"] == len(lessons)
        assert summary["priority_lessons"] == sum(1 for l in lessons if l["is_priority"])
        assert summary["non_priority_lessons"] == sum(1 for l in lessons if not l["is_priority"])

        status_counts = summary["status_counts"]
        assert sum(status_counts.values()) == len(lessons)
        for st, count in status_counts.items():
            assert sum(1 for l in lessons if l["status"] == st) == count

        total_chars = sum(l["char_count"] for l in lessons)
        assert summary["total_chars"] == total_chars

    def test_scrub_teacher_names_unit(self) -> None:
        raw_title = "ОНЛАЙН-ПРАКТИКУМИ ДО ЗНО від Анни Огойко"
        sanitized = scrub_teacher_names(raw_title)
        assert "огойко" not in sanitized.lower()
        assert sanitized == "ОНЛАЙН-ПРАКТИКУМИ ДО ЗНО"

        teacher_only = "Анна Огойко"
        assert scrub_teacher_names(teacher_only) == ""

        clean_title = "Пароніми і лексичні помилки на НМТ"
        assert scrub_teacher_names(clean_title) == clean_title

    def test_clean_vtt_text_unit(self) -> None:
        sample_vtt = """WEBVTT
Kind: captions
Language: uk

00:00:01.000 --> 00:00:03.000
<c>Привіт</c>, друзі!

00:00:03.000 --> 00:00:05.000
<c>Привіт</c>, друзі!

00:00:05.000 --> 00:00:08.000
Сьогодні ми вивчаємо <b>пароніми</b>.
"""
        cleaned = clean_vtt_text(sample_vtt)
        assert "WEBVTT" not in cleaned
        assert "-->" not in cleaned
        assert "<c>" not in cleaned
        assert "<b>" not in cleaned
        # Deduplication check
        assert cleaned.count("Привіт, друзі!") == 1
        assert "Сьогодні ми вивчаємо пароніми." in cleaned

    def test_order_lessons_by_priority_unit(self) -> None:
        fake_lessons = [
            {
                "id": "l1",
                "video_id": "vid1",
                "topic": "всяка_всячина",
                "topics": ["всяка_всячина"],
                "is_priority": False,
            },
            {"id": "l2", "video_id": "vid2", "topic": "наголос", "topics": ["наголос"], "is_priority": True},
            {"id": "l3", "video_id": "vid3", "topic": "пароніми", "topics": ["пароніми"], "is_priority": True},
            {"id": "l4", "video_id": "vid4", "topic": "синтаксис", "topics": ["синтаксис"], "is_priority": False},
        ]
        ordered = order_lessons_by_priority(fake_lessons)
        assert [l["id"] for l in ordered] == ["l3", "l2", "l1", "l4"]

    def test_mock_fetch_single_caption_available(self, tmp_path: Path) -> None:
        video_id = "testvid1234"
        vtt_file = tmp_path / f"{video_id}.uk.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nТестовий текст.", encoding="utf-8")

        status, char_count, sha256_hash = fetch_single_caption(video_id, tmp_path)
        assert status == "available"
        assert char_count == len("Тестовий текст.")
        assert isinstance(sha256_hash, str) and len(sha256_hash) == 64

    def test_mock_fetch_single_caption_bot_blocked(self, tmp_path: Path) -> None:
        video_id = "blockedvid1"
        fake_proc = MagicMock()
        fake_proc.returncode = 1
        fake_proc.stdout = ""
        fake_proc.stderr = "ERROR: [youtube] blockedvid1: Sign in to confirm you’re not a bot."

        with patch("subprocess.run", return_value=fake_proc):
            status, char_count, sha256_hash = fetch_single_caption(video_id, tmp_path)

        assert status == "bot_blocked"
        assert char_count == 0
        assert sha256_hash is None
