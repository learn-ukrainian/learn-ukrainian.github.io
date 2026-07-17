from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ai_agent_bridge import _channels, _channels_cli, _db


def _clean_git_env() -> dict[str, str]:
    return {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }


def _init_repo(path: Path) -> None:
    git_env = _clean_git_env()
    subprocess.run(
        ["git", "init"], cwd=path, check=True, capture_output=True, env=git_env
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=path,
        check=True,
        capture_output=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
        capture_output=True,
        env=git_env,
    )
    (path / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=path, check=True, env=git_env)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=path,
        check=True,
        capture_output=True,
        env=git_env,
    )


@pytest.fixture()
def isolated_bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)

    # Patch both bindings — ``_db`` imports DB_PATH from ``_config`` by
    # name, so they are independent (#5247 xdist leak class).
    from ai_agent_bridge import _config

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    monkeypatch.setattr(_channels_cli, "REPO_ROOT", repo)
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )
    _channels.create_channel("architecture", exist_ok=False)
    return repo


def test_discuss_detects_post_round_write_and_marks_violation(
    isolated_bridge: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        assert agent_name == "claude"
        assert kwargs["mode"] == "read-only"
        assert kwargs["tool_config"]["discussion_readonly"] is True
        (isolated_bridge / "agent-write.txt").write_text("bad\n", encoding="utf-8")
        return SimpleNamespace(ok=True, response="I wrote a file. [DISAGREE]")

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)
    args = SimpleNamespace(
        channel="architecture",
        body="Discuss without editing files.",
        with_agents="claude",
        max_rounds=1,
        review=False,
    )

    assert _channels_cli._handle_discuss(args) == 1
    captured = capsys.readouterr()
    assert "READ_ONLY_VIOLATION: claude" in captured.err
    assert "READ_ONLY_VIOLATION: claude" in captured.out
    assert "agent-write.txt" in captured.err

    messages = _channels.read("architecture", tail=10)
    warning = messages[-1]
    assert warning["kind"] == "system"
    assert warning["body"].startswith("⚠️ READ-ONLY DISCUSSION VIOLATION")
    assert "READ_ONLY_VIOLATION: claude" in warning["body"]
    assert not any(message["from_agent"] == "claude" for message in messages)


def test_discuss_posts_normal_reply_when_worktree_is_unchanged(
    isolated_bridge: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        assert agent_name == "codex"
        assert kwargs["mode"] == "read-only"
        return SimpleNamespace(ok=True, response="Normal analysis only. [DISAGREE]", session_id=None)

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)
    args = SimpleNamespace(
        channel="architecture",
        body="Discuss without editing files.",
        with_agents="codex",
        max_rounds=1,
        review=False,
    )

    assert _channels_cli._handle_discuss(args) == 0
    messages = _channels.read("architecture", tail=10)
    replies = [message for message in messages if message["from_agent"] == "codex"]
    assert len(replies) == 1
    assert replies[0]["body"] == "Normal analysis only. [DISAGREE]"
