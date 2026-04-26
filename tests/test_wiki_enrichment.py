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


class TestExternalResourceLoading:
    def test_skips_reference_only_articles_and_videos(self):
        from wiki.enrichment import _load_external_resources

        resources = {
            "a1-demo": {
                "articles": [
                    {
                        "title": "Cached article",
                        "source": "ULP",
                        "url": "https://example.test/cached",
                        "relevance": "high",
                    },
                    {
                        "title": "Reference only",
                        "source": "Blog",
                        "url": "https://example.test/ref-only",
                        "relevance": "high",
                    },
                ],
                "youtube": [
                    {
                        "title": "Bare video ref",
                        "url": "https://youtube.test/watch?v=1",
                        "relevance": "high",
                    },
                ],
            },
        }

        def _lookup(url: str) -> dict | None:
            if url.endswith("/cached"):
                return {
                    "title": "Cached article",
                    "domain": "ULP",
                    "text": "Useful cached pedagogical content.",
                }
            return None

        with patch("wiki.enrichment._get_external_resources", return_value=resources), \
             patch("wiki.sources_db.lookup_by_url", side_effect=_lookup):
            chunks = _load_external_resources("a1", "demo")

        assert len(chunks) == 1
        assert chunks[0]["source_type"] == "external_article"
        assert chunks[0]["text"] == "Useful cached pedagogical content."


class TestSourceBudgeting:
    def test_dedupes_by_chunk_id(self):
        from wiki.enrichment import _dedupe_chunks

        chunks = [
            {"chunk_id": "dup-1", "text": "First copy"},
            {"chunk_id": "dup-1", "text": "Second copy"},
            {"chunk_id": "unique", "text": "Unique"},
        ]

        deduped = _dedupe_chunks(chunks)
        assert len(deduped) == 2
        assert deduped[0]["text"] == "First copy"

    def test_limits_background_sources_before_primary(self):
        from wiki.enrichment import _cap_source_chunks

        background_chunks = [
            {
                "chunk_id": f"wiki-{i}",
                "source_type": "wikipedia",
                "_kw_score": 90 - i,
                "text": "W" * 4000,
            }
            for i in range(5)
        ]
        textbook_chunks = [
            {
                "chunk_id": f"tb-{i}",
                "source_type": "textbook",
                "_kw_score": 100 - i,
                "text": "T" * 5000,
            }
            for i in range(4)
        ]

        kept, char_cap, total_chars = _cap_source_chunks("a1", background_chunks + textbook_chunks)

        assert char_cap == 60_000
        assert total_chars <= char_cap
        assert sum(1 for c in kept if c.get("source_type") == "wikipedia") <= 3
        assert sum(1 for c in kept if c.get("source_type") == "textbook") == 4


# ── Tests: keyword source matching in enrich_sources ─────────────
#
# The `TRACK_LITERARY_MAP` / `KEYWORD_SOURCE_MAP` / `_load_relevant_chunks`
# static-mapping architecture was retired. Seminar-track keyword enrichment
# now runs through `sources_db.search_literary()` (FTS5 index over the
# literary JSONL corpus) rather than hand-maintained constants.
#
# The two tests that used to live here (test_kobzar_keyword_triggers_shevchenko,
# test_no_keyword_match_no_extra) patched constants that no longer exist and
# therefore failed at `patch()` binding, not at assertion. Since covering the
# FTS5 path requires a live SQLite fixture, the tests were deleted rather
# than rewritten — a proper integration-style test belongs in a fixture-
# heavy suite, not these unit tests. Tracking in the backlog.


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
