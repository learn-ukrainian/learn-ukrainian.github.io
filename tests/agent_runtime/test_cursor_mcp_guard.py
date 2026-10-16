"""The commit guard for the per-run Cursor MCP config (#10837)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.agent_runtime.cursor_mcp_guard import config_problems, head, recorded_config_problems

TRACKED = {"mcpServers": {"sources": {"url": "http://127.0.0.1:8766/mcp"}}}
MIRROR = {"mcpServers": {"sources": {"command": "/usr/bin/env", "args": ["-i", "python"]}}}


def _git(repo: Path, *argv: str) -> str:
    done = subprocess.run(["git", *argv], cwd=repo, check=True, capture_output=True, text=True, timeout=30)
    return done.stdout.strip()


def _commit(repo: Path, config: dict | None, message: str) -> None:
    path = repo / ".cursor" / "mcp.json"
    if config is None:
        path.unlink()
    else:
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(config), encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    for key, value in (("user.email", "test@example.invalid"), ("user.name", "test"), ("core.hooksPath", "/dev/null")):
        _git(tmp_path, "config", key, value)
    _commit(tmp_path, TRACKED, "base")
    return tmp_path


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (TRACKED, []),
        ({"mcpServers": {"sources": {"type": "streamable-http", "url": "http://127.0.0.1:8766/mcp"}}}, []),
        (MIRROR, ["server 'sources' carries per-run keys ['args', 'command']"]),
        (
            {"mcpServers": {"sources": {"url": "u", "env": {"K": "v"}}}},
            ["server 'sources' carries per-run keys ['env']"],
        ),
        ({"mcpServers": {"sources": {}}}, ["server 'sources' has no url"]),
        ({"mcpServers": {"sources": "u"}}, ["server 'sources' is not an object"]),
        ({"mcpServers": {}, "extra": 1}, ["the file must hold exactly one mcpServers object"]),
        ([], ["the file must hold exactly one mcpServers object"]),
    ],
)
def test_config_problems(config, expected):
    assert config_problems(json.dumps(config).encode()) == expected


def test_config_problems_refuses_unparseable_bytes():
    assert config_problems(b"\xff{") == ["not valid UTF-8 JSON"]


def test_a_clean_run_records_nothing(repo):
    start = head(repo)
    (repo / "README.md").write_text("work\n", encoding="utf-8")
    _commit(repo, TRACKED, "work")
    assert recorded_config_problems(repo, start) == []


def test_a_committed_then_reverted_copy_is_still_found(repo):
    start = head(repo)
    _commit(repo, MIRROR, "leak")
    _commit(repo, TRACKED, "restore")
    problems = recorded_config_problems(repo, start)
    assert len(problems) == 1 and "carries per-run keys" in problems[0]


def test_a_staged_copy_is_found_and_a_committed_one_is_not_reported_twice(repo):
    start = head(repo)
    _commit(repo, MIRROR, "leak")
    assert len(recorded_config_problems(repo, start)) == 1
    (repo / ".cursor" / "mcp.json").write_text(json.dumps(TRACKED), encoding="utf-8")  # The worker's restore.
    assert len(recorded_config_problems(repo, start)) == 1
    _git(repo, "add", ".cursor/mcp.json")
    _commit(repo, TRACKED, "restore")
    (repo / ".cursor" / "mcp.json").write_text(json.dumps(MIRROR), encoding="utf-8")
    _git(repo, "add", ".cursor/mcp.json")
    assert recorded_config_problems(repo, start)[-1].startswith(".cursor/mcp.json at index: ")


def test_commits_before_the_run_are_not_its_record(repo):
    _commit(repo, MIRROR, "an older leak")
    start = head(repo)
    _commit(repo, TRACKED, "restore")
    assert recorded_config_problems(repo, start) == []


def test_a_deletion_is_not_a_leak(repo):
    start = head(repo)
    _commit(repo, None, "remove")
    assert recorded_config_problems(repo, start) == []


def test_a_git_failure_fails_closed(repo):
    assert recorded_config_problems(repo, "0" * 40) == [f"git rev-list {'0' * 12}..HEAD failed"]
    assert recorded_config_problems(repo / "missing", head(repo))[0].endswith("could not run git: FileNotFoundError")


def test_head_refuses_a_checkout_without_commits(tmp_path):
    _git(tmp_path, "init", "-q")
    with pytest.raises(RuntimeError, match="cannot read HEAD"):
        head(tmp_path)
