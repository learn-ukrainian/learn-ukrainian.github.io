#!/usr/bin/env python3
"""Materialize the admitted VSPU handbook as exact private page source units.

The PDF and JSONL remain outside Git.  The public receipt is text-free and
records conversion and exactness evidence only; it does not freeze semantic
roles, authorize database mutation, or open Phase 4.
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
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator
from pypdf import PdfReader

from scripts.projects.open_model_data import phase3_vspu_modern_theory_intake as intake
from scripts.rag.extract_text import detect_native_text_anomalies

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_vspu_source_materialization_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_vspu_source_materialization_v1.json"
DEFAULT_CANDIDATE_PATH = DATA / "admission/phase3_vspu_modern_theory_candidate_v1.json"
DEFAULT_UNIVERSITY_FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
DEFAULT_SOURCE_POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"
DEFAULT_HISTORICAL_FREEZE_PATH = DATA / "admission/phase3_historical_periodization_freeze_v1.json"

SCHEMA_VERSION = "phase3_vspu_source_materialization_v1"
STATUS = "PRIVATE_SOURCE_UNITS_MATERIALIZED_PENDING_DB_INGEST_GATE"
RECORD_SCHEMA_VERSION = "phase3_vspu_page_source_unit_v1"
SCOPE_SCHEMA_VERSION = "phase3_vspu_scope_circularity_review_v1"
SOURCE_ID = intake.SOURCE_ID
OUTPUT_FILENAME = f"{SOURCE_ID}.jsonl"
SCOPE_PROVIDER_RESULT_SHA256 = "d2c92e39cbe476c271c79a44b2b1f5295de71f7e4e8d90cc362d97312df836d0"
PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"

EXPECTED_BINDINGS = {
    "phase3_recovery_prompt_v2_sha256": intake.V2_PROMPT_SHA256,
    "phase3_reboot_prompt_v3_sha256": intake.V3_PROMPT_SHA256,
    "candidate_receipt_sha256": "0d0563e33da30951e6b2d74beb05ee91039dfcd3523e2e58019463cbd65c3adb",
    "university_content_audit_freeze_v1_sha256": "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b",
    "complete_source_policy_v4_sha256": "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559",
    "historical_periodization_freeze_v1_sha256": "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198",
}


class VspuSourceMaterializationError(ValueError):
    """Private source conversion or a bound admission fact drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VspuSourceMaterializationError(message)


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
        raise VspuSourceMaterializationError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_bytes(body))


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
        raise VspuSourceMaterializationError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not Path(path).is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def _prepare_private_directory(path: Path) -> None:
    require(not _inside_git_checkout(path), "private output cannot live inside Git")
    _reject_symlink_components(path, "private output directory")
    prior_umask = os.umask(0o077)
    try:
        path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    finally:
        os.umask(prior_umask)
    os.chmod(path, PRIVATE_DIR_MODE)
    result = path.lstat()
    require(stat.S_ISDIR(result.st_mode) and not path.is_symlink(), "private output must be a regular directory")
    require(stat.S_IMODE(result.st_mode) == PRIVATE_DIR_MODE, "private output directory must be mode 0700")


def _read_json(path: Path, label: str, *, private: bool = False) -> dict[str, Any]:
    if private:
        _private_regular_file(path, label)
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuSourceMaterializationError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _validate_bound_public_inputs(
    *,
    candidate_path: Path,
    university_freeze_path: Path,
    source_policy_path: Path,
    historical_freeze_path: Path,
) -> None:
    paths = {
        "candidate_receipt_sha256": candidate_path,
        "university_content_audit_freeze_v1_sha256": university_freeze_path,
        "complete_source_policy_v4_sha256": source_policy_path,
        "historical_periodization_freeze_v1_sha256": historical_freeze_path,
    }
    for key, path in paths.items():
        require(sha256_file(path) == EXPECTED_BINDINGS[key], f"{key} byte drift")
    candidate = intake.validate_receipt(_read_json(candidate_path, "VSPU candidate receipt"))
    require(candidate["receipt_sha256"] == intake.receipt_sha256(candidate), "candidate receipt hash drift")
    require(candidate["source"]["source_id"] == SOURCE_ID, "candidate source identity drift")
    require(candidate["gates"]["scope_critic_complete"] is False, "candidate unexpectedly claims scope completion")


