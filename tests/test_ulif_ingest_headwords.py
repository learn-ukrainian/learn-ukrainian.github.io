"""Cached relation-first entry regression and bounded headword repair (#9338)."""

import gzip
import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.runner import fetch_ulif_homonyms as runner
from scripts.lexicon.runner.ulif_dictua_parse import parse_ulif_entry
from scripts.wiki.sources_db import store_ulif_dictua_entry

FIXTURES = Path(__file__).parent / "fixtures" / "ulif_dictua"
CAPTURE_HASHES = {
    "synonyms": "e5a00511a7058dee620965e97c678582e3f656dc1ce575bd75166758d7798145",
    "paradigm": "ab69869953a93e36df6cc77d62f073544bcbf54e3bbda587ac0e390ee2fce9d7",
}


def _capture(kind):
    body = gzip.decompress((FIXTURES / f"ulif-entry-22798-{kind}.html.gz").read_bytes())
    assert hashlib.sha256(body).hexdigest() == CAPTURE_HASHES[kind]
    return body.decode("utf-8")


@pytest.fixture
def cached_group(tmp_path):
    db = tmp_path / "sources.db"
    conn = runner.prepare_database(db)
    ledger = runner.SpellingLedger(tmp_path / "state" / "ledger.sqlite")
    ledger.set_meta("mode", "walk")
    ledger.ensure_row(427, 21, select_arg="Select$21", stressed_headword="ба́чити", normalized_spelling="бачити")
    ledger.mark_row(427, 21, "completed", entry_sha256=CAPTURE_HASHES["synonyms"])
    for role, kind in [("entry", "synonyms"), ("tab", "paradigm"), ("tab", "synonyms")]:
        html = _capture(kind)
        ulif_raw_cache.put(CAPTURE_HASHES[kind], html.encode(), path=ulif_raw_cache.cache_path(db))
        ledger.record_response(
            spelling="бачити",
            role=role,
            tab_kind=kind if role == "tab" else "",
            response_sha256=CAPTURE_HASHES[kind],
            request_sha256="",
            homonym_index=1,
            register_position="427:21",
        )
    old = parse_ulif_entry(_capture("synonyms"), homonym_index=1, register_position="427:21")
    assert old["canonical_headword"] == ""
    store_ulif_dictua_entry(
        word="бачити",
        canonical_headword="",
        sections={"synonyms": [{"text": "synthetic retained section"}]},
        raw_responses={"paradigm": _capture("paradigm"), "synonyms": _capture("synonyms")},
        retrieved_at="captured",
        parser_version=runner.ULIF_PARSER_VERSION,
        status="ok",
        register_position="427:21",
        homonym_checked=1,
        content_sha256=old["content_sha256"],
        conn=conn,
        db_path=db,
    )
    # Unrelated rows must survive the bounded replay unchanged.
    store_ulif_dictua_entry(
        word="дуже",
        canonical_headword="ду́же",
        sections={},
        raw_responses={},
        retrieved_at="untouched",
        parser_version="untouched",
        status="ok",
        conn=conn,
        db_path=db,
    )
    conn.commit()
    try:
        yield ledger, conn
    finally:
        conn.close()
        ledger.close()


@pytest.mark.parametrize("walk_commit", [False, True])
def test_relation_first_capture_ingests_paradigm_identity(cached_group, walk_commit):
    ledger, conn = cached_group
    entry_id = conn.execute("SELECT id FROM ulif_dictua_entries WHERE normalized_query='бачити'").fetchone()[0]
    provenance_sql = "SELECT retrieved_at, raw_response_ref, response_sha256 FROM ulif_dictua_entries WHERE id=?"
    provenance_before = tuple(conn.execute(provenance_sql, (entry_id,)).fetchone())
    sections_sql = "SELECT * FROM ulif_dictua_sections WHERE entry_id=? ORDER BY id"
    sections_before = [tuple(row) for row in conn.execute(sections_sql, (entry_id,))]
    if walk_commit:
        runner._commit_spelling_group(ledger, conn, "бачити")
    else:
        ledger.ensure("бачити")
        ledger.mark("бачити", "stored", entry_count=1)
        assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 1
    recovered = conn.execute(
        "SELECT id, canonical_headword, grammatical_label, homonym_index, register_position, homonym_checked, status "
        "FROM ulif_dictua_entries WHERE normalized_query='бачити'"
    ).fetchone()
    assert tuple(recovered) == (entry_id, "ба́чити", "дієслово недоконаного виду", 1, "427:21", 1, "ok")
    untouched = conn.execute(
        "SELECT canonical_headword, retrieved_at, parser_version FROM ulif_dictua_entries WHERE normalized_query='дуже'"
    ).fetchone()
    assert tuple(untouched) == ("ду́же", "untouched", "untouched")
    assert {r[0] for r in conn.execute("SELECT kind FROM ulif_dictua_sections")} == (
        {"paradigm", "synonyms"} if walk_commit else {"synonyms"}
    )
    if not walk_commit:
        assert tuple(conn.execute(provenance_sql, (entry_id,)).fetchone()) == provenance_before
        assert [tuple(row) for row in conn.execute(sections_sql, (entry_id,))] == sections_before
        assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 0
    assert conn.execute("SELECT count(*) FROM ulif_dictua_entries").fetchone()[0] == 2


