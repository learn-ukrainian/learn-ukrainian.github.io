"""Schema and exact-row ingestion for private historical source corpora."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "historical-source-record.v1"
ALLOWED_DISPOSITIONS = {
    "text_bearing",
    "non_textual_or_no_text",
    "quarantined_metadata",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")

HISTORICAL_SOURCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS historical_source_records (
    id INTEGER PRIMARY KEY,
    collection_id TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    title TEXT,
    source_url TEXT,
    published INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1)),
    original_transcription TEXT,
    epidoc_text TEXT,
    epidoc_interpretation TEXT,
    interpretative_edition TEXT,
    romanisation TEXT,
    translation_ukr TEXT,
    translation_eng TEXT,
    commentary_ukr TEXT,
    commentary_eng TEXT,
    source_language_label TEXT,
    source_writing_system_label TEXT,
    min_year INTEGER,
    max_year INTEGER,
    disposition TEXT NOT NULL,
    stage_label TEXT,
    quality_flags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    raw_record_sha256 TEXT NOT NULL,
    UNIQUE(collection_id, source_record_id)
);
CREATE INDEX IF NOT EXISTS idx_historical_collection
    ON historical_source_records(collection_id);
CREATE INDEX IF NOT EXISTS idx_historical_disposition
    ON historical_source_records(collection_id, disposition);
CREATE VIRTUAL TABLE IF NOT EXISTS historical_source_records_fts USING fts5(
    title,
    original_transcription,
    epidoc_text,
    epidoc_interpretation,
    interpretative_edition,
    romanisation,
    translation_ukr,
    translation_eng,
    commentary_ukr,
    commentary_eng,
    content='historical_source_records',
    content_rowid='id',
    tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS historical_source_records_ai
AFTER INSERT ON historical_source_records BEGIN
    INSERT INTO historical_source_records_fts(
        rowid, title, original_transcription, epidoc_text,
        epidoc_interpretation, interpretative_edition, romanisation,
        translation_ukr, translation_eng, commentary_ukr, commentary_eng
    ) VALUES (
        new.id, new.title, new.original_transcription, new.epidoc_text,
        new.epidoc_interpretation, new.interpretative_edition, new.romanisation,
        new.translation_ukr, new.translation_eng, new.commentary_ukr,
        new.commentary_eng
    );
END;
"""

INSERT_SQL = """INSERT INTO historical_source_records (
    collection_id, source_record_id, title, source_url, published,
    original_transcription, epidoc_text, epidoc_interpretation,
    interpretative_edition, romanisation, translation_ukr, translation_eng,
    commentary_ukr, commentary_eng, source_language_label,
    source_writing_system_label, min_year, max_year, disposition, stage_label,
    quality_flags_json, metadata_json, raw_record_sha256
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

TEXT_FIELDS = (
    "title",
    "source_url",
    "original_transcription",
    "epidoc_text",
    "epidoc_interpretation",
    "interpretative_edition",
    "romanisation",
    "translation_ukr",
    "translation_eng",
    "commentary_ukr",
    "commentary_eng",
    "source_language_label",
    "source_writing_system_label",
)


class HistoricalSourceError(RuntimeError):
    """Raised when historical source evidence is incomplete or malformed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ensure_historical_source_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(HISTORICAL_SOURCE_SCHEMA)


def _require_optional_year(row: dict[str, Any], field: str, *, source: str) -> int | None:
    value = row.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise HistoricalSourceError(f"{source}: {field} must be an integer or null")
    return value


def build_row(row: dict[str, Any], *, source: str) -> tuple[Any, ...]:
    if row.get("schema_version") != SCHEMA_VERSION:
        raise HistoricalSourceError(
            f"{source}: schema_version must be {SCHEMA_VERSION!r}"
        )
    collection_id = row.get("collection_id")
    source_record_id = row.get("source_record_id")
    if not isinstance(collection_id, str) or not collection_id:
        raise HistoricalSourceError(f"{source}: collection_id must be a nonempty string")
    if not isinstance(source_record_id, str) or not source_record_id:
        raise HistoricalSourceError(f"{source}: source_record_id must be a nonempty string")
    disposition = row.get("disposition")
    if disposition not in ALLOWED_DISPOSITIONS:
        raise HistoricalSourceError(f"{source}: invalid disposition {disposition!r}")
    published = row.get("published")
    if not isinstance(published, bool):
        raise HistoricalSourceError(f"{source}: published must be boolean")
    stage_label = row.get("stage_label")
    if stage_label is not None and not isinstance(stage_label, str):
        raise HistoricalSourceError(f"{source}: stage_label must be a string or null")
    flags = row.get("quality_flags")
    if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
        raise HistoricalSourceError(f"{source}: quality_flags must be a list of strings")
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        raise HistoricalSourceError(f"{source}: metadata must be an object")
    raw_hash = row.get("raw_record_sha256")
    if not isinstance(raw_hash, str) or SHA256_RE.fullmatch(raw_hash) is None:
        raise HistoricalSourceError(f"{source}: raw_record_sha256 must be lowercase SHA-256")
    text_values: list[str | None] = []
    for field in TEXT_FIELDS:
        value = row.get(field)
        if value is not None and not isinstance(value, str):
            raise HistoricalSourceError(f"{source}: {field} must be a string or null")
        text_values.append(value)
    min_year = _require_optional_year(row, "min_year", source=source)
    max_year = _require_optional_year(row, "max_year", source=source)
    return (
        collection_id,
        source_record_id,
        text_values[0],
        text_values[1],
        int(published),
        *text_values[2:],
        min_year,
        max_year,
        disposition,
        stage_label,
        canonical_json(flags),
        canonical_json(metadata),
        raw_hash,
    )


def load_rows(path: Path) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    seen: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise HistoricalSourceError(f"{path}:{line_number}: blank lines are not allowed")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HistoricalSourceError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise HistoricalSourceError(f"{path}:{line_number}: row must be an object")
            built = build_row(value, source=f"{path}:{line_number}")
            key = (built[0], built[1])
            if key in seen:
                raise HistoricalSourceError(f"{path}:{line_number}: duplicate key {key!r}")
            seen.add(key)
            rows.append(built)
    if not rows:
        raise HistoricalSourceError(f"{path}: no records")
    collections = {row[0] for row in rows}
    if len(collections) != 1:
        raise HistoricalSourceError(f"{path}: expected one collection, found {sorted(collections)}")
    return rows


def insert_rows(conn: sqlite3.Connection, rows: Iterable[tuple[Any, ...]]) -> int:
    materialized = list(rows)
    conn.executemany(INSERT_SQL, materialized)
    return len(materialized)


def validate_historical_fts(conn: sqlite3.Connection) -> None:
    source_count = conn.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0]
    fts_count = conn.execute("SELECT COUNT(*) FROM historical_source_records_fts").fetchone()[0]
    if source_count != fts_count:
        raise HistoricalSourceError(
            "historical_source_records/FTS row parity failed "
            f"({source_count} source, {fts_count} indexed)"
        )
    conn.execute(
        "INSERT INTO historical_source_records_fts(historical_source_records_fts) "
        "VALUES ('integrity-check')"
    )
