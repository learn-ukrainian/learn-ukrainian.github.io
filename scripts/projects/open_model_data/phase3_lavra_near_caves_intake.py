#!/usr/bin/env python3
"""Materialize a protected raw intake for one Near Caves epigraphic study.

The source is Tymur Bobrovskyy's 2010 article on a multiline dipinto found in
the Near Caves of the Kyiv-Pechersk Lavra.  The article is direct cave evidence,
but its historic transcription uses a legacy ``CyrillicaBEM`` font whose
native PDF extraction is not Unicode text.  This module therefore preserves
the complete article and exact legacy-font spans without guessing mappings or
admitting any row to training.

The private JSONL contains source text.  The repository-facing receipt is
strictly text-free.
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
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pypdf import PdfReader

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value
from scripts.projects.open_model_data.phase3_spas_catalog_materialization import (
    _inside_git_checkout,
    file_sha256,
)

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_lavra_near_caves_intake_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_lavra_near_caves_intake_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_lavra_near_caves_intake_v1"
PRIVATE_RECORD_VERSION = "phase3_lavra_near_caves_raw_page_v1"
COLLECTION_ID = "bobrovskyy-near-caves-dipinto-2010"
SOURCE_TITLE = "Древнерусская надпись-дипинто из Ближних пещер Киево-Печерской лавры"
SOURCE_AUTHOR = "Тимур Бобровский"
SOURCE_YEAR = 2010
SOURCE_URL = "https://history.org.ua/JournALL/ruthenica/ruthenica_2010_9/ruthenica_2010_9.pdf"
SOURCE_PDF_SHA256 = "434b8654e6f2515c3db5d39b6499e29232b715947e356a5c2d364855d99c01e6"
RETRIEVAL_RECEIPT_SHA256 = "773770c35459ce10220f6f8e4bff0d86f2f5532e0c845a505c4b3237f87ca148"
EXPECTED_PDF_PAGES = 234
ARTICLE_PDF_PAGE_START = 166
ARTICLE_PDF_PAGE_END = 184
EXPECTED_ARTICLE_PAGES = 19
EXPECTED_NATIVE_TEXT_CHARACTERS = 38_394
EXPECTED_PAGES_WITH_LEGACY_FONT = 17
EXPECTED_LEGACY_FONT_SPANS = 559
EXPECTED_LEGACY_FONT_CHARACTERS = 2_141
EXPECTED_LEGACY_FONT_NONSPACE_CHARACTERS = 1_804
EXPECTED_LEGACY_FONT_BASE_NAME_COUNTS = {
    "/BCKIFG+CyrillicaBEM-Normal": 23,
    "/BCNADJ+CyrillicaBEM-Normal": 2_118,
}
LEGACY_FONT_SUFFIX = "CyrillicaBEM-Normal"
OUTPUT_FILENAME = "near-caves-dipinto-raw-pages-v1.jsonl.gz"
RECEIPT_FILENAME = "near-caves-intake-receipt-v1.json"

PRIVATE_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "record_id",
        "collection_id",
        "source_pdf_sha256",
        "pdf_page_number",
        "source_text",
        "source_text_sha256",
        "offset_basis",
        "legacy_font_spans",
        "legacy_font_characters",
        "legacy_font_nonspace_characters",
        "direct_lavra_near_caves_evidence",
        "source_attributed_reading_only",
        "legacy_encoding_resolved",
        "inferred_character_repairs",
        "inscription_and_commentary_layers_separated",
        "qualified_historical_review_complete",
        "semantic_gold",
        "training_eligible",
        "modern_correction_eligible",
        "provider_calls",
        "phase4_authorized",
    }
)


class LavraNearCavesIntakeError(ValueError):
    """A source identity, offset, denominator, or custody invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LavraNearCavesIntakeError(message)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LavraNearCavesIntakeError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be an object")
    return value


