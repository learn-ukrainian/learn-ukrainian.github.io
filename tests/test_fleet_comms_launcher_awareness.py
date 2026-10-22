"""Standalone TUI launchers must point at shared fleet-comms authority doctrine."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/lib/fleet_comms_cold_start.sh"


def test_cold_clause_resolves_live_mode_when_env_unset() -> None:
    """Unset FLEET_COMMS_PLANE_MODE must not hardcode mode=off when live is authority."""
    env = os.environ.copy()
    env.pop("FLEET_COMMS_PLANE_MODE", None)
    env.pop("FLEET_COMMS_MESSAGE_PLANE", None)
    env["PROJECT_DIR"] = str(REPO)
    env["LC_ROOT"] = str(REPO)

    script = f"""
set -euo pipefail
source "{HELPER}"
resolved="$(fleet_comms_resolve_plane_mode)"
clause="$(fleet_comms_cold_clause)"
printf 'resolved=%s\\n' "$resolved"
printf 'clause=%s\\n' "$clause"
"""
    proc = subprocess.run(
        ["bash", "-c", script],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "resolved=authority" in out or "resolved=dual_write" in out or "resolved=shadow" in out
    # When resolve returns authority, clause must carry it (not a hardcoded off).
    if "resolved=authority" in out:
        assert "mode=authority" in out
        assert "current mode=off" not in out
