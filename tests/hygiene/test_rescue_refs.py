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
    assert receipt["preserving_ref"] == "refs/remotes/origin/main"
    assert receipt["preserving_sha"] == git(repo, "rev-parse", "refs/remotes/origin/main")
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


def _alive(repo: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=repo,
            capture_output=True,
            timeout=30,
        ).returncode
        == 0
    )


def test_whitespace_collision_is_not_patch_equivalent(repo: Path, tmp_path: Path) -> None:
    """Equal stable patch-ids with different indentation are different programs.

    ``git patch-id --stable`` drops whitespace. The feature file prints; the
    main file does not. The rescue ref must survive, and creation must pin it.
    """
    git(repo, "checkout", "-b", "feature")
    feature = "if False:\n    print('inside')\nprint('outside')\n"
    main = "if False:\n    print('inside')\n    print('outside')\n"
    (repo / "program.py").write_text(feature, encoding="utf-8")
    git(repo, "add", "program.py")
    git(repo, "commit", "-m", "feature program", when="2026-10-10T00:00:00Z")
    tip = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    (repo / "program.py").write_text(main, encoding="utf-8")
    git(repo, "add", "program.py")
    git(repo, "commit", "-m", "main program", when="2026-10-10T01:00:00Z")
    main_tip = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "main")
    assert git(repo, "rev-parse", f"{tip}^{{tree}}") != git(repo, "rev-parse", f"{main_tip}^{{tree}}")
    ref = pin(repo, "whitespace", tip)

    found = next(row for row in rescue_refs.classify_rescue_refs(repo) if row.ref == ref)
    assert found.classification == "UNIQUE"
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "whitespace.json")
    assert git(repo, "rev-parse", ref) == tip
    created, error = reaper_lifecycle.create_recovery_ref(repo, branch="feature", head=tip)
    assert error is None and created is not None
    assert git(repo, "rev-parse", created) == tip


def test_revert_then_reapply_is_not_patch_equivalent(repo: Path, tmp_path: Path) -> None:
    """A patch-id that occurs more times on the rescue tip than on main is not preserved.

    Main adds the file and reverts it. The rescue tip adds, reverts, and adds
    again, so the file is still there. Set membership would delete it.
    """
    git(repo, "checkout", "-b", "feature")
    (repo / "toggle.txt").write_text("on\n", encoding="utf-8")
    git(repo, "add", "toggle.txt")
    git(repo, "commit", "-m", "add toggle", when="2026-10-11T00:00:00Z")
    added = git(repo, "rev-parse", "HEAD")
    git(repo, "revert", "--no-edit", added)
    git(repo, "cherry-pick", added)
    tip = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    git(repo, "cherry-pick", added)
    git(repo, "revert", "--no-edit", "HEAD")
    git(repo, "push", "origin", "main")
    assert not (repo / "toggle.txt").exists()
    ref = pin(repo, "reapplied", tip)

    found = next(row for row in rescue_refs.classify_rescue_refs(repo) if row.ref == ref)
    assert found.classification == "UNIQUE"
    rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "reapply.json")
    assert git(repo, "rev-parse", ref) == tip


def test_failed_origin_fetch_refuses_a_stale_contained_ref(repo: Path, tmp_path: Path) -> None:
    """A rewind that fetch cannot see is not containment, and creation still pins the tip."""
    base = git(repo, "rev-parse", "HEAD")
    (repo / "lost.txt").write_text("only on obsolete main\n", encoding="utf-8")
    git(repo, "add", "lost.txt")
    git(repo, "commit", "-m", "later", when="2026-10-12T00:00:00Z")
    tip = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "main")
    remote = tmp_path / "origin.git"
    git(remote, "update-ref", "refs/heads/main", base)
    git(repo, "checkout", "--detach", base)
    git(repo, "branch", "-D", "main")
    git(repo, "remote", "set-url", "origin", str(tmp_path / "unreachable.git"))
    ref = pin(repo, "stale", tip)

    created, error = reaper_lifecycle.create_recovery_ref(repo, branch="old", head=tip)
    assert error is None and created is not None
    found = next(row for row in rescue_refs.classify_rescue_refs(repo) if row.ref == ref)
    assert found.classification == "UNIQUE"
    assert "fetch" in found.proof
    summary = rescue_refs.run(repo, apply=True, limit=5, listing=tmp_path / "stale.json")
    assert summary.deleted == 0
    assert _alive(repo, ref)


