"""Hermetic policy tests for the Hramatka new-scope gate."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.fleet import hramatka_scope_gate as gate

PUBLIC = gate.PUBLIC_REPOSITORY
PRIVATE = gate.PRIVATE_REPOSITORY
REGISTRY = {
    "hramatka": [4542],
    "infra-harness": [4707],
    "devops": [5703],
}


def _issue(repository: str, number: int) -> gate.IssueRef:
    return gate.IssueRef(repository, number)


def _observation(
    *,
    labels: set[str] | None = None,
    body: str = "",
    parent_number: int | None = None,
) -> gate.IssueObservation:
    return gate.IssueObservation(
        labels=frozenset(labels or set()),
        body=body,
        parent_number=parent_number,
    )


def _reader(observation: gate.IssueObservation) -> gate.IssueReader:
    return lambda _issue_ref: observation


def _unavailable(_issue_ref: gate.IssueRef) -> gate.IssueObservation:
    raise gate.IssueLookupUnavailable("fixture unavailable")


def test_constants_pin_the_approved_hramatka_scope() -> None:
    config = gate.HRAMATKA_SCOPE_GATE

    assert config.stream_name == "hramatka"
    assert config.public_epic == 4542
    assert config.private_board == _issue(PRIVATE, 349)
    assert config.operator_only_issues == {_issue(PRIVATE, 360), _issue(PRIVATE, 212)}


def test_configured_public_epic_allows_without_api_lookup() -> None:
    def must_not_run(_issue_ref: gate.IssueRef) -> gate.IssueObservation:
        pytest.fail("the configured public epic is already exact membership")

    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PUBLIC, 4542),
        stream_registry=REGISTRY,
        reader=must_not_run,
    )

    assert decision.outcome is gate.Outcome.ALLOW
    assert decision.destination is None


def test_public_native_child_of_hramatka_epic_allows() -> None:
    decision = gate.decide_scope(
        action="new_scope",
        issue=_issue(PUBLIC, 6001),
        stream_registry=REGISTRY,
        reader=_reader(_observation(parent_number=4542)),
    )

    assert decision.outcome is gate.Outcome.ALLOW


def test_secondary_configured_hramatka_epic_is_still_exact_membership() -> None:
    registry = {**REGISTRY, "hramatka": [4542, 6999]}

    decision = gate.decide_scope(
        action="new_scope",
        issue=_issue(PUBLIC, 6005),
        stream_registry=registry,
        reader=_reader(_observation(parent_number=6999)),
    )

    assert decision.outcome is gate.Outcome.ALLOW


def test_public_other_stream_routes_to_named_epic() -> None:
    decision = gate.decide_scope(
        action="new_pr",
        issue=_issue(PUBLIC, 6002),
        stream_registry=REGISTRY,
        reader=_reader(_observation(parent_number=4707)),
    )

    assert decision.outcome is gate.Outcome.ROUTE
    assert decision.destination == "infra-harness epic #4707"


def test_primary_membership_beats_a_hramatka_word_mention() -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PUBLIC, 6003),
        stream_registry=REGISTRY,
        reader=_reader(
            _observation(
                labels={"hramatka"},
                body="Hramatka is mentioned here.",
                parent_number=4707,
            )
        ),
    )

    assert decision.outcome is gate.Outcome.ROUTE
    assert decision.destination == "infra-harness epic #4707"


def test_unassigned_public_issue_routes_to_stream_triage() -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PUBLIC, 6004),
        stream_registry=REGISTRY,
        reader=_reader(_observation()),
    )

    assert decision.outcome is gate.Outcome.ROUTE
    assert decision.destination == "stream triage (link the issue to exactly one stream epic)"


@pytest.mark.parametrize(
    "observation",
    [
        _observation(labels={"hramatka"}),
        _observation(labels={"stream:hramatka"}),
        _observation(body="<!-- stream:hramatka -->"),
        _observation(parent_number=349),
    ],
)
def test_explicit_private_hramatka_tracking_allows(observation: gate.IssueObservation) -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PRIVATE, 6101),
        stream_registry=REGISTRY,
        reader=_reader(observation),
    )

    assert decision.outcome is gate.Outcome.ALLOW


def test_private_board_itself_is_explicit_hramatka_tracking() -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PRIVATE, 349),
        stream_registry=REGISTRY,
        reader=_reader(_observation()),
    )

    assert decision.outcome is gate.Outcome.ALLOW


def test_private_other_stream_tag_routes_to_named_destination() -> None:
    decision = gate.decide_scope(
        action="new_scope",
        issue=_issue(PRIVATE, 6102),
        stream_registry=REGISTRY,
        reader=_reader(_observation(body="stream: infra-harness")),
    )

    assert decision.outcome is gate.Outcome.ROUTE
    assert decision.destination == "infra-harness epic #4707"


def test_untagged_private_issue_routes_to_private_board_triage() -> None:
    decision = gate.decide_scope(
        action="new_pr",
        issue=_issue(PRIVATE, 6103),
        stream_registry=REGISTRY,
        reader=_reader(_observation()),
    )

    assert decision.outcome is gate.Outcome.ROUTE
    assert decision.destination == "private Hramatka board #349 triage"


def test_conflicting_private_stream_tags_hold() -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PRIVATE, 6104),
        stream_registry=REGISTRY,
        reader=_reader(_observation(labels={"hramatka", "stream:infra-harness"})),
    )

    assert decision.outcome is gate.Outcome.HOLD


@pytest.mark.parametrize("action", sorted(gate.GATED_ACTIONS))
def test_private_api_unavailable_holds_every_new_scope_action(action: str) -> None:
    decision = gate.decide_scope(
        action=action,
        issue=_issue(PRIVATE, 349),
        stream_registry=REGISTRY,
        reader=_unavailable,
    )

    assert decision.outcome is gate.Outcome.HOLD
    assert "UNKNOWN" in decision.reason


@pytest.mark.parametrize("number", [360, 212])
def test_operator_only_private_host_mutation_escalates_without_lookup(number: int) -> None:
    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PRIVATE, number),
        stream_registry=REGISTRY,
        reader=_unavailable,
    )

    assert decision.outcome is gate.Outcome.ESCALATE
    assert "operator-only" in decision.reason


@pytest.mark.parametrize("action", sorted(gate.EXEMPT_ACTIONS))
def test_non_scope_actions_are_exempt_without_api_lookup(action: str) -> None:
    decision = gate.decide_scope(
        action=action,
        issue=_issue(PRIVATE, 6106),
        stream_registry=REGISTRY,
        reader=_unavailable,
    )

    assert decision.outcome is gate.Outcome.ALLOW


def test_environment_variable_cannot_bypass_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_HRAMATKA_SCOPE_GATE", "1")

    decision = gate.decide_scope(
        action="new_dispatch",
        issue=_issue(PUBLIC, 6107),
        stream_registry=REGISTRY,
        reader=_reader(_observation(parent_number=4707)),
    )

    assert decision.outcome is gate.Outcome.ROUTE


def test_issue_refs_reject_unqualified_or_nonpositive_identifiers() -> None:
    with pytest.raises(ValueError, match="qualified"):
        gate.IssueRef("4542", 4542)
    with pytest.raises(ValueError, match="positive"):
        gate.IssueRef(PUBLIC, 0)


def test_gh_reader_uses_the_repo_qualified_graphql_target(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "data": {
                        "repository": {
                            "issue": {
                                "number": 349,
                                "body": "<!-- stream:hramatka -->",
                                "labels": {"nodes": [{"name": "hramatka"}]},
                                "parent": None,
                            }
                        }
                    }
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(gate.subprocess, "run", fake_run)

    observation = gate._gh_issue_observation(_issue(PRIVATE, 349))

    assert observation == _observation(labels={"hramatka"}, body="<!-- stream:hramatka -->")
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[:3] == ["gh", "api", "graphql"]
    assert f"owner={PRIVATE.split('/', 1)[0]}" in command
    assert f"name={PRIVATE.split('/', 1)[1]}" in command
    assert "number=349" in command
    assert kwargs["cwd"] == gate.REPO_ROOT


def test_gh_reader_hides_private_api_errors_and_treats_malformed_output_as_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def nonzero_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="private issue title: sensitive")

    monkeypatch.setattr(gate.subprocess, "run", nonzero_run)
    with pytest.raises(gate.IssueLookupUnavailable) as nonzero_error:
        gate._gh_issue_observation(_issue(PRIVATE, 349))
    assert "sensitive" not in str(nonzero_error.value)

    def malformed_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="not json", stderr="")

    monkeypatch.setattr(gate.subprocess, "run", malformed_run)
    with pytest.raises(gate.IssueLookupUnavailable):
        gate._gh_issue_observation(_issue(PRIVATE, 349))


def test_cli_emits_only_json_and_nonzero_for_a_route(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = gate.main(
        ["--action", "new_dispatch", "--issue-repo", PUBLIC, "--issue", "6108"],
        reader=_reader(_observation(parent_number=4707)),
        stream_registry=REGISTRY,
    )

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out) == {
        "destination": "infra-harness epic #4707",
        "outcome": "ROUTE",
        "reason": "public issue belongs to infra-harness through epic #4707",
    }


def test_cli_allows_configured_epic_and_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = gate.main(
        ["--action", "new_dispatch", "--issue-repo", PUBLIC, "--issue", "4542"],
        reader=_unavailable,
        stream_registry=REGISTRY,
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "ALLOW"
    assert "destination" not in payload
