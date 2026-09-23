"""Collection stays error-free when default sparse trees are absent.

The check copies a representative subset's repo via hardlinks, deletes
``curriculum/``, ``wiki/``, ``data/projects/``, and ``data/lexicon/``, and
collects the modules that used to read those trees at import time.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ABSENT_TREES = ("curriculum", "wiki", "data/projects", "data/lexicon")
_REPRESENTATIVE_MODULES = (
    "tests/curriculum/test_plan_validate_cross.py",
    "tests/projects/open_model_data/test_a10_pilot_review_gate.py",
    "tests/projects/open_model_data/test_a2_resolved_schema.py",
    "tests/projects/open_model_data/test_v4_active_release.py",
    "tests/test_open_model_phase3_p2_contracts.py",
    "tests/test_open_model_phase3_pravopys_evaluation_context.py",
)


def _drop_tree(root: Path, relative: str) -> None:
    target = root.joinpath(*relative.split("/"))
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)


def test_representative_modules_collect_when_sparse_trees_are_absent(tmp_path: Path) -> None:
    copy_root = tmp_path / "repo"
    copy_root.mkdir()
    subprocess.run(["cp", "-al", f"{_REPO_ROOT}/.", str(copy_root)], check=True)
    for relative in _ABSENT_TREES:
        _drop_tree(copy_root, relative)
        assert not (copy_root / relative).exists()

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *_REPRESENTATIVE_MODULES,
            "--collect-only",
            "-q",
            "--tb=line",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        cwd=copy_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "errors during collection" not in output
    assert "Interrupted:" not in output
