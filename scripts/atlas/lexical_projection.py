"""Deterministic v2 Atlas lexical projection builder (ADR-017).

The JSONL source remains editorial truth.  This module writes a fresh SQLite
query projection and can export the accepted source records canonically.  It
does not mutate the source JSONL or the legacy v1 ``atlas_db`` projection.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import tempfile
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"

RECORD_TYPES = (
    "source",
    "lemma_entry",
    "sense",
    "attestation",
    "practice_deck",
    "practice_deck_item",
)
RECORD_TYPE_ORDER = {record_type: index for index, record_type in enumerate(RECORD_TYPES)}
PRIMARY_KEY_FIELDS = {
    "source": ("source_id",),
    "lemma_entry": ("entry_slug",),
    "sense": ("sense_slug",),
    "attestation": ("attestation_id",),
    "practice_deck": ("deck_slug",),
    "practice_deck_item": ("deck_slug", "sense_slug"),
}

# These measured constants come from #5791's curated-seed rebuild.  They are
# calibrated quality gates, not tunable defaults: changing either requires a
# new design decision.
RUSSIAN_ONLY_LETTERS = frozenset("ыэъё")
UKRAINIAN_SPECIFIC_LETTERS = frozenset("іїєґ")
UNKNOWN_TOKEN_RATIO_LIMIT = 0.30

# Exercise material may put the deliberately defective passage *above* the
# prompt, so a hit excludes the whole textbook chunk, never only nearby text.
EXERCISE_INSTRUCTION_RE = re.compile(
    r"виправте|знайдіть\s+помилк|відредагуйте|помилков|"
    r"неправильно\s+вжит|запишіть\s+правильно|суржик|який\s+недолік|"
    r"доберіть\s+правильн|перебудуйте|правильний\s+варіант",
    re.IGNORECASE,
)
UKRAINIAN_TOKEN_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:[ʼ’'][А-Яа-яІіЇїЄєҐґ]+)*")
APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'"})


class ProjectionError(ValueError):
    """The declared lexical source cannot safely become a projection."""


@dataclass(frozen=True)
class RejectedRecord:
    """A deterministic, reportable build-time attestation rejection."""

    attestation_id: str
    reason: str
    record: dict[str, Any]


@dataclass(frozen=True)
class BuildResult:
    accepted_records: int
    rejected_records: tuple[RejectedRecord, ...]

    @property
    def rejection_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rejected in self.rejected_records:
            counts[rejected.reason] = counts.get(rejected.reason, 0) + 1
        return counts


SCHEMA = """
CREATE TABLE lemma_entries (
    entry_slug TEXT PRIMARY KEY,
    lemma TEXT NOT NULL,
    display_head TEXT,
    entry_type TEXT NOT NULL,
    route_path TEXT,
    visibility TEXT NOT NULL DEFAULT 'public',
    record_json TEXT NOT NULL
);
CREATE TABLE senses (
    sense_slug TEXT PRIMARY KEY,
    entry_slug TEXT NOT NULL,
    sense_key TEXT,
    definition_json TEXT,
    review_state TEXT,
    record_json TEXT NOT NULL,
    FOREIGN KEY (entry_slug) REFERENCES lemma_entries(entry_slug)
);
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    source_work TEXT NOT NULL,
    author TEXT,
    author_uk TEXT,
    canonical_url TEXT,
    file_path TEXT,
    source_revision TEXT,
    language_period TEXT,
    grade TEXT,
    license_type TEXT NOT NULL,
    attribution_type TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    source_kind TEXT,
    record_json TEXT NOT NULL
);
CREATE TABLE attestations (
    attestation_id TEXT PRIMARY KEY,
    sense_slug TEXT NOT NULL,
    source_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    span_start INTEGER NOT NULL,
    span_end INTEGER NOT NULL,
    text TEXT NOT NULL,
    chunk_text TEXT,
    extraction_mode TEXT,
    review_state TEXT,
    record_json TEXT NOT NULL,
    CHECK (span_start >= 0),
    CHECK (span_end > span_start),
    FOREIGN KEY (sense_slug) REFERENCES senses(sense_slug),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
CREATE TABLE practice_decks (
    deck_slug TEXT PRIMARY KEY,
    title TEXT,
    version TEXT,
    scope TEXT,
    record_json TEXT NOT NULL
);
CREATE TABLE practice_deck_items (
    deck_slug TEXT NOT NULL,
    sense_slug TEXT NOT NULL,
    attestation_id TEXT,
    card_template TEXT,
    record_json TEXT NOT NULL,
    PRIMARY KEY (deck_slug, sense_slug),
    FOREIGN KEY (deck_slug) REFERENCES practice_decks(deck_slug),
    FOREIGN KEY (sense_slug) REFERENCES senses(sense_slug),
    FOREIGN KEY (attestation_id) REFERENCES attestations(attestation_id)
);
CREATE INDEX idx_senses_entry_slug ON senses(entry_slug);
CREATE INDEX idx_attestations_sense_slug ON attestations(sense_slug);
CREATE INDEX idx_attestations_source_id ON attestations(source_id);
CREATE INDEX idx_practice_deck_items_sense_slug ON practice_deck_items(sense_slug);

-- Read-only v1 compatibility projections.  The existing v1 ``atlas_db``
-- tables remain untouched; these views allow a v2-only projection to serve
-- legacy SELECT consumers during the migration.
CREATE VIEW articles AS
SELECT entry_slug AS slug, COALESCE(display_head, lemma) AS display_head,
       lemma, entry_type, NULL AS pos, NULL AS gloss,
       'approved' AS review_state, visibility, NULL AS cefr,
       NULL AS heritage_classification, NULL AS created_at, NULL AS updated_at
FROM lemma_entries;
CREATE VIEW enrichment AS
SELECT sense.entry_slug AS slug, 'meaning' AS section,
       COALESCE(sense.definition_json, '{}') AS payload_json,
       NULL AS source, NULL AS filled_at, NULL AS phase
FROM senses AS sense;
CREATE VIEW related_entries AS
SELECT CAST(NULL AS TEXT) AS slug, CAST(NULL AS TEXT) AS related_slug,
       CAST(NULL AS TEXT) AS entry_type, CAST(NULL AS TEXT) AS relation,
       CAST(NULL AS TEXT) AS component_role, CAST(NULL AS TEXT) AS provenance
WHERE 0;
"""


def canonical_json(record: dict[str, Any]) -> str:
    """Canonical JSONL encoding used for byte-stable source exports."""
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deterministic_attestation_id(source_id: str, chunk_id: str, span_start: int, span_end: int) -> str:
    """Return ADR-017's stable source/chunk/span composite attestation key."""
    return f"{source_id}:{chunk_id}:{span_start}:{span_end}"


def _normalized_form(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.translate(APOSTROPHE_TRANSLATION))
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _required_string(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProjectionError(f"{record.get('record_type', 'record')} requires non-empty {field!r}")
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise ProjectionError(f"{field!r} must be NFC-normalized")
    return value


def _required_int(record: dict[str, Any], field: str) -> int:
    value = record.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProjectionError(f"{record.get('record_type', 'record')} requires integer {field!r}")
    return value


def _record_key(record: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    record_type = _required_string(record, "record_type")
    if record_type not in PRIMARY_KEY_FIELDS:
        raise ProjectionError(f"unsupported record_type {record_type!r}")
    return record_type, tuple(_required_string(record, field) for field in PRIMARY_KEY_FIELDS[record_type])


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProjectionError(f"invalid JSONL at {path}:{line_number}: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise ProjectionError(f"JSONL record at {path}:{line_number} must be an object")
        key = _record_key(record)
        if key in seen:
            raise ProjectionError(f"duplicate {key[0]} primary key at {path}:{line_number}: {key[1]!r}")
        seen.add(key)
        records.append(record)
    return records


def load_vesum_forms(vesum_db: Path) -> frozenset[str]:
    """Load the authoritative visible VESUM forms once per build."""
    if not vesum_db.is_file():
        raise ProjectionError(f"VESUM forms database is required for attestation ingest: {vesum_db}")
    try:
        with sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True) as connection:
            rows = connection.execute("SELECT word_form FROM forms").fetchall()
    except sqlite3.Error as exc:
        raise ProjectionError(f"cannot read VESUM forms from {vesum_db}: {exc}") from exc
    return frozenset(_normalized_form(str(row[0])) for row in rows if row[0])


def _is_textbook_source(source: dict[str, Any], attestation: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            source.get("source_kind"),
            source.get("source_work"),
            source.get("source_id"),
            attestation.get("source_kind"),
            attestation.get("source_work"),
            attestation.get("chunk_id"),
        )
    ).casefold()
    return "textbook" in haystack or "ukrmova" in haystack


def attestation_rejection_reason(
    attestation: dict[str, Any], source: dict[str, Any], vesum_forms: frozenset[str]
) -> str | None:
    """Return the first calibrated quality-gate failure for an attestation."""
    source_period = source.get("language_period")
    chunk_period = attestation.get("language_period")
    if (
        source_period not in {None, "modern"}
        or chunk_period not in {None, "modern"}
        or (source_period is None and chunk_period is None)
    ):
        return "language_period_not_modern"

    text = _required_string(attestation, "text")
    folded = text.casefold()
    if RUSSIAN_ONLY_LETTERS.intersection(folded):
        return "russian_only_letter"

    # The conjunction matters: 34 legitimate sentences lack і/ї/є/ґ, while a
    # surname alone can raise the VESUM miss rate.  Neither signal is safe by
    # itself; only this exact combined predicate rejects a row.
    if not UKRAINIAN_SPECIFIC_LETTERS.intersection(folded):
        tokens = UKRAINIAN_TOKEN_RE.findall(text)
        unknown = sum(_normalized_form(token) not in vesum_forms for token in tokens)
        if tokens and unknown / len(tokens) > UNKNOWN_TOKEN_RATIO_LIMIT:
            return "ukrainian_purity_unknown_ratio"

    chunk_text = str(attestation.get("chunk_text") or attestation.get("source_text") or text)
    if _is_textbook_source(source, attestation) and EXERCISE_INSTRUCTION_RE.search(chunk_text):
        return "textbook_exercise_instruction"
    return None


def _validate_attestation_identity(record: dict[str, Any]) -> None:
    source_id = _required_string(record, "source_id")
    chunk_id = _required_string(record, "chunk_id")
    span_start = _required_int(record, "span_start")
    span_end = _required_int(record, "span_end")
    if span_start < 0 or span_end <= span_start:
        raise ProjectionError("attestation span must satisfy 0 <= span_start < span_end")
    expected = deterministic_attestation_id(source_id, chunk_id, span_start, span_end)
    if _required_string(record, "attestation_id") != expected:
        raise ProjectionError(f"attestation_id must equal deterministic composite {expected!r}")


def _insert_record(cursor: sqlite3.Cursor, record: dict[str, Any]) -> None:
    record_type, _ = _record_key(record)
    payload = canonical_json(record)
    if record_type == "lemma_entry":
        cursor.execute(
            """INSERT INTO lemma_entries
               (entry_slug, lemma, display_head, entry_type, route_path, visibility, record_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                _required_string(record, "entry_slug"),
                _required_string(record, "lemma"),
                record.get("display_head"),
                _required_string(record, "entry_type"),
                record.get("route_path"),
                record.get("visibility", "public"),
                payload,
            ),
        )
    elif record_type == "sense":
        cursor.execute(
            """INSERT INTO senses(sense_slug, entry_slug, sense_key, definition_json, review_state, record_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                _required_string(record, "sense_slug"),
                _required_string(record, "entry_slug"),
                record.get("sense_key"),
                json.dumps(record["definition"], ensure_ascii=False, sort_keys=True)
                if "definition" in record
                else None,
                record.get("review_state"),
                payload,
            ),
        )
    elif record_type == "source":
        cursor.execute(
            """INSERT INTO sources
               (source_id, source_work, author, author_uk, canonical_url, file_path, source_revision,
                language_period, grade, license_type, attribution_type, rights_status, source_kind, record_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _required_string(record, "source_id"),
                _required_string(record, "source_work"),
                record.get("author"),
                record.get("author_uk"),
                record.get("canonical_url"),
                record.get("file_path"),
                record.get("source_revision"),
                record.get("language_period"),
                record.get("grade"),
                _required_string(record, "license_type"),
                _required_string(record, "attribution_type"),
                _required_string(record, "rights_status"),
                record.get("source_kind"),
                payload,
            ),
        )
    elif record_type == "attestation":
        _validate_attestation_identity(record)
        cursor.execute(
            """INSERT INTO attestations
               (attestation_id, sense_slug, source_id, chunk_id, span_start, span_end, text, chunk_text,
                extraction_mode, review_state, record_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _required_string(record, "attestation_id"),
                _required_string(record, "sense_slug"),
                _required_string(record, "source_id"),
                _required_string(record, "chunk_id"),
                _required_int(record, "span_start"),
                _required_int(record, "span_end"),
                _required_string(record, "text"),
                record.get("chunk_text"),
                record.get("extraction_mode"),
                record.get("review_state"),
                payload,
            ),
        )
    elif record_type == "practice_deck":
        cursor.execute(
            "INSERT INTO practice_decks(deck_slug, title, version, scope, record_json) VALUES (?, ?, ?, ?, ?)",
            (
                _required_string(record, "deck_slug"),
                record.get("title"),
                record.get("version"),
                record.get("scope"),
                payload,
            ),
        )
    else:
        cursor.execute(
            """INSERT INTO practice_deck_items(deck_slug, sense_slug, attestation_id, card_template, record_json)
               VALUES (?, ?, ?, ?, ?)""",
            (
                _required_string(record, "deck_slug"),
                _required_string(record, "sense_slug"),
                record.get("attestation_id"),
                record.get("card_template"),
                payload,
            ),
        )


def _records_for_build(
    records: Iterable[dict[str, Any]], vesum_forms: frozenset[str]
) -> tuple[list[dict[str, Any]], list[RejectedRecord]]:
    by_type = {record_type: [] for record_type in RECORD_TYPES}
    sources: dict[str, dict[str, Any]] = {}
    for record in records:
        record_type, _ = _record_key(record)
        by_type[record_type].append(record)
        if record_type == "source":
            sources[_required_string(record, "source_id")] = record

    accepted: list[dict[str, Any]] = []
    rejected: list[RejectedRecord] = []
    for record_type in RECORD_TYPES:
        for record in by_type[record_type]:
            if record_type == "attestation":
                _validate_attestation_identity(record)
                source_id = _required_string(record, "source_id")
                source = sources.get(source_id)
                if source is None:
                    raise ProjectionError(f"attestation references undeclared source_id {source_id!r}")
                reason = attestation_rejection_reason(record, source, vesum_forms)
                if reason:
                    rejected.append(RejectedRecord(_required_string(record, "attestation_id"), reason, record))
                    continue
            accepted.append(record)
    return accepted, rejected


def _foreign_key_check(connection: sqlite3.Connection) -> None:
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise ProjectionError(f"foreign key check failed: {violations!r}")


def build_projection(
    input_jsonl: Path,
    db_path: Path,
    *,
    vesum_db: Path = DEFAULT_VESUM_DB,
    strict: bool = False,
) -> BuildResult:
    """Build a fresh v2 projection and atomically replace ``db_path`` on success."""
    records = _read_jsonl(input_jsonl)
    attestation_count = sum(record.get("record_type") == "attestation" for record in records)
    vesum_forms = load_vesum_forms(vesum_db) if attestation_count else frozenset()
    accepted, rejected = _records_for_build(records, vesum_forms)
    if strict and rejected:
        raise ProjectionError(
            f"strict build rejected {len(rejected)} attestation record(s): {BuildResult(0, tuple(rejected)).rejection_counts}"
        )

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent, delete=False
    ) as tmp:
        temp_path = Path(tmp.name)
    try:
        with sqlite3.connect(temp_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise ProjectionError("SQLite foreign key enforcement could not be enabled")
            connection.executescript(SCHEMA)
            cursor = connection.cursor()
            for record in accepted:
                _insert_record(cursor, record)
            _foreign_key_check(connection)
            connection.commit()
        os.replace(temp_path, db_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return BuildResult(accepted_records=len(accepted), rejected_records=tuple(rejected))


def export_projection(db_path: Path, output_jsonl: Path) -> None:
    """Export accepted v2 source records in canonical deterministic JSONL order."""
    rows: list[dict[str, Any]] = []
    tables = {
        "source": "sources",
        "lemma_entry": "lemma_entries",
        "sense": "senses",
        "attestation": "attestations",
        "practice_deck": "practice_decks",
        "practice_deck_item": "practice_deck_items",
    }
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
        for record_type, table in tables.items():
            for row in connection.execute(f"SELECT record_json FROM {table}"):
                record = json.loads(row[0])
                if record.get("record_type") != record_type:
                    raise ProjectionError(f"{table} row has mismatched record_type")
                rows.append(record)
    rows.sort(key=lambda record: (RECORD_TYPE_ORDER[str(record["record_type"])], _record_key(record)[1]))
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.write_text("".join(f"{canonical_json(record)}\n" for record in rows), encoding="utf-8")


def write_rejection_report(result: BuildResult, output_jsonl: Path) -> None:
    """Write rejected rows in a deterministic, auditable JSONL format."""
    rows = [
        {"attestation_id": item.attestation_id, "gate_failed": item.reason, "record": item.record}
        for item in sorted(result.rejected_records, key=lambda item: (item.reason, item.attestation_id))
    ]
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.write_text("".join(f"{canonical_json(row)}\n" for row in rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the ADR-017 Atlas lexical v2 projection.")
    parser.add_argument("--input", required=True, type=Path, help="Canonical lexical source JSONL")
    parser.add_argument("--db", required=True, type=Path, help="Projection SQLite path")
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--export", type=Path, help="Optional canonical JSONL export path")
    parser.add_argument("--rejections", type=Path, help="Optional rejected-attestation JSONL report")
    parser.add_argument(
        "--strict", action="store_true", help="Fail instead of writing a projection when a gate rejects a row"
    )
    args = parser.parse_args()
    try:
        result = build_projection(args.input, args.db, vesum_db=args.vesum_db, strict=args.strict)
        if args.export:
            export_projection(args.db, args.export)
        if args.rejections:
            write_rejection_report(result, args.rejections)
        print(
            json.dumps(
                {"accepted_records": result.accepted_records, "rejections": result.rejection_counts}, sort_keys=True
            )
        )
    except ProjectionError as exc:
        raise SystemExit(f"lexical projection failed: {exc}") from exc


if __name__ == "__main__":
    main()
