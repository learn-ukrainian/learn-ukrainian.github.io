"""Adversarial checks for the metadata-only Phase 3 V3-C custody contract."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_v3c_heldout_extension_solo_custody as v3c


def _artifact() -> dict[str, Any]:
    return json.loads(v3c.ARTIFACT_PATH.read_text(encoding="utf-8"))


def _schema() -> dict[str, Any]:
    return json.loads(v3c.SCHEMA_PATH.read_text(encoding="utf-8"))


def _receipt(
    *,
    sequence: int,
    cycle_id: str,
    event_type: str,
    cycle_status: str,
    previous_receipt_sha256: str | None,
    freeze_commitment_sha256: str,
    evaluation_version_sha256: str,
    mutation: bool = False,
    new_cycle_required: bool = False,
    reason_code: str = "test_receipt",
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": v3c.RECEIPT_SCHEMA_VERSION,
        "receipt_id": "0" * 64,
        "sequence": sequence,
        "cycle_id": cycle_id,
        "event_type": event_type,
        "cycle_status": cycle_status,
        "operator_role_id": v3c.SOLO_OPERATOR_ROLE,
        "construction_mutation_after_exposure": mutation,
        "new_cycle_required": new_cycle_required,
        "freeze_field_count": len(v3c.FIREWALL_FIELDS),
        "freeze_commitment_sha256": freeze_commitment_sha256,
        "evaluation_version_sha256": evaluation_version_sha256,
        "requirement_ledger_sha256": _artifact()["requirement_ledger"]["ledger_sha256"],
        "reason_code": reason_code,
        "previous_receipt_sha256": previous_receipt_sha256,
        "receipt_sha256": "0" * 64,
    }
    value["receipt_id"] = v3c.sha256_value(v3c._receipt_identity(value))
    value["receipt_sha256"] = v3c.receipt_sha(value)
    return value


def test_tracked_contract_is_strict_canonical_and_text_free() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    artifact = _artifact()
    v3c.validate(artifact, schema)
    assert v3c.SCHEMA_PATH.read_bytes() == v3c.canonical_bytes(schema)
    assert v3c.ARTIFACT_PATH.read_bytes() == v3c.canonical_bytes(artifact)
    assert artifact["text_free"] is True
    assert artifact["metadata_only"] is True
    assert artifact["status"] == "FROZEN_METADATA_ONLY_NO_EXPOSURE"


def test_frozen_outcome_and_v3a_denominator_are_exact() -> None:
    artifact = _artifact()
    assert artifact["outcome_boundary"] == {
        "parent_outcome_sha256": v3c.PARENT_OUTCOME_SHA256,
        "reviewed_v3_consensus_sha256": v3c.V3_CONSENSUS_SHA256,
        "v3a_artifact_sha256": v3c.V3A_ARTIFACT_SHA256,
        "heldout_membership_present": False,
        "heldout_content_present": False,
        "provider_calls": 0,
        "labeling_count": 0,
        "evaluation_runs": 0,
        "training_runs": 0,
    }
    assert artifact["denominator"] == {
        "source_units": 57,
        "visible_cells": 19,
        "active_coverage_target_cells": 16,
        "active_coverage_blocked_cells": 16,
        "not_applicable_cells": 2,
        "lineage_only_parent_cells": 1,
        "rights_operation_cells": 399,
        "rule_slots_R": 0,
    }


def test_every_visible_stratum_is_present_once_with_nonzero_or_explicit_blocker() -> None:
    artifact = _artifact()
    strata = artifact["strata"]
    assert len(strata) == 19
    assert [row["denominator_ordinal"] for row in strata] == list(range(1, 20))
    assert len({row["stratum_id"] for row in strata}) == 19
    classes = {name: sum(row["denominator_class"] == name for row in strata) for name in (
        "active_blocked",
        "not_applicable",
        "lineage_only",
    )}
    assert classes == {"active_blocked": 16, "not_applicable": 2, "lineage_only": 1}
    for row in strata:
        requirement = row["heldout_requirement"]
        assert requirement["exact"] is True
        assert requirement["blocker_is_denominator_visible"] is True
        if row["denominator_class"] == "active_blocked":
            assert requirement["required_item_count"] == 1
        else:
            assert requirement["required_item_count"] is None
        assert requirement["blocker_code"]
    ledger = artifact["requirement_ledger"]
    assert ledger["rows"] == strata
    assert ledger["exact_row_count"] == ledger["visible_stratum_count"] == 19
    assert ledger["no_silent_zero"] is True


def test_identity_groups_and_assignment_are_frozen_without_membership() -> None:
    artifact = _artifact()
    freeze = artifact["identity_group_freeze"]
    assert tuple(item["dimension_id"] for item in freeze["dimensions"]) == v3c.IDENTITY_DIMENSIONS
    assert freeze["all_identity_dimensions_frozen"] is True
    assert freeze["source_admission_assigns_hidden_membership"] is False
    assert freeze["construction_receives_hidden_membership"] is False
    assert all(item["actual_membership_present"] is False for item in freeze["dimensions"])
    assert all(item["public_membership_present"] is False for item in freeze["dimensions"])
    split = artifact["split_assignment"]
    assert split["identity_dimensions"] == list(v3c.IDENTITY_DIMENSIONS)
    assert split["assignment_unit"] == "duplicate_group_identity"
    assert split["grouping_before_split"] is True
    assert split["same_group_never_split"] is True
    assert split["assignment_is_deterministic"] is True
    assert split["assignment_is_content_blind"] is True
    assert split["membership_present"] is False
    assert split["membership_commitment_present"] is False
    assert split["construction_access"] == "forbidden"
    assert split["source_admission_assigns_hidden_membership"] is False


def test_construction_roles_are_blind_to_all_heldout_surfaces() -> None:
    visibility = _artifact()["construction_visibility"]
    assert visibility["all_construction_roles_blind"] is True
    assert visibility["source_admission_may_read_rights_only"] is True
    assert visibility["heldout_membership_never_enters_construction_prompt"] is True
    assert {row["role_id"] for row in visibility["construction_roles"]} == set(v3c.CONSTRUCTION_ROLE_IDS)
    fields = (
        "heldout_identity_visible",
        "heldout_content_visible",
        "heldout_labels_visible",
        "heldout_locators_visible",
        "heldout_fingerprints_visible",
        "heldout_derivatives_visible",
        "heldout_near_neighbours_visible",
    )
    for role in visibility["construction_roles"]:
        assert all(role[field] is False for field in fields)
        assert set(role["forbidden_fields"]) == set(v3c.VISIBILITY_FORBIDDEN_FIELDS)


def test_solo_temporal_firewall_and_disclosure_are_truthful() -> None:
    artifact = _artifact()
    firewall = artifact["temporal_firewall"]
    assert firewall["pre_exposure_construction_freeze_required"] is True
    assert firewall["freeze_fields"] == list(v3c.FIREWALL_FIELDS)
    assert firewall["freeze_field_commitments"] == {field: None for field in v3c.FIREWALL_FIELDS}
    assert firewall["exposure_before_freeze_forbidden"] is True
    assert firewall["construction_mutation_after_exposure"] is False
    assert firewall["post_exposure_mutation_action"] == "invalidate_evaluation_version_and_require_new_sealed_cycle"
    assert firewall["current_cycle_state"] == "UNSEALED_NO_EXPOSURE"
    assert firewall["exposure_allowed"] is False
    custody = artifact["solo_operator_custody"]
    assert custody["operator_count"] == 1
    assert custody["credential_claimed"] is False
    assert custody["institutional_independence_claimed"] is False
    assert custody["independent_adjudicator_claimed"] is False
    assert custody["private_identity_present"] is False
    assert custody["ambiguity_action"] == "abstain_non_gold"


def test_thresholds_and_residuals_cover_the_same_denominator() -> None:
    artifact = _artifact()
    strata_ids = [row["stratum_id"] for row in artifact["strata"]]
    thresholds = artifact["evaluation_policy"]["per_stratum_thresholds"]
    residuals = artifact["residual_query"]["rows"]
    assert [row["stratum_id"] for row in thresholds] == strata_ids
    assert [row["stratum_id"] for row in residuals] == strata_ids
    assert artifact["evaluation_policy"]["threshold_row_count"] == 19
    assert artifact["residual_query"]["row_count"] == 19
    assert all(row["minimum_direct_human_review_fraction"] == 1.0 for row in thresholds)
    assert all(row["abstention_is_not_gold"] for row in thresholds)
    assert all(row["blocking"] is True for row in residuals)


def test_execution_stays_off_and_receipt_ledger_is_empty() -> None:
    artifact = _artifact()
    gates = artifact["execution_gates"]
    assert gates == {
        "provider_calls_authorized": False,
        "provider_call_count": 0,
        "labeling_authorized": False,
        "labeling_count": 0,
        "evaluation_authorized": False,
        "evaluation_runs": 0,
        "training_authorized": False,
        "training_runs": 0,
        "heldout_rows_created": 0,
    }
    assert artifact["custody_receipts"]["rows"] == []
    assert artifact["custody_receipts"]["row_count"] == 0
    assert artifact["custody_receipts"]["append_only"] is True
    assert artifact["custody_receipts"]["update_or_delete_permitted"] is False


def test_custody_receipt_chain_requires_seal_exposure_invalidation_and_new_cycle() -> None:
    artifact = _artifact()
    freeze = "1" * 64
    version = "2" * 64
    seal = _receipt(
        sequence=0,
        cycle_id="cycle-test-001",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=None,
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
    )
    exposure = _receipt(
        sequence=1,
        cycle_id="cycle-test-001",
        event_type="exposure",
        cycle_status="EXPOSED",
        previous_receipt_sha256=seal["receipt_sha256"],
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
    )
    invalidation = _receipt(
        sequence=2,
        cycle_id="cycle-test-001",
        event_type="invalidation",
        cycle_status="INVALIDATED_RESEAL_REQUIRED",
        previous_receipt_sha256=exposure["receipt_sha256"],
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
        mutation=True,
        new_cycle_required=True,
        reason_code="post_exposure_construction_mutation",
    )
    reseal = _receipt(
        sequence=3,
        cycle_id="cycle-test-002",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=invalidation["receipt_sha256"],
        freeze_commitment_sha256="3" * 64,
        evaluation_version_sha256="4" * 64,
    )
    exposure_two = _receipt(
        sequence=4,
        cycle_id="cycle-test-002",
        event_type="exposure",
        cycle_status="EXPOSED",
        previous_receipt_sha256=reseal["receipt_sha256"],
        freeze_commitment_sha256="3" * 64,
        evaluation_version_sha256="4" * 64,
    )
    v3c.validate_custody_receipts([seal, exposure, invalidation, reseal, exposure_two], artifact)


def test_custody_receipt_rejects_exposure_without_seal_and_uninvalidated_mutation() -> None:
    artifact = _artifact()
    exposure = _receipt(
        sequence=0,
        cycle_id="cycle-test-001",
        event_type="exposure",
        cycle_status="EXPOSED",
        previous_receipt_sha256=None,
        freeze_commitment_sha256="1" * 64,
        evaluation_version_sha256="2" * 64,
    )
    with pytest.raises(v3c.V3CError, match="must begin with cycle seal"):
        v3c.validate_custody_receipts([exposure], artifact)

    seal = _receipt(
        sequence=0,
        cycle_id="cycle-test-001",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=None,
        freeze_commitment_sha256="1" * 64,
        evaluation_version_sha256="2" * 64,
    )
    bad_invalidation = _receipt(
        sequence=1,
        cycle_id="cycle-test-001",
        event_type="invalidation",
        cycle_status="INVALIDATED_RESEAL_REQUIRED",
        previous_receipt_sha256=seal["receipt_sha256"],
        freeze_commitment_sha256="1" * 64,
        evaluation_version_sha256="2" * 64,
        mutation=False,
        new_cycle_required=False,
    )
    with pytest.raises(v3c.V3CError, match="without prior exposure"):
        v3c.validate_custody_receipts([seal, bad_invalidation], artifact)


def test_invalidation_requires_a_fresh_cycle_id() -> None:
    artifact = _artifact()
    freeze = "1" * 64
    version = "2" * 64
    seal = _receipt(
        sequence=0,
        cycle_id="cycle-test-001",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=None,
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
    )
    exposure = _receipt(
        sequence=1,
        cycle_id="cycle-test-001",
        event_type="exposure",
        cycle_status="EXPOSED",
        previous_receipt_sha256=seal["receipt_sha256"],
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
    )
    invalidation = _receipt(
        sequence=2,
        cycle_id="cycle-test-001",
        event_type="invalidation",
        cycle_status="INVALIDATED_RESEAL_REQUIRED",
        previous_receipt_sha256=exposure["receipt_sha256"],
        freeze_commitment_sha256=freeze,
        evaluation_version_sha256=version,
        mutation=True,
        new_cycle_required=True,
    )
    reused = _receipt(
        sequence=3,
        cycle_id="cycle-test-001",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=invalidation["receipt_sha256"],
        freeze_commitment_sha256="3" * 64,
        evaluation_version_sha256="4" * 64,
    )
    with pytest.raises(v3c.V3CError, match="new cycle id required"):
        v3c.validate_custody_receipts([seal, exposure, invalidation, reused], artifact)


def test_custody_receipt_hash_chain_and_replay_are_fail_closed() -> None:
    artifact = _artifact()
    seal = _receipt(
        sequence=0,
        cycle_id="cycle-test-001",
        event_type="cycle_sealed",
        cycle_status="SEALED_PRE_EXPOSURE",
        previous_receipt_sha256=None,
        freeze_commitment_sha256="1" * 64,
        evaluation_version_sha256="2" * 64,
    )
    tampered = copy.deepcopy(seal)
    tampered["reason_code"] = "tampered"
    with pytest.raises(v3c.V3CError, match=r"identity drift|self-hash mismatch"):
        v3c.validate_custody_receipts([tampered], artifact)

    divergent = copy.deepcopy(seal)
    divergent["reason_code"] = "divergent"
    with pytest.raises(v3c.V3CError, match=r"identity drift|self-hash mismatch|divergent"):
        v3c.validate_custody_receipts([seal, divergent], artifact)


def test_forbidden_heldout_fields_and_post_exposure_state_are_rejected() -> None:
    artifact = _artifact()
    value = copy.deepcopy(artifact)
    value["residual_query"]["rows"][0]["heldout_content"] = "forbidden"
    value["receipt_sha256"] = v3c.receipt_sha(value)
    with pytest.raises(v3c.V3CError, match=r"schema violation|forbidden field"):
        v3c.validate(value, _schema())

    value = copy.deepcopy(artifact)
    value["temporal_firewall"]["construction_mutation_after_exposure"] = True
    value["receipt_sha256"] = v3c.receipt_sha(value)
    with pytest.raises(v3c.V3CError, match=r"schema violation|temporal firewall drift"):
        v3c.validate(value, _schema())


def test_global_stops_are_frozen() -> None:
    policy = _artifact()["stop_policy"]
    assert policy["global_stop_codes"] == list(v3c.STOP_CODES)
    assert policy["fail_closed"] is True
    assert policy["new_cycle_required_on_invalidation"] is True
    machine = _artifact()["state_machine"]
    assert machine["global_stop_codes"] == list(v3c.STOP_CODES)
    assert machine["invalidated_cycle_cannot_be_reused"] is True
