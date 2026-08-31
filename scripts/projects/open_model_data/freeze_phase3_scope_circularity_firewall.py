#!/usr/bin/env python3
"""Freeze #7427's metadata-only held-out and Cycle007 lineage firewall.

This module deliberately has no labeler or derivation callback.  It permits
builders to receive only the public freeze hashes.  The optional steward
runtime privately streams authenticated source/evidence bodies to construct a
mode-0600 collision corpus; it never exposes membership, labels, prompts,
source text, or private locators to builders or public output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import os
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_storage_custody as storage
from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_near_duplicate as near
from scripts.projects.open_model_data import phase3_source_unit_materialization as materialization

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
P1 = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P1_AMENDMENT = DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
P2 = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
NEAR_POLICY = DATA / "evidence/correction_protection_near_duplicate_policy_v1.json"
CYCLE007 = DATA / "reference/phase3_cycle007_storage_public_summary_v1.json"
OUTPUT = DATA / "evidence/phase3_scope_circularity_firewall_v1.json"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
PINS = {
    P1: "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b",
    P1_AMENDMENT: "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa",
    P2: "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    NEAR_POLICY: "fa30e82d7a5f90b7bf4b58d3aef6106b255dda270e81459a91ba011489fdb4b4",
}
DENY_NAMESPACES = (
    "row_ids", "packets", "examples", "source_units", "document_groups",
    "work_groups", "edition_groups", "sidecars", "annotations", "labels",
    "prompts", "paraphrases", "synthetic_siblings", "duplicates",
    "derivatives", "fingerprints",
)
FAIL_CODES = (
    "leakage", "uncertain_lineage", "graph_incompleteness", "hash_drift",
    "denominator_drift", "rights_provenance_corruption", "protected_damage",
    "custody_role_collision", "private_binding_unbound", "private_path_unsafe",
    "document_lineage_denominator_not_frozen", "unregistered_authority",
)
PRIVATE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700
STEWARD_CONFIG_ENV = "PHASE3_EVAL_STEWARD_CONFIG"
EXPECTED_OBJECT_SET_SHA256 = storage.EXPECTED_OBJECT_SET_SHA256
EXPECTED_ORDERED_ROW_IDENTITY_SHA256 = storage.EXPECTED_ORDERED_ROW_IDENTITY_SHA256
EXPECTED_PACK_MANIFEST_RECEIPT_SHA256 = "2a883cb3e9a3b2ee673e397c8f5ba511f886f725bea980b2c982ca17f92a5e7d"
CANDIDATE_LINEAGE_KEYS = (
    "packet", "sidecar", "annotation", "label_or_prompt", "paraphrase_parent",
    "synthetic_parent", "derivative_parent", "provenance_receipt", "raw_or_log",
    "provider_result_terminal",
)
ROW_DERIVED_DENY_ARRAYS = (
    "row", "source_example", "document_work_edition", "packet", "exact", "component",
)
PRIVATE_DENY_ARRAYS = (
    "sidecar", "annotation", "labeling_receipt", "prompt_or_request", "raw_or_log",
    "provider_result_terminal", "derivative", "paraphrase_parent", "synthetic_parent",
)
ALL_DENY_ARRAYS = ROW_DERIVED_DENY_ARRAYS + PRIVATE_DENY_ARRAYS


class FirewallError(ValueError):
    """Fail-closed firewall violation with a public-safe code only."""


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def artifact(path: Path) -> dict[str, str]:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FirewallError(code)


def _read_pinned(path: Path) -> dict[str, Any]:
    _require(sha256_file(path) == PINS[path], "hash_drift")
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), "hash_drift")
    return value


def _pinned_state() -> dict[str, Any]:
    p1, amendment, p2, near = (_read_pinned(path) for path in PINS)
    _require(p1.get("controlling_outcome_sha256") == OUTCOME_SHA256, "hash_drift")
    binding = p2.get("p1_binding")
    _require(isinstance(binding, dict), "denominator_drift")
    _require((binding.get("source_unit_count"), binding.get("unknown_rights_blocker_count"), binding.get("required_cell_count"), binding.get("composite_required_cell_count")) == (57, 39, 15, 16), "denominator_drift")
    statuses = binding.get("composite_required_cell_statuses")
    _require(isinstance(statuses, list) and len(statuses) == 16, "denominator_drift")
    counts = {state: sum(item.get("status") == state for item in statuses if isinstance(item, dict)) for state in ("coverage_blocked", "not_applicable_with_evidence")}
    _require(counts == {"coverage_blocked": 14, "not_applicable_with_evidence": 2}, "denominator_drift")
    _require(p2.get("rule_slot_universe", {}).get("slot_count") == 0, "denominator_drift")
    _require(near.get("schema_version") == "near_duplicate_policy_v1", "hash_drift")
    return {"p1": p1, "amendment": amendment, "p2": p2, "near": near}


def build_contract() -> dict[str, Any]:
    _pinned_state()
    cycle = json.loads(CYCLE007.read_text(encoding="utf-8"))
    _require(cycle.get("text_free") is True and cycle.get("outcome_sha256") == OUTCOME_SHA256, "hash_drift")
    _require((cycle.get("public_packet_count"), cycle.get("public_row_count")) == (204, 10159), "denominator_drift")
    return {
        "schema_version": "phase3_scope_circularity_firewall_v1", "text_free": True,
        "status": "FROZEN_METADATA_ONLY", "controlling_outcome_sha256": OUTCOME_SHA256,
        "phase_bindings": {"p1": artifact(P1), "p1_dialect_amendment": artifact(P1_AMENDMENT), "p2": artifact(P2), "near_duplicate_policy": artifact(NEAR_POLICY)},
        "denominator": {"source_units": 57, "unknown_rights_blockers": 39, "base_required_cells": 15, "composite_required_cells": 16, "coverage_blocked_cells": 14, "not_applicable_cells": 2, "rule_slots_R": 0, "membership_hash_required": True, "canonical_order_required": True},
        "split_firewall": {"atomicity": ["source", "document", "work", "edition", "exact_duplicate_component", "near_duplicate_connected_component"], "cell_requirement_records": 16, "heldout_cases_selected": 0, "zero_heldout_cases_state": "BLOCKED_NOT_ZERO", "builder_clearance": "positive_only_metadata_hashes", "builder_receives_membership": False, "derivation_callback_permitted": False, "private_steward_role": "evaluation_steward_only", "builder_steward_collision_forbidden": True},
        "cycle007": {"state": "evaluation_only", "deny_namespaces": list(DENY_NAMESPACES), "pack_manifest_receipt_sha256": EXPECTED_PACK_MANIFEST_RECEIPT_SHA256, "object_set_sha256": EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "public_packet_count": 204, "public_row_count": 10159, "physical_sidecar_count": 204, "logical_sidecar_count": 408, "object_count": 419, "private_binding_state": "UNBOUND", "fresh_private_materialization_claimed": False, "concept_reuse": "independent_origin_only_without_cycle007_identity_or_membership", "authority_reuse": "citation_only_without_heldout_span_locator_annotation_or_membership"},
        "fail_closed": {"terminal_codes": list(FAIL_CODES), "batch_failure_outputs": {"emitted": 0, "promoted": 0, "activated": 0}, "partial_denominator_permitted": False, "provider_calls": 0, "labels_created": 0, "gold_created": 0, "training_performed": False},
        "private_runtime": {"environment_binding": STEWARD_CONFIG_ENV, "file_mode": "0600", "directory_mode": "0700", "self_hash_verified_config_and_pack_manifest": True, "uses_cycle007_storage_pack_proof": True, "rejects": ["symlink", "hardlink", "traversal", "owner_mismatch", "path_overlap", "inode_device_change", "ancestor_replacement", "post_pin_toctou"], "public_output_text_free": True},
        "generator": artifact(Path(__file__)),
    }


def validate_contract_integrity(contract: Mapping[str, Any]) -> bool:
    try:
        return canonical_json(dict(contract)) == canonical_json(build_contract())
    except (FirewallError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def validate_builder_clearance(clearance: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    """Positive-only builder clearance. No membership or derived data is accepted."""
    try:
        generated = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    if not validate_contract_integrity(generated) or (contract is not None and canonical_json(dict(contract)) != canonical_json(generated)):
        return False
    allowed = {"p1_sha256", "p1_amendment_sha256", "p2_sha256", "near_duplicate_policy_sha256", "firewall_sha256"}
    if set(clearance) != allowed or not all(isinstance(value, str) and len(value) == 64 for value in clearance.values()):
        return False
    expected = {"p1_sha256": PINS[P1], "p1_amendment_sha256": PINS[P1_AMENDMENT], "p2_sha256": PINS[P2], "near_duplicate_policy_sha256": PINS[NEAR_POLICY], "firewall_sha256": sha256_file(OUTPUT) if OUTPUT.exists() else ""}
    return clearance == expected


def validate_pack_commitments(manifest: Mapping[str, Any], inventory: Mapping[str, Any]) -> bool:
    """Reject same-count pack, row-order, or object-membership substitutions."""
    try:
        storage._require_receipt(manifest, "hash_drift")
        objects = manifest.get("objects")
        return (
            manifest.get("schema_version") == storage.PACK_SCHEMA_VERSION
            and manifest.get("pack_kind") == "content_compact"
            and manifest.get("receipt_sha256") == EXPECTED_PACK_MANIFEST_RECEIPT_SHA256
            and manifest.get("object_set_sha256") == EXPECTED_OBJECT_SET_SHA256
            and manifest.get("ordered_row_identity_commitment_sha256") == EXPECTED_ORDERED_ROW_IDENTITY_SHA256
            and (manifest.get("packet_count"), manifest.get("row_count"), manifest.get("object_count")) == (204, 10159, 419)
            and isinstance(objects, list) and len(objects) == 419
            and all(isinstance(item, Mapping) and {"object_relative_path", "sha256", "stored_sha256", "storage", "selection_class", "selection_classes", "size_bytes", "role_relative_paths"} <= set(item) for item in objects)
            and (inventory.get("packet_count"), inventory.get("row_count"), inventory.get("object_count"), inventory.get("sidecar_count")) == (204, 10159, 419, 408)
            and inventory.get("object_set_sha256") == EXPECTED_OBJECT_SET_SHA256
            and inventory.get("ordered_row_identity_commitment_sha256") == EXPECTED_ORDERED_ROW_IDENTITY_SHA256
        )
    except (AttributeError, FirewallError, storage.StorageCustodyError):
        return False


def validate_lineage_batch(records: Sequence[Mapping[str, Any]], *, derive: Callable[[Mapping[str, Any]], Any] | None = None) -> dict[str, Any]:
    """Validate metadata-only identities; never invoke derive on any rejection."""
    required = {"candidate_id", "origin", "namespace", "membership_sha256", "component_sha256", "independent_origin"}
    seen: set[str] = set()
    for record in records:
        if set(record) != required or not all(isinstance(record[key], str) and record[key] for key in required):
            return {"ok": False, "code": "graph_incompleteness", "emitted": 0, "promoted": 0, "activated": 0}
        if record["candidate_id"] in seen or record["namespace"] in DENY_NAMESPACES or record["origin"] == "cycle007" or record["independent_origin"] != "true":
            return {"ok": False, "code": "leakage", "emitted": 0, "promoted": 0, "activated": 0}
        seen.add(record["candidate_id"])
    # Derivation is intentionally absent from the implementation contract.
    del derive
    return _zero("uncertain_lineage")


def _safe_private_path(path: Path, root: Path) -> tuple[int, os.stat_result]:
    _require(path.is_absolute() and not any(part == ".." for part in path.parts), "private_path_unsafe")
    _require(root.is_absolute() and path.is_relative_to(root), "private_path_unsafe")
    root_detail = os.lstat(root)
    _require(not stat.S_ISLNK(root_detail.st_mode) and stat.S_ISDIR(root_detail.st_mode), "private_path_unsafe")
    _require(root_detail.st_uid == os.getuid() and (root_detail.st_mode & 0o777) == PRIVATE_DIR_MODE, "private_path_unsafe")
    cursor = root
    for part in path.relative_to(root).parts[:-1]:
        cursor /= part
        detail = os.lstat(cursor)
        _require(not stat.S_ISLNK(detail.st_mode) and stat.S_ISDIR(detail.st_mode), "private_path_unsafe")
        _require(detail.st_uid == os.getuid() and (detail.st_mode & 0o777) == PRIVATE_DIR_MODE, "private_path_unsafe")
    before = os.lstat(path)
    _require(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode), "private_path_unsafe")
    _require(before.st_nlink == 1 and before.st_uid == os.getuid() and (before.st_mode & 0o777) == PRIVATE_MODE, "private_path_unsafe")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    after = os.fstat(fd)
    _require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "private_path_unsafe")
    return fd, before


def _secure_pack_object_fd(pack_dir: Path, relative: str) -> tuple[int, os.stat_result]:
    """Open a compact-pack object exactly once through no-follow dir fds."""
    parts = Path(relative).parts
    _require(parts and not Path(relative).is_absolute() and ".." not in parts, "private_path_unsafe")
    root_fd = os.open(pack_dir, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
    current = root_fd
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0), dir_fd=current)
            detail = os.fstat(next_fd)
            _require(stat.S_ISDIR(detail.st_mode) and detail.st_uid == os.getuid() and stat.S_IMODE(detail.st_mode) == PRIVATE_DIR_MODE, "private_path_unsafe")
            os.close(current)
            current = next_fd
        fd = os.open(parts[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=current)
        detail = os.fstat(fd)
        _require(stat.S_ISREG(detail.st_mode) and detail.st_nlink == 1 and detail.st_uid == os.getuid() and stat.S_IMODE(detail.st_mode) == PRIVATE_MODE, "private_path_unsafe")
        return fd, detail
    finally:
        os.close(current)


def _secure_object_raw(pack_dir: Path, item: Mapping[str, Any]) -> bytes:
    relative = item.get("object_relative_path")
    _require(isinstance(relative, str), "pack_shape_failure")
    fd, before = _secure_pack_object_fd(pack_dir, relative)
    try:
        stored = b"".join(iter(lambda: os.read(fd, 1024 * 1024), b""))
        _require(sha256_bytes(stored) == item.get("stored_sha256"), "identity_roundtrip_failure")
        os.lseek(fd, 0, os.SEEK_SET)
        storage_kind = item.get("storage")
        if storage_kind == "raw":
            raw = b"".join(iter(lambda: os.read(fd, 1024 * 1024), b""))
        elif storage_kind == "lzma":
            with lzma.open(os.fdopen(os.dup(fd), "rb"), "rb") as stream:
                raw = stream.read()
        elif storage_kind == "zstd":
            executable = storage._effective_zstd_executable(None)
            with os.fdopen(os.dup(fd), "rb") as source:
                process = subprocess.run([str(executable), *storage.ZSTD_DECOMPRESS_ARGS], stdin=source, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
            _require(process.returncode == 0, "identity_roundtrip_failure")
            raw = process.stdout
        else:
            raise FirewallError("pack_shape_failure")
        after = os.fstat(fd)
        _require((before.st_dev, before.st_ino, before.st_size) == (after.st_dev, after.st_ino, after.st_size), "private_path_unsafe")
        _require(sha256_bytes(raw) == item.get("sha256") and len(raw) == item.get("size_bytes"), "identity_roundtrip_failure")
        return raw
    except (OSError, lzma.LZMAError, subprocess.SubprocessError) as exc:
        raise FirewallError("identity_roundtrip_failure") from exc
    finally:
        os.close(fd)


def _secure_content_pack_proof(pack_dir: Path, manifest: Mapping[str, Any], inventory: Mapping[str, Any]) -> None:
    """Descriptor-pinned 419-object stream proof; no pack object path is reopened."""
    objects = manifest.get("objects")
    _require(isinstance(objects, list) and len(objects) == 419, "pack_shape_failure")
    restored: list[tuple[str, str]] = []
    stored_entries: list[dict[str, Any]] = []
    for item in objects:
        _require(isinstance(item, Mapping), "pack_shape_failure")
        _secure_object_raw(pack_dir, item)
        restored.extend((path, item["sha256"]) for path in item.get("role_relative_paths", []))
        stored_entries.append({"sha256": item["sha256"], "storage": item["storage"], "stored_sha256": item["stored_sha256"], "stored_size_bytes": int(item["stored_size_bytes"])})
    object_set = storage._pairs_digest(restored)
    _require(object_set == EXPECTED_OBJECT_SET_SHA256 and object_set == manifest.get("object_set_sha256"), "identity_roundtrip_failure")
    _require(len(restored) == inventory.get("selected_path_count") and sum(entry["stored_size_bytes"] for entry in stored_entries) == manifest.get("total_stored_payload_bytes"), "identity_roundtrip_failure")
    _require(manifest.get("stored_payload_digest") == storage.digest(storage.canonical(sorted(stored_entries, key=lambda entry: str(entry["sha256"]))),), "identity_roundtrip_failure")


def _zero(code: str) -> dict[str, Any]:
    return {"ok": False, "code": code, "emitted": 0, "promoted": 0, "activated": 0}


def _config_hash(value: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json({key: item for key, item in value.items() if key != "config_sha256"}))


def _safe_private_directory(path: Path, root: Path) -> None:
    _require(path.is_absolute() and path.is_relative_to(root), "private_path_unsafe")
    detail = os.lstat(path)
    _require(not stat.S_ISLNK(detail.st_mode) and stat.S_ISDIR(detail.st_mode), "private_path_unsafe")
    _require(detail.st_uid == os.getuid() and (detail.st_mode & 0o777) == PRIVATE_DIR_MODE, "private_path_unsafe")


def _validate_private_tree(path: Path, root: Path) -> None:
    """Reject any traversed component that could redirect or disclose custody."""
    _safe_private_directory(path, root)
    for directory, names, filenames in os.walk(path, followlinks=False):
        current = Path(directory)
        detail = os.lstat(current)
        _require(not stat.S_ISLNK(detail.st_mode) and detail.st_uid == os.getuid(), "private_path_unsafe")
        _require((detail.st_mode & 0o077) == 0, "private_path_unsafe")
        for name in [*names, *filenames]:
            candidate = current / name
            item = os.lstat(candidate)
            _require(not stat.S_ISLNK(item.st_mode) and item.st_uid == os.getuid(), "private_path_unsafe")
            _require((item.st_mode & 0o077) == 0, "private_path_unsafe")
            _require(stat.S_ISDIR(item.st_mode) or stat.S_ISREG(item.st_mode), "private_path_unsafe")


def _read_steward_config(config_path: Path) -> tuple[dict[str, Any], Path]:
    # The config names paths but never supplies an authority hash. The pack and
    # metadata sidecar are independently self-hash and content-proof checked.
    _require(config_path.is_absolute(), "private_path_unsafe")
    root = config_path.parent
    fd, before = _safe_private_path(config_path, root)
    try:
        payload = os.read(fd, 65537)
        _require(os.read(fd, 1) == b"", "private_path_unsafe")
    finally:
        os.close(fd)
    after = os.lstat(config_path)
    _require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "private_path_unsafe")
    value = json.loads(payload.decode("utf-8"))
    keys = {"schema_version", "private_root", "content_pack_directory", "steward_output_root", "steward_role", "config_sha256"}
    _require(isinstance(value, dict) and set(value) == keys, "private_path_unsafe")
    _require(value.get("schema_version") == "phase3_evaluation_steward_config_v1", "private_path_unsafe")
    _require(value.get("steward_role") == "evaluation_steward", "custody_role_collision")
    _require(value.get("config_sha256") == _config_hash(value), "hash_drift")
    private_root = Path(value["private_root"])
    _require(private_root.is_absolute() and private_root == root, "private_path_unsafe")
    _safe_private_directory(private_root, private_root)
    for key in ("content_pack_directory", "steward_output_root"):
        _require(isinstance(value[key], str) and Path(value[key]).is_absolute(), "private_path_unsafe")
        _require(Path(value[key]).is_relative_to(private_root), "private_path_unsafe")
    return value, private_root


def _canonical_packed_document_identity(entry: Mapping[str, Any]) -> str:
    """Validate the source-production packet contract before using its identity.

    The exact pack proof authenticates this field for the exceptional family
    that predates the old helper switch; unsupported caller candidates never
    receive this exception.
    """
    required = {"family_id", "unit_id", "unit_sha256", "source_locator", "source_text", "source_text_sha256", "source_record", "materialization_projection"}
    _require(required <= set(entry), "document_lineage_denominator_not_frozen")
    text = entry.get("source_text")
    locator = entry.get("source_locator")
    _require(isinstance(text, str) and isinstance(locator, Mapping) and isinstance(entry.get("source_record"), Mapping), "document_lineage_denominator_not_frozen")
    _require(entry.get("source_text_sha256") == sha256_bytes(text.encode()) and isinstance(entry.get("unit_sha256"), str) and len(entry["unit_sha256"]) == 64, "document_lineage_denominator_not_frozen")
    try:
        return materialization._identity(str(entry["family_id"]), entry["source_record"], {"locator": locator})
    except materialization.MaterializationError as exc:
        raise FirewallError("document_lineage_denominator_not_frozen") from exc


LABELING_RECEIPT_SCHEMA_COUNTS = {
    "phase3_cycle007_gemini_attempt_v2": 4,
    "phase3_cycle007_gemini_pre_call_v1": 2,
    "phase3_cycle007_gemini_request_plan_v1": 1,
    "phase3_cycle007_gemini_provider_stop_v3": 1,
}


def _receipt_commitment(receipt: Mapping[str, Any], *, object_sha256: str, fields: tuple[str, ...]) -> str:
    """Hash only authenticated metadata commitments, never emitted receipt data."""
    selected = {
        key: value
        for key, value in receipt.items()
        if any(token in key.lower() for token in fields)
    }
    return sha256_bytes(canonical_json({"object": object_sha256, "commitments": selected}))


def _metadata_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_metadata_common(receipt: Mapping[str, Any], keys: set[str]) -> bool:
    return (
        set(receipt) == keys
        and receipt.get("evaluation_cycle_id") == "phase3-v2-1-evaluation-cycle-007"
        and receipt.get("lane") in {"clean_label", "residual_label"}
        and receipt.get("exact_model") == "Gemini 3.6 Flash (High)"
        and receipt.get("model_family") == "google"
        and receipt.get("harness") == "agy"
        and receipt.get("text_free") is True
    )


def _validate_attempt_v2(receipt: Mapping[str, Any]) -> bool:
    """Closed terminal-attempt shape from the canonical Cycle007 guardian."""
    common = {
        "schema_version", "evaluation_cycle_id", "lane", "packet_index", "chunk_index", "attempt",
        "exact_model", "model_family", "harness", "text_free", "request_plan_sha256",
        "request_byte_budget", "request_byte_count", "state",
    }
    if receipt.get("state") == "started":
        return (
            _validate_metadata_common(receipt, common)
            and receipt.get("schema_version") == "phase3_cycle007_gemini_attempt_v2"
            and all(_positive_int(receipt.get(key)) for key in ("packet_index", "chunk_index", "attempt", "request_byte_budget", "request_byte_count"))
            and receipt["request_byte_count"] <= receipt["request_byte_budget"]
            and _metadata_digest(receipt.get("request_plan_sha256"))
        )
    terminal = common | {
        "failure_code", "failure_stage",
        "provider_call_started", "executable_binding_result", "provider_return_code", "raw_byte_count",
        "raw_sha256", "log_byte_count", "log_sha256", "init_count", "result_count",
        "first_event_kind", "last_event_kind", "model_binding_result", "result_status",
        "structured_output_type", "elapsed_milliseconds",
    }
    return (
        _validate_metadata_common(receipt, terminal)
        and receipt.get("schema_version") == "phase3_cycle007_gemini_attempt_v2"
        and receipt.get("state") == "terminal"
        and all(_positive_int(receipt.get(key)) for key in ("packet_index", "chunk_index", "attempt", "request_byte_budget", "request_byte_count"))
        and receipt["request_byte_count"] <= receipt["request_byte_budget"]
        and all(_metadata_digest(receipt.get(key)) for key in ("request_plan_sha256", "raw_sha256", "log_sha256"))
        and isinstance(receipt.get("provider_call_started"), bool)
        and all(_nonnegative_int(receipt.get(key)) for key in ("raw_byte_count", "log_byte_count", "init_count", "result_count"))
        and _nonnegative_int(receipt.get("elapsed_milliseconds"))
    )


def _validate_pre_call_v1(receipt: Mapping[str, Any]) -> bool:
    keys = {
        "schema_version", "evaluation_cycle_id", "lane", "packet_index", "chunk_index", "attempt",
        "request_plan_sha256", "planner_version", "row_count", "request_byte_budget", "request_byte_count",
        "estimated_input_tokens_ceiling", "ordered_identity_sha256", "text_free", "receipt_sha256",
    }
    return (
        set(receipt) == keys
        and receipt.get("schema_version") == "phase3_cycle007_gemini_pre_call_v1"
        and receipt.get("evaluation_cycle_id") == "phase3-v2-1-evaluation-cycle-007"
        and receipt.get("lane") in {"clean_label", "residual_label"}
        and receipt.get("text_free") is True
        and all(_positive_int(receipt.get(key)) for key in ("packet_index", "chunk_index", "attempt", "row_count", "request_byte_budget", "request_byte_count", "estimated_input_tokens_ceiling"))
        and receipt["request_byte_count"] <= receipt["request_byte_budget"]
        and all(_metadata_digest(receipt.get(key)) for key in ("request_plan_sha256", "ordered_identity_sha256", "receipt_sha256"))
    )


def _validate_request_plan_v1(receipt: Mapping[str, Any]) -> bool:
    keys = {
        "schema_version", "evaluation_cycle_id", "lane", "packet_index", "planner_version",
        "request_byte_budget", "row_count", "packet_identity_set_sha256", "label_prompt_sha256",
        "chunks", "text_free", "plan_sha256",
    }
    chunk_keys = {"chunk_index", "row_start", "row_end", "row_count", "request_byte_count", "estimated_input_tokens_ceiling", "ordered_identity_sha256"}
    chunks = receipt.get("chunks")
    return (
        set(receipt) == keys
        and receipt.get("schema_version") == "phase3_cycle007_gemini_request_plan_v1"
        and receipt.get("evaluation_cycle_id") == "phase3-v2-1-evaluation-cycle-007"
        and receipt.get("lane") in {"clean_label", "residual_label"}
        and receipt.get("text_free") is True
        and all(_positive_int(receipt.get(key)) for key in ("packet_index", "request_byte_budget", "row_count"))
        and all(_metadata_digest(receipt.get(key)) for key in ("packet_identity_set_sha256", "label_prompt_sha256", "plan_sha256"))
        and isinstance(chunks, list) and bool(chunks)
        and all(
            isinstance(chunk, Mapping)
            and set(chunk) == chunk_keys
            and all(_positive_int(chunk.get(key)) for key in ("chunk_index", "row_start", "row_end", "row_count", "request_byte_count", "estimated_input_tokens_ceiling"))
            and chunk["row_start"] <= chunk["row_end"]
            and chunk["request_byte_count"] <= receipt["request_byte_budget"]
            and _metadata_digest(chunk.get("ordered_identity_sha256"))
            for chunk in chunks
        )
    )


def _validate_provider_stop_v3(receipt: Mapping[str, Any]) -> bool:
    keys = {
        "schema_version", "evaluation_cycle_id", "lane", "terminal_packet_index", "failure_code",
        "new_provider_calls_allowed", "exact_model", "model_family", "harness", "text_free",
        "failure_stage", "provider_call_started", "executable_binding_result", "provider_return_code",
        "raw_byte_count", "raw_sha256", "log_byte_count", "log_sha256", "init_count", "result_count",
        "first_event_kind", "last_event_kind", "model_binding_result", "result_status", "structured_output_type",
        "chunk_index", "attempt", "terminal_marker_sha256", "request_plan_sha256", "request_byte_budget",
        "request_byte_count", "elapsed_milliseconds",
    }
    return (
        _validate_metadata_common(receipt, keys)
        and receipt.get("schema_version") == "phase3_cycle007_gemini_provider_stop_v3"
        and receipt.get("new_provider_calls_allowed") is False
        and isinstance(receipt.get("provider_call_started"), bool)
        and all(_positive_int(receipt.get(key)) for key in ("terminal_packet_index", "chunk_index", "attempt", "request_byte_budget", "request_byte_count"))
        and receipt["request_byte_count"] <= receipt["request_byte_budget"]
        and all(_nonnegative_int(receipt.get(key)) for key in ("raw_byte_count", "log_byte_count", "init_count", "result_count", "elapsed_milliseconds"))
        and all(_metadata_digest(receipt.get(key)) for key in ("raw_sha256", "log_sha256", "terminal_marker_sha256", "request_plan_sha256"))
    )


def _validate_labeling_metadata_receipt(receipt: Mapping[str, Any]) -> bool:
    schema = receipt.get("schema_version")
    return (
        _validate_attempt_v2(receipt) if schema == "phase3_cycle007_gemini_attempt_v2"
        else _validate_pre_call_v1(receipt) if schema == "phase3_cycle007_gemini_pre_call_v1"
        else _validate_request_plan_v1(receipt) if schema == "phase3_cycle007_gemini_request_plan_v1"
        else _validate_provider_stop_v3(receipt) if schema == "phase3_cycle007_gemini_provider_stop_v3"
        else False
    )


def _labeling_expansion_identities(pack_dir: Path, manifest: Mapping[str, Any]) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Protect the exact historical metadata-receipt census as deny lineage.

    The receipts authenticate historical provider attempts and terminal metadata.
    They are not new #7427 calls and no request/result body is retained here, but
    their object/request/prompt/raw/log/result/terminal identities must remain
    unavailable to any candidate builder.
    """
    by_schema = {schema: 0 for schema in LABELING_RECEIPT_SCHEMA_COUNTS}
    namespaces = {name: [] for name in ("labeling_receipt", "prompt_or_request", "raw_or_log", "provider_result_terminal", "derivative")}
    historical_provider_attempts = 0
    historical_result_receipts = 0
    historical_raw_log_receipts = 0
    for item in manifest["objects"]:
        if "labeling_expansion" not in item.get("selection_classes", [item.get("selection_class")]):
            continue
        raw = _secure_object_raw(pack_dir, item)
        receipt = json.loads(raw.decode("utf-8"))
        _require(
            isinstance(receipt, Mapping)
            and receipt.get("schema_version") in LABELING_RECEIPT_SCHEMA_COUNTS
            and _validate_labeling_metadata_receipt(receipt),
            "graph_incompleteness",
        )
        schema = str(receipt["schema_version"])
        by_schema[schema] += 1
        fields_forbidden_by_shape = schema in {
            "phase3_cycle007_gemini_pre_call_v1",
            "phase3_cycle007_gemini_request_plan_v1",
        } or (schema == "phase3_cycle007_gemini_attempt_v2" and receipt.get("state") == "started")
        _require(
            not fields_forbidden_by_shape
            or not {"provider_call_started", "result_count", "raw_byte_count", "log_byte_count"} & set(receipt),
            "graph_incompleteness",
        )
        started = receipt.get("provider_call_started") is True
        result = receipt.get("result_count", 0)
        raw_bytes = receipt.get("raw_byte_count", 0)
        log_bytes = receipt.get("log_byte_count", 0)
        _require(
            isinstance(result, int) and not isinstance(result, bool) and result >= 0
            and isinstance(raw_bytes, int) and not isinstance(raw_bytes, bool) and raw_bytes >= 0
            and isinstance(log_bytes, int) and not isinstance(log_bytes, bool) and log_bytes >= 0,
            "graph_incompleteness",
        )
        _require(
            result in {0, 1}
            and started == (result == 1) == (raw_bytes > 0 and log_bytes > 0),
            "graph_incompleteness",
        )
        historical_provider_attempts += int(started)
        historical_result_receipts += int(result > 0)
        historical_raw_log_receipts += int(raw_bytes > 0 and log_bytes > 0)
        object_sha256 = item.get("sha256")
        _require(isinstance(object_sha256, str) and len(object_sha256) == 64, "graph_incompleteness")
        namespaces["labeling_receipt"].append(object_sha256)
        namespaces["prompt_or_request"].append(_receipt_commitment(receipt, object_sha256=object_sha256, fields=("request", "prompt")))
        namespaces["raw_or_log"].append(_receipt_commitment(receipt, object_sha256=object_sha256, fields=("raw", "log")))
        namespaces["provider_result_terminal"].append(_receipt_commitment(receipt, object_sha256=object_sha256, fields=("result", "terminal", "provider_call")))
        namespaces["derivative"].append(_receipt_commitment(receipt, object_sha256=object_sha256, fields=("request", "prompt", "raw", "log", "result", "terminal", "provider_call")))
    _require(
        by_schema == LABELING_RECEIPT_SCHEMA_COUNTS
        and sum(by_schema.values()) == 8
        and (historical_provider_attempts, historical_result_receipts, historical_raw_log_receipts) == (3, 3, 3),
        "graph_incompleteness",
    )
    census = {
        "schema_counts": by_schema,
        "historical_provider_attempts": historical_provider_attempts,
        "historical_result_receipts": historical_result_receipts,
        "historical_raw_log_receipts": historical_raw_log_receipts,
        "bodies_available": False,
    }
    return {name: sorted(values) for name, values in namespaces.items()}, census


