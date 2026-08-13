#!/usr/bin/env python3
"""Rehearse and apply the exact one-source VSPU ``sources.db`` cutover.

The default is a read-only plan. ``--apply-in-place`` first rebuilds the exact
postimage on a disposable SQLite copy, validates the complete VSPU source and
the recoverable Google Drive preimage, then copies the rehearsed postimage into
the existing live inode. Any failure after cutover starts restores an exact
private predecessor copy before returning an error.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.guardrails.worktree_containment import resolve_main_root
from scripts.ingest import incremental_textbook_ingest as textbook_ingest
from scripts.projects.open_model_data import phase3_vspu_source_materialization as materialization
from scripts.projects.open_model_data import university_source_policy

ROOT = Path(__file__).resolve().parents[3]
PRIMARY_ROOT = resolve_main_root(ROOT) or ROOT
SCHEMA_VERSION = "phase3_vspu_db_cutover_v1"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_vspu_db_cutover_v1.schema.json"
MATERIALIZATION_PATH = ROOT / "data/projects/open_model_data/admission/phase3_vspu_source_materialization_v1.json"
ADDITIVE_POLICY_PATH = (
    ROOT / "data/projects/open_model_data/admission/phase3_vspu_additive_university_source_policy_v3.json"
)
DEFAULT_LIVE_DB = PRIMARY_ROOT / "data/sources.db"

SOURCE_ID = "uni-ukrmova-sulm-attestation-vspu-2021"
EXPECTED_SOURCE_ROWS = 158
EXPECTED_PRE_DB_SHA256 = "9fc3bd9e8b5692b5a4f4f0974268ba8031e2ba46099670b1461130be39d61a29"
EXPECTED_FOREIGN_KEY_COUNT = 134_836
EXPECTED_FOREIGN_KEY_SHA256 = "9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb"
EXPECTED_MATERIALIZATION_FILE_SHA256 = "f023fab75ebc82ecb84a88a487f2ef2d477722035a82c5c23c18431b11e8b45c"
EXPECTED_ADDITIVE_POLICY_SHA256 = "c2d2d094931751fefba0dd14143a83b344dc59f52b36414b165be920d29309f5"
EXPECTED_PRIVATE_JSONL_SHA256 = "babb8a266a7d6720d68fb960f7848aace03f646f1ede5b30de2831f7cbb85dc8"
EXPECTED_PREIMAGE_BACKUP_RECEIPT_SHA256 = "e53355f2d6c221c7bfe9cbba63b4055982f286b26d72618e8b9a393231febb0a"
EXPECTED_COMPRESSED_PREIMAGE_SHA256 = "ba41ce56eabb2d72856c906cd498ec168b3036bbe79b9264bb074dbc87831d81"
EXPECTED_COMPLETE_POLICY_V4_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
EXPECTED_PROMPT_V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
EXPECTED_PROMPT_V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
COUNTS_BEFORE = {
    "textbook_rows": 50_153,
    "fts_rows": 50_153,
    "section_rows": 36_322,
    "source_count": 187,
    "university_rows": 4_078,
    "university_source_count": 20,
}
COUNTS_AFTER = {
    "textbook_rows": 50_311,
    "fts_rows": 50_311,
    "section_rows": 36_480,
    "source_count": 188,
    "university_rows": 4_236,
    "university_source_count": 21,
}
PRIVATE_FILE_MODE = 0o600


class VspuDatabaseCutoverError(ValueError):
    """The VSPU cutover inputs, rehearsal, or database state are unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VspuDatabaseCutoverError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise VspuDatabaseCutoverError(f"cannot read file: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_bytes(body))


def _regular_file(path: Path, label: str, *, private: bool = False) -> None:
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise VspuDatabaseCutoverError(f"missing {label}: {path}") from exc
    require(
        stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(),
        f"{label} must be a regular file",
    )
    if private:
        require(
            stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE,
            f"{label} must be mode 0600",
        )


def _read_json(path: Path, label: str, *, private: bool = False) -> dict[str, Any]:
    _regular_file(path, label, private=private)
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuDatabaseCutoverError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _drive_item_id(path: Path) -> str:
    resolved = Path(path).resolve()
    cloud_storage = Path.home() / "Library/CloudStorage"
    try:
        roots = [
            candidate.resolve()
            for candidate in cloud_storage.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise VspuDatabaseCutoverError("cannot inspect configured Google Drive mounts") from exc
    matches = [root for root in roots if resolved.is_relative_to(root)]
    require(len(matches) == 1, "private artifact is not inside exactly one Google Drive mount")
    try:
        result = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VspuDatabaseCutoverError("private artifact lacks Google Drive provider identity") from exc
    item_id = result.stdout.strip()
    require(bool(item_id), "private artifact has an empty Google Drive provider identity")
    return item_id


def _streamed_gzip_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with gzip.open(path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise VspuDatabaseCutoverError("compressed preimage is not a readable gzip stream") from exc
    return digest.hexdigest()


def _validate_materialization_and_policy(
    *,
    materialization_path: Path,
    additive_policy_path: Path,
    private_jsonl_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    require(
        sha256_file(materialization_path) == EXPECTED_MATERIALIZATION_FILE_SHA256,
        "VSPU materialization receipt byte drift",
    )
    try:
        materialization_receipt = materialization.validate_receipt(
            _read_json(materialization_path, "VSPU materialization receipt")
        )
    except materialization.VspuSourceMaterializationError as exc:
        raise VspuDatabaseCutoverError(str(exc)) from exc
    require(
        materialization_receipt["source_id"] == SOURCE_ID,
        "VSPU materialization source identity drift",
    )
    require(
        materialization_receipt["private_artifact"]["source_unit_count"] == EXPECTED_SOURCE_ROWS,
        "VSPU materialization row denominator drift",
    )
    require(
        materialization_receipt["gates"]["database_ingest_authorized"] is False,
        "materialization receipt unexpectedly authorizes database mutation",
    )

    require(
        sha256_file(additive_policy_path) == EXPECTED_ADDITIVE_POLICY_SHA256,
        "VSPU additive policy byte drift",
    )
    try:
        policy, policy_sha256 = university_source_policy.load_policy(additive_policy_path)
    except university_source_policy.UniversitySourcePolicyError as exc:
        raise VspuDatabaseCutoverError(str(exc)) from exc
    require(policy_sha256 == EXPECTED_ADDITIVE_POLICY_SHA256, "VSPU additive policy hash drift")
    require(policy["source_count"] == 1, "VSPU additive policy is not a one-source policy")
    entry = policy["sources"][0]
    require(entry["source_file"] == SOURCE_ID, "VSPU additive policy source drift")
    require(entry["content_disposition"] == "contextual_only", "VSPU disposition drift")
    require(
        entry["allowed_lanes"] == ["contextual_retrieval", "corpus_ingest"],
        "VSPU allowed-lane drift",
    )

    _regular_file(private_jsonl_path, "private VSPU JSONL", private=True)
    require(
        Path(private_jsonl_path).name == f"{SOURCE_ID}.jsonl",
        "private VSPU JSONL filename drift",
    )
    require(
        sha256_file(private_jsonl_path) == EXPECTED_PRIVATE_JSONL_SHA256,
        "private VSPU JSONL byte drift",
    )
    _drive_item_id(private_jsonl_path)
    try:
        rows = university_source_policy.load_jsonl_rows(private_jsonl_path)
        admission = university_source_policy.require_source_admission(
            source_file=SOURCE_ID,
            jsonl_path=private_jsonl_path,
            policy_path=additive_policy_path,
            lane="corpus_ingest",
        )
    except university_source_policy.UniversitySourcePolicyError as exc:
        raise VspuDatabaseCutoverError(str(exc)) from exc
    require(len(rows) == EXPECTED_SOURCE_ROWS, "private VSPU JSONL row denominator drift")
    require(admission["content_disposition"] == "contextual_only", "VSPU admission drift")
    require("linguistic_rule_evidence" not in admission["allowed_lanes"], "VSPU policy grants rule authority")
    return materialization_receipt, policy


def _validate_preimage_backup(*, receipt_path: Path, compressed_path: Path) -> dict[str, Any]:
    require(
        sha256_file(receipt_path) == EXPECTED_PREIMAGE_BACKUP_RECEIPT_SHA256,
        "preimage backup receipt byte drift",
    )
    receipt = _read_json(receipt_path, "preimage backup receipt", private=True)
    _regular_file(compressed_path, "compressed preimage database", private=True)
    require(
        sha256_file(compressed_path) == EXPECTED_COMPRESSED_PREIMAGE_SHA256,
        "compressed preimage database byte drift",
    )
    _drive_item_id(receipt_path)
    _drive_item_id(compressed_path)
    database = receipt.get("database", {})
    custody = receipt.get("custody", {})
    require(
        receipt.get("schema_version") == "phase3_saint_sophia_db_drive_backup_receipt_v1",
        "preimage backup receipt schema drift",
    )
    require(
        receipt.get("status") == "VERIFIED_UPLOADED_SUCCESSOR_DATABASE",
        "preimage backup is not provider-verified",
    )
    require(database.get("successor_sha256") == EXPECTED_PRE_DB_SHA256, "backup database identity drift")
    require(
        database.get("compressed_sha256") == EXPECTED_COMPRESSED_PREIMAGE_SHA256,
        "backup compressed identity drift",
    )
    require(
        database.get("streamed_restore_sha256") == EXPECTED_PRE_DB_SHA256,
        "backup receipt restore identity drift",
    )
    require(database.get("gzip_integrity") is True, "backup receipt lacks gzip integrity")
    require(database.get("integrity_check") == "ok", "backed-up database integrity is not ok")
    expected_receipt_counts = {
        "textbook_rows": database.get("textbook_rows"),
        "fts_rows": database.get("textbook_fts_rows"),
        "section_rows": database.get("textbook_section_rows"),
        "source_count": database.get("textbook_sources"),
        "university_rows": database.get("university_rows"),
        "university_source_count": database.get("university_sources"),
    }
    require(expected_receipt_counts == COUNTS_BEFORE, "backup database count drift")
    require(
        database.get("foreign_key_failures") == EXPECTED_FOREIGN_KEY_COUNT
        and database.get("foreign_key_failure_sha256") == EXPECTED_FOREIGN_KEY_SHA256,
        "backup foreign-key baseline drift",
    )
    require(custody.get("all_new_files_uploaded") is True, "preimage backup is not uploaded")
    require(custody.get("all_new_files_uploading") is False, "preimage backup is still uploading")
    require(custody.get("all_new_files_readback_hash_match") is True, "backup read-back proof failed")
    require(custody.get("predecessor_backup_preserved") is True, "predecessor backup was not preserved")
    require(
        _streamed_gzip_sha256(compressed_path) == EXPECTED_PRE_DB_SHA256,
        "compressed preimage streamed restore hash drift",
    )
    return receipt


def _foreign_key_evidence(connection: sqlite3.Connection) -> tuple[int, str]:
    failures = sorted(tuple(row) for row in connection.execute("PRAGMA foreign_key_check"))
    return len(failures), sha256_bytes(canonical_json(failures).encode("utf-8"))


def _database_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "textbook_rows": connection.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
        "fts_rows": connection.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
        "section_rows": connection.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
        "source_count": connection.execute("SELECT COUNT(DISTINCT source_file) FROM textbooks").fetchone()[0],
        "university_rows": connection.execute("SELECT COUNT(*) FROM textbooks WHERE grade='university'").fetchone()[0],
        "university_source_count": connection.execute(
            "SELECT COUNT(DISTINCT source_file) FROM textbooks WHERE grade='university'"
        ).fetchone()[0],
    }


def _hash_rows(digest: Any, label: str, rows: Iterable[Sequence[Any]]) -> None:
    digest.update(f"{label}\n".encode())
    for row in rows:
        digest.update(canonical_bytes(list(row)))


def _existing_corpus_fingerprint(connection: sqlite3.Connection) -> str:
    """Hash every pre-existing textbook row plus unrelated table structure/counts."""
    digest = hashlib.sha256()
    schema_rows = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    )
    _hash_rows(digest, "schema", schema_rows)
    _hash_rows(
        digest,
        "existing_textbooks",
        connection.execute(
            "SELECT * FROM textbooks WHERE source_file<>? ORDER BY id",
            (SOURCE_ID,),
        ),
    )
    _hash_rows(
        digest,
        "existing_textbook_sections",
        connection.execute(
            "SELECT * FROM textbook_sections WHERE source_file<>? ORDER BY section_id",
            (SOURCE_ID,),
        ),
    )
    unrelated_tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' "
            "AND name NOT IN ('textbooks','textbook_sections') "
            "AND name NOT LIKE 'textbooks_fts%' ORDER BY name"
        )
    ]
    counts = []
    for table in unrelated_tables:
        quoted = table.replace('"', '""')
        counts.append((table, connection.execute(f'SELECT COUNT(*) FROM "{quoted}"').fetchone()[0]))
    _hash_rows(digest, "unrelated_table_counts", counts)
    return digest.hexdigest()


