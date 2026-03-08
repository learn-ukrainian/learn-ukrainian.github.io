"""Canonical path resolution for all scripts, regardless of directory depth.

Usage in any script:
    from paths import PROJECT_ROOT, SCRIPTS_DIR
    # or
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from paths import PROJECT_ROOT, SCRIPTS_DIR
"""
from pathlib import Path

# scripts/ directory — always the directory containing this file
SCRIPTS_DIR = Path(__file__).resolve().parent

# Project root — parent of scripts/
PROJECT_ROOT = SCRIPTS_DIR.parent

# Common paths
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
CURRICULUM_L2 = CURRICULUM_DIR / "l2-uk-en"
STARLIGHT_DOCS_DIR = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
DOCS_DIR = PROJECT_ROOT / "docs"
