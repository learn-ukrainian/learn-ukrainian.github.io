"""#9878: Kimi finalize runs after the worker reaps its runtime temp root.

A delegate worker process runs with ``TMPDIR`` at its task's runtime lease,
and ``tempfile`` caches that root per process. The worker reaps the lease as
soon as its agent exits, then runs the Kimi content check and auto-finalize,
which create a scratch index with ``tempfile``. These tests reproduce that
order: the root is cached, reaped, and only then does finalize run.
"""

from __future__ import annotations

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
