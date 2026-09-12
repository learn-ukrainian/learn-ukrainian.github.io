"""Hermetic tests for VESUM inspection API (scripts/verification/vesum.py).

Tests:
- inspect_word across all InspectionStatus values (CLEAN, KNOWN_INVALID, NONSTANDARD,
  SLANG, ARCH_OR_DIALECT_UNRESOLVED, ORTHOGRAPHIC_VARIANT, VULGAR, MIXED, NOT_FOUND)
- inspect_words batch querying
- inspect_lemma paradigm querying
- Fail-closed UNAVAILABLE behavior on legacy schema and missing database
- Zero-regression compatibility of verify_word and verify_words on the new schema view
"""

from __future__ import annotations

import bz2
import json
import os
import sqlite3
import threading
from pathlib import Path

import pytest

from scripts.rag.vesum_reingest import build_shadow_database
from scripts.verification.vesum import (
    InspectionStatus,
    LemmaInspection,
    WordInspection,
    close_vesum_conn,
    get_vesum_conn,
    get_vesum_connection,
    inspect_lemma,
    inspect_word,
    inspect_words,
    verify_lemma,
    verify_word,
    verify_words,
)

SYNTHETIC_INSPECTION_BLOCKS = """\
clean noun:inanim:m:v_naz    # clean header
  clean-form noun:inanim:m:v_rod    # clean form
alternate adj:alt
archaic noun:arch
invalid noun:bad
  invalid-form noun:bad
nonstandard noun:subst
obscene noun:obsc
slangy noun:slang
vulgar noun:vulg
dialect-pure noun:inanim:m:v_naz    # діалект
  dialect-pure-form noun:inanim:m:v_rod
dialect-homograph noun:anim:m:v_naz
  dialect-homograph-form noun:anim:m:v_rod
dialect-homograph noun:inanim:m:v_naz    # діалект
  dialect-homograph-form noun:inanim:m:v_rod
mixed-paradigm noun:anim:m:v_naz
  mixed-modern noun:anim:m:v_rod
  mixed-archaic noun:anim:m:v_rod:arch
ortho-clean noun:inanim:m:v_naz
ortho-bad noun:inanim:m:v_naz:bad
"""


@pytest.fixture(scope="module")
def inspection_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_dir = tmp_path_factory.mktemp("vesum_inspection_test")
    asset_path = tmp_dir / "synthetic_inspection.txt.bz2"
    with bz2.open(asset_path, "wt", encoding="utf-8") as target:
        target.write(SYNTHETIC_INSPECTION_BLOCKS)
    db_path = tmp_dir / "inspection_shadow.db"
    build_shadow_database(asset_path, db_path)
    return db_path


def test_inspect_word_clean(inspection_db: Path) -> None:
    res = inspect_word("clean", db_path=inspection_db)
    assert isinstance(res, WordInspection)
    assert res.status == InspectionStatus.CLEAN
    assert len(res.clean_analyses) == 1
    assert len(res.marked_analyses) == 0
    assert res.clean_analyses[0]["lemma"] == "clean"
    assert res.clean_analyses[0]["pos"] == "noun"
    assert res.effective_markers == []
    assert len(res.source_locations) > 0


def test_inspect_word_known_invalid_bad(inspection_db: Path) -> None:
    res = inspect_word("invalid", db_path=inspection_db)
    assert res.status == InspectionStatus.KNOWN_INVALID
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["bad"]
    assert res.marked_analyses[0]["markers"] == [
        {"marker": "bad", "origin": "tag", "marker_class": "invalid"}
    ]


def test_inspect_word_known_invalid_obsc(inspection_db: Path) -> None:
    res = inspect_word("obscene", db_path=inspection_db)
    assert res.status == InspectionStatus.KNOWN_INVALID
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["obsc"]


def test_inspect_word_nonstandard_subst(inspection_db: Path) -> None:
    res = inspect_word("nonstandard", db_path=inspection_db)
    assert res.status == InspectionStatus.NONSTANDARD
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["subst"]


def test_inspect_word_slang(inspection_db: Path) -> None:
    res = inspect_word("slangy", db_path=inspection_db)
    assert res.status == InspectionStatus.SLANG
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["slang"]


def test_inspect_word_archaic(inspection_db: Path) -> None:
    res = inspect_word("archaic", db_path=inspection_db)
    assert res.status == InspectionStatus.ARCH_OR_DIALECT_UNRESOLVED
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["arch"]


