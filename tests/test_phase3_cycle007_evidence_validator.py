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
from typing import Any

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
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
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "extracted_forms": [],
        "evidence": records,
        "evidence_ids": evidence_ids,
        "phenomenon_evidence_ids": phenomenon_evidence_ids or {},
        "sufficient_support": any(contract.is_sufficient_positive(record) for record in records),
        "archaic_only_risk": False,
        "russian_shadow_suspected": any(record["channel"] == "russian_shadow_suspicion" for record in records),
    }


# --------------------------------------------------------------------------
# Sidecar/manifest fixtures — fixes v3, item 5: every schema field and exact
# constant is mandatory, so these fixtures are fully populated (never the
# minimal partial dicts a conditional check would have tolerated).
# --------------------------------------------------------------------------


def _expected_identity(**overrides: Any) -> dict[str, Any]:
    base = {
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": copy.deepcopy(compiler.CODE_HASHES),
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
    }
    base.update(overrides)
    return base


def _payload_record(row, *, channel="vesum_attestation", source_identity="vesum", status="attested",
                     supports="attestation", phenomenon_id=None, payload=None):
    """Build one evidence record whose retrieval_sha256 is a real sha256_value(payload)."""
    payload = payload if payload is not None else {"marker": f"{channel}:{source_identity}:{phenomenon_id}"}
    record = contract.build_evidence_record(
        channel=channel,
        source_identity=source_identity,
        source_version="v1",
        locator="locator",
        query="слово",
        status=status,
        supports=supports if status == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_value(payload),
        parser_id="test-parser-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else status,
    )
    return record, payload


def _packet_binding(**overrides: Any) -> dict[str, Any]:
    base = {
        "canonical_basename": "packet-0001.json",
        "raw_sha256": "3" * 64,
        "packet_identity_set_sha256": "4" * 64,
    }
    base.update(overrides)
    return base


def _full_sidecar(rows, retrieval_payloads, *, lane="clean_label", identity=None, packet_index=1, packet_binding=None):
    identity = identity or _expected_identity()
    body = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": lane,
        "packet_binding": packet_binding or _packet_binding(),
        "packet_index": packet_index,
        "row_count": len(rows),
        "tokenizer_id": identity["tokenizer_id"],
        "tokenizer_version": identity["tokenizer_version"],
        "code_hashes": identity["code_hashes"],
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
        "network_lookups_performed": 0,
        "rows": rows,
        "retrieval_payloads": dict(retrieval_payloads),
    }
    body["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(body)
    return body


def _full_manifest(
    *, identity=None, packet_count=1, row_count=3, sidecars=None,
    source_package_binding=None, mcp_transport_attestation=None, **overrides
):
    identity = identity or _expected_identity()
    sidecars = (
        sidecars
        if sidecars is not None
        else [
            {
                "packet_index": 1,
                "row_count": 3,
                "sidecar_sha256": "a" * 64,
                "sidecar_id": "cycle007_sidecar:" + "b" * 64,
                "lane": "clean_label",
                "packet_binding": _packet_binding(),
            }
        ]
    )
    manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "tokenizer_id": identity["tokenizer_id"],
        "tokenizer_version": identity["tokenizer_version"],
        "code_hashes": identity["code_hashes"],
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
        "packet_count": packet_count,
        "row_count": row_count,
        "network_lookups_performed": 0,
        "counts_by_channel": {},
        "counts_by_status": {},
        "counts_by_supports": {},
        "sufficient_support_rows": 0,
        "archaic_only_risk_rows": 0,
        "russian_shadow_suspected_rows": 0,
        "sidecars": sidecars,
        "source_package_binding": source_package_binding,
        "mcp_transport_attestation": mcp_transport_attestation,
    }
    manifest.update(overrides)
    manifest["manifest_sha256"] = contract.sha256_value(manifest)
    return manifest


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
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a, copy.deepcopy(row_a)], {record["retrieval_sha256"]: payload})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
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


def test_classify_sufficiency_decisive_not_found_overrides_an_attested_record_elsewhere():
    row_evidence = _row_evidence(
        ROW_A,
        [
            _vesum_record(ROW_A, status="not_found"),
            _heritage_record(ROW_A, status="attested"),
        ],
    )
    assert validator.classify_sufficiency(row_evidence) == "insufficient_conflicting"


