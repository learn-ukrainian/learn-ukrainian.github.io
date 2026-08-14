#!/usr/bin/env python3
"""Mint or audit the text-free UzhNU 2023 morphemology/derivatology candidate."""

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

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_uzhnu_2023_morphemology_derivatology_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_uzhnu_2023_morphemology_derivatology_candidate_v1.json"
FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"
SCRIPT_PATH = Path(__file__).resolve()

SCHEMA_VERSION = "phase3_uzhnu_2023_morphemology_derivatology_candidate_v1"
STATUS = "ACADEMIC_CANON_CORROBORATION_CANDIDATE_NO_GAP_TRANSITION"
SOURCE_ID = "uni-ukrmova-applied-morphemology-derivatology-vovchenko-2023"
TITLE = "Прикладне українське мовознавство: морфемологія і дериватологія сучасної української літературної мови"
AUTHOR = "Вовченко, Галина Іванівна"
STAGING_RELATIVE = "university_corpus/staging/phase3-6375-uzhnu-2023-morphemology-derivatology"
FREEZE_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"
POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PRIVATE_FILE_MODE, PRIVATE_DIR_MODE = 0o600, 0o700
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"
FREEZE_WORD_FORMATION_AREA = "word formation"

ARTIFACTS = {
    "item_metadata": (
        "item-metadata.json",
        6260,
        "96bc11ae3467d89d954bf8afccdf79fbc81a7b51df526c5d75c7d9f817596277",
        "96e472886184ef80fb858627606907a2d59ff3e7b83f4d23e22e27b497c371f5",
    ),
    "repository_license": (
        "license.txt",
        6479,
        "525cca59abbf86f988d32c88deea3b73bc496b316a23e142f527073047d6547e",
        "0a3beef69d511f81c3034e07bb9b802f3ae607a248e95222ca1bc43f6586d959",
    ),
    "source_pdf": (
        "uzhnu-2023-morphemology-derivatology.pdf",
        1210971,
        "a0afc0920b1846e0c16b8c3f84311e0c5c90bda1f6ee06005576eb9074f5ed97",
        "184c8d98c37e5b37c7c23d601e5ee23a7740807700a239e73d5d2e1d822aba2d",
    ),
    "private_audit_receipt": (
        "private-audit-receipt-v1.json",
        3925,
        "80e1e0a21749e496cb9d40bf8959c7199d9148024adde6855ae0fa975e0969b4",
        "a41cff713e6bf3d95c403d143a5da48cb9588a1f7239c1595f7d9d5ce81eee25",
    ),
}
TARGETS = {
    "morphemics": "Dedicated post-2019 university textbook on morphemics and morphemic structure of Ukrainian words.",
    "word_formation": "Specialized university coursebook on Ukrainian word formation (дериватологія).",
}


