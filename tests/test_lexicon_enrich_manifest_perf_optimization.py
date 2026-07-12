import sqlite3
import sys

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.enrich_manifest import _idioms_frazeolohichnyi


def _force_like(cache: dict, conn: sqlite3.Connection) -> None:
    """Seed the per-DB availability cache with False so the LIKE path runs."""
    cache[enrich_manifest_module._db_cache_key(conn)] = False


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

    assert _idioms_frazeolohichnyi(conn, "яблуко") is None
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
