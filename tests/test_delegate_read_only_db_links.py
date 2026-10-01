"""Read-only dispatches that read the local databases must not create them (#9122).

A sparse dispatch worktree has no tracked ``data/*.db``. ``_ensure_worktree``
links the primary checkout's databases into ``data/``, but used to do so before
``git sparse-checkout init --cone``, which deletes ``data/`` together with the
ignored links. A worker that then ran ``sqlite3.connect('data/vesum.db')`` from
the worktree created an empty file, read nothing, and the read-only guard
failed the task with ``read-only checkout mutation detected: data/vesum.db``.

These tests drive the real worktree creation and sparse profile in a throwaway
repository; they need no network, no ``origin``, and no host database.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

_DATABASES = ("vesum.db", "sources.db")

# What dispatch records for a read-only Gemini Flash Ukrainian review (#9275).
_AGY_UKRAINIAN_REVIEW = {
    "mode": "read-only",
    "advisory_exemption": {
        "model_id": "gemini-3.8-flash-high",
        "task_family": "ukrainian-review",
        "review_profile": None,
        "mode": "read-only",
        "classified_paths": [],
    },
}


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    return proc.stdout.strip()


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    return tasks_dir


@pytest.fixture
def primary(tmp_path, monkeypatch) -> Path:
    """A primary checkout shaped like production: sparse-excluded data trees, ignored DBs."""
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    repo = (tmp_path / "primary").resolve()
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / ".gitignore").write_text("*.db\n.worktrees/\nbatch_state/\n", encoding="utf-8")
    for relative in ("data/projects/f.txt", "data/lexicon/f.txt", "data/datasets/f.txt", "scripts/f.txt"):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{relative}\n", encoding="utf-8")
    (repo / "data" / "readme.txt").write_text("data root\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    for name in _DATABASES:
        with sqlite3.connect(repo / "data" / name) as conn:
            conn.execute("CREATE TABLE proof (value TEXT)")
            conn.execute("INSERT INTO proof VALUES (?)", (f"primary {name}",))
        conn.close()
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    return repo


def _dispatch_path(primary: Path, task_id: str) -> Path:
    return primary / ".worktrees" / "dispatch" / "agy" / task_id


def _assert_primary_links(worktree: Path, primary: Path) -> None:
    for name in _DATABASES:
        link = worktree / "data" / name
        assert link.is_symlink(), f"data/{name} is not linked into the sparse worktree"
        assert link.resolve() == (primary / "data" / name).resolve()


def test_sparse_detached_worktree_keeps_primary_database_links(primary: Path) -> None:
    head = _git(primary, "rev-parse", "HEAD")
    worktree = _dispatch_path(primary, "review-9122-links")

    path, branch, telemetry = delegate._ensure_worktree(
        agent="agy",
        task_id="review-9122-links",
        raw_path=str(worktree),
        resolved_base_sha=head,
        detached=True,
    )

    assert branch is None
    assert telemetry["sparse"]["excluded"] == ["data/lexicon", "data/projects"]
    # The cone dropped the excluded data trees; the links sit beside the kept ones.
    assert sorted(entry.name for entry in (path / "data").iterdir()) == [
        "datasets",
        "readme.txt",
        "sources.db",
        "vesum.db",
    ]
    _assert_primary_links(path, primary)


def test_reused_sparse_worktree_restores_primary_database_links(primary: Path) -> None:
    head = _git(primary, "rev-parse", "HEAD")
    worktree = _dispatch_path(primary, "impl-9122-reuse")
    path, _branch, _telemetry = delegate._ensure_worktree(
        agent="agy",
        task_id="impl-9122-reuse",
        raw_path=str(worktree),
        resolved_base_sha=head,
    )
    for name in _DATABASES:
        (path / "data" / name).unlink()

    reused, _branch, telemetry = delegate._ensure_worktree(
        agent="agy",
        task_id="impl-9122-reuse",
        raw_path=str(worktree),
        resolved_base_sha=head,
    )

    assert telemetry["reused"] is True
    assert reused == path
    _assert_primary_links(reused, primary)


_WORKER_LOOKUP = """
import json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.verification.vesum import get_vesum_connection
from scripts.wiki.sources_db import _open_conn

values = []
# The ad-hoc query the AGY reviewer ran, relative to its worktree cwd.
for name in ("data/vesum.db", "data/sources.db"):
    conn = sqlite3.connect(name)
    values.append(conn.execute("SELECT value FROM proof").fetchone()[0])
    conn.close()
# The repository's read-only openers given the same relative paths.
with get_vesum_connection("data/vesum.db") as conn:
    values.append(conn.execute("SELECT value FROM proof").fetchone()[0])
conn = _open_conn(Path("data/sources.db"), read_only=True)
values.append(conn.execute("SELECT value FROM proof").fetchone()[0])
conn.close()
print(json.dumps(values))
"""


def test_read_only_sparse_dispatch_with_sources_lookup_ends_done(primary: Path, tmp_tasks_dir) -> None:
    """AC-02: the worker's database lookups read the primary data and leave the checkout clean."""
    head = _git(primary, "rev-parse", "HEAD")
    task_id = "review-9122-lookup"
    worktree, _branch, _telemetry = delegate._ensure_worktree(
        agent="agy",
        task_id=task_id,
        raw_path=str(_dispatch_path(primary, task_id)),
        resolved_base_sha=head,
        detached=True,
    )
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(worktree), **_AGY_UKRAINIAN_REVIEW})
    repo_root = str(Path(__file__).resolve().parent.parent)
    lookups: list[str] = []

    def worker_reads_databases(*_args, **_kwargs):
        proc = subprocess.run(
            [sys.executable, "-c", _WORKER_LOOKUP, repo_root],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        lookups.append(proc.stdout.strip())
        return type(
            "_Result",
            (),
            {
                "ok": True,
                "response": "VERDICT: PASS",
                "stderr_excerpt": None,
                "returncode": 0,
                "rate_limited": False,
                "model": "gemini-3.8-flash-high",
                "effort": "high",
                "cli_version": "fixture",
            },
        )()

    with patch("agent_runtime.runner.invoke", side_effect=worker_reads_databases):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="agy",
            prompt="Review the sentences with VESUM lookups; do not edit the tree.",
            mode="read-only",
            cwd_str=str(worktree),
            model=None,
            hard_timeout=60,
        )

    state = delegate._read_state(state_path)
    assert lookups == ['["primary vesum.db", "primary sources.db", "primary vesum.db", "primary sources.db"]']
    assert rc == 0
    assert state is not None
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    _assert_primary_links(worktree, primary)


@pytest.mark.parametrize("name", _DATABASES)
def test_read_only_database_openers_never_create_a_missing_file(tmp_path: Path, name: str) -> None:
    """With no database present, the repository openers fail typed and create nothing."""
    from scripts.verification.vesum import get_vesum_connection
    from scripts.wiki.sources_db import _open_conn

    missing = tmp_path / "data" / name
    missing.parent.mkdir()

    if name == "vesum.db":
        with pytest.raises(FileNotFoundError, match="VESUM database not found"), get_vesum_connection(missing):
            pass
    else:
        with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
            _open_conn(missing, read_only=True)

    assert not missing.exists()
    assert list(missing.parent.iterdir()) == []
