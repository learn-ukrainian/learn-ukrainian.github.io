#!/usr/bin/env python3
"""Admit the private Pliush 2005 canonical-grammar official NBUV bitstream.

Private Google Drive custody is already root-verified. This module publishes one
text-free public candidate receipt that binds those private hashes, official
locators, page-count discrepancy, corrected page map, NBUV rights, and
ACADEMIC_CANON / NARROW_ONLY dispositions. It does not authorize database
ingest, training export, semantic gold, topic-gap closure/narrowing,
source-universe freeze, Phase 3 completion, or Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_pliush_2005_canonical_grammar_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_pliush_2005_canonical_grammar_candidate_v1.json"
UNIVERSITY_FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
SOURCE_POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"

SCHEMA_VERSION = "phase3_pliush_2005_canonical_grammar_candidate_v1"
STATUS = "ACADEMIC_CANON_CORROBORATION_CANDIDATE_NO_GAP_TRANSITION"
SOURCE_ID = "uni-ukrmova-grammar-morphemics-word-formation-morphology-pliush-2005"
SOURCE_TITLE = "Граматика української мови. Ч. 1 : Морфеміка. Словотвір. Морфологія"
SOURCE_AUTHORS = ["Марія Яківна Плющ"]
SOURCE_METADATA_AUTHORS = ["Плющ, Марія Яківна", "Плющ М. Я."]
SOURCE_INSTITUTION = "НБУВ / електронна бібліотека «Україніка» (irbis-nbuv.gov.ua)"
SOURCE_PUBLISHER = "Київ: Вища школа"
SOURCE_WORK_ISBN = "966-642-264-6"
SOURCE_PART_1_ISBN = "966-642-263-8"
SOURCE_ITEM_ID = "UKR0000663"
SOURCE_PDF_ID = "ukr0000402"
SOURCE_ITEM_URL = f"https://irbis-nbuv.gov.ua/ulib/item/{SOURCE_ITEM_ID}"
SOURCE_PDF_URL = f"https://irbis-nbuv.gov.ua/E_LIB/PDF/{SOURCE_PDF_ID}.pdf"
SOURCE_ONLINE_BOOK_URL = (
    "https://irbis-nbuv.gov.ua/cgi-bin/ua/elib.exe?C21COM=S&I21DBN=UKRLIB&P21DBN=UKRLIB"
    "&S21CNR=20&S21FMT=online_book&S21P01=0&S21P02=0&S21P03=FF%3D&S21REF=10"
    f"&S21STN=1&S21STR={SOURCE_PDF_ID}&Z21ID="
)
PRIVATE_INPUT_LOCATOR = "university_corpus/staging/phase3-6375-pliush-2005-canonical-grammar"

PDF_FILENAME = "source/pliush-2005-grammar-morphemics-word-formation-morphology.pdf"
ITEM_HTML_FILENAME = "metadata/ukrainica-item-UKR0000663.html"
ONLINE_BOOK_HTML_FILENAME = "metadata/ukrainica-online-book-ukr0000402.html"
PDF_HEADERS_FILENAME = "metadata/pliush-2005-pdf-response-headers.txt"
ITEM_HEADERS_FILENAME = "metadata/ukrainica-item-response-headers.txt"
ONLINE_BOOK_HEADERS_FILENAME = "metadata/ukrainica-online-book-response-headers.txt"

PDF_SHA256 = "af0e2fea1756d6b3a79fb2b94d8b9cf6b1e66afb4f1587b1bb46cdabe70d2f5e"
PDF_MD5 = "788711c54e286f38e23b8d452474a067"
PDF_BYTES = 7_548_590
PDF_PAGE_OBJECTS = 289
TITLE_IMPRINT_PAGES = 286
NBUV_PRESENTATION_PAGES = 288
TEXT_BEARING_PAGES = 289
EMPTY_TEXT_PAGES: list[int] = []
UNICODE_CODE_POINTS = 576_759
UTF8_BYTES = 1_022_704
PAGE_MANIFEST_SHA256 = "01e7d3fb72cd2a483e82c280cdb03418cd512082c5d26f44d43330076df85070"
EXTRACTED_TEXT_SHA256 = "bde4c529607ea36a78fd79edd44904a1f32b8a6a95c716264fb7654403cf26b3"
ITEM_HTML_SHA256 = "e36bae96dd222f695fccdced53d13ea21027cded7f6581d21113ec5cc9dacc15"
ITEM_HTML_BYTES = 222_581
ONLINE_BOOK_HTML_SHA256 = "16660eba2e50b65f8daac5d7cbb79fa25787590990977fe05ff3b49edee34a55"
ONLINE_BOOK_HTML_BYTES = 216_860
PDF_HEADERS_SHA256 = "5db1f21afecdc04d1eeca0c0175b0ec6a9204b6e771630bf042ac76c8aa310a6"
PDF_HEADERS_BYTES = 265
ITEM_HEADERS_SHA256 = "8b3c2f376df7f71ae0d721628de367e96b9c3fc2abbd6a78d0917e03eace6d5b"
ITEM_HEADERS_BYTES = 190
ONLINE_BOOK_HEADERS_SHA256 = "e7422225627740e65bed0d3a01df5ec692924878d91f5299851c54d296dac1dc"
ONLINE_BOOK_HEADERS_BYTES = 190

AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256 = {
    "item_html": "ea43f1d3fb510285307d4c7888d3bf6e228cc1dc68bb61be46f09eec561ad721",
    "item_response_headers": "9e742934373f3a8d5c5c5257a9bba022f39796ccea0666dc89ea78afcaa84291",
    "online_book_html": "0cce75c32619711f34689d3db2a2c3723f5f3bbd90f9b1950b6705402e2b0f21",
    "online_book_response_headers": "a943fa23dd86f1c0aae5e28af3cc0e634005da6d6a8c45d039fd12137f7c79bf",
    "pdf_response_headers": "e08725d437150d999fedb513a427c155dc4c94d6d036e347377af5eaf4d5e51e",
    "source_pdf": "ad7c320f5dc6adc1b71f54a16ea2923aa7fc4360b162d292125eb2c2ce7b5148",
}

V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
V2_SOURCE_UNITS = 67_041
V2_EVALUATION_IDENTITIES = 9_392
PHASE3_LABELS = 0
UNIVERSITY_TOPIC_AREAS = 26
UNIVERSITY_SUFFICIENT = 5
UNIVERSITY_PARTIAL = 21
UNIVERSITY_MISSING = 0
CANDIDATE_SOURCE_COUNT = 30
DATABASE_RESIDENT_SOURCE_COUNT = 20
REFERENCE_ONLY_SOURCE_COUNT = 6
QUARANTINE_SOURCE_COUNT = 4
UNIVERSITY_FREEZE_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"
SOURCE_POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
MORPHEMICS_QUALIFIED_SOURCE_NEEDED = (
    "Dedicated post-2019 university textbook on morphemics and morphemic structure of Ukrainian words."
)
WORD_FORMATION_QUALIFIED_SOURCE_NEEDED = (
    "Specialized university coursebook on Ukrainian word formation (дериватологія)."
)
FREEZE_WORD_FORMATION_AREA = "word formation"
PRIMARY_CELLS = ["morphemics", "word_formation"]
SECONDARY_CELLS = ["morphology"]
VISUAL_QA_PASSED_PDF_PAGES = [3, 8, 21, 70, 283, 289]
RIGHTS_STATEMENT = (
    "NBUV Ukrainica educational/scientific noncommercial use with attribution; "
    "no downstream reproduction of full texts"
)
NBUV_TERMS = "educational_and_scientific_noncommercial_with_attribution_no_downstream_full_text_reproduction"

PAGE_MAP: dict[str, Any] = {
    "body_mapping_rule": "pdf_object_equals_printed_page_plus_one",
    "prior_advisory_off_by_one_corrected": True,
    "morphemics": {"pdf_start": 8, "pdf_end": 20, "printed_start": 7, "printed_end": 19},
    "word_formation": {"pdf_start": 21, "pdf_end": 69, "printed_start": 20, "printed_end": 68},
    "morphology_main_body": {"pdf_start": 70, "pdf_end": 280, "printed_start": 69, "printed_end": 279},
    "abbreviations": {"pdf_start": 281, "pdf_end": 282, "printed_start": 280, "printed_end": 281},
    "contents": {"pdf_start": 283, "pdf_end": 287, "printed_start": 282, "printed_end": 286},
    "colophon_pdf_page": 289,
}

CONTENT_FITNESS: dict[str, Any] = {
    "adversarial_dispositions": {
        "morphemics": "NARROW_ONLY",
        "morphology": "SECONDARY_CORROBORATION",
        "word_formation": "NARROW_ONLY",
    },
    "audience": {
        "current_ukrainian_philology_students": True,
        "publication_period_post_2019": False,
        "publication_year": 2005,
        "publisher_institution": "Вища школа (Kyiv); custody via NBUV Ukrainica",
        "repository_type": "Book",
    },
    "cells": {
        "morphemics": {
            "disposition": "NARROW_ONLY",
            "frozen_status": "partial",
            "provisional_effect": "academic_canon_theory_corroboration_not_a_gap_transition",
            "qualified_source_needed": MORPHEMICS_QUALIFIED_SOURCE_NEEDED,
            "rationale_codes": [
                "dedicated_pre_2019_university_pidruchnyk_title_and_toc",
                "full_theory_morphemics_block_pdf_8_20",
                "fails_literal_post_2019_freeze_need",
                "canonical_theory_corroboration_only",
                "no_topic_gap_closure_or_narrowing",
            ],
            "role": "canonical_theory_corroboration",
        },
        "word_formation": {
            "disposition": "NARROW_ONLY",
            "frozen_status": "partial",
            "provisional_effect": "academic_canon_theory_corroboration_not_a_gap_transition",
            "qualified_source_needed": WORD_FORMATION_QUALIFIED_SOURCE_NEEDED,
            "rationale_codes": [
                "dedicated_pre_2019_university_pidruchnyk_title_and_toc",
                "full_theory_word_formation_block_pdf_21_69",
                "fails_literal_current_specialized_freeze_need",
                "canonical_theory_corroboration_only",
                "no_topic_gap_closure_or_narrowing",
            ],
            "role": "canonical_theory_corroboration",
        },
    },
    "document_profile": {
        "genre": "university_philology_pidruchnyk_academic_canon_theory",
        "printed_page_offset_note": (
            "Body mapping: PDF object = printed page + 1; imprint cites 286 pp; "
            "NBUV presentation may say 288; PDF has 289 objects — recorded, not repaired"
        ),
    },
    "explicit_limitations": [
        "Pliush 2005 is Ukrainian academic-canon theory evidence, not modern-currency closure.",
        "Fails the frozen literal post-2019 / dedicated specialized need for morphemics and word formation.",
        "No university topic gap is closed or narrowed by this custody packet.",
        "Morphology is secondary corroboration only; not a morphology gap transition.",
        "Title/imprint cites 286 pages; NBUV presentation may say 288; PDF has 289 objects.",
        "ISBN 966-642-264-6 identifies the two-part work; ISBN 966-642-263-8 identifies Part I.",
        "Public full-text export and unrestricted training export remain false.",
        "No DB ingest, source-universe freeze, semantic gold, author/eval membership, or Phase 4.",
    ],
    "provisional_effect": "academic_canon_corroboration_candidate_no_gap_transition",
    "secondary_observation_cells": {
        "morphology": {
            "disposition": "SECONDARY_CORROBORATION",
            "provisional_effect": "academic_canon_secondary_corroboration_not_a_gap_transition",
            "rationale_codes": [
                "deep_morphology_main_body_pdf_70_280",
                "pre_2019_cannot_satisfy_modern_morphology_freeze_need",
                "secondary_corroboration_only",
            ],
            "role": "secondary_corroboration",
        }
    },
    "target_cells": list(PRIMARY_CELLS),
    "topic_gaps_closed": [],
    "topic_gaps_narrowed_claimed": [],
}

CUSTODY_ARTIFACTS = {
    "item_html": ITEM_HTML_FILENAME,
    "item_response_headers": ITEM_HEADERS_FILENAME,
    "online_book_html": ONLINE_BOOK_HTML_FILENAME,
    "online_book_response_headers": ONLINE_BOOK_HEADERS_FILENAME,
    "pdf_response_headers": PDF_HEADERS_FILENAME,
    "source_pdf": PDF_FILENAME,
}

PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700
TRACKED_PUBLIC_FILE_MODE = 0o644
ACCEPTED_PUBLIC_RECEIPT_MODES = frozenset({PRIVATE_FILE_MODE, TRACKED_PUBLIC_FILE_MODE})
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"
DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0
DEFAULT_XATTR_TIMEOUT_SECONDS: float = 30.0


class Pliush2005CanonicalGrammarIntakeError(ValueError):
    """Exact identity, custody, rights, or fail-closed disposition drifted."""


class DriveIdentityPendingError(Pliush2005CanonicalGrammarIntakeError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Pliush2005CanonicalGrammarIntakeError(message)


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
        raise Pliush2005CanonicalGrammarIntakeError(f"cannot read artifact: {path}") from exc
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
        raise Pliush2005CanonicalGrammarIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _private_directory(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISDIR(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a directory")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_DIR_MODE, f"{label} must be mode 0700")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _regular_public(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    mode = stat.S_IMODE(result.st_mode)
    require(mode in ACCEPTED_PUBLIC_RECEIPT_MODES, f"{label} permissions must be 0600 or tracked 0644")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Pliush2005CanonicalGrammarIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def default_drive_project_root() -> Path:
    try:
        drive_roots = [
            candidate
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError("cannot inspect configured Google Drive mounts") from exc
    require(len(drive_roots) == 1, "expected exactly one configured Google Drive mount")
    return drive_roots[0] / "My Drive" / "Projects" / "learn-ukrainian-data"


def default_staging_root() -> Path:
    return default_drive_project_root() / PRIVATE_INPUT_LOCATOR


def _drive_item_id(path: Path) -> str:
    resolved = path.resolve()
    try:
        drive_roots = [
            candidate.resolve()
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError("cannot inspect configured Google Drive mounts") from exc
    matches = [root for root in drive_roots if resolved.is_relative_to(root)]
    require(len(matches) == 1, "artifact is not inside exactly one configured Google Drive mount")
    try:
        probe = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=DEFAULT_XATTR_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise DriveIdentityPendingError("artifact lacks Google Drive provider identity") from exc
    value = probe.stdout.strip()
    require(value, "artifact has an empty Google Drive provider identity")
    return value


def _wait_for_drive_item_id(
    path: Path,
    *,
    timeout_seconds: float = DRIVE_IDENTITY_TIMEOUT_SECONDS,
    poll_seconds: float = DRIVE_IDENTITY_POLL_SECONDS,
) -> str:
    require(timeout_seconds >= 0, "Google Drive identity timeout must be non-negative")
    require(poll_seconds >= 0, "Google Drive identity poll interval must be non-negative")
    deadline = time.monotonic() + timeout_seconds
    last_error: DriveIdentityPendingError | None = None
    while True:
        try:
            return _drive_item_id(path)
        except DriveIdentityPendingError as exc:
            last_error = exc
        if time.monotonic() >= deadline:
            raise Pliush2005CanonicalGrammarIntakeError(
                f"artifact did not acquire Google Drive provider identity within {timeout_seconds:g} seconds"
            ) from last_error
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))


def _verify_drive_readback(path: Path, expected_sha256: str) -> str:
    readback = sha256_file(path)
    require(readback == expected_sha256, "Drive read-back hash mismatch")
    return _wait_for_drive_item_id(path)


def validate_authoritative_university_state(
    *,
    university_freeze_path: Path | None = None,
    source_policy_path: Path | None = None,
) -> dict[str, str]:
    freeze_path = university_freeze_path if university_freeze_path is not None else UNIVERSITY_FREEZE_PATH
    policy_path = source_policy_path if source_policy_path is not None else SOURCE_POLICY_PATH
    require(freeze_path.is_file(), "missing university content-audit freeze")
    require(policy_path.is_file(), "missing complete source policy v4")
    freeze_sha256 = sha256_file(freeze_path)
    policy_sha256 = sha256_file(policy_path)
    require(freeze_sha256 == UNIVERSITY_FREEZE_SHA256, "university content-audit freeze hash drift")
    require(policy_sha256 == SOURCE_POLICY_SHA256, "complete source policy v4 hash drift")

    freeze = _read_json(freeze_path, "university content-audit freeze")
    counts = freeze.get("topic_coverage", {}).get("counts")
    require(isinstance(counts, Mapping), "university freeze topic counts missing")
    require(counts.get("areas_required") == UNIVERSITY_TOPIC_AREAS, "university topic-area denominator drift")
    require(counts.get("sufficient") == UNIVERSITY_SUFFICIENT, "university sufficient denominator drift")
    require(counts.get("partial") == UNIVERSITY_PARTIAL, "university partial denominator drift")
    require(counts.get("missing") == UNIVERSITY_MISSING, "university missing denominator drift")

    source_universe = freeze.get("source_universe")
    require(isinstance(source_universe, Mapping), "university freeze source_universe missing")
    require(
        source_universe.get("candidate_source_count") == CANDIDATE_SOURCE_COUNT,
        "university candidate-source denominator drift",
    )
    require(
        source_universe.get("database_resident_source_count") == DATABASE_RESIDENT_SOURCE_COUNT,
        "university database-resident denominator drift",
    )
    require(
        source_universe.get("reference_only_source_count") == REFERENCE_ONLY_SOURCE_COUNT,
        "university reference-only denominator drift",
    )
    require(
        source_universe.get("quarantine_source_count") == QUARANTINE_SOURCE_COUNT,
        "university quarantine denominator drift",
    )

    topics = freeze.get("topic_coverage", {}).get("topics")
    require(isinstance(topics, list), "university freeze topics missing")
    by_area = {topic.get("area"): topic for topic in topics if isinstance(topic, Mapping)}
    morphemics = by_area.get("morphemics")
    word_formation = by_area.get(FREEZE_WORD_FORMATION_AREA)
    require(isinstance(morphemics, Mapping), "university freeze morphemics topic missing")
    require(isinstance(word_formation, Mapping), "university freeze word formation topic missing")
    require(morphemics.get("status") == "partial", "university freeze morphemics status drift")
    require(word_formation.get("status") == "partial", "university freeze word formation status drift")
    require(
        morphemics.get("qualified_source_needed") == MORPHEMICS_QUALIFIED_SOURCE_NEEDED,
        "university freeze morphemics qualified-source need drift",
    )
    require(
        word_formation.get("qualified_source_needed") == WORD_FORMATION_QUALIFIED_SOURCE_NEEDED,
        "university freeze word formation qualified-source need drift",
    )

    freeze_gates = freeze.get("gates")
    require(isinstance(freeze_gates, Mapping), "university freeze gates missing")
    require(freeze_gates.get("source_coverage_ready") is False, "university freeze overclaims source coverage")
    require(freeze_gates.get("phase3_complete") is False, "university freeze overclaims Phase 3 completion")
    require(freeze_gates.get("phase4_blocked") is True, "university freeze opens Phase 4")
    require(
        freeze_gates.get("overall_phase3_source_freeze_ready") is False,
        "university freeze overclaims overall Phase 3 source freeze readiness",
    )

    policy = _read_json(policy_path, "complete source policy v4")
    require(policy.get("phase3_complete") is False, "source policy overclaims Phase 3 completion")
    require(policy.get("phase4_blocked") is True, "source policy opens Phase 4")
    require(policy.get("source_freeze_ready") is False, "source policy overclaims source freeze readiness")
    require(policy.get("source_count") == CANDIDATE_SOURCE_COUNT, "source policy candidate denominator drift")
    disposition_counts = policy.get("disposition_counts")
    require(isinstance(disposition_counts, Mapping), "source policy disposition counts missing")
    require(disposition_counts.get("quarantine") == QUARANTINE_SOURCE_COUNT, "source policy quarantine drift")
    require(disposition_counts.get("total") == CANDIDATE_SOURCE_COUNT, "source policy total drift")
    return {
        "university_content_audit_freeze_v1_sha256": freeze_sha256,
        "complete_source_policy_v4_sha256": policy_sha256,
    }


def build_custody_block() -> dict[str, Any]:
    return {
        "google_drive_custody": True,
        "google_drive_mount_containment_verified": True,
        "google_drive_provider_identity_present": True,
        "google_drive_provider_identity_sha256": dict(AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256),
        "drive_relative_directory": PRIVATE_INPUT_LOCATOR,
        "private_files_mode_0600": True,
        "private_directory_mode_0700": True,
        "all_new_files_readback_hash_match": True,
        "artifacts": dict(CUSTODY_ARTIFACTS),
    }


def build_receipt_body() -> dict[str, Any]:
    authoritative = validate_authoritative_university_state()
    content_fitness = json.loads(canonical_json(CONTENT_FITNESS))
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source": {
            "source_id": SOURCE_ID,
            "title": SOURCE_TITLE,
            "authors": list(SOURCE_AUTHORS),
            "metadata_authors": list(SOURCE_METADATA_AUTHORS),
            "institution": SOURCE_INSTITUTION,
            "publisher": SOURCE_PUBLISHER,
            "audience": "native_ukrainian_philology_higher_education_students",
            "year": 2005,
            "work_isbn": SOURCE_WORK_ISBN,
            "part_1_isbn": SOURCE_PART_1_ISBN,
            "isbn_roles_recorded": True,
            "pages": PDF_PAGE_OBJECTS,
            "title_imprint_pages": TITLE_IMPRINT_PAGES,
            "nbuv_presentation_pages": NBUV_PRESENTATION_PAGES,
            "page_count_discrepancy_recorded": True,
            "item_url": SOURCE_ITEM_URL,
            "pdf_url": SOURCE_PDF_URL,
            "online_book_url": SOURCE_ONLINE_BOOK_URL,
            "private_input_locator": PRIVATE_INPUT_LOCATOR,
            "bitstream_is_complete_publication": True,
            "repository_custody": "NBUV Ukrainica irbis-nbuv.gov.ua",
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "item_html_sha256": ITEM_HTML_SHA256,
            "item_html_bytes": ITEM_HTML_BYTES,
            "online_book_html_sha256": ONLINE_BOOK_HTML_SHA256,
            "online_book_html_bytes": ONLINE_BOOK_HTML_BYTES,
            "pdf_response_headers_sha256": PDF_HEADERS_SHA256,
            "pdf_response_headers_bytes": PDF_HEADERS_BYTES,
            "item_response_headers_sha256": ITEM_HEADERS_SHA256,
            "item_response_headers_bytes": ITEM_HEADERS_BYTES,
            "online_book_response_headers_sha256": ONLINE_BOOK_HEADERS_SHA256,
            "online_book_response_headers_bytes": ONLINE_BOOK_HEADERS_BYTES,
            "university_content_audit_freeze_v1_sha256": authoritative["university_content_audit_freeze_v1_sha256"],
            "complete_source_policy_v4_sha256": authoritative["complete_source_policy_v4_sha256"],
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "text_layer": {
            "pages": PDF_PAGE_OBJECTS,
            "text_bearing_pages": TEXT_BEARING_PAGES,
            "empty_text_pages": list(EMPTY_TEXT_PAGES),
            "unicode_code_points": UNICODE_CODE_POINTS,
            "utf8_bytes": UTF8_BYTES,
            "page_manifest_sha256": PAGE_MANIFEST_SHA256,
            "extracted_text_sha256": EXTRACTED_TEXT_SHA256,
            "anomaly_page_count": 0,
            "encrypted": False,
            "isbn_text_verified": True,
            "page_count_discrepancy": {
                "title_imprint_pages": TITLE_IMPRINT_PAGES,
                "nbuv_presentation_pages": NBUV_PRESENTATION_PAGES,
                "pdf_page_objects": PDF_PAGE_OBJECTS,
                "recorded_without_correction": True,
            },
            "normalization_applied": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
        },
        "page_map": json.loads(canonical_json(PAGE_MAP)),
        "visual_qa": {
            "passed_pdf_pages": list(VISUAL_QA_PASSED_PDF_PAGES),
            "native_anomaly_detector_flagged_pages": 0,
        },
        "native_exactness": {
            "flagged_page_count": 0,
            "pdf_page_objects": PDF_PAGE_OBJECTS,
            "text_bearing_pages": TEXT_BEARING_PAGES,
            "production_eligible_under_exactness_gate": False,
            "production_eligible_note": (
                "native anomaly detector flagged 0 pages; academic-canon corroboration only, "
                "not a production gap transition"
            ),
        },
        "content_fitness": content_fitness,
        "custody": build_custody_block(),
        "rights": {
            "visibility": "publicly_accessible_national_library_digital_library",
            "nbuv_terms": NBUV_TERMS,
            "rights_statement": RIGHTS_STATEMENT,
            "attribution_required": True,
            "private_acquisition": True,
            "private_audit": True,
            "private_training_preparation": True,
            "public_full_text_export": False,
            "unrestricted_training_export": False,
            "public_redistribution_authorized": False,
            "public_dataset_export_authorized": False,
            "publish_source_text_authorized": False,
            "unrestricted_reuse_authorized": False,
            "legal_reuse_authorization_established": False,
            "takedown_ready": True,
            "adapt_or_remove_on_substantiated_complaint": True,
        },
        "review_scope": {
            "content_disposition": "academic_canon_corroboration_candidate",
            "ukrainian_canon_review_complete": False,
            "scope_critic_complete": False,
            "topic_gaps_closed": [],
            "topic_gaps_narrowed": [],
            "primary_cells": list(PRIMARY_CELLS),
            "secondary_cells": list(SECONDARY_CELLS),
            "adversarial_dispositions": {
                "morphemics": "NARROW_ONLY",
                "word_formation": "NARROW_ONLY",
                "morphology": "SECONDARY_CORROBORATION",
            },
            "coverage_effect": "academic_canon_corroboration_no_gap_transition",
        },
        "denominators": {
            "v2_source_units": V2_SOURCE_UNITS,
            "v2_evaluation_identities": V2_EVALUATION_IDENTITIES,
            "phase3_labels": PHASE3_LABELS,
            "university_topic_areas": UNIVERSITY_TOPIC_AREAS,
            "university_sufficient": UNIVERSITY_SUFFICIENT,
            "university_partial": UNIVERSITY_PARTIAL,
            "university_missing": UNIVERSITY_MISSING,
            "candidate_source_count": CANDIDATE_SOURCE_COUNT,
            "database_resident_source_count": DATABASE_RESIDENT_SOURCE_COUNT,
            "reference_only_source_count": REFERENCE_ONLY_SOURCE_COUNT,
            "quarantine_source_count": QUARANTINE_SOURCE_COUNT,
            "candidate_additive_outside_v2_totals": True,
            "cycle002_diagnostic_only": True,
        },
        "gates": {
            "database_ingest_authorized": False,
            "retained_extracted_text_authorized": False,
            "private_training_conversion_candidate": False,
            "training_conversion_complete": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "author_eval_membership": False,
            "topic_gaps_closed": False,
            "topic_gaps_narrowed": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
            "phase4_authorized": False,
        },
        "residuals": [
            "Exact official bytes are privately custodied; Git retains metadata only.",
            "Native anomaly detector flagged 0 of 289 text-bearing PDF pages.",
            "Pliush is academic-canon theory corroboration for morphemics/word formation; morphology is secondary only.",
            "No topic gap is closed or narrowed; post-2019 freeze need remains unmet.",
            "Imprint 286 / NBUV presentation 288 / PDF objects 289 — discrepancy recorded, not corrected.",
            "ISBN roles preserved: 966-642-264-6 for the two-part work; 966-642-263-8 for Part I.",
            "NBUV terms allow educational/scientific noncommercial use with attribution; no full-text downstream reproduction.",
            "Public full-text export and unrestricted training export remain false.",
            "v2 denominators preserved: 67,041 / 9,392; Phase 3 incomplete; Phase 4 blocked.",
        ],
    }


def mint_receipt() -> dict[str, Any]:
    body = build_receipt_body()
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "Pliush candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise Pliush2005CanonicalGrammarIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    authoritative = validate_authoritative_university_state()
    require(receipt["status"] == STATUS, "status drift")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(
        receipt["bindings"]["university_content_audit_freeze_v1_sha256"]
        == authoritative["university_content_audit_freeze_v1_sha256"],
        "university freeze binding drift",
    )
    require(
        receipt["bindings"]["complete_source_policy_v4_sha256"] == authoritative["complete_source_policy_v4_sha256"],
        "source policy binding drift",
    )
    require(receipt["bindings"]["phase3_recovery_prompt_v2_sha256"] == V2_PROMPT_SHA256, "v2 prompt binding drift")
    require(receipt["bindings"]["phase3_reboot_prompt_v3_sha256"] == V3_PROMPT_SHA256, "v3 prompt binding drift")
    require(receipt["bindings"]["source_pdf_sha256"] == PDF_SHA256, "receipt PDF hash drift")
    require(receipt["bindings"]["source_pdf_bytes"] == PDF_BYTES, "receipt PDF bytes drift")
    require(receipt["bindings"]["source_pdf_md5"] == PDF_MD5, "receipt PDF MD5 drift")
    require(receipt["bindings"]["item_html_sha256"] == ITEM_HTML_SHA256, "item HTML hash drift")
    require(receipt["bindings"]["online_book_html_sha256"] == ONLINE_BOOK_HTML_SHA256, "online-book HTML hash drift")
    require(
        receipt["custody"]["google_drive_provider_identity_sha256"]
        == AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256,
        "google drive provider identity mapping drift",
    )
    require(receipt["source"]["source_id"] == SOURCE_ID, "source identity drift")
    require(receipt["source"]["item_url"] == SOURCE_ITEM_URL, "source item locator drift")
    require(receipt["source"]["pdf_url"] == SOURCE_PDF_URL, "source PDF locator drift")
    require(receipt["source"]["work_isbn"] == SOURCE_WORK_ISBN, "work ISBN drift")
    require(receipt["source"]["part_1_isbn"] == SOURCE_PART_1_ISBN, "Part I ISBN drift")
    require(receipt["source"]["isbn_roles_recorded"] is True, "ISBN roles are not recorded")
    require(receipt["source"]["year"] == 2005, "publication year drift")
    require(receipt["source"]["title"] == SOURCE_TITLE, "source title drift")
    require(receipt["content_fitness"]["audience"]["publication_year"] == 2005, "content-fitness year drift")
    require(
        receipt["content_fitness"]["audience"]["publication_period_post_2019"] is False,
        "receipt overclaims modern/post-2019 status",
    )
    require(receipt["page_map"] == PAGE_MAP, "page map drift")
    require(
        receipt["page_map"]["morphemics"] == PAGE_MAP["morphemics"],
        "morphemics page-map boundary drift",
    )
    require(
        receipt["page_map"]["word_formation"] == PAGE_MAP["word_formation"],
        "word-formation page-map boundary drift",
    )
    require(
        receipt["page_map"]["morphology_main_body"] == PAGE_MAP["morphology_main_body"],
        "morphology page-map boundary drift",
    )
    require(receipt["visual_qa"]["passed_pdf_pages"] == VISUAL_QA_PASSED_PDF_PAGES, "visual QA page drift")
    require(
        receipt["text_layer"]["page_count_discrepancy"]["recorded_without_correction"] is True,
        "page-count discrepancy must remain recorded without correction",
    )
    require(receipt["text_layer"]["ocr_used"] is False, "receipt overclaims OCR")
    require(receipt["text_layer"]["repairs_applied"] is False, "receipt overclaims repairs")
    require(receipt["review_scope"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["review_scope"]["topic_gaps_narrowed"] == [], "receipt overclaims topic narrowing")
    require(receipt["content_fitness"]["topic_gaps_closed"] == [], "content-fitness overclaims closure")
    require(receipt["content_fitness"]["topic_gaps_narrowed_claimed"] == [], "content-fitness overclaims narrowing")
    require(
        receipt["content_fitness"]["cells"]["morphemics"]["role"] == "canonical_theory_corroboration",
        "morphemics role expansion",
    )
    require(
        receipt["content_fitness"]["cells"]["word_formation"]["role"] == "canonical_theory_corroboration",
        "word_formation role expansion",
    )
    require(
        receipt["content_fitness"]["secondary_observation_cells"]["morphology"]["role"] == "secondary_corroboration",
        "morphology role expansion",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["morphemics"] == "NARROW_ONLY",
        "morphemics disposition drift",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["word_formation"] == "NARROW_ONLY",
        "word_formation disposition drift",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["morphology"] == "SECONDARY_CORROBORATION",
        "morphology disposition drift",
    )
    require(receipt["gates"]["semantic_gold"] is False, "receipt overclaims semantic gold")
    require(receipt["gates"]["database_ingest_authorized"] is False, "receipt overclaims database ingest")
    require(receipt["gates"]["author_eval_membership"] is False, "receipt overclaims author/eval membership")
    require(receipt["gates"]["topic_gaps_closed"] is False, "receipt overclaims topic gap closure")
    require(receipt["gates"]["topic_gaps_narrowed"] is False, "receipt overclaims topic gap narrowing")
    require(receipt["gates"]["source_freeze_ready"] is False, "receipt overclaims source freeze readiness")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["gates"]["phase4_authorized"] is False, "receipt overclaims Phase 4 authorization")
    require(receipt["denominators"]["v2_source_units"] == V2_SOURCE_UNITS, "v2 source-unit denominator drift")
    require(
        receipt["denominators"]["v2_evaluation_identities"] == V2_EVALUATION_IDENTITIES,
        "v2 evaluation denominator drift",
    )
    require(receipt["rights"]["rights_statement"] == RIGHTS_STATEMENT, "rights statement drift")
    require(receipt["rights"]["nbuv_terms"] == NBUV_TERMS, "NBUV terms drift")
    require(receipt["rights"]["private_acquisition"] is True, "private acquisition rights drift")
    require(receipt["rights"]["private_audit"] is True, "private audit rights drift")
    require(receipt["rights"]["private_training_preparation"] is True, "private training-preparation rights drift")
    require(receipt["rights"]["public_full_text_export"] is False, "receipt overclaims public full-text export")
    require(
        receipt["rights"]["unrestricted_training_export"] is False,
        "receipt overclaims unrestricted training export",
    )
    require(receipt["rights"]["public_redistribution_authorized"] is False, "receipt overclaims redistribution")
    receipt_body = {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    require(receipt_body == build_receipt_body(), "receipt body drift")
    serialized = canonical_json(receipt)
    require("GoogleDrive-" not in serialized, "receipt leaks private Drive identity")
    require("@gmail.com" not in serialized, "receipt leaks private account identity")
    require("/Users/" not in serialized, "receipt leaks absolute private path")
    require("Library/CloudStorage" not in serialized, "receipt leaks absolute private path")
    require("\f" not in serialized, "receipt retains extracted page-join markers")
    require("page_texts" not in receipt, "receipt retains private page texts")
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


def write_public_receipt(path: Path, value: Mapping[str, Any]) -> None:
    """Idempotent public receipt publish with atomic first-create semantics."""
    require(_inside_git_checkout(path), "public receipt must live inside Git")
    _reject_symlink_components(path.parent, "public receipt parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    if path.exists() or path.is_symlink():
        _regular_public(path, "public receipt")
        require(
            _read_public_receipt_no_follow(path) == payload,
            "refusing to overwrite an immutable public receipt",
        )
        return
    temporary: Path | None = None
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.chmod(temporary, 0o600)
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        _regular_public(path, "public receipt")
        require(
            _read_public_receipt_no_follow(path) == payload,
            "refusing to overwrite an immutable public receipt",
        )
    except OSError as exc:
        raise Pliush2005CanonicalGrammarIntakeError("cannot atomically publish public receipt") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def private_audit(staging_root: Path | None = None) -> dict[str, Any]:
    """Rehash the private Drive packet against authoritative constants. Mutates nothing."""
    staging = staging_root or default_staging_root()
    _private_directory(staging, "staging root")
    _private_directory(staging / "source", "source directory")
    _private_directory(staging / "metadata", "metadata directory")

    checks = {
        "source_pdf": (staging / PDF_FILENAME, PDF_SHA256, PDF_BYTES),
        "item_html": (staging / ITEM_HTML_FILENAME, ITEM_HTML_SHA256, ITEM_HTML_BYTES),
        "online_book_html": (staging / ONLINE_BOOK_HTML_FILENAME, ONLINE_BOOK_HTML_SHA256, ONLINE_BOOK_HTML_BYTES),
        "pdf_response_headers": (staging / PDF_HEADERS_FILENAME, PDF_HEADERS_SHA256, PDF_HEADERS_BYTES),
        "item_response_headers": (staging / ITEM_HEADERS_FILENAME, ITEM_HEADERS_SHA256, ITEM_HEADERS_BYTES),
        "online_book_response_headers": (
            staging / ONLINE_BOOK_HEADERS_FILENAME,
            ONLINE_BOOK_HEADERS_SHA256,
            ONLINE_BOOK_HEADERS_BYTES,
        ),
    }
    provider_ids: dict[str, str] = {}
    for label, (path, expected_sha, expected_bytes) in checks.items():
        _private_regular_file(path, label)
        require(sha256_file(path) == expected_sha, f"{label} hash drift")
        require(path.stat().st_size == expected_bytes, f"{label} byte denominator drift")
        if label in AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256:
            provider_ids[label] = _verify_drive_readback(path, expected_sha)

    provider_identity_sha256 = {
        name: sha256_bytes(value.encode("utf-8")) for name, value in sorted(provider_ids.items())
    }
    require(
        provider_identity_sha256 == AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256,
        "google drive provider identity mapping drift",
    )
    return {
        "ok": True,
        "staging_root": str(PRIVATE_INPUT_LOCATOR),
        "artifact_count": len(checks),
        "provider_identity_sha256": provider_identity_sha256,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="validate an existing public receipt")
    parser.add_argument(
        "--mint",
        action="store_true",
        help="mint the authoritative public receipt from frozen constants (no private Drive required)",
    )
    parser.add_argument(
        "--write",
        type=Path,
        default=DEFAULT_PUBLIC_RECEIPT_PATH,
        help="output path for --mint",
    )
    parser.add_argument(
        "--private-audit",
        action="store_true",
        help="rehash the private Drive packet against authoritative constants",
    )
    parser.add_argument("--staging-root", type=Path, help="private Drive staging directory")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            require(not args.mint and not args.private_audit, "check mode is exclusive")
            receipt = validate_receipt(_read_json(args.check, "Pliush candidate receipt"))
            print(
                canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]})
            )
        elif args.private_audit:
            require(not args.mint, "private-audit mode is exclusive of mint")
            result = private_audit(args.staging_root)
            print(canonical_json(result))
        elif args.mint:
            receipt = mint_receipt()
            write_public_receipt(args.write, receipt)
            print(
                canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]})
            )
        else:
            raise Pliush2005CanonicalGrammarIntakeError("specify --check, --mint, or --private-audit")
    except Pliush2005CanonicalGrammarIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
