"""Pin the stripped-flavor import contract (#4444 spawn guard, #4931 fallout).

The delegate worker and build entrypoints put only ``scripts/`` on sys.path
and import shared modules WITHOUT the ``scripts.`` prefix (e.g.
``guardrails.worktree_containment``, ``path_safety``, ``audit.*``). A hard
``from scripts...`` import inside any of those modules breaks that flavor —
which broke every write-capable dispatch spawn (fail-closed refusal in
``agent_runtime.runner._ensure_write_cwd_isolated``) after the #4931
relocation of ``git_context``/``release_layout`` into ``scripts/common/``.

These tests import the stripped flavors in a subprocess whose sys.path
contains ONLY the stdlib/site-packages and ``scripts/`` — exactly the worker
environment — so a future hard ``scripts.*`` import fails here first.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

STRIPPED_MODULES = (
    "guardrails.worktree_containment",
    "path_safety",
    "audit.decision_lineage",
    "common.git_context",
    "common.release_layout",
)


@pytest.mark.parametrize("module_name", STRIPPED_MODULES)
def test_module_imports_with_only_scripts_on_sys_path(module_name: str) -> None:
    probe = (
        "import sys\n"
        # Drop the repo root and any cwd-derived entries; keep stdlib AND
        # site-packages (the venv lives under the repo, so filter by name).
        "sys.path = [p for p in sys.path if p and ('learn-ukrainian' not in p or 'site-packages' in p)]\n"
        f"sys.path.insert(0, {str(SCRIPTS_DIR)!r})\n"
        f"import importlib; importlib.import_module({module_name!r})\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd="/",  # never let the repo-root cwd leak onto sys.path
        timeout=30,
    )
    assert result.returncode == 0, (
        f"stripped-flavor import of {module_name!r} failed — this breaks the "
        f"delegate worker's write-capable spawn guard (fail-closed refusal):\n"
        f"{result.stderr}"
    )
    assert result.stdout.strip() == "OK"
