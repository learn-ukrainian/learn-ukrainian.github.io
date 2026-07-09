"""Run the launcher deploy fail-honest fixtures under the required pytest gate.

``scripts/audit/test_deploy_extensions.sh`` exercises
``scripts/lib/deploy_extensions.sh`` — the helper both launchers
(``start-claude.sh``, ``start-codex.sh``) use to deploy
``agents_extensions/shared`` into the gitignored runtime dirs at startup.
The old inline blocks ran the deploy behind ``2>/dev/null || true`` and then
unconditionally printed a success line, so a failing deploy (orphan-path
guard trip, prompt-lint violation, rsync error) silently launched against a
STALE ``.claude``/``.codex``. This wrapper makes the failure banner and the
launcher wiring load-bearing in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _REPO_ROOT / "scripts" / "audit" / "test_deploy_extensions.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_deploy_extensions_fixtures() -> None:
    assert _FIXTURES.is_file(), f"missing deploy fixtures: {_FIXTURES}"
    result = subprocess.run(
        ["bash", str(_FIXTURES)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"deploy fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - deploy extensions fixtures passed" in result.stdout
