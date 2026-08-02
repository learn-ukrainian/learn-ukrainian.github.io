"""review-pr formal CF model + effort pins (practical defaults)."""

from __future__ import annotations

from scripts.agent_runtime.adapters.acpx import (
    ACPX_PARTICIPANT_EFFORTS,
    ACPX_SUPPORTED_PARTICIPANTS,
)
from scripts.ai_agent_bridge._review_pr import (
    FORMAL_CF_EFFORT,
    FORMAL_CF_MODEL,
    formal_cf_pin,
    handle_review_pr,
    resolve_reviewer,
)


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
