#!/usr/bin/env python3
"""Build the text-free, nonadmitting #7430 P4 pilot-construction contract.

The current frozen inputs contain no canonical P2 rule slot and no registered
source-qualified adjudication registry.  This generator therefore emits only
the reproducible blocked construction state.  It never opens a source body,
held-out membership, label, prompt, provider result, or row payload.

Candidate preflight is structural metadata validation only.  It cannot prove
adjudication-registry membership or evidence binding and cannot admit a future
row.  A nonempty successor must bind and verify those facts under a newly
frozen contract version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
CONTRACTS = DATA / "contracts"
EVIDENCE = DATA / "evidence"
ADMISSION = DATA / "admission"

SCHEMA_PATH = CONTRACTS / "phase3_p4_pilot_construction_v1.schema.json"
OUTPUT_PATH = ADMISSION / "phase3_p4_pilot_construction_v1.json"
P2_PATH = EVIDENCE / "phase3_p2_canonical_contracts_v1.json"
FIREWALL_PATH = EVIDENCE / "phase3_scope_circularity_firewall_v1.json"
MODERN_PATH = ADMISSION / "phase3_modern_contact_channels_v1.json"
HISTORICAL_PATH = ADMISSION / "phase3_historical_protection_channels_v1.json"
CAPABILITY_POLICY_PATH = EVIDENCE / "source_capability_policy_v1.json"
SOURCE_RECORD_SCHEMA_PATH = CONTRACTS / "source_record_v1.schema.json"
CORPUS_ADMISSION_VALIDATOR_PATH = ROOT / "scripts/projects/open_model_data/admit_existing_corpus.py"
EXPORT_ADMISSION_GATE_PATH = ROOT / "scripts/projects/open_model_data/model_view_exporter.py"

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
SCHEMA_VERSION = "phase3_p4_pilot_construction_v1"
PINS = {
    P2_PATH: "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    FIREWALL_PATH: "4470448c6d0f665196375cf28255d7c092148700a99934b2d0dd1f43a8a3e24c",
    MODERN_PATH: "573e7d9b7c25f1d09a874e70a6f1ac573d14c228c86f9a67d619e70b07a8160a",
    HISTORICAL_PATH: "837e826ca2a4eb005def3ef438ef7e4e29c58e87414ee80ab482ee3fe8591654",
    CAPABILITY_POLICY_PATH: "3a4a3af2edb1f7d68ebec8717e617ba8465ec26e74c29b408812ef1503aa6c60",
    SOURCE_RECORD_SCHEMA_PATH: "db39258d365b939fb36c1a913b3911d9c185ae7c36e41265e04671be43e36b29",
    CORPUS_ADMISSION_VALIDATOR_PATH: "07b8329cd2c160c15cf3f892d4743ff4e3985156883bd35bd0410f97da9c4278",
    EXPORT_ADMISSION_GATE_PATH: "ad782f925e7468bb9608d0d870b8cd00828f5ee570a5c5e89d68621ce19f12c1",
}
CASE_ROLES = (
    "correct_modern_production",
    "source_backed_correction",
    "minimal_contrast",
    "protected_historical_context",
    "protected_dialect_or_regional_context",
    "abstention",
    "not_applicable_with_evidence",
    "coverage_blocked",
)
FORBIDDEN_CANDIDATE_KEYS = frozenset(
    {
        "content",
        "source_body",
        "source_text",
        "text",
        "gold",
        "label",
        "prompt",
        "provider_output",
        "heldout_membership",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RULE_SLOT_RE = re.compile(r"^p2_rule_slot:[0-9a-f]{64}$")
# Kept equal to the source-record contract's source_family token grammar.
SOURCE_FAMILY_RE = re.compile(r"^[a-z][a-z0-9_.:-]{2,127}$")


class P4PilotError(ValueError):
    """Raised when an input or proposed pilot case is not safely admissible."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise P4PilotError(message)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise P4PilotError(f"cannot read required artifact: {path.name}") from exc


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise P4PilotError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def artifact(path: Path) -> dict[str, str]:
    actual = sha256_file(path)
    require(actual == PINS[path], f"{path.name} hash drift")
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": actual}


