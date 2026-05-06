from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest.dictionary_ingest import ADAPTERS, build_parser, ingest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("source", "table", "expected"),
    [
        ("antonenko", "style_antonenko", 2),
        ("karavansky", "karavansky_r2u", 2),
        ("holovashchuk", "style_holovashchuk", 2),
        ("paronyms", "paronyms_full", 2),
    ],
)
def test_adapter_ingests_fixture_rows(tmp_path: Path, source: str, table: str, expected: int) -> None:
    db_path = tmp_path / "sources.db"
    result = ingest(
        ADAPTERS[source],
        FIXTURES / f"{source}.txt",
        db_path,
        dry_run=False,
        force=False,
    )

    assert result.parsed == expected
    assert result.inserted == expected
    assert result.skipped == 0

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()
    assert count == expected


@pytest.mark.parametrize(
    ("source", "fts_table", "query", "expected_column"),
    [
        ("antonenko", "style_antonenko_fts", "священник", "right_form"),
        ("karavansky", "karavansky_r2u_fts", "коротко", "uk_translations"),
        ("holovashchuk", "style_holovashchuk_fts", "участь", "correct_usage"),
        ("paronyms", "paronyms_full_fts", "результативний", "meaning_b"),
    ],
)
def test_fts_search_returns_expected_rows(
    tmp_path: Path,
    source: str,
    fts_table: str,
    query: str,
    expected_column: str,
) -> None:
    db_path = tmp_path / "sources.db"
    ingest(ADAPTERS[source], FIXTURES / f"{source}.txt", db_path, dry_run=False, force=False)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT 1",
            (query,),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row[expected_column]


def test_idempotent_rerun_skips_duplicates(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    adapter = ADAPTERS["karavansky"]
    fixture = FIXTURES / "karavansky.txt"

    first = ingest(adapter, fixture, db_path, dry_run=False, force=False)
    second = ingest(adapter, fixture, db_path, dry_run=False, force=False)

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped == 2

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM karavansky_r2u").fetchone()[0]
    finally:
        conn.close()
    assert count == 2


def test_all_adapters_ingest_into_one_db_and_fts_search(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    searches = [
        ("style_antonenko_fts", "священник"),
        ("karavansky_r2u_fts", "коротко"),
        ("style_holovashchuk_fts", "участь"),
        ("paronyms_full_fts", "результативний"),
    ]

    for source, adapter in ADAPTERS.items():
        result = ingest(adapter, FIXTURES / f"{source}.txt", db_path, dry_run=False, force=False)
        assert result.inserted == 2

    conn = sqlite3.connect(db_path)
    try:
        for fts_table, query in searches:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {fts_table} WHERE {fts_table} MATCH ?",
                (query,),
            ).fetchone()[0]
            assert count >= 1
    finally:
        conn.close()


def test_force_reingest_replaces_target_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    adapter = ADAPTERS["antonenko"]
    fixture = FIXTURES / "antonenko.txt"

    ingest(adapter, fixture, db_path, dry_run=False, force=False)
    forced = ingest(adapter, fixture, db_path, dry_run=False, force=True)

    assert forced.inserted == 2
    assert forced.skipped == 0

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM style_antonenko").fetchone()[0]
    finally:
        conn.close()
    assert count == 2


def test_dry_run_does_not_create_database(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"

    result = ingest(
        ADAPTERS["paronyms"],
        FIXTURES / "paronyms.txt",
        db_path,
        dry_run=True,
        force=False,
    )

    assert result.parsed == 2
    assert result.dry_run is True
    assert not db_path.exists()


def test_paronym_parser_keeps_meanings_separate() -> None:
    rows = ADAPTERS["paronyms"].parse((FIXTURES / "paronyms.txt").read_text(encoding="utf-8"))

    assert rows[0].values["meaning_a"] == "письмове привітання"
    assert rows[0].values["meaning_b"] == "місце проживання"


def test_help_documents_sources(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])

    assert exc.value.code == 0
    out = capsys.readouterr().out
    for source in ADAPTERS:
        assert source in out
    assert "PDF extraction is not" in out
    assert "handled here" in out