def _validate_retrieval_receipt(path: Path) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), "retrieval receipt is missing or unsafe")
    require(file_sha256(path) == RETRIEVAL_RECEIPT_SHA256, "retrieval receipt SHA-256 drift")
    receipt = _load_json_object(path, description="retrieval receipt")
    require(
        receipt.get("schema_version") == "phase3_historical_source_retrieval_receipt_v1",
        "retrieval receipt schema drift",
    )
    source = receipt.get("source")
    custody = receipt.get("custody")
    scope = receipt.get("phase3_scope")
    require(isinstance(source, Mapping), "retrieval source metadata is missing")
    require(isinstance(custody, Mapping), "retrieval custody metadata is missing")
    require(isinstance(scope, Mapping), "retrieval Phase 3 scope is missing")
    require(source.get("title") == SOURCE_TITLE, "retrieval title drift")
    require(source.get("author") == SOURCE_AUTHOR, "retrieval author drift")
    require(source.get("year") == SOURCE_YEAR, "retrieval year drift")
    require(source.get("landing_or_file_url") == SOURCE_URL, "retrieval URL drift")
    require(custody.get("sha256") == SOURCE_PDF_SHA256, "retrieval PDF identity drift")
    require(custody.get("pdf_pages") == EXPECTED_PDF_PAGES, "retrieval PDF page denominator drift")
    require(custody.get("storage") == "private_google_drive", "retrieval custody location drift")
    require(scope.get("direct_inscription_evidence") is True, "direct evidence flag is missing")
    require(scope.get("training_admitted") is False, "retrieval receipt cannot admit training")
    require(scope.get("phase4_blocked") is True, "retrieval receipt must keep Phase 4 blocked")
    return receipt


def _legacy_font_spans(text: str, font_tags: Sequence[str]) -> list[dict[str, Any]]:
    require(len(text) == len(font_tags), "font tag alignment drift")
    spans: list[dict[str, Any]] = []
    cursor = 0
    while cursor < len(text):
        if not font_tags[cursor].endswith(LEGACY_FONT_SUFFIX):
            cursor += 1
            continue
        base_font = font_tags[cursor]
        end = cursor + 1
        while end < len(text) and font_tags[end] == base_font:
            end += 1
        span_text = text[cursor:end]
        spans.append(
            {
                "span_id": f"legacy-font-span:{len(spans) + 1:04d}",
                "font_base_name": base_font,
                "start_char": cursor,
                "end_char": end,
                "raw_text": span_text,
                "raw_text_sha256": _sha256_text(span_text),
                "encoding_status": "legacy_font_unresolved_no_unicode_claim",
            }
        )
        cursor = end
    return spans


