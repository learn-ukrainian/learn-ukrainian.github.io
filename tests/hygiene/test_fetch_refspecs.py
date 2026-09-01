"""Tests for stale remote fetch-refspec hygiene (#7121).

A narrow clone with a configured refspec pointing at a deleted remote head
cannot `git fetch` at all. The cleaner/guard must drop that entry, keep the
canonical main refspec, and make fetch succeed again.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.hygiene import fetch_refspecs
from scripts.orchestration import scheduled_worktree_cleanup as cleanup


def _git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        env=_git_env(),
        timeout=30,
    )


def _git_ok(cwd: Path, *args: str) -> str:
    return _git(cwd, *args).stdout.strip()


def _narrow_clone(tmp_path: Path) -> Path:
    """Bare origin + single-branch clone whose fetch config is main-only."""
    remote = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    clone = tmp_path / "narrow"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", "--initial-branch=main", str(seed))
    _git(seed, "config", "user.email", "test@example.invalid")
    _git(seed, "config", "user.name", "Test User")
    (seed / "README.md").write_text("base\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-m", "base")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "-u", "origin", "main")
    _git(
        tmp_path,
        "clone",
        "--filter=blob:none",
        "--single-branch",
        "--branch",
        "main",
        str(remote),
        str(clone),
    )
    _git(clone, "config", "user.email", "test@example.invalid")
    _git(clone, "config", "user.name", "Test User")
    return clone


def _fetch_refspecs(repo: Path) -> list[str]:
    return fetch_refspecs.list_fetch_refspecs(repo)


def _add_stale_refspec(repo: Path, branch: str) -> str:
    spec = fetch_refspecs.head_refspec(branch)
    _git(repo, "config", "--add", "remote.origin.fetch", spec)
    return spec


def test_stale_refspec_hard_fails_fetch_until_guard_runs(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    stale = "cursor/scrub-public-ops-paths-a004"
    spec = _add_stale_refspec(repo, stale)

    before = _git(repo, "fetch", "origin", check=False)
    assert before.returncode != 0
    assert "couldn't find remote ref" in (before.stderr or before.stdout)

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=True)

    assert report["ok"] is True
    assert spec in report["pruned"]
    assert fetch_refspecs.canonical_main_refspec() in report["after"]
    assert spec not in _fetch_refspecs(repo)

    after = _git(repo, "fetch", "origin", check=False)
    assert after.returncode == 0, after.stderr or after.stdout


def test_add_fetch_branch_is_idempotent(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    branch = "cursor/infra-7095-progress-backlog"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)

    first = fetch_refspecs.add_fetch_branch(repo, branch)
    second = fetch_refspecs.add_fetch_branch(repo, branch)

    assert first["added"] is True
    assert second["added"] is False
    assert second["already_present"] is True
    assert _fetch_refspecs(repo).count(first["refspec"]) == 1

    fetched = _git(repo, "fetch", "origin", check=False)
    assert fetched.returncode == 0, fetched.stderr or fetched.stdout


def test_reconcile_dedups_duplicate_refspecs(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    branch = "cursor/infra-7095-progress-backlog"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    spec = fetch_refspecs.head_refspec(branch)
    _git(repo, "config", "--add", "remote.origin.fetch", spec)
    _git(repo, "config", "--add", "remote.origin.fetch", spec)

    assert _fetch_refspecs(repo).count(spec) == 2

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=True)

    assert report["ok"] is True
    assert report["deduped"] == [spec]
    assert _fetch_refspecs(repo).count(spec) == 1
    assert fetch_refspecs.canonical_main_refspec() in _fetch_refspecs(repo)

    fetched = _git(repo, "fetch", "origin", check=False)
    assert fetched.returncode == 0, fetched.stderr or fetched.stdout


def test_reconcile_keeps_live_extra_branch_refspec(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    branch = "feat/still-open"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    spec = fetch_refspecs.head_refspec(branch)
    _git(repo, "config", "--add", "remote.origin.fetch", spec)

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=True)

    assert spec in report["after"]
    assert spec not in report["pruned"]
    assert spec in _fetch_refspecs(repo)


def test_reconcile_restores_canonical_main_refspec(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    stale = fetch_refspecs.head_refspec("gone/only-entry")
    _git(repo, "config", "--unset-all", "remote.origin.fetch")
    _git(repo, "config", "--add", "remote.origin.fetch", stale)

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=True)

    assert report["restored_main"] is True
    assert fetch_refspecs.canonical_main_refspec() in _fetch_refspecs(repo)
    assert stale not in _fetch_refspecs(repo)
    fetched = _git(repo, "fetch", "origin", check=False)
    assert fetched.returncode == 0, fetched.stderr or fetched.stdout


def test_reconcile_does_not_drop_live_specs_when_ls_remote_fails(
    tmp_path: Path,
) -> None:
    repo = _narrow_clone(tmp_path)
    branch = "feat/keep-when-offline"
    spec = fetch_refspecs.head_refspec(branch)
    _git(repo, "config", "--add", "remote.origin.fetch", spec)
    _git(repo, "remote", "set-url", "origin", "file:///no/such/remote.git")

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=True)

    assert report["live_heads_available"] is False
    assert spec in _fetch_refspecs(repo)
    assert spec not in report["pruned"]


def test_drop_never_removes_canonical_main(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    assert fetch_refspecs.drop_fetch_refspec_for_branch(repo, "main") is False
    assert fetch_refspecs.canonical_main_refspec() in _fetch_refspecs(repo)


def test_origin_head_delete_also_drops_matching_refspec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _narrow_clone(tmp_path)
    branch = "codex/merged-origin"
    _git(repo, "branch", branch, "main")
    _git(repo, "push", "origin", branch)
    spec = fetch_refspecs.add_fetch_branch(repo, branch)["refspec"]
    _git(repo, "fetch", "origin")
    head_sha = _git_ok(repo, "rev-parse", branch)

    def _prs(_repo: Path, candidate: str | None):
        if candidate != branch:
            return [], None
        return (
            [
                cleanup.reap_worktrees.PullRequestState(
                    number=77,
                    state="MERGED",
                    head_sha=head_sha,
                )
            ],
            None,
        )

    monkeypatch.setattr(cleanup.reap_worktrees, "_query_pr_states", _prs)

    applied = cleanup.cleanup_stale_origin_branches(repo, apply=True)

    deleted = next(item for item in applied if item["branch"] == branch)
    assert deleted["action"] == "deleted"
    assert deleted["refspec_dropped"] is True
    assert spec not in _fetch_refspecs(repo)
    assert fetch_refspecs.canonical_main_refspec() in _fetch_refspecs(repo)

    fetched = _git(repo, "fetch", "origin", check=False)
    assert fetched.returncode == 0, fetched.stderr or fetched.stdout


def test_dry_run_reconcile_does_not_write(tmp_path: Path) -> None:
    repo = _narrow_clone(tmp_path)
    spec = _add_stale_refspec(repo, "cursor/stale-dry-run")
    before = _fetch_refspecs(repo)

    report = fetch_refspecs.reconcile_fetch_refspecs(repo, apply=False)

    assert report["applied"] is False
    assert spec in report["pruned"]
    assert _fetch_refspecs(repo) == before


def test_scheduled_hygiene_heals_stale_refspec_before_fetch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _narrow_clone(tmp_path)
    spec = _add_stale_refspec(repo, "kimi/infra-7080-audit-dashboard-r2")
    monkeypatch.setattr(cleanup, "_worktree_prune", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(cleanup.reap_worktrees, "reap_worktrees", lambda **_kwargs: [])
    monkeypatch.setattr(cleanup.reap_worktrees, "adopt_dispatch_worktrees", lambda _repo: [])
    monkeypatch.setattr(cleanup, "cleanup_gone_local_branches", lambda *_a, **_k: [])
    monkeypatch.setattr(cleanup, "cleanup_stale_origin_branches", lambda *_a, **_k: [])
    monkeypatch.setattr(cleanup, "cleanup_untracked_local_branches", lambda *_a, **_k: [])
    monkeypatch.setattr(cleanup, "find_orphaned_worktree_directories", lambda _repo: [])
    monkeypatch.setattr(cleanup, "_git_maintenance", lambda _repo, *, apply: {"ok": True})
    monkeypatch.setattr(cleanup, "sweep_review_temp_orphans", lambda: {"errors": 0})
    monkeypatch.setattr(
        cleanup,
        "sweep_tmp_leaks",
        lambda apply=False: {
            "errors": 0,
            "roots_reaped": 0,
            "bytes_freed": 0,
            "candidates": 0,
            "skipped_live": 0,
        },
    )

    result = cleanup._repo_result(repo, apply=True)

    assert result["fetch"]["ok"] is True
    assert spec in (result["fetch_refspecs"] or {}).get("pruned", [])
    assert spec not in _fetch_refspecs(repo)
    fetched = _git(repo, "fetch", "origin", check=False)
    assert fetched.returncode == 0, fetched.stderr or fetched.stdout


def test_cli_json_heals_stale_refspec(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _narrow_clone(tmp_path)
    spec = _add_stale_refspec(repo, "agy/infra-6977-runner")

    rc = fetch_refspecs.main(["--repo-root", str(repo), "--json"])

    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert spec in report["pruned"]
    assert spec not in _fetch_refspecs(repo)
