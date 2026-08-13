#!/usr/bin/env python3
"""Verify the private raw intake for the 1582–1588 Zhytomyr act book.

The acquired file is a bundled multipage DjVu scan of Mykola Boichuk's 1965
scholarly edition.  This module validates the exact source bytes and walks the
DjVu IFF container without interpreting its compressed text layer.  It writes
only a text-free private receipt; it does not copy the source, infer historical
language labels, admit training rows, or authorize Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_middle_ukrainian_act_book_intake_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_middle_ukrainian_act_book_intake_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_middle_ukrainian_act_book_intake_v1"
COLLECTION_ID = "boichuk-zhytomyr-municipal-act-book-1582-1588-1965"
SOURCE_TITLE = "Актова книга Житомирського міського уряду кінця XVI ст. (1582–1588 рр.)"
SOURCE_PREPARER = "М. К. Бойчук"
PUBLICATION_YEAR = 1965
DOCUMENT_YEAR_START = 1582
DOCUMENT_YEAR_END = 1588
INSTITUTIONAL_CATALOGUE_URL = "https://irbis-nbuv.gov.ua/ulib/item/ukr0000028423"
MIRROR_DOWNLOAD_URL = (
    "https://file.lib.in.ua/djvu/boichuk-mk-aktova-knyha-zhytomyrskoho-miskoho-uriadu-kintsia-xvi-st-1582-1588-rr.djvu"
)
SOURCE_FILENAME = "boichuk-aktova-knyha-zhytomyr-1582-1588-1965.djvu"
SOURCE_SHA256 = "3f274c60e4411b8df925008c318a92db00dec5cc211d05172e0896fce7802f9e"
SOURCE_BYTES = 14_631_551
EXPECTED_DIRECTORY_FLAGS = 129
EXPECTED_COMPONENTS = 200
EXPECTED_PAGE_COMPONENTS = 196
EXPECTED_SHARED_COMPONENTS = 4
EXPECTED_PAGES_WITH_EMBEDDED_TEXT = 194
EXPECTED_CHUNK_COUNTS = {
    "BG44": 28,
    "Djbz": 4,
    "FGbz": 3,
    "INCL": 191,
    "INFO": 196,
    "Sjbz": 191,
    "TXTz": 194,
}
RECEIPT_FILENAME = "middle-ukrainian-act-book-intake-receipt-v1.json"


class MiddleUkrainianActBookIntakeError(ValueError):
    """A source identity, DjVu structure, custody, or safety invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MiddleUkrainianActBookIntakeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _u16(data: bytes, offset: int, label: str) -> int:
    require(offset >= 0 and offset + 2 <= len(data), f"truncated {label}")
    return int.from_bytes(data[offset : offset + 2], "big")


def _u32(data: bytes, offset: int, label: str) -> int:
    require(offset >= 0 and offset + 4 <= len(data), f"truncated {label}")
    return int.from_bytes(data[offset : offset + 4], "big")


def _ascii_fourcc(data: bytes, offset: int, label: str) -> str:
    require(offset >= 0 and offset + 4 <= len(data), f"truncated {label}")
    try:
        return data[offset : offset + 4].decode("ascii")
    except UnicodeDecodeError as exc:
        raise MiddleUkrainianActBookIntakeError(f"non-ASCII {label}") from exc


