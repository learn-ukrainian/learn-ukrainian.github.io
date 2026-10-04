"""#9125: real target diffs reach the production parser and admission entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import delegate
from scripts.common.git_context import sanitized_git_env


def _git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True, env=sanitized_git_env(), timeout=30).strip()


def _init_review_repo(tmp_path, monkeypatch):
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


@pytest.fixture
def review_repo(tmp_path, monkeypatch):
    return _init_review_repo(tmp_path, monkeypatch)


def _change(repo, path):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("value = 2\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "review target")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", head)
    return head


@pytest.fixture
def ordinary_review_scope(tmp_path, monkeypatch):
    """Real ordinary Git scope, even when a dispatch test stubs process spawning."""
    from scripts.review import security_paths, target_resolution

    repo, _base = _init_review_repo(tmp_path, monkeypatch)
    _change(repo, "ordinary.py")
    run_git = target_resolution._run_git
    real_run, real_popen = subprocess.run, subprocess.Popen

    def fixture_git(args, cwd, *, timeout=30.0):
        with patch.object(subprocess, "run", real_run), patch.object(subprocess, "Popen", real_popen):
            return run_git(args, cwd, timeout=timeout)

    monkeypatch.setattr(target_resolution, "_run_git", fixture_git)
    monkeypatch.setattr(security_paths, "_run_git", fixture_git)
    return repo


def write_code_review_manifest(repo, path):
    """Freeze a real code target in the same target shape admission reads."""
    from scripts.review.target_resolution import resolve_branch_target

    target = resolve_branch_target(repo, "refs/remotes/origin/review-target", "refs/remotes/origin/main")
    path.write_text(json.dumps({"target": asdict(target)}))
    return path


def _args(*flags, model="claude-sonnet-5-5"):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "claude",
            "--model",
            model,
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
    refusal, target = _admit(_args(*flags, model="claude-opus-5-5"))
    assert refusal is None
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")


@pytest.mark.parametrize(
    "paths,refused",
    [
        (("wiki/a1/lesson.md",), None),
        (("wiki/a1/lesson.md", "scripts/delegate.py"), "first non-content path: scripts/delegate.py"),
    ],
)
def test_admission_calls_a_ukrainian_target_collector_once(paths, refused):
    from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit

    calls = []

    def collect():
        calls.append(1)
        return paths

    def admit():
        return resolve_and_admit(
            ("claude",),
            model="claude-opus-5-5",
            mode="read-only",
            review_dispatch=True,
            review_profile="ukrainian",
            review_attempt=True,
            review_changed_paths=collect,
        )

    if refused is None:
        (target,) = admit()
        assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    else:
        with pytest.raises(ReviewAdmissionRefused, match=refused):
            admit()
    assert calls == [1]


def test_standalone_ukrainian_admission_has_no_target():
    from scripts.agent_runtime.target_admission import resolve_and_admit

    (target,) = resolve_and_admit(
        ("claude",), model="claude-opus-5-5", mode="read-only", review_dispatch=True, review_profile="ukrainian"
    )
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")


# --- #9714: a targeted Ukrainian review is admitted against its authoritative paths ---

UK_REVIEWERS = [("claude", "claude-opus-5-5"), ("codex", "gpt-6.1-sol")]
CONTENT_ONLY_OWNERSHIP = [pytest.param((), id="owned-omitted"), ("--owned-path", "wiki/a1/lesson.md")]


def _count_collections(monkeypatch):
    calls = []
    real = delegate._dispatch_review_changed_paths

    def counted(args):
        calls.append(1)
        return real(args)

    monkeypatch.setattr(delegate, "_dispatch_review_changed_paths", counted)
    return calls


def _ukrainian(seat, model, *flags):
    return _args("--agent", seat, "--review-profile", "ukrainian", *flags, model=model)


@pytest.mark.parametrize("ownership", CONTENT_ONLY_OWNERSHIP)
@pytest.mark.parametrize("seat,model", UK_REVIEWERS)
@pytest.mark.parametrize(
    "changed", [("scripts/agent_runtime/target_admission.py",), ("wiki/a1/lesson.md", "scripts/launchers/claude.sh")]
)
def test_ukrainian_branch_review_of_code_or_mixed_target_refuses(
    review_repo, monkeypatch, seat, model, ownership, changed
):
    repo, _ = review_repo
    for path in changed:
        head = _change(repo, path)
    calls = _count_collections(monkeypatch)
    args = _ukrainian(seat, model, "--branch", "review-target", *ownership)
    refusal, target = _admit(args)
    assert target is None
    assert "REVIEW_ROUTE_REFUSED" in refusal and f"first non-content path: {changed[-1]}" in refusal
    assert calls == [1] and args.pinned_head == head


@pytest.mark.parametrize("seat,model", [*UK_REVIEWERS, ("agy", "gemini-3.8-flash-high")])
def test_ukrainian_branch_review_of_content_is_admitted_at_the_pinned_head(review_repo, monkeypatch, seat, model):
    repo, _ = review_repo
    head = _change(repo, "wiki/a1/lesson.md")
    calls = _count_collections(monkeypatch)
    args = _ukrainian(seat, model, "--branch", "review-target")
    refusal, target = _admit(args)
    assert refusal is None and (target.recipient, target.model) == (seat, model)
    assert calls == [1] and args.pinned_head == head


@pytest.mark.parametrize("path", ["wiki/reviewer.zsh", "wiki/reviewer.go", "wiki/reviewer.rb", "wiki/a1/reviewer"])
def test_gemini_ukrainian_branch_review_of_an_unsupported_content_kind_refuses(review_repo, path):
    repo, _ = review_repo
    _change(repo, path)
    refusal, target = _admit(_ukrainian("agy", "gemini-3.8-flash-high", "--branch", "review-target"))
    assert target is None
    assert "gemini_code_review_forbidden" in refusal and f"; first non-content path: {path})" in refusal


@pytest.mark.parametrize("ownership", CONTENT_ONLY_OWNERSHIP)
@pytest.mark.parametrize("seat,model", UK_REVIEWERS)
def test_ukrainian_pr_review_of_code_refuses(review_repo, monkeypatch, seat, model, ownership):
    from scripts.review.target_resolution import resolve_branch_target

    repo, _ = review_repo
    head = _change(repo, "scripts/review/record_cf_verdict.py")
    resolved = resolve_branch_target(repo, head, "origin/main")
    monkeypatch.setattr("scripts.review.target_resolution.resolve_pr_target", lambda *_args: resolved)
    args = _ukrainian(seat, model, "--pr", "9714", *ownership)
    refusal, target = _admit(args)
    assert target is None and "first non-content path: scripts/review/record_cf_verdict.py" in refusal
    assert args._review_admission_head == head


@pytest.mark.parametrize("ownership", CONTENT_ONLY_OWNERSHIP)
@pytest.mark.parametrize(
    "changed,refused",
    [
        (["scripts/delegate.py"], "first non-content path: scripts/delegate.py"),
        (["wiki/a1/lesson.md", "scripts/publish/github.py"], "first non-content path: scripts/publish/github.py"),
        (["wiki/a1/lesson.md", "site/src/content/docs/a1/lesson.mdx"], None),
    ],
)
def test_ukrainian_frozen_attempt_target_decides_admission(tmp_path, monkeypatch, ownership, changed, refused):
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps({"target": {"changed_paths": changed}}))
    calls = _count_collections(monkeypatch)
    refusal, target = _admit(_ukrainian("claude", "claude-opus-5-5", "--review-attempt", str(attempt), *ownership))
    assert calls == [1]
    if refused is None:
        assert refusal is None and (target.recipient, target.model) == ("claude", "claude-opus-5-5")
    else:
        assert target is None and refused in refusal


@pytest.mark.parametrize(
    "record", ["{}x: [", "- a list\n", json.dumps({"target": {}}), json.dumps({"target": {"changed_paths": []}})]
)
def test_ukrainian_attempt_with_an_unresolvable_target_refuses(tmp_path, record):
    attempt = tmp_path / "attempt.yaml"
    attempt.write_text(record)
    refusal, target = _admit(_ukrainian("claude", "claude-opus-5-5", "--review-attempt", str(attempt)))
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal


def test_ukrainian_attempt_with_a_missing_record_refuses(tmp_path):
    refusal, target = _admit(_ukrainian("claude", "claude-opus-5-5", "--review-attempt", str(tmp_path / "gone.yaml")))
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal


def test_standalone_ukrainian_request_reads_no_git_paths(monkeypatch):
    from scripts.review import security_paths

    def unexpected(*_args, **_kwargs):
        pytest.fail("a standalone language request has no Git target to read")

    monkeypatch.setattr(security_paths, "git_changed_paths", unexpected)
    monkeypatch.setattr(delegate, "_dispatch_review_changed_paths", unexpected)
    refusal, target = _admit(_ukrainian("codex", "gpt-6.1-sol"))
    assert refusal is None and (target.recipient, target.model) == ("codex", "gpt-6.1-sol")


CODEX_ADAPTER = "scripts/agent_runtime/adapters/codex.py"


def _rename(repo, old, new):
    _change(repo, old)
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / new).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", old, new)
    _git(repo, "commit", "-qm", "rename")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", head)


def _delete(repo, path):
    _change(repo, path)
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "rm", "-q", path)
    _git(repo, "commit", "-qm", "delete")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", _git(repo, "rev-parse", "HEAD"))


@pytest.mark.parametrize("profile", ["code", "infra", "ukrainian"])
@pytest.mark.parametrize("shape", ["modified", "renamed-to-content", "deleted"])
@pytest.mark.parametrize("ownership", CONTENT_ONLY_OWNERSHIP)
def test_changed_paths_exclude_the_own_subject_seat(review_repo, profile, shape, ownership):
    repo, _ = review_repo
    if shape == "modified":
        _change(repo, CODEX_ADAPTER)
    elif shape == "renamed-to-content":
        _rename(repo, CODEX_ADAPTER, "wiki/a1/codex.md")
    else:
        _delete(repo, CODEX_ADAPTER)
    flags = ["--agent", "codex", "--review-profile", profile, "--branch", "review-target", *ownership]
    refusal, target = _admit(_args(*flags, model="gpt-6.1-sol"))
    assert target is None and "REVIEW_ROUTE_REFUSED" in refusal
    if profile == "ukrainian":
        assert "subject seat codex" in refusal and CODEX_ADAPTER in refusal


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_a_reviewer_outside_the_changed_subject_keeps_its_identity(review_repo, profile):
    repo, _ = review_repo
    _change(repo, CODEX_ADAPTER)
    flags = ["--agent", "claude", "--review-profile", profile, "--branch", "review-target"]
    refusal, target = _admit(_args(*flags, model="claude-opus-5-5"))
    assert refusal is None and (target.recipient, target.model) == ("claude", "claude-opus-5-5")


def test_ukrainian_branch_review_of_an_empty_target_refuses(review_repo):
    repo, base = review_repo
    _git(repo, "update-ref", "refs/remotes/origin/review-target", base)
    refusal, target = _admit(_ukrainian("claude", "claude-opus-5-5", "--branch", "review-target"))
    assert target is None and "REVIEW_TARGET_UNRESOLVED" in refusal and "no paths" in refusal


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
