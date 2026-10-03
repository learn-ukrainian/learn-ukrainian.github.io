"""Tests for the quality-first cross-family reviewer resolver."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
DEEPSEEK_V4_PRO = replace(SONNET_5_5, name="deepseek-v4-pro", concrete_model="deepseek-v4-pro", family="deepseek", route="deepseek")
DEEPSEEK_V4_1_FLASH = replace(DEEPSEEK_V4_PRO, name="deepseek-v4.1-flash", concrete_model="deepseek-v4.1-flash")


@pytest.fixture
def practical_astra(monkeypatch):
    monkeypatch.setitem(REVIEW_CANDIDATES, PRACTICAL_ASTRA.name, PRACTICAL_ASTRA)
    return PRACTICAL_ASTRA


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
    for cand_name in ("composer-2.5", "grok-4.7-cursor-fallback", "claude-fable-5-1-cursor-fallback"):
        cand = REVIEW_CANDIDATES[cand_name]
        res = evaluate_candidate(cand, kimi_inputs)
        assert res.status == "excluded", (cand_name, res.status)

    # xAI-family author: Cursor-transport candidates must be excluded
    grok_inputs = ResolverInputs(author_model="grok-4.6")
    for cand_name in ("composer-2.5", "grok-4.7-cursor-fallback", "claude-fable-5-1-cursor-fallback"):
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


@pytest.mark.parametrize("model", ["claude-fable-5", "cursor:CLAUDE-FABLE-5-thinking-high", "grok-4.6", "grok-4.6-high", "grok-4.6[context=500k]"])
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
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", pinned_candidate=model,
                       pressure_override_reason="test explicit pin")
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


def test_fable_uses_cursor_only_when_native_claude_is_unhealthy():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            risk="critical",
            routing_snapshot={"claude": "unhealthy", "cursor": "healthy"},
        )
    )

    assert resolution.selected is None
    fallback = next(entry for entry in resolution.trace if entry.name == "claude-fable-5-1-cursor-fallback")
    assert fallback.status == "excluded"
    # The Cursor endpoint is formal only for the models it pins (#9488); Fable is not one.
    assert fallback.reason == "sealed endpoint 'cursor' is not pinned for model 'claude-fable-5-1'"
    native = next(entry for entry in resolution.trace if entry.name == "claude-fable-5-1")
    assert native.status == "excluded"
    assert "unhealthy" in native.reason


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
    composer = next(entry for entry in resolution.trace if entry.name == "composer-2.5")
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
    assert resolution.selected is None


def test_native_grok_never_judges_and_cursor_grok_needs_a_healthy_cursor_lane():
    """#9488 replaced "Grok never judges" with "native Grok never judges".

    Native Grok stays excluded whatever its health; the attested Cursor seat is
    selectable only while the Cursor lane itself is not unhealthy.
    """
    snapshot = {
        "grok": "unhealthy",
        "cursor": "healthy",
        "claude": "unhealthy",
        "codex": "unhealthy",
        "agy": "unhealthy",
        "kimi": "unhealthy",
    }
    injected = resolve_reviewer(
        ResolverInputs(author_model="claude", risk="medium", routing_snapshot=snapshot),
        ladder=((GROK_4_7, GROK_4_7_CURSOR_FALLBACK),),
    )
    native = next(item for item in injected.trace if item.name == "grok-4.7")
    assert native.status == "excluded" and "native Grok never judges" in native.reason
    assert injected.selected is not None and injected.selected.name == "grok-4.7-cursor-fallback"
    dark = resolve_reviewer(
        ResolverInputs(author_model="claude", risk="medium", routing_snapshot={**snapshot, "cursor": "unhealthy"})
    )
    assert dark.selected is None
    cursor = next(item for item in dark.trace if item.name == "grok-4.7-cursor-fallback")
    assert cursor.reason == "lane health is unhealthy — route is operationally unavailable"


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
        ResolverInputs(
            author_model="claude", required_capabilities=frozenset({"vesum_mcp"}), formal_review=False
        ),
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
            ResolverInputs(author_model="claude", risk="high", exact_head=f"{index:040x}"),
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
    fable = REVIEW_CANDIDATES["claude-fable-5-1"]
    selected = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            author_family="openai",
            risk="medium",
            pinned_candidate=fable.name,
            pressure_override_reason="operator requested Fable dissent",
        )
    )
    assert selected.selected is not None
    assert selected.selected.name == "claude-fable-5-1"
    assert "explicit pressure override" in selected.substitution_note

    same_family = resolve_reviewer(
        ResolverInputs(
            author_model="claude-sonnet-5-5",
            author_family="anthropic",
            risk="medium",
            pinned_candidate=fable.name,
            pressure_override_reason="operator requested Fable dissent",
        )
    )
    assert same_family.selected is None
    assert "hard eligibility" in same_family.fail_closed_reason
    assert next(item for item in same_family.trace if item.name == fable.name).status == "excluded"


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


def test_critical_ladder_keeps_authority_before_practical():
    critical = REVIEW_LADDERS["critical"]
    # #9394: Opus/Sol precede practical seats; Fable follows all primary seats.
    assert [rung[0].name for rung in critical[:4]] == [
        "openai_frontier",
        "claude-opus-5-5",
        "claude-opus-5-5-cursor-fallback",
        "composer-2.5",
    ]


def test_high_ladder_holds_only_sol_and_opus_seats():
    ladder = REVIEW_LADDERS["high"]
    assert [[c.name for c in rung] for rung in ladder] == [
        ["openai_frontier"],
        ["claude-opus-5-5"],
        ["claude-opus-5-5-cursor-fallback"],
    ]
    assert {c.concrete_model for rung in ladder for c in rung} == {"gpt-6.1-sol", "claude-opus-5-5"}


def test_practical_ladder_starts_with_sol_then_opus_fallbacks():
    for risk in ("medium", "low"):
        ladder = REVIEW_LADDERS[risk]
        assert [rung[0].name for rung in ladder[:5]] == [
            "openai_frontier",
            "claude-opus-5-5",
            "claude-opus-5-5-cursor-fallback",
            "claude-sonnet-5-5",
            "composer-2.5",
        ]
        assert "glm-5.3" not in {c.name for rung in ladder for c in rung}
        assert ladder[5][0].name == "pool"


def test_medium_codex_author_falls_through_unavailable_opus_to_sonnet_5_5():
    ladder = REVIEW_LADDERS["medium"]
    assert [rung[0].name for rung in ladder[:4]] == [
        "openai_frontier",
        "claude-opus-5-5",
        "claude-opus-5-5-cursor-fallback",
        "claude-sonnet-5-5",
    ]
    # For an OpenAI author Sol is same-family; an unavailable Opus rung
    # must leave the practical Sonnet rung in the same position.
    without_opus = tuple(rung for rung in ladder if not rung[0].name.startswith("claude-opus-5-5"))
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="medium"), ladder=without_opus)
    assert resolution.selected is not None
    assert resolution.selected.name == "claude-sonnet-5-5"


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
    # #9488: native Grok still never judges; the attested Cursor seat is the
    # last resort once every Anthropic primary is unavailable.
    assert without.selected is not None and without.selected.name == "grok-4.7-cursor-fallback"
    assert "native Grok never judges" in _grok_trace(without)["grok-4.7"].reason

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
    with_readme = resolve_reviewer(
        ResolverInputs(author_model="claude", risk="high", owned_paths=("README.md",))
    )
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
            owned_paths=("scripts/agent_runtime/adapters/kimi.py", "scripts/agent_runtime/adapters/kimicc.py"),
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
    "openai": "gpt-6.1-sol", "anthropic": "claude-opus-5-5",
    "google": "gemini-3.8-flash-high", "xai": "grok-4.7",
    "moonshot": "composer-2.5", "zhipu": "glm-5.3",
    "poolside": "poolside/laguna-s-2.1", "deepseek": "deepseek-v4.1-flash",
    "qwen": "qwen/qwen3.6-plus",
}


@pytest.mark.parametrize("family,author", _AUTHOR_MODELS.items())
@pytest.mark.parametrize("risk", ["critical", "high", "medium", "low"])
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_every_author_family_risk_profile_pick(family, author, risk, profile):
    if risk == "critical":
        expected = "gpt-6.1-sol" if family == "anthropic" else "claude-opus-5-5"
    elif risk == "high":
        # #9538: high holds only Sol and Opus; infra suitability puts Opus first
        # for every author family Sol is not barred from.
        expected = "gpt-6.1-sol" if family == "anthropic" or (profile == "code" and family != "openai") else "claude-opus-5-5"
    else:
        expected = "gpt-6.1-sol" if family == "anthropic" or family != "openai" else "claude-sonnet-5-5"
    resolution = resolve_reviewer(ResolverInputs(author_model=author, risk=risk, review_profile=profile))
    assert resolution.fail_closed_reason is None
    assert resolution.selected.concrete_model == expected
    assert resolution.selected.family != family


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("primary", ["openai_frontier", "claude-opus-5-5"])
def test_fable_last_resort_never_beats_eligible_sol_or_opus(profile, primary):
    fallback = REVIEW_CANDIDATES["claude-fable-5-1"]
    first = REVIEW_CANDIDATES[primary]
    inputs = ResolverInputs(author_model="gemini-3.8-flash-high", risk="critical", review_profile=profile)
    # Higher load and a reversed ladder must not put the last resort first.
    snapshot = {"agents": {first.route: {"status": "healthy", "scheduler": {"completed_input_bytes": 999999}}}}
    resolution = resolve_reviewer(inputs, ladder=((fallback,), (first,)), runtime_state=snapshot)
    assert resolution.selected.name == primary
    # Only the first model is unhealthy; the shared provider remains available.
    resolution = resolve_reviewer(replace(inputs, routing_snapshot={primary: "unhealthy"}),
                                  ladder=((first,), (fallback,)))
    assert resolution.selected.name == "claude-fable-5-1"
    assert "last resort" in resolution.substitution_note


@pytest.mark.parametrize(
    "candidate,reason",
    [
        (GROK_4_7, "native Grok never judges"),
        # #9488: the Cursor seat has no critical_review role in the catalogue.
        (GROK_4_7_CURSOR_FALLBACK, "missing required review role suitability"),
    ],
)
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_grok_critical_review_forbidden_even_with_explicit_pin_and_custom_ladder(candidate, reason, profile):
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="critical", review_profile=profile,
                            formal_review=False, pinned_candidate=candidate.name,
                            pressure_override_reason="adversarial test")
    resolution = resolve_reviewer(inputs, ladder=((candidate,),))
    assert resolution.selected is None
    assert "hard eligibility gate" in resolution.fail_closed_reason
    assert reason in resolution.trace[0].reason


_SOL_OPUS = {"gpt-6.1-sol", "claude-opus-5-5"}
_HIGH_SEATS = {"openai_frontier", "claude-opus-5-5", "claude-opus-5-5-cursor-fallback"}
_SOL_UNAVAILABLE = {"codex": "unhealthy"}
# (author, Sol state, profile) -> expected concrete reviewer; None = no reviewer.
_HIGH_DENOMINATOR = {
    ("claude-opus-5-5", "healthy", "code"): "gpt-6.1-sol",
    ("claude-opus-5-5", "healthy", "infra"): "gpt-6.1-sol",
    ("claude-opus-5-5", "unavailable", "code"): None,
    ("claude-opus-5-5", "unavailable", "infra"): None,
    ("claude-sonnet-5-5", "healthy", "code"): "gpt-6.1-sol",
    ("claude-sonnet-5-5", "healthy", "infra"): "gpt-6.1-sol",
    ("claude-sonnet-5-5", "unavailable", "code"): None,
    ("claude-sonnet-5-5", "unavailable", "infra"): None,
    ("gpt-6.1-sol", "healthy", "code"): "claude-opus-5-5",
    ("gpt-6.1-sol", "healthy", "infra"): "claude-opus-5-5",
    ("gpt-6.1-sol", "unavailable", "code"): "claude-opus-5-5",
    ("gpt-6.1-sol", "unavailable", "infra"): "claude-opus-5-5",
    ("gpt-6-luna", "healthy", "code"): "claude-opus-5-5",
    ("gpt-6-luna", "healthy", "infra"): "claude-opus-5-5",
    ("gpt-6-luna", "unavailable", "code"): "claude-opus-5-5",
    ("gpt-6-luna", "unavailable", "infra"): "claude-opus-5-5",
    ("grok-4.7", "healthy", "code"): "gpt-6.1-sol",
    ("grok-4.7", "healthy", "infra"): "claude-opus-5-5",
    ("grok-4.7", "unavailable", "code"): "claude-opus-5-5",
    ("grok-4.7", "unavailable", "infra"): "claude-opus-5-5",
    ("composer-2.5", "healthy", "code"): "gpt-6.1-sol",
    ("composer-2.5", "healthy", "infra"): "claude-opus-5-5",
    ("composer-2.5", "unavailable", "code"): "claude-opus-5-5",
    ("composer-2.5", "unavailable", "infra"): "claude-opus-5-5",
}


@pytest.mark.parametrize("key", sorted(_HIGH_DENOMINATOR))
def test_high_risk_resolves_only_to_sol_or_opus_or_to_no_reviewer(key):
    """#9538: the denominator never reaches Sonnet, Composer, Pool or Cursor Grok."""
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
    assert resolution.selected.concrete_model in _SOL_OPUS
    assert resolution.selected.transport in {"native_codex", "native_claude", "cursor"}


