"""Tests for navsi200 lesson catalog shape, schema, and loader."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

# Ensure scripts/ is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from navsi200_catalog import (
    DEFAULT_CATALOG_PATH,
    PRIORITY_TOPICS,
    get_catalog_summary,
    get_lesson_by_id,
    get_lesson_by_video_id,
    get_lessons_by_topic,
    get_priority_lessons,
    load_catalog,
)


class TestNavsi200Catalog:
    """Verification suite for navsi200-catalog.json and its loader."""

    @pytest.fixture(scope="class")
    def catalog(self) -> dict:
        return load_catalog()

    def test_catalog_file_exists(self) -> None:
        assert DEFAULT_CATALOG_PATH.exists()
        assert DEFAULT_CATALOG_PATH.stat().st_size > 1000

    def test_catalog_metadata_shape(self, catalog: dict) -> None:
        assert catalog.get("version") == 1
        assert "Анна Огойко" in catalog.get("author", "")
        assert isinstance(catalog.get("source_urls"), list)
        assert len(catalog["source_urls"]) >= 2
        assert "https://navsi200.com/videos/" in catalog["source_urls"]
        assert "https://www.youtube.com/@navsi200" in catalog["source_urls"]
        assert catalog.get("scraped_at") is not None
        assert isinstance(catalog.get("summary"), dict)
        assert isinstance(catalog.get("priority_topics"), list)
        assert isinstance(catalog.get("topics"), dict)
        assert isinstance(catalog.get("lessons"), list)

    def test_priority_topics_defined(self, catalog: dict) -> None:
        for topic in PRIORITY_TOPICS:
            assert topic in catalog["priority_topics"]
            assert topic in catalog["topics"]
            assert len(catalog["topics"][topic]) > 0

    def test_lessons_shape_and_types(self, catalog: dict) -> None:
        dur_pattern = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
        yt_id_pattern = re.compile(r"^[a-zA-Z0-9_\-]{11}$")

        lessons = catalog["lessons"]
        assert len(lessons) >= 150

        seen_ids = set()
        seen_video_ids = set()

        for lesson in lessons:
            # Identifier checks
            lesson_id = lesson.get("id")
            assert isinstance(lesson_id, str) and len(lesson_id) > 0
            assert lesson_id not in seen_ids, f"Duplicate lesson ID: {lesson_id}"
            seen_ids.add(lesson_id)

            video_id = lesson.get("video_id")
            assert isinstance(video_id, str)
            assert yt_id_pattern.match(video_id), f"Invalid video_id: {video_id}"
            assert video_id not in seen_video_ids, f"Duplicate video ID: {video_id}"
            seen_video_ids.add(video_id)

            # Title check
            title = lesson.get("title")
            assert isinstance(title, str) and len(title) > 3

            # URL checks
            url = lesson.get("url")
            assert isinstance(url, str)
            parsed_url = urlparse(url)
            assert parsed_url.scheme == "https"
            assert parsed_url.netloc in {"navsi200.com", "www.navsi200.com", "youtube.com", "www.youtube.com"}

            yt_url = lesson.get("youtube_url")
            assert isinstance(yt_url, str) and yt_url.startswith("https://www.youtube.com/watch?v=")

            # Duration checks
            duration = lesson.get("duration")
            assert isinstance(duration, str)
            assert dur_pattern.match(duration), f"Invalid duration format: {duration}"

            dur_sec = lesson.get("duration_seconds")
            assert isinstance(dur_sec, int) and dur_sec > 0

            # Verify duration_seconds matches duration string
            parts = [int(p) for p in duration.split(":")]
            expected_sec = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
            assert dur_sec == expected_sec

            # Topic checks
            topic = lesson.get("topic")
            assert isinstance(topic, str) and len(topic) > 0

            topics = lesson.get("topics")
            assert isinstance(topics, list) and len(topics) > 0

            is_prio = lesson.get("is_priority")
            assert isinstance(is_prio, bool)

    def test_priority_topic_paronyms(self, catalog: dict) -> None:
        paronyms = get_priority_lessons(catalog, "пароніми")
        assert len(paronyms) >= 1
        p_lesson = paronyms[0]
        assert "паронім" in p_lesson["title"].lower() or "пароніми" in p_lesson.get("navsi200_title", "").lower()
        assert p_lesson["video_id"] == "KHTDig7qPLg"
        assert p_lesson["duration"] == "11:29"
        assert p_lesson["url"] == "https://navsi200.com/videos/paronimy/"

    def test_priority_topic_stress(self, catalog: dict) -> None:
        stress_lessons = get_priority_lessons(catalog, "наголос")
        assert len(stress_lessons) >= 3
        video_ids = {l["video_id"] for l in stress_lessons}
        assert "bRt0PfOL6cg" in video_ids  # Картки з усіма наголосами (25:51)
        assert "CYHFtuRWRQo" in video_ids  # Як запам’ятати наголоси (16:06)
        assert "9y8MiNPmpNI" in video_ids  # 5 порад + наголоси (8:32)

    def test_priority_topic_lexical_norm(self, catalog: dict) -> None:
        lex_lessons = get_priority_lessons(catalog, "лексична норма")
        assert len(lex_lessons) >= 5
        video_ids = {l["video_id"] for l in lex_lessons}
        assert "YDkL2r1aMfQ" in video_ids  # 100 завдань: лексичні помилки
        assert "hDoKMDo06Jc" in video_ids  # 50 карток: лексичні помилки дієслів
        assert "sfz6Fnv_R84" in video_ids  # 100 пар слів: іншомовні слова та українські відповідники
        assert "KHTDig7qPLg" in video_ids  # Пароніми і лексичні помилки
        assert "dC_7FDw8aCU" in video_ids  # Всяка всячина з лексики

    def test_priority_topic_typical_zno(self, catalog: dict) -> None:
        zno_lessons = get_priority_lessons(catalog, "найтиповіші завдання ЗНО")
        assert len(zno_lessons) >= 99

    def test_get_priority_lessons_all(self, catalog: dict) -> None:
        all_prio = get_priority_lessons(catalog)
        assert len(all_prio) >= 100
        for lesson in all_prio:
            assert lesson.get("is_priority") is True

    def test_invalid_priority_topic_raises(self, catalog: dict) -> None:
        with pytest.raises(ValueError, match="Unknown priority topic"):
            get_priority_lessons(catalog, "неіснуюча тема")

    def test_get_lessons_by_topic(self, catalog: dict) -> None:
        phonetics = get_lessons_by_topic(catalog, "фонетика_орфоепія_графіка")
        assert len(phonetics) >= 11
        for p in phonetics:
            assert "фонетика_орфоепія_графіка" in p["topics"]

    def test_get_lesson_by_id_and_video_id(self, catalog: dict) -> None:
        lesson = get_lesson_by_id(catalog, "navsi200-paronimy")
        assert lesson is not None
        assert lesson["video_id"] == "KHTDig7qPLg"

        by_vid = get_lesson_by_video_id(catalog, "bRt0PfOL6cg")
        assert by_vid is not None
        assert by_vid["id"] == "navsi200-naholosy"

        assert get_lesson_by_id(catalog, "non-existent") is None
        assert get_lesson_by_video_id(catalog, "non-existent") is None

    def test_summary_consistency(self, catalog: dict) -> None:
        summary = get_catalog_summary(catalog)
        assert summary["total_lessons"] == len(catalog["lessons"])
        assert summary["priority_topic_counts"]["пароніми"] == len(catalog["topics"]["пароніми"])
        assert summary["priority_topic_counts"]["наголос"] == len(catalog["topics"]["наголос"])
        assert summary["priority_topic_counts"]["лексична норма"] == len(catalog["topics"]["лексична норма"])
        assert summary["priority_topic_counts"]["найтиповіші завдання ЗНО"] == len(
            catalog["topics"]["найтиповіші завдання ЗНО"]
        )
        assert summary["total_duration_seconds"] == sum(l["duration_seconds"] for l in catalog["lessons"])
