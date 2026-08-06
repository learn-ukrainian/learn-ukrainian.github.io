"""Deterministic tests for the Phase 3 v2 compatibility matrix."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

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
        "matrix_sha256": compatibility.sha256_file(compatibility.MATRIX_PATH),
        "inventory_count": 26,
        "invalidated_count": 22,
        "rebound_count": 1,
        "valid_count": 3,
        "source_authoring_blocked": True,
        "phase4_blocked": True,
    }


def test_matrix_rejects_v2_drift_semantic_reuse_and_missing_claim(tmp_path: Path) -> None:
    baseline = _matrix()
    cases = []
    v2_drift = copy.deepcopy(baseline)
    v2_drift["phase3_v2_contract_sha256"] = "0" * 64
    cases.append((v2_drift, "schema violation|v2 pin drift"))
    semantic_reuse = copy.deepcopy(baseline)
    semantic_reuse["inventory"][0]["disposition"] = "valid"  # type: ignore[index]
    semantic_reuse["inventory"][0]["machine_reason"] = "deterministic_nonsemantic_engine_valid_under_v2"  # type: ignore[index]
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
        "blocked": True,
        "reason": "v2_exclusive_role_independence_not_established",
    }