def test_high_risk_with_opus_unavailable_never_falls_back_to_sonnet():
    snapshot = {"claude": "unhealthy", "cursor": "unhealthy"}
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="high", routing_snapshot=snapshot))
    assert resolution.selected is None
    assert {entry.name for entry in resolution.trace} == _HIGH_SEATS


_HIGH_RISK_RULE = "a formal review at high risk is performed only by gpt-6.1-sol, claude-opus-5-5"


@pytest.mark.parametrize("profile", ["code", "infra"])
@pytest.mark.parametrize("name", ["claude-sonnet-5-5", "claude-fable-5-1", "grok-4.7-cursor-fallback"])
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
        author_model="gpt-6.1-sol", review_profile=profile, domain=profile, risk="high",
        pinned_candidate="claude-opus-5-5", pressure_override_reason="pressure probe",
    )
    assert resolve_reviewer(inputs).selected.name == "claude-opus-5-5"


def test_advisory_resolution_is_outside_the_formal_high_risk_rule():
    inputs = ResolverInputs(author_model="gpt-6.1-sol", risk="high", formal_review=False)
    assert not (evaluate_candidate(SONNET_5_5, inputs).reason or "").startswith(_HIGH_RISK_RULE)


# --- #9577: recorded exception when independence alone exhausts the high ladder ---

