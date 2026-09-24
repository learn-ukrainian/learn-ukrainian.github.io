"""Release-commit override must be a real ancestor, never a silent fallback."""

from __future__ import annotations

import subprocess
from pathlib import Path
from runpy import run_path

import pytest

REPOSITORY = Path(__file__).resolve().parents[3]
resolve_public_commit = run_path(str(REPOSITORY / "packages/v4-runtime/build_assets.py"))["resolve_public_commit"]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPOSITORY, text=True).strip()


def test_malformed_commit_override_raises(monkeypatch):
    monkeypatch.setenv("LEARN_UKRAINIAN_V4_RUNTIME_COMMIT", "not-a-commit")
    with pytest.raises(ValueError):
        resolve_public_commit()


def test_uppercase_commit_override_raises(monkeypatch):
    monkeypatch.setenv("LEARN_UKRAINIAN_V4_RUNTIME_COMMIT", _git("rev-parse", "HEAD").upper())
    with pytest.raises(ValueError):
        resolve_public_commit()


def test_missing_commit_override_raises(monkeypatch):
    monkeypatch.setenv("LEARN_UKRAINIAN_V4_RUNTIME_COMMIT", "a" * 40)
    with pytest.raises(ValueError, match="does not name an existing commit"):
        resolve_public_commit()


def test_non_ancestor_commit_override_raises(monkeypatch):
    dangling = _git("commit-tree", _git("rev-parse", "HEAD^{tree}"), "-m", "v4 runtime override probe")
    monkeypatch.setenv("LEARN_UKRAINIAN_V4_RUNTIME_COMMIT", dangling)
    with pytest.raises(ValueError, match="ancestor of HEAD"):
        resolve_public_commit()


def test_head_and_ancestor_commit_overrides_are_accepted(monkeypatch):
    head = _git("rev-parse", "HEAD")
    parent = _git("rev-parse", "HEAD^")
    for commit in (head, parent):
        monkeypatch.setenv("LEARN_UKRAINIAN_V4_RUNTIME_COMMIT", commit)
        assert resolve_public_commit() == commit
