#!/usr/bin/env python3
"""Reject bare python/python3 in staged shell scripts (pre-commit).

The project interpreter is always ``.venv/bin/python``. The only allowed
system-interpreter use is bootstrapping a *new* virtualenv via
``python[3] -m venv …`` — there is no project venv to defer to yet.

A line that merely *contains* ``-m venv`` (comment, second command, etc.)
does not exempt other bare-python invocations on that line.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# Command-start boundary: line start or typical shell command separators.
_BARE_PYTHON = re.compile(
    r"(?:^|(?<=[\s;|&(`]))(?P<cmd>python3?)(?=\s)"
)
_VENV_BOOTSTRAP = re.compile(r"^python3?\s+-m\s+venv(?:\s|$)")
_SHELL_SUFFIX = frozenset({".sh", ".bash"})


def _strip_shell_comment(line: str) -> str:
    """Drop a bash ``# …`` comment tail so comments cannot launder exemptions.

    Bash starts a comment only when ``#`` begins a word (start of line, or after
    an *unescaped* whitespace / ``;|&()``). Mid-token hashes (``foo#bar``),
    escaped hashes (``\\#``), and hashes after escaped separators
    (``foo\\ #bar``, ``foo\\;#bar``) stay literal.
    """

    in_single = False
    in_double = False
    escaped = False
    at_word_start = True
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            at_word_start = False
            continue
        if char == "\\" and not in_single:
            # Outside single quotes, backslash escapes the next character.
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            at_word_start = False
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            at_word_start = False
            continue
        if char == "#" and not in_single and not in_double and at_word_start:
            return line[:index]
        at_word_start = char in " \t;|&()" and not in_single and not in_double
    return line


def bare_python_hits(text: str) -> list[tuple[int, str]]:
    """Return ``(1-based line, line text)`` for disallowed bare-python uses."""

    hits: list[tuple[int, str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_shell_comment(raw_line)
        for match in _BARE_PYTHON.finditer(line):
            snippet = line[match.start("cmd") :]
            if _VENV_BOOTSTRAP.match(snippet):
                continue
            hits.append((line_number, raw_line.rstrip("\n")))
            break
    return hits


def staged_shell_files(repo_root: Path) -> list[Path]:
    """Return staged added/modified shell scripts under ``repo_root``."""

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("git diff --cached timed out after 30s", file=sys.stderr)
        raise SystemExit(2) from None
    if result.returncode != 0:
        print(result.stderr or result.stdout or "git diff --cached failed", file=sys.stderr)
        raise SystemExit(2)
    files: list[Path] = []
    for name in result.stdout.splitlines():
        path = Path(name)
        if path.suffix in _SHELL_SUFFIX:
            files.append(repo_root / path)
    return files


def check_files(files: Iterable[Path]) -> int:
    """Print violations and return process exit code."""

    exit_code = 0
    for path in files:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"ERROR: {path} is not utf-8", file=sys.stderr)
            exit_code = 1
            continue
        hits = bare_python_hits(text)
        if not hits:
            continue
        exit_code = 1
        rel = path
        print(
            f"ERROR: {rel} uses bare python/python3, use .venv/bin/python instead",
            file=sys.stderr,
        )
        for line_number, line in hits:
            print(f"{line_number}:{line}", file=sys.stderr)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Git repo root (default: cwd). Used with --staged.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--staged",
        action="store_true",
        help="Scan staged added/modified .sh/.bash files (pre-commit mode).",
    )
    group.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="Scan explicit files (tests / ad-hoc).",
    )
    group.add_argument(
        "--stdin",
        action="store_true",
        help="Scan a single shell script from stdin (tests).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.stdin:
        hits = bare_python_hits(sys.stdin.read())
        for line_number, line in hits:
            print(f"{line_number}:{line}")
        return 1 if hits else 0
    if args.files is not None:
        return check_files(args.files)
    repo_root = (args.repo_root or Path.cwd()).resolve()
    return check_files(staged_shell_files(repo_root))


if __name__ == "__main__":
    raise SystemExit(main())
