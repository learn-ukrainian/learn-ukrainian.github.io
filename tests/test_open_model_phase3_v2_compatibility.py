"""Deterministic tests for the Phase 3 v2 compatibility matrix."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles
from scripts.projects.open_model_data import phase3_v2_compatibility as compatibility


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def _matrix() -> dict[str, object]:
    return json.loads(compatibility.MATRIX_PATH.read_text(encoding="utf-8"))


def test_tracked_matrix_is_complete_hash_bound_and_blocks_phase4() -> None:
    result = compatibility.verify()
    assert result == {
        "ok": True,
        "schema_version": "phase3_v2_compatibility_matrix_v1",
        "phase3_v2_contract_sha256": compatibility.V2_SHA256,
        "phase3_v2_1_amendment_sha256": compatibility.V2_1_AMENDMENT_SHA256,
        "phase3_v2_1_combined_contract_sha256": compatibility.V2_1_COMBINED_SHA256,
        "matrix_sha256": compatibility.sha256_file(compatibility.MATRIX_PATH),
        "inventory_count": 28,
        "invalidated_count": 21,
        "rebound_count": 4,
        "valid_count": 3,
        "role_graph_ready": True,
        "source_authoring_blocked": False,
        "phase4_blocked": True,
    }


def test_engine_inventory_is_the_complete_current_v2_1_runtime_schema_closure() -> None:
    matrix = _matrix()
    bindings = matrix["engine_bindings"]  # type: ignore[index]
    paths = {entry["logical_path"] for entry in bindings}  # type: ignore[index]
    assert paths == compatibility.ENGINE_PATHS
    assert len(bindings) == len(compatibility.ENGINE_PATHS) == 42
    assert all(entry["artifact_sha256"] for entry in bindings)  # type: ignore[index]
    assert all(not path.startswith("data/projects/open_model_data/evidence/") for path in paths)


def test_engine_inventory_rejects_missing_extra_unhashed_and_historical_v1_only_paths(tmp_path: Path) -> None:
    baseline = _matrix()
    cases: list[tuple[dict[str, object], str]] = []

    missing = copy.deepcopy(baseline)
    missing["engine_bindings"] = missing["engine_bindings"][1:]  # type: ignore[index]
    cases.append((missing, "schema violation|engine binding set drift"))

    extra = copy.deepcopy(baseline)
    extra["engine_bindings"].append(copy.deepcopy(extra["engine_bindings"][0]))  # type: ignore[index]
    cases.append((extra, "schema violation|engine binding set drift"))

    unhashed = copy.deepcopy(baseline)
    unhashed["engine_bindings"][0]["artifact_sha256"] = ""  # type: ignore[index]
    cases.append((unhashed, "schema violation|artifact hash drift"))

    historical = copy.deepcopy(baseline)
    historical["engine_bindings"][0]["logical_path"] = (  # type: ignore[index]
        "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json"
    )
    cases.append((historical, "schema violation|engine binding set drift"))

    for index, (value, pattern) in enumerate(cases):
        path = tmp_path / f"engine-matrix-{index}.json"
        _write(path, value)
        with pytest.raises(compatibility.CompatibilityError, match=pattern):
            compatibility.verify(path)


def test_matrix_rejects_v2_drift_semantic_reuse_and_missing_claim(tmp_path: Path) -> None:
    baseline = _matrix()
    cases = []
    v2_drift = copy.deepcopy(baseline)
    v2_drift["phase3_v2_contract_sha256"] = "0" * 64
    cases.append((v2_drift, "schema violation|v2 pin drift"))
    semantic_reuse = copy.deepcopy(baseline)
    semantic = next(item for item in semantic_reuse["inventory"] if item["artifact_class"] == "source_status")  # type: ignore[index]
    semantic["disposition"] = "valid"
    semantic["machine_reason"] = "deterministic_nonsemantic_engine_valid_under_v2"
    cases.append((semantic_reuse, "not invalidated"))
    missing_claim = copy.deepcopy(baseline)
    missing_claim["legacy_claims"] = missing_claim["legacy_claims"][:-1]  # type: ignore[index]
    cases.append((missing_claim, "schema violation|claim invalidation set drift"))
    for index, (value, pattern) in enumerate(cases):
        path = tmp_path / f"matrix-{index}.json"
        _write(path, value)
        with pytest.raises(compatibility.CompatibilityError, match=pattern):
            compatibility.verify(path)


def test_matrix_explicitly_invalidates_every_prohibited_legacy_claim() -> None:
    matrix = _matrix()
    claims = {item["claim_id"]: item for item in matrix["legacy_claims"]}  # type: ignore[index]
    assert set(claims) == set(compatibility.REQUIRED_CLAIMS)
    assert all(item["disposition"] == "invalidated" for item in claims.values())
    assert matrix["legacy_provenance"]["authority"] == "legacy_provenance_only_not_current_authority"  # type: ignore[index]


def test_pre_v2_role_contract_is_not_reused_as_independence_evidence() -> None:
    matrix = _matrix()
    role_contract = next(
        item
        for item in matrix["inventory"]  # type: ignore[index]
        if item["logical_path"].endswith("correction_protection_role_contract_v1.json")
    )
    assert role_contract["artifact_class"] == "role_contract_status"
    assert role_contract["disposition"] == "invalidated"
    assert role_contract["machine_reason"] == "pre_v2_role_contract_invalidated"
    assert matrix["source_authoring"] == {
        "blocked": False,
        "reason": "heldout_labels_frozen_source_transport_ready",
    }


def test_functional_role_ledger_has_exact_tasks_directed_edges_and_fail_closed_status() -> None:
    result = functional_roles.verify()
    assert result["role_count"] == 10
    assert result["role_graph_ready"] is True
    assert result["source_authoring_blocked"] is True
    ledger = functional_roles.read_json(functional_roles.LEDGER_PATH)
    roles = {item["role_id"]: item for item in ledger["functional_roles"]}
    assert {item["task_id"] for item in roles.values()} == set(functional_roles.ROLE_TASKS.values())
    assert roles["rule_author_extractor"]["model_family"] == "gemini"
    assert roles["ukrainian_source_reviewer"]["model_family"] == "xai"
    assert roles["cross_family_code_infra_reviewer"]["model_family"] != "openai"
    assert functional_roles.tasks_conflict(
        ledger,
        functional_roles.ROLE_TASKS["rule_author_extractor"],
        functional_roles.ROLE_TASKS["ukrainian_source_reviewer"],
    )
    assert not functional_roles.tasks_conflict(
        ledger,
        functional_roles.ROLE_TASKS["scope_circularity_critic"],
        functional_roles.ROLE_TASKS["disposition_auditor"],
    )


def test_functional_role_ledger_rejects_task_lane_graph_and_cycle_drift() -> None:
    baseline = functional_roles.read_json(functional_roles.LEDGER_PATH)
    cases: list[tuple[dict[str, object], str]] = []
    duplicate_task = copy.deepcopy(baseline)
    duplicate_task["functional_roles"][1]["task_id"] = duplicate_task["functional_roles"][0]["task_id"]  # type: ignore[index]
    cases.append((duplicate_task, "schema violation|task IDs"))
    self_edge = copy.deepcopy(baseline)
    self_edge["task_conflict_graph"]["edges"][0]["consumer_task_id"] = self_edge["task_conflict_graph"]["edges"][0]["producer_task_id"]  # type: ignore[index]
    cases.append((self_edge, "schema violation|graph edge drift|self-review"))
    lane_drift = copy.deepcopy(baseline)
    lane_drift["functional_roles"][1]["model_family"] = "gemini"  # type: ignore[index]
    cases.append((lane_drift, "functional role binding drift|sanctioned capability lane"))
    cycle_drift = copy.deepcopy(baseline)
    cycle_drift["evaluation_cycle"]["voided_cycle_may_not_resume"] = False  # type: ignore[index]
    cases.append((cycle_drift, "schema violation|evaluation cycle"))
    for value, pattern in cases:
        with pytest.raises(functional_roles.FunctionalRoleError, match=pattern):
            functional_roles.verify_value(value)
