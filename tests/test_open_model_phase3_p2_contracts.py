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
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import freeze_phase3_p2_contracts as p2

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/projects/open_model_data"
P1 = DATA / "evidence/phase3_p1_universe_freeze_v1.json"
P1_AMENDMENT = DATA / "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json"
P2 = DATA / "evidence/phase3_p2_canonical_contracts_v1.json"
SCHEMA = DATA / "contracts/phase3_p2_canonical_contracts_v1.schema.json"
P1_AMENDMENT_SCHEMA = DATA / "contracts/phase3_p1_dialect_regional_protection_amendment_v1.schema.json"
P1_SHA256 = "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b"
P1_AMENDMENT_SHA256 = "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa"
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


def _validate_case_schema(value: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    case_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        **schema["$defs"]["case_record"],
    }
    Draft202012Validator(case_schema).validate(value)


def _p1_cells() -> dict[str, dict[str, Any]]:
    manifest = _json(P1)
    return {item["cell_id"]: item for item in manifest["required_cell_manifest"]["cells"]}


def _amendment() -> dict[str, Any]:
    return _json(P1_AMENDMENT)


def _composite_cells() -> dict[str, dict[str, Any]]:
    base = list(_p1_cells().values())
    additive = _amendment()["amendment"]["additive_cells"]
    return {item["cell_id"]: item for item in [*base, *additive]}


def _cell_id(status: str) -> str:
    return next(cell_id for cell_id, cell in _p1_cells().items() if cell["status"] == status)


def _protected_cell_id() -> str:
    return next(cell_id for cell_id, cell in _p1_cells().items() if cell["protection_required"])


def _dialect_cell_id() -> str:
    return next(
        cell_id
        for cell_id, cell in _composite_cells().items()
        if cell.get("role") == "protected_dialect_or_regional"
    )


def _composite_input_sha256() -> str:
    statuses = [
        {"cell_id": cell["cell_id"], "status": cell["status"]}
        for cell in sorted(_composite_cells().values(), key=lambda item: item["cell_id"])
    ]
    return p2.sha256_bytes(
        p2.canonical_json(
            {
                "base_p1_manifest_sha256": P1_SHA256,
                "dialect_regional_amendment_sha256": P1_AMENDMENT_SHA256,
                "composite_required_cell_statuses": statuses,
            }
        )
    )


def _eligible_source_unit(*, protected: bool = False) -> dict[str, Any]:
    return next(
        unit
        for unit in _json(P1)["source_manifest"]["source_units"]
        if unit["rights"]["required_state"] == "scoped_capability"
        and unit["source_unit_disposition"] == ("protected" if protected else "supporting_only")
    )


def _evidence_ref(
    claim_role: str,
    suffix: str,
    *,
    protected: bool = False,
    coverage_stratum_id: str | None = None,
) -> dict[str, str]:
    unit = _eligible_source_unit(protected=protected)
    if coverage_stratum_id is None:
        coverage_stratum_id = _cell_id("not_applicable_with_evidence")
    candidates = unit.get("identity_candidates")
    identity_candidate = candidates[0] if isinstance(candidates, list) and candidates else unit["source_unit_id"]
    return {
        "evidence_ref_id": f"evidence:{suffix}",
        "claim_role": claim_role,
        "source_unit_id": unit["source_unit_id"],
        "source_class": unit["source_class"],
        "identity_candidate": identity_candidate,
        "coverage_stratum_id": coverage_stratum_id,
        "source_unit_identity_sha256": unit["identity_sha256"],
        "source_artifact_sha256": unit["source_artifact"]["sha256"],
        "provenance_sha256": p2.sha256_bytes(p2.canonical_json(unit["provenance"])),
    }


