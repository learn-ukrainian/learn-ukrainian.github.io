"""Terminal publication uses real local remotes and ordinary Git hooks (#10931)."""

from __future__ import annotations

import subprocess

import pytest

import delegate
from tests.test_delegate import (
    _agy_dispatch_worktree,
    _git_out,
    _sanitize_git_env_for_test,
    isolated_finalization_context,  # noqa: F401
)


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    worktree = _agy_dispatch_worktree(tmp_path, "codex/finalize")
    marker = tmp_path / "push-observed"
    hook = worktree / ".git/hooks/pre-push"
    hook.write_text(f'#!/bin/sh\nprintf observed >> "{marker}"\n')
    hook.chmod(0o755)
    return worktree, tmp_path / "origin.git", marker


def finalize(worktree):
    return delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id="finalize",
        agent="codex",
        model="gpt-6.1-sol",
        branch="codex/finalize",
        base_branch="main",
        owned_paths=["artifact.txt"],
    )


def remote_head(origin):
    output = _git_out(origin, "for-each-ref", "--format=%(objectname)", "refs/heads/codex/finalize")
    return output.strip() or None


def commit(worktree, content=b"committed\r\n"):
    (worktree / "artifact.txt").write_bytes(content)
    _git_out(worktree, "add", "artifact.txt")
    _git_out(worktree, "commit", "-m", "completed work")
    return delegate._resolve_sha(worktree)


@pytest.mark.parametrize("case", ["clean", "dirty", "mixed", "retry"])
def test_finalization_publishes_exact_head_and_preserves_bytes(checkout, case):
    worktree, origin, marker = checkout
    if case != "dirty":
        commit(worktree)
    if case in {"dirty", "mixed"}:
        (worktree / "artifact.txt").write_bytes(b"current\r\n\x00bytes\n")
    expected = (worktree / "artifact.txt").read_bytes()
    first = finalize(worktree)
    assert first.ok, first.error
    assert first.commit_sha == remote_head(origin) == delegate._resolve_sha(worktree)
    assert (worktree / "artifact.txt").read_bytes() == expected
    assert _git_out(worktree, "status", "--porcelain") == ""
    assert delegate._count_unpushed_commits(worktree, "codex/finalize") == 0
    assert marker.read_text() == "observed"
    second = finalize(worktree)
    assert second.ok and second.commit_sha == first.commit_sha == remote_head(origin)
    assert (worktree / "artifact.txt").read_bytes() == expected
    assert marker.read_text() == "observedobserved"


@pytest.mark.parametrize("case", ["clean", "dirty", "mixed"])
def test_rejected_pre_push_retains_commit_and_current_bytes(checkout, case):
    worktree, origin, marker = checkout
    if case != "dirty":
        commit(worktree)
    if case != "clean":
        (worktree / "artifact.txt").write_bytes(b"current\r\n\x00bytes\n")
    expected = (worktree / "artifact.txt").read_bytes()
    hook = worktree / ".git/hooks/pre-push"
    (worktree.parent / "trusted-gate-refuse").touch()
    hook.write_text(hook.read_text() + "exit 1\n")
    result = finalize(worktree)
    assert not result.ok and result.error.startswith("auto_finalize_push_failed")
    assert remote_head(origin) is None
    assert result.commit_sha == delegate._resolve_sha(worktree)
    assert (worktree / "artifact.txt").read_bytes() == expected
    assert marker.read_text() == "observed"
    (worktree.parent / "trusted-gate-refuse").unlink()
    hook.write_text(hook.read_text().replace("exit 1\n", ""))
    retried = finalize(worktree)
    assert retried.ok and retried.commit_sha == result.commit_sha == remote_head(origin)


@pytest.mark.parametrize("branch", ["main", "master", "codex/foreign", None])
def test_protected_or_mismatched_recorded_branch_publishes_nothing(checkout, branch):
    worktree, origin, marker = checkout
    head = commit(worktree)
    (worktree / "artifact.txt").write_bytes(b"dirty bytes\r\n")
    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id="finalize",
        agent="codex",
        branch=branch,
        base_branch="main",
        owned_paths=["artifact.txt"],
    )
    assert not result.ok and result.error == "auto_finalize_unsafe_branch"
    assert remote_head(origin) is None and not marker.exists()
    assert delegate._resolve_sha(worktree) == head
    assert (worktree / "artifact.txt").read_bytes() == b"dirty bytes\r\n"


