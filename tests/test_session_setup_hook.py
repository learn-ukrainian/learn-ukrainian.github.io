"""Run the SessionStart-hook handoff-routing fixtures under the required pytest gate.

``scripts/audit/test_session_setup_hook.sh`` exercises the cold-start handoff
selection logic in ``agents_extensions/shared/hooks/session-setup.sh`` — including
the regression guard that ``SESSION_HANDOFF_AGENT`` routes each lane (e.g.
``claude`` vs ``claude-infra``) to its OWN ``.agent/<agent>-thread-handoff.md``
slot. The shell script was previously not wired into CI, so this thin wrapper
makes the guard load-bearing: it runs in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_session_setup_hook.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_session_setup_hook_handoff_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing hook test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"hook fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - session setup hook handoff fixtures passed" in result.stdout
