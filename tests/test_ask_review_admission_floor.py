"""#9125: real target diffs reach the production parser and admission entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.common.git_context import sanitized_git_env


def _git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True, env=sanitized_git_env(), timeout=30).strip()


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    repo = tmp_path / "target"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    (repo / "ordinary.py").write_text("value = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    monkeypatch.setattr(delegate, "_local_repo_root", repo)
    return repo, base


def _change(repo, path):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("value = 2\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "review target")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", head)
    return head


def _args(*flags):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "claude",
            "--model",
            "claude-sonnet-5-5",
            "--task-id",
            "floor-9125",
            "--mode",
            "read-only",
            "--prompt",
            "Review target",
            "--require-review-verdict",
            *flags,
        ]
    )


def _admit(args):
    return delegate._admit_dispatch_target(
        args,
        agent=args.agent,
        trees=None,
        route=delegate._dispatch_route(
            args, delegate._DispatchRouting(), language_lane=False, review_attempt=args.review_attempt
        ),
    )


@pytest.mark.parametrize("risk", ["low", "medium", "high"])
def test_branch_without_owned_paths_uses_merge_base_and_pins_head(review_repo, risk):
    repo, base = review_repo
    head = _change(repo, "scripts/delegate.py")
    # Base advances independently; admission must classify only the branch diff.
    _git(repo, "checkout", "-q", "--detach", base)
    _change(repo, "ordinary-base.py")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", head)
    args = _args("--branch", "review-target", "--review-author-model", "gpt-6.1-sol", "--review-risk", risk)
    refusal, target = _admit(args)
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    assert args.pinned_head == head


def test_ask_review_command_reaches_delegate_floor(review_repo, tmp_path):
    from agent_runtime.target_admission import resolve_and_admit
    from scripts.ai_agent_bridge._dispatch_wrappers import build_ask_review_dispatch_command

    repo, _ = review_repo
    head = _change(repo, "scripts/agent_runtime/adapters/claude.py")
    (seat,) = resolve_and_admit(("claude",), mode="read-only", model="claude-sonnet-5-5", review=True)
    command = build_ask_review_dispatch_command(
        seat, "floor-ask-9125", tmp_path / "prompt.md", effort="high", branch="review-target", pinned_head=head
    )
    args = delegate.build_parser().parse_args(command[2:])
    assert args.branch == "review-target" and args.pinned_head == head
    refusal, target = _admit(args)
    assert target is None
    assert "REVIEW_ROUTE_REFUSED" in refusal and "ineligible" in refusal


def test_attempt_record_paths_reach_immutable_review_admission(tmp_path):
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps({"target": {"changed_paths": ["scripts/delegate.py"]}}))
    refusal, target = _admit(
        _args("--review-attempt", str(attempt), "--review-risk", "low", "--review-author-model", "gpt-6.1-sol")
    )
    assert target is None
    assert "REVIEW_ATTEMPT_IDENTITY_REFUSED" in refusal


@pytest.mark.parametrize(
    "owned", ["scripts/agent_runtime", "scripts/hooks", "scripts/", "scripts", "./scripts/delegate.py"]
)
def test_directory_and_dot_owned_paths_raise_ordinary_branch_to_critical(review_repo, owned):
    repo, _ = review_repo
    _change(repo, "ordinary.py")
    refusal, target = _admit(
        _args(
            "--branch",
            "review-target",
            "--owned-path",
            owned,
            "--review-author-model",
            "gpt-6.1-sol",
            "--review-risk",
            "low",
        )
    )
    assert refusal is None and target.model == "claude-opus-5-5"


@pytest.mark.parametrize(
    "flags",
    [
        (),
        ("--branch", "missing"),
        ("--pinned-head", "f" * 40),
        ("--branch", "review-target", "--pinned-head", "--bad-ref"),
    ],
)
def test_unresolvable_target_refuses_before_route(review_repo, flags, monkeypatch):
    def unexpected(*_args, **_kwargs):
        pytest.fail("unresolved review must refuse before route or launch")

    # An option-shaped SHA is supplied as an equals argument so argparse accepts it.
    if flags and flags[-1] == "--bad-ref":
        flags = (*flags[:-2], "--pinned-head=--bad-ref")
    refusal, target = delegate._admit_dispatch_target(_args(*flags), agent="claude", trees=None, route=unexpected)
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal


@pytest.mark.parametrize(
    "record",
    [{}, {"target": {}}, {"target": {"changed_paths": "scripts/delegate.py"}}, {"target": {"changed_paths": [None]}}],
)
def test_unresolved_attempt_refuses(tmp_path, record):
    path = tmp_path / "attempt.json"
    path.write_text(json.dumps(record))
    refusal, target = _admit(_args("--review-attempt", str(path)))
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal


def test_ordinary_diff_keeps_sonnet(review_repo):
    repo, _ = review_repo
    _change(repo, "ordinary.py")
    refusal, target = _admit(
        _args("--branch", "review-target", "--review-author-model", "gpt-6.1-sol", "--review-risk", "low")
    )
    assert refusal is None and target.model == "claude-sonnet-5-5"


@pytest.mark.parametrize("seat,model", [("kimi", "k3"), ("claude", "claude-fable-5-1")])
def test_prohibited_original_request_refuses_before_target_reads(monkeypatch, seat, model):
    def unexpected(*_args):
        pytest.fail("a prohibited original request must refuse before reading target refs")

    monkeypatch.setattr(delegate, "_dispatch_review_changed_paths", unexpected)
    refusal, target = _admit(_args("--agent", seat, "--model", model))
    assert refusal is not None and target is None
    assert "REVIEW_TARGET_UNRESOLVED" not in refusal


def test_pr_uses_actual_resolved_base_and_refuses_wrong_pin(review_repo, monkeypatch):
    from scripts.review.target_resolution import resolve_branch_target

    repo, _ = review_repo
    head = _change(repo, "scripts/delegate.py")
    resolved = resolve_branch_target(repo, head, "origin/main")
    monkeypatch.setattr("scripts.review.target_resolution.resolve_pr_target", lambda *_args: resolved)
    args = _args("--pr", "9125", "--review-author-model", "gpt-6.1-sol", "--review-risk", "low")
    refusal, target = _admit(args)
    assert refusal is None and target.model == "claude-opus-5-5"
    assert args._review_admission_head == head
    args.pinned_head = "f" * 40
    refusal, target = _admit(args)
    assert target is None and "pinned head differs" in refusal