from scripts.review.reviewer_resolver import (
    SUBJECT_SEAT_EXCEPTION,
    SUBJECT_SEAT_EXCEPTION_CANDIDATE,
    ReviewChange,
    review_exception_decision,
    review_exception_receipt,
    verify_review_exception_receipt,
)
from scripts.review.subject_seat import (
    change_supported_seats,
    classify_exact_changed_path,
    classify_owned_path,
    exact_change_path_problem,
)

_EXCEPTION_ID = "subject-seat-exhausted-kimi-k3-cursor"
_AUTHORS = {"openai": "gpt-6.1-sol", "anthropic": "claude-opus-5-5", "moonshot": "composer-2.5"}
_SUBJECTS = {"none": (), "codex": ("codex",), "claude": ("claude",), "both": ("codex", "claude")}
# The changed file that makes each seat a subject of the change.
_SEAT_PATHS = {"codex": "scripts/agent_runtime/adapters/codex.py", "claude": "scripts/agent_runtime/adapters/claude.py"}
_UNRELATED = "scripts/ci/x.py"
# The issue's denominator at high risk: author family x subject seats.
_HIGH_MATRIX = {
    ("openai", "none"): "claude-opus-5-5",
    ("openai", "codex"): "claude-opus-5-5",
    ("openai", "claude"): _EXCEPTION_ID,
    ("openai", "both"): _EXCEPTION_ID,
    ("anthropic", "none"): "openai_frontier",
    ("anthropic", "codex"): _EXCEPTION_ID,
    ("anthropic", "claude"): "openai_frontier",
    ("anthropic", "both"): _EXCEPTION_ID,
    ("moonshot", "none"): "openai_frontier",
    ("moonshot", "codex"): "claude-opus-5-5",
    ("moonshot", "claude"): "openai_frontier",
    ("moonshot", "both"): None,
}


