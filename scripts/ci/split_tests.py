"""Static, duration-balanced split of pytest files across CI shards.

``split`` reads test file paths on stdin and prints the files for one shard.
Every shard computes the same assignment: files are placed longest first on
the least-loaded shard (LPT), using the recorded per-file seconds in
``scripts/ci/pytest-file-durations.json``. A file with no recorded time gets
the median, so a new or renamed file is still run, only balanced less well.
The shards are a partition of the input: every file lands on exactly one.

``durations`` rebuilds that JSON from the JUnit files of a full run:

    python -m scripts.ci.split_tests durations junit/*.xml > scripts/ci/pytest-file-durations.json

Stdlib only, so it runs before the project environment is installed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

DEFAULT_DURATIONS = Path(__file__).with_name("pytest-file-durations.json")


def assign(files: list[str], durations: dict[str, float], shard_count: int) -> list[list[str]]:
    """Longest-processing-time-first assignment of ``files`` to ``shard_count`` shards."""
    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if len(set(files)) != len(files):
        raise ValueError("duplicate test file in the input")
    known = [durations[name] for name in files if name in durations]
    default = statistics.median(known) if known else 1.0
    loads = [0.0] * shard_count
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    # Name breaks ties so the order never depends on the input order.
    for name in sorted(files, key=lambda item: (-durations.get(item, default), item)):
        target = min(range(shard_count), key=lambda index: (loads[index], index))
        shards[target].append(name)
        loads[target] += durations.get(name, default)
    return [sorted(shard) for shard in shards]


def junit_file_seconds(paths: list[Path]) -> dict[str, float]:
    """Sum testcase time per test file (``tests/.../test_x.py``) over JUnit files."""
    totals: dict[str, float] = defaultdict(float)
    for path in paths:
        for case in ElementTree.parse(path).getroot().iter("testcase"):
            parts = case.get("classname", "").split(".")
            # The module is the last dotted part named like a test file; test
            # classes are ``Test*`` and never match ``test_``.
            modules = [index for index, part in enumerate(parts) if part.startswith("test_")]
            if not modules:
                continue
            totals["/".join(parts[: modules[-1] + 1]) + ".py"] += float(case.get("time") or 0)
    return {name: round(seconds, 3) for name, seconds in sorted(totals.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split", help="print one shard's files (input: file paths on stdin)")
    split.add_argument("--shard", type=int, required=True, help="1-based shard number")
    split.add_argument("--of", type=int, required=True, dest="shard_count")
    split.add_argument("--durations", type=Path, default=DEFAULT_DURATIONS)
    durations = commands.add_parser("durations", help="print per-file seconds from JUnit XML")
    durations.add_argument("junit", nargs="+", type=Path)
    args = parser.parse_args(argv)

    if args.command == "durations":
        json.dump(junit_file_seconds(args.junit), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if not 1 <= args.shard <= args.shard_count:
        parser.error(f"--shard {args.shard} is outside 1..{args.shard_count}")
    files = [line.strip() for line in sys.stdin if line.strip()]
    if not files:
        parser.error("no test files on stdin")
    recorded = json.loads(args.durations.read_text(encoding="utf-8"))
    shard = assign(files, recorded, args.shard_count)[args.shard - 1]
    sys.stdout.write("".join(f"{name}\n" for name in shard))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
