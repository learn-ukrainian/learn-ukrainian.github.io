"""Worktree-aware project interpreter resolution for subprocess tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def project_python() -> Path:
    """Return the shared project interpreter when tests run in a worktree."""
    local = _REPO_ROOT / ".venv" / "bin" / "python"
    if local.is_file():
        return local

    try:
        common_dir = subprocess.check_output(
            [
                "git",
                "-C",
                str(_REPO_ROOT),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as error:
        raise RuntimeError("Could not locate the project's Git common directory.") from error

    canonical = Path(common_dir).parent / ".venv" / "bin" / "python"
    if canonical.is_file():
        return canonical

    raise RuntimeError(
        "Project interpreter missing from this checkout and its canonical Git checkout: "
        f"{local}, {canonical}"
    )
