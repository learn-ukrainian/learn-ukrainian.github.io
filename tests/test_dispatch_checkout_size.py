"""Default dispatch checkout size budget (#10777).

The size test reads tracked blob sizes at ``HEAD`` (``git ls-tree -r -l``),
never a live host path, so it measures the profile and not local caches.
"""

from __future__ import annotations

import ast
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
# the previous default profile kept 408.9 MiB; this profile keeps 196.3 MiB.
# The ceiling sits 45% below that baseline and leaves room for ordinary
# growth of scripts/, tests/ and docs/.
DEFAULT_PROFILE_CEILING_BYTES = 225 * MIB

# Files inside excluded trees that ``pytest -m repo_wide`` reads in a default
# dispatch checkout: (path, reader, text in the reader that names it). A
# module that reads at import aborts collection of the whole run when the
# file is missing.
ANCHORED_READS = (
    ("curriculum/l2-uk-direct/a1/abetka-1.yaml", "tests/test_ohoiko_source_inventory_scope.py", "abetka-*.yaml"),
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


def _conftest():
    return next(
        module
        for module in list(sys.modules.values())
        if str(getattr(module, "__file__", "") or "").endswith("tests/conftest.py")
    )


def test_conftest_skips_tests_for_every_unanchored_exclusion() -> None:
    """A test reading an excluded tree skips with its --sparse-include, not a bare FileNotFoundError.

    Anchored trees keep their directory; the conftest sees one absent through
    the sparse cone only when it is listed in _SPARSE_ANCHORED_TREES. wiki has
    no test readers.
    """
    conftest = _conftest()
    expected = set(delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(delegate._DISPATCH_SPARSE_ANCHORS) - {"wiki"}

    assert set(delegate._DISPATCH_SPARSE_ANCHORS) >= conftest._SPARSE_ANCHORED_TREES
    assert set(conftest._SPARSE_TREES) == expected | conftest._SPARSE_ANCHORED_TREES


_DECISIONS = "registry/lexicon/source-inventory-review-decisions"
# Tests that read a tree the default profile dropped in #10777 and passed in
# a full checkout but failed in a default one: (test file, test item, tree).
# A parametrized test whose cases come from the absent tree collects one
# empty-parameter item, ``[ledger_path0]``; it must skip naming the include
# too, not as ``got empty parameter set``.
EXCLUDED_TREE_READERS = (
    (
        "tests/test_source_inventory_review_decisions.py",
        "test_committed_first_source_inventory_review_batch_validates",
        _DECISIONS,
    ),
    (
        "tests/test_source_inventory_review_decisions.py",
        "test_default_committed_decision_file_parametrization_is_complete",
        _DECISIONS,
    ),
    (
        "tests/test_source_inventory_review_decisions.py",
        "test_default_committed_decision_files_keep_aggregate_floors",
        _DECISIONS,
    ),
    (
        "tests/test_source_inventory_review_decisions.py",
        "test_default_committed_decision_files_validate[ledger_path0]",
        _DECISIONS,
    ),
    ("tests/test_source_inventory_review_decisions.py", "test_committed_ohoiko_batch_ledgers_validate", _DECISIONS),
    (
        "tests/test_source_inventory_promotion_plan.py",
        "test_plan_maps_approved_decision_to_manifest_addition",
        _DECISIONS,
    ),
    ("tests/test_scrub_decision_ledger_keys.py", "test_shards_independently_pass_validation", _DECISIONS),
    (
        "tests/test_ohoiko_source_inventory_scope.py",
        "test_ohoiko_abetka_inventory_has_review_decisions_for_all_rows",
        _DECISIONS,
    ),
    (
        "tests/test_promote_teacher_lesson_intake.py",
        "test_private_teacher_lesson_delta_inventory_is_privacy_safe",
        "registry/lexicon/source-inventory",
    ),
    (
        "tests/test_generate_search_index.py",
        "test_committed_usage_sources_are_bound_to_their_passages",
        "site/src/data",
    ),
    ("tests/audit/test_check_mdx_source_parity.py", "test_real_generated_a1_pages_pass_parity", "site/src/content"),
)


@pytest.mark.parametrize(("test_file", "item_name", "tree"), EXCLUDED_TREE_READERS)
def test_excluded_tree_readers_skip_naming_their_include(test_file: str, item_name: str, tree: str) -> None:
    reason = _conftest().sparse_missing_tree_skip_reason(
        test_file, sparse_enabled=True, missing_trees={tree}, item_name=item_name
    )

    assert reason == f"{tree} is absent from this sparse worktree; re-include it with --sparse-include {tree}"


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


def test_every_exclusion_is_reincludable() -> None:
    names = sorted(delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT)

    assert delegate._normalize_sparse_include(names) == tuple(names)
    cone_dirs, excluded = delegate._dispatch_sparse_profile(_list_dirs, names)
    assert excluded == []
    assert _profile_bytes(tuple(names)) == sum(_tracked_tree()[0].values())
    assert cone_dirs


_SOURCE_INVENTORY = ("registry/lexicon/source-inventory", "registry/lexicon/source-inventory-review-decisions")


@pytest.fixture
def owned_files_here(monkeypatch: pytest.MonkeyPatch) -> None:
    """Read owned files from this checkout; delegate's root is the primary checkout, which may be behind it."""
    monkeypatch.setattr(delegate, "_REPO_ROOT", REPO_ROOT)


@pytest.mark.usefixtures("owned_files_here")
@pytest.mark.parametrize(
    ("owned", "expected"),
    [
        ("site/src/data/curriculum-stats.json", ("site/src/data",)),
        ("site/src/pages/index.astro", ("site/src/content", "site/src/data")),
        ("site", ("site/src/content", "site/src/data")),
        ("registry/lexicon", _SOURCE_INVENTORY),
        ("data", ("data/datasets", "data/lexicon", "data/processed", "data/projects")),
        ("scripts/delegate.py", ()),
        ("tests/test_preparation_api.py", ("site/src/content",)),
        ("tests/test_landings_use_levellanding.py", ("curriculum", "site/src/content", "site/src/data")),
        ("tests/test_env_sanitize.py", ()),
        ("scripts/generate_landing_pages.py", ("curriculum", "site/src/content")),
        ("scripts/audit/check_static_practice_assets.py", ("site/src/data",)),
        ("scripts/lexicon/lesson_atlas_link_census.py", (*_SOURCE_INVENTORY, "site/src/content", "site/src/data")),
        (".", ()),
    ],
)
def test_owned_path_includes_the_trees_it_needs(owned: str, expected: tuple[str, ...]) -> None:
    assert delegate._infer_sparse_include(None, owned_paths=[owned]) == expected


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("./site/src/data/curriculum-stats.json", "site/src/data/curriculum-stats.json"),
        ("registry/./projects/open_model_data/x.json", "registry/projects/open_model_data/x.json"),
        ("site//src//data/curriculum-stats.json", "site/src/data/curriculum-stats.json"),
        ("site/src/data/", "site/src/data"),
        ("site/src/data/**", "site/src/data"),
        ("./registry/lexicon/", "registry/lexicon"),
        (".\\site\\src\\data\\curriculum-stats.json", "site/src/data/curriculum-stats.json"),
    ],
)
def test_owned_path_aliases_include_what_their_canonical_spelling_includes(alias: str, canonical: str) -> None:
    """Every spelling ownership admission accepts names the same trees (#10777)."""
    from scripts.guardrails.delegate_ownership import owned_path_matcher

    assert owned_path_matcher(alias) is not None
    expected = delegate._infer_sparse_include(None, owned_paths=[canonical])

    assert expected
    assert delegate._infer_sparse_include(None, owned_paths=[alias]) == expected


