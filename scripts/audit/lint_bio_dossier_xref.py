#!/usr/bin/env python3
"""Lint bio research dossiers for fabricated Section 7 cross-track plan paths.

Bio research dossiers (``docs/research/bio/*.md``) cite curriculum plan YAML paths
in Section 7 ("Cross-track links"). Paths listed under **Existing** bullets must
resolve to real files under ``curriculum/l2-uk-en/plans/``. Forward-looking
**Potential**, **Candidate**, and **Phase 2+** bullets are exempt.

Use when
========
- Pre-commit on edited bio dossiers.
- CI / manual sweeps before merging new research dossiers.

Examples
========

    .venv/bin/python scripts/audit/lint_bio_dossier_xref.py
    .venv/bin/python scripts/audit/lint_bio_dossier_xref.py --paths docs/research/bio/yurii-klen.md

Outputs
=======
- stdout: table of fabrications (file, line, path, bullet context).
- exit 0 when every checked Existing path exists on disk.
- exit 1 when one or more Existing paths are missing.

Related
=======
- Issue #2410 — deterministic §7 cross-track path validator.
- Sibling guardrails: scripts/audit/lint_dispatch_brief.py, scripts/audit/lint_agent_trailer.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BIO_DOSSIER_GLOB = "docs/research/bio/*.md"

SECTION7_HEADING = re.compile(r"^##\s+7\.\s+Cross-track links\s*$", re.IGNORECASE)
NEXT_SECTION_HEADING = re.compile(r"^##\s+\d+\.\s+", re.IGNORECASE)
BULLET_HEADING = re.compile(r"^(\s*)-\s+\*\*(.+?)\*\*")
PLAN_PATH = re.compile(
    r"(?:curriculum/l2-uk-en/)?(?:docs/)?plans/[\w-]+/[\w-]+\.yaml"
)

_EXEMPT_MARKERS = ("potential", "candidate", "phase 2+")


@dataclass(frozen=True)
class Fabrication:
    file: Path
    line: int
    path: str
    bullet_context: str


def default_dossier_paths() -> list[Path]:
    return sorted(PROJECT_ROOT.glob(BIO_DOSSIER_GLOB))


def normalize_plan_path(raw_path: str) -> Path:
    """Map a cited plan path to an on-disk curriculum location."""
    path = raw_path.strip("`")
    if path.startswith("curriculum/l2-uk-en/"):
        return PROJECT_ROOT / path
    if path.startswith("docs/"):
        path = path.removeprefix("docs/")
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / path


def _section7_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Return ``(line_number, line)`` rows for Section 7 only."""
    start: int | None = None
    for index, line in enumerate(lines):
        if SECTION7_HEADING.match(line):
            start = index + 1
            break
    if start is None:
        return []

    section: list[tuple[int, str]] = []
    for offset, line in enumerate(lines[start:], start=start + 1):
        if NEXT_SECTION_HEADING.match(line):
            break
        section.append((offset, line))
    return section


def _bullet_is_checked(bullet_context: str) -> bool:
    lowered = bullet_context.casefold()
    if any(marker in lowered for marker in _EXEMPT_MARKERS):
        return False
    return "existing" in lowered


def lint_dossier(path: Path) -> list[Fabrication]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"Error: {path} is not a valid UTF-8 file ({exc})", file=sys.stderr)
        sys.exit(2)

    fabrications: list[Fabrication] = []
    current_bullet = ""
    for line_number, line in _section7_lines(content.splitlines()):
        bullet_match = BULLET_HEADING.match(line)
        if bullet_match:
            current_bullet = bullet_match.group(2).strip()

        if not current_bullet or not _bullet_is_checked(current_bullet):
            continue

        for raw_path in PLAN_PATH.findall(line):
            resolved = normalize_plan_path(raw_path)
            if not resolved.exists():
                fabrications.append(
                    Fabrication(
                        file=path,
                        line=line_number,
                        path=raw_path,
                        bullet_context=current_bullet,
                    )
                )
    return fabrications


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def print_report(fabrications: list[Fabrication]) -> None:
    if not fabrications:
        print("No fabricated Existing cross-track plan paths found.")
        return

    file_width = max(len(_display_path(item.file)) for item in fabrications)
    path_width = max(len(item.path) for item in fabrications)

    header = (
        f"{'file':<{file_width}}  {'line':>4}  "
        f"{'path':<{path_width}}  bullet_context"
    )
    print(header)
    print("-" * len(header))
    for item in fabrications:
        print(
            f"{_display_path(item.file):<{file_width}}  {item.line:>4}  "
            f"{item.path:<{path_width}}  {item.bullet_context}"
        )
    print()
    print(f"❌ {len(fabrications)} fabricated Existing cross-track plan path(s).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Section 7 Existing cross-track plan paths in bio research dossiers.\n"
            "Flags YAML paths that do not exist under curriculum/l2-uk-en/plans/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        type=Path,
        metavar="PATH",
        help=(
            "One or more bio dossier markdown files to scan. "
            f"Default: every file matching {BIO_DOSSIER_GLOB}."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = [Path(p) for p in args.paths] if args.paths else default_dossier_paths()

    fabrications: list[Fabrication] = []
    for path in paths:
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists() or not path.is_file():
            parser.error(f"dossier does not exist or is not a file: {path}")
        fabrications.extend(lint_dossier(path))

    print_report(fabrications)
    return 1 if fabrications else 0


if __name__ == "__main__":
    sys.exit(main())
