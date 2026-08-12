#!/usr/bin/env python3
"""Materialize exact page-aligned DjVu text as private Phase 3 evidence.

The source-specific controller validates the prior raw-intake receipt, exact
source bytes, pinned decoder bytes, deterministic page/zone denominators, and
an immutable private JSONL identity.  It does not perform OCR, normalize or
repair decoded text, admit training rows, or authorize Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_middle_ukrainian_act_book_intake as intake
from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value

ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "scripts/projects/open_model_data/phase3_middle_ukrainian_djvu_extract.js"
RECEIPT_SCHEMA_PATH = (
    ROOT
    / "data/projects/open_model_data/contracts/phase3_middle_ukrainian_text_extraction_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_middle_ukrainian_text_extraction_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_middle_ukrainian_text_extraction_v1"
ROW_SCHEMA_VERSION = "phase3_middle_ukrainian_page_text_private_v1"
PRIVATE_JSONL_FILENAME = "middle-ukrainian-page-text-private-v1.jsonl"
RECEIPT_FILENAME = "middle-ukrainian-text-extraction-receipt-v1.json"

DECODER_RELEASE_TAG = "L.0.5.4_V.0.10.1"
DECODER_RELEASE_URL = f"https://github.com/RussCoder/djvujs/releases/tag/{DECODER_RELEASE_TAG}"
DECODER_ASSET_URL = f"https://github.com/RussCoder/djvujs/releases/download/{DECODER_RELEASE_TAG}/djvu.js"
DECODER_VERSION = "0.5.4"
DECODER_BYTES = 556_634
DECODER_SHA256 = "10a831d62cc7ced39c30c7350a11410402d082a0f0a5b073a88d3d7ca662add3"

EXPECTED_PAGES = 196
EXPECTED_TEXT_LAYER_PAGES = 194
EXPECTED_NONEMPTY_TEXT_PAGES = 194
EXPECTED_TOTAL_CODE_POINTS = 475_094
EXPECTED_TOTAL_UTF8_BYTES = 811_825
EXPECTED_TOTAL_ZONES = 70_566
EXPECTED_PRIVATE_JSONL_BYTES = 5_514_409
EXPECTED_PRIVATE_JSONL_SHA256 = "6368ab7308dc579a324ba29c233d7218e1a0735d127812f8b34e16cca49f4f0a"
EXPECTED_PAGE_TEXT_HASH_MANIFEST_SHA256 = "fbf074151e7fe74937c6112c2fbdb8d51a39241b2bc6a1bc5c042a13411a61f7"
EXPECTED_TEXT_ZONE_HASH_MANIFEST_SHA256 = "636ca07572f07b7e95f67cc2946777834f62af9e2a99618cf5036a70a1d45c78"
EXPECTED_PAGE_GEOMETRY_MANIFEST_SHA256 = "5292b823c7e53868151704153d382b190cedac91a035cbcc240b4d0328358a43"
EXPECTED_GEOMETRY_COUNTS = {
    "3594x4980@600r0": 195,
    "4356x4980@600r0": 1,
}
RAW_INTAKE_RECEIPT_FILE_SHA256 = "16a9919e254817a246c3c0b368bf71fcb310bf0a2ed00e6aa6f9cc26cc72dc6d"
RAW_INTAKE_RECEIPT_SHA256 = "5adb31db0f7542f6d3a4d7e0fca1e7dd08628ecdcd0ac0ba61a5fcddad2a7d36"

PRIVATE_ROW_KEYS = {
    "schema_version",
    "source_sha256",
    "page_number",
    "page_width",
    "page_height",
    "dpi",
    "rotation",
    "text_layer_present",
    "decoded_text",
    "decoded_text_sha256",
    "decoded_text_code_points",
    "decoded_text_utf8_bytes",
    "text_zones",
    "text_zones_sha256",
    "text_zone_count",
    "ocr_used",
    "normalization_applied",
    "inferred_character_repairs",
}
ZONE_KEYS = {"x", "y", "width", "height", "text"}


class MiddleUkrainianTextExtractionError(ValueError):
    """A source, decoder, private-output, replay, or safety invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MiddleUkrainianTextExtractionError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_compact_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _exact_regular_file(path: Path, *, label: str, expected_bytes: int, expected_sha256: str) -> None:
    candidate = Path(path)
    require(candidate.is_file() and not candidate.is_symlink(), f"{label} is missing or unsafe")
    require(candidate.stat().st_size == expected_bytes, f"{label} byte count drift")
    require(sha256_file(candidate) == expected_sha256, f"{label} SHA-256 drift")


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{label} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianTextExtractionError(f"cannot read {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _int_value(value: Any, *, label: str, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{label} must be an integer")
    require(value >= minimum, f"{label} is below its minimum")
    return value


