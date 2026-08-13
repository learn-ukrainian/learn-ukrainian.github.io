#!/usr/bin/env python3
"""Freeze source-attributed Spas reconstruction lines without semantic overclaiming.

The upstream layout queue contains 101 historic-script-dominant lines.  Eighty-
two are preceded in the complete published record by an explicit author cue
(``текст`` plus a reconstruction/shape phrase); nineteen are comparison or
layout lines without that evidence.  This module deterministically records the
first group as qualified *source-attributed reconstructions* and leaves the
second group unresolved.  It does not turn either group into semantic gold,
modern correction data, or Phase 4 training material.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    COLLECTION_ID,
    SOURCE_AUTHOR,
    SOURCE_PDF_SHA256,
    SOURCE_RECORD_URL,
    SOURCE_TITLE,
    SOURCE_YEAR,
    SpasCatalogMaterializationError,
    _inside_git_checkout,
    file_sha256,
)
from scripts.projects.open_model_data.phase3_spas_glyph_adapter import SpasGlyphAdapterError
from scripts.projects.open_model_data.phase3_spas_layout_candidates import (
    EXPECTED_DOMINANT_LINES,
    EXPECTED_DOMINANT_RECORDS,
    EXPECTED_TRIGGER_LINES,
    EXPECTED_TRIGGER_RECORDS,
    EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP,
    EXPECTED_UNRESOLVED_LINES,
    EXPECTED_UNRESOLVED_RECORDS,
    SHAPE_CUES,
    TEXT_CUE_RE,
    SpasLayoutCandidateError,
    validate_existing_layout_candidates,
)
from scripts.projects.open_model_data.phase3_spas_layout_candidates import (
    OUTPUT_FILENAME as LAYOUT_OUTPUT_FILENAME,
)
from scripts.projects.open_model_data.phase3_spas_layout_candidates import (
    RECEIPT_FILENAME as LAYOUT_RECEIPT_FILENAME,
)

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_spas_source_attribution_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_spas_source_attribution_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_spas_source_attribution_v1"
OUTPUT_FILENAME = "spas-na-berestovi-source-attribution-v1.jsonl.gz"
RECEIPT_FILENAME = "source-attribution-receipt-v1.json"

EXPECTED_LAYOUT_OUTPUT_SHA256 = "661a8f247ecb5f0a6413c53346e72a8255a63e51fbe7b47ef1d2d10b89bd90d6"
EXPECTED_LAYOUT_RECEIPT_FILE_SHA256 = "aa8a67b32c478a309826a08c94679a45d31e5cfa558fa4e977bf2959a034c3d4"
EXPECTED_LAYOUT_RECEIPT_SHA256 = "5d2ff83247101de7d7de26f61d17a1d34fcd20c24ead14e5f7b0a515de2482d1"
EXPECTED_LAYOUT_IMPLEMENTATION_SHA256 = "2bc7a49dfea7a7cb9118321f4a8010d54b34f1aded3031a400ae84e5a0c4a034"
EXPECTED_LAYOUT_RECEIPT_SCHEMA_SHA256 = "26ad006a4e654f94e18779f8ae21900630660611490ef638ff76f8e490cfc140"
EXPECTED_INPUT_RECORDS = 477

TRIGGER_CLASSIFICATION = "author_reconstruction_trigger_candidate"
FALLBACK_CLASSIFICATION = "dominant_historic_script_unresolved"
ATTRIBUTED_DISPOSITION = "qualified_source_attributed"
UNRESOLVED_DISPOSITION = "unresolved"


class SpasSourceAttributionError(ValueError):
    """An attribution, denominator, identity, or custody invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SpasSourceAttributionError(message)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasSourceAttributionError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be an object")
    return value


def _load_jsonl_gzip(path: Path, *, description: str) -> list[dict[str, Any]]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpasSourceAttributionError(f"cannot read {description}: {exc}") from exc
    require(all(isinstance(row, dict) for row in rows), f"{description} rows must be objects")
    return rows


