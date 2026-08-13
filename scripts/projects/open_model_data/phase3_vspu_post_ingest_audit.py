#!/usr/bin/env python3
"""Verify and publish the text-free VSPU post-ingest/backup audit."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_db_cutover as cutover

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_VERSION = "phase3_vspu_post_ingest_audit_v1"
SCHEMA_PATH = DATA / "contracts/phase3_vspu_post_ingest_audit_v1.schema.json"
DEFAULT_RECEIPT_PATH = DATA / "admission/phase3_vspu_post_ingest_audit_v1.json"

EXPECTED_POST_DB_SHA256 = "de9e448896341cb33b0d73b3729ec966919f7aff2669183bcfc7295e7d5353b7"
EXPECTED_CUTOVER_FILE_SHA256 = "265099931f1aa8a2c60a000e80313980093af8790b58aa91e0b55caca71eba4f"
EXPECTED_CUTOVER_BODY_SHA256 = "a4542d7d1771738fba50fef12aa55548787ce238e9f2f3ca3776a24429e1ef24"
EXPECTED_BACKUP_RECEIPT_SHA256 = "d78d51073db46b8cd9202e2b30be93d691a8feb6f1cebb432e23000ec581e317"
EXPECTED_COMPRESSED_SHA256 = "c07318782a8ad924902ee7f89592cfd03ec17d47c3be183ea186b851edec92f2"
EXPECTED_PROMPT_V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
EXPECTED_COUNTS = cutover.COUNTS_AFTER
PRIVATE_FILE_MODE = 0o600


class VspuPostIngestAuditError(ValueError):
    """The post-ingest database or private backup evidence is incomplete."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VspuPostIngestAuditError(message)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise VspuPostIngestAuditError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"})
    ).hexdigest()


