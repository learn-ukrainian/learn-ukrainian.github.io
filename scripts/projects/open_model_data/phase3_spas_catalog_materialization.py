#!/usr/bin/env python3
"""Materialize the Spas na Berestovi graffiti catalogue as protected raw records.

The source is a Lavra-associated church corpus, not the Kyiv-Pechersk Lavra
cave-graffiti corpus.  Native PDF text is split only at the 477 printed
``Графіті №`` headings.  The private output preserves raw extraction and exact
page offsets; it deliberately does not normalize historical glyphs, separate
the author's commentary from inscription readings, or authorize training use.
The public receipt is text-free.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pypdf import PdfReader

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_spas_catalog_materialization_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_spas_catalog_materialization_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_spas_catalog_materialization_v1"
COLLECTION_ID = "korniienko-spas-na-berestovi-2013"
SOURCE_TITLE = "Корпус графіті церкви Спаса на Берестові (остання третина XI – перша третина XVIII ст.)"
SOURCE_AUTHOR = "В. В. Корнієнко"
SOURCE_YEAR = 2013
SOURCE_RECORD_URL = "https://resource.history.org.ua/item/0015198"
SOURCE_PDF_SHA256 = "b464439c73dee0a3092bb0cc37f56a0cd7d32709392c7b8745869d5df9b9281a"
EXPECTED_PDF_PAGES = 303
CATALOG_PDF_PAGE_START = 15
CATALOG_PDF_PAGE_END = 116
EXPECTED_CATALOG_RECORDS = 477
EXPECTED_NATIVE_TEXT_CHARACTERS = 229190
EXPECTED_PRIVATE_USE_COUNTS = {
    "U+E002": 13,
    "U+E026": 4,
    "U+E027": 10,
    "U+E02E": 3,
    "U+E02F": 27,
}
OUTPUT_FILENAME = "spas-na-berestovi-raw-catalog.jsonl.gz"
RECEIPT_FILENAME = "materialization-receipt-v1.json"
HEADING_PATTERN = r"Графіті\s*№\s*(\d+)(?=\s|\[|\()"
HEADING_RE = re.compile(HEADING_PATTERN)
RAW_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_id",
        "collection_id",
        "source_record_identity",
        "graffito_number",
        "heading_text",
        "source_pdf_sha256",
        "source_page_fragments",
        "source_text",
        "source_text_sha256",
        "offset_basis",
        "private_use_codepoint_counts",
        "contains_private_use_glyphs",
        "materialization_status",
        "normalization_status",
        "commentary_and_inscription_layers_separated",
        "page_header_footer_cleanup_applied",
        "training_eligible",
        "modern_correction_eligible",
        "ocr_used",
        "inferred_character_repairs",
        "images_included",
        "provider_calls",
    }
)


class SpasCatalogMaterializationError(ValueError):
    """An immutable identity or raw-materialization invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SpasCatalogMaterializationError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _private_use_counts(text: str) -> dict[str, int]:
    counts = Counter(f"U+{ord(char):04X}" for char in text if 0xE000 <= ord(char) <= 0xF8FF)
    return dict(sorted(counts.items()))


def _inside_git_checkout(path: Path) -> bool:
    return any((candidate / ".git").exists() for candidate in (path, *path.parents))


