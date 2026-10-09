"""Gemini's native low/medium formal-review boundary (#10073)."""

from dataclasses import replace

import pytest

from scripts.review.family_exclusions import family_exclusion
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate, resolve_reviewer

GEMINI = REVIEW_CANDIDATES["gemini-3.8-flash-high"]


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
@pytest.mark.parametrize("path", ["scripts/review/reviewer_resolver.py", "scripts/agent_runtime/adapters/agy.py", ".github/workflows/ci.yml"])
def test_gemini_security_paths_override_declared_risk(risk, scope, path):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, **{scope: (path,)})
    result = evaluate_candidate(GEMINI, inputs)
    assert result.status == "excluded"
    assert "security-sensitive" in result.reason
    assert resolve_reviewer(inputs, ladder=((GEMINI,),)).selected is None


@pytest.mark.parametrize("formal", [True, False])
def test_custom_roles_cannot_grant_gemini_high_risk(formal):
    forged = replace(GEMINI, model_roles=frozenset({"critical_review", "standard_review"}))
    assert evaluate_candidate(forged, ResolverInputs(author_model="gpt-6.1-sol", risk="critical", formal_review=formal)).status == "excluded"


def test_gemini_independence_and_unhealthy_route():
    same = evaluate_candidate(GEMINI, ResolverInputs(author_model="gemini-3.8-flash-high", risk="low"))
    assert same.status == "excluded"
    assert "same family" in same.reason
    unhealthy = evaluate_candidate(GEMINI, ResolverInputs(author_model="gpt-6.1-sol", risk="low", routing_snapshot={"agy": "unhealthy"}))
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


@pytest.mark.parametrize("field,value", [("participant", "codex"), ("catalog_transport", "native_codex"), ("sealed_executable", "other.py"), ("adapter_transport", "acp")])
def test_native_endpoint_identity_cannot_be_forged(field, value):
    forged = replace(GEMINI, **{field: value})
    result = evaluate_candidate(forged, ResolverInputs(author_model="gpt-6.1-sol", risk="low"))
    assert result.status == "excluded"
    assert "endpoint identity" in result.reason


@pytest.mark.parametrize("risk,eligible", [(None, False), ("low", True), ("medium", True), ("high", False), ("critical", False)])
def test_role_family_filter_uses_risk(risk, eligible):
    result = family_exclusion(family="google", route="agy", transport="agy", risk=risk)
    assert (result is None) == eligible
