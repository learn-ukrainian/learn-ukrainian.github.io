"""Primary bare drift: heal-then-proceed (Fable layout A; #5578 inverted)."""

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


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=_clean_env(),
    )


def test_heal_primary_bare_if_needed_resets_core_bare(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-b", "main", str(repo))
    _git("-C", str(repo), "config", "core.bare", "true")
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "core.bare"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        ).stdout.strip()
        == "true"
    )

    result = wc.heal_primary_bare_if_needed(repo)
    assert result["healed"] is True
    assert result["was_bare"] is True
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "core.bare"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        ).stdout.strip()
        == "false"
    )
    # worktreeConfig asserted
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "extensions.worktreeConfig"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        ).stdout.strip()
        == "true"
    )


def test_primary_checkout_dirty_status_heals_bare_then_reports_status(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-b", "main", str(repo))
    (repo / "README").write_text("x\n", encoding="utf-8")
    _git("-C", str(repo), "add", "README")
    _git("-C", str(repo), "config", "user.email", "t@example.com")
    _git("-C", str(repo), "config", "user.name", "t")
    _git("-C", str(repo), "commit", "-m", "init")
    # Dirty after commit
    (repo / "README").write_text("dirty\n", encoding="utf-8")
    # Simulate bare pollution
    _git("-C", str(repo), "config", "core.bare", "true")

    status = wc.primary_checkout_dirty_status(repo)
    assert status["bare_primary"] is False
    assert status["bare_healed"] is True
    assert status["dirty"] is True
    assert status["dirty_count"] >= 1
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "core.bare"],
            capture_output=True,
            text=True,
            env=_clean_env(),
            check=False,
        ).stdout.strip()
        == "false"
    )
