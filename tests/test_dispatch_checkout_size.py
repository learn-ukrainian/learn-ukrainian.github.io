"""Default dispatch checkout size budget (#10777).

The size test reads tracked blob sizes at ``HEAD`` (``git ls-tree -r -l``),
never a live host path, so it measures the profile and not local caches.
"""

from __future__ import annotations

import subprocess
import sys
from functools import cache
from pathlib import Path

import pytest

from scripts import delegate

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.repo_wide

MIB = 1024 * 1024
# Measured 2026-10-16 on main c0f3aaf4639 (tracked bytes, git ls-tree):
# the previous default profile kept 408.9 MiB; this profile keeps 195.8 MiB.
# The ceiling sits 45% below that baseline and leaves room for ordinary
# growth of scripts/, tests/ and docs/.
DEFAULT_PROFILE_CEILING_BYTES = 225 * MIB

# Files inside excluded trees that ``pytest -m repo_wide`` reads in a default
# dispatch checkout: (path, reader, text in the reader that names it). A
# module that reads at import aborts collection of the whole run when the
# file is missing.
ANCHORED_READS = (
    ("curriculum/l2-uk-en/curriculum.yaml", "tests/test_landings_use_levellanding.py", "curriculum.yaml"),
    ("curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml", "scripts/curriculum/arc/loader.py", "_arc.yaml"),
    ("curriculum/l2-uk-en/plans/a1/a1-finale.yaml", "tests/audit/test_track_deterministic_audit.py", '"plans" / "a1"'),
    (
        "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml",
        "scripts/curriculum/validate/a1_reference.py",
        "ohoiko-oho-a1-reference.yaml",
    ),
    (
        "registry/projects/open_model_data/instruction_catalog.yaml",
        "tests/projects/open_model_data/test_instruction_catalog.py",
        "instruction_catalog.yaml",
    ),
    (
        "registry/projects/open_model_data/instruction_catalog.schema.json",
        "tests/projects/open_model_data/test_instruction_catalog.py",
        "instruction_catalog.schema.json",
    ),
)


@cache
def _tracked_tree() -> tuple[dict[str, int], dict[str, tuple[str, ...]]]:
    """Return tracked blob sizes and child directories at HEAD."""
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-l", "-z", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        timeout=60,
    ).stdout
    sizes: dict[str, int] = {}
    children: dict[str, set[str]] = {}
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        _mode, kind, _sha, size = meta.split()
        if kind != b"blob":
            continue
        path = raw_path.decode("utf-8", "surrogateescape")
        sizes[path] = int(size)
        parts = path.split("/")
        for depth in range(len(parts) - 1):
            children.setdefault("/".join(parts[:depth]), set()).add("/".join(parts[: depth + 1]))
    return sizes, {parent: tuple(sorted(names)) for parent, names in children.items()}


def _list_dirs(parent: str) -> tuple[str, ...]:
    return _tracked_tree()[1].get(parent, ())


def _in_cone(path: str, cone_dirs: list[str]) -> bool:
    """Cone mode: root files, everything under a cone dir, files beside its ancestors."""
    parent = path.rpartition("/")[0]
    if not parent:
        return True
    return any(path.startswith(cone + "/") or cone.startswith(parent + "/") for cone in cone_dirs)


def _profile_bytes(sparse_include: tuple[str, ...] = ()) -> int:
    cone_dirs, _excluded = delegate._dispatch_sparse_profile(_list_dirs, sparse_include)
    return sum(size for path, size in _tracked_tree()[0].items() if _in_cone(path, cone_dirs))


def test_default_profile_tracked_size_stays_under_ceiling() -> None:
    size = _profile_bytes()

    assert size <= DEFAULT_PROFILE_CEILING_BYTES, (
        f"default dispatch checkout holds {size / MIB:.1f} MiB of tracked files, over the "
        f"{DEFAULT_PROFILE_CEILING_BYTES / MIB:.0f} MiB ceiling (#10777). Exclude the tree that grew in "
        "scripts/delegate.py _DISPATCH_SPARSE_EXCLUDE_DEFAULT, or raise the ceiling with a new measurement."
    )


def test_ceiling_fails_when_an_excluded_tree_returns() -> None:
    """The ceiling is tight enough to catch a large tree coming back."""
    assert _profile_bytes(("site/src/data", "registry/lexicon/source-inventory")) > DEFAULT_PROFILE_CEILING_BYTES


@pytest.mark.parametrize(("path", "reader", "marker"), ANCHORED_READS)
def test_default_profile_keeps_files_repo_wide_reads(path: str, reader: str, marker: str) -> None:
    sizes, _ = _tracked_tree()
    assert path in sizes, f"{path} is no longer tracked; update ANCHORED_READS and _DISPATCH_SPARSE_ANCHORS"
    assert marker in (REPO_ROOT / reader).read_text(encoding="utf-8"), f"{reader} no longer reads {path}"
    cone_dirs, excluded = delegate._dispatch_sparse_profile(_list_dirs)
    assert any(path.startswith(tree + "/") for tree in excluded), f"{path} is no longer excluded; drop its anchor"

    assert _in_cone(path, cone_dirs), (
        f"{path} (read by {reader}) is missing from the default dispatch checkout; "
        "add an anchor in scripts/delegate.py _DISPATCH_SPARSE_ANCHORS"
    )


def test_every_anchor_lies_inside_its_excluded_tree_and_exists() -> None:
    _cone_dirs, excluded = delegate._dispatch_sparse_profile(_list_dirs)
    for tree, anchors in delegate._DISPATCH_SPARSE_ANCHORS.items():
        assert tree in delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT, tree
        assert tree in excluded, f"{tree} is not tracked at HEAD; drop its anchors"
        for anchor in anchors:
            assert anchor.startswith(tree + "/"), anchor
            assert anchor in _list_dirs(anchor.rpartition("/")[0]), f"anchor {anchor} is not a directory at HEAD"