def test_inspect_word_pure_dialect(inspection_db: Path) -> None:
    res = inspect_word("dialect-pure", db_path=inspection_db)
    assert res.status == InspectionStatus.ARCH_OR_DIALECT_UNRESOLVED
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["dialect"]
    assert res.marked_analyses[0]["markers"] == [
        {"marker": "dialect", "origin": "comment", "marker_class": "dialect"}
    ]


def test_inspect_word_orthographic_variant_alt(inspection_db: Path) -> None:
    res = inspect_word("alternate", db_path=inspection_db)
    assert res.status == InspectionStatus.ORTHOGRAPHIC_VARIANT
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["alt"]


def test_inspect_word_vulgar(inspection_db: Path) -> None:
    res = inspect_word("vulgar", db_path=inspection_db)
    assert res.status == InspectionStatus.VULGAR
    assert len(res.clean_analyses) == 0
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["vulg"]


def test_inspect_word_mixed_clean_and_dialect_homograph(inspection_db: Path) -> None:
    res = inspect_word("dialect-homograph", db_path=inspection_db)
    assert res.status == InspectionStatus.MIXED
    assert len(res.clean_analyses) == 1
    assert len(res.marked_analyses) == 1
    assert res.clean_analyses[0]["pos"] == "noun"
    assert res.marked_analyses[0]["markers"] == [
        {"marker": "dialect", "origin": "comment", "marker_class": "dialect"}
    ]
    assert res.effective_markers == ["dialect"]


def test_inspect_word_not_found(inspection_db: Path) -> None:
    res = inspect_word("nonexistent-word-xyz", db_path=inspection_db)
    assert res.status == InspectionStatus.NOT_FOUND
    assert res.clean_analyses == []
    assert res.marked_analyses == []
    assert res.effective_markers == []


def test_inspect_word_pos_filter(inspection_db: Path) -> None:
    matching = inspect_word("clean", pos_filter="noun", db_path=inspection_db)
    assert matching.status == InspectionStatus.CLEAN
    assert len(matching.clean_analyses) == 1

    mismatch = inspect_word("clean", pos_filter="verb", db_path=inspection_db)
    assert mismatch.status == InspectionStatus.NOT_FOUND
    assert mismatch.clean_analyses == []


def test_inspect_words_batch(inspection_db: Path) -> None:
    words = ["clean", "invalid", "nonstandard", "slangy", "nonexistent"]
    batch = inspect_words(words, db_path=inspection_db)

    assert set(batch.keys()) == set(words)
    assert batch["clean"].status == InspectionStatus.CLEAN
    assert batch["invalid"].status == InspectionStatus.KNOWN_INVALID
    assert batch["nonstandard"].status == InspectionStatus.NONSTANDARD
    assert batch["slangy"].status == InspectionStatus.SLANG
    assert batch["nonexistent"].status == InspectionStatus.NOT_FOUND


def test_inspect_words_empty(inspection_db: Path) -> None:
    assert inspect_words([], db_path=inspection_db) == {}


def test_inspect_lemma(inspection_db: Path) -> None:
    res = inspect_lemma("mixed-paradigm", db_path=inspection_db)
    assert isinstance(res, LemmaInspection)
    assert res.lemma == "mixed-paradigm"
    assert res.status == InspectionStatus.MIXED
    assert len(res.forms) == 3
    # 2 clean forms (naz, rod modern) and 1 marked form (rod archaic)
    assert len(res.clean_analyses) == 2
    assert len(res.marked_analyses) == 1
    assert res.effective_markers == ["arch"]

    not_found = inspect_lemma("ghost-lemma", db_path=inspection_db)
    assert not_found.status == InspectionStatus.NOT_FOUND
    assert not_found.forms == []


def test_inspect_as_dict_serializable(inspection_db: Path) -> None:
    word_res = inspect_word("clean", db_path=inspection_db)
    word_dict = word_res.as_dict()
    assert word_dict["status"] == "CLEAN"
    json_str = json.dumps(word_dict, ensure_ascii=False)
    assert "clean" in json_str

    lemma_res = inspect_lemma("clean", db_path=inspection_db)
    lemma_dict = lemma_res.as_dict()
    assert lemma_dict["status"] == "CLEAN"
    json.dumps(lemma_dict, ensure_ascii=False)


