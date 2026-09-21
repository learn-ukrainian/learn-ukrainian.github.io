"""Homonym-safe ULIF entry table for the runner's own SQLite store.

The legacy crawler keeps writing ``ulif_entries`` (one row per spelling) in
``data/ulif_dump_all.db``. This module never touches that table. A runner work
database gets ``ulif_dictua_entries`` keyed by ``(normalized_query, homonym_index)``.
``sources.db`` uses the same column set; its migration lives in
``scripts.wiki.sources_db``.
"""

from __future__ import annotations

import sqlite3

ULIF_DICTUA_ENTRY_COLUMNS: tuple[str, ...] = (
    "id",
    "normalized_query",
    "homonym_index",
    "canonical_headword",
    "grammatical_label",
    "content_sha256",
    "register_position",
    "homonym_checked",
    "raw_response_ref",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "status",
)

def ulif_dictua_entries_table_sql(table_name: str = "ulif_dictua_entries") -> str:
    """CREATE TABLE statement for the homonym-safe entry identity.

    ``table_name`` is interpolated only for the migration's temporary table.
    It must be a fixed identifier, never user input.
    """
    if table_name not in {"ulif_dictua_entries", "ulif_dictua_entries_mig"}:
        raise ValueError(f"unexpected ULIF entry table name: {table_name}")
    return f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY,
    normalized_query TEXT NOT NULL,
    homonym_index INTEGER NOT NULL DEFAULT 1 CHECK (homonym_index >= 1),
    canonical_headword TEXT NOT NULL DEFAULT '',
    grammatical_label TEXT NOT NULL DEFAULT '',
    content_sha256 TEXT NOT NULL DEFAULT '',
    register_position TEXT NOT NULL DEFAULT '',
    homonym_checked INTEGER NOT NULL DEFAULT 0 CHECK (homonym_checked IN (0, 1)),
    raw_response_ref TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    response_sha256 TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'transient_error', 'parse_error')),
    UNIQUE(normalized_query, homonym_index)
);
"""


ULIF_DICTUA_ENTRIES_DDL = (
    ulif_dictua_entries_table_sql()
    + """
CREATE INDEX IF NOT EXISTS idx_ulif_dictua_entries_status
    ON ulif_dictua_entries(status, normalized_query);
"""
)


def ensure_runner_ulif_entries(conn: sqlite3.Connection) -> None:
    """Create the homonym-safe entry table on a runner database.

    Refuses to rewrite a legacy ``ulif_entries`` table. Callers that already
    have the old ``ulif_dictua_entries`` unique-on-spelling shape must migrate
    through ``scripts.wiki.sources_db.migrate_ulif_dictua_entries``.
    """
    legacy = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ulif_entries'"
    ).fetchone()
    entries = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ulif_dictua_entries'"
    ).fetchone()
    if legacy is not None and entries is None:
        raise RuntimeError(
            "refusing to add ulif_dictua_entries beside a live ulif_entries table; "
            "open a runner work database, not the legacy dump"
        )
    conn.executescript(ULIF_DICTUA_ENTRIES_DDL)
    conn.commit()


def upsert_runner_ulif_entry(
    conn: sqlite3.Connection,
    *,
    normalized_query: str,
    homonym_index: int,
    canonical_headword: str,
    grammatical_label: str = "",
    content_sha256: str = "",
    register_position: str = "",
    homonym_checked: int = 0,
    raw_response_ref: str = "",
    retrieved_at: str = "",
    response_sha256: str = "",
    parser_version: str = "",
    status: str = "ok",
) -> None:
    """Insert or replace one identity row. ``content_sha256`` is not part of the key."""
    if homonym_index < 1:
        raise ValueError(f"homonym_index must be 1-based, got {homonym_index}")
    ensure_runner_ulif_entries(conn)
    conn.execute(
        """
        INSERT INTO ulif_dictua_entries (
            normalized_query, homonym_index, canonical_headword, grammatical_label,
            content_sha256, register_position, homonym_checked, raw_response_ref,
            retrieved_at, response_sha256, parser_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(normalized_query, homonym_index) DO UPDATE SET
            canonical_headword = excluded.canonical_headword,
            grammatical_label = excluded.grammatical_label,
            content_sha256 = excluded.content_sha256,
            register_position = excluded.register_position,
            homonym_checked = excluded.homonym_checked,
            raw_response_ref = excluded.raw_response_ref,
            retrieved_at = excluded.retrieved_at,
            response_sha256 = excluded.response_sha256,
            parser_version = excluded.parser_version,
            status = excluded.status
        """,
        (
            normalized_query,
            homonym_index,
            canonical_headword,
            grammatical_label,
            content_sha256,
            register_position,
            homonym_checked,
            raw_response_ref,
            retrieved_at,
            response_sha256,
            parser_version,
            status,
        ),
    )
    conn.commit()
