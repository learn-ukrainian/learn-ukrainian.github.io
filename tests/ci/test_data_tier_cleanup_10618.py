"""The nightly data-tier runner removes its own throwaway checkout (#10618).

The nightly leaves ignored byproducts (``data/atlas.db*``, ``.pytest_cache``)
in ``.worktrees/data-tier/run-<hex>``. They carry no task attribution, so the
general preservation gate refused every removal. Only a tree that proves it is
the runner's own disposable checkout may skip that gate; everything else keeps
the existing refusal.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import data_tier
from scripts.orchestration import worktree_claims

REFUSAL = "missing canonical task attribution"
RUN = "run-" + "a" * 32


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


@pytest.fixture
def primary(tmp_path: Path) -> Path:
    root = tmp_path / "primary"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tier@example.invalid")
    _git(root, "config", "user.name", "Tier Test")
    (root / ".gitignore").write_text(".worktrees/\nbatch_state/\ndata/atlas.db*\n.pytest_cache/\n", encoding="utf-8")
    (root / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", ".gitignore", "tracked.txt")
    _git(root, "commit", "-m", "base")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def _checkout(primary: Path, path: Path | None = None) -> Path:
    path = path or primary / ".worktrees" / "data-tier" / RUN
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(primary, "worktree", "add", "--detach", str(path), "origin/main")
    return path


def _byproducts(checkout: Path) -> None:
    (checkout / "data").mkdir(exist_ok=True)
    (checkout / "data" / "atlas.db").write_bytes(b"atlas")
    (checkout / "data" / "atlas.db-wal").write_bytes(b"wal")
    (checkout / ".pytest_cache").mkdir(exist_ok=True)
    (checkout / ".pytest_cache" / "README.md").write_text("cache\n", encoding="utf-8")
    assert _git(checkout, "status", "--porcelain") == ""


def _registered(primary: Path, checkout: Path) -> bool:
    return str(checkout) in _git(primary, "worktree", "list", "--porcelain")


def test_data_tier_checkout_with_ignored_byproducts_is_removed(primary: Path) -> None:
    checkout = _checkout(primary)
    _byproducts(checkout)

    data_tier.remove_test_worktree(primary, checkout)

    assert not checkout.exists()
    assert not _registered(primary, checkout)
    assert not (primary / "batch_state" / "preserved").exists()


def test_eligible_checkout_reports_removed_through_the_guard(primary: Path) -> None:
    checkout = _checkout(primary)
    _byproducts(checkout)

    removal = worktree_claims.remove_unclaimed_worktree(
        checkout,
        repo_root=primary,
        reason="data-tier checkout cleanup",
        owner_task_id=None,
        force=True,
        data_tier_run=True,
    )

    assert removal.action == "removed"
    assert not checkout.exists()


def test_the_flag_is_required_for_the_exemption(primary: Path) -> None:
    checkout = _checkout(primary)
    _byproducts(checkout)

    removal = worktree_claims.remove_unclaimed_worktree(
        checkout, repo_root=primary, reason="plain cleanup", owner_task_id=None, force=True
    )

    assert removal.action == "skipped"
    assert REFUSAL in removal.reason
    assert checkout.is_dir()


def _tracked_change(primary: Path) -> Path:
    checkout = _checkout(primary)
    _byproducts(checkout)
    (checkout / "tracked.txt").write_text("changed\n", encoding="utf-8")
    return checkout


def _off_main(primary: Path) -> Path:
    checkout = _checkout(primary)
    _byproducts(checkout)
    (checkout / "new.txt").write_text("work\n", encoding="utf-8")
    _git(checkout, "add", "new.txt")
    _git(checkout, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-m", "off main")
    return checkout


def _named(*parts: str):
    def build(primary: Path) -> Path:
        checkout = _checkout(primary, primary.joinpath(".worktrees", *parts))
        _byproducts(checkout)
        return checkout

    return build


def _symlinked(primary: Path) -> Path:
    real = _checkout(primary, primary / ".worktrees" / "elsewhere" / "real")
    _byproducts(real)
    link = primary / ".worktrees" / "data-tier" / ("run-" + "b" * 32)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(real, target_is_directory=True)
    return link


NEGATIVES = {
    "tracked-change": _tracked_change,
    "head-not-on-origin-main": _off_main,
    "uppercase-hex-name": _named("data-tier", "run-" + "A" * 32),
    "short-name": _named("data-tier", "run-" + "a" * 31),
    "dispatch-tree-with-run-name": _named("dispatch", "claude", "task", RUN),
    "dispatch-tree": _named("dispatch", "claude", "task"),
    "nested-under-data-tier": _named("data-tier", "sub", RUN),
    "symlinked-run-dir": _symlinked,
}


@pytest.mark.parametrize("case", sorted(NEGATIVES))
def test_ineligible_trees_are_still_refused(primary: Path, case: str) -> None:
    target = NEGATIVES[case](primary)
    resolved = target.resolve()

    with pytest.raises(data_tier.DataTierError, match=r"checkout cleanup (skipped|error)"):
        data_tier.remove_test_worktree(primary, target)

    assert target.exists()
    assert resolved.is_dir()
    assert _registered(primary, resolved)
    assert (
        worktree_claims.data_tier_checkout_refusal(
            target, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
        )
        is not None
    )


def test_non_ancestor_head_is_refused_by_the_ancestry_proof_not_attribution(primary: Path) -> None:
    checkout = _off_main(primary)
    # Clean tracked tree, so only the ancestry condition can refuse.
    refusal = worktree_claims.data_tier_checkout_refusal(
        checkout, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
    )
    assert refusal == "HEAD is not an ancestor of refs/remotes/origin/main"
    removal = worktree_claims.remove_unclaimed_worktree(
        checkout, repo_root=primary, reason="r", owner_task_id=None, force=True, data_tier_run=True
    )
    assert removal.action == "skipped"
    assert REFUSAL in removal.reason


def test_tracked_change_names_the_dirty_refusal(primary: Path) -> None:
    checkout = _tracked_change(primary)
    refusal = worktree_claims.data_tier_checkout_refusal(
        checkout, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
    )
    assert refusal == "tracked changes present"


def test_task_record_reference_withholds_the_exemption(primary: Path) -> None:
    checkout = _checkout(primary)
    _byproducts(checkout)
    tasks = primary / "batch_state" / "tasks"
    tasks.mkdir(parents=True)
    record = {"task_id": "referenced", "status": "done", "run_nonce": "n", "worktree_path": str(checkout)}
    (tasks / "referenced.json").write_text(json.dumps(record), encoding="utf-8")

    assert (
        worktree_claims.data_tier_checkout_refusal(checkout, repo_root=primary, tasks_dir=tasks)
        == "a task record references the tree"
    )


def test_eligibility_probe_never_raises_on_missing_path(primary: Path) -> None:
    refusal = worktree_claims.data_tier_checkout_refusal(
        primary / ".worktrees" / "data-tier" / RUN, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
    )
    assert refusal == "not a real directory"


def test_prune_stale_worktrees_uses_the_same_removal_path(primary: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stale = _checkout(primary)
    _byproducts(stale)
    os.utime(stale, (0, 0))
    recent = _checkout(primary, primary / ".worktrees" / "data-tier" / ("run-" + "c" * 32))
    _byproducts(recent)
    monkeypatch.setattr(data_tier, "command", lambda *args, **kwargs: SimpleNamespace(stdout=""))

    data_tier.prune_stale_worktrees(primary)

    assert not stale.exists()
    assert not _registered(primary, stale)
    assert recent.is_dir()


def _common_git_dir(primary: Path) -> Path:
    return Path(_git(primary, "rev-parse", "--path-format=absolute", "--git-common-dir"))


def _age_origin_main(primary: Path) -> None:
    """Backdate the remote-tracking ref so only a freshness check can refuse."""
    git_dir = _common_git_dir(primary)
    for relative in ("refs/remotes/origin/main", "logs/refs/remotes/origin/main"):
        path = git_dir / relative
        if path.is_file():
            os.utime(path, (0, 0))


@pytest.mark.parametrize("case", ["remote-present", "remote-absent", "stale-ref"])
def test_local_origin_main_branch_cannot_authorize_removal(primary: Path, case: str) -> None:
    """A branch named origin/main must not stand in for refs/remotes/origin/main (#10618).

    ``remote-present`` and ``remote-absent`` put the off-main commit on
    ``refs/heads/origin/main``. ``stale-ref`` leaves HEAD on main but backdates
    the remote-tracking ref. All three must keep the checkout.
    """
    if case == "stale-ref":
        checkout = _checkout(primary)
        _byproducts(checkout)
        _age_origin_main(primary)
    else:
        checkout = _off_main(primary)
        _git(primary, "update-ref", "refs/heads/origin/main", _git(checkout, "rev-parse", "HEAD"))
        if case == "remote-absent":
            _git(primary, "update-ref", "-d", "refs/remotes/origin/main")
    head = _git(checkout, "rev-parse", "HEAD")

    refusal = worktree_claims.data_tier_checkout_refusal(
        checkout, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
    )
    removal = worktree_claims.remove_unclaimed_worktree(
        checkout, repo_root=primary, reason="r", owner_task_id=None, force=True, data_tier_run=True
    )

    assert refusal
    assert "refs/remotes/origin/main" in refusal
    assert removal.action != "removed"
    assert checkout.is_dir()
    assert _git(checkout, "rev-parse", "HEAD") == head
    assert _registered(primary, checkout)


@pytest.mark.parametrize("mutation", ["tracked-edit", "unique-commit"])
def test_mutation_between_proof_and_removal_is_kept(
    primary: Path, mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change that lands after the first proof must not be deleted (#10618).

    ``tracked-edit`` lands inside the destructive git call, so only a non-force
    remove can keep it. ``unique-commit`` lands after the proof returns and
    moves ``refs/remotes/origin/main`` onto that commit, so a later ancestry
    check still passes and only a HEAD comparison can keep it.
    """
    checkout = _checkout(primary)
    _byproducts(checkout)
    head = _git(checkout, "rev-parse", "HEAD")
    injected = {"done": False}
    git_calls: list[list[str]] = []
    real_refusal = worktree_claims.data_tier_checkout_refusal
    real_git = worktree_claims.safe_git

    def refusal(worktree: Path, *, repo_root: Path, tasks_dir: Path, proved_head: list[str] | None = None):
        result = real_refusal(worktree, repo_root=repo_root, tasks_dir=tasks_dir, proved_head=proved_head)
        if result is None and mutation == "unique-commit" and not injected["done"]:
            injected["done"] = True
            (worktree / "unique.txt").write_text("unique\n", encoding="utf-8")
            _git(worktree, "add", "unique.txt")
            _git(worktree, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-m", "unique")
            _git(worktree, "update-ref", "refs/remotes/origin/main", "HEAD")
        return result

    def git(args: list[str], **kwargs: object):
        git_calls.append(list(args))
        if args[:2] == ["worktree", "remove"] and mutation == "tracked-edit" and not injected["done"]:
            injected["done"] = True
            (checkout / "tracked.txt").write_text("injected\n", encoding="utf-8")
        return real_git(args, **kwargs)

    monkeypatch.setattr(worktree_claims, "data_tier_checkout_refusal", refusal)
    monkeypatch.setattr(worktree_claims, "safe_git", git)

    removal = worktree_claims.remove_unclaimed_worktree(
        checkout, repo_root=primary, reason="r", owner_task_id=None, force=True, data_tier_run=True
    )

    assert removal.action != "removed"
    assert checkout.is_dir()
    assert _registered(primary, checkout)
    removes = [args for args in git_calls if args[:2] == ["worktree", "remove"]]
    if mutation == "tracked-edit":
        assert removes and all("--force" not in args for args in removes)
        assert (checkout / "tracked.txt").read_text(encoding="utf-8") == "injected\n"
        assert _git(checkout, "rev-parse", "HEAD") == head
    else:
        assert not removes
        assert _git(checkout, "log", "-1", "--format=%s") == "unique"
        assert _git(checkout, "rev-parse", "HEAD") != head


def test_origin_main_refresh_bound_covers_the_run_budget_only() -> None:
    """The freshness bound is one nightly run, not the 9-hour stale-checkout grace."""
    assert worktree_claims.DATA_TIER_ORIGIN_MAIN_MAX_AGE_S >= data_tier.RUN_BUDGET_SECONDS
    assert worktree_claims.DATA_TIER_ORIGIN_MAIN_MAX_AGE_S < 9 * 3600


def test_refresh_stamps_an_unchanged_origin_main(tmp_path: Path) -> None:
    """An unchanged fetch must still refresh the ref age eligibility measures."""
    remote = tmp_path / "remote"
    local = tmp_path / "local"
    remote.mkdir()
    local.mkdir()
    _git(remote, "init", "-b", "main")
    _git(remote, "config", "user.email", "t@example.invalid")
    _git(remote, "config", "user.name", "T")
    (remote / "f.txt").write_text("one\n", encoding="utf-8")
    _git(remote, "add", "f.txt")
    _git(remote, "commit", "-m", "one")
    _git(local, "init", "-b", "main")
    _git(local, "config", "user.email", "t@example.invalid")
    _git(local, "config", "user.name", "T")
    _git(local, "remote", "add", "origin", str(remote))
    data_tier.refresh_origin_main(local)
    ref = worktree_claims.DATA_TIER_ORIGIN_MAIN_REF
    loose = Path(_git(local, "rev-parse", "--path-format=absolute", "--git-path", ref))
    assert loose.is_file()
    os.utime(loose, (0, 0))
    log = Path(_git(local, "rev-parse", "--path-format=absolute", "--git-path", f"logs/{ref}"))
    if log.is_file():
        os.utime(log, (0, 0))
    before = _git(local, "rev-parse", ref)
    data_tier.refresh_origin_main(local)
    assert _git(local, "rev-parse", ref) == before
    assert loose.stat().st_mtime > 1_000_000_000


def test_unreadable_task_archive_is_not_eligible(primary: Path) -> None:
    """An unreadable archive directory must not look like an empty inventory (#10618)."""
    checkout = _checkout(primary)
    _byproducts(checkout)
    tasks = primary / "batch_state" / "tasks"
    archive = tasks / "archive"
    archive.mkdir(parents=True)
    (archive / "hidden.json").write_text(
        json.dumps({"task_id": "hidden", "status": "running", "worktree_path": str(checkout)}),
        encoding="utf-8",
    )
    os.chmod(archive, 0)
    try:
        refusal = worktree_claims.data_tier_checkout_refusal(checkout, repo_root=primary, tasks_dir=tasks)
        removal = worktree_claims.remove_unclaimed_worktree(
            checkout,
            repo_root=primary,
            reason="r",
            owner_task_id=None,
            force=True,
            data_tier_run=True,
            tasks_dir=tasks,
        )
        assert refusal
        assert "unreadable" in refusal
        assert removal.action != "removed"
        assert checkout.is_dir()
        assert _registered(primary, checkout)
    finally:
        os.chmod(archive, 0o700)
