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
import os
import sqlite3
import sys
import time
from collections.abc import Container, Mapping, Sequence
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

NATIVE_LINEAGE_MODES = frozenset(
    {
        "native_digital_source",
        "native_pdf_text",
        "native_text",
        "mixed_native",
    }
)
OCR_LINEAGE_MODES = frozenset(
    {
        "apple_vision_ocr",
        "ocr",
        "scanned_image",
    }
)

FAMILY_APPROVED_TABLES: dict[str, str] = {
    "literary": "literary_texts",
    "public_textbooks": "textbooks",
}
ALLOWED_DATABASE_TABLES: frozenset[str] = frozenset(FAMILY_APPROVED_TABLES.values())

PROGRESSION_DESCRIPTION = (
    "First eligible cohort (literary-non-ocr) is 100% accessible and verified non-OCR; "
    "accessible native textbooks with verified chunk and DB presence are also permitted to proceed."
)
PROGRESSION_DESCRIPTION_HALTED = (
    "First eligible cohort is not 100% accessible and verified non-OCR; progression halted."
)


def derive_progression_decision(first_eligible_ready: bool) -> dict[str, Any]:
    """Derive deterministic progression decision block for missing report (ACCESS-4)."""
    if first_eligible_ready:
        return {
            "permitted": True,
            "description": PROGRESSION_DESCRIPTION,
            "permitted_cohort_ids": ["literary-non-ocr"],
        }
    return {
        "permitted": False,
        "description": PROGRESSION_DESCRIPTION_HALTED,
        "permitted_cohort_ids": [],
    }


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


def _make_receipt_id(config_hash: str, index_hash: str, missing_report_hash: str) -> str:
    seed = f"{config_hash}:{index_hash}:{missing_report_hash}".encode()
    return f"receipt.custody.{hashlib.sha256(seed).hexdigest()[:24]}"


PRIMARY_REPO_ROOT_ENV = "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"


def _primary_repo_root() -> Path | None:
    """Resolve an extra search root from env or cwd-relative git discovery.

    Fail closed: no baked host checkout path. An unset env plus failed
    cwd-relative discovery returns None so callers do not invent a location.
    """
    raw = os.environ.get(PRIMARY_REPO_ROOT_ENV, "").strip()
    if raw:
        candidate = Path(raw)
        resolved = candidate.resolve() if candidate.is_absolute() else (Path.cwd() / candidate).resolve()
        if not resolved.is_dir():
            raise CustodyAccessError(f"{PRIMARY_REPO_ROOT_ENV} is set but is not an existing directory")
        return resolved
    try:
        cur = Path.cwd().resolve()
        for parent in [cur, *list(cur.parents)]:
            git_file = parent / ".git"
            if git_file.is_file():
                content = git_file.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    raw_gitdir = content.split(":", 1)[1].strip()
                    git_dir = Path(raw_gitdir)
                    if not git_dir.is_absolute():
                        git_dir = (parent / git_dir).resolve()
                    common_git = git_dir.parents[1]
                    primary = common_git.parent
                    if primary.is_dir():
                        return primary
            elif git_file.is_dir():
                return parent
    except Exception:
        pass
    return None


def _get_search_roots(input_root: Path) -> list[Path]:
    """Ordered search roots for local custody inputs."""
    norm_in = input_root.resolve()
    roots = [norm_in, Path.cwd()]
    primary = _primary_repo_root()
    if primary is not None and primary not in roots:
        roots.append(primary)
    return roots


def _resolve_archive_mount(archive_locator: str, roots: Sequence[Path]) -> Path | None:
    """Resolve a logical archive locator (e.g. gdrive:learn-ukrainian-data/textbooks) to a local mount directory."""
    if not archive_locator:
        return None
    for r in roots:
        candidates: list[Path] = []
        if archive_locator.startswith("gdrive:learn-ukrainian-data/"):
            rel = archive_locator.removeprefix("gdrive:learn-ukrainian-data/")
            candidates.extend([r / "data" / rel, r / rel])
        elif archive_locator.startswith("gdrive:"):
            rel = archive_locator.removeprefix("gdrive:")
            candidates.extend([r / "data" / rel, r / rel])
        elif archive_locator.startswith("data/"):
            candidates.append(r / archive_locator)
        elif Path(archive_locator).is_absolute():
            candidates.append(Path(archive_locator))
        else:
            candidates.extend([r / archive_locator, r / "data" / archive_locator])

        for c in candidates:
            if c.is_dir():
                return c
    return None


def _build_archive_cache_map(
    archive_locator: str,
    lineage_rule: str,
    roots: Sequence[Path],
) -> dict[str, Path]:
    """Pre-index all files in the mounted archive directory (including grade-* subdirectories)."""
    mount_dir = _resolve_archive_mount(archive_locator, roots)
    if mount_dir is None or not mount_dir.is_dir():
        return {}
    suffix = ".jsonl" if lineage_rule == "native_digital_source" else ".pdf"
    archive_map: dict[str, Path] = {}
    for p in mount_dir.glob(f"*{suffix}"):
        if p.is_file():
            archive_map[p.stem] = p
    for p in mount_dir.glob(f"grade-*/*{suffix}"):
        if p.is_file():
            archive_map[p.stem] = p
    for p in mount_dir.glob(f"*/*{suffix}"):
        if p.is_file() and p.stem not in archive_map:
            archive_map[p.stem] = p
    return archive_map


def _check_archive_on_host(
    archive_locator: str,
    source_file: str,
    lineage_rule: str,
    roots: Sequence[Path],
    cached_map: Mapping[str, Path] | None = None,
) -> bool:
    """Grade-aware check for an archive source file on host storage."""
    if cached_map is not None:
        return source_file in cached_map
    mount_dir = _resolve_archive_mount(archive_locator, roots)
    if mount_dir is None or not mount_dir.is_dir():
        return False
    suffix = ".jsonl" if lineage_rule == "native_digital_source" else ".pdf"
    if (mount_dir / f"{source_file}{suffix}").is_file():
        return True
    for grade_dir in mount_dir.glob("grade-*"):
        if grade_dir.is_dir() and (grade_dir / f"{source_file}{suffix}").is_file():
            return True
    for sub in mount_dir.iterdir():
        if sub.is_dir() and not sub.name.startswith(".") and (sub / f"{source_file}{suffix}").is_file():
            return True
    return False


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


