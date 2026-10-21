"""Read-only git under the three #8874 entry points never takes optional locks.

A read-only ``git status`` refreshes stale index stat data and rewrites the
index under ``index.lock``; a caller killed mid-write leaves the lock behind.
``GIT_OPTIONAL_LOCKS=0`` turns that refresh off for a process and every child.
The Monitor API, the project-state reporter and the reconcile sweep set it at
their entry points. These tests run plain ``git status`` (no flag) as a child
of each entry point against a repository whose index is stale, and check the
index bytes. An explicit operator value wins, so ``1`` lets the refresh happen.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.guardrails.delegate_ownership import OwnershipLedger
from scripts.orchestration import reconcile_sweep

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VAR = "GIT_OPTIONAL_LOCKS"
_GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", _VAR)


@pytest.fixture
def stale_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A committed repo whose tracked file is newer than its index entry; git env isolated."""
    for key in _GIT_ENV_DROP:
        monkeypatch.delenv(key, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "fixture")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "fixture@example.invalid")
    repo = tmp_path / "repo"
    repo.mkdir()
    tracked = repo / "tracked.txt"
    tracked.write_text("content\n", encoding="utf-8")
    for args in (("init", "-q", "--template="), ("add", "tracked.txt"), ("commit", "-q", "-m", "fixture")):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)
    index = repo / ".git" / "index"
    past = index.stat().st_mtime - 120
    os.utime(index, (past, past))
    os.utime(tracked, (past + 60, past + 60))
    return repo


def _index(repo: Path) -> tuple[int, bytes]:
    index = repo / ".git" / "index"
    return index.stat().st_mtime_ns, index.read_bytes()


def _env(prior: str | None) -> dict[str, str]:
    env = dict(os.environ)
    if prior is not None:
        env[_VAR] = prior
    return env


@pytest.mark.parametrize(("prior", "refreshed"), [(None, True), ("1", True), ("0", False)])
def test_variable_alone_decides_whether_status_rewrites_the_index(
    stale_repo: Path, prior: str | None, refreshed: bool
) -> None:
    """Control: the fixture really is stale, and the variable alone stops the rewrite."""
    before = _index(stale_repo)
    subprocess.run(["git", "status", "--porcelain"], cwd=stale_repo, env=_env(prior), check=True, timeout=30)
    assert (_index(stale_repo) != before) is refreshed


@pytest.mark.parametrize(("prior", "expected"), [(None, "0"), ("1", "1")])
def test_monitor_api_import_disables_optional_locks_for_children(
    stale_repo: Path, prior: str | None, expected: str
) -> None:
    script = (
        "import os, subprocess, sys\n"
        "import scripts.api.main\n"
        "print(os.environ.get('GIT_OPTIONAL_LOCKS'))\n"
        "subprocess.run(['git', 'status', '--porcelain'], cwd=sys.argv[1], check=True, timeout=30)\n"
    )
    before = _index(stale_repo)
    proc = subprocess.run(
        [sys.executable, "-c", script, str(stale_repo)],
        cwd=_REPO_ROOT,
        env=_env(prior),
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert proc.stdout.splitlines()[0] == expected
    assert (_index(stale_repo) == before) is (expected == "0")


@pytest.mark.parametrize(("prior", "expected"), [(None, "0"), ("1", "1")])
def test_project_state_reporter_exports_variable_to_its_child(
    stale_repo: Path, tmp_path: Path, prior: str | None, expected: str
) -> None:
    """The wrapper execs ``$LEARN_UKRAINIAN_PYTHON``; a stand-in records what it inherits."""
    stand_in = tmp_path / "python"
    stand_in.write_text(
        f'#!/usr/bin/env bash\nprintf "%s\\n" "$GIT_OPTIONAL_LOCKS"\nexec git -C "{stale_repo}" status --porcelain\n',
        encoding="utf-8",
    )
    stand_in.chmod(0o755)
    env = _env(prior)
    env["LEARN_UKRAINIAN_PYTHON"] = str(stand_in)
    before = _index(stale_repo)
    proc = subprocess.run(
        ["bash", str(_REPO_ROOT / "scripts/orchestration/run_project_state_reporter.sh")],
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert proc.stdout.splitlines()[0] == expected
    assert (_index(stale_repo) == before) is (expected == "0")


@pytest.mark.parametrize(("prior", "expected"), [(None, "0"), ("1", "1")])
def test_reconcile_sweep_runs_git_children_without_optional_locks(
    stale_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prior: str | None, expected: str
) -> None:
    if prior is not None:
        monkeypatch.setenv(_VAR, prior)
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    seen: list[str | None] = []

    def _release(_ledger: object) -> list[str]:
        seen.append(os.environ.get(_VAR))
        subprocess.run(["git", "status", "--porcelain"], cwd=stale_repo, check=True, timeout=30)
        return []

    monkeypatch.setattr(reconcile_sweep.dispatch_settle, "release_inactive_claims", _release)
    before = _index(stale_repo)
    reconcile_sweep.run_reconcile_sweep(
        apply=True, task_dir=task_dir, ledger=OwnershipLedger(tmp_path / "own.sqlite3", task_state_dir=task_dir)
    )

    assert seen == [expected]
    assert (_index(stale_repo) == before) is (expected == "0")
    assert os.environ.get(_VAR) == prior