def _database_evidence(path: Path) -> dict[str, Any]:
    _regular_file(path, "database")
    uri = f"file:{Path(path).resolve()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=30.0) as connection:
            counts = _database_counts(connection)
            target_rows = connection.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file=?",
                (SOURCE_ID,),
            ).fetchone()[0]
            target_fts_rows = connection.execute(
                "SELECT COUNT(*) FROM textbooks_fts AS f JOIN textbooks AS t ON t.id=f.rowid WHERE t.source_file=?",
                (SOURCE_ID,),
            ).fetchone()[0]
            target_sections = connection.execute(
                "SELECT COUNT(*) FROM textbook_sections WHERE source_file=?",
                (SOURCE_ID,),
            ).fetchone()[0]
            target_links = connection.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
                (SOURCE_ID,),
            ).fetchone()[0]
            foreign_count, foreign_hash = _foreign_key_evidence(connection)
            integrity_rows = [str(row[0]) for row in connection.execute("PRAGMA integrity_check")]
            return {
                "sha256": sha256_file(path),
                "counts": counts,
                "target_rows": target_rows,
                "target_fts_rows": target_fts_rows,
                "target_section_rows": target_sections,
                "target_linked_rows": target_links,
                "foreign_key_failure_count": foreign_count,
                "foreign_key_failure_sha256": foreign_hash,
                "existing_corpus_fingerprint": _existing_corpus_fingerprint(connection),
                "integrity_check": "ok" if integrity_rows == ["ok"] else integrity_rows,
                "journal_mode": str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower(),
            }
    except sqlite3.Error as exc:
        raise VspuDatabaseCutoverError(f"cannot inspect database: {exc}") from exc


