"""V4 A3 held-out source-family seal is text-free and exposes no membership to builders."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.schema.json"
A2_RECEIPT = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"
V3_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"

CYCLE007_FINGERPRINTS = {
    "de77b0e2444365e3c9cdec3441128f87b96ca8a15f897e4c769f9b840ccac398",
    "af94e8d12c075e1e5e1816de076327dd68a3fd5d5f06ec77debcbbd590bcc9ec",
    "2a883cb3e9a3b2ee673e397c8f5ba511f886f725bea980b2c982ca17f92a5e7d",
    "d873d7493c6cd276a9604954c9c7aa07e760ca4f47a276658fd28956d6fa940b",
    "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
}

FORBIDDEN_KEYS = {
    "content",
    "text",
    "source_body",
    "source_text",
    "prompt",
    "label",
    "gold",
    "heldout_membership",
    "heldout_locator",
    "heldout_fingerprint",
    "heldout_neighbour",
    "heldout_near_neighbour",
    "held_out_membership",
}

BUILDER_ROLE_IDS = {
    "A0_scope_lead",
    "A1_custody",
    "A2_source_inventory_admission",
    "A4_deterministic_extraction",
    "A5_evidence_enrichment",
    "A6_safe_arena",
    "A7_original_row_factory",
    "A8_admission_assembly",
    "A9_evaluation_package",
    "A10_pilot_review",
    "A11_training_ready_release",
    "A12_later_gold_overlay",
    "A13_cleanup_recovery",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _receipt() -> dict[str, Any]:
    return _load(RECEIPT)


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda error: list(error.path))


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_a3_heldout_seal_schema_and_v4_control_binding() -> None:
    receipt = _receipt()

    assert not _errors(receipt)
    assert receipt["controlling_outcome_sha256"] == V4_SHA256
    assert receipt["text_free"] is True
    assert receipt["status"] == "A3_HELDOUT_SOURCE_FAMILY_SEAL_FIREWALL_SEALED_MEMBERSHIP_PENDING"

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a3_heldout_seal_bindings_match_exact_inputs() -> None:
    receipt = _receipt()

    for binding in receipt["bindings"].values():
        bound_path = ROOT / binding["path"]
        assert bound_path.is_file()
        assert hashlib.sha256(bound_path.read_bytes()).hexdigest() == binding["sha256"]

    assert receipt["bindings"]["cycle007_scope_circularity_evidence"]["v3_only"] is True
    assert receipt["bindings"]["cycle007_scope_circularity_evidence"]["used_for_denial_only"] is True


def test_a3_heldout_seal_receipt_is_payload_and_membership_free() -> None:
    receipt = _receipt()

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    # The V3 SHA appears exactly once: as the explicitly denied cycle007 source binding.
    assert receipt["cycle007_denial"]["source_cycle_controlling_outcome_sha256"] == V3_SHA256
    assert receipt["cycle007_denial"]["denied"] is True

    seal = receipt["heldout_partition_seal"]
    assert seal["heldout_membership_included"] is False
    assert seal["families_assigned_heldout"] == 0
    assert seal["families_assigned_builder_eligible"] == 0
    assert seal["families_assignment_pending"] == receipt["source_family_registry"]["family_count"]
    assert seal["sealed_before_any_builder_packet"] is True

    assert receipt["temporal_firewall"]["builder_packet_issued"] is False
    assert receipt["temporal_firewall"]["exposure_allowed"] is False
    assert receipt["safety_assertions"]["heldout_membership_exposed_to_builder"] is False
    assert receipt["execution_counters"]["dataset_rows_emitted"] == 0
    assert receipt["execution_counters"]["builder_packets_issued"] == 0
    assert receipt["safety_assertions"]["prebuilder_state_claimed"] is False
    assert receipt["safety_assertions"]["later_release_state_claimed"] is False
    assert receipt["safety_assertions"]["epic_done_claimed"] is False


def test_a3_heldout_membership_not_present_in_any_builder_facing_role() -> None:
    receipt = _receipt()
    roles = {entry["role_id"]: entry for entry in receipt["access_firewall"]}

    assert set(roles) == BUILDER_ROLE_IDS | {"A3_heldout"}

    for role_id, entry in roles.items():
        if role_id == "A3_heldout":
            continue
        assert role_id in BUILDER_ROLE_IDS
        assert entry["heldout_family_pool_visible"] is False
        assert entry["heldout_membership_locator_visible"] is False
        assert entry["heldout_fingerprint_visible"] is False
        assert entry["heldout_near_neighbour_visible"] is False
        assert set(entry["forbidden_fields"]) == {
            "heldout_family_pool",
            "heldout_membership_locator",
            "heldout_fingerprint",
            "heldout_near_neighbour",
        }

    heldout_role = roles["A3_heldout"]
    assert heldout_role["heldout_family_pool_visible"] is True
    assert heldout_role["forbidden_fields"] == []


def test_a3_heldout_seal_groups_a2_source_units_by_identity_not_arrival_order() -> None:
    receipt = _receipt()
    a2_receipt = _load(A2_RECEIPT)

    a2_unit_ids = {entry["source_unit_id"] for entry in a2_receipt["source_operation_ledger"]}
    families = receipt["source_family_registry"]["families"]
    family_unit_ids: set[str] = set()

    assert receipt["source_family_registry"]["grouping_basis"] == (
        "source_identity_not_prestige_or_provider_arrival_order"
    )
    assert len(families) == receipt["source_family_registry"]["family_count"]

    for family in families:
        assert len(family["member_source_unit_ids"]) == len(set(family["member_source_unit_ids"]))
        family_unit_ids |= set(family["member_source_unit_ids"])

    # Every A2 candidate source unit is grouped into exactly one family; nothing invented or dropped.
    assert family_unit_ids == a2_unit_ids
    all_members = [uid for family in families for uid in family["member_source_unit_ids"]]
    assert len(all_members) == len(set(all_members))


def test_a3_heldout_seal_carries_forward_every_a2_residual() -> None:
    receipt = _receipt()
    a2_receipt = _load(A2_RECEIPT)

    a2_residual_ids = {entry["residual_id"] for entry in a2_receipt["residuals"]}
    carried_ids = {entry["residual_id"] for entry in receipt["a2_residuals_carried_forward"]}

    assert carried_ids == a2_residual_ids
    for entry in receipt["a2_residuals_carried_forward"]:
        assert entry["origin_stage"] == "A2"
        assert entry["status"] == "unresolved_carried_to_a3"

    assert receipt["a3_residuals"]
    for entry in receipt["a3_residuals"]:
        assert entry["stage"] == "A3"
        assert entry["owner_role"]
        assert entry["next_action"]
        assert entry["retryability"] in {"retryable", "not_retryable"}


def test_a3_heldout_seal_denies_cycle007_fingerprints() -> None:
    receipt = _receipt()
    denial = receipt["cycle007_denial"]

    assert denial["denied"] is True
    assert denial["reused_in_v4"] is False
    assert denial["adoption_forbidden"] is True
    assert denial["source_cycle_controlling_outcome_sha256"] == V3_SHA256
    assert denial["source_cycle_controlling_outcome_sha256"] != receipt["controlling_outcome_sha256"]

    denied_values = {entry["value"] for entry in denial["denied_fingerprints"]}
    assert denied_values == CYCLE007_FINGERPRINTS
    for entry in denial["denied_fingerprints"]:
        assert entry["denied"] is True

    assert receipt["execution_counters"]["cycle007_material_reused"] == 0
    assert receipt["safety_assertions"]["cycle007_material_reused"] is False