def test_bounded_replay_requires_stored_ledger_unit(cached_group):
    ledger, conn = cached_group
    with pytest.raises(ValueError, match="lack a stored ledger unit"):
        runner.parse_stored(ledger, conn, empty_headwords_only=True)


def test_bounded_replay_refuses_group_membership_change(cached_group):
    ledger, conn = cached_group
    ledger.ensure("бачити")
    ledger.mark("бачити", "stored", entry_count=1)
    conn.execute("UPDATE ulif_dictua_entries SET register_position='other' WHERE normalized_query='бачити'")
    conn.commit()
    with pytest.raises(ValueError, match="refusing to change group membership"):
        runner.parse_stored(ledger, conn, empty_headwords_only=True)
    assert (
        conn.execute("SELECT canonical_headword FROM ulif_dictua_entries WHERE normalized_query='бачити'").fetchone()[0]
        == ""
    )


def test_paradigm_identity_mismatch_fails_closed():
    with pytest.raises(ValueError, match="cached identity mismatch"):
        runner._parse_cached_entry(
            _capture("synonyms"),
            {"paradigm": _capture("paradigm")},
            spelling="дуже",
            homonym_index=1,
            register_position="427:21",
            stressed_headword="ду́же",
        )


@pytest.mark.parametrize("walk_commit", [False, True])
def test_same_spelling_different_stress_fails_closed(cached_group, walk_commit):
    ledger, conn = cached_group
    ledger.conn.execute("UPDATE register_rows SET stressed_headword='бачи́ти'")
    ledger.conn.commit()
    ledger.ensure("бачити")
    ledger.mark("бачити", "stored", entry_count=1)
    with pytest.raises(ValueError, match="cached identity mismatch"):
        if walk_commit:
            # The stored shortcut applies only once homonym indexes are populated.
            runner._commit_spelling_group(ledger, conn, "бачити")
        else:
            runner.parse_stored(ledger, conn, empty_headwords_only=True)
    assert (
        conn.execute("SELECT canonical_headword FROM ulif_dictua_entries WHERE normalized_query='бачити'").fetchone()[0]
        == ""
    )


def test_repair_preserves_global_content_metadata(cached_group):
    ledger, conn = cached_group
    ledger.ensure("бачити")
    ledger.mark("бачити", "stored", entry_count=1)
    ledger.set_meta("differing_content_hashes", "12345")
    ledger.set_duplicate_content("бачити", True)
    assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 1
    assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 0
    assert ledger.meta("differing_content_hashes") == "12345"
    assert ledger.conn.execute("SELECT duplicate_content FROM spellings WHERE spelling='бачити'").fetchone()[0] == 1


@pytest.mark.parametrize("initial_error", [False, True])
@pytest.mark.parametrize("other_headword", ["ба́чити", "бачи́ти", "Ба́чити", ""])
def test_mismatch_repair_identity_and_second_run(cached_group, monkeypatch, capsys, initial_error, other_headword):
    ledger, conn = cached_group
    ledger.ensure_row(427, 22, select_arg="Select$22", stressed_headword=other_headword, normalized_spelling="бачити")
    ledger.mark_row(427, 22, "completed", entry_sha256=CAPTURE_HASHES["synonyms"])
    for role, kind in [("entry", "synonyms"), ("tab", "paradigm")]:
        ledger.record_response(
            spelling="бачити",
            role=role,
            tab_kind=kind if role == "tab" else "",
            response_sha256=CAPTURE_HASHES[kind],
            request_sha256="",
            homonym_index=2,
            register_position="427:22",
        )
    store_ulif_dictua_entry(
        word="бачити",
        canonical_headword="",
        homonym_index=2,
        sections={},
        raw_responses={},
        retrieved_at="second",
        parser_version="previous",
        status="ok",
        register_position="427:22",
        conn=conn,
        db_path=runner._db_path(conn),
    )
    conn.commit()
    ledger.ensure("бачити")
    error = "printed_number_mismatch register=[1, 2] printed=[2, 1]"
    ledger.mark("бачити", "error" if initial_error else "stored", entry_count=2, error=error if initial_error else "")
    if not initial_error:
        # Drive the mismatch path independently of the HTML printed-number parser.
        monkeypatch.setattr(runner, "_printed_number_mismatch", lambda rows: ([1, 2], [2, 1]))
        # Keep each cached tab bound to its own register identity before the group check.
        original = runner._parse_cached_entry

        def parse(html, raw, **kwargs):
            kwargs["stressed_headword"] = "ба́чити"
            return original(html, raw, **kwargs)

        monkeypatch.setattr(runner, "_parse_cached_entry", parse)
    before = [tuple(row) for row in conn.execute("SELECT * FROM ulif_dictua_entries ORDER BY id")]
    assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 1
    rows = conn.execute(
        "SELECT canonical_headword, status FROM ulif_dictua_entries WHERE normalized_query='бачити' ORDER BY homonym_index"
    ).fetchall()
    expected = ("ба́чити", "ok") if other_headword == "ба́чити" else ("", "parse_error")
    assert [tuple(row) for row in rows] == [expected, expected]
    after = [tuple(row) for row in conn.execute("SELECT * FROM ulif_dictua_entries ORDER BY id")]
    # Only headword, parser version and status may change; ordering and provenance stay intact.
    for old, new in zip(before, after, strict=True):
        assert tuple(value for i, value in enumerate(old) if i not in {3, 12, 13}) == tuple(
            value for i, value in enumerate(new) if i not in {3, 12, 13}
        )
    assert ledger.meta("headword_repair_reason:бачити")
    cache_changes, ledger_changes = conn.total_changes, ledger.conn.total_changes
    assert runner.parse_stored(ledger, conn, empty_headwords_only=True) == 0
    assert conn.total_changes == cache_changes
    assert ledger.conn.total_changes == ledger_changes
    assert "residual: бачити: printed_number_mismatch" in capsys.readouterr().out
    assert (
        conn.execute(
            "SELECT count(*) FROM ulif_dictua_entries WHERE status='ok' AND trim(canonical_headword)=''"
        ).fetchone()[0]
        == 0
    )


