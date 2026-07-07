from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ingest.zno_ingest import ingest, ingest_documents, init_db


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


def test_task_extraction_and_fts(db_path: Path, cache_dir: Path) -> None:
    # Set up our cached files in the temporary test cache dir
    project_cache = Path("tmp/zno_cache")
    cached_ids = [347, 401, 471]
    for cid in cached_ids:
        src = project_cache / f"{cid}_main.html"
        if src.exists():
            dest = cache_dir / f"{cid}_main.html"
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # Mock urllib.request.urlopen to return dummy HTML for uncached pages
    dummy_html = """
    <html>
      <body>
        <div class="task-card" id="q1">
          <form class="q-test" id="q_form_1">
            <input type="hidden" name="q[tip]" value="1">
            <div class="question">
              <p>Dummy question stem text</p>
            </div>
            <div class="answers">
              <div class="answer"><span class="marker">А</span>Dummy option A</div>
              <div class="answer"><span class="marker">Б</span>Dummy option B</div>
            </div>
            <input type="hidden" name="result" value="a">
          </form>
          <div class="explanation" id="commentar_1">
            <strong>Пояснення</strong>
            <p><strong>ТЕМА: Фонетика.</strong></p>
          </div>
        </div>
      </body>
    </html>
    """

    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = dummy_html.encode("utf-8")
    mock_response.getcode.return_value = 200

    with patch("urllib.request.urlopen", return_value=mock_response):
        total_tasks = ingest(db_path, cache_dir)

    conn = sqlite3.connect(db_path)
    try:
        # Check total number of tasks in the DB
        tasks_count = conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0]
        assert tasks_count > 0

        # Assert the actual count of tasks extracted for 2019 Main Session (test_id 347, document_id 14)
        # In 2019 Main session, zno.osvita.ua has 58 questions.
        q19_count = conn.execute("SELECT count(*) FROM zno_tasks WHERE year = 2019 AND session = 'osnovna'").fetchone()[
            0
        ]
        assert q19_count == 58

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
