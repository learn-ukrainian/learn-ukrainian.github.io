import json
import sqlite3
import sys

import pytest

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.enrich_manifest import (
    _idioms_frazeolohichnyi,
    _synonyms_from_ukrajinet,
)


def test_ukrajinet_exact_hit_and_parity_and_idempotency(tmp_path, monkeypatch):
    # Mock candidate_allowed to always return True for this test to focus on lookup/matching
    monkeypatch.setattr(
        enrich_manifest_module,
        "_candidate_allowed",
        lambda lemma, candidate: True
    )

    db_path = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE ukrajinet (
            id INTEGER PRIMARY KEY,
            words TEXT NOT NULL DEFAULT ''
        )
    """)

    conn.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати", "швидко"], ensure_ascii=False),))
    conn.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["йти", "пішки"], ensure_ascii=False),))
    conn.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати"], ensure_ascii=False),))
    conn.commit()

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = None

    # Test exact-hit short circuit / index population
    out_idx = []
    seen_idx = set()
    _synonyms_from_ukrajinet(conn, "бігати", out_idx, seen_idx)
    assert "швидко" in out_idx
    assert "йти" not in out_idx

    # Check that the index was lazily created and populated
    cursor = conn.execute("SELECT COUNT(*) FROM ukrajinet_word_index")
    count1 = cursor.fetchone()[0]
    assert count1 > 0

    # Test idempotency (calling _ensure_ukrajinet_word_index again should be a no-op)
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = None
    _synonyms_from_ukrajinet(conn, "йти", out_idx, seen_idx)
    assert "пішки" in out_idx

    cursor = conn.execute("SELECT COUNT(*) FROM ukrajinet_word_index")
    count2 = cursor.fetchone()[0]
    assert count1 == count2

    # Test parity vs LIKE fallback
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = False
    out_like = []
    seen_like = set()
    _synonyms_from_ukrajinet(conn, "бігати", out_like, seen_like)
    assert set(out_like) == {"бігати", "швидко"}

    out_fresh_idx = []
    seen_fresh_idx = set()
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = None
    _synonyms_from_ukrajinet(conn, "бігати", out_fresh_idx, seen_fresh_idx)

    out_fresh_like = []
    seen_fresh_like = set()
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = False
    _synonyms_from_ukrajinet(conn, "бігати", out_fresh_like, seen_fresh_like)

    assert out_fresh_idx == out_fresh_like
    conn.close()


def test_ukrajinet_readonly_degrades(tmp_path, monkeypatch):
    monkeypatch.setattr(
        enrich_manifest_module,
        "_candidate_allowed",
        lambda lemma, candidate: True
    )

    db_path = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE ukrajinet (
            id INTEGER PRIMARY KEY,
            words TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати"], ensure_ascii=False),))
    conn.commit()
    conn.close()

    conn_ro = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = None
    enrich_manifest_module._UKRAJINET_INDEX_WARN_LOGGED = False

    captured_stderr = []
    monkeypatch.setattr(sys, "stderr", type("StderrMock", (object,), {"write": captured_stderr.append, "flush": lambda self: None})())

    out = []
    seen = set()
    _synonyms_from_ukrajinet(conn_ro, "бігати", out, seen)

    err_text = "".join(captured_stderr)
    assert "ukrajinet_word_index table is missing and connection is read-only" in err_text
    conn_ro.close()


def test_frazeolohichnyi_fts_exact_hit_and_parity_and_idempotency(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sources_fts.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
    """)

    conn.executemany(
        "INSERT INTO frazeolohichnyi (id, word, definition, text, source) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "яблуко розбрату", "Причина ворожнечі.", "яблуко розбрату", "Словник"),
            (2, "брати верх", "Перемагати.", "брати верх", "Словник"),
        ]
    )
    conn.commit()

    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: (("яблуко", "noun"),) if word == "яблуко" else (),
    )

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = None

    res_idx = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_idx is not None
    assert len(res_idx["items"]) == 1
    assert res_idx["items"][0]["phrase"] == "яблуко розбрату"

    cursor = conn.execute("SELECT COUNT(*) FROM frazeolohichnyi_fts")
    assert cursor.fetchone()[0] == 2

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = None
    res_idx2 = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_idx2 == res_idx
    cursor = conn.execute("SELECT COUNT(*) FROM frazeolohichnyi_fts")
    assert cursor.fetchone()[0] == 2

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = False
    res_like = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_like == res_idx
    conn.close()


def test_frazeolohichnyi_short_variant_fallback_and_missing_table(tmp_path):
    db_path = tmp_path / "test_sources_short.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
    """)
    conn.execute("INSERT INTO frazeolohichnyi (id, word, definition, text, source) VALUES (?, ?, ?, ?, ?)",
                 (1, "як", "Опис слова як.", "як", "Словник"))
    conn.commit()

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = None
    _idioms_frazeolohichnyi(conn, "як")

    cursor = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frazeolohichnyi_fts'")
    assert cursor.fetchone() is None
    conn.close()


def test_missing_table_returns_none():
    conn = sqlite3.connect(":memory:")
    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = None
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE = None

    # frazeolohichnyi returns None (existing behavior)
    assert _idioms_frazeolohichnyi(conn, "яблуко") is None

    # ukrajinet raises sqlite3.OperationalError (existing behavior)
    out = []
    seen = set()
    with pytest.raises(sqlite3.OperationalError):
        _synonyms_from_ukrajinet(conn, "бігати", out, seen)
    conn.close()


def test_frazeolohichnyi_readonly_degrades(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sources_ro.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
    """)
    conn.execute("INSERT INTO frazeolohichnyi (id, word, definition, text, source) VALUES (?, ?, ?, ?, ?)",
                 (1, "яблуко розбрату", "Причина ворожнечі.", "яблуко розбрату", "Словник"))
    conn.commit()
    conn.close()

    conn_ro = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE = None
    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_WARN_LOGGED = False

    captured_stderr = []
    monkeypatch.setattr(sys, "stderr", type("StderrMock", (object,), {"write": captured_stderr.append, "flush": lambda self: None})())

    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: (("яблуко", "noun"),) if word == "яблуко" else (),
    )

    res = _idioms_frazeolohichnyi(conn_ro, "яблуко")
    assert res is not None
    assert res["items"][0]["phrase"] == "яблуко розбрату"

    err_text = "".join(captured_stderr)
    assert "frazeolohichnyi_fts table is missing and connection is read-only" in err_text
    conn_ro.close()
