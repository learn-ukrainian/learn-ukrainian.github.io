"""Tests for the quality-first cross-family reviewer resolver."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.fleet import credit_lane
from scripts.review.reviewer_resolver import (
    AMBIGUOUS_AUTHOR_FAMILY,
    CONFLICTING_AUTHOR_FAMILY,
    CURSOR_AUTO_UNION_FAMILY,
    GLM,
    GROK_4_7,
    GROK_4_7_CURSOR_FALLBACK,
    OPENAI_FRONTIER,
    POOL,
    QWEN,
    REVIEW_CANDIDATES,
    REVIEW_LADDERS,
    SONNET_5_5,
    UNKNOWN_AUTHOR_FAMILY,
    ResolverInputs,
    evaluate_candidate,
    resolve_author_family,
    resolve_family,
    resolve_reviewer,
)

# Synthetic same-tier OpenAI candidate for ranking tests, never a fleet route.
PRACTICAL_ASTRA = replace(
    OPENAI_FRONTIER,
    name="synthetic-practical-astra",
    quality_tier="frontier_practical",
    model_roles=frozenset({"implementation", "investigation", "standard_review"}),
)


# Deliberately forbidden candidates exercise custom-ladder admission, never fleet seats.
DEEPSEEK_V4_PRO = replace(
    SONNET_5_5, name="deepseek-v4-pro", concrete_model="deepseek-v4-pro", family="deepseek", route="deepseek"
)
DEEPSEEK_V4_1_FLASH = replace(DEEPSEEK_V4_PRO, name="deepseek-v4.1-flash", concrete_model="deepseek-v4.1-flash")


@pytest.fixture
def practical_astra(monkeypatch):
    monkeypatch.setitem(REVIEW_CANDIDATES, PRACTICAL_ASTRA.name, PRACTICAL_ASTRA)
    return PRACTICAL_ASTRA


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("entrypoint", ["evaluate", "pin", "custom_ladder"])
def test_missing_critical_review_role_is_excluded(monkeypatch, profile, entrypoint):
    candidate = replace(REVIEW_CANDIDATES["openai_frontier"], model_roles=frozenset({"strong_review"}))
    inputs = ResolverInputs(author_model="claude-opus-5-5", review_profile=profile, risk="critical")
    reason = f"missing required review role suitability: {profile}/critical catalog suitability"

    if entrypoint == "evaluate":
        result = evaluate_candidate(candidate, inputs)
    else:
        if entrypoint == "pin":
            monkeypatch.setitem(REVIEW_CANDIDATES, candidate.name, candidate)
            monkeypatch.setitem(
                REVIEW_LADDERS,
                "critical",
                tuple(
                    tuple(candidate if seat.name == candidate.name else seat for seat in rung)
                    for rung in REVIEW_LADDERS["critical"]
                ),
            )
            resolution = resolve_reviewer(
                replace(inputs, pinned_candidate=candidate.name, pressure_override_reason="critical role gate probe")
            )
        else:
            resolution = resolve_reviewer(inputs, ladder=((candidate,),))
        assert resolution.selected is None
        result = next(item for item in resolution.trace if item.name == candidate.name)

    assert result.status == "excluded"
    assert result.reason == reason


def test_family_resolution_across_model_and_harness_aliases():
    cases = {
        "claude": "anthropic",
        "claude-tools": "anthropic",
        "claude-sonnet-5-5": "anthropic",
        "claude-opus-4-8": "anthropic",
        "claude-fable-5-1": "anthropic",
        "codex": "openai",
        "codex-tools": "openai",
        "gpt-6.1-sol": "openai",
        "gpt-5.6-sol": "openai",
        "gpt-5.6-terra": "openai",
        "gpt-5.6-luna": "openai",
        "gemini": "google",
        "gemini-tools": "google",
        "agy": "google",
        "gemma-4-31b-it": "google",
        "grok": "xai",
        "grok-build": "xai",
        "grok-hermes": "xai",
        "grok-4.6": "xai",
        "deepseek-v4.1-flash": "deepseek",
        "deepseek-v4-pro": "deepseek",
        "pool": "poolside",
        "glm-5.3": "zhipu",
        "qwen/qwen3.6-plus": "qwen",
        "kimi": "moonshot",
        "kimi-code/k3": "moonshot",
        "composer-2.5": "moonshot",
    }
    for seat, expected_family in cases.items():
        assert resolve_family(seat) == expected_family, seat


def test_fleet_endpoint_eligibility_is_a_projection_of_model_catalog() -> None:
    root = Path(__file__).resolve().parent.parent
    catalog = yaml.safe_load((root / "scripts/config/model_catalog.yaml").read_text(encoding="utf-8"))
    fleet = yaml.safe_load((root / "scripts/config/fleet_communications.yaml").read_text(encoding="utf-8"))
    assert fleet["formal_review_eligibility_source"].endswith("#review_scheduler.endpoints")
    policy = catalog["review_scheduler"]["endpoints"]
    aliases = {"glm-local": "glm", "kimi": "kimicc"}
    for endpoint in fleet["endpoints"]:
        policy_name = aliases.get(endpoint["name"], endpoint["name"])
        if policy_name in policy:
            assert endpoint["formal_review_eligible"] is policy[policy_name]["formal_review_eligible"]
        else:
            assert endpoint["formal_review_eligible"] is False


def test_family_resolution_unknown_and_bare_cursor_are_not_fabricated():
    assert resolve_family("") == "unknown"
    assert resolve_family("some-made-up-seat") == "unknown"
    assert resolve_family("cursor") == "unknown"
    assert resolve_family("cursor-tools") == "unknown"
    assert resolve_family("composer") == "unknown"


def test_cursor_requires_concrete_model_identity():
    assert resolve_author_family("cursor") == AMBIGUOUS_AUTHOR_FAMILY
    assert resolve_author_family("cursor-tools") == AMBIGUOUS_AUTHOR_FAMILY
    assert resolve_author_family("cursor:gpt-5.6-sol") == "openai"
    assert resolve_author_family("cursor:claude-opus-4-8") == "anthropic"
    assert resolve_author_family("cursor:composer-2.5") == "moonshot"
    assert resolve_author_family("cursor:grok-4.6") == "xai"
    assert resolve_author_family("cursor", author_family="anthropic") == "anthropic"


def test_cursor_auto_is_union_family():
    # Cursor Auto / unknown-Auto resolves to the allowlist-union family {xAI, Moonshot}.
    assert resolve_author_family("cursor:auto") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("cursor:unknown") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("cursor-auto") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("cursor-tools:auto") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("cursor-tools:unknown") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("Cursor:AUTO") == CURSOR_AUTO_UNION_FAMILY
    assert resolve_author_family("Cursor:UNKNOWN") == CURSOR_AUTO_UNION_FAMILY


def test_author_family_override_against_auto_attestation_is_a_conflict():
    # The harness attests the model was Auto; a caller-asserted single family
    # cannot be corroborated against Auto and is a fail-closed conflict.
    assert resolve_author_family("cursor:auto", author_family="openai") == CONFLICTING_AUTHOR_FAMILY
    assert resolve_author_family("cursor-auto", author_family="anthropic") == CONFLICTING_AUTHOR_FAMILY
    assert resolve_author_family("cursor:unknown", author_family="xai") == CONFLICTING_AUTHOR_FAMILY
    resolution = resolve_reviewer(ResolverInputs(author_model="cursor:auto", author_family="openai"))
    assert resolution.selected is None
    assert resolution.quorum == ()
    assert resolution.fail_closed_reason


def test_unknown_auto_author_resolves_single_reviewer_outside_union():
    for token in ("cursor:auto", "cursor:unknown", "cursor-auto"):
        for risk in ("low", "medium", "high", "critical"):
            resolution = resolve_reviewer(ResolverInputs(author_model=token, risk=risk))
            assert resolution.fail_closed_reason is None, (token, risk)
            assert resolution.selected is not None, (token, risk)
            assert resolution.selected.family not in {"xai", "moonshot"}, (token, risk)
            assert resolution.quorum == (), (token, risk)


def test_unknown_auto_author_excludes_xai_and_moonshot_candidates():
    inputs = ResolverInputs(author_model="cursor:auto", risk="medium")
    resolution = resolve_reviewer(inputs)
    for entry in resolution.trace:
        if entry.family in {"xai", "moonshot"} or entry.transport == "cursor":
            assert entry.status == "excluded", (entry.name, entry.family, entry.status)


def test_cursor_as_reviewer_excluded_against_xai_and_moonshot_authors():
    # Moonshot-family author: Cursor-transport candidates must be excluded
    kimi_inputs = ResolverInputs(author_model="kimi-code/k3")
    for cand_name in ("composer-2.5", "grok-4.7-cursor-fallback", "claude-opus-5-5-cursor-fallback"):
        cand = REVIEW_CANDIDATES[cand_name]
        res = evaluate_candidate(cand, kimi_inputs)
        assert res.status == "excluded", (cand_name, res.status)

    # xAI-family author: Cursor-transport candidates must be excluded
    grok_inputs = ResolverInputs(author_model="grok-4.6")
    for cand_name in ("composer-2.5", "grok-4.7-cursor-fallback", "claude-opus-5-5-cursor-fallback"):
        cand = REVIEW_CANDIDATES[cand_name]
        res = evaluate_candidate(cand, grok_inputs)
        assert res.status == "excluded", (cand_name, res.status)


def test_attested_cursor_author_resolves_to_model_family():
    assert resolve_author_family("cursor:grok-4.6") == "xai"
    assert resolve_author_family("cursor:composer-2.5") == "moonshot"
    res_grok = resolve_reviewer(ResolverInputs(author_model="cursor:grok-4.6", risk="medium"))
    assert res_grok.selected is not None
    assert res_grok.selected.family != "xai"
    res_comp = resolve_reviewer(ResolverInputs(author_model="cursor:composer-2.5", risk="medium"))
    assert res_comp.selected is not None
    assert res_comp.selected.family != "moonshot"


def test_invalid_or_conflicting_author_identity_fails_closed():
    assert resolve_author_family("") == UNKNOWN_AUTHOR_FAMILY
    assert resolve_author_family("unknown-seat") == UNKNOWN_AUTHOR_FAMILY
    assert resolve_author_family("cursor:gpt-5.6-sol", author_family="anthropic") == CONFLICTING_AUTHOR_FAMILY
    for inputs in (
        ResolverInputs(author_model="cursor"),
        ResolverInputs(author_model="unknown-seat"),
        ResolverInputs(author_model="cursor:gpt-5.6-sol", author_family="anthropic"),
    ):
        resolution = resolve_reviewer(inputs)
        assert resolution.selected is None
        assert resolution.trace == ()
        assert resolution.fail_closed_reason


def test_unsupported_risk_fails_closed():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="urgent"))
    assert resolution.selected is None
    assert resolution.trace == ()
    assert "unsupported review risk" in resolution.fail_closed_reason


def test_critical_uses_authority_while_routine_uses_practical_defaults():
    # #9394: OpenAI author gets Opus at critical; #9538: high is Opus too;
    # the practical defaults at medium and low remain Sonnet.
    for risk in ("critical", "high"):
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected.name == "claude-opus-5-5", risk
    for risk in ("medium", "low"):
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected.name == "claude-sonnet-5-5", risk


@pytest.mark.parametrize("author_model", ("gpt-6.1-sol", "grok-4.7"))
@pytest.mark.parametrize("review_profile", ("code", "infra"))
def test_critical_security_review_excludes_sonnet_5_5(author_model: str, review_profile: str) -> None:
    resolution = resolve_reviewer(
        ResolverInputs(author_model=author_model, review_profile=review_profile, risk="critical")
    )
    assert resolution.selected is not None
    assert resolution.selected.concrete_model != "claude-sonnet-5-5"
    assert all(entry.name != "claude-sonnet-5-5" for entry in resolution.trace)


def test_high_risk_anthropic_author_gets_strong_practical_formal_gate():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", risk="high"))
    assert resolution.selected is not None
    assert resolution.selected.name == "openai_frontier"
    assert resolution.selected.suitability_rank == 1


def test_critical_anthropic_author_gets_astra_as_formal_gate():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", risk="critical"))
    assert resolution.selected.name == "openai_frontier"
    assert resolution.selected.concrete_model == "gpt-6.1-sol"


def test_high_risk_openai_author_gets_opus_not_sonnet_or_fable():
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-5.6-terra", risk="high"))
    assert resolution.selected.name == "claude-opus-5-5"
    assert resolution.selected.transport == "native_claude"
    # Astra remains same-family advisory context, never this author’s CF gate.
    assert next(entry for entry in resolution.trace if entry.name == "openai_frontier").status == "advisory_only"


def test_high_risk_ladder_leaves_sonnet_out_so_opus_wins_the_openai_author_seat():
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="high"))
    assert resolution.selected.name == "claude-opus-5-5"
    assert resolution.selected.suitability_rank == 3
    assert "claude-sonnet-5-5" not in {item.name for item in resolution.trace}
    # At medium the practical ladder still lets Sonnet's closer fit beat Opus.
    medium = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="medium"))
    assert medium.selected.name == "claude-sonnet-5-5"
    opus = next(item for item in medium.trace if item.name == "claude-opus-5-5")
    assert opus.status == "eligible"
    assert opus.suitability_rank == 4


@pytest.mark.parametrize(
    "model",
    ["claude-fable-5", "cursor:CLAUDE-FABLE-5-thinking-high", "grok-4.6", "grok-4.6-high", "grok-4.6[context=500k]"],
)
def test_retired_model_is_excluded_before_quality_even_on_custom_ladder(model):
    candidate = replace(OPENAI_FRONTIER, name="retired-test", concrete_model=model, family="anthropic")
    resolution = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", formal_review=False), ladder=((candidate,),)
    )
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"
    assert "retired" in resolution.trace[0].reason
    assert resolution.trace[0].selection_score is None


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", "claude-sonnet-5"])
def test_critical_security_sonnet_pin_and_custom_ladder_fail_closed(model):
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk="critical",
            pinned_candidate=model,
            pressure_override_reason="test explicit pin",
        )
    )
    assert resolution.selected is None
    if model == "claude-sonnet-5":
        assert model not in REVIEW_CANDIDATES
        assert resolution.fail_closed_reason
    else:
        assert "hard eligibility gate" in resolution.fail_closed_reason
        assert "Sonnet is excluded" in next(item for item in resolution.trace if item.name == model).reason
    candidate = replace(SONNET_5_5, concrete_model=model)
    result = evaluate_candidate(candidate, ResolverInputs(author_model="codex", risk="critical"))
    assert result.status == "excluded"
    assert "Sonnet is excluded" in result.reason


@pytest.mark.parametrize("model", ["cursor:CLAUDE-SONNET-5-5-high", "claude-sonnet-5[1m]"])
def test_qualified_sonnet_pin_cannot_bypass_security_filter(model):
    candidate = replace(SONNET_5_5, concrete_model=model, model_roles=frozenset({"critical_review"}))
    result = evaluate_candidate(candidate, ResolverInputs(author_model="codex", risk="critical"))
    assert result.status == "excluded"
    assert "Sonnet is excluded" in result.reason


@pytest.mark.parametrize("author", ["gpt-6.1-sol", "claude-opus-5-5"])
def test_critical_review_never_falls_back_to_fable(author):
    """#9583: Fable is no reviewer at any risk, even when every primary seat is unhealthy."""
    assert not any(candidate.concrete_model.startswith("claude-fable") for candidate in REVIEW_CANDIDATES.values())
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model=author,
            risk="critical",
            routing_snapshot={"claude": "unhealthy", "codex": "unhealthy", "cursor": "healthy"},
        )
    )
    assert resolution.selected.concrete_model == "grok-4.7"
    assert not any(entry.name.startswith("claude-fable") for entry in resolution.trace)
    pinned = resolve_reviewer(
        ResolverInputs(
            author_model=author,
            risk="critical",
            pinned_candidate="claude-fable-5-1",
            pressure_override_reason="test explicit Fable pin",
        )
    )
    assert pinned.selected is None
    assert pinned.fail_closed_reason == "unknown explicit reviewer pin 'claude-fable-5-1'"


