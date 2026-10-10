#!/usr/bin/env python3
"""Fail when a test adds a wall-clock sleep outside the frozen baseline.

A fixed ``time.sleep`` is how timing tests flake and how the next test copies
that flake. New waits go through ``tests/wait_helpers.py``, which sleeps only
until a condition is true. The baseline is a ceiling: a file may lose sleeps
without a baseline edit, and the ceiling itself may be lowered later. A higher
count fails. ``time.sleep``, ``import time as t`` then ``t.sleep``, and
``from time import sleep`` are the same call.

Examples:
  .venv/bin/python scripts/audit/lint_timing_sleep.py

Outputs: one path and the current versus allowed count per extra sleep.
Writes nothing.
Exit codes: 0 when no count grew, 1 when a count grew or a new file sleeps.
Related: tests/wait_helpers.py, tests/timing_sleep_baseline.txt.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BASELINE = _ROOT / "tests" / "timing_sleep_baseline.txt"
_ALLOWED = "tests/wait_helpers.py"


def _sleep_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Module aliases for ``time``, and names bound to ``time.sleep``."""
    modules: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "time":
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "time":
            for alias in node.names:
                if alias.name == "sleep":
                    calls.add(alias.asname or alias.name)
    return modules, calls


def _is_time_sleep(node: ast.AST, modules: set[str], calls: set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in calls
    if not isinstance(func, ast.Attribute) or func.attr != "sleep":
        return False
    return isinstance(func.value, ast.Name) and func.value.id in modules


def sleep_counts(root: Path | None = None) -> dict[str, int]:
    """Return ``time.sleep`` call counts for test files other than the wait helper."""
    base = _ROOT if root is None else root
    counts: dict[str, int] = {}
    tests = base / "tests"
    if not tests.is_dir():
        return counts
    for path in tests.rglob("*.py"):
        rel = path.relative_to(base).as_posix()
        if rel == _ALLOWED:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue
        modules, calls = _sleep_bindings(tree)
        count = sum(1 for node in ast.walk(tree) if _is_time_sleep(node, modules, calls))
        if count:
            counts[rel] = count
    return counts


def read_baseline(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rel, raw = line.split("\t")
        counts[rel] = int(raw)
    return counts


def drift(current: dict[str, int], baseline: dict[str, int]) -> list[str]:
    """Return rows where a file sleeps more than the baseline allows, or is new.

    A smaller count is clean. The baseline file can be lowered to the new
    count; this lint does not require that edit.
    """
    rows: list[str] = []
    for rel in sorted(set(current) | set(baseline)):
        now = current.get(rel, 0)
        allowed = baseline.get(rel, 0)
        if now > allowed:
            rows.append(f"{rel} sleeps={now} allowed={allowed}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(sys.argv[1:] if argv is None else argv)
    rows = drift(sleep_counts(), read_baseline(_BASELINE))
    if rows:
        print("\n".join(rows))
        print(
            "timing-sleep lint: wait with tests.wait_helpers. Do not add time.sleep.",
            file=sys.stderr,
        )
        return 1
    print("timing-sleep lint clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
