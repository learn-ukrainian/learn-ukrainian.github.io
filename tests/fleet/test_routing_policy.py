"""Config defaults, one metric override, and a hard rule that cannot move."""

from __future__ import annotations

import pytest

from scripts.fleet.routing_policy import (
    HardRuleRefused,
    done_check_pass_rate,
    log_overrides,
    projected_unused_pct,
    resolve_job,
)


def test_metric_override_replaces_one_job_type() -> None:
    choice = resolve_job(
        "orchestrate",
        metrics={"job_types": {"orchestrate": {"pair": "gemini-with-sol"}}},
    )
    assert choice["pair"]["id"] == "gemini-with-sol"
    assert choice["pair"]["executor"] == "agy"
    assert choice["pair"]["adviser"] == "codex"
    lines = log_overrides(choice)
    assert any("field=pair" in line and "metric=gemini-with-sol" in line for line in lines)
    untouched = resolve_job("implement")
    assert untouched["pair"]["id"] == "grok-with-claude"


def test_hard_rule_rejects_a_metric_that_puts_grok_on_language_work() -> None:
    with pytest.raises(HardRuleRefused):
        resolve_job(
            "implement",
            language=True,
            metrics={"job_types": {"implement": {"pair": "grok-with-claude"}}},
        )


def test_language_handoff_stays_on_sol_or_gemini() -> None:
    choice = resolve_job("orchestrate", language=True)
    assert choice["handoff"] == ["codex", "agy"]
    assert "grok" not in choice["handoff"]
    assert "kimi" not in choice["lanes"]


def test_projected_unused_is_a_percent_only() -> None:
    assert projected_unused_pct(40.0, True) == 40.0
    assert projected_unused_pct(10.0, False) == 0.0
    assert projected_unused_pct(None, True) is None


def test_done_check_pass_rate_groups_existing_outcomes() -> None:
    rates = done_check_pass_rate([
        {"lane": "codex", "model": "sol", "passed": True},
        {"lane": "codex", "model": "sol", "passed": False},
        {"lane": "agy", "model": "flash", "passed": True},
    ])
    assert rates["codex"]["sol"] == 0.5
    assert rates["agy"]["flash"] == 1.0