def test_inspection_fail_closed_on_legacy_schema(tmp_path: Path) -> None:
    """Test that a database with only the legacy flat schema returns UNAVAILABLE."""
    import sqlite3

    legacy_db = tmp_path / "legacy.db"
    conn = sqlite3.connect(legacy_db)
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    conn.execute("INSERT INTO forms VALUES ('слово', 'слово', 'noun:inanim:n:v_naz', 'noun')")
    conn.commit()
    conn.close()

    res = inspect_word("слово", db_path=legacy_db)
    assert res.status == InspectionStatus.UNAVAILABLE
    assert res.source_version == "unavailable"
    assert res.clean_analyses == []
    assert res.marked_analyses == []

    batch_res = inspect_words(["слово"], db_path=legacy_db)
    assert batch_res["слово"].status == InspectionStatus.UNAVAILABLE

    lemma_res = inspect_lemma("слово", db_path=legacy_db)
    assert lemma_res.status == InspectionStatus.UNAVAILABLE


def test_inspection_fail_closed_on_missing_db(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.db"

    res = inspect_word("слово", db_path=missing_path)
    assert res.status == InspectionStatus.UNAVAILABLE

    batch_res = inspect_words(["слово"], db_path=missing_path)
    assert batch_res["слово"].status == InspectionStatus.UNAVAILABLE

    lemma_res = inspect_lemma("слово", db_path=missing_path)
    assert lemma_res.status == InspectionStatus.UNAVAILABLE


def test_legacy_verify_word_hides_bad_subst_obsc(inspection_db: Path) -> None:
    """Compatibility view 'forms' must hide bad, subst, obsc and keep arch, slang, alt, vulg, dialect."""
    # Clean form: FOUND
    assert len(verify_word("clean", db_path=inspection_db)) == 1

    # Hidden in compatibility view:
    assert verify_word("invalid", db_path=inspection_db) == []
    assert verify_word("nonstandard", db_path=inspection_db) == []
    assert verify_word("obscene", db_path=inspection_db) == []

    # Visible in compatibility view:
    assert len(verify_word("slangy", db_path=inspection_db)) == 1
    assert len(verify_word("archaic", db_path=inspection_db)) == 1
    assert len(verify_word("alternate", db_path=inspection_db)) == 1
    assert len(verify_word("vulgar", db_path=inspection_db)) == 1
    assert len(verify_word("dialect-pure", db_path=inspection_db)) == 1


def test_legacy_verify_words_batch(inspection_db: Path) -> None:
    words = ["clean", "invalid", "nonstandard", "slangy", "archaic"]
    results = verify_words(words, db_path=inspection_db)

    assert len(results["clean"]) == 1
    assert results["invalid"] == []
    assert results["nonstandard"] == []
    assert len(results["slangy"]) == 1
    assert len(results["archaic"]) == 1


def test_legacy_verify_lemma(inspection_db: Path) -> None:
    forms = verify_lemma("clean", db_path=inspection_db)
    assert len(forms) == 2
    form_words = {f["word_form"] for f in forms}
    assert form_words == {"clean", "clean-form"}


def test_inspection_fail_closed_on_incomplete_schema(tmp_path: Path) -> None:
    """Incomplete schemas (e.g. missing entry_id or marker_class columns) must return UNAVAILABLE without error."""
    db_path = tmp_path / "incomplete.db"
    conn = sqlite3.connect(db_path)
    # forms_all missing entry_id, source_comment, source_location
    conn.execute(
        "CREATE TABLE forms_all (id INTEGER PRIMARY KEY, word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)"
    )
    # form_markers missing marker_class
    conn.execute(
        "CREATE TABLE form_markers (form_id INT, marker TEXT, origin TEXT)"
    )
    conn.execute("INSERT INTO forms_all VALUES (1, 'тест', 'тест', 'noun', 'tag')")
    conn.commit()
    conn.close()

    res = inspect_word("тест", db_path=db_path)
    assert res.status == InspectionStatus.UNAVAILABLE

    batch_res = inspect_words(["тест"], db_path=db_path)
    assert batch_res["тест"].status == InspectionStatus.UNAVAILABLE

    lemma_res = inspect_lemma("тест", db_path=db_path)
    assert lemma_res.status == InspectionStatus.UNAVAILABLE


def test_vesum_cli_global_db_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, inspection_db: Path, capsys: pytest.CaptureFixture) -> None:
    """Ensure --db is honored whether placed before or after the subcommand."""
    from scripts.verification.vesum import main as vesum_main

    # 1. Global --db before subcommand
    monkeypatch.setattr(
        "sys.argv",
        ["vesum.py", "--db", str(inspection_db), "word", "clean", "--json"],
    )
    vesum_main()
    out1 = capsys.readouterr().out
    data1 = json.loads(out1)
    assert len(data1) == 1
    assert data1[0]["lemma"] == "clean"

    # 2. Local --db after subcommand
    monkeypatch.setattr(
        "sys.argv",
        ["vesum.py", "word", "clean", "--db", str(inspection_db), "--json"],
    )
    vesum_main()
    out2 = capsys.readouterr().out
    data2 = json.loads(out2)
    assert len(data2) == 1
    assert data2[0]["lemma"] == "clean"