def _validate_pre_database(evidence: Mapping[str, Any]) -> None:
    require(evidence["sha256"] == EXPECTED_PRE_DB_SHA256, "live database preimage SHA-256 drift")
    require(evidence["counts"] == COUNTS_BEFORE, "live database pre-count drift")
    require(evidence["target_rows"] == 0, "single-use cutover is stale: VSPU rows already exist")
    require(evidence["target_fts_rows"] == 0, "single-use cutover is stale: VSPU FTS rows exist")
    require(evidence["target_section_rows"] == 0, "single-use cutover is stale: VSPU sections exist")
    require(evidence["target_linked_rows"] == 0, "single-use cutover is stale: VSPU links exist")
    require(evidence["integrity_check"] == "ok", "live database integrity check is not ok")
    require(evidence["journal_mode"] == "wal", "live database journal-mode drift")
    require(
        evidence["foreign_key_failure_count"] == EXPECTED_FOREIGN_KEY_COUNT
        and evidence["foreign_key_failure_sha256"] == EXPECTED_FOREIGN_KEY_SHA256,
        "live database foreign-key baseline drift",
    )


def _validate_post_database(after: Mapping[str, Any], before: Mapping[str, Any]) -> None:
    require(after["counts"] == COUNTS_AFTER, "VSPU post-count drift")
    require(after["target_rows"] == EXPECTED_SOURCE_ROWS, "VSPU row denominator drift")
    require(after["target_fts_rows"] == EXPECTED_SOURCE_ROWS, "VSPU FTS parity drift")
    require(after["target_section_rows"] == EXPECTED_SOURCE_ROWS, "VSPU section denominator drift")
    require(after["target_linked_rows"] == EXPECTED_SOURCE_ROWS, "VSPU section-link parity drift")
    require(after["integrity_check"] == "ok", "post-ingest database integrity check is not ok")
    require(after["journal_mode"] == "wal", "post-ingest database journal-mode drift")
    require(
        (
            after["foreign_key_failure_count"],
            after["foreign_key_failure_sha256"],
        )
        == (
            before["foreign_key_failure_count"],
            before["foreign_key_failure_sha256"],
        ),
        "VSPU ingest changed the foreign-key baseline",
    )
    require(
        after["existing_corpus_fingerprint"] == before["existing_corpus_fingerprint"],
        "VSPU ingest changed pre-existing corpus evidence",
    )


