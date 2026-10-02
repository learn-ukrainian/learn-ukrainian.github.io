"""Read-only dispatches that look up the local databases (#9122).

The stray ``data/vesum.db`` and ``data/sources.db`` that failed AGY read-only
reviews were created by the reviewer's own ad-hoc shell commands, which ran
``sqlite3.connect('data/vesum.db')`` relative to the sparse dispatch worktree.
That is a real checkout write, and the read-only guard must keep flagging it
without the primary database changing. A lookup through the ``sources`` MCP
resolves the primary's databases through the one resolver per database, opens
them read-only, and leaves the worktree untouched; with no database present it
fails typed and creates nothing.

These tests drive the real worktree creation, sparse profile, read-only guard
and MCP wire handler in a throwaway repository; they need no network, no
``origin`` and no host database.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

REPO_ROOT = Path(__file__).resolve().parent.parent
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


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    monkeypatch.delenv("LU_SOURCES_DB", raising=False)
    monkeypatch.setenv("LU_MCP_SOURCES_LOG_DIR", str(tmp_path / "mcp-logs"))
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
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    with sqlite3.connect(repo / "data" / "vesum.db") as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.execute("INSERT INTO forms VALUES ('читати', 'читати', 'verb', 'verb:imperf:inf')")
    conn.close()
    with sqlite3.connect(repo / "data" / "sources.db") as conn:
        conn.execute("CREATE TABLE textbooks (chunk_id TEXT, title TEXT, text TEXT)")
        conn.execute("CREATE TABLE literary_texts (chunk_id TEXT, title TEXT, text TEXT)")
        conn.execute("INSERT INTO textbooks VALUES ('chunk-1', 'Fixture', 'Primary source text')")
    conn.close()
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    return repo


def _sparse_dispatch_worktree(primary: Path, task_id: str) -> Path:
    worktree, branch, telemetry = delegate._ensure_worktree(
        agent="agy",
        task_id=task_id,
        raw_path=str(primary / ".worktrees" / "dispatch" / "agy" / task_id),
        resolved_base_sha=_git(primary, "rev-parse", "HEAD"),
        detached=True,
    )
    assert branch is None
    assert telemetry["sparse"]["excluded"] == ["data/lexicon", "data/projects"]
    return worktree


def _run_read_only_worker(worktree: Path, task_id: str, worker_script: str, *args: str) -> tuple[int, dict, str]:
    """Run ``worker_script`` as the agy worker of a read-only dispatch, with the worktree as cwd."""
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "cwd": str(worktree), **_AGY_UKRAINIAN_REVIEW})
    outputs: list[str] = []

    def worker(*_args, **_kwargs):
        proc = subprocess.run(
            [sys.executable, "-c", worker_script, *args],
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        outputs.append(proc.stdout.strip())
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

    with patch("agent_runtime.runner.invoke", side_effect=worker):
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
    assert state is not None
    assert len(outputs) == 1
    return rc, state, outputs[0]


# The commands the AGY reviewers ran in review-8843-sent-1 and -5: ad-hoc
# Python opening the database relative to the worktree cwd.
_RELATIVE_OPEN = """
import sqlite3, sys
conn = sqlite3.connect("data/" + sys.argv[1])
if sys.argv[2] == "write":
    conn.execute("CREATE TABLE IF NOT EXISTS worker_write (value TEXT)")
    conn.execute("INSERT INTO worker_write VALUES ('from the read-only worker')")
    conn.commit()
else:
    conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
