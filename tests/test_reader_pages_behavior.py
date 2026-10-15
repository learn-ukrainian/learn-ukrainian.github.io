"""Run the five reader pages in Chrome against synthetic API responses."""

import subprocess
from pathlib import Path


def test_reader_pages_browser_behavior():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--test", "tests/reader_pages_behavior.test.cjs"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