def test_opus_keeps_native_claude_when_native_health_is_degraded():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            risk="critical",
            routing_snapshot={"claude": "degraded", "cursor": "healthy"},
        )
    )

    assert resolution.selected.name == "claude-opus-5-5"
    assert resolution.selected.transport == "native_claude"
    assert resolution.selected.health == "degraded"


def test_high_risk_kimi_author_gets_claude_not_composer():
    resolution = resolve_reviewer(ResolverInputs(author_model="kimi-code/k3", risk="critical"))
    assert resolution.selected.name == "claude-opus-5-5"
    composer = evaluate_candidate(REVIEW_CANDIDATES["composer-2.5"], ResolverInputs(author_model="kimi-code/k3", risk="medium"))
    assert composer.status == "excluded"
    assert "same family" in composer.reason


def test_medium_risk_uses_sonnet_and_keeps_pool_eligible():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert resolution.selected.name == "claude-sonnet-5-5"
    assert next(entry for entry in resolution.trace if entry.name == "pool").status == "excluded"


def test_low_risk_pool_author_gets_astra_before_economical_routes():
    resolution = resolve_reviewer(ResolverInputs(author_model="pool", risk="low"))
    assert resolution.selected.name == "openai_frontier"


def test_policy_receipt_exposes_catalog_version_date_and_risk():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="high"))
    assert resolution.policy_version == "deterministic-formal-routing.v2"
    assert resolution.catalog_reviewed_on == "2026-09-24"
    assert resolution.resolved_risk == "high"


def test_codexbar_unavailable_status_fail_open_does_not_ban_lane():
    """Probe failure (status=unavailable) is missing evidence, not a dead seat."""
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-luna",
            author_family="openai",
            risk="medium",
            routing_snapshot={
                "agents": {
                    "claude": {"status": "unavailable"},
                    "codex": {"status": "unavailable"},
                }
            },
        )
    )
    assert resolution.selected is not None
    assert resolution.selected.name == "claude-sonnet-5-5"
    assert resolution.selected.health in {None, "healthy"}


def test_unhealthy_route_is_unavailable_and_falls_to_the_next_quality_tier():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            risk="medium",
            routing_snapshot={"codex": "unhealthy", "cursor": "healthy"},
        )
    )
    # Practical ladder: Astra dark → Sonnet 5.5 (Claude healthy by default).
    assert resolution.selected.name == "claude-sonnet-5-5"
    terra = next(entry for entry in resolution.trace if entry.name == "openai_frontier")
    assert terra.status == "excluded"
    assert "unhealthy" in terra.reason


def test_real_routing_budget_payload_is_normalized_without_crashing():
    snapshot = {
        "generated_at": "2026-07-17T00:00:00Z",
        "agents": {
            "gemini": {"status": "hot", "health": {"healthy": True}},
            "grok": {"status": "cool", "health": {"healthy": True}},
            "claude": {"status": "warm", "health": {"healthy": True}},
        },
    }
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium", routing_snapshot=snapshot))
    assert resolution.selected.name == "claude-sonnet-5-5"
    assert resolution.selected.health == "degraded"


def test_gemini_lane_outage_does_not_create_code_review_route():
    snapshot = {
        "agents": {
            "gemini": {"status": "unknown", "health": {"healthy": False}},
            "grok": {"status": "cool", "health": {"healthy": True}},
        }
    }
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium", routing_snapshot=snapshot))
    assert resolution.selected.name == "claude-sonnet-5-5"
    assert all(not entry.concrete_model.startswith("gemini-") for entry in resolution.trace)


def test_gemini_code_review_refused_even_in_injected_ladder_and_pin(monkeypatch):
    injected = replace(
        SONNET_5_5,
        name="injected-gemini",
        concrete_model="gemini-3.8-flash-high",
        family="google",
        route="agy",
        transport="agy",
    )
    inputs = ResolverInputs(author_model="codex", risk="medium")
    result = evaluate_candidate(injected, inputs)
    assert result.status == "excluded"
    assert "operator 2026-09-25" in result.reason
    resolution = resolve_reviewer(inputs, ladder=((injected,),))
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"
    assert "Gemini reviews Ukrainian only, never code" in resolution.trace[0].reason
    monkeypatch.setitem(REVIEW_CANDIDATES, injected.name, injected)
    pinned = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            pinned_candidate=injected.name,
            pressure_override_reason="explicit regression pin",
        ),
        ladder=((injected,),),
    )
    assert pinned.selected is None
    assert "hard eligibility gate" in pinned.fail_closed_reason


def test_health_statuses_are_case_normalized_and_unsupported_values_fail_closed():
    unhealthy = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "UNHEALTHY", "grok": "healthy"},
        )
    )
    assert unhealthy.selected.name == "claude-sonnet-5-5"

    invalid = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "cooldown"},
        )
    )
    assert invalid.selected is None
    assert invalid.trace == ()
    assert "invalid routing snapshot" in invalid.fail_closed_reason


def test_pre_launch_is_healthy_and_unknown_is_fail_open():
    pre_launch = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "pre_launch", "grok": "near_cap"},
        )
    )
    assert pre_launch.selected.name == "claude-sonnet-5-5"
    assert pre_launch.selected.health is None

    unknown = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "unknown", "grok": "unknown"},
        )
    )
    missing = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert unknown.selected.name == missing.selected.name == "claude-sonnet-5-5"
    assert unknown.substitution_note is None


