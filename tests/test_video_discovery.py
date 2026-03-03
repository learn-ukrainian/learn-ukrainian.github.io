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
    extract_lemmas_from_hints,
    build_search_keywords,
    build_discovery_keywords,
    cap_query,
    search_blogs,
    format_blog_discovery,
    search_rag,
    format_rag_discovery,
    _SEMINAR_TRACKS,
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
            assert result.warning == "No videos found across channels"


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
        assert "No discoveries available" in text

    def test_no_relevant_videos(self):
        result = DiscoveryResult(
            videos=[VideoCandidate(url="x", channel="c", title="t", relevance_score=0.2)],
        )
        text = format_discovery_for_template(result)
        assert "No relevant resources found" in text

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


# ---------------------------------------------------------------------------
# Keyword cleaning
# ---------------------------------------------------------------------------

class TestExtractLemmas:
    def test_simple(self):
        assert extract_lemmas_from_hints(["книга (book)"]) == ["книга"]

    def test_multiple_forms_slash(self):
        result = extract_lemmas_from_hints(["цей / ця / це (this)"])
        assert "цей" in result
        assert "ця" in result
        assert "це" in result

    def test_strips_description(self):
        result = extract_lemmas_from_hints(["стіл (table) — High frequency"])
        assert result == ["стіл"]
        assert "table" not in result
        assert "High" not in result

    def test_empty(self):
        assert extract_lemmas_from_hints([]) == []

    def test_non_string(self):
        assert extract_lemmas_from_hints([None, 42, ""]) == []

    def test_apostrophe(self):
        result = extract_lemmas_from_hints(["м'яч (ball)"])
        assert "м'яч" in result


class TestBuildSearchKeywords:
    def test_basic_structure(self):
        kw = build_search_keywords("Topic Title", {"required": ["книга (book)"]})
        assert kw[0] == "Topic Title"
        assert "книга" in kw

    def test_deduplicates(self):
        kw = build_search_keywords("книга", {"required": ["книга (book)"]})
        count = sum(1 for k in kw if k == "книга")
        assert count == 1

    def test_list_format(self):
        kw = build_search_keywords("Test", ["стіл (table)", "ручка (pen)"])
        assert "стіл" in kw
        assert "ручка" in kw

    def test_max_keywords(self):
        hints = [f"слово{i} (word{i})" for i in range(20)]
        kw = build_search_keywords("Test", {"required": hints}, max_keywords=4)
        assert len(kw) <= 4


class TestCapQuery:
    def test_joins(self):
        assert cap_query(["hello", "world"]) == "hello world"

    def test_caps_length(self):
        result = cap_query(["a" * 50, "b" * 50, "c" * 50], max_len=60)
        assert len(result) <= 60

    def test_empty(self):
        assert cap_query([]) == ""


# ---------------------------------------------------------------------------
# Blog discovery
# ---------------------------------------------------------------------------

class TestSearchBlogs:
    def test_finds_results(self):
        results = search_blogs(
            module_slug="the-cyrillic-code-i",
            level="A1",
            topic_title="The Cyrillic Code I",
            keywords=["alphabet", "cyrillic", "letters"],
        )
        assert len(results) >= 1

    def test_caps_results(self):
        results = search_blogs(
            module_slug="test",
            level="A1",
            topic_title="Grammar",
            keywords=["grammar", "cases"],
            max_results=2,
        )
        assert len(results) <= 2

    def test_keyword_gate_rejects_level_only_match(self):
        """Level-only match (zero keyword overlap) should be filtered out."""
        # Use keywords that won't match any blog content
        results = search_blogs(
            module_slug="nonexistent-module",
            level="A1",
            topic_title="zzz_fake_topic_zzz",
            keywords=["zzz_fake_topic_zzz", "xyznonexistent123"],
        )
        # All results should have at least some keyword overlap,
        # so gibberish keywords should yield zero blog results
        # (only pre-computed score DB might return something)
        for r in results:
            # Any result from Layer 2 (blog DB matching) would require keyword overlap
            # Pre-computed results (Layer 1) are fine — they use a different mechanism
            assert r.get("relevance_score", 0) > 0

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


class TestFormatBlogDiscovery:
    def test_empty(self):
        result = format_blog_discovery([])
        assert "No blog articles" in result

    def test_has_content(self):
        result = format_blog_discovery([
            {"title": "Test", "url": "https://x.com", "source": "test",
             "relevance_score": 0.8, "topics": ["grammar"]},
        ])
        assert "Test" in result
        assert "https://x.com" in result


# ---------------------------------------------------------------------------
# RAG discovery
# ---------------------------------------------------------------------------

