from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.execute("""
            CREATE TABLE zno_tasks (
                id INTEGER PRIMARY KEY,
                topic_norm TEXT DEFAULT '',
                task_subtype TEXT DEFAULT '',
                paronym_pair TEXT DEFAULT '',
                stress_word TEXT DEFAULT ''
            )
        """)
        # Task 1: Unannotated
        conn.execute(
            "INSERT INTO zno_tasks (id, topic_norm, task_subtype, paronym_pair, stress_word) VALUES (1, '', '', '', '')"
        )
        # Task 2: Unannotated
        conn.execute(
            "INSERT INTO zno_tasks (id, topic_norm, task_subtype, paronym_pair, stress_word) VALUES (2, '', '', '', '')"
        )
        # Task 3: Already annotated
        conn.execute(
            "INSERT INTO zno_tasks (id, topic_norm, task_subtype, paronym_pair, stress_word) VALUES (3, 'literature', '', '', '')"
        )
        conn.commit()
    finally:
        conn.close()
    return db_file


@pytest.fixture
def write_worksheet(tmp_path: Path):
    def _write(annotations: list[dict]) -> Path:
        yaml_file = tmp_path / "worksheet.yaml"
        content = {
            "schema_version": 1,
            "zno_annotations": annotations,
        }
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)
        return yaml_file

    return _write


def run_applier(db: Path, worksheet: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    args = [
        sys.executable,
        "-m",
        "scripts.ingest.apply_zno_annotations",
        "--db",
        str(db),
        "--worksheet",
        str(worksheet),
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True)


def test_apply_success(temp_db: Path, write_worksheet) -> None:
    # 1. Propose valid updates for Task 1 and Task 2
    annotations = [
        {
            "id": 1,
            "topic_norm": "lexical_norm",
            "task_subtype": "word_choice",
            "paronym_pair": "інформативний/інформаційний",
        },
        {
            "id": 2,
            "topic_norm": "orthoepic_norm",
            "stress_word": "причіп",
        },
    ]
    worksheet = write_worksheet(annotations)

    result = run_applier(temp_db, worksheet)
    assert result.returncode == 0
    assert "Summary: 2 updated / 0 skipped-identical / 0 conflicts" in result.stdout

    # Verify updates in DB
    conn = sqlite3.connect(temp_db)
    try:
        row1 = conn.execute(
            "SELECT topic_norm, task_subtype, paronym_pair, stress_word FROM zno_tasks WHERE id = 1"
        ).fetchone()
        assert row1 == ("lexical_norm", "word_choice", "інформативний/інформаційний", "")

        row2 = conn.execute(
            "SELECT topic_norm, task_subtype, paronym_pair, stress_word FROM zno_tasks WHERE id = 2"
        ).fetchone()
        assert row2 == ("orthoepic_norm", "", "", "причіп")
    finally:
        conn.close()


def test_apply_idempotency(temp_db: Path, write_worksheet) -> None:
    # 1. Run first time to apply
    annotations = [
        {
            "id": 1,
            "topic_norm": "lexical_norm",
            "task_subtype": "word_choice",
        }
    ]
    worksheet = write_worksheet(annotations)

    result1 = run_applier(temp_db, worksheet)
    assert result1.returncode == 0
    assert "Summary: 1 updated / 0 skipped-identical / 0 conflicts" in result1.stdout

    # 2. Run second time to ensure it is a no-op
    result2 = run_applier(temp_db, worksheet)
    assert result2.returncode == 0
    assert "Summary: 0 updated / 1 skipped-identical / 0 conflicts" in result2.stdout


def test_apply_conflict_refusal(temp_db: Path, write_worksheet) -> None:
    # Task 3 is already 'literature' in DB. Proposing 'lexical_norm' should cause conflict.
    annotations = [
        {
            "id": 1,
            "topic_norm": "lexical_norm",  # This would be a valid update
        },
        {
            "id": 3,
            "topic_norm": "lexical_norm",  # This is a conflict
        },
    ]
    worksheet = write_worksheet(annotations)

    result = run_applier(temp_db, worksheet)
    assert result.returncode == 2
    assert "Conflicts detected:" in result.stderr
    assert "Task ID 3, column 'topic_norm': DB has 'literature', proposed is 'lexical_norm'" in result.stderr
    assert "Summary: 1 updated / 0 skipped-identical / 1 conflicts" in result.stdout

    # Verify that NO updates were written to the DB (atomic transaction refusal)
    conn = sqlite3.connect(temp_db)
    try:
        # Task 1 should STILL be empty
        row1 = conn.execute("SELECT topic_norm FROM zno_tasks WHERE id = 1").fetchone()
        assert row1[0] == ""

        # Task 3 should STILL be 'literature'
        row3 = conn.execute("SELECT topic_norm FROM zno_tasks WHERE id = 3").fetchone()
        assert row3[0] == "literature"
    finally:
        conn.close()


def test_apply_dry_run(temp_db: Path, write_worksheet) -> None:
    annotations = [
        {
            "id": 1,
            "topic_norm": "lexical_norm",
            "task_subtype": "word_choice",
        }
    ]
    worksheet = write_worksheet(annotations)

    result = run_applier(temp_db, worksheet, extra_args=["--dry-run"])
    assert result.returncode == 0
    assert "Summary: 1 updated / 0 skipped-identical / 0 conflicts" in result.stdout
    assert "Planned updates: 1" in result.stdout
    assert "Sample updates (up to 5):" in result.stdout
    assert "Task ID 1: topic_norm: '' -> 'lexical_norm', task_subtype: '' -> 'word_choice'" in result.stdout

    # Verify that database was NOT modified
    conn = sqlite3.connect(temp_db)
    try:
        row1 = conn.execute("SELECT topic_norm, task_subtype FROM zno_tasks WHERE id = 1").fetchone()
        assert row1 == ("", "")
    finally:
        conn.close()
