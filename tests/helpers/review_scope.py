"""Small ordinary Git targets shared by review tests."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.common.git_context import sanitized_git_env


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo, text=True, env=sanitized_git_env(), timeout=30
    ).strip()


def init_review_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "target"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "core.hooksPath", "/dev/null")
    (repo / "ordinary.py").write_text("value = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    return repo, base


def make_ordinary_review_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Real ordinary Git scope, even when a dispatch test stubs process spawning."""
    from scripts.review import security_paths, target_resolution

    repo, _base = init_review_repo(tmp_path)
    file = repo / "ordinary.py"
    file.write_text("value = 2\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "review target\n\nX-Agent: codex/gpt-6.1-sol")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", "refs/remotes/origin/review-target", head)
    run_git = target_resolution._run_git
    real_run, real_popen = subprocess.run, subprocess.Popen

    def fixture_git(args, cwd, *, timeout=30.0):
        with patch.object(subprocess, "run", real_run), patch.object(subprocess, "Popen", real_popen):
            return run_git(args, cwd, timeout=timeout)

    monkeypatch.setattr(target_resolution, "_run_git", fixture_git)
    monkeypatch.setattr(security_paths, "_run_git", fixture_git)
    return repo


def write_code_review_manifest(repo: Path, path: Path) -> Path:
    """Freeze a real code target in the shape admission reads."""
    from scripts.review.target_resolution import resolve_branch_target

    target = resolve_branch_target(repo, "refs/remotes/origin/review-target", "refs/remotes/origin/main")
    path.write_text(json.dumps({"target": asdict(target)}))
    return path


@pytest.fixture
def ordinary_review_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return make_ordinary_review_scope(tmp_path, monkeypatch)