@pytest.mark.parametrize(
    ("glob", "expected"),
    [
        ("curriculum/l2-uk-en/evidence/a1/**/lessons.lock.yaml", ("curriculum",)),
        ("site/src/data/lexicon-*.json", ("site/src/data",)),
        # fnmatch's ``*`` crosses ``/``: this glob can own files in both site trees.
        ("site/*.json", ("site/src/content", "site/src/data")),
        ("./registry/projects/*/x.json", ("registry/projects",)),
        ("scripts/*.py", ()),
    ],
)
def test_owned_glob_includes_the_trees_its_literal_directories_reach(glob: str, expected: tuple[str, ...]) -> None:
    assert delegate._infer_sparse_include(None, owned_paths=[glob]) == expected


@pytest.mark.parametrize(
    "owned",
    [
        "site-extra/src/data/x.json",
        "site-extra",
        "registry/projects2/x.json",
        "registry/projects2",
        "data/projects-old/x",
        "curriculum2/a1.yaml",
        "registry/lexicon/source-inventory-old/x.yaml",
    ],
)
def test_owned_path_prefix_confusion_includes_nothing(owned: str) -> None:
    assert delegate._infer_sparse_include(None, owned_paths=[owned]) == ()


@pytest.mark.parametrize("owned", ["", ".", "./", "/site/src/data", "site/../site/src/data", "**", "./**", "*/x"])
def test_an_owned_path_that_owns_nothing_includes_nothing(owned: str) -> None:
    """Admission refuses these claims; inference reads them the same way."""
    from scripts.guardrails.delegate_ownership import owned_path_matcher

    assert owned_path_matcher(owned) is None
    assert delegate._infer_sparse_include(None, owned_paths=[owned]) == ()


