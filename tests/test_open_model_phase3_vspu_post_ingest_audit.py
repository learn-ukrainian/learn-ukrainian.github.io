"""Tests for the tracked text-free VSPU post-ingest audit."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_post_ingest_audit as audit


def _tracked() -> dict[str, object]:
    return json.loads(audit.DEFAULT_RECEIPT_PATH.read_text(encoding="utf-8"))


def _live_evidence() -> dict[str, object]:
    return {
        "sha256": audit.EXPECTED_POST_DB_SHA256,
        "counts": copy.deepcopy(audit.EXPECTED_COUNTS),
        "target_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
        "target_fts_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
        "target_section_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
        "target_linked_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
        "integrity_check": "ok",
        "journal_mode": "wal",
        "foreign_key_failure_count": audit.cutover.EXPECTED_FOREIGN_KEY_COUNT,
        "foreign_key_failure_sha256": audit.cutover.EXPECTED_FOREIGN_KEY_SHA256,
        "existing_corpus_fingerprint": "e" * 64,
    }


def _private_receipts() -> tuple[dict[str, object], dict[str, object]]:
    cutover_receipt = {
        "database": {
            "existing_corpus_fingerprint_before": "e" * 64,
            "existing_corpus_fingerprint_after": "e" * 64,
            "live_inode_preserved": True,
        }
    }
    backup_receipt = {
        "database": {
            "textbook_rows": audit.EXPECTED_COUNTS["textbook_rows"],
            "textbook_fts_rows": audit.EXPECTED_COUNTS["fts_rows"],
        }
    }
    return cutover_receipt, backup_receipt


def _valid_backup_receipt() -> dict[str, object]:
    return {
        "status": "VERIFIED_UPLOADED_SUCCESSOR_DATABASE",
        "database": {
            "successor_sha256": audit.EXPECTED_POST_DB_SHA256,
            "compressed_sha256": audit.EXPECTED_COMPRESSED_SHA256,
            "streamed_restore_sha256": audit.EXPECTED_POST_DB_SHA256,
            "gzip_integrity": True,
            "integrity_check": "ok",
            "live_inode_before": 123,
            "live_inode_after": 123,
            "foreign_key_failures": audit.cutover.EXPECTED_FOREIGN_KEY_COUNT,
            "foreign_key_failure_sha256": audit.cutover.EXPECTED_FOREIGN_KEY_SHA256,
            "textbook_rows": audit.EXPECTED_COUNTS["textbook_rows"],
            "textbook_fts_rows": audit.EXPECTED_COUNTS["fts_rows"],
            "textbook_section_rows": audit.EXPECTED_COUNTS["section_rows"],
            "textbook_sources": audit.EXPECTED_COUNTS["source_count"],
            "university_rows": audit.EXPECTED_COUNTS["university_rows"],
            "university_sources": audit.EXPECTED_COUNTS["university_source_count"],
            "vspu_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
            "vspu_fts_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
            "vspu_section_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
            "vspu_linked_rows": audit.cutover.EXPECTED_SOURCE_ROWS,
        },
        "custody": {
            "all_new_files_uploaded": True,
            "all_new_files_uploading": False,
            "all_new_files_provider_item_id_present": True,
            "all_new_files_readback_hash_match": True,
            "private_files_mode_0600": True,
            "predecessor_backup_preserved": True,
        },
        "authority": {
            "content_disposition": "contextual_only",
            "normative_rule_authority": False,
            "semantic_gold": False,
            "public_redistribution_authorized": False,
        },
        "phase_boundaries": {
            "database_ingest_complete": True,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "cutover_receipt": {
            "file_sha256": audit.EXPECTED_CUTOVER_FILE_SHA256,
            "body_receipt_sha256": audit.EXPECTED_CUTOVER_BODY_SHA256,
            "database_ingest_complete": True,
        },
    }


def _private_evidence_files(
    tmp_path: Path,
    *,
    cutover_mode: int = 0o600,
    backup_mode: int = 0o600,
    compressed_mode: int = 0o600,
) -> tuple[Path, Path, Path]:
    cutover_path = tmp_path / "cutover.json"
    backup_path = tmp_path / "backup.json"
    compressed_path = tmp_path / "sources.db.gz"
    cutover_path.write_text("{}", encoding="utf-8")
    backup_path.write_text(json.dumps(_valid_backup_receipt()), encoding="utf-8")
    compressed_path.write_bytes(b"fixture")
    cutover_path.chmod(cutover_mode)
    backup_path.chmod(backup_mode)
    compressed_path.chmod(compressed_mode)
    return cutover_path, backup_path, compressed_path


def _patch_private_checks(monkeypatch: pytest.MonkeyPatch, paths: tuple[Path, Path, Path]) -> list[Path]:
    cutover_path, backup_path, compressed_path = paths
    expected_hashes = {
        cutover_path: audit.EXPECTED_CUTOVER_FILE_SHA256,
        backup_path: audit.EXPECTED_BACKUP_RECEIPT_SHA256,
        compressed_path: audit.EXPECTED_COMPRESSED_SHA256,
    }
    monkeypatch.setattr(audit, "sha256_file", lambda path: expected_hashes[Path(path)])
    monkeypatch.setattr(
        audit.cutover,
        "validate_receipt",
        lambda _value: {"receipt_sha256": audit.EXPECTED_CUTOVER_BODY_SHA256},
    )
    monkeypatch.setattr(audit, "_streamed_restore_sha256", lambda _path: audit.EXPECTED_POST_DB_SHA256)
    monkeypatch.setattr(audit, "_uploaded", lambda _path: True)
    inspected: list[Path] = []
    monkeypatch.setattr(audit, "_drive_item_id", lambda path: inspected.append(Path(path)) or "item-id")
    return inspected


def _bind_live_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    live_database = tmp_path / "sources.db"
    live_database.write_bytes(b"live-database-fixture")
    monkeypatch.setattr(audit.cutover, "DEFAULT_LIVE_DB", live_database)
    return live_database


def test_schema_is_closed_and_valid() -> None:
    schema = json.loads(audit.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["phaseBoundaries"]["additionalProperties"] is False


def test_tracked_post_ingest_receipt_validates_and_is_text_free() -> None:
    receipt = audit.validate_receipt(_tracked())
    assert receipt["text_free"] is True
    assert receipt["provider_calls"] is False
    assert receipt["database"]["target_rows"] == 158
    assert receipt["custody"]["successor_backup_uploaded"] is True
    assert receipt["authority"]["content_disposition"] == "contextual_only"
    assert receipt["phase_boundaries"] == {
        "database_ingest_complete": True,
        "post_ingest_backup_complete": True,
        "source_universe_frozen": False,
        "source_coverage_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("database", "post_sha256"), "0" * 64, "schema violation"),
        (("custody", "successor_backup_uploaded"), False, "schema violation"),
        (("authority", "semantic_gold"), True, "schema violation"),
        (("phase_boundaries", "source_coverage_ready"), True, "schema violation"),
        (("phase_boundaries", "phase3_complete"), True, "schema violation"),
        (("phase_boundaries", "phase4_blocked"), False, "schema violation"),
    ],
)
def test_receipt_rejects_overclaim_or_identity_drift(
    path: tuple[str, str],
    value: object,
    message: str,
) -> None:
    broken = copy.deepcopy(_tracked())
    broken[path[0]][path[1]] = value
    broken["receipt_sha256"] = audit.receipt_sha256(broken)
    with pytest.raises(audit.VspuPostIngestAuditError, match=message):
        audit.validate_receipt(broken)


def test_receipt_rejects_runtime_binding_drift() -> None:
    broken = copy.deepcopy(_tracked())
    broken["bindings"]["implementation_sha256"] = "0" * 64
    broken["receipt_sha256"] = audit.receipt_sha256(broken)
    with pytest.raises(audit.VspuPostIngestAuditError, match="implementation binding drift"):
        audit.validate_receipt(broken)


def test_audit_rebinds_live_successor_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    live_database = _bind_live_database(monkeypatch, tmp_path)
    monkeypatch.setattr(audit, "_validate_private_evidence", lambda **_kwargs: _private_receipts())
    monkeypatch.setattr(audit.cutover, "_database_evidence", lambda _path: _live_evidence())

    receipt = audit.audit(
        database_path=live_database,
        cutover_receipt_path=tmp_path / "cutover.json",
        backup_receipt_path=tmp_path / "backup.json",
        compressed_backup_path=tmp_path / "sources.db.gz",
    )

    assert receipt["database"]["post_sha256"] == audit.EXPECTED_POST_DB_SHA256
    assert receipt["database"]["counts"] == audit.EXPECTED_COUNTS
    assert receipt["phase_boundaries"]["phase4_blocked"] is True


def test_audit_rejects_live_database_count_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    live_database = _bind_live_database(monkeypatch, tmp_path)
    evidence = _live_evidence()
    evidence["counts"] = {**audit.EXPECTED_COUNTS, "source_count": 189}
    monkeypatch.setattr(audit, "_validate_private_evidence", lambda **_kwargs: _private_receipts())
    monkeypatch.setattr(audit.cutover, "_database_evidence", lambda _path: evidence)

    with pytest.raises(audit.VspuPostIngestAuditError, match="counts drift"):
        audit.audit(
            database_path=live_database,
            cutover_receipt_path=tmp_path / "cutover.json",
            backup_receipt_path=tmp_path / "backup.json",
            compressed_backup_path=tmp_path / "sources.db.gz",
        )


def test_audit_rejects_nonlive_database_with_identical_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    live_database = _bind_live_database(monkeypatch, tmp_path)
    copied_database = tmp_path / "copied-sources.db"
    copied_database.write_bytes(live_database.read_bytes())
    monkeypatch.setattr(
        audit,
        "_validate_private_evidence",
        lambda **_kwargs: pytest.fail("private evidence must not be read for a nonlive database"),
    )

    with pytest.raises(audit.VspuPostIngestAuditError, match="restricted to the primary-checkout"):
        audit.audit(
            database_path=copied_database,
            cutover_receipt_path=tmp_path / "cutover.json",
            backup_receipt_path=tmp_path / "backup.json",
            compressed_backup_path=tmp_path / "sources.db.gz",
        )


def test_write_receipt_rejects_symlink_output(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("preserve", encoding="utf-8")
    output = tmp_path / "receipt.json"
    output.symlink_to(target)

    with pytest.raises(audit.VspuPostIngestAuditError, match="must not be a symlink"):
        audit.write_receipt(output, _tracked())

    assert target.read_text(encoding="utf-8") == "preserve"


def test_private_evidence_rebinds_all_three_drive_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _private_evidence_files(tmp_path)
    inspected = _patch_private_checks(monkeypatch, paths)

    cutover_receipt, backup_receipt = audit._validate_private_evidence(
        cutover_receipt_path=paths[0],
        backup_receipt_path=paths[1],
        compressed_backup_path=paths[2],
    )

    assert cutover_receipt["receipt_sha256"] == audit.EXPECTED_CUTOVER_BODY_SHA256
    assert backup_receipt["authority"]["semantic_gold"] is False
    assert inspected == [paths[0], paths[2], paths[1]]


@pytest.mark.parametrize(
    ("mode_argument", "artifact_index", "error_label"),
    [
        ("cutover_mode", 0, "cutover receipt"),
        ("backup_mode", 1, "backup receipt"),
        ("compressed_mode", 2, "compressed successor backup"),
    ],
)
def test_private_evidence_guards_each_artifact_before_hashing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode_argument: str,
    artifact_index: int,
    error_label: str,
) -> None:
    paths = _private_evidence_files(tmp_path, **{mode_argument: 0o644})
    hashes_attempted: list[Path] = []
    _patch_private_checks(monkeypatch, paths)
    expected_hashes = {
        paths[0]: audit.EXPECTED_CUTOVER_FILE_SHA256,
        paths[1]: audit.EXPECTED_BACKUP_RECEIPT_SHA256,
        paths[2]: audit.EXPECTED_COMPRESSED_SHA256,
    }
    monkeypatch.setattr(
        audit,
        "sha256_file",
        lambda path: hashes_attempted.append(Path(path)) or expected_hashes[Path(path)],
    )

    with pytest.raises(audit.VspuPostIngestAuditError, match=rf"{error_label} must be mode 0600"):
        audit._validate_private_evidence(
            cutover_receipt_path=paths[0],
            backup_receipt_path=paths[1],
            compressed_backup_path=paths[2],
        )
    assert paths[artifact_index] not in hashes_attempted


def test_private_evidence_rejects_backup_authority_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _private_evidence_files(tmp_path)
    backup_receipt = _valid_backup_receipt()
    backup_receipt["authority"]["semantic_gold"] = True
    paths[1].write_text(json.dumps(backup_receipt), encoding="utf-8")
    paths[1].chmod(0o600)
    _patch_private_checks(monkeypatch, paths)

    with pytest.raises(audit.VspuPostIngestAuditError, match="authority drift"):
        audit._validate_private_evidence(
            cutover_receipt_path=paths[0],
            backup_receipt_path=paths[1],
            compressed_backup_path=paths[2],
        )


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        ("custody", "all_new_files_uploaded", False, "does not confirm upload"),
        ("custody", "all_new_files_uploading", True, "reports active upload"),
        ("custody", "all_new_files_provider_item_id_present", False, "lacks provider identity"),
        ("custody", "all_new_files_readback_hash_match", False, "read-back proof failed"),
        ("custody", "predecessor_backup_preserved", False, "predecessor backup was not preserved"),
        ("cutover_receipt", "file_sha256", "0" * 64, "backup cutover file drift"),
        ("cutover_receipt", "body_receipt_sha256", "0" * 64, "backup cutover body drift"),
        ("database", "textbook_rows", 50_312, "database count drift"),
    ],
)
def test_private_evidence_rejects_custody_binding_or_count_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    section: str,
    field: str,
    value: object,
    message: str,
) -> None:
    paths = _private_evidence_files(tmp_path)
    backup_receipt = _valid_backup_receipt()
    backup_receipt[section][field] = value
    paths[1].write_text(json.dumps(backup_receipt), encoding="utf-8")
    paths[1].chmod(0o600)
    _patch_private_checks(monkeypatch, paths)

    with pytest.raises(audit.VspuPostIngestAuditError, match=message):
        audit._validate_private_evidence(
            cutover_receipt_path=paths[0],
            backup_receipt_path=paths[1],
            compressed_backup_path=paths[2],
        )
