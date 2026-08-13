#!/usr/bin/env python3
"""Verify the private VSPU 2021 modern-Ukrainian theory source intake.

The source remains outside Git.  This module replays byte custody, the complete
PDF text layer, institutional metadata, and the qualified source-review result,
then emits one text-free candidate receipt.  It deliberately does not authorize
database ingest, training conversion, a source-universe freeze, or Phase 4.
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
SCHEMA_PATH = DATA / "contracts/phase3_vspu_modern_theory_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_vspu_modern_theory_candidate_v1.json"

SCHEMA_VERSION = "phase3_vspu_modern_theory_candidate_v1"
STATUS = "ADMIT_SCOPED_CANDIDATE_PENDING_DETERMINISTIC_CONVERSION_AND_SCOPE_CRITIC"
SOURCE_ID = "uni-ukrmova-sulm-attestation-vspu-2021"
SOURCE_TITLE = "Сучасна українська літературна мова: підготовка до атестації"
SOURCE_AUTHORS = ["Гороф’янюк І. В.", "Павликівська Н. М.", "Павлушенко О. А.", "Прокопчук Л. В."]
SOURCE_METADATA_AUTHORS = [
    "Гороф’янюк, І. В.",
    "Павликівська, Н. М.",
    "Павлушенко, О. А.",
    "Прокопчук, Л. В.",
]
SOURCE_ITEM_UUID = "6b7a72f8-9e3a-40fa-b3e9-eb1365f605e7"
SOURCE_BITSTREAM_UUID = "b4c1c3c9-05b1-4e78-bccf-eefba3e1a84f"
SOURCE_ITEM_URL = f"https://dspace.vspu.edu.ua/items/{SOURCE_ITEM_UUID}"
SOURCE_BITSTREAM_URL = f"https://dspace.vspu.edu.ua/server/api/core/bitstreams/{SOURCE_BITSTREAM_UUID}/content"
SOURCE_ISBN = "978-966-949-794-9"

PDF_SHA256 = "3d9daeef725188a36489346517cb40f3fca6566f4878a0237407aecd2b974cb2"
PDF_MD5 = "2f4cf21988feca4c2416826e7da556a9"
PDF_BYTES = 1_643_715
PDF_PAGES = 158
TEXT_BEARING_PAGES = 158
UNICODE_CODE_POINTS = 279_249
UTF8_BYTES = 500_171
PAGE_MANIFEST_SHA256 = "96b9fca939ff64544bd11844b51249eb76ddf7ca45bbf88e3b61ffeb3f87b60e"
EXTRACTED_TEXT_SHA256 = "246f63d6a7849cb81d804bd64a0a6755d495dc3fa6666a8e1bd9018784b37e28"
ITEM_METADATA_SHA256 = "138e393629b02d0b45e73dcb79b5183dd1a149349eb93b4b9db19cb5a49104fb"
BITSTREAM_METADATA_SHA256 = "6847132c5401446fcee726a5e7b9a55dc331f1bf957a78dbc280fc767e51822c"
REVIEW_RESULT_SHA256 = "4d1e19f97bd8963bef9380c68b2d60108578b83e4cc3d0bc58d91540273c76b4"
V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"

TOPICS_NARROWED = [
    "phonetics",
    "phonology",
    "graphics",
    "morphemics",
    "word_formation",
    "semantics",
    "phraseology",
    "morphology",
    "government_valency",
    "historical_grammar",
]
TOPICS_UNCHANGED = [
    "orthoepy",
    "accentology",
    "discourse_pragmatics",
    "stylistics",
    "culture_of_language",
    "dialectology",
    "sociolinguistics",
    "language_contact",
    "history_of_literary_language",
    "corpus_linguistics",
    "ukrainian_specific_computational_linguistics_tokenization",
]
PRIMARY_ROLES = ["explicit_rule", "correct_example", "answer_key"]
SECONDARY_ROLES = ["ordinary_narration", "bibliography"]
ALLOWED_LANES = [
    "private_contextual_retrieval",
    "private_corpus_ingest",
    "linguistic_rule_evidence_after_conversion_and_review",
]
PROHIBITED_CLAIMS = [
    "cc_or_any_standardized_license",
    "warranty",
    "public_redistribution",
    "unrestricted_reuse",
]
PRIVATE_FILE_MODE = 0o600


class VspuModernTheoryIntakeError(ValueError):
    """The exact private source or its fail-closed disposition drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VspuModernTheoryIntakeError(message)


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
        raise VspuModernTheoryIntakeError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _inside_git_checkout(path: Path) -> bool:
    candidate = Path(path).resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _reject_symlink_components(path: Path, label: str) -> None:
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
        raise VspuModernTheoryIntakeError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _read_private_json(path: Path, label: str, expected_sha256: str) -> dict[str, Any]:
    _private_regular_file(path, label)
    require(sha256_file(path) == expected_sha256, f"{label} byte drift")
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuModernTheoryIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuModernTheoryIntakeError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _metadata_values(metadata: Mapping[str, Any], key: str) -> list[str]:
    rows = metadata.get("metadata", {}).get(key, [])
    require(isinstance(rows, list), f"item metadata {key} is malformed")
    values = [row.get("value") for row in rows if isinstance(row, Mapping)]
    require(all(isinstance(value, str) for value in values), f"item metadata {key} contains a malformed value")
    return [str(value) for value in values]


