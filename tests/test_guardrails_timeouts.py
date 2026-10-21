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

from scripts.guardrails import primary_write_guard as pwg

GIT_TIMEOUT_S = 30
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
# worktree_containment._run_git
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# assert_primary_on_main._git
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# primary_write_guard — ls-files sites (get_writable_tracked_files /
# apply_guard / release_guard)
# ---------------------------------------------------------------------------


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
