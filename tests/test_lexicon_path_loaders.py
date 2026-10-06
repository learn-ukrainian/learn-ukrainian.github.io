"""Load path-imported lexicon modules with the repository absent from sys.path.

The frontend search-index build executes ``scripts/audit/generate_search_index.py``
as a file. That process does not put the repository root on ``sys.path``.
``_load_helper_module`` then loads helpers by file path. A module-level
``scripts.*`` import fails in that process.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Changed lexicon modules this tree loads by file path, and the loader that does it.
# scripts/audit/generate_search_index.py:88 _load_helper_module
#   called at scripts/audit/generate_search_index.py:111
PATH_LOADED = ("scripts/lexicon/heritage_classifier.py",)
SEARCH_INDEX_LOADER = "scripts/audit/generate_search_index.py"


def _load_on_clean_path(repo: str, *relative_paths: str) -> None:
    """Import each path with spec_from_file_location after dropping the repo from sys.path."""
    import importlib.util
    from pathlib import Path

    root = Path(repo).resolve()
    cleaned: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        resolved = Path(entry).resolve()
        if resolved == root or root in resolved.parents:
            continue
        cleaned.append(entry)
    sys.path[:] = cleaned

    for relative in relative_paths:
        target = root / relative
        sys.path[:] = [entry for entry in sys.path if entry and Path(entry).resolve() != root / "scripts"]
        spec = importlib.util.spec_from_file_location(f"_pathload_{target.stem}", target)
        if spec is None or spec.loader is None:
            raise SystemExit(f"cannot load {relative}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if relative.endswith("heritage_classifier.py"):
            opener = module._open_readonly
            if opener.__module__ != "lib.readonly_sqlite":
                raise SystemExit(f"{relative} imported {opener.__module__}, expected lib.readonly_sqlite")
            if not callable(module.resolve_usage_label) or not callable(module.usage_source_records):
                raise SystemExit(f"{relative} did not finish initializing")
        if (
            relative.endswith("generate_search_index.py")
            and module._HERITAGE_CLASSIFIER._open_readonly.__module__ != "lib.readonly_sqlite"
        ):
            raise SystemExit("search-index loader did not path-load heritage_classifier")
    print("ok")


def test_path_loaded_lexicon_modules_import_without_repo_on_sys_path() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), str(REPO), *PATH_LOADED, SEARCH_INDEX_LOADER],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip() == "ok"


if __name__ == "__main__":
    _load_on_clean_path(sys.argv[1], *sys.argv[2:])
