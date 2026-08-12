#!/usr/bin/env python3
"""Build a protected review queue for Spas transcription-layer separation.

The canonical PDF's native text stream retains an embedded Bukyvede font. This
module replays that stream with pypdf's font visitor, binds every font-tagged
character to the existing raw and Unicode-adapter records, and emits exact
font spans plus historic-script-dominant line candidates.

The lexical cue is intentionally only a routing signal: a dominant line is
classified as an ``author_reconstruction_trigger_candidate`` when the prior
220 code points in the same complete record contain ``текст`` and a frozen
shape/reconstruction cue.  No candidate becomes semantic gold or training
data without qualified historical review of the complete record context.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pypdf import PdfReader

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    CATALOG_PDF_PAGE_END,
    CATALOG_PDF_PAGE_START,
    COLLECTION_ID,
    EXPECTED_CATALOG_RECORDS,
    SOURCE_PDF_SHA256,
    SpasCatalogMaterializationError,
    _inside_git_checkout,
    file_sha256,
)
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    OUTPUT_FILENAME as RAW_OUTPUT_FILENAME,
)
from scripts.projects.open_model_data.phase3_spas_glyph_adapter import (
    EXPECTED_MAPPING_EVIDENCE_SHA256,
    EXPECTED_RAW_OUTPUT_SHA256,
    EXPECTED_RAW_RECEIPT_FILE_SHA256,
    EXPECTED_RAW_RECEIPT_SHA256,
    SpasGlyphAdapterError,
    validate_existing_glyph_adapter,
)
from scripts.projects.open_model_data.phase3_spas_glyph_adapter import (
    OUTPUT_FILENAME as ADAPTER_OUTPUT_FILENAME,
)
from scripts.projects.open_model_data.phase3_spas_glyph_adapter import (
    RECEIPT_FILENAME as ADAPTER_RECEIPT_FILENAME,
)

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_spas_layout_candidate_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_spas_layout_candidate_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_spas_layout_candidates_v1"
OUTPUT_FILENAME = "spas-na-berestovi-layout-candidates-v1.jsonl.gz"
RECEIPT_FILENAME = "layout-candidate-receipt-v1.json"
BUKYVEDE_FONT_BASE_NAME = "/GATIPV+Bukyvede"
CONTEXT_WINDOW_CODEPOINTS = 220
SHAPE_CUES = ("таким чином", "вигляд", "реконструк", "віднов")
TEXT_CUE_RE = re.compile(r"(?<!\w)текст(?!\w)")

EXPECTED_ADAPTER_OUTPUT_SHA256 = "3a828f0a4ca57e5f44a4bf72536ed6de8597f6633e2987bab663cacc55dbf6d4"
EXPECTED_ADAPTER_RECEIPT_FILE_SHA256 = "8278b133026ded0b197e8518167730189963a9a781d91e1ac7751eb73b3ca372"
EXPECTED_ADAPTER_RECEIPT_SHA256 = "e494cd3030b74d40574a03498ca6089d23a6827e9e8283b5df0d34965c02adf8"

EXPECTED_RECORDS_WITH_BUKYVEDE = 302
EXPECTED_RECORDS_WITHOUT_BUKYVEDE = 175
EXPECTED_BUKYVEDE_RUNS = 883
EXPECTED_BUKYVEDE_CHARACTERS = 5393
EXPECTED_BUKYVEDE_NONSPACE_CHARACTERS = 4896
EXPECTED_LINES_WITH_BUKYVEDE = 637
EXPECTED_DOMINANT_LINES = 101
EXPECTED_DOMINANT_RECORDS = 90
EXPECTED_TRIGGER_LINES = 82
EXPECTED_TRIGGER_RECORDS = 81
EXPECTED_UNRESOLVED_LINES = 19
EXPECTED_UNRESOLVED_RECORDS = 12
EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP = 3


class SpasLayoutCandidateError(ValueError):
    """A source-layout, offset, denominator, or custody invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SpasLayoutCandidateError(message)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasLayoutCandidateError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be an object")
    return value


def _load_jsonl_gzip(path: Path, *, description: str) -> list[dict[str, Any]]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpasLayoutCandidateError(f"cannot read {description}: {exc}") from exc
    require(all(isinstance(row, dict) for row in rows), f"{description} rows must be objects")
    return rows


