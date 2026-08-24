"""Tests for subprocess call timeouts and TimeoutExpired handling in scripts/orchestration/ (#7213)."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.orchestration import (
    curriculum_lifecycle_pilot as clp,
)
from scripts.orchestration import (
    dispatch_settle as ds,
)
from scripts.orchestration import (
    handoff_ready as hr,
)
from scripts.orchestration import (
    install_archived_thread_cleanup_launchd as iatc,
)
from scripts.orchestration import (
    install_mac_observer_launchd as imol,
)
from scripts.orchestration import (
    install_worktree_cleanup_launchd as iwcl,
)
from scripts.orchestration import (
    integration_sweep as isw,
)
from scripts.orchestration import (
    job_host_exec as jhe,
)
from scripts.orchestration import (
    orchestrator_control as oc,
)
from scripts.orchestration import (
    reaper_lifecycle as rl,
)
from scripts.orchestration import (
    task_closeout as tc,
)
from scripts.orchestration import (
    task_lifecycle as tl,
)


def _completed(
    args: list[str] | None = None,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args or [],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# 1. reaper_lifecycle.py
# ---------------------------------------------------------------------------


def test_reaper_lifecycle_create_recovery_ref_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        ref, err = rl.create_recovery_ref(tmp_path, branch="feature", head="a" * 40)
        assert ref is not None
        assert err is None

    assert len(calls) == 1
    assert calls[0]["timeout"] == rl.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "update-ref"], rl.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        ref, err = rl.create_recovery_ref(tmp_path, branch="feature", head="a" * 40)
        assert ref is None
        assert "timed out after 30.0s" in str(err)


def test_reaper_lifecycle_restore_worktree_timeouts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    wt_dir = repo / ".worktrees"
    wt_dir.mkdir()
    target = wt_dir / "target"

    # 1. Timeout on rev-parse recovery_ref
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], rl.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        ok, err = rl.restore_worktree(
            repo,
            recovery_ref="refs/reaper-rescue/test",
            branch="feature",
            worktree_path=target,
        )
        assert ok is False
        assert "git rev-parse timed out" in str(err)

    # 2. Timeout on rev-parse branch
    with patch(
        "subprocess.run",
        side_effect=[
            _completed(stdout="a" * 40 + "\n"),
            subprocess.TimeoutExpired(["git", "rev-parse"], rl.DEFAULT_GIT_TIMEOUT_SECONDS),
        ],
    ):
        ok, err = rl.restore_worktree(
            repo,
            recovery_ref="refs/reaper-rescue/test",
            branch="feature",
            worktree_path=target,
        )
        assert ok is False
        assert "git rev-parse branch timed out after 30.0s" in str(err)

    # 3. Timeout on worktree add
    with patch(
        "subprocess.run",
        side_effect=[
            _completed(stdout="a" * 40 + "\n"),
            _completed(returncode=0, stdout="a" * 40 + "\n"),
            subprocess.TimeoutExpired(["git", "worktree", "add"], rl.DEFAULT_GIT_TIMEOUT_SECONDS),
        ],
    ):
        ok, err = rl.restore_worktree(
            repo,
            recovery_ref="refs/reaper-rescue/test",
            branch="feature",
            worktree_path=target,
        )
        assert ok is False
        assert "git worktree add timed out after 30.0s" in str(err)

    # 4. Successful restore verifies timeout passed to all calls
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="a" * 40 + "\n")

    with patch("subprocess.run", side_effect=fake_run):
        ok, err = rl.restore_worktree(
            repo,
            recovery_ref="refs/reaper-rescue/test",
            branch="feature",
            worktree_path=target,
        )
        assert ok is True
        assert err is None

    assert len(calls) == 3
    assert all(c.get("timeout") == rl.DEFAULT_GIT_TIMEOUT_SECONDS for c in calls)


# ---------------------------------------------------------------------------
# 2. job_host_exec.py
# ---------------------------------------------------------------------------


def test_job_host_exec_forward_dispatch_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(jhe.ENV_HOST, "job-alias")
    monkeypatch.setenv(jhe.ENV_REPO, "/remote/repo")

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        rc = jhe.forward_dispatch(
            host_id="host-job",
            argv=["scripts/delegate.py", "dispatch", "--agent", "codex", "--task-id", "test-task"],
        )
        assert rc == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == jhe.DEFAULT_SSH_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["ssh"], jhe.DEFAULT_SSH_TIMEOUT_SECONDS),
    ):
        with pytest.raises(jhe.SshTransportError, match=r"SSH transport timed out after 300\.0s"):
            jhe.forward_dispatch(
                host_id="host-job",
                argv=["scripts/delegate.py", "dispatch", "--agent", "codex", "--task-id", "test-task"],
            )


def test_job_host_exec_main_timeout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(jhe.ENV_HOST, "job-alias")
    monkeypatch.setenv(jhe.ENV_REPO, "/remote/repo")

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["ssh"], jhe.DEFAULT_SSH_TIMEOUT_SECONDS),
    ):
        rc = jhe.main(["--host-id", "host-job", "--", "true"])
        assert rc == 255
        err = capsys.readouterr().err
        assert "SSH command timed out after 300.0s" in err


# ---------------------------------------------------------------------------
# 3. handoff_ready.py
# ---------------------------------------------------------------------------


def test_handoff_ready_git_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="clean")

    with patch("subprocess.run", side_effect=fake_run):
        rc, out = hr._git("status", "--porcelain")
        assert rc == 0
        assert out == "clean"

    assert len(calls) == 1
    assert calls[0]["timeout"] == hr.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], hr.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        rc, out = hr._git("status", "--porcelain")
        assert rc == 124
        assert "git status --porcelain timed out after 30.0s" in out


def test_handoff_ready_gh_json_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout='{"ok": true}')

    with patch("subprocess.run", side_effect=fake_run):
        rc, data = hr._gh_json("pr", "view")
        assert rc == 0
        assert data == {"ok": True}

    assert len(calls) == 1
    assert calls[0]["timeout"] == hr.DEFAULT_GH_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gh"], hr.DEFAULT_GH_TIMEOUT_SECONDS),
    ):
        rc, data = hr._gh_json("pr", "view")
        assert rc == 124
        assert "gh pr view timed out after 60.0s" in str(data)


# ---------------------------------------------------------------------------
# 4. curriculum_lifecycle_pilot.py
# ---------------------------------------------------------------------------


def test_curriculum_lifecycle_pilot_git_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="main\n")

    with patch("subprocess.run", side_effect=fake_run):
        out = clp._git(tmp_path, "rev-parse", "HEAD")
        assert out == "main"

    assert len(calls) == 1
    assert calls[0]["timeout"] == clp.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], clp.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(clp.PilotError, match=r"git rev-parse HEAD timed out after 30\.0s"):
            clp._git(tmp_path, "rev-parse", "HEAD")


def test_curriculum_lifecycle_pilot_commit_is_ancestor_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        assert clp._commit_is_ancestor(tmp_path, "abc1234") is True

    assert len(calls) == 1
    assert calls[0]["timeout"] == clp.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], clp.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(
            clp.PilotError,
            match=r"cannot verify historical commit abc1234: git merge-base timed out after 30\.0s",
        ):
            clp._commit_is_ancestor(tmp_path, "abc1234")


# ---------------------------------------------------------------------------
# 5. task_lifecycle.py
# ---------------------------------------------------------------------------


def test_task_lifecycle_run_git_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="status-output\n")

    with patch("subprocess.run", side_effect=fake_run):
        out = tl._run_git(tmp_path, ["status", "--short"])
        assert out == "status-output"

    assert len(calls) == 1
    assert calls[0]["timeout"] == tl.DEFAULT_GIT_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], tl.DEFAULT_GIT_TIMEOUT_SECONDS),
    ):
        with pytest.raises(tl.LifecycleError, match=r"git status --short timed out after 30\.0s"):
            tl._run_git(tmp_path, ["status", "--short"])


# ---------------------------------------------------------------------------
# 6. task_closeout.py
# ---------------------------------------------------------------------------


def test_task_closeout_default_runner_timeout(tmp_path: Path) -> None:
    runner = tc._default_runner(tmp_path)
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="output\n")

    with patch("subprocess.run", side_effect=fake_run):
        res = runner(["gh", "pr", "view", "123"])
        assert res == "output\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == tc.DEFAULT_COMMAND_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gh"], tc.DEFAULT_COMMAND_TIMEOUT_SECONDS),
    ):
        with pytest.raises(tl.LifecycleError, match=r"gh pr view 123 timed out after 60\.0s"):
            runner(["gh", "pr", "view", "123"])


# ---------------------------------------------------------------------------
# 7. orchestrator_control.py
# ---------------------------------------------------------------------------


def test_orchestrator_control_cmd_dispatch_timeout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = argparse.Namespace(
        repo_root=tmp_path,
        run_id="run-1",
        task_id="task-1",
        agent="codex",
        prompt="do stuff",
        prompt_file=None,
        mode="read-only",
        model=None,
        effort=None,
        cwd=None,
        worktree=None,
        full_checkout=False,
        sparse_include=None,
        base="main",
        hard_timeout=None,
        silence_timeout=None,
        initial_response_timeout=None,
        max_budget_usd=None,
        lifecycle_file=None,
        dry_run=False,
        note="",
    )

    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout='{"status": "running"}\n')

    with patch("subprocess.run", side_effect=fake_run):
        rc = oc.cmd_dispatch(args)
        assert rc == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == oc.DEFAULT_DELEGATE_TIMEOUT_SECONDS
    capsys.readouterr()

    with patch(

        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["python", "delegate.py"], oc.DEFAULT_DELEGATE_TIMEOUT_SECONDS
        ),
    ):
        rc = oc.cmd_dispatch(args)
        assert rc == 124
        out = json.loads(capsys.readouterr().out)
        assert out["error"] == "delegate dispatch timed out"
        assert out["returncode"] == 124
        assert "timed out after 180.0s" in out["stderr"]


# ---------------------------------------------------------------------------
# 8. integration_sweep.py
# ---------------------------------------------------------------------------


def test_integration_sweep_default_runner_timeout(tmp_path: Path) -> None:
    adapter = isw.GitHubAdapter(tmp_path)
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="output\n")

    with patch("subprocess.run", side_effect=fake_run):
        res = adapter._default_runner(["gh", "pr", "list"])
        assert res == "output\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == isw.DEFAULT_GH_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gh"], isw.DEFAULT_GH_TIMEOUT_SECONDS),
    ):
        with pytest.raises(isw.SweepError, match=r"gh pr list timed out after 60\.0s"):
            adapter._default_runner(["gh", "pr", "list"])


# ---------------------------------------------------------------------------
# 9. install_worktree_cleanup_launchd.py
# ---------------------------------------------------------------------------


def test_install_worktree_cleanup_launchd_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="service printout")

    with patch("subprocess.run", side_effect=fake_run):
        res = iwcl._launchctl(["print", "gui/501/com.learn-ukrainian.worktree-cleanup"])
        assert res.returncode == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == iwcl.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["/bin/launchctl"], iwcl.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS
        ),
    ):
        with pytest.raises(
            iwcl.LaunchdError,
            match=r"/bin/launchctl print gui/501/com\.learn-ukrainian\.worktree-cleanup timed out after 30\.0s",
        ):
            iwcl._launchctl(["print", "gui/501/com.learn-ukrainian.worktree-cleanup"])


# ---------------------------------------------------------------------------
# 10. install_mac_observer_launchd.py
# ---------------------------------------------------------------------------


def test_install_mac_observer_launchd_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="service printout")

    with patch("subprocess.run", side_effect=fake_run):
        res = imol._launchctl(["print", "gui/501/com.learn-ukrainian.mac-observer-heartbeat"])
        assert res.returncode == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == imol.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["/bin/launchctl"], imol.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS
        ),
    ):
        with pytest.raises(
            imol.LaunchdError,
            match=r"/bin/launchctl print gui/501/com\.learn-ukrainian\.mac-observer-heartbeat timed out after 30\.0s",
        ):
            imol._launchctl(["print", "gui/501/com.learn-ukrainian.mac-observer-heartbeat"])


# ---------------------------------------------------------------------------
# 11. install_archived_thread_cleanup_launchd.py
# ---------------------------------------------------------------------------


def test_install_archived_thread_cleanup_launchd_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="service printout")

    with patch("subprocess.run", side_effect=fake_run):
        res = iatc._launchctl(["print", "gui/501/com.learn-ukrainian.codex-archived-thread-cleanup"])
        assert res.returncode == 0

    assert len(calls) == 1
    assert calls[0]["timeout"] == iatc.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["/bin/launchctl"], iatc.DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS
        ),
    ):
        with pytest.raises(
            iatc.LaunchdError,
            match=r"/bin/launchctl print gui/501/com\.learn-ukrainian\.codex-archived-thread-cleanup timed out after 30\.0s",
        ):
            iatc._launchctl(["print", "gui/501/com.learn-ukrainian.codex-archived-thread-cleanup"])


# ---------------------------------------------------------------------------
# 12. dispatch_settle.py
# ---------------------------------------------------------------------------


def test_dispatch_settle_run_timeout() -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0, stdout="main\n")

    with patch("subprocess.run", side_effect=fake_run):
        res = ds._run(["git", "rev-parse", "HEAD"])
        assert res.returncode == 0
        assert res.stdout == "main\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == ds.DEFAULT_COMMAND_TIMEOUT_SECONDS

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], ds.DEFAULT_COMMAND_TIMEOUT_SECONDS),
    ):
        res = ds._run(["git", "rev-parse", "HEAD"])
        assert res.returncode == 124
        assert "command timed out after 60.0s" in res.stderr

    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git"], ds.DEFAULT_COMMAND_TIMEOUT_SECONDS),
    ):
        with pytest.raises(subprocess.TimeoutExpired):
            ds._run(["git", "rev-parse", "HEAD"], check=True)
