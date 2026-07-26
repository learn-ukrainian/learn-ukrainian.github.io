"""Race-safe reaper for retired deploy artifacts under ``.agent/``.

Deploy records what it wrote to ``.agent/`` in a manifest, and on the next run
removes only entries that have since disappeared from the source tree. That much
was already correct in shell. What shell could not express is doing it *safely*.

The shell version validated a PATH and then deleted by that same PATH. Between
those two steps the path can be redirected: a review reproduced a symlink swapped
in after validation, and deploy then deleted a file OUTSIDE the repository
(``TOCTOU_FILE_EXTERNAL_VICTIM=DELETED``, and the same for ``rmdir``). This is not
a hypothetical race here — ``.agent/`` is written by agents, deploy runs while
other agents are live, and deploy runs with the operator's full privileges.

No amount of path validation closes a check-then-use race, so this module does not
validate paths and then delete them. It walks the components with
``O_NOFOLLOW | O_DIRECTORY``, so a symlinked component fails at *open* time, and
then unlinks relative to that directory file descriptor. The entry removed is the
one inside the directory actually opened, whatever happens to any path prefix
afterwards.

Kind semantics, matching the manifest format ``TYPE<TAB>PATH``:

``f``
    Remove a regular file. Refuses if the leaf is a symlink — deleting through it
    would follow the link.
``l``
    Remove a symlink. Removes the LINK itself, never its target.
``d``
    Remove a directory, and only when already empty.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import os
import stat as stat_module
import sys
from pathlib import Path

REDACTED_UNSAFE = "ignoring unsafe manifest entry"
VALID_KINDS = frozenset({"d", "f", "l"})


def path_is_lexically_safe(relative: str) -> bool:
    """Reject absolute paths, traversal, and separator-bearing oddities.

    This is the cheap first layer. It is NOT the security boundary — the
    ``O_NOFOLLOW`` walk below is. Keeping it means a malformed manifest is
    rejected with a clear message before we touch the filesystem at all.
    """
    if not relative or relative.startswith("/"):
        return False
    if "\n" in relative or "\t" in relative or "\0" in relative:
        return False
    parts = relative.split("/")
    return not any(part in ("", ".", "..") for part in parts)


def _open_dir_nofollow(parent_fd: int | None, name: str) -> int:
    """Open a directory component, refusing to traverse a symlink.

    ``O_NOFOLLOW`` makes this raise ELOOP when *name* is a symlink, which is
    exactly the escape the shell version allowed. ``O_DIRECTORY`` additionally
    rejects a non-directory component.
    """
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if parent_fd is None:
        return os.open(name, flags)
    return os.open(name, flags, dir_fd=parent_fd)


class ComponentRefused(Exception):
    """A path component could not be traversed safely.

    Carries the component name so the operator sees WHICH one was refused. The
    errno for a symlinked directory component differs across platforms (ELOOP on
    Linux, ENOTDIR on macOS), so the reason is classified by inspecting the entry
    rather than by mapping errno — the message must not be platform-dependent.
    """

    def __init__(self, component: str, reason: str) -> None:
        super().__init__(f"{reason} '{component}'")
        self.component = component
        self.reason = reason


def _classify_component(parent_fd: int | None, name: str) -> str:
    """Explain why a component could not be opened. Message-only, never a gate.

    Safety comes from ``O_NOFOLLOW`` failing the open. This lstat runs only after
    that failure, purely to name the cause.
    """
    try:
        info = (
            os.lstat(name) if parent_fd is None else os.lstat(name, dir_fd=parent_fd)
        )
    except OSError:
        return "cannot resolve component"
    if stat_module.S_ISLNK(info.st_mode):
        return "symlinked component"
    if not stat_module.S_ISDIR(info.st_mode):
        return "non-directory component"
    return "unreadable component"


def _walk_to_parent(agent_root: str, parts: list[str]) -> tuple[int, list[int]]:
    """Open every intermediate component without following symlinks.

    Returns the parent directory fd plus every fd opened, so the caller can close
    them all. Raises ComponentRefused if any component is a symlink or not a
    directory — the O_NOFOLLOW open is what enforces that, not a prior check.
    """
    opened: list[int] = []
    try:
        try:
            fd = _open_dir_nofollow(None, agent_root)
        except OSError as exc:
            raise ComponentRefused(agent_root, _classify_component(None, agent_root)) from exc
        opened.append(fd)
        for component in parts[:-1]:
            try:
                fd = _open_dir_nofollow(fd, component)
            except OSError as exc:
                raise ComponentRefused(component, _classify_component(fd, component)) from exc
            opened.append(fd)
    except BaseException:
        # Review finding P2: this list is LOCAL. When we raise, the caller's own
        # `opened` was never assigned, so it closed nothing and every refused entry
        # leaked one directory fd — a corrupt manifest could exhaust the table and
        # deny the reap entirely. Close our own fds before propagating.
        _close_all(opened)
        raise
    return fd, opened


def _close_all(fds: list[int]) -> None:
    for fd in fds:
        with contextlib.suppress(OSError):
            os.close(fd)


def _describe(exc: OSError, relative: str) -> str:
    if exc.errno == errno.ELOOP:
        return f"{REDACTED_UNSAFE} '{relative}': symlinked component refused"
    if exc.errno == errno.ENOTDIR:
        return f"{REDACTED_UNSAFE} '{relative}': component is not a directory"
    if exc.errno == errno.ENOENT:
        return f"  .agent: nothing to remove for '{relative}'"
    return f"{REDACTED_UNSAFE} '{relative}': {exc.strerror}"


def reap_entry(agent_root: str, kind: str, relative: str) -> tuple[bool, str]:
    """Remove one manifest entry. Returns (removed, message)."""
    if kind not in VALID_KINDS or not path_is_lexically_safe(relative):
        return False, f"  .agent: {REDACTED_UNSAFE} '{kind} {relative}'"

    parts = relative.split("/")
    leaf = parts[-1]
    opened: list[int] = []
    unsafe = f"{REDACTED_UNSAFE} '{kind} {relative}'"
    try:
        parent_fd, opened = _walk_to_parent(agent_root, parts)
    except ComponentRefused as exc:
        # No _close_all here: on failure `opened` was never assigned, so it is still
        # empty and closing it did nothing — that WAS the leak (P2). _walk_to_parent
        # now closes its own fds before propagating. Closing a stale number here
        # would risk closing an unrelated fd that reused it.
        return False, f"  .agent: {unsafe}: {exc.reason} '{exc.component}'"
    except OSError as exc:
        return False, f"  .agent: {_describe(exc, relative)}"

    try:
        try:
            info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False, f"  .agent: nothing to remove for '{relative}'"

        is_link = stat_module.S_ISLNK(info.st_mode)
        is_dir = stat_module.S_ISDIR(info.st_mode)

        if kind == "l":
            if not is_link:
                return False, f"  .agent: {REDACTED_UNSAFE} '{relative}': expected a symlink"
            os.unlink(leaf, dir_fd=parent_fd)
        elif kind == "f":
            if is_link:
                # Deleting a symlink declared as a file would follow the link.
                return False, f"  .agent: {REDACTED_UNSAFE} '{relative}': symlinked leaf declared 'f'"
            if is_dir:
                return False, f"  .agent: {REDACTED_UNSAFE} '{relative}': directory declared 'f'"
            os.unlink(leaf, dir_fd=parent_fd)
        else:  # kind == "d"
            if is_link:
                return False, f"  .agent: {REDACTED_UNSAFE} '{relative}': symlinked leaf declared 'd'"
            if not is_dir:
                return False, f"  .agent: {REDACTED_UNSAFE} '{relative}': not a directory"
            try:
                os.rmdir(leaf, dir_fd=parent_fd)
            except OSError as exc:
                if exc.errno in (errno.ENOTEMPTY, errno.EEXIST):
                    # Runtime scratch still lives here — preserve by default (#4741).
                    return False, ""
                raise
        return True, f"  .agent: removed retired deploy artifact '{relative}'"
    except OSError as exc:
        return False, f"  .agent: {_describe(exc, relative)}"
    finally:
        _close_all(opened)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source-root", required=True)
    args = parser.parse_args(argv)

    agent_root = args.agent_root
    # Validate the mirror root FIRST — before the missing-manifest early return.
    # Review finding P1: with the check after that return, a first run (no manifest
    # yet) exited 0 having never looked at the root at all, and deploy_prompts.sh
    # then runs a path-based `rsync` into `.agent/`. A symlinked root therefore
    # redirected deploy WRITES outside the repository. Validating here means the
    # helper refuses loudly on every path through it, first run included.
    # Distinguish ABSENT from REDIRECTED. On a first deploy `.agent` does not exist
    # yet and rsync creates it — refusing there breaks every clean install (caught by
    # the existing suite when I first wrote this check as `not isdir`). What must be
    # refused is a root that EXISTS but is not a real directory, which is the actual
    # redirect.
    if os.path.lexists(agent_root):
        if os.path.islink(agent_root) or not os.path.isdir(agent_root):
            print(
                f"  .agent: refusing manifest reap: '{agent_root}' is not a real directory",
                file=sys.stderr,
            )
            return 1
    else:
        # Nothing deployed yet, so nothing to reap. rsync will create a real directory.
        return 0

    manifest = Path(args.manifest)
    if not manifest.is_file():
        print("  .agent: no deploy manifest yet; preserving all existing paths during migration")
        return 0

    source_root = Path(args.source_root)
    files: list[tuple[str, str]] = []
    dirs: list[tuple[str, str]] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        kind, _, relative = line.partition("\t")
        if not relative:
            print(f"  .agent: {REDACTED_UNSAFE} '{line}'", file=sys.stderr)
            continue
        # Validate BEFORE consulting the source tree. `source_root / relative` returns
        # the absolute path unchanged when `relative` is absolute, so an absolute entry
        # naming an existing external file would otherwise look "still in source" and be
        # skipped silently instead of refused loudly. Refusing must be the visible outcome.
        if kind not in VALID_KINDS or not path_is_lexically_safe(relative):
            print(f"  .agent: {REDACTED_UNSAFE} '{kind} {relative}'", file=sys.stderr)
            continue
        # Still present in source => not retired.
        candidate = source_root / relative
        if candidate.exists() or candidate.is_symlink():
            continue
        (dirs if kind == "d" else files).append((kind, relative))

    # Review finding P2: `failed` was declared and never assigned — a flag that
    # cannot fire, so the exit code claimed success unconditionally. Deliberate
    # semantics now, stated rather than implied:
    #   REFUSING an entry is the SAFE outcome (we preserved a file we were unsure
    #   about) and must NOT fail deploy — a symlink an agent legitimately left in
    #   .agent/ would otherwise block every deploy.
    #   An UNEXPECTED internal error is different: it means the reap did not do what
    #   it was asked, and a silently-skipped reap is a false-green.
    refused = 0
    errored = 0

    def _run(kind: str, relative: str) -> None:
        nonlocal refused, errored
        try:
            removed, message = reap_entry(agent_root, kind, relative)
        except Exception as exc:  # broad on purpose: one bad entry must not abort the reap
            errored += 1
            print(f"  .agent: internal error reaping '{relative}': {exc}", file=sys.stderr)
            return
        if message:
            print(message, file=sys.stdout if removed else sys.stderr)
        if not removed and message:
            refused += 1

    for kind, relative in files:
        _run(kind, relative)
    # Deepest first, so a parent becomes empty only after its children are gone.
    for kind, relative in sorted(dirs, key=lambda item: item[1].count("/"), reverse=True):
        _run(kind, relative)

    if refused:
        print(f"  .agent: {refused} manifest entry(ies) refused and preserved", file=sys.stderr)
    return 1 if errored else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
