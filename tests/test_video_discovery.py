"""Tests for video_discovery.py — standalone video/blog discovery module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ and scripts/content/ are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "content"))

from video_discovery_helpers import (
    extract_lemmas_from_hints,
)

from video_discovery import (
    DiscoveryResult,
    VideoCandidate,
    clean_srt,
    read_discovery_yaml,
    search_blogs,
    search_channel,
    write_discovery_yaml,
)

# ---------------------------------------------------------------------------
# clean_srt
# ---------------------------------------------------------------------------

class TestCleanSrt:
    def test_strips_metadata(self):
        srt = (
            "1\n"
            "00:00:01,000 --> 00:00:03,000\n"
            "Привіт, світе!\n"
            "\n"
            "2\n"
            "00:00:04,000 --> 00:00:06,000\n"
            "Як справи?\n"
        )
        result = clean_srt(srt)
        assert result == "Привіт, світе! Як справи?"

    def test_strips_html_tags(self):
        srt = "1\n00:00:01,000 --> 00:00:02,000\n<c>Текст</c> з <b>тегами</b>\n"
        result = clean_srt(srt)
        assert result == "Текст з тегами"

    def test_deduplicates_consecutive_lines(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:02,000\nПовтор\n\n"
            "2\n00:00:02,000 --> 00:00:03,000\nПовтор\n\n"
            "3\n00:00:03,000 --> 00:00:04,000\nНовий\n"
        )
        result = clean_srt(srt)
        assert result == "Повтор Новий"


# ---------------------------------------------------------------------------
# search_channel — no yt-dlp
# ---------------------------------------------------------------------------

class TestSearchChannel:
    def test_returns_empty_when_no_yt_dlp(self):
        with patch("video_discovery.subprocess.run", side_effect=FileNotFoundError):
            result = search_channel(["тест"], "@testchannel")
            assert result == []


# ---------------------------------------------------------------------------
# download_transcript — failure
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# filter_channels
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# run_discovery — no yt-dlp
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# YAML roundtrip
# ---------------------------------------------------------------------------

class TestYamlRoundtrip:
    def test_write_read_roundtrip(self):
        original = DiscoveryResult(
            discovered_at="2026-03-01T12:00:00+00:00",
            query_keywords=["козаки", "Запоріжжя"],
            videos=[
                VideoCandidate(
                    url="https://www.youtube.com/watch?v=abc123",
                    channel="Реальна Історія",
                    title="Козаки та Запоріжжя",
                    relevance_score=0.85,
                    relevance_note="Highly relevant to Cossack history",
                    transcript_excerpt="Запорізька Січ була центром...",
                    embed_suggestion="After section 'Козацька доба'",
                ),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discovery.yaml"
            write_discovery_yaml(original, path)
            loaded = read_discovery_yaml(path)

            assert loaded.discovered_at == original.discovered_at
            assert loaded.query_keywords == original.query_keywords
            assert loaded.error is None
            assert len(loaded.videos) == 1
            v = loaded.videos[0]
            assert v.url == "https://www.youtube.com/watch?v=abc123"
            assert v.channel == "Реальна Історія"
            assert v.relevance_score == pytest.approx(0.85)

    def test_write_read_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.yaml"
            write_discovery_yaml(DiscoveryResult(), path)
            loaded = read_discovery_yaml(path)
            assert loaded.videos == []


# ---------------------------------------------------------------------------
# format_discovery_for_template
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Keyword cleaning
# ---------------------------------------------------------------------------

class TestExtractLemmas:

    def test_apostrophe(self):
        result = extract_lemmas_from_hints(["м'яч (ball)"])
        assert "м'яч" in result


# ---------------------------------------------------------------------------
# Blog discovery
# ---------------------------------------------------------------------------

class TestSearchBlogs:

    def test_keyword_gate_with_mock_data(self):
        """Podcast with level match but zero keyword overlap must be rejected."""
        fake_articles = [
            {
                "url": "https://example.com/greetings",
                "title": "Ukrainian Greetings",
                "topics": ["greetings", "hello"],
                "suggested_level": "A1",
                "content_type": "podcast_episode",
                "description": "Learn how to say hello in Ukrainian",
                "source": "ukrainianlessons.com",
            },
            {
                "url": "https://example.com/alphabet",
                "title": "Ukrainian Alphabet Guide",
                "topics": ["alphabet", "letters", "cyrillic"],
                "suggested_level": "A1",
                "content_type": "blog_article",
                "description": "Complete guide to the Ukrainian alphabet and letters",
                "source": "ukrainianlessons.com",
            },
        ]
        with patch("video_discovery._load_blog_dbs", return_value=fake_articles), \
             patch("video_discovery._load_score_db", return_value={}):
            results = search_blogs(
                module_slug="the-cyrillic-code-i",
                level="A1",
                topic_title="The Cyrillic Code I",
                keywords=["alphabet", "letters", "cyrillic"],
            )
            urls = [r["url"] for r in results]
            # Alphabet article matches keywords → included
            assert "https://example.com/alphabet" in urls
            # Greetings episode has zero keyword overlap → excluded by gate
            assert "https://example.com/greetings" not in urls


# ---------------------------------------------------------------------------
# RAG discovery
# ---------------------------------------------------------------------------


class TestDiscoveryYamlRagRoundtrip:
    def test_roundtrip_with_rag_data(self):
        original = DiscoveryResult(
            discovered_at="2026-03-01T12:00:00+00:00",
            query_keywords=["книга"],
            rag_chunks=[{"text": "chunk1", "grade": 3, "section_title": "S"}],
            rag_images=[{"description_uk": "img", "grade": 2, "teaching_value": "high"}],
            rag_literary=[{"work": "ПВЛ", "year": 1113, "text": "літопис"}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discovery.yaml"
            write_discovery_yaml(original, path)
            loaded = read_discovery_yaml(path)

            assert len(loaded.rag_chunks) == 1
            assert loaded.rag_chunks[0]["text"] == "chunk1"
            assert len(loaded.rag_images) == 1
            assert loaded.rag_images[0]["description_uk"] == "img"
            assert len(loaded.rag_literary) == 1
            assert loaded.rag_literary[0]["work"] == "ПВЛ"

    def test_backward_compat_no_rag_fields(self):
        """Old discovery.yaml without rag fields should load fine."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.yaml"
            path.write_text("discovered_at: '2026-01-01'\nquery_keywords: []\nvideos: []\nblogs: []\n")
            loaded = read_discovery_yaml(path)
            assert loaded.rag_chunks == []
            assert loaded.rag_images == []
            assert loaded.rag_literary == []


