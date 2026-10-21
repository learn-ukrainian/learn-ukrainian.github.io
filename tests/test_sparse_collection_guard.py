"""Collection stays error-free when default sparse trees are absent.

No repo copy (``cp -al`` walks the whole checkout and fails across
filesystems). A child ``pytest --collect-only`` sets
``SPARSE_TEST_FORCE_MISSING_TREES`` so ``tree_absent()`` — the predicate
``tests/conftest.py``'s ``sparse_missing_tree_skip_reason`` consumes — treats
the default dispatch exclusions (``scripts/delegate.py``
``_DISPATCH_SPARSE_EXCLUDE_DEFAULT``) as absent, except the cone anchors a
default dispatch checkout keeps (``_DISPATCH_SPARSE_ANCHORS``, #10777).
The same child loads ``tests.sparse_collection_audit``, which raises
``FileNotFoundError`` for reads of those trees and for ``os.stat`` /
``os.lstat`` (so ``Path.exists()`` agrees). Paths are resolved, so a symlink
or ``/proc/self/cwd`` spelling is the same as the tree's real path. The
environment variable alone does not hide files on a full checkout; the hook
does, and it is installed only in that child.

Coverage is derived, not sampled: every test module whose module-level code
(imports, assignments, decorators, parametrize arguments) names one of the
sparse trees, unioned with the test modules changed by #8581 that reach the
trees through helper calls the scan cannot see. Modules that read the trees
only inside test bodies cannot break collection and are excluded to keep the
guard fast. The child collects their common parent directory once and ignores
every other test file (``tests.sparse_collection_scope``). One pytest
argument per module makes pytest re-scan that directory each time, which was
the per-PR cost.

A module-level ``skipped`` outcome only passes for a target and reason on the
``_ALLOWED_SKIP_REASONS`` allow-list. An unlisted skip — a dependency import
via ``pytest.importorskip``, or a module that catches an absent sparse tree
and skips instead of failing — is exactly the failure class this guard
exists to catch, so it fails the guard.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts import delegate
from tests.sparse_collection_scope import OUTCOMES_FILE_ENV, SCOPE_FILE_ENV
from tests.sparse_trees import FORCE_MISSING_TREES_ENV, REPO_ROOT_ENV, VISIBLE_ANCHORS_ENV

pytestmark = [pytest.mark.reads_content, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ABSENT_TREES = tuple(sorted(delegate._DISPATCH_SPARSE_EXCLUDE_DEFAULT))
_VISIBLE_ANCHORS = tuple(sorted(anchor for anchors in delegate._DISPATCH_SPARSE_ANCHORS.values() for anchor in anchors))
# A nested tree is named by its full path; a top-level one by "tree/" so the
# bare word in prose does not match.
_TREE_REFERENCE = re.compile(
    "|".join(re.escape(tree if "/" in tree else f"{tree}/") for tree in sorted(_ABSENT_TREES, key=len, reverse=True))
)
_BARE_SEGMENTS = tuple(tree for tree in _ABSENT_TREES if "/" not in tree)


def _references_sparse_tree(value: str) -> bool:
    if _TREE_REFERENCE.search(value):
        return True
    # Path-join segments: root / "curriculum" / ... or ".../wiki".
    return value in _BARE_SEGMENTS or any(value.endswith(f"/{tree}") for tree in _BARE_SEGMENTS)


def _div_segments(node: ast.AST) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_segments(node.left) + _div_segments(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def _joins_sparse_tree(node: ast.AST) -> bool:
    """``root / "site" / "src" / "data"`` names a nested tree one segment at a time."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return False
    joined = "/".join(_div_segments(node))
    return any(joined == tree or f"{tree}/" in f"{joined}/" for tree in _ABSENT_TREES if "/" in tree)


# Test modules changed by #8581. Unioned with the derived scan so coverage of
# the modules this fix touched can never silently shrink — the scan alone
# cannot see modules that reach the trees through helper calls (e.g.
# test_plan_validate_cross.py parametrizes via _cross_case_parameters()).
_PR_CHANGED_MODULES = (
    "tests/curriculum/test_plan_validate_cross.py",
    "tests/projects/open_model_data/test_a10_pilot_review_gate.py",
    "tests/projects/open_model_data/test_a11_silver_release_gate.py",
    "tests/projects/open_model_data/test_a12_gold_overlay_gate.py",
    "tests/projects/open_model_data/test_a13_cleanup_recovery.py",
    "tests/projects/open_model_data/test_a3_builder_packet.py",
    "tests/projects/open_model_data/test_a3_heldout_family_assignment_script.py",
    "tests/projects/open_model_data/test_a4_deterministic_extraction.py",
    "tests/projects/open_model_data/test_a5_evidence_enrichment.py",
    "tests/projects/open_model_data/test_a6_blind_arena.py",
    "tests/projects/open_model_data/test_a7_original_row_factory.py",
    "tests/projects/open_model_data/test_a8_admission_assembly.py",
    "tests/projects/open_model_data/test_a9_evaluation_package.py",
    "tests/projects/open_model_data/test_v4_per_slot_factory.py",
    "tests/projects/open_model_data/test_v4_slot_assignment.py",
    "tests/test_open_model_phase3_p2_contracts.py",
    "tests/test_open_model_phase3_pravopys_evaluation_context.py",
)


