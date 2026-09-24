"""Hermetic tests for settle-stale / archive / restore (#8625).

Every test runs against a tmp task directory, a tmp git repository with a
bare ``origin``, and a fake REST pull pager; nothing reads the real
``batch_state/tasks`` or reaches GitHub.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate
from scripts.orchestration import stale_task_records as str_mod
from scripts.orchestration import task_record_store, worktree_claims

SLUG = "owner/repo"
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
OLD_FINISH = NOW - timedelta(days=10)
OLD_START = OLD_FINISH - timedelta(hours=1)


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "PRE_COMMIT")) and key != "AGENT_NO_MERGE"
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    return env


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=_git_env(), timeout=30
    ).stdout.strip()


def _orphan_commit(repo: Path, name: str) -> str:
    """Commit on a throwaway branch, then delete the branch: no ref holds the commit."""
    _git(repo, "checkout", "-b", f"tmp/{name}")
    (repo / f"{name}.txt").write_text(f"{name}\n")
    _git(repo, "add", f"{name}.txt")
    _git(repo, "commit", "-m", name)
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", f"tmp/{name}")
    return sha


def _auto_finalized(sha: str) -> dict[str, Any]:
    return {"ok": False, "commit_sha": sha, "pr_url": None, "error": "push failed", "changed_files": ["x"]}


SCAN_KEY = "test"
SCAN_PREFIX = f"refs/lu-stale-scan/{SCAN_KEY}"


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    monkeypatch.setattr(delegate, "_WORKTREE_LOCK_DIR", tmp_path / "lu-worktree-locks")
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    # The tool drops every GIT_CONFIG* variable, so git reads $HOME's config: keep it empty.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"):
        monkeypatch.delenv(key, raising=False)
    # The allowlisted fetch URL of SLUG is the tmp bare repository, not GitHub.
    target = str_mod.FetchTarget(key=SCAN_KEY, url=str(tmp_path / "origin.git"))
    monkeypatch.setattr(str_mod, "fleet_fetch_target", lambda slug: target if slug == SLUG else None)


@pytest.fixture
def repo(tmp_path) -> Path:
    """A checkout whose ``origin`` is a local bare repository."""
    origin = tmp_path / "origin.git"
    checkout = tmp_path / "checkout"
    _git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    _git(tmp_path, "init", "-b", "main", str(checkout))
    (checkout / "README").write_text("base\n")
    _git(checkout, "add", "README")
    _git(checkout, "commit", "-m", "base")
    _git(checkout, "remote", "add", "origin", str(origin))
    _git(checkout, "push", "-u", "origin", "main")
    return checkout


@pytest.fixture
def tasks_dir(tmp_path) -> Path:
    path = tmp_path / "tasks"
    path.mkdir()
    return path


def _record(tasks_dir: Path, name: str, **fields: Any) -> Path:
    record = {
        "task_id": name,
        "agent": "codex",
        "mode": "danger",
        "status": "needs_finalize",
        "needs_finalize": True,
        "repository": SLUG,
        "worktree_branch": f"codex/{name}",
        "worktree_base": "main",
        "worktree_path": str(tasks_dir.parent / "gone" / name),
        "started_at": OLD_START.isoformat(),
        "finished_at": OLD_FINISH.isoformat(),
        "returncode": 0,
        "commits_ahead": 0,
        "worktree_dirty_on_exit": False,
    }
    record.update(fields)
    path = tasks_dir / f"{name}.json"
    path.write_text(json.dumps(record, indent=2))
    return path


def _merged(
    branch: str, number: int, merged_at: datetime, *, slug: str = SLUG, head_sha: str | None = None
) -> dict[str, Any]:
    return {
        "number": number,
        "html_url": f"https://github.com/{slug}/pull/{number}",
        "merged_at": merged_at.isoformat(),
        "updated_at": merged_at.isoformat(),
        "merge_commit_sha": f"{number + 0xABC:040x}",
        "head": {"ref": branch, "sha": head_sha or f"{number:040x}", "repo": {"full_name": slug}},
    }


class FakePager:
    def __init__(self, pulls: list[dict[str, Any]]):
        self.pulls = pulls
        self.calls: list[tuple[str, int]] = []

    def __call__(self, slug: str, page: int) -> list[dict[str, Any]]:
        self.calls.append((slug, page))
        start = (page - 1) * str_mod.PR_PAGE_SIZE
        return self.pulls[start : start + str_mod.PR_PAGE_SIZE]


def _snapshot(directory: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(path.relative_to(directory)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


@pytest.fixture
def mixed(tmp_path, repo, tasks_dir):
    """One record of every class, plus a young record that must be left alone."""
    # A: branch published on origin, local branch deleted.
    _git(repo, "branch", "codex/published")
    _git(repo, "push", "origin", "codex/published")
    _git(repo, "branch", "-D", "codex/published")
    _record(tasks_dir, "published")
    # B: local branch with an unpushed commit, worktree gone.
    _git(repo, "checkout", "-b", "codex/local-only")
    (repo / "work.txt").write_text("unpushed\n")
    _git(repo, "add", "work.txt")
    _git(repo, "commit", "-m", "unpushed")
    _git(repo, "checkout", "main")
    _record(tasks_dir, "local-only", commits_ahead=1)
    # B: dirty detached worktree, no branch anywhere.
    dirty_wt = tmp_path / "wt-dirty"
    _git(repo, "worktree", "add", "--detach", str(dirty_wt))
    (dirty_wt / "scratch.txt").write_text("uncommitted\n")
    _record(tasks_dir, "dirty", worktree_path=str(dirty_wt), worktree_branch="codex/dirty")
    # D: clean detached worktree, no branch anywhere.
    clean_wt = tmp_path / "wt-clean"
    _git(repo, "worktree", "add", "--detach", str(clean_wt))
    _record(tasks_dir, "clean-detached", worktree_path=str(clean_wt), worktree_branch="codex/clean-detached")
    # D: repository unknown.
    _record(tasks_dir, "no-repo", repository=None)
    # C: a recorded commit no ref holds, merged by PR #7 -> done; clean no-commit
    # exit -> no_deliverable; crash -> failed.
    merged_sha = _orphan_commit(repo, "merged")
    _record(
        tasks_dir, "merged", commits_ahead=0, worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(merged_sha)
    )
    _record(tasks_dir, "no-commits")
    _record(tasks_dir, "crashed", returncode=1)
    # C: a PR for the same branch merged BEFORE the task started is not its deliverable.
    stale_sha = _orphan_commit(repo, "stale-pr")
    _record(tasks_dir, "stale-pr", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(stale_sha))
    # Young needs_finalize record: below --min-age-days.
    _record(tasks_dir, "young", finished_at=(NOW - timedelta(days=1)).isoformat())
    # Terminal record: not a settle candidate.
    _record(tasks_dir, "already-done", status="done")
    pager = FakePager(
        [
            _merged("codex/merged", 7, OLD_FINISH + timedelta(hours=2), head_sha=merged_sha),
            _merged("codex/merged", 8, OLD_FINISH + timedelta(hours=1), slug="fork/repo", head_sha=merged_sha),
            _merged("codex/stale-pr", 5, OLD_START - timedelta(days=3)),
        ]
    )
    return {"repo": repo, "pager": pager, "merged_sha": merged_sha}


def _run(tasks_dir: Path, mixed: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return str_mod.settle_stale(
        tasks_dir,
        repo_checkouts={SLUG: mixed["repo"]},
        pager=mixed["pager"],
        now=NOW,
        **kwargs,
    )


def _by_file(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["file"]: row for row in report["records"]}


def test_classifies_every_class_like_the_report(tasks_dir, mixed):
    report = _run(tasks_dir, mixed)
    rows = _by_file(report)

    assert report["classes"] == {"A": 1, "B": 2, "C": 4, "D": 2}
    assert report["younger_left_alone"] == 1
    assert "young.json" not in rows and "already-done.json" not in rows
    assert rows["published.json"]["class"] == "A"
    assert rows["published.json"]["evidence"]["branch_on_origin"] is True
    assert rows["local-only.json"]["class"] == "B"
    assert rows["local-only.json"]["evidence"]["local_commits_ahead_of_base"] == 1
    assert rows["dirty.json"]["class"] == "B"
    assert rows["dirty.json"]["evidence"]["worktree_dirty"] is True
    assert rows["clean-detached.json"]["class"] == "D"
    assert rows["no-repo.json"]["class"] == "D"
    assert rows["merged.json"]["outcome"] == "done"
    assert rows["merged.json"]["merged_pr"]["number"] == 7  # the fork PR #8 never counts
    assert rows["no-commits.json"]["outcome"] == "no_deliverable"
    assert rows["crashed.json"]["outcome"] == "failed"
    assert rows["stale-pr.json"]["outcome"] == "failed"
    assert report["outcomes"] == {"done": 1, "no_deliverable": 1, "failed": 2}
    # One paged REST list for the repository, never a per-record call.
    assert mixed["pager"].calls == [(SLUG, 1)]


def test_dry_run_writes_nothing(tasks_dir, mixed):
    before = _snapshot(tasks_dir)
    report = _run(tasks_dir, mixed)
    assert report["mode"] == "dry-run"
    assert report["actions"]["would_settle"] == 4
    assert _snapshot(tasks_dir) == before


def test_apply_settles_class_c_with_receipt_and_leaves_a_b_d_untouched(tasks_dir, mixed):
    untouched = ["published.json", "local-only.json", "dirty.json", "clean-detached.json", "no-repo.json", "young.json"]
    before = {name: (tasks_dir / name).read_bytes() for name in untouched}

    report = _run(tasks_dir, mixed, apply=True)

    assert report["actions"] == {"settled": 4, "report": 5}
    for name in untouched:
        assert (tasks_dir / name).read_bytes() == before[name], name
    merged = json.loads((tasks_dir / "merged.json").read_text())
    assert merged["status"] == "done"
    assert merged["needs_finalize"] is False
    assert merged["settled_by"] == "settle-stale"
    assert merged["settled_at"] == NOW.isoformat()
    assert merged["settle_previous_status"] == "needs_finalize"
    assert "PR #7" in merged["settle_reason"]
    assert merged["merged_pr"]["url"].endswith("/pull/7")
    assert merged["merged_pr"]["head_sha"] == mixed["merged_sha"]
    assert merged["settle_evidence"]["recorded_commits_reachable"] is False
    assert merged["settle_evidence"]["branch_on_origin"] is False
    no_commits = json.loads((tasks_dir / "no-commits.json").read_text())
    assert no_commits["status"] == "no_deliverable"
    assert no_commits["no_deliverable_reason"] == no_commits["settle_reason"]
    assert json.loads((tasks_dir / "crashed.json").read_text())["status"] == "failed"
    # Settled records release their claim: the worktree claim scan no longer honors them.
    assert all(
        json.loads((tasks_dir / name).read_text())["status"] in worktree_claims.RELEASED_TASK_STATUSES
        for name in ("merged.json", "no-commits.json", "crashed.json", "stale-pr.json")
    )


def test_class_b_untouched_even_when_it_looks_orphaned_otherwise(tasks_dir, mixed):
    """A local branch alone keeps a record in class B, whatever the PR list says."""
    mixed["pager"].pulls.append(_merged("codex/local-only", 9, OLD_FINISH + timedelta(hours=3)))
    before = (tasks_dir / "local-only.json").read_bytes()
    report = _run(tasks_dir, mixed, apply=True)
    assert _by_file(report)["local-only.json"]["class"] == "B"
    assert _by_file(report)["local-only.json"]["action"] == "report"
    assert (tasks_dir / "local-only.json").read_bytes() == before


def test_record_changed_since_classification_is_skipped(tasks_dir, mixed):
    target = tasks_dir / "crashed.json"

    def live_writer(_candidates):
        record = json.loads(target.read_text())
        record["heartbeat"] = "live writer"
        target.write_text(json.dumps(record))
        stat = target.stat()
        os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

    report = _run(tasks_dir, mixed, apply=True, before_apply=live_writer)

    row = _by_file(report)["crashed.json"]
    assert row["action"] == "skipped"
    assert row["skip_reason"] == "record changed since classification"
    record = json.loads(target.read_text())
    assert record["status"] == "needs_finalize"
    assert record["heartbeat"] == "live writer"
    assert _by_file(report)["merged.json"]["action"] == "settled"


def test_worktree_reappearing_before_the_write_is_skipped(tasks_dir, mixed):
    target = tasks_dir / "no-commits.json"

    def reattach(_candidates):
        Path(json.loads(target.read_text())["worktree_path"]).mkdir(parents=True)

    report = _run(tasks_dir, mixed, apply=True, before_apply=reattach)

    row = _by_file(report)["no-commits.json"]
    assert (row["action"], row["skip_reason"]) == ("skipped", "worktree path reappeared since classification")
    assert json.loads(target.read_text())["status"] == "needs_finalize"


def test_record_whose_worktree_lock_is_held_is_skipped(tasks_dir, mixed):
    target_path = json.loads((tasks_dir / "no-commits.json").read_text())["worktree_path"]
    held, release = threading.Event(), threading.Event()

    def holder():
        with delegate.worktree_lock(target_path, timeout_s=1):
            held.set()
            release.wait(10)

    thread = threading.Thread(target=holder)
    thread.start()
    try:
        assert held.wait(5)
        report = _run(tasks_dir, mixed, apply=True, lock_timeout_s=0.1)
    finally:
        release.set()
        thread.join()

    row = _by_file(report)["no-commits.json"]
    assert (row["action"], row["skip_reason"]) == ("skipped", worktree_claims.LOCK_BUSY)
    assert json.loads((tasks_dir / "no-commits.json").read_text())["status"] == "needs_finalize"


def test_pull_list_failure_settles_nothing(tasks_dir, mixed):
    def broken(_slug, _page):
        raise RuntimeError("gh api failed: HTTP 502")

    before = _snapshot(tasks_dir)
    report = str_mod.settle_stale(tasks_dir, repo_checkouts={SLUG: mixed["repo"]}, pager=broken, now=NOW, apply=True)
    assert report["classes"]["C"] == 4
    assert "settled" not in report["actions"]
    assert all(
        "pull request list unavailable" in row["skip_reason"] for row in report["records"] if row["class"] == "C"
    )
    assert _snapshot(tasks_dir) == before


def test_unavailable_repository_evidence_is_class_d(tasks_dir, mixed, tmp_path):
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    report = str_mod.settle_stale(tasks_dir, repo_checkouts={SLUG: not_a_repo}, pager=mixed["pager"], now=NOW)
    assert report["classes"] == {"A": 0, "B": 0, "C": 0, "D": 9}
    assert mixed["pager"].calls == []


def test_pull_index_pages_until_the_oldest_task_start():
    start = NOW - timedelta(days=5)
    pulls = [
        {**_merged(f"codex/b{i}", i, NOW - timedelta(hours=i)), "updated_at": (NOW - timedelta(hours=i)).isoformat()}
        for i in range(250)
    ]
    pager = FakePager(pulls)
    index = str_mod.build_pull_index(SLUG, oldest_start=start, pager=pager, max_pages=10)
    # Page 1 ends ~99h back (after the 5-day start); page 2 ends ~199h back (before it).
    assert [call[1] for call in pager.calls] == [1, 2]
    assert index.covered_since is None and index.error is None

    capped = str_mod.build_pull_index(SLUG, oldest_start=start, pager=FakePager(pulls), max_pages=1)
    assert capped.covered_since == NOW - timedelta(hours=99)


def test_candidate_older_than_the_pull_coverage_is_skipped(tasks_dir, mixed):
    filler = [
        {
            "number": 1000 + i,
            "merged_at": None,
            "updated_at": (NOW - timedelta(minutes=i)).isoformat(),
            "head": {"ref": f"other/{i}", "repo": {"full_name": SLUG}},
        }
        for i in range(str_mod.PR_PAGE_SIZE)
    ]
    mixed["pager"].pulls[:0] = filler
    report = _run(tasks_dir, mixed, max_pr_pages=1, apply=True)
    rows = [row for row in report["records"] if row["class"] == "C"]
    assert rows and all("does not reach back" in row["skip_reason"] for row in rows)
    assert all(row["action"] == "report" for row in rows)


def _settle(tasks_dir: Path, repo: Path, pulls: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return str_mod.settle_stale(tasks_dir, repo_checkouts={SLUG: repo}, pager=FakePager(pulls), now=NOW, **kwargs)


@pytest.mark.parametrize("head_field", ["final", "legacy", "neither"])
def test_recorded_final_head_classifies_orphaned_work(tasks_dir, repo, head_field):
    sha = _orphan_commit(repo, f"head-{head_field}")
    fields: dict[str, Any] = {"commits_ahead": 1, "worktree_dirty_on_exit": True}
    if head_field == "final":
        fields["final_branch_head_commit"] = sha
    elif head_field == "legacy":
        fields["auto_finalize"] = _auto_finalized(sha)
    _record(tasks_dir, f"head-{head_field}", **fields)

    row = _by_file(_settle(tasks_dir, repo, []))[f"head-{head_field}.json"]

    assert row["class"] == ("D" if head_field == "neither" else "C")
    assert row["evidence"]["recorded_commits"] == ([] if head_field == "neither" else [sha])


def test_renamed_branch_keeps_its_record_out_of_class_c(tasks_dir, repo):
    """Sol's probe: the recorded branch name is gone because the branch was renamed, not deleted."""
    _git(repo, "checkout", "-b", "codex/renamed")
    (repo / "work.txt").write_text("unpushed\n")
    _git(repo, "add", "work.txt")
    _git(repo, "commit", "-m", "unpushed")
    work_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-m", "codex/renamed", "rescue/renamed")
    # The record names no commit, so commits_ahead > 0 alone keeps it out of class C.
    _record(tasks_dir, "renamed", commits_ahead=1)
    # The record names the commit, and the renamed branch still holds it.
    _record(
        tasks_dir,
        "renamed-named",
        commits_ahead=1,
        worktree_dirty_on_exit=True,
        auto_finalize=_auto_finalized(work_sha),
    )
    # The recorded commit was published on origin under another name only.
    pushed_sha = _orphan_commit(repo, "pushed")
    _git(repo, "push", "origin", f"{pushed_sha}:refs/heads/elsewhere/pushed")
    _record(tasks_dir, "pushed-elsewhere", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(pushed_sha))
    # A recorded commit this checkout has never seen cannot be proven gone.
    _record(tasks_dir, "unknown-commit", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized("ab" * 20))
    before = _snapshot(tasks_dir)

    report = _settle(tasks_dir, repo, [], apply=True)

    rows = _by_file(report)
    assert report["classes"] == {"A": 1, "B": 1, "C": 0, "D": 2}
    assert rows["renamed.json"]["class"] == "D"
    assert "names no commit" in rows["renamed.json"]["skip_reason"]
    assert rows["renamed-named.json"]["class"] == "B"
    assert rows["renamed-named.json"]["evidence"]["refs_containing_commit"] == ["refs/heads/rescue/renamed"]
    assert rows["pushed-elsewhere.json"]["class"] == "A"
    assert rows["pushed-elsewhere.json"]["evidence"]["origin_heads_at_commit"] == ["elsewhere/pushed"]
    assert rows["unknown-commit.json"]["class"] == "D"
    assert "not in the local object store" in rows["unknown-commit.json"]["skip_reason"]
    assert _snapshot(tasks_dir) == before


