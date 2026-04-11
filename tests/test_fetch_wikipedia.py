"""Tests for scripts/wiki/fetch_wikipedia.py — topic filtering + rate pacing.

Bug history: before this test file, fetch_wikipedia.py:
- Fed every plan content_outline section title to the Wikipedia API as a
  search term, including pedagogical headers like "Джерела: Рішительні
  пункти..." and "Аналіз: Наслідки та значення" that will never match any
  real article.
- Applied its 1-second rate limit ONLY after successful fetches, so runs
  of failed topics fired back-to-back API calls and triggered HTTP 429.
- Did not recognize 429 responses — treated them as "article missing".
- Had no negative cache, so every run re-asked for the same dead topics.

These tests lock in the fixes.
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Load the module directly since it's not on sys.path normally
_SPEC = importlib.util.spec_from_file_location(
    "fetch_wikipedia", ROOT / "scripts" / "wiki" / "fetch_wikipedia.py",
)
assert _SPEC is not None and _SPEC.loader is not None
fw = importlib.util.module_from_spec(_SPEC)
sys.modules["fetch_wikipedia"] = fw
_SPEC.loader.exec_module(fw)


# ──────────────────────────────────────────────────────────────────────
# _is_pedagogical_header — filters out module section headings
# ──────────────────────────────────────────────────────────────────────


class TestIsPedagogicalHeader:
    @pytest.mark.parametrize("topic", [
        "Джерела: Рішительні пункти та таємні інструкції",  # real seminar header
        "Аналіз: Наслідки та значення",                     # real seminar header
        "Вступ: Контекст періоду",
        "Висновки",
        "Контекст",
        "Методологія",
        "Огляд літератури",
        "Conclusion: Key findings",
        "Sources: Primary documents",
        "Introduction",
        "Analysis: Outcomes",
        "Leo: Tolstoy",     # colon with short word on left
        "",
        "ab",               # too short
        "   ",              # whitespace only
    ])
    def test_headers_are_filtered(self, topic):
        assert fw._is_pedagogical_header(topic) is True

    @pytest.mark.parametrize("topic", [
        "Тарас Шевченко",
        "Іван Франко",
        "Київська Русь",
        "Президентство Дуайта Ейзенхауера",
        "Голодомор 1932-1933 років",
        "Пересопницьке Євангеліє",
        "Ізборник Святослава",
        # Long-prefixed colon-containing title that is genuinely an article
        "Pacta et Constitutiones legum libertatumque Exercitus Zaporoviensis: Philippus Orlyk",
    ])
    def test_real_topics_are_kept(self, topic):
        assert fw._is_pedagogical_header(topic) is False


# ──────────────────────────────────────────────────────────────────────
# _extract_topics_from_plans — end-to-end topic list filtering
# ──────────────────────────────────────────────────────────────────────


class TestExtractTopicsFromPlans:
    def test_filters_pedagogical_sections(self, tmp_path):
        # Build a fake plan with mixed good + bad sections
        plans_dir = tmp_path / "plans" / "hist"
        plans_dir.mkdir(parents=True)
        plan_yaml = """
title: "Кийвська Русь"
content_outline:
  - section: "Джерела: Рішительні пункти"
    words: 500
  - section: "Волхви та ідоли"
    words: 500
  - section: "Аналіз: Причини розпаду"
    words: 500
  - section: "Князь Володимир Великий"
    words: 500
  - section: "Висновки"
    words: 200
