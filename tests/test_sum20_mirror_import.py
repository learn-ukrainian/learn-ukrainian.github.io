"""СУМ-20 mirror import: rule sum20-mirror-rule-v1, reader routing and the generation writer (#8579).

Every article here is synthetic fixture text, not dictionary content. Every
store lives under tmp_path in the generation layout (docs/runbooks/storage-topology.md).
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.ingest import sum20_mirror_import as importer
from scripts.lexdata import generation, transforms
from scripts.lexicon import sum20_lookup
from scripts.lexicon.sum20_store import Sum20StoreError
from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import cli as storage_cli
from scripts.storage import generations
from scripts.wiki import sources_db, sum20_mirror
from scripts.wiki.sum20_official import PARSER_VERSION, ensure_sum20_official_schema, normalize_sum20_lookup

SPAWN = multiprocessing.get_context("spawn")
WAIT = 60  # an event that never fires fails the test instead of hanging it
FOOTER = " Джерело: Словник української мови (СУМ-20) на Slovnyk.me"
# (url slug, page headword, article body). The body follows the page's own headword prefix.
MIRROR = [
    ("берег", "берег", "БЕ́РЕГ, а, ч. Synthetic mirror-only sense."),
    ("вода", "вода", "ВОДА́, и́, ж. Synthetic agreeing sense."),
    ("дух", "дух", "ДУХ, у, ч. Synthetic mirror sense for a quarantined key."),
    ("ліс", "ліс", "ЛІС, у, ч. Synthetic mirror sense that differs."),
    ("м_ясо", "м'ясо", "М'Я́СО, а, с. Synthetic apostrophe headword."),
]
# (wordid, key, article text, quarantine reason)
OFFICIAL = [
    (10, "вода", "ВОДА́, и́, ж. Synthetic agreeing sense.", ""),
    (11, "дух", "ДУХ, у, ч. Synthetic quarantined official row.", "unverified-provenance: fixture"),
    (12, "ліс", "ЛІС¹, у, ч. Synthetic official homonym one.", ""),
    (13, "ліс", "ЛІС², у, ч. Synthetic official homonym two.", ""),
]


def _url(slug: str) -> str:
    return f"https://slovnyk.example/dict/newsum/{slug}"


def _make_staging(path: Path, rows=MIRROR) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript("""
            CREATE TABLE sum20_slovnyk_articles (url TEXT PRIMARY KEY, lemma TEXT NOT NULL,
                mirror TEXT NOT NULL DEFAULT 'slovnyk.me newsum', title TEXT NOT NULL, headword TEXT NOT NULL,
                text TEXT NOT NULL, paragraphs_json TEXT NOT NULL DEFAULT '[]', content_sha256 TEXT NOT NULL,
                source_url TEXT NOT NULL, fetched_at TEXT NOT NULL, raw_html TEXT NOT NULL DEFAULT '',
                senses_json TEXT NOT NULL DEFAULT '[]', sense_count INTEGER NOT NULL DEFAULT 0,
                raw_sense_count INTEGER NOT NULL DEFAULT 0, mismatch_senses INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE sum20_slovnyk_outcomes (url TEXT PRIMARY KEY, status TEXT NOT NULL, http_code INTEGER,
                attempted_at TEXT NOT NULL, error_text TEXT NOT NULL DEFAULT '');
            CREATE TABLE sum20_slovnyk_checkpoint (singleton INTEGER PRIMARY KEY, completed_count INTEGER NOT NULL,
                last_url TEXT NOT NULL, updated_at TEXT NOT NULL);
        """)
        for slug, headword, body in rows:
            text = f"{headword} {body}{FOOTER}"
            senses = {
                "headword": body.split(",")[0],
                "header_grammar": "а, ч.",
                "senses": [{"sense_num": 1, "labels": "", "definition": "parsed", "raw_text": f"1. {body}"}],
            }
            conn.execute(
                "INSERT INTO sum20_slovnyk_articles (url, lemma, title, headword, text, content_sha256, source_url, "
                "fetched_at, senses_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _url(slug),
                    slug,
                    f"{headword} — fixture",
                    headword,
                    text,
                    hashlib.sha256(text.encode()).hexdigest(),
                    _url(slug),
                    "2026-10-01T00:00:00+00:00",
                    json.dumps(senses, ensure_ascii=False),
                ),
            )
            conn.execute("INSERT INTO sum20_slovnyk_outcomes VALUES (?, 'ok', 200, 'fixture', '')", (_url(slug),))
        conn.execute("INSERT INTO sum20_slovnyk_checkpoint VALUES (1, ?, ?, 'fixture')", (len(rows), _url(rows[-1][0])))
        conn.commit()
        conn.execute("PRAGMA journal_mode=WAL")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_live(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        ensure_sum20_official_schema(conn)
        for wordid, key, text, reason in OFFICIAL:
            conn.execute(
                "INSERT INTO sum20_articles (wordid, normalized_lookup_key, headword, stressed_headword, article_html, "
                "article_text, definition_text, official_url, fetched_at, content_sha256, parser_version, "
                "quarantine_reason) VALUES (?, ?, ?, ?, '', ?, ?, ?, 'fixture', ?, ?, ?)",
                (
                    wordid,
                    normalize_sum20_lookup(key),
                    key.upper(),
                    key.upper(),
                    text,
                    text,
                    f"https://official.example/?wordid={wordid}",
                    f"digest-{wordid}",
                    PARSER_VERSION,
                    reason,
                ),
            )
            conn.execute(
                "INSERT INTO sum20_senses (article_id, sense_order, definition) "
                "SELECT id, 1, definition_text FROM sum20_articles WHERE wordid = ?",
                (wordid,),
            )
        conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT)")
        conn.execute("INSERT INTO textbooks (text) VALUES ('fixture chunk')")
        conn.commit()
        conn.execute("PRAGMA journal_mode=WAL")
    path.chmod(0o444)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bootstrap(selector: Path) -> Path:
    """Turn the fixture's regular store into its first generation, as the operator's bootstrap does."""
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        return generations.publish_generation(selector, held, mode="bootstrap").generation


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A fixture repository: a held store behind its selector and a complete staged mirror."""
    for name in ("LEXDATA_DB_PATH", "LU_LEXDATA_DB", "LU_SOURCES_DB", "SOURCES_DB_PATH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_FD, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_SELECTOR, raising=False)
    # The publisher's real margin (generation + 10 GiB + 4 GiB) is tested with the generations.
    monkeypatch.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "0")
    monkeypatch.setenv("LU_EVIDENCE_WAL_CEILING_BYTES", "0")
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sum20_lookup, "REPO_ROOT", tmp_path)
    data = tmp_path / "data"
    _make_live(data / "sources.db")
    _bootstrap(data / "sources.db")
    sha = _make_staging(data / "sum20_slovnyk_staging.db")
    target = importer.writer_target(test_data_dir=data)
    return target, sha


