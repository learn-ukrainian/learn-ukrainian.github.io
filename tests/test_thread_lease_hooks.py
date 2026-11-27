"""Run the thread-lease hook fixtures under the required pytest gate.

``scripts/audit/test_thread_lease_hooks.sh`` exercises the three thread-lease
hook scripts (PostToolUse heartbeat, Stop heartbeat, SessionEnd release) end
to end against the real CLI, with NO ``LEARN_UKRAINIAN_THREAD_LEASE_GENERATION``
in the environment at all — proving the identity-proof fence (which replaced
the generation-env-var fence, since that export never reached hook
subprocesses) actually works outside of unit-test mocking. The shell script
was previously not wired into CI, so this thin wrapper makes the guard
load-bearing: it runs in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.githooks import bind_hook_host_context

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_thread_lease_hooks.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_thread_lease_hook_fixtures(tmp_path: Path) -> None:
    assert _HOOK_TEST.is_file(), f"missing hook test: {_HOOK_TEST}"
    # lu-machinery 0.1.83 hooks start from the host binding (LU_PYTHON, host_context shell).
    env = dict(os.environ)
    bind_hook_host_context(tmp_path, env, product=_REPO_ROOT, python=sys.executable, machinery=tmp_path / "machinery")
    env["LEARN_UKRAINIAN_PYTHON"] = env["LU_PYTHON"]
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, (
        f"hook fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - thread lease hook fixtures passed" in result.stdout
