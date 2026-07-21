"""Bare primary checkout is not dirty-checkable via git status."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.guardrails import worktree_containment as wc

_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _git(*args: str) -> None:
    subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
    )


def test_primary_checkout_dirty_status_treats_bare_as_clean(tmp_path: Path, monkeypatch) -> None:
    bare = tmp_path / "primary.git"
    _git("init", "--bare", str(bare))
    monkeypatch.setattr(wc, "resolve_main_root", lambda start=None: bare)
    monkeypatch.setattr(wc, "current_branch", lambda root: "main")

    # _run_git uses sanitized_git_env — still pass bare path via resolve_main_root.
    status = wc.primary_checkout_dirty_status(bare)
    assert status["dirty"] is False
    assert status["dirty_count"] == 0
    assert status["entries"] == []
    assert status.get("bare_primary") is True
