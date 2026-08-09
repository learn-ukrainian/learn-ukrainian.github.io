"""Hermetic tests for the text-free Phase 3 disposition audit primitives."""

from __future__ import annotations

import json
import subprocess
import tracemalloc
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_disposition_audit as audit
from scripts.projects.open_model_data import phase3_lexical_coverage as lexical


def _token(value: str) -> str:
    return value * 64


def _git_token(value: str) -> str:
    return value * 40


def _coverage() -> dict[str, Any]:
    return {"text_free": True, "mandatory_families": [{"family_id": "fixture_source", "audit": {
        "auditor_role_id": "disposition_auditor", "seed_owner_role_id": "disposition_auditor",
        "nonconverted_formula": "min(nonconverted_total,max(100,ceil(0.02*family_unit_total)))",
        "converted_formula": "min(converted_total,max(100,ceil(0.02*family_unit_total)))",
        "nonconverted_stratification": ["disposition_code", "document_or_edition_identity"],
        "converted_stratification": ["source_role", "claim_type", "document_or_edition_identity"],
        "sampling_without_replacement": True,
        "nonconverted_decision_codes": ["agree", "disagree_should_be_converted", "disagree_wrong_code", "insufficient_locator_evidence"],
        "converted_miss_codes": ["disagree_stub_conversion", "disagree_misclassified_role_or_claim", "disagree_unsupported_evidence", "disagree_non_actionable_rule"],
        "repair_invalidates_both_samples": True, "passing_sample_reuse_forbidden": True,
    }}]}


def _roles() -> dict[str, Any]:
    return json.loads(audit.DEFAULT_ROLE_CONTRACT.read_text(encoding="utf-8"))


def _bindings(roles: dict[str, Any]) -> dict[str, str]:
    return audit._current_contract_bindings(roles, role_contract_path=audit.DEFAULT_ROLE_CONTRACT)


def _ledger(coverage: dict[str, Any], roles: dict[str, Any], unit_ids: list[str]) -> dict[str, Any]:
    units = [{"unit_id": unit_id, "unit_sha256": audit.sha256_value({"unit_id": unit_id}), "unit_locator_sha256": audit.sha256_value({"locator": unit_id})} for unit_id in unit_ids]
    family_hash = audit.source_family_universe_sha256(units)
    rows = [
        {
            "unit_id": unit_id,
            "unit_sha256": units[index]["unit_sha256"], "unit_locator_sha256": units[index]["unit_locator_sha256"],
            "disposition_code": "converted" if index % 2 else "not_rule_bearing",
            "document_or_edition_identity": f"edition_{index % 2}",
            "source_role": "rule_source" if index % 2 else None,
            "claim_type": "claim" if index % 2 else None,
            "canonical_content_identity": "content_fixture" if index % 2 else None,
            "evidence_artifact_locators": ["artifact_fixture"] if index % 2 else [],
            "consumer_view_ids": ["view_fixture"] if index % 2 else [],
            "conversion_predicate_locator": "predicate_fixture" if index % 2 else None,
            "reason_locator": None if index % 2 else "reason_fixture",
            "repeated_reason_count": None if index % 2 else 4,
            "predicate_or_rationale_locator": None,
        }
        for index, unit_id in enumerate(unit_ids)
    ]
    total = len(unit_ids)
    return {
        "schema_version": "phase3_disposition_ledger_v2_1", "text_free": True,
        "source_universe_receipt_sha256": _token("a"), "source_universe_payload_manifest_sha256": _token("b"),
        "coverage_contract_sha256": audit.sha256_value(coverage),
        **{key: _bindings(roles)[key] for key in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )},
        "repair_generation": 0,
        "families": [{
            "family_id": "fixture_source", "frozen_input_identity_total": total, "family_unit_total": total,
            "ledger_input_total": total, "disposition_row_sum": total, "ledger_universe_sha256": family_hash,
            "audit_universe_sha256": family_hash, "rows": rows,
        }],
    }