def _inputs(author: str, subject: str, risk: str = "high", **extra) -> ResolverInputs:
    """The change's subject seats come from its changed files, as the exception requires."""
    paths = tuple(_SEAT_PATHS[seat] for seat in _SUBJECTS[subject]) or (_UNRELATED,)
    return ResolverInputs(author_model=_AUTHORS[author], risk=risk, owned_paths=paths, changed_paths=paths, **extra)


@pytest.mark.parametrize(("author", "subject"), sorted(_HIGH_MATRIX))
def test_9577_high_risk_matrix_selects_the_exception_only_when_independence_exhausts_the_ladder(author, subject):
    resolution = resolve_reviewer(_inputs(author, subject))
    expected = _HIGH_MATRIX[(author, subject)]
    assert (resolution.selected.name if resolution.selected else None) == expected
    if expected == _EXCEPTION_ID:
        assert resolution.selected.concrete_model == "kimi-code/k3"
        assert resolution.selected.route == "cursor" and resolution.selected.family == "moonshot"
        assert resolution.recorded_exception["id"] == _EXCEPTION_ID
        assert resolution.recorded_exception["decision"] == "#9532"
        assert resolution.recorded_exception["issue"] == "#9577"
        assert resolution.recorded_exception["mode"] == "read-only"
        assert "recorded exception" in resolution.substitution_note and "#9532" in resolution.substitution_note
    elif (author, subject) == ("moonshot", "both"):
        # The trigger holds, but a Kimi/Composer author is the exception seat's own family.
        assert resolution.recorded_exception is None
        excluded = {entry.name: entry for entry in resolution.trace}[_EXCEPTION_ID]
        assert excluded.status == "excluded" and "same family as author (moonshot)" in excluded.reason
    else:
        assert resolution.recorded_exception is None
        assert all(entry.name != _EXCEPTION_ID for entry in resolution.trace)


