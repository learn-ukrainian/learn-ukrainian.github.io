"""Offline VTS snapshot import uses fixtures, never the host dictionary stores."""

import hashlib
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
    args = ["--cache-dir", str(cache), "--db", str(db), "--dict", "vts", "--db-role", "staging", "--create-db"]
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
        ingest.main(["--cache-dir", str(cache), "--dict", "vts", "--db", str(db), "--db-role", "staging", "--create-db"])
    assert not db.exists()


def write_cache(cache, data, name=None):
    cache.mkdir(exist_ok=True)
    (cache / f"{name or data.get('lemma', 'fixture')}.json").write_text(json.dumps(data))


def test_every_cached_dictionary_is_imported_with_provenance_and_use_role(tmp_path):
    cache = tmp_path / "slovnyk_cache"
    data = snapshot()
    for slug in ("newsum", "sum", "orthoepy"):
        data["lookups"].update(snapshot(slug=slug)["lookups"])
    data["lookups"]["ukreng"] = None
    write_cache(cache, data)
    write_cache(cache, snapshot(word="other"))
    db = tmp_path / "sources.db"
    report = ingest.ingest_cache(db, cache, words=["fixture"], dictionaries=None, dry_run=False, max_text_chars=30, db_role="staging", create=True)
    assert report.entries == {"vts": 1, "newsum": 1, "sum": 1, "orthoepy": 1}
    assert report.files == 1 and report.inserted == 4
    full_text = snapshot()["lookups"]["vts"]["text"]
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT dictionary_slug, use_role, content_sha256, cache_path, importer_version, length(text) "
            "FROM slovnyk_me_entries ORDER BY dictionary_slug"
        ).fetchall()
    sha = hashlib.sha256(full_text.encode()).hexdigest()
    assert rows == [
        ("newsum", "candidate-discovery", sha, "slovnyk_cache/fixture.json", ingest.IMPORTER_VERSION, 30),
        ("orthoepy", "reference", sha, "slovnyk_cache/fixture.json", ingest.IMPORTER_VERSION, 30),
        ("sum", "contrast", sha, "slovnyk_cache/fixture.json", ingest.IMPORTER_VERSION, 30),
        ("vts", "reference", sha, "slovnyk_cache/fixture.json", ingest.IMPORTER_VERSION, 30),
    ]


def test_dict_option_narrows_the_import(tmp_path):
    cache = tmp_path / "cache"
    data = snapshot()
    data["lookups"].update(snapshot(slug="newsum")["lookups"])
    write_cache(cache, data)
    db = tmp_path / "sources.db"
    report = ingest.ingest_cache(db, cache, words=[], dictionaries=["newsum"], dry_run=False, max_text_chars=200, db_role="staging", create=True)
    assert report.entries == {"newsum": 1}
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT dictionary_slug FROM slovnyk_me_entries").fetchall() == [("newsum",)]


def test_observed_404_is_a_not_found_row_and_a_bare_null_is_not(tmp_path):
    cache = tmp_path / "slovnyk_cache"
    data = snapshot()
    data["lookups"].update({"synonyms": None, "orthoepy": None, "ukreng": None})
    data["not_found"] = {
        "synonyms": {"http_status": 404, "lookup_word": "Fixture"},
        "ukreng": {"http_status": 503, "lookup_word": "fixture"},
    }
    write_cache(cache, data)
    db = tmp_path / "sources.db"
    args = dict(words=[], dictionaries=None, dry_run=False, max_text_chars=200)
    report = ingest.ingest_cache(db, cache, **args, db_role="staging", create=True)
    assert report.misses == {"synonyms": 1}
    assert report.unproven == {"orthoepy": 1, "ukreng": 1}
    with sqlite3.connect(db) as conn:
        miss = conn.execute(
            "SELECT query, lookup_word, normalized_word, dictionary_slug, lookup_status, http_status, "
            "source_url, fetched_at, use_role, cache_path, importer_version FROM slovnyk_me_lookup_misses"
        ).fetchall()
        assert miss == [(
            "fixture", "Fixture", "fixture", "synonyms", "not_found", 404,
            "https://slovnyk.me/dict/synonyms/Fixture", snapshot()["fetched_at"], "reference",
            "slovnyk_cache/fixture.json", ingest.IMPORTER_VERSION,
        )]
        assert conn.execute("SELECT count(*) FROM slovnyk_me_entries").fetchone()[0] == 1
        first = conn.execute("SELECT * FROM slovnyk_me_lookup_misses").fetchall()
    ingest.ingest_cache(db, cache, **args, db_role="staging", create=True)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT * FROM slovnyk_me_lookup_misses").fetchall() == first


