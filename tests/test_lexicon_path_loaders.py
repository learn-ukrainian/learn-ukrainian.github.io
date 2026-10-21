"""Load path-imported lexicon modules with the repository absent from sys.path.

The frontend search-index build executes ``scripts/audit/generate_search_index.py``
as a file. That process does not put the repository root on ``sys.path``.
``_load_helper_module`` then loads helpers by file path. A module-level
``scripts.*`` import fails in that process.

The reader fallback may run only for that missing top-level package. An import
failure raised while ``readonly_sqlite`` initializes must propagate for both
the package import and the direct file load.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Changed lexicon modules this tree loads by file path, and the loader that does it.
# scripts/audit/generate_search_index.py:105 _load_helper_module
#   called at scripts/audit/generate_search_index.py:129
PATH_LOADED = ("scripts/lexicon/heritage_classifier.py",)
SEARCH_INDEX_LOADER = "scripts/audit/generate_search_index.py"
_IMPORT_ERROR = "reader initialization failed"
_OTHER_MODULE = "missing_reader_dependency"


class _ReaderInitLoader(importlib.abc.Loader):
    """Fail while ``scripts.lib.readonly_sqlite`` itself is initializing."""

    def __init__(self, kind: str) -> None:
        self.kind = kind

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if self.kind == "import-error":
            raise ImportError(_IMPORT_ERROR)
        if self.kind == "other-module":
            raise ModuleNotFoundError(f"No module named {_OTHER_MODULE!r}", name=_OTHER_MODULE)
        raise RuntimeError(self.kind)


class _ReaderInitFinder(importlib.abc.MetaPathFinder):
    """Raise from ``readonly_sqlite`` initialization.

    File loads have no ``scripts`` package. Synthesizing the parent packages
    lets the leaf module initialize and fail, which is the condition the
    fallback must not hide. ``lib.readonly_sqlite`` stays the real module, so
    a broad ``except ImportError`` would still succeed.
    """

    def __init__(self, kind: str, *, synthesize_parents: bool) -> None:
        self.kind = kind
        self.synthesize_parents = synthesize_parents

    def find_spec(self, fullname, path, target=None):
        if self.synthesize_parents and fullname in {"scripts", "scripts.lib"}:
            spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = []
            return spec
        if fullname == "scripts.lib.readonly_sqlite":
            return importlib.machinery.ModuleSpec(fullname, _ReaderInitLoader(self.kind))
        return None


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _drop_repo(root: Path) -> None:
    """Remove the repository so a file load cannot see the ``scripts`` package."""
    cleaned: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        resolved = Path(entry).resolve()
        if resolved == root or root in resolved.parents:
            continue
        cleaned.append(entry)
    sys.path[:] = cleaned


def _load_heritage_file(root: Path):
    _drop_repo(root)
    target = root / "scripts" / "lexicon" / "heritage_classifier.py"
    spec = importlib.util.spec_from_file_location("_pathload_heritage_classifier", target)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_database(database: Path) -> None:
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE kept(id INTEGER)")
        connection.commit()
    finally:
        connection.close()


def _opened_database(opener, database: Path) -> Path:
    connection = opener(database)
    try:
        row = connection.execute("PRAGMA database_list").fetchone()
    finally:
        connection.close()
    if row is None or not row[2]:
        raise RuntimeError(f"no database file for {database}")
    return Path(row[2]).resolve()


def _load_on_clean_path(repo: str, *relative_paths: str) -> None:
    """Import each path with spec_from_file_location after dropping the repo from sys.path."""
    root = Path(repo).resolve()
    _drop_repo(root)

    for relative in relative_paths:
        target = root / relative
        # A previous helper may have put scripts/ back on sys.path.
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


def _expected_failure(kind: str) -> str:
    if kind == "import-error":
        return _IMPORT_ERROR
    if kind == "other-module":
        return f"No module named {_OTHER_MODULE!r}"
    raise SystemExit(f"unknown kind {kind}")


def _assert_init_failure(kind: str, mode: str, repo: str) -> None:
    sys.meta_path.insert(0, _ReaderInitFinder(kind, synthesize_parents=mode == "file"))
    root = Path(repo).resolve()
    expected = _expected_failure(kind)
    try:
        if mode == "package":
            sys.path.insert(0, str(root))
            import scripts.lexicon.heritage_classifier  # noqa: F401
        elif mode == "file":
            _load_heritage_file(root)
        else:
            raise SystemExit(f"unknown mode {mode}")
    except ImportError as exc:
        if str(exc) != expected or (kind == "other-module" and exc.name != _OTHER_MODULE):
            raise SystemExit(f"{mode} {kind} raised {type(exc).__name__} name={exc.name!r}: {exc}") from exc
    else:
        raise SystemExit(f"{mode} {kind} swallowed {expected}")
    print("propagated")


def _assert_opened_path(mode: str, repo: str, database: str) -> None:
    root = Path(repo).resolve()
    db = Path(database)
    if mode == "package":
        sys.path.insert(0, str(root))
        from scripts.lexicon.heritage_classifier import _open_readonly

        opener = _open_readonly
        expected_module = "scripts.lib.readonly_sqlite"
    elif mode == "file":
        opener = _load_heritage_file(root)._open_readonly
        expected_module = "lib.readonly_sqlite"
    else:
        raise SystemExit(f"unknown mode {mode}")
    if opener.__module__ != expected_module:
        raise SystemExit(f"{mode} imported {opener.__module__}, expected {expected_module}")
    opened = _opened_database(opener, db)
    if opened != db.resolve():
        raise SystemExit(f"{mode} opened {opened}, expected {db.resolve()}")
    print(opened)


def test_package_import_uses_scripts_package_reader(tmp_path: Path) -> None:
    from scripts.lexicon.heritage_classifier import (
        _open_readonly,
        resolve_usage_label,
        usage_source_records,
    )

    database = tmp_path / "reader.db"
    _make_database(database)
    assert _open_readonly.__module__ == "scripts.lib.readonly_sqlite"
    assert callable(resolve_usage_label)
    assert callable(usage_source_records)
    assert _opened_database(_open_readonly, database) == database.resolve()


def test_path_loaded_lexicon_modules_import_without_repo_on_sys_path() -> None:
    result = _run("path-load", str(REPO), *PATH_LOADED, SEARCH_INDEX_LOADER)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip() == "ok"


def test_reader_initialization_error_propagates_for_package_and_file_load() -> None:
    for kind in ("import-error", "other-module"):
        for mode in ("package", "file"):
            result = _run("init-failure", kind, mode, str(REPO))
            assert result.returncode == 0, result.stderr or result.stdout
            assert result.stdout.strip() == "propagated"


def test_file_load_opens_the_given_database(tmp_path: Path) -> None:
    database = tmp_path / "reader.db"
    _make_database(database)
    result = _run("open-path", "file", str(REPO), str(database))
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip() == str(database.resolve())


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "path-load":
        _load_on_clean_path(sys.argv[2], *sys.argv[3:])
    elif command == "init-failure":
        _assert_init_failure(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "open-path":
        _assert_opened_path(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(f"unknown command {command}")
