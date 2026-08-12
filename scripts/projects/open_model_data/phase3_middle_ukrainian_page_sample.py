#!/usr/bin/env python3
"""Build a private, source-bound review packet for Middle Ukrainian page text.

The packet pairs deterministic full-resolution page renders with the exact
embedded-text rows already frozen by the predecessor extraction.  It prepares
evidence for qualified review; it does not perform or claim that review.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import html
import json
import os
import shutil
import stat
import struct
import subprocess
import tempfile
import zlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_middle_ukrainian_text_extraction as extraction
from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value

ROOT = Path(__file__).resolve().parents[3]
RENDERER_PATH = ROOT / "scripts/projects/open_model_data/phase3_middle_ukrainian_page_sample_render.js"
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_middle_ukrainian_page_sample_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_middle_ukrainian_page_sample_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_middle_ukrainian_page_sample_v1"
SELECTED_JSONL_FILENAME = "selected-page-text-private-v1.jsonl"
REVIEW_HTML_FILENAME = "page-text-review-private-v1.html"
REVIEW_TEMPLATE_FILENAME = "page-text-review-response-template-private-v1.json"
RECEIPT_FILENAME = "middle-ukrainian-page-sample-receipt-v1.json"
IMAGE_DIRECTORY_NAME = "page-images"

EXTRACTION_RECEIPT_FILE_SHA256 = "dba0513079203fafbba48faf88112fba533ad706217ef12b8d52bae090f37bdf"
EXTRACTION_RECEIPT_SHA256 = "defe03ac154e4184d29f60266dbcd9eeed217c189f7fd88832afa50b021f7496"
EXTRACTION_PRIVATE_JSONL_SHA256 = "6368ab7308dc579a324ba29c233d7218e1a0735d127812f8b34e16cca49f4f0a"

PAGE_SELECTION: tuple[dict[str, Any], ...] = (
    {"page_number": 1, "reasons": ["front_matter_cover", "low_density_anchor"]},
    {"page_number": 2, "reasons": ["front_matter_title", "low_density_anchor"]},
    {"page_number": 3, "reasons": ["missing_text_layer", "front_matter_anchor"]},
    {"page_number": 4, "reasons": ["front_matter_anchor", "low_density_anchor"]},
    {"page_number": 20, "reasons": ["systematic_interval_20"]},
    {"page_number": 40, "reasons": ["systematic_interval_20"]},
    {"page_number": 60, "reasons": ["systematic_interval_20"]},
    {"page_number": 80, "reasons": ["systematic_interval_20"]},
    {"page_number": 100, "reasons": ["systematic_interval_20"]},
    {"page_number": 120, "reasons": ["systematic_interval_20"]},
    {"page_number": 140, "reasons": ["systematic_interval_20"]},
    {"page_number": 160, "reasons": ["systematic_interval_20"]},
    {"page_number": 163, "reasons": ["maximum_codepoint_density"]},
    {"page_number": 180, "reasons": ["systematic_interval_20"]},
    {"page_number": 195, "reasons": ["late_low_density_anchor"]},
    {"page_number": 196, "reasons": ["missing_text_layer", "alternate_geometry", "terminal_page"]},
)
SELECTED_PAGES = tuple(item["page_number"] for item in PAGE_SELECTION)


class MiddleUkrainianPageSampleError(ValueError):
    """A source, render, packet, replay, or safety invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MiddleUkrainianPageSampleError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _exact_regular_file(path: Path, *, label: str) -> None:
    candidate = Path(path)
    require(candidate.is_file() and not candidate.is_symlink(), f"{label} is missing or unsafe")
    require(stat.S_IMODE(candidate.stat().st_mode) == 0o600, f"{label} permissions drift")


def _exact_private_directory(path: Path, *, label: str) -> None:
    candidate = Path(path)
    require(candidate.is_dir() and not candidate.is_symlink(), f"{label} is missing or unsafe")
    require(stat.S_IMODE(candidate.stat().st_mode) == 0o700, f"{label} permissions drift")


