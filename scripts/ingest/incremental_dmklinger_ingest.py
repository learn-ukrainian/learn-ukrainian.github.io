"""Restore the complete pinned dmklinger translations without replacing rows (#8959).

Use reviewed corrected chunks.jsonl and an explicit database and receipt. This
command grants no canonical activation authority. Dry-run opens SQLite read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from contextlib import closing, redirect_stdout
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.scratch import ensure_scratch_root
from scripts.lib.readonly_sqlite import open_readonly
from scripts.projects.open_model_data.textbook_native_exactness import atomic_write
from scripts.wiki.build_sources_db import SCHEMA, _ingest_jsonl

TABLE = "dmklinger_uk_en"
COLUMNS = ("id", "word", "pos", "translations", "text", "source")
INPUT_SHA256 = "c16ed0975a1abd0ec9b84c21a0b47d59133ef12bc2853a95a51ba992f4aee023"
PREIMAGE_SHA256 = "1fb4661c21925b0044233173735dd372147511ac2c253887a89ef4aa45e46ed7"
POSTIMAGE_SHA256 = "fe687570109bfb34280683d15c4f2753ec75346c9b86c63564e9748bae1973d4"
EXPECTED_CHANGED_ROWS = 116
EXPECTED_RESTORED_ITEMS = 380


class IngestError(RuntimeError):
    """A conservation gate refused the operation before commit."""


def table_rows(conn: sqlite3.Connection) -> list[tuple]:
    """Read every stored column in original row-id order, including duplicates."""
    return conn.execute(f"SELECT {', '.join(COLUMNS)} FROM {TABLE} ORDER BY id").fetchall()


def rows_digest(rows: list[tuple]) -> str:
    """Use the frozen scout's canonical JSON array of full row objects."""
    objects = [dict(zip(COLUMNS, row, strict=True)) for row in rows]
    encoded = json.dumps(objects, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _schema(conn: sqlite3.Connection) -> list[tuple]:
    return conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE tbl_name=? ORDER BY type, name",
        (TABLE,),
    ).fetchall()


def _expected_input(input_path: Path, input_sha256: str) -> tuple[list[tuple], list[tuple]]:
    payload = input_path.read_bytes()
    if input_sha256 != INPUT_SHA256 or hashlib.sha256(payload).hexdigest() != INPUT_SHA256:
        raise IngestError("corrected input SHA256 does not match the reviewed pin")
    # Snapshot exactly the hashed bytes on the managed scratch root. The builder
    # reads this private snapshot, so a replacement of the caller's input cannot
    # race its second open.
    with tempfile.TemporaryDirectory(prefix="dmklinger-input-", dir=ensure_scratch_root()) as directory:
        snapshot = Path(directory) / "chunks.jsonl"
        snapshot.write_bytes(payload)
        with closing(sqlite3.connect(":memory:")) as oracle:
            oracle.executescript(SCHEMA)
            with redirect_stdout(sys.stderr):
                _ingest_jsonl(oracle, TABLE, snapshot, list(COLUMNS[1:]), "DMKlinger UK→EN")
            expected = table_rows(oracle)
            schema = _schema(oracle)
    if rows_digest(expected) != POSTIMAGE_SHA256:
        raise IngestError("builder output does not match the reviewed postimage")
    return expected, schema


def _changes(before: list[tuple], expected: list[tuple]) -> tuple[list[tuple], int]:
    if len(before) != len(expected):
        raise IngestError("source row count changed")
    updates = []
    restored = 0
    for old, new in zip(before, expected, strict=True):
        if old[:3] != new[:3] or old[4:] != new[4:]:
            raise IngestError("row id, word/POS order, text or source changed")
        old_items, new_items = json.loads(old[3]), json.loads(new[3])
        if not isinstance(old_items, list) or not isinstance(new_items, list) or old_items != new_items[:10]:
            raise IngestError("translations do not match the frozen first-ten preimage")
        if old[3] != new[3]:
            updates.append((new[3], old[0]))
            restored += len(new_items) - len(old_items)
    if len(updates) != EXPECTED_CHANGED_ROWS or restored != EXPECTED_RESTORED_ITEMS:
        raise IngestError("unexpected changed-row or restored-item set")
    return updates, restored


def _resolve_prework_identity(path: Path, failure: str) -> Path:
    """Resolve one identity before any read, database open, or receipt write.

    On Python 3.12, ``Path.resolve`` raises ``RuntimeError`` for a symlink loop.
    That invalid input becomes ``IngestError`` with the runtime error chained.
    Later code must use the returned path. A runtime error after this returns
    is not a refusal.
    """
    try:
        return path.resolve()
    except RuntimeError as exc:
        raise IngestError(failure) from exc