def validate_and_resolve_paths(
    config: Mapping[str, Any],
    input_root: Path,
    output_root: Path,
    config_path: Path | None = None,
) -> tuple[dict[str, Path], dict[str, Path]]:
    """Validate output containment, distinctness, and input/output disjointness (ACCESS-1, ACCESS-4)."""
    in_root = input_root.resolve()
    out_root = output_root.resolve()
    roots = _get_search_roots(in_root)

    resolved_inputs: dict[str, Path] = {}
    cp = Path(config_path) if config_path is not None else DEFAULT_CONFIG
    resolved_inputs["config"] = _resolve_file(cp, roots).resolve()

    for s_name, s_path in (
        ("config_schema", CONFIG_SCHEMA_PATH),
        ("item_schema", ITEM_SCHEMA_PATH),
        ("missing_report_schema", MISSING_REPORT_SCHEMA_PATH),
        ("receipt_schema", RECEIPT_SCHEMA_PATH),
    ):
        resolved_inputs[s_name] = _resolve_file(s_path, roots).resolve()

    inputs_cfg = config.get("inputs", {})
    for k in ("provenance_index", "provenance_receipt", "database", "textbook_chunks_dir"):
        if k in inputs_cfg:
            raw_p = Path(inputs_cfg[k])
            p = _resolve_file(raw_p, roots).resolve()
            resolved_inputs[k] = p

    outputs_cfg = config.get("outputs", {})
    resolved_outputs: dict[str, Path] = {}
    seen_output_paths: dict[Path, str] = {}

    for k in ("index", "missing_report", "receipt"):
        if k not in outputs_cfg:
            raise CustodyAccessError(f"Missing required output key in config: '{k}'")
        raw_p = Path(outputs_cfg[k])
        p = raw_p.resolve() if raw_p.is_absolute() else (out_root / raw_p).resolve()

        if not p.is_relative_to(out_root):
            raise CustodyAccessError(f"Output path for '{k}' ({p}) escapes output_root ({out_root})")

        if p in seen_output_paths:
            prev_k = seen_output_paths[p]
            raise CustodyAccessError(f"Output path collision between '{prev_k}' and '{k}': both resolve to {p}")
        seen_output_paths[p] = k
        resolved_outputs[k] = p

    for out_k, out_p in resolved_outputs.items():
        for in_k, in_p in resolved_inputs.items():
            if out_p == in_p:
                raise CustodyAccessError(f"Output '{out_k}' ({out_p}) aliases input '{in_k}' ({in_p})")
            if (in_k == "textbook_chunks_dir" or in_p.is_dir()) and out_p.is_relative_to(in_p):
                raise CustodyAccessError(
                    f"Output '{out_k}' ({out_p}) is located inside input directory '{in_k}' ({in_p})"
                )

    return resolved_inputs, resolved_outputs


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
        if batch_size <= 0:
            raise CustodyAccessError(f"batch_size must be strictly positive (> 0), got {batch_size}")
        if table not in ALLOWED_DATABASE_TABLES:
            raise CustodyAccessError(
                f"Table '{table}' is not an approved custody database table (expected one of {sorted(ALLOWED_DATABASE_TABLES)})"
            )
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
                f'SELECT id, chunk_id, text FROM "{table}" WHERE source_file = ? ORDER BY id ASC',
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


def _precompute_table_source_metrics(
    conn: sqlite3.Connection,
    table: str,
    selected_source_files: Container[str] | set[str] | None = None,
) -> tuple[dict[str, tuple[int, int, str]], dict[str, tuple[int, str]]]:
    """Compute bounded read metrics and chunk lineage digests for selected source files in a table in a single pass.

    Returns:
        stream_metrics: source_file -> (observed_records, observed_characters, stream_sha256)
        chunk_metrics: source_file -> (record_count, chunk_digest)
    """
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cur.fetchone():
        return {}, {}

    if selected_source_files is not None and not selected_source_files:
        return {}, {}

    stream_metrics: dict[str, tuple[int, int, str]] = {}
    chunk_metrics: dict[str, tuple[int, str]] = {}

    selected_set = set(selected_source_files) if selected_source_files is not None else None
    sorted_sfs = sorted(selected_set) if selected_set is not None else None

    # Chunk into parameter batches of up to 500 files to avoid SQLite parameter limits
    sf_batches = [sorted_sfs[i : i + 500] for i in range(0, len(sorted_sfs), 500)] if sorted_sfs is not None else [None]

    for sf_batch in sf_batches:
        if sf_batch is not None:
            placeholders = ",".join("?" for _ in sf_batch)
            sql = f'SELECT source_file, id, chunk_id, text FROM "{table}" WHERE source_file IN ({placeholders}) ORDER BY source_file, id ASC'
            cur.execute(sql, sf_batch)
        else:
            cur.execute(f'SELECT source_file, id, chunk_id, text FROM "{table}" ORDER BY source_file, id ASC')

        curr_sf: str | None = None
        rec_cnt = 0
        char_cnt = 0
        stream_digest = hashlib.sha256()
        chunk_digest = hashlib.sha256()

        while batch := cur.fetchmany(5000):
            for sf, r_id, r_chunk_id, r_text in batch:
                if selected_set is not None and sf not in selected_set:
                    continue
                if sf != curr_sf:
                    if curr_sf is not None and rec_cnt > 0:
                        stream_metrics[curr_sf] = (rec_cnt, char_cnt, stream_digest.hexdigest())
                        chunk_metrics[curr_sf] = (rec_cnt, chunk_digest.hexdigest())
                    curr_sf = sf
                    rec_cnt = 0
                    char_cnt = 0
                    stream_digest = hashlib.sha256()
                    chunk_digest = hashlib.sha256()
                rec_cnt += 1
                t_str = r_text or ""
                t_len = len(t_str)
                char_cnt += t_len
                t_hash = hashlib.sha256(t_str.encode("utf-8")).hexdigest()
                stream_digest.update(f"{r_id}:{r_chunk_id}:{t_len}:{t_hash}\n".encode())
                chunk_digest.update(f"{r_chunk_id}:{t_len}:{t_hash}\n".encode())

        if curr_sf is not None and rec_cnt > 0:
            stream_metrics[curr_sf] = (rec_cnt, char_cnt, stream_digest.hexdigest())
            chunk_metrics[curr_sf] = (rec_cnt, chunk_digest.hexdigest())

    return stream_metrics, chunk_metrics


def check_chunk_file_lineage(
    chunk_file: Path,
    excluded_modes: Sequence[str] = ("apple_vision_ocr", "ocr", "scanned_image"),
) -> tuple[str, bool, int, int, str | None]:
    """Examine a textbook chunk file for non-OCR lineage (ACCESS-2).

    Validates every single row:
    - Absent/unlabelled extraction modes fail closed as unknown lineage.
    - Excluded modes (e.g. apple_vision_ocr) flag the file as OCR-derived.
    - Unknown/non-native modes fail closed as unknown lineage.

    Returns:
        (lineage_mode, is_ocr, row_count, char_count, content_sha256)
    """
    for m in excluded_modes:
        if m not in OCR_LINEAGE_MODES:
            raise CustodyAccessError(
                f"check_chunk_file_lineage: excluded_modes contains unsupported or non-OCR mode '{m}' "
                f"(expected subset of {sorted(OCR_LINEAGE_MODES)})"
            )

    if not chunk_file.is_file():
        return "unknown", False, 0, 0, None

    effective_ocr_modes = set(OCR_LINEAGE_MODES).union(excluded_modes)

    row_count = 0
    char_count = 0
    chunk_digest = hashlib.sha256()
    has_ocr = False
    detected_ocr_mode: str | None = None
    has_unknown = False
    seen_native_modes: set[str] = set()

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
            t_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunk_digest.update(f"{c_id}:{len(text)}:{t_hash}\n".encode())
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
                    if m in effective_ocr_modes:
                        has_ocr = True
                        if detected_ocr_mode is None:
                            detected_ocr_mode = m
                    elif m in ("native_text", "native_pdf_text"):
                        seen_native_modes.add(m)
                    else:
                        has_unknown = True

    if row_count == 0:
        return "unknown", False, 0, 0, None

    content_sha256 = chunk_digest.hexdigest()

    if has_ocr:
        return detected_ocr_mode or "apple_vision_ocr", True, row_count, char_count, content_sha256

    if has_unknown:
        return "unknown", False, row_count, char_count, content_sha256

    if len(seen_native_modes) > 1:
        observed_mode = "mixed_native"
    elif "native_text" in seen_native_modes:
        observed_mode = "native_text"
    else:
        observed_mode = "native_pdf_text"

    return observed_mode, False, row_count, char_count, content_sha256