def test_removing_the_preserving_ref_skips_deletion(repo: Path) -> None:
    """The origin ref that proved containment is checked again under the lock."""
    git(repo, "checkout", "-b", "side")
    (repo / "side.txt").write_text("side\n", encoding="utf-8")
    git(repo, "add", "side.txt")
    git(repo, "commit", "-m", "side", when="2026-10-13T00:00:00Z")
    tip = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "-u", "origin", "side")
    git(repo, "checkout", "main")
    ref = pin(repo, "side-tip", tip)
    rows = rescue_refs.classify_rescue_refs(repo)
    row = next(item for item in rows if item.ref == ref)
    assert row.classification == "CONTAINED"
    assert row.preserving_ref == "refs/remotes/origin/side"
    assert row.preserving_sha
    git(repo, "update-ref", "-d", "refs/remotes/origin/side", tip)
    git(repo.parent / "origin.git", "update-ref", "-d", "refs/heads/side", tip)
    git(repo, "branch", "-D", "side")

    deleted, skipped = rescue_refs._apply(repo, rows, limit=1, lock_timeout_s=5, deleter=rescue_refs.delete_ref)

    assert (deleted, skipped) == (0, 1)
    assert git(repo, "rev-parse", ref) == tip
    reason = str(journal_events(repo)[-1]["reason"])
    assert "preserving ref" in reason


def test_shallow_clone_does_not_delete_a_hidden_parent(repo: Path, tmp_path: Path) -> None:
    """A depth-1 clone must not treat a hidden parent as patch-equivalent to an orphan main."""
    git(repo, "checkout", "-b", "feature")
    (repo / "hidden.txt").write_text("unique parent\n", encoding="utf-8")
    git(repo, "add", "hidden.txt")
    git(repo, "commit", "-m", "hidden", when="2026-10-14T00:00:00Z")
    hidden = git(repo, "rev-parse", "HEAD")
    (repo / "matched.txt").write_text("matched tip\n", encoding="utf-8")
    git(repo, "add", "matched.txt")
    git(repo, "commit", "-m", "tip", when="2026-10-14T01:00:00Z")
    tip = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "feature")
    git(repo, "checkout", "--orphan", "adopted")
    _clear_tree(repo)
    git(repo, "read-tree", f"{tip}^{{tree}}")
    git(repo, "checkout-index", "-a", "-f")
    git(repo, "commit", "-m", "independent root", when="2026-10-14T02:00:00Z")
    git(repo, "branch", "-M", "main")
    git(repo, "push", "--force", "origin", "main")

    shallow = tmp_path / "shallow"
    remote = tmp_path / "origin.git"
    git(tmp_path, "clone", "--depth", "1", "--branch", "feature", f"file://{remote}", str(shallow))
    git(shallow, "config", "user.name", "Test")
    git(shallow, "config", "user.email", "test@example.invalid")
    git(shallow, "config", "core.hooksPath", "/dev/null")
    git(shallow, "config", "commit.gpgsign", "false")
    git(shallow, "fetch", "--depth=1", "origin", "main:refs/remotes/origin/main")
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"
    visible = set(git(shallow, "rev-list", "HEAD", "--not", "refs/remotes/origin/main").splitlines())
    assert hidden not in visible
    ref = pin(shallow, "target", tip)

    found = next(row for row in rescue_refs.classify_rescue_refs(shallow) if row.ref == ref)
    assert found.classification == "UNIQUE"
    assert "shallow" in found.proof
    summary = rescue_refs.run(shallow, apply=True, limit=5, listing=tmp_path / "shallow.json")
    assert summary.deleted == 0
    assert git(shallow, "rev-parse", ref) == tip


