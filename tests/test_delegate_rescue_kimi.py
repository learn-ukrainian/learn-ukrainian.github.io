"""#9878: ``delegate.py rescue`` preserves a terminal Kimi task's work past its worktree push block.

Real git: a primary repository with a bare ``origin``, and one linked Kimi
dispatch worktree carrying the boundary ``kimi_boundary.install`` sets up.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import kimi_boundary
from tests.test_delegate import (  # noqa: F401
    _fixture_worktree_lock_dir,
    _keep_delegate_unit_tests_local,
    _sanitize_git_env_for_test,
    tmp_tasks_dir,
)
from tests.test_kimi_coding_only_admission import _FAKE_TOKEN, HOSTILE_GIT_ERRORS, assert_no_host_details

pytestmark = pytest.mark.usefixtures("tmp_tasks_dir")

TASK_ID = "kimi-rescue"
BRANCH = f"kimi/{TASK_ID}"
RESCUE_REF = f"rescue/kimi/{delegate._x_agent_task_id('kimi', TASK_ID)}"
OWNED = "site/src/components/"
LABEL = "site/src/components/Label.tsx"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=60).stdout


def _git_proc(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True, timeout=60)


def _remote_heads(origin: Path) -> dict[str, str]:
    lines = _git(origin, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads").splitlines()
    return dict(line.split(" ", 1) for line in lines)


@pytest.fixture
def kimi_rescue(tmp_path, monkeypatch):
    """A failed Kimi task whose worktree holds the boundary; ``write(text, commit=...)`` leaves its work."""
    from scripts.orchestration import reap_worktrees

    _sanitize_git_env_for_test(monkeypatch)
    # These are real-Git mechanism tests, independent of a worker harness's
    # PATH shim (which rejects --no-verify for its own scanned pushes).
    monkeypatch.setenv("PATH", os.defpath)
    primary = tmp_path / "primary"
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(origin))
    _git(tmp_path, "init", "--initial-branch=main", str(primary))
    for key, value in (("user.email", "test@example.com"), ("user.name", "test"), ("commit.gpgsign", "false")):
        _git(primary, "config", key, value)
    (primary / "README.md").write_text("base\n", encoding="utf-8")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-m", "base")
    _git(primary, "remote", "add", "origin", str(origin))
    _git(primary, "push", "origin", "HEAD:refs/heads/main")
    worktree = primary / ".worktrees" / "dispatch" / "kimi" / TASK_ID
    worktree.parent.mkdir(parents=True)
    _git(primary, "worktree", "add", "-b", BRANCH, str(worktree), "HEAD")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary.resolve())
    monkeypatch.setattr(reap_worktrees, "_active_task_ids", lambda: set())
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _root: set())
    kimi_boundary.install(worktree, agent="kimi", base_ref="origin/main", owned_paths=[OWNED])
    state_path = delegate._state_path(TASK_ID)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": TASK_ID,
            "agent": "kimi",
            "status": "failed",
            "finished_at": "2020-01-01T00:00:00Z",
            "worktree_path": str(worktree.resolve()),
            "worktree_branch": BRANCH,
            "worktree_base": "main",
            "worktree_reused": False,
            "owned_paths": [OWNED],
        },
    )

    def write(text: str, *, commit: bool = False) -> None:
        label = worktree / LABEL
        label.parent.mkdir(parents=True, exist_ok=True)
        label.write_text(text, encoding="utf-8")
        if commit:
            _git(worktree, "add", "-A")
            _git(worktree, "commit", "--no-verify", "-m", "worker commit")

    return worktree.resolve(), origin, state_path, write


def _assert_push_block_intact(worktree: Path) -> None:
    assert kimi_boundary.is_installed(worktree)
    assert kimi_boundary.PUSH_BLOCK_URL in _git(worktree, "config", "--get-all", "remote.origin.pushurl").splitlines()
    proc = _git_proc(worktree, "push", "origin", "HEAD:refs/heads/worker-push")
    assert proc.returncode != 0 and "kimi-push-disabled" in proc.stderr


@pytest.mark.parametrize("committed", [False, True])
def test_rescue_pushes_clean_kimi_work_and_leaves_the_push_block_in_place(kimi_rescue, committed):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=committed)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _git(origin, "show", f"{RESCUE_REF}:{LABEL}") == "export const label = 'Lesson';\n"
    state = delegate._read_state(state_path)
    assert (state["rescue_ref"], state["rescue_status"]) == (RESCUE_REF, "rescued")
    _assert_push_block_intact(worktree)
    assert "worker-push" not in _remote_heads(origin)


def test_rescue_dry_run_reports_clean_kimi_work_without_pushing(kimi_rescue):
    _worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")

    result = delegate._rescue_task(state_path, apply=False)

    assert (result["action"], result["rescue_ref"]) == ("candidate", RESCUE_REF)
    assert RESCUE_REF not in _remote_heads(origin)


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("apply", [False, True])
def test_rescue_refuses_kimi_work_that_fails_the_content_check(kimi_rescue, committed, apply):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Урок';\n", commit=committed)
    head = _git(worktree, "rev-parse", "HEAD")
    status = _git(worktree, "status", "--porcelain")

    result = delegate._rescue_task(state_path, apply=apply)

    assert result["action"] == "error"
    assert result["failure_code"] == "kimi_content_refused"
    # #9878: the row names the typed cause; the refusal text, with its path, stays in the local .diag.
    assert result["reason"] == "kimi_content_refused"
    assert LABEL not in json.dumps(result)
    kept = delegate._diagnostic_path(TASK_ID).read_text(encoding="utf-8")
    assert "KIMI CODING-ONLY" in kept and LABEL in kept
    assert RESCUE_REF not in _remote_heads(origin)
    assert _git(worktree, "rev-parse", "HEAD") == head
    assert _git(worktree, "status", "--porcelain") == status
    assert delegate._read_state(state_path).get("rescue_ref") is None
    _assert_push_block_intact(worktree)


def test_rescue_checks_a_kimi_record_even_without_its_boundary(kimi_rescue):
    worktree, origin, state_path, write = kimi_rescue
    kimi_boundary.remove(worktree)
    write("export const label = 'Урок';\n")

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "kimi_content_refused")
    assert RESCUE_REF not in _remote_heads(origin)


def test_rescue_refuses_when_the_main_repository_push_url_is_blocked_too(kimi_rescue):
    worktree, origin, state_path, write = kimi_rescue
    _git(worktree, "config", "remote.origin.pushurl", kimi_boundary.PUSH_BLOCK_URL)  # the shared config
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "error"
    assert result["reason"] == "rescue_push_url_unavailable, git config"
    kept = delegate._diagnostic_path(TASK_ID).read_text(encoding="utf-8")
    assert "main repository has no single usable push URL for origin" in kept
    assert RESCUE_REF not in _remote_heads(origin)


def test_rescue_ignores_a_push_url_the_kimi_worktree_set_for_itself(kimi_rescue, tmp_path):
    """The canonical URL comes from the main repository, never the worker's worktree-scoped config."""
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--worktree", "remote.origin.url", str(decoy))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