def test_get_vesum_conn_replacement_detection(tmp_path: Path) -> None:
    """Replacing the database file on disk causes get_vesum_conn to reopen to the new inode."""
    close_vesum_conn()
    db_path = tmp_path / "live.db"

    # DB 1: contains row 'first'
    conn1 = sqlite3.connect(db_path)
    conn1.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
    conn1.execute("INSERT INTO forms VALUES ('first', 'first', 'noun', 'tag')")
    conn1.commit()
    conn1.close()

    c1 = get_vesum_conn(db_path)
    rows1 = c1.execute("SELECT word_form FROM forms").fetchall()
    assert [r["word_form"] for r in rows1] == ["first"]

    # DB 2: built in temp location and atomically replaces DB 1
    new_db = tmp_path / "replacement.db"
    conn2 = sqlite3.connect(new_db)
    conn2.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
    conn2.execute("INSERT INTO forms VALUES ('second', 'second', 'noun', 'tag')")
    conn2.commit()
    conn2.close()

    os.replace(new_db, db_path)

    # get_vesum_conn without explicit close must detect inode/mtime change and read 'second'
    c2 = get_vesum_conn(db_path)
    rows2 = c2.execute("SELECT word_form FROM forms").fetchall()
    assert [r["word_form"] for r in rows2] == ["second"]
    close_vesum_conn()


def test_concurrent_connection_replacement_during_active_reader(tmp_path: Path) -> None:
    """Active reader connection is not closed prematurely when another thread triggers replacement."""
    close_vesum_conn()
    db_path = tmp_path / "live_concurrent.db"

    conn1 = sqlite3.connect(db_path)
    conn1.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
    conn1.execute("INSERT INTO forms VALUES ('first', 'first', 'noun', 'tag')")
    conn1.commit()
    conn1.close()

    reader_acquired = threading.Event()
    replacement_done = threading.Event()
    reader_results: list[str] = []
    reader_error: list[Exception] = []

    def reader_thread() -> None:
        try:
            with get_vesum_connection(db_path) as conn:
                reader_acquired.set()
                # Wait until the other thread has replaced the database file on disk
                # and triggered a replacement check in get_vesum_connection!
                assert replacement_done.wait(timeout=5.0)
                # Reader executes query on its acquired connection.
                # Must NOT raise ProgrammingError: Cannot operate on a closed database!
                rows = conn.execute("SELECT word_form FROM forms").fetchall()
                reader_results.extend(r["word_form"] for r in rows)
        except Exception as exc:
            reader_error.append(exc)

    t = threading.Thread(target=reader_thread)
    t.start()

    assert reader_acquired.wait(timeout=5.0)

    # Concurrently replace the database file on disk with DB 2 ('second')
    new_db = tmp_path / "replacement_concurrent.db"
    conn2 = sqlite3.connect(new_db)
    conn2.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
    conn2.execute("INSERT INTO forms VALUES ('second', 'second', 'noun', 'tag')")
    conn2.commit()
    conn2.close()

    os.replace(new_db, db_path)

    # Thread 2 (here) acquires connection, detecting replacement and switching to DB 2
    with get_vesum_connection(db_path) as new_c:
        new_rows = new_c.execute("SELECT word_form FROM forms").fetchall()
        assert [r["word_form"] for r in new_rows] == ["second"]

    # Signal reader_thread that replacement and switch occurred
    replacement_done.set()
    t.join(timeout=5.0)

    assert not reader_error, f"Reader encountered error during concurrent replacement: {reader_error}"
    assert reader_results == ["first"], f"Expected reader to complete on first connection, got {reader_results}"
    close_vesum_conn()
