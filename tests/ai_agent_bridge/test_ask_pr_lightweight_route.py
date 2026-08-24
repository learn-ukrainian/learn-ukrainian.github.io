"""#7155: ask-* review intent must reach a reviewer with tools, never ACP.

ACP is intercommunication only (`--deny-all --no-fs --no-terminal`); a
reviewer must be able to run `gh`/pytest/fs. Live proof: #7155
`ask-codex --review --pr 7155` ABSTAINed via ACP (`gh auth` unavailable),
while the same review via headless dispatch with tools approved. `ask-*
--review` / `--type review` / `--pr` / `--branch` now route to the headless
`scripts/delegate.py dispatch` path, never to the tool-less ACP shim
(`run_compat_ask`). Ordinary asks without review intent are unaffected.
"""

from __future__ import annotations

import pytest

from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers


@pytest.fixture()
def acp_guard(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Fail the test the instant review intent reaches the tool-less ACP shim."""
    calls = {"count": 0}

    def fail_if_called(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("run_compat_ask must not be called for review intent (#7155)")

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fail_if_called)
    return calls


@pytest.fixture()
def captured_dispatch(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_dispatch(agent, content, **kwargs):
        captured["agent"] = agent
        captured["content"] = content
        captured.update(kwargs)
        return {
            "ok": True,
            "status": "done",
            "response": "VERDICT: APPROVED\nEvidence: reviewed the diff at scripts/foo.py:1.",
        }

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", fake_dispatch)
    return captured


def test_ask_pr_routes_to_headless_dispatch_not_acp(
    acp_guard: dict[str, int], captured_dispatch: dict[str, object]
) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-7010", "--pr", "7010", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert acp_guard["count"] == 0
    assert captured_dispatch["agent"] == "claude"
    assert captured_dispatch["task_id"] == "review-7010"
    # Target folded into the prompt.
    assert "PR #7010" in captured_dispatch["content"]
    assert "gh pr diff 7010" in captured_dispatch["content"]


def test_ask_branch_routes_to_headless_dispatch_not_acp(
    acp_guard: dict[str, int], captured_dispatch: dict[str, object]
) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-kimi", "review this change", "--task-id", "review-branch", "--branch", "feat-x", "--from", "test"]
    )

    _cli._handle_ask_kimi(args)

    assert acp_guard["count"] == 0
    assert "origin/feat-x" in captured_dispatch["content"]


def test_ask_pr_and_branch_remain_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        _cli._build_parser().parse_args(["ask-claude", "body", "--task-id", "t", "--pr", "1", "--branch", "b"])


def test_ask_pr_no_longer_refuses_with_review_pr_circle(
    acp_guard: dict[str, int], captured_dispatch: dict[str, object]
) -> None:
    """The old refusal named the retired review-pr command as the next step."""
    args = _cli._build_parser().parse_args(
        ["ask-codex", "body", "--task-id", "review-circle", "--pr", "42", "--from", "test"]
    )

    _cli._handle_ask_codex(args)  # must not raise SystemExit

    assert acp_guard["count"] == 0
    assert captured_dispatch["agent"] == "codex"


def test_ask_pr_type_review_does_not_reach_acp(acp_guard: dict[str, int], captured_dispatch: dict[str, object]) -> None:
    """Exact #7155 acceptance scenario: ask-codex --pr <N> --type review."""
    args = _cli._build_parser().parse_args(
        [
            "ask-codex",
            "review this change",
            "--task-id",
            "review-7155",
            "--pr",
            "7155",
            "--type",
            "review",
            "--from",
            "test",
        ]
    )

    _cli._handle_ask_codex(args)

    assert acp_guard["count"] == 0
    assert captured_dispatch["agent"] == "codex"


def test_ordinary_ask_without_review_intent_still_uses_acp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-review asks are unaffected: ACP intercom stays the transport."""
    from types import SimpleNamespace

    captured: dict[str, object] = {}

    def fake_compat(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "run_compat_ask", fake_compat)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "just a question", "--task-id", "plain-ask", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert captured["args"][0] == "claude"
    assert captured["review"] is False


def test_ask_help_no_longer_requires_review_pr() -> None:
    parser = _cli._build_parser()
    help_text = parser.format_help()
    for sub in parser._subparsers._group_actions:
        for action in getattr(sub, "choices", {}).values():
            help_text += "\n" + action.format_help()
    assert "formal review targets require the review-pr command" not in help_text
    assert "substitute: review-pr" not in help_text