def test_unfetched_remote_branch_descending_from_the_recorded_commit_is_not_class_c(tasks_dir, repo):
    """Sol r2: an origin branch this checkout never fetched has advanced past the recorded commit."""
    work_sha = _orphan_commit(repo, "advanced")
    _git(repo, "checkout", "-b", "tmp/descendant", work_sha)
    (repo / "later.txt").write_text("later\n")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later")
    _git(repo, "push", "origin", "tmp/descendant:refs/heads/rescue/advanced")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", "tmp/descendant")
    # The checkout has not fetched it: no local or remote-tracking ref holds the work.
    _git(repo, "update-ref", "-d", "refs/remotes/origin/rescue/advanced")
    assert work_sha not in _git(repo, "rev-list", "--all").split()
    _record(tasks_dir, "advanced", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(work_sha))
    before = _snapshot(tasks_dir)

    row = _by_file(_settle(tasks_dir, repo, []))["advanced.json"]

    assert row["class"] == "A"
    assert row["evidence"]["refs_containing_commit"] == [f"{SCAN_PREFIX}/rescue/advanced"]
    # The scan namespace is private: the checkout's own remote-tracking refs are untouched.
    assert "rescue/advanced" not in _git(repo, "for-each-ref", "refs/remotes/origin")
    assert _snapshot(tasks_dir) == before