# ---------------------------------------------------------------------------
# build_discovery_keywords
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029", ""], ids=["NEL", "LS", "PS", "ASCII"])
def test_unicode_structured_boundary_video_title(separator):
    from subprocess import CompletedProcess

    from video_discovery import _yt_dlp_search

    title = f"alpha{separator}beta"
    reply = CompletedProcess([], 0, stdout=f"{title}\tvideo-id\tuk\n", stderr="")
    with patch("video_discovery.subprocess.run", return_value=reply):
        assert _yt_dlp_search("synthetic", 1, 1) == [
            {"title": title, "url": "https://www.youtube.com/watch?v=video-id"},
        ]


@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_video_records_filter_order_limit_and_unterminated(ending):
    from subprocess import CompletedProcess

    from video_discovery import _yt_dlp_search

    records = ["", "malformed", "short\tid", "rejected\tr-id\tru", "first\t1\tuk", "second\t2\ten", "last\t3\tuk"]
    reply = CompletedProcess([], 0, stdout=ending.join(records), stderr="")
    with patch("video_discovery.subprocess.run", return_value=reply):
        assert _yt_dlp_search("synthetic", 8, 2) == [
            {"title": "first", "url": "https://www.youtube.com/watch?v=1"},
            {"title": "second", "url": "https://www.youtube.com/watch?v=2"},
        ]
        assert _yt_dlp_search("synthetic", 8, 9)[-1] == {
            "title": "last", "url": "https://www.youtube.com/watch?v=3",
        }


@pytest.mark.parametrize("stdout", ["", "\n\r\n", "malformed\nshort\tid"])
def test_video_empty_or_malformed_records(stdout):
    from subprocess import CompletedProcess

    from video_discovery import _yt_dlp_search

    reply = CompletedProcess([], 0, stdout=stdout, stderr="")
    with patch("video_discovery.subprocess.run", return_value=reply):
        assert _yt_dlp_search("synthetic", 1, 1) == []


@pytest.mark.parametrize("error_kind", ["rate_limit", "timeout", "nonretryable", "missing", "called_process", "unexpected"])
def test_video_search_failure_and_retry_contract(error_kind):
    import subprocess

    from video_discovery import _yt_dlp_search

    failure = {
        "rate_limit": subprocess.CompletedProcess([], 1, stdout="", stderr="HTTP Error 429"),
        "timeout": subprocess.TimeoutExpired("yt-dlp", 45),
        "nonretryable": subprocess.CompletedProcess([], 1, stdout="", stderr="invalid query"),
        "missing": FileNotFoundError(),
        "called_process": subprocess.CalledProcessError(1, "yt-dlp"),
        "unexpected": RuntimeError("synthetic failure"),
    }[error_kind]
    with patch("video_discovery.subprocess.run", side_effect=[failure] * 3) as run, patch("time.sleep") as sleep:
        assert _yt_dlp_search("synthetic", 3, 1, flat_playlist=True) == []
    expected_calls = 3 if error_kind in {"rate_limit", "timeout"} else 1
    assert run.call_count == expected_calls
    assert sleep.call_count == expected_calls - 1
    assert "--flat-playlist" in run.call_args.args[0]
    assert run.call_args.args[0][-2:] == ["--playlist-end", "3"]
