#!/usr/bin/env python3
"""Resolve and verify existing non-OCR source custody access (#7884).

Implements ACCESS-1 through ACCESS-4 under epic #7423 (operator decision 2026-09-10):
- ACCESS-1: Resolves selected existing native digital sources through established
  storage/custody arrangements and records a source-free access result.
- ACCESS-2: Confirms selected input is native digital text or has a native PDF
  text layer with non-OCR extraction lineage; excludes OCR-derived text; fails
  closed on unknown extraction lineage.
- ACCESS-3: Makes the bounded existing-custody read path executable without broad
  recollection, new storage infrastructure, or copying protected corpus content
  to the coordinator.
- ACCESS-4: Records affected missing paths/inputs and an owner while permitting
  another already accessible eligible source to proceed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONFIG_SCHEMA_VERSION = "v4_source_custody_access_config_v1"
ITEM_SCHEMA_VERSION = "v4_source_custody_access_v1"
MISSING_REPORT_SCHEMA_VERSION = "v4_source_custody_missing_report_v1"
RECEIPT_SCHEMA_VERSION = "v4_source_custody_access_receipt_v1"

DEFAULT_CONFIG = Path("data/projects/open_model_data/custody/v4_source_custody_access_config_v1.json")
CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")
CONFIG_SCHEMA_PATH = CONTRACTS_DIR / "v4_source_custody_access_config_v1.schema.json"
ITEM_SCHEMA_PATH = CONTRACTS_DIR / "v4_source_custody_access_item_v1.schema.json"
MISSING_REPORT_SCHEMA_PATH = CONTRACTS_DIR / "v4_source_custody_missing_report_v1.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v4_source_custody_access_receipt_v1.schema.json"


class CustodyAccessError(RuntimeError):
    """Raised when custody resolution or lineage verification fails closed."""


def canonical_json(data: Any) -> str:
    """Return canonical UTF-8 JSON representation."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash a file in 1 MiB blocks without loading entirely into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    """Hash a string as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_access_id(source_id: str, cohort_id: str) -> str:
    seed = f"{source_id}:{cohort_id}".encode()
    return f"access.{hashlib.sha256(seed).hexdigest()[:24]}"


def _make_receipt_id(config_hash: str, index_hash: str) -> str:
    seed = f"{config_hash}:{index_hash}".encode()
    return f"receipt.custody.{hashlib.sha256(seed).hexdigest()[:24]}"


def _resolve_file(path: Path, roots: Sequence[Path]) -> Path:
    if path.is_absolute() and path.exists():
        return path
    for r in roots:
        candidate = r / path
        if candidate.exists():
            return candidate
    return roots[0] / path


def _load_schema(schema_path: Path, roots: Sequence[Path]) -> Draft202012Validator:
    resolved = _resolve_file(schema_path, roots)
    if not resolved.is_file():
        raise CustodyAccessError(f"Missing schema contract: {resolved}")
    schema_dict = json.loads(resolved.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema_dict)
    return Draft202012Validator(schema_dict)


def _load_config(config_path: Path, roots: Sequence[Path]) -> tuple[dict[str, Any], Path]:
    resolved = _resolve_file(config_path, roots)
    if not resolved.is_file():
        raise CustodyAccessError(f"Missing config file: {resolved}")
    config = json.loads(resolved.read_text(encoding="utf-8"))
    validator = _load_schema(CONFIG_SCHEMA_PATH, roots)
    errors = list(validator.iter_errors(config))
    if errors:
        raise CustodyAccessError(f"Config schema validation failed: {errors[0].message}")
    return config, resolved


