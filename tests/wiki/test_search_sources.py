from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import sources_db


class FakeTokenizer:
    def encode(self, text: str, **_kwargs) -> list[int]:
        return list(range(len(text.split())))


def _make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            author_uk TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            parent_section_id INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(
            title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
        )
        """
    )
    conn.execute(
        """
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END
        """
    )
    conn.execute(
        """
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
        )
        """
    )
    return conn


def _seed_conn(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO textbook_sections (
            section_id, source_file, grade, section_title, section_number,
            page_start, page_end, chunk_count, full_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                101,
                "grade1-book",
                1,
                "Апостроф і наголос",
                "§ 1",
                1,
                2,
                2,
                "Апостроф і наголос. Чергування у-в і м'які приголосні.",
            ),
            (
                202,
                "grade5-book",
                5,
                "Гортань",
                "§ 2",
                3,
                4,
                2,
                "Гортань, голосові зв'язки та оглушення.",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO textbooks (
            id, chunk_id, title, text, source_file, grade, author, char_count, parent_section_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "grade1-book_s0001", "Сторінка 1", "Апостроф і наголос у слові.", "grade1-book", "1", "tester", 40, 101),
            (2, "grade1-book_s0002", "Сторінка 2", "Чергування у-в і м'які приголосні.", "grade1-book", "1", "tester", 38, 101),
            (3, "grade5-book_s0001", "Сторінка 5", "Гортань і голосові зв'язки.", "grade5-book", "5", "tester", 34, 202),
            (4, "grade5-book_s0002", "Сторінка 6", "Оглушення в кінці слова.", "grade5-book", "5", "tester", 28, 202),
        ],
    )


def test_search_sections_fts5_groups_chunks_and_applies_fixed_weights(monkeypatch):
    conn = _make_conn()
    _seed_conn(conn)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)

    results = sources_db._search_sections_fts5(
        ['"апостроф і наголос"'],
        {"апостроф", "наголос", "чергування"},
        track="a1",
        max_chunk_candidates=10,
        max_sections=10,
    )

    assert [row["section_id"] for row in results] == [101]
    assert results[0]["bucket_a_hits"] == 1
    assert results[0]["bucket_b_hits"] == 2
    assert results[0]["section_score"] == 5
    assert results[0]["chunk_id"] == "S101"
    assert results[0]["text"] == results[0]["full_text"]


def test_search_sources_ranks_unsectioned_chunks_with_sections(monkeypatch):
    conn = _make_conn()
    _seed_conn(conn)
    conn.executemany(
        """
        INSERT INTO textbooks (
            id, chunk_id, title, text, source_file, grade, author, char_count, parent_section_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (5, "section-hit", "uniquealpha", "section candidate", "grade1-book", "1", "tester", 24, 101),
            (6, "ulp-unsectioned-hit", "uniquebeta", "unsectioned candidate", "ulp-test", "", "tester", 29, None),
        ],
    )
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections",))
    monkeypatch.setattr(sources_db, "_get_tokenizer", lambda: FakeTokenizer())
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, candidates, limit=10, **_kwargs: [
            {**candidate, "dense_score": 0.0, "ranking": "keyword_rrf"}
            for candidate in candidates[:limit]
        ],
    )

    results = sources_db.search_sources("uniquealpha uniquebeta", track="a1", limit=5)

    by_chunk = {row["chunk_id"]: row for row in results}
    assert "ulp-unsectioned-hit" in by_chunk
    assert by_chunk["ulp-unsectioned-hit"]["parent_section_id"] is None
    assert by_chunk["ulp-unsectioned-hit"]["text"] == "unsectioned candidate"
    assert by_chunk["ulp-unsectioned-hit"]["unit_key"] == "textbook_sections:ulp-unsectioned-hit"
    assert by_chunk["S101"]["section_id"] == 101
    assert {row["keyword_rank"] for row in results} == {1, 2}


