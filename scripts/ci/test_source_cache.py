"""Process-local source/AST cache for repo-wide static test guards."""

from __future__ import annotations

import ast
import os
from functools import cache
from pathlib import Path

FileIdentity = tuple[Path, int, int, int]


def _file_identity(path: Path) -> FileIdentity:
    """Return a cheap identity that changes when a path is replaced or edited."""
    resolved_path = path.resolve()
    stat = os.stat(resolved_path)
    return (resolved_path, stat.st_mtime_ns, stat.st_size, stat.st_ino)


@cache
def _read_test_source(identity: FileIdentity) -> str:
    """Read one source-file identity once per pytest process."""
    path = identity[0]
    return path.read_text(encoding="utf-8")


def read_test_source(path: Path) -> str:
    """Read static-scan source, reusing cache entries only for the same file."""
    return _read_test_source(_file_identity(path))


@cache
def _parse_test_source(identity: FileIdentity) -> ast.Module:
    """Parse one source-file identity once per pytest process."""
    path = identity[0]
    return ast.parse(_read_test_source(identity), filename=str(path))


def parse_test_source(path: Path) -> ast.Module:
    """Parse static-scan source using the matching read-cache identity."""
    return _parse_test_source(_file_identity(path))
