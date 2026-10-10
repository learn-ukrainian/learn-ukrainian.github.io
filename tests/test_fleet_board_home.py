"""DOM render contracts for the fleet board home."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_fleet_board_home_render() -> None:
    result = subprocess.run(
        ["node", "--test", "tests/fleet_board_home.test.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
