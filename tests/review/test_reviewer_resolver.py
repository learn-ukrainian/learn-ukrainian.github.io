"""Gemini's native low/medium formal-review boundary (#10073)."""

from dataclasses import replace

import pytest

from scripts.review.family_exclusions import family_exclusion
from scripts.review.reviewer_resolver import (
    REVIEW_CANDIDATES,
    ResolverInputs,
    evaluate_candidate,
    normalize_review_task_id,
    red_team_seat_refusal,
    resolve_reviewer,
    review_task_id_comparison_keys,
)

GEMINI = REVIEW_CANDIDATES["gemini-3.8-flash-high"]


@pytest.mark.parametrize(
    "task_id,expected",
    [
        ("author-one", "author-one"),
        ("AUTHOR-ONE", "author-one"),
        (" author-one ", "author-one"),
        ("CODEX/Author-One", "author-one"),
        ("codex-AUTHOR-ONE", "author-one"),
        ("codex/Author name!", "author-name"),
        ("...", "task"),
    ],
)
def test_review_task_identity_matches_trailer_suffix(task_id, expected):
    assert normalize_review_task_id(task_id, agent="codex") == expected


@pytest.mark.parametrize(
    "task_id,agent,expected",
    [
        ("claude-impl-x", "cursor", {"claude-impl-x", "impl-x"}),
        (" CODEX/Author-One ", "claude", {"codex-author-one", "author-one"}),
        ("cursor/Author name!", "cursor", {"cursor-author-name", "author-name"}),
        ("grok-hermes-author", "codex", {"grok-hermes-author", "hermes-author", "author"}),
        ("custom/author-one", "custom", {"custom-author-one", "author-one"}),
        ("codex/gpt-6.1-sol", "claude", {"codex-gpt-6.1-sol", "gpt-6.1-sol"}),
        ("other-task", "claude", {"other-task"}),
    ],
)
def test_review_task_comparison_keys_include_known_harnesses(task_id, agent, expected):
    assert review_task_id_comparison_keys(task_id, agent=agent) == expected


def test_different_task_comparison_keys_do_not_intersect():
    assert not review_task_id_comparison_keys("other-task", agent="claude") & review_task_id_comparison_keys(
        "codex/author-one", agent="codex"
    )


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("entrypoint", ["evaluate", "pin", "ladder"])
def test_gemini_risk_boundary(profile, risk, entrypoint):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", review_profile=profile, risk=risk)
    if entrypoint == "evaluate":
        eligible = evaluate_candidate(GEMINI, inputs).status == "eligible"
    else:
        if entrypoint == "pin":
            inputs = replace(inputs, pinned_candidate=GEMINI.name, pressure_override_reason="boundary test")
        eligible = resolve_reviewer(inputs, ladder=((GEMINI,),)).selected is not None
    assert eligible == (profile == "code" and risk in {"low", "medium"})


@pytest.mark.parametrize("risk", ["low", "medium"])
@pytest.mark.parametrize("scope", ["changed_paths", "owned_paths"])
@pytest.mark.parametrize(
    "path", ["scripts/review/reviewer_resolver.py", "scripts/agent_runtime/adapters/agy.py", ".github/workflows/ci.yml"]
)
def test_gemini_security_paths_override_declared_risk(risk, scope, path):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, **{scope: (path,)})
    result = evaluate_candidate(GEMINI, inputs)
    assert result.status == "excluded"
    assert "security-sensitive" in result.reason
    assert resolve_reviewer(inputs, ladder=((GEMINI,),)).selected is None


@pytest.mark.parametrize("formal", [True, False])
def test_custom_roles_cannot_grant_gemini_high_risk(formal):
    forged = replace(GEMINI, model_roles=frozenset({"critical_review", "standard_review"}))
    assert (
        evaluate_candidate(
            forged, ResolverInputs(author_model="gpt-6.1-sol", risk="critical", formal_review=formal)
        ).status
        == "excluded"
    )


def test_gemini_independence_and_unhealthy_route():
    same = evaluate_candidate(GEMINI, ResolverInputs(author_model="gemini-3.8-flash-high", risk="low"))
    assert same.status == "excluded"
    assert "same family" in same.reason
    unhealthy = evaluate_candidate(
        GEMINI, ResolverInputs(author_model="gpt-6.1-sol", risk="low", routing_snapshot={"agy": "unhealthy"})
    )
    assert unhealthy.status == "excluded"


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_automatic_ladder_can_use_gemini_when_other_routes_unavailable(risk):
    snapshot = {route: "unhealthy" for route in {candidate.route for candidate in REVIEW_CANDIDATES.values()}}
    snapshot["agy"] = "healthy"
    result = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk, routing_snapshot=snapshot))
    assert (result.selected.name if result.selected else None) == (GEMINI.name if risk in {"low", "medium"} else None)


@pytest.mark.parametrize("risk", ["low", "medium"])
def test_native_agy_suitability_precedes_grok_when_frontier_budgets_near_cap(risk):
    result = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            risk=risk,
            routing_snapshot={
                "agents": {
                    route: {"status": "near_cap", "remaining_pct": 5, "health": {"healthy": True}}
                    for route in ("claude", "codex")
                },
                "diagnostics": {"stale": False},
            },
        )
    )
    assert result.selected.name == GEMINI.name
    grok = next(row for row in result.trace if row.name == "grok-4.7")
    assert grok.status == "eligible"
    assert result.selected.suitability_rank < grok.suitability_rank


