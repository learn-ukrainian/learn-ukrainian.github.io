"""Hostile contract tests for the #7427 held-out / Cycle007 firewall."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import freeze_phase3_scope_circularity_firewall as firewall


def _record(*, namespace: str = "independent", origin: str = "independent", candidate: str = "a") -> dict[str, str]:
    return {"candidate_id": candidate, "origin": origin, "namespace": namespace, "membership_sha256": "a" * 64, "component_sha256": "b" * 64, "independent_origin": "true"}


def _private_binding(root: Path, name: str = "binding.json") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    path = root / name
    path.write_text(json.dumps({"binding_version": "phase3_evaluation_private_binding_v1", "membership_sha256": "a" * 64, "component_graph_sha256": "b" * 64, "steward_role": "evaluation_steward"}), encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def test_generated_contract_is_exact_and_schema_valid() -> None:
    contract = firewall.build_contract()
    assert firewall.validate_contract_integrity(contract)
    schema = json.loads((firewall.DATA / "contracts/phase3_scope_circularity_firewall_v1.schema.json").read_text())
    Draft202012Validator(schema).validate(contract)
    assert contract["denominator"]["coverage_blocked_cells"] == 14
    assert contract["cycle007"]["private_binding_state"] == "UNBOUND"


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


def test_private_binding_rejects_unsafe_paths_and_accepts_opaque_safe_binding(tmp_path: Path) -> None:
    root = tmp_path / "private"
    binding = _private_binding(root)
    assert firewall.validate_private_runtime_binding(str(binding), private_root=root)["ok"]
    os.chmod(binding, 0o644)
    assert firewall.validate_private_runtime_binding(str(binding), private_root=root)["code"] == "private_path_unsafe"
    os.chmod(binding, 0o600)
    hard = root / "hard.json"
    os.link(binding, hard)
    assert firewall.validate_private_runtime_binding(str(hard), private_root=root)["code"] == "private_path_unsafe"
    hard.unlink()
    link = root / "link.json"
    link.symlink_to(binding)
    assert firewall.validate_private_runtime_binding(str(link), private_root=root)["code"] == "private_path_unsafe"


def test_unbound_and_graph_incomplete_batches_fail_with_zero_outputs() -> None:
    assert firewall.validate_private_runtime_binding(None)["code"] == "private_binding_unbound"
    result = firewall.validate_lineage_batch([{"candidate_id": "missing"}])
    assert result == {"ok": False, "code": "graph_incompleteness", "emitted": 0, "promoted": 0, "activated": 0}
