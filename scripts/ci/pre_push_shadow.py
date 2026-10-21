"""Select the pytest files a pre-push range affects, by importer closure (#10033, #11207).

The pre-push gate blocks on these files together with the changed test files;
CI still runs the full suite and remains the merge gate.  A test file is
affected when it reaches a changed path through the static load graph that
``components.scan_imports`` proves: Python imports (with their parent
packages), literal ``importlib``/``runpy`` loads, literal file reads and literal
Python subprocesses.  A changed ``conftest.py`` affects every test file under
its directory.  A change to a file pytest loads for every test file affects
every test file: the pytest configuration, the root and ``tests/conftest.py``,
and the plugins ``addopts`` loads with ``-p``.  The answer lists the
test files nearest first (by hop count, then path).

A deleted path is no longer in the tree, so the tests that import it are found
through the import graph of the range's base commit (``--base``), whose edges
join the head's; the same configuration and conftest rules apply to it.  Without
that base graph a deleted path is an error, never an empty selection.  Only base
files that can hold an edge to a deleted path are parsed (``may_reach``).

Two kinds of reach are not followed, and CI's full suite covers them.  Edges
the scanner cannot prove (a computed path, a shell command, a ``sys.path``
edit): treating each as "could read anything" selects almost every test file
on every push.  A module reached only through what a conftest imports: the
root ``tests/conftest.py`` imports a chain that reaches most of ``scripts/``,
so following it would again select every test file, while any selected test
already loads that conftest.  The same holds for what a ``-p`` plugin imports.  The selection is the proven importer closure,
not a certificate that nothing else is affected.  Any failure of this command
is the gate's to handle: it falls back to its conservative set and records why.

The module keeps its historical name; the gate and its tests invoke it by it.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import tomllib
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

from scripts.ci import components

SCHEMA = "pre-push-selection.v1"
# Files pytest reads for every test it collects in this repository.
# ``tests/conftest.py`` is the session-wide conftest of the configured ``testpaths``.
PYTEST_CONFIG_FILES = ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", "conftest.py", "tests/conftest.py")
PYPROJECT = "pyproject.toml"


def is_test_file(path: str) -> bool:
    """The gate's own test-file shape: ``tests/**/test_*.py``."""
    parts = PurePosixPath(path).parts
    return len(parts) >= 2 and parts[0] == "tests" and parts[-1].startswith("test_") and parts[-1].endswith(".py")


def plugin_files(pyproject: bytes, tracked: set[str]) -> list[str]:
    """Resolve the ``-p`` plugins in ``addopts`` to tracked files on the configured ``pythonpath``."""
    try:
        options = tomllib.loads(pyproject.decode("utf-8"))["tool"]["pytest"]["ini_options"]
    except (KeyError, TypeError, UnicodeError, tomllib.TOMLDecodeError):
        return []
    addopts = options.get("addopts", "")
    tokens = shlex.split(addopts) if isinstance(addopts, str) else [str(token) for token in addopts]
    names = [tokens[index + 1] for index, token in enumerate(tokens[:-1]) if token == "-p"]
    names += [token[2:] for token in tokens if token.startswith("-p") and len(token) > 2]
    roots = ["", *(f"{entry.rstrip('/')}/" for entry in options.get("pythonpath", []) if isinstance(entry, str))]
    found = []
    for name in names:
        module = name.replace(".", "/")
        found += [
            path for root in roots for path in (f"{root}{module}.py", f"{root}{module}/__init__.py") if path in tracked
        ]
    return sorted(set(found))


def importer_distances(paths: Iterable[str], file_edges: Iterable[Sequence[str]]) -> dict[str, int]:
    """Every file that reaches one of ``paths`` through proven edges, with its hop count (the paths are 0)."""
    reverse: dict[str, set[str]] = {}
    for importer, target in file_edges:
        reverse.setdefault(target, set()).add(importer)
    distances = dict.fromkeys(paths, 0)
    layer = sorted(distances)
    while layer:
        following = []
        for target in layer:
            for importer in sorted(reverse.get(target, ())):
                if importer not in distances:
                    distances[importer] = distances[target] + 1
                    following.append(importer)
        layer = following
    return distances