def _parse_component(data: bytes, *, index: int, offset: int, next_offset: int) -> dict[str, Any]:
    require(data[offset : offset + 4] == b"FORM", f"component {index} is not an IFF FORM")
    form_size = _u32(data, offset + 4, f"component {index} FORM size")
    require(form_size >= 4, f"component {index} FORM is too short")
    form_type = _ascii_fourcc(data, offset + 8, f"component {index} FORM type")
    require(form_type in {"DJVU", "DJVI"}, f"unsupported component type at {index}: {form_type}")

    form_end = offset + 8 + form_size
    require(form_end <= len(data), f"component {index} exceeds source bytes")
    padded_form_end = form_end + (form_size & 1)
    allowed_next_offsets = {padded_form_end}
    if form_end == len(data):
        allowed_next_offsets.add(form_end)
    require(next_offset in allowed_next_offsets, f"component {index} offset/size continuity drift")

    cursor = offset + 12
    chunks: list[dict[str, Any]] = []
    while cursor < form_end:
        require(cursor + 8 <= form_end, f"truncated chunk header in component {index}")
        chunk_id = _ascii_fourcc(data, cursor, f"component {index} chunk ID")
        chunk_size = _u32(data, cursor + 4, f"component {index} {chunk_id} size")
        payload_end = cursor + 8 + chunk_size
        require(payload_end <= form_end, f"component {index} {chunk_id} exceeds FORM bounds")
        chunks.append(
            {
                "chunk_id": chunk_id,
                "offset": cursor,
                "payload_bytes": chunk_size,
            }
        )
        if payload_end == form_end:
            cursor = form_end
        else:
            cursor = payload_end + (chunk_size & 1)
            require(cursor <= form_end, f"component {index} {chunk_id} padding exceeds FORM bounds")
    require(cursor == form_end, f"component {index} child-chunk walk did not close")

    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    if form_type == "DJVU":
        require(chunk_ids.count("INFO") == 1, f"page component {index} must contain one INFO chunk")
        require(
            sum(chunk_id in {"TXTa", "TXTz"} for chunk_id in chunk_ids) <= 1, f"page {index} has multiple text chunks"
        )
    else:
        require("INFO" not in chunk_ids, f"shared component {index} cannot contain a page INFO chunk")

    return {
        "component_index": index,
        "offset": offset,
        "form_bytes": form_size + 8,
        "form_type": form_type,
        "chunk_ids": chunk_ids,
        "chunk_manifest_sha256": sha256_value(chunks),
    }


def parse_djvu_structure(data: bytes) -> dict[str, Any]:
    """Walk one bundled DjVu IFF container and return a text-free manifest."""
    require(data[:4] == b"AT&T", "DjVu AT&T signature is missing")
    require(data[4:8] == b"FORM", "top-level DjVu FORM is missing")
    top_form_size = _u32(data, 8, "top-level FORM size")
    require(top_form_size + 12 == len(data), "top-level FORM size does not cover the source bytes")
    require(data[12:16] == b"DJVM", "source is not a bundled multipage DJVM document")
    require(data[16:20] == b"DIRM", "bundled DjVu directory chunk is missing")

    directory_bytes = _u32(data, 20, "DIRM size")
    directory_start = 24
    directory_end = directory_start + directory_bytes
    require(directory_end <= len(data), "DIRM payload exceeds source bytes")
    directory_payload = data[directory_start:directory_end]
    require(len(directory_payload) >= 3, "DIRM payload is truncated")
    directory_flags = directory_payload[0]
    component_count = _u16(directory_payload, 1, "DIRM component count")
    offsets_start = 3
    offsets_end = offsets_start + 4 * component_count
    require(offsets_end <= len(directory_payload), "DIRM component offset table is truncated")
    offsets = [
        _u32(directory_payload, offsets_start + 4 * index, f"DIRM component offset {index}")
        for index in range(component_count)
    ]
    require(offsets == sorted(set(offsets)), "DIRM component offsets are duplicated or out of order")
    first_component_offset = directory_end + (directory_bytes & 1)
    require(offsets and offsets[0] == first_component_offset, "DIRM first component offset drift")

    components = []
    for index, offset in enumerate(offsets):
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else len(data)
        components.append(_parse_component(data, index=index, offset=offset, next_offset=next_offset))

    form_type_counts = Counter(component["form_type"] for component in components)
    chunk_counts: Counter[str] = Counter()
    pages_with_embedded_text = 0
    for component in components:
        chunk_counts.update(component["chunk_ids"])
        if component["form_type"] == "DJVU" and any(
            chunk_id in {"TXTa", "TXTz"} for chunk_id in component["chunk_ids"]
        ):
            pages_with_embedded_text += 1

    component_identity_manifest = [
        {
            "component_index": component["component_index"],
            "offset": component["offset"],
            "form_bytes": component["form_bytes"],
            "form_type": component["form_type"],
            "chunk_ids": component["chunk_ids"],
            "chunk_manifest_sha256": component["chunk_manifest_sha256"],
        }
        for component in components
    ]
    return {
        "container_signature": "AT&T/FORM:DJVM",
        "top_form_size": top_form_size,
        "directory_bytes": directory_bytes,
        "directory_flags": directory_flags,
        "component_count": component_count,
        "page_components": form_type_counts["DJVU"],
        "shared_components": form_type_counts["DJVI"],
        "pages_with_embedded_text": pages_with_embedded_text,
        "chunk_counts": dict(sorted(chunk_counts.items())),
        "component_identity_manifest_sha256": sha256_value(component_identity_manifest),
        "container_fully_walked": True,
    }