def validate_scope_review(path: Path) -> dict[str, Any]:
    review = _read_json(path, "VSPU scope/circularity review", private=True)
    require(review.get("schema_version") == SCOPE_SCHEMA_VERSION, "scope review schema drift")
    require(review.get("reviewer_seat") == "Scope/Circularity Critic", "scope reviewer seat drift")
    require(review.get("verdict") == "PASS", "scope critic did not pass the additive candidate")
    denominator = review.get("denominator")
    require(isinstance(denominator, Mapping), "scope review denominator is missing")
    require(denominator.get("existing_candidate_sources") == 30, "scope review existing-source denominator drift")
    require(denominator.get("additive_candidate_sources") == 1, "scope review additive-source denominator drift")
    require(denominator.get("proposed_total_candidate_sources") == 31, "scope review total-source denominator drift")
    require(denominator.get("topic_areas") == 26, "scope review topic denominator drift")
    require(review.get("topic_gaps_closed") == [], "scope review overclaims a closed topic")
    require(review.get("topic_gaps_narrowed") == intake.TOPICS_NARROWED, "scope review narrowed-topic drift")
    require(review.get("topic_gaps_unchanged") == intake.TOPICS_UNCHANGED, "scope review unchanged-topic drift")
    require(
        review.get("source_disposition") == "admit_scoped_candidate",
        "scope review source disposition drift",
    )
    require(
        review.get("private_page_materialization_authorized") is True, "scope review did not authorize materialization"
    )
    require(review.get("source_wide_normative_authority") is False, "scope review grants source-wide authority")
    require(review.get("semantic_gold") is False, "scope review grants semantic gold")
    require(review.get("source_universe_frozen") is False, "scope review freezes the source universe")
    require(review.get("source_coverage_ready") is False, "scope review overclaims source coverage")
    require(review.get("phase3_complete") is False, "scope review overclaims Phase 3 completion")
    require(review.get("phase4_blocked") is True, "scope review opens Phase 4")
    findings = review.get("material_findings")
    require(findings == [], "scope review has unresolved material findings")
    return review


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
        "source_pdf_sha256": intake.PDF_SHA256,
        "subject": "ukrmova",
        "grade": "university",
        "author": "Гороф’янюк та ін.",
        "author_uk": "Гороф’янюк І. В. та ін.",
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
    """Extract every page without normalization and reject objective anomalies."""
    facts = intake.inspect_pdf(source_pdf)
    try:
        reader = PdfReader(source_pdf)
    except Exception as exc:
        raise VspuSourceMaterializationError("cannot parse VSPU source PDF") from exc
    require(not reader.is_encrypted, "VSPU source PDF is unexpectedly encrypted")
    require(len(reader.pages) == intake.PDF_PAGES, "VSPU page denominator drift")
    records: list[dict[str, Any]] = []
    text_manifest: list[dict[str, Any]] = []
    complete_text: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise VspuSourceMaterializationError(f"cannot extract VSPU source page {page_number}") from exc
        require(text, f"VSPU source page {page_number} has no embedded text")
        anomaly = detect_native_text_anomalies(text)
        require(
            not anomaly["requires_visual_verification"], f"VSPU source page {page_number} requires visual verification"
        )
        record = _page_record(page_number, text)
        records.append(record)
        text_manifest.append(
            {
                "page": page_number,
                "chars": len(text),
                "bytes": len(text.encode("utf-8")),
                "sha256": record["text_sha256"],
            }
        )
        complete_text.append(text)
    require([row["page_start"] for row in records] == list(range(1, intake.PDF_PAGES + 1)), "page sequence drift")
    manifest_hash = sha256_bytes(b"".join(canonical_bytes(row) for row in text_manifest))
    complete_hash = sha256_bytes("\n\f\n".join(complete_text).encode("utf-8"))
    require(manifest_hash == intake.PAGE_MANIFEST_SHA256, "materialized page manifest drift")
    require(complete_hash == intake.EXTRACTED_TEXT_SHA256, "materialized complete-text hash drift")
    require(facts["unicode_code_points"] == sum(len(row["text"]) for row in records), "character denominator drift")
    metadata_manifest = [{key: value for key, value in record.items() if key != "text"} for record in records]
    evidence = {
        "source_unit_count": len(records),
        "page_start": 1,
        "page_end": intake.PDF_PAGES,
        "text_bearing_pages": len(records),
        "native_text_pages": len(records),
        "ocr_pages": 0,
        "normalized_pages": 0,
        "repaired_pages": 0,
        "anomaly_pages": 0,
        "unicode_code_points": facts["unicode_code_points"],
        "utf8_bytes": facts["utf8_bytes"],
        "page_text_manifest_sha256": manifest_hash,
        "complete_text_sha256": complete_hash,
        "text_free_record_manifest_sha256": sha256_bytes(canonical_bytes(metadata_manifest)),
    }
    return records, evidence