def _contains_tree_reference(node: ast.AST) -> bool:
    return any(
        (isinstance(sub, ast.Constant) and isinstance(sub.value, str) and _references_sparse_tree(sub.value))
        or _joins_sparse_tree(sub)
        for sub in ast.walk(node)
    )


def _module_level_tree_reference(path: Path) -> bool:
    """True when a tree name appears outside function/class bodies.

    Function bodies run at test time, not collection; decorators, default
    arguments, and module-level statements run at import and can abort
    collection.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parts = list(node.decorator_list)
            parts += [default for default in (*node.args.defaults, *node.args.kw_defaults) if default]
        elif isinstance(node, ast.ClassDef):
            parts = [*node.decorator_list, *node.bases, *[keyword.value for keyword in node.keywords]]
        else:
            parts = [node]
        if any(_contains_tree_reference(part) for part in parts):
            return True
    return False


def _collection_targets() -> list[str]:
    derived = {
        path.relative_to(_REPO_ROOT).as_posix()
        for path in (_REPO_ROOT / "tests").rglob("test_*.py")
        if _module_level_tree_reference(path)
    }
    targets = derived | set(_PR_CHANGED_MODULES)
    missing = [module for module in targets if not (_REPO_ROOT / module).is_file()]
    assert not missing, f"collection targets no longer exist: {missing}"
    return sorted(targets)


def _resolved_targets(targets: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        resolved.append(path.resolve())
    missing = [str(path) for path in resolved if not path.is_file()]
    assert not missing, f"collection targets no longer exist: {missing}"
    return resolved


def _collection_directory(resolved: list[Path]) -> Path:
    """Narrowest directory that contains every target."""
    common = Path(os.path.commonpath([str(path) for path in resolved]))
    if common.is_file():
        return common.parent
    return common


def _pytest_collection_arg(directory: Path, cwd: Path) -> str:
    try:
        relative = directory.resolve().relative_to(cwd.resolve())
    except ValueError:
        return directory.as_posix()
    text = relative.as_posix()
    return text or "."


def collect_with_absent_trees(
    targets: list[str],
    *,
    cwd: Path | None = None,
    repo_root: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, dict[str, str | None]]]:
    """Run ``pytest --collect-only`` in a child that cannot see the sparse trees.

    The audit plugin is named on the command line and imported only by the
    child. This process does not import it, so the hook stays inactive here.
    The same child loads ``tests.sparse_collection_scope`` and collects the
    targets' common parent once, ignoring every test module outside ``targets``.
    Eager-read failures still abort that collection. The child writes each
    target's outcome (``collected``, ``skipped``, or ``failed``, plus the
    skip reason when applicable) beside the scope file; both are removed
    before this returns. ``extra_env`` is merged into the child's
    environment, e.g. to redirect ``connect_sources_db()`` at a scratch
    database via ``LU_SOURCES_DB`` without touching the repository tree.
    """
    work = cwd or _REPO_ROOT
    root = Path(os.path.abspath(repo_root or _REPO_ROOT))
    resolved = _resolved_targets(targets)
    directory = _collection_directory(resolved)
    env = os.environ.copy()
    env[FORCE_MISSING_TREES_ENV] = ",".join(_ABSENT_TREES)
    # Like _dispatch_sparse_profile, keep only anchors that exist in the checkout.
    env[VISIBLE_ANCHORS_ENV] = ",".join(anchor for anchor in _VISIBLE_ANCHORS if (root / anchor).is_dir())
    env[REPO_ROOT_ENV] = str(root)
    # The child runs in an isolated scratch cwd and loads its own audit plugin.
    # The dispatch parent's plugin is not importable there.
    env.pop("PYTEST_PLUGINS", None)
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_REPO_ROOT) if not prior else f"{_REPO_ROOT}{os.pathsep}{prior}"
    scratch = tempfile.mkdtemp(prefix="sparse-collection-")
    scope_path = os.path.join(scratch, "scope.txt")
    outcomes_path = os.path.join(scratch, "outcomes.json")
    Path(scope_path).write_text("\n".join(path.as_posix() for path in resolved) + "\n", encoding="utf-8")
    env[SCOPE_FILE_ENV] = scope_path
    env[OUTCOMES_FILE_ENV] = outcomes_path
    if extra_env:
        env.update(extra_env)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                _pytest_collection_arg(directory, work),
                "--collect-only",
                "-q",
                "--tb=line",
                "-o",
                "addopts=",
                "-p",
                "no:cacheprovider",
                "-p",
                "tests.sparse_collection_scope",
                "-p",
                "tests.sparse_collection_audit",
            ],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=100,
        )
        return completed, _read_collection_outcomes(outcomes_path)
    finally:
        shutil.rmtree(scratch)


def _read_collection_outcomes(path: str) -> dict[str, dict[str, str | None]]:
    file = Path(path)
    try:
        text = file.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key): {"status": str(value.get("status")), "reason": value.get("reason")}
        for key, value in data.items()
        if isinstance(value, dict)
    }


# Module-level skips this guard accepts as a passing outcome, keyed by the
# repo-relative target path the skip must come from. The value is a stable
# substring of the skip reason — not the whole message, which may drift
# (line numbers, environment specifics). Any other module-level skip means a
# missing dependency or an absent sparse tree was silently swallowed, which
# is the failure class this guard exists to catch, so it fails the guard.
_ALLOWED_SKIP_REASONS: dict[str, str] = {
    "tests/test_citation_resolution_invariant.py": "sources.db not populated",
}


def _assert_targets_reported(
    completed: subprocess.CompletedProcess[str],
    outcomes: dict[str, dict[str, str | None]],
    targets: list[str],
) -> None:
    """Collection succeeded, and every target was collected or an allow-listed skip."""
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "errors during collection" not in output
    assert "Interrupted:" not in output
    resolved = _resolved_targets(targets)
    failed = [
        target
        for target, path in zip(targets, resolved, strict=True)
        if outcomes.get(path.as_posix(), {}).get("status") == "failed"
    ]
    assert not failed, f"collection failed: {failed}\n{output[-2000:]}"
    unexpected = [
        f"{target}={outcomes.get(path.as_posix(), {}).get('status')!r}"
        for target, path in zip(targets, resolved, strict=True)
        if outcomes.get(path.as_posix(), {}).get("status") not in {"collected", "skipped"}
    ]
    assert not unexpected, f"collection outcomes: {unexpected}\n{output[-2000:]}"
    unallowed_skips = []
    for target, path in zip(targets, resolved, strict=True):
        entry = outcomes.get(path.as_posix(), {})
        if entry.get("status") != "skipped":
            continue
        reason = str(entry.get("reason") or "")
        allowed_reason = _ALLOWED_SKIP_REASONS.get(target)
        if allowed_reason is None or allowed_reason not in reason:
            unallowed_skips.append(f"{target}: {reason!r}")
    assert not unallowed_skips, f"unallowed module-level skip: {unallowed_skips}\n{output[-2000:]}"


def _unmaterialized_anchors(root: Path) -> list[str]:
    """Anchors tracked at HEAD that this sparse checkout has not checked out.

    A worktree created before an anchor joined the default profile lacks the
    files the anchor brings, so the child cannot collect their readers there.
    """
    # A pre-push hook runs with GIT_DIR and friends set for the pushing checkout.
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    missing: list[str] = []
    for anchor in _VISIBLE_ANCHORS:
        listed = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-d", "--name-only", "HEAD", anchor],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=30,
        )
        if listed.returncode == 0 and listed.stdout.strip() == anchor and not (root / anchor).is_dir():
            missing.append(anchor)
    return missing


@pytest.mark.slow
def test_tree_referencing_modules_collect_when_sparse_trees_are_absent() -> None:
    missing = _unmaterialized_anchors(_REPO_ROOT)
    assert not missing, (
        "this sparse checkout predates the default dispatch profile and lacks its anchors; run "
        f"`git sparse-checkout add {' '.join(missing)}` and push again (#10777)"
    )
    targets = _collection_targets()
    completed, outcomes = collect_with_absent_trees(targets)
    _assert_targets_reported(completed, outcomes, targets)


def test_unmaterialized_anchor_names_the_command_to_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    anchor = _VISIBLE_ANCHORS[0]
    (repo / anchor).mkdir(parents=True)
    (repo / anchor / "kept.txt").write_text("x\n", encoding="utf-8")
    env = {"GIT_CEILING_DIRECTORIES": str(tmp_path), "HOME": str(tmp_path), "PATH": os.environ.get("PATH", "")}
    for args in (
        ["init", "-q", "-b", "main"],
        ["add", "."],
        ["-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init"],
    ):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env, timeout=30)

    assert _unmaterialized_anchors(repo) == []
    shutil.rmtree(repo / anchor)
    assert _unmaterialized_anchors(repo) == [anchor]
