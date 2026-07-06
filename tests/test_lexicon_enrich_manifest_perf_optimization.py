import json
import sqlite3
import sys

import pytest

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.enrich_manifest import (
    _idioms_frazeolohichnyi,
    _synonyms_from_ukrajinet,
)


def _force_like(cache: dict, conn: sqlite3.Connection) -> None:
    """Seed the per-DB availability cache with False so the LIKE path runs."""
    cache[enrich_manifest_module._db_cache_key(conn)] = False


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

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()

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
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()
    _synonyms_from_ukrajinet(conn, "йти", out_idx, seen_idx)
    assert "пішки" in out_idx

    cursor = conn.execute("SELECT COUNT(*) FROM ukrajinet_word_index")
    count2 = cursor.fetchone()[0]
    assert count1 == count2

    # Test parity vs LIKE fallback
    _force_like(enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE, conn)
    out_like = []
    seen_like = set()
    _synonyms_from_ukrajinet(conn, "бігати", out_like, seen_like)
    assert set(out_like) == {"бігати", "швидко"}

    out_fresh_idx = []
    seen_fresh_idx = set()
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()
    _synonyms_from_ukrajinet(conn, "бігати", out_fresh_idx, seen_fresh_idx)

    out_fresh_like = []
    seen_fresh_like = set()
    _force_like(enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE, conn)
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

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()
    enrich_manifest_module._UKRAJINET_INDEX_WARN_LOGGED = False

    captured_stderr = []
    monkeypatch.setattr(sys, "stderr", type("StderrMock", (object,), {"write": captured_stderr.append, "flush": lambda self: None})())

    out = []
    seen = set()
    _synonyms_from_ukrajinet(conn_ro, "бігати", out, seen)

    err_text = "".join(captured_stderr)
    assert "ukrajinet_word_index table is missing and connection is read-only" in err_text
    conn_ro.close()


def test_ukrajinet_cyrillic_case_parity(tmp_path, monkeypatch):
    """The sidecar index casefolds Cyrillic at build time; SQLite's ASCII-only
    lower()+LIKE does not. The indexed path must NOT surface rows the LIKE
    fallback never matched (capitalized Cyrillic in the raw JSON)."""
    monkeypatch.setattr(
        enrich_manifest_module,
        "_candidate_allowed",
        lambda lemma, candidate: True
    )

    db_path = tmp_path / "case_parity.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE ukrajinet (
            id INTEGER PRIMARY KEY,
            words TEXT NOT NULL DEFAULT ''
        )
    """)
    # Capital Б: SQLite lower() leaves 'Брати' untouched → LIKE '%брати%' misses
    # the row. 'родичі' deliberately does not embed the needle as a substring.
    conn.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["Брати", "родичі"], ensure_ascii=False),))
    conn.commit()

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()
    out_idx, seen_idx = [], set()
    _synonyms_from_ukrajinet(conn, "брати", out_idx, seen_idx)

    _force_like(enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE, conn)
    out_like, seen_like = [], set()
    _synonyms_from_ukrajinet(conn, "брати", out_like, seen_like)

    assert out_idx == out_like == []
    conn.close()


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

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()

    res_idx = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_idx is not None
    assert len(res_idx["items"]) == 1
    assert res_idx["items"][0]["phrase"] == "яблуко розбрату"

    cursor = conn.execute("SELECT COUNT(*) FROM frazeolohichnyi_fts")
    assert cursor.fetchone()[0] == 2

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()
    res_idx2 = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_idx2 == res_idx
    cursor = conn.execute("SELECT COUNT(*) FROM frazeolohichnyi_fts")
    assert cursor.fetchone()[0] == 2

    _force_like(enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE, conn)
    res_like = _idioms_frazeolohichnyi(conn, "яблуко")
    assert res_like == res_idx
    conn.close()


def test_frazeolohichnyi_fts_limit_crowding_parity(tmp_path, monkeypatch):
    """codex #4514 finding 1: FTS trigram folds Cyrillic case, LIKE does not.
    Uppercase near-matches with LOWER ids must not crowd true lowercase
    matches out of the LIMIT-80 window — the emitted set must be identical
    to the LIKE fallback's."""
    db_path = tmp_path / "crowding.db"
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
    rows = []
    # ids 1..85: uppercase-Cyrillic words — trigram MATCHes them (case fold),
    # SQLite lower()+LIKE does not. On the broken path these fill the LIMIT-80
    # window and then die in post-filtering → empty result.
    for i in range(1, 86):
        rows.append((i, f"ЯБЛУКО РОЗБРАТУ {i}", f"Опис ворожнечі {i}.", "", "Словник"))
    # ids 100..184: lowercase true matches (more than 80).
    for i in range(100, 185):
        rows.append((i, f"яблуко розбрату {i}", f"Причина ворожнечі {i}.", "", "Словник"))
    conn.executemany(
        "INSERT INTO frazeolohichnyi (id, word, definition, text, source) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()

    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: (("яблуко", "noun"),) if word == "яблуко" else (),
    )

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()
    res_idx = _idioms_frazeolohichnyi(conn, "яблуко")

    _force_like(enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE, conn)
    res_like = _idioms_frazeolohichnyi(conn, "яблуко")

    assert res_idx == res_like
    assert res_idx is not None and len(res_idx["items"]) > 0
    conn.close()


