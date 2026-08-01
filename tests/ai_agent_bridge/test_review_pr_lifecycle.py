"""Cutover contracts for the retired review-pr bridge lifecycle."""

from __future__ import annotations

from argparse import Namespace

from ai_agent_bridge import _review_pr


def _args(*, background: bool = False, dry_run: bool = False) -> Namespace:
    return Namespace(
        pr="5900",
        reviewer="auto",
        claude_available=None,
        model=None,
        effort=None,
        extra=None,
        task_id=None,
        dry_run=dry_run,
        background=background,
        no_timeout=False,
        from_llm="codex",
    )


def test_review_pr_background_bridge_worker_is_retired(capsys) -> None:
    assert _review_pr.handle_review_pr(_args(background=True)) == 2
    assert "background bridge workers are retired" in capsys.readouterr().err


def test_review_pr_dry_run_selects_glm_acp_pin(capsys) -> None:
    assert _review_pr.handle_review_pr(_args(dry_run=True)) == 0
    output = capsys.readouterr().out
    assert "reviewer=glm" in output
    assert "model=glm-5.2" in output
    assert "effort=high" in output