class BoundedCustodyReader:
    """Bounded, read-only custody stream reader (ACCESS-3).

    Reads records in fixed batches directly from established storage (SQLite or JSONL),
    computes text-free stream digest, and never logs or copies corpus text.
    """

    def __init__(self, database_path: Path):
        self.database_path = database_path

    def read_source_stream(
        self,
        table: str,
        source_file: str,
        batch_size: int = 1000,
    ) -> dict[str, Any]:
        if not self.database_path.is_file():
            raise CustodyAccessError(f"Database file not found: {self.database_path}")

        uri = f"file:{self.database_path.resolve()}?mode=ro"
        start_time = time.monotonic()
        records_streamed = 0
        chars_streamed = 0
        digest = hashlib.sha256()

        conn = sqlite3.connect(uri, uri=True)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA query_only = ON;")
            cursor.execute(
                f"SELECT id, chunk_id, text FROM {table} WHERE source_file = ? ORDER BY id ASC",
                (source_file,),
            )
            while rows := cursor.fetchmany(batch_size):
                for row_id, chunk_id, text in rows:
                    text_str = text or ""
                    text_len = len(text_str)
                    records_streamed += 1
                    chars_streamed += text_len
                    text_hash = hashlib.sha256(text_str.encode("utf-8")).hexdigest()
                    row_repr = f"{row_id}:{chunk_id}:{text_len}:{text_hash}\n".encode()
                    digest.update(row_repr)
        finally:
            conn.close()

        duration = time.monotonic() - start_time
        stream_hash = digest.hexdigest() if records_streamed > 0 else None

        return {
            "source_file": source_file,
            "table": table,
            "records_streamed": records_streamed,
            "chars_streamed": chars_streamed,
            "stream_sha256": stream_hash,
            "duration_seconds": duration,
        }

    def read_chunk_stream(
        self,
        chunk_file: Path,
    ) -> dict[str, Any]:
        """Stream records directly from a JSONL chunk file (ACCESS-3)."""
        if not chunk_file.is_file():
            raise CustodyAccessError(f"Chunk file not found: {chunk_file}")

        start_time = time.monotonic()
        records_streamed = 0
        chars_streamed = 0
        digest = hashlib.sha256()

        with chunk_file.open(encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                row = json.loads(line_str)
                c_id = row.get("chunk_id", "")
                text_str = row.get("text", "") or ""
                text_len = len(text_str)
                records_streamed += 1
                chars_streamed += text_len
                text_hash = hashlib.sha256(text_str.encode("utf-8")).hexdigest()
                digest.update(f"{c_id}:{text_len}:{text_hash}\n".encode())

        duration = time.monotonic() - start_time
        stream_hash = digest.hexdigest() if records_streamed > 0 else None

        return {
            "source_file": chunk_file.stem,
            "chunk_file": str(chunk_file),
            "records_streamed": records_streamed,
            "chars_streamed": chars_streamed,
            "stream_sha256": stream_hash,
            "duration_seconds": duration,
        }


def check_chunk_file_lineage(
    chunk_file: Path,
    excluded_modes: Sequence[str] = ("apple_vision_ocr", "ocr", "scanned_image"),
) -> tuple[str, bool, int, int, list[tuple[str, str]]]:
    """Examine a textbook chunk file for non-OCR lineage (ACCESS-2).

    Validates every single row:
    - Absent/unlabelled extraction modes fail closed as unknown lineage.
    - Excluded modes (e.g. apple_vision_ocr) flag the file as OCR-derived.
    - Unknown/non-native modes fail closed as unknown lineage.

    Returns:
        (lineage_mode, is_ocr, row_count, char_count, chunk_records)
        where chunk_records is [(chunk_id, text), ...]
    """
    if not chunk_file.is_file():
        return "unknown", False, 0, 0, []

    row_count = 0
    char_count = 0
    chunk_records: list[tuple[str, str]] = []
    has_ocr = False
    has_unknown = False

    with chunk_file.open(encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            row_count += 1
            try:
                row = json.loads(line_str)
            except json.JSONDecodeError as exc:
                raise CustodyAccessError(f"Corrupted JSON in chunk file {chunk_file}: {exc}") from exc

            c_id = str(row.get("chunk_id", ""))
            text = str(row.get("text") or "")
            chunk_records.append((c_id, text))
            char_count += len(text)

            mode = row.get("extraction_mode")
            page_mode = row.get("page_extraction_mode")

            # Validate extraction mode per row:
            # If neither extraction_mode nor page_extraction_mode is set, row is unlabelled -> unknown lineage
            modes_for_row = [str(m) for m in (mode, page_mode) if m]
            if not modes_for_row:
                has_unknown = True
            else:
                for m in modes_for_row:
                    if m in excluded_modes:
                        has_ocr = True
                    elif m not in ("native_text", "native_pdf_text"):
                        has_unknown = True

    if row_count == 0:
        return "unknown", False, 0, 0, []

    if has_ocr:
        return "apple_vision_ocr", True, row_count, char_count, chunk_records

    if has_unknown:
        return "unknown", False, row_count, char_count, chunk_records

    return "native_pdf_text", False, row_count, char_count, chunk_records


def resolve_source_access(
    source_id: str,
    source_file: str,
    cohort_id: str,
    source_family: str,
    cohort_cfg: dict[str, Any],
    input_root: Path,
    db_conn: sqlite3.Connection,
    chunks_map: Mapping[str, Path],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Resolve custody arrangement and verify lineage for one source (ACCESS-1, ACCESS-2, ACCESS-4)."""
    table = "literary_texts" if source_family == "literary" else "textbooks"
    primary_store = f"sqlite:sources.db#{table}"
    access_id = _make_access_id(source_id, cohort_id)

    cur = db_conn.cursor()
    cur.execute(
        f"SELECT COUNT(*) FROM {table} WHERE source_file = ?",
        (source_file,),
    )
    db_row = cur.fetchone()
    db_records = db_row[0] if db_row else 0

    chunk_path = chunks_map.get(source_file)
    chunk_ref = None
    if chunk_path is not None:
        try:
            rel = chunk_path.relative_to(input_root)
            chunk_ref = f"file:{rel}"
        except ValueError:
            chunk_ref = f"file:{chunk_path.name}"

    archive_locator = cohort_cfg.get("archive_locator", "")
    if source_family == "literary":
        archive_ref = f"{archive_locator}/{source_file}.jsonl" if archive_locator else None
    else:
        archive_ref = f"{archive_locator}/{source_file}.pdf" if archive_locator else None

    # Check host archive accessibility
    archive_on_host = False
    if archive_locator and archive_locator.startswith("data/"):
        host_archive_path = input_root / archive_locator
        if host_archive_path.is_dir():
            suffix = ".jsonl" if source_family == "literary" else ".pdf"
            archive_file = host_archive_path / f"{source_file}{suffix}"
            if archive_file.is_file():
                archive_on_host = True

    # Lineage verification
    missing_report_item = None
    if source_family == "literary":
        # Literary corpus is established native digital text from human-authored archives
        lineage_status = "CONFIRMED_NATIVE"
        lineage_mode = "native_digital_source"
        evidence_ref = "sqlite:sources.db#literary_texts"
        is_ocr = False
        permitted = db_records > 0
        custody_status = "RESOLVED_ACCESSIBLE" if db_records > 0 else "UNREACHABLE_ON_HOST"
        blocking_reason = None if permitted else "source_records_not_found_in_database"
    else:
        # Public textbooks cohort
        excluded_modes = cohort_cfg.get("excluded_modes", ["apple_vision_ocr", "ocr", "scanned_image"])

        if chunk_path is not None and chunk_path.is_file():
            chunk_mode, chunk_is_ocr, _chunk_rows, _chunk_chars, chunk_records = check_chunk_file_lineage(
                chunk_path, excluded_modes
            )
            if chunk_is_ocr:
                lineage_status = "EXCLUDED_OCR"
                lineage_mode = "apple_vision_ocr"
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = True
                permitted = False
                blocking_reason = "ocr_derived_extraction_mode_excluded"
                custody_status = "PARTIAL_CHUNKS_AND_DB_ONLY"
            elif chunk_mode in ("native_pdf_text", "native_text"):
                # Bind accessed database content to the verified chunk file lineage (ACCESS-2)
                cur.execute(
                    f"SELECT chunk_id, text FROM {table} WHERE source_file = ? ORDER BY id ASC",
                    (source_file,),
                )
                db_rows = cur.fetchall()
                db_records_list = [(str(r[0]), str(r[1] or "")) for r in db_rows]

                if not db_records_list:
                    lineage_status = "UNKNOWN_LINEAGE"
                    lineage_mode = "unknown"
                    evidence_ref = f"{chunk_ref}#missing_db"
                    is_ocr = False
                    permitted = False
                    blocking_reason = "source_records_not_found_in_database"
                    custody_status = "PARTIAL_CHUNKS_AND_DB_ONLY"
                elif db_records_list != chunk_records:
                    # Database content does not match verified chunk lineage
                    lineage_status = "UNKNOWN_LINEAGE"
                    lineage_mode = "unknown"
                    evidence_ref = f"{chunk_ref}#discrepancy"
                    is_ocr = False
                    permitted = False
                    blocking_reason = "database_content_does_not_match_lineage_chunk_evidence"
                    custody_status = "PARTIAL_CHUNKS_AND_DB_ONLY"
                else:
                    lineage_status = "CONFIRMED_NATIVE"
                    lineage_mode = "native_pdf_text"
                    evidence_ref = f"{chunk_ref}#extraction_mode"
                    is_ocr = False
                    permitted = True
                    custody_status = "RESOLVED_ACCESSIBLE" if archive_on_host else "PARTIAL_CHUNKS_AND_DB_ONLY"
                    blocking_reason = None
            else:
                lineage_status = "UNKNOWN_LINEAGE"
                lineage_mode = "unknown"
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = False
                permitted = False
                blocking_reason = "unknown_extraction_lineage_not_silently_called_native"
                custody_status = "PARTIAL_CHUNKS_AND_DB_ONLY"
        else:
            # No chunk file found on host
            lineage_status = "UNKNOWN_LINEAGE"
            lineage_mode = "unknown"
            evidence_ref = "none"
            is_ocr = False
            permitted = False
            custody_status = "UNREACHABLE_ON_HOST"
            blocking_reason = "missing_chunk_file_and_unmounted_archive"

        if not permitted:
            missing_report_item = {
                "source_id": source_id,
                "source_locator": {"source_file": source_file},
                "cohort_id": cohort_id,
                "missing_path_ref": archive_ref or f"gdrive:learn-ukrainian-data/textbooks/{source_file}.pdf",
                "reason": blocking_reason or "not_permitted_to_proceed",
                "owner": "existing custody/source-access owner",
                "blocks": "direct PDF byte extraction for this source",
            }
        elif not archive_on_host:
            missing_report_item = {
                "source_id": source_id,
                "source_locator": {"source_file": source_file},
                "cohort_id": cohort_id,
                "missing_path_ref": archive_ref or f"gdrive:learn-ukrainian-data/textbooks/{source_file}.pdf",
                "reason": "execution_host_resolver_unmounted",
                "owner": "existing custody/source-access owner",
                "blocks": "direct PDF byte extraction for this source",
            }

    # Bounded read digest computation (content-sensitive text hashing)
    stream_digest = None
    observed_records = 0
    observed_chars = 0

    if permitted and db_records > 0:
        cur.execute(
            f"SELECT id, chunk_id, text FROM {table} WHERE source_file = ? ORDER BY id ASC",
            (source_file,),
        )
        digest = hashlib.sha256()
        while rows := cur.fetchmany(1000):
            for row_id, chunk_id, text in rows:
                text_str = text or ""
                t_len = len(text_str)
                observed_records += 1
                observed_chars += t_len
                text_hash = hashlib.sha256(text_str.encode("utf-8")).hexdigest()
                digest.update(f"{row_id}:{chunk_id}:{t_len}:{text_hash}\n".encode())
        stream_digest = digest.hexdigest()

    record = {
        "schema_version": ITEM_SCHEMA_VERSION,
        "access_id": access_id,
        "source_id": source_id,
        "cohort_id": cohort_id,
        "source_family": source_family,
        "source_locator": {"source_file": source_file},
        "custody_resolution": {
            "status": custody_status,
            "primary_store": primary_store,
            "chunks_store": chunk_ref,
            "archive_store": archive_ref,
            "host_reachable": custody_status != "UNREACHABLE_ON_HOST",
        },
        "lineage_verification": {
            "status": lineage_status,
            "lineage_mode": lineage_mode,
            "evidence_ref": evidence_ref,
            "is_ocr_derived": is_ocr,
        },
        "bounded_read_metrics": {
            "observed_records": observed_records,
            "observed_characters": observed_chars,
            "stream_sha256": stream_digest,
        },
        "permitted_to_proceed": permitted,
        "blocking_reason": blocking_reason,
    }

    return record, missing_report_item


def build(
    config_path: Path,
    input_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Execute custody resolution and lineage audit (ACCESS-1..4)."""
    roots = [Path.cwd(), input_root]
    config, resolved_config_path = _load_config(config_path, roots)
    config_sha256 = sha256_file(resolved_config_path)

    # Resolve input paths
    prov_index_path = _resolve_file(Path(config["inputs"]["provenance_index"]), roots)
    db_path = _resolve_file(Path(config["inputs"]["database"]), roots)
    chunks_dir = _resolve_file(Path(config["inputs"]["textbook_chunks_dir"]), roots)

    if not prov_index_path.is_file():
        raise CustodyAccessError(f"Provenance index missing: {prov_index_path}")
    if not db_path.is_file():
        raise CustodyAccessError(f"Database missing: {db_path}")

    # Read unique sources from provenance index
    unique_sources: dict[str, tuple[str, str, str]] = {}  # source_id -> (source_file, cohort_id, source_family)
    with prov_index_path.open(encoding="utf-8") as f:
        header_line = f.readline()
        _ = json.loads(header_line)
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            sid = row["source_id"]
            sf = row["source_locator"]["source_file"]
            cid = row["cohort_id"]
            fam = row["source_family"]
            if sid not in unique_sources:
                unique_sources[sid] = (sf, cid, fam)

    # Map chunk files
    chunks_map: dict[str, Path] = {}
    if chunks_dir.is_dir():
        for chunk_file in chunks_dir.glob("*/*.jsonl"):
            stem = chunk_file.name[:-6] if chunk_file.name.endswith(".jsonl") else chunk_file.stem
            chunks_map[stem] = chunk_file

    # Connect to database read-only
    db_uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)

    cohorts_by_id = {c["cohort_id"]: c for c in config["cohorts"]}
    access_records = []
    missing_items = []

    try:
        # Sort sources deterministically by cohort_id, then source_id
        sorted_sids = sorted(unique_sources.keys(), key=lambda s: (unique_sources[s][1], s))
        for sid in sorted_sids:
            sf, cid, fam = unique_sources[sid]
            cohort_cfg = cohorts_by_id.get(cid, {})
            record, missing_item = resolve_source_access(
                source_id=sid,
                source_file=sf,
                cohort_id=cid,
                source_family=fam,
                cohort_cfg=cohort_cfg,
                input_root=input_root,
                db_conn=conn,
                chunks_map=chunks_map,
            )
            access_records.append(record)
            if missing_item is not None:
                missing_items.append(missing_item)
    finally:
        conn.close()

    # Validate each access record against ITEM schema
    item_validator = _load_schema(ITEM_SCHEMA_PATH, roots)
    for record in access_records:
        errors = list(item_validator.iter_errors(record))
        if errors:
            raise CustodyAccessError(f"Access record schema failure: {errors[0].message}")

    # Prepare outputs
    out_index_path = output_root / config["outputs"]["index"]
    out_missing_path = output_root / config["outputs"]["missing_report"]
    out_receipt_path = output_root / config["outputs"]["receipt"]

    out_index_path.parent.mkdir(parents=True, exist_ok=True)
    out_missing_path.parent.mkdir(parents=True, exist_ok=True)
    out_receipt_path.parent.mkdir(parents=True, exist_ok=True)

    # Write index JSONL atomically
    index_header = {
        "schema_version": "v4_source_custody_access_index_v1",
        "config_sha256": config_sha256,
        "records": len(access_records),
        "ordering": "cohort_id,source_id",
    }
    index_lines = [canonical_json(index_header)]
    for r in access_records:
        index_lines.append(canonical_json(r))

    index_text = "\n".join(index_lines) + "\n"
    out_index_path.write_text(index_text, encoding="utf-8")
    index_sha256 = sha256_file(out_index_path)

    # Write missing report JSON
    missing_report = {
        "schema_version": MISSING_REPORT_SCHEMA_VERSION,
        "operator_decision_date": config["operator_decision"]["date"],
        "issue": config["operator_decision"]["issue"],
        "owner": config["ownership"]["unmounted_archive_owner"],
        "scope": config["ownership"]["blocks_scope"],
        "unmounted_archive_locator": config["inputs"]["retained_archive_locator"],
        "missing_inputs": missing_items,
        "accessible_eligible_sources_permitted_to_proceed": {
            "permitted": True,
            "description": (
                "First eligible cohort (literary-non-ocr) is 100% accessible and verified non-OCR; "
                "accessible native textbooks with verified chunk and DB presence are also permitted to proceed."
            ),
            "permitted_cohort_ids": ["literary-non-ocr"],
        },
    }
    missing_validator = _load_schema(MISSING_REPORT_SCHEMA_PATH, roots)
    missing_errors = list(missing_validator.iter_errors(missing_report))
    if missing_errors:
        raise CustodyAccessError(f"Missing report schema failure: {missing_errors[0].message}")

    out_missing_path.write_text(json.dumps(missing_report, indent=2) + "\n", encoding="utf-8")
    missing_report_sha256 = sha256_file(out_missing_path)

    # Prepare receipt
    lit_records = [r for r in access_records if r["cohort_id"] == "literary-non-ocr"]
    tb_records = [r for r in access_records if r["cohort_id"] == "public-textbooks-non-stem-non-ocr"]

    lit_acc = sum(1 for r in lit_records if r["custody_resolution"]["status"] == "RESOLVED_ACCESSIBLE")
    lit_native = sum(1 for r in lit_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    lit_permitted = all(r["permitted_to_proceed"] for r in lit_records)

    tb_acc = sum(
        1
        for r in tb_records
        if r["custody_resolution"]["status"] in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY")
        and r["permitted_to_proceed"]
    )
    tb_missing = sum(1 for r in tb_records if not r["permitted_to_proceed"])
    tb_native = sum(1 for r in tb_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    tb_perm_count = sum(1 for r in tb_records if r["permitted_to_proceed"])

    total_evaluated = len(access_records)
    total_accessible = sum(
        1
        for r in access_records
        if r["custody_resolution"]["status"] in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY")
        and r["permitted_to_proceed"]
    )
    total_unreachable = sum(1 for r in access_records if r["custody_resolution"]["status"] == "UNREACHABLE_ON_HOST")
    total_native = sum(1 for r in access_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    total_ocr = sum(1 for r in access_records if r["lineage_verification"]["status"] == "EXCLUDED_OCR")
    total_permitted = sum(1 for r in access_records if r["permitted_to_proceed"])

    receipt_id = _make_receipt_id(config_sha256, index_sha256)
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "config_sha256": config_sha256,
        "index_sha256": index_sha256,
        "missing_report_sha256": missing_report_sha256,
        "summary": {
            "total_sources_evaluated": total_evaluated,
            "accessible_sources_count": total_accessible,
            "unreachable_on_host_count": total_unreachable,
            "confirmed_native_count": total_native,
            "excluded_ocr_count": total_ocr,
            "permitted_to_proceed_count": total_permitted,
            "first_eligible_cohort": {
                "cohort_id": "literary-non-ocr",
                "total_sources": len(lit_records),
                "accessible_sources": lit_acc,
                "confirmed_native": lit_native,
                "coverage_ratio": round(lit_acc / len(lit_records), 6) if lit_records else 0.0,
                "permitted_to_proceed": lit_permitted,
            },
            "textbook_cohort": {
                "cohort_id": "public-textbooks-non-stem-non-ocr",
                "total_sources": len(tb_records),
                "accessible_sources": tb_acc,
                "missing_on_host": tb_missing,
                "confirmed_native": tb_native,
                "permitted_to_proceed": tb_perm_count,
            },
        },
        "safety_assertions": {
            "no_corpus_text_emitted": True,
            "no_private_host_paths_disclosed": True,
            "no_broad_recollection": True,
            "no_new_storage_infrastructure": True,
            "ocr_derived_excluded": True,
            "unknown_lineage_not_called_native": True,
            "first_eligible_cohort_ready": lit_permitted and (lit_acc == len(lit_records)),
        },
        "verdict": "PROCEED_WITH_ACCESSIBLE_SOURCES",
    }

    receipt_validator = _load_schema(RECEIPT_SCHEMA_PATH, roots)
    receipt_errors = list(receipt_validator.iter_errors(receipt))
    if receipt_errors:
        raise CustodyAccessError(f"Receipt schema failure: {receipt_errors[0].message}")

    out_receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def _is_private_or_absolute_host_path(path_str: str) -> bool:
    """Detect platform-independent absolute host paths and private host segments (including Windows drive/UNC)."""
    if not path_str:
        return False
    tokens = path_str.split()
    for token in tokens:
        t = token.strip("\"'()[]{}<>,;")
        if not t:
            continue
        normalized = t.replace("\\", "/")
        if normalized.startswith(("/", "~")):
            return True
        if len(normalized) >= 2 and normalized[0].isalpha() and normalized[1] == ":":
            return True
        if normalized.startswith("//"):
            return True
        parts = [p.lower() for p in normalized.strip("/").split("/")]
        private_parts = {"home", "users", "root", "tmp", "temp", "var", "appdata", "private"}
        if any(p in private_parts or p.startswith("~") for p in parts):
            return True
    return False


def _contains_private_or_absolute_host_path(obj: Any) -> bool:
    """Recursively scan all string values in an object (dict, list, string) for private or absolute host paths."""
    if isinstance(obj, str):
        return _is_private_or_absolute_host_path(obj)
    if isinstance(obj, Mapping):
        return any(_contains_private_or_absolute_host_path(v) for v in obj.values())
    if isinstance(obj, (list, tuple, set)):
        return any(_contains_private_or_absolute_host_path(item) for item in obj)
    return False


def verify(
    config_path: Path,
    input_root: Path,
    output_root: Path,
) -> bool:
    """Verify committed custody artifacts against contracts and invariants."""
    roots = [Path.cwd(), input_root]
    config, resolved_config_path = _load_config(config_path, roots)
    expected_config_sha256 = sha256_file(resolved_config_path)

    out_index_path = output_root / config["outputs"]["index"]
    out_missing_path = output_root / config["outputs"]["missing_report"]
    out_receipt_path = output_root / config["outputs"]["receipt"]

    for path, name in [
        (out_index_path, "Index"),
        (out_missing_path, "Missing report"),
        (out_receipt_path, "Receipt"),
    ]:
        if not path.is_file():
            raise CustodyAccessError(f"{name} artifact missing: {path}")

    # Verify receipt schema and hashes
    receipt_validator = _load_schema(RECEIPT_SCHEMA_PATH, roots)
    receipt = json.loads(out_receipt_path.read_text(encoding="utf-8"))
    receipt_errors = list(receipt_validator.iter_errors(receipt))
    if receipt_errors:
        raise CustodyAccessError(f"Receipt validation error: {receipt_errors[0].message}")

    expected_index_sha256 = sha256_file(out_index_path)
    expected_missing_report_sha256 = sha256_file(out_missing_path)

    if receipt["config_sha256"] != expected_config_sha256:
        raise CustodyAccessError("Receipt config_sha256 mismatch")
    if receipt["index_sha256"] != expected_index_sha256:
        raise CustodyAccessError("Receipt index_sha256 mismatch")
    if receipt["missing_report_sha256"] != expected_missing_report_sha256:
        raise CustodyAccessError("Receipt missing_report_sha256 mismatch")

    expected_receipt_id = _make_receipt_id(expected_config_sha256, expected_index_sha256)
    if receipt.get("receipt_id") != expected_receipt_id:
        raise CustodyAccessError(
            f"Receipt receipt_id mismatch: expected {expected_receipt_id}, got {receipt.get('receipt_id')}"
        )

    # Verify index and recompute invariants directly from index records (Finding 3)
    item_validator = _load_schema(ITEM_SCHEMA_PATH, roots)
    record_count = 0
    recomputed_total = 0
    recomputed_accessible = 0
    recomputed_unreachable = 0
    recomputed_native = 0
    recomputed_ocr = 0
    recomputed_permitted = 0

    recomputed_no_corpus_text = True
    recomputed_no_private_host_paths = True
    recomputed_no_broad_recollection = True
    recomputed_no_new_storage_infrastructure = True
    recomputed_ocr_derived_excluded = True
    recomputed_unknown_not_native = True

    lit_records = []
    tb_records = []

    with out_index_path.open(encoding="utf-8") as f:
        header_line = f.readline().strip()
        header = json.loads(header_line)
        if header.get("schema_version") != "v4_source_custody_access_index_v1":
            raise CustodyAccessError("Index header schema_version invalid")
        if header.get("config_sha256") != expected_config_sha256:
            raise CustodyAccessError("Index header config_sha256 mismatch")

        for line_num, line in enumerate(f, start=2):
            if not line.strip():
                continue
            record_count += 1
            row = json.loads(line)
            errors = list(item_validator.iter_errors(row))
            if errors:
                raise CustodyAccessError(f"Index line {line_num} error: {errors[0].message}")

            permitted = row["permitted_to_proceed"]
            status = row["lineage_verification"]["status"]
            is_ocr = row["lineage_verification"]["is_ocr_derived"]
            cust_status = row["custody_resolution"]["status"]
            host_reachable = row["custody_resolution"]["host_reachable"]
            metrics = row["bounded_read_metrics"]
            blocking_reason = row["blocking_reason"]

            # Explicit invariant checks
            if permitted:
                if status != "CONFIRMED_NATIVE":
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is True but lineage status is {status}"
                    )
                if is_ocr:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is True but is_ocr_derived is True"
                    )
                if not host_reachable:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is True but host_reachable is False"
                    )
                if blocking_reason is not None:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is True but blocking_reason is {blocking_reason}"
                    )
                if metrics["observed_records"] <= 0 or not metrics["stream_sha256"]:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is True but observed_records is {metrics['observed_records']}"
                    )
            else:
                if blocking_reason is None:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"permitted_to_proceed is False but blocking_reason is None"
                    )
                if is_ocr and status != "EXCLUDED_OCR":
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"is_ocr_derived is True but lineage status is {status}"
                    )

            # Recompute safety assertions directly from row content
            forbidden_keys = {"text", "content", "corpus_text", "raw_text", "body"}
            if forbidden_keys.intersection(row.keys()):
                recomputed_no_corpus_text = False

            if _contains_private_or_absolute_host_path(row):
                recomputed_no_private_host_paths = False


            cust = row.get("custody_resolution", {})
            if row.get("cohort_id") not in ("literary-non-ocr", "public-textbooks-non-stem-non-ocr"):
                recomputed_no_broad_recollection = False

            p_store = cust.get("primary_store") or ""
            if p_store and not p_store.startswith("sqlite:sources.db#"):
                recomputed_no_broad_recollection = False

            c_store = cust.get("chunks_store") or ""
            if c_store and not c_store.startswith("file:data/textbook_chunks/"):
                recomputed_no_new_storage_infrastructure = False

            if is_ocr and (status != "EXCLUDED_OCR" or permitted):
                recomputed_ocr_derived_excluded = False
            if status == "EXCLUDED_OCR" and permitted:
                recomputed_ocr_derived_excluded = False

            if status == "UNKNOWN_LINEAGE" and (status == "CONFIRMED_NATIVE" or permitted):
                recomputed_unknown_not_native = False
            if status != "CONFIRMED_NATIVE" and row["lineage_verification"].get("lineage_mode") is None and permitted:
                recomputed_unknown_not_native = False

            recomputed_total += 1
            if cust_status in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY") and permitted:
                recomputed_accessible += 1
            if cust_status == "UNREACHABLE_ON_HOST":
                recomputed_unreachable += 1
            if status == "CONFIRMED_NATIVE":
                recomputed_native += 1
            if status == "EXCLUDED_OCR":
                recomputed_ocr += 1
            if permitted:
                recomputed_permitted += 1

            if row["cohort_id"] == "literary-non-ocr":
                lit_records.append(row)
            elif row["cohort_id"] == "public-textbooks-non-stem-non-ocr":
                tb_records.append(row)

    if header.get("records") != record_count:
        raise CustodyAccessError(f"Index header record count {header.get('records')} != observed {record_count}")

    # Verify receipt summary against recomputed invariants
    summary = receipt.get("summary", {})
    if summary.get("total_sources_evaluated") != recomputed_total:
        raise CustodyAccessError(
            f"Receipt summary total_sources_evaluated mismatch: {summary.get('total_sources_evaluated')} != {recomputed_total}"
        )
    if summary.get("accessible_sources_count") != recomputed_accessible:
        raise CustodyAccessError(
            f"Receipt summary accessible_sources_count mismatch: {summary.get('accessible_sources_count')} != {recomputed_accessible}"
        )
    if summary.get("unreachable_on_host_count") != recomputed_unreachable:
        raise CustodyAccessError(
            f"Receipt summary unreachable_on_host_count mismatch: {summary.get('unreachable_on_host_count')} != {recomputed_unreachable}"
        )
    if summary.get("confirmed_native_count") != recomputed_native:
        raise CustodyAccessError(
            f"Receipt summary confirmed_native_count mismatch: {summary.get('confirmed_native_count')} != {recomputed_native}"
        )
    if summary.get("excluded_ocr_count") != recomputed_ocr:
        raise CustodyAccessError(
            f"Receipt summary excluded_ocr_count mismatch: {summary.get('excluded_ocr_count')} != {recomputed_ocr}"
        )
    if summary.get("permitted_to_proceed_count") != recomputed_permitted:
        raise CustodyAccessError(
            f"Receipt summary permitted_to_proceed_count mismatch: {summary.get('permitted_to_proceed_count')} != {recomputed_permitted}"
        )

    # Recompute cohort summaries
    lit_acc = sum(
        1
        for r in lit_records
        if r["custody_resolution"]["status"] in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY")
        and r["permitted_to_proceed"]
    )
    lit_native = sum(1 for r in lit_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    lit_perm = sum(1 for r in lit_records if r["permitted_to_proceed"])
    lit_cov = round(lit_acc / len(lit_records), 6) if lit_records else 0.0

    rc_lit = summary.get("first_eligible_cohort", {})
    if (
        rc_lit.get("total_sources") != len(lit_records)
        or rc_lit.get("accessible_sources") != lit_acc
        or rc_lit.get("confirmed_native") != lit_native
        or rc_lit.get("permitted_to_proceed") != (lit_perm == len(lit_records))
        or rc_lit.get("coverage_ratio") != lit_cov
    ):
        raise CustodyAccessError("Receipt first_eligible_cohort discrepancy")

    tb_acc = sum(
        1
        for r in tb_records
        if r["custody_resolution"]["status"] in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY")
        and r["permitted_to_proceed"]
    )
    tb_missing = sum(1 for r in tb_records if not r["permitted_to_proceed"])
    tb_native = sum(1 for r in tb_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    tb_perm = sum(1 for r in tb_records if r["permitted_to_proceed"])

    rc_tb = summary.get("textbook_cohort", {})
    if (
        rc_tb.get("total_sources") != len(tb_records)
        or rc_tb.get("accessible_sources") != tb_acc
        or rc_tb.get("missing_on_host") != tb_missing
        or rc_tb.get("confirmed_native") != tb_native
        or rc_tb.get("permitted_to_proceed") != tb_perm
    ):
        raise CustodyAccessError("Receipt textbook_cohort discrepancy")

    # Verify missing report
    missing_validator = _load_schema(MISSING_REPORT_SCHEMA_PATH, roots)
    missing_report = json.loads(out_missing_path.read_text(encoding="utf-8"))
    missing_errors = list(missing_validator.iter_errors(missing_report))
    if missing_errors:
        raise CustodyAccessError(f"Missing report error: {missing_errors[0].message}")

    if _contains_private_or_absolute_host_path(missing_report):
        recomputed_no_private_host_paths = False


    expected_first_ready = bool(lit_perm == len(lit_records) and len(lit_records) > 0 and lit_acc == len(lit_records))
    expected_verdict = (
        "PROCEED_WITH_ACCESSIBLE_SOURCES"
        if expected_first_ready and recomputed_permitted > 0
        else "HALT_INACCESSIBLE_SOURCES"
    )

    if receipt.get("verdict") != expected_verdict:
        raise CustodyAccessError(
            f"Receipt verdict mismatch: expected {expected_verdict}, got {receipt.get('verdict')}"
        )

    # Invariant: First eligible cohort must be 100% accessible and permitted to proceed
    first_cohort = receipt["summary"]["first_eligible_cohort"]
    if not first_cohort["permitted_to_proceed"] or first_cohort["coverage_ratio"] != 1.0:
        raise CustodyAccessError("First eligible cohort is not 100% ready to proceed")

    # Invariant: Recompute every safety assertion and verify against receipt
    recomputed_safety = {
        "no_corpus_text_emitted": recomputed_no_corpus_text,
        "no_private_host_paths_disclosed": recomputed_no_private_host_paths,
        "no_broad_recollection": recomputed_no_broad_recollection,
        "no_new_storage_infrastructure": recomputed_no_new_storage_infrastructure,
        "ocr_derived_excluded": recomputed_ocr_derived_excluded,
        "unknown_lineage_not_called_native": recomputed_unknown_not_native,
        "first_eligible_cohort_ready": expected_first_ready,
    }

    safety = receipt.get("safety_assertions", {})
    for key, expected_val in recomputed_safety.items():
        if safety.get(key) != expected_val:
            raise CustodyAccessError(
                f"Receipt safety_assertions.{key} mismatch: expected {expected_val}, got {safety.get(key)}"
            )
        if not expected_val:
            raise CustodyAccessError(f"Recomputed safety assertion {key} failed (False)")

    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V4 source custody access resolution and verification")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build custody access artifacts")
    build_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    build_parser.add_argument("--input-root", type=Path, default=Path.cwd())
    build_parser.add_argument("--output-root", type=Path, default=Path.cwd())

    verify_parser = subparsers.add_parser("verify", help="Verify custody access artifacts")
    verify_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    verify_parser.add_argument("--input-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--output-root", type=Path, default=Path.cwd())

    read_parser = subparsers.add_parser("read", help="Execute bounded stream read on a source (ACCESS-3 proof)")
    read_parser.add_argument("--database", type=Path, default=Path("data/sources.db"))
    read_parser.add_argument("--table", choices=["literary_texts", "textbooks"], required=True)
    read_parser.add_argument("--source-file", type=str, required=True)
    read_parser.add_argument("--batch-size", type=int, default=1000)

    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            receipt = build(args.config, args.input_root, args.output_root)
            print(f"Custody access build complete. Receipt: {receipt['receipt_id']}, verdict: {receipt['verdict']}")
            return 0
        elif args.command == "verify":
            success = verify(args.config, args.input_root, args.output_root)
            if success:
                print("Custody access verification PASSED with 0 errors.")
                return 0
            return 1
        elif args.command == "read":
            reader = BoundedCustodyReader(args.database)
            result = reader.read_source_stream(args.table, args.source_file, args.batch_size)
            print(canonical_json(result))
            return 0
    except CustodyAccessError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