def extract_font_layout_pages(
    pdf_path: Path,
    *,
    page_start: int = CATALOG_PDF_PAGE_START,
    page_end: int = CATALOG_PDF_PAGE_END,
) -> dict[int, dict[str, Any]]:
    """Return exact pypdf native page text plus one font label per code point."""
    require(pdf_path.is_file() and not pdf_path.is_symlink(), "source PDF is missing or unsafe")
    require(file_sha256(pdf_path) == SOURCE_PDF_SHA256, "source PDF SHA-256 drift")
    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:
        raise SpasLayoutCandidateError(f"cannot open source PDF: {exc}") from exc
    require(not reader.is_encrypted, "encrypted source PDF is not supported")
    require(1 <= page_start <= page_end <= len(reader.pages), "catalogue page range is invalid")

    layouts: dict[int, dict[str, Any]] = {}
    for page_number in range(page_start, page_end + 1):
        font_tags: list[str] = []

        def visitor(
            text: str,
            _cm: Sequence[float],
            _tm: Sequence[float],
            font_dictionary: Mapping[str, Any] | None,
            _font_size: float,
            _font_tags: list[str] = font_tags,
        ) -> None:
            base_font = str(font_dictionary.get("/BaseFont")) if font_dictionary else "NONE"
            _font_tags.extend([base_font] * len(text))

        try:
            text = reader.pages[page_number - 1].extract_text(visitor_text=visitor) or ""
        except Exception as exc:
            raise SpasLayoutCandidateError(f"font-layout extraction failed on PDF page {page_number}: {exc}") from exc
        require(text != "", f"catalogue PDF page {page_number} has no native text")
        require("\ufffd" not in text, f"catalogue PDF page {page_number} contains replacement characters")
        require(len(text) == len(font_tags), f"font tag length drift on PDF page {page_number}")
        layouts[page_number] = {
            "text": text,
            "text_sha256": _sha256_text(text),
            "font_tags": font_tags,
        }
    require(file_sha256(pdf_path) == SOURCE_PDF_SHA256, "source PDF changed while extracting layout")
    return layouts


def _raw_boundary_to_normalized(record: Mapping[str, Any], raw_offset: int) -> int:
    raw_text = record["raw_source_text"]
    normalized_text = record["normalized_text"]
    require(isinstance(raw_offset, int) and 0 <= raw_offset <= len(raw_text), "raw boundary is out of range")
    delta = 0
    for event in record["mapping_events"]:
        raw_start = event["raw_start_char"]
        raw_end = event["raw_end_char"]
        normalized_start = event["normalized_start_char"]
        normalized_end = event["normalized_end_char"]
        require(normalized_start == raw_start - delta, "adapter event start relationship drift")
        if raw_offset < raw_start:
            return raw_offset - delta
        if raw_offset == raw_start:
            return normalized_start
        require(not raw_start < raw_offset < raw_end, "candidate boundary splits a glyph mapping event")
        if raw_offset == raw_end:
            return normalized_end
        delta += (raw_end - raw_start) - (normalized_end - normalized_start)
    normalized_offset = raw_offset - delta
    require(0 <= normalized_offset <= len(normalized_text), "normalized boundary is out of range")
    return normalized_offset


def _record_layout(
    raw_record: Mapping[str, Any],
    normalized_record: Mapping[str, Any],
    page_layouts: Mapping[int, Mapping[str, Any]],
) -> tuple[str, list[str], list[tuple[int, int] | None]]:
    raw_text = raw_record["source_text"]
    require(normalized_record["raw_source_text"] == raw_text, "adapter/raw record text drift")
    require(normalized_record["source_record_id"] == raw_record["record_id"], "adapter/raw record id drift")
    parts: list[str] = []
    tags: list[str] = []
    page_refs: list[tuple[int, int] | None] = []
    for index, fragment in enumerate(raw_record["source_page_fragments"]):
        if index:
            parts.append("\n")
            tags.append("NONE")
            page_refs.append(None)
        page_number = fragment["pdf_page_number"]
        require(page_number in page_layouts, "record refers to an unknown layout page")
        page_text = page_layouts[page_number]["text"]
        page_tags = page_layouts[page_number]["font_tags"]
        start, end = fragment["start_char"], fragment["end_char"]
        require(0 <= start < end <= len(page_text), "record page fragment offsets drift")
        fragment_text = page_text[start:end]
        require(fragment["text_sha256"] == _sha256_text(fragment_text), "record page fragment hash drift")
        parts.append(fragment_text)
        tags.extend(page_tags[start:end])
        page_refs.extend((page_number, page_offset) for page_offset in range(start, end))
    reconstructed = "".join(parts)
    require(reconstructed == raw_text, "record layout does not reproduce raw source text")
    require(len(reconstructed) == len(tags) == len(page_refs), "record layout alignment drift")
    return reconstructed, tags, page_refs


def _font_spans(
    raw_text: str,
    normalized_record: Mapping[str, Any],
    tags: Sequence[str],
    page_refs: Sequence[tuple[int, int] | None],
) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    cursor = 0
    while cursor < len(tags):
        if tags[cursor] != BUKYVEDE_FONT_BASE_NAME:
            cursor += 1
            continue
        end = cursor + 1
        while end < len(tags) and tags[end] == BUKYVEDE_FONT_BASE_NAME:
            end += 1
        refs = page_refs[cursor:end]
        require(all(ref is not None for ref in refs), "Bukyvede font span crosses an inserted page separator")
        typed_refs = [ref for ref in refs if ref is not None]
        page_numbers = {ref[0] for ref in typed_refs}
        require(len(page_numbers) == 1, "Bukyvede font span crosses PDF pages")
        require(
            [ref[1] for ref in typed_refs] == list(range(typed_refs[0][1], typed_refs[-1][1] + 1)),
            "Bukyvede page offsets are not contiguous",
        )
        normalized_start = _raw_boundary_to_normalized(normalized_record, cursor)
        normalized_end = _raw_boundary_to_normalized(normalized_record, end)
        raw_span = raw_text[cursor:end]
        normalized_span = normalized_record["normalized_text"][normalized_start:normalized_end]
        spans.append(
            {
                "span_id": f"font-span:{len(spans) + 1:04d}",
                "font_base_name": BUKYVEDE_FONT_BASE_NAME,
                "pdf_page_number": typed_refs[0][0],
                "page_start_char": typed_refs[0][1],
                "page_end_char": typed_refs[-1][1] + 1,
                "raw_start_char": cursor,
                "raw_end_char": end,
                "raw_text": raw_span,
                "raw_text_sha256": _sha256_text(raw_span),
                "normalized_start_char": normalized_start,
                "normalized_end_char": normalized_end,
                "normalized_text": normalized_span,
                "normalized_text_sha256": _sha256_text(normalized_span),
            }
        )
        cursor = end
    return spans


