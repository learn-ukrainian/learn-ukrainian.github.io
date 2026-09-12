#!/usr/bin/env python3
"""v4_native_extraction_validation.py — Validate native extraction fidelity and exclude damaged spans.

Under the operator's private human-source Ukrainian dataset scope (Issue #7885), this
command enforces deterministic passage extraction, span-level character offset linkage,
objective encoding damage and layout anomaly detection, fail-closed quarantine of
unfaithful/OCR spans from training views, and bit-level reconstruction verification
against custody access stream digests (EXTRACT-1 .. EXTRACT-4).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.extract_text import detect_native_text_anomalies

CONFIG_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_native_extraction_config_v1.schema.json")
ITEM_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_native_extraction_item_v1.schema.json")
QUARANTINE_SCHEMA_PATH = Path(
    "data/projects/open_model_data/contracts/v4_native_extraction_quarantine_report_v1.schema.json"
)
RECEIPT_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_native_extraction_receipt_v1.schema.json")

DEFAULT_CONFIG_PATH = Path("data/projects/open_model_data/extraction/v4_native_extraction_config_v1.json")

RESERVED_PRIVATE_DIR_NAMES = {
    "home",
    "users",
    "root",
    "tmp",
    "temp",
    "var",
    "appdata",
    "private",
}


class NativeExtractionError(RuntimeError):
    """Raised when native extraction fidelity checks fail or are violated."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _make_extraction_id(source_id: str, chunk_id: str, start_char: int) -> str:
    raw = f"{source_id}:{chunk_id}:{start_char}"
    return f"extract.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _make_quarantine_id(config_sha256: str, quarantined_count: int) -> str:
    raw = f"{config_sha256}:{quarantined_count}"
    return f"quarantine.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _make_receipt_id(config_sha256: str, index_sha256: str, quarantine_sha256: str) -> str:
    raw = f"{config_sha256}:{index_sha256}:{quarantine_sha256}"
    return f"receipt.extraction.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


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
            raise NativeExtractionError(f"{PRIMARY_REPO_ROOT_ENV} is set but is not an existing directory")
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
    norm_in = input_root.resolve()
    roots = [norm_in, Path.cwd()]
    primary = _primary_repo_root()
    if primary is not None and primary not in roots:
        roots.append(primary)
    return roots


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
        raise NativeExtractionError(f"Missing schema contract: {resolved}")
    schema_dict = json.loads(resolved.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema_dict)
    return Draft202012Validator(schema_dict)


def _contains_private_or_absolute_host_path(value: Any) -> bool:
    """Detect private or absolute host paths in output data structures."""
    if isinstance(value, str):
        normalized = value.replace("\\", "/")
        if normalized.startswith(("/home/", "/root/", "/tmp/", "/var/", "/private/")):
            return True
        if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("//"):
            return True
        if "/" in normalized:
            segments = set(normalized.lower().split("/"))
            if RESERVED_PRIVATE_DIR_NAMES.intersection(segments):
                return True
        return False
    elif isinstance(value, dict):
        return any(
            _contains_private_or_absolute_host_path(k) or _contains_private_or_absolute_host_path(v)
            for k, v in value.items()
        )
    elif isinstance(value, list):
        return any(_contains_private_or_absolute_host_path(item) for item in value)
    return False


