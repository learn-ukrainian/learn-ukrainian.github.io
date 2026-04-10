#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _compress_ranges(lines: list[int]) -> str:
    if not lines:
        return "-"
    ranges: list[str] = []
    start = prev = lines[0]
    for line in lines[1:]:
        if line == prev + 1:
            prev = line
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = line
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest coverage and summarize files below a threshold.")
    parser.add_argument("--threshold", type=float, default=50.0, help="Coverage threshold percentage.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "coverage.json"
        cmd = [
            ".venv/bin/pytest",
            "--cov=scripts",
            "--cov-report=term-missing",
            f"--cov-report=json:{report_path}",
            "tests/",
            "-q",
        ]
        completed = subprocess.run(cmd, check=False)
        if not report_path.exists():
            print("coverage JSON was not produced", file=sys.stderr)
            return completed.returncode or 1
        payload = json.loads(report_path.read_text())

    rows: list[tuple[float, str, str]] = []
    for filename, file_data in payload.get("files", {}).items():
        summary = file_data.get("summary", {})
        percent = float(summary.get("percent_covered", 0.0))
        if percent >= args.threshold:
            continue
        missing_lines = file_data.get("missing_lines", [])
        rows.append((percent, filename, _compress_ranges(missing_lines)))

    print()
    print(f"Files below {args.threshold:.1f}% coverage")
    if not rows:
        print("none")
        return completed.returncode

    rows.sort(key=lambda row: (row[0], row[1]))
    width = max(len(filename) for _, filename, _ in rows)
    header = f"{'file'.ljust(width)}  coverage  missing_lines"
    print(header)
    print(f"{'-' * width}  --------  -------------")
    for percent, filename, missing in rows:
        print(f"{filename.ljust(width)}  {percent:7.1f}%  {missing}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