def test_near_cap_receives_no_new_automatic_assignment_and_uses_eligible_fallback():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            risk="medium",
            routing_snapshot={"codex": "near_cap", "cursor": "healthy"},
        )
    )
    assert resolution.selected is not None
    assert resolution.selected.name == "claude-sonnet-5-5"
    terra = next(item for item in resolution.trace if item.name == "openai_frontier")
    assert terra.status == "excluded"
    assert "automatic assignments are prohibited" in terra.reason


def test_all_top_tier_routes_unavailable_fall_to_next_quality_tier():
    snapshot = {
        "claude": "unhealthy",
        "cursor": "unhealthy",
        "codex": "unhealthy",
        "agy": "unhealthy",
        "gemini": "unhealthy",
        "grok": "healthy",
    }
    resolution = resolve_reviewer(
        ResolverInputs(author_model="kimi-code/k3", risk="critical", routing_snapshot=snapshot)
    )
    assert resolution.selected.name == "grok-4.7"


def test_native_grok_health_and_cursor_transport_fallback():
    snapshot = {"grok": "unhealthy", "cursor": "healthy", "claude": "unhealthy", "codex": "unhealthy", "agy": "unhealthy", "kimi": "unhealthy"}
    injected = resolve_reviewer(ResolverInputs(author_model="claude", risk="medium", routing_snapshot=snapshot), ladder=((GROK_4_7, GROK_4_7_CURSOR_FALLBACK),))
    native = next(item for item in injected.trace if item.name == "grok-4.7")
    assert native.status == "excluded" and "lane health is unhealthy" in native.reason
    assert injected.selected.name == "grok-4.7-cursor-fallback"
    dark = resolve_reviewer(ResolverInputs(author_model="claude", risk="medium", routing_snapshot={**snapshot, "cursor": "unhealthy"}))
    assert dark.selected is None
    assert next(item for item in dark.trace if item.name == "grok-4.7-cursor-fallback").reason == "lane health is unhealthy — route is operationally unavailable"


def test_missing_health_signal_is_fail_open():
    empty = resolve_reviewer(ResolverInputs(author_model="codex", risk="low", routing_snapshot={}))
    absent = resolve_reviewer(ResolverInputs(author_model="codex", risk="low", routing_snapshot=None))
    assert empty.selected.name == absent.selected.name == "claude-sonnet-5-5"


def test_family_exclusion_is_not_mislabeled_as_a_substitution():
    resolution = resolve_reviewer(ResolverInputs(author_model="gemini", risk="medium"))
    assert resolution.selected.name == "openai_frontier"
    assert resolution.substitution_note is None


def test_health_breaks_ties_only_within_the_same_remaining_quality_rung():
    # With sequential practical rungs, the first eligible practical seat wins even
    # when near_cap (near_cap never demotes out of its rung).
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={
                "cursor": "unhealthy",
                "claude": "unhealthy",
                "grok": "unhealthy",
                "agy": "unhealthy",
                "gemini": "unhealthy",
                "kimi": "near_cap",
                "deepseek-v4-pro": "healthy",
            },
        )
    )
    assert resolution.selected is None


def test_deepseek_is_absent_from_automatic_ladders_even_when_other_lanes_are_dark():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="low",
            routing_snapshot={
                "cursor": "unhealthy",
                "claude": "unhealthy",
                "grok": "unhealthy",
                "agy": "unhealthy",
                "gemini": "unhealthy",
                "kimi": "unhealthy",
                "glm": "unhealthy",
                # Dark Pro by candidate name; leave route "deepseek" open for Flash.
                "deepseek-v4-pro": "unhealthy",
                "pool": "unhealthy",
            },
            data_egress_policy="local_interactive",
        )
    )
    assert resolution.selected is None
    assert all(item.family != "deepseek" for item in resolution.trace)


def test_folk_content_excludes_both_deepseek_models():
    for candidate in (DEEPSEEK_V4_PRO, DEEPSEEK_V4_1_FLASH):
        result = evaluate_candidate(
            candidate,
            ResolverInputs(author_model="claude", domain="folk_content", formal_review=False),
            author_family="anthropic",
        )
        assert result.status == "excluded"
        assert "DeepSeek is excluded" in result.reason


def test_glm_data_egress_gate_is_fail_closed():
    # Explicit pin bypasses retirement so the egress gate is still testable.
    for policy in (None, "ci_automated"):
        result = evaluate_candidate(
            GLM,
            ResolverInputs(
                author_model="claude",
                data_egress_policy=policy,
                pinned_candidate=GLM.name,
                pressure_override_reason="fixture pin for egress gate",
            ),
            author_family="anthropic",
        )
        assert result.status == "excluded"
    eligible = evaluate_candidate(
        GLM,
        ResolverInputs(
            author_model="claude",
            data_egress_policy="local_interactive",
            requested_role="security_review",
            pinned_candidate=GLM.name,
            pressure_override_reason="fixture pin for egress gate",
        ),
        author_family="anthropic",
    )
    assert eligible.status == "eligible"


def test_glm_automatic_selection_is_retired_without_explicit_pin():
    result = evaluate_candidate(
        GLM,
        ResolverInputs(
            author_model="claude",
            data_egress_policy="local_interactive",
            requested_role="security_review",
        ),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert result.reason == "retired→cursor"


def test_qwen_is_excluded_from_automatic_routing():
    result = evaluate_candidate(
        QWEN,
        ResolverInputs(author_model="claude"),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "cost" in result.reason


def test_required_capabilities_and_isolation_fail_closed():
    missing = evaluate_candidate(
        POOL,
        ResolverInputs(author_model="claude", required_capabilities=frozenset({"vesum_mcp"}), formal_review=False),
        author_family="anthropic",
    )
    assert missing.status == "excluded"
    assert "capabilities" in missing.reason

    isolation = evaluate_candidate(
        REVIEW_CANDIDATES["claude-opus-5-5-cursor-fallback"],
        ResolverInputs(author_model="codex", isolation_required=True, formal_review=False),
        author_family="openai",
    )
    assert isolation.status == "excluded"
    assert "isolation" in isolation.reason


def test_review_profile_is_a_hard_eligibility_filter():
    result = evaluate_candidate(
        OPENAI_FRONTIER,
        ResolverInputs(author_model="claude", review_profile="content", formal_review=False),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "profile exclusion" in result.reason


def test_learner_content_profile_fails_before_reviewer_ladder_resolution():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", review_profile="content"))

    assert resolution.selected is None
    assert resolution.trace == ()
    assert resolution.advisory == ()
    assert "unsupported local-code-review profile" in resolution.fail_closed_reason
    assert "post-build-review" in resolution.fail_closed_reason


def test_custom_ladder_still_supported_for_focused_callers():
    resolution = resolve_reviewer(
        ResolverInputs(author_model="deepseek-v4-pro", risk="medium"),
        ladder=((DEEPSEEK_V4_1_FLASH,),),
    )
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"


def test_same_tier_balancing_is_stable_and_yaml_order_independent(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    inputs = ResolverInputs(author_model="gemini", exact_head="a" * 40)
    forward = resolve_reviewer(inputs, ladder=((PRACTICAL_ASTRA, sonnet),))
    reverse = resolve_reviewer(inputs, ladder=((sonnet, PRACTICAL_ASTRA),))

    assert forward.selected is not None
    assert forward.selected.name == reverse.selected.name
    assert forward.selected.selection_score == reverse.selected.selection_score
    assert forward.selected.selection_score is not None


def test_load_capacity_headroom_and_freshness_balance_only_within_best_tier(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    ladder = ((PRACTICAL_ASTRA, sonnet),)
    inputs = ResolverInputs(author_model="gemini", exact_head="b" * 40, requested_role="implementation")
    capacity_weighted = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 500, "active_reserved_input_bytes": 0}},
            "claude": {"scheduler": {"completed_input_bytes": 600, "active_reserved_input_bytes": 0}},
        }
    }
    weighted_terra = replace(PRACTICAL_ASTRA, capacity_weight=2.0)
    weighted = resolve_reviewer(inputs, ladder=((weighted_terra, sonnet),), runtime_state=capacity_weighted)
    assert weighted.selected.name == "synthetic-practical-astra"

    headroom = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 10, "quota_remaining_pct": 5}},
            "claude": {"scheduler": {"completed_input_bytes": 10, "quota_remaining_pct": 90}},
        }
    }
    selected = resolve_reviewer(inputs, ladder=ladder, runtime_state=headroom)
    assert selected.selected.name == "claude-sonnet-5-5"

    stale_codex = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 10, "quota_stale": True}},
            "claude": {"scheduler": {"completed_input_bytes": 10, "quota_stale": False}},
        }
    }
    assert resolve_reviewer(inputs, ladder=ladder, runtime_state=stale_codex).selected.name == "claude-sonnet-5-5"

    # A stale route with deceptively low recorded load must not outrank a
    # fresh, verified route solely because its last-known-good counter is old.
    stale_low_load = {
        "agents": {
            "codex": {
                "scheduler": {
                    "completed_input_bytes": 0,
                    "quota_remaining_pct": 90,
                    "quota_stale": True,
                }
            },
            "claude": {
                "scheduler": {
                    "completed_input_bytes": 100,
                    "quota_remaining_pct": 90,
                    "quota_stale": False,
                }
            },
        }
    }
    assert resolve_reviewer(inputs, ladder=ladder, runtime_state=stale_low_load).selected.name == "claude-sonnet-5-5"


def test_deterministic_stress_follows_capacity_only_for_equally_suitable_authority_models():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    opus = replace(REVIEW_CANDIDATES["claude-opus-5-5"], capacity_weight=2.0)
    counts = {"openai_frontier": 0, "claude-opus-5-5": 0}
    assigned_bytes = {"codex": 0, "claude": 0}

    for index in range(120):
        snapshot = {
            "agents": {
                route: {
                    "status": "healthy",
                    "scheduler": {
                        "completed_input_bytes": assigned,
                        "active_reserved_input_bytes": 0,
                        "quota_remaining_pct": 75,
                    },
                }
                for route, assigned in assigned_bytes.items()
            }
        }
        resolution = resolve_reviewer(
            ResolverInputs(author_model="gemini", risk="critical", exact_head=f"{index:040x}"),
            ladder=((sol, opus),),
            runtime_state=snapshot,
        )
        selected = resolution.selected
        assert selected is not None
        counts[selected.name] += 1
        assigned_bytes[selected.route] += 1_000

    assert counts == {"openai_frontier": 40, "claude-opus-5-5": 80}
    assert assigned_bytes == {"codex": 40_000, "claude": 80_000}


