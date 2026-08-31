#!/usr/bin/env python3
"""Freeze #7427's metadata-only held-out and Cycle007 lineage firewall.

This module deliberately has no extractor, labeler, or derivation callback.
It permits builders to receive only the public freeze hashes.  The optional
steward runtime reads an opaque private binding solely to prove safe custody;
it never opens source/evidence bodies or emits membership, labels, prompts, or
private locators.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

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
)
PRIVATE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


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
        "split_firewall": {"atomicity": ["source", "document", "work", "edition", "exact_duplicate_component", "near_duplicate_connected_component"], "heldout_records_frozen": 16, "builder_clearance": "positive_only_metadata_hashes", "builder_receives_membership": False, "derivation_callback_permitted": False, "private_steward_role": "evaluation_steward_only", "builder_steward_collision_forbidden": True},
        "cycle007": {"state": "evaluation_only", "deny_namespaces": list(DENY_NAMESPACES), "public_packet_count": 204, "public_row_count": 10159, "physical_sidecar_count": 204, "logical_sidecar_count": 408, "object_count": 419, "private_binding_state": "UNBOUND", "fresh_private_materialization_claimed": False, "concept_reuse": "independent_origin_only_without_cycle007_identity_or_membership", "authority_reuse": "citation_only_without_heldout_span_locator_annotation_or_membership"},
        "fail_closed": {"terminal_codes": list(FAIL_CODES), "batch_failure_outputs": {"emitted": 0, "promoted": 0, "activated": 0}, "partial_denominator_permitted": False, "provider_calls": 0, "labels_created": 0, "gold_created": 0, "training_performed": False},
        "private_runtime": {"environment_binding": "PHASE3_EVAL_PRIVATE_BINDING", "file_mode": "0600", "directory_mode": "0700", "rejects": ["symlink", "hardlink", "traversal", "owner_mismatch", "path_overlap", "inode_device_change", "ancestor_replacement", "post_pin_toctou"], "public_output_text_free": True},
        "generator": artifact(Path(__file__)),
    }


def validate_contract_integrity(contract: Mapping[str, Any]) -> bool:
    try:
        return canonical_json(dict(contract)) == canonical_json(build_contract())
    except (FirewallError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def validate_builder_clearance(clearance: Mapping[str, Any], contract: Mapping[str, Any] | None = None) -> bool:
    """Positive-only builder clearance. No membership or derived data is accepted."""
    if contract is not None and not validate_contract_integrity(contract):
        return False
    allowed = {"p1_sha256", "p1_amendment_sha256", "p2_sha256", "near_duplicate_policy_sha256", "firewall_sha256"}
    if set(clearance) != allowed or not all(isinstance(value, str) and len(value) == 64 for value in clearance.values()):
        return False
    expected = {"p1_sha256": PINS[P1], "p1_amendment_sha256": PINS[P1_AMENDMENT], "p2_sha256": PINS[P2], "near_duplicate_policy_sha256": PINS[NEAR_POLICY], "firewall_sha256": sha256_file(OUTPUT) if OUTPUT.exists() else ""}
    return clearance == expected


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
    return {"ok": True, "code": None, "emitted": 0, "promoted": 0, "activated": 0}


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


def validate_private_runtime_binding(binding: str | None = None, *, private_root: Path | None = None) -> dict[str, Any]:
    """Validate an opaque steward binding without disclosing or reading data bodies."""
    configured = binding if binding is not None else os.environ.get("PHASE3_EVAL_PRIVATE_BINDING")
    if not configured:
        return {"ok": False, "code": "private_binding_unbound", "emitted": 0, "promoted": 0, "activated": 0}
    root = private_root or ROOT / "batch_state/open-model-data/phase3-evaluation-steward"
    try:
        path = Path(configured)
        fd, before = _safe_private_path(path, root)
        try:
            # The binding is opaque metadata. One bounded read rejects content-bearing shapes.
            value = json.loads(os.read(fd, 65537).decode("utf-8"))
            _require(os.read(fd, 1) == b"", "private_path_unsafe")
        finally:
            os.close(fd)
        after = os.lstat(path)
        _require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), "private_path_unsafe")
        _require(isinstance(value, dict) and set(value) == {"binding_version", "membership_sha256", "component_graph_sha256", "steward_role"}, "private_path_unsafe")
        _require(value.get("binding_version") == "phase3_evaluation_private_binding_v1" and value.get("steward_role") == "evaluation_steward", "custody_role_collision")
        _require(all(isinstance(value[key], str) and len(value[key]) == 64 for key in ("membership_sha256", "component_graph_sha256")), "private_path_unsafe")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, FirewallError):
        return {"ok": False, "code": "private_path_unsafe", "emitted": 0, "promoted": 0, "activated": 0}
    return {"ok": True, "code": None, "emitted": 0, "promoted": 0, "activated": 0}


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
