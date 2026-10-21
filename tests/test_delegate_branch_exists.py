"""#9874: --branch continues a canonical remote branch, never creates one."""

from __future__ import annotations

import subprocess

import pytest

from tests.test_authoring_review_feasibility import delegate, mini_repo


@pytest.fixture
def branch_repo(tmp_path, monkeypatch):
    repo = mini_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.chdir(repo.root)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    return repo


def _argv(*, branch="feature", agent="codex", mode="workspace-write"):
    return [
        "dispatch",
        "--agent",
        agent,
        "--task-id",
        "branch-exists",
        "--initiator",
        "codex",
        "--mode",
        mode,
        "--branch",
        branch,
        "--prompt",
        "Implement the fix.",
        "--owned-path",
        "site/src/components/Status.tsx",
    ]


def _forbid_admission(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("missing branch reached admission or provider routing")

    for name in ("_kimi_dispatch_gate", "_dispatch_route", "_authoring_review_admission"):
        monkeypatch.setattr(delegate, name, forbidden)
    monkeypatch.setattr(delegate.dispatch_isolation, "spawn_detached_worker", forbidden)


@pytest.mark.parametrize("agent", ["codex", "kimi"])
@pytest.mark.parametrize("branch", ["absent", "feature"])
def test_absent_or_local_only_branch_refuses_before_admission(branch_repo, monkeypatch, capsys, agent, branch):
    # feature exists locally; neither name is served by the canonical remote.
    _forbid_admission(monkeypatch)
    before = branch_repo.snapshot()
    assert delegate.main(_argv(branch=branch, agent=agent)) == 2
    err = capsys.readouterr().err
    assert err.count("DISPATCH_BRANCH_NOT_FOUND:") == 1
    assert "does not exist on the canonical remote" in err
    assert "--branch continues an existing remote branch" in err
    assert "omit --branch (default: <agent>/<task-id>), optionally with --base" in err
    assert "KIMI CODING-ONLY" not in err and "AUTHORING_REVIEW" not in err
    assert branch_repo.snapshot() == before


@pytest.mark.parametrize("mode", ["workspace-write", "danger", "read-only"])
def test_existing_remote_branch_reaches_unchanged_admission(branch_repo, monkeypatch, mode):
    branch_repo.publish()

    class ReachedAdmission(Exception):
        pass

    def admitted(*_args, **_kwargs):
        raise ReachedAdmission

    monkeypatch.setattr(delegate, "_kimi_dispatch_gate", admitted)
    with pytest.raises(ReachedAdmission):
        delegate.main(_argv(mode=mode))


def test_canonical_remote_wins_over_origin_mirror(branch_repo, monkeypatch, capsys, tmp_path):
    branch_repo.publish()
    branch_repo.git("remote", "rename", "origin", "github")
    mirror = tmp_path / "mirror.git"
    branch_repo.git("init", "-q", "--bare", str(mirror))
    branch_repo.git("remote", "add", "origin", str(mirror))
    _forbid_admission(monkeypatch)
    # The branch is present only in the stale mirror, not the canonical remote.
    branch_repo.publish(to="mirror-only", remote=mirror)
    assert delegate.main(_argv(branch="mirror-only")) == 2
    assert "DISPATCH_BRANCH_NOT_FOUND:" in capsys.readouterr().err


def test_remote_read_failure_is_not_branch_absence(branch_repo, monkeypatch, capsys, tmp_path):
    _forbid_admission(monkeypatch)
    branch_repo.git("remote", "set-url", "origin", str(tmp_path / "unreachable.git"))
    assert delegate.main(_argv()) == 2
    err = capsys.readouterr().err
    assert "DISPATCH_BRANCH_REMOTE_READ_FAILED:" in err
    assert "git ls-remote) failed (exit 128)" in err
    assert "DISPATCH_BRANCH_NOT_FOUND" not in err
    assert str(tmp_path) not in err


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired(["git"], 1), OSError("private detail")])
def test_strict_remote_read_preserves_unknown_failure(branch_repo, monkeypatch, failure):
    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(delegate.subprocess, "run", fail)
    with pytest.raises(delegate._AuthoringObservationUnknown, match=r"timed out|could not run"):
        delegate._ls_remote_branch_sha("origin", "feature", strict=True)
    assert delegate._ls_remote_branch_sha("origin", "feature") is None


def test_initial_authoring_head_reuses_observed_remote_sha(branch_repo, monkeypatch):
    head = branch_repo.publish()

    def forbidden(*_args, **_kwargs):
        pytest.fail("initial admission repeated the canonical remote read")

    monkeypatch.setattr(delegate, "_ls_remote_branch_sha", forbidden)
    assert (
        delegate._authoring_attach_head(
            kind="existing-branch",
            checkout=None,
            branch="feature",
            pinned_head=None,
            remote="origin",
            observed_branch_head=head,
        )
        == head
    )


def test_branch_help_explains_continue_only_semantics(capsys):
    with pytest.raises(SystemExit) as exited:
        delegate.main(["dispatch", "--help"])
    assert exited.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "Continue an existing remote branch, e.g. codex/fix-123" in help_text
    assert "For a new branch omit --branch (default: <agent>/<task-id>), optionally with --base" in help_text