def _assert_closed_zero_namespace_census(manifest: Mapping[str, Any]) -> None:
    """Only the documented compact-pack selection classes can justify zeros."""
    known = {
        "materialization_packet", "materialization_custody", "materialization_manifest",
        "evidence_sidecar", "evidence_manifest", "labeling_expansion", "compile_expansion",
    }
    classes = {
        value
        for item in manifest["objects"]
        for value in item.get("selection_classes", [item.get("selection_class")])
    }
    _require(classes <= known, "graph_incompleteness")
    _require(not any("paraphrase" in str(value).lower() or "synthetic" in str(value).lower() for value in classes), "graph_incompleteness")


def _build_private_deny_corpus(pack_dir: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the source/example/document/exact/near graph inside the steward lane."""
    policy = near.policy_for_governed_use("train_development_to_heldout_firewall")
    rows: list[dict[str, str]] = []
    for item in manifest["objects"]:
        if "materialization_packet" not in item.get("selection_classes", [item.get("selection_class")]):
            continue
        raw = _secure_object_raw(pack_dir, item)
        payload = json.loads(raw.decode("utf-8"))
        entries = payload.get("rows") if isinstance(payload, Mapping) else None
        _require(isinstance(entries, list), "graph_incompleteness")
        for entry in entries:
            _require(isinstance(entry, Mapping), "graph_incompleteness")
            family = entry.get("family_id")
            source_record = entry.get("source_record")
            locator = entry.get("source_locator", entry.get("frozen_locator"))
            text = entry.get("source_text")
            unit_id, unit_sha256 = entry.get("unit_id"), entry.get("unit_sha256")
            document = _canonical_packed_document_identity(entry)
            _require(all(isinstance(value, str) and value for value in (family, text, unit_id, unit_sha256)), "document_lineage_denominator_not_frozen")
            _require(isinstance(source_record, Mapping) and isinstance(locator, Mapping) and len(unit_sha256) == 64, "document_lineage_denominator_not_frozen")
            fingerprint = near.fingerprint(str(text))
            source_example = sha256_bytes(canonical_json({"family_id": family, "source_record": source_record, "source_locator": locator}))
            rows.append({"row": sha256_bytes(canonical_json({"unit_id": unit_id, "unit_sha256": unit_sha256})), "source_example": source_example, "document_or_edition": sha256_bytes(document.encode()), "exact": fingerprint.exact_fingerprint, "surface": str(text), "normalized_surface": fingerprint.normalized_surface, "token_hashes": ",".join(sorted(sha256_bytes(token.encode()) for token in set(fingerprint.tokens))), "packet": sha256_bytes(str(item.get("packet_identity_set_sha256", item["sha256"])).encode())})
    _require(len(rows) == 10159 and len({row["row"] for row in rows}) == 10159, "graph_incompleteness")
    # Union source/example and explicit canonical document-or-edition groups,
    # then exact and pinned-0.9 near edges. No group is inferred from a path.
    parent = list(range(len(rows)))
    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    def union(left: int, right: int) -> None:
        first, second = find(left), find(right)
        if first != second:
            parent[max(first, second)] = min(first, second)
    for key in ("source_example", "document_or_edition", "exact"):
        seen: dict[str, int] = {}
        for index, row in enumerate(rows):
            if row[key] in seen:
                union(index, seen[row[key]])
            else:
                seen[row[key]] = index
    surfaces = [row["surface"] for row in rows]
    fingerprints: list[near.TextFingerprint] = []
    token_index: dict[str, list[int]] = {}
    for index, surface in enumerate(surfaces):
        for candidate in heldout._near_duplicate_candidates(surface, surfaces[:index], token_index=token_index, exclusion_fps=fingerprints):
            if near.duplicate_or_fail_closed(surface, surfaces[candidate], scope="span", policy=policy):
                union(index, candidate)
        fingerprint = near.fingerprint(surface)
        fingerprints.append(fingerprint)
        for token in set(fingerprint.tokens):
            token_index.setdefault(token, []).append(index)
    physical_sidecars = sum("evidence_sidecar" in item.get("selection_classes", []) for item in manifest["objects"])
    logical_sidecars = sum(item.get("selection_classes", []).count("evidence_sidecar") * len(item.get("role_relative_paths", [])) for item in manifest["objects"])
    _require(physical_sidecars == 204 and logical_sidecars == 408, "graph_incompleteness")
    components: dict[int, list[str]] = {}
    for index, row in enumerate(rows):
        components.setdefault(find(index), []).append(row["row"])
    component_by_row = {row_id: sha256_bytes(canonical_json(sorted(values))) for values in components.values() for row_id in values}
    sidecar_hashes = [sha256_bytes(str(item.get("sidecar_id")).encode()) for item in manifest["objects"] if "evidence_sidecar" in item.get("selection_classes", [])]
    labeling_namespaces, labeling_census = _labeling_expansion_identities(pack_dir, manifest)
    _assert_closed_zero_namespace_census(manifest)
    namespaces = {
        "row": sorted(row["row"] for row in rows),
        "source_example": sorted(row["source_example"] for row in rows),
        "document_work_edition": sorted(row["document_or_edition"] for row in rows),
        "packet": sorted(row["packet"] for row in rows),
        "sidecar": sorted(sidecar_hashes),
        "annotation": sorted(sidecar_hashes),
        "exact": sorted(row["exact"] for row in rows),
        "near_token": sorted(row["token_hashes"] for row in rows),
        "component": sorted(component_by_row.values()),
        "paraphrase_parent": [], "synthetic_parent": [],
    } | labeling_namespaces
    commitments = {name: {"count": len(values), "sha256": sha256_bytes(canonical_json(values))} for name, values in namespaces.items()}
    _require(set(ALL_DENY_ARRAYS) <= set(namespaces), "graph_incompleteness")
    private_arrays = {name: namespaces[name] for name in PRIVATE_DENY_ARRAYS}
    corpus = {"schema_version": "phase3_cycle007_private_deny_corpus_v1", "pack_manifest_receipt_sha256": manifest["receipt_sha256"], "object_set_sha256": EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "near_duplicate_policy_sha256": near.pinned_policy_fingerprint(), "namespace_commitments": commitments, "deny_arrays": private_arrays, "candidate_clearance_allowlist": [], "candidate_clearance_commitment_sha256": sha256_bytes(canonical_json([])), "labeling_expansion_census": labeling_census, "rows": [{key: value for key, value in row.items() if key != "surface"} | {"component": component_by_row[row["row"]]} for row in rows], "zero_namespace_proofs": {name: 0 for name in ("paraphrases", "synthetic_siblings")}}
    corpus["corpus_sha256"] = sha256_bytes(canonical_json(corpus))
    return corpus


def _content_pack_inventory(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct only the custody inventory view committed by the content pack."""
    objects = manifest.get("objects")
    _require(isinstance(objects, list) and len(objects) == 419, "denominator_drift")
    selected = sum(len(item.get("role_relative_paths", [])) for item in objects if isinstance(item, Mapping))
    inventory = {
        "packet_count": manifest.get("packet_count"), "row_count": manifest.get("row_count"),
        "object_count": len(objects), "sidecar_count": 408, "selected_path_count": selected,
        "object_set_sha256": manifest.get("object_set_sha256"),
        "ordered_row_identity_commitment_sha256": manifest.get("ordered_row_identity_commitment_sha256"),
        "receipt_sha256": manifest.get("inventory_receipt_sha256"), "objects": objects,
    }
    _require(selected == 624 and isinstance(inventory["receipt_sha256"], str), "denominator_drift")
    return inventory


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    payload = canonical_json(dict(value))
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, PRIVATE_MODE)
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_MODE)
        current = os.lstat(path)
        _require(current.st_nlink == 1 and stat.S_IMODE(current.st_mode) == PRIVATE_MODE, "private_path_unsafe")
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def _write_run_state(output_root: Path, state: str, *, code: str | None = None, corpus_sha256: str | None = None, receipt_sha256: str | None = None) -> None:
    value: dict[str, Any] = {"schema_version": "phase3_evaluation_steward_run_state_v1", "state": state, "text_free": True}
    if code is not None:
        value["code"] = code
    if corpus_sha256 is not None:
        value["corpus_sha256"] = corpus_sha256
    if receipt_sha256 is not None:
        value["public_receipt_sha256"] = receipt_sha256
    value["state_sha256"] = sha256_bytes(canonical_json(value))
    _write_private_json(output_root / "cycle007-firewall-run-state-v1.json", value)