class TestSearchRag:
    def test_returns_empty_when_qdrant_unavailable(self):
        """Should gracefully degrade when Qdrant is not running."""
        with patch("video_discovery._is_qdrant_available", return_value=False):
            result = search_rag(["книга", "стіл"], track="a1", level="A1")
            assert result["text_chunks"] == []
            assert result["images"] == []
            assert result["literary"] == []

    def test_returns_empty_on_import_error(self):
        """Should degrade if rag.query is not importable."""
        with patch("video_discovery._is_qdrant_available", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("no rag")):
                result = search_rag(["тест"], track="a1")
                assert result["text_chunks"] == []

    def test_seminar_tracks_search_literary(self):
        """Seminar tracks should also search literary sources."""
        import types

        mock_text = [{"score": 0.9, "text": "chunk", "chunk_id": "c1", "section_title": "S", "grade": 3, "author": "A", "page": 1, "trust_tier": 1}]
        mock_img = [{"score": 0.8, "image_path": "/img.png", "grade": 3, "description_uk": "Desc", "teaching_value": "high"}]
        mock_lit = [{"score": 0.7, "text": "літопис", "chunk_id": "l1", "work": "ПВЛ", "year": 1113, "genre": "chronicle", "language_period": "old_east_slavic"}]

        # Create a mock rag.query module
        mock_rag_query = types.ModuleType("rag.query")
        mock_rag_query.search_text = lambda *a, **kw: mock_text
        mock_rag_query.search_images = lambda *a, **kw: mock_img
        mock_rag_query.search_literary = lambda *a, **kw: mock_lit

        with patch("video_discovery._is_qdrant_available", return_value=True):
            with patch.dict("sys.modules", {"rag.query": mock_rag_query}):
                result = search_rag(["козаки"], track="hist", level="HIST")
                assert len(result["text_chunks"]) >= 1
                assert len(result["images"]) >= 1
                assert len(result["literary"]) >= 1

    def test_core_tracks_skip_literary(self):
        """Core tracks (A1-C2) should NOT search literary sources."""
        assert "a1" not in _SEMINAR_TRACKS
        assert "b2" not in _SEMINAR_TRACKS

    def test_seminar_track_list(self):
        """Seminar track list should be complete."""
        for t in ["hist", "istorio", "bio", "lit", "oes", "ruth"]:
            assert t in _SEMINAR_TRACKS

    def test_empty_keywords(self):
        """Empty keywords should return empty results."""
        with patch("video_discovery._is_qdrant_available", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError):
                result = search_rag([], track="a1")
                assert result["text_chunks"] == []


class TestFormatRagDiscovery:
    def test_empty(self):
        result = format_rag_discovery([], [], [])
        assert "No RAG content found" in result

    def test_text_chunks(self):
        chunks = [{"section_title": "Іменники", "grade": 3, "text": "Іменник — це частина мови..."}]
        result = format_rag_discovery(chunks, [], [])
        assert "Textbook References" in result
        assert "Іменники" in result
        assert "Grade 3" in result

    def test_images(self):
        images = [{"description_uk": "Діти в класі", "grade": 2, "teaching_value": "high", "image_path": "/img.png"}]
        result = format_rag_discovery([], images, [])
        assert "Textbook Images" in result
        assert "Діти в класі" in result
        assert "high" in result

    def test_literary(self):
        literary = [{"work": "Слово о полку Ігоревім", "year": 1187, "genre": "epic", "text": "Не лѣпо ли ны бяшетъ..."}]
        result = format_rag_discovery([], [], literary)
        assert "Literary Primary Sources" in result
        assert "Слово о полку Ігоревім" in result

    def test_combined(self):
        chunks = [{"section_title": "S", "grade": 1, "text": "text"}]
        images = [{"description_uk": "D", "grade": 1, "teaching_value": "high", "image_path": "p"}]
        literary = [{"work": "W", "year": 1000, "genre": "g", "text": "t"}]
        result = format_rag_discovery(chunks, images, literary)
        assert "Textbook References" in result
        assert "Textbook Images" in result
        assert "Literary Primary Sources" in result


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


class TestFormatDiscoveryWithRag:
    def test_includes_rag_section(self):
        result = DiscoveryResult(
            rag_chunks=[{"section_title": "Дієслова", "grade": 4, "text": "Дієслово означає дію..."}],
        )
        text = format_discovery_for_template(result)
        assert "Textbook References" in text
        assert "Дієслова" in text

    def test_no_rag_section_when_empty(self):
        result = DiscoveryResult(
            videos=[VideoCandidate(url="x", channel="c", title="t", relevance_score=0.9)],
        )
        text = format_discovery_for_template(result)
        assert "Textbook References" not in text


# ---------------------------------------------------------------------------
# build_discovery_keywords
# ---------------------------------------------------------------------------

# Minimal plan fixtures based on real plan files
_PLAN_CYRILLIC = {
    "title": "The Cyrillic Code I",
    "focus": "grammar",
    "objectives": [
        "Learner can recognize and pronounce 6 Ukrainian letters (А, М, Л, У, Н, С)",
        "Learner can classify letters as голосні (vowels) or приголосні (consonants)",
        "Learner can combine letters into open and closed syllables",
        "Learner can read simple words using the 6 known letters",
    ],
    "content_outline": [
        {"section": "Вступ", "words": 300},
        {"section": "Голосні — А, У", "words": 400},
        {"section": "Приголосні — М, Л, Н, С", "words": 500},
        {"section": "Перші склади — First Syllables", "words": 350},
        {"section": "Практика читання — Reading Practice", "words": 300},
        {"section": "Підсумок", "words": 150},
    ],
    "grammar": [
        "Letter recognition (А, М, Л, У, Н, С)",
        "Sound-letter correspondence",
        "Vowel vs consonant classification",
        "Syllable formation",
    ],
    "vocabulary_hints": {
        "required": [
            "мама — first word readable from 6 letters",
            "нас (us) — pronoun",
            "сам (self/alone) — adjective",
            "луна (echo) — noun",
            "сума (bag/sum) — noun",
        ],
    },
}

