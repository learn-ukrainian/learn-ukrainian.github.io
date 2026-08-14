#!/usr/bin/env python3
"""Materialize complete ordered parent-section context for school held-outs.

Pinned custody (#6782) classifies 3,526 of 8,005 held-out school identities as
sitting in complete non-null parent-section groups.  This adapter assembles the
ordered sibling context for exactly that positive cohort and writes the private
3,526-row JSONL only to approved Google Drive custody.

The 4,479 null-parent negative cohort stays immutable and outside this output.
No labels, semantic gold, corrections, source-role inferences, or provider calls
are emitted.  School-family / Phase-3 / Phase-4 completion remain false.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_context_manifest as eval_manifest
from scripts.projects.open_model_data import phase3_school_context_negative_recovery as negrec

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_school_parent_section_context_receipt_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT = DATA / "inventory/phase3_school_parent_section_context_receipt_v1.json"
NEGREC_RECEIPT = DATA / "inventory/phase3_school_context_negative_recovery_receipt_v1.json"
EVAL_CONTEXT_RECEIPT = DATA / "inventory/phase3_evaluation_context_manifest_receipt_v1.json"
SOURCE_UNIVERSE_RECEIPT = DATA / "evidence/source_universe_v1/source-universe-freeze-receipt.json"

PRIVATE_FILENAME = "school_parent_section_context_v1.jsonl"
CUSTODY_RECEIPT_FILENAME = "phase3_school_parent_section_context_custody_receipt_v1.json"
CUSTODY_RECEIPT_SUCCESSOR_FILENAME = "phase3_school_parent_section_context_custody_receipt_v1.successor.json"
CUSTODY_RECEIPT_SUCCESSOR_STEM = "phase3_school_parent_section_context_custody_receipt_v1.successor"
CUSTODY_SUCCESSOR_MAX = 32
CHECKSUMS_FILENAME = "SHA256SUMS"
SCHEMA_VERSION = "phase3_school_parent_section_context_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_school_parent_section_context_v1"
CONTEXT_KIND = "school_complete_parent_section_context"
PARENT_SECTION_SEPARATOR = "\n\n"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
# Git-tracked text-free receipts check out as 0644; new writes stay owner-only 0600.
TRACKED_PUBLIC_FILE_MODE = 0o644
ACCEPTED_PUBLIC_RECEIPT_MODES = frozenset({PRIVATE_FILE_MODE, TRACKED_PUBLIC_FILE_MODE})
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"

PINNED_SOURCE_UNITS_JSONL_SHA256 = eval_manifest.PINNED_SOURCE_UNITS_JSONL_SHA256
PINNED_PARTITION_SHA256 = eval_manifest.PINNED_PARTITION_SHA256
PINNED_CUSTODY_TARBALL_SHA256 = eval_manifest.PINNED_CUSTODY_TARBALL_SHA256
PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256 = negrec.PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256
PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256 = negrec.PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256
PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256 = negrec.PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256
PINNED_NEGREC_RECEIPT_BODY_SHA256 = "c72ddf3c9c07f5a393c0bb4eb33c057c5d820d0cec4df29029d7a8ac7c7747ae"
PINNED_NEGREC_RECEIPT_FILE_SHA256 = "2d63b8295b1583abf835ab6a1661646ab15ea4b85979e37a7bf1ffcf8d39651c"

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
POSITIVE_HELDOUT_PARENT_GROUPS = 939
POSITIVE_HELDOUT_SOURCE_FILES = 15

ROW_FIELDS = frozenset(
    {
        "unit_id",
        "unit_sha256",
        "family_id",
        "candidate_lane",
        "context_kind",
        "complete_sentence_context",
        "source_file",
        "parent_section_id",
        "source_record_id",
        "chunk_id",
        "unit_text",
        "unit_text_sha256",
        "complete_parent_section_context",
        "complete_parent_section_context_sha256",
        "unit_text_start_offset",
        "unit_text_end_offset",
        "sibling_count",
        "group_membership_sha256",
        "group_order_sha256",
        "separator",
    }
)

DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0


class SchoolParentSectionContextError(ValueError):
    """School parent-section context cannot be built or verified safely."""


class DriveIdentityPendingError(SchoolParentSectionContextError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SchoolParentSectionContextError(message)


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
        raise SchoolParentSectionContextError(f"cannot read artifact: {path}") from exc
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
        raise SchoolParentSectionContextError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")


def _regular_private(path: Path, label: str) -> None:
    _regular_file(path, label)
    require(stat.S_IMODE(path.lstat().st_mode) == PRIVATE_FILE_MODE, f"{label} permissions must be 0600")


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
        raise SchoolParentSectionContextError(f"invalid strict JSON: {label}") from exc
    require(isinstance(value, dict), f"{label} top-level type drift")
    return value


def _iter_jsonl(path: Path, label: str) -> Iterator[dict[str, Any]]:
    _regular_file(path, label)
    with path.open("rb") as handle:
        for index, raw_line in enumerate(handle, start=1):
            require(raw_line.endswith(b"\n"), f"{label} row lacks LF: {index}")
            line = raw_line[:-1]
            require(line.strip() == line, f"{label} noncanonical whitespace: {index}")
            require(line, f"{label} empty line: {index}")
            yield _strict_json_object(line, f"{label} line {index}")


def _atomic_write(path: Path, payload: bytes) -> None:
    """Atomically write *payload* with owner-only permissions (mode 0600).

    Mode is a fixed literal at every fchmod/chmod site (no caller-controlled
    argument) so static analysis can prove the permission policy.
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


