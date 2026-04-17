"""Tests for wiki source loading, enrichment, and topic grouping."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add scripts/ to path so wiki package is importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))
sys.path.insert(0, _project_root)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def literary_jsonl(tmp_path):
    """Create a sample literary text JSONL file."""
    chunks = [
        {
            "chunk_id": "abc123_c0000",
            "text": "Козацтво як явище виникло на українських землях.",
            "work": "Історія козацтва",
            "author": "shcherbak",
            "year": 2000,
            "genre": "history",
            "language_period": "modern",
            "token_count": 8,
        },
        {
            "chunk_id": "abc123_c0001",
            "text": "Думи — це ліро-епічні твори, що оспівують героїзм козаків.",
            "work": "Історія козацтва",
            "author": "shcherbak",
            "year": 2000,
            "genre": "history",
            "language_period": "modern",
            "token_count": 10,
        },
        {
            "chunk_id": "abc123_c0002",
            "text": "Загадки в українській народній традиції мають давнє коріння.",
            "work": "Народна творчість",
            "author": "kostomarov",
            "year": 1872,
            "genre": "folklore",
            "language_period": "modern",
            "token_count": 9,
        },
    ]
    jsonl_path = tmp_path / "test-literary.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return jsonl_path


@pytest.fixture
def textbook_jsonl(tmp_path):
    """Create a sample textbook chunk JSONL file."""
    chunks = [
        {
            "chunk_id": "5-klas-ukrmova_s0001",
            "text": "Іменник — це частина мови, що називає предмет.",
            "token_count": 9,
            "section_title": "Сторінка 5",
            "section_level": 2,
            "quality": {"is_clean": True, "clean_ratio": 1.0},
            "grade": 5,
            "author": "avramenko",
            "year": 2022,
            "subject": "ukrmova",
            "trust_tier": 1,
            "pdf_stem": "5-klas-ukrmova-avramenko-2022",
        },
        {
            "chunk_id": "5-klas-ukrmova_s0002",
            "text": "garbled text !@#$%",
            "token_count": 3,
            "section_title": "Сторінка 6",
            "section_level": 2,
            "quality": {"is_clean": False, "clean_ratio": 0.3},
            "grade": 5,
            "author": "avramenko",
            "year": 2022,
            "subject": "ukrmova",
            "trust_tier": 1,
            "pdf_stem": "5-klas-ukrmova-avramenko-2022",
        },
    ]
    grade_dir = tmp_path / "grade-05"
    grade_dir.mkdir()
    jsonl_path = grade_dir / "5-klas-ukrmova-avramenko-2022.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return jsonl_path


@pytest.fixture
def discovery_dir(tmp_path):
    """Create a sample discovery directory for the folk track."""
    discovery_path = tmp_path / "curriculum" / "l2-uk-en" / "folk" / "discovery"
    discovery_path.mkdir(parents=True)

    discovery_data = {
        "discovered_at": "2026-03-13T23:41:40.557703+00:00",
        "query_keywords": [
            "Думи лицарські: Оспівування звитяги",
            "Самійло Кішка",
            "Козацький ідеал лицарства",
            "Heroic dumas — Cossack martial ethos",
            "лицарський",
            "звитяга",
        ],
        "error": None,
        "warning": None,
        "videos": [],
        "blogs": [],
        "rag_chunks": [
            {
                "chunk_id": "7-klas-ukrlit_s0105",
                "text": "Думи — це народні ліро-епічні пісні героїчного змісту.",
                "section_title": "Сторінка 70",
                "grade": 7,
                "author": "zabolotnyi",
                "score": 0.5,
            },
        ],
        "rag_images": [],
        "rag_literary": [
            {
                "chunk_id": "literary_c0001",
                "text": "Думи козацькі оспівують подвиги запорозьких козаків.",
                "score": 0.6,
            },
        ],
    }

    with open(discovery_path / "dumy-lytsarski.yaml", "w", encoding="utf-8") as f:
        yaml.dump(discovery_data, f, allow_unicode=True)

    # A second discovery file
    discovery_data_2 = {
        "discovered_at": "2026-03-13T23:42:00+00:00",
        "query_keywords": ["Загадки: Метафоричне бачення світу"],
        "error": None,
        "rag_chunks": [],
        "rag_images": [],
        "rag_literary": [],
    }
    with open(discovery_path / "zahadky.yaml", "w", encoding="utf-8") as f:
        yaml.dump(discovery_data_2, f, allow_unicode=True)

    return tmp_path / "curriculum" / "l2-uk-en"


@pytest.fixture
def folk_micro_genres_yaml(tmp_path):
    """Create a sample folk_micro_genres.yaml."""
    data = {
        "загадки": [
            {"text": "Голубе́ вітри́ло весь світ накри́ло.", "answer": "не́бо",
             "themes": ["природа"], "difficulty": "A2", "source": "Вашуленко, 3 клас"},
            {"text": "Що схо́дить без насі́ння?", "answer": "со́нце",
             "themes": ["природа"], "difficulty": "A2", "source": "Вашуленко, 3 клас"},
        ],
        "прислів'я": [
            {"text": "Без діла слабіє сила.", "themes": ["праця"],
             "difficulty": "A2", "source": "Большакова, 2 клас"},
        ],
    }
    yaml_path = tmp_path / "data" / "folk_micro_genres.yaml"
    yaml_path.parent.mkdir(parents=True)
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    return yaml_path


# ── Tests: sources.py ─────────────────────────────────────────────


class TestLoadLiteraryJsonl:
    def test_loads_all_chunks(self, literary_jsonl):
        from wiki.sources import load_literary_jsonl
        chunks = load_literary_jsonl(literary_jsonl)
        assert len(chunks) == 3

    def test_chunk_has_required_fields(self, literary_jsonl):
        from wiki.sources import load_literary_jsonl
        chunks = load_literary_jsonl(literary_jsonl)
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk

    def test_empty_lines_skipped(self, tmp_path):
        from wiki.sources import load_literary_jsonl
        path = tmp_path / "empty.jsonl"
        path.write_text('{"chunk_id": "a", "text": "hello"}\n\n\n{"chunk_id": "b", "text": "world"}\n')
        chunks = load_literary_jsonl(path)
        assert len(chunks) == 2


class TestLoadTextbookJsonl:
    def test_filters_garbled_chunks(self, textbook_jsonl):
        from wiki.sources import load_textbook_jsonl
        chunks = load_textbook_jsonl(textbook_jsonl)
        assert len(chunks) == 1  # Only clean chunk
        assert chunks[0]["chunk_id"] == "5-klas-ukrmova_s0001"

    def test_keeps_chunks_without_quality_field(self, tmp_path):
        from wiki.sources import load_textbook_jsonl
        path = tmp_path / "no-quality.jsonl"
        path.write_text('{"chunk_id": "x", "text": "valid"}\n')
        chunks = load_textbook_jsonl(path)
        assert len(chunks) == 1


class TestListTextbookSources:
    def test_filters_by_grade(self, tmp_path):
        from wiki.sources import list_textbook_sources
        # Create grade dirs with files
        for grade in [5, 6, 7]:
            d = tmp_path / f"grade-{grade:02d}"
            d.mkdir()
            (d / f"{grade}-klas-ukrmova.jsonl").write_text("{}")

        with patch("wiki.sources.TEXTBOOK_CHUNKS_DIR", tmp_path):
            files = list_textbook_sources(grades=[5, 7])
        assert len(files) == 2
        assert all("grade-06" not in str(f) for f in files)

    def test_filters_by_subject(self, tmp_path):
        from wiki.sources import list_textbook_sources
        d = tmp_path / "grade-05"
        d.mkdir()
        (d / "5-klas-ukrmova-avramenko.jsonl").write_text("{}")
        (d / "5-klas-istoria-gisem.jsonl").write_text("{}")
        (d / "5-klas-ukrlit-avramenko.jsonl").write_text("{}")

        with patch("wiki.sources.TEXTBOOK_CHUNKS_DIR", tmp_path):
            files = list_textbook_sources(subjects=["istoria"])
        assert len(files) == 1
        assert "istoria" in files[0].stem

    def test_returns_empty_if_dir_missing(self, tmp_path):
        from wiki.sources import list_textbook_sources
        with patch("wiki.sources.TEXTBOOK_CHUNKS_DIR", tmp_path / "nonexistent"):
            assert list_textbook_sources() == []


class TestDiscovery:
    def test_load_discovery(self, discovery_dir):
        from wiki.sources import load_discovery
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir):
            disc = load_discovery("folk", "dumy-lytsarski")
        assert disc is not None
        assert "query_keywords" in disc
        assert len(disc["query_keywords"]) == 6

    def test_load_discovery_missing(self, discovery_dir):
        from wiki.sources import load_discovery
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir):
            assert load_discovery("folk", "nonexistent") is None

    def test_list_discovery_slugs(self, discovery_dir):
        from wiki.sources import list_discovery_slugs
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir):
            slugs = list_discovery_slugs("folk")
        assert slugs == ["dumy-lytsarski", "zahadky"]

    def test_list_discovery_slugs_missing_track(self, discovery_dir):
        from wiki.sources import list_discovery_slugs
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir):
            assert list_discovery_slugs("nonexistent") == []


class TestExtractSourceRefs:
    def test_extracts_all_types(self):
        from wiki.sources import extract_source_refs
        disc = {
            "rag_literary": [{"chunk_id": "lit1"}, {"chunk_id": "lit2"}],
            "rag_chunks": [{"chunk_id": "text1"}],
            "rag_images": [{"chunk_id": "img1"}],
        }
        refs = extract_source_refs(disc)
        assert refs["literary"] == ["lit1", "lit2"]
        assert refs["textbook"] == ["text1"]
        assert refs["image"] == ["img1"]

    def test_handles_empty_discovery(self):
        from wiki.sources import extract_source_refs
        refs = extract_source_refs({})
        assert refs == {"literary": [], "textbook": [], "image": []}

    def test_skips_empty_chunk_ids(self):
        from wiki.sources import extract_source_refs
        disc = {
            "rag_literary": [{"chunk_id": ""}, {"chunk_id": "valid"}],
            "rag_chunks": [],
            "rag_images": [],
        }
        refs = extract_source_refs(disc)
        assert refs["literary"] == ["valid"]


class TestFindLiteraryByKeywords:
    def test_matches_by_stem(self, tmp_path):
        from wiki.sources import find_literary_by_keywords
        # Create fake literary files
        (tmp_path / "ukrlib-shevchenko.jsonl").write_text("{}")
        (tmp_path / "wave7-kostomarov-mifolohiia.jsonl").write_text("{}")
        (tmp_path / "wave9-shevelov-fonolohiia.jsonl").write_text("{}")

        with patch("wiki.sources.LITERARY_DIR", tmp_path):
            matches = find_literary_by_keywords(["shevchenko", "shevelov"])
        assert len(matches) == 2
        stems = {m.stem for m in matches}
        assert "ukrlib-shevchenko" in stems
        assert "wave9-shevelov-fonolohiia" in stems

    def test_no_matches(self, tmp_path):
        from wiki.sources import find_literary_by_keywords
        (tmp_path / "some-file.jsonl").write_text("{}")
        with patch("wiki.sources.LITERARY_DIR", tmp_path):
            assert find_literary_by_keywords(["nonexistent"]) == []


class TestGatherDiscoverySources:
    def test_returns_error_for_missing_slug(self, discovery_dir):
        from wiki.sources import gather_discovery_sources
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir):
            result = gather_discovery_sources("folk", "nonexistent")
        assert "error" in result

    def test_gathers_inline_chunks(self, discovery_dir):
        from wiki.sources import gather_discovery_sources
        with patch("wiki.sources.CURRICULUM_DIR", discovery_dir), \
             patch("wiki.sources.LITERARY_DIR", Path("/nonexistent")):
            result = gather_discovery_sources("folk", "dumy-lytsarski")
        assert "discovery" in result
        assert len(result["literary_chunks"]) == 1
        assert len(result["textbook_chunks"]) == 1
        assert result["keywords"][0] == "Думи лицарські: Оспівування звитяги"


# ── Tests: enrichment.py ──────────────────────────────────────────


class TestExtractUkrainianKeywords:
    def test_extracts_cyrillic_words(self):
        from wiki.enrichment import _extract_ukrainian_keywords
        sources_info = {
            "discovery": {
                "query_keywords": [
                    "Думи лицарські: Оспівування звитяги",
                    "Самійло Кішка",
                    "Heroic dumas — Cossack martial ethos",
                ],
            },
        }
        keywords = _extract_ukrainian_keywords(sources_info)
        assert "думи" in keywords
        assert "лицарські" in keywords
        assert "звитяги" in keywords
        assert "самійло" in keywords
        assert "кішка" in keywords
        # English words should NOT be present
        assert "heroic" not in keywords
        assert "cossack" not in keywords

    def test_skips_short_words(self):
        from wiki.enrichment import _extract_ukrainian_keywords
        sources_info = {
            "discovery": {
                "query_keywords": ["Це як то так"],
            },
        }
        keywords = _extract_ukrainian_keywords(sources_info)
        # All words are 3 chars or less
        assert len(keywords) == 0

    def test_handles_missing_discovery(self):
        from wiki.enrichment import _extract_ukrainian_keywords
        assert _extract_ukrainian_keywords({}) == set()
        assert _extract_ukrainian_keywords({"discovery": {}}) == set()


# The `TestLoadRelevantChunks` class used to exercise a now-retired
# function (`wiki.enrichment._load_relevant_chunks`) that scanned
# hand-maintained literary JSONL files keyed by slug. Seminar-track
# keyword scoring was moved into `sources_db.search_literary()`
# (FTS5-indexed) — the function it tested no longer exists. Covering
# the FTS5 path requires a live SQLite fixture which doesn't fit
# these unit tests. Removed rather than faked.


class TestLoadFolkMicroGenres:
    def test_loads_zahadky(self, folk_micro_genres_yaml):
        from wiki.enrichment import _load_folk_micro_genres
        with patch("wiki.enrichment.PROJECT_ROOT", folk_micro_genres_yaml.parent.parent):
            chunks = _load_folk_micro_genres("zahadky")
        assert len(chunks) == 2
        assert "не́бо" in chunks[0]["text"]
        assert chunks[0]["chunk_id"].startswith("folk-micro-")

    def test_loads_prykazky(self, folk_micro_genres_yaml):
        from wiki.enrichment import _load_folk_micro_genres
        with patch("wiki.enrichment.PROJECT_ROOT", folk_micro_genres_yaml.parent.parent):
            chunks = _load_folk_micro_genres("prykazky-ta-pryslivia")
        assert len(chunks) == 1  # Deduplicated — both keys map to same genre
        assert "слабіє сила" in chunks[0]["text"]

    def test_no_match_returns_empty(self, folk_micro_genres_yaml):
        from wiki.enrichment import _load_folk_micro_genres
        with patch("wiki.enrichment.PROJECT_ROOT", folk_micro_genres_yaml.parent.parent):
            chunks = _load_folk_micro_genres("dumy-lytsarski")
        assert chunks == []

    def test_handles_missing_file(self, tmp_path):
        from wiki.enrichment import _load_folk_micro_genres
        with patch("wiki.enrichment.PROJECT_ROOT", tmp_path):
            chunks = _load_folk_micro_genres("zahadky")
        assert chunks == []


class TestEnrichSources:
    """
    The empty-query-keywords path: when ``discovery.query_keywords`` is
    empty, ``enrich_sources`` should skip all FTS5 search branches and
    only expose the discovery chunks (plus any local/external mappings
    it can resolve offline). These tests target that invariant — with
    FTS5 calls guarded off by the empty-keyword condition, no live
    SQLite fixture is needed.
    """

    def test_caps_at_80k_chars_for_a1(self):
        """A1 track cap is 80K chars (see `enrichment.char_caps`)."""
        from wiki.enrichment import enrich_sources
        # Huge discovery chunks, no query keywords (so FTS5 branches skipped)
        big_chunk = {"text": "x" * 50_000, "chunk_id": "big1"}
        big_chunk2 = {"text": "y" * 50_000, "chunk_id": "big2"}
        sources_info = {
            "discovery": {"query_keywords": []},
            "literary_chunks": [big_chunk, big_chunk2],
            "textbook_chunks": [],
            "literary_files": [],
        }
        # Track "a1" has the smallest cap (80_000); picking it makes the
        # assertion tight. Seminar/folk tracks get 150K, which these
        # 2×50K chunks wouldn't exceed.
        result = enrich_sources("a1", "test", sources_info)
        total_chars = sum(len(c.get("text", "")) for c in result)
        assert total_chars <= 80_001

    def test_includes_discovery_chunks(self):
        from wiki.enrichment import enrich_sources
        sources_info = {
            "discovery": {"query_keywords": []},
            "literary_chunks": [{"text": "literary text", "chunk_id": "lit1"}],
            "textbook_chunks": [{"text": "textbook text", "chunk_id": "text1"}],
            "literary_files": [],
        }
        result = enrich_sources("folk", "test", sources_info)
        # Enrichment may add local/external mapped chunks for the track,
        # but the two discovery chunks MUST survive — that's the contract.
        ids = {c["chunk_id"] for c in result}
        assert "lit1" in ids
        assert "text1" in ids

    def test_fallback_when_no_sources(self):
        from wiki.enrichment import enrich_sources
        sources_info = {
            "discovery": {"query_keywords": []},
            "literary_chunks": [],
            "textbook_chunks": [],
            "literary_files": [],
        }
        result = enrich_sources("folk", "test-slug-without-resources", sources_info)
        # With empty discovery + empty keywords + a slug that has no
        # local/external mapping, the fallback ``no-source`` chunk must
        # be emitted so the compiler has something to chew on.
        assert any(c.get("chunk_id") == "no-source" for c in result), (
            f"expected 'no-source' fallback in {[c.get('chunk_id') for c in result]}"
        )


# ── Tests: state.py ───────────────────────────────────────────────


class TestState:
    def test_mark_and_check_compiled(self, tmp_path):
        from wiki.state import is_compiled, load_progress, mark_compiled
        with patch("wiki.state.WIKI_STATE_DIR", tmp_path / ".state"), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            assert not is_compiled("folk/genres/dumy")
            mark_compiled("folk/genres/dumy", source_count=5, word_count=1500, model="test")
            assert is_compiled("folk/genres/dumy")

            progress = load_progress()
            assert progress["articles"]["folk/genres/dumy"]["word_count"] == 1500
            assert progress["articles"]["folk/genres/dumy"]["status"] == "compiled"

    def test_status_summary(self, tmp_path):
        from wiki.state import get_status_summary, mark_compiled
        with patch("wiki.state.WIKI_STATE_DIR", tmp_path / ".state"), \
             patch("wiki.state.WIKI_DIR", tmp_path):
            mark_compiled("folk/a", word_count=100)
            mark_compiled("folk/b", word_count=200)
            mark_compiled("periods/c", word_count=300)

            summary = get_status_summary()
            assert summary["total_compiled"] == 3
            assert summary["total_words"] == 600
            assert summary["by_domain"]["folk"] == 2
            assert summary["by_domain"]["periods"] == 1


# ── Tests: compile.py (topic generation, domain mapping) ─────────


class TestSlugToTopic:
    def test_uses_discovery_keywords(self):
        from wiki.compile import _slug_to_topic
        sources_info = {
            "discovery": {
                "query_keywords": [
                    "Думи лицарські: Оспівування звитяги",
                    "English fallback",
                ],
            },
        }
        topic = _slug_to_topic("dumy-lytsarski", "folk", sources_info)
        assert "Думи лицарські" in topic
        assert "Український фольклор" in topic

    def test_falls_back_to_slug(self):
        from wiki.compile import _slug_to_topic
        topic = _slug_to_topic("dumy-lytsarski", "folk")
        assert "Dumy Lytsarski" in topic
        assert "Український фольклор" in topic

    def test_falls_back_when_keywords_english_only(self):
        from wiki.compile import _slug_to_topic
        sources_info = {
            "discovery": {
                "query_keywords": ["English only topic", "Another English one"],
            },
        }
        topic = _slug_to_topic("some-topic", "hist", sources_info)
        assert "Some Topic" in topic  # Fell back to slug


class TestDomainMapping:
    def test_folk_domain_map(self):
        from wiki.compile import _get_domain
        assert _get_domain("folk", "dumy-lytsarski") == "folk/genres"
        assert _get_domain("folk", "koliadky-shchedrivky") == "folk/ritual"
        assert _get_domain("folk", "kobzarstvo-fenomen") == "folk/tradition"
        assert _get_domain("folk", "prykazky-ta-pryslivia") == "folk/short-forms"
        assert _get_domain("folk", "narodni-balady") == "folk/prose"
        assert _get_domain("folk", "chumatski-burlatski-pisni") == "folk/lyric"

    def test_other_tracks(self):
        from wiki.compile import _get_domain
        assert _get_domain("hist", "some-event") == "periods"
        assert _get_domain("bio", "shevchenko") == "figures"
        assert _get_domain("oes", "phonology") == "linguistics/oes"
        assert _get_domain("ruth", "statutes") == "linguistics/ruthenian"
        assert _get_domain("lit", "some-work") == "literature/works"
        assert _get_domain("istorio", "debate") == "historiography"
