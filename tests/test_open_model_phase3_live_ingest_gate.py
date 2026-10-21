"""One-time Phase 3 live-ingest gate tests."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_live_ingest_gate as live_gate
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REGISTRY_OPEN_MODEL_DATA_DIR / "admission/phase3_live_ingest_gate_v1.json"


def _fixture_db(path: Path, *, staged_source_present: bool = False) -> dict:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            text TEXT,
            source_file TEXT,
            grade TEXT
        );
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(
            title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;
        CREATE TABLE textbook_sections (
            id INTEGER PRIMARY KEY,
            source_file TEXT
        );
        """
    )
    if staged_source_present:
        conn.execute(
            "INSERT INTO textbooks(title, text, source_file, grade) VALUES (?, ?, ?, ?)",
            (
                "Тест",
                "Тестовий текст",
                live_gate.REQUESTED_SOURCES[0],
                "university",
            ),
        )
    conn.commit()
    counts = live_gate._database_counts(conn)
    conn.close()
    return counts


def _fixture_gate(path: Path, counts: dict) -> dict:
    return {
        "database": {
            "sha256_before": live_gate.sha256_file(path),
            "counts_before": counts,
            "foreign_key_failure_count": 0,
            "foreign_key_failure_hash": hashlib.sha256(b"[]").hexdigest(),
            "integrity_check": "ok",
            "journal_mode": "wal",
        }
    }


def test_runtime_loader_rejects_semantically_identical_byte_drift(tmp_path):
    drifted = tmp_path / GATE_PATH.name
    drifted.write_text(GATE_PATH.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(live_gate.LiveIngestGateError, match="byte drift"):
        live_gate.load_gate(drifted)

    with pytest.raises(live_gate.LiveIngestGateError, match="is missing"):
        live_gate.load_gate(tmp_path / "absent.json")


def test_database_preimage_accepts_only_exact_live_path_and_absent_sources(tmp_path):
    db_path = tmp_path / "sources.db"
    counts = _fixture_db(db_path)
    document = _fixture_gate(db_path, counts)

    live_gate.validate_database_preimage(
        document,
        db_path=db_path,
        expected_live_db_path=db_path,
    )

    copied_path = tmp_path / "copy.db"
    copied_path.write_bytes(db_path.read_bytes())
    with pytest.raises(live_gate.LiveIngestGateError, match="primary checkout sources database"):
        live_gate.validate_database_preimage(
            document,
            db_path=copied_path,
            expected_live_db_path=db_path,
        )


def test_database_preimage_rejects_already_present_staged_source(tmp_path):
    db_path = tmp_path / "sources.db"
    counts = _fixture_db(db_path, staged_source_present=True)
    document = _fixture_gate(db_path, counts)

    with pytest.raises(live_gate.LiveIngestGateError, match="already present"):
        live_gate.validate_database_preimage(
            document,
            db_path=db_path,
            expected_live_db_path=db_path,
        )


def test_preconditions_reject_wrong_source_set_before_database_access(tmp_path):
    with pytest.raises(live_gate.LiveIngestGateError, match="exact four-source set"):
        live_gate.validate_live_ingest_preconditions(
            gate_path=GATE_PATH,
            db_path=tmp_path / "missing.db",
            expected_live_db_path=tmp_path / "missing.db",
            source_ids=[live_gate.REQUESTED_SOURCES[0]],
            quarantine_source_ids=[],
            source_policy_sha256=live_gate.EXPECTED_INPUT_HASHES["complete_source_policy_v4_sha256"],
            dry_run=False,
            copied_database_rehearsal=False,
            receipt_path=tmp_path / "receipt.json",
        )


@pytest.mark.parametrize(
    ("dry_run", "copied_rehearsal", "receipt_path", "message"),
    [
        (True, False, Path("receipt.json"), "not a dry-run"),
        (False, True, Path("receipt.json"), "cannot be combined"),
        (False, False, None, "explicit receipt path"),
    ],
)
def test_preconditions_reject_non_cutover_execution_before_database_access(
    tmp_path,
    dry_run,
    copied_rehearsal,
    receipt_path,
    message,
):
    with pytest.raises(live_gate.LiveIngestGateError, match=message):
        live_gate.validate_live_ingest_preconditions(
            gate_path=GATE_PATH,
            db_path=tmp_path / "missing.db",
            expected_live_db_path=tmp_path / "missing.db",
            source_ids=live_gate.REQUESTED_SOURCES,
            quarantine_source_ids=[],
            source_policy_sha256=live_gate.EXPECTED_INPUT_HASHES["complete_source_policy_v4_sha256"],
            dry_run=dry_run,
            copied_database_rehearsal=copied_rehearsal,
            receipt_path=receipt_path,
        )
