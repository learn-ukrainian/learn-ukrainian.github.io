#!/usr/bin/env python3
"""Block local-only private-source review exports from being committed."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PRIVATE_EXPORT_MARKERS = (
    "private_teacher_lesson_bulk_triage.v1",
    "private_teacher_lesson_full_intake.v1",
    "Local review-only bulk triage",
    "Local review-only candidate payload",
)
REVIEW_EXPORT_SUFFIXES = {".json", ".md"}


def staged_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def find_private_source_review_exports(paths: list[Path]) -> list[Path]:
    blocked: list[Path] = []
    for path in paths:
        if path.suffix.lower() not in REVIEW_EXPORT_SUFFIXES or not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(marker in text for marker in PRIVATE_EXPORT_MARKERS):
            blocked.append(path)
    return blocked


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional explicit paths to scan.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = list(args.paths) if args.paths else staged_paths()
    blocked = find_private_source_review_exports(paths)
    if not blocked:
        return 0
    print(
        "ERROR: local-only private-source review exports must not be committed:",
        file=sys.stderr,
    )
    for path in blocked:
        print(f"  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