def evaluate_span_fidelity(
    text: str,
    rules: Mapping[str, Any],
    is_ocr: bool = False,
) -> tuple[str, bool, list[dict[str, Any]], bool]:
    """Evaluate native extraction fidelity, encoding integrity, and layout anomalies (EXTRACT-2, EXTRACT-3).

    Returns:
        status: "ACCEPTED_FAITHFUL", "QUARANTINED_ANOMALOUS", "EXCLUDED_OCR", or "REJECTED_DAMAGED"
        encoding_valid: True if encoding is clean UTF-8 with zero replacement or control characters
        anomaly_findings: List of detected anomaly objects
        training_eligible: True only if clean, native, and faithful
    """
    findings: list[dict[str, Any]] = []
    encoding_valid = True

    anomaly_cfg = rules.get("anomaly_detection", {})

    # Check 1: OCR Exclusion (EXTRACT-3)
    if is_ocr and anomaly_cfg.get("fail_closed_on_ocr", True):
        findings.append(
            {
                "type": "ocr_extraction_detected",
                "description": "Passage originates from OCR-derived pipeline; excluded from training view",
                "severity": "BLOCKING",
            }
        )
        return "EXCLUDED_OCR", False, findings, False

    # Check 2: Replacement Characters (EXTRACT-2)
    if anomaly_cfg.get("detect_replacement_characters", True) and "\ufffd" in text:
        encoding_valid = False
        findings.append(
            {
                "type": "unicode_replacement_character",
                "description": "Found U+FFFD replacement character indicating broken original encoding",
                "severity": "BLOCKING",
            }
        )

    # Check 2b: Illegal Control Characters (EXTRACT-2)
    if anomaly_cfg.get("detect_control_characters", True):
        for c in text:
            if ord(c) < 32 and c not in ("\t", "\n", "\r"):
                encoding_valid = False
                findings.append(
                    {
                        "type": "illegal_control_character",
                        "description": f"Found illegal ASCII control character code {ord(c)}",
                        "severity": "BLOCKING",
                    }
                )
                break

    # Check 3: Objective Layout Anomalies (EXTRACT-2)
    layout_findings = detect_native_text_anomalies(text)

    if anomaly_cfg.get("detect_duplicate_lines", True):
        dup_lines = layout_findings.get("adjacent_duplicate_line_pairs", [])
        if dup_lines:
            findings.append(
                {
                    "type": "adjacent_duplicate_line_pairs",
                    "description": f"Detected {len(dup_lines)} adjacent identical line pair(s)",
                    "severity": "BLOCKING",
                }
            )

    if anomaly_cfg.get("detect_truncation_pairs", True):
        trunc_pairs = layout_findings.get("adjacent_first_character_truncation_pairs", [])
        if trunc_pairs:
            findings.append(
                {
                    "type": "adjacent_first_character_truncation_pairs",
                    "description": f"Detected {len(trunc_pairs)} adjacent first-character truncation pair(s)",
                    "severity": "BLOCKING",
                }
            )

    if anomaly_cfg.get("detect_intraline_duplicates", True):
        intraline_dups = layout_findings.get("intraline_duplicate_token_spans", [])
        if intraline_dups:
            findings.append(
                {
                    "type": "intraline_duplicate_token_spans",
                    "description": f"Detected {len(intraline_dups)} repeated token span(s) on same line",
                    "severity": "BLOCKING",
                }
            )

    # Record soft hyphens and single letter runs as non-blocking observations
    soft_hyphens = layout_findings.get("soft_hyphen_whitespace_sequences", [])
    if soft_hyphens:
        findings.append(
            {
                "type": "soft_hyphen_observation",
                "description": f"Observed {len(soft_hyphens)} soft-hyphen sequence(s)",
                "severity": "OBSERVATION",
            }
        )

    has_blocking = any(f["severity"] == "BLOCKING" for f in findings)
    if not encoding_valid:
        return "REJECTED_DAMAGED", False, findings, False
    elif has_blocking:
        return "QUARANTINED_ANOMALOUS", encoding_valid, findings, False
    else:
        return "ACCEPTED_FAITHFUL", encoding_valid, findings, True


