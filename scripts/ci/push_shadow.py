"""Report importer closure for a push, without authorizing or blocking it (#10033)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

from scripts.ci.components import python_sources, scan_imports


def selection(root: Path, changed: list[str]) -> dict:
    """Reuse the conservative dependency scanner and retain unresolved edges."""
    sources = python_sources(root)
    graph = scan_imports(sources)
    reverse = defaultdict(set)
    for importer, dependency in graph["file_edges"]:
        reverse[dependency].add(importer)
    visited = set(changed)
    pending = deque(changed)
    while pending:
        for importer in reverse[pending.popleft()]:
            if importer not in visited:
                visited.add(importer)
                pending.append(importer)
    tests = sorted(p for p in sources if p.startswith("tests/") and Path(p).name.startswith("test_"))
    unresolved = graph["unresolved_edges"]
    return {
        "schema_version": 1, "mode": "shadow", "status": "recorded",
        "closure_tests": sorted(set(tests) & visited),
        "selected_tests": tests if unresolved else sorted(set(tests) & visited),
        "unresolved_dependencies": unresolved, "full_fallback": bool(unresolved),
    }


if __name__ == "__main__":
    # Internal harness IPC; stdin holds only repository-relative changed paths.
    print(json.dumps(selection(Path.cwd(), json.load(sys.stdin))))
