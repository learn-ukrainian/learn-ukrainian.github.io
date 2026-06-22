"""Run the launcher handoff-identity fixtures under the required pytest gate.

``scripts/audit/test_handoff_identity.sh`` exercises
``scripts/lib/handoff_identity.sh`` — the derivation that ``start-claude.sh``
uses to turn a Claude Code ``--agent`` selection into the right
``SESSION_HANDOFF_AGENT`` cold-start slot (e.g. ``infra-orchestrator`` →
``claude-infra``). This thin wrapper makes that mapping load-bearing in the
required ``Test (pytest)`` job, so the infra/folk cold-start collision cannot
silently regress.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_handoff_identity.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_handoff_identity_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing identity test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"identity fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - handoff identity fixtures passed" in result.stdout