conn.close()
print("opened")
"""


@pytest.mark.parametrize("action", ["write", "read"])
@pytest.mark.parametrize("name", _DATABASES)
def test_read_only_sparse_dispatch_flags_a_relative_database_open(
    primary: Path, tmp_tasks_dir, name: str, action: str
) -> None:
    """A worker that opens ``data/<db>`` relative to its worktree is flagged; the primary is untouched."""
    primary_db = primary / "data" / name
    before = _digest(primary_db)
    task_id = f"review-9122-{action}-{name.removesuffix('.db')}"
    worktree = _sparse_dispatch_worktree(primary, task_id)

    rc, state, output = _run_read_only_worker(worktree, task_id, _RELATIVE_OPEN, name, action)

    assert output == "opened"
    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == [f"data/{name}"]
    assert state["last_error"] == f"read-only checkout mutation detected: data/{name}"
    # The open created a separate file in the worktree; nothing reached the primary.
    created = worktree / "data" / name
    assert created.is_file() and not created.is_symlink()
    assert created.resolve() != primary_db.resolve()
    assert _digest(primary_db) == before


# A worker that looks words and chunks up through the real sources MCP wire
# handler. The server code lives in this test checkout, so its resolvers are
# anchored at the fixture dispatch worktree (cwd) the way they are anchored at
# the server's own checkout in production; resolution itself is unpatched.
_SOURCES_MCP_LOOKUP = """
import asyncio, importlib.util, json, sys
from pathlib import Path

repo, worktree = Path(sys.argv[1]), Path.cwd()
sys.path[:0] = [str(repo), str(repo / "scripts")]
from mcp.types import CallToolRequestParams

import scripts.rag.config as rag_config
from scripts.verification import vesum
from wiki import sources_db

vesum_db = rag_config._resolve_vesum_db_path(worktree / "data" / "vesum.db", worktree)
rag_config.VESUM_DB_PATH = vesum.VESUM_DB_PATH = vesum_db
sources_db.PROJECT_ROOT = worktree
sources_db.SOURCES_DB_PATH = worktree / "data" / "sources.db"
spec = importlib.util.spec_from_file_location("sources_server", repo / ".mcp" / "servers" / "sources" / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

results = {}
for tool, arguments in (("verify_words", {"words": ["читати"]}), ("get_chunk_context", {"chunk_id": "chunk-1"})):
    result = asyncio.run(server._on_call_tool(None, CallToolRequestParams(name=tool, arguments=arguments)))
    results[tool] = {"is_error": result.is_error, "text": result.content[0].text}
print(json.dumps(results, ensure_ascii=False))
"""


def test_read_only_sparse_dispatch_with_sources_mcp_lookup_ends_done(primary: Path, tmp_tasks_dir) -> None:
    """AC-02: real ``sources`` MCP lookups read the primary data and leave the checkout clean."""
    before = {name: _digest(primary / "data" / name) for name in _DATABASES}
    task_id = "review-9122-sources-mcp"
    worktree = _sparse_dispatch_worktree(primary, task_id)

    rc, state, output = _run_read_only_worker(worktree, task_id, _SOURCES_MCP_LOOKUP, str(REPO_ROOT))

    results = json.loads(output)
    assert results["verify_words"]["is_error"] is False
    assert "**читати** — FOUND" in results["verify_words"]["text"]
    assert results["get_chunk_context"]["is_error"] is False
    assert "Primary source text" in results["get_chunk_context"]["text"]
    assert rc == 0
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert state["last_error"] is None
    assert sorted(path.name for path in (worktree / "data").iterdir()) == ["datasets"]
    assert {name: _digest(primary / "data" / name) for name in _DATABASES} == before


def test_sources_mcp_lookup_without_databases_fails_typed_and_creates_nothing(primary: Path, tmp_tasks_dir) -> None:
    """With no database anywhere, the lookups fail typed and no file appears in either checkout."""
    for name in _DATABASES:
        (primary / "data" / name).unlink()
    task_id = "review-9122-sources-absent"
    worktree = _sparse_dispatch_worktree(primary, task_id)

    rc, state, output = _run_read_only_worker(worktree, task_id, _SOURCES_MCP_LOOKUP, str(REPO_ROOT))

    results = json.loads(output)
    assert results["verify_words"] == {"is_error": True, "text": "Tool call failed: verify_words."}
    assert results["get_chunk_context"]["text"] == "Sources database not found."
    assert rc == 0
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert sorted(path.name for path in (worktree / "data").iterdir()) == ["datasets"]
    assert sorted((primary / "data").glob("*.db")) == []


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
