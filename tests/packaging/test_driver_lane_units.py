"""Context guard timer and boot lane relaunch unit templates (#10814)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGING = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
UNITS = (
    "learn-ukrainian-context-guard.service",
    "learn-ukrainian-context-guard.timer",
    "learn-ukrainian-lane-relaunch.service",
)


def _text(name: str) -> str:
    return (PACKAGING / name).read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("systemd-analyze") is None, reason="systemd-analyze unavailable")
def test_rendered_units_pass_systemd_analyze_verify(tmp_path: Path) -> None:
    root = str(Path(sys.executable).parents[2])
    paths = []
    for name in UNITS:
        rendered = tmp_path / name
        rendered.write_text(_text(name).replace("@REPO_ROOT@", root), encoding="utf-8")
        paths.append(str(rendered))
    modes = [["verify"]]
    if os.environ.get("XDG_RUNTIME_DIR"):
        modes.append(["--user", "verify"])
    for mode in modes:
        result = subprocess.run(
            ["systemd-analyze", *mode, *paths], capture_output=True, text=True, check=False, timeout=60
        )
        assert result.returncode == 0, (mode, result.stderr)
        assert "learn-ukrainian-context-guard" not in result.stderr
        assert "learn-ukrainian-lane-relaunch" not in result.stderr
