"""Tests for TrailSpec v1/v1.1 validation and receipt-contract invariants."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
import yaml

from scripts.orchestration.red_ci_known_failures import VALID_STOP_CODES
from scripts.orchestration.validate_trailspec import (
    COMMAND_RECEIPT_SCHEMA_PATH,
    DEFAULT_DECISION_TABLES_PATH,
    DEFAULT_EXAMPLE_TRAIL_PATH,
    STEP_RECEIPT_SCHEMA_PATH,
    STEP_RECEIPT_V11_SCHEMA_PATH,
    TRAIL_SPEC_SCHEMA_PATH,
    TRAIL_SPEC_V11_SCHEMA_PATH,
    TrailSpecValidationError,
    compute_command_receipt_digest,
    compute_trail_hash,
    validate_command_receipt_data,
    validate_decision_tables,
    validate_decision_tables_data,
    validate_step_receipt_data,
    validate_trail_table_refs,
    validate_trailspec,
    validate_trailspec_data,
)


def _get_happy_example_data() -> dict[str, Any]:
    return yaml.safe_load(DEFAULT_EXAMPLE_TRAIL_PATH.read_text(encoding="utf-8"))


_TRAILS_DIR = DEFAULT_EXAMPLE_TRAIL_PATH.parent
_ALL_SHIPPED_TRAILS = sorted(_TRAILS_DIR.glob("*.trail.yaml"))

# Every draft the T2 initiative has shipped so far, by trail_id. A deleted or renamed
# draft must FAIL this list, not silently shrink the glob (review finding on #5886:
# the glob-only guard passed as long as ANY trail remained).
REQUIRED_TRAIL_IDS = {
    "rb1-cold-start",
    "rb2-dispatch-loop",
    "rb3-pr-lifecycle",
    "rb4-red-ci-triage",
    "rb5-session-close",
    "rb6-estate-probes",
}


def test_trails_dir_is_not_empty() -> None:
    """Guard the glob itself: an empty parametrization must fail, not silently pass."""
    assert _ALL_SHIPPED_TRAILS, f"no *.trail.yaml found under {_TRAILS_DIR}"


def test_required_trail_drafts_present() -> None:
    """Every registered draft must exist on disk — a missing draft is a failure even
    while other trails keep the glob non-empty."""
    found_ids = {p.name.removesuffix(".trail.yaml") for p in _ALL_SHIPPED_TRAILS}
    missing = REQUIRED_TRAIL_IDS - found_ids
    assert not missing, f"required trail drafts missing from {_TRAILS_DIR}: {sorted(missing)}"


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


def _get_happy_v11_trail_data() -> dict[str, Any]:
    """Small, complete v1.1 trail fixture with receipt-only predicates."""
    return {
        "schema_version": "trailspec.v1.1",
        "trail_id": "v11-contract-fixture",
        "version": "1.1.0",
        "title": "TrailSpec v1.1 contract fixture",
        "seats": ["kimi"],
        "parameters": {"issue_number": "integer"},
        "steps": [
            {
                "step_id": "observe_issue",
                "intent": "Observe the configured issue once.",
                "command": {
                    "adapter": "shell",
                    "argv": ["issue-observer", "--issue", "{issue_number}"],
                    "environment": {"TRAIL_INVOCATION_ID": "{invocation_id}"},
                    "timeout_seconds": 30,
                    "mutation_class": "observe",
                    "outcome_decoder": {"source": "stdout-token"},
                },
                "transitions": {
                    "accepted": {
                        "target": "complete",
                        "evidence": {
                            "predicate_id": "accepted-outcome",
                            "clauses": [
                                {
                                    "source": "command_receipt",
                                    "field": "actor_outcome",
                                    "op": "eq",
                                    "value": "accepted",
                                },
                                {
                                    "source": "command_receipt",
                                    "field": "exit_code",
                                    "op": "eq",
                                    "value": 0,
                                },
                            ],
                        },
                    },
                    "refused": {
                        "target": "complete",
                        "evidence": {
                            "predicate_id": "refused-outcome",
                            "clauses": [
                                {
                                    "source": "command_receipt",
                                    "field": "actor_outcome",
                                    "op": "eq",
                                    "value": "refused",
                                }
                            ],
                        },
                    },
                },
                "blocked_on": None,
            }
        ],
        "stop_codes": ["STOP-unknown"],
        "terminal_outcomes": ["complete"],
    }


def _get_happy_command_receipt_data(trail: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "command-receipt.v1",
        "invocation_id": "3e99cd0b-6718-48a9-a2c9-9658a650bc55",
        "run_id": "run-20260728-001",
        "trail_id": trail["trail_id"],
        "trail_version": trail["version"],
        "trail_hash": compute_trail_hash(trail),
        "step_id": "observe_issue",
        "resolved_command_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "actor_outcome": "accepted",
        "exit_code": 0,
        "stdout_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "artifact_digests": {},
        "prepared_at": "2026-07-28T10:00:00Z",
        "completed_at": "2026-07-28T10:00:01Z",
        "status": "complete",
    }


def _get_happy_v11_step_receipt_data(
    trail: dict[str, Any], command_receipt: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "step-receipt.v1.1",
        "trail_id": trail["trail_id"],
        "trail_version": trail["version"],
        "trail_hash": compute_trail_hash(trail),
        "run_id": command_receipt["run_id"],
        "step_id": command_receipt["step_id"],
        "task_family": "infra-orchestration",
        "lineage_id": "lin-12345",
        "pr_head": None,
        "lease_generation": 1,
        "predicate_exit": 0,
        "evidence_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "transition_taken": "accepted",
        "timestamp": "2026-07-28T10:00:02Z",
        "idempotency_key": "idempotency-key-001",
        "invocation_id": command_receipt["invocation_id"],
        "command_receipt_digest": compute_command_receipt_digest(command_receipt),
        "actor_outcome": command_receipt["actor_outcome"],
        "predicate_id": "accepted-outcome",
    }


def test_happy_path_example_trail() -> None:
    """Happy path: validate the example rb3-pr-lifecycle.trail.yaml."""
    res = validate_trailspec(spec_path=DEFAULT_EXAMPLE_TRAIL_PATH)
    assert res["ok"] is True
    assert res["spec"]["trail_id"] == "rb3-pr-lifecycle"
    assert res["spec"]["version"] == "2.0.3"
    assert res["spec"]["steps_count"] == 14
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


def test_v1_is_schema_valid_but_execution_ineligible() -> None:
    """v1 can be inspected and hashed, but its prose predicates cannot be executed."""
    res = validate_trailspec_data(_get_happy_example_data())

    assert res["ok"] is True
    assert res["execution_eligible"] is False
    assert "must refuse v1 execution and closure" in res["execution_refusal"]


def test_v11_happy_path_binds_command_and_step_receipts(tmp_path) -> None:
    """v1.1 validates the command/receipt chain and reports execution eligibility."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    step_receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)

    trail_path = tmp_path / "trail.json"
    command_receipt_path = tmp_path / "command-receipt.json"
    step_receipt_path = tmp_path / "step-receipt.json"
    trail_path.write_text(json.dumps(trail), encoding="utf-8")
    command_receipt_path.write_text(json.dumps(command_receipt), encoding="utf-8")
    step_receipt_path.write_text(json.dumps(step_receipt), encoding="utf-8")

    res = validate_trailspec(
        spec_path=trail_path,
        receipt_path=step_receipt_path,
        command_receipt_path=command_receipt_path,
    )

    assert res["ok"] is True
    assert res["spec"]["execution_eligible"] is True
    assert res["receipt"]["schema_version"] == "step-receipt.v1.1"
    assert res["command_receipt"]["status"] == "complete"