def _encoded_records(records: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_bytes(record) for record in records)


def write_private_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> tuple[int, str]:
    _prepare_private_directory(path.parent)
    require(path.name == OUTPUT_FILENAME, "private JSONL filename drift")
    _reject_symlink_components(path, "private JSONL")
    payload = _encoded_records(records)
    if path.exists():
        _private_regular_file(path, "private JSONL")
        require(path.read_bytes() == payload, "refusing to overwrite a changed private JSONL")
        return len(payload), sha256_bytes(payload)
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
    _private_regular_file(path, "private JSONL")
    return len(payload), sha256_bytes(payload)


def read_private_jsonl(path: Path) -> list[dict[str, Any]]:
    _private_regular_file(path, "private JSONL")
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                value = json.loads(line)
                require(isinstance(value, dict), f"private JSONL line {line_number} is not an object")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise VspuSourceMaterializationError("cannot read private JSONL") from exc
    require(records, "private JSONL is empty")
    return records


def _drive_item_id(path: Path) -> str:
    resolved = path.resolve()
    try:
        drive_roots = [
            candidate.resolve()
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise VspuSourceMaterializationError("cannot inspect configured Google Drive mounts") from exc
    matches = [root for root in drive_roots if resolved.is_relative_to(root)]
    require(len(matches) == 1, "private JSONL is not inside exactly one configured Google Drive mount")
    try:
        probe = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VspuSourceMaterializationError("private JSONL lacks Google Drive provider identity") from exc
    value = probe.stdout.strip()
    require(value, "private JSONL has an empty Google Drive provider identity")
    return value


def build_receipt(
    *,
    source_pdf: Path,
    scope_review_path: Path,
    private_jsonl_path: Path,
    candidate_path: Path = DEFAULT_CANDIDATE_PATH,
    university_freeze_path: Path = DEFAULT_UNIVERSITY_FREEZE_PATH,
    source_policy_path: Path = DEFAULT_SOURCE_POLICY_PATH,
    historical_freeze_path: Path = DEFAULT_HISTORICAL_FREEZE_PATH,
) -> dict[str, Any]:
    _validate_bound_public_inputs(
        candidate_path=candidate_path,
        university_freeze_path=university_freeze_path,
        source_policy_path=source_policy_path,
        historical_freeze_path=historical_freeze_path,
    )
    review = validate_scope_review(scope_review_path)
    records, evidence = extract_records(source_pdf)
    jsonl_bytes, jsonl_sha256 = write_private_jsonl(private_jsonl_path, records)
    require(read_private_jsonl(private_jsonl_path) == records, "private JSONL round-trip drift")
    drive_item_id = _drive_item_id(private_jsonl_path)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source_id": SOURCE_ID,
        "bindings": {
            **EXPECTED_BINDINGS,
            "source_pdf_sha256": intake.PDF_SHA256,
            "scope_circularity_provider_result_sha256": SCOPE_PROVIDER_RESULT_SHA256,
            "scope_circularity_review_sha256": sha256_file(scope_review_path),
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "private_artifact": {
            "filename": OUTPUT_FILENAME,
            "jsonl_sha256": jsonl_sha256,
            "jsonl_bytes": jsonl_bytes,
            "file_mode": "0600",
            "inside_git": False,
            "google_drive_custody": True,
            "google_drive_mount_containment_verified": True,
            "google_drive_provider_identity_present": True,
            "google_drive_provider_identity_sha256": sha256_bytes(drive_item_id.encode("utf-8")),
            **evidence,
        },
        "scope_review": {
            "verdict": review["verdict"],
            "existing_candidate_sources": 30,
            "additive_candidate_sources": 1,
            "proposed_total_candidate_sources": 31,
            "topic_areas": 26,
            "topic_gaps_closed": [],
            "topic_gaps_narrowed": list(intake.TOPICS_NARROWED),
            "topic_gaps_unchanged": list(intake.TOPICS_UNCHANGED),
            "source_disposition": review["source_disposition"],
            "material_findings": [],
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
            "scope_critic_complete": True,
            "private_source_units_materialized": True,
            "exactness_audit_complete": True,
            "database_ingest_authorized": False,
            "database_ingest_complete": False,
            "role_layer_conversion_complete": False,
            "training_conversion_complete": False,
            "normative_rule_authority": False,
            "semantic_gold": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "A separate one-source database-ingest gate must bind this JSONL, a current database preimage backup, and an atomic copied-database rehearsal.",
            "The 158 source units still require deterministic role-layer conversion before any exact span can support scoped rule evidence.",
            "The source narrows ten university topics but closes none; the twenty-one partial university topics remain partial.",
            "Historical periodization and evidence residuals are unchanged.",
            "Bibliography may remain only a secondary attribute; its primary role must map to ordinary_narration or ambiguous_or_ocr under the frozen 12-role canon.",
        ],
    }
    receipt = {**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))}
    return validate_receipt(receipt)


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "VSPU materialization schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise VspuSourceMaterializationError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    for key, expected in EXPECTED_BINDINGS.items():
        require(receipt["bindings"][key] == expected, f"receipt binding drift: {key}")
    require(receipt["bindings"]["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(receipt["bindings"]["schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    require(receipt["scope_review"]["topic_gaps_closed"] == [], "receipt overclaims a closed topic")
    require(receipt["private_artifact"]["source_unit_count"] == intake.PDF_PAGES, "source-unit denominator drift")
    require(receipt["private_artifact"]["anomaly_pages"] == 0, "receipt admits anomalous pages")
    require(receipt["gates"]["database_ingest_authorized"] is False, "receipt authorizes database mutation")
    require(receipt["gates"]["semantic_gold"] is False, "receipt grants semantic gold")
    require(receipt["gates"]["phase3_complete"] is False, "receipt overclaims Phase 3 completion")
    require(receipt["gates"]["phase4_blocked"] is True, "receipt opens Phase 4")
    require(
        receipt["rights"]["legal_reuse_authorization_established"] is False,
        "receipt overclaims legal reuse authorization",
    )
    require(
        "operator_private_text_only_phase3_use_authorized" not in receipt["rights"],
        "receipt retains legacy operator authorization field",
    )
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
    os.replace(temporary, path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    parser.add_argument("--scope-review", type=Path)
    parser.add_argument("--private-jsonl", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check is not None:
            require(
                not any((args.source_pdf, args.scope_review, args.private_jsonl, args.output)),
                "check mode is exclusive",
            )
            receipt = validate_receipt(_read_json(args.check, "VSPU materialization receipt"))
        else:
            required = {
                "--source-pdf": args.source_pdf,
                "--scope-review": args.scope_review,
                "--private-jsonl": args.private_jsonl,
                "--output": args.output,
            }
            missing = [name for name, item in required.items() if item is None]
            require(not missing, f"materialization mode requires: {', '.join(missing)}")
            receipt = build_receipt(
                source_pdf=args.source_pdf,
                scope_review_path=args.scope_review,
                private_jsonl_path=args.private_jsonl,
            )
            write_public_receipt(args.output, receipt)
        print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    except VspuSourceMaterializationError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
