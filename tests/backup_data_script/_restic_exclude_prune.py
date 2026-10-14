"""Apply restic exclude patterns to a fake snapshot directory.

restic's filter matches each path component with Go's filepath.Match, anchors a
pattern that starts with ``/``, and lets a ``**`` component span directories.
This is the fake ``restic`` file-phase pruner: it deletes what those patterns
exclude instead of guessing ``*-home`` names on its own.
"""

from __future__ import annotations

import os
import shutil
import sys


def component_match(pattern: str, name: str) -> bool:
    """Go ``filepath.Match`` for one path component, which never contains ``/``."""

    def match_chunk(chunk: str, text: str) -> tuple[str, bool]:
        failed = False
        while chunk:
            failed = failed or not text
            char = chunk[0]
            if char == "[":
                if not failed:
                    rune, text = text[0], text[1:]
                else:
                    rune = ""
                chunk = chunk[1:]
                negated = chunk.startswith("^")
                if negated:
                    chunk = chunk[1:]
                matched = False
                ranges = 0
                while True:
                    if chunk.startswith("]") and ranges > 0:
                        chunk = chunk[1:]
                        break
                    if not chunk or chunk[0] in "-]":
                        raise ValueError("bad pattern")
                    low, chunk = _escaped(chunk)
                    high = low
                    if chunk.startswith("-"):
                        high, chunk = _escaped(chunk[1:])
                    matched = matched or (low <= rune <= high)
                    ranges += 1
                failed = failed or (matched == negated)
            elif char == "?":
                if not failed:
                    failed = text[0] == "/"
                    text = text[1:]
                chunk = chunk[1:]
            elif char == "\\":
                chunk = chunk[1:]
                if not chunk:
                    raise ValueError("bad pattern")
                if not failed:
                    failed = chunk[0] != text[0]
                    text = text[1:]
                chunk = chunk[1:]
            else:
                if not failed:
                    failed = chunk[0] != text[0]
                    text = text[1:]
                chunk = chunk[1:]
        if failed:
            return "", False
        return text, True

    def _escaped(chunk: str) -> tuple[str, str]:
        if not chunk or chunk[0] in "-]":
            raise ValueError("bad pattern")
        if chunk[0] == "\\":
            chunk = chunk[1:]
            if not chunk:
                raise ValueError("bad pattern")
        return chunk[0], chunk[1:]

    while pattern:
        star = False
        while pattern.startswith("*"):
            pattern = pattern[1:]
            star = True
        in_range = False
        split_at = len(pattern)
        index = 0
        while index < len(pattern):
            current = pattern[index]
            if current == "\\":
                index += 2 if index + 1 < len(pattern) else 1
                continue
            if current == "[":
                in_range = True
            elif current == "]":
                in_range = False
            elif current == "*" and not in_range:
                split_at = index
                break
            index += 1
        chunk, pattern = pattern[:split_at], pattern[split_at:]
        if star and chunk == "":
            return "/" not in name
        rest, ok = match_chunk(chunk, name)
        if ok and (rest == "" or pattern):
            name = rest
            continue
        if star:
            for index in range(len(name)):
                if name[index] == "/":
                    break
                rest, ok = match_chunk(chunk, name[index + 1 :])
                if ok and not (pattern == "" and rest):
                    name = rest
                    break
            else:
                return False
            continue
        return False
    return name == ""


def split_path(path: str) -> list[str]:
    """``filepath.Clean`` plus the leading ``/`` component restic uses."""
    cleaned = os.path.normpath(path)
    parts = cleaned.split("/")
    if parts and parts[0] == "":
        parts[0] = "/"
    return parts


def prepare_pattern(pattern: str) -> list[str]:
    """Expand ``$VAR`` the way an exclude file does, then split out ``**``."""
    return ["" if part == "**" else part for part in split_path(os.path.expandvars(pattern))]


def _component_ok(pattern: str, name: str) -> bool:
    """Literal components compare equal; the rest use Go ``filepath.Match``."""
    if not any(char in pattern for char in "\\[]*?"):
        return pattern == name
    return component_match(pattern, name)


