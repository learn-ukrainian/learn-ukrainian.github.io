"""Synthetic public tests for the Cycle 007 evidence validator.

Builds evidence records directly through
``phase3_cycle007_evidence_contract`` so these tests are independent of the
compiler's client wiring and focus purely on the validator's fail-closed
behavior: sorted/unique same-row and same-phenomenon evidence IDs,
sufficient-support decisions, source-role boundaries, and fail-closed
missing/conflicting/unavailable evidence.
"""

from __future__ import annotations

import copy

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

ROW_A = {"unit_id": "unit-a", "unit_sha256": "a" * 64}
ROW_B = {"unit_id": "unit-b", "unit_sha256": "b" * 64}


def _vesum_record(row, *, status="attested", supports="attestation", phenomenon_id=None):
    return contract.build_evidence_record(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="data/vesum.db#forms",
        query="слово",
        status=status,
        supports=supports if status == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_text("payload"),
        parser_id="vesum-forms-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else status,
    )


def _heritage_record(row, *, status="attested", phenomenon_id=None):
    return contract.build_evidence_record(
        channel="heritage_attestation",
        source_identity="heritage-cache",
        source_version="v1",
        locator="repo:data/sources.db#heritage",
        query="слово",
        status=status,
        supports="attestation" if status == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_text("heritage-payload"),
        parser_id="heritage-cache-search-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else status,
    )


def _shadow_record(row):
    return contract.build_evidence_record(
        channel="russian_shadow_suspicion",
        source_identity="check_ru_morph",
        source_version="v1",
        locator="repo:scripts/verification/check_ru_morph.py",
        query="слово",
        status="attested",
        supports="suspicion",
        retrieval_sha256=contract.sha256_text("payload"),
        parser_id="russian-shadow-heuristic-v1",
        parser_version="1",
        row=row,
    )


def _row_evidence(row, records, *, phenomenon_evidence_ids=None):
    evidence_ids = sorted({record["evidence_id"] for record in records})
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "evidence": records,
        "evidence_ids": evidence_ids,
        "phenomenon_evidence_ids": phenomenon_evidence_ids or {},
        "sufficient_support": any(contract.is_sufficient_positive(record) for record in records),
        "archaic_only_risk": False,
        "russian_shadow_suspected": any(record["channel"] == "russian_shadow_suspicion" for record in records),
    }


# --------------------------------------------------------------------------
# validate_evidence_record / validate_row_evidence
# --------------------------------------------------------------------------


def test_validate_row_evidence_accepts_well_formed_row():
    records = [_vesum_record(ROW_A), _shadow_record(ROW_A)]
    validator.validate_row_evidence(_row_evidence(ROW_A, records))


def test_validate_evidence_record_detects_hash_drift():
    record = dict(_vesum_record(ROW_A))
    record["evidence_id"] = "cycle007_evidence:" + "0" * 64
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "evidence_id_hash_drift"


def test_validate_evidence_record_detects_source_role_boundary_violation():
    """A hand-edited record claiming russian_shadow_suspicion=attestation must fail closed."""
    record = dict(_shadow_record(ROW_A))
    record["supports"] = "attestation"  # forbidden for this channel
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "source_role_boundary_violation"


def test_validate_row_evidence_rejects_cross_row_evidence():
    foreign_record = _vesum_record(ROW_B)
    row_evidence = _row_evidence(ROW_A, [foreign_record])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "cross_row_evidence"


def test_validate_row_evidence_rejects_duplicate_evidence_id():
    record = _vesum_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record, copy.deepcopy(record)])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "duplicate_evidence_id"


def test_validate_row_evidence_rejects_unsorted_declared_ids():
    record_a = _vesum_record(ROW_A)
    record_b = _shadow_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record_a, record_b])
    row_evidence["evidence_ids"] = list(reversed(row_evidence["evidence_ids"]))
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "evidence_id_order_drift"


def test_validate_row_evidence_rejects_invented_declared_id():
    record = _vesum_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record])
    row_evidence["evidence_ids"] = sorted({*row_evidence["evidence_ids"], "cycle007_evidence:" + "f" * 64})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "evidence_id_set_drift"


def test_validate_row_evidence_rejects_cross_phenomenon_evidence():
    scoped = _vesum_record(ROW_A, phenomenon_id="apostrophe")
    row_evidence = _row_evidence(ROW_A, [scoped], phenomenon_evidence_ids={"punctuation": [scoped["evidence_id"]]})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "cross_phenomenon_evidence"


def test_validate_sidecar_rejects_duplicate_row():
    row_a = _row_evidence(ROW_A, [_vesum_record(ROW_A)])
    sidecar = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "row_count": 2,
        "rows": [row_a, copy.deepcopy(row_a)],
    }
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar)
    assert excinfo.value.code == "duplicate_row"