def _regular_file(path: Path, label: str, *, private: bool = False) -> None:
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise VspuPostIngestAuditError(f"cannot inspect {label}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    if private:
        require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")


def read_json(path: Path, label: str, *, private: bool = False) -> dict[str, Any]:
    _regular_file(path, label, private=private)
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuPostIngestAuditError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _drive_item_id(path: Path) -> str:
    try:
        return cutover._wait_for_drive_item_id(Path(path))
    except cutover.VspuDatabaseCutoverError as exc:
        raise VspuPostIngestAuditError("private backup lacks Google Drive provider identity") from exc


def _uploaded(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["mdls", "-raw", "-name", "kMDItemIsUploaded", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VspuPostIngestAuditError("cannot read Google Drive upload state") from exc
    return result.stdout.strip() == "1"


def _streamed_restore_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with gzip.open(path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise VspuPostIngestAuditError("successor backup is not a valid gzip stream") from exc
    return digest.hexdigest()


def _require_live_database(path: Path) -> Path:
    database_path = Path(path)
    expected_path = Path(cutover.DEFAULT_LIVE_DB)
    require(
        database_path.resolve() == expected_path.resolve(),
        "audit is restricted to the primary-checkout live sources database",
    )
    try:
        require(
            os.path.samefile(database_path, expected_path),
            "audit database is not the live sources database inode",
        )
    except OSError as exc:
        raise VspuPostIngestAuditError("cannot verify the live sources database inode") from exc
    return database_path


def _schema_validator() -> Draft202012Validator:
    schema = read_json(SCHEMA_PATH, "post-ingest schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    errors = sorted(_schema_validator().iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise VspuPostIngestAuditError(f"post-ingest schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "post-ingest receipt body hash drift")
    bindings = receipt["bindings"]
    require(bindings["implementation_sha256"] == sha256_file(Path(__file__).resolve()), "implementation binding drift")
    require(bindings["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(
        bindings["cutover_implementation_sha256"] == sha256_file(Path(cutover.__file__).resolve()),
        "cutover implementation binding drift",
    )
    require(bindings["cutover_schema_sha256"] == sha256_file(cutover.SCHEMA_PATH), "cutover schema binding drift")
    require(receipt["phase_boundaries"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["phase_boundaries"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["authority"]["semantic_gold"] is False, "receipt grants semantic gold")
    return receipt


def _validate_private_evidence(
    *,
    cutover_receipt_path: Path,
    backup_receipt_path: Path,
    compressed_backup_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _regular_file(cutover_receipt_path, "cutover receipt", private=True)
    require(sha256_file(cutover_receipt_path) == EXPECTED_CUTOVER_FILE_SHA256, "cutover receipt byte drift")
    cutover_receipt = cutover.validate_receipt(read_json(cutover_receipt_path, "cutover receipt", private=True))
    require(cutover_receipt["receipt_sha256"] == EXPECTED_CUTOVER_BODY_SHA256, "cutover body hash drift")
    require(_uploaded(cutover_receipt_path), "cutover receipt is still uploading")
    _drive_item_id(cutover_receipt_path)
    _regular_file(backup_receipt_path, "backup receipt", private=True)
    require(sha256_file(backup_receipt_path) == EXPECTED_BACKUP_RECEIPT_SHA256, "backup receipt byte drift")
    backup_receipt = read_json(backup_receipt_path, "backup receipt", private=True)
    require(backup_receipt.get("status") == "VERIFIED_UPLOADED_SUCCESSOR_DATABASE", "backup is not verified")
    _regular_file(compressed_backup_path, "compressed successor backup", private=True)
    require(sha256_file(compressed_backup_path) == EXPECTED_COMPRESSED_SHA256, "compressed backup byte drift")
    require(_streamed_restore_sha256(compressed_backup_path) == EXPECTED_POST_DB_SHA256, "backup restore hash drift")
    require(_uploaded(compressed_backup_path), "successor backup is still uploading")
    _drive_item_id(compressed_backup_path)
    require(_uploaded(backup_receipt_path), "backup receipt is still uploading")
    _drive_item_id(backup_receipt_path)
    database = backup_receipt.get("database", {})
    expected_backup_counts = {
        "textbook_rows": EXPECTED_COUNTS["textbook_rows"],
        "textbook_fts_rows": EXPECTED_COUNTS["fts_rows"],
        "textbook_section_rows": EXPECTED_COUNTS["section_rows"],
        "textbook_sources": EXPECTED_COUNTS["source_count"],
        "university_rows": EXPECTED_COUNTS["university_rows"],
        "university_sources": EXPECTED_COUNTS["university_source_count"],
        "vspu_rows": cutover.EXPECTED_SOURCE_ROWS,
        "vspu_fts_rows": cutover.EXPECTED_SOURCE_ROWS,
        "vspu_section_rows": cutover.EXPECTED_SOURCE_ROWS,
        "vspu_linked_rows": cutover.EXPECTED_SOURCE_ROWS,
    }
    require(database.get("successor_sha256") == EXPECTED_POST_DB_SHA256, "backup successor identity drift")
    require(database.get("compressed_sha256") == EXPECTED_COMPRESSED_SHA256, "backup compressed identity drift")
    require(database.get("streamed_restore_sha256") == EXPECTED_POST_DB_SHA256, "backup restore receipt drift")
    require(database.get("gzip_integrity") is True, "backup receipt lacks gzip integrity")
    require(database.get("integrity_check") == "ok", "backup receipt integrity drift")
    require(database.get("live_inode_before") == database.get("live_inode_after"), "backup receipt inode drift")
    require(
        database.get("foreign_key_failures") == cutover.EXPECTED_FOREIGN_KEY_COUNT
        and database.get("foreign_key_failure_sha256") == cutover.EXPECTED_FOREIGN_KEY_SHA256,
        "backup receipt foreign-key baseline drift",
    )
    require(
        all(database.get(key) == value for key, value in expected_backup_counts.items()),
        "backup receipt database count drift",
    )
    custody = backup_receipt.get("custody", {})
    require(custody.get("all_new_files_uploaded") is True, "backup receipt does not confirm upload")
    require(custody.get("all_new_files_uploading") is False, "backup receipt reports active upload")
    require(custody.get("all_new_files_provider_item_id_present") is True, "backup receipt lacks provider identity")
    require(custody.get("all_new_files_readback_hash_match") is True, "backup receipt read-back proof failed")
    require(custody.get("private_files_mode_0600") is True, "backup receipt private-mode proof failed")
    require(custody.get("predecessor_backup_preserved") is True, "predecessor backup was not preserved")
    require(
        backup_receipt.get("authority")
        == {
            "content_disposition": "contextual_only",
            "normative_rule_authority": False,
            "semantic_gold": False,
            "public_redistribution_authorized": False,
        },
        "backup receipt authority drift",
    )
    require(
        backup_receipt.get("phase_boundaries")
        == {
            "database_ingest_complete": True,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "backup receipt phase-boundary drift",
    )
    cutover_binding = backup_receipt.get("cutover_receipt", {})
    require(cutover_binding.get("file_sha256") == EXPECTED_CUTOVER_FILE_SHA256, "backup cutover file drift")
    require(cutover_binding.get("body_receipt_sha256") == EXPECTED_CUTOVER_BODY_SHA256, "backup cutover body drift")
    require(cutover_binding.get("database_ingest_complete") is True, "backup does not bind completed cutover")
    return cutover_receipt, backup_receipt


def audit(
    *,
    database_path: Path,
    cutover_receipt_path: Path,
    backup_receipt_path: Path,
    compressed_backup_path: Path,
) -> dict[str, Any]:
    database_path = _require_live_database(database_path)
    cutover_receipt, backup_receipt = _validate_private_evidence(
        cutover_receipt_path=Path(cutover_receipt_path),
        backup_receipt_path=Path(backup_receipt_path),
        compressed_backup_path=Path(compressed_backup_path),
    )
    try:
        evidence = cutover._database_evidence(Path(database_path))
    except cutover.VspuDatabaseCutoverError as exc:
        raise VspuPostIngestAuditError(str(exc)) from exc
    require(evidence["sha256"] == EXPECTED_POST_DB_SHA256, "live successor database identity drift")
    require(evidence["counts"] == EXPECTED_COUNTS, "live successor database counts drift")
    require(evidence["target_rows"] == cutover.EXPECTED_SOURCE_ROWS, "live VSPU row denominator drift")
    require(evidence["target_fts_rows"] == cutover.EXPECTED_SOURCE_ROWS, "live VSPU FTS parity drift")
    require(evidence["target_section_rows"] == cutover.EXPECTED_SOURCE_ROWS, "live VSPU section denominator drift")
    require(evidence["target_linked_rows"] == cutover.EXPECTED_SOURCE_ROWS, "live VSPU linkage drift")
    require(evidence["integrity_check"] == "ok", "live successor integrity check failed")
    require(
        evidence["foreign_key_failure_count"] == cutover.EXPECTED_FOREIGN_KEY_COUNT
        and evidence["foreign_key_failure_sha256"] == cutover.EXPECTED_FOREIGN_KEY_SHA256,
        "live successor foreign-key baseline drift",
    )
    cutover_db = cutover_receipt["database"]
    require(
        evidence["existing_corpus_fingerprint"]
        == cutover_db["existing_corpus_fingerprint_after"]
        == cutover_db["existing_corpus_fingerprint_before"],
        "pre-existing corpus fingerprint drift",
    )
    backup_db = backup_receipt["database"]
    require(backup_db.get("textbook_rows") == evidence["counts"]["textbook_rows"], "backup row count drift")
    require(backup_db.get("textbook_fts_rows") == evidence["counts"]["fts_rows"], "backup FTS count drift")
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "provider_calls": False,
        "bindings": {
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "schema_sha256": sha256_file(SCHEMA_PATH),
            "cutover_implementation_sha256": sha256_file(Path(cutover.__file__).resolve()),
            "cutover_schema_sha256": sha256_file(cutover.SCHEMA_PATH),
            "phase3_reboot_prompt_v3_sha256": EXPECTED_PROMPT_V3_SHA256,
            "cutover_receipt_file_sha256": EXPECTED_CUTOVER_FILE_SHA256,
            "cutover_receipt_body_sha256": EXPECTED_CUTOVER_BODY_SHA256,
            "backup_receipt_file_sha256": EXPECTED_BACKUP_RECEIPT_SHA256,
            "compressed_backup_sha256": EXPECTED_COMPRESSED_SHA256,
        },
        "database": {
            "pre_sha256": cutover.EXPECTED_PRE_DB_SHA256,
            "post_sha256": evidence["sha256"],
            "counts": evidence["counts"],
            "target_rows": evidence["target_rows"],
            "target_fts_rows": evidence["target_fts_rows"],
            "target_section_rows": evidence["target_section_rows"],
            "target_linked_rows": evidence["target_linked_rows"],
            "foreign_key_failure_count": evidence["foreign_key_failure_count"],
            "foreign_key_failure_sha256": evidence["foreign_key_failure_sha256"],
            "existing_corpus_fingerprint_unchanged": True,
            "integrity_check": evidence["integrity_check"],
            "journal_mode": evidence["journal_mode"],
            "live_inode_preserved": cutover_db["live_inode_preserved"],
        },
        "custody": {
            "successor_backup_uploaded": True,
            "successor_backup_uploading": False,
            "successor_backup_provider_identity_present": True,
            "successor_backup_gzip_integrity": True,
            "successor_backup_streamed_restore_sha256": EXPECTED_POST_DB_SHA256,
            "private_receipts_mode_0600": True,
            "predecessor_backup_preserved_at_successor_backup_time": True,
        },
        "authority": {
            "source_id": cutover.SOURCE_ID,
            "content_disposition": "contextual_only",
            "allowed_lanes": ["contextual_retrieval", "corpus_ingest"],
            "normative_rule_authority": False,
            "semantic_gold": False,
            "public_redistribution_authorized": False,
        },
        "phase_boundaries": {
            "database_ingest_complete": True,
            "post_ingest_backup_complete": True,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    return validate_receipt({**body, "receipt_sha256": receipt_sha256(body)})


def write_receipt(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    require(path.parent.is_dir() and not path.parent.is_symlink(), "receipt parent must be a real directory")
    require(not path.is_symlink(), "receipt output must not be a symlink")
    payload = canonical_bytes(value)
    if path.exists():
        require(path.read_bytes() == payload, "refusing to overwrite a different immutable audit receipt")
        return
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--cutover-receipt", type=Path)
    parser.add_argument("--backup-receipt", type=Path)
    parser.add_argument("--compressed-backup", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_RECEIPT_PATH)
    parser.add_argument("--check", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            validate_receipt(read_json(args.check, "tracked post-ingest receipt"))
            print(json.dumps({"ok": True, "mode": "check"}, separators=(",", ":")))
            return 0
        require(
            all((args.database, args.cutover_receipt, args.backup_receipt, args.compressed_backup)),
            "database and all private evidence paths are required",
        )
        receipt = audit(
            database_path=args.database,
            cutover_receipt_path=args.cutover_receipt,
            backup_receipt_path=args.backup_receipt,
            compressed_backup_path=args.compressed_backup,
        )
        write_receipt(args.output, receipt)
        print(json.dumps({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}, separators=(",", ":")))
    except VspuPostIngestAuditError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
