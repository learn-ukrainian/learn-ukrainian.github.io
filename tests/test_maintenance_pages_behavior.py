"""Execute B4's shipped inline scripts in Chromium with synthetic API responses."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_maintenance_pages_browser_behavior() -> None:
    result = subprocess.run(
        ["node", "--test", "tests/maintenance_pages_behavior.test.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
