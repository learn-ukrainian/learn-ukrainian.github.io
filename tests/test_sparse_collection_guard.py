"""Collection stays error-free when default sparse trees are absent.

No repo copy (``cp -al`` walks the whole checkout and fails across
filesystems). A child ``pytest --collect-only`` sets
``SPARSE_TEST_FORCE_MISSING_TREES`` so ``tree_absent()`` — the predicate
``tests/conftest.py``'s ``sparse_missing_tree_skip_reason`` consumes — treats
``curriculum/``, ``wiki/``, ``data/projects/``, and ``data/lexicon/`` as
absent. The same child loads ``tests.sparse_collection_audit``, which raises
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
guard fast.
"""

from __future__ import annotations

import ast
import errno
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.sparse_trees import FORCE_MISSING_TREES_ENV, REPO_ROOT_ENV

pytestmark = pytest.mark.reads_content

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


def _assert_eager_collection_fails(
    modules: list[Path],
    *,
    repo_root: Path,
    cwd: Path | None = None,
) -> None:
    completed = collect_with_absent_trees(
        [str(module) for module in modules],
        cwd=cwd or modules[0].parent,
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


def _present_fake_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Return ``(repo, curriculum_file)`` with all four sparse trees present."""
    fake = tmp_path / "full-checkout"
    curriculum_file = fake / "curriculum" / "lesson.txt"
    curriculum_file.parent.mkdir(parents=True)
    curriculum_file.write_text("привіт\n", encoding="utf-8")
    lexicon = fake / "data" / "lexicon"
    lexicon.mkdir(parents=True)
    (lexicon / "entry.json").write_text("{}\n", encoding="utf-8")
    (fake / "wiki").mkdir()
    (fake / "data" / "projects").mkdir()
    return fake, curriculum_file


def _curriculum_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Return ``(repo, curriculum_file)`` with only the curriculum tree present.

    The guard hides every forced tree whether or not that directory exists.
    These probes only need a file inside ``curriculum/``.
    """
    fake = tmp_path / "full-checkout"
    curriculum_file = fake / "curriculum" / "lesson.txt"
    curriculum_file.parent.mkdir(parents=True)
    curriculum_file.write_text("привіт\n", encoding="utf-8")
    return fake, curriculum_file


def _write_module(directory: Path, name: str, source: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(source, encoding="utf-8")
    return path


def test_guard_child_blocks_proc_cwd_and_symlink_reads(tmp_path: Path) -> None:
    """A read whose spelling is not the tree root still fails collection.

    ``/proc/self/cwd/<tree>/…``, a symlink created outside the tree, and a
    ``..`` segment after that symlink all resolve inside it. The parent
    process has no hook, so the same paths still read.
    """
    fake, curriculum_file = _present_fake_repo(tmp_path)
    link = tmp_path / "into-tree"
    link.symlink_to(curriculum_file)
    alias_dir = tmp_path / "alias-dir"
    alias_dir.symlink_to(curriculum_file.parent)
    dotdot = os.path.join(tmp_path, "alias-dir", "..", "curriculum", "lesson.txt")
    assert curriculum_file.read_text(encoding="utf-8") == "привіт\n"
    assert link.read_text(encoding="utf-8") == "привіт\n"
    assert Path(dotdot).read_text(encoding="utf-8") == "привіт\n"
    modules = tmp_path / "resolved-modules"
    proc_reader = _write_module(
        modules,
        "test_proc_cwd_read.py",
        "from pathlib import Path\n"
        "Path('/proc/self/cwd/curriculum/lesson.txt').read_text(encoding='utf-8')\n"
        "\n"
        "def test_proc_cwd_read() -> None:\n"
        "    pass\n",
    )
    link_reader = _write_module(
        modules,
        "test_symlink_read.py",
        "from pathlib import Path\n"
        f"Path({str(link)!r}).read_text(encoding='utf-8')\n"
        "\n"
        "def test_symlink_read() -> None:\n"
        "    pass\n",
    )
    dotdot_reader = _write_module(
        modules,
        "test_symlink_dotdot_read.py",
        "from pathlib import Path\n"
        f"Path({dotdot!r}).read_text(encoding='utf-8')\n"
        "\n"
        "def test_symlink_dotdot_read() -> None:\n"
        "    pass\n",
    )
    _assert_eager_collection_fails(
        [proc_reader, link_reader, dotdot_reader],
        repo_root=fake,
        cwd=fake,
    )
    assert curriculum_file.read_text(encoding="utf-8") == "привіт\n"
    assert link.read_text(encoding="utf-8") == "привіт\n"
    assert Path(dotdot).read_text(encoding="utf-8") == "привіт\n"


def test_guard_child_existence_checks_hide_present_trees(tmp_path: Path) -> None:
    """``Path.exists()`` is false in the guarded child, and that aborts collection.

    The parent still sees the file. The child is a separate process: a direct
    probe checks ``Path.exists()``, ``os.path.exists()``, ``Path.is_dir()``,
    ``os.stat``, and ``os.lstat``, then a module-level ``if not p.exists():
    raise`` fails collection. ``dir_fd`` and ``follow_symlinks`` still reach
    ``os.stat`` for a path outside the trees.
    """
    fake, curriculum_file = _present_fake_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    outside_link = tmp_path / "outside-link"
    outside_link.symlink_to(outside)
    assert curriculum_file.exists()
    assert os.path.exists(curriculum_file)
    assert curriculum_file.parent.is_dir()
    assert os.stat(curriculum_file).st_size > 0

    env = os.environ.copy()
    env[FORCE_MISSING_TREES_ENV] = ",".join(_ABSENT_TREES)
    env[REPO_ROOT_ENV] = str(Path(os.path.abspath(fake)))
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_REPO_ROOT) if not prior else f"{_REPO_ROOT}{os.pathsep}{prior}"
    env["TREE_FILE"] = str(curriculum_file)
    env["TREE_DIR"] = str(curriculum_file.parent)
    env["OUTSIDE_FILE"] = str(outside)
    env["OUTSIDE_LINK"] = str(outside_link)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os\n"
            "import stat\n"
            "from pathlib import Path\n"
            "import tests.sparse_collection_audit\n"
            "tree_file = Path(os.environ['TREE_FILE'])\n"
            "tree_dir = Path(os.environ['TREE_DIR'])\n"
            "outside = os.environ['OUTSIDE_FILE']\n"
            "link = os.environ['OUTSIDE_LINK']\n"
            "print('exists=' + str(tree_file.exists()).lower())\n"
            "print('path_exists=' + str(os.path.exists(tree_file)).lower())\n"
            "print('is_dir=' + str(tree_dir.is_dir()).lower())\n"
            "for label, fn in (('stat', os.stat), ('lstat', os.lstat)):\n"
            "    try:\n"
            "        fn(tree_file)\n"
            "        print(label + '=visible')\n"
            "    except FileNotFoundError as exc:\n"
            "        print(f'{label}={exc.errno}')\n"
            "os.stat(outside, follow_symlinks=True)\n"
            "followed = os.stat(link, follow_symlinks=False)\n"
            "assert stat.S_ISLNK(followed.st_mode)\n"
            "parent = os.path.dirname(outside)\n"
            "fd = os.open(parent, os.O_RDONLY)\n"
            "try:\n"
            "    os.stat(os.path.basename(outside), dir_fd=fd, follow_symlinks=True)\n"
            "    os.lstat(os.path.basename(outside), dir_fd=fd)\n"
            "finally:\n"
            "    os.close(fd)\n"
            "print('outside=ok')\n",
        ],
        cwd=fake,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    probe_output = probe.stdout + probe.stderr
    assert probe.returncode == 0, probe_output
    assert "exists=false" in probe.stdout
    assert "path_exists=false" in probe.stdout
    assert "is_dir=false" in probe.stdout
    assert f"stat={errno.ENOENT}" in probe.stdout
    assert f"lstat={errno.ENOENT}" in probe.stdout
    assert "outside=ok" in probe.stdout

    module = _write_module(
        tmp_path / "exists-modules",
        "test_exists_aborts_collection.py",
        "from pathlib import Path\n"
        f"p = Path({str(curriculum_file)!r})\n"
        "if not p.exists():\n"
        "    raise FileNotFoundError(p)\n"
        "\n"
        "def test_exists_aborts_collection() -> None:\n"
        "    pass\n",
    )
    _assert_eager_collection_fails([module], repo_root=fake, cwd=fake)
    assert curriculum_file.exists()
    assert os.path.exists(curriculum_file)
    assert os.stat(curriculum_file).st_size > 0


