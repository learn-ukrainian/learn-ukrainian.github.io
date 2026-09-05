"""Resolved A2 metadata admits prerequisites, never completed dataset slots."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import _v4_synthetic_chain_fixture as chain
import pytest
from jsonschema import Draft202012Validator
from learn_ukrainian_v4_runtime import provenance, resources
from learn_ukrainian_v4_runtime import v4_stage_evidence as ev

SCHEMA = "data/projects/open_model_data/contracts/dataset_v4_a2_source_operation_admission_receipt_v1.schema.json"


def validator() -> Draft202012Validator:
    schema = json.loads((chain.ROOT / SCHEMA).read_bytes())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_packaged_schema_matches_current_asset_without_resealing_history() -> None:
    assert resources.read_bytes(SCHEMA) == (chain.ROOT / SCHEMA).read_bytes()
    spec = json.loads(resources.read_bytes(provenance.SPEC))
    assert all(
        binding["path"] != SCHEMA
        for receipt in spec["receipts"]
        for binding in receipt["bindings"].values()
    )
    provenance.verify_current_identity()


@pytest.mark.parametrize("assigned", [False, True])
def test_schema_valid_resolved_stratum_only_changes_prerequisites(tmp_path: Path, assigned: bool) -> None:
    chain.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    admission = tmp_path / "data/projects/open_model_data/admission"
    a2 = json.loads((admission / "dataset_v4_a2_source_operation_admission_receipt_v1.json").read_bytes())
    validator().validate(a2)
    assert a2["source_operation_ledger"] == chain.REAL_A2["source_operation_ledger"]
    assert a2["execution_counters"] == chain.REAL_A2["execution_counters"]
    assert a2["execution_counters"]["dataset_rows_emitted"] == 0
    assert [c for c in a2["stratum_coverage_map"] if c["stratum"] != "standard_correct"] == [
        c for c in chain.REAL_A2["stratum_coverage_map"] if c["stratum"] != "standard_correct"
    ]
    manifest = chain.assigned_manifest("standard_correct") if assigned else copy.deepcopy(chain.REAL_MANIFEST)
    (admission / "dataset_v4_pilot_slot_manifest_v1.json").write_text(json.dumps(manifest))
    eligibility = ev.stratum_eligibility(manifest, a2)
    selected = next(c for c in eligibility if c["stratum"] == "standard_correct")
    assert selected["rights_resolved"] is True
    assert selected["assigned"] is assigned
    assert selected["prerequisite_eligible"] is assigned
    assert sum(c["prerequisite_eligible"] for c in eligibility) == int(assigned)
    gate = chain.a6.check_arena_gate(tmp_path)
    assert gate["a5_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == (15 if assigned else 0)
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["arena_slice_ready"] is False
    assert gate["blocked_reason_code"] == (
        "eligible_slots_awaiting_this_stage_execution" if assigned else "no_slot_prerequisite_eligible"
    )
    if assigned:
        total = set(ev.all_frozen_slot_ids(manifest))
        assert len(total) == 100
        for stage, receipt in chain.run_chain_a6_through_a9(tmp_path).items():
            assert receipt[f"{stage}_completions"] == []
            residual = {r["subject_id"] for r in receipt[f"{stage}_residuals"]}
            assert residual == total
            ev.validate_partition(total, set(), residual, label=stage)
            assert receipt["execution_counters"]["dataset_rows_emitted"] == 0


@pytest.mark.parametrize("state", ["candidate_support_identified", "support_identified_with_residual", "source_incomplete"])
def test_unresolved_coverage_cannot_silently_drop_residuals(state: str) -> None:
    receipt = chain.resolved_a2_receipt("standard_correct")
    receipt["stratum_coverage_map"][0]["coverage_state"] = state
    assert list(validator().iter_errors(receipt))
    with pytest.raises(ValueError, match="carries no residual ids"):
        ev.stratum_eligibility(chain.REAL_MANIFEST, receipt)


def test_resolved_coverage_cannot_retain_residuals() -> None:
    receipt = copy.deepcopy(chain.REAL_A2)
    receipt["stratum_coverage_map"][0]["coverage_state"] = "resolved"
    assert list(validator().iter_errors(receipt))
    assert not ev.eligible_slot_ids(ev.stratum_eligibility(chain.assigned_manifest("standard_correct"), receipt))


def test_dangling_residual_reference_is_refused_by_consumer() -> None:
    receipt = copy.deepcopy(chain.REAL_A2)
    missing = receipt["stratum_coverage_map"][0]["residual_ids"][0]
    receipt["residuals"] = [r for r in receipt["residuals"] if r["residual_id"] != missing]
    validator().validate(receipt)
    with pytest.raises(ValueError, match="absent from A2's own residuals"):
        ev.stratum_eligibility(chain.REAL_MANIFEST, receipt)


def test_default_public_state_remains_zero_completed_100_residual_zero_emitted() -> None:
    validator().validate(chain.REAL_A2)
    assert not ev.eligible_slot_ids(ev.stratum_eligibility(chain.REAL_MANIFEST, chain.REAL_A2))
    receipt = chain.a6.build_receipt()
    chain.a6.validate_receipt_independently(receipt)
    assert receipt["a6_completions"] == []
    assert {r["subject_id"] for r in receipt["a6_residuals"]} == set(ev.all_frozen_slot_ids(chain.REAL_MANIFEST))
    assert len(receipt["a6_residuals"]) == 100
    assert receipt["execution_counters"]["dataset_rows_emitted"] == 0
