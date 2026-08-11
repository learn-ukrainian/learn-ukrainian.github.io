"""One-time Phase 3 live-ingest gate tests."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_live_ingest_gate as live_gate

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_live_ingest_gate_v1.json"


def _gate() -> dict:
    return json.loads(GATE_PATH.read_text(encoding="utf-8"))


def _reseal(gate: dict) -> dict:
    body = {key: value for key, value in gate.items() if key != "receipt_sha256"}
    gate["receipt_sha256"] = hashlib.sha256(
        (live_gate.canonical_json(body) + "\n").encode("utf-8")
    ).hexdigest()
    return gate


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


def test_tracked_gate_is_exact_and_single_use():
    document, gate_sha256 = live_gate.load_gate(GATE_PATH)

    assert gate_sha256 == live_gate.EXPECTED_GATE_SHA256
    assert document["requested_sources"] == list(live_gate.REQUESTED_SOURCES)
    assert document["database"]["sha256_before"] == live_gate.EXPECTED_LIVE_DB_SHA256
    assert document["database"]["counts_before"] == live_gate.COUNTS_BEFORE
    assert document["database"]["counts_after_expected"] == live_gate.COUNTS_AFTER
    assert document["execution"] == {
        "live_ingest_authorized": True,
        "single_use": True,
        "exact_preimage_required": True,
        "exact_source_set_required": True,
        "receipt_required": True,
        "post_ingest_backup_required": True,
        "provider_work_authorized": False,
    }
    assert document["source_freeze_ready"] is False
    assert document["phase3_complete"] is False
    assert document["phase4_blocked"] is True


def test_gate_binds_rehearsal_review_and_provider_uploaded_preimage():
    document = _gate()

    assert document["bindings"] == {
        **live_gate.EXPECTED_INPUT_HASHES,
        "pr6631_merge_commit": live_gate.PR6631_MERGE_COMMIT,
    }
    assert document["copied_database_rehearsal"] == {
        "execution_scope": "copied_database_rehearsal",
        "status": "committed",
        "database_sha256_before": "4b7b6aa7913b415114f270b497141fc706a0c9f1dabf2fdbae7cd4db8110a391",
        "database_sha256_after": "e3c7d01dec04c6b7c6c8ea8dbe8fab11e0b3cdb9fea9c1280a927167a236f70b",
        "counts_before": {"textbook_rows": 49568, "fts_rows": 49568, "section_rows": 35777},
        "counts_after": {"textbook_rows": 50153, "fts_rows": 50153, "section_rows": 36322},
        "inserted_rows": 585,
        "source_count": 4,
        "integrity_check": "ok",
        "foreign_key_failures_unchanged": True,
        "per_source_fts_and_linkage_passed": True,
    }
    assert document["pre_ingest_backup"]["provider_uploaded"] is True
    assert document["pre_ingest_backup"]["provider_uploading"] is False
    assert document["pre_ingest_backup"]["drive_item_id_present"] is True
    assert document["pre_ingest_backup"]["restored_database_sha256"] == live_gate.EXPECTED_LIVE_DB_SHA256


def test_schema_rejects_open_execution_fields():
    document = copy.deepcopy(_gate())
    document["execution"]["skip_backup"] = True
    schema = json.loads(live_gate.SCHEMA_PATH.read_text(encoding="utf-8"))

    errors = list(Draft202012Validator(schema).iter_errors(document))

    assert errors
    assert any("Additional properties are not allowed" in error.message for error in errors)


def test_gate_rejects_source_or_phase_drift_even_when_resealed():
    document = copy.deepcopy(_gate())
    document["requested_sources"] = list(reversed(document["requested_sources"]))

    with pytest.raises(live_gate.LiveIngestGateError, match="schema violation"):
        live_gate.validate_gate_document(_reseal(document))

    document = copy.deepcopy(_gate())
    document["phase4_blocked"] = False
    with pytest.raises(live_gate.LiveIngestGateError, match="schema violation"):
        live_gate.validate_gate_document(_reseal(document))


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
