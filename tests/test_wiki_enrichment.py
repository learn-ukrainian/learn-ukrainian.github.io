"""Tests for wiki enrichment — _load_local_data, keyword source matching."""

import json
import os
import sys
from unittest.mock import patch

import yaml

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


# ── Tests: _load_local_data ──────────────────────────────────────


class TestLoadLocalData:
    def test_folk_track_delegates_to_micro_genres(self, tmp_path):
        from wiki.enrichment import _load_local_data

        # Create micro genres file
        data = {
            "загадки": [
                {"text": "Що росте без коріння?", "answer": "камінь"},
            ],
        }
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        with open(data_dir / "folk_micro_genres.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

        with patch("wiki.enrichment.PROJECT_ROOT", tmp_path):
            chunks = _load_local_data("folk", "zahadky")
        assert len(chunks) == 1
        assert "камінь" in chunks[0]["text"]

    def test_non_folk_track_returns_empty(self, tmp_path):
        from wiki.enrichment import _load_local_data

        with patch("wiki.enrichment.PROJECT_ROOT", tmp_path):
            chunks = _load_local_data("hist", "some-event")
        assert chunks == []


# ── Tests: keyword source matching in enrich_sources ─────────────


class TestKeywordSourceMatching:
    def test_kobzar_keyword_triggers_shevchenko(self, tmp_path):
        from wiki.enrichment import enrich_sources

        # Create the expected literary file with text that matches slug words
        # so _load_relevant_chunks scores > 0
        lit_dir = tmp_path / "literary"
        lit_dir.mkdir()
        chunks = [{"chunk_id": "shev1", "text": "Кобзарство як феномен козацької доби."}]
        with open(lit_dir / "ukrlib-shevchenko.jsonl", "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")

        sources_info = {
            "discovery": {"query_keywords": ["Кобзарство як феномен"]},
            "literary_chunks": [],
            "textbook_chunks": [],
            "literary_files": [],
        }

        with patch("wiki.enrichment.LITERARY_DIR", lit_dir), \
             patch("wiki.enrichment.TRACK_LITERARY_MAP", {}), \
             patch("wiki.enrichment.PROJECT_ROOT", tmp_path):
            result = enrich_sources("folk", "kobzarstvo-fenomen", sources_info)

        # Should find the shevchenko file via KEYWORD_SOURCE_MAP
        ids = {c.get("chunk_id") for c in result}
        assert "shev1" in ids

    def test_no_keyword_match_no_extra(self):
        from wiki.enrichment import enrich_sources

        sources_info = {
            "discovery": {"query_keywords": []},
            "literary_chunks": [{"text": "base chunk", "chunk_id": "base1"}],
            "textbook_chunks": [],
            "literary_files": [],
        }

        with patch("wiki.enrichment.TRACK_LITERARY_MAP", {}), \
             patch("wiki.enrichment.KEYWORD_SOURCE_MAP", {}):
            result = enrich_sources("folk", "generic-slug", sources_info)
        assert len(result) == 1
        assert result[0]["chunk_id"] == "base1"


# ── Tests: sources.py gaps ───────────────────────────────────────


class TestFindLiteraryByChunkIds:
    def test_finds_chunks_across_files(self, tmp_path):
        from wiki.sources import find_literary_by_chunk_ids

        # Create two JSONL files
        chunks_a = [
            {"chunk_id": "abc_c0000", "text": "First"},
            {"chunk_id": "abc_c0001", "text": "Second"},
        ]
        chunks_b = [
            {"chunk_id": "def_c0000", "text": "Third"},
        ]
        (tmp_path / "file_a.jsonl").write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in chunks_a) + "\n"
        )
        (tmp_path / "file_b.jsonl").write_text(
            json.dumps(chunks_b[0], ensure_ascii=False) + "\n"
        )

        with patch("wiki.sources.LITERARY_DIR", tmp_path):
            result = find_literary_by_chunk_ids(["abc_c0001", "def_c0000"])

        # Should map files to matching chunk IDs
        all_matched = []
        for _path, ids in result.items():
            all_matched.extend(ids)
        assert set(all_matched) == {"abc_c0001", "def_c0000"}

    def test_returns_empty_for_no_ids(self, tmp_path):
        from wiki.sources import find_literary_by_chunk_ids

        with patch("wiki.sources.LITERARY_DIR", tmp_path):
            assert find_literary_by_chunk_ids([]) == {}

    def test_returns_empty_when_no_match(self, tmp_path):
        from wiki.sources import find_literary_by_chunk_ids

        (tmp_path / "file.jsonl").write_text(
            '{"chunk_id": "xxx_c0000", "text": "content"}\n'
        )

        with patch("wiki.sources.LITERARY_DIR", tmp_path):
            result = find_literary_by_chunk_ids(["yyy_c0000"])
        assert result == {}


class TestGetTrackSourceSummary:
    def test_summarizes_track(self, tmp_path):
        from wiki.sources import get_track_source_summary

        # Create discovery files
        disc_dir = tmp_path / "curriculum" / "l2-uk-en" / "folk" / "discovery"
        disc_dir.mkdir(parents=True)

        disc1 = {
            "query_keywords": ["test"],
            "rag_literary": [{"chunk_id": "lit1", "text": "sample"}],
            "rag_chunks": [{"chunk_id": "tb1"}, {"chunk_id": "tb2"}],
            "rag_images": [],
        }
        disc2 = {
            "query_keywords": ["test2"],
            "rag_literary": [],
            "rag_chunks": [{"chunk_id": "tb3"}],
            "rag_images": [{"image_id": "img1"}],
        }

        with open(disc_dir / "slug-a.yaml", "w") as f:
            yaml.dump(disc1, f)
        with open(disc_dir / "slug-b.yaml", "w") as f:
            yaml.dump(disc2, f)

        with patch("wiki.sources.CURRICULUM_DIR", tmp_path / "curriculum" / "l2-uk-en"):
            summary = get_track_source_summary("folk")

        assert summary["track"] == "folk"
        assert summary["module_count"] == 2
        assert summary["slugs"] == ["slug-a", "slug-b"]
        assert summary["total_literary_refs"] == 1
        assert summary["total_textbook_refs"] == 3

    def test_empty_track(self, tmp_path):
        from wiki.sources import get_track_source_summary

        with patch("wiki.sources.CURRICULUM_DIR", tmp_path / "nonexistent"):
            summary = get_track_source_summary("empty")
        assert summary["module_count"] == 0
        assert summary["slugs"] == []