def test_kimi_never_receives_automatic_review_load():
    """Kimi seats admit web, UI and backend coding only: no Kimi candidate is ever evaluated or selected."""
    counts = {"openai_frontier": 0}
    assigned_bytes = {"codex": 0, "kimi": 0}

    for index in range(20):
        runtime_state = {
            "agents": {
                route: {
                    "status": "healthy",
                    "scheduler": {
                        "completed_input_bytes": assigned,
                        "active_reserved_input_bytes": 0,
                        "quota_remaining_pct": 80,
                    },
                }
                for route, assigned in assigned_bytes.items()
            }
        }
        resolution = resolve_reviewer(
            ResolverInputs(author_model="claude", risk="high", requested_role="standard_review", exact_head=f"{index:040x}"),
            runtime_state=runtime_state,
        )
        selected = resolution.selected
        assert selected is not None
        assert selected.name == "openai_frontier"
        counts[selected.name] += 1
        assigned_bytes[selected.quota_bucket] += 1_000
        assert not [item for item in resolution.trace if item.quota_bucket == "kimi"]

    assert counts == {"openai_frontier": 20}
    assert assigned_bytes == {"codex": 20_000, "kimi": 0}


def test_weaker_idle_or_cheaper_route_never_beats_the_best_suitable_quality_tier(practical_astra):
    weaker = REVIEW_CANDIDATES["pool-xs"]
    resolution = resolve_reviewer(
        ResolverInputs(author_model="gemini", formal_review=False, exact_head="e" * 40),
        ladder=((PRACTICAL_ASTRA,), (weaker,)),
        runtime_state={
            "agents": {
                "codex": {
                    "scheduler": {
                        "completed_input_bytes": 9_000_000,
                        "active_reserved_input_bytes": 1_000_000,
                        "quota_remaining_pct": 1,
                    }
                },
                "pool": {
                    "scheduler": {
                        "completed_input_bytes": 0,
                        "active_reserved_input_bytes": 0,
                        "quota_remaining_pct": 100,
                    }
                },
            }
        },
    )
    assert resolution.selected.name == "synthetic-practical-astra"
    assert resolution.selected.quality_tier == "frontier_practical"
    weaker_trace = next(item for item in resolution.trace if item.name == "pool-xs")
    assert weaker_trace.status == "excluded"
    assert "suitability" in weaker_trace.reason


def test_near_cap_falls_to_a_healthy_same_quality_suitable_candidate(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    resolution = resolve_reviewer(
        ResolverInputs(author_model="gemini", risk="medium"),
        ladder=((sonnet, PRACTICAL_ASTRA),),
        runtime_state={"agents": {"claude": {"status": "near_cap"}, "codex": {"status": "healthy"}}},
    )
    assert resolution.selected.name == "synthetic-practical-astra"
    sonnet_trace = next(item for item in resolution.trace if item.name == "claude-sonnet-5-5")
    assert sonnet_trace.status == "excluded"
    assert "near cap" in sonnet_trace.reason


def test_circuit_and_shared_bucket_are_hard_exclusions_before_balancing(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    ladder = ((PRACTICAL_ASTRA, sonnet),)
    inputs = ResolverInputs(author_model="gemini", exact_head="c" * 40)
    circuit = resolve_reviewer(
        inputs,
        ladder=ladder,
        runtime_state={"agents": {"codex": {"scheduler": {"circuit_open": True}}}},
    )
    assert circuit.selected.name == "claude-sonnet-5-5"
    assert "circuit is open" in next(item.reason for item in circuit.trace if item.name == "synthetic-practical-astra")

    bucket = resolve_reviewer(inputs, ladder=ladder, excluded_quota_buckets=frozenset({"codex"}))
    assert bucket.selected.name == "claude-sonnet-5-5"
    assert "already reserved" in next(item.reason for item in bucket.trace if item.name == "synthetic-practical-astra")

    full_credential = resolve_reviewer(
        inputs,
        ladder=ladder,
        runtime_state={"agents": {"codex": {"scheduler": {"capacity_exhausted": True}}}},
    )
    assert full_credential.selected.name == "claude-sonnet-5-5"
    assert "no unreserved concurrency slot" in next(
        item.reason for item in full_credential.trace if item.name == "synthetic-practical-astra"
    )


def test_explicit_pin_requires_reason_and_cannot_bypass_formal_transport_gate(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    missing_reason = resolve_reviewer(
        ResolverInputs(author_model="gemini", pinned_candidate=sonnet.name), ladder=((PRACTICAL_ASTRA, sonnet),)
    )
    assert missing_reason.selected is None
    assert "pressure_override_reason" in missing_reason.fail_closed_reason

    # Composer is a Cursor model the formal endpoint does not pin (#9488).
    unsafe = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            pinned_candidate="composer-2.5",
            pressure_override_reason="native capacity incident",
        ),
        ladder=((REVIEW_CANDIDATES["composer-2.5"],),),
    )
    assert unsafe.selected is None
    assert "hard eligibility" in unsafe.fail_closed_reason
    assert unsafe.trace[0].reason == "sealed endpoint 'cursor' is not pinned for model 'composer-2.5'"


def test_explicit_pin_may_override_ladder_preference_but_not_hard_gates():
    # At medium the ladder prefers Sonnet for an OpenAI author; the pin overrides that.
    pin = REVIEW_CANDIDATES["claude-opus-5-5"]
    selected = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            author_family="openai",
            risk="medium",
            pinned_candidate=pin.name,
            pressure_override_reason="operator requested Opus dissent",
        )
    )
    assert selected.selected is not None
    assert selected.selected.name == "claude-opus-5-5"
    assert "explicit pressure override" in selected.substitution_note

    same_family = resolve_reviewer(
        ResolverInputs(
            author_model="claude-sonnet-5-5",
            author_family="anthropic",
            risk="medium",
            pinned_candidate=pin.name,
            pressure_override_reason="operator requested Opus dissent",
        )
    )
    assert same_family.selected is None
    assert "hard eligibility" in same_family.fail_closed_reason
    assert next(item for item in same_family.trace if item.name == pin.name).status == "excluded"


def test_unknown_explicit_pin_fails_closed_before_candidate_walk():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            pinned_candidate="not-a-catalog-candidate",
            pressure_override_reason="test",
        )
    )
    assert resolution.selected is None
    assert resolution.trace == ()
    assert "unknown explicit reviewer pin" in resolution.fail_closed_reason


def test_kimi_k3_is_not_a_review_candidate_and_its_pin_fails_closed():
    """Formerly the explicit kimicc ACPX review participant; Kimi seats now admit web, UI and backend coding only."""
    assert "kimi-k3" not in REVIEW_CANDIDATES
    assert not [c for c in REVIEW_CANDIDATES.values() if c.family == "moonshot" and c.route in {"kimi", "kimicc"}]
    resolution = resolve_reviewer(
        ResolverInputs(author_model="codex", pinned_candidate="kimi-k3", pressure_override_reason="test pin")
    )
    assert resolution.selected is None
    assert "unknown explicit reviewer pin" in resolution.fail_closed_reason


def test_glm_on_ladder_is_skipped_unless_explicitly_pinned():
    """Even if a caller still lists glm on a ladder, automatic resolve skips it."""
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-sol",
            author_family="openai",
            review_profile="infra",
            risk="medium",
            data_egress_policy="local_interactive",
            exact_head="f" * 40,
        ),
        ladder=((GLM,), (SONNET_5_5,)),
    )

    assert resolution.selected is not None
    assert resolution.selected.name == "claude-sonnet-5-5"
    glm_entry = next(entry for entry in resolution.trace if entry.name == "glm-5.3")
    assert glm_entry.status == "excluded"
    assert glm_entry.reason == "retired→cursor"


def test_explicit_glm_pin_remains_eligible_with_egress_policy():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-sol",
            author_family="openai",
            review_profile="infra",
            risk="medium",
            data_egress_policy="local_interactive",
            exact_head="f" * 40,
            pinned_candidate="glm-5.3",
            pressure_override_reason="operator-requested glm-5.3 pin",
        ),
    )
    assert resolution.selected is not None
    assert resolution.selected.name == "glm-5.3"
    assert resolution.selected.family == "zhipu"


def test_sealed_acpx_receipt_exposes_participant_and_credential_bucket_sharing():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", exact_head="d" * 40))
    selected = resolution.selected
    assert selected is not None
    assert selected.participant == "codex"
    assert selected.adapter_transport == "acp"
    assert selected.sealed_executable == "agent_runtime.runner:invoke_inter_agent"
    assert selected.quota_bucket == "codex"
    assert selected.credential_bucket == "codex"
    assert selected.quota_limit == selected.credential_limit == 1

    # Kimi seats admit web, UI and backend coding only: no review candidate binds a Kimi participant.
    assert not [c for c in REVIEW_CANDIDATES.values() if c.participant in {"kimi", "kimicc"}]


def test_every_risk_ladder_has_unique_candidates_and_a_cross_family_outcome():
    for risk, ladder in REVIEW_LADDERS.items():
        names = [candidate.name for rung in ladder for candidate in rung]
        assert len(names) == len(set(names))
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected is not None
        assert resolution.selected.family != "openai"


@pytest.mark.parametrize("risk", ["critical", "high", "medium", "low"])
def test_ladders_place_native_and_cursor_grok_directly_after_opus(risk):
    ladder = REVIEW_LADDERS[risk]
    assert [rung[0].name for rung in ladder[:5]] == ["openai_frontier", "claude-opus-5-5", "grok-4.7", "grok-4.7-cursor-fallback", "claude-opus-5-5-cursor-fallback"]
    if risk == "critical":
        assert [rung[0].name for rung in ladder[5:]] == ["composer-2.5", "pool", "pool-xs"]
    elif risk == "high":
        assert {c.concrete_model for rung in ladder for c in rung} == {"gpt-6.1-sol", "claude-opus-5-5", "grok-4.7"}
    else:
        assert ladder[5][0].name == "claude-sonnet-5-5"
        assert ladder[7][0].name == "pool"
        assert "glm-5.3" not in {c.name for rung in ladder for c in rung}


def test_medium_codex_author_keeps_sonnet_ahead_of_unavailable_opus():
    ladder = REVIEW_LADDERS["medium"]
    without_opus = tuple(rung for rung in ladder if not rung[0].name.startswith("claude-opus-5-5"))
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="medium"), ladder=without_opus)
    assert resolution.selected.concrete_model == "claude-sonnet-5-5"


def test_old_sonnet_record_still_resolves_anthropic_family():
    assert resolve_author_family("claude-sonnet-5") == "anthropic"
    assert "claude-sonnet-5" not in REVIEW_CANDIDATES


