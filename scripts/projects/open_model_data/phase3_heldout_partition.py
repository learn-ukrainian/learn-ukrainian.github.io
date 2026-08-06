#!/usr/bin/env python3
"""Deterministic, fail-closed Phase 3 held-out partition, seal, and author clearance.

Label-blind steward lane only: partitions and seals custody before extraction.
Does not label Ukrainian gold, extract rules, or implement the scorer under test.
Private artifacts stay under ignored batch_state; the tracked public receipt is
source-text-free and identity-free.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from scripts.projects.open_model_data import phase3_near_duplicate as near
from scripts.projects.open_model_data import phase3_source_universe as freeze_mod
from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as source_freeze

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SOURCE_UNIVERSE = DATA / "evidence/source_universe_v1"
DEFAULT_SOURCES_DB = ROOT / "data/sources.db"
DEFAULT_ROLE_CONTRACT = DATA / "evidence/correction_protection_role_contract_v1.json"
DEFAULT_EVAL_CONTRACT = DATA / "evidence/correction_protection_evaluation_contract_v1.json"
DEFAULT_COVERAGE_CONTRACT = DATA / "evidence/correction_protection_coverage_contract_v1.json"
DEFAULT_NEAR_DUP_POLICY = DATA / "evidence/correction_protection_near_duplicate_policy_v1.json"
DEFAULT_SCHEMA = DATA / "contracts/phase3_heldout_partition_bundle_v1.schema.json"
DEFAULT_PUBLIC_DIR = DATA / "evidence/phase3_heldout_partition_v1"
DEFAULT_PRIVATE_DIR = ROOT / "batch_state/open-model-data/phase3-heldout"

UA_EVAL_ARTIFACTS = (
    "data/projects/ua_eval_harness/evalset_v1.jsonl",
    "data/projects/ua_eval_harness/heldout_manifest_v1.json",
    "data/projects/ua_eval_harness/analysis/v0.1.1/item_evidence.jsonl",
    "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
)
PUBLIC_CANARY_ARTIFACTS = (
    "data/projects/open_model_data/detector/correction_protection_known_answers_v1.json",
)

CONTROLLER_IDENTITY = "controller_phase3_heldout_steward_cursor_runtime_01"
ARTIFACT_TASK_ID = "phase3-heldout-partition-seal-cursor-v1"
ATTESTATION_TASK_ID = "phase3-role-heldout-steward-cursor-v2"
ROLE_ID = "heldout_steward"
SEAT_ID = "seat_heldout_steward"

CAPABILITY_STATE = "NOT_YET_LABELLED_OR_ACTIVATED"
IMPLEMENTATION_VERSION = "phase3_heldout_partition_v1"
UA_GEC_FAMILY = "ua_gec"
UA_GEC_TABLE = "ua_gec_errors"
SHORTFALL_CODE = "NON_UA_GEC_LABEL_BLIND_HELDOUT_NOT_SEALED"
SHORTFALL_DETAIL = "contract_requires_ua_gec_test_as_mandatory_private_side_only_at_partition_time"
SHORTFALL_FAMILIES = "non_ua_gec_evaluation_families_deferred_hash_only"
PUBLIC_TOKEN_STRINGS = frozenset(
    {
        "phase3_heldout_public_receipt_v1",
        IMPLEMENTATION_VERSION,
        ROLE_ID,
        SEAT_ID,
        CONTROLLER_IDENTITY,
        ATTESTATION_TASK_ID,
        ARTIFACT_TASK_ID,
        CAPABILITY_STATE,
        SHORTFALL_CODE,
        SHORTFALL_DETAIL,
        SHORTFALL_FAMILIES,
    }
)
FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "unit_id",
        "unit_ids",
        "document_id",
        "document_ids",
        "doc_id",
        "doc_ids",
        "locator",
        "locators",
        "fingerprint",
        "fingerprints",
        "span_fingerprint",
        "normalized_surface",
        "complement",
        "complements",
        "heldout_items",
        "author_items",
        "source_text",
        "text",
        "error",
        "correct",
        "near_neighbour",
        "near_neighbours",
    }
)
PRIVATE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


class PartitionError(ValueError):
    """Partition, seal, or clearance cannot proceed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PartitionError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_value(value: Any) -> str:
    return sha256_bytes((canonical_json(value) + "\n").encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PartitionError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PartitionError(f"cannot read JSON: {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def write_private_json(path: Path, value: Mapping[str, Any]) -> str:
    """Atomically write a permissions-restricted private JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    payload = (canonical_json(value) + "\n").encode("utf-8")
    digest = sha256_bytes(payload)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, PRIVATE_MODE)
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_MODE)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise
    require(sha256_file(path) == digest, f"private artifact hash drift: {path}")
    require((path.stat().st_mode & 0o777) == PRIVATE_MODE, f"private artifact mode drift: {path}")
    return digest


def receipt_body_sha256(value: Mapping[str, Any], *, hash_field: str = "receipt_sha256") -> str:
    return sha256_value({key: item for key, item in value.items() if key != hash_field})


def attach_receipt_hash(value: dict[str, Any], *, hash_field: str = "receipt_sha256") -> dict[str, Any]:
    payload = dict(value)
    payload.pop(hash_field, None)
    payload[hash_field] = sha256_value(payload)
    return payload


def write_public_json(path: Path, value: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (canonical_json(value) + "\n").encode("utf-8")
    digest = sha256_bytes(payload)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise
    require(sha256_file(path) == digest, f"public artifact hash drift: {path}")
    return digest


def _schema_validate(instance: Mapping[str, Any], schema: Mapping[str, Any], definition: str) -> None:
    try:
        Draft202012Validator.check_schema(dict(schema))
        validator = Draft202012Validator(
            {
                "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
                "$ref": f"#/$defs/{definition}",
                "$defs": schema.get("$defs", {}),
            }
        )
        validator.validate(instance)
    except (SchemaError, ValidationError) as exc:
        message = getattr(exc, "message", str(exc))
        raise PartitionError(f"schema validation failed for {definition}: {message}") from exc


def document_identity_for_ua_gec(doc_id: str) -> str:
    """Namespace-hash raw doc_id; layer/partition are not part of identity."""
    require(isinstance(doc_id, str) and doc_id != "", "ua_gec doc_id must be a non-empty string")
    return f"doc.ua_gec.{sha256_value(freeze_mod._normal(doc_id))}"


def parse_ua_gec_partition(partition: str) -> tuple[str, str]:
    require(isinstance(partition, str) and "/" in partition, "ua_gec partition must be layer/split")
    layer, split = partition.rsplit("/", 1)
    require(layer != "" and split in {"train", "test"}, f"ua_gec partition split unsafe: {partition!r}")
    return layer, split


def _connect_sources(path: Path) -> sqlite3.Connection:
    require(path.is_file() and path.stat().st_size > 0, f"missing sources DB: {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _load_freeze_ua_gec_units(source_universe: Path) -> list[dict[str, Any]]:
    path = source_universe / "ua_gec.units.jsonl"
    require(path.is_file(), f"missing frozen ua_gec units: {path}")
    units: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for ordinal, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                unit = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PartitionError(f"malformed frozen ua_gec unit at line {ordinal}") from exc
            require(isinstance(unit, dict), f"frozen ua_gec unit must be object at line {ordinal}")
            require(unit.get("family_id") == UA_GEC_FAMILY, "frozen unit family drift")
            unit_id = unit.get("unit_id")
            require(isinstance(unit_id, str) and unit_id not in seen_ids, "duplicate or missing frozen unit_id")
            seen_ids.add(unit_id)
            units.append(unit)
    require(units, "frozen ua_gec ledger is empty")
    return units


def _identity_hash_for_row_id(row_id: int) -> str:
    return freeze_mod._unit_hash({"id": row_id})


def _opaque_unit_id_for_row_id(row_id: int) -> str:
    return freeze_mod._opaque_id(f"unit.{UA_GEC_FAMILY}", {"table": UA_GEC_TABLE, "identity": {"id": row_id}})


def reconstruct_ua_gec_rows(
    *,
    sources_db: Path,
    freeze_units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Join frozen unit identities to sources.db rows; fail closed on drift."""
    by_pk_hash = {
        str(unit["locator"]["primary_key_sha256"]): unit
        for unit in freeze_units
    }
    require(len(by_pk_hash) == len(freeze_units), "frozen ua_gec primary_key_sha256 collision")
    connection = _connect_sources(sources_db)
    try:
        rows = connection.execute(
            'SELECT "id", "error", "correct", "error_type", "doc_id", "annotator_id", '
            '"partition", "is_native", "source_lang" FROM "ua_gec_errors" ORDER BY "id"'
        ).fetchall()
    finally:
        connection.close()
    require(len(rows) == len(freeze_units), "ua_gec sources.db row count drifts from freeze")
    reconstructed: list[dict[str, Any]] = []
    matched: set[str] = set()
    for row in rows:
        row_id = int(row["id"])
        pk_hash = _identity_hash_for_row_id(row_id)
        unit = by_pk_hash.get(pk_hash)
        require(unit is not None, "frozen ua_gec unit missing for sources.db row")
        require(unit["unit_id"] == _opaque_unit_id_for_row_id(row_id), "frozen ua_gec unit_id drift")
        matched.add(pk_hash)
        layer, split = parse_ua_gec_partition(str(row["partition"]))
        error = row["error"]
        correct = row["correct"]
        require(isinstance(error, str) and isinstance(correct, str), "ua_gec row text fields malformed")
        error_type = row["error_type"]
        doc_id = row["doc_id"]
        annotator_id = row["annotator_id"]
        is_native = row["is_native"]
        source_lang = row["source_lang"]
        require(isinstance(doc_id, str) and doc_id != "", "ua_gec doc_id malformed")
        require(isinstance(error_type, str) and error_type, "ua_gec error_type malformed")
        require(isinstance(annotator_id, str) and annotator_id, "ua_gec annotator_id malformed")
        require(isinstance(is_native, int), "ua_gec is_native malformed")
        require(isinstance(source_lang, str), "ua_gec source_lang malformed")
        source_record = freeze_mod._normal(
            {
                "id": row_id,
                "error": error,
                "correct": correct,
                "error_type": error_type,
                "doc_id": doc_id,
                "annotator_id": annotator_id,
                "partition": str(row["partition"]),
                "is_native": is_native,
                "source_lang": source_lang,
            }
        )
        require(unit["unit_sha256"] == freeze_mod._unit_hash(source_record), "ua_gec frozen unit hash drift")
        reconstructed.append(
            {
                "family_id": UA_GEC_FAMILY,
                "unit_id": unit["unit_id"],
                "unit_sha256": unit["unit_sha256"],
                "ordinal": unit["ordinal"],
                "primary_key_sha256": pk_hash,
                "row_id": row_id,
                "doc_id": doc_id,
                "source_document_identity": document_identity_for_ua_gec(doc_id),
                "layer": layer,
                "split": split,
                "partition": str(row["partition"]),
                "error": error,
                "correct": correct,
                "error_type": error_type,
                "annotator_id": annotator_id,
                "is_native": is_native,
                "source_lang": source_lang,
                "source_record": source_record,
                "locator": unit["locator"],
            }
        )
    require(matched == set(by_pk_hash), "freeze contains units absent from sources.db")
    reconstructed.sort(key=lambda item: (item["ordinal"], item["unit_id"]))
    return reconstructed


def _artifact_binding(logical_path: str, *, root: Path = ROOT) -> dict[str, str]:
    path = root / logical_path
    require(path.is_file(), f"missing binding artifact: {logical_path}")
    return {"logical_path": logical_path, "sha256": sha256_file(path)}


_SURFACE_KEYS = frozenset(
    {
        "text",
        "target",
        "surface",
        "replacement",
        "error",
        "correct",
        "original",
        "incorrect",
        "normalized_surface",
        "source_text",
    }
)
_SURFACE_CONTAINER_KEYS = frozenset(
    {
        "blind_reviewer_view",
        "positive",
        "acceptable_control",
        "protected",
        "evidence",
        "categories",
        "cases",
        "items",
        "examples",
    }
)


def _collect_string_surfaces(value: Any, into: list[str]) -> None:
    """Collect only explicit text-bearing fields; never harvest ids/hashes/tags."""
    if isinstance(value, str):
        if value.strip():
            into.append(value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _SURFACE_KEYS and isinstance(item, str) and item.strip():
                into.append(item)
            elif key == "source" and isinstance(item, str) and item.strip() and not item.startswith("data/"):
                # heldout-manifest sentence source text, not a filesystem locator
                into.append(item)
            elif (
                key in _SURFACE_CONTAINER_KEYS
                or isinstance(item, Mapping)
                or (isinstance(item, list) and item and isinstance(item[0], Mapping))
            ):
                _collect_string_surfaces(item, into)
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, (Mapping, list)):
                _collect_string_surfaces(item, into)


def build_ua_eval_exclusion_manifest(*, root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    """Hash-bound UA Eval exclusion set: opaque fingerprints and unit row hashes only."""
    bindings = [_artifact_binding(path, root=root) for path in UA_EVAL_ARTIFACTS]
    excluded_row_id_hashes: set[str] = set()
    excluded_doc_identity_hashes: set[str] = set()
    surface_fingerprints: set[str] = set()
    surfaces: list[str] = []

    evalset = root / "data/projects/ua_eval_harness/evalset_v1.jsonl"
    with evalset.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            require(isinstance(item, dict), "ua eval evalset row malformed")
            _collect_string_surfaces(item.get("text"), surfaces)
            _collect_string_surfaces(item.get("target"), surfaces)
            error_id = item.get("provenance", {}).get("ua_gec_error_id")
            if error_id is not None:
                excluded_row_id_hashes.add(sha256_value({"ua_gec_error_id": int(error_id)}))

    heldout = read_json(root / "data/projects/ua_eval_harness/heldout_manifest_v1.json")
    layout = heldout.get("record_layouts", {})
    item_fields = layout.get("item")
    exclusion_fields = layout.get("exclusion")
    require(isinstance(item_fields, list) and "doc_id" in item_fields, "heldout manifest item layout drift")
    require(isinstance(exclusion_fields, list) and "doc_id" in exclusion_fields, "heldout manifest exclusion layout drift")
    doc_index = item_fields.index("doc_id")
    source_index = item_fields.index("source") if "source" in item_fields else None
    excl_doc_index = exclusion_fields.index("doc_id")
    for row in heldout.get("items", []):
        require(isinstance(row, list) and len(row) == len(item_fields), "heldout item width drift")
        doc_id = row[doc_index]
        require(isinstance(doc_id, str) and doc_id, "heldout item doc_id malformed")
        excluded_doc_identity_hashes.add(document_identity_for_ua_gec(doc_id))
        if source_index is not None and isinstance(row[source_index], str):
            surfaces.append(row[source_index])
        if "references" in item_fields:
            for ref in row[item_fields.index("references")]:
                if isinstance(ref, list) and len(ref) > 1 and isinstance(ref[1], str) and ref[1].strip():
                    surfaces.append(ref[1])
    for row in heldout.get("exclusions", []):
        require(isinstance(row, list) and len(row) == len(exclusion_fields), "heldout exclusion width drift")
        doc_id = row[excl_doc_index]
        require(isinstance(doc_id, str) and doc_id, "heldout exclusion doc_id malformed")
        excluded_doc_identity_hashes.add(document_identity_for_ua_gec(doc_id))

    for logical in (
        "data/projects/ua_eval_harness/analysis/v0.1.1/item_evidence.jsonl",
        "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
    ):
        path = root / logical
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                _collect_string_surfaces(json.loads(line), surfaces)

    for surface in surfaces:
        try:
            surface_fingerprints.add(near.fingerprint(surface).exact_fingerprint)
        except near.NearDuplicatePolicyError:
            surface_fingerprints.add(sha256_text("malformed_exclusion_surface"))

    body = {
        "schema_version": "phase3_ua_eval_exclusion_manifest_v1",
        "text_free": True,
        "source_artifact_bindings": bindings,
        "excluded_ua_gec_row_id_sha256s": sorted(excluded_row_id_hashes),
        "excluded_document_identity_sha256s": sorted(excluded_doc_identity_hashes),
        "excluded_surface_fingerprint_sha256s": sorted(surface_fingerprints),
        "counts": {
            "source_artifact_count": len(bindings),
            "excluded_ua_gec_row_id_count": len(excluded_row_id_hashes),
            "excluded_document_identity_count": len(excluded_doc_identity_hashes),
            "excluded_surface_fingerprint_count": len(surface_fingerprints),
        },
    }
    body["manifest_sha256"] = sha256_value({key: value for key, value in body.items() if key != "manifest_sha256"})
    return body, surfaces


def build_public_canary_exclusion_manifest(*, root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    bindings = [_artifact_binding(path, root=root) for path in PUBLIC_CANARY_ARTIFACTS]
    surfaces: list[str] = []
    for logical in PUBLIC_CANARY_ARTIFACTS:
        _collect_string_surfaces(read_json(root / logical), surfaces)
    fingerprints: set[str] = set()
    for surface in surfaces:
        try:
            fingerprints.add(near.fingerprint(surface).exact_fingerprint)
        except near.NearDuplicatePolicyError:
            fingerprints.add(sha256_text("malformed_exclusion_surface"))
    body = {
        "schema_version": "phase3_public_canary_exclusion_manifest_v1",
        "text_free": True,
        "source_artifact_bindings": bindings,
        "excluded_surface_fingerprint_sha256s": sorted(fingerprints),
        "counts": {
            "source_artifact_count": len(bindings),
            "excluded_surface_fingerprint_count": len(fingerprints),
        },
    }
    body["manifest_sha256"] = sha256_value({key: value for key, value in body.items() if key != "manifest_sha256"})
    return body, surfaces


def _load_exclusion_surfaces(*, root: Path = ROOT) -> tuple[set[str], list[str], set[str], set[str], dict[str, Any], dict[str, Any]]:
    """Return exact fingerprints, surfaces, excluded row hashes, doc identities, and manifests."""
    ua_eval, ua_surfaces = build_ua_eval_exclusion_manifest(root=root)
    canary, canary_surfaces = build_public_canary_exclusion_manifest(root=root)
    exact = set(ua_eval["excluded_surface_fingerprint_sha256s"]) | set(
        canary["excluded_surface_fingerprint_sha256s"]
    )
    surfaces = _unique_exclusion_surfaces([*ua_surfaces, *canary_surfaces])
    return (
        exact,
        surfaces,
        set(ua_eval["excluded_ua_gec_row_id_sha256s"]),
        set(ua_eval["excluded_document_identity_sha256s"]),
        ua_eval,
        canary,
    )


def _unique_exclusion_surfaces(surfaces: Iterable[str]) -> list[str]:
    """Deduplicate exclusion surfaces by exact fingerprint for near-neighbour checks."""
    ordered: list[str] = []
    seen: set[str] = set()
    for surface in surfaces:
        try:
            fingerprint = near.fingerprint(surface).exact_fingerprint
        except near.NearDuplicatePolicyError:
            fingerprint = sha256_text("malformed_exclusion_surface")
            ordered.append(surface)
            seen.add(fingerprint)
            continue
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        ordered.append(surface)
    return ordered


def _near_duplicate_candidates(
    text: str,
    exclusion_surfaces: Sequence[str],
    *,
    token_index: Mapping[str, Sequence[int]],
    exclusion_fps: Sequence[near.TextFingerprint],
) -> list[int]:
    """Return exclusion indices that share enough tokens to possibly meet the 0.9 Jaccard floor."""
    try:
        probe = near.fingerprint(text)
    except near.NearDuplicatePolicyError:
        return list(range(len(exclusion_surfaces)))
    if not probe.tokens:
        return list(range(len(exclusion_surfaces)))
    scores: dict[int, int] = {}
    for token in set(probe.tokens):
        for index in token_index.get(token, ()):
            scores[index] = scores.get(index, 0) + 1
    required = max(1, int(0.9 * len(set(probe.tokens))))
    return [index for index, shared in scores.items() if shared >= required]


def unit_conflicts_with_exclusions(
    unit: Mapping[str, Any],
    *,
    exact_fingerprints: set[str],
    exclusion_surfaces: Sequence[str],
    exclusion_fps: Sequence[near.TextFingerprint],
    token_index: Mapping[str, Sequence[int]],
    excluded_row_hashes: set[str],
    excluded_doc_identities: set[str],
    policy: Mapping[str, Any],
) -> tuple[bool, str]:
    """Return (excluded, aggregate_reason_code). Malformed comparisons fail closed."""
    row_hash = sha256_value({"ua_gec_error_id": int(unit["row_id"])})
    if row_hash in excluded_row_hashes:
        return True, "ua_eval_row_identity"
    if unit["source_document_identity"] in excluded_doc_identities:
        return True, "ua_eval_document_identity"
    for field in ("error", "correct"):
        text = unit.get(field)
        if not isinstance(text, str):
            return True, "malformed_comparison"
        try:
            fp = near.fingerprint(text).exact_fingerprint
        except near.NearDuplicatePolicyError:
            return True, "malformed_comparison"
        if fp in exact_fingerprints:
            return True, "exact_surface_exclusion"
        for index in _near_duplicate_candidates(
            text, exclusion_surfaces, token_index=token_index, exclusion_fps=exclusion_fps
        ):
            if near.duplicate_or_fail_closed(text, exclusion_surfaces[index], scope="span", policy=policy):
                return True, "near_or_malformed_surface_exclusion"
    return False, "cleared"


def frozen_locator_binding(locator: Mapping[str, Any]) -> dict[str, Any]:
    """Copy the immutable freeze locator; refuse unexpected shapes."""
    require(isinstance(locator, Mapping), "frozen locator missing")
    require(locator.get("kind") == "sqlite_row", "frozen locator kind drift")
    require(locator.get("table") == UA_GEC_TABLE, "frozen locator table drift")
    fields = locator.get("primary_key_fields")
    require(isinstance(fields, list) and fields == ["id"], "frozen locator primary_key_fields drift")
    pk = locator.get("primary_key_sha256")
    require(isinstance(pk, str) and len(pk) == 64, "frozen locator primary_key_sha256 drift")
    return {
        "kind": "sqlite_row",
        "table": UA_GEC_TABLE,
        "primary_key_fields": ["id"],
        "primary_key_sha256": pk,
    }


def span_fingerprints_for_pair(error: str, correct: str) -> dict[str, str]:
    """Pin near-duplicate exact fingerprints for sealed error/correct bytes."""
    require(isinstance(error, str) and isinstance(correct, str), "sealed text fields must be strings")
    try:
        error_fp = near.fingerprint(error).exact_fingerprint
        correct_fp = near.fingerprint(correct).exact_fingerprint
    except near.NearDuplicatePolicyError as exc:
        raise PartitionError("cannot fingerprint sealed held-out surfaces") from exc
    return {
        "error_span_fingerprint_sha256": error_fp,
        "correct_span_fingerprint_sha256": correct_fp,
        "near_duplicate_policy_fingerprint_sha256": near.PINNED_POLICY_FINGERPRINT,
    }


def build_heldout_sealed_unit(
    row: Mapping[str, Any],
    *,
    sources_db_sha256: str,
) -> dict[str, Any]:
    """Assemble one private custody row: bytes, locator, fingerprints, and pins."""
    require(row.get("split") == "test", "non-test row cannot enter held-out seal")
    error = row["error"]
    correct = row["correct"]
    require(isinstance(error, str) and isinstance(correct, str), "held-out row text fields malformed")
    fingerprints = span_fingerprints_for_pair(error, correct)
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "source_document_identity": row["source_document_identity"],
        "layer": row["layer"],
        "split": row["split"],
        "primary_key_sha256": row["primary_key_sha256"],
        "ordinal": row["ordinal"],
        "family_id": UA_GEC_FAMILY,
        "error": error,
        "correct": correct,
        "locator": frozen_locator_binding(row["locator"]),
        "error_span_fingerprint_sha256": fingerprints["error_span_fingerprint_sha256"],
        "correct_span_fingerprint_sha256": fingerprints["correct_span_fingerprint_sha256"],
        "sources_db_sha256": sources_db_sha256,
        "near_duplicate_policy_fingerprint_sha256": fingerprints[
            "near_duplicate_policy_fingerprint_sha256"
        ],
    }


def _build_exclusion_index(
    exclusion_surfaces: Sequence[str],
) -> tuple[list[near.TextFingerprint], dict[str, list[int]]]:
    fingerprints: list[near.TextFingerprint] = []
    token_index: dict[str, list[int]] = {}
    for index, surface in enumerate(exclusion_surfaces):
        try:
            item = near.fingerprint(surface)
        except near.NearDuplicatePolicyError:
            item = near.TextFingerprint(normalized_surface="", exact_fingerprint=sha256_text("malformed"), tokens=())
        fingerprints.append(item)
        for token in set(item.tokens):
            token_index.setdefault(token, []).append(index)
    return fingerprints, token_index


def verify_role_binding(role_contract: Mapping[str, Any]) -> dict[str, str]:
    exclusivity = role_contract.get("identity_exclusivity_contract")
    require(isinstance(exclusivity, Mapping), "identity exclusivity contract missing")
    for invariant in (
        "one_natural_person_or_continuing_agent_identity_per_decision_role_maximum",
        "same_controller_reuses_identity_across_sessions_task_ids_harnesses_models_and_providers",
        "controller_identity_attestation_required_before_role_action",
        "assigned_controller_identity_ids_unique_across_decision_seats",
        "root_controller_identity_forbidden_from_decision_seats",
        "unassigned_reserved_seats_may_not_act_or_issue_receipts",
        "task_binding_must_match_seat_controller_identity",
    ):
        require(exclusivity.get(invariant) is True, f"role exclusivity invariant disabled: {invariant}")

    seats = role_contract.get("seats")
    require(isinstance(seats, list), "role contract seats missing")
    assigned = [item for item in seats if item.get("assignment_state") == "assigned_verified"]
    require(assigned, "role contract has no assigned decision seats")
    controllers = [item.get("controller_identity_id") for item in assigned]
    require(all(isinstance(identity, str) and identity for identity in controllers), "assigned seat controller missing")
    require(len(controllers) == len(set(controllers)), "assigned decision seats reuse a controller identity")
    require(
        all(item.get("controller_identity_attested") is True for item in assigned),
        "assigned decision seat controller unattested",
    )

    root = role_contract.get("root")
    require(isinstance(root, Mapping), "root role boundary missing")
    root_identity = root.get("controller_identity_id")
    require(isinstance(root_identity, str) and root_identity not in controllers, "root occupies a decision seat")
    require(root.get("may_hold_decision_role") is False, "root may hold a decision role")
    require(root.get("decision_role_ids") == [], "root decision-role list is not empty")

    seat = next((item for item in seats if item.get("seat_id") == SEAT_ID), None)
    require(seat is not None, "heldout steward seat missing")
    require(seat.get("role_id") == ROLE_ID, "heldout steward role drift")
    require(seat.get("controller_identity_id") == CONTROLLER_IDENTITY, "heldout steward controller unbound")
    require(seat.get("controller_identity_attested") is True, "heldout steward controller unattested")
    require(seat.get("assignment_state") == "assigned_verified", "heldout steward seat not assigned_verified")
    require(
        {"label_linguistic_gold", "extract_rules", "implement_scorer_under_test"}.issubset(
            set(seat.get("must_not", []))
        ),
        "heldout steward prohibited functions drift",
    )
    bindings = role_contract.get("task_bindings")
    require(isinstance(bindings, list), "role contract task bindings missing")
    binding_by_role: dict[str, Mapping[str, Any]] = {}
    seat_by_role = {str(item.get("role_id")): item for item in assigned}
    require(len(seat_by_role) == len(assigned), "assigned decision role duplicated")
    for item in bindings:
        require(isinstance(item, Mapping), "role contract task binding malformed")
        role_id = item.get("role_id")
        require(isinstance(role_id, str) and role_id not in binding_by_role, "task binding role missing or duplicated")
        binding_by_role[role_id] = item
    require(set(binding_by_role) == set(seat_by_role), "task bindings do not exactly cover assigned seats")
    for role_id, assigned_seat in seat_by_role.items():
        require(
            binding_by_role[role_id].get("controller_identity_id") == assigned_seat.get("controller_identity_id"),
            f"task binding controller differs from assigned seat: {role_id}",
        )
    binding = next((item for item in bindings if item.get("role_id") == ROLE_ID), None)
    require(binding is not None, "heldout steward task binding missing")
    require(binding.get("reserved_task_id") == ATTESTATION_TASK_ID, "heldout steward attestation task drift")
    require(binding.get("controller_identity_id") == CONTROLLER_IDENTITY, "heldout steward task controller drift")

    acl = role_contract.get("heldout_acl")
    require(isinstance(acl, Mapping), "heldout ACL missing")
    pre_release = set(acl.get("pre_release_read_roles", []))
    post_release = set(acl.get("post_release_scorer_roles", []))
    forbidden = set(acl.get("forbidden_roles", []))
    require(pre_release == {"heldout_steward", "heldout_label_reviewer"}, "heldout pre-release ACL drift")
    require(post_release == {"scorer"}, "heldout post-release scorer ACL drift")
    require(
        {"rule_author_extractor", "ukrainian_source_reviewer", "outsider_reproducer"}.issubset(forbidden),
        "heldout forbidden-role ACL drift",
    )
    require(not (pre_release & forbidden) and not (post_release & forbidden), "heldout ACL roles overlap")
    return {
        "role_id": ROLE_ID,
        "seat_id": SEAT_ID,
        "controller_identity_id": CONTROLLER_IDENTITY,
        "attestation_task_id": ATTESTATION_TASK_ID,
        "artifact_task_id": ARTIFACT_TASK_ID,
    }


def _assert_no_forbidden_public_fields(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            require(key not in FORBIDDEN_PUBLIC_KEYS, f"public receipt forbids field {key} at {path}")
            lower = key.lower()
            # Policy/artifact fingerprint hashes are allowed; unit/doc/span fingerprints are not.
            if lower in {
                "near_duplicate_policy_fingerprint_sha256",
                "policy_fingerprint_sha256",
            } or lower.endswith("_policy_fingerprint_sha256"):
                _assert_no_forbidden_public_fields(item, path=f"{path}.{key}")
                continue
            require(
                not any(
                    token == lower or lower.startswith(token + "_") or lower.endswith("_" + token)
                    for token in ("unit_id", "unit_ids", "doc_id", "doc_ids", "locator", "locators", "complement", "complements")
                ),
                f"public receipt forbids identity-bearing field {key}",
            )
            require(
                "span_fingerprint" not in lower
                and lower not in {"fingerprint", "fingerprints", "normalized_surface"},
                f"public receipt forbids content fingerprint field {key}",
            )
            _assert_no_forbidden_public_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_public_fields(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        # This receipt has a closed token vocabulary plus SHA-256 bindings.  Do
        # not accept arbitrary ASCII, which could still disclose source prose.
        require(
            value in PUBLIC_TOKEN_STRINGS or re.fullmatch(r"[a-f0-9]{64}", value) is not None,
            f"public receipt contains an unapproved string at {path}",
        )


def partition_ua_gec(
    rows: Sequence[Mapping[str, Any]],
    *,
    policy: Mapping[str, Any],
    exact_fingerprints: set[str],
    exclusion_surfaces: Sequence[str],
    excluded_row_hashes: set[str],
    excluded_doc_identities: set[str],
) -> dict[str, Any]:
    """Partition at document identity; seal /test; clear safe /train author units."""
    exclusion_fps, token_index = _build_exclusion_index(exclusion_surfaces)
    docs: dict[str, set[str]] = {}
    for row in rows:
        docs.setdefault(row["source_document_identity"], set()).add(row["split"])
    heldout_docs: set[str] = set()
    author_candidate_docs: set[str] = set()
    for doc, splits in docs.items():
        require(splits <= {"train", "test"}, "unexpected ua_gec split")
        if "test" in splits:
            require(splits == {"test"}, "ua_gec document spans train and test")
            heldout_docs.add(doc)
        else:
            author_candidate_docs.add(doc)

    # Cross-layer collapse: identity is doc-hash only; verify layers do not create split conflicts.
    by_raw_doc: dict[str, set[str]] = {}
    for row in rows:
        by_raw_doc.setdefault(row["doc_id"], set()).add(row["split"])
    for splits in by_raw_doc.values():
        require(not ({"train", "test"} <= splits), "raw doc_id spans train and test after layer collapse")

    heldout_units: list[dict[str, Any]] = []
    author_cleared: list[dict[str, Any]] = []
    omit_reasons: dict[str, int] = {
        "heldout_document": 0,
        "ua_eval_row_identity": 0,
        "ua_eval_document_identity": 0,
        "exact_surface_exclusion": 0,
        "near_or_malformed_surface_exclusion": 0,
        "malformed_comparison": 0,
    }

    for row in rows:
        doc = row["source_document_identity"]
        if doc in heldout_docs:
            require(row["split"] == "test", "non-test unit attached to held-out document")
            heldout_units.append(
                {
                    "unit_id": row["unit_id"],
                    "unit_sha256": row["unit_sha256"],
                    "source_document_identity": doc,
                    "layer": row["layer"],
                    "split": row["split"],
                    "primary_key_sha256": row["primary_key_sha256"],
                    "ordinal": row["ordinal"],
                    "family_id": UA_GEC_FAMILY,
                }
            )
            continue
        require(row["split"] == "train", "author-candidate unit is not train")
        require(doc in author_candidate_docs, "train unit document not author-candidate")
        excluded, reason = unit_conflicts_with_exclusions(
            row,
            exact_fingerprints=exact_fingerprints,
            exclusion_surfaces=exclusion_surfaces,
            exclusion_fps=exclusion_fps,
            token_index=token_index,
            excluded_row_hashes=excluded_row_hashes,
            excluded_doc_identities=excluded_doc_identities,
            policy=policy,
        )
        if excluded:
            omit_reasons[reason] = omit_reasons.get(reason, 0) + 1
            continue
        author_cleared.append(
            {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "family_id": UA_GEC_FAMILY,
                "source_document_identity": doc,
            }
        )

    heldout_units.sort(key=lambda item: (item["ordinal"], item["unit_id"]))
    author_cleared.sort(key=lambda item: item["unit_id"])

    heldout_doc_set = {item["source_document_identity"] for item in heldout_units}
    author_doc_set = {item["source_document_identity"] for item in author_cleared}
    require(heldout_doc_set.isdisjoint(author_doc_set), "document-level author/held-out overlap")
    heldout_unit_ids = {item["unit_id"] for item in heldout_units}
    author_unit_ids = {item["unit_id"] for item in author_cleared}
    require(heldout_unit_ids.isdisjoint(author_unit_ids), "unit-level author/held-out overlap")
    require(all(item["split"] == "test" for item in heldout_units), "held-out contains non-test units")
    require("/test" not in "".join(item.get("split", "") for item in author_cleared), "author clearance contains test marker")
    require(all(item["unit_id"] not in heldout_unit_ids for item in author_cleared), "test units leaked into author clearance")

    return {
        "heldout_units": heldout_units,
        "author_cleared_units": author_cleared,
        "omit_reasons": {key: omit_reasons[key] for key in sorted(omit_reasons)},
        "heldout_document_count": len(heldout_doc_set),
        "author_candidate_document_count": len(author_candidate_docs),
        "author_cleared_document_count": len(author_doc_set),
        "zero_overlap": {
            "document_exact": True,
            "unit_exact": True,
            "test_excluded_from_author_clearance": True,
        },
    }


def build_input_bindings(
    *,
    root: Path,
    source_universe: Path,
    role_contract_path: Path,
    eval_contract_path: Path,
    coverage_contract_path: Path,
    near_dup_policy_path: Path,
    ua_eval_manifest: Mapping[str, Any],
    public_canary_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    freeze_receipt = source_universe / "source-universe-freeze-receipt.json"
    require(freeze_receipt.is_file(), "source universe freeze receipt missing")
    return {
        "schema_version": "phase3_heldout_input_bindings_v1",
        "combined_contract_sha256": "bf387adaeb180d11ade272819d77e1eb3d3fdecc43982fff9c775039c9e0bed7",
        "original_prompt_sha256": "6a563a7526c4ec7a89732f3de5651b0ab2e176ec089abf80f9eb733337db7662",
        "scope_amendment_sha256": "da0f814f2f12e4974073de1a7b547fc3f27c07f6d903c95fde8f704d4e664132",
        "role_contract_sha256": sha256_file(role_contract_path),
        "evaluation_contract_sha256": sha256_file(eval_contract_path),
        "coverage_contract_sha256": sha256_file(coverage_contract_path),
        "source_universe_receipt_sha256": sha256_file(freeze_receipt),
        "near_duplicate_policy_sha256": sha256_file(near_dup_policy_path),
        "near_duplicate_policy_fingerprint_sha256": near.PINNED_POLICY_FINGERPRINT,
        "ua_eval_exclusion_manifest_sha256": ua_eval_manifest["manifest_sha256"],
        "public_canary_exclusion_manifest_sha256": public_canary_manifest["manifest_sha256"],
        "sources_db_sha256": sha256_file(root / "data/sources.db") if (root / "data/sources.db").is_file() else None,
    }


def build_artifacts(
    *,
    root: Path = ROOT,
    source_universe: Path = DEFAULT_SOURCE_UNIVERSE,
    sources_db: Path = DEFAULT_SOURCES_DB,
    private_dir: Path = DEFAULT_PRIVATE_DIR,
    public_dir: Path = DEFAULT_PUBLIC_DIR,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    eval_contract_path: Path = DEFAULT_EVAL_CONTRACT,
    coverage_contract_path: Path = DEFAULT_COVERAGE_CONTRACT,
    near_dup_policy_path: Path = DEFAULT_NEAR_DUP_POLICY,
    schema_path: Path = DEFAULT_SCHEMA,
    skip_source_freeze_git_binding: bool = False,
) -> dict[str, Any]:
    """Build private seals/clearance and the public aggregate receipt."""
    if not skip_source_freeze_git_binding:
        source_freeze.validate(source_universe, repo_root=root)
    else:
        # Synthetic tests may supply a miniature freeze directory.
        require((source_universe / "ua_gec.units.jsonl").is_file(), "synthetic freeze missing ua_gec units")

    role_contract = read_json(role_contract_path)
    role_binding = verify_role_binding(role_contract)
    policy = near.policy_for_governed_use(
        "train_development_to_heldout_firewall",
        path=near_dup_policy_path,
        expected_fingerprint=near.PINNED_POLICY_FINGERPRINT,
    )
    near.policy_for_governed_use("ua_eval_exclusion", path=near_dup_policy_path)
    near.policy_for_governed_use("public_canary_neighbour_exclusion", path=near_dup_policy_path)

    ua_eval_manifest, public_canary_manifest = None, None
    exact_fps, near_surfaces, excluded_rows, excluded_docs, ua_eval_manifest, public_canary_manifest = (
        _load_exclusion_surfaces(root=root)
    )

    freeze_units = _load_freeze_ua_gec_units(source_universe)
    rows = reconstruct_ua_gec_rows(sources_db=sources_db, freeze_units=freeze_units)
    partitioned = partition_ua_gec(
        rows,
        policy=policy,
        exact_fingerprints=exact_fps,
        exclusion_surfaces=near_surfaces,
        excluded_row_hashes=excluded_rows,
        excluded_doc_identities=excluded_docs,
    )

    bindings = build_input_bindings(
        root=root,
        source_universe=source_universe,
        role_contract_path=role_contract_path,
        eval_contract_path=eval_contract_path,
        coverage_contract_path=coverage_contract_path,
        near_dup_policy_path=near_dup_policy_path,
        ua_eval_manifest=ua_eval_manifest,
        public_canary_manifest=public_canary_manifest,
    )
    # Prefer live sources DB hash when reconstructing.
    bindings["sources_db_sha256"] = sha256_file(sources_db)

    heldout_ids = {item["unit_id"] for item in partitioned["heldout_units"]}
    sealed_units = [
        build_heldout_sealed_unit(row, sources_db_sha256=bindings["sources_db_sha256"])
        for row in rows
        if row["unit_id"] in heldout_ids
    ]
    sealed_units.sort(key=lambda item: (item["ordinal"], item["unit_id"]))
    require(len(sealed_units) == len(partitioned["heldout_units"]), "sealed custody row count drift")
    require(
        {item["unit_id"] for item in sealed_units} == heldout_ids,
        "sealed custody unit set drift",
    )

    heldout_seal = {
        "schema_version": "phase3_heldout_seal_receipt_v1",
        "text_free": False,
        "implementation_version": IMPLEMENTATION_VERSION,
        "role_binding": role_binding,
        "input_bindings": bindings,
        "family_id": UA_GEC_FAMILY,
        "sealed_units": sealed_units,
        "sealed_unit_count": len(sealed_units),
        "sealed_document_count": partitioned["heldout_document_count"],
        "label_state": CAPABILITY_STATE,
    }
    heldout_seal = attach_receipt_hash(heldout_seal)

    author_clearance = attach_receipt_hash(
        {
            "schema_version": "phase3_author_clearance_receipt_v1",
            "text_free": True,
            "implementation_version": IMPLEMENTATION_VERSION,
            "role_binding": role_binding,
            "input_bindings": {
                key: bindings[key]
                for key in (
                    "combined_contract_sha256",
                    "role_contract_sha256",
                    "evaluation_contract_sha256",
                    "coverage_contract_sha256",
                    "source_universe_receipt_sha256",
                    "near_duplicate_policy_fingerprint_sha256",
                    "ua_eval_exclusion_manifest_sha256",
                    "public_canary_exclusion_manifest_sha256",
                )
            },
            "cleared_units": [
                {
                    "unit_id": item["unit_id"],
                    "unit_sha256": item["unit_sha256"],
                    "family_id": item["family_id"],
                }
                for item in partitioned["author_cleared_units"]
            ],
            "cleared_unit_count": len(partitioned["author_cleared_units"]),
            "heldout_excluded": True,
            "ua_eval_exclusion_enforced": True,
            "public_canary_exclusion_enforced": True,
            "heldout_complement_encoded": False,
            "fingerprints_encoded": False,
            "locators_encoded": False,
        }
    )

    leakage = attach_receipt_hash(
        {
            "schema_version": "phase3_heldout_leakage_verification_v1",
            "text_free": True,
            "zero_overlap": partitioned["zero_overlap"],
            "near_duplicate_policy_fingerprint_sha256": near.PINNED_POLICY_FINGERPRINT,
            "ua_eval_exclusion_enforced": True,
            "public_canary_exclusion_enforced": True,
            "malformed_comparisons_fail_closed": True,
            "cross_layer_doc_id_collapsed": True,
        }
    )

    partition_verification = attach_receipt_hash(
        {
            "schema_version": "phase3_heldout_partition_verification_v1",
            "text_free": True,
            "ua_gec_input_total": len(rows),
            "heldout_sealed_unit_total": len(partitioned["heldout_units"]),
            "author_cleared_unit_total": len(partitioned["author_cleared_units"]),
            "author_omitted_unit_total": sum(partitioned["omit_reasons"].values()),
            "omit_reason_totals": partitioned["omit_reasons"],
            "zero_overlap": partitioned["zero_overlap"],
            "role_binding": role_binding,
        }
    )

    non_ua_gec_shortfall = {
        "code": SHORTFALL_CODE,
        "detail": SHORTFALL_DETAIL,
        "families_not_sealed": SHORTFALL_FAMILIES,
        "denominator_shrinkage": False,
    }

    public_receipt = {
        "schema_version": "phase3_heldout_public_receipt_v1",
        "text_free": True,
        "implementation_version": IMPLEMENTATION_VERSION,
        "role_binding": role_binding,
        "input_bindings": {
            "combined_contract_sha256": bindings["combined_contract_sha256"],
            "role_contract_sha256": bindings["role_contract_sha256"],
            "evaluation_contract_sha256": bindings["evaluation_contract_sha256"],
            "coverage_contract_sha256": bindings["coverage_contract_sha256"],
            "source_universe_receipt_sha256": bindings["source_universe_receipt_sha256"],
            "near_duplicate_policy_fingerprint_sha256": bindings["near_duplicate_policy_fingerprint_sha256"],
            "ua_eval_exclusion_manifest_sha256": bindings["ua_eval_exclusion_manifest_sha256"],
            "public_canary_exclusion_manifest_sha256": bindings["public_canary_exclusion_manifest_sha256"],
            "sources_db_sha256": bindings["sources_db_sha256"],
        },
        "artifact_hashes": {
            "heldout_seal_sha256": heldout_seal["receipt_sha256"],
            "author_clearance_sha256": author_clearance["receipt_sha256"],
            "partition_verification_sha256": partition_verification["receipt_sha256"],
            "leakage_verification_sha256": leakage["receipt_sha256"],
        },
        "aggregates": {
            "ua_gec_input_total": len(rows),
            "heldout_sealed_unit_total": len(partitioned["heldout_units"]),
            "author_cleared_unit_total": len(partitioned["author_cleared_units"]),
            "author_omitted_unit_total": sum(partitioned["omit_reasons"].values()),
            "omit_reason_code_count": len(partitioned["omit_reasons"]),
        },
        "zero_overlap": partitioned["zero_overlap"],
        "capability": {
            "state": CAPABILITY_STATE,
            "per_phenomenon_floors_claimed": False,
            "automatic_rule_activation_floors_claimed": False,
            "shortfalls": [non_ua_gec_shortfall],
        },
    }
    _assert_no_forbidden_public_fields(public_receipt)
    public_receipt = attach_receipt_hash(public_receipt)
    require(receipt_body_sha256(public_receipt) == public_receipt["receipt_sha256"], "public receipt body hash drift")

    schema = read_json(schema_path) if schema_path.is_file() else None
    if schema is not None:
        _schema_validate(bindings, schema, "inputBindings")
        _schema_validate(heldout_seal, schema, "heldoutSealReceipt")
        _schema_validate(author_clearance, schema, "authorClearanceReceipt")
        _schema_validate(public_receipt, schema, "publicReceipt")
        _schema_validate(partition_verification, schema, "partitionVerificationReceipt")
        _schema_validate(leakage, schema, "leakageVerificationReceipt")

    private_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(private_dir, PRIVATE_DIR_MODE)
    paths = {
        "ua_eval_exclusion_manifest": private_dir / "ua_eval_exclusion_manifest_v1.json",
        "public_canary_exclusion_manifest": private_dir / "public_canary_exclusion_manifest_v1.json",
        "heldout_seal": private_dir / "heldout_seal_v1.json",
        "author_clearance": private_dir / "author_clearance_v1.json",
        "partition_verification": private_dir / "partition_verification_v1.json",
        "leakage_verification": private_dir / "leakage_verification_v1.json",
        "public_receipt": public_dir / "public_receipt_v1.json",
    }
    write_private_json(paths["ua_eval_exclusion_manifest"], ua_eval_manifest)
    write_private_json(paths["public_canary_exclusion_manifest"], public_canary_manifest)
    write_private_json(paths["heldout_seal"], heldout_seal)
    write_private_json(paths["author_clearance"], author_clearance)
    write_private_json(paths["partition_verification"], partition_verification)
    write_private_json(paths["leakage_verification"], leakage)
    public_hash = write_public_json(paths["public_receipt"], public_receipt)
    require(public_hash == sha256_file(paths["public_receipt"]), "public receipt write drift")
    require(receipt_body_sha256(public_receipt) == public_receipt["receipt_sha256"], "public receipt body hash drift after write")

    return {
        "ok": True,
        "public_receipt_path": str(paths["public_receipt"].relative_to(root)),
        "public_receipt_sha256": public_receipt["receipt_sha256"],
        "heldout_seal_path": str(paths["heldout_seal"].relative_to(root)),
        "heldout_seal_sha256": heldout_seal["receipt_sha256"],
        "author_clearance_path": str(paths["author_clearance"].relative_to(root)),
        "author_clearance_sha256": author_clearance["receipt_sha256"],
        "aggregates": public_receipt["aggregates"],
        "zero_overlap": public_receipt["zero_overlap"],
        "capability_state": CAPABILITY_STATE,
    }


def _assert_author_clearance_text_free(author: Mapping[str, Any]) -> None:
    """Author clearance stays separate and must not encode held-out custody material."""
    require(author.get("text_free") is True, "author clearance must remain text-free")
    require(author.get("heldout_complement_encoded") is False, "author clearance encodes complement")
    require(author.get("fingerprints_encoded") is False, "author clearance encodes fingerprints")
    require(author.get("locators_encoded") is False, "author clearance encodes locators")
    require(author.get("heldout_excluded") is True, "author clearance does not attest heldout exclusion")
    require(author.get("ua_eval_exclusion_enforced") is True, "author clearance does not attest UA Eval exclusion")
    require(
        author.get("public_canary_exclusion_enforced") is True,
        "author clearance does not attest public-canary exclusion",
    )
    require("sealed_unit_count" not in author, "author clearance contains held-out counts")
    require("sealed_document_count" not in author, "author clearance contains held-out document counts")
    forbidden_unit_keys = frozenset(
        {
            "error",
            "correct",
            "locator",
            "locators",
            "error_span_fingerprint_sha256",
            "correct_span_fingerprint_sha256",
            "span_fingerprint",
            "normalized_surface",
            "source_document_identity",
            "primary_key_sha256",
            "label",
            "labels",
            "canary",
            "canaries",
        }
    )
    for unit in author.get("cleared_units", []):
        require(isinstance(unit, Mapping), "author cleared unit malformed")
        overlap = forbidden_unit_keys.intersection(unit)
        require(not overlap, f"author clearance encodes forbidden custody fields: {sorted(overlap)}")
        unit_dump = canonical_json(unit)
        require("heldout" not in unit_dump, "author clearance unit names heldout")
        require('"locator"' not in unit_dump, "author clearance unit encodes locator key")
        require("span_fingerprint" not in unit_dump, "author clearance unit encodes span fingerprints")
        require("normalized_surface" not in unit_dump, "author clearance unit encodes normalized surfaces")


def verify_heldout_seal_custody(
    heldout_receipt: Mapping[str, Any],
    *,
    sources_db: Path,
    source_universe: Path,
) -> None:
    """Fail closed on sealed byte, locator, fingerprint, or binding drift."""
    require(heldout_receipt.get("text_free") is False, "heldout seal must declare text_free:false")
    bindings = heldout_receipt.get("input_bindings")
    require(isinstance(bindings, Mapping), "heldout seal input bindings missing")
    sources_db_sha256 = bindings.get("sources_db_sha256")
    policy_fp = bindings.get("near_duplicate_policy_fingerprint_sha256")
    require(isinstance(sources_db_sha256, str), "heldout seal sources_db binding missing")
    require(isinstance(policy_fp, str), "heldout seal policy fingerprint binding missing")
    require(sha256_file(sources_db) == sources_db_sha256, "live sources.db drifts from sealed binding")
    require(policy_fp == near.PINNED_POLICY_FINGERPRINT, "heldout seal policy fingerprint pin drift")

    freeze_units = _load_freeze_ua_gec_units(source_universe)
    live_rows = reconstruct_ua_gec_rows(sources_db=sources_db, freeze_units=freeze_units)
    by_unit_id = {row["unit_id"]: row for row in live_rows}
    sealed_units = heldout_receipt.get("sealed_units")
    require(isinstance(sealed_units, list), "heldout seal sealed_units missing")
    require(len(sealed_units) == heldout_receipt.get("sealed_unit_count"), "sealed_unit_count drift")

    seen: set[str] = set()
    for unit in sealed_units:
        require(isinstance(unit, Mapping), "sealed unit malformed")
        unit_id = unit.get("unit_id")
        require(isinstance(unit_id, str) and unit_id not in seen, "sealed unit_id missing or duplicated")
        seen.add(unit_id)
        live = by_unit_id.get(unit_id)
        require(live is not None, "sealed unit absent from frozen sources reconstruction")
        require(unit.get("unit_sha256") == live["unit_sha256"], "sealed frozen unit hash drift")
        require(
            unit.get("source_document_identity") == live["source_document_identity"],
            "sealed source-document identity drift",
        )
        require(unit.get("primary_key_sha256") == live["primary_key_sha256"], "sealed primary key drift")
        require(unit.get("error") == live["error"], "sealed error byte drift")
        require(unit.get("correct") == live["correct"], "sealed correct byte drift")
        require(
            frozen_locator_binding(unit.get("locator", {})) == frozen_locator_binding(live["locator"]),
            "sealed locator drift",
        )
        expected = span_fingerprints_for_pair(str(unit["error"]), str(unit["correct"]))
        require(
            unit.get("error_span_fingerprint_sha256") == expected["error_span_fingerprint_sha256"],
            "sealed error fingerprint drift",
        )
        require(
            unit.get("correct_span_fingerprint_sha256") == expected["correct_span_fingerprint_sha256"],
            "sealed correct fingerprint drift",
        )
        require(unit.get("sources_db_sha256") == sources_db_sha256, "sealed unit sources_db binding drift")
        require(
            unit.get("near_duplicate_policy_fingerprint_sha256") == policy_fp,
            "sealed unit policy fingerprint drift",
        )
        require(unit.get("split") == live["split"] == "test", "sealed unit is not an exact test unit")
        require(unit.get("ordinal") == live["ordinal"], "sealed unit ordinal drift")
    expected_test_ids = {row["unit_id"] for row in live_rows if row["split"] == "test"}
    require(seen == expected_test_ids, "sealed custody does not exactly cover the frozen test denominator")


def verify_artifacts(
    *,
    root: Path = ROOT,
    private_dir: Path = DEFAULT_PRIVATE_DIR,
    public_dir: Path = DEFAULT_PUBLIC_DIR,
    schema_path: Path = DEFAULT_SCHEMA,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    eval_contract_path: Path = DEFAULT_EVAL_CONTRACT,
    coverage_contract_path: Path = DEFAULT_COVERAGE_CONTRACT,
    near_dup_policy_path: Path = DEFAULT_NEAR_DUP_POLICY,
    sources_db: Path = DEFAULT_SOURCES_DB,
    source_universe: Path = DEFAULT_SOURCE_UNIVERSE,
    require_private: bool = True,
    skip_source_freeze_git_binding: bool = False,
) -> dict[str, Any]:
    public_path = public_dir / "public_receipt_v1.json"
    public_receipt = read_json(public_path)
    require(receipt_body_sha256(public_receipt) == public_receipt.get("receipt_sha256"), "public receipt hash drift")
    _assert_no_forbidden_public_fields(public_receipt)
    role_binding = verify_role_binding(read_json(role_contract_path))
    require(public_receipt.get("role_binding") == role_binding, "public role binding drift")
    require(
        public_receipt.get("capability")
        == {
            "state": CAPABILITY_STATE,
            "per_phenomenon_floors_claimed": False,
            "automatic_rule_activation_floors_claimed": False,
            "shortfalls": [
                {
                    "code": SHORTFALL_CODE,
                    "detail": SHORTFALL_DETAIL,
                    "families_not_sealed": SHORTFALL_FAMILIES,
                    "denominator_shrinkage": False,
                }
            ],
        },
        "capability state or shortfall drift",
    )
    require(
        public_receipt.get("input_bindings", {}).get("role_contract_sha256") == sha256_file(role_contract_path),
        "public receipt role-contract hash drift",
    )
    require(
        public_receipt.get("input_bindings", {}).get("evaluation_contract_sha256") == sha256_file(eval_contract_path),
        "public receipt evaluation-contract hash drift",
    )
    require(
        public_receipt.get("input_bindings", {}).get("coverage_contract_sha256") == sha256_file(coverage_contract_path),
        "public receipt coverage-contract hash drift",
    )

    schema = read_json(schema_path)
    _schema_validate(public_receipt, schema, "publicReceipt")
    public_aggregates = public_receipt.get("aggregates")
    require(isinstance(public_aggregates, Mapping), "public aggregates missing")
    require(
        public_aggregates.get("ua_gec_input_total")
        == public_aggregates.get("heldout_sealed_unit_total")
        + public_aggregates.get("author_cleared_unit_total")
        + public_aggregates.get("author_omitted_unit_total"),
        "public aggregate denominator arithmetic drift",
    )

    result: dict[str, Any] = {
        "ok": True,
        "public_receipt_sha256": public_receipt["receipt_sha256"],
        "private_verified": False,
        "zero_overlap": public_receipt.get("zero_overlap"),
        "aggregates": public_receipt.get("aggregates"),
        "capability_state": CAPABILITY_STATE,
    }
    if not require_private:
        return result

    if not skip_source_freeze_git_binding:
        source_freeze.validate(source_universe, repo_root=root)
    else:
        require((source_universe / "ua_gec.units.jsonl").is_file(), "synthetic freeze missing ua_gec units")

    require(private_dir.is_dir(), "private steward directory missing")
    require((private_dir.stat().st_mode & 0o777) == PRIVATE_DIR_MODE, "private steward directory permissions too open")
    private_paths = {
        "ua_eval_manifest": private_dir / "ua_eval_exclusion_manifest_v1.json",
        "public_canary_manifest": private_dir / "public_canary_exclusion_manifest_v1.json",
        "heldout": private_dir / "heldout_seal_v1.json",
        "author": private_dir / "author_clearance_v1.json",
        "partition": private_dir / "partition_verification_v1.json",
        "leakage": private_dir / "leakage_verification_v1.json",
    }
    require(all(path.is_file() for path in private_paths.values()), "private steward artifacts missing")
    for name, path in private_paths.items():
        require((path.stat().st_mode & 0o777) == PRIVATE_MODE, f"private artifact permissions too open: {name}")
    heldout_path = private_paths["heldout"]
    author_path = private_paths["author"]
    heldout_receipt = read_json(heldout_path)
    author = read_json(author_path)
    partition_receipt = read_json(private_paths["partition"])
    leakage_receipt = read_json(private_paths["leakage"])
    ua_eval_manifest = read_json(private_paths["ua_eval_manifest"])
    public_canary_manifest = read_json(private_paths["public_canary_manifest"])
    require(receipt_body_sha256(heldout_receipt) == heldout_receipt.get("receipt_sha256"), "heldout seal hash drift")
    require(receipt_body_sha256(author) == author.get("receipt_sha256"), "author clearance hash drift")
    require(
        receipt_body_sha256(partition_receipt) == partition_receipt.get("receipt_sha256"),
        "partition verification hash drift",
    )
    require(
        receipt_body_sha256(leakage_receipt) == leakage_receipt.get("receipt_sha256"),
        "leakage verification hash drift",
    )
    require(
        sha256_value({key: value for key, value in ua_eval_manifest.items() if key != "manifest_sha256"})
        == ua_eval_manifest.get("manifest_sha256"),
        "UA Eval exclusion manifest hash drift",
    )
    require(
        sha256_value({key: value for key, value in public_canary_manifest.items() if key != "manifest_sha256"})
        == public_canary_manifest.get("manifest_sha256"),
        "public-canary exclusion manifest hash drift",
    )
    _schema_validate(heldout_receipt, schema, "heldoutSealReceipt")
    _schema_validate(author, schema, "authorClearanceReceipt")
    _schema_validate(partition_receipt, schema, "partitionVerificationReceipt")
    _schema_validate(leakage_receipt, schema, "leakageVerificationReceipt")
    require(
        public_receipt["artifact_hashes"]["heldout_seal_sha256"] == heldout_receipt["receipt_sha256"],
        "public heldout hash binding drift",
    )
    require(
        public_receipt["artifact_hashes"]["author_clearance_sha256"] == author["receipt_sha256"],
        "public author clearance hash binding drift",
    )
    require(
        public_receipt["artifact_hashes"]["partition_verification_sha256"] == partition_receipt["receipt_sha256"],
        "public partition verification hash binding drift",
    )
    require(
        public_receipt["artifact_hashes"]["leakage_verification_sha256"] == leakage_receipt["receipt_sha256"],
        "public leakage verification hash binding drift",
    )
    require(
        public_receipt["input_bindings"]["ua_eval_exclusion_manifest_sha256"] == ua_eval_manifest["manifest_sha256"],
        "public UA Eval exclusion manifest binding drift",
    )
    require(
        public_receipt["input_bindings"]["public_canary_exclusion_manifest_sha256"]
        == public_canary_manifest["manifest_sha256"],
        "public-canary exclusion manifest binding drift",
    )
    exact_fps, near_surfaces, excluded_rows, excluded_docs, expected_ua_eval, expected_canary = (
        _load_exclusion_surfaces(root=root)
    )
    require(ua_eval_manifest == expected_ua_eval, "UA Eval exclusion manifest does not match live bound sources")
    require(
        public_canary_manifest == expected_canary, "public-canary exclusion manifest does not match live bound sources"
    )
    require(
        heldout_receipt.get("input_bindings", {}).get("role_contract_sha256") == sha256_file(role_contract_path),
        "private seal role-contract hash drift",
    )
    verify_heldout_seal_custody(
        heldout_receipt,
        sources_db=sources_db,
        source_universe=source_universe,
    )
    live_rows = reconstruct_ua_gec_rows(
        sources_db=sources_db,
        freeze_units=_load_freeze_ua_gec_units(source_universe),
    )
    policy = near.policy_for_governed_use(
        "train_development_to_heldout_firewall",
        path=near_dup_policy_path,
        expected_fingerprint=near.PINNED_POLICY_FINGERPRINT,
    )
    near.policy_for_governed_use("ua_eval_exclusion", path=near_dup_policy_path)
    near.policy_for_governed_use("public_canary_neighbour_exclusion", path=near_dup_policy_path)
    recomputed_partition = partition_ua_gec(
        live_rows,
        policy=policy,
        exact_fingerprints=exact_fps,
        exclusion_surfaces=near_surfaces,
        excluded_row_hashes=excluded_rows,
        excluded_doc_identities=excluded_docs,
    )
    live_by_id = {row["unit_id"]: row for row in live_rows}
    heldout_ids = {item["unit_id"] for item in heldout_receipt.get("sealed_units", [])}
    author_ids = {item["unit_id"] for item in author.get("cleared_units", [])}
    require(heldout_ids.isdisjoint(author_ids), "verify found author/held-out unit overlap")
    _assert_author_clearance_text_free(author)
    require(len(author_ids) == author.get("cleared_unit_count"), "author cleared-unit count drift")
    for unit in author.get("cleared_units", []):
        live = live_by_id.get(unit["unit_id"])
        require(live is not None and live["split"] == "train", "author clearance contains a non-train unit")
        require(unit.get("unit_sha256") == live["unit_sha256"], "author cleared-unit hash drift")
        require(unit.get("family_id") == UA_GEC_FAMILY, "author cleared-unit family drift")
    recomputed_author_units = [
        {
            "unit_id": item["unit_id"],
            "unit_sha256": item["unit_sha256"],
            "family_id": item["family_id"],
        }
        for item in recomputed_partition["author_cleared_units"]
    ]
    require(
        author.get("cleared_units") == recomputed_author_units,
        "author clearance differs from live exclusion-safe partition",
    )
    require(
        heldout_ids == {item["unit_id"] for item in recomputed_partition["heldout_units"]},
        "heldout seal differs from live recomputed partition",
    )

    require(partition_receipt.get("role_binding") == role_binding, "partition verification role binding drift")
    require(heldout_receipt.get("role_binding") == role_binding, "heldout seal role binding drift")
    require(author.get("role_binding") == role_binding, "author clearance role binding drift")
    expected_author_bindings = {
        key: public_receipt["input_bindings"][key]
        for key in (
            "combined_contract_sha256",
            "role_contract_sha256",
            "evaluation_contract_sha256",
            "coverage_contract_sha256",
            "source_universe_receipt_sha256",
            "near_duplicate_policy_fingerprint_sha256",
            "ua_eval_exclusion_manifest_sha256",
            "public_canary_exclusion_manifest_sha256",
        )
    }
    require(author.get("input_bindings") == expected_author_bindings, "author clearance input binding drift")
    require(partition_receipt.get("zero_overlap") == leakage_receipt.get("zero_overlap"), "private zero-overlap drift")
    require(partition_receipt.get("zero_overlap") == public_receipt.get("zero_overlap"), "public zero-overlap drift")
    require(
        leakage_receipt.get("near_duplicate_policy_fingerprint_sha256") == near.PINNED_POLICY_FINGERPRINT,
        "leakage policy fingerprint drift",
    )
    omit_reason_totals = partition_receipt.get("omit_reason_totals")
    require(isinstance(omit_reason_totals, Mapping), "partition omit reasons missing")
    require(
        omit_reason_totals == recomputed_partition["omit_reasons"],
        "partition omit reasons differ from live exclusion-safe partition",
    )
    require(
        partition_receipt.get("author_omitted_unit_total") == sum(omit_reason_totals.values()),
        "partition omit-reason total drift",
    )
    expected_aggregates = {
        "ua_gec_input_total": len(live_rows),
        "heldout_sealed_unit_total": len(heldout_ids),
        "author_cleared_unit_total": len(author_ids),
        "author_omitted_unit_total": len(live_rows) - len(heldout_ids) - len(author_ids),
        "omit_reason_code_count": len(omit_reason_totals),
    }
    require(public_receipt.get("aggregates") == expected_aggregates, "public aggregates differ from private evidence")
    require(
        {
            key: partition_receipt.get(key)
            for key in (
                "ua_gec_input_total",
                "heldout_sealed_unit_total",
                "author_cleared_unit_total",
                "author_omitted_unit_total",
            )
        }
        == {key: expected_aggregates[key] for key in expected_aggregates if key != "omit_reason_code_count"},
        "partition denominator evidence drift",
    )
    result["private_verified"] = True
    result["heldout_seal_sha256"] = heldout_receipt["receipt_sha256"]
    result["author_clearance_sha256"] = author["receipt_sha256"]
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-universe", type=Path, default=None)
    parser.add_argument("--sources-db", type=Path, default=None)
    parser.add_argument("--private-dir", type=Path, default=None)
    parser.add_argument("--public-dir", type=Path, default=None)
    parser.add_argument("--schema", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build")
    build_parser.add_argument("--skip-source-freeze-git-binding", action="store_true")
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument(
        "--public-only",
        action="store_true",
        help="Validate the public receipt without opening private steward bodies.",
    )
    verify_parser.add_argument(
        "--skip-source-freeze-git-binding",
        action="store_true",
        help="Skip git-bound freeze validation (synthetic fixtures only).",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    source_universe = (args.source_universe or (root / DEFAULT_SOURCE_UNIVERSE.relative_to(ROOT))).resolve()
    sources_db = (args.sources_db or (root / DEFAULT_SOURCES_DB.relative_to(ROOT))).resolve()
    private_dir = (args.private_dir or (root / DEFAULT_PRIVATE_DIR.relative_to(ROOT))).resolve()
    public_dir = (args.public_dir or (root / DEFAULT_PUBLIC_DIR.relative_to(ROOT))).resolve()
    schema = (args.schema or (root / DEFAULT_SCHEMA.relative_to(ROOT))).resolve()
    try:
        if args.command == "build":
            result = build_artifacts(
                root=root,
                source_universe=source_universe,
                sources_db=sources_db,
                private_dir=private_dir,
                public_dir=public_dir,
                role_contract_path=root / DEFAULT_ROLE_CONTRACT.relative_to(ROOT),
                eval_contract_path=root / DEFAULT_EVAL_CONTRACT.relative_to(ROOT),
                coverage_contract_path=root / DEFAULT_COVERAGE_CONTRACT.relative_to(ROOT),
                near_dup_policy_path=root / DEFAULT_NEAR_DUP_POLICY.relative_to(ROOT),
                schema_path=schema,
                skip_source_freeze_git_binding=bool(args.skip_source_freeze_git_binding),
            )
        else:
            result = verify_artifacts(
                root=root,
                private_dir=private_dir,
                public_dir=public_dir,
                schema_path=schema,
                role_contract_path=root / DEFAULT_ROLE_CONTRACT.relative_to(ROOT),
                eval_contract_path=root / DEFAULT_EVAL_CONTRACT.relative_to(ROOT),
                coverage_contract_path=root / DEFAULT_COVERAGE_CONTRACT.relative_to(ROOT),
                near_dup_policy_path=root / DEFAULT_NEAR_DUP_POLICY.relative_to(ROOT),
                sources_db=sources_db,
                source_universe=source_universe,
                require_private=not bool(args.public_only),
                skip_source_freeze_git_binding=bool(
                    getattr(args, "skip_source_freeze_git_binding", False)
                ),
            )
    except PartitionError as exc:
        parser.error(str(exc))
    sys.stdout.write(canonical_json(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
