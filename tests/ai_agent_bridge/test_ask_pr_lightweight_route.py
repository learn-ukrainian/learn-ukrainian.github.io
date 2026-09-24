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

import json
import os
import stat

import pytest

from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

_HEAD_SHA = "a" * 40
_MOVED_SHA = "b" * 40
_HEAD_BRANCH = "cursor/impl-8706"


def _install_fake_gh(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    stdout: str = "",
    stderr: str = "",
    code: int = 0,
) -> None:
    """Put a no-network ``gh`` first on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gh"
    script.write_text(
        "#!/bin/sh\n"
        f"printf '%s' {json.dumps(stdout)}\n"
        f"printf '%s' {json.dumps(stderr)} >&2\n"
        f"exit {int(code)}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")


def _same_repo_payload(*, head_sha: str = _HEAD_SHA, branch: str = _HEAD_BRANCH) -> str:
    return json.dumps(
        {
            "headRefName": branch,
            "headRefOid": head_sha,
            "isCrossRepository": False,
        }
    )


@pytest.fixture()
def same_repo_pr_gh(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gh(tmp_path, monkeypatch, stdout=_same_repo_payload())


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
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    same_repo_pr_gh: None,
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
    assert f"exact head {_HEAD_SHA}" in captured_dispatch["content"]
    assert "git rev-parse HEAD" in captured_dispatch["content"]
    assert f"If it differs from {_HEAD_SHA}" in captured_dispatch["content"]
    assert "stop without a verdict" in captured_dispatch["content"]
    assert captured_dispatch["branch"] == _HEAD_BRANCH


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
        _cli._build_parser().parse_args(
            ["ask-claude", "body", "--task-id", "t", "--pr", "1", "--branch", "b"]
        )


def test_ask_pr_no_longer_refuses_with_review_pr_circle(
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    same_repo_pr_gh: None,
) -> None:
    """The old refusal named the retired review-pr command as the next step."""
    args = _cli._build_parser().parse_args(
        ["ask-codex", "body", "--task-id", "review-circle", "--pr", "42", "--from", "test"]
    )

    _cli._handle_ask_codex(args)  # must not raise SystemExit

    assert acp_guard["count"] == 0
    assert captured_dispatch["agent"] == "codex"


def test_ask_pr_type_review_does_not_reach_acp(
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    same_repo_pr_gh: None,
) -> None:
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


def test_ask_pr_dispatches_the_pr_head_branch_and_sha(
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    same_repo_pr_gh: None,
) -> None:
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-8706", "--pr", "8706", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    assert acp_guard["count"] == 0
    assert captured_dispatch["branch"] == _HEAD_BRANCH
    assert f"exact head {_HEAD_SHA}" in str(captured_dispatch["content"])


def test_ask_pr_refuses_cross_repository(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gh(
        tmp_path,
        monkeypatch,
        stdout=json.dumps(
            {
                "headRefName": "fork/feature",
                "headRefOid": _HEAD_SHA,
                "isCrossRepository": True,
            }
        ),
    )
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-cross", "--pr", "12", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="cross-repository"):
        _cli._handle_ask_claude(args)


def test_ask_pr_refuses_when_gh_fails(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gh(tmp_path, monkeypatch, stderr="no such pull request", code=1)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-missing", "--pr", "99", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="refusing to review main"):
        _cli._handle_ask_claude(args)


def test_ask_branch_does_not_consult_gh(
    acp_guard: dict[str, int],
    captured_dispatch: dict[str, object],
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_gh(tmp_path, monkeypatch, stderr="gh must not be called", code=1)
    args = _cli._build_parser().parse_args(
        ["ask-kimi", "review this change", "--task-id", "review-branch", "--branch", "feat-x", "--from", "test"]
    )

    _cli._handle_ask_kimi(args)

    assert acp_guard["count"] == 0
    assert captured_dispatch["branch"] == "feat-x"
    assert "origin/feat-x" in captured_dispatch["content"]
    assert "exact head" not in str(captured_dispatch["content"])
    assert "git rev-parse HEAD" not in str(captured_dispatch["content"])


def test_ask_pr_reports_when_dispatch_base_sha_moved(
    same_repo_pr_gh: None,
    captured_dispatch: dict[str, object],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def moved_dispatch(agent, content, **kwargs):
        captured_dispatch["agent"] = agent
        captured_dispatch["content"] = content
        captured_dispatch.update(kwargs)
        return {
            "ok": True,
            "status": "done",
            "response": "VERDICT: APPROVED\nEvidence: reviewed the diff at scripts/foo.py:1.",
            "worktree_base_sha": _MOVED_SHA,
        }

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", moved_dispatch)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-moved", "--pr", "8706", "--from", "test"]
    )

    _cli._handle_ask_claude(args)

    err = capsys.readouterr().err
    assert f"resolved {_HEAD_SHA}" in err
    assert f"dispatch record base {_MOVED_SHA}" in err


def test_branch_prompt_binds_sha_only_when_known() -> None:
    bound = _cli._review_target_content("remote branch origin/feat-x", "body", sha=_HEAD_SHA)
    unbound = _cli._review_target_content("remote branch origin/feat-x", "body", sha=None)

    assert f"differs from {_HEAD_SHA}" in bound
    assert "git rev-parse HEAD" in bound
    assert "git rev-parse HEAD" not in unbound


def test_ask_pr_names_deleted_origin_branch(
    same_repo_pr_gh: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_branch(*_args, **_kwargs):
        raise RuntimeError(
            "delegate.py dispatch failed rc=1: "
            "could not fetch existing branch 'cursor/impl-8706': "
            "fatal: couldn't find remote ref refs/heads/cursor/impl-8706"
        )

    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", missing_branch)
    args = _cli._build_parser().parse_args(
        ["ask-claude", "review this change", "--task-id", "review-gone", "--pr", "8706", "--from", "test"]
    )

    with pytest.raises(SystemExit, match="no longer exists on origin") as exc_info:
        _cli._handle_ask_claude(args)

    message = str(exc_info.value)
    assert _HEAD_BRANCH in message
    assert "merged or deleted" in message
