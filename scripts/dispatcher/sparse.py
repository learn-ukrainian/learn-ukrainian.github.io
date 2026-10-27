"""Legacy dispatch cone profile and include inference, without the legacy runner.

Ported mechanically from scripts/delegate.py:10169-10704 (B2).
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections.abc import Callable, Collection, Sequence
from pathlib import Path
from typing import Any

from scripts.common.git_context import sanitized_git_env
from scripts.common.repo_root import resolve_repo_root

_REPO_ROOT = resolve_repo_root(Path(__file__), 2)
DEFAULT_GIT_TIMEOUT_S = 30.0


def _sanitized_git_env() -> dict[str, str]:
    # Keep v2's config-injection isolation when applying the legacy cone profile.
    env = {key: value for key, value in sanitized_git_env(strip_config_injection=True).items()
           if not key.startswith("PRE_COMMIT")}
    return {**env, "GIT_TERMINAL_PROMPT": "0"}

_DISPATCH_SPARSE_EXCLUDE_DEFAULT = frozenset(
    {
        "curriculum",
        "wiki",
        "data/projects",
        "data/lexicon",
        "registry/projects",
        "data/datasets",
        "data/processed",
        "registry/lexicon/source-inventory",
        "registry/lexicon/source-inventory-review-decisions",
        "site/src/content",
        "site/src/data",
    }
)
# Cone directories kept inside an excluded tree so tests that every
# dispatch can run (``pytest -m repo_wide``, ``tests/curriculum``
# collection) still find the files they read. Each anchor is added only
# when that directory exists at HEAD.
_DISPATCH_SPARSE_ANCHORS: dict[str, tuple[str, ...]] = {
    "curriculum": (
        "curriculum/l2-uk-direct/a1",
        "curriculum/l2-uk-en/lesson-plans",
        "curriculum/l2-uk-en/plans/a1",
    ),
    "registry/lexicon/source-inventory": ("registry/lexicon/source-inventory/grade-01",),
    "registry/projects": ("registry/projects/open_model_data/integrations",),
}
# Owned-path prefixes that re-include a default-excluded tree even when the
# path itself is not under that tree (tests and scripts that read it).
# Filename stems end with "_" and match tests/test_open_model_*.py. Exact
# files are listed only when grep shows that file reads the tree.
# ``tests/test_open_model_`` is content-gated: most of those modules never
# read data/projects, and a blanket stem would check out ~633MB. The lexicon
# readers read the source inventories, which #8853 moved from data/lexicon
# to registry/lexicon. Frontend work under ``site/`` builds from the
# generated data and the published lessons. Test files are not listed: an
# owned test gets the trees its pytest.mark.needs_sparse_tree marks name
# (_owned_test_marked_trees).
_SOURCE_INVENTORY_READERS = (
    "scripts/lexicon",
    "tests/lexicon",
    "tests/test_source_inventory_",
    "scripts/audit/source_inventory_review_decisions.py",
    "scripts/audit/generate_source_inventory_review_candidates.py",
    "scripts/practice/author_densified_pairs.py",
    "scripts/practice/creation_review.py",
    "scripts/practice/thin_mode_source_inventory.py",
)
_SPARSE_OWNED_PATH_REINCLUDE: dict[str, tuple[str, ...]] = {
    # Landing pages take module titles from the plans and status files.
    "curriculum": ("scripts/generate_landing_pages.py",),
    "data/projects": (
        "data/projects",
        "tests/projects/open_model_data",
        "scripts/projects/open_model_data",
        "tests/test_open_model_",
    ),
    "registry/lexicon/source-inventory": _SOURCE_INVENTORY_READERS,
    "registry/lexicon/source-inventory-review-decisions": _SOURCE_INVENTORY_READERS,
    # Scripts whose tests carry pytest.mark.needs_sparse_tree for the tree.
    "site/src/content": (
        "site",
        "scripts/api/preparation_state.py",
        "scripts/generate_landing_pages.py",
        "scripts/generate_mdx/reading_links.py",
        "scripts/lexicon/lesson_atlas_link_census.py",
    ),
    "site/src/data": (
        "site",
        "scripts/audit/check_static_practice_assets.py",
        "scripts/lexicon/check_manifest_freshness.py",
        "scripts/lexicon/lesson_atlas_link_census.py",
    ),
}
# Stem prefixes whose match still has to mention the tree in that file.
_SPARSE_REINCLUDE_CONTENT_MARKERS: dict[str, tuple[str, ...]] = {
    "tests/test_open_model_": ("data/projects",),
}


def _sparse_path_has_prefix(path: str, prefix: str) -> bool:
    prefix = prefix.strip("/")
    return path == prefix or path.startswith(prefix + "/")


def _sparse_reinclude_prefix_matches(path: str, prefix: str) -> bool:
    """Match a directory prefix, an exact file, or a filename stem.

    Stems end with ``_`` so ``tests/test_open_model_`` matches
    ``tests/test_open_model_foundry_cli.py`` without also matching a
    sibling directory.
    """
    if _sparse_path_has_prefix(path, prefix):
        return True
    return prefix.endswith("_") and path.startswith(prefix)


def _assignment_mentions_marker(module_path: Path, name: str, markers: tuple[str, ...]) -> bool:
    """True when ``name = ...`` in ``module_path`` embeds a marker string."""
    try:
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeError):
        return False
    for stmt in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets = [stmt.target]
            value = stmt.value
        if value is None:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            rendered = ast.unparse(value)
            if any(marker in rendered for marker in markers):
                return True
    return False


def _imported_binding_mentions_marker(text: str, markers: tuple[str, ...]) -> bool:
    """True when the file uses an imported name whose value embeds a marker.

    Content-gated sparse stems used to require the literal ``data/projects``
    in the owned file. Readers that reach the tree through an imported path
    constant (``foundry.DEFAULT_V011_MANIFEST``) still need that tree.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    imported: dict[str, tuple[str, str]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                imported[alias.asname or alias.name] = (stmt.module, alias.name)
    needed: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.value.id)
            if binding is None:
                continue
            module, imported_name = binding
            needed.add((f"{module}.{imported_name}", node.attr))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.id)
            if binding is not None:
                needed.add(binding)
    for dotted, attr in needed:
        module_path = _REPO_ROOT / Path(*dotted.split(".")).with_suffix(".py")
        if module_path.is_file() and _assignment_mentions_marker(module_path, attr, markers):
            return True
    return False