def select(
    paths: Sequence[str],
    graph: dict,
    tracked: Sequence[str],
    plugins: Sequence[str] = (),
    *,
    deleted: Sequence[str] = (),
    base_graph: dict | None = None,
) -> dict[str, object]:
    """The affected test files for ``paths`` and ``deleted``, nearest first: by hop count, then path.

    ``deleted`` paths reach their importers through ``base_graph``, the import graph of the commit they
    were deleted from; its edges join ``graph``'s. The gate runs a prefix of this order when the whole
    selection exceeds its cost cap, so the tests closest to the change are the last to be deferred to CI.
    """
    if deleted and base_graph is None:
        raise ValueError("deleted paths need the base import graph")
    base_edges = base_graph["file_edges"] if base_graph is not None else []
    tests = sorted(path for path in tracked if is_test_file(path))
    touched = [*paths, *deleted]
    distances = importer_distances(touched, [*graph["file_edges"], *base_edges])
    reasons = sorted(
        {"pytest_configuration" for path in touched if path in PYTEST_CONFIG_FILES}
        | {"pytest_plugin" for path in touched if path in plugins}
    )
    # A changed conftest.py changes the fixtures and hooks of every test file under its directory.
    for conftest in sorted(path for path in touched if PurePosixPath(path).name == "conftest.py"):
        scope = f"{PurePosixPath(conftest).parent.as_posix()}/"
        for test in tests:
            if test.startswith(scope):
                distances[test] = min(distances.get(test, 1), 1)
    selected = tests if reasons else [test for test in tests if test in distances]
    nearest = len(distances) + 1  # after every reached file, for tests only a configuration change selects
    return {
        "schema": SCHEMA,
        "scope": "all_tests" if reasons else "importer_closure",
        "all_tests_reasons": reasons,
        "changed_paths": len(paths),
        "deleted_paths": len(deleted),
        "python_files": graph["python_files"],
        "import_edges": len(graph["file_edges"]),
        "base_import_edges": len(base_edges),
        "unfollowed_edges": len(graph["unresolved_edges"]),
        "selected_tests": sorted(selected, key=lambda test: (distances.get(test, nearest), test)),
    }


def commit_blobs(root: Path, commit: str) -> dict[str, str]:
    """Every file of ``commit`` with its blob id; an unknown commit is an error."""
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", commit], cwd=root, check=True, capture_output=True, timeout=30
    ).stdout
    blobs = {}
    for entry in listing.decode("utf-8", errors="surrogateescape").split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            _mode, kind, sha = meta.split()
            if kind == "blob":
                blobs[path] = sha
    return blobs


def may_reach(path: str, source: bytes, deleted: Sequence[str]) -> bool:
    """Whether the base file ``path`` can hold a proven edge to a deleted path.

    Every proven edge names its target in the importer's own text: a module import or literal load ends
    in the target's module name, a literal read or file load in its file name. The exceptions are the
    package edges a relative import adds (``from . import x`` reaches ``__init__.py`` without naming it),
    so for a deleted ``__init__.py`` every file under its package is kept, with every file naming the
    package. The deleted files themselves are kept. Only edges to deleted paths come from the base graph;
    the head graph supplies the rest of the closure.
    """
    for target in deleted:
        pure = PurePosixPath(target)
        if path == target:
            return True
        if pure.name == "__init__.py":
            package = pure.parent.as_posix()
            if path.startswith(f"{package}/") or pure.parent.name.encode() in source:
                return True
        elif pure.name.encode() in source or (pure.suffix == ".py" and pure.stem.encode() in source):
            return True
    return False


def selection(
    paths: Sequence[str], root: Path = components.ROOT, *, deleted: Sequence[str] = (), base: str | None = None
) -> dict[str, object]:
    """Scan the indexed tree at ``root`` and select for ``paths``, and for ``deleted`` through ``base``."""
    base_graph = None
    base_known: set[str] = set()
    if deleted:
        if not base:
            raise ValueError("deleted paths need the base commit")
        blobs = commit_blobs(root, base)
        base_known = set(blobs)
        python = tuple((path, sha) for path, sha in sorted(blobs.items()) if path.endswith(".py"))
        sources = components.indexed_python_sources(str(root), python, ())
        # Parsing is the cost; reading the blobs is not. Module resolution needs every package.
        kept = {
            path: source
            for path, source in sources.items()
            if path.endswith("/__init__.py") or may_reach(path, source, deleted)
        }
        base_graph = components.scan_imports(kept, base_known)
    tracked = components.tracked_paths(root)
    known = set(tracked)
    graph = components.scan_imports(components.python_sources(root), known)
    pyproject = (root / PYPROJECT).read_bytes() if PYPROJECT in known else b""
    # A deleted plugin file that the configuration still loads resolves against the base tree.
    plugins = plugin_files(pyproject, known | base_known)
    return select(paths, graph, tracked, plugins, deleted=deleted, base_graph=base_graph)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog="Example:\n  .venv/bin/python -m scripts.ci.pre_push_shadow --base origin/main --deleted scripts/old.py "
        "--paths scripts/ci/components.py\n"
        "Output: one JSON object on stdout (schema pre-push-selection.v1). Exit codes: 0 selected; "
        "non-zero on any error, which the gate treats as an unavailable selector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--paths", nargs="*", default=[], help="repository-relative changed paths; default: none")
    parser.add_argument("--deleted", nargs="*", default=[], help="repository-relative deleted paths; default: none")
    parser.add_argument("--base", help="commit the deleted paths are read from; required with --deleted")
    arguments = parser.parse_args(argv)
    print(json.dumps(selection(arguments.paths, deleted=arguments.deleted, base=arguments.base), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
