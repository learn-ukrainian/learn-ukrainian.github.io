"""Run a product pre-commit entry point named in product data (#12504, step 4 S8).

The lesson-schema and Atlas lexicon-fingerprint hooks regenerate committed
files with product code. Machinery does not import that code. The product
names each hook's entry point in one data file,
``scripts/build/pre_commit_entry_points.v1.json``, and this module is the only
reader: it validates the file, imports the named module and calls the named
function with the recorded arguments.

The file is trusted because of where it is read from: the path is fixed
relative to this module, and no environment variable or flag redirects it.
Changing an entry point is a reviewed commit to that file.

Fail closed. :func:`load_entry_point` raises :class:`EntryPointError` when the
file is missing, a symlink, not a regular file or too large; is not strict
UTF-8 JSON (a duplicate key counts); has another schema, schema version or
origin; carries a missing or unknown field; or names a hook that is not
listed, an entry point outside ``scripts.<module>:<function>`` or an argument
that is not a string.

Example:
  .venv/bin/python -c "from scripts.pre_commit.product_entry import load_entry_point as l; print(l('lesson-schema-drift'))"
"""

from __future__ import annotations

import importlib
import json
import os
import re
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "learn-ukrainian.pre-commit-entry-points"
SCHEMA_VERSION = 1
ENTRY_POINTS_REL = "scripts/build/pre_commit_entry_points.v1.json"
ENTRY_POINTS_PATH = Path(__file__).resolve().parents[2] / ENTRY_POINTS_REL
MAX_BYTES = 16 * 1024

_TOP_FIELDS = frozenset({"schema", "schema_version", "origin", "entry_points"})
_ENTRY_FIELDS = frozenset({"entry_point", "argv"})
_IDENTIFIER = r"[a-z_][a-z0-9_]*"
_ENTRY_POINT_RE = re.compile(rf"(scripts(?:\.{_IDENTIFIER})+):({_IDENTIFIER})\Z")


class EntryPointError(ValueError):
    """The entry-point file or the requested hook refused."""


@dataclass(frozen=True)
class EntryPoint:
    module: str
    function: str
    argv: tuple[str, ...]


def _read(path: Path) -> Any:
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise EntryPointError(f"cannot read {path}: {exc.strerror}") from None
    if not stat.S_ISREG(info.st_mode):
        raise EntryPointError(f"{path} is not a regular file (symlinks are refused)")
    if info.st_size > MAX_BYTES:
        raise EntryPointError(f"{path} is larger than {MAX_BYTES} bytes")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise EntryPointError(f"cannot read {path}: {exc.strerror}") from None
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise EntryPointError(f"{path} changed while it was opened")
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise EntryPointError(f"{path} is larger than {MAX_BYTES} bytes")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise EntryPointError(f"{path} repeats a key")
        return dict(pairs)

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EntryPointError(f"{path} is not UTF-8 JSON: {exc}") from None


def _fields(value: Any, expected: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.keys() != expected:
        raise EntryPointError(f"{where} must have exactly the fields {', '.join(sorted(expected))}")
    return value


def load_entry_point(hook_id: str, path: Path = ENTRY_POINTS_PATH) -> EntryPoint:
    """Return the validated entry point for one hook id, or raise :class:`EntryPointError`."""
    document = _fields(_read(path), _TOP_FIELDS, "entry-point file")
    if document["schema"] != SCHEMA or type(document["schema_version"]) is not int:
        raise EntryPointError(f"schema must be {SCHEMA!r} with an integer schema_version")
    if document["schema_version"] != SCHEMA_VERSION:
        raise EntryPointError(f"schema_version {document['schema_version']} is not {SCHEMA_VERSION}")
    if document["origin"] != ENTRY_POINTS_REL or path.name != Path(ENTRY_POINTS_REL).name:
        raise EntryPointError(f"origin and file name must be {ENTRY_POINTS_REL!r}")
    entries = document["entry_points"]
    if not isinstance(entries, dict) or hook_id not in entries:
        raise EntryPointError(f"no entry point for hook {hook_id!r}")
    entry = _fields(entries[hook_id], _ENTRY_FIELDS, f"entry point {hook_id!r}")
    match = _ENTRY_POINT_RE.match(entry["entry_point"]) if isinstance(entry["entry_point"], str) else None
    if match is None:
        raise EntryPointError(f"entry point {hook_id!r} must be 'scripts.<module>:<function>'")
    argv = entry["argv"]
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        raise EntryPointError(f"argv for {hook_id!r} must be a list of strings")
    return EntryPoint(module=match[1], function=match[2], argv=tuple(argv))


def run_entry_point(hook_id: str) -> int:
    """Import and call the product entry point for ``hook_id``; return its exit code."""
    entry = load_entry_point(hook_id)
    function: Callable[[list[str]], int] = getattr(importlib.import_module(entry.module), entry.function)
    return function(list(entry.argv))
