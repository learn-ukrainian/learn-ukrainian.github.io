"""Fixture proof for the fenced ULIF raw-cache migration."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.tools import migrate_ulif_raw
from scripts.wiki import sources_db


def test_migration_preserves_lookups_and_swaps_cleanly(tmp_path: Path, capsys):
    db = tmp_path / "sources.db"
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="за́мок",
        sections={"synonyms": [{"terms": [{"text": "фортеця"}]}]},
        raw_responses={"synonyms": "<html>замок</html>"},
        retrieved_at="2026-09-25T00:00:00+00:00",
        parser_version="test",
        status="ok",
        db_path=db,
    )
    sources_db.store_ulif_dictua_entry(
        word="немає",
        canonical_headword="",
        sections={},
        raw_responses={},
        retrieved_at="2026-09-25T00:00:00+00:00",
        parser_version="test",
        status="not_found",
        db_path=db,
    )
    cache = ulif_raw_cache.cache_path(db)
    with closing(ulif_raw_cache.open_cache(cache, create=False)) as raw, closing(sqlite3.connect(db)) as source:
        source.execute(ulif_raw_cache.RAW_SCHEMA)
        source.executemany(
            "INSERT INTO ulif_dictua_raw_responses VALUES (?, ?, ?, ?)",
            list(raw.execute("SELECT response_sha256, body, content_type, stored_at FROM ulif_dictua_raw_responses")),
        )
        source.commit()
    lookup_file = tmp_path / "lookups.json"
    assert migrate_ulif_raw.main(["--db", str(db), "--record-lookups", str(lookup_file)]) == 0
    assert len(json.loads(lookup_file.read_text())["words"]) == 2
    assert migrate_ulif_raw.main(["--db", str(db), "--check"]) == 0
    assert migrate_ulif_raw.main(["--db", str(db), "--execute"]) == 0
    assert migrate_ulif_raw.main(["--db", str(db), "--compare-lookups", str(lookup_file)]) == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1]) == {"compared": 2, "identical": True}

    with closing(sqlite3.connect(db)) as source, closing(ulif_raw_cache.open_cache(cache, create=False)) as raw:
        assert source.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert source.execute("SELECT 1 FROM sqlite_master WHERE name='ulif_dictua_raw_responses'").fetchone() is None
        assert source.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0] == 2
        rows = list(raw.execute("SELECT response_sha256, body FROM ulif_dictua_raw_responses"))
        assert len(rows) == 3
        assert all(hashlib.sha256(body).hexdigest() == sha for sha, body in rows)
    assert db.with_name("sources.db.pre-8800").is_file()
    with closing(sqlite3.connect(db.with_name("sources.db.pre-8800"))) as post_drop:
        assert (
            post_drop.execute("SELECT 1 FROM sqlite_master WHERE name='ulif_dictua_raw_responses'").fetchone() is None
        )
    assert not db.with_name("sources.db.new").exists()
    assert not Path(f"{db}-wal").exists()
    assert not Path(f"{db}-shm").exists()


def test_writer_cannot_add_raw_row_during_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "sources.db"
    body = b"initial"
    sha = hashlib.sha256(body).hexdigest()
    with closing(sqlite3.connect(db)) as source:
        source.execute("PRAGMA journal_mode=WAL")
        source.execute(ulif_raw_cache.RAW_SCHEMA)
        source.execute(
            "INSERT INTO ulif_dictua_raw_responses VALUES (?, ?, ?, ?)",
            (sha, body, "text/html", "first"),
        )
        source.commit()
    attempted = False
    original_put = ulif_raw_cache.put

    def put_during_copy(*args, **kwargs):
        nonlocal attempted
        if not attempted:
            attempted = True
            second_body = b"late writer"
            with closing(sqlite3.connect(db, timeout=0.05)) as writer:
                with pytest.raises(sqlite3.OperationalError, match="database is locked"):
                    writer.execute(
                        "INSERT INTO ulif_dictua_raw_responses VALUES (?, ?, ?, ?)",
                        (hashlib.sha256(second_body).hexdigest(), second_body, "text/html", "late"),
                    )
        return original_put(*args, **kwargs)

    monkeypatch.setattr(ulif_raw_cache, "put", put_during_copy)
    report = migrate_ulif_raw.migrate(db, ulif_raw_cache.cache_path(db))
    assert attempted
    assert report["copied_rows"] == 1
    with closing(ulif_raw_cache.open_cache(ulif_raw_cache.cache_path(db), create=False)) as raw:
        assert list(raw.execute("SELECT response_sha256 FROM ulif_dictua_raw_responses")) == [(sha,)]


def test_row_added_after_preflight_is_copied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "sources.db"
    body = b"late but before lock"
    sha = hashlib.sha256(body).hexdigest()
    with closing(sqlite3.connect(db)) as source:
        source.execute("PRAGMA journal_mode=WAL")
        source.execute(ulif_raw_cache.RAW_SCHEMA)
        source.commit()
    original_preflight = migrate_ulif_raw._preflight

    def preflight_then_insert(path: Path):
        report = original_preflight(path)
        with closing(sqlite3.connect(path)) as writer:
            writer.execute(
                "INSERT INTO ulif_dictua_raw_responses VALUES (?, ?, ?, ?)",
                (sha, body, "text/html", "late"),
            )
            writer.commit()
        return report

    monkeypatch.setattr(migrate_ulif_raw, "_preflight", preflight_then_insert)
    report = migrate_ulif_raw.migrate(db, ulif_raw_cache.cache_path(db))
    assert report["preflight"]["raw_rows"] == 0
    assert report["copied_rows"] == 1
    with closing(ulif_raw_cache.open_cache(ulif_raw_cache.cache_path(db), create=False)) as raw:
        assert raw.execute(
            "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (sha,)
        ).fetchone() == (body,)


def test_same_count_but_different_cache_row_keeps_source_table(tmp_path: Path):
    db = tmp_path / "sources.db"
    body = b"response"
    sha = hashlib.sha256(body).hexdigest()
    with closing(sqlite3.connect(db)) as source:
        source.execute("PRAGMA journal_mode=WAL")
        source.execute(ulif_raw_cache.RAW_SCHEMA)
        source.execute(
            "INSERT INTO ulif_dictua_raw_responses VALUES (?, ?, ?, ?)",
            (sha, body, "text/html", "source timestamp"),
        )
        source.commit()
    cache = ulif_raw_cache.cache_path(db)
    ulif_raw_cache.put(sha, body, "text/html", "different timestamp", path=cache)

    with pytest.raises(RuntimeError, match="raw rows differ"):
        migrate_ulif_raw.migrate(db, cache)
    with closing(sqlite3.connect(db)) as source:
        assert source.execute("SELECT COUNT(*) FROM ulif_dictua_raw_responses").fetchone()[0] == 1
    assert not db.with_name("sources.db.pre-8800").exists()


def test_corrupt_cache_body_fails_closed(tmp_path: Path):
    cache = tmp_path / "raw.sqlite"
    body = b"<html>valid</html>"
    sha = hashlib.sha256(body).hexdigest()
    ulif_raw_cache.put(sha, body, path=cache)
    with ulif_raw_cache.open_cache(cache) as raw:
        raw.execute("UPDATE ulif_dictua_raw_responses SET body = X'00'")
    with pytest.raises(ValueError, match="hash mismatch"):
        ulif_raw_cache.get(sha, path=cache)


def test_caller_transaction_cannot_publish_entry_before_cache(tmp_path: Path):
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    sources_db.ensure_ulif_dictua_schema(conn)
    conn.execute("BEGIN")
    stored = sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="за́мок",
        sections={},
        raw_responses={"paradigm": "<html>source</html>"},
        retrieved_at="2026-09-25T00:00:00+00:00",
        parser_version="test",
        status="ok",
        conn=conn,
        db_path=db,
    )
    assert stored is not None
    assert ulif_raw_cache.resolve_ref(stored["raw_response_ref"], path=ulif_raw_cache.cache_path(db))
    with sqlite3.connect(db) as separate:
        assert separate.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0] == 0
    conn.rollback()
    conn.close()
    with sqlite3.connect(db) as separate:
        assert separate.execute("SELECT COUNT(*) FROM ulif_dictua_entries").fetchone()[0] == 0


def test_manifest_references_are_verified_recursively(tmp_path: Path):
    cache = tmp_path / "raw.sqlite"
    body = b"<html>article</html>"
    body_sha = hashlib.sha256(body).hexdigest()
    ulif_raw_cache.put(body_sha, body, path=cache)
    nested = json.dumps({"a": f"sha256:{body_sha}", "b": f"sha256:{body_sha}"}).encode()
    nested_sha = hashlib.sha256(nested).hexdigest()
    ulif_raw_cache.put(nested_sha, nested, "application/json", path=cache)
    assert ulif_raw_cache.resolve_ref(f"sha256:{nested_sha}", path=cache) == nested
    with ulif_raw_cache.open_cache(cache) as raw:
        raw.execute("DELETE FROM ulif_dictua_raw_responses WHERE response_sha256 = ?", (body_sha,))
    assert ulif_raw_cache.resolve_ref(f"sha256:{nested_sha}", path=cache) is None
    mixed = json.dumps({"valid": f"sha256:{body_sha}", "invalid": "plain text"}).encode()
    mixed_sha = hashlib.sha256(mixed).hexdigest()
    ulif_raw_cache.put(mixed_sha, mixed, "application/json", path=cache)
    with pytest.raises(ValueError, match="Invalid ULIF raw response manifest"):
        ulif_raw_cache.resolve_ref(f"sha256:{mixed_sha}", path=cache)


def test_store_preserves_non_section_http_responses(tmp_path: Path):
    db = tmp_path / "sources.db"
    stored = sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="за́мок",
        sections={},
        raw_responses={"initial": "<html>register</html>", "paradigm": "<html>entry</html>"},
        retrieved_at="2026-09-25T00:00:00+00:00",
        parser_version="test",
        status="ok",
        db_path=db,
    )
    assert stored is not None
    manifest = sources_db.resolve_ulif_dictua_raw_response(stored["raw_response_ref"], db_path=db)
    assert manifest is not None
    assert set(json.loads(manifest)) == {"initial", "paradigm"}


def test_lookup_sample_keeps_rare_status_after_large_section_strata(tmp_path: Path):
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        sources_db.ensure_ulif_dictua_schema(conn)
        for kind in sources_db.ULIF_DICTUA_SECTION_KINDS:
            for index in range(100):
                word = f"{kind}_{index}"
                entry_id = conn.execute(
                    "INSERT INTO ulif_dictua_entries (normalized_query, status) VALUES (?, 'ok') RETURNING id",
                    (word,),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO ulif_dictua_sections (entry_id, kind, source_order, payload_json) VALUES (?, ?, 0, '{}')",
                    (entry_id, kind),
                )
        for index in range(100):
            conn.execute(
                "INSERT INTO ulif_dictua_entries (normalized_query, status) VALUES (?, 'not_found')",
                (f"missing_{index}",),
            )
        conn.execute("INSERT INTO ulif_dictua_entries (normalized_query, status) VALUES ('rare_parse', 'parse_error')")
    sample = migrate_ulif_raw._lookup_sample(db)
    assert len(sample) == 200
    assert "rare_parse" in sample
    assert any(word.startswith("missing_") for word in sample)
    for kind in sources_db.ULIF_DICTUA_SECTION_KINDS:
        assert any(word.startswith(f"{kind}_") for word in sample)
