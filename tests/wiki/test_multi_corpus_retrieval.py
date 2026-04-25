from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.embedding_manifest import (
    LEGACY_SHIPPED_CONFIG,
    EmbeddingManifest,
    UnitSpecInput,
    append_shard,
)

from wiki import dense_rerank, sources_db


class FakeTokenizer:
    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        truncation: bool = True,
        max_length: int | None = None,
    ) -> list[int]:
        tokens = list(range(1, len(text.split()) + 1))
        if max_length is not None:
            limit = max_length - (2 if add_special_tokens else 0)
            tokens = tokens[:limit]
        if add_special_tokens:
            return [0, *tokens, 1]
        return tokens

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        ids = [token for token in token_ids if not skip_special_tokens or token not in {0, 1}]
        return " ".join(f"tok{token}" for token in ids)


def _vec(cosine: float) -> np.ndarray:
    vector = np.zeros(dense_rerank.EMBEDDING_DIMS, dtype=np.float32)
    vector[0] = cosine
    vector[1] = math.sqrt(max(0.0, 1.0 - (cosine * cosine)))
    return vector.astype(np.float16)


def _conn(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            parent_section_id INTEGER
        );
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(
            title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;

        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            section_number TEXT,
            page_start INTEGER,
            page_end INTEGER,
            chunk_count INTEGER NOT NULL,
            full_text TEXT NOT NULL
        );

        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            author TEXT DEFAULT '',
            work TEXT DEFAULT '',
            work_id TEXT DEFAULT '',
            year INTEGER,
            genre TEXT DEFAULT '',
            language_period TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        CREATE VIRTUAL TABLE literary_fts USING fts5(
            title, text, content='literary_texts', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER literary_ai AFTER INSERT ON literary_texts BEGIN
            INSERT INTO literary_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;

        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            url TEXT NOT NULL,
            url_normalized TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            source_file TEXT NOT NULL,
            domain TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            channel_id TEXT DEFAULT '',
            speaker TEXT DEFAULT '',
            register_tag TEXT DEFAULT '',
            decolonization_tag TEXT DEFAULT '',
            quality_tier INTEGER DEFAULT 2,
            publish_date TEXT DEFAULT '',
            duration_s INTEGER DEFAULT 0,
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER,
            video_id TEXT DEFAULT ''
        );
        CREATE VIRTUAL TABLE external_fts USING fts5(
            title, text, speaker, content='external_articles', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER external_ai AFTER INSERT ON external_articles BEGIN
            INSERT INTO external_fts(rowid, title, text, speaker)
            VALUES (new.id, new.title, new.text, new.speaker);
        END;

        CREATE TABLE wikipedia (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            char_count INTEGER DEFAULT 0,
            fetched_at TEXT NOT NULL DEFAULT ''
        );
        CREATE VIRTUAL TABLE wikipedia_fts USING fts5(
            title, text, content='wikipedia', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER wikipedia_ai AFTER INSERT ON wikipedia BEGIN
            INSERT INTO wikipedia_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;
        """
    )
    return conn


def _seed_multi_corpus(conn: sqlite3.Connection, manifest_path: Path) -> None:
    manifest = EmbeddingManifest(manifest_path)
    try:
        textbook_vectors = np.stack([_vec(score) for score in (0.80, 0.22, 0.18, 0.12)], axis=0)
        modern_vectors = np.stack([_vec(score) for score in (0.82, 0.25, 0.19, 0.13)], axis=0)
        archaic_vectors = np.stack([_vec(score) for score in (0.88, 0.24, 0.17, 0.11)], axis=0)
        external_vectors = np.stack([_vec(score) for score in (0.70, 0.21, 0.16, 0.10)], axis=0)
        wikipedia_vectors = np.stack([_vec(score) for score in (0.75, 0.23, 0.15, 0.09)], axis=0)

        conn.executemany(
            """
            INSERT INTO textbook_sections (
                section_id, source_file, grade, section_title, section_number,
                page_start, page_end, chunk_count, full_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "tb-1", 1, "Textbook top", "§1", 1, 1, 1, "апостроф тема textbook top"),
                (2, "tb-2", 1, "Textbook 2", "§2", 2, 2, 1, "апостроф тема textbook 2"),
                (3, "tb-3", 1, "Textbook 3", "§3", 3, 3, 1, "апостроф тема textbook 3"),
                (4, "tb-4", 1, "Textbook 4", "§4", 4, 4, 1, "апостроф тема textbook 4"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO textbooks (
                id, chunk_id, title, text, source_file, grade, author, char_count, parent_section_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "tb-1-c1", "Textbook top", "апостроф тема textbook top", "tb-1", "1", "tester", 20, 1),
                (2, "tb-2-c1", "Textbook 2", "апостроф тема textbook 2", "tb-2", "1", "tester", 20, 2),
                (3, "tb-3-c1", "Textbook 3", "апостроф тема textbook 3", "tb-3", "1", "tester", 20, 3),
                (4, "tb-4-c1", "Textbook 4", "апостроф тема textbook 4", "tb-4", "1", "tester", 20, 4),
            ],
        )

        conn.executemany(
            """
            INSERT INTO literary_texts (
                id, chunk_id, title, text, source_file, author, work, work_id,
                year, genre, language_period, char_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (101, "mod-1", "Modern top", "апостроф тема modern top", "modern-a", "auth", "work a", "work_a", 2001, "poetry", "modern", 24),
                (102, "mod-2", "Modern 2", "апостроф тема modern 2", "modern-b", "auth", "work b", "work_b", 2001, "poetry", "modern", 20),
                (103, "mod-3", "Modern 3", "апостроф тема modern 3", "modern-c", "auth", "work c", "work_c", 2001, "poetry", "modern", 20),
                (104, "mod-4", "Modern 4", "апостроф тема modern 4", "modern-d", "auth", "work d", "work_d", 2001, "poetry", "modern", 20),
                (201, "arc-1", "Archaic top", "апостроф тема archaic top", "archaic-a", "auth", "work e", "work_e", 1700, "chronicle", "middle_ukrainian", 24),
                (202, "arc-2", "Archaic 2", "апостроф тема archaic 2", "archaic-b", "auth", "work f", "work_f", 1700, "chronicle", "old_east_slavic", 20),
                (203, "arc-3", "Archaic 3", "апостроф тема archaic 3", "archaic-c", "auth", "work g", "work_g", 1700, "chronicle", "middle_ukrainian", 20),
                (204, "arc-4", "Archaic 4", "апостроф тема archaic 4", "archaic-d", "auth", "work h", "work_h", 1700, "chronicle", "old_east_slavic", 20),
            ],
        )

        conn.executemany(
            """
            INSERT INTO external_articles (
                id, chunk_id, url, title, text, source_file, domain, char_count, speaker
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (301, "ext-1", "https://e/1", "External top", "апостроф тема external top", "ext-a", "example.com", 24, "speaker"),
                (302, "ext-2", "https://e/2", "External 2", "апостроф тема external 2", "ext-b", "example.com", 20, "speaker"),
                (303, "ext-3", "https://e/3", "External 3", "апостроф тема external 3", "ext-c", "example.com", 20, "speaker"),
                (304, "ext-4", "https://e/4", "External 4", "апостроф тема external 4", "ext-d", "example.com", 20, "speaker"),
            ],
        )

        conn.executemany(
            """
            INSERT INTO wikipedia (id, title, url, text, char_count, fetched_at)
            VALUES (?, ?, ?, ?, ?, '2026-04-20T00:00:00Z')
            """,
            [
                (401, "WikiTop", "https://wiki/1", "апостроф тема wiki top", 22),
                (402, "WikiTwo", "https://wiki/2", "апостроф тема wiki 2", 20),
                (403, "WikiThree", "https://wiki/3", "апостроф тема wiki 3", 20),
                (404, "WikiFour", "https://wiki/4", "апостроф тема wiki 4", 20),
            ],
        )
        conn.commit()

        append_shard(
            manifest,
            corpus="textbook_sections",
            vectors=textbook_vectors,
            unit_specs=[
                UnitSpecInput(f"textbook_sections:{idx}", f"tb-{idx}", f"sha-tb-{idx}")
                for idx in range(1, 5)
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
        append_shard(
            manifest,
            corpus="modern_literary",
            vectors=modern_vectors,
            unit_specs=[
                UnitSpecInput(f"modern_literary:mod-{idx}", f"work_{chr(96 + idx)}", f"sha-mod-{idx}")
                for idx in range(1, 5)
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
        append_shard(
            manifest,
            corpus="archaic_literary",
            vectors=archaic_vectors,
            unit_specs=[
                UnitSpecInput(f"archaic_literary:arc-{idx}", f"work_{chr(100 + idx)}", f"sha-arc-{idx}")
                for idx in range(1, 5)
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
        append_shard(
            manifest,
            corpus="external",
            vectors=external_vectors,
            unit_specs=[
                UnitSpecInput(f"external:ext-{idx}", f"ext-{idx}", f"sha-ext-{idx}")
                for idx in range(1, 5)
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
        append_shard(
            manifest,
            corpus="wikipedia",
            vectors=wikipedia_vectors,
            unit_specs=[
                UnitSpecInput(f"wikipedia:{title}:chunk_0", title, f"sha-{title}")
                for title in ("WikiTop", "WikiTwo", "WikiThree", "WikiFour")
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
    finally:
        manifest.close()


def _configure_dense(monkeypatch: pytest.MonkeyPatch, manifest_path: Path) -> None:
    fake_tokenizer = FakeTokenizer()
    monkeypatch.setattr(dense_rerank, "_TOKENIZER", fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_get_tokenizer", lambda: fake_tokenizer)
    monkeypatch.setattr(
        dense_rerank,
        "encode_query",
        lambda query, encoder=None, max_length=dense_rerank.QUERY_MAX_LENGTH: np.array([1.0, 0.0, *([0.0] * (dense_rerank.EMBEDDING_DIMS - 2))], dtype=np.float32),
    )
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, candidates, *, corpus, limit=10: dense_rerank.rerank_candidates(
            query,
            candidates,
            corpus=corpus,
            limit=limit,
            manifest_db=manifest_path,
        ),
    )


def test_search_sources_merges_corpora_with_track_priors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _conn(tmp_path)
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    _seed_multi_corpus(conn, manifest_path)
    _configure_dense(monkeypatch, manifest_path)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)

    a1_results = sources_db.search_sources("апостроф тема", track="a1", limit=5)
    c2_results = sources_db.search_sources("апостроф тема", track="c2", limit=5)
    lit_results = sources_db.search_sources("апостроф тема", track="lit", limit=5)

    assert a1_results[0]["corpus"] == "textbook_sections"
    assert c2_results[0]["corpus"] == "modern_literary"
    assert lit_results[0]["corpus"] == "archaic_literary"
    assert a1_results[0]["final_score"] > a1_results[1]["final_score"]

    conn.close()


def test_neighbor_expansion_groups_adjacent_literary_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _conn(tmp_path)
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    manifest = EmbeddingManifest(manifest_path)
    try:
        conn.executemany(
            """
            INSERT INTO literary_texts (
                id, chunk_id, title, text, source_file, author, work, work_id,
                year, genre, language_period, char_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "n-1", "Before", "before chunk marker", "src", "a", "w", "neighbor_work", 2000, "genre", "modern", 20),
                (2, "n-2", "Middle", "middle chunk marker", "src", "a", "w", "neighbor_work", 2000, "genre", "modern", 20),
                (3, "n-3", "After", "after chunk marker", "src", "a", "w", "neighbor_work", 2000, "genre", "modern", 20),
            ],
        )
        conn.commit()
        append_shard(
            manifest,
            corpus="modern_literary",
            vectors=np.stack([_vec(0.2), _vec(0.95), _vec(0.25)], axis=0),
            unit_specs=[
                UnitSpecInput("modern_literary:n-1", "neighbor_work", "sha-1"),
                UnitSpecInput("modern_literary:n-2", "neighbor_work", "sha-2"),
                UnitSpecInput("modern_literary:n-3", "neighbor_work", "sha-3"),
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
    finally:
        manifest.close()

    _configure_dense(monkeypatch, manifest_path)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)

    results = sources_db.search_sources("chunk marker", track="lit", limit=3)

    assert results[0]["corpus"] == "modern_literary"
    assert "before chunk marker" in results[0]["full_text"]
    assert "middle chunk marker" in results[0]["full_text"]
    assert "after chunk marker" in results[0]["full_text"]
    assert len(results[0]["context_unit_keys"]) == 3

    conn.close()


def test_search_sources_respects_track_char_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _conn(tmp_path)
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    manifest = EmbeddingManifest(manifest_path)
    large_text = "апостроф " * 120
    try:
        conn.executemany(
            """
            INSERT INTO textbook_sections (
                section_id, source_file, grade, section_title, section_number,
                page_start, page_end, chunk_count, full_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "tb-a", 1, "A", "§1", 1, 1, 1, large_text),
                (2, "tb-b", 1, "B", "§2", 2, 2, 1, large_text),
            ],
        )
        conn.executemany(
            """
            INSERT INTO textbooks (
                id, chunk_id, title, text, source_file, grade, author, char_count, parent_section_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, "a", "A", large_text, "tb-a", "1", "t", len(large_text), 1),
                (2, "b", "B", large_text, "tb-b", "1", "t", len(large_text), 2),
            ],
        )
        conn.commit()
        append_shard(
            manifest,
            corpus="textbook_sections",
            vectors=np.stack([_vec(0.9), _vec(0.8)], axis=0),
            unit_specs=[
                UnitSpecInput("textbook_sections:1", "tb-a", "sha-a"),
                UnitSpecInput("textbook_sections:2", "tb-b", "sha-b"),
            ],
            encoder_config=LEGACY_SHIPPED_CONFIG,
        )
    finally:
        manifest.close()

    from wiki import enrichment

    _configure_dense(monkeypatch, manifest_path)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setitem(enrichment.SOURCE_CHAR_CAPS, "test_track", 1000)

    results = sources_db.search_sources("апостроф", track="test_track", limit=5)

    assert sum(len(result["full_text"]) for result in results) <= 1000
    conn.close()


def test_archaic_metadata_strategy_filters_to_archaic_periods(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    conn = _conn(tmp_path)
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    conn.executemany(
        """
        INSERT INTO literary_texts (
            id, chunk_id, title, text, source_file, author, work, work_id,
            year, genre, language_period, char_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "m-1", "Modern", "апостроф modern", "src-m", "a", "w", "modern_work", 2000, "genre", "modern", 20),
            (2, "a-1", "Archaic", "апостроф archaic", "src-a", "a", "w", "archaic_work", 1700, "genre", "middle_ukrainian", 20),
            (3, "a-2", "Archaic 2", "апостроф archaic 2", "src-b", "a", "w", "archaic_work_2", 1600, "genre", "old_east_slavic", 20),
        ],
    )
    conn.commit()
    _configure_dense(monkeypatch, manifest_path)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)

    results = sources_db.search_sources(
        "апостроф",
        track="ruth",
        strategy="archaic_metadata",
        limit=5,
    )

    assert {result["language_period"] for result in results} == {
        "middle_ukrainian",
        "old_east_slavic",
    }
    conn.close()
