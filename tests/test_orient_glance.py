"""Run the Orient glance browser-JavaScript contracts in the dashboard test suite."""
import subprocess
from pathlib import Path


def test_orient_glance_javascript_contracts():
    result = subprocess.run(
        ["node", "--test", "tests/orient_glance.test.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
