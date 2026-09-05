"""V4 A3 held-out source-family seal is text-free and exposes no membership to builders."""

from __future__ import annotations

import copy
import hashlib
import json
import re
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

NEAR_DUP_POLICY = ROOT / "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"

# Exact (kind, value) pairs the denial must contain -- checked as pairs, not
# just as a value set, so a kind/value mismatch (or a masked duplicate) fails.
CYCLE007_DENIED_FINGERPRINTS = {
    ("object_set_sha256", "af94e8d12c075e1e5e1816de076327dd68a3fd5d5f06ec77debcbbd590bcc9ec"),
    ("pack_manifest_receipt_sha256", "2a883cb3e9a3b2ee673e397c8f5ba511f886f725bea980b2c982ca17f92a5e7d"),
    ("ordered_row_identity_commitment_sha256", "d873d7493c6cd276a9604954c9c7aa07e760ca4f47a276658fd28956d6fa940b"),
    ("candidate_clearance_commitment_sha256", "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"),
    ("private_graph_commitment_sha256", "de77b0e2444365e3c9cdec3441128f87b96ca8a15f897e4c769f9b840ccac398"),
    ("near_duplicate_policy_fingerprint_sha256", "19518efb07dd8ef4173b32487da7427f3c1eb0b8f8dd5d21b046cfc4dc5d560e"),
}

ASSIGNMENT_ALGORITHM_DESCRIPTOR = {
    "algorithm_id": "v4-a3-hmac-sha256-family-rank-split-v1",
    "algorithm_version": "v1",
    "identity_dimensions": ["family_id"],
    "content_blind": True,
    "formula": (
        "rank_key(family_id) = int(hmac.new(key=private_salt, "
        "msg=family_id.encode('utf-8'), digestmod=hashlib.sha256).hexdigest(), 16); "
        "order family_ids ascending by (rank_key(family_id), family_id); "
        "heldout_target_count = max(1, round(family_count * heldout_fraction)); "
        "the first heldout_target_count family_ids in that order are assigned to the "
        "heldout pool; every remaining family_id is assigned to the builder_eligible pool"
    ),
    "heldout_fraction": 0.1,
    "rounding_rule": "python_round_half_to_even",
    "minimum_heldout_count": 1,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

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
    assert receipt["status"] == "A3_HELDOUT_SOURCE_FAMILY_SEAL_FIREWALL_SEALED_MEMBERSHIP_ASSIGNED_PRIVATE"

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a3_heldout_seal_bindings_match_exact_inputs() -> None:
    receipt = _receipt()

    for binding in receipt["bindings"].values():
        from learn_ukrainian_v4_runtime import resources
        logical = binding["path"]
        if logical.startswith("scripts/"):
            logical = "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
        assert hashlib.sha256(resources.read_bytes(logical)).hexdigest() == binding["sha256"]

    assert receipt["bindings"]["cycle007_scope_circularity_evidence"]["v3_only"] is True
    assert receipt["bindings"]["cycle007_scope_circularity_evidence"]["used_for_denial_only"] is True


def test_a3_heldout_seal_schema_forbids_sensitive_unknown_fields_on_bindings() -> None:
    """A binding object must not be able to smuggle in the private salt or a
    membership locator -- neither field is ever legitimate on a public
    artifact_binding entry, and the schema must reject them outright rather
    than silently accepting and ignoring them."""
    receipt = _receipt()

    for key in receipt["bindings"]:
        with_salt = copy.deepcopy(receipt)
        with_salt["bindings"][key]["salt_hex"] = "00" * 32
        assert _errors(with_salt), f"schema accepted salt_hex on bindings.{key}"

        with_locator = copy.deepcopy(receipt)
        with_locator["bindings"][key]["heldout_membership_locator"] = "batch_state/whatever"
        assert _errors(with_locator), f"schema accepted heldout_membership_locator on bindings.{key}"


def test_a3_heldout_seal_receipt_is_payload_and_membership_free() -> None:
    receipt = _receipt()

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    # The V3 SHA appears exactly once: as the explicitly denied cycle007 source binding.
    assert receipt["cycle007_denial"]["source_cycle_controlling_outcome_sha256"] == V3_SHA256
    assert receipt["cycle007_denial"]["denied"] is True

    seal = receipt["heldout_partition_seal"]
    assert seal["heldout_membership_included"] is False
    assert seal["heldout_membership_assigned_privately"] is True
    assert seal["heldout_count"] > 0
    assert seal["builder_eligible_count"] > 0
    assert seal["heldout_count"] + seal["builder_eligible_count"] == receipt["source_family_registry"]["family_count"]
    assert seal["sealed_before_any_builder_packet"] is True

    algorithm = seal["assignment_algorithm"]
    assert algorithm["identity_dimensions"] == ["family_id"]
    assert algorithm["content_blind"] is True
    # The descriptor hash is recomputed from a formula frozen in this test file
    # (independent of the receipt), so a different private implementation that
    # silently changed the formula cannot keep this hash and still pass.
    assert algorithm["algorithm_descriptor_sha256"] == hashlib.sha256(
        _canonical_json(ASSIGNMENT_ALGORITHM_DESCRIPTOR).encode("utf-8")
    ).hexdigest()
    assert re.fullmatch(r"[a-f0-9]{64}", algorithm["salt_commitment_sha256"])
    assert re.fullmatch(r"[a-f0-9]{64}", algorithm["assignment_commitment_sha256"])
    # The private salt itself, and the family->pool membership, never appear here.
    assert not _all_keys(receipt) & {"salt", "private_salt", "heldout_family_pool"}

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

    # The A3-owned held-out membership assignment is complete (see the
    # heldout-assignment test below), so a3_residuals may legitimately be
    # empty; it must not carry a stale "still pending" placeholder.
    assert isinstance(receipt["a3_residuals"], list)
    assert not any(
        entry.get("reason_code") == "membership_not_yet_assigned" for entry in receipt["a3_residuals"]
    )
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

    pairs = [(entry["fingerprint_kind"], entry["value"]) for entry in denial["denied_fingerprints"]]
    # Exact unique (kind, value) pairs -- catches both a masked duplicate value
    # (same value under two kinds) and a kind/value mismatch that a plain
    # value-set comparison would hide.
    assert len(pairs) == len(denial["denied_fingerprints"])
    assert len(pairs) == len(set(pairs))
    assert set(pairs) == CYCLE007_DENIED_FINGERPRINTS
    values = [entry["value"] for entry in denial["denied_fingerprints"]]
    assert len(values) == len(set(values)), "denied fingerprint values must be pairwise distinct"
    for entry in denial["denied_fingerprints"]:
        assert entry["denied"] is True

    # The near-duplicate-policy fingerprint is grounded against the actual
    # bound policy file's own commitment field, not just a hardcoded literal.
    policy_fingerprint = _load(NEAR_DUP_POLICY)["policy_fingerprint_sha256"]
    assert ("near_duplicate_policy_fingerprint_sha256", policy_fingerprint) in set(pairs)

    assert receipt["execution_counters"]["cycle007_material_reused"] == 0
    assert receipt["safety_assertions"]["cycle007_material_reused"] is False
