"""Tests for read-only dispatch checkout mutation guard (#7124).

Dedicated test module to keep CI fastlane slim and avoid pulling heavy
dependencies from tests/test_delegate.py.

- Scoping read-only snapshot off .worktrees/ entirely
- Preserving real worker failures alongside read-only mutation diagnostics
- Negative returncode signal decoding
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import agent_runtime.runner as runner
import delegate


def _sanitize_git_env_for_test(monkeypatch) -> None:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def _init_git_repo_for_test(path: Path, monkeypatch) -> None:
    _sanitize_git_env_for_test(monkeypatch)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, timeout=30)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=path,
        check=True,
        capture_output=True,
        timeout=30,
    )


def _seed_read_only_checkout_fixture(repo: Path, monkeypatch) -> None:
    """Git repo with production-shaped ignore rules + one tracked file."""
    _init_git_repo_for_test(repo, monkeypatch)
    entire = repo / ".entire"
    entire.mkdir(parents=True, exist_ok=True)
    (entire / ".gitignore").write_text(
        "tmp/\nsettings.local.json\nmetadata/\nlogs/\nredactors/local/\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text(
        ".agent/\n"
        "batch_state/\n"
        ".pytest_cache/\n"
        ".pytest_breadcrumbs/\n"
        ".ruff_cache/\n"
        "__pycache__/\n"
        ".runtime/\n"
        "*.sqlite3-wal\n"
        "*.sqlite3-shm\n"
        "*.sqlite3-journal\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", ".entire/.gitignore", ".gitignore", "tracked.txt"],
        cwd=repo,
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )


def _finalize_mock_result():
    return type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "grok-4.6",
            "effort": "high",
            "cli_version": "0.2.111",
        },
    )()


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    return tasks_dir


def test_read_only_snapshot_excluded_path_classification():
    """#7124: every ``.worktrees/`` path is out of snapshot scope."""
    assert delegate._is_read_only_snapshot_excluded_path(".worktrees")
    assert delegate._is_read_only_snapshot_excluded_path(".worktrees/dispatch/other-lane/other-task/scripts/foo.py")
    assert delegate._is_read_only_snapshot_excluded_path("./.worktrees/dispatch/a/b/")
    assert not delegate._is_read_only_snapshot_excluded_path("tracked.txt")
    assert not delegate._is_read_only_snapshot_excluded_path("sub/.worktrees/file")
    assert not delegate._is_read_only_snapshot_excluded_path(".worktreesish/file")


def test_real_delegate_snapshot_sidecar_is_runtime_state_via_batch_state(tmp_path, monkeypatch):
    """#7208: real sidecars under batch_state/tasks/<task>.snapshots/ are exempt.

    Sidecars are built from ``_TASKS_DIR`` (``batch_state/tasks``), so the
    existing ``batch_state`` runtime-state dir-name check covers them.
    Suite isolation points ``_TASKS_DIR`` at a temp store (#8654); this test
    owns a tmp repo whose ``batch_state/tasks`` is that directory.
    """
    repo = tmp_path / "repo"
    tasks_dir = repo / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True)
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    abs_path = delegate._read_only_snapshot_sidecar_path("read-only-task", "pre")
    sidecar = str(abs_path.relative_to(delegate._REPO_ROOT)).replace("\\", "/")
    assert sidecar == ("batch_state/tasks/read-only-task.snapshots/read_only_checkout_pre.json")
    assert delegate._is_read_only_runtime_state_path(sidecar)
    assert not delegate._is_read_only_runtime_telemetry_path(sidecar)


def test_read_only_delegate_snapshot_sidecar_path_is_runtime_state():
    """#7203/#7208: repo-root dispatches observe the sidecar as ``tasks/<id>.snapshots/…``.

    The ``batch_state`` dir-name exemption does not apply there — see
    ``tests/test_delegate.py`` ``[repo-root]`` cases.
    """
    sidecar = "tasks/read-only-task.snapshots/read_only_checkout_pre.json"
    digest = "tasks/read-only-task.snapshots/digest.json"
    assert delegate._is_read_only_delegate_snapshot_sidecar_path(sidecar)
    assert delegate._is_read_only_delegate_snapshot_sidecar_path(digest)
    assert delegate._is_read_only_runtime_state_path(digest)
    assert delegate._is_read_only_runtime_state_path(sidecar)
    assert not delegate._is_read_only_runtime_telemetry_path(sidecar)