def inspect_pdf(path: Path) -> dict[str, Any]:
    """Reproduce complete text-layer facts without retaining source text."""
    _private_regular_file(path, "VSPU source PDF")
    before = Path(path).stat()
    payload = Path(path).read_bytes()
    after = Path(path).stat()
    require(
        (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
        "VSPU source PDF changed while reading",
    )
    require(len(payload) == PDF_BYTES, "VSPU source PDF byte denominator drift")
    require(hashlib.sha256(payload).hexdigest() == PDF_SHA256, "VSPU source PDF SHA-256 drift")
    require(hashlib.md5(payload, usedforsecurity=False).hexdigest() == PDF_MD5, "VSPU source PDF MD5 drift")
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise VspuModernTheoryIntakeError("cannot parse VSPU source PDF") from exc
    require(not reader.is_encrypted, "VSPU source PDF is unexpectedly encrypted")
    require(len(reader.pages) == PDF_PAGES, "VSPU source PDF page denominator drift")
    page_rows: list[dict[str, Any]] = []
    complete_text: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise VspuModernTheoryIntakeError(f"cannot extract VSPU source page {page_number}") from exc
        require(text, f"VSPU source page {page_number} has no embedded text")
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
    joined_text = "\n\f\n".join(complete_text).encode("utf-8")
    facts = {
        "pages": len(page_rows),
        "text_bearing_pages": sum(row["chars"] > 0 for row in page_rows),
        "unicode_code_points": sum(row["chars"] for row in page_rows),
        "utf8_bytes": sum(row["bytes"] for row in page_rows),
        "page_manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "extracted_text_sha256": hashlib.sha256(joined_text).hexdigest(),
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
        },
        "VSPU complete text-layer facts drift",
    )
    return facts


def validate_item_metadata(path: Path) -> dict[str, Any]:
    value = _read_private_json(path, "VSPU item metadata", ITEM_METADATA_SHA256)
    require(value.get("uuid") == SOURCE_ITEM_UUID, "VSPU item UUID drift")
    require(value.get("name") == SOURCE_TITLE.upper(), "VSPU item title drift")
    require(_metadata_values(value, "dc.date.issued") == ["2021"], "VSPU issue year drift")
    require(SOURCE_ISBN in _metadata_values(value, "dc.identifier.isbn"), "VSPU ISBN drift")
    require(SOURCE_ITEM_URL in _metadata_values(value, "dc.identifier.uri"), "VSPU item locator drift")
    require(
        _metadata_values(value, "dc.contributor.author")[:4] == SOURCE_METADATA_AUTHORS,
        "VSPU author metadata drift",
    )
    require(not _metadata_values(value, "dc.rights"), "VSPU metadata unexpectedly declares a rights license")
    return value


