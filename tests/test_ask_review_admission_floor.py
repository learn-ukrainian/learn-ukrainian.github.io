"""#9125: real target diffs reach the production parser and admission entry point."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.common.git_context import sanitized_git_env
from tests.claude_route_accounts import HOST_ACCOUNT
from tests.helpers.review_scope import _git
from tests.helpers.review_scope import ordinary_review_scope as ordinary_review_scope


@pytest.fixture(autouse=True)
def fixed_reviewer_headroom(monkeypatch, reviewer_headroom_snapshot):
    """Exercise the admission floor with fixed capacity, never host quota (#10764)."""
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: deepcopy(reviewer_headroom_snapshot))


@pytest.mark.parametrize("as_request", [False, True])
def test_uninjected_routing_snapshot_fails_before_network(as_request):
    url = "https://example.invalid/api/state/routing-budget?fresh_codexbar=true"
    request = urllib.request.Request(url) if as_request else url
    with pytest.raises(pytest.fail.Exception, match="live reviewer routing snapshot read: inject a fixed snapshot"):
        urllib.request.urlopen(request, timeout=1)


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    from tests.helpers.review_scope import init_review_repo

    repo, base = init_review_repo(tmp_path)
    monkeypatch.setattr(delegate, "_local_repo_root", repo)
    return repo, base


FIXTURE_AUTHOR_TRAILER = "X-Agent: codex/gpt-6.1-sol"


def _change(repo, path):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("value = 2\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, env=sanitized_git_env(), timeout=30)
    subprocess.run(
        ["git", "commit", "-qm", f"review target\n\n{FIXTURE_AUTHOR_TRAILER}"],
        cwd=repo, check=True, env=sanitized_git_env(), timeout=30,
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True, env=sanitized_git_env(), timeout=30).strip()
    subprocess.run(["git", "update-ref", "refs/remotes/origin/review-target", head], cwd=repo, check=True, env=sanitized_git_env(), timeout=30)
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


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_attempt_record_paths_reach_immutable_review_admission(tmp_path, profile):
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps({"target": {"changed_paths": ["scripts/delegate.py"]}}))
    refusal, target = _admit(_args("--review-attempt", str(attempt), "--review-profile", profile))
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
@pytest.mark.parametrize("profile", ["code", "infra"])
def test_unresolved_attempt_refuses(tmp_path, record, profile):
    path = tmp_path / "attempt.json"
    path.write_text(json.dumps(record))
    refusal, target = _admit(_args("--review-attempt", str(path), "--review-profile", profile))
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal


@pytest.mark.parametrize("attempt", [False, True])
def test_ukrainian_review_never_collects_floor_paths(tmp_path, monkeypatch, attempt):
    def unexpected_paths(_args):
        raise AssertionError("Ukrainian review must not collect code/infra floor paths")

    monkeypatch.setattr(delegate, "_dispatch_review_changed_paths", unexpected_paths)
    manifest = tmp_path / "lesson.yaml"
    manifest.write_text("kind: lesson\ninputs: {}\n")
    flags = ["--review-profile", "ukrainian"]
    if attempt:
        flags += ["--review-attempt", str(manifest)]
    refusal, target = _admit(_args(*flags))
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-sonnet-5-5")


def test_admission_does_not_call_a_ukrainian_path_collector():
    from scripts.agent_runtime.target_admission import resolve_and_admit

    def unexpected_paths():
        raise AssertionError("Ukrainian admission must not read code/infra scope")

    (target,) = resolve_and_admit(
        ("claude",),
        model="claude-sonnet-5-5",
        mode="read-only",
        review_dispatch=True,
        review_profile="ukrainian",
        review_attempt=True,
        review_changed_paths=unexpected_paths,
        claude_account=HOST_ACCOUNT,
    )
    assert (target.recipient, target.model) == ("claude", "claude-sonnet-5-5")


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
