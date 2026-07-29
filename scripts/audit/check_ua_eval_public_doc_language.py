#!/usr/bin/env python3
"""Reject Cyrillic running prose in the public English UA-eval documents."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ENGLISH_DOCS = (
    Path("docs/projects/ua-eval-harness/DATA_CARD.en.md"),
    Path("docs/projects/ua-eval-harness/README.md"),
    Path("docs/projects/ua-eval-harness/REPRODUCING.md"),
    Path("docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md"),
    Path("docs/projects/ua-eval-harness/contamination-policy.md"),
)

_CYRILLIC_RE = re.compile(r"[\u0400-\u052f]")
_MARKDOWN = MarkdownIt("commonmark")


@dataclass(frozen=True, order=True)
class Finding:
    """One Cyrillic character found in visible prose."""

    path: Path
    line: int
    column: int
    excerpt: str
    message: str = "Cyrillic is not allowed in English running prose"

    def format(self) -> str:
        return f"{display_path(self.path)}:{self.line}:{self.column}: {self.message}: {self.excerpt}"


def display_path(path: Path) -> str:
    """Return a stable repository-relative path when possible."""

    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _token_span(token: Token, fallback: tuple[int, int]) -> tuple[int, int]:
    if token.map is None:
        return fallback
    return token.map[0], token.map[1]


def _visible_fragments(
    tokens: list[Token],
    fallback_span: tuple[int, int],
) -> list[tuple[str, tuple[int, int]]]:
    """Return rendered text fragments while excluding parsed Markdown code."""

    fragments: list[tuple[str, tuple[int, int]]] = []
    for token in tokens:
        span = _token_span(token, fallback_span)
        if token.type in {"code_block", "code_inline", "fence"}:
            continue
        if token.children:
            fragments.extend(_visible_fragments(token.children, span))
        elif token.content:
            fragments.append((token.content, span))
    return fragments


def _fence_is_closed(token: Token, source_lines: list[str]) -> bool:
    """Return whether a parsed root-level fence has an explicit closing line."""

    if token.map is None or not token.markup:
        return False
    start, end = token.map
    marker = re.escape(token.markup[0])
    width = len(token.markup)
    closing = re.compile(rf"^ {{0,3}}{marker}{{{width},}}[ \t]*$")
    return any(closing.fullmatch(source_lines[index]) for index in range(start + 1, min(end, len(source_lines))))


def _unclosed_fence_findings(tokens: list[Token], source_lines: list[str], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for token in tokens:
        if token.type != "fence" or _fence_is_closed(token, source_lines):
            continue
        line_index = token.map[0] if token.map is not None else 0
        excerpt = source_lines[line_index].strip() if source_lines else ""
        findings.append(
            Finding(
                path=path,
                line=line_index + 1,
                column=1,
                excerpt=excerpt,
                message="Unclosed fenced code block is not allowed because it can hide later prose",
            )
        )
    return findings


def _cyrillic_word(fragment: str, position: int) -> str:
    start = position
    end = position + 1
    while start > 0 and _CYRILLIC_RE.fullmatch(fragment[start - 1]):
        start -= 1
    while end < len(fragment) and _CYRILLIC_RE.fullmatch(fragment[end]):
        end += 1
    return fragment[start:end]


def _source_location(
    fragment: str,
    position: int,
    span: tuple[int, int],
    source_lines: list[str],
) -> tuple[int, int, str]:
    """Map a rendered Cyrillic fragment back to its source line."""

    start_line, end_line = span
    relative_line = fragment[:position].count("\n")
    preferred_line = min(start_line + relative_line, max(start_line, end_line - 1))
    word = _cyrillic_word(fragment, position)
    candidate_lines = [preferred_line, *range(start_line, end_line)]

    seen: set[int] = set()
    for line_index in candidate_lines:
        if line_index in seen or not (0 <= line_index < len(source_lines)):
            continue
        seen.add(line_index)
        column = source_lines[line_index].find(word)
        if column >= 0:
            return line_index + 1, column + 1, source_lines[line_index].strip()

    excerpt = fragment.splitlines()[relative_line].strip()
    return preferred_line + 1, 1, excerpt


def scan_text(text: str, path: Path = Path("<memory>")) -> list[Finding]:
    """Return Cyrillic occurrences outside explicit Markdown code."""

    source_lines = text.splitlines()
    tokens = _MARKDOWN.parse(text)
    findings = _unclosed_fence_findings(tokens, source_lines, path)

    for fragment, span in _visible_fragments(tokens, (0, len(source_lines))):
        match = _CYRILLIC_RE.search(fragment)
        if match is None:
            continue
        line, column, excerpt = _source_location(fragment, match.start(), span, source_lines)
        findings.append(
            Finding(
                path=path,
                line=line,
                column=column,
                excerpt=excerpt,
            )
        )

    return sorted(set(findings))


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
