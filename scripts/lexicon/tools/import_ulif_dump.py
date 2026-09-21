#!/usr/bin/env python3
"""Import crawled ULIF DictUA dump into sources.db (ulif_dictua_* tables).

Reads entries from the standalone crawler SQLite database (e.g. data/ulif_dump_all.db)
and transactionally streams them into the canonical sources.db tables
(ulif_dictua_entries and ulif_dictua_sections).

Supports one-shot execution or continuous `--watch` mode to progressively ingest
entries while dump_ulif.py is crawling in the background.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

ULIF_SECTION_KINDS = ("paradigm", "synonyms", "antonyms", "phraseology")


def normalize_query(word: str) -> str:
    """Case-insensitive normalized query key."""
    return " ".join(word.split()).casefold()


def ensure_target_schema(conn: sqlite3.Connection) -> None:
    """Ensure ulif_dictua_* tables exist in the target database."""
    try:
        from scripts.wiki.sources_db import ensure_ulif_dictua_schema
    except ImportError:
        from wiki.sources_db import ensure_ulif_dictua_schema

    ensure_ulif_dictua_schema(conn)
    conn.commit()


def require_homonym_schema(conn: sqlite3.Connection) -> None:
    """Refuse an un-migrated spelling-only table before any ``homonym_index`` query."""
    try:
        from scripts.wiki.sources_db import (
            ULIF_DICTUA_MIGRATE_MESSAGE,
            _ulif_dictua_schema_current,
            _ulif_table_exists,
        )
    except ImportError:
        from wiki.sources_db import (
            ULIF_DICTUA_MIGRATE_MESSAGE,
            _ulif_dictua_schema_current,
            _ulif_table_exists,
        )

    if _ulif_table_exists(conn, "ulif_dictua_entries") and not _ulif_dictua_schema_current(conn):
        raise RuntimeError(ULIF_DICTUA_MIGRATE_MESSAGE)


def import_batch(
    dump_conn: sqlite3.Connection,
    target_conn: sqlite3.Connection,
    *,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Import new or updated entries from dump_db to target_db."""
    require_homonym_schema(target_conn)
    # Find existing entries in target to skip identical ones
    existing_records = {
        (row[0], row[1]): row[2]
        for row in target_conn.execute(
            "SELECT normalized_query, homonym_index, retrieved_at FROM ulif_dictua_entries"
        )
    }

    query = (
        "SELECT lemma, canonical_headword, status, retrieved_at, "
        "paradigm_json, synonyms_json, phraseology_json, antonyms_json "
        "FROM ulif_entries "
        "WHERE status IN ('ok', 'not_found', 'parse_error') "
        "ORDER BY rowid ASC"
    )
    if limit:
        query += f" LIMIT {limit}"

    cursor = dump_conn.execute(query)
    tally = {"scanned": 0, "inserted": 0, "updated": 0, "skipped": 0, "sections": 0}

    entries_to_insert: list[tuple[str, str, str, str, str, str, str, dict[str, Any]]] = []

    for row in cursor:
        tally["scanned"] += 1
        lemma = row[0]
        canonical_headword = row[1] or ""
        status = row[2]
        retrieved_at = row[3] or ""
        paradigm_json = row[4]
        synonyms_json = row[5]
        phraseology_json = row[6]
        antonyms_json = row[7]

        normalized = normalize_query(lemma)
        if not normalized:
            tally["skipped"] += 1
            continue

        existing_retrieved = existing_records.get((normalized, 1))
        if existing_retrieved and existing_retrieved == retrieved_at:
            tally["skipped"] += 1
            continue

        sections_dict: dict[str, Any] = {}
        if paradigm_json:
            with contextlib.suppress(Exception):
                sections_dict["paradigm"] = json.loads(paradigm_json)
        if synonyms_json:
            with contextlib.suppress(Exception):
                sections_dict["synonyms"] = json.loads(synonyms_json)
        if phraseology_json:
            with contextlib.suppress(Exception):
                sections_dict["phraseology"] = json.loads(phraseology_json)
        if antonyms_json:
            with contextlib.suppress(Exception):
                sections_dict["antonyms"] = json.loads(antonyms_json)

        digest = hashlib.sha256(
            f"{lemma}:{canonical_headword}:{status}:{retrieved_at}".encode()
        ).hexdigest()

        entries_to_insert.append(
            (
                normalized,
                canonical_headword,
                "dump_ulif",
                retrieved_at,
                digest,
                "1.0",
                status,
                sections_dict,
            )
        )

    if dry_run or not entries_to_insert:
        return tally

    with target_conn:
        for (
            normalized,
            canonical_headword,
            raw_ref,
            retrieved_at,
            digest,
            version,
            status,
            sections_dict,
        ) in entries_to_insert:
            is_new = (normalized, 1) not in existing_records
            target_conn.execute(
                """
                INSERT INTO ulif_dictua_entries
                    (normalized_query, homonym_index, canonical_headword, grammatical_label,
                     content_sha256, register_position, homonym_checked, raw_response_ref,
                     retrieved_at, response_sha256, parser_version, status)
                VALUES (?, 1, ?, '', ?, '', 0, ?, ?, ?, ?, ?)
                ON CONFLICT(normalized_query, homonym_index) DO UPDATE SET
                    canonical_headword = excluded.canonical_headword,
                    content_sha256 = excluded.content_sha256,
                    raw_response_ref = excluded.raw_response_ref,
                    retrieved_at = excluded.retrieved_at,
                    response_sha256 = excluded.response_sha256,
                    parser_version = excluded.parser_version,
                    status = excluded.status
                """,
                (
                    normalized,
                    canonical_headword,
                    digest,
                    raw_ref,
                    retrieved_at,
                    digest,
                    version,
                    status,
                ),
            )
            entry_row = target_conn.execute(
                """
                SELECT id FROM ulif_dictua_entries
                WHERE normalized_query = ? AND homonym_index = 1
                """,
                (normalized,),
            ).fetchone()
            if not entry_row:
                continue
            entry_id = entry_row[0]

            target_conn.execute(
                "DELETE FROM ulif_dictua_sections WHERE entry_id = ?", (entry_id,)
            )

            if status == "ok":
                for kind in ULIF_SECTION_KINDS:
                    data = sections_dict.get(kind)
                    if not data:
                        continue
                    payloads = data if isinstance(data, list) else [data]
                    for order, payload in enumerate(payloads):
                        if not isinstance(payload, dict):
                            continue
                        group_id = f"{kind}:{order + 1}"
                        target_conn.execute(
                            """
                            INSERT INTO ulif_dictua_sections
                                (entry_id, kind, source_order, sense_or_group_id, payload_json)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                entry_id,
                                kind,
                                order,
                                group_id,
                                json.dumps(payload, ensure_ascii=False),
                            ),
                        )
                        tally["sections"] += 1

            if is_new:
                tally["inserted"] += 1
            else:
                tally["updated"] += 1

    return tally


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stream entries from ULIF crawler dump DB into sources.db."
    )
    parser.add_argument(
        "--dump-db",
        type=Path,
        default=Path("data/ulif_dump_all.db"),
        help="Path to SQLite database created by dump_ulif.py",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=Path("data/sources.db"),
        help="Path to canonical sources.db",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum entries to process in this run",
    )
    parser.add_argument(
        "--watch",
        type=int,
        metavar="SECONDS",
        default=None,
        help="Poll interval in seconds for continuous incremental ingestion",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report counts without modifying sources.db",
    )

    args = parser.parse_args(argv)

    if not args.dump_db.exists():
        print(f"Error: dump database not found at {args.dump_db}", file=sys.stderr)
        return 1

    dump_conn = sqlite3.connect(str(args.dump_db))
    target_conn = sqlite3.connect(str(args.sources_db))

    try:
        require_homonym_schema(target_conn)
        ensure_target_schema(target_conn)
        while True:
            t0 = time.monotonic()
            tally = import_batch(
                dump_conn, target_conn, limit=args.limit, dry_run=args.dry_run
            )
            elapsed = time.monotonic() - t0
            print(
                f"Import complete in {elapsed:.2f}s: "
                f"scanned={tally['scanned']}, inserted={tally['inserted']}, "
                f"updated={tally['updated']}, skipped={tally['skipped']}, "
                f"sections={tally['sections']}"
            )

            if args.watch is None:
                break
            time.sleep(args.watch)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        dump_conn.close()
        target_conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