def _set_evidence_roles(record: dict[str, Any], roles: list[str]) -> None:
    protected = record["record_kind"] == "protected_historical_context"
    refs = [
        _evidence_ref(
            role,
            f"mutation-{index}",
            protected=protected,
            coverage_stratum_id=record["coverage_stratum_id"],
        )
        for index, role in enumerate(roles)
    ]
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
        "protected_dialect_or_regional_context": ["protected_dialect_or_regional_identity", "rights_provenance"],
        "abstention": ["abstention_or_not_applicable_authority", "rights_provenance"],
        "not_applicable_with_evidence": ["abstention_or_not_applicable_authority", "rights_provenance"],
    }
    protected = record_kind == "protected_historical_context"
    coverage_stratum_id = (
        _cell_id("not_applicable_with_evidence")
        if record_kind == "not_applicable_with_evidence"
        else _protected_cell_id()
        if record_kind == "protected_historical_context"
        else _dialect_cell_id()
        if record_kind == "protected_dialect_or_regional_context"
        else _cell_id("coverage_blocked")
    )
    refs = [
        _evidence_ref(
            role,
            f"{record_kind}-{index}",
            protected=protected,
            coverage_stratum_id=coverage_stratum_id,
        )
        for index, role in enumerate(required_roles[record_kind])
    ]
    value: dict[str, Any] = {
        "record_kind": record_kind,
        "record_id": f"case:{record_kind}",
        "coverage_stratum_id": coverage_stratum_id,
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
    elif record_kind == "protected_dialect_or_regional_context":
        value.update(
            {
                "dialect_or_regional_identity": "fixture_dialect_or_regional_form",
                "region_id": "region:fixture",
                "register_id": "register:fixture",
                "source_qualified_identity": True,
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
            "input_identity_sha256": _composite_input_sha256(),
            "proposal_process_version": "phase3-p2-proposal-fixture-v1",
        },
        "input_identity_sha256": _composite_input_sha256(),
        "proposal_metadata": {
            "proposal_schema_version": "phase3_p2_proposal_metadata_v1",
            "candidate_kind": "fixture_candidate",
            "candidate_identity_sha256": SHA256,
            "coverage_stratum_id": _cell_id("not_applicable_with_evidence"),
        },
    }
    value["proposal_metadata_sha256"] = p2.sha256_bytes(p2.canonical_json(value["proposal_metadata"]))
    value["proposal_sha256"] = p2.sha256_bytes(p2.canonical_json(value))
    return value


def _rule_slot(
    *,
    coverage_stratum_id: str | None = None,
    lineage_kind: str = "root",
    parent_slot_ids: list[str] | None = None,
) -> dict[str, Any]:
    identity = {
        "coverage_stratum_id": coverage_stratum_id or _cell_id("coverage_blocked"),
        "claim_type": "fixture_claim_type",
        "source_class": "fixture_source_class",
        "identity_candidate": "fixture_identity_candidate",
        "applicability_predicate_id": "predicate:fixture",
        "evidence_set_sha256": SHA256,
        "adjudication_record_sha256": SHA256,
    }
    return {
        "rule_slot_id": "p2_rule_slot:" + p2.sha256_bytes(p2.canonical_json(identity)),
        "atomic_identity": identity,
        "lineage_kind": lineage_kind,
        "parent_slot_ids": [] if parent_slot_ids is None else parent_slot_ids,
    }


def _rule_manifest(
    slots: list[dict[str, Any]],
    *,
    version: str = "phase3_p2_rule_manifest_v1",
    parent_rule_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "manifest_version": version,
        "slots": slots,
        "rule_manifest_sha256": p2.sha256_bytes(p2.canonical_json(slots)),
    }
    if parent_rule_manifest_sha256 is not None:
        value["parent_rule_manifest_sha256"] = parent_rule_manifest_sha256
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
    assert p1_binding["dialect_regional_protection_amendment"] == {
        "path": "data/projects/open_model_data/evidence/phase3_p1_dialect_regional_protection_amendment_v1.json",
        "sha256": P1_AMENDMENT_SHA256,
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
    assert p1_binding["composite_required_cell_count"] == len(_composite_cells()) == 16
    assert p1_binding["composite_required_cell_statuses"] == [
        {"cell_id": cell["cell_id"], "status": cell["status"]}
        for cell in sorted(_composite_cells().values(), key=lambda item: item["cell_id"])
    ]
    assert p1_binding["composite_input_sha256"] == _composite_input_sha256()


def test_p2_schema_is_strict_and_the_frozen_artifact_validates() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    _validate_contract(_json(P2))


def test_dialect_regional_amendment_is_additive_versioned_and_schema_valid() -> None:
    amendment = _amendment()
    amendment_schema = json.loads(P1_AMENDMENT_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(amendment_schema)
    Draft202012Validator(amendment_schema).validate(amendment)
    assert p2.sha256_file(P1_AMENDMENT) == P1_AMENDMENT_SHA256
    assert amendment["base_p1_manifest"] == {"path": "data/projects/open_model_data/evidence/phase3_p1_universe_freeze_v1.json", "sha256": P1_SHA256}
    assert amendment["amendment"]["base_p1_rewritten"] is False
    assert amendment["amendment"]["base_required_cell_count"] == 15
    assert amendment["amendment"]["additive_required_cell_count"] == 1
    assert amendment["amendment"]["composite_required_cell_count"] == 16
    assert len(amendment["amendment"]["additive_cells"]) == 1
    cell = amendment["amendment"]["additive_cells"][0]
    assert cell == {
        "cell_id": _dialect_cell_id(),
        "context_role": "dialect_or_regional_form",
        "language_identity": "source_attested_ukrainian_dialect_or_regional_form",
        "phenomenon": "dialect_or_regional_identity",
        "protection_required": True,
        "role": "protected_dialect_or_regional",
        "status": "coverage_blocked",
    }
    assert amendment["dialect_regional_protection"] == {
        "source_qualified_identity_required": True,
        "region_required": True,
        "register_required": True,
        "dialect_or_regional_forms_protected": True,
        "modern_correction_eligible": False,
        "automatic_normalization_to_modern_standard_ukrainian": False,
        "automatic_mapping_to_modern_national_successor": False,
        "identity_or_region_unknown_route": "coverage_blocked_or_abstention",
    }
    assert amendment["safety"] == {
        "provider_calls": False,
        "labels_created": False,
        "dataset_rows_emitted": False,
        "gold_created": False,
        "training_performed": False,
    }


@pytest.mark.parametrize(
    "record_kind",
    [
        "correct_modern_production",
        "source_backed_correction",
        "minimal_contrast",
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
        "coverage_blocked",
    ],
)
def test_json_schema_accepts_each_state_specific_case_branch(record_kind: str) -> None:
    _validate_case_schema(_case(record_kind))


@pytest.mark.parametrize(
    ("record_kind", "field", "value"),
    [
        ("coverage_blocked", "authority", copy.deepcopy(AUTHORITY)),
        ("protected_historical_context", "dialect_or_regional_identity", "cross-state"),
        ("protected_dialect_or_regional_context", "historical_identity", "cross-state"),
        ("protected_dialect_or_regional_context", "source_qualified_identity", False),
        ("protected_dialect_or_regional_context", "modern_normalization", True),
        ("abstention", "not_applicable_evidence_id", "cross-state"),
        ("not_applicable_with_evidence", "abstention_reason_code", "cross-state"),
        ("correct_modern_production", "modern_normalization", False),
    ],
)
def test_json_schema_rejects_cross_state_case_fields(
    record_kind: str, field: str, value: Any
) -> None:
    record = _case(record_kind)
    record[field] = value
    with pytest.raises(ValidationError):
        _validate_case_schema(record)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ({"amendment": {"base_p1_rewritten": True}}, "p1_dialect_regional_amendment_sha_drift"),
        ({"amendment": {"composite_required_cell_count": 15}}, "p1_dialect_regional_amendment_sha_drift"),
        ({"dialect_regional_protection": {"automatic_normalization_to_modern_standard_ukrainian": True}}, "p1_dialect_regional_amendment_sha_drift"),
    ],
)
def test_amendment_mutation_cannot_rewrite_the_composite_denominator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict[str, Any],
    error: str,
) -> None:
    value = _amendment()
    section, field_value = next(iter(mutation.items()))
    value[section].update(copy.deepcopy(field_value))
    mutated = tmp_path / "dialect-amendment-mutated.json"
    _write_json(mutated, value)
    monkeypatch.setattr(p2, "P1_DIALECT_REGIONAL_AMENDMENT", mutated)
    with pytest.raises(ValueError, match=error):
        p2.build_contract()