def inspect_source(path: Path) -> dict[str, Any]:
    """Validate exact source identity and return its frozen container facts."""
    source = Path(path)
    require(source.is_file() and not source.is_symlink(), "source DjVu is missing or unsafe")
    require(source.name == SOURCE_FILENAME, "source filename drift")
    require(source.stat().st_size == SOURCE_BYTES, "source byte count drift")
    require(sha256_file(source) == SOURCE_SHA256, "source SHA-256 drift")
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise MiddleUkrainianActBookIntakeError(f"cannot read source DjVu: {exc}") from exc
    require(len(data) == SOURCE_BYTES, "source changed while reading")
    structure = parse_djvu_structure(data)
    expected = {
        "directory_flags": EXPECTED_DIRECTORY_FLAGS,
        "component_count": EXPECTED_COMPONENTS,
        "page_components": EXPECTED_PAGE_COMPONENTS,
        "shared_components": EXPECTED_SHARED_COMPONENTS,
        "pages_with_embedded_text": EXPECTED_PAGES_WITH_EMBEDDED_TEXT,
        "chunk_counts": EXPECTED_CHUNK_COUNTS,
    }
    require(
        {key: structure[key] for key in expected} == expected,
        "frozen DjVu structure denominator drift",
    )
    require(sha256_file(source) == SOURCE_SHA256, "source changed while inspecting")
    return structure


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianActBookIntakeError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be a JSON object")
    return value


def _receipt_body(*, structure: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "source": {
            "collection_id": COLLECTION_ID,
            "title": SOURCE_TITLE,
            "preparer": SOURCE_PREPARER,
            "publication_year": PUBLICATION_YEAR,
            "document_year_start": DOCUMENT_YEAR_START,
            "document_year_end": DOCUMENT_YEAR_END,
            "institutional_catalogue_url": INSTITUTIONAL_CATALOGUE_URL,
            "mirror_download_url": MIRROR_DOWNLOAD_URL,
            "filename": SOURCE_FILENAME,
            "bytes": SOURCE_BYTES,
            "sha256": SOURCE_SHA256,
            "format": "bundled_multipage_djvu",
        },
        "implementation": {
            "implementation_sha256": sha256_file(Path(__file__)),
            "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA_PATH),
            "parser": "bounded_iff_djvm_container_walker_no_text_decompression",
        },
        "container": dict(structure),
        "evidence_scope": {
            "official_catalogue_identity_verified": True,
            "source_bytes_privately_preserved": True,
            "direct_municipal_documentary_source_candidate": True,
            "documentary_genre": "zhytomyr_municipal_act_book",
            "geographic_scope": "zhytomyr",
            "historical_stage_assignment": "pending_qualified_historical_review",
            "representative_of_all_middle_ukrainian_varieties": False,
        },
        "rights_and_custody": {
            "storage": "private_google_drive",
            "nbuv_terms": "educational_and_scientific_noncommercial_with_attribution_no_downstream_full_text_reproduction",
            "mirror_rights_expression_verified": False,
            "private_research_and_source_evidence_only": True,
            "source_attribution_and_locator_preserved": True,
            "full_scan_public_redistribution_authorized": False,
            "full_text_public_redistribution_authorized": False,
            "training_export_authorized": False,
            "adapt_or_remove_on_substantiated_notice": True,
        },
        "safeguards": {
            "container_boundaries_verified": True,
            "embedded_text_chunks_detected_without_interpretation": True,
            "embedded_text_extracted": False,
            "text_layer_quality_verified": False,
            "inferred_character_repairs": False,
            "qualified_historical_review_complete": False,
            "semantic_gold": False,
            "training_eligible": False,
            "modern_correction_eligible": False,
            "public_repo_contains_source_text": False,
            "provider_calls": False,
            "phase3_complete": False,
            "phase4_authorized": False,
            "phase4_blocked": True,
        },
        "residuals": {
            "verified_djvu_text_extraction_required": True,
            "page_level_text_and_image_alignment_required": True,
            "qualified_historical_language_layer_review_required": True,
            "additional_middle_ukrainian_genres_and_regions_required": True,
            "middle_ukrainian_genre_and_region_gap_closed": False,
            "source_freeze_ready": False,
        },
        "text_free": True,
        "provider_calls": False,
    }


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianActBookIntakeError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise MiddleUkrainianActBookIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    require(
        receipt["container"]["component_count"]
        == receipt["container"]["page_components"] + receipt["container"]["shared_components"],
        "component denominator does not close",
    )
    require(
        receipt["container"]["pages_with_embedded_text"] == receipt["container"]["chunk_counts"]["TXTz"],
        "embedded text denominator does not close",
    )