def test_search_sources_uses_query_builder_and_dense_rerank(monkeypatch, tmp_path):
    conn = _make_conn()
    _seed_conn(conn)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections",))
    monkeypatch.setattr(sources_db, "_get_tokenizer", lambda: FakeTokenizer())
    monkeypatch.setattr(
        sources_db,
        "build_query_buckets",
        lambda query, track: (['"апостроф і наголос"'], {"апостроф", "наголос"}),
    )
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, sections, corpus, limit=10, **kwargs: sorted(
            sections,
            key=lambda row: -row["section_score"],
        )[:limit],
    )

    discovery_path = tmp_path / "demo.yaml"
    discovery_path.write_text("query_keywords: []\n", encoding="utf-8")

    results = sources_db.search_sources(discovery_path, track="a1", limit=5)

    assert len(results) == 1
    assert results[0]["grade"] == 1
    assert results[0]["section_title"] == "Апостроф і наголос"


def test_search_sources_uses_track_weighted_rrf_without_dense_index(monkeypatch):
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections", "modern_literary"))
    monkeypatch.setattr(
        sources_db,
        "_prepare_query",
        lambda query, track: ([], {"відмінок"}, "відмінок"),
    )
    textbook = {
        "corpus": "textbook_sections",
        "unit_key": "textbook_sections:1",
        "section_id": 1,
        "text": "Textbook section",
        "full_text": "Textbook section",
        "fts_score": -1.0,
    }
    literary = {
        "corpus": "modern_literary",
        "unit_key": "modern_literary:1",
        "chunk_id": "literary-1",
        "text": "Literary passage",
        "full_text": "Literary passage",
        "fts_score": -100.0,
    }
    monkeypatch.setattr(sources_db, "_search_sections_fts5", lambda *args, **kwargs: [textbook])
    monkeypatch.setattr(sources_db, "_expand_to_chunk_candidates", lambda rows, **kwargs: rows)
    monkeypatch.setattr(sources_db, "_search_literary_candidates", lambda *args, **kwargs: [literary])
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, candidates, **kwargs: [
            {**candidate, "dense_score": 0.0, "ranking": "keyword_rrf"}
            for candidate in candidates
        ],
    )
    monkeypatch.setattr(sources_db, "_expand_neighbor_context", lambda hit: hit)

    results = sources_db.search_sources("відмінок", track="a1", limit=2)

    assert [hit["corpus"] for hit in results] == ["textbook_sections", "modern_literary"]
    assert all(hit["ranking"] == "keyword_rrf" for hit in results)
    for hit in results:
        assert hit["keyword_rank"] == 1
        assert hit["keyword_score"] == pytest.approx(1 / (sources_db.RRF_K + 1))
        assert hit["final_score"] == pytest.approx(
            hit["keyword_score"] * sources_db._corpus_prior("a1", hit["corpus"])
        )
    assert results[0]["fts_score"] > results[1]["fts_score"]

    monkeypatch.setattr(sources_db, "_corpus_prior", lambda track, corpus: 1.0)
    # The corpus enumeration puts textbook first, so this proves the documented
    # corpus tie-break wins over stable input order.
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections", "modern_literary"))
    tied_results = sources_db.search_sources("відмінок", track="a1", limit=2)
    assert [(hit["corpus"], hit["unit_key"]) for hit in tied_results] == [
        ("modern_literary", "modern_literary:1"),
        ("textbook_sections", "textbook_sections:1"),
    ]


def test_search_sources_archaic_strategy_is_reserved(tmp_path):
    discovery_path = tmp_path / "demo.yaml"
    discovery_path.write_text("query_keywords: []\n", encoding="utf-8")

    result = {
        "corpus": "archaic_literary",
        "chunk_id": "lit-1",
        "full_text": "Архаїчний уривок.",
        "text": "Архаїчний уривок.",
    }
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(sources_db, "_search_archaic_metadata", lambda *args, **kwargs: [result])
        results = sources_db.search_sources(discovery_path, track="ruth", strategy="archaic_metadata")

    assert results == [result]


