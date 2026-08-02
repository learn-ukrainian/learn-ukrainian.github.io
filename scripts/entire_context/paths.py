"""Shared runtime paths for the rebuildable Entire context projection."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.fleet_comms.paths import default_plane_root

DEFAULT_STATE_RELATIVE = Path("batch_state") / "entire-context" / "v1"
DEFAULT_DB_NAME = "context-links.sqlite3"
DEFAULT_PROVIDER_STATUS_NAME = "provider-status.json"
ENV_DB = "ENTIRE_CONTEXT_DB"
ENV_ACP_ROOT = "ENTIRE_CONTEXT_ACP_ROOT"


def shared_repository_root(cwd: Path | str) -> Path:
    """Return the primary checkout shared by all linked worktrees.

    Git's common directory is the stable local join: in a linked worktree it
    points back to the primary checkout's ``.git`` directory. A non-repository
    caller safely falls back to its own working directory.
    """
    root = Path(cwd).expanduser().resolve()
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return root
    if completed.returncode != 0:
        return root
    common_dir = Path(completed.stdout.strip()).expanduser().resolve()
    return common_dir.parent if common_dir.name == ".git" else root


def state_directory(cwd: Path | str) -> Path:
    return shared_repository_root(cwd) / DEFAULT_STATE_RELATIVE


def projection_path(cwd: Path | str, explicit: Path | str | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get(ENV_DB)
    if configured:
        return Path(configured).expanduser().resolve()
    return state_directory(cwd) / DEFAULT_DB_NAME


def acp_root(cwd: Path | str, explicit: Path | str | None = None) -> Path:
    """Resolve the shared canonical ACP plane used by Fleet services.

    Caller-supplied and Entire-specific overrides win.  The default delegates
    to Fleet Comms' canonical resolver so the CLI, API, primary checkout, and
    linked worktrees cannot drift onto different receipt databases.
    """
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get(ENV_ACP_ROOT)
    if configured:
        return Path(configured).expanduser().resolve()
    return default_plane_root(repo_root=Path(cwd))


def provider_status_path(cwd: Path | str) -> Path:
    return state_directory(cwd) / DEFAULT_PROVIDER_STATUS_NAME
