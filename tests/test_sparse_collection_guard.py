"""Collection stays error-free when default sparse trees are absent.

No repo copy (``cp -al`` walks the whole checkout and fails across
filesystems): ``SPARSE_TEST_FORCE_MISSING_TREES`` makes the shared sparse
predicate in ``tests/sparse_trees.py`` — the same one ``tests/conftest.py``'s
``sparse_missing_tree_skip_reason`` consumes — treat ``curriculum/``,
``wiki/``, ``data/projects/``, and ``data/lexicon/`` as absent, then a
subprocess runs ``pytest --collect-only`` with that switch on.

Coverage is derived, not sampled: every test module whose module-level code
(imports, assignments, decorators, parametrize arguments) names one of the
sparse trees, unioned with the test modules changed by #8581 that reach the
trees through helper calls the scan cannot see. Modules that read the trees
only inside test bodies cannot break collection and are excluded to keep the
guard fast.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ABSENT_TREES = ("curriculum", "wiki", "data/projects", "data/lexicon")
_TREE_REFERENCE = re.compile(r"data/projects|data/lexicon|curriculum/|wiki/")
_BARE_SEGMENTS = ("curriculum", "wiki")


def _references_sparse_tree(value: str) -> bool:
    if _TREE_REFERENCE.search(value):
        return True
    # Path-join segments: root / "curriculum" / ... or ".../wiki".
    return value in _BARE_SEGMENTS or any(value.endswith(f"/{tree}") for tree in _BARE_SEGMENTS)

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
        isinstance(sub, ast.Constant) and isinstance(sub.value, str) and _references_sparse_tree(sub.value)
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


def test_tree_referencing_modules_collect_when_sparse_trees_are_absent() -> None:
    env = os.environ.copy()
    env["SPARSE_TEST_FORCE_MISSING_TREES"] = ",".join(_ABSENT_TREES)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *_collection_targets(),
            "--collect-only",
            "-q",
            "--tb=line",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=100,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "errors during collection" not in output
    assert "Interrupted:" not in output