def test_candidate_constants_preserve_expected_identity():
    assert OPENAI_FRONTIER.concrete_model == "gpt-6.1-sol"
    assert "kimi-k3" not in REVIEW_CANDIDATES
    assert POOL.concrete_model == "poolside/laguna-s-2.1"
    assert POOL.invocation.endswith("ask-pool")
    assert GLM.requires_data_egress_policy == "local_interactive"
    assert GLM.invocation.endswith("ask-glm")
    assert GROK_4_7.transport == "native_grok"
    from scripts.review.reviewer_resolver import GROK_4_7_CURSOR_FALLBACK, SONNET_5_5

    assert GROK_4_7_CURSOR_FALLBACK.transport == "cursor"
    assert GROK_4_7_CURSOR_FALLBACK.concrete_model == "grok-4.7"
    assert SONNET_5_5.concrete_model == "claude-sonnet-5-5"


def test_contradictory_snapshot_surfaces_degraded_telemetry_reason():
    """Self-contradictory telemetry (healthy=true + status=unavailable) surfaces degraded_telemetry reason."""
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude-sonnet-5",
            author_family="anthropic",
            risk="medium",
            routing_snapshot={
                "agents": {
                    "codex": {"health": {"healthy": True}, "status": "unavailable"},
                }
            },
        )
    )
    codex_entry = next(entry for entry in resolution.trace if entry.name == "openai_frontier")
    assert codex_entry.status == "excluded"
    assert "degraded_telemetry" in codex_entry.reason
    assert "healthy=true, status=unavailable" in codex_entry.reason


def test_glm_egress_exclusion_reason_names_unlock_flag():
    """GLM fail-closed egress policy exclusion names the unlocking flag."""
    result = evaluate_candidate(
        GLM,
        ResolverInputs(
            author_model="claude",
            data_egress_policy=None,
            pinned_candidate=GLM.name,
            pressure_override_reason="fixture pin for egress gate",
        ),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "requires --data-egress-policy local_interactive" in result.reason


def test_astra_authors_never_receive_openai_cross_family_review():
    for risk in ("low", "medium", "high", "critical"):
        resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk=risk))
        assert resolution.selected is not None
        assert resolution.selected.family != "openai"
        for entry in resolution.trace:
            if REVIEW_CANDIDATES[entry.name].family == "openai":
                assert entry.status == ("advisory_only" if entry.name == "openai_frontier" else "excluded")


def test_actual_catalog_resolver_imports_and_selects_approved_codex_model():
    assert "gpt-5.6-terra" not in REVIEW_CANDIDATES
    result = resolve_reviewer(ResolverInputs(author_model="claude", risk="medium"))
    assert result.selected is not None
    assert result.selected.concrete_model == "gpt-6.1-sol"


def test_sealed_executable_catalog_and_resolver_parity():
    import dataclasses

    from scripts.review.reviewer_resolver import _SEALED_REVIEW_EXECUTABLE, _hard_exclusion_reason

    assert _SEALED_REVIEW_EXECUTABLE == "agent_runtime.runner:invoke_inter_agent"
    for name, candidate in REVIEW_CANDIDATES.items():
        if candidate.formal_review_eligible:
            assert candidate.sealed_executable == _SEALED_REVIEW_EXECUTABLE, (
                f"{name} sealed_executable {candidate.sealed_executable!r} != {_SEALED_REVIEW_EXECUTABLE!r}"
            )
            # Normal inputs pass sealed_executable hard exclusion
            inputs = ResolverInputs(
                author_model="gemini",
                risk="medium",
                formal_review=True,
                review_profile="code",
            )
            reason = _hard_exclusion_reason(candidate, inputs)
            assert reason != "candidate is not bound to the sealed ACP executable"

            # Tampered executable is rejected
            mismatched = dataclasses.replace(candidate, sealed_executable="other.module:func")
            assert _hard_exclusion_reason(mismatched, inputs) == "candidate is not bound to the sealed ACP executable"


def _grok_trace(resolution):
    return {entry.name: entry for entry in resolution.trace if entry.name.startswith("grok")}


def test_resolve_reviewer_subject_seat_for_grok_adapter_never_selects_grok():
    """AC-01: a Grok adapter change excludes every Grok seat and says why."""
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            risk="high",
            owned_paths=("scripts/agent_runtime/adapters/grok_build.py",),
        ),
        ladder=(*REVIEW_LADDERS["high"], (GROK_4_7, GROK_4_7_CURSOR_FALLBACK)),
    )
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family != "xai"
    assert not resolution.selected.name.startswith("grok")
    assert resolution.selected.name == "openai_frontier"
    grok = _grok_trace(resolution)
    assert set(grok) >= {"grok-4.7", "grok-4.7-cursor-fallback"}
    for entry in grok.values():
        assert entry.status == "excluded"
        assert entry.reason is not None
        assert "subject exclusion" in entry.reason
        assert "subject seat grok" in entry.reason
        assert "scripts/agent_runtime/adapters/grok_build.py" in entry.reason


def test_resolve_reviewer_subject_seat_blocks_grok_when_claude_lane_is_unhealthy():
    """The #8912 shape (Grok adapter, codex author, infra domain) at medium risk, where Grok may review (#9538)."""
    without = resolve_reviewer(
        ResolverInputs(
            author_model="codex:gpt-6.1-sol",
            domain="infra",
            risk="medium",
            routing_snapshot={"claude": "unhealthy"},
        ),
        ladder=(*REVIEW_LADDERS["high"], (GROK_4_7, GROK_4_7_CURSOR_FALLBACK)),
    )
    # #9769: native Grok is the regular fallback when Anthropic is unavailable.
    assert without.selected.concrete_model == "grok-4.7"
    assert _grok_trace(without)["grok-4.7"].status in {"eligible", "selected"}

    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex:gpt-6.1-sol",
            domain="infra",
            risk="medium",
            routing_snapshot={"claude": "unhealthy"},
            owned_paths=("scripts/agent_runtime/adapters/grok_build.py",),
        ),
        ladder=(*REVIEW_LADDERS["high"], (GROK_4_7, GROK_4_7_CURSOR_FALLBACK)),
    )
    assert resolution.selected is None
    grok = next(entry for entry in resolution.trace if entry.name == "grok-4.7")
    assert grok.status == "excluded"
    assert "subject exclusion" in grok.reason
    fallback = next(entry for entry in resolution.trace if entry.name == "grok-4.7-cursor-fallback")
    assert fallback.status == "excluded"
    assert "subject seat grok" in fallback.reason


def test_resolve_reviewer_explicit_subject_family_excludes_xai_without_guessing_paths():
    resolution = resolve_reviewer(
        ResolverInputs(author_model="claude", risk="medium", subject_families=frozenset({"xai"})),
        ladder=(*REVIEW_LADDERS["high"], (GROK_4_7, GROK_4_7_CURSOR_FALLBACK)),
    )
    assert resolution.selected is not None
    assert resolution.selected.family != "xai"
    grok = next(entry for entry in resolution.trace if entry.name == "grok-4.7")
    assert grok.status == "excluded"
    assert "subject family xai" in grok.reason
    assert "paths=" not in grok.reason


def test_resolve_reviewer_without_subject_information_matches_empty_subject_fields():
    """AC-02: explicit empty subject inputs do not change the trace."""
    authors = (
        dict(author_model="claude", risk="medium"),
        dict(author_model="claude", risk="high"),
        dict(author_model="codex", risk="high"),
        dict(author_model="codex:gpt-6.1-sol", risk="high", domain="infra"),
        dict(author_model="cursor:auto", risk="medium"),
        dict(author_model="kimi-code/k3", risk="critical"),
        dict(author_model="pool", risk="low"),
        dict(author_model="gpt-5.6-terra", risk="high"),
    )
    for kwargs in authors:
        plain = resolve_reviewer(ResolverInputs(**kwargs))
        empty = resolve_reviewer(
            ResolverInputs(
                **kwargs,
                subject_seats=frozenset(),
                subject_families=frozenset(),
                owned_paths=(),
                subject_evidence=(),
            )
        )
        assert plain == empty, kwargs


def test_resolve_reviewer_unrelated_owned_path_does_not_change_selection():
    plain = resolve_reviewer(ResolverInputs(author_model="claude", risk="high"))
    with_readme = resolve_reviewer(ResolverInputs(author_model="claude", risk="high", owned_paths=("README.md",)))
    assert with_readme == plain
    assert with_readme.selected is not None
    assert with_readme.selected.name == "openai_frontier"


def test_resolve_reviewer_ambiguous_adapter_path_requires_explicit_subject():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="high",
            owned_paths=("scripts/agent_runtime/adapters/acpx.py",),
        )
    )
    assert resolution.selected is None
    assert resolution.trace == ()
    assert resolution.fail_closed_reason is not None
    assert "ambiguous subject-seat inference" in resolution.fail_closed_reason
    assert "acpx.py" in resolution.fail_closed_reason
    assert "--subject-seat" in resolution.fail_closed_reason

    explicit = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            risk="high",
            subject_seats=frozenset({"grok"}),
            owned_paths=("scripts/agent_runtime/adapters/acpx.py",),
        )
    )
    assert explicit.fail_closed_reason is None
    assert explicit.selected is not None
    assert explicit.selected.family != "xai"


def test_resolve_reviewer_subject_seat_kimi_does_not_exclude_composer():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            owned_paths=("site/src/app.ts",),
            subject_seats=frozenset({"kimi"}),
        )
    )
    assert not [entry for entry in resolution.trace if entry.quota_bucket == "kimi"]
    composer = next(entry for entry in resolution.trace if entry.name == "composer-2.5")
    assert "subject exclusion" not in (composer.reason or "")


def test_resolve_reviewer_subject_seat_cursor_excludes_cursor_transport_only():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            subject_seats=frozenset({"cursor"}),
        )
    )
    native = next(entry for entry in resolution.trace if entry.name == "claude-opus-5-5")
    fallback = next(entry for entry in resolution.trace if entry.name == "claude-opus-5-5-cursor-fallback")
    composer = next(entry for entry in resolution.trace if entry.name == "composer-2.5")
    assert "subject exclusion" not in (native.reason or "")
    assert fallback.status == "excluded"
    assert "subject seat cursor" in fallback.reason
    assert composer.status == "excluded"
    assert "subject seat cursor" in composer.reason


def test_resolve_reviewer_unknown_subject_seat_and_family_fail_closed():
    bad_seat = resolve_reviewer(ResolverInputs(author_model="codex", subject_seats=frozenset({"not-a-seat"})))
    assert bad_seat.selected is None
    assert bad_seat.trace == ()
    assert "unknown subject seat" in bad_seat.fail_closed_reason

    bad_family = resolve_reviewer(ResolverInputs(author_model="codex", subject_families=frozenset({"cursor"})))
    assert bad_family.selected is None
    assert "unknown subject family" in bad_family.fail_closed_reason