def _validate_zone(
    zone: Any,
    *,
    page_number: int,
    zone_index: int,
    page_width: int,
    page_height: int,
) -> None:
    require(isinstance(zone, dict) and set(zone) == ZONE_KEYS, f"page {page_number} zone {zone_index} shape drift")
    x = _int_value(zone["x"], label=f"page {page_number} zone {zone_index} x")
    y = _int_value(zone["y"], label=f"page {page_number} zone {zone_index} y")
    width = _int_value(zone["width"], label=f"page {page_number} zone {zone_index} width")
    height = _int_value(zone["height"], label=f"page {page_number} zone {zone_index} height")
    require(isinstance(zone["text"], str), f"page {page_number} zone {zone_index} text must be a string")
    require(x + width <= page_width and y + height <= page_height, f"page {page_number} zone exceeds bounds")


def validate_private_jsonl(path: Path) -> dict[str, Any]:
    """Validate every private row without returning or printing source text."""
    private_path = Path(path)
    _exact_regular_file(
        private_path,
        label="private page-text JSONL",
        expected_bytes=EXPECTED_PRIVATE_JSONL_BYTES,
        expected_sha256=EXPECTED_PRIVATE_JSONL_SHA256,
    )
    text_hashes: list[str] = []
    zone_hashes: list[str] = []
    geometry_manifest: list[dict[str, int]] = []
    geometry_counts: Counter[str] = Counter()
    rows = 0
    text_layer_pages = 0
    nonempty_text_pages = 0
    total_code_points = 0
    total_utf8_bytes = 0
    total_zones = 0
    try:
        handle = private_path.open("r", encoding="utf-8")
    except OSError as exc:
        raise MiddleUkrainianTextExtractionError(f"cannot open private JSONL: {exc}") from exc
    with handle:
        for line_number, line in enumerate(handle, start=1):
            require(line.endswith("\n"), f"private JSONL line {line_number} lacks newline termination")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise MiddleUkrainianTextExtractionError(
                    f"private JSONL line {line_number} is invalid JSON: {exc.msg}"
                ) from exc
            require(isinstance(row, dict) and set(row) == PRIVATE_ROW_KEYS, f"private row {line_number} shape drift")
            require(row["schema_version"] == ROW_SCHEMA_VERSION, f"private row {line_number} schema drift")
            require(row["source_sha256"] == intake.SOURCE_SHA256, f"private row {line_number} source drift")
            page_number = _int_value(row["page_number"], label=f"row {line_number} page number", minimum=1)
            require(page_number == line_number, f"private page sequence drift at line {line_number}")
            page_width = _int_value(row["page_width"], label=f"page {page_number} width", minimum=1)
            page_height = _int_value(row["page_height"], label=f"page {page_number} height", minimum=1)
            dpi = _int_value(row["dpi"], label=f"page {page_number} DPI", minimum=1)
            rotation = _int_value(row["rotation"], label=f"page {page_number} rotation")
            require(rotation in {0, 90, 180, 270}, f"page {page_number} rotation drift")
            geometry_key = f"{page_width}x{page_height}@{dpi}r{rotation}"
            geometry_counts[geometry_key] += 1
            geometry_manifest.append(
                {
                    "page_number": page_number,
                    "width": page_width,
                    "height": page_height,
                    "dpi": dpi,
                    "rotation": rotation,
                }
            )

            require(isinstance(row["text_layer_present"], bool), f"page {page_number} layer flag drift")
            decoded_text = row["decoded_text"]
            require(isinstance(decoded_text, str), f"page {page_number} decoded text must be a string")
            decoded_hash = hashlib.sha256(decoded_text.encode("utf-8")).hexdigest()
            require(row["decoded_text_sha256"] == decoded_hash, f"page {page_number} text hash drift")
            code_points = _int_value(
                row["decoded_text_code_points"], label=f"page {page_number} code-point count"
            )
            utf8_bytes = _int_value(row["decoded_text_utf8_bytes"], label=f"page {page_number} UTF-8 bytes")
            require(code_points == len(decoded_text), f"page {page_number} code-point denominator drift")
            require(utf8_bytes == len(decoded_text.encode("utf-8")), f"page {page_number} byte denominator drift")

            zones = row["text_zones"]
            if row["text_layer_present"]:
                require(isinstance(zones, list) and zones, f"page {page_number} present layer lacks zones")
                text_layer_pages += 1
            else:
                require(zones is None, f"page {page_number} absent layer must use null zones")
            if isinstance(zones, list):
                for zone_index, zone in enumerate(zones):
                    _validate_zone(
                        zone,
                        page_number=page_number,
                        zone_index=zone_index,
                        page_width=page_width,
                        page_height=page_height,
                    )
            zone_count = _int_value(row["text_zone_count"], label=f"page {page_number} zone count")
            require(zone_count == (len(zones) if isinstance(zones, list) else 0), f"page {page_number} zone count drift")
            zone_hash = sha256_compact_json(zones)
            require(row["text_zones_sha256"] == zone_hash, f"page {page_number} zone hash drift")
            require(row["ocr_used"] is False, f"page {page_number} claims OCR")
            require(row["normalization_applied"] is False, f"page {page_number} claims normalization")
            require(row["inferred_character_repairs"] is False, f"page {page_number} claims repairs")

            rows += 1
            if decoded_text:
                nonempty_text_pages += 1
            total_code_points += code_points
            total_utf8_bytes += utf8_bytes
            total_zones += zone_count
            text_hashes.append(decoded_hash)
            zone_hashes.append(zone_hash)

    summary = {
        "pages": rows,
        "text_layer_pages": text_layer_pages,
        "nonempty_text_pages": nonempty_text_pages,
        "total_code_points": total_code_points,
        "total_utf8_bytes": total_utf8_bytes,
        "total_zones": total_zones,
        "private_jsonl_bytes": private_path.stat().st_size,
        "private_jsonl_sha256": sha256_file(private_path),
        "page_text_hash_manifest_sha256": sha256_compact_json(text_hashes),
        "text_zone_hash_manifest_sha256": sha256_compact_json(zone_hashes),
        "page_geometry_manifest_sha256": sha256_compact_json(geometry_manifest),
        "geometry_counts": dict(sorted(geometry_counts.items())),
    }
    expected = {
        "pages": EXPECTED_PAGES,
        "text_layer_pages": EXPECTED_TEXT_LAYER_PAGES,
        "nonempty_text_pages": EXPECTED_NONEMPTY_TEXT_PAGES,
        "total_code_points": EXPECTED_TOTAL_CODE_POINTS,
        "total_utf8_bytes": EXPECTED_TOTAL_UTF8_BYTES,
        "total_zones": EXPECTED_TOTAL_ZONES,
        "private_jsonl_bytes": EXPECTED_PRIVATE_JSONL_BYTES,
        "private_jsonl_sha256": EXPECTED_PRIVATE_JSONL_SHA256,
        "page_text_hash_manifest_sha256": EXPECTED_PAGE_TEXT_HASH_MANIFEST_SHA256,
        "text_zone_hash_manifest_sha256": EXPECTED_TEXT_ZONE_HASH_MANIFEST_SHA256,
        "page_geometry_manifest_sha256": EXPECTED_PAGE_GEOMETRY_MANIFEST_SHA256,
        "geometry_counts": EXPECTED_GEOMETRY_COUNTS,
    }
    require(summary == expected, "private extraction denominator drift")
    return summary


