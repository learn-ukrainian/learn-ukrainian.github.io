from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestration import pr_freeze

REPO = "example/repo"


def _fetch(count):
    calls = []

    def fetch(repo):
        calls.append(repo)
        return count

    return fetch, calls


def test_refuses_at_threshold(tmp_path: Path) -> None:
    fetch, _ = _fetch(15)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused
    line = decision.refusal_line(REPO)
    assert "15 open PRs" in line
    assert "Land your own open PRs first" in line


def test_admits_below_threshold(tmp_path: Path) -> None:
    fetch, _ = _fetch(14)
    assert not pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json").refused


def test_env_override(tmp_path: Path) -> None:
    fetch, _ = _fetch(20)
    env = {pr_freeze.THRESHOLD_ENV: "25"}
    assert not pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json").refused
    env = {pr_freeze.THRESHOLD_ENV: "0"}
    assert not pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json").refused
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "junk"}) == 15


def test_fails_open_with_warning(tmp_path: Path) -> None:
    def broken(repo):
        raise RuntimeError("network down")

    decision = pr_freeze.evaluate(REPO, environ={}, fetch=broken, cache_file=tmp_path / "c.json")
    assert not decision.refused
    assert decision.warning and "network down" in decision.warning


def test_cache_reused_within_ttl(tmp_path: Path) -> None:
    fetch, calls = _fetch(3)
    cache = tmp_path / "c.json"
    clock = iter([100.0, 130.0, 200.0, 200.0])
    for _ in range(3):
        pr_freeze.cached_open_pr_count(REPO, fetch=fetch, cache_file=cache, ttl_s=60, now=lambda: next(clock))
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, True),
        ({"branch": "codex/fix-1"}, False),
        ({"pr": 12}, False),
        ({"cwd": "/some/worktree"}, False),
        ({"review": True}, False),
        ({"mode": "read-only"}, False),
        ({"repo_role": "private-infra"}, False),
    ],
)
def test_only_new_public_implementation_jobs_gated(kwargs, expected) -> None:
    base = {
        "mode": "workspace-write",
        "repo_role": "public-monorepo",
        "branch": None,
        "pr": None,
        "cwd": None,
        "review": False,
    }
    base.update(kwargs)
    assert pr_freeze.opens_new_pr(**base) is expected


def test_delegate_refuses_new_public_implementation(monkeypatch, capsys) -> None:
    import argparse
    from types import SimpleNamespace

    from scripts import delegate

    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", "/nonexistent-cache-dir-for-test")
    monkeypatch.setenv(pr_freeze.CACHE_ENV, "0")
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(mode="workspace-write", branch=None, pr=None, cwd=None)
    monkeypatch.setattr(pr_freeze, "evaluate", lambda r, **kw: pr_freeze.FreezeDecision(True, 30, 15))
    assert delegate._check_open_pr_freeze(args, repo) == 3
    err = capsys.readouterr().err
    assert "Land your own open PRs first" in err

    existing = argparse.Namespace(mode="workspace-write", branch="codex/fix-1", pr=None, cwd=None)
    assert delegate._check_open_pr_freeze(existing, repo) is None