@pytest.mark.parametrize("risk", ["critical", "medium", "low"])
@pytest.mark.parametrize("author", sorted(_AUTHORS))
@pytest.mark.parametrize("subject", sorted(_SUBJECTS))
def test_9577_controls_other_risks_never_use_the_exception(risk, author, subject):
    resolution = resolve_reviewer(_inputs(author, subject, risk=risk))
    assert resolution.recorded_exception is None
    assert all(entry.name != _EXCEPTION_ID for entry in resolution.trace)


@pytest.mark.parametrize(
    ("author", "snapshot"),
    [
        ("anthropic", {"codex": "unhealthy"}),
        ("openai", {"claude": "unhealthy", "cursor": "unhealthy"}),
        ("anthropic", {"codex": "near_cap"}),
    ],
)
def test_9577_sol_or_opus_unavailability_never_triggers_the_exception(author, snapshot):
    resolution = resolve_reviewer(_inputs(author, "none", routing_snapshot=snapshot))
    assert resolution.selected is None
    assert resolution.recorded_exception is None


def test_9577_exception_seat_obeys_its_own_health_gate():
    resolution = resolve_reviewer(_inputs("anthropic", "codex", routing_snapshot={"cursor": "unhealthy"}))
    assert resolution.selected is None and resolution.recorded_exception is None
    excluded = {entry.name: entry for entry in resolution.trace}[_EXCEPTION_ID]
    assert excluded.status == "excluded" and "unhealthy" in excluded.reason


