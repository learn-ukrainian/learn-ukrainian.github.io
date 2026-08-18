"""#7010: ``ask-* --pr`` / ``--branch`` route to the lightweight direct review.

Sealed ``review-pr`` is retired (operator 2026-08-07). The legacy ask flags
must no longer bounce agents to it; they fold the target into the prompt and
force review mode on the same path as ``ask-LANE - --type review``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge import _acp_compat, _cli


@pytest.fixture()
def captured(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_compat(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fake_compat)
    return captured


def test_ask_pr_routes_to_lightweight_review_path(captured: dict[str, object]) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-7010", "--pr", "7010", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert captured["args"][0] == "claude"
    # Target folded into the prompt; review mode forced.
    assert "PR #7010" in captured["args"][1]
    assert "gh pr diff 7010" in captured["args"][1]
    assert captured["review"] is True


def test_ask_branch_routes_to_lightweight_review_path(captured: dict[str, object]) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-kimi", "review this change", "--task-id", "review-branch", "--branch", "feat-x", "--from", "test"]
    )

    _cli._handle_ask_kimi(args)

    assert "origin/feat-x" in captured["args"][1]
    assert captured["review"] is True


def test_ask_pr_and_branch_remain_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        _cli._build_parser().parse_args(
            ["ask-claude", "body", "--task-id", "t", "--pr", "1", "--branch", "b"]
        )


def test_ask_pr_no_longer_refuses_with_review_pr_circle(captured: dict[str, object]) -> None:
    """The old refusal named the retired review-pr command as the next step."""
    args = _cli._build_parser().parse_args(
        ["ask-codex", "body", "--task-id", "review-circle", "--pr", "42", "--from", "test"]
    )

    _cli._handle_ask_codex(args)  # must not raise SystemExit

    assert captured["review"] is True


def test_ask_help_no_longer_requires_review_pr() -> None:
    parser = _cli._build_parser()
    help_text = parser.format_help()
    for sub in parser._subparsers._group_actions:  # noqa: SLF001
        for action in getattr(sub, "choices", {}).values():
            help_text += "\n" + action.format_help()
    assert "formal review targets require the review-pr command" not in help_text
    assert "substitute: review-pr" not in help_text