# --------------------------------------------------------------------------
# classify_sufficiency: fail-closed missing/conflicting/unavailable
# --------------------------------------------------------------------------


def test_classify_sufficiency_sufficient():
    row_evidence = _row_evidence(ROW_A, [_vesum_record(ROW_A, status="attested", supports="attestation")])
    assert validator.classify_sufficiency(row_evidence) == "sufficient"


def test_classify_sufficiency_missing():
    row_evidence = _row_evidence(ROW_A, [_vesum_record(ROW_A, status="not_found")])
    assert validator.classify_sufficiency(row_evidence) == "insufficient_missing"


def test_classify_sufficiency_unavailable():
    row_evidence = _row_evidence(ROW_A, [_vesum_record(ROW_A, status="unavailable")])
    assert validator.classify_sufficiency(row_evidence) == "insufficient_unavailable"


def test_classify_sufficiency_conflicting():
    row_evidence = _row_evidence(ROW_A, [_vesum_record(ROW_A, status="ambiguous")])
    assert validator.classify_sufficiency(row_evidence) == "insufficient_conflicting"


def test_classify_sufficiency_prioritizes_conflicting_over_unavailable():
    row_evidence = _row_evidence(
        ROW_A,
        [_vesum_record(ROW_A, status="ambiguous"), _vesum_record(ROW_A, status="unavailable", supports="attestation")],
    )
    # Two distinct records collide on evidence_id only if every field matches;
    # status differs here so both survive as distinct evidence entries.
    assert validator.classify_sufficiency(row_evidence) == "insufficient_conflicting"


# --------------------------------------------------------------------------
# validate_label_evidence_refs: sufficiency + scoping gate
# --------------------------------------------------------------------------


def test_validate_label_evidence_refs_accepts_sufficient_agree_decision():
    record = _vesum_record(ROW_A, status="attested", supports="attestation")
    row_evidence = _row_evidence(ROW_A, [record])
    validator.validate_label_evidence_refs(row_evidence, decision_code="agree", evidence_ids=[record["evidence_id"]])


def test_validate_label_evidence_refs_rejects_insufficient_agree_decision():
    record = _vesum_record(ROW_A, status="not_found")
    row_evidence = _row_evidence(ROW_A, [record])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence, decision_code="agree", evidence_ids=[record["evidence_id"]])
    assert excinfo.value.code == "insufficient_evidence_for_decision"


def test_validate_label_evidence_refs_uncertainty_path_never_needs_sufficiency():
    record = _vesum_record(ROW_A, status="not_found")
    row_evidence = _row_evidence(ROW_A, [record])
    validator.validate_label_evidence_refs(
        row_evidence, decision_code="reject_insufficient_locator_evidence", evidence_ids=[record["evidence_id"]]
    )


def test_validate_label_evidence_refs_rejects_cross_row_reference():
    record = _vesum_record(ROW_B, status="attested", supports="attestation")
    row_evidence_a = _row_evidence(ROW_A, [])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence_a, decision_code="agree", evidence_ids=[record["evidence_id"]])
    assert excinfo.value.code == "cross_row_evidence"


def test_validate_label_evidence_refs_rejects_cross_phenomenon_reference():
    scoped = _vesum_record(ROW_A, status="attested", supports="attestation", phenomenon_id="apostrophe")
    row_evidence = _row_evidence(ROW_A, [scoped], phenomenon_evidence_ids={"apostrophe": [scoped["evidence_id"]]})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(
            row_evidence, decision_code="positive", evidence_ids=[scoped["evidence_id"]], phenomenon_id="punctuation"
        )
    assert excinfo.value.code == "cross_phenomenon_evidence"


def test_validate_label_evidence_refs_rejects_reordered_ids():
    record_a = _vesum_record(ROW_A)
    record_b = _shadow_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record_a, record_b])
    reordered = sorted(row_evidence["evidence_ids"], reverse=True)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence, decision_code="abstention", evidence_ids=reordered)
    assert excinfo.value.code == "evidence_id_order_drift"


def test_validate_label_evidence_refs_rejects_unknown_decision_code():
    record = _vesum_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence, decision_code="not_a_real_code", evidence_ids=[record["evidence_id"]])
    assert excinfo.value.code == "unknown_decision_code"


# --------------------------------------------------------------------------
# Amendment step 7: sufficiency ordering — a decisive negative record forces
# uncertainty even when an unrelated record is attested.
# --------------------------------------------------------------------------


def test_classify_sufficiency_decisive_unavailable_overrides_an_attested_record_elsewhere():
    row_evidence = _row_evidence(
        ROW_A,
        [
            _vesum_record(ROW_A, status="attested", supports="attestation"),
            _heritage_record(ROW_A, status="unavailable"),
        ],
    )
    assert validator.classify_sufficiency(row_evidence) == "insufficient_unavailable"


