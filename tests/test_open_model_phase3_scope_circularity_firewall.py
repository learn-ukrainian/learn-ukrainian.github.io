"""Hostile contract tests for the #7427 held-out / Cycle007 firewall."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import freeze_phase3_scope_circularity_firewall as firewall


def _record(*, namespace: str = "independent", origin: str = "independent", candidate: str = "a") -> dict[str, str]:
    return {"candidate_id": candidate, "origin": origin, "namespace": namespace, "membership_sha256": "a" * 64, "component_sha256": "b" * 64, "independent_origin": "true"}


def _private_config(root: Path, name: str = "config.json") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    path = root / name
    value = {
        "schema_version": "phase3_evaluation_steward_config_v1",
        "private_root": str(root),
        "content_pack_directory": str(root / "content-pack"),
        "steward_output_root": str(root / "steward-output"),
        "steward_role": "evaluation_steward",
    }
    value["config_sha256"] = firewall._config_hash(value)
    path.write_text(json.dumps(value), encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def test_generated_contract_is_exact_and_schema_valid() -> None:
    contract = firewall.build_contract()
    assert firewall.validate_contract_integrity(contract)
    schema = json.loads((firewall.DATA / "contracts/phase3_scope_circularity_firewall_v1.schema.json").read_text())
    Draft202012Validator(schema).validate(contract)
    assert contract["denominator"]["coverage_blocked_cells"] == 14
    assert contract["cycle007"]["private_binding_state"] == "UNBOUND"


def test_schema_rejects_nested_extra_missing_and_frozen_drift() -> None:
    contract = firewall.build_contract()
    schema = json.loads((firewall.DATA / "contracts/phase3_scope_circularity_firewall_v1.schema.json").read_text())
    validator = Draft202012Validator(schema)
    extra = deepcopy(contract)
    extra["cycle007"]["unexpected"] = True
    missing = deepcopy(contract)
    del missing["private_runtime"]["rejects"]
    drift = deepcopy(contract)
    drift["denominator"]["source_units"] = 58
    assert list(validator.iter_errors(extra)) and list(validator.iter_errors(missing)) and list(validator.iter_errors(drift))


@pytest.mark.parametrize("namespace", firewall.DENY_NAMESPACES)
def test_every_cycle007_deny_namespace_is_terminal_and_never_derives(namespace: str) -> None:
    called = 0

    def derive(_: object) -> None:
        nonlocal called
        called += 1

    result = firewall.validate_lineage_batch([_record(namespace=namespace)], derive=derive)
    assert result == {"ok": False, "code": "leakage", "emitted": 0, "promoted": 0, "activated": 0}
    assert called == 0


def test_duplicate_and_cycle007_concept_cannot_call_derivation() -> None:
    called = 0

    def derive(_: object) -> None:
        nonlocal called
        called += 1

    duplicate = firewall.validate_lineage_batch([_record(), _record(candidate="a")], derive=derive)
    cycle = firewall.validate_lineage_batch([_record(origin="cycle007")], derive=derive)
    assert duplicate["code"] == "leakage"
    assert cycle["code"] == "leakage"
    assert called == 0


def test_clearance_is_positive_only_and_rehashed_outer_receipt_cannot_bypass() -> None:
    contract = firewall.build_contract()
    clearance = {"p1_sha256": firewall.PINS[firewall.P1], "p1_amendment_sha256": firewall.PINS[firewall.P1_AMENDMENT], "p2_sha256": firewall.PINS[firewall.P2], "near_duplicate_policy_sha256": firewall.PINS[firewall.NEAR_POLICY], "firewall_sha256": firewall.sha256_file(firewall.OUTPUT)}
    assert firewall.validate_builder_clearance(clearance, contract)
    assert not firewall.validate_builder_clearance({**clearance, "membership": "a" * 64}, contract)
    assert not firewall.validate_builder_clearance({**clearance, "near_duplicate_policy_sha256": "0" * 64}, contract)
    assert firewall.validate_lineage_batch([_record(namespace="prompts")])["emitted"] == 0


def test_same_count_pack_or_row_commitment_mutation_fails() -> None:
    manifest = {"schema_version": firewall.storage.PACK_SCHEMA_VERSION, "pack_kind": "content_compact", "receipt_sha256": firewall.EXPECTED_PACK_MANIFEST_RECEIPT_SHA256, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "packet_count": 204, "row_count": 10159, "object_count": 419}
    inventory = {"packet_count": 204, "row_count": 10159, "object_count": 419, "sidecar_count": 408, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256}
    assert firewall.validate_pack_commitments(manifest, inventory)
    assert not firewall.validate_pack_commitments({**manifest, "object_set_sha256": "0" * 64}, inventory)
    assert not firewall.validate_pack_commitments(manifest, {**inventory, "ordered_row_identity_commitment_sha256": "0" * 64})


def test_private_runtime_rejects_caller_hashes_and_unsafe_config_paths(tmp_path: Path) -> None:
    root = tmp_path / "private"
    config = _private_config(root)
    assert firewall.run_steward_production(str(config))["ok"] is False
    forged = json.loads(config.read_text())
    forged["membership_sha256"] = "a" * 64
    forged["component_graph_sha256"] = "b" * 64
    config.write_text(json.dumps(forged), encoding="utf-8")
    os.chmod(config, 0o600)
    assert firewall.run_steward_production(str(config))["code"] == "private_path_unsafe"
    config = _private_config(root)
    os.chmod(config, 0o644)
    assert firewall.run_steward_production(str(config))["code"] == "private_path_unsafe"
    os.chmod(config, 0o600)
    hard = root / "hard.json"
    os.link(config, hard)
    assert firewall.run_steward_production(str(hard))["code"] == "private_path_unsafe"
    hard.unlink()
    link = root / "link.json"
    link.symlink_to(config)
    assert firewall.run_steward_production(str(link))["code"] == "private_path_unsafe"


def test_production_fixture_uses_only_content_compact_pack_and_writes_private_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "private"
    pack = root / "content-pack"
    output = root / "steward-output"
    for path in (root, pack, output):
        path.mkdir(parents=True, exist_ok=True)
        os.chmod(path, 0o700)
    objects = [{"role_relative_path": f"object-{index}", "role_relative_paths": [f"object-{index}", f"alias-{index}"] if index < 205 else [f"object-{index}"], "selection_class": "materialization_manifest", "selection_classes": ["materialization_manifest"]} for index in range(419)]
    manifest = firewall.storage._receipt({"schema_version": firewall.storage.PACK_SCHEMA_VERSION, "pack_kind": "content_compact", "packet_count": 204, "row_count": 10159, "object_count": 419, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "inventory_receipt_sha256": "a" * 64, "content_bodies_stored": True, "objects": objects})
    (pack / "pack-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    os.chmod(pack / "pack-manifest.json", 0o600)
    config = {"schema_version": "phase3_evaluation_steward_config_v1", "private_root": str(root), "content_pack_directory": str(pack), "steward_output_root": str(output), "steward_role": "evaluation_steward"}
    config["config_sha256"] = firewall._config_hash(config)
    config_path = root / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    os.chmod(config_path, 0o600)
    monkeypatch.setattr(firewall, "validate_pack_commitments", lambda *_: True)
    monkeypatch.setattr(firewall.storage, "prove_content_pack_stream", lambda *_: ({}, {}))
    monkeypatch.setattr(firewall, "_build_private_deny_corpus", lambda *_: {"corpus_sha256": "b" * 64})
    result = firewall.run_steward_production(str(config_path))
    assert result["ok"] is True
    assert (output / "cycle007-deny-component-manifest-v1.json").stat().st_mode & 0o777 == 0o600


def test_unbound_and_graph_incomplete_batches_fail_with_zero_outputs() -> None:
    assert firewall.validate_private_runtime_binding(None)["code"] == "private_binding_unbound"
    result = firewall.validate_lineage_batch([{"candidate_id": "missing"}])
    assert result == {"ok": False, "code": "graph_incompleteness", "emitted": 0, "promoted": 0, "activated": 0}


def test_candidate_evaluator_rejects_caller_collision_and_cycle_derivative() -> None:
    row = {"row": "a" * 64, "source_example": "b" * 64, "document_or_edition": "c" * 64, "exact": "d" * 64, "token_hashes": "e" * 64, "component": "f" * 64, "packet": "0" * 64}
    corpus = {"schema_version": "phase3_cycle007_private_deny_corpus_v1", "pack_manifest_receipt_sha256": firewall.EXPECTED_PACK_MANIFEST_RECEIPT_SHA256, "near_duplicate_policy_sha256": firewall.near.pinned_policy_fingerprint(), "rows": [row]}
    corpus["corpus_sha256"] = firewall.sha256_bytes(firewall.canonical_json(corpus))
    assert firewall.evaluate_candidate_batch([{"evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007"}], corpus)["code"] == "uncertain_lineage"
    assert firewall.evaluate_candidate_batch([{"unit_id": "x"}], corpus)["code"] == "uncertain_lineage"


def test_concept_authority_gate_allows_independent_and_rejects_renamed_derivative() -> None:
    allowed = {"kind": "authority_citation", "origin_kind": "independent", "concept_or_citation_id": "external_authority", "authority_sha256": "a" * 64}
    assert firewall.admit_concept_or_authority(allowed)["ok"] is True
    rejected = {"kind": "abstract_concept", "origin_kind": "independent", "concept_or_citation_id": "rehash", "authority_sha256": "a" * 64, "membership": "b" * 64}
    assert firewall.admit_concept_or_authority(rejected)["code"] == "uncertain_lineage"
