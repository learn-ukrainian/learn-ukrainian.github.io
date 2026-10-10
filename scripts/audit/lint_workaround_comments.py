#!/usr/bin/env python3
"""Fail when scripts or tests contain the copy-bait word for a local bypass.

Agents copy the nearest comment. A comment that names a bypass becomes the
next implementation. The supported path belongs in the code. This lint reads Python and shell
under ``scripts/`` and ``tests/`` and exits 1 when that word appears.

Examples:
  .venv/bin/python scripts/audit/lint_workaround_comments.py

Outputs: repo-relative path and line on stdout. Writes nothing.
Exit codes: 0 when the trees are clean, 1 when the word appears.
Related: scripts/agent_runtime/adapters/gemini.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_TOKEN = "work" "around"
_PATTERN = re.compile(rf"\b{_TOKEN}s?\b", re.IGNORECASE)
_ROOTS = ("scripts", "tests")
_SKIP = {".venv", "__pycache__", "node_modules"}


def findings(root: Path | None = None) -> list[str]:
    """Return ``path:line`` hits under scripts and tests."""
    base = _ROOT if root is None else root
    hits: list[str] = []
    for name in _ROOTS:
        tree = base / name
        if not tree.is_dir():
            continue
        for pattern in ("*.py", "*.sh"):
            for path in tree.rglob(pattern):
                if any(part in _SKIP for part in path.parts):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                for number, line in enumerate(text.splitlines(), 1):
                    if _PATTERN.search(line):
                        hits.append(f"{path.relative_to(base).as_posix()}:{number}")
    return hits


def main(argv: list[str] | None = None) -> int:
    del argv
    hits = findings()
    if hits:
        print("\n".join(hits))
        print(f"bypass-note lint: {len(hits)} hit(s). Delete the bypass note.", file=sys.stderr)
        return 1
    print("bypass-note lint clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