def _load_private_json(path: Path, root: Path) -> dict[str, Any]:
    fd, before = _safe_private_path(path, root)
    try:
        chunks: list[bytes] = []
        while chunk := os.read(fd, 65536):
            chunks.append(chunk)
    finally:
        os.close(fd)
    after = os.lstat(path)
    _require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "private_path_unsafe")
    value = json.loads(b"".join(chunks).decode("utf-8"))
    _require(isinstance(value, dict), "private_path_unsafe")
    return value


def _candidate_clearance_binding(candidate: Mapping[str, Any]) -> str:
    """The evaluator, not a caller field, derives the full candidate lineage key."""
    return sha256_bytes(canonical_json({"schema_version": "phase3_evaluation_candidate_lineage_v1", "candidate": candidate}))


def _validate_private_deny_corpus(corpus: Mapping[str, Any]) -> dict[str, set[str]]:
    _require(corpus.get("corpus_sha256") == sha256_bytes(canonical_json({key: value for key, value in corpus.items() if key != "corpus_sha256"})), "hash_drift")
    _require(corpus.get("pack_manifest_receipt_sha256") == EXPECTED_PACK_MANIFEST_RECEIPT_SHA256 and corpus.get("near_duplicate_policy_sha256") == near.pinned_policy_fingerprint(), "hash_drift")
    arrays = corpus.get("deny_arrays")
    commitments = corpus.get("namespace_commitments")
    allowlist = corpus.get("candidate_clearance_allowlist")
    _require(isinstance(arrays, Mapping) and isinstance(commitments, Mapping) and isinstance(allowlist, list), "graph_incompleteness")
    _require(set(arrays) == set(PRIVATE_DENY_ARRAYS) and all(isinstance(arrays[name], list) and all(_metadata_digest(value) for value in arrays[name]) for name in PRIVATE_DENY_ARRAYS), "graph_incompleteness")
    _require(corpus.get("candidate_clearance_commitment_sha256") == sha256_bytes(canonical_json(sorted(allowlist))) and all(_metadata_digest(value) for value in allowlist), "hash_drift")
    rows = corpus.get("rows")
    _require(isinstance(rows, list) and all(isinstance(row, Mapping) and all(_metadata_digest(row.get(field)) for field in ("row", "source_example", "document_or_edition", "packet", "exact", "component")) for row in rows), "graph_incompleteness")
    derived = {
        "row": sorted(row["row"] for row in rows),
        "source_example": sorted(row["source_example"] for row in rows),
        "document_work_edition": sorted(row["document_or_edition"] for row in rows),
        "packet": sorted(row["packet"] for row in rows),
        "exact": sorted(row["exact"] for row in rows),
        "component": sorted(row["component"] for row in rows),
    }
    all_arrays = derived | dict(arrays)
    for name, values in all_arrays.items():
        item = commitments.get(name)
        _require(isinstance(item, Mapping) and item == {"count": len(values), "sha256": sha256_bytes(canonical_json(values))}, "hash_drift")
    return {name: set(values) for name, values in all_arrays.items()}