def _candidate_lines(
    raw_text: str,
    normalized_record: Mapping[str, Any],
    tags: Sequence[str],
    page_refs: Sequence[tuple[int, int] | None],
) -> tuple[list[dict[str, Any]], int]:
    candidates: list[dict[str, Any]] = []
    lines_with_bukyvede = 0
    raw_start = 0
    for line in raw_text.splitlines(keepends=True):
        raw_end = raw_start + len(line)
        nonspace_positions = [offset for offset, char in enumerate(line) if not char.isspace()]
        bukyvede_nonspace = sum(tags[raw_start + offset] == BUKYVEDE_FONT_BASE_NAME for offset in nonspace_positions)
        if bukyvede_nonspace:
            lines_with_bukyvede += 1
        if nonspace_positions and 2 * bukyvede_nonspace >= len(nonspace_positions):
            line_page_refs = [ref for ref in page_refs[raw_start:raw_end] if ref is not None]
            require(bool(line_page_refs), "candidate line lacks a PDF page locator")
            require(len({ref[0] for ref in line_page_refs}) == 1, "candidate line crosses PDF pages")
            require(
                [ref[1] for ref in line_page_refs] == list(range(line_page_refs[0][1], line_page_refs[-1][1] + 1)),
                "candidate line page offsets are not contiguous",
            )
            context_start = max(0, raw_start - CONTEXT_WINDOW_CODEPOINTS)
            context = raw_text[context_start:raw_start]
            folded_context = context.casefold()
            has_text_cue = TEXT_CUE_RE.search(folded_context) is not None
            matched_shape_cues = [cue for cue in SHAPE_CUES if cue in folded_context]
            classification = (
                "author_reconstruction_trigger_candidate"
                if has_text_cue and matched_shape_cues
                else "dominant_historic_script_unresolved"
            )
            normalized_start = _raw_boundary_to_normalized(normalized_record, raw_start)
            normalized_end = _raw_boundary_to_normalized(normalized_record, raw_end)
            normalized_line = normalized_record["normalized_text"][normalized_start:normalized_end]
            candidates.append(
                {
                    "candidate_id": f"dominant-line:{len(candidates) + 1:03d}",
                    "classification": classification,
                    "classification_is_semantic_gold": False,
                    "pdf_page_number": line_page_refs[0][0],
                    "page_start_char": line_page_refs[0][1],
                    "page_end_char": line_page_refs[-1][1] + 1,
                    "raw_start_char": raw_start,
                    "raw_end_char": raw_end,
                    "raw_text": line,
                    "raw_text_sha256": _sha256_text(line),
                    "normalized_start_char": normalized_start,
                    "normalized_end_char": normalized_end,
                    "normalized_text": normalized_line,
                    "normalized_text_sha256": _sha256_text(normalized_line),
                    "line_nonspace_characters": len(nonspace_positions),
                    "bukyvede_nonspace_characters": bukyvede_nonspace,
                    "dominance_numerator": bukyvede_nonspace,
                    "dominance_denominator": len(nonspace_positions),
                    "dominance_threshold": "at_least_one_half",
                    "trigger_context_start_char": context_start,
                    "trigger_context_end_char": raw_start,
                    "trigger_context_sha256": _sha256_text(context),
                    "text_cue_present": has_text_cue,
                    "matched_shape_cues": matched_shape_cues,
                    "qualified_historical_review_status": "pending",
                    "training_eligible": False,
                }
            )
        raw_start = raw_end
    require(raw_start == len(raw_text), "line scan did not consume complete raw context")
    return candidates, lines_with_bukyvede


