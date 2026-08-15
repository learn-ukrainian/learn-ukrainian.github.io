#!/usr/bin/env python3
"""Mint or audit the text-free LNU 2024 phonetics/phonology candidate."""

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
SCHEMA_PATH = DATA / "contracts/phase3_lnu_2024_phonetics_phonology_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_lnu_2024_phonetics_phonology_candidate_v1.json"
FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"
SCRIPT_PATH = Path(__file__).resolve()

SCHEMA_VERSION = "phase3_lnu_2024_phonetics_phonology_candidate_v1"
STATUS = "ACADEMIC_CANON_CORROBORATION_CANDIDATE_NO_GAP_TRANSITION"
SOURCE_ID = "uni-ukrmova-phonetics-phonology-asiyiv-piletskyi-2024"
TITLE = (
    "Фонетика і фонологія сучасної української літературної мови: "
    "збірник лекційних матеріалів, практичних, тестових та контрольних завдань"
)
AUTHOR = "Асіїв, Любослава; Пілецький, Володимир"
STAGING_RELATIVE = "university_corpus/staging/phase3-6375-lnu-2024-phonetics-phonology"
FREEZE_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"
POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PRIVATE_FILE_MODE, PRIVATE_DIR_MODE = 0o600, 0o700
DRIVE_XATTR_TIMEOUT_SECONDS = 30
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"

ARTIFACTS = {
    "institutional_listing": (
        "institutional-listing.html",
        166878,
        "7b4821f44667cdbe28667bd91123d5272cea2ec05f3afbb3037ab56cc8f72f2c",
        "c9cd5a2879688b548ad73400e698ebf35ff512eaa2313138e2173fec6a7fc266",
    ),
    "rights_access_note": (
        "rights-access-note.json",
        1089,
        "f2fa89f484b678da06d0e41acd1575e7eb84ca360d081c5fc8b1fb051df1cd91",
        "9790bf42185dd70969faedece9538bcc8446c52fa989aafe252afb1aa82a8c2c",
    ),
    "source_response_headers": (
        "source-response-headers.txt",
        551,
        "be90712c2a5f0732872a1ecdf0dd8a2704c9de22629fd2c134b9e9c3b356780a",
        "7b5723aff075089725c2958872a468b0aa94f99faf1360931054990493017bed",
    ),
    "source_pdf": (
        "asiyiv-piletskyi-2024-fonetyka-fonolohiia.pdf",
        7630415,
        "61c4f9bab191c7361eea93ce704eceaee1b8ac66129140f0d07f45f9e82e1a53",
        "b20dc048236af37412afa706b3ca71aee2b582d38910a939f5defa18fadb1e49",
    ),
    "private_audit_receipt": (
        "private-audit-receipt-v1.json",
        1873,
        "6783dff411c2c1400947a44a761a5547348051311e13349063bc38b0c11bd04e",
        "22c34b7e072bd53d68f5c2fac3edd05be8dac693b475a39796197e65d12b8684",
    ),
}
TARGETS = {
    "phonetics": "Modern post-2019 university textbook dedicated to theoretical phonetics and acoustic phonology (e.g. Hryshchenko et al. post-2019 edition).",
    "phonology": "Dedicated university course manual on Ukrainian phonology and morphonology.",
    "orthoepy": "Post-2019 standard Ukrainian orthoepy handbook with updated stress and pronunciation norms.",
    "accentology": "Dedicated modern university manual on Ukrainian accentology and accentual paradigms.",
}