def test_partial_clone_missing_blob_is_not_patch_equivalent(repo: Path, tmp_path: Path) -> None:
    """A blob the partial clone never transferred cannot prove patch equivalence."""
    git(repo, "checkout", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "add", "feature.txt")
    git(repo, "commit", "-m", "feature", when="2026-10-15T00:00:00Z")
    feature = git(repo, "rev-parse", "HEAD")
    blob = git(repo, "rev-parse", f"{feature}:feature.txt")
    git(repo, "checkout", "main")
    git(repo, "merge", "--squash", "feature")
    git(repo, "commit", "-m", "squash feature", when="2026-10-15T01:00:00Z")
    git(repo, "push", "origin", "main")
    git(repo, "push", "origin", "feature")
    remote = tmp_path / "origin.git"
    git(remote, "config", "uploadpack.allowFilter", "true")
    git(remote, "config", "uploadpack.allowReachableSHA1InWant", "true")
    partial = tmp_path / "partial"
    git(
        tmp_path,
        "clone",
        "--filter=blob:none",
        "--no-checkout",
        "--single-branch",
        "--branch",
        "main",
        f"file://{remote}",
        str(partial),
    )
    git(partial, "config", "user.name", "Test")
    git(partial, "config", "user.email", "test@example.invalid")
    git(partial, "config", "core.hooksPath", "/dev/null")
    git(partial, "config", "commit.gpgsign", "false")
    git(partial, "fetch", "--filter=blob:none", "origin", feature)
    missing = git(partial, "rev-list", "--objects", "--missing=print", "--max-count=1", feature)
    assert f"?{blob}" in missing.splitlines()
    ref = pin(partial, "feature", feature)

    found = next(row for row in rescue_refs.classify_rescue_refs(partial) if row.ref == ref)
    assert found.classification == "UNIQUE"
    assert "missing" in found.proof
    still = git(partial, "rev-list", "--objects", "--missing=print", "--max-count=1", feature)
    assert f"?{blob}" in still.splitlines()
    summary = rescue_refs.run(partial, apply=True, limit=5, listing=tmp_path / "partial-patch.json")
    assert summary.deleted == 0
    assert git(partial, "rev-parse", ref) == feature


def test_partial_clone_complete_ancestry_stays_contained(repo: Path, tmp_path: Path) -> None:
    """Containment follows the commit walk. A missing blob on a partial clone does not void it.

    Parent links are stored on the commit objects. ``blob:none`` omits blobs and
    keeps those commits, so a tip that is an ancestor of a fresh ``origin/main``
    is CONTAINED. A shallow boundary or a graft is not this case.
    """
    (repo / "recent.txt").write_text("available\n", encoding="utf-8")
    git(repo, "add", "recent.txt")
    git(repo, "commit", "-m", "recent", when="2026-10-15T02:00:00Z")
    git(repo, "push", "origin", "main")
    root = git(repo, "rev-parse", "HEAD~1")
    blob = git(repo, "rev-parse", f"{root}:readme")
    remote = tmp_path / "origin.git"
    git(remote, "config", "uploadpack.allowFilter", "true")
    partial = tmp_path / "partial-contained"
    git(
        tmp_path,
        "clone",
        "--filter=blob:none",
        "--no-checkout",
        "--branch",
        "main",
        f"file://{remote}",
        str(partial),
    )
    git(partial, "config", "user.name", "Test")
    git(partial, "config", "user.email", "test@example.invalid")
    git(partial, "config", "core.hooksPath", "/dev/null")
    git(partial, "config", "commit.gpgsign", "false")
    missing = git(partial, "rev-list", "--objects", "--missing=print", "origin/main")
    assert f"?{blob}" in missing.splitlines()
    ref = pin(partial, "old-main", root)

    found = next(row for row in rescue_refs.classify_rescue_refs(partial) if row.ref == ref)
    assert found.classification == "CONTAINED"
    assert found.preserving_ref == "refs/remotes/origin/main"
    assert found.preserving_sha
    still = git(partial, "rev-list", "--objects", "--missing=print", "origin/main")
    assert f"?{blob}" in still.splitlines()
    rescue_refs.run(partial, apply=True, limit=5, listing=tmp_path / "partial-contained.json")
    assert not _alive(partial, ref)