def _candidate_path(live_path: Path) -> Path:
    fd, candidate = tempfile.mkstemp(
        dir=live_path.parent,
        prefix=f".{live_path.name}.vspu-",
        suffix=".candidate",
    )
    os.close(fd)
    os.chmod(candidate, PRIVATE_FILE_MODE)
    return Path(candidate)


def _sidecars(path: Path) -> tuple[Path, Path]:
    return path.with_name(f"{path.name}-wal"), path.with_name(f"{path.name}-shm")


def _reject_nonempty_wal(path: Path) -> None:
    wal, _ = _sidecars(path)
    require(not wal.exists() or wal.stat().st_size == 0, "database has a non-empty WAL")


def _require_empty_or_absent_wal(path: Path) -> None:
    wal, _ = _sidecars(path)
    require(not wal.exists() or wal.stat().st_size == 0, "database WAL remains non-empty")


def _cleanup_sidecars(path: Path) -> None:
    for sidecar in _sidecars(path):
        sidecar.unlink(missing_ok=True)


def _sqlite_backup(source: Path, target: Path) -> None:
    source_uri = f"file:{Path(source).resolve()}?mode=ro"
    try:
        with sqlite3.connect(source_uri, uri=True) as source_connection, sqlite3.connect(target) as target_connection:
            source_connection.backup(target_connection)
            target_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error as exc:
        raise VspuDatabaseCutoverError(f"SQLite online backup failed: {exc}") from exc


