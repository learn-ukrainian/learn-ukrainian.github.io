from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import AgentTimeoutError
from ai_agent_bridge import _channels, _db, _inbox
from ai_agent_bridge._orphan_recovery import (
    RecoveryCandidate,
    RecoveryResult,
    recover_orphan_commit,
)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".venv" / "bin").mkdir(parents=True)
    ruff = repo / ".venv" / "bin" / "ruff"
    ruff.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    ruff.chmod(0o755)
    (repo / "scripts").mkdir()
    (repo / "tests").mkdir()
    (repo / "docs").mkdir()
    (repo / "plans").mkdir()
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md", ".venv/bin/ruff")
    _git(repo, "commit", "-m", "init")
    return repo


def _candidate(*bodies: str) -> RecoveryCandidate:
    return RecoveryCandidate(
        delivery_id="delivery-123",
        thread_id="thread-456",
        latest_message_body=bodies[-1],
        thread_bodies=tuple(bodies),
    )


def test_recover_orphan_commit_commits_matching_allowed_files(tmp_path: Path):
    repo = _init_repo(tmp_path)
    target = repo / "scripts" / "ai_agent_bridge"
    target.mkdir()
    changed = target / "_inbox.py"
    changed.write_text("print('ok')\n", encoding="utf-8")

    result = recover_orphan_commit(
        _candidate("Hook into scripts/ai_agent_bridge/_inbox.py"),
        repo_root=repo,
    )

    assert result.commit_sha
    assert result.changed_files == ("scripts/ai_agent_bridge/_inbox.py",)
    assert _git(repo, "status", "--short").stdout == ""
    message = _git(repo, "log", "-1", "--pretty=%B").stdout
    assert "[TIMEOUT RECOVERY] Hook into scripts/ai_agent_bridge/_inbox.py" in message
    assert "Recovery of stranded Codex work from delivery delivery-123" in message


def test_recover_orphan_commit_is_idempotent_on_clean_tree(tmp_path: Path):
    repo = _init_repo(tmp_path)

    result = recover_orphan_commit(
        _candidate("Touch scripts/ai_agent_bridge/_inbox.py"),
        repo_root=repo,
    )

    assert result.commit_sha is None
    assert result.reason == "clean-tree"


def test_recover_orphan_commit_rejects_files_outside_allowed_roots(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (repo / "starlight").mkdir()
    (repo / "starlight" / "page.mdx").write_text("nope\n", encoding="utf-8")

    result = recover_orphan_commit(
        _candidate("Touch starlight/page.mdx"),
        repo_root=repo,
    )

    assert result.commit_sha is None
    assert result.reason == "outside-allowed-scope"


def test_recover_orphan_commit_rejects_when_ruff_fails(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (repo / "scripts" / "task.py").write_text("print('bad')\n", encoding="utf-8")

    with patch("ai_agent_bridge._orphan_recovery._run_ruff", return_value=False):
        result = recover_orphan_commit(
            _candidate("Touch scripts/task.py"),
            repo_root=repo,
        )

    assert result.commit_sha is None
    assert result.reason == "ruff-failed"
    assert "?? scripts/" in _git(repo, "status", "--short").stdout


def test_recover_orphan_commit_rejects_when_pre_commit_blocks(tmp_path: Path):
    repo = _init_repo(tmp_path)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    (repo / "scripts" / "task.py").write_text("print('ok')\n", encoding="utf-8")

    result = recover_orphan_commit(
        _candidate("Touch scripts/task.py"),
        repo_root=repo,
    )

    assert result.commit_sha is None
    assert result.reason == "pre-commit-failed"
    assert _git(repo, "diff", "--cached", "--name-only", check=False).stdout == ""


@pytest.fixture(autouse=True)
def isolate_db(tmp_path: Path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch(
        "ai_agent_bridge._db.DB_PATH", db_file
    ):
        _db.init_db()
        yield


@patch("ai_agent_bridge._inbox.runtime_invoke")
@patch(
    "ai_agent_bridge._inbox._maybe_recover_orphan_commit",
    return_value=RecoveryResult(commit_sha="abc123", reason=None),
)
def test_run_inbox_timeout_recovery_marks_delivery_delivered(
    _mock_recovery,
    mock_invoke,
):
    _channels.create_channel("reviews")
    post = _channels.post(
        "reviews",
        "user",
        "Edit scripts/ai_agent_bridge/_inbox.py",
        to_agents=["codex"],
        auto_snapshot=False,
        mode="workspace-write",
    )
    mock_invoke.side_effect = AgentTimeoutError("codex", 900)

    summary = _inbox.run_inbox("codex")

    assert summary.deliveries_delivered == 1
    assert summary.aborted is False
    conn = _db.get_db()
    try:
        row = conn.execute(
            "SELECT status, error FROM deliveries WHERE delivery_id = ?",
            (post["delivery_ids"][0],),
        ).fetchone()
    finally:
        conn.close()
    assert row["status"] == "delivered"
    assert row["error"] == "timeout-recovered:abc123"
