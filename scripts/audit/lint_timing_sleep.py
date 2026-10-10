#!/usr/bin/env python3
"""Fail when a test adds a wall-clock sleep outside the frozen baseline.

A fixed ``time.sleep`` is how timing tests flake and how the next test copies
that flake. New waits go through ``tests/wait_helpers.py``, which sleeps only
until a condition is true. The baseline counts existing ``time.sleep`` calls
and may only shrink.

Examples:
  .venv/bin/python scripts/audit/lint_timing_sleep.py

Outputs: one path and the current versus allowed count per extra sleep.
Writes nothing.
Exit codes: 0 when the tree matches the baseline, 1 when a count grew or a
new file sleeps.
Related: tests/wait_helpers.py, tests/timing_sleep_baseline.txt.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BASELINE = _ROOT / "tests" / "timing_sleep_baseline.txt"
_ALLOWED = "tests/wait_helpers.py"


def _is_time_sleep(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    return node.func.attr == "sleep" and isinstance(node.func.value, ast.Name) and node.func.value.id == "time"


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
        except (OSError, SyntaxError):
            continue
        count = sum(1 for node in ast.walk(tree) if _is_time_sleep(node))
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
    """Return rows where a file sleeps more than the baseline allows, or is new."""
    rows: list[str] = []
    for rel in sorted(set(current) | set(baseline)):
        now = current.get(rel, 0)
        allowed = baseline.get(rel, 0)
        if now > allowed:
            rows.append(f"{rel} sleeps={now} allowed={allowed}")
        elif now < allowed:
            rows.append(f"{rel} sleeps={now} allowed={allowed} shrink-the-baseline")
    return rows


def main(argv: list[str] | None = None) -> int:
    del argv
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