def _site_tree_markers() -> set[tuple[str, str]]:
    """``(test file, tree)`` for every needs_sparse_tree marker naming a site tree."""
    found: set[tuple[str, str]] = set()
    for path in sorted((REPO_ROOT / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "needs_sparse_tree"
            ):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and str(arg.value).startswith("site/"):
                        found.add((path.relative_to(REPO_ROOT).as_posix(), str(arg.value)))
    return found


def test_an_owned_test_gets_the_excluded_trees_its_marks_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test_file = tmp_path / "tests" / "test_reader.py"
    test_file.parent.mkdir()
    test_file.write_text(
        "import pytest\n"
        'needs_data = pytest.mark.needs_sparse_tree("site/src/data")\n'
        '@pytest.mark.needs_sparse_tree("data/projects", "not/excluded")\n'
        "def test_x(): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_broken.py").write_text("def (\n", encoding="utf-8")
    monkeypatch.setattr(delegate, "_REPO_ROOT", tmp_path)

    assert delegate._owned_test_marked_trees("tests/test_reader.py") == ("data/projects", "site/src/data")
    assert delegate._owned_test_marked_trees("tests/test_broken.py") == ()
    assert delegate._owned_test_marked_trees("tests/test_missing.py") == ()
    # Only test files are read for marks.
    assert delegate._owned_test_marked_trees("scripts/test_reader.py") == ()


def test_delegate_names_no_test_file() -> None:
    """A test file name in scripts/delegate.py makes every test a repo_wide candidate (#10777).

    The prefilter in tests/test_repo_wide_marker_invariant.py reads it as a
    load of that test, and tests/conftest.py imports delegate.py.
    """
    tree = ast.parse((REPO_ROOT / "scripts" / "delegate.py").read_text(encoding="utf-8"))
    named = sorted(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.rpartition("/")[2].startswith("test_")
        and node.value.endswith(".py")
    )

    assert not named, f"read owned test readers from their needs_sparse_tree marks instead: {named}"


@pytest.mark.usefixtures("owned_files_here")
def test_owning_a_marked_site_reader_includes_its_tree() -> None:
    """A worker that owns a test marked for a site tree gets that tree, so the test runs instead of skipping."""
    markers = _site_tree_markers()
    assert ("tests/test_lesson_atlas_link_census.py", "site/src/data") in markers
    missing = sorted(
        (test_file, tree)
        for test_file, tree in markers
        if tree not in delegate._infer_sparse_include(None, owned_paths=[test_file])
    )

    assert not missing, f"add these readers to scripts/delegate.py _SPARSE_OWNED_PATH_REINCLUDE: {missing}"


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