def _descending_branch_only_on_origin(repo: Path, name: str) -> str:
    """A recorded commit whose only holder is an origin branch that has advanced past it."""
    work_sha = _orphan_commit(repo, name)
    _git(repo, "checkout", "-b", "tmp/descendant", work_sha)
    (repo / "later.txt").write_text("later\n")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later")
    _git(repo, "push", "origin", f"tmp/descendant:refs/heads/rescue/{name}")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", "tmp/descendant")
    _git(repo, "update-ref", "-d", f"refs/remotes/origin/rescue/{name}")
    assert work_sha not in _git(repo, "rev-list", "--all").split()
    return work_sha


def test_narrow_configured_refspec_still_finds_the_descending_branch(tasks_dir, repo):
    """Sol r3: a fetch through origin's own refspec would never bring rescue/* in."""
    work_sha = _descending_branch_only_on_origin(repo, "narrow")
    _git(repo, "config", "--replace-all", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
    _git(repo, "fetch", "--prune", "origin")
    assert work_sha not in _git(repo, "rev-list", "--all").split()
    _record(tasks_dir, "narrow", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(work_sha))

    report = _settle(tasks_dir, repo, [], apply=True)

    row = _by_file(report)["narrow.json"]
    assert row["class"] == "A"
    assert row["evidence"]["refs_containing_commit"] == [f"{SCAN_PREFIX}/rescue/narrow"]
    assert "settled" not in report["actions"]
    assert _git(repo, "config", "--get-all", "remote.origin.fetch") == "+refs/heads/main:refs/remotes/origin/main"


def test_scan_namespace_is_pruned(tasks_dir, repo):
    _record(tasks_dir, "no-commits")
    _git(repo, "push", "origin", "main:refs/heads/doomed")
    _settle(tasks_dir, repo, [])
    assert f"{SCAN_PREFIX}/doomed" in _git(repo, "for-each-ref", "--format=%(refname)", SCAN_PREFIX)
    _git(repo, "push", "origin", ":refs/heads/doomed")
    _settle(tasks_dir, repo, [])
    assert _git(repo, "for-each-ref", "--format=%(refname)", SCAN_PREFIX).split() == [f"{SCAN_PREFIX}/main"]


def test_git_config_env_redirect_is_ignored(tasks_dir, repo, tmp_path, monkeypatch):
    """Sol r3: inherited GIT_CONFIG_* rewrites the fetch URL to a repository without the rescue branch."""
    work_sha = _descending_branch_only_on_origin(repo, "redirected")
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(decoy))
    _git(repo, "push", str(decoy), "main")
    origin = str(tmp_path / "origin.git")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", f"url.{decoy}.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", origin)
    monkeypatch.setenv("GIT_CONFIG_PARAMETERS", f"'url.{decoy}.insteadof'='{origin}'")
    # Under the inherited environment, unscrubbed, the URL resolves to the decoy.
    unscrubbed = subprocess.run(
        ["git", "ls-remote", "--get-url", origin], cwd=repo, capture_output=True, text=True, check=True, timeout=30
    )
    assert unscrubbed.stdout.strip() == str(decoy)
    _record(tasks_dir, "redirected", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(work_sha))

    row = _by_file(_settle(tasks_dir, repo, [], apply=True))["redirected.json"]

    assert row["class"] == "A"
    assert row["evidence"]["refs_containing_commit"] == [f"{SCAN_PREFIX}/rescue/redirected"]


