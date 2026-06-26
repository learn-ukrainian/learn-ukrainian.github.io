#!/usr/bin/env python3
"""Block internal corpus/source IDs from published seminar MDX."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"
READINGS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "readings"

SEMINAR_DOC_TRACKS = {
    "bio",
    "folk",
    "hist",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}

INTERNAL_ID_PATTERNS = (
    ("corpus chunk id", re.compile(r"\b[0-9a-f]{8}_c[0-9]{4}\b")),
    ("source section id", re.compile(r"\bS[0-9]{3,4}\b")),
)


@dataclass(frozen=True, order=True)
class Finding:
    path: Path
    line_no: int
    column_no: int
    kind: str
    value: str

    def format(self) -> str:
        return (
            f"{display_path(self.path)}:{self.line_no}:{self.column_no}: "
            f"internal {self.kind} leaked: {self.value}"
        )


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _as_absolute_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _repo_relative(path: Path) -> Path | None:
    try:
        return _as_absolute_path(path).resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None


def is_published_seminar_mdx(path: Path, *, allow_external: bool = False) -> bool:
    if path.suffix.lower() != ".mdx":
        return False

    rel_path = _repo_relative(path)
    if rel_path is None:
        return allow_external

    parts = rel_path.parts
    if len(parts) >= 5 and parts[:4] == ("site", "src", "content", "readings"):
        return True
    if len(parts) >= 6 and parts[:4] == ("site", "src", "content", "docs"):
        return parts[4] in SEMINAR_DOC_TRACKS
    return False


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        normalized = path.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(path)
    return unique_paths


def scan_candidates(paths: list[Path], *, allow_external: bool = False) -> list[Path]:
    candidates: list[Path] = []
    for raw_path in paths:
        path = _as_absolute_path(raw_path)
        if not path.is_file():
            continue
        if is_published_seminar_mdx(path, allow_external=allow_external):
            candidates.append(path)
    return _dedupe(candidates)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in INTERNAL_ID_PATTERNS:
            for match in pattern.finditer(line):
                findings.append(
                    Finding(
                        path=path,
                        line_no=line_no,
                        column_no=match.start() + 1,
                        kind=kind,
                        value=match.group(0),
                    )
                )
    return findings


def scan_files(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(scan_file(path))
    return sorted(findings)


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=PROJECT_ROOT, text=True)


def get_changed_files(base: str) -> list[Path]:
    merge_base = _git_output(["merge-base", base, "HEAD"]).strip()
    output = _git_output(["diff", "--name-only", f"{merge_base}...HEAD"])
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def get_local_changed_files(*, cached: bool = False) -> list[Path]:
    cmd = ["diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    output = _git_output(cmd)
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check published seminar/readings MDX for internal source IDs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--changed-vs-base", metavar="BASE", help="Compare against base branch, e.g. origin/main")
    group.add_argument("--files", nargs="+", type=Path, help="Scan explicit files, e.g. from pre-commit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.changed_vs_base:
        raw_paths = [
            *get_changed_files(args.changed_vs_base),
            *get_local_changed_files(),
            *get_local_changed_files(cached=True),
        ]
        candidates = scan_candidates(raw_paths)
    else:
        candidates = scan_candidates(args.files, allow_external=True)

    if not candidates:
        print("0 findings: no published seminar/readings MDX files to scan.")
        return 0

    findings = scan_files(candidates)
    if not findings:
        print(f"0 findings: no internal IDs in {len(candidates)} published seminar/readings MDX file(s).")
        return 0

    for finding in findings:
        print(finding.format())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
