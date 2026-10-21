"""Tests for the primary-venv integrity probe (#6830).

scripts/audit/check_venv_integrity.py — detection ONLY of an empty/broken
primary venv: (a) a curated set of lightweight core modules failing to
import, (b) console-script launchers whose embedded interpreter doesn't
match the venv's own. No repair path exists here; a detection is always an
ALERT (mirrors check_node_modules_integrity.py's posture and test shape).
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.audit.check_venv_integrity import (
    find_broken_console_scripts,
)


def _make_fake_venv(tmp_path: Path, name: str = "venv") -> tuple[Path, Path]:
    """A minimal venv: bin/python + bin/python3 symlinked to THIS interpreter,
    mirroring how `python -m venv` / `uv venv` actually lay out bin/ (the
    venv's own python is normally a symlink OUT to the base interpreter, not
    a copy — the whole reason find_broken_console_scripts cannot use a
    "resolves inside venv_dir" test)."""
    venv_dir = tmp_path / name
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").symlink_to(Path(sys.executable))
    (bin_dir / "python3").symlink_to(Path("python"))
    return venv_dir, bin_dir


def _write_exec_trick_launcher(bin_dir: Path, name: str, interpreter: Path) -> Path:
    """Pip's long-path launcher form — matches the real broken pytest/py.test/
    cbor2 scripts found on the primary venv verbatim (#6830 live finding)."""
    script = bin_dir / name
    script.write_text(f"#!/bin/sh\n'''exec' '{interpreter}' \"$0\" \"$@\"\n' '''\n# -*- coding: utf-8 -*-\nprint('ok')\n")
    script.chmod(0o755)
    return script


# ---------------------------------------------------------------------------
# console-script shebang detection
# ---------------------------------------------------------------------------


def test_launcher_pointing_at_deleted_path_is_detected(tmp_path: Path) -> None:
    """Reproduces the live #6830 finding verbatim: the exec-trick form
    pointing at a python3 under a worktree venv that no longer exists."""
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    deleted = tmp_path / "some-worktree" / ".venv" / "bin" / "python3"
    _write_exec_trick_launcher(bin_dir, "pytest", deleted)

    found = find_broken_console_scripts(venv_dir)
    assert len(found) == 1
    assert found[0] == {"script": "pytest", "interpreter": str(deleted), "exists": False}


# ---------------------------------------------------------------------------
# sentinel import detection
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# combined probe
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# attribution: running dispatches recorded on the alert event
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