@pytest.fixture
def frozen(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    coverage, roles = _coverage(), _roles()
    unit_ids = [f"unit.fixture.{index:03d}" for index in range(8)]
    source_receipt = {"artifact_manifest": {"payload_manifest_sha256": _token("b")}}
    units = [{"unit_id": unit_id, "unit_sha256": audit.sha256_value({"unit_id": unit_id}), "unit_locator_sha256": audit.sha256_value({"locator": unit_id})} for unit_id in unit_ids]
    monkeypatch.setattr(audit, "_source_receipt", lambda _: (source_receipt, _token("a"), {"fixture_source": units}))
    monkeypatch.setattr(audit, "_first_containing_squash_merge", lambda *args, **kwargs: _git_token("f"))
    ledger = _ledger(coverage, roles, unit_ids)
    return ledger, coverage, roles


def _seed(freeze: dict[str, Any], roles: dict[str, Any], family_id: str = "fixture_source", population_kind: str = "nonconverted", **changes: object) -> dict[str, Any]:
    population = next(item for item in freeze["families"] if item["family_id"] == family_id)[population_kind]
    population_hash = audit._population_hash(population["records"])
    entropy, derived_seed, first_commit = audit.derive_entropy_seed(
        freeze,
        audit_kind="source_disposition",
        family_id=family_id,
        population_kind=population_kind,
        population_universe_sha256=population_hash,
    )
    result: dict[str, Any] = {
        "schema_version": "phase3_disposition_audit_seed_receipt_v2_1", "text_free": True,
        "audit_round_id": "audit_round_fixture", "seed": derived_seed,
        "seed_commitment_sha256": audit.sha256_bytes(derived_seed.encode("ascii")),
        "seed_owner_role_id": "disposition_auditor", "auditor_task_id": _bindings(roles)["auditor_task_id"],
        "source_universe_receipt_sha256": freeze["source_universe_receipt_sha256"],
        "disposition_ledger_sha256": freeze["disposition_ledger_sha256"],
        "population_freeze_sha256": freeze["population_freeze_sha256"],
        "coverage_contract_sha256": freeze["coverage_contract_sha256"],
        **{key: freeze[key] for key in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )},
        "repair_generation": freeze["repair_generation"], "results_recorded": False, "reroll_count": 0,
        "prior_sample_reused": False, "proposal_task_ids": [], "family_id": family_id, "population_kind": population_kind,
        "population_sha256": population_hash, "strata_allocation_sha256": audit.sha256_value(population["strata"]),
        "entropy_contract_version": audit.ENTROPY_CONTRACT_VERSION, "origin_main_ref": audit.ORIGIN_MAIN_REF,
        "first_containing_squash_merge_sha": first_commit, "audit_kind": "source_disposition",
        "entropy_tuple": entropy, "entropy_tuple_sha256": derived_seed,
        "seed_committer_task_id": _bindings(roles)["auditor_task_id"],
        "seed_attestor_task_id": _bindings(roles)["auditor_task_id"], "derivation_mode": "unique_sha256_or_abort",
    }
    result.update(changes)
    return result


def _action(
    roles: dict[str, Any], *, input_manifest_sha256: str, output_sha256: str,
    action_kind: str = "disposition_audit_results",
) -> dict[str, Any]:
    bindings = _bindings(roles)
    execution = next(item for item in roles["functional_roles"] if item["role_id"] == "disposition_auditor")
    identity = {
        "role_id": bindings["auditor_role_id"], "task_id": bindings["auditor_task_id"],
        "input_manifest_sha256": input_manifest_sha256,
        "evaluation_cycle_id": bindings["evaluation_cycle_id"], "output_sha256": output_sha256,
        "status": "completed",
    }
    return {
        "receipt_id": "phase3_functional_action:" + audit.sha256_value(identity), **identity,
        "action_kind": action_kind, "provider": "anthropic", "exact_model": execution["exact_model"],
        "model_family": execution["model_family"], "harness": execution["harness"],
        **{key: bindings[key] for key in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )},
        "started_at": "2026-08-09T00:00:00Z", "completed_at": "2026-08-09T00:01:00Z",
    }


def _results(manifest: dict[str, Any], freeze: dict[str, Any], roles: dict[str, Any]) -> dict[str, Any]:
    task_id = _bindings(roles)["auditor_task_id"]
    rows = [
        {
            "family_id": sample["family_id"], "sample_kind": sample["sample_kind"], "unit_id": unit_id,
            "decision_code": "agree", "auditor_task_id": task_id,
            "evidence_artifact_locators": ["artifact_result"],
        }
        for sample in manifest["samples"] for unit_id in sample["unit_ids"]
    ]
    return {
        "schema_version": "phase3_disposition_audit_results_v2_1", "text_free": True,
        "sample_manifest_sha256": manifest["sample_manifest_sha256"],
        "population_freeze_sha256": manifest["population_freeze_sha256"],
        **{key: freeze[key] for key in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )},
        "repair_generation": freeze["repair_generation"], "results": rows,
        "action_receipt": _action(
            roles, input_manifest_sha256=manifest["sample_manifest_sha256"],
            output_sha256=audit.sha256_value(rows),
        ),
    }


def test_exact_formula_is_not_weakened() -> None:
    assert audit.sample_size(101, 10000) == 101
    assert audit.sample_size(500, 10000) == 200
    assert audit.sample_size(17, 0) == 17