def validate_cohort_spec(cohort_cfg: Mapping[str, Any]) -> None:
    """Validate that cohort configuration declares compatible resolver_kind, lineage_rule, and approved store."""
    cohort_id = cohort_cfg.get("cohort_id", "<unknown>")
    family = cohort_cfg.get("source_family")
    resolver_kind = cohort_cfg.get("resolver_kind")
    lineage_rule = cohort_cfg.get("lineage_rule")
    primary_store = cohort_cfg.get("primary_store")

    if family not in FAMILY_APPROVED_TABLES:
        raise CustodyAccessError(f"Cohort '{cohort_id}' has unsupported source_family '{family}'")
    approved_table = FAMILY_APPROVED_TABLES[family]

    if primary_store is not None:
        expected_store = f"sqlite:sources.db#{approved_table}"
        if primary_store != expected_store:
            raise CustodyAccessError(
                f"Cohort '{cohort_id}' primary_store '{primary_store}' does not match approved store '{expected_store}'"
            )

    if family == "literary":
        if resolver_kind != "sqlite_database":
            raise CustodyAccessError(
                f"Cohort '{cohort_id}' (family 'literary') requires resolver_kind 'sqlite_database', got '{resolver_kind}'"
            )
        if lineage_rule != "native_digital_source":
            raise CustodyAccessError(
                f"Cohort '{cohort_id}' (family 'literary') requires lineage_rule 'native_digital_source', got '{lineage_rule}'"
            )
    elif family == "public_textbooks":
        if resolver_kind != "hybrid_sqlite_chunks_archive":
            raise CustodyAccessError(
                f"Cohort '{cohort_id}' (family 'public_textbooks') requires resolver_kind 'hybrid_sqlite_chunks_archive', got '{resolver_kind}'"
            )
        if lineage_rule != "native_pdf_text":
            raise CustodyAccessError(
                f"Cohort '{cohort_id}' (family 'public_textbooks') requires lineage_rule 'native_pdf_text', got '{lineage_rule}'"
            )

    excluded_modes = cohort_cfg.get("excluded_modes")
    if excluded_modes is not None:
        if not isinstance(excluded_modes, (list, tuple)):
            raise CustodyAccessError(f"Cohort '{cohort_id}' excluded_modes must be a list, got {type(excluded_modes)}")
        for mode in excluded_modes:
            if mode not in OCR_LINEAGE_MODES:
                raise CustodyAccessError(
                    f"Cohort '{cohort_id}' excluded_modes contains unsupported or non-OCR mode '{mode}' "
                    f"(expected subset of {sorted(OCR_LINEAGE_MODES)})"
                )


def derive_missing_report_item(
    row: Mapping[str, Any],
    config: Mapping[str, Any],
    effective_custody_status: str | None = None,
) -> dict[str, Any] | None:
    """Derive expected missing report item from an access record and custody config (ACCESS-4)."""
    cid = row.get("cohort_id", "")
    cust = row.get("custody_resolution", {})
    status = effective_custody_status if effective_custody_status is not None else cust.get("status")
    permitted = row.get("permitted_to_proceed", False)
    owner = config.get("ownership", {}).get("unmounted_archive_owner", "existing custody/source-access owner")
    source_locator = row.get("source_locator", {})
    sfile = source_locator.get("source_file", "")
    source_id = row.get("source_id", "")

    if cid == "public-textbooks-non-stem-non-ocr":
        if status != "RESOLVED_ACCESSIBLE":
            reason = (
                row.get("blocking_reason") or "not_permitted_to_proceed"
                if not permitted
                else "execution_host_resolver_unmounted"
            )
            return {
                "source_id": source_id,
                "source_locator": {"source_file": sfile},
                "cohort_id": cid,
                "missing_path_ref": cust.get("archive_store") or f"gdrive:learn-ukrainian-data/textbooks/{sfile}.pdf",
                "reason": reason,
                "owner": owner,
                "blocks": "direct PDF byte extraction for this source",
            }
        return None
    else:
        if not permitted:
            p_store = cust.get("primary_store", "")
            return {
                "source_id": source_id,
                "source_locator": {"source_file": sfile},
                "cohort_id": cid,
                "missing_path_ref": cust.get("archive_store") or f"{p_store}#{sfile}",
                "reason": row.get("blocking_reason") or "not_permitted_to_proceed",
                "owner": owner,
                "blocks": "source records missing from database",
            }
    return None


