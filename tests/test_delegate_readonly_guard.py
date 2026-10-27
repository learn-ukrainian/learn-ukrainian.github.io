"""Tests for read-only dispatch checkout mutation guard (#7124).

Dedicated test module to keep CI fastlane slim and avoid pulling heavy
dependencies from tests/test_delegate.py.

- Scoping read-only snapshot off .worktrees/ entirely
- Preserving real worker failures alongside read-only mutation diagnostics
- Negative returncode signal decoding
"""

from __future__ import annotations

import contextlib
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import agent_runtime.runner as runner

# ---------------------------------------------------------------------------
# #8516: read-only dispatch must not be able to write into the checkout
# (AC-02 post-run guard; AC-03 per-lane coverage; AC-01 agy cwd pin)
# ---------------------------------------------------------------------------


# kimi is absent: Kimi seats never run read-only (the worker refuses them before invocation).
# --- #8516 AC-01: runner cwd pin (agy re-anchors its cwd after spawn) -------

_needs_procfs = pytest.mark.skipif(not Path("/proc").is_dir(), reason="cwd pin reads /proc (Linux-only)")


@contextlib.contextmanager
def _sleeping_child(cwd: Path, *argv_prefix: str):
    argv = list(argv_prefix) or ["sleep", "30"]
    proc = subprocess.Popen(argv, cwd=str(cwd))
    try:
        yield proc
    finally:
        proc.kill()
        proc.wait(timeout=10)


@_needs_procfs
def test_read_only_agy_cwd_pin_scoping(tmp_path):
    """The pin applies only to dispatch (task_id set) read-only agy spawns."""
    with _sleeping_child(tmp_path) as proc:
        assert runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id=None) is None
        assert (
            runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="codex", task_id="t") is None
        )
        assert runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="workspace-write", agent_name="agy", task_id="t") is None
        pin = runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None


@_needs_procfs
def test_read_only_agy_cwd_pin_verifies_child_settled_inside(tmp_path):
    """A child anchored in the pinned tree verifies on the first check."""
    with _sleeping_child(tmp_path) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=tmp_path, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        assert pin.check() is None
        assert pin.verified is True


@_needs_procfs
def test_read_only_agy_cwd_pin_fails_when_child_anchors_outside(tmp_path, monkeypatch):
    """A child still outside the pinned tree when grace closes fails cwd_unpinned."""
    monkeypatch.setenv(runner._CWD_PIN_GRACE_ENV, "0.2")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    with _sleeping_child(elsewhere) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=pinned, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        assert pin.check() is None  # still inside the grace window
        time.sleep(0.4)
        assert pin.check() == "cwd_unpinned"
        assert pin.last_observed is not None


@_needs_procfs
def test_read_only_agy_cwd_pin_allows_late_settle(tmp_path, monkeypatch):
    """A child that starts in scratch and then settles into the pin passes.

    Mirrors the 2026-09-24 agy evidence on #8516: the CLI starts in its own
    scratch directory and only later finds the cwd it was given.
    """
    monkeypatch.setenv(runner._CWD_PIN_GRACE_ENV, "120")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    argv = ["bash", "-c", 'sleep 0.5; cd "$1" && exec sleep 30', "_", str(pinned)]
    with _sleeping_child(elsewhere, *argv) as proc:
        pin = runner._ChildCwdPin.start(proc=proc, cwd=pinned, mode="read-only", agent_name="agy", task_id="t")
        assert pin is not None
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and not pin.verified:
            assert pin.check() is None
            time.sleep(0.2)
        assert pin.verified is True