def _guarded_probe(
    source: str,
    *,
    cwd: Path,
    repo_root: Path,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``source`` in a child that has installed the collection guard."""
    env = os.environ.copy()
    env[FORCE_MISSING_TREES_ENV] = ",".join(_ABSENT_TREES)
    env[REPO_ROOT_ENV] = str(Path(os.path.abspath(repo_root)))
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_REPO_ROOT) if not prior else f"{_REPO_ROOT}{os.pathsep}{prior}"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_guard_blocks_symlink_created_after_absent_exists_check(tmp_path: Path) -> None:
    """An absent absolute path is not remembered as outside the trees.

    The child calls ``Path(alias).exists()`` while ``alias`` is missing, then
    creates that name as a symlink to a file inside ``curriculum/``. ``open``
    of the same path must fail in that process.
    """
    fake, curriculum_file = _curriculum_repo(tmp_path)
    alias = tmp_path / "absent-alias"
    assert not alias.exists()
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    completed = _guarded_probe(
        "import os\n"
        "from pathlib import Path\n"
        "import tests.sparse_collection_audit\n"
        "alias = os.environ['ALIAS']\n"
        "assert Path(alias).exists() is False\n"
        "print('exists=false')\n"
        "os.symlink(os.environ['INSIDE'], alias)\n"
        "try:\n"
        "    open(alias, encoding='utf-8').close()\n"
        "    print('open=visible')\n"
        "except FileNotFoundError as exc:\n"
        "    print(f'open={exc.errno}')\n",
        cwd=neutral,
        repo_root=fake,
        extra_env={"ALIAS": str(alias), "INSIDE": str(curriculum_file)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "exists=false" in completed.stdout
    assert f"open={errno.ENOENT}" in completed.stdout
    assert "open=visible" not in completed.stdout
    assert alias.read_text(encoding="utf-8") == "привіт\n"


def test_guard_blocks_symlink_repointed_into_a_tree(tmp_path: Path) -> None:
    """A symlink allowed on first resolution is hidden after it is re-pointed.

    The child resolves the link while it points at an outside file, then
    points the same path at a file inside ``curriculum/``. The second read
    must fail in that same process.
    """
    fake, curriculum_file = _curriculum_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "moving-link"
    link.symlink_to(outside)
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    completed = _guarded_probe(
        "import os\n"
        "from pathlib import Path\n"
        "import tests.sparse_collection_audit\n"
        "link = os.environ['LINK']\n"
        "first = Path(link).read_text(encoding='utf-8')\n"
        "assert first == 'outside\\n', first\n"
        "print('first=outside')\n"
        "os.remove(link)\n"
        "os.symlink(os.environ['INSIDE'], link)\n"
        "try:\n"
        "    Path(link).read_text(encoding='utf-8')\n"
        "    print('repoint=visible')\n"
        "except FileNotFoundError as exc:\n"
        "    print(f'repoint={exc.errno}')\n",
        cwd=neutral,
        repo_root=fake,
        extra_env={"LINK": str(link), "INSIDE": str(curriculum_file)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "first=outside" in completed.stdout
    assert f"repoint={errno.ENOENT}" in completed.stdout
    assert "repoint=visible" not in completed.stdout


def test_guard_blocks_proc_cwd_after_chdir(tmp_path: Path) -> None:
    """``/proc/self/cwd/...`` is resolved against the cwd of the call.

    The child first reads through ``/proc/self/cwd`` from an outside
    directory, then changes into the repo and reads a tree file through the
    same spelling.
    """
    fake, _curriculum_file = _curriculum_repo(tmp_path)
    start = tmp_path / "start"
    start.mkdir()
    (start / "outside.txt").write_text("outside\n", encoding="utf-8")
    completed = _guarded_probe(
        "import os\n"
        "from pathlib import Path\n"
        "import tests.sparse_collection_audit\n"
        "first = Path('/proc/self/cwd/outside.txt').read_text(encoding='utf-8')\n"
        "assert first == 'outside\\n', first\n"
        "print('first=outside')\n"
        "os.chdir(os.environ['REPO'])\n"
        "try:\n"
        "    Path('/proc/self/cwd/curriculum/lesson.txt').read_text(encoding='utf-8')\n"
        "    print('after=visible')\n"
        "except FileNotFoundError as exc:\n"
        "    print(f'after={exc.errno}')\n",
        cwd=start,
        repo_root=fake,
        extra_env={"REPO": str(fake)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "first=outside" in completed.stdout
    assert f"after={errno.ENOENT}" in completed.stdout
    assert "after=visible" not in completed.stdout


def test_guard_open_relative_to_dir_fd(tmp_path: Path) -> None:
    """``os.open(relative, dir_fd=...)`` follows that directory, not cwd.

    The tree directory fd is opened before the guard is installed: once the
    guard is active, opening that directory is already hidden. The same
    relative spelling must then be hidden for that fd and allowed for an
    outside directory fd. The outside fd is opened only after the tree fd is
    closed, so a reused descriptor number still has to be resolved again.
    ``os.stat`` of the resulting integer fd is left unguarded.
    """
    fake, curriculum_file = _curriculum_repo(tmp_path)
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "lesson.txt").write_text("outside\n", encoding="utf-8")
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    completed = _guarded_probe(
        "import os\n"
        "tree_fd = os.open(os.environ['TREE_DIR'], os.O_RDONLY)\n"
        "import tests.sparse_collection_audit\n"
        "try:\n"
        "    try:\n"
        "        leaked = os.open('lesson.txt', os.O_RDONLY, dir_fd=tree_fd)\n"
        "    except FileNotFoundError as exc:\n"
        "        print(f'tree={exc.errno}')\n"
        "    else:\n"
        "        os.close(leaked)\n"
        "        print('tree=visible')\n"
        "finally:\n"
        "    os.close(tree_fd)\n"
        "out_fd = os.open(os.environ['OUT_DIR'], os.O_RDONLY)\n"
        "try:\n"
        "    opened = os.open('lesson.txt', os.O_RDONLY, dir_fd=out_fd)\n"
        "    try:\n"
        "        os.stat(opened)\n"
        "        data = os.read(opened, 64)\n"
        "    finally:\n"
        "        os.close(opened)\n"
        "    print('outside=' + data.decode())\n"
        "finally:\n"
        "    os.close(out_fd)\n",
        cwd=neutral,
        repo_root=fake,
        extra_env={"TREE_DIR": str(curriculum_file.parent), "OUT_DIR": str(outside_dir)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert f"tree={errno.ENOENT}" in completed.stdout
    assert "tree=visible" not in completed.stdout
    assert "outside=outside\n" in completed.stdout


def test_guard_lstat_outside_symlink_returns_metadata(tmp_path: Path) -> None:
    """No-follow calls return an outside symlink, including ``/proc/self/cwd``.

    The child changes into the tree root, so ``/proc/self/cwd`` names that
    root. ``os.lstat`` and ``os.stat(..., follow_symlinks=False)`` must return
    the symlink's own metadata. An outside symlink whose target is inside the
    tree is likewise not hidden.
    """
    fake, curriculum_file = _curriculum_repo(tmp_path)
    outside_link = tmp_path / "into-tree-link"
    outside_link.symlink_to(curriculum_file)
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    completed = _guarded_probe(
        "import os\n"
        "import stat\n"
        "import tests.sparse_collection_audit\n"
        "os.chdir(os.environ['TREE_DIR'])\n"
        "for label, st in (\n"
        "    ('proc', os.lstat('/proc/self/cwd')),\n"
        "    ('proc_stat', os.stat('/proc/self/cwd', follow_symlinks=False)),\n"
        "    ('link', os.lstat(os.environ['OUTSIDE_LINK'])),\n"
        "):\n"
        "    print(label + '=' + ('symlink' if stat.S_ISLNK(st.st_mode) else 'other'))\n",
        cwd=neutral,
        repo_root=fake,
        extra_env={"TREE_DIR": str(curriculum_file.parent), "OUTSIDE_LINK": str(outside_link)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "proc=symlink" in completed.stdout
    assert "proc_stat=symlink" in completed.stdout
    assert "link=symlink" in completed.stdout


def test_guarded_open_without_mode_matches_umask(tmp_path: Path) -> None:
    """A create that omits mode keeps ``os.open``'s own default.

    The child sets one umask, creates a file with the unguarded ``os.open``
    before the hook is installed, then creates another with the guarded
    ``os.open`` and no mode argument. Both permission masks must match
    ``0o777 & ~umask``.
    """
    fake, _curriculum_file = _curriculum_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    completed = _guarded_probe(
        "import os\n"
        "import stat\n"
        "os.umask(0o027)\n"
        "plain = os.path.join(os.environ['OUT_DIR'], 'plain')\n"
        "fd = os.open(plain, os.O_CREAT | os.O_WRONLY | os.O_EXCL)\n"
        "os.close(fd)\n"
        "before = stat.S_IMODE(os.stat(plain).st_mode)\n"
        "import tests.sparse_collection_audit\n"
        "guarded = os.path.join(os.environ['OUT_DIR'], 'guarded')\n"
        "fd = os.open(guarded, os.O_CREAT | os.O_WRONLY | os.O_EXCL)\n"
        "os.close(fd)\n"
        "after = stat.S_IMODE(os.stat(guarded).st_mode)\n"
        "print(f'before={before:o}')\n"
        "print(f'after={after:o}')\n",
        cwd=outside,
        repo_root=fake,
        extra_env={"OUT_DIR": str(outside)},
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "before=750" in completed.stdout
    assert "after=750" in completed.stdout
