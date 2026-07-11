from __future__ import annotations

import io
import json
import os
import sqlite3
import urllib.request
from pathlib import Path

import pytest

from scripts.ingest import zno_ingest
from scripts.ingest.zno_ingest import (
    FETCH_TIMEOUT_SECONDS,
    ONLINE_TEST_MAPPING,
    derive_task_metadata,
    fetch_page_with_rate_limit,
    ingest,
    ingest_documents,
    init_db,
    parse_and_insert_tasks,
)


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


def test_online_mapping_covers_every_booklet_with_a_clean_interactive_source() -> None:
    assert ONLINE_TEST_MAPPING == {
        (2010, "sesiya-1", "mova-lit"): ("ukrainian", 15),
        (2010, "sesiya-2", "mova-lit"): ("ukrainian", 16),
        (2010, "sesiya-3", "mova-lit"): ("ukrainian", 17),
        (2011, "sesiya-1", "mova-lit"): ("ukrainian", 13),
        (2011, "sesiya-2", "mova-lit"): ("ukrainian", 14),
        (2012, "sesiya-1", "mova-lit"): ("ukrainian", 11),
        (2012, "sesiya-2", "mova-lit"): ("ukrainian", 12),
        (2013, "sesiya-1", "mova-lit"): ("ukrainian", 6),
        (2013, "sesiya-2", "mova-lit"): ("ukrainian", 10),
        (2014, "sesiya-1", "mova-lit"): ("ukrainian", 132),
        (2014, "sesiya-2", "mova-lit"): ("ukrainian", 133),
        (2014, "dodatkova", "mova-lit"): ("ukrainian", 130),
        (2015, "osnovna", "mova-lit"): ("ukrainian", 143),
        (2016, "osnovna", "mova-lit"): ("ukrainian", 189),
        (2017, "osnovna", "mova-lit"): ("ukrainian", 240),
        (2017, "dodatkova", "mova-lit"): ("ukrainian", 254),
        (2018, "osnovna", "mova-lit"): ("ukrainian", 299),
        (2018, "dodatkova", "mova-lit"): ("ukrainian", 309),
        (2019, "osnovna", "mova-lit"): ("ukrainian", 347),
        (2019, "dodatkova", "mova-lit"): ("ukrainian", 363),
        (2020, "osnovna", "mova-lit"): ("ukrainian", 401),
        (2020, "dodatkova", "mova-lit"): ("ukrainian", 429),
        (2021, "osnovna", "mova-lit"): ("ukrainian", 471),
        (2021, "dodatkova", "mova-lit"): ("ukrainian", 491),
        (2022, "osnovna", "mova"): ("ukrmova", 617),
        (2023, "sesiya-1", "mova"): ("ukrmova", 619),
        (2023, "sesiya-2", "mova"): ("ukrmova", 620),
        (2024, "sesiya-1", "mova"): ("ukrmova", 622),
        (2024, "sesiya-2", "mova"): ("ukrmova", 623),
        (2025, "sesiya-1", "mova"): ("ukrmova", 667),
        (2025, "sesiya-2", "mova"): ("ukrmova", 668),
    }


def test_task_refresh_preserves_reviewed_annotations(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        html = (Path(__file__).parent / "fixtures" / "347_trimmed.html").read_text(encoding="utf-8")
        parse_and_insert_tasks(conn, html, 14, 2019, "zno", "osnovna")
        conn.execute(
            """
            UPDATE zno_tasks
            SET topic_norm = ?, task_subtype = ?, paronym_pair = ?, stress_word = ?
            WHERE document_id = ? AND task_no = ?
            """,
            ("lexical_norm", "paronym", "saved-pair", "saved-word", 14, 1),
        )

        parse_and_insert_tasks(conn, html, 14, 2019, "zno", "osnovna")
        refreshed = conn.execute(
            """
            SELECT topic_norm, task_subtype, paronym_pair, stress_word
            FROM zno_tasks WHERE document_id = ? AND task_no = ?
            """,
            (14, 1),
        ).fetchone()

        assert refreshed == ("lexical_norm", "paronym", "saved-pair", "saved-word")
        assert conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0] == 4
    finally:
        conn.close()


def test_derive_task_metadata_uses_explicit_prompt_and_answer() -> None:
    assert derive_task_metadata(
        "Антонімами є слова в рядку",
        json.dumps(["перший", "другий"], ensure_ascii=False),
        "",
        "single-choice",
    ) == ("antonym", "")
    assert derive_task_metadata(
        "На перший склад падає наголос у слові",
        json.dumps(["слово А", "слово Б"], ensure_ascii=False),
        "Б",
        "single-choice",
    ) == ("", "слово Б")
    assert derive_task_metadata(
        "Лексичну помилку допущено в рядку",
        "[]",
        "",
        "single-choice",
    ) == ("lexical_error", "")


def test_parser_classifies_the_question_prompt_not_source_text(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        html = """
        <div class="task-card" id="q1">
          <input name="q[tip]" value="1">
          <div class="question">
            <p>У тексті вжито слово «синонім».</p>
            <p>Визначте головну думку тексту.</p>
          </div>
          <div class="answer"><span class="marker">А</span>перша</div>
          <div class="answer"><span class="marker">Б</span>друга</div>
          <input name="result" value="a">
        </div>
        """
        parse_and_insert_tasks(conn, html, 14, 2019, "zno", "osnovna")

        assert conn.execute("SELECT task_subtype FROM zno_tasks").fetchone() == ("",)
    finally:
        conn.close()


def test_fetch_page_uses_bounded_request_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    timeouts: list[int] = []

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
            return None

        def read(self) -> bytes:
            return io.BytesIO("<html>тест</html>".encode()).read()

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> Response:
        assert request.full_url == "https://example.invalid/test/"
        timeouts.append(timeout)
        return Response()

    monkeypatch.setattr(zno_ingest.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(zno_ingest, "_last_request_time", 0.0)

    html = fetch_page_with_rate_limit("https://example.invalid/test/", tmp_path / "page.html", rate_limit=0)

    assert html == "<html>тест</html>"
    assert timeouts == [FETCH_TIMEOUT_SECONDS]


@pytest.mark.skipif(os.getenv("ZNO_LIVE") != "1", reason="Requires ZNO_LIVE=1 env var")
def test_task_extraction_live(db_path: Path, cache_dir: Path) -> None:
    total_tasks = ingest(db_path, cache_dir)
    assert total_tasks == 1646

    conn = sqlite3.connect(db_path)
    try:
        tasks_count = conn.execute("SELECT count(*) FROM zno_tasks").fetchone()[0]
        assert tasks_count == 1646

        year_counts = dict(conn.execute("SELECT year, count(*) FROM zno_tasks GROUP BY year"))
        assert year_counts == {
            2010: 183,
            2011: 122,
            2012: 122,
            2013: 122,
            2014: 183,
            2015: 58,
            2016: 58,
            2017: 116,
            2018: 116,
            2019: 116,
            2020: 116,
            2021: 134,
            2022: 20,
            2023: 60,
            2024: 60,
            2025: 60,
        }

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