SECRET = "lu_synthetic_TOKEN_9f8e7d6c5b4a39281706"


def test_checkout_config_rewrite_refuses_the_fetch_and_hides_credentials(tasks_dir, repo, tmp_path):
    """``url.*.insteadOf`` in the checkout's own config would silently change which repository is fetched."""
    origin = str(tmp_path / "origin.git")
    _git(repo, "config", f"url.https://x-access-token:{SECRET}@example.invalid/r.git.insteadOf", origin)
    _record(tasks_dir, "no-commits")

    report = _settle(tasks_dir, repo, [], apply=True)

    row = _by_file(report)["no-commits.json"]
    assert row["class"] == "D"
    assert "refusing to fetch" in row["skip_reason"]
    assert "https://example.invalid/r.git" in row["evidence"]["fetch_failed"]
    assert SECRET not in json.dumps(report) and "x-access-token" not in json.dumps(report)


def test_git_error_text_never_carries_credentials(tasks_dir, mixed, monkeypatch, capsys):
    """Sol r3: the fetch error line was copied into the report verbatim."""
    real_git = str_mod._git
    stderr = (
        f"fatal: unable to access 'https://x-access-token:{SECRET}@github.com/owner/repo.git/': "
        f"The requested URL returned error: 403 token={SECRET}\n"
    )

    def leaky_fetch(args, **kwargs):
        if args[0] == "fetch":
            return subprocess.CompletedProcess(["git", *args], 128, "", stderr)
        return real_git(args, **kwargs)

    monkeypatch.setattr(str_mod, "_git", leaky_fetch)
    report = _run(tasks_dir, mixed)
    assert "unable to access 'https://github.com/owner/repo.git/'" in report["records"][0]["skip_reason"]
    assert SECRET not in json.dumps(report)

    assert str_mod.main(["settle-stale", "--tasks-dir", str(tasks_dir)]) == 0
    assert SECRET not in capsys.readouterr().out


def test_gh_error_text_never_carries_credentials(monkeypatch):
    def failing_gh(*_args, **_kwargs):
        return subprocess.CompletedProcess(["gh"], 1, "", f"error: https://user:{SECRET}@api.github.com denied\n")

    monkeypatch.setattr(str_mod.subprocess, "run", failing_gh)
    index = str_mod.build_pull_index(SLUG, oldest_start=None, pager=str_mod.gh_pull_page, max_pages=1)
    assert index.error and "https://api.github.com denied" in index.error
    assert SECRET not in index.error