def test_r_is_empty_until_source_qualified_rule_admission_and_is_hash_bound() -> None:
    rule_universe = _contract()["rule_slot_universe"]
    assert rule_universe["symbol"] == "R"
    assert rule_universe["coverage_strata_are_rules"] is False
    assert rule_universe["slot_count"] == 0
    assert rule_universe["slots"] == []
    assert rule_universe["rule_manifest_sha256"] == p2.sha256_bytes(p2.canonical_json([]))

    algorithm = rule_universe["algorithm"]
    unsigned_algorithm = {key: value for key, value in algorithm.items() if key != "algorithm_sha256"}
    assert algorithm["input_composite_manifest_sha256"] == _composite_input_sha256()
    assert algorithm["atomic_identity_fields"] == list(p2.RULE_SLOT_IDENTITY_FIELDS)
    assert algorithm["admission_requirements"] == [
        "source_qualified_claim_typed_evidence",
        "registered_qualified_human_adjudication",
        "immutable_adjudication_record_sha256",
        "unique_canonical_rule_slot_id",
    ]
    assert algorithm["slot_id_rule"] == "p2_rule_slot:sha256_canonical_atomic_identity"
    assert algorithm["algorithm_sha256"] == p2.sha256_bytes(p2.canonical_json(unsigned_algorithm))
    assert "p1_cells_are_coverage_strata_not_rules" in algorithm["derivation"]


