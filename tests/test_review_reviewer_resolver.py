"""Tests for scripts/review/reviewer_resolver.py — cross-family reviewer resolution."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.review.reviewer_resolver import (
    DEEPSEEK_V4_FLASH,
    GLM,
    GROK_4_5,
    POOL,
    QWEN,
    ResolverInputs,
    evaluate_candidate,
    resolve_family,
    resolve_reviewer,
)

# --- family resolution across model x harness aliases -------------------------

def test_family_resolution_across_model_and_harness_aliases():
    cases = {
        "claude": "anthropic",
        "claude-tools": "anthropic",
        "sonnet": "anthropic",
        "opus": "anthropic",
        "fable": "anthropic",
        "codex": "openai",
        "codex-tools": "openai",
        "gpt-5.6-sol": "openai",
        "gpt-5.6-terra": "openai",
        "gpt-5.6-luna": "openai",
        "gemini": "google",
        "gemini-tools": "google",
        "agy": "google",
        "agy-tools": "google",
        "gemma": "google",
        "gemma-4-31b-it": "google",
        "grok": "xai",
        "grok-build": "xai",  # permanent historical alias
        "grok-hermes": "xai",  # demoted hermes-hosted path, still xAI
        "grok-tools": "xai",  # V7 writer/reviewer seat alias
        "grok-4.5": "xai",
        "deepseek": "deepseek",
        "deepseek-tools": "deepseek",
        "deepseek-v4-flash": "deepseek",
        "deepseek-v4-pro": "deepseek",
        "cursor": "cursor",
        "cursor-tools": "cursor",
        "pool": "poolside",
        "glm": "zhipu",
        "glm-5.2": "zhipu",
        "qwen": "alibaba",
        "qwen-tools": "alibaba",
    }
    for seat, expected_family in cases.items():
        assert resolve_family(seat) == expected_family, f"{seat} -> expected {expected_family}"


def test_family_resolution_unknown_and_empty():
    assert resolve_family("") == "unknown"
    assert resolve_family("some-made-up-seat-xyz") == "unknown"


# --- default code ladder: cross-family selection ------------------------------

def test_default_ladder_picks_deepseek_for_anthropic_author():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude"))
    assert resolution.selected is not None
    assert resolution.selected.name == "deepseek-v4-flash"
    assert resolution.substitution_note is None


def test_default_ladder_excludes_same_family_and_falls_to_next_rung():
    """Author IS deepseek — deepseek-v4-flash must be excluded (same family),
    falling through to grok-4.5."""
    resolution = resolve_reviewer(ResolverInputs(author_model="deepseek-v4-pro"))
    assert resolution.selected is not None
    assert resolution.selected.name == "grok-4.5"
    deepseek_trace = next(r for r in resolution.trace if r.name == "deepseek-v4-flash")
    assert deepseek_trace.status == "excluded"
    assert "same family" in deepseek_trace.reason
    assert resolution.substitution_note is not None


def test_default_ladder_grok_author_falls_to_deepseek():
    resolution = resolve_reviewer(ResolverInputs(author_model="grok-build"))
    assert resolution.selected is not None
    assert resolution.selected.name == "deepseek-v4-flash"


def test_default_ladder_codex_author_gets_deepseek_and_openai_frontier_is_advisory():
    resolution = resolve_reviewer(ResolverInputs(author_model="codex"))
    assert resolution.selected is not None
    assert resolution.selected.name == "deepseek-v4-flash"
    assert len(resolution.advisory) == 1
    assert resolution.advisory[0].name == "openai_frontier"
    assert resolution.advisory[0].concrete_model == "gpt-5.6-sol"
    assert resolution.advisory[0].status == "advisory_only"


def test_openai_frontier_resolves_to_concrete_model_regardless_of_author():
    """Even for a non-OpenAI author, openai_frontier must resolve to a concrete
    model (gpt-5.6-sol) rather than a bare label."""
    resolution = resolve_reviewer(ResolverInputs(author_model="claude"))
    frontier_entry = next(r for r in resolution.trace if r.name == "openai_frontier")
    assert frontier_entry.concrete_model == "gpt-5.6-sol"


def test_openai_frontier_never_becomes_the_formal_gate_for_openai_author():
    """No matter what happens upstream, an OpenAI-family author must never
    get openai_frontier as the `selected` (formal, blocking) reviewer."""
    resolution = resolve_reviewer(ResolverInputs(author_model="gpt-5.6-terra"))
    assert resolution.selected is None or resolution.selected.name != "openai_frontier"
    assert any(r.name == "openai_frontier" and r.status == "advisory_only" for r in resolution.trace)


def test_openai_frontier_is_a_formal_eligible_candidate_for_non_openai_author():
    """For a non-OpenAI author, openai_frontier is a normal (non-advisory)
    ladder candidate — just ranked last by default."""
    resolution = resolve_reviewer(ResolverInputs(author_model="claude"))
    frontier_entry = next(r for r in resolution.trace if r.name == "openai_frontier")
    assert frontier_entry.status == "eligible"


# --- health tie-break ---------------------------------------------------------

def test_health_does_not_override_ladder_priority_across_rungs():
    """Health is a tie-breaker AMONG QUALIFIED ROUTES at the same priority —
    it must not silently reroute away from a healthy-ranked-first candidate
    just because a routing snapshot marks it degraded. That would make health
    a hard filter instead of a tie-breaker, and hide a real ladder-priority
    decision behind lane-health noise."""
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            routing_snapshot={"deepseek-v4-flash": "unhealthy"},
        )
    )
    assert resolution.selected.name == "deepseek-v4-flash"
    assert resolution.selected.health == "unhealthy"


def test_health_breaks_genuine_ties_within_a_rung():
    grok_variant = GROK_4_5
    deepseek_variant = DEEPSEEK_V4_FLASH
    same_rung_ladder = ((deepseek_variant, grok_variant),)
    resolution = resolve_reviewer(
        ResolverInputs(
            author_model="claude",
            routing_snapshot={"deepseek-v4-flash": "unhealthy", "grok-4.5": "healthy"},
        ),
        ladder=same_rung_ladder,
    )
    assert resolution.selected.name == "grok-4.5"


def test_health_missing_signal_is_fail_open_not_excluded():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude", routing_snapshot={}))
    assert resolution.selected.name == "deepseek-v4-flash"
    resolution_none = resolve_reviewer(ResolverInputs(author_model="claude", routing_snapshot=None))
    assert resolution_none.selected.name == "deepseek-v4-flash"


# --- domain carve-out (folk content) -------------------------------------------

def test_folk_content_domain_excludes_deepseek():
    result = evaluate_candidate(
        DEEPSEEK_V4_FLASH,
        ResolverInputs(author_model="claude", domain="folk_content"),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "folk_content" in result.reason


def test_non_folk_domain_does_not_exclude_deepseek():
    result = evaluate_candidate(
        DEEPSEEK_V4_FLASH,
        ResolverInputs(author_model="claude", domain="code"),
        author_family="anthropic",
    )
    assert result.status == "eligible"


# --- fail-closed data-egress + hard cost exclusions ----------------------------

def test_glm_excluded_when_data_egress_policy_unspecified_fail_closed():
    result = evaluate_candidate(
        GLM,
        ResolverInputs(author_model="claude", data_egress_policy=None),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "fail-closed" in result.reason


def test_glm_excluded_for_wrong_policy_value():
    result = evaluate_candidate(
        GLM,
        ResolverInputs(author_model="claude", data_egress_policy="ci_automated"),
        author_family="anthropic",
    )
    assert result.status == "excluded"


def test_glm_eligible_only_for_matching_local_interactive_policy():
    result = evaluate_candidate(
        GLM,
        ResolverInputs(author_model="claude", data_egress_policy="local_interactive"),
        author_family="anthropic",
    )
    assert result.status == "eligible"


def test_qwen_always_excluded_regardless_of_policy():
    result = evaluate_candidate(
        QWEN,
        ResolverInputs(author_model="claude", data_egress_policy="local_interactive"),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "cost" in result.reason


# --- required capabilities / isolation ------------------------------------------

def test_missing_required_capability_excludes_candidate():
    result = evaluate_candidate(
        POOL,
        ResolverInputs(author_model="claude", required_capabilities=frozenset({"vesum_mcp"})),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "capabilities" in result.reason


def test_isolation_required_excludes_candidate_without_it():
    result = evaluate_candidate(
        GROK_4_5,
        ResolverInputs(author_model="claude", isolation_required=True),
        author_family="anthropic",
    )
    assert result.status == "excluded"
    assert "isolation" in result.reason


# --- receipt visibility ---------------------------------------------------------

def test_trace_covers_every_ladder_candidate_for_receipt_visibility():
    resolution = resolve_reviewer(ResolverInputs(author_model="claude"))
    traced_names = {r.name for r in resolution.trace}
    assert traced_names == {"deepseek-v4-flash", "grok-4.5", "pool", "openai_frontier"}


def test_no_eligible_candidate_leaves_selected_none():
    """An author family that happens to match every ladder rung (contrived,
    via a single-candidate custom ladder) must not silently promote an
    excluded/advisory candidate to selected."""
    resolution = resolve_reviewer(
        ResolverInputs(author_model="deepseek-v4-pro"),
        ladder=((DEEPSEEK_V4_FLASH,),),
    )
    assert resolution.selected is None
    assert resolution.trace[0].status == "excluded"
