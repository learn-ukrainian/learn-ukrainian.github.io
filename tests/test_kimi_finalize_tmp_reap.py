"""#9878: Kimi finalize runs after the worker reaps its runtime temp root.

A delegate worker process runs with ``TMPDIR`` at its task's runtime lease,
and ``tempfile`` caches that root per process. The worker reaps the lease as
soon as its agent exits, then runs the Kimi content check and auto-finalize,
which create a scratch index with ``tempfile``. These tests reproduce that
order: the root is cached, reaped, and only then does finalize run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

# Autouse fixtures of the delegate unit suite that keep a ``_run_worker`` hermetic; its
# ``_fixture_runtime_tmp_root`` is left out on purpose, since it replaces the temp root under test.
from tests.test_delegate import (  # noqa: F401
    _agy_dispatch_worktree,
    _bg_mock_result,
    _fixture_worktree_lock_dir,
    _git_out,
    _keep_delegate_unit_tests_local,
    _review_target_from_fixture_refs,
    _sanitize_git_env_for_test,
    _stub_node_modules_integrity_sweep,
    _stub_primary_integrity_sweep,
    _stub_venv_integrity_sweep,
    _stub_worktree_cleanup_integrity_sweep,
    _worktree_add_via_run,
    tmp_tasks_dir,
)
from tests.test_kimi_coding_only_admission import _FAKE_TOKEN, HOSTILE_GIT_ERRORS, assert_no_host_details

pytestmark = pytest.mark.usefixtures("tmp_tasks_dir")


@pytest.fixture
def worker_tmp_lease(tmp_path, monkeypatch):
    """This process as a delegate worker: ``TMPDIR`` at a real runtime lease, cached by ``tempfile``."""
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    lease, namespace = delegate._create_runtime_tmp_lease("kimi-tmp-reap")
    monkeypatch.setenv("TMPDIR", str(lease))
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(lease))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(namespace.parent))
    monkeypatch.setattr(tempfile, "tempdir", None)
    assert tempfile.gettempdir() == str(lease)  # cached for the rest of the process
    return lease, namespace


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=30).stdout


@pytest.fixture
def clean_kimi_worktree(tmp_path, monkeypatch):
    """A worktree whose uncommitted and untracked changes hold no Ukrainian content."""
    _sanitize_git_env_for_test(monkeypatch)
    repo = tmp_path / "wt"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=kimi/task")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "legacy.py").write_text("GREETING = 'hi'\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "base")
    _git(repo, "branch", "base")
    (repo / "Button.tsx").write_text("export const Button = () => null;\n", encoding="utf-8")
    (repo / "legacy.py").write_text("GREETING = 'hello'\n", encoding="utf-8")
    return repo


def test_the_kimi_content_check_reads_the_changes_after_the_worker_reaps_its_tmp_root(
    worker_tmp_lease, clean_kimi_worktree
):
    lease, namespace = worker_tmp_lease

    reap = delegate._reap_runtime_tmp_lease(lease, namespace)

    assert reap["tmp_reap_error"] is None
    assert not lease.exists()
    assert delegate._kimi_diff_refusal(clean_kimi_worktree, "base", "kimi") is None
    assert delegate._auto_finalize_additions_deletions(clean_kimi_worktree) == (("Button.tsx",), ())


def test_the_reaped_process_and_its_children_get_a_live_tmp_root(worker_tmp_lease):
    lease, namespace = worker_tmp_lease

    delegate._reap_runtime_tmp_lease(lease, namespace)

    assert Path(tempfile.gettempdir()) == namespace.parent.resolve()
    assert os.environ["TMPDIR"] == str(namespace.parent.resolve())
    assert "LU_RUNTIME_TMP_ROOT" not in os.environ
    # A child process (a git hook's mktemp, gh) inherits a root that exists.
    child = subprocess.run(
        ["sh", "-c", 'mktemp "$TMPDIR/lu-child.XXXXXX"'], capture_output=True, text=True, check=True, timeout=30
    )
    created = Path(child.stdout.strip())
    assert created.is_file()
    created.unlink()


def test_a_failed_reap_keeps_the_live_lease_as_the_tmp_root(worker_tmp_lease, monkeypatch):
    lease, namespace = worker_tmp_lease

    def fail_rmtree(*_args, **_kwargs):
        raise OSError("permission denied")

    fail_rmtree.avoids_symlink_attacks = True
    monkeypatch.setattr(delegate.shutil, "rmtree", fail_rmtree)

    reap = delegate._reap_runtime_tmp_lease(lease, namespace)

    assert "permission denied" in str(reap["tmp_reap_error"])
    assert lease.is_dir()
    assert tempfile.gettempdir() == str(lease)
    assert os.environ["TMPDIR"] == str(lease)
    assert os.environ["LU_RUNTIME_TMP_ROOT"] == str(lease)


def test_a_parent_reaping_a_child_lease_keeps_its_own_tmp_root(tmp_path, monkeypatch):
    """Only the worker's own binding moves; a dispatcher reaping a child's lease is untouched."""
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    own_tmp = tmp_path / "own-tmp"
    own_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(own_tmp))
    monkeypatch.setattr(tempfile, "tempdir", None)
    lease, namespace = delegate._create_runtime_tmp_lease("child-task")

    reap = delegate._reap_runtime_tmp_lease(lease, namespace)

    assert reap["tmp_reap_error"] is None
    assert not lease.exists()
    assert tempfile.gettempdir() == str(own_tmp)
    assert os.environ["TMPDIR"] == str(own_tmp)


def test_a_kimi_write_dispatch_that_used_tempfile_finalizes_after_the_reap(tmp_path, monkeypatch, worker_tmp_lease):
    """AC-00 end to end: the worker caches and uses its temp root, the root is reaped, finalize still delivers."""
    from scripts.agent_runtime import kimi_boundary

    _sanitize_git_env_for_test(monkeypatch)
    lease, namespace = worker_tmp_lease
    task_id = "kimi-tmp-reap"
    branch = f"kimi/{task_id}"
    worktree = _agy_dispatch_worktree(tmp_path, branch)
    label = worktree / "site" / "src" / "components" / "Label.tsx"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "cli_version": "test",
            "worktree_path": str(worktree),
            "worktree_branch": branch,
            "worktree_base": "main",
            "owned_paths": ["site/src/components/"],
            "keep_worktree": True,
        },
    )
    worker_saw: dict[str, object] = {}

    def worker(*_args, **_kwargs):
        with tempfile.NamedTemporaryFile("w") as scratch:  # the worker uses its temp root
            worker_saw["tmp"] = scratch.name
        label.parent.mkdir(parents=True, exist_ok=True)
        label.write_text("export const t = 'Lesson';\n", encoding="utf-8")
        return _bg_mock_result("")

    monkeypatch.setattr(delegate, "_count_unpushed_commits", lambda *_a: 0)
    with patch("agent_runtime.runner.invoke", side_effect=worker):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="kimi",
            prompt="Implement the label.",
            mode="workspace-write",
            cwd_str=str(worktree),
            model=None,
            hard_timeout=60,
            effort=None,
            keep_worktree=True,
            runtime_tmp_root=str(lease),
            runtime_tmp_namespace_root=str(namespace),
        )

    state = delegate._read_state(state_path)
    assert Path(str(worker_saw["tmp"])).parent == lease
    assert not lease.exists()
    assert state["tmp_reap_error"] is None
    assert state.get("kimi_content_refusal") is None, state.get("kimi_content_refusal")
    assert state["auto_finalize"]["ok"] is True, state["auto_finalize"]
    assert state["status"] == "done"
    assert rc == 0
    assert _git_out(worktree, "show", "--name-only", "--format=", "HEAD").split() == ["site/src/components/Label.tsx"]
    assert f"refs/heads/{branch}" in _git_out(worktree, "ls-remote", "--heads", "origin").split()
    assert not kimi_boundary.is_installed(worktree)


# --- #9878: a refused finalize exposes only its typed cause; git's error stays in the local .diag ----


def _kimi_dispatch_record(tmp_path: Path, task_id: str) -> tuple[Path, Path, Path]:
    """A Kimi write dispatch worktree and its task record: ``(worktree, label, state_path)``."""
    branch = f"kimi/{task_id}"
    worktree = _agy_dispatch_worktree(tmp_path, branch)
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "cli_version": "test",
            "worktree_path": str(worktree),
            "worktree_branch": branch,
            "worktree_base": "main",
            "owned_paths": ["site/src/components/"],
            "keep_worktree": True,
        },
    )
    return worktree, worktree / "site" / "src" / "components" / "Label.tsx", state_path


def _diagnostics(task_id: str) -> list[dict]:
    path = delegate._diagnostic_path(task_id)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_kimi_finalize_refusal_exposes_its_typed_cause_and_keeps_git_s_error_local(
    tmp_path, monkeypatch, worker_tmp_lease, kind
):
    _sanitize_git_env_for_test(monkeypatch)
    lease, namespace = worker_tmp_lease
    task_id = f"kimi-refusal-{kind.replace('_', '-')}"
    worktree, label, state_path = _kimi_dispatch_record(tmp_path, task_id)
    stderr = HOSTILE_GIT_ERRORS[kind]
    real_run = subprocess.run

    def run(cmd, *args, **kwargs):
        if list(cmd) == ["git", "add", "-A", "--intent-to-add"]:
            return subprocess.CompletedProcess(cmd, 128, "", stderr)
        return real_run(cmd, *args, **kwargs)

    def worker(*_args, **_kwargs):
        label.parent.mkdir(parents=True, exist_ok=True)
        label.write_text("export const t = 'Lesson';\n", encoding="utf-8")
        return _bg_mock_result("")

    monkeypatch.setattr(delegate, "_count_unpushed_commits", lambda *_a: 0)
    monkeypatch.setattr(delegate.subprocess, "run", run)
    with patch("agent_runtime.runner.invoke", side_effect=worker):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="kimi",
            prompt="Implement the label.",
            mode="workspace-write",
            cwd_str=str(worktree),
            model=None,
            hard_timeout=60,
            effort=None,
            keep_worktree=True,
            runtime_tmp_root=str(lease),
            runtime_tmp_namespace_root=str(namespace),
        )

    state = delegate._read_state(state_path)
    assert rc != 0 and state["status"] == "failed"
    # #9878: the record's reason fields are public causes only.
    assert state["kimi_content_refusal"] == "kimi_content_refused; temp_index_failed, git add, exit 128"
    assert state["last_error"] == state["kimi_content_refusal"]
    # Nothing the task record, its result or the Monitor can show carries git's error.
    exposed = json.dumps(state, ensure_ascii=False)
    result_path = state_path.with_suffix(".result")
    if result_path.exists():
        exposed += result_path.read_text(encoding="utf-8")
    assert_no_host_details(exposed)
    assert "Could not resolve" not in exposed and "fatal:" not in exposed
    # The local diagnostic keeps it, credentials redacted.
    (entry,) = [entry for entry in _diagnostics(task_id) if entry["source"] == "finalize"]
    assert (entry["field"], entry["code"]) == ("kimi_content_refusal", "temp_index_failed")
    assert "could not be read for Ukrainian content" in entry["diagnostic"]  # the refusal text, kept locally
    assert entry["public"] == "temp_index_failed, git add, exit 128"
    if kind == "credential_url":
        assert _FAKE_TOKEN not in entry["diagnostic"] and "Authentication failed for" in entry["diagnostic"]
    else:
        assert stderr.splitlines()[0] in entry["diagnostic"]
    assert _git_out(worktree, "status", "--porcelain").strip()  # nothing was committed for the worker


def test_a_diagnostic_is_written_only_beside_an_existing_task_record():
    cause = delegate._TypedCause("rescue_push_failed", "push", 128, diagnostic=HOSTILE_GIT_ERRORS["credential_url"])

    assert delegate._record_diagnostic("no-such-task", cause, source="rescue") is None
    assert not delegate._diagnostic_path("no-such-task").exists()

    delegate._write_state_atomic(delegate._state_path("has-record"), {"task_id": "has-record"})
    pointer = delegate._record_diagnostic("has-record", cause, source="rescue")

    assert pointer is not None and not Path(pointer).is_absolute() and pointer.endswith("has-record.diag")
    assert_no_host_details(pointer)
    (entry,) = _diagnostics("has-record")
    assert entry["public"] == "rescue_push_failed, git push, exit 128"
    assert "Authentication failed for" in entry["diagnostic"] and _FAKE_TOKEN not in entry["diagnostic"]


def test_force_new_archives_the_diagnostic_with_its_record():
    delegate._write_state_atomic(delegate._state_path("archived"), {"task_id": "archived", "status": "failed"})
    delegate._record_diagnostic("archived", delegate._TypedCause("rescue_step_failed"), source="rescue")
    diagnostic = delegate._diagnostic_path("archived")
    rotated = diagnostic.with_name(diagnostic.name + delegate._DIAG_ROTATED_SUFFIX)
    rotated.write_text("", encoding="utf-8")

    archived = delegate._archive_task_artifacts("archived", stamp="20260101T000000Z")

    assert not diagnostic.exists() and not rotated.exists()
    assert any(path.name.endswith(".archived.diag") for path in archived), archived
    assert any(path.name.endswith(".archived.prev") for path in archived), archived