@pytest.mark.parametrize(
    "extra",
    [
        pytest.param({"subject_seats": frozenset({"codex", "cursor"})}, id="cursor-is-a-subject-seat"),
        pytest.param({"changed_paths": ("curriculum/l2-uk-en/a1/plan.yaml",)}, id="ukrainian-content"),
        pytest.param({"language_lane": True}, id="language-lane"),
        pytest.param({"formal_review": False}, id="advisory"),
    ],
)
def test_9577_exception_keeps_every_other_gate(extra):
    resolution = resolve_reviewer(replace(_inputs("anthropic", "codex"), **extra))
    assert resolution.recorded_exception is None
    assert resolution.selected is None or resolution.selected.name != _EXCEPTION_ID


def test_9577_exception_needs_the_default_ladder_and_is_never_pinnable():
    inputs = _inputs("anthropic", "codex")
    assert resolve_reviewer(inputs, ladder=REVIEW_LADDERS["high"]).recorded_exception is None
    pinned = resolve_reviewer(replace(inputs, pinned_candidate=_EXCEPTION_ID, pressure_override_reason="probe"))
    assert pinned.selected is None and pinned.fail_closed_reason == f"unknown explicit reviewer pin {_EXCEPTION_ID!r}"


@pytest.mark.parametrize("risk", ["high", "medium", "critical"])
def test_9577_direct_evaluation_of_the_exception_seat_is_always_excluded(risk):
    result = evaluate_candidate(SUBJECT_SEAT_EXCEPTION_CANDIDATE, _inputs("anthropic", "codex", risk=risk))
    assert result.status == "excluded" and "recorded exception seat" in result.reason
    assert _EXCEPTION_ID not in REVIEW_CANDIDATES
    assert all(
        candidate.name != _EXCEPTION_ID for rungs in REVIEW_LADDERS.values() for rung in rungs for candidate in rung
    )


@pytest.mark.parametrize(
    ("paths", "declared"),
    [
        pytest.param((_UNRELATED,), {"codex"}, id="unrelated-path-declares-codex"),
        pytest.param((_UNRELATED,), {"codex", "claude"}, id="unrelated-path-declares-both"),
        pytest.param(("scripts/agent_runtime/adapters/base.py",), {"codex"}, id="shared-surface-lists-no-seat"),
        pytest.param(("docs/x.md",), set(), id="no-subject"),
    ],
)
def test_9577_declared_seats_the_diff_does_not_support_never_trigger_the_exception(paths, declared):
    # Blocker 1 (review-9577): an unrelated Claude-authored change declaring codex
    # excludes Sol (a conservative exclusion) but cannot manufacture Kimi review.
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5", risk="high", owned_paths=paths, subject_seats=frozenset(declared)
        )
    )
    assert resolution.recorded_exception is None
    assert resolution.selected is None or resolution.selected.name != _EXCEPTION_ID


@pytest.mark.parametrize(
    ("paths", "declared"),
    [
        pytest.param((_SEAT_PATHS["codex"],), set(), id="codex-adapter"),
        pytest.param(("scripts/agent_runtime/codex_hook_policy.py",), set(), id="codex-hook"),
        pytest.param(("scripts/agent_runtime/adapters/acpx.py",), {"codex"}, id="shared-adapter-lists-codex"),
        pytest.param((_SEAT_PATHS["codex"], _UNRELATED), {"codex"}, id="codex-adapter-plus-unrelated"),
    ],
)
def test_9577_a_genuine_codex_change_triggers_the_exception(paths, declared):
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5", risk="high", owned_paths=paths, subject_seats=frozenset(declared)
        )
    )
    assert resolution.selected is not None and resolution.selected.name == _EXCEPTION_ID
    assert resolution.recorded_exception["subject_seats"] == ["codex"]