def test_failed_fetch_keeps_every_record_of_the_repository_out_of_class_c(tasks_dir, mixed, monkeypatch):
    real_git = str_mod._git

    def offline_fetch(args, **kwargs):
        if args[0] == "fetch":
            return subprocess.CompletedProcess(["git", *args], 128, "", "fatal: unable to access origin\n")
        return real_git(args, **kwargs)

    monkeypatch.setattr(str_mod, "_git", offline_fetch)
    before = _snapshot(tasks_dir)

    report = _run(tasks_dir, mixed, apply=True)

    rows = _by_file(report)
    assert report["classes"] == {"A": 0, "B": 0, "C": 0, "D": 9}
    for name in ("published.json", "local-only.json", "merged.json", "no-commits.json", "crashed.json"):
        assert rows[name]["class"] == "D"
        assert rows[name]["skip_reason"].startswith("fetch_failed: git fetch ")
        assert "failed: fatal: unable to access origin" in rows[name]["skip_reason"]
    assert "settled" not in report["actions"]
    assert mixed["pager"].calls == []
    assert _snapshot(tasks_dir) == before


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"commits_ahead": 3}, "commits_ahead=3 but the record names no commit"),
        ({"commits_ahead": None}, "commits_ahead=None but the record names no commit"),
        ({"worktree_dirty_on_exit": True}, "uncommitted work at exit"),
        ({"worktree_dirty_on_exit": None}, "uncommitted work at exit"),
    ],
)
def test_work_without_a_recorded_commit_is_never_class_c(tasks_dir, repo, fields, reason):
    _record(tasks_dir, "unnamed-work", **fields)
    row = _by_file(_settle(tasks_dir, repo, []))["unnamed-work.json"]
    assert row["class"] == "D"
    assert reason in row["skip_reason"]


def test_reused_branch_name_pr_is_never_claimed_as_done(tasks_dir, repo):
    """Sol's probe: a later task reused the head ref and its pull request merged."""
    _record(tasks_dir, "reused")  # clean exit, no commits: names no commit
    own_sha = _orphan_commit(repo, "own")
    _record(tasks_dir, "reused-named", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(own_sha))
    later = OLD_FINISH + timedelta(days=2)
    pulls = [_merged("codex/reused", 11, later), _merged("codex/reused-named", 12, later)]
    before = _snapshot(tasks_dir)

    report = _settle(tasks_dir, repo, pulls, apply=True)

    rows = _by_file(report)
    for name, number in (("reused.json", 11), ("reused-named.json", 12)):
        assert rows[name]["class"] == "D", name
        assert rows[name]["action"] == "report"
        assert "outcome" not in rows[name]
        assert rows[name]["skip_reason"].startswith(f"ambiguous: merged PR #{number} reuses branch")
        assert rows[name]["evidence"]["untied_merged_prs"] == [number]
    assert _snapshot(tasks_dir) == before


def test_done_needs_a_pull_request_tied_by_commit_identity(tasks_dir, repo):
    # Renamed, then merged from the new name: the head sha still ties the PR to the task.
    renamed_sha = _orphan_commit(repo, "renamed-pr")
    _record(tasks_dir, "renamed-pr", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(renamed_sha))
    # More commits landed on the branch after the task: the PR head descends from the recorded commit.
    _git(repo, "checkout", "-b", "tmp/extended")
    for step in ("one", "two"):
        (repo / "extended.txt").write_text(f"{step}\n")
        _git(repo, "add", "extended.txt")
        _git(repo, "commit", "-m", step)
        if step == "one":
            recorded_sha = _git(repo, "rev-parse", "HEAD")
    extended_head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", "tmp/extended")
    _record(tasks_dir, "extended", worktree_dirty_on_exit=True, auto_finalize=_auto_finalized(recorded_sha))
    later = OLD_FINISH + timedelta(days=1)
    pulls = [
        _merged("rescue/renamed-pr", 21, later, head_sha=renamed_sha),
        _merged("codex/extended", 22, later, head_sha=extended_head),
    ]

    report = _settle(tasks_dir, repo, pulls, apply=True)

    rows = _by_file(report)
    assert (rows["renamed-pr.json"]["outcome"], rows["renamed-pr.json"]["merged_pr"]["number"]) == ("done", 21)
    assert (rows["extended.json"]["outcome"], rows["extended.json"]["merged_pr"]["number"]) == ("done", 22)
    assert json.loads((tasks_dir / "extended.json").read_text())["status"] == "done"


# ---------------------------------------------------------------------------
# archive / restore
# ---------------------------------------------------------------------------


def _terminal(tasks_dir: Path, name: str, *, status: str = "done", age_days: float = 20, **fields: Any) -> Path:
    path = tasks_dir / f"{name}.json"
    record = {
        "task_id": name,
        "status": status,
        "finished_at": (NOW - timedelta(days=age_days)).isoformat(),
        "result_file": str(tasks_dir / f"{name}.result"),
        **fields,
    }
    path.write_text(json.dumps(record))
    return path


def test_archive_round_trip_moves_record_with_sidecars(tasks_dir):
    _terminal(tasks_dir, "old-done")
    (tasks_dir / "old-done.result").write_text("reply\n")
    (tasks_dir / "old-done.snapshots").mkdir()
    (tasks_dir / "old-done.snapshots" / "read_only_checkout_pre.json").write_text("{}")
    # A --force-new archived record keeps its own stamped sidecars.
    stamp = "20260901T000000123456Z"
    _terminal(tasks_dir, f"redo.{stamp}.archived", status="failed")
    (tasks_dir / f"redo.{stamp}.archived.result").write_text("old reply\n")
    (tasks_dir / f"redo.snapshots.{stamp}.archived").mkdir()
    (tasks_dir / f"redo.snapshots.{stamp}.archived" / "read_only_checkout_post.json").write_text("{}")
    before = _snapshot(tasks_dir)

    dry = str_mod.archive_terminal(tasks_dir, now=NOW)
    assert dry["actions"] == {"would_archive": 2}
    assert _snapshot(tasks_dir) == before

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    assert report["actions"] == {"archived": 2}
    archive = tasks_dir / "archive"
    assert sorted(path.name for path in tasks_dir.iterdir()) == ["archive"]
    assert (archive / "old-done.snapshots" / "read_only_checkout_pre.json").is_file()
    assert (archive / f"redo.snapshots.{stamp}.archived" / "read_only_checkout_post.json").is_file()
    assert task_record_store.locate_task_record(tasks_dir, "old-done") == archive / "old-done.json"

    restored = str_mod.restore_archived(tasks_dir, ["old-done", f"redo.{stamp}.archived.json"], apply=True)
    assert restored["actions"] == {"restored": 2}
    assert {key: value[0] for key, value in _snapshot(tasks_dir).items()} == {
        key: value[0] for key, value in before.items()
    }
    assert task_record_store.locate_task_record(tasks_dir, "old-done") == tasks_dir / "old-done.json"


