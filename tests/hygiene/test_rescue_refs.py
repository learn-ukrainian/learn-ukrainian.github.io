"""Rescue-ref classification and deletion, on throwaway repositories only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.hygiene import rescue_refs
from scripts.orchestration import reaper_lifecycle


def git(repo: Path, *args: str, when: str | None = None) -> str:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_") or key.startswith("PRE_COMMIT") or key == "AGENT_NO_MERGE":
            env.pop(key)
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, f"git {args[0]} failed: {result.stderr or result.stdout}"
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    root = tmp_path / "checkout"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "core.hooksPath", "/dev/null")
    git(root, "config", "commit.gpgsign", "false")
    (root / "readme").write_text("base\n", encoding="utf-8")
    git(root, "add", "readme")
    git(root, "commit", "-m", "base", when="2026-10-01T00:00:00Z")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root


def pin(repo: Path, name: str, sha: str) -> str:
    ref = f"refs/reaper-rescue/{name}"
    git(repo, "update-ref", ref, sha)
    return ref


def classes(repo: Path) -> dict[str, str]:
    return {row.ref: row.classification for row in rescue_refs.classify_rescue_refs(repo)}


def journal_events(repo: Path) -> list[dict[str, object]]:
    path = reaper_lifecycle.journal_path(repo)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_contained_ancestor_is_deleted_and_dry_run_keeps_it(repo: Path, tmp_path: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    ref = pin(repo, "contained", sha)
    listing = tmp_path / "listing.json"

    dry = rescue_refs.run(repo, listing=listing)
    assert dry.counts == {"CONTAINED": 1, "PATCH-EQUIVALENT": 0, "UNIQUE": 0}
    assert git(repo, "rev-parse", ref) == sha
    body = json.loads(listing.read_text(encoding="utf-8"))
    assert body["refs"][0]["classification"] == "CONTAINED"
    assert "2026-08-01" in body["window"]

    rescue_refs.run(repo, apply=True, limit=10, listing=tmp_path / "applied.json")
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            timeout=30,
        ).returncode
        != 0
    )
    receipt = next(row for row in journal_events(repo) if row["event"] == "rescue-ref-delete")
    assert receipt["ref"] == ref
    assert receipt["sha"] == sha
    assert receipt["classification"] == "CONTAINED"
    assert receipt["proof"]
    assert str(receipt["at"]).endswith("Z")


def test_other_origin_branch_is_contained(repo: Path, tmp_path: Path) -> None:
    git(repo, "checkout", "-b", "side")
    (repo / "side.txt").write_text("side\n", encoding="utf-8")
    git(repo, "add", "side.txt")
    git(repo, "commit", "-m", "side", when="2026-10-02T00:00:00Z")
    sha = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "-u", "origin", "side")
    git(repo, "checkout", "main")
    ref = pin(repo, "side-tip", sha)

    assert classes(repo)[ref] == "CONTAINED"
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "side.json")
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            timeout=30,
        ).returncode
        != 0
    )


def test_squash_merge_is_patch_equivalent(repo: Path, tmp_path: Path) -> None:
    git(repo, "checkout", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "add", "feature.txt")
    git(repo, "commit", "-m", "feature", when="2026-10-03T00:00:00Z")
    feature = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    git(repo, "merge", "--squash", "feature")
    git(repo, "commit", "-m", "squash feature", when="2026-10-03T01:00:00Z")
    git(repo, "push", "origin", "main")
    ref = pin(repo, "squash", feature)

    found = {row.ref: row for row in rescue_refs.classify_rescue_refs(repo)}
    assert found[ref].classification == "PATCH-EQUIVALENT"
    assert "since 2026-08-01" in found[ref].proof
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "squash.json")
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            timeout=30,
        ).returncode
        != 0
    )


def test_one_unmatched_commit_survives_apply(repo: Path, tmp_path: Path) -> None:
    git(repo, "checkout", "-b", "feature")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "add a", when="2026-10-04T00:00:00Z")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    git(repo, "add", "b.txt")
    git(repo, "commit", "-m", "add b", when="2026-10-04T01:00:00Z")
    tip = git(repo, "rev-parse", "HEAD")
    first = git(repo, "rev-parse", "HEAD~1")
    git(repo, "checkout", "main")
    git(repo, "cherry-pick", first)
    git(repo, "push", "origin", "main")
    ref = pin(repo, "half", tip)

    assert classes(repo)[ref] == "UNIQUE"
    rescue_refs.run(repo, apply=True, limit=20, listing=tmp_path / "half.json")
    assert git(repo, "rev-parse", ref) == tip


def test_commit_without_a_patch_id_is_unique(repo: Path, tmp_path: Path) -> None:
    git(repo, "checkout", "-b", "empty")
    git(repo, "commit", "--allow-empty", "-m", "empty", when="2026-10-05T00:00:00Z")
    sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    ref = pin(repo, "empty", sha)

    found = next(row for row in rescue_refs.classify_rescue_refs(repo) if row.ref == ref)
    assert found.classification == "UNIQUE"
    assert "emitted no patch-id" in found.proof
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "empty.json")
    assert git(repo, "rev-parse", ref) == sha


def _clear_tree(repo: Path) -> None:
    git(repo, "read-tree", "--empty")
    for child in repo.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def test_match_older_than_the_window_is_unique(repo: Path, tmp_path: Path) -> None:
    """A patch that exists on main only before 2026-08-01 is not preserved."""
    git(repo, "checkout", "--orphan", "dated")
    _clear_tree(repo)
    (repo / "old.txt").write_text("same\n", encoding="utf-8")
    git(repo, "add", "old.txt")
    git(repo, "commit", "-m", "july file", when="2026-07-15T00:00:00Z")
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "later.txt")
    git(repo, "commit", "-m", "august file", when="2026-08-15T00:00:00Z")
    git(repo, "branch", "-M", "main")
    git(repo, "push", "--force", "origin", "main")
    git(repo, "checkout", "--orphan", "replay")
    _clear_tree(repo)
    (repo / "old.txt").write_text("same\n", encoding="utf-8")
    git(repo, "add", "old.txt")
    git(repo, "commit", "-m", "replay july", when="2026-09-01T00:00:00Z")
    replay = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    ref = pin(repo, "old-match", replay)

    found = next(row for row in rescue_refs.classify_rescue_refs(repo) if row.ref == ref)
    assert found.classification == "UNIQUE"
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "old.json")
    assert git(repo, "rev-parse", ref) == replay


def test_limit_stops_the_batch(repo: Path, tmp_path: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    kept = [pin(repo, f"cap-{index}", sha) for index in range(3)]
    rescue_refs.run(repo, apply=True, limit=2, listing=tmp_path / "cap.json")
    still = [
        ref
        for ref in kept
        if subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            timeout=30,
        ).returncode
        == 0
    ]
    assert len(still) == 1


def test_moved_ref_is_skipped(repo: Path) -> None:
    original = git(repo, "rev-parse", "HEAD")
    git(repo, "commit", "--allow-empty", "-m", "other", when="2026-10-06T00:00:00Z")
    moved = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    # The empty commit is not on main. Point the ref at main, classify, then move it.
    ref = pin(repo, "moves", original)
    rows = rescue_refs.classify_rescue_refs(repo)
    git(repo, "update-ref", ref, moved)
    deleted, skipped = rescue_refs._apply(repo, rows, limit=5, lock_timeout_s=5, deleter=rescue_refs.delete_ref)
    assert (deleted, skipped) == (0, 1)
    assert git(repo, "rev-parse", ref) == moved
    assert journal_events(repo)[-1]["reason"] == "ref moved"


def test_compare_and_delete_refuses_a_ref_that_moves_after_the_reread(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = git(repo, "rev-parse", "HEAD")
    git(repo, "commit", "--allow-empty", "-m", "later", when="2026-10-07T00:00:00Z")
    moved = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    ref = pin(repo, "race", original)
    rows = rescue_refs.classify_rescue_refs(repo)
    git(repo, "update-ref", ref, moved)
    monkeypatch.setattr(rescue_refs, "_current_sha", lambda _repo, _ref: original)

    deleted, skipped = rescue_refs._apply(repo, rows, limit=5, lock_timeout_s=5, deleter=rescue_refs.delete_ref)

    assert (deleted, skipped) == (0, 1)
    assert git(repo, "rev-parse", ref) == moved
    assert "compare-and-delete refused" in str(journal_events(repo)[-1]["reason"])


def test_native_operation_refuses_the_batch(repo: Path, tmp_path: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    ref = pin(repo, "busy", sha)
    (repo / ".git" / "MERGE_HEAD").write_text(f"{sha}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="in-progress operation"):
        rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "busy.json")
    assert git(repo, "rev-parse", ref) == sha


def test_receipt_is_durable_before_delete(repo: Path, tmp_path: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    ref = pin(repo, "crash", sha)

    def crash(_repo: Path, _ref: str, _expected: str) -> None:
        raise RuntimeError("crash after receipt")

    with pytest.raises(RuntimeError, match="crash after receipt"):
        rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "crash.json", deleter=crash)
    assert git(repo, "rev-parse", ref) == sha
    receipt = next(row for row in journal_events(repo) if row["event"] == "rescue-ref-delete")
    assert receipt["sha"] == sha
    assert receipt["classification"] == "CONTAINED"


def test_held_reaper_lock_refuses_apply(repo: Path, tmp_path: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    ref = pin(repo, "locked", sha)
    lock = repo / ".git" / "worktree-reaper.lock"
    holder = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl,os,time; fd=os.open(os.environ['LOCK'], os.O_RDWR|os.O_CREAT, 0o600); "
            "fcntl.flock(fd, fcntl.LOCK_EX); os.write(1, b'locked\\n'); time.sleep(30)",
        ],
        env={**os.environ, "LOCK": str(lock)},
        stdout=subprocess.PIPE,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline() == b"locked\n"
        with pytest.raises(RuntimeError, match="another worktree cleanup holds"):
            rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "lock.json", lock_timeout_s=0.2)
    finally:
        holder.terminate()
        holder.wait(timeout=5)
    assert git(repo, "rev-parse", ref) == sha


def test_listing_inside_the_repository_is_refused(repo: Path) -> None:
    sha = git(repo, "rev-parse", "HEAD")
    pin(repo, "local", sha)
    with pytest.raises(rescue_refs.RescueRefError, match="outside the repository"):
        rescue_refs.run(repo, listing=repo / "listing.json")


def test_creation_skips_preserved_tips_and_pins_unique_work(repo: Path) -> None:
    contained = git(repo, "rev-parse", "HEAD")
    ref, err = reaper_lifecycle.create_recovery_ref(repo, branch="codex/contained", head=contained)
    assert (ref, err) == (None, None)
    assert not git(repo, "for-each-ref", "refs/reaper-rescue")

    git(repo, "checkout", "-b", "unique-work")
    (repo / "only-here.txt").write_text("unique\n", encoding="utf-8")
    git(repo, "add", "only-here.txt")
    git(repo, "commit", "-m", "unique", when="2026-10-08T00:00:00Z")
    unique = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    created, create_err = reaper_lifecycle.create_recovery_ref(repo, branch="codex/unique", head=unique)
    assert create_err is None and created is not None
    assert git(repo, "rev-parse", created) == unique

    git(repo, "checkout", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "add", "feature.txt")
    git(repo, "commit", "-m", "feature", when="2026-10-08T01:00:00Z")
    feature = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    git(repo, "merge", "--squash", "feature")
    git(repo, "commit", "-m", "squash feature", when="2026-10-08T02:00:00Z")
    git(repo, "push", "origin", "main")
    skipped, skip_err = reaper_lifecycle.create_recovery_ref(repo, branch="codex/feature", head=feature)
    assert (skipped, skip_err) == (None, None)

    events = [row["event"] for row in journal_events(repo)]
    assert events.count("rescue-skipped") == 2
    proofs = [str(row["proof"]) for row in journal_events(repo) if row["event"] == "rescue-skipped"]
    assert any("ancestor of origin/main" in proof for proof in proofs)
    assert any("patch-id" in proof for proof in proofs)
