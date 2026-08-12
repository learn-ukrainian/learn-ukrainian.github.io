"""Hermetic fixture tests for Saint Sophia database reconciliation."""

from __future__ import annotations

import copy
import json
import sqlite3
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_saint_sophia_db_reconciliation as reconciliation


def _row(source_id: str) -> dict[str, object]:
    return {
        "schema_version": "historical-source-record.v1", "collection_id": reconciliation.COLLECTION_ID,
        "source_record_id": source_id, "title": None, "source_url": None, "published": True,
        "original_transcription": None, "epidoc_text": None, "epidoc_interpretation": None,
        "interpretative_edition": None, "romanisation": None, "translation_ukr": None,
        "translation_eng": None, "commentary_ukr": None, "commentary_eng": None,
        "source_language_label": None, "source_writing_system_label": None, "min_year": None,
        "max_year": None, "disposition": "non_textual_or_no_text", "stage_label": None,
        "quality_flags": [], "metadata": {}, "raw_record_sha256": "a" * 64,
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, str]:
    jsonl = tmp_path / "saint-sophia.jsonl"
    identifiers = ["1", "2"]
    jsonl.write_text("".join(json.dumps(_row(identifier), separators=(",", ":")) + "\n" for identifier in identifiers), encoding="utf-8")
    id_hash = reconciliation._ids_sha256(identifiers)
    coverage = tmp_path / "coverage.json"
    coverage_value = {
        "public_inscription_count": 2, "id_set_sha256": id_hash,
        "output_hashes": {"historical_source_records.jsonl": reconciliation.sha256_file(jsonl)},
    }
    coverage.write_text(json.dumps(coverage_value), encoding="utf-8")
    database = tmp_path / "sources.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE stable_records (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO stable_records VALUES (1, 'fixture')")
    expected = reconciliation.sha256_file(database)
    collection = {
        "collection_id": reconciliation.COLLECTION_ID,
        "public_record_id_set_sha256": id_hash,
        "artifact_sha256": {
            "historical_source_records_jsonl": reconciliation.sha256_file(jsonl),
            "coverage_receipt_json": reconciliation.sha256_file(coverage),
        },
        "canonical_database": {"historical_source_rows": 2, "historical_fts_rows": 2, "sha256": "b" * 64},
    }
    monkeypatch.setattr(reconciliation, "EXPECTED_ROWS", 2)
    monkeypatch.setattr(reconciliation, "EXPECTED_ID_SET_SHA256", id_hash)
    monkeypatch.setattr(reconciliation, "EXPECTED_JSONL_SHA256", reconciliation.sha256_file(jsonl))
    monkeypatch.setattr(reconciliation, "EXPECTED_COVERAGE_SHA256", reconciliation.sha256_file(coverage))
    monkeypatch.setattr(reconciliation, "_denominator", lambda: (collection, "c" * 64))
    return database, jsonl, coverage, expected


def test_dry_run_is_text_free_and_does_not_mutate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    result = reconciliation.reconcile(
        database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
        coverage_receipt_path=coverage,
    )
    assert result["mode"] == "dry_run"
    assert result["text_free"] is True and result["provider_calls"] is False
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='historical_source_records'"
        ).fetchone() is None
        assert connection.execute("SELECT value FROM stable_records").fetchone()[0] == "fixture"


def test_numeric_ids_match_established_numeric_first_hash() -> None:
    assert reconciliation._ids_sha256(["2", "10"]) == reconciliation.ingest._sha256_lines(["2", "10"])


def test_candidate_apply_writes_private_receipt_and_preserves_non_historical_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    receipt_path = tmp_path / "private-receipt.json"
    receipt = reconciliation.reconcile(
        database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
        coverage_receipt_path=coverage, output_receipt_path=receipt_path, apply=True,
    )
    assert reconciliation.validate_receipt(receipt) == receipt
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM historical_source_records_fts").fetchone()[0] == 2
        assert connection.execute("SELECT value FROM stable_records").fetchone()[0] == "fixture"


def test_candidate_failure_keeps_live_database_and_output_receipt_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text("previous", encoding="utf-8")
    before_database = database.read_bytes()
    monkeypatch.setattr(
        reconciliation.ingest,
        "ingest",
        lambda **_kwargs: (_ for _ in ()).throw(reconciliation.historical_sources.HistoricalSourceError("fixture failure")),
    )
    with pytest.raises(reconciliation.SaintSophiaReconciliationError, match="fixture failure"):
        reconciliation.reconcile(database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl, coverage_receipt_path=coverage, output_receipt_path=receipt_path, apply=True)
    assert database.read_bytes() == before_database
    assert receipt_path.read_text(encoding="utf-8") == "previous"


