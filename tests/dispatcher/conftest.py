"""Shared product-facing dispatcher test fixtures."""


import os
import subprocess
import sys
from pathlib import Path

import pytest

DOCTOR_NOT_FETCHED = "Managed settings (remote): not fetched — requires an Enterprise or Team subscription"


@pytest.fixture(autouse=True)
def agy_dispatch_guards(monkeypatch):
    """Record AGY guard provisioning only for in-process builds outside ``.worktrees/dispatch``.

    Those builds use disposable checkouts, where provisioning refuses. A build in a dispatch
    worktree, and every subprocess ``sandbox`` dispatch, runs the real provisioning.
    """
    from lu_machinery.agent_runtime import agy_hook_config

    real, calls = agy_hook_config.require_dispatch_guards, []

    def provision(worktree, home):
        if "/.worktrees/dispatch/" in Path(worktree).absolute().as_posix() + "/":
            return real(worktree, home)
        calls.append(worktree)
        return None

    monkeypatch.setattr(agy_hook_config, "require_dispatch_guards", provision)
    return calls


@pytest.fixture(autouse=True)
def claude_doctor(tmp_path_factory, monkeypatch):
    """A read-only Claude dispatch asks ``claude doctor`` for server-managed settings; answer as a consumer login.

    CI has no Claude Code, and a developer host's own login must not decide a test. Tests that start a
    provider ``claude`` put their own stub first on ``PATH``.
    """
    return install_claude_doctor_stub(tmp_path_factory.mktemp("claude-doctor"), monkeypatch)


def install_claude_doctor_stub(bin_dir, monkeypatch):
    """Put a ``claude`` that answers only ``claude doctor``, as a consumer login, first on ``PATH``."""
    stub = bin_dir / "claude"
    stub.write_text(
        f"#!{sys.executable}\nimport sys\n"
        f"if sys.argv[1:] != ['doctor']:\n    sys.exit('claude doctor stub: ' + ' '.join(sys.argv[1:]))\n"
        f"print({DOCTOR_NOT_FETCHED!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', os.defpath)}")
    return stub


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()