def test_validate_label_rejects_positive_when_vesum_is_not_found():
    heritage = _heritage_record(ROW_A, status="attested")
    row_evidence = _row_evidence(ROW_A, [_vesum_record(ROW_A, status="not_found"), heritage])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_label_evidence_refs(
            row_evidence,
            decision_code="positive",
            evidence_ids=[heritage["evidence_id"]],
        )
    assert excinfo.value.code == "insufficient_evidence_for_decision"


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
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload})
    sidecar["row_count"] = 5
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "sidecar_shape_drift"


def test_validate_sidecar_detects_sidecar_id_hash_drift():
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload})
    sidecar["sidecar_id"] = "cycle007_sidecar:" + "0" * 64
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "sidecar_id_hash_drift"


def test_validate_sidecar_detects_missing_retrieval_payload():
    record, _payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {})  # the record's retrieval_sha256 is not here
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "retrieval_payload_missing"


def test_validate_sidecar_rejects_a_missing_required_field():
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload})
    del sidecar["code_hashes"]
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "sidecar_shape_drift"


def test_validate_sidecar_detects_identity_hash_drift():
    """A rehashed sidecar that self-consistently substitutes an arbitrary code/source hash still fails closed."""
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity(vesum_db_sha256="9" * 64))
    assert excinfo.value.code == "identity_hash_drift"


def test_validate_sidecar_detects_retrieval_payload_hash_drift():
    record, _payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: {"tampered": True}})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "retrieval_payload_hash_drift"


def test_validate_sidecar_rejects_an_unreferenced_retrieval_payload():
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    extra_payload = {"unused": True}
    sidecar = _full_sidecar(
        [row_a],
        {record["retrieval_sha256"]: payload, contract.sha256_value(extra_payload): extra_payload},
    )
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "retrieval_payload_unreferenced"


def test_validate_sidecar_rejects_clean_lane_phenomenon_contamination():
    record, payload = _payload_record(ROW_A, phenomenon_id="apostrophe")
    row_a = _row_evidence(ROW_A, [record], phenomenon_evidence_ids={"apostrophe": [record["evidence_id"]]})
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload}, lane="clean_label")
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "clean_lane_phenomenon_contamination"


def test_validate_sidecar_rejects_residual_lane_missing_a_phenomenon():
    """Subset of the frozen 23-phenomenon taxonomy — never silently accepted."""
    pairs = [_payload_record(ROW_A, phenomenon_id=p) for p in contract.RESIDUAL_PHENOMENON_TAXONOMY[:-1]]
    records = [record for record, _payload in pairs]
    payload_map = {record["retrieval_sha256"]: payload for record, payload in pairs}
    phenomenon_evidence_ids = {record["phenomenon_id"]: [record["evidence_id"]] for record in records}
    row_a = _row_evidence(ROW_A, records, phenomenon_evidence_ids=phenomenon_evidence_ids)
    sidecar = _full_sidecar([row_a], payload_map, lane="residual_label")
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "residual_lane_phenomenon_scope_drift"


def test_validate_sidecar_rejects_residual_lane_extra_phenomenon_key():
    pairs = [_payload_record(ROW_A, phenomenon_id=p) for p in contract.RESIDUAL_PHENOMENON_TAXONOMY]
    records = [record for record, _payload in pairs]
    payload_map = {record["retrieval_sha256"]: payload for record, payload in pairs}
    phenomenon_evidence_ids = {record["phenomenon_id"]: [record["evidence_id"]] for record in records}
    phenomenon_evidence_ids["not-a-real-phenomenon"] = []
    row_a = _row_evidence(ROW_A, records, phenomenon_evidence_ids=phenomenon_evidence_ids)
    sidecar = _full_sidecar([row_a], payload_map, lane="residual_label")
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())
    assert excinfo.value.code == "residual_lane_phenomenon_scope_drift"


def test_validate_manifest_accepts_a_well_formed_manifest():
    manifest = _full_manifest()
    validator.validate_manifest(manifest, expected_identity=_expected_identity())


def test_validate_manifest_detects_manifest_sha256_hash_drift():
    manifest = _full_manifest()
    manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_id_hash_drift"


def test_validate_manifest_detects_row_count_mismatch():
    manifest = _full_manifest(row_count=999)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"


