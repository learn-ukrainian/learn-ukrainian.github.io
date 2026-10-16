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


def test_guard_timer_is_persistent_every_five_minutes() -> None:
    timer = _text("learn-ukrainian-context-guard.timer")
    assert "OnCalendar=*:0/5\n" in timer
    assert "Unit=learn-ukrainian-context-guard.service\n" in timer
    assert "WantedBy=timers.target\n" in timer
    service = _text("learn-ukrainian-context-guard.service")
    assert "Type=oneshot\n" in service
    assert "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.ops.context_guard tick\n" in service


def test_relaunch_is_a_boot_oneshot_that_scopes_the_tmux_server() -> None:
    service = _text("learn-ukrainian-lane-relaunch.service")
    assert "Type=oneshot\n" in service
    assert "WantedBy=default.target\n" in service
    assert "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.ops.lane_relaunch --server-scope\n" in service
    assert "WorkingDirectory=@REPO_ROOT@\n" in service
    # Ordering after default.target would be a cycle for a unit default.target wants.
    assert "After=default.target" not in service


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
