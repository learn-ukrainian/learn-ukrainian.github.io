"""review-pr formal CF model + effort pins (practical defaults)."""

from __future__ import annotations

import pytest

from scripts.agent_runtime.adapters.acpx import (
    ACPX_PARTICIPANT_EFFORTS,
    ACPX_SUPPORTED_PARTICIPANTS,
)
from scripts.ai_agent_bridge._review_pr import (
    FORMAL_CF_EFFORT,
    FORMAL_CF_MODEL,
    _normalize_known_null_review_annotations,
    formal_cf_pin,
    handle_review_pr,
    resolve_requested_review_candidate,
    resolve_reviewer,
)
from scripts.ai_agent_bridge._review_safety import ReviewSafetyError
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES


def test_auto_remains_semantic_until_the_deterministic_scheduler_runs():
    assert resolve_reviewer("auto") == "auto"
    assert resolve_reviewer("codex") == "codex"
    assert resolve_reviewer("agy") == "agy"
    assert resolve_reviewer("auto", claude_available=False) == "auto"


def test_formal_cf_pins_are_practical_seats_at_high():
    assert formal_cf_pin("codex") == ("gpt-5.6-terra", "high")
    assert formal_cf_pin("claude") == ("claude-sonnet-5", "high")
    assert formal_cf_pin("agy") == ("gemini-3.6-flash-high", "high")
    assert formal_cf_pin("glm") == ("glm-5.2", "high")
    assert FORMAL_CF_MODEL["codex"] == "gpt-5.6-terra"
    assert FORMAL_CF_EFFORT["claude"] == "high"


def test_formal_cross_family_pins_match_enabled_acp_routes():
    for reviewer in ("agy", "glm"):
        model, effort = formal_cf_pin(reviewer)
        assert ACPX_SUPPORTED_PARTICIPANTS[reviewer]["model"] == model
        assert ACPX_PARTICIPANT_EFFORTS[reviewer] == effort


@pytest.mark.parametrize(
    ("reviewer", "model", "candidate"),
    [
        ("claude", "claude-sonnet-5", "claude-sonnet-5"),
        ("claude", "claude-fable-5", "claude-fable-5"),
        ("codex", "gpt-5.6-terra", "gpt-5.6-terra"),
        ("codex", "gpt-5.6-sol", "openai_frontier"),
        ("glm", "glm-5.2", "glm-5.2"),
        ("grok", "grok-4.5", "grok-4.5"),
    ],
)
def test_explicit_model_selects_every_formally_eligible_native_route(
    reviewer: str,
    model: str,
    candidate: str,
):
    assert resolve_requested_review_candidate(reviewer, model, REVIEW_CANDIDATES) == candidate


def test_explicit_reviewer_without_model_preserves_practical_default():
    assert (
        resolve_requested_review_candidate("claude", None, REVIEW_CANDIDATES)
        == "claude-sonnet-5"
    )


def test_model_only_pin_ignores_non_formal_fallback_with_same_model():
    assert (
        resolve_requested_review_candidate("auto", "claude-fable-5", REVIEW_CANDIDATES)
        == "claude-fable-5"
    )
    assert (
        resolve_requested_review_candidate("auto", "grok-4.5", REVIEW_CANDIDATES)
        == "grok-4.5"
    )


def test_explicit_model_refuses_wrong_route_and_ineligible_endpoint():
    with pytest.raises(ReviewSafetyError, match="model_not_formal_review_eligible"):
        resolve_requested_review_candidate("claude", "gpt-5.6-sol", REVIEW_CANDIDATES)
    with pytest.raises(ReviewSafetyError, match="reviewer_not_formal_review_eligible"):
        resolve_requested_review_candidate("agy", "gemini-3.6-flash-high", REVIEW_CANDIDATES)


@pytest.mark.parametrize("reviewer", ["agy", "kimi"])
def test_ineligible_reviewer_default_refuses_before_provider_spawn(reviewer: str):
    with pytest.raises(ReviewSafetyError, match="reviewer_not_formal_review_eligible"):
        resolve_requested_review_candidate(reviewer, None, REVIEW_CANDIDATES)


