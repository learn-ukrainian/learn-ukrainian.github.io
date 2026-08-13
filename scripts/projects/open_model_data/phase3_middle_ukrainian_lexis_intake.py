#!/usr/bin/env python3
"""Verify a private raw snapshot of two early Ukrainian lexicographic monuments.

The snapshot preserves the public Izbornyk electronic publication of Vasyl
Nimchuk's 1964 edition of Lavrentii Zyzanii's 1596 printed ``Лексис`` and the
seventeenth-century manuscript ``Синоніма славеноросская``.  It contains both
facsimile images and electronic transcriptions, plus scholarly commentary.

This module freezes exact source bytes and structural layer boundaries without
extracting entries, resolving mixed language layers, assigning historical
stage gold, admitting training rows, or authorizing Phase 4.  Source files and
the receipt stay in private Google Drive; Git receives only this text-free
validator, its schema, and hermetic tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import stat
import struct
import tempfile
import zlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_linguistic_representation import canonical_json, sha256_value

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_middle_ukrainian_lexis_intake_receipt_v1.schema.json"
)

SCHEMA_VERSION = "phase3_middle_ukrainian_lexis_intake_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_middle_ukrainian_lexis_intake_v1"
COLLECTION_ID = "zyzanii-lexis-1596-synonima-17c-nimchuk-1964"
SOURCE_TITLE = "Лексис Лаврентія Зизанія. Синоніма славеноросская"
SOURCE_PREPARER = "В. В. Німчук"
PUBLICATION_YEAR = 1964
LEXIS_YEAR = 1596
SYNONIMA_DATE = "seventeenth_century_date_unresolved"
INSTITUTIONAL_CATALOGUE_URL = "https://irbis-nbuv.gov.ua/ulib/item/0001524"
ELECTRONIC_PUBLICATION_URL = "http://litopys.org.ua/zyzlex/zyz.htm"
RECEIPT_FILENAME = "middle-ukrainian-lexis-intake-receipt-v1.json"

HTML_PATHS = (
    "zyzlex/zyz.htm",
    *(f"zyzlex/zyz{number:02d}.htm" for number in range(1, 100)),
    *(f"zyzlex/zyz{number}.htm" for number in range(100, 103)),
)
PNG_PATHS = tuple(f"zyzlex/zyzle{number:03d}.png" for number in range(1, 182, 2))
CSS_PATHS = ("zsuv.css", "zyzlex/zyz.css")
EXPECTED_RESOURCE_PATHS = tuple(sorted((*HTML_PATHS, *PNG_PATHS, *CSS_PATHS)))

INDEX_HTML_PATHS = ("zyzlex/zyz.htm",)
EDITORIAL_HTML_PATHS = (
    "zyzlex/zyz01.htm",
    "zyzlex/zyz69.htm",
    "zyzlex/zyz98.htm",
)
TARGET_TRANSCRIPTION_HTML_PATHS = (
    "zyzlex/zyz70.htm",
    "zyzlex/zyz71.htm",
    "zyzlex/zyz72.htm",
    "zyzlex/zyz73.htm",
    "zyzlex/zyz99.htm",
)
SUPPLEMENTAL_TRANSCRIPTION_HTML_PATHS = (
    "zyzlex/zyz100.htm",
    "zyzlex/zyz101.htm",
    "zyzlex/zyz102.htm",
)
FACSIMILE_WRAPPER_HTML_PATHS = tuple(
    sorted(
        set(HTML_PATHS)
        - set(INDEX_HTML_PATHS)
        - set(EDITORIAL_HTML_PATHS)
        - set(TARGET_TRANSCRIPTION_HTML_PATHS)
        - set(SUPPLEMENTAL_TRANSCRIPTION_HTML_PATHS)
    )
)
FACSIMILE_PAGE_IMAGE_PAIRS = tuple(
    [(f"zyzlex/zyz{page:02d}.htm", f"zyzlex/zyzle{2 * (page - 2) + 1:03d}.png") for page in range(2, 69)]
    + [(f"zyzlex/zyz{page:02d}.htm", f"zyzlex/zyzle{135 + 2 * (page - 74):03d}.png") for page in range(74, 98)]
)

EXPECTED_RESOURCE_COUNT = 196
EXPECTED_HTML_COUNT = 103
EXPECTED_PNG_COUNT = 91
EXPECTED_CSS_COUNT = 2
EXPECTED_TOTAL_BYTES = 2_767_216
EXPECTED_HTML_BYTES = 1_581_427
EXPECTED_PNG_BYTES = 1_182_465
EXPECTED_CSS_BYTES = 3_324
EXPECTED_RESOURCE_MANIFEST_SHA256 = "e23da810eb21d0b5c18fbc4a3ca527a4bb56c8c4d0502ccf765fbd7a27f5a37c"
EXPECTED_PNG_STRUCTURE_MANIFEST_SHA256 = "c0c93041bc8cb3dde1a650e30175fc64c1c89143a29f47738dabde2687bcb538"
EXPECTED_REFERENCE_MANIFEST_SHA256 = "59522ddfb38ab78426f90c0ec4be4eaf5df129166ed65143583aed997919b920"

HTML_REFERENCE_PATTERN = re.compile(rb"(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
SOURCE_HTML_PATTERN = re.compile(r"^zyzlex/zyz(?:\d{2,3})?\.htm$")
SOURCE_PNG_PATTERN = re.compile(r"^zyzlex/zyzle\d{3}\.png$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MiddleUkrainianLexisIntakeError(ValueError):
    """A source identity, snapshot, custody, or safety invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MiddleUkrainianLexisIntakeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _reject_symlink_components(path: Path, *, label: str) -> None:
    candidate = Path(os.path.abspath(os.fspath(path)))
    current = Path(candidate.anchor)
    for component in candidate.parts[1:]:
        current /= component
        if not current.exists() and not current.is_symlink():
            return
        require(not current.is_symlink(), f"{label} contains a symbolic-link path component")