def validate_bitstream_metadata(path: Path) -> dict[str, Any]:
    value = _read_private_json(path, "VSPU bitstream metadata", BITSTREAM_METADATA_SHA256)
    require(value.get("uuid") == SOURCE_BITSTREAM_UUID, "VSPU bitstream UUID drift")
    require(value.get("sizeBytes") == PDF_BYTES, "VSPU bitstream size drift")
    require(value.get("bundleName") == "ORIGINAL", "VSPU bitstream bundle drift")
    require(
        value.get("checkSum") == {"checkSumAlgorithm": "MD5", "value": PDF_MD5},
        "VSPU bitstream checksum drift",
    )
    return value


def validate_review(path: Path, text_facts: Mapping[str, Any]) -> dict[str, Any]:
    review = _read_private_json(path, "VSPU Ukrainian source review", REVIEW_RESULT_SHA256)
    require(review.get("schema_version") == "phase3_vspu_modern_theory_source_review_v1", "review schema drift")
    require(review.get("reviewer_seat") == "Ukrainian Source Reviewer", "reviewer seat drift")
    require(review.get("retry_scope") == "hash_blocker_resolution_only_no_semantic_rerun", "review retry scope drift")
    require(review.get("source_id") == SOURCE_ID, "review source identity drift")
    require(
        review.get("verified_bindings")
        == {
            "pdf_sha256": PDF_SHA256,
            "pdf_bytes": PDF_BYTES,
            **dict(text_facts),
            "item_metadata_sha256": ITEM_METADATA_SHA256,
            "bitstream_metadata_sha256": BITSTREAM_METADATA_SHA256,
        },
        "review evidence bindings drift",
    )
    require(review.get("content_disposition") == "admit_scoped_candidate", "review disposition drift")
    require(review.get("topic_gaps_closed") == [], "review overclaims a closed topic gap")
    require(review.get("topic_gaps_narrowed") == TOPICS_NARROWED, "review narrowed-topic set drift")
    require(review.get("topic_gaps_unchanged") == TOPICS_UNCHANGED, "review unchanged-topic set drift")
    require(review.get("primary_roles") == PRIMARY_ROLES, "review primary-role drift")
    require(review.get("secondary_roles") == SECONDARY_ROLES, "review secondary-role drift")
    require(review.get("allowed_lanes") == ALLOWED_LANES, "review lane drift")
    require(review.get("prohibited_claims") == PROHIBITED_CLAIMS, "review prohibited-claim drift")
    rights = review.get("rights_state")
    require(isinstance(rights, Mapping), "review rights state missing")
    require(rights.get("standardized_license") == "none", "review invents a standardized license")
    require(
        rights.get("authorization") == "operator_explicit_private_text_only_phase3_use",
        "review operator authorization drift",
    )
    require(review.get("normative_rule_authority") is False, "review grants source-wide normative authority")
    for key in (
        "database_ingest_authorized",
        "training_conversion_complete",
        "semantic_gold",
        "source_universe_frozen",
        "phase3_complete",
    ):
        require(review.get(key) is False, f"review overclaims {key}")
    require(review.get("phase4_blocked") is True, "review opens Phase 4")
    require(review.get("verdict") == STATUS, "review verdict drift")
    return review