def test_review_pr_dry_run_emits_model_and_effort(capsys):
    class Args:
        pr = "5594"
        reviewer = "auto"
        claude_available = None
        model = None
        effort = None
        extra = None
        task_id = None
        dry_run = True
        from_llm = "grok"
        background = False
        no_timeout = False
        initiator = "grok/orchestrator"
        author_model = "grok-4.5"
        author_family = "xai"

    rc = handle_review_pr(Args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "reviewer_request=auto" in out
    assert "model=deterministic-scheduler" in out
    assert "initiator=grok/orchestrator" in out


def test_review_pr_dry_run_accepts_fable_on_claude_route(capsys):
    class Args:
        pr = "6349"
        reviewer = "claude"
        claude_available = None
        model = "claude-fable-5"
        effort = "high"
        extra = None
        task_id = None
        dry_run = True
        from_llm = "codex"
        background = False
        no_timeout = False
        initiator = "codex/6349-reviewer-model-flexibility"
        author_model = "gpt-5.6-sol"
        author_family = "openai"
        override_reason = "operator requested Fable"

    assert handle_review_pr(Args()) == 0
    out = capsys.readouterr().out
    assert "reviewer_request=claude" in out
    assert "candidate=claude-fable-5" in out
    assert "model=claude-fable-5 effort=high" in out


def test_review_pr_dry_run_accepts_bare_reviewer_default_without_override(capsys):
    class Args:
        pr = "6349"
        reviewer = "claude"
        claude_available = None
        model = None
        effort = None
        extra = None
        task_id = None
        dry_run = True
        from_llm = "codex"
        background = False
        no_timeout = False
        initiator = "codex/6349-reviewer-model-flexibility"
        author_model = "gpt-5.6-sol"
        author_family = "openai"
        override_reason = None

    assert handle_review_pr(Args()) == 0
    out = capsys.readouterr().out
    assert "candidate=claude-sonnet-5" in out
    assert "model=claude-sonnet-5 effort=high" in out


def test_review_pr_dry_run_requires_override_reason_for_explicit_fable(capsys):
    class Args:
        pr = "6349"
        reviewer = "claude"
        claude_available = None
        model = "claude-fable-5"
        effort = None
        extra = None
        task_id = None
        dry_run = True
        from_llm = "codex"
        background = False
        no_timeout = False
        initiator = "codex/6349-reviewer-model-flexibility"
        author_model = "gpt-5.6-sol"
        author_family = "openai"
        override_reason = None

    assert handle_review_pr(Args()) == 2
    assert "requires --override-reason" in capsys.readouterr().err


def test_review_pr_refuses_unbounded_lease_before_provider_spawn(capsys):
    class Args:
        pr = "6349"
        reviewer = "auto"
        claude_available = None
        model = None
        effort = None
        extra = None
        task_id = None
        dry_run = False
        from_llm = "codex"
        background = False
        no_timeout = True
        initiator = "codex/6349-reviewer-model-flexibility"
        author_model = "gpt-5.6-sol"
        author_family = "openai"

    assert handle_review_pr(Args()) == 2
    assert "--no-timeout is unsafe for leased formal reviews" in capsys.readouterr().err


def test_known_null_review_annotation_is_removed_without_relaxing_schema():
    response = (
        '{"schema_version":"code-review-findings.v1","overall":{},'
        '"findings":[{"id":"F1","verbatim_note":null}]}'
    )

    normalized = _normalize_known_null_review_annotations(response)

    assert '"verbatim_note"' not in normalized
    assert '"id":"F1"' in normalized


@pytest.mark.parametrize(
    "response",
    [
        '{"findings":[{"verbatim_note":"meaningful"}]}',
        '{"findings":[{"unknown_note":null}]}',
        '{"findings":[],"findings":[]}',
    ],
)
def test_review_annotation_normalization_preserves_strict_rejections(response: str):
    assert _normalize_known_null_review_annotations(response) == response
