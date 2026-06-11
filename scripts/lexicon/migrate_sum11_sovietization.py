#!/usr/bin/env python3
"""Idempotently add and populate СУМ-11 Sovietization flags.

This is the operational wrapper for the Word Atlas decolonization layer:
it applies the ``sum11`` flag columns when absent, then reuses
``scripts.audit.sum11_sovietization_scan.classify_entry`` through the scan
module to populate every row.

Run from the repo root:

    .venv/bin/python scripts/lexicon/migrate_sum11_sovietization.py --db data/sources.db
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.audit.sum11_sovietization_scan import scan_and_update, write_audit_report

DEFAULT_DB = ROOT / "data" / "sources.db"


def _sum11_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("PRAGMA table_info(sum11);").fetchall()
    if not rows:
        raise sqlite3.OperationalError("missing required table: sum11")
    return {str(row[1]) for row in rows}


def ensure_sum11_sovietization_columns(
    conn: sqlite3.Connection,
    *,
    dry_run: bool = False,
) -> list[str]:
    """Apply missing ``sum11`` sovietization schema pieces.

    Returns human-readable action labels. Safe to run repeatedly.
    """
    cols = _sum11_columns(conn)
    statements: list[tuple[str, str]] = []
    if "sovietization_risk" not in cols:
        statements.append(
            (
                "add sovietization_risk",
                "ALTER TABLE sum11 "
                "ADD COLUMN sovietization_risk INTEGER NOT NULL DEFAULT 0",
            )
        )
    if "sovietization_keywords" not in cols:
        statements.append(
            (
                "add sovietization_keywords",
                "ALTER TABLE sum11 "
                "ADD COLUMN sovietization_keywords TEXT NOT NULL DEFAULT ''",
            )
        )
    statements.append(
        (
            "ensure idx_sum11_sovietization",
            "CREATE INDEX IF NOT EXISTS idx_sum11_sovietization "
            "ON sum11(sovietization_risk) WHERE sovietization_risk > 0",
        )
    )

    actions = [label for label, _sql in statements]
    if dry_run:
        return actions

    with conn:
        for _label, sql in statements:
            conn.execute(sql)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Add sum11.sovietization_* columns if needed and populate them "
            "using scripts/audit/sum11_sovietization_scan.py logic."
        )
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to data/sources.db SQLite file.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional markdown report path. No report is written by default.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show schema actions and scan counts without mutating the database.",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        print(f"ERROR: DB file not found: {args.db}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(args.db)
    try:
        actions = ensure_sum11_sovietization_columns(conn, dry_run=args.dry_run)
        if args.dry_run:
            print("[dry-run] schema actions: " + ", ".join(actions))
        else:
            print("schema actions: " + ", ".join(actions))
        stats = scan_and_update(conn, dry_run=args.dry_run)
    except sqlite3.Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    if args.report is not None:
        write_audit_report(stats, args.report, args.db)

    print(
        f"Scanned {stats.total_rows:,} rows. "
        f"Flagged {stats.flagged_total:,} "
        f"({stats.flagged_pct:.2f}% — {stats.flagged_high:,} high, "
        f"{stats.flagged_low:,} low)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
