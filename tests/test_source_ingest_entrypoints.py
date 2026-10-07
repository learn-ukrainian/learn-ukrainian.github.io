"""Real source-ingest entrypoints must reach offline help without PYTHONPATH (#9991)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.repo_invariant
@pytest.mark.parametrize("module", ["grac_frequency_ingest", "slovnyk_me_ingest"])
@pytest.mark.parametrize("style", ["file", "module"])
def test_source_ingest_help_from_repository_root(module: str, style: str) -> None:
    argv = (
        [f"scripts/ingest/{module}.py"]
        if style == "file"
        else ["-m", f"scripts.ingest.{module}"]
    )
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["LEXICON_SLOVNYK_OFFLINE"] = "1"
    result = subprocess.run(
        [sys.executable, *argv, "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout.lower(), result.stdout + result.stderr
    assert "--help" in result.stdout