def _restore_exact_prestate(rollback: Path, target: Path, expected_sha256: str) -> None:
    _sqlite_backup(rollback, target)
    _require_empty_or_absent_wal(target)
    if sha256_file(target) != expected_sha256:
        with rollback.open("rb") as source, target.open("r+b") as destination:
            destination.seek(0)
            destination.truncate(0)
            shutil.copyfileobj(source, destination)
            destination.flush()
            os.fsync(destination.fileno())
    _require_empty_or_absent_wal(target)
    require(sha256_file(target) == expected_sha256, "rollback did not restore exact prestate")


def _atomic_write_private(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    parent = path.parent
    require(parent.is_dir() and not parent.is_symlink(), "receipt parent must be a real directory")
    require(not path.is_symlink(), "receipt output must not be a symlink")
    payload = canonical_bytes(value)
    if path.exists():
        _regular_file(path, "existing private receipt", private=True)
        require(path.read_bytes() == payload, "refusing to overwrite an immutable private receipt")
        return
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, PRIVATE_FILE_MODE)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _validate_rehearsal_receipt(path: Path) -> dict[str, Any]:
    receipt = _read_json(path, "copied-database rehearsal receipt", private=True)
    require(receipt.get("schema_version") == "incremental-textbook-ingest.v2", "rehearsal schema drift")
    require(receipt.get("status") == "committed", "copied-database rehearsal did not commit")
    require(
        receipt.get("execution_scope") == "copied_database_rehearsal",
        "receipt is not a copied-database rehearsal",
    )
    require(receipt.get("requested_replace_sources") == [SOURCE_ID], "rehearsal source-set drift")
    require(receipt.get("requested_quarantine_sources") == [], "rehearsal quarantined a source")
    require(
        receipt.get("university_source_policy_sha256") == EXPECTED_ADDITIVE_POLICY_SHA256,
        "rehearsal policy binding drift",
    )
    require(
        receipt.get("before") == {key: COUNTS_BEFORE[key] for key in ("textbook_rows", "fts_rows", "section_rows")},
        "rehearsal pre-count drift",
    )
    require(
        receipt.get("after_transaction")
        == {key: COUNTS_AFTER[key] for key in ("textbook_rows", "fts_rows", "section_rows")},
        "rehearsal post-count drift",
    )
    require(receipt.get("integrity_check") == "ok", "rehearsal integrity check failed")
    require(receipt.get("foreign_key_failures_unchanged") is True, "rehearsal foreign-key baseline changed")
    require(
        receipt.get("foreign_key_failure_count_before") == EXPECTED_FOREIGN_KEY_COUNT
        and receipt.get("foreign_key_failure_count_after") == EXPECTED_FOREIGN_KEY_COUNT,
        "rehearsal foreign-key count drift",
    )
    require(
        receipt.get("foreign_key_failure_hash_before") == EXPECTED_FOREIGN_KEY_SHA256
        and receipt.get("foreign_key_failure_hash_after") == EXPECTED_FOREIGN_KEY_SHA256,
        "rehearsal foreign-key hash drift",
    )
    per_source = receipt.get("per_source")
    require(isinstance(per_source, list) and len(per_source) == 1, "rehearsal per-source shape drift")
    source = per_source[0]
    require(source.get("source_file") == SOURCE_ID, "rehearsal per-source identity drift")
    require(source.get("inserted_rows") == EXPECTED_SOURCE_ROWS, "rehearsal row-count drift")
    require(source.get("section_rows") == EXPECTED_SOURCE_ROWS, "rehearsal section-count drift")
    require(source.get("linked_rows") == EXPECTED_SOURCE_ROWS, "rehearsal linkage drift")
    require(source.get("section_policy") == "exact_page_labels", "rehearsal section-policy drift")
    require(source.get("fts", {}).get("indexed_rows") == EXPECTED_SOURCE_ROWS, "rehearsal FTS-count drift")
    require(source.get("fts", {}).get("parity") is True, "rehearsal FTS parity failed")
    admission = source.get("university_source_policy", {})
    require(admission.get("content_disposition") == "contextual_only", "rehearsal disposition drift")
    require(
        "linguistic_rule_evidence" not in admission.get("allowed_lanes", []),
        "rehearsal grants rule-authority lane",
    )
    return receipt


