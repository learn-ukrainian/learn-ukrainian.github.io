"""Hermetic tests for the v2.1-bound Pravopys delta primitives."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_audit_entropy as entropy
from scripts.projects.open_model_data import phase3_pravopys_delta as delta


def _hash(value: object) -> str:
    return hashlib.sha256(delta.canonical_json(value).encode("utf-8")).hexdigest()


def _units(edition: str, count: int) -> list[dict[str, object]]:
    return [{
        "family_id": edition,
        "unit_id": f"{edition}.{number}",
        "unit_sha256": hashlib.sha256(f"unit-{edition}-{number}".encode()).hexdigest(),
        "normalized_text_sha256": hashlib.sha256(f"hash-{number}".encode()).hexdigest(),
        "ordinal": number,
        "locator": {
            "kind": "pdf_numbered_hierarchy",
            "edition_sha256": delta.EDITION_HASHES[edition],
            "page": number,
            "line": 1,
            "end_page": number,
            "end_line": 1,
            "section_path": [f"paragraph:{number}"],
        },
        "duplicate_group_id": f"duplicate.{edition}.{number}",
        "parse_status": "numbered_hierarchy_parsed",
        "rights": {
            "source_text_committed": False,
            "locator_only_allowed": True,
            "rights_limited_disposition": "rights_limited_locator_only",
        },
        "provenance": {
            "input_sha256": delta.EDITION_HASHES[edition],
            "unit_grain": "pdf_numbered_hierarchy",
        },
    } for number in range(1, count + 1)]


def _write_freeze(tmp_path: Path) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    directory = tmp_path / "freeze"
    directory.mkdir()
    rows = {
        delta.EDITION_2019: _units(delta.EDITION_2019, 1090),
        delta.EDITION_2026: _units(delta.EDITION_2026, 1466),
    }
    ledger_hashes = {}
    payloads = []
    for edition, units in rows.items():
        name = f"{edition}.units.jsonl"
        content = "".join(delta.canonical_json(unit) + "\n" for unit in units).encode("utf-8")
        (directory / name).write_bytes(content)
        ledger_hashes[edition] = hashlib.sha256(content).hexdigest()
        payloads.append({"path": name, "sha256": ledger_hashes[edition]})
    inputs = {
        "calque_module": "1" * 64,
        "pravopys_2019_pdf": delta.EDITION_HASHES[delta.EDITION_2019],
        "pravopys_2026_pdf": delta.EDITION_HASHES[delta.EDITION_2026],
        "r2u_cache": "2" * 64,
        "sources_db": "3" * 64,
        "vesum_db": "4" * 64,
    }
    contract, bindings = delta.load_functional_role_bindings()
    source_binding = bindings[delta.UKRAINIAN_REVIEWER_ROLE]
    receipt = {
        "schema_version": "phase3_source_universe_freeze_v1",
        "text_free": True,
        "status": delta.LEGACY_SOURCE_FREEZE_STATUS,
        "input_sha256": inputs,
        "families": [
            {"family_id": edition, "ledger_file": f"{edition}.units.jsonl", "ledger_sha256": ledger_hashes[edition], "unit_count": count}
            for edition, count in delta.EDITION_TOTALS.items()
        ],
        "artifact_manifest": {"payloads": payloads},
    }
    receipt_path = directory / "receipt.json"
    receipt_path.write_text(delta.canonical_json(receipt) + "\n", encoding="utf-8")
    manifest = {
        "wrapper_schema_version": delta.SOURCE_FREEZE_WRAPPER_SCHEMA_VERSION,
        "legacy_receipt_path": "freeze/receipt.json",
        "legacy_receipt_sha256": delta.sha256_file(receipt_path),
        "source_status": delta.CURRENT_SOURCE_FREEZE_STATUS,
        "input_sha256": inputs,
        "ledger_sha256": ledger_hashes,
        "ledger_unit_counts": delta.EDITION_TOTALS,
        "base_contract_sha256": delta.functional_roles.BASE_SHA256,
        "amendment_sha256": delta.functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": delta.functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": source_binding["functional_role_contract_sha256"],
        "conflict_graph_sha256": source_binding["conflict_graph_sha256"],
        "evaluation_cycle_id": source_binding["evaluation_cycle_id"],
        "source_freeze_input_manifest_sha256": delta.source_freeze_input_manifest_sha256(
            inputs, ledger_hashes, delta.EDITION_TOTALS,
        ),
        "source_review_receipt_locator": "immutable://source-review/current-wrapper",
        "source_review_receipt_sha256": "a" * 64,
    }
    manifest["source_review_result_sha256"] = delta.source_freeze_review_result_sha256(manifest)
    manifest["source_review_action_receipt"] = _action(
        contract,
        source_binding,
        action_kind=delta.SOURCE_REVIEW_ACTION_KIND,
        input_sha256=manifest["source_freeze_input_manifest_sha256"],
        output_sha256=manifest["source_review_result_sha256"],
    )
    return manifest, rows[delta.EDITION_2019], rows[delta.EDITION_2026]


def _action(
    role_contract: dict[str, object], binding: dict[str, str], *, action_kind: str, input_sha256: str, output_sha256: str,
) -> dict[str, str]:
    role = next(item for item in role_contract["functional_roles"] if item["role_id"] == binding["role_id"])
    identity = {
        "role_id": binding["role_id"],
        "task_id": binding["task_id"],
        "input_manifest_sha256": input_sha256,
        "evaluation_cycle_id": binding["evaluation_cycle_id"],
        "output_sha256": output_sha256,
        "status": "completed",
    }
    return {
        "receipt_id": "phase3_functional_action:" + _hash(identity),
        "role_id": binding["role_id"],
        "task_id": binding["task_id"],
        "action_kind": action_kind,
        "provider": delta.ROLE_PROVIDERS[binding["role_id"]],
        "exact_model": role["exact_model"],
        "model_family": role["model_family"],
        "harness": role["harness"],
        "input_manifest_sha256": input_sha256,
        "output_sha256": output_sha256,
        "evaluation_cycle_id": binding["evaluation_cycle_id"],
        "base_contract_sha256": delta.functional_roles.BASE_SHA256,
        "amendment_sha256": delta.functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": delta.functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": binding["functional_role_contract_sha256"],
        "conflict_graph_sha256": binding["conflict_graph_sha256"],
        "started_at": "2026-08-09T00:00:00Z",
        "completed_at": "2026-08-09T00:01:00Z",
        "status": "completed",
    }


def _ledger(tmp_path: Path) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object], dict[str, dict[str, str]]]:
    freeze, old, new = _write_freeze(tmp_path)
    candidates = delta.generate_candidate_alignment(old, new)
    contract, bindings = delta.load_functional_role_bindings()
    rows = []
    for candidate in candidates:
        old_ids, new_ids = candidate["unit_ids_2019"], candidate["unit_ids_2026"]
        disposition, semantic = ("unchanged", False)
        if old_ids and not new_ids:
            disposition, semantic = "removed_rule_bearing_unit", True
        elif new_ids and not old_ids:
            disposition, semantic = "added_rule_bearing_unit", True
        row = {
            "delta_id": f"delta.{candidate['candidate_id']}",
            "delta_disposition": disposition,
            "candidate_ids": [candidate["candidate_id"]],
            "unit_ids_2019": sorted(old_ids),
            "unit_ids_2026": sorted(new_ids),
            "edition_section_identity": "opaque-section",
        }
        review_hash = hashlib.sha256(row["delta_id"].encode()).hexdigest()
        row["ukrainian_review"] = {
            "role_id": delta.UKRAINIAN_REVIEWER_ROLE,
            "task_id": bindings[delta.UKRAINIAN_REVIEWER_ROLE]["task_id"],
            "review_receipt_locator": f"immutable://review/{row['delta_id']}",
            "review_receipt_sha256": review_hash,
            "evidence_locator": f"immutable://evidence/{row['delta_id']}",
            "evidence_sha256": hashlib.sha256((row["delta_id"] + "evidence").encode()).hexdigest(),
            "adjudication_state": "externally_reviewed",
            "semantic_review": semantic,
            "action_receipt": _action(
                contract,
                bindings[delta.UKRAINIAN_REVIEWER_ROLE],
                action_kind=delta.REVIEW_ACTION_KIND,
                input_sha256=delta._delta_review_input_manifest_sha256(freeze, row),
                output_sha256=review_hash,
            ),
        }
        rows.append(row)
    return freeze, old, new, candidates, rows, contract, bindings


def _seed(rows: list[dict[str, object]], freeze: dict[str, object]) -> dict[str, object]:
    population = delta.freeze_population(rows)
    nonce = "b" * 64
    entropy_receipt = {
        "schema_version": "phase3_audit_entropy_receipt_v1",
        "text_free": True,
        "commitment_path": "data/projects/open_model_data/audit_entropy_commitments/opaque.json",
        "commitment_sha256": "c" * 64,
        "commitment_first_containing_merge_sha": "a" * 40,
        "auditor_nonce": nonce,
    }
    return {
        "population_sha256": population["population_sha256"],
        "seed_owner_role_id": delta.AUDITOR_ROLE,
        "auditor_attests_only": True,
        "audit_id": "pravopys_delta",
        "family_id": "pravopys_2019_2026_delta",
        "universe_sha256": delta.source_universe_sha256(freeze),
        "entropy_receipt": entropy_receipt,
    }


def test_current_hash_bound_freeze_loads_exact_denominators_and_rejects_old_status(tmp_path: Path) -> None:
    freeze, old, new = _write_freeze(tmp_path)
    wrapper, loaded_old, loaded_new = delta.load_frozen_pravopys_ledgers(freeze, repo_root=tmp_path)
    assert wrapper["source_status"] == delta.CURRENT_SOURCE_FREEZE_STATUS
    assert len(loaded_old) == len(old) == 1090
    assert len(loaded_new) == len(new) == 1466
    assert delta.generate_candidate_alignment(loaded_old, loaded_new) == delta.generate_candidate_alignment(old, new)
    old_status = copy.deepcopy(freeze)
    old_status["source_status"] = delta.LEGACY_SOURCE_FREEZE_STATUS
    with pytest.raises(delta.PravopysDeltaError, match="invalidated or non-current"):
        delta.load_frozen_pravopys_ledgers(old_status, repo_root=tmp_path)


def test_source_freeze_rejects_rebranded_legacy_receipt_and_tampered_review_action(tmp_path: Path) -> None:
    freeze, _, _ = _write_freeze(tmp_path)
    receipt_path = tmp_path / "freeze" / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    with pytest.raises(delta.PravopysDeltaError, match="wrapper fields drift"):
        delta.load_frozen_pravopys_ledgers(receipt, repo_root=tmp_path)

    for field, value, pattern in (
        ("provider", "legacy-provider", "provider binding"),
        ("task_id", "legacy-controller-task", "task binding"),
        ("exact_model", "legacy-controller-model", "lane mismatch"),
        ("evaluation_cycle_id", "legacy-cycle", "contract or evaluation-cycle"),
    ):
        tampered = copy.deepcopy(freeze)
        tampered["source_review_action_receipt"][field] = value
        with pytest.raises(delta.PravopysDeltaError, match=pattern):
            delta.load_frozen_pravopys_ledgers(tampered, repo_root=tmp_path)


def test_v21_role_bindings_and_closed_review_receipts_are_required(tmp_path: Path) -> None:
    freeze, old, new, candidates, rows, contract, bindings = _ledger(tmp_path)
    assert delta.validate_delta_ledger(rows, candidates, old, new, source_freeze=freeze, role_contract=contract, reviewer_binding=bindings[delta.UKRAINIAN_REVIEWER_ROLE])["edition_totals"] == delta.EDITION_TOTALS
    stale = copy.deepcopy(rows)
    stale[0]["ukrainian_review"]["action_receipt"]["provider"] = "legacy-provider"
    with pytest.raises(delta.PravopysDeltaError, match="provider binding"):
        delta.validate_delta_ledger(stale, candidates, old, new, source_freeze=freeze, role_contract=contract, reviewer_binding=bindings[delta.UKRAINIAN_REVIEWER_ROLE])
    mismatched = copy.deepcopy(rows)
    mismatched[0]["ukrainian_review"]["action_receipt"]["input_manifest_sha256"] = "0" * 64
    with pytest.raises(delta.PravopysDeltaError, match="input/output"):
        delta.validate_delta_ledger(mismatched, candidates, old, new, source_freeze=freeze, role_contract=contract, reviewer_binding=bindings[delta.UKRAINIAN_REVIEWER_ROLE])


def test_complete_bundle_requires_current_freeze_and_auditor_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze, old, new, candidates, rows, contract, bindings = _ledger(tmp_path)
    population = delta.freeze_population(rows)
    seed = _seed(rows, freeze)
    verifier_calls: list[dict[str, object]] = []

    def verifier(receipt: object, **kwargs: object) -> dict[str, str]:
        assert receipt == seed["entropy_receipt"]
        verifier_calls.append(kwargs)
        return {
            "derived_seed": "f" * 64,
            "entropy_receipt_sha256": "1" * 64,
            "first_containing_merge_sha": "a" * 40,
            "canonical_tuple_sha256": "2" * 64,
        }

    monkeypatch.setattr(entropy, "verify_entropy_receipt", verifier)
    sample = delta.draw_audit_sample(rows, population, seed, source_freeze=freeze)
    results = [{"delta_id": identifier, "decision": "agree", "repair_applied": False} for identifier in sample["sample_delta_ids"]]
    audit_action = _action(
        contract,
        bindings[delta.AUDITOR_ROLE],
        action_kind=delta.AUDIT_ACTION_KIND,
        input_sha256=delta.sha256_json(sample),
        output_sha256=delta.sha256_json(results),
    )
    bundle = {
        "schema_version": delta.SCHEMA_VERSION,
        "text_free": True,
        "source_freeze": freeze,
        "units_2019": old,
        "units_2026": new,
        "candidate_alignment": candidates,
        "delta_ledger": rows,
        "population_freeze": population,
        "auditor_seed": seed,
        "audit_sample": sample,
        "audit_results": results,
        "audit_action_receipt": audit_action,
    }
    assert delta.validate_bundle(bundle, repo_root=tmp_path)["ok"] is True
    assert verifier_calls and verifier_calls[0]["auditor_role_id"] == delta.AUDITOR_ROLE
    stale_cycle = copy.deepcopy(bundle)
    stale_cycle["audit_action_receipt"]["evaluation_cycle_id"] = "old-cycle"
    with pytest.raises(delta.PravopysDeltaError, match="contract or evaluation-cycle"):
        delta.validate_bundle(stale_cycle, repo_root=tmp_path)


def test_public_entropy_verifier_injection_is_not_a_production_api(tmp_path: Path) -> None:
    freeze, _, _, _, rows, _, _ = _ledger(tmp_path)
    population = delta.freeze_population(rows)
    with pytest.raises(TypeError, match="approved_common_entropy_contract"):
        delta.draw_audit_sample(
            rows,
            population,
            _seed(rows, freeze),
            source_freeze=freeze,
            approved_common_entropy_contract=lambda *_args, **_kwargs: None,
        )


def test_schema_is_strict_and_current_contract_shaped() -> None:
    assert delta.hamilton_allocation({("a", "x"): 7, ("b", "y"): 3, ("c", "z"): 2}, 5) == {
        ("a", "x"): 3,
        ("b", "y"): 1,
        ("c", "z"): 1,
    }
    schema = json.loads(Path(delta.SCHEMA_PATH).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$defs"]["source_freeze"]["properties"]["source_status"]["const"] == delta.CURRENT_SOURCE_FREEZE_STATUS
    assert schema["$defs"]["source_freeze"]["properties"]["wrapper_schema_version"]["const"] == delta.SOURCE_FREEZE_WRAPPER_SCHEMA_VERSION
    assert schema["$defs"]["review"]["properties"]["task_id"]["const"] == "phase3-v2-1-ukrainian-source-review"
    assert schema["additionalProperties"] is False
