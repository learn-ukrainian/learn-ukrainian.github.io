#!/usr/bin/env python3
"""Join the frozen 9,392 held-out identities to evaluation-scoped context.

The adapter binds the pinned 67,041-row source materialization, the sealed
evaluation partition, and current-main UA-GEC closure-v2 complete-context
records.  It emits one private JSONL row per held-out identity plus a
text-free public receipt.  It does not label gold, author rules, promote
Cycle002 diagnostics, or claim Phase 3 completion.
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

from scripts.projects.open_model_data import phase3_ua_gec_complete_context as ua_context

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCRIPT_PATH = Path(__file__).resolve()
SCHEMA_PATH = DATA / "contracts/phase3_evaluation_context_manifest_receipt_v1.schema.json"
DEFAULT_PUBLIC_RECEIPT = DATA / "evidence/phase3_evaluation_context_manifest_receipt_v1.json"
PRIVATE_FILENAME = "evaluation_context_manifest_v1.jsonl"
CUSTODY_RECEIPT_FILENAME = "phase3_evaluation_context_manifest_custody_receipt_v1.json"
CHECKSUMS_FILENAME = "SHA256SUMS"
SCHEMA_VERSION = "phase3_evaluation_context_manifest_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_evaluation_context_manifest_v1"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
CLOUD_STORAGE_ROOT = Path.home() / "Library/CloudStorage"
ROW_COUNT = 9_392
V2_SOURCE_UNITS = 67_041
V2_UA_GEC_UNITS = 8_937
V2_EVALUATION_IDENTITIES = 9_392
CYCLE002_IDENTITIES = 9_392
CYCLE002_AGREEMENTS = 6_462
CYCLE002_DISAGREEMENTS = 2_930
CYCLE002_UA_GEC_EVIDENCE_ROWS = 906
CYCLE002_NON_AUTHORITATIVE_ROWS = 8_486
FROZEN_EVIDENCE_BACKED_LABELS = 0
LANE_COUNTS = {"clean_modern": 2_000, "phenomenon_strata": 7_392}
MATERIALIZATION_FAMILY_COUNTS = {
    "antonenko_style_guide": 342,
    "ua_gec": 8_937,
    "school_textbooks": 54_979,
    "antonenko_textbook_representation": 169,
    "calque_inventory": 58,
    "pravopys_2019_complete": 1_090,
    "pravopys_2026_complete": 1_466,
    "other_normative_style_inventory": 0,
}
SEALED_FAMILY_COUNTS = {
    "school_textbooks": 8_005,
    "ua_gec": 909,
    "pravopys_2026_complete": 235,
    "pravopys_2019_complete": 178,
    "antonenko_style_guide": 58,
    "calque_inventory": 7,
    "antonenko_textbook_representation": 0,
    "other_normative_style_inventory": 0,
}
CONTEXT_ACCOUNTING = {
    "ua_gec_complete_context": 907,
    "ua_gec_typed_exclusion": 2,
    "frozen_source_unit_text": 8_483,
}
PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256 = "39061cc9c76d3cc510497dfb1df19639c07f76eb933599a3930137bf60ee31a0"
PINNED_SOURCE_UNITS_JSONL_SHA256 = "e9d89b8fae5193a29a8c3dd055f464fc1290c18f507b669f3efb0720644f6d8c"
PINNED_MATERIALIZATION_RECEIPT_FILE_SHA256 = "45ee76edddb060f8719b0adf03afb954979f9af0c3c9290a0c822d138a75110f"
PINNED_MATERIALIZATION_RECEIPT_BODY_SHA256 = "c5f0a6ed23dbea8a3157862e476e79f1ca7af50db2dce91e38ac36a1c8ef3d1f"
PINNED_PARTITION_SHA256 = "3797e005d7c461f192dacb06e23a9028121bd73cb240f2c2851953a83955aa7d"
PINNED_EVALUATION_FREEZE_FILE_SHA256 = "00005536c7783a5f88211cca7aa52246d3fc66fd81d6f3cca666e133ddcf1bba"
PINNED_EVALUATION_FREEZE_BODY_SHA256 = "6c73258b3702070fde7667f6748fa4f63e0bae28484ffdf4712f5db1ce7721bf"
PINNED_UA_GEC_CONTEXT_SHA256 = "d214ebfb1c16c0b4cee5ad1150eada58b8e415e0d8f47b4bb018edec39ff7940"
PINNED_UA_GEC_EXCLUSIONS_SHA256 = "f4e02163a7e19cc0dd64f6fb5bfffc6d14bd82f49f2bcc088f15e6b845ae735d"
PINNED_UA_GEC_CONTEXT_RECEIPT_FILE_SHA256 = "d377fb4de8b970adf9e21fedacdc631cc4c56d17e37407ceafea20fcfcbc7729"
PINNED_UA_GEC_CONTEXT_RECEIPT_BODY_SHA256 = "b60077eae9fb50310dff04e08c1b1db6d53fa14b7556052d3c904088366b60a8"
PINNED_CUSTODY_TARBALL_SHA256 = "364055091f44e1c7ff4df71da81d7a43460100fd8a25cd06e7c820e1b114bc08"
TARBALL_MEMBERS = {
    "source_jsonl": "batch_state/phase3-private/v21-cycle001/source-materialization/source_units_v1.jsonl",
    "materialization_receipt": "batch_state/phase3-private/v21-cycle001/source-materialization-public.json",
    "partition": "batch_state/phase3-private/v21-cycle001/evaluation-partition/partition_manifest_v1.jsonl",
    "evaluation_freeze_receipt": "batch_state/phase3-private/v21-cycle001/evaluation-partition-public.json",
}
CONTEXT_KINDS = frozenset({"ua_gec_complete_context", "ua_gec_typed_exclusion", "frozen_source_unit_text"})
PARTITION_FIELDS = frozenset(
    {
        "family_id",
        "unit_id",
        "unit_sha256",
        "reason",
        "candidate_lane",
        "source_text_sha256",
        "frozen_locator_sha256",
    }
)
SOURCE_FIELDS = frozenset(
    {
        "family_id",
        "unit_id",
        "unit_sha256",
        "frozen_locator",
        "frozen_locator_sha256",
        "document_or_edition_identity",
        "source_text",
        "source_record",
        "source_text_sha256",
    }
)


class EvaluationContextManifestError(ValueError):
    """The held-out context manifest cannot be built or verified safely."""


class DriveIdentityPendingError(EvaluationContextManifestError):
    """DriveFS has not yet assigned provider identity to a freshly written artifact."""


DRIVE_IDENTITY_TIMEOUT_SECONDS = 120.0
DRIVE_IDENTITY_POLL_SECONDS = 2.0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationContextManifestError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise EvaluationContextManifestError(f"cannot read artifact: {path}") from exc
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
        raise EvaluationContextManifestError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular file")
    require(stat.S_IMODE(state.st_mode) == PRIVATE_FILE_MODE, f"{label} permissions must be 0600")


def _strict_json_bytes(raw: bytes, label: str, top: type[Any] = dict) -> Any:
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationContextManifestError(f"invalid strict JSON: {label}") from exc
    require(isinstance(value, top), f"{label} top-level type drift")
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular_private(path, label)
    value = _strict_json_bytes(path.read_bytes(), label)
    require(isinstance(value, dict), f"{label} must be an object")
    return value


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


def _validate_materialization_receipt(path: Path, source_jsonl: Path) -> dict[str, Any]:
    receipt = _read_json(path, "materialization receipt")
    require(
        receipt.get("schema_version") == "phase3_source_unit_materialization_receipt_v1",
        "wrong materialization receipt",
    )
    require(receipt.get("private_record_count") == V2_SOURCE_UNITS, "materialization denominator drift")
    require(
        receipt.get("source_universe_receipt_sha256") == PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256, "source universe drift"
    )
    require(sha256_file(path) == PINNED_MATERIALIZATION_RECEIPT_FILE_SHA256, "materialization receipt file drift")
    require(receipt_sha256(receipt) == PINNED_MATERIALIZATION_RECEIPT_BODY_SHA256, "materialization receipt body drift")
    require(
        receipt.get("private_jsonl_sha256") == sha256_file(source_jsonl) == PINNED_SOURCE_UNITS_JSONL_SHA256,
        "source jsonl drift",
    )
    require(receipt.get("family_counts") == MATERIALIZATION_FAMILY_COUNTS, "family counts drift")
    return receipt


def _validate_evaluation_freeze_receipt(path: Path, partition: Path) -> dict[str, Any]:
    receipt = _read_json(path, "evaluation freeze receipt")
    require(
        receipt.get("schema_version") == "phase3_evaluation_partition_receipt_v1", "wrong evaluation freeze receipt"
    )
    require(sha256_file(path) == PINNED_EVALUATION_FREEZE_FILE_SHA256, "evaluation freeze file drift")
    require(receipt_sha256(receipt) == PINNED_EVALUATION_FREEZE_BODY_SHA256, "evaluation freeze body drift")
    artifact_hashes = receipt.get("artifact_hashes", {})
    require(
        artifact_hashes.get("partition_manifest_sha256") == sha256_file(partition) == PINNED_PARTITION_SHA256,
        "partition drift",
    )
    aggregates = receipt.get("aggregates", {})
    require(aggregates.get("sealed_evaluation_total") == ROW_COUNT, "sealed evaluation total drift")
    require(aggregates.get("clean_modern_candidate_total") == LANE_COUNTS["clean_modern"], "clean modern drift")
    return receipt


def _validate_ua_gec_context_receipt(path: Path) -> dict[str, Any]:
    receipt = _read_json(path, "UA-GEC complete-context receipt")
    require(sha256_file(path) == PINNED_UA_GEC_CONTEXT_RECEIPT_FILE_SHA256, "UA-GEC receipt file drift")
    try:
        validated = ua_context.validate_receipt(receipt)
    except ua_context.UaGecCompleteContextError as exc:
        raise EvaluationContextManifestError(str(exc)) from exc
    require(receipt_sha256(validated) == PINNED_UA_GEC_CONTEXT_RECEIPT_BODY_SHA256, "UA-GEC receipt body drift")
    return validated


def _load_source_index(path: Path, receipt: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows = _read_jsonl(path, "source materialization")
    require(len(rows) == V2_SOURCE_UNITS, "source materialization row count drift")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    require(digest.hexdigest() == receipt["private_jsonl_sha256"], "source materialization stream drift")
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


def _load_partition_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_jsonl(path, "partition manifest")
    require(len(rows) == ROW_COUNT, "partition row count drift")
    require(sha256_file(path) == PINNED_PARTITION_SHA256, "partition manifest hash drift")
    seen: set[tuple[str, str]] = set()
    family_counts: Counter[str] = Counter()
    lane_counts: Counter[str] = Counter()
    for line_number, row in enumerate(rows, start=1):
        require(set(row) == PARTITION_FIELDS, f"partition row shape drift: {line_number}")
        require(row["reason"] == "evaluation_only", f"partition reason drift: {line_number}")
        identity = (row["unit_id"], row["unit_sha256"])
        require(identity not in seen, f"duplicate partition identity: {line_number}")
        seen.add(identity)
        family_counts[row["family_id"]] += 1
        lane_counts[row["candidate_lane"]] += 1
    require(
        {family: family_counts.get(family, 0) for family in SEALED_FAMILY_COUNTS} == SEALED_FAMILY_COUNTS,
        "partition family counts drift",
    )
    require(
        {lane: lane_counts.get(lane, 0) for lane in LANE_COUNTS} == LANE_COUNTS,
        "partition lane counts drift",
    )
    return sorted(rows, key=lambda item: (item["family_id"], item["unit_id"]))


def _load_ua_gec_context_index(path: Path) -> dict[str, dict[str, Any]]:
    _regular_private(path, "UA-GEC complete-context JSONL")
    require(sha256_file(path) == PINNED_UA_GEC_CONTEXT_SHA256, "UA-GEC context JSONL drift")
    index: dict[str, dict[str, Any]] = {}
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            require(raw.endswith(b"\n"), f"UA-GEC context row lacks LF: {line_number}")
            record = _strict_json_bytes(raw, f"UA-GEC context:{line_number}")
            locator = record["document"]["frozen_locator"]
            unit_ids = locator["v2_unit_ids"]
            require(isinstance(unit_ids, list) and unit_ids, f"UA-GEC context missing v2_unit_ids: {line_number}")
            for unit_id in unit_ids:
                require(isinstance(unit_id, str) and unit_id, f"invalid UA-GEC unit id: {line_number}")
                require(unit_id not in index, f"duplicate UA-GEC unit mapping: {unit_id}")
                index[unit_id] = record
    return index


def _load_ua_gec_exclusions(path: Path) -> dict[str, str]:
    _regular_private(path, "UA-GEC exclusions JSONL")
    require(sha256_file(path) == PINNED_UA_GEC_EXCLUSIONS_SHA256, "UA-GEC exclusions drift")
    exclusions: dict[str, str] = {}
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            require(raw.endswith(b"\n"), f"UA-GEC exclusion row lacks LF: {line_number}")
            row = _strict_json_bytes(raw, f"UA-GEC exclusion:{line_number}")
            require(set(row) == {"unit_id", "reason"}, f"UA-GEC exclusion shape drift: {line_number}")
            unit_id = row["unit_id"]
            reason = row["reason"]
            require(isinstance(unit_id, str) and unit_id, f"invalid exclusion unit id: {line_number}")
            require(isinstance(reason, str) and reason, f"invalid exclusion reason: {line_number}")
            require(unit_id not in exclusions, f"duplicate UA-GEC exclusion: {unit_id}")
            exclusions[unit_id] = reason
    return exclusions


def _context_record_sha256(record: Mapping[str, Any]) -> str:
    return sha256_value(record)


def _build_manifest_row(
    partition_row: Mapping[str, Any],
    source_row: Mapping[str, Any],
    *,
    context_kind: str,
    complete_sentence_context: bool,
    ua_gec_record: Mapping[str, Any] | None = None,
    exclusion_reason_code: str | None = None,
) -> dict[str, Any]:
    require(context_kind in CONTEXT_KINDS, "unknown context kind")
    require(source_row["unit_id"] == partition_row["unit_id"], "partition/source unit id drift")
    require(source_row["unit_sha256"] == partition_row["unit_sha256"], "partition/source unit hash drift")
    require(source_row["family_id"] == partition_row["family_id"], "partition/source family drift")
    require(partition_row["source_text_sha256"] == source_row["source_text_sha256"], "partition source hash drift")
    require(partition_row["frozen_locator_sha256"] == source_row["frozen_locator_sha256"], "partition locator drift")
    row: dict[str, Any] = {
        "unit_id": partition_row["unit_id"],
        "unit_sha256": partition_row["unit_sha256"],
        "family_id": partition_row["family_id"],
        "candidate_lane": partition_row["candidate_lane"],
        "context_kind": context_kind,
        "complete_sentence_context": complete_sentence_context,
    }
    if context_kind == "ua_gec_complete_context":
        require(partition_row["family_id"] == "ua_gec", "non-UA-GEC row cannot use complete UA-GEC context")
        require(ua_gec_record is not None, "UA-GEC context record missing")
        require(exclusion_reason_code is None, "complete-context row cannot carry an exclusion reason")
        row["context_record_sha256"] = _context_record_sha256(ua_gec_record)
        row["representation"] = ua_gec_record
        require(complete_sentence_context is True, "UA-GEC complete-context rows must be complete sentence context")
    elif context_kind == "ua_gec_typed_exclusion":
        require(partition_row["family_id"] == "ua_gec", "typed exclusion applies only to UA-GEC")
        require(exclusion_reason_code, "typed exclusion requires a reason code")
        require(ua_gec_record is None, "typed exclusion cannot embed a complete-context record")
        require(complete_sentence_context is False, "typed exclusion is not complete sentence context")
        row["exclusion_reason_code"] = exclusion_reason_code
        row["source_text"] = source_row["source_text"]
        row["source_text_sha256"] = source_row["source_text_sha256"]
        row["frozen_locator_sha256"] = source_row["frozen_locator_sha256"]
    else:
        require(
            partition_row["family_id"] != "ua_gec" or exclusion_reason_code is not None or ua_gec_record is None,
            "UA-GEC fragment misuse",
        )
        require(ua_gec_record is None, "frozen source-unit rows cannot embed UA-GEC complete context")
        require(exclusion_reason_code is None, "frozen source-unit rows cannot carry exclusion reasons")
        require(complete_sentence_context is False, "frozen source-unit text is never complete sentence context")
        row["source_text"] = source_row["source_text"]
        row["source_text_sha256"] = source_row["source_text_sha256"]
        row["frozen_locator_sha256"] = source_row["frozen_locator_sha256"]
    require("qualified_human" not in row, "manifest rows cannot claim qualified_human authority")
    return row


def build_manifest(
    *,
    source_jsonl: Path,
    materialization_receipt_path: Path,
    partition_path: Path,
    evaluation_freeze_receipt_path: Path,
    ua_gec_context_path: Path,
    ua_gec_exclusions_path: Path,
    ua_gec_receipt_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Counter[str]]]:
    materialization_receipt = _validate_materialization_receipt(materialization_receipt_path, source_jsonl)
    _validate_evaluation_freeze_receipt(evaluation_freeze_receipt_path, partition_path)
    _validate_ua_gec_context_receipt(ua_gec_receipt_path)
    require(sha256_file(ua_gec_context_path) == PINNED_UA_GEC_CONTEXT_SHA256, "UA-GEC context path drift")
    require(sha256_file(ua_gec_exclusions_path) == PINNED_UA_GEC_EXCLUSIONS_SHA256, "UA-GEC exclusions path drift")

    source_index = _load_source_index(source_jsonl, materialization_receipt)
    partition_rows = _load_partition_rows(partition_path)
    context_index = _load_ua_gec_context_index(ua_gec_context_path)
    exclusions = _load_ua_gec_exclusions(ua_gec_exclusions_path)

    manifest_rows: list[dict[str, Any]] = []
    accounting: Counter[str] = Counter()
    for partition_row in partition_rows:
        identity = (partition_row["unit_id"], partition_row["unit_sha256"])
        source_row = source_index.get(identity)
        require(
            source_row is not None,
            f"partition identity missing from source materialization: {partition_row['unit_id']}",
        )
        unit_id = partition_row["unit_id"]
        if unit_id in exclusions:
            row = _build_manifest_row(
                partition_row,
                source_row,
                context_kind="ua_gec_typed_exclusion",
                complete_sentence_context=False,
                exclusion_reason_code=exclusions[unit_id],
            )
        elif unit_id in context_index:
            row = _build_manifest_row(
                partition_row,
                source_row,
                context_kind="ua_gec_complete_context",
                complete_sentence_context=True,
                ua_gec_record=context_index[unit_id],
            )
        else:
            row = _build_manifest_row(
                partition_row,
                source_row,
                context_kind="frozen_source_unit_text",
                complete_sentence_context=False,
            )
        accounting[row["context_kind"]] += 1
        manifest_rows.append(row)

    require(len(manifest_rows) == ROW_COUNT, "manifest row count drift")
    require(dict(accounting) == CONTEXT_ACCOUNTING, "context accounting drift")
    return manifest_rows, accounting


def _schema_validator() -> Draft202012Validator:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationContextManifestError("cannot read manifest receipt schema") from exc
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
    require(value["family_counts"] == SEALED_FAMILY_COUNTS, "family count drift")
    require(value["lanes"] == LANE_COUNTS, "lane count drift")
    require(value["frozen_evidence_backed_labels"] == FROZEN_EVIDENCE_BACKED_LABELS, "label denominator drift")
    require(value["labels_present"] is False, "labels must remain absent")
    require(value["gates"]["source_authoring_blocked"] is True, "source authoring opened")
    require(value["gates"]["phase3_complete"] is False, "phase 3 overclaim")
    require(value["gates"]["phase4_blocked"] is True, "phase 4 opened")
    require(value["cycle002"]["disposition"] == "diagnostic_only", "cycle002 disposition drift")
    require(value["cycle002"]["semantic_gold"] is False, "cycle002 promoted to semantic gold")
    bindings = value["bindings"]
    for key, expected in {
        "source_universe_receipt_sha256": PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
        "source_units_jsonl_sha256": PINNED_SOURCE_UNITS_JSONL_SHA256,
        "materialization_receipt_file_sha256": PINNED_MATERIALIZATION_RECEIPT_FILE_SHA256,
        "materialization_receipt_body_sha256": PINNED_MATERIALIZATION_RECEIPT_BODY_SHA256,
        "partition_manifest_sha256": PINNED_PARTITION_SHA256,
        "evaluation_freeze_receipt_file_sha256": PINNED_EVALUATION_FREEZE_FILE_SHA256,
        "evaluation_freeze_receipt_body_sha256": PINNED_EVALUATION_FREEZE_BODY_SHA256,
        "ua_gec_complete_context_jsonl_sha256": PINNED_UA_GEC_CONTEXT_SHA256,
        "ua_gec_complete_context_exclusions_jsonl_sha256": PINNED_UA_GEC_EXCLUSIONS_SHA256,
        "ua_gec_complete_context_receipt_file_sha256": PINNED_UA_GEC_CONTEXT_RECEIPT_FILE_SHA256,
        "ua_gec_complete_context_receipt_body_sha256": PINNED_UA_GEC_CONTEXT_RECEIPT_BODY_SHA256,
        "custody_tarball_sha256": PINNED_CUSTODY_TARBALL_SHA256,
    }.items():
        require(bindings[key] == expected, f"binding drift: {key}")
    require(bindings["implementation_sha256"] == sha256_file(SCRIPT_PATH), "implementation binding drift")
    require(bindings["receipt_schema_sha256"] == sha256_file(SCHEMA_PATH), "schema binding drift")
    return value


def _prepare_private_output(path: Path) -> None:
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
        raise EvaluationContextManifestError(f"private write refuses group/other bits: {mode:04o}")
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


def _write_public_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _reject_symlink_components(path, "public receipt")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(receipt)
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


def _drive_item_id(path: Path) -> str:
    resolved = path.resolve()
    try:
        drive_roots = [
            candidate.resolve()
            for candidate in CLOUD_STORAGE_ROOT.glob("GoogleDrive-*")
            if candidate.is_dir() and (candidate / "My Drive").is_dir()
        ]
    except OSError as exc:
        raise EvaluationContextManifestError("cannot inspect configured Google Drive mounts") from exc
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
            raise EvaluationContextManifestError(
                f"artifact did not acquire Google Drive provider identity within {timeout_seconds:g} seconds"
            ) from last_error
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))


def _verify_drive_readback(path: Path, expected_sha256: str) -> None:
    readback = sha256_file(path)
    require(readback == expected_sha256, "Drive read-back hash mismatch")
    _wait_for_drive_item_id(path)


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
            _atomic_write(target, payload, PRIVATE_FILE_MODE)
            extracted[key] = target
    return extracted


def _build_receipt(
    *,
    manifest_payload: bytes,
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
            "source_universe_receipt_sha256": PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256,
            "source_units_jsonl_sha256": PINNED_SOURCE_UNITS_JSONL_SHA256,
            "materialization_receipt_file_sha256": PINNED_MATERIALIZATION_RECEIPT_FILE_SHA256,
            "materialization_receipt_body_sha256": PINNED_MATERIALIZATION_RECEIPT_BODY_SHA256,
            "partition_manifest_sha256": PINNED_PARTITION_SHA256,
            "evaluation_freeze_receipt_file_sha256": PINNED_EVALUATION_FREEZE_FILE_SHA256,
            "evaluation_freeze_receipt_body_sha256": PINNED_EVALUATION_FREEZE_BODY_SHA256,
            "ua_gec_complete_context_jsonl_sha256": PINNED_UA_GEC_CONTEXT_SHA256,
            "ua_gec_complete_context_exclusions_jsonl_sha256": PINNED_UA_GEC_EXCLUSIONS_SHA256,
            "ua_gec_complete_context_receipt_file_sha256": PINNED_UA_GEC_CONTEXT_RECEIPT_FILE_SHA256,
            "ua_gec_complete_context_receipt_body_sha256": PINNED_UA_GEC_CONTEXT_RECEIPT_BODY_SHA256,
            "custody_tarball_sha256": custody_tarball_sha256,
        },
        "denominators": {
            "v2_source_units": V2_SOURCE_UNITS,
            "v2_evaluation_identities": V2_EVALUATION_IDENTITIES,
            "v2_ua_gec_units": V2_UA_GEC_UNITS,
        },
        "row_count": ROW_COUNT,
        "family_counts": SEALED_FAMILY_COUNTS,
        "lanes": LANE_COUNTS,
        "context_accounting": CONTEXT_ACCOUNTING,
        "manifest": {
            "private_jsonl_sha256": sha256_bytes(manifest_payload),
            "private_jsonl_bytes": len(manifest_payload),
            "private_jsonl_rows": ROW_COUNT,
        },
        "frozen_evidence_backed_labels": FROZEN_EVIDENCE_BACKED_LABELS,
        "labels_present": False,
        "cycle002": {
            "identities": CYCLE002_IDENTITIES,
            "agreements": CYCLE002_AGREEMENTS,
            "disagreements": CYCLE002_DISAGREEMENTS,
            "rows_with_ua_gec_evidence": CYCLE002_UA_GEC_EVIDENCE_ROWS,
            "rows_without_authoritative_evidence": CYCLE002_NON_AUTHORITATIVE_ROWS,
            "semantic_gold": False,
            "disposition": "diagnostic_only",
        },
        "gates": {
            "evaluation_context_manifest_ready": True,
            "semantic_labels_present": False,
            "cycle002_labels_diagnostic_only": True,
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
    materialization_receipt_path: Path,
    partition_path: Path,
    evaluation_freeze_receipt_path: Path,
    ua_gec_context_path: Path,
    ua_gec_exclusions_path: Path,
    ua_gec_receipt_path: Path,
    private_output: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
    custody_tarball_sha256: str = PINNED_CUSTODY_TARBALL_SHA256,
) -> dict[str, Any]:
    rows, _accounting = build_manifest(
        source_jsonl=source_jsonl,
        materialization_receipt_path=materialization_receipt_path,
        partition_path=partition_path,
        evaluation_freeze_receipt_path=evaluation_freeze_receipt_path,
        ua_gec_context_path=ua_gec_context_path,
        ua_gec_exclusions_path=ua_gec_exclusions_path,
        ua_gec_receipt_path=ua_gec_receipt_path,
    )
    effective_completed_at = completed_at or utc_now()
    payload = b"".join(canonical_bytes(row) for row in rows)
    receipt = _build_receipt(
        manifest_payload=payload,
        started_at=started_at,
        completed_at=effective_completed_at,
        custody_tarball_sha256=custody_tarball_sha256,
    )
    _prepare_private_output(private_output)
    if private_output.exists():
        require(private_output.read_bytes() == payload, "refusing to overwrite a changed private manifest")
    else:
        _atomic_write(private_output, payload, PRIVATE_FILE_MODE)
    _write_public_receipt(public_receipt_path, receipt)
    return receipt


def _write_checksums(directory: Path, files: Mapping[str, Path]) -> Path:
    lines = [f"{sha256_file(path)}  {name}\n" for name, path in sorted(files.items())]
    checksums_path = directory / CHECKSUMS_FILENAME
    _atomic_write(checksums_path, "".join(lines).encode("utf-8"), PRIVATE_FILE_MODE)
    return checksums_path


def _build_custody_receipt(
    *,
    private_manifest: Path,
    checksums_path: Path,
    public_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    manifest_sha256 = sha256_file(private_manifest)
    checksums_sha256 = sha256_file(checksums_path)
    provider_id = _wait_for_drive_item_id(private_manifest)
    body = {
        "schema_version": "phase3_evaluation_context_manifest_custody_receipt_v1",
        "text_free": True,
        "provider_calls": False,
        "artifacts": {
            "private_manifest_filename": PRIVATE_FILENAME,
            "private_manifest_sha256": manifest_sha256,
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
            "private_files_mode_0600": stat.S_IMODE(private_manifest.stat().st_mode) == PRIVATE_FILE_MODE,
            "private_directory_mode_0700": stat.S_IMODE(private_manifest.parent.stat().st_mode) == PRIVATE_DIR_MODE,
        },
        "gates": {
            "evaluation_context_manifest_ready": True,
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
    private_output = drive_backup_dir / PRIVATE_FILENAME
    _regular_private(private_output, "private manifest")
    receipt = _read_json(public_receipt_path, "public receipt")
    validated = validate_receipt(receipt)
    _verify_drive_readback(private_output, validated["manifest"]["private_jsonl_sha256"])
    checksums_path = _write_checksums(drive_backup_dir, {PRIVATE_FILENAME: private_output})
    custody_receipt = _build_custody_receipt(
        private_manifest=private_output,
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
    ua_gec_context_path: Path,
    ua_gec_exclusions_path: Path,
    ua_gec_receipt_path: Path,
    drive_backup_dir: Path,
    public_receipt_path: Path,
    started_at: str,
    completed_at: str | None = None,
) -> dict[str, Any]:
    require(drive_backup_dir.parent.is_dir(), "drive backup parent must exist")
    drive_backup_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(drive_backup_dir, PRIVATE_DIR_MODE)
    temp_root = Path(tempfile.mkdtemp(prefix="phase3-eval-context-", dir=None))
    os.chmod(temp_root, PRIVATE_DIR_MODE)
    try:
        extracted = _extract_tarball_members(custody_tarball, temp_root)
        private_output = drive_backup_dir / PRIVATE_FILENAME
        receipt = materialize(
            source_jsonl=extracted["source_jsonl"],
            materialization_receipt_path=extracted["materialization_receipt"],
            partition_path=extracted["partition"],
            evaluation_freeze_receipt_path=extracted["evaluation_freeze_receipt"],
            ua_gec_context_path=ua_gec_context_path,
            ua_gec_exclusions_path=ua_gec_exclusions_path,
            ua_gec_receipt_path=ua_gec_receipt_path,
            private_output=private_output,
            public_receipt_path=public_receipt_path,
            started_at=started_at,
            completed_at=completed_at,
            custody_tarball_sha256=PINNED_CUSTODY_TARBALL_SHA256,
        )
        _verify_drive_readback(private_output, receipt["manifest"]["private_jsonl_sha256"])
        checksums_path = _write_checksums(
            drive_backup_dir,
            {PRIVATE_FILENAME: private_output},
        )
        custody_receipt = _build_custody_receipt(
            private_manifest=private_output,
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
    materialization_receipt_path: Path,
    partition_path: Path,
    evaluation_freeze_receipt_path: Path,
    ua_gec_context_path: Path,
    ua_gec_exclusions_path: Path,
    ua_gec_receipt_path: Path,
    private_output: Path,
    public_receipt_path: Path,
) -> dict[str, Any]:
    rows, accounting = build_manifest(
        source_jsonl=source_jsonl,
        materialization_receipt_path=materialization_receipt_path,
        partition_path=partition_path,
        evaluation_freeze_receipt_path=evaluation_freeze_receipt_path,
        ua_gec_context_path=ua_gec_context_path,
        ua_gec_exclusions_path=ua_gec_exclusions_path,
        ua_gec_receipt_path=ua_gec_receipt_path,
    )
    payload = b"".join(canonical_bytes(row) for row in rows)
    _regular_private(private_output, "private manifest")
    require(private_output.read_bytes() == payload, "private manifest drift")
    receipt = _read_json(public_receipt_path, "public receipt")
    validated = validate_receipt(receipt)
    require(
        validated["manifest"]["private_jsonl_sha256"] == sha256_bytes(payload), "public receipt manifest hash drift"
    )
    require(dict(accounting) == CONTEXT_ACCOUNTING, "context accounting drift on verify")
    return validated


def _reject_live_database(path: Path | None) -> None:
    if path is None:
        return
    require(not path.exists() or path.name == ".keep", "live database rematerialization is forbidden")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build the private manifest and public receipt")
    build.add_argument("--source-jsonl", type=Path, required=True)
    build.add_argument("--materialization-receipt", type=Path, required=True)
    build.add_argument("--partition", type=Path, required=True)
    build.add_argument("--evaluation-freeze-receipt", type=Path, required=True)
    build.add_argument("--ua-gec-context", type=Path, required=True)
    build.add_argument("--ua-gec-exclusions", type=Path, required=True)
    build.add_argument("--ua-gec-receipt", type=Path, required=True)
    build.add_argument("--private-output", type=Path, required=True)
    build.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    build.add_argument("--started-at")
    build.add_argument("--completed-at")
    build.add_argument("--database", type=Path, help=argparse.SUPPRESS)

    verify = subparsers.add_parser("verify", help="verify an existing manifest and receipt")
    verify.add_argument("--source-jsonl", type=Path, required=True)
    verify.add_argument("--materialization-receipt", type=Path, required=True)
    verify.add_argument("--partition", type=Path, required=True)
    verify.add_argument("--evaluation-freeze-receipt", type=Path, required=True)
    verify.add_argument("--ua-gec-context", type=Path, required=True)
    verify.add_argument("--ua-gec-exclusions", type=Path, required=True)
    verify.add_argument("--ua-gec-receipt", type=Path, required=True)
    verify.add_argument("--private-output", type=Path, required=True)
    verify.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)

    production = subparsers.add_parser("production", help="extract custody inputs and publish to Drive")
    production.add_argument("--custody-tarball", type=Path, required=True)
    production.add_argument("--ua-gec-context", type=Path, required=True)
    production.add_argument("--ua-gec-exclusions", type=Path, required=True)
    production.add_argument("--ua-gec-receipt", type=Path, required=True)
    production.add_argument("--drive-backup-dir", type=Path, required=True)
    production.add_argument("--public-receipt", type=Path, default=DEFAULT_PUBLIC_RECEIPT)
    production.add_argument("--started-at")
    production.add_argument("--completed-at")

    finish = subparsers.add_parser("finish-custody", help="complete Drive custody for an existing manifest")
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
                materialization_receipt_path=args.materialization_receipt,
                partition_path=args.partition,
                evaluation_freeze_receipt_path=args.evaluation_freeze_receipt,
                ua_gec_context_path=args.ua_gec_context,
                ua_gec_exclusions_path=args.ua_gec_exclusions,
                ua_gec_receipt_path=args.ua_gec_receipt,
                private_output=args.private_output,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
        elif args.command == "verify":
            receipt = verify_existing(
                source_jsonl=args.source_jsonl,
                materialization_receipt_path=args.materialization_receipt,
                partition_path=args.partition,
                evaluation_freeze_receipt_path=args.evaluation_freeze_receipt,
                ua_gec_context_path=args.ua_gec_context,
                ua_gec_exclusions_path=args.ua_gec_exclusions,
                ua_gec_receipt_path=args.ua_gec_receipt,
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
                ua_gec_context_path=args.ua_gec_context,
                ua_gec_exclusions_path=args.ua_gec_exclusions,
                ua_gec_receipt_path=args.ua_gec_receipt,
                drive_backup_dir=args.drive_backup_dir,
                public_receipt_path=args.public_receipt,
                started_at=args.started_at or utc_now(),
                completed_at=args.completed_at,
            )
    except (OSError, EvaluationContextManifestError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
