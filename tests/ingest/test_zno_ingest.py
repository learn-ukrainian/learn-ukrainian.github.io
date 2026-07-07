from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from scripts.ingest.zno_ingest import ingest, ingest_documents, init_db, parse_and_insert_tasks


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "sources.db"


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "zno_cache"
    d.mkdir()
    return d


def test_schema_creation_is_idempotent(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        # Run first time
        init_db(conn)
        # Run second time - should not raise any error
        init_db(conn)
    finally:
        conn.close()


def test_documents_count_and_status(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        ingest_documents(conn)

        # Assert count is exactly 33
        count = conn.execute("SELECT count(*) FROM zno_documents").fetchone()[0]
        assert count == 33

        # Assert that the dead status is correctly preserved for the 2014 additional session
        dead_doc = conn.execute(
            "SELECT fetch_status, verified_by FROM zno_documents WHERE year = 2014 AND session = 'dodatkova'"
        ).fetchone()
        assert dead_doc is not None
        assert dead_doc[0] == "dead"
        assert dead_doc[1] == "claude-live"

        # Assert wrong-content status for 2010 session 1
        wrong_doc = conn.execute(
            "SELECT fetch_status, verified_by FROM zno_documents WHERE year = 2010 AND session = 'sesiya-1'"
        ).fetchone()
        assert wrong_doc is not None
        assert wrong_doc[0] == "wrong-content"
        assert wrong_doc[1] == "claude-live"
    finally:
        conn.close()


def test_task_extraction_from_fixtures(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        ingest_documents(conn)

        fixtures_dir = Path(__file__).parent / "fixtures"

        # Ingest from 2019 osnovna trimmed fixture (doc_id = 14)
        fixture_347_path = fixtures_dir / "347_trimmed.html"
        html_347 = fixture_347_path.read_text(encoding="utf-8")
        parsed_347 = parse_and_insert_tasks(conn, html_347, 14, 2019, "zno", "osnovna")
        assert parsed_347 == 4  # q1, q2, q24, q58

        # Ingest from 2021 osnovna trimmed fixture (doc_id = 8)
        fixture_471_path = fixtures_dir / "471_trimmed.html"
        html_471 = fixture_471_path.read_text(encoding="utf-8")
        parsed_471 = parse_and_insert_tasks(conn, html_471, 8, 2021, "zno", "osnovna")
        assert parsed_471 == 4  # q1, q2, q24, q67

        conn.commit()

        # Check total number of tasks in the DB
        tasks_count = conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0]
        assert tasks_count == 8

        # Verify columns and data format of a single-choice task
        task = conn.execute(
            "SELECT task_no, subject, task_format, stem, options_json, correct_json, topic_tag "
            "FROM zno_tasks WHERE year = 2019 AND session = 'osnovna' AND task_no = 1"
        ).fetchone()
        assert task is not None
        assert task[0] == 1  # task_no
        assert task[1] == "mova"  # subject
        assert task[2] == "single-choice"  # task_format
        assert "На перший склад падає наголос" in task[3]  # stem

        options = json.loads(task[4])
        assert len(options) == 4
        assert options[0] == "причіп"
        assert task[5] == "В"  # correct_json mapped from 'c' -> 'В'
        assert "Орфоепія" in task[6]  # topic_tag

        # Verify a matching task
        task_match = conn.execute(
            "SELECT task_no, task_format, options_json, correct_json "
            "FROM zno_tasks WHERE year = 2019 AND session = 'osnovna' AND task_no = 24"
        ).fetchone()
        assert task_match is not None
        assert task_match[1] == "matching"

        opts = json.loads(task_match[2])
        assert "left" in opts
        assert "right" in opts
        assert len(opts["left"]) == 4
        assert len(opts["right"]) == 5

        corr = json.loads(task_match[3])
        assert corr["1"] == "Г"
        assert corr["2"] == "В"
        assert corr["3"] == "Д"
        assert corr["4"] == "А"

        # Assert FTS queries return expected stems
        fts_res = conn.execute("SELECT rowid FROM zno_tasks_fts WHERE zno_tasks_fts MATCH 'причіп'").fetchall()
        assert len(fts_res) > 0

    finally:
        conn.close()


@pytest.mark.skipif(os.getenv("ZNO_LIVE") != "1", reason="Requires ZNO_LIVE=1 env var")
def test_task_extraction_live(db_path: Path, cache_dir: Path) -> None:
    total_tasks = ingest(db_path, cache_dir)
    assert total_tasks == 366

    conn = sqlite3.connect(db_path)
    try:
        tasks_count = conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0]
        assert tasks_count == 366

        # Check real counts for all 6 documents
        q19_count = conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2019 AND session = 'osnovna'").fetchone()[0]
        assert q19_count == 58

        assert conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2019 AND session = 'dodatkova'").fetchone()[0] == 58
        assert conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2020 AND session = 'osnovna'").fetchone()[0] == 58
        assert conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2020 AND session = 'dodatkova'").fetchone()[0] == 58
        assert conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2021 AND session = 'osnovna'").fetchone()[0] == 67
        assert conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2021 AND session = 'dodatkova'").fetchone()[0] == 67

        # Verify task details on real data
        task = conn.execute(
            "SELECT task_no, subject, task_format, stem, options_json, correct_json, topic_tag "
            "FROM zno_tasks WHERE year = 2019 AND session = 'osnovna' AND task_no = 1"
        ).fetchone()
        assert task is not None
        assert task[0] == 1
        assert task[1] == "mova"
        assert task[2] == "single-choice"
        assert "На перший склад падає наголос" in task[3]

        options = json.loads(task[4])
        assert len(options) == 4
        assert options[0] == "причіп"
        assert task[5] == "В"
        assert "Орфоепія" in task[6]

        task_match = conn.execute(
            "SELECT task_no, task_format, options_json, correct_json "
            "FROM zno_tasks WHERE year = 2019 AND session = 'osnovna' AND task_no = 24"
        ).fetchone()
        assert task_match is not None
        assert task_match[1] == "matching"

        opts = json.loads(task_match[2])
        assert len(opts["left"]) == 4
        assert len(opts["right"]) == 5

        corr = json.loads(task_match[3])
        assert corr["1"] == "Г"
        assert corr["2"] == "В"
        assert corr["3"] == "Д"
        assert corr["4"] == "А"

        fts_res = conn.execute("SELECT rowid FROM zno_tasks_fts WHERE zno_tasks_fts MATCH 'причіп'").fetchall()
        assert len(fts_res) > 0
    finally:
        conn.close()