def test_9577_a_declared_seat_still_excludes_the_exception_seat_itself():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude-opus-5-5",
            risk="high",
            owned_paths=(_SEAT_PATHS["codex"],),
            subject_seats=frozenset({"cursor"}),
        )
    )
    assert resolution.recorded_exception is None and resolution.selected is None


_HEAD = "a" * 40
_CHANGE = ReviewChange(
    repository="owner/repo", task_id="review-x", head_sha=_HEAD, changed_paths=(_SEAT_PATHS["codex"], _UNRELATED)
)
_RECEIPT_ARGS = dict(
    seat="cursor", model="kimi-k3-high", mode="read-only", author_model="claude-opus-5-5", risk="high", change=_CHANGE
)


def _verify(receipt, **override):
    context = {
        "mode": "read-only",
        "change": _CHANGE,
        "author_model": "claude-opus-5-5",
        "risk": "high",
        "profile": "code",
        **override,
    }
    return verify_review_exception_receipt(receipt, **context)


def test_9577_receipt_binds_repository_task_head_risk_profile_author_and_derived_subjects():
    receipt = review_exception_receipt(**_RECEIPT_ARGS)
    assert receipt["id"] == SUBJECT_SEAT_EXCEPTION["id"]
    assert receipt["repository"] == "owner/repo" and receipt["task_id"] == "review-x" and receipt["head_sha"] == _HEAD
    assert receipt["risk"] == "high" and receipt["review_profile"] == "code"
    assert receipt["author_model"] == "claude-opus-5-5" and receipt["author_family"] == "anthropic"
    assert receipt["subject_seats"] == ["codex"]
    assert _verify(receipt) is None


def test_9577_receipt_is_issued_only_for_the_exact_seat_slug_mode_and_change():
    for change in (
        {"model": "kimi-k3-max"},
        {"model": "kimi-k3-high-fast"},
        {"seat": "kimi"},
        {"mode": "workspace-write"},
        {"risk": "critical"},
        {"author_model": "composer-2.5"},
        {"author_model": None},
        {"change": None},
        {"change": replace(_CHANGE, changed_paths=(_UNRELATED,))},
        {"change": replace(_CHANGE, head_sha="abc123")},
        {"change": replace(_CHANGE, task_id="")},
        {"change": replace(_CHANGE, changed_paths=())},
    ):
        receipt, reason = review_exception_decision(**{**_RECEIPT_ARGS, **change})
        assert receipt is None and reason, change


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        pytest.param("tests/fixtures/" + _SEAT_PATHS["codex"], "does not select", id="nested-test-fixture"),
        pytest.param("docs/" + _SEAT_PATHS["codex"], "does not select", id="nested-docs"),
        pytest.param(_SEAT_PATHS["codex"].replace("scripts", "Scripts", 1), "does not select", id="case-variant"),
        pytest.param(_SEAT_PATHS["codex"] + " ", "has whitespace at either end", id="trailing-space"),
        pytest.param(" " + _SEAT_PATHS["codex"], "has whitespace at either end", id="leading-space"),
        pytest.param(_SEAT_PATHS["codex"] + "\t", "has whitespace at either end", id="trailing-tab"),
        pytest.param(_SEAT_PATHS["codex"].replace("/", "\\"), "has a backslash", id="backslash"),
        pytest.param("scripts\\" + _SEAT_PATHS["codex"], "has a backslash", id="backslash-prefix"),
        pytest.param(_SEAT_PATHS["codex"].replace(".py", "\x07.py"), "control", id="control-character"),
        pytest.param(_SEAT_PATHS["codex"].replace(".py", "\u200b.py"), "format", id="format-character"),
        pytest.param("./" + _SEAT_PATHS["codex"], "not a canonical", id="dot-prefix"),
        pytest.param(_SEAT_PATHS["codex"].replace("/adapters/", "//adapters/"), "not a canonical", id="empty-segment"),
        pytest.param("/" + _SEAT_PATHS["codex"], "not a canonical", id="absolute"),
    ],
)
def test_9577_only_an_exact_git_filename_makes_a_subject_seat(path, reason):
    """Review 9577-b: an adapter-looking or untrimmed name never derives the Codex seat."""
    receipt, why = review_exception_decision(**{**_RECEIPT_ARGS, "change": replace(_CHANGE, changed_paths=(path,))})
    assert receipt is None and reason in why, why
    assert change_supported_seats((path,)) == frozenset()