def test_positive_entry_supersedes_a_recorded_miss(tmp_path):
    cache = tmp_path / "cache"
    missing = snapshot()
    missing["lookups"] = {"vts": None}
    missing["not_found"] = {"vts": {"http_status": 404, "lookup_word": "fixture"}}
    write_cache(cache, missing)
    db = tmp_path / "sources.db"
    args = dict(words=[], dictionaries=None, dry_run=False, max_text_chars=200)
    assert ingest.ingest_cache(db, cache, **args, db_role="staging", create=True).inserted_misses == 1
    write_cache(cache, snapshot())
    ingest.ingest_cache(db, cache, **args, db_role="staging", create=True)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM slovnyk_me_lookup_misses").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM slovnyk_me_entries").fetchone()[0] == 1


def test_mirror_shape_takes_its_timestamp_from_provenance(tmp_path):
    cache = tmp_path / "cache"
    mirror = snapshot()
    del mirror["schema_version"], mirror["fetched_at"]
    mirror["sources"] = ["vts"]
    mirror["provenance"] = {"mirror": "slovnyk.me vts", "updated_at": "2026-10-10T08:16:18+00:00"}
    write_cache(cache, mirror)
    db = tmp_path / "sources.db"
    ingest.ingest_cache(db, cache, words=[], dictionaries=None, dry_run=False, max_text_chars=200, db_role="staging", create=True)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT fetched_at FROM slovnyk_me_entries").fetchall() == [("2026-10-10T08:16:18+00:00",)]


def test_dry_run_reads_but_never_writes(tmp_path):
    cache = tmp_path / "cache"
    write_cache(cache, snapshot())
    db = tmp_path / "sources.db"
    report = ingest.ingest_cache(db, cache, words=[], dictionaries=None, dry_run=True, max_text_chars=200, db_role="staging", create=True)
    assert report.entries == {"vts": 1}
    assert not db.exists()