# --- #9878 review probes: rescue runs nothing the worker's worktree configured ---------------


def _seat(kimi_rescue, seat: str) -> str:
    """Make the fixture's task a ``seat`` task; the rescue ref it gets."""
    worktree, _origin, state_path, _write = kimi_rescue
    if seat != "kimi":
        kimi_boundary.remove(worktree)
        state = delegate._read_state(state_path)
        delegate._write_state_atomic(state_path, {**state, "agent": seat})
    return f"rescue/{seat}/{delegate._x_agent_task_id(seat, TASK_ID)}"


def _worktree_hooks(worktree: Path, tmp_path: Path) -> Path:
    """A worktree-scoped ``core.hooksPath``: every hook leaves a marker; pre-commit also swaps in Cyrillic."""
    hooks = tmp_path / "worker-hooks"
    hooks.mkdir()
    marker = tmp_path / "hook-ran"
    swap = f"printf \"export const label = 'Урок';\\n\" > {LABEL}\ngit add {LABEL}\n"
    for name in ("pre-commit", "commit-msg", "post-commit", "pre-push", "post-checkout", "reference-transaction"):
        hook = hooks / name
        hook.write_text(f"#!/bin/sh\necho {name} >> '{marker}'\n{swap if name == 'pre-commit' else ''}exit 0\n")
        hook.chmod(0o755)
    _git(worktree, "config", "--worktree", "core.hooksPath", str(hooks))
    return marker


def _worker_snapshot(worktree: Path) -> tuple[bytes, str, str, bytes]:
    """The worker's index, HEAD, branch and changed file, read without letting git rewrite the index."""
    index = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "index").strip())
    return (
        index.read_bytes(),
        _git(worktree, "rev-parse", "HEAD"),
        _git(worktree, "symbolic-ref", "HEAD"),
        (worktree / LABEL).read_bytes(),
    )