@pytest.mark.parametrize(
    "field_name",
    ["invocation_id", "command_receipt_digest", "actor_outcome", "predicate_id"],
)
def test_negative_v11_receipt_additions_are_required(field_name: str) -> None:
    """Mutation check: every required v1.1 receipt addition binds its command."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    del receipt[field_name]

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_step_receipt_data(receipt, receipt_schema_path=STEP_RECEIPT_V11_SCHEMA_PATH)

    assert field_name in str(exc_info.value)


def test_negative_v11_optional_authority_receipt_must_be_a_digest() -> None:
    """Mutation check: optional authority evidence cannot become unbound prose."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    receipt["authority_receipt_digest"] = "approval-in-chat"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_step_receipt_data(receipt, receipt_schema_path=STEP_RECEIPT_V11_SCHEMA_PATH)

    assert "authority_receipt_digest" in str(exc_info.value)


def test_negative_v11_receipt_transition_taken_must_be_a_label(tmp_path) -> None:
    """Mutation check: a target value cannot be substituted for transition_taken."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    receipt["transition_taken"] = "complete"  # target, not the "accepted" label

    trail_path = tmp_path / "trail.json"
    receipt_path = tmp_path / "receipt.json"
    trail_path.write_text(json.dumps(trail), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec(spec_path=trail_path, receipt_path=receipt_path)

    assert "transition_taken must be a transition label" in str(exc_info.value)


def test_negative_v11_command_receipt_actor_must_bind(tmp_path) -> None:
    """Mutation check: an actor outcome from another command receipt cannot bind a step."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    command_receipt["actor_outcome"] = "refused"

    trail_path = tmp_path / "trail.json"
    command_receipt_path = tmp_path / "command-receipt.json"
    receipt_path = tmp_path / "step-receipt.json"
    trail_path.write_text(json.dumps(trail), encoding="utf-8")
    command_receipt_path.write_text(json.dumps(command_receipt), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec(
            spec_path=trail_path,
            receipt_path=receipt_path,
            command_receipt_path=command_receipt_path,
        )

    assert "actor_outcome" in str(exc_info.value)


def test_negative_v11_command_receipt_digest_must_bind(tmp_path) -> None:
    """Mutation check: a valid digest for a different receipt cannot bind a step."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    receipt["command_receipt_digest"] = "0" * 64

    trail_path = tmp_path / "trail.json"
    command_receipt_path = tmp_path / "command-receipt.json"
    receipt_path = tmp_path / "step-receipt.json"
    trail_path.write_text(json.dumps(trail), encoding="utf-8")
    command_receipt_path.write_text(json.dumps(command_receipt), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec(
            spec_path=trail_path,
            receipt_path=receipt_path,
            command_receipt_path=command_receipt_path,
        )

    assert "command_receipt_digest" in str(exc_info.value)


def test_negative_v11_command_receipt_requires_complete_exit_status() -> None:
    """Mutation check: a complete receipt cannot hide a missing exit code."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    command_receipt["exit_code"] = None

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_command_receipt_data(
            command_receipt, receipt_schema_path=COMMAND_RECEIPT_SCHEMA_PATH
        )

    assert "exit_code" in str(exc_info.value)


def test_negative_v11_requires_invocation_environment() -> None:
    """Mutation check: every command needs the runner-owned invocation environment."""
    trail = _get_happy_v11_trail_data()
    del trail["steps"][0]["command"]["environment"]["TRAIL_INVOCATION_ID"]

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "TRAIL_INVOCATION_ID" in str(exc_info.value)


def test_negative_v11_typed_primitive_requires_invocation_flag() -> None:
    """Mutation check: typed primitives receive both required invocation channels."""
    trail = _get_happy_v11_trail_data()
    command = trail["steps"][0]["command"]
    command["adapter"] = "typed-primitive"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "--invocation-id" in str(exc_info.value)


def test_negative_v11_rejects_undeclared_or_shell_interpolated_parameters() -> None:
    """Mutation checks: parameter values are declared and never interpolated into -c."""
    trail = _get_happy_v11_trail_data()
    trail["steps"][0]["command"]["argv"][2] = "{unknown_parameter}"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "Undeclared command parameter" in str(exc_info.value)

    shell_interpolated = _get_happy_v11_trail_data()
    shell_interpolated["steps"][0]["command"]["argv"] = [
        "sh",
        "-c",
        "observer --issue {issue_number}",
    ]
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(
            shell_interpolated, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH
        )

    assert "Unquoted parameter interpolation prohibited" in str(exc_info.value)

    untyped = _get_happy_v11_trail_data()
    untyped["parameters"]["issue_number"] = "free-form-prose"
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(untyped, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "TrailSpec schema violation" in str(exc_info.value)


def test_negative_v11_predicate_must_be_unique_and_receipt_only() -> None:
    """Mutation checks: transition predicates cannot collide or execute a command."""
    trail = _get_happy_v11_trail_data()
    trail["steps"][0]["transitions"]["refused"]["evidence"]["predicate_id"] = (
        "accepted-outcome"
    )

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "Exactly-one-predicate rule" in str(exc_info.value)

    command_predicate = _get_happy_v11_trail_data()
    command_predicate["steps"][0]["transitions"]["accepted"]["evidence"]["clauses"][
        0
    ]["source"] = "shell-command"
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(
            command_predicate, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH
        )

    assert "TrailSpec schema violation" in str(exc_info.value)


@pytest.mark.parametrize("case", ["zero", "multiple"])
def test_negative_v11_command_receipt_must_match_exactly_one_predicate(
    tmp_path, case: str
) -> None:
    """Mutation check: zero or multiple matching predicates park as STOP-unknown."""
    trail = _get_happy_v11_trail_data()
    command_receipt = _get_happy_command_receipt_data(trail)
    step_receipt = _get_happy_v11_step_receipt_data(trail, command_receipt)
    if case == "zero":
        command_receipt["actor_outcome"] = "indeterminate"
        step_receipt["actor_outcome"] = "indeterminate"
        step_receipt["command_receipt_digest"] = compute_command_receipt_digest(command_receipt)
    else:
        refused_clause = trail["steps"][0]["transitions"]["refused"]["evidence"][
            "clauses"
        ][0]
        refused_clause.update({"field": "exit_code", "value": 0})
        command_receipt["trail_hash"] = compute_trail_hash(trail)
        step_receipt["trail_hash"] = compute_trail_hash(trail)
        step_receipt["command_receipt_digest"] = compute_command_receipt_digest(command_receipt)

    trail_path = tmp_path / "trail.json"
    command_receipt_path = tmp_path / "command-receipt.json"
    step_receipt_path = tmp_path / "step-receipt.json"
    trail_path.write_text(json.dumps(trail), encoding="utf-8")
    command_receipt_path.write_text(json.dumps(command_receipt), encoding="utf-8")
    step_receipt_path.write_text(json.dumps(step_receipt), encoding="utf-8")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec(
            spec_path=trail_path,
            receipt_path=step_receipt_path,
            command_receipt_path=command_receipt_path,
        )

    assert "Exactly-one-predicate match rule" in str(exc_info.value)
    assert "STOP-unknown" in str(exc_info.value)


def test_negative_v11_blocked_on_must_be_structured_and_declared() -> None:
    """Mutation checks: blocked work is a structured STOP, not executable prose."""
    trail = _get_happy_v11_trail_data()
    trail["steps"][0]["blocked_on"] = "wait for an operator"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)

    assert "TrailSpec schema violation" in str(exc_info.value)

    undeclared_stop = _get_happy_v11_trail_data()
    undeclared_stop["steps"][0]["blocked_on"] = {
        "id": "operator-approval",
        "reason": "Needs a current authority receipt.",
        "stop_code": "STOP-timeout",
    }
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(
            undeclared_stop, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH
        )

    assert "must be declared by the trail" in str(exc_info.value)


def test_negative_v11_seat_syntax_and_registry_eligibility(tmp_path) -> None:
    """Seat syntax remains schema-level; eligibility comes from the mutable registry."""
    trail = _get_happy_v11_trail_data()
    trail["seats"] = ["not a seat"]
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(trail, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)
    assert "TrailSpec schema violation" in str(exc_info.value)

    ineligible = _get_happy_v11_trail_data()
    ineligible["seats"] = ["unknown-seat"]
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(ineligible, spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH)
    assert "seat eligibility failed" in str(exc_info.value)

    dynamic_registry = tmp_path / "seat-registry.yaml"
    dynamic_registry.write_text(
        yaml.safe_dump(
            {"endpoints": [{"name": "future-seat", "state": "live"}]},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    dynamic = _get_happy_v11_trail_data()
    dynamic["seats"] = ["future-seat"]
    res = validate_trailspec_data(
        dynamic,
        spec_schema_path=TRAIL_SPEC_V11_SCHEMA_PATH,
        seat_registry_path=dynamic_registry,
    )
    assert res["execution_eligible"] is True


def test_stop_vocabulary_has_18_codes_and_never_reports_16() -> None:
    """The published operational vocabulary is 18 codes; 16 names trigger classes."""
    assert len(VALID_STOP_CODES) == 18
    data = _get_happy_example_data()
    data["stop_codes"].append("STOP-not-published")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)

    message = str(exc_info.value)
    assert "18-code STOP vocabulary" in message
    assert "16-item" not in message


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
    # Corrupt a copy: replace a real transition of a step selected by id (not by
    # index — step order is not part of this test's contract) with a dangling
    # target.
    step = next(s for s in data["steps"] if s["step_id"] == "request_review")
    step["transitions"]["review_fired"] = "non_existent_step_123"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    err_msg = str(exc_info.value)
    assert "Dangling transition" in err_msg
    assert "non_existent_step_123" in err_msg

    # Mutation check: restore original copy -> passes
    restored = _get_happy_example_data()
    res = validate_trailspec_data(restored, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)
    assert res["ok"] is True


def test_negative_unreachable_step() -> None:
    """Negative invariant test: a spec with an unreachable/orphan step fails validation."""
    data = _get_happy_example_data()
    # Add an orphan step that no step transitions to
    orphan_step = {
        "step_id": "orphan_step_xyz",
        "intent": "Unreachable step for testing",
        "command": "echo orphan",
        "evidence_predicate": {
            "command": "echo orphan",
            "success_pattern": "^orphan$",
        },
        "transitions": {
            "success": "request_review",
        },
        "kind": "mechanical",
        "blocked_on": None,
    }
    data["steps"].append(orphan_step)

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)

    err_msg = str(exc_info.value)
    assert "Unreachable step(s)" in err_msg
    assert "orphan_step_xyz" in err_msg

    # Mutation check: restore original copy -> passes
    restored = _get_happy_example_data()
    res = validate_trailspec_data(restored, spec_schema_path=TRAIL_SPEC_SCHEMA_PATH)
    assert res["ok"] is True


def test_negative_unknown_stop_code() -> None:
    """Negative invariant test: unknown stop_code not in the 18-code vocabulary fails."""
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


def _get_happy_tables_data() -> dict[str, Any]:
    return yaml.safe_load(DEFAULT_DECISION_TABLES_PATH.read_text(encoding="utf-8"))


def test_decision_tables_file_validates() -> None:
    """The shipped decision-tables draft must pass its schema (review finding on #5886:
    the v0 file declared itself unvalidated and sat outside all coverage)."""
    res = validate_decision_tables()
    assert res["ok"] is True
    assert res["precedence"] == "first-match"
    for expected in ("queue-pick", "review-gate-arm", "settle-status", "width"):
        assert expected in res["tables"], f"table '{expected}' missing from the draft"


def test_negative_decision_tables_bad_mode() -> None:
    """Mutation check: an unknown table mode must fail schema validation."""
    data = _get_happy_tables_data()
    data["tables"]["queue-pick"]["mode"] = "vibes"
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_decision_tables_data(data)
    assert "DecisionTables schema violation" in str(exc_info.value)

    restored = _get_happy_tables_data()
    assert validate_decision_tables_data(restored)["ok"] is True


def test_negative_decision_tables_static_requires_rows() -> None:
    """Mutation check: a static table with its rows deleted must fail."""
    data = _get_happy_tables_data()
    del data["tables"]["queue-pick"]["rows"]
    with pytest.raises(TrailSpecValidationError):
        validate_decision_tables_data(data)


def test_negative_decision_tables_missing_precedence() -> None:
    """Mutation check: dropping the first-match precedence contract must fail —
    without it the row-ordering conflicts the #5886 review found come back."""
    data = _get_happy_tables_data()
    del data["precedence"]
    with pytest.raises(TrailSpecValidationError):
        validate_decision_tables_data(data)


def test_negative_decision_tables_unknown_stop_code() -> None:
    """Mutation check: a row action naming an unpublished STOP code must fail."""
    data = _get_happy_tables_data()
    data["tables"]["queue-pick"]["rows"].append(
        {"when": "impossible synthetic condition", "then": "STOP-made-up-code"}
    )
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_decision_tables_data(data)
    assert "STOP-made-up-code" in str(exc_info.value)


_RB1_PATH = _TRAILS_DIR / "rb1-cold-start.trail.yaml"
_RB4_PATH = _TRAILS_DIR / "rb4-red-ci-triage.trail.yaml"


def _get_rb1_data() -> dict[str, Any]:
    return yaml.safe_load(_RB1_PATH.read_text(encoding="utf-8"))


def test_rb4_lookup_routes_never_make_a_rerun_reachable() -> None:
    """Stage 2 may return retry data but must not execute or route a rerun."""
    spec = yaml.safe_load(_RB4_PATH.read_text(encoding="utf-8"))
    lookup_step = next(step for step in spec["steps"] if step["step_id"] == "allowlist_match")
    commands = "\n".join(step["command"] for step in spec["steps"])

    assert "red_ci_known_failures.py lookup" in lookup_step["command"]
    assert lookup_step["transitions"]["matched_retry_once"] == "STOP-manual-intervention"
    assert "gh run rerun" not in commands


@pytest.mark.parametrize("trail_path", _ALL_SHIPPED_TRAILS, ids=lambda p: p.stem)
def test_declared_table_refs_resolve(trail_path) -> None:
    """Every table a shipped trail declares must exist in the decision-tables draft
    (r2 review finding on #5886: table references were unbound and unvalidatable)."""
    spec = yaml.safe_load(trail_path.read_text(encoding="utf-8"))
    tables = _get_happy_tables_data()
    res = validate_trail_table_refs(spec, tables)
    assert res["ok"] is True


def test_rb1_table_lookup_steps_bind_tables() -> None:
    """RB1's table-lookup steps must each name their table (RB3 predates the tables
    draft — its retrofit is a T2-certification item on #5885, not enforced here)."""
    spec = _get_rb1_data()
    tables = _get_happy_tables_data()
    res = validate_trail_table_refs(spec, tables)
    lookup_steps = [s["step_id"] for s in spec["steps"] if s.get("kind") == "table-lookup"]
    unbound = [s for s in lookup_steps if s not in res["bound_steps"]]
    assert not unbound, f"RB1 table-lookup steps without a table binding: {unbound}"


def test_negative_table_lookup_without_table_fails_schema() -> None:
    """A table-lookup step must name a non-null table in the TrailSpec schema."""
    spec = _get_rb1_data()
    lookup_step = next(step for step in spec["steps"] if step["kind"] == "table-lookup")
    del lookup_step["table"]

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(spec)

    assert "TrailSpec schema violation" in str(exc_info.value)
    assert "table" in str(exc_info.value)


def test_negative_table_lookup_without_table_fails_cross_check() -> None:
    """The table cross-check fails closed even when its caller bypasses schema validation."""
    spec = _get_rb1_data()
    tables = _get_happy_tables_data()
    lookup_step = next(step for step in spec["steps"] if step["kind"] == "table-lookup")
    lookup_step["table"] = None

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trail_table_refs(spec, tables)

    assert "Missing table binding" in str(exc_info.value)
    assert lookup_step["step_id"] in str(exc_info.value)


@pytest.mark.parametrize("table_ref", [[], {}], ids=["list", "mapping"])
def test_negative_table_lookup_non_string_table_fails_cross_check(
    table_ref: object,
) -> None:
    """The cross-check must reject non-string table bindings before membership tests."""
    spec = _get_rb1_data()
    tables = _get_happy_tables_data()
    lookup_step = next(step for step in spec["steps"] if step["kind"] == "table-lookup")
    lookup_step["table"] = table_ref

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trail_table_refs(spec, tables)

    assert "Missing table binding" in str(exc_info.value)
    assert lookup_step["step_id"] in str(exc_info.value)


def test_negative_unbound_table_ref() -> None:
    """Mutation check: a misspelled table reference must fail the cross-document check."""
    spec = _get_rb1_data()
    tables = _get_happy_tables_data()
    for step in spec["steps"]:
        if step.get("table"):
            step["table"] = "queue-pikc"  # misspelled
            break
    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trail_table_refs(spec, tables)
    assert "queue-pikc" in str(exc_info.value)

    restored = _get_rb1_data()
    assert validate_trail_table_refs(restored, tables)["ok"] is True


def test_cli_tables_flag_runs_cross_check(tmp_path, capsys) -> None:
    """r3 review finding: the CLI --tables path must run the cross-document check, not
    just the two independent validators — an unbound reference must fail the COMMAND."""
    from scripts.orchestration.validate_trailspec import main

    spec = _get_rb1_data()
    for step in spec["steps"]:
        if step.get("table"):
            step["table"] = "queue-pikc"  # misspelled
            break
    bad_spec = tmp_path / "rb1-bad-ref.trail.yaml"
    bad_spec.write_text(yaml.dump(spec), encoding="utf-8")

    rc = main(["--spec", str(bad_spec), "--tables", str(DEFAULT_DECISION_TABLES_PATH), "--json"])
    assert rc == 1
    assert "queue-pikc" in capsys.readouterr().out

    rc_ok = main(["--spec", str(_RB1_PATH), "--tables", str(DEFAULT_DECISION_TABLES_PATH), "--json"])
    assert rc_ok == 0
    out_ok = capsys.readouterr().out
    assert '"table_refs"' in out_ok


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


def test_cli_registry_flag_runs_validation(tmp_path, capsys) -> None:
    """CLI --registry mode validates red-CI known-failures registry."""
    from scripts.orchestration.validate_trailspec import main

    reg_data = {
        "schema_version": "red-ci-known-failures.v1",
        "registry_version": "1.0.0",
        "entries": [
            {
                "id": "pytest-cache-race",
                "matcher": {
                    "check_name": {"exact": "CI / Test (pytest)"},
                    "lines": {
                        "required": [
                            {
                                "type": "regex",
                                "value": r"^FAILED tests/test_cache\.py::test_parallel_cache .*$",
                            }
                        ],
                        "accepted": [
                            {
                                "type": "regex",
                                "value": r"^FAILED tests/test_cache\.py::test_parallel_cache .*$",
                            }
                        ],
                        "require_full_coverage": True,
                    },
                },
                "action": {"kind": "retry-once"},
                "owning_issue": 5885,
                "evidence": [
                    {
                        "run_id": 123456789,
                        "run_attempt": 1,
                        "pr_number": 1234,
                        "head_sha": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4",
                        "observed_at": "2026-07-28T10:00:00Z",
                        "signature_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    }
                ],
                "governance": {
                    "added_by": "developer1",
                    "added_at": "2026-07-28T10:00:00Z",
                    "added_in_pr": 6000,
                    "reviewed_by": ["reviewer1"],
                    "reviewed_at": "2026-07-28T11:00:00Z",
                    "review_by": "2026-08-27T11:00:00Z",
                },
            }
        ],
    }
    reg_file = tmp_path / "valid_registry.json"
    reg_file.write_text(json.dumps(reg_data), encoding="utf-8")

    rc = main([
        "--spec", str(DEFAULT_EXAMPLE_TRAIL_PATH),
        "--registry", str(reg_file),
        "--as-of", "2026-07-28T12:00:00Z",
        "--json",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"registry"' in out
    assert '"entries_count": 1' in out

    # Test failure case
    reg_data["entries"][0]["governance"]["review_by"] = "2026-07-01T00:00:00Z"
    bad_reg_file = tmp_path / "expired_registry.json"
    bad_reg_file.write_text(json.dumps(reg_data), encoding="utf-8")

    rc_err = main([
        "--spec", str(DEFAULT_EXAMPLE_TRAIL_PATH),
        "--registry", str(bad_reg_file),
        "--as-of", "2026-07-28T12:00:00Z",
        "--json",
    ])
    assert rc_err == 1
    err_out = capsys.readouterr().out
    assert "expired at review_by" in err_out