def test_classify_sufficiency_decisive_conflicting_overrides_an_attested_record_elsewhere():
    row_evidence = _row_evidence(
        ROW_A,
        [
            _vesum_record(ROW_A, status="attested", supports="attestation"),
            _heritage_record(ROW_A, status="ambiguous"),
        ],
    )
    assert validator.classify_sufficiency(row_evidence) == "insufficient_conflicting"


def test_validate_label_evidence_refs_rejects_agree_when_a_decisive_channel_is_unavailable_elsewhere():
    vesum = _vesum_record(ROW_A, status="attested", supports="attestation")
    row_evidence = _row_evidence(ROW_A, [vesum, _heritage_record(ROW_A, status="unavailable")])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(row_evidence, decision_code="agree", evidence_ids=[vesum["evidence_id"]])
    assert excinfo.value.code == "insufficient_evidence_for_decision"
    # The uncertainty path remains valid with the same citation.
    validator.validate_label_evidence_refs(row_evidence, decision_code="abstention", evidence_ids=[vesum["evidence_id"]])


def test_classify_sufficiency_is_phenomenon_scoped():
    """A decisive negative bound to a different phenomenon must not block this one."""
    scoped_positive = _vesum_record(ROW_A, status="attested", supports="attestation", phenomenon_id="apostrophe")
    other_phenomenon_negative = _heritage_record(ROW_A, status="unavailable", phenomenon_id="punctuation")
    row_evidence = _row_evidence(
        ROW_A,
        [scoped_positive, other_phenomenon_negative],
        phenomenon_evidence_ids={
            "apostrophe": [scoped_positive["evidence_id"]],
            "punctuation": [other_phenomenon_negative["evidence_id"]],
        },
    )
    assert validator.classify_sufficiency(row_evidence, phenomenon_id="apostrophe") == "sufficient"
    assert validator.classify_sufficiency(row_evidence, phenomenon_id="punctuation") == "insufficient_unavailable"


# --------------------------------------------------------------------------
# Amendment step 12: raw_payload_publication_allowed / claim_boundary /
# sidecar_id / manifest_sha256 shape checks.
# --------------------------------------------------------------------------


def test_validate_evidence_record_rejects_a_hand_edited_raw_payload_flag():
    record = dict(_vesum_record(ROW_A))
    record["raw_payload_publication_allowed"] = True
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "evidence_shape_drift"


def test_validate_evidence_record_rejects_a_hand_edited_claim_boundary_flag():
    record = dict(_vesum_record(ROW_A))
    record["claim_boundary"] = dict(record["claim_boundary"])
    record["claim_boundary"]["authoritative"] = True
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "evidence_shape_drift"


def test_validate_sidecar_rejects_row_count_mismatch():
    row_a = _row_evidence(ROW_A, [_vesum_record(ROW_A)])
    sidecar = {"schema_version": "phase3_cycle007_evidence_sidecar_v1", "row_count": 5, "rows": [row_a]}
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar)
    assert excinfo.value.code == "sidecar_shape_drift"


def test_validate_sidecar_detects_sidecar_id_hash_drift():
    row_a = _row_evidence(ROW_A, [_vesum_record(ROW_A)])
    sidecar = {"schema_version": "phase3_cycle007_evidence_sidecar_v1", "row_count": 1, "rows": [row_a]}
    sidecar["sidecar_id"] = "cycle007_sidecar:" + "0" * 64
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar)
    assert excinfo.value.code == "sidecar_id_hash_drift"


def test_validate_sidecar_detects_missing_retrieval_payload():
    record = _vesum_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "row_count": 1,
        "rows": [row_a],
        "retrieval_payloads": {},  # the record's retrieval_sha256 is not here
    }
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar)
    assert excinfo.value.code == "retrieval_payload_missing"


def test_validate_manifest_accepts_a_well_formed_manifest():
    manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "packet_count": 1,
        "row_count": 3,
        "sidecars": [{"packet_index": 1, "row_count": 3, "sidecar_sha256": "a" * 64}],
    }
    manifest["manifest_sha256"] = contract.sha256_value(manifest)
    validator.validate_manifest(manifest)


def test_validate_manifest_detects_manifest_sha256_hash_drift():
    manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "packet_count": 1,
        "row_count": 3,
        "sidecars": [{"packet_index": 1, "row_count": 3, "sidecar_sha256": "a" * 64}],
        "manifest_sha256": "0" * 64,
    }
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest)
    assert excinfo.value.code == "manifest_id_hash_drift"


def test_validate_manifest_detects_row_count_mismatch():
    manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "packet_count": 1,
        "row_count": 999,
        "sidecars": [{"packet_index": 1, "row_count": 3, "sidecar_sha256": "a" * 64}],
    }
    manifest["manifest_sha256"] = contract.sha256_value(manifest)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest)
    assert excinfo.value.code == "manifest_shape_drift"
