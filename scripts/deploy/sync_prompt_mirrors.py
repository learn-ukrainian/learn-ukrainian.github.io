#!/usr/bin/env python3
"""Copy deploy mirrors in one process, with rsync -a --delete exclude semantics.

``deploy_prompts.sh`` used to start rsync once per destination and once per shared
skill. The transfers are independent and the exclude rules are anchored, so one
walk per pair keeps the same tree. ``.agent`` is not handled here: that mirror
stays descriptor-bound in ``sync_agent_mirror.py``.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
import stat
import sys
from pathlib import Path


def _pattern_hits(parts: list[str], is_dir: bool, pattern: str) -> bool:
    """Whether ``parts`` is covered by one anchored rsync exclude pattern."""
    directory_only = pattern.endswith("/")
    body = pattern[1:] if pattern.startswith("/") else pattern
    if body.endswith("/"):
        body = body[:-1]
    if not body:
        return False
    tokens = body.split("/")
    if len(parts) < len(tokens):
        return False
    if not all(fnmatch.fnmatchcase(piece, token) for piece, token in zip(parts, tokens, strict=False)):
        return False
    if len(parts) == len(tokens):
        return is_dir or not directory_only
    # A matched directory is not descended into, so everything under it is excluded.
    return True


def excluded(relative: str, is_dir: bool, patterns: tuple[str, ...]) -> bool:
    """``relative`` is excluded by an anchored ``--exclude`` pattern (leading slash)."""
    if not relative:
        return False
    parts = relative.split("/")
    return any(_pattern_hits(parts, is_dir, pattern) for pattern in patterns)


def _remove(path: Path, is_dir: bool) -> None:
    if path.is_symlink():
        path.unlink()
    elif is_dir:
        shutil.rmtree(path)
    else:
        path.unlink()


def _place(source: Path, destination: Path) -> None:
    info = source.lstat()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(source)
        if destination.is_symlink() or destination.exists():
            _remove(destination, destination.is_dir() and not destination.is_symlink())
        destination.symlink_to(target)
        return
    if stat.S_ISDIR(info.st_mode):
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            _remove(destination, False)
        destination.mkdir(parents=True, exist_ok=True)
        os.chmod(destination, stat.S_IMODE(info.st_mode))
        return
    if not stat.S_ISREG(info.st_mode):
        raise OSError(f"refusing to copy non-regular file {source}")
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        _remove(destination, destination.is_dir() and not destination.is_symlink())
    shutil.copy2(source, destination)


def _source_records(source: Path, patterns: tuple[str, ...]) -> list[str]:
    records: list[str] = []

    def walk(directory: Path, prefix: str) -> None:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            is_dir = entry.is_dir(follow_symlinks=False)
            if excluded(relative, is_dir, patterns):
                continue
            records.append(relative)
            if is_dir:
                walk(Path(entry.path), relative)

    walk(source, "")
    return records


def _delete_extras(destination: Path, kept: set[str], patterns: tuple[str, ...]) -> None:
    if not destination.exists():
        return

    def walk(directory: Path, prefix: str) -> None:
        for entry in os.scandir(directory):
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            is_dir = entry.is_dir(follow_symlinks=False)
            path = Path(entry.path)
            if excluded(relative, is_dir, patterns):
                continue
            if relative not in kept:
                _remove(path, is_dir and not entry.is_symlink())
            elif is_dir and not entry.is_symlink():
                walk(path, relative)

    walk(destination, "")


def sync_tree(source: Path, destination: Path, patterns: tuple[str, ...], *, delete: bool) -> None:
    """Copy ``source``/ into ``destination``/. ``delete`` removes unexcluded extras."""
    if not source.is_dir():
        raise NotADirectoryError(f"deploy mirror source is not a directory: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    records = _source_records(source, patterns)
    for relative in records:
        _place(source / relative, destination / relative)
    if delete:
        _delete_extras(destination, set(records), patterns)


def apply_spec(spec_path: Path) -> None:
    """Apply a tab-separated spec: ``delete|copy``, source, destination, excludes."""
    text = spec_path.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            continue
        kind, source, destination, *patterns = line.split("\t")
        if kind not in {"delete", "copy"}:
            raise ValueError(f"deploy mirror spec line {line_number} has kind {kind!r}")
        sync_tree(Path(source), Path(destination), tuple(patterns), delete=kind == "delete")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: sync_prompt_mirrors.py SPEC", file=sys.stderr)
        return 2
    try:
        apply_spec(Path(argv[0]))
    except (OSError, ValueError) as exc:
        print(f"Error: deploy mirror sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