def evaluate_candidate_batch(candidates: Sequence[Mapping[str, Any]], corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Steward-only collision gate; novelty requires a private exact clearance."""
    try:
        denied = _validate_private_deny_corpus(corpus)
        surfaces = [row["normalized_surface"] for row in corpus["rows"]]
        primary_keys = {"evaluation_cycle_id", "family_id", "unit_id", "unit_sha256", "source_text", "source_record", "source_locator", "document_or_edition_identity"}
        for candidate in candidates:
            _require(isinstance(candidate, Mapping) and primary_keys <= set(candidate) <= primary_keys | {"lineage"} and candidate.get("evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-007", "uncertain_lineage")
            family, unit, digest, text, record, locator, document = (candidate.get(key) for key in ("family_id", "unit_id", "unit_sha256", "source_text", "source_record", "source_locator", "document_or_edition_identity"))
            _require(all(isinstance(value, str) and value for value in (family, unit, digest, text, document)) and isinstance(record, Mapping) and isinstance(locator, Mapping), "uncertain_lineage")
            row = sha256_bytes(canonical_json({"unit_id": unit, "unit_sha256": digest}))
            source = sha256_bytes(canonical_json({"family_id": family, "source_record": record, "source_locator": locator}))
            try:
                expected_document = materialization._identity(family, record, {"locator": locator})
            except materialization.MaterializationError as exc:
                raise FirewallError("uncertain_lineage") from exc
            _require(document == expected_document, "uncertain_lineage")
            fp = near.fingerprint(text)
            values = {"row": row, "source_example": source, "document_work_edition": sha256_bytes(document.encode()), "exact": fp.exact_fingerprint}
            if any(value in denied[key] for key, value in values.items()):
                return _zero("leakage")
            if any(near.duplicate_or_fail_closed(text, surface, scope="span", policy=near.policy_for_governed_use("train_development_to_heldout_firewall")) for surface in surfaces):
                return _zero("leakage")
            lineage = candidate.get("lineage")
            _require(isinstance(lineage, Mapping) and set(lineage) == set(CANDIDATE_LINEAGE_KEYS) and all(value is None or _metadata_digest(value) for value in lineage.values()), "uncertain_lineage")
            namespace_by_lineage = {"packet": "packet", "sidecar": "sidecar", "annotation": "annotation", "label_or_prompt": "prompt_or_request", "paraphrase_parent": "paraphrase_parent", "synthetic_parent": "synthetic_parent", "derivative_parent": "derivative", "provenance_receipt": "labeling_receipt", "raw_or_log": "raw_or_log", "provider_result_terminal": "provider_result_terminal"}
            if any(value is not None and value in denied[namespace_by_lineage[name]] for name, value in lineage.items()):
                return _zero("leakage")
            _require(_candidate_clearance_binding(candidate) in corpus["candidate_clearance_allowlist"], "uncertain_lineage")
    except (FirewallError, near.NearDuplicatePolicyError, KeyError, TypeError, ValueError):
        return _zero("uncertain_lineage")
    return {"ok": True, "code": None, "emitted": 0, "promoted": 0, "activated": 0}


def admit_concept_or_authority(record: Mapping[str, Any], registry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify only; P2's frozen nonadmitting registry cannot grant admission."""
    forbidden = {"row_id", "example_id", "document_id", "span", "locator", "annotation", "membership", "cycle007", "derivative", "prompt", "paraphrase", "synthetic"}
    try:
        _require(isinstance(record, Mapping), "uncertain_lineage")
        if any(token in key.lower() or token in str(value).lower() for key, value in record.items() for token in forbidden):
            return _zero("leakage")
        _require(isinstance(record, Mapping) and set(record) == {"kind", "origin_kind", "concept_or_citation_id", "authority_sha256"}, "uncertain_lineage")
        _require(record.get("kind") in {"abstract_concept", "authority_citation"} and record.get("origin_kind") == "independent", "uncertain_lineage")
        _require(all(isinstance(record[key], str) and record[key] for key in ("concept_or_citation_id", "authority_sha256")), "uncertain_lineage")
        _require(_metadata_digest(record["authority_sha256"]), "uncertain_lineage")
    except FirewallError as exc:
        return _zero(str(exc))
    del registry
    return _zero("unregistered_authority")


def run_steward_production(config: str | None = None) -> dict[str, Any]:
    """Build the only valid steward receipt from the retained pack, never caller hashes.

    It reuses the storage lane's strict inventory and stream-roundtrip proof.
    The private mode-0600 corpus retains normalized surfaces needed by the
    pinned near-duplicate policy.  No expanded source tree or private content
    is exposed; returned values are public-safe commitments and builder hashes.
    """
    configured = config if config is not None else os.environ.get(STEWARD_CONFIG_ENV)
    if not configured:
        return _zero("private_binding_unbound")
    output_root: Path | None = None
    try:
        payload, root = _read_steward_config(Path(configured))
        pack_dir = Path(payload["content_pack_directory"])
        output_root = Path(payload["steward_output_root"])
        _require(pack_dir != output_root and not output_root.is_relative_to(pack_dir) and not pack_dir.is_relative_to(output_root), "private_path_unsafe")
        _validate_private_tree(pack_dir, root)
        _safe_private_directory(output_root, root)
        output_before = os.lstat(output_root)
        _write_run_state(output_root, "RUNNING")
        manifest_path = pack_dir / "pack-manifest.json"
        manifest_fd, manifest_before = _safe_private_path(manifest_path, root)
        os.close(manifest_fd)
        manifest = storage._read_json(manifest_path, "pack_shape_failure")
        _require(isinstance(manifest, Mapping), "hash_drift")
        storage._require_receipt(manifest, "hash_drift")
        _require(manifest.get("schema_version") == storage.PACK_SCHEMA_VERSION and manifest.get("pack_kind") == "content_compact", "hash_drift")
        inventory = _content_pack_inventory(manifest)
        _require(validate_pack_commitments(manifest, inventory), "denominator_drift")
        _secure_content_pack_proof(pack_dir, manifest, inventory)
        corpus = _build_private_deny_corpus(pack_dir, manifest)
        _require(manifest.get("content_bodies_stored") is True, "graph_incompleteness")
        classes = {value for item in manifest["objects"] for value in item.get("selection_classes", [item.get("selection_class")])}
        _require("compile_expansion" not in classes and not any("label-output" in str(value) for value in classes), "graph_incompleteness")
        manifest_after = os.lstat(manifest_path)
        _require((manifest_before.st_dev, manifest_before.st_ino) == (manifest_after.st_dev, manifest_after.st_ino), "private_path_unsafe")
        _secure_content_pack_proof(pack_dir, manifest, inventory)
        _write_private_json(output_root / "cycle007-deny-component-manifest-v1.json", corpus)
        public_receipt = {"schema_version": "phase3_scope_circularity_public_binding_receipt_v1", "text_free": True, "pack_manifest_receipt_sha256": manifest["receipt_sha256"], "object_set_sha256": EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "packet_count": 204, "row_count": 10159, "physical_sidecar_count": 204, "logical_sidecar_count": 408, "object_count": 419, "private_graph_commitment_sha256": corpus["corpus_sha256"], "builder_clearance": {"p1_sha256": PINS[P1], "p1_amendment_sha256": PINS[P1_AMENDMENT], "p2_sha256": PINS[P2], "near_duplicate_policy_sha256": PINS[NEAR_POLICY], "firewall_sha256": sha256_file(OUTPUT)}}
        public_receipt["receipt_sha256"] = sha256_bytes(canonical_json(public_receipt))
        _require((output_before.st_dev, output_before.st_ino) == (os.lstat(output_root).st_dev, os.lstat(output_root).st_ino), "private_path_unsafe")
        _write_run_state(output_root, "COMPLETE", corpus_sha256=corpus["corpus_sha256"], receipt_sha256=public_receipt["receipt_sha256"])
        return {"ok": True, "code": None, "emitted": 0, "promoted": 0, "activated": 0, "public_receipt": public_receipt}
    except FirewallError as exc:
        if output_root is not None:
            with suppress(FirewallError, OSError):
                _write_run_state(output_root, "TERMINAL_FAILURE", code=str(exc))
        return _zero(str(exc))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, storage.StorageCustodyError):
        if output_root is not None:
            with suppress(FirewallError, OSError):
                _write_run_state(output_root, "TERMINAL_FAILURE", code="private_path_unsafe")
        return _zero("private_path_unsafe")