def test_resolve_reviewer_subject_seat_pin_cannot_select_the_governed_seat():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="high",
            subject_seats=frozenset({"grok-4.7"}),
            pinned_candidate="grok-4.7",
            pressure_override_reason="operator pin",
        )
    )
    assert resolution.selected is None
    assert "hard eligibility" in resolution.fail_closed_reason
    grok = next(entry for entry in resolution.trace if entry.name == "grok-4.7")
    assert grok.status == "excluded"
    assert "subject seat grok" in grok.reason


@pytest.mark.repo_wide
def test_resolve_reviewer_classifies_every_adapter_and_reviewer_hook():
    from scripts.review.subject_seat import KNOWN_SUBJECT_SEATS, adapter_subject_index, classify_owned_path

    repo = Path(__file__).resolve().parent.parent
    expected = {
        "__init__.py": None,
        "_output_schema.py": None,
        "_template.py": None,
        "acpx.py": None,
        "agy.py": "agy",
        "base.py": None,
        "claude.py": "claude",
        "codex.py": "codex",
        "codex_events.py": "codex",
        "cursor.py": "cursor",
        "deepseek.py": "deepseek",
        "gemini.py": "gemini",
        "glm.py": "glm",
        "grok_build.py": "grok",
        "hermes_common.py": None,
        "hermes_deepseek.py": "deepseek",
        "hermes_grok.py": "grok",
        "hermes_qwen.py": "qwen",
        "kimi.py": "kimi",
        "kimicc.py": "kimi",
    }
    adapter_dir = repo / "scripts/agent_runtime/adapters"
    found = sorted(path.name for path in adapter_dir.glob("*.py"))
    assert found == sorted(expected)
    for name, seat in expected.items():
        classified = classify_owned_path(f"scripts/agent_runtime/adapters/{name}")
        if seat is None:
            assert classified.kind == "ambiguous", name
        else:
            assert classified.kind == "seat", name
            assert classified.seats == frozenset({seat})
            assert seat in KNOWN_SUBJECT_SEATS

    hooks = {
        "scripts/agent_runtime/grok_hook_bridge.py": "grok",
        "scripts/hooks/apply_grok_hook_profile.py": "grok",
        "scripts/agent_runtime/profiles/acpx-grok-read-only.md": "grok",
        "scripts/agent_runtime/profiles/acpx-grok-sealed-review.md": "grok",
        "scripts/agent_runtime/codex_hook_entry.sh": "codex",
        "scripts/agent_runtime/codex_hook_policy.py": "codex",
        "scripts/agent_runtime/codex_hook_probe.py": "codex",
        "agents_extensions/codex/hooks.json": "codex",
        "agents_extensions/shared/hooks/guard-reviewer-publish.py": None,
        "scripts/agent_runtime/hermes_hooks/log_tool_call.sh": None,
    }
    for rel, seat in hooks.items():
        assert (repo / rel).is_file(), rel
        classified = classify_owned_path(rel)
        if seat is None:
            assert classified.kind == "ambiguous", rel
        else:
            assert classified == type(classified)("seat", frozenset({seat}), seat)

    for seats in adapter_subject_index().values():
        assert seats <= KNOWN_SUBJECT_SEATS


_AUTHOR_MODELS = {
    "openai": "gpt-6.1-sol",
    "anthropic": "claude-opus-5-5",
    "google": "gemini-3.8-flash-high",
    "xai": "grok-4.7",
    "moonshot": "composer-2.5",
    "zhipu": "glm-5.3",
    "poolside": "poolside/laguna-s-2.1",
    "deepseek": "deepseek-v4.1-flash",
    "qwen": "qwen/qwen3.6-plus",
}


@pytest.mark.parametrize("family,author", _AUTHOR_MODELS.items())
@pytest.mark.parametrize("risk", ["critical", "high", "medium", "low"])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_every_author_family_risk_profile_pick(family, author, risk, profile):
    if risk == "critical":
        expected = "gpt-6.1-sol" if family == "anthropic" else "claude-opus-5-5"
    elif risk == "high":
        expected = "gpt-6.1-sol" if family == "anthropic" or (family != "openai" and profile == "code") else "claude-opus-5-5"
    else:
        expected = "claude-sonnet-5-5" if family == "openai" else "gpt-6.1-sol"
    resolution = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, review_profile=profile))
    assert resolution.fail_closed_reason is None
    assert resolution.selected.concrete_model == expected
    assert resolution.selected.family != family


_AUTHORITY_DOWN = {
    "codex": "unhealthy",
    "claude": "unhealthy",
    "claude-opus-5-5-cursor-fallback": "unhealthy",
}


@pytest.mark.parametrize("author", ["gpt-6.1-sol", "claude-opus-5-5", "claude-sonnet-5-5", "grok-4.7", "kimi-code/k3"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("state,snapshot,fallback", [
    ("healthy", {"codex": "healthy", "claude": "healthy", "grok": "healthy", "cursor": "healthy"}, False),
    ("unknown", None, False),
    ("native-down-authorities-up", {"grok": "unhealthy"}, False),
    ("cursor-down-authorities-up", {"cursor": "unhealthy"}, False),
    ("authorities-down", {**_AUTHORITY_DOWN, "grok": "healthy", "cursor": "healthy"}, True),
    ("native-degraded", {**_AUTHORITY_DOWN, "grok": "degraded", "cursor": "healthy"}, True),
    ("native-near-cap", {**_AUTHORITY_DOWN, "grok": "near_cap", "cursor": "healthy"}, True),
    ("native-down", {**_AUTHORITY_DOWN, "grok": "unhealthy", "cursor": "healthy"}, True),
    ("all-down", {**_AUTHORITY_DOWN, "grok": "unhealthy", "cursor": "unhealthy"}, True),
])
def test_exact_review_seat_matrix(author, risk, profile, state, snapshot, fallback):
    """Whole-ladder choices preserve other models' suitability at every risk."""
    if fallback:
        if author == "grok-4.7" or state == "all-down":
            expected = None
        elif state in {"native-near-cap", "native-down"}:
            # Cursor's allowlist-union independence excludes Moonshot authors.
            expected = None if author == "kimi-code/k3" else "grok-4.7-cursor-fallback"
        else:
            expected = "grok-4.7"
    elif author in {"claude-opus-5-5", "claude-sonnet-5-5"}:
        expected = "openai_frontier"
    elif risk == "critical" or (risk == "high" and (author == "gpt-6.1-sol" or profile == "infra")):
        expected = "claude-opus-5-5"
    elif author == "gpt-6.1-sol":
        expected = "claude-sonnet-5-5"
    else:
        expected = "openai_frontier"
    result = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, review_profile=profile, routing_snapshot=snapshot))
    assert (result.selected.name if result.selected else None) == expected


def test_medium_anthropic_author_still_selects_sol_before_grok():
    assert resolve_reviewer(ResolverInputs(author_model="claude-opus-5-5", risk="medium")).selected.name == "openai_frontier"


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_native_grok_precedes_cursor_across_heads_pressure_and_subject_exclusions(risk, profile):
    # Deny the authority families as governed seats; cursor is deliberately
    # better on every resource term, and reversed rungs cannot change fallback.
    snapshot = {"agents": {
        "grok": {"status": "healthy", "scheduler": {"completed_input_bytes": 999999, "quota_remaining_pct": 1}},
        "cursor": {"status": "healthy", "scheduler": {"completed_input_bytes": 0, "quota_remaining_pct": 99}},
    }}
    for head in range(200):
        inputs = ResolverInputs(
            author_model="claude-sonnet-5-5", risk=risk, review_profile=profile,
            subject_families=frozenset({"openai", "anthropic"}),
            routing_snapshot=snapshot, exact_head=f"{head:040x}",
        )
        ladder = ((GROK_4_7_CURSOR_FALLBACK,), (GROK_4_7,))
        assert resolve_reviewer(inputs, ladder=ladder).selected.name == "grok-4.7"
        down = {"grok": "unhealthy", "cursor": "healthy"}
        assert resolve_reviewer(replace(inputs, routing_snapshot=down), ladder=ladder).selected.name == "grok-4.7-cursor-fallback"


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("primary", ["openai_frontier", "claude-opus-5-5"])
def test_last_resort_never_beats_eligible_sol_or_opus(profile, primary):
    fallback = replace(GROK_4_7_CURSOR_FALLBACK, last_resort=True)
    first = REVIEW_CANDIDATES[primary]
    inputs = ResolverInputs(author_model="gemini-3.8-flash-high", risk="medium", review_profile=profile)
    # Higher load and a reversed ladder must not put the last resort first.
    snapshot = {"agents": {first.route: {"status": "healthy", "scheduler": {"completed_input_bytes": 999999}}}}
    resolution = resolve_reviewer(inputs, ladder=((fallback,), (first,)), runtime_state=snapshot)
    assert resolution.selected.name == primary
    # Only the first model is unhealthy; the shared provider remains available.
    resolution = resolve_reviewer(
        replace(inputs, routing_snapshot={primary: "unhealthy"}), ladder=((first,), (fallback,))
    )
    assert resolution.selected.name == fallback.name
    assert "last resort" in resolution.substitution_note


@pytest.mark.parametrize("candidate", [GROK_4_7, GROK_4_7_CURSOR_FALLBACK])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_grok_critical_review_admitted_with_explicit_pin_and_custom_ladder(candidate, profile):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="critical", review_profile=profile, pinned_candidate=candidate.name, pressure_override_reason="admission probe")
    resolution = resolve_reviewer(inputs, ladder=((candidate,),))
    assert resolution.selected.name == candidate.name
    assert resolution.trace[0].status == "selected"


_SOL_OPUS_GROK = {"gpt-6.1-sol", "claude-opus-5-5", "grok-4.7"}
_HIGH_SEATS = {"openai_frontier", "claude-opus-5-5", "claude-opus-5-5-cursor-fallback", "grok-4.7", "grok-4.7-cursor-fallback"}
_SOL_UNAVAILABLE = {"codex": "unhealthy"}
# (author, Sol state, profile) -> expected concrete reviewer; None = no reviewer.
_HIGH_DENOMINATOR = {
    (author, sol, profile): (
        ("gpt-6.1-sol" if sol == "healthy" else "grok-4.7")
        if author in {"claude-opus-5-5", "claude-sonnet-5-5"}
        else (
            "gpt-6.1-sol"
            if author in {"grok-4.7", "composer-2.5"} and sol == "healthy" and profile == "code"
            else "claude-opus-5-5"
        )
    )
    for author in ("claude-opus-5-5", "claude-sonnet-5-5", "gpt-6.1-sol", "gpt-6-luna", "grok-4.7", "composer-2.5")
    for sol in ("healthy", "unavailable")
    for profile in ("code", "infra")
}


