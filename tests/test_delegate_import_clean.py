"""Clean-interpreter import of ``scripts.delegate`` (#10397)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_import_scripts_delegate_without_pythonpath() -> None:
    """A child at the repo root imports scripts.delegate with PYTHONPATH removed.

    pytest's ``pythonpath = ["scripts"]`` hides the bare ``agent_runtime``
    import. This child starts from the repo root with that variable gone.
    """
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.delegate"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
