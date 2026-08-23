"""Process-local source/AST cache for repo-wide static test guards."""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path


@cache
def read_test_source(path: Path) -> str:
    """Read one static-scan source file once per pytest process."""
    return path.read_text(encoding="utf-8")


@cache
def parse_test_source(path: Path) -> ast.Module:
    """Parse one static-scan source file once per pytest process."""
    return ast.parse(read_test_source(path), filename=str(path))