def load_article_pages(pdf_path: Path) -> dict[int, dict[str, Any]]:
    """Extract complete article pages and one exact font label per code point."""
    require(pdf_path.is_file() and not pdf_path.is_symlink(), "source PDF is missing or unsafe")
    require(file_sha256(pdf_path) == SOURCE_PDF_SHA256, "source PDF SHA-256 drift")
    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:
        raise LavraNearCavesIntakeError(f"cannot open source PDF: {exc}") from exc
    require(not reader.is_encrypted, "encrypted source PDF is not supported")
    require(len(reader.pages) == EXPECTED_PDF_PAGES, "source PDF page denominator drift")

    pages: dict[int, dict[str, Any]] = {}
    for page_number in range(ARTICLE_PDF_PAGE_START, ARTICLE_PDF_PAGE_END + 1):
        font_tags: list[str] = []

        def visitor(
            extracted_text: str,
            _cm: Sequence[float],
            _tm: Sequence[float],
            font_dictionary: Mapping[str, Any] | None,
            _font_size: float,
            _font_tags: list[str] = font_tags,
        ) -> None:
            base_font = str(font_dictionary.get("/BaseFont")) if font_dictionary else "NONE"
            _font_tags.extend([base_font] * len(extracted_text))

        try:
            text = reader.pages[page_number - 1].extract_text(visitor_text=visitor) or ""
        except Exception as exc:
            raise LavraNearCavesIntakeError(f"native extraction failed on PDF page {page_number}: {exc}") from exc
        require(text.strip() != "", f"article PDF page {page_number} has no native text")
        require("\ufffd" not in text, f"article PDF page {page_number} contains replacement characters")
        require(len(text) == len(font_tags), f"font tag alignment drift on PDF page {page_number}")
        spans = _legacy_font_spans(text, font_tags)
        pages[page_number] = {
            "text": text,
            "text_sha256": _sha256_text(text),
            "font_tags": font_tags,
            "legacy_font_spans": spans,
        }

    require(file_sha256(pdf_path) == SOURCE_PDF_SHA256, "source PDF changed while extracting")
    require(len(pages) == EXPECTED_ARTICLE_PAGES, "article page denominator drift")
    first_page_text = re.sub(r"\s+", " ", pages[ARTICLE_PDF_PAGE_START]["text"])
    require(SOURCE_TITLE in first_page_text, "article title identity drift")
    require("Ruthenica IX (2010), 166–184" in pages[ARTICLE_PDF_PAGE_START]["text"], "article citation identity drift")
    return pages


def build_page_record(page_number: int, page: Mapping[str, Any]) -> dict[str, Any]:
    text = page["text"]
    font_tags = page["font_tags"]
    spans = page["legacy_font_spans"]
    legacy_characters = sum(len(span["raw_text"]) for span in spans)
    legacy_nonspace = sum(not char.isspace() for span in spans for char in span["raw_text"])
    require(sum(tag.endswith(LEGACY_FONT_SUFFIX) for tag in font_tags) == legacy_characters, "legacy font count drift")
    return {
        "schema_version": PRIVATE_RECORD_VERSION,
        "record_id": f"lavra-near-caves-dipinto:pdf-page:{page_number:03d}",
        "collection_id": COLLECTION_ID,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "pdf_page_number": page_number,
        "source_text": text,
        "source_text_sha256": _sha256_text(text),
        "offset_basis": "unicode_code_points_in_pypdf_native_page_text",
        "legacy_font_spans": spans,
        "legacy_font_characters": legacy_characters,
        "legacy_font_nonspace_characters": legacy_nonspace,
        "direct_lavra_near_caves_evidence": True,
        "source_attributed_reading_only": True,
        "legacy_encoding_resolved": False,
        "inferred_character_repairs": False,
        "inscription_and_commentary_layers_separated": False,
        "qualified_historical_review_complete": False,
        "semantic_gold": False,
        "training_eligible": False,
        "modern_correction_eligible": False,
        "provider_calls": False,
        "phase4_authorized": False,
    }