def test_r_merge_split_and_denominator_changes_are_versioned_and_fail_closed() -> None:
    rule_universe = _contract()["rule_slot_universe"]
    assert rule_universe["merge_criteria"] == {
        "permitted": True,
        "requires": [
            "source_qualified_claim_typed_evidence",
            "registered_qualified_human_adjudication",
            "all_parent_slot_ids",
        ],
        "preserves": ["coverage_stratum_id", "case_denominator", "atomic_identity_lineage"],
        "version_effect": "new_rule_manifest_version_with_all_parent_lineage",
    }
    assert rule_universe["split_criteria"] == {
        "permitted": True,
        "requires": [
            "source_qualified_claim_typed_evidence",
            "registered_qualified_human_adjudication",
            "parent_slot_id",
        ],
        "preserves": ["coverage_stratum_id", "case_denominator", "atomic_identity_lineage"],
        "version_effect": "new_rule_manifest_version_with_parent_child_lineage",
    }
    assert rule_universe["denominator_change_policy"] == "new_p1_manifest_sha256_and_new_dataset_version_required"


def test_composite_strata_and_adjudication_registry_are_explicitly_non_admitting() -> None:
    contract = _contract()
    assert contract["p1_binding"]["required_cell_count"] == 15
    assert contract["p1_binding"]["composite_required_cell_count"] == 16
    assert len(contract["p1_binding"]["composite_required_cell_statuses"]) == 16
    assert next(
        status
        for status in contract["p1_binding"]["composite_required_cell_statuses"]
        if status["cell_id"] == _dialect_cell_id()
    )["status"] == "coverage_blocked"
    assert contract["case_state_contract"]["structurally_distinct_states"] == [
        "correct_modern_production",
        "source_backed_correction",
        "minimal_contrast",
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
        "coverage_blocked",
    ]
    assert contract["case_state_contract"]["protected_dialect_or_regional_is_not_modern_correction"] is True
    assert contract["adjudication_contract"] == {
        "registry_status": "FROZEN_NONADMITTING",
        "semantic_case_admission_permitted": False,
        "required_adjudicator_qualification": {
            "authority_kind": "source_qualified_human_adjudication",
            "actor_kind": "human",
            "qualification_status": "registered_source_qualified_human",
        },
        "required_adjudication_record": {
            "record_identity_rule": "sha256_canonical_adjudication_metadata",
            "record_sha256_required": True,
            "evidence_ref_ids_bound": True,
            "source_qualified_identity_bound": True,
        },
        "adjudication_registry_sha256": None,
    }


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("p1_binding", "source_unit_count"), 56),
        (("p1_binding", "unknown_rights_blocker_count"), 38),
        (("p1_binding", "required_cell_count"), 14),
        (("p1_binding", "composite_required_cell_count"), 15),
        (("p1_binding", "composite_input_sha256"), SHA256),
        (("rule_slot_universe", "slot_count"), 1),
        (("rule_slot_universe", "coverage_strata_are_rules"), True),
        (("rule_slot_universe", "rule_manifest_sha256"), SHA256),
        (("rule_slot_universe", "algorithm"), {"forged": True}),
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