def _write_private(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _validate_predecessor(
    *,
    source_path: Path,
    raw_intake_dir: Path,
    extraction_dir: Path,
) -> dict[str, Any]:
    summary = extraction.validate_existing_extraction(
        source_path=source_path,
        raw_intake_dir=raw_intake_dir,
        private_output_dir=extraction_dir,
    )
    require(
        summary["receipt_file_sha256"] == EXTRACTION_RECEIPT_FILE_SHA256,
        "predecessor extraction receipt file SHA-256 drift",
    )
    require(summary["receipt_sha256"] == EXTRACTION_RECEIPT_SHA256, "predecessor extraction self-hash drift")
    require(
        summary["private_jsonl_sha256"] == EXTRACTION_PRIVATE_JSONL_SHA256,
        "predecessor private JSONL SHA-256 drift",
    )
    return summary


def _load_source_rows(extraction_dir: Path) -> tuple[list[dict[str, Any]], list[bytes]]:
    source_jsonl = Path(extraction_dir) / extraction.PRIVATE_JSONL_FILENAME
    _exact_regular_file(source_jsonl, label="predecessor private page-text JSONL")
    require(sha256_file(source_jsonl) == EXTRACTION_PRIVATE_JSONL_SHA256, "predecessor private JSONL drift")
    lines = source_jsonl.read_bytes().splitlines(keepends=True)
    require(len(lines) == extraction.EXPECTED_PAGES, "predecessor page denominator drift")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        require(line.endswith(b"\n"), f"predecessor line {line_number} lacks newline termination")
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MiddleUkrainianPageSampleError(f"predecessor line {line_number} is invalid JSON") from exc
        require(isinstance(row, dict), f"predecessor row {line_number} is not an object")
        require(row.get("page_number") == line_number, f"predecessor page sequence drift at {line_number}")
        rows.append(row)
    return rows, lines


def _validate_selection(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    require(len(rows) == extraction.EXPECTED_PAGES, "source row denominator drift")
    require(tuple(sorted(set(SELECTED_PAGES))) == SELECTED_PAGES, "page selection is not unique and ordered")
    require(SELECTED_PAGES[:4] == (1, 2, 3, 4), "front-matter selection drift")
    require(tuple(range(20, 181, 20)) == tuple(page for page in SELECTED_PAGES if page % 20 == 0), "interval selection drift")
    max_density = max(rows, key=lambda row: int(row["decoded_text_code_points"]))
    require(max_density["page_number"] == 163, "maximum-density source fact drift")
    require(not rows[2]["text_layer_present"] and not rows[195]["text_layer_present"], "missing-layer anchors drift")
    require(rows[195]["page_width"] != rows[0]["page_width"], "alternate-geometry anchor drift")

    selected: list[dict[str, Any]] = []
    reasons_by_page = {item["page_number"]: list(item["reasons"]) for item in PAGE_SELECTION}
    for page_number in SELECTED_PAGES:
        row = rows[page_number - 1]
        selected.append(
            {
                "page_number": page_number,
                "reasons": reasons_by_page[page_number],
                "text_layer_present": row["text_layer_present"],
                "decoded_text_code_points": row["decoded_text_code_points"],
                "decoded_text_utf8_bytes": row["decoded_text_utf8_bytes"],
                "text_zone_count": row["text_zone_count"],
                "page_width": row["page_width"],
                "page_height": row["page_height"],
                "dpi": row["dpi"],
                "rotation": row["rotation"],
                "decoded_text_sha256": row["decoded_text_sha256"],
                "text_zones_sha256": row["text_zones_sha256"],
            }
        )
    require(sum(bool(item["text_layer_present"]) for item in selected) == 14, "selected text-layer count drift")
    return selected


def _invoke_renderer(
    *,
    source_path: Path,
    decoder_path: Path,
    image_directory: Path,
) -> dict[str, Any]:
    node = shutil.which("node")
    require(node is not None, "Node.js is required for pinned DjVu page rendering")
    command = [
        node,
        str(RENDERER_PATH),
        "--source",
        str(source_path),
        "--decoder",
        str(decoder_path),
        "--output-dir",
        str(image_directory),
        "--pages",
        ",".join(str(page) for page in SELECTED_PAGES),
        "--expected-source-sha256",
        extraction.intake.SOURCE_SHA256,
        "--expected-source-bytes",
        str(extraction.intake.SOURCE_BYTES),
        "--expected-decoder-sha256",
        extraction.DECODER_SHA256,
        "--expected-decoder-version",
        extraction.DECODER_VERSION,
        "--expected-pages",
        str(extraction.EXPECTED_PAGES),
    ]
    environment = dict(os.environ)
    environment["NODE_NO_WARNINGS"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MiddleUkrainianPageSampleError(f"page-render transport failed: {exc}") from exc
    require(completed.returncode == 0, f"page render failed: {completed.stderr.strip()}")
    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MiddleUkrainianPageSampleError("page renderer emitted invalid summary JSON") from exc
    require(isinstance(summary, dict), "page renderer summary must be an object")
    return summary


def _validate_png(path: Path, *, expected_width: int, expected_height: int) -> dict[str, Any]:
    _exact_regular_file(path, label=f"page image {path.name}")
    payload = path.read_bytes()
    require(payload.startswith(b"\x89PNG\r\n\x1a\n"), f"page image {path.name} lacks PNG signature")
    offset = 8
    chunks: list[tuple[bytes, bytes]] = []
    while offset < len(payload):
        require(offset + 12 <= len(payload), f"page image {path.name} has a truncated chunk")
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        end = offset + 12 + length
        require(end <= len(payload), f"page image {path.name} has an invalid chunk length")
        data = payload[offset + 8 : offset + 8 + length]
        recorded_crc = struct.unpack(">I", payload[offset + 8 + length : end])[0]
        require(
            recorded_crc == (binascii.crc32(chunk_type + data) & 0xFFFFFFFF),
            f"page image {path.name} CRC drift",
        )
        chunks.append((chunk_type, data))
        offset = end
    require(offset == len(payload), f"page image {path.name} trailing bytes drift")
    require([chunk_type for chunk_type, _data in chunks] == [b"IHDR", b"IDAT", b"IEND"], f"page image {path.name} chunk structure drift")
    header = chunks[0][1]
    require(len(header) == 13, f"page image {path.name} IHDR drift")
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", header)
    require((width, height) == (expected_width, expected_height), f"page image {path.name} geometry drift")
    require((bit_depth, color_type, compression, filter_method, interlace) == (8, 6, 0, 0, 0), f"page image {path.name} encoding drift")
    try:
        scanlines = zlib.decompress(chunks[1][1])
    except zlib.error as exc:
        raise MiddleUkrainianPageSampleError(f"page image {path.name} IDAT is invalid") from exc
    row_bytes = width * 4
    require(len(scanlines) == height * (row_bytes + 1), f"page image {path.name} scanline length drift")
    rgba_digest = hashlib.sha256()
    for row_index in range(height):
        offset = row_index * (row_bytes + 1)
        require(scanlines[offset] == 0, f"page image {path.name} filter drift")
        rgba_digest.update(scanlines[offset + 1 : offset + 1 + row_bytes])
    return {
        "filename": path.name,
        "width": width,
        "height": height,
        "rgba_bytes": width * height * 4,
        "rgba_sha256": rgba_digest.hexdigest(),
        "png_bytes": len(payload),
        "png_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _validate_images(
    image_directory: Path,
    *,
    selected_metadata: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    _exact_private_directory(image_directory, label="page image directory")
    expected_filenames = {f"page-{int(item['page_number']):03d}.png" for item in selected_metadata}
    require({path.name for path in image_directory.iterdir()} == expected_filenames, "page image set drift")
    images: list[dict[str, Any]] = []
    for item in selected_metadata:
        page_number = int(item["page_number"])
        image = _validate_png(
            image_directory / f"page-{page_number:03d}.png",
            expected_width=int(item["page_width"]),
            expected_height=int(item["page_height"]),
        )
        images.append(
            {
                "page_number": page_number,
                **image,
                "dpi": int(item["dpi"]),
                "rotation": int(item["rotation"]),
            }
        )
    return images


def _review_template(selected_metadata: Sequence[Mapping[str, Any]], images: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    image_by_page = {int(item["page_number"]): item for item in images}
    return {
        "schema_version": "phase3_middle_ukrainian_page_sample_review_response_template_v1",
        "packet_scope": {
            "source_sha256": extraction.intake.SOURCE_SHA256,
            "source_text_jsonl_sha256": EXTRACTION_PRIVATE_JSONL_SHA256,
            "selection_method": "content_blind_structural_interval_and_density_anchors",
            "selected_pages": list(SELECTED_PAGES),
        },
        "reviewer": {
            "reviewer_id": "",
            "qualification": "unfilled",
            "affiliation_or_independent_status": "",
            "reviewed_at_utc": "",
        },
        "instructions": {
            "copy_template_before_editing": True,
            "compare_full_page_image_to_exact_embedded_text": True,
            "do_not_modernize_historical_forms": True,
            "record_uncertain_instead_of_guessing": True,
            "page_pass_does_not_assign_historical_stage_or_training_eligibility": True,
        },
        "pages": [
            {
                "page_number": int(item["page_number"]),
                "image_filename": image_by_page[int(item["page_number"])]["filename"],
                "image_png_sha256": image_by_page[int(item["page_number"])]["png_sha256"],
                "decoded_text_sha256": item["decoded_text_sha256"],
                "text_zones_sha256": item["text_zones_sha256"],
                "visual_text_presence": "pending",
                "character_fidelity": "pending",
                "word_order": "pending",
                "line_break_and_whitespace_fidelity": "pending",
                "zone_alignment": "pending",
                "historical_forms_preserved": "pending",
                "observed_error_count": None,
                "error_examples": [],
                "reviewer_notes": "",
            }
            for item in selected_metadata
        ],
        "overall": {
            "sample_review_status": "pending",
            "embedded_text_quality_disposition": "pending",
            "known_limitations": [],
            "recommended_next_action": "pending",
            "reviewer_rationale": "",
        },
    }


def _review_html(rows: Sequence[Mapping[str, Any]], selected_metadata: Sequence[Mapping[str, Any]]) -> str:
    metadata_by_page = {int(item["page_number"]): item for item in selected_metadata}
    cards: list[str] = []
    for row in rows:
        page_number = int(row["page_number"])
        item = metadata_by_page[page_number]
        cards.append(
            "\n".join(
                [
                    f'<section id="page-{page_number:03d}">',
                    f"<h2>Source page {page_number}</h2>",
                    (
                        "<p class=\"meta\">Selection: "
                        + html.escape(", ".join(item["reasons"]))
                        + f" · text layer: {str(item['text_layer_present']).lower()}"
                        + f" · code points: {item['decoded_text_code_points']}"
                        + f" · zones: {item['text_zone_count']}</p>"
                    ),
                    '<div class="pair">',
                    f'<img src="{IMAGE_DIRECTORY_NAME}/page-{page_number:03d}.png" alt="Rendered source page {page_number}">',
                    '<div class="text-panel">',
                    "<h3>Exact embedded text</h3>",
                    f"<pre lang=\"uk\">{html.escape(str(row['decoded_text']))}</pre>",
                    "</div>",
                    "</div>",
                    "</section>",
                ]
            )
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\'; style-src \'unsafe-inline\'">',
            "<title>Private Middle Ukrainian page-text review packet</title>",
            "<style>body{font:16px/1.45 system-ui,sans-serif;margin:2rem;background:#f7f5ef;color:#171717}"
            "h1{max-width:70rem}section{margin:3rem 0;padding-top:1rem;border-top:2px solid #999}"
            ".pair{display:grid;grid-template-columns:minmax(20rem,1fr) minmax(20rem,1fr);gap:1.5rem;align-items:start}"
            "img{width:100%;height:auto;background:white}pre{white-space:pre-wrap;word-break:break-word;background:white;padding:1rem;max-height:90vh;overflow:auto}"
            ".meta,.warning{max-width:75rem}.warning{padding:1rem;background:#fff3cd;border:1px solid #d6b656}"
            "@media(max-width:900px){.pair{grid-template-columns:1fr}}</style></head><body>",
            "<h1>Private Middle Ukrainian page-text review packet</h1>",
            '<p class="warning">Private research evidence. Do not redistribute. Copy the response template before editing. Compare image and text faithfully; do not modernize historical forms and mark uncertainty instead of guessing. This packet does not authorize training, source freeze, Phase 3 completion, or Phase 4.</p>',
            *cards,
            "</body></html>\n",
        ]
    )


def _packet_files_summary(
    *,
    selected_jsonl: Path,
    review_html: Path,
    review_template: Path,
    images: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "selected_text": {
            "filename": SELECTED_JSONL_FILENAME,
            "bytes": selected_jsonl.stat().st_size,
            "sha256": sha256_file(selected_jsonl),
            "rows": len(SELECTED_PAGES),
        },
        "review_html": {
            "filename": REVIEW_HTML_FILENAME,
            "bytes": review_html.stat().st_size,
            "sha256": sha256_file(review_html),
        },
        "review_response_template": {
            "filename": REVIEW_TEMPLATE_FILENAME,
            "bytes": review_template.stat().st_size,
            "sha256": sha256_file(review_template),
        },
        "image_directory": IMAGE_DIRECTORY_NAME,
        "image_count": len(images),
        "total_png_bytes": sum(int(image["png_bytes"]) for image in images),
        "images": list(images),
    }


def _receipt_body(
    *,
    selected_metadata: Sequence[Mapping[str, Any]],
    packet_files: Mapping[str, Any],
    renderer_summary: Mapping[str, Any],
) -> dict[str, Any]:
    sample_text_layer_pages = sum(bool(item["text_layer_present"]) for item in selected_metadata)
    return {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "source_binding": {
            "collection_id": extraction.intake.COLLECTION_ID,
            "source_filename": extraction.intake.SOURCE_FILENAME,
            "source_bytes": extraction.intake.SOURCE_BYTES,
            "source_sha256": extraction.intake.SOURCE_SHA256,
            "predecessor_extraction_receipt_file_sha256": EXTRACTION_RECEIPT_FILE_SHA256,
            "predecessor_extraction_receipt_sha256": EXTRACTION_RECEIPT_SHA256,
            "predecessor_private_jsonl_sha256": EXTRACTION_PRIVATE_JSONL_SHA256,
        },
        "decoder_binding": {
            "project": "DjVu.js",
            "release_tag": extraction.DECODER_RELEASE_TAG,
            "asset_url": extraction.DECODER_ASSET_URL,
            "version": extraction.DECODER_VERSION,
            "bytes": extraction.DECODER_BYTES,
            "sha256": extraction.DECODER_SHA256,
            "decoder_binary_copied_to_output": False,
            "decoder_license_expression_verified": False,
            "execution_tool_only_not_source_authority": True,
        },
        "implementation_binding": {
            "controller_sha256": sha256_file(Path(__file__)),
            "renderer_sha256": sha256_file(RENDERER_PATH),
            "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA_PATH),
        },
        "selection": {
            "method": "content_blind_structural_interval_and_density_anchors",
            "complete_source_pages": extraction.EXPECTED_PAGES,
            "complete_text_layer_pages": extraction.EXPECTED_TEXT_LAYER_PAGES,
            "sample_pages": len(SELECTED_PAGES),
            "sample_text_layer_pages": sample_text_layer_pages,
            "sample_missing_text_layer_pages": len(SELECTED_PAGES) - sample_text_layer_pages,
            "selected_pages": list(SELECTED_PAGES),
            "samples": list(selected_metadata),
            "semantic_representativeness_claimed": False,
            "random_sampling_used": False,
        },
        "rendering": {
            "method": "pinned_djvujs_getImageData_node_zlib_png",
            "full_resolution": True,
            "lossless_png": True,
            "rgba_bit_depth": 8,
            "png_color_type": 6,
            "png_filter": 0,
            "png_interlaced": False,
            "zlib_level": 9,
            "node_version": renderer_summary["node_version"],
            "zlib_version": renderer_summary["zlib_version"],
            "ocr_used": False,
            "normalization_applied": False,
            "inferred_character_repairs": False,
        },
        "private_packet": {
            "storage": "private_google_drive",
            **dict(packet_files),
        },
        "review_contract": {
            "packet_ready_for_qualified_review": True,
            "review_response_status": "pending",
            "qualified_reviewer_identified": False,
            "visual_text_image_alignment_quality_verified": False,
            "embedded_text_quality_verified": False,
            "historical_language_fidelity_verified": False,
            "document_level_stage_assignment_verified": False,
        },
        "rights_and_custody": {
            "source_and_packet_storage": "private_google_drive",
            "private_research_and_source_evidence_only": True,
            "public_repo_contains_source_text_or_page_images": False,
            "public_redistribution_authorized": False,
            "training_export_authorized": False,
            "adapt_or_remove_on_substantiated_notice": True,
        },
        "safeguards": {
            "semantic_gold": False,
            "training_eligible": False,
            "modern_correction_eligible": False,
            "provider_calls": False,
            "source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_authorized": False,
            "phase4_blocked": True,
        },
        "residuals": {
            "qualified_page_sample_review_required": True,
            "qualified_historical_language_review_required": True,
            "review_response_must_be_separate_and_immutable": True,
            "additional_middle_ukrainian_regions_and_genres_required": True,
            "middle_ukrainian_coverage_gap_closed": False,
        },
        "text_free": True,
        "provider_calls": False,
    }


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    try:
        schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianPageSampleError("cannot read page-sample receipt schema") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda item: tuple(f"{type(part).__name__}:{part}" for part in item.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise MiddleUkrainianPageSampleError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")


def _validate_renderer_summary(summary: Mapping[str, Any], images: Sequence[Mapping[str, Any]]) -> None:
    require(summary.get("source_sha256") == extraction.intake.SOURCE_SHA256, "renderer source drift")
    require(summary.get("decoder_version") == extraction.DECODER_VERSION, "renderer decoder drift")
    require(summary.get("page_selection") == list(SELECTED_PAGES), "renderer page selection drift")
    require(summary.get("provider_calls") is False, "renderer provider-call drift")
    require(summary.get("image_count") == len(images), "renderer image count drift")
    require(summary.get("total_png_bytes") == sum(int(image["png_bytes"]) for image in images), "renderer byte total drift")
    require(summary.get("images") == list(images), "renderer image manifest does not replay")
    require(isinstance(summary.get("node_version"), str) and summary["node_version"], "renderer Node version missing")
    require(isinstance(summary.get("zlib_version"), str) and summary["zlib_version"], "renderer zlib version missing")


def materialize_page_sample(
    *,
    source_path: Path,
    raw_intake_dir: Path,
    extraction_dir: Path,
    decoder_path: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Write one immutable private page-image/text review packet."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private page sample cannot be written inside Git")
    require(not output_dir.exists() and not output_dir.is_symlink(), "immutable private output already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    require(output_dir.parent.is_dir() and not output_dir.parent.is_symlink(), "private output parent is unsafe")
    _validate_predecessor(source_path=source_path, raw_intake_dir=raw_intake_dir, extraction_dir=extraction_dir)
    extraction._validate_decoder(decoder_path)
    rows, source_lines = _load_source_rows(extraction_dir)
    selected_metadata = _validate_selection(rows)
    selected_rows = [rows[page - 1] for page in SELECTED_PAGES]
    selected_lines = b"".join(source_lines[page - 1] for page in SELECTED_PAGES)

    staged_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    image_directory = staged_dir / IMAGE_DIRECTORY_NAME
    image_directory.mkdir(mode=0o700)
    selected_jsonl = staged_dir / SELECTED_JSONL_FILENAME
    review_html_path = staged_dir / REVIEW_HTML_FILENAME
    review_template_path = staged_dir / REVIEW_TEMPLATE_FILENAME
    receipt_path = staged_dir / RECEIPT_FILENAME
    try:
        _write_private(selected_jsonl, selected_lines)
        renderer_summary = _invoke_renderer(
            source_path=source_path,
            decoder_path=decoder_path,
            image_directory=image_directory,
        )
        images = _validate_images(image_directory, selected_metadata=selected_metadata)
        _validate_renderer_summary(renderer_summary, images)
        template = _review_template(selected_metadata, images)
        _write_private(
            review_template_path,
            (json.dumps(template, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        _write_private(review_html_path, _review_html(selected_rows, selected_metadata).encode("utf-8"))
        packet_files = _packet_files_summary(
            selected_jsonl=selected_jsonl,
            review_html=review_html_path,
            review_template=review_template_path,
            images=images,
        )
        receipt_body = _receipt_body(
            selected_metadata=selected_metadata,
            packet_files=packet_files,
            renderer_summary=renderer_summary,
        )
        receipt = {**receipt_body, "receipt_sha256": sha256_value(receipt_body)}
        _validate_receipt(receipt)
        _write_private(
            receipt_path,
            (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        validate_existing_page_sample(
            source_path=source_path,
            raw_intake_dir=raw_intake_dir,
            extraction_dir=extraction_dir,
            private_output_dir=staged_dir,
        )
        os.replace(staged_dir, output_dir)
    finally:
        if staged_dir.exists():
            shutil.rmtree(staged_dir)
    return validate_existing_page_sample(
        source_path=source_path,
        raw_intake_dir=raw_intake_dir,
        extraction_dir=extraction_dir,
        private_output_dir=output_dir,
    )


def validate_existing_page_sample(
    *,
    source_path: Path,
    raw_intake_dir: Path,
    extraction_dir: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Replay a private packet without returning or printing source text."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private page sample cannot be read from inside Git")
    _exact_private_directory(output_dir, label="private page-sample directory")
    expected_root = {
        SELECTED_JSONL_FILENAME,
        REVIEW_HTML_FILENAME,
        REVIEW_TEMPLATE_FILENAME,
        RECEIPT_FILENAME,
        IMAGE_DIRECTORY_NAME,
    }
    require({path.name for path in output_dir.iterdir()} == expected_root, "private page-sample contents drift")
    _validate_predecessor(source_path=source_path, raw_intake_dir=raw_intake_dir, extraction_dir=extraction_dir)
    rows, source_lines = _load_source_rows(extraction_dir)
    selected_metadata = _validate_selection(rows)
    selected_rows = [rows[page - 1] for page in SELECTED_PAGES]

    selected_jsonl = output_dir / SELECTED_JSONL_FILENAME
    _exact_regular_file(selected_jsonl, label="selected private page text")
    require(
        selected_jsonl.read_bytes() == b"".join(source_lines[page - 1] for page in SELECTED_PAGES),
        "selected private page text does not reproduce from predecessor",
    )
    images = _validate_images(output_dir / IMAGE_DIRECTORY_NAME, selected_metadata=selected_metadata)
    review_template_path = output_dir / REVIEW_TEMPLATE_FILENAME
    _exact_regular_file(review_template_path, label="private review response template")
    expected_template = json.dumps(
        _review_template(selected_metadata, images), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    require(review_template_path.read_text(encoding="utf-8") == expected_template, "review response template drift")
    review_html_path = output_dir / REVIEW_HTML_FILENAME
    _exact_regular_file(review_html_path, label="private review HTML")
    require(review_html_path.read_text(encoding="utf-8") == _review_html(selected_rows, selected_metadata), "review HTML drift")

    receipt_path = output_dir / RECEIPT_FILENAME
    _exact_regular_file(receipt_path, label="page-sample receipt")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianPageSampleError("cannot read page-sample receipt") from exc
    require(isinstance(receipt, dict), "page-sample receipt must be an object")
    _validate_receipt(receipt)
    packet_files = _packet_files_summary(
        selected_jsonl=selected_jsonl,
        review_html=review_html_path,
        review_template=review_template_path,
        images=images,
    )
    renderer_facts = {
        "node_version": receipt["rendering"]["node_version"],
        "zlib_version": receipt["rendering"]["zlib_version"],
    }
    body = _receipt_body(
        selected_metadata=selected_metadata,
        packet_files=packet_files,
        renderer_summary=renderer_facts,
    )
    rebuilt = {**body, "receipt_sha256": sha256_value(body)}
    require(receipt == rebuilt, "page-sample receipt does not reproduce from current inputs")
    sample_text_layer_pages = sum(bool(item["text_layer_present"]) for item in selected_metadata)
    return {
        "schema_version": SCHEMA_VERSION,
        "source_sha256": extraction.intake.SOURCE_SHA256,
        "sample_pages": len(SELECTED_PAGES),
        "sample_text_layer_pages": sample_text_layer_pages,
        "sample_missing_text_layer_pages": len(SELECTED_PAGES) - sample_text_layer_pages,
        "selected_text_sha256": packet_files["selected_text"]["sha256"],
        "total_png_bytes": packet_files["total_png_bytes"],
        "receipt_file_sha256": sha256_file(receipt_path),
        "receipt_sha256": receipt["receipt_sha256"],
        "packet_ready_for_qualified_review": True,
        "review_response_status": "pending",
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
        subparser.add_argument("--raw-intake-dir", type=Path, required=True)
        subparser.add_argument("--extraction-dir", type=Path, required=True)
        subparser.add_argument("--private-output-dir", type=Path, required=True)
        if command == "materialize":
            subparser.add_argument("--decoder", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize_page_sample(
            source_path=args.source,
            raw_intake_dir=args.raw_intake_dir,
            extraction_dir=args.extraction_dir,
            decoder_path=args.decoder,
            private_output_dir=args.private_output_dir,
        )
    else:
        result = validate_existing_page_sample(
            source_path=args.source,
            raw_intake_dir=args.raw_intake_dir,
            extraction_dir=args.extraction_dir,
            private_output_dir=args.private_output_dir,
        )
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
