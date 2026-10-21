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
    PRIORITY_TOPICS,
    load_catalog,
)


class TestNavsi200Catalog:
    """Verification suite for navsi200-catalog.json and its loader."""

    @pytest.fixture(scope="class")
    def catalog(self) -> dict:
        return load_catalog()

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
