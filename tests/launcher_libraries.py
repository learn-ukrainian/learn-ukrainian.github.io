"""Tracked library inventory for fixtures that run real launcher entry points."""

from __future__ import annotations

import functools
import json
import subprocess
import sys
from pathlib import Path


def launcher_library_files(repo: Path) -> tuple[Path, ...]:
    """Include every tracked library, including future additions and package data."""
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "scripts/lib"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return tuple(Path(raw) for raw in tracked.stdout.split("\0") if raw)


_CATALOG_IMPORT_PROBE = r"""
import contextlib, importlib.util, io, json, os, runpy, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
opened = set()

def record(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if path.endswith(".pyc") and Path(path).parent.name == "__pycache__":
            path = importlib.util.source_from_cache(path)
        opened.add(path)

sys.addaudithook(record)
script = root / "scripts/review/model_catalog.py"
for arguments in (
    ["--check-retired-model", "gpt-6.1-sol"],
    ["--resolve-kimi-model", "k3"],
    ["--resolve-glm-model", "glm"],
    ["--resolve-role", "bounded_advisor"],
):
    sys.argv = [str(script), *arguments]
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            runpy.run_path(str(script), run_name="__main__")
        except SystemExit as exc:
            if exc.code != 0:
                raise
sources = set()
for raw in opened:
    path = Path(raw).resolve()
    if path.is_relative_to(root) and path.is_file():
        sources.add(str(path.relative_to(root)))
print(json.dumps(sorted(sources)))
"""


@functools.cache
def launcher_catalog_files(repo: Path) -> tuple[Path, ...]:
    """Measure the file-path catalog commands' import/data closure once per repo.

    Like the slot-registry sandbox probe, record opened source and bytecode files
    so dynamic imports and modules replacing their sys.modules entry are covered.
    Isolated mode prevents an ambient PYTHONPATH from hiding missing dependencies.
    Only tracked files are staged; opened Git metadata and local state stay out.
    """
    probe = subprocess.run(
        [sys.executable, "-I", "-c", _CATALOG_IMPORT_PROBE, str(repo.resolve())],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    tracked = set(subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo, capture_output=True, text=True,
        check=True, timeout=30,
    ).stdout.split("\0"))
    return tuple(Path(raw) for raw in json.loads(probe.stdout) if raw in tracked)