def test_read_only_checkout_snapshot_excludes_worktrees_tree(tmp_path, monkeypatch):
    """#7124: the snapshot records no ``.worktrees/`` entries at all."""
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo, monkeypatch)
    noise = repo / ".worktrees" / "dispatch" / "gemini" / "other-task"
    noise.mkdir(parents=True)
    (noise / "draft.md").write_text("other lane\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("visible\n", encoding="utf-8")

    snapshot, error = delegate._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert "untracked.txt" in snapshot
    assert not any(delegate._is_read_only_snapshot_excluded_path(path) for path in snapshot)


@pytest.mark.parametrize("suffix", [".result", ".json"])
def test_read_only_worker_fails_after_overwriting_another_task_record(suffix, tmp_tasks_dir, tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    own_id = "review-task"
    own_path = delegate._state_path(own_id)
    delegate._write_state_atomic(own_path, {"task_id": own_id, "cwd": str(checkout)})
    foreign_path = tmp_tasks_dir / f"impl-task{suffix}"
    foreign_path.write_text("original\n", encoding="utf-8")

    def overwrite_foreign_record(*_args, **_kwargs):
        foreign_path.write_text("replaced\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=overwrite_foreign_record):
        rc = delegate._run_worker(
            task_id=own_id,
            agent="grok",
            prompt="Review the change.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(own_path)
    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == [f"batch_state/tasks/{foreign_path.name}"]
    assert f"batch_state/tasks/{foreign_path.name}" in state["last_error"]


def test_read_only_checkout_snapshot_keeps_rename_source_into_worktrees(tmp_path, monkeypatch):
    """#7147: renaming a tracked file INTO ``.worktrees/`` keeps the source.

    ``git mv tracked.txt .worktrees/lane/tracked.txt`` is a mutation of the
    tracked source even though the destination is out of snapshot scope, so
    the source must still be recorded instead of the whole record dropping.
    """
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo, monkeypatch)
    lane = repo / ".worktrees" / "lane"
    lane.mkdir(parents=True)
    subprocess.run(
        ["git", "mv", "tracked.txt", ".worktrees/lane/tracked.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )

    snapshot, error = delegate._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert snapshot["tracked.txt"] == "R :source"
    assert ".worktrees/lane/tracked.txt" not in snapshot


def test_read_only_dispatch_allows_concurrent_sibling_worktree_add(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: a concurrent dispatch sandbox appearing under ``.worktrees/`` is excluded from snapshot."""
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    gitignore = checkout / ".gitignore"
    gitignore.write_text(gitignore.read_text(encoding="utf-8") + ".worktrees/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=checkout, check=True, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "ignore worktrees"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )
    # Detach HEAD so ``git worktree add -b`` can create a sibling branch without
    # fighting the fixture branch checked out in this repo.
    subprocess.run(
        ["git", "checkout", "--detach", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )

    task_id = "read-only-concurrent-sibling-worktree"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    sibling = checkout / ".worktrees" / "dispatch" / "cursor" / "codeql-path-injection-fix"

    def concurrent_sibling_worktree(*_args, **_kwargs):
        sibling.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                "cursor/codeql-path-injection-fix",
                str(sibling),
                "HEAD",
            ],
            cwd=checkout,
            check=True,
            capture_output=True,
            timeout=30,
        )
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=concurrent_sibling_worktree):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Inventory thin-mode sources without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    assert state["read_only_snapshot_retention"] == "digest"
    assert sibling.exists()


def test_read_only_dispatch_ignores_other_lane_worktree_activity(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: writes inside an EXISTING sibling dispatch sandbox are out of scope.

    #6938 exempted only newly appeared sandboxes, so a concurrent lane writing
    under a ``.worktrees/dispatch/<agent>/<task>/`` tree that already existed at
    the pre-snapshot still false-failed a clean read-only dispatch.
    """
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    gitignore = checkout / ".gitignore"
    gitignore.write_text(gitignore.read_text(encoding="utf-8") + ".worktrees/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=checkout, check=True, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "ignore worktrees"],
        cwd=checkout,
        check=True,
        capture_output=True,
        timeout=30,
    )

    other_lane = checkout / ".worktrees" / "dispatch" / "gemini" / "other-task"
    other_lane.mkdir(parents=True)
    (other_lane / "draft.md").write_text("other lane v1\n", encoding="utf-8")

    task_id = "read-only-other-lane-worktree-noise"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    def other_lane_activity(*_args, **_kwargs):
        (other_lane / "draft.md").write_text("other lane v2\n", encoding="utf-8")
        (other_lane / "more.py").write_text("# other lane\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=other_lane_activity):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Inventory thin-mode sources without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    assert state["read_only_snapshot_retention"] == "digest"


def test_read_only_failed_worker_keeps_real_error_alongside_mutation(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#7124: the guard diagnostic must not overwrite the returncode-derived error."""
    checkout = (tmp_path / "repo-root").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)

    task_id = "read-only-sigkill-plus-mutation"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(checkout)},
    )

    sigkill_result = type(
        "_Result",
        (),
        {
            "ok": False,
            "response": "",
            "stderr_excerpt": "worker killed: out of memory",
            "returncode": -9,
            "rate_limited": False,
            "model": "grok-4.6",
            "effort": "high",
            "cli_version": "0.2.111",
        },
    )()

    def sigkill_with_mutation(*_args, **_kwargs):
        (checkout / "tracked.txt").write_text("partial write before kill\n", encoding="utf-8")
        return sigkill_result

    with patch("agent_runtime.runner.invoke", side_effect=sigkill_with_mutation):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="grok",
            prompt="Review the module without edits.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 1
    assert state is not None
    assert state["status"] == "failed"
    assert state["returncode"] == -9
    assert state["returncode_reason"] == ("worker subprocess terminated by SIGKILL (returncode -9)")
    assert state["read_only_mutation_paths"] == ["tracked.txt"]
    last_error = state["last_error"]
    assert "worker killed: out of memory" in last_error
    assert "read-only checkout mutation detected: tracked.txt" in last_error


# ---------------------------------------------------------------------------
# #8516: read-only dispatch must not be able to write into the checkout
# (AC-02 post-run guard; AC-03 per-lane coverage; AC-01 agy cwd pin)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("agent", ["codex", "claude", "grok", "cursor", "kimi"])
def test_read_only_snapshot_untracked_root_leak_fails_task_per_lane(
    agent,
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#8516 AC-02/AC-03: a fake agent writing an untracked file into the
    checkout root fails the task with that path named — on every lane.

    Replays the review-a3-api-ui leak shape (``routes_and_dash.txt`` at the
    checkout root) through the post-run snapshot guard.
    """
    checkout = (tmp_path / f"repo-{agent}").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)

    task_id = f"read-only-root-leak-{agent}"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(checkout)})

    def root_leak(*_args, **_kwargs):
        (checkout / "routes_and_dash.txt").write_text("Routes found: 3\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=root_leak):
        rc = delegate._run_worker(
            task_id=task_id,
            agent=agent,
            prompt="Review the API surface without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 1
    assert state is not None
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == ["routes_and_dash.txt"]
    assert state["last_error"] == "read-only checkout mutation detected: routes_and_dash.txt"
    assert state["read_only_snapshot_retention"] == "full"


def test_read_only_snapshot_ignored_scratch_leak_fails_task(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#8516 AC-02: gitignored scratch writes are NOT exempt build noise.

    The exact review-a3-api-ui escape: agy wrote ``check_dead.py``-class
    files at the checkout root (matched by the repo's ``/*.py`` ignore rule)
    and under ``scratch/`` — every one landed as ``!!`` and the pre-#8516
    guard filed them as diagnostic-only "ignored mutations" while the task
    settled ``done``. They now fail the task and are named.
    """
    checkout = (tmp_path / "repo-ignored-scratch").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)
    gitignore = checkout / ".gitignore"
    gitignore.write_text(gitignore.read_text(encoding="utf-8") + "/*.py\n/scratch/\n", encoding="utf-8")

    task_id = "read-only-ignored-scratch-leak"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(checkout)})

    def ignored_scratch_leak(*_args, **_kwargs):
        (checkout / "check_dead.py").write_text("# scratch\n", encoding="utf-8")
        scratch = checkout / "scratch"
        scratch.mkdir()
        (scratch / "notes.txt").write_text("scratch\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=ignored_scratch_leak):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="agy",
            prompt="Inventory the routes without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 1
    assert state is not None
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == ["check_dead.py", "scratch/notes.txt"]
    assert state["read_only_ignored_mutation_paths"] == []
    assert "check_dead.py" in state["last_error"]
    assert "scratch/notes.txt" in state["last_error"]


def test_read_only_snapshot_runtime_noise_still_passes(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#8516 AC-02 boundary: recognized harness/runtime build noise stays exempt."""
    checkout = (tmp_path / "repo-runtime-noise").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)

    task_id = "read-only-runtime-noise"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(checkout)})

    noise = [".pytest_cache/v/lastfailed", "batch_state/fleet-comms/v1/comms.sqlite3-wal"]

    def runtime_noise_only(*_args, **_kwargs):
        for relative in noise:
            target = checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("noise\n", encoding="utf-8")
        return _finalize_mock_result()

    with patch("agent_runtime.runner.invoke", side_effect=runtime_noise_only):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="agy",
            prompt="Review without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ignored_mutation_paths"] == noise
    assert state["last_error"] is None


def test_read_only_snapshot_clean_run_passes(
    tmp_tasks_dir,
    tmp_path,
    monkeypatch,
):
    """#8516 AC-02: a clean read-only run settles done with empty mutations."""
    checkout = (tmp_path / "repo-clean").resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(checkout, monkeypatch)

    task_id = "read-only-clean-run"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(checkout)})

    with patch("agent_runtime.runner.invoke", side_effect=lambda *_args, **_kwargs: _finalize_mock_result()):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="agy",
            prompt="Review without editing the tree.",
            mode="read-only",
            cwd_str=str(checkout),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ignored_mutation_paths"] == []
    assert state["last_error"] is None
    assert state["read_only_snapshot_retention"] == "digest"