def _registered_worktrees(worktree: Path) -> list[str]:
    return [
        line for line in _git(worktree, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")
    ]


@pytest.mark.parametrize("seat", ["kimi", "cursor"])
@pytest.mark.parametrize("committed", [False, True])
def test_rescue_runs_no_hook_of_the_worker_worktree(kimi_rescue, tmp_path, committed, seat):
    worktree, origin, state_path, write = kimi_rescue
    rescue_ref = _seat(kimi_rescue, seat)
    write("export const label = 'Lesson';\n", commit=committed)
    marker = _worktree_hooks(worktree, tmp_path)
    before, registered = _worker_snapshot(worktree), _registered_worktrees(worktree)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert not marker.exists(), marker.read_text()
    assert _remote_heads(origin)[rescue_ref] == result["head"]
    assert _git(origin, "show", f"{rescue_ref}:{LABEL}") == "export const label = 'Lesson';\n"
    assert _worker_snapshot(worktree) == before  # rescue never writes the worker's worktree
    assert _registered_worktrees(worktree) == registered  # the publish worktree is gone
    if seat == "kimi":
        _assert_push_block_intact(worktree)


@pytest.mark.parametrize("committed", [False, True])
def test_a_worktree_url_rewrite_receives_nothing(kimi_rescue, tmp_path, committed):
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--worktree", f"url.{decoy}.insteadOf", str(origin))
    write("export const label = 'Lesson';\n", commit=committed)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


def test_a_url_rewrite_cannot_fake_the_remote_verification(kimi_rescue, tmp_path):
    """A rewrite the push itself follows (shared configuration) still fails the neutral ``ls-remote`` proof."""
    _worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(tmp_path / "primary", "config", f"url.{decoy}.insteadOf", str(origin))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "rescue_remote_unverified"), result
    assert result["reason"] == "rescue_remote_unverified, git ls-remote"
    assert RESCUE_REF not in _remote_heads(origin)
    assert delegate._read_state(state_path).get("rescue_ref") is None


def test_a_repeated_rescue_of_the_same_uncommitted_work_is_already_rescued(kimi_rescue):
    _worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    first = delegate._rescue_task(state_path, apply=True)

    again = delegate._rescue_task(state_path, apply=True)

    assert first["action"] == "rescued", first
    assert again == {"task_id": TASK_ID, "action": "skipped", "reason": "already rescued at HEAD"}
    assert _remote_heads(origin)[RESCUE_REF] == first["head"]


# --- #9878: a rescue row carries only the typed cause; git's error stays in the local .diag ----------

# The kinds git reports for a remote it never reached.
_UNREACHABLE = {"dns_hostname", "ssh_dns_hostname", "ipv6_interface"}


def _fail_rescue_git(monkeypatch, subcommand: str, stderr: str) -> None:
    """Every rescue ``git <subcommand>`` exits 128 with ``stderr``; the argv carries the host paths git saw."""
    real_git = delegate._rescue_git

    def failing(cwd, *args, **kwargs):
        if args and args[0] == subcommand:
            argv = ["git", *kwargs.get("git_options", ()), *args]
            return subprocess.CompletedProcess(argv, 128, "", stderr)
        return real_git(cwd, *args, **kwargs)

    monkeypatch.setattr(delegate, "_rescue_git", failing)


def _assert_kept_locally(task_id: str, stderr: str, code: str) -> None:
    lines = delegate._diagnostic_path(task_id).read_text(encoding="utf-8").splitlines()
    (entry,) = (json.loads(line) for line in lines)
    assert (entry["source"], entry["code"]) == ("rescue", code)
    if _FAKE_TOKEN in stderr:
        assert _FAKE_TOKEN not in entry["diagnostic"] and "Authentication failed for" in entry["diagnostic"]
    else:
        assert stderr.splitlines()[0] in entry["diagnostic"]


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_push_error_row_carries_only_its_typed_cause(kimi_rescue, monkeypatch, capsys, kind):
    worktree, origin, _state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    registered = _registered_worktrees(worktree)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "push", stderr)
    code = "remote_unreachable" if kind in _UNREACHABLE else "rescue_push_failed"

    assert delegate.cmd_rescue(argparse.Namespace(task_id=TASK_ID, all_stale=False, older_than=None, apply=True)) == 1
    summary = capsys.readouterr().out
    (result,) = json.loads(summary)["tasks"]

    assert (result["action"], result["failure_code"]) == ("error", code)
    assert result["reason"] == f"{code}, git push, exit 128"
    assert result["diagnostic"].endswith(f"{TASK_ID}.diag")
    assert_no_host_details(summary, worktree, origin)
    assert "fatal:" not in summary and "Could not" not in summary
    _assert_kept_locally(TASK_ID, stderr, code)
    assert RESCUE_REF not in _remote_heads(origin)
    assert _registered_worktrees(worktree) == registered


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_remote_query_error_row_carries_only_its_typed_cause(kimi_rescue, monkeypatch, apply, kind):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "ls-remote", stderr)
    code = "remote_unreachable" if kind in _UNREACHABLE else "rescue_remote_unverified"

    result = delegate._rescue_task(state_path, apply=apply)

    assert (result["action"], result["failure_code"]) == ("error", code)
    assert result["reason"] == f"{code}, git ls-remote, exit 128"
    assert_no_host_details(json.dumps(result), worktree, origin)
    _assert_kept_locally(TASK_ID, stderr, code)


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_kimi_check_that_cannot_read_the_changes_refuses_with_its_typed_cause(kimi_rescue, monkeypatch, kind):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "diff-tree", stderr)

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "kimi_content_refused")
    assert result["reason"] == "kimi_content_refused; diff_command_failed, git diff-tree, exit 128"
    assert_no_host_details(json.dumps(result, ensure_ascii=False), worktree, origin)
    _assert_kept_locally(TASK_ID, stderr, "diff_command_failed")
    assert RESCUE_REF not in _remote_heads(origin)


