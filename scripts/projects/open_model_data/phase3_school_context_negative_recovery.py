#!/usr/bin/env python3
"""Seal the negative recovery for Phase 3 school evaluation context.

Pinned private materialization cannot supply complete parent-section context for
all 8,005 held-out school identities, the freeze ``sources.db`` pin is absent,
and sealed-canonical reanchor of the null-parent cohort fails.  This adapter
re-proves the text-free parent-section census from the pinned custody members
and publishes a public receipt that keeps school rows on
``frozen_source_unit_text`` with ``complete_sentence_context=false``.

It does not emit private source text, labels, provider calls, or Phase 4 gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_context_manifest as eval_manifest

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_school_context_negative_recovery_receipt_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT = DATA / "inventory/phase3_school_context_negative_recovery_receipt_v1.json"
EVAL_CONTEXT_RECEIPT = DATA / "inventory/phase3_evaluation_context_manifest_receipt_v1.json"
SCHOOL_LEDGER = DATA / "evidence/source_universe_v1/school_textbooks.units.jsonl"
SOURCE_UNIVERSE_RECEIPT = DATA / "evidence/source_universe_v1/source-universe-freeze-receipt.json"

SCHEMA_VERSION = "phase3_school_context_negative_recovery_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_school_context_negative_recovery_v1"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
# Git-tracked text-free receipts check out as 0644; new writes stay owner-only 0600.
TRACKED_PUBLIC_FILE_MODE = 0o644
ACCEPTED_PUBLIC_RECEIPT_MODES = frozenset({PRIVATE_FILE_MODE, TRACKED_PUBLIC_FILE_MODE})

PINNED_SOURCE_UNITS_JSONL_SHA256 = eval_manifest.PINNED_SOURCE_UNITS_JSONL_SHA256
PINNED_PARTITION_SHA256 = eval_manifest.PINNED_PARTITION_SHA256
PINNED_CUSTODY_TARBALL_SHA256 = eval_manifest.PINNED_CUSTODY_TARBALL_SHA256
PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256 = eval_manifest.PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256
PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256 = "f01d8efd0a1279d7cf4b742ad6909de4a7d2a3866195b7f7e1b56d8e1e2598d1"
PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256 = "292a42ee85a3413859d2eb6063484ff55756ad026fbcd6fab8d83bde4d9345fb"
PINNED_SCHOOL_LEDGER_SHA256 = "fd39efa11d5689dfcc5baaaa1a6a97eb8f00db36780ee4ebbf59b73e94c9065e"
PINNED_FREEZE_DATABASE_SHA256 = "eb5e0c3745020def62d5d5cdfb5190bc8a91d6c3dc04b05f5f98f259b3696c4d"

TARBALL_MEMBERS = {
    "source_jsonl": "batch_state/phase3-private/v21-cycle001/source-materialization/source_units_v1.jsonl",
    "partition": "batch_state/phase3-private/v21-cycle001/evaluation-partition/partition_manifest_v1.jsonl",
}

V2_SOURCE_UNITS = 67_041
V2_EVALUATION_IDENTITIES = 9_392
SCHOOL_UNIVERSE = 54_979
SCHOOL_HELDOUT = 8_005
PARENT_NULL_HELDOUT = 4_479
PARENT_COMPLETE_HELDOUT = 3_526
SCHOOL_NULL_PARENT_ROWS = 31_005
NON_NULL_PARENT_GROUPS = 5_510
FREEZE_SECTION_GRAIN = 7_250

CANONICAL_REANCHOR = {
    "denominator": 4_479,
    "missing_source_jsonl": 710,
    "exact_unique": 5,
    "exact_ambiguous": 0,
    "unique_containment": 3,
    "ambiguous_containment": 1,
    "no_match": 3_760,
    "parse_or_input_errors": 0,
}
QUARANTINE_REANCHOR = {
    "exact_unique": 4_477,
    "exact_ambiguous": 2,
    "locateable_after_chunk_id_tiebreak": 4_479,
    "multi_chunk_section": 2_290,
    "singleton_section": 2_189,
    "custody_bound_files": 0,
    "custody_bound_rows": 0,
}
BLOCKER_CODES = [
    "freeze_database_absent",
    "parent_section_id_null_on_heldout_majority",
    "public_school_ledger_lacks_parent_boundaries",
    "canonical_drive_jsonl_not_freeze_text_identical",
    "quarantine_extracts_not_sealed_canonical_custody",
    "sentence_complete_authority_absent_for_school",
]


class SchoolContextNegativeRecoveryError(ValueError):
    """School complete-context recovery cannot be sealed or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SchoolContextNegativeRecoveryError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SchoolContextNegativeRecoveryError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_sha256(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    return sha256_bytes(canonical_bytes(body))


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(_absolute(path).anchor)
    for component in _absolute(path).parts[1:]:
        current /= component
        if not current.exists() and not current.is_symlink():
            return
        require(not current.is_symlink(), f"symlink forbidden for {label}")


def _regular_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        state = path.lstat()
    except OSError as exc:
        raise SchoolContextNegativeRecoveryError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")


def _regular_public(path: Path, label: str) -> None:
    """Accept only explicit safe modes for an existing public receipt.

    New receipts are created owner-only (0600). A normal git checkout of the
    committed text-free receipt is 0644. Any other mode fails closed.
    """
    _regular_file(path, label)
    mode = stat.S_IMODE(path.lstat().st_mode)
    require(
        mode in ACCEPTED_PUBLIC_RECEIPT_MODES,
        f"{label} permissions must be 0600 or tracked 0644",
    )


def _strict_json_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchoolContextNegativeRecoveryError(f"invalid strict JSON: {label}") from exc
    require(isinstance(value, dict), f"{label} top-level type drift")
    return value


def _iter_jsonl(path: Path, label: str) -> Iterator[dict[str, Any]]:
    _regular_file(path, label)
    with path.open("rb") as handle:
        for index, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = _strict_json_object(line, f"{label} line {index}")
            yield row


def _atomic_write(path: Path, payload: bytes) -> None:
    """Atomically write *payload* with owner-only permissions (mode 0600).

    Mode is fixed at every fchmod/chmod site (no caller-controlled argument) so
    static analysis can prove the permission policy without tracking a variable.
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


def _write_public_receipt(path: Path, payload: bytes) -> None:
    """Idempotent public receipt write via the fixed private atomic writer.

    Creation always uses owner-only 0600. Existing files may be 0600 or the
    normal git-tracked 0644 checkout mode; changed bytes are refused.
    """
    _reject_symlink_components(path, "public receipt")
    if path.exists():
        _regular_public(path, "public receipt")
        require(path.read_bytes() == payload, "refusing to overwrite changed public receipt")
        return
    _atomic_write(path, payload)


def _canonical_temp_root(prefix: str) -> Path:
    """Create a private temp directory on a symlink-free resolved path.

    macOS often exposes ``TMPDIR`` under ``/var`` which is a symlink to
    ``/private/var``. The strict symlink guard must keep rejecting that alias,
    so production staging always uses the realpath canonical root with mode 0700.
    """
    created = Path(tempfile.mkdtemp(prefix=prefix, dir=None))
    resolved = Path(os.path.realpath(created))
    if resolved != created:
        require(resolved.exists(), "resolved temp root missing after mkdtemp")
    os.chmod(resolved, PRIVATE_DIR_MODE)
    _reject_symlink_components(resolved, "temp root")
    return resolved


def _validate_public_bindings() -> None:
    require(SCHEMA_PATH.is_file(), "missing negative-recovery schema")
    require(EVAL_CONTEXT_RECEIPT.is_file(), "missing evaluation context receipt")
    require(SCHOOL_LEDGER.is_file(), "missing public school ledger")
    require(SOURCE_UNIVERSE_RECEIPT.is_file(), "missing source universe receipt")
    require(
        sha256_file(EVAL_CONTEXT_RECEIPT) == PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256,
        "evaluation context receipt file drift",
    )
    eval_receipt = _strict_json_object(EVAL_CONTEXT_RECEIPT.read_bytes(), "evaluation context receipt")
    require(
        receipt_sha256(eval_receipt) == PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256,
        "evaluation context receipt body drift",
    )
    require(
        eval_receipt.get("family_counts", {}).get("school_textbooks") == SCHOOL_HELDOUT,
        "evaluation context school held-out drift",
    )
    require(
        eval_receipt.get("context_accounting", {}).get("frozen_source_unit_text") == 8_483,
        "evaluation context frozen-text accounting drift",
    )
    require(
        sha256_file(SCHOOL_LEDGER) == PINNED_SCHOOL_LEDGER_SHA256,
        "public school ledger hash drift",
    )
    require(
        sha256_file(SOURCE_UNIVERSE_RECEIPT) == PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
        "source universe receipt hash drift",
    )


def _assert_public_ledger_lacks_parent_boundaries() -> None:
    forbidden = {"parent_section_id", "section_id", "section_title", "page"}
    for index, row in enumerate(_iter_jsonl(SCHOOL_LEDGER, "public school ledger"), start=1):
        require(row.get("family_id") == "school_textbooks", f"public ledger family drift at {index}")
        locator = row.get("locator")
        require(isinstance(locator, dict), f"public ledger locator drift at {index}")
        require(locator.get("kind") == "sqlite_row", f"public ledger locator kind drift at {index}")
        require(locator.get("table") == "textbooks", f"public ledger table drift at {index}")
        overlap = forbidden.intersection(locator)
        require(not overlap, f"public ledger unexpectedly exposes parent boundaries at {index}")
        require("parent_section_id" not in row, f"public ledger row exposes parent_section_id at {index}")
        if index >= 3:
            # Shape is uniform; three rows are enough to fail closed on a drifted grain.
            break


def _load_heldout_school_ids(partition_path: Path) -> dict[str, str]:
    heldout: dict[str, str] = {}
    for row in _iter_jsonl(partition_path, "partition manifest"):
        if row.get("family_id") != "school_textbooks":
            continue
        unit_id = row.get("unit_id")
        unit_sha = row.get("unit_sha256")
        require(isinstance(unit_id, str) and isinstance(unit_sha, str), "partition school row identity drift")
        require(unit_id not in heldout, f"duplicate held-out school unit_id: {unit_id}")
        heldout[unit_id] = unit_sha
    require(len(heldout) == SCHOOL_HELDOUT, "held-out school count drift")
    return heldout


def _metadata_only_record(source_record: Mapping[str, Any]) -> dict[str, Any]:
    """Return only identity/order fields; never retain source text."""
    parent = source_record.get("parent_section_id")
    require(parent is None or isinstance(parent, (str, int)), "parent_section_id type drift")
    source_file = source_record.get("source_file")
    require(isinstance(source_file, str) and source_file, "source_file missing")
    record_id = source_record.get("id")
    chunk_id = source_record.get("chunk_id")
    require(record_id is not None, "source_record.id missing")
    require(chunk_id is not None, "source_record.chunk_id missing")
    return {
        "parent_section_id": parent,
        "source_file": source_file,
        "id": record_id,
        "chunk_id": chunk_id,
    }


def compute_parent_section_census(
    *,
    source_jsonl: Path,
    partition_path: Path,
) -> dict[str, Any]:
    require(sha256_file(source_jsonl) == PINNED_SOURCE_UNITS_JSONL_SHA256, "source units hash drift")
    require(sha256_file(partition_path) == PINNED_PARTITION_SHA256, "partition hash drift")
    heldout = _load_heldout_school_ids(partition_path)

    school_rows = 0
    school_null_parent = 0
    heldout_seen: set[str] = set()
    heldout_null = 0
    unit_sha_mismatches = 0
    groups: dict[tuple[str, Any], list[tuple[Any, Any, str]]] = defaultdict(list)

    for row in _iter_jsonl(source_jsonl, "source units"):
        if row.get("family_id") != "school_textbooks":
            continue
        school_rows += 1
        unit_id = row.get("unit_id")
        unit_sha = row.get("unit_sha256")
        require(isinstance(unit_id, str) and isinstance(unit_sha, str), "school unit identity drift")
        source_record = row.get("source_record")
        require(isinstance(source_record, Mapping), "school source_record missing")
        meta = _metadata_only_record(source_record)
        if meta["parent_section_id"] is None:
            school_null_parent += 1
        else:
            groups[(meta["source_file"], meta["parent_section_id"])].append((meta["id"], meta["chunk_id"], unit_id))
        if unit_id in heldout:
            require(unit_id not in heldout_seen, f"duplicate school held-out materialization: {unit_id}")
            heldout_seen.add(unit_id)
            if heldout[unit_id] != unit_sha:
                unit_sha_mismatches += 1
            if meta["parent_section_id"] is None:
                heldout_null += 1

    require(school_rows == SCHOOL_UNIVERSE, "school universe count drift")
    require(school_null_parent == SCHOOL_NULL_PARENT_ROWS, "school null-parent universe drift")
    require(len(heldout_seen) == SCHOOL_HELDOUT, "held-out school materialization coverage drift")
    require(unit_sha_mismatches == 0, "held-out unit_sha256 mismatches")
    require(heldout_null == PARENT_NULL_HELDOUT, "held-out null parent_section_id drift")

    complete_heldout = 0
    for members in groups.values():
        ids = [item[0] for item in members]
        chunk_ids = [item[1] for item in members]
        require(len(ids) == len(set(ids)), "non-unique source_record.id inside parent section")
        require(len(chunk_ids) == len(set(chunk_ids)), "non-unique chunk_id inside parent section")
        ordered = sorted(members, key=lambda item: item[0])
        for _record_id, _chunk_id, unit_id in ordered:
            if unit_id in heldout:
                complete_heldout += 1

    require(len(groups) == NON_NULL_PARENT_GROUPS, "non-null parent section group count drift")
    require(complete_heldout == PARENT_COMPLETE_HELDOUT, "complete parent-section held-out drift")
    require(
        heldout_null + complete_heldout == SCHOOL_HELDOUT,
        "held-out parent-section partition does not cover 8005",
    )
    return {
        "heldout_with_null_parent_section_id": heldout_null,
        "heldout_in_complete_ordered_parent_section": complete_heldout,
        "school_rows_with_null_parent_section_id": school_null_parent,
        "non_null_parent_section_groups": len(groups),
        "freeze_section_grain_target": FREEZE_SECTION_GRAIN,
    }


def _assert_reanchor_invariants() -> None:
    canonical_sum = sum(
        CANONICAL_REANCHOR[key]
        for key in (
            "missing_source_jsonl",
            "exact_unique",
            "exact_ambiguous",
            "unique_containment",
            "ambiguous_containment",
            "no_match",
            "parse_or_input_errors",
        )
    )
    require(canonical_sum == CANONICAL_REANCHOR["denominator"] == PARENT_NULL_HELDOUT, "canonical reanchor sum drift")
    require(
        QUARANTINE_REANCHOR["exact_unique"] + QUARANTINE_REANCHOR["exact_ambiguous"]
        == QUARANTINE_REANCHOR["locateable_after_chunk_id_tiebreak"]
        == PARENT_NULL_HELDOUT,
        "quarantine reanchor sum drift",
    )
    require(
        QUARANTINE_REANCHOR["multi_chunk_section"] + QUARANTINE_REANCHOR["singleton_section"] == PARENT_NULL_HELDOUT,
        "quarantine section grain sum drift",
    )
    require(QUARANTINE_REANCHOR["custody_bound_files"] == 0, "quarantine custody bind drift")
    require(QUARANTINE_REANCHOR["custody_bound_rows"] == 0, "quarantine custody row bind drift")


def _assert_candidate_database_not_freeze(path: Path | None) -> None:
    if path is None:
        return
    _regular_file(path, "candidate database")
    digest = sha256_file(path)
    require(digest != PINNED_FREEZE_DATABASE_SHA256, "candidate database unexpectedly matches freeze pin")


def build_receipt(
    *,
    source_jsonl: Path,
    partition_path: Path,
    started_at: str,
    completed_at: str,
    candidate_database: Path | None = None,
) -> dict[str, Any]:
    _validate_public_bindings()
    _assert_public_ledger_lacks_parent_boundaries()
    _assert_reanchor_invariants()
    _assert_candidate_database_not_freeze(candidate_database)
    census = compute_parent_section_census(source_jsonl=source_jsonl, partition_path=partition_path)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "started_at": started_at,
        "completed_at": completed_at,
        "bindings": {
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "receipt_schema_sha256": sha256_file(SCHEMA_PATH),
            "source_units_jsonl_sha256": PINNED_SOURCE_UNITS_JSONL_SHA256,
            "partition_manifest_sha256": PINNED_PARTITION_SHA256,
            "custody_tarball_sha256": PINNED_CUSTODY_TARBALL_SHA256,
            "evaluation_context_manifest_receipt_body_sha256": PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256,
            "evaluation_context_manifest_receipt_file_sha256": PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256,
            "source_universe_receipt_sha256": PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
            "school_textbooks_units_jsonl_sha256": PINNED_SCHOOL_LEDGER_SHA256,
        },
        "denominators": {
            "v2_source_units": V2_SOURCE_UNITS,
            "v2_evaluation_identities": V2_EVALUATION_IDENTITIES,
            "school_universe_units": SCHOOL_UNIVERSE,
        },
        "disposition": "school_complete_parent_or_sentence_context_not_recoverable",
        "school_heldout": SCHOOL_HELDOUT,
        "parent_section_census": census,
        "canonical_reanchor_accounting": dict(CANONICAL_REANCHOR),
        "quarantine_reanchor_accounting": dict(QUARANTINE_REANCHOR),
        "freeze_database": {
            "pinned_sha256": PINNED_FREEZE_DATABASE_SHA256,
            "status": "absent",
        },
        "context_retained": {
            "context_kind": "frozen_source_unit_text",
            "complete_sentence_context": False,
            "school_heldout_rows": SCHOOL_HELDOUT,
            "upgrade_claimed": False,
        },
        "blocker_codes": list(BLOCKER_CODES),
        "labels_present": False,
        "gates": {
            "school_negative_recovery_sealed": True,
            "school_complete_context_ready": False,
            "semantic_labels_present": False,
            "source_authoring_blocked": True,
            "complete_evaluation_package_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt["receipt_sha256"] = receipt_sha256(receipt)
    Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).validate(receipt)
    return receipt


def validate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).validate(receipt)
    require(receipt_sha256(receipt) == receipt["receipt_sha256"], "receipt self-hash drift")
    require(receipt.get("text_free") is True, "receipt must be text-free")
    require(receipt.get("provider_calls") is False, "provider_calls must be false")
    require(receipt.get("labels_present") is False, "labels_present must be false")
    require(receipt["gates"]["school_complete_context_ready"] is False, "school complete context overclaim")
    require(receipt["gates"]["phase3_complete"] is False, "phase3 completion overclaim")
    require(receipt["gates"]["phase4_blocked"] is True, "phase4 must remain blocked")
    # Fail closed on stale/tampered *current* public binding inputs, not only pinned constants.
    _validate_public_bindings()
    bindings = receipt["bindings"]
    require(
        bindings["implementation_sha256"] == sha256_file(SCRIPT_PATH),
        "implementation binding drift",
    )
    require(
        bindings["receipt_schema_sha256"] == sha256_file(SCHEMA_PATH),
        "schema binding drift",
    )
    require(
        bindings["source_units_jsonl_sha256"] == PINNED_SOURCE_UNITS_JSONL_SHA256,
        "source units binding drift",
    )
    require(
        bindings["partition_manifest_sha256"] == PINNED_PARTITION_SHA256,
        "partition binding drift",
    )
    require(
        bindings["custody_tarball_sha256"] == PINNED_CUSTODY_TARBALL_SHA256,
        "custody tarball binding drift",
    )
    require(
        bindings["evaluation_context_manifest_receipt_body_sha256"] == PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256,
        "evaluation context body binding drift",
    )
    require(
        bindings["evaluation_context_manifest_receipt_file_sha256"] == PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256,
        "evaluation context file binding drift",
    )
    require(
        bindings["source_universe_receipt_sha256"] == PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
        "source universe binding drift",
    )
    require(
        bindings["school_textbooks_units_jsonl_sha256"] == PINNED_SCHOOL_LEDGER_SHA256,
        "school ledger binding drift",
    )
    return dict(receipt)


def materialize(
    *,
    source_jsonl: Path,
    partition_path: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
    candidate_database: Path | None = None,
) -> dict[str, Any]:
    finished = completed_at or utc_now()
    receipt = build_receipt(
        source_jsonl=source_jsonl,
        partition_path=partition_path,
        started_at=started_at,
        completed_at=finished,
        candidate_database=candidate_database,
    )
    _write_public_receipt(public_receipt_path, canonical_bytes(receipt))
    return validate_receipt(_strict_json_object(public_receipt_path.read_bytes(), "public receipt"))


def verify_existing(
    *,
    source_jsonl: Path,
    partition_path: Path,
    public_receipt_path: Path,
    candidate_database: Path | None = None,
) -> dict[str, Any]:
    receipt = validate_receipt(_strict_json_object(public_receipt_path.read_bytes(), "public receipt"))
    _regular_public(public_receipt_path, "public receipt")
    rebuilt = build_receipt(
        source_jsonl=source_jsonl,
        partition_path=partition_path,
        started_at=receipt["started_at"],
        completed_at=receipt["completed_at"],
        candidate_database=candidate_database,
    )
    # Fail closed on current implementation/schema bindings via validate_receipt;
    # then compare sealed findings and remaining pinned bindings.
    for key in (
        "disposition",
        "school_heldout",
        "parent_section_census",
        "canonical_reanchor_accounting",
        "quarantine_reanchor_accounting",
        "freeze_database",
        "context_retained",
        "blocker_codes",
        "labels_present",
        "gates",
        "denominators",
    ):
        require(receipt[key] == rebuilt[key], f"public receipt drift on {key}")
    for key in (
        "implementation_sha256",
        "receipt_schema_sha256",
        "source_units_jsonl_sha256",
        "partition_manifest_sha256",
        "custody_tarball_sha256",
        "evaluation_context_manifest_receipt_body_sha256",
        "evaluation_context_manifest_receipt_file_sha256",
        "source_universe_receipt_sha256",
        "school_textbooks_units_jsonl_sha256",
    ):
        require(receipt["bindings"][key] == rebuilt["bindings"][key], f"binding drift on {key}")
    return receipt


def _extract_tarball_members(tarball: Path, destination: Path) -> dict[str, Path]:
    require(tarball.is_file() and not tarball.is_symlink(), "custody tarball must be a regular file")
    require(sha256_file(tarball) == PINNED_CUSTODY_TARBALL_SHA256, "custody tarball hash drift")
    destination.mkdir(parents=True, exist_ok=True)
    os.chmod(destination, PRIVATE_DIR_MODE)
    extracted: dict[str, Path] = {}
    with tarfile.open(tarball, mode="r:gz") as archive:
        members = {member.name: member for member in archive.getmembers() if member.isfile()}
        for key, member_name in TARBALL_MEMBERS.items():
            member = members.get(member_name)
            require(member is not None, f"missing tarball member: {member_name}")
            require(not member.issym() and not member.islnk(), f"unsafe tarball member: {member_name}")
            stream = archive.extractfile(member)
            require(stream is not None, f"cannot extract tarball member: {member_name}")
            payload = stream.read()
            target = destination / Path(member_name).name
            _atomic_write(target, payload)
            extracted[key] = target
    return extracted


def production_run(
    *,
    custody_tarball: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
    candidate_database: Path | None = None,
) -> dict[str, Any]:
    temp_root = _canonical_temp_root("phase3-school-negrec-")
    try:
        extracted = _extract_tarball_members(custody_tarball, temp_root)
        return materialize(
            source_jsonl=extracted["source_jsonl"],
            partition_path=extracted["partition"],
            public_receipt_path=public_receipt_path,
            started_at=started_at,
            completed_at=completed_at,
            candidate_database=candidate_database,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build the public negative-recovery receipt")
    build.add_argument("--source-jsonl", type=Path, required=True)
    build.add_argument("--partition", type=Path, required=True)
    build.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    build.add_argument("--candidate-database", type=Path)
    build.add_argument("--started-at")
    build.add_argument("--completed-at")

    verify = subparsers.add_parser("verify", help="re-prove census and verify an existing receipt")
    verify.add_argument("--source-jsonl", type=Path, required=True)
    verify.add_argument("--partition", type=Path, required=True)
    verify.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    verify.add_argument("--candidate-database", type=Path)

    production = subparsers.add_parser("production", help="extract custody inputs and publish the receipt")
    production.add_argument("--custody-tarball", type=Path, required=True)
    production.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    production.add_argument("--candidate-database", type=Path)
    production.add_argument("--started-at")
    production.add_argument("--completed-at")

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            receipt = materialize(
                source_jsonl=args.source_jsonl,
                partition_path=args.partition,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
                candidate_database=args.candidate_database,
            )
        elif args.command == "verify":
            receipt = verify_existing(
                source_jsonl=args.source_jsonl,
                partition_path=args.partition,
                public_receipt_path=args.public_receipt,
                candidate_database=args.candidate_database,
            )
        else:
            receipt = production_run(
                custody_tarball=args.custody_tarball,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
                candidate_database=args.candidate_database,
            )
    except (OSError, SchoolContextNegativeRecoveryError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