def _validate_source_candidate(record: Mapping[str, Any], candidate: Mapping[str, Any]) -> None:
    raw_start, raw_end = candidate["raw_start_char"], candidate["raw_end_char"]
    normalized_start, normalized_end = candidate["normalized_start_char"], candidate["normalized_end_char"]
    require(0 <= raw_start < raw_end <= len(record["raw_context"]), "candidate raw offset drift")
    require(
        0 <= normalized_start < normalized_end <= len(record["normalized_context"]),
        "candidate normalized offset drift",
    )
    require(record["raw_context"][raw_start:raw_end] == candidate["raw_text"], "candidate raw text drift")
    require(
        record["normalized_context"][normalized_start:normalized_end] == candidate["normalized_text"],
        "candidate normalized text drift",
    )
    require(candidate["raw_text_sha256"] == _sha256_text(candidate["raw_text"]), "candidate raw hash drift")
    require(
        candidate["normalized_text_sha256"] == _sha256_text(candidate["normalized_text"]),
        "candidate normalized hash drift",
    )

    context_start = candidate["trigger_context_start_char"]
    context_end = candidate["trigger_context_end_char"]
    require(0 <= context_start <= context_end == raw_start, "candidate trigger context offset drift")
    context = record["raw_context"][context_start:context_end]
    require(candidate["trigger_context_sha256"] == _sha256_text(context), "candidate trigger context hash drift")
    folded_context = context.casefold()
    expected_text_cue = TEXT_CUE_RE.search(folded_context) is not None
    expected_shape_cues = [cue for cue in SHAPE_CUES if cue in folded_context]
    require(candidate["text_cue_present"] is expected_text_cue, "candidate text cue drift")
    require(candidate["matched_shape_cues"] == expected_shape_cues, "candidate shape cue drift")
    expected_classification = (
        TRIGGER_CLASSIFICATION if expected_text_cue and expected_shape_cues else FALLBACK_CLASSIFICATION
    )
    require(candidate["classification"] == expected_classification, "candidate source classification drift")
    require(candidate["classification_is_semantic_gold"] is False, "upstream classification cannot be gold")
    require(candidate["training_eligible"] is False, "upstream candidate cannot authorize training")


def _disposition(candidate: Mapping[str, Any]) -> dict[str, Any]:
    attributed = candidate["classification"] == TRIGGER_CLASSIFICATION
    require(
        attributed or candidate["classification"] == FALLBACK_CLASSIFICATION,
        "unknown upstream candidate classification",
    )
    if attributed:
        require(candidate["text_cue_present"] is True, "attributed line lacks the required text cue")
        require(bool(candidate["matched_shape_cues"]), "attributed line lacks a reconstruction shape cue")
    else:
        require(
            candidate["text_cue_present"] is False or not candidate["matched_shape_cues"],
            "unresolved line unexpectedly satisfies the complete attribution cue",
        )
    return {
        "candidate_id": candidate["candidate_id"],
        "source_classification": candidate["classification"],
        "disposition": ATTRIBUTED_DISPOSITION if attributed else UNRESOLVED_DISPOSITION,
        "layer": "source_attributed_inscription_reconstruction" if attributed else "unresolved_historic_script_line",
        "authority": "published_edition_author" if attributed else "unresolved",
        "pdf_page_number": candidate["pdf_page_number"],
        "page_start_char": candidate["page_start_char"],
        "page_end_char": candidate["page_end_char"],
        "raw_start_char": candidate["raw_start_char"],
        "raw_end_char": candidate["raw_end_char"],
        "raw_text": candidate["raw_text"],
        "raw_text_sha256": candidate["raw_text_sha256"],
        "normalized_start_char": candidate["normalized_start_char"],
        "normalized_end_char": candidate["normalized_end_char"],
        "normalized_text": candidate["normalized_text"],
        "normalized_text_sha256": candidate["normalized_text_sha256"],
        "source_attribution_evidence": {
            "source_author": SOURCE_AUTHOR,
            "source_title": SOURCE_TITLE,
            "source_year": SOURCE_YEAR,
            "source_record_url": SOURCE_RECORD_URL,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "trigger_context_start_char": candidate["trigger_context_start_char"],
            "trigger_context_end_char": candidate["trigger_context_end_char"],
            "trigger_context_sha256": candidate["trigger_context_sha256"],
            "whole_word_text_cue_present": candidate["text_cue_present"],
            "matched_shape_cues": candidate["matched_shape_cues"],
            "evidence_status": "explicit_author_reconstruction_cue" if attributed else "insufficient_for_attribution",
        },
        "semantic_gold": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "phase4_authorized": False,
    }


