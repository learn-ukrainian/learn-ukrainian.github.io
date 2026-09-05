"""V4 A6 safe arena: a label-blind, author-blind, hash-keyed packet plus a
no-self-vote / leave-one-out disagreement receipt, bound to the merged A5
evidence receipt, the frozen V4 pilot slot manifest, and the V4 SHA.

Everything here runs against public artifacts only -- no ``batch_state/``,
no A4 private ledger, no held-out membership -- so this suite passes in a
fresh checkout.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import _v4_synthetic_chain_fixture as fixture
import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_arena_receipt as arena

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a6_blind_arena_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a6_blind_arena_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A4_RECEIPT_PATH = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RECEIPT_PATH = ADMISSION / "dataset_v4_a5_evidence_enrichment_receipt_v1.json"
MANIFEST_PATH = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

REAL_RECEIPT = json.loads(RECEIPT.read_text(encoding="utf-8"))
REAL_A2_RECEIPT = json.loads(A2_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A4_RECEIPT = json.loads(A4_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_A5_RECEIPT = json.loads(A5_RECEIPT_PATH.read_text(encoding="utf-8"))
REAL_MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

FORBIDDEN_KEYS = a6.FORBIDDEN_KEYS
FORBIDDEN_SUBSTRINGS = a6.FORBIDDEN_SUBSTRINGS


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def _write_artifact(path: Path, override: dict | None, real_path: Path) -> None:
    """Writes ``override`` if given, else the real file's exact on-disk
    bytes (never a ``json.dumps`` round-trip of the already-parsed dict,
    which would silently change the byte formatting and break any binding
    hash computed against the real file)."""
    if override is None:
        path.write_bytes(real_path.read_bytes())
    else:
        path.write_text(json.dumps(override))


def _write_receipt_tree(tmp_path: Path, *, a2=None, a4=None, a5=None, manifest=None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    _write_artifact(admission_dir / "dataset_v4_a2_source_operation_admission_receipt_v1.json", a2, A2_RECEIPT_PATH)
    _write_artifact(admission_dir / "dataset_v4_a4_deterministic_extraction_receipt_v1.json", a4, A4_RECEIPT_PATH)
    _write_artifact(admission_dir / "dataset_v4_a5_evidence_enrichment_receipt_v1.json", a5, A5_RECEIPT_PATH)
    _write_artifact(admission_dir / "dataset_v4_pilot_slot_manifest_v1.json", manifest, MANIFEST_PATH)
    # A5's (and this module's own) bindings include a path to their own
    # implementation script under scripts/ -- a symlink would resolve
    # outside tmp_path and trip the path-escape refusal, so copy the one
    # subtree that carries every V4 module referenced by a binding.
    scripts_dir = tmp_path / "scripts/projects/open_model_data"
    if not scripts_dir.exists():
        shutil.copytree(ROOT / "scripts/projects/open_model_data", scripts_dir)
    return tmp_path


# --- frozen 100-slot denominator ---------------------------------------------


def test_a6_frozen_slot_denominator_reproduces_the_locked_100_slot_series() -> None:
    strata = a6.frozen_slot_strata(REAL_MANIFEST)
    all_ids = a6.all_frozen_slot_ids(REAL_MANIFEST)
    assert len(all_ids) == 100
    assert len(set(all_ids)) == 100
    assert {s["stratum"]: s["count"] for s in strata} == {
        "standard_correct": 15,
        "correction": 15,
        "literary": 15,
        "dialect_regional": 15,
        "archaic_historical": 15,
        "mixing": 10,
        "quotation_interference": 10,
        "abstention": 5,
    }
    assert all_ids[0] == "v4p-standard-correct-001"


# --- arena gate ----------------------------------------------------------------


def test_a6_gate_against_the_real_production_artifacts_stays_closed_today() -> None:
    gate = a6.check_arena_gate()
    assert gate["a5_receipt_valid"] is True
    # The frozen manifest is still UNASSIGNED_PENDING_A2_A3 for every stratum and
    # A2 still carries 8 unresolved rights/coverage residuals -- so the honest
    # gate state today is closed. If this ever flips to True, it means a real
    # A2/A3 slot assignment landed and the checked-in receipt must be regenerated.
    assert gate["slots_prerequisite_eligible"] == 0
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["arena_slice_ready"] is False
    assert gate["blocked_reason_code"] == "no_slot_prerequisite_eligible"


def test_a6_gate_closed_when_a_required_public_artifact_is_missing(tmp_path: Path) -> None:
    _write_receipt_tree(tmp_path)
    (tmp_path / "data/projects/open_model_data/admission/dataset_v4_a5_evidence_enrichment_receipt_v1.json").unlink()
    gate = a6.check_arena_gate(tmp_path)
    assert gate["arena_slice_ready"] is False
    assert gate["blocked_reason_code"] == "required_public_artifact_missing:a5_receipt"


def test_a6_gate_closed_when_a5_receipt_is_invalid(tmp_path: Path) -> None:
    forged = copy.deepcopy(REAL_A5_RECEIPT)
    forged["bindings"]["a4_deterministic_extraction"]["sha256"] = "0" * 64
    _write_receipt_tree(tmp_path, a5=forged)
    gate = a6.check_arena_gate(tmp_path)
    assert gate["a5_receipt_valid"] is False
    assert gate["blocked_reason_code"] == "upstream_receipt_invalid"


def test_a6_gate_reports_prerequisite_eligibility_without_stubbing_any_validator(tmp_path: Path) -> None:
    """Prerequisite eligibility (A2 rights resolved + manifest assignment) is
    a real, live-validated fact -- never behind a stubbed validator. This
    also proves eligibility is not completion: even with one whole stratum
    eligible, ``arena_slice_ready`` stays false because A6 has no positive
    ``a6_completions`` evidence (no execution mechanism exists yet). See
    ``_v4_synthetic_chain_fixture`` for why the fixture only resolves one
    stratum, not all eight (A4/A5's own residual cross-checks are not
    root-parametric -- fully resolving A2 would desync them)."""
    fixture.build_synthetic_chain_root(tmp_path, resolved_stratum="standard_correct")
    gate = a6.check_arena_gate(tmp_path)
    assert gate["a5_receipt_valid"] is True
    assert gate["slots_prerequisite_eligible"] == 15
    assert gate["slots_stage_complete"] == 0
    assert gate["slots_residual"] == 100
    assert gate["arena_slice_ready"] is False
    assert gate["blocked_reason_code"] == "eligible_slots_awaiting_this_stage_execution"


# --- A6 residuals ----------------------------------------------------------------


def test_a6_residuals_are_one_typed_independence_unavailable_entry_per_frozen_slot() -> None:
    gate = a6.check_arena_gate()
    residuals = a6.derive_a6_slot_residuals(REAL_MANIFEST, REAL_A2_RECEIPT, gate)
    assert len(residuals) == 100
    assert len({r["residual_id"] for r in residuals}) == 100
    assert {r["subject_id"] for r in residuals} == set(a6.all_frozen_slot_ids(REAL_MANIFEST))
    assert all(r["reason_code"] == "independence_unavailable" for r in residuals)
    assert all(r["stage"] == "A6" for r in residuals)
    # Never a duplicated or synthesized vote (a "label" field) standing in for
    # the missing independent view -- only a typed, textual residual.
    assert not any("label" in r for r in residuals)


# --- receipt assembly and independent verification ------------------------------


def test_a6_receipt_validates_independently_against_the_real_public_artifacts() -> None:
    assert a6.validate_receipt_independently(REAL_RECEIPT) is None


def test_a6_receipt_matches_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(REAL_RECEIPT))
    assert not errors, errors[0].message if errors else None


def test_a6_receipt_binds_v4_sha_and_control_surfaces() -> None:
    assert REAL_RECEIPT["controlling_outcome_sha256"] == V4_SHA256
    assert REAL_RECEIPT["control_surfaces"] == {
        "public_control_issue": 7423,
        "pilot_child_issue": 7430,
        "private_operational_board": 622,
    }
    assert REAL_RECEIPT["bindings"]["a5_evidence_enrichment"]["sha256"] == a6.sha256_file(A5_RECEIPT_PATH)
    assert REAL_RECEIPT["bindings"]["pilot_slot_manifest"]["sha256"] == a6.sha256_file(MANIFEST_PATH)


def test_a6_receipt_carries_forward_every_a2_a4_a5_residual_unresolved() -> None:
    assert {e["residual_id"] for e in REAL_RECEIPT["a2_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A2_RECEIPT["residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a4_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A4_RECEIPT["a4_residuals"]}
    assert {e["residual_id"] for e in REAL_RECEIPT["a5_residuals_carried_forward"]} == {e["residual_id"] for e in REAL_A5_RECEIPT["a5_residuals"]}
    assert all(e["status"] == "unresolved_carried_to_a6" for e in REAL_RECEIPT["a2_residuals_carried_forward"])
    assert all(e["status"] == "unresolved_carried_to_a6" for e in REAL_RECEIPT["a4_residuals_carried_forward"])
    assert all(e["status"] == "unresolved_carried_to_a6" for e in REAL_RECEIPT["a5_residuals_carried_forward"])


def test_a6_receipt_does_not_claim_arena_slice_ready_while_the_gate_is_closed() -> None:
    assert REAL_RECEIPT["arena_gate"]["arena_slice_ready"] is False
    assert REAL_RECEIPT["status"] != "ARENA_SLICE_READY"
    assert REAL_RECEIPT["execution_counters"]["slots_prerequisite_eligible"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_stage_complete"] == 0
    assert REAL_RECEIPT["execution_counters"]["slots_residual"] == 100


def test_a6_receipt_eligibility_all_false_and_zero_rows_emitted() -> None:
    assert REAL_RECEIPT["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert REAL_RECEIPT["execution_counters"]["dataset_rows_emitted"] == 0
    assert REAL_RECEIPT["execution_counters"]["live_proposals_run"] == 0
    assert REAL_RECEIPT["execution_counters"]["candidates_voted"] == 0
    assert REAL_RECEIPT["safety_assertions"]["rows_not_admitted"] is True
    assert all(v is False for k, v in REAL_RECEIPT["safety_assertions"].items() if k != "rows_not_admitted")


def test_a6_receipt_never_names_source_text_a_held_out_family_or_a_plaintext_source_id() -> None:
    keys = _all_keys(REAL_RECEIPT)
    assert not keys & FORBIDDEN_KEYS
    serialized = json.dumps(REAL_RECEIPT, ensure_ascii=False, sort_keys=True)
    assert not any(needle in serialized for needle in FORBIDDEN_SUBSTRINGS)
    # Slot IDs are frozen public strings from the manifest -- never a real
    # source_unit_id or its commitment hash.
    assert REAL_RECEIPT["a6_residuals"][0]["subject_id"].startswith("v4p-")


def test_a6_packet_reuses_the_live_arena_engine_constants_never_a_stale_copy() -> None:
    packet = REAL_RECEIPT["packet"]
    assert packet["proposal_schema_version"] == arena.PROPOSAL_SCHEMA_VERSION
    assert packet["begin_marker"] == arena.BEGIN_MARKER
    assert packet["end_marker"] == arena.END_MARKER
    assert packet["quarantine_disposition"] == arena.QUARANTINE
    assert packet["self_vote_forbidden"] is True
    assert packet["format_retry_policy"] == "one_format_only_retry_then_recorded_failure"
    assert packet["aggregation"] == "leave_one_out_ballots_only_never_self_report"


def test_a6_bindings_hash_to_disk_for_every_bound_artifact() -> None:
    from learn_ukrainian_v4_runtime.resources import resource_root

    for name, binding in REAL_RECEIPT["bindings"].items():
        path = resource_root() / (
            "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
            if binding["path"].startswith("scripts/") else binding["path"]
        )
        assert path.is_file(), name
        assert a6.sha256_file(path) == binding["sha256"], name


# --- fail-closed on tampering ----------------------------------------------------


def test_a6_refuses_a_tampered_binding_hash() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["bindings"]["a2_source_operation_admission"]["sha256"] = "0" * 64
    with pytest.raises(a6.ArenaWiringError):
        a6.validate_receipt_independently(receipt)


def test_a6_refuses_a_forged_arena_slice_ready_claim() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["status"] = "ARENA_SLICE_READY"
    receipt["arena_gate"] = {**receipt["arena_gate"], "arena_slice_ready": True, "blocked_reason_code": None}
    with pytest.raises(a6.ArenaWiringError):
        a6.validate_receipt_independently(receipt)


def test_a6_refuses_a_dropped_a2_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a2_residuals_carried_forward"].pop()
    with pytest.raises(a6.ArenaWiringError):
        a6.validate_receipt_independently(receipt)


def test_a6_refuses_a_missing_frozen_slot_residual() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["a6_residuals"].pop()
    with pytest.raises(a6.ArenaWiringError):
        a6.validate_receipt_independently(receipt)


def test_a6_refuses_a_duplicate_vote_standing_in_for_a_missing_independent_view() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    forged = dict(receipt["a6_residuals"][0])
    forged["reason_code"] = "duplicate_vote_substituted"
    receipt["a6_residuals"][0] = forged
    with pytest.raises(a6.ArenaWiringError):
        a6.validate_receipt_independently(receipt)


def test_a6_schema_rejects_a_leaked_gold_label_value() -> None:
    receipt = copy.deepcopy(REAL_RECEIPT)
    receipt["eligibility"]["gold"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(receipt))
    assert errors


def test_a6_gold_key_is_a_frozen_false_eligibility_flag_never_a_real_label() -> None:
    # "gold" is deliberately excluded from FORBIDDEN_KEYS (unlike A5) because it
    # is the name of this receipt's own always-false eligibility flag, matching
    # v4_arena_receipt.build_receipts' own {"gold": False, ...} shape.
    assert "gold" not in FORBIDDEN_KEYS
    assert REAL_RECEIPT["eligibility"]["gold"] is False


# --- the shared engine, exercised only via a synthetic, non-corpus fixture ------


def _engine_self_test_fixture() -> dict[str, object]:
    """A small, frozen, synthetic fixture -- distinct candidate/case IDs, no
    corpus content -- proving *this project's* packet metadata (begin/end
    markers, proposal schema, quarantine constant) is the same thing the
    shared engine actually enforces for no-self-vote and leave-one-out."""
    packet = REAL_RECEIPT["packet"]
    cases = ["engine-self-test-case-01", "engine-self-test-case-02"]
    candidates = {
        "engine-self-test-candidate-1": {"provider_id": "engine-self-test-provider-1", "route_id": "engine-self-test-route-1"},
        "engine-self-test-candidate-2": {"provider_id": "engine-self-test-provider-2", "route_id": "engine-self-test-route-2"},
    }

    def proposal(candidate_id: str, provider_id: str, labels: list[str]) -> str:
        return f"{packet['begin_marker']}\n" + json.dumps(
            {
                "schema_version": packet["proposal_schema_version"],
                "candidate_id": candidate_id,
                "provider_id": provider_id,
                "cases": [{"case_id": cid, "label": label, "tags": []} for cid, label in zip(cases, labels, strict=True)],
            },
            sort_keys=True,
            separators=(",", ":"),
        ) + f"\n{packet['end_marker']}"

    return {
        "outcome_sha256": V4_SHA256,
        "prompt_sha256": "b" * 64,
        "case_ids": cases,
        "route_denominator": ["engine-self-test-route-1", "engine-self-test-route-2"],
        "candidate_map": candidates,
        "provider_outputs": {
            "engine-self-test-candidate-1": proposal("engine-self-test-candidate-1", "engine-self-test-provider-1", ["agree", "agree"]),
            "engine-self-test-candidate-2": proposal("engine-self-test-candidate-2", "engine-self-test-provider-2", ["agree", "disagree"]),
        },
        "ballots": [
            {"voter_candidate_id": "engine-self-test-candidate-1", "candidate_id": "engine-self-test-candidate-2", "case_id": cid, "label": "agree"}
            for cid in cases
        ] + [
            {"voter_candidate_id": "engine-self-test-candidate-2", "candidate_id": "engine-self-test-candidate-1", "case_id": cid, "label": "agree"}
            for cid in cases
        ] + [
            # A self-vote must never be counted -- this one must surface as a residual.
            {"voter_candidate_id": "engine-self-test-candidate-1", "candidate_id": "engine-self-test-candidate-1", "case_id": cases[0], "label": "agree"}
        ],
        "allowed_labels": ["agree", "disagree"],
        "allowed_tags": ["synthetic"],
    }


def test_a6_engine_self_vote_is_forbidden_and_quarantine_holds() -> None:
    fixture = _engine_self_test_fixture()
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    public = receipts["public"]
    assert "SELF_VOTE" in {r["code"] for r in public["residuals"]}
    assert all(case["disposition"] == arena.QUARANTINE for case in public["cases"])
    assert public["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}


def test_a6_engine_leave_one_out_never_mixes_in_a_candidates_own_self_report() -> None:
    fixture = _engine_self_test_fixture()
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    second_case = receipts["public"]["cases"][1]
    assert second_case["case_id"] == "engine-self-test-case-02"
    loo = {item["candidate_id"]: item for item in second_case["leave_one_out_ballots"]}
    # candidate-2's own self-reported label for case 2 is "disagree", but its
    # peer's (candidate-1) leave-one-out ballot is "agree" -- the two must not
    # be conflated.
    assert loo["engine-self-test-candidate-2"]["label_counts"] == {"agree": 1}
    own_report = next(o for o in second_case["candidate_outputs"] if o["candidate_id"] == "engine-self-test-candidate-2")
    assert own_report["label"] == "disagree"