def test_in_place_backup_bootstraps_missing_schema_and_preserves_inode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    inode = database.stat().st_ino
    receipt = reconciliation.reconcile(
        database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
        coverage_receipt_path=coverage, output_receipt_path=tmp_path / "receipt.json", apply_in_place=True,
    )
    assert receipt["mode"] == "in_place_sqlite_backup"
    assert database.stat().st_ino == inode
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 2
    assert not list(tmp_path.glob(".sources.db.saint-sophia-*"))
    assert not list(tmp_path.glob("*.candidate-wal"))
    assert not list(tmp_path.glob("*.candidate-shm"))


def test_in_place_backup_leaves_preexisting_zero_byte_live_sidecars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    wal, shm = reconciliation._sidecars(database)
    wal.touch()
    shm.touch()
    wal_inode, shm_inode = wal.stat().st_ino, shm.stat().st_ino
    reconciliation.reconcile(
        database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
        coverage_receipt_path=coverage, output_receipt_path=tmp_path / "receipt.json", apply_in_place=True,
    )
    assert wal.exists() and shm.exists()
    assert wal.stat().st_ino == wal_inode and shm.stat().st_ino == shm_inode
    assert wal.stat().st_size == 0
    assert not list(tmp_path.glob(".sources.db.saint-sophia-*"))


def test_in_place_transaction_rolls_back_on_postcondition_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    with sqlite3.connect(database) as connection:
        reconciliation.historical_sources.ensure_historical_source_schema(connection)
    expected = reconciliation.sha256_file(database)
    original = reconciliation._non_historical_fingerprint
    calls = 0

    def changed_fingerprint(connection: sqlite3.Connection) -> str:
        nonlocal calls
        calls += 1
        return original(connection) if calls == 1 else "0" * 64

    monkeypatch.setattr(reconciliation, "_non_historical_fingerprint", changed_fingerprint)
    with pytest.raises(reconciliation.SaintSophiaReconciliationError, match="non-historical"):
        reconciliation.reconcile(database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl, coverage_receipt_path=coverage, output_receipt_path=tmp_path / "never.json", apply_in_place=True)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 0
        assert connection.execute("SELECT value FROM stable_records").fetchone()[0] == "fixture"


def test_receipt_write_failure_restores_prestate_and_removes_output_and_temps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "missing-receipt.json"
    monkeypatch.setattr(
        reconciliation,
        "_atomic_write_private",
        lambda *_args: (_ for _ in ()).throw(OSError("fixture receipt failure")),
    )
    with pytest.raises(OSError, match="fixture receipt failure"):
        reconciliation.reconcile(
            database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
            coverage_receipt_path=coverage, output_receipt_path=output, apply=True,
        )
    assert reconciliation.sha256_file(database) == expected
    assert not output.exists()
    assert not list(tmp_path.glob(".sources.db.saint-sophia-*"))
    assert not list(tmp_path.glob("*.candidate-wal"))
    assert not list(tmp_path.glob("*.candidate-shm"))


def test_live_backup_failure_after_copy_restores_exact_prestate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "missing-receipt.json"
    original_backup = reconciliation._sqlite_backup
    interrupted = False

    def copy_then_fail(source: Path, target: Path) -> None:
        nonlocal interrupted
        original_backup(source, target)
        if target == database and not interrupted:
            interrupted = True
            raise reconciliation.SaintSophiaReconciliationError("backup interrupted after copy")

    monkeypatch.setattr(reconciliation, "_sqlite_backup", copy_then_fail)
    with pytest.raises(reconciliation.SaintSophiaReconciliationError, match="backup interrupted"):
        reconciliation.reconcile(
            database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl,
            coverage_receipt_path=coverage, output_receipt_path=output, apply_in_place=True,
        )
    assert reconciliation.sha256_file(database) == expected
    assert not output.exists()
    assert not list(tmp_path.glob(".sources.db.saint-sophia-*"))


def test_receipt_rejects_authority_or_boundary_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database, jsonl, coverage, expected = _fixture(tmp_path, monkeypatch)
    receipt = reconciliation.reconcile(database_path=database, expected_pre_db_sha256=expected, jsonl_path=jsonl, coverage_receipt_path=coverage, output_receipt_path=tmp_path / "receipt.json", apply=True)
    broken = copy.deepcopy(receipt)
    broken["provider_calls"] = True
    broken["receipt_sha256"] = reconciliation.receipt_sha256(broken)
    with pytest.raises(reconciliation.SaintSophiaReconciliationError):
        reconciliation.validate_receipt(broken)
    forged = copy.deepcopy(receipt)
    forged["bindings"]["saint_sophia_jsonl_sha256"] = "0" * 64
    forged["receipt_sha256"] = reconciliation.receipt_sha256(forged)
    with pytest.raises(reconciliation.SaintSophiaReconciliationError, match="JSONL binding drift"):
        reconciliation.validate_receipt(forged)
