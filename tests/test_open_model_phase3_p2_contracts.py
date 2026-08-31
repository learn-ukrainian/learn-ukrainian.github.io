"""Adversarial, metadata-only checks for the Phase 3 P2 contract (#7426).

These fixtures contain identifiers, hashes, and contract metadata only.  They
never open source/evidence bodies, call a provider, create labels/gold, or
train a model.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import freeze_phase3_p2_contracts as p2

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/projects/open_model_data"
P1 = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P2 = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
SCHEMA = DATA / "contracts/phase3_p2_canonical_contracts_v1.schema.json"
P1_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
SHA256 = "a" * 64
AUTHORITY = {
    "authority_kind": "source_qualified_human_adjudication",
    "actor_kind": "human",
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(p2.canonical_json(value))


def _contract() -> dict[str, Any]:
    return copy.deepcopy(p2.build_contract())


def _validate_contract(value: dict[str, Any]) -> None:
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(value)


def _p1_cells() -> dict[str, dict[str, Any]]:
    manifest = _json(P1)
    return {item["cell_id"]: item for item in manifest["required_cell_manifest"]["cells"]}


def _cell_id(status: str) -> str:
    return next(cell_id for cell_id, cell in _p1_cells().items() if cell["status"] == status)


def _protected_cell_id() -> str:
    return next(cell_id for cell_id, cell in _p1_cells().items() if cell["protection_required"])


def _eligible_source_unit(*, protected: bool = False) -> dict[str, Any]:
    return next(
        unit
        for unit in _json(P1)["source_manifest"]["source_units"]
        if unit["rights"]["required_state"] == "scoped_capability"
        and unit["source_unit_disposition"] == ("protected" if protected else "supporting_only")
    )


def _evidence_ref(claim_role: str, suffix: str, *, protected: bool = False) -> dict[str, str]:
    unit = _eligible_source_unit(protected=protected)
    return {
        "evidence_ref_id": f"evidence:{suffix}",
        "claim_role": claim_role,
        "source_unit_id": unit["source_unit_id"],
        "source_unit_identity_sha256": unit["identity_sha256"],
        "source_artifact_sha256": unit["source_artifact"]["sha256"],
        "provenance_sha256": p2.sha256_bytes(p2.canonical_json(unit["provenance"])),
    }


def _set_evidence_roles(record: dict[str, Any], roles: list[str]) -> None:
    protected = record["record_kind"] == "protected_historical_context"
    refs = [_evidence_ref(role, f"mutation-{index}", protected=protected) for index, role in enumerate(roles)]
    record["evidence_refs"] = refs
    record["authority"]["evidence_ref_ids"] = sorted(ref["evidence_ref_id"] for ref in refs)


def _satisfied_p1_for(record_kind: str) -> dict[str, Any]:
    """Return a metadata-only P1 view with one suitable stratum satisfied."""
    value = _json(P1)
    target_id = _protected_cell_id() if record_kind == "protected_historical_context" else _cell_id("coverage_blocked")
    for cell in value["required_cell_manifest"]["cells"]:
        if cell["cell_id"] == target_id:
            cell["status"] = "satisfied"
            break
    return value


def _case(record_kind: str) -> dict[str, Any]:
    if record_kind == "coverage_blocked":
        return {
            "record_kind": record_kind,
            "coverage_stratum_id": _cell_id("coverage_blocked"),
            "blocker_code": "rights_or_evidence_unavailable",
        }

    required_roles = {
        "correct_modern_production": ["applicability_scope", "rights_provenance"],
        "source_backed_correction": ["applicability_scope", "correction_authority", "rights_provenance"],
        "minimal_contrast": ["minimal_contrast_authority", "rights_provenance"],
        "protected_historical_context": ["protected_historical_identity", "rights_provenance"],
        "abstention": ["abstention_or_not_applicable_authority", "rights_provenance"],
        "not_applicable_with_evidence": ["abstention_or_not_applicable_authority", "rights_provenance"],
    }
    protected = record_kind == "protected_historical_context"
    refs = [
        _evidence_ref(role, f"{record_kind}-{index}", protected=protected)
        for index, role in enumerate(required_roles[record_kind])
    ]
    value: dict[str, Any] = {
        "record_kind": record_kind,
        "record_id": f"case:{record_kind}",
        "coverage_stratum_id": (
            _cell_id("not_applicable_with_evidence")
            if record_kind == "not_applicable_with_evidence"
            else _protected_cell_id()
            if record_kind == "protected_historical_context"
            else _cell_id("coverage_blocked")
        ),
        "evidence_refs": refs,
        "authority": {
            **copy.deepcopy(AUTHORITY),
            "adjudication_id": f"adjudication:{record_kind}",
            "evidence_ref_ids": sorted(ref["evidence_ref_id"] for ref in refs),
        },
    }
    if record_kind == "protected_historical_context":
        value.update(
            {
                "historical_identity": "old_east_slavic_kyivan_rus",
                "period_id": "period:fixture",
                "region_id": "region:fixture",
                "recension_editorial_layer": "recension:fixture",
                "modern_normalization": False,
            }
        )
    elif record_kind == "abstention":
        value["abstention_reason_code"] = "identity_unresolved"
    elif record_kind == "not_applicable_with_evidence":
        value["not_applicable_evidence_id"] = "evidence:scope-boundary"
    elif record_kind in {
        "correct_modern_production",
        "source_backed_correction",
        "minimal_contrast",
    }:
        value["rule_slot_id"] = "p2_rule_slot:" + SHA256
        if record_kind == "minimal_contrast":
            value["contrast_pair_id"] = "contrast:fixture"
    return value


def _proposal(*, producer_kind: str = "model") -> dict[str, Any]:
    value: dict[str, Any] = {
        "record_kind": "proposal",
        "proposal_id": "proposal:fixture",
        "producer_kind": producer_kind,
        "producer_provenance": {
            "producer_kind": producer_kind,
            "run_identity_sha256": SHA256,
            "input_identity_sha256": P1_SHA256,
            "proposal_process_version": "phase3-p2-proposal-fixture-v1",
        },
        "input_identity_sha256": P1_SHA256,
        "proposal_metadata_sha256": SHA256,
    }
    value["proposal_sha256"] = p2.sha256_bytes(p2.canonical_json(value))
    return value


def _promotion(proposal: dict[str, Any], *, decision: str = "pending") -> dict[str, Any]:
    return {
        "record_kind": "promotion_decision",
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal["proposal_sha256"],
        "decision": decision,
        "authority": copy.deepcopy(AUTHORITY),
    }


def test_p2_artifact_reproduces_exactly_from_the_frozen_p1_metadata() -> None:
    artifact = _json(P2)
    generated = p2.build_contract()
    assert artifact == generated

    p1 = _json(P1)
    p1_binding = generated["p1_binding"]
    assert p2.sha256_file(P1) == P1_SHA256 == p2.PINNED_P1_MANIFEST_SHA256
    assert p1_binding["p1_manifest"] == {
        "path": "data/projects/open_model_data/evidence/phase3_p1_universe_freeze_v1.json",
        "sha256": P1_SHA256,
    }
    assert p1_binding["source_unit_count"] == len(p1["source_manifest"]["source_units"]) == 57
    assert p1_binding["unknown_rights_blocker_count"] == sum(
        unit["rights"]["required_state"] == "unknown" for unit in p1["source_manifest"]["source_units"]
    ) == 39
    expected_statuses = [
        {"cell_id": cell["cell_id"], "status": cell["status"]}
        for cell in sorted(p1["required_cell_manifest"]["cells"], key=lambda item: item["cell_id"])
    ]
    assert p1_binding["required_cell_count"] == len(expected_statuses) == 15
    assert p1_binding["required_cell_statuses"] == expected_statuses


def test_p2_schema_is_strict_and_the_frozen_artifact_validates() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    _validate_contract(_json(P2))


def test_r_is_empty_until_source_qualified_rule_admission_and_is_hash_bound() -> None:
    rule_universe = _contract()["rule_slot_universe"]
    assert rule_universe["symbol"] == "R"
    assert rule_universe["coverage_strata_are_rules"] is False
    assert rule_universe["slot_count"] == 0
    assert rule_universe["slots"] == []
    assert rule_universe["rule_manifest_sha256"] == p2.sha256_bytes(p2.canonical_json([]))

    algorithm = rule_universe["algorithm"]
    unsigned_algorithm = {key: value for key, value in algorithm.items() if key != "algorithm_sha256"}
    assert algorithm["input_p1_manifest_sha256"] == P1_SHA256
    assert algorithm["algorithm_sha256"] == p2.sha256_bytes(p2.canonical_json(unsigned_algorithm))
    assert "p1_cells_are_coverage_strata_not_rules" in algorithm["derivation"]


def test_r_merge_split_and_denominator_changes_are_versioned_and_fail_closed() -> None:
    rule_universe = _contract()["rule_slot_universe"]
    assert rule_universe["merge_criteria"] == {
        "permitted": True,
        "requires": ["source_qualified_claim_typed_evidence", "human_adjudication", "all_parent_slot_ids"],
        "preserves": ["p1_cell_id", "case_denominator"],
        "version_effect": "new_rule_manifest_version",
    }
    assert rule_universe["split_criteria"] == {
        "permitted": True,
        "requires": ["source_qualified_claim_typed_evidence", "human_adjudication", "parent_slot_id"],
        "preserves": ["p1_cell_id", "case_denominator"],
        "version_effect": "new_rule_manifest_version_with_parent_child_lineage",
    }
    assert rule_universe["denominator_change_policy"] == "new_p1_manifest_sha256_and_new_dataset_version_required"


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("p1_binding", "source_unit_count"), 56),
        (("p1_binding", "unknown_rights_blocker_count"), 38),
        (("p1_binding", "required_cell_count"), 14),
        (("rule_slot_universe", "slot_count"), 1),
        (("rule_slot_universe", "coverage_strata_are_rules"), True),
        (("rule_slot_universe", "rule_manifest_sha256"), SHA256),
        (("rule_slot_universe", "merge_criteria"), "merge any compatible cells"),
        (("rule_slot_universe", "split_criteria"), "split whenever a model requests it"),
        (("rule_slot_universe", "denominator_change_policy"), "revise denominator in place"),
    ],
)
def test_check_rejects_mutations_of_frozen_r_and_p1_bindings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, str],
    replacement: object,
) -> None:
    value = _contract()
    value[path[0]][path[1]] = replacement
    output = tmp_path / "p2.json"
    _write_json(output, value)
    monkeypatch.setattr(p2, "OUTPUT", output)
    monkeypatch.setattr(sys, "argv", ["freeze_phase3_p2_contracts", "--check"])
    with pytest.raises(SystemExit, match="p2_contract_drift"):
        p2.main()


def test_same_count_p1_metadata_mutation_is_rejected_before_contract_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = _json(P1)
    # Preserve every denominator while changing a frozen source identity.
    value["source_manifest"]["source_units"][0]["identity_sha256"] = SHA256
    mutated = tmp_path / "p1-mutated.json"
    _write_json(mutated, value)
    monkeypatch.setattr(p2, "P1", mutated)
    with pytest.raises(ValueError, match="p1_artifact_sha_drift"):
        p2.build_contract()


def test_contract_integrity_rejects_forged_r_and_hidden_denominator_changes() -> None:
    contract = _contract()
    assert p2.validate_contract_integrity(contract) is True

    for section, field, replacement in (
        ("p1_binding", "source_unit_count", 56),
        ("p1_binding", "unknown_rights_blocker_count", 0),
        ("rule_slot_universe", "slot_count", 1),
        ("rule_slot_universe", "coverage_strata_are_rules", True),
        ("rule_slot_universe", "rule_manifest_sha256", SHA256),
        ("rule_slot_universe", "algorithm", {"forged": True}),
    ):
        mutated = copy.deepcopy(contract)
        mutated[section][field] = replacement
        assert p2.validate_contract_integrity(mutated) is False


@pytest.mark.parametrize(
    "field",
    ["source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"],
)
def test_case_evidence_refs_pin_source_identity_artifact_and_provenance(field: str) -> None:
    record = _case("not_applicable_with_evidence")
    record["evidence_refs"][0][field] = SHA256
    assert p2.validate_case_record(record) is False


def test_case_evidence_ref_cannot_use_an_unknown_rights_source() -> None:
    record = _case("not_applicable_with_evidence")
    unknown = next(
        unit
        for unit in _json(P1)["source_manifest"]["source_units"]
        if unit["rights"]["required_state"] == "unknown"
    )
    record["evidence_refs"][0].update(
        {
            "source_unit_id": unknown["source_unit_id"],
            "source_unit_identity_sha256": unknown["identity_sha256"],
            "source_artifact_sha256": unknown["source_artifact"]["sha256"],
            "provenance_sha256": p2.sha256_bytes(p2.canonical_json(unknown["provenance"])),
        }
    )
    assert p2.validate_case_record(record) is False


def test_case_authority_must_bind_exactly_the_cited_evidence_refs() -> None:
    record = _case("not_applicable_with_evidence")
    record["authority"]["evidence_ref_ids"] = ["evidence:not-cited"]
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind",
    ["protected_historical_context", "abstention", "not_applicable_with_evidence", "coverage_blocked"],
)
def test_protected_abstention_na_and_coverage_blocked_are_distinct_states(record_kind: str) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "abstention"}:
        # P1 deliberately has no satisfied semantic cells yet.  A metadata-only
        # fixture can exercise the state shape only through an explicit,
        # non-persisted satisfied-stratum view.
        assert p2.validate_case_record(record) is False
        return
    assert p2.validate_case_record(record) is True


@pytest.mark.parametrize("record_kind", ["protected_historical_context", "abstention"])
def test_semantic_case_roles_validate_only_with_a_satisfied_p1_stratum(
    record_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    assert p2.validate_case_record(_case(record_kind)) is True


@pytest.mark.parametrize(
    ("record_kind", "mutation"),
    [
        ("protected_historical_context", {"modern_normalization": True}),
        ("protected_historical_context", {"historical_identity": "modern_standard_ukrainian"}),
        ("protected_historical_context", {"period_id": ""}),
        ("protected_historical_context", {"rule_slot_id": "p2_rule_slot:" + SHA256}),
        ("abstention", {"not_applicable_evidence_id": "evidence:wrong-state"}),
        ("abstention", {"coverage_stratum_id": _cell_id("not_applicable_with_evidence")}),
        ("not_applicable_with_evidence", {"abstention_reason_code": "reason:wrong-state"}),
        ("not_applicable_with_evidence", {"coverage_stratum_id": _cell_id("coverage_blocked")}),
        ("coverage_blocked", {"authority": copy.deepcopy(AUTHORITY)}),
        ("coverage_blocked", {"coverage_stratum_id": _cell_id("not_applicable_with_evidence")}),
        ("coverage_blocked", {"coverage_stratum_id": "p1-cell:not-frozen"}),
    ],
)
def test_case_state_mutations_fail_closed(
    record_kind: str, mutation: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "abstention"}:
        monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    record.update(copy.deepcopy(mutation))
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    ("record_kind", "wrong_role"),
    [
        ("protected_historical_context", "correction_authority"),
        ("abstention", "protected_historical_identity"),
        ("not_applicable_with_evidence", "correction_authority"),
    ],
)
def test_case_evidence_roles_are_claim_appropriate(
    record_kind: str, wrong_role: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "abstention"}:
        monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    _set_evidence_roles(record, [wrong_role, "rights_provenance"])
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind", ["protected_historical_context", "abstention", "not_applicable_with_evidence"]
)
def test_case_evidence_requires_a_non_attestation_claim_role(
    record_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "abstention"}:
        monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    _set_evidence_roles(record, ["attestation_only", "rights_provenance"])
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "authority",
    [
        {"authority_kind": "source_qualified_human_adjudication", "actor_kind": "model"},
        {"authority_kind": "source_qualified_human_adjudication", "actor_kind": "tool"},
        {"authority_kind": "attestation", "actor_kind": "human"},
        {"authority_kind": "model_agreement", "actor_kind": "human"},
    ],
)
def test_case_authority_laundering_is_rejected(
    authority: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case("protected_historical_context")
    monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for("protected_historical_context"))
    record["authority"].update(authority)
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind", ["correct_modern_production", "source_backed_correction", "minimal_contrast"]
)
def test_rule_backed_case_roles_cannot_fabricate_a_target_when_r_is_empty(record_kind: str) -> None:
    assert p2.validate_case_record(_case(record_kind), _contract()) is False


@pytest.mark.parametrize("producer_kind", ["model", "tool"])
def test_proposals_are_metadata_only_and_can_only_remain_pending_or_rejected(producer_kind: str) -> None:
    proposal = _proposal(producer_kind=producer_kind)
    for decision in ("pending", "rejected"):
        assert p2.validate_promotion(proposal, _promotion(proposal, decision=decision), _contract()) is True


@pytest.mark.parametrize("decision", ["accepted", "admitted", "gold", "target"])
def test_proposals_cannot_promote_to_targets(decision: str) -> None:
    proposal = _proposal()
    assert p2.validate_promotion(proposal, _promotion(proposal, decision=decision), _contract()) is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"proposal_sha256": SHA256},
        {"producer_kind": "human"},
        {"source_text": "forbidden"},
        {"evidence_text": "forbidden"},
        {"gold_text": "forbidden"},
        {"content": "forbidden"},
        {"unexpected_metadata": "must-be-rejected"},
    ],
)
def test_proposal_mutations_and_text_bearing_fields_fail_closed(mutation: dict[str, Any]) -> None:
    proposal = _proposal()
    proposal.update(copy.deepcopy(mutation))
    if "proposal_sha256" not in mutation:
        proposal["proposal_sha256"] = p2.sha256_bytes(
            p2.canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"})
        )
    promotion = _promotion(proposal)
    assert p2.validate_promotion(proposal, promotion, _contract()) is False


def test_promotion_cannot_launder_model_authority_or_mismatch_proposal_identity() -> None:
    proposal = _proposal()
    promotion = _promotion(proposal)
    promotion["authority"] = {"authority_kind": "model_agreement", "actor_kind": "model"}
    assert p2.validate_promotion(proposal, promotion, _contract()) is False

    promotion = _promotion(proposal)
    promotion["proposal_sha256"] = SHA256
    assert p2.validate_promotion(proposal, promotion, _contract()) is False

    # A changed identifier is a new proposal only when its persisted digest
    # and decision are updated together.  Keeping the old decision binding is
    # the crash/resume-style mutation this validator must reject.
    proposal = _proposal()
    promotion = _promotion(proposal)
    proposal["proposal_id"] = "proposal:after-persistence"
    assert p2.validate_promotion(proposal, promotion, _contract()) is False


def test_missing_case_provenance_or_claim_evidence_is_rejected() -> None:
    protected = _case("protected_historical_context")
    del protected["evidence_refs"]
    assert p2.validate_case_record(protected, _contract()) is False

    abstention = _case("abstention")
    abstention["evidence_refs"] = []
    assert p2.validate_case_record(abstention, _contract()) is False

    proposal = _proposal()
    del proposal["producer_provenance"]
    proposal["proposal_sha256"] = p2.sha256_bytes(p2.canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"}))
    assert p2.validate_promotion(proposal, _promotion(proposal), _contract()) is False