def test_common_entropy_tuple_is_ordered_and_lane_specific() -> None:
    seeds = set()
    for audit_kind, population_kind in [
        ("source_disposition", "nonconverted"),
        ("textbook_nonhit", "textbook_nonhit"),
        ("pravopys_delta", "pravopys_delta"),
    ]:
        frozen_tuple, seed = audit._derive_entropy_seed_from_fields(
            first_containing_squash_merge_sha=_git_token("f"),
            audit_kind=audit_kind,
            family_id="fixture_family",
            population_kind=population_kind,
            population_freeze_sha256=_token("a"),
            population_universe_sha256=_token("b"),
        )
        assert [item["field"] for item in frozen_tuple] == [
            "version_tag", "first_containing_squash_merge_sha", "audit_kind", "family_id",
            "population_kind", "population_freeze_sha256", "population_universe_sha256",
        ]
        seeds.add(seed)
    assert len(seeds) == 3


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "hash"])
def test_disposition_ledger_requires_exact_source_identity(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]], mutation: str) -> None:
    ledger, coverage, roles = frozen
    candidate = deepcopy(ledger)
    rows = candidate["families"][0]["rows"]
    if mutation == "duplicate":
        rows[1]["unit_id"] = rows[0]["unit_id"]
    elif mutation == "missing":
        rows.pop()
        candidate["families"][0]["disposition_row_sum"] -= 1
    else:
        candidate["families"][0]["audit_universe_sha256"] = _token("0")
    with pytest.raises(audit.AuditError):
        audit.validate_disposition_ledger(candidate, coverage_contract=coverage, role_contract=roles)