def test_archive_selects_only_old_terminal_records_without_a_live_worktree(tasks_dir, tmp_path):
    linked = tmp_path / "linked-wt"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: /elsewhere\n")
    # A read-only task ran in a primary checkout (``.git`` directory), which no task owns.
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    _terminal(tasks_dir, "old-done")
    _terminal(tasks_dir, "young-done", age_days=3)
    _terminal(tasks_dir, "old-needs-finalize", status="needs_finalize")
    _terminal(tasks_dir, "old-running", status="running")
    _terminal(tasks_dir, "old-queued", status="queued")
    _terminal(tasks_dir, "old-with-worktree", worktree_path=str(linked))
    _terminal(tasks_dir, "old-read-only", status="failed", cwd=str(primary))

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    assert sorted(row["file"] for row in report["records"]) == ["old-done.json", "old-read-only.json"]
    assert report["kept_hot"] == {"worktree path still exists": 1}
    assert report["younger_left_alone"] == 1
    hot = sorted(path.name for path in tasks_dir.glob("*.json"))
    assert hot == [
        "old-needs-finalize.json",
        "old-queued.json",
        "old-running.json",
        "old-with-worktree.json",
        "young-done.json",
    ]


def test_archive_never_overwrites_and_claim_scan_ignores_archive(tasks_dir, tmp_path):
    archive = tasks_dir / "archive"
    archive.mkdir()
    (archive / "dup.json").write_text('{"status": "done", "task_id": "dup", "keep": true}')
    _terminal(tasks_dir, "dup")
    (tasks_dir / "dup.result").write_text("new reply\n")

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    moved = report["records"][0]["moved"]
    assert json.loads((archive / "dup.json").read_text())["keep"] is True
    assert moved[0].startswith("dup.") and moved[0].endswith(".archived.json")
    assert moved[1] == moved[0].removesuffix(".json") + ".result"
    # An unfinished record parked in archive/ (never produced by archive) is not a claim.
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (archive / "parked.json").write_text(
        json.dumps({"task_id": "parked", "status": "running", "worktree_path": str(worktree)})
    )
    assert worktree_claims.active_worktree_claim_refusal(worktree, tasks_dir=tasks_dir, repo_root=tmp_path) is None


def test_restore_refuses_to_overwrite_a_hot_record(tasks_dir):
    _terminal(tasks_dir, "again")
    str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    _terminal(tasks_dir, "again", status="failed", age_days=1)
    report = str_mod.restore_archived(tasks_dir, ["again"], apply=True)
    assert report["records"][0]["action"] == "skipped"
    assert json.loads((tasks_dir / "again.json").read_text())["status"] == "failed"


def test_cli_defaults_to_dry_run_json(tasks_dir, capsys):
    _terminal(tasks_dir, "old-done")
    assert str_mod.main(["archive", "--tasks-dir", str(tasks_dir), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "dry-run"
    assert (tasks_dir / "old-done.json").is_file()
    assert str_mod.main(["archive", "--tasks-dir", str(tasks_dir / "missing")]) == str_mod.EXIT_USAGE


@pytest.mark.parametrize("names_checkout", [True, False])
def test_archive_skips_a_record_whose_lock_is_held(tasks_dir, tmp_path, names_checkout):
    """Archive takes the lock settle takes: the checkout's, else the record file's own."""
    checkout = tmp_path / "gone-wt"
    fields = {"worktree_path": str(checkout)} if names_checkout else {}
    record_path = _terminal(tasks_dir, "locked", **fields)
    held, release = threading.Event(), threading.Event()

    def holder():
        with delegate.worktree_lock(str(checkout if names_checkout else record_path), timeout_s=1):
            held.set()
            release.wait(10)

    thread = threading.Thread(target=holder)
    thread.start()
    try:
        assert held.wait(5)
        report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True, lock_timeout_s=0.1)
    finally:
        release.set()
        thread.join()

    row = report["records"][0]
    assert (row["action"], row["skip_reason"]) == ("skipped", worktree_claims.LOCK_BUSY)
    assert record_path.is_file()


def test_archive_rechecks_the_record_under_its_lock(tasks_dir, tmp_path):
    reattached = tmp_path / "reattached-wt"
    _terminal(tasks_dir, "revived")
    _terminal(tasks_dir, "touched")
    _terminal(tasks_dir, "reattached", worktree_path=str(reattached))
    _terminal(tasks_dir, "untouched")

    def live_writer(path: Path) -> None:
        stat = path.stat()
        if path.name == "revived.json":
            # Rewritten as running with its mtime restored: only the status re-check sees it.
            path.write_text(json.dumps({**json.loads(path.read_text()), "status": "running"}))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        elif path.name == "touched.json":
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
        elif path.name == "reattached.json":
            reattached.mkdir()

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True, before_move=live_writer)

    rows = {row["file"]: (row["action"], row.get("skip_reason")) for row in report["records"]}
    assert rows == {
        "revived.json": ("skipped", "record no longer terminal"),
        "touched.json": ("skipped", "record changed since selection"),
        "reattached.json": ("skipped", "worktree path still exists"),
        "untouched.json": ("archived", None),
    }
    assert sorted(path.name for path in tasks_dir.glob("*.json")) == ["reattached.json", "revived.json", "touched.json"]


def test_archive_keeps_records_that_still_own_a_path(tasks_dir, tmp_path):
    half_removed = tmp_path / "half-removed"  # a checkout directory without its .git file
    half_removed.mkdir()
    acp_runtime = tmp_path / "acp-runtime"
    acp_runtime.mkdir()
    _terminal(tasks_dir, "half-removed", worktree_path=str(half_removed))
    _terminal(tasks_dir, "cwd-owner", cwd=str(half_removed))
    _terminal(
        tasks_dir,
        "acp-owner",
        worktree_path=str(tmp_path / "gone-wt"),
        acp_runtime_paths=[str(tmp_path / "acp-gone"), str(acp_runtime)],
    )
    _terminal(tasks_dir, "acp-gone", acp_runtime_paths=[str(tmp_path / "acp-gone")])

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    assert [row["file"] for row in report["records"]] == ["acp-gone.json"]
    assert report["kept_hot"] == {"worktree path still exists": 2, "ACP runtime path still exists": 1}
    assert sorted(path.name for path in tasks_dir.glob("*.json")) == [
        "acp-owner.json",
        "cwd-owner.json",
        "half-removed.json",
    ]


