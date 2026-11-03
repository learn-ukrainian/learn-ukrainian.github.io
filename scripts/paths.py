"""Canonical path resolution for all scripts, regardless of directory depth.

Usage in any script:
    from paths import PROJECT_ROOT, SCRIPTS_DIR
    # or
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from paths import PROJECT_ROOT, SCRIPTS_DIR

``PROJECT_ROOT`` is the runtime root: the checkout this code runs from, a dispatch
worktree included, so curriculum paths below stay inside the worktree being edited. It
is deliberately not the configured primary checkout. The primary checkout, GitHub slug,
state root, rules directory and interpreter come from the one machinery configuration in
``scripts/common/repo_root.py`` (``machinery_roots``).
"""
from pathlib import Path

# scripts/ directory — always the directory containing this file
SCRIPTS_DIR = Path(__file__).resolve().parent

# Project root — parent of scripts/
PROJECT_ROOT = SCRIPTS_DIR.parent

# Common paths
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
CURRICULUM_L2 = CURRICULUM_DIR / "l2-uk-en"
STARLIGHT_DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
DOCS_DIR = PROJECT_ROOT / "docs"
