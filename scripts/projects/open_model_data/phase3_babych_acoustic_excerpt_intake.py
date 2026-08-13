#!/usr/bin/env python3
"""Verify the private KUBG Babych 2022 acoustic-phonetics excerpt intake.

The downloadable official PDF remains outside Git. This module replays exact
byte custody, institutional HTML/METS/JSON metadata, and the deterministic
13-page excerpt structure, then emits one text-free public receipt. It does not
admit training conversion, database ingest, normative authority, semantic gold,
source-universe freeze, topic-gap narrowing/closure, Phase 3 completion, or
Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_babych_acoustic_excerpt_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_babych_acoustic_excerpt_candidate_v1.json"

SCHEMA_VERSION = "phase3_babych_acoustic_excerpt_candidate_v1"
STATUS = "CONTEXTUAL_EXCERPT_PENDING_UKRAINIAN_SOURCE_REVIEW_AND_SCOPE_CRITIC"
SOURCE_ID = "uni-ukrmova-phonetics-audiology-babych-2022"
SOURCE_TITLE = "Фонетика та фонологія з основами аудіології"
SOURCE_AUTHOR_DISPLAY = "Наталія Миколаївна Бабич"
SOURCE_METADATA_AUTHOR = "Бабич, Наталія Миколаїівна"
SOURCE_METADATA_GIVEN = "Наталія Миколаїівна"
SOURCE_METADATA_FAMILY = "Бабич"
SOURCE_INSTITUTION = "Київський університет імені Бориса Грінченка"
SOURCE_PUBLISHER = 'ТОВ "Альянс", Україна'
SOURCE_ISBN = "978-617-7819-30-0"
SOURCE_EPRINT_ID = "43529"
SOURCE_ITEM_URL = f"https://elibrary.kubg.edu.ua/id/eprint/{SOURCE_EPRINT_ID}/"
SOURCE_ITEM_URL_BARE = f"https://elibrary.kubg.edu.ua/id/eprint/{SOURCE_EPRINT_ID}"
SOURCE_BITSTREAM_URL = f"https://elibrary.kubg.edu.ua/id/eprint/{SOURCE_EPRINT_ID}/1/N_Babych_FTFZOA_FPSRSO.pdf"
SOURCE_METS_OBJID = f"eprint_{SOURCE_EPRINT_ID}"
SOURCE_METS_FILE_ID = f"eprint_{SOURCE_EPRINT_ID}_229171_1"
SOURCE_METS_TITLE_CORRUPT = "ARRAY(0x55b74057aae8)"
PRIVATE_INPUT_LOCATOR = "university_corpus/staging/phase3-6375-wave-k-acoustic-phonetics"

PDF_SHA256 = "7adee0a1f2f77af95a3c76474ec8a7df4208039d64d3420d3008466f1f66e537"
PDF_MD5 = "f93ec105f9e4b4a369fab521ca9e70ec"
PDF_BYTES = 357_368
PDF_PAGES = 13
CATALOG_PRINT_COLLATION_PAGES = 294
TEXT_BEARING_PAGES = 13
UNICODE_CODE_POINTS = 17_490
UTF8_BYTES = 29_668
PAGE_MANIFEST_SHA256 = "dc58cc622724864d6236743b026bbbd6b371dac1c35eadf544025861ee58f7f8"
EXTRACTED_TEXT_SHA256 = "d75ab3d661dc9ff560887cd58be805585685c6cc17668689000f99a0f303675f"
METS_SHA256 = "36b11282b95bc74a58490e82ad8d6680749c9ae52114130073e3137fafbdadd6"
ITEM_RECORD_SHA256 = "4e21fbd647816675750702b05c6d57b2ee2fa56b741721b9e26b3e1e2cf190b7"
EXPORT_JSON_SHA256 = "860c6b7bc59ab3c2d4816defa2c06fd0c8d26ba8362d68f868545dac5731c942"
V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"

PRINT_PAGE_BY_PDF_PAGE = {
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 20,
    10: 21,
    11: 22,
    12: 23,
}
FRONT_MATTER_PDF_PAGES = [1, 2, 3, 4, 5, 6, 7, 8]
SYMBOLS_PDF_PAGE = 9
MODULE_I_ACOUSTIC_PDF_PAGES = [10, 11, 12]
COLOPHON_PDF_PAGE = 13
ACOUSTIC_MARKERS = (
    "інтенсивність",
    "частота",
    "спектр",
    "тривалість",
    "фаза",
)
DISCONTINUITIES = [
    {
        "after_pdf_page": 8,
        "from_print_page": 8,
        "to_print_page": 20,
        "evidence": "print_page_jump_8_to_20",
    },
    {
        "after_pdf_page": 12,
        "from_print_page": 23,
        "to_role": "colophon",
        "evidence": "print_page_23_followed_by_colophon",
    },
]
PRIVATE_FILE_MODE = 0o600


class BabychAcousticExcerptIntakeError(ValueError):
    """The exact private excerpt or its fail-closed disposition drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BabychAcousticExcerptIntakeError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


