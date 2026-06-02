#!/usr/bin/env python3
"""Validate that compiled wiki short citations resolve in visible source lists."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_FIGURES_DIR = PROJECT_ROOT / "wiki" / "figures"
CITATION_RE = re.compile(r"\[S(?P<num>10|[1-9])\]")
SOURCE_HEADING_RE = re.compile(
    r"^#{2,6}\s*(?:джерела|список джерел|бібліографія|references|sources)\b",
    re.IGNORECASE | re.MULTILINE,
)
SOURCE_MAPPING_RE = re.compile(r"(?:^|\n)\s*(?:[-*]\s*)?(?:\[(S(?:[1-9]|10))\]|(S(?:[1-9]|10))\s*[.:])\s+\S")


@dataclass(frozen=True)
class CitationResolutionFinding:
    path: str
    cited_ids: list[str]
    reason: str


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def inline_citation_ids(text: str) -> list[str]:
    return [f"S{num}" for num in sorted({int(match.group("num")) for match in CITATION_RE.finditer(text)})]


def has_source_mapping_section(text: str) -> bool:
    heading = SOURCE_HEADING_RE.search(text)
    if not heading:
        return False
    section = text[heading.end():]
    next_heading = re.search(r"^#{1,6}\s+\S", section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    return bool(SOURCE_MAPPING_RE.search(section))


def check_citation_resolution_text(text: str, *, path: str = "<text>") -> CitationResolutionFinding | None:
    cited_ids = inline_citation_ids(text)
    if not cited_ids:
        return None
    if has_source_mapping_section(text):
        return None
    return CitationResolutionFinding(
        path=path,
        cited_ids=cited_ids,
        reason="inline [S#] citations have no visible source-list mapping",
    )


def check_file(path: Path) -> CitationResolutionFinding | None:
    text = path.read_text(encoding="utf-8")
    return check_citation_resolution_text(text, path=_relative(path))


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


def check_paths(paths: list[Path]) -> list[CitationResolutionFinding]:
    findings: list[CitationResolutionFinding] = []
    for path in paths:
        finding = check_file(path)
        if finding:
            findings.append(finding)
    return findings


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
            print(f"{finding.path}: {finding.reason}")
            print(f"  cited-ids: {', '.join(finding.cited_ids)}")
        print(f"Scanned {len(paths)} wiki figure file(s) · {len(findings)} unresolved citation file(s)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