def build_source_attribution_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Build one complete-context record for an upstream candidate-bearing row."""
    candidates = record["historic_script_dominant_line_candidates"]
    require(isinstance(candidates, list) and candidates, "source-attribution row requires candidate lines")
    require(record["collection_id"] == COLLECTION_ID, "upstream collection drift")
    require(record["source_pdf_sha256"] == SOURCE_PDF_SHA256, "upstream source PDF drift")
    require(record["raw_context_sha256"] == _sha256_text(record["raw_context"]), "upstream raw context hash drift")
    require(
        record["normalized_context_sha256"] == _sha256_text(record["normalized_context"]),
        "upstream normalized context hash drift",
    )
    for field in (
        "commentary_and_inscription_layers_separated",
        "semantic_gold",
        "training_eligible",
        "modern_correction_eligible",
        "provider_calls",
        "phase4_authorized",
    ):
        require(record[field] is False, f"unsafe upstream flag: {field}")
    for candidate in candidates:
        _validate_source_candidate(record, candidate)
    dispositions = [_disposition(candidate) for candidate in candidates]
    attributed = sum(item["disposition"] == ATTRIBUTED_DISPOSITION for item in dispositions)
    unresolved = len(dispositions) - attributed
    return {
        "schema_version": "phase3_spas_source_attribution_record_v1",
        "record_id": f"{record['source_record_id']}:source-attribution-v1",
        "source_candidate_record_id": record["record_id"],
        "source_record_id": record["source_record_id"],
        "collection_id": COLLECTION_ID,
        "graffito_number": record["graffito_number"],
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "upstream_layout_output_sha256": EXPECTED_LAYOUT_OUTPUT_SHA256,
        "raw_context": record["raw_context"],
        "raw_context_sha256": record["raw_context_sha256"],
        "normalized_context": record["normalized_context"],
        "normalized_context_sha256": record["normalized_context_sha256"],
        "candidate_dispositions": dispositions,
        "denominator": {
            "candidate_lines": len(dispositions),
            "source_attributed_lines": attributed,
            "unresolved_lines": unresolved,
        },
        "candidate_denominator_fully_dispositioned": True,
        "explicit_source_attribution_pass_complete": True,
        "candidate_line_disposition_complete": True,
        "qualified_historical_semantic_review_complete": False,
        "semantic_gold": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "provider_calls": False,
        "phase4_authorized": False,
    }


def _observed_denominator(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    attributed_records: set[int] = set()
    unresolved_records: set[int] = set()
    attributed_lines = 0
    unresolved_lines = 0
    for record in records:
        for disposition in record["candidate_dispositions"]:
            if disposition["disposition"] == ATTRIBUTED_DISPOSITION:
                attributed_lines += 1
                attributed_records.add(record["graffito_number"])
            else:
                unresolved_lines += 1
                unresolved_records.add(record["graffito_number"])
    return {
        "input_records": EXPECTED_INPUT_RECORDS,
        "candidate_records": len(records),
        "candidate_lines": attributed_lines + unresolved_lines,
        "source_attributed_lines": attributed_lines,
        "source_attributed_records": len(attributed_records),
        "unresolved_lines": unresolved_lines,
        "unresolved_records": len(unresolved_records),
        "attributed_unresolved_record_overlap": len(attributed_records & unresolved_records),
    }


def _expected_denominator() -> dict[str, int]:
    return {
        "input_records": EXPECTED_INPUT_RECORDS,
        "candidate_records": EXPECTED_DOMINANT_RECORDS,
        "candidate_lines": EXPECTED_DOMINANT_LINES,
        "source_attributed_lines": EXPECTED_TRIGGER_LINES,
        "source_attributed_records": EXPECTED_TRIGGER_RECORDS,
        "unresolved_lines": EXPECTED_UNRESOLVED_LINES,
        "unresolved_records": EXPECTED_UNRESOLVED_RECORDS,
        "attributed_unresolved_record_overlap": EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP,
    }


def _write_jsonl_gzip(path: Path, records: Sequence[Mapping[str, Any]]) -> tuple[int, int, str]:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with (
            temporary.open("wb") as raw_handle,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
        ):
            for record in records:
                gzip_handle.write(canonical_json(record).encode("utf-8") + b"\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(records), path.stat().st_size, file_sha256(path)


def _receipt_with_hash(body: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(body)
    receipt["receipt_sha256"] = sha256_value(body)
    return receipt


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasSourceAttributionError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise SpasSourceAttributionError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    denominator = receipt["denominator"]
    require(
        denominator["source_attributed_lines"] + denominator["unresolved_lines"] == denominator["candidate_lines"],
        "receipt candidate disposition partition drift",
    )
    require(denominator["candidate_records"] == receipt["output"]["records"], "receipt output denominator drift")
    require(
        receipt["residuals"]["unresolved_candidate_lines"] == denominator["unresolved_lines"],
        "receipt unresolved denominator drift",
    )


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _validate_receipt(receipt)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _remove_staging_dir(path: Path) -> None:
    for filename in (OUTPUT_FILENAME, RECEIPT_FILENAME):
        candidate = path / filename
        if candidate.is_file() or candidate.is_symlink():
            candidate.unlink()
    if path.exists():
        path.rmdir()


def _load_and_rebind_layout(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    adapter_output_dir: Path,
    mapping_evidence_path: Path,
    layout_candidate_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    upstream = validate_existing_layout_candidates(
        pdf_path=pdf_path,
        raw_catalog_dir=raw_catalog_dir,
        adapter_output_dir=adapter_output_dir,
        mapping_evidence_path=mapping_evidence_path,
        private_output_dir=layout_candidate_dir,
    )
    require(upstream["records"] == EXPECTED_INPUT_RECORDS, "upstream layout record denominator drift")
    require(upstream["candidate_lines"] == EXPECTED_DOMINANT_LINES, "upstream layout candidate denominator drift")
    require(upstream["trigger_lines"] == EXPECTED_TRIGGER_LINES, "upstream trigger denominator drift")
    require(upstream["unresolved_lines"] == EXPECTED_UNRESOLVED_LINES, "upstream unresolved denominator drift")
    require(upstream["output_sha256"] == EXPECTED_LAYOUT_OUTPUT_SHA256, "upstream layout output identity drift")
    require(upstream["receipt_sha256"] == EXPECTED_LAYOUT_RECEIPT_SHA256, "upstream layout receipt identity drift")
    require(upstream["training_eligible"] is False, "upstream layout cannot authorize training")
    require(upstream["phase4_authorized"] is False, "upstream layout cannot authorize Phase 4")

    output_path = layout_candidate_dir / LAYOUT_OUTPUT_FILENAME
    receipt_path = layout_candidate_dir / LAYOUT_RECEIPT_FILENAME
    require(file_sha256(output_path) == EXPECTED_LAYOUT_OUTPUT_SHA256, "layout output SHA-256 drift")
    require(file_sha256(receipt_path) == EXPECTED_LAYOUT_RECEIPT_FILE_SHA256, "layout receipt file identity drift")
    receipt = _load_json_object(receipt_path, description="layout candidate receipt")
    require(
        file_sha256(receipt_path) == EXPECTED_LAYOUT_RECEIPT_FILE_SHA256,
        "layout receipt changed while loading",
    )
    require(receipt["receipt_sha256"] == EXPECTED_LAYOUT_RECEIPT_SHA256, "layout receipt self-identity drift")
    require(
        receipt["inputs"]["implementation_sha256"] == EXPECTED_LAYOUT_IMPLEMENTATION_SHA256,
        "layout implementation identity drift",
    )
    require(
        receipt["inputs"]["receipt_schema_sha256"] == EXPECTED_LAYOUT_RECEIPT_SCHEMA_SHA256,
        "layout receipt schema identity drift",
    )
    rows = _load_jsonl_gzip(output_path, description="layout candidate JSONL")
    require(file_sha256(output_path) == EXPECTED_LAYOUT_OUTPUT_SHA256, "layout output changed while loading")
    require(len(rows) == EXPECTED_INPUT_RECORDS, "layout JSONL record denominator drift")
    require(
        [row.get("graffito_number") for row in rows] == list(range(1, EXPECTED_INPUT_RECORDS + 1)),
        "layout JSONL record sequence drift",
    )
    return rows, receipt


def materialize_source_attribution(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    adapter_output_dir: Path,
    mapping_evidence_path: Path,
    layout_candidate_dir: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Write an immutable private attribution artifact and text-free receipt."""
    resolved_output = private_output_dir.resolve()
    require(not _inside_git_checkout(resolved_output), "private text output cannot be inside a Git checkout")
    require(not private_output_dir.exists(), "immutable private output directory already exists")
    require(private_output_dir.parent.is_dir(), "private output parent directory does not exist")
    require(not private_output_dir.parent.is_symlink(), "private output parent directory cannot be a symbolic link")

    layout_rows, _layout_receipt = _load_and_rebind_layout(
        pdf_path=pdf_path,
        raw_catalog_dir=raw_catalog_dir,
        adapter_output_dir=adapter_output_dir,
        mapping_evidence_path=mapping_evidence_path,
        layout_candidate_dir=layout_candidate_dir,
    )
    output_records = [
        build_source_attribution_record(row) for row in layout_rows if row["historic_script_dominant_line_candidates"]
    ]
    denominator = _observed_denominator(output_records)
    require(denominator == _expected_denominator(), "source attribution denominator drift")
    identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_context_sha256": record["raw_context_sha256"],
            "normalized_context_sha256": record["normalized_context_sha256"],
            "candidate_lines": record["denominator"]["candidate_lines"],
            "source_attributed_lines": record["denominator"]["source_attributed_lines"],
            "unresolved_lines": record["denominator"]["unresolved_lines"],
        }
        for record in output_records
    ]

    staging_dir = Path(tempfile.mkdtemp(prefix=f".{private_output_dir.name}.staging-", dir=private_output_dir.parent))
    try:
        output_path = staging_dir / OUTPUT_FILENAME
        output_count, output_bytes, output_sha256 = _write_jsonl_gzip(output_path, output_records)
        body: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "mode": "qualified_source_attribution_not_semantic_gold",
            "text_free": True,
            "inputs": {
                "collection_id": COLLECTION_ID,
                "source_pdf_sha256": SOURCE_PDF_SHA256,
                "layout_output_sha256": EXPECTED_LAYOUT_OUTPUT_SHA256,
                "layout_receipt_file_sha256": EXPECTED_LAYOUT_RECEIPT_FILE_SHA256,
                "layout_receipt_sha256": EXPECTED_LAYOUT_RECEIPT_SHA256,
                "layout_implementation_sha256": EXPECTED_LAYOUT_IMPLEMENTATION_SHA256,
                "layout_receipt_schema_sha256": EXPECTED_LAYOUT_RECEIPT_SCHEMA_SHA256,
                "implementation_sha256": file_sha256(Path(__file__)),
                "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
            },
            "source_authority": {
                "author": SOURCE_AUTHOR,
                "title": SOURCE_TITLE,
                "year": SOURCE_YEAR,
                "source_record_url": SOURCE_RECORD_URL,
                "authority_scope": "published_author_reconstruction_only",
            },
            "attribution_contract": {
                "input_trigger_classification": TRIGGER_CLASSIFICATION,
                "attributed_disposition": ATTRIBUTED_DISPOSITION,
                "fallback_classification": FALLBACK_CLASSIFICATION,
                "fallback_disposition": UNRESOLVED_DISPOSITION,
                "requires_whole_word_text_cue": True,
                "requires_shape_cue": True,
                "source_attribution_is_semantic_gold": False,
            },
            "denominator": denominator,
            "output": {
                "filename": OUTPUT_FILENAME,
                "records": output_count,
                "bytes": output_bytes,
                "sha256": output_sha256,
                "record_identity_manifest_sha256": sha256_value(identity_manifest),
            },
            "rights_and_scope": {
                "inherits_upstream_accepted_operational_risk": True,
                "private_research_artifact_only": True,
                "attribution_and_field_level_removal_preserved": True,
                "binary_media_reuse_authorized": False,
                "full_publication_training_export_authorized": False,
                "adapt_on_substantiated_rights_notice": True,
            },
            "safeguards": {
                "complete_record_context_preserved": True,
                "source_offsets_preserved": True,
                "candidate_denominator_fully_dispositioned": True,
                "explicit_source_attribution_pass_complete": True,
                "qualified_historical_semantic_review_complete": False,
                "full_catalog_commentary_inscription_separation_complete": False,
                "semantic_gold": False,
                "training_eligible": False,
                "modern_correction_eligible": False,
                "provider_calls": False,
                "phase4_authorized": False,
            },
            "residuals": {
                "unresolved_candidate_lines": denominator["unresolved_lines"],
                "inline_or_nondominant_font_spans_remain_context_only": True,
                "semantic_labels_pending": True,
                "full_catalog_layer_separation_pending": True,
                "lavra_cave_corpus_gap_closed": False,
            },
        }
        receipt = _receipt_with_hash(body)
        _write_receipt(staging_dir / RECEIPT_FILENAME, receipt)
        require(not private_output_dir.exists(), "immutable private output directory appeared during publication")
        os.replace(staging_dir, private_output_dir)
        return receipt
    finally:
        _remove_staging_dir(staging_dir)


