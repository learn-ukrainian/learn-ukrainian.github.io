#!/usr/bin/env python3
"""Quarantine the СУМ-20 rows whose provenance cannot be established (#9609).

Eleven ``sum20_articles`` rows carry ``parser_version = 'v1-official-codification'``.
No ingest code in the repository's history writes that parser version; the rows
have no senses or citations, a literal-midnight ``fetched_at`` and ``wordid``
values (300044–300066) above every article the official crawler stored.  They
are marked with a ``quarantine_reason`` and kept: nothing is deleted.  Every
СУМ-20 reader excludes a row whose ``quarantine_reason`` is not empty.

Dry-run by default (opens the database read-only).  ``--apply`` writes inside
one transaction and commits only when the marked rows are exactly the frozen
set below and no row count changed.

    .venv/bin/python scripts/ingest/sum20_quarantine_unverified.py [--db PATH] [--apply]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Mapping
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.lib.readonly_sqlite import open_readonly as _shared_open_readonly
from scripts.wiki.sum20_official import QUARANTINE_COLUMN, ensure_sum20_quarantine_column

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO / "data" / "sources.db"

UNVERIFIED_PARSER_VERSION = "v1-official-codification"
QUARANTINE_REASON = "unverified-provenance: parser v1-official-codification has no ingest code (#9609)"

# wordid -> content_sha256 of every row to quarantine, measured read-only 2026-10-03.
EXPECTED_ROWS: Mapping[int, str] = {
    300044: "199f862143007d07ade0ba8ae79ebf1710adda07960bca9f56b8e8732e3d0bea",
    300051: "2cbea3a4b69545a45344f989fc1810a571a27b726edb85fa6c4ae1740e123f3d",
    300052: "523c394a7254a26c39058a63f9bba7267dfee9cf31205cdbc75bb6d3d0856d05",
    300053: "bf0969809e3ff710ff768050674a3038ed77bae9afc314d65b2f7be8ae85c7fe",
    300054: "860f61209ae98061afef9795c574668d7fba1949278f20928beb36fe5b0b3b6f",
    300055: "c3488500690bb18d7daffede5a879a96af973748310dadafad5062613a8d17ce",
    300059: "6fb53070c39b05a3d6eefd77150d9506a160505f03f723d4eb4b29628cb8fc96",
    300060: "3bfdd22079540f14206889f49e896bb6d966623ff5a2f7d04e126f213c24b71d",
    300061: "94323d116c3697d2a198b99db9bcc26e41f9512e11048c69a60305b81ccd13fd",
    300064: "bbdc4b738778ae6fb639adb2b42ad2dc8b8160c57ba6541ba66447748cf2995b",
    300066: "bd672f75bf167e31f9a99fbfd1735b7e42b303bdc78cd877c3b202887df5fa6c",
}


class QuarantineError(RuntimeError):
    """The database does not hold exactly the expected rows; nothing was written."""


def _counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in ("sum20_articles", "sum20_senses", "sum20_citations")
    }


def _candidates(conn: sqlite3.Connection) -> dict[int, str]:
    rows = conn.execute(
        "SELECT wordid, content_sha256 FROM sum20_articles WHERE parser_version = ? ORDER BY wordid",
        (UNVERIFIED_PARSER_VERSION,),
    ).fetchall()
    return {int(wordid): str(digest) for wordid, digest in rows}


def _quarantined(conn: sqlite3.Connection) -> dict[int, str]:
    rows = conn.execute(
        f"SELECT wordid, {QUARANTINE_COLUMN} FROM sum20_articles WHERE {QUARANTINE_COLUMN} != '' ORDER BY wordid"
    ).fetchall()
    return {int(wordid): str(reason) for wordid, reason in rows}


def _has_column(conn: sqlite3.Connection) -> bool:
    return QUARANTINE_COLUMN in {str(row[1]) for row in conn.execute("PRAGMA table_info(sum20_articles)")}


def quarantine(db_path: Path, *, apply: bool, expected: Mapping[int, str] = EXPECTED_ROWS) -> dict[str, object]:
    """Check (and with ``apply``, mark) the unverified rows; return a receipt."""
    if not db_path.is_file():
        raise QuarantineError(f"database not found: {db_path}")
    conn = sqlite3.connect(db_path, isolation_level=None) if apply else _shared_open_readonly(db_path.resolve())
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        before = _counts(conn)
        found = _candidates(conn)
        if found != dict(expected):
            raise QuarantineError(
                f"expected {len(expected)} rows {sorted(expected)} with frozen hashes; found {len(found)} "
                f"{sorted(found)} (hash mismatches: "
                f"{sorted(w for w in found.keys() & expected.keys() if found[w] != expected[w])})"
            )
        receipt: dict[str, object] = {
            "db": db_path.name,
            "mode": "apply" if apply else "dry-run",
            "counts_before": before,
            "column_present_before": _has_column(conn),
            "candidates": len(found),
            "already_quarantined": len(_quarantined(conn)) if _has_column(conn) else 0,
        }
        if not apply:
            receipt["would_mark"] = len(found) - int(receipt["already_quarantined"])
            return receipt
        conn.execute("BEGIN IMMEDIATE")
        try:
            receipt["column_added"] = ensure_sum20_quarantine_column(conn)
            marked = conn.execute(
                f"UPDATE sum20_articles SET {QUARANTINE_COLUMN} = ? "
                f"WHERE parser_version = ? AND {QUARANTINE_COLUMN} = ''",
                (QUARANTINE_REASON, UNVERIFIED_PARSER_VERSION),
            ).rowcount
            after = _counts(conn)
            quarantined = _quarantined(conn)
            if after != before or set(quarantined) != set(expected):
                raise QuarantineError(
                    f"post-check failed: counts {before} -> {after}; quarantined {sorted(quarantined)}"
                )
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        receipt.update({"marked": marked, "counts_after": after, "quarantined": len(quarantined)})
        return receipt
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="sources.db to check (default: data/sources.db)")
    parser.add_argument("--apply", action="store_true", help="write the quarantine marks (default: dry-run)")
    args = parser.parse_args(argv)
    try:
        receipt = quarantine(args.db, apply=args.apply, expected=EXPECTED_ROWS)
    except QuarantineError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