@pytest.mark.parametrize("env", [{"SOURCES_MCP_NO_DENSE": "1"}, {}])
def test_search_sources_keyword_path_needs_no_model_assets(monkeypatch, tmp_path, env):
    from wiki import dense_rerank

    conn = _make_conn()
    _seed_conn(conn)
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(sources_db, "_CORPORA", ("textbook_sections",))
    monkeypatch.delenv(dense_rerank.NO_DENSE_ENV, raising=False)
    monkeypatch.delenv(dense_rerank.CPU_DENSE_ENV, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    # No env → the CPU-host default, where dense rerank is opt-in.
    monkeypatch.setattr(dense_rerank, "_accelerator_available", lambda: False)
    monkeypatch.setattr(
        dense_rerank,
        "load_corpus_index",
        lambda corpus, **_kwargs: dense_rerank.CorpusEmbeddingIndex(
            corpus=corpus,
            shards={0: np.zeros((1, dense_rerank.EMBEDDING_DIMS), dtype=np.float16)},
            unit_rows={"textbook_sections:101": (0, 0)},
        ),
    )

    def missing_assets(*_args, **_kwargs):
        raise OSError("Can't load tokenizer for 'BAAI/bge-m3'")

    monkeypatch.setattr(sources_db, "_get_tokenizer", missing_assets)
    monkeypatch.setattr(dense_rerank, "_get_tokenizer", missing_assets)
    monkeypatch.setattr(dense_rerank, "_get_encoder", missing_assets)
    monkeypatch.setattr(
        sources_db,
        "build_query_buckets",
        lambda query, track: (['"апостроф і наголос"'], {"апостроф", "наголос"}),
    )
    discovery_path = tmp_path / "demo.yaml"
    discovery_path.write_text("query_keywords: []\n", encoding="utf-8")

    results = sources_db.search_sources(discovery_path, track="a1", limit=5)

    assert [row["unit_key"] for row in results] == ["textbook_sections:101"]
    assert results[0]["section_title"] == "Апостроф і наголос"
    assert results[0]["dense_score"] == 0.0


_NO_INDEX_SEARCH = """
import functools, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from wiki import dense_rerank, sources_db

db_path, manifest_db = Path(sys.argv[2]), Path(sys.argv[3])
conn = sources_db._open_conn(db_path, read_only=True)
sources_db._get_conn = lambda: conn
sources_db._CORPORA = ("textbook_sections",)
sources_db.dense_rerank_enabled = functools.partial(dense_rerank.dense_rerank_enabled, manifest_db=manifest_db)
sources_db.rerank_candidates = functools.partial(dense_rerank.rerank_candidates, manifest_db=manifest_db)
results = sources_db.search_sources("апостроф і наголос", track="a1", limit=5)
assert results and results[0]["unit_key"] == "textbook_sections:101", results
loaded = sorted(name for name in ("torch", "transformers") if name in sys.modules)
assert not loaded, f"keyword-only search imported {loaded}"
"""


@pytest.mark.parametrize("no_dense", [True, False], ids=["no-dense-switch", "cpu-default"])
def test_no_index_search_never_imports_torch_or_transformers(tmp_path, no_dense):
    from wiki import dense_rerank

    db_path = tmp_path / "sources.db"
    seeded = _make_conn()
    _seed_conn(seeded)
    seeded.commit()
    with sqlite3.connect(db_path) as target:
        seeded.backup(target)
    env = {
        name: value
        for name, value in os.environ.items()
        if name not in {dense_rerank.NO_DENSE_ENV, dense_rerank.CPU_DENSE_ENV}
    }
    if no_dense:
        env[dense_rerank.NO_DENSE_ENV] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _NO_INDEX_SEARCH,
            str(Path(sources_db.__file__).resolve().parents[1]),
            str(db_path),
            str(tmp_path / "embeddings" / "manifest.db"),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_candidate_pieces_keep_whole_unit_without_tokenizer():
    pieces = sources_db._candidate_pieces("Ціла стаття.", corpus="wikipedia", tokenizer=None)

    assert [(piece.chunk_index, piece.text, piece.extra_metadata) for piece in pieces] == [(0, "Ціла стаття.", {})]
    assert sources_db._candidate_pieces("", corpus="wikipedia", tokenizer=None) == []
