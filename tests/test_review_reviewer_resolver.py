"""Tests for the quality-first cross-family reviewer resolver."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.review.reviewer_resolver import (
    AMBIGUOUS_AUTHOR_FAMILY,
    CONFLICTING_AUTHOR_FAMILY,
    DEEPSEEK_V4_FLASH,
    DEEPSEEK_V4_PRO,
    GLM,
    GROK_4_5,
    KIMI_K3,
    POOL,
    QWEN,
    REVIEW_LADDERS,
    TERRA,
    UNKNOWN_AUTHOR_FAMILY,
    ResolverInputs,
    evaluate_candidate,
    resolve_author_family,
    resolve_family,
    resolve_reviewer,
)


def test_family_resolution_across_model_and_harness_aliases():
    cases = {
        "claude": "anthropic",
        "claude-tools": "anthropic",
        "claude-sonnet-5": "anthropic",
        "claude-opus-4-8": "anthropic",
        "claude-fable-5": "anthropic",
        "codex": "openai",
        "codex-tools": "openai",
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
        "grok-4.5": "xai",
        "deepseek-v4-flash": "deepseek",
        "deepseek-v4-pro": "deepseek",
        "pool": "poolside",
        "glm-5.2": "zhipu",
        "qwen/qwen3.6-plus": "qwen",
        "kimi": "moonshot",
        "kimi-code/k3": "moonshot",
        "composer-2.5": "moonshot",
    }
    for seat, expected_family in cases.items():
        assert resolve_family(seat) == expected_family, seat


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
    assert resolve_author_family("cursor", author_family="anthropic") == "anthropic"


def test_invalid_or_conflicting_author_identity_fails_closed():
    assert resolve_author_family("") == UNKNOWN_AUTHOR_FAMILY
    assert resolve_author_family("unknown-seat") == UNKNOWN_AUTHOR_FAMILY
    assert (
        resolve_author_family("cursor:gpt-5.6-sol", author_family="anthropic")
        == CONFLICTING_AUTHOR_FAMILY
    )
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


def test_every_formal_review_risk_uses_the_binding_quality_prior():
    resolutions = [
        resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        for risk in ("critical", "high", "medium", "low")
    ]

    # Sol is advisory for an OpenAI author, so Fable is the first eligible
    # formal reviewer at every risk. A low-risk receipt may not jump to Flash.
    assert [resolution.selected.name for resolution in resolutions] == ["claude-fable-5"] * 4


def test_high_risk_anthropic_author_gets_sol_as_formal_gate():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", risk="high"))
    assert resolution.selected.name == "openai_frontier"
    assert resolution.selected.concrete_model == "gpt-5.6-sol"
    assert resolution.selected.route == "codex"
    assert resolution.selected.transport == "native_codex"


def test_high_risk_openai_author_gets_claude_and_sol_is_advisory():
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-5.6-terra", risk="high"))
    assert resolution.selected.name == "claude-fable-5"
    assert resolution.selected.transport == "cursor"
    assert [entry.name for entry in resolution.advisory] == ["openai_frontier"]
    assert resolution.advisory[0].status == "advisory_only"


def test_high_risk_kimi_author_gets_claude_not_composer():
    resolution = resolve_reviewer(ResolverInputs(author_model="kimi-code/k3", risk="critical"))
    assert resolution.selected.name == "openai_frontier"
    composer = next(entry for entry in resolution.trace if entry.name == "composer-2.5")
    assert composer.status == "excluded"
    assert "same family" in composer.reason


def test_medium_risk_keeps_sol_before_lower_quality_reviewers():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert resolution.selected.name == "claude-fable-5"
    assert next(entry for entry in resolution.trace if entry.name == "pool").status == "eligible"


def test_low_risk_pool_author_keeps_sol_before_economical_routes():
    resolution = resolve_reviewer(ResolverInputs(author_model="pool", risk="low"))
    assert resolution.selected.name == "openai_frontier"


def test_policy_receipt_exposes_catalog_version_date_and_risk():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="high"))
    assert resolution.policy_version == "model-catalog.v1"
    assert resolution.catalog_reviewed_on == "2026-07-17"
    assert resolution.resolved_risk == "high"


def test_unhealthy_route_is_unavailable_and_falls_to_the_next_quality_tier():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            risk="medium",
            routing_snapshot={"codex": "unhealthy", "cursor": "healthy"},
        )
    )
    assert resolution.selected.name == "claude-fable-5"
    sol = next(entry for entry in resolution.trace if entry.name == "openai_frontier")
    assert sol.status == "excluded"
    assert "unhealthy" in sol.reason


def test_real_routing_budget_payload_is_normalized_without_crashing():
    snapshot = {
        "generated_at": "2026-07-17T00:00:00Z",
        "agents": {
            "gemini": {"status": "hot", "health": {"healthy": True}},
            "grok": {"status": "cool", "health": {"healthy": True}},
            "claude": {"status": "warm", "health": {"healthy": True}},
        },
    }
    resolution = resolve_reviewer(
        ResolverInputs(author_model="codex", risk="medium", routing_snapshot=snapshot)
    )
    assert resolution.selected.name == "claude-fable-5"
    assert resolution.selected.health is None


def test_real_gemini_lane_outage_excludes_agy_candidates():
    snapshot = {
        "agents": {
            "gemini": {"status": "unknown", "health": {"healthy": False}},
            "grok": {"status": "cool", "health": {"healthy": True}},
        }
    }
    resolution = resolve_reviewer(
        ResolverInputs(author_model="codex", risk="medium", routing_snapshot=snapshot)
    )
    assert resolution.selected.name == "claude-fable-5"
    gemini = next(entry for entry in resolution.trace if entry.name == "gemini-3.1-pro")
    assert gemini.health == "unhealthy"
    assert gemini.status == "excluded"


def test_health_statuses_are_case_normalized_and_unsupported_values_fail_closed():
    unhealthy = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "UNHEALTHY", "grok": "healthy"},
        )
    )
    assert unhealthy.selected.name == "claude-fable-5"

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
    assert pre_launch.selected.name == "claude-fable-5"
    assert pre_launch.selected.health is None

    unknown = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "unknown", "grok": "unknown"},
        )
    )
    missing = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert unknown.selected.name == missing.selected.name == "claude-fable-5"
    assert "no eligible candidate" in unknown.substitution_note


def test_near_cap_cannot_promote_a_lower_quality_tier():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            risk="medium",
            routing_snapshot={"codex": "near_cap", "cursor": "healthy"},
        )
    )
    assert resolution.selected.name == "openai_frontier"
    assert resolution.selected.health == "near_cap"
    assert resolution.substitution_note is None


def test_all_top_tier_routes_unavailable_fall_to_next_quality_tier():
    snapshot = {
        "claude": "unhealthy",
        "cursor": "unhealthy",
        "codex": "unhealthy",
        "agy": "healthy",
    }
    resolution = resolve_reviewer(
        ResolverInputs(author_model="kimi-code/k3", risk="critical", routing_snapshot=snapshot)
    )
    assert resolution.selected.name == "grok-4.5"


def test_missing_health_signal_is_fail_open():
    empty = resolve_reviewer(
        ResolverInputs(author_model="codex", risk="low", routing_snapshot={})
    )
    absent = resolve_reviewer(
        ResolverInputs(author_model="codex", risk="low", routing_snapshot=None)
    )
    assert empty.selected.name == absent.selected.name == "claude-fable-5"


def test_family_exclusion_is_not_mislabeled_as_a_substitution():
    resolution = resolve_reviewer(ResolverInputs(author_model="gemini", risk="medium"))
    assert resolution.selected.name == "openai_frontier"
    assert resolution.substitution_note is None


def test_health_breaks_ties_only_within_the_same_remaining_quality_rung():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={
                "cursor": "unhealthy",
                "claude": "unhealthy",
                "grok": "unhealthy",
                "agy": "unhealthy",
                "kimi": "near_cap",
                "deepseek-v4-pro": "healthy",
            },
        )
    )
    assert resolution.selected.name == "deepseek-v4-pro"
    assert resolution.selected.health == "healthy"
    assert "kimi-k3" in resolution.substitution_note
    assert "by lane health" in resolution.substitution_note


def test_deepseek_receipt_carries_required_silence_timeout():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="low",
            routing_snapshot={
                "cursor": "unhealthy",
                "claude": "unhealthy",
                "grok": "unhealthy",
                "agy": "unhealthy",
                "kimi": "unhealthy",
                "deepseek-v4-pro": "unhealthy",
                "pool": "unhealthy",
            },
        )
    )
    assert resolution.selected.name == "deepseek-v4-flash"
    assert resolution.selected.requires_silence_timeout is True
    assert "--agent deepseek" in resolution.selected.invocation


def test_folk_content_excludes_both_deepseek_models():
    for candidate in (DEEPSEEK_V4_PRO, DEEPSEEK_V4_FLASH):
        result = evaluate_candidate(
            candidate,
            ResolverInputs(author_model="claude", domain="folk_content"),
            author_family="anthropic",
        )
        assert result.status == "excluded"
        assert "folk_content" in result.reason


def test_glm_data_egress_gate_is_fail_closed():
    for policy in (None, "ci_automated"):
        result = evaluate_candidate(
            GLM,
            ResolverInputs(author_model="claude", data_egress_policy=policy),
            author_family="anthropic",
        )
        assert result.status == "excluded"
    eligible = evaluate_candidate(
        GLM,
        ResolverInputs(author_model="claude", data_egress_policy="local_interactive"),
        author_family="anthropic",
    )
    assert eligible.status == "eligible"


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
        ResolverInputs(author_model="claude", required_capabilities=frozenset({"vesum_mcp"})),
        author_family="anthropic",
    )
    assert missing.status == "excluded"
    assert "capabilities" in missing.reason

    isolation = evaluate_candidate(
        GROK_4_5,
        ResolverInputs(author_model="claude", isolation_required=True),
        author_family="anthropic",
    )
    assert isolation.status == "excluded"
    assert "isolation" in isolation.reason


def test_review_profile_is_a_hard_eligibility_filter():
    result = evaluate_candidate(
        GROK_4_5,
        ResolverInputs(author_model="claude", review_profile="content"),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "profile exclusion" in result.reason


def test_custom_ladder_still_supported_for_focused_callers():
    resolution = resolve_reviewer(
        ResolverInputs(author_model="deepseek-v4-pro", risk="medium"),
        ladder=((DEEPSEEK_V4_FLASH,),),
    )
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"


def test_every_risk_ladder_has_unique_candidates_and_a_cross_family_outcome():
    for risk, ladder in REVIEW_LADDERS.items():
        names = [candidate.name for rung in ladder for candidate in rung]
        assert len(names) == len(set(names))
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected is not None
        assert resolution.selected.family != "openai"


def test_binding_quality_prior_matches_issue_5293_order():
    expected = [
        "openai_frontier",
        "claude-fable-5",
        "claude-opus-4-8",
        "gpt-5.6-terra",
        "grok-4.5",
        "composer-2.5",
        "glm-5.2",
        "gemini-3.1-pro",
    ]
    for ladder in REVIEW_LADDERS.values():
        assert [rung[0].name for rung in ladder[:8]] == expected


def test_candidate_constants_preserve_expected_identity():
    assert TERRA.concrete_model == "gpt-5.6-terra"
    assert KIMI_K3.concrete_model == "kimi-code/k3"
    assert KIMI_K3.transport == "native_kimi"
    assert POOL.concrete_model == "poolside/laguna-m.1"
    assert POOL.invocation.endswith("ask-pool")
    assert GLM.requires_data_egress_policy == "local_interactive"
    assert GLM.invocation.endswith("ask-glm")