"""
        (plans_dir / "kyivska-rus.yaml").write_text(plan_yaml, encoding="utf-8")

        with patch.object(fw, "CURRICULUM_DIR", tmp_path):
            topics = fw._extract_topics_from_plans("hist")

        # Plan title kept
        assert "Кийвська Русь" in topics
        # Real section titles kept
        assert "Волхви та ідоли" in topics
        assert "Князь Володимир Великий" in topics
        # Pedagogical headers filtered out
        assert "Джерела: Рішительні пункти" not in topics
        assert "Аналіз: Причини розпаду" not in topics
        assert "Висновки" not in topics

    def test_deduplicates_same_topic_across_plans(self, tmp_path):
        plans_dir = tmp_path / "plans" / "lit"
        plans_dir.mkdir(parents=True)
        (plans_dir / "a.yaml").write_text('title: "Тарас Шевченко"\n', encoding="utf-8")
        (plans_dir / "b.yaml").write_text('title: "Тарас Шевченко"\n', encoding="utf-8")
        (plans_dir / "c.yaml").write_text('title: "тарас шевченко"\n', encoding="utf-8")

        with patch.object(fw, "CURRICULUM_DIR", tmp_path):
            topics = fw._extract_topics_from_plans("lit")

        # Case-insensitive dedup: exactly one
        lowered = [t.lower() for t in topics]
        assert lowered.count("тарас шевченко") == 1

    def test_missing_track_returns_empty(self, tmp_path):
        with patch.object(fw, "CURRICULUM_DIR", tmp_path):
            assert fw._extract_topics_from_plans("nonexistent") == []

    def test_strips_english_parenthetical(self, tmp_path):
        plans_dir = tmp_path / "plans" / "hist"
        plans_dir.mkdir(parents=True)
        (plans_dir / "x.yaml").write_text(
            'title: "Test"\n'
            'content_outline:\n'
            '  - section: "Народний календар (Folk Calendar)"\n',
            encoding="utf-8",
        )
        with patch.object(fw, "CURRICULUM_DIR", tmp_path):
            topics = fw._extract_topics_from_plans("hist")
        assert "Народний календар" in topics
        # English parenthetical stripped
        assert not any("(Folk Calendar)" in t for t in topics)


# ──────────────────────────────────────────────────────────────────────
# _pace_api_call — ensures minimum gap between consecutive calls
# ──────────────────────────────────────────────────────────────────────


class TestPaceApiCall:
    def setup_method(self):
        # Reset the module-level tracker before each test
        fw._last_call_ts = 0.0

    def test_first_call_has_no_delay(self):
        start = time.monotonic()
        fw._pace_api_call()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # should return ~immediately

    def test_second_call_within_interval_sleeps(self):
        # Use a tighter interval for speed
        with patch.object(fw, "_MIN_INTERVAL_S", 0.3):
            fw._pace_api_call()
            start = time.monotonic()
            fw._pace_api_call()  # immediately after → should sleep ~0.3s
            elapsed = time.monotonic() - start
        # Should have slept at least the interval
        assert elapsed >= 0.25
        assert elapsed < 0.5  # but not much more

    def test_gap_longer_than_interval_no_sleep(self):
        with patch.object(fw, "_MIN_INTERVAL_S", 0.1):
            fw._pace_api_call()
            time.sleep(0.2)  # wait longer than the interval
            start = time.monotonic()
            fw._pace_api_call()
            elapsed = time.monotonic() - start
        # Second call should not have slept
        assert elapsed < 0.05


# ──────────────────────────────────────────────────────────────────────
# _api_get — 429 handling with backoff
# ──────────────────────────────────────────────────────────────────────


class TestApiGet429Handling:
    def test_429_triggers_backoff_then_retry_then_success(self):
        import urllib.error

        # First call returns 429, second returns real JSON
        responses = []

        class FakeResp:
            def __init__(self, data): self._data = data
            def read(self): return self._data
            def __enter__(self): return self
            def __exit__(self, *args): pass

        def fake_urlopen(req, timeout):
            if len(responses) == 0:
                responses.append("429")
                raise urllib.error.HTTPError(
                    url="x", code=429, msg="Too Many Requests", hdrs=None, fp=None,
                )
            return FakeResp(b'{"query": {"pages": {}}}')

        # Collapse the backoff to near-zero for fast test
        with patch.object(fw, "_BACKOFF_BASE_S", 0.05), \
             patch.object(fw, "_BACKOFF_MAX_S", 0.1), \
             patch.object(fw, "_MIN_INTERVAL_S", 0.0), \
             patch("urllib.request.urlopen", side_effect=fake_urlopen):
            fw._last_call_ts = 0.0
            result = fw._api_get("http://fake/api")

        assert result is not None
        assert len(responses) == 1  # one 429 seen, one success

    def test_429_exhausts_retries_returns_none(self):
        import urllib.error

        def always_429(req, timeout):
            raise urllib.error.HTTPError(
                url="x", code=429, msg="Too Many Requests", hdrs=None, fp=None,
            )

        with patch.object(fw, "_BACKOFF_BASE_S", 0.01), \
             patch.object(fw, "_BACKOFF_MAX_S", 0.02), \
             patch.object(fw, "_MIN_INTERVAL_S", 0.0), \
             patch.object(fw, "_MAX_429_RETRIES", 3), \
             patch("urllib.request.urlopen", side_effect=always_429):
            fw._last_call_ts = 0.0
            result = fw._api_get("http://fake/api")

        assert result is None

    def test_non_429_http_error_returns_none_immediately(self):
        import urllib.error

        calls = []

        def always_404(req, timeout):
            calls.append(1)
            raise urllib.error.HTTPError(
                url="x", code=404, msg="Not Found", hdrs=None, fp=None,
            )

        with patch.object(fw, "_MIN_INTERVAL_S", 0.0), \
             patch("urllib.request.urlopen", side_effect=always_404):
            fw._last_call_ts = 0.0
            result = fw._api_get("http://fake/api")

        assert result is None
        assert len(calls) == 1  # no retry on non-429