def _validate_inputs() -> dict[str, dict[str, Any]]:
    values = {
        "p2": read_json(P2_PATH, "P2 contract"),
        "firewall": read_json(FIREWALL_PATH, "Cycle007 firewall"),
        "modern": read_json(MODERN_PATH, "modern contact channels"),
        "historical": read_json(HISTORICAL_PATH, "historical protection channels"),
        "policy": read_json(CAPABILITY_POLICY_PATH, "source capability policy"),
    }
    for path in PINS:
        artifact(path)
    for name, value, schema_version in (
        ("p2", values["p2"], "phase3_p2_canonical_contracts_v1"),
        ("firewall", values["firewall"], "phase3_scope_circularity_firewall_v1"),
        ("modern", values["modern"], "phase3_modern_contact_channels_v1"),
        ("historical", values["historical"], "phase3_historical_protection_channels_v1"),
    ):
        require(
            value.get("schema_version") == schema_version
            and value.get("text_free") is True
            and value.get("controlling_outcome_sha256") == OUTCOME_SHA256,
            f"{name} contract binding drift",
        )
    p2 = values["p2"]
    require(
        p2.get("status") == "FROZEN_METADATA_ONLY"
        and p2.get("rule_slot_universe", {}).get("symbol") == "R"
        and p2.get("rule_slot_universe", {}).get("slot_count") == 0
        and p2.get("rule_slot_universe", {}).get("slots") == []
        and p2.get("adjudication_contract", {}).get("registry_status") == "FROZEN_NONADMITTING"
        and p2.get("adjudication_contract", {}).get("semantic_case_admission_permitted") is False,
        "P2 nonadmitting rule/adjudication state drift",
    )
    require(
        p2.get("p1_binding", {}).get("source_unit_count") == 57
        and p2.get("p1_binding", {}).get("unknown_rights_blocker_count") == 39
        and p2.get("p1_binding", {}).get("required_cell_count") == 15
        and p2.get("p1_binding", {}).get("composite_required_cell_count") == 16,
        "P2 denominator drift",
    )
    firewall = values["firewall"]
    require(
        firewall.get("denominator")
        == {
            "source_units": 57,
            "unknown_rights_blockers": 39,
            "base_required_cells": 15,
            "composite_required_cells": 16,
            "coverage_blocked_cells": 14,
            "not_applicable_cells": 2,
            "rule_slots_R": 0,
            "canonical_order_required": True,
            "membership_hash_required": True,
        }
        and firewall.get("cycle007", {}).get("state") == "evaluation_only"
        and firewall.get("cycle007", {}).get("private_binding_state") == "BOUND",
        "Cycle007 firewall denominator/state drift",
    )
    require(
        values["modern"].get("status") == "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION"
        and values["modern"].get("safety_counters", {}).get("dataset_rows_emitted") == 0
        and values["historical"].get("zero_counters", {}).get("source_rows_emitted") == 0
        and values["historical"].get("historical_protection", {}).get("modern_correction_eligible") is False,
        "P3 channel state drift",
    )
    wikipedia = next(
        (item for item in values["policy"].get("family_defaults", []) if item.get("source_family") == "wikipedia"),
        None,
    )
    require(
        isinstance(wikipedia, Mapping)
        and wikipedia.get("decisions", {}).get("local_model_learning", {}).get("state") == "excluded",
        "Wikipedia ineligibility policy drift",
    )
    source_schema = read_json(SOURCE_RECORD_SCHEMA_PATH, "source record schema")
    require("source_family" in source_schema.get("required", ()), "source record family binding drift")
    return values