@pytest.mark.parametrize("key", sorted(_HIGH_DENOMINATOR))
def test_high_risk_resolves_to_sol_opus_or_grok(key):
    """#9769: the denominator admits Sol, Opus and both Grok transports."""
    author, sol, profile = key
    snapshot = _SOL_UNAVAILABLE if sol == "unavailable" else None
    resolution = resolve_reviewer(
        ResolverInputs(author_model=author, risk="high", review_profile=profile, routing_snapshot=snapshot)
    )
    expected = _HIGH_DENOMINATOR[key]
    assert {entry.name for entry in resolution.trace} <= _HIGH_SEATS
    if expected is None:
        assert resolution.selected is None
        assert resolution.fail_closed_reason is None
        # The reason is stated per seat: Sol is down, both Opus transports share the author's family.
        reasons = {entry.name: entry.reason for entry in resolution.trace}
        assert reasons["openai_frontier"] == "lane health is unhealthy — route is operationally unavailable"
        for name in ("claude-opus-5-5", "claude-opus-5-5-cursor-fallback"):
            assert "same family as author" in reasons[name]
        return
    assert resolution.selected is not None
    assert resolution.selected.concrete_model == expected
    assert resolution.selected.concrete_model in _SOL_OPUS_GROK
    assert resolution.selected.transport in {"native_codex", "native_claude", "native_grok", "cursor"}


def test_high_risk_with_opus_unavailable_never_falls_back_to_sonnet():
    snapshot = {"claude": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"}
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="high", routing_snapshot=snapshot))
    assert resolution.selected is None
    assert {entry.name for entry in resolution.trace} == _HIGH_SEATS


_HIGH_RISK_RULE = "a formal review at high risk is performed only by gpt-6.1-sol, claude-opus-5-5"


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("name", ["claude-sonnet-5-5"])
def test_high_risk_pin_and_custom_ladder_refuse_seats_outside_sol_and_opus(profile, name):
    """#9538: the rule is an eligibility gate, so neither a pin nor a caller ladder bypasses it."""
    author = "claude-opus-5-5" if name.startswith("grok") else "gpt-6.1-sol"
    inputs = ResolverInputs(author_model=author, review_profile=profile, domain=profile, risk="high")
    pinned = resolve_reviewer(replace(inputs, pinned_candidate=name, pressure_override_reason="pressure probe"))
    assert pinned.selected is None
    assert pinned.fail_closed_reason == f"explicit reviewer pin {name!r} failed a hard eligibility gate"
    assert {entry.name: entry.reason for entry in pinned.trace}[name].startswith(_HIGH_RISK_RULE)
    custom = resolve_reviewer(inputs, ladder=((REVIEW_CANDIDATES[name],),))
    assert custom.selected is None
    assert custom.trace[0].status == "excluded" and custom.trace[0].reason.startswith(_HIGH_RISK_RULE)
    medium = evaluate_candidate(REVIEW_CANDIDATES[name], replace(inputs, risk="medium"))
    assert medium.reason is None or not medium.reason.startswith(_HIGH_RISK_RULE)


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_high_risk_opus_pin_is_still_admitted(profile):
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol",
        review_profile=profile,
        domain=profile,
        risk="high",
        pinned_candidate="claude-opus-5-5",
        pressure_override_reason="pressure probe",
    )
    assert resolve_reviewer(inputs).selected.name == "claude-opus-5-5"


def test_advisory_resolution_is_outside_the_formal_high_risk_rule():
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="high", formal_review=False)
    assert not (evaluate_candidate(SONNET_5_5, inputs).reason or "").startswith(_HIGH_RISK_RULE)


@pytest.mark.parametrize("risk", ["low", "medium", "high"])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_security_diff_has_critical_floor_before_ladder_selection(risk, profile):
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol",
        risk=risk,
        review_profile=profile,
        changed_paths=("scripts/delegate.py",),
        owned_paths=("site/src/app.ts",),
    )
    result = resolve_reviewer(inputs)
    assert result.resolved_risk == "critical"
    assert result.selected.concrete_model == "claude-opus-5-5"
    assert "critical_review" in REVIEW_CANDIDATES[result.selected.name].model_roles
    assert {entry.name for entry in result.trace} == {
        candidate.name for rung in REVIEW_LADDERS["critical"] for candidate in rung
    }
    assert inputs.risk == risk  # Caller input is immutable.


@pytest.mark.parametrize("risk", ["low", "medium", "high"])
@pytest.mark.parametrize("candidate", [SONNET_5_5])
def test_security_floor_cannot_be_bypassed_by_pin_custom_ladder_or_direct_evaluation(risk, candidate):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk, changed_paths=("scripts/delegate.py",))
    direct = evaluate_candidate(candidate, inputs)
    assert direct.status == "excluded" and direct.reason
    custom = resolve_reviewer(inputs, ladder=((candidate,),))
    assert custom.resolved_risk == "critical"
    assert custom.selected is None and custom.fail_closed_reason
    assert custom.trace[0].reason
    pinned = resolve_reviewer(replace(inputs, pinned_candidate=candidate.name, pressure_override_reason="bypass probe"))
    assert pinned.resolved_risk == "critical"
    assert pinned.selected is None and pinned.fail_closed_reason


def test_security_owned_paths_only_add_coverage():
    inputs = ResolverInputs(
        author_model="gpt-6.1-sol", risk="low", changed_paths=("site/src/app.ts",), owned_paths=("scripts/delegate.py",)
    )
    assert resolve_reviewer(inputs).resolved_risk == "critical"


def test_security_qualified_reviewer_unavailable_refuses_without_downgrade():
    result = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk="low",
            changed_paths=("scripts/delegate.py",),
            routing_snapshot={"claude": "unhealthy", "grok": "unhealthy", "cursor": "unhealthy"},
        )
    )
    assert result.resolved_risk == "critical"
    assert result.selected is None and result.fail_closed_reason
    assert all(entry.reason for entry in result.trace)


def test_security_subject_seat_exclusion_still_binds():
    result = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol",
            risk="low",
            changed_paths=("scripts/delegate.py",),
            subject_seats=frozenset({"claude"}),
        )
    )
    assert result.resolved_risk == "critical"
    assert result.selected.concrete_model == "grok-4.7"
    assert all(entry.status == "excluded" for entry in result.trace if entry.family == "anthropic")


def test_security_infra_requires_critical_review_role_even_on_custom_candidate():
    candidate = replace(OPENAI_FRONTIER, model_roles=frozenset({"security_review"}))
    inputs = ResolverInputs(
        author_model="claude-opus-5-5", risk="low", review_profile="infra", changed_paths=("scripts/delegate.py",)
    )
    result = evaluate_candidate(candidate, inputs)
    assert result.status == "excluded" and "critical_review" in result.reason


@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_ordinary_paths_preserve_resolution(risk):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk=risk)
    assert resolve_reviewer(inputs) == resolve_reviewer(replace(inputs, changed_paths=("site/src/app.ts",)))


# --- #9517: near-cap lanes with a published credit balance -------------------

# Captured at import, before the conftest autouse fixture stubs the reader.
_REAL_RATE_LIMIT_READER = credit_lane.read_recent_rate_limits


# The probe reading a published credit leaf rests on; relief is re-checked against it (#9740 F6).
_FRESH_PROBE = {"freshness": "fresh", "age_s": 60.0}


def _credit_codex(credit: dict | None, *, diagnostics: dict | None = None, **overrides) -> dict:
    """A near-cap, healthy Codex routing-budget record with a fresh probe, publishing ``credit``.

    The record carries the inputs the producer computed ``credit`` from (remaining
    allowance, raw balance and its fetch time): relief is re-decided from them (#9740).
    """
    evidence = credit.get("evidence") if isinstance(credit, dict) else None
    fetched = (evidence or {}).get("credit_fetched_at") or (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    record = {
        "status": "near_cap",
        "health": {"healthy": True},
        "remaining_pct": 1.0,
        "credit_balance": 62500.0,
        "fetched_at": fetched,
        **_FRESH_PROBE,
        **overrides,
    }
    if credit is not None:
        record["credit"] = credit
    snapshot: dict = {"agents": {"codex": record}}
    if diagnostics is not None:
        snapshot["diagnostics"] = diagnostics
    return snapshot


def _published_credit(*, fetched_at: datetime | None = None) -> dict:
    """The credit field routing-budget publishes, computed by credit_lane itself (conftest: no rate limits)."""
    now = datetime.now(UTC)
    fetched = (fetched_at or now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    info = {
        "remaining_pct": 1.0,
        "freshness": "fresh",
        "age_s": 60.0,
        "credit_balance": 62500.0,
        "codexbar": {"weekly_remaining_pct": 1.0, "freshness": "fresh", "age_s": 60.0, "fetched_at": fetched},
    }
    return credit_lane.lane_credit_state("codex", info, credit_lane.load_policy(), now=now)


def test_near_cap_codex_with_credit_balance_keeps_allowlisted_reviewer_eligible():
    credit = _published_credit()
    assert credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(credit))
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "eligible", result.reason
    assert result.health == "near_cap"
    assert result.credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT
    assert result.credit["model_allowed"] is True
    assert result.credit["draw"] == credit_lane.DRAW_NOT_VERIFIED
    assert result.credit["evidence"]["credit_balance"] == 62500.0

    resolution = resolve_reviewer(inputs)
    traced = next(item for item in resolution.trace if item.name == "openai_frontier")
    assert traced.status in {"eligible", "selected"}
    assert traced.credit["allowed_models"] == ["gpt-6.1-sol", "gpt-6-luna"]


@pytest.mark.parametrize(
    "credit",
    [
        None,
        {"state": credit_lane.CREDIT_USE_UNCONFIRMED, "reason": "recent rate limit"},
        {"state": credit_lane.CREDITS_UNVERIFIED, "reason": "credit probe freshness=stale"},
        {"state": credit_lane.CREDITS_EXHAUSTED, "reason": "credit balance 0"},
        {"state": credit_lane.POLICY_ERROR, "reason": "credit-lane policy unreadable"},
        {"state": credit_lane.PLAN_UNKNOWN, "reason": "plan allowance unknown"},
        {"state": credit_lane.NOT_CONFIGURED},
    ],
    ids=[
        "no-credit-field",
        "use-unconfirmed",
        "unverified",
        "exhausted",
        "policy-error",
        "plan-unknown",
        "not-configured",
    ],
)
def test_near_cap_without_usable_credits_stays_excluded(credit):
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(credit))
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded"
    assert result.reason == "quota bucket is near cap — automatic assignments are prohibited"
    assert result.credit is None


def test_flat_near_cap_map_carries_no_credit_and_stays_excluded():
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot={"codex": "near_cap"})
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded" and result.credit is None


