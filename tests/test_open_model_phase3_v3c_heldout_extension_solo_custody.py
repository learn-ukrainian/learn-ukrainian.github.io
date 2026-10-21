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


def test_reseal_cannot_reuse_any_historical_commitment_pair() -> None:
    artifact = _artifact()
    receipts: list[dict[str, Any]] = []

    def append(
        cycle_id: str,
        event_type: str,
        cycle_status: str,
        freeze: str,
        version: str,
        *,
        mutation: bool = False,
        new_cycle_required: bool = False,
    ) -> None:
        previous = receipts[-1]["receipt_sha256"] if receipts else None
        receipts.append(
            _receipt(
                sequence=len(receipts),
                cycle_id=cycle_id,
                event_type=event_type,
                cycle_status=cycle_status,
                previous_receipt_sha256=previous,
                freeze_commitment_sha256=freeze,
                evaluation_version_sha256=version,
                mutation=mutation,
                new_cycle_required=new_cycle_required,
            )
        )

    append("cycle-test-001", "cycle_sealed", "SEALED_PRE_EXPOSURE", "1" * 64, "2" * 64)
    append("cycle-test-001", "exposure", "EXPOSED", "1" * 64, "2" * 64)
    append(
        "cycle-test-001",
        "invalidation",
        "INVALIDATED_RESEAL_REQUIRED",
        "1" * 64,
        "2" * 64,
        mutation=True,
        new_cycle_required=True,
    )
    append("cycle-test-002", "cycle_sealed", "SEALED_PRE_EXPOSURE", "3" * 64, "4" * 64)
    append("cycle-test-002", "exposure", "EXPOSED", "3" * 64, "4" * 64)
    append(
        "cycle-test-002",
        "invalidation",
        "INVALIDATED_RESEAL_REQUIRED",
        "3" * 64,
        "4" * 64,
        mutation=True,
        new_cycle_required=True,
    )
    append("cycle-test-003", "cycle_sealed", "SEALED_PRE_EXPOSURE", "1" * 64, "2" * 64)

    with pytest.raises(v3c.V3CError, match="commitment pair cannot be reused"):
        v3c.validate_custody_receipts(receipts, artifact)


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

    with pytest.raises(v3c.V3CError, match="duplicate custody receipt in canonical stream"):
        v3c.validate_custody_receipts([seal, copy.deepcopy(seal)], artifact)


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