def _validate_page_record(record: Mapping[str, Any], page: Mapping[str, Any], page_number: int) -> None:
    require(set(record) == PRIVATE_RECORD_FIELDS, f"private page {page_number} fields drift")
    require(record["schema_version"] == PRIVATE_RECORD_VERSION, "private record schema drift")
    require(record["record_id"] == f"lavra-near-caves-dipinto:pdf-page:{page_number:03d}", "record id drift")
    require(record["collection_id"] == COLLECTION_ID, "record collection drift")
    require(record["source_pdf_sha256"] == SOURCE_PDF_SHA256, "record source identity drift")
    require(record["pdf_page_number"] == page_number, "record page number drift")
    require(record["source_text"] == page["text"], "record text does not round-trip")
    require(record["source_text_sha256"] == page["text_sha256"], "record text hash drift")
    require(record["offset_basis"] == "unicode_code_points_in_pypdf_native_page_text", "offset basis drift")
    require(record["legacy_font_spans"] == page["legacy_font_spans"], "legacy font spans drift")
    require(
        record["legacy_font_characters"] == sum(len(span["raw_text"]) for span in page["legacy_font_spans"]),
        "legacy character denominator drift",
    )
    require(
        record["legacy_font_nonspace_characters"]
        == sum(not char.isspace() for span in page["legacy_font_spans"] for char in span["raw_text"]),
        "legacy nonspace denominator drift",
    )
    for field in ("direct_lavra_near_caves_evidence", "source_attributed_reading_only"):
        require(record[field] is True, f"required evidence flag drift: {field}")
    for field in (
        "legacy_encoding_resolved",
        "inferred_character_repairs",
        "inscription_and_commentary_layers_separated",
        "qualified_historical_review_complete",
        "semantic_gold",
        "training_eligible",
        "modern_correction_eligible",
        "provider_calls",
        "phase4_authorized",
    ):
        require(record[field] is False, f"unsafe private record flag: {field}")


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
        raise LavraNearCavesIntakeError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise LavraNearCavesIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    denominator = receipt["denominator"]
    output = receipt["output"]
    require(
        denominator["article_pages"] == denominator["nonempty_native_text_pages"] == output["records"],
        "receipt page denominator drift",
    )
    require(
        denominator["legacy_cyrillica_characters"] == sum(denominator["legacy_font_base_name_counts"].values()),
        "receipt legacy font base-name denominator drift",
    )


def _denominator_for_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    legacy_base_counts: Counter[str] = Counter()
    for record in records:
        for span in record["legacy_font_spans"]:
            legacy_base_counts[span["font_base_name"]] += len(span["raw_text"])
    return {
        "article_pages": len(records),
        "nonempty_native_text_pages": sum(bool(record["source_text"].strip()) for record in records),
        "native_text_characters": sum(len(record["source_text"]) for record in records),
        "pages_with_legacy_cyrillica": sum(bool(record["legacy_font_spans"]) for record in records),
        "legacy_cyrillica_spans": sum(len(record["legacy_font_spans"]) for record in records),
        "legacy_cyrillica_characters": sum(record["legacy_font_characters"] for record in records),
        "legacy_cyrillica_nonspace_characters": sum(record["legacy_font_nonspace_characters"] for record in records),
        "legacy_font_base_name_counts": dict(sorted(legacy_base_counts.items())),
    }