def test_stale_published_credit_balance_stays_excluded():
    stale = _published_credit(fetched_at=datetime.now(UTC) - timedelta(minutes=1))
    stale["evidence"]["credit_fetched_at"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(stale))
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded"
    assert "near cap" in result.reason and credit_lane.CREDITS_UNVERIFIED in result.reason
    assert result.credit["state"] == credit_lane.CREDITS_UNVERIFIED


@pytest.mark.parametrize(
    ("record", "diagnostics", "why"),
    [
        ({"freshness": "stale_last_good"}, None, "credit probe freshness=stale_last_good"),
        ({"stale": True}, None, "credit probe freshness=fresh"),
        ({"freshness": None, "age_s": None}, None, "credit probe freshness=missing"),
        ({}, {"stale": True}, "routing-budget snapshot is stale"),
    ],
    ids=["stale-probe", "stale-flag", "missing-freshness", "stale-snapshot"],
)
def test_published_credit_relief_is_rechecked_against_the_full_record(record, diagnostics, why):
    """#9740 F6: a published ``credit_balance_present`` leaf never outlives contradictory probe evidence."""
    snapshot = _credit_codex(_published_credit(), diagnostics=diagnostics, **record)
    result = evaluate_candidate(
        OPENAI_FRONTIER, ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=snapshot)
    )
    assert result.status == "excluded"
    assert result.credit["state"] == credit_lane.CREDITS_UNVERIFIED
    assert result.credit["reason"] == f"published credit relief not re-verified: {why}"


def test_credit_balance_never_relaxes_hard_health_exclusion():
    snapshot = _credit_codex(_published_credit(), health={"healthy": False})
    result = evaluate_candidate(
        OPENAI_FRONTIER, ResolverInputs(author_model="claude-opus-5-5", routing_snapshot=snapshot)
    )
    assert result.status == "excluded"
    assert result.reason == "lane health is unhealthy — route is operationally unavailable"


def test_off_allowlist_model_on_credit_lane_is_excluded_naming_the_allowlist(monkeypatch):
    policy = credit_lane.load_policy()
    monkeypatch.setattr(
        credit_lane, "load_policy", lambda path=None: replace(policy, allowed_models={"codex": ("gpt-6-luna",)})
    )
    inputs = ResolverInputs(
        author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(_published_credit())
    )
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded"
    assert "outside the credit-period allowlist [gpt-6-luna]" in result.reason
    assert result.credit["model_allowed"] is False


def test_credit_backed_seat_ranks_after_equal_plan_backed_seat(practical_astra):
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5-5"]
    inputs = ResolverInputs(author_model="gemini", exact_head="d" * 40, requested_role="implementation")
    ladder = ((PRACTICAL_ASTRA, sonnet),)
    # Without credit evidence the lighter-loaded Codex seat wins the balance.
    light_codex = {"completed_input_bytes": 0, "active_reserved_input_bytes": 0}
    busy_claude = {"completed_input_bytes": 900, "active_reserved_input_bytes": 0}
    plain = {"agents": {"codex": {"scheduler": light_codex}, "claude": {"scheduler": busy_claude}}}
    assert resolve_reviewer(inputs, ladder=ladder, runtime_state=plain).selected.name == "synthetic-practical-astra"

    credit_backed = {
        "agents": {
            "codex": {**_credit_codex(_published_credit())["agents"]["codex"], "scheduler": light_codex},
            "claude": {"status": "healthy", "scheduler": busy_claude},
        }
    }
    resolution = resolve_reviewer(inputs, ladder=ladder, runtime_state=credit_backed)
    assert resolution.selected.name == "claude-sonnet-5-5"
    assert next(item for item in resolution.trace if item.name == "synthetic-practical-astra").status == "eligible"

    # With the plan-backed seat near cap too, the credit-backed seat is selected and the receipt says so.
    only_credit = {
        "agents": {
            "codex": _credit_codex(_published_credit())["agents"]["codex"],
            "claude": {"status": "near_cap"},
        }
    }
    resolution = resolve_reviewer(inputs, ladder=ladder, runtime_state=only_credit)
    assert resolution.selected.name == "synthetic-practical-astra"
    assert resolution.selected.credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT
    assert credit_lane.DRAW_NOT_VERIFIED in resolution.substitution_note


def _shared_rate_limit(monkeypatch, tmp_path, *, at: datetime) -> None:
    """One codex ``rate_limited`` record at ``at`` in a simulated shared runtime log, read by the real reader."""
    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", _REAL_RATE_LIMIT_READER)
    stamp = at.astimezone(UTC)
    (tmp_path / f"usage_codex-delegate_{stamp:%Y-%m-%d}.jsonl").write_text(
        json.dumps({"ts": stamp.isoformat().replace("+00:00", "Z"), "outcome": "rate_limited"}) + "\n",
        encoding="utf-8",
    )


def test_published_credit_snapshot_is_not_reused_after_a_new_rate_limit(monkeypatch, tmp_path):
    credit = _published_credit()  # published while the lane had no rate limit
    assert credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT
    _shared_rate_limit(monkeypatch, tmp_path, at=datetime.now(UTC) - timedelta(minutes=10))
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(credit))
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded"
    assert credit_lane.CREDIT_USE_UNCONFIRMED in result.reason
    assert result.credit["state"] == credit_lane.CREDIT_USE_UNCONFIRMED
    assert result.credit["evidence"]["rate_limited_count"] == 1


def test_unreadable_rate_limit_evidence_denies_credit_relief(monkeypatch):
    def broken(*_args, **_kwargs):
        raise OSError("usage dir unreadable")

    credit = _published_credit()
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", broken)
    inputs = ResolverInputs(author_model="claude-opus-5-5", risk="high", routing_snapshot=_credit_codex(credit))
    result = evaluate_candidate(OPENAI_FRONTIER, inputs)
    assert result.status == "excluded"
    assert result.credit["state"] == credit_lane.CREDITS_UNVERIFIED


# --- #9739: complete branch authorship ------------------------------------------------------------


def _complete(families, *, risk="medium", author_model="", author_family=None, paths=("docs/a.md",)):
    from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

    return resolve_reviewer(
        ResolverInputs(
            author_model=author_model,
            author_family=author_family,
            author_families=frozenset(families),
            risk=risk,
            changed_paths=paths,
            owned_paths=paths,
        )
    )


def test_complete_author_set_excludes_every_member_not_only_the_latest():
    from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

    latest_only = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="medium", changed_paths=("docs/a.md",))
    )
    complete = _complete({"anthropic", "openai"}, author_model="gpt-6.1-sol")

    assert latest_only.selected.family == "anthropic"
    assert complete.selected.name == "grok-4.7"
    reasons = {entry.name: entry.reason for entry in complete.trace}
    assert "same family as author (anthropic)" in reasons["claude-opus-5-5"]
    # Grok reviews at every risk (#9769); an xAI member removes it too.
    assert _complete({"anthropic", "openai", "xai"}, risk="critical").selected is None


def test_single_author_fields_add_to_the_complete_set_and_never_shrink_it():
    # The single field names a family outside the set; both stay excluded.
    resolution = _complete({"anthropic", "xai"}, author_model="gpt-6.1-sol", risk="critical")
    assert resolution.selected is None and resolution.fail_closed_reason is None
    # An explicit override cannot replace the set either.
    overridden = _complete(
        {"openai", "xai"}, author_model="claude-opus-5-5", author_family="anthropic", risk="critical"
    )
    assert overridden.selected is None


@pytest.mark.parametrize(
    "families,author_model",
    [({"anthropic", "ambiguous"}, ""), ({"anthropic"}, "cursor")],
)
def test_complete_set_with_an_unresolved_member_fails_closed(families, author_model):
    from scripts.review.reviewer_resolver import ResolverInputs, evaluate_candidate

    resolution = _complete(families, author_model=author_model)
    assert resolution.selected is None and "holds an unresolved family" in resolution.fail_closed_reason
    inputs = ResolverInputs(author_model=author_model, author_families=frozenset(families), risk="medium")
    assert evaluate_candidate(OPENAI_FRONTIER, inputs).status == "excluded"


def test_cursor_auto_member_keeps_the_union_and_transport_restrictions():
    resolution = _complete({"openai", "cursor-auto-union"})
    reasons = {entry.name: entry.reason for entry in resolution.trace}
    assert "within author union family" in reasons["grok-4.7-cursor-fallback"]
    assert resolution.selected.family == "anthropic"


@pytest.mark.parametrize("candidate", [SONNET_5_5, OPENAI_FRONTIER, GROK_4_7, GROK_4_7_CURSOR_FALLBACK])
@pytest.mark.parametrize("author_model", ["", "cursor:auto"])
def test_unknown_committed_author_accepts_any_qualified_known_family(candidate, author_model):
    inputs = ResolverInputs(author_model=author_model, author_families=frozenset({"unknown"}), risk="medium")
    assert evaluate_candidate(candidate, inputs).status == "eligible"
    selected = resolve_reviewer(inputs, ladder=((candidate,),)).selected
    assert (selected.name, selected.family, selected.concrete_model) == (
        candidate.name, candidate.family, candidate.concrete_model
    )


def test_unknown_committed_author_does_not_hide_known_author_exclusions():
    resolution = _complete({"unknown", "anthropic"})
    assert resolution.selected.family != "anthropic"
    assert evaluate_candidate(
        SONNET_5_5, ResolverInputs(author_model="", author_families=frozenset({"unknown", "anthropic"}))
    ).status == "excluded"


def test_unknown_committed_author_does_not_hide_incoming_cursor_auto_union():
    inputs = ResolverInputs(
        author_model="cursor:auto", author_families=frozenset({"unknown", "cursor-auto-union"})
    )
    assert evaluate_candidate(GROK_4_7, inputs).status == "excluded"
    selected = resolve_reviewer(inputs).selected
    assert selected is not None and selected.family in {"anthropic", "openai"}


@pytest.mark.parametrize("authors", [{"unknown"}, {"anthropic"}])
def test_unknown_reviewer_family_is_always_refused(authors):
    candidate = replace(OPENAI_FRONTIER, family="unknown")
    inputs = ResolverInputs(author_model="", author_families=frozenset(authors))
    result = evaluate_candidate(candidate, inputs)
    assert result.status == "excluded" and "reviewer family unknown" in result.reason
    assert resolve_reviewer(inputs, ladder=((candidate,),)).selected is None


def test_empty_complete_set_keeps_single_author_selection_identical():
    from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

    single = ResolverInputs(author_model="claude-opus-5-5", risk="high", changed_paths=("docs/a.md",))
    assert resolve_reviewer(single) == resolve_reviewer(replace(single, author_families=frozenset()))