def build_layout_candidate_record(
    raw_record: Mapping[str, Any],
    normalized_record: Mapping[str, Any],
    page_layouts: Mapping[int, Mapping[str, Any]],
    *,
    adapter_output_sha256: str,
) -> dict[str, Any]:
    """Build one complete-context, fail-closed layout-review record."""
    raw_text, tags, page_refs = _record_layout(raw_record, normalized_record, page_layouts)
    spans = _font_spans(raw_text, normalized_record, tags, page_refs)
    candidates, lines_with_bukyvede = _candidate_lines(raw_text, normalized_record, tags, page_refs)
    bukyvede_characters = sum(len(span["raw_text"]) for span in spans)
    bukyvede_nonspace = sum(sum(not char.isspace() for char in span["raw_text"]) for span in spans)
    return {
        "schema_version": "phase3_spas_layout_candidate_record_v1",
        "record_id": f"{raw_record['record_id']}:layout-candidates-v1",
        "source_record_id": raw_record["record_id"],
        "collection_id": COLLECTION_ID,
        "graffito_number": raw_record["graffito_number"],
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "upstream_raw_catalog_sha256": EXPECTED_RAW_OUTPUT_SHA256,
        "upstream_adapter_output_sha256": adapter_output_sha256,
        "raw_context": raw_text,
        "raw_context_sha256": _sha256_text(raw_text),
        "normalized_context": normalized_record["normalized_text"],
        "normalized_context_sha256": normalized_record["normalized_text_sha256"],
        "font_spans": spans,
        "historic_script_dominant_line_candidates": candidates,
        "denominator": {
            "bukyvede_font_spans": len(spans),
            "bukyvede_characters": bukyvede_characters,
            "bukyvede_nonspace_characters": bukyvede_nonspace,
            "lines_with_bukyvede": lines_with_bukyvede,
            "dominant_line_candidates": len(candidates),
        },
        "separation_status": "candidate_routing_only_pending_qualified_historical_review",
        "commentary_and_inscription_layers_separated": False,
        "semantic_gold": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "provider_calls": False,
        "phase4_authorized": False,
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
        raise SpasLayoutCandidateError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise SpasLayoutCandidateError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    denominator = receipt["denominator"]
    require(
        denominator["input_records"]
        == denominator["output_records"]
        == receipt["output"]["records"]
        == EXPECTED_CATALOG_RECORDS,
        "receipt record denominator drift",
    )
    require(
        denominator["records_with_bukyvede"] + denominator["records_without_bukyvede"] == denominator["input_records"],
        "receipt font-presence partition drift",
    )
    require(
        denominator["trigger_line_candidates"] + denominator["unresolved_dominant_line_candidates"]
        == denominator["dominant_line_candidates"],
        "receipt candidate classification partition drift",
    )
    require(
        receipt["residuals"]["candidate_review_denominator"] == denominator["dominant_line_candidates"],
        "receipt review denominator drift",
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


def materialize_layout_candidates(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    adapter_output_dir: Path,
    mapping_evidence_path: Path,
    private_output_dir: Path,
    expected_records: int = EXPECTED_CATALOG_RECORDS,
    expected_records_with_bukyvede: int = EXPECTED_RECORDS_WITH_BUKYVEDE,
    expected_records_without_bukyvede: int = EXPECTED_RECORDS_WITHOUT_BUKYVEDE,
    expected_bukyvede_runs: int = EXPECTED_BUKYVEDE_RUNS,
    expected_bukyvede_characters: int = EXPECTED_BUKYVEDE_CHARACTERS,
    expected_bukyvede_nonspace_characters: int = EXPECTED_BUKYVEDE_NONSPACE_CHARACTERS,
    expected_lines_with_bukyvede: int = EXPECTED_LINES_WITH_BUKYVEDE,
    expected_dominant_lines: int = EXPECTED_DOMINANT_LINES,
    expected_dominant_records: int = EXPECTED_DOMINANT_RECORDS,
    expected_trigger_lines: int = EXPECTED_TRIGGER_LINES,
    expected_trigger_records: int = EXPECTED_TRIGGER_RECORDS,
    expected_unresolved_lines: int = EXPECTED_UNRESOLVED_LINES,
    expected_unresolved_records: int = EXPECTED_UNRESOLVED_RECORDS,
    expected_overlap_records: int = EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP,
) -> dict[str, Any]:
    """Write an immutable private review queue plus a text-free receipt."""
    resolved_output = private_output_dir.resolve()
    require(not _inside_git_checkout(resolved_output), "private text output cannot be inside a Git checkout")
    require(not private_output_dir.exists(), "immutable private output directory already exists")
    require(private_output_dir.parent.is_dir(), "private output parent directory does not exist")
    require(mapping_evidence_path.parent.resolve() == raw_catalog_dir.resolve(), "mapping evidence path drift")

    upstream = validate_existing_glyph_adapter(
        pdf_path=pdf_path,
        raw_catalog_dir=raw_catalog_dir,
        mapping_evidence_path=mapping_evidence_path,
        private_output_dir=adapter_output_dir,
    )
    require(upstream["records"] == expected_records, "upstream adapter record denominator drift")
    require(upstream["output_sha256"] == EXPECTED_ADAPTER_OUTPUT_SHA256, "upstream adapter output identity drift")
    require(upstream["receipt_sha256"] == EXPECTED_ADAPTER_RECEIPT_SHA256, "upstream adapter receipt identity drift")
    require(upstream["training_eligible"] is False, "upstream adapter cannot authorize training")
    require(upstream["phase4_authorized"] is False, "upstream adapter cannot authorize Phase 4")

    raw_path = raw_catalog_dir / RAW_OUTPUT_FILENAME
    adapter_path = adapter_output_dir / ADAPTER_OUTPUT_FILENAME
    adapter_receipt_path = adapter_output_dir / ADAPTER_RECEIPT_FILENAME
    require(file_sha256(raw_path) == EXPECTED_RAW_OUTPUT_SHA256, "raw catalogue identity drift")
    require(file_sha256(adapter_path) == EXPECTED_ADAPTER_OUTPUT_SHA256, "adapter output identity drift")
    require(
        file_sha256(adapter_receipt_path) == EXPECTED_ADAPTER_RECEIPT_FILE_SHA256,
        "adapter receipt file identity drift",
    )
    require(file_sha256(mapping_evidence_path) == EXPECTED_MAPPING_EVIDENCE_SHA256, "mapping evidence identity drift")
    raw_records = _load_jsonl_gzip(raw_path, description="raw catalogue JSONL")
    normalized_records = _load_jsonl_gzip(adapter_path, description="glyph adapter JSONL")
    require(file_sha256(raw_path) == EXPECTED_RAW_OUTPUT_SHA256, "raw catalogue changed while loading")
    require(file_sha256(adapter_path) == EXPECTED_ADAPTER_OUTPUT_SHA256, "adapter output changed while loading")
    require(len(raw_records) == len(normalized_records) == expected_records, "input record count drift")
    require(
        [record.get("graffito_number") for record in raw_records]
        == [record.get("graffito_number") for record in normalized_records]
        == list(range(1, expected_records + 1)),
        "input record sequence drift",
    )
    page_layouts = extract_font_layout_pages(pdf_path)
    output_records = [
        build_layout_candidate_record(
            raw_record,
            normalized_record,
            page_layouts,
            adapter_output_sha256=EXPECTED_ADAPTER_OUTPUT_SHA256,
        )
        for raw_record, normalized_record in zip(raw_records, normalized_records, strict=True)
    ]

    records_with_bukyvede = sum(bool(record["font_spans"]) for record in output_records)
    records_without_bukyvede = len(output_records) - records_with_bukyvede
    bukyvede_runs = sum(record["denominator"]["bukyvede_font_spans"] for record in output_records)
    bukyvede_characters = sum(record["denominator"]["bukyvede_characters"] for record in output_records)
    bukyvede_nonspace = sum(record["denominator"]["bukyvede_nonspace_characters"] for record in output_records)
    lines_with_bukyvede = sum(record["denominator"]["lines_with_bukyvede"] for record in output_records)
    dominant_lines = sum(record["denominator"]["dominant_line_candidates"] for record in output_records)
    dominant_record_ids = {
        record["graffito_number"] for record in output_records if record["historic_script_dominant_line_candidates"]
    }
    trigger_record_ids: set[int] = set()
    unresolved_record_ids: set[int] = set()
    trigger_lines = 0
    unresolved_lines = 0
    for record in output_records:
        for candidate in record["historic_script_dominant_line_candidates"]:
            if candidate["classification"] == "author_reconstruction_trigger_candidate":
                trigger_lines += 1
                trigger_record_ids.add(record["graffito_number"])
            else:
                unresolved_lines += 1
                unresolved_record_ids.add(record["graffito_number"])

    observed = {
        "records_with_bukyvede": records_with_bukyvede,
        "records_without_bukyvede": records_without_bukyvede,
        "bukyvede_font_spans": bukyvede_runs,
        "bukyvede_characters": bukyvede_characters,
        "bukyvede_nonspace_characters": bukyvede_nonspace,
        "lines_with_bukyvede": lines_with_bukyvede,
        "dominant_line_candidates": dominant_lines,
        "records_with_dominant_candidates": len(dominant_record_ids),
        "trigger_line_candidates": trigger_lines,
        "records_with_trigger_candidates": len(trigger_record_ids),
        "unresolved_dominant_line_candidates": unresolved_lines,
        "records_with_unresolved_candidates": len(unresolved_record_ids),
        "trigger_unresolved_record_overlap": len(trigger_record_ids & unresolved_record_ids),
    }
    expected = {
        "records_with_bukyvede": expected_records_with_bukyvede,
        "records_without_bukyvede": expected_records_without_bukyvede,
        "bukyvede_font_spans": expected_bukyvede_runs,
        "bukyvede_characters": expected_bukyvede_characters,
        "bukyvede_nonspace_characters": expected_bukyvede_nonspace_characters,
        "lines_with_bukyvede": expected_lines_with_bukyvede,
        "dominant_line_candidates": expected_dominant_lines,
        "records_with_dominant_candidates": expected_dominant_records,
        "trigger_line_candidates": expected_trigger_lines,
        "records_with_trigger_candidates": expected_trigger_records,
        "unresolved_dominant_line_candidates": expected_unresolved_lines,
        "records_with_unresolved_candidates": expected_unresolved_records,
        "trigger_unresolved_record_overlap": expected_overlap_records,
    }
    require(observed == expected, "layout candidate denominator drift")

    identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_context_sha256": record["raw_context_sha256"],
            "normalized_context_sha256": record["normalized_context_sha256"],
            "font_span_count": len(record["font_spans"]),
            "candidate_line_count": len(record["historic_script_dominant_line_candidates"]),
        }
        for record in output_records
    ]
    page_layout_manifest = [
        {
            "pdf_page_number": page_number,
            "native_text_sha256": page_layouts[page_number]["text_sha256"],
            "native_text_characters": len(page_layouts[page_number]["text"]),
        }
        for page_number in sorted(page_layouts)
    ]

    staging_dir = Path(tempfile.mkdtemp(prefix=f".{private_output_dir.name}.staging-", dir=private_output_dir.parent))
    try:
        output_path = staging_dir / OUTPUT_FILENAME
        output_count, output_bytes, output_sha256 = _write_jsonl_gzip(output_path, output_records)
        body: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "mode": "source_font_layout_candidate_routing",
            "text_free": True,
            "inputs": {
                "collection_id": COLLECTION_ID,
                "source_pdf_sha256": SOURCE_PDF_SHA256,
                "raw_catalog_sha256": EXPECTED_RAW_OUTPUT_SHA256,
                "raw_materialization_receipt_file_sha256": EXPECTED_RAW_RECEIPT_FILE_SHA256,
                "raw_materialization_receipt_sha256": EXPECTED_RAW_RECEIPT_SHA256,
                "mapping_evidence_sha256": EXPECTED_MAPPING_EVIDENCE_SHA256,
                "adapter_output_sha256": EXPECTED_ADAPTER_OUTPUT_SHA256,
                "adapter_receipt_file_sha256": EXPECTED_ADAPTER_RECEIPT_FILE_SHA256,
                "adapter_receipt_sha256": EXPECTED_ADAPTER_RECEIPT_SHA256,
                "pypdf_version": importlib.metadata.version("pypdf"),
                "implementation_sha256": file_sha256(Path(__file__)),
                "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
                "page_layout_manifest_sha256": sha256_value(page_layout_manifest),
            },
            "routing_contract": {
                "font_base_name": BUKYVEDE_FONT_BASE_NAME,
                "dominance_rule": "2 * bukyvede_nonspace_characters >= line_nonspace_characters",
                "context_window_codepoints": CONTEXT_WINDOW_CODEPOINTS,
                "required_text_cue": "whole_word:текст",
                "shape_cues": list(SHAPE_CUES),
                "trigger_classification": "author_reconstruction_trigger_candidate",
                "fallback_classification": "dominant_historic_script_unresolved",
                "classifications_are_semantic_gold": False,
            },
            "denominator": {
                "input_records": len(raw_records),
                "output_records": output_count,
                **observed,
            },
            "output": {
                "filename": OUTPUT_FILENAME,
                "records": output_count,
                "bytes": output_bytes,
                "sha256": output_sha256,
                "record_identity_manifest_sha256": sha256_value(identity_manifest),
            },
            "rights_and_scope": {
                "inherits_upstream_accepted_operational_risk": True,
                "private_review_queue_only": True,
                "attribution_and_field_level_removal_preserved": True,
                "binary_media_reuse_authorized": False,
                "full_publication_training_export_authorized": False,
                "adapt_on_substantiated_rights_notice": True,
            },
            "safeguards": {
                "complete_record_context_preserved": True,
                "raw_and_normalized_offsets_preserved": True,
                "font_spans_source_derived": True,
                "candidate_routing_only": True,
                "commentary_and_inscription_layers_separated": False,
                "qualified_historical_review_complete": False,
                "semantic_gold": False,
                "training_eligible": False,
                "modern_correction_eligible": False,
                "images_included": False,
                "provider_calls": False,
                "phase4_authorized": False,
            },
            "residuals": {
                "all_dominant_line_candidates_require_review": True,
                "candidate_review_denominator": dominant_lines,
                "inline_or_nondominant_font_spans_remain_context_only": True,
                "commentary_transcription_separation_pending": True,
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


def _validate_candidate_record(record: Mapping[str, Any]) -> None:
    require(record["schema_version"] == "phase3_spas_layout_candidate_record_v1", "candidate row schema drift")
    require(record["collection_id"] == COLLECTION_ID, "candidate row collection drift")
    require(record["source_pdf_sha256"] == SOURCE_PDF_SHA256, "candidate row PDF identity drift")
    require(record["upstream_raw_catalog_sha256"] == EXPECTED_RAW_OUTPUT_SHA256, "candidate row raw identity drift")
    require(
        record["upstream_adapter_output_sha256"] == EXPECTED_ADAPTER_OUTPUT_SHA256,
        "candidate row adapter identity drift",
    )
    require(record["raw_context_sha256"] == _sha256_text(record["raw_context"]), "candidate raw hash drift")
    require(
        record["normalized_context_sha256"] == _sha256_text(record["normalized_context"]),
        "candidate normalized hash drift",
    )
    for field in (
        "commentary_and_inscription_layers_separated",
        "semantic_gold",
        "training_eligible",
        "modern_correction_eligible",
        "provider_calls",
        "phase4_authorized",
    ):
        require(record[field] is False, f"unsafe candidate row flag: {field}")
    for span in record["font_spans"]:
        raw_start, raw_end = span["raw_start_char"], span["raw_end_char"]
        normalized_start, normalized_end = span["normalized_start_char"], span["normalized_end_char"]
        require(record["raw_context"][raw_start:raw_end] == span["raw_text"], "font span raw offset drift")
        require(
            record["normalized_context"][normalized_start:normalized_end] == span["normalized_text"],
            "font span normalized offset drift",
        )
        require(span["raw_text_sha256"] == _sha256_text(span["raw_text"]), "font span raw hash drift")
        require(
            span["normalized_text_sha256"] == _sha256_text(span["normalized_text"]),
            "font span normalized hash drift",
        )
    for candidate in record["historic_script_dominant_line_candidates"]:
        raw_start, raw_end = candidate["raw_start_char"], candidate["raw_end_char"]
        normalized_start, normalized_end = candidate["normalized_start_char"], candidate["normalized_end_char"]
        require(record["raw_context"][raw_start:raw_end] == candidate["raw_text"], "candidate raw offset drift")
        require(
            record["normalized_context"][normalized_start:normalized_end] == candidate["normalized_text"],
            "candidate normalized offset drift",
        )
        require(candidate["raw_text_sha256"] == _sha256_text(candidate["raw_text"]), "candidate raw hash drift")
        require(
            candidate["normalized_text_sha256"] == _sha256_text(candidate["normalized_text"]),
            "candidate normalized hash drift",
        )
        context_start = candidate["trigger_context_start_char"]
        context_end = candidate["trigger_context_end_char"]
        require(context_end == raw_start, "candidate trigger context end drift")
        trigger_context = record["raw_context"][context_start:context_end]
        require(
            candidate["trigger_context_sha256"] == _sha256_text(trigger_context),
            "candidate trigger context hash drift",
        )
        folded_context = trigger_context.casefold()
        expected_text_cue = TEXT_CUE_RE.search(folded_context) is not None
        expected_shape_cues = [cue for cue in SHAPE_CUES if cue in folded_context]
        require(candidate["text_cue_present"] is expected_text_cue, "candidate text cue drift")
        require(candidate["matched_shape_cues"] == expected_shape_cues, "candidate shape cue drift")
        expected_classification = (
            "author_reconstruction_trigger_candidate"
            if expected_text_cue and expected_shape_cues
            else "dominant_historic_script_unresolved"
        )
        require(candidate["classification"] == expected_classification, "candidate classification drift")
        require(
            2 * candidate["bukyvede_nonspace_characters"] >= candidate["line_nonspace_characters"],
            "candidate dominance drift",
        )
        require(candidate["classification_is_semantic_gold"] is False, "candidate cannot be semantic gold")
        require(candidate["qualified_historical_review_status"] == "pending", "candidate review status drift")
        require(candidate["training_eligible"] is False, "candidate cannot authorize training")


def validate_existing_layout_candidates(
    *,
    pdf_path: Path,
    raw_catalog_dir: Path,
    adapter_output_dir: Path,
    mapping_evidence_path: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Rebind an existing candidate queue to every current source input."""
    receipt_path = private_output_dir / RECEIPT_FILENAME
    output_path = private_output_dir / OUTPUT_FILENAME
    receipt = _load_json_object(receipt_path, description="layout candidate receipt")
    _validate_receipt(receipt)
    inputs = receipt["inputs"]
    denominator = receipt["denominator"]
    exact_inputs = {
        "collection_id": COLLECTION_ID,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "raw_catalog_sha256": EXPECTED_RAW_OUTPUT_SHA256,
        "raw_materialization_receipt_file_sha256": EXPECTED_RAW_RECEIPT_FILE_SHA256,
        "raw_materialization_receipt_sha256": EXPECTED_RAW_RECEIPT_SHA256,
        "mapping_evidence_sha256": EXPECTED_MAPPING_EVIDENCE_SHA256,
        "adapter_output_sha256": EXPECTED_ADAPTER_OUTPUT_SHA256,
        "adapter_receipt_file_sha256": EXPECTED_ADAPTER_RECEIPT_FILE_SHA256,
        "adapter_receipt_sha256": EXPECTED_ADAPTER_RECEIPT_SHA256,
        "pypdf_version": importlib.metadata.version("pypdf"),
        "implementation_sha256": file_sha256(Path(__file__)),
        "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
    }
    for key, expected_value in exact_inputs.items():
        require(inputs[key] == expected_value, f"receipt input identity drift: {key}")
    expected_denominator = {
        "input_records": EXPECTED_CATALOG_RECORDS,
        "output_records": EXPECTED_CATALOG_RECORDS,
        "records_with_bukyvede": EXPECTED_RECORDS_WITH_BUKYVEDE,
        "records_without_bukyvede": EXPECTED_RECORDS_WITHOUT_BUKYVEDE,
        "bukyvede_font_spans": EXPECTED_BUKYVEDE_RUNS,
        "bukyvede_characters": EXPECTED_BUKYVEDE_CHARACTERS,
        "bukyvede_nonspace_characters": EXPECTED_BUKYVEDE_NONSPACE_CHARACTERS,
        "lines_with_bukyvede": EXPECTED_LINES_WITH_BUKYVEDE,
        "dominant_line_candidates": EXPECTED_DOMINANT_LINES,
        "records_with_dominant_candidates": EXPECTED_DOMINANT_RECORDS,
        "trigger_line_candidates": EXPECTED_TRIGGER_LINES,
        "records_with_trigger_candidates": EXPECTED_TRIGGER_RECORDS,
        "unresolved_dominant_line_candidates": EXPECTED_UNRESOLVED_LINES,
        "records_with_unresolved_candidates": EXPECTED_UNRESOLVED_RECORDS,
        "trigger_unresolved_record_overlap": EXPECTED_TRIGGER_UNRESOLVED_RECORD_OVERLAP,
    }
    require(denominator == expected_denominator, "receipt exact denominator drift")
    upstream = validate_existing_glyph_adapter(
        pdf_path=pdf_path,
        raw_catalog_dir=raw_catalog_dir,
        mapping_evidence_path=mapping_evidence_path,
        private_output_dir=adapter_output_dir,
    )
    require(upstream["output_sha256"] == EXPECTED_ADAPTER_OUTPUT_SHA256, "upstream adapter identity drift")
    require(output_path.is_file() and not output_path.is_symlink(), "candidate output is missing or unsafe")
    require(file_sha256(output_path) == receipt["output"]["sha256"], "candidate output SHA-256 drift")
    require(output_path.stat().st_size == receipt["output"]["bytes"], "candidate output byte count drift")
    page_layouts = extract_font_layout_pages(pdf_path)
    page_layout_manifest = [
        {
            "pdf_page_number": page_number,
            "native_text_sha256": page_layouts[page_number]["text_sha256"],
            "native_text_characters": len(page_layouts[page_number]["text"]),
        }
        for page_number in sorted(page_layouts)
    ]
    require(
        sha256_value(page_layout_manifest) == inputs["page_layout_manifest_sha256"],
        "page layout manifest drift",
    )
    raw_records = _load_jsonl_gzip(raw_catalog_dir / RAW_OUTPUT_FILENAME, description="raw catalogue JSONL")
    normalized_records = _load_jsonl_gzip(
        adapter_output_dir / ADAPTER_OUTPUT_FILENAME, description="glyph adapter JSONL"
    )
    output_records = _load_jsonl_gzip(output_path, description="layout candidate JSONL")
    expected_records = [
        build_layout_candidate_record(
            raw_record,
            normalized_record,
            page_layouts,
            adapter_output_sha256=EXPECTED_ADAPTER_OUTPUT_SHA256,
        )
        for raw_record, normalized_record in zip(raw_records, normalized_records, strict=True)
    ]
    require(output_records == expected_records, "candidate output does not equal deterministic source replay")
    for record in output_records:
        _validate_candidate_record(record)
    identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "raw_context_sha256": record["raw_context_sha256"],
            "normalized_context_sha256": record["normalized_context_sha256"],
            "font_span_count": len(record["font_spans"]),
            "candidate_line_count": len(record["historic_script_dominant_line_candidates"]),
        }
        for record in output_records
    ]
    require(
        sha256_value(identity_manifest) == receipt["output"]["record_identity_manifest_sha256"],
        "candidate identity manifest drift",
    )
    return {
        "ok": True,
        "records": len(output_records),
        "candidate_lines": denominator["dominant_line_candidates"],
        "trigger_lines": denominator["trigger_line_candidates"],
        "unresolved_lines": denominator["unresolved_dominant_line_candidates"],
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
        "phase4_authorized": False,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--raw-catalog-dir", type=Path, required=True)
    parser.add_argument("--adapter-output-dir", type=Path, required=True)
    parser.add_argument("--mapping-evidence", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument("--validate-existing", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.validate_existing:
            result = validate_existing_layout_candidates(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                adapter_output_dir=args.adapter_output_dir,
                mapping_evidence_path=args.mapping_evidence,
                private_output_dir=args.private_output_dir,
            )
            status = "layout_candidates_validated"
        else:
            receipt = materialize_layout_candidates(
                pdf_path=args.pdf,
                raw_catalog_dir=args.raw_catalog_dir,
                adapter_output_dir=args.adapter_output_dir,
                mapping_evidence_path=args.mapping_evidence,
                private_output_dir=args.private_output_dir,
            )
            result = {
                "records": receipt["output"]["records"],
                "candidate_lines": receipt["denominator"]["dominant_line_candidates"],
                "trigger_lines": receipt["denominator"]["trigger_line_candidates"],
                "unresolved_lines": receipt["denominator"]["unresolved_dominant_line_candidates"],
                "output_sha256": receipt["output"]["sha256"],
                "receipt_sha256": receipt["receipt_sha256"],
                "training_eligible": False,
                "phase4_authorized": False,
            }
            status = "layout_candidates_materialized"
    except (SpasLayoutCandidateError, SpasCatalogMaterializationError, SpasGlyphAdapterError) as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(canonical_json({"status": status, **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