def _receipt_body(*, output_path: Path, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    page_manifest = [
        {
            "pdf_page_number": record["pdf_page_number"],
            "source_text_sha256": record["source_text_sha256"],
            "legacy_span_manifest_sha256": sha256_value(
                [
                    {
                        "font_base_name": span["font_base_name"],
                        "start_char": span["start_char"],
                        "end_char": span["end_char"],
                        "raw_text_sha256": span["raw_text_sha256"],
                    }
                    for span in record["legacy_font_spans"]
                ]
            ),
        }
        for record in records
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "inputs": {
            "collection_id": COLLECTION_ID,
            "source_title": SOURCE_TITLE,
            "source_author": SOURCE_AUTHOR,
            "source_year": SOURCE_YEAR,
            "institutional_source_url": SOURCE_URL,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "retrieval_receipt_sha256": RETRIEVAL_RECEIPT_SHA256,
            "pdf_pages": EXPECTED_PDF_PAGES,
            "article_pdf_page_start": ARTICLE_PDF_PAGE_START,
            "article_pdf_page_end": ARTICLE_PDF_PAGE_END,
            "extraction_backend": "pypdf",
            "extraction_backend_version": importlib.metadata.version("pypdf"),
            "implementation_sha256": file_sha256(Path(__file__)),
            "receipt_schema_sha256": file_sha256(RECEIPT_SCHEMA_PATH),
        },
        "denominator": _denominator_for_records(records),
        "output": {
            "filename": OUTPUT_FILENAME,
            "records": len(records),
            "bytes": output_path.stat().st_size,
            "sha256": file_sha256(output_path),
            "page_identity_manifest_sha256": sha256_value(page_manifest),
        },
        "source_scope": {
            "direct_lavra_near_caves_epigraphic_study": True,
            "article_subject": "one_multiline_dipinto_in_the_near_caves",
            "historical_period": "late_twelfth_century",
            "institutional_retrieval": True,
            "source_attributed_reading_only": True,
            "full_lavra_cave_corpus": False,
        },
        "rights_and_scope": {
            "operator_accepted_bounded_operational_risk": True,
            "private_research_and_source_evidence_only": True,
            "source_attribution_and_locator_preserved": True,
            "full_pdf_public_redistribution_authorized": False,
            "full_publication_training_export_authorized": False,
            "adapt_or_remove_on_substantiated_notice": True,
        },
        "safeguards": {
            "complete_article_context_preserved_privately": True,
            "native_text_offsets_preserved": True,
            "legacy_font_spans_source_derived": True,
            "legacy_encoding_resolved": False,
            "inferred_character_repairs": False,
            "qualified_historical_review_complete": False,
            "semantic_gold": False,
            "training_eligible": False,
            "modern_correction_eligible": False,
            "public_repo_contains_source_text": False,
            "provider_calls": False,
            "phase4_authorized": False,
        },
        "residuals": {
            "legacy_font_mapping_required": True,
            "inscription_and_commentary_separation_required": True,
            "qualified_historical_review_required": True,
            "additional_near_far_and_varangian_cave_sources_required": True,
            "lavra_cave_corpus_gap_closed": False,
        },
    }


def _assert_expected_denominator(receipt: Mapping[str, Any]) -> None:
    denominator = receipt["denominator"]
    expected = {
        "article_pages": EXPECTED_ARTICLE_PAGES,
        "nonempty_native_text_pages": EXPECTED_ARTICLE_PAGES,
        "native_text_characters": EXPECTED_NATIVE_TEXT_CHARACTERS,
        "pages_with_legacy_cyrillica": EXPECTED_PAGES_WITH_LEGACY_FONT,
        "legacy_cyrillica_spans": EXPECTED_LEGACY_FONT_SPANS,
        "legacy_cyrillica_characters": EXPECTED_LEGACY_FONT_CHARACTERS,
        "legacy_cyrillica_nonspace_characters": EXPECTED_LEGACY_FONT_NONSPACE_CHARACTERS,
        "legacy_font_base_name_counts": EXPECTED_LEGACY_FONT_BASE_NAME_COUNTS,
    }
    require(denominator == expected, "frozen Near Caves article denominator drift")


def materialize_intake(*, pdf_path: Path, retrieval_receipt_path: Path, private_output_dir: Path) -> dict[str, Any]:
    """Write the deterministic private raw layer and text-free receipt once."""
    require(not _inside_git_checkout(private_output_dir), "private source text cannot be written inside Git")
    require(not private_output_dir.is_symlink(), "private output directory cannot be a symbolic link")
    require(not private_output_dir.exists(), "immutable private output directory already exists")
    private_output_dir.parent.mkdir(parents=True, exist_ok=True)
    require(
        private_output_dir.parent.is_dir() and not private_output_dir.parent.is_symlink(),
        "private output parent is missing or unsafe",
    )

    _validate_retrieval_receipt(retrieval_receipt_path)
    pages = load_article_pages(pdf_path)
    records = [build_page_record(page_number, pages[page_number]) for page_number in sorted(pages)]
    for record in records:
        _validate_page_record(record, pages[record["pdf_page_number"]], record["pdf_page_number"])
    _assert_expected_denominator({"denominator": _denominator_for_records(records)})

    staged_output_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{private_output_dir.name}.stage-",
            dir=private_output_dir.parent,
        )
    )
    staged_output_path = staged_output_dir / OUTPUT_FILENAME
    staged_receipt_path = staged_output_dir / RECEIPT_FILENAME
    try:
        _write_jsonl_gzip(staged_output_path, records)
        receipt = _receipt_with_hash(_receipt_body(output_path=staged_output_path, records=records))
        _assert_expected_denominator(receipt)
        _validate_receipt(receipt)
        staged_receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_existing_intake(
            pdf_path=pdf_path,
            retrieval_receipt_path=retrieval_receipt_path,
            private_output_dir=staged_output_dir,
        )
        os.replace(staged_output_dir, private_output_dir)
    finally:
        if staged_output_dir.exists():
            for staged_file in (
                staged_output_dir / f".{OUTPUT_FILENAME}.tmp",
                staged_output_path,
                staged_receipt_path,
            ):
                if staged_file.exists():
                    staged_file.unlink()
            staged_output_dir.rmdir()
    validate_existing_intake(
        pdf_path=pdf_path,
        retrieval_receipt_path=retrieval_receipt_path,
        private_output_dir=private_output_dir,
    )
    return receipt


