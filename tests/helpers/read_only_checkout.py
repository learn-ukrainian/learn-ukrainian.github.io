"""Minimal Git checkout used by read-only dispatch tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _sanitize_git_env(monkeypatch) -> None:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def seed_read_only_checkout(repo: Path, monkeypatch) -> None:
    _sanitize_git_env(monkeypatch)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True, capture_output=True, timeout=30)
    (repo / ".gitignore").write_text(
        ".agent/\n.mcp/servers/message-broker/*.log\nscratch/\n.cache/\nbatch_state/\n.pytest_cache/\n"
        ".pytest_breadcrumbs/\n.ruff_cache/\n__pycache__/\n.runtime/\n*.sqlite3-wal\n*.sqlite3-shm\n*.sqlite3-journal\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "tracked.txt"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True, timeout=30)

AGY_UKRAINIAN_REVIEW = {
    "mode": "read-only",
    "advisory_exemption": {
        "model_id": "gemini-3.8-flash-high",
        "task_family": "ukrainian-review",
        "mode": "read-only",
        "classified_paths": [],
    },
}
