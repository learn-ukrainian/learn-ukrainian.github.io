"""The upload CLI cannot infer an old in-tree export destination."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_upload_requires_explicit_package_directory() -> None:
    script = Path(__file__).resolve().parents[3] / "scripts/projects/open_model_data/upload_to_huggingface.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "--dataset-dir" in result.stderr
    assert "huggingface" not in result.stdout.lower()