def validate_existing_intake(
    *,
    pdf_path: Path,
    retrieval_receipt_path: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Rebind an existing private intake to its current source bytes and implementation."""
    require(not _inside_git_checkout(private_output_dir), "private source text cannot be read from inside Git")
    output_path = private_output_dir / OUTPUT_FILENAME
    receipt_path = private_output_dir / RECEIPT_FILENAME
    require(output_path.is_file() and not output_path.is_symlink(), "private intake JSONL is missing or unsafe")
    require(receipt_path.is_file() and not receipt_path.is_symlink(), "intake receipt is missing or unsafe")
    _validate_retrieval_receipt(retrieval_receipt_path)
    receipt = _load_json_object(receipt_path, description="intake receipt")
    _validate_receipt(receipt)
    _assert_expected_denominator(receipt)
    inputs = receipt["inputs"]
    require(inputs["implementation_sha256"] == file_sha256(Path(__file__)), "implementation SHA-256 drift")
    require(inputs["receipt_schema_sha256"] == file_sha256(RECEIPT_SCHEMA_PATH), "receipt schema SHA-256 drift")
    require(inputs["extraction_backend_version"] == importlib.metadata.version("pypdf"), "pypdf version drift")
    require(output_path.stat().st_size == receipt["output"]["bytes"], "private output byte count drift")
    require(file_sha256(output_path) == receipt["output"]["sha256"], "private output SHA-256 drift")

    pages = load_article_pages(pdf_path)
    try:
        with gzip.open(output_path, "rt", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LavraNearCavesIntakeError(f"cannot read private intake JSONL: {exc}") from exc
    require(len(records) == EXPECTED_ARTICLE_PAGES, "private output record denominator drift")
    require(all(isinstance(record, dict) for record in records), "private intake rows must be objects")
    for expected_page, record in zip(sorted(pages), records, strict=True):
        _validate_page_record(record, pages[expected_page], expected_page)

    rebuilt_body = _receipt_body(output_path=output_path, records=records)
    rebuilt_receipt = _receipt_with_hash(rebuilt_body)
    require(receipt == rebuilt_receipt, "receipt does not reproduce from current source and private output")
    return {
        "records": len(records),
        "output_sha256": receipt["output"]["sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "legacy_encoding_resolved": False,
        "training_eligible": False,
        "phase4_authorized": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("materialize", "validate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--pdf", type=Path, required=True)
        subparser.add_argument("--retrieval-receipt", type=Path, required=True)
        subparser.add_argument("--private-output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        receipt = materialize_intake(
            pdf_path=args.pdf,
            retrieval_receipt_path=args.retrieval_receipt,
            private_output_dir=args.private_output_dir,
        )
        print(canonical_json(receipt))
        return 0
    result = validate_existing_intake(
        pdf_path=args.pdf,
        retrieval_receipt_path=args.retrieval_receipt,
        private_output_dir=args.private_output_dir,
    )
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