def _selected(target) -> Path:
    return generations.inspect_selector(target.selector).generation


def _import(target, sha):
    """Run the import; return its payload and the generation it published."""
    payload = importer.run_import(target, sha)
    return payload, target.data_dir / generations.GENERATIONS_DIRNAME / payload["generation"]


def _query(word, db=None):
    return sources_db.query_sum20(word, db_path=db)


def _leftovers(target) -> list[Path]:
    """Candidate and staging-snapshot files the import must never leave in ``data/``."""
    return sorted(target.data_dir.glob(".sources.db.*")) + sorted(target.data_dir.glob(f".{importer.STAGING_NAME}.*"))


def test_import_leaves_the_previous_generation_untouched_and_verifies_the_rule(store):
    target, sha = store
    previous = _selected(target)
    before = _sha(previous)
    payload, published = _import(target, sha)

    assert _sha(previous) == before
    assert payload["previous"] == previous.name and _selected(target) == published
    assert payload["verification"]["relation_counts"] == {
        "mirror_only": 2,
        "agrees_with_official": 1,
        "official_quarantined": 1,
        "differs_from_official": 1,
    }
    assert payload["reconcile_differing"] == 2  # ліс and the quarantined дух; вода matches
    assert payload["default_reader"] == {"key_sampled": True, "serves_mirror": True}
    assert generations.is_held(published) and _sha(published) == payload["sha256"]
    assert generations.read_receipt(published)["state"] == "published"
    assert not _leftovers(target)


