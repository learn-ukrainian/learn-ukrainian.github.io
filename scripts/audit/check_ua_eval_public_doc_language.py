#!/usr/bin/env python3
"""Reject Cyrillic running prose in the public English UA-eval documents."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ENGLISH_DOCS = (
    Path("docs/projects/ua-eval-harness/DATA_CARD.en.md"),
    Path("docs/projects/ua-eval-harness/README.md"),
    Path("docs/projects/ua-eval-harness/REPRODUCING.md"),
    Path("docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md"),
    Path("docs/projects/ua-eval-harness/contamination-policy.md"),
)

_CYRILLIC_RE = re.compile(r"[\u0400-\u052f]")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True, order=True)
class Finding:
    """One Cyrillic character found in visible prose."""

    path: Path
    line: int
    column: int
    excerpt: str

    def format(self) -> str:
        return (
            f"{display_path(self.path)}:{self.line}:{self.column}: "
            f"Cyrillic is not allowed in English running prose: {self.excerpt}"
        )


def display_path(path: Path) -> str:
    """Return a stable repository-relative path when possible."""

    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _mask(text: str) -> str:
    """Replace content with spaces without changing offsets or line breaks."""

    return "".join(char if char in "\r\n" else " " for char in text)


def _mask_fenced_code(text: str) -> str:
    """Mask CommonMark backtick and tilde fenced code blocks."""

    output: list[str] = []
    fence_char: str | None = None
    fence_width = 0

    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if fence_char is not None:
            output.append(_mask(line))
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_char)}{{{fence_width},}}[ \t]*",
                body,
            )
            if closing:
                fence_char = None
                fence_width = 0
            continue

        opening = _FENCE_OPEN_RE.match(body)
        if opening is None:
            output.append(line)
            continue

        marker, info = opening.groups()
        if marker[0] == "`" and "`" in info:
            output.append(line)
            continue

        fence_char = marker[0]
        fence_width = len(marker)
        output.append(_mask(line))

    return "".join(output)


def _backtick_run_length(text: str, start: int) -> int:
    end = start
    while end < len(text) and text[end] == "`":
        end += 1
    return end - start


def _find_matching_backtick_run(text: str, start: int, width: int) -> int | None:
    cursor = start
    while cursor < len(text):
        candidate = text.find("`", cursor)
        if candidate < 0:
            return None
        candidate_width = _backtick_run_length(text, candidate)
        if candidate_width == width:
            return candidate
        cursor = candidate + candidate_width
    return None


def _mask_inline_code(text: str) -> str:
    """Mask CommonMark-style inline code spans, including multiline spans."""

    output = list(text)
    cursor = 0
    while cursor < len(text):
        opening = text.find("`", cursor)
        if opening < 0:
            break
        width = _backtick_run_length(text, opening)
        closing = _find_matching_backtick_run(text, opening + width, width)
        if closing is None:
            cursor = opening + width
            continue
        for index in range(opening, closing + width):
            if output[index] not in "\r\n":
                output[index] = " "
        cursor = closing + width
    return "".join(output)


def mask_code(text: str) -> str:
    """Mask explicit Markdown code while preserving source coordinates."""

    return _mask_inline_code(_mask_fenced_code(text))


def scan_text(text: str, path: Path = Path("<memory>")) -> list[Finding]:
    """Return Cyrillic occurrences outside explicit Markdown code."""

    masked_lines = mask_code(text).splitlines()
    source_lines = text.splitlines()
    findings: list[Finding] = []

    for line_number, masked_line in enumerate(masked_lines, start=1):
        match = _CYRILLIC_RE.search(masked_line)
        if match is None:
            continue
        excerpt = source_lines[line_number - 1].strip()
        findings.append(
            Finding(
                path=path,
                line=line_number,
                column=match.start() + 1,
                excerpt=excerpt,
            )
        )

    return findings


def governed_paths() -> list[Path]:
    """Return the complete public English document set."""

    return [PROJECT_ROOT / path for path in PUBLIC_ENGLISH_DOCS]


def _selected_paths(paths: list[Path] | None) -> list[Path]:
    if paths is None:
        return governed_paths()

    governed = {path.resolve(): path for path in governed_paths()}
    selected: list[Path] = []
    seen: set[Path] = set()
    for supplied in paths:
        absolute = supplied if supplied.is_absolute() else PROJECT_ROOT / supplied
        resolved = absolute.resolve()
        if resolved in governed and resolved not in seen:
            selected.append(governed[resolved])
            seen.add(resolved)
    return selected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--files",
        nargs="*",
        type=Path,
        default=None,
        help="Optional pre-commit file list; non-governed paths are ignored.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = _selected_paths(args.files)
    missing = [path for path in paths if not path.is_file()]
    findings: list[Finding] = []

    for path in paths:
        if path.is_file():
            findings.extend(scan_text(path.read_text(encoding="utf-8"), path))

    if not missing and not findings:
        return 0

    print(
        "ERROR: public English UA-eval documents must use English running prose.",
        file=sys.stderr,
    )
    for path in missing:
        print(f"{display_path(path)}: governed document is missing", file=sys.stderr)
    for finding in findings:
        print(finding.format(), file=sys.stderr)
    print(
        "Put exact Ukrainian tokens or examples in Markdown code spans/blocks; put Ukrainian prose in DATA_CARD.uk.md.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
