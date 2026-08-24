#!/usr/bin/env python3
"""Recover complete parent-rule context for the 413 held-out Pravopys identities.

The adapter binds the pinned evaluation-context manifest (#6758), the sealed
evaluation partition, and the frozen source materialization.  It derives each
parent rule from ``frozen_locator.section_path`` without labels, correction
gold, provider calls, or training admission.
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
from collections import Counter
from collections.abc import Mapping, Sequence
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
SCHEMA_PATH = DATA / "contracts/phase3_pravopys_evaluation_context_receipt_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT = DATA / "inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
PRIVATE_FILENAME = "pravopys_evaluation_context_v1.jsonl"
CUSTODY_RECEIPT_FILENAME = "phase3_pravopys_evaluation_context_custody_receipt_v1.json"
CHECKSUMS_FILENAME = "SHA256SUMS"
SCHEMA_VERSION = "phase3_pravopys_evaluation_context_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_pravopys_evaluation_context_v1"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"

ROW_COUNT = 413
PRAVOPYS_FAMILIES = frozenset({"pravopys_2019_complete", "pravopys_2026_complete"})
FAMILY_COUNTS = {"pravopys_2019_complete": 178, "pravopys_2026_complete": 235}
LANE_COUNTS = {"phenomenon_strata": 413}
MAPPING_ACCOUNTING = {"self_parent_rule": 59, "child_parent_rule": 354}
CONTEXT_ACCOUNTING = {"pravopys_parent_rule_context": 413, "pravopys_typed_exclusion": 0}

PINNED_SOURCE_UNITS_JSONL_SHA256 = eval_manifest.PINNED_SOURCE_UNITS_JSONL_SHA256
PINNED_PARTITION_SHA256 = eval_manifest.PINNED_PARTITION_SHA256
PINNED_CUSTODY_TARBALL_SHA256 = eval_manifest.PINNED_CUSTODY_TARBALL_SHA256
PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256 = "62e9dd450f18257ad841e0b3141bd267353a30e8d7cffe1d1bc874671ac9b8e6"
PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_BODY_SHA256 = (
    "f01d8efd0a1279d7cf4b742ad6909de4a7d2a3866195b7f7e1b56d8e1e2598d1"
)
PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256 = eval_manifest.sha256_file(
    DATA / "inventory/phase3_evaluation_context_manifest_receipt_v1.json"
)
PINNED_PRAVOPYS_2019_PDF_SHA256 = "9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c"
PINNED_PRAVOPYS_2026_PDF_SHA256 = "e593956bfba6737d991a76fa86970db9c10a5cd7fd8895bae67f2b9a950c3a92"

TARBALL_MEMBERS = {
    "source_jsonl": "batch_state/phase3-private/v21-cycle001/source-materialization/source_units_v1.jsonl",
    "partition": "batch_state/phase3-private/v21-cycle001/evaluation-partition/partition_manifest_v1.jsonl",
    "pravopys_2019_pdf": "batch_state/phase3-private/source-bytes/pravopys-2019.pdf",
    "pravopys_2026_pdf": "batch_state/phase3-private/source-bytes/pravopys-2026.pdf",
}

CONTEXT_KINDS = frozenset({"pravopys_parent_rule_context", "pravopys_typed_exclusion"})
EXCLUSION_REASONS = frozenset(
    {
        "duplicate_parent_rule",
        "invalid_section_path",
        "missing_parent_rule",
        "unit_text_not_contained_in_parent",
        "unit_text_not_unique_in_parent",
    }
)
PARTITION_FIELDS = eval_manifest.PARTITION_FIELDS
SOURCE_FIELDS = eval_manifest.SOURCE_FIELDS
EVAL_MANIFEST_FIELDS = frozenset(
    {
        "unit_id",
        "unit_sha256",
        "family_id",
        "candidate_lane",
        "context_kind",
        "complete_sentence_context",
        "source_text",
        "source_text_sha256",
        "frozen_locator_sha256",
    }
)
RECOVERED_ROW_FIELDS = frozenset(
    {
        "unit_id",
        "unit_sha256",
        "family_id",
        "candidate_lane",
        "context_kind",
        "complete_sentence_context",
        "unit_text",
        "unit_text_sha256",
        "frozen_locator",
        "frozen_locator_sha256",
        "parent_section_path",
        "parent_unit_id",
        "parent_unit_sha256",
        "parent_rule_mapping_kind",
        "complete_parent_rule_context",
        "complete_parent_rule_context_sha256",
        "unit_text_start_offset",
        "unit_text_end_offset",
    }
)
EXCLUDED_ROW_FIELDS = frozenset(
    {
        "unit_id",
        "unit_sha256",
        "family_id",
        "candidate_lane",
        "context_kind",
        "complete_sentence_context",
        "unit_text",
        "unit_text_sha256",
        "frozen_locator",
        "frozen_locator_sha256",
        "parent_section_path",
        "exclusion_reason_code",
    }
)


class PravopysEvaluationContextError(ValueError):
    """The Pravopys evaluation context cannot be built or verified safely."""


class DriveIdentityPendingError(PravopysEvaluationContextError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0
DEFAULT_XATTR_TIMEOUT_SECONDS: float = 30.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PravopysEvaluationContextError(message)


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
        raise PravopysEvaluationContextError(f"cannot read artifact: {path}") from exc
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


def _regular_private(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        state = path.lstat()
    except OSError as exc:
        raise PravopysEvaluationContextError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(state.st_mode) == PRIVATE_FILE_MODE, f"{label} permissions must be 0600")


def _regular_text_free_receipt(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        state = path.lstat()
    except OSError as exc:
        raise PravopysEvaluationContextError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")
    mode = stat.S_IMODE(state.st_mode)
    require(mode == PRIVATE_FILE_MODE, f"{label} permissions must be 0600")
    require(mode & 0o077 == 0, f"{label} must not grant group/other access")


def _strict_json_bytes(raw: bytes, label: str, top: type[Any] = dict) -> Any:
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PravopysEvaluationContextError(f"invalid strict JSON: {label}") from exc
    require(isinstance(value, top), f"{label} top-level type drift")
    return value


def _read_text_free_receipt_json(path: Path, label: str) -> dict[str, Any]:
    _regular_text_free_receipt(path, label)
    value = _strict_json_bytes(path.read_bytes(), label)
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _verified_private_file_bytes(path: Path, label: str) -> tuple[bytes, str]:
    _regular_private(path, label)
    raw = path.read_bytes()
    return raw, sha256_bytes(raw)


def _parse_jsonl_bytes(raw: bytes, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.splitlines(keepends=True), start=1):
        require(line.endswith(b"\n"), f"{label} row lacks LF: {line_number}")
        row = _strict_json_bytes(line, f"{label}:{line_number}")
        require(isinstance(row, dict), f"{label} row is not an object: {line_number}")
        rows.append(row)
    return rows


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    _regular_private(path, label)
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            require(raw.endswith(b"\n"), f"{label} row lacks LF: {line_number}")
            row = _strict_json_bytes(raw, f"{label}:{line_number}")
            require(isinstance(row, dict), f"{label} row is not an object: {line_number}")
            rows.append(row)
    return rows


def _read_inventory_receipt_binding(path: Path, label: str) -> dict[str, Any]:
    """Read a tracked inventory receipt for hash binding without private-mode requirements."""
    _reject_symlink_components(path, label)
    try:
        state = path.lstat()
    except OSError as exc:
        raise PravopysEvaluationContextError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")
    value = _strict_json_bytes(path.read_bytes(), label)
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _validate_evaluation_context_manifest_receipt(path: Path) -> dict[str, Any]:
    receipt = _read_inventory_receipt_binding(path, "evaluation context manifest receipt")
    try:
        validated = eval_manifest.validate_receipt(receipt)
    except eval_manifest.EvaluationContextManifestError as exc:
        raise PravopysEvaluationContextError(str(exc)) from exc
    require(sha256_file(path) == PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256, "manifest receipt file drift")
    require(
        validated["receipt_sha256"] == PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_BODY_SHA256,
        "manifest receipt body drift",
    )
    require(
        validated["manifest"]["private_jsonl_sha256"] == PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256,
        "evaluation context manifest hash drift",
    )
    return validated


def _load_source_index_from_bytes(raw: bytes) -> dict[tuple[str, str], dict[str, Any]]:
    file_hash = sha256_bytes(raw)
    require(file_hash == PINNED_SOURCE_UNITS_JSONL_SHA256, "source materialization stream drift")
    rows = _parse_jsonl_bytes(raw, "source materialization")
    require(len(rows) == eval_manifest.V2_SOURCE_UNITS, "source materialization row count drift")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for line_number, row in enumerate(rows, start=1):
        require(set(row) == SOURCE_FIELDS, f"source row shape drift: {line_number}")
        require(
            sha256_bytes(row["source_text"].encode("utf-8")) == row["source_text_sha256"],
            f"source text hash drift: {line_number}",
        )
        identity = (row["unit_id"], row["unit_sha256"])
        require(identity not in index, f"duplicate source identity: {line_number}")
        index[identity] = row
    return index


def _load_partition_rows(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    rows = _read_jsonl(path, "partition manifest")
    require(len(rows) == eval_manifest.ROW_COUNT, "partition row count drift")
    require(sha256_file(path) == PINNED_PARTITION_SHA256, "partition manifest hash drift")
    index: dict[tuple[str, str], dict[str, Any]] = {}
    family_counts: Counter[str] = Counter()
    for line_number, row in enumerate(rows, start=1):
        require(set(row) == PARTITION_FIELDS, f"partition row shape drift: {line_number}")
        require(row["reason"] == "evaluation_only", f"partition reason drift: {line_number}")
        identity = (row["unit_id"], row["unit_sha256"])
        require(identity not in index, f"duplicate partition identity: {line_number}")
        index[identity] = row
        family_counts[row["family_id"]] += 1
    for family, count in FAMILY_COUNTS.items():
        require(family_counts.get(family, 0) == count, f"partition family count drift: {family}")
    return index


def _load_evaluation_manifest_rows(path: Path) -> list[dict[str, Any]]:
    raw, file_hash = _verified_private_file_bytes(path, "evaluation context manifest")
    require(file_hash == PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256, "evaluation context manifest drift")
    rows = _parse_jsonl_bytes(raw, "evaluation context manifest")
    require(len(rows) == eval_manifest.ROW_COUNT, "evaluation context manifest row count drift")
    prav_rows: list[dict[str, Any]] = []
    for line_number, row in enumerate(rows, start=1):
        if row["family_id"] in PRAVOPYS_FAMILIES:
            require(set(row) == EVAL_MANIFEST_FIELDS, f"evaluation manifest row shape drift: {line_number}")
            require(row["context_kind"] == "frozen_source_unit_text", f"unexpected context kind: {line_number}")
            require(row["complete_sentence_context"] is False, f"complete sentence overclaim: {line_number}")
            prav_rows.append(row)
    require(len(prav_rows) == ROW_COUNT, "pravopys held-out denominator drift")
    family_counts = Counter(row["family_id"] for row in prav_rows)
    require(dict(family_counts) == FAMILY_COUNTS, "pravopys family count drift")
    lane_counts = Counter(row["candidate_lane"] for row in prav_rows)
    require(dict(lane_counts) == LANE_COUNTS, "pravopys lane count drift")
    return sorted(prav_rows, key=lambda item: (item["family_id"], item["unit_id"]))


def _build_path_index(
    source_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, dict[tuple[str, ...], dict[str, Any]]]:
    path_index: dict[str, dict[tuple[str, ...], dict[str, Any]]] = {family: {} for family in PRAVOPYS_FAMILIES}
    duplicate_paths: list[tuple[str, tuple[str, ...]]] = []
    for row in source_index.values():
        family_id = row["family_id"]
        if family_id not in PRAVOPYS_FAMILIES:
            continue
        section_path = tuple(row["frozen_locator"]["section_path"])
        bucket = path_index[family_id]
        if section_path in bucket:
            duplicate_paths.append((family_id, section_path))
        else:
            bucket[section_path] = dict(row)
    require(not duplicate_paths, "duplicate parent path in materialization")
    return path_index


def _paragraph_parent_path(section_path: Sequence[str]) -> tuple[str, ...] | None:
    paragraph_indices = [index for index, token in enumerate(section_path) if token.startswith("paragraph:")]
    if len(paragraph_indices) > 1:
        return None
    if len(paragraph_indices) == 1:
        return tuple(section_path[: paragraph_indices[0] + 1])
    return tuple(section_path)


def _unique_codepoint_offsets(parent_text: str, unit_text: str) -> tuple[int, int]:
    occurrences = []
    start = 0
    while True:
        index = parent_text.find(unit_text, start)
        if index < 0:
            break
        occurrences.append(index)
        start = index + 1
    if not occurrences:
        raise PravopysEvaluationContextError("unit text not contained in parent")
    if len(occurrences) > 1:
        raise PravopysEvaluationContextError("unit text not unique in parent")
    start_offset = occurrences[0]
    end_offset = start_offset + len(unit_text)
    require(parent_text[start_offset:end_offset] == unit_text, "unicode offset round-trip drift")
    return start_offset, end_offset


def _resolve_parent_rule(
    source_row: Mapping[str, Any],
    *,
    path_index: Mapping[str, Mapping[tuple[str, ...], Mapping[str, Any]]],
) -> tuple[dict[str, Any] | None, str | None]:
    section_path = tuple(source_row["frozen_locator"]["section_path"])
    parent_path = _paragraph_parent_path(section_path)
    if parent_path is None:
        return None, "invalid_section_path"
    family_id = source_row["family_id"]
    parent_candidates = path_index[family_id]
    parent_matches = [
        candidate for candidate_path, candidate in parent_candidates.items() if candidate_path == parent_path
    ]
    if len(parent_matches) > 1:
        return None, "duplicate_parent_rule"
    parent_row = parent_matches[0] if parent_matches else None
    if parent_row is None:
        return None, "missing_parent_rule"
    unit_text = source_row["source_text"]
    parent_text = parent_row["source_text"]
    mapping_kind = "self_parent_rule" if parent_path == section_path else "child_parent_rule"
    if mapping_kind == "self_parent_rule":
        require(unit_text == parent_text, "self parent rule text drift")
        start_offset, end_offset = 0, len(unit_text)
    else:
        try:
            start_offset, end_offset = _unique_codepoint_offsets(parent_text, unit_text)
        except PravopysEvaluationContextError as exc:
            message = str(exc)
            if "not contained" in message:
                return None, "unit_text_not_contained_in_parent"
            return None, "unit_text_not_unique_in_parent"
    row: dict[str, Any] = {
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "family_id": family_id,
        "candidate_lane": source_row.get("candidate_lane"),
        "context_kind": "pravopys_parent_rule_context",
        "complete_sentence_context": False,
        "unit_text": unit_text,
        "unit_text_sha256": source_row["source_text_sha256"],
        "frozen_locator": source_row["frozen_locator"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
        "parent_section_path": list(parent_path),
        "parent_unit_id": parent_row["unit_id"],
        "parent_unit_sha256": parent_row["unit_sha256"],
        "parent_rule_mapping_kind": mapping_kind,
        "complete_parent_rule_context": parent_text,
        "complete_parent_rule_context_sha256": sha256_bytes(parent_text.encode("utf-8")),
        "unit_text_start_offset": start_offset,
        "unit_text_end_offset": end_offset,
    }
    require(set(row) == RECOVERED_ROW_FIELDS, "recovered row shape drift")
    return row, None


def _build_exclusion_row(
    *,
    manifest_row: Mapping[str, Any],
    source_row: Mapping[str, Any],
    parent_section_path: Sequence[str] | None,
    exclusion_reason_code: str,
) -> dict[str, Any]:
    require(exclusion_reason_code in EXCLUSION_REASONS, "unknown exclusion reason")
    row: dict[str, Any] = {
        "unit_id": manifest_row["unit_id"],
        "unit_sha256": manifest_row["unit_sha256"],
        "family_id": manifest_row["family_id"],
        "candidate_lane": manifest_row["candidate_lane"],
        "context_kind": "pravopys_typed_exclusion",
        "complete_sentence_context": False,
        "unit_text": source_row["source_text"],
        "unit_text_sha256": source_row["source_text_sha256"],
        "frozen_locator": source_row["frozen_locator"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
        "parent_section_path": list(parent_section_path) if parent_section_path is not None else [],
        "exclusion_reason_code": exclusion_reason_code,
    }
    require(set(row) == EXCLUDED_ROW_FIELDS, "exclusion row shape drift")
    return row


def build_context_rows(
    *,
    source_jsonl: Path,
    partition_path: Path,
    evaluation_manifest_path: Path,
    evaluation_manifest_receipt_path: Path,
) -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    _validate_evaluation_context_manifest_receipt(evaluation_manifest_receipt_path)
    source_raw, _source_hash = _verified_private_file_bytes(source_jsonl, "source materialization")
    source_index = _load_source_index_from_bytes(source_raw)
    partition_index = _load_partition_rows(partition_path)
    manifest_rows = _load_evaluation_manifest_rows(evaluation_manifest_path)
    path_index = _build_path_index(source_index)

    output_rows: list[dict[str, Any]] = []
    context_accounting: Counter[str] = Counter()
    mapping_accounting: Counter[str] = Counter()
    for manifest_row in manifest_rows:
        identity = (manifest_row["unit_id"], manifest_row["unit_sha256"])
        partition_row = partition_index.get(identity)
        require(partition_row is not None, f"partition identity missing: {manifest_row['unit_id']}")
        source_row = source_index.get(identity)
        require(source_row is not None, f"source identity missing: {manifest_row['unit_id']}")
        require(partition_row["family_id"] == manifest_row["family_id"], "partition/manifest family drift")
        require(source_row["family_id"] == manifest_row["family_id"], "source/manifest family drift")
        require(partition_row["candidate_lane"] == manifest_row["candidate_lane"], "lane drift")
        require(partition_row["source_text_sha256"] == manifest_row["source_text_sha256"], "manifest source hash drift")
        require(
            partition_row["frozen_locator_sha256"] == manifest_row["frozen_locator_sha256"],
            "manifest locator hash drift",
        )
        require(source_row["source_text_sha256"] == manifest_row["source_text_sha256"], "source/manifest hash drift")
        require(
            source_row["frozen_locator_sha256"] == manifest_row["frozen_locator_sha256"],
            "source/manifest locator drift",
        )
        require(source_row["source_text"] == manifest_row["source_text"], "source/manifest text drift")
        source_row = dict(source_row)
        source_row["candidate_lane"] = manifest_row["candidate_lane"]
        parent_path = _paragraph_parent_path(tuple(source_row["frozen_locator"]["section_path"]))
        recovered, exclusion_reason = _resolve_parent_rule(source_row, path_index=path_index)
        if exclusion_reason is not None:
            row = _build_exclusion_row(
                manifest_row=manifest_row,
                source_row=source_row,
                parent_section_path=parent_path,
                exclusion_reason_code=exclusion_reason,
            )
            context_accounting["pravopys_typed_exclusion"] += 1
        else:
            require(recovered is not None, "recovered row missing")
            row = recovered
            context_accounting["pravopys_parent_rule_context"] += 1
            mapping_accounting[row["parent_rule_mapping_kind"]] += 1
        output_rows.append(row)

    require(len(output_rows) == ROW_COUNT, "output row count drift")
    require(
        {key: context_accounting.get(key, 0) for key in CONTEXT_ACCOUNTING} == CONTEXT_ACCOUNTING,
        "context accounting drift",
    )
    require(dict(mapping_accounting) == MAPPING_ACCOUNTING, "mapping accounting drift")
    return output_rows, context_accounting, mapping_accounting


def _schema_validator() -> Draft202012Validator:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PravopysEvaluationContextError("cannot read receipt schema") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(receipt)
    errors = sorted(_schema_validator().iter_errors(value), key=lambda item: list(item.path))
    require(not errors, f"receipt schema violation: {errors[0].message if errors else ''}")
    require(value["receipt_sha256"] == receipt_sha256(value), "receipt body hash drift")
    require(value["provider_calls"] is False, "provider calls are forbidden")
    require(value["text_free"] is True, "public receipt must remain text-free")
    require(value["row_count"] == ROW_COUNT, "row count drift")
    require(value["context_accounting"] == CONTEXT_ACCOUNTING, "context accounting drift")
    require(value["mapping_accounting"] == MAPPING_ACCOUNTING, "mapping accounting drift")
    require(value["family_counts"] == FAMILY_COUNTS, "family count drift")
    require(value["lanes"] == LANE_COUNTS, "lane count drift")
    require(value["labels_present"] is False, "labels must remain absent")
    require(value["gates"]["source_authoring_blocked"] is True, "source authoring opened")
    require(value["gates"]["phase3_complete"] is False, "phase 3 overclaim")
    require(value["gates"]["phase4_blocked"] is True, "phase 4 opened")
    bindings = value["bindings"]
    for key, expected in {
        "source_units_jsonl_sha256": PINNED_SOURCE_UNITS_JSONL_SHA256,
        "partition_manifest_sha256": PINNED_PARTITION_SHA256,
        "evaluation_context_manifest_jsonl_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256,
        "evaluation_context_manifest_receipt_body_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_BODY_SHA256,
        "evaluation_context_manifest_receipt_file_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256,
        "pravopys_2019_pdf_sha256": PINNED_PRAVOPYS_2019_PDF_SHA256,
        "pravopys_2026_pdf_sha256": PINNED_PRAVOPYS_2026_PDF_SHA256,
        "custody_tarball_sha256": PINNED_CUSTODY_TARBALL_SHA256,
    }.items():
        require(bindings[key] == expected, f"binding drift: {key}")
    require(
        bindings["implementation_sha256"] in {
            "7a6e73714cc7b4723489432ddde5435edd94e756ff46e86aa1327ab31418361c",
            sha256_file(SCRIPT_PATH),
        },
        "implementation binding drift",
    )
    require(bindings["receipt_schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    return value


def _prepare_private_output(path: Path) -> None:
    _reject_symlink_components(path, "private output")
    parent = path.parent
    if parent.exists():
        require(parent.is_dir() and not parent.is_symlink(), "private output parent must be a real directory")
        require(stat.S_IMODE(parent.stat().st_mode) == PRIVATE_DIR_MODE, "private output directory must be mode 0700")
    else:
        parent.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        os.chmod(parent, PRIVATE_DIR_MODE)
    if path.exists():
        require(path.is_file() and not path.is_symlink(), "private output path is unsafe")
        require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_FILE_MODE, "existing private output must be mode 0600")


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    if mode & 0o077:
        raise PravopysEvaluationContextError(f"private write refuses group/other bits: {mode:04o}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent != path:
        os.chmod(path.parent, PRIVATE_DIR_MODE if stat.S_ISDIR(path.parent.stat().st_mode) else mode)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_text_free_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _reject_symlink_components(path, "text-free receipt")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(receipt)
    if path.exists():
        _regular_text_free_receipt(path, "text-free receipt")
        require(path.read_bytes() == payload, "refusing to overwrite an immutable text-free receipt")
        return
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            os.chmod(temporary, PRIVATE_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _drive_item_id(path: Path) -> str:
    resolved = path.resolve()
    try:
        drive_roots = [
            candidate.resolve()
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise PravopysEvaluationContextError("cannot inspect configured Google Drive mounts") from exc
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
            raise PravopysEvaluationContextError(
                f"artifact did not acquire Google Drive provider identity within {timeout_seconds:g} seconds"
            ) from last_error
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))


def _verify_drive_readback(path: Path, expected_sha256: str) -> None:
    readback = sha256_file(path)
    require(readback == expected_sha256, "Drive read-back hash mismatch")
    _wait_for_drive_item_id(path)


def _safe_tar_member_name(name: str) -> None:
    require(name == name.strip(), "tar member name has surrounding whitespace")
    require(not name.startswith("/"), "tar member absolute path forbidden")
    require(".." not in Path(name).parts, "tar member traversal forbidden")


def _extract_tarball_members(tarball: Path, destination: Path) -> dict[str, Path]:
    require(tarball.is_file() and not tarball.is_symlink(), "custody tarball must be a regular file")
    require(sha256_file(tarball) == PINNED_CUSTODY_TARBALL_SHA256, "custody tarball hash drift")
    destination.mkdir(parents=True, exist_ok=True)
    os.chmod(destination, PRIVATE_DIR_MODE)
    extracted: dict[str, Path] = {}
    seen_names: set[str] = set()
    with tarfile.open(tarball, mode="r:gz") as archive:
        file_names = [member.name for member in archive.getmembers() if member.isfile()]
        require(len(file_names) == len(set(file_names)), "duplicate tarball member names")
        members_by_name = {member.name: member for member in archive.getmembers()}
        for key, member_name in TARBALL_MEMBERS.items():
            _safe_tar_member_name(member_name)
            require(member_name not in seen_names, f"duplicate tarball member request: {member_name}")
            seen_names.add(member_name)
            member = members_by_name.get(member_name)
            require(member is not None, f"missing tarball member: {member_name}")
            require(member.isreg(), f"tarball member must be a regular file: {member_name}")
            require(not member.issym() and not member.islnk(), f"unsafe tarball member: {member_name}")
            stream = archive.extractfile(member)
            require(stream is not None, f"cannot extract tarball member: {member_name}")
            payload = stream.read()
            expected_hash = {
                "pravopys_2019_pdf": PINNED_PRAVOPYS_2019_PDF_SHA256,
                "pravopys_2026_pdf": PINNED_PRAVOPYS_2026_PDF_SHA256,
            }.get(key)
            if expected_hash is not None:
                require(sha256_bytes(payload) == expected_hash, f"{key} hash drift")
            target = destination / Path(member_name).name
            _atomic_write(target, payload, PRIVATE_FILE_MODE)
            extracted[key] = target
    return extracted


def _build_receipt(
    *,
    context_payload: bytes,
    started_at: str,
    completed_at: str,
    custody_tarball_sha256: str,
) -> dict[str, Any]:
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
            "evaluation_context_manifest_jsonl_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256,
            "evaluation_context_manifest_receipt_body_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_BODY_SHA256,
            "evaluation_context_manifest_receipt_file_sha256": PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256,
            "pravopys_2019_pdf_sha256": PINNED_PRAVOPYS_2019_PDF_SHA256,
            "pravopys_2026_pdf_sha256": PINNED_PRAVOPYS_2026_PDF_SHA256,
            "custody_tarball_sha256": custody_tarball_sha256,
        },
        "row_count": ROW_COUNT,
        "family_counts": FAMILY_COUNTS,
        "lanes": LANE_COUNTS,
        "context_accounting": CONTEXT_ACCOUNTING,
        "mapping_accounting": MAPPING_ACCOUNTING,
        "context": {
            "private_jsonl_sha256": sha256_bytes(context_payload),
            "private_jsonl_bytes": len(context_payload),
            "private_jsonl_rows": ROW_COUNT,
        },
        "labels_present": False,
        "gates": {
            "pravopys_evaluation_context_ready": True,
            "semantic_labels_present": False,
            "source_authoring_blocked": True,
            "complete_evaluation_package_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt["receipt_sha256"] = receipt_sha256(receipt)
    return validate_receipt(receipt)


def materialize(
    *,
    source_jsonl: Path,
    partition_path: Path,
    evaluation_manifest_path: Path,
    evaluation_manifest_receipt_path: Path,
    private_output: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
    custody_tarball_sha256: str = PINNED_CUSTODY_TARBALL_SHA256,
) -> dict[str, Any]:
    rows, _context_accounting, _mapping_accounting = build_context_rows(
        source_jsonl=source_jsonl,
        partition_path=partition_path,
        evaluation_manifest_path=evaluation_manifest_path,
        evaluation_manifest_receipt_path=evaluation_manifest_receipt_path,
    )
    effective_completed_at = completed_at or utc_now()
    payload = b"".join(canonical_bytes(row) for row in rows)
    receipt = _build_receipt(
        context_payload=payload,
        started_at=started_at,
        completed_at=effective_completed_at,
        custody_tarball_sha256=custody_tarball_sha256,
    )
    _prepare_private_output(private_output)
    if private_output.exists():
        require(private_output.read_bytes() == payload, "refusing to overwrite a changed private context artifact")
    else:
        _atomic_write(private_output, payload, PRIVATE_FILE_MODE)
    _write_text_free_receipt(public_receipt_path, receipt)
    return receipt


def _write_checksums(directory: Path, files: Mapping[str, Path]) -> Path:
    lines = [f"{sha256_file(path)}  {name}\n" for name, path in sorted(files.items())]
    checksums_path = directory / CHECKSUMS_FILENAME
    _atomic_write(checksums_path, "".join(lines).encode("utf-8"), PRIVATE_FILE_MODE)
    return checksums_path


def _build_custody_receipt(
    *,
    private_context: Path,
    checksums_path: Path,
    public_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    context_sha256 = sha256_file(private_context)
    checksums_sha256 = sha256_file(checksums_path)
    provider_id = _wait_for_drive_item_id(private_context)
    body = {
        "schema_version": "phase3_pravopys_evaluation_context_custody_receipt_v1",
        "text_free": True,
        "provider_calls": False,
        "artifacts": {
            "private_context_filename": PRIVATE_FILENAME,
            "private_context_sha256": context_sha256,
            "checksums_filename": CHECKSUMS_FILENAME,
            "checksums_sha256": checksums_sha256,
            "public_receipt_sha256": public_receipt["receipt_sha256"],
        },
        "custody": {
            "google_drive_custody": True,
            "google_drive_mount_containment_verified": True,
            "google_drive_provider_identity_present": True,
            "google_drive_provider_identity_sha256": sha256_bytes(provider_id.encode("utf-8")),
            "all_new_files_uploaded": True,
            "all_new_files_uploading": False,
            "all_new_files_readback_hash_match": True,
            "private_files_mode_0600": stat.S_IMODE(private_context.stat().st_mode) == PRIVATE_FILE_MODE,
            "private_directory_mode_0700": stat.S_IMODE(private_context.parent.stat().st_mode) == PRIVATE_DIR_MODE,
        },
        "gates": {
            "pravopys_evaluation_context_ready": True,
            "semantic_labels_present": False,
            "source_authoring_blocked": True,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    body["receipt_sha256"] = receipt_sha256(body)
    return body


def finish_custody(
    *,
    drive_backup_dir: Path,
    public_receipt_path: Path,
) -> dict[str, Any]:
    _reject_symlink_components(drive_backup_dir, "drive backup directory")
    private_output = drive_backup_dir / PRIVATE_FILENAME
    _regular_private(private_output, "private context artifact")
    receipt = _read_text_free_receipt_json(public_receipt_path, "text-free receipt")
    validated = validate_receipt(receipt)
    _verify_drive_readback(private_output, validated["context"]["private_jsonl_sha256"])
    checksums_path = _write_checksums(drive_backup_dir, {PRIVATE_FILENAME: private_output})
    custody_receipt = _build_custody_receipt(
        private_context=private_output,
        checksums_path=checksums_path,
        public_receipt=validated,
    )
    custody_path = drive_backup_dir / CUSTODY_RECEIPT_FILENAME
    _atomic_write(custody_path, canonical_bytes(custody_receipt), PRIVATE_FILE_MODE)
    _verify_drive_readback(custody_path, sha256_bytes(canonical_bytes(custody_receipt)))
    _verify_drive_readback(checksums_path, sha256_file(checksums_path))
    return validated


def production_run(
    *,
    custody_tarball: Path,
    evaluation_manifest_path: Path,
    evaluation_manifest_receipt_path: Path,
    drive_backup_dir: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
) -> dict[str, Any]:
    require(drive_backup_dir.parent.is_dir(), "drive backup parent must exist")
    _reject_symlink_components(drive_backup_dir, "drive backup directory")
    drive_backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(drive_backup_dir, PRIVATE_DIR_MODE)
    temp_root = Path(tempfile.mkdtemp(prefix="phase3-pravopys-eval-context-", dir=None))
    os.chmod(temp_root, PRIVATE_DIR_MODE)
    try:
        extracted = _extract_tarball_members(custody_tarball, temp_root)
        private_output = drive_backup_dir / PRIVATE_FILENAME
        receipt = materialize(
            source_jsonl=extracted["source_jsonl"],
            partition_path=extracted["partition"],
            evaluation_manifest_path=evaluation_manifest_path,
            evaluation_manifest_receipt_path=evaluation_manifest_receipt_path,
            private_output=private_output,
            public_receipt_path=public_receipt_path,
            started_at=started_at,
            completed_at=completed_at,
            custody_tarball_sha256=PINNED_CUSTODY_TARBALL_SHA256,
        )
        _verify_drive_readback(private_output, receipt["context"]["private_jsonl_sha256"])
        checksums_path = _write_checksums(drive_backup_dir, {PRIVATE_FILENAME: private_output})
        custody_receipt = _build_custody_receipt(
            private_context=private_output,
            checksums_path=checksums_path,
            public_receipt=receipt,
        )
        custody_path = drive_backup_dir / CUSTODY_RECEIPT_FILENAME
        _atomic_write(custody_path, canonical_bytes(custody_receipt), PRIVATE_FILE_MODE)
        _verify_drive_readback(custody_path, sha256_bytes(canonical_bytes(custody_receipt)))
        _verify_drive_readback(checksums_path, sha256_file(checksums_path))
        return receipt
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def verify_existing(
    *,
    source_jsonl: Path,
    partition_path: Path,
    evaluation_manifest_path: Path,
    evaluation_manifest_receipt_path: Path,
    private_output: Path,
    public_receipt_path: Path,
) -> dict[str, Any]:
    rows, context_accounting, mapping_accounting = build_context_rows(
        source_jsonl=source_jsonl,
        partition_path=partition_path,
        evaluation_manifest_path=evaluation_manifest_path,
        evaluation_manifest_receipt_path=evaluation_manifest_receipt_path,
    )
    payload = b"".join(canonical_bytes(row) for row in rows)
    _regular_private(private_output, "private context artifact")
    require(private_output.read_bytes() == payload, "private context artifact drift")
    receipt = _read_text_free_receipt_json(public_receipt_path, "text-free receipt")
    validated = validate_receipt(receipt)
    require(validated["context"]["private_jsonl_sha256"] == sha256_bytes(payload), "public receipt context hash drift")
    require(
        {key: context_accounting.get(key, 0) for key in CONTEXT_ACCOUNTING} == CONTEXT_ACCOUNTING,
        "context accounting drift on verify",
    )
    require(dict(mapping_accounting) == MAPPING_ACCOUNTING, "mapping accounting drift on verify")
    return validated


def _reject_live_database(path: Path | None) -> None:
    if path is None:
        return
    require(not path.exists() or path.name == ".keep", "live database rematerialization is forbidden")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build the private context artifact and public receipt")
    build.add_argument("--source-jsonl", type=Path, required=True)
    build.add_argument("--partition", type=Path, required=True)
    build.add_argument("--evaluation-manifest", type=Path, required=True)
    build.add_argument("--evaluation-manifest-receipt", type=Path, required=True)
    build.add_argument("--private-output", type=Path, required=True)
    build.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    build.add_argument("--started-at")
    build.add_argument("--completed-at")
    build.add_argument("--database", type=Path, help=argparse.SUPPRESS)

    verify = subparsers.add_parser("verify", help="verify an existing context artifact and receipt")
    verify.add_argument("--source-jsonl", type=Path, required=True)
    verify.add_argument("--partition", type=Path, required=True)
    verify.add_argument("--evaluation-manifest", type=Path, required=True)
    verify.add_argument("--evaluation-manifest-receipt", type=Path, required=True)
    verify.add_argument("--private-output", type=Path, required=True)
    verify.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)

    production = subparsers.add_parser("production", help="extract custody inputs and publish to Drive")
    production.add_argument("--custody-tarball", type=Path, required=True)
    production.add_argument("--evaluation-manifest", type=Path, required=True)
    production.add_argument("--evaluation-manifest-receipt", type=Path, required=True)
    production.add_argument("--drive-backup-dir", type=Path, required=True)
    production.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    production.add_argument("--started-at")
    production.add_argument("--completed-at")

    finish = subparsers.add_parser("finish-custody", help="complete Drive custody for an existing context artifact")
    finish.add_argument("--drive-backup-dir", type=Path, required=True)
    finish.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            _reject_live_database(getattr(args, "database", None))
            receipt = materialize(
                source_jsonl=args.source_jsonl,
                partition_path=args.partition,
                evaluation_manifest_path=args.evaluation_manifest,
                evaluation_manifest_receipt_path=args.evaluation_manifest_receipt,
                private_output=args.private_output,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
        elif args.command == "verify":
            receipt = verify_existing(
                source_jsonl=args.source_jsonl,
                partition_path=args.partition,
                evaluation_manifest_path=args.evaluation_manifest,
                evaluation_manifest_receipt_path=args.evaluation_manifest_receipt,
                private_output=args.private_output,
                public_receipt_path=args.public_receipt,
            )
        elif args.command == "finish-custody":
            receipt = finish_custody(
                drive_backup_dir=args.drive_backup_dir,
                public_receipt_path=args.public_receipt,
            )
        else:
            receipt = production_run(
                custody_tarball=args.custody_tarball,
                evaluation_manifest_path=args.evaluation_manifest,
                evaluation_manifest_receipt_path=args.evaluation_manifest_receipt,
                drive_backup_dir=args.drive_backup_dir,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
    except (OSError, PravopysEvaluationContextError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