def test_unowned_committed_work_is_never_published(checkout):
    worktree, origin, marker = checkout
    _git_out(worktree, "commit", "--allow-empty", "-m", "empty owned change")
    (worktree / "README.md").write_text("foreign commit\n")
    _git_out(worktree, "add", "README.md")
    _git_out(worktree, "commit", "-m", "foreign change")
    result = finalize(worktree)
    assert not result.ok and result.error == "auto_finalize_committed_scope_unowned"
    assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "README.md").read_text() == "foreign commit\n"


@pytest.mark.parametrize("failure", ["timeout", "unknown_remote", "remote_moved", "head_moved"])
def test_push_uncertainty_never_reports_success(checkout, monkeypatch, failure):
    worktree, origin, _marker = checkout
    head = commit(worktree)
    real_run = delegate.subprocess.run
    seen = 0

    def run(args, **kwargs):
        nonlocal seen
        if args[1:2] == ["push"] and failure == "timeout":
            raise subprocess.TimeoutExpired(args, 1)
        if args[1:3] == ["ls-remote", "--refs"]:
            seen += 1
            if failure == "unknown_remote":
                return subprocess.CompletedProcess(args, 128, b"", b"network unavailable")
            if failure == "remote_moved" and seen == 2:
                return subprocess.CompletedProcess(args, 0, b"0" * 40 + b"\trefs/heads/codex/finalize\n", b"")
        result = real_run(args, **kwargs)
        if args[1:2] == ["push"] and failure == "head_moved":
            real_run(
                ["git", "commit", "--allow-empty", "-m", "concurrent movement"],
                cwd=worktree,
                check=True,
                capture_output=True,
            )
        return result

    monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert not result.ok
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"
    assert remote_head(origin) == (head if failure in {"remote_moved", "head_moved"} else None)
    assert result.commit_sha == head


def test_remote_divergence_is_not_force_pushed(checkout, tmp_path):
    worktree, origin, _marker = checkout
    local = commit(worktree)
    other = tmp_path / "other"
    _git_out(tmp_path, "clone", "--branch", "main", str(origin), str(other))
    _git_out(other, "config", "user.email", "test@example.com")
    _git_out(other, "config", "user.name", "test")
    _git_out(other, "checkout", "-b", "codex/finalize")
    (other / "different.txt").write_text("other writer\n")
    _git_out(other, "add", "different.txt")
    _git_out(other, "commit", "-m", "other writer")
    _git_out(other, "push", "origin", "codex/finalize")
    remote = delegate._resolve_sha(other)
    result = finalize(worktree)
    assert not result.ok and remote_head(origin) == remote != local
    assert delegate._resolve_sha(worktree) == local
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


def test_push_destination_is_verified_instead_of_fetch_destination(checkout, tmp_path):
    worktree, origin, marker = checkout
    destination = tmp_path / "push.git"
    _git_out(tmp_path, "init", "--bare", str(destination))
    head = commit(worktree)
    _git_out(worktree, "remote", "set-url", "--push", "origin", str(destination))
    result = finalize(worktree)
    assert result.ok, result.error
    assert result.commit_sha == head == remote_head(origin)
    assert remote_head(destination) is None
    assert marker.read_text() == "observed"
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


@pytest.mark.parametrize("configuration", ["multiple", "missing", "changed"])
def test_unknown_or_moved_push_destination_never_claims_delivery(checkout, tmp_path, monkeypatch, configuration):
    worktree, origin, marker = checkout
    head = commit(worktree)
    if configuration == "multiple":
        _git_out(worktree, "config", "--add", "remote.origin.pushurl", str(origin))
        _git_out(worktree, "config", "--add", "remote.origin.pushurl", str(tmp_path / "other.git"))
    elif configuration == "missing":
        _git_out(worktree, "remote", "remove", "origin")
    else:
        real_run = delegate.subprocess.run

        def run(args, **kwargs):
            result = real_run(args, **kwargs)
            if args[1:2] == ["push"]:
                real_run(
                    ["git", "remote", "set-url", "--push", "origin", str(tmp_path / "other.git")],
                    cwd=worktree,
                    check=True,
                    capture_output=True,
                )
            return result

        monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert result.ok, result.error
    assert remote_head(origin) == head
    assert marker.read_text() == "observed"
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