def case_role_requirements() -> list[dict[str, Any]]:
    """Return the complete role map future metadata must satisfy before emission."""
    claim_roles = {
        "correct_modern_production": ["applicability_scope", "correction_authority", "rights_provenance", "source_qualified_human_adjudication"],
        "source_backed_correction": ["applicability_scope", "correction_authority", "rights_provenance", "source_qualified_human_adjudication"],
        "minimal_contrast": ["applicability_scope", "minimal_contrast_authority", "rights_provenance", "source_qualified_human_adjudication"],
        "protected_historical_context": ["protected_historical_identity", "rights_provenance", "source_qualified_human_adjudication"],
        "protected_dialect_or_regional_context": ["protected_dialect_or_regional_identity", "rights_provenance", "source_qualified_human_adjudication"],
        "abstention": ["abstention_or_not_applicable_authority", "rights_provenance", "source_qualified_human_adjudication"],
        "not_applicable_with_evidence": ["abstention_or_not_applicable_authority", "rights_provenance", "source_qualified_human_adjudication"],
        "coverage_blocked": [],
    }
    return [
        {
            "case_role": role,
            "claim_appropriate_evidence_roles": claim_roles[role],
            "emits_dataset_case": role != "coverage_blocked",
            "may_be_modern_correction": role in {"correct_modern_production", "source_backed_correction", "minimal_contrast"},
        }
        for role in CASE_ROLES
    ]


def _candidate_roles(case_role: str) -> list[str]:
    return next(
        item["claim_appropriate_evidence_roles"]
        for item in case_role_requirements()
        if item["case_role"] == case_role
    )


def _require_sha256(value: object, label: str) -> None:
    require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, f"{label} must be a SHA-256")


def _require_canonical_ref_ids(value: object, label: str) -> None:
    require(
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
        and value == sorted(value)
        and len(value) == len(set(value)),
        f"{label} must be a nonempty unique canonical-order list of nonempty strings",
    )


