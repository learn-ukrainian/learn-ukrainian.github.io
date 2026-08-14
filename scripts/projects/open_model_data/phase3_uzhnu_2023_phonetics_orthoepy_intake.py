#!/usr/bin/env python3
"""Mint or audit the text-free UzhNU 2023 phonetics/orthoepy candidate."""

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
SCHEMA_PATH = DATA / "contracts/phase3_uzhnu_2023_phonetics_orthoepy_candidate_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT_PATH = DATA / "admission/phase3_uzhnu_2023_phonetics_orthoepy_candidate_v1.json"
FREEZE_PATH = DATA / "admission/phase3_university_content_audit_freeze_v1.json"
POLICY_PATH = DATA / "admission/phase3_complete_source_policy_v4.json"
SCRIPT_PATH = Path(__file__).resolve()

SCHEMA_VERSION = "phase3_uzhnu_2023_phonetics_orthoepy_candidate_v1"
STATUS = "ACADEMIC_CANON_CORROBORATION_CANDIDATE_NO_GAP_TRANSITION"
SOURCE_ID = "uni-ukrmova-applied-phonetics-phonology-orthoepy-shkurko-2023"
TITLE = "Прикладне українське мовознавство. Фонетика. Фонологія. Орфоепія"
AUTHOR = "Шкурко, Галина Вячеславівна"
STAGING_RELATIVE = "university_corpus/staging/phase3-6375-uzhnu-2023-phonetics-orthoepy"
FREEZE_SHA256 = "d48db94a4576ffa13285d7678a774247ef6db484f85f866aa4a02f6fb33f5c0b"
POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"
V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PRIVATE_FILE_MODE, PRIVATE_DIR_MODE = 0o600, 0o700
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"

ARTIFACTS = {
    "item_metadata": (
        "item-metadata.json",
        6329,
        "d4e5bdd9df629a103ad13326c1391f45997eba9459d89f335adfd336e7ac4c8f",
        "508e47f1679d52959eb92a2c171c74e54920d72864f7c0248c820328535a651e",
    ),
    "repository_license": (
        "repository-license.txt",
        6479,
        "525cca59abbf86f988d32c88deea3b73bc496b316a23e142f527073047d6547e",
        "d1e4a569d913e276e7155cc75f43296e662e78579df90738b552bd9442f687d0",
    ),
    "source_pdf": (
        "uzhnu-2023-applied-ukrainian-linguistics-phonetics-phonology-orthoepy.pdf",
        1513330,
        "bb73bcc7f6092340b514a8f2645ebe49acac347bdbb1c20671f1ccddf2349179",
        "122f74af71eaf0fd790c376caa2a5d1eef0b7d6c926f8c6fa6343ce42b57dcfe",
    ),
    "private_audit_receipt": (
        "private-audit-receipt-v1.json",
        3537,
        "0f31807d11cb1ed30d66266ff9d4e75818dd28a69168c3321112f5d813dc3321",
        "bb5e61394651ead27fd360fbeb7330e215078a74f1e18a2ae7b8c05ac5006cd0",
    ),
}
TARGETS = {
    "phonetics": "Modern post-2019 university textbook dedicated to theoretical phonetics and acoustic phonology (e.g. Hryshchenko et al. post-2019 edition).",
    "phonology": "Dedicated university course manual on Ukrainian phonology and morphonology.",
    "orthoepy": "Post-2019 standard Ukrainian orthoepy handbook with updated stress and pronunciation norms.",
    "accentology": "Dedicated modern university manual on Ukrainian accentology and accentual paradigms.",
}


class Uzhnu2023PhoneticsOrthoepyIntakeError(ValueError):
    """A frozen source identity, custody condition, or gate drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Uzhnu2023PhoneticsOrthoepyIntakeError(message)


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
        raise Uzhnu2023PhoneticsOrthoepyIntakeError("cannot read private artifact") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Uzhnu2023PhoneticsOrthoepyIntakeError(f"cannot read {label}") from exc
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
        raise Uzhnu2023PhoneticsOrthoepyIntakeError("missing private stage") from exc
    require(stat.S_ISDIR(mode) and not path.is_symlink(), "private stage must be a directory")
    require(stat.S_IMODE(mode) == PRIVATE_DIR_MODE, "private stage must be mode 0700")
    require(not _inside_git_checkout(path), "private stage cannot live inside Git")


def _private_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Uzhnu2023PhoneticsOrthoepyIntakeError(f"missing {label}") from exc
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
        raise Uzhnu2023PhoneticsOrthoepyIntakeError("artifact lacks Google Drive provider identity") from exc
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
            "approval": "faculty academic council protocol no. 8 dated 15 June 2023",
            "year": 2023,
            "printed_pages": 53,
            "pdf_page_objects": 54,
            "genre": "native_university_navchalno-metodychnyi_posibnyk",
            "item_uuid": "427a4176-23d8-4253-9498-8b1357f6c95b",
            "handle_url": "https://dspace.uzhnu.edu.ua/jspui/handle/lib/62683",
            "item_api_url": "https://dspace.uzhnu.edu.ua/server/api/core/items/427a4176-23d8-4253-9498-8b1357f6c95b",
            "pdf_bitstream_uuid": "b8b3093e-3c06-47e1-8991-747e513adb2b",
            "license_bitstream_uuid": "29b04566-b6f2-48e9-9d49-7aa4baf14538",
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
            "pdf_pages": 54,
            "text_bearing_pages": 54,
            "extracted_characters": 97903,
            "encrypted": False,
            "ocr_used": False,
            "repairs_applied": False,
            "source_text_retained_in_public_receipt": False,
            "visual_qa_passed_pdf_pages": [1, 2, 4, 8, 16, 28, 40, 52],
        },
        "signals": {
            "practical_session_markers": 30,
            "exercise_markers": 92,
            "acoustic": 5,
            "experimental": 2,
            "spectrograph": 0,
            "formant": 0,
            "oscillograph": 0,
            "articulation": 5,
            "orthoepy": 75,
            "stress": 43,
            "intonation": 6,
            "orthography": 30,
        },
        "content_fitness": {
            "primary_role": "modern_ukrainian_practical_university_handbook",
            "target_cells": cells,
            "secondary_observation": {
                "area": "orthography",
                "frozen_status": "sufficient",
                "role": "secondary_corroboration_only",
            },
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
            ],
            "limitations": "practical handbook, not deep acoustic theory; no spectrographic, formant, or oscillographic treatment",
            "topic_gaps_closed": [],
            "topic_gaps_narrowed_claimed": [],
        },
        "rights": {
            "metadata_standard_license_present": False,
            "repository_deposit_terms": "author retains copyright; grants UzhNU non-exclusive repository, preservation, open-access, noncommercial-copying, and distribution rights",
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
            "All four frozen target cells remain partial; the qualified-source needs remain open.",
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
        raise Uzhnu2023PhoneticsOrthoepyIntakeError(f"receipt schema violation at {location}: {errors[0].message}")
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
        raise Uzhnu2023PhoneticsOrthoepyIntakeError("cannot safely read existing public receipt") from exc
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "public receipt must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    except OSError as exc:
        raise Uzhnu2023PhoneticsOrthoepyIntakeError("cannot safely read existing public receipt") from exc
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
            raise Uzhnu2023PhoneticsOrthoepyIntakeError("specify --check, --mint, or --private-audit")
        print(canonical_json(result))
    except Uzhnu2023PhoneticsOrthoepyIntakeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
