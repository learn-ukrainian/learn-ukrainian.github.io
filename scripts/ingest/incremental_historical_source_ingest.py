"""Transactionally replace one historical evidence collection in sources.db."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.historical_sources import (
    HistoricalSourceError,
    ensure_historical_source_schema,
    insert_rows,
    load_rows,
    sha256_file,
    validate_historical_fts,
)

DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"
RECEIPT_SCHEMA_VERSION = "incremental-historical-source-ingest.v1"


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _sha256_lines(values: list[str]) -> str:
    def sort_key(value: str) -> tuple[int, int | str]:
        return (0, int(value)) if value.isdecimal() else (1, value)

    payload = "".join(f"{value}\n" for value in sorted(values, key=sort_key)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _read_coverage_receipt(path: Path, *, jsonl_path: Path, rows: list[tuple]) -> dict[str, Any]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalSourceError(f"invalid coverage receipt {path}: {exc}") from exc
    if not isinstance(receipt, dict):
        raise HistoricalSourceError(f"coverage receipt {path} must be an object")
    expected_count = receipt.get("public_inscription_count")
    if expected_count != len(rows):
        raise HistoricalSourceError(
            f"coverage receipt count {expected_count!r} does not match {len(rows)} JSONL rows"
        )
    expected_id_hash = receipt.get("id_set_sha256")
    actual_id_hash = _sha256_lines([str(row[1]) for row in rows])
    if expected_id_hash != actual_id_hash:
        raise HistoricalSourceError("coverage receipt ID-set hash does not match JSONL")
    output_hashes = receipt.get("output_hashes")
    expected_jsonl_hash = (
        output_hashes.get("historical_source_records.jsonl")
        if isinstance(output_hashes, dict)
        else None
    )
    if expected_jsonl_hash != sha256_file(jsonl_path):
        raise HistoricalSourceError("coverage receipt JSONL hash does not match input bytes")
    return receipt


def _counts(conn: sqlite3.Connection, collection_id: str) -> dict[str, int]:
    return {
        "global_rows": conn.execute(
            "SELECT COUNT(*) FROM historical_source_records"
        ).fetchone()[0],
        "collection_rows": conn.execute(
            "SELECT COUNT(*) FROM historical_source_records WHERE collection_id = ?",
            (collection_id,),
        ).fetchone()[0],
        "fts_rows": conn.execute(
            "SELECT COUNT(*) FROM historical_source_records_fts"
        ).fetchone()[0],
    }


def ingest(
    *,
    db_path: Path,
    jsonl_path: Path,
    coverage_receipt_path: Path,
    output_receipt_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    rows = load_rows(jsonl_path)
    collection_id = str(rows[0][0])
    source_ids = [str(row[1]) for row in rows]
    coverage = _read_coverage_receipt(
        coverage_receipt_path,
        jsonl_path=jsonl_path,
        rows=rows,
    )
    disposition_counts = dict(sorted(Counter(str(row[18]) for row in rows).items()))
    plan = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "collection_id": collection_id,
        "source_jsonl": str(jsonl_path),
        "source_jsonl_sha256": sha256_file(jsonl_path),
        "coverage_receipt": str(coverage_receipt_path),
        "coverage_receipt_sha256": sha256_file(coverage_receipt_path),
        "input_rows": len(rows),
        "source_id_set_sha256": _sha256_lines(source_ids),
        "disposition_counts": disposition_counts,
        "dry_run": dry_run,
    }
    if dry_run:
        return plan
    if not db_path.is_file():
        raise HistoricalSourceError(f"database does not exist: {db_path}")

    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        ensure_historical_source_schema(conn)
        before = _counts(conn, collection_id)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "DELETE FROM historical_source_records WHERE collection_id = ?",
            (collection_id,),
        )
        insert_rows(conn, rows)
        actual_ids = [
            str(row[0])
            for row in conn.execute(
                "SELECT source_record_id FROM historical_source_records "
                "WHERE collection_id = ? ORDER BY source_record_id",
                (collection_id,),
            )
        ]
        if set(actual_ids) != set(source_ids) or len(actual_ids) != len(source_ids):
            raise HistoricalSourceError("database collection IDs do not equal input IDs")
        conn.execute(
            "INSERT INTO historical_source_records_fts(historical_source_records_fts) "
            "VALUES ('rebuild')"
        )
        validate_historical_fts(conn)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise HistoricalSourceError(f"PRAGMA integrity_check returned {integrity!r}")
        after = _counts(conn, collection_id)
        if after["collection_rows"] != len(rows):
            raise HistoricalSourceError(
                f"collection has {after['collection_rows']} rows, expected {len(rows)}"
            )
        conn.commit()
        checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()

    receipt = {
        **plan,
        "dry_run": False,
        "before_transaction": before,
        "after_transaction": after,
        "integrity_check": "ok",
        "wal_checkpoint": checkpoint,
        "database_sha256": sha256_file(db_path),
        "coverage_known_identified_total_lower_bound": coverage.get(
            "known_identified_total_lower_bound"
        ),
        "coverage_known_unexposed_residual": coverage.get("known_unexposed_residual"),
    }
    _atomic_write_json(output_receipt_path, receipt)
    return receipt


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--jsonl", type=Path, required=True)
    parser.add_argument("--coverage-receipt", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt = ingest(
        db_path=args.db,
        jsonl_path=args.jsonl,
        coverage_receipt_path=args.coverage_receipt,
        output_receipt_path=args.output_receipt,
        dry_run=args.dry_run,
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
