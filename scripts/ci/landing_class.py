#!/usr/bin/env python3
"""Classify merge-queue diffs as docs/skills-only vs full CI (#7018).

Fail-closed: empty path lists, unreadable git, unexpected errors, and any
path outside the allowlist yield ``full``. Only an exhaustive allowlist match
yields ``docs_skills``.

Allowlist (deny by omission):
  - ``agents_extensions/shared/skills/**``
  - ``docs/**/*.md``
  - repo-root ``*.md``

Stdlib only so GitHub runners can invoke it with system ``python3`` before
``actions/setup-python``. The CLI always exits 0 and always emits a class
(``full`` on any failure) so CI Gate can require downstream jobs as success
via no-op paths, never via ``skipped`` (#5762).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

CLASS_DOCS_SKILLS = "docs_skills"
CLASS_FULL = "full"

SKILLS_PREFIX = "agents_extensions/shared/skills"


def path_allowed(path: str) -> bool:
    """Return True when a repo-relative POSIX path is on the docs/skills allowlist."""
    text = PurePosixPath(path.strip()).as_posix()
    if not text or text in {".", "/"}:
        return False
    if text == SKILLS_PREFIX or text.startswith(f"{SKILLS_PREFIX}/"):
        return True
    if text.startswith("docs/") and text.endswith(".md"):
        return True
    return "/" not in text and text.endswith(".md")


def classify(paths: Iterable[str]) -> str:
    """Return ``docs_skills`` only when every path is allowlisted; else ``full``."""
    normalized = [p.strip() for p in paths if p and p.strip()]
    if not normalized:
        return CLASS_FULL
    if all(path_allowed(path) for path in normalized):
        return CLASS_DOCS_SKILLS
    return CLASS_FULL


def _parse_nul_delimited_paths(raw: bytes) -> list[str]:
    return sorted(path.decode("utf-8", errors="surrogateescape") for path in raw.split(b"\0") if path)


def changed_files(git_range: str, *, cwd: Path | None = None) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--no-ext-diff",
            "--name-only",
            "-z",
            git_range,
        ],
        check=True,
        capture_output=True,
        cwd=cwd or Path.cwd(),
    )
    return _parse_nul_delimited_paths(result.stdout)


def comparison_range(base: str, head: str = "HEAD") -> str:
    """Three-dot merge-base range (``BASE...HEAD``) for landing classification."""
    return base if "..." in base else f"{base}...{head}"


def read_paths_from_stdin(stream: Iterable[str] | None = None) -> list[str]:
    source = sys.stdin if stream is None else stream
    return [line.strip() for line in source if line.strip()]


def write_github_output(landing_class: str, path: Path | None = None) -> None:
    output = path
    if output is None:
        raw = os.environ.get("GITHUB_OUTPUT")
        if not raw:
            return
        output = Path(raw)
    with output.open("a", encoding="utf-8") as handle:
        handle.write(f"class={landing_class}\n")


def write_step_summary(landing_class: str, *, path_count: int, path: Path | None = None) -> None:
    summary = path
    if summary is None:
        raw = os.environ.get("GITHUB_STEP_SUMMARY")
        if not raw:
            return
        summary = Path(raw)
    with summary.open("a", encoding="utf-8") as handle:
        handle.write("## Landing class (#7018)\n\n")
        handle.write(f"`class={landing_class}` changed_files={path_count}\n")


def emit(landing_class: str, *, path_count: int, as_json: bool, github_output: bool) -> None:
    if as_json:
        print(json.dumps({"class": landing_class, "changed_files": path_count}, sort_keys=True))
    else:
        print(landing_class)
    write_step_summary(landing_class, path_count=path_count)
    if github_output:
        write_github_output(landing_class)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="",
        help="base SHA/ref for git diff (merge_group.base_sha / push before). "
        "Omit to read newline-delimited paths from stdin.",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="head SHA/ref (merge_group.head_sha / github.sha); default HEAD",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit {\"class\": ..., \"changed_files\": N} on stdout",
    )
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="append class=... to $GITHUB_OUTPUT when set",
    )
    as_json = False
    github_output = False
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        as_json = bool(args.json)
        github_output = bool(args.github_output)
        base = (args.base or "").strip()
        head = (args.head or "HEAD").strip() or "HEAD"
        if base:
            if set(base) == {"0"}:
                emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
                return 0
            paths = changed_files(comparison_range(base, head))
        elif github_output:
            # CI without a usable base SHA — fail closed (do not read stdin).
            emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
            return 0
        elif sys.stdin.isatty():
            # No paths and no git range — fail closed.
            emit(CLASS_FULL, path_count=0, as_json=as_json, github_output=github_output)
            return 0
        else:
            paths = read_paths_from_stdin()
        landing = classify(paths)
        emit(landing, path_count=len(paths), as_json=as_json, github_output=github_output)
        return 0
    except Exception as exc:
        # Fail closed to full; never crash the landing-class job.
        print(f"landing-class: error → {CLASS_FULL} ({exc})", file=sys.stderr)
        emit(CLASS_FULL, path_count=-1, as_json=as_json, github_output=github_output)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
