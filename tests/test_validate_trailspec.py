"""Tests for TrailSpec v1 and StepReceipt v1 validation and invariants."""

from __future__ import annotations

import copy
from typing import Any

import pytest
import yaml

from scripts.orchestration.validate_trailspec import (
    DEFAULT_EXAMPLE_TRAIL_PATH,
    STEP_RECEIPT_SCHEMA_PATH,
    TRAIL_SPEC_SCHEMA_PATH,
    TrailSpecValidationError,
    compute_trail_hash,
    validate_step_receipt_data,
    validate_trailspec,
    validate_trailspec_data,
)


def _get_happy_example_data() -> dict[str, Any]:
    return yaml.safe_load(DEFAULT_EXAMPLE_TRAIL_PATH.read_text(encoding="utf-8"))


_TRAILS_DIR = DEFAULT_EXAMPLE_TRAIL_PATH.parent
_ALL_SHIPPED_TRAILS = sorted(_TRAILS_DIR.glob("*.trail.yaml"))


def test_trails_dir_is_not_empty() -> None:
    """Guard the glob itself: an empty parametrization must fail, not silently pass."""
    assert _ALL_SHIPPED_TRAILS, f"no *.trail.yaml found under {_TRAILS_DIR}"


@pytest.mark.parametrize("trail_path", _ALL_SHIPPED_TRAILS, ids=lambda p: p.stem)
def test_every_shipped_trail_validates(trail_path) -> None:
    """Every trail shipped in scripts/config/trails/ must pass the validator,
    so a future draft cannot land unvalidated by editing only the yaml."""
    res = validate_trailspec(spec_path=trail_path)
    assert res["ok"] is True
    assert res["spec"]["trail_id"] == trail_path.name.removesuffix(".trail.yaml")
    assert res["spec"]["trail_hash"]


def _get_happy_step_receipt_data() -> dict[str, Any]:
    return {
        "schema_version": "step-receipt.v1",
        "trail_id": "rb3-pr-lifecycle",
        "trail_version": "1.0.0",
        "trail_hash": "918baac42f0682697ee9389a8b7b79361ba47770ef1c18fcf33e2731524fcfd1",
        "run_id": "run-20260727-001",
        "step_id": "request_review",
        "task_family": "infra-orchestration",
        "lineage_id": "lin-12345",
        "pr_head": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
        "lease_generation": 1,
        "predicate_exit": 0,
        "evidence_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "transition_taken": "success",
        "timestamp": "2026-07-27T02:00:00Z",
        "idempotency_key": "idempotency-key-001",
    }


def test_happy_path_example_trail() -> None:
    """Happy path: validate the example rb3-pr-lifecycle.trail.yaml."""
    res = validate_trailspec(spec_path=DEFAULT_EXAMPLE_TRAIL_PATH)
    assert res["ok"] is True
    assert res["spec"]["trail_id"] == "rb3-pr-lifecycle"
    assert res["spec"]["version"] == "1.0.0"
    assert res["spec"]["steps_count"] == 9
    assert len(res["spec"]["trail_hash"]) == 64


def test_happy_path_step_receipt() -> None:
    """Happy path: validate a valid StepReceipt instance."""
    receipt_data = _get_happy_step_receipt_data()
    res = validate_step_receipt_data(
        receipt_data, receipt_schema_path=STEP_RECEIPT_SCHEMA_PATH
    )
    assert res["ok"] is True
    assert res["step_id"] == "request_review"
    assert res["run_id"] == "run-20260727-001"


def test_negative_non_summon_step_lacks_predicate() -> None:
    """Negative invariant test: non-summon step without evidence_predicate fails validation."""
    data = _get_happy_example_data()
    # Corrupt a copy: remove evidence_predicate from mechanical step 'request_review'
    data["steps"][0]["evidence_predicate"] = None

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    err_msg = str(exc_info.value)
    assert "evidence_predicate" in err_msg
    assert "steps[0]" in err_msg or "request_review" in err_msg

    # Mutation check: restore original copy -> passes
    restored = _get_happy_example_data()
    res = validate_trailspec_data(restored, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)
    assert res["ok"] is True


