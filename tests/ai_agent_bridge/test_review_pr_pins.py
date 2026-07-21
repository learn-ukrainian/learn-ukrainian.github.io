"""review-pr formal CF model + effort pins (practical defaults)."""

from __future__ import annotations

from scripts.ai_agent_bridge._review_pr import (
    FORMAL_CF_EFFORT,
    FORMAL_CF_MODEL,
    formal_cf_pin,
    handle_review_pr,
    resolve_reviewer,
)


def test_auto_and_codex_resolve_to_codex_transport():
    assert resolve_reviewer("auto") == "codex"
    assert resolve_reviewer("codex") == "codex"
    assert resolve_reviewer("auto", claude_available=False) == "glm"


def test_formal_cf_pins_are_practical_seats_at_high():
    assert formal_cf_pin("codex") == ("gpt-5.6-terra", "high")
    assert formal_cf_pin("claude") == ("claude-sonnet-5", "high")
    assert formal_cf_pin("glm") == ("glm-5.2", "high")
    assert FORMAL_CF_MODEL["codex"] == "gpt-5.6-terra"
    assert FORMAL_CF_EFFORT["claude"] == "high"


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

    rc = handle_review_pr(Args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "reviewer=codex" in out
    assert "model=gpt-5.6-terra" in out
    assert "effort=high" in out
    assert "gpt-5.6-terra @ effort=high" in out
