#!/usr/bin/env python3
"""Admit the private ZHDU 2026 lexicology/phraseology official bitstream.

Downloads are verified against the frozen official PDF identity, stored only in
private Google Drive staging, audited for native logical-text exactness, and
summarized as one text-free public candidate receipt.  This module does not
authorize database ingest, training export, semantic gold, topic-gap closure,
source-universe freeze, Phase 3 completion, or Phase 4.
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
from pypdf import PdfReader

from scripts.projects.open_model_data.textbook_native_exactness import audit_chunk_files
from scripts.rag.extract_text import detect_native_text_anomalies

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_zhdu_2026_lexicology_phraseology_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_zhdu_2026_lexicology_phraseology_candidate_v1.json"
UNIVERSITY_FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
SOURCE_POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"

SCHEMA_VERSION = "phase3_zhdu_2026_lexicology_phraseology_candidate_v1"
STATUS = "NARROW_ONLY_CANDIDATE_PENDING_UKRAINIAN_CANON_REVIEW_AND_SCOPE_CRITIC"
SOURCE_ID = "uni-ukrmova-lexicology-phraseology-zhdu-2026"
SOURCE_TITLE = (
    "Лексикологія, фразеологія, фонетика і фонологія сучасної української "
    "літературної мови: навчальний посібник. Ч. 1: Лексикологія, фразеологія, лексикографія"
)
SOURCE_AUTHORS = ["Наталія Дяченко", "Людмила Фальківська"]
SOURCE_METADATA_AUTHORS = ["Дяченко, Н. М.", "Фальківська, Л. П."]
SOURCE_INSTITUTION = (
    "Житомирський державний університет імені Івана Франка, кафедра української мови та методики її навчання"
)
SOURCE_PUBLISHER = "Житомирський державний університет імені Івана Франка"
SOURCE_ISBN = "978-966-485-336-8"
SOURCE_EPRINT_ID = "48784"
SOURCE_ITEM_URL = f"https://eprints.zu.edu.ua/{SOURCE_EPRINT_ID}/"
SOURCE_BITSTREAM_URL = f"https://eprints.zu.edu.ua/{SOURCE_EPRINT_ID}/1/1.pdf"
PRIVATE_INPUT_LOCATOR = "university_corpus/staging/phase3-6375-zhdu-2026-lexicology-phraseology"
PDF_FILENAME = f"{SOURCE_ID}.pdf"
LANDING_FILENAME = f"zu-eprints-{SOURCE_EPRINT_ID}-landing.html"
JSONL_FILENAME = f"{SOURCE_ID}.jsonl"
EXACTNESS_AUDIT_FILENAME = "textbook-native-exactness-audit-v1.json"
CUSTODY_RECEIPT_FILENAME = "phase3_zhdu_2026_lexicology_phraseology_custody_receipt_v1.json"
CHECKSUMS_FILENAME = "SHA256SUMS"
RECORD_SCHEMA_VERSION = "phase3_zhdu_2026_page_source_unit_v1"

PDF_SHA256 = "fdaf6a524f4cc6dc2cb19c721fae9cb15d96a23c20c0ec75d8049458ca665019"
PDF_MD5 = "f725b24a7e834b155d2d4fb9b2de84e3"
PDF_BYTES = 744_081
PDF_PAGES = 98
TEXT_BEARING_PAGES = 98
UNICODE_CODE_POINTS = 214_095
UTF8_BYTES = 382_099
PAGE_MANIFEST_SHA256 = "ad07207b4cfcc2f9c375931df148c4ea1d077defa3963ec8a6f998706a263911"
EXTRACTED_TEXT_SHA256 = "b0d08c67f049c46c6e556735070204104bd99a312973682dbb168209a7964deb"
LANDING_SHA256 = "fcf9ff188ddf2a3e1f48f0e44e24ebcc7295112ac4da6a5c81210fb448c041f5"
LANDING_BYTES = 28_667
V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
V2_SOURCE_UNITS = 67_041
V2_EVALUATION_IDENTITIES = 9_392
PHASE3_LABELS = 0
UNIVERSITY_TOPIC_AREAS = 26
UNIVERSITY_SUFFICIENT = 5
UNIVERSITY_PARTIAL = 21
UNIVERSITY_MISSING = 0
UNIVERSITY_FREEZE_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"
SOURCE_POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
SEMANTICS_QUALIFIED_SOURCE_NEEDED = "Advanced university textbook on lexical and structural semantics."
PHRASEOLOGY_QUALIFIED_SOURCE_NEEDED = (
    "Dedicated university phraseology manual (e.g. Uzhchenko Phraseology of Modern Ukrainian)."
)

CONTENT_FIT_MARKER_HITS = {
    "lexicology": 43,
    "phraseology": 181,
    "semantics": 331,
    "lexicography": 262,
    "definitions": 33,
    "theory_classification": 27,
    "examples": 49,
    "exercises": 115,
    "self_control_answers": 11,
    "audience_philology": 1,
    "board_recommendation": 2,
}
CONTENT_FIT_PAGE_COUNTS = {
    "semantics_topic_pages": 62,
    "phraseology_topic_pages": 41,
    "lexicology_topic_pages": 21,
    "lexicography_topic_pages": 53,
    "definition_pages": 22,
    "theory_classification_pages": 20,
    "example_pages": 25,
    "exercise_pages": 52,
    "self_control_answer_pages": 6,
}
CONTENT_FIT_DOCUMENT_WIDE_DEPTH = {
    "definition_marker_hits": 33,
    "definition_pages": 22,
    "theory_classification_marker_hits": 27,
    "theory_classification_pages": 20,
    "example_marker_hits": 49,
    "example_pages": 25,
    "exercise_marker_hits": 115,
    "exercise_pages": 52,
    "self_control_answer_marker_hits": 11,
    "self_control_answer_pages": 6,
}
CONTENT_FIT_TOPIC_CONDITIONED = {
    "semantics": {
        "topic_marker_hits": 331,
        "topic_pages": 62,
        "definition_marker_hits": 22,
        "definition_pages": 15,
        "theory_classification_marker_hits": 21,
        "theory_classification_pages": 15,
        "example_marker_hits": 37,
        "example_pages": 18,
        "exercise_marker_hits": 78,
        "exercise_pages": 32,
        "self_control_answer_marker_hits": 9,
        "self_control_answer_pages": 4,
    },
    "phraseology": {
        "topic_marker_hits": 181,
        "topic_pages": 41,
        "definition_marker_hits": 11,
        "definition_pages": 8,
        "theory_classification_marker_hits": 17,
        "theory_classification_pages": 11,
        "example_marker_hits": 12,
        "example_pages": 7,
        "exercise_marker_hits": 53,
        "exercise_pages": 21,
        "self_control_answer_marker_hits": 8,
        "self_control_answer_pages": 3,
    },
}
RIGHTS_MARKER_HITS = {
    "author_copyright_marker_hits": 1,
    "university_copyright_marker_hits": 1,
    "creative_commons_marker_hits": 0,
    "license_word_hits": 0,
}
UKRAINIAN_REVIEW_FLAGS = {
    "davnoruska_marker_hits": 8,
    "shared_east_slavic_calque_hits": 2,
    "russian_comparison_hits": 10,
    "soviet_era_marker_hits": 5,
    "etymology_marker_hits": 27,
    "yazyk_token_hits": 1,
    "adjudication": "pending_independent_ukrainian_canon_review",
}

CONTENT_FIT_MARKERS = {
    "lexicology": ("лексиколог",),
    "phraseology": ("фразеолог",),
    "semantics": ("семантик", "полісемі", "омонім", "синонім", "антонім", "значення слова"),
    "lexicography": ("лексикограф", "словник"),
    "definitions": ("визначення", "дефініц"),
    "theory_classification": ("класифікац", "типолог"),
    "examples": ("наприклад",),
    "exercises": ("завдання", "вправ", "практичн"),
    "self_control_answers": ("самоконтроль", "відповіді", "ключі до"),
    "audience_philology": (
        "українська мова та література",
        "студентів-філолог",
        "студентів філолог",
    ),
    "board_recommendation": ("рекомендовано", "вченою радою"),
}

PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700
TRACKED_PUBLIC_FILE_MODE = 0o644
ACCEPTED_PUBLIC_RECEIPT_MODES = frozenset({PRIVATE_FILE_MODE, TRACKED_PUBLIC_FILE_MODE})
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"
DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0
DEFAULT_XATTR_TIMEOUT_SECONDS: float = 30.0
RIGHTS_STATEMENT = "publicly accessible; reuse license not stated"
PROVISIONAL_NARROW_CELLS = ["semantics", "phraseology"]
PRIVATE_FILE_MODE_LABEL = "0600"
PRIVATE_DIR_MODE_LABEL = "0700"


class Zhdu2026LexicologyPhraseologyIntakeError(ValueError):
    """Exact identity, custody, exactness, or fail-closed disposition drifted."""


class DriveIdentityPendingError(Zhdu2026LexicologyPhraseologyIntakeError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Zhdu2026LexicologyPhraseologyIntakeError(message)


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
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"cannot read artifact: {path}") from exc
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
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _regular_public(path: Path, label: str) -> None:
    """Accept only explicit safe modes for an existing public receipt.

    New receipts are created owner-only (0600). A normal git checkout of the
    committed text-free receipt is 0644. Any other mode fails closed.
    """
    _reject_symlink_components(path, label)
    try:
        result = Path(path).lstat()
    except OSError as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    mode = stat.S_IMODE(result.st_mode)
    require(
        mode in ACCEPTED_PUBLIC_RECEIPT_MODES,
        f"{label} permissions must be 0600 or tracked 0644",
    )


def _prepare_private_directory(path: Path, label: str) -> None:
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")
    _reject_symlink_components(path, label)
    prior_umask = os.umask(0o077)
    try:
        path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    finally:
        os.umask(prior_umask)
    os.chmod(path, PRIVATE_DIR_MODE)
    result = path.lstat()
    require(stat.S_ISDIR(result.st_mode) and not path.is_symlink(), f"{label} must be a regular directory")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_DIR_MODE, f"{label} must be mode 0700")


def _atomic_write_private_bytes(path: Path, payload: bytes, label: str) -> None:
    _prepare_private_directory(path.parent, f"{label} parent")
    _reject_symlink_components(path, label)
    if path.exists():
        _private_regular_file(path, label)
        require(path.read_bytes() == payload, f"refusing to overwrite a changed {label}")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.chmod(temporary, PRIVATE_FILE_MODE)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    _private_regular_file(path, label)


def _atomic_write(path: Path, payload: bytes) -> None:
    """Atomically write *payload* with owner-only permissions (mode 0600).

    Mode is a fixed literal at every fchmod/chmod site (no caller-controlled
    argument) so static analysis can prove the permission policy without tracking
    a variable.
    """
    _reject_symlink_components(path, "output path")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _read_private_bytes(path: Path, label: str, expected_sha256: str) -> bytes:
    _private_regular_file(path, label)
    try:
        before = Path(path).stat()
        payload = Path(path).read_bytes()
        after = Path(path).stat()
    except OSError as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"cannot read {label}") from exc
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        f"{label} changed while reading",
    )
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, f"{label} byte drift")
    return payload


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"cannot read {label}") from exc
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
        raise Zhdu2026LexicologyPhraseologyIntakeError("cannot inspect configured Google Drive mounts") from exc
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
        raise Zhdu2026LexicologyPhraseologyIntakeError("cannot inspect configured Google Drive mounts") from exc
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
            raise Zhdu2026LexicologyPhraseologyIntakeError(
                f"artifact did not acquire Google Drive provider identity within {timeout_seconds:g} seconds"
            ) from last_error
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))


def _verify_drive_readback(path: Path, expected_sha256: str) -> str:
    readback = sha256_file(path)
    require(readback == expected_sha256, "Drive read-back hash mismatch")
    return _wait_for_drive_item_id(path)


def _meta_values(html: str, name: str) -> list[str]:
    pattern = re.compile(
        rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"',
        flags=re.IGNORECASE,
    )
    return [match.group(1) for match in pattern.finditer(html)]


def _count_marker_hits(text_lower: str, markers: Sequence[str]) -> int:
    return sum(text_lower.count(marker) for marker in markers)


def _page_count(pages: Sequence[str], markers: Sequence[str]) -> int:
    return sum(1 for page in pages if any(marker in page.lower() for marker in markers))


def _page_matches(page: str, markers: Sequence[str]) -> bool:
    text_lower = page.lower()
    return any(marker in text_lower for marker in markers)


def _depth_evidence_from_pages(pages: Sequence[str]) -> dict[str, int]:
    joined_lower = "\n".join(pages).lower()
    return {
        "definition_marker_hits": _count_marker_hits(joined_lower, CONTENT_FIT_MARKERS["definitions"]),
        "definition_pages": _page_count(pages, CONTENT_FIT_MARKERS["definitions"]),
        "theory_classification_marker_hits": _count_marker_hits(
            joined_lower, CONTENT_FIT_MARKERS["theory_classification"]
        ),
        "theory_classification_pages": _page_count(pages, CONTENT_FIT_MARKERS["theory_classification"]),
        "example_marker_hits": _count_marker_hits(joined_lower, CONTENT_FIT_MARKERS["examples"]),
        "example_pages": _page_count(pages, CONTENT_FIT_MARKERS["examples"]),
        "exercise_marker_hits": _count_marker_hits(joined_lower, CONTENT_FIT_MARKERS["exercises"]),
        "exercise_pages": _page_count(pages, CONTENT_FIT_MARKERS["exercises"]),
        "self_control_answer_marker_hits": _count_marker_hits(
            joined_lower, CONTENT_FIT_MARKERS["self_control_answers"]
        ),
        "self_control_answer_pages": _page_count(pages, CONTENT_FIT_MARKERS["self_control_answers"]),
    }


def _topic_conditioned_depth(pages: Sequence[str], cell: str) -> dict[str, int]:
    topic_markers = CONTENT_FIT_MARKERS[cell]
    topic_pages = [page for page in pages if _page_matches(page, topic_markers)]
    return {
        "topic_marker_hits": _count_marker_hits("\n".join(pages).lower(), topic_markers),
        "topic_pages": len(topic_pages),
        **_depth_evidence_from_pages(topic_pages),
    }


def _content_fit_from_pages(pages: Sequence[str]) -> dict[str, Any]:
    joined_lower = "\n".join(pages).lower()
    hits = {key: _count_marker_hits(joined_lower, markers) for key, markers in CONTENT_FIT_MARKERS.items()}
    page_counts = {
        "semantics_topic_pages": _page_count(pages, CONTENT_FIT_MARKERS["semantics"]),
        "phraseology_topic_pages": _page_count(pages, CONTENT_FIT_MARKERS["phraseology"]),
        "lexicology_topic_pages": _page_count(pages, CONTENT_FIT_MARKERS["lexicology"]),
        "lexicography_topic_pages": _page_count(pages, CONTENT_FIT_MARKERS["lexicography"]),
        "definition_pages": _page_count(pages, CONTENT_FIT_MARKERS["definitions"]),
        "theory_classification_pages": _page_count(pages, CONTENT_FIT_MARKERS["theory_classification"]),
        "example_pages": _page_count(pages, CONTENT_FIT_MARKERS["examples"]),
        "exercise_pages": _page_count(pages, CONTENT_FIT_MARKERS["exercises"]),
        "self_control_answer_pages": _page_count(pages, CONTENT_FIT_MARKERS["self_control_answers"]),
    }
    document_wide_depth = _depth_evidence_from_pages(pages)
    topic_conditioned = {cell: _topic_conditioned_depth(pages, cell) for cell in PROVISIONAL_NARROW_CELLS}
    rights = {
        "author_copyright_marker_hits": len(re.findall(r"©\s*Дяченко", "\n".join(pages))),
        "university_copyright_marker_hits": len(re.findall(r"©\s*ЖДУ", "\n".join(pages))),
        "creative_commons_marker_hits": len(
            re.findall(r"Creative\s*Commons|CC\s*BY|creativecommons", "\n".join(pages), flags=re.IGNORECASE)
        ),
        "license_word_hits": joined_lower.count("ліцензі"),
    }
    flags = {
        "davnoruska_marker_hits": joined_lower.count("давньорус"),
        "shared_east_slavic_calque_hits": joined_lower.count("спільносхіднослов") + joined_lower.count("общерус"),
        "russian_comparison_hits": joined_lower.count("російськ") + joined_lower.count("русск"),
        "soviet_era_marker_hits": joined_lower.count("радянськ") + joined_lower.count("ссср"),
        "etymology_marker_hits": joined_lower.count("етимолог"),
        "yazyk_token_hits": len(re.findall(r"\bязик\b", joined_lower)),
        "adjudication": "pending_independent_ukrainian_canon_review",
    }
    require(hits == CONTENT_FIT_MARKER_HITS, "content-fit marker hit drift")
    require(page_counts == CONTENT_FIT_PAGE_COUNTS, "content-fit page-count drift")
    require(document_wide_depth == CONTENT_FIT_DOCUMENT_WIDE_DEPTH, "document-wide depth drift")
    require(topic_conditioned == CONTENT_FIT_TOPIC_CONDITIONED, "topic-conditioned depth drift")
    require(rights == RIGHTS_MARKER_HITS, "rights marker hit drift")
    require(flags == UKRAINIAN_REVIEW_FLAGS, "Ukrainian-review flag drift")
    return {
        "marker_hits": hits,
        "page_counts": page_counts,
        "document_wide_depth": document_wide_depth,
        "topic_conditioned": topic_conditioned,
        "rights_marker_hits": rights,
        "ukrainian_review_flags": flags,
    }


def inspect_pdf(path: Path) -> dict[str, Any]:
    """Reproduce complete text-layer and content-fit facts without retaining source text."""
    _private_regular_file(path, "ZHDU source PDF")
    before = Path(path).stat()
    payload = Path(path).read_bytes()
    after = Path(path).stat()
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        "ZHDU source PDF changed while reading",
    )
    require(len(payload) == PDF_BYTES, "ZHDU source PDF byte denominator drift")
    require(hashlib.sha256(payload).hexdigest() == PDF_SHA256, "ZHDU source PDF SHA-256 drift")
    require(hashlib.md5(payload, usedforsecurity=False).hexdigest() == PDF_MD5, "ZHDU source PDF MD5 drift")
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError("cannot parse ZHDU source PDF") from exc
    require(not reader.is_encrypted, "ZHDU source PDF is unexpectedly encrypted")
    require(len(reader.pages) == PDF_PAGES, "ZHDU source PDF page denominator drift")
    page_rows: list[dict[str, Any]] = []
    complete_text: list[str] = []
    anomaly_pages: list[int] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise Zhdu2026LexicologyPhraseologyIntakeError(f"cannot extract ZHDU source page {page_number}") from exc
        require(text, f"ZHDU source page {page_number} has no embedded text")
        anomaly = detect_native_text_anomalies(text)
        if anomaly.get("requires_visual_verification"):
            anomaly_pages.append(page_number)
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
    require(not anomaly_pages, f"ZHDU native exactness defects on pages {anomaly_pages}")
    manifest_payload = b"".join(canonical_bytes(row) for row in page_rows)
    joined_text = "\n\f\n".join(complete_text).encode("utf-8")
    content_fit = _content_fit_from_pages(complete_text)
    facts = {
        "pages": len(page_rows),
        "text_bearing_pages": sum(row["chars"] > 0 for row in page_rows),
        "unicode_code_points": sum(row["chars"] for row in page_rows),
        "utf8_bytes": sum(row["bytes"] for row in page_rows),
        "page_manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "extracted_text_sha256": hashlib.sha256(joined_text).hexdigest(),
        "anomaly_page_count": 0,
        "isbn_text_verified": SOURCE_ISBN in "\n".join(complete_text),
        "board_recommendation_marker_verified": content_fit["marker_hits"]["board_recommendation"] > 0,
        "audience_philology_marker_verified": content_fit["marker_hits"]["audience_philology"] > 0,
        "content_fit": content_fit,
        "page_texts": complete_text,
    }
    require(
        {
            "pages": facts["pages"],
            "text_bearing_pages": facts["text_bearing_pages"],
            "unicode_code_points": facts["unicode_code_points"],
            "utf8_bytes": facts["utf8_bytes"],
            "page_manifest_sha256": facts["page_manifest_sha256"],
            "extracted_text_sha256": facts["extracted_text_sha256"],
        }
        == {
            "pages": PDF_PAGES,
            "text_bearing_pages": TEXT_BEARING_PAGES,
            "unicode_code_points": UNICODE_CODE_POINTS,
            "utf8_bytes": UTF8_BYTES,
            "page_manifest_sha256": PAGE_MANIFEST_SHA256,
            "extracted_text_sha256": EXTRACTED_TEXT_SHA256,
        },
        "ZHDU complete text-layer facts drift",
    )
    require(facts["isbn_text_verified"] is True, "ZHDU ISBN missing from embedded text")
    return facts


def validate_landing(path: Path) -> dict[str, Any]:
    payload = _read_private_bytes(path, "ZHDU landing HTML", LANDING_SHA256)
    require(len(payload) == LANDING_BYTES, "ZHDU landing byte denominator drift")
    try:
        html = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError("ZHDU landing is not UTF-8") from exc
    require(SOURCE_TITLE in _meta_values(html, "eprints.title"), "ZHDU landing title drift")
    require(_meta_values(html, "eprints.creators_name") == SOURCE_METADATA_AUTHORS, "ZHDU landing author drift")
    require(SOURCE_ISBN in _meta_values(html, "eprints.isbn"), "ZHDU landing ISBN drift")
    require(_meta_values(html, "eprints.type") == ["book"], "ZHDU landing type drift")
    require(_meta_values(html, "eprints.publisher") == [SOURCE_PUBLISHER], "ZHDU landing publisher drift")
    require("2026-06-26" in _meta_values(html, "eprints.date"), "ZHDU landing publication-date drift")
    require("creativecommons" not in html.lower(), "ZHDU landing unexpectedly declares Creative Commons")
    require("creative commons" not in html.lower(), "ZHDU landing unexpectedly declares Creative Commons")
    require(not re.search(r"\bCC\s*BY\b", html, flags=re.IGNORECASE), "ZHDU landing unexpectedly declares CC BY")
    return {
        "landing_sha256": LANDING_SHA256,
        "landing_bytes": LANDING_BYTES,
        "type": "book",
        "standardized_license_present": False,
    }


def _page_record(page_number: int, text: str) -> dict[str, Any]:
    encoded = text.encode("utf-8")
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "chunk_id": f"{SOURCE_ID}_p{page_number:04d}",
        "title": f"Сторінка {page_number}",
        "section_title": f"Сторінка {page_number}",
        "text": text,
        "text_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_file": SOURCE_ID,
        "source_pdf_sha256": PDF_SHA256,
        "subject": "ukrmova",
        "grade": "university",
        "author": "Дяченко; Фальківська",
        "author_uk": "Дяченко Н. М.; Фальківська Л. П.",
        "page_start": page_number,
        "page_end": page_number,
        "extraction_mode": "native_pdf_text",
        "page_extraction_mode": "native_pdf_text",
        "exactness": {
            "normalization_applied": False,
            "ocr_used": False,
            "repairs_applied": False,
        },
    }


def extract_records(source_pdf: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    facts = inspect_pdf(source_pdf)
    records = [_page_record(page_number, text) for page_number, text in enumerate(facts["page_texts"], start=1)]
    require(len(records) == PDF_PAGES, "page record denominator drift")
    text_free_facts = {key: value for key, value in facts.items() if key != "page_texts"}
    return records, text_free_facts


def write_private_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> tuple[int, str]:
    require(path.name == JSONL_FILENAME, "private JSONL filename drift")
    payload = b"".join(canonical_bytes(record) for record in records)
    _atomic_write_private_bytes(path, payload, "private JSONL")
    return len(payload), sha256_bytes(payload)


def run_exactness_audit(chunks_root: Path, audit_dir: Path) -> dict[str, Any]:
    _prepare_private_directory(audit_dir, "exactness audit directory")
    receipt, quarantined = audit_chunk_files(chunks_root)
    require(receipt["source_count"] == 1, "exactness source_count drift")
    require(receipt["chunk_total"] == PDF_PAGES, "exactness chunk_total drift")
    require(receipt["flagged_chunk_count"] == 0, "exactness flagged_chunk_count drift")
    require(receipt["flagged_page_count"] == 0, "exactness flagged_page_count drift")
    require(receipt["unverified_flagged_chunk_count"] == 0, "exactness unverified flagged drift")
    require(not quarantined, "exactness quarantine unexpectedly non-empty")
    public_safe = {
        "schema_version": receipt["schema_version"],
        "source_count": receipt["source_count"],
        "chunk_total": receipt["chunk_total"],
        "flagged_source_count": receipt["flagged_source_count"],
        "flagged_chunk_count": receipt["flagged_chunk_count"],
        "verified_flagged_chunk_count": receipt["verified_flagged_chunk_count"],
        "unverified_flagged_chunk_count": receipt["unverified_flagged_chunk_count"],
        "flagged_page_count": receipt["flagged_page_count"],
        "clean_chunk_count": receipt["clean_chunk_count"],
        "source_file": SOURCE_ID,
        "relative_jsonl": f"grade-00/{JSONL_FILENAME}",
        "jsonl_sha256": receipt["sources"][0]["jsonl_sha256"],
    }
    payload = canonical_bytes(public_safe)
    audit_path = audit_dir / EXACTNESS_AUDIT_FILENAME
    _atomic_write_private_bytes(audit_path, payload, "exactness audit receipt")
    return {
        **public_safe,
        "audit_receipt_sha256": sha256_bytes(payload),
        "audit_receipt_bytes": len(payload),
        "audit_path": audit_path,
    }


def build_content_fitness(content_fit: Mapping[str, Any]) -> dict[str, Any]:
    hits = content_fit["marker_hits"]
    pages = content_fit["page_counts"]
    topic_conditioned = content_fit["topic_conditioned"]
    return {
        "target_cells": list(PROVISIONAL_NARROW_CELLS),
        "provisional_effect": "narrow_only_candidate",
        "topic_gaps_closed": [],
        "topic_gaps_narrowed_claimed": [],
        "document_wide_depth_evidence": {
            "scope": "document_wide",
            **dict(content_fit["document_wide_depth"]),
        },
        "cells": {
            "semantics": {
                "frozen_status": "partial",
                "provisional_effect": "narrow_only_candidate",
                "qualified_source_needed": SEMANTICS_QUALIFIED_SOURCE_NEEDED,
                "depth_evidence": {
                    "scope": "topic_conditioned",
                    **dict(topic_conditioned["semantics"]),
                },
            },
            "phraseology": {
                "frozen_status": "partial",
                "provisional_effect": "narrow_only_candidate",
                "qualified_source_needed": PHRASEOLOGY_QUALIFIED_SOURCE_NEEDED,
                "depth_evidence": {
                    "scope": "topic_conditioned",
                    **dict(topic_conditioned["phraseology"]),
                },
            },
        },
        "supporting_depth_outside_target_cells": {
            "lexicology_marker_hits": hits["lexicology"],
            "lexicology_pages": pages["lexicology_topic_pages"],
            "lexicography_marker_hits": hits["lexicography"],
            "lexicography_pages": pages["lexicography_topic_pages"],
            "lexicology_frozen_status": "sufficient",
            "note": "lexicology is already sufficient; this candidate is not used to claim lexicology closure",
        },
        "audience": {
            "current_ukrainian_philology_students": True,
            "programme_marker_verified": hits["audience_philology"] > 0,
            "repository_type": "book",
            "publication_year": 2026,
            "publication_period_post_2019": True,
            "board_recommendation_date": "2026-06-26",
            "board_recommendation_marker_verified": hits["board_recommendation"] > 0,
        },
        "explicit_limitations": [
            "Cursor content-fit notes are provisional marker evidence only.",
            "Independent Ukrainian-canon review must adjudicate terminology, Russianisms/calques, and factual claims.",
            "No university topic is closed by this candidate.",
            "Semantics and phraseology remain partial until root disposition after Ukrainian review.",
            "Cell depth_evidence is topic_conditioned; document_wide_depth_evidence is reported separately and must not be read as cell evidence.",
        ],
        "flags_for_ukrainian_review": dict(content_fit["ukrainian_review_flags"]),
    }


def validate_authoritative_university_state(
    *,
    university_freeze_path: Path | None = None,
    source_policy_path: Path | None = None,
) -> dict[str, str]:
    """Re-open and re-derive live university freeze / source-policy facts."""
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

    topics = freeze.get("topic_coverage", {}).get("topics")
    require(isinstance(topics, list), "university freeze topics missing")
    by_area = {topic.get("area"): topic for topic in topics if isinstance(topic, Mapping)}
    semantics = by_area.get("semantics")
    phraseology = by_area.get("phraseology")
    require(isinstance(semantics, Mapping), "university freeze semantics topic missing")
    require(isinstance(phraseology, Mapping), "university freeze phraseology topic missing")
    require(semantics.get("status") == "partial", "university freeze semantics status drift")
    require(phraseology.get("status") == "partial", "university freeze phraseology status drift")
    require(
        semantics.get("qualified_source_needed") == SEMANTICS_QUALIFIED_SOURCE_NEEDED,
        "university freeze semantics qualified-source need drift",
    )
    require(
        phraseology.get("qualified_source_needed") == PHRASEOLOGY_QUALIFIED_SOURCE_NEEDED,
        "university freeze phraseology qualified-source need drift",
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
    return {
        "university_content_audit_freeze_v1_sha256": freeze_sha256,
        "complete_source_policy_v4_sha256": policy_sha256,
    }


def build_receipt_body(
    *,
    text_facts: Mapping[str, Any],
    landing: Mapping[str, Any],
    exactness: Mapping[str, Any],
    custody: Mapping[str, Any],
    private_jsonl_sha256: str,
    private_jsonl_bytes: int,
) -> dict[str, Any]:
    authoritative = validate_authoritative_university_state()
    content_fitness = build_content_fitness(text_facts["content_fit"])
    body: dict[str, Any] = {
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
            "audience": "native_ukrainian_philology_students_ukrainian_language_and_literature",
            "year": 2026,
            "isbn": SOURCE_ISBN,
            "pages": PDF_PAGES,
            "item_url": SOURCE_ITEM_URL,
            "bitstream_url": SOURCE_BITSTREAM_URL,
            "private_input_locator": PRIVATE_INPUT_LOCATOR,
            "bitstream_is_complete_publication": True,
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "landing_html_sha256": LANDING_SHA256,
            "landing_html_bytes": LANDING_BYTES,
            "private_jsonl_sha256": private_jsonl_sha256,
            "private_jsonl_bytes": private_jsonl_bytes,
            "exactness_audit_sha256": exactness["audit_receipt_sha256"],
            "university_content_audit_freeze_v1_sha256": authoritative["university_content_audit_freeze_v1_sha256"],
            "complete_source_policy_v4_sha256": authoritative["complete_source_policy_v4_sha256"],
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
            "anomaly_page_count": text_facts["anomaly_page_count"],
            "isbn_text_verified": text_facts["isbn_text_verified"],
            "normalization_applied": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
        },
        "native_exactness": {
            "schema_version": exactness["schema_version"],
            "source_count": exactness["source_count"],
            "chunk_count": exactness["chunk_total"],
            "flagged_chunk_count": exactness["flagged_chunk_count"],
            "flagged_page_count": exactness["flagged_page_count"],
            "verified_flagged_chunk_count": exactness["verified_flagged_chunk_count"],
            "unverified_flagged_chunk_count": exactness["unverified_flagged_chunk_count"],
            "clean_chunk_count": exactness["clean_chunk_count"],
            "production_eligible_under_exactness_gate": True,
            "audit_receipt_sha256": exactness["audit_receipt_sha256"],
        },
        "content_fitness": content_fitness,
        "custody": custody,
        "rights": {
            "visibility": "publicly_accessible",
            "reuse_license": "not_stated",
            "rights_statement": RIGHTS_STATEMENT,
            "standardized_license_present": False,
            "landing_standardized_license_present": landing["standardized_license_present"],
            "author_copyright_notice_present": True,
            "university_copyright_notice_present": True,
            "operator_private_attributed_research_use_directed": True,
            "legal_reuse_authorization_established": False,
            "attribution_required": True,
            "takedown_ready": True,
            "adapt_or_remove_on_substantiated_complaint": True,
            "public_redistribution_authorized": False,
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
            "coverage_effect": "narrow_only_pending_ukrainian_canon_review",
        },
        "denominators": {
            "v2_source_units": V2_SOURCE_UNITS,
            "v2_evaluation_identities": V2_EVALUATION_IDENTITIES,
            "phase3_labels": PHASE3_LABELS,
            "university_topic_areas": UNIVERSITY_TOPIC_AREAS,
            "university_sufficient": UNIVERSITY_SUFFICIENT,
            "university_partial": UNIVERSITY_PARTIAL,
            "university_missing": UNIVERSITY_MISSING,
            "candidate_additive_outside_v2_totals": True,
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
            "Exact official bytes are privately custodied; Git retains metadata only.",
            "Native exactness passed with zero flagged pages/chunks; semantic validation remains out of scope.",
            "Cursor content-fit evidence may support NARROW_ONLY for semantics and phraseology but closes none.",
            "Independent Ukrainian-canon review must adjudicate terminology, calques, and factual/etymological claims.",
            "Root disposition remains required; Phase 3 stays incomplete and Phase 4 stays blocked.",
            "Absent reuse license keeps PDF/text private and blocks public redistribution and unrestricted training export.",
        ],
    }
    return body


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "ZHDU candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise Zhdu2026LexicologyPhraseologyIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
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
    require(receipt["bindings"]["source_pdf_sha256"] == PDF_SHA256, "receipt PDF hash drift")
    require(receipt["bindings"]["source_pdf_bytes"] == PDF_BYTES, "receipt PDF bytes drift")
    require(receipt["review_scope"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["review_scope"]["topic_gaps_narrowed"] == [], "receipt overclaims topic narrowing")
    require(receipt["content_fitness"]["topic_gaps_closed"] == [], "content-fitness overclaims closure")
    require(receipt["content_fitness"]["topic_gaps_narrowed_claimed"] == [], "content-fitness overclaims narrowing")
    require(
        receipt["content_fitness"]["cells"]["semantics"]["depth_evidence"]["scope"] == "topic_conditioned",
        "semantics depth evidence must be topic_conditioned",
    )
    require(
        receipt["content_fitness"]["cells"]["phraseology"]["depth_evidence"]["scope"] == "topic_conditioned",
        "phraseology depth evidence must be topic_conditioned",
    )
    require(
        receipt["content_fitness"]["document_wide_depth_evidence"]["scope"] == "document_wide",
        "document-wide depth scope drift",
    )
    require(
        receipt["content_fitness"]["cells"]["semantics"]["qualified_source_needed"]
        == SEMANTICS_QUALIFIED_SOURCE_NEEDED,
        "semantics qualified-source need drift",
    )
    require(
        receipt["content_fitness"]["cells"]["phraseology"]["qualified_source_needed"]
        == PHRASEOLOGY_QUALIFIED_SOURCE_NEEDED,
        "phraseology qualified-source need drift",
    )
    require(receipt["gates"]["semantic_gold"] is False, "receipt overclaims semantic gold")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(receipt["gates"]["source_coverage_ready"] is False, "receipt overclaims source coverage")
    require(receipt["denominators"]["v2_source_units"] == V2_SOURCE_UNITS, "v2 source-unit denominator drift")
    require(
        receipt["denominators"]["v2_evaluation_identities"] == V2_EVALUATION_IDENTITIES,
        "v2 evaluation denominator drift",
    )
    require(receipt["denominators"]["university_topic_areas"] == UNIVERSITY_TOPIC_AREAS, "topic-area denominator drift")
    require(receipt["denominators"]["university_sufficient"] == UNIVERSITY_SUFFICIENT, "sufficient denominator drift")
    require(receipt["denominators"]["university_partial"] == UNIVERSITY_PARTIAL, "partial denominator drift")
    require(receipt["denominators"]["university_missing"] == UNIVERSITY_MISSING, "missing denominator drift")
    require(receipt["rights"]["rights_statement"] == RIGHTS_STATEMENT, "rights statement drift")
    require(receipt["rights"]["public_redistribution_authorized"] is False, "receipt overclaims redistribution")
    require(
        receipt["rights"]["unrestricted_training_export_authorized"] is False,
        "receipt overclaims training export",
    )
    serialized = canonical_json(receipt)
    require("GoogleDrive-" not in serialized, "receipt leaks private Drive identity")
    require("@gmail.com" not in serialized, "receipt leaks private account identity")
    require("\f" not in serialized, "receipt retains extracted page-join markers")
    require("page_texts" not in receipt, "receipt retains private page texts")
    return receipt


def _read_public_receipt_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise Zhdu2026LexicologyPhraseologyIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


def write_public_receipt(path: Path, value: Mapping[str, Any]) -> None:
    """Idempotent public receipt write via the fixed private atomic writer.

    Creation always uses owner-only 0600. Existing files may be 0600 or the
    normal git-tracked 0644 checkout mode; changed bytes are refused. Never
    chmod/fchmod to 0644.
    """
    require(_inside_git_checkout(path), "public receipt must live inside Git")
    _reject_symlink_components(path, "public receipt")
    payload = canonical_bytes(value)
    if path.exists() or path.is_symlink():
        _regular_public(path, "public receipt")
        require(
            _read_public_receipt_no_follow(path) == payload,
            "refusing to overwrite an immutable public receipt",
        )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, payload)


def build_custody_block(
    *,
    staging_root: Path,
    provider_ids: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "google_drive_custody": True,
        "google_drive_mount_containment_verified": True,
        "google_drive_provider_identity_present": True,
        "google_drive_provider_identity_sha256": {
            name: sha256_bytes(value.encode("utf-8")) for name, value in sorted(provider_ids.items())
        },
        "drive_relative_directory": PRIVATE_INPUT_LOCATOR,
        "private_files_mode_0600": True,
        "private_directory_mode_0700": stat.S_IMODE(staging_root.stat().st_mode) == PRIVATE_DIR_MODE,
        "all_new_files_readback_hash_match": True,
        "artifacts": {
            "source_pdf": PDF_FILENAME,
            "landing_html": LANDING_FILENAME,
            "private_jsonl": f"processed/grade-00/{JSONL_FILENAME}",
            "exactness_audit": f"exactness/{EXACTNESS_AUDIT_FILENAME}",
            "custody_receipt": CUSTODY_RECEIPT_FILENAME,
            "checksums": CHECKSUMS_FILENAME,
        },
    }


def write_checksums(staging_root: Path, files: Mapping[str, Path]) -> Path:
    lines = [f"{sha256_file(path)}  {name}" for name, path in sorted(files.items())]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path = staging_root / CHECKSUMS_FILENAME
    _atomic_write_private_bytes(path, payload, "SHA256SUMS")
    return path


def write_custody_receipt(staging_root: Path, custody_receipt: Mapping[str, Any]) -> Path:
    path = staging_root / CUSTODY_RECEIPT_FILENAME
    payload = canonical_bytes(custody_receipt)
    _atomic_write_private_bytes(path, payload, "custody receipt")
    return path


def production_run(
    *,
    staging_root: Path,
    public_receipt_path: Path,
    source_pdf: Path | None = None,
    landing_html: Path | None = None,
) -> dict[str, Any]:
    _prepare_private_directory(staging_root, "ZHDU staging root")
    pdf_path = source_pdf or (staging_root / PDF_FILENAME)
    landing_path = landing_html or (staging_root / LANDING_FILENAME)
    require(pdf_path.resolve().parent == staging_root.resolve() or source_pdf is not None, "PDF path drift")
    landing = validate_landing(landing_path)
    records, text_facts = extract_records(pdf_path)
    jsonl_path = staging_root / "processed" / "grade-00" / JSONL_FILENAME
    jsonl_bytes, jsonl_sha256 = write_private_jsonl(jsonl_path, records)
    require(sha256_file(jsonl_path) == jsonl_sha256, "private JSONL read-back hash mismatch")
    exactness = run_exactness_audit(staging_root / "processed", staging_root / "exactness")
    require(exactness["jsonl_sha256"] == jsonl_sha256, "exactness JSONL hash drift")
    provider_ids = {
        "source_pdf": _verify_drive_readback(pdf_path, PDF_SHA256),
        "landing_html": _verify_drive_readback(landing_path, LANDING_SHA256),
        "private_jsonl": _verify_drive_readback(jsonl_path, jsonl_sha256),
        "exactness_audit": _verify_drive_readback(exactness["audit_path"], exactness["audit_receipt_sha256"]),
    }
    custody = build_custody_block(staging_root=staging_root, provider_ids=provider_ids)
    body = build_receipt_body(
        text_facts=text_facts,
        landing=landing,
        exactness=exactness,
        custody=custody,
        private_jsonl_sha256=jsonl_sha256,
        private_jsonl_bytes=jsonl_bytes,
    )
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    receipt = validate_receipt(receipt)
    write_public_receipt(public_receipt_path, receipt)
    checksum_files = {
        PDF_FILENAME: pdf_path,
        LANDING_FILENAME: landing_path,
        f"processed/grade-00/{JSONL_FILENAME}": jsonl_path,
        f"exactness/{EXACTNESS_AUDIT_FILENAME}": exactness["audit_path"],
    }
    checksums_path = write_checksums(staging_root, checksum_files)
    custody_receipt = {
        "schema_version": "phase3_zhdu_2026_lexicology_phraseology_custody_receipt_v1",
        "text_free": True,
        "provider_calls": False,
        "semantic_gold": False,
        "artifacts": {
            "source_pdf_sha256": PDF_SHA256,
            "landing_html_sha256": LANDING_SHA256,
            "private_jsonl_sha256": jsonl_sha256,
            "exactness_audit_sha256": exactness["audit_receipt_sha256"],
            "checksums_sha256": sha256_file(checksums_path),
            "public_receipt_sha256": receipt["receipt_sha256"],
        },
        "custody": custody,
        "native_exactness": {
            "chunk_count": exactness["chunk_total"],
            "flagged_chunk_count": exactness["flagged_chunk_count"],
            "flagged_page_count": exactness["flagged_page_count"],
        },
        "gates": {
            "private_custody_complete": True,
            "native_exactness_clean": True,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    custody_receipt["receipt_sha256"] = receipt_sha256(custody_receipt)
    custody_path = write_custody_receipt(staging_root, custody_receipt)
    _verify_drive_readback(custody_path, sha256_bytes(canonical_bytes(custody_receipt)))
    _verify_drive_readback(checksums_path, sha256_file(checksums_path))
    return receipt


def build_receipt(
    *,
    source_pdf: Path,
    landing_html: Path,
    private_jsonl: Path,
    exactness_audit: Path,
    custody_receipt: Path,
) -> dict[str, Any]:
    """Replay-only builder for hermetic tests and immutable public receipt checks."""
    landing = validate_landing(landing_html)
    records, text_facts = extract_records(source_pdf)
    payload = b"".join(canonical_bytes(record) for record in records)
    _private_regular_file(private_jsonl, "private JSONL")
    require(private_jsonl.read_bytes() == payload, "private JSONL replay drift")
    exactness_payload = _read_private_bytes(
        exactness_audit,
        "exactness audit receipt",
        sha256_file(exactness_audit),
    )
    exactness = json.loads(exactness_payload.decode("utf-8"))
    require(isinstance(exactness, dict), "exactness audit must be an object")
    require(exactness.get("flagged_chunk_count") == 0, "exactness replay flagged drift")
    custody_doc = json.loads(
        _read_private_bytes(custody_receipt, "custody receipt", sha256_file(custody_receipt)).decode("utf-8")
    )
    require(isinstance(custody_doc, dict), "custody receipt must be an object")
    custody = custody_doc.get("custody")
    require(isinstance(custody, Mapping), "custody block missing")
    body = build_receipt_body(
        text_facts=text_facts,
        landing=landing,
        exactness={
            **exactness,
            "audit_receipt_sha256": sha256_bytes(exactness_payload),
        },
        custody=dict(custody),
        private_jsonl_sha256=sha256_bytes(payload),
        private_jsonl_bytes=len(payload),
    )
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", type=Path, help="private Drive staging directory")
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--landing-html", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_PUBLIC_RECEIPT_PATH)
    parser.add_argument("--check", type=Path, help="validate an existing public receipt")
    parser.add_argument(
        "--production",
        action="store_true",
        help="materialize private JSONL/exactness/custody and write the public receipt",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            require(not args.production, "check mode is exclusive")
            receipt = validate_receipt(_read_json(args.check, "ZHDU candidate receipt"))
        elif args.production:
            staging = args.staging_root or default_staging_root()
            receipt = production_run(
                staging_root=staging,
                public_receipt_path=args.output,
                source_pdf=args.source_pdf,
                landing_html=args.landing_html,
            )
        else:
            raise Zhdu2026LexicologyPhraseologyIntakeError("specify --production or --check")
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]}))
    except Zhdu2026LexicologyPhraseologyIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
