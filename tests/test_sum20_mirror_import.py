"""СУМ-20 mirror import: rule sum20-mirror-rule-v1, reader routing and the generation writer (#8579).

Every article here is synthetic fixture text, not dictionary content.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts.atlas import word_card_sources as src
from scripts.ingest import sum20_mirror_import as importer
from scripts.lexdata import generation, transforms
from scripts.lexicon import sum20_lookup
from scripts.wiki import sources_db, sum20_mirror
from scripts.wiki.sum20_official import PARSER_VERSION, ensure_sum20_official_schema, normalize_sum20_lookup

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


def _observed(holders=(), locks=()):
    return {"holders": list(holders), "locks": list(locks), "unscannable": []}


def _no_holders(paths):
    return _observed()


def _options(**overrides):
    options = {
        "scan": _no_holders,
        "control": lambda action, unit: None,
        "drain_units": [],
        "wait_drained": 0.0,
        "sleep": lambda s: None,
    }
    options.update(overrides)
    return options


READER = {"pid": 8, "writable": False, "files": ["sources.db"], "command": "python"}
WRITER = {"pid": 7, "writable": True, "files": ["sources.db"], "command": "python"}
UNKNOWN = {"pid": 9, "writable": None, "files": ["sources.db"], "command": "python"}
READ_LOCK = {"pid": 4, "access": "READ", "file": "sources.db-shm"}
WRITE_LOCK = {"pid": 5, "access": "WRITE", "file": "sources.db-shm"}


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A fixture repository with a held live store and a complete staged mirror."""
    for name in ("LEXDATA_DB_PATH", "LU_LEXDATA_DB", "LU_SOURCES_DB", "SOURCES_DB_PATH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(sources_db, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sum20_lookup, "REPO_ROOT", tmp_path)
    data = tmp_path / "data"
    _make_live(data / "sources.db")
    sha = _make_staging(data / "sum20_slovnyk_staging.db")
    target = importer.writer_target(test_data_dir=data)
    return target, sha


def _build(target, sha):
    return importer.build(target, sha, scan=_no_holders)


def _query(word, db=None):
    return sources_db.query_sum20(word, db_path=db)


def test_build_leaves_live_untouched_and_verifies_the_rule(store):
    target, sha = store
    before = _sha(target.live)
    receipt = _build(target, sha)

    assert _sha(target.live) == before
    assert receipt["state"] == "candidate"
    assert receipt["verification"]["relation_counts"] == {
        "mirror_only": 2,
        "agrees_with_official": 1,
        "official_quarantined": 1,
        "differs_from_official": 1,
    }
    assert receipt["reconcile_differing"] == 2  # ліс and the quarantined дух; вода matches
    candidate = target.candidate(receipt["generation"])
    assert candidate.stat().st_mode & 0o777 == 0o444
    assert not any(path.exists() for path in importer._sidecars(candidate))
    assert not list(target.work_dir.glob("staging.*"))


def test_rule_serves_official_first_and_flags_every_mirror_row(store):
    target, sha = store
    candidate = target.candidate(_build(target, sha)["generation"])

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
    candidate = target.candidate(_build(target, sha)["generation"])
    for word in ("вода", "ліс", "дух"):
        assert [r for r in _query(word, candidate) if r["source_role"] == "official"] == _query(word, target.live)
    with (
        closing(sqlite3.connect(f"file:{candidate}?mode=ro", uri=True)) as new,
        closing(sqlite3.connect(f"file:{target.live}?mode=ro", uri=True)) as old,
    ):
        assert importer.official_digest(new) == importer.official_digest(old)
        quarantined = new.execute("SELECT wordid FROM sum20_articles WHERE quarantine_reason != ''").fetchall()
    assert quarantined == [(11,)]


def test_rule_is_judged_at_read_time_against_a_later_official_row(store):
    target, sha = store
    candidate = target.candidate(_build(target, sha)["generation"])
    candidate.chmod(0o644)
    with closing(sqlite3.connect(candidate)) as conn:  # an official ingest later adds the mirror-only key
        conn.execute(
            "INSERT INTO sum20_articles (wordid, normalized_lookup_key, headword, stressed_headword, article_html, "
            "article_text, definition_text, official_url, fetched_at, content_sha256, parser_version) "
            "VALUES (20, 'берег', 'БЕРЕГ', 'БЕРЕГ', '', 'БЕ́РЕГ, а, ч. Synthetic mirror-only sense.', '', "
            "'https://official.example/?wordid=20', 'fixture', 'digest-20', ?)",
            (PARSER_VERSION,),
        )
        conn.commit()
    assert [r["source_role"] for r in _query("берег", candidate)] == ["official"]


def test_publish_retains_the_previous_generation_and_restore_brings_it_back(store):
    target, sha = store
    old_sha, old_ino = _sha(target.live), target.live.stat().st_ino
    built = _build(target, sha)

    published = importer.publish(target, built["generation"], _options())
    assert published["status"] == "published" and published["unit_restart_errors"] == []
    assert _sha(target.live) == built["sha256"]
    assert target.live.stat().st_mode & 0o777 == 0o444  # the hold survives the swap
    backup = target.backup(published["previous"])
    assert backup.stat().st_ino == old_ino and _sha(backup) == old_sha  # the old inode itself, no copy
    assert backup.stat().st_mode & 0o777 == 0o444  # unfenced after the rename
    assert not importer._journal(target).exists()
    assert json.loads(target.receipt(built["generation"]).read_text())["state"] == "published"
    assert _query("берег")[0]["source_role"] == "mirror"  # default selection reads the new generation
    listing = {row["generation"]: row for row in importer.generations(target)["generations"]}
    assert listing[built["generation"]]["live"] and listing[published["previous"]]["restorable"]

    restored = importer.restore(target, published["previous"], _options())
    assert restored["status"] == "restored" and _sha(target.live) == old_sha
    assert _sha(backup) == old_sha  # restoring copies; the retained generation stays pristine
    assert _query("берег") == []
    again = importer.restore(target, built["generation"], _options())  # the published one was retained too
    assert again["status"] == "restored" and _sha(target.live) == built["sha256"]


def test_drain_restarts_every_unit_and_reports_restart_failures_apart(store, capsys):
    target, sha = store
    built = _build(target, sha)
    calls = []

    def control(action, unit):
        calls.append((action, unit))
        if (action, unit) == ("start", "b.service"):
            raise TimeoutError("fixture")

    published = importer.publish(
        target, built["generation"], _options(drain_units=["a.service", "b.service"], control=control)
    )
    assert calls == [("stop", "a.service"), ("stop", "b.service"), ("start", "b.service"), ("start", "a.service")]
    assert published["status"] == "published"  # the swap committed and says so
    assert published["unit_restart_errors"] == ["start b.service: TimeoutError"]
    assert json.loads(target.receipt(built["generation"]).read_text())["state"] == "published"


def test_a_unit_stop_failure_refuses_and_still_starts_every_unit(store):
    target, sha = store
    built = _build(target, sha)
    before, calls = _sha(target.live), []

    def control(action, unit):
        calls.append((action, unit))
        if (action, unit) == ("stop", "b.service"):
            raise TimeoutError("fixture")

    with pytest.raises(importer.Refused, match="unit_stop_failed") as exc:
        importer.publish(target, built["generation"], _options(drain_units=["a.service", "b.service"], control=control))
    assert calls[-2:] == [("start", "b.service"), ("start", "a.service")]
    assert exc.value.detail["unit_errors"] == ["stop b.service: TimeoutError"]
    assert _sha(target.live) == before


@pytest.mark.parametrize(
    "observed",
    [_observed([WRITER]), _observed([READER]), _observed([UNKNOWN]), _observed(locks=[READ_LOCK])],
    ids=["writer", "reader", "unknown-access", "lock-only"],
)
def test_publication_needs_a_full_drain(store, observed):
    target, sha = store
    built = _build(target, sha)
    before = _sha(target.live)
    with pytest.raises(importer.Refused, match="live_store_in_use") as exc:
        importer.publish(
            target,
            built["generation"],
            _options(scan=lambda paths: observed, wait_drained=10.0, clock=iter(range(0, 100, 5)).__next__),
        )
    assert exc.value.detail == {"holders": observed["holders"], "locks": observed["locks"]}
    assert _sha(target.live) == before and not list(target.backups_dir.glob("*.db"))


def test_publication_waits_for_readers_to_leave(store):
    target, sha = store
    built = _build(target, sha)
    scans, slept = iter([_observed([READER]), _observed(locks=[READ_LOCK])]), []
    scan = lambda paths: next(scans, _observed())  # noqa: E731
    published = importer.publish(
        target, built["generation"], _options(scan=scan, wait_drained=60.0, sleep=slept.append)
    )
    assert published["status"] == "published" and slept == [importer.DRAIN_POLL_S] * 2


def test_an_open_after_the_fence_rolls_the_publication_back(store, monkeypatch):
    target, sha = store
    built = _build(target, sha)
    before, old_ino = _sha(target.live), target.live.stat().st_ino
    calls = iter([_observed(), _observed(), _observed([READER])])  # the final barrier sees a late reader
    with pytest.raises(importer.Refused, match="live_store_in_use"):
        importer.publish(target, built["generation"], _options(scan=lambda paths: next(calls)))
    assert target.live.stat().st_ino == old_ino and _sha(target.live) == before
    assert target.live.stat().st_mode & 0o777 == 0o444  # unfenced
    assert all(p.stat().st_ino != old_ino for p in target.backups_dir.glob("*.db"))  # no backup aliases live
    assert not importer._journal(target).exists()
    assert target.candidate(built["generation"]).is_file()


def _crash_before_rename(target, built):
    """The state a killed process leaves after the journal, link and fence but before the rename."""
    parent = json.loads(target.receipt(built["generation"]).read_text())
    previous = importer.generation_id(parent["parent_sha256"])
    importer._write_json(
        importer._journal(target),
        {
            "previous": previous,
            "previous_sha256": parent["parent_sha256"],
            "old_ino": target.live.stat().st_ino,
            "old_mode": 0o444,
            "kind": "retained_before_import",
            "published": built["generation"],
        },
    )
    target.backups_dir.mkdir(parents=True, exist_ok=True)
    os.link(target.live, target.backup(previous))
    target.live.chmod(0)
    return previous


def test_recovery_undoes_a_publication_killed_before_the_rename(store):
    target, sha = store
    built = _build(target, sha)
    old_ino = target.live.stat().st_ino
    previous = _crash_before_rename(target, built)

    listing = importer.generations(target)
    assert listing["recovered_first"] == {"recovered": "rolled_back", "previous": previous}
    assert target.live.stat().st_ino == old_ino and target.live.stat().st_mode & 0o777 == 0o444
    assert not target.backup(previous).exists()  # the alias of the live inode is gone
    assert importer.publish(target, built["generation"], _options())["status"] == "published"


def test_recovery_finishes_a_publication_killed_after_the_rename(store):
    target, sha = store
    built = _build(target, sha)
    old_ino = target.live.stat().st_ino
    previous = _crash_before_rename(target, built)
    os.replace(target.candidate(built["generation"]), target.live)

    assert importer.generations(target)["recovered_first"] == {"recovered": "rolled_forward", "previous": previous}
    backup = target.backup(previous)
    assert backup.stat().st_ino == old_ino and backup.stat().st_mode & 0o777 == 0o444
    assert json.loads(target.receipt(built["generation"]).read_text())["state"] == "published"
    assert json.loads(target.receipt(previous).read_text())["state"] == "retained"


def test_build_refuses_writers_an_unheld_store_and_a_busy_wal(store):
    target, sha = store
    for observed in (_observed([WRITER]), _observed([UNKNOWN]), _observed(locks=[WRITE_LOCK])):
        with pytest.raises(importer.Refused, match="live_store_has_writers"):
            importer.build(target, sha, scan=lambda paths, observed=observed: observed)
    assert importer.build(target, sha, scan=lambda paths: _observed([READER], [READ_LOCK]))["state"] == "candidate"
    target.live.chmod(0o644)
    with pytest.raises(importer.Refused, match="live_store_not_held"):
        _build(target, sha)
    wal = Path(f"{target.live}-wal")
    wal.unlink(missing_ok=True)
    wal.write_bytes(b"frames")
    with pytest.raises(importer.Refused, match="live_store_not_checkpointed"):
        _build(target, sha)


def test_staging_must_match_the_admitted_digest_and_hold_no_wal_frames(store):
    target, sha = store
    with pytest.raises(importer.Refused, match="staging_digest_mismatch"):
        _build(target, "0" * 64)
    conn = sqlite3.connect(target.staging)
    try:
        conn.execute("PRAGMA wal_autocheckpoint=0")
        conn.execute("UPDATE sum20_slovnyk_articles SET text = 'changed in the WAL only' WHERE lemma = 'берег'")
        conn.commit()  # committed, but only in the WAL: the main file and its digest are unchanged
        assert _sha(target.staging) == sha
        with pytest.raises(importer.Refused, match="staging_not_checkpointed"):
            _build(target, sha)
    finally:
        conn.close()


def test_incomplete_staging_is_refused(store):
    target, _ = store
    target.staging.unlink()
    _make_staging(target.staging, MIRROR[:2])
    with closing(sqlite3.connect(target.staging)) as conn:
        conn.execute("UPDATE sum20_slovnyk_checkpoint SET completed_count = 1")
        conn.commit()
    with pytest.raises(importer.Refused, match="staging_incomplete"):
        _build(target, _sha(target.staging))


def test_publish_refuses_a_live_store_changed_since_the_candidate(store):
    target, sha = store
    built = _build(target, sha)
    for part in [target.live, *importer._sidecars(target.live)]:  # lift the hold, write, hold again
        if part.exists():
            part.chmod(0o644)
    with closing(sqlite3.connect(target.live)) as conn:
        conn.execute("INSERT INTO textbooks (text) VALUES ('a later write')")
        conn.commit()
    for part in [target.live, *importer._sidecars(target.live)]:
        if part.exists():
            part.chmod(0o444)
    with pytest.raises(importer.Refused, match="live_store_changed_since_candidate"):
        importer.publish(target, built["generation"], _options())
    assert importer.generations(target)["generations"]


def test_writer_refuses_a_linked_worktree(tmp_path, monkeypatch):
    monkeypatch.setattr(importer, "main_checkout_root", lambda root: tmp_path / "primary")
    (tmp_path / "linked" / "scripts").mkdir(parents=True)
    (tmp_path / "linked" / "data").mkdir()
    with pytest.raises(importer.Refused, match="linked_worktree"):
        importer.writer_target(tmp_path / "linked")


def test_cli_reports_refusals_path_free_and_exit_3_for_a_failed_restart(store, capsys, monkeypatch):
    target, sha = store
    assert importer.main(["publish", "--generation", "missing"], test_data_dir=target.data_dir) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "refused", "reason": "candidate_unknown"}
    built = _build(target, sha)

    def failing_start(action, unit):
        if action == "start":
            raise TimeoutError("fixture")

    monkeypatch.setattr(importer, "holders", _no_holders)
    monkeypatch.setattr(importer, "systemctl", failing_start)
    argv = ["publish", "--generation", built["generation"], "--drain-unit", "a.service"]
    assert importer.main(argv, test_data_dir=target.data_dir) == 3
    assert json.loads(capsys.readouterr().out)["status"] == "published"


