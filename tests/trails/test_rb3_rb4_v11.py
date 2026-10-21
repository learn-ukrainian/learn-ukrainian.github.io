"""Contract tests for the RB-3/RB-4 TrailSpec v1.1 P9 migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.trail_predicates import evaluate_named_table, load_decision_tables
from scripts.orchestration.validate_trailspec import (
    PROJECT_ROOT,
)

RB3_PATH = PROJECT_ROOT / "scripts/config/trails/rb3-pr-lifecycle.trail.yaml"
RB4_PATH = PROJECT_ROOT / "scripts/config/trails/rb4-red-ci-triage.trail.yaml"


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


def test_rb3_babysit_registration_continues_to_bounded_state_observation() -> None:
    """A durable registration hands control to the bounded lifecycle observation."""
    _assert_rb3_babysit_routing(_load(RB3_PATH))


def test_rb3_review_in_flight_self_loops_for_driver_owned_pacing() -> None:
    """Each invocation observes one request state, so in-flight review remains paced."""
    review_request = _steps(_load(RB3_PATH))["observe_review_request"]
    assert review_request["transitions"]["review_in_flight"]["target"] == (
        "observe_review_request"
    )


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