def materialize_intake(*, source_path: Path, private_output_dir: Path) -> dict[str, Any]:
    """Write one immutable, text-free receipt beside the privately held source."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private receipt cannot be written inside Git")
    require(not output_dir.is_symlink(), "private output directory cannot be a symbolic link")
    require(not output_dir.exists(), "immutable private output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    require(output_dir.parent.is_dir() and not output_dir.parent.is_symlink(), "private output parent is unsafe")

    structure = inspect_source(source_path)
    receipt_body = _receipt_body(structure=structure)
    receipt = {**receipt_body, "receipt_sha256": sha256_value(receipt_body)}
    _validate_receipt(receipt)

    staged_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    staged_receipt = staged_dir / RECEIPT_FILENAME
    try:
        staged_receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_existing_intake(source_path=source_path, private_output_dir=staged_dir)
        os.replace(staged_dir, output_dir)
    finally:
        if staged_dir.exists():
            if staged_receipt.exists():
                staged_receipt.unlink()
            staged_dir.rmdir()
    validate_existing_intake(source_path=source_path, private_output_dir=output_dir)
    return receipt


def validate_existing_intake(*, source_path: Path, private_output_dir: Path) -> dict[str, Any]:
    """Rebuild the receipt from current source, schema, and implementation bytes."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private receipt cannot be read from inside Git")
    receipt_path = output_dir / RECEIPT_FILENAME
    receipt = _load_json_object(receipt_path, description="Middle Ukrainian act-book intake receipt")
    _validate_receipt(receipt)
    structure = inspect_source(source_path)
    rebuilt_body = _receipt_body(structure=structure)
    rebuilt = {**rebuilt_body, "receipt_sha256": sha256_value(rebuilt_body)}
    require(receipt == rebuilt, "receipt does not reproduce from current source and code")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_sha256": SOURCE_SHA256,
        "page_components": structure["page_components"],
        "pages_with_embedded_text": structure["pages_with_embedded_text"],
        "receipt_file_sha256": sha256_file(receipt_path),
        "receipt_sha256": receipt["receipt_sha256"],
        "text_layer_quality_verified": False,
        "training_eligible": False,
        "phase3_complete": False,
        "phase4_blocked": True,
        "provider_calls": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("materialize", "validate"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--source", type=Path, required=True)
        subparser.add_argument("--private-output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize_intake(source_path=args.source, private_output_dir=args.private_output_dir)
    else:
        result = validate_existing_intake(source_path=args.source, private_output_dir=args.private_output_dir)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
