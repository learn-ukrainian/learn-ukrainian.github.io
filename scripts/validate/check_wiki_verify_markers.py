#!/usr/bin/env python3
"""Fail compiled wiki files that still contain VERIFY markers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_FIGURES_DIR = PROJECT_ROOT / "wiki" / "figures"
VERIFY_RE = re.compile(r"<!--\s*VERIFY\b.*?-->|(?<![A-Za-z])VERIFY\s*:", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class VerifyMarkerFinding:
    path: str
    line: int
    marker: str


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_verify_markers_text(text: str, *, path: str = "<text>") -> list[VerifyMarkerFinding]:
    findings: list[VerifyMarkerFinding] = []
    for match in VERIFY_RE.finditer(text):
        marker = " ".join(match.group(0).split())
        findings.append(
            VerifyMarkerFinding(
                path=path,
                line=_line_number(text, match.start()),
                marker=marker[:160],
            )
        )
    return findings


def check_file(path: Path) -> list[VerifyMarkerFinding]:
    text = path.read_text(encoding="utf-8")
    return find_verify_markers_text(text, path=_relative(path))


def iter_paths(paths: list[str] | None = None) -> list[Path]:
    if not paths:
        return sorted(WIKI_FIGURES_DIR.glob("*.md"))
    resolved: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            resolved.extend(sorted(path.glob("*.md")))
        else:
            resolved.append(path)
    return resolved


def check_paths(paths: list[Path]) -> list[VerifyMarkerFinding]:
    findings: list[VerifyMarkerFinding] = []
    for path in paths:
        findings.extend(check_file(path))
    return findings


def assert_no_verify_markers(text: str, *, path: Path | str = "<text>") -> None:
    """Raise ValueError if compiled wiki text contains a VERIFY marker."""
    findings = find_verify_markers_text(text, path=str(path))
    if findings:
        first = findings[0]
        raise ValueError(f"VERIFY marker survivor in {first.path}:{first.line}: {first.marker}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", help="Explicit wiki files/directories.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    paths = iter_paths(args.paths)
    findings = check_paths(paths)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: VERIFY marker survivor")
            print(f"  marker: {finding.marker}")
        print(f"Scanned {len(paths)} wiki figure file(s) · {len(findings)} VERIFY marker(s)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
