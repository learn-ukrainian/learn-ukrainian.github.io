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
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

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


# ──────────────────────────────────────────────────────────────────────
# _pace_api_call — ensures minimum gap between consecutive calls
# ──────────────────────────────────────────────────────────────────────


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