def _require_private_mode(path: Path, *, directory: bool, label: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    require(mode & 0o077 == 0, f"{label} exposes group or other permission bits")
    if directory:
        require(mode & 0o700 == 0o700, f"{label} is not owner-accessible")
    else:
        require(mode & 0o600 == 0o600, f"{label} is not owner-readable and writable")


def _snapshot_files(root: Path) -> dict[str, Path]:
    _reject_symlink_components(root, label="source snapshot path")
    require(root.is_dir() and not root.is_symlink(), "source snapshot directory is missing or unsafe")
    require(not _inside_git_checkout(root), "source snapshot cannot be read from inside Git")
    _require_private_mode(root, directory=True, label="source snapshot directory")
    discovered: dict[str, Path] = {}
    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        current = Path(current_root)
        _require_private_mode(current, directory=True, label="source snapshot subdirectory")
        for directory_name in directory_names:
            directory = current / directory_name
            require(not directory.is_symlink(), "source snapshot contains a symbolic-link directory")
        for file_name in file_names:
            source_file = current / file_name
            require(source_file.is_file() and not source_file.is_symlink(), "source snapshot contains an unsafe file")
            _require_private_mode(source_file, directory=False, label="source snapshot file")
            relative_path = source_file.relative_to(root).as_posix()
            require(relative_path not in discovered, "source snapshot contains a duplicate path")
            discovered[relative_path] = source_file
    require(tuple(sorted(discovered)) == EXPECTED_RESOURCE_PATHS, "source snapshot resource inventory drift")
    return discovered


def _inspect_png(data: bytes, *, path: str) -> dict[str, Any]:
    require(data.startswith(PNG_SIGNATURE), f"PNG signature drift at {path}")
    cursor = len(PNG_SIGNATURE)
    chunk_index = 0
    ihdr: tuple[int, int, int, int, int] | None = None
    saw_iend = False
    while cursor < len(data):
        require(cursor + 12 <= len(data), f"truncated PNG chunk at {path}")
        length = struct.unpack(">I", data[cursor : cursor + 4])[0]
        chunk_type = data[cursor + 4 : cursor + 8]
        payload_start = cursor + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        require(crc_end <= len(data), f"PNG chunk exceeds file bounds at {path}")
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        require(actual_crc == expected_crc, f"PNG CRC drift at {path}")
        try:
            chunk_name = chunk_type.decode("ascii")
        except UnicodeDecodeError as exc:
            raise MiddleUkrainianLexisIntakeError(f"non-ASCII PNG chunk type at {path}") from exc
        if chunk_index == 0:
            require(chunk_name == "IHDR", f"PNG first chunk is not IHDR at {path}")
        if chunk_name == "IHDR":
            require(ihdr is None and length == 13, f"PNG IHDR drift at {path}")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            require(width > 0 and height > 0, f"PNG dimensions are invalid at {path}")
            require(compression == 0 and filter_method == 0, f"PNG method drift at {path}")
            require(bit_depth == 1 and color_type == 0 and interlace == 0, f"PNG pixel format drift at {path}")
            ihdr = (width, height, bit_depth, color_type, interlace)
        if chunk_name == "IEND":
            require(length == 0 and not saw_iend, f"PNG IEND drift at {path}")
            saw_iend = True
            require(crc_end == len(data), f"PNG trailing bytes after IEND at {path}")
        cursor = crc_end
        chunk_index += 1
    require(ihdr is not None and saw_iend and cursor == len(data), f"PNG structure did not close at {path}")
    width, height, bit_depth, color_type, interlace = ihdr
    return {
        "path": path,
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
    }


def _source_specific_reference(*, html_path: str, raw_reference: bytes) -> str | None:
    try:
        reference = raw_reference.decode("ascii").strip()
    except UnicodeDecodeError:
        return None
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "http" or parsed.netloc != "litopys.org.ua":
            return None
        candidate = parsed.path.lstrip("/")
    elif parsed.path.startswith("/"):
        candidate = parsed.path.lstrip("/")
    else:
        candidate = posixpath.normpath(posixpath.join(posixpath.dirname(html_path), parsed.path))
    if candidate == "zsuv.css":
        return candidate
    if SOURCE_HTML_PATTERN.fullmatch(candidate) or SOURCE_PNG_PATTERN.fullmatch(candidate):
        return candidate
    if candidate == "zyzlex/zyz.css":
        return candidate
    return None


def inspect_snapshot(snapshot_dir: Path) -> dict[str, Any]:
    """Re-hash and structurally inspect every frozen source resource."""
    root = Path(snapshot_dir)
    resources = _snapshot_files(root)
    pair_wrapper_paths = [wrapper_path for wrapper_path, _ in FACSIMILE_PAGE_IMAGE_PAIRS]
    pair_image_paths = [image_path for _, image_path in FACSIMILE_PAGE_IMAGE_PAIRS]
    require(
        len(pair_wrapper_paths) == len(set(pair_wrapper_paths))
        and set(pair_wrapper_paths) == set(FACSIMILE_WRAPPER_HTML_PATHS),
        "facsimile pair wrapper identity drift",
    )
    require(
        len(pair_image_paths) == len(set(pair_image_paths)) and set(pair_image_paths) == set(PNG_PATHS),
        "facsimile pair image identity drift",
    )
    manifest: list[dict[str, Any]] = []
    png_structures: list[dict[str, Any]] = []
    source_references: set[str] = set()
    category_bytes = {"html": 0, "png": 0, "css": 0}

    for relative_path in EXPECTED_RESOURCE_PATHS:
        source_file = resources[relative_path]
        before = source_file.stat()
        try:
            data = source_file.read_bytes()
        except OSError as exc:
            raise MiddleUkrainianLexisIntakeError(f"cannot read source resource {relative_path}: {exc}") from exc
        after = source_file.stat()
        require(
            (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
            f"source resource changed while reading: {relative_path}",
        )
        require(data, f"source resource is empty: {relative_path}")
        manifest.append(
            {
                "path": relative_path,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
        if relative_path.endswith(".htm"):
            category_bytes["html"] += len(data)
            lowered = data.lower()
            require(b"<html" in lowered and b"</html>" in lowered, f"HTML boundary drift at {relative_path}")
            require(b"windows-1251" in lowered, f"HTML charset declaration drift at {relative_path}")
            for reference in HTML_REFERENCE_PATTERN.findall(data):
                normalized = _source_specific_reference(html_path=relative_path, raw_reference=reference)
                if normalized is not None:
                    source_references.add(normalized)
        elif relative_path.endswith(".png"):
            category_bytes["png"] += len(data)
            png_structures.append(_inspect_png(data, path=relative_path))
        else:
            category_bytes["css"] += len(data)

    require(source_references == set(EXPECTED_RESOURCE_PATHS), "source-specific HTML reference closure drift")
    for wrapper_path, image_path in FACSIMILE_PAGE_IMAGE_PAIRS:
        wrapper = resources[wrapper_path].read_bytes()
        require(
            Path(image_path).name.encode("ascii") in wrapper,
            f"facsimile wrapper/image alignment drift at {wrapper_path}",
        )

    summary = {
        "resources": len(manifest),
        "html_pages": len(HTML_PATHS),
        "facsimile_png_assets": len(PNG_PATHS),
        "css_assets": len(CSS_PATHS),
        "total_bytes": sum(item["bytes"] for item in manifest),
        "html_bytes": category_bytes["html"],
        "png_bytes": category_bytes["png"],
        "css_bytes": category_bytes["css"],
        "resource_manifest_sha256": sha256_value(manifest),
        "png_structure_manifest_sha256": sha256_value(png_structures),
        "source_specific_reference_paths": len(source_references),
        "source_specific_reference_manifest_sha256": sha256_value(sorted(source_references)),
        "facsimile_page_image_links": len(FACSIMILE_PAGE_IMAGE_PAIRS),
        "html_charset": "windows-1251",
        "png_pixel_format": "1_bit_grayscale_non_interlaced",
        "raw_snapshot_fully_walked": True,
    }
    expected = {
        "resources": EXPECTED_RESOURCE_COUNT,
        "html_pages": EXPECTED_HTML_COUNT,
        "facsimile_png_assets": EXPECTED_PNG_COUNT,
        "css_assets": EXPECTED_CSS_COUNT,
        "total_bytes": EXPECTED_TOTAL_BYTES,
        "html_bytes": EXPECTED_HTML_BYTES,
        "png_bytes": EXPECTED_PNG_BYTES,
        "css_bytes": EXPECTED_CSS_BYTES,
        "resource_manifest_sha256": EXPECTED_RESOURCE_MANIFEST_SHA256,
        "png_structure_manifest_sha256": EXPECTED_PNG_STRUCTURE_MANIFEST_SHA256,
        "source_specific_reference_paths": EXPECTED_RESOURCE_COUNT,
        "source_specific_reference_manifest_sha256": EXPECTED_REFERENCE_MANIFEST_SHA256,
        "facsimile_page_image_links": EXPECTED_PNG_COUNT,
        "html_charset": "windows-1251",
        "png_pixel_format": "1_bit_grayscale_non_interlaced",
        "raw_snapshot_fully_walked": True,
    }
    require(summary == expected, "frozen source snapshot denominator drift")
    return summary


def _load_json_object(path: Path, *, description: str) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"{description} is missing or unsafe")
    _require_private_mode(path, directory=False, label=description)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MiddleUkrainianLexisIntakeError(f"cannot read {description}: {exc}") from exc
    require(isinstance(value, dict), f"{description} must be a JSON object")
    return value


def _receipt_body(*, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "source": {
            "collection_id": COLLECTION_ID,
            "title": SOURCE_TITLE,
            "preparer": SOURCE_PREPARER,
            "publication_year": PUBLICATION_YEAR,
            "institutional_catalogue_url": INSTITUTIONAL_CATALOGUE_URL,
            "electronic_publication_url": ELECTRONIC_PUBLICATION_URL,
            "components": [
                {
                    "component_id": "zyzanii-lexis-1596",
                    "title": "Лексис Лаврентія Зизанія",
                    "date": str(LEXIS_YEAR),
                    "medium": "printed_lexicography",
                },
                {
                    "component_id": "synonima-slavenorosskaia-17c",
                    "title": "Синоніма славеноросская",
                    "date": SYNONIMA_DATE,
                    "medium": "manuscript_lexicography",
                },
            ],
        },
        "implementation": {
            "implementation_sha256": sha256_file(Path(__file__)),
            "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA_PATH),
            "parser": "exact_static_snapshot_manifest_html_link_closure_and_png_crc_walker",
        },
        "snapshot": dict(snapshot),
        "layer_inventory": {
            "index_html_pages": len(INDEX_HTML_PATHS),
            "scholarly_editorial_html_pages": len(EDITORIAL_HTML_PATHS),
            "target_monument_transcription_html_pages": len(TARGET_TRANSCRIPTION_HTML_PATHS),
            "supplemental_historical_transcription_html_pages": len(SUPPLEMENTAL_TRANSCRIPTION_HTML_PATHS),
            "facsimile_wrapper_html_pages": len(FACSIMILE_WRAPPER_HTML_PATHS),
            "facsimile_png_assets": len(PNG_PATHS),
            "layer_assignments_are_site_structure_only": True,
            "editorial_and_source_layers_semantically_separated": False,
        },
        "evidence_scope": {
            "ukrainian_academic_scholarly_edition": True,
            "direct_printed_lexicographic_source_candidate": True,
            "direct_manuscript_lexicographic_source_candidate": True,
            "candidate_gap_cell": "middle_ukrainian_print_and_lexicography",
            "mixed_church_slavonic_and_historical_ukrainian_layers_present": True,
            "historical_stage_assignment": "pending_qualified_historical_review",
            "geographic_representativeness_verified": False,
            "representative_of_all_middle_ukrainian_varieties": False,
            "nimchuk_as_sole_periodization_authority": False,
        },
        "rights_and_custody": {
            "storage": "private_google_drive",
            "public_source_access": True,
            "source_site_scan_and_processing_credit": "Максим, Ізборник, 27.IX.2003",
            "standardized_dataset_license_present": False,
            "retrieval_transport": "plain_http_site_snapshot",
            "retrieval_transport_authenticated": False,
            "private_research_and_source_evidence_only": True,
            "source_attribution_and_locators_preserved": True,
            "full_scan_public_redistribution_authorized": False,
            "full_text_public_redistribution_authorized": False,
            "training_export_authorized": False,
            "adapt_or_remove_on_substantiated_notice": True,
        },
        "safeguards": {
            "resource_inventory_exact": True,
            "resource_hashes_verified": True,
            "html_boundaries_and_charset_verified": True,
            "source_specific_link_closure_verified": True,
            "png_boundaries_and_crc_verified": True,
            "content_layer_extracted": False,
            "normalization_applied": False,
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
            "page_and_transcription_alignment_required": True,
            "editorial_and_direct_source_layer_separation_required": True,
            "church_slavonic_and_historical_ukrainian_layer_separation_required": True,
            "qualified_historical_feature_review_required": True,
            "print_and_lexicography_gap_narrowed_not_closed": True,
            "private_writing_gap_remains_open": True,
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
        raise MiddleUkrainianLexisIntakeError(f"cannot read receipt schema: {RECEIPT_SCHEMA_PATH}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: tuple(map(str, item.path)))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise MiddleUkrainianLexisIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    require(receipt["receipt_sha256"] == sha256_value(body), "receipt self-hash drift")
    require(
        receipt["snapshot"]["resources"]
        == receipt["snapshot"]["html_pages"]
        + receipt["snapshot"]["facsimile_png_assets"]
        + receipt["snapshot"]["css_assets"],
        "snapshot resource denominator does not close",
    )
    require(
        receipt["layer_inventory"]["facsimile_wrapper_html_pages"]
        == receipt["layer_inventory"]["facsimile_png_assets"],
        "facsimile wrapper/image denominator does not close",
    )
    require(receipt["safeguards"]["training_eligible"] is False, "receipt overclaims training eligibility")
    require(receipt["safeguards"]["semantic_gold"] is False, "receipt overclaims semantic gold")
    require(receipt["safeguards"]["phase4_blocked"] is True, "receipt unblocks Phase 4")


def materialize_intake(*, snapshot_dir: Path, private_output_dir: Path) -> dict[str, Any]:
    """Write one immutable, text-free receipt for the privately held snapshot."""
    output_dir = Path(private_output_dir)
    _reject_symlink_components(output_dir.parent, label="private output parent")
    require(not _inside_git_checkout(output_dir), "private receipt cannot be written inside Git")
    require(not output_dir.is_symlink(), "private output directory cannot be a symbolic link")
    require(not output_dir.exists(), "immutable private output directory already exists")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    require(output_dir.parent.is_dir() and not output_dir.parent.is_symlink(), "private output parent is unsafe")

    snapshot = inspect_snapshot(snapshot_dir)
    receipt_body = _receipt_body(snapshot=snapshot)
    receipt = {**receipt_body, "receipt_sha256": sha256_value(receipt_body)}
    _validate_receipt(receipt)

    staged_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.stage-", dir=output_dir.parent))
    os.chmod(staged_dir, 0o700)
    staged_receipt = staged_dir / RECEIPT_FILENAME
    try:
        staged_receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.chmod(staged_receipt, 0o600)
        validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=staged_dir)
        os.replace(staged_dir, output_dir)
    finally:
        if staged_dir.exists():
            if staged_receipt.exists():
                staged_receipt.unlink()
            staged_dir.rmdir()
    validate_existing_intake(snapshot_dir=snapshot_dir, private_output_dir=output_dir)
    return receipt


def validate_existing_intake(*, snapshot_dir: Path, private_output_dir: Path) -> dict[str, Any]:
    """Rebuild the receipt from current snapshot, schema, and implementation bytes."""
    output_dir = Path(private_output_dir)
    _reject_symlink_components(output_dir, label="private receipt path")
    require(not _inside_git_checkout(output_dir), "private receipt cannot be read from inside Git")
    require(output_dir.is_dir() and not output_dir.is_symlink(), "private receipt directory is missing or unsafe")
    _require_private_mode(output_dir, directory=True, label="private receipt directory")
    receipt_path = output_dir / RECEIPT_FILENAME
    receipt = _load_json_object(receipt_path, description="Middle Ukrainian lexis intake receipt")
    _validate_receipt(receipt)
    snapshot = inspect_snapshot(snapshot_dir)
    rebuilt_body = _receipt_body(snapshot=snapshot)
    rebuilt = {**rebuilt_body, "receipt_sha256": sha256_value(rebuilt_body)}
    require(receipt == rebuilt, "receipt does not reproduce from current source and code")
    return {
        "schema_version": SCHEMA_VERSION,
        "collection_id": COLLECTION_ID,
        "resources": snapshot["resources"],
        "facsimile_png_assets": snapshot["facsimile_png_assets"],
        "target_monument_transcription_html_pages": len(TARGET_TRANSCRIPTION_HTML_PATHS),
        "resource_manifest_sha256": snapshot["resource_manifest_sha256"],
        "receipt_file_sha256": sha256_file(receipt_path),
        "receipt_sha256": receipt["receipt_sha256"],
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
        subparser.add_argument("--snapshot-dir", type=Path, required=True)
        subparser.add_argument("--private-output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize_intake(snapshot_dir=args.snapshot_dir, private_output_dir=args.private_output_dir)
    else:
        result = validate_existing_intake(snapshot_dir=args.snapshot_dir, private_output_dir=args.private_output_dir)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