def test_archive_puts_back_a_record_replaced_during_the_move(tasks_dir, monkeypatch):
    target = _terminal(tasks_dir, "raced")
    (tasks_dir / "raced.result").write_text("reply\n")
    real_rename = os.rename
    raced: list[bool] = []

    def racing_rename(src, dst):
        if Path(src) == target and not raced:
            # A writer replaces the record after the final re-check, before the rename.
            raced.append(True)
            delegate._write_state_atomic(target, {**json.loads(target.read_text()), "status": "running"})
        real_rename(src, dst)

    monkeypatch.setattr(str_mod.os, "rename", racing_rename)
    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert (row["action"], row["skip_reason"]) == ("skipped", "record replaced during the move; put back")
    assert json.loads(target.read_text())["status"] == "running"
    assert (tasks_dir / "raced.result").is_file()
    assert not list((tasks_dir / "archive").iterdir())


def _link_after_writer(monkeypatch, target: Path, write: Callable[[], None]) -> list[bool]:
    """Make a writer create ``target`` just before the tool links a file onto it."""
    real_link = os.link
    raced: list[bool] = []

    def racing_link(src, dst, **kwargs):
        if Path(dst) == target and not raced:
            raced.append(True)
            write()
        return real_link(src, dst, **kwargs)

    monkeypatch.setattr(str_mod.os, "link", racing_link)
    return raced


def test_restore_keeps_a_hot_record_a_writer_created_after_the_check(tasks_dir, monkeypatch):
    _terminal(tasks_dir, "revived")
    (tasks_dir / "revived.result").write_text("old reply\n")
    str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    hot = tasks_dir / "revived.json"
    raced = _link_after_writer(
        monkeypatch, hot, lambda: delegate._write_state_atomic(hot, {"task_id": "revived", "status": "running"})
    )

    report = str_mod.restore_archived(tasks_dir, ["revived"], apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "skipped"
    assert "a writer created revived.json" in row["skip_reason"]
    assert json.loads(hot.read_text())["status"] == "running"
    assert json.loads((tasks_dir / "archive" / "revived.json").read_text())["status"] == "done"
    assert (tasks_dir / "archive" / "revived.result").read_text() == "old reply\n"
    assert not (tasks_dir / "revived.result").exists()


def _rename_after_writer(monkeypatch, target: Path, write: Callable[[], None]) -> list[bool]:
    """Make a writer act on ``target`` just before the tool renames a directory onto it."""
    real_rename = os.rename
    raced: list[bool] = []

    def racing_rename(src, dst):
        if Path(dst) == target and not raced:
            raced.append(True)
            write()
        return real_rename(src, dst)

    monkeypatch.setattr(str_mod.os, "rename", racing_rename)
    return raced


SNAPSHOT_FILES = {"read_only_checkout_pre.json": '{"old": "pre"}', "read_only_checkout_post.json": '{"old": "post"}'}


def _with_snapshots(tasks_dir: Path, name: str) -> Path:
    _terminal(tasks_dir, name)
    (tasks_dir / f"{name}.result").write_text("old reply\n")
    snapshots = tasks_dir / f"{name}.snapshots"
    snapshots.mkdir()
    for file_name, text in SNAPSHOT_FILES.items():
        (snapshots / file_name).write_text(text)
    return snapshots


def _contents(directory: Path) -> dict[str, str]:
    return {path.name: path.read_text() for path in directory.iterdir()}


def _writer_child(directory: Path) -> Callable[[], None]:
    """A writer that creates ``directory`` holding one child named like an original snapshot."""

    def write() -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "read_only_checkout_post.json").write_text("writer\n")

    return write