def test_rule_serves_official_first_and_flags_every_mirror_row(store):
    target, sha = store
    _, candidate = _import(target, sha)

    berег = _query("берег", candidate)
    assert [(r["source_role"], r["official_relation"]) for r in berег] == [("mirror", "mirror_only")]
    assert berег[0]["source_id"] == sum20_mirror.MIRROR_SOURCE_ID
    assert berег[0]["source_url"] == _url("берег") and berег[0]["retrieved_at"] == "2026-10-01T00:00:00+00:00"
    assert berег[0]["senses"][0]["definition"].startswith("БЕ́РЕГ")  # verbatim raw text, number stripped

    assert [r["source_role"] for r in _query("вода", candidate)] == ["official"]  # agreeing mirror suppressed

    дух = _query("дух", candidate)  # the quarantined official row stays hidden
    assert [(r["source_role"], r.get("official_relation")) for r in дух] == [("mirror", "official_quarantined")]

    ліс = _query("ліс", candidate)  # both official homonyms first, then the differing mirror row
    assert [r["source_role"] for r in ліс] == ["official", "official", "mirror"]
    assert ліс[2]["official_relation"] == "differs_from_official"
    assert [r["source_record_id"] for r in ліс[:2]] == ["12", "13"]

    assert _query("м'ясо", candidate)[0]["source_record_id"] == _url("м_ясо")  # headword, not slug


def test_official_records_and_tables_are_unchanged(store):
    target, sha = store
    previous = _selected(target)
    _, candidate = _import(target, sha)
    for word in ("вода", "ліс", "дух"):
        assert [r for r in _query(word, candidate) if r["source_role"] == "official"] == _query(word, previous)
    with closing(open_readonly(candidate)) as new, closing(open_readonly(previous)) as old:
        assert importer.official_digest(new) == importer.official_digest(old)
        quarantined = new.execute("SELECT wordid FROM sum20_articles WHERE quarantine_reason != ''").fetchall()
    assert quarantined == [(11,)]


def test_rule_is_judged_at_read_time_against_a_later_official_row(store, tmp_path):
    target, sha = store
    _, published = _import(target, sha)
    later = tmp_path / "later.db"  # a scratch copy; a published generation is never written in place
    with closing(open_readonly(published)) as source, closing(sqlite3.connect(later)) as conn:
        source.backup(conn)
        conn.execute(  # an official ingest later adds the mirror-only key
            "INSERT INTO sum20_articles (wordid, normalized_lookup_key, headword, stressed_headword, article_html, "
            "article_text, definition_text, official_url, fetched_at, content_sha256, parser_version) "
            "VALUES (20, 'берег', 'БЕРЕГ', 'БЕРЕГ', '', 'БЕ́РЕГ, а, ч. Synthetic mirror-only sense.', '', "
            "'https://official.example/?wordid=20', 'fixture', 'digest-20', ?)",
            (PARSER_VERSION,),
        )
        conn.commit()
    assert [r["source_role"] for r in _query("берег", later)] == ["official"]


def test_import_retains_the_previous_generation_and_restore_selects_it_again(store):
    target, sha = store
    previous = _selected(target)
    old_sha, old_ino = _sha(previous), previous.stat().st_ino
    payload, published = _import(target, sha)

    assert _query("берег")[0]["source_role"] == "mirror"  # default selection reads the new generation
    assert previous.stat().st_ino == old_ino and _sha(previous) == old_sha  # retained in place, never copied
    assert generations.read_receipt(published)["previous"] == previous.name

    assert storage_cli.main(["restore-generation", str(previous), "--store", str(target.selector)]) == 0
    assert _selected(target) == previous and _sha(previous) == old_sha
    assert _query("берег") == []
    assert storage_cli.main(["restore-generation", str(published), "--store", str(target.selector)]) == 0
    assert _selected(target) == published and _sha(published) == payload["sha256"]  # the new one was retained too


def reader_across_publication(selector: str, ready, go, out) -> None:
    """Open the store, read, wait while the import publishes, then read again on the same connection."""

    def view(conn) -> tuple:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE name LIKE 'sum20_mirror%' ORDER BY name").fetchall()
        return (
            [str(name) for (name,) in tables],
            importer.official_digest(conn),
            conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
            len(sum20_mirror.served_rows(conn, "берег")),
        )

    try:
        with closing(open_readonly(selector, isolation_level=None)) as conn:
            conn.execute("BEGIN")
            pinned = view(conn)
            ready.set()
            assert go.wait(WAIT)
            during = view(conn)  # the same read transaction, after the switch
            conn.execute("COMMIT")
            after = view(conn)  # a new transaction on the connection opened before the switch
        out.put({"pinned": pinned, "during": during, "after": after})
    except BaseException as error:  # report, so the parent fails with the cause
        ready.set()
        out.put({"error": repr(error)})