def _reinclude_file_confirms(path: str, prefix: str) -> bool:
    """Content-gated stems must read the tree, directly or via an import."""
    markers = _SPARSE_REINCLUDE_CONTENT_MARKERS.get(prefix)
    if not markers:
        return True
    file_path = _REPO_ROOT / path
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return False
    if any(marker in text for marker in markers):
        return True
    return _imported_binding_mentions_marker(text, markers)


def _owned_test_marked_trees(path: str) -> tuple[str, ...]:
    """Excluded trees an owned test file names in ``pytest.mark.needs_sparse_tree``.

    The owner gets them, so the marked tests run instead of skipping. Test
    file names stay out of this module: the repo_wide marker prefilter
    (tests/test_repo_wide_marker_invariant.py) reads a file name in a module
    that loads modules dynamically as a load of that test, and this module is
    imported by tests/conftest.py, so every test became a candidate (#10777).
    """
    if not (path.startswith("tests/") and path.endswith(".py")):
        return ()
    try:
        tree = ast.parse((_REPO_ROOT / path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError, ValueError):
        return ()
    found = {
        arg.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "needs_sparse_tree"
        for arg in node.args
        if isinstance(arg, ast.Constant) and arg.value in _DISPATCH_SPARSE_EXCLUDE_DEFAULT
    }
    return tuple(sorted(found))


def _normalize_sparse_include(raw: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize --sparse-include values to unique default-excluded trees.

    Fail closed: explicit values must be names in the default exclusion set
    (``_DISPATCH_SPARSE_EXCLUDE_DEFAULT``). Other nested paths and unknown
    names raise :class:`ValueError`.
    """
    if not raw:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    allowed = ", ".join(sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT))
    for item in raw:
        name = str(item).strip().strip("/")
        if not name or name in {".", ".."} or name.startswith("../") or "/../" in f"/{name}/":
            raise ValueError(
                f"--sparse-include {item!r} is empty or invalid; "
                "pass a default-excluded tree such as 'curriculum', 'wiki', 'data/projects', "
                "or 'registry/projects'"
            )
        if name not in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
            if "/" in name:
                raise ValueError(f"--sparse-include {item!r} must name a default-excluded tree. Allowed: {allowed}")
            raise ValueError(f"--sparse-include {name!r} is not a default-excluded tree; allowed: {allowed}")
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def _infer_sparse_include_from_text(text: str | None) -> tuple[str, ...]:
    """Detect default-excluded path prefixes referenced in a prompt."""
    if not text:
        return ()
    found: list[str] = []
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        # Path-like reference: curriculum/…, data/projects/… — not bare words.
        if re.search(rf"(?<![\w.-]){re.escape(name)}/", text):
            found.append(name)
    return tuple(found)


def _sparse_owned_path_root(raw: str) -> str | None:
    """The repo-relative path an owned-path claim covers, read as ownership admission reads it.

    ``./site/src/data/x.json``, ``registry/./projects/x`` and ``a//b`` name
    the same path as their canonical spelling (``normalize_claim``). A glob
    covers the literal directories before its first wildcard segment
    (``curriculum/l2-uk-en/**/lessons.lock.yaml`` covers
    ``curriculum/l2-uk-en``). A claim that owns nothing (empty, ``.``,
    absolute, ``..``) covers nothing.
    """
    try:
        from scripts.guardrails.delegate_ownership import ClaimKind, normalize_claim, owned_path_matcher
    except ImportError:  # pragma: no cover - flat script path
        from guardrails.delegate_ownership import ClaimKind, normalize_claim, owned_path_matcher  # type: ignore

    if owned_path_matcher(raw) is None:
        return None
    claim = normalize_claim(raw)
    if claim.kind is ClaimKind.SUBTREE:
        return claim.norm
    literal: list[str] = []
    for segment in claim.norm.split("/"):
        if any(ch in segment for ch in "*?["):
            break
        literal.append(segment)
    root = normalize_claim("/".join(literal))
    return root.norm if root.kind is ClaimKind.SUBTREE else None


def _sparse_trees_for_owned_path(raw: str) -> tuple[str, ...]:
    """Return the excluded trees an owned path (``--owned-path`` or research) requires.

    A path inside an excluded tree needs that tree. A directory that holds
    excluded trees (``site``, ``registry/lexicon``) needs all of them. A
    path outside every excluded tree needs the trees its reader prefixes
    name in ``_SPARSE_OWNED_PATH_REINCLUDE`` and, for a test file, the trees
    its ``needs_sparse_tree`` marks name.
    """
    path = _sparse_owned_path_root(str(raw))
    if path is None:
        return ()
    for name in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
        if _sparse_path_has_prefix(path, name):
            return (name,)
    nested = sorted(name for name in _DISPATCH_SPARSE_EXCLUDE_DEFAULT if name.startswith(path + "/"))
    return tuple(
        dict.fromkeys(
            [
                *nested,
                *(
                    tree
                    for tree, prefixes in _SPARSE_OWNED_PATH_REINCLUDE.items()
                    if any(
                        _sparse_reinclude_prefix_matches(path, prefix) and _reinclude_file_confirms(path, prefix)
                        for prefix in prefixes
                    )
                ),
                *_owned_test_marked_trees(path),
            ]
        )
    )


def _infer_sparse_include(
    explicit: Sequence[str] | None,
    *,
    owned_paths: Sequence[str] | None = None,
    prompt_text: str | None = None,
) -> tuple[str, ...]:
    """Merge explicit includes with owned-path prefixes and prompt path references.

    ``owned_paths`` holds the dispatch's ``--owned-path`` claims and its
    ``--research-owned-path`` values. An owned path such as
    ``curriculum/...``, ``scripts/projects/open_model_data/...`` or a lexicon
    reader such as ``scripts/lexicon/...`` materializes the matching excluded
    tree without a second flag.
    """
    merged: list[str] = list(_normalize_sparse_include(explicit))
    seen = set(merged)
    for raw in owned_paths or ():
        for name in _sparse_trees_for_owned_path(str(raw)):
            if name not in seen:
                seen.add(name)
                merged.append(name)
    for name in _infer_sparse_include_from_text(prompt_text):
        if name not in seen:
            seen.add(name)
            merged.append(name)
    return tuple(merged)


def _list_worktree_dirs(worktree_path: Path, *tree_path: str, at_ref: str = "HEAD") -> list[str]:
    """Return directory names from ``git ls-tree -d`` at ``at_ref``.

    With no ``tree_path``, lists top-level directories. ``data/`` lists the
    children (``data/projects``, …) so new ``data/*`` dirs are included
    automatically and only the named exclusions drop out.
    """
    label = "/".join(tree_path) if tree_path else "top-level"
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-d", "--name-only", at_ref, *tree_path],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not list {label} dirs in {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git ls-tree failed").strip()
        raise RuntimeError(f"could not list {label} dirs in {worktree_path}: {detail}")
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _list_worktree_top_dirs(worktree_path: Path, *, at_ref: str = "HEAD") -> list[str]:
    """Return top-level directory names at ``at_ref`` inside a worktree."""
    return _list_worktree_dirs(worktree_path, at_ref=at_ref)


def _dispatch_sparse_cone_dirs(
    list_dirs: Callable[[str], Sequence[str]],
    exclude: Collection[str],
) -> tuple[list[str], list[str]]:
    """Build a cone include list that drops excluded dirs at directory level.

    ``list_dirs("")`` returns the top-level directories and
    ``list_dirs("site/src")`` the repo-relative child directories of
    ``site/src``. A nested exclusion (``data/projects``,
    ``site/src/data``) is expressed by listing the sibling directories at
    every level down to it instead of their parent. Cone mode then keeps
    files directly in each parent and preserves the other sibling trees.
    A parent whose every child directory is excluded keeps its own files
    only when an anchor sits below it, since cone mode has no file entries.
    """
    exclude_set = {name.strip("/") for name in exclude}
    cone: list[str] = []
    excluded: list[str] = []

    def walk(parent: str) -> None:
        cone_start, excluded_start = len(cone), len(excluded)
        for child in list_dirs(parent):
            if parent and not child.startswith(parent + "/"):
                # Not a child of ``parent``: descending again would never end.
                continue
            if child in exclude_set:
                excluded.append(child)
            elif any(name.startswith(child + "/") for name in exclude_set):
                cone_mark, excluded_mark = len(cone), len(excluded)
                walk(child)
                if len(excluded) == excluded_mark:
                    # Nothing beneath exists at this ref: keep the whole tree,
                    # including the files directly in it.
                    del cone[cone_mark:]
                    cone.append(child)
            else:
                cone.append(child)
        if parent and len(excluded) > excluded_start and len(cone) == cone_start:
            # Cone mode needs a child entry to retain files directly in a parent
            # whose children are all excluded. Preserve v2's parent-file contract
            # without materializing any excluded child or creating a tracked file.
            cone.append(parent + "/.dispatch-parent-files")

    walk("")
    return cone, sorted(excluded)


def _dispatch_sparse_profile(
    list_dirs: Callable[[str], Sequence[str]],
    sparse_include: Sequence[str] = (),
) -> tuple[list[str], list[str]]:
    """Return ``(cone_dirs, excluded_trees)`` for the default dispatch profile.

    ``sparse_include`` names default-excluded trees to keep. Anchors of a
    tree that stays excluded join the cone when they exist at HEAD.
    """
    includes = _normalize_sparse_include(sparse_include)
    exclude = set(_DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(includes)
    included, excluded = _dispatch_sparse_cone_dirs(list_dirs, exclude)
    for tree in excluded:
        for anchor in _DISPATCH_SPARSE_ANCHORS.get(tree, ()):
            parent = anchor.rpartition("/")[0]
            if anchor in list_dirs(parent):
                included.append(anchor)
    return included, excluded


def _worktree_dir_lister(worktree_path: Path) -> Callable[[str], list[str]]:
    """List directories at HEAD in ``worktree_path`` for the sparse profile."""

    def list_dirs(parent: str) -> list[str]:
        if not parent:
            return _list_worktree_top_dirs(worktree_path)
        return _list_worktree_dirs(worktree_path, parent + "/")

    return list_dirs


def _apply_dispatch_sparse_checkout(
    worktree_path: Path,
    *,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
) -> dict[str, Any]:
    """Apply (or disable) cone sparse-checkout on a dispatch worktree.

    The default profile drops every tree in
    ``_DISPATCH_SPARSE_EXCLUDE_DEFAULT``; nested trees such as
    ``site/src/data`` are dropped by listing their siblings, so the rest of
    ``site/`` stays. Anchors in ``_DISPATCH_SPARSE_ANCHORS`` keep the files
    collection reads (``curriculum/l2-uk-en/curriculum.yaml``) without the
    rest of their tree. ``--full-checkout`` disables sparse mode.
    ``--sparse-include`` keeps a named excluded tree.
    """
    includes = _normalize_sparse_include(sparse_include)
    telemetry: dict[str, Any] = {
        "full_checkout": bool(full_checkout),
        "sparse_include": list(includes),
        "excluded": [],
        "included_dirs": [],
        "applied": False,
        "error": None,
    }

    def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        # Must sanitize GIT_* so sparse-checkout applies to *this* worktree
        # when a parent harness injects GIT_DIR/GIT_WORK_TREE (pre-commit, etc.).
        try:
            return subprocess.run(
                args,
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=args,
                returncode=124,
                stdout="",
                stderr=f"sparse-checkout command timed out after {DEFAULT_GIT_TIMEOUT_S}s",
            )

    if full_checkout:
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    included, excluded = _dispatch_sparse_profile(_worktree_dir_lister(worktree_path), includes)
    telemetry["excluded"] = excluded
    telemetry["included_dirs"] = included

    if not excluded:
        # Nothing to drop at this ref (or everything was re-included). Prefer a
        # full tree rather than an empty cone set.
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    proc = _run_git(["git", "sparse-checkout", "init", "--cone"])
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout init failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(f"failed to init sparse-checkout in {worktree_path}: {detail}")

    set_args = ["git", "sparse-checkout", "set", "--cone"]
    if included:
        set_args.extend(["--", *included])
    proc = _run_git(set_args)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout set failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(
            f"failed to set sparse-checkout in {worktree_path}: {detail}. "
            "Commit/stash local changes under excluded paths, or pass "
            "--full-checkout / --sparse-include."
        )

    telemetry["applied"] = True
    print(
        f"🌲 dispatch sparse-checkout: excluded {', '.join(excluded)} "
        f"in {worktree_path} "
        "(git sparse-checkout add <dir>, or --sparse-include / --full-checkout)",
        file=sys.stderr,
    )
    return telemetry
