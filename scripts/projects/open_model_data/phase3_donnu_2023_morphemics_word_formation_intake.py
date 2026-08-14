#!/usr/bin/env python3
"""Admit the private DonNU 2023 morphemics/word-formation official bitstream.

Private Google Drive custody is already root-verified. This module publishes one
text-free public candidate receipt that binds those private hashes, official
locators, page-count discrepancy, fail-closed rights, and NARROW_ONLY/REJECT
dispositions. It does not authorize database ingest, training export, semantic
gold, topic-gap closure/narrowing, source-universe freeze, Phase 3 completion,
or Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
SCHEMA_PATH = DATA / "contracts/phase3_donnu_2023_morphemics_word_formation_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_donnu_2023_morphemics_word_formation_candidate_v1.json"
UNIVERSITY_FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
SOURCE_POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"

SCHEMA_VERSION = "phase3_donnu_2023_morphemics_word_formation_candidate_v1"
STATUS = "NARROW_ONLY_CANDIDATE_PENDING_UKRAINIAN_CANON_REVIEW_AND_SCOPE_CRITIC"
SOURCE_ID = "uni-ukrmova-morphemics-word-formation-donnu-2023"
SOURCE_TITLE = "Сучасна українська мова: Морфеміка. Словотвір: матеріали для дистанційної роботи студентів"
SOURCE_TITLE_METADATA = (
    "СУЧАСНА УКРАЇНСЬКА МОВА: МОРФЕМІКА. СЛОВОТВІР: МАТЕРІАЛИ ДЛЯ ДИСТАНЦІЙНОЇ РОБОТИ СТУДЕНТІВ. НАВЧАЛЬНИЙ ПОСІБНИК"
)
SOURCE_AUTHORS = ["Каріна Бортун", "Олена Важеніна"]
SOURCE_METADATA_AUTHORS = ["Бортун, Каріна", "Важеніна, Олена"]
SOURCE_INSTITUTION = "DonNU DSpace r2.donnu.edu.ua (repository custody)"
SOURCE_PUBLISHER = "Київ: Приватний вищий навчальний заклад «Європейський університет»"
SOURCE_ISBN = "978-966-301-261-2"
SOURCE_ITEM_UUID = "74e2161c-c67f-4b5f-817c-4cc4707b9470"
SOURCE_BITSTREAM_UUID = "eee9a7c4-006f-45b8-8c9c-42f086942e25"
SOURCE_LICENSE_BITSTREAM_UUID = "c48b8471-536d-408d-bc41-5969a449530d"
SOURCE_ITEM_URL = f"https://r2.donnu.edu.ua/items/{SOURCE_ITEM_UUID}"
SOURCE_BITSTREAM_URL = f"https://r2.donnu.edu.ua/server/api/core/bitstreams/{SOURCE_BITSTREAM_UUID}/content"
SOURCE_ITEM_API_URL = f"https://r2.donnu.edu.ua/server/api/core/items/{SOURCE_ITEM_UUID}"
SOURCE_LICENSE_BITSTREAM_URL = (
    f"https://r2.donnu.edu.ua/server/api/core/bitstreams/{SOURCE_LICENSE_BITSTREAM_UUID}/content"
)
PRIVATE_INPUT_LOCATOR = "university_corpus/staging/phase3-6375-donnu-2023-morphemics-word-formation"
PDF_FILENAME = f"{SOURCE_ID}.pdf"
LANDING_FILENAME = f"donnu-dspace-{SOURCE_ITEM_UUID}-landing.html"
ITEM_METADATA_FILENAME = f"donnu-dspace-{SOURCE_ITEM_UUID}-item.json"
BITSTREAM_METADATA_FILENAME = f"donnu-dspace-{SOURCE_BITSTREAM_UUID}-bitstream.json"
LICENSE_TEXT_FILENAME = "license/LICENSE_BITSTREAM.txt"
LICENSE_BITSTREAM_METADATA_FILENAME = f"license/donnu-dspace-{SOURCE_LICENSE_BITSTREAM_UUID}-bitstream.json"
JSONL_FILENAME = f"{SOURCE_ID}.jsonl"
EXACTNESS_AUDIT_FILENAME = "textbook-native-exactness-audit-v1.json"
CONTENT_FIT_AUDIT_FILENAME = "phase3_donnu_2023_content_fit_audit_v1.json"
CUSTODY_RECEIPT_FILENAME = "phase3_donnu_2023_morphemics_word_formation_custody_receipt_v1.json"
EXTRACTION_FACTS_FILENAME = "phase3_donnu_2023_extraction_facts_v1.json"
CHECKSUMS_FILENAME = "SHA256SUMS"

PDF_SHA256 = "f0bc5940e1aff1ae9cca8717306ba85f54eab878883cfa8dc9a82d1034cfccc5"
PDF_MD5 = "69e85724612a1575892154e11486f558"
PDF_BYTES = 3_561_818
PDF_PAGE_OBJECTS = 215
CATALOG_CITATION_PAGES = 214
TEXT_BEARING_PAGES = 214
EMPTY_TEXT_PAGES = [1]
UNICODE_CODE_POINTS = 218_710
UTF8_BYTES = 386_290
PAGE_MANIFEST_SHA256 = "fbd671f02534359717bf13c2c0a0df2e4ab1b6df0d397f1ce38952f370495410"
EXTRACTED_TEXT_SHA256 = "1bdf9fdc17bc4e614fa4dddac1fff6fb1652d2af182e63af25ed48b4af5986a2"
LANDING_SHA256 = "ff19ad7ce3b672745761448644f90988e2ade7d2122cd8c7def932f929272ce8"
LANDING_BYTES = 368_058
ITEM_METADATA_SHA256 = "78a838ad8042a4ee15168705ff5db845d3c72b7aac620e79a91c262f13d84101"
ITEM_METADATA_BYTES = 6_099
BITSTREAM_METADATA_SHA256 = "5fc7177018ea008b0f238c07f717b46e2a6097fbd543f69101387342d246f154"
BITSTREAM_METADATA_BYTES = 2_048
LICENSE_TEXT_SHA256 = "ab044a4cadbd499552a26ad0ab8a241fd38197db21e666f11ad3bb4d4cafcd28"
LICENSE_TEXT_BYTES = 1_748
LICENSE_BITSTREAM_METADATA_SHA256 = "8c39b96832a6eefd0b631571fa1329c6575aafcb111602061e4c5710a5e56eff"
PRIVATE_JSONL_SHA256 = "e7595a03f81c94491fb96a74d9bcdc2bf303f7021b6c42329928009bf766f641"
PRIVATE_JSONL_BYTES = 566_118
EXACTNESS_AUDIT_SHA256 = "9b01a15062c54ab035024d75a2205c14dfd8f0f8cd5ff6cc352021140ff21a42"
CONTENT_FIT_AUDIT_SHA256 = "b39b63eac42ef89552c2c42da9ec4c5b75be0d8a7e04a09affb28b0f931d373a"
CUSTODY_RECEIPT_FILE_SHA256 = "e089cecc947b822ef74f5f5fcc8efeb0c4f052e5fb3186cbb4d827b63db3da55"
CUSTODY_RECEIPT_BODY_SHA256 = "194dcc099d6b27e0e57dbf2cd0dd877e4fbaa3cd55ffab60c075821108a4ec1f"
CHECKSUMS_SHA256 = "31e0ac9b8a861e1b385986cf4349c760ffe7ef4466bee1de3b07f01dc4ffe469"
CHECKSUMS_ENTRY_COUNT = 13
PAGE_TEXT_INDEX_SHA256 = "779d9cf025bf21e22fb6940b54b118da7e29cf46f49271c26ad33dbe883fcf57"
VISUAL_QA_RECEIPT_SHA256 = "523bacce5373ef1d0c7f58709b687ad0af0fb28b1442450b5b2c65fb542a19c4"
EXTRACTION_FACTS_SHA256 = "a0540b56328e17970094ce46ab6f1fd788e8a283020f929e683706866430a090"

AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256 = {
    "bitstream_metadata": "bddf658e837552c480228e2d0bdda0899239702244596f08c88569269a061a5e",
    "content_fit_audit": "26126eabff7126f6320ac45c845059fee00d08856a76b3cfe712700bba983de6",
    "exactness_audit": "5f48649af924d04dc0b6b542405756f5e5fe28e473eb636ebe5102f37259d55d",
    "item_metadata": "cd12372028e49b29d1b3f1ceb105fbdbfb16301f3c75e8d9a5bcab45a914900f",
    "landing_html": "4bd07da47078b46676da074eb86ed8a4482e247f94231e0791e6fde412a808ee",
    "license_text": "5dd8d9d6ce6372c8d25d9a8467fee16be2b252923614b0f6dddb8366b1896e60",
    "private_jsonl": "56972510cc19b5a91877d814e9af3821c3f52a9c40a0cf39a81a8bb71513abd4",
    "source_pdf": "2b0b3da00c592424d944e49ebbad6c9deaafc732f31276e66bfd76ddfbc7e31b",
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
PROVISIONAL_NARROW_CELLS = ["morphemics", "word_formation"]
REJECTED_SECONDARY_CELLS = ["semantics", "phraseology"]
RIGHTS_STATEMENT = (
    "public DonNU DSpace distribution; author/publisher copyright; "
    "DSpace non-exclusive distribution/preservation grant only; reuse license not established"
)

PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700
TRACKED_PUBLIC_FILE_MODE = 0o644
ACCEPTED_PUBLIC_RECEIPT_MODES = frozenset({PRIVATE_FILE_MODE, TRACKED_PUBLIC_FILE_MODE})
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"
DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0

CONTENT_FITNESS: dict[str, Any] = json.loads(
    """{"adversarial_dispositions": {"morphemics": "NARROW_ONLY", "phraseology": "REJECT", "semantics": "REJECT", "word_formation": "NARROW_ONLY"}, "audience": {"board_recommendation_marker_verified": true, "current_ukrainian_philology_students": true, "philology_bachelor_marker_verified": true, "programme_marker_verified": true, "publication_period_post_2019": true, "publication_year": 2023, "publisher_institution": "ПВНЗ «Європейський університет» (Kyiv); custody via DonNU DSpace r2.donnu.edu.ua", "repository_type": "Book"}, "cells": {"morphemics": {"depth_evidence": {"bibliography_marker_hits": 19, "bibliography_pages": 8, "definition_marker_hits": 12, "definition_pages": 10, "example_marker_hits": 3, "example_pages": 3, "exceptions_competing_marker_hits": 0, "exceptions_competing_pages": 0, "exercise_marker_hits": 37, "exercise_pages": 13, "paradigms_models_marker_hits": 52, "paradigms_models_pages": 34, "scope": "topic_conditioned", "self_control_answer_marker_hits": 0, "self_control_answer_pages": 0, "theory_classification_marker_hits": 24, "theory_classification_pages": 7, "topic_marker_hits": 863, "topic_pages": 132}, "disposition": "NARROW_ONLY", "frozen_status": "partial", "provisional_effect": "diagnostic_narrow_only_candidate_not_a_gap_transition", "qualified_source_needed": "Dedicated post-2019 university textbook on morphemics and morphemic structure of Ukrainian words.", "rationale_codes": ["dedicated_post_2019_university_posibnyk_title_and_toc", "high_topic_marker_density_and_page_coverage", "glossary_and_morphemic_analysis_schemes_present", "exercise_and_test_coverage_strong", "missing_answer_key_self_control_evidence", "exceptions_competing_analyses_not_evidenced", "theory_depth_secondary_to_test_workbook_format", "ukrainian_canon_review_required_before_any_gap_transition"], "role": "primary"}, "word_formation": {"depth_evidence": {"bibliography_marker_hits": 22, "bibliography_pages": 11, "definition_marker_hits": 13, "definition_pages": 12, "example_marker_hits": 0, "example_pages": 0, "exceptions_competing_marker_hits": 0, "exceptions_competing_pages": 0, "exercise_marker_hits": 42, "exercise_pages": 16, "paradigms_models_marker_hits": 81, "paradigms_models_pages": 49, "scope": "topic_conditioned", "self_control_answer_marker_hits": 0, "self_control_answer_pages": 0, "theory_classification_marker_hits": 13, "theory_classification_pages": 6, "topic_marker_hits": 859, "topic_pages": 147}, "disposition": "NARROW_ONLY", "frozen_status": "partial", "provisional_effect": "diagnostic_narrow_only_candidate_not_a_gap_transition", "qualified_source_needed": "Specialized university coursebook on Ukrainian word formation (дериватологія).", "rationale_codes": ["dedicated_post_2019_university_posibnyk_title_and_toc", "high_topic_marker_density_and_page_coverage", "word_formation_analysis_schemes_and_glossary_present", "exercise_and_test_coverage_strong", "missing_answer_key_self_control_evidence", "exceptions_competing_analyses_not_evidenced", "theory_depth_secondary_to_test_workbook_format", "ukrainian_canon_review_required_before_any_gap_transition"], "role": "primary"}}, "document_profile": {"genre": "distance_learning_test_and_task_posibnyk", "printed_page_offset_note": "PDF object N roughly maps to printed page N-1 for body pages; PDF has 215 objects vs catalog 214 pp", "toc_observed": ["vstup", "testovi_zavdannia_za_temamy", "indyvidualno_naukovo_doslidne_zavdannia", "prezentatsii_vymohy", "samostiina_robota", "indyvidualni_zavdannia", "morfemnyi_analiz_samples", "slovotvirnyi_analiz_samples", "hlosarii", "spysok_literatury", "slovnyky"]}, "document_wide_depth_evidence": {"bibliography_marker_hits": 26, "bibliography_pages": 14, "definition_marker_hits": 16, "definition_pages": 14, "example_marker_hits": 6, "example_pages": 5, "exceptions_competing_marker_hits": 0, "exceptions_competing_pages": 0, "exercise_marker_hits": 45, "exercise_pages": 19, "paradigms_models_marker_hits": 91, "paradigms_models_pages": 58, "scope": "document_wide", "self_control_answer_marker_hits": 0, "self_control_answer_pages": 0, "theory_classification_marker_hits": 30, "theory_classification_pages": 9}, "explicit_limitations": ["Marker counts are provisional diagnostic evidence only.", "Topic-conditioned depth must not be read as document-wide depth.", "No university topic gap is closed or narrowed in repository state by this custody packet.", "Workbook/test format dominates; theory/definitions exist mainly in intro, analysis schemes, and glossary rather than full lecture exposition.", "No answer-key / self-control solution evidence observed.", "Exceptions and competing analyses not evidenced by markers.", "Catalog cites 214 pages; PDF has 215 page objects (page 1 image-only cover; page 214 notes; page 215 colophon) — discrepancy recorded, not repaired.", "DSpace license bitstream is non-exclusive distribution/preservation grant only; reuse_license_not_established.", "Independent Ukrainian-canon and cross-family review required before any admission disposition.", "Semantics/phraseology observations are diagnostic secondary only."], "flags_for_ukrainian_review": {"adjudication": "pending_independent_ukrainian_canon_review", "davnoruska_marker_hits": 0, "etymology_marker_hits": 48, "historical_origin_excluded_from_normative_authority": true, "historical_origin_excluded_from_semantic_gold": true, "historical_origin_marker_hits": 16, "historical_origin_pages_in_intro_window": 3, "russian_comparison_hits": 2, "shared_east_slavic_calque_hits": 0, "soviet_era_marker_hits": 2, "yazyk_token_hits": 2}, "historical_origin_exclusion": {"etymology_marker_hits": 48, "excluded_from_normative_authority": true, "excluded_from_semantic_gold": true, "historical_origin_marker_hits": 16, "historical_origin_pages_in_window": 3, "intro_page_window": "1-20", "note": "Etymology/historical-structure mentions remain diagnostic only; excluded from semantic gold and normative authority."}, "provisional_effect": "narrow_only_candidate", "secondary_observation_cells": {"phraseology": {"depth_evidence": {"bibliography_marker_hits": 0, "bibliography_pages": 0, "definition_marker_hits": 0, "definition_pages": 0, "example_marker_hits": 0, "example_pages": 0, "exceptions_competing_marker_hits": 0, "exceptions_competing_pages": 0, "exercise_marker_hits": 0, "exercise_pages": 0, "paradigms_models_marker_hits": 0, "paradigms_models_pages": 0, "scope": "topic_conditioned", "self_control_answer_marker_hits": 0, "self_control_answer_pages": 0, "theory_classification_marker_hits": 0, "theory_classification_pages": 0, "topic_marker_hits": 0, "topic_pages": 0}, "disposition": "REJECT", "provisional_effect": "diagnostic_marker_evidence_only", "rationale_codes": ["zero_phraseology_marker_hits", "not_in_scope_for_this_candidate", "diagnostic_secondary_observation_only"], "role": "secondary_observation"}, "semantics": {"depth_evidence": {"bibliography_marker_hits": 10, "bibliography_pages": 3, "definition_marker_hits": 3, "definition_pages": 3, "example_marker_hits": 0, "example_pages": 0, "exceptions_competing_marker_hits": 0, "exceptions_competing_pages": 0, "exercise_marker_hits": 1, "exercise_pages": 1, "paradigms_models_marker_hits": 29, "paradigms_models_pages": 18, "scope": "topic_conditioned", "self_control_answer_marker_hits": 0, "self_control_answer_pages": 0, "theory_classification_marker_hits": 1, "theory_classification_pages": 1, "topic_marker_hits": 79, "topic_pages": 48}, "disposition": "REJECT", "provisional_effect": "diagnostic_marker_evidence_only", "rationale_codes": ["not_a_primary_target_cell_for_this_candidate", "marker_evidence_only_incidental_to_morphemics_word_formation", "diagnostic_secondary_observation_only"], "role": "secondary_observation"}}, "supporting_depth_outside_target_cells": {"lexicography_marker_hits": 103, "lexicography_pages": 38, "lexicology_marker_hits": 6, "lexicology_pages": 5, "note": "lexicography hits largely reflect dictionary/task references; not a lexicography candidate"}, "target_cells": ["morphemics", "word_formation"], "topic_gaps_closed": [], "topic_gaps_narrowed_claimed": []}"""
)

CUSTODY_ARTIFACTS = {
    "bitstream_metadata": BITSTREAM_METADATA_FILENAME,
    "checksums": CHECKSUMS_FILENAME,
    "content_fit_audit": CONTENT_FIT_AUDIT_FILENAME,
    "custody_receipt": CUSTODY_RECEIPT_FILENAME,
    "exactness_audit": f"exactness/{EXACTNESS_AUDIT_FILENAME}",
    "extraction_facts": EXTRACTION_FACTS_FILENAME,
    "item_metadata": ITEM_METADATA_FILENAME,
    "landing_html": LANDING_FILENAME,
    "license_bitstream_metadata": LICENSE_BITSTREAM_METADATA_FILENAME,
    "license_text": LICENSE_TEXT_FILENAME,
    "page_text_index": "page-text/page_text_index_v1.json",
    "private_jsonl": f"processed/grade-00/{JSONL_FILENAME}",
    "source_pdf": PDF_FILENAME,
    "visual_qa_dir": "visual-qa/",
    "visual_qa_receipt": "visual-qa/visual_qa_receipt_v1.json",
}


class Donnu2023MorphemicsWordFormationIntakeError(ValueError):
    """Exact identity, custody, rights, or fail-closed disposition drifted."""


class DriveIdentityPendingError(Donnu2023MorphemicsWordFormationIntakeError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Donnu2023MorphemicsWordFormationIntakeError(message)


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
        raise Donnu2023MorphemicsWordFormationIntakeError(f"cannot read artifact: {path}") from exc
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
        raise Donnu2023MorphemicsWordFormationIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _regular_public(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise Donnu2023MorphemicsWordFormationIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    mode = stat.S_IMODE(result.st_mode)
    require(mode in ACCEPTED_PUBLIC_RECEIPT_MODES, f"{label} permissions must be 0600 or tracked 0644")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Donnu2023MorphemicsWordFormationIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_private_bytes(path: Path, label: str, expected_sha256: str) -> bytes:
    _private_regular_file(path, label)
    try:
        before = Path(path).stat()
        payload = Path(path).read_bytes()
        after = Path(path).stat()
    except OSError as exc:
        raise Donnu2023MorphemicsWordFormationIntakeError(f"cannot read {label}") from exc
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        f"{label} changed while reading",
    )
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, f"{label} byte drift")
    return payload


def default_drive_project_root() -> Path:
    try:
        drive_roots = [
            candidate
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise Donnu2023MorphemicsWordFormationIntakeError("cannot inspect configured Google Drive mounts") from exc
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
        raise Donnu2023MorphemicsWordFormationIntakeError("cannot inspect configured Google Drive mounts") from exc
    matches = [root for root in drive_roots if resolved.is_relative_to(root)]
    require(len(matches) == 1, "artifact is not inside exactly one configured Google Drive mount")
    try:
        probe = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
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
            raise Donnu2023MorphemicsWordFormationIntakeError(
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
            "metadata_title": SOURCE_TITLE_METADATA,
            "authors": list(SOURCE_AUTHORS),
            "metadata_authors": list(SOURCE_METADATA_AUTHORS),
            "institution": SOURCE_INSTITUTION,
            "publisher": SOURCE_PUBLISHER,
            "audience": "native_ukrainian_philology_students_distance_learning",
            "year": 2023,
            "isbn": SOURCE_ISBN,
            "pages": PDF_PAGE_OBJECTS,
            "catalog_citation_pages": CATALOG_CITATION_PAGES,
            "page_count_discrepancy_recorded": True,
            "item_url": SOURCE_ITEM_URL,
            "item_api_url": SOURCE_ITEM_API_URL,
            "bitstream_url": SOURCE_BITSTREAM_URL,
            "license_bitstream_url": SOURCE_LICENSE_BITSTREAM_URL,
            "private_input_locator": PRIVATE_INPUT_LOCATOR,
            "bitstream_is_complete_publication": True,
            "repository_custody": "DonNU DSpace r2.donnu.edu.ua",
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "landing_html_sha256": LANDING_SHA256,
            "landing_html_bytes": LANDING_BYTES,
            "item_metadata_sha256": ITEM_METADATA_SHA256,
            "item_metadata_bytes": ITEM_METADATA_BYTES,
            "bitstream_metadata_sha256": BITSTREAM_METADATA_SHA256,
            "bitstream_metadata_bytes": BITSTREAM_METADATA_BYTES,
            "license_text_sha256": LICENSE_TEXT_SHA256,
            "license_text_bytes": LICENSE_TEXT_BYTES,
            "license_bitstream_metadata_sha256": LICENSE_BITSTREAM_METADATA_SHA256,
            "private_jsonl_sha256": PRIVATE_JSONL_SHA256,
            "private_jsonl_bytes": PRIVATE_JSONL_BYTES,
            "exactness_audit_sha256": EXACTNESS_AUDIT_SHA256,
            "content_fit_audit_sha256": CONTENT_FIT_AUDIT_SHA256,
            "custody_receipt_file_sha256": CUSTODY_RECEIPT_FILE_SHA256,
            "custody_receipt_body_sha256": CUSTODY_RECEIPT_BODY_SHA256,
            "checksums_sha256": CHECKSUMS_SHA256,
            "page_text_index_sha256": PAGE_TEXT_INDEX_SHA256,
            "visual_qa_receipt_sha256": VISUAL_QA_RECEIPT_SHA256,
            "extraction_facts_sha256": EXTRACTION_FACTS_SHA256,
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
            "isbn_text_verified": True,
            "page_count_discrepancy": {
                "catalog_citation_pages": CATALOG_CITATION_PAGES,
                "pdf_page_objects": PDF_PAGE_OBJECTS,
                "delta": PDF_PAGE_OBJECTS - CATALOG_CITATION_PAGES,
                "recorded_without_correction": True,
            },
            "normalization_applied": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
        },
        "native_exactness": {
            "schema_version": "textbook-native-exactness-audit.v1",
            "source_count": 1,
            "chunk_count": PDF_PAGE_OBJECTS,
            "flagged_chunk_count": 0,
            "flagged_page_count": 0,
            "verified_flagged_chunk_count": 0,
            "unverified_flagged_chunk_count": 0,
            "clean_chunk_count": PDF_PAGE_OBJECTS,
            "empty_text_page_count": 1,
            "empty_text_pages": list(EMPTY_TEXT_PAGES),
            "production_eligible_under_exactness_gate": False,
            "production_eligible_note": (
                "exactness detector flagged 0 chunks; page 1 is image-only cover with no native text"
            ),
            "audit_receipt_sha256": EXACTNESS_AUDIT_SHA256,
        },
        "content_fitness": content_fitness,
        "custody": build_custody_block(),
        "rights": {
            "visibility": "publicly_accessible_institutional_repository",
            "reuse_license": "reuse_license_not_established",
            "rights_statement": RIGHTS_STATEMENT,
            "standardized_open_reuse_license_present": False,
            "landing_standardized_license_present": False,
            "landing_ui_i18n_creative_commons_label_present": False,
            "landing_creativecommons_org_uri_present": False,
            "creative_commons_uri_present": False,
            "item_metadata_rights_fields_present": False,
            "author_copyright_notice_present": True,
            "dspace_license_bitstream_present": True,
            "dspace_license_type": "non_exclusive_distribution_preservation_grant",
            "public_repository_distribution_evidence": True,
            "acquisition_and_private_analysis_may_proceed": True,
            "legal_reuse_authorization_established": False,
            "attribution_required": True,
            "takedown_ready": True,
            "adapt_or_remove_on_substantiated_complaint": True,
            "public_redistribution_authorized": False,
            "public_dataset_export_authorized": False,
            "publish_source_text_authorized": False,
            "unrestricted_reuse_authorized": False,
            "unrestricted_training_export_authorized": False,
            "private_corpus_text_and_pdf_required": True,
        },
        "review_scope": {
            "content_disposition": "narrow_only_candidate",
            "ukrainian_canon_review_complete": False,
            "scope_critic_complete": False,
            "topic_gaps_closed": [],
            "topic_gaps_narrowed": [],
            "provisional_narrow_cells": list(PROVISIONAL_NARROW_CELLS),
            "rejected_secondary_cells": list(REJECTED_SECONDARY_CELLS),
            "adversarial_dispositions": {
                "morphemics": "NARROW_ONLY",
                "word_formation": "NARROW_ONLY",
                "semantics": "REJECT",
                "phraseology": "REJECT",
            },
            "coverage_effect": "narrow_only_pending_ukrainian_canon_review_no_gap_transition",
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
            "topic_gaps_closed": False,
            "topic_gaps_narrowed": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "Exact official bytes are privately custodied; Git retains metadata only.",
            "Native exactness is clean across 215/215 chunks with zero flagged pages; page 1 is image-only cover.",
            "Cursor content-fit evidence supports NARROW_ONLY for morphemics and word formation but closes/narrows none.",
            "Semantics is REJECT (incidental only); phraseology is REJECT (out of scope).",
            "Catalog citation claims 214 pages; PDF has 215 page objects — discrepancy recorded, not corrected.",
            "Distance-learning test/task posibnyk: thin full-theory exposition, no answer keys, no evidenced exceptions.",
            "DSpace license is a generic non-exclusive distribution/preservation grant; reuse license not established.",
            "Public redistribution, public dataset export, publish-source-text, and unrestricted training export remain false.",
            "Independent Ukrainian-canon review and cross-family root disposition remain outstanding.",
            "v2 denominators preserved: 67,041 / 9,392; Cycle002 diagnostic only; Phase 3 incomplete; Phase 4 blocked.",
        ],
    }


def mint_receipt() -> dict[str, Any]:
    body = build_receipt_body()
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "DonNU candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise Donnu2023MorphemicsWordFormationIntakeError(
            f"receipt schema violation at {location}: {errors[0].message}"
        )
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    authoritative = validate_authoritative_university_state()
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
    require(receipt["bindings"]["private_jsonl_sha256"] == PRIVATE_JSONL_SHA256, "private JSONL hash drift")
    require(receipt["bindings"]["private_jsonl_bytes"] == PRIVATE_JSONL_BYTES, "private JSONL byte denominator drift")
    require(receipt["bindings"]["exactness_audit_sha256"] == EXACTNESS_AUDIT_SHA256, "exactness audit hash drift")
    require(
        receipt["native_exactness"]["audit_receipt_sha256"] == EXACTNESS_AUDIT_SHA256,
        "native exactness audit receipt hash drift",
    )
    require(
        receipt["native_exactness"]["audit_receipt_sha256"] == receipt["bindings"]["exactness_audit_sha256"],
        "native exactness audit receipt binding twin drift",
    )
    require(receipt["bindings"]["content_fit_audit_sha256"] == CONTENT_FIT_AUDIT_SHA256, "content-fit audit hash drift")
    require(
        receipt["bindings"]["custody_receipt_file_sha256"] == CUSTODY_RECEIPT_FILE_SHA256,
        "custody receipt file hash drift",
    )
    require(
        receipt["bindings"]["custody_receipt_body_sha256"] == CUSTODY_RECEIPT_BODY_SHA256,
        "custody receipt body hash drift",
    )
    require(receipt["bindings"]["checksums_sha256"] == CHECKSUMS_SHA256, "SHA256SUMS hash drift")
    require(receipt["bindings"]["landing_html_sha256"] == LANDING_SHA256, "landing hash drift")
    require(receipt["bindings"]["item_metadata_sha256"] == ITEM_METADATA_SHA256, "item metadata hash drift")
    require(
        receipt["bindings"]["bitstream_metadata_sha256"] == BITSTREAM_METADATA_SHA256,
        "bitstream metadata hash drift",
    )
    require(receipt["bindings"]["license_text_sha256"] == LICENSE_TEXT_SHA256, "license text hash drift")
    require(
        receipt["custody"]["google_drive_provider_identity_sha256"]
        == AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256,
        "google drive provider identity mapping drift",
    )
    require(receipt["source"]["source_id"] == SOURCE_ID, "source identity drift")
    require(receipt["source"]["item_url"] == SOURCE_ITEM_URL, "source item locator drift")
    require(receipt["source"]["bitstream_url"] == SOURCE_BITSTREAM_URL, "source bitstream locator drift")
    require(receipt["source"]["isbn"] == SOURCE_ISBN, "source ISBN drift")
    require(receipt["source"]["title"] == SOURCE_TITLE, "source title drift")
    require(receipt["source"]["authors"] == SOURCE_AUTHORS, "source authors drift")
    require(
        receipt["text_layer"]["page_count_discrepancy"]["recorded_without_correction"] is True,
        "page-count discrepancy must remain recorded without correction",
    )
    require(
        receipt["text_layer"]["page_count_discrepancy"]["pdf_page_objects"] == PDF_PAGE_OBJECTS,
        "page-count discrepancy pdf objects drift",
    )
    require(
        receipt["text_layer"]["page_count_discrepancy"]["catalog_citation_pages"] == CATALOG_CITATION_PAGES,
        "page-count discrepancy catalog pages drift",
    )
    require(receipt["text_layer"]["empty_text_pages"] == EMPTY_TEXT_PAGES, "empty-text pages drift")
    require(receipt["text_layer"]["ocr_used"] is False, "receipt overclaims OCR")
    require(receipt["text_layer"]["repairs_applied"] is False, "receipt overclaims repairs")
    require(receipt["review_scope"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["review_scope"]["topic_gaps_narrowed"] == [], "receipt overclaims topic narrowing")
    require(receipt["content_fitness"]["topic_gaps_closed"] == [], "content-fitness overclaims closure")
    require(receipt["content_fitness"]["topic_gaps_narrowed_claimed"] == [], "content-fitness overclaims narrowing")
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["morphemics"] == "NARROW_ONLY",
        "morphemics disposition drift",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["word_formation"] == "NARROW_ONLY",
        "word_formation disposition drift",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["semantics"] == "REJECT",
        "semantics disposition drift",
    )
    require(
        receipt["content_fitness"]["adversarial_dispositions"]["phraseology"] == "REJECT",
        "phraseology disposition drift",
    )
    require(
        receipt["content_fitness"]["cells"]["morphemics"]["disposition"] == "NARROW_ONLY",
        "morphemics cell disposition drift",
    )
    require(
        receipt["content_fitness"]["cells"]["word_formation"]["disposition"] == "NARROW_ONLY",
        "word_formation cell disposition drift",
    )
    require(
        receipt["content_fitness"]["secondary_observation_cells"]["semantics"]["disposition"] == "REJECT",
        "semantics secondary disposition drift",
    )
    require(
        receipt["content_fitness"]["secondary_observation_cells"]["phraseology"]["disposition"] == "REJECT",
        "phraseology secondary disposition drift",
    )
    require(receipt["gates"]["semantic_gold"] is False, "receipt overclaims semantic gold")
    require(receipt["gates"]["database_ingest_authorized"] is False, "receipt overclaims database ingest")
    require(receipt["gates"]["topic_gaps_closed"] is False, "receipt overclaims topic gap closure")
    require(receipt["gates"]["topic_gaps_narrowed"] is False, "receipt overclaims topic gap narrowing")
    require(receipt["gates"]["source_freeze_ready"] is False, "receipt overclaims source freeze readiness")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["denominators"]["v2_source_units"] == V2_SOURCE_UNITS, "v2 source-unit denominator drift")
    require(
        receipt["denominators"]["v2_evaluation_identities"] == V2_EVALUATION_IDENTITIES,
        "v2 evaluation denominator drift",
    )
    require(receipt["denominators"]["cycle002_diagnostic_only"] is True, "Cycle002 diagnostic-only drift")
    require(
        receipt["denominators"]["candidate_additive_outside_v2_totals"] is True,
        "candidate must remain additive outside v2 totals",
    )
    require(receipt["rights"]["rights_statement"] == RIGHTS_STATEMENT, "rights statement drift")
    require(receipt["rights"]["reuse_license"] == "reuse_license_not_established", "reuse license drift")
    require(receipt["rights"]["public_redistribution_authorized"] is False, "receipt overclaims redistribution")
    require(receipt["rights"]["public_dataset_export_authorized"] is False, "receipt overclaims dataset export")
    require(receipt["rights"]["publish_source_text_authorized"] is False, "receipt overclaims publish-source-text")
    require(
        receipt["rights"]["unrestricted_training_export_authorized"] is False,
        "receipt overclaims training export",
    )
    require(
        receipt["rights"]["standardized_open_reuse_license_present"] is False,
        "receipt overclaims open reuse license",
    )
    require(
        receipt["rights"]["dspace_license_type"] == "non_exclusive_distribution_preservation_grant",
        "DSpace license type drift",
    )
    serialized = canonical_json(receipt)
    require("GoogleDrive-" not in serialized, "receipt leaks private Drive identity")
    require("@gmail.com" not in serialized, "receipt leaks private account identity")
    require("\f" not in serialized, "receipt retains extracted page-join markers")
    require("page_texts" not in receipt, "receipt retains private page texts")
    require('"text"' not in serialized or '"text_free"' in serialized, "unexpected text field leakage")
    # Stronger: no private PDF body / license sample leakage markers beyond bibliographic metadata.
    require("NOTE: PLACE YOUR OWN LICENSE HERE" not in serialized, "receipt leaks private license bitstream text")
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise Donnu2023MorphemicsWordFormationIntakeError("cannot safely read existing public receipt") from exc
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
        raise Donnu2023MorphemicsWordFormationIntakeError("cannot atomically publish public receipt") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def private_audit(staging_root: Path | None = None) -> dict[str, Any]:
    """Rehash the private Drive packet against authoritative constants. Mutates nothing."""
    staging = staging_root or default_staging_root()
    require(staging.is_dir(), f"missing staging root: {staging}")
    require(stat.S_IMODE(staging.stat().st_mode) == PRIVATE_DIR_MODE, "staging root must be mode 0700")
    require(not _inside_git_checkout(staging), "staging root cannot live inside Git")

    checks = {
        "source_pdf": (staging / PDF_FILENAME, PDF_SHA256, PDF_BYTES),
        "landing_html": (staging / LANDING_FILENAME, LANDING_SHA256, LANDING_BYTES),
        "item_metadata": (staging / ITEM_METADATA_FILENAME, ITEM_METADATA_SHA256, ITEM_METADATA_BYTES),
        "bitstream_metadata": (
            staging / BITSTREAM_METADATA_FILENAME,
            BITSTREAM_METADATA_SHA256,
            BITSTREAM_METADATA_BYTES,
        ),
        "license_text": (staging / LICENSE_TEXT_FILENAME, LICENSE_TEXT_SHA256, LICENSE_TEXT_BYTES),
        "private_jsonl": (
            staging / "processed" / "grade-00" / JSONL_FILENAME,
            PRIVATE_JSONL_SHA256,
            PRIVATE_JSONL_BYTES,
        ),
        "exactness_audit": (
            staging / "exactness" / EXACTNESS_AUDIT_FILENAME,
            EXACTNESS_AUDIT_SHA256,
            None,
        ),
        "content_fit_audit": (staging / CONTENT_FIT_AUDIT_FILENAME, CONTENT_FIT_AUDIT_SHA256, None),
        "custody_receipt": (staging / CUSTODY_RECEIPT_FILENAME, CUSTODY_RECEIPT_FILE_SHA256, None),
        "checksums": (staging / CHECKSUMS_FILENAME, CHECKSUMS_SHA256, None),
        "extraction_facts": (staging / EXTRACTION_FACTS_FILENAME, EXTRACTION_FACTS_SHA256, None),
    }
    provider_ids: dict[str, str] = {}
    for label, (path, expected_sha, expected_bytes) in checks.items():
        _private_regular_file(path, label)
        require(sha256_file(path) == expected_sha, f"{label} hash drift")
        if expected_bytes is not None:
            require(path.stat().st_size == expected_bytes, f"{label} byte denominator drift")
        if label in AUTHORITATIVE_GOOGLE_DRIVE_PROVIDER_IDENTITY_SHA256:
            provider_ids[label] = _verify_drive_readback(path, expected_sha)

    custody_payload = _read_private_bytes(
        staging / CUSTODY_RECEIPT_FILENAME, "custody receipt", CUSTODY_RECEIPT_FILE_SHA256
    )
    custody_doc = json.loads(custody_payload.decode("utf-8"))
    require(isinstance(custody_doc, dict), "custody receipt must be an object")
    require(receipt_sha256(custody_doc) == CUSTODY_RECEIPT_BODY_SHA256, "custody receipt body hash drift")
    require(custody_doc.get("receipt_sha256") == CUSTODY_RECEIPT_BODY_SHA256, "custody receipt self-hash drift")

    checksum_lines = (staging / CHECKSUMS_FILENAME).read_text(encoding="utf-8").strip().splitlines()
    require(len(checksum_lines) == CHECKSUMS_ENTRY_COUNT, "SHA256SUMS entry-count drift")

    # Fail-closed rights: license text must remain the generic DSpace grant, not CC.
    license_text = (staging / LICENSE_TEXT_FILENAME).read_text(encoding="utf-8")
    require("NON-EXCLUSIVE DISTRIBUTION LICENSE" in license_text, "DSpace license grant missing")
    require("creativecommons.org" not in license_text.lower(), "license unexpectedly declares Creative Commons URI")
    require(not re.search(r"\bCC\s*BY\b", license_text, flags=re.IGNORECASE), "license unexpectedly declares CC BY")

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
        "checksum_entries": CHECKSUMS_ENTRY_COUNT,
        "custody_receipt_body_sha256": CUSTODY_RECEIPT_BODY_SHA256,
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
            receipt = validate_receipt(_read_json(args.check, "DonNU candidate receipt"))
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
            raise Donnu2023MorphemicsWordFormationIntakeError("specify --check, --mint, or --private-audit")
    except Donnu2023MorphemicsWordFormationIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
