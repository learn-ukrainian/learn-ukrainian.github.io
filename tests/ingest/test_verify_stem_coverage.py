"""Exercise census evidence against a real SQLite FTS5 fixture."""

import hashlib
import json
import sqlite3
import subprocess
import sys

from scripts.ingest.verify_stem_coverage import census, main


def test_census_separates_all_grade_totals_and_scoped_fts(tmp_path):
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            "CREATE TABLE textbooks(id INTEGER PRIMARY KEY, source_file TEXT, grade TEXT, subject TEXT, text TEXT);"
            "CREATE VIRTUAL TABLE textbooks_fts USING fts5(text, content='textbooks', content_rowid='id');"
        )
        conn.executemany(
            "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?)",
            [
                (1, "primary", "3", "informatyka", "алгоритм"),
                (2, "secondary", "5", "informatyka", "алгоритм"),
                (3, "secondary", "5", "informatyka", "рівняння"),
                (4, "humanities", "5", "ukrmova", "алгоритм"),
                (5, "null-grade", None, "informatyka", "алгоритм"),
            ],
        )
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES ('rebuild')")
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    report = census(db)
    assert report["total_textbook_chunks"] == 5
    subject = report["subjects"]["informatyka"]
    assert (subject["files"], subject["chunks"]) == (3, 4)
    assert subject["grades_5_11"]["5"] == {"files": 1, "chunks": 2}
    assert subject["absent_grades_5_11"] == [6, 7, 8, 9, 10, 11]
    assert report["subjects"]["biolohiya"]["files"] == 0
    assert report["fts_probes"]["алгоритм"] == {"all_textbooks": 4, "stem_grades_5_11": 1}
    assert report["fts_probes"]["фотосинтез"] == {"all_textbooks": 0, "stem_grades_5_11": 0}
    assert subject["sources"][2] == {"source_file": "secondary", "grade": "5", "chunks": 2}
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert main(["--db", str(db)]) == 0


def test_missing_database_is_not_created(tmp_path, capsys):
    db = tmp_path / "absent.db"
    assert main(["--db", str(db)]) == 2
    assert not db.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_missing_fts_is_error_not_zero_evidence(tmp_path, capsys):
    db = tmp_path / "incomplete.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE textbooks(id INTEGER, source_file TEXT, grade TEXT, subject TEXT)")
    assert main(["--db", str(db)]) == 2
    output = capsys.readouterr()
    assert "no such table: textbooks_fts" in output.err
    assert not output.out


def test_cli_json(tmp_path, capsys):
    db = tmp_path / "empty.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            "CREATE TABLE textbooks(id INTEGER, source_file TEXT, grade TEXT, subject TEXT);"
            "CREATE VIRTUAL TABLE textbooks_fts USING fts5(text);"
        )
    assert main(["--db", str(db)]) == 0
    assert json.loads(capsys.readouterr().out)["total_textbook_chunks"] == 0


def test_cli_help_uses_portable_example():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.ingest.verify_stem_coverage", "--help"],
        capture_output=True, text=True, check=True,
    )
    assert "/home/" not in result.stdout
    assert ".venv/bin/python -m scripts.ingest.verify_stem_coverage" in result.stdout
    assert "--db /path/to/sources.db" in result.stdout
    assert not result.stderr