def test_a_reader_of_the_previous_generation_sees_no_mixed_data_while_the_import_publishes(store):
    target, sha = store
    previous = _selected(target)
    before = _sha(previous)
    ready, go, out = SPAWN.Event(), SPAWN.Event(), SPAWN.Queue()
    reader = SPAWN.Process(target=reader_across_publication, args=(str(target.selector), ready, go, out))
    reader.start()
    try:
        assert ready.wait(WAIT)
        _, published = _import(target, sha)  # the reader keeps its connection open throughout
        go.set()
        seen = out.get(timeout=WAIT)
    finally:
        reader.join(WAIT)
    assert "error" not in seen, seen
    assert seen["pinned"][0] == [] and seen["pinned"][3] == 0  # the previous generation has no mirror rows
    assert seen["during"] == seen["pinned"] and seen["after"] == seen["pinned"]  # whole and unchanged
    assert _selected(target) == published and _sha(previous) == before
    with closing(open_readonly(target.selector)) as fresh:  # a new opener gets the new generation, whole
        assert len(sum20_mirror.served_rows(fresh, "берег")) == 1
        assert importer.official_digest(fresh) == seen["pinned"][1]


def test_import_refuses_a_busy_lock_a_pre_bootstrap_store_and_a_writable_generation(store, tmp_path):
    target, sha = store
    previous = _selected(target)
    with generations.writer_lock(target.selector):  # another writer holds the lock: refused, never waited for
        with pytest.raises(importer.Refused, match="writer_lock_busy"):
            importer.run_import(target, sha)
    generations.lift_database(previous)
    try:
        with pytest.raises(importer.Refused, match="current_generation_writable"):
            importer.run_import(target, sha)
    finally:
        generations.hold_database(previous)
    assert _selected(target) == previous and not _leftovers(target)

    legacy = tmp_path / "legacy" / "data"  # before the operator's bootstrap the store is one regular file
    _make_live(legacy / "sources.db")
    _make_staging(legacy / "sum20_slovnyk_staging.db")
    with pytest.raises(importer.Refused, match="import_requires_selector"):
        importer.run_import(importer.writer_target(test_data_dir=legacy), sha)
    assert (legacy / "sources.db").is_file() and not (legacy / "sources.db").is_symlink()


def test_staging_must_match_the_admitted_digest_and_hold_no_wal_frames(store):
    target, sha = store
    with pytest.raises(importer.Refused, match="staging_digest_mismatch"):
        _import(target, "0" * 64)
    conn = sqlite3.connect(target.staging)
    try:
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("UPDATE sum20_slovnyk_articles SET text = 'changed in the WAL only' WHERE lemma = 'берег'")
        conn.commit()  # committed, but only in the WAL: the main file and its digest are unchanged
        assert _sha(target.staging) == sha
        with pytest.raises(importer.Refused, match="staging_not_checkpointed"):
            _import(target, sha)
    finally:
        conn.close()
    assert not _leftovers(target)


def test_incomplete_staging_is_refused(store):
    target, _ = store
    target.staging.unlink()
    _make_staging(target.staging, MIRROR[:2])
    with closing(sqlite3.connect(target.staging)) as conn:
        conn.execute("UPDATE sum20_slovnyk_checkpoint SET completed_count = 1")
        conn.commit()
    with pytest.raises(importer.Refused, match="staging_incomplete"):
        _import(target, _sha(target.staging))


def test_import_refuses_a_generation_changed_since_the_copy(store, monkeypatch):
    target, sha = store
    previous = _selected(target)
    real_verify = importer.verify

    def write_behind_the_lock(*args):
        generations.lift_database(previous)  # a writer that bypasses the lock (e.g. by mode bits)
        with closing(sqlite3.connect(previous)) as conn:
            conn.execute("INSERT INTO textbooks (text) VALUES ('a later write')")
            conn.commit()
        generations.hold_database(previous)
        return real_verify(*args)

    monkeypatch.setattr(importer, "verify", write_behind_the_lock)
    with pytest.raises(importer.Refused, match="current_generation_changed"):
        importer.run_import(target, sha)
    assert _selected(target) == previous and not _leftovers(target)


def test_writer_refuses_a_linked_worktree(tmp_path, monkeypatch):
    monkeypatch.setattr(importer, "main_checkout_root", lambda root: tmp_path / "primary")
    (tmp_path / "linked" / "scripts").mkdir(parents=True)
    (tmp_path / "linked" / "data").mkdir()
    with pytest.raises(importer.Refused, match="linked_worktree"):
        importer.writer_target(tmp_path / "linked")