def load_catalog_pages(
    pdf_path: Path,
    *,
    expected_pdf_sha256: str = SOURCE_PDF_SHA256,
    expected_pdf_pages: int = EXPECTED_PDF_PAGES,
    catalog_pdf_page_start: int = CATALOG_PDF_PAGE_START,
    catalog_pdf_page_end: int = CATALOG_PDF_PAGE_END,
) -> dict[int, str]:
    """Load the exact native-text catalogue page range from an immutable PDF."""
    require(pdf_path.is_file(), f"source PDF is missing: {pdf_path}")
    require(not pdf_path.is_symlink(), "source PDF cannot be a symbolic link")
    actual_sha256 = file_sha256(pdf_path)
    require(
        actual_sha256 == expected_pdf_sha256,
        f"source PDF SHA-256 mismatch: expected {expected_pdf_sha256}, got {actual_sha256}",
    )
    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:  # pypdf exposes several backend-specific errors
        raise SpasCatalogMaterializationError(f"cannot open source PDF: {exc}") from exc
    require(not reader.is_encrypted, "encrypted source PDF is not supported")
    require(len(reader.pages) == expected_pdf_pages, "source PDF page denominator drift")
    require(
        1 <= catalog_pdf_page_start <= catalog_pdf_page_end <= len(reader.pages),
        "catalogue PDF page range is invalid",
    )

    pages: dict[int, str] = {}
    for pdf_page_number in range(catalog_pdf_page_start, catalog_pdf_page_end + 1):
        try:
            text = reader.pages[pdf_page_number - 1].extract_text() or ""
        except Exception as exc:
            raise SpasCatalogMaterializationError(
                f"native extraction failed on PDF page {pdf_page_number}: {exc}"
            ) from exc
        require(text.strip() != "", f"catalogue PDF page {pdf_page_number} has no native text")
        require("\ufffd" not in text, f"catalogue PDF page {pdf_page_number} contains replacement characters")
        pages[pdf_page_number] = text
    return pages


def split_catalog_records(
    page_texts: Mapping[int, str],
    *,
    expected_record_count: int = EXPECTED_CATALOG_RECORDS,
    source_pdf_sha256: str = SOURCE_PDF_SHA256,
) -> list[dict[str, Any]]:
    """Split native page text at exact printed graffito headings."""
    require(bool(page_texts), "catalogue page set is empty")
    page_numbers = sorted(page_texts)
    require(
        page_numbers == list(range(page_numbers[0], page_numbers[-1] + 1)),
        "catalogue page set must be contiguous",
    )
    for page_number in page_numbers:
        text = page_texts[page_number]
        require(isinstance(text, str) and text.strip() != "", f"catalogue page {page_number} is empty")
        require("\ufffd" not in text, f"catalogue page {page_number} contains replacement characters")

    headings: list[tuple[int, int, int, str]] = []
    for page_number in page_numbers:
        for match in HEADING_RE.finditer(page_texts[page_number]):
            headings.append((int(match.group(1)), page_number, match.start(), match.group(0)))

    numbers = [number for number, _, _, _ in headings]
    require(
        numbers == list(range(1, expected_record_count + 1)),
        "graffito heading denominator is not the exact sequential range",
    )

    records: list[dict[str, Any]] = []
    for index, (number, start_page, start_offset, heading_text) in enumerate(headings):
        if index + 1 < len(headings):
            _, end_page, end_offset, _ = headings[index + 1]
        else:
            end_page = page_numbers[-1]
            end_offset = len(page_texts[end_page])

        fragments: list[dict[str, Any]] = []
        fragment_texts: list[str] = []
        for page_number in range(start_page, end_page + 1):
            page_text = page_texts[page_number]
            fragment_start = start_offset if page_number == start_page else 0
            fragment_end = end_offset if page_number == end_page else len(page_text)
            require(
                0 <= fragment_start <= fragment_end <= len(page_text),
                f"record {number} has an invalid page fragment",
            )
            if fragment_start == fragment_end:
                continue
            fragment_text = page_text[fragment_start:fragment_end]
            fragment_texts.append(fragment_text)
            fragments.append(
                {
                    "pdf_page_number": page_number,
                    "start_char": fragment_start,
                    "end_char": fragment_end,
                    "text_sha256": hashlib.sha256(fragment_text.encode("utf-8")).hexdigest(),
                }
            )

        require(bool(fragment_texts), f"record {number} has no source text")
        source_text = "\n".join(fragment_texts)
        require(HEADING_RE.match(source_text) is not None, f"record {number} does not begin at its heading")
        pua_counts = _private_use_counts(source_text)
        records.append(
            {
                "schema_version": "phase3_spas_raw_catalog_record_v1",
                "record_id": f"spas-na-berestovi:graffito:{number:04d}",
                "collection_id": COLLECTION_ID,
                "source_record_identity": f"Графіті № {number}",
                "graffito_number": number,
                "heading_text": heading_text,
                "source_pdf_sha256": source_pdf_sha256,
                "source_page_fragments": fragments,
                "source_text": source_text,
                "source_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "offset_basis": "unicode_code_points_in_pypdf_native_page_text",
                "private_use_codepoint_counts": pua_counts,
                "contains_private_use_glyphs": bool(pua_counts),
                "materialization_status": "raw_record_boundary_verified",
                "normalization_status": "not_applied",
                "commentary_and_inscription_layers_separated": False,
                "page_header_footer_cleanup_applied": False,
                "training_eligible": False,
                "modern_correction_eligible": False,
                "ocr_used": False,
                "inferred_character_repairs": False,
                "images_included": False,
                "provider_calls": False,
            }
        )
    return records