def test_an_unexpected_rescue_exception_is_typed_by_its_class(kimi_rescue, monkeypatch):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)

    def unreachable_mount(*_args, **_kwargs):
        raise OSError(f"cannot stat {HOSTILE_GIT_ERRORS['home_relative_mount']}")

    monkeypatch.setattr(delegate, "_rescue_canonical_push_url", unreachable_mount)
    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "rescue_step_failed")
    assert result["reason"] == "rescue_step_failed, OSError"
    assert_no_host_details(json.dumps(result), worktree, origin)
    _assert_kept_locally(TASK_ID, "cannot stat", "rescue_step_failed")


@pytest.mark.parametrize("contents", ["empty", "nonempty", "symlink", "replacement"])
def test_failed_publish_add_keeps_its_cause_and_only_removes_its_empty_directory(
    kimi_rescue, monkeypatch, contents
):
    worktree, _origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    repo = delegate._rescue_repo(worktree)
    registered = repo.git("worktree", "list", "--porcelain").stdout
    real_git = delegate._rescue_git
    created = []
    removals = []
    stderr = "fatal: synthetic worktree add failure"

    def fail_add(cwd, *args, **kwargs):
        if args[:2] == ("worktree", "add"):
            path = Path(args[-2])
            assert path.is_dir() and not list(path.iterdir())
            created.append(path)
            if contents == "nonempty":
                (path / "keep.txt").write_text("retain\n")
            elif contents in {"symlink", "replacement"}:
                original = path.with_name(path.name + "-original")
                path.rename(original)
                if contents == "symlink":
                    path.symlink_to(original, target_is_directory=True)
                else:
                    path.mkdir()
            return subprocess.CompletedProcess(["git", *args], 128, "", stderr)
        return real_git(cwd, *args, **kwargs)

    real_remove = delegate.worktree_claims.remove_unclaimed_worktree

    def record_removal(path, **kwargs):
        removals.append(path)
        return real_remove(path, **kwargs)

    monkeypatch.setattr(delegate, "_rescue_git", fail_add)
    monkeypatch.setattr(delegate.worktree_claims, "remove_unclaimed_worktree", record_removal)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["reason"] == "rescue_publish_worktree_failed, git worktree, exit 128", result
    assert result["action"] == "error"
    _assert_kept_locally(TASK_ID, stderr, "rescue_publish_worktree_failed")
    assert not removals  # A directory from a failed add is never a removal target.
    (path,) = created
    if contents == "empty":
        assert not path.exists()
    elif contents == "nonempty":
        assert (path / "keep.txt").read_text() == "retain\n"
    else:
        assert path.is_dir()
        assert path.is_symlink() == (contents == "symlink")
        assert path.with_name(path.name + "-original").is_dir()
    assert repo.git("worktree", "list", "--porcelain").stdout == registered