class Lnu2024PhoneticsPhonologyIntakeError(ValueError):
    """A frozen source identity, custody condition, or gate drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lnu2024PhoneticsPhonologyIntakeError(message)


TRAINING_AUTHORIZATION_FIELDS = (
    "private_training_preparation",
    "general_downstream_dataset_license_established",
    "unrestricted_training_export",
)


def _require_no_training_authorization(rights: Mapping[str, Any]) -> None:
    for field in TRAINING_AUTHORIZATION_FIELDS:
        require(rights[field] is False, f"training authorization must stay false: {field}")


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
        raise Lnu2024PhoneticsPhonologyIntakeError("cannot read private artifact") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Lnu2024PhoneticsPhonologyIntakeError(f"cannot read {label}") from exc
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
        raise Lnu2024PhoneticsPhonologyIntakeError("missing private stage") from exc
    require(stat.S_ISDIR(mode) and not path.is_symlink(), "private stage must be a directory")
    require(stat.S_IMODE(mode) == PRIVATE_DIR_MODE, "private stage must be mode 0700")
    require(not _inside_git_checkout(path), "private stage cannot live inside Git")


def _private_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Lnu2024PhoneticsPhonologyIntakeError(f"missing {label}") from exc
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
            timeout=DRIVE_XATTR_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise Lnu2024PhoneticsPhonologyIntakeError("artifact lacks Google Drive provider identity") from exc
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
        require(topics.get(area, {}).get("status") == "partial", f"university {area} status drift")
        require(
            topics.get(area, {}).get("qualified_source_needed") == need,
            f"university {area} qualified-source need drift",
        )
    require(topics.get("orthography", {}).get("status") == "sufficient", "university orthography status drift")
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
    rights = {
        "metadata_standard_license_present": False,
        "repository_deposit_terms": (
            "public institutional website copy; no explicit standard license; "
            "downstream dataset reuse not established; retain only for private audit and later rights review"
        ),
        "general_downstream_dataset_license_established": False,
        "private_acquisition": True,
        "private_backup": True,
        "private_extraction": True,
        "private_training_preparation": False,
        "public_reconstructable_full_text_export": False,
        "unrestricted_training_export": False,
        "public_text_free_metadata_hash_nonreconstructable_evidence": True,
        "final_release_review_required": True,
        "takedown_adapt_on_substantiated_complaint": True,
    }
    _require_no_training_authorization(rights)
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
            "institution": "Львівський національний університет імені Івана Франка",
            "faculty_department": (
                "Faculty of Philology, Department of Ukrainian Language named after Professor Ivan Kovalyk"
            ),
            "approval": (
                "institutional course publication on LNU Philology faculty website "
                "(secondary-education teacher-training track)"
            ),
            "year": 2024,
            "printed_pages": 399,
            "pdf_page_objects": 399,
            "genre": "native_university_zbirnyk_lektsij_praktykum_testiv",
            "course_page_url": (
                "https://philology.lnu.edu.ua/course/suchasna-ukrajinska-literaturna-mova-fonetyka-i-fonolohiya-osvita/"
                "fonetyka_serednia-osvita-1"
            ),
            "pdf_url": "https://philology.lnu.edu.ua/wp-content/uploads/2016/10/FONETYKA_Serednia-osvita-1.pdf",
            "institutional_listing_url": "https://philology.lnu.edu.ua/department/ukrajinskoji-movy",
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
            "pdf_pages": 399,
            "text_bearing_pages": 399,
            "extracted_characters": 739288,
            "encrypted": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
            "visual_qa_passed_pdf_pages": [1, 2, 4, 8, 16, 32, 64, 128, 192, 256, 320, 384, 399],
        },
        "signals": {
            "practical_session_markers": 40,
            "exercise_markers": 216,
            "acoustic": 77,
            "experimental": 4,
            "spectrograph": 0,
            "formant": 1,
            "oscillograph": 0,
            "articulation": 115,
            "orthoepy": 20,
            "stress": 144,
            "intonation": 20,
            "orthography": 40,
        },
        "content_fitness": {
            "primary_role": "modern_ukrainian_practical_university_handbook",
            "target_cells": cells,
            "secondary_observation": {
                "area": "orthography",
                "frozen_status": "sufficient",
                "role": "secondary_corroboration_only",
            },
            "descriptive_topics": [
                {"topic": "morphonology", "role": "diagnostic_signal_only_not_a_primary_cell"},
            ],
            "broad_topics": [
                "phonetics",
                "phonology",
                "vowels_consonants",
                "sound_changes",
                "synchronic_historical_alternations",
                "accentology",
                "syllable_theory",
                "intonation",
                "orthoepy_literary_pronunciation",
                "graphics",
                "orthography",
                "lecture_materials",
                "practical_tasks",
                "tests",
                "control_tasks",
            ],
            "limitations": (
                "institutional lecture/practice/test collection for secondary-education teacher-training track; "
                "practical breadth over deep acoustic instrumentation; no sustained spectrographic, formant, "
                "or oscillographic laboratory treatment"
            ),
            "topic_gaps_closed": [],
            "topic_gaps_narrowed_claimed": [],
        },
        "rights": rights,
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
            "Current institutional course-material corroboration does not close or narrow any frozen gap.",
            "All four frozen target cells remain partial; the qualified-source needs remain open.",
            "Morphonology marker counts are descriptive only, not primary gap-transition cells.",
            "No database ingest, semantic gold, author/eval membership, source-universe freeze, Phase 3 completion, or Phase 4 authorization.",
        ],
    }


def mint_receipt() -> dict[str, Any]:
    body = build_receipt_body()
    return validate_receipt({**body, "receipt_sha256": sha256_bytes(canonical_bytes(body))})


def validate_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    schema = _read_json(SCHEMA_PATH, "LNU candidate schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "receipt"
        raise Lnu2024PhoneticsPhonologyIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
    require(receipt["receipt_sha256"] == receipt_sha256(receipt), "receipt self-hash drift")
    _require_no_training_authorization(receipt["rights"])
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
        raise Lnu2024PhoneticsPhonologyIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    except OSError as exc:
        raise Lnu2024PhoneticsPhonologyIntakeError("cannot safely read existing public receipt") from exc
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
            receipt = validate_receipt(_read_json(args.check, "LNU candidate receipt"))
            result = {"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]}
        elif args.private_audit:
            require(not args.mint, "private-audit mode is exclusive")
            result = private_audit(args.staging_root)
        elif args.mint:
            receipt = mint_receipt()
            write_public_receipt(args.write, receipt)
            result = {"ok": True, "receipt_sha256": receipt["receipt_sha256"], "status": receipt["status"]}
        else:
            raise Lnu2024PhoneticsPhonologyIntakeError("specify --check, --mint, or --private-audit")
        print(canonical_json(result))
    except Lnu2024PhoneticsPhonologyIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
