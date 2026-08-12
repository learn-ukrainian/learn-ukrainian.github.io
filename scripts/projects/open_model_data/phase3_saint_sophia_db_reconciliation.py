#!/usr/bin/env python3
"""Fail-closed Saint Sophia historical-corpus reconciliation for ``sources.db``.

The default is a plan only. ``--apply`` validates a same-directory candidate
and atomically replaces the target. ``--apply-in-place`` validates the same
candidate then uses SQLite online backup into the existing target inode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import yaml
from jsonschema import Draft202012Validator

from scripts.ingest import incremental_historical_source_ingest as ingest
from scripts.wiki import historical_sources

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_saint_sophia_db_reconciliation_v1.schema.json"
DENOMINATOR_PATH = ROOT / "data/historical_language_corpus_denominator.yaml"
COLLECTION_ID = "saint-sophia-inscriptions"
EXPECTED_ROWS = 4_157
EXPECTED_ID_SET_SHA256 = "44b6428c07a8f496e7b933b53fa7476b8ddd54c548c9c397f2a516f26d3e584b"
EXPECTED_JSONL_SHA256 = "6199f2a92bd948dfe63d12e9da68637b02a4d16ff58b0ddba3d5e252bb3ec4fe"
EXPECTED_COVERAGE_SHA256 = "2a12ad921efc1d88f7f039e1de133ceed7c4c39715d622c316e1af14ea29c5a7"
PRIVATE_FILE_MODE = 0o600


class SaintSophiaReconciliationError(ValueError):
    """The input or database cannot support a safe reconciliation."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SaintSophiaReconciliationError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SaintSophiaReconciliationError(f"cannot read file: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _regular_file(path: Path, label: str) -> None:
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise SaintSophiaReconciliationError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular_file(path, label)
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SaintSophiaReconciliationError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _schema_validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH, "reconciliation schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_schema(value: Mapping[str, Any]) -> None:
    errors = sorted(_schema_validator().iter_errors(value), key=lambda item: list(item.path))
    if errors:
        place = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise SaintSophiaReconciliationError(f"reconciliation schema violation at {place}: {errors[0].message}")