def test_index_availability_cached_per_database(tmp_path):
    """codex #4514 finding 2: DB A's availability verdict must not leak onto
    DB B in the same process."""
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"

    conn_a = sqlite3.connect(db_a)
    conn_a.execute("CREATE TABLE ukrajinet (id INTEGER PRIMARY KEY, words TEXT NOT NULL DEFAULT '')")
    conn_a.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати"], ensure_ascii=False),))
    conn_a.commit()

    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()
    enrich_manifest_module._UKRAJINET_INDEX_WARN_LOGGED = True  # silence warns

    assert enrich_manifest_module._ensure_ukrajinet_word_index(conn_a) is True

    # DB B: same table shape, NO sidecar index, read-only connection. With the
    # leaked verdict it would claim True and serve empty indexed results; the
    # per-DB cache must return False (degrade to LIKE) instead.
    setup_b = sqlite3.connect(db_b)
    setup_b.execute("CREATE TABLE ukrajinet (id INTEGER PRIMARY KEY, words TEXT NOT NULL DEFAULT '')")
    setup_b.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати"], ensure_ascii=False),))
    setup_b.commit()
    setup_b.close()
    conn_b = sqlite3.connect(f"file:{db_b}?mode=ro", uri=True)

    assert enrich_manifest_module._ensure_ukrajinet_word_index(conn_b) is False
    # And DB A's verdict is untouched.
    assert enrich_manifest_module._ensure_ukrajinet_word_index(conn_a) is True

    conn_a.close()
    conn_b.close()


def test_pathless_db_verdicts_never_cached(monkeypatch):
    """codex re-review repro: id(conn)-keyed sentinels get REUSED by the
    allocator after an in-memory connection closes, leaking a stale True
    verdict onto an unrelated new :memory: DB whose empty sidecar index then
    silently returns []. Pathless DBs must not be cached at all."""
    monkeypatch.setattr(
        enrich_manifest_module,
        "_candidate_allowed",
        lambda lemma, candidate: True
    )
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()

    conn_a = sqlite3.connect(":memory:")
    conn_a.execute("CREATE TABLE ukrajinet (id INTEGER PRIMARY KEY, words TEXT NOT NULL DEFAULT '')")
    conn_a.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати", "швидко"], ensure_ascii=False),))
    conn_a.commit()
    assert enrich_manifest_module._db_cache_key(conn_a) is None
    assert enrich_manifest_module._ensure_ukrajinet_word_index(conn_a) is True
    # Verdict must NOT have been cached anywhere.
    assert enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE == {}
    conn_a.close()

    # New :memory: DB (id(conn) may be recycled): table + EMPTY sidecar index.
    # A leaked True verdict would skip population and return [] silently.
    conn_b = sqlite3.connect(":memory:")
    conn_b.execute("CREATE TABLE ukrajinet (id INTEGER PRIMARY KEY, words TEXT NOT NULL DEFAULT '')")
    conn_b.execute("INSERT INTO ukrajinet (words) VALUES (?)", (json.dumps(["бігати", "швидко"], ensure_ascii=False),))
    conn_b.execute("CREATE TABLE ukrajinet_word_index (word_key TEXT, rowid INTEGER)")
    conn_b.commit()

    out, seen = [], set()
    _synonyms_from_ukrajinet(conn_b, "бігати", out, seen)
    assert "швидко" in out
    conn_b.close()


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

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()
    _idioms_frazeolohichnyi(conn, "як")

    cursor = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frazeolohichnyi_fts'")
    assert cursor.fetchone() is None
    conn.close()


def test_missing_table_returns_none():
    conn = sqlite3.connect(":memory:")
    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()
    enrich_manifest_module._UKRAJINET_INDEX_AVAILABLE.clear()

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

    enrich_manifest_module._FRAZEOLOHICHNYI_FTS_AVAILABLE.clear()
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