def test_existing_database_is_backed_up_before_the_write(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    write_cache(cache, snapshot())
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE marker (value TEXT)")
        conn.execute("INSERT INTO marker VALUES ('before')")
    backups = tmp_path / "bk"
    copy_contents = []
    real_backup = ingest.backup_database

    def capture_backup(conn, db_path, backup_dir=None):
        target = real_backup(conn, db_path, backup_dir)
        with sqlite3.connect(target) as copy_conn:
            copy_contents.append((
                copy_conn.execute("SELECT value FROM marker").fetchall(),
                copy_conn.execute("SELECT name FROM sqlite_master WHERE name = 'slovnyk_me_entries'").fetchall(),
            ))
        return target

    monkeypatch.setattr(ingest, "backup_database", capture_backup)
    report = ingest.ingest_cache(
        db, cache, words=[], dictionaries=None, dry_run=False, max_text_chars=200, backup_dir=backups,
     db_role="staging", create=True)
    assert copy_contents == [([("before",)], [])]
    assert report.backup_removed is True
    assert report.backup_path is None
    assert not list(backups.glob("*.db"))


def test_network_database_is_refused_before_any_write(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    write_cache(cache, snapshot())
    monkeypatch.setattr(ingest, "is_network_filesystem_path", lambda path: True)
    db = tmp_path / "sources.db"
    with pytest.raises(ValueError, match="local storage"):
        ingest.ingest_cache(db, cache, words=[], dictionaries=None, dry_run=False, max_text_chars=200, db_role="staging", create=True)
    assert not db.exists()


def test_older_table_gains_provenance_columns_without_losing_rows(tmp_path):
    from scripts.wiki.slovnyk_me import SLOVNYK_ME_SCHEMA_SQL, ensure_slovnyk_me_schema

    db = tmp_path / "sources.db"
    legacy = SLOVNYK_ME_SCHEMA_SQL.replace(
        """    use_role TEXT NOT NULL DEFAULT 'reference',
    content_sha256 TEXT NOT NULL DEFAULT '',
    cache_path TEXT NOT NULL DEFAULT '',
    importer_version TEXT NOT NULL DEFAULT '',
    UNIQUE(normalized_word, dictionary_slug, source_url)""",
        "    UNIQUE(normalized_word, dictionary_slug, source_url)",
        1,
    )
    assert legacy != SLOVNYK_ME_SCHEMA_SQL
    with sqlite3.connect(db) as conn:
        conn.executescript(legacy)
        conn.execute("INSERT INTO slovnyk_me_entries (word, dictionary_slug) VALUES ('стара', 'vts')")
        ensure_slovnyk_me_schema(conn)
        ensure_slovnyk_me_schema(conn)
        assert conn.execute(
            "SELECT word, use_role, content_sha256, cache_path, importer_version FROM slovnyk_me_entries"
        ).fetchall() == [("стара", "reference", "", "", "")]


def test_cache_path_unavailable_and_missing_input(tmp_path):
    with pytest.raises(ValueError, match="unavailable"):
        ingest.ingest_cache(tmp_path / "db", tmp_path / "missing", words=[], dictionaries=["vts"], dry_run=True, max_text_chars=200, db_role="staging", create=True)
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
    args = ["fixture", "--words-file", str(words_file), "--dict", "vts", "--dict", "sum", "--sleep", "0", "--db", str(db), "--db-role", "staging", "--create-db"]
    assert ingest.main([*args, "--dry-run"]) == 0
    assert not db.exists()
    assert ingest.main(args) == 0
    assert calls == [("fixture", 200), ("other", 200)] * 2
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT word FROM slovnyk_me_entries ORDER BY id").fetchall() == [("fixture",), ("other",)]
    output = capsys.readouterr()
    assert "UNAVAILABLE: newsum (fixture unavailable)" in output.out
    assert "Skipping slovnyk.me/sum" in output.err


PUBLIC_CONTACT = "+https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues"


def _capture_prepared_requests(monkeypatch, status_code):
    """Capture real PreparedRequests at the HTTPAdapter boundary; no socket is opened."""
    import requests

    sent = []

    def fake_send(self, request, **kwargs):
        sent.append((request, kwargs))
        response = requests.Response()
        response.status_code = status_code
        response._content = b"<html></html>"
        response.url = request.url
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", fake_send)
    return sent


def test_wiki_fetch_entry_default_request_carries_public_contact_and_original_identity(monkeypatch):
    from scripts.wiki.slovnyk_me import DEFAULT_USER_AGENT, fetch_entry

    sent = _capture_prepared_requests(monkeypatch, 404)

    assert fetch_entry("слово", "newsum", timeout=7) is None

    (request, kwargs), = sent
    agent = request.headers["User-Agent"]
    assert agent == DEFAULT_USER_AGENT
    assert PUBLIC_CONTACT in agent
    assert agent.startswith("learn-ukrainian-slovnyk-me/1.0 ")
    assert "noncommercial educational verification; issue 1715" in agent
    assert request.url == "https://slovnyk.me/dict/newsum/%D1%81%D0%BB%D0%BE%D0%B2%D0%BE"
    assert kwargs["timeout"] == 7


def test_wiki_fetch_entry_keeps_explicit_user_agent(monkeypatch):
    from scripts.wiki.slovnyk_me import fetch_entry

    sent = _capture_prepared_requests(monkeypatch, 404)

    assert fetch_entry("слово", "newsum", user_agent="caller-agent/2.0") is None

    (request, _kwargs), = sent
    assert request.headers["User-Agent"] == "caller-agent/2.0"


def test_wiki_fetch_entry_refusal_still_raises_and_still_identifies(monkeypatch):
    import requests

    from scripts.wiki.slovnyk_me import fetch_entry

    sent = _capture_prepared_requests(monkeypatch, 403)

    with pytest.raises(requests.HTTPError):
        fetch_entry("слово", "newsum")

    (request, _kwargs), = sent
    assert PUBLIC_CONTACT in request.headers["User-Agent"]


def _staging_file(path, rows):
    """A dictionary-acquisition staging file: (target, lookup, article word, status)."""
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE job (singleton INTEGER PRIMARY KEY, spec TEXT, fingerprint TEXT, state TEXT, reason TEXT,"
        " started REAL, restarts INTEGER DEFAULT 0);"
        "CREATE TABLE results (position INTEGER PRIMARY KEY, target TEXT UNIQUE, lookup TEXT, status TEXT,"
        " attempts INTEGER DEFAULT 0, next_attempt_at REAL DEFAULT 0, http_status INTEGER, reason TEXT DEFAULT '',"
        " payload TEXT);"
    )
    spec = {"dictionary": "vts", "lookup_mode": "source_headword", "manifest_sha256": "f" * 64, "denominator": 9}
    conn.execute("INSERT INTO job VALUES (1, ?, ?, 'running', '', 0, 0)", (json.dumps(spec), "e" * 64))
    for position, (target, lookup, word, status) in enumerate(rows):
        text = f"{word} {word}́ ч. " + "Повне тлумачення статті. " * 20
        url = "https://slovnyk.me/dict/vts/" + target
        payload = None if status != "positive" else json.dumps({
            "article": {"word": word, "lookup_word": lookup, "dictionary_slug": "vts", "dictionary_label": "ВТС",
                        "source_url": url, "text": text, "title": word},
            "content_sha256": hashlib.sha256(text.encode()).hexdigest(), "source_url": url,
            "fetched_at": "2026-10-29T01:02:03+00:00", "http_status": 200, "provenance": "observed_http",
        })
        conn.execute("INSERT INTO results(position, target, lookup, status, payload) VALUES (?, ?, ?, ?, ?)",
                     (position, target, lookup, status, payload))
    conn.commit()
    conn.close()


def _empty_store(path):
    from scripts.wiki.slovnyk_me import ensure_slovnyk_me_schema

    with sqlite3.connect(path) as conn:
        ensure_slovnyk_me_schema(conn)


def test_staging_import_maps_source_headwords_and_rejects_unmatched_keys(tmp_path):
    """Defect class: staged source headwords keyed wrongly, truncated, or silently dropped."""
    staging = tmp_path / "vts" / "staging.sqlite3"
    staging.parent.mkdir()
    _staging_file(staging, [
        ("Індій", "індій", "Індій", "positive"),            # case difference: maps
        ("аве_марія", "аве_марія", "аве марія", "positive"),  # URL space encoding: maps
        ("об_яв", "об_яв", "об'яв", "positive"),            # URL apostrophe encoding: maps
        ("авто_ea0", "авто_ea0", "авто", "positive"),        # homonym suffix: maps
        ("авто", "авто", "авто...", "positive"),            # combining-form article: rejected
        ("ла[-_][_]я", "ла[-_][_]я", "ла[/'][']я", "positive"),  # bracketed variants: rejected
        ("пізніше", "пізніше", "", "pending"),             # not fetched yet: not read
    ])
    before = staging.read_bytes()
    db = tmp_path / "sources.db"
    _empty_store(db)
    report = ingest.ingest_staging(db, staging, dry_run=True, db_role="staging")
    assert (report.staged_positive, report.mapped, report.new, report.written) == (6, 4, 4, 0)
    assert report.rejected == {"prefix_entry": 1, "key_mismatch": 1}
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM slovnyk_me_entries").fetchone()[0] == 0
    assert ingest.main(["--staging", str(staging), "--db", str(db), "--db-role", "staging"]) == 0
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT normalized_word, source_url, text, content_sha256, fetched_at, importer_version, cache_path"
            " FROM slovnyk_me_entries ORDER BY normalized_word"
        ).fetchall()
    assert {row[0] for row in rows} == {"аве марія", "авто", "індій", "об'яв"}
    for _key, url, text, sha, fetched_at, version, locator in rows:
        assert len(text) > 200 and hashlib.sha256(text.encode()).hexdigest() == sha  # full witness
        assert url.startswith("https://slovnyk.me/dict/vts/") and fetched_at == "2026-10-29T01:02:03+00:00"
        assert version == ingest.STAGING_IMPORTER_VERSION and locator.startswith("staging:vts#position=")
    assert staging.read_bytes() == before


def test_staging_import_rerun_changes_nothing_and_upgrades_truncated_rows(tmp_path):
    """Defect class: a re-run or another copy's location rewrites rows, or a truncated row stays truncated."""
    staging = tmp_path / "vts" / "staging.sqlite3"
    staging.parent.mkdir()
    _staging_file(staging, [("слово", "слово", "слово", "positive"), ("нове", "нове", "нове", "positive")])
    db = tmp_path / "sources.db"
    write_cache(tmp_path / "cache", snapshot(word="слово"))
    ingest.ingest_cache(db, tmp_path / "cache", words=[], dictionaries=None, dry_run=False, max_text_chars=200,
                        db_role="staging", create=True)
    first = ingest.ingest_staging(db, staging, dry_run=False, db_role="staging")
    assert (first.new, first.updated, first.unchanged, first.written) == (1, 1, 0, 2)
    with sqlite3.connect(db) as conn:
        snapshot_rows = conn.execute("SELECT * FROM slovnyk_me_entries ORDER BY id").fetchall()
    assert len(snapshot_rows) == 2
    copy = tmp_path / "synced-copy" / "staging-mac.sqlite3"  # the same data from another location
    copy.parent.mkdir()
    copy.write_bytes(staging.read_bytes())
    for source in (staging, copy):
        again = ingest.ingest_staging(db, source, dry_run=False, db_role="staging")
        assert (again.new, again.updated, again.unchanged, again.written) == (0, 0, 2, 0)
        assert not again.backup_removed  # nothing to write: no backup taken
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT * FROM slovnyk_me_entries ORDER BY id").fetchall() == snapshot_rows
