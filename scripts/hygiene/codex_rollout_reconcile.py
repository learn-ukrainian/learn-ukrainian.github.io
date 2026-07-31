#!/usr/bin/env python3
"""Safely reconcile Codex thread rows whose rollout JSONL is missing.

The default command is a read-only JSON scan.  Apply is deliberately narrow:
it needs an explicit acknowledgement and the exact stale-row count from a
prior scan, then deletes only old, unpinned rows with safe rollout paths.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

SCHEMA = "codex.rollout-reconcile.v1"
STATE_PATTERN = re.compile(r"state_[A-Za-z0-9][A-Za-z0-9._-]*\.sqlite\Z")
ROLLOUT_PATTERN = re.compile(r"rollout-[^/]+\.jsonl\Z")
REQUIRED_COLUMNS = frozenset({"id", "rollout_path", "created_at", "updated_at"})
DEFAULT_MIN_AGE_SECONDS = 24 * 60 * 60
CLASSIFICATIONS = (
    "present",
    "eligible_stale",
    "protected_pinned",
    "protected_recent",
    "suspicious_path",
    "suspicious_schema",
)
class ReconcileError(RuntimeError):
    """A fail-closed discovery, schema, or database error."""


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _home(value: Path | str | None) -> Path:
    return (Path(value).expanduser() if value is not None else Path.home() / ".codex").resolve()


def _db_uri(path: Path) -> str:
    return f"file:{quote(str(path.resolve()), safe='/')}?mode=ro"


def _open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(_db_uri(path), uri=True, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _schema_issues(connection: sqlite3.Connection) -> tuple[set[str], set[str], list[str]]:
    tables = _tables(connection)
    if "threads" not in tables:
        raise ReconcileError("compatible state DB is missing the threads table")
    thread_columns = _columns(connection, "threads")
    if missing := sorted(REQUIRED_COLUMNS - thread_columns):
        raise ReconcileError(f"compatible state DB is missing threads columns: {', '.join(missing)}")
    issues: list[str] = []
    if "is_pinned" not in thread_columns:
        issues.append("threads.is_pinned is missing; missing rollouts are protected")
    if "thread_spawn_edges" in tables and not {"parent_thread_id", "child_thread_id"}.issubset(_columns(connection, "thread_spawn_edges")):
        issues.append("thread_spawn_edges has no parent_thread_id/child_thread_id columns")
    if "thread_dynamic_tools" in tables:
        dynamic_columns = _columns(connection, "thread_dynamic_tools")
        cascades = connection.execute("PRAGMA foreign_key_list(thread_dynamic_tools)").fetchall()
        has_cascade = any(
            (str(row[2]), str(row[3]), str(row[4]), str(row[6]).upper())
            == ("threads", "thread_id", "id", "CASCADE")
            for row in cascades
        )
        if "thread_id" not in dynamic_columns or not has_cascade:
            issues.append("thread_dynamic_tools lacks its declared threads CASCADE foreign key")
    return tables, thread_columns, issues


def _compatible(path: Path) -> bool:
    try:
        with _open_readonly(path) as connection:
            _schema_issues(connection)
        return True
    except (OSError, ReconcileError, sqlite3.Error):
        return False


def discover_database(codex_home: Path | str, explicit: Path | str | None = None) -> Path:
    """Find an exact compatible ``state_*.sqlite`` without writing to it."""
    home = _home(codex_home)
    if explicit is not None:
        path = Path(explicit).expanduser().resolve()
        if not STATE_PATTERN.fullmatch(path.name) or not path.is_file():
            raise ReconcileError(f"explicit DB is not an exact state_*.sqlite file: {path}")
        if not _compatible(path):
            raise ReconcileError(f"explicit DB is not compatible: {path}")
        return path

    candidates = [
        path
        for path in home.glob("state_*.sqlite")
        if path.is_file() and STATE_PATTERN.fullmatch(path.name) and _compatible(path)
    ]
    if not candidates:
        raise ReconcileError(f"no compatible state_*.sqlite found under {home}")
    candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
    if len(candidates) > 1 and candidates[0].stat().st_mtime_ns == candidates[1].stat().st_mtime_ns:
        raise ReconcileError("newest compatible state DB is ambiguous")
    return candidates[0]


def _load_pins(home: Path) -> tuple[set[str], list[str]]:
    path = home / ".codex-global-state.json"
    if not path.exists():
        return set(), []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return set(), [f"cannot read pinned-thread state: {exc.__class__.__name__}"]
    values = payload.get("pinned-thread-ids", payload.get("pinned_thread_ids")) if isinstance(payload, dict) else None
    if values is None:
        return set(), []
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        return set(), ["pinned-thread-ids is not a list of strings"]
    return set(values), []


def _integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def _pinned(value: Any) -> bool | None:
    number = _integer(value)
    return bool(number) if number in (0, 1) else None


def _path_state(raw: Any, home: Path) -> tuple[str, Path | None]:
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        return "invalid", None
    try:
        path = Path(raw).resolve(strict=False)
        roots = [(home / name).resolve(strict=False) for name in ("sessions", "archived_sessions")]
        safe = any(path.is_relative_to(root) for root in roots)
        filename_ok = ROLLOUT_PATTERN.fullmatch(path.name) is not None
        if not safe or not filename_ok:
            return "invalid", path
        if path.exists():
            return ("present" if path.is_file() else "invalid"), path
    except (OSError, RuntimeError, ValueError):
        return "invalid", None
    return "missing", path


def _row_report(
    row: sqlite3.Row,
    *,
    home: Path,
    pins: set[str],
    schema_issues: list[str],
    now: float,
    min_age_seconds: float,
) -> dict[str, Any]:
    thread_id = row["id"]
    raw_path = row["rollout_path"]
    updated_at = _integer(row["updated_at"])
    pinned_column = _pinned(row["is_pinned"])
    base: dict[str, Any] = {"id": str(thread_id) if thread_id is not None else None,
        "rollout_path": raw_path if isinstance(raw_path, str) else None, "updated_at": updated_at,
        "pinned": pinned_column if pinned_column is not None else str(thread_id) in pins}
    if thread_id is None or not isinstance(raw_path, str) or updated_at is None or updated_at < 0:
        base.update(classification="suspicious_schema", reason="invalid thread row types")
        return base
    path_state, _ = _path_state(raw_path, home)
    if path_state == "invalid":
        classification, reason = "suspicious_path", "outside allowed rollout roots or malformed"
    elif path_state == "present":
        classification, reason = "present", "rollout file exists"
    elif pinned_column is None or schema_issues:
        classification, reason = "suspicious_schema", "pin or dependent-table schema is unknown"
    elif pinned_column or str(thread_id) in pins:
        classification, reason = "protected_pinned", "thread is pinned"
    elif now - updated_at < min_age_seconds:
        classification, reason = "protected_recent", "updated within the conservative age window"
    else:
        classification, reason = "eligible_stale", "old, unpinned, safe missing rollout"
    base.update(classification=classification, reason=reason)
    return base


def _scan_with_connection(
    connection: sqlite3.Connection,
    *,
    home: Path,
    now: float,
    min_age_seconds: float,
) -> dict[str, Any]:
    _tables, columns, schema_issues = _schema_issues(connection)
    pins, pin_issues = _load_pins(home)
    schema_issues = [*schema_issues, *pin_issues]
    selected = ["id", "rollout_path", "created_at", "updated_at",
                "is_pinned" if "is_pinned" in columns else "NULL AS is_pinned"]
    rows = connection.execute(f"SELECT {', '.join(selected)} FROM threads ORDER BY id").fetchall()
    reports = [
        _row_report(row, home=home, pins=pins, schema_issues=schema_issues,
                    now=now, min_age_seconds=min_age_seconds)
        for row in rows
    ]
    counts = {classification: 0 for classification in CLASSIFICATIONS}
    for report in reports:
        counts[report["classification"]] += 1
    return {
        "schema": SCHEMA,
        "mode": "scan",
        "codex_home": str(home),
        "database": str(connection.execute("PRAGMA database_list").fetchone()[2]),
        "min_age_seconds": min_age_seconds,
        "schema_issues": schema_issues,
        "counts": counts,
        "eligible_stale_ids": [r["id"] for r in reports if r["classification"] == "eligible_stale"],
        "rows": reports,
    }


def scan(
    *,
    codex_home: Path | str | None = None,
    db_path: Path | str | None = None,
    min_age_seconds: float = DEFAULT_MIN_AGE_SECONDS,
    now: float | None = None,
) -> dict[str, Any]:
    """Return a deterministic, read-only classification report."""
    if min_age_seconds < 0:
        raise ReconcileError("min_age_seconds must be non-negative")
    home = _home(codex_home)
    database = discover_database(home, db_path)
    with _open_readonly(database) as connection:
        report = _scan_with_connection(
            connection,
            home=home,
            now=time.time() if now is None else now,
            min_age_seconds=min_age_seconds,
        )
    report["database"] = str(database)
    return report


def _create_backup(database: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    path = backup_dir / f"{database.stem}-before-reconcile-{uuid.uuid4().hex}.sqlite"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with _open_readonly(database) as source, sqlite3.connect(path) as destination:
            source.backup(destination)
            destination.commit()
        os.chmod(path, 0o600)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def _fingerprints(rows: list[dict[str, Any]]) -> dict[str, tuple[Any, ...]]:
    return {
        row["id"]: (row["rollout_path"], row["updated_at"], row["pinned"])
        for row in rows
        if row["id"] is not None
    }


def apply(
    *,
    codex_home: Path | str | None = None,
    db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
    expected_eligible_stale: int | None = None,
    acknowledge: bool = False,
    min_age_seconds: float = DEFAULT_MIN_AGE_SECONDS,
    now: float | None = None,
) -> dict[str, Any]:
    """Apply a confirmed count-matched scan, with transactional revalidation."""
    if not acknowledge:
        return {"schema": SCHEMA, "mode": "apply", "error": "acknowledgement_required"}
    if expected_eligible_stale is None or expected_eligible_stale < 0:
        return {"schema": SCHEMA, "mode": "apply", "error": "expected_count_required"}
    clock = time.time() if now is None else now
    initial = scan(codex_home=codex_home, db_path=db_path, min_age_seconds=min_age_seconds, now=clock)
    eligible = [row for row in initial["rows"] if row["classification"] == "eligible_stale"]
    if len(eligible) != expected_eligible_stale:
        return {
            "schema": SCHEMA,
            "mode": "apply",
            "error": "expected_count_mismatch",
            "expected_eligible_stale": expected_eligible_stale,
            "observed_eligible_stale": len(eligible),
            "counts": initial["counts"],
            "backup_path": None,
        }

    database = Path(initial["database"])
    backup_path: Path | None = None
    deleted: list[str] = []
    skipped: list[dict[str, str]] = []
    edge_count = 0
    connection: sqlite3.Connection | None = None
    try:
        if eligible:
            target_backup_dir = Path(backup_dir).expanduser() if backup_dir is not None else database.parent / "backups"
            backup_path = _create_backup(database, target_backup_dir)
            connection = sqlite3.connect(database, timeout=5.0)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("BEGIN IMMEDIATE")
            tables, columns, schema_issues = _schema_issues(connection)
            pins, pin_issues = _load_pins(_home(codex_home))
            schema_issues = [*schema_issues, *pin_issues]
            selected = "id, rollout_path, updated_at, " + ("is_pinned" if "is_pinned" in columns else "NULL AS is_pinned")
            for candidate in eligible:
                current = connection.execute(f"SELECT {selected} FROM threads WHERE id = ?", (candidate["id"],)).fetchone()
                if current is None:
                    skipped.append({"id": candidate["id"], "reason": "row_missing"})
                    continue
                if (
                    current["rollout_path"] != candidate["rollout_path"]
                    or _integer(current["updated_at"]) != candidate["updated_at"]
                    or _pinned(current["is_pinned"]) is not False
                ):
                    skipped.append({"id": candidate["id"], "reason": "row_changed"})
                    continue
                check = _row_report(current, home=_home(codex_home), pins=pins,
                                    schema_issues=schema_issues, now=clock,
                                    min_age_seconds=min_age_seconds)
                if check["classification"] != "eligible_stale":
                    skipped.append({"id": candidate["id"], "reason": check["classification"]})
                    continue
                deleted_count = connection.execute("DELETE FROM threads WHERE id = ?", (candidate["id"],)).rowcount
                if deleted_count != 1:
                    skipped.append({"id": candidate["id"], "reason": "delete_race"})
                    continue
                deleted.append(candidate["id"])
                if "thread_spawn_edges" in tables:
                    edge_count += connection.execute("DELETE FROM thread_spawn_edges WHERE parent_thread_id = ? OR child_thread_id = ?",
                                                      (candidate["id"], candidate["id"])).rowcount
            connection.commit()
        after = scan(
            codex_home=codex_home,
            db_path=database,
            min_age_seconds=min_age_seconds,
            now=clock,
        )
        with _open_readonly(database) as integrity_connection:
            integrity = integrity_connection.execute("PRAGMA integrity_check").fetchone()[0]
            remaining_edges = 0
            if deleted and "thread_spawn_edges" in _tables(integrity_connection):
                placeholders = ",".join("?" for _ in deleted)
                remaining_edges = integrity_connection.execute(
                    "SELECT count(*) FROM thread_spawn_edges "
                    f"WHERE parent_thread_id IN ({placeholders}) OR child_thread_id IN ({placeholders})",
                    [*deleted, *deleted],
                ).fetchone()[0]
        before_fingerprints = _fingerprints(initial["rows"])
        after_fingerprints = _fingerprints(after["rows"])
        skipped_ids = {item["id"] for item in skipped}
        parity = (
            integrity == "ok"
            and remaining_edges == 0
            and all(
                thread_id not in after_fingerprints if thread_id in deleted else
                True if thread_id in skipped_ids else
                after_fingerprints.get(thread_id) == fingerprint
                for thread_id, fingerprint in before_fingerprints.items()
            )
        )
        return {
            "schema": SCHEMA,
            "mode": "apply",
            "database": str(database),
            "backup_path": str(backup_path) if backup_path else None,
            "deleted_ids": deleted,
            "counts": {"deleted": len(deleted), "skipped": len(skipped), "spawn_edges_deleted": edge_count},
            "skipped": skipped,
            "integrity_check": integrity,
            "post_apply_parity": parity,
            "remaining": {"counts": after["counts"], "rows": after["rows"]},
        }
    except (OSError, sqlite3.Error, ReconcileError) as exc:
        if connection is not None:
            connection.rollback()
        return {
            "schema": SCHEMA,
            "mode": "apply",
            "database": str(database),
            "backup_path": str(backup_path) if backup_path else None,
            "error": f"apply_failed: {exc}",
            "deleted_ids": [],
            "counts": {"deleted": 0, "skipped": len(skipped), "spawn_edges_deleted": 0},
        }
    finally:
        if connection is not None:
            connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("scan", "apply"), default="scan")
    parser.add_argument("--codex-home", type=Path, default=None)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--min-age-hours", type=float, default=24.0)
    parser.add_argument("--now", type=float, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--fail-on-stale", action="store_true")
    parser.add_argument("--confirm-stale", "--acknowledge", dest="acknowledge", action="store_true")
    parser.add_argument(
        "--expected-eligible-stale", "--expected-count", dest="expected_count", type=int, default=None
    )
    parser.add_argument("--backup-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            report = scan(
                codex_home=args.codex_home,
                db_path=args.db,
                min_age_seconds=args.min_age_hours * 60 * 60,
                now=args.now,
            )
            print(_json(report), end="")
            return 1 if args.fail_on_stale and report["counts"]["eligible_stale"] else 0
        if args.fail_on_stale:
            print(_json({"schema": SCHEMA, "mode": "apply", "error": "fail_on_stale_is_read_only"}), end="")
            return 3
        receipt = apply(
            codex_home=args.codex_home,
            db_path=args.db,
            backup_dir=args.backup_dir,
            expected_eligible_stale=args.expected_count,
            acknowledge=args.acknowledge,
            min_age_seconds=args.min_age_hours * 60 * 60,
            now=args.now,
        )
        print(_json(receipt), end="")
        if receipt.get("error"):
            return 3 if receipt["error"] in {
                "acknowledgement_required", "expected_count_required", "expected_count_mismatch"
            } else 2
        return 0 if receipt.get("post_apply_parity") else 2
    except (OSError, ReconcileError, sqlite3.Error) as exc:
        print(_json({"schema": SCHEMA, "mode": args.command, "error": str(exc)}), end="")
        return 2


if __name__ == "__main__":
    sys.exit(main())