def _validate_attribution_record(record: Mapping[str, Any]) -> None:
    require(record["schema_version"] == "phase3_spas_source_attribution_record_v1", "attribution row schema drift")
    require(record["collection_id"] == COLLECTION_ID, "attribution row collection drift")
    require(record["source_pdf_sha256"] == SOURCE_PDF_SHA256, "attribution row PDF drift")
    require(
        record["upstream_layout_output_sha256"] == EXPECTED_LAYOUT_OUTPUT_SHA256,
        "attribution row upstream identity drift",
    )
    require(record["raw_context_sha256"] == _sha256_text(record["raw_context"]), "attribution raw hash drift")
    require(
        record["normalized_context_sha256"] == _sha256_text(record["normalized_context"]),
        "attribution normalized hash drift",
    )
    require(record["candidate_dispositions"], "attribution row lacks dispositions")
    for disposition in record["candidate_dispositions"]:
        raw_start, raw_end = disposition["raw_start_char"], disposition["raw_end_char"]
        normalized_start, normalized_end = disposition["normalized_start_char"], disposition["normalized_end_char"]
        require(record["raw_context"][raw_start:raw_end] == disposition["raw_text"], "disposition raw offset drift")
        require(
            record["normalized_context"][normalized_start:normalized_end] == disposition["normalized_text"],
            "disposition normalized offset drift",
        )
        require(disposition["raw_text_sha256"] == _sha256_text(disposition["raw_text"]), "disposition raw hash drift")
        require(
            disposition["normalized_text_sha256"] == _sha256_text(disposition["normalized_text"]),
            "disposition normalized hash drift",
        )
        evidence = disposition["source_attribution_evidence"]
        require(evidence["source_author"] == SOURCE_AUTHOR, "disposition source author drift")
        require(evidence["source_title"] == SOURCE_TITLE, "disposition source title drift")
        context_start = evidence["trigger_context_start_char"]
        context_end = evidence["trigger_context_end_char"]
        require(0 <= context_start <= context_end == raw_start, "disposition trigger context offset drift")
        context = record["raw_context"][context_start:context_end]
        require(evidence["trigger_context_sha256"] == _sha256_text(context), "disposition trigger context hash drift")
        folded_context = context.casefold()
        expected_text_cue = TEXT_CUE_RE.search(folded_context) is not None
        expected_shape_cues = [cue for cue in SHAPE_CUES if cue in folded_context]
        require(evidence["whole_word_text_cue_present"] is expected_text_cue, "disposition text cue drift")
        require(evidence["matched_shape_cues"] == expected_shape_cues, "disposition shape cue drift")
        if disposition["disposition"] == ATTRIBUTED_DISPOSITION:
            require(disposition["source_classification"] == TRIGGER_CLASSIFICATION, "attributed classification drift")
            require(evidence["whole_word_text_cue_present"] is True, "attributed disposition lacks text cue")
            require(bool(evidence["matched_shape_cues"]), "attributed disposition lacks shape cue")
            require(evidence["evidence_status"] == "explicit_author_reconstruction_cue", "attributed evidence drift")
        else:
            require(disposition["source_classification"] == FALLBACK_CLASSIFICATION, "unresolved classification drift")
            require(evidence["evidence_status"] == "insufficient_for_attribution", "unresolved evidence drift")
        for field in ("semantic_gold", "training_eligible", "modern_correction_eligible", "phase4_authorized"):
            require(disposition[field] is False, f"unsafe disposition flag: {field}")
    require(
        record["denominator"]["candidate_lines"] == len(record["candidate_dispositions"]),
        "attribution row candidate denominator drift",
    )
    require(
        record["denominator"]["source_attributed_lines"] + record["denominator"]["unresolved_lines"]
        == record["denominator"]["candidate_lines"],
        "attribution row partition drift",
    )
    require(record["candidate_line_disposition_complete"] is True, "candidate-line disposition is incomplete")
    require(
        record["explicit_source_attribution_pass_complete"] is True,
        "explicit source-attribution pass is incomplete",
    )
    for field in (
        "qualified_historical_semantic_review_complete",
        "semantic_gold",
        "training_eligible",
        "modern_correction_eligible",
        "provider_calls",
        "phase4_authorized",
    ):
        require(record[field] is False, f"unsafe attribution row flag: {field}")