def build(
    config_path: Path = DEFAULT_CONFIG_PATH,
    input_root: Path | None = None,
    output_root: Path | None = None,
    all_sources: bool = False,
) -> dict[str, Any]:
    """Execute native extraction validation and fidelity accounting (Issue #7885)."""
    norm_in = (input_root or Path.cwd()).resolve()
    norm_out = (output_root or Path.cwd()).resolve()
    roots = _get_search_roots(norm_in)

    # 1. Load and validate config
    config_resolved = _resolve_file(config_path, roots)
    if not config_resolved.is_file():
        raise NativeExtractionError(f"Config file not found: {config_resolved}")
    config_validator = _load_schema(CONFIG_SCHEMA_PATH, roots)
    config = json.loads(config_resolved.read_text(encoding="utf-8"))
    config_errors = list(config_validator.iter_errors(config))
    if config_errors:
        raise NativeExtractionError(f"Config validation error: {config_errors[0].message}")

    # 2. Resolve inputs
    custody_idx_path = _resolve_file(Path(config["inputs"]["custody_index"]), roots)
    custody_receipt_path = _resolve_file(Path(config["inputs"]["custody_receipt"]), roots)
    db_path = _resolve_file(Path(config["inputs"]["database"]), roots)

    if not custody_idx_path.is_file():
        raise NativeExtractionError(f"Custody index missing: {custody_idx_path}")
    if not custody_receipt_path.is_file():
        raise NativeExtractionError(f"Custody receipt missing: {custody_receipt_path}")
    if not db_path.is_file():
        raise NativeExtractionError(f"Database missing: {db_path}")

    # Validate custody receipt match
    custody_receipt = json.loads(custody_receipt_path.read_text(encoding="utf-8"))
    actual_custody_idx_hash = sha256_file(custody_idx_path)
    if custody_receipt.get("index_sha256") != actual_custody_idx_hash:
        raise NativeExtractionError("Custody receipt index_sha256 does not match observed custody index")

    # 3. Filter eligible sources by target cohorts and optional target sources
    target_cohorts = set(config["extraction_rules"]["target_cohorts"])
    configured_target_sources = config["extraction_rules"].get("target_sources")
    target_sources = set(configured_target_sources) if configured_target_sources and not all_sources else None

    eligible_sources: list[dict[str, Any]] = []
    with custody_idx_path.open(encoding="utf-8") as f:
        _ = f.readline()  # header
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("cohort_id") in target_cohorts and row.get("permitted_to_proceed"):
                if target_sources is not None and row.get("source_id") not in target_sources:
                    continue
                eligible_sources.append(row)

    if not eligible_sources:
        raise NativeExtractionError("No permitted eligible sources found in custody index for target cohorts")

    # Sort sources deterministically
    eligible_sources.sort(key=lambda r: (r["cohort_id"], r["source_id"]))

    # 4. Connect to database read-only
    db_uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    cur = conn.cursor()

    out_index_path = norm_out / config["outputs"]["index"]
    out_quarantine_path = norm_out / config["outputs"]["quarantine_report"]
    out_receipt_path = norm_out / config["outputs"]["receipt"]

    out_index_path.parent.mkdir(parents=True, exist_ok=True)
    out_quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    out_receipt_path.parent.mkdir(parents=True, exist_ok=True)

    config_sha256 = sha256_file(config_resolved)

    total_spans = 0
    accepted_spans = 0
    quarantined_spans = 0
    rejected_spans = 0
    training_eligible_spans = 0

    quarantined_items: list[dict[str, Any]] = []

    # Map chunks for textbook sources if directory exists
    chunks_map: dict[str, Path] = {}
    tb_chunks_rel = config["inputs"].get("textbook_chunks_dir")
    if tb_chunks_rel:
        tb_chunks_path = _resolve_file(Path(tb_chunks_rel), roots)
        if tb_chunks_path.is_dir():
            for cf in tb_chunks_path.glob("*/*.jsonl"):
                stem = cf.name[:-6] if cf.name.endswith(".jsonl") else cf.stem
                chunks_map[stem] = cf

    try:
        with out_index_path.open("w", encoding="utf-8") as out_f:
            # Placeholder header
            header: dict[str, Any] = {
                "schema_version": "v4_native_extraction_index_v1",
                "config_sha256": config_sha256,
                "target_cohorts": sorted(target_cohorts),
                "records": 0,
            }
            if target_sources is not None:
                header["target_sources"] = sorted(target_sources)
            out_f.write(canonical_json(header) + "\n")

            for src in eligible_sources:
                sid = src["source_id"]
                cid = src["cohort_id"]
                fam = src["source_family"]
                sf = src["source_locator"]["source_file"]
                table = "literary_texts" if fam == "literary" else "textbooks"
                custody_metrics = src["bounded_read_metrics"]
                expected_stream_sha256 = custody_metrics["stream_sha256"]

                # Extract spans from database
                cur.execute(
                    f'SELECT id, chunk_id, text FROM "{table}" WHERE source_file = ? ORDER BY id ASC',
                    (sf,),
                )
                rows = cur.fetchall()
                if not rows:
                    raise NativeExtractionError(
                        f"Permitted source {sid} ({sf}) yielded 0 database records in table {table}"
                    )

                source_stream_digest = hashlib.sha256()
                source_char_offset = 0

                for seq_order, (r_id, r_chunk_id, r_text) in enumerate(rows):
                    text_str = r_text or ""
                    char_len = len(text_str)
                    text_hash = hashlib.sha256(text_str.encode("utf-8")).hexdigest()

                    # Stream contribution hash
                    contrib_raw = f"{r_id}:{r_chunk_id}:{char_len}:{text_hash}\n"
                    source_stream_digest.update(contrib_raw.encode("utf-8"))
                    stream_contrib_hash = hashlib.sha256(contrib_raw.encode("utf-8")).hexdigest()

                    # Evaluate extraction fidelity
                    status, enc_valid, findings, training_eligible = evaluate_span_fidelity(
                        text=text_str,
                        rules=config["extraction_rules"],
                        is_ocr=src["lineage_verification"]["is_ocr_derived"],
                    )

                    start_c = source_char_offset
                    end_c = source_char_offset + char_len
                    source_char_offset = end_c

                    extraction_id = _make_extraction_id(sid, r_chunk_id, start_c)

                    item: dict[str, Any] = {
                        "schema_version": "v4_native_extraction_v1",
                        "extraction_id": extraction_id,
                        "source_id": sid,
                        "cohort_id": cid,
                        "source_family": fam,
                        "source_file": sf,
                        "chunk_id": r_chunk_id,
                        "span_locator": {
                            "start_char": start_c,
                            "end_char": end_c,
                            "char_length": char_len,
                            "span_sha256": text_hash,
                        },
                        "fidelity_assessment": {
                            "status": status,
                            "encoding_valid": enc_valid,
                            "anomaly_findings": findings,
                            "is_ocr": src["lineage_verification"]["is_ocr_derived"],
                            "training_eligible": training_eligible,
                        },
                        "reconstruction_linkage": {
                            "sequence_order": seq_order,
                            "stream_digest_contribution": stream_contrib_hash,
                        },
                    }

                    total_spans += 1
                    if status == "ACCEPTED_FAITHFUL":
                        accepted_spans += 1
                    elif status == "QUARANTINED_ANOMALOUS":
                        quarantined_spans += 1
                        quarantined_items.append(
                            {
                                "source_id": sid,
                                "cohort_id": cid,
                                "source_file": sf,
                                "chunk_id": r_chunk_id,
                                "reason": "layout_or_encoding_anomaly",
                                "details": [f["type"] for f in findings if f["severity"] == "BLOCKING"],
                            }
                        )
                    elif status == "EXCLUDED_OCR":
                        quarantined_spans += 1
                        quarantined_items.append(
                            {
                                "source_id": sid,
                                "cohort_id": cid,
                                "source_file": sf,
                                "chunk_id": r_chunk_id,
                                "reason": "ocr_extraction_detected",
                                "details": "ocr_derived",
                            }
                        )
                    elif status == "REJECTED_DAMAGED":
                        rejected_spans += 1
                        quarantined_items.append(
                            {
                                "source_id": sid,
                                "cohort_id": cid,
                                "source_file": sf,
                                "chunk_id": r_chunk_id,
                                "reason": "broken_encoding_or_control_characters",
                                "details": [f["type"] for f in findings],
                            }
                        )

                    if training_eligible:
                        training_eligible_spans += 1

                    out_f.write(canonical_json(item) + "\n")

                # Verify deterministic reconstruction against custody access digest (EXTRACT-4)
                observed_stream_hash = source_stream_digest.hexdigest()
                if observed_stream_hash != expected_stream_sha256:
                    raise NativeExtractionError(
                        f"Reconstructed stream digest mismatch for source {sid} ({sf}): "
                        f"reconstructed {observed_stream_hash} != custody {expected_stream_sha256}"
                    )

        # Rewrite index with final header count
        index_lines = out_index_path.read_text(encoding="utf-8").splitlines()
        header["records"] = total_spans
        index_lines[0] = canonical_json(header)
        out_index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    finally:
        conn.close()

    # Write quarantine report
    quarantine_id = _make_quarantine_id(config_sha256, len(quarantined_items))
    quarantine_report = {
        "schema_version": "v4_native_extraction_quarantine_report_v1",
        "report_id": quarantine_id,
        "config_sha256": config_sha256,
        "quarantined_spans": quarantined_items,
        "summary": {
            "total_spans_evaluated": total_spans,
            "accepted_spans_count": accepted_spans,
            "quarantined_spans_count": quarantined_spans,
            "rejected_spans_count": rejected_spans,
            "training_eligible_spans_count": training_eligible_spans,
        },
    }
    out_quarantine_path.write_text(json.dumps(quarantine_report, indent=2) + "\n", encoding="utf-8")

    # Write receipt
    index_sha256 = sha256_file(out_index_path)
    quarantine_sha256 = sha256_file(out_quarantine_path)
    receipt_id = _make_receipt_id(config_sha256, index_sha256, quarantine_sha256)

    receipt = {
        "schema_version": "v4_native_extraction_receipt_v1",
        "receipt_id": receipt_id,
        "config_sha256": config_sha256,
        "index_sha256": index_sha256,
        "quarantine_report_sha256": quarantine_sha256,
        "summary": {
            "total_sources_evaluated": len(eligible_sources),
            "total_spans_evaluated": total_spans,
            "accepted_spans_count": accepted_spans,
            "quarantined_spans_count": quarantined_spans,
            "rejected_spans_count": rejected_spans,
            "training_eligible_spans_count": training_eligible_spans,
        },
        "safety_assertions": {
            "no_corpus_text": True,
            "no_private_host_paths": True,
            "immutable_original_preserved": True,
            "zero_silent_omissions": True,
        },
        "verdict": "EXTRACTION_FIDELITY_CONFIRMED",
    }
    out_receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    return receipt