def test_population_freeze_and_seed_timing_role_separation(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    good = _seed(freeze, roles)
    assert audit.validate_seed_receipt(good, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")["ok"] is True
    for change in ({"results_recorded": True}, {"reroll_count": 1}, {"proposal_task_ids": ["phase3-task-x"]}):
        with pytest.raises(audit.AuditError):
            audit.validate_seed_receipt(_seed(freeze, roles, **change), freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")
    with pytest.raises(audit.AuditError, match="prohibited task"):
        audit.validate_seed_receipt(good, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted", prohibited_task_ids=[_bindings(roles)["auditor_task_id"]])
    with pytest.raises(audit.AuditError, match="assigned auditor"):
        audit.validate_seed_receipt(_seed(freeze, roles, auditor_task_id="phase3-v2-1-rule-author-extraction"), freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")


@pytest.mark.parametrize("mutation", ["seed", "tuple", "merge", "committer"])
def test_entropy_receipt_rejects_every_alternative_derivation(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]], mutation: str) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    receipt = _seed(freeze, roles)
    if mutation == "seed":
        receipt["seed"] = _token("0")
    elif mutation == "tuple":
        receipt["entropy_tuple"][3]["value"] = "other_family"
    elif mutation == "merge":
        receipt["first_containing_squash_merge_sha"] = _git_token("e")
    else:
        receipt["seed_committer_task_id"] = "phase3-v2-1-root-orchestration"
    with pytest.raises(audit.AuditError):
        audit.validate_seed_receipt(receipt, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")


def _git_run(repo: Any, *arguments: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *arguments], check=True, capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize("subject, accepted", [("feat: land freeze (#123)", True), ("feat: manual landing", False)])
def test_first_containing_entropy_commit_must_be_origin_main_squash(tmp_path: Any, subject: str, accepted: bool) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_run(repo, "init", "-q")
    _git_run(repo, "config", "user.email", "noreply@github.com")
    _git_run(repo, "config", "user.name", "GitHub")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git_run(repo, "add", "README.md")
    _git_run(repo, "commit", "-q", "-m", "chore: initialize (#1)")
    base = {"schema_version": "phase3_disposition_population_freeze_v2_1", "text_free": True}
    freeze = {**base, "population_freeze_sha256": audit.sha256_value(base)}
    (repo / "freeze.json").write_text(json.dumps(freeze, sort_keys=True) + "\n", encoding="utf-8")
    _git_run(repo, "add", "freeze.json")
    _git_run(repo, "commit", "-q", "-m", subject)
    head = _git_run(repo, "rev-parse", "HEAD")
    _git_run(repo, "update-ref", "refs/remotes/origin/main", head)
    if accepted:
        assert audit._first_containing_squash_merge(freeze, repo_root=repo) == head
        frozen_tuple, seed, first_commit = audit.derive_entropy_seed(
            freeze,
            audit_kind="textbook_nonhit",
            family_id="school_textbooks",
            population_kind="textbook_nonhit",
            population_universe_sha256=_token("b"),
            repo_root=repo,
        )
        assert first_commit == head
        assert seed == audit.sha256_bytes(audit.canonical_json(frozen_tuple).encode("utf-8"))
    else:
        with pytest.raises(audit.AuditError, match="not a GitHub squash"):
            audit.derive_entropy_seed(
                freeze,
                audit_kind="textbook_nonhit",
                family_id="school_textbooks",
                population_kind="textbook_nonhit",
                population_universe_sha256=_token("b"),
                repo_root=repo,
            )


def test_stratified_selection_is_deterministic_and_without_replacement() -> None:
    records = [
        {"unit_id": f"unit.{index}", "disposition_code": f"code_{index % 3}", "document_or_edition_identity": f"edition_{index % 2}"}
        for index in range(40)
    ]
    first = audit._stratified_ids(records, 11, _token("d"), "fixture_source", "nonconverted")
    second = audit._stratified_ids(records, 11, _token("d"), "fixture_source", "nonconverted")
    assert first == second
    assert len(first) == len(set(first)) == 11
    assert {next(row for row in records if row["unit_id"] == unit)["disposition_code"] for unit in first} == {"code_0", "code_1", "code_2"}


def test_published_strata_uses_proportional_largest_remainder() -> None:
    records = [
        {"unit_id": f"unit.{index}", "disposition_code": "major" if index < 8 else "minor", "document_or_edition_identity": "edition"}
        for index in range(10)
    ]
    assert audit._strata_allocation(records, 3, "nonconverted") == [
        {"stratum": ["major", "edition"], "population_total": 8, "sample_allocation": 2},
        {"stratum": ["minor", "edition"], "population_total": 2, "sample_allocation": 1},
    ]


def test_stale_and_repaired_seed_receipts_cannot_be_reused(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seed = _seed(freeze, roles)
    with pytest.raises(audit.AuditError, match="cannot be reused"):
        audit.validate_seed_receipt(seed, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted", prior_seed_receipt_sha256s=[audit.sha256_value(seed)])
    stale = _seed(freeze, roles, repair_generation=1)
    with pytest.raises(audit.AuditError, match="repair generation"):
        audit.validate_seed_receipt(stale, freeze, role_contract=roles, family_id="fixture_source", population_kind="nonconverted")


def test_result_codes_and_zero_miss_gate(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seeds = [_seed(freeze, roles), _seed(freeze, roles, population_kind="converted")]
    manifest = audit.emit_samples(freeze, seeds, ledger=ledger, role_contract=roles, coverage_contract=coverage)
    results = _results(manifest, freeze, roles)
    assert audit.validate_audit_results(results, manifest, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)["zero_miss"] is True
    next(row for row in results["results"] if row["sample_kind"] == "nonconverted")["decision_code"] = "disagree_wrong_code"
    with pytest.raises(audit.AuditError, match="zero-nonagree"):
        audit.validate_audit_results(results, manifest, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)


def test_results_reject_self_hashed_subset_manifest(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seeds = [_seed(freeze, roles), _seed(freeze, roles, population_kind="converted")]
    manifest = audit.emit_samples(freeze, seeds, ledger=ledger, role_contract=roles, coverage_contract=coverage)
    forged = deepcopy(manifest)
    forged["samples"][0]["unit_ids"] = forged["samples"][0]["unit_ids"][:1]
    forged["samples"][0]["sample_size"] = 1
    base = {key: value for key, value in forged.items() if key != "sample_manifest_sha256"}
    forged["sample_manifest_sha256"] = audit.sha256_value(base)
    results = _results(manifest, freeze, roles)
    results["sample_manifest_sha256"] = forged["sample_manifest_sha256"]
    results["population_freeze_sha256"] = forged["population_freeze_sha256"]
    with pytest.raises(audit.AuditError, match="differs from deterministic"):
        audit.validate_audit_results(results, forged, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)


def test_emit_rejects_substituted_self_consistent_freeze(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    substituted = deepcopy(freeze)
    substituted["families"][0]["nonconverted"]["records"][0]["document_or_edition_identity"] = "edition_substituted"
    population = substituted["families"][0]["nonconverted"]
    population["strata"] = audit._strata_allocation(population["records"], population["sample_size"], "nonconverted")
    base = {key: value for key, value in substituted.items() if key != "population_freeze_sha256"}
    substituted["population_freeze_sha256"] = audit.sha256_value(base)
    seeds = [_seed(substituted, roles), _seed(substituted, roles, population_kind="converted")]
    with pytest.raises(audit.AuditError, match="freshly derived"):
        audit.emit_samples(substituted, seeds, ledger=ledger, role_contract=roles, coverage_contract=coverage)


def test_source_text_shape_is_rejected(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    ledger["families"][0]["rows"][0]["text"] = "forbidden"
    with pytest.raises(audit.AuditError, match="source text"):
        audit.validate_disposition_ledger(ledger, coverage_contract=coverage, role_contract=roles)


def test_unit_hash_and_conversion_evidence_are_required(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    candidate = deepcopy(ledger)
    candidate["families"][0]["rows"][0]["unit_sha256"] = _token("0")
    with pytest.raises(audit.AuditError, match="unit hash"):
        audit.validate_disposition_ledger(candidate, coverage_contract=coverage, role_contract=roles)
    candidate = deepcopy(ledger)
    candidate["families"][0]["rows"][1]["evidence_artifact_locators"] = []
    with pytest.raises(audit.AuditError, match="evidence"):
        audit.validate_disposition_ledger(candidate, coverage_contract=coverage, role_contract=roles)


def test_repeated_reason_count_is_computed_not_trusted(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    candidate = deepcopy(ledger)
    nonconverted = [row for row in candidate["families"][0]["rows"] if row["disposition_code"] != "converted"]
    assert len(nonconverted) == 4
    for row in nonconverted:
        row["repeated_reason_count"] = 1
    with pytest.raises(audit.AuditError, match="declared repeated reason count"):
        audit.validate_disposition_ledger(candidate, coverage_contract=coverage, role_contract=roles)


def test_blocked_disposition_cannot_pass_coverage(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    ledger["families"][0]["rows"][0]["disposition_code"] = "blocked_with_reason"
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seeds = [_seed(freeze, roles), _seed(freeze, roles, population_kind="converted")]
    manifest = audit.emit_samples(freeze, seeds, ledger=ledger, role_contract=roles, coverage_contract=coverage)
    results = _results(manifest, freeze, roles)
    with pytest.raises(audit.AuditError, match="blocked_with_reason"):
        audit.validate_audit_results(results, manifest, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, coverage_contract=coverage, role_contract=roles)


def test_bundle_recomputes_every_artifact_binding(frozen: tuple[dict[str, Any], dict[str, Any], dict[str, Any]]) -> None:
    ledger, coverage, roles = frozen
    freeze = audit.freeze_audit_populations(ledger, coverage_contract=coverage, role_contract=roles)
    seeds = [_seed(freeze, roles), _seed(freeze, roles, population_kind="converted")]
    manifest = audit.emit_samples(freeze, seeds, ledger=ledger, role_contract=roles, coverage_contract=coverage)
    results = _results(manifest, freeze, roles)
    bundle = {
        "schema_version": "phase3_disposition_audit_bundle_v2_1", "text_free": True,
        "source_universe_receipt_sha256": freeze["source_universe_receipt_sha256"],
        "coverage_contract_sha256": audit.sha256_value(coverage),
        **{key: freeze[key] for key in (
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256",
        )},
        "disposition_ledger_sha256": audit.sha256_value(ledger), "population_freeze_sha256": freeze["population_freeze_sha256"],
        "seed_receipt_sha256s": sorted(audit.sha256_value(seed) for seed in seeds),
        "sample_manifest_sha256": manifest["sample_manifest_sha256"], "audit_results_sha256": audit.sha256_value(results),
    }
    schema = json.loads((audit.DATA / "contracts/phase3_disposition_audit_bundle_v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for artifact in [ledger, freeze, *seeds, manifest, results, bundle]:
        validator.validate(artifact)
    assert audit.validate_bundle(bundle, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, sample_manifest=manifest, results=results, coverage_contract=coverage, role_contract=roles)["bundle_verified"] is True
    bundle["audit_results_sha256"] = _token("0")
    with pytest.raises(audit.AuditError, match="audit_results_sha256"):
        audit.validate_bundle(bundle, ledger=ledger, population_freeze=freeze, seed_receipts=seeds, sample_manifest=manifest, results=results, coverage_contract=coverage, role_contract=roles)


def test_schema_is_a_closed_artifact_schema() -> None:
    schema = json.loads((audit.DATA / "contracts/phase3_disposition_audit_bundle_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert "oneOf" in schema and "ledgerRow" in schema["$defs"] and schema["$defs"]["ledgerRow"]["additionalProperties"] is False


def test_historical_controller_lexical_census_is_non_current() -> None:
    census = {
        "schema_version": "phase3_lexical_complete_census_v1", "text_free": True,
        "auditor_controller_identity_id": "controller_fixture_auditor", "families": [],
    }
    with pytest.raises(audit.AuditError, match="historical v1"):
        audit.validate_lexical_complete_census(census, coverage_contract=_coverage(), role_contract=_roles())


def _lexical_roles() -> dict[str, Any]:
    return json.loads(lexical.DEFAULT_ROLE_CONTRACT.read_text(encoding="utf-8"))


def _lexical_population() -> dict[str, Any]:
    locator = {"kind": "release_artifact_immutable_locator", "artifact_id": "release_fixture", "artifact_sha256": _token("a"), "path": "release.json", "anchor_sha256": _token("b")}
    families = []
    for index, family_id in enumerate(sorted(lexical.LEXICAL_FAMILIES)):
        rows = [] if index else [{"family_id": family_id, "unit_id": f"unit.{family_id}.{_token('c')}", "unit_sha256": _token("d"), "evidence_locators": [locator]}]
        families.append({"family_id": family_id, "structural_universe_sha256": _token("e"), "used_subset_total": len(rows), "rows": rows, "used_subset_population_sha256": lexical.sha256_value(rows)})
    base = {
        "schema_version": "phase3_lexical_used_subset_population_freeze_v2_1", "text_free": True,
        "source_universe_receipt_sha256": _token("1"), "source_universe_payload_manifest_sha256": _token("2"), "lexical_structural_freeze_sha256": _token("3"),
        "release_artifact_manifest_sha256": _token("4"), "release_files_sha256": _token("5"), "coverage_contract_sha256": _token("6"),
        **lexical._contract_bindings(_lexical_roles()), "producer_task_id": lexical.POPULATION_FREEZE_TASK,
        "implementation_sha256": lexical.implementation_sha256(),
        "repair_generation": 0, "families": families,
    }
    return {**base, "population_freeze_sha256": lexical.sha256_value(base)}


def _complete_census(population: dict[str, Any]) -> dict[str, Any]:
    families = []
    for family in population["families"]:
        rows = [{**row, "decision_code": "agree"} for row in family["rows"]]
        families.append({"family_id": family["family_id"], "used_subset_total": len(rows), "rows": rows, "used_subset_census_sha256": lexical.sha256_value(rows)})
    roles = _lexical_roles()
    result = {
        "schema_version": "phase3_lexical_complete_census_v2_1", "text_free": True,
        "source_universe_receipt_sha256": population["source_universe_receipt_sha256"],
        "source_universe_payload_manifest_sha256": population["source_universe_payload_manifest_sha256"],
        "lexical_structural_freeze_sha256": population["lexical_structural_freeze_sha256"],
        "coverage_contract_sha256": population["coverage_contract_sha256"],
        **lexical._contract_bindings(roles), "population_freeze_sha256": population["population_freeze_sha256"],
        "implementation_sha256": lexical.implementation_sha256(), "repair_generation": 0,
        "seed_required": False, "families": families,
    }
    result["action_receipt"] = _action(
        roles,
        action_kind="lexical_complete_census",
        input_manifest_sha256=lexical.sha256_value({
            "population_freeze_sha256": result["population_freeze_sha256"], "repair_generation": 0,
        }),
        output_sha256=lexical.sha256_value(families),
    )
    return result


@pytest.mark.parametrize("mutation", ["omission", "addition", "substitution", "duplicate", "stale", "zero_family", "nonagree", "auditor", "seed"])
def test_closed_lexical_census_fails_closed_for_population_and_authority(mutation: str) -> None:
    population, roles = _lexical_population(), _lexical_roles()
    census = _complete_census(population)
    first = census["families"][0]
    if mutation == "omission":
        first["rows"] = []
        first["used_subset_total"] = 0
    elif mutation == "addition":
        first["rows"].append(deepcopy(first["rows"][0]))
        first["rows"][-1]["unit_id"] = f"unit.{first['family_id']}.{_token('9')}"
        first["used_subset_total"] = 2
    elif mutation == "substitution":
        first["rows"][0]["unit_sha256"] = _token("9")
    elif mutation == "duplicate":
        first["rows"].append(deepcopy(first["rows"][0]))
        first["used_subset_total"] = 2
    elif mutation == "stale":
        census["repair_generation"] = 1
    elif mutation == "zero_family":
        census["families"].pop()
    elif mutation == "nonagree":
        first["rows"][0]["decision_code"] = "disagree_invalid_attestation"
    elif mutation == "auditor":
        census["auditor_task_id"] = "phase3-v2-1-rule-author-extraction"
    else:
        census["seed"] = _token("f")
    with pytest.raises(lexical.LexicalCoverageError):
        lexical.validate_complete_census(census, population, role_contract=roles)


def test_complete_census_rejects_stale_population_role_contract() -> None:
    population, roles = _lexical_population(), _lexical_roles()
    next(item for item in roles["functional_roles"] if item["role_id"] == "disposition_auditor")["task_id"] = "phase3-v2-1-other-audit"
    with pytest.raises(lexical.LexicalCoverageError, match="functional-role schema"):
        lexical.validate_complete_census(_complete_census(population), population, role_contract=roles)


def test_cli_validates_synthetic_closed_lexical_census_v2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    roles = _lexical_roles()
    population = _lexical_population()
    census = _complete_census(population)
    role_path = tmp_path / "roles.json"
    population_path = tmp_path / "population.json"
    census_path = tmp_path / "census.json"
    role_path.write_text(json.dumps(roles), encoding="utf-8")
    population_path.write_text(json.dumps(population), encoding="utf-8")
    census_path.write_text(json.dumps(census), encoding="utf-8")

    assert audit.main([
        "--role-contract", str(role_path),
        "validate-lexical-census-v2",
        "--census", str(census_path),
        "--population-freeze", str(population_path),
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {
        "complete_census": True,
        "family_count": 13,
        "ok": True,
        "seed_required": False,
        "status": "MECHANICS_ONLY_NOT_SOURCE_COVERAGE_READY",
        "used_unit_count": 1,
    }


def test_release_manifest_is_closed_and_rejects_generic_locator(tmp_path: Any) -> None:
    release = tmp_path / "release"
    release.mkdir()
    artifact = release / "release.json"
    artifact.write_text('{"opaque":true}\n', encoding="utf-8")
    item = {"artifact_id": "release_fixture", "path": "release.json", "sha256": lexical.sha256_file(artifact)}
    manifest = {"schema_version": "phase3_lexical_release_manifest_v1", "text_free": True, "release_files": [item], "release_artifact_manifest_sha256": ""}
    manifest["release_artifact_manifest_sha256"] = lexical.sha256_value({key: value for key, value in manifest.items() if key != "release_artifact_manifest_sha256"})
    assert lexical._validate_release_manifest(manifest, release_root=release)[0] == manifest["release_artifact_manifest_sha256"]
    (release / "extra.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(lexical.LexicalCoverageError, match="closure"):
        lexical._validate_release_manifest(manifest, release_root=release)
    family_id = "lexical_balla_en_uk"
    with pytest.raises(lexical.LexicalCoverageError, match="database-only"):
        lexical._validate_typed_reference({"family_id": family_id, "unit_id": f"unit.{family_id}.{_token('a')}", "unit_sha256": _token("b"), "evidence_locator": {"kind": "database_locator", "artifact_id": "release_fixture", "artifact_sha256": item["sha256"], "path": "release.json", "anchor_sha256": _token("c")}}, files={"release_fixture": item})


def test_closed_release_scanner_extracts_embedded_typed_reference_and_rejects_legacy_generic_use(tmp_path: Any) -> None:
    release = tmp_path / "release"
    release.mkdir()
    family_id = "lexical_vesum"
    typed = {"record": {"lexical_unit_reference": {"family_id": family_id, "unit_id": f"unit.{family_id}.{_token('a')}", "unit_sha256": _token("b")}}}
    artifact = release / "release.json"
    artifact.write_text(json.dumps(typed) + "\n", encoding="utf-8")
    file = {"artifact_id": "release_fixture", "path": "release.json", "sha256": lexical.sha256_file(artifact)}
    references = lexical.extract_typed_lexical_references([file], release_root=release)
    assert [(item["family_id"], item["unit_id"]) for item in references] == [(family_id, typed["record"]["lexical_unit_reference"]["unit_id"])]
    artifact.write_text(json.dumps({"channel": "vesum", "locator": "data/vesum.db"}) + "\n", encoding="utf-8")
    file["sha256"] = lexical.sha256_file(artifact)
    with pytest.raises(lexical.LexicalCoverageError, match="generic lexical"):
        lexical.extract_typed_lexical_references([file], release_root=release)
    artifact.write_text(json.dumps({"channel": "r2u", "locator": "r2u-cache.json"}) + "\n", encoding="utf-8")
    file["sha256"] = lexical.sha256_file(artifact)
    with pytest.raises(lexical.LexicalCoverageError, match="generic lexical"):
        lexical.extract_typed_lexical_references([file], release_root=release)


def test_multiple_typed_occurrences_form_one_used_unit_with_all_locators() -> None:
    family_id = "lexical_vesum"
    unit_id = f"unit.{family_id}.{_token('a')}"
    def occurrence(artifact_id: str, anchor: str, unit_hash: str = _token("b")) -> dict[str, Any]:
        return {"family_id": family_id, "unit_id": unit_id, "unit_sha256": unit_hash, "evidence_locator": {"kind": "release_artifact_immutable_locator", "artifact_id": artifact_id, "artifact_sha256": _token("c"), "path": f"{artifact_id}.json", "anchor_sha256": anchor}}

    rows = lexical.aggregate_typed_occurrences([occurrence("release_b", _token("2")), occurrence("release_a", _token("1"))])
    assert len(rows) == 1
    assert len(rows[0]["evidence_locators"]) == 2
    assert [item["artifact_id"] for item in rows[0]["evidence_locators"]] == ["release_a", "release_b"]
    with pytest.raises(lexical.LexicalCoverageError, match="conflicting hashes"):
        lexical.aggregate_typed_occurrences([occurrence("release_a", _token("1")), occurrence("release_b", _token("2"), _token("d"))])


@pytest.mark.parametrize("field", ["duplicate_group_observation_total", "duplicate_group_rolling_sha256"])
def test_structural_audit_compares_reopened_duplicate_groups(monkeypatch: pytest.MonkeyPatch, field: str) -> None:
    roles, coverage = _lexical_roles(), {"coverage": "fixture"}
    summaries = [{"family_id": family_id, "unit_count": 2, "ordered_rolling_sha256": _token("a"), "duplicate_group_observation_total": 2, "duplicate_group_rolling_sha256": _token("b"), "parse_status_counts": {"parsed": 2}, "provenance": {"input_sha256": _token("c"), "unit_grain": "fixture"}} for family_id in sorted(lexical.LEXICAL_FAMILIES)]
    source = {"artifact_manifest": {"payload_manifest_sha256": _token("d")}}
    monkeypatch.setattr(lexical, "_source_bindings", lambda _: (source, _token("e"), {"families": summaries}, _token("f")))
    monkeypatch.setattr(lexical, "reopen_structural_universe", lambda **_: summaries)
    receipt = {
        "schema_version": "phase3_lexical_structural_audit_v2_1", "text_free": True,
        "source_universe_receipt_sha256": _token("e"), "source_universe_payload_manifest_sha256": _token("d"),
        "lexical_structural_freeze_sha256": _token("f"), "coverage_contract_sha256": lexical.sha256_value(coverage),
        **lexical._contract_bindings(roles), "implementation_sha256": lexical.implementation_sha256(),
        "repair_generation": 0, "families": deepcopy(summaries),
    }
    receipt["action_receipt"] = _action(
        roles, action_kind="lexical_structural_audit",
        input_manifest_sha256=lexical.sha256_value({
            "source_universe_receipt_sha256": receipt["source_universe_receipt_sha256"],
            "lexical_structural_freeze_sha256": receipt["lexical_structural_freeze_sha256"],
            "coverage_contract_sha256": receipt["coverage_contract_sha256"],
            "implementation_sha256": receipt["implementation_sha256"], "repair_generation": 0,
        }),
        output_sha256=lexical.sha256_value(receipt["families"]),
    )
    assert lexical.validate_structural_audit(receipt, coverage_contract=coverage, role_contract=roles, sources_db=Path("unused"), vesum_db=Path("unused"), r2u_cache=Path("unused"))["structural_audit_verified"] is True
    receipt["families"][0][field] = 1 if field.endswith("total") else _token("9")
    with pytest.raises(lexical.LexicalCoverageError, match="reopened lexical"):
        lexical.validate_structural_audit(receipt, coverage_contract=coverage, role_contract=roles, sources_db=Path("unused"), vesum_db=Path("unused"), r2u_cache=Path("unused"))


def test_lexical_bundle_cannot_accept_an_unvalidated_structural_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    population, roles = _lexical_population(), _lexical_roles()
    census = _complete_census(population)
    structural = {"invalid": True}
    bindings = {name: population[name] for name in ("source_universe_receipt_sha256", "source_universe_payload_manifest_sha256", "lexical_structural_freeze_sha256", "coverage_contract_sha256", "base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256", "auditor_task_id", "implementation_sha256", "repair_generation")}
    bundle = {"schema_version": "phase3_lexical_coverage_bundle_v2_1", "text_free": True, **bindings, "structural_audit_sha256": lexical.sha256_value(structural), "structural_action_receipt_id": _token("7"), "population_freeze_sha256": population["population_freeze_sha256"], "complete_census_sha256": lexical.sha256_value(census), "census_action_receipt_id": census["action_receipt"]["receipt_id"], "release_artifact_manifest_sha256": population["release_artifact_manifest_sha256"], "first_containing_squash_merge_sha": _git_token("a")}
    monkeypatch.setattr(lexical, "validate_structural_audit", lambda *args, **kwargs: (_ for _ in ()).throw(lexical.LexicalCoverageError("invalid structural receipt")))
    with pytest.raises(lexical.LexicalCoverageError, match="invalid structural"):
        lexical.validate_lexical_bundle(bundle, structural_audit=structural, population_freeze=population, census=census, role_contract=roles, coverage_contract={"fixture": True}, sources_db=Path("unused"), vesum_db=Path("unused"), r2u_cache=Path("unused"))


@pytest.mark.parametrize("binding", ["source_universe_receipt_sha256", "coverage_contract_sha256", "functional_role_contract_sha256", "repair_generation"])
def test_lexical_bundle_rejects_stale_cross_receipt_bindings(monkeypatch: pytest.MonkeyPatch, binding: str) -> None:
    roles, coverage = _lexical_roles(), {"coverage": "fixture"}
    population = _lexical_population()
    population["coverage_contract_sha256"] = lexical.sha256_value(coverage)
    base = {key: value for key, value in population.items() if key != "population_freeze_sha256"}
    population["population_freeze_sha256"] = lexical.sha256_value(base)
    census = _complete_census(population)
    structural = {name: population[name] for name in ("source_universe_receipt_sha256", "source_universe_payload_manifest_sha256", "lexical_structural_freeze_sha256", "coverage_contract_sha256", "base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256", "auditor_task_id", "implementation_sha256", "repair_generation")}
    structural["action_receipt"] = {"receipt_id": _token("7")}
    bundle = {"schema_version": "phase3_lexical_coverage_bundle_v2_1", "text_free": True, **{key: value for key, value in structural.items() if key != "action_receipt"}, "structural_audit_sha256": lexical.sha256_value(structural), "structural_action_receipt_id": structural["action_receipt"]["receipt_id"], "population_freeze_sha256": population["population_freeze_sha256"], "complete_census_sha256": lexical.sha256_value(census), "census_action_receipt_id": census["action_receipt"]["receipt_id"], "release_artifact_manifest_sha256": population["release_artifact_manifest_sha256"], "first_containing_squash_merge_sha": _git_token("a")}
    monkeypatch.setattr(lexical, "validate_structural_audit", lambda *args, **kwargs: {"ok": True})
    monkeypatch.setattr(lexical, "validate_complete_census", lambda *args, **kwargs: {"ok": True})
    if binding == "repair_generation":
        bundle[binding] = 1
    else:
        bundle[binding] = _token("9")
    with pytest.raises(lexical.LexicalCoverageError, match="binding mismatch"):
        lexical.validate_lexical_bundle(bundle, structural_audit=structural, population_freeze=population, census=census, role_contract=roles, coverage_contract=coverage, sources_db=Path("unused"), vesum_db=Path("unused"), r2u_cache=Path("unused"))


def test_structural_summary_streams_large_synthetic_family() -> None:
    def units() -> Any:
        for index in range(150_000):
            yield {"unit_id": f"unit.fixture.{index}", "unit_sha256": _token("a"), "duplicate_group_id": f"duplicate.fixture.{index % 3}", "parse_status": "parsed", "provenance": {"input_sha256": _token("b"), "unit_grain": "fixture"}}

    tracemalloc.start()
    summary = lexical._structural_summary("fixture", units())
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert summary["unit_count"] == summary["duplicate_group_observation_total"] == 150_000
    assert peak < 5 * 1024 * 1024