def test_holders_scan_matches_inodes_access_mode_locks_and_unscannable(tmp_path):
    db = tmp_path / "sources.db"
    db.write_bytes(b"x")
    info = db.stat()
    proc = tmp_path / "proc"
    for pid, flags in (("101", "0100000"), ("102", "0100002"), ("103", None)):
        (proc / pid / "fd").mkdir(parents=True)
        (proc / pid / "fdinfo").mkdir()
        (proc / pid / "fd" / "3").symlink_to(db)
        if flags is not None:
            (proc / pid / "fdinfo" / "3").write_text(f"pos:\t0\nflags:\t{flags}\n")
        else:  # a descriptor whose access mode cannot be read
            (proc / pid / "fdinfo" / "3").mkdir()
        (proc / pid / "comm").write_text("python\n")
    (proc / "104").mkdir()
    (proc / "104" / "comm").write_text("guarded\n")
    (proc / "104" / "fd").mkdir(mode=0)
    device = f"{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}"
    (proc / "locks").write_text(
        f"1: POSIX  ADVISORY  READ 105 {device} 1073741826 1073742335\n2: POSIX  ADVISORY  WRITE 106 00:00:1 0 EOF\n"
    )
    try:
        found = importer.holders([db, tmp_path / "sources.db-wal"], proc=proc)
    finally:
        (proc / "104" / "fd").chmod(0o755)
    assert [(h["pid"], h["writable"], h["files"]) for h in found["holders"]] == [
        (101, False, ["sources.db"]),
        (102, True, ["sources.db"]),
        (103, None, ["sources.db"]),
    ]
    assert found["locks"] == [{"pid": 105, "access": "READ", "file": "sources.db"}]
    if os.geteuid() != 0:  # root can list a mode-000 directory
        assert found["unscannable"] == [{"pid": 104, "command": "guarded"}]


