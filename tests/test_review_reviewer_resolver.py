"""Tests for the quality-first cross-family reviewer resolver."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.review.reviewer_resolver import (
    AMBIGUOUS_AUTHOR_FAMILY,
    CONFLICTING_AUTHOR_FAMILY,
    DEEPSEEK_V4_FLASH,
    DEEPSEEK_V4_PRO,
    GLM,
    GROK_4_5,
    GROK_4_5_CURSOR_FALLBACK,
    KIMI_K3,
    POOL,
    QWEN,
    REVIEW_CANDIDATES,
    REVIEW_LADDERS,
    TERRA,
    UNATTESTED_AUTHOR_FAMILY,
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
    assert resolve_author_family("cursor", author_family="anthropic") == "anthropic"


def test_cursor_auto_is_unattested_not_unknown():
    # Cursor Auto positively attests no pinned model (model="auto",
    # resolved_model=null) — distinct from a silent/bare harness record.
    assert resolve_author_family("cursor:auto") == UNATTESTED_AUTHOR_FAMILY
    assert resolve_author_family("cursor-auto") == UNATTESTED_AUTHOR_FAMILY
    assert resolve_author_family("cursor-tools:auto") == UNATTESTED_AUTHOR_FAMILY
    assert resolve_author_family("Cursor:AUTO") == UNATTESTED_AUTHOR_FAMILY


def test_author_family_override_against_auto_attestation_is_a_conflict():
    # The harness attests the model was NOT pinned; a caller-asserted single
    # family cannot be corroborated and must not dodge the quorum.
    assert resolve_author_family("cursor:auto", author_family="openai") == CONFLICTING_AUTHOR_FAMILY
    assert resolve_author_family("cursor-auto", author_family="anthropic") == CONFLICTING_AUTHOR_FAMILY
    resolution = resolve_reviewer(ResolverInputs(author_model="cursor:auto", author_family="openai"))
    assert resolution.selected is None
    assert resolution.quorum == ()
    assert resolution.fail_closed_reason


def test_unattested_author_resolves_a_dual_family_quorum():
    resolution = resolve_reviewer(ResolverInputs(author_model="cursor-auto", risk="medium"))
    assert resolution.fail_closed_reason is None
    # No single reviewer of record — the quorum is the formal gate.
    assert resolution.selected is None
    assert len(resolution.quorum) == 2
    families = {seat.family for seat in resolution.quorum}
    assert len(families) == 2
    assert all(seat.status == "selected" for seat in resolution.quorum)
    assert "exact-head" in resolution.quorum_rule
    # Both seats are promoted in the trace, like a single selection would be.
    selected_in_trace = [entry for entry in resolution.trace if entry.status == "selected"]
    assert {entry.name for entry in selected_in_trace} == {seat.name for seat in resolution.quorum}


def test_unattested_quorum_holds_at_every_risk():
    for risk in ("low", "medium", "high", "critical"):
        resolution = resolve_reviewer(ResolverInputs(author_model="cursor:auto", risk=risk))
        assert resolution.fail_closed_reason is None, risk
        assert len(resolution.quorum) == 2, risk
        assert len({seat.family for seat in resolution.quorum}) == 2, risk


def test_unattested_author_with_single_eligible_family_fails_closed():
    # A ladder that only offers one family cannot satisfy the quorum.
    anthropic_only = (
        (REVIEW_CANDIDATES["claude-sonnet-5"],),
        (REVIEW_CANDIDATES["claude-fable-5"],),
    )
    resolution = resolve_reviewer(
        ResolverInputs(author_model="cursor-auto", risk="medium"),
        ladder=anthropic_only,
    )
    assert resolution.selected is None
    assert resolution.quorum == ()
    assert "dual-family quorum unsatisfiable" in resolution.fail_closed_reason


def test_unattested_author_rejects_explicit_reviewer_pin():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="cursor-auto",
            pinned_candidate="gpt-5.6-terra",
            pressure_override_reason="operator request",
        )
    )
    assert resolution.selected is None
    assert resolution.quorum == ()
    assert "pin cannot satisfy the dual-family quorum" in resolution.fail_closed_reason


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
    # OpenAI author: critical → Fable 5 (Sol advisory); high/medium/low → Sonnet 5.
    # Operator 2026-07-26: Opus 5 de-advisored; Fable is the Anthropic authority seat.
    critical = resolve_reviewer(ResolverInputs(author_model="codex", risk="critical"))
    assert critical.selected.name == "claude-fable-5"
    for risk in ("high", "medium", "low"):
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected.name == "claude-sonnet-5", risk


def test_high_risk_anthropic_author_gets_strong_practical_formal_gate():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", risk="high"))
    assert resolution.selected is not None
    assert resolution.selected.name == "grok-4.5"
    assert resolution.selected.suitability_rank == 0


def test_critical_anthropic_author_still_gets_sol_as_formal_gate():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", risk="critical"))
    assert resolution.selected.name == "openai_frontier"
    assert resolution.selected.concrete_model == "gpt-5.6-sol"


def test_high_risk_openai_author_gets_sonnet_not_fable():
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-5.6-terra", risk="high"))
    assert resolution.selected.name == "claude-sonnet-5"
    assert resolution.selected.transport == "native_claude"
    # Authority seats are off the practical ladders — no Sol advisory on routine.
    assert all(entry.name != "openai_frontier" for entry in resolution.trace)


def test_fable_uses_cursor_only_when_native_claude_is_unhealthy():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            risk="critical",
            routing_snapshot={"claude": "unhealthy", "cursor": "healthy"},
        )
    )

    assert resolution.selected is None
    fallback = next(entry for entry in resolution.trace if entry.name == "claude-fable-5-cursor-fallback")
    assert fallback.status == "excluded"
    assert ("formal-review transport" in fallback.reason) or ("generic multi-model harness" in fallback.reason)
    native = next(entry for entry in resolution.trace if entry.name == "claude-fable-5")
    assert native.status == "excluded"
    assert "unhealthy" in native.reason


def test_fable_keeps_native_claude_when_native_health_is_degraded():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-terra",
            risk="critical",
            routing_snapshot={"claude": "degraded", "cursor": "healthy"},
        )
    )

    assert resolution.selected.name == "claude-fable-5"
    assert resolution.selected.transport == "native_claude"
    assert resolution.selected.health == "degraded"


def test_high_risk_kimi_author_gets_claude_not_composer():
    resolution = resolve_reviewer(ResolverInputs(author_model="kimi-code/k3", risk="critical"))
    assert resolution.selected.name == "claude-fable-5"
    composer = next(entry for entry in resolution.trace if entry.name == "composer-2.5")
    assert composer.status == "excluded"
    assert "same family" in composer.reason


def test_medium_risk_uses_sonnet_and_keeps_pool_eligible():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert resolution.selected.name == "claude-sonnet-5"
    assert next(entry for entry in resolution.trace if entry.name == "pool").status == "excluded"


def test_low_risk_pool_author_gets_terra_before_economical_routes():
    resolution = resolve_reviewer(ResolverInputs(author_model="pool", risk="low"))
    assert resolution.selected.name == "gpt-5.6-terra"


def test_policy_receipt_exposes_catalog_version_date_and_risk():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="high"))
    assert resolution.policy_version == "deterministic-formal-routing.v2"
    assert resolution.catalog_reviewed_on == "2026-08-02"
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
    assert resolution.selected.name == "claude-sonnet-5"
    assert resolution.selected.health in {None, "healthy"}


def test_unhealthy_route_is_unavailable_and_falls_to_the_next_quality_tier():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            risk="medium",
            routing_snapshot={"codex": "unhealthy", "cursor": "healthy"},
        )
    )
    # Practical ladder: Terra dark → Sonnet 5 (Claude healthy by default).
    assert resolution.selected.name == "claude-sonnet-5"
    terra = next(entry for entry in resolution.trace if entry.name == "gpt-5.6-terra")
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
    assert resolution.selected.name == "claude-sonnet-5"
    assert resolution.selected.health == "degraded"


def test_real_gemini_lane_outage_excludes_agy_candidates():
    snapshot = {
        "agents": {
            "gemini": {"status": "unknown", "health": {"healthy": False}},
            "grok": {"status": "cool", "health": {"healthy": True}},
        }
    }
    resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium", routing_snapshot=snapshot))
    assert resolution.selected.name == "claude-sonnet-5"
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
    assert unhealthy.selected.name == "claude-sonnet-5"

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
    assert pre_launch.selected.name == "claude-sonnet-5"
    assert pre_launch.selected.health is None

    unknown = resolve_reviewer(
        ResolverInputs(
            author_model="codex",
            risk="medium",
            routing_snapshot={"agy": "unknown", "grok": "unknown"},
        )
    )
    missing = resolve_reviewer(ResolverInputs(author_model="codex", risk="medium"))
    assert unknown.selected.name == missing.selected.name == "claude-sonnet-5"
    assert unknown.substitution_note is None


def test_near_cap_receives_no_new_automatic_assignment_and_uses_eligible_fallback():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            risk="medium",
            routing_snapshot={"codex": "near_cap", "cursor": "healthy"},
        )
    )
    assert resolution.selected is not None
    assert resolution.selected.name == "grok-4.5"
    terra = next(item for item in resolution.trace if item.name == "gpt-5.6-terra")
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


def test_native_grok_dark_falls_to_explicit_cursor_grok():
    snapshot = {
        "grok": "unhealthy",
        "cursor": "healthy",
        "claude": "unhealthy",
        "codex": "unhealthy",
        "agy": "unhealthy",
        "kimi": "unhealthy",
    }
    resolution = resolve_reviewer(
        ResolverInputs(author_model="claude", risk="high", routing_snapshot=snapshot)
    )
    assert resolution.selected is None
    assert next(item for item in resolution.trace if item.name == "grok-4.5-cursor-fallback").status == "excluded"


def test_missing_health_signal_is_fail_open():
    empty = resolve_reviewer(ResolverInputs(author_model="codex", risk="low", routing_snapshot={}))
    absent = resolve_reviewer(ResolverInputs(author_model="codex", risk="low", routing_snapshot=None))
    assert empty.selected.name == absent.selected.name == "claude-sonnet-5"


def test_family_exclusion_is_not_mislabeled_as_a_substitution():
    resolution = resolve_reviewer(ResolverInputs(author_model="gemini", risk="medium"))
    assert resolution.selected.name == "gpt-5.6-terra"
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


def test_deepseek_flash_receipt_uses_entire_native_opencode_high_route():
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
    assert next(item for item in resolution.trace if item.name == "deepseek-v4-flash").status == "excluded"


def test_folk_content_excludes_both_deepseek_models():
    for candidate in (DEEPSEEK_V4_PRO, DEEPSEEK_V4_FLASH):
        result = evaluate_candidate(
            candidate,
            ResolverInputs(author_model="claude", domain="folk_content", formal_review=False),
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
        ResolverInputs(
            author_model="claude", data_egress_policy="local_interactive", requested_role="security_review"
        ),
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
        ResolverInputs(
            author_model="claude", required_capabilities=frozenset({"vesum_mcp"}), formal_review=False
        ),
        author_family="anthropic",
    )
    assert missing.status == "excluded"
    assert "capabilities" in missing.reason

    isolation = evaluate_candidate(
        GROK_4_5_CURSOR_FALLBACK,
        ResolverInputs(author_model="claude", isolation_required=True, formal_review=False),
        author_family="anthropic",
    )
    assert isolation.status == "excluded"
    assert "isolation" in isolation.reason


def test_review_profile_is_a_hard_eligibility_filter():
    result = evaluate_candidate(
        GROK_4_5,
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
        ladder=((DEEPSEEK_V4_FLASH,),),
    )
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"


def test_same_tier_balancing_is_stable_and_yaml_order_independent():
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5"]
    inputs = ResolverInputs(author_model="gemini", exact_head="a" * 40)
    forward = resolve_reviewer(inputs, ladder=((TERRA, sonnet),))
    reverse = resolve_reviewer(inputs, ladder=((sonnet, TERRA),))

    assert forward.selected is not None
    assert forward.selected.name == reverse.selected.name
    assert forward.selected.selection_score == reverse.selected.selection_score
    assert forward.selected.selection_score is not None


def test_load_capacity_headroom_and_freshness_balance_only_within_best_tier():
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5"]
    ladder = ((TERRA, sonnet),)
    inputs = ResolverInputs(author_model="gemini", exact_head="b" * 40, requested_role="implementation")
    capacity_weighted = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 500, "active_reserved_input_bytes": 0}},
            "claude": {"scheduler": {"completed_input_bytes": 600, "active_reserved_input_bytes": 0}},
        }
    }
    weighted_terra = replace(TERRA, capacity_weight=2.0)
    weighted = resolve_reviewer(inputs, ladder=((weighted_terra, sonnet),), runtime_state=capacity_weighted)
    assert weighted.selected.name == "gpt-5.6-terra"

    headroom = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 10, "quota_remaining_pct": 5}},
            "claude": {"scheduler": {"completed_input_bytes": 10, "quota_remaining_pct": 90}},
        }
    }
    selected = resolve_reviewer(inputs, ladder=ladder, runtime_state=headroom)
    assert selected.selected.name == "claude-sonnet-5"

    stale_codex = {
        "agents": {
            "codex": {"scheduler": {"completed_input_bytes": 10, "quota_stale": True}},
            "claude": {"scheduler": {"completed_input_bytes": 10, "quota_stale": False}},
        }
    }
    assert resolve_reviewer(inputs, ladder=ladder, runtime_state=stale_codex).selected.name == "claude-sonnet-5"

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
    assert resolve_reviewer(inputs, ladder=ladder, runtime_state=stale_low_load).selected.name == "claude-sonnet-5"


def test_deterministic_stress_follows_capacity_only_for_equally_suitable_authority_models():
    sol = REVIEW_CANDIDATES["openai_frontier"]
    fable = replace(REVIEW_CANDIDATES["claude-fable-5"], capacity_weight=2.0)
    counts = {"openai_frontier": 0, "claude-fable-5": 0}
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
            ladder=((sol, fable),),
            runtime_state=snapshot,
        )
        selected = resolution.selected
        assert selected is not None
        counts[selected.name] += 1
        assigned_bytes[selected.route] += 1_000

    assert counts == {"openai_frontier": 40, "claude-fable-5": 80}
    assert assigned_bytes == {"codex": 40_000, "claude": 80_000}


def test_ineligible_kimi_k3_never_receives_automatic_review_load():
    counts = {"grok-4.5": 0, "kimi-k3": 0}
    assigned_bytes = {"grok": 0, "kimi": 0}

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
        assert selected.name == "grok-4.5"
        counts[selected.name] += 1
        assigned_bytes[selected.quota_bucket] += 1_000
        kimi_trace = next(item for item in resolution.trace if item.name == "kimi-k3")
        assert kimi_trace.status == "excluded"
        assert "authenticated K3 sealed MCP canary" in kimi_trace.reason

    assert counts == {"grok-4.5": 20, "kimi-k3": 0}
    assert assigned_bytes == {"grok": 20_000, "kimi": 0}


def test_weaker_idle_or_cheaper_route_never_beats_the_best_suitable_quality_tier():
    weaker = REVIEW_CANDIDATES["pool-xs"]
    resolution = resolve_reviewer(
        ResolverInputs(author_model="gemini", formal_review=False, exact_head="e" * 40),
        ladder=((TERRA,), (weaker,)),
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
    assert resolution.selected.name == "gpt-5.6-terra"
    assert resolution.selected.quality_tier == "frontier_practical"
    weaker_trace = next(item for item in resolution.trace if item.name == "pool-xs")
    assert weaker_trace.status == "excluded"
    assert "suitability" in weaker_trace.reason


def test_near_cap_falls_to_a_healthy_same_quality_suitable_candidate():
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5"]
    resolution = resolve_reviewer(
        ResolverInputs(author_model="gemini", risk="high"),
        ladder=((sonnet, TERRA),),
        runtime_state={"agents": {"claude": {"status": "near_cap"}, "codex": {"status": "healthy"}}},
    )
    assert resolution.selected.name == "gpt-5.6-terra"
    sonnet_trace = next(item for item in resolution.trace if item.name == "claude-sonnet-5")
    assert sonnet_trace.status == "excluded"
    assert "near cap" in sonnet_trace.reason


def test_circuit_and_shared_bucket_are_hard_exclusions_before_balancing():
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5"]
    ladder = ((TERRA, sonnet),)
    inputs = ResolverInputs(author_model="gemini", exact_head="c" * 40)
    circuit = resolve_reviewer(
        inputs,
        ladder=ladder,
        runtime_state={"agents": {"codex": {"scheduler": {"circuit_open": True}}}},
    )
    assert circuit.selected.name == "claude-sonnet-5"
    assert "circuit is open" in next(item.reason for item in circuit.trace if item.name == "gpt-5.6-terra")

    bucket = resolve_reviewer(inputs, ladder=ladder, excluded_quota_buckets=frozenset({"codex"}))
    assert bucket.selected.name == "claude-sonnet-5"
    assert "already reserved" in next(item.reason for item in bucket.trace if item.name == "gpt-5.6-terra")

    full_credential = resolve_reviewer(
        inputs,
        ladder=ladder,
        runtime_state={"agents": {"codex": {"scheduler": {"capacity_exhausted": True}}}},
    )
    assert full_credential.selected.name == "claude-sonnet-5"
    assert "no unreserved concurrency slot" in next(
        item.reason for item in full_credential.trace if item.name == "gpt-5.6-terra"
    )


def test_explicit_pin_requires_reason_and_cannot_bypass_formal_transport_gate():
    sonnet = REVIEW_CANDIDATES["claude-sonnet-5"]
    missing_reason = resolve_reviewer(
        ResolverInputs(author_model="gemini", pinned_candidate=sonnet.name), ladder=((TERRA, sonnet),)
    )
    assert missing_reason.selected is None
    assert "pressure_override_reason" in missing_reason.fail_closed_reason

    unsafe = resolve_reviewer(
        ResolverInputs(
            author_model="gemini",
            pinned_candidate="grok-4.5-cursor-fallback",
            pressure_override_reason="native capacity incident",
        ),
        ladder=((REVIEW_CANDIDATES["grok-4.5-cursor-fallback"],),),
    )
    assert unsafe.selected is None
    assert "hard eligibility" in unsafe.fail_closed_reason


def test_explicit_pin_may_override_ladder_preference_but_not_hard_gates():
    fable = REVIEW_CANDIDATES["claude-fable-5"]
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
    assert selected.selected.name == "claude-fable-5"
    assert "explicit pressure override" in selected.substitution_note

    same_family = resolve_reviewer(
        ResolverInputs(
            author_model="claude-sonnet-5",
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


def test_formal_k3_participant_identity_is_explicit():
    k3 = REVIEW_CANDIDATES["kimi-k3"]
    assert k3.route == "kimicc"
    resolution = resolve_reviewer(ResolverInputs(author_model="codex"), ladder=((k3,),))
    assert resolution.selected is None
    result = resolution.trace[0]
    assert result.name == "kimi-k3"
    assert result.transport == "native_kimi"
    assert result.participant == "kimicc"
    assert "authenticated K3 sealed MCP canary" in result.reason


def test_glm_is_a_profile_suitable_fallback_when_preferred_cross_family_route_is_unavailable():
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-5.6-sol",
            author_family="openai",
            review_profile="infra",
            risk="high",
            data_egress_policy="local_interactive",
            exact_head="f" * 40,
        ),
        runtime_state={
            "agents": {
                "codex": {"status": "unhealthy"},
                "claude": {"status": "unhealthy"},
                "grok": {"status": "unhealthy"},
                "kimi": {"status": "unhealthy"},
            }
        },
    )

    assert resolution.selected is not None
    assert resolution.selected.name == "glm-5.2"
    assert resolution.selected.family == "zhipu"
    assert resolution.selected.suitability_rank == 1


def test_sealed_acpx_receipt_exposes_participant_and_credential_bucket_sharing():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", exact_head="d" * 40))
    selected = resolution.selected
    assert selected is not None
    assert selected.participant == "codex"
    assert selected.adapter_transport == "acp"
    assert selected.sealed_executable == "scripts.ai_agent_bridge._review_pr:invoke_inter_agent"
    assert selected.quota_bucket == "codex"
    assert selected.credential_bucket == "codex"
    assert selected.quota_limit == selected.credential_limit == 1

    # K3 is the explicit kimicc ACPX participant, and it shares Kimi's
    # credential/quota buckets rather than creating a fictitious account.
    kimi = REVIEW_CANDIDATES["kimi-k3"]
    assert kimi.participant == "kimicc"
    assert kimi.quota_bucket == kimi.credential_bucket == "kimi"
    assert kimi.quota_limit == kimi.credential_limit == 1


def test_every_risk_ladder_has_unique_candidates_and_a_cross_family_outcome():
    for risk, ladder in REVIEW_LADDERS.items():
        names = [candidate.name for rung in ladder for candidate in rung]
        assert len(names) == len(set(names))
        resolution = resolve_reviewer(ResolverInputs(author_model="codex", risk=risk))
        assert resolution.selected is not None
        assert resolution.selected.family != "openai"


def test_critical_ladder_keeps_authority_before_practical():
    critical = REVIEW_LADDERS["critical"]
    # Operator directive 2026-07-26: Fable 5 is the Anthropic authority seat;
    # Opus 5 is de-advisored and absent from the critical ladder entirely.
    assert [rung[0].name for rung in critical[:4]] == [
        "openai_frontier",
        "claude-fable-5",
        "claude-fable-5-cursor-fallback",
        "gpt-5.6-terra",
    ]


def test_practical_ladder_starts_with_terra_then_sonnet():
    for risk in ("high", "medium", "low"):
        ladder = REVIEW_LADDERS[risk]
        assert [rung[0].name for rung in ladder[:4]] == [
            "gpt-5.6-terra",
            "claude-sonnet-5",
            "glm-5.2",
            "gemini-3.6-flash",
        ]
        assert ladder[4][0].name == "grok-4.5"


def test_candidate_constants_preserve_expected_identity():
    assert TERRA.concrete_model == "gpt-5.6-terra"
    assert KIMI_K3.concrete_model == "kimi-code/k3"
    assert KIMI_K3.transport == "native_kimi"
    assert POOL.concrete_model == "poolside/laguna-s-2.1"
    assert POOL.invocation.endswith("ask-pool")
    assert GLM.requires_data_egress_policy == "local_interactive"
    assert GLM.invocation.endswith("ask-glm")
    assert GROK_4_5.transport == "native_grok"
    from scripts.review.reviewer_resolver import GROK_4_5_CURSOR_FALLBACK, SONNET_5

    assert GROK_4_5_CURSOR_FALLBACK.transport == "cursor"
    assert GROK_4_5_CURSOR_FALLBACK.concrete_model == "grok-4.5"
    assert SONNET_5.concrete_model == "claude-sonnet-5"


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
    codex_entry = next(entry for entry in resolution.trace if entry.name == "gpt-5.6-terra")
    assert codex_entry.status == "excluded"
    assert "degraded_telemetry" in codex_entry.reason
    assert "healthy=true, status=unavailable" in codex_entry.reason


def test_glm_egress_exclusion_reason_names_unlock_flag():
    """GLM fail-closed egress policy exclusion names the unlocking flag."""
    result = evaluate_candidate(
        GLM,
        ResolverInputs(author_model="claude", data_egress_policy=None),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "requires --data-egress-policy local_interactive" in result.reason