ACOUSTIC_MARKERS_SET_SHA256 = sha256_bytes(canonical_bytes(sorted(ACOUSTIC_MARKERS)))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BabychAcousticExcerptIntakeError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _reject_symlink_components(path: Path, label: str) -> None:
    raw_path = Path(os.fspath(path))
    require(".." not in raw_path.parts, f"{label} cannot contain parent traversal")
    candidate = Path(os.path.abspath(os.fspath(path)))
    current = Path(candidate.anchor)
    for component in candidate.parts[1:]:
        current /= component
        if not current.exists() and not current.is_symlink():
            return
        require(not current.is_symlink(), f"{label} contains a symbolic-link path component")


def _private_regular_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise BabychAcousticExcerptIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _read_private_bytes(path: Path, label: str, expected_sha256: str) -> bytes:
    _private_regular_file(path, label)
    try:
        before = Path(path).stat()
        payload = Path(path).read_bytes()
        after = Path(path).stat()
    except OSError as exc:
        raise BabychAcousticExcerptIntakeError(f"cannot read {label}") from exc
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        f"{label} changed while reading",
    )
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, f"{label} byte drift")
    return payload


def _read_private_json(path: Path, label: str, expected_sha256: str) -> dict[str, Any]:
    payload = _read_private_bytes(path, label, expected_sha256)
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise BabychAcousticExcerptIntakeError(f"cannot parse {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BabychAcousticExcerptIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _html_meta(item: str) -> dict[str, list[str]]:
    meta: dict[str, list[str]] = {}
    for match in re.finditer(r"<meta\s+([^>]+?)/?>", item, flags=re.IGNORECASE):
        attributes = {
            key.lower(): value
            for key, value in re.findall(r"([A-Za-z_:.-]+)\s*=\s*[\"']([^\"']*)[\"']", match.group(1))
        }
        if "name" in attributes and "content" in attributes:
            meta.setdefault(attributes["name"], []).append(attributes["content"])
    return meta


def inspect_pdf(path: Path) -> dict[str, Any]:
    """Reproduce excerpt text-layer facts without retaining source text."""
    payload = _read_private_bytes(path, "Babych source PDF", PDF_SHA256)
    require(len(payload) == PDF_BYTES, "Babych source PDF byte denominator drift")
    require(hashlib.md5(payload, usedforsecurity=False).hexdigest() == PDF_MD5, "Babych source PDF MD5 drift")
    try:
        reader = PdfReader(io.BytesIO(payload))
    except Exception as exc:
        raise BabychAcousticExcerptIntakeError("cannot parse Babych source PDF") from exc
    require(not reader.is_encrypted, "Babych source PDF is unexpectedly encrypted")
    require(len(reader.pages) == PDF_PAGES, "Babych source PDF page denominator drift")
    require(len(reader.pages) != CATALOG_PRINT_COLLATION_PAGES, "Babych PDF overclaims the full 294-page book")

    page_rows: list[dict[str, Any]] = []
    complete_text: list[str] = []
    observed_print_pages: dict[str, int] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise BabychAcousticExcerptIntakeError(f"cannot extract Babych source page {page_number}") from exc
        require(text.strip(), f"Babych source page {page_number} has no embedded text")
        first_line = _first_nonempty_line(text)
        if page_number in PRINT_PAGE_BY_PDF_PAGE:
            expected_print = PRINT_PAGE_BY_PDF_PAGE[page_number]
            require(
                first_line == str(expected_print),
                f"Babych print-page discontinuity drift at PDF page {page_number}",
            )
            observed_print_pages[str(page_number)] = expected_print
        if page_number == COLOPHON_PDF_PAGE:
            require(
                "Навчально-методичне видання" in text and "Підписано до друку" in text,
                "Babych colophon page drift",
            )
        encoded = text.encode("utf-8")
        page_rows.append(
            {
                "page": page_number,
                "chars": len(text),
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }
        )
        complete_text.append(text)

    require(
        observed_print_pages == {str(page): print_page for page, print_page in PRINT_PAGE_BY_PDF_PAGE.items()},
        "Babych observed print-page map drift",
    )
    module_text = "\n".join(complete_text[page - 1] for page in MODULE_I_ACOUSTIC_PDF_PAGES)
    for marker in ACOUSTIC_MARKERS:
        require(marker in module_text, f"Babych acoustic marker missing: {marker}")

    manifest_payload = b"".join(canonical_bytes(row) for row in page_rows)
    complete_source_text = "\n\f\n".join(complete_text)
    require(SOURCE_ISBN in complete_source_text, "Babych source PDF ISBN drift")
    require(
        re.search(rf"2022\D{{0,20}}{CATALOG_PRINT_COLLATION_PAGES}\s*с\.", complete_source_text) is not None,
        "Babych source PDF catalog collation drift",
    )
    joined_text = complete_source_text.encode("utf-8")
    root = reader.trailer["/Root"]
    if hasattr(root, "get_object"):
        root = root.get_object()
    facts = {
        "pages": len(page_rows),
        "text_bearing_pages": sum(bool(text.strip()) for text in complete_text),
        "unicode_code_points": sum(row["chars"] for row in page_rows),
        "utf8_bytes": sum(row["bytes"] for row in page_rows),
        "page_manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "extracted_text_sha256": hashlib.sha256(joined_text).hexdigest(),
        "acroform_present": "/AcroForm" in root,
        "form_field_count": len(reader.get_fields() or {}),
        "javascript_present": bool("/Names" in root and "/JavaScript" in root["/Names"]),
        "source_isbn_text_verified": True,
        "catalog_page_count_in_excerpt_text_verified": True,
        "observed_print_pages": observed_print_pages,
    }
    require(
        facts
        == {
            "pages": PDF_PAGES,
            "text_bearing_pages": TEXT_BEARING_PAGES,
            "unicode_code_points": UNICODE_CODE_POINTS,
            "utf8_bytes": UTF8_BYTES,
            "page_manifest_sha256": PAGE_MANIFEST_SHA256,
            "extracted_text_sha256": EXTRACTED_TEXT_SHA256,
            "acroform_present": False,
            "form_field_count": 0,
            "javascript_present": False,
            "source_isbn_text_verified": True,
            "catalog_page_count_in_excerpt_text_verified": True,
            "observed_print_pages": {str(page): print_page for page, print_page in PRINT_PAGE_BY_PDF_PAGE.items()},
        },
        "Babych excerpt text-layer facts drift",
    )
    return facts


def validate_mets(path: Path) -> None:
    payload = _read_private_bytes(path, "KUBG METS metadata", METS_SHA256)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise BabychAcousticExcerptIntakeError("cannot parse KUBG METS metadata") from exc
    require(root.attrib.get("OBJID") == SOURCE_METS_OBJID, "KUBG METS object identity drift")
    title = root.findtext(".//{http://www.loc.gov/mods/v3}title")
    require(title == SOURCE_METS_TITLE_CORRUPT, "KUBG METS corrupt-title provenance drift")
    given = root.findtext('.//{http://www.loc.gov/mods/v3}namePart[@type="given"]')
    family = root.findtext('.//{http://www.loc.gov/mods/v3}namePart[@type="family"]')
    require(given == SOURCE_METADATA_GIVEN, "KUBG METS author given-name drift")
    require(family == SOURCE_METADATA_FAMILY, "KUBG METS author family-name drift")
    issued = root.findtext(".//{http://www.loc.gov/mods/v3}dateIssued")
    require(issued == "2022", "KUBG METS year drift")
    publisher = root.findtext(".//{http://www.loc.gov/mods/v3}publisher")
    require(publisher == SOURCE_PUBLISHER, "KUBG METS publisher drift")
    files = root.findall(".//{http://www.loc.gov/METS/}file")
    require(len(files) == 1, "KUBG METS file denominator drift")
    source_file = files[0]
    require(source_file.attrib.get("ID") == SOURCE_METS_FILE_ID, "KUBG METS file identity drift")
    require(source_file.attrib.get("SIZE") == str(PDF_BYTES), "KUBG METS file size drift")
    require(source_file.attrib.get("OWNERID") == SOURCE_BITSTREAM_URL, "KUBG METS bitstream OWNERID drift")
    locations = source_file.findall("{http://www.loc.gov/METS/}FLocat")
    require(len(locations) == 1, "KUBG METS bitstream locator denominator drift")
    require(
        locations[0].attrib.get("{http://www.w3.org/1999/xlink}href") == SOURCE_BITSTREAM_URL,
        "KUBG METS bitstream locator drift",
    )


def validate_html_metadata(item_record: Path) -> None:
    item = _read_private_bytes(item_record, "KUBG item record", ITEM_RECORD_SHA256).decode("utf-8")
    meta = _html_meta(item)
    require(SOURCE_METADATA_AUTHOR in meta.get("DC.creator", []), "KUBG item author drift")
    require(SOURCE_METADATA_AUTHOR in meta.get("eprints.creators_name", []), "KUBG eprints author drift")
    require(SOURCE_TITLE in meta.get("DC.title", []), "KUBG item title drift")
    require(SOURCE_TITLE in meta.get("eprints.title", []), "KUBG eprints title drift")
    require(SOURCE_BITSTREAM_URL in meta.get("DC.identifier", []), "KUBG item bitstream locator drift")
    require(SOURCE_BITSTREAM_URL in meta.get("eprints.document_url", []), "KUBG eprints bitstream locator drift")
    require(SOURCE_ITEM_URL in meta.get("DC.relation", []), "KUBG item locator drift")
    require("2022" in meta.get("DC.date", []), "KUBG item year drift")
    require(SOURCE_ISBN in meta.get("eprints.isbn", []), "KUBG item ISBN drift")
    require("294" in meta.get("eprints.pages", []), "KUBG item catalog extent drift")
    require(SOURCE_AUTHOR_DISPLAY in item, "KUBG item display-name drift")
    require(SOURCE_METADATA_AUTHOR in item, "KUBG item metadata spelling-defect drift")


def validate_export_json(path: Path) -> None:
    export = _read_private_json(path, "KUBG export JSON", EXPORT_JSON_SHA256)
    require(export.get("eprintid") == int(SOURCE_EPRINT_ID), "KUBG export eprint identity drift")
    require(export.get("uri") == SOURCE_ITEM_URL_BARE, "KUBG export item locator drift")
    require(export.get("date") == 2022, "KUBG export year drift")
    require(export.get("isbn") == SOURCE_ISBN, "KUBG export ISBN drift")
    require(export.get("pages") == CATALOG_PRINT_COLLATION_PAGES, "KUBG export catalog extent drift")
    require(export.get("publisher") == SOURCE_PUBLISHER, "KUBG export publisher drift")
    titles = export.get("title")
    require(isinstance(titles, list) and titles, "KUBG export title missing")
    require(
        any(isinstance(row, Mapping) and row.get("text") == SOURCE_TITLE for row in titles), "KUBG export title drift"
    )
    creators = export.get("creators")
    require(isinstance(creators, list) and creators, "KUBG export creators missing")
    name = creators[0].get("name") if isinstance(creators[0], Mapping) else None
    require(isinstance(name, Mapping), "KUBG export creator name missing")
    require(name.get("given") == SOURCE_METADATA_GIVEN, "KUBG export author given-name drift")
    require(name.get("family") == SOURCE_METADATA_FAMILY, "KUBG export author family-name drift")
    documents = export.get("documents")
    require(isinstance(documents, list) and len(documents) == 1, "KUBG export document denominator drift")
    files = documents[0].get("files") if isinstance(documents[0], Mapping) else None
    require(isinstance(files, list) and len(files) == 1, "KUBG export file denominator drift")
    source_file = files[0]
    require(isinstance(source_file, Mapping), "KUBG export file missing")
    require(source_file.get("filesize") == PDF_BYTES, "KUBG export file size drift")
    require(source_file.get("hash_type") == "MD5", "KUBG export checksum type drift")
    require(source_file.get("hash") == PDF_MD5, "KUBG export checksum drift")
    require(source_file.get("filename") == "N_Babych_FTFZOA_FPSRSO.pdf", "KUBG export filename drift")


def build_receipt(
    *,
    source_pdf: Path,
    mets: Path,
    item_record: Path,
    export_json: Path,
) -> dict[str, Any]:
    text_facts = inspect_pdf(source_pdf)
    validate_mets(mets)
    validate_html_metadata(item_record)
    validate_export_json(export_json)
    observed_print_pages = dict(text_facts["observed_print_pages"])
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source": {
            "source_id": SOURCE_ID,
            "title": SOURCE_TITLE,
            "author_display": SOURCE_AUTHOR_DISPLAY,
            "author_metadata_raw": SOURCE_METADATA_AUTHOR,
            "author_metadata_spelling_defect_preserved": True,
            "institution": SOURCE_INSTITUTION,
            "publisher": SOURCE_PUBLISHER,
            "audience": "native_ukrainian_bachelor_programme_016_01_logopedia",
            "year": 2022,
            "isbn": SOURCE_ISBN,
            "catalog_print_collation_pages": CATALOG_PRINT_COLLATION_PAGES,
            "exact_bitstream_pages": PDF_PAGES,
            "bitstream_is_complete_publication": False,
            "bitstream_characterization": "curated_official_excerpt",
            "item_url": SOURCE_ITEM_URL,
            "bitstream_url": SOURCE_BITSTREAM_URL,
            "private_input_locator": PRIVATE_INPUT_LOCATOR,
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "mets_sha256": METS_SHA256,
            "item_record_sha256": ITEM_RECORD_SHA256,
            "export_json_sha256": EXPORT_JSON_SHA256,
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "text_layer": {
            "pages": text_facts["pages"],
            "text_bearing_pages": text_facts["text_bearing_pages"],
            "unicode_code_points": text_facts["unicode_code_points"],
            "utf8_bytes": text_facts["utf8_bytes"],
            "page_manifest_sha256": text_facts["page_manifest_sha256"],
            "extracted_text_sha256": text_facts["extracted_text_sha256"],
            "acroform_present": text_facts["acroform_present"],
            "form_field_count": text_facts["form_field_count"],
            "javascript_present": text_facts["javascript_present"],
            "source_isbn_text_verified": text_facts["source_isbn_text_verified"],
            "catalog_page_count_in_excerpt_text_verified": text_facts["catalog_page_count_in_excerpt_text_verified"],
            "normalization_applied": False,
            "ocr_used": False,
            "source_text_retained_in_public_receipt": False,
        },
        "excerpt_structure": {
            "pdf_pages": PDF_PAGES,
            "catalogued_publication_pages": CATALOG_PRINT_COLLATION_PAGES,
            "absent_pages_not_synthesized": True,
            "front_matter_pdf_pages": list(FRONT_MATTER_PDF_PAGES),
            "symbols_pdf_page": SYMBOLS_PDF_PAGE,
            "module_i_acoustic_begin_pdf_pages": list(MODULE_I_ACOUSTIC_PDF_PAGES),
            "colophon_pdf_page": COLOPHON_PDF_PAGE,
            "observed_print_pages": observed_print_pages,
            "discontinuities": list(DISCONTINUITIES),
            "acoustic_markers_present_verified": True,
            "acoustic_markers_set_sha256": ACOUSTIC_MARKERS_SET_SHA256,
        },
        "review_scope": {
            "content_disposition": "contextual_only",
            "ukrainian_source_review_complete": False,
            "scope_critic_complete": False,
            "topic_gaps_closed": [],
            "topic_gaps_narrowed": [],
            "coverage_effect": "pending_ukrainian_source_review",
            "closure_candidates_pending_matrix_critic": [],
        },
        "rights": {
            "standardized_license_present": False,
            "operator_private_attributed_research_use_directed": True,
            "legal_reuse_authorization_established": False,
            "attribution_required": True,
            "takedown_ready": True,
            "adapt_or_remove_on_substantiated_complaint": True,
            "public_redistribution_authorized": False,
            "unrestricted_reuse_authorized": False,
        },
        "gates": {
            "database_ingest_authorized": False,
            "retained_extracted_text_authorized": False,
            "private_training_conversion_candidate": False,
            "training_conversion_complete": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "The downloadable official bitstream is a 13-page curated excerpt, not the catalogued 294-page publication.",
            "Print-page discontinuities 8→20 and 23→colophon prove absent pages; those 281 pages must not be inferred.",
            "Engineering records mechanical excerpt structure only; no university topic is narrowed or closed.",
            "Ukrainian source-fitness review and scope criticism remain outstanding before any admission upgrade.",
            "Training conversion, database ingest, normative authority, semantic gold, and Phase 4 remain unauthorized.",
        ],
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "Babych excerpt candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise BabychAcousticExcerptIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(
        receipt["bindings"]["phase3_recovery_prompt_v2_sha256"] == V2_PROMPT_SHA256,
        "v2 prompt binding drift",
    )
    require(
        receipt["bindings"]["phase3_reboot_prompt_v3_sha256"] == V3_PROMPT_SHA256,
        "v3 prompt binding drift",
    )
    require(receipt["source"]["exact_bitstream_pages"] == PDF_PAGES, "receipt page-count overclaim")
    require(receipt["source"]["bitstream_is_complete_publication"] is False, "receipt full-book overclaim")
    require(receipt["source"]["catalog_print_collation_pages"] == CATALOG_PRINT_COLLATION_PAGES, "catalog extent drift")
    require(receipt["review_scope"]["content_disposition"] == "contextual_only", "content disposition drift")
    require(receipt["review_scope"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["review_scope"]["topic_gaps_narrowed"] == [], "receipt overclaims topic narrowing")
    require(
        receipt["review_scope"]["coverage_effect"] == "pending_ukrainian_source_review",
        "receipt overclaims coverage effect",
    )
    require(receipt["gates"]["source_coverage_ready"] is False, "receipt overclaims source coverage")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["gates"]["normative_rule_authority"] is False, "receipt overclaims normative_rule_authority")
    require(receipt["gates"]["semantic_gold"] is False, "receipt overclaims semantic_gold")
    require(receipt["gates"]["training_conversion_complete"] is False, "receipt overclaims training conversion")
    require(receipt["gates"]["database_ingest_authorized"] is False, "receipt overclaims database ingest")
    require(receipt["rights"]["public_redistribution_authorized"] is False, "receipt overclaims redistribution")
    require(
        receipt["rights"]["legal_reuse_authorization_established"] is False,
        "receipt overclaims legal reuse authorization",
    )
    require(receipt["excerpt_structure"]["absent_pages_not_synthesized"] is True, "absent-page synthesis drift")
    serialized = canonical_json(receipt)
    require("GoogleDrive-" not in serialized, "receipt leaks private Drive identity")
    require("@gmail.com" not in serialized, "receipt leaks private account identity")
    require("ФОНЕТИКА ТА ФОНОЛОГІЯ" not in serialized, "receipt retains private source text")
    require("децибел" not in serialized, "receipt retains private source text")
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise BabychAcousticExcerptIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