def test_validate_manifest_rejects_a_missing_required_field():
    manifest = _full_manifest()
    del manifest["code_hashes"]
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"


def test_validate_manifest_detects_identity_hash_drift():
    manifest = _full_manifest()
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity(server_code_sha256="9" * 64))
    assert excinfo.value.code == "identity_hash_drift"


# --------------------------------------------------------------------------
# Amendment (fixes v3, item 5): private query field required + recomputed.
# --------------------------------------------------------------------------


def test_validate_evidence_record_detects_query_mutation():
    record = dict(_vesum_record(ROW_A))
    record["query"] = "інше слово"  # mutated without updating query_sha256
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "query_sha256_hash_drift"


def test_validate_evidence_record_rejects_a_deleted_query_field():
    record = dict(_vesum_record(ROW_A))
    del record["query"]
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == "evidence_shape_drift"


# --------------------------------------------------------------------------
# P1 schema hardening reprobes: the Python gate must reject the same malformed
# shapes, unsafe names, and count drifts that the published schemas/producer
# contract exclude, even when a caller rehashes its outer container.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda record: record.__setitem__("extra", True), "evidence_shape_drift"),
        (lambda record: record.__setitem__("row_identity", {"unit_id": "unit-a", "unit_sha256": "A" * 64}), "evidence_shape_drift"),
        (lambda record: record.__setitem__("retrieval_sha256", "g" * 64), "evidence_shape_drift"),
        (lambda record: record.__setitem__("phenomenon_id", "invented"), "evidence_shape_drift"),
    ],
)
def test_validate_evidence_record_rejects_closed_schema_reprobes(mutate, expected_code):
    record = dict(_vesum_record(ROW_A))
    mutate(record)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_evidence_record(record)
    assert excinfo.value.code == expected_code


def test_validate_row_evidence_rejects_extra_key_and_non_hex_row_identity():
    record = _vesum_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record])
    row_evidence["unit_sha256"] = "A" * 64
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "row_identity_drift"

    row_evidence = _row_evidence(ROW_A, [record])
    row_evidence["extra"] = True
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "row_shape_drift"


def test_validate_row_evidence_recomputes_compiler_boolean_summaries():
    record = _vesum_record(ROW_A)
    row_evidence = _row_evidence(ROW_A, [record])
    row_evidence["sufficient_support"] = False
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "row_count_drift"


def test_validate_row_evidence_requires_a_complete_phenomenon_index():
    record = _vesum_record(ROW_A, phenomenon_id="apostrophe")
    row_evidence = _row_evidence(ROW_A, [record])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_row_evidence(row_evidence)
    assert excinfo.value.code == "phenomenon_evidence_set_drift"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda sidecar: sidecar.__setitem__("evaluation_cycle_id", "phase3-v2-1-evaluation-cycle-006"),
        lambda sidecar: sidecar["packet_binding"].__setitem__("canonical_basename", "../packet-0001.json"),
        lambda sidecar: sidecar["packet_binding"].__setitem__("raw_sha256", "A" * 64),
        lambda sidecar: sidecar["rows"][0].__setitem__("tokenizer_version", "drift"),
        lambda sidecar: sidecar.__setitem__("extra", True),
    ],
)
def test_validate_sidecar_rejects_closed_shape_cycle_hash_and_packet_name_reprobes(mutate):
    record, payload = _payload_record(ROW_A)
    row_a = _row_evidence(ROW_A, [record])
    sidecar = _full_sidecar([row_a], {record["retrieval_sha256"]: payload})
    mutate(sidecar)
    with pytest.raises(validator.EvidenceValidationError):
        validator.validate_sidecar(sidecar, expected_identity=_expected_identity())


def test_validate_manifest_rejects_missing_required_count_fields_and_count_map_total_drift():
    manifest = _full_manifest()
    del manifest["counts_by_channel"]
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"

    manifest = _full_manifest(counts_by_channel={"vesum_attestation": 1})
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.__setitem__("evaluation_cycle_id", "phase3-v2-1-evaluation-cycle-006"),
        lambda manifest: manifest.__setitem__("extra", True),
        lambda manifest: manifest["sidecars"][0].__setitem__("sidecar_sha256", "A" * 64),
        lambda manifest: manifest["sidecars"][0]["packet_binding"].__setitem__("canonical_basename", "/tmp/packet-0001.json"),
    ],
)
def test_validate_manifest_rejects_closed_entry_cycle_hash_and_packet_name_reprobes(mutate):
    manifest = _full_manifest()
    mutate(manifest)
    with pytest.raises(validator.EvidenceValidationError):
        validator.validate_manifest(manifest, expected_identity=_expected_identity())