def resolve_source_access(
    source_id: str,
    source_file: str,
    cohort_id: str,
    source_family: str,
    cohort_cfg: dict[str, Any],
    input_root: Path,
    db_conn: sqlite3.Connection,
    chunks_map: Mapping[str, Path],
    unmounted_archive_owner: str = "existing custody/source-access owner",
    archive_cache_map: Mapping[str, Path] | None = None,
    precomputed_stream_metrics: Mapping[str, tuple[int, int, str]] | None = None,
    precomputed_chunk_metrics: Mapping[str, tuple[int, str]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Resolve custody arrangement and verify lineage for one source (ACCESS-1, ACCESS-2, ACCESS-4)."""
    if not cohort_cfg or cohort_cfg.get("cohort_id") != cohort_id:
        raise CustodyAccessError(f"Source {source_id} requires an exact configured cohort entry for '{cohort_id}'")
    if cohort_cfg.get("source_family") != source_family:
        raise CustodyAccessError(
            f"Source {source_id} ({cohort_id}) source_family '{source_family}' "
            f"does not match configured cohort source_family '{cohort_cfg.get('source_family')}'"
        )
    validate_cohort_spec(cohort_cfg)

    lineage_rule = cohort_cfg["lineage_rule"]
    if source_family not in FAMILY_APPROVED_TABLES:
        raise CustodyAccessError(f"Source {source_id} has unsupported source_family '{source_family}'")
    table = FAMILY_APPROVED_TABLES[source_family]
    expected_primary_store = f"sqlite:sources.db#{table}"
    primary_store = cohort_cfg.get("primary_store") or expected_primary_store
    if primary_store != expected_primary_store:
        raise CustodyAccessError(
            f"Cohort '{cohort_id}' primary_store '{primary_store}' does not match approved store '{expected_primary_store}'"
        )
    access_id = _make_access_id(source_id, cohort_id)

    cur = db_conn.cursor()
    if precomputed_stream_metrics is not None:
        stream_tuple = precomputed_stream_metrics.get(source_file)
        db_records = stream_tuple[0] if stream_tuple is not None else 0
    else:
        cur.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE source_file = ?',
            (source_file,),
        )
        db_row = cur.fetchone()
        db_records = db_row[0] if db_row else 0

    norm_input_root = input_root.resolve()
    roots = _get_search_roots(norm_input_root)
    chunk_path = chunks_map.get(source_file)
    chunk_ref = None
    if chunk_path is not None:
        for r in roots:
            try:
                rel = chunk_path.resolve().relative_to(r.resolve())
                chunk_ref = f"file:{rel}"
                break
            except ValueError:
                continue
        if chunk_ref is None:
            chunk_ref = f"file:{chunk_path.name}"

    archive_locator = cohort_cfg.get("archive_locator", "")
    if lineage_rule == "native_digital_source":
        archive_ref = f"{archive_locator}/{source_file}.jsonl" if archive_locator else None
    else:
        archive_ref = f"{archive_locator}/{source_file}.pdf" if archive_locator else None

    # Check host archive accessibility (grade-aware, logical-mount-aware)
    archive_on_host = _check_archive_on_host(
        archive_locator=archive_locator,
        source_file=source_file,
        lineage_rule=lineage_rule,
        roots=roots,
        cached_map=archive_cache_map,
    )

    # Lineage verification driven by cohort's configured lineage_rule
    if lineage_rule == "native_digital_source":
        # Literary corpus is established native digital text from human-authored archives
        lineage_status = "CONFIRMED_NATIVE"
        lineage_mode = "native_digital_source"
        evidence_ref = primary_store
        is_ocr = False
        permitted = db_records > 0
        custody_status = "RESOLVED_ACCESSIBLE" if db_records > 0 else "UNREACHABLE_ON_HOST"
        blocking_reason = None if permitted else "source_records_not_found_in_database"
    else:
        # Public textbooks cohort with hybrid resolver (native_pdf_text)
        excluded_modes = cohort_cfg.get("excluded_modes", ["apple_vision_ocr", "ocr", "scanned_image"])

        if chunk_path is not None and chunk_path.is_file():
            chunk_mode, chunk_is_ocr, _chunk_rows, _chunk_chars, chunk_digest = check_chunk_file_lineage(
                chunk_path, excluded_modes
            )
            chunk_custody_status = "RESOLVED_ACCESSIBLE" if archive_on_host else "PARTIAL_CHUNKS_AND_DB_ONLY"
            if chunk_is_ocr:
                lineage_status = "EXCLUDED_OCR"
                lineage_mode = chunk_mode
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = True
                permitted = False
                blocking_reason = "ocr_derived_extraction_mode_excluded"
                custody_status = chunk_custody_status
            elif chunk_mode in ("native_pdf_text", "native_text", "mixed_native"):
                # Bind accessed database content to the verified chunk file lineage (ACCESS-2)
                if precomputed_chunk_metrics is not None:
                    chunk_tuple = precomputed_chunk_metrics.get(source_file)
                    db_records_count, db_stream_hash = chunk_tuple if chunk_tuple is not None else (0, None)
                else:
                    cur.execute(
                        f'SELECT chunk_id, text FROM "{table}" WHERE source_file = ? ORDER BY id ASC',
                        (source_file,),
                    )
                    db_digest = hashlib.sha256()
                    db_records_count = 0
                    while batch := cur.fetchmany(1000):
                        for r_chunk_id, r_text in batch:
                            db_records_count += 1
                            t = r_text or ""
                            t_hash = hashlib.sha256(t.encode("utf-8")).hexdigest()
                            db_digest.update(f"{r_chunk_id}:{len(t)}:{t_hash}\n".encode())
                    db_stream_hash = db_digest.hexdigest() if db_records_count > 0 else None

                if db_records_count == 0:
                    lineage_status = "UNKNOWN_LINEAGE"
                    lineage_mode = "unknown"
                    evidence_ref = f"{chunk_ref}#missing_db"
                    is_ocr = False
                    permitted = False
                    blocking_reason = "source_records_not_found_in_database"
                    custody_status = chunk_custody_status
                elif db_records_count != _chunk_rows or db_stream_hash != chunk_digest:
                    # Database content does not match verified chunk lineage
                    lineage_status = "UNKNOWN_LINEAGE"
                    lineage_mode = "unknown"
                    evidence_ref = f"{chunk_ref}#discrepancy"
                    is_ocr = False
                    permitted = False
                    blocking_reason = "database_content_does_not_match_lineage_chunk_evidence"
                    custody_status = chunk_custody_status
                else:
                    lineage_status = "CONFIRMED_NATIVE"
                    lineage_mode = chunk_mode
                    evidence_ref = f"{chunk_ref}#extraction_mode"
                    is_ocr = False
                    permitted = True
                    custody_status = chunk_custody_status
                    blocking_reason = None
            else:
                lineage_status = "UNKNOWN_LINEAGE"
                lineage_mode = "unknown"
                evidence_ref = f"{chunk_ref}#extraction_mode"
                is_ocr = False
                permitted = False
                blocking_reason = "unknown_extraction_lineage_not_silently_called_native"
                custody_status = chunk_custody_status
        else:
            # No chunk file found on host
            lineage_status = "UNKNOWN_LINEAGE"
            lineage_mode = "unknown"
            evidence_ref = "none"
            is_ocr = False
            permitted = False
            custody_status = "RESOLVED_ACCESSIBLE" if archive_on_host else "UNREACHABLE_ON_HOST"
            blocking_reason = (
                "missing_chunk_file_and_unmounted_archive" if not archive_on_host else "missing_chunk_file"
            )

    # Bounded read digest computation (content-sensitive text hashing)
    stream_digest = None
    observed_records = 0
    observed_chars = 0

    if permitted and db_records > 0:
        if precomputed_stream_metrics is not None:
            stream_tuple = precomputed_stream_metrics.get(source_file)
            if stream_tuple is not None:
                observed_records, observed_chars, stream_digest = stream_tuple
        else:
            cur.execute(
                f'SELECT id, chunk_id, text FROM "{table}" WHERE source_file = ? ORDER BY id ASC',
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

    missing_report_item = derive_missing_report_item(
        record,
        {"ownership": {"unmounted_archive_owner": unmounted_archive_owner}},
    )
    return record, missing_report_item


def build(
    config_path: Path,
    input_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Execute custody resolution and lineage audit (ACCESS-1..4)."""
    norm_input_root = input_root.resolve()
    norm_output_root = output_root.resolve()
    roots = _get_search_roots(norm_input_root)
    config, resolved_config_path = _load_config(config_path, roots)
    config_sha256 = sha256_file(resolved_config_path)

    resolved_inputs, resolved_outputs = validate_and_resolve_paths(
        config, norm_input_root, norm_output_root, config_path=resolved_config_path
    )

    # Resolve input paths
    prov_index_path = resolved_inputs["provenance_index"]
    db_path = resolved_inputs["database"]
    chunks_dir = resolved_inputs.get("textbook_chunks_dir", Path())

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

    # Pre-build archive cache maps for cohorts (Finding 2)
    for c in config["cohorts"]:
        validate_cohort_spec(c)
    cohorts_by_id = {c["cohort_id"]: c for c in config["cohorts"]}
    archive_maps_by_cohort: dict[str, dict[str, Path]] = {}
    for cid, c_cfg in cohorts_by_id.items():
        archive_maps_by_cohort[cid] = _build_archive_cache_map(
            c_cfg.get("archive_locator", ""),
            c_cfg.get("lineage_rule", ""),
            roots,
        )

    # Connect to database read-only
    db_uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    access_records = []
    missing_items = []

    try:
        # Precompute table stream and chunk metrics for approved tables (ACCESS-1, ACCESS-2, ACCESS-3)
        table_stream_metrics: dict[str, dict[str, tuple[int, int, str]]] = {}
        table_chunk_metrics: dict[str, dict[str, tuple[int, str]]] = {}
        for tbl in set(FAMILY_APPROVED_TABLES.values()):
            selected_sfs = {sf for sf, _cid, fam in unique_sources.values() if FAMILY_APPROVED_TABLES.get(fam) == tbl}
            s_m, c_m = _precompute_table_source_metrics(conn, tbl, selected_source_files=selected_sfs)
            table_stream_metrics[tbl] = s_m
            table_chunk_metrics[tbl] = c_m

        # Sort sources deterministically by cohort_id, then source_id
        sorted_sids = sorted(unique_sources.keys(), key=lambda s: (unique_sources[s][1], s))
        for sid in sorted_sids:
            sf, cid, fam = unique_sources[sid]
            if cid not in cohorts_by_id:
                raise CustodyAccessError(f"Provenance source {sid} references unconfigured cohort_id '{cid}'")
            cohort_cfg = cohorts_by_id[cid]
            if cohort_cfg.get("source_family") != fam:
                raise CustodyAccessError(
                    f"Provenance source {sid} ({cid}) source_family '{fam}' "
                    f"does not match configured cohort source_family '{cohort_cfg.get('source_family')}'"
                )
            tbl = FAMILY_APPROVED_TABLES[fam]
            record, missing_item = resolve_source_access(
                source_id=sid,
                source_file=sf,
                cohort_id=cid,
                source_family=fam,
                cohort_cfg=cohort_cfg,
                input_root=norm_input_root,
                db_conn=conn,
                chunks_map=chunks_map,
                unmounted_archive_owner=config["ownership"]["unmounted_archive_owner"],
                archive_cache_map=archive_maps_by_cohort.get(cid),
                precomputed_stream_metrics=table_stream_metrics.get(tbl),
                precomputed_chunk_metrics=table_chunk_metrics.get(tbl),
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
    out_index_path = resolved_outputs["index"]
    out_missing_path = resolved_outputs["missing_report"]
    out_receipt_path = resolved_outputs["receipt"]

    out_index_path.parent.mkdir(parents=True, exist_ok=True)
    out_missing_path.parent.mkdir(parents=True, exist_ok=True)
    out_receipt_path.parent.mkdir(parents=True, exist_ok=True)

    # Compute cohort metrics and progression decision (Finding 4)
    lit_records = [r for r in access_records if r["cohort_id"] == "literary-non-ocr"]
    tb_records = [r for r in access_records if r["cohort_id"] == "public-textbooks-non-stem-non-ocr"]

    lit_acc = sum(1 for r in lit_records if r["custody_resolution"]["status"] == "RESOLVED_ACCESSIBLE")
    lit_native = sum(1 for r in lit_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    lit_permitted = all(r["permitted_to_proceed"] for r in lit_records)
    first_cohort_ready = bool(lit_permitted and len(lit_records) > 0 and lit_acc == len(lit_records))

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
        "accessible_eligible_sources_permitted_to_proceed": derive_progression_decision(first_cohort_ready),
    }
    missing_validator = _load_schema(MISSING_REPORT_SCHEMA_PATH, roots)
    missing_errors = list(missing_validator.iter_errors(missing_report))
    if missing_errors:
        raise CustodyAccessError(f"Missing report schema failure: {missing_errors[0].message}")

    out_missing_path.write_text(json.dumps(missing_report, indent=2) + "\n", encoding="utf-8")
    missing_report_sha256 = sha256_file(out_missing_path)

    # Prepare receipt
    tb_acc = sum(
        1
        for r in tb_records
        if r["custody_resolution"]["status"] in ("RESOLVED_ACCESSIBLE", "PARTIAL_CHUNKS_AND_DB_ONLY")
        and r["permitted_to_proceed"]
    )
    tb_missing = sum(1 for r in tb_records if r["custody_resolution"]["status"] != "RESOLVED_ACCESSIBLE")
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

    receipt_id = _make_receipt_id(config_sha256, index_sha256, missing_report_sha256)
    first_cohort_ready = bool(lit_permitted and len(lit_records) > 0 and (lit_acc == len(lit_records)))
    custody_verdict = (
        "PROCEED_WITH_ACCESSIBLE_SOURCES" if first_cohort_ready and total_permitted > 0 else "HALT_INACCESSIBLE_SOURCES"
    )
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
            "first_eligible_cohort_ready": first_cohort_ready,
        },
        "verdict": custody_verdict,
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

    def _is_path_candidate(s: str) -> bool:
        if s.startswith(("/", "~")):
            return True
        if len(s) >= 3 and s[0].isalpha() and s[1] == ":" and s[2] == "/":
            return True
        if s.startswith("//"):
            return True
        if "/" in s:
            parts = [p.lower() for p in s.strip("/").split("/") if p]
            private_parts = {"home", "users", "root", "tmp", "temp", "var", "appdata", "private"}
            if any(p in private_parts or p.startswith("~") for p in parts):
                return True
        return False

    tokens = path_str.split()
    for token in tokens:
        t = token.strip("\"'()[]{}<>,;")
        if not t:
            continue
        normalized = t.replace("\\", "/")
        if _is_path_candidate(normalized):
            return True

        # Check sub-tokens after separators like = or : (e.g. location=/opt/private-corpus)
        if "=" in normalized:
            for sub in normalized.split("=")[1:]:
                sub = sub.strip("\"'()[]{}<>,;")
                if sub and _is_path_candidate(sub):
                    return True

        if ":" in normalized and "://" not in normalized:
            for sub in normalized.split(":")[1:]:
                sub = sub.strip("\"'()[]{}<>,;")
                if sub and _is_path_candidate(sub):
                    return True
        elif "://" in normalized:
            _, remainder = normalized.split("://", 1)
            remainder = remainder.strip("\"'()[]{}<>,;")
            if remainder.startswith("/"):
                if _is_path_candidate(remainder):
                    return True
            elif "/" in remainder:
                parts = [p.lower() for p in remainder.strip("/").split("/") if p]
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
    *,
    require_database: bool = False,
) -> bool:
    """Verify committed custody artifacts against contracts and invariants."""
    norm_input_root = input_root.resolve()
    norm_output_root = output_root.resolve()
    roots = _get_search_roots(norm_input_root)
    config, resolved_config_path = _load_config(config_path, roots)
    expected_config_sha256 = sha256_file(resolved_config_path)
    for c in config["cohorts"]:
        validate_cohort_spec(c)
    cohorts_by_id = {c["cohort_id"]: c for c in config["cohorts"]}

    _resolved_inputs, resolved_outputs = validate_and_resolve_paths(
        config, norm_input_root, norm_output_root, config_path=resolved_config_path
    )
    out_index_path = resolved_outputs["index"]
    out_missing_path = resolved_outputs["missing_report"]
    out_receipt_path = resolved_outputs["receipt"]

    for path, name in [
        (out_index_path, "Index"),
        (out_missing_path, "Missing report"),
        (out_receipt_path, "Receipt"),
    ]:
        if not path.is_file():
            raise CustodyAccessError(f"{name} artifact missing: {path}")

    # Revalidate configured source stores (Finding 1 & 2: ACCESS-1, ACCESS-2, ACCESS-3)
    db_path = _resolved_inputs.get("database")
    if require_database and (db_path is None or not db_path.is_file()):
        raise CustodyAccessError(f"Database missing or not found on host: {db_path}")

    db_conn: sqlite3.Connection | None = None
    if db_path is not None and db_path.is_file():
        db_uri = f"file:{db_path.resolve()}?mode=ro"
        conn_candidate = sqlite3.connect(db_uri, uri=True)
        cur = conn_candidate.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {r[0] for r in cur.fetchall()}
        required_tables = set(FAMILY_APPROVED_TABLES.values())
        missing_tables = required_tables - existing_tables
        if missing_tables:
            conn_candidate.close()
            if require_database:
                raise CustodyAccessError(f"Database {db_path} missing required tables: {sorted(missing_tables)}")
        else:
            db_conn = conn_candidate

    # Map chunk files from textbook_chunks_dir if available
    chunks_map: dict[str, Path] = {}
    chunks_dir = _resolved_inputs.get("textbook_chunks_dir")
    if chunks_dir is not None and chunks_dir.is_dir():
        for chunk_file in chunks_dir.glob("*/*.jsonl"):
            stem = chunk_file.name[:-6] if chunk_file.name.endswith(".jsonl") else chunk_file.stem
            chunks_map[stem] = chunk_file

    # Pre-build archive cache maps for cohorts (Finding 2)
    archive_maps_by_cohort: dict[str, dict[str, Path]] = {}
    for cid, c_cfg in cohorts_by_id.items():
        archive_maps_by_cohort[cid] = _build_archive_cache_map(
            c_cfg.get("archive_locator", ""),
            c_cfg.get("lineage_rule", ""),
            roots,
        )

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

    expected_receipt_id = _make_receipt_id(
        expected_config_sha256, expected_index_sha256, expected_missing_report_sha256
    )
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
    expected_missing_items = []
    seen_access_ids: set[str] = set()
    seen_source_identities: dict[str, tuple[str, str, str]] = {}
    seen_cohort_locators: set[tuple[str, str]] = set()

    try:
        # Load provenance denominator first to validate index source projection (ACCESS-1, ACCESS-4)
        prov_index_path = _resolve_file(Path(config["inputs"]["provenance_index"]), roots)
        if not prov_index_path.is_file():
            raise CustodyAccessError(f"Provenance index missing: {prov_index_path}")
        prov_identities: dict[str, tuple[str, str, str]] = {}
        with prov_index_path.open(encoding="utf-8") as pf:
            _ = pf.readline()
            for pline in pf:
                if not pline.strip():
                    continue
                prow = json.loads(pline)
                psid = prow["source_id"]
                psf = prow.get("source_locator", {}).get("source_file", "")
                pcid = prow.get("cohort_id", "")
                pfam = prow.get("source_family", "")
                if pcid not in cohorts_by_id:
                    raise CustodyAccessError(
                        f"Provenance denominator source {psid} references unconfigured cohort_id '{pcid}'"
                    )
                if cohorts_by_id[pcid].get("source_family") != pfam:
                    raise CustodyAccessError(
                        f"Provenance denominator source {psid} ({pcid}) source_family '{pfam}' "
                        f"does not match configured cohort source_family '{cohorts_by_id[pcid].get('source_family')}'"
                    )
                prov_identities[psid] = (psf, pcid, pfam)

        table_stream_metrics: dict[str, dict[str, tuple[int, int, str]]] = {}
        table_chunk_metrics: dict[str, dict[str, tuple[int, str]]] = {}
        if db_conn is not None:
            db_cur = db_conn.cursor()
            db_cur.execute("PRAGMA query_only = ON;")
            for tbl in set(FAMILY_APPROVED_TABLES.values()):
                selected_sfs = {
                    psf for psf, _pcid, pfam in prov_identities.values() if FAMILY_APPROVED_TABLES.get(pfam) == tbl
                }
                s_m, c_m = _precompute_table_source_metrics(db_conn, tbl, selected_source_files=selected_sfs)
                table_stream_metrics[tbl] = s_m
                table_chunk_metrics[tbl] = c_m

        with out_index_path.open(encoding="utf-8") as f:
            header_line = f.readline().strip()
            header = json.loads(header_line)

            # Strict schema and safety validation of index header
            expected_header_keys = {"schema_version", "config_sha256", "records", "ordering"}
            if set(header.keys()) != expected_header_keys:
                raise CustodyAccessError(
                    f"Index header keys mismatch: expected {expected_header_keys}, got {set(header.keys())}"
                )
            if header.get("schema_version") != "v4_source_custody_access_index_v1":
                raise CustodyAccessError("Index header schema_version invalid")
            if header.get("config_sha256") != expected_config_sha256:
                raise CustodyAccessError("Index header config_sha256 mismatch")
            if header.get("ordering") != "cohort_id,source_id":
                raise CustodyAccessError(f"Index header ordering invalid: {header.get('ordering')}")
            if not isinstance(header.get("records"), int) or header.get("records") < 0:
                raise CustodyAccessError(f"Index header records count invalid: {header.get('records')}")

            forbidden_keys = {"text", "content", "corpus_text", "raw_text", "body"}
            if forbidden_keys.intersection(header.keys()):
                recomputed_no_corpus_text = False
            if _contains_private_or_absolute_host_path(header):
                recomputed_no_private_host_paths = False

            for line_num, line in enumerate(f, start=2):
                if not line.strip():
                    continue
                record_count += 1
                row = json.loads(line)
                errors = list(item_validator.iter_errors(row))
                if errors:
                    raise CustodyAccessError(f"Index line {line_num} error: {errors[0].message}")

                source_id = row["source_id"]
                cohort_id = row["cohort_id"]
                source_family = row.get("source_family", "")
                source_file = row.get("source_locator", {}).get("source_file", "")

                if cohort_id not in cohorts_by_id:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): unconfigured cohort_id '{cohort_id}'"
                    )
                cohort_cfg = cohorts_by_id[cohort_id]
                if cohort_cfg.get("source_family") != source_family:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): source_family '{source_family}' "
                        f"does not match configured cohort source_family '{cohort_cfg.get('source_family')}'"
                    )

                if source_id in seen_source_identities:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): duplicate source_id in access index"
                    )

                if (cohort_id, source_file) in seen_cohort_locators:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): duplicate source locator ({cohort_id}, {source_file}) in access index"
                    )
                seen_cohort_locators.add((cohort_id, source_file))
                seen_source_identities[source_id] = (source_file, cohort_id, source_family)

                expected_access_id = _make_access_id(source_id, cohort_id)
                if row.get("access_id") != expected_access_id:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): access_id mismatch: "
                        f"expected {expected_access_id}, got {row.get('access_id')}"
                    )

                access_id = row["access_id"]
                if access_id in seen_access_ids:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): duplicate access_id {access_id} in access index"
                    )
                seen_access_ids.add(access_id)

                permitted = row["permitted_to_proceed"]
                status = row["lineage_verification"]["status"]
                lineage_mode = row["lineage_verification"].get("lineage_mode")
                is_ocr = row["lineage_verification"]["is_ocr_derived"]
                cust_status = row["custody_resolution"]["status"]
                host_reachable = row["custody_resolution"]["host_reachable"]
                metrics = row["bounded_read_metrics"]
                blocking_reason = row["blocking_reason"]

                # Explicit invariant checks across ALL rows (permitted and blocked)
                if status == "CONFIRMED_NATIVE":
                    if lineage_mode not in NATIVE_LINEAGE_MODES:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is CONFIRMED_NATIVE but lineage_mode is '{lineage_mode}'"
                        )
                    if is_ocr:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is CONFIRMED_NATIVE but is_ocr_derived is True"
                        )
                elif status == "UNKNOWN_LINEAGE":
                    if lineage_mode != "unknown":
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is UNKNOWN_LINEAGE but lineage_mode is '{lineage_mode}'"
                        )
                    if is_ocr:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is UNKNOWN_LINEAGE but is_ocr_derived is True"
                        )
                    if permitted:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"permitted_to_proceed is True but lineage status is UNKNOWN_LINEAGE"
                        )
                elif status == "EXCLUDED_OCR":
                    if lineage_mode not in OCR_LINEAGE_MODES:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is EXCLUDED_OCR but lineage_mode is '{lineage_mode}'"
                        )
                    if not is_ocr:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"lineage status is EXCLUDED_OCR but is_ocr_derived is False"
                        )
                    if permitted:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"permitted_to_proceed is True but lineage status is EXCLUDED_OCR"
                        )
                else:
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): unknown lineage status '{status}'"
                    )

                if lineage_mode == "unknown" and status != "UNKNOWN_LINEAGE":
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"lineage_mode is 'unknown' but lineage status is '{status}'"
                    )
                if lineage_mode in OCR_LINEAGE_MODES and status != "EXCLUDED_OCR":
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"lineage_mode is '{lineage_mode}' but lineage status is '{status}'"
                    )
                if lineage_mode in NATIVE_LINEAGE_MODES and status != "CONFIRMED_NATIVE":
                    raise CustodyAccessError(
                        f"Contradictory record at line {line_num} ({row['source_id']}): "
                        f"lineage_mode is '{lineage_mode}' but lineage status is '{status}'"
                    )

                if permitted:
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
                    expected_rule = cohort_cfg["lineage_rule"]
                    if expected_rule == "native_digital_source" and lineage_mode != "native_digital_source":
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"permitted_to_proceed is True but lineage_mode is '{lineage_mode}' "
                            f"instead of expected cohort lineage_rule '{expected_rule}'"
                        )
                    if expected_rule == "native_pdf_text" and lineage_mode not in (
                        "native_pdf_text",
                        "native_text",
                        "mixed_native",
                    ):
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"permitted_to_proceed is True but lineage_mode is '{lineage_mode}' "
                            f"instead of compatible native mode for cohort lineage_rule '{expected_rule}'"
                        )
                else:
                    if blocking_reason is None:
                        raise CustodyAccessError(
                            f"Contradictory record at line {line_num} ({row['source_id']}): "
                            f"permitted_to_proceed is False but blocking_reason is None"
                        )

                # Check projection against provenance denominator
                if source_id not in prov_identities or (source_file, cohort_id, source_family) != prov_identities.get(
                    source_id
                ):
                    raise CustodyAccessError(
                        f"Access index source projection does not match provenance denominator: "
                        f"source_id '{source_id}' identity ({source_file}, {cohort_id}, {source_family}) "
                        f"does not match provenance denominator {prov_identities.get(source_id)}"
                    )

                lineage_rule = cohort_cfg["lineage_rule"]
                archive_locator = cohort_cfg.get("archive_locator", "")

                if db_conn is not None:
                    # Probe host storage to re-resolve custody independently of index assertions (ACCESS-1, ACCESS-4)
                    archive_on_host = _check_archive_on_host(
                        archive_locator=archive_locator,
                        source_file=source_file,
                        lineage_rule=lineage_rule,
                        roots=roots,
                        cached_map=archive_maps_by_cohort.get(cohort_id),
                    )

                    chunk_path = chunks_map.get(source_file) if chunks_map else None
                    chunk_on_host = chunk_path is not None and chunk_path.is_file()

                    if cohort_id == "public-textbooks-non-stem-non-ocr":
                        re_resolved_status = (
                            "RESOLVED_ACCESSIBLE"
                            if archive_on_host
                            else ("PARTIAL_CHUNKS_AND_DB_ONLY" if chunk_on_host else "UNREACHABLE_ON_HOST")
                        )
                    else:
                        table = FAMILY_APPROVED_TABLES[source_family]
                        s_metrics = table_stream_metrics.get(table, {})
                        db_tuple = s_metrics.get(source_file)
                        re_resolved_status = (
                            "RESOLVED_ACCESSIBLE" if db_tuple is not None and db_tuple[0] > 0 else "UNREACHABLE_ON_HOST"
                        )

                    expected_host_reachable = re_resolved_status != "UNREACHABLE_ON_HOST"
                    if cust_status != re_resolved_status:
                        raise CustodyAccessError(
                            f"Index line {line_num} ({source_id}): custody status mismatch: "
                            f"stored '{cust_status}', host probe derived '{re_resolved_status}'"
                        )
                    if host_reachable != expected_host_reachable:
                        raise CustodyAccessError(
                            f"Index line {line_num} ({source_id}): host_reachable mismatch: "
                            f"stored '{host_reachable}', host probe derived '{expected_host_reachable}'"
                        )

                    # Revalidate database and lineage against current host stores (Finding 1)
                    table = FAMILY_APPROVED_TABLES[source_family]
                    s_metrics = table_stream_metrics.get(table, {})
                    c_metrics = table_chunk_metrics.get(table, {})

                    if source_family == "literary":
                        db_tuple = s_metrics.get(source_file)
                        if permitted:
                            if db_tuple is None:
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): source permitted but not found in database table '{table}'"
                                )
                            db_rec_count, db_char_count, actual_stream_hash = db_tuple
                            if metrics["observed_records"] != db_rec_count:
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): observed_records mismatch: "
                                    f"index has {metrics['observed_records']}, database has {db_rec_count}"
                                )
                            if metrics["observed_characters"] != db_char_count:
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): observed_characters mismatch: "
                                    f"index has {metrics['observed_characters']}, database has {db_char_count}"
                                )
                            if metrics["stream_sha256"] != actual_stream_hash:
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): stream_sha256 mismatch: "
                                    f"index has {metrics['stream_sha256']}, database has {actual_stream_hash}"
                                )
                        else:
                            if db_tuple is not None:
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): source marked unpermitted but found in database table '{table}'"
                                )

                    elif source_family == "public_textbooks":
                        excluded_modes = cohort_cfg.get("excluded_modes", OCR_LINEAGE_MODES)
                        if chunk_on_host:
                            chunk_mode, chunk_is_ocr, chunk_rows, _chunk_chars, chunk_digest = check_chunk_file_lineage(
                                chunk_path, excluded_modes
                            )
                            if chunk_is_ocr:
                                if status != "EXCLUDED_OCR" or not is_ocr or lineage_mode != chunk_mode:
                                    raise CustodyAccessError(
                                        f"Index line {line_num} ({source_id}): chunk file has OCR lineage ({chunk_mode}) "
                                        f"but index has status={status}, lineage_mode={lineage_mode}, is_ocr={is_ocr}"
                                    )
                                if permitted:
                                    raise CustodyAccessError(
                                        f"Index line {line_num} ({source_id}): chunk file has OCR lineage but index permits it to proceed"
                                    )
                            elif chunk_mode in ("native_pdf_text", "native_text", "mixed_native"):
                                db_chk = c_metrics.get(source_file)
                                db_str = s_metrics.get(source_file)

                                if db_chk is None:
                                    if permitted or status != "UNKNOWN_LINEAGE":
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): source records not found in database, "
                                            f"but index has status={status}, permitted={permitted}"
                                        )
                                elif db_chk[0] != chunk_rows or db_chk[1] != chunk_digest:
                                    if permitted or status != "UNKNOWN_LINEAGE":
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): database content does not match chunk lineage, "
                                            f"but index has status={status}, permitted={permitted}"
                                        )
                                else:
                                    if status != "CONFIRMED_NATIVE" or lineage_mode != chunk_mode or not permitted:
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): native chunk and db match, "
                                            f"but index has status={status}, lineage_mode={lineage_mode}, permitted={permitted}"
                                        )
                                    tb_rec_count, tb_char_count, tb_stream_hash = db_str if db_str else (0, 0, None)
                                    if metrics["observed_records"] != tb_rec_count:
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): observed_records mismatch: "
                                            f"index has {metrics['observed_records']}, database has {tb_rec_count}"
                                        )
                                    if metrics["observed_characters"] != tb_char_count:
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): observed_characters mismatch: "
                                            f"index has {metrics['observed_characters']}, database has {tb_char_count}"
                                        )
                                    if metrics["stream_sha256"] != tb_stream_hash:
                                        raise CustodyAccessError(
                                            f"Index line {line_num} ({source_id}): stream_sha256 mismatch: "
                                            f"index has {metrics['stream_sha256']}, database has {tb_stream_hash}"
                                        )
                            else:
                                if permitted or status != "UNKNOWN_LINEAGE":
                                    raise CustodyAccessError(
                                        f"Index line {line_num} ({source_id}): chunk has unknown extraction mode '{chunk_mode}', "
                                        f"but index has status={status}, permitted={permitted}"
                                    )
                        else:
                            if permitted or status != "UNKNOWN_LINEAGE":
                                raise CustodyAccessError(
                                    f"Index line {line_num} ({source_id}): chunk file not on host, "
                                    f"but index has status={status}, permitted={permitted}"
                                )
                else:
                    re_resolved_status = cust_status

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
                expected_p_store = f"sqlite:sources.db#{FAMILY_APPROVED_TABLES[source_family]}"
                if p_store != expected_p_store:
                    raise CustodyAccessError(
                        f"Index line {line_num} ({source_id}): primary_store '{p_store}' does not match expected '{expected_p_store}'"
                    )

                c_store = cust.get("chunks_store") or ""
                if c_store and not c_store.startswith("file:data/textbook_chunks/"):
                    recomputed_no_new_storage_infrastructure = False

                if is_ocr and (status != "EXCLUDED_OCR" or permitted):
                    recomputed_ocr_derived_excluded = False
                if status == "EXCLUDED_OCR" and (permitted or lineage_mode not in OCR_LINEAGE_MODES or not is_ocr):
                    recomputed_ocr_derived_excluded = False
                if lineage_mode in OCR_LINEAGE_MODES and (status != "EXCLUDED_OCR" or permitted or not is_ocr):
                    recomputed_ocr_derived_excluded = False

                if (status == "UNKNOWN_LINEAGE" or lineage_mode == "unknown") and (
                    status == "CONFIRMED_NATIVE" or permitted
                ):
                    recomputed_unknown_not_native = False
                if status == "CONFIRMED_NATIVE" and lineage_mode not in NATIVE_LINEAGE_MODES:
                    recomputed_unknown_not_native = False
                if status == "UNKNOWN_LINEAGE" and lineage_mode != "unknown":
                    recomputed_unknown_not_native = False
                if lineage_mode == "unknown" and status != "UNKNOWN_LINEAGE":
                    recomputed_unknown_not_native = False
                if status != "CONFIRMED_NATIVE" and lineage_mode is None and permitted:
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

                m_item = derive_missing_report_item(row, config, effective_custody_status=re_resolved_status)
                if m_item is not None:
                    expected_missing_items.append(m_item)
    finally:
        if db_conn is not None:
            db_conn.close()

    if header.get("records") != record_count:
        raise CustodyAccessError(f"Index header record count {header.get('records')} != observed {record_count}")

    # Compare complete source projection against bound provenance denominator
    prov_index_path = _resolve_file(Path(config["inputs"]["provenance_index"]), roots)
    if not prov_index_path.is_file():
        raise CustodyAccessError(f"Provenance index missing: {prov_index_path}")
    prov_identities: dict[str, tuple[str, str, str]] = {}
    with prov_index_path.open(encoding="utf-8") as pf:
        _ = pf.readline()
        for pline in pf:
            if not pline.strip():
                continue
            prow = json.loads(pline)
            psid = prow["source_id"]
            psf = prow.get("source_locator", {}).get("source_file", "")
            pcid = prow.get("cohort_id", "")
            pfam = prow.get("source_family", "")
            if pcid not in cohorts_by_id:
                raise CustodyAccessError(
                    f"Provenance denominator source {psid} references unconfigured cohort_id '{pcid}'"
                )
            if cohorts_by_id[pcid].get("source_family") != pfam:
                raise CustodyAccessError(
                    f"Provenance denominator source {psid} ({pcid}) source_family '{pfam}' "
                    f"does not match configured cohort source_family '{cohorts_by_id[pcid].get('source_family')}'"
                )
            prov_identities[psid] = (psf, pcid, pfam)
    if seen_source_identities != prov_identities:
        missing = set(prov_identities.keys()) - set(seen_source_identities.keys())
        extra = set(seen_source_identities.keys()) - set(prov_identities.keys())
        mismatches = [
            sid
            for sid in (set(seen_source_identities.keys()) & set(prov_identities.keys()))
            if seen_source_identities[sid] != prov_identities[sid]
        ]
        raise CustodyAccessError(
            f"Access index source projection does not match provenance denominator: "
            f"{len(missing)} missing, {len(extra)} unexpected, {len(mismatches)} projection mismatches"
        )

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
        rc_lit.get("cohort_id") != "literary-non-ocr"
        or rc_lit.get("total_sources") != len(lit_records)
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
    tb_missing = sum(1 for r in tb_records if r["custody_resolution"]["status"] != "RESOLVED_ACCESSIBLE")
    tb_native = sum(1 for r in tb_records if r["lineage_verification"]["status"] == "CONFIRMED_NATIVE")
    tb_perm = sum(1 for r in tb_records if r["permitted_to_proceed"])

    rc_tb = summary.get("textbook_cohort", {})
    if (
        rc_tb.get("cohort_id") != "public-textbooks-non-stem-non-ocr"
        or rc_tb.get("total_sources") != len(tb_records)
        or rc_tb.get("accessible_sources") != tb_acc
        or rc_tb.get("missing_on_host") != tb_missing
        or rc_tb.get("confirmed_native") != tb_native
        or rc_tb.get("permitted_to_proceed") != tb_perm
    ):
        raise CustodyAccessError("Receipt textbook_cohort discrepancy")

    # Verify missing report schema and invariants (ACCESS-4)
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
        raise CustodyAccessError(f"Receipt verdict mismatch: expected {expected_verdict}, got {receipt.get('verdict')}")

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

    # Cross-check missing report metadata against config
    expected_owner = config.get("ownership", {}).get("unmounted_archive_owner")
    if missing_report.get("owner") != expected_owner:
        raise CustodyAccessError(
            f"Missing report owner mismatch: expected '{expected_owner}', got '{missing_report.get('owner')}'"
        )

    expected_scope = config.get("ownership", {}).get("blocks_scope")
    if missing_report.get("scope") != expected_scope:
        raise CustodyAccessError(
            f"Missing report scope mismatch: expected '{expected_scope}', got '{missing_report.get('scope')}'"
        )

    expected_date = config.get("operator_decision", {}).get("date")
    if missing_report.get("operator_decision_date") != expected_date:
        raise CustodyAccessError(
            f"Missing report operator_decision_date mismatch: expected '{expected_date}', "
            f"got '{missing_report.get('operator_decision_date')}'"
        )

    expected_issue = config.get("operator_decision", {}).get("issue")
    if missing_report.get("issue") != expected_issue:
        raise CustodyAccessError(
            f"Missing report issue mismatch: expected {expected_issue}, got {missing_report.get('issue')}"
        )

    expected_archive_locator = config.get("inputs", {}).get("retained_archive_locator")
    if missing_report.get("unmounted_archive_locator") != expected_archive_locator:
        raise CustodyAccessError(
            f"Missing report unmounted_archive_locator mismatch: expected '{expected_archive_locator}', "
            f"got '{missing_report.get('unmounted_archive_locator')}'"
        )

    # Validate missing-report progression decision (Finding 4)
    expected_progression = derive_progression_decision(expected_first_ready)
    obs_progression = missing_report.get("accessible_eligible_sources_permitted_to_proceed")
    if obs_progression != expected_progression:
        raise CustodyAccessError(
            f"Missing report accessible_eligible_sources_permitted_to_proceed mismatch: "
            f"expected {expected_progression}, got {obs_progression}"
        )

    # Cross-check derived missing entries against missing_report["missing_inputs"] (Finding 3)
    observed_missing_inputs = missing_report.get("missing_inputs", [])
    if len(observed_missing_inputs) != len(expected_missing_items):
        raise CustodyAccessError(
            f"Missing report item count mismatch: derived {len(expected_missing_items)} missing items from access index, "
            f"but missing report contains {len(observed_missing_inputs)}"
        )

    derived_by_id = {item["source_id"]: item for item in expected_missing_items}
    seen_missing_ids: set[str] = set()
    for idx, obs_item in enumerate(observed_missing_inputs):
        sid = obs_item.get("source_id")
        if sid in seen_missing_ids:
            raise CustodyAccessError(f"Missing report entry {idx} has duplicate source_id '{sid}' in missing_inputs")
        seen_missing_ids.add(sid)
        if sid not in derived_by_id:
            raise CustodyAccessError(
                f"Missing report entry {idx} has unexpected source_id '{sid}' not derived as missing from access index"
            )
        exp_item = derived_by_id[sid]
        if obs_item != exp_item:
            raise CustodyAccessError(f"Missing report entry for '{sid}' mismatch: expected {exp_item}, got {obs_item}")

    if seen_missing_ids != set(derived_by_id.keys()):
        missing_sids = set(derived_by_id.keys()) - seen_missing_ids
        raise CustodyAccessError(
            f"Missing report does not contain all derived missing sources: missing {len(missing_sids)} ({missing_sids})"
        )

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
            success = verify(args.config, args.input_root, args.output_root, require_database=True)
            if success:
                print("Custody access verification PASSED with 0 errors.")
                return 0
            return 1
        elif args.command == "read":
            reader = BoundedCustodyReader(args.database)
            result = reader.read_source_stream(args.table, args.source_file, args.batch_size)
            print(canonical_json(result))
            if result.get("records_streamed", 0) == 0:
                print(
                    f"Error: Access proof failed — source '{args.source_file}' yielded 0 records in '{args.table}'",
                    file=sys.stderr,
                )
                return 1
            return 0
    except CustodyAccessError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
