#!/usr/bin/env python3
"""Unexpected repo-root entry guard (#6863).

A transport/quoting defect once materialized garbage directories at the repo
root — names that were verbatim opencode/ACP event-stream JSON lines and
word-split tokens of them (a literal ``-rf`` among them). Empty directories
are invisible to ``git status``, so this class of pollution sat undetected;
one of them even grew a shadow fleet-comms DB and swallowed a message.

This guard deterministically lists the primary checkout's top-level entries
and reports any that are neither tracked nor gitignored. It is ALERT-ONLY:
nothing is ever deleted here — garbage root entries are forensic evidence and
removal is an explicit human decision.

Surfaces:
* Session-start sweep: ``agents_extensions/shared/hooks/session-setup.sh``
  invokes this module bounded and surfaces findings as an ISSUE line.
* Advisory CLI: ``python -m scripts.hygiene.root_entry_guard [--strict]``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Dual-flavor import: delegate workers put only ``scripts/`` on sys.path (see
# the note in scripts/guardrails/worktree_containment.py).
try:
    from scripts.common.git_context import sanitized_git_env
    from scripts.guardrails.worktree_containment import resolve_main_root
except ImportError:  # scripts/ on sys.path (stripped flavor)
    from common.git_context import sanitized_git_env  # type: ignore[no-redef]
    from guardrails.worktree_containment import resolve_main_root  # type: ignore[no-redef]

__all__ = ["UnexpectedEntry", "main", "scan_unexpected_root_entries"]


class UnexpectedEntry:
    """One top-level repo-root entry that git does not expect."""

    def __init__(self, name: str, *, kind: str, empty_dir: bool) -> None:
        self.name = name
        self.kind = kind
        # Empty dirs are invisible to git status; everything else git can see.
        self.git_invisible = empty_dir

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "git_invisible": self.git_invisible,
        }


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        env=sanitized_git_env(),
    )


def _tracked_top_level_names(root: Path) -> set[str]:
    """First path component of every tracked file (NUL-safe)."""
    proc = _run_git(root, "ls-files", "-z")
    if proc.returncode != 0:
        raise RuntimeError(
            f"git ls-files failed under {root}: "
            f"{(proc.stderr or proc.stdout or 'unknown error').strip()}"
        )
    names: set[str] = set()
    for path in proc.stdout.split("\0"):
        if path:
            names.add(path.split("/", 1)[0])
    return names


def _is_ignored(root: Path, name: str) -> bool:
    # -q: exit 0 == ignored, 1 == not ignored, 128 == error.
    proc = _run_git(root, "check-ignore", "-q", "--", name)
    return proc.returncode == 0


def _classify(entry: Path) -> tuple[str, bool]:
    """(kind, empty_dir) for a top-level entry; symlinks are not followed."""
    if entry.is_symlink():
        return "symlink", False
    if entry.is_dir():
        try:
            empty = not any(entry.iterdir())
        except OSError:
            empty = False
        return "dir", empty
    return "file", False


def scan_unexpected_root_entries(repo_root: Path | None = None) -> list[UnexpectedEntry]:
    """Top-level entries of the primary checkout that git neither tracks nor ignores.

    ``repo_root`` may point anywhere inside the repo (a worktree cwd included);
    the scan always targets the primary checkout that owns the shared ``.git``.
    Raises if the anchor is not inside a git repository.
    """
    root = resolve_main_root(repo_root if repo_root is not None else Path.cwd())
    tracked = _tracked_top_level_names(root)

    unexpected: list[UnexpectedEntry] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        name = entry.name
        if name == ".git" or name in tracked:
            continue
        if _is_ignored(root, name):
            continue
        kind, empty_dir = _classify(entry)
        unexpected.append(UnexpectedEntry(name, kind=kind, empty_dir=empty_dir))
    return unexpected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Alert on unexpected top-level entries in the primary checkout "
            "(including empty dirs git cannot see). Advisory by default; "
            "never deletes anything (#6863)."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Anchor path inside the repo (default: cwd); scan targets the primary checkout.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when unexpected entries exist (default: always exit 0).",
    )
    args = parser.parse_args(argv)

    root = resolve_main_root(args.repo_root if args.repo_root is not None else Path.cwd())
    unexpected = scan_unexpected_root_entries(root)
    report = {
        "repo_root": str(root),
        "unexpected_count": len(unexpected),
        "unexpected": [entry.to_dict() for entry in unexpected],
    }
    if args.json:
        print(json.dumps(report, indent=2))
    elif unexpected:
        print("UNEXPECTED repo-root entries (inspect manually; never auto-deleted, #6863):")
        for entry in unexpected:
            invis = " [git-invisible empty dir]" if entry.git_invisible else ""
            print(f"  - {entry.name} ({entry.kind}){invis}")
    else:
        print("Root hygiene OK: no unexpected top-level entries.")
    return 1 if (args.strict and unexpected) else 0


if __name__ == "__main__":
    sys.exit(main())