def write_public_receipt(path: Path, value: Mapping[str, Any]) -> None:
    require(_inside_git_checkout(path), "public receipt must live inside Git")
    _reject_symlink_components(path.parent, "public receipt parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    if path.exists() or path.is_symlink():
        require(_read_public_receipt_no_follow(path) == payload, "refusing to overwrite an immutable public receipt")
        return
    temporary: Path | None = None
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        require(_read_public_receipt_no_follow(path) == payload, "refusing to overwrite an immutable public receipt")
    except OSError as exc:
        raise BabychAcousticExcerptIntakeError("cannot atomically publish public receipt") from exc
    finally:
        temporary.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--mets", type=Path)
    parser.add_argument("--item-record", type=Path)
    parser.add_argument("--export-json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            require(
                not any((args.source_pdf, args.mets, args.item_record, args.export_json, args.output)),
                "check mode is exclusive",
            )
            receipt = validate_receipt(_read_json(args.check, "Babych excerpt candidate receipt"))
        else:
            required = {
                "--source-pdf": args.source_pdf,
                "--mets": args.mets,
                "--item-record": args.item_record,
                "--export-json": args.export_json,
                "--output": args.output,
            }
            missing = [name for name, item in required.items() if item is None]
            require(not missing, f"materialization mode requires: {', '.join(missing)}")
            receipt = build_receipt(
                source_pdf=args.source_pdf,
                mets=args.mets,
                item_record=args.item_record,
                export_json=args.export_json,
            )
            write_public_receipt(args.output, receipt)
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    except BabychAcousticExcerptIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
