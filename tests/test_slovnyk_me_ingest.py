"""Offline VTS snapshot import uses fixtures, never the host dictionary stores."""

import json
import sqlite3

import pytest

from scripts.ingest import slovnyk_me_ingest as ingest


def snapshot(word="fixture", slug="vts"):
    return {
        "schema_version": 4, "lemma": word, "fetched_at": "2026-08-06T05:26:40+00:00",
        "lookups": {slug: {
            "word": word, "dictionary_slug": slug, "dictionary_label": "fixture label",
            "source_url": f"https://slovnyk.me/dict/{slug}/{word}",
            "text": word + " source bytes " * 30, "title": word,
        }},
    }


def test_cache_cli_import_is_offline_bounded_idempotent_and_searchable(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    source = cache / "fixture.json"
    source.write_text(json.dumps(snapshot()))
    before = source.read_bytes()
    db = tmp_path / "sources.db"
    monkeypatch.setattr(ingest, "fetch_entries", lambda *a, **kw: pytest.fail("offline import fetched live data"))
    args = ["--cache-dir", str(cache), "--db", str(db), "--dict", "vts"]
    assert ingest.main([*args, "--dry-run"]) == 0
    assert not db.exists()
    assert ingest.main(args) == 0
    with sqlite3.connect(db) as conn:
        first = conn.execute("SELECT * FROM slovnyk_me_entries").fetchall()
        assert conn.execute("SELECT count(*) FROM slovnyk_me_entries_fts WHERE slovnyk_me_entries_fts MATCH 'fixture'").fetchone()[0] == 1
        row = conn.execute("SELECT text, fetched_at, is_modern, source_url FROM slovnyk_me_entries").fetchone()
        assert len(row[0]) == 200
        assert row[1:] == (snapshot()["fetched_at"], 1, "https://slovnyk.me/dict/vts/fixture")
    assert ingest.main(args) == 0
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT * FROM slovnyk_me_entries").fetchall() == first
    assert source.read_bytes() == before


@pytest.mark.parametrize("mutation", ["version", "url", "word", "slug", "timestamp", "lookups"])
def test_bad_cache_refuses_before_creating_database(tmp_path, mutation):
    cache = tmp_path / "cache"
    cache.mkdir()
    data = snapshot()
    if mutation == "version":
        data["schema_version"] = 3
    elif mutation == "url":
        data["lookups"]["vts"]["source_url"] = "https://example.org/dict/vts/fixture"
    elif mutation == "word":
        data["lookups"]["vts"]["word"] = ""
    elif mutation == "slug":
        data["lookups"]["vts"]["dictionary_slug"] = "sum"
    elif mutation == "timestamp":
        data["fetched_at"] = ""
    else:
        data["lookups"] = []
    (cache / "fixture.json").write_text(json.dumps(data))
    db = tmp_path / "sources.db"
    with pytest.raises(ValueError):
        ingest.main(["--cache-dir", str(cache), "--dict", "vts", "--db", str(db)])
    assert not db.exists()


def test_cache_filter_misses_and_overlapping_dictionaries(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    data = snapshot()
    data["lookups"].update(snapshot(slug="sum")["lookups"])
    data["lookups"]["newsum"] = None
    (cache / "fixture.json").write_text(json.dumps(data))
    (cache / "other.json").write_text(json.dumps(snapshot(word="other")))
    db = tmp_path / "sources.db"
    assert ingest.ingest_cache(db, cache, words=["fixture"], dictionaries=["vts", "sum", "newsum"], dry_run=False, max_text_chars=30) == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT word, dictionary_slug FROM slovnyk_me_entries").fetchall() == [("fixture", "vts")]


def test_cache_path_unavailable_and_missing_input(tmp_path):
    with pytest.raises(ValueError, match="unavailable"):
        ingest.ingest_cache(tmp_path / "db", tmp_path / "missing", words=[], dictionaries=["vts"], dry_run=True, max_text_chars=200)
    assert ingest.main([]) == 2
    assert "--cache-dir" in ingest.build_parser().format_help()


def test_existing_live_cli_path_and_word_file_still_use_bounded_fetch(tmp_path, monkeypatch, capsys):
    calls = []

    def fetch(word, **kwargs):
        calls.append((word, kwargs["max_text_chars"]))
        kwargs["outages"].append({"dictionary_slug": "newsum", "error": "fixture unavailable"})
        row = snapshot(word)["lookups"]["vts"]
        row["text"] = "bounded fixture bytes"
        row["fetched_at"] = snapshot()["fetched_at"]
        return [row]

    monkeypatch.setattr(ingest, "fetch_entries", fetch)
    words_file = tmp_path / "words.txt"
    words_file.write_text("# fixture\nfixture\nother\n\n")
    db = tmp_path / "sources.db"
    args = ["fixture", "--words-file", str(words_file), "--dict", "vts", "--dict", "sum", "--sleep", "0", "--db", str(db)]
    assert ingest.main([*args, "--dry-run"]) == 0
    assert not db.exists()
    assert ingest.main(args) == 0
    assert calls == [("fixture", 200), ("other", 200)] * 2
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT word FROM slovnyk_me_entries ORDER BY id").fetchall() == [("fixture",), ("other",)]
    output = capsys.readouterr()
    assert "UNAVAILABLE: newsum (fixture unavailable)" in output.out
    assert "Skipping slovnyk.me/sum" in output.err