def _prepare_private_output(path: Path) -> None:
    _reject_symlink_components(path, "private output")
    parent = path.parent
    if parent.exists():
        require(parent.is_dir() and not parent.is_symlink(), "private output parent must be a real directory")
        require(
            stat.S_IMODE(parent.stat().st_mode) == PRIVATE_DIR_MODE,
            "private output directory must be mode 0700",
        )
    else:
        parent.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        os.chmod(parent, PRIVATE_DIR_MODE)
    if path.exists():
        require(path.is_file() and not path.is_symlink(), "private output path is unsafe")
        require(
            stat.S_IMODE(path.stat().st_mode) == PRIVATE_FILE_MODE,
            "existing private output must be mode 0600",
        )


def _write_immutable(path: Path, payload: bytes, *, label: str) -> None:
    """Idempotent private write: existing files must remain mode 0600 with identical bytes."""
    _reject_symlink_components(path, label)
    if path.exists():
        _regular_private(path, label)
        require(path.read_bytes() == payload, f"refusing to overwrite changed {label}")
        return
    _atomic_write(path, payload)


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
    so production staging always uses the realpath canonical root.
    """
    created = Path(tempfile.mkdtemp(prefix=prefix, dir=None))
    resolved = Path(os.path.realpath(created))
    if resolved != created:
        # realpath may return the same inode via a different lexical path.
        require(resolved.exists(), "resolved temp root missing after mkdtemp")
    os.chmod(resolved, PRIVATE_DIR_MODE)
    _reject_symlink_components(resolved, "temp root")
    return resolved


def _drive_item_id(path: Path) -> str:
    resolved = path.resolve()
    try:
        drive_roots = [
            candidate.resolve()
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise SchoolParentSectionContextError("cannot inspect configured Google Drive mounts") from exc
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
            raise SchoolParentSectionContextError(
                f"artifact did not acquire Google Drive provider identity within {timeout_seconds:g} seconds"
            ) from last_error
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))


def _verify_drive_readback(path: Path, expected_sha256: str) -> str:
    readback = sha256_file(path)
    require(readback == expected_sha256, "Drive read-back hash mismatch")
    return _wait_for_drive_item_id(path)


def _validate_public_bindings() -> None:
    require(SCHEMA_PATH.is_file(), "missing parent-section context schema")
    require(NEGREC_RECEIPT.is_file(), "missing #6782 negative-recovery receipt")
    require(EVAL_CONTEXT_RECEIPT.is_file(), "missing evaluation context receipt")
    require(SOURCE_UNIVERSE_RECEIPT.is_file(), "missing source universe receipt")
    require(
        sha256_file(NEGREC_RECEIPT) == PINNED_NEGREC_RECEIPT_FILE_SHA256,
        "negative-recovery receipt file drift",
    )
    neg = _strict_json_object(NEGREC_RECEIPT.read_bytes(), "negative-recovery receipt")
    require(receipt_sha256(neg) == PINNED_NEGREC_RECEIPT_BODY_SHA256, "negative-recovery receipt body drift")
    require(
        neg.get("receipt_sha256") == PINNED_NEGREC_RECEIPT_BODY_SHA256,
        "negative-recovery receipt_sha256 field drift",
    )
    require(
        neg.get("parent_section_census", {}).get("heldout_in_complete_ordered_parent_section")
        == PARENT_COMPLETE_HELDOUT,
        "#6782 positive cohort drift",
    )
    require(
        neg.get("parent_section_census", {}).get("heldout_with_null_parent_section_id") == PARENT_NULL_HELDOUT,
        "#6782 negative cohort drift",
    )
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
        sha256_file(SOURCE_UNIVERSE_RECEIPT) == PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
        "source universe receipt hash drift",
    )


def _load_heldout_school(partition_path: Path) -> dict[str, dict[str, Any]]:
    require(sha256_file(partition_path) == PINNED_PARTITION_SHA256, "partition hash drift")
    heldout: dict[str, dict[str, Any]] = {}
    for row in _iter_jsonl(partition_path, "partition manifest"):
        if row.get("family_id") != "school_textbooks":
            continue
        unit_id = row.get("unit_id")
        unit_sha = row.get("unit_sha256")
        require(isinstance(unit_id, str) and isinstance(unit_sha, str), "partition school row identity drift")
        require(unit_id not in heldout, f"duplicate held-out school unit_id: {unit_id}")
        require(row.get("reason") == "evaluation_only", "partition reason drift")
        lane = row.get("candidate_lane")
        require(isinstance(lane, str) and lane, "partition candidate_lane drift")
        heldout[unit_id] = {
            "unit_sha256": unit_sha,
            "candidate_lane": lane,
            "source_text_sha256": row.get("source_text_sha256"),
        }
    require(len(heldout) == SCHOOL_HELDOUT, "held-out school count drift")
    return heldout


def _assemble_parent_section(texts: Sequence[str]) -> tuple[str, list[tuple[int, int]]]:
    require(texts, "empty parent section group")
    parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for index, text in enumerate(texts):
        require(isinstance(text, str), "sibling text type drift")
        if index:
            parts.append(PARENT_SECTION_SEPARATOR)
            cursor += len(PARENT_SECTION_SEPARATOR)
        start = cursor
        end = start + len(text)
        offsets.append((start, end))
        parts.append(text)
        cursor = end
    context = "".join(parts)
    require(len(offsets) == len(texts), "offset/text cardinality drift")
    for (start, end), text in zip(offsets, texts, strict=True):
        require(context[start:end] == text, "unicode offset round-trip drift")
    return context, offsets


def build_context_rows(
    *,
    source_jsonl: Path,
    partition_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(sha256_file(source_jsonl) == PINNED_SOURCE_UNITS_JSONL_SHA256, "source units hash drift")
    heldout = _load_heldout_school(partition_path)

    school_rows = 0
    school_null_parent = 0
    heldout_seen: set[str] = set()
    heldout_null = 0
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)

    for row in _iter_jsonl(source_jsonl, "source units"):
        if row.get("family_id") != "school_textbooks":
            continue
        school_rows += 1
        unit_id = row.get("unit_id")
        unit_sha = row.get("unit_sha256")
        require(isinstance(unit_id, str) and isinstance(unit_sha, str), "school unit identity drift")
        source_text = row.get("source_text")
        source_text_sha = row.get("source_text_sha256")
        require(isinstance(source_text, str), "school source_text missing")
        require(isinstance(source_text_sha, str), "school source_text_sha256 missing")
        require(
            sha256_bytes(source_text.encode("utf-8")) == source_text_sha,
            "school source_text hash drift",
        )
        source_record = row.get("source_record")
        require(isinstance(source_record, Mapping), "school source_record missing")
        parent = source_record.get("parent_section_id")
        source_file = source_record.get("source_file")
        record_id = source_record.get("id")
        chunk_id = source_record.get("chunk_id")
        require(isinstance(source_file, str) and source_file, "source_file missing")
        require(record_id is not None, "source_record.id missing")
        require(chunk_id is not None, "source_record.chunk_id missing")

        if unit_id in heldout:
            require(unit_id not in heldout_seen, f"duplicate school held-out materialization: {unit_id}")
            heldout_seen.add(unit_id)
            require(heldout[unit_id]["unit_sha256"] == unit_sha, "held-out unit_sha256 mismatch")
            expected_text_sha = heldout[unit_id]["source_text_sha256"]
            if isinstance(expected_text_sha, str):
                require(expected_text_sha == source_text_sha, "held-out source_text_sha256 mismatch")

        if parent is None:
            school_null_parent += 1
            if unit_id in heldout:
                heldout_null += 1
            continue

        require(isinstance(parent, int), "non-null parent_section_id must be int")
        groups[(source_file, parent)].append(
            {
                "unit_id": unit_id,
                "unit_sha256": unit_sha,
                "source_text": source_text,
                "source_text_sha256": source_text_sha,
                "source_file": source_file,
                "parent_section_id": parent,
                "source_record_id": record_id,
                "chunk_id": chunk_id,
                "is_heldout": unit_id in heldout,
                "candidate_lane": heldout[unit_id]["candidate_lane"] if unit_id in heldout else None,
            }
        )

    require(school_rows == SCHOOL_UNIVERSE, "school universe count drift")
    require(school_null_parent == SCHOOL_NULL_PARENT_ROWS, "school null-parent universe drift")
    require(len(heldout_seen) == SCHOOL_HELDOUT, "held-out school materialization coverage drift")
    require(heldout_null == PARENT_NULL_HELDOUT, "held-out null parent_section_id drift")
    require(len(groups) == NON_NULL_PARENT_GROUPS, "non-null parent section group count drift")

    positive_rows: list[dict[str, Any]] = []
    positive_groups = 0
    positive_files: set[str] = set()

    for (source_file, parent_section_id), members in groups.items():
        ids = [item["source_record_id"] for item in members]
        chunk_ids = [item["chunk_id"] for item in members]
        require(len(ids) == len(set(ids)), "non-unique source_record.id inside parent section")
        require(len(chunk_ids) == len(set(chunk_ids)), "non-unique chunk_id inside parent section")
        try:
            ordered = sorted(members, key=lambda item: item["source_record_id"])
        except TypeError as exc:
            raise SchoolParentSectionContextError("ambiguous parent-section ordering") from exc
        # Stable total order must be unique under the sort key.
        require(
            [item["source_record_id"] for item in ordered] == sorted(ids),
            "ambiguous parent-section ordering",
        )
        held_members = [item for item in ordered if item["is_heldout"]]
        if not held_members:
            continue
        positive_groups += 1
        positive_files.add(source_file)

        texts = [item["source_text"] for item in ordered]
        context, offsets = _assemble_parent_section(texts)
        context_sha = sha256_bytes(context.encode("utf-8"))
        membership = [item["unit_id"] for item in ordered]
        order_payload = [
            {
                "source_record_id": item["source_record_id"],
                "unit_id": item["unit_id"],
                "unit_sha256": item["unit_sha256"],
            }
            for item in ordered
        ]
        membership_sha = sha256_bytes(canonical_bytes(membership))
        order_sha = sha256_bytes(canonical_bytes(order_payload))
        sibling_count = len(ordered)
        require(sibling_count >= 1, "incomplete parent section group")

        for item, (start, end) in zip(ordered, offsets, strict=True):
            if not item["is_heldout"]:
                continue
            require(item["candidate_lane"] is not None, "held-out candidate_lane missing")
            require(context[start:end] == item["source_text"], "held-out offset round-trip drift")
            row = {
                "unit_id": item["unit_id"],
                "unit_sha256": item["unit_sha256"],
                "family_id": "school_textbooks",
                "candidate_lane": item["candidate_lane"],
                "context_kind": CONTEXT_KIND,
                "complete_sentence_context": False,
                "source_file": source_file,
                "parent_section_id": parent_section_id,
                "source_record_id": item["source_record_id"],
                "chunk_id": item["chunk_id"],
                "unit_text": item["source_text"],
                "unit_text_sha256": item["source_text_sha256"],
                "complete_parent_section_context": context,
                "complete_parent_section_context_sha256": context_sha,
                "unit_text_start_offset": start,
                "unit_text_end_offset": end,
                "sibling_count": sibling_count,
                "group_membership_sha256": membership_sha,
                "group_order_sha256": order_sha,
                "separator": PARENT_SECTION_SEPARATOR,
            }
            require(set(row) == ROW_FIELDS, "private row shape drift")
            positive_rows.append(row)

    require(len(positive_rows) == PARENT_COMPLETE_HELDOUT, "positive parent-section held-out drift")
    require(positive_groups == POSITIVE_HELDOUT_PARENT_GROUPS, "positive held-out group count drift")
    require(len(positive_files) == POSITIVE_HELDOUT_SOURCE_FILES, "positive held-out source-file count drift")
    require(
        heldout_null + len(positive_rows) == SCHOOL_HELDOUT,
        "held-out parent-section partition does not cover 8005",
    )

    positive_ids = {row["unit_id"] for row in positive_rows}
    require(len(positive_ids) == PARENT_COMPLETE_HELDOUT, "duplicate positive unit_id in output")
    require(len(heldout) - len(positive_ids) == PARENT_NULL_HELDOUT, "negative cohort exclusion drift")
    require(positive_ids.issubset(set(heldout)), "positive output escaped held-out set")
    for row in positive_rows:
        require(row["parent_section_id"] is not None, "null parent_section_id leaked into positive output")

    positive_rows.sort(key=lambda item: (item["source_file"], item["parent_section_id"], item["source_record_id"]))
    accounting = {
        "positive_parent_section_heldout": len(positive_rows),
        "negative_null_parent_heldout_excluded": PARENT_NULL_HELDOUT,
        "positive_heldout_parent_section_groups": positive_groups,
        "positive_heldout_source_files": len(positive_files),
        "non_null_parent_section_groups_total": len(groups),
        "school_heldout_total": SCHOOL_HELDOUT,
        "school_universe_units": SCHOOL_UNIVERSE,
    }
    return positive_rows, accounting


def _build_receipt(
    *,
    context_payload: bytes,
    accounting: Mapping[str, Any],
    started_at: str,
    completed_at: str,
    custody: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_public_bindings()
    require(accounting["positive_parent_section_heldout"] == PARENT_COMPLETE_HELDOUT, "accounting positive drift")
    require(
        accounting["negative_null_parent_heldout_excluded"] == PARENT_NULL_HELDOUT,
        "accounting negative drift",
    )
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "labels_present": False,
        "semantic_gold": False,
        "started_at": started_at,
        "completed_at": completed_at,
        "bindings": {
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "receipt_schema_sha256": sha256_file(SCHEMA_PATH),
            "source_units_jsonl_sha256": PINNED_SOURCE_UNITS_JSONL_SHA256,
            "partition_manifest_sha256": PINNED_PARTITION_SHA256,
            "custody_tarball_sha256": PINNED_CUSTODY_TARBALL_SHA256,
            "school_context_negative_recovery_receipt_body_sha256": PINNED_NEGREC_RECEIPT_BODY_SHA256,
            "school_context_negative_recovery_receipt_file_sha256": PINNED_NEGREC_RECEIPT_FILE_SHA256,
            "evaluation_context_manifest_receipt_body_sha256": PINNED_EVAL_CONTEXT_RECEIPT_BODY_SHA256,
            "evaluation_context_manifest_receipt_file_sha256": PINNED_EVAL_CONTEXT_RECEIPT_FILE_SHA256,
            "source_universe_receipt_sha256": PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
        },
        "denominators": {
            "v2_source_units": V2_SOURCE_UNITS,
            "v2_evaluation_identities": V2_EVALUATION_IDENTITIES,
            "school_universe_units": SCHOOL_UNIVERSE,
            "school_heldout_total": SCHOOL_HELDOUT,
            "positive_parent_section_heldout": PARENT_COMPLETE_HELDOUT,
            "negative_null_parent_heldout_excluded": PARENT_NULL_HELDOUT,
            "non_null_parent_section_groups_total": NON_NULL_PARENT_GROUPS,
            "positive_heldout_parent_section_groups": POSITIVE_HELDOUT_PARENT_GROUPS,
            "positive_heldout_source_files": POSITIVE_HELDOUT_SOURCE_FILES,
        },
        "context": {
            "private_jsonl_filename": PRIVATE_FILENAME,
            "private_jsonl_sha256": sha256_bytes(context_payload),
            "private_jsonl_bytes": len(context_payload),
            "private_jsonl_rows": PARENT_COMPLETE_HELDOUT,
            "separator": PARENT_SECTION_SEPARATOR,
            "separator_sha256": sha256_bytes(PARENT_SECTION_SEPARATOR.encode("utf-8")),
        },
        "gates": {
            "school_parent_section_context_materialized": True,
            "school_complete_context_ready": False,
            "semantic_labels_present": False,
            "source_authoring_blocked": True,
            "complete_evaluation_package_ready": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    if custody is not None:
        receipt["custody"] = dict(custody)
    receipt["receipt_sha256"] = receipt_sha256(receipt)
    _schema_validator().validate(receipt)
    return receipt


def _schema_validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def validate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _schema_validator().validate(receipt)
    require(receipt_sha256(receipt) == receipt["receipt_sha256"], "receipt self-hash drift")
    require(receipt.get("text_free") is True, "receipt must be text-free")
    require(receipt.get("provider_calls") is False, "provider_calls must be false")
    require(receipt.get("labels_present") is False, "labels_present must be false")
    require(receipt.get("semantic_gold") is False, "semantic_gold must be false")
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
        bindings["school_context_negative_recovery_receipt_body_sha256"] == PINNED_NEGREC_RECEIPT_BODY_SHA256,
        "negative-recovery body binding drift",
    )
    require(
        bindings["school_context_negative_recovery_receipt_file_sha256"] == PINNED_NEGREC_RECEIPT_FILE_SHA256,
        "negative-recovery file binding drift",
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
    # Public receipt must not contain private source text or row-level held-out IDs.
    dumped = canonical_json(receipt)
    require("unit.school_textbooks." not in dumped, "public receipt leaked held-out unit id")
    require(not any("\u0400" <= char <= "\u04ff" for char in dumped), "public receipt leaked Cyrillic text")
    return dict(receipt)


def materialize(
    *,
    source_jsonl: Path,
    partition_path: Path,
    private_output: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
    custody: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    rows, accounting = build_context_rows(source_jsonl=source_jsonl, partition_path=partition_path)
    payload = b"".join(canonical_bytes(row) for row in rows)
    require(payload.count(b"\n") == PARENT_COMPLETE_HELDOUT, "private JSONL row count drift")
    finished = completed_at or utc_now()
    receipt = _build_receipt(
        context_payload=payload,
        accounting=accounting,
        started_at=started_at,
        completed_at=finished,
        custody=custody,
    )
    _prepare_private_output(private_output)
    _write_immutable(private_output, payload, label="private context artifact")
    _write_public_receipt(public_receipt_path, canonical_bytes(receipt))
    return validate_receipt(_strict_json_object(public_receipt_path.read_bytes(), "public receipt"))


def verify_existing(
    *,
    source_jsonl: Path,
    partition_path: Path,
    private_output: Path,
    public_receipt_path: Path,
) -> dict[str, Any]:
    rows, accounting = build_context_rows(source_jsonl=source_jsonl, partition_path=partition_path)
    payload = b"".join(canonical_bytes(row) for row in rows)
    _regular_private(private_output, "private context artifact")
    require(private_output.read_bytes() == payload, "private context artifact drift")
    _regular_public(public_receipt_path, "public receipt")
    receipt = validate_receipt(_strict_json_object(public_receipt_path.read_bytes(), "public receipt"))
    require(
        receipt["context"]["private_jsonl_sha256"] == sha256_bytes(payload),
        "public receipt context hash drift",
    )
    require(
        receipt["denominators"]["positive_parent_section_heldout"] == accounting["positive_parent_section_heldout"],
        "denominator drift on verify",
    )
    rebuilt = _build_receipt(
        context_payload=payload,
        accounting=accounting,
        started_at=receipt["started_at"],
        completed_at=receipt["completed_at"],
        custody=receipt.get("custody"),
    )
    require(receipt == rebuilt, "public receipt drift against rebuilt proof")
    return receipt


def _write_checksums(directory: Path, files: Mapping[str, Path]) -> Path:
    lines = [f"{sha256_file(path)}  {name}\n" for name, path in sorted(files.items())]
    checksums_path = directory / CHECKSUMS_FILENAME
    _write_immutable(checksums_path, "".join(lines).encode("utf-8"), label="checksums")
    return checksums_path


def _custody_successor_path(drive_backup_dir: Path, index: int) -> Path:
    """Return versioned custody successor path (1 → .successor.json, 2+ → .successor.N.json)."""
    require(1 <= index <= CUSTODY_SUCCESSOR_MAX, "custody successor index out of range")
    if index == 1:
        return drive_backup_dir / CUSTODY_RECEIPT_SUCCESSOR_FILENAME
    return drive_backup_dir / f"{CUSTODY_RECEIPT_SUCCESSOR_STEM}.{index}.json"


def _iter_custody_receipt_paths(drive_backup_dir: Path) -> list[Path]:
    """Primary plus existing versioned successors in write order."""
    paths = [drive_backup_dir / CUSTODY_RECEIPT_FILENAME]
    for index in range(1, CUSTODY_SUCCESSOR_MAX + 1):
        candidate = _custody_successor_path(drive_backup_dir, index)
        if candidate.exists():
            paths.append(candidate)
        else:
            break
    return paths


def _write_custody_receipt(drive_backup_dir: Path, custody_receipt: Mapping[str, Any]) -> Path:
    """Write custody receipt immutably, preserving prior evidence via versioned successors."""
    payload = canonical_bytes(custody_receipt)
    primary = drive_backup_dir / CUSTODY_RECEIPT_FILENAME
    if not primary.exists():
        _write_immutable(primary, payload, label="custody receipt")
        return primary
    _regular_private(primary, "custody receipt")
    if primary.read_bytes() == payload:
        return primary
    for index in range(1, CUSTODY_SUCCESSOR_MAX + 1):
        successor = _custody_successor_path(drive_backup_dir, index)
        if successor.exists():
            _regular_private(successor, f"custody receipt successor {index}")
            if successor.read_bytes() == payload:
                return successor
            continue
        _atomic_write(successor, payload)
        return successor
    raise SchoolParentSectionContextError("custody successor chain exhausted")


def _build_custody_block(
    *,
    private_context: Path,
    drive_backup_dir: Path,
    provider_id: str,
) -> dict[str, Any]:
    relative = str(drive_backup_dir)
    # Prefer a stable relative locator under the Drive project tree when possible.
    marker = "Projects/learn-ukrainian-data/"
    if marker in relative:
        relative = relative.split(marker, 1)[1]
    return {
        "google_drive_custody": True,
        "google_drive_mount_containment_verified": True,
        "google_drive_provider_identity_present": True,
        "google_drive_provider_identity_sha256": sha256_bytes(provider_id.encode("utf-8")),
        "drive_relative_directory": relative,
        "private_files_mode_0600": stat.S_IMODE(private_context.stat().st_mode) == PRIVATE_FILE_MODE,
        "private_directory_mode_0700": stat.S_IMODE(private_context.parent.stat().st_mode) == PRIVATE_DIR_MODE,
        "all_new_files_readback_hash_match": True,
    }


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
    drive_backup_dir: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
) -> dict[str, Any]:
    require(drive_backup_dir.parent.is_dir(), "drive backup parent must exist")
    _reject_symlink_components(drive_backup_dir, "drive backup directory")
    drive_backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(drive_backup_dir, PRIVATE_DIR_MODE)
    temp_root = _canonical_temp_root("phase3-school-parent-ctx-")
    try:
        extracted = _extract_tarball_members(custody_tarball, temp_root)
        private_output = drive_backup_dir / PRIVATE_FILENAME
        # First pass builds payload; custody metadata filled after Drive identity.
        rows, accounting = build_context_rows(
            source_jsonl=extracted["source_jsonl"],
            partition_path=extracted["partition"],
        )
        payload = b"".join(canonical_bytes(row) for row in rows)
        _prepare_private_output(private_output)
        _write_immutable(private_output, payload, label="private context artifact")
        provider_id = _verify_drive_readback(private_output, sha256_bytes(payload))
        custody = _build_custody_block(
            private_context=private_output,
            drive_backup_dir=drive_backup_dir,
            provider_id=provider_id,
        )
        finished = completed_at or utc_now()
        receipt = _build_receipt(
            context_payload=payload,
            accounting=accounting,
            started_at=started_at,
            completed_at=finished,
            custody=custody,
        )
        _write_public_receipt(public_receipt_path, canonical_bytes(receipt))
        checksums_path = _write_checksums(drive_backup_dir, {PRIVATE_FILENAME: private_output})
        custody_receipt = {
            "schema_version": "phase3_school_parent_section_context_custody_receipt_v1",
            "text_free": True,
            "provider_calls": False,
            "labels_present": False,
            "semantic_gold": False,
            "artifacts": {
                "private_context_filename": PRIVATE_FILENAME,
                "private_context_sha256": sha256_bytes(payload),
                "checksums_filename": CHECKSUMS_FILENAME,
                "checksums_sha256": sha256_file(checksums_path),
                "public_receipt_sha256": receipt["receipt_sha256"],
            },
            "custody": custody,
            "gates": {
                "school_parent_section_context_materialized": True,
                "school_complete_context_ready": False,
                "phase3_complete": False,
                "phase4_blocked": True,
            },
        }
        custody_receipt["receipt_sha256"] = receipt_sha256(custody_receipt)
        custody_path = _write_custody_receipt(drive_backup_dir, custody_receipt)
        _verify_drive_readback(custody_path, sha256_bytes(canonical_bytes(custody_receipt)))
        _verify_drive_readback(checksums_path, sha256_file(checksums_path))
        return validate_receipt(receipt)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build private context + public receipt")
    build.add_argument("--source-jsonl", type=Path, required=True)
    build.add_argument("--partition", type=Path, required=True)
    build.add_argument("--private-output", type=Path, required=True)
    build.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    build.add_argument("--started-at")
    build.add_argument("--completed-at")

    verify = subparsers.add_parser("verify", help="re-prove context and verify existing artifacts")
    verify.add_argument("--source-jsonl", type=Path, required=True)
    verify.add_argument("--partition", type=Path, required=True)
    verify.add_argument("--private-output", type=Path, required=True)
    verify.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)

    production = subparsers.add_parser("production", help="extract custody and write Drive private JSONL")
    production.add_argument("--custody-tarball", type=Path, required=True)
    production.add_argument("--drive-backup-dir", type=Path, required=True)
    production.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
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
                private_output=args.private_output,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
        elif args.command == "verify":
            receipt = verify_existing(
                source_jsonl=args.source_jsonl,
                partition_path=args.partition,
                private_output=args.private_output,
                public_receipt_path=args.public_receipt,
            )
        else:
            receipt = production_run(
                custody_tarball=args.custody_tarball,
                drive_backup_dir=args.drive_backup_dir,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
    except (OSError, SchoolParentSectionContextError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        canonical_json(
            {
                "ok": True,
                "receipt_sha256": receipt["receipt_sha256"],
                "private_jsonl_sha256": receipt["context"]["private_jsonl_sha256"],
                "private_jsonl_rows": receipt["context"]["private_jsonl_rows"],
                "provider_calls": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
