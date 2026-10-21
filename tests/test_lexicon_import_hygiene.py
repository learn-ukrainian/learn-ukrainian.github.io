"""Importing the lexicon admit scripts must not change the process environment (#9473).

A module-level ``os.environ[...] = ...`` leaks into every later test in the same
xdist worker. The offline switch belongs in each script's entry point, scoped.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_KEY = "LEXICON_SLOVNYK_OFFLINE"
ADMIT_MODULES = ["scripts.lexicon.admit_fmu_boosters", "scripts.lexicon.admit_stem_slice_2a"]


@pytest.mark.parametrize("module", ADMIT_MODULES)
def test_import_leaves_environment_unchanged(module: str) -> None:
    code = (
        "import os\n"
        "before = dict(os.environ)\n"
        f"import {module}\n"
        "assert dict(os.environ) == before, sorted(set(os.environ) ^ set(before))\n"
    )
    env = {k: v for k, v in os.environ.items() if k != ENV_KEY}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