def test_lexdata_official_rows_still_get_mirror_rows_from_sources(store, monkeypatch):
    target, sha = store
    importer.publish(target, _build(target, sha)["generation"], _options())
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
    for part in [target.live, *importer._sidecars(target.live)]:  # no sources store at all
        if part.exists():
            part.unlink()
    assert [r["source_role"] for r in _query("берег")] == ["official"]  # the official answer survives


def test_word_card_inventory_records_served_mirror_locators(store):
    target, sha = store
    candidate = target.candidate(_build(target, sha)["generation"])
    conn = sqlite3.connect(f"file:{candidate}?mode=ro", uri=True)
    try:
        sources = src.PilotSources(conn, conn, conn)
        assert sources.sum20_mirror_articles("берег") == [
            {
                "source_url": _url("берег"),
                "fetched_at": "2026-10-01T00:00:00+00:00",
                "content_sha256": hashlib.sha256(f"берег {MIRROR[0][2]}{FOOTER}".encode()).hexdigest(),
                "relation": "mirror_only",
            }
        ]
        assert sources.sum20_mirror_articles("вода") == []
        assert {"sum20_mirror_articles:берег", "sum20_mirror_articles:вода"} <= set(sources.consumed)
    finally:
        conn.close()


def test_stores_without_mirror_tables_serve_no_mirror_rows(store):
    target, _ = store
    with closing(sqlite3.connect(f"file:{target.live}?mode=ro", uri=True)) as conn:
        assert sum20_mirror.served_rows(conn, "берег") == []
    assert os.access(target.live, os.W_OK) is False