def test_cli_reports_refusals_path_free(store, capsys):
    target, sha = store
    argv = ["import", "--expect-staging-sha256", "0" * 64]
    assert importer.main(argv, test_data_dir=target.data_dir) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "refused", "reason": "staging_digest_mismatch"}
    with generations.writer_lock(target.selector):
        assert importer.main(["import", "--expect-staging-sha256", sha], test_data_dir=target.data_dir) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "refused", "reason": "writer_lock_busy"}
    assert importer.main(["import", "--expect-staging-sha256", sha], test_data_dir=target.data_dir) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "published"


def test_lexdata_official_rows_still_get_mirror_rows_from_sources(store, monkeypatch):
    target, sha = store
    _import(target, sha)
    lexdata = target.data_dir / "lexdata.db"
    with closing(sqlite3.connect(lexdata)) as conn:
        ensure_sum20_official_schema(conn)
        conn.execute(
            "INSERT INTO sum20_articles (wordid, normalized_lookup_key, headword, stressed_headword, article_html, "
            "article_text, official_url, fetched_at, content_sha256, parser_version) "
            "VALUES (30, 'берег', 'БЕРЕГ', 'БЕРЕГ', '', 'Different lexdata text.', 'u', 'f', 'd', ?)",
            (PARSER_VERSION,),
        )
        meta = {
            "singleton": 1,
            "generation": "fixture",
            "status": "published",
            "generation_schema_version": __import__("scripts.lexdata.schema", fromlist=["x"]).GENERATION_SCHEMA_VERSION,
            "normalizer_digest": transforms.normalizer_digest(transforms.DEFAULT_BINDING),
            "l1_transform_digests": json.dumps(generation.current_transform_digests(transforms.DEFAULT_BINDING)),
            **{
                key: "{}"
                for key in (
                    "input_manifest",
                    "transform_manifest",
                    "normalizer_manifest",
                    "store_fingerprints",
                    "diff_receipt",
                )
            },
        }
        conn.execute("CREATE TABLE meta (" + ", ".join(meta) + ")")
        conn.execute("INSERT INTO meta VALUES (" + ", ".join("?" for _ in meta) + ")", tuple(meta.values()))
        conn.commit()

    records = _query("берег")
    assert [(r["source_role"], r.get("official_relation")) for r in records] == [
        ("official", None),
        ("mirror", "differs_from_official"),
    ]  # judged against the lexdata official row

    monkeypatch.setenv("LU_LEXDATA_DB", str(lexdata))  # an explicit override is exclusive
    assert [r["source_role"] for r in _query("берег")] == ["official"]

    monkeypatch.delenv("LU_LEXDATA_DB")
    target.selector.unlink()  # no sources store at all
    assert [r["source_role"] for r in _query("берег")] == ["official"]  # the official answer survives
    monkeypatch.setenv("LU_SOURCES_DB", str(target.selector))  # an explicit override that names nothing still refuses
    with pytest.raises(Sum20StoreError):
        _query("берег")


def test_stores_without_mirror_tables_serve_no_mirror_rows(store):
    target, _ = store
    with closing(open_readonly(target.selector)) as conn:
        assert sum20_mirror.served_rows(conn, "берег") == []
    assert generations.is_held(_selected(target))


def test_a_failed_staging_snapshot_removes_its_partial_file(store, monkeypatch):
    target, sha = store
    previous = _selected(target)

    def disk_full(fd):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(importer.os, "fsync", disk_full)
    with pytest.raises(OSError):
        importer.run_import(target, sha)
    assert _selected(target) == previous and not _leftovers(target)


def test_an_error_after_the_selector_switch_is_reported_as_published(store, monkeypatch, capsys):
    target, sha = store
    previous = _selected(target)
    real_complete = generations._complete_receipt
    calls = []

    def fail_after_the_switch(generation):
        calls.append(generation)
        if len(calls) > 1:  # the publisher's first call completes the previous receipt, before the switch
            raise generations.GenerationError("receipt_write_failed")
        real_complete(generation)

    monkeypatch.setattr(generations, "_complete_receipt", fail_after_the_switch)
    assert importer.main(["import", "--expect-staging-sha256", sha], test_data_dir=target.data_dir) == 3
    report = json.loads(capsys.readouterr().out)
    selected = _selected(target)
    assert selected != previous and not _leftovers(target)
    assert report == {
        "status": "published_post_switch_failed",
        "reason": "receipt_write_failed",
        "generation": selected.name,
        "previous": previous.name,
    }
