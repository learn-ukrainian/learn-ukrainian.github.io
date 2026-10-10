from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_branch_exempt_only_with_open_pr(tmp_path: Path) -> None:
    fetch, _ = _fetch(30)
    cache = tmp_path / "c.json"
    with_pr = pr_freeze.evaluate(
        REPO, branch="codex/fix-1", environ={}, fetch=fetch, has_open_pr=lambda r, b: True, cache_file=cache
    )
    assert not with_pr.refused
    no_pr = pr_freeze.evaluate(
        REPO, branch="codex/new", environ={}, fetch=fetch, has_open_pr=lambda r, b: False, cache_file=cache
    )
    assert no_pr.refused

    def broken(repo, branch):
        raise RuntimeError("lookup failed")

    unknown = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, has_open_pr=broken, cache_file=cache)
    assert not unknown.refused and "lookup failed" in (unknown.warning or "")


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
        ({"pr": 12}, False),
        ({"cwd": "/some/worktree"}, False),
        ({"review": True}, False),
        ({"reused_worktree": True}, False),
        ({"continuation": True}, False),
        ({"mode": "read-only"}, False),
        ({"repo_role": "private-infra"}, False),
    ],
)
def test_only_new_public_implementation_jobs_gated(kwargs, expected) -> None:
    base = {"mode": "workspace-write", "repo_role": "public-monorepo", "pr": None, "cwd": None, "review": False}
    base.update(kwargs)
    assert pr_freeze.opens_new_pr(**base) is expected


def test_dispatch_refuses_before_any_side_effect(monkeypatch, capsys, tmp_path) -> None:
    """End-to-end: a frozen new-PR dispatch exits 3 and leaves no task record."""
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path / "tasks")

    def no_side_effects(*a, **k):
        raise AssertionError("side effect reached before the freeze check")

    monkeypatch.setattr(delegate, "_state_path", no_side_effects)
    monkeypatch.setattr(delegate, "_archive_task_artifacts", no_side_effects)
    argv = [
        "delegate.py",
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        "freeze-probe",
        "--mode",
        "workspace-write",
        "--worktree",
        "--prompt",
        "implement a thing",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    rc = delegate.main()
    err = capsys.readouterr().err
    assert rc == 3, err
    assert "Land your own open PRs first" in err
    assert not (tmp_path / "tasks").exists()


def test_helper_allows_existing_pr_branch(monkeypatch) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setattr(pr_freeze, "branch_has_open_pr", lambda repo, branch: True)
    monkeypatch.setenv(pr_freeze.CACHE_ENV, "0")
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(mode="workspace-write", branch="codex/fix-1", pr=None, cwd=None, worktree=None)
    assert delegate._check_open_pr_freeze(args, repo) is None


def test_branch_lookup_encodes_head(monkeypatch) -> None:
    seen = []

    def fake_get(endpoint):
        seen.append(endpoint)
        return [{"number": 1}]

    monkeypatch.setattr(pr_freeze, "_gh_get", fake_get)
    assert pr_freeze.branch_has_open_pr(REPO, "codex/fix+123&x#y%z")
    assert seen[0].endswith("head=example%3Acodex%2Ffix%2B123%26x%23y%25z")


def test_force_new_without_prior_record_is_still_refused(monkeypatch, capsys, tmp_path) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path / "tasks")
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(
        mode="workspace-write", branch=None, pr=None, cwd=None, worktree="auto", force_new=True, task_id="fresh-id"
    )
    assert delegate._check_open_pr_freeze(args, repo) == 3
    assert not (tmp_path / "tasks").exists()

    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "fresh-id.json").write_text("{}")
    assert delegate._check_open_pr_freeze(args, repo) is None