def test_mismatch_repair_refuses_group_membership_change(cached_group):
    ledger, conn = cached_group
    ledger.ensure("бачити")
    ledger.mark("бачити", "error", entry_count=1, error="printed_number_mismatch register=[1] printed=[2]")
    conn.execute("UPDATE ulif_dictua_entries SET register_position='other' WHERE normalized_query='бачити'")
    with pytest.raises(ValueError, match="refusing to change group membership"):
        runner.parse_stored(ledger, conn, empty_headwords_only=True)


def test_no_paradigm_preserves_entry_identity():
    html = (FIXTURES / "duzhe.html").read_text()
    parsed = runner._parse_cached_entry(html, {}, spelling="дуже", homonym_index=1, register_position="1:0")
    assert parsed["canonical_headword"] == "ду́же"


def test_existing_entry_identity_is_preserved_when_tab_differs():
    html = (FIXTURES / "duzhe.html").read_text()
    parsed = runner._parse_cached_entry(
        html, {"paradigm": _capture("paradigm")}, spelling="дуже", homonym_index=1, register_position="1:0"
    )
    assert parsed["canonical_headword"] == "ду́же"


def test_identity_repair_rolls_back_on_upsert_failure(cached_group):
    _ledger, conn = cached_group
    store_ulif_dictua_entry(
        word="бачити",
        canonical_headword="",
        homonym_index=2,
        sections={},
        raw_responses={},
        retrieved_at="synthetic",
        parser_version="synthetic",
        status="ok",
        register_position="427:22",
        conn=conn,
        db_path=runner._db_path(conn),
    )
    conn.commit()
    conn.execute(
        "CREATE TRIGGER fail_second_repair BEFORE UPDATE ON ulif_dictua_entries "
        "WHEN new.homonym_index = 2 BEGIN SELECT RAISE(ABORT, 'injected repair failure'); END"
    )
    conn.commit()
    parsed = [
        parse_ulif_entry(_capture("paradigm"), homonym_index=index, register_position=f"427:{20 + index}")
        for index in (1, 2)
    ]
    with pytest.raises(sqlite3.IntegrityError, match="injected repair failure"):
        runner._repair_group_identity(conn, "бачити", parsed)
    assert [
        row[0]
        for row in conn.execute(
            "SELECT canonical_headword FROM ulif_dictua_entries WHERE normalized_query='бачити' ORDER BY homonym_index"
        )
    ] == ["", ""]


def test_missing_identity_cannot_be_written_as_ok(tmp_path):
    conn = runner.prepare_database(tmp_path / "sources.db")
    parsed = parse_ulif_entry(_capture("synonyms"), homonym_index=1)
    try:
        for _ in range(2):
            runner._write_group(conn, "бачити", [parsed], [{}], [{}], store_ulif_dictua_entry)
            assert conn.execute("SELECT status FROM ulif_dictua_entries").fetchone()[0] == "parse_error"
    finally:
        conn.close()


def test_parse_help_documents_bounded_replay(capsys):
    with pytest.raises(SystemExit) as exc:
        runner.main(["parse", "--help"])
    assert exc.value.code == 0
    assert "--empty-headwords-only" in capsys.readouterr().out
