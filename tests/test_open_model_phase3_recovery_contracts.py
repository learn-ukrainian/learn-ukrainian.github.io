"""Focused fail-closed tests for the Phase 3 recovery pre-extraction freeze."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_recovery_contracts as contracts

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
EVIDENCE = ROOT / "data/projects/open_model_data/evidence"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def _isolated_root(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    target.mkdir()
    destination = target / "data/projects/open_model_data"
    destination.parent.mkdir(parents=True)
    shutil.copytree(CONTRACTS, destination / "contracts")
    shutil.copytree(EVIDENCE, destination / "evidence")
    implementation = target / contracts.NEAR_DUPLICATE_IMPLEMENTATION_MODULE
    implementation.parent.mkdir(parents=True)
    shutil.copy2(ROOT / contracts.NEAR_DUPLICATE_IMPLEMENTATION_MODULE, implementation)
    return target


def _install_synthetic_binding_inputs(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    batch_state = root / "batch_state"
    batch_state.mkdir()
    prompt = batch_state / "phase3-recovery-prompt-v1.md"
    amendment = batch_state / "phase3-recovery-scope-amendment-v3.md"
    prompt.write_bytes(b"synthetic reviewed prompt\n")
    amendment.write_bytes(b"synthetic reviewed amendment\n")
    prompt_hash = contracts.sha256_file(prompt)
    amendment_hash = contracts.sha256_file(amendment)
    combined_hash = hashlib.sha256(prompt.read_bytes() + b"\n---\n" + amendment.read_bytes()).hexdigest()
    monkeypatch.setattr(contracts, "PROMPT_HASH", prompt_hash)
    monkeypatch.setattr(contracts, "AMENDMENT_HASH", amendment_hash)
    monkeypatch.setattr(contracts, "COMBINED_HASH", combined_hash)
    for name in contracts.ARTIFACT_NAMES:
        path, artifact = _artifact(root, name)
        artifact["contract_inputs"] = {
            "original_prompt_sha256": prompt_hash,
            "scope_amendment_sha256": amendment_hash,
            "combined_contract_sha256": combined_hash,
        }
        _write_json(path, artifact)
    return prompt, amendment


def _artifact(root: Path, name: str) -> tuple[Path, dict[str, Any]]:
    path = root / "data/projects/open_model_data/evidence" / name
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_contract_freeze_positive_cli_and_schema_meta_validation(capsys: pytest.CaptureFixture[str]) -> None:
    assert contracts.main(["--repo-root", str(ROOT)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {
        "artifacts": list(contracts.ARTIFACT_NAMES),
        "local_binding_inputs_verified": contracts.locate_shared_batch_state(ROOT) is not None,
        "ok": True,
        "schema_version": "phase3_recovery_contract_validator_v1",
    }
    for name in contracts.SCHEMA_NAMES:
        Draft202012Validator.check_schema(json.loads((CONTRACTS / name).read_text(encoding="utf-8")))


def test_denominator_shrinkage_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    next(item for item in coverage["mandatory_families"] if item["family_id"] == "ua_gec")["input_identity"]["observed_input_total"] = 8936
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="denominator shrunk: ua_gec"):
        contracts.validate_contracts(root)


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        ("pravopys_2026_authority", "official_download_locator", "https://example.invalid/2026.pdf"),
        ("edition_alignment", "pravopys_2019_official_pdf_sha256", "0" * 64),
        ("edition_alignment", "pravopys_2019_official_provenance_verified", False),
    ],
)
def test_verified_pravopys_acquisition_identity_drift_fails_closed(
    tmp_path: Path, section: str, field: str, replacement: object,
) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage[section][field] = replacement
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_source_audit_formula_weakening_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["mandatory_families"][9]["audit"]["converted_formula"] = "min(converted_total,1)"
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_mandatory_family_identity_reuse_fails_schema_only(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["mandatory_families"][1]["family_id"] = coverage["mandatory_families"][0]["family_id"]
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_missing_matrix_cell_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["release_category_matrix"]["phenomena"].pop()
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_near_duplicate_threshold_change_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["near_duplicate_policy"]["numeric_thresholds"]["near_duplicate_minimum"] = 0.89
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_near_duplicate_implementation_is_exactly_bound_to_its_pinned_artifact(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    _, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    policy = evaluation["near_duplicate_policy"]
    assert policy["implementation_version"] == contracts.NEAR_DUPLICATE_IMPLEMENTATION_VERSION
    assert policy["implementation_module"] == contracts.NEAR_DUPLICATE_IMPLEMENTATION_MODULE
    assert policy["implementation_artifact"] == contracts.NEAR_DUPLICATE_POLICY_ARTIFACT
    assert policy["policy_fingerprint_sha256"] == contracts.NEAR_DUPLICATE_POLICY_FINGERPRINT
    assert contracts.validate_contracts(root)["ok"] is True


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("implementation_version", "implementation_pending"),
        ("implementation_module", "scripts/projects/open_model_data/drift.py"),
        ("implementation_artifact", "data/projects/open_model_data/evidence/drift.json"),
        ("policy_fingerprint_sha256", "0" * 64),
    ],
)
def test_near_duplicate_implementation_binding_drift_fails_closed(
    tmp_path: Path, field: str, replacement: str
) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["near_duplicate_policy"][field] = replacement
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_near_duplicate_policy_artifact_content_drift_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    artifact_path = root / contracts.NEAR_DUPLICATE_POLICY_ARTIFACT
    policy_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    policy_artifact["implementation"]["module"] = "scripts/projects/open_model_data/drift.py"
    fingerprint_input = dict(policy_artifact)
    fingerprint_input.pop("policy_fingerprint_sha256")
    policy_artifact["policy_fingerprint_sha256"] = hashlib.sha256(
        (contracts.canonical_json(fingerprint_input) + "\n").encode("utf-8")
    ).hexdigest()
    _write_json(artifact_path, policy_artifact)
    with pytest.raises(contracts.ContractError, match="near-duplicate policy artifact fingerprint drift"):
        contracts.validate_contracts(root)


@pytest.mark.parametrize("mutation", ["role_reuse", "root_assignment"])
def test_role_reuse_and_root_assignment_fail_closed(tmp_path: Path, mutation: str) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    if mutation == "role_reuse":
        roles["seats"][1]["seat_id"] = roles["seats"][0]["seat_id"]
    else:
        roles["root"]["decision_role_ids"] = ["scorer"]
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_weakened_per_phenomenon_threshold_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["per_phenomenon_gate"]["precision_minimum"] = 0.97
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_wrong_current_2026_hash_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["pravopys_2026_authority"]["official_pdf_sha256"] = "0" * 64
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_present_hash_on_nonfrozen_universe_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["mandatory_families"][0]["input_identity"]["universe_sha256"] = "a" * 64
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_2026_paragraph_extent_cannot_be_ledger_input_total(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    next(item for item in coverage["mandatory_families"] if item["family_id"] == "pravopys_2026_complete")["input_identity"]["observed_input_total"] = 168
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="2026 paragraph extent misused"):
        contracts.validate_contracts(root)


def test_lexical_disposition_mode_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    next(item for item in coverage["mandatory_families"] if item["family_id"] == "lexical_vesum")["coverage_mode"] = "source_conversion"
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


@pytest.mark.parametrize("field", ["audit", "scanner_nonhit_audit"])
def test_both_textbook_audits_are_required(tmp_path: Path, field: str) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    textbook = next(item for item in coverage["mandatory_families"] if item["family_id"] == "school_textbooks")
    del textbook[field]
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_stale_ulif_counts_fail_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    next(item for item in coverage["mandatory_families"] if item["family_id"] == "lexical_ulif")["input_identity"]["observed_input_total"] = 7
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="denominator shrunk: lexical_ulif"):
        contracts.validate_contracts(root)


@pytest.mark.parametrize("field", ["matcher_mechanisms", "breadth_floors"])
def test_mechanism_and_breadth_freezes_are_required(tmp_path: Path, field: str) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    del evaluation[field]
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_automatic_category_floor_cannot_drop_below_four(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["breadth_floors"]["automatic_categories_minimum"] = 3
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_combined_contract_hash_is_recomputed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _isolated_root(tmp_path)
    _, amendment = _install_synthetic_binding_inputs(root, monkeypatch)
    amendment.write_text(amendment.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
    mutated_hash = contracts.sha256_file(amendment)
    monkeypatch.setattr(contracts, "AMENDMENT_HASH", mutated_hash)
    for name in contracts.ARTIFACT_NAMES:
        path, artifact = _artifact(root, name)
        artifact["contract_inputs"]["scope_amendment_sha256"] = mutated_hash
        _write_json(path, artifact)
    with pytest.raises(contracts.ContractError, match="combined binding input hash mismatch"):
        contracts.validate_contracts(root)


def test_clean_checkout_validates_committed_hash_receipt_without_local_inputs(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    result = contracts.validate_contracts(root)
    assert result["ok"] is True
    assert result["local_binding_inputs_verified"] is False


def test_unrelated_runtime_batch_state_is_not_a_partial_binding_set(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    batch_state = root / "batch_state"
    batch_state.mkdir()
    (batch_state / "runtime.json").write_text("{}\n", encoding="utf-8")
    result = contracts.validate_contracts(root)
    assert result["ok"] is True
    assert result["local_binding_inputs_verified"] is False


def test_partial_local_binding_state_returns_json_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _isolated_root(tmp_path)
    batch_state = root / "batch_state"
    batch_state.mkdir()
    (batch_state / "phase3-recovery-prompt-v1.md").write_text("partial\n", encoding="utf-8")
    assert contracts.main(["--repo-root", str(root)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False
    assert "binding input" in result["error"]


def test_all_roles_unlaunched_lie_fails_closed(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    for binding in roles["task_bindings"]:
        binding["status"] = "reserved_not_launched"
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match=r"schema violation|approved contract-text review binding changed"):
        contracts.validate_contracts(root)


def test_newly_attested_roles_have_only_their_accepted_bindings(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    roles = _artifact(root, "correction_protection_role_contract_v1.json")[1]
    expected = {
        "rule_author_extractor": ("phase3-role-rule-author-agy-v3", "controller_phase3_rule_author_agy_runtime_01"),
        "heldout_steward": ("phase3-role-heldout-steward-cursor-v2", "controller_phase3_heldout_steward_cursor_runtime_01"),
        "heldout_label_reviewer": ("phase3-role-label-reviewer-codex-v2", "controller_phase3_heldout_label_reviewer_codex_runtime_01"),
    }
    bindings = {binding["role_id"]: binding for binding in roles["task_bindings"]}
    seats = {seat["role_id"]: seat for seat in roles["seats"]}
    for role_id, (task_id, controller_identity_id) in expected.items():
        assert seats[role_id]["assignment_state"] == "assigned_verified"
        assert seats[role_id]["controller_identity_id"] == controller_identity_id
        assert seats[role_id]["controller_identity_attested"] is True
        assert bindings[role_id] == {
            "role_id": role_id,
            "reserved_task_id": task_id,
            "controller_identity_id": controller_identity_id,
            "status": "identity_attested_pre_artifact",
            "artifact_approval_claimed": False,
            "program_completion_claimed": False,
        }
    assert contracts.validate_contracts(root)["ok"] is True


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("reserved_task_id", "phase3-role-drift"),
        ("controller_identity_id", "controller_phase3_drift_01"),
        ("status", "combined_contract_text_approved_pre_artifact"),
    ],
)
@pytest.mark.parametrize("role_id", ("rule_author_extractor", "heldout_steward", "heldout_label_reviewer"))
def test_newly_attested_role_binding_cannot_drift(
    tmp_path: Path, field: str, replacement: str, role_id: str
) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    next(binding for binding in roles["task_bindings"] if binding["role_id"] == role_id)[field] = replacement
    if field == "controller_identity_id":
        next(seat for seat in roles["seats"] if seat["role_id"] == role_id)[field] = replacement
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match=r"attested decision role binding changed|attested decision seat controller identity changed"):
        contracts.validate_contracts(root)


def test_remaining_reserved_roles_cannot_be_activated_without_attestation(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    seats = {seat["role_id"]: seat for seat in roles["seats"]}
    bindings = {binding["role_id"]: binding for binding in roles["task_bindings"]}
    reserved_roles = {
        "scorer",
        "outsider_reproducer",
        "cross_family_code_infra_reviewer",
        "disposition_auditor",
        "textbook_nonhit_auditor",
    }
    for role_id in reserved_roles:
        assert seats[role_id]["assignment_state"] == "reserved_unassigned"
        assert seats[role_id]["controller_identity_id"] is None
        assert bindings[role_id]["status"] == "reserved_not_launched"
    seats["scorer"].update({
        "assignment_state": "assigned_verified",
        "controller_identity_id": "controller_phase3_scorer_01",
        "controller_identity_attested": True,
    })
    bindings["scorer"].update({
        "controller_identity_id": "controller_phase3_scorer_01",
        "status": "identity_attested_pre_artifact",
    })
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="unlaunched decision seat claims a controller identity"):
        contracts.validate_contracts(root)


def test_artifact_review_cannot_self_seal(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    roles["task_bindings"][0]["artifact_approval_claimed"] = True
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


def test_controller_identity_cannot_hold_two_decision_roles(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    roles["seats"][1]["controller_identity_id"] = roles["seats"][0]["controller_identity_id"]
    roles["task_bindings"][1]["controller_identity_id"] = roles["task_bindings"][0]["controller_identity_id"]
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="one durable controller identity assigned to multiple decision roles"):
        contracts.validate_contracts(root)


def test_task_binding_must_match_durable_seat_identity(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    roles["task_bindings"][0]["controller_identity_id"] = "controller_wrong_identity"
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="task binding controller identity differs from decision seat"):
        contracts.validate_contracts(root)


def test_root_controller_identity_cannot_hold_decision_role(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    root_identity = roles["root"]["controller_identity_id"]
    roles["seats"][0]["controller_identity_id"] = root_identity
    roles["task_bindings"][0]["controller_identity_id"] = root_identity
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="root controller identity assigned a decision role"):
        contracts.validate_contracts(root)


def test_ledger_audit_identity_contract_cannot_weaken(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["ledger_audit_identity_contract"]["required_equalities"].pop()
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError):
        contracts.validate_contracts(root)


@pytest.mark.parametrize(
    ("contract_key", "field"),
    [
        ("audit_seed_independence_contract", "author_roles_forbidden_from_seed_proposal_filter_search_or_reroll"),
        ("audit_result_acceptance_contract", "pravopys_delta_zero_nonagree_required"),
    ],
)
def test_audit_independence_and_zero_miss_contracts_cannot_weaken(
    tmp_path: Path, contract_key: str, field: str
) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage[contract_key][field] = False
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_lexical_family_cannot_use_source_disposition_audit(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    lexical = next(item for item in coverage["mandatory_families"] if item["family_id"] == "lexical_vesum")
    source = next(item for item in coverage["mandatory_families"] if item["family_id"] == "ua_gec")
    lexical["audit"] = source["audit"]
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_nonlexical_family_cannot_claim_lexical_coverage_mode(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    source = next(item for item in coverage["mandatory_families"] if item["family_id"] == "ua_gec")
    source["coverage_mode"] = "lexical_structural_and_used_subset"
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_delta_zero_miss_and_fresh_sample_rules_cannot_weaken(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, coverage = _artifact(root, "correction_protection_coverage_contract_v1.json")
    coverage["edition_alignment"]["delta_audit"]["repair_requires_new_freeze_and_sample"] = False
    _write_json(path, coverage)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


def test_forbidden_heldout_acl_cannot_shrink_schema_only(tmp_path: Path) -> None:
    root = _isolated_root(tmp_path)
    path, roles = _artifact(root, "correction_protection_role_contract_v1.json")
    roles["heldout_acl"]["forbidden_roles"].pop()
    _write_json(path, roles)
    with pytest.raises(contracts.ContractError, match="schema violation"):
        contracts.validate_contracts(root)


@pytest.mark.parametrize("admitted", ["phase2_metadata_rows", "public_authored_canaries"])
def test_phase2_and_canary_denominator_admission_fails_closed(tmp_path: Path, admitted: str) -> None:
    root = _isolated_root(tmp_path)
    path, evaluation = _artifact(root, "correction_protection_evaluation_contract_v1.json")
    evaluation["excluded_denominators"].remove(admitted)
    _write_json(path, evaluation)
    with pytest.raises(contracts.ContractError, match=r"schema violation|Phase 2 or canary denominator admitted"):
        contracts.validate_contracts(root)
