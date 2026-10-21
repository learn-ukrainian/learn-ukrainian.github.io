"""Unit tests for Kimi stream bootstrap helpers (no live stream DB required)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("epic", ["../x", "/absolute", "Harness", "bad_name", "harness\n", "інфра"])
@pytest.mark.parametrize("command", ["status", "mint", "bootstrap"])
def test_cli_rejects_unsafe_epic_before_writing(tmp_path: Path, epic: str, command: str) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    if epic == "/absolute":
        epic = str(tmp_path / "absolute")
    extra = ["--stream", "epic:999999", "--out-dir", str(tmp_path / "out")] if command == "mint" else []
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.session_canary.kimi_lane",
            "--repo",
            str(repo),
            command,
            f"--epic={epic}",
            *extra,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert proc.returncode == 2
    assert "error: epic must be a selector" in proc.stderr
    assert list(tmp_path.rglob("*")) == [repo]