def build_receipt(
    *,
    source_pdf: Path,
    item_metadata: Path,
    bitstream_metadata: Path,
    review_result: Path,
) -> dict[str, Any]:
    text_facts = inspect_pdf(source_pdf)
    validate_item_metadata(item_metadata)
    validate_bitstream_metadata(bitstream_metadata)
    review = validate_review(review_result, text_facts)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source": {
            "source_id": SOURCE_ID,
            "title": SOURCE_TITLE,
            "authors": list(SOURCE_AUTHORS),
            "institution": "Вінницький державний педагогічний університет імені Михайла Коцюбинського",
            "audience": "native_ukrainian_bachelor_programmes_014_and_035",
            "year": 2021,
            "pages": PDF_PAGES,
            "isbn": SOURCE_ISBN,
            "item_url": SOURCE_ITEM_URL,
            "bitstream_url": SOURCE_BITSTREAM_URL,
        },
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "source_pdf_sha256": PDF_SHA256,
            "source_pdf_md5": PDF_MD5,
            "source_pdf_bytes": PDF_BYTES,
            "item_metadata_sha256": ITEM_METADATA_SHA256,
            "bitstream_metadata_sha256": BITSTREAM_METADATA_SHA256,
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
            "seat": review["reviewer_seat"],
            "denominator": review["prior_review_denominator"],
            "content_disposition": review["content_disposition"],
            "topic_gaps_closed": [],
            "topic_gaps_narrowed": list(TOPICS_NARROWED),
            "topic_gaps_unchanged": list(TOPICS_UNCHANGED),
            "primary_roles": list(PRIMARY_ROLES),
            "secondary_roles": list(SECONDARY_ROLES),
            "allowed_lanes": list(ALLOWED_LANES),
            "prohibited_claims": list(PROHIBITED_CLAIMS),
        },
        "rights": {
            "standardized_license_present": False,
            "operator_private_text_only_phase3_use_authorized": True,
            "attribution_required": True,
            "takedown_ready": True,
            "adapt_or_remove_on_substantiated_complaint": True,
            "public_redistribution_authorized": False,
            "unrestricted_reuse_authorized": False,
        },
        "gates": {
            "scope_critic_complete": False,
            "database_ingest_authorized": False,
            "training_conversion_complete": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "The source narrows ten partial topics but closes none of the twenty-one frozen university gaps.",
            "An independent Scope/Circularity Critic must review the additive candidate and complete topic matrix.",
            "Deterministic role-layer conversion and a separate database-ingest authorization remain pending.",
            "Only exact reviewed explicit-rule spans may later carry scoped normative authority.",
        ],
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "VSPU candidate receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise VspuModernTheoryIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(receipt["review"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic gap")
    require(receipt["gates"]["source_coverage_ready"] is False, "receipt overclaims source coverage")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    return receipt


def write_public_receipt(path: Path, value: Mapping[str, Any]) -> None:
    require(_inside_git_checkout(path), "public receipt must live inside Git")
    _reject_symlink_components(path.parent, "public receipt parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    if path.exists():
        require(not path.is_symlink() and path.is_file(), "public receipt path is unsafe")
        require(path.read_bytes() == payload, "refusing to overwrite an immutable public receipt")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--item-metadata", type=Path)
    parser.add_argument("--bitstream-metadata", type=Path)
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
                    (args.source_pdf, args.item_metadata, args.bitstream_metadata, args.review_result, args.output)
                ),
                "check mode is exclusive",
            )
            receipt = validate_receipt(_read_json(args.check, "VSPU candidate receipt"))
        else:
            required = {
                "--source-pdf": args.source_pdf,
                "--item-metadata": args.item_metadata,
                "--bitstream-metadata": args.bitstream_metadata,
                "--review-result": args.review_result,
                "--output": args.output,
            }
            missing = [name for name, item in required.items() if item is None]
            require(not missing, f"materialization mode requires: {', '.join(missing)}")
            receipt = build_receipt(
                source_pdf=args.source_pdf,
                item_metadata=args.item_metadata,
                bitstream_metadata=args.bitstream_metadata,
                review_result=args.review_result,
            )
            write_public_receipt(args.output, receipt)
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    except VspuModernTheoryIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