def validate_candidate_admission(candidate: Mapping[str, Any]) -> None:
    """Preflight future text-free candidate metadata, then fail on frozen gates.

    This function intentionally has no writer and cannot establish actual human
    registry membership or evidence binding from candidate-supplied metadata.
    A later, separately frozen P2 rule/adjudication version must bind and verify
    those facts before it creates any nonempty pilot construction artifact.
    """
    required = {
        "case_role",
        "canonical_rule_slot_id",
        "claim_appropriate_evidence_ref_ids",
        "claim_appropriate_evidence_roles",
        "adjudication",
        "rights_provenance",
        "source_identity",
        "firewall_clearance",
        "lineage",
    }
    require(set(candidate) == required, "candidate metadata has missing or unexpected fields")
    require(not (set(candidate) & FORBIDDEN_CANDIDATE_KEYS), "candidate metadata contains forbidden body field")
    role = candidate["case_role"]
    require(role in CASE_ROLES and role != "coverage_blocked", "candidate case role is nonemitting or unknown")
    require(
        isinstance(candidate["canonical_rule_slot_id"], str)
        and RULE_SLOT_RE.fullmatch(candidate["canonical_rule_slot_id"]) is not None,
        "candidate lacks canonical rule slot",
    )
    evidence_ids = candidate["claim_appropriate_evidence_ref_ids"]
    _require_canonical_ref_ids(evidence_ids, "candidate claim-appropriate evidence refs")
    require(
        candidate["claim_appropriate_evidence_roles"] == _candidate_roles(role),
        "candidate evidence roles do not match its case role",
    )
    adjudication = candidate["adjudication"]
    require(
        isinstance(adjudication, Mapping)
        and set(adjudication) == {"actor_kind", "authority_kind", "qualification_status", "record_sha256", "registry_sha256"}
        and adjudication.get("actor_kind") == "human"
        and adjudication.get("authority_kind") == "source_qualified_human_adjudication"
        and adjudication.get("qualification_status") == "registered_source_qualified_human"
        and SHA256_RE.fullmatch(str(adjudication.get("record_sha256"))) is not None
        and SHA256_RE.fullmatch(str(adjudication.get("registry_sha256"))) is not None,
        "candidate lacks registered source-qualified human adjudication",
    )
    rights = candidate["rights_provenance"]
    require(
        isinstance(rights, Mapping)
        and set(rights) == {"rights_status", "provenance_status", "rights_evidence_ref_ids"}
        and rights.get("rights_status") == "evidenced"
        and rights.get("provenance_status") == "complete",
        "candidate rights/provenance is not complete",
    )
    _require_canonical_ref_ids(rights["rights_evidence_ref_ids"], "candidate rights evidence refs")
    source_identity = candidate["source_identity"]
    require(
        isinstance(source_identity, Mapping)
        and set(source_identity) == {"source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"},
        "candidate source identity is incomplete",
    )
    for key, item in source_identity.items():
        _require_sha256(item, f"candidate {key}")
    clearance = candidate["firewall_clearance"]
    require(
        isinstance(clearance, Mapping)
        and set(clearance) == {"status", "clearance_receipt_sha256", "builder_receives_heldout_membership", "cycle007_clear", "heldout_clear", "fingerprint_clear"}
        and clearance.get("status") == "clear"
        and clearance.get("builder_receives_heldout_membership") is False
        and clearance.get("cycle007_clear") is True
        and clearance.get("heldout_clear") is True
        and clearance.get("fingerprint_clear") is True
        and SHA256_RE.fullmatch(str(clearance.get("clearance_receipt_sha256"))) is not None,
        "candidate firewall clearance is incomplete",
    )
    lineage = candidate["lineage"]
    require(
        isinstance(lineage, Mapping)
        and set(lineage) == {"source_family", "cycle007_related", "cycle007_derivative", "cycle007_fingerprint_match", "heldout_related", "provider_authored_gold", "uncertain_lineage", "modern_correction"}
        and isinstance(lineage.get("source_family"), str)
        and SOURCE_FAMILY_RE.fullmatch(lineage["source_family"]) is not None
        and lineage["source_family"] != "wikipedia"
        and all(
            isinstance(lineage[key], bool)
            for key in (
                "cycle007_related",
                "cycle007_derivative",
                "cycle007_fingerprint_match",
                "heldout_related",
                "provider_authored_gold",
                "uncertain_lineage",
                "modern_correction",
            )
        )
        and lineage.get("cycle007_related") is False
        and lineage.get("cycle007_derivative") is False
        and lineage.get("cycle007_fingerprint_match") is False
        and lineage.get("heldout_related") is False
        and lineage.get("provider_authored_gold") is False
        and lineage.get("uncertain_lineage") is False,
        "candidate lineage is denied",
    )
    if role in {"protected_historical_context", "protected_dialect_or_regional_context"}:
        require(lineage.get("modern_correction") is False, "historical/dialect candidate cannot become a modern correction")
    inputs = _validate_inputs()
    require(inputs["p2"]["rule_slot_universe"]["slot_count"] > 0, "current P2 rule universe R=0 blocks nonempty pilot admission")
    require(inputs["p2"]["adjudication_contract"]["semantic_case_admission_permitted"] is True, "current P2 adjudication registry is nonadmitting")


