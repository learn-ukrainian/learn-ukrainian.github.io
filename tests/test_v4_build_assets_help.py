"""Keep the public build CLI help portable and free of host run roots."""

import subprocess
import sys
from pathlib import Path


def test_build_assets_help_uses_relative_interpreter():
    result = subprocess.run(
        [sys.executable, "packages/v4-runtime/build_assets.py", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )

    assert "Example: .venv/bin/python packages/v4-runtime/build_assets.py --development" in result.stdout
    assert "/home/" not in result.stdout + result.stderr
