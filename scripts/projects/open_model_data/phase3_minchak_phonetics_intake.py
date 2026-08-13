#!/usr/bin/env python3
"""Verify the private KNLU Minchak 2023 phonetics/phonology intake.

The source remains outside Git. This module replays exact byte custody, the
complete embedded-text denominator, institutional metadata, and the qualified
Ukrainian source review, then emits one text-free candidate receipt. It does
not authorize source-wide normative authority, semantic gold, database ingest,
source-universe freeze, Phase 3 completion, or Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
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
SCHEMA_PATH = DATA / "contracts/phase3_minchak_phonetics_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_minchak_phonetics_candidate_v1.json"

SCHEMA_VERSION = "phase3_minchak_phonetics_candidate_v1"
STATUS = "ADMIT_SCOPED_CANDIDATE_PENDING_SCOPE_CRITIC_AND_DETERMINISTIC_CONVERSION"
SOURCE_ID = "uni-ukrmova-phonetics-phonology-minchak-2023"
SOURCE_TITLE = "Фонетика і фонологія сучасної української літературної мови в таблицях і схемах"
SOURCE_AUTHOR = "Мінчак Галина Богданівна"
SOURCE_METADATA_AUTHOR = "Мінчак, Галина Богданівна"
SOURCE_INSTITUTION = "Київський національний лінгвістичний університет"
SOURCE_PUBLISHER = "Видавничий центр КНЛУ"
SOURCE_ISBN = "978-966-638-406-8 (Online)"
SOURCE_CATALOG_CITATION = (
    "Мінчак Г. Б. Фонетика і фонологія сучасної української літературної мови в таблицях і "
    "схемах : [навч. посібник] / Г. Б. Мінчак. - К.: Видав. центр КНЛУ, 2023. - 131 с."
)
SOURCE_HANDLE = "787878787/5318"
SOURCE_ITEM_URL = f"http://rep.knlu.edu.ua/xmlui/handle/{SOURCE_HANDLE}"
SOURCE_BITSTREAM_PATH = (
    "/xmlui/bitstream/handle/787878787/5318/"
    "%d0%a4%d0%be%d0%bd%d0%b5%d1%82%d0%b8%d0%ba%d0%b0%20%d1%96%20"
    "%d1%84%d0%be%d0%bd%d0%be%d0%bb%d0%be%d0%b3%d1%96%d1%8f.%20"
    "%d0%97%d0%b1%d1%96%d1%80%d0%bd%d0%b8%d0%ba.pdf?sequence=3&isAllowed=y"
)
SOURCE_BITSTREAM_URL = f"http://rep.knlu.edu.ua{SOURCE_BITSTREAM_PATH}"
SOURCE_METS_ITEM_UUID = "b88efe62-fdda-480f-a1cb-ffc0172dd7e7"
SOURCE_METS_FILE_UUID = "214276b5-284b-48f0-baab-2f12f6bc92da"

PDF_SHA256 = "a855d53d8b1c4c59282eac68628b343d343bad9c2d9ae168018a4fd665a2db57"
PDF_MD5 = "0acaec4c19c5fc31e0bccea40dc76dae"
PDF_BYTES = 2_096_966
PDF_PAGES = 96
CATALOG_PRINT_COLLATION_PAGES = 131
TEXT_BEARING_PAGES = 96
SUBSTANTIVE_PAGES = 95
INTENTIONAL_BLANK_PAGES = [59]
UNICODE_CODE_POINTS = 140_275
UTF8_BYTES = 242_197
PAGE_MANIFEST_SHA256 = "318d76f1ed75d00d298fe342d8e0a46920408f44820779518fc88a8105cfe67c"
EXTRACTED_TEXT_SHA256 = "878c5c622fc9b35c11d193e6cb1ccfe05dade850745fe0ca70a196fed969e894"
METS_SHA256 = "a107c5d3e6a1bf0905dbbd14dd5e113f35720c98dd07f53adc0178a400b9372b"
ITEM_RECORD_SHA256 = "7a79963772a19300ff540cbb617a0de183f06902b046ad237f04749c3862a374"
PUBLICATIONS_PAGE_SHA256 = "a55145353724c21b75f9afbf56c1ed7cb119d57e1762d70a27e229a58e5c9870"
REVIEW_RESULT_SHA256 = "9f160639407f422470626aac43efec9a605627c7c3622681575c923b3fa79494"
V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"

CLOSURE_CANDIDATES = ["phonology"]
TOPICS_NARROWED = [
    "phonetics",
    "orthoepy",
    "accentology",
    "graphics",
    "dialectology",
    "historical_grammar",
    "history_of_literary_language",
]
RISK_CONTROLS = [
    "unkeyed_exercises_not_gold",
    "accentology_dublets_missing_stress_marks",
    "soviet_era_orthoepic_base_requires_current_verification",
    "russian_comparison_and_davnoruska_spans_quarantined",
    "typo_and_table_errors_require_claim_verification",
    "transcription_spans_require_image_verification",
    "duplicate_assimilation_blocks_require_deduplication",
    "exact_96_page_bitstream_is_the_only_citation_denominator",
]
PRIVATE_FILE_MODE = 0o600


class MinchakPhoneticsIntakeError(ValueError):
    """The exact private source or its fail-closed disposition drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MinchakPhoneticsIntakeError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise MinchakPhoneticsIntakeError(f"cannot read artifact: {path}") from exc
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
        raise MinchakPhoneticsIntakeError(f"missing {label}: {path}") from exc
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
        raise MinchakPhoneticsIntakeError(f"cannot read {label}") from exc
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
        raise MinchakPhoneticsIntakeError(f"cannot parse {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MinchakPhoneticsIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def inspect_pdf(path: Path) -> dict[str, Any]:
    """Reproduce complete text-layer facts without retaining source text."""
    payload = _read_private_bytes(path, "Minchak source PDF", PDF_SHA256)
    require(len(payload) == PDF_BYTES, "Minchak source PDF byte denominator drift")
    require(hashlib.md5(payload, usedforsecurity=False).hexdigest() == PDF_MD5, "Minchak source PDF MD5 drift")
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise MinchakPhoneticsIntakeError("cannot parse Minchak source PDF") from exc
    require(not reader.is_encrypted, "Minchak source PDF is unexpectedly encrypted")
    require(len(reader.pages) == PDF_PAGES, "Minchak source PDF page denominator drift")
    require(
        len(reader.pages) != CATALOG_PRINT_COLLATION_PAGES,
        "Minchak PDF overclaims the full 131-page book",
    )
    page_rows: list[dict[str, Any]] = []
    complete_text: list[str] = []
    blank_pages: list[int] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise MinchakPhoneticsIntakeError(f"cannot extract Minchak source page {page_number}") from exc
        require(text.strip(), f"Minchak source page {page_number} has no embedded text")
        if re.fullmatch(rf"\s*{page_number}\s*", text):
            blank_pages.append(page_number)
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
    manifest_payload = b"".join(canonical_bytes(row) for row in page_rows)
    complete_source_text = "\n\f\n".join(complete_text)
    require(SOURCE_ISBN in complete_source_text, "Minchak source PDF ISBN drift")
    require(
        re.search(rf"2023\.\s+{CATALOG_PRINT_COLLATION_PAGES}\s+с\.", complete_source_text) is not None,
        "Minchak source PDF catalog collation drift",
    )
    joined_text = complete_source_text.encode("utf-8")
    root = reader.trailer["/Root"]
    if hasattr(root, "get_object"):
        root = root.get_object()
    facts = {
        "pages": len(page_rows),
        "text_bearing_pages": sum(bool(text.strip()) for text in complete_text),
        "substantive_pages": len(page_rows) - len(blank_pages),
        "intentional_blank_pages": blank_pages,
        "unicode_code_points": sum(row["chars"] for row in page_rows),
        "utf8_bytes": sum(row["bytes"] for row in page_rows),
        "page_manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "extracted_text_sha256": hashlib.sha256(joined_text).hexdigest(),
        "acroform_present": "/AcroForm" in root,
        "form_field_count": len(reader.get_fields() or {}),
        "javascript_present": bool("/Names" in root and "/JavaScript" in root["/Names"]),
        "source_isbn_text_verified": True,
        "catalog_page_count_in_bitstream_text_verified": True,
    }
    require(
        facts
        == {
            "pages": PDF_PAGES,
            "text_bearing_pages": TEXT_BEARING_PAGES,
            "substantive_pages": SUBSTANTIVE_PAGES,
            "intentional_blank_pages": INTENTIONAL_BLANK_PAGES,
            "unicode_code_points": UNICODE_CODE_POINTS,
            "utf8_bytes": UTF8_BYTES,
            "page_manifest_sha256": PAGE_MANIFEST_SHA256,
            "extracted_text_sha256": EXTRACTED_TEXT_SHA256,
            "acroform_present": True,
            "form_field_count": 0,
            "javascript_present": False,
            "source_isbn_text_verified": True,
            "catalog_page_count_in_bitstream_text_verified": True,
        },
        "Minchak complete text-layer facts drift",
    )
    return facts


def validate_mets(path: Path) -> None:
    payload = _read_private_bytes(path, "KNLU METS metadata", METS_SHA256)
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise MinchakPhoneticsIntakeError("cannot parse KNLU METS metadata") from exc
    require(root.attrib.get("ID") == f"hdl:{SOURCE_HANDLE}", "KNLU METS handle drift")
    require(root.attrib.get("OBJEDIT", "").endswith(SOURCE_METS_ITEM_UUID), "KNLU METS item UUID drift")
    fields = {
        (element.attrib.get("element"), element.attrib.get("qualifier")): element.text or ""
        for element in root.findall(".//{http://www.dspace.org/xmlns/dspace/dim}field")
    }
    require(fields.get(("contributor", "author")) == SOURCE_METADATA_AUTHOR, "KNLU METS author drift")
    require(fields.get(("date", "issued")) == "2023", "KNLU METS year drift")
    require(fields.get(("identifier", "uri")) == SOURCE_ITEM_URL, "KNLU METS item locator drift")
    require(fields.get(("title", None)) == SOURCE_TITLE, "KNLU METS title drift")
    require(fields.get(("type", None)) == "Book", "KNLU METS type drift")
    require(fields.get(("publisher", None)) == SOURCE_CATALOG_CITATION, "KNLU METS catalog citation drift")
    require(not any(element == "rights" for element, _qualifier in fields), "KNLU METS invents rights metadata")
    files = root.findall(".//{http://www.loc.gov/METS/}file")
    require(len(files) == 1, "KNLU METS file denominator drift")
    source_file = files[0]
    require(source_file.attrib.get("SIZE") == str(PDF_BYTES), "KNLU METS file size drift")
    require(source_file.attrib.get("CHECKSUMTYPE") == "MD5", "KNLU METS checksum type drift")
    require(source_file.attrib.get("CHECKSUM") == PDF_MD5, "KNLU METS checksum drift")
    require(SOURCE_METS_FILE_UUID in source_file.attrib.get("ID", ""), "KNLU METS file UUID drift")
    locations = source_file.findall("{http://www.loc.gov/METS/}FLocat")
    require(len(locations) == 1, "KNLU METS bitstream locator denominator drift")
    require(
        locations[0].attrib.get("{http://www.w3.org/TR/xlink/}href") == SOURCE_BITSTREAM_PATH,
        "KNLU METS bitstream locator drift",
    )


def validate_html_metadata(item_record: Path, publications_page: Path) -> None:
    item = _read_private_bytes(item_record, "KNLU item record", ITEM_RECORD_SHA256).decode("utf-8")
    meta: dict[str, list[str]] = {}
    for match in re.finditer(r"<meta\s+([^>]+?)/?>", item, flags=re.IGNORECASE):
        attributes = {
            key.lower(): value
            for key, value in re.findall(r"([A-Za-z_:.-]+)\s*=\s*[\"']([^\"']*)[\"']", match.group(1))
        }
        if "name" in attributes and "content" in attributes:
            meta.setdefault(attributes["name"], []).append(attributes["content"])
    require(SOURCE_METADATA_AUTHOR in meta.get("DC.creator", []), "KNLU item author drift")
    require(SOURCE_TITLE in meta.get("DC.title", []), "KNLU item title drift")
    require(SOURCE_ITEM_URL in meta.get("DC.identifier", []), "KNLU item locator drift")
    require("2023" in meta.get("citation_date", []), "KNLU item year drift")
    require(SOURCE_CATALOG_CITATION in meta.get("DC.publisher", []), "KNLU item catalog citation drift")
    require("DC.rights" not in item, "KNLU item unexpectedly declares rights metadata")
    publications = _read_private_bytes(
        publications_page,
        "KNLU official publications page",
        PUBLICATIONS_PAGE_SHA256,
    ).decode("utf-8")
    require(SOURCE_TITLE in publications, "KNLU official publication title drift")
    require(SOURCE_HANDLE in publications, "KNLU official publication locator drift")


def validate_review(path: Path, text_facts: Mapping[str, Any]) -> dict[str, Any]:
    review = _read_private_json(path, "Minchak Ukrainian source review", REVIEW_RESULT_SHA256)
    require(
        review.get("schema_version") == "phase3_minchak_knlu_source_fitness_review_v1",
        "review schema drift",
    )
    identity = review.get("reviewer_identity")
    require(isinstance(identity, Mapping), "reviewer identity missing")
    require(identity.get("seat") == "Ukrainian Source Reviewer", "reviewer seat drift")
    require(identity.get("model_x_harness") == "claude/claude-fable-5 via native Claude CLI", "review model drift")
    require(identity.get("read_only") is True, "review was not read-only")
    require(review.get("source_id") == SOURCE_ID, "review source identity drift")
    bindings = review.get("input_bindings_verified")
    require(isinstance(bindings, Mapping), "review bindings missing")
    require(bindings.get("all_bound_hashes_matched") is True, "review bindings did not match")
    require(bindings.get("input_drift") == "none", "review reports input drift")
    expected = {
        "pdf_sha256": PDF_SHA256,
        "pdf_md5": PDF_MD5,
        "pdf_bytes": PDF_BYTES,
        "pdf_pages_actual": PDF_PAGES,
        "pages_with_embedded_text": TEXT_BEARING_PAGES,
        "substantive_pages": SUBSTANTIVE_PAGES,
        "mets_sha256": METS_SHA256,
        "item_record_sha256": ITEM_RECORD_SHA256,
        "publications_page_sha256": PUBLICATIONS_PAGE_SHA256,
        "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
    }
    for key, value in expected.items():
        require(bindings.get(key) == value, f"review binding drift: {key}")
    require(text_facts["intentional_blank_pages"] == INTENTIONAL_BLANK_PAGES, "review blank-page context drift")
    require(review.get("recommended_disposition") == "admit_scoped_candidate", "review disposition drift")
    require(review.get("topic_gaps_closed") == [], "review overclaims a closed topic gap")
    require(
        [row.get("area") for row in review.get("closure_candidates_pending_matrix_critic", [])]
        == CLOSURE_CANDIDATES,
        "review closure-candidate drift",
    )
    topic_effect = review.get("topic_gate_effect")
    require(isinstance(topic_effect, Mapping), "review topic effects missing")
    require(topic_effect.get("phonology") == "closure_candidate_pending_matrix_critic", "phonology effect drift")
    for topic in TOPICS_NARROWED:
        require(str(topic_effect.get(topic, "")).startswith("narrows_only"), f"review narrowed topic drift: {topic}")
    require(review.get("retained_extracted_text_authorized") is False, "review retains extracted text")
    require(review.get("private_training_conversion_candidate") is True, "private candidate lane drift")
    for key in (
        "public_redistribution_authorized",
        "normative_rule_authority",
        "semantic_gold",
        "source_universe_freeze_authorized",
        "database_ingest_authorized",
        "phase3_complete",
    ):
        require(review.get(key) is False, f"review overclaims {key}")
    require(review.get("phase4_blocked") is True, "review opens Phase 4")
    return review


def build_receipt(
    *,
    source_pdf: Path,
    mets: Path,
    item_record: Path,
    publications_page: Path,
    review_result: Path,
) -> dict[str, Any]:
    text_facts = inspect_pdf(source_pdf)
    validate_mets(mets)
    validate_html_metadata(item_record, publications_page)
    review = validate_review(review_result, text_facts)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source": {
            "source_id": SOURCE_ID,
            "title": SOURCE_TITLE,
            "author": SOURCE_AUTHOR,
            "institution": SOURCE_INSTITUTION,
            "publisher": SOURCE_PUBLISHER,
            "audience": "native_ukrainian_bachelor_programme_014",
            "year": 2023,
            "isbn": SOURCE_ISBN,
            "catalog_print_collation_pages": CATALOG_PRINT_COLLATION_PAGES,
            "exact_bitstream_pages": PDF_PAGES,
            "bitstream_is_complete_publication": False,
            "item_url": SOURCE_ITEM_URL,
            "bitstream_url": SOURCE_BITSTREAM_URL,
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "mets_sha256": METS_SHA256,
            "item_record_sha256": ITEM_RECORD_SHA256,
            "official_publications_page_sha256": PUBLICATIONS_PAGE_SHA256,
            "ukrainian_source_review_sha256": REVIEW_RESULT_SHA256,
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "text_layer": {
            **dict(text_facts),
            "normalization_applied": False,
            "ocr_used": False,
            "source_text_retained_in_public_receipt": False,
        },
        "review": {
            "seat": review["reviewer_identity"]["seat"],
            "model_x_harness": review["reviewer_identity"]["model_x_harness"],
            "content_disposition": review["recommended_disposition"],
            "topic_gaps_closed": [],
            "closure_candidates_pending_matrix_critic": list(CLOSURE_CANDIDATES),
            "topic_gaps_narrowed": list(TOPICS_NARROWED),
            "risk_controls": list(RISK_CONTROLS),
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
            "scope_critic_complete": False,
            "database_ingest_authorized": False,
            "retained_extracted_text_authorized": False,
            "private_training_conversion_candidate": True,
            "training_conversion_complete": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "The source closes no frozen topic; phonology alone is a closure candidate for the matrix critic.",
            "Phonetics remains partial because acoustic and physical phonetics are survey-level only.",
            "Current orthoepy, accentology, graphics, and historical-language gaps remain open.",
            "Deterministic role conversion must quarantine known defects and image-verify transcription spans.",
            "Database ingest and source-universe freeze remain separately unauthorized.",
        ],
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "Minchak candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise MinchakPhoneticsIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(receipt["review"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["review"]["closure_candidates_pending_matrix_critic"] == CLOSURE_CANDIDATES, "closure drift")
    require(receipt["gates"]["source_coverage_ready"] is False, "receipt overclaims source coverage")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["source"]["exact_bitstream_pages"] == PDF_PAGES, "receipt page-count overclaim")
    require(
        receipt["source"]["bitstream_is_complete_publication"] is False,
        "receipt full-book overclaim",
    )
    require(
        receipt["source"]["catalog_print_collation_pages"] == CATALOG_PRINT_COLLATION_PAGES,
        "catalog extent drift",
    )
    require(
        receipt["text_layer"]["catalog_page_count_in_bitstream_text_verified"] is True,
        "catalog page-count statement drift",
    )
    require(
        receipt["rights"]["legal_reuse_authorization_established"] is False,
        "receipt overclaims legal reuse authorization",
    )
    require(
        "operator_private_text_only_phase3_use_authorized" not in receipt["rights"],
        "receipt retains legacy operator authorization field",
    )
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise MinchakPhoneticsIntakeError("cannot safely read existing public receipt") from exc
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
        raise MinchakPhoneticsIntakeError("cannot atomically publish public receipt") from exc
    finally:
        temporary.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--mets", type=Path)
    parser.add_argument("--item-record", type=Path)
    parser.add_argument("--publications-page", type=Path)
    parser.add_argument("--review-result", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            require(
                not any(
                    (
                        args.source_pdf,
                        args.mets,
                        args.item_record,
                        args.publications_page,
                        args.review_result,
                        args.output,
                    )
                ),
                "check mode is exclusive",
            )
            receipt = validate_receipt(_read_json(args.check, "Minchak candidate receipt"))
        else:
            required = {
                "--source-pdf": args.source_pdf,
                "--mets": args.mets,
                "--item-record": args.item_record,
                "--publications-page": args.publications_page,
                "--review-result": args.review_result,
                "--output": args.output,
            }
            missing = [name for name, item in required.items() if item is None]
            require(not missing, f"materialization mode requires: {', '.join(missing)}")
            receipt = build_receipt(
                source_pdf=args.source_pdf,
                mets=args.mets,
                item_record=args.item_record,
                publications_page=args.publications_page,
                review_result=args.review_result,
            )
            write_public_receipt(args.output, receipt)
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    except MinchakPhoneticsIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