def build_contract() -> dict[str, Any]:
    """Build the exact current zero-row P4 construction receipt."""
    _validate_inputs()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "BLOCKED_PENDING_SOURCE_QUALIFIED_ADJUDICATION",
        "text_free": True,
        "controlling_outcome_sha256": OUTCOME_SHA256,
        "bindings": {name: artifact(path) for name, path in (
            ("p2_canonical_contracts", P2_PATH),
            ("scope_circularity_firewall", FIREWALL_PATH),
            ("modern_contact_channels", MODERN_PATH),
            ("historical_protection_channels", HISTORICAL_PATH),
            ("source_capability_policy", CAPABILITY_POLICY_PATH),
            ("source_record_contract", SOURCE_RECORD_SCHEMA_PATH),
            ("corpus_admission_validator", CORPUS_ADMISSION_VALIDATOR_PATH),
            ("model_view_export_admission_gate", EXPORT_ADMISSION_GATE_PATH),
        )},
        "denominator": {
            "source_units": 57,
            "unknown_rights_blockers": 39,
            "base_required_cells": 15,
            "composite_required_cells": 16,
            "coverage_blocked_cells": 14,
            "not_applicable_cells": 2,
            "rule_slots_R": 0,
        },
        "case_role_requirements": case_role_requirements(),
        "candidate_metadata_contract": {
            "canonical_rule_slot_required": True,
            "claim_appropriate_evidence_required": True,
            "registered_source_qualified_human_adjudication_required": True,
            "rights_provenance_required": True,
            "source_identity_required": True,
            "firewall_clearance_required": True,
            "candidate_preflight_only": True,
            "future_nonempty_version_must_verify_adjudication_registry_membership": True,
            "future_nonempty_version_must_verify_adjudication_evidence_binding": True,
            "forbidden_body_fields": sorted(FORBIDDEN_CANDIDATE_KEYS),
        },
        "firewall_constraints": {
            "builder_receives_heldout_membership": False,
            "cycle007_lineage_denied": True,
            "cycle007_derivatives_denied": True,
            "cycle007_fingerprints_denied": True,
            "heldout_lineage_denied": True,
            "provider_authored_gold_denied": True,
            "wikipedia_denied": True,
            "uncertain_lineage_denied": True,
            "atomic_split_requirements": ["source", "document", "work", "edition", "exact_duplicate_component", "near_duplicate_connected_component"],
        },
        "current_construction": {
            "dataset_case_rows": [],
            "dataset_case_row_count": 0,
            "construction_state": "no_admitted_cases",
            "candidate_admission_implemented": True,
        },
        "residuals": [
            "canonical_rule_slots_R_zero",
            "source_qualified_adjudication_registry_frozen_nonadmitting",
            "unknown_rights_blockers_39",
            "coverage_blocked_cells_14",
            "modern_contact_channels_blocked",
            "historical_and_dialect_protection_source_gaps_open",
        ],
        "safety_counters": {
            "dataset_rows_emitted": 0,
            "case_rows_emitted": 0,
            "correction_targets_emitted": 0,
            "gold_created": 0,
            "labels_created": 0,
            "provider_requests": 0,
            "training_rows_emitted": 0,
        },
        "claims": {
            "pilot_validated_claimed": False,
            "dataset_ready_claimed": False,
            "training_validated_claimed": False,
            "nonempty_pilot_constructed": False,
            "historical_or_dialect_modernized": False,
        },
        "generator": {
            "path": "scripts/projects/open_model_data/build_phase3_p4_pilot.py",
            "implementation_sha256": sha256_file(Path(__file__).resolve()),
            "schema_sha256": sha256_file(SCHEMA_PATH),
        },
    }
    body["receipt_sha256"] = sha256_bytes(canonical_bytes(body))
    return body


def validate_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    schema = read_json(SCHEMA_PATH, "P4 pilot schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    require(not errors, f"schema violation: {errors[0].message if errors else ''}")
    expected = build_contract()
    require(dict(value) == expected, "P4 pilot contract drift")
    require(value.get("receipt_sha256") == sha256_bytes(canonical_bytes({key: item for key, item in value.items() if key != "receipt_sha256"})), "receipt hash drift")
    return expected


def write_output(path: Path = OUTPUT_PATH) -> dict[str, Any]:
    value = build_contract()
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, path)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the checked-in deterministic P4 contract")
    args = parser.parse_args(argv)
    expected = build_contract()
    if args.check:
        return 0 if OUTPUT_PATH.exists() and OUTPUT_PATH.read_bytes() == canonical_bytes(expected) else 1
    write_output()
    print(json.dumps({"case_rows": 0, "ok": True, "status": expected["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
