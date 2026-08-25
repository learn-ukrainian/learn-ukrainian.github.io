"""Unit tests for subprocess timeout bounds in scripts/guardrails/ (#7213 slice 12).

Every bounded call site must (a) pass an explicit ``timeout=`` — 30s for git
plumbing, 60s for the hook installer — and (b) map ``subprocess.TimeoutExpired``
to its documented degradation instead of an uncaught traceback, because these
helpers run inside git hooks / launchers:

* ``worktree_containment._run_git``       → failed probe (returncode 124), callers fall back
* ``assert_primary_on_main._git``         → failed CompletedProcess, detached/error paths fire
* ``primary_write_guard`` ls-files sites  → print + ``sys.exit(1)``
* ``primary_write_guard.install_hooks``   → print + ``sys.exit(1)`` via the OSError handler
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.guardrails import assert_primary_on_main as apom
from scripts.guardrails import primary_write_guard as pwg
from scripts.guardrails import worktree_containment as wc

GIT_TIMEOUT_S = 30
HOOK_INSTALL_TIMEOUT_S = 60


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


def _timed_out(cmd: list[str], **_kwargs: object) -> subprocess.TimeoutExpired:
    raise subprocess.TimeoutExpired(cmd, GIT_TIMEOUT_S)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _real_git(repo: Path, *args: str) -> None:
    """Fixture-side git setup with a REAL subprocess (before any patching)."""
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )


@pytest.fixture
def primary_repo(tmp_path: Path) -> Path:
    """Real primary checkout on main, built BEFORE any subprocess patching."""
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(root)],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    _real_git(root, "config", "user.email", "test@example.com")
    _real_git(root, "config", "user.name", "Test")
    _real_git(root, "commit", "--allow-empty", "-m", "init")
    return root


# ---------------------------------------------------------------------------
# worktree_containment._run_git
# ---------------------------------------------------------------------------


def test_run_git_passes_explicit_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, stdout="main\n")

    with patch("subprocess.run", side_effect=fake_run):
        proc = wc._run_git(tmp_path, "symbolic-ref", "--quiet", "--short", "HEAD")

    assert len(calls) == 1
    assert calls[0]["timeout"] == GIT_TIMEOUT_S
    assert proc.returncode == 0
    assert proc.stdout == "main\n"


def test_run_git_maps_timeout_to_failed_probe_not_raise(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        proc = wc._run_git(tmp_path, "status", "--porcelain")

    assert isinstance(proc, subprocess.CompletedProcess)
    assert proc.returncode == 124
    assert proc.stdout == ""
    assert "TimeoutExpired" in proc.stderr


def test_resolve_main_root_falls_back_to_fs_walk_when_git_times_out(tmp_path: Path) -> None:
    """The FileNotFoundError fallback contract must also cover timeouts."""
    fake_repo = tmp_path / "main"
    (fake_repo / ".git").mkdir(parents=True)

    with patch("subprocess.run", side_effect=_timed_out):
        assert wc.resolve_main_root(fake_repo) == fake_repo.resolve()


# ---------------------------------------------------------------------------
# assert_primary_on_main._git
# ---------------------------------------------------------------------------


def test_assert_primary_git_passes_explicit_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, stdout="main\n")

    with patch("subprocess.run", side_effect=fake_run):
        proc = apom._git(tmp_path, "symbolic-ref", "--quiet", "--short", "HEAD")

    assert len(calls) == 1
    assert calls[0]["timeout"] == GIT_TIMEOUT_S
    assert proc.stdout.strip() == "main"


def test_assert_primary_git_maps_timeout_to_failed_process(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        proc = apom._git(tmp_path, "rev-parse", "--short", "HEAD")

    assert isinstance(proc, subprocess.CompletedProcess)
    assert proc.returncode == 124
    assert proc.stdout == ""
    assert "TimeoutExpired" in proc.stderr


def test_primary_head_state_survives_total_git_timeout(primary_repo: Path) -> None:
    """A wedged git must land in the detached/error path, never raise (#7213).

    Every git probe inside primary_head_state times out; root resolution falls
    back to the on-disk ``.git`` walk and symbolic-ref reads as failed, so the
    pre-existing detached-head diagnostics fire.
    """
    with patch("subprocess.run", side_effect=_timed_out):
        state = apom.primary_head_state(primary_repo)

    assert state["ok"] is False
    assert state["reason"] == "detached_head"
    assert state["path"] == str(primary_repo.resolve())
    assert "unknown" in str(state["message"])


# ---------------------------------------------------------------------------
# primary_write_guard — ls-files sites (get_writable_tracked_files /
# apply_guard / release_guard)
# ---------------------------------------------------------------------------


def test_get_writable_tracked_files_passes_explicit_timeout(tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, stdout="")

    with patch("subprocess.run", side_effect=fake_run):
        assert pwg.get_writable_tracked_files(tmp_path) == []

    assert len(calls) == 1
    assert calls[0]["cmd"] == ["git", "ls-files", "-z"]
    assert calls[0]["timeout"] == GIT_TIMEOUT_S


@pytest.mark.parametrize(
    "guard_call",
    [
        lambda: pwg.get_writable_tracked_files(Path("/unused")),
        lambda: pwg.apply_guard(hook_mode=False),
        lambda: pwg.release_guard(),
    ],
    ids=["get_writable_tracked_files", "apply_guard", "release_guard"],
)
def test_ls_files_timeout_exits_1_not_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    guard_call,
) -> None:
    """TimeoutExpired must be caught exactly like CalledProcessError: print + exit 1."""
    monkeypatch.setattr(pwg, "check_primary_checkout_root", lambda hook_mode=False: tmp_path)

    with patch("subprocess.run", side_effect=_timed_out):
        with pytest.raises(SystemExit) as excinfo:
            guard_call()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error listing tracked files:" in captured.err
    # str(TimeoutExpired) reads "Command [...] timed out after N seconds".
    assert "timed out after" in captured.err


@pytest.mark.parametrize(
    "guard_call, expect_owner_write",
    [
        (lambda: pwg.apply_guard(hook_mode=False), False),
        (lambda: pwg.release_guard(), True),
    ],
    ids=["apply_guard", "release_guard"],
)
def test_ls_files_success_still_applies_after_timeout_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    guard_call,
    expect_owner_write: bool,
) -> None:
    """Happy path keeps working with the new kwarg present (signature smoke)."""
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("x\n", encoding="utf-8")
    tracked.chmod(0o444)
    monkeypatch.setattr(pwg, "check_primary_checkout_root", lambda hook_mode=False: tmp_path)

    def fake_run(cmd, **kwargs):
        assert kwargs["timeout"] == GIT_TIMEOUT_S
        return _completed(cmd, stdout="tracked.txt\0")

    with patch("subprocess.run", side_effect=fake_run):
        guard_call()

    owner_write = bool(os.stat(tracked).st_mode & 0o200)
    assert owner_write is expect_owner_write


# ---------------------------------------------------------------------------
# primary_write_guard.install_hooks (hook installer, 60s)
# ---------------------------------------------------------------------------


@pytest.fixture
def installer_root(tmp_path: Path) -> Path:
    installer = tmp_path / "scripts" / "install_git_hooks.sh"
    installer.parent.mkdir(parents=True)
    installer.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    return tmp_path


def test_install_hooks_passes_60s_timeout(installer_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pwg, "check_primary_checkout_root", lambda hook_mode=False: installer_root)
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        pwg.install_hooks()

    assert len(calls) == 1
    assert calls[0]["cmd"] == ["bash", str(installer_root / "scripts" / "install_git_hooks.sh")]
    assert calls[0]["timeout"] == HOOK_INSTALL_TIMEOUT_S


def test_install_hooks_timeout_exits_1_via_existing_handler(
    installer_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TimeoutExpired joins the existing (OSError, CalledProcessError) handler."""
    monkeypatch.setattr(pwg, "check_primary_checkout_root", lambda hook_mode=False: installer_root)

    def timed_out(cmd, **_kwargs):
        raise subprocess.TimeoutExpired(cmd, HOOK_INSTALL_TIMEOUT_S)

    with patch("subprocess.run", side_effect=timed_out):
        with pytest.raises(SystemExit) as excinfo:
            pwg.install_hooks()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Failed to install tracked Git hooks:" in captured.err
    assert "timed out after" in captured.err