@pytest.mark.parametrize("scope", ["--local", "--worktree"])
def test_rescue_create_checkout_push_probe_and_removal_run_no_configured_programs(
    kimi_rescue, tmp_path, monkeypatch, scope
):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    marker = tmp_path / "cleanup-program-ran"
    hooks = tmp_path / "cleanup-hooks"
    hooks.mkdir()
    for name in ("post-checkout", "post-index-change", "fsmonitor", "pre-push", "reference-transaction"):
        program = hooks / name
        program.write_text(f"#!/bin/sh\necho {name} >> '{marker}'\nexit 0\n")
        program.chmod(0o755)
    # Shared settings configured by a worker also apply in a fresh publish tree.
    _git(worktree, "config", scope, "core.hooksPath", str(hooks))
    _git(worktree, "config", scope, "core.fsmonitor", str(hooks / "fsmonitor"))
    real_git = delegate._rescue_git

    def configure_publish(cwd, *args, **kwargs):
        proc = real_git(cwd, *args, **kwargs)
        if scope == "--worktree" and args[:2] == ("worktree", "add") and proc.returncode == 0:
            publish = Path(args[-2])
            _git(publish, "config", scope, "core.hooksPath", str(hooks))
            _git(publish, "config", scope, "core.fsmonitor", str(hooks / "fsmonitor"))
        return proc

    monkeypatch.setattr(delegate, "_rescue_git", configure_publish)
    repo = delegate._rescue_repo(worktree)
    registered = repo.git("worktree", "list", "--porcelain").stdout

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert not marker.exists(), marker.read_text()
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert repo.git("worktree", "list", "--porcelain").stdout == registered
    assert not list(worktree.parent.glob(f"{worktree.name}.rescue-*"))


def test_rescue_publish_tree_uses_driver_private_tmp(kimi_rescue, monkeypatch):
    worktree, _origin, _state_path, _write = kimi_rescue
    worker_tmp = worktree / "worker-tmp"
    worker_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(worker_tmp))
    repo = delegate._rescue_repo(worktree)
    head, _branch = delegate._rescue_head(repo)
    registered = repo.git("worktree", "list", "--porcelain").stdout

    with delegate._rescue_publish_worktree(repo, head) as publish:
        assert publish.parent == delegate._REPO_ROOT / "batch_state" / "tmp"
        assert not publish.is_relative_to(worktree.parent)
        assert not publish.is_relative_to(worker_tmp)
        assert stat.S_IMODE(publish.lstat().st_mode) == 0o700

    assert not publish.exists()
    assert repo.git("worktree", "list", "--porcelain").stdout == registered


@pytest.mark.parametrize("stage", ["before_add", "after_add", "before_removal"])
@pytest.mark.parametrize("nonempty", [False, True])
def test_rescue_publish_symlink_swap_never_touches_target(kimi_rescue, tmp_path, monkeypatch, stage, nonempty):
    worktree, _origin, _state_path, _write = kimi_rescue
    repo = delegate._rescue_repo(worktree)
    head, _branch = delegate._rescue_head(repo)
    target = tmp_path / "swap-target"
    target.mkdir()
    if nonempty:
        (target / "canary").write_bytes(b"retain\n")
    target_identity = target.lstat()
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    paths = []
    removals = []

    def swap(path):
        paths.append(path)
        path.rename(path.with_name(path.name + "-original"))
        path.symlink_to(target, target_is_directory=True)

    real_mkdtemp = delegate.tempfile.mkdtemp

    def create_swapped(*args, **kwargs):
        path = Path(real_mkdtemp(*args, **kwargs))
        swap(path)
        return str(path)

    real_git = delegate._rescue_git

    def add_then_swap(cwd, *args, **kwargs):
        proc = real_git(cwd, *args, **kwargs)
        if args[:2] == ("worktree", "add") and proc.returncode == 0:
            swap(Path(args[-2]))
        return proc

    real_remove = delegate.worktree_claims.remove_unclaimed_worktree

    def record_removal(path, **kwargs):
        removals.append(path)
        return real_remove(path, **kwargs)

    if stage == "before_add":
        monkeypatch.setattr(delegate.tempfile, "mkdtemp", create_swapped)
    elif stage == "after_add":
        monkeypatch.setattr(delegate, "_rescue_git", add_then_swap)
    monkeypatch.setattr(delegate.worktree_claims, "remove_unclaimed_worktree", record_removal)

    with pytest.raises(delegate._RescueFailure) as failure:
        with delegate._rescue_publish_worktree(repo, head) as publish:
            if stage == "before_removal":
                swap(publish)
            else:
                pytest.fail("a replaced publish directory must never be yielded")

    assert failure.value.cause.public() == "rescue_publish_path_changed"
    assert not removals
    assert target.is_dir()
    assert (target.lstat().st_dev, target.lstat().st_ino) == (target_identity.st_dev, target_identity.st_ino)
    assert {p.name: p.read_bytes() for p in target.iterdir()} == before
    assert paths[0].is_symlink()