def _denominator() -> tuple[dict[str, Any], str]:
    _regular_file(DENOMINATOR_PATH, "historical denominator")
    try:
        value = yaml.safe_load(DENOMINATOR_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SaintSophiaReconciliationError("cannot read historical denominator") from exc
    require(isinstance(value, dict), "historical denominator must be an object")
    collections = value.get("collections")
    require(isinstance(collections, list), "historical denominator collections are missing")
    collection = next((item for item in collections if item.get("collection_id") == COLLECTION_ID), None)
    require(isinstance(collection, dict), "Saint Sophia denominator collection is missing")
    return collection, sha256_file(DENOMINATOR_PATH)


def _ids_sha256(values: Sequence[str]) -> str:
    def sort_key(value: str) -> tuple[int, int | str]:
        return (0, int(value)) if value.isdecimal() else (1, value)

    return sha256_bytes("".join(f"{value}\n" for value in sorted(values, key=sort_key)).encode("utf-8"))


def _foreign_key_evidence(connection: sqlite3.Connection) -> tuple[int, str]:
    failures = sorted(tuple(row) for row in connection.execute("PRAGMA foreign_key_check").fetchall())
    return len(failures), sha256_bytes(canonical_json(failures).encode("utf-8"))


def _non_historical_fingerprint(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'historical_source_records%' AND name NOT LIKE 'idx_historical_%' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    entries: list[dict[str, Any]] = []
    for item_type, name, table, definition in rows:
        entry: dict[str, Any] = {"type": item_type, "name": name, "table": table, "sql": definition}
        if item_type == "table":
            count = connection.execute(f'SELECT COUNT(*) FROM "{name.replace(chr(34), chr(34) * 2)}"').fetchone()[0]
            entry["row_count"] = count
        entries.append(entry)
    return sha256_bytes(canonical_json(entries).encode("utf-8"))


def _database_evidence(path: Path) -> dict[str, Any]:
    _regular_file(path, "database")
    uri = f"file:{Path(path).resolve()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            has_historical = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='historical_source_records'"
            ).fetchone()
            historical_rows = (
                connection.execute("SELECT COUNT(*) FROM historical_source_records WHERE collection_id=?", (COLLECTION_ID,)).fetchone()[0]
                if has_historical else 0
            )
            historical_fts_rows = (
                connection.execute(
                    "SELECT COUNT(*) FROM historical_source_records_fts AS f "
                    "JOIN historical_source_records AS r ON r.id=f.rowid WHERE r.collection_id=?", (COLLECTION_ID,)
                ).fetchone()[0]
                if has_historical else 0
            )
            foreign_count, foreign_hash = _foreign_key_evidence(connection)
            return {
                "sha256": sha256_file(path), "historical_rows": historical_rows,
                "historical_fts_rows": historical_fts_rows, "foreign_key_failures": foreign_count,
                "foreign_key_failure_sha256": foreign_hash,
                "non_historical_table_fingerprint": _non_historical_fingerprint(connection),
                "integrity_check": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            }
    except sqlite3.Error as exc:
        raise SaintSophiaReconciliationError(f"cannot inspect database: {exc}") from exc


def _validate_inputs(*, database_path: Path, expected_pre_db_sha256: str, jsonl_path: Path, coverage_receipt_path: Path) -> tuple[list[tuple[Any, ...]], dict[str, Any], str]:
    collection, denominator_hash = _denominator()
    _regular_file(database_path, "database")
    require(sha256_file(database_path) == expected_pre_db_sha256, "caller expected pre-database SHA-256 does not match")
    artifact_hashes = collection.get("artifact_sha256")
    canonical_db = collection.get("canonical_database")
    require(isinstance(artifact_hashes, dict) and isinstance(canonical_db, dict), "Saint Sophia denominator hashes are missing")
    _regular_file(jsonl_path, "Saint Sophia JSONL")
    _regular_file(coverage_receipt_path, "Saint Sophia coverage receipt")
    require(sha256_file(jsonl_path) == artifact_hashes.get("historical_source_records_jsonl"), "Saint Sophia JSONL hash drift")
    require(sha256_file(coverage_receipt_path) == artifact_hashes.get("coverage_receipt_json"), "Saint Sophia coverage hash drift")
    require(canonical_db.get("historical_source_rows") == EXPECTED_ROWS, "Saint Sophia row denominator drift")
    require(canonical_db.get("historical_fts_rows") == EXPECTED_ROWS, "Saint Sophia FTS denominator drift")
    require(canonical_db.get("sha256") != expected_pre_db_sha256, "pre-database SHA must be pre-reconciliation")
    try:
        rows = historical_sources.load_rows(jsonl_path)
    except historical_sources.HistoricalSourceError as exc:
        raise SaintSophiaReconciliationError(str(exc)) from exc
    require(len(rows) == EXPECTED_ROWS and {row[0] for row in rows} == {COLLECTION_ID}, "Saint Sophia input rows drift")
    require(_ids_sha256([str(row[1]) for row in rows]) == EXPECTED_ID_SET_SHA256, "Saint Sophia input ID set drift")
    coverage = _read_json(coverage_receipt_path, "Saint Sophia coverage receipt")
    require(coverage.get("public_inscription_count") == EXPECTED_ROWS, "coverage receipt row count drift")
    require(coverage.get("id_set_sha256") == EXPECTED_ID_SET_SHA256, "coverage receipt ID set drift")
    try:
        ingest._read_coverage_receipt(coverage_receipt_path, jsonl_path=jsonl_path, rows=rows)
    except historical_sources.HistoricalSourceError as exc:
        raise SaintSophiaReconciliationError(str(exc)) from exc
    return rows, collection, denominator_hash


def _verify_post_evidence(path: Path, before: Mapping[str, Any]) -> dict[str, Any]:
    after = _database_evidence(path)
    require(after["historical_rows"] == EXPECTED_ROWS, "Saint Sophia row denominator drift")
    require(after["historical_fts_rows"] == EXPECTED_ROWS, "Saint Sophia FTS parity drift")
    require(after["integrity_check"] == "ok", "PRAGMA integrity_check is not ok")
    require(
        (after["foreign_key_failures"], after["foreign_key_failure_sha256"])
        == (before["foreign_key_failures"], before["foreign_key_failure_sha256"]),
        "foreign-key failures changed",
    )
    require(
        after["non_historical_table_fingerprint"] == before["non_historical_table_fingerprint"],
        "non-historical corpus/table invariants changed",
    )
    return after


def _candidate_path(live_path: Path) -> Path:
    fd, candidate = tempfile.mkstemp(dir=live_path.parent, prefix=f".{live_path.name}.saint-sophia-", suffix=".candidate")
    os.close(fd)
    return Path(candidate)


def _sidecars(path: Path) -> tuple[Path, Path]:
    return path.with_name(f"{path.name}-wal"), path.with_name(f"{path.name}-shm")


def _reject_nonempty_wal(path: Path) -> None:
    wal, _ = _sidecars(path)
    require(not wal.exists() or wal.stat().st_size == 0, "database has a non-empty WAL; reconciliation is unsafe")


def _cleanup_sidecars(path: Path) -> None:
    for sidecar in _sidecars(path):
        sidecar.unlink(missing_ok=True)


def _require_empty_or_absent_wal(path: Path) -> None:
    wal, _ = _sidecars(path)
    require(not wal.exists() or wal.stat().st_size == 0, "database WAL remains non-empty after backup")


def _sqlite_backup(source: Path, target: Path) -> None:
    """Copy a closed SQLite snapshot while preserving *target*'s inode."""
    source_uri = f"file:{Path(source).resolve()}?mode=ro"
    try:
        with sqlite3.connect(source_uri, uri=True) as source_connection, sqlite3.connect(target) as target_connection:
            source_connection.backup(target_connection)
            target_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error as exc:
        raise SaintSophiaReconciliationError(f"SQLite online backup failed: {exc}") from exc


def _restore_exact_prestate(rollback: Path, target: Path, expected_sha256: str) -> None:
    """First use SQLite backup, then byte-rescue if SQLite layout differs."""
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
    require(sha256_file(target) == expected_sha256, "rollback did not restore the exact pre-database SHA-256")


def _atomic_write_private(path: Path, value: Mapping[str, Any]) -> None:
    parent = Path(path).parent
    parent.mkdir(parents=True, exist_ok=True)
    require(parent.is_dir() and not parent.is_symlink(), "receipt parent must be a real directory")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=f".{Path(path).name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, PRIVATE_FILE_MODE)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _receipt(*, mode: str, collection: Mapping[str, Any], denominator_hash: str, jsonl_path: Path, coverage_path: Path, before: Mapping[str, Any], after: Mapping[str, Any], post_sha256: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version":"phase3_saint_sophia_db_reconciliation_v1", "text_free":True, "provider_calls":False, "mode":mode,
        "bindings":{"implementation_sha256":sha256_file(Path(__file__).resolve()), "schema_sha256":sha256_file(SCHEMA_PATH), "denominator_sha256":denominator_hash, "expected_pre_database_sha256":before["sha256"], "saint_sophia_jsonl_sha256":sha256_file(jsonl_path), "saint_sophia_coverage_sha256":sha256_file(coverage_path), "coverage_receipt_sha256":sha256_file(coverage_path)},
        "database":{"pre_sha256":before["sha256"], "post_sha256":post_sha256, "historical_rows_before":before["historical_rows"], "historical_rows_after":after["historical_rows"], "historical_fts_rows_after":after["historical_fts_rows"], "foreign_key_failures_before":before["foreign_key_failures"], "foreign_key_failures_after":after["foreign_key_failures"], "foreign_key_failure_sha256_before":before["foreign_key_failure_sha256"], "foreign_key_failure_sha256_after":after["foreign_key_failure_sha256"]},
        "invariants":{"saint_sophia_id_set_sha256":collection["public_record_id_set_sha256"], "non_historical_table_fingerprint_before":before["non_historical_table_fingerprint"], "non_historical_table_fingerprint_after":after["non_historical_table_fingerprint"], "integrity_check":after["integrity_check"]},
        "safeguards":{"exact_expected_rows":True,"exact_fts_parity":True,"foreign_key_failures_unchanged":True,"non_historical_invariants_unchanged":True,"output_private_0600":True},
        "phase_boundaries":{"historical_modern_correction_eligible":False,"phase4_blocked":True},
    }
    return {**body, "receipt_sha256":receipt_sha256(body)}


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    _validate_schema(receipt)
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "reconciliation receipt body hash drift")
    require(receipt["provider_calls"] is False and receipt["phase_boundaries"]["phase4_blocked"] is True, "reconciliation boundary drift")
    require(receipt["database"]["pre_sha256"] == receipt["bindings"]["expected_pre_database_sha256"], "pre-database binding drift")
    require(receipt["database"]["historical_rows_after"] == EXPECTED_ROWS, "historical row denominator drift")
    require(receipt["database"]["historical_fts_rows_after"] == EXPECTED_ROWS, "historical FTS denominator drift")
    require(receipt["invariants"]["saint_sophia_id_set_sha256"] == EXPECTED_ID_SET_SHA256, "Saint Sophia ID set drift")
    bindings = receipt["bindings"]
    require(bindings["saint_sophia_jsonl_sha256"] == EXPECTED_JSONL_SHA256, "Saint Sophia JSONL binding drift")
    require(bindings["saint_sophia_coverage_sha256"] == EXPECTED_COVERAGE_SHA256, "Saint Sophia coverage binding drift")
    require(bindings["coverage_receipt_sha256"] == EXPECTED_COVERAGE_SHA256, "Saint Sophia duplicate coverage binding drift")
    require(receipt["database"]["foreign_key_failures_before"] == receipt["database"]["foreign_key_failures_after"], "foreign-key failure count drift")
    require(receipt["database"]["foreign_key_failure_sha256_before"] == receipt["database"]["foreign_key_failure_sha256_after"], "foreign-key failure fingerprint drift")
    require(receipt["invariants"]["non_historical_table_fingerprint_before"] == receipt["invariants"]["non_historical_table_fingerprint_after"], "non-historical invariant drift")
    return receipt