def test_conftest_skips_tests_for_every_unanchored_exclusion() -> None:
    """A test reading an excluded tree skips with its --sparse-include, not a bare FileNotFoundError.

    Anchored trees keep their directory, so the conftest cannot see them as
    absent; wiki has no test readers.
    """
    conftest = next(
        module
        for module in list(sys.modules.values())
        if str(getattr(module, "__file__", "") or "").endswith("tests/conftest.py")
    )
    expected = set(delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(delegate._DISPATCH_SPARSE_ANCHORS) - {"wiki"}

    assert set(conftest._SPARSE_TREE_DIRS) == expected


def test_every_exclusion_is_reincludable() -> None:
    names = sorted(delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT)

    assert delegate._normalize_sparse_include(names) == tuple(names)
    cone_dirs, excluded = delegate._dispatch_sparse_profile(_list_dirs, names)
    assert excluded == []
    assert _profile_bytes(tuple(names)) == sum(_tracked_tree()[0].values())
    assert cone_dirs


@pytest.mark.parametrize(
    ("owned", "expected"),
    [
        ("site/src/data/curriculum-stats.json", ("site/src/data",)),
        ("site/src/pages/index.astro", ("site/src/content", "site/src/data")),
        ("site", ("site/src/content", "site/src/data")),
        (
            "registry/lexicon",
            ("registry/lexicon/source-inventory", "registry/lexicon/source-inventory-review-decisions"),
        ),
        ("data", ("data/datasets", "data/lexicon", "data/processed", "data/projects")),
        ("scripts/delegate.py", ()),
        (".", ()),
    ],
)
def test_owned_path_includes_the_trees_it_needs(owned: str, expected: tuple[str, ...]) -> None:
    assert delegate._infer_sparse_include(None, owned_paths=[owned]) == expected


def test_worker_env_points_tool_caches_at_the_scratch_lease(tmp_path: Path) -> None:
    lease = tmp_path / "lease"

    env = delegate._build_worker_env(
        task_id="infra-10777-size",
        dispatch_agent="claude",
        runtime_tmp_root=lease,
        base_env={"PATH": "/usr/bin", "HOME": str(tmp_path)},
    )

    assert env["MYPY_CACHE_DIR"] == str(lease / "tool-cache" / "mypy")
    assert env["PYTHONPYCACHEPREFIX"] == str(lease / "tool-cache" / "pycache")
    assert env["RUFF_CACHE_DIR"] == str(lease / "tool-cache" / "ruff")


def test_worker_env_without_a_lease_leaves_tool_caches_alone(tmp_path: Path) -> None:
    env = delegate._build_worker_env(
        task_id="infra-10777-size",
        dispatch_agent="claude",
        base_env={"PATH": "/usr/bin", "HOME": str(tmp_path)},
    )

    assert not {"MYPY_CACHE_DIR", "PYTHONPYCACHEPREFIX", "RUFF_CACHE_DIR"} & env.keys()


def test_cone_dirs_drop_nested_trees_and_keep_their_siblings() -> None:
    tree = {
        "": ("data", "docs", "site"),
        "data": ("data/datasets", "data/raw"),
        "site": ("site/src", "site/tests"),
        "site/src": ("site/src/content", "site/src/data", "site/src/lib"),
    }

    cone, excluded = delegate._dispatch_sparse_cone_dirs(
        lambda parent: tree.get(parent, ()),
        {"data/datasets", "site/src/data", "site/src/content", "registry/projects", "docs/missing/deep"},
    )

    assert excluded == ["data/datasets", "site/src/content", "site/src/data"]
    # docs/ has no excluded tree at this ref, so it stays whole.
    assert sorted(cone) == ["data/raw", "docs", "site/src/lib", "site/tests"]


def test_apply_sparse_checkout_drops_nested_trees_real_git(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    files = {
        "README.md": "root\n",
        "site/package.json": "{}\n",
        "site/src/content.config.ts": "export {}\n",
        "site/src/data/stats.json": "{}\n",
        "site/src/content/docs/a1/index.mdx": "x\n",
        "site/src/lib/a.ts": "x\n",
        "registry/lexicon/f.txt": "x\n",
        "registry/lexicon/source-inventory/big.yaml": "x\n",
        "registry/lexicon/source-inventory/grade-01/g.yaml": "x\n",
        "registry/lexicon/source-inventory/oneshot/o.yaml": "x\n",
        "scripts/s.py": "x\n",
    }
    for relative, text in files.items():
        path = primary / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    env = {"GIT_CEILING_DIRECTORIES": str(tmp_path), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=primary, check=True, capture_output=True, env=env, timeout=30)

    git("init", "-q", "-b", "main")
    git("add", ".")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    worktree = tmp_path / "wt"
    git("worktree", "add", "-q", str(worktree), "HEAD")

    meta = delegate._apply_dispatch_sparse_checkout(worktree)

    assert meta["excluded"] == ["registry/lexicon/source-inventory", "site/src/content", "site/src/data"]
    present = {relative for relative in files if (worktree / relative).is_file()}
    assert present == {
        "README.md",
        "site/package.json",
        "site/src/content.config.ts",
        "site/src/lib/a.ts",
        "registry/lexicon/f.txt",
        # The grade-01 anchor brings the inventories beside it, not oneshot/.
        "registry/lexicon/source-inventory/big.yaml",
        "registry/lexicon/source-inventory/grade-01/g.yaml",
        "scripts/s.py",
    }