@pytest.mark.parametrize("uncertainty", ["dirty", "changes", "scope", "invalid_remote"])
def test_unknown_finalization_evidence_is_a_typed_refusal(checkout, monkeypatch, uncertainty):
    worktree, origin, marker = checkout
    head = commit(worktree)
    if uncertainty == "dirty":
        monkeypatch.setattr(delegate, "_worktree_is_dirty", lambda *_a: None)
    elif uncertainty == "changes":
        monkeypatch.setattr(delegate, "_worktree_is_dirty", lambda *_a: True)
    elif uncertainty == "scope":
        monkeypatch.setattr(delegate, "_advisory_worker_diff", lambda *_a, **_k: (None, "unreadable"))
    else:
        real_run = delegate.subprocess.run

        def run(args, **kwargs):
            if args[1:3] == ["ls-remote", "--refs"]:
                return subprocess.CompletedProcess(args, 0, b"malformed remote evidence\n", b"")
            return real_run(args, **kwargs)

        monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert not result.ok
    assert (
        result.error
        == {
            "dirty": "auto_finalize_dirty_unknown",
            "changes": "auto_finalize_changes_unknown",
            "scope": "auto_finalize_committed_scope_unknown",
            "invalid_remote": "auto_finalize_remote_unknown",
        }[uncertainty]
    )
    assert delegate.is_public_cause(result.error)
    assert remote_head(origin) is None and not marker.exists()
    assert delegate._resolve_sha(worktree) == head
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


@pytest.mark.parametrize("branch", ["main", "codex/foreign"])
def test_push_boundary_itself_refuses_unsafe_branch(checkout, branch):
    worktree, origin, marker = checkout
    head = commit(worktree)
    with pytest.raises(RuntimeError, match=r"^auto_finalize_unsafe_branch$"):
        delegate._push_auto_finalize_branch(worktree, branch, owned_paths=["artifact.txt"])
    assert delegate._resolve_sha(worktree) == head
    assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


def test_named_origin_push_does_not_rewrite_an_expanded_url_twice(checkout, tmp_path):
    worktree, origin, marker = checkout
    head = commit(worktree)
    unintended = tmp_path / "unintended.git"
    _git_out(tmp_path, "init", "--bare", str(unintended))
    _git_out(worktree, "push", str(unintended), "HEAD:refs/heads/sentinel")
    before = _git_out(unintended, "show-ref")
    marker.unlink()
    _git_out(worktree, "config", f"url.{origin}.insteadOf", "alias:intended")
    _git_out(worktree, "config", f"url.{unintended}.insteadOf", str(origin))
    _git_out(worktree, "remote", "set-url", "origin", "alias:intended")
    assert _git_out(worktree, "remote", "get-url", "--push", "origin").strip() == str(origin)
    assert _git_out(worktree, "ls-remote", "--get-url", str(origin)).strip() == str(unintended)
    result = finalize(worktree)
    assert result.ok, result.error
    assert result.commit_sha == head == remote_head(origin)
    assert delegate._count_unpushed_commits(worktree, "codex/finalize") == 0
    assert _git_out(unintended, "show-ref") == before
    assert remote_head(unintended) is None
    assert marker.read_text() == "observed"
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


def test_push_instead_of_with_unqueryable_endpoint_refuses_before_publication(checkout, tmp_path):
    worktree, origin, marker = checkout
    head = commit(worktree)
    unintended = tmp_path / "unintended.git"
    _git_out(tmp_path, "init", "--bare", str(unintended))
    _git_out(worktree, "config", f"url.{origin}.pushInsteadOf", "alias:intended")
    _git_out(worktree, "config", f"url.{unintended}.insteadOf", str(origin))
    _git_out(worktree, "remote", "set-url", "origin", "alias:intended")
    result = finalize(worktree)
    assert result.ok, result.error
    assert remote_head(origin) == head
    assert remote_head(unintended) is None
    assert marker.read_text() == "observed"


@pytest.mark.parametrize("uncertainty", ["unknown_query", "head", "branch", "endpoint"])
def test_prepublication_movement_or_unknown_query_refuses_before_push(checkout, monkeypatch, uncertainty):
    worktree, origin, marker = checkout
    head = commit(worktree)
    real_query = delegate._finalize_remote_head

    def query(context, branch):
        result = real_query(context, branch)
        if uncertainty == "unknown_query":
            raise delegate.SnapshotRefusal("auto_finalize_remote_unknown")
        if uncertainty == "head":
            _git_out(worktree, "commit", "--allow-empty", "-m", "concurrent movement")
        elif uncertainty == "branch":
            _git_out(worktree, "checkout", "-b", "codex/moved")
        elif uncertainty == "endpoint":
            _git_out(worktree, "remote", "set-url", "origin", str(worktree.parent / "unintended.git"))
        return result

    monkeypatch.setattr(delegate, "_finalize_remote_head", query)
    result = finalize(worktree)
    if uncertainty == "endpoint":
        assert result.ok and remote_head(origin) == head
        assert marker.read_text() == "observed"
    else:
        assert not result.ok
        assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