def _write_jsonl_gzip(path: Path, records: Iterable[Mapping[str, Any]]) -> tuple[int, int, str]:
    temporary = path.with_name(f".{path.name}.tmp")
    count = 0
    try:
        with (
            temporary.open("wb") as raw_handle,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
        ):
            for record in records:
                gzip_handle.write(canonical_json(record).encode("utf-8") + b"\n")
                count += 1
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return count, path.stat().st_size, file_sha256(path)


def _receipt_with_hash(body: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(body)
    receipt["receipt_sha256"] = sha256_value(body)
    return receipt


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasCatalogMaterializationError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise SpasCatalogMaterializationError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    inputs = receipt["inputs"]
    denominator = receipt["denominator"]
    output = receipt["output"]
    pua_audit = receipt["private_use_audit"]
    require(
        denominator["catalog_pages"] == inputs["catalog_pdf_page_end"] - inputs["catalog_pdf_page_start"] + 1,
        "receipt catalogue page denominator drift",
    )
    require(
        denominator["nonempty_native_text_pages"] == denominator["catalog_pages"],
        "receipt nonempty page denominator drift",
    )
    require(
        denominator["expected_records"]
        == denominator["materialized_records"]
        == denominator["unique_record_numbers"]
        == output["records"],
        "receipt record denominator drift",
    )
    require(
        pua_audit["total_occurrences"] == sum(pua_audit["codepoint_counts"].values()),
        "receipt private-use denominator drift",
    )


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _validate_receipt(receipt)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_raw_record(
    record: Mapping[str, Any],
    *,
    expected_number: int,
    expected_pdf_sha256: str,
    page_texts: Mapping[int, str],
) -> None:
    require(set(record) == RAW_RECORD_FIELDS, f"raw record {expected_number} fields drift")
    require(record["schema_version"] == "phase3_spas_raw_catalog_record_v1", "raw record schema drift")
    require(record["record_id"] == f"spas-na-berestovi:graffito:{expected_number:04d}", "record id drift")
    require(record["collection_id"] == COLLECTION_ID, "raw record collection drift")
    require(record["source_record_identity"] == f"Графіті № {expected_number}", "source record identity drift")
    require(record["graffito_number"] == expected_number, "graffito number drift")
    require(record["source_pdf_sha256"] == expected_pdf_sha256, "raw record PDF identity drift")
    require(
        record["offset_basis"] == "unicode_code_points_in_pypdf_native_page_text",
        "raw record offset basis drift",
    )

    fragments = record["source_page_fragments"]
    require(isinstance(fragments, list) and fragments, f"raw record {expected_number} lacks page fragments")
    fragment_texts: list[str] = []
    previous_page = 0
    for fragment in fragments:
        require(
            set(fragment) == {"pdf_page_number", "start_char", "end_char", "text_sha256"},
            f"raw record {expected_number} fragment fields drift",
        )
        page_number = fragment["pdf_page_number"]
        require(page_number in page_texts, f"raw record {expected_number} refers to an unknown page")
        require(page_number > previous_page, f"raw record {expected_number} page fragments are not ordered")
        previous_page = page_number
        page_text = page_texts[page_number]
        start, end = fragment["start_char"], fragment["end_char"]
        require(
            isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(page_text),
            f"raw record {expected_number} fragment offsets drift",
        )
        fragment_text = page_text[start:end]
        require(
            fragment["text_sha256"] == hashlib.sha256(fragment_text.encode("utf-8")).hexdigest(),
            f"raw record {expected_number} fragment hash drift",
        )
        fragment_texts.append(fragment_text)

    source_text = "\n".join(fragment_texts)
    require(record["source_text"] == source_text, f"raw record {expected_number} source text does not round-trip")
    require(
        record["source_text_sha256"] == hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        f"raw record {expected_number} source text hash drift",
    )
    heading = HEADING_RE.match(source_text)
    require(heading is not None and int(heading.group(1)) == expected_number, "raw record heading drift")
    require(record["heading_text"] == heading.group(0), "raw record heading text drift")
    pua_counts = _private_use_counts(source_text)
    require(record["private_use_codepoint_counts"] == pua_counts, "raw record private-use audit drift")
    require(record["contains_private_use_glyphs"] is bool(pua_counts), "raw record private-use flag drift")
    require(record["materialization_status"] == "raw_record_boundary_verified", "materialization status drift")
    require(record["normalization_status"] == "not_applied", "normalization status drift")
    for field in (
        "commentary_and_inscription_layers_separated",
        "page_header_footer_cleanup_applied",
        "training_eligible",
        "modern_correction_eligible",
        "ocr_used",
        "inferred_character_repairs",
        "images_included",
        "provider_calls",
    ):
        require(record[field] is False, f"unsafe raw record flag: {field}")


def validate_existing_materialization(*, pdf_path: Path, private_output_dir: Path) -> dict[str, Any]:
    """Rebind an existing private output to the immutable PDF and every source slice."""
    receipt_path = private_output_dir / RECEIPT_FILENAME
    output_path = private_output_dir / OUTPUT_FILENAME
    require(receipt_path.is_file() and not receipt_path.is_symlink(), "materialization receipt is missing or unsafe")
    require(output_path.is_file() and not output_path.is_symlink(), "private JSONL is missing or unsafe")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpasCatalogMaterializationError(f"cannot read materialization receipt: {exc}") from exc
    require(isinstance(receipt, Mapping), "materialization receipt must be an object")
    _validate_receipt(receipt)
    inputs = receipt["inputs"]
    denominator = receipt["denominator"]
    pua_audit = receipt["private_use_audit"]
    require(inputs["source_pdf_sha256"] == SOURCE_PDF_SHA256, "receipt source PDF identity drift")
    require(inputs["pdf_pages"] == EXPECTED_PDF_PAGES, "receipt PDF page-count identity drift")
    require(
        inputs["catalog_pdf_page_start"] == CATALOG_PDF_PAGE_START,
        "receipt catalogue start-page identity drift",
    )
    require(
        inputs["catalog_pdf_page_end"] == CATALOG_PDF_PAGE_END,
        "receipt catalogue end-page identity drift",
    )
    require(
        denominator["native_text_characters"] == EXPECTED_NATIVE_TEXT_CHARACTERS,
        "receipt native-text character identity drift",
    )
    require(
        denominator["expected_records"] == EXPECTED_CATALOG_RECORDS,
        "receipt record-count identity drift",
    )
    require(
        pua_audit["codepoint_counts"] == EXPECTED_PRIVATE_USE_COUNTS,
        "receipt private-use identity drift",
    )
    require(
        inputs["extraction_backend_version"] == importlib.metadata.version("pypdf"),
        "pypdf extraction version drift",
    )
    require(output_path.stat().st_size == receipt["output"]["bytes"], "private JSONL byte count drift")
    require(file_sha256(output_path) == receipt["output"]["sha256"], "private JSONL SHA-256 drift")

    pages = load_catalog_pages(
        pdf_path,
        expected_pdf_sha256=inputs["source_pdf_sha256"],
        expected_pdf_pages=inputs["pdf_pages"],
        catalog_pdf_page_start=inputs["catalog_pdf_page_start"],
        catalog_pdf_page_end=inputs["catalog_pdf_page_end"],
    )
    require(sum(len(text) for text in pages.values()) == receipt["denominator"]["native_text_characters"], "native text denominator drift")
    pua_counts: Counter[str] = Counter()
    private_use_pages = 0
    for text in pages.values():
        page_counts = _private_use_counts(text)
        pua_counts.update(page_counts)
        private_use_pages += bool(page_counts)
    require(
        dict(sorted(pua_counts.items())) == receipt["private_use_audit"]["codepoint_counts"],
        "source PDF private-use audit drift",
    )
    require(
        private_use_pages == receipt["private_use_audit"]["pages_with_private_use_glyphs"],
        "source PDF private-use page denominator drift",
    )

    try:
        with gzip.open(output_path, "rt", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpasCatalogMaterializationError(f"cannot read private JSONL: {exc}") from exc
    require(len(records) == receipt["output"]["records"], "private JSONL record count drift")
    expected_records = split_catalog_records(
        pages,
        expected_record_count=receipt["denominator"]["expected_records"],
        source_pdf_sha256=inputs["source_pdf_sha256"],
    )
    require(records == expected_records, "private JSONL does not equal deterministic source-page materialization")
    for expected_number, record in enumerate(records, start=1):
        require(isinstance(record, Mapping), f"raw record {expected_number} must be an object")
        _validate_raw_record(
            record,
            expected_number=expected_number,
            expected_pdf_sha256=inputs["source_pdf_sha256"],
            page_texts=pages,
        )
    manifest = [
        {
            "graffito_number": record["graffito_number"],
            "source_text_sha256": record["source_text_sha256"],
            "source_page_fragments": record["source_page_fragments"],
        }
        for record in records
    ]
    require(
        sha256_value(manifest) == receipt["output"]["record_identity_manifest_sha256"],
        "record identity manifest drift",
    )
    return {
        "ok": True,
        "records": len(records),
        "source_pdf_sha256": inputs["source_pdf_sha256"],
        "private_jsonl_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "training_eligible": False,
    }


def materialize_spas_catalog(
    *,
    pdf_path: Path,
    private_output_dir: Path,
    receipt_output: Path,
    expected_pdf_sha256: str = SOURCE_PDF_SHA256,
    expected_pdf_pages: int = EXPECTED_PDF_PAGES,
    catalog_pdf_page_start: int = CATALOG_PDF_PAGE_START,
    catalog_pdf_page_end: int = CATALOG_PDF_PAGE_END,
    expected_record_count: int = EXPECTED_CATALOG_RECORDS,
    expected_native_text_characters: int = EXPECTED_NATIVE_TEXT_CHARACTERS,
    expected_private_use_counts: Mapping[str, int] = EXPECTED_PRIVATE_USE_COUNTS,
) -> dict[str, Any]:
    """Write an immutable private JSONL plus a text-free public receipt."""
    resolved_output = private_output_dir.resolve()
    require(not _inside_git_checkout(resolved_output), "private text output cannot be inside a Git checkout")
    require(receipt_output.parent.resolve() == resolved_output, "receipt must be inside private output directory")
    require(receipt_output.name == RECEIPT_FILENAME, "receipt filename is not the frozen value")
    require(not private_output_dir.exists(), "immutable private output directory already exists")
    require(private_output_dir.parent.is_dir(), "private output parent directory does not exist")

    pages = load_catalog_pages(
        pdf_path,
        expected_pdf_sha256=expected_pdf_sha256,
        expected_pdf_pages=expected_pdf_pages,
        catalog_pdf_page_start=catalog_pdf_page_start,
        catalog_pdf_page_end=catalog_pdf_page_end,
    )
    native_text_characters = sum(len(text) for text in pages.values())
    require(native_text_characters == expected_native_text_characters, "native catalogue character denominator drift")
    page_private_use_counts: Counter[str] = Counter()
    private_use_pages = 0
    for text in pages.values():
        counts = _private_use_counts(text)
        page_private_use_counts.update(counts)
        private_use_pages += bool(counts)
    require(
        dict(sorted(page_private_use_counts.items())) == dict(expected_private_use_counts),
        "private-use glyph denominator drift",
    )

    records = split_catalog_records(
        pages,
        expected_record_count=expected_record_count,
        source_pdf_sha256=expected_pdf_sha256,
    )
    record_identity_manifest = [
        {
            "graffito_number": record["graffito_number"],
            "source_text_sha256": record["source_text_sha256"],
            "source_page_fragments": record["source_page_fragments"],
        }
        for record in records
    ]

    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{private_output_dir.name}.staging-", dir=private_output_dir.parent)
    )
    try:
        output_path = staging_dir / OUTPUT_FILENAME
        record_count, output_bytes, output_sha256 = _write_jsonl_gzip(output_path, records)
        require(record_count == expected_record_count, "private output record count drift")
        body: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "implementation_version": IMPLEMENTATION_VERSION,
            "mode": "full_catalogue_boundary_materialization",
            "text_free": True,
            "inputs": {
                "collection_id": COLLECTION_ID,
                "source_author": SOURCE_AUTHOR,
                "source_title": SOURCE_TITLE,
                "source_year": SOURCE_YEAR,
                "source_record_url": SOURCE_RECORD_URL,
                "source_pdf_sha256": expected_pdf_sha256,
                "pdf_pages": expected_pdf_pages,
                "catalog_pdf_page_start": catalog_pdf_page_start,
                "catalog_pdf_page_end": catalog_pdf_page_end,
                "extraction_backend": "pypdf.page.extract_text",
                "extraction_backend_version": importlib.metadata.version("pypdf"),
            },
            "denominator": {
                "catalog_pages": len(pages),
                "nonempty_native_text_pages": len(pages),
                "native_text_characters": native_text_characters,
                "expected_records": expected_record_count,
                "materialized_records": record_count,
                "unique_record_numbers": len({record["graffito_number"] for record in records}),
                "sequential_record_numbers": True,
            },
            "private_use_audit": {
                "total_occurrences": sum(page_private_use_counts.values()),
                "pages_with_private_use_glyphs": private_use_pages,
                "codepoint_counts": dict(sorted(page_private_use_counts.items())),
                "glyph_font_observed_during_visual_canary": "Bukyvede",
                "mapping_status": "pending_visual_source_verified_adapter",
            },
            "output": {
                "filename": OUTPUT_FILENAME,
                "records": record_count,
                "bytes": output_bytes,
                "sha256": output_sha256,
                "record_identity_manifest_sha256": sha256_value(record_identity_manifest),
            },
            "rights_and_scope": {
                "public_institutional_full_text": True,
                "standardized_dataset_license_expression_found": False,
                "bounded_text_first_use_decision": "accepted_operational_risk",
                "attribution_and_field_level_removal_preserved": True,
                "binary_media_reuse_authorized": False,
                "full_publication_training_export_authorized": False,
                "adapt_on_substantiated_rights_notice": True,
            },
            "safeguards": {
                "raw_source_preserved": True,
                "historical_forms_protected": True,
                "normalized_historical_text_emitted": False,
                "commentary_and_inscription_layers_separated": False,
                "page_header_footer_cleanup_applied": False,
                "modern_correction_eligible": False,
                "training_eligible": False,
                "ocr_used": False,
                "inferred_character_repairs": False,
                "images_included": False,
                "provider_calls": False,
                "phase4_authorized": False,
            },
            "residuals": {
                "spas_na_berestovi_is_lavra_associated": True,
                "spas_na_berestovi_is_not_lavra_cave_corpus": True,
                "lavra_cave_corpus_gap_closed": False,
                "glyph_mapping_pending": True,
                "commentary_transcription_separation_pending": True,
            },
        }
        receipt = _receipt_with_hash(body)
        _write_receipt(staging_dir / RECEIPT_FILENAME, receipt)
        require(not private_output_dir.exists(), "immutable private output directory appeared during publication")
        os.replace(staging_dir, private_output_dir)
        return receipt
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt_output = args.private_output_dir / RECEIPT_FILENAME
    try:
        receipt = materialize_spas_catalog(
            pdf_path=args.pdf,
            private_output_dir=args.private_output_dir,
            receipt_output=receipt_output,
        )
    except SpasCatalogMaterializationError as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(
        canonical_json(
            {
                "status": "raw_catalogue_materialized",
                "records": receipt["output"]["records"],
                "training_eligible": receipt["safeguards"]["training_eligible"],
                "receipt_sha256": receipt["receipt_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