def test_atomic_rule_slot_identity_is_structured_and_canonical() -> None:
    contract = _contract()
    slot = _rule_slot()
    identity = slot["atomic_identity"]
    assert set(identity) == set(p2.RULE_SLOT_IDENTITY_FIELDS)
    assert slot["rule_slot_id"] == "p2_rule_slot:" + p2.sha256_bytes(p2.canonical_json(identity))
    assert slot["lineage_kind"] == "root"
    assert slot["parent_slot_ids"] == []
    assert p2.validate_rule_slot_identity(slot, contract) is True
    assert contract["rule_slot_universe"]["slots"] == []
    assert contract["rule_slot_universe"]["rule_manifest_sha256"] == p2.sha256_bytes(p2.canonical_json([]))


@pytest.mark.parametrize(
    ("lineage_kind", "parent_slot_ids"),
    [
        ("split_child", ["p2_rule_slot:" + SHA256]),
        ("merge", ["p2_rule_slot:" + SHA256, "p2_rule_slot:" + ("b" * 64)]),
    ],
)
def test_atomic_rule_slot_identity_accepts_structurally_valid_lineage(
    lineage_kind: str, parent_slot_ids: list[str]
) -> None:
    assert p2.validate_rule_slot_identity(
        _rule_slot(lineage_kind=lineage_kind, parent_slot_ids=parent_slot_ids), _contract()
    ) is True


@pytest.mark.parametrize(
    "mutation",
    [
        lambda slot: slot.update({"rule_slot_id": "p2_rule_slot:" + SHA256}),
        lambda slot: slot["atomic_identity"].update({"source_class": ""}),
        lambda slot: slot["atomic_identity"].update({"identity_candidate": ""}),
        lambda slot: slot["atomic_identity"].update({"evidence_set_sha256": SHA256.upper()}),
        lambda slot: slot["atomic_identity"].update({"adjudication_record_sha256": "not-a-sha"}),
        lambda slot: slot["atomic_identity"].update({"unexpected": "must-fail"}),
        lambda slot: slot.update({"lineage_kind": "root", "parent_slot_ids": ["p2_rule_slot:" + SHA256]}),
        lambda slot: slot.update({"lineage_kind": "split_child", "parent_slot_ids": []}),
        lambda slot: slot.update({"lineage_kind": "merge", "parent_slot_ids": ["p2_rule_slot:" + SHA256]}),
    ],
)
def test_atomic_rule_slot_identity_mutations_fail_closed(mutation: Any) -> None:
    slot = _rule_slot()
    mutation(slot)
    assert p2.validate_rule_slot_identity(slot, _contract()) is False


def test_rule_manifest_evolution_requires_exact_version_hash_and_lineage() -> None:
    contract = _contract()
    previous = _rule_manifest([])
    slot = _rule_slot()
    next_manifest = _rule_manifest(
        [slot],
        version="phase3_p2_rule_manifest_v2",
        parent_rule_manifest_sha256=previous["rule_manifest_sha256"],
    )
    assert p2.validate_rule_manifest_evolution(previous, next_manifest, contract) is True

    duplicate = copy.deepcopy(next_manifest)
    duplicate["slots"].append(copy.deepcopy(slot))
    duplicate["rule_manifest_sha256"] = p2.sha256_bytes(p2.canonical_json(duplicate["slots"]))
    assert p2.validate_rule_manifest_evolution(previous, duplicate, contract) is False

    collision = copy.deepcopy(next_manifest)
    changed_identity = collision["slots"][0]["atomic_identity"]
    changed_identity["claim_type"] = "fixture_other_claim_type"
    collision["slots"][0]["rule_slot_id"] = slot["rule_slot_id"]
    collision["rule_manifest_sha256"] = p2.sha256_bytes(p2.canonical_json(collision["slots"]))
    assert p2.validate_rule_manifest_evolution(previous, collision, contract) is False

    for field, replacement in (
        ("manifest_version", "phase3_p2_rule_manifest_v1"),
        ("parent_rule_manifest_sha256", SHA256),
        ("rule_manifest_sha256", SHA256),
    ):
        mutated = copy.deepcopy(next_manifest)
        mutated[field] = replacement
        assert p2.validate_rule_manifest_evolution(previous, mutated, contract) is False

    child = _rule_slot(lineage_kind="split_child", parent_slot_ids=["p2_rule_slot:" + SHA256])
    child_manifest = _rule_manifest(
        [child],
        version="phase3_p2_rule_manifest_v2",
        parent_rule_manifest_sha256=previous["rule_manifest_sha256"],
    )
    assert p2.validate_rule_manifest_evolution(previous, child_manifest, contract) is False