def ingest(
    db_path: Path, input_path: Path, *, input_sha256: str,
    receipt_path: Path, apply: bool = False,
) -> dict:
    """Validate one table snapshot and optionally commit translations-only updates.

    A receipt/checkpoint failure after commit returns the established
    committed_with_post_commit_error status, never a rollback claim.
    """
    db_path, input_path, receipt_path = map(Path, (db_path, input_path, receipt_path))
    resolved_db = _resolve_prework_identity(db_path, "database path cannot be resolved")
    resolved_receipt = _resolve_prework_identity(receipt_path, "receipt path cannot be resolved")
    resolved_input = _resolve_prework_identity(input_path, "input path cannot be resolved")
    sidecar_paths = tuple(Path(f"{resolved_db}{suffix}") for suffix in ("-wal", "-shm", "-journal"))
    resolved_sidecars = tuple(
        _resolve_prework_identity(path, "SQLite sidecar path cannot be resolved") for path in sidecar_paths
    )
    protected_paths = (db_path, input_path, *sidecar_paths)
    if resolved_receipt in {resolved_db, resolved_input, *resolved_sidecars} or any(
        receipt_path.exists() and path.exists() and receipt_path.samefile(path) for path in protected_paths
    ):
        raise IngestError("receipt must not overwrite database, input or SQLite sidecars")
    if not db_path.is_file():
        raise IngestError("database must already exist")
    # The pinned connect expression and the read-only opener resolve db_path
    # again. Bind the identity validated above so that second resolve cannot
    # become a refusal after input has been read.
    db_path = resolved_db
    expected, schema = _expected_input(input_path, input_sha256)
    conn = (
        sqlite3.connect(db_path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
        if apply else open_readonly(db_path, isolation_level=None)
    )
    committed = False
    receipt = {
        "schema_version": "incremental-dmklinger-ingest.v1",
        "input_sha256": input_sha256,
        "expected_postimage_sha256": POSTIMAGE_SHA256,
        "mode": "apply" if apply else "dry_run",
        "post_commit_error": None,
        "wal_checkpoint": None,
    }
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        if _schema(conn) != schema:
            raise IngestError("dmklinger schema/index mismatch or trigger present")
        before = table_rows(conn)
        before_digest = rows_digest(before)
        receipt["preimage_sha256"] = before_digest
        receipt["row_count"] = len(before)
        if before_digest == POSTIMAGE_SHA256:
            receipt.update(status="already_applied", changed_rows=0, changed_row_ids=[], restored_items=0)
        else:
            if before_digest != PREIMAGE_SHA256:
                raise IngestError("complete table preimage SHA256 mismatch")
            updates, restored = _changes(before, expected)
            receipt.update(changed_rows=len(updates), changed_row_ids=[row[1] for row in updates], restored_items=restored)
            if apply:
                conn.executemany(f"UPDATE {TABLE} SET translations=? WHERE id=?", updates)
                if table_rows(conn) != expected:
                    raise IngestError("postimage differs from actual builder ingest")
            receipt["status"] = "committed" if apply else "dry_run"
        integrity = [row[0] for row in conn.execute("PRAGMA integrity_check")]
        if integrity != ["ok"]:
            raise IngestError("SQLite integrity check failed")
        receipt["integrity_check"] = integrity
        receipt["postimage_sha256"] = rows_digest(table_rows(conn))
        if apply and receipt["status"] != "already_applied":
            conn.execute("COMMIT")
            committed = True
            try:
                if conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
                    checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
                    receipt["wal_checkpoint"] = checkpoint
                    if checkpoint != [0, 0, 0]:
                        raise IngestError(f"WAL checkpoint did not settle: {checkpoint}")
            except (sqlite3.Error, IngestError) as exc:
                receipt.update(status="committed_with_post_commit_error", post_commit_error=str(exc))
        else:
            conn.execute("ROLLBACK")
    except BaseException:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()
    try:
        atomic_write(receipt_path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    except OSError as exc:
        if not committed:
            raise
        receipt.update(status="committed_with_post_commit_error", post_commit_error=f"receipt write failed: {exc}")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Restore pinned dmklinger translations in one transaction.\n"
                    "Use reviewed corrected JSONL; dry-run is read-only and canonical operations need driver authority.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.ingest.incremental_dmklinger_ingest "
               "--db staged.db --input chunks.jsonl --input-sha256 SHA256 --receipt check.json\n"
               "  .venv/bin/python -m scripts.ingest.incremental_dmklinger_ingest "
               "--db staged.db --input chunks.jsonl --input-sha256 SHA256 --receipt apply.json --apply\n"
               "Outputs: JSON receipt and stdout; --apply updates translations only.\n"
               "Exit codes: 0 = verified/applied; 2 = refused/error; 3 = committed with post-commit error.\n"
               "Related: #8959; convert_phase2.py; build_sources_db.py.",
    )
    parser.add_argument("--db", required=True, type=Path, help="Existing local SQLite database, e.g. staged.db")
    parser.add_argument("--input", required=True, type=Path, help="Corrected pinned chunks.jsonl; no raw source parser")
    parser.add_argument("--input-sha256", required=True, help="Reviewed corrected JSONL SHA256, 64 lowercase hex digits")
    parser.add_argument("--receipt", required=True, type=Path, help="Durable JSON receipt, e.g. receipts/check.json")
    parser.add_argument("--apply", action="store_true", help="Commit translations-only changes (default: read-only dry-run)")
    args = parser.parse_args(argv)
    try:
        receipt = ingest(args.db, args.input, input_sha256=args.input_sha256, receipt_path=args.receipt, apply=args.apply)
    except (IngestError, OSError, ValueError, sqlite3.Error) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 3 if receipt["status"] == "committed_with_post_commit_error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