@pytest.mark.parametrize(
    "field,value",
    [
        ("participant", "codex"),
        ("catalog_transport", "native_codex"),
        ("sealed_executable", "other.py"),
        ("adapter_transport", "acp"),
    ],
)
def test_native_endpoint_identity_cannot_be_forged(field, value):
    forged = replace(GEMINI, **{field: value})
    result = evaluate_candidate(forged, ResolverInputs(author_model="gpt-6.1-sol", risk="low"))
    assert result.status == "excluded"
    assert "endpoint identity" in result.reason


@pytest.mark.parametrize(
    "risk,eligible", [(None, False), ("low", True), ("medium", True), ("high", False), ("critical", False)]
)
def test_role_family_filter_uses_risk(risk, eligible):
    result = family_exclusion(family="google", route="agy", transport="agy", risk=risk)
    assert (result is None) == eligible


@pytest.mark.parametrize("outside_available", [True, False])
def test_red_team_prefers_outside_family_before_same_family(outside_available):
    sol = REVIEW_CANDIDATES["openai_frontier"]
    opus = REVIEW_CANDIDATES["claude-opus-5-5"]
    snapshot = {"claude": "healthy" if outside_available else "unhealthy"}
    result = resolve_reviewer(
        ResolverInputs(author_model="gpt-6-luna", risk="critical", routing_snapshot=snapshot),
        ladder=((sol,), (opus,)),
        review_mode="red_team",
    )
    assert result.selected.name == (opus.name if outside_available else sol.name)
    assert result.review_mode == "red_team"
    assert result.limitation == "Separate non-author red-team review; this label does not attest cross-family review."


def test_red_team_pin_cannot_override_outside_family_preference():
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol",
        risk="critical",
        pinned_candidate="openai_frontier",
        pressure_override_reason="adversarial fixture",
    )
    result = resolve_reviewer(inputs, review_mode="red_team")
    assert result.selected is None
    assert "failed a hard eligibility gate" in result.fail_closed_reason


@pytest.mark.parametrize(
    "inputs",
    [
        ResolverInputs(author_model="unknown-author", risk="critical"),
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk="critical",
            subject_seats=frozenset({"codex"}),
            routing_snapshot={"claude": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"},
        ),
    ],
)
def test_red_team_keeps_identity_and_subject_gates(inputs):
    assert resolve_reviewer(inputs, review_mode="red_team").selected is None


def test_resolver_refuses_invalid_review_mode():
    with pytest.raises(ValueError, match="unsupported review mode"):
        resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol"), review_mode="invalid")


@pytest.mark.parametrize(
    "reviewer,authors,explicit,expected",
    [
        ("gpt-6.1-sol", ("gpt-6.1-sol",), None, "RED_TEAM_REFUSED: reviewer model equals a branch author model"),
        (
            "cursor:gpt-6.1-sol-high",
            ("CODEX/gpt-6.1-sol[1m]",),
            None,
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "claude-opus-5-5[1m]",
            ("claude-opus-5-5-high",),
            None,
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        ("gpt-6-luna", ("gpt-6.1-sol",), None, None),
        ("gpt-6.1-sol", (), None, "RED_TEAM_REFUSED: author model unknown; supply --review-author-model"),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna", None),
            None,
            "RED_TEAM_REFUSED: author model unknown; supply --review-author-model",
        ),
        ("gpt-6.1-sol", (None,), "gpt-6-luna", None),
        (
            "gpt-6.1-sol",
            ("gpt-6.1-sol",),
            "gpt-6-luna",
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna",),
            "gpt-6.1-sol",
            "RED_TEAM_REFUSED: reviewer model equals a branch author model",
        ),
        (
            "gpt-6.1-sol",
            ("gpt-6-luna",),
            "unlisted-model",
            "RED_TEAM_REFUSED: author model unknown; supply --review-author-model",
        ),
    ],
)
def test_red_team_seat_rule_uses_canonical_models(reviewer, authors, explicit, expected):
    assert red_team_seat_refusal((reviewer,), author_models=authors, author_model=explicit) == expected


def test_red_team_evaluation_refuses_same_model_before_selection():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    result = evaluate_candidate(sol, ResolverInputs(author_model="gpt-6.1-sol"), review_mode="red_team")
    assert result.status == "excluded"
    assert result.reason == "RED_TEAM_REFUSED: reviewer model equals a branch author model"


def test_red_team_evaluation_accepts_different_same_family_model():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    result = evaluate_candidate(sol, ResolverInputs(author_model="gpt-6-luna"), review_mode="red_team")
    assert result.status == "eligible"


def test_red_team_evaluation_refuses_one_unknown_author_in_complete_branch():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    result = evaluate_candidate(
        sol,
        ResolverInputs(author_model="", author_models=("gpt-6-luna", None), author_families=frozenset({"openai"})),
        review_mode="red_team",
    )
    assert result.status == "excluded"
    assert result.reason == "RED_TEAM_REFUSED: author model unknown; supply --review-author-model"