def validate_existing_source_attribution(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    adapter_output_dir: Path,
    mapping_evidence_path: Path,
    layout_candidate_dir: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Rebind an existing attribution artifact to current source bytes and replay it."""
    receipt_path = private_output_dir / RECEIPT_FILENAME
    output_path = private_output_dir / OUTPUT_FILENAME
    receipt = _load_json_object(receipt_path, description="source attribution receipt")
    _validate_receipt(receipt)
    exact_inputs = {
        "collection_id": COLLECTION_ID,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "layout_output_sha256": EXPECTED_LAYOUT_OUTPUT_SHA256,
        "layout_receipt_file_sha256": EXPECTED_LAYOUT_RECEIPT_FILE_SHA256,
        "layout_receipt_sha256": EXPECTED_LAYOUT_RECEIPT_SHA256,
        "layout_implementation_sha256": EXPECTED_LAYOUT_IMPLEMENTATION_SHA256,
        "layout_receipt_schema_sha256": EXPECTED_LAYOUT_RECEIPT_SCHEMA_SHA256,
        "implementation_sha256": file_sha256(Path(__file__)),
        "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
    }
    for key, expected in exact_inputs.items():
        require(receipt["inputs"][key] == expected, f"receipt input identity drift: {key}")
    require(receipt["denominator"] == _expected_denominator(), "receipt exact denominator drift")

    layout_rows, _layout_receipt = _load_and_rebind_layout(
        pdf_path=pdf_path,
        raw_catalog_dir=raw_catalog_dir,
        adapter_output_dir=adapter_output_dir,
        mapping_evidence_path=mapping_evidence_path,
        layout_candidate_dir=layout_candidate_dir,
    )
    require(output_path.is_file() and not output_path.is_symlink(), "source attribution output is missing or unsafe")
    require(file_sha256(output_path) == receipt["output"]["sha256"], "source attribution output SHA-256 drift")
    require(output_path.stat().st_size == receipt["output"]["bytes"], "source attribution output byte count drift")
    output_records = _load_jsonl_gzip(output_path, description="source attribution JSONL")
    expected_records = [
        build_source_attribution_record(row) for row in layout_rows if row["historic_script_dominant_line_candidates"]
    ]
    require(output_records == expected_records, "source attribution output does not equal deterministic replay")
    for record in output_records:
        _validate_attribution_record(record)
    require(_observed_denominator(output_records) == _expected_denominator(), "output attribution denominator drift")
    identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_context_sha256": record["raw_context_sha256"],
            "normalized_context_sha256": record["normalized_context_sha256"],
            "candidate_lines": record["denominator"]["candidate_lines"],
            "source_attributed_lines": record["denominator"]["source_attributed_lines"],
            "unresolved_lines": record["denominator"]["unresolved_lines"],
        }
        for record in output_records
    ]
    require(
        sha256_value(identity_manifest) == receipt["output"]["record_identity_manifest_sha256"],
        "source attribution identity manifest drift",
    )
    return {
        "ok": True,
        "records": len(output_records),
        "candidate_lines": receipt["denominator"]["candidate_lines"],
        "source_attributed_lines": receipt["denominator"]["source_attributed_lines"],
        "unresolved_lines": receipt["denominator"]["unresolved_lines"],
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "semantic_gold": False,
        "training_eligible": False,
        "phase4_authorized": False,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--raw-catalog-dir", type=Path, required=True)
    parser.add_argument("--adapter-output-dir", type=Path, required=True)
    parser.add_argument("--mapping-evidence", type=Path, required=True)
    parser.add_argument("--layout-candidate-dir", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument("--validate-existing", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.validate_existing:
            result = validate_existing_source_attribution(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                adapter_output_dir=args.adapter_output_dir,
                mapping_evidence_path=args.mapping_evidence,
                layout_candidate_dir=args.layout_candidate_dir,
                private_output_dir=args.private_output_dir,
            )
            status = "source_attribution_validated"
        else:
            receipt = materialize_source_attribution(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                adapter_output_dir=args.adapter_output_dir,
                mapping_evidence_path=args.mapping_evidence,
                layout_candidate_dir=args.layout_candidate_dir,
                private_output_dir=args.private_output_dir,
            )
            result = {
                "records": receipt["output"]["records"],
                "candidate_lines": receipt["denominator"]["candidate_lines"],
                "source_attributed_lines": receipt["denominator"]["source_attributed_lines"],
                "unresolved_lines": receipt["denominator"]["unresolved_lines"],
                "output_sha256": receipt["output"]["sha256"],
                "receipt_sha256": receipt["receipt_sha256"],
                "semantic_gold": False,
                "training_eligible": False,
                "phase4_authorized": False,
            }
            status = "source_attribution_materialized"
    except (
        SpasSourceAttributionError,
        SpasLayoutCandidateError,
        SpasCatalogMaterializationError,
        SpasGlyphAdapterError,
    ) as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(canonical_json({"status": status, **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
