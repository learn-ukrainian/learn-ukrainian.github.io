"""Tests for video_discovery.py — standalone video/blog discovery module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from video_discovery import (
    VideoCandidate,
    DiscoveryResult,
    clean_srt,
    download_transcript,
    filter_channels,
    search_channel,
    score_candidates,
    run_discovery,
    write_discovery_yaml,
    read_discovery_yaml,
    format_discovery_for_template,
    DEFAULT_CHANNELS,
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
        assert "Текст з тегами" == result

    def test_deduplicates_consecutive_lines(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:02,000\nПовтор\n\n"
            "2\n00:00:02,000 --> 00:00:03,000\nПовтор\n\n"
            "3\n00:00:03,000 --> 00:00:04,000\nНовий\n"
        )
        result = clean_srt(srt)
        assert result == "Повтор Новий"

    def test_empty_input(self):
        assert clean_srt("") == ""

    def test_only_metadata(self):
        srt = "1\n00:00:01,000 --> 00:00:02,000\n\n"
        assert clean_srt(srt) == ""


# ---------------------------------------------------------------------------
# search_channel — no yt-dlp
# ---------------------------------------------------------------------------

class TestSearchChannel:
    def test_returns_empty_when_no_yt_dlp(self):
        with patch("video_discovery.subprocess.run", side_effect=FileNotFoundError):
            result = search_channel(["тест"], "@testchannel")
            assert result == []

    def test_returns_empty_on_timeout(self):
        import subprocess
        with patch("video_discovery.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = search_channel(["тест"], "@testchannel")
            assert result == []


# ---------------------------------------------------------------------------
# download_transcript — failure
# ---------------------------------------------------------------------------

class TestDownloadTranscript:
    def test_returns_empty_on_failure(self):
        with patch("video_discovery.subprocess.run", side_effect=FileNotFoundError):
            result = download_transcript("https://www.youtube.com/watch?v=test")
            assert result == ""


# ---------------------------------------------------------------------------
# filter_channels
# ---------------------------------------------------------------------------

class TestFilterChannels:
    def test_wildcard_matches_any_track(self):
        channels = [{"name": "Test", "handle": "@test", "tracks": ["*"]}]
        assert len(filter_channels(channels, "hist")) == 1
        assert len(filter_channels(channels, "a1")) == 1

    def test_specific_track_match(self):
        channels = [{"name": "Test", "handle": "@test", "tracks": ["hist", "bio"]}]
        assert len(filter_channels(channels, "hist")) == 1
        assert len(filter_channels(channels, "bio")) == 1
        assert len(filter_channels(channels, "a1")) == 0

    def test_base_track_extraction(self):
        """b2-pro should match channels tagged with 'b2'."""
        channels = [{"name": "Test", "handle": "@test", "tracks": ["b2"]}]
        assert len(filter_channels(channels, "b2-pro")) == 1

    def test_default_channels_have_wildcard(self):
        """At least one channel should match any track via wildcard."""
        result = filter_channels(DEFAULT_CHANNELS, "a1")
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# run_discovery — no yt-dlp
# ---------------------------------------------------------------------------

class TestRunDiscovery:
    def test_returns_result_with_error_when_no_yt_dlp(self):
        def mock_dispatch(*args, **kwargs):
            return (True, "ok")

        with patch("video_discovery.subprocess.run", side_effect=FileNotFoundError):
            result = run_discovery(
                topic="Тест",
                keywords=["тест"],
                outline=[],
                vocab=[],
                dispatch_fn=mock_dispatch,
                track="a1",
            )
            assert isinstance(result, DiscoveryResult)
            assert result.error == "No videos found across channels"


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

class TestFormatDiscovery:
    def test_empty_result(self):
        result = DiscoveryResult(error="No videos found")
        text = format_discovery_for_template(result)
        assert "No video discoveries available" in text

    def test_no_relevant_videos(self):
        result = DiscoveryResult(
            videos=[VideoCandidate(url="x", channel="c", title="t", relevance_score=0.2)],
        )
        text = format_discovery_for_template(result)
        assert "No relevant videos found" in text

    def test_formats_relevant_videos(self):
        result = DiscoveryResult(
            videos=[
                VideoCandidate(
                    url="https://youtube.com/watch?v=abc",
                    channel="Test Channel",
                    title="Test Video",
                    relevance_score=0.9,
                    relevance_note="Very relevant",
                    embed_suggestion="After intro",
                    transcript_excerpt="Sample text",
                ),
            ],
        )
        text = format_discovery_for_template(result)
        assert "**Test Video**" in text
        assert "Test Channel" in text
        assert "https://youtube.com/watch?v=abc" in text
        assert "0.9" in text
        assert "After intro" in text


# ---------------------------------------------------------------------------
# Phase registration (build_module.py integration)
# ---------------------------------------------------------------------------

class TestPhaseRegistration:
    def test_discover_in_phase_sequence(self):
        from scripts.build_module import PHASE_SEQUENCE_V4
        assert "discover" in PHASE_SEQUENCE_V4
        idx_r = PHASE_SEQUENCE_V4.index("research")
        idx_d = PHASE_SEQUENCE_V4.index("discover")
        idx_c = PHASE_SEQUENCE_V4.index("content")
        assert idx_r < idx_d < idx_c

    def test_discover_in_state_ids(self):
        from scripts.build_module import _V4_PHASE_STATE_IDS
        assert "discover" in _V4_PHASE_STATE_IDS

    def test_discover_in_labels(self):
        from scripts.build_module import PHASE_LABELS_V4
        assert "discover" in PHASE_LABELS_V4

    def test_discover_in_functions(self):
        from scripts.build_module import PHASE_FUNCTIONS_V4
        assert "discover" in PHASE_FUNCTIONS_V4
        assert callable(PHASE_FUNCTIONS_V4["discover"])