def reconcile(*, database_path: Path, expected_pre_db_sha256: str, jsonl_path: Path, coverage_receipt_path: Path, output_receipt_path: Path | None = None, apply: bool = False, apply_in_place: bool = False) -> dict[str, Any]:
    """Plan by default; apply exactly one explicit, fail-closed mutation mode."""
    require(not (apply and apply_in_place), "choose only one apply mode")
    rows, collection, denominator_hash = _validate_inputs(database_path=Path(database_path), expected_pre_db_sha256=expected_pre_db_sha256, jsonl_path=Path(jsonl_path), coverage_receipt_path=Path(coverage_receipt_path))
    before = _database_evidence(Path(database_path))
    plan = {"text_free":True,"provider_calls":False,"mode":"dry_run","pre_database_sha256":before["sha256"],"input_rows":len(rows),"saint_sophia_id_set_sha256":EXPECTED_ID_SET_SHA256,"phase4_blocked":True}
    if not apply and not apply_in_place:
        return plan
    require(output_receipt_path is not None, "output receipt is required for apply")
    mode = "in_place_sqlite_backup" if apply_in_place else "candidate_atomic_replace"
    target = Path(database_path)
    candidate: Path | None = None
    candidate_ingest_receipt: Path | None = None
    rollback: Path | None = None
    cutover_started = False
    rollback_retained = False
    try:
        _reject_nonempty_wal(target)
        require(
            sha256_file(target) == before["sha256"],
            "pre-database bytes drifted before reconciliation",
        )
        rollback = _candidate_path(target)
        shutil.copy2(target, rollback)
        os.chmod(rollback, PRIVATE_FILE_MODE)
        candidate = _candidate_path(target)
        _sqlite_backup(target, candidate)
        candidate_ingest_receipt = candidate.with_suffix(".ingest-receipt.json")
        try:
            ingest.ingest(
                db_path=candidate,
                jsonl_path=Path(jsonl_path),
                coverage_receipt_path=Path(coverage_receipt_path),
                output_receipt_path=candidate_ingest_receipt,
            )
        except (historical_sources.HistoricalSourceError, OSError, sqlite3.Error) as exc:
            raise SaintSophiaReconciliationError(str(exc)) from exc
        after_candidate = _verify_post_evidence(candidate, before)
        candidate_ingest_receipt.unlink(missing_ok=True)
        candidate_ingest_receipt = None
        if apply:
            cutover_started = True
            os.replace(candidate, target)
            candidate = None
            _require_empty_or_absent_wal(target)
            after = _verify_post_evidence(target, before)
            post_sha256 = sha256_file(target)
        else:
            cutover_started = True
            _sqlite_backup(candidate, target)
            _require_empty_or_absent_wal(target)
            after = _verify_post_evidence(target, before)
            post_sha256 = sha256_file(target)
        require(
            {key: value for key, value in after.items() if key != "sha256"}
            == {key: value for key, value in after_candidate.items() if key != "sha256"},
            "live postconditions differ from validated candidate",
        )
        receipt = validate_receipt(_receipt(mode=mode, collection=collection, denominator_hash=denominator_hash, jsonl_path=Path(jsonl_path), coverage_path=Path(coverage_receipt_path), before=before, after=after, post_sha256=post_sha256))
        _atomic_write_private(Path(output_receipt_path), receipt)
        return receipt
    except BaseException as reconciliation_error:
        if cutover_started and rollback is not None:
            try:
                _restore_exact_prestate(rollback, target, before["sha256"])
            except BaseException as restore_error:
                rollback_retained = True
                raise SaintSophiaReconciliationError(
                    "reconciliation and automatic rollback both failed; "
                    f"exact predecessor copy retained at {rollback}: {restore_error}"
                ) from reconciliation_error
        raise
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
            _cleanup_sidecars(candidate)
        if candidate_ingest_receipt is not None:
            candidate_ingest_receipt.unlink(missing_ok=True)
        if rollback is not None and not rollback_retained:
            rollback.unlink(missing_ok=True)
            _cleanup_sidecars(rollback)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--expected-pre-db-sha256", required=True)
    parser.add_argument("--saint-sophia-jsonl", type=Path, required=True)
    parser.add_argument("--coverage-receipt", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--apply-in-place", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = reconcile(database_path=args.database, expected_pre_db_sha256=args.expected_pre_db_sha256, jsonl_path=args.saint_sophia_jsonl, coverage_receipt_path=args.coverage_receipt, output_receipt_path=args.output_receipt, apply=args.apply, apply_in_place=args.apply_in_place)
        print(canonical_json({"ok":True,"mode":result["mode"],"receipt_sha256":result.get("receipt_sha256")}))
    except SaintSophiaReconciliationError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