def test_empty_rule_manifest_can_resume_only_as_the_exact_empty_manifest() -> None:
    contract = _contract()
    previous = _rule_manifest([])
    empty_next = _rule_manifest(
        [],
        version="phase3_p2_rule_manifest_v2",
        parent_rule_manifest_sha256=previous["rule_manifest_sha256"],
    )
    assert p2.validate_rule_manifest_evolution(previous, empty_next, contract) is True
    assert p2.validate_rule_manifest_evolution([], [], contract) is False
    assert p2.validate_rule_manifest_evolution(previous, {"slots": []}, contract) is False


@pytest.mark.parametrize(
    "field",
    [
        "source_class",
        "identity_candidate",
        "coverage_stratum_id",
        "source_unit_identity_sha256",
        "source_artifact_sha256",
        "provenance_sha256",
    ],
)
def test_case_evidence_refs_pin_source_identity_artifact_and_provenance(field: str) -> None:
    record = _case("not_applicable_with_evidence")
    record["evidence_refs"][0][field] = (
        SHA256
        if field.endswith("sha256")
        else "source-class:forged"
        if field == "source_class"
        else "identity-candidate:forged"
        if field == "identity_candidate"
        else _cell_id("coverage_blocked")
    )
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
    "mutation",
    [
        {"authority": {"authority_kind": "self_asserted_adjudication"}},
        {"evidence_refs": [{"source_class": "mismatched-source-class"}]},
        {"evidence_refs": [{"identity_candidate": "mismatched-identity-candidate"}]},
    ],
)
def test_semantic_cases_reject_self_asserted_or_mismatched_source_identity(
    mutation: dict[str, Any],
) -> None:
    record = _case("not_applicable_with_evidence")
    if "authority" in mutation:
        record["authority"].update(mutation["authority"])
    else:
        record["evidence_refs"][0].update(mutation["evidence_refs"][0])
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind",
    [
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
        "coverage_blocked",
    ],
)
def test_protected_abstention_na_and_coverage_blocked_are_distinct_states(record_kind: str) -> None:
    record = _case(record_kind)
    if record_kind == "coverage_blocked":
        assert p2.validate_case_record(record) is True
    else:
        # The adjudication registry is deliberately FROZEN_NONADMITTING.  A
        # caller-supplied human-shaped object cannot turn any semantic state
        # into an admitted case, including the additive dialect protection
        # state.
        assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind",
    [
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
    ],
)
def test_semantic_case_roles_remain_blocked_even_with_a_satisfied_p1_stratum(
    record_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if record_kind != "protected_dialect_or_regional_context":
        monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    assert p2.validate_case_record(_case(record_kind)) is False


@pytest.mark.parametrize(
    ("record_kind", "mutation"),
    [
        ("protected_historical_context", {"modern_normalization": True}),
        ("protected_historical_context", {"historical_identity": "modern_standard_ukrainian"}),
        ("protected_historical_context", {"period_id": ""}),
        ("protected_historical_context", {"rule_slot_id": "p2_rule_slot:" + SHA256}),
        ("protected_dialect_or_regional_context", {"modern_normalization": True}),
        ("protected_dialect_or_regional_context", {"source_qualified_identity": False}),
        ("protected_dialect_or_regional_context", {"region_id": ""}),
        ("protected_dialect_or_regional_context", {"historical_identity": "forbidden-cross-state-field"}),
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
        ("protected_dialect_or_regional_context", "protected_historical_identity"),
        ("abstention", "protected_historical_identity"),
        ("not_applicable_with_evidence", "correction_authority"),
    ],
)
def test_case_evidence_roles_are_claim_appropriate(
    record_kind: str, wrong_role: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "protected_dialect_or_regional_context", "abstention"}:
        monkeypatch.setattr(p2, "read_p1", lambda: _satisfied_p1_for(record_kind))
    _set_evidence_roles(record, [wrong_role, "rights_provenance"])
    assert p2.validate_case_record(record) is False


@pytest.mark.parametrize(
    "record_kind",
    [
        "protected_historical_context",
        "protected_dialect_or_regional_context",
        "abstention",
        "not_applicable_with_evidence",
    ],
)
def test_case_evidence_requires_a_non_attestation_claim_role(
    record_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _case(record_kind)
    if record_kind in {"protected_historical_context", "protected_dialect_or_regional_context", "abstention"}:
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


def test_protected_dialect_cannot_be_laundered_as_historical_or_modern_state() -> None:
    record = _case("protected_dialect_or_regional_context")
    record["record_kind"] = "protected_historical_context"
    assert p2.validate_case_record(record) is False

    record = _case("protected_dialect_or_regional_context")
    record["record_kind"] = "correct_modern_production"
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


def test_proposal_binds_the_pinned_composite_input_not_the_base_p1_only() -> None:
    contract = _contract()
    proposal = _proposal()
    assert proposal["input_identity_sha256"] == contract["p1_binding"]["composite_input_sha256"]
    assert proposal["producer_provenance"]["input_identity_sha256"] == proposal["input_identity_sha256"]
    assert p2.validate_promotion(proposal, _promotion(proposal), contract) is True

    for replacement in (P1_SHA256, SHA256):
        mutated = copy.deepcopy(proposal)
        mutated["input_identity_sha256"] = replacement
        mutated["producer_provenance"]["input_identity_sha256"] = replacement
        mutated["proposal_sha256"] = p2.sha256_bytes(p2.canonical_json({key: value for key, value in mutated.items() if key != "proposal_sha256"}))
        assert p2.validate_promotion(mutated, _promotion(mutated), contract) is False


@pytest.mark.parametrize("field", ["input_identity_sha256", "proposal_metadata_sha256", "proposal_sha256"])
def test_proposal_digest_fields_require_lowercase_hex(field: str) -> None:
    proposal = _proposal()
    if field == "input_identity_sha256":
        proposal[field] = proposal[field].upper()
        proposal["producer_provenance"]["input_identity_sha256"] = proposal[field]
    elif field == "proposal_metadata_sha256":
        proposal[field] = proposal[field].upper()
    else:
        proposal[field] = proposal[field].upper()
    if field != "proposal_sha256":
        proposal["proposal_sha256"] = p2.sha256_bytes(
            p2.canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"})
        )
    assert p2.validate_promotion(proposal, _promotion(proposal), _contract()) is False


@pytest.mark.parametrize(
    ("nested_path", "replacement"),
    [
        (("proposal_metadata", "candidate_identity_sha256"), SHA256.upper()),
        (("producer_provenance", "run_identity_sha256"), SHA256.upper()),
        (("producer_provenance", "run_identity_sha256"), "not-a-sha256"),
    ],
)
def test_proposal_nested_metadata_and_provenance_hashes_are_lowercase_hex(
    nested_path: tuple[str, str], replacement: str
) -> None:
    proposal = _proposal()
    proposal[nested_path[0]][nested_path[1]] = replacement
    proposal["proposal_metadata_sha256"] = p2.sha256_bytes(p2.canonical_json(proposal["proposal_metadata"]))
    proposal["proposal_sha256"] = p2.sha256_bytes(
        p2.canonical_json({key: value for key, value in proposal.items() if key != "proposal_sha256"})
    )
    assert p2.validate_promotion(proposal, _promotion(proposal), _contract()) is False


@pytest.mark.parametrize("decision", ["accepted", "admitted", "gold", "target"])
def test_proposals_cannot_promote_to_targets(decision: str) -> None:
    proposal = _proposal()
    assert p2.validate_promotion(proposal, _promotion(proposal, decision=decision), _contract()) is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"proposal_sha256": SHA256},
        {"proposal_metadata_sha256": SHA256},
        {"proposal_metadata": {"source_text": "forbidden"}},
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
