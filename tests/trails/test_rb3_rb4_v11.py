"""Contract tests for the RB-3/RB-4 TrailSpec v1.1 P9 migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.trail_predicates import evaluate_named_table, load_decision_tables
from scripts.orchestration.validate_trailspec import (
    DEFAULT_DECISION_TABLES_V1_PATH,
    PROJECT_ROOT,
    validate_trailspec,
)

RB3_PATH = PROJECT_ROOT / "scripts/config/trails/rb3-pr-lifecycle.trail.yaml"
RB4_PATH = PROJECT_ROOT / "scripts/config/trails/rb4-red-ci-triage.trail.yaml"

REVIEW_GATE_INPUTS = {
    "is_draft",
    "current_head_reviews_terminal_published",
    "reviewer_is_independent",
    "requested_changes_resolved",
    "has_stale_approval",
    "verdicts_conflict",
    "blocking_ci",
    "has_current_cross_family_approval",
}


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _steps(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {step["step_id"]: step for step in spec["steps"]}


def _command_text(step: dict[str, Any]) -> str:
    return "\n".join(step["command"]["argv"])


def _assert_retry_once_stops(spec: dict[str, Any]) -> None:
    allowlist = _steps(spec)["allowlist_match"]
    assert allowlist["transitions"]["matched_retry_once"]["target"].startswith("STOP-")
    assert allowlist["transitions"]["matched_retry_once"]["target"] == "STOP-manual-intervention"


def _assert_rb3_babysit_routing(spec: dict[str, Any]) -> None:
    steps = _steps(spec)
    assert (
        steps["observe_babysit_registration"]["transitions"]["registration_observed"]["target"]
        == "observe_babysit_state"
    )
    transitions = steps["observe_babysit_state"]["transitions"]
    assert {
        outcome: transition["target"] for outcome, transition in transitions.items()
    } == {
        "pr_merged": "post_merge_hygiene",
        "blocking_red": "handed_to_red_ci_triage",
        "disarmed_open": "observe_gate_inputs",
        "automerge_armed": "register_babysit",
        "still_armed": "observe_babysit_state",
        "babysit_state_unreadable": "STOP-precondition-failed",
    }


@pytest.mark.parametrize(
    ("path", "trail_id", "version"),
    [(RB3_PATH, "rb3-pr-lifecycle", "2.1.0"), (RB4_PATH, "rb4-red-ci-triage", "0.5.0")],
)
def test_migrated_trails_validate_v11(path: Path, trail_id: str, version: str) -> None:
    """Both P9 rails are execution-eligible v1.1 specifications."""
    result = validate_trailspec(spec_path=path)
    assert result["ok"] is True
    assert result["spec"]["trail_id"] == trail_id
    assert result["spec"]["version"] == version
    assert result["spec"]["execution_eligible"] is True


@pytest.mark.parametrize("path", [RB3_PATH, RB4_PATH])
def test_every_command_binds_invocation_and_uses_typed_parameter_transport(path: Path) -> None:
    """v1.1 commands bind the runner UUID and never interpolate parameters into sh -c."""
    spec = _load(path)
    for step in spec["steps"]:
        command = step["command"]
        assert command["environment"]["TRAIL_INVOCATION_ID"] == "{invocation_id}"
        if command["argv"][:2] == ["sh", "-c"]:
            for parameter_name in spec["parameters"]:
                assert f"{{{parameter_name}}}" not in command["argv"][2], step["step_id"]


@pytest.mark.parametrize("path", [RB3_PATH, RB4_PATH])
def test_transition_predicates_are_receipt_unique(path: Path) -> None:
    """Each command outcome has at most one receipt predicate transition."""
    for step in _load(path)["steps"]:
        outcomes = []
        predicate_ids = []
        for transition in step["transitions"].values():
            predicate_ids.append(transition["evidence"]["predicate_id"])
            outcomes.extend(
                clause["value"]
                for clause in transition["evidence"]["clauses"]
                if clause["field"] == "actor_outcome"
            )
        assert len(predicate_ids) == len(set(predicate_ids)), step["step_id"]
        assert len(outcomes) == len(set(outcomes)), step["step_id"]


def test_rb4_retry_once_is_a_non_rerun_stop_and_commands_have_no_rerun_primitive() -> None:
    """P13 owns reruns: RB-4 cannot invoke one, claim one, or route retry-once onward."""
    spec = _load(RB4_PATH)
    _assert_retry_once_stops(spec)
    command_text = "\n".join(_command_text(step) for step in spec["steps"])
    assert "gh run rerun" not in command_text
    assert "rerun-claims" not in command_text
    assert "claimant-ledger" not in command_text


def test_negative_rb4_retry_once_rewire_fails_non_rerun_contract() -> None:
    """Mutation proof: rerouting retry-once away from STOP fails exactly this contract."""
    spec = _load(RB4_PATH)
    _steps(spec)["allowlist_match"]["transitions"]["matched_retry_once"]["target"] = (
        "back_to_pr_lifecycle"
    )
    with pytest.raises(AssertionError):
        _assert_retry_once_stops(spec)


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({"reviewer_is_independent": False}, "request-independent-review"),
        ({"requested_changes_resolved": False}, "wait-requested-changes"),
        ({"has_stale_approval": True}, "request-current-head-review"),
        ({"verdicts_conflict": True}, "STOP-contested"),
        ({"is_draft": True}, "hold-draft"),
        ({"blocking_ci": "red"}, "delegate-red-ci-triage"),
    ],
)
def test_rb3_refusal_rows_cannot_reach_gate_passed(
    changed: dict[str, bool | str], expected: str
) -> None:
    """All mandatory refusal plants are distinct non-arming review-gate rows."""
    facts: dict[str, bool | str] = {
        "is_draft": False,
        "current_head_reviews_terminal_published": True,
        "reviewer_is_independent": True,
        "requested_changes_resolved": True,
        "has_stale_approval": False,
        "verdicts_conflict": False,
        "blocking_ci": "green",
        "has_current_cross_family_approval": True,
    }
    facts.update(changed)
    outcome = evaluate_named_table(load_decision_tables(), "review-gate-arm", facts)
    assert outcome == expected
    assert outcome != "arm-automerge"

    rb3 = _steps(_load(RB3_PATH))["evaluate_review_gate"]
    label = "stop_contested" if outcome == "STOP-contested" else outcome.replace("-", "_")
    assert rb3["transitions"][label]["target"] != "arm_automerge"


def test_rb3_review_gate_evaluates_all_eight_typed_inputs() -> None:
    """Every RB-3 review-gate evaluation consumes the complete P2 input contract."""
    rb3 = _steps(_load(RB3_PATH))
    observation = rb3["observe_gate_inputs"]
    evaluation = rb3["evaluate_review_gate"]
    observation_program = _command_text(observation)
    evaluation_program = _command_text(evaluation)

    tables = load_decision_tables()
    assert set(tables["tables"]["review-gate-arm"]["inputs"]) == REVIEW_GATE_INPUTS
    for input_name in REVIEW_GATE_INPUTS:
        assert input_name in observation_program
    assert evaluation["command"]["environment"]["TABLE_ID"] == "review-gate-arm"
    assert evaluation["command"]["environment"]["TABLES_PATH"] == str(
        DEFAULT_DECISION_TABLES_V1_PATH.relative_to(PROJECT_ROOT)
    )
    assert "evaluate_named_table" in evaluation_program
    assert evaluation["command"]["environment"]["GATE_FACTS_RECEIPT"] == "{gate_facts_receipt}"


def test_rb3_babysit_registration_continues_to_bounded_state_observation() -> None:
    """A durable registration hands control to the bounded lifecycle observation."""
    _assert_rb3_babysit_routing(_load(RB3_PATH))


def test_negative_rb3_babysit_registration_stop_rewire_fails_routing_contract() -> None:
    """Mutation proof: restoring the inverted registration STOP fails this contract."""
    spec = _load(RB3_PATH)
    _steps(spec)["observe_babysit_registration"]["transitions"]["registration_observed"][
        "target"
    ] = "STOP-manual-intervention"
    with pytest.raises(AssertionError):
        _assert_rb3_babysit_routing(spec)


def test_rb3_review_in_flight_self_loops_for_driver_owned_pacing() -> None:
    """Each invocation observes one request state, so in-flight review remains paced."""
    review_request = _steps(_load(RB3_PATH))["observe_review_request"]
    assert review_request["transitions"]["review_in_flight"]["target"] == (
        "observe_review_request"
    )


def test_rb3_former_judgment_nodes_are_receipt_observations_or_stops() -> None:
    """Former summon/judgment nodes neither fabricate completion nor perform their action."""
    steps = _steps(_load(RB3_PATH))
    former_judgment_steps = {
        "observe_delivery_application_receipt": "rb3-deliveries-",
        "observe_stuck_request_resolution": "rb3-stuck-request-",
        "observe_verdict_receipt": "rb3-verdict-",
        "observe_fix_round_receipt": "rb3-fix-round-",
        "observe_finalize_note_receipt": "rb3-finalize-",
    }
    for step_id, receipt_name in former_judgment_steps.items():
        step = steps[step_id]
        assert step["command"]["mutation_class"] == "observe"
        command = _command_text(step)
        assert receipt_name in command
        assert "jq" in command
        assert any(target.startswith("STOP-") for target in (
            transition["target"] for transition in step["transitions"].values()
        ))


def test_rb4_keeps_head_currency_reachable_and_url_bound() -> None:
    """RB-4 keeps both v0.4.3 safety properties through migration."""
    steps = _steps(_load(RB4_PATH))
    assert steps["extract_signature"]["transitions"]["signature_recorded"]["target"] == (
        "head_currency_check"
    )
    assert steps["head_currency_check"]["transitions"]["head_current"]["target"] == (
        "staleness_probe"
    )
    locate_command = _command_text(steps["locate_failing_run"])
    assert "/actions/runs/" in locate_command
    assert "gh run list --branch" not in locate_command