def match(pattern_parts: list[str], parts: list[str]) -> bool:
    """restic ``filter.Match``: ``**`` spans directories; a leading ``/`` anchors.

    A match may leave unmatched components after the pattern, which is how a
    directory pattern excludes its children. A pattern that does not start
    with ``/`` may begin at any later component, but not on the absolute-path
    marker itself. ``**`` alone matches one or more of those components.
    Expanding every ``**`` into a fresh pattern is the same rule and is too
    slow for the thousand-file backup tests, so each pattern is one pass.
    """
    if not pattern_parts and not parts:
        return True
    if not pattern_parts:
        return False
    if all(part == "" for part in pattern_parts):
        start = 1 if parts and parts[0] == "/" else 0
        return start < len(parts)
    if pattern_parts[0] == "/":
        return _window_matches(pattern_parts, parts, 0)
    start = 1 if parts and parts[0] == "/" else 0
    # The empty part is a leading "**": the pattern may start further along.
    return _window_matches(["", *pattern_parts], parts, start)


def _window_matches(pattern: list[str], parts: list[str], start: int) -> bool:
    """True when ``pattern`` consumes a contiguous window starting at ``start``."""
    count = len(parts)
    if start < 0 or start > count:
        return False
    states = [False] * (count + 1)
    states[start] = True
    for part in pattern:
        if not any(states):
            return False
        nxt = [False] * (count + 1)
        if part == "":
            seen = False
            for index, active in enumerate(states):
                seen = seen or active
                if seen:
                    nxt[index] = True
            states = nxt
            continue
        try:
            for index in range(count):
                if states[index] and _component_ok(part, parts[index]):
                    nxt[index + 1] = True
        except ValueError:
            return False
        states = nxt
    return any(states)


def path_is_excluded(patterns: list[str], path: str) -> bool:
    parts = split_path(path)
    return any(match(prepare_pattern(pattern), parts) for pattern in patterns if pattern)


def prune(
    snapshot_root: str,
    source_root: str,
    patterns: list[str],
    protected: list[str] | None = None,
) -> None:
    """Delete snapshot paths whose source path matches a passed exclude pattern.

    ``protected`` paths are explicit backup targets. restic saves an explicit
    file or directory even when an exclude matches that path, and still
    applies excludes to children found by walking a directory target.
    """
    prepared = [prepare_pattern(pattern) for pattern in patterns if pattern]
    protected_norm = {os.path.normpath(path) for path in protected or []}

    def excluded(source: str) -> bool:
        # An explicit target stays, and so do its ancestor directories: a
        # directory exclude must not rmtree the explicit file inside it.
        # Other children of those ancestors are still eligible.
        norm = os.path.normpath(source)
        if norm in protected_norm or any(path.startswith(f"{norm}{os.sep}") for path in protected_norm):
            return False
        parts = split_path(source)
        return any(match(pattern, parts) for pattern in prepared)

    for directory, dirnames, filenames in os.walk(snapshot_root, topdown=True, followlinks=False):
        relative = os.path.relpath(directory, snapshot_root)
        source_directory = source_root if relative == "." else os.path.join(source_root, relative)
        kept: list[str] = []
        for name in dirnames:
            full = os.path.join(directory, name)
            source = os.path.join(source_directory, name)
            if excluded(source):
                if os.path.islink(full):
                    os.unlink(full)
                else:
                    shutil.rmtree(full)
            else:
                kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            full = os.path.join(directory, name)
            source = os.path.join(source_directory, name)
            if excluded(source) and os.path.lexists(full):
                os.unlink(full)


def _nul_texts(raw: bytes) -> list[str]:
    return [item.decode() for item in raw.split(b"\0") if item]


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print("usage: prune SNAPSHOT_ROOT SOURCE_ROOT [PROTECTED_FILE]", file=sys.stderr)
        return 2
    snapshot_root, source_root = argv[1], argv[2]
    protected: list[str] = []
    if len(argv) == 4:
        with open(argv[3], "rb") as handle:
            protected = _nul_texts(handle.read())
    patterns = _nul_texts(sys.stdin.buffer.read())
    prune(snapshot_root, source_root, patterns, protected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
