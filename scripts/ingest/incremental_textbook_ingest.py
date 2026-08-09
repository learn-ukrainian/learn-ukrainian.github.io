"""Incrementally ingest textbook chunk JSONL files into the live sources.db.

The #4593 wave-1 path (reused for wave 2+): no destructive ``--force``
rebuild — per the safe recipe in docs/corpus-inventory.md, each book is
DELETE-then-INSERT inside one transaction, followed by an external-content
FTS resync (the delete fires no FTS trigger, so a rebuild is mandatory).

Rows are built via ``build_sources_db._build_textbook_row`` so the subject
column and the author_uk strictness gate apply exactly as in a full rebuild.
JSONL entries carry ``author_uk: null`` (extraction emits Latin slugs only),
so entries are enriched from ``AUTHOR_UK`` first — canonical Cyrillic forms
title-probed from the source pages during wave-1 acquisition (2026-07-06).

Usage:
    .venv/bin/python scripts/ingest/incremental_textbook_ingest.py \
        --slugs 9-klas-khimiya-popel-2017 [...] \
        [--db data/sources.db] [--chunks-root GDRIVE/textbook_chunks] [--dry-run]
    .venv/bin/python scripts/ingest/incremental_textbook_ingest.py --wave1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from projects.open_model_data.textbook_native_exactness import (
    SCHEMA_VERSION as NATIVE_EXACTNESS_SCHEMA_VERSION,
)
from projects.open_model_data.textbook_native_exactness import (
    ExactnessAuditError,
    atomic_write,
    load_jsonl_rows,
    require_production_eligible_entry,
    sha256_file,
)
from projects.open_model_data.university_source_policy import (
    DEFAULT_POLICY_PATH as DEFAULT_UNIVERSITY_POLICY,
)
from projects.open_model_data.university_source_policy import (
    UniversitySourcePolicyError,
    require_source_admission,
)
from wiki.build_sources_db import _build_textbook_row
from wiki.config import TEXTBOOK_CHUNKS_DIR
from wiki.extract_sections import (
    ChunkRow,
    SectionAssignment,
    assign_sections,
    build_section_groups,
    ensure_schema,
    is_page_placeholder,
    load_textbook_rows,
    parse_page_number,
)
from wiki.textbook_subjects import AUTHOR_UK_BY_TRANSLIT

# The canonical chunk store is the Google Drive corpus mount. Keep this
# constant patchable for local fixtures, but do not assume the absent
# repo-local data/textbook_chunks directory is the production source.
CHUNKS_DIR = TEXTBOOK_CHUNKS_DIR
DEFAULT_DB = PROJECT_ROOT / "data" / "sources.db"

# Author map: single source of truth in wiki.textbook_subjects (PR #4650).
AUTHOR_UK = AUTHOR_UK_BY_TRANSLIT

WAVE1_SLUGS: tuple[str, ...] = (
    "5-klas-informatyka-ryvkind-2022",
    "5-klas-matematyka-ister-2022",
    "6-klas-informatyka-ryvkind-2023",
    "6-klas-matematyka-ister-2023",
    "7-klas-algebra-merzliak-2024",
    "7-klas-biolohiya-zadorozhnyi-2024",
    "7-klas-fizyka-bariakhtar-2024",
    "7-klas-heometriya-merzliak-2024",
    "7-klas-informatyka-ryvkind-2024",
    "7-klas-khimiya-hryhorovych-2024",
    "8-klas-algebra-merzliak-2025",
    "8-klas-biolohiya-anderson-2025",
    "8-klas-fizyka-bariakhtar-2025",
    "8-klas-heometriya-burda-tarasenkova-2025",
    "8-klas-informatyka-ryvkind-2025",
    "8-klas-khimiya-hryhorovych-2025",
    "9-klas-algebra-merzliak-2017",
    "9-klas-biolohiya-zadorozhnyi-2026",
    "9-klas-fizyka-bariakhtar-2022",
    "9-klas-heometriya-merzliak-2017",
    "9-klas-informatyka-ryvkind-2017",
    "9-klas-khimiya-popel-2017",
)


class IngestError(RuntimeError):
    """Deterministic ingest failure."""


def find_jsonl(slug: str, *, chunks_root: Path | None = None) -> Path:
    """Resolve one source JSONL under the explicit or canonical chunk root."""
    root = Path(chunks_root) if chunks_root is not None else CHUNKS_DIR
    if slug.startswith("uni-"):
        path = root / "grade-00" / f"{slug}.jsonl"
    else:
        grade = int(slug.split("-")[0])
        path = root / f"grade-{grade:02d}" / f"{slug}.jsonl"
    if path.is_file():
        return path
    exact_matches = sorted(root.glob(f"grade-*/{slug}.jsonl"))
    if len(exact_matches) == 1:
        return exact_matches[0]
    if not exact_matches:
        raise IngestError(f"chunk file missing: {path}")
    raise IngestError(f"chunk file is ambiguous for {slug}: {exact_matches}")


def enrich_author_uk(entry: dict, *, slug: str) -> dict:
    """Fill author_uk from the canonical mapping when extraction left it null."""
    author = str(entry.get("author") or "").strip()
    if author and not str(entry.get("author_uk") or "").strip():
        uk = AUTHOR_UK.get(author.lower())
        if uk is None:
            raise IngestError(
                f"{slug}: author {author!r} has no canonical Cyrillic form in "
                "AUTHOR_UK — add it (title-probed, never guessed) before ingest."
            )
        entry = {**entry, "author_uk": uk}
    return entry


def require_verified_ocr(entry: dict, *, slug: str) -> None:
    """Refuse any uncertain page text without exact page-image verification.

    OCR always requires verification.  Native text can also require it when
    deterministic extraction records a logical-layer anomaly.  Model agreement
    is never accepted as evidence.
    """
    try:
        require_production_eligible_entry(entry, source_file=slug)
    except ExactnessAuditError as exc:
        raise IngestError(str(exc)) from exc


def build_rows(
    slug: str,
    *,
    chunks_root: Path | None = None,
    university_policy_path: Path = DEFAULT_UNIVERSITY_POLICY,
) -> list[tuple]:
    jsonl_path = find_jsonl(slug, chunks_root=chunks_root)
    university_source = slug.startswith("uni-")
    if university_source:
        try:
            require_source_admission(
                source_file=slug,
                jsonl_path=jsonl_path,
                policy_path=university_policy_path,
                lane="corpus_ingest",
            )
        except UniversitySourcePolicyError as exc:
            raise IngestError(str(exc)) from exc
    grade = "university" if university_source else f"grade-{int(slug.split('-')[0]):02d}"
    rows: list[tuple] = []
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            require_verified_ocr(entry, slug=slug)
            if university_source:
                entry = {**entry, "grade": "university"}
            entry = enrich_author_uk(entry, slug=slug)
            rows.append(
                _build_textbook_row(
                    entry,
                    source_file=slug,
                    grade=grade,
                    chunk_index=len(rows),
                )
            )
    if not rows:
        raise IngestError(f"{slug}: no chunks in {jsonl_path}")
    return rows


TB_SQL = """INSERT INTO textbooks
            (chunk_id, title, text, source_file, subject, grade, author,
             author_uk, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""


SECTION_INSERT_SQL = """INSERT INTO textbook_sections
    (source_file, grade, section_title, section_number, page_start, page_end,
     chunk_count, full_text)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""


FRONT_MATTER_SECTION = "Вступні матеріали"


def _section_row_for_grouping(row: ChunkRow) -> ChunkRow:
    """Map the university DB label to numeric grade zero for section grouping."""
    if row.grade != "university":
        return row
    return ChunkRow(
        id=row.id,
        chunk_id=row.chunk_id,
        title=row.title,
        text=row.text,
        source_file=row.source_file,
        grade="grade-00",
    )


def _assign_leading_front_matter(
    assignments: list[SectionAssignment],
) -> list[SectionAssignment]:
    """Assign a real parent to preface rows before the first detected heading.

    Title, imprint, contents, and author-preface pages commonly precede the
    first machine-detectable chapter. They belong to a bounded synthetic front
    matter section. A source with no detected heading at all still fails closed;
    this helper does not turn arbitrary unstructured content into a section.
    """
    first_assigned = next(
        (index for index, item in enumerate(assignments) if item.section_title is not None),
        None,
    )
    if first_assigned in {None, 0}:
        return assignments
    return [
        SectionAssignment(
            row=item.row,
            page_number=item.page_number,
            section_title=FRONT_MATTER_SECTION,
        )
        if index < first_assigned and item.section_title is None
        else item
        for index, item in enumerate(assignments)
    ]


def _rebuild_source_sections(conn: sqlite3.Connection, slug: str) -> tuple[int, int, str]:
    """Replace only one source's section rows and parent links.

    The existing extraction helpers provide deterministic assignment and
    grouping. This writer deliberately avoids ``persist_sections`` because
    that helper clears every textbook section and every parent link in the
    database, which is not safe for an incremental source replacement.

    Page-labelled extraction is intentionally not passed through semantic
    heading inference. Its exact PDF page labels are already sufficient parent
    units, while promoting body text to a likely heading would invent source
    structure that the extraction did not supply.
    """
    ensure_schema(conn)
    source_rows = [row for row in load_textbook_rows(conn) if row.source_file == slug]
    if source_rows and all(is_page_placeholder(row.title) for row in source_rows):
        assignments = [
            SectionAssignment(
                row=_section_row_for_grouping(row),
                page_number=parse_page_number(row),
                section_title=row.title,
            )
            for row in source_rows
        ]
        section_policy = "exact_page_labels"
    else:
        assignments = _assign_leading_front_matter(assign_sections(source_rows))
        section_policy = "explicit_or_detected_sections"
    sections = build_section_groups(assignments)

    # Null links before deleting section parents so this remains valid if a
    # caller has enabled foreign-key enforcement on the connection.
    conn.execute(
        "UPDATE textbooks SET parent_section_id = NULL WHERE source_file = ?",
        (slug,),
    )
    conn.execute("DELETE FROM textbook_sections WHERE source_file = ?", (slug,))

    section_id_by_row_id: dict[int, int] = {}
    for section in sections:
        cursor = conn.execute(
            SECTION_INSERT_SQL,
            (
                section.source_file,
                section.grade,
                section.section_title,
                section.section_number,
                section.page_start,
                section.page_end,
                section.chunk_count,
                section.full_text,
            ),
        )
        section_id = cursor.lastrowid
        for assignment in section.rows:
            section_id_by_row_id[assignment.row.id] = section_id

    links = [
        (section_id_by_row_id[assignment.row.id], assignment.row.id)
        for assignment in assignments
        if assignment.section_title is not None
    ]
    conn.executemany(
        "UPDATE textbooks SET parent_section_id = ? WHERE id = ?",
        links,
    )
    linked_rows = conn.execute(
        """SELECT COUNT(*) FROM textbooks
           WHERE source_file = ? AND parent_section_id IS NOT NULL""",
        (slug,),
    ).fetchone()[0]
    total_rows = len(source_rows)
    if linked_rows != total_rows:
        raise IngestError(
            f"{slug}: {total_rows - linked_rows} accepted school-textbook rows remain unlinked from textbook_sections"
        )
    return len(sections), linked_rows, section_policy


def _fts_source_evidence(
    conn: sqlite3.Connection,
    slug: str,
    expected_rows: int,
) -> dict[str, object]:
    """Return and validate the source's external-content FTS row parity."""
    indexed_rows = conn.execute(
        """SELECT COUNT(*) FROM textbooks_fts AS f
           JOIN textbooks AS t ON t.id = f.rowid
           WHERE t.source_file = ?""",
        (slug,),
    ).fetchone()[0]
    evidence = {
        "source_file": slug,
        "expected_rows": expected_rows,
        "indexed_rows": indexed_rows,
        "parity": indexed_rows == expected_rows,
    }
    if not evidence["parity"]:
        raise IngestError(
            f"{slug}: textbooks/textbooks_fts parity failed ({indexed_rows} indexed, {expected_rows} rows)"
        )
    return evidence


def _database_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Return the corpus-table counts used by mutation receipts."""
    return {
        "textbook_rows": conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
        "fts_rows": conn.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
        "section_rows": conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
    }


def _foreign_key_evidence(conn: sqlite3.Connection) -> tuple[list[tuple[Any, ...]], str]:
    """Return deterministic foreign-key failures and their compact hash."""
    failures = sorted(tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall())
    digest = hashlib.sha256(
        json.dumps(failures, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return failures, digest


def ingest(
    slugs: list[str],
    *,
    db_path: Path,
    dry_run: bool,
    chunks_root: Path | None = None,
    quarantine_slugs: list[str] | None = None,
    receipt_path: Path | None = None,
    university_policy_path: Path = DEFAULT_UNIVERSITY_POLICY,
) -> dict[str, int]:
    """Run one atomic replace/quarantine/FTS-resync cycle.

    Concurrency note (review, PR #4624): sources.db runs in WAL mode in
    production, so MCP readers are not blocked by this writer; still,
    prefer running while no build/review dispatch is mid-flight.
    """
    quarantine_slugs = list(quarantine_slugs or [])
    overlap = sorted(set(slugs) & set(quarantine_slugs))
    if overlap:
        raise IngestError(f"sources cannot be replaced and quarantined together: {overlap}")
    counts: dict[str, int] = {}
    receipts: dict[str, dict[str, object]] = {}
    per_slug_rows = {
        slug: build_rows(
            slug,
            chunks_root=chunks_root,
            university_policy_path=university_policy_path,
        )
        for slug in slugs
    }  # fail fast, pre-tx
    university_admissions: dict[str, dict[str, Any]] = {}
    for slug in slugs:
        if not slug.startswith("uni-"):
            continue
        jsonl_path = find_jsonl(slug, chunks_root=chunks_root)
        try:
            university_admissions[slug] = require_source_admission(
                source_file=slug,
                jsonl_path=jsonl_path,
                policy_path=university_policy_path,
                lane="corpus_ingest",
            )
        except UniversitySourcePolicyError as exc:
            raise IngestError(str(exc)) from exc
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    committed = False
    checkpoint: list[int] | None = None
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if journal_mode == "wal":
            preflight_checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if preflight_checkpoint != [0, 0, 0]:
                raise IngestError(f"WAL was not settled before ingest: {preflight_checkpoint}")
        db_sha256_before = sha256_file(db_path)
        conn.execute("BEGIN IMMEDIATE")
        ensure_schema(conn)
        foreign_key_failures_before, foreign_key_hash_before = _foreign_key_evidence(conn)
        before = _database_counts(conn)
        for slug in quarantine_slugs:
            deleted = conn.execute("DELETE FROM textbooks WHERE source_file = ?", (slug,)).rowcount
            deleted_sections = conn.execute("DELETE FROM textbook_sections WHERE source_file = ?", (slug,)).rowcount
            receipts[slug] = {
                "source_file": slug,
                "disposition": "quarantined_unverified_ocr",
                "deleted_rows": deleted,
                "deleted_sections": deleted_sections,
            }
            print(f"  {slug}: quarantined {deleted} rows and {deleted_sections} sections")
        for slug, rows in per_slug_rows.items():
            deleted = conn.execute("DELETE FROM textbooks WHERE source_file = ?", (slug,)).rowcount
            conn.executemany(TB_SQL, rows)
            section_rows, linked_rows, section_policy = _rebuild_source_sections(conn, slug)
            counts[slug] = len(rows)
            receipts[slug] = {
                "source_file": slug,
                "deleted_rows": deleted,
                "inserted_rows": len(rows),
                "section_rows": section_rows,
                "linked_rows": linked_rows,
                "section_policy": section_policy,
            }
            if slug in university_admissions:
                receipts[slug]["university_source_policy"] = university_admissions[slug]
            print(f"  {slug}: deleted {deleted}, inserted {len(rows)}, sections {section_rows}, links {linked_rows}")
        print("  resyncing textbooks_fts (external-content rebuild)…")
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        for slug, rows in per_slug_rows.items():
            receipts[slug]["fts"] = _fts_source_evidence(conn, slug, len(rows))
            print(f"  FTS evidence: {json.dumps(receipts[slug]['fts'], ensure_ascii=False)}")
        for slug in quarantine_slugs:
            receipts[slug]["fts"] = _fts_source_evidence(conn, slug, 0)
            print(f"  quarantine FTS evidence: {json.dumps(receipts[slug]['fts'], ensure_ascii=False)}")
        after = _database_counts(conn)
        if after["textbook_rows"] != after["fts_rows"]:
            raise IngestError("global textbooks/textbooks_fts row parity failed after ingest")
        foreign_key_failures_after, foreign_key_hash_after = _foreign_key_evidence(conn)
        integrity_rows = [str(row[0]) for row in conn.execute("PRAGMA integrity_check").fetchall()]
        integrity = "ok" if integrity_rows == ["ok"] else integrity_rows
        if foreign_key_failures_after != foreign_key_failures_before or integrity != "ok":
            raise IngestError(
                "database validation failed: "
                f"foreign_keys_before={len(foreign_key_failures_before)} "
                f"foreign_keys_after={len(foreign_key_failures_after)} integrity={integrity!r}"
            )
        if dry_run:
            conn.execute("ROLLBACK")
            print("  DRY-RUN: rolled back")
        else:
            conn.execute("COMMIT")
            committed = True
        if journal_mode == "wal":
            checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if checkpoint != [0, 0, 0]:
                raise IngestError(f"WAL checkpoint did not settle after ingest: {checkpoint}")
    except BaseException:
        # Explicit rollback (review, PR #4624): never leave the live DB with
        # an open write transaction on the error path.
        conn.rollback()
        raise
    finally:
        conn.close()
    receipt_document = {
        "schema_version": "incremental-textbook-ingest.v2",
        "status": "committed" if committed else "dry_run_rolled_back",
        "db_path": str(db_path),
        "db_sha256_before": db_sha256_before,
        "db_sha256_after": sha256_file(db_path),
        "requested_replace_sources": sorted(slugs),
        "requested_quarantine_sources": sorted(quarantine_slugs),
        "university_source_policy_sha256": (
            sha256_file(Path(university_policy_path)) if university_admissions else None
        ),
        "before": before,
        "after_transaction": after,
        "integrity_check": integrity,
        "foreign_key_failure_count_before": len(foreign_key_failures_before),
        "foreign_key_failure_count_after": len(foreign_key_failures_after),
        "foreign_key_failure_hash_before": foreign_key_hash_before,
        "foreign_key_failure_hash_after": foreign_key_hash_after,
        "foreign_key_failures_unchanged": foreign_key_failures_after == foreign_key_failures_before,
        "wal_checkpoint": checkpoint,
        "per_source": [receipts[slug] for slug in sorted(receipts)],
    }
    if receipt_path is not None:
        atomic_write(
            Path(receipt_path),
            json.dumps(receipt_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    for _slug, receipt in receipts.items():
        print(f"  receipt: {json.dumps(receipt, ensure_ascii=False, sort_keys=True)}")
    return counts


def load_native_anomaly_quarantine_plan(
    audit_path: Path,
    *,
    chunks_root: Path,
    quarantine_dir: Path,
) -> dict[str, list[str]]:
    """Verify a hash-bound exactness audit and its preserved source rows."""
    audit_path = Path(audit_path)
    chunks_root = Path(chunks_root).resolve()
    quarantine_dir = Path(quarantine_dir)
    document = json.loads(audit_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != NATIVE_EXACTNESS_SCHEMA_VERSION:
        raise IngestError(f"unsupported native-exactness audit schema: {document.get('schema_version')!r}")

    archived_manifest = quarantine_dir / "textbook-native-exactness-audit-v1.json"
    if not archived_manifest.is_file() or sha256_file(archived_manifest) != sha256_file(audit_path):
        raise IngestError("quarantine audit manifest is absent or differs from the requested audit")

    plan: dict[str, list[str]] = {}
    for source in document.get("sources", []):
        if not isinstance(source, dict):
            raise IngestError("native-exactness audit source entry is not an object")
        findings = source.get("findings")
        if not findings:
            continue
        source_file = str(source.get("source_file") or "").strip()
        relative_jsonl = Path(str(source.get("relative_jsonl") or ""))
        jsonl_path = (chunks_root / relative_jsonl).resolve()
        if not source_file or not jsonl_path.is_relative_to(chunks_root) or jsonl_path.stem != source_file:
            raise IngestError(f"unsafe or inconsistent audit path for source {source_file!r}")
        if not jsonl_path.is_file() or sha256_file(jsonl_path) != source.get("jsonl_sha256"):
            raise IngestError(f"{source_file}: canonical JSONL is absent or changed since audit")

        canonical_rows = load_jsonl_rows(jsonl_path)
        canonical_by_id = {str(row.get("chunk_id") or ""): row for row in canonical_rows}
        chunk_ids = [str(item.get("chunk_id") or "") for item in findings if isinstance(item, dict)]
        if not chunk_ids or any(not chunk_id for chunk_id in chunk_ids) or len(chunk_ids) != len(set(chunk_ids)):
            raise IngestError(f"{source_file}: audit has missing or duplicate flagged chunk ids")
        if any(chunk_id not in canonical_by_id for chunk_id in chunk_ids):
            raise IngestError(f"{source_file}: audit references a chunk absent from canonical JSONL")

        archive_path = quarantine_dir / f"{source_file}.jsonl"
        if not archive_path.is_file():
            raise IngestError(f"{source_file}: preserved quarantine JSONL is absent")
        archived_rows = load_jsonl_rows(archive_path)
        archived_by_id = {str(row.get("chunk_id") or ""): row for row in archived_rows}
        if set(archived_by_id) != set(chunk_ids):
            raise IngestError(f"{source_file}: quarantine chunk-id set differs from audit")
        if any(archived_by_id[chunk_id] != canonical_by_id[chunk_id] for chunk_id in chunk_ids):
            raise IngestError(f"{source_file}: quarantine row differs from canonical source row")
        plan[source_file] = sorted(chunk_ids)

    expected_sources = int(document.get("flagged_source_count") or 0)
    expected_chunks = int(document.get("flagged_chunk_count") or 0)
    if len(plan) != expected_sources or sum(map(len, plan.values())) != expected_chunks:
        raise IngestError("audit totals do not equal the exact quarantine plan")
    return plan


def quarantine_native_anomaly_chunks(
    *,
    audit_path: Path,
    chunks_root: Path,
    quarantine_dir: Path,
    db_path: Path,
    dry_run: bool,
) -> dict[str, Any]:
    """Atomically remove only hash-bound anomalous chunks from production search."""
    plan = load_native_anomaly_quarantine_plan(
        audit_path,
        chunks_root=chunks_root,
        quarantine_dir=quarantine_dir,
    )
    db_path = Path(db_path)
    per_source: list[dict[str, Any]] = []
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    committed = False
    checkpoint: list[int] | None = None
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if journal_mode == "wal":
            preflight_checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
            if preflight_checkpoint != [0, 0, 0]:
                raise IngestError(f"WAL was not settled before quarantine: {preflight_checkpoint}")
        db_sha256_before = sha256_file(db_path)
        conn.execute("BEGIN IMMEDIATE")
        foreign_key_failures_before = sorted(
            tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall()
        )
        foreign_key_hash_before = hashlib.sha256(
            json.dumps(foreign_key_failures_before, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        before = {
            "textbook_rows": conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
            "fts_rows": conn.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
            "section_rows": conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
        }
        for source_file, chunk_ids in sorted(plan.items()):
            existing_ids = {
                str(row[0])
                for row in conn.execute(
                    "SELECT chunk_id FROM textbooks WHERE source_file = ?",
                    (source_file,),
                )
            }
            already_absent_ids = sorted(set(chunk_ids) - existing_ids)
            present_chunk_ids = sorted(set(chunk_ids) & existing_ids)
            rows_before = len(existing_ids)
            if present_chunk_ids:
                conn.executemany(
                    "DELETE FROM textbooks WHERE source_file = ? AND chunk_id = ?",
                    [(source_file, chunk_id) for chunk_id in present_chunk_ids],
                )
                section_rows, linked_rows, section_policy = _rebuild_source_sections(conn, source_file)
            else:
                section_rows = conn.execute(
                    "SELECT COUNT(*) FROM textbook_sections WHERE source_file = ?",
                    (source_file,),
                ).fetchone()[0]
                linked_rows = conn.execute(
                    "SELECT COUNT(*) FROM textbooks WHERE source_file = ? AND parent_section_id IS NOT NULL",
                    (source_file,),
                ).fetchone()[0]
                section_policy = "unchanged_already_absent"
            rows_after = conn.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file = ?",
                (source_file,),
            ).fetchone()[0]
            if rows_before - rows_after != len(present_chunk_ids):
                raise IngestError(f"{source_file}: database deletion count differs from audit")
            remaining = conn.execute(
                f"SELECT chunk_id FROM textbooks WHERE source_file = ? "
                f"AND chunk_id IN ({','.join('?' for _ in chunk_ids)})",
                (source_file, *chunk_ids),
            ).fetchall()
            if remaining:
                raise IngestError(f"{source_file}: audited chunks remain after quarantine")
            per_source.append(
                {
                    "source_file": source_file,
                    "audited_chunk_count": len(chunk_ids),
                    "removed_chunk_count": len(present_chunk_ids),
                    "removed_chunk_ids": present_chunk_ids,
                    "already_absent_chunk_count": len(already_absent_ids),
                    "already_absent_chunk_ids": already_absent_ids,
                    "rows_before": rows_before,
                    "rows_after": rows_after,
                    "section_rows_after": section_rows,
                    "linked_rows_after": linked_rows,
                    "section_policy": section_policy,
                }
            )

        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        after = {
            "textbook_rows": conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
            "fts_rows": conn.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
            "section_rows": conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
        }
        if after["textbook_rows"] != after["fts_rows"]:
            raise IngestError("global textbooks/textbooks_fts row parity failed after quarantine")
        foreign_key_failures_after = sorted(
            tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall()
        )
        foreign_key_hash_after = hashlib.sha256(
            json.dumps(foreign_key_failures_after, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        if foreign_key_failures_after != foreign_key_failures_before or integrity != "ok":
            raise IngestError(
                "database validation failed: "
                f"foreign_keys_before={len(foreign_key_failures_before)} "
                f"foreign_keys_after={len(foreign_key_failures_after)} integrity={integrity!r}"
            )
        if dry_run:
            conn.execute("ROLLBACK")
        else:
            conn.execute("COMMIT")
            committed = True
            if journal_mode == "wal":
                checkpoint = list(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
                if checkpoint != [0, 0, 0]:
                    raise IngestError(f"WAL checkpoint did not settle after quarantine: {checkpoint}")
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "schema_version": "textbook-native-anomaly-quarantine.v1",
        "status": "committed" if committed else "dry_run_rolled_back",
        "policy": "Exact audited chunk ids only; no text repair, replacement, or inferred deletion.",
        "audit_path": str(Path(audit_path)),
        "audit_sha256": sha256_file(Path(audit_path)),
        "quarantine_dir": str(Path(quarantine_dir)),
        "db_path": str(db_path),
        "db_sha256_before": db_sha256_before,
        "db_sha256_after": sha256_file(db_path),
        "audited_source_count": len(per_source),
        "removed_source_count": sum(int(item["removed_chunk_count"] > 0) for item in per_source),
        "removed_chunk_count": sum(int(item["removed_chunk_count"]) for item in per_source),
        "already_absent_chunk_count": sum(
            int(item["already_absent_chunk_count"]) for item in per_source
        ),
        "before": before,
        "after_transaction": after,
        "integrity_check": integrity,
        "foreign_key_failure_count_before": len(foreign_key_failures_before),
        "foreign_key_failure_count_after": len(foreign_key_failures_after),
        "foreign_key_failure_hash_before": foreign_key_hash_before,
        "foreign_key_failure_hash_after": foreign_key_hash_after,
        "foreign_key_failures_unchanged": foreign_key_failures_after == foreign_key_failures_before,
        "wal_checkpoint": checkpoint,
        "per_source": per_source,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slugs", nargs="+", help="Canonical source_file slugs")
    group.add_argument("--wave1", action="store_true", help="Ingest the 22 #4593 wave-1 books")
    group.add_argument(
        "--quarantine-audit",
        type=Path,
        help="Hash-bound textbook-native-exactness audit whose exact chunk ids must leave production search",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--chunks-root",
        type=Path,
        default=CHUNKS_DIR,
        help="Canonical textbook chunk directory (Google Drive mount or fixture root)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quarantine-dir", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument(
        "--university-policy",
        type=Path,
        default=DEFAULT_UNIVERSITY_POLICY,
        help="Hash-bound audience/lane policy required for every uni-* source",
    )
    args = parser.parse_args(argv)

    try:
        if args.quarantine_audit:
            if args.quarantine_dir is None:
                raise IngestError("--quarantine-dir is required with --quarantine-audit")
            receipt = quarantine_native_anomaly_chunks(
                audit_path=args.quarantine_audit,
                chunks_root=args.chunks_root,
                quarantine_dir=args.quarantine_dir,
                db_path=args.db,
                dry_run=args.dry_run,
            )
            if args.receipt:
                atomic_write(
                    args.receipt,
                    json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                )
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
            return 0
        slugs = list(WAVE1_SLUGS) if args.wave1 else list(args.slugs)
        counts = ingest(
            slugs,
            db_path=args.db,
            dry_run=args.dry_run,
            chunks_root=args.chunks_root,
            receipt_path=args.receipt,
            university_policy_path=args.university_policy,
        )
    except (IngestError, ValueError) as exc:
        # ValueError: _build_textbook_row's strictness gates (author_uk,
        # unmapped subject) — surface cleanly instead of a traceback.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    total = sum(counts.values())
    print(f"OK: {len(counts)} books, {total} chunks{' (dry-run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