class Uzhnu2023MorphemologyDerivatologyIntakeError(ValueError):
    """A frozen source identity, custody condition, or gate drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError("cannot read private artifact") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError(f"cannot read {label}") from exc
    require(isinstance(result, dict), f"{label} must be an object")
    return result


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


def _inside_git_checkout(path: Path) -> bool:
    resolved = path.resolve()
    return any((parent / ".git").exists() for parent in (resolved, *resolved.parents))


def _private_dir(path: Path) -> None:
    _reject_symlink_components(path, "private stage")
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError("missing private stage") from exc
    require(stat.S_ISDIR(mode) and not path.is_symlink(), "private stage must be a directory")
    require(stat.S_IMODE(mode) == PRIVATE_DIR_MODE, "private stage must be mode 0700")
    require(not _inside_git_checkout(path), "private stage cannot live inside Git")


def _private_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError(f"missing {label}") from exc
    require(stat.S_ISREG(mode) and not path.is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(mode) == PRIVATE_FILE_MODE, f"{label} must be mode 0600")
    require(not _inside_git_checkout(path), f"{label} cannot live inside Git")


def default_staging_root() -> Path:
    roots = [p for p in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*") if (p / "My Drive").is_dir()]
    require(len(roots) == 1, "expected exactly one configured Google Drive mount")
    return roots[0] / "My Drive" / "Projects" / "learn-ukrainian-data" / STAGING_RELATIVE


def _drive_item_id(path: Path) -> str:
    roots = [p.resolve() for p in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*") if (p / "My Drive").is_dir()]
    require(
        len([root for root in roots if path.resolve().is_relative_to(root)]) == 1, "artifact is not in Google Drive"
    )
    try:
        result = subprocess.run(
            ["xattr", "-p", "com.google.drivefs.item-id#S", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError("artifact lacks Google Drive provider identity") from exc
    require(bool(result.stdout.strip()), "artifact has an empty Google Drive provider identity")
    return result.stdout.strip()


def validate_authoritative_state(freeze_path: Path | None = None, policy_path: Path | None = None) -> dict[str, str]:
    freeze_path, policy_path = freeze_path or FREEZE_PATH, policy_path or POLICY_PATH
    require(sha256_file(freeze_path) == FREEZE_SHA256, "university freeze hash drift")
    require(sha256_file(policy_path) == POLICY_SHA256, "source policy hash drift")
    freeze, policy = _read_json(freeze_path, "university freeze"), _read_json(policy_path, "source policy")
    counts = freeze.get("topic_coverage", {}).get("counts", {})
    require(
        counts == {"areas_required": 26, "missing": 0, "partial": 21, "sufficient": 5},
        "university topic denominators drift",
    )
    universe = freeze.get("source_universe", {})
    for key, expected in {
        "candidate_source_count": 30,
        "database_resident_source_count": 20,
        "reference_only_source_count": 6,
        "quarantine_source_count": 4,
    }.items():
        require(universe.get(key) == expected, f"university {key} drift")
    topics = {
        item.get("area"): item
        for item in freeze.get("topic_coverage", {}).get("topics", [])
        if isinstance(item, Mapping)
    }
    for area, need in TARGETS.items():
        freeze_area = FREEZE_WORD_FORMATION_AREA if area == "word_formation" else area
        require(topics.get(freeze_area, {}).get("status") == "partial", f"university {area} status drift")
        require(
            topics.get(freeze_area, {}).get("qualified_source_needed") == need,
            f"university {area} qualified-source need drift",
        )
    gates = freeze.get("gates", {})
    require(
        gates.get("phase3_complete") is False and gates.get("phase4_blocked") is True, "university freeze gate drift"
    )
    require(policy.get("phase3_complete") is False and policy.get("phase4_blocked") is True, "source policy gate drift")
    return {
        "university_content_audit_freeze_v1_sha256": FREEZE_SHA256,
        "complete_source_policy_v4_sha256": POLICY_SHA256,
    }


def build_receipt_body() -> dict[str, Any]:
    bindings = validate_authoritative_state()
    cells = [
        {
            "area": area,
            "frozen_status": "partial",
            "qualified_source_needed": need,
            "evidence_classification": "NARROW_ONLY",
            "role": "current_practical_corroboration_no_gap_transition",
        }
        for area, need in TARGETS.items()
    ]
    artifacts = {
        label: {"filename": filename, "bytes": size, "sha256": digest, "provider_item_id_sha256": provider}
        for label, (filename, size, digest, provider) in ARTIFACTS.items()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "text_free": True,
        "provider_calls": False,
        "source": {
            "source_id": SOURCE_ID,
            "title": TITLE,
            "author": AUTHOR,
            "institution": "ДВНЗ «Ужгородський національний університет»",
            "faculty_department": "Faculty of Philology, Department of Ukrainian Language",
            "approval": "faculty academic council protocol no. 6 dated 30 March 2023",
            "year": 2023,
            "printed_pages": 67,
            "pdf_page_objects": 67,
            "genre": "native_university_navchalno-metodychnyi_posibnyk",
            "item_uuid": "57c669bb-90bf-4cf5-a8bc-339c6b1108ca",
            "handle_url": "https://dspace.uzhnu.edu.ua/jspui/handle/lib/51016",
            "item_api_url": "https://dspace.uzhnu.edu.ua/server/api/core/items/57c669bb-90bf-4cf5-a8bc-339c6b1108ca",
            "pdf_bitstream_uuid": "b9ce2537-1792-4f8a-be39-e6f07e076d83",
            "license_bitstream_uuid": "84b4db4c-fcfa-40ff-bbef-e59f862942e9",
            "private_input_locator": STAGING_RELATIVE,
        },
        "bindings": {
            **bindings,
            "phase3_recovery_prompt_v2_sha256": V2_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_SHA256,
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "custody": {
            "private_stage_mode": "0700",
            "private_file_mode": "0600",
            "drive_uploaded_readback_verified": True,
            "artifacts": artifacts,
        },
        "text_layer": {
            "pdf_pages": 67,
            "text_bearing_pages": 67,
            "extracted_characters": 156236,
            "encrypted": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
            "visual_qa_passed_pdf_pages": [1, 2, 4, 10, 30, 60, 67],
        },
        "signals": {
            "morphemics": 263,
            "derivatology": 56,
            "word_formation": 348,
            "practical": 54,
            "theoretical": 19,
            "morphonology": 39,
        },
        "content_fitness": {
            "primary_role": "modern_ukrainian_practical_university_handbook",
            "target_cells": cells,
            "descriptive_topics": [
                {"topic": "derivatology", "role": "diagnostic_signal_only_not_a_primary_cell"},
                {"topic": "morphonology", "role": "diagnostic_signal_only_not_a_primary_cell"},
            ],
            "broad_topics": [
                "morphemics",
                "morphemology",
                "word_formation",
                "derivatology",
                "morphonology",
                "practical_exercises",
                "theoretical_foundations",
                "morphemic_analysis",
                "derivational_analysis",
            ],
            "limitations": (
                "faculty-approved practical-methodological manual; derivatology and morphonology "
                "signals are descriptive only and do not substitute dedicated qualified sources"
            ),
            "topic_gaps_closed": [],
            "topic_gaps_narrowed_claimed": [],
        },
        "rights": {
            "metadata_standard_license_present": False,
            "repository_deposit_terms": (
                "author retains copyright; grants UzhNU non-exclusive repository, preservation, "
                "open-access, noncommercial-copying, and distribution rights"
            ),
            "general_downstream_dataset_license_established": False,
            "private_acquisition": True,
            "private_backup": True,
            "private_extraction": True,
            "private_training_preparation": True,
            "public_reconstructable_full_text_export": False,
            "unrestricted_training_export": False,
            "public_text_free_metadata_hash_nonreconstructable_evidence": True,
            "final_release_review_required": True,
            "takedown_adapt_on_substantiated_complaint": True,
        },
        "denominators": {
            "v2_source_units": 67041,
            "v2_evaluation_identities": 9392,
            "university_total": 26,
            "university_sufficient": 5,
            "university_partial": 21,
            "university_missing": 0,
            "candidate_sources": 30,
            "database_resident_sources": 20,
            "reference_only_sources": 6,
            "quarantine_sources": 4,
        },
        "gates": {
            "database_ingest_authorized": False,
            "semantic_gold": False,
            "author_eval_membership": False,
            "topic_gaps_closed": False,
            "topic_gaps_narrowed": False,
            "source_universe_frozen": False,
            "source_coverage_ready": False,
            "source_freeze_ready": False,
            "phase3_complete": False,
            "phase4_authorized": False,
            "phase4_blocked": True,
        },
        "residuals": [
            "Current faculty-approved practical corroboration does not close or narrow any frozen gap.",
            "Both frozen target cells remain partial; the qualified-source needs remain open.",
            "Derivatology and morphonology marker counts are descriptive only, not primary gap-transition cells.",
            "No database ingest, semantic gold, author/eval membership, source-universe freeze, Phase 3 completion, or Phase 4 authorization.",
        ],
    }


def mint_receipt() -> dict[str, Any]:
    body = build_receipt_body()
    return validate_receipt({**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))})


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "UzhNU candidate schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise Uzhnu2023MorphemologyDerivatologyIntakeError(
            f"receipt schema violation at {location}: {errors[0].message}"
        )
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    require(receipt == {**build_receipt_body(), "receipt_sha256": receipt["receipt_sha256"]}, "receipt body drift")
    encoded = canonical_json(receipt)
    for forbidden in (
        "GoogleDrive-",
        "@gmail.com",
        "/Users/",
        "Library/CloudStorage",
        '"page_texts"',
        '"source_text"',
        "\f",
    ):
        require(forbidden not in encoded, "receipt leaks private path, identity, or source text")
    return receipt


def _read_public_no_follow(path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    require(no_follow != 0, "platform cannot enforce no-follow public receipt reads")
    try:
        descriptor = os.open(path, os.O_RDONLY | no_follow)
    except OSError as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    except OSError as exc:
        raise Uzhnu2023MorphemologyDerivatologyIntakeError("cannot safely read existing public receipt") from exc
    finally:
        os.close(descriptor)


def write_public_receipt(path: Path, value: Mapping[str, Any]) -> None:
    require(_inside_git_checkout(path), "public receipt must live inside Git")
    _reject_symlink_components(path.parent, "public receipt parent")
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        require(
            not path.is_symlink() and _read_public_no_follow(path) == payload,
            "refusing to overwrite immutable public receipt",
        )
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.chmod(temporary, PRIVATE_FILE_MODE)
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        require(_read_public_no_follow(path) == payload, "refusing to overwrite immutable public receipt")
    finally:
        temporary.unlink(missing_ok=True)


def private_audit(staging_root: Path | None = None) -> dict[str, Any]:
    staging = staging_root or default_staging_root()
    _private_dir(staging)
    provider_hashes: dict[str, str] = {}
    for label, (filename, expected_bytes, expected_hash, expected_provider_hash) in ARTIFACTS.items():
        path = staging / filename
        _private_file(path, label)
        require(path.stat().st_size == expected_bytes, f"{label} byte drift")
        require(sha256_file(path) == expected_hash, f"{label} hash drift")
        provider_hashes[label] = sha256_bytes(_drive_item_id(path).encode("utf-8"))
        require(provider_hashes[label] == expected_provider_hash, f"{label} provider identity drift")
    return {
        "ok": True,
        "staging_root": STAGING_RELATIVE,
        "artifact_count": len(ARTIFACTS),
        "provider_identity_sha256": provider_hashes,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--mint", action="store_true")
    parser.add_argument("--write", type=Path, default=DEFAULT_PUBLIC_RECEIPT_PATH)
    parser.add_argument("--private-audit", action="store_true")
    parser.add_argument("--staging-root", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.check:
            require(not args.mint and not args.private_audit, "check mode is exclusive")
            receipt = validate_receipt(_read_json(args.check, "UzhNU candidate receipt"))
            result = {"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]}
        elif args.private_audit:
            require(not args.mint, "private-audit mode is exclusive")
            result = private_audit(args.staging_root)
        elif args.mint:
            receipt = mint_receipt()
            write_public_receipt(args.write, receipt)
            result = {"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]}
        else:
            raise Uzhnu2023MorphemologyDerivatologyIntakeError("specify --check, --mint, or --private-audit")
        print(canonical_json(result))
    except Uzhnu2023MorphemologyDerivatologyIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