# --- #8516 AC-01: runner cwd pin (agy re-anchors its cwd after spawn) -------

_needs_procfs = pytest.mark.skipif(not Path("/proc").is_dir(), reason="cwd pin reads /proc (Linux-only)")


@contextlib.contextmanager
def _sleeping_child(cwd: Path, *argv_prefix: str):
    argv = list(argv_prefix) or ["sleep", "30"]
    proc = subprocess.Popen(argv, cwd=str(cwd))
    try:
        yield proc
    finally:
        proc.kill()
        proc.wait(timeout=10)


@_needs_procfs
def test_read_only_agy_cwd_pin_scoping(tmp_path):
    """The pin applies only to dispatch (task_id set) read-only agy spawns."""
    with _sleeping_child(tmp_path) as proc:
        assert runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id=None) is None
        assert (
            runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="codex", task_id="t") is None
        )
        assert runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="workspace-write", agent_name="agy", task_id="t") is None
        pin = runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None


@_needs_procfs
def test_read_only_agy_cwd_pin_verifies_child_settled_inside(tmp_path):
    """A child anchored in the pinned tree verifies on the first check."""
    with _sleeping_child(tmp_path) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        assert pin.check() is None
        assert pin.verified is True


@_needs_procfs
def test_read_only_agy_cwd_pin_fails_when_child_anchors_outside(tmp_path, monkeypatch):
    """A child still outside the pinned tree when grace closes fails cwd_unpinned."""
    monkeypatch.setenv(runner._CWD_PIN_GRACE_ENV, "0.2")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    with _sleeping_child(elsewhere) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=pinned, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        assert pin.check() is None  # still inside the grace window
        time.sleep(0.4)
        assert pin.check() == "cwd_unpinned"
        assert pin.last_observed is not None


@_needs_procfs
def test_read_only_agy_cwd_pin_allows_late_settle(tmp_path, monkeypatch):
    """A child that starts in scratch and then settles into the pin passes.

    Mirrors the 2026-09-24 agy evidence on #8516: the CLI starts in its own
    scratch directory and only later finds the cwd it was given.
    """
    monkeypatch.setenv(runner._CWD_PIN_GRACE_ENV, "10")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    argv = ["bash", "-c", 'sleep 0.5; cd "$1" && exec sleep 30', "_", str(pinned)]
    with _sleeping_child(elsewhere, *argv) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=pinned, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not pin.verified:
            assert pin.check() is None
            time.sleep(0.2)
        assert pin.verified is True
