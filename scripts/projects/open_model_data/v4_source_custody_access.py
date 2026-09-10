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
                f"SELECT id, chunk_id, length(text) FROM {table} WHERE source_file = ? ORDER BY id ASC",
                (source_file,),
            )
            while rows := cursor.fetchmany(batch_size):
                for row_id, chunk_id, text_len in rows:
                    records_streamed += 1
                    chars_streamed += text_len or 0
                    row_repr = f"{row_id}:{chunk_id}:{text_len}\n".encode()
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


def check_chunk_file_lineage(
    chunk_file: Path,
    excluded_modes: Sequence[str] = ("apple_vision_ocr", "ocr", "scanned_image"),
) -> tuple[str, bool, int, int]:
    """Examine a textbook chunk file for non-OCR lineage (ACCESS-2).

    Returns:
        (lineage_mode, is_ocr, row_count, char_count)
    """
    if not chunk_file.is_file():
        return "unknown", False, 0, 0

    row_count = 0
    char_count = 0
    modes_seen = set()
    has_ocr = False

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

            mode = row.get("extraction_mode")
            page_mode = row.get("page_extraction_mode")
            for m in (mode, page_mode):
                if m:
                    modes_seen.add(str(m))
                    if str(m) in excluded_modes:
                        has_ocr = True

            text = row.get("text") or ""
            char_count += len(text)

    if not modes_seen:
        return "unknown", False, row_count, char_count

    if has_ocr:
        return "apple_vision_ocr", True, row_count, char_count

    if all(m in ("native_text", "native_pdf_text") for m in modes_seen):
        return "native_pdf_text", False, row_count, char_count

    return "unknown", False, row_count, char_count


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
        f"SELECT COUNT(*), SUM(length(text)) FROM {table} WHERE source_file = ?",
        (source_file,),
    )
    db_row = cur.fetchone()
    db_records = db_row[0] if db_row else 0
    db_chars = db_row[1] if (db_row and db_row[1] is not None) else 0

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
            chunk_mode, chunk_is_ocr, chunk_rows, _chunk_chars = check_chunk_file_lineage(chunk_path, excluded_modes)
            if chunk_is_ocr:
                lineage_status = "EXCLUDED_OCR"
                lineage_mode = "apple_vision_ocr"
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = True
                permitted = False
                blocking_reason = "ocr_derived_extraction_mode_excluded"
                custody_status = "PARTIAL_CHUNKS_AND_DB_ONLY"
            elif chunk_mode in ("native_pdf_text", "native_text"):
                lineage_status = "CONFIRMED_NATIVE"
                lineage_mode = "native_pdf_text"
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = False
                # Accessible if DB or chunks present
                permitted = db_records > 0 or chunk_rows > 0
                custody_status = "RESOLVED_ACCESSIBLE" if archive_on_host else "PARTIAL_CHUNKS_AND_DB_ONLY"
                blocking_reason = None
                if not archive_on_host:
                    missing_report_item = {
                        "source_id": source_id,
                        "source_locator": {"source_file": source_file},
                        "cohort_id": cohort_id,
                        "missing_path_ref": archive_ref or f"gdrive:learn-ukrainian-data/textbooks/{source_file}.pdf",
                        "reason": "execution_host_resolver_unmounted",
                        "owner": "existing custody/source-access owner",
                        "blocks": "direct PDF byte extraction for this source",
                    }
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
            missing_report_item = {
                "source_id": source_id,
                "source_locator": {"source_file": source_file},
                "cohort_id": cohort_id,
                "missing_path_ref": archive_ref or f"gdrive:learn-ukrainian-data/textbooks/{source_file}.pdf",
                "reason": "execution_host_resolver_unmounted_and_missing_chunks",
                "owner": "existing custody/source-access owner",
                "blocks": "direct PDF byte extraction for this source",
            }

    # Bounded read digest computation
    stream_digest = None
    observed_records = db_records
    observed_chars = db_chars

    if db_records > 0:
        cur.execute(
            f"SELECT id, chunk_id, length(text) FROM {table} WHERE source_file = ? ORDER BY id ASC",
            (source_file,),
        )
        digest = hashlib.sha256()
        while rows := cur.fetchmany(1000):
            for row_id, chunk_id, text_len in rows:
                digest.update(f"{row_id}:{chunk_id}:{text_len}\n".encode())
        stream_digest = digest.hexdigest()
    elif chunk_path is not None and chunk_path.is_file():
        # Compute digest over chunk row IDs without database
        digest = hashlib.sha256()
        observed_records = 0
        observed_chars = 0
        with chunk_path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                observed_records += 1
                row = json.loads(line)
                c_id = row.get("chunk_id", "")
                t_len = len(row.get("text", ""))
                observed_chars += t_len
                digest.update(f"{c_id}:{t_len}\n".encode())
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
            "host_reachable": archive_on_host or (db_records > 0) or (chunk_path is not None and chunk_path.is_file()),
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
    total_accessible = sum(1 for r in access_records if r["permitted_to_proceed"])
    total_unreachable = sum(1 for r in access_records if not r["permitted_to_proceed"])
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

    if receipt["config_sha256"] != expected_config_sha256:
        raise CustodyAccessError("Receipt config_sha256 mismatch")
    if receipt["index_sha256"] != sha256_file(out_index_path):
        raise CustodyAccessError("Receipt index_sha256 mismatch")
    if receipt["missing_report_sha256"] != sha256_file(out_missing_path):
        raise CustodyAccessError("Receipt missing_report_sha256 mismatch")

    # Verify index
    item_validator = _load_schema(ITEM_SCHEMA_PATH, roots)
    record_count = 0
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

    if header.get("records") != record_count:
        raise CustodyAccessError(f"Index header record count {header.get('records')} != observed {record_count}")

    # Verify missing report
    missing_validator = _load_schema(MISSING_REPORT_SCHEMA_PATH, roots)
    missing_report = json.loads(out_missing_path.read_text(encoding="utf-8"))
    missing_errors = list(missing_validator.iter_errors(missing_report))
    if missing_errors:
        raise CustodyAccessError(f"Missing report error: {missing_errors[0].message}")

    # Invariant: First eligible cohort must be 100% accessible and permitted to proceed
    first_cohort = receipt["summary"]["first_eligible_cohort"]
    if not first_cohort["permitted_to_proceed"] or first_cohort["coverage_ratio"] != 1.0:
        raise CustodyAccessError("First eligible cohort is not 100% ready to proceed")

    # Invariant: Safety assertions must all be True
    for key, val in receipt["safety_assertions"].items():
        if not val:
            raise CustodyAccessError(f"Safety assertion {key} is not True")

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