def test_restore_keeps_a_result_a_writer_created_after_the_check(tasks_dir, monkeypatch):
    _with_snapshots(tasks_dir, "revived")
    str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    target = tasks_dir / "revived.result"
    raced = _link_after_writer(monkeypatch, target, lambda: target.write_text("writer\n"))

    report = str_mod.restore_archived(tasks_dir, ["revived"], apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "restored"
    assert row["kept_in_archive"] == [str(tasks_dir / "archive" / "revived.result")]
    assert target.read_text() == "writer\n"
    assert (tasks_dir / "archive" / "revived.result").read_text() == "old reply\n"
    assert json.loads((tasks_dir / "revived.json").read_text())["status"] == "done"
    assert _contents(tasks_dir / "revived.snapshots") == SNAPSHOT_FILES


def test_restore_keeps_a_snapshot_directory_whole_when_a_writer_fills_its_hot_name(tasks_dir, monkeypatch):
    """A writer's child in the hot snapshot directory keeps the archived one whole, never split."""
    _with_snapshots(tasks_dir, "revived")
    str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    hot = tasks_dir / "revived.snapshots"
    raced = _rename_after_writer(monkeypatch, hot, _writer_child(hot))

    report = str_mod.restore_archived(tasks_dir, ["revived"], apply=True)

    row = report["records"][0]
    archived = tasks_dir / "archive" / "revived.snapshots"
    assert raced and row["action"] == "restored"
    assert row["kept_in_archive"] == [str(archived)]
    assert _contents(archived) == SNAPSHOT_FILES
    assert _contents(hot) == {"read_only_checkout_post.json": "writer\n"}
    assert (tasks_dir / "revived.result").read_text() == "old reply\n"


def test_restore_moves_a_snapshot_directory_onto_an_empty_one(tasks_dir, monkeypatch):
    _with_snapshots(tasks_dir, "revived")
    str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)
    hot = tasks_dir / "revived.snapshots"
    raced = _rename_after_writer(monkeypatch, hot, hot.mkdir)

    report = str_mod.restore_archived(tasks_dir, ["revived"], apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "restored" and "kept_in_archive" not in row
    assert _contents(hot) == SNAPSHOT_FILES
    assert not (tasks_dir / "archive" / "revived.snapshots").exists()


def test_archive_moves_a_snapshot_directory_onto_an_empty_one(tasks_dir):
    _with_snapshots(tasks_dir, "empty-dest")
    (tasks_dir / "archive" / "empty-dest.snapshots").mkdir(parents=True)

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert row["action"] == "archived"
    assert row["moved"] == ["empty-dest.json", "empty-dest.result", "empty-dest.snapshots"]
    assert _contents(tasks_dir / "archive" / "empty-dest.snapshots") == SNAPSHOT_FILES
    assert sorted(path.name for path in tasks_dir.iterdir()) == ["archive"]


def test_archive_moves_a_snapshot_directory_whole_past_a_writer_filled_name(tasks_dir, monkeypatch):
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    _with_snapshots(tasks_dir, "clash")
    foreign = tasks_dir / "archive" / "clash.snapshots"
    raced = _rename_after_writer(monkeypatch, foreign, _writer_child(foreign))

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    stamped = tasks_dir / "archive" / f"clash.{STAMP}.archived.snapshots"
    assert raced and row["action"] == "archived"
    assert row["moved"] == ["clash.json", "clash.result", stamped.name]
    assert _contents(stamped) == SNAPSHOT_FILES
    assert _contents(foreign) == {"read_only_checkout_post.json": "writer\n"}
    assert sorted(path.name for path in tasks_dir.iterdir()) == ["archive"]
    assert _no_staging_left(tasks_dir)


def test_archive_never_splits_a_snapshot_directory(tasks_dir, monkeypatch):
    """Sol r4 probe: a writer fills the snapshot directory's archive name mid-move, its stamped names are taken.

    Child-by-child moves left one original snapshot in the archive and returned
    the other hot. The directory now goes back whole to its hot name.
    """
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    hot = _with_snapshots(tasks_dir, "split")
    archive = tasks_dir / "archive"
    taken = [archive / f"split.{STAMP}.archived.snapshots", archive / f"split.{STAMP}.{os.getpid()}.archived.snapshots"]
    for directory in taken:
        _writer_child(directory)()
    foreign = archive / "split.snapshots"
    raced = _rename_after_writer(monkeypatch, foreign, _writer_child(foreign))

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "error" and row["moved"] == ["split.json", "split.result"]
    assert "split.snapshots not archived (archive already holds split.snapshots and its stamped name)" in row["error"]
    assert row["error"].endswith(f"left at {hot}")
    assert _contents(hot) == SNAPSHOT_FILES
    for directory in (foreign, *taken):
        assert _contents(directory) == {"read_only_checkout_post.json": "writer\n"}
    assert json.loads((archive / "split.json").read_text())["status"] == "done"
    assert _no_staging_left(tasks_dir)


def test_archive_parks_a_snapshot_directory_whole_when_its_hot_name_is_retaken(tasks_dir, monkeypatch):
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    hot = _with_snapshots(tasks_dir, "parked")
    archive = tasks_dir / "archive"
    for name in (
        "parked.snapshots",
        f"parked.{STAMP}.archived.snapshots",
        f"parked.{STAMP}.{os.getpid()}.archived.snapshots",
    ):
        _writer_child(archive / name)()
    # Every archive name is taken, so the directory heads home; a writer fills that name first.
    raced = _rename_after_writer(monkeypatch, hot, _writer_child(hot))

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "error"
    parked = Path(row["error"].rsplit("left at ", 1)[1])
    assert parked.parent == archive and parked.name.startswith("parked.snapshots.unplaced-")
    assert _contents(parked) == SNAPSHOT_FILES
    assert _contents(hot) == {"read_only_checkout_post.json": "writer\n"}
    assert _no_staging_left(tasks_dir)


def test_archive_never_replaces_a_destination_created_during_the_move(tasks_dir, monkeypatch):
    _terminal(tasks_dir, "clash")
    (tasks_dir / "clash.result").write_text("reply\n")
    foreign = tasks_dir / "archive" / "clash.json"
    raced = _link_after_writer(monkeypatch, foreign, lambda: foreign.write_text("foreign\n"))

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert raced and row["action"] == "archived"
    assert foreign.read_text() == "foreign\n"
    record_name, result_name = row["moved"]
    assert record_name.endswith(".archived.json") and result_name == record_name.removesuffix(".json") + ".result"
    assert json.loads((foreign.parent / record_name).read_text())["status"] == "done"
    assert (foreign.parent / result_name).read_text() == "reply\n"
    assert sorted(path.name for path in tasks_dir.iterdir()) == ["archive"]
    assert not list(foreign.parent.glob(".*.moving"))


STAMP = "20260924T120000000000Z"


def _fill_archive_names(archive: Path, file_name: str) -> dict[str, bytes]:
    """Take a file's archive name and both stamped fallbacks, as a racing run could."""
    archive.mkdir(exist_ok=True)
    stem, suffix = file_name.rsplit(".", 1)
    names = [file_name, f"{stem}.{STAMP}.archived.{suffix}", f"{stem}.{STAMP}.{os.getpid()}.archived.{suffix}"]
    for name in names:
        (archive / name).write_bytes(f"foreign {name}\n".encode())
    return {name: (archive / name).read_bytes() for name in names}


def _no_staging_left(tasks_dir: Path) -> bool:
    return not list(tasks_dir.rglob(".*.moving"))


def test_archive_double_collision_puts_the_record_back(tasks_dir, monkeypatch):
    """Sol r3: both archive names taken used to raise with the record only at its hidden staging name."""
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    record = _terminal(tasks_dir, "twice")
    (tasks_dir / "twice.result").write_text("reply\n")
    original = record.read_bytes()
    foreign = _fill_archive_names(tasks_dir / "archive", "twice.json")

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert row["action"] == "skipped"
    assert row["skip_reason"] == "archive already holds twice.json and its stamped name; record left in place"
    assert record.read_bytes() == original
    assert (tasks_dir / "twice.result").read_text() == "reply\n"
    assert {name: (tasks_dir / "archive" / name).read_bytes() for name in foreign} == foreign
    assert _no_staging_left(tasks_dir)
    assert report["actions"] == {"skipped": 1}


def test_archive_double_collision_with_the_hot_name_retaken_parks_the_record_visibly(tasks_dir, monkeypatch):
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    record = _terminal(tasks_dir, "twice")
    original = record.read_bytes()
    _fill_archive_names(tasks_dir / "archive", "twice.json")
    raced = _link_after_writer(
        monkeypatch, record, lambda: delegate._write_state_atomic(record, {"task_id": "twice", "status": "running"})
    )

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    parked = Path(row["recover_path"])
    assert raced and row["action"] == "error"
    assert row["error"] == f"archive already holds twice.json and its stamped name; record left at {parked}"
    assert parked.parent == tasks_dir / "archive" and parked.name.startswith("twice.json.unplaced-")
    assert parked.read_bytes() == original
    assert json.loads(record.read_text())["status"] == "running"
    assert _no_staging_left(tasks_dir)
    assert str_mod.main(["archive", "--tasks-dir", str(tasks_dir)]) == 0  # the parked file is no record


def test_archive_double_collision_on_a_sidecar_keeps_it_hot_and_reports_it(tasks_dir, monkeypatch):
    monkeypatch.setattr(delegate, "_archive_stamp", lambda: STAMP)
    _terminal(tasks_dir, "split")
    (tasks_dir / "split.result").write_text("reply\n")
    _fill_archive_names(tasks_dir / "archive", "split.result")

    report = str_mod.archive_terminal(tasks_dir, now=NOW, apply=True)

    row = report["records"][0]
    assert row["action"] == "error" and row["moved"] == ["split.json"]
    assert "split.result not archived (archive already holds split.result and its stamped name)" in row["error"]
    assert row["error"].endswith(f"left at {tasks_dir / 'split.result'}")
    assert (tasks_dir / "split.result").read_text() == "reply\n"
    assert json.loads((tasks_dir / "archive" / "split.json").read_text())["status"] == "done"
    assert _no_staging_left(tasks_dir)
