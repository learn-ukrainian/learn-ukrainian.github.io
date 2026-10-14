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
        checkout, repo_root=primary, reason="data-tier checkout cleanup", owner_task_id=None, force=True,
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
        worktree_claims.data_tier_checkout_refusal(target, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks")
        is not None
    )


def test_non_ancestor_head_is_refused_by_the_ancestry_proof_not_attribution(primary: Path) -> None:
    checkout = _off_main(primary)
    # Clean tracked tree, so only the ancestry condition can refuse.
    refusal = worktree_claims.data_tier_checkout_refusal(
        checkout, repo_root=primary, tasks_dir=primary / "batch_state" / "tasks"
    )
    assert refusal == "HEAD is not an ancestor of origin/main"
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

    assert worktree_claims.data_tier_checkout_refusal(
        checkout, repo_root=primary, tasks_dir=tasks
    ) == "a task record references the tree"


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
