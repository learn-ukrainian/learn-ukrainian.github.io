"""Collection stays error-free when default sparse trees are absent.

No repo copy (``cp -al`` walks the whole checkout and fails across
filesystems). A child ``pytest --collect-only`` sets
``SPARSE_TEST_FORCE_MISSING_TREES`` so ``tree_absent()`` — the predicate
``tests/conftest.py``'s ``sparse_missing_tree_skip_reason`` consumes — treats
``curriculum/``, ``wiki/``, ``data/projects/``, and ``data/lexicon/`` as
absent. The same child loads ``tests.sparse_collection_audit``, which raises
``FileNotFoundError`` for reads of those trees. The environment variable
alone does not hide files on a full checkout; the hook does, and it is
installed only in that child.

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

from tests.sparse_trees import FORCE_MISSING_TREES_ENV, REPO_ROOT_ENV

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


def collect_with_absent_trees(
    targets: list[str],
    *,
    cwd: Path | None = None,
    repo_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``pytest --collect-only`` in a child that cannot see the sparse trees.

    The audit plugin is named on the command line and imported only by the
    child. This process does not import it, so the hook stays inactive here.
    """
    work = cwd or _REPO_ROOT
    root = Path(os.path.abspath(repo_root or _REPO_ROOT))
    env = os.environ.copy()
    env[FORCE_MISSING_TREES_ENV] = ",".join(_ABSENT_TREES)
    env[REPO_ROOT_ENV] = str(root)
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_REPO_ROOT) if not prior else f"{_REPO_ROOT}{os.pathsep}{prior}"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            "--collect-only",
            "-q",
            "--tb=line",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
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


def test_tree_referencing_modules_collect_when_sparse_trees_are_absent() -> None:
    completed = collect_with_absent_trees(_collection_targets())
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "errors during collection" not in output
    assert "Interrupted:" not in output


def _existing_curriculum_file(repo: Path) -> Path | None:
    curriculum = repo / "curriculum"
    if not curriculum.is_dir():
        return None
    preferred = (
        curriculum / "l2-uk-direct" / "manifest.yaml",
        curriculum / "l2-uk-en" / "curriculum.yaml",
    )
    for path in preferred:
        if path.is_file():
            return path
    for path in curriculum.rglob("*"):
        if path.is_file():
            return path
    return None


def _write_eager_modules(directory: Path, curriculum_file: Path, lexicon: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    reader = directory / "test_eager_curriculum_read.py"
    reader.write_text(
        "from pathlib import Path\n"
        f"Path({str(curriculum_file)!r}).read_text(encoding='utf-8')\n"
        "\n"
        "def test_eager_curriculum_read() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    lister = directory / "test_eager_lexicon_list.py"
    lister.write_text(
        "import os\n"
        f"os.listdir({str(lexicon)!r})\n"
        "\n"
        "def test_eager_lexicon_list() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    return [reader, lister]


def _assert_eager_collection_fails(modules: list[Path], *, repo_root: Path) -> None:
    completed = collect_with_absent_trees(
        [str(module) for module in modules],
        cwd=modules[0].parent,
        repo_root=repo_root,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0, output
    assert "FileNotFoundError" in output, output
    assert "during collection" in output, output
    for module in modules:
        assert module.name in output, output


def test_guard_child_errors_on_eager_reads_of_present_trees(tmp_path: Path) -> None:
    """Eager import-time reads fail collection even when the files exist.

    The materialized tree is the full-checkout case: the parent can read it,
    and the child still errors. The same helper is then pointed at this
    checkout, whose trees are present in a full worktree and absent in a
    sparse one; either way an import-time read must not collect cleanly.
    """
    fake = tmp_path / "full-checkout"
    curriculum_file = fake / "curriculum" / "lesson.txt"
    curriculum_file.parent.mkdir(parents=True)
    curriculum_file.write_text("привіт\n", encoding="utf-8")
    lexicon = fake / "data" / "lexicon"
    lexicon.mkdir(parents=True)
    (lexicon / "entry.json").write_text("{}\n", encoding="utf-8")
    (fake / "wiki").mkdir()
    (fake / "data" / "projects").mkdir()
    assert curriculum_file.read_text(encoding="utf-8") == "привіт\n"
    assert os.listdir(lexicon) == ["entry.json"]
    _assert_eager_collection_fails(
        _write_eager_modules(tmp_path / "fake-modules", curriculum_file, lexicon),
        repo_root=fake,
    )

    worktree_lexicon = _REPO_ROOT / "data" / "lexicon"
    worktree_file = _existing_curriculum_file(_REPO_ROOT)
    if worktree_file is None:
        worktree_file = _REPO_ROOT / "curriculum" / "l2-uk-direct" / "manifest.yaml"
    else:
        assert worktree_file.read_text(encoding="utf-8")
    if worktree_lexicon.is_dir():
        assert os.listdir(worktree_lexicon)
    _assert_eager_collection_fails(
        _write_eager_modules(tmp_path / "worktree-modules", worktree_file, worktree_lexicon),
        repo_root=_REPO_ROOT,
    )