def test_upstream_binding_failure_keeps_published_commit_but_refuses_success(checkout, monkeypatch):
    worktree, origin, marker = checkout
    head = commit(worktree)
    real_run = delegate.subprocess.run

    def run(args, **kwargs):
        if args[:2] == ["git", "branch"]:
            return subprocess.CompletedProcess(args, 1, "", "upstream unavailable")
        return real_run(args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert result.ok and result.commit_sha == head == remote_head(origin)
    assert delegate._count_unpushed_commits(worktree, "codex/finalize") == 0
    assert marker.read_text() == "observed"


def test_reverted_unowned_commit_is_still_refused_before_publication(checkout):
    worktree, origin, marker = checkout
    head = commit(worktree)
    original = (worktree / "README.md").read_bytes()
    (worktree / "README.md").write_bytes(b"unowned intermediate bytes\r\n")
    _git_out(worktree, "add", "README.md")
    _git_out(worktree, "commit", "-m", "unowned intermediate commit")
    _git_out(worktree, "revert", "--no-edit", "HEAD")
    assert _git_out(worktree, "diff", head, "HEAD") == ""
    result = finalize(worktree)
    assert not result.ok and result.error == "auto_finalize_committed_scope_unowned"
    assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "README.md").read_bytes() == original
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


@pytest.mark.parametrize("failure", ["unknown_base", "error", "timeout"])
def test_unknown_committed_history_never_publishes(checkout, monkeypatch, failure):
    worktree, origin, marker = checkout
    head = commit(worktree)
    real_run = delegate.subprocess.run
    if failure == "unknown_base":
        monkeypatch.setattr(delegate, "_resolve_merge_base", lambda *_a, **_k: None)
        # Simulate independently unavailable history after the initial diff.
        monkeypatch.setattr(delegate, "_advisory_worker_diff", lambda *_a, **_k: ("artifact.txt\0", None))
    else:

        def run(args, **kwargs):
            if args[:2] == ["git", "log"]:
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(args, 30)
                return subprocess.CompletedProcess(args, 128, "", "history unavailable")
            return real_run(args, **kwargs)

        monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert not result.ok and result.error == "auto_finalize_committed_scope_unknown"
    assert remote_head(origin) is None and not marker.exists()
    assert delegate._resolve_sha(worktree) == head
    assert (worktree / "artifact.txt").read_bytes() == b"committed\r\n"


@pytest.mark.parametrize("case", ["clean", "dirty", "mixed"])
def test_finalizer_binds_the_callers_intended_commit_before_push(checkout, monkeypatch, case):
    worktree, origin, marker = checkout
    if case != "dirty":
        commit(worktree)
    if case != "clean":
        (worktree / "artifact.txt").write_bytes(b"current\x00\r\n")
    expected = (worktree / "artifact.txt").read_bytes()
    real_push = delegate._push_auto_finalize_branch
    intended = []

    def move_before_entry(path, branch, *, expected_head=None, **kwargs):
        intended.append(expected_head)
        _git_out(path, "commit", "--allow-empty", "-m", "movement before push helper entry")
        real_push(path, branch, expected_head=expected_head, **kwargs)

    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", move_before_entry)
    result = finalize(worktree)
    assert not result.ok and result.error == "auto_finalize_head_moved"
    assert result.commit_sha == intended[0] != delegate._resolve_sha(worktree)
    assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "artifact.txt").read_bytes() == expected


@pytest.mark.parametrize("step", ["add", "commit"])
def test_head_movement_during_dirty_finalization_never_publishes(checkout, monkeypatch, step):
    worktree, origin, marker = checkout
    commit(worktree)
    (worktree / "artifact.txt").write_bytes(b"current\x00\r\n")
    real_run = delegate.subprocess.run

    def run(args, **kwargs):
        if "--literal-pathspecs" in args and delegate._git_subcommand(args) == step:
            (worktree / "README.md").write_bytes(b"foreign concurrent commit\r\n")
            real_run(["git", "add", "README.md"], cwd=worktree, check=True, capture_output=True)
            real_run(
                ["git", "commit", "--only", "README.md", "-m", "concurrent writer"],
                cwd=worktree,
                check=True,
                capture_output=True,
            )
        return real_run(args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    result = finalize(worktree)
    assert not result.ok and result.error == "auto_finalize_head_moved"
    assert remote_head(origin) is None and not marker.exists()
    assert (worktree / "artifact.txt").read_bytes() == b"current\x00\r\n"
    assert (worktree / "README.md").read_bytes() == b"foreign concurrent commit\r\n"