def _build_receipt(
    *,
    rehearsal_receipt_path: Path,
    rehearsal: Mapping[str, Any],
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    inode_preserved: bool,
) -> dict[str, Any]:
    source = rehearsal["per_source"][0]
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "provider_calls": False,
        "mode": "in_place_sqlite_backup",
        "source_id": SOURCE_ID,
        "bindings": {
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "schema_sha256": sha256_file(SCHEMA_PATH),
            "incremental_ingest_implementation_sha256": sha256_file(Path(textbook_ingest.__file__).resolve()),
            "phase3_reboot_prompt_v3_sha256": EXPECTED_PROMPT_V3_SHA256,
            "phase3_recovery_prompt_v2_sha256": EXPECTED_PROMPT_V2_SHA256,
            "complete_source_policy_v4_sha256": EXPECTED_COMPLETE_POLICY_V4_SHA256,
            "vspu_materialization_receipt_sha256": EXPECTED_MATERIALIZATION_FILE_SHA256,
            "vspu_additive_policy_sha256": EXPECTED_ADDITIVE_POLICY_SHA256,
            "private_jsonl_sha256": EXPECTED_PRIVATE_JSONL_SHA256,
            "preimage_backup_receipt_sha256": EXPECTED_PREIMAGE_BACKUP_RECEIPT_SHA256,
            "compressed_preimage_database_sha256": EXPECTED_COMPRESSED_PREIMAGE_SHA256,
        },
        "preimage_backup": {
            "status": "VERIFIED_UPLOADED_SUCCESSOR_DATABASE",
            "database_sha256": EXPECTED_PRE_DB_SHA256,
            "compressed_sha256": EXPECTED_COMPRESSED_PREIMAGE_SHA256,
            "streamed_restore_sha256": EXPECTED_PRE_DB_SHA256,
            "gzip_integrity": True,
            "google_drive_provider_identity_present": True,
            "predecessor_backup_preserved": True,
        },
        "copied_database_rehearsal": {
            "execution_scope": "copied_database_rehearsal",
            "status": "committed",
            "database_sha256_before": rehearsal["db_sha256_before"],
            "database_sha256_after": rehearsal["db_sha256_after"],
            "ingest_receipt_sha256": sha256_file(rehearsal_receipt_path),
            "inserted_rows": source["inserted_rows"],
            "section_rows": source["section_rows"],
            "linked_rows": source["linked_rows"],
            "fts_rows": source["fts"]["indexed_rows"],
            "integrity_check": rehearsal["integrity_check"],
            "foreign_key_failures_unchanged": rehearsal["foreign_key_failures_unchanged"],
            "existing_corpus_fingerprint_unchanged": (
                before["existing_corpus_fingerprint"] == after["existing_corpus_fingerprint"]
            ),
        },
        "database": {
            "target_locator": "primary_checkout:data/sources.db",
            "pre_sha256": before["sha256"],
            "post_sha256": after["sha256"],
            "counts_before": before["counts"],
            "counts_after": after["counts"],
            "target_absent_before": before["target_rows"] == 0,
            "target_rows_after": after["target_rows"],
            "target_fts_rows_after": after["target_fts_rows"],
            "target_section_rows_after": after["target_section_rows"],
            "target_linked_rows_after": after["target_linked_rows"],
            "foreign_key_failure_count_before": before["foreign_key_failure_count"],
            "foreign_key_failure_count_after": after["foreign_key_failure_count"],
            "foreign_key_failure_sha256_before": before["foreign_key_failure_sha256"],
            "foreign_key_failure_sha256_after": after["foreign_key_failure_sha256"],
            "existing_corpus_fingerprint_before": before["existing_corpus_fingerprint"],
            "existing_corpus_fingerprint_after": after["existing_corpus_fingerprint"],
            "integrity_check": after["integrity_check"],
            "journal_mode": after["journal_mode"],
            "live_inode_preserved": inode_preserved,
        },
        "safeguards": {
            "exact_preimage_required": True,
            "exact_one_source_set_required": True,
            "copied_database_rehearsal_passed": True,
            "recoverable_google_drive_preimage_verified": True,
            "rollback_copy_created_before_cutover": True,
            "automatic_exact_prestate_restore_on_failure": True,
            "existing_corpus_unchanged": True,
            "global_textbook_fts_parity": after["counts"]["textbook_rows"] == after["counts"]["fts_rows"],
            "private_receipt_0600": True,
        },
        "rights_and_authority": {
            "private_operator_authorized_use_only": True,
            "public_redistribution_authorized": False,
            "unrestricted_reuse_authorized": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "role_layer_conversion_complete": False,
            "adapt_or_remove_on_substantiated_complaint": True,
        },
        "phase_boundaries": {
            "database_ingest_complete": True,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
            "post_ingest_backup_required": True,
        },
    }
    return {**body, "receipt_sha256": receipt_sha256(body)}