_PLAN_OBJECTS = {
    "title": "My World: Objects",
    "focus": "grammar",
    "objectives": [
        "Learner can use цей/ця/це/ці to point to objects near them",
        "Learner can name 40 common household and everyday objects",
    ],
    "content_outline": [
        {"section": "Вступ (Introduction)", "words": 350},
        {"section": "Презентація (Presentation)", "words": 650},
        {"section": "Практика (Practice)", "words": 450},
        {"section": "Культурний контекст (Cultural Insight)", "words": 300},
    ],
    "grammar": [
        "Demonstratives цей/ця/це/ці (this)",
        "Gender agreement with demonstratives",
    ],
    "vocabulary_hints": {
        "required": [
            "цей / ця / це / ці (this) — High frequency",
            "стіл (table) — Household",
        ],
    },
}

_PLAN_FAMILY = {
    "title": "My Family",
    "focus": "vocabulary",
    "objectives": [
        "Learner can name family members",
        "Learner can describe family relationships",
    ],
    "content_outline": [
        {"section": "Вступ: Моя сім'я (Introduction: My Family)", "words": 400},
    ],
    "grammar": [
        "Family vocabulary",
        "Possessives with family members",
    ],
    "vocabulary_hints": {
        "required": [
            "мама (mom) — рідна мама",
            "тато (dad) — рідний тато",
            "сім'я (family) — велика сім'я",
        ],
    },
}


class TestBuildDiscoveryKeywords:
    def test_empty_plan(self):
        assert build_discovery_keywords({}) == []

    def test_title_is_first(self):
        kw = build_discovery_keywords({"title": "Test Title"})
        assert kw[0] == "Test Title"

    def test_cyrillic_code_has_letter_keywords(self):
        kw = build_discovery_keywords(_PLAN_CYRILLIC)
        kw_lower = [k.lower() for k in kw]
        assert kw[0] == "The Cyrillic Code I"
        # Should include section-derived keywords about letters/syllables
        assert any("голосні" in k for k in kw_lower)
        assert any("приголосні" in k for k in kw_lower)
        # Should include grammar topics
        assert any("syllable" in k for k in kw_lower)

    def test_objects_has_demonstrative_keywords(self):
        kw = build_discovery_keywords(_PLAN_OBJECTS)
        kw_lower = [k.lower() for k in kw]
        assert kw[0] == "My World: Objects"
        # Generic PPP labels (Презентація, Practice) should be filtered out
        assert "презентація" not in kw_lower
        assert "practice" not in kw_lower
        # Should include grammar-derived keywords
        assert any("demonstratives" in k or "цей" in k for k in kw_lower)

    def test_family_has_family_keywords(self):
        kw = build_discovery_keywords(_PLAN_FAMILY)
        kw_lower = [k.lower() for k in kw]
        assert kw[0] == "My Family"
        # Should get "My Family" from section title
        assert any("сім'я" in k or "family" in k for k in kw_lower)

    def test_caps_at_max(self):
        kw = build_discovery_keywords(_PLAN_CYRILLIC, max_keywords=5)
        assert len(kw) <= 5

    def test_no_duplicates(self):
        kw = build_discovery_keywords(_PLAN_CYRILLIC)
        lower_kw = [k.lower() for k in kw]
        assert len(lower_kw) == len(set(lower_kw))

    def test_includes_focus(self):
        kw = build_discovery_keywords({"title": "Test", "focus": "cultural"})
        assert "cultural" in kw

    def test_skips_generic_sections(self):
        """Generic section names like 'Вступ' and 'Підсумок' should be skipped."""
        kw = build_discovery_keywords(_PLAN_CYRILLIC)
        kw_lower = [k.lower() for k in kw]
        assert "вступ" not in kw_lower
        assert "підсумок" not in kw_lower

    def test_vocab_hints_as_list(self):
        """Should handle vocab_hints as a plain list (not dict)."""
        plan = {
            "title": "Test",
            "vocabulary_hints": ["книга (book)", "стіл (table)"],
        }
        kw = build_discovery_keywords(plan)
        assert "книга" in kw
        assert "стіл" in kw

    def test_objectives_extract_noun_phrases(self):
        plan = {
            "title": "Test",
            "objectives": [
                "Learner can recognize and pronounce 6 Ukrainian letters",
            ],
        }
        kw = build_discovery_keywords(plan)
        # Should extract "Ukrainian letters" (minus the number)
        assert any("Ukrainian letters" in k for k in kw)
