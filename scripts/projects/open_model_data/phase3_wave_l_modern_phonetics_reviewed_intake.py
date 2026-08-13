#!/usr/bin/env python3
"""Record the qualified Ukrainian source review for Wave L modern-phonetics candidates.

Two private university PDFs and their acquisition receipts remain outside Git.
This module hash-binds custody, institutional metadata, the search receipt, and
the external qualified review result, then emits one text-free public receipt.
It does not mutate frozen audit v1, the v2 denominator, held-out identities,
database ingest, training conversion, semantic gold, source-universe freeze,
Phase 3 completion, or Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
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
SCHEMA_PATH = DATA / "contracts/phase3_wave_l_modern_phonetics_reviewed_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_wave_l_modern_phonetics_reviewed_v1.json"

SCHEMA_VERSION = "phase3_wave_l_modern_phonetics_reviewed_v1"
STATUS = "CONTEXTUAL_ONLY_QUALIFIED_UKRAINIAN_SOURCE_REVIEW_RECORDED"
ISSUE = 6375
WAVE = "phase3-6375-wave-l-modern-phonetics"
PRIVATE_INPUT_LOCATOR = "university_corpus/staging/phase3-6375-wave-l-modern-phonetics"
REVIEW_CUSTODY_SUBDIRECTORY = "qualified-source-review-fable"
REVIEW_RESULT_FILENAME = "phase3-6375-wave-l-qualified-source-review-fable.result"
REVIEW_CUSTODY_RECEIPT_FILENAME = "REVIEW-CUSTODY-RECEIPT.json"
REVIEW_CUSTODY_SCHEMA_VERSION = "phase3_wave_l_qualified_review_custody_v1"

V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
REVIEW_RESULT_SHA256 = "a35de95c7b9e05a0a09717fa25a76c4db5a59a521e1466f063a1a35ed67cdfba"
REVIEW_RESULT_BYTES = 9284
SEARCH_RECEIPT_SHA256 = "04884a0c9ddd980b8a2724e0caacf554140830e2fb519bf084a12d8f5c336c56"
REVIEWER_MODEL_X_HARNESS = "claude/claude-fable-5"
REVIEWER_SEAT = "qualified_ukrainian_source_review"

KOVALENKO_SOURCE_ID = "uni-ukrmova-phonetics-orthoepy-kovalenko-2024"
KOVALENKO_TITLE = "Сучасна українська літературна мова: Фонетика. Фонологія. Орфоепія. Графіка. Орфографія"
KOVALENKO_INSTITUTION = "Кам’янець-Подільський національний університет імені Івана Огієнка"
KOVALENKO_YEAR = 2024
KOVALENKO_PAGES = 172
KOVALENKO_PDF_SHA256 = "bc06ea99f5d3b32b975987851d48af0873442f52c24332d9503705ff822d6aaa"
KOVALENKO_PDF_MD5 = "09af974006d2ee23b29cad1f8e971721"
KOVALENKO_PDF_BYTES = 5_837_731
KOVALENKO_ACQUISITION_SHA256 = "8f07223b5add2a97e03101b5406cc4a8f1582b77a90f169eab3b472f790c9d9e"
KOVALENKO_METADATA_SHA256 = "3e70f88da7f4cf4b27d10a7fd1009348944ce98b8bb872640f06f28cfcf1e8c3"
KOVALENKO_RISK_CODES = [
    "course_manual_not_monographic_textbook",
    "acoustic_phonetics_survey_level_only",
    "accentology_stress_typology_without_paradigm_system",
]

YASHNYK_SOURCE_ID = "uni-ukrmova-acoustic-phonetics-yashnyk-2020"
YASHNYK_TITLE = "Акустичні засади розробки україномовних артикуляційних таблиць"
YASHNYK_INSTITUTION = (
    "Національний технічний університет України «Київський політехнічний інститут імені Ігоря Сікорського»"
)
YASHNYK_YEAR = 2020
YASHNYK_PAGES = 142
YASHNYK_PDF_SHA256 = "052e2c21578e7d24936923946f645edb0495a68373799b7a6508ff223e565169"
YASHNYK_PDF_MD5 = "c25391d609279325229ec77a46b3a70b"
YASHNYK_PDF_BYTES = 4_045_309
YASHNYK_ACQUISITION_SHA256 = "9a53cdd2cec53e6592860789a30cc9716d109c819e3bda86c4f1139c84aa9bad"
YASHNYK_METADATA_SHA256 = "5d87cf35f8e26f265d36518d7dd2906d6189990e9059f9138ddebff6f3422658"
YASHNYK_AUTHOR_AGREEMENT_SHA256 = "c61526195f43d10bd8c4622a1125ad4f96fee1232f2622910cfb53986db943b2"
YASHNYK_RISK_CODES = [
    "letters_sounds_phonemes_category_conflation",
    "nonstandard_balto_slavic_genealogical_label",
    "yellow_prince_author_attribution_error",
    "derivative_linguistics_russian_engineering_methods",
    "marginal_dialectal_table_lexemes",
]

TOPIC_MATRIX = {
    "phonetics": "partial_narrowed",
    "phonology": "partial_narrowed",
    "orthoepy": "partial_narrowed",
    "accentology": "partial_unchanged",
    "graphics": "partial_narrowed",
    "orthography": "sufficient_unchanged",
}
TOPICS_NARROWED = ["phonetics", "phonology", "orthoepy", "graphics"]
LEGACY_AUTHORIZATION_FIELDS = (
    "private_inspection_authorized",
    "operator_private_text_only_phase3_use_authorized",
    "operator_private_inspection_authorized",
    "operator_text_only_phase3_use_authorized",
)
PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


class WaveLModernPhoneticsReviewedIntakeError(ValueError):
    """The exact private Wave L custody or its fail-closed disposition drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WaveLModernPhoneticsReviewedIntakeError(message)


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
        raise WaveLModernPhoneticsReviewedIntakeError(f"cannot read artifact: {path}") from exc
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
        raise WaveLModernPhoneticsReviewedIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _qualified_review_source_allowed_in_git(path: Path) -> bool:
    resolved = Path(path).resolve()
    return resolved.name == REVIEW_RESULT_FILENAME and "batch_state" in resolved.parts and "tasks" in resolved.parts


