"""Tests for the core.bare repo-health canary (#2842)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit.check_core_bare import check_core_bare, main


def _init_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def _core_bare(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "config", "--get", "core.bare"],
        capture_output=True,
        text=True,
    ).stdout.strip()


def _set_bare(repo: Path, value: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "core.bare", value],
        check=True,
    )


def test_ok_when_core_bare_false(tmp_path):
    repo = _init_repo(tmp_path)
    ok, message = check_core_bare(repo, fix=False)
    assert ok
    assert "ok" in message


def test_detects_core_bare_true_without_fix(tmp_path):
    repo = _init_repo(tmp_path)
    _set_bare(repo, "true")
    ok, message = check_core_bare(repo, fix=False)
    assert not ok
    assert "BROKEN" in message
    # check-only must NOT mutate the repo
    assert _core_bare(repo) == "true"


def test_fix_resets_core_bare_true(tmp_path):
    repo = _init_repo(tmp_path)
    _set_bare(repo, "true")
    ok, message = check_core_bare(repo, fix=True)
    assert ok
    assert "reset" in message
    assert _core_bare(repo) == "false"


def test_main_exit_codes(tmp_path):
    repo = _init_repo(tmp_path)
    # healthy → exit 0
    assert main(["--repo", str(repo), "--quiet"]) == 0
    # drifted, no --fix → exit 1, still broken
    _set_bare(repo, "true")
    assert main(["--repo", str(repo)]) == 1
    assert _core_bare(repo) == "true"
    # drifted, --fix → exit 0, healed and stays healed
    assert main(["--repo", str(repo), "--fix"]) == 0
    assert _core_bare(repo) == "false"
    assert main(["--repo", str(repo)]) == 0
