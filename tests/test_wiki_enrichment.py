"""Tests for wiki enrichment — _load_local_data, keyword source matching."""

import json
import os
import sys
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.reads_content

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
        data_dir = tmp_path / "registry"
        data_dir.mkdir()
        with open(data_dir / "folk_micro_genres.yaml", "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

        with patch("wiki.enrichment.PROJECT_ROOT", tmp_path):
            chunks = _load_local_data("folk", "zahadky")
        assert len(chunks) == 1
        assert "камінь" in chunks[0]["text"]


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


# ── Tests: dossier-seeded dense retrieval (no discovery file) ──────


class TestDossierSeededRetrieval:

    def test_enrich_seeds_dense_from_dossier_when_no_discovery(self, tmp_path):
        from wiki.enrichment import enrich_sources

        # No discovery file under CURRICULUM_DIR → dossier-only retrieval path.
        curriculum = tmp_path / "curriculum"
        (curriculum / "folk" / "discovery").mkdir(parents=True)
        dossier = tmp_path / "docs" / "research" / "folk" / "demo.md"
        dossier.parent.mkdir(parents=True)
        dossier.write_text("# Демо тема\n\nbody\n", encoding="utf-8")

        captured = {}

        def fake_search(query, *, track, strategy, limit):
            captured["query"] = query
            return [{"chunk_id": "real1", "text": "corpus chunk"}]

        with (
            patch("wiki.enrichment.CURRICULUM_DIR", curriculum),
            patch("wiki.enrichment.PROJECT_ROOT", tmp_path),
            patch("wiki.sources_db.search_sources", side_effect=fake_search),
            patch("wiki.enrichment._load_local_data", return_value=[]),
            patch("wiki.enrichment._load_external_resources", return_value=[]),
        ):
            chunks = enrich_sources("folk", "demo", {})

        # Dense retrieval ran, seeded by the dossier title + slug (not skipped).
        assert captured.get("query") == "Демо тема demo"
        assert any(c.get("chunk_id") == "real1" for c in chunks)

    def test_enrich_no_dense_when_no_discovery_and_no_dossier(self, tmp_path):
        from wiki.enrichment import enrich_sources

        curriculum = tmp_path / "curriculum"
        (curriculum / "folk" / "discovery").mkdir(parents=True)

        def fail_search(*args, **kwargs):  # pragma: no cover - must not be called
            raise AssertionError("search_sources must not run without a seed")

        with (
            patch("wiki.enrichment.CURRICULUM_DIR", curriculum),
            patch("wiki.enrichment.PROJECT_ROOT", tmp_path),
            patch("wiki.sources_db.search_sources", side_effect=fail_search),
            patch("wiki.enrichment._load_local_data", return_value=[]),
            patch("wiki.enrichment._load_external_resources", return_value=[]),
        ):
            chunks = enrich_sources("folk", "noseed", {})

        # Falls back to the single topic stub, no dense call.
        assert len(chunks) == 1
        assert chunks[0]["chunk_id"] == "no-source"