def _read_bound_bytes(path: Path, label: str, expected_sha256: str, *, require_private_mode: bool = True) -> bytes:
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise WaveLModernPhoneticsReviewedIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    if require_private_mode:
        require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(
        not _inside_git_checkout(path) or _qualified_review_source_allowed_in_git(path),
        f"{label} cannot live inside Git",
    )
    try:
        before = Path(path).stat()
        payload = Path(path).read_bytes()
        after = Path(path).stat()
    except OSError as exc:
        raise WaveLModernPhoneticsReviewedIntakeError(f"cannot read {label}") from exc
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        f"{label} changed while reading",
    )
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, f"{label} byte drift")
    return payload


def _read_private_bytes(path: Path, label: str, expected_sha256: str) -> bytes:
    return _read_bound_bytes(path, label, expected_sha256, require_private_mode=True)


def _read_private_json(path: Path, label: str, expected_sha256: str) -> dict[str, Any]:
    payload = _read_private_bytes(path, label, expected_sha256)
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise WaveLModernPhoneticsReviewedIntakeError(f"cannot parse {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WaveLModernPhoneticsReviewedIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _reject_legacy_authorization_fields(value: Mapping[str, Any], label: str) -> None:
    serialized = canonical_json(value)
    for field in LEGACY_AUTHORIZATION_FIELDS:
        require(f'"{field}"' not in serialized, f"{label} retains legacy authorization field {field}")


def _verify_pdf_pages(path: Path, label: str, expected_pages: int, expected_bytes: int, expected_sha256: str) -> None:
    payload = _read_private_bytes(path, label, expected_sha256)
    require(len(payload) == expected_bytes, f"{label} byte denominator drift")
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise WaveLModernPhoneticsReviewedIntakeError(f"cannot parse {label}") from exc
    require(not reader.is_encrypted, f"{label} is unexpectedly encrypted")
    require(len(reader.pages) == expected_pages, f"{label} page denominator drift")


def validate_search_receipt(path: Path) -> dict[str, Any]:
    receipt = _read_private_json(path, "Wave L search receipt", SEARCH_RECEIPT_SHA256)
    require(
        receipt.get("schema_version") == "phase3_university_source_negative_search_receipt_v1", "search schema drift"
    )
    require(receipt.get("issue") == ISSUE, "search issue drift")
    require(receipt.get("wave") == WAVE, "search wave drift")
    require(receipt.get("preserved_candidate_count") == 2, "search candidate count drift")
    preserved = receipt.get("preserved_source_ids")
    require(
        preserved == [KOVALENKO_SOURCE_ID, YASHNYK_SOURCE_ID],
        "search preserved source identity drift",
    )
    phase_effect = receipt.get("phase_effect")
    require(isinstance(phase_effect, Mapping), "search phase effect missing")
    require(phase_effect.get("topic_gaps_closed") == 0, "search overclaims topic closure")
    require(phase_effect.get("topic_gaps_narrowed") is False, "search provisional narrowing drift")
    require(phase_effect.get("phase3_complete") is False, "search overclaims Phase 3 completion")
    require(phase_effect.get("phase4_blocked") is True, "search opens Phase 4")
    return receipt


def validate_acquisition_receipt(
    path: Path,
    *,
    label: str,
    expected_sha256: str,
    source_id: str,
    pdf_sha256: str,
    pdf_bytes: int,
    pdf_pages: int,
) -> dict[str, Any]:
    receipt = _read_private_json(path, label, expected_sha256)
    require(receipt.get("schema_version") == "phase3_university_source_acquisition_receipt_v1", f"{label} schema drift")
    require(receipt.get("issue") == ISSUE, f"{label} issue drift")
    require(receipt.get("wave") == WAVE, f"{label} wave drift")
    require(
        receipt.get("status") == "VERIFIED_DRIVE_CUSTODY_PENDING_QUALIFIED_SOURCE_DISPOSITION",
        f"{label} status drift",
    )
    source = receipt.get("source")
    require(isinstance(source, Mapping), f"{label} source missing")
    require(source.get("source_id") == source_id, f"{label} source identity drift")
    files = receipt.get("files")
    require(isinstance(files, list) and files, f"{label} files missing")
    pdf_row = next(
        (row for row in files if isinstance(row, Mapping) and row.get("role") == "immutable_source_bytes"), None
    )
    require(isinstance(pdf_row, Mapping), f"{label} PDF file row missing")
    require(pdf_row.get("sha256") == pdf_sha256, f"{label} PDF hash drift")
    require(pdf_row.get("bytes") == pdf_bytes, f"{label} PDF byte drift")
    inspection = receipt.get("deterministic_inspection")
    require(isinstance(inspection, Mapping), f"{label} inspection missing")
    require(inspection.get("pdf_pages") == pdf_pages, f"{label} page denominator drift")
    provisional = receipt.get("provisional_content_scope")
    require(isinstance(provisional, Mapping), f"{label} provisional scope missing")
    require(
        provisional.get("qualified_ukrainian_source_review_state") == "pending",
        f"{label} provisional review state drift",
    )
    gates = receipt.get("gates")
    require(isinstance(gates, Mapping), f"{label} gates missing")
    require(gates.get("topic_gaps_closed") == 0, f"{label} overclaims topic closure")
    require(gates.get("topic_gaps_narrowed") is False, f"{label} provisional narrowing drift")
    require(gates.get("phase3_complete") is False, f"{label} overclaims Phase 3 completion")
    require(gates.get("phase4_blocked") is True, f"{label} opens Phase 4")
    rights = receipt.get("rights_boundary")
    require(isinstance(rights, Mapping), f"{label} rights missing")
    require(rights.get("legal_reuse_authorization_established") is False, f"{label} overclaims legal reuse")
    require(rights.get("normative_rule_authority") is False, f"{label} overclaims normative authority")
    return receipt


def validate_review_result(path: Path) -> bytes:
    custody_path = path.parent.name == REVIEW_CUSTODY_SUBDIRECTORY or REVIEW_CUSTODY_SUBDIRECTORY in path.parts
    payload = _read_bound_bytes(
        path,
        "qualified Ukrainian source review",
        REVIEW_RESULT_SHA256,
        require_private_mode=custody_path,
    )
    require(len(payload) == REVIEW_RESULT_BYTES, "qualified review byte denominator drift")
    text = payload.decode("utf-8")
    require("topic_gaps_closed: 0" in text, "qualified review topic closure marker missing")
    require("topic_gaps_narrowed: true" in text, "qualified review narrowing marker missing")
    require("Kovalenko 2024 — PASS" in text, "qualified review Kovalenko verdict marker missing")
    require("Yashnyk 2020 — PASS" in text, "qualified review Yashnyk verdict marker missing")
    require("REJECT for any normative" in text, "qualified review Yashnyk authority rejection missing")
    return payload


def build_review_custody_receipt(review_bytes: int) -> dict[str, Any]:
    return {
        "schema_version": REVIEW_CUSTODY_SCHEMA_VERSION,
        "issue": ISSUE,
        "wave": WAVE,
        "reviewer_seat": REVIEWER_SEAT,
        "reviewer_model_x_harness": REVIEWER_MODEL_X_HARNESS,
        "review_result_filename": REVIEW_RESULT_FILENAME,
        "review_result_sha256": REVIEW_RESULT_SHA256,
        "review_result_bytes": review_bytes,
        "supersedes_provisional_interpretations": [
            "acquisition_receipt_provisional_content_scope",
            "acquisition_receipt_rights_boundary_contextual_private_inspection_only",
            "search_receipt_topic_gaps_narrowed_false",
        ],
        "acquisition_receipts_not_overwritten": True,
        "text_free": True,
    }


def write_review_drive_custody(
    wave_root: Path,
    review_source: Path,
    review_payload: bytes,
) -> Path:
    _reject_symlink_components(wave_root, "wave root")
    custody_dir = wave_root / REVIEW_CUSTODY_SUBDIRECTORY
    custody_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(custody_dir, PRIVATE_DIR_MODE)
    review_dest = custody_dir / REVIEW_RESULT_FILENAME
    if review_dest.exists():
        require(review_dest.read_bytes() == review_payload, "existing review custody byte drift")
    else:
        review_dest.write_bytes(review_payload)
    os.chmod(review_dest, PRIVATE_FILE_MODE)
    custody_receipt = build_review_custody_receipt(len(review_payload))
    custody_receipt_path = custody_dir / REVIEW_CUSTODY_RECEIPT_FILENAME
    custody_payload = canonical_bytes(custody_receipt)
    if custody_receipt_path.exists():
        require(custody_receipt_path.read_bytes() == custody_payload, "review custody receipt drift")
    else:
        custody_receipt_path.write_bytes(custody_payload)
    os.chmod(custody_receipt_path, PRIVATE_FILE_MODE)
    sums_lines = [
        f"{REVIEW_RESULT_SHA256}  {REVIEW_RESULT_FILENAME}",
        f"{sha256_bytes(custody_payload)}  {REVIEW_CUSTODY_RECEIPT_FILENAME}",
    ]
    sums_payload = ("\n".join(sums_lines) + "\n").encode("utf-8")
    sums_path = custody_dir / "SHA256SUMS"
    if sums_path.exists():
        require(sums_path.read_bytes() == sums_payload, "review custody SHA256SUMS drift")
    else:
        sums_path.write_bytes(sums_payload)
    os.chmod(sums_path, PRIVATE_FILE_MODE)
    return custody_dir


def build_receipt(
    *,
    search_receipt: Path,
    kovalenko_pdf: Path,
    kovalenko_metadata: Path,
    kovalenko_acquisition: Path,
    yashnyk_pdf: Path,
    yashnyk_metadata: Path,
    yashnyk_author_agreement: Path,
    yashnyk_acquisition: Path,
    review_result: Path,
    write_drive_custody: Path | None = None,
) -> dict[str, Any]:
    validate_search_receipt(search_receipt)
    validate_acquisition_receipt(
        kovalenko_acquisition,
        label="Kovalenko acquisition receipt",
        expected_sha256=KOVALENKO_ACQUISITION_SHA256,
        source_id=KOVALENKO_SOURCE_ID,
        pdf_sha256=KOVALENKO_PDF_SHA256,
        pdf_bytes=KOVALENKO_PDF_BYTES,
        pdf_pages=KOVALENKO_PAGES,
    )
    validate_acquisition_receipt(
        yashnyk_acquisition,
        label="Yashnyk acquisition receipt",
        expected_sha256=YASHNYK_ACQUISITION_SHA256,
        source_id=YASHNYK_SOURCE_ID,
        pdf_sha256=YASHNYK_PDF_SHA256,
        pdf_bytes=YASHNYK_PDF_BYTES,
        pdf_pages=YASHNYK_PAGES,
    )
    _verify_pdf_pages(
        kovalenko_pdf,
        "Kovalenko source PDF",
        KOVALENKO_PAGES,
        KOVALENKO_PDF_BYTES,
        KOVALENKO_PDF_SHA256,
    )
    _verify_pdf_pages(
        yashnyk_pdf,
        "Yashnyk source PDF",
        YASHNYK_PAGES,
        YASHNYK_PDF_BYTES,
        YASHNYK_PDF_SHA256,
    )
    _read_private_bytes(kovalenko_metadata, "Kovalenko item metadata", KOVALENKO_METADATA_SHA256)
    _read_private_bytes(yashnyk_metadata, "Yashnyk item metadata", YASHNYK_METADATA_SHA256)
    _read_private_bytes(
        yashnyk_author_agreement,
        "Yashnyk repository author agreement",
        YASHNYK_AUTHOR_AGREEMENT_SHA256,
    )
    review_payload = validate_review_result(review_result)
    if write_drive_custody is not None:
        write_review_drive_custody(write_drive_custody, review_result, review_payload)

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "issue": ISSUE,
        "wave": WAVE,
        "text_free": True,
        "producer_provider_calls": False,
        "review_provider_call_recorded": True,
        "private_input_locator": PRIVATE_INPUT_LOCATOR,
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "search_receipt_sha256": SEARCH_RECEIPT_SHA256,
            "qualified_ukrainian_source_review_sha256": REVIEW_RESULT_SHA256,
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "review": {
            "seat": REVIEWER_SEAT,
            "model_x_harness": REVIEWER_MODEL_X_HARNESS,
            "qualified_ukrainian_source_review_state": "reviewed",
            "topic_gaps_closed": 0,
            "topic_gaps_narrowed": True,
            "topic_matrix": dict(TOPIC_MATRIX),
            "topics_narrowed": list(TOPICS_NARROWED),
        },
        "sources": [
            {
                "source_id": KOVALENKO_SOURCE_ID,
                "title": KOVALENKO_TITLE,
                "institution": KOVALENKO_INSTITUTION,
                "year": KOVALENKO_YEAR,
                "exact_bitstream_pages": KOVALENKO_PAGES,
                "review_verdict": "pass",
                "final_disposition": "contextual_only",
                "qualified_ukrainian_source_review_state": "reviewed",
                "normative_rule_authority": False,
                "scoped_rule_corroboration": True,
                "normative_linguistic_rule_authority_rejected": False,
                "risk_codes": list(KOVALENKO_RISK_CODES),
                "bindings": {
                    "source_pdf_sha256": KOVALENKO_PDF_SHA256,
                    "source_pdf_md5": KOVALENKO_PDF_MD5,
                    "source_pdf_bytes": KOVALENKO_PDF_BYTES,
                    "acquisition_receipt_sha256": KOVALENKO_ACQUISITION_SHA256,
                    "item_metadata_sha256": KOVALENKO_METADATA_SHA256,
                },
            },
            {
                "source_id": YASHNYK_SOURCE_ID,
                "title": YASHNYK_TITLE,
                "institution": YASHNYK_INSTITUTION,
                "year": YASHNYK_YEAR,
                "exact_bitstream_pages": YASHNYK_PAGES,
                "review_verdict": "pass_contextual_only",
                "final_disposition": "contextual_only",
                "qualified_ukrainian_source_review_state": "reviewed",
                "normative_rule_authority": False,
                "scoped_rule_corroboration": False,
                "normative_linguistic_rule_authority_rejected": True,
                "risk_codes": list(YASHNYK_RISK_CODES),
                "bindings": {
                    "source_pdf_sha256": YASHNYK_PDF_SHA256,
                    "source_pdf_md5": YASHNYK_PDF_MD5,
                    "source_pdf_bytes": YASHNYK_PDF_BYTES,
                    "acquisition_receipt_sha256": YASHNYK_ACQUISITION_SHA256,
                    "item_metadata_sha256": YASHNYK_METADATA_SHA256,
                    "author_agreement_sha256": YASHNYK_AUTHOR_AGREEMENT_SHA256,
                },
            },
        ],
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
            "frozen_audit_v1_mutated": False,
            "v2_denominator_mutated": False,
            "heldout_identity_mutated": False,
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
            "Post-2019 dedicated theoretical phonetics and acoustic phonology textbook gap remains open.",
            "Post-2019 dedicated orthoepy handbook and current accentology normative handbook remain open.",
            "Applied instrumental acoustic data from Yashnyk does not substitute a non-applied theoretical monograph.",
            "Neither source establishes legal reuse, training conversion, ingest, or redistribution authorization.",
            "Frozen audit v1, the v2 denominator, and held-out identities were not modified by this lane.",
        ],
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "Wave L reviewed receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise WaveLModernPhoneticsReviewedIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(receipt["producer_provider_calls"] is False, "producer overclaims provider calls")
    require(receipt["review_provider_call_recorded"] is True, "external qualified review not recorded")
    require(receipt["review"]["topic_gaps_closed"] == 0, "receipt overclaims topic closure")
    require(receipt["review"]["topic_gaps_narrowed"] is True, "receipt underclaims topic narrowing")
    require(receipt["review"]["topic_matrix"] == TOPIC_MATRIX, "topic matrix drift")
    kovalenko = receipt["sources"][0]
    yashnyk = receipt["sources"][1]
    require(kovalenko["normative_rule_authority"] is False, "Kovalenko normative authority overclaim")
    require(kovalenko["scoped_rule_corroboration"] is True, "Kovalenko scoped corroboration drift")
    require(yashnyk["normative_linguistic_rule_authority_rejected"] is True, "Yashnyk authority rejection drift")
    require(yashnyk["normative_rule_authority"] is False, "Yashnyk normative authority overclaim")
    require(receipt["gates"]["frozen_audit_v1_mutated"] is False, "receipt mutates frozen audit v1")
    require(receipt["gates"]["v2_denominator_mutated"] is False, "receipt mutates v2 denominator")
    require(receipt["gates"]["heldout_identity_mutated"] is False, "receipt mutates held-out identities")
    require(receipt["gates"]["source_coverage_ready"] is False, "receipt overclaims source coverage")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(
        receipt["rights"]["legal_reuse_authorization_established"] is False,
        "receipt overclaims legal reuse authorization",
    )
    require(
        receipt["rights"]["operator_private_attributed_research_use_directed"] is True,
        "operator research direction drift",
    )
    _reject_legacy_authorization_fields(receipt, "public receipt")
    serialized = canonical_json(receipt)
    require("GoogleDrive-" not in serialized, "receipt leaks private Drive identity")
    require("@gmail.com" not in serialized, "receipt leaks private account identity")
    require("Барка" not in serialized, "receipt retains reviewer defect quotation")
    require("Манько" not in serialized, "receipt retains reviewer defect quotation")
    require("балто-слов" not in serialized, "receipt retains reviewer defect quotation")
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise WaveLModernPhoneticsReviewedIntakeError("cannot safely read existing public receipt") from exc
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
        raise WaveLModernPhoneticsReviewedIntakeError("cannot atomically publish public receipt") from exc
    finally:
        temporary.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-receipt", type=Path)
    parser.add_argument("--kovalenko-pdf", type=Path)
    parser.add_argument("--kovalenko-metadata", type=Path)
    parser.add_argument("--kovalenko-acquisition", type=Path)
    parser.add_argument("--yashnyk-pdf", type=Path)
    parser.add_argument("--yashnyk-metadata", type=Path)
    parser.add_argument("--yashnyk-author-agreement", type=Path)
    parser.add_argument("--yashnyk-acquisition", type=Path)
    parser.add_argument("--review-result", type=Path)
    parser.add_argument("--write-drive-custody", type=Path, help="Wave root for private review custody")
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
                        args.search_receipt,
                        args.kovalenko_pdf,
                        args.kovalenko_metadata,
                        args.kovalenko_acquisition,
                        args.yashnyk_pdf,
                        args.yashnyk_metadata,
                        args.yashnyk_author_agreement,
                        args.yashnyk_acquisition,
                        args.review_result,
                        args.output,
                        args.write_drive_custody,
                    )
                ),
                "check mode is exclusive",
            )
            receipt = validate_receipt(_read_json(args.check, "Wave L reviewed receipt"))
        else:
            required = {
                "--search-receipt": args.search_receipt,
                "--kovalenko-pdf": args.kovalenko_pdf,
                "--kovalenko-metadata": args.kovalenko_metadata,
                "--kovalenko-acquisition": args.kovalenko_acquisition,
                "--yashnyk-pdf": args.yashnyk_pdf,
                "--yashnyk-metadata": args.yashnyk_metadata,
                "--yashnyk-author-agreement": args.yashnyk_author_agreement,
                "--yashnyk-acquisition": args.yashnyk_acquisition,
                "--review-result": args.review_result,
                "--output": args.output,
            }
            missing = [name for name, item in required.items() if item is None]
            require(not missing, f"materialization mode requires: {', '.join(missing)}")
            receipt = build_receipt(
                search_receipt=args.search_receipt,
                kovalenko_pdf=args.kovalenko_pdf,
                kovalenko_metadata=args.kovalenko_metadata,
                kovalenko_acquisition=args.kovalenko_acquisition,
                yashnyk_pdf=args.yashnyk_pdf,
                yashnyk_metadata=args.yashnyk_metadata,
                yashnyk_author_agreement=args.yashnyk_author_agreement,
                yashnyk_acquisition=args.yashnyk_acquisition,
                review_result=args.review_result,
                write_drive_custody=args.write_drive_custody,
            )
            write_public_receipt(args.output, receipt)
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    except WaveLModernPhoneticsReviewedIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
