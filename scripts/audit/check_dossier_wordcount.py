#!/usr/bin/env python3
"""Check research dossier prose length against the Phase 1 template floor.

The count is intentionally deterministic and local-only: remove YAML
frontmatter, fenced code blocks, HTML comments, URLs, and common Markdown
syntax, then count Unicode alphanumeric runs as words. Link text, heading text,
and inline-code text remain countable because they are reader-visible prose.
This is a template-floor guard, not a readability metric.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORD_FLOOR = 1200

WORD = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*", re.UNICODE)
FENCED_BLOCK = re.compile(r"```.*?```", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAG = re.compile(r"<[^>\n]+>")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
URL = re.compile(r"https?://\S+|www\.\S+")


@dataclass(frozen=True)
class DossierCount:
    path: Path
    words: int

    @property
    def passed(self) -> bool:
        return self.words >= WORD_FLOOR


def _strip_yaml_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def _strip_markdown_markup(text: str) -> str:
    text = _strip_yaml_frontmatter(text)
    text = FENCED_BLOCK.sub(" ", text)
    text = HTML_COMMENT.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    text = INLINE_CODE.sub(r"\1", text)
    text = IMAGE.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    text = URL.sub(" ", text)

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s{0,3}>\s?", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)]\s+", "", line)
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    return re.sub(r"[*_~{}\[\]()|:;,.!?/\\]", " ", text)


def count_words(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    prose = _strip_markdown_markup(text)
    return len(WORD.findall(prose))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _repo_relative(path: Path) -> Path | None:
    absolute = path if path.is_absolute() else PROJECT_ROOT / path
    try:
        return absolute.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None


def _is_research_dossier(path: Path) -> bool:
    relative = _repo_relative(path)
    if relative is None or path.suffix != ".md":
        return False
    return len(relative.parts) >= 3 and relative.parts[:2] == ("docs", "research")


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    cwd_path = path.resolve()
    if cwd_path.exists():
        return cwd_path
    return PROJECT_ROOT / path


def changed_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", "origin/main...HEAD"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)
    return [PROJECT_ROOT / line for line in result.stdout.splitlines() if line]


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        resolved = _resolve_path(path)
        key = resolved.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(resolved)
    return deduped


def collect_paths(args: argparse.Namespace) -> list[Path]:
    paths = [_resolve_path(path) for path in args.paths]
    if args.changed:
        paths.extend(changed_paths())
    return [
        path
        for path in _dedupe(paths)
        if _is_research_dossier(path) and path.exists() and path.is_file()
    ]


def print_report(counts: list[DossierCount]) -> None:
    if not counts:
        print("No docs/research dossier files to check.")
        return

    file_width = max(len(_display_path(item.path)) for item in counts)
    print(f"Dossier word-count floor: {WORD_FLOOR}")
    print(f"{'file':<{file_width}}  {'words':>5}  {'floor':>5}  status")
    print("-" * (file_width + 25))
    for item in counts:
        status = "PASS" if item.passed else "FAIL"
        print(
            f"{_display_path(item.path):<{file_width}}  "
            f"{item.words:>5}  {WORD_FLOOR:>5}  {status}"
        )

    failures = [item for item in counts if not item.passed]
    if failures:
        print()
        print(f"{len(failures)} dossier(s) below the {WORD_FLOOR}-word floor.")
    else:
        print()
        print(f"All checked dossiers meet the {WORD_FLOOR}-word floor.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check docs/research dossier word counts against the template floor.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        type=Path,
        default=[],
        metavar="PATH",
        help="One or more dossier markdown files to check.",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Check changed dossier files from git diff origin/main...HEAD.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.paths and not args.changed:
        parser.error("provide --paths or --changed")

    counts = [DossierCount(path=path, words=count_words(path)) for path in collect_paths(args)]
    print_report(counts)
    return 1 if any(not item.passed for item in counts) else 0


if __name__ == "__main__":
    sys.exit(main())
