"""Default dispatch checkout size budget (#10777).

The size test reads tracked blob sizes at ``HEAD`` (``git ls-tree -r -l``),
never a live host path, so it measures the profile and not local caches.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.repo_wide

# Measured 2026-10-16 on main c0f3aaf4639 (tracked bytes, git ls-tree):
# the previous default profile kept 408.9 MiB; this profile keeps 196.3 MiB.
# The ceiling sits 45% below that baseline and leaves room for ordinary
# growth of scripts/, tests/ and docs/.

# Files inside excluded trees that ``pytest -m repo_wide`` reads in a default
# dispatch checkout: (path, reader, text in the reader that names it). A
# module that reads at import aborts collection of the whole run when the
# file is missing.


def _conftest():
    return next(
        module
        for module in list(sys.modules.values())
        if str(getattr(module, "__file__", "") or "").endswith("tests/conftest.py")
    )
def test_ledger_tests_that_build_their_own_ledgers_still_run_without_the_ledgers() -> None:
    """Marks stay on the readers: the tmp_path unit tests beside them keep their coverage."""
    reason = _conftest().sparse_missing_tree_skip_reason(
        "tests/test_source_inventory_review_decisions.py",
        sparse_enabled=True,
        missing_trees=set(_conftest()._SPARSE_TREES),
        item_name="test_decision_validator_rejects_bad_source_key",
    )

    assert reason is None


@pytest.fixture
def conftest_on_repo(monkeypatch: pytest.MonkeyPatch):
    """Point the conftest's sparse checks at another checkout; reset its caches on both sides."""
    conftest = _conftest()
    caches = (conftest._sparse_checkout_enabled, conftest._sparse_cone_dirs)

    def use(root: Path):
        monkeypatch.setattr(conftest, "_REPO_ROOT", root)
        for lru in caches:
            lru.cache_clear()
        return conftest

    monkeypatch.delenv("SPARSE_TEST_FORCE_MISSING_TREES", raising=False)
    yield use
    for lru in caches:
        lru.cache_clear()


def test_conftest_sees_an_anchored_tree_absent_through_the_sparse_cone(tmp_path: Path, conftest_on_repo) -> None:
    repo = tmp_path / "repo"
    inventory = "registry/lexicon/source-inventory"
    for relative in (f"{inventory}/loose.yaml", f"{inventory}/grade-01/g.yaml", f"{inventory}/oneshot/o.yaml"):
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text("x\n", encoding="utf-8")
    env = {"GIT_CEILING_DIRECTORIES": str(tmp_path), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env, timeout=30)

    git("init", "-q", "-b", "main")
    git("add", ".")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    git("sparse-checkout", "set", "--cone", f"{inventory}/grade-01")

    conftest = conftest_on_repo(repo)
    # The anchor keeps the directory, so only the cone shows the tree is absent.
    assert (repo / inventory).is_dir()
    assert not (repo / inventory / "oneshot").exists()
    assert inventory in conftest._sparse_missing_trees()

    git("sparse-checkout", "add", inventory)
    conftest = conftest_on_repo(repo)
    assert inventory not in conftest._sparse_missing_trees()

    # A checkout that is not in cone mode reads as holding the tree, so the test runs.
    git("sparse-checkout", "set", "--no-cone", "/registry/lexicon/source-inventory/grade-01/")
    conftest = conftest_on_repo(repo)
    assert inventory not in conftest._sparse_missing_trees()
