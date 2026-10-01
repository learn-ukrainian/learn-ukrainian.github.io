"""Opt-in, read-only ULIF snapshots for tests that assert dictionary authority."""

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_stress_sources(request, tmp_path, monkeypatch):
    """Stress unit tests never inherit an ambient source store or connection."""
    if not request.path.name.startswith("test_stress"):
        return
    from scripts.wiki import sources_db

    monkeypatch.setenv("LU_SOURCES_DB", str(tmp_path / "absent-sources.sqlite"))
    monkeypatch.setattr(sources_db, "_conn", None)


@pytest.fixture
def ulif_stress_db(tmp_path, monkeypatch):
    """Materialize captured source rows without depending on the host corpus."""
    from scripts.verification import stress
    from scripts.wiki import sources_db

    capture = json.loads((Path(__file__).parents[1] / "fixtures/stress-ci.json").read_text())
    path = tmp_path / "ulif-stress.sqlite"
    with sqlite3.connect(path) as conn:
        for table, rows in (
            ("ulif_forms_build", [capture["build"]]),
            ("ulif_forms", capture["forms"]),
            ("ulif_dictua_entries", capture["entries"]),
        ):
            columns = list(rows[0])
            conn.execute(f"CREATE TABLE {table} ({','.join(columns)})")
            conn.executemany(
                f"INSERT INTO {table} VALUES ({','.join('?' for _ in columns)})",
                [[row[column] for column in columns] for row in rows],
            )
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    monkeypatch.setenv("LU_SOURCES_DB", str(path))
    # Other words retain the existing VESUM/trie fixture behavior; the captured
    # words have a frozen identity join as well as frozen stress rows.
    original = stress._vesum_lookup
    monkeypatch.setattr(
        stress,
        "_vesum_lookup",
        lambda form: [dict(row) for row in capture["vesum"][form]] if form in capture["vesum"] else original(form),
    )
    try:
        with sources_db.using_connection(conn):
            yield path
    finally:
        conn.close()