def test_validate_manifest_requires_ordered_unique_typed_sidecar_entries():
    first = _full_manifest()["sidecars"][0]
    second = copy.deepcopy(first)
    second["packet_index"] = 1
    second["sidecar_id"] = "cycle007_sidecar:" + "c" * 64
    manifest = _full_manifest(packet_count=2, row_count=6, sidecars=[first, second])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"

    second["packet_index"] = True
    manifest = _full_manifest(packet_count=2, row_count=6, sidecars=[first, second])
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "manifest_shape_drift"


def test_validate_manifest_checks_source_package_binding_semantics():
    binding = {
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": "c" * 64,
        "materialization_manifest_sha256": "d" * 64,
        "ordered_identity_commitment_sha256": "e" * 64,
        "identity_union_commitment_sha256": "f" * 64,
        "ordered_packet_commitment_sha256": "1" * 64,
        "packet_count": 1,
        "row_count": 3,
    }
    manifest = _full_manifest(source_package_binding=binding)
    validator.validate_manifest(manifest, expected_identity=_expected_identity())

    binding = copy.deepcopy(binding)
    binding["source_evaluation_cycle_id"] = "phase3-v2-1-evaluation-cycle-006"
    manifest = _full_manifest(source_package_binding=binding)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "source_package_binding_shape_drift"

    binding = copy.deepcopy(binding)
    binding["source_evaluation_cycle_id"] = "phase3-v2-1-evaluation-cycle-005"
    binding["row_count"] = 4
    manifest = _full_manifest(source_package_binding=binding)
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(manifest, expected_identity=_expected_identity())
    assert excinfo.value.code == "source_package_binding_shape_drift"


def test_real_denominator_requires_reconciled_streamable_http_attestation():
    sidecars = [
        {
            "packet_index": index,
            "row_count": 9 if index == 204 else 50,
            "sidecar_sha256": f"{index:064x}",
            "sidecar_id": "cycle007_sidecar:" + f"{index + 204:064x}",
            "lane": "clean_label" if index <= 40 else "residual_label",
            "packet_binding": {
                "canonical_basename": f"packet-{index:04d}.json",
                "raw_sha256": f"{index + 408:064x}",
                "packet_identity_set_sha256": f"{index + 612:064x}",
            },
        }
        for index in range(1, 205)
    ]
    binding = {
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": "c" * 64,
        "materialization_manifest_sha256": "d" * 64,
        "ordered_identity_commitment_sha256": "e" * 64,
        "identity_union_commitment_sha256": "f" * 64,
        "ordered_packet_commitment_sha256": "1" * 64,
        "packet_count": 204,
        "row_count": 10_159,
    }
    attestation = {
        "schema_version": "phase3_cycle007_mcp_transport_attestation_v1",
        "transport": "streamable_http",
        "endpoint_sha256": contract.sha256_text("http://127.0.0.1:8766/mcp"),
        "required_tool_set_sha256": "2" * 64,
        "tool_call_count": 10_160,
        "counts_by_tool": {"mcp_server_identity": 1, "verify_words": 10_159},
        "server_identity_call_count": 1,
        "ordered_call_commitment_sha256": "3" * 64,
    }
    manifest = _full_manifest(
        packet_count=204,
        row_count=10_159,
        sidecars=sidecars,
        source_package_binding=binding,
        mcp_transport_attestation=attestation,
    )
    validator.validate_manifest(manifest, expected_identity=_expected_identity())

    missing = dict(manifest)
    missing["mcp_transport_attestation"] = None
    missing["manifest_sha256"] = contract.sha256_value(
        {key: value for key, value in missing.items() if key != "manifest_sha256"}
    )
    with pytest.raises(validator.EvidenceValidationError) as excinfo:
        validator.validate_manifest(missing, expected_identity=_expected_identity())
    assert excinfo.value.code == "mcp_transport_attestation_drift"
