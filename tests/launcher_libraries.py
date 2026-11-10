"""Tracked library inventory for fixtures that run real launcher entry points."""

from __future__ import annotations

import base64
import functools
import hashlib
import importlib.metadata
import importlib.resources
import json
import os
import subprocess
import sys
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from tests.helpers import machinery_package

# The released machinery distribution and the package it installs.
INSTALLED_DISTRIBUTION = "lu-machinery"
INSTALLED_PACKAGE = "lu_machinery"


@dataclass(frozen=True)
class InstalledMachinery:
    """The installed machinery release: its package directory and the files its RECORD lists."""

    name: str
    version: str
    directory: Path
    files: tuple[PurePosixPath, ...]


@functools.cache
def installed_machinery() -> InstalledMachinery:
    """Locate the installed release and prove its package files are the recorded release bytes.

    The package must be the one the import system resolves, inside the distribution's own
    install location, so a checkout or path entry cannot stand in for it. Every package file
    the distribution's RECORD lists must exist with its recorded SHA-256; an edited or
    partially replaced installation fails here instead of being exercised as the release.
    """
    distribution = importlib.metadata.distribution(INSTALLED_DISTRIBUTION)
    directory = Path(os.fspath(importlib.resources.files(INSTALLED_PACKAGE)))
    located = Path(os.fspath(distribution.locate_file(INSTALLED_PACKAGE)))
    assert directory.resolve() == located.resolve(), (directory, located)
    direct_url = distribution.read_text("direct_url.json")
    if direct_url:
        assert not json.loads(direct_url).get("dir_info", {}).get("editable"), "editable install is not a release"
    files = []
    for entry in distribution.files or ():
        if entry.parts[:1] != (INSTALLED_PACKAGE,):
            continue
        assert entry.hash is not None and entry.hash.mode == "sha256", entry
        relative = PurePosixPath(*entry.parts[1:])
        digest = hashlib.sha256((directory / relative).read_bytes()).digest()
        assert base64.urlsafe_b64encode(digest).rstrip(b"=").decode() == entry.hash.value, relative
        files.append(relative)
    assert PurePosixPath("lib/launcher_core.sh") in files, "release ships no launcher library"
    return InstalledMachinery(INSTALLED_PACKAGE, distribution.version, directory, tuple(sorted(files)))


def freeze_product_wrapper(source: Path, destination: Path, package: str) -> None:
    """Copy product wrapper ``source`` as fixture data, its launcher core taken from ``package``.

    The source line is the only change, and the wrapper may name no other machinery path.
    """
    body = source.read_text(encoding="utf-8")
    old = f'"$ROOT/{machinery_package()}/lib/launcher_core.sh"'
    code = [line for line in body.replace(old, "").splitlines() if not line.lstrip().startswith("#")]
    assert body.count(old) == 1 and not [line for line in code if f"{machinery_package()}/" in line], source
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    destination.write_text(body.replace(old, f'"$ROOT/{package}/lib/launcher_core.sh"'), encoding="utf-8")
    destination.chmod(0o755)


def link_installed_machinery(destination: Path, replaced: Collection[str] = ()) -> InstalledMachinery:
    """Mirror the installed package at ``destination``: real directories, file symlinks into the release.

    Shell libraries resolve their helpers from their own directory, so a fixture that must
    replace a boundary helper gives them a directory of their own; every other file is a
    symlink whose target is the recorded release file, never a copy. ``replaced`` names the
    package-relative files left absent for the caller to write. Writing through any other
    path in the mirror would modify the installed release, so callers unlink before writing.
    """
    release = installed_machinery()
    for relative in release.files:
        if relative.as_posix() in replaced:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(release.directory / relative)
    return release


def launcher_library_files(repo: Path) -> tuple[Path, ...]:
    """Include every tracked library, including future additions and package data."""
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{machinery_package()}/lib"],
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
package = sys.argv[2]
opened = set()

def record(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if path.endswith(".pyc") and Path(path).parent.name == "__pycache__":
            path = importlib.util.source_from_cache(path)
        opened.add(path)

sys.addaudithook(record)
script = root / package / "review" / "model_catalog.py"
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
            code = 0 if exc.code in (None, 0) else exc.code
            # Retired Kimi and GLM aliases still open the catalog; include their
            # refusal import closures. Every active command must exit 0.
            if code != 0 and not (
                arguments in (["--resolve-kimi-model", "k3"], ["--resolve-glm-model", "glm"]) and code == 2
            ):
                raise
# The launcher now executes the shared credential policy rather than only
# printing intermediate drop names. Include that real import closure too.
if (root / package / "agent_runtime" / "env_sanitize.py").is_file():
    sys.path[:0] = [str(root), str(root / package)]
    child_credential_env = importlib.import_module("agent_runtime.env_sanitize").child_credential_env
    child_credential_env({"HOME": "synthetic-stored-login"}, "kimi")
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
        [sys.executable, "-I", "-c", _CATALOG_IMPORT_PROBE, str(repo.resolve()), machinery_package()],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.split("\0")
    )
    return tuple(Path(raw) for raw in json.loads(probe.stdout) if raw in tracked)