def evaluate_steward_candidates(candidates: Sequence[Mapping[str, Any]], config: str | None = None) -> dict[str, Any]:
    """Load only a completed, self-bound steward corpus; callers cannot supply one."""
    configured = config if config is not None else os.environ.get(STEWARD_CONFIG_ENV)
    if not configured:
        return _zero("private_binding_unbound")
    try:
        payload, root = _read_steward_config(Path(configured))
        output_root = Path(payload["steward_output_root"])
        state = _load_private_json(output_root / "cycle007-firewall-run-state-v1.json", root)
        _require(state.get("state") == "COMPLETE" and state.get("state_sha256") == sha256_bytes(canonical_json({key: value for key, value in state.items() if key != "state_sha256"})), "private_binding_unbound")
        corpus = _load_private_json(output_root / "cycle007-deny-component-manifest-v1.json", root)
        _require(state.get("corpus_sha256") == corpus.get("corpus_sha256"), "hash_drift")
        return evaluate_candidate_batch(candidates, corpus)
    except (FirewallError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _zero("private_binding_unbound")


def validate_private_runtime_binding(binding: str | None = None, *, private_root: Path | None = None) -> dict[str, Any]:
    """Compatibility wrapper: arbitrary hash bindings can never become valid."""
    del private_root
    return run_steward_production(binding)


def write_output(path: Path = OUTPUT) -> None:
    payload = canonical_json(build_contract())
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--private-runtime", action="store_true")
    args = parser.parse_args()
    if args.private_runtime:
        print(json.dumps(validate_private_runtime_binding(), sort_keys=True))
        return 0
    expected = canonical_json(build_contract())
    if args.check:
        return 0 if OUTPUT.exists() and OUTPUT.read_bytes() == expected else 1
    write_output()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