def test_negative_dangling_transition() -> None:
    """Negative invariant test: dangling transition target fails validation."""
    data = _get_happy_example_data()
    # Corrupt a copy: set transition to non-existent step
    data["steps"][0]["transitions"]["success"] = "non_existent_step_123"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    err_msg = str(exc_info.value)
    assert "Dangling transition" in err_msg
    assert "non_existent_step_123" in err_msg

    # Mutation check: restore original copy -> passes
    restored = _get_happy_example_data()
    res = validate_trailspec_data(restored, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)
    assert res["ok"] is True


def test_negative_unknown_stop_code() -> None:
    """Negative invariant test: unknown stop_code not in 16-item contract list fails validation."""
    data = _get_happy_example_data()
    # Corrupt a copy: add an invalid stop code
    data["stop_codes"].append("STOP-FORBIDDEN-CUSTOM-CODE")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    err_msg = str(exc_info.value)
    assert "Unknown stop_code(s)" in err_msg
    assert "STOP-FORBIDDEN-CUSTOM-CODE" in err_msg

    # Mutation check: restore original copy -> passes
    restored = _get_happy_example_data()
    res = validate_trailspec_data(restored, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)
    assert res["ok"] is True


def test_negative_schema_violation() -> None:
    """Negative invariant test: schema violation (extra property, invalid seat) fails validation."""
    data = _get_happy_example_data()
    # Corrupt top level schema: forbidden property
    data["invalid_top_level_prop"] = 123

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    assert "TrailSpec schema violation" in str(exc_info.value)

    # Corrupt seat enum
    data2 = _get_happy_example_data()
    data2["seats"].append("invalid-seat-name")

    with pytest.raises(TrailSpecValidationError) as exc_info2:
        validate_trailspec_data(data2, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    assert "TrailSpec schema violation" in str(exc_info2.value)


def test_negative_step_receipt_schema_violation() -> None:
    """Negative test: StepReceipt with invalid hash pattern or missing field fails validation."""
    receipt_data = _get_happy_step_receipt_data()
    # Corrupt trail_hash pattern (short hash)
    receipt_data["trail_hash"] = "abc123short"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_step_receipt_data(
            receipt_data, receipt_schema_path=STEP_RECEIPT_SCHEMA_PATH
        )

    assert "StepReceipt schema violation" in str(exc_info.value)


def test_hash_stability() -> None:
    """Test TrailSpec content hash calculation and stability across YAML formatting changes."""
    data_orig = _get_happy_example_data()
    hash_orig = compute_trail_hash(data_orig)

    # 1. Formatting change: dump with different key sorting or spacing, re-parse dict
    yaml_formatted = yaml.dump(data_orig, sort_keys=True, indent=4)
    data_reparsed = yaml.safe_load(yaml_formatted)
    hash_reparsed = compute_trail_hash(data_reparsed)

    assert hash_orig == hash_reparsed, "Parsed document canonical JSON hash must be identical despite YAML formatting changes"

    # 2. Key order variation in dict copy
    data_reordered: dict[str, Any] = {}
    for key in reversed(list(data_orig.keys())):
        data_reordered[key] = copy.deepcopy(data_orig[key])
    hash_reordered = compute_trail_hash(data_reordered)

    assert hash_orig == hash_reordered, "Canonical JSON hash must be invariant under Python dict key ordering"

    # 3. Semantic content mutation -> MUST yield different hash
    data_mutated = _get_happy_example_data()
    data_mutated["title"] = "Mutated Title for Trail"
    hash_mutated = compute_trail_hash(data_mutated)

    assert hash_orig != hash_mutated, "Semantic mutation must alter canonical JSON hash"