def test_9577_exact_filenames_keep_the_genuine_adapter_and_hook_seats():
    assert exact_change_path_problem(_SEAT_PATHS["codex"]) is None
    assert change_supported_seats((_SEAT_PATHS["codex"], _UNRELATED)) == frozenset({"codex"})
    assert change_supported_seats(("scripts/agent_runtime/codex_hook_policy.py",)) == frozenset({"codex"})
    assert classify_exact_changed_path("tests/fixtures/" + _SEAT_PATHS["codex"]).kind == "unrelated"
    # The ordinary exclusion path still normalizes owned paths: it only excludes.
    assert classify_owned_path("./" + _SEAT_PATHS["codex"]).seats == frozenset({"codex"})


def test_9577_unsupported_declared_seat_is_named_in_the_refusal():
    receipt, reason = review_exception_decision(
        **{**_RECEIPT_ARGS, "change": replace(_CHANGE, changed_paths=(_UNRELATED,))}, subject_seats=frozenset({"codex"})
    )
    assert receipt is None and "codex are not supported by the changed files" in reason


@pytest.mark.parametrize(
    "override",
    [
        pytest.param({"change": replace(_CHANGE, task_id="review-other")}, id="replay-across-tasks"),
        pytest.param({"change": replace(_CHANGE, head_sha="b" * 40)}, id="replay-across-heads"),
        pytest.param({"change": replace(_CHANGE, repository="owner/other")}, id="replay-across-repositories"),
        pytest.param({"risk": "critical"}, id="critical-task-high-receipt"),
        pytest.param({"risk": "medium"}, id="medium-task-high-receipt"),
        pytest.param({"profile": "ukrainian"}, id="profile"),
        pytest.param({"author_model": "gpt-6.1-sol"}, id="author"),
        pytest.param({"change": replace(_CHANGE, changed_paths=(_UNRELATED,))}, id="subjects-not-in-the-diff"),
        pytest.param(
            {"change": replace(_CHANGE, changed_paths=(_SEAT_PATHS["codex"], _SEAT_PATHS["claude"]))},
            id="subjects-differ",
        ),
        pytest.param({"mode": "acp"}, id="mode"),
    ],
)
def test_9577_a_receipt_replayed_outside_its_review_is_refused(override):
    receipt = review_exception_receipt(**_RECEIPT_ARGS)
    assert _verify(receipt, **override)


@pytest.mark.parametrize(
    "tamper",
    [
        {"author_model": "gpt-6.1-sol"},
        {"author_family": "openai"},
        {"subject_seats": []},
        {"risk": "critical"},
        {"id": "another-exception"},
        {"task_id": "review-other"},
        {"head_sha": "b" * 40},
        {"declared_subject_seats": "codex"},
        {"declared_subject_seats": ["cursor"]},
    ],
)
def test_9577_a_tampered_receipt_is_refused(tamper):
    receipt = review_exception_receipt(**_RECEIPT_ARGS)
    assert _verify({**receipt, **tamper})
    assert _verify(None)