def _validate_decoder(path: Path) -> None:
    _exact_regular_file(
        path,
        label="DjVu.js decoder",
        expected_bytes=DECODER_BYTES,
        expected_sha256=DECODER_SHA256,
    )


def _invoke_extractor(*, source_path: Path, decoder_path: Path, output_path: Path) -> dict[str, Any]:
    node = shutil.which("node")
    require(node is not None, "Node.js is required for pinned DjVu text decoding")
    command = [
        node,
        str(RUNNER_PATH),
        "--source",
        str(source_path),
        "--decoder",
        str(decoder_path),
        "--output",
        str(output_path),
        "--expected-source-sha256",
        intake.SOURCE_SHA256,
        "--expected-source-bytes",
        str(intake.SOURCE_BYTES),
        "--expected-decoder-sha256",
        DECODER_SHA256,
        "--expected-decoder-version",
        DECODER_VERSION,
        "--expected-pages",
        str(EXPECTED_PAGES),
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
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MiddleUkrainianTextExtractionError(f"DjVu extraction transport failed: {exc}") from exc
    require(completed.returncode == 0, f"DjVu extraction failed: {completed.stderr.strip()}")
    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MiddleUkrainianTextExtractionError("DjVu extractor emitted invalid summary JSON") from exc
    require(isinstance(summary, dict), "DjVu extractor summary must be an object")
    return summary


def _receipt_body(*, private_summary: Mapping[str, Any], intake_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "source_binding": {
            "collection_id": intake.COLLECTION_ID,
            "source_filename": intake.SOURCE_FILENAME,
            "source_bytes": intake.SOURCE_BYTES,
            "source_sha256": intake.SOURCE_SHA256,
            "raw_intake_receipt_file_sha256": intake_summary["receipt_file_sha256"],
            "raw_intake_receipt_sha256": intake_summary["receipt_sha256"],
        },
        "decoder_binding": {
            "project": "DjVu.js",
            "release_tag": DECODER_RELEASE_TAG,
            "release_url": DECODER_RELEASE_URL,
            "asset_url": DECODER_ASSET_URL,
            "version": DECODER_VERSION,
            "bytes": DECODER_BYTES,
            "sha256": DECODER_SHA256,
            "decoder_binary_copied_to_output": False,
            "decoder_license_expression_verified": False,
            "execution_tool_only_not_source_authority": True,
        },
        "implementation_binding": {
            "controller_sha256": sha256_file(Path(__file__)),
            "runner_sha256": sha256_file(RUNNER_PATH),
            "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA_PATH),
        },
        "private_output": {
            "filename": PRIVATE_JSONL_FILENAME,
            "storage": "private_google_drive",
            **dict(private_summary),
        },
        "extraction_scope": {
            "method": "embedded_djvu_text_layer_decode",
            "page_coordinate_alignment_structurally_verified": True,
            "visual_text_image_alignment_quality_verified": False,
            "embedded_text_quality_verified": False,
            "source_transcription_candidate_only": True,
            "ocr_used": False,
            "normalization_applied": False,
            "inferred_character_repairs": False,
        },
        "rights_and_custody": {
            "source_and_text_storage": "private_google_drive",
            "source_attribution_and_locators_inherited_from_raw_intake": True,
            "private_research_and_source_evidence_only": True,
            "full_scan_public_redistribution_authorized": False,
            "full_text_public_redistribution_authorized": False,
            "training_export_authorized": False,
            "public_repo_contains_source_text": False,
            "adapt_or_remove_on_substantiated_notice": True,
        },
        "safeguards": {
            "qualified_historical_review_complete": False,
            "historical_stage_assignment_frozen": False,
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
        raise MiddleUkrainianTextExtractionError("cannot read text-extraction receipt schema") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise MiddleUkrainianTextExtractionError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")


def _validate_intake(*, source_path: Path, raw_intake_dir: Path) -> dict[str, Any]:
    summary = intake.validate_existing_intake(source_path=source_path, private_output_dir=raw_intake_dir)
    require(
        summary["receipt_file_sha256"] == RAW_INTAKE_RECEIPT_FILE_SHA256,
        "raw-intake receipt file SHA-256 drift",
    )
    require(summary["receipt_sha256"] == RAW_INTAKE_RECEIPT_SHA256, "raw-intake receipt self-hash drift")
    return summary


def materialize_extraction(
    *,
    source_path: Path,
    raw_intake_dir: Path,
    decoder_path: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Write exact private page text plus one immutable, text-free receipt."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private extraction cannot be written inside Git")
    require(not output_dir.exists() and not output_dir.is_symlink(), "immutable private output already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    require(output_dir.parent.is_dir() and not output_dir.parent.is_symlink(), "private output parent is unsafe")
    intake_summary = _validate_intake(source_path=source_path, raw_intake_dir=raw_intake_dir)
    _validate_decoder(decoder_path)

    staged_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    staged_jsonl = staged_dir / PRIVATE_JSONL_FILENAME
    staged_receipt = staged_dir / RECEIPT_FILENAME
    try:
        runner_summary = _invoke_extractor(
            source_path=source_path,
            decoder_path=decoder_path,
            output_path=staged_jsonl,
        )
        private_summary = validate_private_jsonl(staged_jsonl)
        expected_runner_subset = {
            "pages": private_summary["pages"],
            "text_layer_pages": private_summary["text_layer_pages"],
            "nonempty_text_pages": private_summary["nonempty_text_pages"],
            "total_code_points": private_summary["total_code_points"],
            "total_utf8_bytes": private_summary["total_utf8_bytes"],
            "total_zones": private_summary["total_zones"],
            "private_jsonl_bytes": private_summary["private_jsonl_bytes"],
            "private_jsonl_sha256": private_summary["private_jsonl_sha256"],
            "page_text_hash_manifest_sha256": private_summary["page_text_hash_manifest_sha256"],
            "text_zone_hash_manifest_sha256": private_summary["text_zone_hash_manifest_sha256"],
            "page_geometry_manifest_sha256": private_summary["page_geometry_manifest_sha256"],
        }
        require(
            {key: runner_summary.get(key) for key in expected_runner_subset} == expected_runner_subset,
            "runner summary does not match private JSONL replay",
        )
        require(
            runner_summary.get("row_schema_version") == ROW_SCHEMA_VERSION
            and runner_summary.get("decoder_version") == DECODER_VERSION
            and runner_summary.get("source_sha256") == intake.SOURCE_SHA256
            and runner_summary.get("ocr_used") is False
            and runner_summary.get("normalization_applied") is False
            and runner_summary.get("inferred_character_repairs") is False,
            "runner safety summary drift",
        )
        receipt_body = _receipt_body(private_summary=private_summary, intake_summary=intake_summary)
        receipt = {**receipt_body, "receipt_sha256": sha256_value(receipt_body)}
        _validate_receipt(receipt)
        staged_receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(staged_receipt, 0o600)
        validate_existing_extraction(
            source_path=source_path,
            raw_intake_dir=raw_intake_dir,
            private_output_dir=staged_dir,
        )
        os.replace(staged_dir, output_dir)
    finally:
        if staged_dir.exists():
            for staged_path in (staged_jsonl, staged_receipt):
                if staged_path.exists():
                    staged_path.unlink()
            staged_dir.rmdir()
    return validate_existing_extraction(
        source_path=source_path,
        raw_intake_dir=raw_intake_dir,
        private_output_dir=output_dir,
    )


def validate_existing_extraction(
    *,
    source_path: Path,
    raw_intake_dir: Path,
    private_output_dir: Path,
) -> dict[str, Any]:
    """Rebuild the text-free receipt from current code, source, and private output."""
    output_dir = Path(private_output_dir)
    require(not _inside_git_checkout(output_dir), "private extraction cannot be read from inside Git")
    require(output_dir.is_dir() and not output_dir.is_symlink(), "private extraction directory is missing or unsafe")
    require(
        {path.name for path in output_dir.iterdir()} == {PRIVATE_JSONL_FILENAME, RECEIPT_FILENAME},
        "private extraction directory contents drift",
    )
    intake_summary = _validate_intake(source_path=source_path, raw_intake_dir=raw_intake_dir)
    private_summary = validate_private_jsonl(output_dir / PRIVATE_JSONL_FILENAME)
    receipt = _load_json_object(output_dir / RECEIPT_FILENAME, label="text-extraction receipt")
    _validate_receipt(receipt)
    rebuilt_body = _receipt_body(private_summary=private_summary, intake_summary=intake_summary)
    rebuilt = {**rebuilt_body, "receipt_sha256": sha256_value(rebuilt_body)}
    require(receipt == rebuilt, "text-extraction receipt does not reproduce from current inputs")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_sha256": intake.SOURCE_SHA256,
        "private_jsonl_sha256": private_summary["private_jsonl_sha256"],
        "receipt_file_sha256": sha256_file(output_dir / RECEIPT_FILENAME),
        "receipt_sha256": receipt["receipt_sha256"],
        "pages": private_summary["pages"],
        "text_layer_pages": private_summary["text_layer_pages"],
        "total_code_points": private_summary["total_code_points"],
        "total_zones": private_summary["total_zones"],
        "visual_alignment_quality_verified": False,
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
        subparser.add_argument("--private-output-dir", type=Path, required=True)
        if command == "materialize":
            subparser.add_argument("--decoder", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize_extraction(
            source_path=args.source,
            raw_intake_dir=args.raw_intake_dir,
            decoder_path=args.decoder,
            private_output_dir=args.private_output_dir,
        )
    else:
        result = validate_existing_extraction(
            source_path=args.source,
            raw_intake_dir=args.raw_intake_dir,
            private_output_dir=args.private_output_dir,
        )
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
