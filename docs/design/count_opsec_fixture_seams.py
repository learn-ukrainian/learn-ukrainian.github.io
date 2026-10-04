"""Record the seams the live OPSEC-sweep `isolated_fixture` installs (#9630).

`docs/design/monitor-api-router-inventory.md` pins its seam tables to this output
through `tests/api/test_router_inventory_seams.py`. Nothing here is copied from the
fixture: the real fixture function runs against a recording `MonkeyPatch`.

Run from the repo root, in a fresh interpreter (the loops inside the fixture walk
`sys.modules`, so the result depends on what has been imported):

  /path/to/.venv/bin/python docs/design/count_opsec_fixture_seams.py [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

KIND_ATTR = "setattr"
KIND_ENV = "env"


class RecordingMonkeyPatch(pytest.MonkeyPatch):
    """A real `MonkeyPatch` that also records every attribute and environment seam."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str, str]] = []

    def setattr(self, target: Any, *args: Any, **kwargs: Any) -> None:
        if isinstance(target, str):
            raise TypeError("the fixture patches objects, not dotted-string targets")
        owner = (
            target.__name__
            if isinstance(target, type(sys))
            else f"{type(target).__module__}.{type(target).__qualname__}"
        )
        self.calls.append((KIND_ATTR, owner, args[0]))
        super().setattr(target, *args, **kwargs)

    def setitem(self, dic: Any, name: Any, value: Any) -> None:
        # `setenv` and `delenv` route through here; os.environ is the only mapping the fixture edits.
        if dic is not os.environ:
            raise TypeError("the fixture is only expected to set environment variables through setitem")
        self.calls.append((KIND_ENV, "os.environ", str(name)))
        super().setitem(dic, name, value)

    def delitem(self, dic: Any, name: Any, raising: bool = True) -> None:
        raise TypeError("unrecorded seam kind: delitem")

    def syspath_prepend(self, path: Any) -> None:
        raise TypeError("unrecorded seam kind: syspath_prepend")

    def chdir(self, path: Any) -> None:
        raise TypeError("unrecorded seam kind: chdir")


def summarize(calls: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    """Unique `(kind, owner, name)` targets with their invocation counts, sorted."""
    counts = Counter(calls)
    return [
        {"kind": kind, "owner": owner, "name": name, "invocations": counts[(kind, owner, name)]}
        for kind, owner, name in sorted(counts)
    ]


def record_fixture_seams() -> list[dict[str, Any]]:
    """Run the real `isolated_fixture` body against a recorder and return its seams."""
    sys.path.insert(0, str(REPO_ROOT))
    from tests.api.opsec_sweep import test_opsec_route_sweep as sweep

    body = sweep.isolated_fixture.__wrapped__
    recorder = RecordingMonkeyPatch()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            body(recorder, Path(tmp))
            calls = list(recorder.calls)
    finally:
        recorder.undo()
    return summarize(calls)


def render_markdown(seams: list[dict[str, Any]]) -> str:
    lines = ["| Target | Kind | Invocations |", "| --- | --- | ---: |"]
    lines += [f"| `{seam['owner']}.{seam['name']}` | {seam['kind']} | {seam['invocations']} |" for seam in seams]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print the raw seam list as JSON")
    args = parser.parse_args()
    seams = record_fixture_seams()
    print(json.dumps(seams, indent=2) if args.json else render_markdown(seams))


if __name__ == "__main__":
    main()