def _schema_validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH, "VSPU cutover schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    errors = sorted(_schema_validator().iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise VspuDatabaseCutoverError(f"VSPU cutover schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "cutover receipt body hash drift")
    bindings = receipt["bindings"]
    require(
        bindings["implementation_sha256"] == sha256_file(Path(__file__).resolve()),
        "cutover implementation binding drift",
    )
    require(bindings["schema_sha256"] == sha256_file(SCHEMA_PATH), "cutover schema binding drift")
    require(
        bindings["incremental_ingest_implementation_sha256"] == sha256_file(Path(textbook_ingest.__file__).resolve()),
        "incremental ingest implementation binding drift",
    )
    require(
        receipt["database"]["existing_corpus_fingerprint_before"]
        == receipt["database"]["existing_corpus_fingerprint_after"],
        "receipt reports changed pre-existing corpus evidence",
    )
    require(
        receipt["phase_boundaries"]["database_ingest_complete"] is True,
        "receipt reports database_ingest_complete=false",
    )
    require(receipt["phase_boundaries"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["rights_and_authority"]["semantic_gold"] is False, "receipt grants semantic gold")
    return receipt


def reconcile(
    *,
    database_path: Path,
    private_jsonl_path: Path,
    preimage_backup_receipt_path: Path,
    compressed_preimage_path: Path,
    output_receipt_path: Path | None = None,
    materialization_path: Path = MATERIALIZATION_PATH,
    additive_policy_path: Path = ADDITIVE_POLICY_PATH,
    apply_in_place: bool = False,
    expected_live_db_path: Path | None = None,
    require_google_drive_output: bool = True,
) -> dict[str, Any]:
    """Plan or run the exact one-source copied-rehearsal/live cutover."""
    target = Path(database_path)
    expected_target = Path(expected_live_db_path or DEFAULT_LIVE_DB)
    _regular_file(target, "database")
    require(not target.is_symlink(), "database target must not be a symlink")
    require(target.resolve() == expected_target.resolve(), "cutover is restricted to the live sources database")
    require(os.path.samefile(target, expected_target), "cutover target is not the live database inode")
    _validate_materialization_and_policy(
        materialization_path=Path(materialization_path),
        additive_policy_path=Path(additive_policy_path),
        private_jsonl_path=Path(private_jsonl_path),
    )
    _validate_preimage_backup(
        receipt_path=Path(preimage_backup_receipt_path),
        compressed_path=Path(compressed_preimage_path),
    )
    before = _database_evidence(target)
    _validate_pre_database(before)
    plan = {
        "text_free": True,
        "provider_calls": False,
        "mode": "dry_run",
        "source_id": SOURCE_ID,
        "pre_database_sha256": before["sha256"],
        "source_rows": EXPECTED_SOURCE_ROWS,
        "recoverable_google_drive_preimage_verified": True,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    if not apply_in_place:
        return plan
    require(output_receipt_path is not None, "private output receipt is required for apply")
    if require_google_drive_output:
        # The receipt does not exist yet, so prove the output directory through a
        # provider-backed sibling already bound by this cutover.
        output_parent = Path(output_receipt_path).parent.resolve()
        backup_parent = Path(preimage_backup_receipt_path).parent.resolve()
        require(
            output_parent.is_relative_to(backup_parent.parent.parent.parent),
            "private cutover receipt must remain in the Phase 3 Google Drive backup tree",
        )
    require(not Path(output_receipt_path).exists(), "refusing to overwrite a cutover receipt")

    candidate: Path | None = None
    rollback: Path | None = None
    rehearsal_receipt_path: Path | None = None
    cutover_started = False
    rollback_retained = False
    live_inode_before = target.stat().st_ino
    try:
        _reject_nonempty_wal(target)
        require(sha256_file(target) == before["sha256"], "database bytes drifted before rehearsal")
        rollback = _candidate_path(target)
        shutil.copy2(target, rollback)
        os.chmod(rollback, PRIVATE_FILE_MODE)
        candidate = _candidate_path(target)
        shutil.copy2(target, candidate)
        os.chmod(candidate, PRIVATE_FILE_MODE)
        require(sha256_file(candidate) == EXPECTED_PRE_DB_SHA256, "candidate preimage byte drift")
        rehearsal_receipt_path = candidate.with_suffix(".ingest-receipt.json")
        try:
            textbook_ingest.ingest(
                [SOURCE_ID],
                db_path=candidate,
                dry_run=False,
                chunks_root=Path(private_jsonl_path).parent.parent,
                receipt_path=rehearsal_receipt_path,
                university_policy_path=Path(additive_policy_path),
                copied_database_rehearsal=True,
                additional_rehearsal_policy_sha256=EXPECTED_ADDITIVE_POLICY_SHA256,
            )
        except (textbook_ingest.IngestError, OSError, sqlite3.Error) as exc:
            raise VspuDatabaseCutoverError(str(exc)) from exc
        os.chmod(rehearsal_receipt_path, PRIVATE_FILE_MODE)
        rehearsal = _validate_rehearsal_receipt(rehearsal_receipt_path)
        after_candidate = _database_evidence(candidate)
        _validate_post_database(after_candidate, before)

        require(sha256_file(target) == before["sha256"], "live database drifted during rehearsal")
        _reject_nonempty_wal(target)
        cutover_started = True
        _sqlite_backup(candidate, target)
        _require_empty_or_absent_wal(target)
        after = _database_evidence(target)
        _validate_post_database(after, before)
        require(
            {key: item for key, item in after.items() if key != "sha256"}
            == {key: item for key, item in after_candidate.items() if key != "sha256"},
            "live postconditions differ from the rehearsed candidate",
        )
        receipt = validate_receipt(
            _build_receipt(
                rehearsal_receipt_path=rehearsal_receipt_path,
                rehearsal=rehearsal,
                before=before,
                after=after,
                inode_preserved=target.stat().st_ino == live_inode_before,
            )
        )
        _atomic_write_private(Path(output_receipt_path), receipt)
        if require_google_drive_output:
            _drive_item_id(Path(output_receipt_path))
        return receipt
    except BaseException as cutover_error:
        if cutover_started and rollback is not None:
            try:
                _restore_exact_prestate(rollback, target, before["sha256"])
            except BaseException as restore_error:
                rollback_retained = True
                raise VspuDatabaseCutoverError(
                    "VSPU cutover and exact rollback both failed; "
                    f"private predecessor retained at {rollback}: {restore_error}"
                ) from cutover_error
        if output_receipt_path is not None:
            Path(output_receipt_path).unlink(missing_ok=True)
        raise
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
            _cleanup_sidecars(candidate)
        if rehearsal_receipt_path is not None:
            rehearsal_receipt_path.unlink(missing_ok=True)
        if rollback is not None and not rollback_retained:
            rollback.unlink(missing_ok=True)
            _cleanup_sidecars(rollback)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_LIVE_DB)
    parser.add_argument("--private-jsonl", type=Path, required=True)
    parser.add_argument("--preimage-backup-receipt", type=Path, required=True)
    parser.add_argument("--compressed-preimage", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path)
    parser.add_argument("--materialization-receipt", type=Path, default=MATERIALIZATION_PATH)
    parser.add_argument("--additive-policy", type=Path, default=ADDITIVE_POLICY_PATH)
    parser.add_argument("--apply-in-place", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = reconcile(
            database_path=args.database,
            private_jsonl_path=args.private_jsonl,
            preimage_backup_receipt_path=args.preimage_backup_receipt,
            compressed_preimage_path=args.compressed_preimage,
            output_receipt_path=args.output_receipt,
            materialization_path=args.materialization_receipt,
            additive_policy_path=args.additive_policy,
            apply_in_place=args.apply_in_place,
        )
        print(
            canonical_json(
                {
                    "ok": True,
                    "mode": result["mode"],
                    "receipt_sha256": result.get("receipt_sha256"),
                }
            )
        )
    except VspuDatabaseCutoverError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