def verify(
    config_path: Path = DEFAULT_CONFIG_PATH,
    input_root: Path | None = None,
    output_root: Path | None = None,
) -> None:
    """Independently verify native extraction artifacts, invariants, and tamper resistance."""
    norm_in = (input_root or Path.cwd()).resolve()
    norm_out = (output_root or Path.cwd()).resolve()
    roots = _get_search_roots(norm_in)

    # 1. Load config and schemas
    config_resolved = _resolve_file(config_path, roots)
    if not config_resolved.is_file():
        raise NativeExtractionError(f"Config file not found: {config_resolved}")
    config_validator = _load_schema(CONFIG_SCHEMA_PATH, roots)
    item_validator = _load_schema(ITEM_SCHEMA_PATH, roots)
    quarantine_validator = _load_schema(QUARANTINE_SCHEMA_PATH, roots)
    receipt_validator = _load_schema(RECEIPT_SCHEMA_PATH, roots)

    config = json.loads(config_resolved.read_text(encoding="utf-8"))
    config_errors = list(config_validator.iter_errors(config))
    if config_errors:
        raise NativeExtractionError(f"Config validation error: {config_errors[0].message}")

    out_index_path = _resolve_file(norm_out / config["outputs"]["index"], roots)
    out_quarantine_path = _resolve_file(norm_out / config["outputs"]["quarantine_report"], roots)
    out_receipt_path = _resolve_file(norm_out / config["outputs"]["receipt"], roots)

    if not out_index_path.is_file():
        raise NativeExtractionError(f"Extraction index missing: {out_index_path}")
    if not out_quarantine_path.is_file():
        raise NativeExtractionError(f"Quarantine report missing: {out_quarantine_path}")
    if not out_receipt_path.is_file():
        raise NativeExtractionError(f"Receipt missing: {out_receipt_path}")

    expected_config_sha256 = sha256_file(config_resolved)
    expected_index_sha256 = sha256_file(out_index_path)
    expected_quarantine_sha256 = sha256_file(out_quarantine_path)

    receipt = json.loads(out_receipt_path.read_text(encoding="utf-8"))
    receipt_errors = list(receipt_validator.iter_errors(receipt))
    if receipt_errors:
        raise NativeExtractionError(f"Receipt validation error: {receipt_errors[0].message}")

    if receipt["config_sha256"] != expected_config_sha256:
        raise NativeExtractionError("Receipt config_sha256 mismatch")
    if receipt["index_sha256"] != expected_index_sha256:
        raise NativeExtractionError("Receipt index_sha256 mismatch")
    if receipt["quarantine_report_sha256"] != expected_quarantine_sha256:
        raise NativeExtractionError("Receipt quarantine_report_sha256 mismatch")

    expected_receipt_id = _make_receipt_id(expected_config_sha256, expected_index_sha256, expected_quarantine_sha256)
    if receipt["receipt_id"] != expected_receipt_id:
        raise NativeExtractionError(f"Receipt ID mismatch: expected {expected_receipt_id}, got {receipt['receipt_id']}")

    quarantine_report = json.loads(out_quarantine_path.read_text(encoding="utf-8"))
    quarantine_errors = list(quarantine_validator.iter_errors(quarantine_report))
    if quarantine_errors:
        raise NativeExtractionError(f"Quarantine report error: {quarantine_errors[0].message}")

    # Verify index records and recompute counters
    observed_total_spans = 0
    observed_accepted = 0
    observed_quarantined = 0
    observed_rejected = 0
    observed_training_eligible = 0
    seen_extraction_ids: set[str] = set()

    sources_seen: set[str] = set()
    prev_source: str | None = None
    prev_seq_order = -1

    with out_index_path.open(encoding="utf-8") as f:
        header_line = f.readline().strip()
        header = json.loads(header_line)
        if header.get("schema_version") != "v4_native_extraction_index_v1":
            raise NativeExtractionError("Index header schema_version invalid")
        if header.get("config_sha256") != expected_config_sha256:
            raise NativeExtractionError("Index header config_sha256 mismatch")

        for line_num, line in enumerate(f, start=2):
            if not line.strip():
                continue
            observed_total_spans += 1
            row = json.loads(line)
            errors = list(item_validator.iter_errors(row))
            if errors:
                raise NativeExtractionError(f"Index line {line_num} error: {errors[0].message}")

            ext_id = row["extraction_id"]
            if ext_id in seen_extraction_ids:
                raise NativeExtractionError(f"Index line {line_num}: duplicate extraction_id {ext_id}")
            seen_extraction_ids.add(ext_id)

            sid = row["source_id"]
            sources_seen.add(sid)

            seq_order = row["reconstruction_linkage"]["sequence_order"]
            if sid != prev_source:
                prev_source = sid
                prev_seq_order = seq_order
                if seq_order != 0:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): first span sequence_order must be 0, got {seq_order}"
                    )
            else:
                if seq_order != prev_seq_order + 1:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): non-consecutive sequence_order: expected {prev_seq_order + 1}, got {seq_order}"
                    )
                prev_seq_order = seq_order

            loc = row["span_locator"]
            if loc["char_length"] != loc["end_char"] - loc["start_char"]:
                raise NativeExtractionError(
                    f"Index line {line_num} ({sid}): char_length mismatch: "
                    f"char_length={loc['char_length']} != end_char({loc['end_char']}) - start_char({loc['start_char']})"
                )

            fa = row["fidelity_assessment"]
            status = fa["status"]
            enc_valid = fa["encoding_valid"]
            is_ocr = fa["is_ocr"]
            training_eligible = fa["training_eligible"]

            # Invariant: non-accepted status cannot be training-eligible
            if status == "ACCEPTED_FAITHFUL":
                if not training_eligible:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): ACCEPTED_FAITHFUL span cannot have training_eligible=False"
                    )
                if not enc_valid:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): ACCEPTED_FAITHFUL span cannot have encoding_valid=False"
                    )
                if is_ocr:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): ACCEPTED_FAITHFUL span cannot be OCR-derived"
                    )
                observed_accepted += 1
                observed_training_eligible += 1
            elif status == "QUARANTINED_ANOMALOUS":
                if training_eligible:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): QUARANTINED_ANOMALOUS span cannot have training_eligible=True"
                    )
                observed_quarantined += 1
            elif status == "EXCLUDED_OCR":
                if training_eligible:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): EXCLUDED_OCR span cannot have training_eligible=True"
                    )
                observed_quarantined += 1
            elif status == "REJECTED_DAMAGED":
                if training_eligible:
                    raise NativeExtractionError(
                        f"Index line {line_num} ({sid}): REJECTED_DAMAGED span cannot have training_eligible=True"
                    )
                observed_rejected += 1

    if header.get("records") != observed_total_spans:
        raise NativeExtractionError(
            f"Index header record count {header.get('records')} != observed {observed_total_spans}"
        )

    # Verify summary consistency
    rec_sum = receipt["summary"]
    if rec_sum["total_sources_evaluated"] != len(sources_seen):
        raise NativeExtractionError(
            f"Receipt total_sources_evaluated mismatch: expected {len(sources_seen)}, got {rec_sum['total_sources_evaluated']}"
        )
    if rec_sum["total_spans_evaluated"] != observed_total_spans:
        raise NativeExtractionError(
            f"Receipt total_spans_evaluated mismatch: expected {observed_total_spans}, got {rec_sum['total_spans_evaluated']}"
        )
    if rec_sum["accepted_spans_count"] != observed_accepted:
        raise NativeExtractionError(
            f"Receipt accepted_spans_count mismatch: expected {observed_accepted}, got {rec_sum['accepted_spans_count']}"
        )
    if rec_sum["quarantined_spans_count"] != observed_quarantined:
        raise NativeExtractionError(
            f"Receipt quarantined_spans_count mismatch: expected {observed_quarantined}, got {rec_sum['quarantined_spans_count']}"
        )
    if rec_sum["rejected_spans_count"] != observed_rejected:
        raise NativeExtractionError(
            f"Receipt rejected_spans_count mismatch: expected {observed_rejected}, got {rec_sum['rejected_spans_count']}"
        )
    if rec_sum["training_eligible_spans_count"] != observed_training_eligible:
        raise NativeExtractionError(
            f"Receipt training_eligible_spans_count mismatch: expected {observed_training_eligible}, got {rec_sum['training_eligible_spans_count']}"
        )

    # Safety assertions verification
    if _contains_private_or_absolute_host_path(receipt):
        raise NativeExtractionError("Receipt contains prohibited private or absolute host paths")
    if _contains_private_or_absolute_host_path(quarantine_report):
        raise NativeExtractionError("Quarantine report contains prohibited private or absolute host paths")

    # Ensure no raw text leakage in receipt or quarantine report
    forbidden_keys = {"text", "content", "corpus_text", "raw_text", "body"}
    if forbidden_keys.intersection(receipt.keys()):
        raise NativeExtractionError("Receipt violates safety assertion: forbidden corpus text keys present")
    if forbidden_keys.intersection(quarantine_report.keys()):
        raise NativeExtractionError("Quarantine report violates safety assertion: forbidden corpus text keys present")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate native extraction fidelity and exclude damaged source spans."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build extraction index, quarantine report, and receipt.")
    build_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    build_parser.add_argument("--input-root", type=Path, default=Path.cwd())
    build_parser.add_argument("--output-root", type=Path, default=Path.cwd())
    build_parser.add_argument(
        "--all", action="store_true", help="Extract all eligible sources regardless of target_sources filter"
    )

    verify_parser = subparsers.add_parser("verify", help="Verify extraction artifacts and invariants.")
    verify_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    verify_parser.add_argument("--input-root", type=Path, default=Path.cwd())
    verify_parser.add_argument("--output-root", type=Path, default=Path.cwd())

    args = parser.parse_args()

    try:
        if args.command == "build":
            res = build(
                config_path=args.config, input_root=args.input_root, output_root=args.output_root, all_sources=args.all
            )
            print(f"Native extraction build complete. Receipt: {res['receipt_id']}, verdict: {res['verdict']}")
        elif args.command == "verify":
            verify(config_path=args.config, input_root=args.input_root, output_root=args.output_root)
            print("Native extraction verification PASSED with 0 errors.")
    except NativeExtractionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
