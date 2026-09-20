"""Deterministic isolation coverage for primary-root ACP compatibility calls."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import scripts
from scripts.ai_agent_bridge import _acp_execution
from scripts.ai_agent_bridge._acp_execution import (
    AcpExecutionWorkspaceError,
    acp_execution_cwd,
)
from scripts.common.acp_runtime_lock import build_lock_reason, process_start_time
from scripts.guardrails.worktree_containment import classify_repo_path

PROJECT_ROOT = Path(scripts.__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True, timeout=30,
    )


def _make_primary(tmp_path: Path) -> Path:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main")
    _git(primary, "config", "user.name", "ACP Test")
    _git(primary, "config", "user.email", "acp@example.invalid")
    (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(primary, "add", "tracked.txt")
    _git(primary, "commit", "-m", "fixture")
    return primary


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return env


def test_primary_root_call_uses_and_removes_detached_no_checkout_worktree(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main")
    _git(primary, "config", "user.name", "ACP Test")
    _git(primary, "config", "user.email", "acp@example.invalid")
    (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(primary, "add", "tracked.txt")
    _git(primary, "commit", "-m", "fixture")

    with acp_execution_cwd(primary, task_id="task-6243") as workspace:
        assert workspace != primary
        assert workspace.is_relative_to(primary / ".worktrees" / "dispatch" / "acp")
        assert classify_repo_path(workspace, cwd=workspace) == "dispatch_worktree"
        assert {item.name for item in workspace.iterdir()} == {".git"}
        listed = _git(primary, "worktree", "list", "--porcelain").stdout
        assert str(workspace) in listed
        assert "locked active ACP execution task-6243" in listed

        _git(primary, "worktree", "prune", "--expire", "now")
        after_prune = _git(primary, "worktree", "list", "--porcelain").stdout
        assert str(workspace) in after_prune
        assert workspace.exists()

    assert not workspace.exists()
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert str(workspace) not in listed


@pytest.mark.parametrize(
    "token",
    [
        "-rf",
        '{"type":"tool","part":{"tool":"bash"}}',
        'prompt"}}',
    ],
)
def test_transport_fragment_task_id_is_rejected_before_directory_creation(
    tmp_path: Path,
    token: str,
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main")

    with pytest.raises(
        AcpExecutionWorkspaceError,
        match="unsafe_acp_execution_task_id",
    ):
        with acp_execution_cwd(primary, task_id=token):
            raise AssertionError("unsafe task id reached the ACP execution body")

    assert not (primary / ".worktrees").exists()
    assert not (primary / token).exists()


_ASK_BODY = (
    "import sys, time\n"
    "from pathlib import Path\n"
    "from scripts.ai_agent_bridge._acp_execution import acp_execution_cwd\n"
    "with acp_execution_cwd(Path(sys.argv[1]), task_id=sys.argv[2]) as workspace:\n"
    "    print(f'WORKSPACE={workspace}', flush=True)\n"
    "    time.sleep(120)\n"
)


def _spawn_ask(primary: Path, task_id: str) -> tuple[subprocess.Popen[str], Path]:
    proc = subprocess.Popen(
        [sys.executable, "-c", _ASK_BODY, str(primary), task_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_subprocess_env(),
    )
    try:
        assert proc.stdout is not None
        line = proc.stdout.readline().strip()
        assert line.startswith("WORKSPACE="), line
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    return proc, Path(line.removeprefix("WORKSPACE="))


def test_sigkilled_owner_leaves_locked_worktree_that_next_entry_sweeps(
    tmp_path: Path,
) -> None:
    primary = _make_primary(tmp_path)
    proc, leaked = _spawn_ask(primary, "doomed-8344")
    proc.kill()  # SIGKILL: no unwind, the finally never runs
    proc.wait(timeout=30)

    assert leaked.exists()
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert f"worktree {leaked}" in listed
    assert f"locked active ACP execution doomed-8344 (owner pid={proc.pid} start=" in listed

    # The next ACP execution entry sweeps the provably-dead owner before
    # creating its own workspace.
    with acp_execution_cwd(primary, task_id="next-8344") as workspace:
        assert workspace != leaked
        assert not leaked.exists()
        listed = _git(primary, "worktree", "list", "--porcelain").stdout
        assert str(leaked) not in listed
        assert str(workspace) in listed
    assert not workspace.exists()


def _plant_locked_runtime(
    primary: Path,
    name: str,
    reason: str,
) -> Path:
    runtime = primary / ".worktrees" / "dispatch" / "acp" / name
    runtime.parent.mkdir(parents=True, exist_ok=True)
    _git(primary, "worktree", "add", "--detach", "--no-checkout", str(runtime), "HEAD")
    _git(primary, "worktree", "lock", "--reason", reason, str(runtime))
    return runtime


def test_live_owner_is_never_swept(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    own_pid = os.getpid()
    live = _plant_locked_runtime(
        primary,
        "runtime-live-owner",
        build_lock_reason("live-8344", pid=own_pid, start_time=process_start_time(own_pid)),
    )

    with acp_execution_cwd(primary, task_id="polite-8344") as workspace:
        assert workspace != live
        assert live.exists()
        listed = _git(primary, "worktree", "list", "--porcelain").stdout
        assert f"locked active ACP execution live-8344 (owner pid={own_pid}" in listed

    assert live.exists()
    _git(primary, "worktree", "unlock", str(live))
    _git(primary, "worktree", "remove", "--force", str(live))


def test_recycled_pid_with_different_start_time_is_treated_as_dead(
    tmp_path: Path,
) -> None:
    primary = _make_primary(tmp_path)
    own_pid = os.getpid()
    start = process_start_time(own_pid)
    assert start is not None
    stale = _plant_locked_runtime(
        primary,
        "runtime-recycled-pid",
        # A live pid whose recorded start time differs: the original owner is
        # dead and the pid has been recycled.
        build_lock_reason("recycled-8344", pid=own_pid, start_time=start + 1000),
    )

    with acp_execution_cwd(primary, task_id="reaper-8344"):
        assert not stale.exists()
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert str(stale) not in listed


def test_sigterm_unwinds_and_leaves_nothing_behind(tmp_path: Path) -> None:
    primary = _make_primary(tmp_path)
    proc, workspace = _spawn_ask(primary, "cancelled-8344")

    proc.send_signal(signal.SIGTERM)
    returncode = proc.wait(timeout=30)

    # Orderly unwind ran the finally cleanup, then exited with the
    # conventional 128+SIGTERM code — the signal was not swallowed.
    assert returncode == 128 + signal.SIGTERM
    assert not workspace.exists()
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert str(workspace) not in listed
    stderr = proc.stderr.read() if proc.stderr is not None else ""
    assert "ACP execution worktree cleanup failed" not in stderr


def test_sweep_preserves_dead_owner_worktree_with_unexpected_files(
    tmp_path: Path,
) -> None:
    primary = _make_primary(tmp_path)
    proc = subprocess.Popen(["true"])
    dead_pid = proc.pid
    proc.wait(timeout=30)
    stale = _plant_locked_runtime(
        primary,
        "runtime-dead-with-files",
        build_lock_reason("dead-8344", pid=dead_pid, start_time=1),
    )
    (stale / "stray.txt").write_text("keep\n", encoding="utf-8")

    swept = _acp_execution.sweep_dead_acp_runtime_worktrees(primary)

    assert swept == []
    assert (stale / "stray.txt").read_text(encoding="utf-8") == "keep\n"
    listed = _git(primary, "worktree", "list", "--porcelain").stdout
    assert f"worktree {stale}" in listed


def test_install_orderly_sigterm_from_non_main_thread_is_noop() -> None:
    previous = signal.getsignal(signal.SIGTERM)
    outcome: list[object] = []

    def worker() -> None:
        try:
            outcome.append(_acp_execution._install_orderly_sigterm())
        except Exception as exc:
            outcome.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=30)

    assert outcome == [None]
    assert signal.getsignal(signal.SIGTERM) == previous
